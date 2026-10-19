import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import type { Batch } from "@/api";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
  Progress,
  Separator,
} from "@/components/ui";
import { RunDetails } from "./run-details";

type Props = {
  batch: Batch;
  online: boolean;
  cancelling: boolean;
  onCancel: () => void;
};

export const RunCard = ({ batch, online, cancelling, onCancel }: Props) => {
  const [open, setOpen] = useState(false);
  const finished = batch.completed + batch.failed >= batch.selected;
  const running = !finished && !batch.cancelled;
  const label = batch.cancelled
    ? "Cancelled"
    : finished
      ? batch.failed
        ? "Needs attention"
        : "Completed"
      : "In progress";
  const percent = batch.selected
    ? Math.min(
        100,
        Math.round(((batch.completed + batch.failed) / batch.selected) * 100)
      )
    : 0;
  const Chevron = open ? ChevronUp : ChevronDown;

  return (
    <Collapsible open={open} onOpenChange={setOpen} asChild>
      <Card className="gap-0 py-0">
        <div className="relative">
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="absolute inset-0 size-full cursor-pointer rounded-none focus-visible:ring-inset"
              aria-label={`View details for analysis run ${batch.id}`}
            />
          </CollapsibleTrigger>
          <div className="pointer-events-none relative flex flex-col gap-4 py-5">
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 flex-col gap-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <CardTitle>Analysis run</CardTitle>
                    <Badge
                      variant={
                        batch.failed
                          ? "destructive"
                          : finished
                            ? "secondary"
                            : "outline"
                      }
                    >
                      {label}
                    </Badge>
                  </div>
                  <CardDescription>
                    {batch.selected}{" "}
                    {batch.selected === 1
                      ? "feedback message"
                      : "feedback messages"}
                  </CardDescription>
                </div>
                <div className="flex shrink-0 items-center gap-2 text-sm text-muted-foreground">
                  <span className="hidden sm:inline">
                    {open ? "Hide details" : "View details"}
                  </span>
                  <Chevron className="size-5" aria-hidden="true" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <Progress value={percent} aria-label="Analysis progress" />
              <p className="text-sm text-muted-foreground">
                {batch.completed} analyzed
                {batch.failed > 0 ? ` · ${batch.failed} need attention` : ""}
              </p>
            </CardContent>
          </div>
        </div>
        {running && (
          <CardContent className="flex justify-end pb-4">
            <Button
              variant="outline"
              size="sm"
              disabled={!online || cancelling}
              onClick={onCancel}
            >
              Cancel run
            </Button>
          </CardContent>
        )}
        <CollapsibleContent>
          <Separator />
          <CardContent className="py-5">
            <RunDetails
              id={batch.id}
              open={open}
              online={online}
              running={running}
            />
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
};
