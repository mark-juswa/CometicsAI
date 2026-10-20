import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { JSDOM } from "jsdom";
const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost:3000",
  pretendToBeVisual: true,
});
for (const name of [
  "window",
  "document",
  "HTMLElement",
  "HTMLInputElement",
  "Event",
  "MouseEvent",
  "getComputedStyle",
])
  Object.defineProperty(globalThis, name, {
    value: dom.window[name],
    configurable: true,
    writable: true,
  });
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});
globalThis.self = window;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
for (const path of ["next/image", "next/link"]) {
  const module = await import(path + ".js");
  test.mock.module(path, {
    defaultExport: module.default.default ?? module.default,
  });
}
const { render, screen, fireEvent, cleanup, waitFor } =
  await import("@testing-library/react");
const { AppRouterContext } =
  await import("next/dist/shared/lib/app-router-context.shared-runtime.js");
const { default: Consultation } =
  await import("../components/consultation.tsx");
const originalFetch = globalThis.fetch;
const png =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/X1sAAAAASUVORK5CYII=";
let calls, allowance, mode, hasConsultation, selectedRecommendation, provider;
const rows = ["crew_cut", "bob_hair", "bun"].map((id, index) => ({
  id: "look-" + (index + 1),
  primary: {
    feature: "hairstyle",
    style_id: id,
    style_name: ["Crew Cut", "Bob", "Bun"][index],
    service: { name: "Hair" },
    nail_path: null,
  },
  reason: "Matches your preferences",
  complements: [],
}));
const state = () => ({
  primary_service: "hairstyle",
  stage: "recommended",
  conversation_status: "ready_for_recommendation",
  photo: null,
  messages: [],
  recommendations: { recommendations: rows },
  generations: [],
  selected_recommendation_id: null,
});
const session = () => ({
  state: allowance,
  expires_at: "2030-01-01T00:00:00Z",
  handle: hasConsultation ? "guest-handle" : null,
  recommendation_id: selectedRecommendation,
  result_temporary: true,
  preparation_locked: false,
});
const detail = (id, status = "completed") => ({
  generation: {
    recommendation_id: id,
    status,
    attempts: 1,
    error: null,
    result_available: status === "completed",
  },
  result:
    status === "completed"
      ? {
          image: {
            data_url: png,
            content_type: "image/png",
            width: 1,
            height: 1,
          },
          style: {
            id:
              rows.find((row) => row.id === id)?.primary.style_id ?? "crew_cut",
            name: "Fixture",
            description: "Fixture",
            status: "available",
          },
          status: "completed",
        }
      : null,
});
async function transport(input, init = {}) {
  const path = String(input);
  const method = init.method ?? "GET";
  calls.push({ path, method });
  if (!path.startsWith("/api/ai-trial/"))
    throw new Error("Trial reached a member or external API: " + path);
  const tail = path.slice("/api/ai-trial/".length);
  if (tail === "session") return Response.json(session());
  if (tail === "mode") return Response.json({ provider });
  if (tail === "consultations") {
    hasConsultation = true;
    return Response.json({ ...state(), handle: "guest-handle" });
  }
  if (["consultations/state", "consultations/photo"].includes(tail))
    return Response.json(state());
  if (tail === "consultations/turn") {
    const turns = calls.filter((c) => c.path.endsWith("/turn")).length;
    const ready = turns > 1;
    return Response.json({
      state: {
        ...state(),
        recommendations: ready ? { recommendations: rows } : null,
        messages: [
          {
            role: "assistant",
            content: ready
              ? "Your recommendations are ready."
              : "What is the occasion?",
          },
        ],
      },
      status: ready ? "ready_for_recommendation" : "more_information",
      recommendations: ready ? { recommendations: rows } : null,
    });
  }
  if (tail === "consultations/recommendations")
    return Response.json({ recommendations: rows });
  if (tail.endsWith("/generation")) {
    const id = tail.split("/")[2];
    if (method === "POST") {
      if (mode === "busy") {
        mode = "success";
        provider = "deterministic";
        return Response.json(
          {
            error:
              "Another generation is still running. No new generation was started.",
            code: "AI_BUSY",
          },
          { status: 429 },
        );
      }
      selectedRecommendation = id;
      if (mode === "unknown") {
        allowance = "reserved";
        return Response.json(
          { error: "Connection uncertain. Check status." },
          { status: 503 },
        );
      }
      allowance = "spent";
      return Response.json(detail(id));
    }
    if (mode === "unknown")
      return Response.json(
        { error: "Unresolved trial attempt." },
        { status: 409 },
      );
    return Response.json(
      detail(id, selectedRecommendation ? "completed" : "pending"),
    );
  }
  throw new Error("Unrecognized fixture path " + tail);
}
const router = {
  push() {},
  replace() {},
  prefetch: async () => {},
  back() {},
  forward() {},
  refresh() {},
};
function mount() {
  return render(
    React.createElement(
      AppRouterContext.Provider,
      { value: router },
      React.createElement(Consultation, { trial: true }),
    ),
  );
}
async function prepare() {
  mount();
  await waitFor(() => assert.ok(calls.some((c) => c.path.endsWith("/mode"))));
  fireEvent.click(screen.getByRole("button", { name: /Hairstyle / }));
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.change(screen.getByLabelText("Upload consultation photo"), {
    target: {
      files: [new File(["fixture"], "portrait.png", { type: "image/png" })],
    },
  });
  const button = screen.getByRole("button", { name: "Find my looks" });
  await waitFor(() => assert.equal(button.disabled, false));
  fireEvent.click(button);
  fireEvent.click(
    await screen.findByRole("button", { name: "Explore My Looks" }),
  );
}
test.beforeEach(() => {
  calls = [];
  allowance = "available";
  mode = "success";
  provider = "deterministic";
  hasConsultation = false;
  selectedRecommendation = null;
  globalThis.fetch = transport;
  URL.createObjectURL = () => "blob:trial-fixture";
  URL.revokeObjectURL = () => {};
});
test.afterEach(() => {
  cleanup();
  globalThis.fetch = originalFetch;
});
test("guest chooses recommendation two and generates only that image with signup invitation and real price display", async () => {
  await prepare();
  fireEvent.click(screen.getByRole("button", { name: "View look 2: Bob" }));
  fireEvent.click(screen.getByRole("button", { name: "Generate Bob" }));
  await screen.findByRole("link", { name: "Download" });
  const posts = calls.filter(
    (c) => c.method === "POST" && c.path.endsWith("/generation"),
  );
  assert.deepEqual(
    posts.map((c) => c.path),
    ["/api/ai-trial/consultations/recommendations/look-2/generation"],
  );
  assert.equal(screen.queryByRole("button", { name: /^Generate / }), null);
  assert.equal(
    screen.queryByRole("button", { name: "Select This Look" }),
    null,
  );
  assert.equal(screen.queryByRole("button", { name: "Save Look" }), null);
  assert.equal(
    screen.queryByRole("button", { name: "Book Selected Look" }),
    null,
  );
  assert.equal(screen.queryByText(/Prefer to choose yourself/), null);
  assert.equal(
    screen
      .getByRole("link", { name: "Sign up for the full consultation" })
      .getAttribute("href"),
    "/register?continue=consultation",
  );
  assert.ok(screen.getByText(/not automatically saved or transferred/));
  assert.ok(screen.getByText(/short-to-medium cut/));
  assert.ok(screen.getByText("\u20b1180"));
});
test("reopening a spent trial restores the selected result through reads and cannot generate another", async () => {
  hasConsultation = true;
  allowance = "spent";
  selectedRecommendation = "look-2";
  mount();
  await screen.findByRole("link", { name: "Download" });
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    0,
  );
  assert.ok(
    calls.some(
      (c) => c.method === "GET" && c.path.endsWith("look-2/generation"),
    ),
  );
  assert.equal(screen.queryByRole("button", { name: /^Generate / }), null);
  fireEvent.click(
    screen.getByRole("button", { name: "View look 1: Crew Cut" }),
  );
  assert.equal(screen.queryByRole("button", { name: /^Generate / }), null);
});
test("confirmed busy keeps the allowance available for one deliberate retry", async () => {
  await prepare();
  mode = "busy";
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  await waitFor(() =>
    assert.equal(
      screen.getByRole("button", { name: "Generate Crew Cut" }).disabled,
      false,
    ),
  );
  assert.equal(allowance, "available");
  assert.ok(screen.getByRole("alert"));
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  await screen.findByRole("link", { name: "Download" });
  assert.equal(allowance, "spent");
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    2,
  );
});
test("ambiguous submission locks the trial, permits status reads and never auto retries", async () => {
  await prepare();
  mode = "unknown";
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  await screen.findByRole("button", { name: "Check status" });
  assert.equal(allowance, "reserved");
  assert.equal(screen.queryByRole("button", { name: /^Generate / }), null);
  fireEvent.click(screen.getByRole("button", { name: "Check status" }));
  await waitFor(() => assert.ok(screen.getByRole("alert")));
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    1,
  );
});

test("guest conversational mode reaches recommendations and still generates only one image", async () => {
  provider = "gemini";
  mount();
  await waitFor(() => assert.ok(calls.some((c) => c.path.endsWith("/mode"))));
  fireEvent.click(screen.getByRole("button", { name: /Hairstyle / }));
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.change(screen.getByLabelText("Upload consultation photo"), {
    target: {
      files: [new File(["fixture"], "portrait.png", { type: "image/png" })],
    },
  });
  const start = await screen.findByRole("button", {
    name: "Start AI consultation",
  });
  await waitFor(() => assert.equal(start.disabled, false));
  fireEvent.click(start);
  await screen.findByText("What is the occasion?");
  fireEvent.change(screen.getByLabelText("Your reply"), {
    target: { value: "Graduation" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
  fireEvent.click(
    await screen.findByRole("button", { name: "Explore My Looks" }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  await screen.findByRole("link", { name: "Download" });
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/turn")).length,
    2,
  );
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    1,
  );
});
