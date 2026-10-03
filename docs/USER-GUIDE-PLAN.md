# User guide correction plan

Correct the validated caller ambiguities in the current guide while preserving
the accepted-input lesson and the app's behavior. This plan is detailed enough
to implement independently of the
[SBPL helper sketch](../controller/SBPL-CHECK-PLAN.md). If the helper has not
changed, document its current behavior; do not describe the proposed redesign
as implemented.

The starting evidence is [the user report](../pw-user-guide-report.md), source
inspection, twelve native review cases and a passing 377-test runner batch.
The report concerns 0.2.4; several of its questions are already answered by the
current contract. Its historical policy-run populations were not independently
replayed. The findings and source owners below are sufficient to perform this
work without the local review artifacts.

## Scope and ownership

Primary edits belong in [PolicyWitness.md](PolicyWitness.md),
[limits.json](limits.json), and [REQUEST-GRAMMAR.md](REQUEST-GRAMMAR.md).
[LIMITS.md](LIMITS.md) and the guide's copied limits are generated outputs.

Include two small source-comment corrections:

- The exec-field encoding comment in
  [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift).
- The comment above `pathFilterIsUnresolvable` in
  [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift).

Those files participate in the exact worker source identity, even for comment
edits. Regenerating it also changes the generated regions in
`controller/tools/pw_probe_runner/pw_probe_runner_abi.h`,
`runner/Sources/PWRunnerCore/CWorker.swift`, and `tests/lib/contract.py`.
These mechanical updates are part of the comment corrections. No runtime logic,
request/response schema number, budget, public flag or new evidence field is
needed for this plan.

Keep generated sections under their existing owners:

| Content | Edit owner |
| --- | --- |
| Limits and their guide copy | `docs/limits.json`, then `docs/generate_limits.py` |
| Copied questions | `docs/QUESTIONS.md`, then the same generator; no question rewrite is presently needed |
| Copied comparison reading rules | `tests/FAILURE-PROPAGATION-CONTRACT.md`; leave these conditional rules intact for this work |
| Contract numbers | `docs/contract.json`; no number change is planned |
| Worker source identity | `docs/generate_worker_identity.py`; never hand-edit the generated values |

## Findings to address

| Report question | Current assessment | Planned treatment |
| --- | --- | --- |
| Specimen version | Resolved by current admission and teaching examples | Verify consistency; preserve the lesson. |
| Missing parameters and compiler diagnostics | Contradictory guide and misleading helper output remain | Correct the current-behavior account; defer helper behavior to its sketch. |
| Validator exit and signal fields | Exactly-one rule is too broad | Replace with confirmed versus unconfirmed disposition rules. |
| Empty exec streams | Guide already corrected | Preserve guide text and fix the stale encoder comment. |
| Missing path and later diagnostics | Null guarantee is false | Delete the guarantee and explain the two observation times. |
| RPC versus sentinel timeout | Wrong token and incomplete field mapping | Correct the limits source and add a compact mapping in the guide. |
| Unsupported and incomplete attempts | Unsupported public inputs are now refused; source mapping still needs clarity | State the public source rule and keep defensive construction detail in developer guidance. |

## Implementation sequence

### Establish the current baseline

Read repository instructions, the relevant guide sections and the linked source
owners before editing. Compare the helper to its sketch's reproduction results;
if intervening implementation work changed them, document the new verified
behavior instead of restoring the old account.

Inspect the diff before starting and preserve unrelated work. Treat this as a
documentation change: edit the claims below, without changing the runtime to
match a preferred explanation. Write current rules in the finished guide, not
review history or references to the 0.2.4 report.

### Correct the SBPL helper account

Edit **SBPL check (`sbpl-check`)** and its cross-reference in
**normalized_outcome catalog**. Ground the wording in
[sbpl-check.rs](../controller/src/bin/sbpl-check.rs), particularly the early
refusals, `compile_sbpl`, and final outcome selection. Check the immediate
reader in [policy_check.rs](../controller/src/policy_check.rs).

As the implementation stands:

- Format, missing-source and source-size refusals happen before compilation.
  Their current outcomes are `unsupported_format`, `bad_policy`, and
  `policy_too_large`, respectively.
- A nonempty literal missing-name list does not prevent the compile attempt.
  Input conversion or parameter setup can still fail before the compiler call.
- After that attempt, nonempty `params_missing` wins the summary and exit code:
  `missing_params`, exit 1, even if `compiled` is true. Otherwise successful
  compilation yields `ok`; failure yields `compile_error`.
