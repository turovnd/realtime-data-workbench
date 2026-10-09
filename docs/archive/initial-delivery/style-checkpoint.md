# Style checkpoint: original samples

2026-10-09. **Accepted by the owner on 2026-10-09; implementation authorized.** TypeScript arrow exports and the proposed Python conventions are accepted. These samples are independently authored with synthetic inputs; no private implementation has been copied.

## Frontend: a focused approval component

This is a documentation excerpt for style review, not an installed or browser-tested UI. It composes official shadcn `Button`, `Alert`, `AlertTitle`, `AlertDescription` and `Spinner`; these components must be added through the official registry when the application is initialized. The excerpt intentionally omits imports until the actual alias and primitive configuration exist. Current component APIs were checked with the shadcn CLI and official documentation.

```tsx
type ApprovalState =
  | { status: "ready" }
  | { status: "submitting" }
  | { status: "failed"; message: string };

type ApprovalActionsProps = {
  state: ApprovalState;
  errorId: string;
  onApprove: () => void;
};

export const ApprovalActions = ({
  state,
  errorId,
  onApprove,
}: ApprovalActionsProps) => {
  const isSubmitting = state.status === "submitting";

  return (
    <section aria-label="Proposal approval" className="flex flex-col gap-3">
      {state.status === "failed" && (
        <Alert variant="destructive" id={errorId} role="alert">
          <AlertTitle>Approval could not be completed</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      )}
      <Button
        type="button"
        disabled={isSubmitting}
        aria-describedby={state.status === "failed" ? errorId : undefined}
        onClick={onApprove}
      >
        {isSubmitting && <Spinner data-icon="inline-start" aria-hidden="true" />}
        {isSubmitting ? "Approving…" : "Approve proposal"}
      </Button>
      <p role="status" className="sr-only">
        {isSubmitting ? "Approval is being saved." : ""}
      </p>
    </section>
  );
};
```

The parent feature displays the full proposal and version, supplies a unique stable `errorId`, and owns success/conflict views. A separate `export const useApproveProposal = (...) => {}` hook will own mutation state, the stable retry key and query invalidation. The disabled button improves feedback; only the server transaction can enforce idempotency. Browser focus, success navigation and repeated-click behavior remain unverified.

