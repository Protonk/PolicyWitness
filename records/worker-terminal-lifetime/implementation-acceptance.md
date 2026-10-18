# Terminal exit implementation acceptance

Status: implemented, reviewed and accepted. All 192 default cases have passing
credit across the default run and repaired-case rerun; both selected opt-in
mutation controls passed. This record belongs to the
[implementation plan](../../controller/tools/pw_probe_runner/TERMINAL-EXIT-REFACTOR-PLAN.md).

## Implemented boundary

The production C worker erases the full accepted token buffer before its existing
terminal `done` release-store, then calls `_exit(0)`. Ordinary early returns and
pre-acknowledgement cancellation erase accepted storage while preserving their
exit codes and publication rules. Consumption and pre-intervention erasure remain
in place. Erasure does not release native extension authority.

The host reconciles acknowledgement after confirmed reap, before the final
snapshot and collection basis. This uses the existing ownership/release/ack
predicate for both clean and abnormal exits. It cannot repair lost ownership,
invent release, withdraw previously established phase credit, or turn a deadline
into timely completion. Raw native query observations remain available when
phase order is unestablished. The existing reader predicate and wire/layout
versions are unchanged.

The coordinator reviewed the sub-agent's production changes, deterministic
fixtures, rejection assertions and documentation. Review also corrected two
harness timing observations: elapsed values require an actual applied sample,
and a late-release delay is reported from that sample rather than the requested
delay. The absent-release case's description now matches its actual fixture; it
does not claim to have killed an XPC host.

## Source and signed candidate

The implementation starts from `b4e6ccf0010d4019c6665cf2e7681a7962853a79`.
[acceptance-source.json](acceptance-source.json) records SHA-256 hashes of every
changed or new non-record file at default acceptance; unchanged files come from
that base. [acceptance-repair-source.json](acceptance-repair-source.json) records
the subsequent test-only repairs and explicitly lists their delta. The committed
implementation supplies those file contents. Later plan statuses, this receipt,
case credits and retention entries are acceptance bookkeeping.

The signed build completed successfully with:

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

The [build transcript](implementation-build.log) retains the invocation's output
with one trailing space on a compiler progress line removed.
It produced `dist/PolicyWitness.app`, its ZIP and the standalone guide. Signing
verification covered eight executables and two seals with Developer ID,
hardened runtime and secure timestamps. The regenerated worker identity is
`4dd8d75126025defa7b9719fb434d265b69f25b9d3bd6d9fd3836d1321f02976`.
No app input changed after this build. Harness timing corrections were included
before default testing; subsequent changes affect test oracles and messages.

## Executions and corrections

Commands ran from the repository root outside the automation sandbox. The
dispatcher records effective configuration, equipment, each canonical case ID,
command and complete result accounting in each run. Raw run directories linked
below are gitignored and available only in this checkout; the retention index
pins them. They are not a notarized release acceptance.

```sh
PW_TEST_OUT_DIR=tests/out/runs/terminal-exit-default-20261018 tests/run.sh
PW_TEST_OUT_DIR=tests/out/runs/terminal-exit-repairs-20261018 tests/run.sh \
  --case source_drift/limits_documentation \
  --case dispatcher/selection_controls \
  --case runner_unit/pwrunner_core_unit_executable \
  --case runner_c_worker_harness/bare_deny_default \
  --case runner_c_worker_harness/compile_failure \
  --case runner_unit/reaped_ack_mutation \
  --case witness_contract/order_barrier_mutations
```

The [default run](../../tests/out/runs/terminal-exit-default-20261018/run.json),
`20261018T183220Z_040bf851`, completed all 192 selected cases: 189 passed, three
failed, none skipped or unrun. Its inspected app was valid and unchanged. The
failed result remains intact. Its three failures prompted these reviewed repairs:

| Case | Failure and correction |
| --- | --- |
| `source_drift/limits_documentation` | Two stale-copy mutations searched for an obsolete reading-rule prefix and made no change. Use the current prefix and explicitly require each mutation to change its input. |
| `dispatcher/selection_controls` | The opt-in assertion confused requested membership with expanded selection. A default dependency of an opt-in case already existed at the base commit. Check requested non-default membership, transitive dependency closure and selection labels separately; independently exercise one passing fixture and five rejected variants. The dispatcher itself is unchanged. |
| `runner_unit/pwrunner_core_unit_executable` | Four clock controls required raw `allow` after opening the worker-refusal gate before validator launch. Prompt worker exit produced raw `deny`. Require the actual phase-local record's outcome, native return, errno/error, operation and filter to survive with validator provenance, absent attempts and unestablished order. Do not impose a target-liveness interpretation on its raw answer. |

