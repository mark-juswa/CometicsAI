import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { PGlite } from "@electric-sql/pglite";
import sharp from "sharp";
import { applySavedLookMigrations } from "../scripts/saved-look-migrations";
import { bookingApi, savedLooks, type Dependencies } from "../lib/business/api";
import { createBusinessStore } from "../lib/business/store";
import {
  clientHistory,
  clientImages,
  consultationHistory,
  archiveConsultationResponse,
  paymentHistory,
  type HistoryDependencies,
} from "../lib/business/customer-history";
import { workAvailability } from "../lib/business/work-availability";
import { bookingAvailability, availableBookingSlots } from "../lib/business/booking-availability";
import { allServices, serviceDurationMinutes } from "../lib/services";
import { preservingBusinessRecords } from "../scripts/business-preservation";
import { bookingNotifications } from "../lib/business/booking-notifications";
import { stylistServiceHistory } from "../lib/business/stylist-history";
import { signConsultationHandle } from "../lib/ai/consultation-handle";
const C = "11111111-1111-4111-8111-111111111111",
  OTHER = "22222222-2222-4222-8222-222222222222",
  S = "33333333-3333-4333-8333-333333333333",
  A = "55555555-5555-4555-8555-555555555555";
const ORIGIN = "http://localhost:3000",
  SECRET = "test-history-secret-".repeat(3),
  BUDGET = 134217728;
const hours = Array.from({ length: 7 }, (_, day) => ({
  day,
  start: "09:00",
  end: "17:00",
}));
let db: PGlite,
  deps: Dependencies,
  history: HistoryDependencies,
  actor: string | null = C,
  png: Buffer;
const query = async (sql: string, values: unknown[] = []) =>
  (await db.query<Record<string, unknown>>(sql, values)).rows;
const req = (path: string, method = "GET", body?: unknown, origin = ORIGIN) =>
  new Request(ORIGIN + path, {
    method,
    headers: { "Content-Type": "application/json", Origin: origin },
    ...(method === "GET" ? {} : { body: JSON.stringify(body ?? {}) }),
  });
const book = (date = "2030-10-17T02:00:00Z", stylist: string | null = S) =>
  bookingApi(
    req("/api/appointments", "POST", {
      serviceName: "Women's Cut & Blowdry",
      serviceType: "hair",
      appointmentDate: date,
      stylistId: stylist,
    }),
    undefined,
    deps,
  );
const state = {
  primary_service: "hairstyle",
  stage: "collecting",
  messages: [{ role: "user", content: "Private customer preference" }],
  generations: [],
  selected_recommendation_id: null,
};
async function archiveStart() {
  const handle = await signConsultationHandle(
    C,
    randomUUID(),
    "2031-01-01T00:00:00Z",
    SECRET,
  );
  await archiveConsultationResponse(
    req("/api/ai/consultations", "POST"),
    Response.json({ ...state, handle }),
    ["consultations"],
    C,
    query,
    SECRET,
    BUDGET,
  );
  const [session] = await query(
    "SELECT id FROM client_consultations WHERE client_id=$1 ORDER BY created_at DESC",
    [C],
  );
  return { handle, sessionId: String(session.id) };
}
function output(image = png) {
  return {
    generation: { recommendation_id: "rec-1", status: "completed" },
    result: {
      status: "completed",
      style: { id: "crew_cut", name: "Crew Cut" },
      image: { data_url: "data:image/png;base64," + image.toString("base64") },
    },
  };
}
async function archiveGenerated(handle: string, image = png) {
  await archiveConsultationResponse(
    new Request(
      ORIGIN + "/api/ai/consultations/recommendations/rec-1/generation",
      { headers: { "x-ai-consultation-handle": handle } },
    ),
    Response.json(output(image)),
    ["consultations", "recommendations", "rec-1", "generation"],
    C,
    query,
    SECRET,
    BUDGET,
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
  png = await sharp({
    create: { width: 32, height: 32, channels: 3, background: "#ba90c4" },
  })
    .png()
    .toBuffer();
  const store = createBusinessStore(query);
  const current = async () =>
    actor ? ((await store.currentUser(actor)) ?? null) : null;
  deps = {
    actor: current,
    store,
    settings: { enabled: true, clientLimit: 20, storageBudget: BUDGET },
  };
  history = { actor: current, query };
});
test.beforeEach(async () => {
  await db.exec("TRUNCATE users CASCADE");
  actor = C;
  for (const [id, role] of [
    [C, "client"],
    [OTHER, "client"],
    [S, "stylist"],
    [A, "admin"],
  ])
    await query(
      "INSERT INTO users(id,email,name,password_hash,role) VALUES($1,$2,$3,$4,$5)",
      [id, role + id + "@example.invalid", role, "not-a-login", role],
    );
  await query("INSERT INTO stylist_specialties VALUES($1,'hair')", [S]);
  await query("SELECT beautycore_set_work($1,true,$2::jsonb)", [
    S,
    JSON.stringify(hours),
  ]);
});
test.after(async () => {
  await db.close();
});

