import test from "node:test";
import assert from "node:assert/strict";
import { saveLook, businessRequest } from "../lib/business/client";
const result = {
  status: "completed",
  style: { id: "fixture" },
  image: { data_url: "data:image/png;base64,fixture" },
} as Parameters<typeof saveLook>[1];
test("saved look retries temporary admission errors using the identical payload", async () => {
  const original = globalThis.fetch,
    bodies: unknown[] = [];
  globalThis.fetch = async (_input, init) => {
    bodies.push(init?.body);
    return bodies.length < 3
      ? Response.json(
          { error: "Please try again." },
          { status: bodies.length === 1 ? 429 : 503 },
        )
      : Response.json({ look: { id: "saved-id" } });
  };
  try {
    assert.equal((await saveLook("nails", result, "manual")).id, "saved-id");
    assert.equal(bodies.length, 3);
    assert.ok(bodies.every((b) => b === bodies[0]));
  } finally {
    globalThis.fetch = original;
  }
});
test("permanent save errors are shown without retries", async () => {
  const original = globalThis.fetch;
  try {
    for (const status of [400, 401, 403, 409, 413, 507]) {
      let calls = 0;
      globalThis.fetch = async () => {
        calls++;
        return Response.json({ error: "Specific save error" }, { status });
      };
      await assert.rejects(
        saveLook("nails", result, "manual"),
        /Specific save error/,
      );
      assert.equal(calls, 1);
    }
  } finally {
    globalThis.fetch = original;
  }
});
test("HTML responses produce a usable error and exhausted retries stop", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response("<!DOCTYPE html><html>Error</html>", { status: 502 });
  };
  try {
    await assert.rejects(
      saveLook("nails", result, "manual"),
      /unexpected response/,
    );
    assert.equal(calls, 3);
    await assert.rejects(
      businessRequest("/api/example"),
      /unexpected response/,
    );
  } finally {
    globalThis.fetch = original;
  }
});
