# Verification and release

The agreed Feedback Desk MVP is implemented and published: feedback review, real AI analysis, preserved run history and isolated workspaces. Source verification and the local real-AI flow passed. The UI and backend are deployed, but hosted real-AI acceptance is blocked by an OpenRouter edge-policy rejection from the server. This is not a completed public AI demonstration.

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

## Published revision

| Surface            | Verified identity                                                                                                                                                     |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Application source | [`a6b6f149bfa2af833be87a9c670731f522cc66ab`](https://github.com/turovnd/realtime-data-workbench/commit/a6b6f149bfa2af833be87a9c670731f522cc66ab) on `main`            |
| GitHub CI          | [Run 43767141171](https://github.com/turovnd/realtime-data-workbench/actions/runs/43767141171): backend, frontend and container jobs passed                           |
| Vercel             | Git-triggered production deployment `dpl_6agrt1MtBkqqxt2cLpUQ4HA4BLyN`, READY for the same application commit; root directory `frontend`                              |
| Backend            | `turovnd-realtime:a6b6f149bfa2af833be87a9c670731f522cc66ab`; image `sha256:9a915aa2ee69f8c46077521bd4c92bbe7737cc6434b3f389309b642244a54e6f`; revision label verified |
| Database           | Explicit adoption to Alembic `0002`, metadata check passed, original-column row fingerprints preserved                                                                |
| Public API         | HTTPS health, Swagger UI and 16-path OpenAPI returned HTTP 200                                                                                                        |

Only the application's API and worker containers were recreated. The database, existing migration container, other application containers and HTTPS proxy configuration were preserved. A fresh backup and its hash-verified off-host copy were retained after an isolated restore rehearsal.

### Hosted AI blocker

The public browser opened a new demo workspace, loaded 24 clearly labelled sample results and submitted the editable example. The feedback was persisted, but its live analysis failed with provider HTTP 403. An explicit retry also failed; the source message and both run records remain available. Each run made one provider attempt, for a durable counter of two; no successful hosted generation was recorded.

A separate read-only check from the running worker confirmed the server's outgoing IP and repeated the failure on both the unauthenticated OpenRouter model catalog and authenticated key endpoint: `Access denied by security policy`. The same catalog returned HTTP 200 locally, and the local and deployed credentials matched. Rejection therefore occurs before model selection; changing models is not a demonstrated fix. The edge response does not disclose whether the underlying rule concerns an individual IP, a network or geography.

No proxy, policy bypass, mock fallback or successful hosted generation is claimed. Public real-AI acceptance requires an OpenRouter access-policy resolution or an explicitly selected provider/hosting change. API health alone does not verify provider access. The final UI and worker scenario must be repeated after that external issue is resolved.

## Deployment boundary

The frontend is published through the Git-connected Vercel project. The API, worker and PostgreSQL belong to the isolated `turovnd-realtime` Docker project. Backend deployment and schema adoption are separate from frontend auto-deployment. A prior image alone is not a safe schema rollback after new analysis runs have been accepted; see [operations](operations.md#schema-aware-rollback).

The release enables real OpenRouter processing for submitted feedback and explicit analysis. Opening a demo seeds deterministic examples without paid calls. The existing cumulative `unlimited` configuration retains its durable counter; each job still has bounded attempts, timeouts and output tokens. Shipped local defaults remain disabled.

## Practical limits

The evaluation is a small synthetic development set, not a held-out quality benchmark. Exact quotes do not prove a summary’s interpretation. No customer-impact, high-throughput or general adversarial-robustness claim is made. The database restore rehearsal verifies this release’s recovery artifact; scheduled off-host backups and recurring recovery drills remain operational work. See [limits](limits.md), [testing](testing.md) and the [MVP plan](planning/README.md).
