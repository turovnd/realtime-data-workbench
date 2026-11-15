import { CircleCheck, Quote, Sparkles } from "lucide-react";

import { isAiOutput } from "@/api";
import type { AnalysisState } from "@/api/feedback";
import { formatAnalysisError, topics } from "@/components/feedback";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Skeleton,
  Spinner,
} from "@/components/ui";
import { AnalysisProgress } from "./analysis-progress";

type Props = { analysis: AnalysisState };

export const AnalysisCard = ({ analysis }: Props) => {
  const { output, job, action, busy, completed, previous, preview } = analysis;
  const failed =
    !action.isPending &&
    (job?.status === "failed" || job?.status === "cancelled");
  const ai = isAiOutput(output);
  const aiJob = job?.provider?.startsWith("openrouter/");

  return (
    <Card aria-busy={busy}>
      <CardHeader>
        <CardTitle>Analysis</CardTitle>
        <CardDescription>
          {ai
            ? "Check the summary and quotes against the original message."
            : "Run AI analysis to get a fresh summary of this message."}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {analysis.samplePending && (
          <Alert role="status">
            <Spinner aria-hidden="true" />
            <AlertTitle>Preparing sample feedback</AlertTitle>
            <AlertDescription>
              You can run AI analysis once the sample is ready.
            </AlertDescription>
          </Alert>
        )}
        {busy && !analysis.samplePending && (
          <AnalysisProgress
            stage={
              action.isPending
                ? "starting"
                : job?.status === "leased"
                  ? "leased"
                  : "queued"
            }
            submittedAt={action.submittedAt}
          />
        )}
        {action.error && !busy && (
          <Alert variant="destructive">
            <AlertTitle>Couldn’t start AI analysis</AlertTitle>
            <AlertDescription>{action.error.message}</AlertDescription>
          </Alert>
        )}
        {failed && !action.error && (
          <Alert variant="destructive">
            <AlertTitle>
              {aiJob ? "AI analysis failed" : "Sample analysis unavailable"}
            </AlertTitle>
            <AlertDescription>
              {aiJob
                ? formatAnalysisError(job?.error)
                : "Run AI analysis to generate a fresh result from the original message."}
            </AlertDescription>
          </Alert>
        )}
        {completed && !busy && !action.error && (
          <Alert role="status">
            <CircleCheck />
            <AlertTitle>Analysis complete</AlertTitle>
            <AlertDescription>The new result is ready below.</AlertDescription>
          </Alert>
        )}
        {preview && (
          <p className="text-sm text-muted-foreground">
            Connect the API to run AI analysis.
          </p>
        )}
        {output ? (
          <section
            aria-label={previous ? "Previous result" : "Analysis result"}
            className="flex flex-col gap-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              {previous && (
                <h2 className="text-sm font-medium">Previous result</h2>
              )}
              <Badge variant={ai ? "secondary" : "outline"}>
                {ai ? "AI analysis" : "Sample analysis"}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">{topics[output.topic]}</Badge>
              <Badge variant="outline">
                {
                  {
                    issue: "Issue",
                    request: "Feature request",
                    praise: "Positive feedback",
                    unclear: "Needs review",
                  }[output.intent]
                }
              </Badge>
            </div>
            <p className="text-sm leading-relaxed">{output.summary}</p>
            <div className="flex flex-col gap-3">
              <h2 className="text-sm font-medium">Supporting quotes</h2>
              {output.evidence.map(quote => (
                <blockquote
                  key={quote}
                  className="flex gap-3 rounded-lg bg-muted/50 p-4 text-sm leading-relaxed"
                >
                  <Quote className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  <span>“{quote}”</span>
                </blockquote>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              {ai
                ? `AI · ${output.provider.replace("openrouter/", "")} · `
                : "Sample · "}
              {new Date(output.created_at).toLocaleString(undefined, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </p>
          </section>
        ) : busy ? (
          <div className="flex flex-col gap-3" aria-label="Preparing analysis">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        ) : (
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <Sparkles />
              </EmptyMedia>
              <EmptyTitle>No AI analysis yet</EmptyTitle>
              <EmptyDescription>
                Analyze this message to identify its main topic, intent and
                supporting quotes.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </CardContent>
    </Card>
  );
};
