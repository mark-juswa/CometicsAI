import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PGlite } from "@electric-sql/pglite";
import { applySavedLookMigrations } from "../scripts/saved-look-migrations";
import { createBusinessStore } from "../lib/business/store";
import {
  bookingApi,
  serviceLifecycle,
  completeAppointment,
  type Dependencies,
} from "../lib/business/api";
import { availableBookingSlots } from "../lib/business/booking-availability";
const C = "11111111-1111-4111-8111-111111111111",
  S = "33333333-3333-4333-8333-333333333333",
  OTHER = "44444444-4444-4444-8444-444444444444",
  A = "55555555-5555-4555-8555-555555555555";
const start = Date.parse("2030-10-17T02:00:00Z");
const hours = Array.from({ length: 7 }, (_, day) => ({
  day,
  start: "09:00",
  end: "17:00",
}));
let db: PGlite,
  deps: Dependencies,
  actor = C,
  now = start - 60000;
const query = async (text: string, values: unknown[] = []) =>
  (await db.query<Record<string, unknown>>(text, values)).rows;
const req = (path: string, body?: unknown) =>
  new Request("http://localhost:3000" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      Origin: "http://localhost:3000",
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
async function book(date = start, stylist = S) {
  actor = C;
  const r = await bookingApi(
    req("/api/appointments", {
      serviceName: "Women's Cut & Blowdry",
      serviceType: "hair",
      stylistId: stylist,
      appointmentDate: new Date(date).toISOString(),
    }),
    undefined,
    deps,
  );
  assert.equal(r.status, 201, await r.clone().text());
  return (await r.json()).appointment.id as string;
}
const act = (id: string, action: string, extra = {}) =>
  serviceLifecycle(
    req("/api/appointments/" + id + "/service", { action, ...extra }),
    id,
    deps,
  );
const sweep = async (time: number) =>
  Number(
    (
      await query("SELECT beautycore_process_no_shows($1::timestamptz) AS n", [
        new Date(time).toISOString(),
      ])
    )[0].n,
  );
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
    actor: async () => (await store.currentUser(actor)) ?? null,
    now: () => now,
    settings: { enabled: true, clientLimit: 20, storageBudget: 134217728 },
  };
});
test.beforeEach(async () => {
  await db.exec("TRUNCATE users CASCADE");
  actor = C;
  now = start - 60000;
  for (const [id, role] of [
    [C, "client"],
    [S, "stylist"],
    [OTHER, "stylist"],
    [A, "admin"],
  ])
    await query(
      "INSERT INTO users(id,email,name,password_hash,role) VALUES($1,$2,$3,$4,$5)",
      [id, id + "@example.invalid", role, "not-a-login", role],
    );
  for (const id of [S, OTHER]) {
    await query("INSERT INTO stylist_specialties VALUES($1,'hair')", [id]);
    await query("SELECT beautycore_set_work($1,true,$2::jsonb)", [
      id,
      JSON.stringify(hours),
    ]);
  }
});
test.after(async () => await db?.close());

