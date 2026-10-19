import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const filters = { q: "invoice", status: "all", topic: "all" } as const;
const pageResult = {
  workspace_id: "workspace-a",
  records: [],
  next_cursor: null,
  refresh_cursor: "opaque-view.head",
  watermark: 24,
  revision: 3,
  total: 0,
};

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("VITE_API_URL", "https://api.example.test");
  vi.stubGlobal("sessionStorage", {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
  });
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("generated HTTP client boundary", () => {
  it("omits an initial cursor, carries the bounded limit and passes an opaque continuation unchanged", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() => Promise.resolve(Response.json(pageResult)));
    vi.stubGlobal("fetch", fetchMock);
    const { setSession } = await import("@/api/auth");
    const { createHttpAdapter } = await import("@/api/client");
    setSession({
      workspace_id: "workspace-a",
      token: "test-bearer",
      email: null,
      kind: "demo",
    });
    const adapter = createHttpAdapter();
    const abort = new AbortController();
    await adapter.page(filters, null, 12, abort.signal);
    const first = new URL(fetchMock.mock.calls[0][0]);
    expect(first.pathname).toBe("/api/feedback");
    expect(first.searchParams.get("q")).toBe("invoice");
    expect(first.searchParams.get("limit")).toBe("12");
    expect(first.searchParams.has("cursor")).toBe(false);
    expect(
      new Headers(fetchMock.mock.calls[0][1].headers).get("Authorization")
    ).toBe("Bearer test-bearer");
    expect(fetchMock.mock.calls[0][1].signal).toBe(abort.signal);

    const cursor = "opaque-view.+/=:next";
    await adapter.page(filters, cursor, 12);
    const next = new URL(fetchMock.mock.calls[1][0]);
    expect(next.searchParams.get("cursor")).toBe(cursor);
    expect(next.searchParams.get("limit")).toBe("12");
  });

  it("admits a fresh analysis after an existing second result and retains its run and provider", async () => {
    const record = {
      id: "00000000-0000-4000-8000-000000000001",
      sequence: 1,
      text: "The monthly export freezes.",
      channel: "Support",
      ingested_at: "2026-10-01T09:00:00Z",
      jobs: Array.from({ length: 3 }, (_, index) => ({
        id: `job-${index + 1}`,
        run: index + 1,
        config: index === 0 ? "v1" : "v2",
        status: index === 2 ? "queued" : "succeeded",
        attempts: index === 2 ? 0 : 1,
        error: null,
        origin: index === 2 ? "analysis" : "live",
        provider:
          index === 2 ? "openrouter/test-model" : "deterministic/fixture",
      })),
      outputs: [1, 2].map(run => ({
        run,
        config: run === 1 ? "v1" : "v2",
        topic: "performance",
        intent: "issue",
        summary: "An earlier result.",
        evidence: ["The monthly export freezes."],
        provider: "deterministic/fixture",
        created_at: "2026-10-01T10:00:00Z",
      })),
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json(record, { status: 202 }));
    vi.stubGlobal("fetch", fetchMock);
    const { createHttpAdapter } = await import("@/api/client");
    const result = await createHttpAdapter().analyze(
      record.id,
      "same-request-on-retry"
    );
    expect(fetchMock.mock.calls[0][0]).toBe(
      `https://api.example.test/api/feedback/${record.id}/analysis`
    );
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      identity: "same-request-on-retry",
    });
    expect(result.jobs.at(-1)).toMatchObject({
      run: 3,
      provider: "openrouter/test-model",
      origin: "analysis",
      status: "queued",
    });
    expect(result.outputs.map(output => output.run)).toEqual([1, 2]);
  });

  it("rejects malformed successful response data instead of admitting it to the query cache", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          ...pageResult,
          records: [{ id: "bad-record", sequence: "twenty-four" }],
        })
      )
      .mockResolvedValueOnce(
        Response.json({
          id: "bad-record",
          sequence: 1,
          text: "source",
          jobs: [],
          outputs: [],
        })
      );
    vi.stubGlobal("fetch", fetchMock);
    const { createHttpAdapter } = await import("@/api/client");
    const adapter = createHttpAdapter();
    await expect(adapter.page(filters, null, 12)).rejects.toThrow();
    await expect(adapter.record("bad-record")).rejects.toThrow();
  });
});
