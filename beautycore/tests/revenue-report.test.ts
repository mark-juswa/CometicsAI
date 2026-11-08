import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PGlite } from "@electric-sql/pglite";
import { applySavedLookMigrations } from "../scripts/saved-look-migrations";
import { revenueWindow } from "../lib/business/revenue-periods";
import { createBusinessStore } from "../lib/business/store";
import { stylistPerformance, type Dependencies } from "../lib/business/api";
const C = "11111111-1111-4111-8111-111111111111",
  S = "33333333-3333-4333-8333-333333333333",
  S2 = "44444444-4444-4444-8444-444444444444",
  A = "55555555-5555-4555-8555-555555555555";
let db: PGlite,
  deps: Dependencies,
  actor: string | null = A;
const query = async (sql: string, values: unknown[] = []) =>
  (await db.query<Record<string, unknown>>(sql, values)).rows;
const request = (params: string) =>
  new Request("http://localhost:3000/api/admin/stylist-performance?" + params);
async function appointment(
  date: string,
  amount: number | null,
  stylist: string | null = S,
  status = "completed",
) {
  await query(
    "INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,total_price,status) VALUES($1,$2,'Recorded service','hair',$3,$4,$5)",
    [C, stylist, date, amount, status],
  );
}
test.before(async () => {
  db = new PGlite();
  await db.exec(readFileSync("tests/fixtures/business-base.sql", "utf8"));
  await applySavedLookMigrations((statements) =>
    db.transaction(async (tx) => {
      for (const sql of statements) await tx.query(sql);
    }),
  );
  const store = createBusinessStore(query);
  deps = {
    store,
    actor: async () =>
      actor ? ((await store.currentUser(actor)) ?? null) : null,
    settings: { enabled: true, clientLimit: 20, storageBudget: 134217728 },
    now: () => Date.parse("2026-11-08T16:00:00Z"),
  };
});
test.beforeEach(async () => {
  actor = A;
  await db.exec("TRUNCATE users CASCADE");
  for (const [id, role, name] of [
    [C, "client", "Client"],
    [S, "stylist", "Stylist One"],
    [S2, "stylist", "Stylist Two"],
    [A, "admin", "Admin"],
  ])
    await query(
      "INSERT INTO users(id,email,name,password_hash,role) VALUES($1,$2,$3,$4,$5)",
      [id, id + "@example.invalid", name, "not-a-login", role],
    );
  await query("INSERT INTO stylist_specialties VALUES($1,'hair')", [S]);
});
test.after(async () => {
  await db.close();
});

