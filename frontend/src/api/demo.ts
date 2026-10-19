import type { Adapter, FeedbackRecord, Snapshot } from "./contracts";
import { feedbackInputSchema } from "./contracts";
import { samples, previewOutput as output } from "./demo-fixtures";
import { readPreview, writePreview, type PreviewOptions } from "./demo-storage";
import { ApiError } from "./errors";

export const createDemoAdapter = (options: PreviewOptions = {}): Adapter => {
  const workspaceId = options.workspaceId ?? "browser";
  const restored = readPreview(options);
  let cursor = restored?.cursor ?? 1;
  let records: FeedbackRecord[] = restored?.records ?? [];
  const batches: (Snapshot["batches"][number] & { ids: string[] })[] =
    restored?.batches ?? [];
  const identities = new Map(restored?.identities ?? []);
  const persist = () =>
    writePreview(options, {
      workspace_id: workspaceId,
      cursor,
      records,
      batches,
      identities: [...identities],
    });
  const append = (initial = false) => {
    if (records.length + 12 > 500)
      throw new Error(
        "This bounded browser demo is full. Sign out and start a new demo."
      );
    const start = records.length;
    const next = samples.map((sample, index): FeedbackRecord => {
      const sequence = start + index + 1;
      const row: FeedbackRecord = {
        id: `feedback-${sequence}`,
        sequence,
        text: sample[0],
        channel: sample[1],
        ingested_at: new Date(Date.now() - (12 - index) * 60000).toISOString(),
        jobs: [
          {
            id: `job-${sequence}-v1`,
            config: "v1",
            status: initial ? "succeeded" : "queued",
            attempts: initial ? 1 : 0,
            error: null,
            origin: "live",
          },
        ],
        outputs: [],
      };
      if (initial && index !== 8) row.outputs = [output(row, "v1")];
      if (initial && index === 8)
        row.jobs[0] = {
          ...row.jobs[0],
          status: "failed",
          error:
            "Simulated invalid provider output. Retry uses the valid deterministic fixture.",
        };
      return row;
    });
    records = [...next.reverse(), ...records];
    cursor++;
    persist();
  };
  if (!restored) {
    append(true);
    append(true);
  }
  const tick = () => {
    const job = records
      .flatMap(row => row.jobs.map(job => ({ row, job })))
      .find(({ job }) => job.status === "queued");
    if (!job) return;
    job.job.status = "succeeded";
    job.job.attempts++;
    job.job.error = null;
    job.row.outputs.push(output(job.row, job.job.config));
    cursor++;
    persist();
  };
  return {
    analyze: async () => {
      throw new Error("Connect the API to run AI analysis.");
    },
    mode: "browser-demo",
    batch: async (id, pageCursor, limit, signal) => {
      signal?.throwIfAborted();
      const batch = batches.find(item => item.id === id);
      if (!batch) throw new ApiError("Analysis run was not found", 404);
      const prefix = `${id}:`;
      if (pageCursor && !pageCursor.startsWith(prefix))
        throw new ApiError("Invalid run cursor", 400);
      const offset = pageCursor ? Number(pageCursor.slice(prefix.length)) : 0;
      if (!Number.isInteger(offset) || offset < 0)
        throw new ApiError("Invalid run cursor", 400);
      tick();
      const selected = records.filter(row => batch.ids.includes(row.id));
      const items = selected.map(row => {
        const job =
          row.jobs.find(
            job => job.config === batch.config && job.origin !== "analysis"
          ) ?? null;
        return {
          record_id: row.id,
          sequence: row.sequence,
          text: row.text,
          channel: row.channel,
          job,
          output: job
            ? (row.outputs.find(
                output => output.config === job.config && output.run === job.run
              ) ?? null)
            : null,
        };
      });
      return structuredClone({
        batch: {
          ...batch,
          completed: items.filter(item => item.job?.status === "succeeded")
            .length,
          failed: items.filter(item => item.job?.status === "failed").length,
        },
        items: items.slice(offset, offset + limit),
        next_cursor:
          offset + limit < items.length ? `${prefix}${offset + limit}` : null,
      });
    },
    record: async (id, signal) => {
      signal?.throwIfAborted();
      const record = records.find(row => row.id === id);
      if (!record) throw new ApiError("Feedback was not found", 404);
      tick();
      return structuredClone(record);
    },
    create: async input => {
      const value = feedbackInputSchema.parse(input);
      const previousId = identities.get(value.identity);
      const previous = records.find(row => row.id === previousId);
      if (previous) {
        if (previous.text !== value.text || previous.channel !== value.channel)
          throw new ApiError(
            "An input identity cannot be reused with different content",
            409
          );
        return structuredClone(previous);
      }
      if (records.length >= 500)
        throw new ApiError(
          "This bounded demo workspace is full (500 records)",
          409
        );
      const sequence = records.length + 1;
      const row: FeedbackRecord = {
        id: `feedback-${sequence}`,
        sequence,
        text: value.text,
        channel: value.channel,
        ingested_at: new Date().toISOString(),
        outputs: [],
        jobs: [
          {
            id: `job-${sequence}-v1`,
            config: "v1",
            status: "queued",
            attempts: 0,
            error: null,
            origin: "live",
          },
        ],
      };
      records = [row, ...records];
      identities.set(value.identity, row.id);
      cursor++;
      persist();
      return structuredClone(row);
    },
    snapshot: async signal => {
      signal?.throwIfAborted();
      tick();
      return structuredClone({
        workspace_id: workspaceId,
        cursor,
        records,
        mode: "browser-demo",
        batches: batches.map(batch => ({
          id: batch.id,
          config: batch.config,
          selected: batch.selected,
          watermark: batch.watermark,
          cancelled: batch.cancelled,
          completed: records.filter(
            row =>
              batch.ids.includes(row.id) &&
              row.outputs.some(result => result.config === batch.config)
          ).length,
          failed: records.filter(
            row =>
              batch.ids.includes(row.id) &&
              row.jobs.some(
                job => job.config === batch.config && job.status === "failed"
              )
          ).length,
        })),
      });
    },
    simulate: async () => {
      append();
    },
    backfill: async (ids, config) => {
      if (!ids.length || ids.length > 100)
        throw new Error("Select between 1 and 100 records.");
      const rows = records.filter(row => ids.includes(row.id));
      const pending = rows.filter(
        row => !row.jobs.some(job => job.config === config)
      );
      if (!pending.length)
        throw new Error(
          "This version already exists. Inspect its results or retry its failed job."
        );
      const id = `batch-${batches.length + 1}`;
      pending.forEach(row =>
        row.jobs.push({
          id: `${row.id}-${config}`,
          config,
          status: "queued",
          attempts: 0,
          error: null,
          origin: "backfill",
        })
      );
      batches.push({
        id,
        ids: rows.map(row => row.id),
        config,
        selected: rows.length,
        completed: 0,
        failed: 0,
        cancelled: false,
        watermark: Math.max(...rows.map(row => row.sequence)),
      });
      cursor++;
      persist();
    },
    retry: async id => {
      const job = records.flatMap(row => row.jobs).find(job => job.id === id);
      if (
        !job ||
        !["failed", "cancelled"].includes(job.status) ||
        job.attempts >= 3
      )
        throw new Error("This job has no remaining retries.");
      job.status = "queued";
      job.error = null;
      cursor++;
      persist();
    },
    cancel: async id => {
      const batch = batches.find(batch => batch.id === id);
      if (!batch) throw new Error("Batch not found");
      batch.cancelled = true;
      records
        .filter(row => batch.ids.includes(row.id))
        .forEach(row =>
          row.jobs
            .filter(
              job => job.config === batch.config && job.status === "queued"
            )
            .forEach(job => {
              job.status = "cancelled";
            })
        );
      cursor++;
      persist();
    },
  };
};
