# Workflows and consistency

## Ingest and enrich

A bounded simulation creates server-authored synthetic inputs. Input identity is unique per workspace: identical retries are idempotent; changed text under the same identity conflicts. Input and initial job commit together. Original text is immutable.

A separate worker claims one of at most two globally admitted leases, runs deterministic enrichment or the explicitly configured provider outside the transaction, validates structured output and exact evidence substrings, then conditionally writes an immutable result for `(record, configuration)`. Failed/invalid output remains visible; no silent deterministic fallback occurs.

Jobs have queued/leased/succeeded/failed/cancelled states. Leases last 30 seconds; the provider deadline is 10 seconds; the lifetime attempt budget is three. A stale or cancelled lease cannot commit. Crash recovery resumes from persisted jobs. The same provider call can be attempted again after uncertainty, so exactly-once external execution or charges are not guaranteed.

## Versioned backfill

Select up to 100 records across pages/filters. Starting a backfill freezes those IDs and atomically enqueues the bounded selection. v1/v2 are fixed processing configurations; an existing `(record, configuration)` is not overwritten when the default provider changes. Progress comes from persisted per-job state, not an in-memory counter.

Cancel unfinished work without deleting completed results. Retry only an eligible failed job and keep its original provider/configuration and lifetime attempt budget. Inspect both versions and unchanged source text after completion.

## Stable browsing and offline read-only state

A feed view freezes matching IDs while records arrive and statuses change. Each cursor page hydrates only requested rows. Three-second polling updates status/results; **Show new feedback** / **Refresh view** opens a current membership snapshot. Selection is a set of IDs, independent of the rendered page and filters, and must remain bounded.

Explicit offline save records currently loaded synthetic data with snapshot age. Offline mutation is disabled. The service worker caches shell/assets only; API requests bypass it. Session changes clear private query data and offline copies. The browser fixture is labelled, makes no API/model calls and resets on reload; it is not proof of server durability.

See [API](api.md), [authentication](auth-tenancy.md) and [testing](testing.md).
