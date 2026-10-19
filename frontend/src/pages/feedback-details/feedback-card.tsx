import type { FeedbackRecord } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";

export const FeedbackCard = ({ record }: { record: FeedbackRecord }) => (
  <Card>
    <CardHeader>
      <CardTitle>Customer message</CardTitle>
    </CardHeader>
    <CardContent className="flex flex-col gap-6">
      <blockquote className="text-base leading-relaxed whitespace-pre-wrap">
        {record.text}
      </blockquote>
      <dl className="flex flex-wrap gap-x-8 gap-y-4 text-sm">
        <div>
          <dt className="text-xs text-muted-foreground">Source</dt>
          <dd className="mt-1 font-medium">{record.channel}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Received</dt>
          <dd className="mt-1 font-medium">
            <time dateTime={record.ingested_at}>
              {new Date(record.ingested_at).toLocaleString(undefined, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </time>
          </dd>
        </div>
      </dl>
    </CardContent>
  </Card>
);
