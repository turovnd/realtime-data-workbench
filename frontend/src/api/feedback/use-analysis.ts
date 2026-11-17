import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useOnline } from "@/hooks";

import { getSession } from "../auth";
import { adapter } from "../client";
import { currentJob, currentOutput, isAiOutput } from "../contracts";
import { isSampleProvider } from "../providers";
import { createSavedFeedbackStorage } from "../saved-feedback";

export const useAnalysis = (id: string) => {
  const online = useOnline();
  const client = useQueryClient();
  const session = getSession();
  const key = ["feedback-record", session?.workspace_id, id];
  const identity = useRef(crypto.randomUUID());

  const query = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => adapter.record(id, signal),
    enabled: online,
    refetchOnWindowFocus: query => !query.state.error,
    refetchOnReconnect: query => !query.state.error,
    refetchInterval: query => {
      if (query.state.error) return false;

      const status = query.state.data && currentJob(query.state.data)?.status;

      return status === "queued" || status === "leased" ? 1000 : 10000;
    },
    retry: false,
  });

  const record =
    query.data ??
    (!online
      ? createSavedFeedbackStorage(
          localStorage,
          session?.workspace_id ?? "none"
        )
          .read()
          ?.snapshot.records.find(row => row.id === id)
      : undefined);
  const job = record && currentJob(record);
  const output = record && currentOutput(record);

  const action = useMutation({
    mutationFn: (request: { identity: string; token: string | undefined }) => {
      if (!request.token || request.token !== getSession()?.token) {
        throw new Error("Your session changed. Sign in again to run analysis.");
      }

      return adapter.analyze(id, request.identity);
    },
    onMutate: async () => {
      await client.cancelQueries({ queryKey: key });
    },
    onSuccess: (updated, request) => {
      if (request.token !== getSession()?.token) {
        return;
      }

      identity.current = crypto.randomUUID();
      client.setQueryData(key, updated);
      void client.invalidateQueries({ queryKey: key });
      void client.invalidateQueries({
        queryKey: ["feedback", session?.workspace_id],
      });
      void client.invalidateQueries({
        queryKey: ["feedback-status", session?.workspace_id],
      });
    },
    onError: () => {
      void client.invalidateQueries({ queryKey: key });
    },
  });

  const running = job?.status === "queued" || job?.status === "leased";
  const busy = action.isPending || running;
  const samplePending =
    !action.isPending && running && isSampleProvider(job?.provider);

  const completed =
    job?.status === "succeeded" &&
    output?.run === job.run &&
    isAiOutput(output);
  const previous =
    !!output &&
    (busy ||
      job?.status !== "succeeded" ||
      (job?.run !== undefined && output.run !== job.run));
  const preview = adapter.mode === "browser-demo";

  const start = () => {
    if (!online || busy || preview) {
      return;
    }

    action.mutate({ identity: identity.current, token: getSession()?.token });
  };

  return {
    query,
    record,
    job,
    output,
    online,
    action,
    busy,
    samplePending,
    completed,
    previous,
    preview,
    start,
  };
};

export type AnalysisState = ReturnType<typeof useAnalysis>;
