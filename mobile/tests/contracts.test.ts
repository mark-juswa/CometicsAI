import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, createApiClient } from '../lib/api/client';
import { parseApiBaseUrl } from '../lib/config/environment';
import { validatePhoto } from '../lib/image/validation';
import { useStudio } from '../store/studio';

const style = { id: 'catalog_style', name: 'Catalog style', description: 'From backend', status: 'available' };
const photo = { uri: 'file:///private/gallery/portrait.jpg', name: 'portrait.jpg', mimeType: 'image/jpeg' as const, width: 512, height: 512, size: 1024 };

test('configuration has no fallback and rejects credentials, non-HTTP URLs and paths', () => {
  assert.equal(parseApiBaseUrl('https://api.example.test/'), 'https://api.example.test');
  for (const value of [undefined, '', 'file:///photo', 'https://user:pass@example.test', 'https://example.test/api', 'https://example.test?key=1']) {
    assert.throws(() => parseApiBaseUrl(value));
  }
});
test('all three catalogs and health use the application API via GET, with no upload', async () => {
  const calls: string[] = [];
  const fetcher: typeof fetch = async (input, init) => {
    calls.push(String(input)); assert.equal(init?.method, 'GET'); assert.equal(init?.body, undefined);
    return Response.json(String(input).endsWith('/health') ? { status: 'ok', generator: 'mock' } : [style]);
  };
  const client = createApiClient('https://api.example.test', fetcher);
  assert.equal((await client.health()).generator, 'mock');
  for (const feature of ['hairstyle', 'makeup', 'nails'] as const) assert.deepEqual(await client.styles(feature), [style]);
  assert.deepEqual(calls, ['https://api.example.test/health', ...['hairstyle', 'makeup', 'nails'].map(id => `https://api.example.test/features/${id}/styles`)]);
});
test('unknown discovery IDs and malformed catalogs are rejected before rendering', async () => {
  const client = createApiClient('https://api.example.test', async () => Response.json([{ id: 'unknown', name: 'Unknown', description: '' }]));
  await assert.rejects(client.features(), (error: unknown) => error instanceof ApiError && error.code === 'invalid_response');
  await assert.rejects(client.styles('nails'), (error: unknown) => error instanceof ApiError && error.code === 'invalid_response');
});
test('backend detail, validation arrays and adapter errors remain controlled', async () => {
  for (const [body, expected] of [
    [{ detail: 'Styles unavailable.' }, 'Styles unavailable.'],
    [{ detail: [{ msg: 'Invalid feature.' }] }, 'Invalid feature.'],
    [{ error: 'Sign in to continue.' }, 'Sign in to continue.'],
  ] as const) {
    const client = createApiClient('https://api.example.test', async () => Response.json(body, { status: 422 }));
    await assert.rejects(client.health(), (error: unknown) => error instanceof ApiError && error.message === expected && error.status === 422);
  }
});
test('HTML failures, broken JSON and network loss show safe errors, never automatic retry', async () => {
  let attempts = 0;
  const html = createApiClient('https://api.example.test', async () => new Response('<html>private proxy</html>', { status: 502 }));
  await assert.rejects(html.health(), /could not complete/);
  const broken = createApiClient('https://api.example.test', async () => new Response('broken'));
  await assert.rejects(broken.health(), /unreadable response/);
  const lost = createApiClient('https://api.example.test', async () => { attempts++; throw new Error('internal details'); });
  await assert.rejects(lost.health(), /Cannot reach/); assert.equal(attempts, 1);
});
test('read deadline aborts a stalled API call', async () => {
  const client = createApiClient('https://api.example.test', async (_input, init) => new Promise((_resolve, reject) => {
    init?.signal?.addEventListener('abort', () => reject(new Error('aborted')), { once: true });
  }), 10);
  await assert.rejects(client.health(), (error: unknown) => error instanceof ApiError && error.code === 'timeout');
});
test('gallery checks match the backend boundaries without changing a photo', () => {
  assert.deepEqual(validatePhoto(photo), photo);
  assert.doesNotThrow(() => validatePhoto({ ...photo, width: 4096, height: 4096, size: 8 * 1024 * 1024 }));
  for (const changes of [{ mimeType: 'image/heic' }, { size: 0 }, { size: 8 * 1024 * 1024 + 1 }, { width: 63 }, { height: 4097 }]) {
    assert.throws(() => validatePhoto({ ...photo, ...changes }));
  }
});
test('photo replacement/removal and style change invalidate previews and reset is feature-local', () => {
  const store = useStudio.getState();
  store.setPhoto('hairstyle', photo); store.selectStyle('hairstyle', style.id); store.showPreview('hairstyle', style);
  store.setPhoto('makeup', photo);
  store.setPhoto('hairstyle', { ...photo, name: 'replacement.jpg' });
  assert.equal(useStudio.getState().drafts.hairstyle.previewStyle, null);
  store.showPreview('hairstyle', style); store.selectStyle('hairstyle', 'another');
  assert.equal(useStudio.getState().drafts.hairstyle.previewStyle, null);
  store.setPhoto('hairstyle', null); assert.equal(useStudio.getState().drafts.hairstyle.photo, null);
  store.reset('hairstyle'); assert.equal(useStudio.getState().drafts.hairstyle.styleId, null);
  assert.deepEqual(useStudio.getState().drafts.makeup.photo, photo); store.reset('makeup');
});