test("automatic no-show has an exact thirty-minute boundary, preserves details, and is idempotent", async () => {
  const id = await book();
  const original = (
    await query(
      "SELECT client_id,stylist_id,appointment_date,service_name,total_price FROM appointments WHERE id=$1",
      [id],
    )
  )[0];
  assert.equal(await sweep(start + 1800000 - 1), 0);
  assert.equal(await sweep(start + 1800000), 1);
  assert.equal(await sweep(start + 3600000), 0);
  const row = (
    await query("SELECT status FROM appointments WHERE id=$1", [id])
  )[0];
  assert.equal(row.status, "no_show");
  assert.deepEqual(
    (
      await query(
        "SELECT client_id,stylist_id,appointment_date,service_name,total_price FROM appointments WHERE id=$1",
        [id],
      )
    )[0],
    original,
  );
  const history = await query(
    "SELECT * FROM appointment_activity WHERE appointment_id=$1 AND action='automatic_no_show'",
    [id],
  );
  assert.equal(history.length, 1);
  assert.equal(history[0].actor_id, null);
  assert.equal(history[0].source, "system");
  assert.ok(
    (
      await query(
        "SELECT no_show_at FROM appointment_service_tracking WHERE appointment_id=$1",
        [id],
      )
    )[0].no_show_at,
  );
});
test("recorded arrival protects the booking, and a later service start remains possible", async () => {
  const id = await book();
  actor = S;
  now = start + 600000;
  assert.equal((await act(id, "arrive")).status, 200);
  assert.equal(await sweep(start + 2700000), 0);
  now = start + 3600000;
  assert.equal((await act(id, "start")).status, 200);
  const row = await deps.store.appointment(id, { id: S, role: "stylist" });
  assert.equal(row?.status, "in_progress");
  assert.ok((row?.tracking as Record<string, unknown>).started_at);
  assert.equal(await sweep(start + 86400000), 0);
});
test("running service cannot become no-show, blocks other bookings, and completes with real end/audit records", async () => {
  const id = await book();
  actor = S;
  assert.equal((await act(id, "start")).status, 200);
  assert.equal(await sweep(start + 1800000), 0);
  assert.equal(
    (await act(id, "no_show", { confirmed: true, reason: "Wrong outcome" }))
      .status,
    409,
  );
  const denied = await bookingApi(
    req("/api/appointments", {
      serviceName: "Women's Cut & Blowdry",
      serviceType: "hair",
      stylistId: S,
      appointmentDate: "2030-10-17T02:30:00Z",
    }),
    undefined,
    { ...deps, actor: async () => ({ id: C, role: "client" }) },
  );
  assert.equal(denied.status, 409);
  const response = await completeAppointment(
    req("/api/appointments/" + id + "/complete", { products: [] }),
    id,
    deps,
  );
  assert.equal(response.status, 200);
  const row = await deps.store.appointment(id, { id: S, role: "stylist" });
  assert.equal(row?.status, "completed");
  assert.ok((row?.tracking as Record<string, unknown>).ended_at);
  const audit = await query(
    "SELECT actor_id FROM appointment_activity WHERE appointment_id=$1 AND status='completed'",
    [id],
  );
  assert.equal(audit[0].actor_id, S);
});
test("only assigned stylist/admin can act, stop requires confirmation, and malformed actor fields are rejected", async () => {
  const id = await book();
  assert.equal((await act(id, "start")).status, 403);
  actor = OTHER;
  assert.equal((await act(id, "start")).status, 404);
  actor = S;
  now = start + 300000;
  assert.equal((await act(id, "no_show", { reason: "Absent" })).status, 400);
  assert.equal((await act(id, "start", { actorId: A })).status, 400);
  assert.equal(
    (
      await act(id, "no_show", {
        confirmed: true,
        reason: "Customer confirmed they will not attend",
      })
    ).status,
    200,
  );
  const tracking = (
    await query(
      "SELECT * FROM appointment_service_tracking WHERE appointment_id=$1",
      [id],
    )
  )[0];
  assert.equal(tracking.no_show_by, S);
});
test("no-show is terminal for ordinary actions and completion, with an admin-only future restoration", async () => {
  const id = await book();
  await sweep(start + 1800000);
  actor = S;
  now = start + 1800000;
  assert.equal((await act(id, "start")).status, 409);
  assert.equal(
    (await completeAppointment(req("/complete", { products: [] }), id, deps))
      .status,
    409,
  );
  assert.equal(
    (
      await act(id, "restore", {
        confirmed: true,
        reason: "Late arrival",
        appointmentDate: "2030-10-17T05:00:00Z",
      })
    ).status,
    409,
  );
  actor = A;
  assert.equal(
    (
      await act(id, "restore", {
        confirmed: true,
        reason: "Rescheduled late arrival",
        appointmentDate: "2030-10-17T05:00:00Z",
      })
    ).status,
    200,
  );
  assert.equal(
    (await deps.store.appointment(id, { id: A, role: "admin" }))?.status,
    "confirmed",
  );
  assert.equal(
    (
      await query(
        "SELECT count(*)::int AS n FROM appointment_activity WHERE appointment_id=$1 AND status='no_show'",
        [id],
      )
    )[0].n,
    1,
  );
});
test("restoration rechecks conflicts and does not erase a no-show when it cannot reserve the new time", async () => {
  const id = await book();
  await book(start + 10800000);
  await sweep(start + 1800000);
  actor = A;
  now = start + 1800000;
  assert.equal(
    (
      await act(id, "restore", {
        confirmed: true,
        reason: "Retry",
        appointmentDate: "2030-10-17T05:00:00Z",
      })
    ).status,
    409,
  );
  assert.equal(
    (await query("SELECT status FROM appointments WHERE id=$1", [id]))[0]
      .status,
    "no_show",
  );
});
test("Other retains active status; cancellation ends running work and preserves history", async () => {
  const id = await book();
  actor = S;
  assert.equal((await act(id, "start")).status, 200);
  assert.equal(
    (
      await act(id, "other", {
        confirmed: true,
        reason: "Waiting for the client to choose a colour",
      })
    ).status,
    200,
  );
  assert.equal(
    (await deps.store.appointment(id, { id: S, role: "stylist" }))?.status,
    "in_progress",
  );
  assert.equal(
    (
      await act(id, "cancel", {
        confirmed: true,
        reason: "Customer requested cancellation",
      })
    ).status,
    200,
  );
  const row = await deps.store.appointment(id, { id: S, role: "stylist" });
  assert.equal(row?.status, "cancelled");
  assert.ok((row?.tracking as Record<string, unknown>).ended_at);
});
test("start and sweep racing produce one valid outcome, never a started no-show", async () => {
  const id = await book();
  actor = S;
  now = start + 1800000 - 1;
  await Promise.all([act(id, "start"), sweep(start + 1800000)]);
  const row = (
    await query(
      "SELECT a.status,t.started_at FROM appointments a LEFT JOIN appointment_service_tracking t ON t.appointment_id=a.id WHERE a.id=$1",
      [id],
    )
  )[0];
  assert.ok(["in_progress", "no_show"].includes(String(row.status)));
  assert.ok(!(row.status === "no_show" && row.started_at));
});
test("release offers the next future minute and running work protects nearby times without blocking the future", () => {
  const reservations = [
    {
      stylistId: S,
      appointmentDate: "2030-10-17T02:00:00Z",
      durationMinutes: 90,
      status: "no_show",
      releasedAt: "2030-10-17T02:30:00Z",
    },
  ];
  const slots = availableBookingSlots(
    "2030-10-17",
    [{ id: S, hours }],
    reservations,
    new Date("2030-10-17T02:30:10Z"),
  );
  assert.equal(slots.find((s) => s.available)?.time, "10:31");
  reservations[0].status = "in_progress";
  assert.ok(
    availableBookingSlots(
      "2030-10-17",
      [{ id: S, hours }],
      reservations,
      new Date("2030-10-17T02:30:10Z"),
    ).some((s) => s.available),
  );
});
test("automatic processing does not retroactively modify overdue records before policy activation", async () => {
  const id = await book();
  await query("UPDATE appointment_lifecycle_policy SET enabled_at=$1", [
    new Date(start + 1).toISOString(),
  ]);
  try {
    assert.equal(await sweep(start + 1800000), 0);
    assert.equal(
      (await query("SELECT status FROM appointments WHERE id=$1", [id]))[0]
        .status,
      "confirmed",
    );
  } finally {
    await query(
      "UPDATE appointment_lifecycle_policy SET enabled_at='2026-01-01T00:00:00Z'",
    );
  }
});

