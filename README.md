# Feedback Desk

Customer feedback often mixes a useful request with background details, workarounds and frustration. Reading a long message is easy; consistently capturing its main issue without losing the customer’s meaning takes more care.

Feedback Desk turns a message into a short AI summary, a topic, an intent and supporting quotes. The original stays beside the result so a reviewer can check the interpretation. Every analysis run is saved, including failures and repeated attempts.

**[Try the demo](https://turovnd-feedback-desk.vercel.app)** · [API docs](https://realtime-api.b2p.space/docs) · [Architecture](docs/architecture.md) · [Verification and release](docs/delivery-status.md)

## Try one complete scenario

1. Choose **Try the demo**. No account is required; sample feedback belongs to an isolated workspace.
2. Choose **Try an example** in the inbox. Review or edit the longer customer message about a monthly export that fails while smaller exports still work.
3. Submit the message for analysis. Follow the actual queued and analyzing states until a result or an actionable error appears.
4. Compare the AI summary with the original and its supporting quotes. Check that the failed monthly export, working smaller exports and customer impact have not been confused.
5. Run **Analyze again**, then open **Activity** to inspect the saved runs and their results.

Opening the demo does not call a model: seeded results are labelled as samples. Submitting a message to the live-configured API or explicitly analyzing an existing one invokes OpenRouter. The result identifies its model. Provider failures remain visible; a failed live request never becomes a sample response.

## What the MVP does

- Add feedback, filter the inbox and page through results with opaque cursors.
- Review AI summaries, classification and exact source quotes beside the original text.
- Analyze again or process a fixed selection without overwriting previous results.
- Inspect progress, failures and saved results in Activity.
- Use a temporary demo workspace or sign in to a personal, isolated workspace.

This is a focused review tool. It does not automatically decide product priorities or manage a roadmap or team. Example messages are synthetic; there is no connected customer inbox.

## Engineering choices

| Choice                                          | Why                                                                                                           | Tradeoff                                                                                      |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| PostgreSQL stores both records and durable jobs | A message and its work commit together. Claims, retries and accepted results have one transactional boundary. | A bounded, deliberately serialized demo; no high-throughput claim or separate broker.         |
| Separate API and worker                         | Model latency does not hold an HTTP request open. Work survives a worker restart.                             | A worker must be operated and monitored alongside the API.                                    |
| Structured output plus exact source quotes      | Reject malformed results and quotes that are absent from the original.                                        | Provenance is checkable; classification and interpretation still need human review.           |
| Immutable messages and saved analysis runs      | A new model result cannot erase what the customer said or what an earlier run produced.                       | More stored history; list and detail responses need explicit bounds.                          |
| Polling and stable cursor views                 | Progress updates work with ordinary HTTP; new messages do not reshuffle a page while it is being reviewed.    | Progress is not instantaneous, and new arrivals require a refreshed list.                     |
| Vercel UI with a Docker backend                 | Static frontend delivery is independent of Python workers and persistent PostgreSQL storage.                  | UI and backend releases must be coordinated; a Git UI deployment does not deploy the backend. |

The worker owns retries and uses leases with completion fencing to reject stale results. An interrupted external call can still have been billed: the system does not promise exactly-once model calls. Model, timeout and token limits are server-side settings. See [architecture](docs/architecture.md), [workflows](docs/workflows.md) and [operational limits](docs/limits.md).

## Run locally

Requires Node 24, pnpm 11.20.0 and Docker Compose v2. Preserve an existing `.env`; otherwise copy `.env.example` and set a unique database password.

```sh
cp -n .env.example .env
docker compose --profile local-web up --build -d --wait
```

Open `http://127.0.0.1:8082`. Fresh installs start with live model calls disabled. To use real AI, configure the server-side OpenRouter key and explicit enablement described in [setup](docs/setup.md#live-analysis). Existing databases without Alembic require the documented [adoption procedure](docs/setup.md#existing-unversioned-database); never delete a volume to make an upgrade succeed.

For frontend-only work, `pnpm install --frozen-lockfile` followed by `pnpm dev` starts the labelled browser preview. It does not simulate a successful live AI request.

## Implementation and evidence

`frontend/` contains the React UI and mirrored tests. `backend/` contains the FastAPI application, typed SQLAlchemy models, Alembic migrations, worker and mirrored tests. The frontend client is generated from the actual OpenAPI schema.

Tests cover workspace isolation, cursor boundaries, concurrent claims, stale-worker completion, retries, migration preservation and browser journeys. A [small real-model evaluation](docs/ai-evaluation.md) checks the demonstration scenarios separately from deterministic regression tests. It is a review sample, not a production accuracy or business-impact benchmark. See [testing](docs/testing.md) and [delivery status](docs/delivery-status.md) for the exact evidence and published revision.

[Project documentation](docs/README.md) · [MVP epics, stories and tasks](docs/planning/README.md)

Built independently with AI assistance and synthetic data. No private client code or customer data is included.
