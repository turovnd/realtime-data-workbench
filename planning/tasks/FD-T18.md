---
id: FD-T18
type: task
is_task_of: FD-S08
status: backlog
depends_on: ["FD-T15"]
---

# FD-T18: Backup and restore rehearsal

Parent story: [FD-S08](../stories/FD-S08.md).

## Goal

Recover retained account data independently of the running volume.

## Scope

Configure encrypted off-host database exports and retention, then restore into a new isolated database without touching existing service data.

## Dependencies

- [FD-T15](../tasks/FD-T15.md)

## Acceptance criteria

- [ ] A backup exists outside the application host with a documented retention/access policy.
- [ ] Restore recreates schema, ownership and expected rows; a complete synthetic flow passes.
- [ ] Recovery scope and rollback limitations are documented.

## Tests and verification

- pg_dump/pg_restore rehearsal on isolated storage.
- Row-count/schema checks and post-restore app/worker smoke.

## Status

**backlog**.

## Implementation evidence

Private persistent volumes exist. Off-host backup configuration and successful restore have not been verified.

Implementation and verification locations:

- [docs/operations.md](../../docs/operations.md)
- [compose.yaml](../../compose.yaml)
