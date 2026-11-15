import { useState } from "react";

import { adapter, createSavedFeedbackStorage, getSession } from "@/api";
import type { FeedFilters, Snapshot } from "@/api";
import { useFeed, useFeedbackStatus } from "@/api/feedback";
import { useOnline } from "@/hooks";

export const useFeedback = (filters: FeedFilters) => {
  const online = useOnline();
  const workspace = getSession()?.workspace_id ?? "none";
  const storage = createSavedFeedbackStorage(localStorage, workspace);
  const [saved, setSaved] = useState(storage.read);
  const feed = useFeed(filters, online);
  const status = useFeedbackStatus(online);
  const { query, head, records, refresh } = feed;

  const snapshot: Snapshot | undefined = head
    ? {
        workspace_id: head.workspace_id,
        cursor: Math.max(
          ...(query.data?.pages.map(page => page.revision) ?? [0])
        ),
        records,
        batches: status.data?.batches ?? [],
        mode: adapter.mode,
      }
    : undefined;

  const save = () => {
    if (!snapshot) {
      return;
    }

    setSaved(storage.save(snapshot));
  };

  const clearSaved = () => {
    storage.clear();
    setSaved(null);
  };

  return {
    query,
    status,
    data: online ? snapshot : saved?.snapshot,
    online,
    saved,
    save,
    clearSaved,
    mode: adapter.mode,
    refresh,
    hasNew: !!head && (status.data?.latest_sequence ?? 0) > head.watermark,
    total: head?.total ?? 0,
  };
};
