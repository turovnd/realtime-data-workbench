# ADR 0002: Vercel UI and independent Docker backend

Status: accepted and used by the deployed baseline. The earlier text is preserved in [the historical archive](../archive/initial-delivery/decisions/0002-hybrid-hosting.md).

The browser UI runs on Vercel and calls the HTTPS API directly. The API, separate durable worker and PostgreSQL run in this repository's own Docker project. Durable jobs are committed in PostgreSQL with business state, then leased and fenced by workers. Vercel Services, Queues, Redis and Kafka are not required by this delivery.

Feedback uses polling, stable feed views and immutable result versions. Each repository owns accounts, schema, tests, images and release verification. The existing reverse proxy is shared infrastructure; unrelated services are outside this app's change scope.

Exact CORS origins and bearer authentication serve different purposes. Git publication to the authorized public `turovnd/realtime-data-workbench` repository and automatic delivery are now authorized; older no-push statements in archived planning do not apply.

Consequences: separate frontend/backend releases, explicit schema compatibility, server maintenance, resource bounds and backup responsibility. The current two independent PostgreSQL instances are retained. [Operations](../operations.md) and [delivery status](../delivery-status.md) distinguish deployed behavior from pending integration work.
