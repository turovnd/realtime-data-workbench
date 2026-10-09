# Feedback Desk · realtime-data-workbench

Inspect incoming synthetic product feedback, review structured results and exact source quotes, then reprocess a fixed selection without losing earlier versions.

**[Open the UI](https://turovnd-feedback-desk.vercel.app)** · [Swagger API](https://realtime-api.b2p.space/docs) · [Source](https://github.com/turovnd/realtime-data-workbench)

Pushes to `main` automatically deploy the UI to Vercel; the first Git-triggered production build is verified. The independent FastAPI API, durable worker and PostgreSQL run in this app’s own Docker project. Public UI authentication, API/data access and complete deterministic backend workflows passed verification. GitHub CI passed for the verified source revision; see [delivery status](docs/delivery-status.md) for exact release and check evidence.

## Run locally

Requires Docker Compose v2. Preserve an existing `.env`; otherwise copy the example and replace its placeholder database password.

```sh
cp -n .env.example .env
# Set a unique URL-safe POSTGRES_PASSWORD in .env.
docker compose --profile local-web up --build -d --wait
```

Open `http://127.0.0.1:8082` and choose **Try an isolated demo**. This stack has its own network, credentials and persistent volume. It does not require the other portfolio repository.

## Documentation

- [Project documentation](docs/README.md): architecture, setup, API/Swagger, auth, workflows, testing, operations and limits.
- [Delivery plan](planning/README.md): separate epic/story index and one detailed file per task.
- [Current verification and deployment status](docs/delivery-status.md): evidence and remaining work.
- [Contribution rules](AGENTS.md): repository boundaries and delivery authority.

Runtime modules are separated and tests mirror their paths under one `tests/` directory. The complete local regression gate passed. See [setup](docs/setup.md), [testing](docs/testing.md) and [delivery status](docs/delivery-status.md) for commands and hosted release status.

## Provenance and scope

Built independently with AI assistance and synthetic data. No private client implementation, real customer dataset, invented commit history or production performance claim is included. The UI uses the official shadcn Nova / Neutral / Blue / chartBlue / Inter / Lucide preset. Deterministic generation is the default; optional live provider calls require explicit server-side enablement and durable budgets.

The browser-only fixture is explicitly labelled and is separate from the connected server mode.
