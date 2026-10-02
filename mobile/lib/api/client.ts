import { apiBaseUrl, parseApiBaseUrl } from '../config/environment';
import { type FeatureId, type Feature, type Style, type Health, isFeature, isStyle, isHealth, record } from './contracts';

export class ApiError extends Error {
  constructor(message: string, public readonly code: 'configuration' | 'network' | 'timeout' | 'http' | 'invalid_response', public readonly status?: number) {
    super(message); this.name = 'ApiError';
  }
}

// Read-only MOBILE-01 client. Generation is deliberately absent so previews cannot spend GPU work.
export function createApiClient(base: string | undefined, fetcher: typeof fetch = fetch, timeoutMs = 12_000) {
  async function get<T>(path: string, validate: (body: unknown) => body is T, signal?: AbortSignal): Promise<T> {
    let origin: string;
    try { origin = parseApiBaseUrl(base); } catch (error) {
      throw new ApiError(error instanceof Error ? error.message : 'API is not configured.', 'configuration');
    }
    const controller = new AbortController();
    const abort = () => controller.abort();
    signal?.addEventListener('abort', abort, { once: true });
    if (signal?.aborted) controller.abort();
    const deadline = setTimeout(abort, timeoutMs);
    try {
      const response = await fetcher(origin + path, { method: 'GET', headers: { Accept: 'application/json' }, signal: controller.signal });
      if (!response.ok) {
        let message = 'The application API could not complete this request.';
        try {
          const body: unknown = await response.json();
          if (record(body)) {
            if (typeof body.detail === 'string') message = body.detail;
            else if (typeof body.error === 'string') message = body.error;
            else if (Array.isArray(body.detail)) {
              const messages = body.detail.filter(record).map(row => row.msg).filter((msg): msg is string => typeof msg === 'string');
              if (messages.length) message = messages.join(' ');
            }
          }
        } catch { /* Do not display proxy HTML. */ }
        throw new ApiError(message, 'http', response.status);
      }
      let body: unknown;
      try { body = await response.json(); } catch { throw new ApiError('The API returned an unreadable response.', 'invalid_response', response.status); }
      if (!validate(body)) throw new ApiError('The API returned an incomplete response.', 'invalid_response', response.status);
      return body;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (controller.signal.aborted) throw new ApiError('Connection check timed out or was cancelled. Check the API address and try again.', 'timeout');
      throw new ApiError('Cannot reach the application API. Check your connection and the configured API address.', 'network');
    } finally {
      clearTimeout(deadline); signal?.removeEventListener('abort', abort);
    }
  }
  return {
    health: (signal?: AbortSignal) => get<Health>('/health', isHealth, signal),
    features: (signal?: AbortSignal) => get<Feature[]>('/features', (body): body is Feature[] => Array.isArray(body) && body.every(isFeature), signal),
    styles: (feature: FeatureId, signal?: AbortSignal) => get<Style[]>(`/features/${feature}/styles`, (body): body is Style[] => Array.isArray(body) && body.every(isStyle), signal),
  };
}
export const api = createApiClient(apiBaseUrl);
