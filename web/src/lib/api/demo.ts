import type {
  Adapter,
  ConfigVersion,
  FeedbackRecord,
  Output,
  Snapshot,
} from "./contracts";

const samples = [
  [
    "The activity page loses my filters whenever new updates arrive.",
    "In-app",
    "reliability",
    "issue",
  ],
  [
    "CSV export times out when I select the full month of feedback.",
    "Support",
    "performance",
    "issue",
  ],
  [
    "Please add a keyboard shortcut to jump between saved views.",
    "Community",
    "usability",
    "request",
  ],
  [
    "The billing page charged our workspace twice this month.",
    "Support",
    "billing",
    "issue",
  ],
  [
    "Search feels slow when I paste a long customer reference.",
    "In-app",
    "performance",
    "issue",
  ],
  [
    "The new filters make our weekly review much easier. Thank you!",
    "Community",
    "usability",
    "praise",
  ],
  [
    "Notifications stop arriving after I reconnect to the network.",
    "Support",
    "reliability",
    "issue",
  ],
  [
    "Please let me pin the source column in the feedback table.",
    "In-app",
    "usability",
    "request",
  ],
  [
    "The invoice download button returns an empty document.",
    "Support",
    "billing",
    "issue",
  ],
  [
    "The dashboard takes ten seconds to load on my laptop.",
    "In-app",
    "performance",
    "issue",
  ],
  [
    "The new evidence panel makes the original feedback easy to verify.",
    "Community",
    "usability",
    "praise",
  ],
  [
    "Something changed yesterday, but I cannot tell what it was.",
    "Community",
    "other",
    "unclear",
  ],
] as const;

export const createDemoAdapter = (): Adapter => {
  let cursor = 1;
  let records: FeedbackRecord[] = [];
  const batches: (Snapshot["batches"][number] & { ids: string[] })[] = [];
  const output = (record: FeedbackRecord, config: ConfigVersion): Output => {
    const sample = samples[(record.sequence - 1) % samples.length];
    return {
      config,
      topic: sample[2],
      intent: sample[3],
      summary:
        config === "v1"
          ? record.text
          : `${sample[3]} · ${sample[2]}: ${record.text}`,
      evidence: [record.text],
      provider: "browser-fixture/1",
      created_at: new Date().toISOString(),
    };
  };
  const append = (initial = false) => {
    if (records.length + 12 > 500)
      throw new Error(
        "This bounded browser demo is full. Reload to start again.",
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
  };
  append(true);
  append(true);
  const tick = () => {
    const job = records
      .flatMap((row) => row.jobs.map((job) => ({ row, job })))
      .find(({ job }) => job.status === "queued");
    if (!job) return;
    job.job.status = "succeeded";
    job.job.attempts++;
    job.job.error = null;
    job.row.outputs.push(output(job.row, job.job.config));
    cursor++;
  };
  return {
    mode: "browser-demo",
    snapshot: async (signal) => {
      signal?.throwIfAborted();
      tick();
      return structuredClone({
        workspace_id: "browser",
        cursor,
        records,
        mode: "browser-demo",
        batches: batches.map((batch) => ({
          id: batch.id,
          config: batch.config,
          selected: batch.selected,
          watermark: batch.watermark,
          cancelled: batch.cancelled,
          completed: records.filter(
            (row) =>
              batch.ids.includes(row.id) &&
              row.outputs.some((result) => result.config === batch.config),
          ).length,
          failed: records.filter(
            (row) =>
              batch.ids.includes(row.id) &&
              row.jobs.some(
                (job) => job.config === batch.config && job.status === "failed",
              ),
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
      const rows = records.filter((row) => ids.includes(row.id));
      const pending = rows.filter(
        (row) => !row.jobs.some((job) => job.config === config),
      );
      if (!pending.length)
        throw new Error(
          "This version already exists. Inspect its results or retry its failed job.",
        );
      const id = `batch-${batches.length + 1}`;
      pending.forEach((row) =>
        row.jobs.push({
          id: `${row.id}-${config}`,
          config,
          status: "queued",
          attempts: 0,
          error: null,
          origin: "backfill",
        }),
      );
      batches.push({
        id,
        ids: rows.map((row) => row.id),
        config,
        selected: rows.length,
        completed: 0,
        failed: 0,
        cancelled: false,
        watermark: Math.max(...rows.map((row) => row.sequence)),
      });
      cursor++;
    },
    retry: async (id) => {
      const job = records
        .flatMap((row) => row.jobs)
        .find((job) => job.id === id);
      if (
        !job ||
        !["failed", "cancelled"].includes(job.status) ||
        job.attempts >= 3
      )
        throw new Error("This job has no remaining retries.");
      job.status = "queued";
      job.error = null;
      cursor++;
    },
    cancel: async (id) => {
      const batch = batches.find((batch) => batch.id === id);
      if (!batch) throw new Error("Batch not found");
      batch.cancelled = true;
      records
        .filter((row) => batch.ids.includes(row.id))
        .forEach((row) =>
          row.jobs
            .filter(
              (job) => job.config === batch.config && job.status === "queued",
            )
            .forEach((job) => {
              job.status = "cancelled";
            }),
        );
      cursor++;
    },
  };
};
