---
id: FD-T03
type: task
is_task_of: FD-S02
status: ready-for-review
depends_on: ["FD-T02"]
---

# FD-T03: Open a record with its current evidence

Parent: [FD-S02](../stories/FD-S02.md). Dependencies: [FD-T02](FD-T02.md)

## Scope

Give each record a direct review view with the original message and a readable result.

## Acceptance

- Record access is workspace-scoped and has visible missing/error/retry states.
- The current result includes exact supporting quotes; earlier results remain preserved by the backend.
- The UI emphasizes the message and result; technical details do not dominate the page.

## Tests

API isolation/validation tests and browser direct-link, back-navigation and evidence checks.

## Evidence and status

The direct route and API are verified locally and ready for owner review. The page presents the original message and current result. Earlier results remain preserved by the backend and can be inspected through Activity.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
