import test from 'node:test';
import assert from 'node:assert/strict';
import { activeRuntimeEndpoint, canonicalRuntime, handleRuntimeRegistration, signRuntime,
  type RuntimeLease, type RuntimeMessage, type RuntimeStore } from '../lib/ai/runtime-registry';
import { handleAiRequest } from '../lib/ai/adapter-core';

const KEY = 'test-only-runtime-key-at-least-thirty-two-characters';
const A = '09b53a8b-e8a6-4a88-946e-355dbfab2c6d';
const B = '40790d2f-4d88-4264-b3c1-886803d5641b';
let now = 1791540000000;
function message(changes: Partial<RuntimeMessage> = {}): RuntimeMessage {
  return { schema: 'beautycore-runtime-v1', operation: 'register', session_id: A,
    endpoint: 'https://fixture-a.trycloudflare.com', started_at: now / 1000 - 60,
    issued_at: now / 1000, ...changes };
}
class MemoryStore implements RuntimeStore {
  row: RuntimeLease | null = null;
  writes = 0;
  async get() { return this.row; }
  async claim(m: RuntimeMessage) {
    if (this.row && (m.issued_at <= this.row.lastIssuedAt ||
      !(this.row.sessionId === m.session_id && this.row.endpoint === m.endpoint && this.row.startedAt === m.started_at ||
        this.row.expiresAt <= now && m.started_at > this.row.startedAt))) return null;
    return this.save(m);
  }
  async renew(m: RuntimeMessage) {
    if (!this.row || this.row.sessionId !== m.session_id || this.row.endpoint !== m.endpoint ||
      this.row.startedAt !== m.started_at || this.row.expiresAt <= now || this.row.lastIssuedAt >= m.issued_at) return null;
    return this.save(m);
  }
  save(m: RuntimeMessage) {
    this.writes++;
    return this.row = { sessionId: m.session_id, endpoint: m.endpoint, startedAt: m.started_at,
      lastIssuedAt: m.issued_at, expiresAt: now + 180000 };
  }
}
function request(m: RuntimeMessage, signature = signRuntime(m, KEY)): Request {
  return new Request('https://app.onrender.com/api/internal/ai-runtime/register', { method: 'POST',
    headers: { 'content-type': 'application/json', 'x-ai-runtime-signature': signature }, body: JSON.stringify(m) });
}
function harness() {
  const store = new MemoryStore();
  const seen: { url: string; init?: RequestInit }[] = [];
  const upstreamFetch: typeof fetch = async (input, init) => {
    seen.push({ url: String(input), init });
    return String(input).endsWith('/health') ? Response.json({ status: 'ok', service: 'render-kaggle-demo-v1' })
      : Response.json({ ready: true, reason: 'ready', foundation_load_count: 1,
        diagnostics_version: 'deployment-01', nails_inference_steps: 8, supported_features: ['hairstyle','makeup','nails'] });
  };
  const deps = { enabled: true, key: KEY, store, upstreamFetch, now: () => now };
  return { store, seen, deps, call: (m: RuntimeMessage) => handleRuntimeRegistration(request(m), deps) };
}
test.beforeEach(() => { now = 1791540000000; });
test('register checks facade/authenticated readiness and stores one lease', async () => {
  const h = harness();
  assert.equal((await h.call(message())).status, 200);
  assert.equal(await activeRuntimeEndpoint(h.store, now), message().endpoint);
  assert.equal(h.seen.length, 2);
  for (const row of h.seen) {
    assert.equal(row.init?.redirect, 'error');
    assert.equal(new Headers(row.init?.headers).get('x-ai-backend-key'), KEY);
    assert(!row.url.includes(KEY));
  }
});
test('missing/wrong/tampered signature cannot query/store a destination', async () => {
  const h = harness();
  for (const signature of ['', '0'.repeat(64)]) {
    assert.equal((await handleRuntimeRegistration(request(message(), signature), h.deps)).status, 401);
  }
  const original = message();
  const tampered = { ...original, endpoint: 'https://other.trycloudflare.com' };
  assert.equal((await handleRuntimeRegistration(request(tampered, signRuntime(original, KEY)), h.deps)).status, 401);
  assert.equal(h.seen.length, 0); assert.equal(h.store.writes, 0);
});
test('canonical Python-compatible message and signature fixture', () => {
  const m = message();
  assert.equal(canonicalRuntime(m), JSON.stringify({endpoint:m.endpoint,issued_at:m.issued_at,operation:m.operation,
    schema:m.schema,session_id:m.session_id,started_at:m.started_at}));
  assert.equal(signRuntime(m, KEY), '875a28e74f807d27d8118f93d89908d35be2c8c896f3331208d83eaafa895483');
});
for (const endpoint of ['http://127.0.0.1:8800', 'https://fixture.trycloudflare.com:443',
  'https://user:pw@fixture.trycloudflare.com', 'https://fixture.trycloudflare.com/path',
  'https://fixture.trycloudflare.com?query=yes', 'https://evil.example', 'https://fixture.trycloudflare.com/']) {
  test('unsafe/noncanonical endpoint rejected: ' + endpoint, async () => {
    const h = harness(); assert.equal((await h.call(message({endpoint}))).status, 400);
    assert.equal(h.seen.length, 0);
  });
}
test('expired timestamps, unknown fields and oversized streamed bodies fail', async () => {
  const h = harness();
  assert.equal((await h.call(message({issued_at:now/1000-1000,started_at:now/1000-1100}))).status, 400);
  assert.equal((await h.call({...message(), extra:'invalid'} as RuntimeMessage)).status, 400);
  const r = new Request('https://app.onrender.com/api/internal/ai-runtime/register', {method:'POST',
    headers:{'content-type':'application/json','x-ai-runtime-signature':'a'.repeat(64)}, body:'x'.repeat(4096)});
  assert.equal((await handleRuntimeRegistration(r,h.deps)).status,400);
  assert.equal(h.store.writes,0);
});
test('redirect, wrong feature/readiness and storage failures do not register', async () => {
  const h = harness();
  for (const response of [new Response('',{status:302}), Response.json({status:'ok',service:'wrong-service'})]) {
    const result = await handleRuntimeRegistration(request(message()),{...h.deps,upstreamFetch:async()=>response});
    assert.equal(result.status,503);
  }
  const result = await handleRuntimeRegistration(request(message()),{...h.deps,store:{...h.store,
    get:async()=>{throw new Error('private database error');},claim:async()=>null,renew:async()=>null}});
  assert.equal(result.status,503); assert(!(await result.text()).includes('private database'));
  assert.equal(h.store.writes,0);
});
test('duplicate acknowledgement does not extend lease; old timestamps are refused', async () => {
  const h = harness(); const m=message(); await h.call(m); const expiry=h.store.row!.expiresAt;
  now+=10000; assert.equal((await h.call(m)).status,200);
  assert.equal(h.store.row!.expiresAt,expiry); assert.equal(h.store.writes,1);
  assert.equal((await h.call({...m,issued_at:m.issued_at-1})).status,409);
});
test('heartbeat renews without GPU readiness so an active generation stays usable', async () => {
  const h=harness(); const m=message(); await h.call(m); now+=60000;
  assert.equal((await h.call({...m,operation:'renew',issued_at:now/1000})).status,200);
  assert.equal(h.seen.length,2); assert.equal(h.store.row!.expiresAt,now+180000);
});
test('active session cannot be replaced; expiry and newer birth allow atomic takeover', async () => {
  const h=harness(); const first=message(); await h.call(first); now+=60000;
  const newer=message({session_id:B,endpoint:'https://fixture-b.trycloudflare.com',started_at:now/1000});
  assert.equal((await h.call(newer)).status,409);
  now+=180000; assert.equal(await activeRuntimeEndpoint(h.store,now),null);
  assert.equal((await h.call({...newer,issued_at:now/1000})).status,200);
  now+=60000;
  assert.equal((await h.call({...first,operation:'renew',issued_at:now/1000})).status,409);
  now+=180000;
  assert.equal((await h.call({...first,issued_at:now/1000})).status,409);
});
test('expired renewals cannot revive a lease',async()=>{
  const h=harness();const m=message();await h.call(m);now+=180000;
  assert.equal((await h.call({...m,operation:'renew',issued_at:now/1000})).status,409);
});
test('claim race losing atomic write is reported without false acknowledgement',async()=>{
  const h=harness(); h.store.claim=async()=>null;
  assert.equal((await h.call(message())).status,409);
});
test('bridge uses dynamic endpoint, fails closed and does not query it for unauthenticated clients',async()=>{
  const req=()=>new Request('https://app.onrender.com/api/ai/features');
  let resolutions=0, dispatches=0;
  const deps={baseUrl:'https://stale.trycloudflare.com',remoteBackend:true,backendKey:KEY,handleSecret:KEY,
    currentUser:async()=>({id:'client-one',role:'client'}),
    resolveBaseUrl:async()=>{resolutions++;return null as string|null;},
    upstreamFetch:async(input:RequestInfo|URL)=>{dispatches++;assert.equal(String(input),'https://active.trycloudflare.com/features');return Response.json({ok:true});}};
  assert.equal((await handleAiRequest(req(),['features'],{...deps,currentUser:async()=>null})).status,401);
  assert.equal(resolutions,0);
  assert.equal((await handleAiRequest(req(),['features'],deps)).status,503);assert.equal(dispatches,0);
  assert.equal((await handleAiRequest(req(),['features'],{...deps,resolveBaseUrl:async()=>'https://active.trycloudflare.com'})).status,200);
});
