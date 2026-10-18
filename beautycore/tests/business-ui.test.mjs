import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';
import { PGlite } from '@electric-sql/pglite';
import sharp from 'sharp';
import React from 'react';
const dom = new JSDOM('<!doctype html><html><body></body></html>', {
  url: 'http://localhost:3000',
  pretendToBeVisual: true,
});
for (const name of [
  'window',
  'document',
  'HTMLElement',
  'HTMLDialogElement',
  'HTMLInputElement',
  'Event',
  'MouseEvent',
  'getComputedStyle',
])
  Object.defineProperty(globalThis, name, {
    value: dom.window[name],
    configurable: true,
    writable: true,
  });
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
globalThis.self = window;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
globalThis.confirm = () => true;
window.matchMedia = () => ({
  matches: false,
  addListener() {},
  removeListener() {},
  addEventListener() {},
  removeEventListener() {},
});
HTMLDialogElement.prototype.showModal = function () {
  this.setAttribute('open', '');
};
HTMLDialogElement.prototype.close = function () {
  this.removeAttribute('open');
};
const { render, screen, fireEvent, cleanup, waitFor } = await import('@testing-library/react');
const { AppRouterContext } =
  await import('next/dist/shared/lib/app-router-context.shared-runtime.js');
const { SearchParamsContext, PathnameContext } =
  await import('next/dist/shared/lib/hooks-client-context.shared-runtime.js');
// Node's CJS default wrapper differs from Next's bundler. Normalize the real framework exports in this DOM harness only.
for (const path of ['next/image', 'next/link']) {
  const module = await import(path + '.js');
  test.mock.module(path, { defaultExport: module.default.default ?? module.default });
}
const { AuthProvider } = await import('../context/AuthContext.tsx');
const { SavedLookActions } = await import('../components/saved-look-actions.tsx');
const { default: NailsPage } = await import('../app/client/nail-studio/page.tsx');
const { default: SavedLooksPage } = await import('../app/client/saved-looks/page.tsx');
const { default: BookingForm } = await import('../app/(public)/booking/booking-form.tsx');
const { default: StylistPage } = await import('../app/stylist/appointments/page.tsx');
const { DailyServices } = await import('../components/daily-services.tsx');
const { default: AdminAppointments } = await import('../app/admin/appointments/page.tsx');
const { bookingApi, savedLooks, dailyServices } = await import('../lib/business/api.ts');
const { createBusinessStore } = await import('../lib/business/store.ts');
const { default: catalog } = await import('../lib/business/style-catalog.json', {
  with: { type: 'json' },
});
const C = '11111111-1111-4111-8111-111111111111',
  S = '33333333-3333-4333-8333-333333333333',
  A = '55555555-5555-4555-8555-555555555555';
let db,
  deps,
  actor = C,
  result,
  png,
  calls = [],
  pushes = [];
