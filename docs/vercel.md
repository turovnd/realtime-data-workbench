# Deployment

The frontend, FastAPI and private Python subscribers deploy together through Vercel Services. PostgreSQL is hosted in Neon. Local Docker remains independent of both services.

## Routing and environment

`vercel.json` routes `/api/*`, `/health`, `/docs`, `/openapi.json` and Swagger assets to the backend. Other routes go to the frontend. Both use the same origin.

| Setting                                   | Purpose                                             |
| ----------------------------------------- | --------------------------------------------------- |
| `VITE_API_URL=same-origin`                | Browser requests use the current deployment.        |
| `WORKBENCH_DATABASE_URL`                  | Pooled runtime PostgreSQL connection.               |
| `WORKBENCH_DATABASE_URL_UNPOOLED`         | Direct connection for explicit migrations.          |
| `WORKBENCH_QUEUE_ENABLED=true`            | Publish accepted jobs to Queues.                    |
| `WORKBENCH_QUEUE_REGION=iad1`             | Keep processing beside the database.                |
| `WORKBENCH_PROVIDER_MODE=openrouter`      | Select live AI processing.                          |
| `WORKBENCH_OPENROUTER_CALLS_ENABLED=true` | Enable model requests.                              |
| `WORKBENCH_OPENROUTER_API_KEY`            | Sensitive server-side credential.                   |
| `WORKBENCH_LIVE_CALL_BUDGET`              | Durable cumulative attempt ceiling, or `unlimited`. |

Link the repository root to the Services project. Remove frontend-only build/output overrides; the service definitions own them. The project needs a Python function timeout of at least 60 seconds for the recovery subscriber; the API is limited to 30 seconds in configuration. Use the Node version declared by the repository.

Connect production and preview to separate Neon branches. Do not give a preview a static production database URL. Restrict live-model credentials to production and deliberately reviewed previews. Runtime TLS verifies the database certificate and hostname.

## Processing

The private `feedback-analysis` subscriber processes durable job IDs. Queue redelivery is at least once; PostgreSQL owns attempt counts, leases and accepted results. Publication happens after the database commit and has a short timeout.

The `feedback-maintenance` subscriber repairs missed publications, expired leases and retention every 30 minutes. It processes bounded pages and publishes continuation messages when needed. With healthy infrastructure, this repair path can take roughly 31 minutes including schedule jitter. It is not an analysis completion SLA.

No continuously running hosted worker is needed. Idle database suspension reduces compute use, but scheduled scans and open browser tabs wake the database. Neon quotas, Vercel usage and OpenRouter billing are separate; no fixed monthly cost is assumed.

## Release and recovery

1. Run source, database, generated-client and browser checks.
2. Back up data before schema changes. Apply Alembic through the direct connection; builds and application startup do not migrate the database.
3. Verify a preview: authentication, cursor paging, private subscribers and a synthetic real-AI submission.
4. Push the reviewed code through the Git integration. Check the production alias, Swagger, readiness and saved Activity result.

`/health` checks API/database readiness, not model availability or worker progress. Diagnose processing through persisted jobs and private subscriber logs; never log credentials or full provider response bodies.

A code rollback does not roll back the schema or accepted feedback. Queued messages may still target an earlier deployment, so keep transitions compatible and prefer a compatible forward fix after new writes. Restore backups into a separate database and verify them before changing traffic. Never run old and new databases as independent writable production copies.