test("a released slot can be rebooked once under competing requests and no-show history cannot be deleted", async () => {
  const id = await book();
  await sweep(start + 1800000);
  now = start + 1800000;
  const make = () =>
    bookingApi(
      req("/api/appointments", {
        serviceName: "Women's Cut & Blowdry",
        serviceType: "hair",
        stylistId: S,
        appointmentDate: new Date(start + 1860000).toISOString(),
      }),
      undefined,
      deps,
    );
  const responses = await Promise.all([make(), make()]);
  assert.deepEqual(responses.map((r) => r.status).sort(), [201, 409]);
  await assert.rejects(
    query("DELETE FROM appointments WHERE id=$1", [id]),
    /history cannot be deleted/,
  );
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM appointments"))[0].n,
    2,
  );
});
test("arrival prevents manual no-show and existing receipts survive an unattended outcome", async () => {
  const id = await book();
  actor = S;
  now = start + 300000;
  assert.equal((await act(id, "arrive")).status, 200);
  assert.equal(
    (await act(id, "no_show", { confirmed: true, reason: "Incorrect no-show" }))
      .status,
    409,
  );
  const second = await book(start + 7200000);
  await query(
    "SELECT beautycore_record_payment($1,$2,$3,10,'cash',NULL,gen_random_uuid())",
    [C, second, A],
  );
  await sweep(start + 9000000);
  assert.equal(
    (await query("SELECT status FROM appointments WHERE id=$1", [second]))[0]
      .status,
    "no_show",
  );
  assert.equal(
    (
      await query(
        "SELECT count(*)::int AS n FROM appointment_payments WHERE appointment_id=$1",
        [second],
      )
    )[0].n,
    1,
  );
  await assert.rejects(
    query(
      "SELECT beautycore_record_payment($1,$2,$3,1,'cash',NULL,gen_random_uuid())",
      [C, second, A],
    ),
    /payment_not_allowed/,
  );
});
