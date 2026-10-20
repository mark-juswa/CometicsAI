import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PGlite } from '@electric-sql/pglite';
import {
  bookingApi,
  completeAppointment,
  appointmentReview,
  stylistPerformance,
  dailyServices,
  type Dependencies,
} from '../lib/business/api';
import { createBusinessStore } from '../lib/business/store';
import { applySavedLookMigrations } from '../scripts/saved-look-migrations';
const C = '11111111-1111-4111-8111-111111111111',
  C2 = '22222222-2222-4222-8222-222222222222',
  S = '33333333-3333-4333-8333-333333333333',
  S2 = '44444444-4444-4444-8444-444444444444',
  A = '55555555-5555-4555-8555-555555555555';
let db: PGlite,
  deps: Dependencies,
  actor: string | null = S;
const query = async (text: string, values: unknown[] = []) =>
  (await db.query<Record<string, unknown>>(text, values)).rows;
const request = (
  path: string,
  method = 'POST',
  body: unknown = {},
  origin = 'http://localhost:3000',
) =>
  new Request('http://localhost:3000' + path, {
    method,
    headers: { 'Content-Type': 'application/json', Origin: origin },
    ...(method === 'GET' ? {} : { body: JSON.stringify(body) }),
  });
const complete = (id: string, products: unknown[] = []) =>
  completeAppointment(request(`/api/appointments/${id}/complete`, 'POST', { products }), id, deps);
const review = (id: string, rating = 5, comment: string | null = 'Great service') =>
  appointmentReview(
    request(`/api/appointments/${id}/review`, 'POST', { rating, comment }),
    id,
    deps,
  );
