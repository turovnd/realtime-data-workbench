---
id: FD-T05
type: task
is_task_of: FD-S03
status: ready-for-review
depends_on: ["FD-T02", "FD-T04"]
---

# FD-T05: Add feedback through the generated API

Parent: [FD-S03](../stories/FD-S03.md). Dependencies: [FD-T02](FD-T02.md), [FD-T04](FD-T04.md)

## Scope

Let a reviewer submit a bounded message and follow processing through the actual API contract.

## Acceptance

- The actual FastAPI schema generates the pinned fetch client; generated files are never hand-edited.
- Authenticated submission validates inputs and uses an idempotent request identity.
- Pending, failure and successful submission remain visible; no fake completion is shown.
- Browser fixtures are labelled and remain separate from connected API failures.

## Tests

Schema/client generation checks, HTTP validation/isolation tests, unit tests and connected browser submission.

## Evidence and status

The generated contract, API and browser submission flow are verified locally and ready for owner review. This route has not been published.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
