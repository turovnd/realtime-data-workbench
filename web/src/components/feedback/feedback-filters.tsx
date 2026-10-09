import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

type Props = {
  search: string;
  status: string;
  topic: string;
  set: (key: string, value: string) => void;
};
export const FeedbackFilters = ({ search, status, topic, set }: Props) => (
  <div className="flex flex-col gap-3">
    <FieldGroup className="flex-row flex-wrap items-end gap-3">
      <Field className="min-w-48 flex-1">
        <FieldLabel className="sr-only" htmlFor="search">
          Search feedback
        </FieldLabel>
        <div className="relative">
          <Input
            id="search"
            placeholder="Search feedback…"
            value={search}
            onChange={(event) => set("q", event.target.value)}
          />
        </div>
      </Field>
      <Field className="w-40">
        <FieldLabel className="sr-only" htmlFor="topic">
          Filter by topic
        </FieldLabel>
        <Select value={topic} onValueChange={(value) => set("topic", value)}>
          <SelectTrigger id="topic">
            <SelectValue placeholder="All topics" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {[
                "all",
                "reliability",
                "usability",
                "billing",
                "performance",
                "other",
              ].map((value) => (
                <SelectItem key={value} value={value}>
                  {value === "all"
                    ? "All topics"
                    : value[0].toUpperCase() + value.slice(1)}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </Field>
    </FieldGroup>
    <ToggleGroup
      type="single"
      value={status}
      onValueChange={(value) => {
        if (value) set("status", value);
      }}
      variant="outline"
      aria-label="Filter by processing status"
    >
      <ToggleGroupItem value="all">All feedback</ToggleGroupItem>
      <ToggleGroupItem value="succeeded">Enriched</ToggleGroupItem>
      <ToggleGroupItem value="queued">Queued</ToggleGroupItem>
      <ToggleGroupItem value="failed">Needs attention</ToggleGroupItem>
    </ToggleGroup>
  </div>
);
