import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PGlite } from '@electric-sql/pglite';
import sharp from 'sharp';
import { bookingApi, dailyServices, savedLooks, type Dependencies } from '../lib/business/api';
import { createBusinessStore } from '../lib/business/store';
import { validateLook, MAX_SAVE_BODY, salonDateTime, salonDay } from '../lib/business/core';
import { allServices, parsePrice } from '../lib/services';
const C = '11111111-1111-4111-8111-111111111111',
  OTHER = '22222222-2222-4222-8222-222222222222',
  S = '33333333-3333-4333-8333-333333333333',
  S2 = '44444444-4444-4444-8444-444444444444',
  A = '55555555-5555-4555-8555-555555555555';
const ORIGIN = 'http://localhost:3000';
let db: PGlite;
let deps: Dependencies;
let actor: string | null = C;
let image: string;
const query = async (text: string, values: unknown[] = []) =>
  (await db.query<Record<string, unknown>>(text, values)).rows;
function request(path: string, method = 'GET', body?: unknown, origin: string | null = ORIGIN) {
  const headers = new Headers();
  if (method !== 'GET' && origin) headers.set('Origin', origin);
  if (body !== undefined) headers.set('Content-Type', 'application/json');
  return new Request(ORIGIN + path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
const saveBody = (feature = 'hairstyle', styleId = 'crew_cut', img = image) => ({
  feature,
  styleId,
  image: img,
  status: 'completed',
  sourceKind: 'manual',
});
const save = async (body = saveBody()) =>
  savedLooks(request('/api/saved-looks', 'POST', body), undefined, false, deps);
async function saved() {
  const response = await save();
  assert.equal(response.status, 201, await response.clone().text());
  return (await response.json()).look.id as string;
}
const booking = (lookId?: string) => ({
  serviceName: "Men's Cut",
  serviceType: 'hair',
  appointmentDate: '2030-10-17T02:00:00Z',
  stylistId: S,
  totalPrice: 1,
  ...(lookId ? { lookId } : {}),
});
async function book(lookId?: string) {
  const response = await bookingApi(
    request('/api/appointments', 'POST', booking(lookId)),
    undefined,
    deps,
  );
  assert.equal(response.status, 201, await response.clone().text());
  return (await response.json()).appointment.id as string;
}
test.before(async () => {
  db = new PGlite();
  await db.exec(readFileSync('tests/fixtures/business-base.sql', 'utf8'));
  await query('INSERT INTO users(id,email,name,password_hash) VALUES($1,$2,$3,$4)', [
    C,
    'legacy@example.invalid',
    'Legacy Client',
    'not-a-login',
  ]);
  await query(
    "INSERT INTO ai_generations(client_id,source_image_url,prompt_text,style_type) VALUES($1,'legacy-source','legacy-prompt','hair')",
    [C],
  );
  for (const file of [
    '0002_saved_looks.sql',
    '0003_saved_look_admission.sql',
    '0004_look_details.sql',
  ])
    await db.exec(readFileSync('db/migrations/' + file, 'utf8'));
  assert.equal(
    (await query('SELECT source_image_url,saved_at FROM ai_generations'))[0].source_image_url,
    'legacy-source',
  );
  assert.equal(
    (await query('SELECT source_image_url,saved_at FROM ai_generations'))[0].saved_at,
    null,
  );
  for (const file of [
    '0002_saved_looks.sql',
    '0003_saved_look_admission.sql',
    '0004_look_details.sql',
  ])
    await db.exec(readFileSync('db/migrations/' + file, 'utf8'));
  image =
    'data:image/png;base64,' +
    (
      await sharp({ create: { width: 64, height: 64, channels: 3, background: '#c09090' } })
        .png()
        .toBuffer()
    ).toString('base64');
  const store = createBusinessStore(query);
  deps = {
    actor: async () => (actor ? ((await store.currentUser(actor)) ?? null) : null),
    store,
    settings: { enabled: true, clientLimit: 20, storageBudget: 128 * 1024 * 1024 },
    now: () => Date.parse('2026-10-17T00:00:00Z'),
  };
});
test.after(async () => db?.close());
test.beforeEach(async () => {
  await db.exec('TRUNCATE appointments,ai_generations,client_profiles,users CASCADE');
  for (const [id, role, name] of [
    [C, 'client', 'Client One'],
    [OTHER, 'client', 'Client Two'],
    [S, 'stylist', 'Stylist One'],
    [S2, 'stylist', 'Stylist Two'],
    [A, 'admin', 'Admin'],
  ])
    await query('INSERT INTO users(id,email,name,password_hash,role) VALUES($1,$2,$3,$4,$5)', [
      id,
      name.replace(/ /g, '') + '@example.invalid',
      name,
      'not-a-login',
      role,
    ]);
  actor = C;
  deps.settings = { enabled: true, clientLimit: 20, storageBudget: 128 * 1024 * 1024 };
});
test('real PostgreSQL migration is repeatable and saved image admission is idempotent', async () => {
  const first = await saved();
  const results = await Promise.all([save(), save()]);
  for (const response of results) {
    assert.equal(response.status, 200);
    assert.equal((await response.json()).look.id, first);
  }
  assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n, 1);
  const row = (await query('SELECT source_image_url,prompt_text FROM ai_generations'))[0];
  assert.equal(row.source_image_url, null);
  assert.equal(row.prompt_text, null);
});
test('all three features and both Nails routing categories save without calling AI', async () => {
  for (const [feature, style] of [
    ['hairstyle', 'bob_hair'],
    ['makeup', 'soft_glam'],
    ['nails', 'classic_red'],
    ['nails', 'nude_pink'],
  ]) {
    const response = await save({ ...saveBody(feature, style), sourceKind: 'consultation' });
    assert.equal(response.status, 201, await response.clone().text());
  }
  assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n, 4);
});
test('saved image access is private, metadata-only and survives independent store instances', async () => {
  const identity = await saved();
  let response = await savedLooks(request('/api/saved-looks'), undefined, false, deps);
  const body = await response.json();
  assert.equal(body.looks.length, 1);
  assert.equal(JSON.stringify(body).includes('base64'), false);
  const otherStore = createBusinessStore(query);
  assert.equal((await otherStore.getLook(identity, C))?.id, identity);
  response = await savedLooks(
    request('/api/saved-looks/' + identity + '/image'),
    identity,
    true,
    deps,
  );
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'private, no-store');
  assert.equal(response.headers.get('content-type'), 'image/png');
  actor = OTHER;
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity), identity, false, deps)).status,
    404,
  );
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity + '/image'), identity, true, deps))
      .status,
    404,
  );
  actor = null;
  assert.equal((await save()).status, 401);
});
test('fresh role checks and exact Origin protect mutations; disabled saves fail clearly', async () => {
  assert.equal(
    (
      await savedLooks(
        request('/api/saved-looks', 'POST', saveBody(), 'https://other.example'),
        undefined,
        false,
        deps,
      )
    ).status,
    403,
  );
  assert.equal(
    (
      await savedLooks(
        request('/api/saved-looks', 'POST', saveBody(), null),
        undefined,
        false,
        deps,
      )
    ).status,
    403,
  );
  await query("UPDATE users SET role='stylist' WHERE id=$1", [C]);
  assert.equal((await save()).status, 403);
  actor = OTHER;
  deps.settings.enabled = false;
  assert.equal((await save()).status, 503);
});
test('image bytes, malformed payloads, unknown styles and overlarge streams are rejected', async () => {
  for (const patch of [
    { image: 'https://other.example/image.png' },
    { image: 'data:image/png;base64,AAAA' },
    { styleId: '__proto__' },
    { status: 'placeholder' },
    { clientId: OTHER },
    { image: 'data:image/jpeg;base64,' + image.split(',')[1] },
  ])
    assert.ok((await save({ ...saveBody(), ...patch })).status >= 400);
  const response = await savedLooks(
    new Request(ORIGIN + '/api/saved-looks', {
      method: 'POST',
      headers: {
        origin: ORIGIN,
        'content-type': 'application/json',
        'content-length': String(MAX_SAVE_BODY + 1),
      },
      body: '{}',
    }),
    undefined,
    false,
    deps,
  );
  assert.equal(response.status, 413);
  const jpeg =
    'data:image/jpeg;base64,' +
    (
      await sharp({ create: { width: 48, height: 48, channels: 3, background: 'pink' } })
        .jpeg()
        .toBuffer()
    ).toString('base64');
  assert.equal((await validateLook({ ...saveBody(), image: jpeg })).imageBytes > 0, true);
});
test('client limit and storage budget are atomic and repeated saves still succeed when full', async () => {
  deps.settings.clientLimit = 1;
  const identity = await saved();
  const blocked = await save(saveBody('nails', 'nude_pink'));
  assert.equal(blocked.status, 409);
  assert.equal((await save()).status, 200);
  await savedLooks(
    request('/api/saved-looks/' + identity, 'PATCH', { saved: false }),
    identity,
    false,
    deps,
  );
  assert.equal((await save()).status, 200);
  deps.settings.clientLimit = 20;
  deps.settings.storageBudget = 1048576;
  await query(
    "INSERT INTO ai_generations(client_id,source_image_url,prompt_text,style_type) VALUES($1,repeat('x',1048576),'legacy','hair')",
    [OTHER],
  );
  assert.equal((await save(saveBody('nails', 'nude_pink'))).status, 507);
  assert.equal(
    (await query('SELECT count(*)::int AS n FROM ai_generations WHERE result_hash IS NOT NULL'))[0]
      .n,
    1,
  );
});
test('booking derives catalog price and rejects foreign or incompatible look references', async () => {
  const identity = await saved();
  const bookingId = await book(identity);
  assert.equal(
    (
      await query('SELECT total_price,ai_generation_id FROM appointments WHERE id=$1', [bookingId])
    )[0].total_price,
    180,
  );
  actor = OTHER;
  assert.equal(
    (await bookingApi(request('/api/appointments', 'POST', booking(identity)), undefined, deps))
      .status,
    404,
  );
  actor = C;
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments', 'POST', {
          ...booking(identity),
          serviceName: 'Gel Manicure',
          serviceType: 'nail',
        }),
        undefined,
        deps,
      )
    ).status,
    400,
  );
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments', 'POST', { ...booking(), clientId: OTHER }),
        undefined,
        deps,
      )
    ).status,
    403,
  );
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments', 'POST', { ...booking(), stylistId: OTHER }),
        undefined,
        deps,
      )
    ).status,
    400,
  );
  await book();
  assert.equal((await query('SELECT count(*)::int AS n FROM appointments'))[0].n, 2);
});
test('removed looks remain on booked appointments; image access follows stylist assignment', async () => {
  const identity = await saved();
  const bookingId = await book(identity);
  assert.equal(
    (
      await savedLooks(
        request('/api/saved-looks/' + identity, 'PATCH', { saved: false }),
        identity,
        false,
        deps,
      )
    ).status,
    200,
  );
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity), identity, false, deps)).status,
    404,
  );
  actor = S;
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity + '/image'), identity, true, deps))
      .status,
    200,
  );
  const rows = (await (await bookingApi(request('/api/appointments'), undefined, deps)).json())
    .appointments;
  assert.equal(rows[0].look.id, identity);
  assert.equal(JSON.stringify(rows).includes('base64'), false);
  actor = S2;
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity + '/image'), identity, true, deps))
      .status,
    404,
  );
  actor = A;
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments/' + bookingId, 'PATCH', { stylistId: S2, totalPrice: 450 }),
        bookingId,
        deps,
      )
    ).status,
    200,
  );
  actor = S;
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity + '/image'), identity, true, deps))
      .status,
    404,
  );
  actor = S2;
  assert.equal(
    (await savedLooks(request('/api/saved-looks/' + identity + '/image'), identity, true, deps))
      .status,
    200,
  );
});
test('database blocks cross-client references and modification of saved content', async () => {
  const identity = await saved();
  await assert.rejects(
    query('UPDATE ai_generations SET generated_image_url=$2 WHERE id=$1', [identity, 'tampered']),
  );
  await assert.rejects(
    query(
      "INSERT INTO appointments(client_id,service_name,service_type,appointment_date,ai_generation_id) VALUES($1,'Cut','hair','2030-01-01',$2)",
      [OTHER, identity],
    ),
  );
});
test('clients cannot patch notes, prices, assignment or look; stylists cannot change others', async () => {
  const identity = await saved();
  const bookingId = await book(identity);
  for (const patch of [
    { notes: 'changed' },
    { totalPrice: 0 },
    { stylistId: S2 },
    { aiGenerationId: null },
    { lookId: null },
  ])
    assert.equal(
      (await bookingApi(request('/api/appointments/' + bookingId, 'PATCH', patch), bookingId, deps))
        .status,
      403,
    );
  actor = S2;
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments/' + bookingId, 'PATCH', { status: 'completed' }),
        bookingId,
        deps,
      )
    ).status,
    404,
  );
  actor = S;
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments/' + bookingId, 'PATCH', { status: 'completed' }),
        bookingId,
        deps,
      )
    ).status,
    200,
  );
  actor = C;
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments/' + bookingId, 'PATCH', { status: 'cancelled' }),
        bookingId,
        deps,
      )
    ).status,
    403,
  );
});
test('Makeup bookings keep unknown prices and labels distinct from free services', async () => {
  const response = await save(saveBody('makeup', 'soft_glam'));
  const look = (await response.json()).look;
  const result = await bookingApi(
    request('/api/appointments', 'POST', {
      ...booking(look.id),
      serviceName: 'Makeup Application',
      serviceType: 'makeup',
      totalPrice: 999,
    }),
    undefined,
    deps,
  );
  assert.equal(result.status, 201);
  assert.equal((await query('SELECT total_price FROM appointments'))[0].total_price, null);
  assert.equal(parsePrice('Libre'), 0);
  assert.equal(parsePrice('Price to be confirmed'), null);
  assert.equal(
    allServices.some((s) => s.serviceType === 'makeup'),
    true,
  );
});
test('daily report handles Manila midnight, all statuses, unassigned, null and zero amounts', async () => {
  for (const [when, status, amount, stylist] of [
    ['2026-10-16 15:59:59', 'completed', 999, S],
    ['2026-10-16 16:00:00', 'completed', 180, S],
    ['2026-10-17 15:59:59', 'completed', null, null],
    ['2026-10-17 03:00:00', 'pending', 500, S],
    ['2026-10-17 04:00:00', 'cancelled', 600, S2],
    ['2026-10-17 06:00:00', 'completed', 0, S2],
    ['2026-10-17 16:00:00', 'completed', 777, S],
  ])
    await query(
      "INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,'Test service','hair',$3,$4,$5)",
      [C, stylist, when, status, amount],
    );
  actor = A;
  const response = await dailyServices(
    request('/api/admin/daily-services?from=2026-10-17&to=2026-10-17'),
    deps,
  );
  assert.equal(response.status, 200, await response.clone().text());
  const report = await response.json();
  assert.equal(Number(report.amount), 180);
  assert.equal(report.total, 5);
  assert.equal(report.unpriced, 1);
  assert.equal(report.summaries.length, 3);
  assert.equal(
    report.rows.every((r: { serviceDay: string }) => r.serviceDay === '2026-10-17'),
    true,
  );
  const filtered = await (
    await dailyServices(
      request('/api/admin/daily-services?from=2026-10-17&stylist=unassigned'),
      deps,
    )
  ).json();
  assert.equal(filtered.total, 1);
  actor = C;
  assert.equal((await dailyServices(request('/api/admin/daily-services'), deps)).status, 403);
});
test('pagination does not change report totals and invalid filters cannot reach unsafe SQL', async () => {
  for (let i = 0; i < 15; i++)
    await query(
      "INSERT INTO appointments(client_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,'Test','hair','2026-10-17 01:00','completed',10)",
      [C],
    );
  actor = A;
  for (const page of [1, 2]) {
    const data = await (
      await dailyServices(request('/api/admin/daily-services?from=2026-10-17&page=' + page), deps)
    ).json();
    assert.equal(Number(data.amount), 150);
    assert.equal(data.total, 15);
    assert.equal(data.rows.length, page === 1 ? 12 : 3);
  }
  for (const suffix of [
    '?from=2026-02-30',
    '?from=2026-10-20&to=2026-10-01',
    '?from=2026-01-01&to=2026-10-17',
    '?stylist=invalid',
    '?page=0',
    '?status=invalid',
  ])
    assert.equal(
      (await dailyServices(request('/api/admin/daily-services' + suffix), deps)).status,
      400,
    );
});
test('salon date conversion is explicit regardless of browser timezone', () => {
  assert.equal(salonDateTime('2030-01-02', '00:00'), '2030-01-01T16:00:00.000Z');
  assert.equal(salonDay(new Date('2030-01-01T16:00:00Z')), '2030-01-02');
  assert.throws(() => salonDateTime('2030-02-30', '12:00'));
  assert.throws(() => salonDateTime('2030-01-02', '25:00'));
});

