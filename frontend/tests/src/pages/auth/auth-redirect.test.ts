import { describe, expect, it } from "vitest";

import { getAuthDestination } from "../../../../src/pages/auth/auth-redirect";

describe("authentication return destination", () => {
  it("preserves supported detail URLs and inbox filters", () => {
    expect(
      getAuthDestination({ from: "/feedback/item-17?q=invoice&status=failed" })
    ).toBe("/feedback/item-17?q=invoice&status=failed");
    expect(getAuthDestination({ from: "/activity?run=recent" })).toBe(
      "/activity?run=recent"
    );
  });

  it("falls back to the inbox for external, missing and unsupported destinations", () => {
    for (const from of [
      "https://example.test",
      "//example.test",
      "/login",
      "/register",
      "/feedback-other",
      "/activity/unknown",
      42,
    ]) {
      expect(getAuthDestination({ from })).toBe("/feedback");
    }

    expect(getAuthDestination(null)).toBe("/feedback");
    expect(getAuthDestination(undefined)).toBe("/feedback");
  });
});
