import { create } from 'zustand';
import { api, safeGenerationRetry } from '../lib/api/client';
import type { FeatureId, GenerationResult, Style } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';

export type GenerationJob = {
  id: number; feature: FeatureId; style: Style; original: LocalPhoto; userId: string;
  phase: 'preparing' | 'running' | 'completed' | 'failed' | 'uncertain';
  startedAt: number; endedAt?: number; result?: GenerationResult; error?: string;
};
type GenerationStore = {
  job: GenerationJob | null;
  run: (feature: FeatureId, photo: LocalPhoto, style: Style, userId: string, upload: () => Promise<FormData>) => Promise<void>;
  acknowledgeEnded: () => void;
  clear: () => void;
};
export function isUnresolved(job: GenerationJob | null) {
  return job?.phase === 'preparing' || job?.phase === 'running' || job?.phase === 'uncertain';
}

// The operation lives outside the screen, so ordinary navigation/rendering cannot
// cancel it or trigger another request. All features share the duplicate guard.
export function createGenerationStore(generate: typeof api.generate = api.generate, now = Date.now) {
  let sequence = 0;
  return create<GenerationStore>((set, get) => ({
    job: null,
    run: async (feature, photo, style, userId, upload) => {
      if (isUnresolved(get().job)) return;
      const id = ++sequence;
      set({ job: { id, feature, style, original: photo, userId, phase: 'preparing', startedAt: now() } });
      let dispatched = false;
      try {
        const body = await upload();
        dispatched = true;
        set(state => ({ job: state.job && { ...state.job, phase: 'running' } }));
        const result = await generate(feature, style.id, body);
        set(state => ({ job: state.job && { ...state.job, phase: 'completed', result, endedAt: now() } }));
      } catch (error) {
        set(state => ({ job: state.job && { ...state.job,
          phase: !dispatched || safeGenerationRetry(error) ? 'failed' : 'uncertain', endedAt: now(),
          error: error instanceof Error ? error.message : 'Generation could not be completed.' } }));
      }
    },
    acknowledgeEnded: () => set(({ job }) => ({ job: job?.phase === 'uncertain' ? { ...job, phase: 'failed' } : job })),
    clear: () => { if (!isUnresolved(get().job)) set({ job: null }); },
  }));
}
export const useGeneration = createGenerationStore();
