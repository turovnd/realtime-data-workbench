import type { Page } from "@playwright/test";

import type { FeedbackRecord } from "../../src/api/contracts";

/** Controlled UI contract fixture. It never sends messages to a provider. */
export const mockSubmission = async (page: Page) => {
  const provider = "openrouter/ui-test-model";
  const identity = {
    workspace_id: "submission-workspace",
    kind: "demo",
    email: null,
  };
  const record: FeedbackRecord = {
    id: "00000000-0000-4000-8000-000000000025",
    sequence: 25,
    text: "",
    channel: "Support",
    ingested_at: "2026-11-15T10:00:00Z",
    jobs: [],
    outputs: [],
  };
  let statusAvailable = true;
  let admitted = false;
  let revision = 1;
  let release!: () => void;
  const admission = new Promise<void>(resolve => {
    release = resolve;
  });
  const submissions: { identity: string; text: string; channel: string }[] = [];
  const explicitAnalysisRequests: string[] = [];

  await page.route(
    url => url.pathname.startsWith("/api/"),
    async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      const respond = (json: unknown, status = 200) =>
        route.fulfill({ status, json });

      if (path === "/api/auth/demo")
        return respond({ ...identity, token: "submission-token" }, 201);
      if (path === "/api/auth/me") return respond(identity);
      if (path === "/api/status") {
        if (!statusAvailable)
          return respond({ detail: "Status unavailable" }, 503);
        return respond({
          ...identity,
          revision,
          latest_sequence: admitted ? 25 : 0,
          received: admitted ? 1 : 0,
          enriched: record.outputs.length,
          failed: 0,
          batches: [],
          provider,
        });
      }
      if (path === "/api/feedback" && request.method() === "GET")
        return respond({
          ...identity,
          records: admitted ? [record] : [],
          total: admitted ? 1 : 0,
          next_cursor: null,
          refresh_cursor: "submission-view.head",
          watermark: 25,
          revision,
        });
      if (path === "/api/feedback" && request.method() === "POST") {
        const input = request.postDataJSON() as {
          identity: string;
          text: string;
          channel: string;
        };
        submissions.push(input);
        record.text = input.text;
        record.channel = input.channel;
        record.jobs = [
          {
            id: "automatic-analysis",
            config: "v1",
            run: 1,
            status: "queued",
            attempts: 0,
            error: null,
            origin: "live",
            provider,
          },
        ];
        admitted = true;
        revision++;
        await admission;
        return respond(record, 201);
      }
      if (path === `/api/feedback/${record.id}`) return respond(record);
      if (path.endsWith("/analysis")) {
        explicitAnalysisRequests.push(path);
        return respond({ detail: "An automatic analysis already exists" }, 409);
      }
      if (path === "/api/activity")
        return respond({
          items: admitted
            ? [
                {
                  kind: "feedback",
                  id: "automatic-analysis",
                  feedback: {
                    record_id: record.id,
                    sequence: record.sequence,
                    text: record.text,
                    channel: record.channel,
                    job: record.jobs[0],
                    output: record.outputs[0] ?? null,
                  },
                },
              ]
            : [],
          next_cursor: null,
          refresh_cursor: "activity-view.head",
          total: admitted ? 1 : 0,
          has_older: false,
          revision,
        });
      throw new Error(
        `Unexpected submission fixture call: ${request.method()} ${path}`
      );
    }
  );

  return {
    submissions,
    explicitAnalysisRequests,
    release,
    setStatusAvailable: (available: boolean) => {
      statusAvailable = available;
    },
    processing: () => {
      record.jobs[0].status = "leased";
      record.jobs[0].attempts = 1;
      revision++;
    },
    complete: (summary: string, evidence: string[]) => {
      record.jobs[0].status = "succeeded";
      record.outputs = [
        {
          config: "v1",
          run: 1,
          topic: "performance",
          intent: "issue",
          summary,
          evidence,
          provider,
          created_at: "2026-11-15T10:00:10Z",
        },
      ];
      revision++;
    },
  };
};