test('gallery pagination and Manila saved-date filters return metadata without image payloads', async () => {
  for (let i = 0; i < 13; i++) {
    const image =
      'data:image/png;base64,' +
      (
        await sharp({
          create: { width: 48, height: 48, channels: 3, background: { r: i * 10, g: 30, b: 80 } },
        })
          .png()
          .toBuffer()
      ).toString('base64');
    assert.equal((await save(saveBody('hairstyle', 'crew_cut', image))).status, 201);
  }
  const first = await (
    await savedLooks(request('/api/saved-looks?page=1&feature=hairstyle'), undefined, false, deps)
  ).json();
  const second = await (
    await savedLooks(request('/api/saved-looks?page=2&feature=hairstyle'), undefined, false, deps)
  ).json();
  assert.equal(first.total, 13);
  assert.equal(first.looks.length, 12);
  assert.equal(second.looks.length, 1);
  assert.equal(new Set([...first.looks, ...second.looks].map((row) => row.id)).size, 13);
  const empty = await (
    await savedLooks(
      request('/api/saved-looks?from=2000-01-01&to=2000-01-02'),
      undefined,
      false,
      deps,
    )
  ).json();
  assert.equal(empty.total, 0);
  assert.equal(JSON.stringify(first).includes('base64'), false);
});

