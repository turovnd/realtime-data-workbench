# Product overview

A reviewer needs to understand a customer message quickly without losing the distinction between a reported problem, its impact and a requested improvement. Feedback Desk presents the original alongside a concise AI summary, a topic, an intent and exact supporting quotes.

## First review flow

1. Choose **Try the demo** to open an isolated workspace. Seeded messages and their sample results let the reviewer browse immediately without invoking a model.
2. Choose **Try an example** in the inbox. The editable message describes a monthly CSV export failure, working weekly exports, a manual workaround and the customer’s request.
3. Submit it for analysis. The live-configured API saves the message and its job together; a separate worker calls the model. The detail page shows actual pending, running, failed or completed state.
4. Read the summary against the original. Check the supporting quotes and the model provenance. Exact source text supports review; it does not guarantee the interpretation is correct.
5. Choose **Analyze again**, then open Activity to inspect the saved results from each run. Earlier successful results remain available when a new run fails.

## Workspace and navigation

`/login` and `/register` handle entry. `/feedback` contains the inbox, search, filters and cursor pagination. `/feedback/:id` opens the original and analysis. `/activity` shows automatic, individual and grouped runs with their messages, saved results and errors. Status refreshes through polling.

The demo is temporary and uses synthetic data. Personal accounts have isolated workspaces. External customer-channel ingestion, Problems, Roadmap and Team are outside this MVP. A labelled browser-only preview supports UI development; it never substitutes for an unavailable connected API or live model.

See the [MVP plan](planning/README.md) for epics, stories and tasks, and [delivery status](delivery-status.md) for the verified source and published runtime.
