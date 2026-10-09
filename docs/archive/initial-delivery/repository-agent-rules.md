# Portfolio implementation rules

## Current stage and authority

Implementation is authorized following the completed style/scenario checkpoint. At the time of this decision, only documentation and small style samples exist; update status as work is verified. Hand-written TypeScript arrow exports are confirmed. The owner selected Vercel UI plus Docker-hosted API, workers and PostgreSQL on their existing server. The owner accepted both scenarios and the Python style; full implementation is authorized. Latest explicit user instructions override the historical plan.

## Provenance and privacy

- Build independently with synthetic data. Never copy private client code, comments, schemas, domains, ticket IDs, datasets, screenshots, logs or Git history.
- Keep career records, education documents, credentials, source manifests and private local paths out of this repository.
- State AI assistance accurately. Do not invent manual authorship, commits, review discussions, production metrics, credentials or titles.
- The owner requested UI deployment on Vercel and backend deployment on their existing Docker server. Proceed within those destinations once the application and required destination/access details exist; do not ask again for generic hosting approval. Public Git pushes, remote creation, purchases and old-repository deletion/archive remain unauthorized. Preserve unrelated deployed services.
- Preserve existing work. Inspect status before edits; do not reset or discard unrelated changes.
- Communicate with the owner in Russian. Code, comments, README, ADRs, UI copy and project documentation are English.

## Code style

- Hand-written TypeScript components, hooks, helpers and factories use `export const name = (...) => {}` (or a local `const` when not exported). The obsolete named-function baseline is superseded. Keep generated upstream UI code in its supported conventions.
- Prefer explicit domain/transport types, `import type`, early returns, small focused modules and dependency injection through arguments. Validate external data at runtime; avoid `any` and unchecked casts.
- Separate route composition, feature UI, API clients, query keys/hooks, domain behavior and persistence. Do not reproduce a large reference monorepo's package count.
- Server state belongs in TanStack Query; shareable filters belong in the URL. Add a client store only for demonstrated cross-component state needs. Keep derived state derived.
- Use official `@shadcn` components through its CLI and available skill. Inspect current component docs and generated files; preserve accessible composition, semantic tokens and component variants.
- Node: use Fastify with an app factory separate from listening, schema-owned routes and explicit dependencies. Historical backend style is a structural reference, not a framework requirement.
- Python baseline accepted by the owner: typed `snake_case` functions, `async def` for async I/O, strict Pydantic boundary models, explicit dependencies, and a session per concurrent unit of work. This is an agreed convention for these new demos, not an authorship claim about historical Python code.
- Proposed tools: pnpm, ESLint, Prettier and strict TypeScript; uv, Ruff formatting/lint and strict mypy for Python. Pin tested versions after the checkpoint. Do not add abstraction or infrastructure merely to signal seniority.

## Evidence and delivery requirements

- Distinguish proposed, implemented, executed and deployed. Never claim an app check passed because an isolated sample passed.
- Require lint, formatting, typecheck, unit/integration/E2E checks and CI/CD. Database guarantees require real PostgreSQL integration tests, including concurrent transactions and worker recovery.
- Exercise the UI in a browser: keyboard/focus, accessible names, loading, empty, error, stale, cancellation and recovery states. A screenshot alone is insufficient.
- Use deterministic inputs and controlled promises/clocks where practical. Do not use arbitrary test sleeps or coverage targets as proof of correctness.
- Keep jobs, client buffers, request sizes, model output, retries and provider spending bounded. Keep credentials server-side. No live paid calls without authorization.
- Separate browser service workers, request-scoped serverless Functions, and durable job execution. Do not rely on an in-memory task or `waitUntil` for durable progress.
- Test at-least-once delivery with idempotent database effects; do not claim general exactly-once execution or billing.
- Keep README and ADR status aligned with actual implementation. Publish benchmarks only after measuring reproducible inputs and environment.
