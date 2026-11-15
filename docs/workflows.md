# Workflows and consistency

## Ingest and enrich

A bounded simulation creates server-authored synthetic inputs. The current local API also accepts one manually entered message per authenticated request, with bounded identity/text and a fixed channel enum. Input identity is unique per workspace: identical retries are idempotent; changed text under the same identity conflicts. Input and initial job commit together. Original text is immutable.

A separate worker claims one of at most two globally admitted leases, runs deterministic enrichment or the explicitly configured provider outside the transaction, validates structured output and exact evidence substrings, then conditionally writes an immutable result for `(record, run)`. Failed/invalid output remains visible; no silent deterministic fallback occurs.

Jobs have queued/leased/succeeded/failed/cancelled states. Leases last 30 seconds; the provider deadline is 10 seconds; the lifetime attempt budget is three. A stale or cancelled lease cannot commit. Crash recovery resumes from persisted jobs. The same provider call can be attempted again after uncertainty, so exactly-once external execution or charges are not guaranteed.

## Interactive AI analysis

Opening a demo workspace creates sample inputs and deterministic seed results. It does not trigger bulk paid analysis. An explicit analysis request on an existing record creates a new run using the selected live provider and model; it works for demo and account workspaces. The prior message and results remain intact, including their original provider identity.

A request identity is unique per record, so retrying an uncertain click returns the same run. Another deliberate click uses a new identity after the current run finishes. Only one run per record may be in flight; there is no lifetime run cap. The worker reserves one persisted live-call attempt before contacting the provider, including each retry. A finite budget is optional; local `unlimited` mode continues counting admitted attempts without rejecting them at a cumulative ceiling. Exhausted finite budgets, missing configuration, provider rejection and invalid output remain visible failures; none switch to deterministic output.

The details page presents the current result with its provider provenance. Sample analysis and real AI analysis must remain distinguishable. Activity exposes earlier runs with their exact saved results. Ordinary record responses contain the latest ten jobs and ten successful outputs independently, so later failures do not hide the last successful result. Older history remains stored.

## Fixed-selection reanalysis

Select up to 100 records across loaded pages in one filtered view. Changing filters clears the current selection. Starting a backfill freezes those IDs and atomically enqueues the bounded selection. Batch processing uses a fixed configuration and preserves accepted results. Explicit per-record analysis creates a new run; changing the default provider does not rewrite a completed result. Progress comes from persisted per-job state, not an in-memory counter.

Cancel unfinished work without deleting completed results. Retry only an eligible failed job and keep its original provider/configuration and lifetime attempt budget. The details page shows the current result and unchanged source text. Activity provides the exact historical result for each listed run, including batch results outside the record response’s recent-history window.

## Inspect an Activity run

Activity includes automatic analysis of new feedback, manual single-message analysis and grouped runs. A group appears once, without duplicate child jobs. The list refreshes every three seconds, showing Queued, Analyzing, Analyzed or Needs attention as work progresses. Expand a card by clicking its summary or using Enter/Space on its disclosure button. Group details load only when opened; individual results arrive with the Activity page. Each selected message shows its original text, this run's status, saved summary, provider label and completion time when available. Loading, missing-result, offline and retry states stay explicit. **Open feedback** navigates to the record's current detail view.

The Activity list loads ten runs per page with cursor-based infinite loading and **Load more activity**. Each view contains the latest 6,000 activities; a visible notice identifies older stored history outside that read window. This does not limit new analyses.

Group details load ten messages per page and support scrolling or **Load more messages**. A pruned or expired cursor restarts the view from its first page; transient failures can retry the affected page. Expanded unfinished runs refresh every three seconds. The displayed result belongs to the selected run; a later analysis of the same message does not replace it. This is a read-only inspection path and does not spend the AI attempt budget.

## Stable browsing and offline read-only state

A feed view freezes matching IDs while records arrive and statuses change. Each cursor page hydrates only requested rows. Three-second polling updates status/results; **Show new feedback** opens a current membership snapshot. Selection is a bounded set of IDs within the active filtered view; it survives loading more records and clears when filters or the view are reset.

Explicit offline save records currently loaded feedback with snapshot age. Offline mutation is disabled. The service worker caches shell/assets only; API requests bypass it. Session changes clear private query data and offline copies. The browser fixture is labelled, makes no API/model calls and persists within its browser session until sign-out; it is not proof of server durability.

See [API](api.md), [authentication](auth-tenancy.md) and [testing](testing.md).
