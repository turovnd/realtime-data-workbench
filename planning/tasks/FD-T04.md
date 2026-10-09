---
id: FD-T04
type: task
is_task_of: FD-S03
status: verified-local
depends_on: ["FD-T01"]
---

# FD-T04: Accounts and workspace sessions

Parent story: [FD-S03](../stories/FD-S03.md).

## Goal

Bind all feedback state to a server-established identity.

## Scope

Independent accounts, Argon2id hashing, persisted auth admission, opaque hashed sessions, deterministic demos and bounded cleanup.

## Dependencies

- [FD-T01](../tasks/FD-T01.md)

## Acceptance criteria

- [x] Foreign workspace data cannot be listed, retried or selected for backfill.
- [x] Logout revokes the token; account data survives anonymous cleanup.
- [x] Auth hashing/admission is bounded.

## Tests and verification

- Real PostgreSQL account/session, rate-bucket and foreign-workspace cases.
- Connected account re-login persistence flow.

## Status

**verified-local**.

## Implementation evidence

Current PostgreSQL and three connected browser journeys passed independent account registration/login, revocation, workspace isolation and persisted results. Database coverage includes bounded auth admission and account-safe anonymous cleanup.

Implementation and verification locations:

- [backend/src/workbench/logic/auth.py](../../backend/src/workbench/logic/auth.py)
- [backend/src/workbench/repositories/accounts.py](../../backend/src/workbench/repositories/accounts.py)
- [tests/backend/src/workbench/logic/test_auth.py](../../tests/backend/src/workbench/logic/test_auth.py)
- [tests/backend/src/workbench/routers/test_auth.py](../../tests/backend/src/workbench/routers/test_auth.py)
