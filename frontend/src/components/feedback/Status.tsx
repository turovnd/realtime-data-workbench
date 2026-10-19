import { statusLabels } from "./labels";
import {
  CircleCheck,
  CircleDashed,
  CircleX,
  Clock3,
  LoaderCircle,
} from "lucide-react";

import {
  currentJob,
  currentOutput,
  isAiOutput,
  type FeedbackRecord,
} from "@/api";
import { Badge } from "@/components/ui";

export const Status = ({ record }: { record: FeedbackRecord }) => {
  const status = currentJob(record)?.status ?? "queued";
  const Icon = {
    queued: Clock3,
    leased: LoaderCircle,
    succeeded: CircleCheck,
    failed: CircleX,
    cancelled: CircleDashed,
  }[status];

  return (
    <Badge
      variant={
        status === "failed"
          ? "destructive"
          : status === "succeeded"
            ? "secondary"
            : "outline"
      }
    >
      <Icon className={status === "leased" ? "animate-spin" : undefined} />
      {status === "succeeded" && !isAiOutput(currentOutput(record))
        ? "Sample analysis"
        : statusLabels[status]}
    </Badge>
  );
};
