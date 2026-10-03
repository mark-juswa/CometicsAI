import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, createApiClient, safeGenerationRetry } from '../lib/api/client';
import type { GenerationResult } from '../lib/api/contracts';
import { createGenerationStore } from '../store/generation';

const style = { id: 'crew_cut', name: 'Crew Cut', description: 'Catalog description', status: 'available' };
const photo = { uri: 'file:///local/photo.jpg', name: 'photo.jpg', mimeType: 'image/jpeg' as const, width: 512, height: 512, size: 1024 };
const user = { id: 'client-test', name: 'Client', email: 'client@example.test', role: 'client', avatar: null };
const result: GenerationResult = { status: 'completed', generator: 'remote_flux', style,
  image: { data_url: 'data:image/png;base64,AA==', content_type: 'image/png', width: 512, height: 512 }, metadata: {} };
const upload = async () => new FormData();

test('login, session and logout use the native cookie jar and only the configured application Origin', async () => {
  const calls: { url: string; init?: RequestInit }[] = [];
  const client = createApiClient('https://application.example.test', async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json(String(url).endsWith('/logout') ? { success: true } : { user });
  });
  assert.deepEqual(await client.login(user.email, 'test-only-password'), { user });
  assert.deepEqual(await client.session(), { user });
  assert.deepEqual(await client.logout(), { success: true });
  assert.deepEqual(calls.map(call => call.url), ['login', 'session', 'logout'].map(route => `https://application.example.test/api/auth/${route}`));
  for (const call of calls) {
    assert.equal(call.init?.credentials, 'include');
    assert.equal(new Headers(call.init?.headers).get('Cookie'), null);
    assert.equal(new Headers(call.init?.headers).get('Authorization'), null);
    assert.equal(new Headers(call.init?.headers).get('Origin'), call.init?.method === 'POST' ? 'https://application.example.test' : null);
  }
  assert.deepEqual(JSON.parse(String(calls[0].init?.body)), { email: user.email, password: 'test-only-password' });
});

test('all feature generations send multipart once through the fixed adapter without a short read deadline', async () => {
  for (const feature of ['hairstyle', 'makeup', 'nails'] as const) {
    let attempts = 0;
    const body = new FormData(); body.append('image', new Blob(['image'], { type: 'image/png' }), 'photo.png'); body.append('style_id', style.id);
    const client = createApiClient('https://application.example.test', async (url, init) => {
      attempts++; assert.equal(String(url), `https://application.example.test/api/ai/features/${feature}/generate`);
      assert.equal(init?.body, body); assert.equal(init?.credentials, 'include');
      assert.equal(new Headers(init?.headers).get('Content-Type'), null);
      await new Promise(resolve => setTimeout(resolve, 25));
      assert.equal(init?.signal?.aborted, false);
      return Response.json(result);
    }, 2);
    assert.deepEqual(await client.generate(feature, style.id, body), result); assert.equal(attempts, 1);
    assert.deepEqual([...body.keys()], ['image', 'style_id']);
  }
});

test('loopback mutations match NextURL canonical Origin while cookies and transport keep the configured host', async () => {
  const client = createApiClient('http://127.0.0.1:3000', async (url, init) => {
    assert.equal(String(url), 'http://127.0.0.1:3000/api/auth/logout');
    assert.equal(new Headers(init?.headers).get('Origin'), 'http://localhost:3000');
    assert.equal(init?.credentials, 'include');
    return Response.json({ success: true });
  });
  await client.logout();
});

test('a mock, external image, malformed result or wrong style cannot become an accepted real result', async () => {
  for (const invalid of [ { ...result, generator: 'mock' }, { ...result, status: 'pending' },
    { ...result, style: { ...style, id: 'different' } }, { ...result, image: { ...result.image, data_url: 'https://upstream.example.test/private.png' } },
    { ...result, image: { ...result.image, width: 0 } }, { ...result, metadata: null } ]) {
    let calls = 0;
    const client = createApiClient('https://application.example.test', async () => { calls++; return Response.json(invalid); });
    await assert.rejects(client.generate('hairstyle', style.id, new FormData()), (error: unknown) => error instanceof ApiError && error.code === 'invalid_response');
    assert.equal(calls, 1);
  }
});

test('duplicate taps across services share one in flight operation and retain its original photo', async () => {
  let finish!: (value: GenerationResult) => void; let calls = 0; let clock = 1000;
  const store = createGenerationStore(async () => { calls++; return new Promise(resolve => { finish = resolve; }); }, () => clock);
  const first = store.getState().run('hairstyle', photo, style, user.id, upload);
  await Promise.resolve();
  await store.getState().run('nails', photo, style, user.id, upload);
  store.getState().clear();
  assert.equal(calls, 1); assert.equal(store.getState().job?.feature, 'hairstyle');
  assert.equal(store.getState().job?.phase, 'running'); assert.deepEqual(store.getState().job?.original, photo);
  clock = 62000; finish(result); await first;
  assert.equal(store.getState().job?.phase, 'completed'); assert.equal(store.getState().job?.endedAt, 62000);
  assert.deepEqual(store.getState().job?.result, result);
  store.getState().clear(); assert.equal(store.getState().job, null);
});

test('response loss and upstream failures remain locked until explicit operator confirmation, without automatic retry', async () => {
  for (const error of [new ApiError('Lost response', 'network'), new ApiError('Read lost', 'timeout'), new ApiError('AI unavailable', 'http', 503),
    new ApiError('Already running', 'http', 409), new ApiError('Bad result', 'invalid_response')]) {
    let calls = 0;
    const store = createGenerationStore(async () => { calls++; throw error; });
    await store.getState().run('hairstyle', photo, style, user.id, upload);
    assert.equal(store.getState().job?.phase, 'uncertain');
    store.getState().clear();
    await store.getState().run('makeup', photo, style, user.id, upload);
    assert.equal(calls, 1); assert.equal(store.getState().job?.phase, 'uncertain');
    store.getState().acknowledgeEnded(); assert.equal(calls, 1); assert.equal(store.getState().job?.phase, 'failed');
    await store.getState().run('hairstyle', photo, style, user.id, upload); assert.equal(calls, 2);
  }
});

test('invalid login, authorization and validation failures permit only an explicit manual retry', async () => {
  for (const status of [400, 401, 403, 404, 413, 415, 422, 429]) {
    let calls = 0;
    const client = createApiClient('https://application.example.test', async () => { calls++; return Response.json({ error: 'Controlled rejection' }, { status }); });
    const store = createGenerationStore(client.generate);
    await store.getState().run('hairstyle', photo, style, user.id, upload);
    assert.equal(store.getState().job?.phase, 'failed'); assert.equal(calls, 1);
    assert.equal(safeGenerationRetry(new ApiError('Rejected', 'http', status)), true);
    await store.getState().run('hairstyle', photo, style, user.id, upload); assert.equal(calls, 2);
  }
  const client = createApiClient('https://application.example.test', async () => Response.json({ error: 'Invalid email or password' }, { status: 401 }));
  await assert.rejects(client.login(user.email, 'wrong'), /Invalid email or password/);
});

test('failed photo preparation never dispatches generation and remains correctable', async () => {
  let calls = 0;
  const store = createGenerationStore(async () => { calls++; return result; });
  await store.getState().run('hairstyle', photo, style, user.id, async () => { throw new Error('Invalid photo'); });
  assert.equal(calls, 0); assert.equal(store.getState().job?.phase, 'failed');
  await store.getState().run('hairstyle', photo, style, user.id, upload);
  assert.equal(calls, 1); assert.equal(store.getState().job?.phase, 'completed');
});
