# Delivery status

**[Live UI](https://turovnd-feedback-desk.vercel.app)** · [Swagger](https://realtime-api.b2p.space/docs) · [OpenAPI](https://realtime-api.b2p.space/openapi.json) · [Public repository](https://github.com/turovnd/realtime-data-workbench)

Production UI deployment from Git `main` is verified. The current API/worker image is deployed, its public workflow checks passed, and GitHub CI succeeded for the source revision linked below.

## Hosted release

| Area                   | Verified evidence                                                                                                                                                                                                                                                                             |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend               | Vercel deployment `dpl_5ji7FhSV5HjtmTRPmQ5aq41VEtT7` reached READY from Git, production `main`.                                                                                                                                                                                               |
| Source revision        | [a39a83381155d6d59fdcab0c3fcde3a7f6f9a163](https://github.com/turovnd/realtime-data-workbench/commit/a39a83381155d6d59fdcab0c3fcde3a7f6f9a163).                                                                                                                                               |
| Backend image          | `turovnd-realtime:20261010-feedback.2`; image configuration digest `sha256:8658d41bff80823abcd149a91f7228c43a389988902b947367a0e4a8da86d233`.                                                                                                                                                 |
| Public Swagger         | HTTPS 200 and 12 operations rendered with local assets; interactive Try it out → Execute returned an actual server response 200 from `GET /health`.                                                                                                                                           |
| Browser/API connection | Production UI authentication and current server data passed; zero console errors. Exact-origin CORS covers the stable production alias.                                                                                                                                                       |
| Database compatibility | All 11 SQLAlchemy table assignments and the migration function matched the preceding deployed image by AST comparison. No schema change was applied.                                                                                                                                          |
| Runtime isolation      | Only this app’s API/worker were replaced. Existing DB/migration containers and data were preserved.                                                                                                                                                                                           |
| GitHub CI              | [Run 38000407525](https://github.com/turovnd/realtime-data-workbench/actions/runs/38000407525) succeeded for source revision [a39a83381155](https://github.com/turovnd/realtime-data-workbench/commit/a39a83381155d6d59fdcab0c3fcde3a7f6f9a163); backend, frontend and container jobs passed. |
| Recovery               | Off-host backups and restore rehearsal remain unverified.                                                                                                                                                                                                                                     |

CI evidence applies to the linked source revision; later documentation commits are checked independently.

## Public workflow verification

The bounded combined HTTPS smoke for both new releases passed: 46 requests in 11.54 seconds, independent authentication/workspaces, disjoint 12+12 cursor pages, durable worker processing and logout revocation. All four issued test tokens were revoked. Feedback additionally verified worker v1 completion and selected v2 backfill while preserving raw input and v1 results.

The final server comparison found all 37 previously running unrelated containers unchanged by ID, start time and state; original nginx configuration hashes were unchanged. Free disk space was 9.21 GiB at that check. These are deployment observations, not ongoing capacity guarantees.

No paid model calls were made by this smoke. The earlier implementation record reports a separately authorized live adapter check; no live-provider retest is claimed for this structural release.

## Current refactor evidence

The current layout passed these local checks:

- Ruff lint/format passed for `src`, `../tests/backend` and `../tools`; strict mypy checked 77 source/test modules.
- `uv run --directory backend pytest` with a disposable real PostgreSQL database: 40 tests passed.
- Frontend lint, typecheck and formatting passed; `pnpm test`: 11 unit tests passed.
- `pnpm test:e2e`: 14 desktop/mobile browser-preview scenarios passed.
- OpenAPI tests checked all 12 application paths, response/security models, local Swagger assets and their pinned checksum manifest. A same-origin Swagger auth/feed/logout flow passed against real PostgreSQL.
- Native local Compose rebuilt and API/worker/web/own PostgreSQL were healthy. Three connected browser journeys passed real account persistence/logout cleanup, worker v1-to-v2 history, stable cursor pages during arrivals, selection/search and 410 refresh.
- Frozen offline pnpm installation passed. Browser inspection rendered Swagger operations and Try it out GET /health returned 200.

No live-provider call was rerun during this refactor. Routine verification remained deterministic.

## Remaining delivery work

1. Keep backend release automation separate from Vercel UI auto-deploy: the current backend rollout used guarded image updates; the repository release workflow packages an image artifact.
2. Configure encrypted off-host backups and verify an isolated restore before relying on retained account data.

Production Git delivery and `VITE_API_URL` cover `main` and the stable production alias. Feature previews require explicit environment/origin configuration. See [operations](operations.md) and [planning](../planning/README.md); earlier records remain in the [archive](archive/README.md).
