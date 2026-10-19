import type { ConfigVersion, FeedbackRecord, Output } from "./contracts";

export const samples = [
  [
    "The activity page loses my filters whenever new updates arrive.",
    "In-app",
    "reliability",
    "issue",
  ],
  [
    "CSV export times out when I select the full month of feedback.",
    "Support",
    "performance",
    "issue",
  ],
  [
    "Please add a keyboard shortcut to jump between saved views.",
    "Community",
    "usability",
    "request",
  ],
  [
    "The billing page charged our workspace twice this month.",
    "Support",
    "billing",
    "issue",
  ],
  [
    "Search feels slow when I paste a long customer reference.",
    "In-app",
    "performance",
    "issue",
  ],
  [
    "The new filters make our weekly review much easier. Thank you!",
    "Community",
    "usability",
    "praise",
  ],
  [
    "Notifications stop arriving after I reconnect to the network.",
    "Support",
    "reliability",
    "issue",
  ],
  [
    "Please let me pin the source column in the feedback table.",
    "In-app",
    "usability",
    "request",
  ],
  [
    "The invoice download button returns an empty document.",
    "Support",
    "billing",
    "issue",
  ],
  [
    "The dashboard takes ten seconds to load on my laptop.",
    "In-app",
    "performance",
    "issue",
  ],
  [
    "The new evidence panel makes the original feedback easy to verify.",
    "Community",
    "usability",
    "praise",
  ],
  [
    "Something changed yesterday, but I cannot tell what it was.",
    "Community",
    "other",
    "unclear",
  ],
] as const;

export const previewOutput = (
  record: FeedbackRecord,
  config: ConfigVersion
): Output => {
  const fixture = samples.find(([text]) => text === record.text);
  const text = record.text.toLowerCase();
  const topic =
    fixture?.[2] ??
    (/invoice|billing|charged/.test(text)
      ? "billing"
      : /slow|timeout|times out|seconds/.test(text)
        ? "performance"
        : /broken|crash|stop|loses/.test(text)
          ? "reliability"
          : /button|keyboard|filter/.test(text)
            ? "usability"
            : "other");
  const intent =
    fixture?.[3] ??
    (/please|would like|could you/.test(text)
      ? "request"
      : /thank|love|great/.test(text)
        ? "praise"
        : /slow|broken|crash|stop|loses|timeout|times out|charged/.test(text)
          ? "issue"
          : "unclear");
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
