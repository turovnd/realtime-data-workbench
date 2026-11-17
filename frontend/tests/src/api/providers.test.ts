import { describe, expect, it } from "vitest";

import { isAiOutput, type Output } from "@/api/contracts";
import {
  formatProvider,
  isAiProvider,
  isSampleProvider,
} from "@/api/providers";

describe("analysis provider provenance", () => {
  it.each([
    ["openrouter/openai/gpt-4.1-mini", "AI · openai/gpt-4.1-mini · OpenRouter"],
  ])("identifies %s without losing model or provider", (provider, label) => {
    expect(isAiProvider(provider)).toBe(true);
    expect(isSampleProvider(provider)).toBe(false);
    expect(formatProvider(provider)).toBe(label);
  });

  it.each([
    "deterministic-rules/1",
    "deterministic/fixture",
    "browser-fixture/1",
  ])("keeps %s visibly separate from real AI", provider => {
    expect(isAiProvider(provider)).toBe(false);
    expect(isSampleProvider(provider)).toBe(true);
    expect(formatProvider(provider)).toBe("Sample analysis");
  });

  it.each([
    undefined,
    "",
    " ",
    "unknown",
    "unknownx",
    "unknown/",
    "unknown/ ",
    "unknown//model",
    "unknown/model",
    "deterministic-rules/other",
  ])("does not classify unknown metadata %s as AI or a sample", provider => {
    expect(isAiProvider(provider)).toBe(false);
    expect(isSampleProvider(provider)).toBe(false);
    expect(formatProvider(provider)).toBe(
      provider?.trim() ? `Provider · ${provider}` : "Provider not identified"
    );
  });

  it("applies the same distinction to completed results", () => {
    const output: Output = {
      config: "v1",
      provider: "openrouter/openai/gpt-4.1-mini",
      topic: "reliability",
      intent: "issue",
      summary: "The export fails.",
      evidence: ["The export fails."],
      created_at: "2026-11-16T10:00:00Z",
    };

    expect(isAiOutput(output)).toBe(true);
    expect(isAiOutput({ ...output, provider: "deterministic-rules/1" })).toBe(
      false
    );
    expect(isAiOutput({ ...output, provider: "" })).toBe(false);
    expect(isAiOutput(undefined)).toBe(false);
  });
});
