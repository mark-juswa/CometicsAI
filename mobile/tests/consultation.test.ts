import test from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient, ApiError } from '../lib/api/client';
import { isConsultationState, isConsultationTurn, isGenerationDetail, isRecommendationSet, recommendationsAvailable } from '../lib/api/consultation-contracts';
import { createConsultationSession } from '../store/consultation-session';
import { createGenerationStore } from '../store/generation';
import { createOperationStore } from '../store/ai-operation';
import { consultationPreferences } from '../features/consultation/direction';
import { photo, catalog, state, detail, recommendations } from './consultation-fixtures';

function fake(overrides: Partial<Parameters<typeof createConsultationSession>[0]> = {}) {
  let current = state(); let posts = 0; let reads = 0; const order: string[] = [];
  const client = {
    consultationMode: async () => 'gemini' as const, consultationCatalog: async () => structuredClone(catalog),
    createConsultation: async () => { order.push('create'); return { handle: 'opaque.signed.handle', state: { ...state(), photo: null, messages: [], conversation_status: 'not_started' as const } }; },
    consultationPhoto: async () => { order.push('photo'); return { ...state(), messages: [], conversation_status: 'not_started' as const }; },
    consultationPreferences: async () => { order.push('preferences'); return { ...state(), messages: [], conversation_status: 'not_started' as const }; },
    consultationTurn: async (_: string, message?: string) => { order.push(message ? 'reply' : 'opening'); current = state(Boolean(message));
      return { state: current, status: current.conversation_status as 'more_information' | 'ready_for_recommendation', recommendations: current.recommendations }; },
    consultationState: async () => structuredClone(current),
    consultationGenerate: async (_: string, id: string) => { posts++; return detail(id); },
    consultationGeneration: async (_: string, id: string) => { reads++; return detail(id); },
    consultationSelect: async (_: string, id: string) => ({ ...state(true), selected_recommendation_id: id }), ...overrides,
  };
  return { client, order, posts: () => posts, reads: () => reads };
}
async function prepare(store: ReturnType<typeof createConsultationSession>) {
  await store.getState().begin('hairstyle', photo, { occasion: 'Everyday' }, 'client-test', async () => new FormData());
  await store.getState().reply('Short and low maintenance');
}

test('all native Consultation methods retain opaque handles, cookies, canonical mutation Origin and private IDs stay server side', async () => {
  const calls: { url: string; init?: RequestInit }[] = [];
  const client = createApiClient('http://127.0.0.1:3000', async (url, init) => {
    calls.push({ url: String(url), init }); const path = new URL(String(url)).pathname;
    let body: unknown = state(true);
    if (path.endsWith('/consultations')) body = { ...state(), handle: 'opaque.signed.handle', photo: { id: 'server-photo-id', ...state().photo } };
    if (path.endsWith('/turn')) { await new Promise(r => setTimeout(r, 15)); assert.equal(init?.signal?.aborted, false); body = { state: state(true), status: 'ready_for_recommendation', recommendations }; }
    if (path.endsWith('/generation')) body = detail();
    if (path.endsWith('/recommendations')) body = recommendations;
    return Response.json(body);
  }, 2);
  const created = await client.createConsultation('hairstyle'); assert.equal('id' in created.state, false); assert.equal('id' in created.state.photo!, false);
  const handle = created.handle; const upload = new FormData(); upload.append('image', new Blob(['fixture'], { type: 'image/png' }), 'portrait.png');
  await client.consultationPhoto(handle, upload); await client.consultationPreferences(handle, { hair_maintenance: 'low' });
  await client.consultationTurn(handle, 'Short please'); await client.consultationState(handle); await client.consultationRecommendations(handle);
  await client.consultationGenerate(handle, 'look_1'); await client.consultationGeneration(handle, 'look_1'); await client.consultationSelect(handle, 'look_1');
  for (const call of calls) {
    assert.ok(call.url.startsWith('http://127.0.0.1:3000/api/ai/consultations')); assert.equal(call.url.includes(handle), false);
    const headers = new Headers(call.init?.headers); assert.equal(call.init?.credentials, 'include');
    assert.equal(headers.get('x-ai-consultation-handle'), call.url.endsWith('/consultations') ? null : handle);
    assert.equal(headers.get('Origin'), call.init?.method === 'GET' ? null : 'http://localhost:3000');
    assert.equal(headers.get('Authorization'), null);
  }
  assert.equal(calls[1].init?.method, 'PUT'); assert.deepEqual([...upload.keys()], ['image']);
  assert.equal(calls[2].init?.method, 'PATCH'); assert.deepEqual(JSON.parse(String(calls[2].init?.body)), { preferences: { hair_maintenance: 'low' } });
  assert.equal(calls.filter(c => c.url.endsWith('/generation') && c.init?.method === 'POST').length, 1);
});