Official references: [Button](https://ui.shadcn.com/docs/components/base/button), [Alert](https://ui.shadcn.com/docs/components/base/alert), [Spinner](https://ui.shadcn.com/docs/components/base/spinner). The CLI returned the Base UI documentation; that is not yet a locked application preset.

## Node: an injected application operation

The sample keeps HTTP concerns outside a small operation factory. Fastify will validate request/response schemas and resolve the authorized workspace before invoking it. The repository contract explicitly requires an atomic implementation; no database implementation or transaction guarantee is claimed by this snippet. IDs and key length limits belong to the eventual request schema. Proposal content must be immutable for a given version, and canonicalization must be versioned before the digest contract changes.

```ts
import { createHash } from "node:crypto";

export type ApprovalCommand = Readonly<{
  workspaceId: string;
  proposalId: string;
  expectedVersion: number;
  idempotencyKey: string;
}>;

export type ApprovalOutcome =
  | { status: "approved" | "replayed"; actionId: string; version: number }
  | { status: "version-conflict"; currentVersion: number }
  | { status: "idempotency-conflict" }
  | { status: "not-found" };

export type ApprovalWrite = ApprovalCommand & { requestDigest: string };

export type ApprovalRepository = {
  // One transaction: workspace-scoped lookup, version check, action and receipt.
  // Receipt uniqueness is (workspaceId, operation, idempotencyKey).
  // Replay the same key + digest before checking the now-advanced version.
  // A reused key with a different digest must return idempotency-conflict.
  // This contract needs real database constraints and concurrency tests.
  approveAtomically: (write: ApprovalWrite) => Promise<ApprovalOutcome>;
};

export const createApproveProposal = (repository: ApprovalRepository) => {
  // The caller must obtain workspaceId from an authorized request context.
  return async (command: ApprovalCommand): Promise<ApprovalOutcome> => {
    if (
      !Number.isSafeInteger(command.expectedVersion) ||
      command.expectedVersion < 0
    ) {
      throw new RangeError("Expected version must be a non-negative integer.");
    }

    if (
      !command.workspaceId.trim() ||
      !command.proposalId.trim() ||
      !command.idempotencyKey.trim()
    ) {
      throw new TypeError(
        "Workspace, proposal and idempotency key are required.",
      );
    }

    const requestDigest = createHash("sha256")
      .update(
        JSON.stringify([
          "approve-proposal:v1",
          command.workspaceId,
          command.proposalId,
          command.expectedVersion,
        ]),
      )
      .digest("hex");

    return repository.approveAtomically({ ...command, requestDigest });
  };
};
```

## Python: strict boundary models and an injected callable

This sample shows the proposed style: typed async functions, Pydantic models for untrusted data, early validation and a callable dependency. It deliberately implements no HTTP client, provider timeout, queue, database or FastAPI route. The provider adapter will enforce timeout and incremental output limits in the actual app; checking the final string is only this sample's parsing boundary.

```python
"""A style sample: validate one enrichment without persistence or network I/O."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    text: str = Field(min_length=1, max_length=4_000)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Feedback must contain non-whitespace text.")
        return value


class Enrichment(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    topic: Literal["reliability", "usability", "other"]
    summary: str = Field(min_length=1, max_length=240)
    evidence: tuple[Annotated[str, Field(min_length=1, max_length=200)], ...] = Field(
        min_length=1, max_length=3
    )


Generate = Callable[[str], Awaitable[str]]


async def enrich_feedback(text: str, *, generate: Generate) -> Enrichment:
    """Check shape and source quotes; these checks do not prove the summary true."""
    feedback = FeedbackInput(text=text)
    raw_result = await generate(feedback.text)
    if len(raw_result) > 8_192:
        raise ValueError("Generated output exceeds the sample's character limit.")

    result = Enrichment.model_validate_json(raw_result)
    if any(
        not quote.strip() or quote not in feedback.text for quote in result.evidence
    ):
        raise ValueError("Evidence must quote non-blank source text exactly.")
    return result


DEMO_FEEDBACK = "The activity page loses my filters whenever new updates arrive."


async def generate_demo_result(text: str) -> str:
    """Return a fixed response for the single synthetic example."""
    if text != DEMO_FEEDBACK:
        raise ValueError("This demo adapter accepts only DEMO_FEEDBACK.")
    return Enrichment(
        topic="usability",
        summary="Live updates reset the selected filters.",
        evidence=("loses my filters",),
    ).model_dump_json()
```

The tuple is immutable application data; Pydantic reads its JSON array representation. The fixed adapter supports exactly one synthetic example and is not a semantic model. The UI will identify deterministic generation explicitly. Evidence substring membership guards provenance only; it does not establish that the summary or classification is true.

## Review choices

- Keep small feature modules, arrow exports, explicit types and injected dependencies for React/Node.
- Use this Python direction (typed functions plus strict models), or specify the desired adjustment before the API/worker implementation starts.
- Formatting proposal: Prettier for TypeScript/JSX; Ruff for Python. The owner has not yet approved the full Python layout or application runtime versions.

## Validation status

Frontend: documentation/API review only. No component installation, render, browser test or typecheck has been performed for this excerpt.

Python: 13 focused tests, Ruff lint/format and mypy strict passed in an isolated sample environment. Versions: CPython 3.14.7, Pydantic 2.14.0, pytest 9.1.1, Ruff 0.16.10, mypy 2.4.0. Tests cover malformed/oversized output, invalid fields, unknown/blank evidence, input bounds and provider errors. These are sample-tool versions, not the chosen application runtime.

Node: two focused sample tests, strict TypeScript noEmit, typed ESLint with zero warnings and Prettier passed. Versions: Node 24.14.1, TypeScript 6.0.3, @types/node 24.19.1, ESLint 10.12.0, typescript-eslint 8.71.1 and Prettier 3.9.9. Checks cover invalid versions before persistence and canonical scoped intent digests; they do not prove atomic database behavior.

No application CI, real-DB integration, E2E or hosted smoke tests exist yet. Node tests use an injected test double and do not prove persistence behavior.
