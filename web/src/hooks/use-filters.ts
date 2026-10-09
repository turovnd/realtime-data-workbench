import { useSyncExternalStore } from "react";
import { feedFiltersSchema } from "@/lib/api/contracts";
const subscribe = (listener: () => void) => {
  window.addEventListener("popstate", listener);
  return () => window.removeEventListener("popstate", listener);
};
export const useFilters = () => {
  const search = useSyncExternalStore(subscribe, () => window.location.search);
  const params = new URLSearchParams(search);
  const parsed = feedFiltersSchema.safeParse({
    q: params.get("q") ?? "",
    status: params.get("status") ?? "all",
    topic: params.get("topic") ?? "all",
  });
  const filters = parsed.success
    ? parsed.data
    : { q: "", status: "all" as const, topic: "all" as const };
  const set = (key: string, value: string) => {
    const next = new URLSearchParams(window.location.search);
    next.delete("page");
    if (value && value !== "all") next.set(key, value);
    else next.delete(key);
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}?${next}`,
    );
    window.dispatchEvent(new PopStateEvent("popstate"));
  };
  return { ...filters, search: filters.q, set };
};

export type FilterState = ReturnType<typeof useFilters>;