test('invalid calendar dates and malformed configured origins fail closed', async () => {
  assert.equal(
    (
      await bookingApi(
        request('/api/appointments', 'POST', {
          ...booking(),
          appointmentDate: '2030-02-30T12:00:00Z',
        }),
        undefined,
        deps,
      )
    ).status,
    400,
  );
  for (const origin of ['', 'https://valid.example/path', 'http://localhost:3000']) {
    const config = { ...deps, publicOrigin: origin };
    assert.equal(
      (await savedLooks(request('/api/saved-looks', 'POST', saveBody()), undefined, false, config))
        .status,
      503,
    );
  }
});

test('save admission bounds concurrent payloads and releases capacity after completion', async () => {
  const original = deps.store;
  let started = 0;
  let release;
  let admit;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const admitted = new Promise<void>((resolve) => {
    admit = resolve;
  });
  deps.store = {
    ...original,
    save: async (...args) => {
      started++;
      if (started === 2) admit!();
      await gate;
      return original.save(...args);
    },
  };
  try {
    const first = save();
    const second = save();
    await admitted;
    assert.equal((await save()).status, 429);
    release!();
    const responses = await Promise.all([first, second]);
    assert.deepEqual(responses.map((response) => response.status).sort(), [200, 201]);
    assert.equal((await save()).status, 200);
    assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n, 1);
  } finally {
    release!();
    deps.store = original;
  }
});

