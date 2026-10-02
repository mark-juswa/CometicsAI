import { create } from 'zustand';
import type { FeatureId, Style } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';

type Draft = { photo: LocalPhoto | null; styleId: string | null; previewStyle: Style | null };
const empty = (): Draft => ({ photo: null, styleId: null, previewStyle: null });
type StudioStore = {
  drafts: Record<FeatureId, Draft>;
  setPhoto: (feature: FeatureId, photo: LocalPhoto | null) => void;
  selectStyle: (feature: FeatureId, styleId: string | null) => void;
  showPreview: (feature: FeatureId, style: Style) => void;
  reset: (feature: FeatureId) => void;
};
// Temporary references only, no persistence, uploads, analytics or base64 copies.
export const useStudio = create<StudioStore>((set) => ({
  drafts: { hairstyle: empty(), makeup: empty(), nails: empty() },
  setPhoto: (feature, photo) => set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], photo, previewStyle: null } } })),
  selectStyle: (feature, styleId) => set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], styleId, previewStyle: null } } })),
  showPreview: (feature, style) => set(state => ({ drafts: { ...state.drafts, [feature]: { ...state.drafts[feature], previewStyle: style } } })),
  reset: feature => set(state => ({ drafts: { ...state.drafts, [feature]: empty() } })),
}));
