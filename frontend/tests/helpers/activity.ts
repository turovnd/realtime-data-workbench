import { expect, type Page } from "@playwright/test";
import type { ActivityItem, FeedbackRecord, FeedStatus } from "@/api";

type Batch = FeedStatus["batches"][number];
type Item = {
  record_id: string;
  sequence: number;
  text: string;
  channel: string;
  job: FeedbackRecord["jobs"][number] | null;
  output: FeedbackRecord["outputs"][number] | null;
};
type DetailRequest = { batchId: string; cursor: string | null; limit: number };

const historicalSummary = "Monthly exports stop before the download completes.";
const latestSummary =
  "A later analysis focuses on the missing progress indicator.";
const otherSummary = "The customer needs invoices grouped by project.";
const firstBatchId = "00000000-0000-4000-8000-000000000101";
const secondBatchId = "00000000-0000-4000-8000-000000000102";

const createRecord = (sequence: number): FeedbackRecord => {
  const text =
    sequence === 13
      ? "Monthly exports stop without telling me whether the download is ready."
      : sequence === 14
        ? "Please group invoices by project so I can review each budget."
        : `The export for project ${sequence} stops before it finishes.`;
  const failed = sequence === 12;
  return {
    id: `00000000-0000-4000-8000-${String(sequence).padStart(12, "0")}`,
    sequence,
    text,
    channel: sequence === 14 ? "In-app" : "Support",
    ingested_at: "2026-10-01T09:00:00Z",
    jobs: [
      {
        id: `batch-job-${sequence}`,
        config: "v2",
        run: 2,
        status: failed ? "failed" : "succeeded",
        attempts: failed ? 3 : 1,
        error: failed
          ? "Provider output schema validation failed (summary: string_too_long)"
          : null,
        origin: "backfill",
        provider: "openrouter/test-provider",
      },
    ],
    outputs: failed
      ? []
      : [
          {
            config: "v2",
            run: 2,
            topic: sequence === 14 ? "billing" : "performance",
            intent: sequence === 14 ? "request" : "issue",
            summary:
              sequence === 13
                ? historicalSummary
                : sequence === 14
                  ? otherSummary
                  : `Export ${sequence} does not finish.`,
            evidence: [text],
            provider: "openrouter/test-provider",
            created_at: "2026-10-01T10:00:00Z",
          },
        ],
  };
};

