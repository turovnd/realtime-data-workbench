import { useState } from "react";
import type { FeedbackRecord } from "@/lib/api/contracts";

export const useFeedbackSelection = (rows: FeedbackRecord[]) => {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const select = (id: string) =>
    setSelected((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else if (next.size < 100) next.add(id);
      return next;
    });
  const selectLoaded = () =>
    setSelected((previous) => {
      const next = new Set(previous);
      const remove = rows.every((row) => next.has(row.id));
      rows.forEach((row) => {
        if (remove) next.delete(row.id);
        else if (next.size < 100) next.add(row.id);
      });
      return next;
    });
  return {
    selected,
    select,
    selectLoaded,
    clear: () => setSelected(new Set()),
  };
};
