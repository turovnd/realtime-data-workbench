export {
  identitySchema,
  baseUrl,
  subscribeAuth,
  getSession,
  setSession,
  clearPrivateStorage,
  api,
  authenticate,
  loadIdentity,
  revokeSession,
} from "./auth";

export type { Identity, Session } from "./auth";

export { createHttpAdapter, resetPreview, adapter } from "./client";

export {
  feedbackInputSchema,
  configSchema,
  jobSchema,
  outputSchema,
  recordSchema,
  batchSchema,
  batchItemSchema,
  batchPageSchema,
  activityItemSchema,
  activityPageSchema,
  snapshotSchema,
  keepNewestSnapshot,
  currentJob,
  currentOutput,
  isAiOutput,
  filterRecords,
  feedFiltersSchema,
  feedPageSchema,
  feedStatusSchema,
} from "./contracts";

export type {
  FeedbackInput,
  Batch,
  BatchItem,
  BatchPage,
  ActivityItem,
  ActivityPage,
  ConfigVersion,
  FeedbackRecord,
  Output,
  Snapshot,
  Adapter,
  FeedFilters,
  FeedPage,
  FeedStatus,
  FeedAdapter,
} from "./contracts";

export { ApiError } from "./errors";
export { isAiProvider, isSampleProvider, formatProvider } from "./providers";
export { createDemoAdapter } from "./demo";
export { createDemoFeedAdapter } from "./demo-feed";
export { createSavedFeedbackStorage } from "./saved-feedback";
export type { SavedFeedback } from "./saved-feedback";
