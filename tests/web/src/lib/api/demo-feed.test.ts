import { describe, expect, it } from "vitest";
import { createDemoFeedAdapter } from "@/lib/api/demo-feed";
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
      new Set([...first.records, ...next.records].map((row) => row.id)).size,
    ).toBe(24);
    expect(next.records.every((row) => row.sequence <= 24)).toBe(true);
    const fresh = await adapter.page(filters, null, 12);
    expect(fresh.total).toBe(36);
    expect(fresh.records[0].sequence).toBe(36);
  });
  it("binds continuation to filters and preserves a refreshed head", async () => {
    const adapter = createDemoFeedAdapter();
    const first = await adapter.page(filters, null, 12);
    await expect(
      adapter.page({ ...filters, q: "billing" }, first.next_cursor, 12),
    ).rejects.toThrow("expired");
    const refreshed = await adapter.page(filters, first.refresh_cursor, 12);
    expect(refreshed.records.map((row) => row.id)).toEqual(
      first.records.map((row) => row.id),
    );
  });
});
