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
  finishGeneration = null;
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
  assert.ok(screen.getByRole("heading", { name: "Your trial preview." }));
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
