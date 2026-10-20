/** Preserve the original Consultation page's contract using signed principal-bound handles. */
import { createBrowserClient, type ConsultationView, type FeatureId, type GenerationDetail,
 type Preferences, type Recommendation } from './browser-client';

export type { GenerationDetail, Preferences, Recommendation };
type ConsultationState = ConsultationView & { id: string };
type RecommendationSet = { recommendations: Recommendation[] };

export function createStudioConsultationApi(base: '/api/ai/' | '/api/ai-trial/' = '/api/ai/') {
  const { createConsultation: create, generateRecommendation: generate, getGenerationStatus, getMode,
   getRecommendations, selectRecommendation: select, sendTurn, updatePreferences, uploadPhoto, getConsultationState } = createBrowserClient(base);
  function withHandle(handle: string, state: ConsultationView): ConsultationState {
    // id is the signed, principal-bound handle, never FastAPI's consultation UUID.
    return { ...state, id: handle };
  }

  async function getConsultationMode(): Promise<{ provider: 'gemini' | 'deterministic' }> {
    return { provider: await getMode() };
  }

  async function createConsultation(feature: FeatureId): Promise<ConsultationState> {
    const created = await create(feature);
    return withHandle(created.handle, created.state);
  }

  async function uploadConsultationPhoto(handle: string, photo: File): Promise<ConsultationState> {
    return withHandle(handle, await uploadPhoto(handle, photo));
  }

  async function updateConsultation(handle: string, preferences: Preferences): Promise<ConsultationState> {
    return withHandle(handle, await updatePreferences(handle, preferences));
  }

  async function sendConsultationTurn(handle: string, message?: string): Promise<{
    state: ConsultationState;
    status: 'more_information' | 'ready_for_recommendation';
    recommendations: RecommendationSet | null;
  }> {
    const turn = await sendTurn(handle, message);
    return {
      state: withHandle(handle, turn.state),
      status: turn.status,
      recommendations: turn.recommendations ? { recommendations: turn.recommendations } : null,
    };
  }

  async function recommendConsultation(handle: string): Promise<RecommendationSet> {
    return { recommendations: await getRecommendations(handle) };
  }

  function generateRecommendation(handle: string, recommendationId: string): Promise<GenerationDetail> {
    return generate(handle, recommendationId);
  }

  function getGenerationDetail(handle: string, recommendationId: string): Promise<GenerationDetail> {
    return getGenerationStatus(handle, recommendationId);
  }

  async function selectRecommendation(handle: string, recommendationId: string): Promise<ConsultationState> {
    return withHandle(handle, await select(handle, recommendationId));
  }

  async function getConsultation(handle: string): Promise<ConsultationState> { return withHandle(handle, await getConsultationState(handle)); }
  return { getConsultationMode, createConsultation, uploadConsultationPhoto, updateConsultation, sendConsultationTurn, recommendConsultation, generateRecommendation, getGenerationDetail, selectRecommendation, getConsultation };
}
export const { getConsultationMode, createConsultation, uploadConsultationPhoto, updateConsultation, sendConsultationTurn, recommendConsultation, generateRecommendation, getGenerationDetail, selectRecommendation, getConsultation } = createStudioConsultationApi();