test("selected available stylist is automatically confirmed; no preference remains pending", async () => {
  const selected = await book();
  assert.equal(selected.status, 201, await selected.clone().text());
  assert.equal((await selected.json()).appointment.status, "confirmed");
  const unassigned = await book("2030-10-17T04:00:00Z", null);
  assert.equal((await unassigned.json()).appointment.status, "pending");
});
test("working hours, service duration, inactive staff, and overlap are checked in the database", async () => {
  assert.equal((await book("2030-10-17T00:30:00Z")).status, 409);
  assert.equal((await book("2030-10-17T08:30:00Z")).status, 409);
  assert.equal((await book()).status, 201);
  assert.equal((await book("2030-10-17T02:30:00Z")).status, 409);
  assert.equal((await book("2030-10-17T03:30:00Z")).status, 201);
  await query("UPDATE users SET is_active=false WHERE id=$1", [S]);
  assert.equal((await book("2030-10-17T05:00:00Z")).status, 400);
});
test("two competing bookings produce exactly one appointment and one conflict", async () => {
  const attempts = await Promise.all([book(), book()]);
  assert.deepEqual(attempts.map((r) => r.status).sort(), [201, 409]);
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM appointments"))[0].n,
    1,
  );
});
test("availability OFF persists, rejects new bookings, and preserves confirmed appointments and edits", async () => {
  const existing = (await (await book()).json()).appointment.id;
  actor = S;
  assert.equal(
    (
      await workAvailability(
        req("/api/stylist/availability", "PUT", { available: false, hours }),
        history,
      )
    ).status,
    200,
  );
  assert.equal(
    (
      await (
        await workAvailability(req("/api/stylist/availability"), history)
      ).json()
    ).available,
    false,
  );
  actor = null;
  actor = S;
  assert.equal(
    (
      await (
        await workAvailability(req("/api/stylist/availability"), history)
      ).json()
    ).available,
    false,
  );
  assert.equal(
    (await query("SELECT status FROM appointments WHERE id=$1", [existing]))[0]
      .status,
    "confirmed",
  );
  assert.equal(
    (
      await bookingApi(
        req("/api/appointments/" + existing, "PATCH", {
          notes: "Preserved booking",
        }),
        existing,
        deps,
      )
    ).status,
    200,
  );
  actor = A;
  assert.equal(
    (
      await bookingApi(
        req("/api/appointments/" + existing, "PATCH", {
          stylistId: S,
          totalPrice: 250,
        }),
        existing,
        deps,
      )
    ).status,
    200,
  );
  actor = C;
  assert.equal((await book("2030-10-17T05:00:00Z")).status, 409);
});
test("availability rejects other roles, spoofed IDs, foreign origins, and malformed schedules", async () => {
  assert.equal(
    (
      await workAvailability(
        req("/api/stylist/availability", "PUT", { available: true, hours }),
        history,
      )
    ).status,
    403,
  );
  actor = S;
  for (const invalid of [
    { available: true, hours: [] },
    { available: true, hours: [null] },
    { available: true, hours: [{ day: 4, start: "17:00", end: "09:00" }] },
    { available: true, hours: [hours[0], hours[0]] },
    { available: false, hours, stylistId: OTHER },
  ])
    assert.equal(
      (
        await workAvailability(
          req("/api/stylist/availability", "PUT", invalid),
          history,
        )
      ).status,
      400,
    );
  assert.equal(
    (
      await workAvailability(
        req(
          "/api/stylist/availability",
          "PUT",
          { available: true, hours },
          "https://foreign.invalid",
        ),
        history,
      )
    ).status,
    403,
  );
});
test("reference upload is stored once, returned privately, and remains associated with its session", async () => {
  const { handle, sessionId } = await archiveStart();
  for (let i = 0; i < 2; i++) {
    const form = new FormData();
    form.set(
      "image",
      new File([new Uint8Array(png)], "reference.png", { type: "image/png" }),
    );
    await archiveConsultationResponse(
      new Request(ORIGIN + "/api/ai/consultations/photo", {
        method: "PUT",
        headers: { "x-ai-consultation-handle": handle },
        body: form,
      }),
      Response.json(state),
      ["consultations", "photo"],
      C,
      query,
      SECRET,
      BUDGET,
    );
  }
  const [image] = await query(
    "SELECT id,consultation_id FROM client_reference_images",
  );
  assert.equal(image.consultation_id, sessionId);
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM client_reference_images"))[0]
      .n,
    1,
  );
  const response = await clientImages(
    req("/api/client-images/" + image.id),
    history,
    String(image.id),
  );
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "private, no-store");
  assert.deepEqual(Buffer.from(await response.arrayBuffer()), png);
  actor = OTHER;
  assert.equal(
    (
      await clientImages(
        req("/api/client-images/" + image.id),
        history,
        String(image.id),
      )
    ).status,
    404,
  );
  assert.equal(
    (
      await consultationHistory(
        req("/api/consultation-history/" + sessionId),
        history,
        sessionId,
      )
    ).status,
    404,
  );
  actor = A;
  assert.equal(
    (await clientImages(req("/api/client-images"), history)).status,
    403,
  );
  assert.equal(
    (
      await clientImages(
        req("/api/client-images/" + image.id),
        history,
        String(image.id),
      )
    ).status,
    403,
  );
  assert.equal(
    (await consultationHistory(req("/api/consultation-history"), history))
      .status,
    403,
  );
});
test("new generated variations retain previous results; saving reuses the archived image record", async () => {
  const { handle, sessionId } = await archiveStart();
  await archiveGenerated(handle);
  await archiveGenerated(handle);
  const alternate = await sharp({
    create: { width: 32, height: 32, channels: 3, background: "#bbaacc" },
  })
    .png()
    .toBuffer();
  await archiveGenerated(handle, alternate);
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM ai_generations"))[0].n,
    2,
  );
  assert.equal(
    (
      await query("SELECT count(*)::int AS n FROM client_consultation_results")
    )[0].n,
    2,
  );
  let library = await (
    await clientImages(req("/api/client-images?kind=generated"), history)
  ).json();
  assert.equal(library.images.length, 0);
  const [image] = await query(
    "SELECT id FROM ai_generations ORDER BY created_at,id",
  );
  assert.equal(
    (
      await savedLooks(
        req("/api/saved-looks/" + image.id, "PATCH", { saved: true }),
        String(image.id),
        false,
        deps,
      )
    ).status,
    200,
  );
  library = await (
    await clientImages(req("/api/client-images?kind=generated"), history)
  ).json();
  assert.equal(library.images.length, 1);
  assert.equal(library.images[0].id, image.id);
  const detail = await (
    await consultationHistory(
      req("/api/consultation-history/" + sessionId),
      history,
      sessionId,
    )
  ).json();
  assert.equal(detail.results.length, 2);
  assert.equal(
    detail.session.snapshot.messages[0].content,
    "Private customer preference",
  );
  actor = A;
  assert.equal(
    (
      await savedLooks(
        req("/api/saved-looks/" + image.id + "/image"),
        String(image.id),
        true,
        deps,
      )
    ).status,
    404,
  );
});
test("hosted job results are archived using the owner-bound submission mapping", async () => {
  const { handle } = await archiveStart();
  const job = randomUUID();
  await archiveConsultationResponse(
    new Request(
      ORIGIN + "/api/ai/consultations/recommendations/rec-1/generation",
      { method: "POST", headers: { "x-ai-consultation-handle": handle } },
    ),
    Response.json({ job_id: job, status: "generating" }),
    ["consultations", "recommendations", "rec-1", "generation"],
    C,
    query,
    SECRET,
    BUDGET,
  );
  await archiveConsultationResponse(
    req("/api/ai/jobs/" + job + "/result"),
    Response.json(output()),
    ["jobs", job, "result"],
    C,
    query,
    SECRET,
    BUDGET,
  );
  assert.equal(
    (
      await query("SELECT count(*)::int AS n FROM client_consultation_results")
    )[0].n,
    1,
  );
});
test("customer history and image list require authentication and exclude other customers", async () => {
  await archiveStart();
  actor = OTHER;
  assert.equal(
    (
      await (
        await consultationHistory(req("/api/consultation-history"), history)
      ).json()
    ).sessions.length,
    0,
  );
  actor = null;
  assert.equal(
    (await consultationHistory(req("/api/consultation-history"), history))
      .status,
    401,
  );
});
test("actual payments are separate from service prices; receipts are idempotent and capped at the balance", async () => {
  const appointment = (await (await book()).json()).appointment.id;
  actor = A;
  let detail = await (
    await clientHistory(req("/api/admin/clients/" + C), C, history)
  ).json();
  assert.equal(Number(detail.appointments[0].paidAmount), 0);
  assert.equal(detail.payments.length, 0);
  assert.ok(!JSON.stringify(detail).includes("imageUrl"));
  const body = {
    appointmentId: appointment,
    amount: 50,
    method: "cash",
    reference: "Receipt 1",
    requestId: randomUUID(),
  };
  const payment = () =>
    clientHistory(
      req("/api/admin/clients/" + C + "/payments", "POST", body),
      C,
      history,
      true,
    );
  assert.equal((await payment()).status, 201);
  assert.equal((await payment()).status, 201);
  assert.equal(
    (await query("SELECT count(*)::int AS n FROM appointment_payments"))[0].n,
    1,
  );
  const excessive = { ...body, requestId: randomUUID(), amount: 100000000 };
  assert.equal(
    (
      await clientHistory(
        req("/api/admin/clients/" + C + "/payments", "POST", excessive),
        C,
        history,
        true,
      )
    ).status,
    409,
  );
  await assert.rejects(
    query("UPDATE appointments SET total_price=1 WHERE id=$1", [appointment]),
  );
  detail = await (
    await clientHistory(req("/api/admin/clients/" + C), C, history)
  ).json();
  assert.equal(Number(detail.summary.paymentsReceived), 50);
  assert.equal(detail.payments[0].method, "cash");
  actor = C;
  assert.equal(
    (await clientHistory(req("/api/admin/clients/" + C), C, history)).status,
    403,
  );
});
test("client service filters use real appointments and never expose consultation snapshots", async () => {
  await book();
  await archiveStart();
  actor = A;
  const detail = await (
    await clientHistory(
      req(
        "/api/admin/clients/" +
          C +
          "?status=confirmed&q=Cut&from=2030-10-17&to=2030-10-17",
      ),
      C,
      history,
    )
  ).json();
  assert.equal(detail.total, 1);
  assert.equal(detail.appointments[0].stylistName, "stylist");
  assert.ok(!JSON.stringify(detail).includes("Private customer preference"));
  assert.equal(
    (
      await clientHistory(
        req("/api/admin/clients/" + C + "?status=cancelled"),
        C,
        history,
      ).then((r) => r.json())
    ).total,
    0,
  );
});
test("login source contains no demo account identifiers or displayed sample credentials", () => {
  const login = readFileSync("app/(public)/login/login-form.tsx", "utf8");
  for (const text of [
    "demoAccounts",
    "DEMO ACCOUNTS",
    "admin123",
    "stylist123",
    "client123",
    "maria@email.com",
    "lara@andreas.com",
  ])
    assert.ok(!login.includes(text));
});

