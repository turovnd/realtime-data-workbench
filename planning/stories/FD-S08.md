---
id: FD-S08
type: story
is_story_of: FD-E04
status: in-progress
---

# FD-S08: Independent hosted delivery and recovery

Parent: [FD-E04](../epics/FD-E04.md).

## User or maintainer outcome

Ship the UI/backend through verified delivery paths and retain recovery controls.

## Tasks

- [FD-T15: Isolated backend delivery](../tasks/FD-T15.md) — verified-hosted.
- [FD-T16: Vercel UI and exact API origin](../tasks/FD-T16.md) — verified-hosted.
- [FD-T17: Public Git and automatic delivery](../tasks/FD-T17.md) — verified-hosted.
- [FD-T18: Backup and restore rehearsal](../tasks/FD-T18.md) — backlog.

## Acceptance and evidence

All linked task criteria must be met, required tests executed, and current evidence recorded. This story remains open when a linked refactor/hosted check is pending, even if the deployed baseline already supports the user behavior. No dependency on the other portfolio repository is introduced.