test('backend readiness, exactly three unique known styles and real matching results are enforced', () => {
  assert.equal(isConsultationState(state(true)), true); assert.equal(isRecommendationSet(recommendations), true);
  assert.equal(isRecommendationSet({ recommendations: recommendations.recommendations.slice(0, 2) }), false);
  assert.equal(isRecommendationSet({ recommendations: Array(3).fill(recommendations.recommendations[0]) }), false);
  assert.equal(isConsultationState({ ...state(), conversation_status: 'ready_for_recommendation' }), false);
  assert.equal(isConsultationState({ ...state(), id: 'raw-upstream-id' }), false);
  assert.equal(isConsultationTurn({ state: state(), status: 'ready_for_recommendation', recommendations }), false);
  assert.equal(recommendationsAvailable(state(true), { ...catalog, hairstyle: catalog.hairstyle.slice(1) }), false);
  assert.equal(recommendationsAvailable(state(true), { ...catalog, hairstyle: catalog.hairstyle.map(s => ({ ...s, status: 'disabled' })) }), false);
  assert.equal(isGenerationDetail({ ...detail(), result: { ...detail().result!, generator: 'mock' } }), false);
  assert.equal(isGenerationDetail({ ...detail(), result: null }), false);
});

test('structured direction maps only the selected service fields and bounded avoids', () => {
  const direction = { occasion: ' Everyday ', vibe: 'Classic', notes: '', avoids: 'a,b,c,d,e,f', servicePreference: 'Low' };
  assert.deepEqual(consultationPreferences('hairstyle', direction), { occasion: 'Everyday', vibe: 'Classic', avoids: ['a', 'b', 'c', 'd', 'e'], notes: undefined, hair_maintenance: 'low' });
  const makeup = consultationPreferences('makeup', { ...direction, servicePreference: 'Soft' });
  assert.equal(makeup.makeup_intensity, 'soft'); assert.equal(makeup.hair_maintenance, undefined);
  assert.equal(consultationPreferences('nails', { ...direction, servicePreference: 'French' }).nail_finish, 'french');
});

test('create, photo upload, preferences and genuine turns precede backend readiness; generation is explicit and Select is confirmed', async () => {
  const f = fake(); let clock = 1000; const store = createConsultationSession(f.client, () => clock);
  await prepare(store); assert.deepEqual(f.order, ['create', 'photo', 'preferences', 'reply']);
  assert.equal(store.getState().state?.recommendations?.recommendations.length, 3); assert.equal(f.posts(), 0);
  assert.deepEqual(store.getState().original, photo); assert.equal(store.getState().userId, 'client-test');
  clock = 62000; await store.getState().generate('look_1'); assert.equal(f.posts(), 1); assert.equal(store.getState().active, null);
  assert.equal(store.getState().details.look_1.generation.status, 'completed');
  assert.equal(await store.getState().select('look_1'), true); assert.equal(store.getState().state?.selected_recommendation_id, 'look_1');
  await store.getState().generate('look_1'); assert.equal(f.posts(), 1); assert.equal(store.getState().clear(), true);
  assert.equal(store.getState().handle, null); assert.equal(store.getState().original, null);
});

