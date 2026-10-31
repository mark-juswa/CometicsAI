import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import expected from '../lib/ai/style-release.json';
import { compatibleStyleCapabilities } from '../lib/ai/style-release';
import { verifyFacade } from '../lib/ai/runtime-registry';

function capabilities() {
  return {
    schema: expected.schema, release_id: expected.release_id,
    manifest_sha256: expected.manifest_sha256,
    model_styles: structuredClone(expected.baseline_model_catalogs[0]),
    renderer_styles: [...expected.renderer_styles], model_profile: expected.model_profile,
  };
}
function readiness() {
  return { ready: true, reason: 'ready', foundation_load_count: 1,
    diagnostics_version: 'deployment-01', nails_inference_steps: 8,
    supported_features: ['hairstyle', 'makeup', 'nails'] };
}
function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
      .map(([key, item]) => [key, canonical(item)]));
  return value;
}

test('generated Render evidence matches the source manifest canonical digest', () => {
  const source = JSON.parse(readFileSync(new URL('../../backend/app/style_release.json', import.meta.url), 'utf8'));
  const ascii = JSON.stringify(canonical(source)).replace(/[\u007f-\uffff]/g,
    (character) => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0'));
  assert.equal(createHash('sha256').update(ascii).digest('hex'), expected.manifest_sha256);
});

test('known baseline facades remain compatible without claiming expansion support', () => {
  assert.equal(compatibleStyleCapabilities(readiness()), true);
});
test('both original Hair registries have explicit compatible release catalogs', () => {
  for (const catalog of expected.baseline_model_catalogs) {
    assert.equal(compatibleStyleCapabilities({
      style_capabilities: { ...capabilities(), model_styles: catalog },
    }), true);
  }
});

for (const field of ['schema', 'release_id', 'manifest_sha256', 'model_profile']) {
  test('reject wrong release identity: ' + field, () => {
    const value = { ...capabilities(), [field]: 'wrong' };
    assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), false);
  });
}
for (const invalid of [null, [], {}, { ...capabilities(), extra: 'unexpected' }]) {
  test('malformed or unknown capability payload cannot register: ' + JSON.stringify(invalid), () => {
    assert.equal(compatibleStyleCapabilities({ style_capabilities: invalid }), false);
  });
}
test('pending and duplicate IDs cannot be advertised as installed supported styles', () => {
  const value = capabilities();
  value.renderer_styles.push('exp_milky_pearl_chrome');
  assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), false);
  value.renderer_styles = [...expected.renderer_styles, expected.renderer_styles[0]];
  assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), false);
  value.renderer_styles = [...expected.renderer_styles];
  value.model_styles.hairstyle.push('exp_unknown_hair');
  assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), false);
});
test('unknown feature and incomplete baseline catalogs fail closed', () => {
  const value = capabilities();
  assert.equal(compatibleStyleCapabilities({ style_capabilities: {
    ...value, model_styles: { ...value.model_styles, unknown: [] },
  } }), false);
  value.model_styles.makeup.pop();
  assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), false);
});

test('protected facade verification enforces compatible capabilities and body bounds', async () => {
  const verify = async (report: unknown) => {
    const upstream: typeof fetch = async (url, init) => {
      assert.equal(new Headers(init?.headers).get('x-ai-backend-key'), 'test-key');
      return String(url).endsWith('/health')
        ? Response.json({ status: 'ok', service: 'render-kaggle-demo-v1' })
        : Response.json(report);
    };
    return verifyFacade('https://fixture.trycloudflare.com', 'test-key', upstream);
  };
  assert.equal(await verify({ ...readiness(), style_capabilities: capabilities() }), true);
  assert.equal(await verify({ ...readiness(), style_capabilities: null }), false);
  assert.equal(await verify({ ...readiness(), style_capabilities: {
    ...capabilities(), manifest_sha256: '0'.repeat(64),
  } }), false);
  assert.equal(await verify({ ...readiness(), padding: 'x'.repeat(8192) }), false);
});

test('preserved releases remain compatible without claiming new five-Hair support', () => {
  assert.equal(expected.compatible_releases.length, 2);
  for (const release of expected.compatible_releases) {
    const value = {
      schema: release.schema, release_id: release.release_id, manifest_sha256: release.manifest_sha256,
      model_profile: release.model_profile, renderer_styles: [...release.renderer_styles],
      model_styles: structuredClone(release.baseline_model_catalogs[0]),
    };
    assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), true);
    value.model_styles.hairstyle.push('exp_wolf_cut');
    assert.equal(compatibleStyleCapabilities({ style_capabilities: value }), false);
  }
});
