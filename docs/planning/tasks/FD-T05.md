---
id: FD-T05
type: task
is_task_of: FD-S03
status: implemented
depends_on: ["FD-T02", "FD-T04"]
---

# FD-T05: Add feedback through the generated API

Parent: [FD-S03](../stories/FD-S03.md). Dependencies: [FD-T02](FD-T02.md), [FD-T04](FD-T04.md)

## Scope

Let a reviewer submit a bounded message and follow processing through the actual API contract.

## Acceptance

- The submission action explains whether it starts real AI analysis; it never issues a second analysis merely to complete the guided example.
- The actual FastAPI schema generates the pinned fetch client; generated files are never hand-edited.
- Authenticated submission validates inputs and uses an idempotent request identity.
- Pending, failure and successful submission remain visible; no fake completion is shown.
- Browser fixtures are labelled and remain separate from connected API failures.

## Tests

Schema/client generation checks, HTTP validation/isolation tests, unit tests and connected browser submission.

## Evidence and status

The generated client is reproducible from the actual OpenAPI schema. Query and session boundaries are separated, and connected submission through API, worker and PostgreSQL passed. See the release ledger for the published source revision.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