test("earlier private reference photos can be reused without rewriting legacy records", async () => {
  const source = "data:image/png;base64," + png.toString("base64");
  const [legacy] = await query(
    "INSERT INTO ai_generations(client_id,source_image_url,style_type) VALUES($1,$2,'hair') RETURNING id",
    [C, source],
  );
  const response = await clientImages(
    req("/api/client-images?kind=uploaded"),
    history,
  );
  assert.equal(response.status, 200);
  assert.equal((await response.json()).images[0].id, legacy.id);
  const image = await clientImages(
    req("/api/client-images/" + legacy.id),
    history,
    String(legacy.id),
  );
  assert.deepEqual(Buffer.from(await image.arrayBuffer()), png);
  assert.equal(
    (
      await query("SELECT source_image_url FROM ai_generations WHERE id=$1", [
        legacy.id,
      ])
    )[0].source_image_url,
    source,
  );
  actor = A;
  assert.equal(
    (
      await clientImages(
        req("/api/client-images/" + legacy.id),
        history,
        String(legacy.id),
      )
    ).status,
    403,
  );
});

test("finance payment history reports actual receipts and enforces admin access and filters", async () => {
  const appointment = (await (await book()).json()).appointment.id;
  actor = A;
  await clientHistory(
    req("/api/admin/clients/" + C + "/payments", "POST", {
      appointmentId: appointment,
      requestId: randomUUID(),
      amount: 50,
      method: "card",
      reference: "Card receipt",
    }),
    C,
    history,
    true,
  );
  const report = await (
    await paymentHistory(
      req("/api/admin/payments?method=card&q=receipt"),
      history,
    )
  ).json();
  assert.equal(report.total, 1);
  assert.equal(report.amount, 50);
  assert.equal(
    (
      await (
        await paymentHistory(req("/api/admin/payments?method=cash"), history)
      ).json()
    ).total,
    0,
  );
  actor = S;
  assert.equal(
    (await paymentHistory(req("/api/admin/payments"), history)).status,
    403,
  );
});

