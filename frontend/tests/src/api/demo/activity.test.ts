import { describe, expect, it, vi } from "vitest";
import { activityPageSchema, type Snapshot } from "@/api/contracts";
import { createDemoActivity } from "@/api/demo";
import { createDemoFeedAdapter } from "@/api/demo";

describe("preview activity", () => {
  it("freezes paginated membership and discovers new feedback on a fresh head", async () => {
    const adapter = createDemoFeedAdapter();
    const first = activityPageSchema.parse(await adapter.activity(null, 12));
    expect(first.total).toBe(24);
    expect(first.has_older).toBe(false);
    const record = await adapter.create({
      identity: "activity-new-feedback",
      text: "The export keeps losing the date filter.",
      channel: "Support",
    });
    const second = await adapter.activity(first.next_cursor, 12);
    expect(second.next_cursor).toBeNull();
    expect(
      new Set([...first.items, ...second.items].map(item => item.id)).size
    ).toBe(24);
    const fresh = await adapter.activity(null, 12);
    expect(fresh.total).toBe(25);
    expect(fresh.items[0]).toMatchObject({
      kind: "feedback",
      feedback: { record_id: record.id, job: { status: "succeeded" } },
    });
    const refreshed = await adapter.activity(first.refresh_cursor, 12);
    expect(refreshed.items.map(item => item.id)).toEqual(
      first.items.map(item => item.id)
    );
  });

  it("binds a result to its run and does not duplicate grouped child jobs", async () => {
    const job = {
      config: "v2" as const,
      status: "succeeded" as const,
      attempts: 1,
      error: null,
      provider: "browser-fixture/1",
    };
    const output = {
      config: "v2" as const,
      topic: "usability" as const,
      intent: "issue" as const,
      evidence: ["Export loses filters."],
      provider: "browser-fixture/1",
      created_at: "2026-10-18T12:00:00Z",
    };
    const snapshot: Snapshot = {
      workspace_id: "preview",
      cursor: 3,
      mode: "browser-demo",
      batches: [
        {
          id: "group",
          config: "v2",
          selected: 1,
          completed: 1,
          failed: 0,
          cancelled: false,
          watermark: 1,
        },
      ],
      records: [
        {
          id: "record",
          sequence: 1,
          text: "Export loses filters.",
          channel: "Support",
          ingested_at: "2026-10-18T11:00:00Z",
          jobs: [
            { ...job, id: "grouped", run: 2, origin: "backfill" },
            { ...job, id: "earlier", run: 3, origin: "analysis" },
            { ...job, id: "latest", run: 11, origin: "analysis" },
          ],
          outputs: [
            { ...output, run: 3, summary: "Earlier result" },
            { ...output, run: 11, summary: "Latest result" },
          ],
        },
      ],
    };
    const read = vi.fn(async () => structuredClone(snapshot));
    const activity = createDemoActivity(read);
    const page = activityPageSchema.parse(await activity(null, 10));
    expect(page.items.map(item => item.id)).toEqual([
      "group",
      "latest",
      "earlier",
    ]);
    expect(page.items[2]).toMatchObject({
      feedback: {
        job: { run: 3 },
        output: { run: 3, summary: "Earlier result" },
      },
    });
    expect(snapshot.records[0].jobs).toHaveLength(3);
    expect(read).toHaveBeenCalledOnce();
  });

  it("rejects invalid, cross-session and expired cursors and honors cancellation", async () => {
    const adapter = createDemoFeedAdapter();
    const first = await adapter.activity(null, 10);
    await expect(adapter.activity("invalid.cursor", 10)).rejects.toMatchObject({
      status: 400,
    });
    await expect(adapter.activity(null, 51)).rejects.toMatchObject({
      status: 400,
    });
    await expect(
      createDemoFeedAdapter().activity(first.next_cursor, 10)
    ).rejects.toMatchObject({ status: 410 });
    const controller = new AbortController();
    controller.abort();
    await expect(
      adapter.activity(null, 10, controller.signal)
    ).rejects.toMatchObject({ name: "AbortError" });
    vi.useFakeTimers();
    try {
      vi.setSystemTime(Date.now() + 600001);
      await expect(
        adapter.activity(first.next_cursor, 10)
      ).rejects.toMatchObject({ status: 410 });
    } finally {
      vi.useRealTimers();
    }
  });
});
