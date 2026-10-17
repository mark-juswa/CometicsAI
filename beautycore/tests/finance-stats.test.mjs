import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PGlite } from '@electric-sql/pglite';
import { drizzle } from 'drizzle-orm/pglite';
import * as schema from '../db/schema.ts';
const pg = new PGlite();
await pg.exec(readFileSync('tests/fixtures/business-base.sql', 'utf8'));
const orm = drizzle(pg, { schema });
let role = 'admin';
test.mock.module('../db/index.ts', { namedExports: { db: orm } });
test.mock.module('../lib/business/server.ts', {
  namedExports: {
    businessDependencies: {
      actor: async () => ({ id: '55555555-5555-4555-8555-555555555555', role }),
    },
  },
});
const { GET } = await import('../app/api/admin/stats/route.ts');
test.after(async () => pg.close());
test('actual admin stats excludes pending and cancelled amounts from both headline and service totals', async () => {
  await pg.exec(
    "INSERT INTO users(id,email,name,password_hash) VALUES('11111111-1111-4111-8111-111111111111','test@example.invalid','Fixture','not-a-login')",
  );
  for (const [status, price] of [
    ['completed', 180],
    ['pending', 500],
    ['cancelled', 900],
  ])
    await pg.query(
      "INSERT INTO appointments(client_id,service_name,service_type,appointment_date,status,total_price) VALUES('11111111-1111-4111-8111-111111111111','Cut','hair',now(),$1,$2)",
      [status, price],
    );
  const response = await GET();
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.stats.totalRevenue, 180);
  assert.equal(body.topServices[0].revenue, 180);
  assert.equal(body.topServices[0].bookings, 3);
});
test('actual admin stats denies a non-admin actor', async () => {
  role = 'client';
  assert.equal((await GET()).status, 403);
});
