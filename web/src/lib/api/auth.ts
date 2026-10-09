import { z } from "zod";

export const identitySchema = z.object({
  workspace_id: z.string(),
  email: z.string().nullable(),
  kind: z.enum(["account", "demo", "browser-demo"]),
});
export type Identity = z.infer<typeof identitySchema>;
const sessionSchema = identitySchema.extend({ token: z.string() });
export type Session = z.infer<typeof sessionSchema>;
export const baseUrl =
  import.meta.env.VITE_API_URL === "same-origin"
    ? window.location.origin
    : import.meta.env.VITE_API_URL?.replace(/\/$/, "");
const storageKey = `feedback-desk-auth:${baseUrl ?? "preview"}`;
const readSession = (): Session | null => {
  try {
    return sessionSchema.parse(
      JSON.parse(sessionStorage.getItem(storageKey) ?? "null"),
    );
  } catch {
    return null;
  }
};
let session = readSession();
let authAttempt = 0;
const listeners = new Set<() => void>();
export const subscribeAuth = (callback: () => void) => {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
};
export const getSession = () => session;
export const setSession = (next: Session | null) => {
  session = next;
  if (next) sessionStorage.setItem(storageKey, JSON.stringify(next));
  else sessionStorage.removeItem(storageKey);
  listeners.forEach((listener) => listener());
};
export const clearPrivateStorage = () => {
  Object.keys(localStorage)
    .filter(
      (key) =>
        key.startsWith("feedback-desk-offline:") ||
        key === "signal-desk-offline-v1",
    )
    .forEach((key) => localStorage.removeItem(key));
};
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}
export const request = async (
  path: string,
  body?: object,
  signal?: AbortSignal,
  authenticated = true,
): Promise<unknown> => {
  if (!baseUrl)
    throw new ApiError("Connect the API to use account authentication.", 503);
  const token = authenticated ? session?.token : undefined;
  const response = await fetch(`${baseUrl}${path}`, {
    method: body ? "POST" : "GET",
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    signal,
    cache: "no-store",
  });
  if (!response.ok) {
    if (response.status === 401 && token && token === session?.token) {
      setSession(null);
      clearPrivateStorage();
    }
    const payload: unknown = await response.json().catch(() => null);
    const error = z.object({ detail: z.string() }).safeParse(payload);
    throw new ApiError(
      error.success
        ? error.data.detail
        : `Request failed (${response.status}). Try again.`,
      response.status,
    );
  }
  return response.json();
};
export const authenticate = async (
  mode: "demo" | "login" | "register",
  credentials?: { email: string; password: string },
) => {
  const attempt = ++authAttempt;
  if (!baseUrl) {
    if (mode !== "demo")
      throw new Error("Account sign-in needs the connected API.");
    const next = {
      workspace_id: "browser",
      email: null,
      kind: "browser-demo" as const,
      token: "local-preview",
    };
    setSession(next);
    return next;
  }
  const next = sessionSchema.parse(
    await request(
      `/api/auth/${mode}`,
      mode === "demo" ? {} : (credentials ?? {}),
      undefined,
      false,
    ),
  );
  if (attempt === authAttempt) setSession(next);
  return next;
};
export const loadIdentity = async (signal?: AbortSignal): Promise<Identity> => {
  if (!baseUrl && session) return identitySchema.parse(session);
  return identitySchema.parse(await request("/api/auth/me", undefined, signal));
};
export const revokeSession = async () => {
  const token = session?.token;
  try {
    if (baseUrl && session) await request("/api/auth/logout", {});
  } finally {
    if (session?.token === token) {
      setSession(null);
      clearPrivateStorage();
    }
  }
};
