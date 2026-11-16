import type { FeatureId } from "./browser-client";

export type PendingConsultationTurn = { text: string; userCount: number };
export type ConsultationMessage = {
  role: "user" | "assistant";
  content: string;
};
export type ConsultationPreparation = {
  handle: string;
  initialIntent: string;
  pendingTurn: PendingConsultationTurn | null;
};
const preparationKey = (owner: string) =>
  `beautycore:consultation-preparation:v1:${owner}`;
const accountEpochs = new Map<string, number>();
let listeningForAccountClear = false;

/** The listener survives route departure, as do requests owned by the shared store. */
export function consultationPreparationEpoch(owner: string): number {
  if (!listeningForAccountClear && typeof window !== "undefined") {
    window.addEventListener("beautycore-generation-clear", (event) => {
      const clearedOwner = (event as CustomEvent).detail;
      if (typeof clearedOwner !== "string") return;
      accountEpochs.set(
        clearedOwner,
        (accountEpochs.get(clearedOwner) || 0) + 1,
      );
      clearConsultationPreparation(clearedOwner);
    });
    listeningForAccountClear = true;
  }
  return accountEpochs.get(owner) || 0;
}

function samePreparationHandle(previous: string, current: string): boolean {
  if (previous === current) return true;
  // JWT refresh changes iat/signature. This is only local draft matching, never
  // authorization: all requests still use the current server-issued signed handle.
  function identity(handle: string) {
    try {
      const payload = handle.split(".")[1];
      const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
      const value = JSON.parse(
        atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "=")),
      );
      if (
        value.iss !== "beautycore-ai-adapter" ||
        typeof value.aud !== "string" ||
        typeof value.sub !== "string" ||
        typeof value.cid !== "string"
      )
        return null;
      return JSON.stringify([value.iss, value.aud, value.sub, value.cid]);
    } catch {
      return null;
    }
  }
  const expected = identity(current);
  return expected !== null && identity(previous) === expected;
}

export function expiredConsultationAccess(cause: unknown): boolean {
  if (!cause || typeof cause !== "object" || !("status" in cause)) return false;
  return (
    cause.status === 404 ||
    cause.status === 410 ||
    (cause.status === 403 &&
      "message" in cause &&
      cause.message === "Consultation access is invalid or expired.")
  );
}

/** Only a local draft and one pending turn, scoped to this tab, account and signed handle. */
export function readConsultationPreparation(
  owner: string,
  handle: string,
): ConsultationPreparation | null {
  try {
    const value = JSON.parse(
      sessionStorage.getItem(preparationKey(owner)) || "null",
    );
    if (
      !value ||
      typeof value.handle !== "string" ||
      !samePreparationHandle(value.handle, handle) ||
      typeof value.initialIntent !== "string" ||
      value.initialIntent.length > 500
    )
      return null;
    const pending = value.pendingTurn;
    if (
      pending !== null &&
      (!pending ||
        typeof pending.text !== "string" ||
        pending.text.length > 500 ||
        !Number.isInteger(pending.userCount) ||
        pending.userCount < 0)
    )
      return null;
    return { handle, initialIntent: value.initialIntent, pendingTurn: pending };
  } catch {
    return null;
  }
}

/** Synchronous barrier before a turn POST; failed storage must not silently drop its recovery lock. */
export function writeConsultationPreparation(
  owner: string,
  value: ConsultationPreparation,
  epoch = consultationPreparationEpoch(owner),
): boolean {
  if (epoch !== consultationPreparationEpoch(owner)) return false;
  try {
    sessionStorage.setItem(preparationKey(owner), JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}
export function clearConsultationPreparation(owner: string) {
  try {
    sessionStorage.removeItem(preparationKey(owner));
  } catch {
    /* No persistent draft was available. */
  }
}

/** A local routing hint only. Ambiguous requests still require an explicit service. */
export function inferConsultationService(text: string): FeatureId | null {
  const matches: FeatureId[] = [];
  if (/\b(hair|haircut|hairstyle|bob|layers|fringe|bangs)\b/i.test(text))
    matches.push("hairstyle");
  if (/\b(makeup|make.up|lipstick|glam|cosmetic)\b/i.test(text))
    matches.push("makeup");
  if (/\b(nails?|manicure|polish|french tip)\b/i.test(text))
    matches.push("nails");
  return matches.length === 1 ? matches[0] : null;
}

/** Position matters: a repeated earlier answer must not confirm a later lost turn. */
export function consultationTurnRecorded(
  messages: ConsultationMessage[],
  pending: PendingConsultationTurn,
): boolean {
  const users = messages.filter((message) => message.role === "user");
  return users[pending.userCount]?.content === pending.text;
}
