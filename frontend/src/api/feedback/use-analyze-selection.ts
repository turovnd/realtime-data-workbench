import { useMutation, useQueryClient } from "@tanstack/react-query";

import { getSession } from "../auth";
import { adapter } from "../client";
import type { ConfigVersion } from "../contracts";

import { createFeedbackActions } from "./actions";

const actions = createFeedbackActions({
  adapter,
  getSession,
  isOnline: () => navigator.onLine,
});

export const useAnalyzeSelection = () => {
  const client = useQueryClient();
  const workspace = getSession()?.workspace_id;

  const mutation = useMutation({
    mutationFn: actions.analyzeSelection,
    onSuccess: async (_, submission) => {
      if (submission.token !== getSession()?.token) {
        return;
      }

      await Promise.all([
        client.invalidateQueries({ queryKey: ["feedback", workspace] }),
        client.invalidateQueries({ queryKey: ["feedback-status", workspace] }),
        client.invalidateQueries({ queryKey: ["feedback-record", workspace] }),
        client.invalidateQueries({ queryKey: ["activity", workspace] }),
      ]);
    },
  });

  const analyze = (
    ids: string[],
    config: ConfigVersion,
    onSuccess: () => void
  ) => {
    mutation.mutate({ ids, config, token: getSession()?.token }, { onSuccess });
  };

  return { analyze, pending: mutation.isPending, error: mutation.error };
};
