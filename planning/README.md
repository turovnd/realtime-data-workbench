# Feedback Desk current delivery plan

Current delivery plan for this independently runnable and releasable project.

## Status rules

- **verified-baseline**: the feature or deployed baseline has explicit prior execution evidence. A new release still requires its own deployment verification.
- **in-progress**: implementation or verification is currently underway.
- **pending**: authorized delivery work with acceptance not yet confirmed.
- **backlog**: an explicitly unfinished improvement, outside the already verified baseline.
- **verified-local**: the stated local checks passed for the current work; remote integration is a separate claim.
- **verified-hosted**: the deployed release passed the stated public/platform checks.

The [delivery ledger](../docs/delivery-status.md) owns externally confirmed status. Every task file contains `is_task_of`, explicit dependencies, goal, scope, acceptance, tests and implementation evidence. Dependencies express the order for the current delivery.

## Epic and story index

| Epic                                                  | Stories                                                  | Outcome                                                                    |
| ----------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------- |
| [FD-E01 — Foundation and contracts](epics/FD-E01.md)  | [FD-S01](stories/FD-S01.md), [FD-S02](stories/FD-S02.md) | Explicit source boundaries, mirrored tests and inspectable HTTP contracts. |
| [FD-E02 — Identity and browsing](epics/FD-E02.md)     | [FD-S03](stories/FD-S03.md), [FD-S04](stories/FD-S04.md) | Independent accounts, private client state and stable paged review.        |
| [FD-E03 — Durable product workflow](epics/FD-E03.md)  | [FD-S05](stories/FD-S05.md), [FD-S06](stories/FD-S06.md) | Source-backed generation, persistence and recoverable effects.             |
| [FD-E04 — Verification and delivery](epics/FD-E04.md) | [FD-S07](stories/FD-S07.md), [FD-S08](stories/FD-S08.md) | Local/hosted evidence, public Git delivery and operational recovery.       |

## Task index

| Task                                                              | Story                       | Status          | Goal                                                                                      |
| ----------------------------------------------------------------- | --------------------------- | --------------- | ----------------------------------------------------------------------------------------- |
| [FD-T01 — Runtime boundaries](tasks/FD-T01.md)                    | [FD-S01](stories/FD-S01.md) | verified-local  | Make module ownership explicit without changing the product contract.                     |
| [FD-T02 — One mirrored test tree](tasks/FD-T02.md)                | [FD-S01](stories/FD-S01.md) | verified-local  | Give every test a discoverable production owner.                                          |
| [FD-T03 — Generated API contract and Swagger](tasks/FD-T03.md)    | [FD-S02](stories/FD-S02.md) | verified-local  | Let a reviewer inspect and exercise the real API contract.                                |
| [FD-T04 — Accounts and workspace sessions](tasks/FD-T04.md)       | [FD-S03](stories/FD-S03.md) | verified-local  | Bind all feedback state to a server-established identity.                                 |
| [FD-T05 — Private client and offline isolation](tasks/FD-T05.md)  | [FD-S03](stories/FD-S03.md) | verified-local  | Prevent previous sessions from leaking through client caches or delayed requests.         |
| [FD-T06 — Stable filtered feed cursors](tasks/FD-T06.md)          | [FD-S04](stories/FD-S04.md) | verified-local  | Browse a stable bounded membership while arrivals and processing continue.                |
| [FD-T07 — Feedback browsing and inspection UI](tasks/FD-T07.md)   | [FD-S04](stories/FD-S04.md) | verified-local  | Inspect original text, evidence and versions while keeping selection stable.              |
| [FD-T08 — Immutable ingestion and results](tasks/FD-T08.md)       | [FD-S05](stories/FD-S05.md) | verified-local  | Keep source messages and versioned output inspectable and reproducible.                   |
| [FD-T09 — Strict bounded enrichment provider](tasks/FD-T09.md)    | [FD-S05](stories/FD-S05.md) | verified-local  | Produce structured feedback labels with inspectable source evidence.                      |
| [FD-T10 — Fenced worker recovery and retries](tasks/FD-T10.md)    | [FD-S06](stories/FD-S06.md) | verified-local  | Recover durable jobs without stale stored effects or unlimited retry.                     |
| [FD-T11 — Fixed-selection versioned backfill](tasks/FD-T11.md)    | [FD-S06](stories/FD-S06.md) | verified-local  | Reprocess exactly the selected records while preserving earlier output.                   |
| [FD-T12 — Live refresh and honest preview modes](tasks/FD-T12.md) | [FD-S06](stories/FD-S06.md) | verified-local  | Show actual processing state without replacing a stable view or hiding API errors.        |
| [FD-T13 — Regression and release evidence](tasks/FD-T13.md)       | [FD-S07](stories/FD-S07.md) | verified-local  | Prove the reorganized application still works as a complete system.                       |
| [FD-T14 — Current docs and traceable plan](tasks/FD-T14.md)       | [FD-S07](stories/FD-S07.md) | verified-local  | Make the project understandable without mixing earlier proposals with delivered behavior. |
| [FD-T15 — Isolated backend delivery](tasks/FD-T15.md)             | [FD-S08](stories/FD-S08.md) | verified-hosted | Run this API, worker and database without disturbing unrelated server services.           |
| [FD-T16 — Vercel UI and exact API origin](tasks/FD-T16.md)        | [FD-S08](stories/FD-S08.md) | verified-hosted | Make the published frontend usable against its real independent API.                      |
| [FD-T17 — Public Git and automatic delivery](tasks/FD-T17.md)     | [FD-S08](stories/FD-S08.md) | verified-hosted | Turn the reviewed public repository into a reproducible delivery source.                  |
| [FD-T18 — Backup and restore rehearsal](tasks/FD-T18.md)          | [FD-S08](stories/FD-S08.md) | backlog         | Recover retained account data independently of the running volume.                        |

## Delivery order and completion rule

Source/test boundaries, API documentation, local regression and the public UI/API release are verified. Git pushes to `main` automatically deploy the production UI. GitHub CI passed for the published source revision; off-host recovery rehearsal remains open. Production Git delivery tracks `main`; feature previews need their own explicit environment/origin configuration.

An epic is complete only when its stories' acceptance is satisfied at the stated scope. Source existence, a static URL returning 200 or a workflow YAML file alone does not establish that outcome. Update the task evidence and [delivery ledger](../docs/delivery-status.md) together when verification changes.
