# Verification and release

Feedback Desk's agreed MVP is implemented and publicly deployed: feedback review, real AI analysis, preserved run history and isolated workspaces. On 17 November 2026, the public browser completed a real OpenRouter analysis through Vercel and saved its result in Neon. Activity displayed the same result after a full reload.

Technical verification does not imply owner acceptance of the interface. Request recovery now preserves loaded content and offers explicit retry/reload actions. The underlying intermittent platform challenge remains an observed limitation; see [remaining verification](#remaining-verification-and-limits).

## Published application

| Surface                   | Verified identity                                                                                                                                                                                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Verified application code | [`46a8970501c519f1e8f793398c5e6682fa4a9674`](https://github.com/turovnd/realtime-data-workbench/commit/46a8970501c519f1e8f793398c5e6682fa4a9674), published through Git `main`                                                                                                               |
| GitHub CI                 | [Verification workflow](https://github.com/turovnd/realtime-data-workbench/actions/workflows/ci.yml) runs backend, frontend and container/browser checks for each published revision.                                                                                                        |
| Vercel                    | B2Data Pro, `turovnd-feedback-desk`; production deployment `dpl_8mE6AEU5JAbbs2DVX27hVYM1Wnwo`, READY for the same source                                                                                                                                                                     |
| Public UI and API         | [turovnd-feedback-desk.vercel.app](https://turovnd-feedback-desk.vercel.app); same-origin `/api/*`, [Swagger](https://turovnd-feedback-desk.vercel.app/docs), [OpenAPI](https://turovnd-feedback-desk.vercel.app/openapi.json), [readiness](https://turovnd-feedback-desk.vercel.app/health) |
| Processing                | Private native Python subscribers for `feedback-analysis` and `feedback-maintenance`; no continuously running hosted worker                                                                                                                                                                  |
| Database                  | Neon Free, PostgreSQL 18.7, Alembic `0002`; runtime pooled connection and explicit direct migration connection use verified TLS                                                                                                                                                              |
| Live provider             | OpenRouter / `openai/gpt-4.1-mini`, enabled; 800 output tokens, at most three attempts per job, cumulative policy `unlimited` with durable counting                                                                                                                                          |

The project retains its Git connection and production domain after moving to B2Data. Repository-root Services configuration deploys the UI, API and subscribers together. Schema changes remain explicit; Git delivery does not run Alembic. The old server API and worker are stopped, with their database and image retained for deliberate recovery.

## Source verification

| Boundary          | Evidence for the published application                                                                                                                                                                                                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend           | 255 tests passed against disposable real PostgreSQL; Ruff lint/format and strict mypy passed. Includes queue redelivery, post-commit publication failure and repair, expired leases, delayed retries, retention and Neon TLS boundaries.                                                                    |
| Frontend          | 62 unit tests and 28 browser regressions with controlled API responses passed; type checks, lint, formatting and production build passed. Recovery coverage includes retained data, paused failed polling, manual retry/reload, cursor recovery and workspace isolation.                                    |
| API contract      | OpenAPI describes 16 paths; generated client reproduced with `pnpm api:check`. Public readiness, Swagger and schema routes were checked.                                                                                                                                                                    |
| Preview           | A real OpenRouter result was saved and displayed in details and Activity. Full reload retained it; cursor pagination reached 25 of 25 activities.                                                                                                                                                           |
| Preview isolation | All ten production application tables remained empty after preview demo creation and real-AI submission. Preview used its own Neon branch.                                                                                                                                                                  |
| Queue functions   | The HTTP function and both private subscribers were discovered in the deployment. A manual Preview schedule execution reached the recovery handler. An automatic production invocation at 10:00:44 UTC on 17 November 2026 logged `queue_recovery_published count=0` from the private subscriber in `iad1`. |
| Database          | Direct and pooled Neon connections verified certificates and hostnames; explicit Alembic initialization and metadata checks passed. The frozen source data was then copied and verified before publication.                                                                                                 |

These checks establish the stated scenarios and boundaries, not a throughput or availability benchmark. The [AI evaluation](ai-evaluation.md) separately retains four synthetic cases and their prompt-development results; it does not establish representative model accuracy.

## Public real-AI scenario

The reviewer opened an isolated demo with 24 deterministic samples, submitted the editable monthly-export example, followed analysis and opened its saved Activity run. The original text, summary, provider and three exact source quotes were visible. Activity loaded 10, then 20, then all 25 runs; expanded details matched the record page, including after a full reload.

The persisted verification at 09:42 UTC recorded:

- Job `fcad7961-89ca-4608-9862-3d15564c1040`: `succeeded`, one admitted attempt, provider `openrouter/openai/gpt-4.1-mini`.
- Structured output passed validation; all three supporting quotes matched the original message exactly.
- The migrated OpenRouter counter advanced from 3 to 4. The 24 seeded jobs completed with the deterministic provider and made no model calls.

This verifies browser → API → Queue → OpenRouter → Neon → details/Activity in production. It is an authenticated generation check, not just a catalog or health request. Live failures still remain visible and never become sample results.

## Data transfer and recovery evidence

Before either final export, only Feedback Desk's source API and worker were stopped. A full backup and a separate data-only dump were retained in protected source and off-host copies with matching SHA-256 hashes. The prepared Neon database was asserted empty, then the ten application tables were restored atomically without dropping or truncating schema. Alembic remained the schema owner.

All eleven table counts and content fingerprints, including `alembic_version`, matched the frozen source. The metadata check passed and the durable OpenRouter counter remained 3 before the public AI verification. The frozen demo records, account and session tables were empty; preserving those tables is not evidence of migrating active sessions. A separate nonempty fixture exercised their foreign-key relationships during rehearsal.

| Artifact                   | SHA-256                                                            |
| -------------------------- | ------------------------------------------------------------------ |
| Full database backup       | `14786bb7347dfa215d3702ca2ec8ab004171b35fdc387e3f13788aa24a0c4c63` |
| Application data-only dump | `c2ed56c4e7dbc67091b9d20e752aa1d78a262f24a20cda10f125877c8b827a4d` |

Rehearsals restored PostgreSQL 17 data into an Alembic-initialized PostgreSQL 18 database with constraints and immutable-history triggers enabled. The final target was Neon PostgreSQL 18.7. Both final backup copies were restricted to owner access; credentials and storage paths are excluded from this repository.

All 23 active Nginx configuration file hashes and non-target container identities/state remained unchanged. The source database, volume and preceding application image were retained. Its writers remain stopped to prevent two divergent production databases. See [operations](operations.md#schema-aware-rollback) before any recovery action. This is one verified transfer and restore rehearsal, not an automated backup or recurring drill policy.

## Remaining verification and limits

- **Browser recovery:** intermittent refresh failures were followed by a Vercel Security Checkpoint on full navigation. Verification passed automatically; a direct API check returned JSON with HTTP 200. The failing request's exact edge status/rule was not captured. The published error boundary distinguishes an explicit challenge header from an unexpected HTML response without displaying upstream HTML or clearing the session. Retry/reload and polling recovery passed targeted browser regressions. Public details, the saved Activity result and pagination were checked again after publication without a repeated error during that observation. This does not prove the platform challenge can never recur; no security protection was changed.
- **Scheduled recovery:** the thirty-minute production schedule ran automatically at 10:00:44 UTC on the verified deployment (request `2qkp5-1794909643679-0dd17f5ecfea`). No due work needed republication. Real-PostgreSQL tests separately cover recovery of pending and expired work; an empty production scan does not prove an outage-recovery SLA.
- **Product acceptance:** the owner has not yet accepted the final interface. Implemented planning tasks describe delivered capabilities; they do not assert that acceptance.
- **Operational scope:** no high-availability, representative AI-quality, customer-impact or load benchmark is claimed. Recurring backups and alerts remain operational work. Exact quotes make evidence checkable, not necessarily the interpretation correct.

The optional direct DeepSeek adapter has contract and regression coverage, but no authenticated DeepSeek generation is claimed. Production explicitly uses OpenRouter; failed calls are never silently routed to another provider. See [limits](limits.md), [testing](testing.md) and the [MVP plan](planning/README.md).