- `compile_error` currently carries both native compiler diagnostics and helper
  validation/setup errors. Its presence alone does not establish a compiler
  invocation. Native failure text in the path-filter reproduction is one
  observed case, not a promise that every missing name causes that failure.
- `params_scan_complete` describes the literal scanner's limitations when it
  runs. Early refusal currently supplies empty scan lists and a true flag;
  readers must not infer a performed scan from that flag alone.

Replace the “both gate before libsandbox” claim and the incorrect compiler
rejection token. Use a short distinction between compiler result, literal scan
and helper summary, with the unused-definition example from the helper sketch
if needed. Avoid expanding the guide into an exhaustive account of every setup
failure. Preserve the existing explanation that fallback compilation is an
independent host observation, invoked only after `xpc_error`.

### Repair validator and exec field rules

In **Top-level fields**, replace the `validator_subprocess` paragraph with a
small table and link to the existing **Receiver evidence** discussion:

| Observed validator disposition | Current status fields |
| --- | --- |
| Confirmed normal termination | `exit_code` present, including nonzero codes; no `term_signal` |
| Confirmed signal termination | `term_signal` present; no `exit_code` |
| Final status unconfirmed | Neither status field supplies a value; the current encoder omits both |

Explain that readers tolerate absent or null optional values, `reaped` records
confirmation, and termination requests and wait errors are independent evidence.
Any observed terminating signal can be recorded; a signal number alone does
not identify its sender. Delete “clean exit” as a synonym for every exit code,
“SIGKILL fallback” as the signal field's definition, and the exhaustive
“null in two cases” claim. An absent subprocess object does not by itself
establish why validator observation is missing.

Sources are [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift),
`PWRunnerValidatorSubprocess` in the API, and
[ValidatorEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift).
Existing controls cover exit 0, exit 23, SIGTERM, SIGKILL, failed cleanup and
unconfirmed waits; the latter are controlled failures, not spontaneous production
observations.

Keep the corrected exec text in **Shape and schema_version** and the attempt
table: a completed exec slot supplies the three child fields; streams are
included only when they produced bytes. Update the API encoder comment to say
the same. The missing-executable review case returned `exec_failed` with
`child_pid: 0`, `child_exit_code: -1`, `child_term_signal: 0`, and no stream keys.
Do not change the encoder or introduce empty stream placeholders.

### Correct the path timing explanation

In **Per-step shape**, under `prediction_unavailable`, remove the unconditional
`path_diagnostics.realpath_resolved` null “second tell.” Identify the existing
`sandbox_check.error` and `query_plan:path_unresolved_at_planning` limitation as
the planning evidence. Do not make that limitation a required field in degraded
replies where the entire comparison was unavailable.

Cross-link **path_diagnostics**, which already says the host observes the path
after orchestration. Add a brief counterexample using the existing accepted
file-create exercise: the query can be excluded for an absent target, creation
can succeed, and the later resolution can succeed. When the resolved bytes equal
the input, `same_as_input` lists `realpath_resolved` and that key is omitted.
Otherwise the diagnostic may carry a different resolved string. The outcome
and the later path form describe different times.

Replace the broad claim about all absent file paths failing with ENOENT before
sandbox checking with the actual planner rule: PW excludes path queries whose
targets the host cannot resolve at planning time. Update the matching comment
above `pathFilterIsUnresolvable`; leave its predicate and the planner unchanged.
Retain the existing compact path representation and its role in log correlation.
No earlier-snapshot field is necessary to correct this prose.

Sources are `planValidatorQueries` in the orchestrator and
`enrichPathDiagnostics` in
[PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift).
The copied comparison reading rule about post-run resolution already has the
correct temporal scope and needs no edit.

### Map timeout layers to exact output fields

Change only the explanatory `effect` of `client_rpc_wait` in `limits.json`:
RPC expiry yields `xpc_timeout`, not `runner_timeout`. Preserve its value,
counting, controls and the independent worker/validator budgets. Regenerate
the tables after completing the prose edits.

In **normalized_outcome catalog**, add a small mapping near the client-generated
outcomes. The following table specifies the intended content for ordinary
successfully captured client output:

| Event | `result.normalized_outcome` | `data.runner_result.normalized_outcome` | Result origin and distinguishing evidence |
| --- | --- | --- | --- |
| Client RPC wait expires | `xpc_timeout` | `xpc_timeout` | Client synthesizes a present result with empty steps; no host subprocess report. Client exit code is 1. |
| Host sentinel budget expires and its reply arrives | `runner_timeout` | `runner_timeout` | Host result includes `runner_subprocess.poll_stop_reason: "sentinel_deadline"` and available disposition evidence. Client exit code is 0 because it delivered the reply. |

