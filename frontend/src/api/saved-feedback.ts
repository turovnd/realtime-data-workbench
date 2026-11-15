import { snapshotSchema } from "./contracts";
import type { Snapshot } from "./contracts";

export type SavedFeedback = {
  snapshot: Snapshot;
  savedAt: string;
};

type Storage = Pick<globalThis.Storage, "getItem" | "setItem" | "removeItem">;

export const createSavedFeedbackStorage = (
  storage: Storage,
  workspace: string
) => {
  const key = `feedback-desk-offline:${workspace}`;

  const read = (): SavedFeedback | null => {
    try {
      const value: unknown = JSON.parse(storage.getItem(key) ?? "null");

      if (
        !value ||
        typeof value !== "object" ||
        !("snapshot" in value) ||
        !("savedAt" in value) ||
        typeof value.savedAt !== "string"
      ) {
        return null;
      }

      const snapshot = snapshotSchema.parse(value.snapshot);

      if (snapshot.workspace_id !== workspace) {
        return null;
      }

      return { snapshot, savedAt: value.savedAt };
    } catch {
      return null;
    }
  };

  const save = (snapshot: Snapshot): SavedFeedback => {
    if (snapshot.workspace_id !== workspace) {
      throw new Error("This feedback belongs to a different workspace.");
    }

    const value = { snapshot, savedAt: new Date().toISOString() };
    storage.setItem(key, JSON.stringify(value));

    return value;
  };

  const clear = () => {
    storage.removeItem(key);
  };

  return { read, save, clear };
};
