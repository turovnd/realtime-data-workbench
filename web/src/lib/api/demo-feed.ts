import { createDemoAdapter } from "./demo";
import { currentJob, filterRecords, type FeedAdapter } from "./contracts";

export const createDemoFeedAdapter = (): FeedAdapter => {
  const demo = createDemoAdapter();
  const views = new Map<
    string,
    { ids: string[]; filters: string; watermark: number }
  >();
  let id = 0;
  return {
    ...demo,
    page: async (filters, cursor, limit, signal) => {
      const snapshot = await demo.snapshot(signal);
      let viewKey: string;
      let before: number;
      if (cursor) {
        const parts = cursor.split(".");
        viewKey = parts[0];
        before = Number(parts[1]);
      } else {
        viewKey = `preview-${++id}`;
        before =
          Math.max(0, ...snapshot.records.map((row) => row.sequence)) + 1;
        views.set(viewKey, {
          ids: filterRecords(
            snapshot.records,
            filters.q,
            filters.status,
            filters.topic,
          ).map((row) => row.id),
          filters: JSON.stringify(filters),
          watermark: before - 1,
        });
        if (views.size > 20) views.delete(views.keys().next().value ?? "");
      }
      const view = views.get(viewKey);
      if (!view || view.filters !== JSON.stringify(filters))
        throw new Error("This view expired. Refresh to continue.");
      const matching = snapshot.records.filter(
        (row) => view.ids.includes(row.id) && row.sequence < before,
      );
      const rows = matching.slice(0, limit);
      return {
        workspace_id: snapshot.workspace_id,
        records: rows,
        next_cursor:
          matching.length > limit
            ? `${viewKey}.${rows.at(-1)?.sequence}`
            : null,
        refresh_cursor: `${viewKey}.${view.watermark + 1}`,
        watermark: view.watermark,
        revision: snapshot.cursor,
        total: view.ids.length,
      };
    },
    status: async (signal) => {
      const snapshot = await demo.snapshot(signal);
      return {
        workspace_id: snapshot.workspace_id,
        revision: snapshot.cursor,
        latest_sequence: Math.max(
          0,
          ...snapshot.records.map((row) => row.sequence),
        ),
        received: snapshot.records.length,
        enriched: snapshot.records.filter(
          (row) => currentJob(row)?.status === "succeeded",
        ).length,
        failed: snapshot.records.filter(
          (row) => currentJob(row)?.status === "failed",
        ).length,
        batches: snapshot.batches.slice(-10).reverse(),
        provider: "browser-fixture/1",
      };
    },
  };
};
