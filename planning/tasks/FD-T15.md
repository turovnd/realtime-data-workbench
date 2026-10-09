---
id: FD-T15
type: task
is_task_of: FD-S08
status: verified-hosted
depends_on: ["FD-T13"]
---

# FD-T15: Isolated backend delivery

Parent story: [FD-S08](../stories/FD-S08.md).

## Goal

Run this API, worker and database without disturbing unrelated server services.

## Scope

Use the own Compose project, private database/network/volume, loopback API, versioned image, exact proxy trust, TLS and bounded resources/logs.

## Dependencies

- [FD-T13](../tasks/FD-T13.md)

## Acceptance criteria

- [x] Migrations and readiness pass for a verified image.
- [x] A bounded public synthetic workflow proves worker and persistence.
- [x] Original unrelated services/configuration and own non-target containers remain unchanged.

## Tests and verification

- HTTPS auth/cursor/worker/logout smoke.
- Before/after container/image/config checks and targeted rollback rehearsal.

## Status

**verified-hosted**.

## Implementation evidence

Image `turovnd-realtime:20261010-feedback.2` is deployed with configuration digest `sha256:8658d41bff80823abcd149a91f7228c43a389988902b947367a0e4a8da86d233`. DB/migration containers were preserved, unchanged schema was verified and public HTTPS worker/auth/cursor/logout smoke passed. Final isolation checks preserved all 37 previously running unrelated containers and original nginx files.

Implementation and verification locations:

- [compose.yaml](../../compose.yaml)
- [backend/Dockerfile](../../backend/Dockerfile)
- [.github/workflows/release.yml](../../.github/workflows/release.yml)
- [docs/operations.md](../../docs/operations.md)
