---
id: FD-T16
type: task
is_task_of: FD-S08
status: pending
depends_on: ["FD-T13", "FD-T15"]
---

# FD-T16: Vercel UI and exact API origin

Parent story: [FD-S08](../stories/FD-S08.md).

## Goal

Make the published frontend usable against its real independent API.

## Scope

Build with the correct public API origin, use the exact stable Vercel alias in server CORS, and verify a full connected browser flow.

## Dependencies

- [FD-T13](../tasks/FD-T13.md)
- [FD-T15](../tasks/FD-T15.md)

## Acceptance criteria

- [ ] The production alias serves the intended build with the correct API origin.
- [ ] Browser auth, cross-origin API requests and one durable workflow complete.
- [ ] No wildcard preview CORS and no silent browser-fixture substitution.

## Tests and verification

- Browser request/response and console review from the stable production alias.
- Session logout/revocation and mobile/keyboard smoke.

## Status

**pending**.

## Implementation evidence

Vercel reported READY and the stable production alias returned HTTP 200. Coordinator also confirmed exact-origin CORS and UI authentication. A complete refactored browser workflow remains pending.

Implementation and verification locations:

- [web/vercel.json](../../web/vercel.json)
- [web/src/lib/api/auth.ts](../../web/src/lib/api/auth.ts)
- [backend/src/workbench/infrastructure/http.py](../../backend/src/workbench/infrastructure/http.py)
- [docs/delivery-status.md](../../docs/delivery-status.md)