test('expanded Hair looks save with server-owned descriptions and survive catalog price changes', async () => {
  const response = await save(saveBody('hairstyle', 'bun'));
  assert.equal(response.status, 201);
  const { look } = await response.json();
  assert.match(look.lookDetails.description, /gathered/);
  assert.ok(look.lookDetails.capturedAt);
  const original = look.lookDetails;
  const service = allServices.find((s) => s.name === 'Updo / Special Occasion')!;
  const oldPrice = service.price;
  try {
    service.price = '₱999';
    const read = await savedLooks(request('/api/saved-looks/' + look.id), look.id, false, deps);
    assert.deepEqual((await read.json()).look.lookDetails, original);
    const duplicate = await save(saveBody('hairstyle', 'bun'));
    assert.equal(duplicate.status, 200);
    assert.deepEqual((await duplicate.json()).look.lookDetails, original);
    const booked = await bookingApi(
      request('/api/appointments', 'POST', { ...booking(look.id), serviceName: service.name }),
      undefined,
      deps,
    );
    assert.equal(booked.status, 201);
    const rows = await deps.store.appointments({ id: S, role: 'stylist' }, false);
    assert.equal(rows[0].totalPrice, 999);
    assert.deepEqual((rows[0].look as any).lookDetails, original);
    await assert.rejects(
      query('UPDATE ai_generations SET look_details=$2::jsonb WHERE id=$1', [
        look.id,
        JSON.stringify({ ...original, description: 'Changed' }),
      ]),
      /immutable/,
    );
  } finally {
    service.price = oldPrice;
  }
});

