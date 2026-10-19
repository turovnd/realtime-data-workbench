import { useSearchParams } from "react-router-dom";

import { feedFiltersSchema } from "@/api";

export const useFilters = () => {
  const [params, setParams] = useSearchParams();
  const parsed = feedFiltersSchema.safeParse({
    q: params.get("q") ?? "",
    status: params.get("status") ?? "all",
    topic: params.get("topic") ?? "all",
  });
  const filters = parsed.success
    ? parsed.data
    : { q: "", status: "all" as const, topic: "all" as const };

  const set = (key: string, value: string) => {
    setParams(
      previous => {
        const next = new URLSearchParams(previous);
        next.delete("page");

        if (value && value !== "all") next.set(key, value);
        else next.delete(key);

        return next;
      },
      { replace: key === "q" }
    );
  };

  const clear = () => setParams({}, { replace: true });

  return { ...filters, search: filters.q, set, clear };
};

export type FilterState = ReturnType<typeof useFilters>;
