import {
  feedPageSchema,
  feedStatusSchema,
  type FeedAdapter,
} from "./contracts";
import { createDemoFeedAdapter } from "./demo-feed";
import { baseUrl, request } from "./auth";

export const createHttpAdapter = (): FeedAdapter => ({
  mode: "server",
  page: async (filters, cursor, limit, signal) => {
    const params = new URLSearchParams({ ...filters, limit: String(limit) });
    if (cursor) params.set("cursor", cursor);
    return feedPageSchema.parse(
      await request(`/api/feedback?${params}`, undefined, signal),
    );
  },
  status: async (signal) =>
    feedStatusSchema.parse(await request("/api/status", undefined, signal)),
  simulate: async () => {
    await request("/api/simulations", {
      request_id: crypto.randomUUID(),
      count: 12,
    });
  },
  backfill: async (ids, config) => {
    await request("/api/backfills", { record_ids: ids, config });
  },
  retry: async (id) => {
    await request(`/api/jobs/${encodeURIComponent(id)}/retry`, {});
  },
  cancel: async (id) => {
    await request(`/api/backfills/${encodeURIComponent(id)}/cancel`, {});
  },
});
let preview = createDemoFeedAdapter();
export const resetPreview = () => {
  preview = createDemoFeedAdapter();
};
export const adapter: FeedAdapter = baseUrl
  ? createHttpAdapter()
  : {
      mode: "browser-demo",
      page: (...args) => preview.page(...args),
      status: (...args) => preview.status(...args),
      simulate: () => preview.simulate(),
      backfill: (...args) => preview.backfill(...args),
      retry: (id) => preview.retry(id),
      cancel: (id) => preview.cancel(id),
    };
