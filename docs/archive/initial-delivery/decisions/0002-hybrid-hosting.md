# ADR 0002: Vercel frontend and Docker backend

Date: 2026-10-09. **Status: hosting decision accepted by the owner; implementation and deployment pending.** Supersedes the hosting and queue-dispatch portions of ADR 0001.

## Decision

Deploy the React/Vite UI to Vercel. Run the API, a separate worker and PostgreSQL on the owner's existing server through Docker Compose. Each repository retains its own local startup, database configuration and tests. A shared HTTPS reverse proxy routes to independent backend stacks; preserve the server's existing configuration until inspected.

The browser connects directly to the HTTPS API for requests and SSE. Exact frontend origins are allowlisted; session/authorization and preview data isolation remain explicit contracts. First visual previews may use labelled deterministic browser data while the real backend is unfinished. A preview is not proof of API/DB integration.

Commit jobs in PostgreSQL together with business state. A dedicated worker polls, leases, retries and checkpoints bounded work. No Vercel Services, Queues, managed workflow runtime, Redis or Kafka is required. Persisted state and fencing provide recovery; permanent process lifetime is not itself a durability guarantee.

## Consequences

The server needs image updates, resource limits, monitoring, off-server backups and tested recovery. It is a shared failure domain; high availability is not claimed. Preview and production deployments must not share privileged mutable data. CORS does not replace authentication, and cross-site preview cookies need explicit testing or a stable same-site staging setup.

Backend deployment is independent from Vercel UI deployment. Keep API changes compatible across releases, run migrations deliberately and smoke-test the paired UI/API version. The selected topology is authorized; still obtain the exact server/access/domain and verify readiness before changing it. Public GitHub pushes and unrelated existing-service changes are outside this decision.

## Evidence and remaining verification

See [the hybrid deployment plan](../hybrid-deployment.md) for official sources and execution steps. Real-DB concurrency/recovery, proxy streaming, browser CORS/session behavior, preview isolation, Compose startup, migrations, backups and deployment smoke tests remain to be implemented and executed.
