import { describe, expect, it } from "vitest";
import { createDemoAdapter } from "@/lib/api/demo";
import {
  filterRecords,
  keepNewestSnapshot,
  snapshotSchema,
} from "@/lib/api/contracts";

describe("snapshot and version contracts", () => {
  it("rejects an older revision only within the same workspace", async () => {
    const adapter = createDemoAdapter();
    const current = await adapter.snapshot();
    const stale = { ...current, cursor: 0 };
    expect(keepNewestSnapshot(current, stale)).toBe(current);
    expect(
      keepNewestSnapshot(current, { ...stale, workspace_id: "new" })
        .workspace_id,
    ).toBe("new");
  });
  it("validates the complete browser contract", async () => {
    expect(
      snapshotSchema.parse(await createDemoAdapter().snapshot()).records,
    ).toHaveLength(24);
  });
  it("freezes backfill selection and preserves old results", async () => {
    const adapter = createDemoAdapter();
    const first = await adapter.snapshot();
    const ids = first.records.slice(0, 2).map((row) => row.id);
    await adapter.backfill(ids, "v2");
    await adapter.simulate();
    for (let i = 0; i < 16; i++) await adapter.snapshot();
    const view = await adapter.snapshot();
    expect(view.batches[0].selected).toBe(2);
    expect(view.batches[0].completed).toBe(2);
    expect(
      view.records
        .filter((row) => ids.includes(row.id))
        .every((row) => row.outputs.length === 2),
    ).toBe(true);
    expect(
      view.records
        .filter((row) => row.sequence > 24)
        .every((row) => row.outputs.length === 1),
    ).toBe(true);
  });
  it("selective retry preserves the original feedback", async () => {
    const adapter = createDemoAdapter();
    const before = await adapter.snapshot();
    const failed = before.records.find(
      (row) => row.jobs[0].status === "failed",
    )!;
    await adapter.retry(failed.jobs[0].id);
    const result = (await adapter.snapshot()).records.find(
      (row) => row.id === failed.id,
    )!;
    expect(result.text).toBe(failed.text);
    expect(result.jobs[0].status).toBe("succeeded");
    expect(result.jobs[0].attempts).toBe(2);
  });
  it("filters status, text and topic together", async () => {
    const view = await createDemoAdapter().snapshot();
    expect(
      filterRecords(view.records, "billing", "succeeded", "billing"),
    ).toHaveLength(2);
    expect(filterRecords(view.records, "no-such-term", "all", "all")).toEqual(
      [],
    );
  });
  it("stops unfinished backfill work", async () => {
    const adapter = createDemoAdapter();
    const before = await adapter.snapshot();
    await adapter.backfill(
      before.records.slice(0, 3).map((row) => row.id),
      "v2",
    );
    const started = await adapter.snapshot();
    await adapter.cancel(started.batches[0].id);
    const stopped = await adapter.snapshot();
    expect(stopped.batches[0].cancelled).toBe(true);
    expect(stopped.batches[0].completed).toBe(1);
  });
});
