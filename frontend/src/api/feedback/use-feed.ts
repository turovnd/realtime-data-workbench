import { useState } from "react";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import type { InfiniteData } from "@tanstack/react-query";

import { getSession } from "../auth";
import { adapter } from "../client";
import type { FeedFilters, FeedPage } from "../contracts";

export const useFeed = (filters: FeedFilters, online: boolean) => {
  const client = useQueryClient();
  const workspace = getSession()?.workspace_id ?? "none";
  const filterKey = JSON.stringify(filters);
  const [view, setView] = useState({ filterKey, generation: 0 });

  if (view.filterKey !== filterKey) {
    setView({ filterKey, generation: view.generation + 1 });
  }

  const key = ["feedback", workspace, filters, view.generation] as const;
  const query = useInfiniteQuery({
    queryKey: key,
    initialPageParam: null as string | null,
    queryFn: ({ signal, pageParam }) => {
      const previous =
        client.getQueryData<InfiniteData<FeedPage, string | null>>(key);
      const cursor = pageParam ?? previous?.pages[0]?.refresh_cursor ?? null;

      return adapter.page(filters, cursor, 12, signal);
    },
    getNextPageParam: page => page.next_cursor ?? undefined,
    enabled: online,
    refetchInterval: 3000,
    retry: false,
  });

  const head = query.data?.pages[0];
  const records = [
    ...new Map(
      query.data?.pages
        .flatMap(page => page.records)
        .map(record => [record.id, record])
    ).values(),
  ];

  const refresh = () => {
    setView(value => ({ ...value, generation: value.generation + 1 }));
    void client.invalidateQueries({ queryKey: ["feedback-status", workspace] });
  };

  return { query, head, records, refresh };
};
