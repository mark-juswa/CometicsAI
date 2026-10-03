import { apiBaseUrl, parseApiBaseUrl } from '../config/environment';
import { type FeatureId, type Feature, type Style, type Session, type GenerationResult, isFeature, isStyle, isSession, isGenerationResult, record } from './contracts';

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
    method?: 'GET' | 'POST'; body?: BodyInit; json?: boolean; signal?: AbortSignal; generation?: boolean;
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
    const deadline = options.generation ? null : setTimeout(abort, timeoutMs);
    try {
      const headers: Record<string, string> = { Accept: 'application/json' };
      if (options.method === 'POST') {
        // NextURL canonicalizes loopback hosts to localhost before the existing
        // adapter compares Origin. Keep transport/cookies on the configured host.
        const applicationOrigin = new URL(origin);
        if (/^(?:127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}|\[::1\]|localhost)$/.test(applicationOrigin.hostname)) {
          applicationOrigin.hostname = 'localhost';
        }
        headers.Origin = applicationOrigin.origin;
      }
      if (options.json) headers['Content-Type'] = 'application/json';
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
  };
}
export const api = createApiClient(apiBaseUrl);
