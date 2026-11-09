import test from 'node:test';
import assert from 'node:assert/strict';
import { GenerationStore } from '../lib/ai/generation-store';
import { AiClientError, type GeneratedResult, type JobOptions } from '../lib/ai/browser-client';
import { DRAFT_TTL, ticketKey, type Assets } from '../lib/ai/generation-storage';

const jobId = '11111111-1111-4111-8111-111111111111';
const result: GeneratedResult = { status: 'completed', style: { id: 'red', name: 'Red', description: '', status: 'available' },
  image: { data_url: 'data:image/png;base64,AA==', content_type: 'image/png', width: 1, height: 1 } };
class MemoryStorage implements Storage {
  values = new Map<string, string>();
  get length() { return this.values.size; }
  clear() { this.values.clear(); }
  getItem(key: string) { return this.values.get(key) ?? null; }
  key(index: number) { return [...this.values.keys()][index] ?? null; }
  removeItem(key: string) { this.values.delete(key); }
  setItem(key: string, value: string) { this.values.set(key, value); }
}
function fixture() {
  const storage = new MemoryStorage(), saved = new Map<string, Assets>();
  const assets = { read: async (key: string) => saved.get(key),
    write: async (key: string, value: Assets) => { saved.set(key, value); }, remove: async (key: string) => { saved.delete(key); } };
  return { storage, assets, saved };
}
const settle = () => new Promise(resolve => setTimeout(resolve, 10));

test('refresh resumes admitted ticket and photo without another POST, then restores cached completion', async () => {
  const deps = fixture(); let posts = 0, gets = 0;
  const first = new GenerationStore('alice', { ...deps, generate: async (_f, _p, _s, options?: JobOptions) => {
    posts++; options?.onAccepted?.(jobId); throw new AiClientError('offline', 502, true);
  } });
  await first.start(); first.setFile('makeup', new File(['portrait'], 'face.png', { type: 'image/png' })); first.select('makeup', 'red');
  await first.run('makeup'); await settle();
  assert.equal(first.getSnapshot().drafts.makeup.phase, 'unknown'); first.stop();
  const second = new GenerationStore('alice', { ...deps, resume: async ticket => { gets++; assert.equal(ticket, jobId); return result; } });
  await second.start(); await settle();
  assert.equal(second.getSnapshot().drafts.makeup.file?.name, 'face.png');
  assert.equal(second.getSnapshot().drafts.makeup.styleId, 'red');
  assert.equal(second.getSnapshot().drafts.makeup.result, result);
  assert.equal(posts, 1); assert.equal(gets, 1); second.stop();
  const third = new GenerationStore('alice', { ...deps, resume: async () => { throw Error('cached output should be restored'); } });
  await third.start(); assert.equal(third.getSnapshot().drafts.makeup.result, result); third.stop();
});

test('shared store rejects overlapping features and ignores completion after account teardown', async () => {
  const deps = fixture(); let complete!: (value: GeneratedResult) => void; let posts = 0;
  const store = new GenerationStore('alice', { ...deps, generate: async (_f, _p, _s, options?: JobOptions) => {
    posts++; options?.onAccepted?.(jobId); return new Promise(resolve => { complete = resolve; });
  } });
  await store.start();
  for (const feature of ['hairstyle', 'nails'] as const) { store.setFile(feature, new File(['p'], 'p.png', { type: 'image/png' })); store.select(feature, 'red'); }
  const running = store.run('hairstyle'); await store.run('nails'); assert.equal(posts, 1);
  store.stop(); complete(result); await running;
  assert.equal(store.getSnapshot().drafts.hairstyle.result, null);
  const other = new GenerationStore('bob', deps); await other.start();
  assert.equal(other.getSnapshot().drafts.hairstyle.file, null); assert.equal(other.getSnapshot().drafts.hairstyle.jobId, undefined); other.stop();
});

test('uncertain admission without ticket blocks replacement until expiry', async () => {
  const deps = fixture(); let posts = 0;
  const store = new GenerationStore('alice', { ...deps, generate: async () => { posts++; throw new AiClientError('response lost', 502, true); } });
  await store.start(); store.setFile('nails', new File(['p'], 'p.png', { type: 'image/png' })); store.select('nails', 'red');
  await store.run('nails'); await store.recover('nails'); await store.run('nails');
  assert.equal(posts, 1); assert.equal(store.getSnapshot().drafts.nails.phase, 'unknown');
  assert.match(store.getSnapshot().drafts.nails.error, /before its ticket/);
  store.getSnapshot().drafts.nails.expires = Date.now() - 1; store.tick();
  assert.equal(store.getSnapshot().drafts.nails.phase, 'failed'); assert.equal(store.busyFeature(), undefined); store.stop();
});

test('expired and mismatched tickets cannot restore images or start recovery', async () => {
  const deps = fixture(); const key = ticketKey('alice', 'makeup');
  deps.storage.setItem(key, JSON.stringify({ owner: 'bob', feature: 'makeup', jobId, styleId: 'red', phase: 'generating', expires: Date.now() + DRAFT_TTL }));
  deps.saved.set(key, { file: new File(['p'], 'secret.png'), result, expires: Date.now() + DRAFT_TTL });
  const store = new GenerationStore('alice', { ...deps, resume: async () => { throw Error('must not poll invalid ticket'); } });
  await store.start(); assert.equal(store.getSnapshot().drafts.makeup.file, null); assert.equal(deps.saved.has(key), false); store.stop();
});

