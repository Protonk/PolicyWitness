# Query-order setup boundary

The ordinary producer/reader difference is an evidence limit. A separate,
constructed actor reply exposed a host reporting-validation gap: an apply-mode
actor could retain `setup_status: unapplied_declared`. Rust and Python already
reject that declaration. The correction adds the same narrow Swift check;
it changes no scheduler, collection barrier, eligibility rule or wire field.

## Boundary traced

This investigation began with source inspection at `ffc56117`, before reading
earlier audit conclusions. The relevant contract owners are
[step order](../../docs/contract/31-steps.surface.md), the
[applied publication](../../docs/contract/30-reply.surface.md), and
[actor reader scope](../../docs/contract/33-actor_evidence.surface.md).

| Boundary | Observation and rule |
| --- | --- |
| Native application | `pw_probe_runner.c` writes `apply_rc`, publishes an operation-8 native failure and exits on nonzero, then publishes `applied` only on zero. The ordinary driver additionally requires `applyRCIsZero` before collection. |
| Ordinary construction | `buildOrdering` and `buildStepResults` require `applied && applyRC == 0`. Release or acknowledgement without that prerequisite adds `release_without_successful_application`. A nonempty violation list prevents `query_first`. |
| Actor construction | `ActorScheduler.setupDisposition` requires the applied setup publication, observed application and zero status for applied actors. Unapplied actors establish their declared setup without application. The assembler supplies that declaration to ordering construction. A late applied publication after setup timeout is retained without restoring setup eligibility. |
| Carried reply | Ordinary `sandboxed_after_apply` carries the acquired publication. `applyRC` and `applyErrno` are not serialized. A published worker failure may separately carry a failed native apply result. Actor records carry mode, setup status, application publication/count, assessment, launch and subprocess observations. |
| Readers | Swift reporting and Rust admission check a claimed `query_first` using the carried setup, worker PID, native query/unique record association, and ordering chain. Python also requires `query_first` when its carried-evidence oracle finds complete eligibility. Separate actor checks reject inconsistent mode, application, launch or ownership records within their respective domains. |

The native prediction must be validator-sourced, with equal reported/native
return, an errno observation, and either allow/zero or deny/one/zero-errno.
Exactly one retained record must match step, operation, filter, outcome and
native values. Collection closure, release, acknowledgement, lifetime and no
protocol violation are independently required. None establishes identical
query/attempt state or prediction/enforcement agreement.

Implementation trace: [construction](../../runner/Sources/PWRunnerCore/CWorkerComparison.swift),
[step assembly](../../runner/Sources/PWRunnerCore/CWorkerStepResults.swift),
[eligibility](../../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift),
[host validation](../../runner/Sources/PWRunnerCore/PWRunnerReply.swift),
[Rust admission](../../controller/src/porcelain_admission.rs),
[actor identity](../../controller/src/porcelain_actor.rs), and
[Python consumer](../../tests/lib/consumer.py).

## Discriminating cases and decision

The existing [reader corpus](../../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift)
retains typed frames before judging them. Added controls distinguish:

| Constructed case | Required interpretation |
| --- | --- |
| Successful ordinary application and complete native-query chain | `query_first`; admitted. |
| `applied=true`, internal `applyRC=-1`, complete release observations | Production builders retain the application flag, add the violation, and report `unestablished`; admitted as a marked conflict. This combination is not a valid native success path. |
| Same output with comparison forced to `query_first` | Rejected because the carried violation remains. |
| Same altered reply with the violation erased too | Accepted: the internal status cannot be recovered from the remaining structured record. The diagnostic summary does not substitute for a native status field. This is deliberately altered data, not producer output. |
| Valid applied actor, only setup status changed to `unapplied_declared` | Ordinary reporting must reject the inconsistent declaration. |
| Actual host reporting of that malformed actor | Rich degradation retains the declaration, removes all comparisons, and admits the degraded form. |

Existing valid applied/unapplied actor and late-setup controls remain in the
same suite. The corpus gives the extension subreader a separate expectation
for the identity-only mismatch: general actor identity validation owns that
refusal. Host, Rust and general Python rejection expectations remain strict.

Removing only the ordinary violation while leaving `unestablished` would
separate Python's stronger production oracle from Swift/Rust's one-way claim
check. That intentional distinction needs no runtime correction. The actor
case instead crossed the complete host path: equipment, authority, application,
count, phase and step checks did not compare the two carried declarations.
The narrow correction rejects `mode == apply && setup_status == unapplied_declared`
before ordinary reporting. Degraded reporting continues to retain conflicts.

## Evidence and acceptance

Regression source: clean commit `8eeae6c7`. Canonical selection:
`runner_unit/pwrunner_core_unit_executable`, output
`tests/out/runs/astra-order-boundary-red`, run `20261113T211124Z_36071ee0`.
The run account
records zero system sleep, an unchanged inspected app, and 604/605 Swift tests
passing. The sole failure was host acceptance of `actor-apply-declares-unapplied`
despite its rejection expectation. The retained
Swift manifest
also records `reporting_failure_observed: false` for the actual host reporting
path. Ordinary cases behaved as predicted. The wrapper stopped at that Swift
failure; this red run supplies no new Rust/Python replay credit.

