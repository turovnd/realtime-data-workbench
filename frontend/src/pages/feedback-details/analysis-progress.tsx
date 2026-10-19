import { useEffect, useState } from "react";
import { CircleCheck, Clock3 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle, Spinner } from "@/components/ui";

type Props = { stage: "starting" | "queued" | "leased"; submittedAt: number };

export const AnalysisProgress = ({ stage, submittedAt }: Props) => {
  const [openedAt] = useState(Date.now);
  const [now, setNow] = useState(Date.now);
  const startedAt = submittedAt || openedAt;
  const elapsed = Math.max(0, Math.floor((now - startedAt) / 1000));

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const title = {
    starting: "Starting AI analysis",
    queued: "Waiting for AI",
    leased: "AI is analyzing your feedback",
  }[stage];
  const description = {
    starting: "Sending your request. This page will update automatically.",
    queued: "Your request is queued. Analysis will start shortly.",
    leased: "Reading the message and checking the summary against its source.",
  }[stage];

  return (
    <Alert role="status" aria-live="polite">
      <Spinner aria-hidden="true" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex flex-col gap-3">
        <p>{description}</p>
        <ol
          className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs"
          aria-label="Analysis steps"
        >
          <li className="flex items-center gap-1.5">
            {stage === "starting" ? (
              <Clock3 className="size-3.5" />
            ) : (
              <CircleCheck className="size-3.5" />
            )}
            Submitted
          </li>
          <li className="flex items-center gap-1.5">
            {stage === "leased" ? (
              <Spinner aria-hidden="true" />
            ) : (
              <Clock3 className="size-3.5" />
            )}
            Analyzing
          </li>
          <li className="flex items-center gap-1.5">
            <Clock3 className="size-3.5" />
            Complete
          </li>
        </ol>
        <p className="text-xs" aria-live="off">
          {elapsed} s elapsed
          {elapsed >= 20
            ? " · Still working. You can leave this page and return later."
            : ""}
        </p>
      </AlertDescription>
    </Alert>
  );
};
