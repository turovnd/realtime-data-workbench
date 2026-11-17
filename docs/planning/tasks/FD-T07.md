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

Host the UI, API and analysis execution so a public reviewer can complete the real-AI journey without local setup.

## Acceptance

- A public submission produces a real OpenRouter result, exact source quotes and the same saved run in Activity.
- The Vite frontend and FastAPI backend share one deployment origin; Swagger UI remains available.
- Database migrations are explicit and preserve existing records, sessions and provider counters.
- Queue redelivery, publication failure and expired leases preserve bounded, recoverable processing. No continuously running hosted worker is required.
- Preview databases are isolated, credentials remain server-side, and the existing Git connection publishes the reviewed code.
- README and deployment guidance explain the product, setup and engineering limits.

## Tests

Real PostgreSQL queue/recovery regressions; Vercel build and subscriber discovery; Neon TLS and preview isolation; public browser submission, result and Activity checks; bounded authenticated OpenRouter generation.

## Evidence and status

Implemented with Vercel Services, private Queue subscribers and Neon PostgreSQL. Queue integration tests cover redelivery and publication recovery. The public flow exposes provider provenance and saved Activity results; the verification procedure is in [testing](../../testing.md).
