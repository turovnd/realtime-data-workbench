import { useQuery } from "@tanstack/react-query";

import { getSession } from "../auth";
import { adapter } from "../client";

export const useFeedbackStatus = (online: boolean) => {
  const workspace = getSession()?.workspace_id ?? "none";

  return useQuery({
    queryKey: ["feedback-status", workspace],
    queryFn: ({ signal }) => adapter.status(signal),
    enabled: online,
    refetchInterval: query => (query.state.error ? false : 3000),
    refetchOnWindowFocus: query => !query.state.error,
    refetchOnReconnect: query => !query.state.error,
    retry: false,
  });
};
