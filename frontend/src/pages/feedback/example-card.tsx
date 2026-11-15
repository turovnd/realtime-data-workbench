import { ArrowRight } from "lucide-react";
import type { MouseEventHandler } from "react";

import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui";

type Props = {
  liveAnalysis: boolean;
  disabled: boolean;
  onTry: MouseEventHandler<HTMLButtonElement>;
};

export const ExampleCard = ({ liveAnalysis, disabled, onTry }: Props) => (
  <Card size="sm">
    <CardHeader>
      <CardTitle>
        {liveAnalysis
          ? "Try AI on a detailed message"
          : "Start with an example"}
      </CardTitle>
      <CardDescription>
        A customer describes a failed monthly export, a workaround and a
        request. See what matters without losing their words.
      </CardDescription>
    </CardHeader>
    <CardContent className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-xs text-muted-foreground">
        {liveAnalysis
          ? "Edit the message → Run AI → Check the quotes"
          : "Explore sample results. Live analysis needs a connected AI provider."}
      </p>
      <Button variant="outline" onClick={onTry} disabled={disabled}>
        Try an example
        <ArrowRight data-icon="inline-end" />
      </Button>
    </CardContent>
  </Card>
);
