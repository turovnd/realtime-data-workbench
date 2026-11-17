---
id: FD-S03
type: story
is_story_of: FD-E02
---

# FD-S03: Add feedback and inspect processing

Parent: [FD-E02](../epics/FD-E02.md).

As a reviewer, I want to submit a customer message and follow its analysis, so I know when a result is ready or what went wrong.

## Acceptance

- An editable example and free-text entry both use the actual API.
- Queued, running, completed and failed states are visible without a page reload.
- OpenRouter failures stay visible; sample output never substitutes for a failed AI call.
- Activity retains the completed result and its provider details.

## Tasks

- [FD-T04: Durable analysis processing](../tasks/FD-T04.md)
- [FD-T05: Feedback submission](../tasks/FD-T05.md)
- [FD-T07: Public real-AI demonstration](../tasks/FD-T07.md)
