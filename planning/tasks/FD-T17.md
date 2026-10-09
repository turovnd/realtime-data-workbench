---
id: FD-T17
type: task
is_task_of: FD-S08
status: in-progress
depends_on: ["FD-T13", "FD-T14", "FD-T16"]
---

# FD-T17: Public Git and automatic delivery

Parent story: [FD-S08](../stories/FD-S08.md).

## Goal

Turn the reviewed public repository into a reproducible delivery source.

## Scope

Create/push the explicitly authorized turovnd repository, connect the correct Vercel project, configure CI and verify push-triggered UI delivery. Track backend automation separately.

## Dependencies

- [FD-T13](../tasks/FD-T13.md)
- [FD-T14](../tasks/FD-T14.md)
- [FD-T16](../tasks/FD-T16.md)

## Acceptance criteria

- [ ] Public source contains no secrets/private inputs and uses the intended remote.
- [ ] A real hosted CI run passes for the published revision.
- [ ] A push triggers the intended Vercel deployment; backend release automation reports its own tested status.

## Tests and verification

- Secret/source allowlist review, remote identity verification, hosted CI run and deployment revision comparison.
- Exercise a harmless follow-up change through the configured delivery path.

## Status

**in-progress**.

## Implementation evidence

The owner authorized public publication. The coordinator confirmed GitHub-to-Vercel linkage through the official integration. First source push, hosted CI and a push-triggered build remain unverified.

Implementation and verification locations:

- [.github/workflows/ci.yml](../../.github/workflows/ci.yml)
- [.github/workflows/release.yml](../../.github/workflows/release.yml)
- [web/vercel.json](../../web/vercel.json)
- [docs/delivery-status.md](../../docs/delivery-status.md)
