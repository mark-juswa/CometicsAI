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
  'CustomEvent',
  'StorageEvent',
  'getComputedStyle',
])
  Object.defineProperty(globalThis, name, {
    value: dom.window[name],
    configurable: true,
    writable: true,
  });
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
globalThis.self = window;
globalThis.localStorage = window.localStorage;
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
const { default: LoginForm } = await import('../app/(public)/login/login-form.tsx');
const { SavedLookActions } = await import('../components/saved-look-actions.tsx');
const { default: NailsPage } = await import('../app/client/nail-studio/page.tsx');
const { default: HairPage } = await import('../app/client/hair-studio/page.tsx');
const { default: MakeupPage } = await import('../app/client/makeup-studio/page.tsx');
const { BookingNotifications } = await import('../components/booking-notifications.tsx');
const { ConsultationHistory } = await import('../components/consultation-history.tsx');
const { bookingAvailability } = await import('../lib/business/booking-availability.ts');
const { bookingNotifications } = await import('../lib/business/booking-notifications.ts');
const { stylistServiceHistory } = await import('../lib/business/stylist-history.ts');
const { default: SavedLooksPage } = await import('../app/client/saved-looks/page.tsx');
const { default: BookingForm } = await import('../app/(public)/booking/booking-form.tsx');
const { default: StylistPage } = await import('../app/stylist/appointments/page.tsx');
const { DailyServices } = await import('../components/daily-services.tsx');
const { default: ConsultationPage } = await import('../app/client/ai-consultation/page.tsx');
const { default: ClientDashboard } = await import('../app/client/dashboard/page.tsx');
const { default: StylistDashboard } = await import('../app/stylist/dashboard/page.tsx');
const { default: ClientAppointments } = await import('../app/client/appointments/page.tsx');
const { StylistPerformance } = await import('../components/stylist-performance.tsx');
const { default: AdminAppointments } = await import('../app/admin/appointments/page.tsx');
const { default: AdminStylists } = await import('../app/admin/stylists/page.tsx');
const { RevenueOverview } = await import('../components/revenue-report.tsx');
const { default: PublicServices } = await import('../app/(public)/services/page.tsx');
const { default: AdminFinance } = await import('../app/admin/finance/page.tsx');
const { default: StylistClients } = await import('../app/stylist/clients/page.tsx');
const { WorkAvailability } = await import('../components/work-availability.tsx');
const { ReferenceImagePicker } = await import('../components/reference-image-picker.tsx');
const { ClientHistory } = await import('../components/client-history.tsx');
const { workAvailability } = await import('../lib/business/work-availability.ts');
const { clientHistory,clientImages,paymentHistory,consultationHistory,archiveConsultationResponse } = await import('../lib/business/customer-history.ts');
const {
  bookingApi,
  savedLooks,
  dailyServices,
  completeAppointment,
  appointmentReview,
  stylistPerformance,
} = await import('../lib/business/api.ts');
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
const consultationRows = Object.entries(catalog.nails)
  .slice(0, 3)
  .map(([id, info], index) => ({
    id: 'look-' + (index + 1),
    primary: {
      feature: 'nails',
      style_id: id,
      style_name: info.name,
      service: { name: 'Nail service' },
    },
    reason: 'Fixture preference match',
    complements: [],
  }));