test("calendar windows use full days, Monday weeks, leap months, and full calendar years", () => {
  assert.deepEqual(
    [
      revenueWindow("week", "2026-11-15").from,
      revenueWindow("week", "2026-11-15").to,
    ],
    ["2026-11-09", "2026-11-15"],
  );
  assert.equal(revenueWindow("month", "2024-02-15").to, "2024-02-29");
  assert.equal(revenueWindow("month", "1900-02-15").to, "1900-02-28");
  assert.equal(revenueWindow("month", "2000-02-15").to, "2000-02-29");
  assert.deepEqual(
    [
      revenueWindow("year", "2024-02-29").from,
      revenueWindow("year", "2024-02-29").to,
    ],
    ["2024-01-01", "2024-12-31"],
  );
  assert.equal(revenueWindow("month", "2026-01-31").previousFrom, "2025-12-01");
  assert.equal(revenueWindow("day", "2026-01-01").previousTo, "2025-12-31");
  assert.throws(() => revenueWindow("month", "2026-02-30"));
});
test("daily earnings honor Manila midnight, keep unpriced and zero services, and retain inactive staff history", async () => {
  await appointment("2026-11-08 15:59:59", 999);
  await appointment("2026-11-08 16:00:00", 100);
  await appointment("2026-11-09 15:59:59", 200);
  await appointment("2026-11-09 16:00:00", 800);
  await appointment("2026-11-09 01:00:00", null);
  await appointment("2026-11-09 02:00:00", 0);
  await appointment("2026-11-09 03:00:00", 30, S2);
  await appointment("2026-11-09 04:00:00", 50, null);
  await appointment("2026-11-09 05:00:00", 4000, null, "pending");
  await appointment("2026-11-09 06:00:00", 5000, null, "cancelled");
  await query("UPDATE users SET is_active=false WHERE id=$1", [S2]);
  const response = await stylistPerformance(
    request("period=day&date=2026-11-09"),
    deps,
  );
  assert.equal(response.status, 200, await response.clone().text());
  const report = await response.json();
  assert.equal(report.summary.amount, 380);
  assert.equal(report.summary.completed, 6);
  assert.equal(report.summary.unpriced, 1);
  assert.equal(report.summary.previousAmount, 999);
  assert.equal(report.summary.unassignedAmount, 50);
  assert.equal(report.series.length, 24);
  assert.equal(
    report.series.reduce(
      (sum: number, row: { amount: number }) => sum + row.amount,
      0,
    ),
    380,
  );
  const one = report.stylists.find((row: { id: string }) => row.id === S),
    two = report.stylists.find((row: { id: string }) => row.id === S2);
  assert.equal(one.dayAmount, 300);
  assert.equal(one.monthAmount, 2099);
  assert.equal(one.yearAmount, 2099);
  assert.equal(one.completed, 4);
  assert.equal(two.isActive, false);
  assert.equal(two.amount, 30);
  assert.deepEqual(one.specialties, ["hair"]);
});
test("weekly revenue includes exactly Monday through Sunday and compares the previous week", async () => {
  await appointment("2026-11-08 15:59:59", 300);
  await appointment("2026-11-08 16:00:00", 100);
  await appointment("2026-11-15 15:59:59", 200);
  await appointment("2026-11-15 16:00:00", 400);
  const report = await (
    await stylistPerformance(request("period=week&date=2026-11-12"), deps)
  ).json();
  assert.equal(report.summary.amount, 300);
  assert.equal(report.summary.previousAmount, 300);
  assert.equal(report.summary.changePercent, 0);
  assert.equal(report.series.length, 7);
  assert.equal(report.series[0].key, "2026-11-09T00:00:00");
  assert.equal(report.series[6].key, "2026-11-15T00:00:00");
});
test("monthly and yearly reports cover full ranges, zero-fill buckets, and exclude the next period", async () => {
  await appointment("2023-12-31 16:00:00", 10);
  await appointment("2024-01-31 16:00:00", 20);
  await appointment("2024-02-29 15:59:59", 30);
  await appointment("2024-02-29 16:00:00", 40);
  await appointment("2024-12-31 15:59:59", 50);
  await appointment("2024-12-31 16:00:00", 1000);
  const month = await (
    await stylistPerformance(request("period=month&date=2024-02-15"), deps)
  ).json();
  assert.equal(month.summary.amount, 50);
  assert.equal(month.summary.previousAmount, 10);
  assert.equal(month.series.length, 29);
  assert.equal(month.series[0].amount, 20);
  assert.equal(month.series[28].amount, 30);
  const yearResponse = await stylistPerformance(
    request("period=year&date=2024-11-09"),
    deps,
  );
  assert.equal(yearResponse.status, 200);
  const year = await yearResponse.json();
  assert.equal(year.summary.amount, 150);
  assert.equal(year.series.length, 12);
  assert.equal(year.series[11].amount, 50);
  assert.equal(year.summary.allTimeAmount, 1150);
  assert.equal(
    year.stylists.find((s: { id: string }) => s.id === S).yearAmount,
    150,
  );
});
test("empty periods and staff without earnings report real zeros without fabricated growth", async () => {
  const report = await (
    await stylistPerformance(request("period=month&date=2026-11-09"), deps)
  ).json();
  assert.equal(report.summary.amount, 0);
  assert.equal(report.summary.changePercent, null);
  assert.equal(report.series.length, 30);
  assert.ok(report.series.every((row: { amount: number }) => row.amount === 0));
  assert.equal(report.stylists.length, 2);
  assert.ok(
    report.stylists.every((row: { amount: number }) => row.amount === 0),
  );
});
test("period reports are admin-only, reject invalid parameters, and use the salon date by default", async () => {
  actor = C;
  assert.equal(
    (await stylistPerformance(request("period=year"), deps)).status,
    403,
  );
  actor = S;
  assert.equal(
    (await stylistPerformance(request("period=year"), deps)).status,
    403,
  );
  actor = null;
  assert.equal(
    (await stylistPerformance(request("period=year"), deps)).status,
    401,
  );
  actor = A;
  for (const params of [
    "period=quarter",
    "period=month&date=2026-02-30",
    "period=day&date=2201-01-01",
    "period=year&from=2026-01-01",
    "period=month&date=",
  ])
    assert.equal((await stylistPerformance(request(params), deps)).status, 400);
  const response = await stylistPerformance(request("period=day"), deps);
  assert.equal(response.headers.get("cache-control"), "private, no-store");
  assert.equal((await response.json()).window.date, "2026-11-09");
});
