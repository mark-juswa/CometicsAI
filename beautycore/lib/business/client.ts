import type { LookDetails } from "./look-information";
import type { FeatureId, GeneratedResult } from "../ai/browser-client";
import { prepareSavedLookImage } from "./saved-look-image";
export type SavedLook = {
  id: string;
  styleType: "hair" | "nail" | "makeup";
  styleId: string;
  styleName: string;
  lookDetails?: LookDetails | null;
  imageUrl: string;
  savedAt: string;
  createdAt: string;
};
export class PortalRequestError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function businessRequest(path: string, init: RequestInit = {}) {
  let response: Response;
  try {
    response = await fetch(path, { ...init, cache: "no-store" });
  } catch (cause) {
    if (cause instanceof Error && cause.name === "AbortError") throw cause;
    throw new PortalRequestError(
      "The connection was interrupted. Please try again.",
      0,
    );
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new PortalRequestError(
      response.status === 413
        ? "This image is too large to save. Download it and choose a smaller image."
        : "The server returned an unexpected response. Please try again.",
      response.ok ? 502 : response.status,
    );
  }
  if (!response.ok)
    throw new PortalRequestError(
      typeof data?.error === "string"
        ? data.error
        : "The request could not be completed.",
      response.status,
    );
  return data;
}
export async function saveLook(
  feature: FeatureId,
  result: GeneratedResult,
  sourceKind: "manual" | "consultation",
): Promise<SavedLook> {
  const image = await prepareSavedLookImage(result.image.data_url);
  const init: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      feature,
      styleId: result.style.id,
      image,
      status: result.status,
      sourceKind,
    }),
  };
  for (let attempt = 0; ; attempt++) {
    try {
      const data = await businessRequest("/api/saved-looks", init);
      if (typeof data?.look?.id !== "string" || !data.look.id)
        throw new PortalRequestError(
          "The saved look could not be read. Please try again.",
          502,
        );
      return data.look;
    } catch (cause) {
      // Save admission is idempotent by owner/style/image hash. Never retry generation.
      if (
        attempt >= 2 ||
        !(cause instanceof PortalRequestError) ||
        ![0, 429, 500, 502, 503, 504].includes(cause.status) ||
        /not enabled|not configured/i.test(cause.message)
      )
        throw cause;
      await new Promise((resolve) =>
        setTimeout(resolve, attempt === 0 ? 300 : 900),
      );
    }
  }
}
export function savedGroup(type: string) {
  return type === "hair"
    ? "hair-design"
    : type === "nail"
      ? "nail-studio"
      : "makeup";
}
