import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { adapter, ApiError, getSession } from "@/api";
import { useOnline } from "@/hooks";

export const useActivity = () => {
  const online = useOnline();
  const client = useQueryClient();
  const session = getSession();
  const workspace = session?.workspace_id;
  const key = ["activity", workspace] as const;
  const query = useInfiniteQuery({
    queryKey: key,
    queryFn: ({ pageParam, signal }) => adapter.activity(pageParam, 10, signal),
    initialPageParam: null as string | null,
    getNextPageParam: page => page.next_cursor ?? undefined,
    enabled: online,
    refetchInterval: query => (query.state.error ? false : 3000),
    refetchOnWindowFocus: query => !query.state.error,
    refetchOnReconnect: query => !query.state.error,
    retry: false,
  });
  const items = [
    ...new Map(
      query.data?.pages
        .flatMap(page => page.items)
        .map(item => [`${item.kind}:${item.id}`, item])
    ).values(),
  ];
  const cancel = useMutation({
    mutationFn: (request: { id: string; token: string | undefined }) => {
      if (request.token !== getSession()?.token)
        throw new Error(
          "Your session changed. Sign in again to cancel this run."
        );

      return adapter.cancel(request.id);
    },
    onSuccess: async (_, request) => {
      await Promise.all([
        client.invalidateQueries({ queryKey: key }),
        client.invalidateQueries({ queryKey: ["feedback-status", workspace] }),
        client.invalidateQueries({ queryKey: ["feedback", workspace] }),
        client.invalidateQueries({
          queryKey: ["analysis-run", workspace, request.id],
        }),
      ]);
    },
  });

  const retry = () => {
    if (
      query.error instanceof ApiError &&
      [400, 410].includes(query.error.status)
    )
      return void client.resetQueries({ queryKey: key, exact: true });

    return void (query.isFetchNextPageError
      ? query.fetchNextPage()
      : query.refetch());
  };

  return {
    query,
    items,
    online,
    cancel,
    retry,
    cancelRun: (id: string) => cancel.mutate({ id, token: session?.token }),
    total: query.data?.pages[0]?.total ?? 0,
    hasOlder: query.data?.pages[0]?.has_older ?? false,
  };
};
