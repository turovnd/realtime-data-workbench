import { CheckCheck, RotateCcw } from "lucide-react";
import type { FeedbackRecord } from "@/lib/api/contracts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

type Props = {
  record: FeedbackRecord | undefined;
  onClose: () => void;
  onRetry: (id: string) => void;
  disabled: boolean;
};
export const RecordInspector = ({
  record,
  onClose,
  onRetry,
  disabled,
}: Props) => (
  <Sheet
    open={!!record}
    onOpenChange={(open) => {
      if (!open) onClose();
    }}
  >
    <SheetContent className="overflow-y-auto sm:max-w-lg">
      <SheetHeader>
        <SheetTitle>Feedback evidence</SheetTitle>
        <SheetDescription>
          Immutable input and every stored enrichment version.
        </SheetDescription>
      </SheetHeader>
      {record && (
        <div className="flex flex-col gap-5 px-5 pb-8">
          <div>
            <div className="text-xs font-medium text-muted-foreground">
              FB-{String(record.sequence).padStart(3, "0")} · {record.channel}
            </div>
            <blockquote className="my-4 text-base leading-relaxed">
              {record.text}
            </blockquote>
            <p className="text-xs text-muted-foreground">
              Received {new Date(record.ingested_at).toLocaleString()}
            </p>
          </div>
          <Separator />
          {record.outputs.length === 0 && (
            <Alert>
              <AlertTitle>No enrichment stored yet</AlertTitle>
              <AlertDescription>
                The original feedback stays available while processing is
                pending or failed.
              </AlertDescription>
            </Alert>
          )}
          {[...record.outputs].reverse().map((output) => (
            <section className="flex flex-col gap-3" key={output.config}>
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Enrichment {output.config}</h3>
                <Badge variant="secondary">
                  <CheckCheck /> Validated
                </Badge>
              </div>
              <div className="flex gap-2">
                <Badge variant="outline">{output.topic}</Badge>
                <Badge variant="outline">{output.intent}</Badge>
              </div>
              <p>{output.summary}</p>
              <div className="flex flex-col gap-2">
                <div className="text-xs font-medium text-muted-foreground">
                  Exact source evidence
                </div>
                {output.evidence.map((quote) => (
                  <blockquote key={quote}>“{quote}”</blockquote>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                {output.provider} · schema 1 ·{" "}
                {new Date(output.created_at).toLocaleTimeString()}
              </p>
              <p className="text-xs text-muted-foreground">
                Valid shape and source quotes do not establish classification
                accuracy.
              </p>
              <Separator />
            </section>
          ))}
          <section className="flex flex-col gap-3">
            <h3 className="font-semibold">Processing history</h3>
            {record.jobs.map((job) => (
              <div className="flex flex-col gap-3" key={job.id}>
                <div className="flex items-center justify-between">
                  <span>
                    {job.config} · {job.origin}
                  </span>
                  <Badge
                    variant={
                      job.status === "failed" ? "destructive" : "outline"
                    }
                  >
                    {job.status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Attempt {job.attempts} / 3
                </p>
                {job.error && (
                  <p className="text-destructive text-xs">{job.error}</p>
                )}
                {["failed", "cancelled"].includes(job.status) && (
                  <Button
                    variant="outline"
                    disabled={disabled || job.attempts >= 3}
                    onClick={() => onRetry(job.id)}
                  >
                    <RotateCcw data-icon="inline-start" />
                    {job.attempts >= 3
                      ? "Retry budget exhausted"
                      : "Retry this version"}
                  </Button>
                )}
              </div>
            ))}
          </section>
        </div>
      )}
    </SheetContent>
  </Sheet>
);
