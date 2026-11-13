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
The [run account](../../tests/out/runs/astra-order-boundary-red/run.json)
records zero system sleep, an unchanged inspected app, and 604/605 Swift tests
passing. The sole failure was host acceptance of `actor-apply-declares-unapplied`
despite its rejection expectation. The retained
[Swift manifest](../../tests/out/runs/astra-order-boundary-red/suites/runner_unit/pwrunner_core_unit_executable/artifacts/reader-corpus/swift.json)
also records `reporting_failure_observed: false` for the actual host reporting
path. Ordinary cases behaved as predicted. The wrapper stopped at that Swift
failure; this red run supplies no new Rust/Python replay credit.

These gitignored development artifacts are local and disposable under normal
retention; the committed controls preserve the reproduction. They establish
constructed host interpretation, not a native scheduler producing malformed
setup. Source inspection establishes the other boundary statements above.

Acceptance is pending the corrected signed build and one coordinated selection:
`failure_boundaries`, `runner_unit`, `runner_abi_layout`,
`runner_c_worker_harness`, `unit`, `source_drift`, and
`witness_contract/comparison_matrix`. The correction does not change the worker
wait, release store or query eligibility rule, so the ordering mutation control
is not required for this change. Final run/source identities and reader receipts
belong here after verification.