These development observations establish
constructed host interpretation, not a native scheduler producing malformed
setup. Source inspection establishes the other boundary statements above.

The corrected signed build is number `1408`, source `5adff9ae`, with worker
identity `55c17ee8ca9c57360610525b026c8d8039be78b8798259c41726408ba5ac7b28`.
`make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`
completed signing and verification. It refreshed the staged guide. No
notarization or publication was performed. The public snapshot and shape
goldens did not change; the new support owner remains `check_read`.

The coordinated selection ran from clean `5adff9ae`:

```sh
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  PW_TEST_OUT_DIR=tests/out/runs/astra-order-boundary-acceptance PW_TEST_QUIET=1 \
  tests/run.sh --suite source_drift --suite failure_boundaries \
    --suite runner_unit --suite runner_abi_layout \
    --suite runner_c_worker_harness --suite unit \
    --case witness_contract/comparison_matrix
```

Run `20261113T211601Z_9debc827` completed all 96 selected cases: 92 passed and
four failed, with zero recorded system sleep. Its four `suite_exit` harness
entries correspond to those case failures. The inspected app stayed unchanged.

| Failure | Finding and disposition |
| --- | --- |
| `runner_unit/pwrunner_core_unit_executable` | Swift passed 605/605 and Rust matched all new expectations. Python rejected three new ordinary positive controls because their constructed worker omitted polling-stop and collection-basis observations. The actual producer always supplies these. Commit `59d2709d` completes the fixture with `done` and `after_confirmed_reap`; it changes no reader expectation or runtime source. |
| `runner_unit/host_setup_oracle_sensitivity` | The partial-unmap variant spawned a child but retained no child receipt. Its 100 ms ready, 200 ms sentinel and 200 ms grace allowances expired; the host recorded SIGKILL and reap. That observation does not identify why the child receipt was missing. An unchanged-case retry passed. |
| `runner_c_worker_harness/native_pause` | This opt-in experiment failed to qualify the standalone `nanosleep` candidate under the deny configurations. It does not exercise a production wait or the reporting correction. The failure remains a failed qualification; no retry or acceptance credit is assigned. |
| `runner_c_worker_harness/arm_wait` | This separate opt-in instruction trial refused without its coordinator gate. No instruction trial ran, and no credit is assigned. The reporting change introduces neither candidate wait primitive. |

The focused follow-up ran from clean `59d2709d`, using the same signed app:

```sh
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  PW_TEST_OUT_DIR=tests/out/runs/astra-order-boundary-followup PW_TEST_QUIET=1 \
  tests/run.sh --case runner_unit/pwrunner_core_unit_executable \
    --case runner_unit/host_setup_oracle_sensitivity
```

Run `20261113T213143Z_38c7d166` passed both cases with no skips, unrun cases,
harness errors or recorded system sleep. Swift passed 605/605. The complete
reader replay passed 149 typed frames and seven JSON-only controls. Its six
new rows distinguish retained order conflicts, a deliberately erased conflict,
the rejected actor declaration and actual rich degradation; independent binary
projection agrees. The malformed ordinary actor is rejected by Swift, Rust and
general Python. The degraded reply retains its declaration and withholds all
comparisons. The extension subreader retains its narrower identity scope.

The other 92 results are retained as a reviewed applicability judgment: the only
subsequent executable-input delta is two fields in the constructed
`ReaderCorpusTests` helper, rerun in full above. The unchanged host-setup recipe
copies production sources and its own fixture, not that helper. Neither runtime
sources, other case inputs nor the inspected app changed. Later record-only
edits receive generator and whitespace checks, not additional behavioral credit.
The two experimental wait screens remain failed/refused; this is not an
all-green 96-case run.

The correction does not change the worker wait, release store or query
eligibility rule, so the ordering mutation control is not required. No native
occurrence of the malformed actor setup is claimed. Development run artifacts
are disposable under normal retention; the committed controls preserve the
reproduction, and the run identities above preserve the outcome account.
All three development runs were reviewed and removed with `make prune APPLY=1`;
their raw artifacts are no longer available. The four release archives and
protected acceptance were preserved. The initial sandboxed pruning preview's
signature diagnostic did not recur outside the automation sandbox.

## Concrete lead left outside this correction

The documented resolver branches
`lifecycle.worker.resolve_stop_reason.missing` and
`lifecycle.worker.resolve_collection_basis.missing` produce
`reason: not_recorded`. The corresponding paths in
`tests/fixtures/contract/response_shape.json` omit `reason`, so the generic
Python shape reader rejects these constructed fallback forms. The live
`ActorSession.collectOutput` always supplies both observations; the other
production initializer supplies only a classifier fallback and is not serialized.
This is a demonstrated documented-fallback/shape-coverage discrepancy, without
demonstrated native reachability. Completing the intended ordinary fixture does
not settle that separate coverage question.