test('administrators and stylists cannot attach an unsubmitted private look by creating a booking',async()=>{
 const {handle}=await archiveStart();await archiveGenerated(handle);
 const [look]=await query('SELECT id FROM ai_generations');
 await savedLooks(req('/api/saved-looks/'+look.id,'PATCH',{saved:true}),String(look.id),false,deps);
 actor=A;
 const body={clientId:C,lookId:look.id,serviceName:"Women's Cut & Blowdry",serviceType:'hair',appointmentDate:'2030-10-17T02:00:00Z',stylistId:S};
 assert.equal((await bookingApi(req('/api/appointments','POST',body),undefined,deps)).status,403);
 assert.equal((await savedLooks(req('/api/saved-looks/'+look.id+'/image'),String(look.id),true,deps)).status,404);
 actor=S;assert.equal((await bookingApi(req('/api/appointments','POST',body),undefined,deps)).status,403);
 assert.equal((await query('SELECT count(*)::int AS n FROM appointments'))[0].n,0);
 actor=C;assert.equal((await bookingApi(req('/api/appointments','POST',body),undefined,deps)).status,201);
 actor=A;assert.equal((await savedLooks(req('/api/saved-looks/'+look.id+'/image'),String(look.id),true,deps)).status,200);
});

test('booking alerts are scoped to the owner and assigned stylist, and update with assignment and cancellation',async()=>{
 const response=await book('2030-10-17T02:00:00Z',null);assert.equal(response.status,201);
 const id=(await query('SELECT id FROM appointments'))[0].id;
 let alerts=await bookingNotifications(req('/api/booking-notifications?clientId='+OTHER),history);assert.equal(alerts.status,200);
 const first=await alerts.json();assert.equal(first.ownerId,C);assert.equal(first.total,1);assert.equal(first.notifications[0].status,'pending');
 actor=OTHER;assert.equal((await(await bookingNotifications(req('/api/booking-notifications'),history)).json()).total,0);
 actor=S;assert.equal((await(await bookingNotifications(req('/api/booking-notifications'),history)).json()).total,0);
 actor=A;assert.equal((await bookingNotifications(req('/api/booking-notifications'),history)).status,403);
 const update=await bookingApi(req('/api/appointments/'+id,'PATCH',{stylistId:S}),String(id),deps);assert.equal(update.status,200);
 actor=S;const assigned=await(await bookingNotifications(req('/api/booking-notifications'),history)).json();assert.equal(assigned.total,1);assert.equal(assigned.notifications[0].id,id);assert.equal(assigned.notifications[0].status,'confirmed');
 assert.equal('clientId' in assigned.notifications[0],false);assert.equal('stylistId' in assigned.notifications[0],false);
 actor=C;const changed=await(await bookingNotifications(req('/api/booking-notifications'),history)).json();assert.notEqual(changed.notifications[0].key,first.notifications[0].key);
 assert.equal((await bookingApi(req('/api/appointments/'+id,'PATCH',{status:'cancelled'}),String(id),deps)).status,200);
 assert.equal((await(await bookingNotifications(req('/api/booking-notifications'),history)).json()).total,0);
 actor=S;assert.equal((await(await bookingNotifications(req('/api/booking-notifications'),history)).json()).total,0);
 actor=null;assert.equal((await bookingNotifications(req('/api/booking-notifications'),history)).status,401);
 assert.equal((await query('SELECT count(*)::int AS n FROM appointments'))[0].n,1);
});

