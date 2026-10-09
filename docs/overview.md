# Product overview

Feedback Desk turns synthetic product feedback into inspectable topic, intent and summary results with exact source quotes. Reviewers can select records across pages, request a new fixed processing version and inspect both old and new output without mutating the original message.

A demo creates 24 synthetic records; a registered account starts empty. **Add 12 live records** creates a finite server-side synthetic batch, not a connection to a real external event stream. The separate worker processes persisted jobs. The UI polls status, preserves the current view while new records arrive, and offers explicit refresh.

The inspector shows source text, evidence, provider and version history. Backfill freezes the selected IDs, reports persisted progress and supports bounded cancellation/retry. Optional offline snapshots are read-only local copies of loaded synthetic data.

When no API origin is configured, the browser exposes a separately labelled deterministic fixture and disables account sign-in. The connected production mode uses FastAPI/PostgreSQL and never silently falls back to the fixture after API failure.

The accepted UI preset is [shadcn b1Ymqvgiu](https://ui.shadcn.com/create?preset=b1Ymqvgiu): Nova, Neutral, Blue/chartBlue, Inter and Lucide. See [workflows](workflows.md), [limits](limits.md) and [delivery status](delivery-status.md).
