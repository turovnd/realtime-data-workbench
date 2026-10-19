import { Fragment } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";

import { adapter, ApiError, getSession } from "@/api";
import { useInfiniteScroll } from "@/hooks";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Button,
  Separator,
  Spinner,
} from "@/components/ui";
import { RunFeedback } from "./run-feedback";

type Props = { id: string; open: boolean; online: boolean; running: boolean };

export const RunDetails = ({ id, open, online, running }: Props) => {
  const query = useInfiniteQuery({
    queryKey: ["analysis-run", getSession()?.workspace_id, id],
    queryFn: ({ pageParam, signal }) =>
      adapter.batch(id, pageParam, 10, signal),
    initialPageParam: null as string | null,
    getNextPageParam: page => page.next_cursor,
    enabled: open && online,
    refetchInterval: query => {
      if (!open || !online) return false;
      const pending = query.state.data?.pages.some(page =>
        page.items.some(
          item => item.job?.status === "queued" || item.job?.status === "leased"
        )
      );
      return running || pending ? 3000 : false;
    },
    retry: false,
  });
  const items = query.data?.pages.flatMap(page => page.items) ?? [];
  const loadMore = () => void query.fetchNextPage();
  const sentinel = useInfiniteScroll(
    open && online && !!query.hasNextPage && !query.isFetching && !query.error,
    loadMore
  );

  return (
    <section aria-label="Analysis run details" className="flex flex-col gap-5">
      {!online && (
        <Alert>
          <AlertDescription>
            Reconnect to load the latest run details.
          </AlertDescription>
        </Alert>
      )}
      {query.isPending && online && (
        <p
          role="status"
          className="flex items-center gap-2 text-sm text-muted-foreground"
        >
          <Spinner aria-hidden="true" />
          Loading run details
        </p>
      )}
      {query.error && (
        <Alert variant="destructive">
          <AlertTitle>Couldn’t load run details</AlertTitle>
          <AlertDescription>
            {query.error.message}
            <Button
              variant="outline"
              size="sm"
              disabled={!online || query.isFetching}
              onClick={() =>
                void (query.isFetchNextPageError &&
                !(
                  query.error instanceof ApiError &&
                  [400, 410].includes(query.error.status)
                )
                  ? query.fetchNextPage()
                  : query.refetch())
              }
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}
      {items.map((item, index) => (
        <Fragment key={item.record_id}>
          {index > 0 && <Separator />}
          <RunFeedback item={item} />
        </Fragment>
      ))}
      {query.data && !items.length && (
        <p className="text-sm text-muted-foreground">
          No feedback is available for this run.
        </p>
      )}
      {!!items.length && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">
            Showing {items.length} of {query.data?.pages[0].batch.selected}{" "}
            messages
          </p>
          {query.hasNextPage && (
            <div ref={sentinel}>
              <Button
                variant="outline"
                size="sm"
                onClick={loadMore}
                disabled={!online || query.isFetching}
              >
                {query.isFetchingNextPage && (
                  <Spinner data-icon="inline-start" aria-hidden="true" />
                )}
                Load more messages
              </Button>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