const consultationState = {
  primary_service: 'nails',
  stage: 'recommended',
  conversation_status: 'ready_for_recommendation',
  photo: null,
  messages: [],
  recommendations: { recommendations: consultationRows },
  generations: [],
  selected_recommendation_id: null,
};
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
  calls.push({ path: url.pathname, method, body: init.body, search:url.search });
  if (url.origin !== 'http://localhost:3000')
    throw new Error('External requests are forbidden in this fixture.');
  if (url.pathname === '/api/auth/session') {
    const user = actor
      ? (await query('SELECT id,name,email,role,avatar FROM users WHERE id=$1', [actor]))[0]
      : null;
    return Response.json({ user });
  }
  if (url.pathname === '/api/stylists' && method==='PATCH'){
    assert.equal(actor,A);
    const body=JSON.parse(init.body);
    const rows=await query('SELECT beautycore_update_stylist($1,$2,$3,$4,$5::text[]) AS updated',[body.id,body.name,body.email,body.isActive,body.specialties]);
    return Response.json({stylist:{id:body.id},updated:rows[0].updated});
  }
  if (url.pathname === '/api/stylists')
    return Response.json({
      stylists: await query(`SELECT u.id,u.name,u.email,u.is_active AS "isActive",
        EXISTS(SELECT 1 FROM stylist_work_settings w WHERE w.stylist_id=u.id AND w.available) AS "workAvailable",
        ARRAY(SELECT service_type FROM stylist_specialties s WHERE s.stylist_id=u.id) AS specialties
        FROM users u WHERE u.role='stylist'`),
    });
  if (/^\/api\/ai\/features\/(hairstyle|makeup|nails)\/styles$/.test(url.pathname))
    return Response.json(
      Object.entries(catalog[url.pathname.split('/')[4]]).map(([id, info]) => ({
        id,
        name: info.name,
        description: 'Fixture style',
        status: 'available',
      })),
    );
  if (url.pathname === '/api/ai/mode') return Response.json({ provider: 'deterministic' });
  if (url.pathname === '/api/ai/consultations')
    return Response.json({ ...consultationState, handle: 'fixture-handle' });
  if (['/api/ai/consultations/photo', '/api/ai/consultations/state'].includes(url.pathname))
    return Response.json(consultationState);
  if (url.pathname === '/api/ai/consultations/recommendations')
    return Response.json({ recommendations: consultationRows });
  if (url.pathname.startsWith('/api/ai/consultations/recommendations/')) {
    const row = consultationRows.find((item) => item.id === url.pathname.split('/')[5]);
    if (!row) throw new Error('Unexpected recommendation fixture');
    if (url.pathname.endsWith('/select'))
      return Response.json({ ...consultationState, selected_recommendation_id: row.id });
    return Response.json({
      generation: {
        recommendation_id: row.id,
        status: 'completed',
        attempts: 1,
        error: null,
        result_available: true,
      },
      result: {
        ...result,
        style: { ...result.style, id: row.primary.style_id, name: row.primary.style_name },
      },
    });
  }
  if (url.pathname === '/api/ai/features/nails/generate') return Response.json(result);
  const headers = new Headers(init.headers);
  if (method !== 'GET') headers.set('origin', 'http://localhost:3000');
  const req = new Request(url, { ...init, method, headers });
  const extra={query,actor:deps.actor};
  if(url.pathname==='/api/booking-notifications')return bookingNotifications(req,extra);
  if(url.pathname.startsWith('/api/admin/stylists/'))return stylistServiceHistory(req,url.pathname.split('/')[4],extra);
  if(url.pathname.startsWith('/api/consultation-history'))return consultationHistory(req,extra,url.pathname.split('/')[3]);
  if(url.pathname==='/api/stylist/availability')return workAvailability(req,extra);
  if(url.pathname.startsWith('/api/client-images'))return clientImages(req,extra,url.pathname.split('/').filter(Boolean)[2]);
  if(url.pathname.startsWith('/api/admin/clients/')){const parts=url.pathname.split('/').filter(Boolean);return clientHistory(req,parts[3],extra,parts[4]==='payments');}
  if (url.pathname.startsWith('/api/saved-looks')) {
    const parts = url.pathname.split('/').filter(Boolean);
    return savedLooks(req, parts[2], parts[3] === 'image', deps);
  }
  if (url.pathname.endsWith('/complete'))
    return completeAppointment(req, url.pathname.split('/')[3], deps);
  if (url.pathname.endsWith('/review'))
    return appointmentReview(req, url.pathname.split('/')[3], deps);
  if (url.pathname === '/api/admin/stylist-performance') return stylistPerformance(req, deps);
  if (url.pathname === '/api/inventory')
    return Response.json({
      inventory: await query('SELECT id,product_name AS \"productName\",brand FROM inventory'),
    });
  if(url.pathname==='/api/appointments/availability')return bookingAvailability(req,{query});
  if (url.pathname.startsWith('/api/appointments'))
    return bookingApi(req, url.pathname.split('/')[3], deps);
  if (url.pathname === '/api/admin/daily-services') return dailyServices(req, deps);
  if (url.pathname === '/api/admin/payments') return paymentHistory(req,extra);
  if (url.pathname === '/api/admin/stats') return Response.json({
    statusBreakdown:await query('SELECT status,count(*)::int AS n FROM appointments GROUP BY status'),
    topServices:await query(`SELECT service_name AS "serviceName",count(*)::int AS bookings,coalesce(sum(total_price),0)::int AS revenue FROM appointments WHERE status='completed' GROUP BY service_name ORDER BY revenue DESC LIMIT 5`),
  });
  throw new Error('Unexpected fixture request: ' + method + ' ' + url.pathname);
}
test.before(async () => {
  db = new PGlite();
  await db.exec(readFileSync('tests/fixtures/business-base.sql', 'utf8'));
  for (const file of [
    '0002_saved_looks.sql',
    '0003_saved_look_admission.sql',
    '0004_look_details.sql',
    '0005_service_completion.sql',
    '0007_business_controls.sql',
    '0008_work_availability.sql',
    '0009_customer_history.sql',
    '0010_ninety_minute_bookings.sql',
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
  window.localStorage.clear();
  window.history.replaceState(null,'','/');
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
  await query("INSERT INTO stylist_specialties(stylist_id,service_type) SELECT $1,x FROM unnest(ARRAY['hair','nail','makeup','treatment','massage','aesthetic']) x", [S]);
  await query(`INSERT INTO stylist_work_settings(stylist_id,available,hours) VALUES($1,true,$2::jsonb)`,[S,JSON.stringify(Array.from({length:7},(_,day)=>({day,start:'00:00',end:'23:59'})))]);
});
test.afterEach(() => cleanup());
test.after(async () => {
  globalThis.fetch = originalFetch;
  await db.close();
  dom.window.close();
});
test('login displays a useful service error when the server returns a 404 HTML page',async()=>{
 actor=null;
 globalThis.fetch=async(input,init)=>String(input)==='/api/auth/login'?new Response('<!DOCTYPE html><html>Not found</html>',{status:404,headers:{'Content-Type':'text/html'}}):transport(input,init);
 try{
  mount(LoginForm,{},'',true);
  fireEvent.change(screen.getByLabelText('Email'),{target:{value:'client@example.invalid'}});
  fireEvent.change(screen.getByLabelText('Password'),{target:{value:'test-password'}});
  fireEvent.click(screen.getByRole('button',{name:'Sign In',exact:true}));
  await screen.findByText('The account service is unavailable. Refresh the page and try again.');
  assert.equal(screen.queryByText(/Unexpected token/),null);
  assert.equal(pushes.length,0);
 }finally{globalThis.fetch=transport;}
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
  await screen.findByText('Your lookbook starts here');
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
  await waitFor(()=>assert.equal(screen.getByLabelText(/Preferred Stylist/).disabled,false));
  fireEvent.change(screen.getByLabelText(/Preferred Stylist/), { target: { value: S } });
  await waitFor(()=>assert.equal(screen.getByLabelText('Time', { exact: true }).disabled,false));
  fireEvent.change(screen.getByLabelText('Time', { exact: true }), { target: { value: '10:00' } });
  fireEvent.click(screen.getByRole('button', { name: 'Confirm Booking' }));
  await screen.findByText('Appointment confirmed');
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
  fireEvent.click(screen.getByLabelText('View visit: Gel Manicure, Client One'));
  fireEvent.click(screen.getByRole('button', { name: /View requested look/ }));
  assert.ok(screen.getByRole('dialog').hasAttribute('open'));
  assert.match(screen.getByRole('dialog').textContent, /Nude Pink Gloss/);
  fireEvent.click(screen.getByRole('button', { name: 'Mark as Completed' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Confirm completion' }));
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
  fireEvent.click(screen.getByRole('button', { name: 'View details for Makeup Application, Client One' }));
  await waitFor(() =>
    assert.equal(
      screen.getByLabelText('Assigned stylist').querySelector(`option[value="${S}"]`)?.textContent,
      'Stylist One',
    ),
  );
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

test('stylist availability switch saves immediately and retains the existing booking',async()=>{
 await transport('/api/appointments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({serviceName:"Women's Cut & Blowdry",serviceType:'hair',appointmentDate:'2030-10-17T02:00:00Z',stylistId:S})});
 actor=S;mount(WorkAvailability);const toggle=await screen.findByRole('switch',{name:'Available to Work'});fireEvent.click(toggle);
 await waitFor(async()=>assert.equal((await query('SELECT available FROM stylist_work_settings WHERE stylist_id=$1',[S]))[0].available,false));
 assert.equal((await query('SELECT status FROM appointments'))[0].status,'confirmed');
 await screen.findByRole('switch',{name:'Not Available'});
});

test('saved image picker previews and loads original image bytes without starting generation',async()=>{
 await transport('/api/saved-looks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feature:'nails',styleId:result.style.id,image:result.image.data_url,status:'completed',sourceKind:'manual'})});
 let selected=null;mount(ReferenceImagePicker,{onSelect:file=>{selected=file;}});
 fireEvent.click(screen.getByRole('button',{name:'Choose an existing image'}));
 fireEvent.click(await screen.findByRole('button',{name:/AI-generated look/}));
 assert.ok(screen.getByAltText('Preview of Nude Pink Gloss'));
 fireEvent.click(screen.getByRole('button',{name:'Use this image'}));
 await waitFor(()=>assert.ok(selected));assert.deepEqual(Buffer.from(await selected.arrayBuffer()),png);
 assert.equal(calls.filter(call=>call.path.endsWith('/generation')&&call.method==='POST').length,0);
});

test('admin client history displays real services and records one actual payment receipt',async()=>{
 await transport('/api/appointments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({serviceName:"Women's Cut & Blowdry",serviceType:'hair',appointmentDate:'2030-10-17T02:00:00Z',stylistId:S})});
 actor=A;mount(ClientHistory,{clientId:C});await screen.findByRole('heading',{name:"Women's Cut & Blowdry"});
 assert.ok(screen.getByText('No payment recorded'));
 fireEvent.click(screen.getByRole('button',{name:'Record payment'}));
 fireEvent.change(screen.getByLabelText('Amount (whole pesos)'),{target:{value:'50'}});
 fireEvent.click(screen.getByRole('button',{name:'Save payment receipt'}));
 await screen.findByText('Payment receipt recorded.');
 await waitFor(async()=>assert.equal((await query('SELECT count(*)::int AS n FROM appointment_payments'))[0].n,1));
 assert.equal(calls.filter(call=>call.path.startsWith('/api/client-images')).length,0);
});

test('dashboard revenue changes between daily, weekly, monthly and yearly periods using database records',async()=>{
 await query("INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,'Completed cut','hair','2030-10-17 02:00:00','completed',250)",[C,S]);
 actor=A;mount(RevenueOverview);
 fireEvent.change(screen.getByLabelText('Revenue reference date'),{target:{value:'2030-10-17'}});
 for(const [name,buckets] of [['Daily',24],['Weekly',7],['Monthly',31],['Yearly',12]]){
  fireEvent.click(screen.getByRole('button',{name,exact:true}));
  await waitFor(()=>assert.equal(screen.getByLabelText('Selected period revenue').textContent,'₱250'));
  await waitFor(()=>assert.equal(screen.getByLabelText('Revenue trend chart').querySelectorAll('button').length,buckets));
  assert.equal(screen.getByRole('button',{name,exact:true}).getAttribute('aria-pressed'),'true');
 }
 assert.ok(calls.some(call=>call.path==='/api/admin/stylist-performance'&&call.search.includes('period=year')));
});

test('stylist earnings roster shows day/month/year values and opens account editing only when requested',async()=>{
 await query("INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,'Completed cut','hair','2030-10-17 02:00:00','completed',250)",[C,S]);
 actor=A;mount(AdminStylists);
 fireEvent.change(screen.getByLabelText('Stylist earnings reference date'),{target:{value:'2030-10-17'}});
 const staff=await screen.findByText('Stylist One');
 await waitFor(()=>assert.equal((staff.closest('tr').textContent.match(/₱250/g)||[]).length,3));
 assert.equal(screen.queryByLabelText('Full name'),null);
 fireEvent.click(screen.getByRole('button',{name:'Yearly',exact:true}));
 await screen.findByRole('heading',{name:'2030',exact:true});
 fireEvent.click(await screen.findByRole('button',{name:'Edit Stylist One'}));
 await screen.findByRole('dialog',{name:'Edit stylist'});
 fireEvent.change(screen.getByLabelText('Full name'),{target:{value:'Stylist Updated'}});
 fireEvent.click(screen.getByRole('button',{name:'Save changes'}));
 await screen.findByText('Stylist details saved.');
 await screen.findByText('Stylist Updated');
 assert.equal((await query('SELECT name FROM users WHERE id=$1',[S]))[0].name,'Stylist Updated');
 assert.equal((await query('SELECT total_price,status FROM appointments'))[0].total_price,250);
 fireEvent.click(screen.getByRole('button',{name:'Add stylist'}));
 await screen.findByRole('dialog',{name:'Add a stylist'});
 assert.ok(screen.getByLabelText(/Temporary password/));
 fireEvent.click(screen.getByRole('button',{name:'Cancel',exact:true}));
 await waitFor(()=>assert.equal(screen.queryByRole('dialog'),null));
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

test('consultation books selected look B while look A is displayed, with one saved result and no regeneration', async () => {
  mount(ConsultationPage);
  fireEvent.click(screen.getByRole('button', { name: /Nails —/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  fireEvent.change(screen.getByLabelText('Upload consultation photo'), {
    target: { files: [new File([png], 'hand.png', { type: 'image/png' })] },
  });
  fireEvent.click(await screen.findByRole('button', { name: 'Find my looks' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Explore My Looks' }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate My Looks' }));
  await waitFor(() =>
    assert.equal(
      calls.filter((c) => c.path.endsWith('/generation') && c.method === 'POST').length,
      3,
    ),
  );
  fireEvent.click(
    screen.getByRole('button', { name: `View look 2: ${consultationRows[1].primary.style_name}` }),
  );
  fireEvent.click(await screen.findByRole('button', { name: 'Select This Look' }));
  await screen.findByRole('button', { name: 'Book Selected Look' });
  fireEvent.click(
    screen.getByRole('button', { name: `View look 1: ${consultationRows[0].primary.style_name}` }),
  );
  fireEvent.click(screen.getByRole('button', { name: 'Book Selected Look' }));
  await waitFor(() => assert.equal(pushes.length, 1));
  const saved = (await query('SELECT id,style_id,source_kind,look_details FROM ai_generations'))[0];
  assert.equal(saved.style_id, consultationRows[1].primary.style_id);
  assert.equal(saved.source_kind, 'consultation');
  assert.ok(saved.look_details.description);
  assert.equal(pushes[0], '/booking?look=' + saved.id);
  assert.equal(
    calls.filter((c) => c.path.endsWith('/generation') && c.method === 'POST').length,
    3,
  );
  assert.equal(calls.filter((c) => c.path === '/api/saved-looks' && c.method === 'POST').length, 1);
});

test('both home dashboards share the booked look; product completion enables a client review and accurate admin performance', async () => {
  const saved = await transport('/api/saved-looks', {
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
  const lookId = (await saved.json()).look.id;
  await transport('/api/appointments', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      serviceName: 'Gel Manicure',
      serviceType: 'nail',
      appointmentDate: '2030-10-17T02:00:00Z',
      stylistId: S,
      lookId,
    }),
  });
  mount(ClientDashboard, {}, '', true);
  assert.ok(await screen.findByAltText('Requested Nude Pink Gloss'));
  assert.match(document.body.textContent, /Stylist One/);
  cleanup();
  actor = S;
  mount(StylistDashboard, {}, '', true);
  assert.ok(await screen.findByAltText('Requested Nude Pink Gloss'));
  assert.match(document.body.textContent, /Client One/);
  cleanup();
  mount(StylistPage);
  fireEvent.click(await screen.findByLabelText('View visit: Gel Manicure, Client One'));
  fireEvent.click(await screen.findByRole('button', { name: 'Mark as Completed' }));
  fireEvent.click(screen.getByRole('button', { name: 'Add product used' }));
  fireEvent.change(screen.getByLabelText('Product name'), { target: { value: 'Top coat' } });
  fireEvent.change(screen.getByLabelText('Brand'), { target: { value: 'Brand Demo' } });
  fireEvent.change(screen.getByLabelText('Quantity used'), { target: { value: '2.5' } });
  fireEvent.change(screen.getByLabelText('Unit', { exact: true }), { target: { value: 'ml' } });
  fireEvent.change(screen.getByLabelText('Material cost per selected unit (PHP)'), {
    target: { value: '1.50' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Confirm completion' }));
  await waitFor(async () =>
    assert.equal((await query('SELECT status FROM appointments'))[0].status, 'completed'),
  );
  cleanup();
  actor = C;
  mount(ClientDashboard, {}, '', true);
  await screen.findByRole('heading', { name: 'Recently Completed' });
  assert.ok(await screen.findByText(/Top coat.*Brand Demo/));
  assert.equal(screen.queryByText(/PHP 1.5 per ml/), null);
  fireEvent.change(screen.getByLabelText('Rating'), { target: { value: '5' } });
  fireEvent.change(screen.getByLabelText('Review (optional)'), {
    target: { value: 'Loved the booked look' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Submit review' }));
  await screen.findByText('Client rating: 5/5');
  assert.equal(screen.queryByRole('button', { name: 'Submit review' }), null);
  cleanup();
  mount(ClientAppointments);
  fireEvent.click(screen.getByRole('button', { name: 'Past' }));
  await screen.findByText('Loved the booked look');
  cleanup();
  actor = A;
  mount(StylistPerformance);
  fireEvent.change(screen.getByLabelText('Performance from'), { target: { value: '2030-10-17' } });
  fireEvent.change(screen.getByLabelText('Performance through'), {
    target: { value: '2030-10-17' },
  });
  const row = (await screen.findByText('Stylist One', { selector: 'td' })).closest('tr');
  await waitFor(() => assert.match(row.textContent, /5.00 \/ 5/));
  assert.match(row.textContent, /₱350/);
  assert.equal((await query('SELECT count(*)::int AS n FROM appointment_reviews'))[0].n, 1);
  assert.equal((await query('SELECT count(*)::int AS n FROM appointment_product_usage'))[0].n, 1);
});

test('service deep links select the correct menu on arrival and on browser history navigation',async()=>{
 for(const [id,label] of [['hair-design','Hair Design'],['nail-studio','Nail Studio'],['face-laser','Face & Laser']]){
  window.history.replaceState(null,'','/services#'+id);
  mount(PublicServices);
  await screen.findByRole('heading',{level:2,name:label});
  const category=screen.getByRole('link',{name:label,exact:true});
  assert.equal(category.getAttribute('aria-current'),'page');
  assert.equal(category.getAttribute('href'),'#'+id);
  assert.equal(screen.getByRole('link',{name:'Book '+label}).getAttribute('href'),'/booking?service='+id);
  cleanup();
 }
 window.history.replaceState(null,'','/services#hair-design');
 mount(PublicServices);
 await screen.findByRole('heading',{level:2,name:'Hair Design'});
 window.history.replaceState(null,'','/services#nail-studio');
 fireEvent(window,new Event('popstate'));
 await screen.findByRole('heading',{level:2,name:'Nail Studio'});
 window.history.replaceState(null,'','/');
});

test('admin booking details save notes, reschedule with Philippine time, and cancel while preserving history',async()=>{
 await transport('/api/appointments',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({serviceName:'Makeup Application',serviceType:'makeup',appointmentDate:'2030-10-17T02:00:00Z'})});
 actor=A;mount(AdminAppointments);
 fireEvent.click(await screen.findByRole('button',{name:'View details for Makeup Application, Client One'}));
 fireEvent.change(screen.getByLabelText('Appointment notes'),{target:{value:'Discuss warm colours before starting.'}});
 fireEvent.click(screen.getByRole('button',{name:'Save notes'}));
 await waitFor(async()=>assert.equal((await query('SELECT notes FROM appointments'))[0].notes,'Discuss warm colours before starting.'));
 fireEvent.click(screen.getByText('Reschedule booking'));
 fireEvent.change(screen.getByLabelText('New appointment date'),{target:{value:'2030-10-18'}});
 fireEvent.change(screen.getByLabelText('New appointment time'),{target:{value:'11:30'}});
 await waitFor(()=>assert.equal(screen.getByRole('button',{name:'Save new schedule'}).disabled,false));
 fireEvent.click(screen.getByRole('button',{name:'Save new schedule'}));
 await waitFor(async()=>assert.equal((await query("SELECT to_char(appointment_date,'YYYY-MM-DD HH24:MI') AS scheduled FROM appointments"))[0].scheduled,'2030-10-18 03:30'));
 await waitFor(()=>assert.equal(screen.getByRole('button',{name:'Cancel appointment'}).disabled,false));
 fireEvent.click(screen.getByRole('button',{name:'Cancel appointment'}));
 assert.equal((await query('SELECT status FROM appointments'))[0].status,'pending');
 fireEvent.click(screen.getByRole('button',{name:'Keep appointment'}));
 assert.equal(screen.queryByRole('button',{name:'Confirm cancellation'}),null);
 fireEvent.click(screen.getByRole('button',{name:'Cancel appointment'}));
 fireEvent.click(screen.getByRole('button',{name:'Confirm cancellation'}));
 await screen.findByRole('heading',{name:'Cancelled booking'});
 assert.equal((await query('SELECT count(*)::int AS n FROM appointments'))[0].n,1);
 assert.equal(screen.queryByRole('button',{name:'Mark as Completed'}),null);
 assert.equal(screen.queryByRole('button',{name:'Save assignment / amount'}),null);
});

test('finance report navigation keeps receipts, service activity and team reports separate',async()=>{
 actor=A;mount(AdminFinance);
 await screen.findByRole('heading',{name:'Total Revenue'});
 await screen.findByRole('heading',{name:'Service performance'});
 fireEvent.click(screen.getByRole('button',{name:'Payment receipts'}));
 await screen.findByRole('heading',{name:'Payments received'});
 await waitFor(()=>assert.ok(calls.some(call=>call.path==='/api/admin/payments')));
 assert.equal(screen.queryByRole('heading',{name:'Total Revenue'}),null);
 fireEvent.click(screen.getByRole('button',{name:'Daily services'}));
 await waitFor(()=>assert.ok(calls.some(call=>call.path==='/api/admin/daily-services')));
 fireEvent.click(screen.getByRole('button',{name:'Team performance'}));
 await waitFor(()=>assert.ok(calls.some(call=>call.path==='/api/admin/stylist-performance'&&!call.search.includes('period='))));
 assert.equal(calls.filter(call=>call.method!=='GET').length,0);
});

test('stylist client directory derives searchable summaries only from their own assigned bookings',async()=>{
 await transport('/api/appointments',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({serviceName:'Gel Manicure',serviceType:'nail',appointmentDate:'2030-10-17T02:00:00Z',stylistId:S})});
 const outsider='77777777-7777-4777-8777-777777777777';
 await query("INSERT INTO users(id,email,name,password_hash,role) VALUES($1,'private@example.invalid','Other Client','unused','client')",[outsider]);
 await query("INSERT INTO appointments(client_id,service_name,service_type,appointment_date,status) VALUES($1,'Private service','hair','2030-10-18 10:00','pending')",[outsider]);
 actor=S;mount(StylistClients);
 await screen.findByText('Client One');
 assert.equal(screen.queryByText('Other Client'),null);
 fireEvent.change(screen.getByLabelText('Search clients'),{target:{value:'missing'}});
 await screen.findByText('No clients found');
 fireEvent.change(screen.getByLabelText('Search clients'),{target:{value:'client@example.invalid'}});
 await screen.findByText('Client One');
 assert.equal(calls.filter(call=>call.path.startsWith('/api/admin/clients')).length,0);
});

test('public price list hides the mens cut while the booking catalog retains it',async()=>{
 window.history.replaceState(null,'','/services#hair-design');mount(PublicServices);
 await screen.findByRole('heading',{name:'Hair Design',level:2});
 assert.ok(screen.getByText("Women's Cut & Blowdry"));assert.equal(screen.queryByText("Men's Cut"),null);
 cleanup();mount(BookingForm,{},'service=hair-design',true);
 const service=await screen.findByLabelText('Service',{exact:true});
 await waitFor(()=>assert.ok([...service.options].some(option=>option.value==="Men's Cut")));
 assert.equal(calls.filter(call=>call.method==='POST').length,0);
});

for(const [label,Component] of [['Hair',HairPage],['Makeup',MakeupPage],['Nail',NailsPage]]){
 test(label+' studio reuses a private existing image without sending a generation request',async()=>{
  await transport('/api/saved-looks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feature:'nails',styleId:result.style.id,image:result.image.data_url,status:'completed',sourceKind:'manual'})});
  mount(Component);fireEvent.click(screen.getByRole('button',{name:'Choose an existing image'}));
  fireEvent.click(await screen.findByRole('button',{name:/AI-generated look/}));
  fireEvent.click(screen.getByRole('button',{name:'Use this image'}));
  await waitFor(()=>assert.ok(screen.queryByRole('button',{name:'Remove'})));
  assert.equal(screen.queryByRole('button',{name:'Use this image'}),null);
  assert.equal(calls.filter(call=>call.method==='POST'&&(call.path.endsWith('/generate')||call.path.endsWith('/generation'))).length,0);
  assert.ok(calls.some(call=>call.path.endsWith('/image')&&call.method==='GET'));
 });
}

test('client and stylist booking alerts remain visible, link to a booking, and keep read state per account',async()=>{
 await transport('/api/appointments',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({serviceName:'Gel Manicure',serviceType:'nail',appointmentDate:'2030-10-17T02:00:00Z',stylistId:S})});
 const first=(await query('SELECT id FROM appointments'))[0].id;
 mount(BookingNotifications,{},'',true);
 await screen.findByRole('button',{name:'Booking notifications, 1 unread'});
 const link=screen.getByRole('link',{name:/1 unread booking update/});assert.equal(link.getAttribute('href'),'/client/appointments#booking-'+first);
 let opened=null;const capture=event=>{opened=event.detail;};window.addEventListener('booking-notification-open',capture,{once:true});
 fireEvent.click(link);await waitFor(()=>assert.equal(opened,first));
 assert.ok(JSON.parse(window.localStorage.getItem('beautycore:booking-alerts:v1:client:'+C)).length===1);
 await screen.findByRole('button',{name:'Booking notifications',exact:true});
 await transport('/api/appointments',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({serviceName:'Makeup Application',serviceType:'makeup',appointmentDate:'2030-10-18T02:00:00Z',stylistId:S})});
 fireEvent(window,new Event('appointments-updated'));
 await screen.findByRole('button',{name:'Booking notifications, 1 unread'});
 fireEvent.click(screen.getByRole('button',{name:'Booking notifications, 1 unread'}));
 assert.ok(await screen.findByRole('heading',{name:'Booking updates'}));
 assert.ok(screen.getAllByRole('link',{name:/Makeup Application/}).length>=1);
 cleanup();actor=S;mount(BookingNotifications,{},'',true);
 await screen.findByRole('button',{name:'Booking notifications, 2 unread'});
 assert.match(screen.getByRole('link',{name:/2 unread booking updates/}).getAttribute('href'),/^\/stylist\/appointments#booking-/);
});

test('admin opens a stylist to inspect completed services and filter their history',async()=>{
 await query("INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,'Completed cut','hair','2030-10-17 02:00:00','completed',350),($1,$2,'Pending cut','hair','2030-10-18 02:00:00','pending',350)",[C,S]);
 actor=A;mount(AdminStylists);
 fireEvent.click(await screen.findByRole('button',{name:'View services by Stylist One'}));
 await screen.findByRole('dialog',{name:'Stylist One'});
 assert.ok(await screen.findByText('Completed cut'));
 assert.equal(screen.queryByText('Pending cut'),null);
 fireEvent.change(screen.getByLabelText('Stylist services from'),{target:{value:'2030-10-18'}});
 await screen.findByText('No completed services in this period');
 fireEvent.click(screen.getByRole('button',{name:'All dates'}));
 await screen.findByText('Completed cut');
});

test('consultation history offers an owner-bound download for an unsaved archived generated look',async()=>{
 const {signConsultationHandle}=await import('../lib/ai/consultation-handle.ts');const {randomUUID}=await import('node:crypto');const secret='archive-download-test-secret-'.repeat(3);
 const handle=await signConsultationHandle(C,randomUUID(),new Date(Date.now()+3600000).toISOString(),secret);
 await archiveConsultationResponse(new Request('http://localhost:3000/api/ai/consultations',{method:'POST'}),Response.json({...consultationState,handle}),['consultations'],C,query,secret,134217728);
 const session=(await query('SELECT id FROM client_consultations'))[0].id;
 await archiveConsultationResponse(new Request('http://localhost:3000/api/ai/consultations/recommendations/rec-1/generation',{method:'POST',headers:{'x-ai-consultation-handle':handle}}),Response.json({generation:{recommendation_id:'rec-1',status:'completed'},result}),['consultations','recommendations','rec-1','generation'],C,query,secret,134217728);
 mount(ConsultationHistory,{sessionId:session});const download=await screen.findByRole('link',{name:'Download Nude Pink Gloss'});
 assert.match(download.getAttribute('href'),/\/api\/saved-looks\/.*\/image\?download=1$/);
 const response=await transport(download.getAttribute('href'));assert.equal(response.status,200);assert.match(response.headers.get('Content-Disposition'),/^attachment/);assert.deepEqual(Buffer.from(await response.arrayBuffer()),png);
 assert.equal((await query('SELECT saved_at FROM ai_generations'))[0].saved_at,null);
 assert.equal(calls.filter(call=>call.path.endsWith('/generation')&&call.method==='POST').length,0);
});

test('a stylist booking link opens the requested visit even when it is on a later page',async()=>{
 let target='';for(let index=0;index<12;index++){
  const rows=await query("INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,$3,'hair',$4::timestamp,'confirmed',350) RETURNING id",[C,S,'Scheduled visit '+(index+1),'2030-10-'+String(17+index)+' 02:00:00']);
  if(index===11)target=rows[0].id;
 }
 actor=S;window.history.replaceState(null,'','/stylist/appointments#booking-'+target);mount(StylistPage);
 await screen.findByRole('heading',{name:'Scheduled visit 12'});
 await waitFor(()=>assert.equal(document.getElementById('booking-'+target).open,true));
 assert.match(screen.getByRole('navigation',{name:'Pagination'}).textContent,/Page 2 of 2/);
});


test('Book This Look recovers a lost save response with one saved record and no generation',async()=>{
 let saves=0;globalThis.fetch=async(input,init)=>{
  if(String(input)==='/api/saved-looks'&&init?.method==='POST'){
   saves++;const response=await transport(input,init);if(saves===1)throw new TypeError('connection lost after commit');return response;
  }
  return transport(input,init);
 };
 try{
  mount(SavedLookActions,{feature:'nails',result});
  fireEvent.click(screen.getByRole('button',{name:'Book This Look'}));
  await waitFor(()=>assert.equal(pushes.length,1),{timeout:4000});
  assert.equal(saves,2);assert.match(pushes[0],/^\/booking\?look=/);
  assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n,1);
  assert.equal(calls.some(c=>c.path.endsWith('/generate')),false);
 }finally{globalThis.fetch=transport;}
});

test('calendar disables overlapping times and keeps the selected stylist',async()=>{
 await transport('/api/appointments',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({serviceName:"Women's Cut & Blowdry",serviceType:'hair',appointmentDate:'2030-10-17T01:00:00Z',stylistId:S})});
 mount(BookingForm,{},'service=hair-design',true);await screen.findByLabelText('Service',{exact:true});
 fireEvent.change(screen.getByLabelText('Service',{exact:true}),{target:{value:"Women's Cut & Blowdry"}});
 await waitFor(()=>assert.equal(screen.getByLabelText(/Preferred Stylist/).disabled,false));
 fireEvent.change(screen.getByLabelText(/Preferred Stylist/),{target:{value:S}});
 fireEvent.change(screen.getByLabelText(/Date \(Philippine time\)/),{target:{value:'2030-10-17'}});
 await waitFor(()=>assert.equal(screen.getByLabelText('Time',{exact:true}).disabled,false));
 const select=screen.getByLabelText('Time',{exact:true});
 for(const time of ['09:00','09:30','10:00'])assert.equal([...select.options].find(o=>o.value===time)?.disabled,true);
 assert.equal([...select.options].find(o=>o.value==='10:30')?.disabled,false);
 assert.equal(screen.getByLabelText(/Preferred Stylist/).value,S);
 fireEvent.change(select,{target:{value:'10:30'}});fireEvent.click(screen.getByRole('button',{name:'Confirm Booking'}));
 await screen.findByText('Appointment confirmed');assert.equal((await query('SELECT count(*)::int AS n FROM appointments'))[0].n,2);
});


test('look-aware booking can reload a temporarily unavailable saved look',async()=>{
 const response=await transport('/api/saved-looks',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({feature:'nails',styleId:result.style.id,image:result.image.data_url,status:'completed',sourceKind:'manual'})});
 const id=(await response.json()).look.id;let reads=0;
 globalThis.fetch=async(input,init)=>{
  if(String(input)==='/api/saved-looks/'+id&&++reads===1)return Response.json({error:'Temporary saved look failure'},{status:503});
  return transport(input,init);
 };
 try{
  mount(BookingForm,{},'look='+id,true);await screen.findByText('Temporary saved look failure');
  fireEvent.click(screen.getByRole('button',{name:'Retry loading look'}));
  await screen.findByText('Booking with Nude Pink Gloss');assert.equal(reads,2);
  assert.equal(screen.getByLabelText('Service',{exact:true}).options[1].value,'Classic Manicure');
 }finally{globalThis.fetch=transport;}
});
