import type { Session } from "../auth";
import type {
  ConfigVersion,
  FeedAdapter,
  FeedbackInput,
  FeedbackRecord,
} from "../contracts";

export type AnalysisSelection = {
  ids: string[];
  config: ConfigVersion;
  token: string | undefined;
};

type Dependencies = {
  adapter: Pick<FeedAdapter, "backfill">;
  getSession: () => Session | null;
  isOnline: () => boolean;
};

export const createFeedbackActions = ({
  adapter,
  getSession,
  isOnline,
}: Dependencies) => {
  const analyzeSelection = async (
    selection: AnalysisSelection
  ): Promise<void> => {
    if (!selection.token || selection.token !== getSession()?.token) {
      throw new Error("Your session changed. Sign in again to run analysis.");
    }

    if (!isOnline()) {
      throw new Error("Reconnect before changing the workspace.");
    }

    await adapter.backfill(selection.ids, selection.config);
  };

  return { analyzeSelection };
};

export type FeedbackSubmission = {
  input: FeedbackInput;
  session: Session | null;
};

type SubmissionDependencies = {
  adapter: Pick<FeedAdapter, "create">;
  getSession: () => Session | null;
  isOnline: () => boolean;
};

export const submitFeedback = async (
  submission: FeedbackSubmission,
  { adapter, getSession, isOnline }: SubmissionDependencies
): Promise<FeedbackRecord> => {
  const activeSession = getSession();

  if (
    !submission.session ||
    submission.session.token !== activeSession?.token ||
    submission.session.workspace_id !== activeSession.workspace_id
  ) {
    throw new Error("Your session changed. Sign in again to add feedback.");
  }

  if (!isOnline()) {
    throw new Error("Reconnect before adding feedback.");
  }

  return adapter.create(submission.input);
};