test('stylist service history is admin-only, completed-only, and preserves zero and unconfirmed amounts',async()=>{
 await query("INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,status,total_price) VALUES($1,$2,'Free completed service','hair','2030-10-16 16:30:00','completed',0),($1,$2,'Unpriced completed service','hair','2030-10-18 02:00:00','completed',NULL),($1,$2,'Upcoming service','hair','2030-10-19 02:00:00','confirmed',350)",[C,S]);
 for(const role of [C,S]){actor=role;assert.equal((await stylistServiceHistory(req('/api/admin/stylists/'+S+'/services'),S,history)).status,403);}
 actor=A;const all=await(await stylistServiceHistory(req('/api/admin/stylists/'+S+'/services'),S,history)).json();assert.equal(all.total,2);assert.equal(all.summary.amount,0);assert.equal(all.summary.unpriced,1);assert.equal(all.services.length,2);assert.ok(all.services.every((row:any)=>!('imageUrl' in row)));
 const day=await(await stylistServiceHistory(req('/api/admin/stylists/'+S+'/services?from=2030-10-17&to=2030-10-17'),S,history)).json();assert.equal(day.total,1);assert.equal(day.services[0].serviceName,'Free completed service');assert.equal(day.services[0].totalPrice,0);
 assert.equal((await stylistServiceHistory(req('/api/admin/stylists/'+S+'/services?from=2030-10-19&to=2030-10-17'),S,history)).status,400);
 assert.equal((await stylistServiceHistory(req('/api/admin/stylists/'+C+'/services'),C,history)).status,404);
});