const originalFetch = globalThis.fetch;
const router = {
  push: (path) => pushes.push(path),
  replace: (path) => pushes.push(path),
  prefetch: async () => {},
  back() {},
  forward() {},
  refresh() {},
};
const query = async (text, values = []) => (await db.query(text, values)).rows;
function mount(Component, props = {}, params = '', auth = false) {
  let content = React.createElement(Component, props);
  if (auth) content = React.createElement(AuthProvider, null, content);
  return render(
    React.createElement(
      AppRouterContext.Provider,
      { value: router },
      React.createElement(
        SearchParamsContext.Provider,
        { value: new URLSearchParams(params) },
        content,
      ),
    ),
  );
}
async function transport(input, init = {}) {
  const url = new URL(String(input), 'http://localhost:3000');
  const method = init.method ?? 'GET';
  calls.push({ path: url.pathname, method, body: init.body });
  if (url.origin !== 'http://localhost:3000')
    throw new Error('External requests are forbidden in this fixture.');
  if (url.pathname === '/api/auth/session') {
    const user = actor
      ? (await query('SELECT id,name,email,role,avatar FROM users WHERE id=$1', [actor]))[0]
      : null;
    return Response.json({ user });
  }
  if (url.pathname === '/api/stylists')
    return Response.json({
      stylists: await query("SELECT id,name FROM users WHERE role='stylist'"),
    });
  if (url.pathname === '/api/ai/features/nails/styles')
    return Response.json(
      Object.entries(catalog.nails).map(([id, info]) => ({
        id,
        name: info.name,
        description: 'Fixture style',
        status: 'available',
      })),
    );
  if (url.pathname === '/api/ai/features/nails/generate') return Response.json(result);
  const headers = new Headers(init.headers);
  if (method !== 'GET') headers.set('origin', 'http://localhost:3000');
  const req = new Request(url, { ...init, method, headers });
  if (url.pathname.startsWith('/api/saved-looks')) {
    const parts = url.pathname.split('/').filter(Boolean);
    return savedLooks(req, parts[2], parts[3] === 'image', deps);
  }
  if (url.pathname.startsWith('/api/appointments'))
    return bookingApi(req, url.pathname.split('/')[3], deps);
  if (url.pathname === '/api/admin/daily-services') return dailyServices(req, deps);
  throw new Error('Unexpected fixture request: ' + method + ' ' + url.pathname);
}
test.before(async () => {
  db = new PGlite();
  await db.exec(readFileSync('tests/fixtures/business-base.sql', 'utf8'));
  for (const file of [
    '0002_saved_looks.sql',
    '0003_saved_look_admission.sql',
    '0004_look_details.sql',
  ])
    await db.exec(readFileSync('db/migrations/' + file, 'utf8'));
  png = await sharp({ create: { width: 64, height: 64, channels: 3, background: '#e1c9c2' } })
    .png()
    .toBuffer();
  result = {
    status: 'completed',
    style: {
      id: 'nude_pink',
      name: 'Nude Pink Gloss',
      description: 'Fixture',
      status: 'available',
    },
    image: {
      data_url: 'data:image/png;base64,' + png.toString('base64'),
      content_type: 'image/png',
      width: 64,
      height: 64,
    },
  };
  const store = createBusinessStore(query);
  deps = {
    store,
    actor: async () => (actor ? ((await store.currentUser(actor)) ?? null) : null),
    settings: { enabled: true, clientLimit: 20, storageBudget: 128 * 1024 * 1024 },
  };
  globalThis.fetch = transport;
});
test.beforeEach(async () => {
  cleanup();
  calls = [];
  pushes = [];
  actor = C;
  deps.settings.enabled = true;
  await db.exec('TRUNCATE appointments,ai_generations,client_profiles,users CASCADE');
  for (const [id, role, name] of [
    [C, 'client', 'Client One'],
    [S, 'stylist', 'Stylist One'],
    [A, 'admin', 'Admin'],
  ])
    await query('INSERT INTO users(id,email,name,password_hash,role) VALUES($1,$2,$3,$4,$5)', [
      id,
      role + '@example.invalid',
      name,
      'not-a-login',
      role,
    ]);
});
test.afterEach(() => cleanup());
test.after(async () => {
  globalThis.fetch = originalFetch;
  await db.close();
  dom.window.close();
});
test('standalone Nails generates once, saves once, and Book reuses the durable saved look', async () => {
  mount(NailsPage);
  await screen.findByText('Nude Pink Gloss');
  fireEvent.change(screen.getByLabelText('Choose a hand photo'), {
    target: { files: [new File([png], 'hand.png', { type: 'image/png' })] },
  });
  fireEvent.click(screen.getByText('Nude Pink Gloss'));
  fireEvent.click(screen.getByRole('button', { name: /Try this style/ }));
  await screen.findByRole('button', { name: 'Save Look' });
  fireEvent.click(screen.getByRole('button', { name: 'Save Look' }));
  fireEvent.click(screen.getByRole('button', { name: /Saving/ }));
  await screen.findByRole('button', { name: 'Saved to My Looks' });
  fireEvent.click(screen.getByRole('button', { name: 'Book This Look' }));
  await waitFor(() => assert.equal(pushes.length, 1));
  assert.match(pushes[0], /^\/booking\?look=/);
  assert.equal(calls.filter((c) => c.path.endsWith('/generate')).length, 1);
  assert.equal(calls.filter((c) => c.path === '/api/saved-looks' && c.method === 'POST').length, 1);
  assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n, 1);
});
test('save failure preserves the preview, permits manual save retry and never generates', async () => {
  deps.settings.enabled = false;
  mount(SavedLookActions, { feature: 'nails', result });
  fireEvent.click(screen.getByRole('button', { name: 'Save Look' }));
  assert.match(
    (await screen.findByRole('alert')).textContent,
    /preview and download remain available/,
  );
  assert.equal(pushes.length, 0);
  deps.settings.enabled = true;
  fireEvent.click(screen.getByRole('button', { name: 'Save Look' }));
  await screen.findByRole('button', { name: 'Saved to My Looks' });
  assert.equal(
    calls.some((c) => c.path.includes('/generate')),
    false,
  );
});
test('saved gallery reload and removal use account data and preserve booked references', async () => {
  await transport('/api/saved-looks', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      feature: 'nails',
      styleId: result.style.id,
      image: result.image.data_url,
      status: 'completed',
      sourceKind: 'manual',
    }),
  });
  mount(SavedLooksPage);
  await screen.findByText('Nude Pink Gloss');
  const href = screen.getByRole('link', { name: 'Book This Look' }).getAttribute('href');
  assert.match(href, /look=/);
  cleanup();
  mount(SavedLooksPage);
  await screen.findByText('Nude Pink Gloss');
  fireEvent.click(screen.getByRole('button', { name: 'Remove from Saved' }));
  await screen.findByText(/No saved looks yet/);
  assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n, 1);
});
test('look-aware booking and assigned stylist preview complete against the same database', async () => {
  const save = await transport('/api/saved-looks', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      feature: 'nails',
      styleId: result.style.id,
      image: result.image.data_url,
      status: 'completed',
      sourceKind: 'consultation',
    }),
  });
  const identity = (await save.json()).look.id;
  mount(BookingForm, {}, 'look=' + identity, true);
  await screen.findByText('Booking with Nude Pink Gloss');
  fireEvent.change(screen.getByLabelText('Service', { exact: true }), {
    target: { value: 'Gel Manicure' },
  });
  fireEvent.change(screen.getByLabelText(/Date \(Philippine time\)/), {
    target: { value: '2030-10-17' },
  });
  fireEvent.change(screen.getByLabelText('Time', { exact: true }), { target: { value: '10:00' } });
  fireEvent.change(screen.getByLabelText(/Preferred Stylist/), { target: { value: S } });
  fireEvent.click(screen.getByRole('button', { name: 'Confirm Booking' }));
  await screen.findByText('Appointment booked');
  const appointment = (
    await query('SELECT ai_generation_id,total_price,appointment_date FROM appointments')
  )[0];
  assert.equal(appointment.ai_generation_id, identity);
  assert.equal(appointment.total_price, 350);
  assert.match(String(appointment.appointment_date), /02:00:00/);
  cleanup();
  actor = S;
  mount(StylistPage);
  await screen.findByRole('heading', { name: 'Gel Manicure' });
  fireEvent.click(screen.getByRole('button', { name: /View requested look/ }));
  assert.ok(screen.getByRole('dialog').hasAttribute('open'));
  assert.match(screen.getByRole('dialog').textContent, /Nude Pink Gloss/);
  fireEvent.click(screen.getByRole('button', { name: 'Complete' }));
  await waitFor(async () =>
    assert.equal((await query('SELECT status FROM appointments'))[0].status, 'completed'),
  );
  cleanup();
  actor = A;
  mount(DailyServices);
  fireEvent.change(screen.getByLabelText('From date'), { target: { value: '2030-10-17' } });
  fireEvent.change(screen.getByLabelText('Through date'), { target: { value: '2030-10-17' } });
  await screen.findByText('Gel Manicure', { selector: 'td' });
  assert.match(document.body.textContent, /₱350/);
  assert.match(document.body.textContent, /Stylist One/);
});
test('placeholder results have no account save or booking action', () => {
  mount(SavedLookActions, { feature: 'nails', result: { ...result, status: 'placeholder' } });
  assert.equal(screen.queryByRole('button', { name: 'Save Look' }), null);
  assert.equal(screen.queryByRole('button', { name: 'Book This Look' }), null);
});
test('anonymous look-aware booking preserves its look in the login link', async () => {
  actor = null;
  const identity = '66666666-6666-4666-8666-666666666666';
  mount(BookingForm, {}, 'look=' + identity, true);
  const link = await screen.findByText('Sign in to view your selected look and finish booking.');
  assert.equal(
    link.getAttribute('href'),
    '/login?redirect=' + encodeURIComponent('/booking?look=' + identity),
  );
});

