import { useQuery } from "@tanstack/react-query";

import { getSession } from "../auth";
import { adapter } from "../client";

export const useFeedbackStatus = (online: boolean) => {
  const workspace = getSession()?.workspace_id ?? "none";

  return useQuery({
    queryKey: ["feedback-status", workspace],
    queryFn: ({ signal }) => adapter.status(signal),
    enabled: online,
    refetchInterval: 3000,
    retry: 1,
  });
};