test('archived generated images can be downloaded privately without saving or generating again',async()=>{
 const {handle,sessionId}=await archiveStart();await archiveGenerated(handle);
 const detail=await(await consultationHistory(req('/api/consultation-history/'+sessionId),history,sessionId)).json();const image=detail.results[0];
 assert.equal(image.savedAt,null);
 const response=await savedLooks(req(image.imageUrl+'?download=1'),image.id,true,deps);assert.equal(response.status,200);assert.match(response.headers.get('Content-Disposition')??'',/^attachment; filename="andreas-.*\.png"$/);assert.equal(response.headers.get('Content-Type'),'image/png');assert.deepEqual(Buffer.from(await response.arrayBuffer()),png);
 actor=OTHER;assert.equal((await savedLooks(req(image.imageUrl+'?download=1'),image.id,true,deps)).status,404);
 actor=S;assert.equal((await savedLooks(req(image.imageUrl+'?download=1'),image.id,true,deps)).status,404);
 assert.equal((await query('SELECT count(*)::int AS n FROM ai_generations'))[0].n,1);
});


test("every catalog service reserves ninety minutes", () => {
  for(const service of allServices) assert.equal(serviceDurationMinutes(service.name, service.serviceType),90,service.name);
});

test("nine o'clock blocks ninety minutes for that stylist and exposes no client data", async () => {
  assert.equal((await book('2030-10-17T01:00:00Z')).status,201);
  assert.equal((await query('SELECT duration_minutes FROM appointments'))[0].duration_minutes,90);
  const response=await bookingAvailability(req('/api/appointments/availability?'+new URLSearchParams({date:'2030-10-17',service:"Women's Cut & Blowdry",stylist:S})),{query});
  assert.equal(response.status,200);assert.match(response.headers.get('Cache-Control') ?? '',/no-store/);
  const body=await response.json() as {slots:{time:string;available:boolean}[]};
  for(const time of ['09:00','09:30','10:00'])assert.notEqual(body.slots.find(s=>s.time===time)?.available,true,time);
  assert.equal(body.slots.find(s=>s.time==='10:30')?.available,true);
  assert.ok(!body.slots.some(s=>s.time==='16:00'));
  assert.equal(JSON.stringify(body).includes(C),false);
  assert.equal((await book('2030-10-17T02:00:00Z')).status,409);
  assert.equal((await book('2030-10-17T02:30:00Z')).status,201);
});

