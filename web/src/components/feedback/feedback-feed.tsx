import { Pause, Play, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FeedbackFilters } from "@/components/feedback/feedback-filters";
import { FeedbackTable } from "@/components/feedback/feedback-table";
import type { WorkbenchState } from "@/hooks/use-workbench";
import type { FilterState } from "@/hooks/use-filters";
import type { FeedbackRecord } from "@/lib/api/contracts";

type FeedbackFeedProps = {
  workbench: WorkbenchState;
  filters: FilterState;
  rows: FeedbackRecord[];
  selected: Set<string>;
  select: (id: string) => void;
  selectLoaded: () => void;
  clearSelection: () => void;
  onInspect: (id: string) => void;
};
export const FeedbackFeed = ({
  workbench,
  filters,
  rows,
  selected,
  select,
  selectLoaded,
  clearSelection,
  onInspect,
}: FeedbackFeedProps) => (
  <Card id="feedback" className="min-w-0">
    <CardHeader>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <CardTitle>Incoming feedback</CardTitle>
          <CardDescription>
            Filters stay fixed while you browse. Refresh to include new matches.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          aria-pressed={workbench.paused}
          onClick={() => workbench.setPaused(!workbench.paused)}
        >
          {workbench.paused ? (
            <Play data-icon="inline-start" />
          ) : (
            <Pause data-icon="inline-start" />
          )}
          {workbench.paused ? "Resume updates" : "Pause updates"}
        </Button>
      </div>
    </CardHeader>
    <CardContent className="flex flex-col gap-4">
      <FeedbackFilters {...filters} />
      {workbench.hasNew && (
        <Alert>
          <AlertTitle>New feedback is available</AlertTitle>
          <AlertDescription>
            <Button variant="outline" onClick={workbench.refresh}>
              Show new feedback
            </Button>
          </AlertDescription>
        </Alert>
      )}
      {selected.size > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            {selected.size} selected across this workspace (maximum 100)
          </p>
          <Button variant="ghost" size="sm" onClick={() => clearSelection()}>
            Clear selection
          </Button>
        </div>
      )}
      {workbench.query.isPending && workbench.online ? (
        <div className="flex flex-col gap-3" aria-label="Loading feedback">
          {[1, 2, 3].map((id) => (
            <Skeleton key={id} className="h-14 w-full" />
          ))}
        </div>
      ) : (
        <FeedbackTable
          records={rows}
          selected={selected}
          onSelect={select}
          onSelectVisible={selectLoaded}
          onInspect={(row) => onInspect(row.id)}
          total={workbench.online ? workbench.total : rows.length}
          hasMore={workbench.query.hasNextPage}
          loadingMore={workbench.query.isFetchingNextPage}
          onLoadMore={() => {
            void workbench.query.fetchNextPage({ cancelRefetch: false });
          }}
          disabled={
            !workbench.online ||
            workbench.query.isFetching ||
            workbench.query.isError
          }
        />
      )}
    </CardContent>
    <CardFooter className="justify-between gap-3">
      <span className="text-xs text-muted-foreground">
        {!workbench.online
          ? "Saved feedback"
          : workbench.paused
            ? "Updates paused"
            : "Processing updates every few seconds"}
      </span>
      <Button
        size="sm"
        variant="ghost"
        disabled={!workbench.online || workbench.query.isFetching}
        onClick={workbench.refresh}
      >
        <RefreshCw data-icon="inline-start" /> Refresh view
      </Button>
    </CardFooter>
  </Card>
);
