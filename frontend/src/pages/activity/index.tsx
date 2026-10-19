import { Link } from "react-router-dom";
import { Activity, ArrowRight } from "lucide-react";

import { useInfiniteScroll } from "@/hooks";
import { PageLoading, PageMessage } from "@/components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Button,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Spinner,
} from "@/components/ui";
import { FeedbackRunCard } from "./feedback-run-card";
import { RunCard } from "./run-card";
import { useActivity } from "./use-activity";

export const ActivityPage = () => {
  const { query, items, online, cancel, cancelRun, retry, total, hasOlder } =
    useActivity();
  const loadMore = () => void query.fetchNextPage();
  const sentinel = useInfiniteScroll(
    online && !!query.hasNextPage && !query.isFetching && !query.error,
    loadMore
  );

  return (
    <>
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">Activity</h1>
        <p className="text-sm text-muted-foreground">
          Track analysis of new feedback, individual messages and selected
          groups.
        </p>
        {hasOlder && (
          <p className="text-sm text-muted-foreground">
            Showing the 6,000 most recent analysis runs.
          </p>
        )}
      </div>
      {!online && query.data && (
        <Alert>
          <AlertDescription>
            You’re offline. Reconnect to see the latest activity.
          </AlertDescription>
        </Alert>
      )}
      {query.error && query.data && (
        <Alert variant="destructive">
          <AlertTitle>Couldn’t update activity</AlertTitle>
          <AlertDescription>
            Your loaded activity is still shown. Try again to get the latest
            runs.
            <Button
              variant="outline"
              size="sm"
              disabled={!online || query.isFetching}
              onClick={retry}
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}
      {cancel.error && (
        <Alert variant="destructive">
          <AlertDescription>{cancel.error.message}</AlertDescription>
        </Alert>
      )}
      {query.isPending && online ? (
        <PageLoading label="Loading activity" embedded />
      ) : !query.data ? (
        <PageMessage
          title={
            online
              ? "We couldn’t load activity"
              : "Activity is unavailable offline"
          }
          description={
            online
              ? "Check your connection and try again."
              : "Reconnect to see your analysis runs."
          }
          backTo="/feedback"
        >
          {online && (
            <Button variant="outline" onClick={retry}>
              Try again
            </Button>
          )}
        </PageMessage>
      ) : !items.length ? (
        <Empty className="min-h-80 rounded-xl border bg-card">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Activity />
            </EmptyMedia>
            <EmptyTitle>No analysis runs yet</EmptyTitle>
            <EmptyDescription>
              Add feedback or start an analysis from your inbox. Its progress
              will appear here.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild>
              <Link to="/feedback">
                Open inbox
                <ArrowRight data-icon="inline-end" />
              </Link>
            </Button>
          </EmptyContent>
        </Empty>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map(item =>
            item.kind === "batch" ? (
              <RunCard
                key={`batch:${item.id}`}
                batch={item.batch}
                online={online}
                cancelling={cancel.isPending}
                onCancel={() => cancelRun(item.id)}
              />
            ) : (
              <FeedbackRunCard
                key={`feedback:${item.id}`}
                item={item.feedback}
              />
            )
          )}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">
              Showing {items.length} of {total} activities
            </p>
            {query.hasNextPage && (
              <div ref={sentinel}>
                <Button
                  variant="outline"
                  onClick={loadMore}
                  disabled={!online || query.isFetching || !!query.error}
                >
                  {query.isFetchingNextPage && (
                    <Spinner data-icon="inline-start" aria-hidden="true" />
                  )}
                  Load more activity
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
