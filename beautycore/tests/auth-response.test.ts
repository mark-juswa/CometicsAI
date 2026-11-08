import test from "node:test";
import assert from "node:assert/strict";
import { authUserFromResponse, readAuthResponse } from "../lib/auth-response";

test("HTML errors and missing auth routes never expose a raw JSON parser error", async () => {
  for (const status of [200, 404, 500, 503]) {
    const response = new Response(
      "<!DOCTYPE html><html>Framework error or missing route</html>",
      { status, headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
    await assert.rejects(
      readAuthResponse(response, "Unable to sign in."),
      (error) =>
        error instanceof Error &&
        error.message ===
          "The account service is unavailable. Refresh the page and try again.",
    );
  }
});
test("malformed JSON and invalid account payloads fail without setting an authenticated user", async () => {
  await assert.rejects(
    readAuthResponse(
      new Response("{not JSON", {
        headers: { "Content-Type": "application/json" },
      }),
      "Sign in failed",
    ),
    /account service is unavailable/,
  );
  await assert.rejects(
    readAuthResponse(Response.json([]), "Sign in failed"),
    /account service is unavailable/,
  );
  for (const user of [
    undefined,
    null,
    {},
    {
      id: "id",
      name: "Name",
      email: "name@example.invalid",
      role: "superadmin",
    },
  ])
    assert.throws(
      () => authUserFromResponse(user),
      /account response was incomplete/,
    );
});
test("invalid credentials keep the existing server message and valid roles keep their account data", async () => {
  await assert.rejects(
    readAuthResponse(
      Response.json({ error: "Invalid email or password." }, { status: 401 }),
      "Sign in failed",
    ),
    /^Error: Invalid email or password\.$/,
  );
  for (const role of ["client", "admin", "stylist"]) {
    const user = {
      id: "id",
      name: "Name",
      email: "name@example.invalid",
      role,
      avatar: null,
    };
    assert.deepEqual(
      authUserFromResponse(
        (await readAuthResponse(Response.json({ user }), "Sign in failed"))
          .user,
      ),
      user,
    );
  }
  assert.deepEqual(
    await readAuthResponse(Response.json({ user: null }), "Session failed"),
    { user: null },
  );
});
