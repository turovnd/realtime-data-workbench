import { useState, useSyncExternalStore } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type InfiniteData,
} from "@tanstack/react-query";
import { adapter } from "@/lib/api/client";
import {
  snapshotSchema,
  type ConfigVersion,
  type FeedFilters,
  type FeedPage,
  type Snapshot,
} from "@/lib/api/contracts";
import { getSession } from "@/lib/api/auth";
const subscribeOnline = (listener: () => void) => {
  window.addEventListener("online", listener);
  window.addEventListener("offline", listener);
  return () => {
    window.removeEventListener("online", listener);
    window.removeEventListener("offline", listener);
  };
};
const savedKey = () =>
  `feedback-desk-offline:${getSession()?.workspace_id ?? "none"}`;
export const readSaved = (): { snapshot: Snapshot; savedAt: string } | null => {
  try {
    const value = JSON.parse(
      localStorage.getItem(savedKey()) ?? "null",
    ) as unknown;
    if (
      !value ||
      typeof value !== "object" ||
      !("snapshot" in value) ||
      !("savedAt" in value) ||
      typeof value.savedAt !== "string"
    )
      return null;
    return {
      snapshot: snapshotSchema.parse(value.snapshot),
      savedAt: value.savedAt,
    };
  } catch {
    return null;
  }
};
export const useWorkbench = (filters: FeedFilters) => {
  const client = useQueryClient();
  const online = useSyncExternalStore(subscribeOnline, () => navigator.onLine);
  const [paused, setPaused] = useState(false);
  const [saved, setSaved] = useState(readSaved);
  const filterKey = JSON.stringify(filters);
  const [view, setView] = useState({ filterKey, generation: 0 });
  if (view.filterKey !== filterKey)
    setView({ filterKey, generation: view.generation + 1 });
  const workspace = getSession()?.workspace_id ?? "none";
  const key = ["feedback", workspace, filters, view.generation] as const;
  const query = useInfiniteQuery({
    queryKey: key,
    initialPageParam: null as string | null,
    queryFn: async ({ signal, pageParam }) => {
      const previous =
        client.getQueryData<InfiniteData<FeedPage, string | null>>(key);
      const cursor = pageParam ?? previous?.pages[0]?.refresh_cursor ?? null;
      return adapter.page(filters, cursor, 12, signal);
    },
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    enabled: online,
    refetchInterval: paused ? false : 3000,
    retry: false,
  });
  const status = useQuery({
    queryKey: ["feedback-status", workspace],
    queryFn: ({ signal }) => adapter.status(signal),
    enabled: online,
    refetchInterval: paused ? false : 3000,
    retry: 1,
  });
  const head = query.data?.pages[0];
  const records = [
    ...new Map(
      query.data?.pages
        .flatMap((page) => page.records)
        .map((row) => [row.id, row]),
    ).values(),
  ];
  const snapshot: Snapshot | undefined = head
    ? {
        workspace_id: head.workspace_id,
        cursor: Math.max(
          ...(query.data?.pages.map((page) => page.revision) ?? [0]),
        ),
        records,
        batches: status.data?.batches ?? [],
        mode: adapter.mode,
      }
    : undefined;
  const refresh = () => {
    setView((value) => ({ ...value, generation: value.generation + 1 }));
    void client.invalidateQueries({ queryKey: ["feedback-status", workspace] });
  };
  const mutation = useMutation({
    mutationFn: async (
      action:
        | { type: "simulate" }
        | { type: "backfill"; ids: string[]; config: ConfigVersion }
        | { type: "retry" | "cancel"; id: string },
    ) => {
      if (!online) throw new Error("Reconnect before changing the workspace.");
      if (action.type === "simulate") await adapter.simulate();
      else if (action.type === "backfill")
        await adapter.backfill(action.ids, action.config);
      else if (action.type === "retry") await adapter.retry(action.id);
      else await adapter.cancel(action.id);
    },
    onSuccess: (_data, action) => {
      if (action.type === "simulate") refresh();
      else void client.invalidateQueries({ queryKey: key });
      void client.invalidateQueries({
        queryKey: ["feedback-status", workspace],
      });
    },
  });
  const save = () => {
    if (!snapshot) return;
    const value = { snapshot, savedAt: new Date().toISOString() };
    localStorage.setItem(savedKey(), JSON.stringify(value));
    setSaved(value);
  };
  const clearSaved = () => {
    localStorage.removeItem(savedKey());
    setSaved(null);
  };
  return {
    query,
    status,
    mutation,
    data: online ? snapshot : saved?.snapshot,
    online,
    paused,
    setPaused,
    saved,
    save,
    clearSaved,
    mode: adapter.mode,
    refresh,
    hasNew: !!head && (status.data?.latest_sequence ?? 0) > head.watermark,
    total: head?.total ?? 0,
  };
};

export type WorkbenchState = ReturnType<typeof useWorkbench>;
