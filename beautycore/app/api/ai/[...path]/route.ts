import 'server-only';

import { eq } from 'drizzle-orm';
import { db, databaseSql } from '@/db';
import { users } from '@/db/schema';
import { getSession } from '@/lib/auth';
import { handleAiRequest } from '@/lib/ai/adapter-core';
import { activeRuntimeEndpoint } from '@/lib/ai/runtime-registry';
import { runtimeStore } from '@/lib/ai/runtime-store';
import { archiveConsultationResponse } from '@/lib/business/customer-history';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type Context = { params: Promise<{ path: string[] }> };

async function route(request: Request, context: Context): Promise<Response> {
  const { path } = await context.params;
  const archiveRequest = path[0] === 'consultations' && path[1] === 'photo' && request.method === 'PUT' ? request.clone() : request;
  const principal: { id?: string } = {};
  const response = await handleAiRequest(request, path, {
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
      if (current?.role === 'client') principal.id = current.id;
      return current ? { id: current.id, role: current.role } : null;
    },
  });
  if (response.ok && principal.id && ['consultations','jobs'].includes(path[0])) {
    try {
      const configured = Number(process.env.SAVED_LOOKS_STORAGE_BYTES || 134217728);
      const budget = Number.isSafeInteger(configured) && configured >= 1048576 && configured <= 268435456 ? configured : 134217728;
      await archiveConsultationResponse(archiveRequest,response,path,principal.id,
        (sql,values) => databaseSql.query(sql,values),process.env.AI_CONSULTATION_HANDLE_SECRET || '',budget);
    } catch {
      // A storage failure must never replay, replace, or hide an admitted generation.
      if (path.at(-1) === 'generation' || path[0] === 'jobs') {
        const payload = await response.json();
        return Response.json({ ...payload, archive_warning: 'Your preview is ready, but it could not be archived. Download it now or use Save Look. Check your consultation history before leaving.' },{status:response.status,headers:{'Cache-Control':'private, no-store'}});
      }
      return Response.json({error:'Your consultation or uploaded photo could not be saved to your account. Check image storage capacity and database migrations before continuing.'},{status:503,headers:{'Cache-Control':'private, no-store'}});
    }
  }
  return response;
}

export const GET = route;
export const POST = route;
export const PUT = route;
export const PATCH = route;
