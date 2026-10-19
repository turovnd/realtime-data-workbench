# Feedback Desk

A first MVP for reviewing product feedback: browse a stable feed, inspect original messages and evidence-backed enrichment, and reprocess selected records without losing earlier results.

[Published application](https://turovnd-feedback-desk.vercel.app) · [Public repository](https://github.com/turovnd/realtime-data-workbench) · [API documentation](https://realtime-api.b2p.space/docs)

The current work is a **verified local checkpoint awaiting owner review** for routed pages, interactive real AI analysis and a generated API client. It has not been published. Verification and the published revision are recorded separately in [delivery status](docs/delivery-status.md). Problem grouping, roadmap planning and team collaboration are future product work.

## Run locally

Use Node 24, pnpm 11.20.0 and the root lockfile:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

The unconfigured development server at `http://127.0.0.1:5174` is an isolated browser preview. For real AI analysis, use the connected API/worker/PostgreSQL stack at `http://127.0.0.1:8082`, or start development with `VITE_API_URL=http://127.0.0.1:8002 pnpm dev`. See [setup](docs/setup.md#live-analysis) for the bounded OpenRouter configuration. A browser-only preview never impersonates a real AI response.

## Project map

- `frontend/`: React application and `frontend/tests/`.
- `backend/`: FastAPI, durable processing and `backend/tests/`.
- [Documentation](docs/README.md): current setup, API, architecture, testing and operational limits.
- [MVP plan](docs/planning/README.md): implemented foundation, current UI review and planned product capabilities.

Built independently with AI assistance and synthetic data. No private client implementation, customer dataset or production performance claim is included. Connected AI analysis uses the explicitly enabled server-side provider and a durable attempt budget. Deterministic fixtures remain separate for browser previews and automated tests.
