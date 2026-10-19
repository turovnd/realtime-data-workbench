# First MVP plan

Build a focused product for collecting, reviewing and reanalyzing customer feedback. The implemented processing foundation supports the current review interface. Problem grouping, roadmap decisions and team collaboration remain planned product work.

## Status

- **implemented**: the capability exists and relevant local checks pass.
- **ready-for-review**: the current UI/API step is verified locally and awaits owner acceptance.
- **planned**: the capability remains unimplemented.

Local verification does not publish a release. See the [delivery ledger](../delivery-status.md) for the exact checks and deployment status.

## Epics

| Epic                                                           | Status           | Outcome                                                                    |
| -------------------------------------------------------------- | ---------------- | -------------------------------------------------------------------------- |
| [FD-E01: Review customer feedback](epics/FD-E01.md)            | ready-for-review | Find, open and understand feedback.                                        |
| [FD-E02: Process and reprocess reliably](epics/FD-E02.md)      | ready-for-review | Turn messages into results while retaining recoverable processing history. |
| [FD-E03: Turn signals into product decisions](epics/FD-E03.md) | planned          | Connect feedback to problems, roadmap decisions and team ownership.        |

## Stories

| Story                                                             | Parent epic               | Status           |
| ----------------------------------------------------------------- | ------------------------- | ---------------- |
| [FD-S01: Open a workspace and browse feedback](stories/FD-S01.md) | [FD-E01](epics/FD-E01.md) | ready-for-review |
| [FD-S02: Understand an individual message](stories/FD-S02.md)     | [FD-E01](epics/FD-E01.md) | ready-for-review |
| [FD-S03: Add feedback and inspect processing](stories/FD-S03.md)  | [FD-E02](epics/FD-E02.md) | ready-for-review |
| [FD-S04: Reprocess a fixed selection](stories/FD-S04.md)          | [FD-E02](epics/FD-E02.md) | implemented      |
| [FD-S05: Group evidence into problems](stories/FD-S05.md)         | [FD-E03](epics/FD-E03.md) | planned          |
| [FD-S06: Plan decisions with the team](stories/FD-S06.md)         | [FD-E03](epics/FD-E03.md) | planned          |

## Tasks

| Task                                                                        | Parent story                | Status           |
| --------------------------------------------------------------------------- | --------------------------- | ---------------- |
| [FD-T01: Workspace and session foundation](tasks/FD-T01.md)                 | [FD-S01](stories/FD-S01.md) | implemented      |
| [FD-T02: Deliver the routed review interface](tasks/FD-T02.md)              | [FD-S01](stories/FD-S01.md) | ready-for-review |
| [FD-T03: Open a record with its current evidence](tasks/FD-T03.md)          | [FD-S02](stories/FD-S02.md) | ready-for-review |
| [FD-T04: Durable enrichment foundation](tasks/FD-T04.md)                    | [FD-S03](stories/FD-S03.md) | implemented      |
| [FD-T05: Add feedback through the generated API](tasks/FD-T05.md)           | [FD-S03](stories/FD-S03.md) | ready-for-review |
| [FD-T06: Reanalyze selected feedback and recover failures](tasks/FD-T06.md) | [FD-S04](stories/FD-S04.md) | implemented      |
| [FD-T07: Build evidence-backed problem grouping](tasks/FD-T07.md)           | [FD-S05](stories/FD-S05.md) | planned          |
| [FD-T08: Connect problems to a roadmap](tasks/FD-T08.md)                    | [FD-S06](stories/FD-S06.md) | planned          |
| [FD-T09: Add team ownership and collaboration](tasks/FD-T09.md)             | [FD-S06](stories/FD-S06.md) | planned          |

## Current checkpoint and next work

The routed inbox, direct record view, message submission and Activity are ready for local owner review. The owner has authorized a local commit; push and deployment remain separate steps. After acceptance, problem grouping comes before roadmap and team workflows. Record details show the latest result; Activity exposes automatic, manual and grouped analysis history with the exact result for each listed run.
