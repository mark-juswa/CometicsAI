export function parseApiBaseUrl(value: string | undefined): string {
  if (!value?.trim()) throw new Error('Set EXPO_PUBLIC_API_BASE_URL to your development application API, then restart Expo.');
  let url: URL;
  try { url = new URL(value.trim()); } catch { throw new Error('API base URL must be a complete HTTP or HTTPS origin.'); }
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('API base URL must be an HTTP or HTTPS origin with no credentials, path, query or fragment.');
  }
  return url.origin;
}
// Only this public application origin enters the bundle. No fallback address or server env imports.
export const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
