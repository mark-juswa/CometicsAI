import { type FeatureId, type GenerationResult, type Style, isFeatureId, isGenerationResult, record } from './contracts';

export type Preferences = {
  occasion?: string; vibe?: string; avoids?: string[]; notes?: string;
  hair_maintenance?: 'low' | 'medium' | 'high'; makeup_intensity?: 'natural' | 'soft' | 'bold';
  nail_finish?: 'glossy' | 'matte' | 'ombre' | 'french';
};
export type Choice = { feature: FeatureId; style_id: string; style_name: string; nail_path: 'model' | 'renderer' | null;
  service: { name: string; currency: string; estimated_price: number; estimated_duration_minutes: number; estimate_kind: 'demo_only' } };
export type Recommendation = { id: string; primary: Choice; reason: string; complements: Choice[] };
export type RecommendationSet = { recommendations: Recommendation[] };
export type GenerationStatus = { recommendation_id: string; status: 'pending' | 'generating' | 'completed' | 'failed';
  error: string | null; attempts: number; result_available: boolean };
export type GenerationDetail = { generation: GenerationStatus; result: GenerationResult | null };
export type ConsultationState = {
  primary_service: FeatureId; stage: 'collecting' | 'recommended';
  conversation_status: 'not_started' | 'more_information' | 'ready_for_recommendation';
  photo: { content_type: string; width: number; height: number } | null;
  messages: { role: 'user' | 'assistant'; content: string }[];
  recommendations: RecommendationSet | null; generations: GenerationStatus[]; selected_recommendation_id: string | null;
};
export type CreatedConsultation = ConsultationState & { handle: string };
export type ConsultationTurn = { state: ConsultationState; status: 'more_information' | 'ready_for_recommendation'; recommendations: RecommendationSet | null };
export type Catalog = Record<FeatureId, Style[]>;
const safeId = (v: unknown): v is string => typeof v === 'string' && /^[A-Za-z0-9_-]{1,100}$/.test(v);
export const availableStatuses = ['prototype', 'experimental', 'verified', 'available', 'trained_preset'];
function choice(v: unknown): v is Choice {
  if (!record(v) || !isFeatureId(v.feature) || !safeId(v.style_id) || typeof v.style_name !== 'string' || !record(v.service)) return false;
  const s = v.service;
  return typeof s.name === 'string' && typeof s.currency === 'string' && s.estimate_kind === 'demo_only' &&
    Number.isInteger(s.estimated_price) && Number(s.estimated_price) >= 0 && Number.isInteger(s.estimated_duration_minutes) && Number(s.estimated_duration_minutes) > 0 &&
    (v.nail_path === null || v.nail_path === 'model' || v.nail_path === 'renderer');
}
export function isRecommendationSet(v: unknown): v is RecommendationSet {
  if (!record(v) || !Array.isArray(v.recommendations) || v.recommendations.length !== 3) return false;
  return v.recommendations.every(r => record(r) && safeId(r.id) && choice(r.primary) && typeof r.reason === 'string' &&
    Array.isArray(r.complements) && r.complements.length <= 2 && r.complements.every(choice)) &&
    new Set(v.recommendations.map(r => r.id)).size === 3 && new Set(v.recommendations.map(r => r.primary.style_id)).size === 3;
}
export function isGenerationStatus(v: unknown): v is GenerationStatus {
  return record(v) && safeId(v.recommendation_id) && ['pending', 'generating', 'completed', 'failed'].includes(String(v.status)) &&
    (v.error === null || typeof v.error === 'string') && Number.isInteger(v.attempts) && Number(v.attempts) >= 0 && typeof v.result_available === 'boolean';
}
export function isGenerationDetail(v: unknown): v is GenerationDetail {
  return record(v) && isGenerationStatus(v.generation) && (v.result === null || isGenerationResult(v.result)) &&
    (v.generation.status === 'completed' ? v.result !== null && v.generation.result_available : v.result === null);
}
export function isConsultationState(v: unknown): v is ConsultationState {
  if (!record(v) || 'id' in v || !isFeatureId(v.primary_service) || !['collecting', 'recommended'].includes(String(v.stage)) ||
    !['not_started', 'more_information', 'ready_for_recommendation'].includes(String(v.conversation_status))) return false;
  return (v.photo === null || record(v.photo) && typeof v.photo.content_type === 'string' && Number(v.photo.width) > 0 && Number(v.photo.height) > 0) &&
    Array.isArray(v.messages) && v.messages.every(m => record(m) && ['user', 'assistant'].includes(String(m.role)) && typeof m.content === 'string') &&
    Array.isArray(v.generations) && v.generations.every(isGenerationStatus) &&
    (v.selected_recommendation_id === null || safeId(v.selected_recommendation_id)) &&
    (v.recommendations === null ? v.conversation_status !== 'ready_for_recommendation' && v.stage === 'collecting' :
      isRecommendationSet(v.recommendations) && v.stage === 'recommended' && v.conversation_status === 'ready_for_recommendation' &&
      v.recommendations.recommendations.every(r => r.primary.feature === v.primary_service));
}
export function isConsultationTurn(v: unknown): v is ConsultationTurn {
  return record(v) && isConsultationState(v.state) && v.status === v.state.conversation_status &&
    ['more_information', 'ready_for_recommendation'].includes(String(v.status)) &&
    (v.recommendations === null ? v.status === 'more_information' : isRecommendationSet(v.recommendations) && v.status === 'ready_for_recommendation');
}
// Project only public view fields; do not retain server IDs or provider metadata.
export function consultationView(v: ConsultationState): ConsultationState {
  return { primary_service: v.primary_service, stage: v.stage, conversation_status: v.conversation_status,
    photo: v.photo && { content_type: v.photo.content_type, width: v.photo.width, height: v.photo.height },
    messages: v.messages.map(({ role, content }) => ({ role, content })), recommendations: v.recommendations,
    generations: v.generations, selected_recommendation_id: v.selected_recommendation_id };
}
export function recommendationsAvailable(state: ConsultationState, catalog: Catalog) {
  return !state.recommendations || state.recommendations.recommendations.every(r => [r.primary, ...r.complements].every(c =>
    catalog[c.feature].some(s => s.id === c.style_id && availableStatuses.includes(s.status))));
}
