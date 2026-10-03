import { create } from 'zustand';
import type { FeatureId, Style } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';

export type StudioStep = 0 | 1 | 2;
type Draft = { photo: LocalPhoto | null; styleId: string | null; previewStyle: Style | null; step: StudioStep };
const empty = (): Draft => ({ photo: null, styleId: null, previewStyle: null, step: 0 });
type StudioStore = {
  drafts: Record<FeatureId, Draft>;
  setPhoto: (feature: FeatureId, photo: LocalPhoto | null) => void;
  selectStyle: (feature: FeatureId, styleId: string | null) => void;
  showPreview: (feature: FeatureId, style: Style) => void;
  reset: (feature: FeatureId) => void;
  goToStep: (feature: FeatureId, step: StudioStep) => void;
  tryAnother: (feature: FeatureId) => void;
};
// Temporary references only, no persistence, uploads, analytics or base64 copies.
export const useStudio = create<StudioStore>((set) => ({
  drafts: { hairstyle: empty(), makeup: empty(), nails: empty() },
  setPhoto: (feature, photo) => set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], photo, previewStyle: null, step: photo ? state.drafts[feature].step : 0 } } })),
  selectStyle: (feature, styleId) => set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], styleId, previewStyle: null } } })),
  showPreview: (feature, style) => set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], previewStyle: style } } })),
  reset: feature => set(state => ({ drafts: { ...state.drafts, [feature]: empty() } })),
  goToStep: (feature, step) => set(state => {
    const draft = state.drafts[feature];
    if ((step > 0 && !draft.photo) || (step === 2 && !draft.styleId)) return state;
    return { drafts: { ...state.drafts, [feature]: { ...draft, step } } };
  }),
  tryAnother: feature => set(state => {
    const draft = state.drafts[feature];
    return { drafts: { ...state.drafts, [feature]: { ...draft, previewStyle: null, step: draft.photo ? 1 : 0 } } };
  }),
}));
