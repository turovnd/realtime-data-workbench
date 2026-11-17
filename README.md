# Feedback Desk

Customer feedback often mixes a useful request with background details, workarounds and frustration. Reading a long message is easy; consistently capturing its main issue without losing the customer’s meaning takes more care.

Feedback Desk turns a message into a short AI summary, a topic, an intent and supporting quotes. The original stays beside the result so a reviewer can check the interpretation. Every analysis run is saved, including failures and repeated attempts.

**[Try the demo](https://turovnd-feedback-desk.vercel.app)** · [API docs](https://turovnd-feedback-desk.vercel.app/docs) · [Architecture](docs/architecture.md) · [Verification and release](docs/delivery-status.md)

## Try one complete scenario

1. Choose **Try the demo**. No account is required; sample feedback belongs to an isolated workspace.
2. Choose **Try an example** in the inbox. Review or edit the longer customer message about a monthly export that fails while smaller exports still work.
3. Submit the message for analysis. Follow the actual queued and analyzing states until a result or an actionable error appears.
4. Compare the AI summary with the original and its supporting quotes. Check that the failed monthly export, working smaller exports and customer impact have not been confused.
5. Run **Analyze again**, then open **Activity** to inspect the saved runs and their results.

Opening the demo does not call a model: seeded results are labelled as samples. Submitting a message or explicitly analyzing an existing one invokes OpenRouter. The result identifies its model. Provider failures remain visible; a failed live request never becomes a sample response.

## What the MVP does

- Add feedback, filter the inbox and page through results with opaque cursors.
- Review AI summaries, classification and exact source quotes beside the original text.
- Analyze again or process a fixed selection without overwriting previous results.
- Inspect progress, failures and saved results in Activity.
- Use a temporary demo workspace or sign in to a personal, isolated workspace.

This is a focused review tool. It does not automatically decide product priorities or manage a roadmap or team. Example messages are synthetic; there is no connected customer inbox.

## Engineering choices

| Choice                                                        | Why                                                                                    | Tradeoff                                                                                 |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| PostgreSQL records and durable jobs, delivered through Queues | Feedback and its job commit together; repeated delivery preserves saved results.       | A thirty-minute schedule repairs missed publication after commit.                        |
| Private Python subscribers with leases and completion fencing | Model calls run outside the HTTP request; stale workers cannot overwrite results.      | At-least-once delivery can repeat an interrupted, already-billed model call.             |
| Structured output plus exact source quotes                    | Reject malformed results and quotes absent from the original.                          | Quotes do not prove correct interpretation; human review remains necessary.              |
| Immutable messages and saved runs                             | A new result cannot erase the source or an earlier interpretation.                     | History grows; list and detail responses have explicit bounds.                           |
| Polling and cursor views                                      | Ordinary HTTP supports progress updates and stable review pages.                       | Updates are periodic, and new arrivals require a refreshed list.                         |
| Vercel Services and Neon Free                                 | One Git revision deploys UI, FastAPI and subscribers without an always-running worker. | Cold starts add latency. Resources have costs or quotas; schema changes remain explicit. |

The API and subscribers run in `iad1` beside Neon. Processing has bounded concurrency, three attempts per job and durable provider counters. Scheduled redispatch can take roughly thirty-one minutes with healthy infrastructure; this is not a completion guarantee or a throughput benchmark. See [architecture](docs/architecture.md), [deployment](docs/vercel.md) and [operational limits](docs/limits.md).

## Run locally

Requires Node 24, pnpm 11.20.0 and Docker Compose v2. Preserve an existing `.env`; otherwise copy `.env.example` and set a unique database password.

```sh
cp -n .env.example .env
docker compose --profile local-web up --build -d --wait
```

Open `http://127.0.0.1:8082`. Local Docker uses a polling worker and needs no Vercel credentials. Fresh installs disable live model calls. Configure a server-side key and explicit enablement through [setup](docs/setup.md#live-analysis) to use real AI. Existing databases without Alembic require the documented [adoption procedure](docs/setup.md#existing-unversioned-database); never delete a volume to make an upgrade succeed.

For frontend-only work, `pnpm install --frozen-lockfile` and `pnpm dev` start the labelled browser fixture.

## Implementation and evidence

`frontend/` contains React; `backend/` contains FastAPI, typed SQLAlchemy models, Alembic and processing logic. Each has mirrored tests. The client is generated from OpenAPI. Git `main` deploys both hosted services; Alembic changes remain explicit.

The published application passed 255 backend tests on disposable PostgreSQL and 62 frontend unit tests. A real OpenRouter analysis completed through the public UI, was saved in Neon and appeared with the same result in Activity. [Delivery status](docs/delivery-status.md) records the exact verification scope and remaining review items. The [AI evaluation](docs/ai-evaluation.md) is a small synthetic regression sample, not a representative accuracy benchmark.

[Project documentation](docs/README.md) · [MVP epics, stories and tasks](docs/planning/README.md)

Built independently with AI assistance and synthetic data. No private client code or customer data is included.
