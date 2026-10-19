import { useRef, useState } from "react";
import { Plus, RefreshCw, Sparkles, WifiOff, X } from "lucide-react";

import { currentJob, filterRecords } from "@/api";
import { useFeedbackSelection, useFilters, useWorkbench } from "@/hooks";
import { Feed, Filter, Summary } from "@/components/feedback";
import { PageLoading } from "@/components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Button,
  Spinner,
} from "@/components/ui";
import { AddFeedback } from "./add-feedback";

export const FeedbackPage = () => {
  const filters = useFilters();
  const state = useWorkbench({
    q: filters.search,
    status: filters.status,
    topic: filters.topic,
  });
  const [adding, setAdding] = useState(false);
  const addButton = useRef<HTMLButtonElement>(null);
  const loaded = state.data?.records ?? [];
  const rows = state.online
    ? loaded
    : filterRecords(loaded, filters.search, filters.status, filters.topic);
  const selection = useFeedbackSelection(
    rows,
    JSON.stringify([filters.search, filters.status, filters.topic])
  );
  const eligible = rows.filter(
    record =>
      selection.selected.has(record.id) &&
      !record.jobs.some(job => job.config === "v2") &&
      currentJob(record)?.status === "succeeded"
  );
  const filtered =
    !!filters.search || filters.status !== "all" || filters.topic !== "all";

  const analyze = () =>
    state.mutation.mutate(
      {
        type: "backfill",
        ids: eligible.map(record => record.id),
        config: "v2",
      },
      { onSuccess: selection.clear }
    );

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">Feedback</h1>
          <p className="text-sm text-muted-foreground">
            Understand what your customers are telling you.
          </p>
        </div>
        <Button
          ref={addButton}
          onClick={() => setAdding(true)}
          disabled={!state.online}
        >
          <Plus data-icon="inline-start" />
          Add feedback
        </Button>
      </div>
      <Summary
        status={state.status.data}
        onAttention={() => filters.set("status", "failed")}
      />
      {!state.online && (
        <Alert>
          <WifiOff />
          <AlertTitle>You’re offline</AlertTitle>
          <AlertDescription>
            {state.saved
              ? "Showing your saved feedback. Reconnect to add or analyze messages."
              : "Reconnect to load your feedback."}
          </AlertDescription>
        </Alert>
      )}
      <Filter filters={filters} />
      {state.hasNew && (
        <Button
          variant="outline"
          className="self-start"
          onClick={() => {
            selection.clear();
            state.refresh();
          }}
        >
          <RefreshCw data-icon="inline-start" />
          Show new feedback
        </Button>
      )}
      {selection.selected.size > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/40 px-4 py-3">
          <span className="text-sm font-medium">
            {selection.selected.size} selected
          </span>
          <Button
            size="sm"
            disabled={
              !eligible.length ||
              state.mutation.isPending ||
              !state.online ||
              state.mode === "browser-demo"
            }
            onClick={analyze}
          >
            {state.mutation.isPending ? (
              <Spinner data-icon="inline-start" aria-hidden="true" />
            ) : (
              <Sparkles data-icon="inline-start" />
            )}
            {state.mutation.isPending
              ? "Starting…"
              : `Analyze selected (${eligible.length})`}
          </Button>
          <Button variant="ghost" size="sm" onClick={selection.clear}>
            <X data-icon="inline-start" />
            Clear selection
          </Button>
        </div>
      )}
      {state.query.error && (
        <Alert variant="destructive">
          <AlertTitle>We couldn’t load feedback</AlertTitle>
          <AlertDescription>
            {state.query.error.message}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                selection.clear();
                state.refresh();
              }}
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}
      {state.mutation.error && (
        <Alert variant="destructive">
          <AlertDescription>{state.mutation.error.message}</AlertDescription>
        </Alert>
      )}
      {state.query.isPending && state.online ? (
        <PageLoading label="Loading feedback" embedded />
      ) : !state.query.error || rows.length ? (
        <Feed
          records={rows}
          total={state.online ? state.total : rows.length}
          selected={selection.selected}
          onSelect={selection.select}
          onSelectLoaded={selection.selectLoaded}
          hasMore={!!state.query.hasNextPage}
          loadingMore={state.query.isFetchingNextPage}
          onLoadMore={() => void state.query.fetchNextPage()}
          disabled={!state.online}
          filtered={filtered}
          onClear={() => {
            filters.clear();
            selection.clear();
          }}
          onAdd={() => setAdding(true)}
        />
      ) : null}
      {state.online && rows.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <Button variant="ghost" size="sm" onClick={state.save}>
            Save for offline
          </Button>
          {state.saved && (
            <>
              <span>
                Saved{" "}
                {new Date(state.saved.savedAt).toLocaleTimeString(undefined, {
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </span>
              <Button variant="ghost" size="sm" onClick={state.clearSaved}>
                Remove saved copy
              </Button>
            </>
          )}
        </div>
      )}
      <AddFeedback
        open={adding}
        onOpenChange={setAdding}
        onCloseFocus={() => addButton.current?.focus()}
      />
    </>
  );
};
