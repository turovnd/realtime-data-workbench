import { Link, useLocation, useParams } from "react-router-dom";
import { ArrowLeft, RotateCcw, Sparkles } from "lucide-react";

import { ApiError, isAiOutput } from "@/api";
import { useAnalysis } from "@/hooks";
import { Status } from "@/components/feedback";
import { PageLoading, PageMessage } from "@/components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Button,
  Spinner,
} from "@/components/ui";
import { FeedbackCard } from "./feedback-card";
import { AnalysisCard } from "./analysis-card";

export const DetailsPage = () => {
  const { id = "" } = useParams();
  return <Details key={id} id={id} />;
};

const Details = ({ id }: { id: string }) => {
  const location = useLocation();
  const analysis = useAnalysis(id);
  const { query, record, online, action, busy, job, output, preview } =
    analysis;
  const back = `/feedback${location.search}`;
  const failed =
    !!action.error || job?.status === "failed" || job?.status === "cancelled";

  const actionLabel = () => {
    if (action.isPending) return "Starting…";
    if (analysis.samplePending) return "Preparing sample…";
    if (busy) return job?.status === "leased" ? "Analyzing…" : "Queued…";
    if (failed) return "Try again";
    return isAiOutput(output) ? "Analyze again" : "Analyze with AI";
  };

  if (query.isPending && online)
    return <PageLoading label="Loading feedback" embedded />;
  if (query.error instanceof ApiError && query.error.status === 404)
    return (
      <PageMessage
        title="Feedback not found"
        description="This feedback is no longer available in your workspace."
        backTo={back}
      />
    );
  if (!record)
    return (
      <PageMessage
        title={
          online
            ? "We couldn’t load this feedback"
            : "This feedback isn’t saved offline"
        }
        description={
          online
            ? "Check your connection and try again."
            : "Reconnect to open this message."
        }
        backTo={back}
      >
        {online && (
          <Button variant="outline" onClick={() => void query.refetch()}>
            Try again
          </Button>
        )}
      </PageMessage>
    );

  return (
    <>
      <Button asChild variant="ghost" size="sm" className="self-start">
        <Link to={back}>
          <ArrowLeft data-icon="inline-start" />
          Back to feedback
        </Link>
      </Button>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">
            Feedback #{record.sequence}
          </h1>
          <Status record={record} />
        </div>
        <Button onClick={analysis.start} disabled={!online || busy || preview}>
          {busy ? (
            <Spinner data-icon="inline-start" aria-hidden="true" />
          ) : failed ? (
            <RotateCcw data-icon="inline-start" />
          ) : (
            <Sparkles data-icon="inline-start" />
          )}
          {actionLabel()}
        </Button>
      </div>
      {!online && (
        <Alert>
          <AlertTitle>You’re offline</AlertTitle>
          <AlertDescription>
            Showing saved feedback. Reconnect to run AI analysis.
          </AlertDescription>
        </Alert>
      )}
      {query.error && (
        <Alert variant="destructive">
          <AlertTitle>Updates unavailable</AlertTitle>
          <AlertDescription>
            Your last loaded feedback is still shown. Reconnect to get the
            latest status.
          </AlertDescription>
        </Alert>
      )}
      <div className="grid items-start gap-6 xl:grid-cols-2">
        <FeedbackCard record={record} />
        <AnalysisCard analysis={analysis} />
      </div>
    </>
  );
};
