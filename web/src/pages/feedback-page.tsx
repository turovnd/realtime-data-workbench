import { useState } from "react";
import { Play } from "lucide-react";
import type { Identity } from "@/lib/api/auth";
import { currentJob, type ConfigVersion } from "@/lib/api/contracts";
import { Button } from "@/components/ui/button";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { FeedbackSummary } from "@/components/feedback/feedback-summary";
import { RecordInspector } from "@/components/feedback/record-inspector";
import { BackfillPanel } from "@/components/feedback/backfill-panel";
import { FeedbackFeed } from "@/components/feedback/feedback-feed";
import { WorkbenchStatus } from "@/components/feedback/workbench-status";
import { OfflinePanel } from "@/components/feedback/offline-panel";
import { useWorkbench } from "@/hooks/use-workbench";
import { useFilters } from "@/hooks/use-filters";
import { useFeedbackSelection } from "@/hooks/use-feedback-selection";

export const FeedbackPage = ({
  identity,
  onLogout,
  signingOut,
}: {
  identity: Identity;
  onLogout: () => void;
  signingOut: boolean;
}) => {
  const filters = useFilters();
  const workbench = useWorkbench({
    q: filters.q,
    status: filters.status,
    topic: filters.topic,
  });
  const [inspected, setInspected] = useState<string>();
  const [version, setVersion] = useState<ConfigVersion>("v2");
  const rows = workbench.data?.records ?? [];
  const disabled =
    !workbench.online ||
    workbench.mutation.isPending ||
    workbench.query.isError ||
    !workbench.data;
  const { selected, select, selectLoaded, clear } = useFeedbackSelection(rows);
  return (
    <WorkspaceShell
      identity={identity}
      recordCount={workbench.status.data?.received ?? rows.length}
      batchCount={workbench.data?.batches.length ?? 0}
      preview={workbench.mode === "browser-demo"}
      onLogout={onLogout}
      signingOut={signingOut}
      inspector={
        <RecordInspector
          record={rows.find((row) => row.id === inspected)}
          onClose={() => setInspected(undefined)}
          disabled={disabled}
          onRetry={(id) => workbench.mutation.mutate({ type: "retry", id })}
        />
      }
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            Feedback stream
          </h1>
          <p className="text-sm text-muted-foreground">
            Review incoming signals, inspect evidence, and keep every version.
          </p>
        </div>
        <Button
          disabled={disabled}
          onClick={() => workbench.mutation.mutate({ type: "simulate" })}
        >
          <Play data-icon="inline-start" />
          {workbench.mutation.isPending ? "Working…" : "Add 12 live records"}
        </Button>
      </div>
      <WorkbenchStatus workbench={workbench} />
      <FeedbackSummary
        received={workbench.status.data?.received ?? rows.length}
        enriched={
          workbench.status.data?.enriched ??
          rows.filter((row) => currentJob(row)?.status === "succeeded").length
        }
        failed={
          workbench.status.data?.failed ??
          rows.filter((row) => currentJob(row)?.status === "failed").length
        }
      />
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_19rem]">
        <FeedbackFeed
          workbench={workbench}
          filters={filters}
          rows={rows}
          selected={selected}
          select={select}
          selectLoaded={selectLoaded}
          clearSelection={clear}
          onInspect={setInspected}
        />
        <BackfillPanel
          selected={selected.size}
          version={version}
          setVersion={setVersion}
          onRun={() =>
            workbench.mutation.mutate({
              type: "backfill",
              ids: [...selected],
              config: version,
            })
          }
          onCancel={(id) => workbench.mutation.mutate({ type: "cancel", id })}
          disabled={disabled}
          batches={workbench.data?.batches ?? []}
        />
      </div>
      <OfflinePanel workbench={workbench} count={rows.length} />
    </WorkspaceShell>
  );
};
