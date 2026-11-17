# Operations and deployment

Feedback Desk runs in the owner's B2Data Pro team on Vercel. See [delivery status](delivery-status.md) for the verified source, deployment and data-transfer evidence, and [Vercel deployment](vercel.md) for configuration details.

## Current topology

| Surface                | Destination                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| UI and API             | [turovnd-feedback-desk.vercel.app](https://turovnd-feedback-desk.vercel.app), with `/api/*` routed to FastAPI |
| API documentation      | [Swagger UI](https://turovnd-feedback-desk.vercel.app/docs) and `/openapi.json`                               |
| Readiness              | [`/health`](https://turovnd-feedback-desk.vercel.app/health)                                                  |
| Analysis               | Private Python subscriber on `feedback-analysis`                                                              |
| Recovery and retention | Private subscriber on `feedback-maintenance`, scheduled every thirty minutes                                  |
| PostgreSQL             | Neon Free beside the `iad1` functions, separate production and preview branches                               |
| Local development      | Docker Compose with PostgreSQL and a polling worker                                                           |

There is no continuously polling hosted worker. Queues deliver at least once; PostgreSQL owns leases, accepted results and attempt counts. Failed publication leaves pending rows for recovery. Scheduled recovery and browser polling still consume resources; cold starts add latency. The Free plan is neither unlimited capacity nor a zero-cost promise.

## Delivery and configuration

Production tracks Git `main`. The repository-root Services configuration builds the UI, FastAPI and private subscribers together. `VITE_API_URL=same-origin` keeps browser calls on the deployment's own origin. Model credentials stay server-side. The [deployment guide](vercel.md#project-configuration) owns the complete environment and builder configuration.

Verify preview-specific Neon variables; a static production URL defeats branch isolation. Restrict model credentials to production and reviewed previews. Preview success does not establish production readiness.

For each release:

1. Run the relevant source checks, real-PostgreSQL tests, frontend checks, build and generated-client verification.
2. Check schema compatibility with both the current deployment and queued work. Retain a recoverable backup before data or schema changes.
3. Apply Alembic deliberately through the direct migration connection. API and subscriber startup never change the schema.
4. Verify the preview's private subscribers, authentication, cursor paging, sample processing and bounded real-AI flow before publishing.
5. After Git delivery, verify the production alias, `/docs`, `/health`, processing and saved results in Activity. Record the actual evidence in the release ledger.

A Git deployment does not apply schema migrations. Database changes must tolerate overlapping function revisions and previously queued messages. Avoid destructive schema changes while either can still use the old shape.

## Health and incident checks

`GET /health` checks API/database readiness, not queue consumption or provider availability. Inspect the HTTP function, both private subscribers, queue deliveries and persisted job state when work stalls. Distinguish a platform access challenge from an application or model error. The UI retains loaded data and pauses failed polling; use Try again for a temporary request failure, or Reload page when the service requires a browser check. Unexpected HTML is never rendered as an API error body. Log safe error categories and request/job identifiers, never bearer tokens, database URLs, provider keys or full provider responses.

For smoke verification, open an isolated demo, page through results, wait for sample jobs, then submit one synthetic message for real AI and check Activity. Verify logout and workspace isolation. Samples do not prove a model call; real-model checks need an explicit attempt bound.

If publication fails, retrying an accepted request can notify its existing job without creating another run. Scheduled recovery also scans due work in bounded pages. With healthy infrastructure, redispatch can take roughly thirty-one minutes. Persistent queue, database or provider failures require diagnosis; repeatedly creating new analysis runs is not a recovery policy.

Monitor job age/failures, subscriber errors, retained data, Neon usage and provider attempts. Automatic alerts, high availability and measured throughput are not claimed. External `/health` polling can keep the database active.

## Schema changes and adoption

Use `WORKBENCH_MIGRATION_DATABASE_URL` for an explicit direct connection, or Neon's deployment-specific `WORKBENCH_DATABASE_URL_UNPOOLED`. The runtime pooled URL is only a fallback. Keep credentials out of command arguments and logs. From the repository root, apply migrations with:

```sh
uv run --directory backend python -m workbench.db
```

Before adopting an unversioned local installation, inspect its schema and rehearse on an isolated restore. Use the explicit `--adopt` option only for a supported shape; do not bypass validation with `stamp head`. Compare records, analysis history, accounts, sessions and provider counters before and after. The [setup guide](setup.md#existing-unversioned-database) contains the adoption commands. Adoption or migration may acquire table locks; plan around active writers.

## Backup and restore

Managed storage does not replace a tested backup procedure. Keep encrypted exports outside the active database, define retention and restore into a separate database before relying on them. Use a direct connection for `pg_dump` and `pg_restore`. Verify schema, immutable-history triggers, record/job/result counts, accounts, sessions and provider counters, then run the synthetic workflow. Roles are handled separately from a per-database dump; see the [PostgreSQL backup documentation](https://www.postgresql.org/docs/current/backup-dump.html).

The server-to-Neon transfer used this sequence:

1. Initialize the empty destination through Alembic and verify its revision and metadata.
2. Stop only the source application's API and worker **before** taking the final exports. Capture frozen table counts and content fingerprints.
3. Take a full custom-format backup and a separate genuine data-only dump, excluding `alembic_version`. Retain protected source and off-host copies with matching hashes.
4. Assert all ten destination application tables are empty. Restore the data-only dump in one transaction with errors fatal, without dropping, truncating or replacing the Alembic schema.
5. Compare all eleven tables, including the migration revision, and retained provider counters. Run the Alembic metadata check and verify unrelated containers and active proxy configuration are unchanged.
6. Publish the verified application against Neon. Keep the old writers stopped and retain the source database, image and backups.

A genuine data-only dump records the table-data dependencies needed for restoration into an existing schema. Do not assume selecting data from a full-schema dump has the same restore order. The release rehearsed PostgreSQL 17 to 18 restoration, including a nonempty fixture with foreign keys and immutable-history triggers enabled. Actual transfer evidence is in the [release ledger](delivery-status.md#data-transfer-and-recovery-evidence).

Record exactly what was restored and checked. A release rehearsal does not establish recurring backups or drills; never test restoration over a live database.

## Schema-aware rollback

Keep the preceding deployment and a verified database backup. A deployment rollback changes code, not schema or accepted data. Older deployment-associated queue messages may still be delivered; inspect that work rather than assuming rollback stops it. Prefer a compatible forward fix once new analysis history has been accepted.

The previous server deployment is a preserved recovery source, not a second writable production database. Its Feedback Desk writers were stopped before the final exports and remain stopped. Do not restart them alongside the new writers. Returning traffic to that server after Neon has accepted writes requires a deliberate data-recovery decision. Restoring an older backup may lose later writes and must never happen implicitly.

Preserve the old Feedback Desk volume, backup and deployment identity until the recovery decision is complete. Any server-side action must target only this application's named containers and configuration. Never run global stop/prune commands, remove data volumes during rollout, or alter unrelated services or the shared HTTPS proxy.
