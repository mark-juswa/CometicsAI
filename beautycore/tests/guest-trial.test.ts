import test, { before, beforeEach, after } from "node:test";
import assert from "node:assert/strict";
import { PGlite } from "@electric-sql/pglite";
import { guestTrialStatements } from "../scripts/guest-trial-migration";
import {
  handleGuestTrial,
  trialConfig,
  trialTokenHash,
  trialNetworkTag,
  GUEST_AUDIENCE,
  GUEST_COOKIE,
  type TrialStore,
  type TrialReply,
} from "../lib/ai/guest-trial";
import { handleAiRequest } from "../lib/ai/adapter-core";
import {
  signConsultationHandle,
  verifyConsultationHandle,
} from "../lib/ai/consultation-handle";

const SECRET = "guest-test-secret-with-at-least-thirty-two-characters";
const ORIGIN = "http://localhost:3000";
const CID = "11111111-1111-4111-8111-111111111111";
const JOB = "22222222-2222-4222-8222-222222222222";
const OTHER = "33333333-3333-4333-8333-333333333333";
const BASE = "https://guest-test.trycloudflare.com/";
let pg: PGlite;
const config = { ...trialConfig({}), enabled: true };
const store: TrialStore = {
  async act(action, hash, network, data = {}) {
    const result = await pg.query<{ result: TrialReply }>(
      "SELECT beautycore_guest_trial($1,$2,$3,$4::jsonb) AS result",
      [action, hash, network, JSON.stringify(data)],
    );
    return result.rows[0].result;
  },
};
before(async () => {
  pg = new PGlite();
  for (const statement of guestTrialStatements()) await pg.query(statement);
  // Idempotent migration, no account tables or records needed.
  for (const statement of guestTrialStatements()) await pg.query(statement);
});
beforeEach(async () => {
  await pg.exec("TRUNCATE ai_guest_trials");
});
after(async () => {
  await pg.close();
});
function fixture() {
  const seen: { path: string; method: string; headers: Headers }[] = [];
  let response: (path: string) => Response | Promise<Response> = (path) =>
    path === "/consultations"
      ? Response.json(
          {
            id: CID,
            expires_at: new Date(Date.now() + 3600000).toISOString(),
            primary_service: "hairstyle",
            stage: "collecting",
            messages: [],
            generations: [],
          },
          { status: 201 },
        )
      : path === "/consultations/mode"
        ? Response.json({ provider: "gemini" })
        : path.endsWith("/generation")
          ? Response.json(
              { job_id: JOB, status: "generating", result_available: false },
              { status: 202 },
            )
          : Response.json({ ok: true });
  const deps = {
    config,
    store,
    baseUrl: BASE,
    remoteBackend: true,
    handleSecret: SECRET,
    backendKey: SECRET,
    signedIn: async () => false,
    upstreamFetch: (async (input: URL | RequestInfo, init?: RequestInit) => {
      const path = new URL(String(input)).pathname;
      seen.push({
        path,
        method: init?.method ?? "GET",
        headers: new Headers(init?.headers),
      });
      return response(path);
    }) as typeof fetch,
  };
  let cookie = "";
  let handle = "";
  const request = (method: string, path: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers);
    if (method !== "GET") headers.set("origin", ORIGIN);
    if (cookie) headers.set("cookie", cookie);
    if (handle) headers.set("x-ai-consultation-handle", handle);
    return new Request(ORIGIN + "/api/ai-trial/" + path, {
      ...options,
      method,
      headers,
    });
  };
  const call = (method: string, path: string, options?: RequestInit) =>
    handleGuestTrial(request(method, path, options), path.split("/"), deps);
  const open = async () => {
    const r = await call("POST", "session");
    assert.equal(r.status, 200);
    cookie = r.headers.get("set-cookie")!.split(";")[0];
    return r;
  };
  const create = async () => {
    const r = await call("POST", "consultations", {
      headers: { "content-type": "application/json" },
      body: '{"primary_service":"hairstyle"}',
    });
    assert.equal(r.status, 201);
    handle = (await r.json()).handle;
    return handle;
  };
  return {
    deps,
    seen,
    call,
    open,
    create,
    request,
    get cookie() {
      return cookie;
    },
    set cookie(value: string) {
      cookie = value;
    },
    set handle(value: string) {
      handle = value;
    },
    set respond(value: typeof response) {
      response = value;
    },
  };
}
const generation = "consultations/recommendations/look-1/generation";

