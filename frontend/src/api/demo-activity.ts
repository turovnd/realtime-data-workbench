import type { ActivityItem, Adapter, FeedAdapter, Snapshot } from "./contracts";
import { ApiError } from "./errors";

type View = { ids: string[]; expiresAt: number };

const activityItems = (snapshot: Snapshot): ActivityItem[] => [
  ...snapshot.batches
    .slice()
    .reverse()
    .map(batch => ({
      kind: "batch" as const,
      id: batch.id,
      batch,
    })),
  ...snapshot.records.flatMap(record =>
    record.jobs
      .slice()
      .reverse()
      .filter(job => job.origin !== "backfill")
      .map(job => ({
        kind: "feedback" as const,
        id: job.id,
        feedback: {
          record_id: record.id,
          sequence: record.sequence,
          text: record.text,
          channel: record.channel,
          job,
          output:
            record.outputs.find(
              output => output.config === job.config && output.run === job.run
            ) ?? null,
        },
      }))
  ),
];

const itemKey = (item: ActivityItem): string => `${item.kind}:${item.id}`;

export const createDemoActivity = (
  readSnapshot: Adapter["snapshot"]
): FeedAdapter["activity"] => {
  const views = new Map<string, View>();

  return async (cursor, limit, signal) => {
    signal?.throwIfAborted();
    if (!Number.isInteger(limit) || limit < 1 || limit > 50)
      throw new ApiError("Activity pages contain 1–50 items.", 400);

    const snapshot = await readSnapshot(signal);
    const items = activityItems(snapshot);
    let id: string;
    let offset = 0;
    let view: View;

    if (cursor) {
      const parts = cursor.split(".");
      id = parts[0];
      offset = Number(parts[1]);
      if (parts.length !== 2 || !Number.isInteger(offset) || offset < 0)
        throw new ApiError("Invalid activity cursor.", 400);
      const previous = views.get(id);
      if (!previous || previous.expiresAt <= Date.now())
        throw new ApiError(
          "This activity view expired. Refresh to continue.",
          410
        );
      if (offset > previous.ids.length)
        throw new ApiError("Invalid activity cursor.", 400);
      view = previous;
    } else {
      id = crypto.randomUUID();
      view = { ids: items.map(itemKey), expiresAt: Date.now() + 600000 };
      views.set(id, view);
      if (views.size > 20) views.delete(views.keys().next().value ?? "");
    }

    const byId = new Map(items.map(item => [itemKey(item), item]));
    const page = view.ids.slice(offset, offset + limit).flatMap(key => {
      const item = byId.get(key);
      return item ? [item] : [];
    });

    return structuredClone({
      items: page,
      next_cursor:
        offset + limit < view.ids.length ? `${id}.${offset + limit}` : null,
      refresh_cursor: `${id}.0`,
      total: view.ids.length,
      has_older: false,
      revision: snapshot.cursor,
    });
  };
};