test('admin can assign a stylist and confirm the recorded amount through the existing booking UI', async () => {
  await transport('/api/appointments', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      serviceName: 'Makeup Application',
      serviceType: 'makeup',
      appointmentDate: '2030-10-17T02:00:00Z',
    }),
  });
  actor = A;
  mount(AdminAppointments);
  await screen.findByText('Makeup Application');
  await waitFor(() => assert.ok(screen.getByRole('option', { name: 'Stylist One' })));
  fireEvent.change(screen.getByLabelText('Assigned stylist'), { target: { value: S } });
  fireEvent.change(screen.getByLabelText('Recorded amount (whole pesos)'), {
    target: { value: '450' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Save assignment / amount' }));
  await waitFor(async () => {
    const row = (await query('SELECT stylist_id,total_price FROM appointments'))[0];
    assert.equal(row.stylist_id, S);
    assert.equal(row.total_price, 450);
  });
});

test('look information displays named service prices and labels saved/current estimates honestly', async () => {
  const { LookInformation } = await import('../components/look-information.tsx');
  const { snapshotLookInformation } = await import('../lib/business/look-information.ts');
  render(React.createElement(LookInformation, { feature: 'nails', styleId: 'french_tip' }));
  assert.ok(screen.getByText('Natural pink nails with white tips.'));
  assert.ok(screen.getByText('Nail Art (per nail)'));
  assert.ok(screen.getByText('From ₱50'));
  cleanup();
  render(React.createElement(LookInformation, { feature: 'makeup', styleId: 'natural_makeup' }));
  assert.ok(screen.getByText('Price to be confirmed by the salon.'));
  assert.equal(screen.queryByText(/₱500/), null);
  cleanup();
  render(
    React.createElement(LookInformation, {
      saved: true,
      feature: 'hairstyle',
      styleId: 'crew_cut',
    }),
  );
  assert.ok(screen.getByText('Current service estimate; the original estimate was not recorded.'));
  cleanup();
  render(
    React.createElement(LookInformation, {
      saved: true,
      feature: 'hairstyle',
      styleId: 'crew_cut',
      details: snapshotLookInformation('hairstyle', 'crew_cut'),
    }),
  );
  assert.ok(screen.getByText('Estimated cost when saved'));
  assert.equal(
    screen.queryByText('Current service estimate; the original estimate was not recorded.'),
    null,
  );
});

test('admin navigation removes Market Trends and keeps Finance and Dashboard', async () => {
  const { default: AdminSidebar } = await import('../components/AdminSidebar.tsx');
  actor = A;
  mount(
    () =>
      React.createElement(
        PathnameContext.Provider,
        { value: '/admin/dashboard' },
        React.createElement(AdminSidebar),
      ),
    {},
    '',
    true,
  );
  assert.equal(screen.queryByRole('link', { name: 'Market Trends' }), null);
  assert.ok(screen.getByRole('link', { name: 'Finance' }));
  assert.ok(screen.getByRole('link', { name: 'Dashboard' }));
});
