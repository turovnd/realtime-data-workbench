import { ArrowDownToLine, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { WorkbenchState } from "@/hooks/use-workbench";
export const OfflinePanel = ({
  workbench,
  count,
}: {
  workbench: WorkbenchState;
  count: number;
}) => (
  <>
    <Separator />
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-sm font-medium">Inspect offline</h2>
        <p className="text-xs text-muted-foreground">
          {workbench.saved
            ? `Snapshot saved ${new Date(workbench.saved.savedAt).toLocaleTimeString()}.`
            : `Save the ${count} loaded records on this device for read-only inspection.`}
        </p>
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          disabled={!workbench.online || !workbench.data}
          onClick={workbench.save}
        >
          <ArrowDownToLine data-icon="inline-start" /> Save snapshot
        </Button>
        {workbench.saved && (
          <Button
            variant="ghost"
            size="icon"
            aria-label="Delete saved snapshot"
            onClick={workbench.clearSaved}
          >
            <Trash2 />
          </Button>
        )}
      </div>
    </div>
  </>
);
