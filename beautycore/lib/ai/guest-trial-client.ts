export type GuestTrialStatus = {
  state: "available" | "reserved" | "spent";
  expires_at: string;
  handle: string | null;
  recommendation_id: string | null;
  result_temporary: boolean;
  preparation_locked: boolean;
};
export async function readTrialSession(
  method: "GET" | "POST" = "GET",
): Promise<GuestTrialStatus> {
  const response = await fetch("/api/ai-trial/session", {
    method,
    cache: "no-store",
  });
  const value = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(
      typeof value?.error === "string"
        ? value.error
        : "Guest trial is unavailable.",
    );
  if (
    !value ||
    !["available", "reserved", "spent"].includes(value.state) ||
    typeof value.expires_at !== "string" ||
    (value.handle !== null && typeof value.handle !== "string") ||
    (value.recommendation_id !== null &&
      typeof value.recommendation_id !== "string")
  )
    throw new Error(
      "Guest trial status could not be read. No new generation was sent.",
    );
  return value;
}
