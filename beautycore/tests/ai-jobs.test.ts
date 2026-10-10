import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveGenerationJob, AiClientError, generateCustom } from '../lib/ai/browser-client';
const ID = '4d321734-0990-4511-a119-0a45796a267b';

test('pending job polls only reads and returns one finished image response', async () => {
  const paths: string[] = [];
  const result = { image: { data_url: 'data:image/png;base64,AA==' } };
  const value = await resolveGenerationJob({ job_id: ID, status: 'generating' }, async path => {
    paths.push(path);
    return path.endsWith('/result') ? result : { job_id: ID, status: paths.length === 1 ? 'generating' : 'completed' };
  }, 0);
  assert.equal(value, result);
  assert.deepEqual(paths, ['jobs/' + ID, 'jobs/' + ID, 'jobs/' + ID + '/result']);
});

test('failed job retrieves recorded failure; lost status never retries generation', async () => {
  let reads = 0;
  await assert.rejects(resolveGenerationJob({ job_id: ID, status: 'failed' }, async path => {
    reads++; assert.equal(path, 'jobs/' + ID + '/result'); throw new AiClientError('Failed', 502);
  }, 0));
  assert.equal(reads, 1);
  reads = 0;
  await assert.rejects(resolveGenerationJob({ job_id: ID, status: 'generating' }, async () => {
    reads++; throw new AiClientError('Disconnected', 502, true);
  }, 0));
  assert.equal(reads, 1);
});

test('arbitrary paths and mismatched tickets cannot select a result', async () => {
  await assert.rejects(resolveGenerationJob({ job_id: '../status', status: 'generating' }, async () => null, 0));
  await assert.rejects(resolveGenerationJob({ job_id: ID, status: 'generating' }, async () => ({ job_id: 'different', status: 'completed' }), 0));
});


test('known pre-admission busy response never polls or retries; unclassified 429 remains uncertain', async () => {
  const original = globalThis.fetch;
  const photo = new File([new Uint8Array([1])], 'hand.png', { type: 'image/png' });
  try {
    for (const code of ['AI_BUSY', undefined]) {
      const calls: string[] = [];
      globalThis.fetch = async (input, init) => {
        calls.push(String(input)); assert.equal(init?.method, 'POST');
        return Response.json({ error: 'Wait for the current generation.', ...(code ? { code } : {}) }, { status: 429 });
      };
      await assert.rejects(generateCustom('nails', photo, 'classic_red'), (error: unknown) => {
        assert.ok(error instanceof AiClientError);
        assert.equal(error.status, 429);
        assert.equal(error.ambiguous, code !== 'AI_BUSY');
        return true;
      });
      assert.deepEqual(calls, ['/api/ai/features/nails/generate']);
    }
  } finally { globalThis.fetch = original; }
});

test('429 reading an already accepted job remains uncertain even with a busy code', async () => {
  const original = globalThis.fetch;
  const paths: string[] = [];
  globalThis.fetch = async (input) => {
    const path = String(input); paths.push(path);
    if(path.endsWith('/generate')) return Response.json({ job_id: ID, status: 'generating' }, { status: 202 });
    return Response.json({ error: 'Busy', code: 'AI_BUSY' }, { status: 429 });
  };
  try {
    await assert.rejects(generateCustom('nails', new File([new Uint8Array([1])], 'hand.png', { type: 'image/png' }), 'classic_red'), (error: unknown) => {
      assert.ok(error instanceof AiClientError); assert.equal(error.ambiguous, true); return true;
    });
    assert.deepEqual(paths, ['/api/ai/features/nails/generate', '/api/ai/jobs/' + ID]);
  } finally { globalThis.fetch = original; }
});