test("slots remain available for another stylist, and retain longer legacy reservations", () => {
  const other='66666666-6666-4666-8666-666666666666';
  const staff=[{id:S,hours},{id:other,hours}],reserved=[{stylistId:S,appointmentDate:'2030-10-17T01:00:00Z',durationMinutes:60}];
  let slots=availableBookingSlots('2030-10-17',staff,reserved,new Date('2030-10-16'));
  assert.equal(slots.find(s=>s.time==='09:00')?.available,true);
  slots=availableBookingSlots('2030-10-17',[staff[0]],reserved,new Date('2030-10-16'));
  assert.notEqual(slots.find(s=>s.time==='10:00')?.available,true);
  assert.equal(slots.find(s=>s.time==='10:30')?.available,true);
  reserved[0].durationMinutes=180;
  slots=availableBookingSlots('2030-10-17',[staff[0]],reserved,new Date('2030-10-16'));
  assert.equal(slots.find(s=>s.time==='10:30')?.available,true);
});

test("scheduling upgrade preserves old rows, blocks short legacy overlaps and forces legacy callers to ninety minutes", async()=>{
  await query("INSERT INTO appointments(client_id,stylist_id,service_name,service_type,appointment_date,duration_minutes,status) VALUES($1,$2,'Legacy hair','hair','2030-10-17 01:00:00',60,'confirmed')",[C,S]);
  const before=await query('SELECT to_jsonb(a) AS row FROM appointments a');
  const statements=readFileSync('db/migrations/0010_ninety_minute_bookings.sql','utf8').split('--> statement-breakpoint').filter(s=>s.trim());
  await db.transaction(async tx=>{for(const sql of preservingBusinessRecords(statements))await tx.query(sql);});
  assert.deepEqual(await query('SELECT to_jsonb(a) AS row FROM appointments a'),before);
  assert.equal((await book('2030-10-17T02:00:00Z')).status,409);
  const created=await query("SELECT * FROM beautycore_create_appointment($1,$2,'Legacy caller','hair','2030-10-17T02:30:00Z',30,100,NULL,NULL)",[C,S]);
  assert.equal(created[0].outcome,'created');
  assert.equal((await query('SELECT duration_minutes FROM appointments WHERE id=$1',[created[0].appointment_id]))[0].duration_minutes,90);
});

