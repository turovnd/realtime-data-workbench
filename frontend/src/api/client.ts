import {
  activityPageSchema,
  batchPageSchema,
  feedbackInputSchema,
  feedPageSchema,
  feedStatusSchema,
  recordSchema,
  type FeedAdapter,
} from "./contracts";
import { createDemoFeedAdapter } from "./demo";
import { api, baseUrl, getSession } from "./auth";

export const createHttpAdapter = (): FeedAdapter => ({
  mode: "server",
  activity: async (cursor, limit, signal) =>
    activityPageSchema.parse(
      (
        await api.api.listActivity(
          { cursor: cursor ?? undefined, limit },
          { signal }
        )
      ).data
    ),
  batch: async (id, cursor, limit, signal) =>
    batchPageSchema.parse(
      (
        await api.api.getBackfill(
          {
            batchId: encodeURIComponent(id),
            cursor: cursor ?? undefined,
            limit,
          },
          { signal }
        )
      ).data
    ),
  page: async (filters, cursor, limit, signal) =>
    feedPageSchema.parse(
      (
        await api.api.listFeedback(
          { ...filters, cursor: cursor ?? undefined, limit },
          { signal }
        )
      ).data
    ),
  status: async signal =>
    feedStatusSchema.parse((await api.api.getFeedbackStatus({ signal })).data),
  record: async (id, signal) =>
    recordSchema.parse(
      (
        await api.api.getFeedback(
          { recordId: encodeURIComponent(id) },
          { signal }
        )
      ).data
    ),
  create: async input =>
    recordSchema.parse(
      (await api.api.createFeedback(feedbackInputSchema.parse(input))).data
    ),
  analyze: async (id, identity) =>
    recordSchema.parse(
      (
        await api.api.analyzeFeedback(
          { recordId: encodeURIComponent(id) },
          { identity }
        )
      ).data
    ),
  simulate: async () => {
    await api.api.createSimulation({
      request_id: crypto.randomUUID(),
      count: 12,
    });
  },
  backfill: async (ids, config) => {
    await api.api.createBackfill({ record_ids: ids, config });
  },
  retry: async id => {
    await api.api.retryEnrichment({ jobId: encodeURIComponent(id) }, {});
  },
  cancel: async id => {
    await api.api.cancelBackfill({ batchId: encodeURIComponent(id) }, {});
  },
});
let preview: FeedAdapter | undefined;
let previewScope: string | undefined;

const getPreview = () => {
  const scope = getSession()?.workspace_id ?? "browser";
  if (!preview || previewScope !== scope) {
    previewScope = scope;
    preview = createDemoFeedAdapter({
      workspaceId: scope,
      storage: sessionStorage,
    });
  }
  return preview;
};

export const resetPreview = () => {
  if (previewScope)
    sessionStorage.removeItem(`feedback-desk-preview:${previewScope}`);
  preview = undefined;
  previewScope = undefined;
};

export const adapter: FeedAdapter = baseUrl
  ? createHttpAdapter()
  : {
      mode: "browser-demo",
      activity: (...args) => getPreview().activity(...args),
      batch: (...args) => getPreview().batch(...args),
      page: (...args) => getPreview().page(...args),
      status: (...args) => getPreview().status(...args),
      record: (...args) => getPreview().record(...args),
      create: input => getPreview().create(input),
      analyze: (...args) => getPreview().analyze(...args),
      simulate: () => getPreview().simulate(),
      backfill: (...args) => getPreview().backfill(...args),
      retry: id => getPreview().retry(id),
      cancel: id => getPreview().cancel(id),
    };
