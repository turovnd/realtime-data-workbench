---
id: FD-S04
type: story
is_story_of: FD-E02
---

# FD-S04: Reprocess a fixed selection

Parent: [FD-E02](../epics/FD-E02.md).

As a reviewer, I want to analyze feedback again or process selected messages, so I can obtain a new result without losing earlier work.

## Acceptance

- A deliberate reanalysis creates a new run; retrying the same request does not duplicate it.
- A group processes the selected records, even if the inbox changes afterward.
- Progress, cancellation and retry preserve completed results.
- Activity opens the result from the selected run, not an unrelated newer result.

## Tasks

- [FD-T06: Reanalysis and recovery](../tasks/FD-T06.md)
