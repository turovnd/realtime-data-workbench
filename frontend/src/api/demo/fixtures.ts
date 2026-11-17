import type { ConfigVersion, FeedbackRecord, Output } from "../contracts";

import { z } from "zod";
import { outputSchema, recordSchema } from "../contracts";
import examples from "./samples.json";

const sampleSchema = z.object({
  text: z.string(),
  channel: recordSchema.shape.channel,
  analysis: outputSchema.pick({
    topic: true,
    intent: true,
    summary: true,
    evidence: true,
  }),
});

export const samples = z.array(sampleSchema).parse(examples);

export const previewOutput = (
  record: FeedbackRecord,
  config: ConfigVersion
): Output => {
  const fixture = samples.find(sample => sample.text === record.text);
  if (fixture)
    return {
      ...fixture.analysis,
      config,
      provider: "browser-fixture/1",
      created_at: new Date().toISOString(),
    };

  const text = record.text.toLowerCase();
  const topic = /invoice|billing|charged/.test(text)
    ? "billing"
    : /slow|timeout|times out|seconds/.test(text)
      ? "performance"
      : /broken|crash|stop|loses/.test(text)
        ? "reliability"
        : /button|keyboard|filter/.test(text)
          ? "usability"
          : "other";
  const intent = /please|would like|could you/.test(text)
    ? "request"
    : /thank|love|great/.test(text)
      ? "praise"
      : /slow|broken|crash|stop|loses|timeout|times out|charged/.test(text)
        ? "issue"
        : "unclear";
  return {
    config,
    topic,
    intent,
    summary: (config === "v1"
      ? record.text
      : `${intent} · ${topic}: ${record.text}`
    ).slice(0, 240),
    evidence: [record.text.slice(0, 200)],
    provider: "browser-fixture/1",
    created_at: new Date().toISOString(),
  };
};
