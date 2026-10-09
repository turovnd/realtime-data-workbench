---
id: FD-T16
type: task
is_task_of: FD-S08
status: verified-hosted
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

- [x] The production alias serves the intended build with the correct API origin.
- [x] Browser auth, cross-origin API requests and one durable workflow complete.
- [x] No wildcard preview CORS and no silent browser-fixture substitution.

## Tests and verification

- Browser request/response and console review from the stable production alias.
- Session logout/revocation and mobile/keyboard smoke.

## Status

**verified-hosted**.

## Implementation evidence

The stable production UI reached READY from Git commit [a39a83381155](https://github.com/turovnd/realtime-data-workbench/commit/a39a83381155d6d59fdcab0c3fcde3a7f6f9a163) in deployment `dpl_5ji7FhSV5HjtmTRPmQ5aq41VEtT7`. Public browser authentication/current server data passed with zero console errors; exact-origin CORS and the complete public deterministic API workflow passed. Production uses the real API origin; feature previews require separate setup.

Implementation and verification locations:

- [web/vercel.json](../../web/vercel.json)
- [web/src/lib/api/auth.ts](../../web/src/lib/api/auth.ts)
- [backend/src/workbench/infrastructure/http.py](../../backend/src/workbench/infrastructure/http.py)
- [docs/delivery-status.md](../../docs/delivery-status.md)