test('Consultation and Custom share a generation guard, including duplicate taps and navigation while in flight', async () => {
  let finish!: (v: ReturnType<typeof detail>) => void; let posts = 0;
  const f = fake({ consultationGenerate: async () => { posts++; return new Promise(r => { finish = r; }); } });
  const operation = createOperationStore(); const store = createConsultationSession(f.client, Date.now, operation);
  const custom = createGenerationStore(async () => { throw new Error('Must never dispatch'); }, Date.now, operation);
  await prepare(store); const running = store.getState().generate('look_1');
  await store.getState().generate('look_2'); await store.getState().generate('look_1');
  await custom.getState().run('hairstyle', photo, catalog.hairstyle[0], 'client-test', async () => new FormData());
  assert.equal(posts, 1); assert.equal(custom.getState().job, null); assert.equal(store.getState().clear(), false);
  await store.getState().checkGeneration(); assert.equal(f.reads(), 0); finish(detail()); await running;
  assert.equal(operation.getState().owner, null);
});

test('lost generation response recovers by status GET, never another POST; unresolved pending remains locked', async () => {
  let posts = 0; let reads = 0; let status: 'generating' | 'completed' | 'pending' = 'generating';
  const f = fake({ consultationGenerate: async () => { posts++; throw new ApiError('Lost response', 'network'); },
    consultationGeneration: async () => { reads++; return detail('look_1', status); } });
  const operation = createOperationStore(); const store = createConsultationSession(f.client, Date.now, operation); await prepare(store);
  await store.getState().generate('look_1'); assert.equal(reads, 1); assert.equal(store.getState().active?.phase, 'unknown');
  status = 'pending'; await store.getState().checkGeneration(); await store.getState().generate('look_2');
  assert.equal(posts, 1); assert.equal(operation.getState().owner, 'consultation'); assert.equal(store.getState().clear(), false);
  status = 'completed'; await store.getState().checkGeneration(); assert.equal(store.getState().active, null);
  assert.equal(store.getState().error, ''); assert.equal(store.getState().details.look_1.result?.style.id, 'crew_cut'); assert.equal(posts, 1);
});

test('confirmed failed generation permits an explicit retry, retains siblings and makes no automatic requests', async () => {
  let posts = 0; const f = fake({ consultationGenerate: async (_, id) => { posts++; if (posts === 1) throw new ApiError('AI unavailable', 'http', 503); return detail(id); },
    consultationGeneration: async () => detail('look_1', 'failed') });
  const store = createConsultationSession(f.client); await prepare(store); await store.getState().generate('look_1');
  assert.equal(posts, 1); assert.equal(store.getState().active, null); assert.equal(store.getState().details.look_1.generation.status, 'failed');
  await store.getState().generate('look_2'); assert.equal(posts, 2);
  await store.getState().generate('look_1'); assert.equal(posts, 3); assert.equal(store.getState().details.look_2.generation.status, 'completed');
});

test('unavailable Gemini and ambiguous text turns require state reconciliation rather than automatic replay', async () => {
  let turns = 0; const f = fake({ consultationTurn: async () => { turns++; throw new ApiError('AI unavailable', 'http', 503); } });
  const store = createConsultationSession(f.client);
  await store.getState().begin('hairstyle', photo, {}, 'client-test', async () => new FormData());
  assert.equal(turns, 0); await store.getState().reply('Hello');
  assert.equal(turns, 1); assert.equal(store.getState().needsSync, true); await store.getState().reply('Hello'); assert.equal(turns, 1);
  await store.getState().refresh(); assert.equal(store.getState().needsSync, false); await store.getState().reply('Hello'); assert.equal(turns, 2);
  assert.equal(f.posts(), 0);
});

