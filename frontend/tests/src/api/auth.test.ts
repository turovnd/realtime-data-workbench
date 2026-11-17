import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
const makeStorage = () => {
  const storage = Object.create(null) as Storage;
  const values = new Map<string, string>();
  Object.defineProperties(storage, {
    getItem: { value: (key: string) => values.get(key) ?? null },
    setItem: {
      value: (key: string, value: string) => {
        values.set(key, value);
        Object.defineProperty(storage, key, {
          value,
          configurable: true,
          enumerable: true,
        });
      },
    },
    removeItem: {
      value: (key: string) => {
        values.delete(key);
        Reflect.deleteProperty(storage, key);
      },
    },
  });
  return storage;
};
const identity = (token: string) => ({
  workspace_id: token,
  token,
  email: `${token}@example.com`,
  kind: "account" as const,
});
const deferredResponse = () => {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>(done => {
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
    const auth = await import("@/api/auth");
    const deferred = deferredResponse();
    const fetchMock = vi.fn(() => deferred.promise);
    vi.stubGlobal("fetch", fetchMock);
    auth.setSession(identity("old"));
    const request = auth.api.api.getFeedbackStatus().catch(error => error);
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    auth.setSession(identity("new"));
    deferred.resolve(
      Response.json({ detail: "Session expired" }, { status: 401 })
    );
    expect(await request).toBeInstanceOf(auth.ApiError);
    expect(auth.getSession()?.token).toBe("new");
  });
  it("a late old logout does not clear a new successful login", async () => {
    const auth = await import("@/api/auth");
    const deferred = deferredResponse();
    const fetchMock = vi.fn(() => deferred.promise);
    vi.stubGlobal("fetch", fetchMock);
    auth.setSession(identity("old"));
    const logout = auth.revokeSession();
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    auth.setSession(identity("new"));
    deferred.resolve(Response.json({ ok: true }));
    await logout;
    expect(auth.getSession()?.token).toBe("new");
  });
  it("the most recent authentication attempt owns the resulting session", async () => {
    const auth = await import("@/api/auth");
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
  it("logout revokes the bearer and clears private snapshots without removing unrelated preferences", async () => {
    const auth = await import("@/api/auth");
    const fetchMock = vi.fn().mockResolvedValue(Response.json({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    auth.setSession(identity("current"));
    localStorage.setItem("feedback-desk-offline:current", "private snapshot");
    localStorage.setItem("signal-desk-offline-v1", "old private snapshot");
    localStorage.setItem("display-preference", "compact");
    sessionStorage.setItem("feedback-desk-preview:current", "private preview");

    await auth.revokeSession();

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.test/api/auth/logout",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ Authorization: "Bearer current" }),
      })
    );
    expect(auth.getSession()).toBeNull();
    expect(Object.keys(sessionStorage)).toEqual([]);
    expect(localStorage.getItem("feedback-desk-offline:current")).toBeNull();
    expect(localStorage.getItem("signal-desk-offline-v1")).toBeNull();
    expect(localStorage.getItem("display-preference")).toBe("compact");
  });

  it("account authentication does not forward a previous workspace bearer", async () => {
    const auth = await import("@/api/auth");
    auth.setSession(identity("previous"));
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json(identity("next")));
    vi.stubGlobal("fetch", fetchMock);

    await auth.authenticate("login", {
      email: "next@example.test",
      password: "a-long-test-password",
    });

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("https://api.example.test/api/auth/login");
    expect(options.headers).not.toHaveProperty("Authorization");
    expect(auth.getSession()?.workspace_id).toBe("next");
  });
});

describe("request recovery", () => {
  it("preserves JSON API detail and status without recommending a page reload", async () => {
    const auth = await import("@/api/auth");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            { detail: "Activity is temporarily unavailable" },
            { status: 503 }
          )
        )
    );

    const error = await auth.api.api
      .listActivity({ limit: 10 })
      .catch(error => error);

    expect(error).toBeInstanceOf(auth.ApiError);
    expect(error.message).toBe("Activity is temporarily unavailable");
    expect(error.status).toBe(503);
    expect(error.recovery).toBe("retry");
  });

  it("recognizes an explicit platform challenge without clearing the signed-in session", async () => {
    const auth = await import("@/api/auth");
    auth.setSession(identity("current"));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("<html>private challenge response</html>", {
          status: 401,
          headers: {
            "content-type": "text/html",
            "x-vercel-mitigated": "challenge",
          },
        })
      )
    );

    const error = await auth.api.api.getFeedbackStatus().catch(error => error);

    expect(error.message).toBe(
      "A browser security check is required. Reload the page to continue."
    );
    expect(error.message).not.toContain("private challenge response");
    expect(error.status).toBe(401);
    expect(error.recovery).toBe("reload");
    expect(auth.getSession()?.token).toBe("current");
  });

  it.each([200, 429])(
    "treats an HTML %s response as unexpected without inventing a challenge",
    async status => {
      const auth = await import("@/api/auth");
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(
          new Response("<html>private upstream page</html>", {
            status,
            headers: { "content-type": "text/html; charset=utf-8" },
          })
        )
      );

      const error = await auth.api.api
        .listActivity({ limit: 10 })
        .catch(error => error);

      expect(error.message).toBe(
        "The service returned an unexpected response. Try again or reload the page."
      );
      expect(error.message).not.toMatch(/security|private upstream page/);
      expect(error.status).toBe(status);
      expect(error.recovery).toBe("reload");
    }
  );
});
