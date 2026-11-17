import { expect, it } from "vitest";

import { createDemoAdapter } from "@/api/demo";

it("starts with distinct customer messages and useful, explicitly prepared results", async () => {
  const { records } = await createDemoAdapter().snapshot();

  expect(new Set(records.map(record => record.text)).size).toBe(24);
  for (const record of records) {
    const result = record.outputs[0];
    expect(record.jobs[0].status).toBe("succeeded");
    expect(result.provider).toBe("browser-fixture/1");
    expect(result.summary.length).toBeLessThan(record.text.length * 0.65);
    expect(record.text).not.toContain(result.summary);
    for (const quote of result.evidence) expect(record.text).toContain(quote);
  }
});
