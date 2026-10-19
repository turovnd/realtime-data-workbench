import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

import { isAiOutput, type BatchItem } from "@/api";
import {
  formatAnalysisError,
  statusLabels,
  topics,
} from "@/components/feedback";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
} from "@/components/ui";

type Props = { item: BatchItem };

export const RunFeedback = ({ item }: Props) => {
  const { job, output } = item;
  const ai = isAiOutput(output ?? undefined);

  return (
    <article
      aria-label={`Feedback #${item.sequence}`}
      className="flex flex-col gap-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-medium">Feedback #{item.sequence}</h3>
          <Badge
            variant={job?.status === "failed" ? "destructive" : "secondary"}
          >
            {job
              ? job.status === "succeeded" && !ai
                ? "Sample analysis"
                : statusLabels[job.status]
              : "Not started"}
          </Badge>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link
            to={`/feedback/${item.record_id}`}
            aria-label={`Open feedback #${item.sequence}`}
          >
            Open feedback
            <ArrowUpRight data-icon="inline-end" />
          </Link>
        </Button>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex min-w-0 flex-col gap-2">
          <h4 className="text-xs font-medium text-muted-foreground">
            Customer message · {item.channel}
          </h4>
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {item.text}
          </p>
        </div>
        <div className="flex min-w-0 flex-col gap-3">
          <h4 className="text-xs font-medium text-muted-foreground">
            Result from this run
          </h4>
          {output ? (
            <>
              <p className="break-words text-sm leading-relaxed">
                {output.summary}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{topics[output.topic]}</Badge>
                <span className="text-xs text-muted-foreground">
                  {ai
                    ? `AI · ${output.provider.replace("openrouter/", "")}`
                    : "Sample analysis"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {new Date(output.created_at).toLocaleString(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
                {job && job.attempts > 1 ? ` · ${job.attempts} attempts` : ""}
              </p>
            </>
          ) : job?.error ? (
            <Alert variant="destructive">
              <AlertTitle>Analysis couldn’t finish</AlertTitle>
              <AlertDescription>
                {formatAnalysisError(job.error)}
              </AlertDescription>
            </Alert>
          ) : (
            <p className="text-sm text-muted-foreground">
              {job?.status === "cancelled"
                ? "This message was cancelled before a result was saved."
                : job?.status === "failed"
                  ? "No result was saved. Open the feedback to try again."
                  : "The result will appear here when processing finishes."}
            </p>
          )}
        </div>
      </div>
    </article>
  );
};
