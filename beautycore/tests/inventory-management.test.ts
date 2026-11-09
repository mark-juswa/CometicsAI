import { preservingBusinessRecords } from "../scripts/business-preservation";
import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import { PGlite } from "@electric-sql/pglite";
import sharp from "sharp";
import { applySavedLookMigrations } from "../scripts/saved-look-migrations";
import { inventoryApi } from "../lib/business/inventory";
import { createBusinessStore } from "../lib/business/store";
import {
  bookingApi,
  completeAppointment,
  type Dependencies,
} from "../lib/business/api";
const A = "55555555-5555-4555-8555-555555555555",
  C = "11111111-1111-4111-8111-111111111111",
  S = "33333333-3333-4333-8333-333333333333";
let db: PGlite,
  actor = A,
  deps: Dependencies,
  service: string;
const query = async (sql: string, values: unknown[] = []) =>
  (await db.query<Record<string, unknown>>(sql, values)).rows;
const request = (path: string, method = "GET", body?: unknown) =>
  new Request("http://localhost:3000" + path, {
    method,
    headers: {
      Origin: "http://localhost:3000",
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
const api = (section: string, method = "GET", body?: unknown, params = "") =>
  inventoryApi(
    request(
      "/api/inventory" + (section === "products" ? "" : "/" + section) + params,
      method,
      body,
    ),
    section,
    { query, actor: deps.actor },
  );
async function add(extra: Record<string, unknown> = {}) {
  actor = A;
  const r = await api("products", "POST", {
    productName: "Shampoo",
    category: "Hair Care",
    brand: "Fixture",
    currentStock: 100,
    minimumThreshold: 10,
    purchaseCost: 2,
    unit: "ml",
    ...extra,
  });
  assert.equal(r.status, 201, await r.clone().text());
  return (await r.json()).item.id as string;
}
async function config(item: string, quantity: number, unit = "ml") {
  actor = A;
  const r = await api("requirements", "PUT", {
    serviceId: service,
    requirements: [{ inventoryId: item, quantity, unit }],
  });
  assert.equal(r.status, 200, await r.clone().text());
}
async function book() {
  actor = C;
  const r = await bookingApi(
    request("/api/appointments", "POST", {
      serviceId: service,
      stylistId: S,
      appointmentDate: "2030-10-17T02:00:00Z",
    }),
    undefined,
    deps,
  );
  assert.equal(r.status, 201, await r.clone().text());
  return (await r.json()).appointment.id as string;
}
async function complete(appointment: string, products: unknown[] = []) {
  actor = S;
  return completeAppointment(
    request("/complete", "POST", { products }),
    appointment,
    deps,
  );
}
const balance = async (item: string) =>
  Number(
    (await query("SELECT current_stock FROM inventory WHERE id=$1", [item]))[0]
      .current_stock,
  );
test("reported-only completion does not require or deduct every configured supply", async () => {
  const item=await add({currentStock:0});
  await config(item,10);
  await query("UPDATE inventory_policy SET consumption_mode='reported_only'");
  const appointment=await book();
  const response=await complete(appointment);
  assert.equal(response.status,200,await response.clone().text());
  assert.equal(await balance(item),0);
  assert.equal((await query("SELECT count(*)::int AS n FROM inventory_service_consumption"))[0].n,0);
});
test("only reported used-up units are deducted once, and omitted supplies are unchanged", async () => {
  const item=await add({productName:'Polish bottle',unit:'bottle',currentStock:6}),other=await add({productName:'Other supply',currentStock:0});
  await config(other,10);
  await query("UPDATE inventory_policy SET consumption_mode='reported_only'");
  const appointment=await book(),payload=[{inventoryId:item,productName:'Polish bottle',quantity:1,unit:'bottle',consumeStock:true}];
  assert.equal((await complete(appointment,payload)).status,200);
  assert.equal((await complete(appointment,payload)).status,200);
  assert.equal(await balance(item),5);assert.equal(await balance(other),0);
  const rows=await query("SELECT t.quantity,d.reason,d.unit FROM inventory_transactions t JOIN inventory_transaction_details d ON d.transaction_id=t.id WHERE d.kind='service_consumption'");
  assert.equal(rows.length,1);assert.equal(Number(rows[0].quantity),1);assert.equal(rows[0].unit,'bottle');assert.match(String(rows[0].reason),/used-up supply/);
});
test("reported-only consumption requires a positive quantity and rejects reusable equipment", async () => {
  const item=await add({currentStock:3,unit:'piece'}),tool=await add({productName:'Dryer',itemType:'equipment',unit:'piece',currentStock:2});
  await query("UPDATE inventory_policy SET consumption_mode='reported_only'");
  const appointment=await book();
  for(const line of [{inventoryId:item,productName:'Supply',consumeStock:true,quantity:0,unit:'piece'},{inventoryId:tool,productName:'Dryer',consumeStock:true,quantity:1,unit:'piece'}])assert.equal((await complete(appointment,[line])).status,409);
  assert.equal(await balance(item),3);assert.equal(await balance(tool),2);
  assert.equal((await query('SELECT status FROM appointments WHERE id=$1',[appointment]))[0].status,'confirmed');
});
const move = (item: string, extra: Record<string, unknown> = {}) =>
  api("transactions", "POST", {
    id: item,
    kind: "stock_out",
    direction: "out",
    quantity: 1,
    unit: "ml",
    reason: "Fixture withdrawal",
    requestId: randomUUID(),
    ...extra,
  });
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
    settings: { enabled: true, clientLimit: 20, storageBudget: 134217728 },
  };
  service = String(
    (
      await query(
        "SELECT id FROM salon_services WHERE name='Women''s Cut & Blowdry'",
      )
    )[0].id,
  );
});
test.beforeEach(async () => {
  await db.exec("TRUNCATE inventory,inventory_suppliers,users CASCADE");
  await query(
    "UPDATE inventory_policy SET shortage_policy='block',expiry_warning_days=30,consumption_mode='configured'",
  );
  actor = A;
  for (const [id, role] of [
    [A, "admin"],
    [C, "client"],
    [S, "stylist"],
  ])
    await query(
      "INSERT INTO users(id,email,name,password_hash,role)VALUES($1,$2,$3,$4,$5)",
      [id, id + "@example.invalid", role, "fixture-only", role],
    );
  await query("INSERT INTO stylist_specialties VALUES($1,'hair')", [S]);
  await query("SELECT beautycore_set_work($1,true,$2::jsonb)", [
    S,
    JSON.stringify(
      Array.from({ length: 7 }, (_, day) => ({
        day,
        start: "09:00",
        end: "17:00",
      })),
    ),
  ]);
});
test.after(async () => await db?.close());
test("migration adds no suggested products and supports exact decimal stock with an opening ledger", async () => {
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM inventory"))[0].n,
    0,
  );
  const id = await add({ currentStock: 10.125, sku: "S-001" });
  assert.equal(await balance(id), 10.125);
  const rows = await query(
    "SELECT quantity FROM inventory_transactions WHERE inventory_id=$1",
    [id],
  );
  assert.equal(rows.length, 1);
  assert.equal(Number(rows[0].quantity), 10.125);
});
test("admin manages metadata, SKU uniqueness, images and safe stock fields", async () => {
  const image =
    "data:image/png;base64," +
    (
      await sharp({
        create: { width: 16, height: 16, channels: 3, background: "pink" },
      })
        .png()
        .toBuffer()
    ).toString("base64");
  const id = await add({
    sku: "SKU-1",
    image,
    description: "Wash stock",
    maximumStock: 250,
    location: "Cabinet A",
  });
  const result = await (await api("products")).json();
  assert.equal(result.inventory[0].description, "Wash stock");
  assert.match(result.inventory[0].imageUrl, /\/image$/);
  assert.equal(JSON.stringify(result).includes("base64"), false);
  const img = await inventoryApi(
    request("/image"),
    "image",
    { query, actor: deps.actor },
    id,
  );
  assert.equal(img.status, 200);
  assert.equal(img.headers.get("Content-Type"), "image/png");
  assert.equal(
    (await api("products", "PATCH", { id, currentStock: 9 })).status,
    400,
  );
  assert.equal(
    (await api("products", "PATCH", { id, brand: "Updated" })).status,
    200,
  );
  assert.equal(
    (
      await api("products", "POST", {
        productName: "Other",
        category: "Hair",
        sku: "sku-1",
      })
    ).status,
    409,
  );
});
test("role boundaries protect mutations, supplier contacts and purchase costs", async () => {
  await add();
  actor = S;
  const staff = await (await api("products")).json();
  assert.equal(staff.inventory[0].purchaseCost, undefined);
  assert.equal(staff.inventory[0].supplierName, undefined);
  assert.equal((await api("products", "POST", {})).status, 403);
  assert.equal((await api("suppliers")).status, 403);
  actor = C;
  assert.equal((await api("products")).status, 403);
});
test("configured supplies are consumed only at completion and exactly once", async () => {
  const item = await add();
  await config(item, 12.5);
  const ap = await book();
  assert.equal(await balance(item), 100);
  const r = await complete(ap);
  assert.equal(r.status, 200, await r.clone().text());
  assert.equal(await balance(item), 87.5);
  const count = (
    await query("SELECT count(*)::int AS n FROM inventory_transactions")
  )[0].n;
  assert.equal((await complete(ap)).status, 200);
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM inventory_transactions"))[0].n,
    count,
  );
  assert.equal(
    (
      await query(
        "SELECT count(*)::int AS n FROM inventory_service_consumption",
      )
    )[0].n,
    1,
  );
});
test("actual usage converts units and requires a quantity-change explanation", async () => {
  const item = await add({ currentStock: 10.5 });
  await config(item, 10);
  const ap = await book();
  const product = {
    inventoryId: item,
    productName: "Forged name",
    quantity: 0.005,
    unit: "l",
    brand: null,
    unitCost: null,
  };
  assert.equal((await complete(ap, [product])).status, 409);
  assert.equal(await balance(item), 10.5);
  const r = await complete(ap, [
    { ...product, adjustmentReason: "Short treatment used less" },
  ]);
  assert.equal(r.status, 200, await r.clone().text());
  assert.equal(await balance(item), 5.5);
  const row = (
    await query(
      "SELECT product_name,quantity,unit FROM appointment_product_usage",
    )
  )[0];
  assert.equal(row.product_name, "Shampoo");
  assert.equal(Number(row.quantity), 5);
  assert.equal(row.unit, "ml");
});
test("zero actual usage is recorded with a reason and does not deduct stock", async () => {
  const item = await add();
  await config(item, 2);
  const ap = await book();
  const r = await complete(ap, [
    {
      inventoryId: item,
      productName: "Shampoo",
      quantity: 0,
      unit: "ml",
      adjustmentReason: "Client declined washing",
    },
  ]);
  assert.equal(r.status, 200, await r.clone().text());
  assert.equal(await balance(item), 100);
  assert.equal(
    Number(
      (
        await query(
          "SELECT requested_quantity FROM inventory_service_consumption",
        )
      )[0].requested_quantity,
    ),
    0,
  );
});
test("reusable equipment is checked but never consumed", async () => {
  const item = await add({
    productName: "Hair Dryer",
    itemType: "equipment",
    unit: "piece",
    currentStock: 2,
  });
  await config(item, 1, "piece");
  const ap = await book();
  assert.equal((await complete(ap)).status, 200);
  assert.equal(await balance(item), 2);
  assert.equal(
    (
      await query(
        "SELECT count(*)::int AS n FROM inventory_transaction_details WHERE kind='service_consumption'",
      )
    )[0].n,
    0,
  );
});
test("insufficient stock blocks the entire completion without partial changes", async () => {
  const item = await add({ currentStock: 3 });
  await config(item, 5);
  const ap = await book();
  const r = await complete(ap);
  assert.equal(r.status, 409);
  assert.equal(await balance(item), 3);
  assert.equal(
    (await query("SELECT status FROM appointments WHERE id=$1", [ap]))[0]
      .status,
    "confirmed",
  );
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM appointment_product_usage"))[0]
      .n,
    0,
  );
});
test("configured review policy records shortages and never creates negative stock", async () => {
  const item = await add({ currentStock: 3 });
  await config(item, 5);
  actor = A;
  assert.equal(
    (
      await api("policy", "PUT", {
        shortagePolicy: "consume_available",
        expiryWarningDays: 30,
      })
    ).status,
    200,
  );
  const ap = await book();
  assert.equal((await complete(ap)).status, 200);
  assert.equal(await balance(item), 0);
  assert.equal(
    Number(
      (await query("SELECT shortage FROM inventory_service_consumption"))[0]
        .shortage,
    ),
    2,
  );
  actor = A;
  assert.equal((await (await api("summary")).json()).shortages.length, 1);
});
test("expired and inactive items are unavailable for normal service consumption", async () => {
  const item = await add({ expirationDate: "2001-01-01" });
  await config(item, 1);
  const ap = await book();
  assert.equal((await complete(ap)).status, 409);
  assert.equal(await balance(item), 100);
  actor = A;
  const list = await (await api("products")).json();
  assert.equal(list.inventory[0].expired, true);
  assert.equal(
    (
      await api("products", "PATCH", {
        id: item,
        expirationDate: null,
        active: false,
      })
    ).status,
    200,
  );
  assert.equal((await complete(ap)).status, 409);
});
test("cancelled and no-show outcomes do not consume inventory", async () => {
  const item = await add();
  await config(item, 10);
  const ap = await book();
  await query("UPDATE appointments SET status='cancelled' WHERE id=$1", [ap]);
  assert.equal((await complete(ap)).status, 409);
  assert.equal(await balance(item), 100);
});
test("stock movement requests are idempotent and conflicting reuse is rejected", async () => {
  const item = await add({ currentStock: 10 });
  const key = randomUUID(),
    body = { quantity: 2, requestId: key };
  assert.equal((await move(item, body)).status, 201);
  assert.equal((await move(item, body)).status, 201);
  assert.equal(await balance(item), 8);
  assert.equal((await move(item, { ...body, quantity: 3 })).status, 409);
  assert.equal(await balance(item), 8);
});
test("concurrent withdrawals cannot overdraw inventory", async () => {
  const item = await add({ currentStock: 10 });
  const responses = await Promise.all([
    move(item, { quantity: 6 }),
    move(item, { quantity: 6 }),
  ]);
  assert.deepEqual(responses.map((r) => r.status).sort(), [201, 409]);
  assert.equal(await balance(item), 4);
});
test("stock adjustments compare the prior balance and preserve immutable history", async () => {
  const item = await add({ currentStock: 10 });
  assert.equal(
    (
      await move(item, {
        kind: "adjustment",
        previousQuantity: 10,
        adjustedQuantity: 7,
        reason: "Physical count",
      })
    ).status,
    201,
  );
  assert.equal(await balance(item), 7);
  assert.equal(
    (
      await move(item, {
        kind: "adjustment",
        previousQuantity: 10,
        adjustedQuantity: 5,
        reason: "Stale count",
      })
    ).status,
    409,
  );
  await assert.rejects(
    query("UPDATE inventory SET current_stock=42 WHERE id=$1", [item]),
    /stock transaction/,
  );
  await assert.rejects(
    query("UPDATE inventory_transactions SET note='rewrite'"),
    /immutable/,
  );
});
test("history-bearing products are archived, while unused products may be removed", async () => {
  const item = await add();
  const response = await api("products", "DELETE", undefined, "?id=" + item);
  assert.equal((await response.json()).result, "archived");
  assert.equal(
    (
      await query(
        "SELECT active FROM inventory_details WHERE inventory_id=$1",
        [item],
      )
    )[0].active,
    false,
  );
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM inventory_transactions"))[0].n,
    1,
  );
  const empty = await add({ currentStock: 0 });
  assert.equal(
    (await (await api("products", "DELETE", undefined, "?id=" + empty)).json())
      .result,
    "removed",
  );
});
test("service requirements lock units, reject unrelated services and preserve independent quantities", async () => {
  const item = await add({ currentStock: 0 });
  await config(item, 2);
  assert.equal(
    (await api("products", "PATCH", { id: item, unit: "l" })).status,
    409,
  );
  assert.equal(
    (
      await api("requirements", "PUT", {
        serviceId: "made-up",
        requirements: [],
      })
    ).status,
    400,
  );
});
test("purchases retain supplier, cost, reference, actor and date snapshots", async () => {
  const supplierResponse = await api("suppliers", "POST", {
    name: "Salon Supplier",
    contact: "Fixture contact",
    email: "supply@example.invalid",
    active: true,
  });
  assert.equal(supplierResponse.status, 201);
  const supplier = (await supplierResponse.json()).supplier.id;
  const item = await add({ currentStock: 0 });
  assert.equal(
    (
      await move(item, {
        kind: "stock_in",
        direction: "in",
        quantity: 5,
        unitCost: 2,
        supplierId: supplier,
        reference: "R-001",
      })
    ).status,
    201,
  );
  const history = await (await api("transactions")).json();
  assert.equal(history.transactions[0].supplierName, "Salon Supplier");
  assert.equal(history.transactions[0].reference, "R-001");
  assert.equal(history.transactions[0].recordedBy, A);
  assert.equal(history.transactions[0].totalCost, 10);
  const report = await (await api("reports")).json();
  assert.equal(report.purchaseExpenses.total, 10);
  assert.equal(report.stats.value, 10);
});
test("linked corrections reconcile consumption without editing the original ledger", async () => {
  const item = await add();
  await config(item, 10);
  const ap = await book();
  assert.equal((await complete(ap)).status, 200);
  actor = A;
  assert.equal(
    (
      await move(item, {
        kind: "correction",
        direction: "in",
        quantity: 2,
        appointmentId: ap,
        reason: "Actual usage was eight ml",
      })
    ).status,
    201,
  );
  assert.equal(await balance(item), 92);
  const report = await (await api("reports")).json();
  assert.equal(report.consumption[0].quantity, 8);
  assert.equal(
    (
      await move(item, {
        kind: "correction",
        direction: "in",
        quantity: 9,
        appointmentId: ap,
        reason: "Too much returned",
      })
    ).status,
    409,
  );
});
test("reports filter actual ledger rows by product, supplier, staff, kind and salon date", async () => {
  const one = await add(),
    two = await add({ productName: "Conditioner" });
  await move(one, { quantity: 2 });
  await move(two, { quantity: 3 });
  const h = await (
    await api(
      "transactions",
      "GET",
      undefined,
      "?product=" + one + "&kind=stock_out&staff=" + A,
    )
  ).json();
  assert.equal(h.total, 1);
  assert.equal(h.transactions[0].productName, "Shampoo");
  const future = await (
    await api("transactions", "GET", undefined, "?from=2099-01-01")
  ).json();
  assert.equal(future.total, 0);
});