/** Every API request, including auth, is intercepted; mutations cannot reach a provider. */
export const mockActivity = async (
  page: Page,
  options: { empty?: boolean; running?: boolean; standalone?: boolean } = {}
) => {
  const records = Array.from({ length: 14 }, (_, index) =>
    createRecord(14 - index)
  );
  const selected = records.filter(record => record.sequence <= 13);
  const items: Item[] = selected.map(record => ({
    record_id: record.id,
    sequence: record.sequence,
    text: record.text,
    channel: record.channel,
    job: structuredClone(record.jobs[0]),
    output: record.outputs[0] ? structuredClone(record.outputs[0]) : null,
  }));
  const original = selected[0];
  original.jobs.push({
    ...original.jobs[0],
    id: "later-analysis",
    run: 3,
    origin: "analysis",
  });
  original.outputs.push({
    ...original.outputs[0],
    run: 3,
    summary: latestSummary,
  });
  const first: Batch = {
    id: firstBatchId,
    config: "v2",
    selected: 13,
    completed: options.running ? 11 : 12,
    failed: 1,
    cancelled: false,
    watermark: 14,
  };
  const second: Batch = {
    ...first,
    id: secondBatchId,
    selected: 1,
    completed: 1,
    failed: 0,
  };
  if (options.running) {
    const pending = items.at(-1)!;
    pending.job = { ...pending.job!, status: "queued", attempts: 0 };
    pending.output = null;
  }
  const standalone = selected.map(record => ({
    kind: "feedback" as const,
    id: `live-${record.id}`,
    feedback: {
      record_id: record.id,
      sequence: record.sequence,
      text: record.text,
      channel: record.channel,
      job: {
        ...record.jobs[0],
        id: `live-${record.id}`,
        config: "v1" as const,
        run: 1,
        origin: "live" as const,
      },
      output: record.outputs[0]
        ? { ...record.outputs[0], config: "v1" as const, run: 1 }
        : null,
    },
  }));
  const firstActivity: ActivityItem = {
    kind: "batch",
    id: first.id,
    batch: first,
  };
  const secondActivity: ActivityItem = {
    kind: "batch",
    id: second.id,
    batch: second,
  };
  const activities: ActivityItem[] = options.empty
    ? []
    : options.standalone
      ? [
          ...standalone.slice(0, 5),
          firstActivity,
          ...standalone.slice(5),
          secondActivity,
        ]
      : [firstActivity, secondActivity];
  const activityRequests: { cursor: string | null; limit: number }[] = [];
  const activityViews = new Map<string, string[]>();
  const expiredActivityViews = new Set<string>();
  let activityCursorStatus = 410;
  let activityViewNumber = 0;
  let revision = 1;
  let session = 0;
  let heldActivity: Promise<void> | undefined;
  let addedFeedback: Extract<ActivityItem, { kind: "feedback" }> | undefined;

  const cancellations: string[] = [];
  const identity = () => ({
    workspace_id: `activity-fixture-workspace-${session}`,
    kind: "demo",
    email: null,
  });
  const requests: DetailRequest[] = [];
  let statusUnavailable = false;
  let detailsUnavailable = false;
  let cursorExpired = false;
  let heldDetails: Promise<void> | undefined;

  await page.route(
    url => url.pathname.startsWith("/api/"),
    async route => {
      const request = route.request();
      const url = new URL(request.url());
      const respond = (json: unknown, status = 200) =>
        route.fulfill({ status, json });
      if (url.pathname === "/api/auth/demo") {
        session++;
        return respond(
          { ...identity(), token: `activity-fixture-token-${session}` },
          201
        );
      }
      if (url.pathname === "/api/auth/me") return respond(identity());
      if (url.pathname === "/api/auth/logout") return respond({ ok: true });
      if (
        request.method() === "POST" &&
        url.pathname === `/api/backfills/${first.id}/cancel`
      ) {
        cancellations.push(first.id);
        first.cancelled = true;
        return respond({ ok: true });
      }
      if (request.method() !== "GET")
        throw new Error(
          `Unexpected mutation in Activity fixture: ${url.pathname}`
        );
      if (url.pathname === "/api/activity") {
        const cursor = url.searchParams.get("cursor");
        const limit = Number(url.searchParams.get("limit") ?? 10);
        activityRequests.push({ cursor, limit });
        if (statusUnavailable)
          return respond(
            { detail: "Activity is temporarily unavailable" },
            503
          );
        let viewId: string;
        let offset: number;
        if (cursor) {
          [viewId] = cursor.split(":");
          offset = Number(cursor.split(":")[1]);
          if (expiredActivityViews.has(viewId))
            return respond(
              { detail: "The saved activity cursor has expired" },
              activityCursorStatus
            );
        } else {
          viewId = `activity-${++activityViewNumber}`;
          offset = 0;
          activityViews.set(
            viewId,
            session === 1 ? activities.map(item => item.id) : []
          );
        }
        const ids = activityViews.get(viewId) ?? [];
        const visible = ids
          .slice(offset, offset + limit)
          .map(id => activities.find(item => item.id === id)!);
        const body = structuredClone({
          items: visible,
          next_cursor:
            offset + limit < ids.length ? `${viewId}:${offset + limit}` : null,
          refresh_cursor: `${viewId}:0`,
          total: ids.length,
          has_older: false,
          revision,
        });
        const pending = heldActivity;
        heldActivity = undefined;
        if (pending) await pending;
        return respond(body);
      }
      if (url.pathname === "/api/status")
        return statusUnavailable
          ? respond({ detail: "Activity is temporarily unavailable" }, 503)
          : respond({
              ...identity(),
              revision: 1,
              latest_sequence: 14,
              received: 14,
              enriched: 13,
              failed: 1,
              batches: options.empty ? [] : [first, second],
              provider: "openrouter/test-provider",
            });
      if (url.pathname === "/api/feedback") {
        const limit = Number(url.searchParams.get("limit") ?? 12);
        const offset = url.searchParams.has("cursor") ? limit : 0;
        return respond({
          ...identity(),
          records: records.slice(offset, offset + limit),
          total: records.length,
          next_cursor:
            offset + limit < records.length ? "fixture-feed.next" : null,
          refresh_cursor: "fixture-feed.head",
          watermark: 14,
          revision: 1,
        });
      }
      const record = records.find(
        record => url.pathname === `/api/feedback/${record.id}`
      );
      if (record) return respond(record);
      const batch = [first, second].find(
        batch => url.pathname === `/api/backfills/${batch.id}`
      );
      if (batch) {
        const cursor = url.searchParams.get("cursor");
        const limit = Number(url.searchParams.get("limit") ?? 10);
        requests.push({ batchId: batch.id, cursor, limit });
        const hold = heldDetails;
        heldDetails = undefined;
        if (hold) await hold;
        if (detailsUnavailable)
          return respond(
            { detail: "Analysis results are temporarily unavailable" },
            503
          );
        if (cursorExpired && cursor === "fixture-batch.next")
          return respond(
            { detail: "The saved selection cursor has expired" },
            410
          );
        const batchItems =
          batch.id === first.id
            ? items
            : [
                {
                  record_id: records[0].id,
                  sequence: records[0].sequence,
                  text: records[0].text,
                  channel: records[0].channel,
                  job: records[0].jobs[0],
                  output: records[0].outputs[0],
                },
              ];
        const offset = cursor ? limit : 0;
        return respond({
          batch,
          items: batchItems.slice(offset, offset + limit),
          next_cursor:
            offset + limit < batchItems.length
              ? cursorExpired
                ? "fixture-batch.renewed"
                : "fixture-batch.next"
              : null,
        });
      }
      throw new Error(`Unexpected Activity API call: ${url.pathname}`);
    }
  );

  return {
    requests,
    activityRequests,
    addFeedback: () => {
      const record = createRecord(15);
      record.text = "Search resets the selected channel when I open a message.";
      const job = {
        ...record.jobs[0],
        id: "new-feedback-job",
        config: "v1" as const,
        run: 1,
        status: "queued" as const,
        attempts: 0,
        origin: "live" as const,
      };
      record.jobs = [job];
      record.outputs = [];
      records.unshift(record);
      addedFeedback = {
        kind: "feedback",
        id: job.id,
        feedback: {
          record_id: record.id,
          sequence: 15,
          text: record.text,
          channel: record.channel,
          job,
          output: null,
        },
      };
      activities.unshift(addedFeedback);
      revision++;
    },
    finishFeedback: (failed = false) => {
      if (!addedFeedback?.feedback.job)
        throw new Error("Add fixture feedback first");
      const item = addedFeedback.feedback;
      item.job = {
        ...item.job!,
        status: failed ? "failed" : "succeeded",
        attempts: 1,
        error: failed
          ? "Provider evidence validation failed: quotes must match the original message exactly"
          : null,
      };
      item.output = failed
        ? null
        : {
            ...records.find(record => record.sequence === 13)!.outputs[0],
            config: "v1",
            run: 1,
            summary: "Opening a message resets the selected channel.",
            evidence: [item.text],
          };
      revision++;
    },
    addManualAnalysis: () => {
      activities.unshift({
        kind: "feedback",
        id: "later-analysis",
        feedback: {
          record_id: original.id,
          sequence: original.sequence,
          text: original.text,
          channel: original.channel,
          job: original.jobs.at(-1)!,
          output: original.outputs.at(-1)!,
        },
      });
      revision++;
    },
    expireActivityCursor: (status = 410) => {
      activityCursorStatus = status;
      for (const id of activityViews.keys()) expiredActivityViews.add(id);
    },
    holdActivity: () => {
      let release!: () => void;
      heldActivity = new Promise<void>(resolve => {
        release = resolve;
      });
      return release;
    },
    cancellations,
    firstBatchId,
    secondBatchId,
    historicalSummary,
    latestSummary,
    otherSummary,
    firstRecordId: original.id,
    firstText: original.text,
    expireCursor: () => {
      cursorExpired = true;
    },
    setStatusUnavailable: (value: boolean) => {
      statusUnavailable = value;
    },
    setDetailsUnavailable: (value: boolean) => {
      detailsUnavailable = value;
    },
    holdDetails: () => {
      let release!: () => void;
      heldDetails = new Promise<void>(resolve => {
        release = resolve;
      });
      return release;
    },
  };
};

export const enterActivity = async (page: Page) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
  await page.goto("/activity");
  await expect(
    page.getByRole("heading", { name: "Activity", exact: true })
  ).toBeVisible();
};