test("disabled trial, forbidden paths and foreign origins cannot issue allowances or reach AI", async () => {
  const f = fixture();
  assert.equal(
    (
      await handleGuestTrial(f.request("POST", "session"), ["session"], {
        ...f.deps,
        config: { ...config, enabled: false },
      })
    ).status,
    404,
  );
  for (const path of [
    "features/nails/generate",
    "consultations/raw-id",
    "catalog",
    "runtime/register",
    "consultations/recommendations/look-1/select",
  ])
    assert.equal((await f.call("POST", path)).status, 404);
  assert.equal(
    (
      await handleGuestTrial(
        new Request(ORIGIN + "/api/ai-trial/session", {
          method: "POST",
          headers: { origin: "https://evil.invalid" },
        }),
        ["session"],
        f.deps,
      )
    ).status,
    403,
  );
  assert.equal(
    (
      await handleGuestTrial(
        new Request(ORIGIN + "/api/ai-trial/session", { method: "POST" }),
        ["session"],
        { ...f.deps, publicOrigin: "not-an-origin" },
      )
    ).status,
    503,
  );
  assert.equal(f.seen.length, 0);
  assert.equal(
    (await pg.query("SELECT * FROM ai_guest_trials")).rows.length,
    0,
  );
});
test("availability works while disabled without touching store or auth", async () => {
  const f = fixture();
  const r = await handleGuestTrial(
    f.request("GET", "availability"),
    ["availability"],
    {
      ...f.deps,
      config: { ...config, enabled: false },
      store: {
        act: async () => {
          throw new Error("must not read");
        },
      },
      signedIn: async () => {
        throw new Error("must not auth");
      },
    },
  );
  assert.deepEqual(await r.json(), { enabled: false });
});
test("cookie and Neon status survive refresh/reconstructed handler; no images or accounts are persisted", async () => {
  const f = fixture();
  const r = await f.open();
  assert.match(r.headers.get("set-cookie")!, /HttpOnly/);
  assert.match(r.headers.get("set-cookie")!, /SameSite=Lax/);
  assert.match(r.headers.get("set-cookie")!, /Max-Age=25919\d\d/);
  assert.deepEqual((await f.call("GET", "session")).status, 200);
  const g = fixture();
  g.cookie = f.cookie;
  assert.equal((await g.call("POST", "session")).status, 200);
  assert.equal(
    (await pg.query("SELECT * FROM ai_guest_trials")).rows.length,
    1,
  );
  assert.equal(f.seen.length, 0);
});
test("production fails closed on unconfigured proxy and local/unkeyed backend; signed-in users use full consultation", async () => {
  const f = fixture();
  assert.equal(
    (
      await handleGuestTrial(f.request("POST", "session"), ["session"], {
        ...f.deps,
        config: { ...config, production: true },
      })
    ).status,
    503,
  );
  assert.equal(
    (
      await handleGuestTrial(f.request("POST", "session"), ["session"], {
        ...f.deps,
        remoteBackend: false,
      })
    ).status,
    503,
  );
  assert.equal(
    (
      await handleGuestTrial(f.request("POST", "session"), ["session"], {
        ...f.deps,
        signedIn: async () => true,
      })
    ).status,
    409,
  );
  assert.equal(
    (await pg.query("SELECT * FROM ai_guest_trials")).rows.length,
    0,
  );
});
test("trusted proxy selection ignores spoofed left entries and never stores raw IP", () => {
  const c = {
    ...config,
    production: true,
    ipHeader: "x-forwarded-for",
    trustedHops: 1,
  };
  const req = (ip: string) =>
    new Request(ORIGIN, { headers: { "x-forwarded-for": ip } });
  assert.equal(
    trialNetworkTag(req("6.6.6.6, 192.0.2.4"), c, SECRET),
    trialNetworkTag(req("1.1.1.1, 192.0.2.4"), c, SECRET),
  );
  assert.equal(
    trialNetworkTag(req("6.6.6.6"), { ...c, trustedHops: 2 }, SECRET),
    null,
  );
  assert.equal(trialNetworkTag(req("invalid"), c, SECRET), null);
  assert.match(trialNetworkTag(req("192.0.2.4"), c, SECRET)!, /^[a-f0-9]{64}$/);
});
test("purpose-separated handles and server-derived owners protect member and guest access", async () => {
  const f = fixture();
  await f.open();
  const handle = await f.create();
  const row = (
    await pg.query<{ owner_id: string }>("SELECT owner_id FROM ai_guest_trials")
  ).rows[0];
  assert.equal(
    await verifyConsultationHandle(handle, row.owner_id, SECRET),
    null,
  );
  assert.equal(
    await verifyConsultationHandle(
      handle,
      row.owner_id,
      SECRET,
      Date.now(),
      GUEST_AUDIENCE,
    ),
    CID,
  );
  const member = await handleAiRequest(
    new Request(ORIGIN + "/api/ai/mode"),
    ["mode"],
    { ...f.deps, currentUser: async () => null },
  );
  assert.equal(member.status, 401);
  const memberHandle = await signConsultationHandle(
    row.owner_id,
    CID,
    new Date(Date.now() + 3600000).toISOString(),
    SECRET,
  );
  f.handle = memberHandle;
  assert.equal((await f.call("GET", "consultations/state")).status, 403);
  f.handle = handle;
  const r = await f.call("POST", generation, {
    headers: { "x-ai-user-id": "other-client", "x-ai-backend-key": "attacker" },
  });
  assert.equal(r.status, 202);
  const sent = f.seen.at(-1)!;
  assert.equal(sent.headers.get("x-ai-user-id"), row.owner_id);
  assert.equal(sent.headers.get("x-ai-backend-key"), SECRET);
  assert.ok(!JSON.stringify(await r.json()).includes(SECRET));
});
test("simultaneous tabs reserve only one generation; same-attempt replay never forwards again", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  f.respond = async () => {
    await new Promise((resolve) => setTimeout(resolve, 30));
    return Response.json(
      { job_id: JOB, status: "generating" },
      { status: 202 },
    );
  };
  const results = await Promise.all([
    f.call("POST", generation),
    f.call("POST", generation),
  ]);
  assert.equal(results.filter((r) => r.status === 202).length, 1);
  assert.equal(results.filter((r) => r.status === 409).length, 1);
  assert.equal(f.seen.filter((s) => s.path.endsWith("/generation")).length, 1);
  assert.equal((await f.call("POST", generation)).status, 202);
  assert.equal(f.seen.filter((s) => s.path.endsWith("/generation")).length, 1);
  assert.equal(
    (await f.call("POST", "consultations/recommendations/look-2/generation"))
      .status,
    409,
  );
  assert.equal(
    (
      await f.call("POST", "consultations", {
        headers: { "content-type": "application/json" },
        body: "{}",
      })
    ).status,
    409,
  );
  assert.equal(
    (await f.call("GET", "session").then((r) => r.json())).state,
    "spent",
  );
});
test("only confirmed pre-admission busy releases credit; retry budget stops repeated busy POSTs", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  f.respond = () =>
    Response.json(
      { detail: "The demo is busy. No new generation was started." },
      { status: 429 },
    );
  for (let i = 0; i < 8; i++) {
    const r = await f.call("POST", generation);
    assert.equal(r.status, 429);
    assert.equal((await r.json()).code, "AI_BUSY");
    assert.equal(
      (await f.call("GET", "session").then((r) => r.json())).state,
      "available",
    );
  }
  const limited = await f.call("POST", generation);
  assert.equal(limited.status, 429);
  assert.match((await limited.json()).error, /activity limit/);
  assert.equal(f.seen.filter((s) => s.path.endsWith("/generation")).length, 8);
});
test("unknown 429, malformed admission and network failure keep allowance locked without automatic POST retry", async () => {
  for (const failure of [
    () => Response.json({ detail: "provider quota" }, { status: 429 }),
    () => Response.json({ job_id: "bad" }, { status: 202 }),
    () => {
      throw new Error("network disconnected");
    },
  ]) {
    await pg.exec("TRUNCATE ai_guest_trials");
    const f = fixture();
    await f.open();
    await f.create();
    f.respond = failure;
    await f.call("POST", generation);
    assert.equal(
      (await f.call("GET", "session").then((r) => r.json())).state,
      "reserved",
    );
    assert.equal((await f.call("POST", generation)).status, 409);
    assert.equal(
      f.seen.filter((s) => s.path.endsWith("/generation")).length,
      1,
    );
  }
});
test("own job status is resumable and foreign jobs/recommendations/guest handles are denied", async () => {
  const f = fixture();
  await f.open();
  const handle = await f.create();
  await f.call("POST", generation);
  f.respond = () => Response.json({ job_id: JOB, status: "generating" });
  const status = await f.call("GET", generation);
  assert.equal(status.status, 200);
  assert.equal((await status.json()).job_id, JOB);
  assert.equal(f.seen.at(-1)!.path, "/jobs/" + JOB);
  assert.equal((await f.call("GET", "jobs/" + OTHER)).status, 403);
  assert.equal(
    (await f.call("GET", "consultations/recommendations/look-2/generation"))
      .status,
    403,
  );
  const g = fixture();
  await g.open();
  g.handle = handle;
  assert.equal((await g.call("GET", "consultations/state")).status, 403);
  assert.equal((await g.call("GET", "jobs/" + JOB)).status, 403);
});
test("invalid uploads and offline endpoint detection happen before generation reservation", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  const r = await f.call("PUT", "consultations/photo", {
    headers: { "content-type": "text/plain" },
    body: "invalid",
  });
  assert.equal(r.status, 400);
  const offline = await handleGuestTrial(
    f.request("POST", generation),
    generation.split("/"),
    { ...f.deps, resolveBaseUrl: async () => null },
  );
  assert.equal(offline.status, 503);
  const row = (
    await pg.query<{ state: string; counters: Record<string, number> }>(
      "SELECT state,counters FROM ai_guest_trials",
    )
  ).rows[0];
  assert.equal(row.state, "available");
  assert.equal(row.counters.generation, undefined);
});
test("consultation recreation and text requests have durable per-trial bounds", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  f.respond = () => Response.json({ recommendations: [] });
  for (let i = 0; i < 2; i++)
    assert.equal(
      (await f.call("POST", "consultations/recommendations")).status,
      200,
    );
  assert.equal(
    (await f.call("POST", "consultations/recommendations")).status,
    429,
  );
  for (let i = 0; i < 6; i++)
    assert.equal(
      (
        await f.call("POST", "consultations/turn", {
          headers: { "content-type": "application/json" },
          body: "{}",
        })
      ).status,
      502,
    );
  assert.equal(
    (
      await f.call("POST", "consultations/turn", {
        headers: { "content-type": "application/json" },
        body: "{}",
      })
    ).status,
    429,
  );
});
test("clearing cookie cannot bypass configured network issuance cap; global generation budget is durable", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  await f.call("POST", generation);
  const g = fixture();
  await g.open();
  await g.create();
  g.deps.config = { ...config, generationLimit: 1 };
  assert.equal((await g.call("POST", generation)).status, 429);
  assert.match(
    (await g.call("POST", generation).then((r) => r.json())).error,
    /activity limit/,
  );
  const h = fixture();
  assert.equal((await h.call("POST", "session")).status, 429);
});
test("expired handles/jobs and interrupted reservation do not grant replacement credit", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  await f.call("POST", generation);
  await pg.exec(
    "UPDATE ai_guest_trials SET consultation_expires_at=now()-interval '1 second'",
  );
  const value = await f.call("GET", "session").then((r) => r.json());
  assert.equal(value.handle, null);
  assert.equal(value.state, "spent");
  f.respond = () => Response.json({ detail: "lost session" }, { status: 404 });
  assert.equal((await f.call("GET", "jobs/" + JOB)).status, 404);
  assert.equal((await f.call("POST", generation)).status, 202); // Same ticket; no GPU resubmission.
  assert.equal(f.seen.filter((s) => s.path.endsWith("/generation")).length, 1);
});
test("database failure after admission fails closed and leaves a durable unresolved reservation", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  const broken: TrialStore = {
    act: async (a, h, n, d) => {
      if (a === "finish") throw new Error("storage interruption");
      return store.act(a, h, n, d);
    },
  };
  const r = await handleGuestTrial(
    f.request("POST", generation),
    generation.split("/"),
    { ...f.deps, store: broken },
  );
  assert.equal(r.status, 502);
  assert.equal(
    (await f.call("GET", "session").then((r) => r.json())).state,
    "reserved",
  );
  assert.equal((await f.call("POST", generation)).status, 409);
  const row = (
    await pg.query<{ operation_id: string | null }>(
      "SELECT operation_id FROM ai_guest_trials",
    )
  ).rows[0];
  assert.ok(row.operation_id);
});

