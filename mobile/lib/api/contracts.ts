export type FeatureId = 'hairstyle' | 'makeup' | 'nails';
export type Feature = { id: FeatureId; name: string; description: string };
export type Style = { id: string; name: string; description: string; status: string };
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
export type User = { id: string; name: string; email: string; role: string; avatar: string | null };
export type Session = { user: User | null };
export function isSession(value: unknown): value is Session {
  if (!record(value)) return false;
  const user = value.user;
  return user === null || record(user) && ['id', 'name', 'email', 'role'].every(key => typeof user[key] === 'string') &&
    (user.avatar === null || typeof user.avatar === 'string');
}
export function isGenerationResult(value: unknown): value is GenerationResult {
  if (!record(value) || value.status !== 'completed' || typeof value.generator !== 'string' || /mock|placeholder/i.test(value.generator) ||
    !isStyle(value.style) || !record(value.image) || !record(value.metadata)) return false;
  const image = value.image;
  return ['image/png', 'image/jpeg'].includes(String(image.content_type)) &&
    Number.isInteger(image.width) && Number(image.width) > 0 && Number(image.width) <= 4096 &&
    Number.isInteger(image.height) && Number(image.height) > 0 && Number(image.height) <= 4096 &&
    typeof image.data_url === 'string' && image.data_url.startsWith(`data:${image.content_type};base64,`) &&
    /^[A-Za-z0-9+/]+={0,2}$/.test(image.data_url.split(',')[1] ?? '');
}
