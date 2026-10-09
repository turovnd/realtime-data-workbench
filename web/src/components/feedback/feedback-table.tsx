import {
  ArrowUpRight,
  Inbox,
  CheckCircle2,
  Clock,
  AlertCircle,
} from "lucide-react";
import { useInfiniteScroll } from "@/hooks/use-infinite-scroll";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  currentJob,
  currentOutput,
  type FeedbackRecord,
} from "@/lib/api/contracts";
type Props = {
  records: FeedbackRecord[];
  selected: Set<string>;
  onSelect: (id: string) => void;
  onInspect: (record: FeedbackRecord) => void;
  onSelectVisible: () => void;
  total: number;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  disabled: boolean;
};
export const FeedbackTable = ({
  records,
  selected,
  onSelect,
  onInspect,
  onSelectVisible,
  total,
  hasMore,
  loadingMore,
  onLoadMore,
  disabled,
}: Props) => {
  const sentinel = useInfiniteScroll(
    hasMore && !disabled && !loadingMore,
    onLoadMore,
  );
  if (!records.length)
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Inbox />
          </EmptyMedia>
          <EmptyTitle>No feedback in this view</EmptyTitle>
          <EmptyDescription>
            Change the filters, refresh the view, or add synthetic feedback to
            begin.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <Checkbox
                aria-label="Select loaded feedback"
                checked={records.every((row) => selected.has(row.id))}
                onCheckedChange={onSelectVisible}
              />
            </TableHead>
            <TableHead>Feedback</TableHead>
            <TableHead>Topic</TableHead>
            <TableHead>Intent</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>
              <span className="sr-only">Inspect</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {records.map((row) => {
            const output = currentOutput(row);
            const job = currentJob(row);
            const StatusIcon =
              job?.status === "succeeded"
                ? CheckCircle2
                : job?.status === "failed"
                  ? AlertCircle
                  : Clock;
            return (
              <TableRow
                key={row.id}
                data-state={selected.has(row.id) ? "selected" : undefined}
              >
                <TableCell>
                  <Checkbox
                    aria-label={`Select feedback ${row.sequence}`}
                    checked={selected.has(row.id)}
                    onCheckedChange={() => onSelect(row.id)}
                  />
                </TableCell>
                <TableCell className="min-w-60 max-w-96 whitespace-normal">
                  <p>{row.text}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    FB-{String(row.sequence).padStart(3, "0")} · {row.channel} ·{" "}
                    {output?.config ?? "v1"}
                  </p>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{output?.topic ?? "Pending"}</Badge>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground">
                    {output?.intent ?? "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      job?.status === "failed"
                        ? "destructive"
                        : job?.status === "succeeded"
                          ? "secondary"
                          : "outline"
                    }
                  >
                    <StatusIcon />
                    {job?.status === "succeeded"
                      ? "Enriched"
                      : job?.status === "leased"
                        ? "Processing"
                        : (job?.status ?? "Queued")}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`Inspect feedback ${row.sequence}`}
                    onClick={() => onInspect(row)}
                  >
                    <ArrowUpRight />
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <div
        ref={sentinel}
        data-testid="feedback-load-more"
        className="flex flex-wrap items-center justify-between gap-3 border-t p-4"
      >
        <p className="text-xs text-muted-foreground" aria-live="polite">
          Showing {records.length} of {total} matching records · {selected.size}{" "}
          selected
        </p>
        {hasMore ? (
          <Button
            variant="outline"
            onClick={onLoadMore}
            disabled={disabled || loadingMore}
          >
            {loadingMore ? "Loading more…" : "Load more feedback"}
          </Button>
        ) : (
          <span className="text-xs text-muted-foreground">
            All matching feedback loaded
          </span>
        )}
      </div>
    </>
  );
};
