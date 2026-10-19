import { describe, expect, it } from "vitest";

import { formatAnalysisError } from "@/components/feedback";

describe("analysis failure messages", () => {
  it.each([
    [
      "Provider output schema validation failed",
      "The AI response did not match the required format. Try again.",
    ],
    [
      "Provider evidence validation failed",
      "The AI quotes did not match the original message. Try again.",
    ],
    [
      "Provider output schema validation failed (summary: string_too_long)",
      "The AI response did not match the required format. Try again.",
    ],
    [
      "Provider evidence validation failed: quotes must match the original message exactly",
      "The AI quotes did not match the original message. Try again.",
    ],
    [
      "Provider response envelope validation failed",
      "The AI service returned an unreadable response. Try again.",
    ],
    [
      "Provider output exceeds 8192 characters",
      "The AI response was too long to process. Try again.",
    ],
  ])("explains %s without exposing a technical error", (error, message) => {
    expect(formatAnalysisError(error)).toBe(message);
  });

  it("retains the safe message for legacy validation failures", () => {
    expect(
      formatAnalysisError(
        "Provider output failed schema or evidence validation"
      )
    ).toBe(
      "The AI response could not be verified against the original message. Try again."
    );
  });

  it("keeps actionable budget, account and timeout guidance", () => {
    expect(formatAnalysisError("Live provider call budget exhausted")).toBe(
      "The AI request limit for this demo has been reached."
    );
    expect(
      formatAnalysisError("Provider rejected the request (402)")
    ).toContain("Add credits before trying again.");
    expect(
      formatAnalysisError("Provider rejected the request (401)")
    ).toContain("Its server credentials need to be updated.");
    expect(formatAnalysisError("Provider request timed out")).toBe(
      "The AI service took too long to respond. Try again."
    );
    expect(formatAnalysisError("TimeoutError")).toBe(
      formatAnalysisError("Provider request timed out")
    );
  });

  it("never displays missing errors or unknown provider content", () => {
    const fallback =
      "The AI service couldn’t complete the request. Try again; your message and previous result are safe.";
    for (const error of [
      undefined,
      null,
      "",
      "Unknown upstream error: private-payload-example",
      "__proto__",
    ]) {
      expect(formatAnalysisError(error)).toBe(fallback);
    }
  });
});
