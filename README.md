# Feedback Desk

Customer messages mix problems, requests, workarounds and background details. Before a product review, someone has to read them, identify what matters and preserve enough context to avoid a misleading conclusion.

Feedback Desk turns a long message into a short takeaway, a topic and an intent, backed by quotes from the original. A reviewer can compare both side by side and inspect previous analyses.

**[Try the demo](https://turovnd-feedback-desk.vercel.app)** · [Swagger](https://turovnd-feedback-desk.vercel.app/docs) · [Architecture](docs/architecture.md)

## See the difference

1. Choose **Try the demo** to open your own workspace with 24 detailed customer messages.
2. Open a message. Compare the original with its prepared sample takeaway: what happened, who is affected and what workaround they use.
3. Choose **Analyze with AI** to analyze that message through OpenRouter, or use **Try an example** to edit and submit your own.
4. Check the summary against the supporting quotes. **Activity** preserves the result and status of every run.

For example, a customer describes a failed monthly export, working weekly exports and manual merging. The useful takeaway is that **monthly exports fail, the workaround costs 30 minutes, and Monday’s finance report is at risk**. The summary is shorter; the original and quotes let the reviewer check it.

Prepared examples are labelled **Sample analysis**. Opening a demo makes no model calls. New submissions and explicit AI analysis use OpenRouter; provider failures remain visible and never become sample results.

## Scope

- Add and search feedback; filter by topic or processing status.
- Browse with cursor pagination, including Activity and grouped run details.
- Run AI analysis, follow progress and retry a failed or completed analysis without losing earlier results.
- Use a temporary demo or an account with an isolated workspace.

The MVP supports feedback review. It does not ingest a real customer inbox, decide priorities, or manage a roadmap or team.

## Engineering choices

- **PostgreSQL owns durable work.** The message and job commit together. Queues deliver job IDs; leases and completion fences prevent stale workers from replacing saved results.
- **Evidence is checked.** Structured output is validated, and every quote must occur in the source. That catches unsupported quotes, but interpretation still needs human review.
- **History is retained.** Reanalysis creates a new run. Retrying an uncertain submission with the same identity does not create a duplicate run.
- **Polling keeps the MVP simple.** Updates are periodic. Saved cursor views keep new arrivals from shifting a list while someone is reviewing it.

External model calls can repeat after an interrupted attempt; exactly-once billing is not guaranteed. Missed queue publication is repaired by a scheduled scan, so this recovery path can take roughly 30 minutes. See [architecture](docs/architecture.md) and [AI evaluation](docs/ai-evaluation.md).

## Run locally

Requires Node 24, pnpm 11.20.0 and Docker Compose. Preserve an existing `.env`; otherwise copy `.env.example` and set a database password.

```sh
cp -n .env.example .env
docker compose --profile local-web up --build -d --wait
```

Open `http://127.0.0.1:8082`. Local live analysis is disabled until an OpenRouter key and enablement are configured; see [setup](docs/setup.md).

`frontend/` owns the React application and its tools. Backend entrypoints are `modules/api` and `modules/worker`; `common` holds shared ORM models, schemas and logic. Alembic owns migrations. The repository root contains shared workspace, Compose and deployment configuration.

[Documentation](docs/README.md) · [MVP plan](docs/planning/README.md) · [Tests](docs/testing.md)
