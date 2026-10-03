import { create } from 'zustand';
import type { FeatureId } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';
import { useAiOperation } from './ai-operation';
import { isUnresolved, useGeneration } from './generation';

export type StudioStep = 0 | 1 | 2;
type Draft = { photo: LocalPhoto | null; styleId: string | null; step: StudioStep };
const empty = (): Draft => ({ photo: null, styleId: null, step: 0 });
const locked = () => Boolean(useAiOperation.getState().owner) || isUnresolved(useGeneration.getState().job);
type StudioStore = {
  drafts: Record<FeatureId, Draft>;
  setPhoto: (feature: FeatureId, photo: LocalPhoto | null) => void;
  selectStyle: (feature: FeatureId, styleId: string | null) => void;
  reset: (feature: FeatureId) => void;
  goToStep: (feature: FeatureId, step: StudioStep) => void;
  tryAnother: (feature: FeatureId) => void;
};
// Temporary draft references only. Real result snapshots live in generation.ts.
export const useStudio = create<StudioStore>((set) => ({
  drafts: { hairstyle: empty(), makeup: empty(), nails: empty() },
  setPhoto: (feature, photo) => { if (!locked()) set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], photo, step: photo ? state.drafts[feature].step : 0 } } })); },
  selectStyle: (feature, styleId) => { if (!locked()) set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], styleId } } })); },
  reset: feature => { if (!locked()) set(state => ({ drafts: { ...state.drafts, [feature]: empty() } })); },
  goToStep: (feature, step) => set(state => {
    if (locked()) return state;
    const draft = state.drafts[feature];
    if ((step > 0 && !draft.photo) || (step === 2 && !draft.styleId)) return state;
    return { drafts: { ...state.drafts, [feature]: { ...draft, step } } };
  }),
  tryAnother: feature => set(state => {
    if (locked()) return state;
    const draft = state.drafts[feature];
    return { drafts: { ...state.drafts, [feature]: { ...draft, step: draft.photo ? 1 : 0 } } };
  }),
}));
