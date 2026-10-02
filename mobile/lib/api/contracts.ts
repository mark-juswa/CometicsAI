export type FeatureId = 'hairstyle' | 'makeup' | 'nails';
export type Feature = { id: FeatureId; name: string; description: string };
export type Style = { id: string; name: string; description: string; status: string };
export type Health = { status: string; generator: string };
export type GenerationResult = {
  status: string; generator: string; style: Style;
  image: { data_url: string; content_type: string; width: number; height: number };
  metadata: Record<string, unknown>;
};
export const featureIds: FeatureId[] = ['hairstyle', 'makeup', 'nails'];
export function isFeatureId(value: unknown): value is FeatureId {
  return typeof value === 'string' && featureIds.includes(value as FeatureId);
}
export function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
export function isStyle(value: unknown): value is Style {
  return record(value) && ['id', 'name', 'description', 'status'].every(key => typeof value[key] === 'string');
}
export function isFeature(value: unknown): value is Feature {
  return record(value) && isFeatureId(value.id) && typeof value.name === 'string' && typeof value.description === 'string';
}
export function isHealth(value: unknown): value is Health {
  return record(value) && value.status === 'ok' && typeof value.generator === 'string';
}
