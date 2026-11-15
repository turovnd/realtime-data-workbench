import { useState } from "react";
import type { FeedbackRecord } from "@/api";

export const useFeedbackSelection = (rows: FeedbackRecord[], scope = "all") => {
  const [selection, setSelection] = useState({ scope, ids: new Set<string>() });

  if (selection.scope !== scope) setSelection({ scope, ids: new Set() });

  const selected =
    selection.scope === scope ? selection.ids : new Set<string>();

  const setSelected = (
    update: Set<string> | ((previous: Set<string>) => Set<string>)
  ) =>
    setSelection(previous => ({
      scope,
      ids:
        typeof update === "function"
          ? update(previous.scope === scope ? previous.ids : new Set())
          : update,
    }));

  const select = (id: string) =>
    setSelected(previous => {
      const next = new Set(previous);

      if (next.has(id)) next.delete(id);
      else if (next.size < 100) next.add(id);

      return next;
    });

  const selectLoaded = () =>
    setSelected(previous => {
      const next = new Set(previous);
      const remove = rows.every(row => next.has(row.id));

      rows.forEach(row => {
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
