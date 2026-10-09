import { Activity, Database, Layers3 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
export const FeedbackSummary = ({
  received,
  enriched,
  failed,
}: {
  received: number;
  enriched: number;
  failed: number;
}) => (
  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
    {[
      { label: "Feedback received", value: received, icon: Database },
      { label: "Enriched", value: enriched, icon: Layers3 },
      { label: "Needs attention", value: failed, icon: Activity },
    ].map((stat) => (
      <Card key={stat.label}>
        <CardHeader>
          <CardDescription>
            <span className="flex items-center justify-between gap-3">
              {stat.label}
              <stat.icon className="size-4" />
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <span className="text-3xl font-semibold tabular-nums">
            {stat.value}
          </span>
        </CardContent>
      </Card>
    ))}
  </div>
);
