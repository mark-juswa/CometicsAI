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
  "HTMLDialogElement",
  "Event",
  "CustomEvent",
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
const modalReturnFocus = new WeakMap();
HTMLDialogElement.prototype.showModal = function () {
  modalReturnFocus.set(this, document.activeElement);
  this.setAttribute("open", "");
  this.querySelector("[autofocus]")?.focus();
};
HTMLDialogElement.prototype.close = function () {
  this.removeAttribute("open");
  modalReturnFocus.get(this)?.focus();
  this.dispatchEvent(new Event("close"));
};
globalThis.self = window;
globalThis.sessionStorage = window.sessionStorage;
globalThis.requestAnimationFrame = (callback) => callback();
HTMLElement.prototype.scrollIntoView = function () {};
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
for (const path of ["next/image", "next/link"]) {
  const module = await import(path + ".js");
  test.mock.module(path, {
    defaultExport: module.default.default ?? module.default,
  });
}
const { render, screen, fireEvent, cleanup, waitFor, within, act } =
  await import("@testing-library/react");
const { AppRouterContext } =
  await import("next/dist/shared/lib/app-router-context.shared-runtime.js");
const { default: Consultation } =
  await import("../components/consultation.tsx");
const { GenerationContext } =
  await import("../components/generation-provider.tsx");
const { GenerationStore } = await import("../lib/ai/generation-store.ts");
const { inferConsultationService, consultationTurnRecorded } =
  await import("../lib/ai/consultation-preparation.ts");
const { resolveLookInformation } =
  await import("../lib/business/look-information.ts");
const {
  readConsultationPreparation,
  writeConsultationPreparation,
  consultationPreparationEpoch,
  expiredConsultationAccess,
} = await import("../lib/ai/consultation-preparation.ts");
const { signConsultationHandle } =
  await import("../lib/ai/consultation-handle.ts");
const { clearGenerationDrafts } =
  await import("../lib/ai/generation-storage.ts");
const signingSecret = "test-only-preparation-token-secret-20261116";
async function guestHandle(
  now,
  subject = "guest-fixture",
  cid = "11111111-1111-4111-8111-111111111111",
  audience = "beautycore-guest-consultation",
) {
  return signConsultationHandle(
    subject,
    cid,
    new Date(now + 60 * 60 * 1000).toISOString(),
    signingSecret,
    now,
    audience,
  );
}
const originalFetch = globalThis.fetch;
const png =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/X1sAAAAASUVORK5CYII=";
let calls,
  allowance,
  mode,
  hasConsultation,
  selectedRecommendation,
  provider,
  finishGeneration;
