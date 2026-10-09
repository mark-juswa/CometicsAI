import 'server-only';
import { handleRuntimeRegistration } from '@/lib/ai/runtime-registry';
import { runtimeStore } from '@/lib/ai/runtime-store';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function POST(request: Request): Promise<Response> {
  return handleRuntimeRegistration(request, {
    enabled: process.env.AI_ENDPOINT_MODE === 'registered' && process.env.AI_BACKEND_MODE === 'kaggle',
    key: process.env.AI_BACKEND_API_KEY ?? '', store: runtimeStore, upstreamFetch: fetch,
  });
}
