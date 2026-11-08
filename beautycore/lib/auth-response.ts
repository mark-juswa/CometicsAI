import type { AuthUser } from "../context/AuthContext";

/** Never expose framework HTML pages or JSON parser exceptions in account forms. */
export async function readAuthResponse(
  response: Response,
  fallback: string,
): Promise<Record<string, unknown>> {
  const unavailable =
    "The account service is unavailable. Refresh the page and try again.";
  if (
    !response.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  )
    throw new Error(unavailable);
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error(unavailable);
  }
  if (!data || typeof data !== "object" || Array.isArray(data))
    throw new Error(unavailable);
  const body = data as Record<string, unknown>;
  if (!response.ok)
    throw new Error(
      typeof body.error === "string" && body.error ? body.error : fallback,
    );
  return body;
}

export function authUserFromResponse(value: unknown): AuthUser {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error(
      "Your account response was incomplete. Refresh the page and try again.",
    );
  const user = value as Record<string, unknown>;
  if (
    typeof user.id !== "string" ||
    !user.id ||
    typeof user.name !== "string" ||
    typeof user.email !== "string" ||
    typeof user.role !== "string" ||
    !["admin", "stylist", "client"].includes(user.role) ||
    (user.avatar != null && typeof user.avatar !== "string")
  )
    throw new Error(
      "Your account response was incomplete. Refresh the page and try again.",
    );
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role as AuthUser["role"],
    avatar: (user.avatar as string | null) ?? null,
  };
}
