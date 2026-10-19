# Product overview

Feedback Desk helps a reviewer understand incoming feedback without losing the original message. The first MVP covers a stable filtered feed, source text, structured topic/intent/summary results, exact evidence quotes and versioned reprocessing of selected records.

The implemented foundation provides isolated demo workspaces, personal accounts, durable processing, cursor pagination, retries and fixed-selection backfill. Demo inputs are synthetic; the application does not claim a connection to external customer channels. A separately labelled browser fixture supports review without API credentials and never silently replaces a failing connected API.

The current local step makes the review experience easier to navigate: actual page routes, direct record access, a compact interface and an OpenAPI-generated client. Its acceptance is local review and regression evidence, not the presence of new files. See [delivery status](delivery-status.md).

## Current local routes

`/login` and `/register` handle entry. `/feedback` contains the paginated inbox; `/feedback/:id` opens a message and its analysis; `/activity` shows batch processing, with expandable cards for the selected messages and results of each run. This iteration focuses on adding feedback, reviewing it and following reprocessing. An ORM rewrite, socket transport changes and the full problems/roadmap/team product are outside this step.

## First review flow

1. Open a demo workspace or sign in to a personal workspace.
2. Browse feedback, apply filters and load more records without unexpected list changes.
3. Open a record, run real AI analysis explicitly and compare the original text, result and supporting quotes. Sample results are labelled separately.
4. Request reprocessing for selected records, then expand its Activity card to inspect messages, statuses and saved results from that run. Earlier results remain preserved by the backend.

Full problem grouping, prioritization, roadmap items, ownership, invitations and team workflows are **planned**. Navigation placeholders do not count as completed features. See the [product plan](planning/README.md).
