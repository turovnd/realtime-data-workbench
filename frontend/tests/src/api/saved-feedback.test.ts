import { describe, expect, it } from "vitest";

import type { Snapshot } from "../../../src/api/contracts";
import { createSavedFeedbackStorage } from "../../../src/api/saved-feedback";

const memoryStorage = () => {
  const values = new Map<string, string>();

  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
  };
};

const snapshot = (workspace: string): Snapshot => ({
  workspace_id: workspace,
  cursor: 7,
  records: [],
  batches: [],
  mode: "server",
});

describe("saved feedback", () => {
  it("round trips the current workspace and removes only its own snapshot", () => {
    const storage = memoryStorage();
    const first = createSavedFeedbackStorage(storage, "first");
    const second = createSavedFeedbackStorage(storage, "second");
    const saved = first.save(snapshot("first"));
    second.save(snapshot("second"));

    expect(first.read()).toEqual(saved);
    expect(saved.savedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);

    first.clear();

    expect(first.read()).toBeNull();
    expect(second.read()?.snapshot.workspace_id).toBe("second");
  });

  it("rejects snapshots from another workspace even when stored under the current key", () => {
    const storage = memoryStorage();
    const saved = createSavedFeedbackStorage(storage, "current");
    storage.setItem(
      "feedback-desk-offline:current",
      JSON.stringify({
        snapshot: snapshot("other"),
        savedAt: "2026-10-20T10:00:00.000Z",
      })
    );

    expect(saved.read()).toBeNull();
    expect(() => saved.save(snapshot("other"))).toThrow("different workspace");
  });

  it("treats corrupt or incomplete browser storage as unavailable", () => {
    const storage = memoryStorage();
    const saved = createSavedFeedbackStorage(storage, "current");

    for (const value of [
      "{",
      "null",
      "{}",
      JSON.stringify({ snapshot: {}, savedAt: "now" }),
    ]) {
      storage.setItem("feedback-desk-offline:current", value);
      expect(saved.read()).toBeNull();
    }
  });
});
