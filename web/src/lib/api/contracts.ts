import { z } from "zod";

export const configSchema = z.enum(["v1", "v2"]);
export const jobSchema = z.object({
  id: z.string(),
  config: configSchema,
  status: z.enum(["queued", "leased", "succeeded", "failed", "cancelled"]),
  attempts: z.number().int().min(0).max(3),
  error: z.string().nullable(),
  origin: z.enum(["live", "backfill"]),
});
export const outputSchema = z.object({
  config: configSchema,
  topic: z.enum([
    "reliability",
    "usability",
    "billing",
    "performance",
    "other",
  ]),
  intent: z.enum(["issue", "request", "praise", "unclear"]),
  summary: z.string().max(240),
  evidence: z.array(z.string().max(200)).min(1).max(3),
  provider: z.string(),
  created_at: z.string(),
});
export const recordSchema = z.object({
  id: z.string(),
  sequence: z.number().int(),
  text: z.string().max(4000),
  channel: z.string(),
  ingested_at: z.string(),
  jobs: z.array(jobSchema).max(2),
  outputs: z.array(outputSchema).max(2),
});
export const batchSchema = z.object({
  id: z.string(),
  config: configSchema,
  selected: z.number(),
  completed: z.number(),
  failed: z.number(),
  cancelled: z.boolean(),
  watermark: z.number(),
});
export const snapshotSchema = z.object({
  workspace_id: z.string(),
  cursor: z.number().int(),
  records: z.array(recordSchema).max(500),
  batches: z.array(batchSchema),
  mode: z.enum(["server", "browser-demo"]),
});
export type ConfigVersion = z.infer<typeof configSchema>;
export type FeedbackRecord = z.infer<typeof recordSchema>;
export type Output = z.infer<typeof outputSchema>;
export type Snapshot = z.infer<typeof snapshotSchema>;
export type Adapter = {
  snapshot: (signal?: AbortSignal) => Promise<Snapshot>;
  simulate: () => Promise<void>;
  backfill: (ids: string[], config: ConfigVersion) => Promise<void>;
  retry: (id: string) => Promise<void>;
  cancel: (id: string) => Promise<void>;
  mode: Snapshot["mode"];
};

export const keepNewestSnapshot = (
  previous: Snapshot | undefined,
  next: Snapshot,
) =>
  previous &&
  previous.workspace_id === next.workspace_id &&
  previous.cursor > next.cursor
    ? previous
    : next;
export const currentJob = (record: FeedbackRecord) => record.jobs.at(-1);
export const currentOutput = (record: FeedbackRecord) => record.outputs.at(-1);
export const filterRecords = (
  records: FeedbackRecord[],
  search: string,
  status: string,
  topic: string,
) =>
  records.filter(
    (record) =>
      (status === "all" || currentJob(record)?.status === status) &&
      (topic === "all" || currentOutput(record)?.topic === topic) &&
      record.text.toLowerCase().includes(search.toLowerCase()),
  );

export const feedFiltersSchema = z.object({
  q: z.string().max(100),
  status: z.enum([
    "all",
    "queued",
    "leased",
    "succeeded",
    "failed",
    "cancelled",
  ]),
  topic: z.enum([
    "all",
    "reliability",
    "usability",
    "billing",
    "performance",
    "other",
  ]),
});
export const feedPageSchema = z.object({
  workspace_id: z.string(),
  records: z.array(recordSchema).max(50),
  next_cursor: z.string().nullable(),
  refresh_cursor: z.string(),
  watermark: z.number().int(),
  revision: z.number().int(),
  total: z.number().int(),
});
export const feedStatusSchema = z.object({
  workspace_id: z.string(),
  revision: z.number().int(),
  latest_sequence: z.number().int(),
  received: z.number().int(),
  enriched: z.number().int(),
  failed: z.number().int(),
  batches: z.array(batchSchema).max(10),
  provider: z.string(),
});
export type FeedFilters = z.infer<typeof feedFiltersSchema>;
export type FeedPage = z.infer<typeof feedPageSchema>;
export type FeedStatus = z.infer<typeof feedStatusSchema>;
export type FeedAdapter = Pick<
  Adapter,
  "simulate" | "backfill" | "retry" | "cancel" | "mode"
> & {
  page: (
    filters: FeedFilters,
    cursor: string | null,
    limit: number,
    signal?: AbortSignal,
  ) => Promise<FeedPage>;
  status: (signal?: AbortSignal) => Promise<FeedStatus>;
};
