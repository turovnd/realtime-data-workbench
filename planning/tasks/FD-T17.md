---
id: FD-T17
type: task
is_task_of: FD-S08
status: verified-hosted
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

- [x] Public source contains no secrets/private inputs and uses the intended remote.
- [x] A real hosted CI run passes for the published revision.
- [x] A push triggers the intended Vercel deployment; backend release automation reports its own tested status.

## Tests and verification

- Secret/source allowlist review, remote identity verification, hosted CI run and deployment revision comparison.
- Verify follow-up commits independently through the configured delivery path.

## Status

**verified-hosted**.

## Implementation evidence

Public source is published to the intended repository. Git `main` commit [a39a83381155](https://github.com/turovnd/realtime-data-workbench/commit/a39a83381155d6d59fdcab0c3fcde3a7f6f9a163) automatically produced READY production deployment `dpl_5ji7FhSV5HjtmTRPmQ5aq41VEtT7`. [GitHub CI run 38000407525](https://github.com/turovnd/realtime-data-workbench/actions/runs/38000407525) succeeded for that exact source revision, including backend, frontend and container jobs. Backend image rollout was verified separately; the release workflow packages an artifact and does not yet establish automatic server deployment.

Implementation and verification locations:

- [.github/workflows/ci.yml](../../.github/workflows/ci.yml)
- [.github/workflows/release.yml](../../.github/workflows/release.yml)
- [web/vercel.json](../../web/vercel.json)
- [docs/delivery-status.md](../../docs/delivery-status.md)
