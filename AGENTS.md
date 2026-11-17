# Feedback Desk repository rules

## Authority and provenance

The owner authorized finishing the Feedback Desk MVP, verifying its real-AI scenario, rewriting the README, publishing the current code to turovnd/realtime-data-workbench and updating the existing Vercel/Docker demo. Release only after the relevant checks pass; verify the exact repository, Vercel project and Docker project before changing them. Preserve unrelated applications, files, services, volumes and proxy configuration. Inspect status before edits and retain the owner's documentation moves/deletions.

Build independently with AI assistance and synthetic data. Do not copy private client implementations, datasets, comments, screenshots, logs or history. Do not invent authorship, dates, commits, reviews, credentials, production metrics or test results. Never commit secrets or private local paths. Code, comments, UI and documentation are English.

## Source ownership and style

- Keep `frontend/` and `backend/` as independent runtime roots in this repository. The frontend uses the root pnpm workspace and lockfile.
- Routing uses `createBrowserRouter` and `RouterProvider`, typed route groups in `routes-auth.tsx` / `routes-main.tsx`, shared `Path` constants, lazy page imports and explicit route error handling. Keep the router instance stable; do not replace this with a JSX `BrowserRouter` / `Routes` tree.
- Pages are implemented directly in `frontend/src/pages/<name>/index.tsx`, with named arrow exports. Truly unique page components live directly beside `index.tsx`, not in a page-specific `components/` hierarchy.
- Reusable and potentially reusable domain components live in `frontend/src/components/<domain>`. Within `feedback`, use `Feed.tsx`, `Filter.tsx`, `Summary.tsx` and named exports through `index.ts`; avoid repeated domain prefixes.
- Public aliases contain at most two segments after `@/`: `@/components/ui`, `@/components/feedback`, `@/pages/auth`, `@/api`. Use named public barrel exports. Local sibling imports remain relative. Generated API and upstream shadcn internals may retain their supported conventions.
- Hand-written TypeScript uses `export const name = (...) => {}`, explicit types, `import type`, early returns and small injected modules. Separate imports, types, declarations and operation phases with readable blank lines. Prettier configuration is the shared formatting authority.
- Generate the fetch client with pinned `swagger-typescript-api` from the actual FastAPI OpenAPI schema. Never hand-edit `frontend/src/api/generated.ts`. Keep session/error handling and runtime validation at a small application boundary; generated types are not runtime validators.
- Backend entrypoints live in `backend/modules/api` and `backend/modules/worker`; shared code lives in `backend/common`. Tests mirror these directories.
- Python separates domain ORM models, routers, schemas, logic, concrete query functions, infrastructure and workers. Alembic owns schema changes; runtime startup never creates or alters tables. Use ORM `Session` / `Query` for application database operations and typed model attributes rather than RowMapping dictionaries. Use typed snake_case functions, async I/O, strict boundary schemas and a session per concurrent unit of work. Business logic does not depend on HTTP handlers.

Use the official shadcn Nova / Neutral / Blue / chartBlue / Inter / Lucide preset and semantic tokens. Follow the owner's public barrel requirement. Server state belongs in TanStack Query; shareable filters belong in URLs. Keep derived state derived. Add stores or infrastructure only for a demonstrated need.

## Tests and verification

Frontend tests live in `frontend/tests/`, backend tests in `backend/tests/`, mirroring their source owners. Distinguish unit, API, real PostgreSQL, worker and browser checks. Test observable behavior rather than duplicating implementation. Use deterministic providers; paid calls require explicit authorization and enforced budgets.

Run relevant formatting, lint, type checks, unit tests and builds. Verify browser keyboard/focus, loading/empty/error/recovery, authentication, pagination and offline behavior. Database guarantees require disposable real PostgreSQL tests, including concurrency/recovery. Screenshots and mocks are not complete flow evidence.

Keep requests, sessions, jobs, retries, provider output and costs bounded. Persist admission, fencing and idempotent effects. Do not claim exactly-once external calls or billing. Credentials stay server-side; `VITE_*` values are public.

## Documentation and planning

`README.md` is the short entry point. `docs/` contains current guidance; `docs/planning/README.md` is the compact product plan. Epics describe product outcomes, stories describe user outcomes, and meaningful tasks record their parent, dependencies, acceptance, tests and status. The agreed first MVP covers feedback review and AI analysis, including Activity, authentication and workspace isolation. Problem grouping, roadmap and team collaboration are outside this MVP; do not retain them as pending MVP tasks or imply a later release is promised. Keep one current plan without archives or product versioning. Owner acceptance and successful technical checks are separate states.

Keep public documentation focused on the product, setup and engineering decisions. Do not add deployment ledgers, account/team identities or historical test counts. Epics and stories describe intended outcomes and acceptance; implementation evidence and status belong to tasks. Report actual checks in the release response.
