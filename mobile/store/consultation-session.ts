import { create } from 'zustand';
import { api, ApiError, safeGenerationRetry } from '../lib/api/client';
import { type Catalog, type ConsultationState, type GenerationDetail, type Preferences, recommendationsAvailable } from '../lib/api/consultation-contracts';
import type { FeatureId } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';
import { createOperationStore, useAiOperation } from './ai-operation';

type ConsultationApi = Pick<typeof api, 'consultationMode' | 'consultationCatalog' | 'createConsultation' | 'consultationPhoto' | 'consultationPreferences' |
  'consultationTurn' | 'consultationState' | 'consultationGenerate' | 'consultationGeneration' | 'consultationSelect'>;
export type ConsultationRun = { recommendationId: string; phase: 'generating' | 'unknown'; startedAt: number };
type Store = {
  handle: string | null; userId: string | null; original: LocalPhoto | null; state: ConsultationState | null; catalog: Catalog | null;
  busy: boolean; error: string; expired: boolean; needsSync: boolean; active: ConsultationRun | null;
  details: Record<string, GenerationDetail>; times: Record<string, { start: number; end?: number }>;
  begin: (feature: FeatureId, photo: LocalPhoto, preferences: Preferences, userId: string, upload: () => Promise<FormData>) => Promise<void>;
  reply: (message?: string) => Promise<boolean>; refresh: () => Promise<boolean>;
  generate: (recommendationId: string) => Promise<void>; checkGeneration: () => Promise<void>;
  select: (recommendationId: string) => Promise<boolean>; clear: () => boolean;
};
const empty = () => ({ handle: null, userId: null, original: null, state: null, catalog: null, busy: false, error: '', expired: false,
  needsSync: false, active: null, details: {}, times: {} });