The [repair run](../../tests/out/runs/terminal-exit-repairs-20261018/run.json),
`20261018T184724Z_975e5373`, passed all seven selected cases with no skips,
unrun cases or harness errors. The full Swift executable passed all 458 tests;
its actual worker-clock replies also passed the Rust and independent Python
reader replays. The app was valid and unchanged, and its inventory exactly
matches the default run's inventory. The [case credits](implementation-case-credits.json)
identify the accepted passing run for every default case and the two opt-ins;
replacement credit does not change the original failed result.

The repair snapshot changes only those three test files plus assertion wording in
`tests/suites/runner_c_worker_harness/run.sh`. The latter changes failure messages
in `happy_default_allow`, `bare_deny_default`, `compile_failure` and the shared
policy-delivery control, plus a comment. It changes no predicate, fixture,
command, selection or input.

After testing, a scoped link check found an existing prose link label in the
worker-lifecycle fixture README incorrectly formatted as a source symbol.
Removing its backticks fixes that check without changing its target or meaning.
This documentation-only delta from the repair snapshot does not affect any
executed case; the final checks record its file hash separately. Other later
changes are the plan statuses and acceptance/retention bookkeeping above.

## Applicability of retained passes

The coordinator traced the affected entrypoints, shared helpers and fixtures.
The repaired Swift file is compiled by the runner-unit case, which is rerun in
full. The limits and dispatcher oracle files belong to their respective rerun
cases. Native app sources, generated worker identity, test catalog, fixtures,
shared test libraries, readers and the other suite scripts match the default
snapshot. The acknowledgement mutation copies only its dedicated lifecycle test
and TestKit alongside production sources, so it does not execute WorkerClockTests.

Reusing default worker-harness passes is a reviewed exception for the changed
shared `run.sh`: only the message/comment delta above differs from the executed
snapshot. All assertions and their inputs are identical. The two selected
harness reruns also exercise changed messages. Source-manifest checks observe
unchanged file membership; architecture/build/version checks retain their
unchanged generator inputs and tested predicates. Final generated-document
checks and a scoped link check separately check completion bookkeeping. Their
[final results](implementation-final-checks.log) are retained. Hash equality establishes
file identity; dependency and reachability judgments here come from source
review, not from hashes alone.

## Discriminating evidence

The default production-worker harness independently reaped normal completion,
an empty final phase and terminal refusal with `exit_requested` left zero and no
cleanup kill. Its pre-done stall still required and observed SIGKILL/reap. Late
release could not revive a refused phase. The integrated default battery also
exercised extension boundaries/combinations, phase ordering, compiled profiles,
failure propagation and supported readers.

The [erasure observations](../../tests/out/runs/terminal-exit-default-20261018/suites/runner_c_worker_harness/terminal_erasure/artifacts/observations.json)
cover 23 baseline scenarios. The observer holds its own mapping, scans the fixed
16,384-byte capacity, and confirms nonzero bytes beyond the token NUL before
cleanup. A shortened erase fails the independent full-capacity assertion. A
reversed erase/publication mutation observes `boundary_zero: 0` while held at
the actual done-store gate, then `final_zero: 1` after reap; it fails specifically
the pre-publication erasure assertion. Host erasure is withheld during both
observations. Native calls are substituted in this flow fixture, so its results
establish cleanup/control flow, not successful kernel extension operations.

The [acknowledgement mutation results](../../tests/out/runs/terminal-exit-repairs-20261018/suites/runner_unit/reaped_ack_mutation/artifacts/controls/results.json)
show all three baseline controls passing. The fixture publishes its previously
unseen acknowledgement only inside the native wait, after the host's last
acknowledgement/done samples. Both clean exit and fatal SIGTERM without done or
phase completion establish order with ownership intact; the latter retains its
signal and abnormal run disposition. Removing final reconciliation fails both
specific ownership-credit assertions, while the prior-ownership-loss control
still passes. This tests recovery, not retention of an earlier sampled ack.

The [ordering mutation observations](../../tests/out/runs/terminal-exit-repairs-20261018/suites/witness_contract/order_barrier_mutations/artifacts/assert.log)
retain a passing baseline with no early completion or attempt. Worker-wait and
host-release bypasses are rejected by independent observations of early effects
while collection is held. Released unlink/exec effects and ancestry are also
observed; neither a compile failure nor a generic nonzero return counts as the
mutation rejection.

## Remaining scope

Native exit itself and native calls that do not return are still not bounded by
this refactor. Cancellation and host grace/termination/reap cleanup remain.
Fatal termination does not promise ordinary worker erasure. Exec descendants
remain the separate supervision investigation; no containment or descendant
cleanup guarantee was added.
