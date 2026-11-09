import type { FeatureId } from './browser-client';

// One navigation in this process. The handoff itself never serializes a photo.
let pending: { feature: FeatureId; file: File } | null = null;

export function rememberCustomPhoto(feature: FeatureId, file: File): void {
  pending = { feature, file };
}

export function takeCustomPhoto(feature: FeatureId): File | null {
  if (pending?.feature !== feature) return null;
  const file = pending.file;
  pending = null;
  return file;
}

export function clearCustomPhotos(): void { pending = null; }