The client exit code here is `data.runner_client.exit_code`, not the exit code
of `policy-witness`; the controller failed both review runs. RPC expiry says
the client received no reply before its deadline. It does not prove the host
never ran, was unreachable, or crashed, and does not establish cancellation of
host work.

Explain absence separately: if client stdout supplies no parsed reply,
`data.runner_result` is null and the controller can report
`runner_output_not_json`; launch or request-delivery failures are `tool_error`
paths. Keep those distinct from the normal synthesized RPC-timeout result and
from a retained but refused malformed/unsupported response.

Replace the catalog's blanket “peer itself can't be reached” explanation and
its promise that the host always replies. In **Caller authentication and ad-hoc
signing**, change “never answered” to “no reply received before the deadline”
and keep any suggested cause explicitly tentative. In **Running specimens in
parallel**, make deadline wording allow RPC expiry as well as host expiry;
avoid assigning every resource delay the `runner_timeout` token.

Source owners are the timeout branch of
[PWRunnerClient/main.swift](../runner/Clients/PWRunnerClient/main.swift),
`runner_outcome` and `complete_execution` in
[run_flow.rs](../controller/src/run_flow.rs), and the runner-client capture path.
Do not turn internal test overrides into user-facing timeout controls.

### Clarify attempt provenance and place defensive detail

In **Top-level fields** and **Per-step shape**, give the direct source mapping:
completed supported worker slots use `attempt.result_source: "worker"`,
including completed failed operations; absent or incomplete publications use
`"synthetic"` with a missing reason. `not_run_worker_died` means no completed
result, not proof that the operation never started. Keep the lifecycle evidence
for that separate question. The source assignment is in
`buildStepResults` in the orchestrator.

Keep the public admission rule prominent: unsupported attempt combinations
refuse the whole specimen before children. In **What the implementation
promises** in `REQUEST-GRAMMAR.md`, extend the existing short defensive-handling
paragraph to state that internal unsupported construction uses `synthetic`
with `attempt_not_supported`, even if handed a completed slot. Link the
implementation and
[ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift)
as appropriate.

Move explanation of that internal construction into the developer paragraph;
leave only a short conditional definition/link where the user guide lists
defensive output vocabulary. Preserve exact conditional meanings in copied
comparison rules and token lists. Do not revive permissive unsupported input
examples or conflate them with the validator's `unsupported_operation` query
result. Keep `result_source`, which distinguishes real observations from missing
results and is used by consumers. Keep the attempt channel free of the already
removed, always-null `native_rc` field.

Finally, verify that **Top-level shape**, the accepted-request exercise and
**Correcting a refused request** agree with the current request contract. Those
sections already resolve the version question; they need no second tutorial.

## Validation and completion

Run generation from the repository root after the planned edits:

```sh
python3 docs/generate_limits.py
python3 docs/generate_worker_identity.py
```

The first command updates owned generated sections; inspect its diff, including
any file outside `docs/`. The second is required for the two source comments and
should change only the three generated identity regions listed above. Do not
regenerate contract numbers or rebuild the distributed app for this prose work.

Then run the existing checks, choosing an unused managed output name:

```sh
python3 docs/generate_limits.py --check
python3 docs/generate_contract.py --check
python3 docs/generate_worker_identity.py --check
PW_TEST_OUT_DIR=tests/out/runs/user-guide-followup-01 tests/run.sh --suite source_drift
git diff --check
```

The source-drift suite covers generated copies, documentation links, source
conventions and identity generation without requiring an app build. New tests
that merely search for preferred sentences are unnecessary. Repeat native
experiments only if an intervening behavior change or an unresolved assertion
requires fresh evidence; the helper sketch supplies its reproducible cases,
and the existing accepted-create exercise supplies the path case. Follow
[runner/AGENTS.md](../runner/AGENTS.md) before using fault controls again.

Review the finished diff against these completion criteria:

- A reader can distinguish scan findings, helper summary and compiler result
  without being promised behavior from the future helper redesign.
- Validator field presence is conditioned on observed status; exec stream
  absence is described consistently in prose and the encoder comment.
- Planning-time path failure makes no promise about later resolution.
- The timeout mapping identifies both envelope levels, result origin and the
  separate meaning of an unavailable runner result.
- Attempt provenance is explicit; unsupported-input admission and defensive
  construction are not presented as the same public workflow.
- Generated sections agree with their owners, all checks pass, and edits outside
  `docs/` are limited to the two comments and generated worker identity regions.

Keep this work reviewable as a documentation change separate from any future
helper implementation. Existing builds and retained run evidence remain intact.
