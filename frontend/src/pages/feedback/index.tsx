import { useRef, useState } from "react";
import { Plus, RefreshCw, Sparkles, WifiOff, X } from "lucide-react";

import { currentJob, filterRecords, getSession } from "@/api";
import { useAnalyzeSelection } from "@/api/feedback";
import {
  Feed,
  Filter,
  Summary,
  useFeedbackSelection,
  useFilters,
} from "@/components/feedback";
import { PageLoading } from "@/components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Button,
  Spinner,
} from "@/components/ui";
import { AddFeedback } from "./add-feedback";
import { useFeedback } from "./use-feedback";
import { ExampleCard } from "./example-card";
import { exampleFeedback } from "./example-feedback";

export const FeedbackPage = () => {
  const filters = useFilters();
  const analysis = useAnalyzeSelection();
  const state = useFeedback({
    q: filters.search,
    status: filters.status,
    topic: filters.topic,
  });
  const [adding, setAdding] = useState<"blank" | "example" | null>(null);
  const addButton = useRef<HTMLButtonElement>(null);
  const dialogTrigger = useRef<HTMLButtonElement | null>(null);
  const demo = getSession()?.kind !== "account";
  const liveAnalysis =
    state.status.data?.provider.startsWith("openrouter/") ?? false;
  const availabilityKnown =
    state.mode === "browser-demo" || !!state.status.data;

  const openBlank = () => {
    if (!state.online || !availabilityKnown) return;

    dialogTrigger.current = addButton.current;
    setAdding("blank");
  };
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
    analysis.analyze(
      eligible.map(record => record.id),
      "v2",
      selection.clear
    );

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">Feedback</h1>
          <p className="text-sm text-muted-foreground">
            Review customer messages and check AI insights against their words.
          </p>
        </div>
        <Button
          ref={addButton}
          onClick={openBlank}
          disabled={!state.online || !availabilityKnown}
        >
          <Plus data-icon="inline-start" />
          Add feedback
        </Button>
      </div>
      {demo && (
        <ExampleCard
          liveAnalysis={liveAnalysis}
          disabled={!state.online || !availabilityKnown}
          onTry={event => {
            dialogTrigger.current = event.currentTarget;
            setAdding("example");
          }}
        />
      )}
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
      {state.status.error && !availabilityKnown && (
        <Alert variant="destructive">
          <AlertTitle>Analysis status unavailable</AlertTitle>
          <AlertDescription>
            We couldn’t check whether new feedback can be analyzed.
            <Button
              variant="outline"
              size="sm"
              onClick={() => void state.status.refetch()}
            >
              Try again
            </Button>
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
              analysis.pending ||
              !state.online ||
              state.mode === "browser-demo"
            }
            onClick={analyze}
          >
            {analysis.pending ? (
              <Spinner data-icon="inline-start" aria-hidden="true" />
            ) : (
              <Sparkles data-icon="inline-start" />
            )}
            {analysis.pending
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
      {analysis.error && (
        <Alert variant="destructive">
          <AlertDescription>{analysis.error.message}</AlertDescription>
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
          disabled={!state.online || !availabilityKnown}
          filtered={filtered}
          onClear={() => {
            filters.clear();
            selection.clear();
          }}
          onAdd={openBlank}
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
      {adding && (
        <AddFeedback
          initialText={adding === "example" ? exampleFeedback.text : ""}
          liveAnalysis={liveAnalysis}
          onOpenChange={open => {
            if (!open) setAdding(null);
          }}
          onCloseFocus={() => dialogTrigger.current?.focus()}
        />
      )}
    </>
  );
};
