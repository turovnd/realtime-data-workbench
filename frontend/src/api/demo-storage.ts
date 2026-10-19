import { z } from "zod";
import { batchSchema, recordSchema } from "./contracts";

export type PreviewOptions = {
  workspaceId?: string;
  storage?: Pick<Storage, "getItem" | "setItem" | "removeItem">;
};

const stateSchema = z.object({
  workspace_id: z.string(),
  cursor: z.number().int().min(0),
  records: z.array(recordSchema).max(500),
  batches: z
    .array(batchSchema.extend({ ids: z.array(z.string()).max(100) }))
    .max(1000),
  identities: z.array(z.tuple([z.string(), z.string()])).max(500),
});

type PreviewState = z.infer<typeof stateSchema>;

const storageKey = (options: PreviewOptions) =>
  `feedback-desk-preview:${options.workspaceId ?? "browser"}`;

export const readPreview = (
  options: PreviewOptions
): PreviewState | undefined => {
  if (!options.storage) return;
  try {
    const value = stateSchema.parse(
      JSON.parse(options.storage.getItem(storageKey(options)) ?? "null")
    );
    if (value.workspace_id === (options.workspaceId ?? "browser")) return value;
  } catch {
    // Missing, obsolete or malformed browser state starts a fresh synthetic preview.
  }
};

export const writePreview = (options: PreviewOptions, value: PreviewState) => {
  try {
    options.storage?.setItem(storageKey(options), JSON.stringify(value));
  } catch {
    // Storage can be unavailable or full; the in-memory preview remains usable.
  }
};
