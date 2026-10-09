import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
const makeStorage = () => {
  const values = new Map<string, string>();
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
  };
};
const identity = (token: string) => ({
  workspace_id: token,
  token,
  email: `${token}@example.com`,
  kind: "account" as const,
});
const deferredResponse = () => {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => {
    resolve = done;
  });
  return { promise, resolve };
};
beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("VITE_API_URL", "https://api.example.test");
  vi.stubGlobal("sessionStorage", makeStorage());
  vi.stubGlobal("localStorage", makeStorage());
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
describe("session transitions", () => {
  it("a late unauthorized old request cannot clear the current session", async () => {
    const auth = await import("@/lib/api/auth");
    const deferred = deferredResponse();
    vi.stubGlobal(
      "fetch",
      vi.fn(() => deferred.promise),
    );
    auth.setSession(identity("old"));
    const request = auth.request("/api/status").catch((error) => error);
    auth.setSession(identity("new"));
    deferred.resolve(
      Response.json({ detail: "Session expired" }, { status: 401 }),
    );
    expect(await request).toBeInstanceOf(auth.ApiError);
    expect(auth.getSession()?.token).toBe("new");
  });
  it("a late old logout does not clear a new successful login", async () => {
    const auth = await import("@/lib/api/auth");
    const deferred = deferredResponse();
    vi.stubGlobal(
      "fetch",
      vi.fn(() => deferred.promise),
    );
    auth.setSession(identity("old"));
    const logout = auth.revokeSession();
    auth.setSession(identity("new"));
    deferred.resolve(Response.json({ ok: true }));
    await logout;
    expect(auth.getSession()?.token).toBe("new");
  });
  it("the most recent authentication attempt owns the resulting session", async () => {
    const auth = await import("@/lib/api/auth");
    const first = deferredResponse();
    const second = deferredResponse();
    const fetchMock = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    vi.stubGlobal("fetch", fetchMock);
    const oldLogin = auth.authenticate("login", {
      email: "old@example.com",
      password: "a-long-test-password",
    });
    const newDemo = auth.authenticate("demo", {
      email: "ignored@example.com",
      password: "never-send-this",
    });
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({});
    second.resolve(Response.json(identity("new")));
    await newDemo;
    first.resolve(Response.json(identity("old")));
    await oldLogin;
    expect(auth.getSession()?.token).toBe("new");
  });
});
