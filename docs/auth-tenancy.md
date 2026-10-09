# Authentication and tenancy

Each app is independent. This repository has its own accounts, bearer sessions, workspace IDs and database; a token from the other portfolio app grants no access here.

## Identity and session boundary

Passwords use Argon2id with bounded memory and two concurrent hash slots. Authentication admission is persisted per IP, with additional per-email limits for registration/login.

Opaque bearer tokens expire after 24 hours and are revocable. PostgreSQL stores token hashes; browser session storage holds the token for the configured API. The server resolves workspace identity from the authenticated token. Workspace IDs supplied by a client are never authority to read or mutate another workspace.

Protected routes require `Authorization: Bearer <token>`. Logout revokes the server session and clears private client state. Delayed failures from an old request must not clear a newer session; delayed login/demo results must not resurrect a logged-out session. CORS permits exact frontend origins but does not replace authentication.

## Workspace ownership

An anonymous demo receives 24 synthetic feedback messages and deterministic jobs. An account starts with an empty workspace and can request bounded synthetic batches. Inputs, jobs, result versions, feed views and backfills are scoped to that workspace.

Anonymous work expires after 24 hours through bounded cleanup. Account data is excluded from demo cleanup; its sessions still expire. Neither session expiry nor logout claims to delete retained account data.

Offline snapshots are explicit read-only copies of loaded synthetic records. Cache identity includes workspace/session scope; logout removes private query and snapshot state. The service worker caches only the app shell/assets and ignores cross-origin API calls, /api/ requests and non-GET requests.

## Limitations

Email identity is unverified. There is no email delivery, password reset, OAuth, organization membership, roles or tenant administration in this slice. Application scoping and real-database isolation tests are implemented; independent security certification and production tenancy assurances are not claimed. Use synthetic data only.

See [API](api.md), [limits](limits.md) and [testing](testing.md).
