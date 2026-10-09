import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveGenerationJob, AiClientError } from '../lib/ai/browser-client';
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