test('clients cannot inject description/price snapshots and Makeup stays unpriced', async () => {
  assert.equal(
    (await save({ ...saveBody(), lookDetails: { description: 'Fake', price: 1 } } as any)).status,
    400,
  );
  const response = await save(saveBody('makeup', 'natural_makeup'));
  assert.equal(response.status, 201);
  const look = (await response.json()).look;
  assert.equal(look.lookDetails.quoteRequired, true);
  assert.equal(look.lookDetails.options[0].amount, null);
  assert.equal(look.lookDetails.options[0].kind, 'quote');
});

test('previous save function remains compatible and old saved looks get a current estimate fallback', async () => {
  const hash = 'b'.repeat(64);
  const inserted = await query(
    `SELECT * FROM beautycore_save_look($1,'hair','crew_cut','Crew Cut',$2,$3,1,'manual',20,134217728)`,
    [C, image, hash],
  );
  const response = await savedLooks(
    request('/api/saved-looks/' + inserted[0].look_id),
    String(inserted[0].look_id),
    false,
    deps,
  );
  assert.equal(response.status, 200);
  const look = (await response.json()).look;
  assert.equal(look.lookDetails.capturedAt, null);
  assert.equal(
    (await query('SELECT look_details FROM ai_generations WHERE id=$1', [look.id]))[0].look_details,
    null,
  );
  assert.match(look.lookDetails.description, /short/);
});
