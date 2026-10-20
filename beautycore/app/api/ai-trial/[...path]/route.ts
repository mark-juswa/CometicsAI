import "server-only";
import { getSession } from "@/lib/auth";
import { handleGuestTrial, trialConfig } from "@/lib/ai/guest-trial";
import { guestTrialStore } from "@/lib/ai/guest-trial-store";
import { activeRuntimeEndpoint } from "@/lib/ai/runtime-registry";
import { runtimeStore } from "@/lib/ai/runtime-store";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
async function route(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleGuestTrial(request, (await context.params).path, {
    store: guestTrialStore,
    config: trialConfig(process.env),
    signedIn: async () => !!(await getSession()),
    baseUrl: process.env.AI_FASTAPI_URL ?? "",
    resolveBaseUrl:
      process.env.AI_ENDPOINT_MODE === "registered"
        ? () => activeRuntimeEndpoint(runtimeStore)
        : undefined,
    remoteBackend: process.env.AI_BACKEND_MODE === "kaggle",
    backendKey: process.env.AI_BACKEND_API_KEY ?? "",
    handleSecret: process.env.AI_CONSULTATION_HANDLE_SECRET ?? "",
    publicOrigin: process.env.RENDER_EXTERNAL_URL,
    upstreamFetch: fetch,
  });
}
export const GET = route;
export const POST = route;
export const PUT = route;
export const PATCH = route;
