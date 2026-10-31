import expected from './style-release.json';

type ModelStyles = { hairstyle: string[]; makeup: string[]; nails: string[] };
const FEATURES = ['hairstyle', 'makeup', 'nails'] as const;
type Release = {
  schema: string; release_id: string; manifest_sha256: string; model_profile: string;
  baseline_model_catalogs: ModelStyles[]; renderer_styles: string[];
};

function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}
function exactIds(value: unknown, ids: readonly string[]): boolean {
  if (!Array.isArray(value) || value.length !== ids.length ||
      !value.every((v) => typeof v === 'string') || new Set(value).size !== value.length) return false;
  const sorted = [...value].sort();
  return [...ids].sort().every((id, index) => sorted[index] === id);
}
function modelCatalog(value: unknown, release: Release): value is ModelStyles {
  return object(value) && Object.keys(value).sort().join(',') === 'hairstyle,makeup,nails' &&
    release.baseline_model_catalogs.some((catalog) =>
      FEATURES.every((feature) => exactIds(value[feature], catalog[feature])));
}

/** Accept the exact current or explicitly preserved release. Legacy has no added styles. */
export function compatibleStyleCapabilities(readiness: Record<string, unknown>): boolean {
  if (!Object.hasOwn(readiness, 'style_capabilities')) return true;
  const value = readiness.style_capabilities;
  if (!object(value) || Object.keys(value).sort().join(',') !==
      'manifest_sha256,model_profile,model_styles,release_id,renderer_styles,schema') return false;
  return [expected, ...expected.compatible_releases].some((release) =>
    value.schema === release.schema && value.release_id === release.release_id &&
    value.manifest_sha256 === release.manifest_sha256 &&
    value.model_profile === release.model_profile &&
    modelCatalog(value.model_styles, release) && exactIds(value.renderer_styles, release.renderer_styles));
}
