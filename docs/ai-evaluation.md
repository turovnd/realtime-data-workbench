# AI scenario evaluation

The demonstration needs to preserve the distinction between a concrete failure, a requested change and an observation that is too vague to classify. Exact source quotes alone do not establish this distinction.

The fixed [four synthetic cases](../backend/evaluation/cases.json) were used to develop and check the prompt with OpenRouter / `openai/gpt-4.1-mini`. They are a regression sample, not a held-out accuracy benchmark. The evaluation sends the actual source text through the production prompt, transport and validator.

These saved reports evaluate OpenRouter only. They do not establish the quality or availability of the direct DeepSeek adapter. A provider change requires a separate bounded real-model report and a browser-to-worker persistence check; intercepted transport tests are not substitutes for either.

## Recorded runs

| Report                                                         | Declared-label and output checks | What it revealed                                                                                                |
| -------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| [Initial instructions](../backend/evaluation/baseline.json)    | 3 of 4 cases passed              | A vague perceived change became a usability issue.                                                              |
| [Prose decision rules](../backend/evaluation/rubric-pass.json) | 2 of 4 cases passed              | The ambiguity remained; another case drifted to usability despite describing an export failure.                 |
| [Explicit taxonomy](../backend/evaluation/latest.json)         | 4 of 4 cases passed              | The tested output distinguishes an unknown change from a concrete issue, and uses the defined topic boundaries. |

All twelve responses passed schema and exact-quote validation. Each report preserves the actual instructions, hashes, outputs, latency and available token usage. There was one request per case and no retries. Failed checks are retained. These results do not demonstrate general prompt-injection resistance, production classification accuracy or customer time saved.

## Qualitative review of the final outputs

The following review was performed with AI assistance by comparing the saved outputs to their source messages. It is separate from the automated checks and is not independent human validation.

| Case                 | Observed result                                                                                                                                                  | Remaining limitation                                                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Monthly export       | Identifies full-month export failure, distinguishes the manual weekly workaround and retains its half-hour effort without claiming Monday’s deadline was missed. | The short summary omits the request for background completion and notification; the original remains necessary for the full request. |
| Ambiguous change     | Uses `other` / `unclear` and preserves the author’s uncertainty.                                                                                                 | A single example does not establish calibration across ambiguous messages.                                                           |
| Russian billing      | Retains duplicate charging, the missing invoice and reconciliation impact in Russian without inventing responsibility.                                           | The customer’s claims are summarized, not independently verified.                                                                    |
| Embedded instruction | Describes the export failure and blocked report; the injected classification instruction is not followed or used as evidence.                                    | One test cannot establish broad adversarial robustness.                                                                              |

The prompt defines intent precedence and topic boundaries explicitly. It treats a workaround’s time cost as effort, not an invented delay, and asks the model to preserve uncertainty. There are no case-specific output substitutions or keyword-based repairs after generation.

For the bounded command and its scope, see [testing](testing.md#small-real-model-evaluation). Browser/API/worker persistence is verified separately in the [release ledger](delivery-status.md).
