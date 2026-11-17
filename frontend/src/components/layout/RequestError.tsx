import { ApiError } from "@/api";
import { Alert, AlertDescription, AlertTitle, Button } from "@/components/ui";

type Props = {
  title: string;
  description?: string;
  error: unknown;
  onRetry: () => void;
  disabled?: boolean;
};

export const RequestError = ({
  title,
  description,
  error,
  onRetry,
  disabled,
}: Props) => (
  <Alert variant="destructive">
    <AlertTitle>{title}</AlertTitle>
    <AlertDescription className="flex flex-col gap-3">
      <div>
        {description && <div>{description}</div>}
        <div>
          {error instanceof ApiError
            ? error.message
            : "Check your connection and try again."}
        </div>
        {error instanceof ApiError && (
          <div>Response status: {error.status}</div>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={onRetry}
        >
          Try again
        </Button>
        {error instanceof ApiError && error.recovery === "reload" && (
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={() => window.location.reload()}
          >
            Reload page
          </Button>
        )}
      </div>
    </AlertDescription>
  </Alert>
);
