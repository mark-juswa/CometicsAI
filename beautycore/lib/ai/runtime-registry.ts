import { createHmac, timingSafeEqual } from 'node:crypto';
import { validBaseUrl } from './adapter-core';

export const RUNTIME_SCHEMA = 'beautycore-runtime-v1';
export const LEASE_SECONDS = 180;
export const CLOCK_SKEW_SECONDS = 90;
export type RuntimeMessage = {
  schema: typeof RUNTIME_SCHEMA; operation: 'register' | 'renew';
  session_id: string; endpoint: string; started_at: number; issued_at: number;
};
export type RuntimeLease = {
  sessionId: string; endpoint: string; startedAt: number; lastIssuedAt: number; expiresAt: number;
};
export interface RuntimeStore {
  get(): Promise<RuntimeLease | null>;
  claim(message: RuntimeMessage): Promise<RuntimeLease | null>;
  renew(message: RuntimeMessage): Promise<RuntimeLease | null>;
}
const PRIVATE = { 'Cache-Control': 'private, no-store' };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

export function canonicalRuntime(message: RuntimeMessage): string {
  return JSON.stringify({ endpoint: message.endpoint, issued_at: message.issued_at,
    operation: message.operation, schema: message.schema, session_id: message.session_id,
    started_at: message.started_at });
}
export function signRuntime(message: RuntimeMessage, key: string): string {
  const derived = createHmac('sha256', key).update('beautycore-runtime-key-v1').digest();
  return createHmac('sha256', derived).update(canonicalRuntime(message)).digest('hex');
}
export async function boundedJson(response: Response, max = 8192): Promise<unknown> {
  if (!response.body) throw new Error('Missing body');
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > max) throw new Error('Body limit');
      chunks.push(value);
    }
  } finally { await reader.cancel().catch(() => {}); }
  const raw = Buffer.concat(chunks);
  return JSON.parse(raw.toString('utf8'));
}
function parseMessage(value: unknown, now: number): RuntimeMessage | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const m = value as RuntimeMessage;
  if (Object.keys(m).sort().join(',') !== 'endpoint,issued_at,operation,schema,session_id,started_at' ||
      m.schema !== RUNTIME_SCHEMA || !['register', 'renew'].includes(m.operation) ||
      typeof m.session_id !== 'string' || !UUID.test(m.session_id) ||
      typeof m.endpoint !== 'string' || m.endpoint.length > 256 ||
      !Number.isSafeInteger(m.started_at) || !Number.isSafeInteger(m.issued_at) ||
      m.started_at <= 0 || m.started_at > m.issued_at ||
      Math.abs(Math.floor(now / 1000) - m.issued_at) > CLOCK_SKEW_SECONDS) return null;
  const url = validBaseUrl(m.endpoint, true);
  if (!url || url.origin !== m.endpoint) return null;
  return m;
}
export async function verifyFacade(endpoint: string, key: string, upstreamFetch: typeof fetch): Promise<boolean> {
  try {
    const headers = { 'x-ai-backend-key': key, 'x-ai-user-id': 'demo-operator' };
    const health = await upstreamFetch(endpoint + '/health', {
      headers, redirect: 'error', cache: 'no-store', signal: AbortSignal.timeout(20000),
    });
    if (health.status !== 200) { await health.body?.cancel(); return false; }
    const h = await boundedJson(health) as Record<string, unknown>;
    if (h.status !== 'ok' || h.service !== 'render-kaggle-demo-v1') return false;
    const response = await upstreamFetch(endpoint + '/deployment/readiness', {
      headers, redirect: 'error', cache: 'no-store', signal: AbortSignal.timeout(30000),
    });
    if (response.status !== 200) { await response.body?.cancel(); return false; }
    const r = await boundedJson(response) as Record<string, unknown>;
    const features = r.supported_features;
    return r.ready === true && r.reason === 'ready' && r.foundation_load_count === 1 &&
      r.diagnostics_version === 'deployment-01' && r.nails_inference_steps === 8 &&
      Array.isArray(features) && ['hairstyle', 'makeup', 'nails'].every(f => features.includes(f));
  } catch { return false; }
}
export async function handleRuntimeRegistration(request: Request, deps: {
  enabled: boolean; key: string; store: RuntimeStore; upstreamFetch: typeof fetch; now?: () => number;
}): Promise<Response> {
  const reply = (status: number, error: string) => Response.json({ error }, { status, headers: PRIVATE });
  if (!deps.enabled || deps.key.length < 32) return reply(503, 'Automatic connection is not configured.');
  if (request.method !== 'POST' || new URL(request.url).search) return reply(404, 'Operation not found.');
  const signature = request.headers.get('x-ai-runtime-signature') ?? '';
  if (!/^[a-f0-9]{64}$/.test(signature)) return reply(401, 'Runtime authentication failed.');
  if (!/^application\/json(?:;|$)/i.test(request.headers.get('content-type') ?? '')) return reply(400, 'Expected JSON.');
  let value: unknown;
  try {
    value = await boundedJson(new Response(request.body), 2048);
  } catch { return reply(400, 'Invalid registration body.'); }
  const now = deps.now?.() ?? Date.now();
  const message = parseMessage(value, now);
  if (!message) return reply(400, 'Invalid or expired registration.');
  if (!timingSafeEqual(Buffer.from(signature, 'hex'), Buffer.from(signRuntime(message, deps.key), 'hex')))
    return reply(401, 'Runtime authentication failed.');
  try {
    const current = await deps.store.get();
    const same = current?.sessionId === message.session_id && current.endpoint === message.endpoint &&
      current.startedAt === message.started_at;
    // Replayed acknowledgement is idempotent and never extends the lease.
    if (same && current.expiresAt > now && current.lastIssuedAt === message.issued_at)
      return Response.json({ connected: true, session_id: current.sessionId, expires_at: current.expiresAt }, { headers: PRIVATE });
    if (current && message.issued_at <= current.lastIssuedAt) return reply(409, 'Stale registration refused.');
    if (message.operation === 'renew') {
      if (!same || current!.expiresAt <= now) return reply(409, 'Session lease expired or replaced. Start a fresh session.');
    } else {
      if (current && !same && (current.expiresAt > now || message.started_at <= current.startedAt))
        return reply(409, 'Another demo session is active or this session is older.');
      if (!await verifyFacade(message.endpoint, deps.key, deps.upstreamFetch))
        return reply(503, 'AI service is running but protected readiness could not be verified.');
    }
    const lease = message.operation === 'renew' ? await deps.store.renew(message) : await deps.store.claim(message);
    // Atomic SQL may reject a concurrent claim that occurred after the initial read.
    if (!lease) return reply(409, 'Session changed during registration. No address was overwritten.');
    return Response.json({ connected: true, session_id: lease.sessionId, expires_at: lease.expiresAt }, { headers: PRIVATE });
  } catch { return reply(503, 'Automatic connection storage is temporarily unavailable.'); }
}
export async function activeRuntimeEndpoint(store: RuntimeStore, now = Date.now()): Promise<string | null> {
  const lease = await store.get();
  if (!lease || !Number.isFinite(lease.expiresAt) || lease.expiresAt <= now || !validBaseUrl(lease.endpoint, true)) return null;
  return lease.endpoint;
}
