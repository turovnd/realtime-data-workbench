import { Progress } from "@/components/ui/progress";
import { ArrowRight, Layers3, Square } from "lucide-react";
import type { ConfigVersion, Snapshot } from "@/lib/api/contracts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = {
  selected: number;
  version: ConfigVersion;
  setVersion: (version: ConfigVersion) => void;
  onRun: () => void;
  onCancel: (id: string) => void;
  disabled: boolean;
  batches: Snapshot["batches"];
};
export const BackfillPanel = ({
  selected,
  version,
  setVersion,
  onRun,
  onCancel,
  disabled,
  batches,
}: Props) => (
  <div className="flex flex-col gap-5">
    <Card>
      <CardHeader>
        <CardTitle>
          <span className="flex items-center gap-2">
            <Layers3 className="size-4" /> Reprocess a selection
          </span>
        </CardTitle>
        <CardDescription>
          Try a new configuration against the same source feedback.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="version">Enrichment version</FieldLabel>
            <Select
              value={version}
              onValueChange={(value) => {
                if (value === "v1" || value === "v2") setVersion(value);
              }}
            >
              <SelectTrigger id="version">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="v2">v2 · Intent-first summary</SelectItem>
                  <SelectItem value="v1">v1 · Source summary</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
            <FieldDescription>
              Previous results stay visible. Every version retains its source
              evidence.
            </FieldDescription>
          </Field>
        </FieldGroup>
        <div className="mt-5 flex items-center justify-between gap-3 text-sm">
          <span>Frozen selection</span>
          <strong>{selected} records</strong>
        </div>
      </CardContent>
      <CardFooter>
        <Button
          className="w-full"
          disabled={disabled || selected === 0 || selected > 100}
          onClick={onRun}
        >
          Run backfill <ArrowRight data-icon="inline-end" />
        </Button>
      </CardFooter>
    </Card>
    <Card>
      <CardHeader>
        <CardTitle>How it works</CardTitle>
        <CardDescription>
          Small operations with explicit recovery.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="flex list-decimal flex-col gap-4 pl-4 text-sm">
          <li>
            <div>
              <strong>Preserve the input</strong>
              <p>Raw feedback is immutable.</p>
            </div>
          </li>
          <li>
            <div>
              <strong>Enrich & validate</strong>
              <p>Bounded retries, exact evidence.</p>
            </div>
          </li>
          <li>
            <div>
              <strong>Store a new version</strong>
              <p>Keep previous results inspectable.</p>
            </div>
          </li>
        </ol>
      </CardContent>
    </Card>
    <Card id="backfills">
      <CardHeader>
        <CardTitle>Recent backfills</CardTitle>
        <CardDescription>Progress for fixed record selections.</CardDescription>
      </CardHeader>
      <CardContent>
        {batches.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Select feedback in the table to create your first backfill.
          </p>
        ) : (
          batches.slice(0, 3).map((batch) => (
            <div className="mb-4 flex flex-col gap-3" key={batch.id}>
              <div className="flex items-center justify-between">
                <strong>
                  {batch.config} · {batch.selected} records
                </strong>
                <Badge variant="outline">
                  {batch.cancelled
                    ? "Stopped"
                    : batch.completed === batch.selected
                      ? "Complete"
                      : "Running"}
                </Badge>
              </div>
              <Progress
                aria-label={`Backfill ${batch.id} progress`}
                value={
                  batch.selected
                    ? ((batch.completed + batch.failed) / batch.selected) * 100
                    : 0
                }
              />
              <p className="text-xs text-muted-foreground">
                {batch.completed} complete · {batch.failed} failed
              </p>
              {!batch.cancelled &&
                batch.completed + batch.failed < batch.selected && (
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={disabled}
                    onClick={() => onCancel(batch.id)}
                  >
                    <Square data-icon="inline-start" /> Stop unfinished work
                  </Button>
                )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  </div>
);
