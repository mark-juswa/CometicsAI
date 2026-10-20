import { createHash, createHmac, randomBytes, randomUUID } from "node:crypto";
import { isIP } from "node:net";
import {
  applicationOrigin,
  forwardAiRequest,
  isDemoBusy,
  validBaseUrl,
  type AiDependencies,
} from "./adapter-core";
import {
  isConsultationId,
  signConsultationHandle,
} from "./consultation-handle";

export const GUEST_COOKIE = "beautycore_guest_trial";
export const GUEST_AUDIENCE = "beautycore-guest-consultation";
export type Trial = {
  token_hash: string;
  owner_id: string;
  state: "available" | "reserved" | "spent";
  expires_at: string;
  consultation_id: string | null;
  consultation_expires_at: string | null;
  recommendation_id: string | null;
  job_id: string | null;
  operation_id: string | null;
};
export type TrialReply = {
  ok: boolean;
  code?: string;
  trial?: Trial;
  replay?: boolean;
};
export type TrialStore = {
  act(
    action: "status" | "issue" | "prepare" | "finish",
    hash: string,
    network: string | null,
    data?: Record<string, unknown>,
  ): Promise<TrialReply>;
};
export type TrialConfig = {
  enabled: boolean;
  production: boolean;
  days: number;
  networkLimit: number;
  dailyLimit: number;
  generationLimit: number;
  ipHeader: string;
  trustedHops: number;
};
type Dependencies = Omit<AiDependencies, "currentUser"> & {
  store: TrialStore;
  config: TrialConfig;
  signedIn: () => Promise<boolean>;
};
const SAFE = /^[A-Za-z0-9_-]{1,80}$/;
export function trialJson(status: number, error: string): Response {
  return new Response(JSON.stringify({ error }), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "private, no-store",
    },
  });
}
function dataJson(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "private, no-store",
    },
  });
}
function cookie(request: Request): string | null {
  const values = (request.headers.get("cookie") ?? "")
    .split(";")
    .map((s) => s.trim())
    .filter((s) => s.startsWith(GUEST_COOKIE + "="))
    .map((s) => s.slice(GUEST_COOKIE.length + 1));
  return values.length === 1 && /^[a-f0-9]{64}$/.test(values[0])
    ? values[0]
    : null;
}
export function trialTokenHash(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}
/** Trust selection must match the verified deployment proxy chain. Missing configuration fails closed. */
export function trialNetworkTag(
  request: Request,
  config: TrialConfig,
  secret: string,
): string | null {
  let address: string | undefined;
  if (!config.production && !config.ipHeader) address = "127.0.0.1";
  else if (config.ipHeader === "cf-connecting-ip")
    address = request.headers.get("cf-connecting-ip")?.trim();
  else if (
    config.ipHeader === "x-forwarded-for" &&
    Number.isInteger(config.trustedHops) &&
    config.trustedHops > 0
  ) {
    const chain = (request.headers.get("x-forwarded-for") ?? "")
      .split(",")
      .map((s) => s.trim());
    address = chain[chain.length - config.trustedHops];
  }
  if (!address || !isIP(address)) return null;
  // Use a keyed tag, never store the raw IP. IPv4-mapped representations share a tag.
  address = address
    .toLowerCase()
    .replace(/^::ffff:(\d+\.\d+\.\d+\.\d+)$/, "$1");
  return createHmac("sha256", secret)
    .update("beautycore-guest-network:" + address)
    .digest("hex");
}
function failure(reply: TrialReply): Response {
  if (reply.code === "missing")
    return trialJson(401, "Trial session expired. Open the trial again.");
  if (reply.code === "ownership")
    return trialJson(403, "Trial access is invalid.");
  if (reply.code === "in_progress" || reply.code === "conflict")
    return trialJson(
      409,
      "A trial request is already in progress. Check status before continuing.",
    );
  if (reply.code === "spent")
    return trialJson(
      409,
      "Your trial attempt is already used or unresolved. Check status, or sign up for the full consultation.",
    );
  return trialJson(
    429,
    "The guest trial activity limit has been reached. Please sign up or try later.",
  );
}
function allowed(method: string, p: string[]): boolean {
  if (p.length === 1 && p[0] === "session")
    return method === "GET" || method === "POST";
  if (method === "GET" && p.length === 1 && p[0] === "mode") return true;
  if (method === "POST" && p.length === 1 && p[0] === "consultations")
    return true;
  if (
    method === "GET" &&
    p[0] === "jobs" &&
    isConsultationId(p[1]) &&
    (p.length === 2 || (p.length === 3 && p[2] === "result"))
  )
    return true;
  if (p[0] !== "consultations") return false;
  if (p.length === 2)
    return (
      (p[1] === "state" && ["GET", "PATCH"].includes(method)) ||
      (p[1] === "photo" && method === "PUT") ||
      (["turn", "recommendations"].includes(p[1]) && method === "POST")
    );
  return (
    p.length === 4 &&
    p[1] === "recommendations" &&
    SAFE.test(p[2]) &&
    p[3] === "generation" &&
    ["GET", "POST"].includes(method)
  );
}
async function publicTrial(trial: Trial, secret: string) {
  let handle: string | null = null;
  if (trial.consultation_id && trial.consultation_expires_at) {
    try {
      handle = await signConsultationHandle(
        trial.owner_id,
        trial.consultation_id,
        trial.consultation_expires_at,
        secret,
        Date.now(),
        GUEST_AUDIENCE,
      );
    } catch {
      /* Expired temporary state. */
    }
  }
  return {
    state: trial.state,
    expires_at: trial.expires_at,
    handle,
    recommendation_id: trial.recommendation_id,
    result_temporary: true,
    preparation_locked: !!trial.operation_id && trial.state === "available",
  };
}
export async function handleGuestTrial(
  request: Request,
  parts: string[],
  deps: Dependencies,
): Promise<Response> {
  if (
    request.method === "GET" &&
    parts.length === 1 &&
    parts[0] === "availability"
  )
    return dataJson({
      enabled: deps.config.enabled,
      ...(request.headers.get("x-beautycore-proxy-probe") === "v1"
        ? {
            proxy_probe: {
              cloudflare_address_present: !!isIP(
                request.headers.get("cf-connecting-ip")?.trim() ?? "",
              ),
              reserved_test_address_seen: [
                "203.0.113.7",
                "198.51.100.9",
              ].includes(request.headers.get("cf-connecting-ip")?.trim() ?? ""),
            },
          }
        : {}),
    });
  if (!deps.config.enabled)
    return trialJson(404, "Guest consultation trial is unavailable.");
  if (!allowed(request.method, parts) || new URL(request.url).search)
    return trialJson(404, "Trial operation not found.");
  if (request.method !== "GET") {
    const expected = applicationOrigin(request, deps.publicOrigin);
    if (!expected)
      return trialJson(503, "Application origin is not configured correctly.");
    if (request.headers.get("origin") !== expected)
      return trialJson(403, "Same-origin request required.");
  }
  if (
    !deps.remoteBackend ||
    deps.handleSecret.length < 32 ||
    (deps.backendKey?.length ?? 0) < 32
  )
    return trialJson(
      503,
      "Guest trial requires the authenticated hosted AI service.",
    );
  try {
    if (await deps.signedIn())
      return trialJson(409, "Use the full consultation from your account.");
    let token = cookie(request);
    let found = token
      ? await deps.store.act("status", trialTokenHash(token), null)
      : null;
    if (parts[0] === "session" && request.method === "POST" && !found?.ok) {
      let base: string | null = deps.baseUrl;
      if (deps.resolveBaseUrl) base = await deps.resolveBaseUrl();
      if (!base || !validBaseUrl(base, true))
        return trialJson(
          503,
          "AI is offline. Please try when the demo server is running.",
        );
      const network = trialNetworkTag(request, deps.config, deps.handleSecret);
      if (!network)
        return trialJson(
          503,
          "Guest trial network protection is not configured.",
        );
      token = randomBytes(32).toString("hex");
      found = await deps.store.act("issue", trialTokenHash(token), network, {
        days: deps.config.days,
        network_limit: deps.config.networkLimit,
        daily_limit: deps.config.dailyLimit,
      });
    }
    if (!found?.ok || !found.trial || !token)
      return found
        ? failure(found)
        : trialJson(401, "Open the guest trial first.");
    const trial = found.trial;
    const hash = trialTokenHash(token);
    if (parts[0] === "session") {
      const response = dataJson(await publicTrial(trial, deps.handleSecret));
      if (request.method === "POST")
        response.headers.set(
          "Set-Cookie",
          GUEST_COOKIE +
            "=" +
            token +
            "; Path=/; HttpOnly; SameSite=Lax" +
            (deps.config.production ? "; Secure" : "") +
            "; Max-Age=" +
            Math.max(
              0,
              Math.floor((Date.parse(trial.expires_at) - Date.now()) / 1000),
            ),
        );
      return response;
    }
    let policyResponse: Response | null = null;
    const policyFailure = (response: Response) => {
      policyResponse = response.clone();
      return response;
    };
    const forwarded = await forwardAiRequest(
      request,
      parts,
      {
        ...deps,
        upstreamFetch: async (input, init) => {
          let url = new URL(String(input));
          const path = url.pathname;
          const method = init?.method ?? "GET";
          if (path.startsWith("/jobs/")) {
            if (
              !trial.job_id ||
              (path !== "/jobs/" + trial.job_id &&
                path !== "/jobs/" + trial.job_id + "/result")
            )
              return policyFailure(
                trialJson(403, "Trial job access is invalid."),
              );
          } else if (
            path.startsWith("/consultations/") &&
            path !== "/consultations/mode"
          ) {
            const cid = path.split("/")[2];
            if (cid !== trial.consultation_id)
              return policyFailure(
                trialJson(403, "Trial consultation access is invalid."),
              );
          }
          const generation =
            /^\/consultations\/[^/]+\/recommendations\/[^/]+\/generation$/.test(
              path,
            );
          if (method === "GET") {
            if (generation && trial.state !== "available") {
              if (parts[2] !== trial.recommendation_id)
                return policyFailure(
                  trialJson(403, "Trial recommendation access is invalid."),
                );
              if (!trial.job_id)
                return policyFailure(
                  trialJson(
                    409,
                    "Your trial request is unresolved. No new generation will be sent.",
                  ),
                );
              url = new URL("/jobs/" + trial.job_id, url);
            }
            return deps.upstreamFetch(url, init);
          }
          const kind = generation
            ? "generation"
            : path === "/consultations"
              ? "create"
              : path.split("/").at(-1) === trial.consultation_id
                ? "state"
                : path.split("/").at(-1)!;
          const operationId = randomUUID();
          const prepared = await deps.store.act("prepare", hash, null, {
            kind,
            operation_id: operationId,
            consultation_id: trial.consultation_id,
            recommendation_id: generation ? parts[2] : undefined,
            generation_limit: deps.config.generationLimit,
          });
          if (!prepared.ok) return policyFailure(failure(prepared));
          if (prepared.replay)
            return dataJson(
              {
                job_id: prepared.trial!.job_id,
                status: "generating",
                result_available: false,
              },
              202,
            );
          const finish: Record<string, unknown> = {
            kind,
            operation_id: operationId,
          };
          try {
            const response = await deps.upstreamFetch(url, init);
            if (
              generation &&
              response.status === 429 &&
              (await isDemoBusy(response.clone()))
            )
              finish.release = "busy";
            if (response.ok && (kind === "create" || generation)) {
              const value = await response
                .clone()
                .json()
                .catch(() => null);
              if (
                kind === "create" &&
                isConsultationId(value?.id) &&
                typeof value?.expires_at === "string" &&
                Number.isFinite(Date.parse(value.expires_at))
              ) {
                finish.consultation_id = value.id;
                finish.consultation_expires_at = value.expires_at;
              }
              if (
                generation &&
                response.status === 202 &&
                isConsultationId(value?.job_id)
              )
                finish.job_id = value.job_id;
            }
            return response;
          } finally {
            // Even a network exception leaves a reserved allowance. A DB failure also fails closed.
            const done = await deps.store.act("finish", hash, null, finish);
            if (!done.ok)
              throw new Error("Trial completion could not be recorded");
          }
        },
      },
      trial.owner_id,
      GUEST_AUDIENCE,
    );
    return policyResponse ?? forwarded;
  } catch {
    return trialJson(
      503,
      "Guest trial is temporarily unavailable. Check status before sending another request.",
    );
  }
}
export function trialConfig(
  env: Record<string, string | undefined>,
): TrialConfig {
  const number = (key: string, fallback: number, max: number) => {
    const value = Number(env[key]);
    return Number.isInteger(value) && value >= 1 && value <= max
      ? value
      : fallback;
  };
  return {
    enabled: env.AI_GUEST_TRIAL_ENABLED === "true",
    production: env.NODE_ENV === "production",
    days: number("AI_GUEST_TRIAL_DAYS", 30, 90),
    networkLimit: number("AI_GUEST_TRIAL_NETWORK_DAILY_LIMIT", 2, 10),
    dailyLimit: number("AI_GUEST_TRIAL_DAILY_LIMIT", 12, 100),
    generationLimit: number("AI_GUEST_TRIAL_GENERATIONS_DAILY_LIMIT", 4, 50),
    ipHeader: env.AI_GUEST_TRIAL_TRUSTED_IP_HEADER ?? "",
    trustedHops: number("AI_GUEST_TRIAL_TRUSTED_PROXY_HOPS", 1, 10),
  };
}
