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

Implemented in `frontend/src/pages/feedback-details` and the feedback read API. Tests cover workspace-scoped access, sample/AI provenance, exact quotes and navigation to historical results.