test("availability rejects malformed inputs and excludes cancelled and off-duty bookings", async()=>{
 for(const params of ([{date:'2030-02-30',service:"Women's Cut & Blowdry"},{date:'2030-10-17',service:'unknown'},{date:'2030-10-17',service:"Women's Cut & Blowdry",stylist:'invalid'}] as Record<string,string>[]))assert.equal((await bookingAvailability(req('/api/appointments/availability?'+new URLSearchParams(params)),{query})).status,400);
 const response=await book('2030-10-17T01:00:00Z');const id=(await response.json()).appointment.id;
 await query("UPDATE appointments SET status='cancelled' WHERE id=$1",[id]);
 const path='/api/appointments/availability?'+new URLSearchParams({date:'2030-10-17',service:"Women's Cut & Blowdry",stylist:S});
 let body=await (await bookingAvailability(req(path),{query})).json() as {slots:{time:string;available:boolean}[]};assert.equal(body.slots.find(s=>s.time==='09:00')?.available,true);
 await query('UPDATE stylist_work_settings SET available=false WHERE stylist_id=$1',[S]);
 body=await (await bookingAvailability(req(path),{query})).json();assert.deepEqual(body.slots,[]);
});


test('schedule starts at working hours and resumes at actual ninety-minute booking end',()=>{
 const staff=[{id:S,hours}];
 assert.deepEqual(availableBookingSlots('2030-10-17',staff,[],new Date('2030-10-16')).map(s=>s.time),['09:00','10:30','12:00','13:30','15:00']);
 const slots=availableBookingSlots('2030-10-17',staff,[{stylistId:S,appointmentDate:'2030-10-17T02:00:00Z',durationMinutes:30}],new Date('2030-10-16'));
 assert.equal(slots.find(s=>s.time==='11:30')?.available,true);assert.ok(!slots.some(s=>s.available&&['10:30','11:00'].includes(s.time)));
 const today=availableBookingSlots('2030-10-17',staff,[],new Date('2030-10-17T04:00:00Z'));assert.ok(today.every(s=>s.time>'12:00'));
});
test('booking uses database service ID and current price and records its foreign key',async()=>{
 const services=await deps.store.serviceCatalog();const service=services.find(s=>s.name==="Women's Cut & Blowdry");assert.ok(service);
 await query('UPDATE salon_services SET price=$1 WHERE id=$2',['₱321',service.id]);
 try{
 const response=await bookingApi(req('/api/appointments','POST',{serviceId:service.id,serviceName:'forged',serviceType:'wrong',appointmentDate:'2030-10-17T02:00:00Z',stylistId:S,totalPrice:1}),undefined,deps);
 assert.equal(response.status,201);const row=(await query('SELECT a.service_name,a.total_price,s.service_id FROM appointments a JOIN appointment_services s ON s.appointment_id=a.id'))[0];assert.equal(row.total_price,321);assert.equal(row.service_id,service.id);assert.equal(row.service_name,service.name);
 }finally{await query('UPDATE salon_services SET price=$1 WHERE id=$2',[service.price,service.id]);}
});
