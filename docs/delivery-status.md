# Delivery status

Current local verification and hosted delivery status. Earlier records are preserved in the [archive](archive/README.md).

| Area                     | Evidence                                                                                                                                   | Current status                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Product baseline         | Real account/demo, cursor isolation and durable worker behavior passed the current local regression.                                       | Verified locally; deployed baseline remains recorded below.                                                                                |
| Public backend           | `https://realtime-api.b2p.space` passed HTTPS, health, auth, cursor/workspace isolation, durable processing and logout checks.             | Deployed.                                                                                                                                  |
| Backend image            | `turovnd-realtime:20261010-feedback` in `turovnd-realtime` with private PostgreSQL and loopback API port 8002.                             | Deployed baseline; refactor has not implicitly replaced it.                                                                                |
| Public UI                | [https://turovnd-feedback-desk.vercel.app](https://turovnd-feedback-desk.vercel.app) returned public HTTP 200 after Vercel reported READY. | Published.                                                                                                                                 |
| Vercel-to-API connection | Coordinator confirmed both exact-origin CORS and UI authentication from the production alias.                                              | Verified for the deployed baseline; full refactored journey pending.                                                                       |
| Source organization      | Runtime modules and tests now use the documented independent boundaries and mirrored root test tree.                                       | Verified locally.                                                                                                                          |
| Schema compatibility     | All 11 SQLAlchemy table assignments and the migration function match the deployed image by AST comparison.                                 | Verified by coordinator; structural release has no schema change.                                                                          |
| Swagger                  | `/docs` with local assets and `/openapi.json` are part of the current API delivery.                                                        | Verified locally; refactored public rollout pending.                                                                                       |
| Public Git repository    | Owner authorized `turovnd/realtime-data-workbench` and Git-connected automatic deployment.                                                 | GitHub repository linked to the correct Vercel project through the official integration; first push and hosted build verification pending. |
| CI/CD                    | Workflow definitions and GitHub-to-Vercel linkage are configured for production main.                                                      | First source push, hosted CI and automatic build verification pending.                                                                     |
| Backups                  | Private persistent volume exists. Off-host backup and restore rehearsal are separate work.                                                 | Not verified.                                                                                                                              |

## Verified baseline

Public HTTPS smoke used two independent demo workspaces, disjoint 12+12 cursor pages, foreign cursor/backfill rejection, actual worker v1 completion, selected v2 processing with preserved original input and v1 output, persisted backfill progress and session revocation. Static checks, real PostgreSQL tests, preview browser tests and connected browser journeys were reported passed before this refactor.

Routine tests and public smoke use deterministic data and no paid model calls. The earlier implementation record reports a separately authorized live adapter smoke; that is not a recurring CI check or a model-quality evaluation.

## Current refactor evidence

The implementation owner verified the current layout locally:

- Ruff lint/format passed for `src`, `../tests/backend` and `../tools`; strict mypy checked 77 source/test modules.
- `uv run --directory backend pytest` with a disposable real PostgreSQL database: 40 tests passed.
- Frontend lint, typecheck and formatting passed; `pnpm test`: 11 unit tests passed.
- `pnpm test:e2e`: 14 desktop/mobile browser-preview scenarios passed.
- OpenAPI tests checked all 12 application paths, response/security models, local Swagger assets and their pinned checksum manifest. A same-origin Swagger auth/feed/logout flow passed against real PostgreSQL.

- Native local Compose rebuilt and API/worker/web/own PostgreSQL were healthy. Three connected browser journeys passed real account persistence/logout cleanup, worker v1-to-v2 history, stable cursor pages during arrivals, selection/search and 410 refresh.
- Frozen offline pnpm installation passed. Browser inspection rendered Swagger operations and Try it out GET /health returned 200.

No live-provider call was rerun during this refactor. The new public image release and hosted Git build remain pending.

## Outstanding delivery gates

1. Deploy the verified refactored image/build and recheck the public pair; the local structural/static/database/browser/container gate is complete.
2. Recheck the production UI/API complete durable workflow after the refactored release. Exact-origin CORS and current UI authentication already passed.
3. Push the reviewed source to the authorized public repository and verify the first hosted CI/build and automatic deployment. Repository-to-Vercel linkage is configured.
4. Verify backend release automation separately from Vercel UI delivery.
5. Configure and rehearse backup restoration before relying on retained account data.

See [planning](../planning/README.md) for task ownership, dependencies and acceptance criteria.
