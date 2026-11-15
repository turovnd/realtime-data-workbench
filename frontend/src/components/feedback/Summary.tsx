import type { FeedStatus } from "@/api";
import { Button, Separator } from "@/components/ui";

type Props = { status: FeedStatus | undefined; onAttention: () => void };

export const Summary = ({ status, onAttention }: Props) => {
  if (!status) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
      <span>
        <strong className="font-medium text-foreground">
          {status.received}
        </strong>{" "}
        received
      </span>
      <Separator orientation="vertical" className="h-4" />
      <span>
        <strong className="font-medium text-foreground">
          {status.enriched}
        </strong>{" "}
        processed
      </span>
      {status.failed > 0 && (
        <>
          <Separator orientation="vertical" className="h-4" />
          <Button variant="link" className="h-auto p-0" onClick={onAttention}>
            {status.failed} need attention
          </Button>
        </>
      )}
    </div>
  );
};
