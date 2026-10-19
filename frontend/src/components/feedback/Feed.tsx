import { Link, useLocation } from "react-router-dom";
import { ArrowRight, Inbox, LoaderCircle } from "lucide-react";

import { currentOutput, type FeedbackRecord } from "@/api";
import { useInfiniteScroll } from "@/hooks";
import {
  Badge,
  Button,
  Checkbox,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui";
import { Status } from "./Status";
import { topics } from "./labels";

type Props = {
  records: FeedbackRecord[];
  total: number;
  selected: Set<string>;
  onSelect: (id: string) => void;
  onSelectLoaded: () => void;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  disabled: boolean;
  filtered: boolean;
  onClear: () => void;
  onAdd: () => void;
};

export const Feed = ({
  records,
  total,
  selected,
  onSelect,
  onSelectLoaded,
  hasMore,
  loadingMore,
  onLoadMore,
  disabled,
  filtered,
  onClear,
  onAdd,
}: Props) => {
  const sentinel = useInfiniteScroll(
    hasMore && !disabled && !loadingMore,
    onLoadMore
  );
  const location = useLocation();
  const selectedCount = records.filter(row => selected.has(row.id)).length;

  if (!records.length)
    return (
      <Empty className="min-h-72 rounded-xl border bg-card">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Inbox />
          </EmptyMedia>
          <EmptyTitle>
            {filtered ? "No matching feedback" : "Your inbox is ready"}
          </EmptyTitle>
          <EmptyDescription>
            {filtered
              ? "Try a different search or clear your filters."
              : "Add a customer message to see its topic, summary and supporting quotes."}
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button
            variant={filtered ? "outline" : "default"}
            onClick={filtered ? onClear : onAdd}
            disabled={!filtered && disabled}
          >
            {filtered ? "Clear filters" : "Add your first feedback"}
          </Button>
        </EmptyContent>
      </Empty>
    );

  return (
    <section
      aria-label="Feedback list"
      className="overflow-hidden rounded-xl border bg-card"
    >
      <div className="flex items-center gap-4 border-b px-4 py-3">
        <Checkbox
          aria-label="Select loaded feedback"
          checked={
            selectedCount === records.length
              ? true
              : selectedCount > 0
                ? "indeterminate"
                : false
          }
          onCheckedChange={onSelectLoaded}
          disabled={disabled}
        />
        <p className="text-xs font-medium text-muted-foreground">
          Newest first
        </p>
      </div>
      <ul className="divide-y">
        {records.map(record => {
          const output = currentOutput(record);
          return (
            <li
              key={record.id}
              className="group flex items-start gap-4 px-4 py-5 transition-colors hover:bg-muted/40 data-[selected=true]:bg-muted/50"
              data-selected={selected.has(record.id)}
            >
              <Checkbox
                className="mt-1"
                aria-label={`Select feedback ${record.sequence}`}
                checked={selected.has(record.id)}
                onCheckedChange={() => onSelect(record.id)}
                disabled={disabled}
              />
              <Link
                to={`/feedback/${encodeURIComponent(record.id)}${location.search}`}
                aria-label={`Open feedback ${record.sequence}`}
                className="flex min-w-0 flex-1 items-center gap-4 rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="flex min-w-0 flex-1 flex-col gap-2">
                  <p className="line-clamp-2 text-sm leading-relaxed font-medium">
                    {record.text}
                  </p>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-muted-foreground">
                    <span>
                      #{record.sequence} · {record.channel}
                    </span>
                    <time dateTime={record.ingested_at}>
                      {new Date(record.ingested_at).toLocaleDateString(
                        undefined,
                        { month: "short", day: "numeric" }
                      )}
                    </time>
                    {output && (
                      <Badge variant="outline">{topics[output.topic]}</Badge>
                    )}
                    <span className="sm:hidden">
                      <Status record={record} />
                    </span>
                  </div>
                </div>
                <span className="hidden shrink-0 sm:block">
                  <Status record={record} />
                </span>
                <ArrowRight className="hidden size-4 shrink-0 text-muted-foreground sm:block" />
              </Link>
            </li>
          );
        })}
      </ul>
      <div
        ref={sentinel}
        data-testid="feedback-load-more"
        className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-4"
      >
        <p className="text-xs text-muted-foreground" aria-live="polite">
          Showing {records.length} of {total}
        </p>
        {hasMore ? (
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || loadingMore}
            onClick={onLoadMore}
          >
            {loadingMore && (
              <LoaderCircle className="animate-spin" data-icon="inline-start" />
            )}
            {loadingMore ? "Loading…" : "Load more"}
          </Button>
        ) : (
          <span className="text-xs text-muted-foreground">
            You’re all caught up
          </span>
        )}
      </div>
    </section>
  );
};
