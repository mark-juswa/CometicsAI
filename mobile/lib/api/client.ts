import { apiBaseUrl, parseApiBaseUrl } from '../config/environment';
import { type FeatureId, type Feature, type Style, type Session, type GenerationResult, isFeature, isStyle, isSession, isGenerationResult, record } from './contracts';
import { type Preferences, type Catalog, type CreatedConsultation, type ConsultationState, type ConsultationTurn, type GenerationDetail,
  type RecommendationSet, isConsultationState, isConsultationTurn, isGenerationDetail, isRecommendationSet, consultationView } from './consultation-contracts';

export class ApiError extends Error {
  constructor(message: string, public readonly code: 'configuration' | 'network' | 'timeout' | 'http' | 'invalid_response', public readonly status?: number) {
    super(message); this.name = 'ApiError';
  }
}
// Only pre-dispatch/auth/validation HTTP failures can safely unlock manual retry.
export function safeGenerationRetry(error: unknown) {
  return error instanceof ApiError && (error.code === 'configuration' || error.code === 'http' &&
    [400, 401, 403, 404, 413, 415, 422, 429].includes(error.status ?? 0));
}

export function createApiClient(base: string | undefined, fetcher: typeof fetch = fetch, timeoutMs = 12_000) {
  async function request<T>(path: string, validate: (body: unknown) => body is T, options: {
    method?: 'GET' | 'POST' | 'PUT' | 'PATCH'; body?: BodyInit; json?: boolean; signal?: AbortSignal; generation?: boolean; handle?: string; longRunning?: boolean;
  } = {}): Promise<T> {
    let origin: string;
    try { origin = parseApiBaseUrl(base); } catch (error) {
      throw new ApiError(error instanceof Error ? error.message : 'API is not configured.', 'configuration');
    }
    const controller = new AbortController();
    const abort = () => controller.abort();
    options.signal?.addEventListener('abort', abort, { once: true });
    if (options.signal?.aborted) controller.abort();
    // Match existing web generation semantics: do not cut off long Nails/remote work.
    const deadline = options.generation || options.longRunning ? null : setTimeout(abort, timeoutMs);
    try {
      const headers: Record<string, string> = { Accept: 'application/json' };
      if (options.method && options.method !== 'GET') {
        // NextURL canonicalizes loopback hosts to localhost before the existing
        // adapter compares Origin. Keep transport/cookies on the configured host.
        const applicationOrigin = new URL(origin);
        if (/^(?:127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}|\[::1\]|localhost)$/.test(applicationOrigin.hostname)) {
          applicationOrigin.hostname = 'localhost';
        }
        headers.Origin = applicationOrigin.origin;
      }
      if (options.json) headers['Content-Type'] = 'application/json';
      if (options.handle) headers['x-ai-consultation-handle'] = options.handle;
      const response = await fetcher(origin + path, { method: options.method ?? 'GET', headers,
        body: options.body, credentials: 'include', redirect: 'error', signal: controller.signal });
      if (!response.ok) {
        let message = 'The application API could not complete this request.';
        try {
          const body: unknown = await response.json();
          if (record(body)) {
            if (typeof body.error === 'string') message = body.error;
            else if (typeof body.detail === 'string') message = body.detail;
            else if (Array.isArray(body.detail)) {
              const messages = body.detail.filter(record).map(row => row.msg).filter((msg): msg is string => typeof msg === 'string');
              if (messages.length) message = messages.join(' ');
            }
          }
        } catch { /* Never display HTML or raw proxy responses. */ }
        throw new ApiError(message, 'http', response.status);
      }
      let body: unknown;
      try { body = await response.json(); } catch { throw new ApiError('The API returned an unreadable response.', 'invalid_response', response.status); }
      if (!validate(body)) throw new ApiError(options.generation ? 'The service did not return a valid real result. No automatic retry was made.' : 'The API returned an incomplete response.', 'invalid_response', response.status);
      return body;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (controller.signal.aborted) throw new ApiError('The application request timed out or was cancelled.', 'timeout');
      throw new ApiError('Cannot reach the application API. Check your connection and try again.', 'network');
    } finally {
      if (deadline) clearTimeout(deadline); options.signal?.removeEventListener('abort', abort);
    }
  }
  return {
    login: (email: string, password: string) => request<Session>('/api/auth/login', isSession, { method: 'POST', json: true, body: JSON.stringify({ email, password }) }),
    session: (signal?: AbortSignal) => request<Session>('/api/auth/session', isSession, { signal }),
    logout: () => request<{ success: true }>('/api/auth/logout', (body): body is { success: true } => record(body) && body.success === true, { method: 'POST' }),
    features: (signal?: AbortSignal) => request<Feature[]>('/api/ai/features', (body): body is Feature[] => Array.isArray(body) && body.every(isFeature), { signal }),
    styles: (feature: FeatureId, signal?: AbortSignal) => request<Style[]>(`/api/ai/features/${feature}/styles`, (body): body is Style[] => Array.isArray(body) && body.every(isStyle), { signal }),
    generate: async (feature: FeatureId, styleId: string, image: FormData) => {
      const result = await request<GenerationResult>(`/api/ai/features/${feature}/generate`, isGenerationResult, { method: 'POST', body: image, generation: true });
      if (result.style.id !== styleId) throw new ApiError('The service returned a different style. No automatic retry was made.', 'invalid_response');
      return result;
    },
    consultationMode: async () => {
      const value = await request<{ provider: 'gemini' | 'deterministic' }>('/api/ai/mode', (v): v is { provider: 'gemini' | 'deterministic' } => record(v) && ['gemini', 'deterministic'].includes(String(v.provider)));
      return value.provider;
    },
    consultationCatalog: async (): Promise<Catalog> => {
      const value = await request<{ styles: Record<FeatureId, { style_id: string; name: string; description: string; status: string }[]> }>('/api/ai/catalog', (v): v is { styles: Record<FeatureId, { style_id: string; name: string; description: string; status: string }[]> } =>
        record(v) && record(v.styles) && ['hairstyle', 'makeup', 'nails'].every(f => Array.isArray(v.styles && (v.styles as Record<string, unknown>)[f]) &&
          ((v.styles as Record<string, unknown[]>)[f]).every(s => record(s) && ['style_id', 'name', 'description', 'status'].every(k => typeof s[k] === 'string'))));
      return Object.fromEntries(Object.entries(value.styles).map(([f, rows]) => [f, rows.map(s => ({ id: s.style_id, name: s.name, description: s.description, status: s.status }))])) as Catalog;
    },
    createConsultation: async (primary_service: FeatureId) => {
      const value = await request<CreatedConsultation>('/api/ai/consultations', (v): v is CreatedConsultation => record(v) && typeof v.handle === 'string' && v.handle.length > 0 && isConsultationState(v),
        { method: 'POST', json: true, body: JSON.stringify({ primary_service }) });
      return { handle: value.handle, state: consultationView(value) };
    },
    consultationState: async (handle: string) => consultationView(await request<ConsultationState>('/api/ai/consultations/state', isConsultationState, { handle })),
    consultationPhoto: async (handle: string, image: FormData) => consultationView(await request<ConsultationState>('/api/ai/consultations/photo', isConsultationState, { handle, method: 'PUT', body: image })),
    consultationPreferences: async (handle: string, preferences: Preferences) => consultationView(await request<ConsultationState>('/api/ai/consultations/state', isConsultationState, { handle, method: 'PATCH', json: true, body: JSON.stringify({ preferences }) })),
    consultationTurn: async (handle: string, message?: string) => {
      const v = await request<ConsultationTurn>('/api/ai/consultations/turn', isConsultationTurn, { handle, method: 'POST', json: true, longRunning: true, body: JSON.stringify(message === undefined ? {} : { message }) });
      return { state: consultationView(v.state), status: v.status, recommendations: v.recommendations };
    },
    consultationRecommendations: (handle: string) => request<RecommendationSet>('/api/ai/consultations/recommendations', isRecommendationSet, { handle, method: 'POST' }),
    consultationGenerate: (handle: string, recommendationId: string) => request<GenerationDetail>(`/api/ai/consultations/recommendations/${encodeURIComponent(recommendationId)}/generation`, isGenerationDetail, { handle, method: 'POST', generation: true }),
    consultationGeneration: (handle: string, recommendationId: string) => request<GenerationDetail>(`/api/ai/consultations/recommendations/${encodeURIComponent(recommendationId)}/generation`, isGenerationDetail, { handle }),
    consultationSelect: async (handle: string, recommendationId: string) => consultationView(await request<ConsultationState>(`/api/ai/consultations/recommendations/${encodeURIComponent(recommendationId)}/select`, isConsultationState, { handle, method: 'POST' })),
  };
}
export const api = createApiClient(apiBaseUrl);