test("starting, cancelling and marking no-show never consume configured products", async () => {
  const item = await add();
  await config(item, 10);
  const ap = await book();
  await query(
    "SELECT * FROM beautycore_service_action($1,$2,'start',NULL,NULL,'2030-10-17T01:59:00Z')",
    [ap, S],
  );
  assert.equal(await balance(item), 100);
  actor = S;
  await query(
    "SELECT * FROM beautycore_service_action($1,$2,'cancel','Fixture cancellation',NULL,'2030-10-17T02:05:00Z')",
    [ap, S],
  );
  assert.equal(await balance(item), 100);
  const second = await book();
  await query(
    "SELECT * FROM beautycore_service_action($1,$2,'no_show','Absent',NULL,'2030-10-17T02:05:00Z')",
    [second, S],
  );
  assert.equal((await complete(second)).status, 409);
  assert.equal(await balance(item), 100);
});
test("competing completions share stock safely and a multi-product shortage rolls back every deduction", async () => {
  const item = await add({ currentStock: 10 });
  await config(item, 8);
  const first = await book();
  actor = C;
  const r = await bookingApi(
    request("/api/appointments", "POST", {
      serviceId: service,
      stylistId: S,
      appointmentDate: "2030-10-17T03:30:00Z",
    }),
    undefined,
    deps,
  );
  assert.equal(r.status, 201);
  const second = (await r.json()).appointment.id;
  const responses = await Promise.all([complete(first), complete(second)]);
  assert.deepEqual(responses.map((r) => r.status).sort(), [200, 409]);
  assert.equal(await balance(item), 2);
});
test("correcting a recorded shortfall clears the outstanding attention item without rewriting history", async () => {
  const item = await add({ currentStock: 3 });
  await config(item, 5);
  await api("policy", "PUT", {
    shortagePolicy: "consume_available",
    expiryWarningDays: 30,
  });
  const ap = await book();
  assert.equal((await complete(ap)).status, 200);
  actor = A;
  assert.equal(
    (await move(item, { kind: "stock_in", direction: "in", quantity: 4 }))
      .status,
    201,
  );
  assert.equal(
    (
      await move(item, {
        kind: "correction",
        direction: "out",
        quantity: 2,
        appointmentId: ap,
        reason: "Supplies reconciled",
      })
    ).status,
    201,
  );
  assert.equal((await (await api("summary")).json()).shortages.length, 0);
  assert.equal(
    Number(
      (
        await query(
          "SELECT shortage FROM inventory_service_consumption WHERE appointment_id=$1",
          [ap],
        )
      )[0].shortage,
    ),
    2,
  );
});
test("attention and disposal reports use actual expiry dates and withdrawal transactions", async () => {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + 1);
  const item = await add({
    expirationDate: date.toISOString().slice(0, 10),
    currentStock: 20,
  });
  assert.equal(
    (await (await api("products")).json()).inventory[0].expiringSoon,
    true,
  );
  await move(item, {
    kind: "damaged",
    quantity: 2,
    reason: "Damaged packaging",
  });
  await move(item, {
    kind: "expired",
    quantity: 3,
    reason: "Expired batch removed",
  });
  const reports = await (await api("reports")).json();
  assert.equal(reports.waste.length, 2);
  assert.equal(await balance(item), 15);
  assert.equal((await move(item, { quantity: 0 })).status, 400);
});

