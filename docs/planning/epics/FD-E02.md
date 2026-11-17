---
id: FD-E02
type: epic
---

# FD-E02: Process and reprocess reliably

## Problem

A submitted message is not useful if the reviewer cannot tell whether analysis is running, failed or complete. Reanalysis must not erase earlier evidence.

## Outcome

Make analysis observable and recoverable, from submission through saved results and subsequent runs.

## Acceptance

- Submitting feedback produces visible progress and a real OpenRouter result, or an actionable error.
- Activity shows the exact result of each run, including failed attempts.
- Repeated and grouped analysis preserve the source and completed results.

## Stories

- [FD-S03: Add feedback and inspect processing](../stories/FD-S03.md)
- [FD-S04: Reprocess a fixed selection](../stories/FD-S04.md)
