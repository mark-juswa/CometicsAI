import type { FeatureId, GeneratedResult } from './browser-client';
import { clearCustomPhotos } from './studio-photo-handoff';

export const DRAFT_TTL = 30 * 60 * 1000;
export const FEATURES: FeatureId[] = ['hairstyle', 'makeup', 'nails'];
export const STORAGE_PREFIX = 'beautycore:generation:v1:';
export type Ticket = { owner: string; feature: FeatureId; styleId: string; jobId?: string;
  phase: 'submitting' | 'generating' | 'unknown' | 'completed' | 'failed'; expires: number; error: string };
export type Assets = { file: File | null; result: GeneratedResult | null; expires: number; jobId?: string; consultation?: Record<string, unknown> };
export const ticketKey = (owner: string, feature: FeatureId) => STORAGE_PREFIX + owner + ':' + feature;

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') { reject(new Error('Browser draft storage is unavailable.')); return; }
    const request = indexedDB.open('beautycore-generation-v1', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('drafts');
    let expired = false;
    const timer = setTimeout(() => { expired = true; reject(new Error('Browser draft storage timed out.')); }, 3000);
    request.onsuccess = () => { clearTimeout(timer); if (expired) request.result.close(); else resolve(request.result); };
    request.onerror = () => { clearTimeout(timer); reject(request.error); };
    request.onblocked = () => { clearTimeout(timer); expired = true; reject(new Error('Browser draft storage is blocked.')); };
  });
}
async function transaction<T>(mode: IDBTransactionMode, operation: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await database();
  try {
    return await new Promise<T>((resolve, reject) => {
      const tx = db.transaction('drafts', mode);
      const request = operation(tx.objectStore('drafts'));
      tx.oncomplete = () => resolve(request.result);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally { db.close(); }
}
export const browserDrafts = {
  read: (key: string) => transaction<Assets | undefined>('readonly', store => store.get(key)),
  write: async (key: string, value: Assets) => { await transaction('readwrite', store => store.put(value, key)); },
  remove: async (key: string) => { await transaction('readwrite', store => store.delete(key)); },
};
export type DraftStorage = typeof browserDrafts;

export function readTicket(storage: Storage, owner: string, feature: FeatureId): Ticket | null {
  try {
    const value = JSON.parse(storage.getItem(ticketKey(owner, feature)) || 'null');
    if (!value || value.owner !== owner || value.feature !== feature || typeof value.styleId !== 'string' ||
        !Number.isFinite(value.expires) || value.expires <= Date.now() || value.expires > Date.now() + DRAFT_TTL + 1000 ||
        !['submitting', 'generating', 'unknown', 'completed', 'failed'].includes(value.phase) ||
        value.jobId !== undefined && !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.jobId)) return null;
    return value as Ticket;
  } catch { return null; }
}

/** Called on logout/account change, never on ordinary route departure. */
export function clearGenerationDrafts(owner: string) {
  clearCustomPhotos();
  if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('beautycore-generation-clear', { detail: owner }));
  for (const feature of FEATURES) {
    const key = ticketKey(owner, feature);
    try { localStorage.removeItem(key); } catch { /* Storage can be disabled. */ }
    void browserDrafts.remove(key).catch(() => {});
  }
  void browserDrafts.remove(STORAGE_PREFIX + owner + ':consultation').catch(() => {});
  try { localStorage.removeItem(STORAGE_PREFIX + owner + ':consultation'); } catch { /* Optional recovery. */ }
  try { sessionStorage.removeItem(STORAGE_PREFIX + owner + ':consultation'); } catch { /* Optional recovery. */ }
  try { localStorage.setItem(STORAGE_PREFIX + 'auth', String(Date.now())); } catch { /* Other tabs also refresh on focus. */ }
}
