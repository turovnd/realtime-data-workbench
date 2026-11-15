# Verification and release

The candidate implements the agreed Feedback Desk MVP: feedback review, real AI analysis, preserved run history and isolated workspaces. Local verification is complete; the coordinated Git, Vercel and Docker release is in progress. Published source and runtime identities will be recorded after deployment succeeds.

## Source verification

| Boundary           | Observed evidence                                                                                                                                                                                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend            | 160 tests passed on disposable PostgreSQL, with no skips. Ruff lint/format and strict mypy passed.                                                                                                                                                                                                                        |
| Frontend           | 42 unit tests passed; type checks, lint, formatting and build passed. The build retains an entry-chunk warning above 500 kB.                                                                                                                                                                                              |
| Browser            | 20 desktop/mobile preview scenarios and 27 connected scenarios passed. Connected checks include seven real API/worker/PostgreSQL flows and twenty controlled-response flows.                                                                                                                                              |
| API contract       | OpenAPI describes 16 paths; the generated client is reproducible with `pnpm api:check`.                                                                                                                                                                                                                                   |
| Real AI            | Twelve bounded requests across four fixed scenarios and three prompt iterations. Final declared checks passed for all four; earlier failures and qualitative limitations remain in the [evaluation report](ai-evaluation.md).                                                                                             |
| Complete live flow | The local browser submitted the editable example through the API. The worker called OpenRouter, persisted the result and displayed it with source quotes and model provenance. Activity showed the same saved result. The isolated usage counter recorded one paid attempt; 24 seeded sample jobs remained deterministic. |
| Schema upgrade     | A backup of the remote database was restored in isolated PostgreSQL. Adoption reached Alembic `0002`, metadata check passed, all ten table fingerprints were preserved and the active database remained unchanged during rehearsal.                                                                                       |

A release review found a deferred-submission session gap. The submission boundary now validates the captured token and workspace immediately before sending the request; focused tests reject drafts from an earlier session before any AI work is enqueued.

## Deployment boundary

The frontend is published through the Git-connected Vercel project. The API, worker and PostgreSQL belong to the isolated `turovnd-realtime` Docker project. Backend deployment and schema adoption are separate from frontend auto-deployment. A prior image alone is not a safe schema rollback after new analysis runs have been accepted; see [operations](operations.md#schema-aware-rollback).

The release enables real OpenRouter processing for submitted feedback and explicit analysis. Opening a demo seeds deterministic examples without paid calls. The existing cumulative `unlimited` configuration retains its durable counter; each job still has bounded attempts, timeouts and output tokens. Shipped local defaults remain disabled.

## Practical limits

The evaluation is a small synthetic development set, not a held-out quality benchmark. Exact quotes do not prove a summary’s interpretation. No customer-impact, high-throughput or general adversarial-robustness claim is made. The database restore rehearsal verifies this release’s recovery artifact; scheduled off-host backups and recurring recovery drills remain operational work. See [limits](limits.md), [testing](testing.md) and the [MVP plan](planning/README.md).
