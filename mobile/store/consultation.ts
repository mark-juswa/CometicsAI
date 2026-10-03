import { create } from 'zustand';
import type { FeatureId } from '../lib/api/contracts';
import type { LocalPhoto } from '../lib/image/validation';
import type { StudioStep } from './studio';
import { useConsultationSession } from './consultation-session';

export type Direction = { occasion: string; vibe: string; servicePreference: string; avoids: string; notes: string };
const emptyDirection = (): Direction => ({ occasion: '', vibe: '', servicePreference: '', avoids: '', notes: '' });
type ConsultationDraft = { step: StudioStep; feature: FeatureId | null; photo: LocalPhoto | null; direction: Direction };
const empty = (): ConsultationDraft => ({ step: 0, feature: null, photo: null, direction: emptyDirection() });
type ConsultationStore = {
  draft: ConsultationDraft;
  chooseService: (feature: FeatureId) => void;
  setPhoto: (photo: LocalPhoto | null) => void;
  setDirection: (field: keyof Direction, value: string) => void;
  goToStep: (step: StudioStep) => void;
  reset: () => void;
};
// Temporary local preparation. Server views and opaque handles live separately.
export const useConsultation = create<ConsultationStore>((set) => ({
  draft: empty(),
  chooseService: feature => { if (feature === useConsultation.getState().draft.feature || !useConsultationSession.getState().clear()) return; set(({ draft }) => {
    if (feature === draft.feature) return { draft };
    const compatible = draft.feature !== null && (draft.feature === 'nails') === (feature === 'nails');
    return { draft: { ...draft, feature, step: 0, photo: compatible ? draft.photo : null,
      direction: { ...draft.direction, servicePreference: '' } } };
  }); },
  setPhoto: photo => { if (useConsultationSession.getState().clear()) set(({ draft }) => ({ draft: { ...draft, photo, step: photo ? draft.step : 0 } })); },
  setDirection: (field, value) => { if (useConsultationSession.getState().clear()) set(({ draft }) => ({ draft: { ...draft, direction: { ...draft.direction, [field]: value } } })); },
  goToStep: step => set(({ draft }) => {
    if (step > 0 && (!draft.feature || !draft.photo)) return { draft };
    return { draft: { ...draft, step } };
  }),
  reset: () => { if (useConsultationSession.getState().clear()) set({ draft: empty() }); },
}));
