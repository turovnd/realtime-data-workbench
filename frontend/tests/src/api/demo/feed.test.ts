import { describe, expect, it } from "vitest";
import { createDemoFeedAdapter } from "@/api/demo";
const filters = { q: "", status: "all", topic: "all" } as const;
describe("isolated browser feed fixture", () => {
  it("freezes membership while new arrivals use a fresh view", async () => {
    const adapter = createDemoFeedAdapter();
    const first = await adapter.page(filters, null, 12);
    expect(first.total).toBe(24);
    await adapter.simulate();
    const next = await adapter.page(filters, first.next_cursor, 12);
    expect(next.next_cursor).toBeNull();
    expect(
      new Set([...first.records, ...next.records].map(row => row.id)).size
    ).toBe(24);
    expect(next.records.every(row => row.sequence <= 24)).toBe(true);
    const fresh = await adapter.page(filters, null, 12);
    expect(fresh.total).toBe(36);
    expect(fresh.records[0].sequence).toBe(36);
  });
  it("binds continuation to filters and preserves a refreshed head", async () => {
    const adapter = createDemoFeedAdapter();
    const first = await adapter.page(filters, null, 12);
    await expect(
      adapter.page({ ...filters, q: "billing" }, first.next_cursor, 12)
    ).rejects.toThrow("expired");
    const refreshed = await adapter.page(filters, first.refresh_cursor, 12);
    expect(refreshed.records.map(row => row.id)).toEqual(
      first.records.map(row => row.id)
    );
  });

  it("keeps custom input and its idempotency across a reload without exposing it to another preview", async () => {
    const values = new Map<string, string>();
    const storage = {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => {
        values.set(key, value);
      },
      removeItem: (key: string) => {
        values.delete(key);
      },
    };
    const first = createDemoFeedAdapter({
      workspaceId: "first-workspace",
      storage,
    });
    const input = {
      identity: "own-message-1",
      text: "Our finance team needs the monthly export to keep the selected date range.",
      channel: "Community" as const,
    };
    const created = await first.create(input);
    expect(created.sequence).toBe(25);
    expect(created.text).toBe(input.text);
    expect(created.channel).toBe("Community");
    const reloaded = createDemoFeedAdapter({
      workspaceId: "first-workspace",
      storage,
    });
    expect((await reloaded.record(created.id)).text).toBe(input.text);
    expect((await reloaded.create(input)).id).toBe(created.id);
    expect((await reloaded.page(filters, null, 12)).total).toBe(25);
    await expect(
      reloaded.create({ ...input, text: "Different customer content" })
    ).rejects.toMatchObject({ status: 409 });
    const other = createDemoFeedAdapter({
      workspaceId: "another-workspace",
      storage,
    });
    await expect(other.record(created.id)).rejects.toMatchObject({
      status: 404,
    });
    expect((await other.page(filters, null, 12)).total).toBe(24);
  });

  it("rejects blank and oversized customer input without adding records", async () => {
    const adapter = createDemoFeedAdapter();
    const input = {
      identity: "bad-input",
      text: "   ",
      channel: "Support" as const,
    };
    await expect(adapter.create(input)).rejects.toThrow();
    await expect(
      adapter.create({ ...input, text: "x".repeat(4001) })
    ).rejects.toThrow();
    expect((await adapter.page(filters, null, 12)).total).toBe(24);
  });

  it("retrieves an unloaded record directly and honors cancellation", async () => {
    const adapter = createDemoFeedAdapter();
    const first = await adapter.page(filters, null, 12);
    expect(first.records.some(record => record.sequence === 1)).toBe(false);
    expect((await adapter.record("feedback-1")).sequence).toBe(1);
    const abort = new AbortController();
    abort.abort();
    await expect(
      adapter.record("feedback-1", abort.signal)
    ).rejects.toMatchObject({ name: "AbortError" });
  });
});
