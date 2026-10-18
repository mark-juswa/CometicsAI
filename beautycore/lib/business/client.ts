import type { LookDetails } from './look-information';
import type { FeatureId, GeneratedResult } from '../ai/browser-client';
export type SavedLook = {
  id: string;
  styleType: 'hair' | 'nail' | 'makeup';
  styleId: string;
  styleName: string;
  lookDetails?: LookDetails | null;
  imageUrl: string;
  savedAt: string;
  createdAt: string;
};
export async function businessRequest(path: string, init: RequestInit = {}) {
  const response = await fetch(path, { ...init, cache: 'no-store' });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.error === 'string' ? data.error : 'The request could not be completed.',
    );
  return data;
}
export async function saveLook(
  feature: FeatureId,
  result: GeneratedResult,
  sourceKind: 'manual' | 'consultation',
): Promise<SavedLook> {
  const data = await businessRequest('/api/saved-looks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      feature,
      styleId: result.style.id,
      image: result.image.data_url,
      status: result.status,
      sourceKind,
    }),
  });
  return data.look;
}
export function savedGroup(type: string) {
  return type === 'hair' ? 'hair-design' : type === 'nail' ? 'nail-studio' : 'makeup';
}