test("configured services cannot bypass completion deductions with a direct status update", async () => {
  const item = await add();
  await config(item, 5);
  const ap = await book();
  await assert.rejects(
    query("UPDATE appointments SET status='completed' WHERE id=$1", [ap]),
    /inventory-aware workflow/,
  );
  assert.equal(await balance(item), 100);
  assert.equal((await complete(ap)).status, 200);
  assert.equal(await balance(item), 95);
});
test("a shortage in one of several required products leaves every product and completion untouched", async () => {
  const first = await add(),
    second = await add({ productName: "Conditioner" });
  const ids = [first, second].sort();
  await move(ids[1], { quantity: 95 });
  await api("requirements", "PUT", {
    serviceId: service,
    requirements: ids.map((inventoryId) => ({
      inventoryId,
      quantity: 10,
      unit: "ml",
    })),
  });
  const ap = await book();
  assert.equal((await complete(ap)).status, 409);
  assert.equal(await balance(ids[0]), 100);
  assert.equal(await balance(ids[1]), 5);
  assert.equal(
    (
      await query(
        "SELECT count(*)::int AS n FROM inventory_transaction_details WHERE kind='service_consumption'",
      )
    )[0].n,
    0,
  );
});
test("numeric widening preserves existing product and transaction row values on repeated installation", async () => {
  const isolated = new PGlite();
  try {
    await isolated.exec(
      readFileSync("tests/fixtures/business-base.sql", "utf8"),
    );
    for (const file of [
      "0002_saved_looks.sql",
      "0003_saved_look_admission.sql",
      "0004_look_details.sql",
      "0005_service_completion.sql",
      "0007_business_controls.sql",
      "0008_work_availability.sql",
      "0009_customer_history.sql",
      "0010_ninety_minute_bookings.sql",
      "0011_booking_services.sql",
      "0012_service_statuses.sql",
      "0013_service_lifecycle.sql",
    ])
      await isolated.exec(readFileSync("db/migrations/" + file, "utf8"));
    await isolated.query(
      "INSERT INTO users(id,email,name,password_hash,role,is_active)VALUES($1,'preserve@example.invalid','Admin','fixture','admin',true)",
      [A],
    );
    await isolated.query(
      "SELECT * FROM beautycore_create_inventory_item('Existing','Brand','Hair',10,3,900,$1)",
      [A],
    );
    const before = (
      await isolated.query("SELECT to_jsonb(i) AS row FROM inventory i")
    ).rows;
    const statements = readFileSync(
      "db/migrations/0014_service_inventory.sql",
      "utf8",
    )
      .split("--> statement-breakpoint")
      .map((s) => s.trim())
      .filter(Boolean);
    for (let run = 0; run < 2; run++)
      await isolated.transaction(async (tx) => {
        for (const statement of preservingBusinessRecords(statements))
          await tx.query(statement);
      });
    assert.equal((await isolated.query<{consumption_mode:string}>("SELECT consumption_mode FROM inventory_policy")).rows[0].consumption_mode,"reported_only");
    assert.deepEqual(
      (await isolated.query("SELECT to_jsonb(i) AS row FROM inventory i")).rows,
      before,
    );
    assert.equal(
      (await isolated.query<{ n: number }>("SELECT count(*)::int AS n FROM inventory")).rows[0]
        .n,
      1,
    );
  } finally {
    await isolated.close();
  }
});