test("production cookie is Secure and duplicate cookies are not accepted as an identity", async () => {
  const f = fixture();
  const production = {
    ...f.deps,
    config: { ...config, production: true, ipHeader: "cf-connecting-ip" },
  };
  const request = new Request(ORIGIN + "/api/ai-trial/session", {
    method: "POST",
    headers: { origin: ORIGIN, "cf-connecting-ip": "192.0.2.9" },
  });
  const response = await handleGuestTrial(request, ["session"], production);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("set-cookie")!, /; Secure/);
  const duplicate = (
    response.headers.get("set-cookie")!.split(";")[0] + "; "
  ).repeat(2);
  const invalid = await handleGuestTrial(
    new Request(ORIGIN + "/api/ai-trial/session", {
      headers: { cookie: duplicate },
    }),
    ["session"],
    production,
  );
  assert.equal(invalid.status, 401);
});
test("global consultation-start budget is atomic across separate guests", async () => {
  const trials = [];
  for (let i = 0; i < 4; i++) {
    const f = fixture();
    f.deps.config = { ...config, networkLimit: 10 };
    await f.open();
    trials.push(f);
  }
  for (const f of trials.slice(0, 3)) {
    await f.create();
    await f.create();
  }
  const limited = await trials[3].call("POST", "consultations", {
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  assert.equal(limited.status, 429);
  assert.equal(trials[3].seen.length, 0);
});
test("an expired cookie allowance can renew only after its fixed period, with a new identity", async () => {
  const f = fixture();
  await f.open();
  await f.create();
  await f.call("POST", generation);
  const previousCookie = f.cookie;
  await pg.exec(
    "UPDATE ai_guest_trials SET created_at=now()-interval '31 days',expires_at=now()-interval '1 day'",
  );
  const renewed = await f.call("POST", "session");
  assert.equal(renewed.status, 200);
  assert.notEqual(
    renewed.headers.get("set-cookie")!.split(";")[0],
    previousCookie,
  );
  assert.equal((await renewed.json()).state, "available");
});

test("opt-in proxy probe discloses only booleans and never touches auth, storage or inference", async () => {
  const f = fixture();
  const deps = {
    ...f.deps,
    config: { ...config, enabled: false },
    store: {
      act: async () => {
        throw new Error("must not read");
      },
    },
    signedIn: async () => {
      throw new Error("must not auth");
    },
  };
  for (const address of ["203.0.113.7", "198.51.100.9", "192.0.2.25", ""]) {
    const request = new Request(ORIGIN + "/api/ai-trial/availability", {
      headers: {
        "x-beautycore-proxy-probe": "v1",
        "cf-connecting-ip": address,
      },
    });
    const r = await handleGuestTrial(request, ["availability"], deps);
    assert.deepEqual(await r.json(), {
      enabled: false,
      proxy_probe: {
        cloudflare_address_present: !!address,
        reserved_test_address_seen: ["203.0.113.7", "198.51.100.9"].includes(
          address,
        ),
      },
    });
  }
  assert.equal(f.seen.length, 0);
});
