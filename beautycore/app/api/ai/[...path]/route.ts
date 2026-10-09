import 'server-only';

import { eq } from 'drizzle-orm';
import { db } from '@/db';
import { users } from '@/db/schema';
import { getSession } from '@/lib/auth';
import { handleAiRequest } from '@/lib/ai/adapter-core';
import { activeRuntimeEndpoint } from '@/lib/ai/runtime-registry';
import { runtimeStore } from '@/lib/ai/runtime-store';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type Context = { params: Promise<{ path: string[] }> };

async function route(request: Request, context: Context): Promise<Response> {
  const { path } = await context.params;
  return handleAiRequest(request, path, {
    baseUrl: process.env.AI_FASTAPI_URL ?? '',
    resolveBaseUrl: process.env.AI_BACKEND_MODE === 'kaggle' && process.env.AI_ENDPOINT_MODE === 'registered'
      ? () => activeRuntimeEndpoint(runtimeStore) : undefined,
    handleSecret: process.env.AI_CONSULTATION_HANDLE_SECRET ?? '',
    remoteBackend: process.env.AI_BACKEND_MODE === 'kaggle',
    backendKey: process.env.AI_BACKEND_API_KEY ?? '',
    publicOrigin: process.env.RENDER_EXTERNAL_URL,
    upstreamFetch: fetch,
    currentUser: async () => {
      const session = await getSession();
      if (!session) return null;
      const current = await db.query.users.findFirst({
        where: eq(users.id, session.userId),
        columns: { id: true, role: true },
      });
      return current ? { id: current.id, role: current.role } : null;
    },
  });
}

export const GET = route;
export const POST = route;
export const PUT = route;
export const PATCH = route;
