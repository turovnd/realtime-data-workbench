# First MVP plan

Feedback Desk helps a reviewer collect feedback, understand the original message and its AI analysis, and follow each processing run. The agreed MVP covers feedback and AI analysis. The review flow includes an editable demonstration message, real AI analysis, source verification and a saved run in Activity. Technical verification and the deployed revision are recorded separately from product scope.

## Status

- **implemented**: the stated capability exists with relevant verification; this does not imply owner acceptance of the whole product.

## MVP scope

- Add feedback, browse and filter the inbox, and load more records with cursor pagination.
- Open the original message and its AI summary, classification and exact supporting quotes.
- Run analysis again for one message or a fixed selection, with visible progress, errors and preserved results.
- Inspect analysis runs and their results in Activity.
- Sign in to an isolated workspace; authentication remains the foundation for access to feedback.

Problems, Roadmap and Team are outside the agreed MVP. They are not pending delivery tasks, and this plan does not promise a later release. The [delivery ledger](../delivery-status.md) separates source verification, the local runtime and the published application.

## Epics

| Epic                                                      | Status      | Outcome                                                                    |
| --------------------------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| [FD-E01: Review customer feedback](epics/FD-E01.md)       | implemented | Find, open and understand feedback.                                        |
| [FD-E02: Process and reprocess reliably](epics/FD-E02.md) | implemented | Turn messages into results while retaining recoverable processing history. |

## Stories

| Story                                                             | Parent epic               | Status      |
| ----------------------------------------------------------------- | ------------------------- | ----------- |
| [FD-S01: Open a workspace and browse feedback](stories/FD-S01.md) | [FD-E01](epics/FD-E01.md) | implemented |
| [FD-S02: Understand an individual message](stories/FD-S02.md)     | [FD-E01](epics/FD-E01.md) | implemented |
| [FD-S03: Add feedback and inspect processing](stories/FD-S03.md)  | [FD-E02](epics/FD-E02.md) | implemented |
| [FD-S04: Reprocess a fixed selection](stories/FD-S04.md)          | [FD-E02](epics/FD-E02.md) | implemented |

## Tasks

| Task                                                                        | Parent story                | Status      |
| --------------------------------------------------------------------------- | --------------------------- | ----------- |
| [FD-T01: Workspace and session foundation](tasks/FD-T01.md)                 | [FD-S01](stories/FD-S01.md) | implemented |
| [FD-T02: Deliver the routed review interface](tasks/FD-T02.md)              | [FD-S01](stories/FD-S01.md) | implemented |
| [FD-T03: Open a record with its current evidence](tasks/FD-T03.md)          | [FD-S02](stories/FD-S02.md) | implemented |
| [FD-T04: Durable enrichment foundation](tasks/FD-T04.md)                    | [FD-S03](stories/FD-S03.md) | implemented |
| [FD-T05: Add feedback through the generated API](tasks/FD-T05.md)           | [FD-S03](stories/FD-S03.md) | implemented |
| [FD-T06: Reanalyze selected feedback and recover failures](tasks/FD-T06.md) | [FD-S04](stories/FD-S04.md) | implemented |

## Implementation and review

| Capability                                | Exists in code                                                                              | Verification and review                                                          |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Personal accounts and isolated workspaces | Registration, login, session ownership and protected routes                                 | Session isolation is covered by API and browser checks.                          |
| Inbox and feedback details                | Filters, cursor pagination, source message, latest analysis and evidence                    | Guided example, direct detail routes and browser journeys.                       |
| Feedback submission and AI analysis       | Generated API client, durable jobs, live OpenRouter integration, explicit repeated analysis | Provider contracts, persisted worker results and separate live-model evaluation. |
| Activity                                  | Automatic, manual and grouped runs; exact historical results; cursor pagination             | Cursor scope, worker recovery and exact run results.                             |

The agreed MVP tasks are implemented. The delivery includes a guided real-AI scenario and a problem-first project explanation. Published source and runtime evidence are recorded separately from owner acceptance. See the delivery ledger for the checked revision and runtime. New product capabilities require a separate scope decision.
