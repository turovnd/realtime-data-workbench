# MVP plan

Help a product reviewer turn customer feedback into a short, verifiable takeaway: what happened, why it matters and which words support it.

The plan separates intended outcomes from implementation evidence. Epics and stories define the work; each task records its parent story, dependencies, acceptance criteria and evidence.

## Scope

- Enter a private demo workspace or sign in to a personal account.
- Add feedback, browse and filter the inbox, and load more with cursor pagination.
- Compare the original message with an AI summary, classification and exact quotes.
- Analyze a message again or process a fixed selection, with visible progress and recovery.
- Inspect saved runs and their results in Activity.

Problem grouping, roadmap management and team administration are outside this MVP.

## Epics and stories

| Epic                                                      | User story                                                        | Outcome                                                    |
| --------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| [FD-E01: Review customer feedback](epics/FD-E01.md)       | [FD-S01: Open a workspace and browse feedback](stories/FD-S01.md) | Find relevant feedback without losing the current view.    |
| FD-E01                                                    | [FD-S02: Understand an individual message](stories/FD-S02.md)     | Understand the customer’s problem and verify the takeaway. |
| [FD-E02: Process and reprocess reliably](epics/FD-E02.md) | [FD-S03: Add feedback and inspect processing](stories/FD-S03.md)  | Submit a message and follow it to a real AI result.        |
| FD-E02                                                    | [FD-S04: Reprocess a fixed selection](stories/FD-S04.md)          | Run analysis again while preserving earlier results.       |

## Tasks

| Task                                                        | Is task of story            | Depends on     |
| ----------------------------------------------------------- | --------------------------- | -------------- |
| [FD-T01: Workspace and session foundation](tasks/FD-T01.md) | [FD-S01](stories/FD-S01.md) | —              |
| [FD-T02: Routed review interface](tasks/FD-T02.md)          | [FD-S01](stories/FD-S01.md) | FD-T01         |
| [FD-T03: Record and supporting evidence](tasks/FD-T03.md)   | [FD-S02](stories/FD-S02.md) | FD-T02         |
| [FD-T04: Durable analysis processing](tasks/FD-T04.md)      | [FD-S03](stories/FD-S03.md) | —              |
| [FD-T05: Feedback submission](tasks/FD-T05.md)              | [FD-S03](stories/FD-S03.md) | FD-T02, FD-T04 |
| [FD-T06: Reanalysis and recovery](tasks/FD-T06.md)          | [FD-S04](stories/FD-S04.md) | FD-T04         |
| [FD-T07: Public real-AI demonstration](tasks/FD-T07.md)     | [FD-S03](stories/FD-S03.md) | FD-T04, FD-T05 |

Implementation status and supporting code/tests live in each task’s **Evidence and status** section. The [testing guide](../testing.md) explains how to verify the MVP.
