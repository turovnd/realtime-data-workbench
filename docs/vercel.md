# Vercel deployment

The migration candidate packages Vite and FastAPI services in one Vercel project, private Python queue subscribers, and Neon PostgreSQL. The local Docker stack remains available without Vercel credentials. The public UI still uses the previous Docker backend until cutover; see [delivery status](delivery-status.md) for verified deployment evidence.

## Request and processing flow

The browser uses `VITE_API_URL=same-origin`. Root `vercel.json` routes `/api/*`, `/health`, `/docs`, `/openapi.json` and `/docs-assets/*` to FastAPI before routing the remaining paths to the SPA. Both runtime roots retain their own dependencies and build configuration.

A write commits the feedback and analysis job together. Only after commit does the API publish the job ID to `feedback-analysis`. A bounded publication failure leaves the accepted job in PostgreSQL and logs a safe error category. Replaying the same request can publish that pending job again without creating another analysis run.

The private subscriber claims that specific job and performs one bounded attempt. PostgreSQL remains authoritative for the lease, completion fence, global concurrency limit, three-attempt ceiling and provider usage. Duplicate deliveries cannot replace a completed result. A retry uses the job's persisted availability time rather than treating a queue delivery as an AI attempt. External calls and billing are not exactly-once.

The private `feedback-maintenance` subscriber handles a schedule every thirty minutes. It removes expired workspace data and republishes due jobs, including expired leases, in pages of at most 100 IDs. Continuations are separate queue messages. This repairs a crash between database commit and publication without another outbox table. With healthy infrastructure, the scheduled redispatch can take roughly thirty-one minutes; that is not a guarantee of analysis completion. Normal submissions are dispatched immediately.

## Database and idle cost

Neon Free supplies 100 CU-hours and 1 GB per project. With no active browser or work, there is no continuously running worker or half-second database poll. The database can suspend after its idle interval. The recovery schedule still wakes it: at 0.25 CU and five idle minutes per invocation, its thirty-minute cadence alone is approximately 30 CU-hours over thirty days. Actual compute size, user traffic, retries, previews and retention work affect usage. An open browser also refreshes data. Free capacity is a usage limit, not an unlimited availability guarantee.

Keep API, queue and database in the same region. The initial selected region is `iad1`, where a Vercel Function reached OpenRouter's public model catalog. A catalog response does not prove authenticated generation.

Vercel Functions and Queues use the team's metered infrastructure allowance; OpenRouter calls are billed separately. There is no standing Daemon allocation. Sources: [Neon plans](https://neon.com/docs/introduction/plans), [Vercel Queues pricing](https://vercel.com/docs/queues/pricing).

## Project configuration

Use the repository root as the Vercel project root. Build settings belong to the services in `vercel.json`; clear previous project-level Vite build/output overrides. Keep Node 24 and the pinned pnpm workspace. The backend service points at `pyproject.toml` so the Python builder discovers both the FastAPI entrypoint and registered subscribers. Verify a project function duration of at least sixty seconds for the private subscribers; the API's thirty-second override does not configure their duration.

| Variable                                  | Purpose                                                                    |
| ----------------------------------------- | -------------------------------------------------------------------------- |
| `VITE_API_URL=same-origin`                | Browser requests stay on their deployment's origin.                        |
| `WORKBENCH_DATABASE_URL`                  | Runtime connection injected by Neon with the `WORKBENCH` prefix.           |
| `WORKBENCH_DATABASE_URL_UNPOOLED`         | Direct connection injected by Neon, used for explicit migrations.          |
| `WORKBENCH_MIGRATION_DATABASE_URL`        | Optional explicit direct-connection override for local release operations. |
| `WORKBENCH_QUEUE_ENABLED=true`            | Enable post-commit queue publication. Local Docker defaults to false.      |
| `WORKBENCH_QUEUE_REGION=iad1`             | Queue region shared by publishers and consumers.                           |
| `WORKBENCH_PROVIDER_MODE=openrouter`      | Provider for new user-submitted analysis jobs.                             |
| `WORKBENCH_OPENROUTER_CALLS_ENABLED=true` | Enable real analysis explicitly.                                           |
| `WORKBENCH_OPENROUTER_API_KEY`            | Server-side secret; never a frontend variable.                             |
| `WORKBENCH_LIVE_CALL_BUDGET=unlimited`    | Preserve the owner-authorized cumulative policy; attempts remain bounded.  |

Use verified TLS. The database adapter accepts standard PostgreSQL connection strings and translates `sslmode=require` to CA and hostname verification. asyncpg does not implement libpq's `channel_binding` option. For Neon hosts, its generated `channel_binding=require` configuration is translated to verified TLS following [Neon's guidance for clients without channel-binding support](https://neon.com/docs/connect/connect-securely#channel-binding-for-enhanced-security). Unknown or conflicting requirements fail explicitly; the adapter does not remove arbitrary database security settings.

Enable Neon's required preview-branch action and verify its deployment-specific connection variables. Never copy a production connection string into a static Preview override: that would bypass branch isolation. Live model credentials should be limited to production and the explicitly reviewed migration preview branch. Untrusted pull requests must not receive provider or database credentials.

## Release and verification

1. Run formatting, lint, type checks, real-PostgreSQL backend tests, frontend tests, build and generated-client verification.
2. Preserve the existing database and a verified backup. Apply Alembic deliberately using the direct migration connection; application startup does not change the schema.
3. Build a preview with its own Neon branch. Inspect the generated HTTP function and both private queue subscribers. Verify migrations, authenticated API access, cursor paging and sample-job completion there.
4. Perform a bounded real OpenRouter analysis. Confirm source quotes, provider identity and the same persisted result in Activity, then repeat or retry deliberately to verify the UI lifecycle.
5. At cutover, stop only the old Feedback Desk writers, take a fresh database export and restore it into the prepared production database. Verify schema, records, sessions and provider counters before changing the public deployment. Preserve the old volume and image.
6. Publish the reviewed commit through the existing Git connection. Verify the production domain, `/docs`, database readiness and a real analysis after deployment. Record actual source/deployment identities and checks in the release ledger.

Rollback requires both code and data compatibility. Queue messages can remain associated with an earlier deployment, so a rollback does not prove those consumers have stopped. Keep payloads and schema compatible across the transition and inspect pending jobs. Returning traffic to the old server after the new database has accepted writes requires a data-recovery decision; do not silently discard those writes.
