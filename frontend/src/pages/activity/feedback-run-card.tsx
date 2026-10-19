import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import type { BatchItem } from "@/api";
import { statusLabels } from "@/components/feedback";
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
  Separator,
} from "@/components/ui";
import { RunFeedback } from "./run-feedback";

type Props = { item: BatchItem };

export const FeedbackRunCard = ({ item }: Props) => {
  const [open, setOpen] = useState(false);
  const { job } = item;
  const sample = !!job && !job.provider?.startsWith("openrouter/");
  const label = job
    ? job.status === "queued"
      ? "Queued"
      : statusLabels[job.status]
    : "Not started";
  const name = `Feedback #${item.sequence}${job?.run ? `, run ${job.run}` : ""}`;
  const Chevron = open ? ChevronUp : ChevronDown;

  return (
    <Collapsible open={open} onOpenChange={setOpen} asChild>
      <Card role="article" aria-label={name} className="gap-0 py-0">
        <div className="relative">
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="absolute inset-0 size-full cursor-pointer rounded-none focus-visible:ring-inset"
              aria-label={`View details for ${name.toLowerCase()}`}
            />
          </CollapsibleTrigger>
          <div className="pointer-events-none relative flex flex-col gap-4 py-5">
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 flex-col gap-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <CardTitle>Feedback #{item.sequence}</CardTitle>
                    <Badge
                      variant={
                        job?.status === "failed" ? "destructive" : "secondary"
                      }
                    >
                      {label}
                    </Badge>
                  </div>
                  <CardDescription>
                    {sample
                      ? "Sample analysis"
                      : job?.origin === "analysis"
                        ? "Manual analysis"
                        : "New feedback"}
                    {" · "}
                    {item.channel}
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
            <CardContent>
              <p className="line-clamp-2 break-words text-sm text-muted-foreground">
                {item.text}
              </p>
            </CardContent>
          </div>
        </div>
        <CollapsibleContent>
          <Separator />
          <CardContent className="py-5">
            <RunFeedback item={item} />
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
};
