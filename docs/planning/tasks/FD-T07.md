---
id: FD-T07
type: task
is_task_of: FD-S03
status: implemented
depends_on: [FD-T04, FD-T05]
---

# FD-T07: Complete the public real-AI demonstration

Parent: [FD-S03](../stories/FD-S03.md). Dependencies: [FD-T04](FD-T04.md), [FD-T05](FD-T05.md).

## Scope

Move the API and analysis execution to the existing Vercel project with Neon Free so a public reviewer can complete the real-AI journey. Preserve existing data and unrelated server applications.

## Acceptance

- A public submission produces a real OpenRouter result, exact source quotes and the same saved run in Activity.
- The Vite frontend and FastAPI backend share one deployment origin; Swagger UI remains available.
- Database migration is explicit. Existing records, sessions and provider counters are preserved and verified before cutover.
- Queue redelivery, publication failure and expired leases preserve bounded, recoverable processing. No continuously running hosted worker is required.
- Preview databases are isolated, credentials remain server-side, and the existing Git connection publishes the reviewed code.
- README, deployment guidance and the release ledger describe the actual running revision and remaining limits.

## Tests

Real PostgreSQL queue/recovery regressions; Vercel build and subscriber discovery; Neon TLS and preview isolation; public browser submission, result and Activity checks; bounded authenticated OpenRouter generation.

## Evidence and status

The public UI, API and private Queue subscribers run in B2Data Pro with Neon Free. All eleven source table fingerprints and the provider counter matched after transfer; unrelated server workloads and proxy configuration were unchanged. The old application writers remain stopped.

A public submission completed one real OpenRouter attempt, saved three exact source quotes and appeared in Activity after reload. Cursor pagination reached 25 of 25 runs. Preview database isolation and a manual recovery-schedule invocation were verified. The production recovery subscriber ran automatically at 10:00:44 UTC on 17 November 2026 and reported no due work to republish.

The capability is implemented. Owner interface acceptance and the observed platform challenge remain explicit in [delivery status](../../delivery-status.md).