test('first user description starts Gemini only after photo and preferences, without an empty opening turn', async () => {
  let turns = 0; let firstMessage = '';
  const f = fake({ consultationTurn: async (_, message) => {
    turns++;
    assert.ok(message);
    firstMessage = message; return { state: state(true), status: 'ready_for_recommendation', recommendations };
  } });
  const store = createConsultationSession(f.client);
  await store.getState().begin('hairstyle', photo, {}, 'client-test', async () => new FormData());
  assert.equal(turns, 0); assert.equal(store.getState().needsSync, false);
  assert.equal(store.getState().state?.conversation_status, 'not_started');
  assert.equal(await store.getState().reply('A classic, short, low maintenance Hair look.'), true);
  assert.equal(turns, 1);
  assert.equal(firstMessage, 'A classic, short, low maintenance Hair look.');
  assert.equal(store.getState().state?.recommendations?.recommendations.length, 3);
  assert.equal(f.posts(), 0);
});

test('a lost first text turn still requires explicit status reconciliation before another POST', async () => {
  let turns = 0; let reads = 0;
  const f = fake({ consultationTurn: async () => { turns++; throw new ApiError('Connection lost', 'network'); },
    consultationState: async () => { reads++; return state(); } });
  const store = createConsultationSession(f.client);
  await store.getState().begin('hairstyle', photo, {}, 'client-test', async () => new FormData());
  assert.equal(turns, 0); assert.equal(reads, 0);
  await store.getState().reply('A short haircut'); assert.equal(turns, 1); assert.equal(store.getState().needsSync, true);
  await store.getState().reply('A short haircut'); assert.equal(turns, 1);
  await store.getState().refresh(); assert.equal(reads, 1); assert.equal(store.getState().needsSync, false);
});

test('unknown or disabled recommendations fail closed; invalid session/expired handle show controlled errors and preserve photo until reset', async () => {
  const f = fake({ consultationCatalog: async () => ({ ...catalog, hairstyle: [] }) }); const store = createConsultationSession(f.client);
  await prepare(store); await store.getState().generate('look_1'); assert.equal(f.posts(), 0); assert.match(store.getState().error, /unavailable/);
  for (const status of [401, 403, 404]) {
    const f = fake({ consultationState: async () => { throw new ApiError('Rejected', 'http', status); } });
    const store = createConsultationSession(f.client); await prepare(store); await store.getState().refresh();
    assert.match(store.getState().error, status === 401 ? /session has ended/ : /expired/); assert.deepEqual(store.getState().original, photo);
    assert.equal(store.getState().clear(), true); assert.equal(store.getState().handle, null);
  }
});

test('wrong result or recommendation identity cannot be accepted or release an uncertain generation lock', async () => {
  const wrong = detail('look_2'); const f = fake({ consultationGenerate: async () => wrong, consultationGeneration: async () => wrong });
  const store = createConsultationSession(f.client); await prepare(store); await store.getState().generate('look_1');
  assert.equal(store.getState().details.look_1, undefined); assert.equal(store.getState().active?.phase, 'unknown'); assert.match(store.getState().error, /does not match/);
});

test('unconfigured conversational mode and invalid photo preparation do not create fake consultation or generation work', async () => {
  const f = fake({ consultationMode: async () => 'deterministic' }); const store = createConsultationSession(f.client);
  await store.getState().begin('hairstyle', photo, {}, 'client-test', async () => new FormData());
  assert.equal(f.order.length, 0); assert.match(store.getState().error, /not available in this server mode/); assert.equal(store.getState().state, null);
  const real = fake(); const other = createConsultationSession(real.client);
  await other.getState().begin('hairstyle', photo, {}, 'client-test', async () => { throw new Error('Invalid selected photo'); });
  assert.equal(real.order.length, 0); assert.match(other.getState().error, /Invalid selected photo/); assert.equal(real.posts(), 0);
});