async function appointment(
  status = 'confirmed',
  stylist: string | null = S,
  amount: number | null = 180,
  date = '2030-10-17 02:00:00',
) {
  return String(
    (
      await query(
        "INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,'Cut','hair',$3,$4,$5) RETURNING id",
        [C, stylist, date, status, amount],
      )
    )[0].id,
  );
}
test.before(async () => {
  db = new PGlite();
  await db.exec(readFileSync('tests/fixtures/business-base.sql', 'utf8'));
  const tx = (statements: string[]) =>
    db.transaction(async (t) => {
      for (const sql of statements) await t.query(sql);
    });
  await applySavedLookMigrations(tx);
  await applySavedLookMigrations(tx);
  const store = createBusinessStore(query);
  deps = {
    store,
    actor: async () => (actor ? ((await store.currentUser(actor)) ?? null) : null),
    settings: { enabled: true, clientLimit: 20, storageBudget: 134217728 },
  };
});
test.beforeEach(async () => {
  await db.exec('TRUNCATE appointments,inventory,users CASCADE');
  actor = S;
  for (const [id, role, name] of [
    [C, 'client', 'Client'],
    [C2, 'client', 'Other Client'],
    [S, 'stylist', 'Stylist One'],
    [S2, 'stylist', 'Stylist Two'],
    [A, 'admin', 'Admin'],
  ])
    await query('INSERT INTO users(id,email,name,password_hash,role) VALUES($1,$2,$3,$4,$5)', [
      id,
      id + '@example.invalid',
      name,
      'not-a-login',
      role,
    ]);
});
test.after(async () => db.close());
test('completion retries keep one timestamp and one set of product records without stock deduction', async () => {
  const id = await appointment();
  const inventory = String(
    (
      await query(
        "INSERT INTO inventory(product_name,brand,category,current_stock,unit_price) VALUES('Treatment','Brand A','Hair',3,900) RETURNING id",
      )
    )[0].id,
  );
  const products = [
    {
      inventoryId: inventory,
      productName: 'Treatment',
      brand: 'Brand A',
      quantity: 20,
      unit: 'ml',
      unitCost: 1.25,
    },
    { productName: 'Finish', brand: 'Custom', quantity: null, unit: null, unitCost: null },
  ];
  const responses = await Promise.all([complete(id, products), complete(id, products)]);
  for (const response of responses)
    assert.equal(response.status, 200, await response.clone().text());
  assert.deepEqual(
    (await Promise.all(responses.map(async (r) => (await r.json()).alreadyCompleted))).sort(),
    [false, true],
  );
  const record = (await deps.store.appointment(id, { id: S, role: 'stylist' }))!;
  assert.equal(record.status, 'completed');
  assert.ok(record.completedAt);
  assert.equal(record.completedBy, S);
  assert.equal((await query('SELECT count(*)::int AS n FROM appointment_product_usage'))[0].n, 2);
  assert.equal((await query('SELECT current_stock FROM inventory'))[0].current_stock, 3);
  const stamp = String(record.completedAt);
  await complete(id, []);
  assert.equal(
    String((await deps.store.appointment(id, { id: S, role: 'stylist' }))!.completedAt),
    stamp,
  );
});
test('client, unassigned stylist, foreign stylist and bad Origin cannot complete; admin requires assignment', async () => {
  const id = await appointment();
  actor = C;
  assert.equal((await complete(id)).status, 403);
  actor = S2;
  assert.equal((await complete(id)).status, 404);
  actor = S;
  assert.equal(
    (await completeAppointment(request('/x', 'POST', {}, 'https://other.invalid'), id, deps))
      .status,
    403,
  );
  const unassigned = await appointment('pending', null);
  assert.equal((await complete(unassigned)).status, 404);
  actor = A;
  assert.equal((await complete(unassigned)).status, 409);
  actor = null;
  assert.equal((await complete(id)).status, 401);
});
test('invalid products roll back completion and all usage; missing catalog items have a clear conflict', async () => {
  const id = await appointment();
  for (const product of [
    { productName: 'X', quantity: -1, unit: 'ml' },
    { productName: 'X', quantity: 2 },
    { productName: 'X', unitCost: 5 },
    { productName: 'X', quantity: 0.0001, unit: 'ml' },
    { productName: 'X', quantity: 1, unit: 'unknown' },
    { productName: 'X', unitCost: 0.001, quantity: 1, unit: 'ml' },
    { productName: 'X', stylistId: S2 },
  ])
    assert.equal((await complete(id, [product])).status, 400);
  assert.equal((await complete(id, [{ inventoryId: S2, productName: 'Missing' }])).status, 409);
  assert.equal(
    (await query('SELECT status FROM appointments WHERE id=$1', [id]))[0].status,
    'confirmed',
  );
  // Exercise transaction rollback below the HTTP validator as well.
  await assert.rejects(
    deps.store.complete(id, { id: S, role: 'stylist' }, [
      { productName: 'Valid' },
      { productName: 'Invalid', quantity: -1, unit: 'ml' },
    ]),
  );
  assert.equal(
    (await query('SELECT status FROM appointments WHERE id=$1', [id]))[0].status,
    'confirmed',
  );
  assert.equal((await query('SELECT count(*)::int AS n FROM appointment_product_usage'))[0].n, 0);
});
test('closed bookings cannot reopen, change attribution or be deleted; admin amount correction remains available', async () => {
  const id = await appointment();
  await complete(id);
  for (const payload of [
    { status: 'confirmed' },
    { stylistId: S2 },
    { appointmentDate: '2031-01-01T00:00:00Z' },
  ]) {
    actor = A;
    assert.equal((await bookingApi(request('/x', 'PATCH', payload), id, deps)).status, 409);
  }
  assert.equal((await bookingApi(request('/x', 'DELETE'), id, deps)).status, 409);
  assert.equal(
    (await bookingApi(request('/x', 'PATCH', { totalPrice: 225 }), id, deps)).status,
    200,
  );
  assert.equal((await query('SELECT total_price FROM appointments'))[0].total_price, 225);
  await assert.rejects(query('UPDATE appointments SET stylist_id=$2 WHERE id=$1', [id, S2]));
  await assert.rejects(query('DELETE FROM appointments WHERE id=$1', [id]));
  const cancelled = await appointment('cancelled');
  actor = S;
  assert.equal((await complete(cancelled)).status, 409);
});
test('one verified review derives owner/stylist, is retry-safe and rejects a different second review', async () => {
  const id = await appointment();
  await complete(id);
  actor = C;
  const responses = await Promise.all([review(id), review(id)]);
  assert.deepEqual(responses.map((r) => r.status).sort(), [200, 201]);
  assert.equal((await review(id, 1, 'Changed')).status, 409);
  assert.deepEqual(
    (await query('SELECT client_id,stylist_id,rating FROM appointment_reviews'))[0],
    { client_id: C, stylist_id: S, rating: 5 },
  );
  actor = C2;
  assert.equal((await review(id)).status, 404);
  actor = S;
  assert.equal((await review(id)).status, 403);
  actor = C;
  assert.equal((await review(id, 6)).status, 400);
  assert.equal((await review(id, 3, 'x'.repeat(1001))).status, 400);
  assert.equal(
    (await appointmentReview(request('/x', 'POST', { rating: 5, stylistId: S2 }), id, deps)).status,
    400,
  );
  assert.equal(
    (
      await appointmentReview(
        request('/x', 'POST', { rating: 5 }, 'https://other.invalid'),
        id,
        deps,
      )
    ).status,
    403,
  );
});
test('pending, cancelled and legacy unassigned services cannot be reviewed; legacy completed dates stay unknown', async () => {
  actor = C;
  for (const status of ['pending', 'cancelled'])
    assert.equal((await review(await appointment(status))).status, 409);
  const legacy = await appointment('completed', null);
  assert.equal((await review(legacy)).status, 409);
  assert.equal(
    (await deps.store.appointment(legacy, { id: C, role: 'client' }))!.completedAt,
    null,
  );
  const assignedLegacy = await appointment('completed', S);
  assert.equal((await review(assignedLegacy)).status, 201);
  assert.equal(
    (await deps.store.appointment(assignedLegacy, { id: C, role: 'client' }))!.completedAt,
    null,
  );
});
test('catalog rename/deletion preserves recorded brand/product/cost; clients cannot see material cost', async () => {
  const item = String(
    (
      await query(
        "INSERT INTO inventory(product_name,brand,category,current_stock) VALUES('Original','Brand A','Hair',2) RETURNING id",
      )
    )[0].id,
  );
  const id = await appointment();
  await complete(id, [
    {
      inventoryId: item,
      productName: 'Original',
      brand: 'Brand A',
      quantity: 2.5,
      unit: 'g',
      unitCost: 0.75,
    },
  ]);
  await query("UPDATE inventory SET product_name='Renamed',brand='Different' WHERE id=$1", [item]);
  await query('DELETE FROM inventory WHERE id=$1', [item]);
  const staff = (await deps.store.appointment(id, { id: S, role: 'stylist' }))!;
  assert.equal((staff.products as any[])[0].productName, 'Original');
  assert.equal((staff.products as any[])[0].brand, 'Brand A');
  assert.equal((staff.products as any[])[0].inventoryId, null);
  assert.equal((staff.products as any[])[0].unitCost, 0.75);
  const client = (await deps.store.appointment(id, { id: C, role: 'client' }))!;
  assert.equal((client.products as any[])[0].unitCost, null);
  assert.equal(await deps.store.appointment(id, { id: C2, role: 'client' }), undefined);
  assert.equal(await deps.store.appointment(id, { id: S2, role: 'stylist' }), undefined);
});
test('performance counts appointments once despite multiple products; ratings, unpriced and Manila boundaries are correct', async () => {
  const id = await appointment('confirmed', S, 180, '2030-10-16 16:00:00');
  await complete(id, [{ productName: 'A' }, { productName: 'B' }, { productName: 'C' }]);
  actor = C;
  await review(id, 4);
  const second = await appointment('completed', S, null, '2030-10-17 15:59:59');
  await review(second, 2, null);
  await appointment('completed', S, 999, '2030-10-17 16:00:00');
  await appointment('pending', S, 777);
  actor = A;
  const response = await stylistPerformance(
    request('/api/admin/stylist-performance?from=2030-10-17&to=2030-10-17', 'GET'),
    deps,
  );
  assert.equal(response.status, 200, await response.clone().text());
  const report = await response.json();
  const first = report.stylists.find((s: any) => s.id === S);
  const unrated = report.stylists.find((s: any) => s.id === S2);
  assert.equal(first.completed, 2);
  assert.equal(Number(first.amount), 180);
  assert.equal(first.unpriced, 1);
  assert.equal(first.reviews, 2);
  assert.equal(first.rating, 3);
  assert.equal(unrated.rating, null);
  assert.equal(unrated.completed, 0);
  const daily = await dailyServices(
    request('/api/admin/daily-services?from=2030-10-17&to=2030-10-17', 'GET'),
    deps,
  );
  assert.equal(Number((await daily.json()).amount), 180);
  actor = S;
  assert.equal((await stylistPerformance(request('/x', 'GET'), deps)).status, 403);
  actor = A;
  assert.equal(
    (await stylistPerformance(request('/x?from=2030-01-01&to=2030-03-01', 'GET'), deps)).status,
    400,
  );
});
test('completion and cancellation competing requests never leave usage on a cancelled appointment', async () => {
  const id = await appointment();
  await Promise.all([
    complete(id, [{ productName: 'Actual' }]),
    bookingApi(request('/x', 'PATCH', { status: 'cancelled' }), id, deps),
  ]);
  const current = (await query('SELECT status FROM appointments WHERE id=$1', [id]))[0];
  const usage = Number(
    (
      await query(
        'SELECT count(*)::int AS n FROM appointment_product_usage WHERE appointment_id=$1',
        [id],
      )
    )[0].n,
  );
  assert.ok(
    (current.status === 'completed' && usage === 1) ||
      (current.status === 'cancelled' && usage === 0),
  );
});
