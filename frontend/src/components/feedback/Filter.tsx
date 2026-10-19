import { topics } from "./labels";
import { Search, X } from "lucide-react";

import type { FilterState } from "@/hooks";
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui";

export const Filter = ({ filters }: { filters: FilterState }) => {
  const active =
    !!filters.search || filters.status !== "all" || filters.topic !== "all";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative w-full sm:max-w-sm sm:flex-1">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          aria-label="Search feedback"
          placeholder="Search feedback…"
          className="pl-9"
          maxLength={100}
          value={filters.search}
          onChange={event => filters.set("q", event.target.value)}
        />
      </div>
      <Select
        value={filters.topic}
        onValueChange={value => filters.set("topic", value)}
      >
        <SelectTrigger aria-label="Topic" className="w-36">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem value="all">All topics</SelectItem>
            {Object.entries(topics).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
      <Select
        value={filters.status}
        onValueChange={value => filters.set("status", value)}
      >
        <SelectTrigger aria-label="Status" className="w-40">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="queued">Waiting</SelectItem>
            <SelectItem value="leased">Analyzing</SelectItem>
            <SelectItem value="succeeded">Analyzed</SelectItem>
            <SelectItem value="failed">Needs attention</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      {active && (
        <Button variant="ghost" onClick={filters.clear}>
          <X data-icon="inline-start" />
          Clear filters
        </Button>
      )}
    </div>
  );
};