test('missing worker result is terminal and recovery never submits replacement', async () => {
  const deps = fixture(); deps.storage.setItem(ticketKey('alice', 'hairstyle'), JSON.stringify({ owner: 'alice', feature: 'hairstyle', jobId,
    styleId: 'red', phase: 'generating', error: '', expires: Date.now() + DRAFT_TTL }));
  const store = new GenerationStore('alice', { ...deps, resume: async () => { throw new AiClientError('not found', 404, true); },
    generate: async () => { throw Error('replacement POST forbidden'); } });
  await store.start(); await settle(); assert.equal(store.getSnapshot().drafts.hairstyle.phase, 'failed');
  assert.match(store.getSnapshot().drafts.hairstyle.error, /unavailable or expired/); store.stop();
});

test('storage failure warns but does not prevent an explicit generation or replay it', async () => {
  const deps = fixture(); let posts = 0;
  deps.storage.setItem = () => { throw Error('quota'); };
  deps.assets.write = async () => { throw Error('disabled'); };
  const store = new GenerationStore('alice', { ...deps, generate: async () => { posts++; return result; } });
  await store.start(); store.setFile('makeup', new File(['p'], 'p.png')); store.select('makeup', 'red');
  await store.run('makeup'); await settle(); assert.equal(posts, 1);
  assert.equal(store.getSnapshot().drafts.makeup.result, result); assert.match(store.getSnapshot().warning, /storage is unavailable/); store.stop();
});

test('another tab ticket blocks admission even without Web Locks', async () => {
  const deps = fixture(); const store = new GenerationStore('alice', { ...deps, generate: async () => { throw Error('must not POST'); } });
  await store.start(); store.setFile('makeup', new File(['p'], 'p.png')); store.select('makeup', 'red');
  const ticket = { owner: 'alice', feature: 'makeup', jobId, styleId: 'red', phase: 'generating', error: '', expires: Date.now() + DRAFT_TTL };
  deps.storage.setItem(ticketKey('alice', 'makeup'), JSON.stringify(ticket));
  await store.run('makeup'); assert.match(store.getSnapshot().drafts.makeup.error, /Another preview/);
  assert.equal(JSON.parse(deps.storage.getItem(ticketKey('alice', 'makeup'))!).jobId, jobId); store.stop();
});

test('a tab following a new job never pairs its old portrait with the new output or overwrites the submitted photo', async () => {
  const deps = fixture(); let count = 0, finish!: (value: GeneratedResult) => void;
  const nextJob = '22222222-2222-4222-8222-222222222222';
  const primary = new GenerationStore('alice', { ...deps, generate: async (_f, _p, _s, options?: JobOptions) => {
    options?.onAccepted?.(++count === 1 ? jobId : nextJob);
    return count === 1 ? result : new Promise(resolve => { finish = resolve; });
  } });
  await primary.start(); primary.setFile('makeup', new File(['a'], 'old.png')); primary.select('makeup', 'red');
  await primary.run('makeup'); await settle();
  let observerFinish!: (value: GeneratedResult) => void;
  const observer = new GenerationStore('alice', { ...deps, resume: async () => new Promise(resolve => { observerFinish = resolve; }) });
  await observer.start(); assert.equal(observer.getSnapshot().drafts.makeup.file?.name, 'old.png');
  primary.setFile('makeup', new File(['b'], 'new.png')); const running = primary.run('makeup');
  await observer.sync();
  assert.notEqual(observer.getSnapshot().drafts.makeup.file?.name, 'old.png');
  assert.equal(observer.getSnapshot().drafts.makeup.result, null);
  await settle(); await observer.sync();
  assert.equal(observer.getSnapshot().drafts.makeup.file?.name, 'new.png');
  finish(result); observerFinish(result); await running; await settle();
  assert.equal(deps.saved.get(ticketKey('alice', 'makeup'))?.file?.name, 'new.png');
  primary.stop(); observer.stop();
});

test('consultation workspace survives route callbacks and restores its signed handle and portrait after refresh', async () => {
  const deps = fixture(); const first = new GenerationStore('alice', deps); await first.start();
  first.setConsultation('file', new File(['face'], 'consultation.png'), null);
  first.setConsultation('consultationId', 'signed-principal-handle', '');
  first.setConsultation('cards', [{ status: 'generating', result: null }], []);
  // A callback from the departed component updates the same workspace.
  first.setConsultation('cards', [{ status: 'completed', result }], []);
  await settle(); first.stop();
  const next = new GenerationStore('alice', deps); await next.start();
  assert.equal(next.getSnapshot().consultation.consultationId, 'signed-principal-handle');
  assert.equal((next.getSnapshot().consultation.file as File).name, 'consultation.png');
  assert.equal((next.getSnapshot().consultation.cards as { status: string }[])[0].status, 'completed');
  next.stop();
});

test('consultation handle is journaled synchronously even when image storage fails', async () => {
  const deps = fixture(); deps.assets.write = async () => { throw Error('quota'); };
  const first = new GenerationStore('alice', deps); await first.start();
  first.setConsultation('consultationId', 'signed-handle-before-image-write', '');
  first.stop();
  const restored = new GenerationStore('alice', deps); await restored.start();
  assert.equal(restored.getSnapshot().consultation.consultationId, 'signed-handle-before-image-write');
  assert.equal(restored.getSnapshot().consultation.file, undefined); restored.stop();
});

test('a consultation generating in the shared workspace prevents a competing manual POST', async () => {
  const deps = fixture(); let posts = 0;
  const store = new GenerationStore('alice', { ...deps, generate: async () => { posts++; return result; } });
  await store.start(); store.setFile('hairstyle', new File(['p'], 'p.png')); store.select('hairstyle', 'red');
  store.setConsultation('service', 'makeup', null); store.setConsultation('phase', 'generating', 'setup');
  assert.equal(store.busyFeature(), 'makeup'); await store.run('hairstyle'); assert.equal(posts, 0);
  store.setConsultation('phase', 'ready', 'setup'); await store.run('hairstyle'); assert.equal(posts, 1); store.stop();
});
