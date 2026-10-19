---
id: FD-T01
type: task
is_task_of: FD-S01
status: implemented
depends_on: []
---

# FD-T01: Workspace and session foundation

Parent: [FD-S01](../stories/FD-S01.md). Dependencies: None.

## Scope

Retain personal accounts, isolated demo workspaces and private client state.

## Acceptance

- Sessions are established server-side and scoped to one workspace.
- Logout and identity changes clear private state; stale requests cannot replace a newer session.

## Tests

Auth/client unit tests and real PostgreSQL workspace/session tests.

## Evidence and status

Implemented. Current auth/client units, connected logout and workspace-isolation journeys, and real PostgreSQL session tests pass locally.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
