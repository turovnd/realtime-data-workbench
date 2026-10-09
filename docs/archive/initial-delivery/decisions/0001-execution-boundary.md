# ADR 0001: durable state and bounded execution

Date: 2026-10-09. **Status: superseded by [ADR 0002](0002-hybrid-hosting.md).** The original proposal is retained below for context; it is not the selected deployment topology.

## Context

The demo needs retryable AI work, inspectable state and recovery after interruption. Frontend and services should run on Vercel; local use must work without model credentials or a managed queue account.

## Proposed decision

Keep business state, jobs, idempotency records and audit events in PostgreSQL. A small execution adapter runs bounded handlers: a separate local worker in development, Vercel Queues push consumers in hosting. Messages carry job references, not the source of truth. Work is at least once; database effects have explicit deduplication and fencing. Commit dispatch intent with the job, publish outside the transaction, and republish ambiguous outcomes. Reconcile unpublished/expired claims and published jobs that never started, including broker TTL expiry. Distinguish dispatch-pending from running in the UI. A daily Hobby reconciliation trigger alone does not promise low-latency recovery; the UI must expose resume while retries and direct publish handle normal operation.

Use SSE with commit-consistent cursors and bounded connections for one-way browser updates. Persist backfill pause/resume and checkpoints rather than holding a request open. Start with a single database-adjacent region. Keep provider requests outside transactions and limit concurrency across instances.

## Alternatives and consequences

- Vercel Workflows can provide durable steps and resumable backfill orchestration. It is a valid alternative if a later spike proves a smaller implementation; do not combine a custom orchestration engine and Workflows for the same state transitions. Python SDK maturity and retention require review.
- Queue beta is a deployment dependency. If unacceptable, retain Vercel frontend/API and use a separately approved continuous worker runtime with the same DB job contract. This adds a host and operational surface. A bounded manual-resume demo is possible but must explicitly disclose that it does not autonomously recover.
- Services beta permits a frontend and backend in one Vercel project. Two Vercel projects per repository are the fallback if this routing/build path fails or beta coupling is unacceptable.
- Kafka adds consumer-group/partition semantics and another service. Those do not solve an unmet v1 need; defer it. A persistent consumer cannot live in a request Function.
- Browser service workers cache the app shell and selected read-only synthetic snapshots. They are unrelated to server durability and never start ingestion or backfill offline.

## Acceptance evidence still needed

Real-DB concurrent claims and stale completions; crash between commit and publish; exhausted retries; replay after cursor expiry; bounded connection usage; queue preview isolation and deployment-version behavior; actual Function timeout and stream recovery. Platform docs establish documented support, not successful operation in this account. See [deployment research](../deployment-research.md).
