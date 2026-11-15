---
id: FD-T03
type: task
is_task_of: FD-S02
status: implemented
depends_on: ["FD-T02"]
---

# FD-T03: Open a record with its current evidence

Parent: [FD-S02](../stories/FD-S02.md). Dependencies: [FD-T02](FD-T02.md)

## Scope

Give each record a direct review view with the original message and a readable result.

## Acceptance

- The result exposes model provenance and a direct path to Activity; sample output is visibly distinct from a real AI result.
- Record access is workspace-scoped and has visible missing/error/retry states.
- The current result includes exact supporting quotes; earlier results remain preserved by the backend.
- The UI emphasizes the message and result; technical details do not dominate the page.

## Tests

API isolation/validation tests and browser direct-link, back-navigation and evidence checks.

## Evidence and status

The direct route and API present the original message and current result; Activity preserves access to earlier results. API isolation, consistent ORM reads and connected browser journeys passed. The product behavior is covered by the linked acceptance criteria.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