function message(error: unknown) {
  if (error instanceof ApiError && error.status === 401) return 'Your BeautyCore session has ended. Sign in again to continue.';
  if (error instanceof ApiError && [403, 404].includes(error.status ?? 0)) return 'Consultation access has expired or is unavailable to this account. Start a new consultation when no generation is running.';
  return error instanceof Error ? error.message : 'The consultation could not complete this request.';
}
export function createConsultationSession(client: ConsultationApi = api, now = Date.now, operation = createOperationStore()) {
  let inFlight = false; let checking = false;
  return create<Store>((set, get) => {
    function fail(error: unknown) {
      set({ error: message(error), expired: error instanceof ApiError && [403, 404].includes(error.status ?? 0) });
    }
    function apply(state: ConsultationState) {
      const catalog = get().catalog;
      if (!catalog || !recommendationsAvailable(state, catalog)) throw new ApiError('A recommended style is unavailable in the active catalog. Refresh your consultation before continuing.', 'invalid_response');
      if (get().state && state.primary_service !== get().state?.primary_service) throw new ApiError('The consultation service changed unexpectedly.', 'invalid_response');
      set({ state });
    }
    function applyDetail(id: string, detail: GenerationDetail) {
      const recommendation = get().state?.recommendations?.recommendations.find(r => r.id === id);
      if (!recommendation || detail.generation.recommendation_id !== id ||
        detail.result && detail.result.style.id !== recommendation.primary.style_id) throw new ApiError('The result does not match this recommended look. Check status before continuing.', 'invalid_response');
      const terminal = ['completed', 'failed'].includes(detail.generation.status);
      set(s => ({ details: { ...s.details, [id]: detail },
        ...(detail.generation.status === 'completed' ? { error: '', expired: false } : {}),
        state: s.state && { ...s.state, generations: s.state.generations.map(g => g.recommendation_id === id ? detail.generation : g) },
        times: terminal && s.times[id] ? { ...s.times, [id]: { ...s.times[id], end: now() } } : s.times,
      }));
      if (terminal && !inFlight) { set({ active: null }); operation.getState().release('consultation'); }
      return terminal;
    }
    return {
      ...empty(),
      begin: async (feature, photo, preferences, userId, upload) => {
        if (get().busy || get().active) return;
        set({ ...empty(), busy: true, original: photo, userId });
        try {
          const [mode, catalog, body] = await Promise.all([client.consultationMode(), client.consultationCatalog(), upload()]);
          if (mode !== 'gemini') throw new Error('The AI consultant is not available in this server mode. Please ask the operator to restore the existing Gemini service.');
          set({ catalog });
          const created = await client.createConsultation(feature);
          set({ handle: created.handle }); apply(created.state);
          apply(await client.consultationPhoto(created.handle, body));
          apply(await client.consultationPreferences(created.handle, preferences));
        } catch (error) { fail(error); set({ needsSync: Boolean(get().handle) }); }
        finally { set({ busy: false }); }
      },
      reply: async value => {
        const s = get(); const text = value?.trim();
        if (!s.handle || s.busy || s.active || s.expired || s.needsSync || s.state?.conversation_status === 'ready_for_recommendation' ||
          value !== undefined && (!text || text.length > 500)) return false;
        set({ busy: true, error: '' });
        try { apply((await client.consultationTurn(s.handle, text)).state); return true; }
        catch (error) { fail(error); set({ needsSync: true }); return false; }
        finally { set({ busy: false }); }
      },
      refresh: async () => {
        const s = get(); if (!s.handle || s.busy || s.active) return false;
        set({ busy: true, error: '' });
        try {
          set({ catalog: await client.consultationCatalog() });
          apply(await client.consultationState(s.handle)); set({ needsSync: false, expired: false }); return true;
        } catch (error) { fail(error); return false; }
        finally { set({ busy: false }); }
      },
      generate: async id => {
        const s = get(); const recommendation = s.state?.recommendations?.recommendations.find(r => r.id === id);
        const status = s.details[id]?.generation.status ?? s.state?.generations.find(g => g.recommendation_id === id)?.status;
        if (!s.handle || !recommendation || !s.original || !s.catalog || s.busy || s.active || s.expired || s.needsSync ||
          !recommendationsAvailable(s.state!, s.catalog) || !['pending', 'failed'].includes(status ?? '') || !operation.getState().claim('consultation')) return;
        const start = now(); inFlight = true;
        set({ active: { recommendationId: id, phase: 'generating', startedAt: start }, error: '', times: { ...s.times, [id]: { start } } });
        let terminal = false;
        try { terminal = applyDetail(id, await client.consultationGenerate(s.handle, id)); }
        catch (error) {
          fail(error);
          // A lost response is followed by reads, never another generation POST.
          try {
            const detail = await client.consultationGeneration(s.handle, id);
            terminal = applyDetail(id, detail);
            if (!terminal && detail.generation.status === 'pending' && safeGenerationRetry(error)) {
              const latest = await client.consultationState(s.handle); apply(latest);
              terminal = !latest.generations.some(g => g.status === 'generating');
            }
          } catch (readError) { fail(readError); }
          if (!terminal) set({ active: { recommendationId: id, phase: 'unknown', startedAt: start } });
        } finally {
          inFlight = false;
          if (terminal) { set({ active: null }); operation.getState().release('consultation'); }
          else if (get().active) set(s => ({ active: s.active && { ...s.active, phase: 'unknown' } }));
        }
      },
      checkGeneration: async () => {
        const s = get(); if (!s.handle || !s.active || checking || inFlight) return;
        checking = true;
        try {
          const detail = await client.consultationGeneration(s.handle, s.active.recommendationId);
          applyDetail(s.active.recommendationId, detail);
          set({ error: detail.generation.status === 'pending' ? 'The request outcome is still uncertain. No new generation will be sent. Check status again or ask the operator to verify processing has ended.' : '' });
        } catch (error) { fail(error); }
        finally { checking = false; }
      },
      select: async id => {
        const s = get(); if (!s.handle || s.busy || s.active || s.expired || s.details[id]?.generation.status !== 'completed') return false;
        set({ busy: true, error: '' });
        try {
          const state = await client.consultationSelect(s.handle, id); apply(state);
          if (state.selected_recommendation_id !== id) throw new ApiError('Your selection was not confirmed. Check your consultation before continuing.', 'invalid_response');
          return true;
        } catch (error) { fail(error); return false; }
        finally { set({ busy: false }); }
      },
      clear: () => { if (get().busy || get().active) return false; set(empty()); return true; },
    };
  });
}
export const useConsultationSession = createConsultationSession(api, Date.now, useAiOperation);