let messages, uploaded;
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
  photo: uploaded ? { content_type: "image/png" } : null,
  messages,
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
  if (tail === "consultations/photo") uploaded = true;
  if (["consultations/state", "consultations/photo"].includes(tail))
    return Response.json(state());
  if (tail === "consultations/turn") {
    const turns = calls.filter((c) => c.path.endsWith("/turn")).length;
    const ready = turns > 1;
    messages.push(
      { role: "user", content: JSON.parse(init.body).message },
      {
        role: "assistant",
        content: ready
          ? "Your recommendations are ready."
          : "What is the occasion?",
      },
    );
    return Response.json({
      state: {
        ...state(),
        recommendations: ready ? { recommendations: rows } : null,
        messages,
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
      if (mode === "processing")
        await new Promise((resolve) => {
          finishGeneration = resolve;
        });
      selectedRecommendation = id;
      if (mode === "unknown") {
        allowance = "reserved";
        return Response.json(
          { error: "Connection uncertain. Check status." },
          { status: 503 },
        );
      }
      allowance = "spent";
      return Response.json(
        detail(id, mode === "failed" ? "failed" : "completed"),
      );
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
function mount(trial = true, store = null) {
  return render(
    React.createElement(
      AppRouterContext.Provider,
      { value: router },
      React.createElement(
        GenerationContext.Provider,
        { value: store },
        React.createElement(Consultation, { trial }),
      ),
    ),
  );
}
async function prepare() {
  mount();
  await waitFor(() => assert.ok(calls.some((c) => c.path.endsWith("/mode"))));
  fireEvent.click(screen.getByRole("button", { name: /Hairstyle / }));
  fireEvent.change(screen.getByLabelText("Your reply"), {
    target: { value: "A simple haircut" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
  assert.ok(screen.getByRole("button", { name: "Use camera", exact: true }));
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
  sessionStorage.clear();
  calls = [];
  allowance = "available";
  mode = "success";
  provider = "deterministic";
  hasConsultation = false;
  selectedRecommendation = null;
  finishGeneration = null;
  messages = [];
  uploaded = false;
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
  const dialog = await screen.findByRole("dialog", {
    name: "Your free trial has been used",
  });
  assert.equal(
    within(dialog)
      .getByRole("link", { name: "Create account" })
      .getAttribute("href"),
    "/register?continue=consultation",
  );
  assert.equal(
    within(dialog).getByRole("link", { name: "Log in" }).getAttribute("href"),
    "/login?continue=consultation",
  );
  assert.ok(within(dialog).getByText(/not automatically saved or transferred/));
  fireEvent.click(
    within(dialog).getByRole("button", { name: "Keep browsing" }),
  );
  await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
  assert.ok(
    within(screen.getByLabelText("Guest trial allowance")).getByText(
      /0 of 1 previews remaining/,
    ),
  );
  assert.ok(
    screen.getByRole("heading", { name: "Your trial recommendations" }),
  );
  assert.ok(screen.getByText(/short-to-medium cut/));
  assert.ok(
    screen.getAllByText(
      resolveLookInformation("hairstyle", "bob_hair").options[0].priceLabel,
    ).length,
  );
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
  const initialDialog = await screen.findByRole("dialog", {
    name: "Your free trial has been used",
  });
  fireEvent.click(
    within(initialDialog).getByRole("button", { name: "Keep browsing" }),
  );
  await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
  fireEvent.click(
    screen.getByRole("button", { name: "View look 1: Crew Cut" }),
  );
  await screen.findByRole("dialog", { name: "Your free trial has been used" });
  assert.ok(screen.getAllByText("Account required").length > 0);
  assert.equal(screen.queryByText("Your preview is up next"), null);
  assert.equal(screen.queryByRole("button", { name: /^Generate / }), null);
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    0,
  );
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
  assert.equal(screen.queryByRole("dialog"), null);
  assert.ok(
    within(screen.getByLabelText("Guest trial allowance")).getByText(
      "1 free preview available",
    ),
  );
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
  fireEvent.change(screen.getByLabelText("Your reply"), {
    target: { value: "A simple haircut" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
  fireEvent.change(screen.getByLabelText("Upload consultation photo"), {
    target: {
      files: [new File(["fixture"], "portrait.png", { type: "image/png" })],
    },
  });
  const start = await screen.findByRole("button", {
    name: "Continue consultation",
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

test("used-trial modal can be dismissed and reopened near the controls without another generation", async () => {
  await prepare();
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  const dialog = await screen.findByRole("dialog", {
    name: "Your free trial has been used",
  });
  fireEvent.click(
    within(dialog).getByRole("button", { name: "Keep browsing" }),
  );
  await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
  assert.ok(screen.getByRole("link", { name: "Download" }));
  const unlock = within(
    screen.getByLabelText("Guest trial allowance"),
  ).getByRole("button", { name: "Unlock more previews" });
  unlock.focus();
  fireEvent.click(unlock);
  const reopened = await screen.findByRole("dialog", {
    name: "Your free trial has been used",
  });
  fireEvent(reopened, new Event("cancel", { cancelable: true }));
  await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
  assert.equal(document.activeElement, unlock);
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    1,
  );
});

test("in-flight generation shows processing and no used-trial modal until it settles", async () => {
  await prepare();
  mode = "processing";
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  await waitFor(() => assert.equal(typeof finishGeneration, "function"));
  assert.ok(
    within(screen.getByLabelText("Guest trial allowance")).getByText(
      "Your trial preview is in progress",
    ),
  );
  assert.equal(screen.queryByRole("dialog"), null);
  await act(async () => {
    finishGeneration();
  });
  await screen.findByRole("dialog", { name: "Your free trial has been used" });
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    1,
  );
});

test("unknown requests have status guidance without falsely declaring a successful preview or starting more work", async () => {
  await prepare();
  mode = "unknown";
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  await screen.findByRole("button", { name: "Check status" });
  assert.equal(screen.queryByRole("dialog"), null);
  const indicator = screen.getByLabelText("Guest trial allowance");
  assert.ok(within(indicator).getByText("Trial request unresolved"));
  fireEvent.click(
    within(indicator).getByRole("button", { name: "View trial details" }),
  );
  const dialog = await screen.findByRole("dialog", {
    name: "Check your current trial request",
  });
  assert.ok(within(dialog).getByText(/may still be running/));
  assert.equal(within(dialog).queryByText(/0 of 1 previews remaining/), null);
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    1,
  );
});

test("an accepted failed attempt shows the used allowance without claiming an image was delivered", async () => {
  await prepare();
  mode = "failed";
  fireEvent.click(screen.getByRole("button", { name: "Generate Crew Cut" }));
  const dialog = await screen.findByRole("dialog", {
    name: "Your free trial has been used",
  });
  assert.ok(within(dialog).getByText(/generation attempt has been used/));
  assert.equal(
    within(dialog).queryByText(/download your generated preview/),
    null,
  );
  assert.equal(screen.queryByRole("link", { name: "Download" }), null);
  assert.equal(screen.queryByRole("button", { name: "Retry this look" }), null);
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    1,
  );
});

test("used allowance still has clear modal feedback when the temporary consultation is gone", async () => {
  allowance = "spent";
  hasConsultation = false;
  mount();
  const dialog = await screen.findByRole("dialog", {
    name: "Your free trial has been used",
  });
  assert.equal(document.body.style.overflow, "hidden");
  assert.ok(within(dialog).getByText(/0 of 1 previews remaining/));
  assert.equal(
    within(dialog).queryByText(/download your generated preview/),
    null,
  );
  fireEvent.click(
    within(dialog).getByRole("button", { name: "Keep browsing" }),
  );
  await waitFor(() => assert.equal(screen.queryByRole("dialog"), null));
  assert.equal(document.body.style.overflow, "");
  fireEvent.click(screen.getByRole("button", { name: /Hairstyle / }));
  await screen.findByRole("dialog", { name: "Your free trial has been used" });
  assert.equal(
    calls.filter((c) => c.method === "POST" && c.path.endsWith("/generation"))
      .length,
    0,
  );
  assert.equal(
    calls.filter(
      (c) => c.method === "POST" && c.path.endsWith("/consultations"),
    ).length,
    0,
  );
});

// AC-2, AC-3, AC-5: preparation and recovery use the real browser API adapter.
let memberState,
  memberMode,
  photoFailure,
  turnFailure,
  turnGate,
  generationGate,
  generationMode,
  navigations,
  setupExpired,
  stateGate;
function memberView() {
  return structuredClone(memberState);
}
async function memberTransport(input, init = {}) {
  const path = String(input),
    method = init.method || "GET";
  calls.push({
    path,
    method,
    body: typeof init.body === "string" ? JSON.parse(init.body) : init.body,
    handle: new Headers(init.headers).get("x-ai-consultation-handle"),
  });
  if (path === "/api/ai/mode") return Response.json({ provider: memberMode });
  if (path === "/api/ai/consultations") {
    memberState.primary_service = JSON.parse(init.body).primary_service;
    return Response.json({ ...memberView(), handle: "member-handle" });
  }
  if (path.endsWith("/photo")) {
    if (setupExpired === "access")
      return Response.json(
        { error: "Consultation access is invalid or expired." },
        { status: 403 },
      );
    if (setupExpired === "photo")
      return Response.json({ error: "Photo session expired" }, { status: 410 });
    if (photoFailure) {
      photoFailure = false;
      return Response.json(
        { error: "Photo upload interrupted" },
        { status: 503 },
      );
    }
    memberState.photo = { content_type: "image/png", width: 1, height: 1 };
    return Response.json(memberView());
  }
  if (path === "/api/ai/consultations/state") {
    if (setupExpired === "access")
      return Response.json(
        { error: "Consultation access is invalid or expired." },
        { status: 403 },
      );
    if (setupExpired === "transient")
      return Response.json(
        { error: "Status temporarily unavailable" },
        { status: 503 },
      );
    if (method === "GET" && stateGate) await stateGate;
    if (method === "PATCH" && setupExpired === "preferences")
      return Response.json(
        { error: "Preferences session expired" },
        { status: 410 },
      );
    if (method === "PATCH")
      memberState.preferences = JSON.parse(init.body).preferences;
    if (turnFailure === "expired")
      return Response.json({ error: "Expired" }, { status: 410 });
    return Response.json(memberView());
  }
  if (path.endsWith("/turn")) {
    assert.ok(memberState.photo, "No real turn may precede the photo");
    if (turnGate) await turnGate;
    if (turnFailure !== "uncommitted" && turnFailure !== "expired") {
      memberState.messages.push(
        { role: "user", content: JSON.parse(init.body).message },
        {
          role: "assistant",
          content: memberState.messages.length
            ? "Your recommendations are ready."
            : "What is the occasion?",
        },
      );
      if (memberState.messages.length > 2) {
        memberState.recommendations = { recommendations: rows };
        memberState.stage = "recommended";
        memberState.conversation_status = "ready_for_recommendation";
      }
    }
    if (turnFailure) throw Error("Controlled lost response");
    return Response.json({
      state: memberView(),
      status: memberState.recommendations
        ? "ready_for_recommendation"
        : "more_information",
      recommendations: memberState.recommendations,
    });
  }
  if (path.endsWith("/recommendations")) {
    memberState.recommendations = { recommendations: rows };
    memberState.stage = "recommended";
    return Response.json({ recommendations: rows });
  }
  if (path.endsWith("/generation")) {
    const id = path.split("/").at(-2);
    if (generationGate) await generationGate;
    if (generationMode === "unknown")
      return Response.json({ error: "Uncertain request" }, { status: 503 });
    return Response.json(
      detail(
        id,
        generationMode === "failed" && id === "look-2" ? "failed" : "completed",
      ),
    );
  }
  if (path.endsWith("/select")) {
    memberState.selected_recommendation_id = path.split("/").at(-2);
    return Response.json(memberView());
  }
  if (path === "/api/saved-looks")
    return Response.json({ look: { id: "saved/fixture" } });
  throw Error("Unexpected member request: " + path);
}
function setupMember() {
  memberState = {
    ...state(),
    messages: [],
    recommendations: null,
    stage: "collecting",
    photo: null,
    conversation_status: "not_started",
  };
  memberMode = "gemini";
  photoFailure = false;
  turnFailure = "";
  turnGate = null;
  generationGate = null;
  generationMode = "";
  navigations = [];
  setupExpired = "";
  stateGate = null;
  globalThis.fetch = memberTransport;
  router.push = (path) => navigations.push(path);
}
async function describe(text = "A simple haircut") {
  await waitFor(() =>
    assert.ok(calls.some((call) => call.path.endsWith("/mode"))),
  );
  fireEvent.change(screen.getByLabelText("Your reply"), {
    target: { value: text },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
}
function attach(
  file = new File(["fixture"], "portrait.png", { type: "image/png" }),
) {
  fireEvent.change(screen.getByLabelText("Upload consultation photo"), {
    target: { files: [file] },
  });
}
async function continueChat() {
  const button = screen.getByRole("button", { name: "Continue consultation" });
  await waitFor(() => assert.equal(button.disabled, false));
  fireEvent.click(button);
}
async function memberRecommendations() {
  setupMember();
  mount(false);
  await describe();
  attach();
  await continueChat();
  await screen.findByText("What is the occasion?");
  fireEvent.click(
    screen.getByRole("button", { name: "Graduation", exact: true }),
  );
  assert.equal(
    calls.filter((call) => call.path.endsWith("/turn")).length,
    1,
    "Suggested reply only fills input",
  );
  fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
  await screen.findByRole("region", { name: "Your recommended looks" });
}
test("AC-2 local description clarifies ambiguous services and validates a photo before any API preparation", async () => {
  setupMember();
  mount(false);
  assert.equal(screen.queryByRole("region", { name: "Your recommended looks" }), null);
  assert.equal(screen.queryByLabelText("Upload consultation photo"), null);
  await describe("Something beautiful for graduation");
  assert.ok(screen.getByText(/Which service would you like/));
  assert.equal(calls.filter((call) => call.method !== "GET").length, 0);
  fireEvent.click(screen.getByRole("button", { name: "Nails", exact: true }));
  assert.ok(screen.getByRole("heading", { name: "Add your hand photo" }));
  attach(new File(["invalid"], "photo.gif", { type: "image/gif" }));
  assert.match(screen.getByRole("alert").textContent, /JPG or PNG/);
  attach(
    new File([new Uint8Array(8 * 1024 * 1024 + 1)], "huge.png", {
      type: "image/png",
    }),
  );
  assert.match(screen.getByRole("alert").textContent, /8 MB/);
  assert.equal(
    screen.getByRole("button", { name: "Continue consultation" }).disabled,
    true,
  );
  attach();
  assert.equal(
    document.activeElement,
    screen.getByRole("button", { name: "Continue consultation" }),
  );
  assert.equal(calls.filter((call) => call.method !== "GET").length, 0);
  await continueChat();
  await screen.findByText("What is the occasion?");
  assert.deepEqual(
    calls
      .filter((call) => call.method !== "GET")
      .map((call) => [call.method, call.path]),
    [
      ["POST", "/api/ai/consultations"],
      ["PUT", "/api/ai/consultations/photo"],
      ["POST", "/api/ai/consultations/turn"],
    ],
  );
  assert.equal(
    calls.find((call) => call.path.endsWith("/turn")).body.message,
    "Something beautiful for graduation",
  );
  assert.equal(
    screen.getAllByText("Something beautiful for graduation").length,
    1,
  );
});
test("AC-3 rapid Continue clicks send exactly one retained first message and preserve IME composition", async () => {
  setupMember();
  let settle;
  turnGate = new Promise((resolve) => {
    settle = resolve;
  });
  mount(false);
  await describe();
  attach();
  const button = screen.getByRole("button", { name: "Continue consultation" });
  fireEvent.click(button);
  fireEvent.click(button);
  await waitFor(() =>
    assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1),
  );
  await act(async () => settle());
  await screen.findByText("What is the occasion?");
  const input = screen.getByLabelText("Your reply");
  fireEvent.change(input, { target: { value: "Graduation" } });
  fireEvent.keyDown(input, { key: "Enter", isComposing: true });
  fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1);
  fireEvent.keyDown(input, { key: "Enter" });
  await screen.findByRole("region", { name: "Your recommended looks" });
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 2);
  assert.equal(screen.queryByLabelText("Your reply"), null);
});
test("AC-5 failed photo setup reuses its handle and retains the description on explicit Continue", async () => {
  setupMember();
  photoFailure = true;
  mount(false);
  await describe();
  attach();
  await continueChat();
  await screen.findByText("Photo upload interrupted");
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 0);
  fireEvent.click(
    screen.getByRole("button", { name: "Continue consultation" }),
  );
  await screen.findByText("What is the occasion?");
  assert.equal(
    calls.filter((call) => call.path === "/api/ai/consultations").length,
    1,
  );
  assert.equal(calls.filter((call) => call.path.endsWith("/photo")).length, 2);
  assert.equal(
    calls.find((call) => call.path.endsWith("/turn")).body.message,
    "A simple haircut",
  );
});
test("AC-5 a committed turn with a lost response is recovered by GET without resubmission", async () => {
  setupMember();
  turnFailure = "committed";
  mount(false);
  await describe();
  attach();
  await continueChat();
  await screen.findByText("What is the occasion?");
  await waitFor(() =>
    assert.equal(
      screen.queryByRole("button", { name: "Check conversation status" }),
      null,
    ),
  );
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1);
  assert.equal(
    calls.filter(
      (call) => call.path.endsWith("/state") && call.method === "GET",
    ).length,
    1,
  );
  assert.equal(screen.getAllByText("A simple haircut").length, 1);
});
test("AC-5 AC-6 an unconfirmed turn survives route departure and only status reads can reconcile it", async () => {
  setupMember();
  turnFailure = "uncommitted";
  const store = new GenerationStore("member-fixture", {
    storage: window.localStorage,
    assets: {
      read: async () => null,
      write: async () => {},
      remove: async () => {},
    },
  });
  let view = mount(false, store);
  await describe();
  attach();
  await continueChat();
  await screen.findByText(/Your message has not been confirmed/);
  assert.equal(screen.queryByLabelText("Your reply"), null);
  view.unmount();
  view = mount(false, store);
  const check = await screen.findByRole("button", {
    name: "Check conversation status",
  });
  fireEvent.click(check);
  await waitFor(() => assert.equal(check.disabled, false));
  assert.equal(screen.getAllByText("A simple haircut").length, 1);
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1);
  assert.equal(
    calls.filter((call) => call.path === "/api/ai/consultations").length,
    1,
  );
  assert.equal(
    screen.queryByRole("button", { name: "Generate My Looks" }),
    null,
  );
});
test("AC-5 expired preparation has an explicit fresh start and no automatic replacement session", async () => {
  setupMember();
  turnFailure = "expired";
  mount(false);
  await describe();
  attach();
  await continueChat();
  const restart = await screen.findByRole("button", {
    name: "Start a new consultation",
  });
  assert.equal(
    calls.filter((call) => call.path === "/api/ai/consultations").length,
    1,
  );
  fireEvent.click(restart);
  assert.ok(screen.getByLabelText("Your reply"));
  assert.equal(
    calls.filter((call) => call.path === "/api/ai/consultations").length,
    1,
  );
});
test("AC-4 member generation is sequential and choosing a preview does not generate or book it", async () => {
  await memberRecommendations();
  const log = screen.getByRole("log", { name: "Consultation conversation" });
  assert.ok(within(log).getByRole("region", { name: "Your recommended looks" }));
  assert.equal(document.querySelectorAll(".cc-body > .cc-details").length, 0);
  fireEvent.click(screen.getByRole("button", { name: "View look 2: Bob" }));
  assert.equal(
    calls.filter((call) => call.path.endsWith("/generation")).length,
    0,
  );
  let settle;
  generationGate = new Promise((resolve) => {
    settle = resolve;
  });
  const button = screen.getByRole("button", { name: "Generate My Looks" });
  fireEvent.click(button);
  fireEvent.click(button);
  await waitFor(() =>
    assert.equal(
      calls.filter((call) => call.path.endsWith("/generation")).length,
      1,
    ),
  );
  await act(async () => settle());
  await waitFor(() =>
    assert.equal(
      calls.filter((call) => call.path.endsWith("/generation")).length,
      3,
    ),
  );
  await screen.findByRole("link", { name: "Download" });
  assert.deepEqual(
    calls
      .filter((call) => call.path.endsWith("/generation"))
      .map((call) => call.path.split("/").at(-2)),
    ["look-1", "look-2", "look-3"],
  );
  fireEvent.click(screen.getByRole("button", { name: "Select This Look" }));
  const book = await screen.findByRole("button", {
    name: "Book Selected Look",
  });
  assert.equal(navigations.length, 0);
  assert.ok(log.contains(book));
  assert.ok(within(log).getByRole("button", { name: "Save Look", exact: true }));
  assert.ok(within(log).getByRole("link", { name: "Download", exact: true }));
  fireEvent.click(book);
  await waitFor(() =>
    assert.deepEqual(navigations, ["/booking?look=saved%2Ffixture"]),
  );
  const saves = calls.filter((call) => call.path === "/api/saved-looks");
  assert.equal(saves.length, 1);
  assert.equal(saves[0].body.sourceKind, "consultation");
  assert.equal(saves[0].body.styleId, "bob_hair");
  assert.equal(
    calls.some((call) => call.path.includes("appointments")),
    false,
  );
  assert.ok(screen.getByRole("link", { name: /Custom Hairstyle/ }));
});
test("AC-5 unknown member generation offers GET status and never submits remaining siblings automatically", async () => {
  await memberRecommendations();
  generationMode = "unknown";
  fireEvent.click(screen.getByRole("button", { name: "Generate My Looks" }));
  const check = await screen.findByRole("button", { name: "Check status" });
  assert.equal(
    screen.queryByRole("button", { name: "Continue remaining looks" }),
    null,
  );
  generationMode = "";
  fireEvent.click(check);
  await screen.findByRole("link", { name: "Download" });
  assert.equal(
    calls.filter(
      (call) => call.path.endsWith("/generation") && call.method === "POST",
    ).length,
    1,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Continue remaining looks" }),
  );
  await waitFor(() =>
    assert.equal(
      calls.filter(
        (call) => call.path.endsWith("/generation") && call.method === "POST",
      ).length,
      3,
    ),
  );
});
test("AC-8 structured mode preserves every preference and can clear optional notes", async () => {
  setupMember();
  memberMode = "deterministic";
  mount(false);
  await describe("A low maintenance haircut");
  attach();
  fireEvent.change(screen.getByLabelText("Occasion or event"), {
    target: { value: "Graduation" },
  });
  fireEvent.change(screen.getByLabelText("Desired vibe"), {
    target: { value: "Classic" },
  });
  fireEvent.change(screen.getByLabelText("Maintenance preference"), {
    target: { value: "low" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add optional details" }));
  assert.equal(
    screen.getByLabelText("Optional notes").value,
    "A low maintenance haircut",
  );
  fireEvent.change(screen.getByLabelText("Optional notes"), {
    target: { value: "" },
  });
  fireEvent.change(screen.getByLabelText(/Anything to avoid/), {
    target: { value: "bleach, high upkeep" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Find my looks" }));
  await screen.findByRole("region", { name: "Your recommended looks" });
  assert.deepEqual(
    calls.find((call) => call.method === "PATCH").body.preferences,
    {
      occasion: "Graduation",
      vibe: "Classic",
      hair_maintenance: "low",
      avoids: ["bleach", "high upkeep"],
    },
  );
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 0);
});
test("AC-2 service inference leaves mixed or missing categories for explicit choice", () => {
  assert.equal(inferConsultationService("A soft makeup look"), "makeup");
  assert.equal(inferConsultationService("French tip manicure"), "nails");
  assert.equal(inferConsultationService("A bob haircut"), "hairstyle");
  assert.equal(inferConsultationService("Hair and makeup"), null);
  assert.equal(inferConsultationService("Graduation"), null);
  assert.equal(
    consultationTurnRecorded([{ role: "user", content: "Everyday" }], {
      text: "Everyday",
      userCount: 1,
    }),
    false,
  );
});

test("AC-6 cold refresh keeps completed previews safe while their result is still loading", async () => {
  setupMember();
  memberState.recommendations = { recommendations: rows };
  memberState.generations = rows.map((row) => detail(row.id).generation);
  let settle;
  generationGate = new Promise((resolve) => {
    settle = resolve;
  });
  const store = new GenerationStore("cold-fixture", {
    storage: window.localStorage,
    assets: {
      read: async () => null,
      write: async () => {},
      remove: async () => {},
    },
  });
  store.setConsultation("consultationId", "member-handle", "");
  mount(false, store);
  await screen.findByText("Recovering this preview…");
  assert.equal(screen.queryByRole("link", { name: "Download" }), null);
  assert.equal(
    screen.queryByRole("button", { name: "Select This Look" }),
    null,
  );
  await act(async () => settle());
  await screen.findByRole("link", { name: "Download" });
  assert.equal(calls.filter((call) => call.method !== "GET").length, 0);
});

test("AC-2 inferred service can be corrected without losing the original direction and photo controls collapse truthfully", async () => {
  setupMember();
  mount(false);
  await describe("A soft glam look");
  assert.equal(
    screen
      .getByRole("button", { name: "Makeup", exact: true })
      .getAttribute("aria-pressed"),
    "true",
  );
  fireEvent.click(screen.getByRole("button", { name: "Nails", exact: true }));
  assert.ok(screen.getByRole("heading", { name: "Add your hand photo" }));
  const toggle = screen.getByRole("button", {
    name: "Your photo",
    exact: true,
  });
  fireEvent.click(toggle);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(screen.queryByLabelText("Upload consultation photo"), null);
  fireEvent.click(toggle);
  attach();
  await continueChat();
  await screen.findByText("What is the occasion?");
  assert.equal(
    calls.find((call) => call.path === "/api/ai/consultations").body
      .primary_service,
    "nails",
  );
  assert.equal(
    calls.find((call) => call.path.endsWith("/turn")).body.message,
    "A soft glam look",
  );
});
test("AC-6 hard refresh restores a pending turn even if IndexedDB has lost the entire draft", async () => {
  setupMember();
  turnFailure = "uncommitted";
  const dependencies = {
    storage: window.localStorage,
    assets: {
      read: async () => null,
      write: async () => {},
      remove: async () => {},
    },
  };
  let view = mount(false, new GenerationStore("refresh-fixture", dependencies));
  await describe();
  attach();
  await continueChat();
  await screen.findByText(/Your message has not been confirmed/);
  view.unmount();
  const fresh = new GenerationStore("refresh-fixture", dependencies);
  fresh.setConsultation("consultationId", "member-handle", "");
  view = mount(false, fresh);
  await screen.findByRole("button", { name: "Check conversation status" });
  await waitFor(() =>
    assert.equal(screen.queryByText("Restoring your consultation…"), null),
  );
  assert.equal(screen.queryByLabelText("Your reply"), null);
  assert.equal(screen.getAllByText("A simple haircut").length, 1);
  assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1);
});
test("AC-6 guest refresh preserves a pending turn and an interrupted photo preparation", async () => {
  for (const failure of ["uncommitted", "photo"]) {
    setupMember();
    sessionStorage.clear();
    calls = [];
    provider = "gemini";
    hasConsultation = false;
    const issued = Date.now(),
      firstHandle = await guestHandle(issued),
      renewedHandle = await guestHandle(issued + 2000);
    assert.notEqual(firstHandle, renewedHandle);
    let currentHandle = firstHandle;
    if (failure === "photo") photoFailure = true;
    else turnFailure = failure;
    globalThis.fetch = async (input, init = {}) => {
      if (String(input) === "/api/ai-trial/session")
        return Response.json({
          ...session(),
          handle: hasConsultation ? currentHandle : null,
        });
      if (String(input) === "/api/ai-trial/consultations") {
        hasConsultation = true;
        const response = await memberTransport("/api/ai/consultations", init);
        return Response.json({
          ...(await response.json()),
          handle: firstHandle,
        });
      }
      return memberTransport(
        String(input).replace("/api/ai-trial/", "/api/ai/"),
        init,
      );
    };
    let view = mount();
    await describe();
    attach();
    await continueChat();
    await screen.findByText(
      failure === "photo"
        ? "Photo upload interrupted"
        : /Your message has not been confirmed/,
    );
    view.unmount();
    currentHandle = renewedHandle;
    view = mount();
    await waitFor(() =>
      assert.ok(
        calls.filter((call) => call.path.endsWith("/mode")).length >= 2,
      ),
    );
    if (failure === "photo") {
      assert.ok(screen.getByText("A simple haircut"));
      fireEvent.click(
        screen.getByRole("button", { name: "Your photo", exact: true }),
      );
      attach();
      await continueChat();
      await screen.findByText("What is the occasion?");
      assert.equal(
        calls.filter((call) => call.path === "/api/ai/consultations").length,
        1,
      );
    } else {
      assert.ok(
        screen.getByRole("button", { name: "Check conversation status" }),
      );
      assert.equal(screen.queryByLabelText("Your reply"), null);
      fireEvent.click(
        screen.getByRole("button", { name: "Check conversation status" }),
      );
      await waitFor(() => assert.equal(calls.at(-1).handle, renewedHandle));
    }
    assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1);
    view.unmount();
  }
});
test("AC-5 storage failure prevents a turn POST rather than losing the recovery barrier", async () => {
  setupMember();
  mount(false);
  await describe();
  attach();
  const storage = globalThis.sessionStorage;
  try {
    globalThis.sessionStorage = {
      getItem: () => null,
      setItem: () => {
        throw Error("Storage blocked");
      },
    };
    await continueChat();
    await screen.findByText(/Allow session storage/);
    assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 0);
  } finally {
    globalThis.sessionStorage = storage;
  }
  await continueChat();
  await screen.findByText("What is the occasion?");
  assert.equal(
    calls.filter((call) => call.path === "/api/ai/consultations").length,
    1,
  );
});
test("AC-5 expired photo and deterministic preference preparation offer explicit restart", async () => {
  for (const failure of ["photo", "preferences"]) {
    setupMember();
    setupExpired = failure;
    memberMode = failure === "preferences" ? "deterministic" : "gemini";
    const view = mount(false);
    await describe();
    attach();
    if (failure === "photo") await continueChat();
    else fireEvent.click(screen.getByRole("button", { name: "Find my looks" }));
    await screen.findByRole("button", { name: "Start a new consultation" });
    assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 0);
    view.unmount();
    calls = [];
    sessionStorage.clear();
  }
});
test("AC-6 a delayed restoration locks reply and generation controls until the canonical state is loaded", async () => {
  setupMember();
  let settle;
  stateGate = new Promise((resolve) => {
    settle = resolve;
  });
  const store = new GenerationStore("delayed-fixture", {
    storage: window.localStorage,
    assets: {
      read: async () => null,
      write: async () => {},
      remove: async () => {},
    },
  });
  store.setConsultation("consultationId", "member-handle", "");
  store.setConsultation("photoUploaded", true, false);
  store.setConsultation(
    "chatMessages",
    [{ role: "assistant", content: "Cached question" }],
    [],
  );
  store.setConsultation("providerMode", "gemini", "loading");
  mount(false, store);
  await screen.findByText("Restoring your consultation…");
  assert.equal(screen.queryByRole("button", { name: "Send reply" }), null);
  assert.equal(calls.filter((call) => call.method !== "GET").length, 0);
  await act(async () => settle());
  await waitFor(() =>
    assert.equal(screen.queryByText("Restoring your consultation…"), null),
  );
  assert.equal(screen.queryByText("Cached question"), null);
});

test("AC-6 renewed guest handles match only the same issuer, purpose, owner and consultation", async () => {
  const now = Date.now(),
    handle = await guestHandle(now);
  writeConsultationPreparation("guest", {
    handle,
    initialIntent: "A haircut",
    pendingTurn: { text: "A haircut", userCount: 0 },
  });
  assert.ok(
    readConsultationPreparation("guest", await guestHandle(now + 2000))
      ?.pendingTurn,
  );
  assert.equal(
    readConsultationPreparation(
      "guest",
      await guestHandle(now + 2000, "other-guest"),
    ),
    null,
  );
  assert.equal(
    readConsultationPreparation(
      "guest",
      await guestHandle(
        now + 2000,
        "guest-fixture",
        "22222222-2222-4222-8222-222222222222",
      ),
    ),
    null,
  );
  assert.equal(
    readConsultationPreparation(
      "guest",
      await guestHandle(
        now + 2000,
        "guest-fixture",
        "11111111-1111-4111-8111-111111111111",
        "beautycore-client-consultation",
      ),
    ),
    null,
  );
});
test("AC-6 account clear after route departure erases the journal and rejects late writes from that account lifetime", async () => {
  setupMember();
  let settle;
  turnGate = new Promise((resolve) => {
    settle = resolve;
  });
  const store = new GenerationStore("departed-account", {
    storage: window.localStorage,
    assets: {
      read: async () => null,
      write: async () => {},
      remove: async () => {},
    },
  });
  const view = mount(false, store);
  await describe();
  attach();
  await continueChat();
  await waitFor(() =>
    assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 1),
  );
  assert.ok(readConsultationPreparation("departed-account", "member-handle"));
  const oldEpoch = consultationPreparationEpoch("departed-account");
  view.unmount();
  store.stop();
  clearGenerationDrafts("departed-account");
  assert.equal(
    readConsultationPreparation("departed-account", "member-handle"),
    null,
  );
  await act(async () => settle());
  assert.equal(
    readConsultationPreparation("departed-account", "member-handle"),
    null,
  );
  assert.equal(
    writeConsultationPreparation(
      "departed-account",
      {
        handle: "member-handle",
        initialIntent: "Private old draft",
        pendingTurn: null,
      },
      oldEpoch,
    ),
    false,
  );
});
test("AC-5 real adapter expired-access response offers restart on preparation and restoration", async () => {
  assert.equal(
    expiredConsultationAccess({
      status: 403,
      message: "Other permission failure",
    }),
    false,
  );
  for (const existing of [false, true]) {
    setupMember();
    setupExpired = "access";
    let store = null;
    if (existing) {
      store = new GenerationStore("expired-member", {
        storage: window.localStorage,
        assets: {
          read: async () => null,
          write: async () => {},
          remove: async () => {},
        },
      });
      store.setConsultation("consultationId", "member-handle", "");
    }
    const view = mount(false, store);
    if (!existing) {
      await describe();
      attach();
      await continueChat();
    }
    await screen.findByRole("button", { name: "Start a new consultation" });
    assert.equal(calls.filter((call) => call.path.endsWith("/turn")).length, 0);
    view.unmount();
    calls = [];
    sessionStorage.clear();
  }
});
test("AC-6 guest pending status can be checked even when the first restoration GET fails", async () => {
  setupMember();
  setupExpired = "transient";
  hasConsultation = true;
  writeConsultationPreparation("guest", {
    handle: "guest-handle",
    initialIntent: "A haircut",
    pendingTurn: { text: "A haircut", userCount: 0 },
  });
  globalThis.fetch = async (input, init = {}) =>
    String(input) === "/api/ai-trial/session"
      ? Response.json(session())
      : memberTransport(
          String(input).replace("/api/ai-trial/", "/api/ai/"),
          init,
        );
  mount();
  await screen.findByText(/Your temporary consultation is unavailable/);
  setupExpired = "";
  fireEvent.click(
    screen.getByRole("button", { name: "Check conversation status" }),
  );
  await screen.findByText(/Your message has not been confirmed/);
  assert.equal(calls.at(-1).handle, "guest-handle");
  assert.equal(calls.filter((call) => call.method !== "GET").length, 0);
});
test("AC-8 guided guest preparation restores its direction after an interrupted photo upload", async () => {
  setupMember();
  memberMode = "deterministic";
  photoFailure = true;
  hasConsultation = false;
  globalThis.fetch = async (input, init = {}) => {
    if (String(input) === "/api/ai-trial/session")
      return Response.json({
        ...session(),
        handle: hasConsultation ? "member-handle" : null,
      });
    if (String(input) === "/api/ai-trial/consultations") hasConsultation = true;
    return memberTransport(
      String(input).replace("/api/ai-trial/", "/api/ai/"),
      init,
    );
  };
  let view = mount();
  await describe("An easy haircut");
  attach();
  fireEvent.click(screen.getByRole("button", { name: "Find my looks" }));
  await screen.findByText("Photo upload interrupted");
  view.unmount();
  view = mount();
  await screen.findByText("An easy haircut");
  fireEvent.click(
    screen.getByRole("button", { name: "Your photo", exact: true }),
  );
  attach();
  fireEvent.click(screen.getByRole("button", { name: "Add optional details" }));
  assert.equal(
    screen.getByLabelText("Optional notes").value,
    "An easy haircut",
  );
  const find = screen.getByRole("button", { name: "Find my looks" });
  await waitFor(() => assert.equal(find.disabled, false));
  fireEvent.click(find);
  await screen.findByRole("region", { name: "Your recommended looks" });
  assert.equal(
    calls.find((call) => call.method === "PATCH").body.preferences.notes,
    "An easy haircut",
  );
  assert.equal(
    calls.filter((call) => call.path === "/api/ai/consultations").length,
    1,
  );
});

test("AC-6 central logout cleanup removes a preparation journal without a consultation event listener", () => {
  const key = "beautycore:consultation-preparation:v1:cold-dashboard";
  sessionStorage.setItem(
    key,
    JSON.stringify({
      handle: "old-handle",
      initialIntent: "Private direction",
      pendingTurn: null,
    }),
  );
  const dispatch = window.dispatchEvent;
  try {
    window.dispatchEvent = () => true;
    clearGenerationDrafts("cold-dashboard");
    assert.equal(sessionStorage.getItem(key), null);
  } finally {
    window.dispatchEvent = dispatch;
  }
});
test("AC-8 a deliberately cleared member note stays empty after failed preparation and route return", async () => {
  setupMember();
  memberMode = "deterministic";
  photoFailure = true;
  const store = new GenerationStore("empty-notes", {
    storage: window.localStorage,
    assets: {
      read: async () => null,
      write: async () => {},
      remove: async () => {},
    },
  });
  let view = mount(false, store);
  await describe("An easy haircut");
  attach();
  fireEvent.click(screen.getByRole("button", { name: "Add optional details" }));
  fireEvent.change(screen.getByLabelText("Optional notes"), {
    target: { value: "" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Find my looks" }));
  await screen.findByText("Photo upload interrupted");
  view.unmount();
  view = mount(false, store);
  await waitFor(() =>
    assert.equal(!!screen.queryByText("Restoring your consultation…"), false),
  );
  assert.equal(screen.getByLabelText("Optional notes").value, "");
});
