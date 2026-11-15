import { describe, expect, it, vi } from "vitest";

import type { Session } from "../../../../src/api/auth";
import {
  createFeedbackActions,
  submitFeedback,
} from "../../../../src/api/feedback/actions";

const session = (token: string): Session => ({
  token,
  workspace_id: `workspace-${token}`,
  email: "owner@example.test",
  kind: "account",
});

describe("selected feedback analysis", () => {
  it("does not submit an old workspace selection after the session changes", async () => {
    let activeSession: Session | null = session("first");
    const backfill = vi.fn().mockResolvedValue(undefined);
    const actions = createFeedbackActions({
      adapter: { backfill },
      getSession: () => activeSession,
      isOnline: () => true,
    });
    const selection = {
      ids: ["feedback-first"],
      config: "v2" as const,
      token: activeSession.token,
    };

    activeSession = session("second");

    await expect(actions.analyzeSelection(selection)).rejects.toThrow(
      "Your session changed"
    );
    expect(backfill).not.toHaveBeenCalled();

    activeSession = null;

    await expect(actions.analyzeSelection(selection)).rejects.toThrow(
      "Your session changed"
    );
    expect(backfill).not.toHaveBeenCalled();
  });

  it("requires a live connection and sends only the selected IDs and configuration", async () => {
    let online = false;
    const activeSession = session("current");
    const backfill = vi.fn().mockResolvedValue(undefined);
    const actions = createFeedbackActions({
      adapter: { backfill },
      getSession: () => activeSession,
      isOnline: () => online,
    });
    const selection = {
      ids: ["feedback-1", "feedback-2"],
      config: "v2" as const,
      token: activeSession.token,
    };

    await expect(actions.analyzeSelection(selection)).rejects.toThrow(
      "Reconnect"
    );
    expect(backfill).not.toHaveBeenCalled();

    online = true;
    await actions.analyzeSelection(selection);

    expect(backfill).toHaveBeenCalledExactlyOnceWith(
      ["feedback-1", "feedback-2"],
      "v2"
    );
  });
});

describe("feedback submission", () => {
  const input = {
    identity: "feedback-submission",
    text: "A private draft from the first workspace.",
    channel: "Support" as const,
  };

  it("rejects a deferred submission after a session switch or sign-out before invoking the adapter", async () => {
    const submission = { input, session: session("first") };
    let activeSession: Session | null = submission.session;
    const create = vi.fn();
    const deferredSubmission = () =>
      submitFeedback(submission, {
        adapter: { create },
        getSession: () => activeSession,
        isOnline: () => true,
      });

    activeSession = session("second");
    await expect(deferredSubmission()).rejects.toThrow("Your session changed");
    expect(create).not.toHaveBeenCalled();

    activeSession = null;
    await expect(deferredSubmission()).rejects.toThrow("Your session changed");
    expect(create).not.toHaveBeenCalled();

    activeSession = {
      ...session("first"),
      workspace_id: "different-workspace",
    };
    await expect(deferredSubmission()).rejects.toThrow("Your session changed");
    expect(create).not.toHaveBeenCalled();
  });

  it("requires connectivity and forwards the original message and request identity only for its current session", async () => {
    const activeSession = session("current");
    let online = false;
    const record = {
      id: "feedback-1",
      sequence: 1,
      text: input.text,
      channel: input.channel,
      ingested_at: "2026-11-15T10:00:00Z",
      jobs: [],
      outputs: [],
    };
    const create = vi.fn().mockResolvedValue(record);
    const dependencies = {
      adapter: { create },
      getSession: () => activeSession,
      isOnline: () => online,
    };
    const submission = { input, session: activeSession };

    await expect(submitFeedback(submission, dependencies)).rejects.toThrow(
      "Reconnect"
    );
    expect(create).not.toHaveBeenCalled();

    online = true;
    await expect(submitFeedback(submission, dependencies)).resolves.toBe(
      record
    );
    expect(create).toHaveBeenCalledExactlyOnceWith(input);
  });
});
