import { expect, type Page } from "@playwright/test";

type Job = {
  id: string;
  config: "v1" | "v2";
  run: number;
  status: "queued" | "leased" | "succeeded" | "failed";
  attempts: number;
  error: string | null;
  origin: "live" | "backfill" | "analysis";
  provider: string;
};

type Output = {
  config: "v1" | "v2";
  run: number;
  topic: "performance";
  intent: "issue";
  summary: string;
  evidence: string[];
  provider: string;
  created_at: string;
};

type Record = {
  id: string;
  sequence: number;
  text: string;
  channel: string;
  ingested_at: string;
  jobs: Job[];
  outputs: Output[];
};

const previousSummary = "An earlier analysis of the export problem.";

const fixtureRecord = (session: number): Record => {
  const text =
    session === 1
      ? "The export freezes whenever I select a full month of customer feedback."
      : "Search should remember the topic filter when I return from a message.";
  const output: Output = {
    config: "v1",
    run: 1,
    topic: "performance",
    intent: "issue",
    summary: previousSummary,
    evidence: [text],
    provider: "deterministic/fixture",
    created_at: "2026-10-01T10:00:00Z",
  };
  return {
    id: `00000000-0000-4000-8000-00000000000${session}`,
    sequence: 1,
    text,
    channel: "Support",
    ingested_at: "2026-10-01T09:00:00Z",
    jobs: [
      {
        id: `initial-${session}`,
        config: "v1",
        run: 1,
        status: "succeeded",
        attempts: 1,
        error: null,
        origin: "live",
        provider: "deterministic/fixture",
      },
      {
        id: `backfill-${session}`,
        config: "v2",
        run: 2,
        status: "succeeded",
        attempts: 1,
        error: null,
        origin: "backfill",
        provider: "deterministic/fixture",
      },
    ],
    outputs: [output, { ...output, config: "v2", run: 2 }],
  };
};

/** All API calls are intercepted, including auth. This fixture never reaches a provider. */
export const mockAnalysis = async (page: Page) => {
  let session = 0;
  let record = fixtureRecord(1);
  let revision = 1;
  const recordView = () => ({
    ...record,
    jobs: record.jobs.slice(-10),
    outputs: record.outputs.slice(-10),
  });
  let admission: Promise<void> | undefined;
  let rejection: { status: number; detail: string } | undefined;
  const requests: { identity: string; authorization: string | undefined }[] =
    [];
  const identity = () => ({
    workspace_id: `fixture-workspace-${session}`,
    email: null,
    kind: "demo",
  });

  await page.route(
    url => url.pathname.startsWith("/api/"),
    async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      const respond = (json: unknown, status = 200) =>
        route.fulfill({ status, json });

      if (path === "/api/auth/demo") {
        session++;
        record = fixtureRecord(session);
        return respond(
          { ...identity(), token: `fixture-token-${session}` },
          201
        );
      }
      if (path === "/api/auth/me") return respond(identity());
      if (path === "/api/auth/logout") return respond({ ok: true });
      if (path === "/api/status")
        return respond({
          ...identity(),
          revision,
          latest_sequence: 1,
          received: 1,
          enriched: record.jobs.at(-1)?.status === "succeeded" ? 1 : 0,
          failed: record.jobs.at(-1)?.status === "failed" ? 1 : 0,
          batches: [],
          provider: "openrouter/test-provider",
        });
      if (path === "/api/feedback" && request.method() === "GET")
        return respond({
          ...identity(),
          records: [recordView()],
          total: 1,
          next_cursor: null,
          refresh_cursor: "fixture-view.head",
          watermark: 1,
          revision,
        });
      if (path === `/api/feedback/${record.id}` && request.method() === "GET")
        return respond(recordView());
      if (
        path === `/api/feedback/${record.id}/analysis` &&
        request.method() === "POST"
      ) {
        const input: unknown = request.postDataJSON();
        if (
          !input ||
          typeof input !== "object" ||
          !("identity" in input) ||
          typeof input.identity !== "string"
        ) {
          throw new Error("Analysis request omitted its idempotency identity");
        }
        requests.push({
          identity: input.identity,
          authorization: request.headers().authorization,
        });
        if (rejection) {
          const error = rejection;
          rejection = undefined;
          return respond({ detail: error.detail }, error.status);
        }
        const run =
          Math.max(
            ...record.jobs
              .filter(job => job.config === "v2")
              .map(job => job.run)
          ) + 1;
        record.jobs.push({
          id: `analysis-${session}-${run}`,
          config: "v2",
          run,
          status: "queued",
          attempts: 0,
          error: null,
          origin: "analysis",
          provider: "openrouter/test-provider",
        });
        revision++;
        const admitted = structuredClone(recordView());
        const pending = admission;
        admission = undefined;
        if (pending) await pending;
        return respond(admitted, 202);
      }
      if (path.startsWith("/api/feedback/"))
        return respond({ detail: "Feedback was not found" }, 404);
      throw new Error(
        `Unexpected fixture API call: ${request.method()} ${path}`
      );
    }
  );

  return {
    requests,
    previousSummary,
    id: () => record.id,
    originalText: () => record.text,
    holdAdmission: () => {
      let release!: () => void;
      admission = new Promise<void>(resolve => {
        release = resolve;
      });
      return release;
    },
    rejectAdmission: (status: number, detail: string) => {
      rejection = { status, detail };
    },
    processing: () => {
      const job = record.jobs.at(-1)!;
      job.status = "leased";
      job.attempts = 1;
      revision++;
    },
    complete: (summary: string) => {
      const job = record.jobs.at(-1)!;
      job.status = "succeeded";
      record.outputs.push({
        config: job.config,
        run: job.run,
        topic: "performance",
        intent: "issue",
        summary,
        evidence: [record.text],
        provider: "openrouter/test-provider",
        created_at: new Date().toISOString(),
      });
      revision++;
    },
    fail: (message: string) => {
      const job = record.jobs.at(-1)!;
      job.status = "failed";
      job.attempts = 1;
      job.error = message;
      revision++;
    },
  };
};

export const openAnalysis = async (page: Page) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await page
    .getByRole("link", { name: "Open feedback 1", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Feedback #1", exact: true })
  ).toBeVisible();
};
