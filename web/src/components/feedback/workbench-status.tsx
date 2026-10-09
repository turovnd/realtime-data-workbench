import { Radio, WifiOff } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { WorkbenchState } from "@/hooks/use-workbench";

export const WorkbenchStatus = ({
  workbench,
}: {
  workbench: WorkbenchState;
}) => {
  const error =
    workbench.mutation.error ?? workbench.query.error ?? workbench.status.error;
  return (
    <>
      <Alert>
        <Radio />
        <AlertTitle>
          {workbench.mode === "browser-demo"
            ? "Deterministic browser demo"
            : workbench.status.data?.provider.startsWith("openrouter/")
              ? "Live enrichment configured"
              : "Deterministic server enrichment"}
        </AlertTitle>
        <AlertDescription>
          {workbench.mode === "browser-demo"
            ? "Synthetic feedback is simulated in this tab. Reload resets the preview; no server or model calls."
            : workbench.status.data?.provider.startsWith("openrouter/")
              ? "New processing uses the configured model. Failed or unavailable provider calls remain visible and never fall back silently."
              : "Synthetic records are processed by the separate server worker. No live model calls are made."}
        </AlertDescription>
      </Alert>
      {!workbench.online && (
        <Alert>
          <WifiOff />
          <AlertTitle>
            Offline · read-only{" "}
            {workbench.saved ? "saved snapshot" : "view unavailable"}
          </AlertTitle>
          <AlertDescription>
            {workbench.saved
              ? `Saved ${new Date(workbench.saved.savedAt).toLocaleString()}. Reconnect to refresh before making changes.`
              : "Save loaded feedback while online to inspect it offline."}
          </AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Unable to update this view</AlertTitle>
          <AlertDescription>
            <p>{error.message}</p>
            <Button
              variant="outline"
              onClick={() => {
                workbench.mutation.reset();
                workbench.refresh();
              }}
            >
              Refresh view
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </>
  );
};
