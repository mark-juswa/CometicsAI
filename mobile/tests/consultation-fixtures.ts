import type { Catalog, ConsultationState, GenerationDetail, RecommendationSet } from '../lib/api/consultation-contracts';
export const photo = { uri: 'file:///local/portrait.png', name: 'portrait.png', mimeType: 'image/png' as const, width: 512, height: 512, size: 1024 };
export const catalog: Catalog = { hairstyle: ['crew_cut', 'bob_cut', 'bun'].map(id => ({ id, name: id, description: 'Test fixture only', status: 'available' })),
  makeup: [{ id: 'soft_glam', name: 'Soft Glam', description: 'Test fixture', status: 'available' }], nails: [{ id: 'classic_red', name: 'Classic Red', description: 'Test fixture', status: 'available' }] };
export const recommendations: RecommendationSet = { recommendations: catalog.hairstyle.map((s, index) => ({ id: `look_${index + 1}`, primary: {
  feature: 'hairstyle', style_id: s.id, style_name: s.name, nail_path: null,
  service: { name: 'Hair styling', currency: 'PHP', estimate_kind: 'demo_only', estimated_price: 500, estimated_duration_minutes: 40 } },
  reason: 'Validated test fixture reason', complements: [] })) };
export function state(ready = false): ConsultationState {
  return { primary_service: 'hairstyle', stage: ready ? 'recommended' : 'collecting', conversation_status: ready ? 'ready_for_recommendation' : 'more_information',
    photo: { content_type: 'image/png', width: 512, height: 512 }, messages: [{ role: 'assistant', content: 'What length do you prefer?' }],
    recommendations: ready ? recommendations : null, generations: ready ? recommendations.recommendations.map(r => ({ recommendation_id: r.id, status: 'pending', error: null, attempts: 0, result_available: false })) : [], selected_recommendation_id: null };
}
export function detail(id = 'look_1', status: 'pending' | 'generating' | 'completed' | 'failed' = 'completed'): GenerationDetail {
  return { generation: { recommendation_id: id, status, error: status === 'failed' ? 'AI service unavailable.' : null, attempts: status === 'pending' ? 0 : 1, result_available: status === 'completed' },
    result: status === 'completed' ? { status: 'completed', generator: 'remote_flux', style: catalog.hairstyle[Number(id.slice(-1)) - 1],
      image: { data_url: 'data:image/png;base64,AA==', content_type: 'image/png', width: 512, height: 512 }, metadata: { fixture: true } } : null };
}
