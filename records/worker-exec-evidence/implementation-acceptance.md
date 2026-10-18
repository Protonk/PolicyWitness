# Exec evidence implementation acceptance

Status: implemented, reviewed and accepted. All 192 default cases have passing
credit across the full run and selection-check repair; the required additional
controls passed. This record belongs to the
[implementation plan](../../controller/tools/pw_probe_runner/EXEC-EVIDENCE-REFACTOR-PLAN.md).

## Implemented boundary and review

Completed, successfully spawned exec attempts now carry optional
`attempt.exec_observation`, with separate collection, termination-request and
leader-reap sections. Collection is frozen before cleanup. Signal returns record
requests, not exit or group absence. Only the owned leader's wait return supports
its status. Missing/null metadata remains unknown. Unpublished slots, pre-spawn
failures, synthetic results and non-exec results supply none of the object.

The coordinator reviewed the sub-agent's C producer, shared layout, Swift decoder
and mapper, Rust/Python validation, controls and documentation. Review preserved
native call order and branch/error precedence, legacy aggregate outcomes,
positive-child spawn comparison precedence and the existing completion gate.
It also tightened present-data checks for positive native errno and impossible
waitid-error/previously-observed-exit combinations, and corrected all readers to
accept the native signed-short range for poll revents while enforcing the actual
error-branch flags. No wait, signal, clock sample, retry, process or resource was
added to the production execution path. Release/order eligibility is unchanged.

The fixed payload consumes 112 reserved bytes at the end of each slot. Existing
field offsets, 8,192-byte slot size, region size and output capacities remain
unchanged. Compiled C/Swift layout agreement and the reviewed layout golden pass.
Request/response/envelope versions remain 5/23/7; absence stays compatible with
older current-format replies. The response-shape change adds only the optional
object's paths and types. The independently bounded optional-field allowance is
688 bytes per slot, or 176,128 bytes for 256 slots; the verified maximum reply is
52,595,368 bytes, below the unchanged 159,383,552-byte transport ceiling.

## Source and signed candidate

The implementation starts from `5034d254a9817b65afa5262399eed7c95234ff17`.
[final-build-source.json](final-build-source.json) records the signed candidate's
changed files. [acceptance-source.json](acceptance-source.json) records the full
battery's source, including test-only changes after that build.
[acceptance-repair-source.json](acceptance-repair-source.json) records the sole
subsequent test-input delta: the opt-in alias in `tests/catalog.json`. Unchanged
files come from the base commit. The committed implementation supplies the
snapshotted contents; later plan statuses, records and retention entries are
acceptance bookkeeping, not additional runtime changes.

The final signed build completed successfully:

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

The [build transcript](implementation-build.log) is a copy with trailing
whitespace trimmed; the earlier build and its snapshot are retained separately
as [pre-repair-build.log](pre-repair-build.log) and [build-source.json](build-source.json).
The final build produced `dist/PolicyWitness.app`, its ZIP and standalone guide.
Verification covered eight executables and two seals with Developer ID,
hardened runtime and secure timestamps. The regenerated worker identity is
`4a0d8ebf41f767dd07869a93082735442b750266b61acac8e0d1e624f6feeeb2`.

No app input changed after the final build. Before full acceptance, only the
exec-reader test's independent absence oracle, the response-shape golden and
fixture README changed, plus trailing whitespace in the native checker. After
full acceptance, only the catalog alias changed. App inventories are identical
before and after the full run, additional controls and reader mutations.
These are development acceptance results, not a notarized release acceptance.

## Executions and corrections

Commands ran from the repository root outside the automation sandbox, through
the checkout-locked dispatcher. Each run retains canonical case IDs, exact
commands/configuration, equipment, raw output and complete accounting. Linked
raw evidence is gitignored, available only in this checkout and pinned in the
retention index. [retained-runs.json](retained-runs.json) lists all 12 executions,
including development failures and unrun cases.

```sh
PW_TEST_OUT_DIR=tests/out/runs/exec-evidence-default-20261018 tests/run.sh
PW_TEST_OUT_DIR=tests/out/runs/exec-evidence-extra-20261018 tests/run.sh \
  --case dispatcher/selection_controls \
  --case runner_exec_lifecycle/closed_streams_leader_exit \
  --case witness_contract/max_exec_steps_spawn
PW_TEST_OUT_DIR=tests/out/runs/exec-evidence-swift-readers-20261018 tests/run.sh \
  --case runner_unit/pwrunner_core_unit_executable \
  --case runner_unit/exec_reader_mutations
PW_TEST_OUT_DIR=tests/out/runs/exec-evidence-owning-suites-20261018 tests/run.sh \
  --case runner_unit/reaped_ack_mutation \
  --case runner_unit/host_setup_oracle_sensitivity \
  --case runner_c_worker_harness/native_clock
```

The [full default run](../../tests/out/runs/exec-evidence-default-20261018/run.json),
`20261018T202431Z_b7bfe1f3`, completed all 192 cases: 191 passed, one failed, none
skipped or unrun. The failure was `dispatcher/selection_controls`: the new
non-default `runner_unit/exec_reader_mutations` case was missing from the
aggregate `opt_in.include` list. Adding that membership repaired the selection
contract without changing a case definition or test implementation. The original
failure and associated suite-exit diagnostic remain intact.

The [repair and live-control run](../../tests/out/runs/exec-evidence-extra-20261018/run.json),
`20261018T204257Z_26f62044`, passed all three cases, with no skips, unrun cases or
harness errors. The full run's Swift executable passed 461/461 tests; actual
production-driver and worker-clock replies also passed Rust and independent
Python replays. Source-drift, ABI, reader/failure-boundary, native worker, exec
lifecycle, extension and ordering coverage passed in the full battery.

The [reader-mutation execution](../../tests/out/runs/exec-evidence-swift-readers-20261018/run.json),
`20261018T202202Z_966fed0c`, passed the mutation case. Its separate full Swift
case initially failed only the expected response-shape change. After reviewing
and adopting that candidate, the dedicated shape-review run passed 461/461;
the later full default run repeated that pass. Mutation credit is unaffected
by the shape golden, as explained below. The maximum-exec case is already in
the default battery and was also run explicitly as the plan requested; it is
not counted as another distinct opt-in.

The [owning-suite completion run](../../tests/out/runs/exec-evidence-owning-suites-20261018/run.json)
passed the three remaining opt-in members of `runner_unit` and
`runner_c_worker_harness`, as required by runner guidance for a new Swift test
file. The retained full-suite selection contains 51 cases; every one has passing
credit across these executions. The host setup sensitivity case characterizes
known checker limitations and makes no product-safety claim. There are 197 unique
credited cases overall, including all 192 default cases.

Earlier development failures are retained: sandboxed signature preflight left
the first native run unrun; unsandboxed compilation exposed a fixture signed/
unsigned comparison; the initial ABI run exposed the intended stale golden;
a new Rust test indexed an empty fixture; and the Swift run exposed the intended
shape delta. Those fixture/golden issues were repaired and superseded by passing
executions. The final implementation is not credited from the initial failures.

[implementation-case-credits.json](implementation-case-credits.json) names the
passing run and source snapshot for every default case and additional control.
Replacement credit does not rewrite the failed historical run.

## Applicability of retained results

The default selection JSON is byte-equivalent as parsed before and after the
catalog repair, including case order, commands, prerequisites, dependencies and
containing suites. Both selections are retained in the full run's supplement.
Source hashes show no other test-input delta from the full-run snapshot.

Reusing those 191 passes is a reviewed applicability exception for the catalog
alias. The coordinator traced `test_cli.py`: default selection reads each case's
default flag; aggregate inclusion affects only selecting that suite. The repaired
selection control directly exercises the changed path and was rerun. Other
dispatcher controls use authored fixture catalogs. Source-manifest checks read
suite keys/default flags and owning case IDs, and generator citation lookups use
owning `cases[].id`; none changed. Wrapper controls observe arguments through
stubs. Production sources, live-case scripts, shared helpers, fixtures and signed
app bytes are unchanged. No application rebuild was required for this alias.

Reader-mutation applicability was checked against its retained copied package:
54 source/fixture files and the package manifest match the final tree; its
intentionally replaced main invokes only the exec-observation tests. The script
copies only `exec_observation.json`, not `response_shape.json`. Neither the shape
update nor aggregate alias membership affects that exact-case invocation.
The case-credit file retains the verified copied-source hashes. These hash and
selection comparisons establish identity; path/dependency conclusions above
come from source review, not hashes alone.

## Discriminating evidence

The production-source native control matches 58 independent pre-refactor call
ledgers, including ordered native arguments, returns, meaningful errno/status
and clock values, with incidental descriptors normalized by role. The
[baseline supplement](../../tests/out/runs/exec-evidence-default-20261018/supplemental/native-policy-baseline/)
preserves the original source, headers, fixture, executable, commands and output;
its adjacent copy receipt records byte equality and the original temporary path.
The six [producer mutation rejections](../../tests/out/runs/exec-evidence-default-20261018/suites/runner_c_worker_harness/exec_control_states/artifacts/rejected-mutations.json)
fail their designated unchanged assertions: collection overwritten by final
reap, ESRCH turned into success, group result substituted for fallback, pending
wait treated as reap, and revents or local grace expiry fabricated as errno.
Native calls are substituted in these controls; they establish recording and
call policy, not real process termination effects.

The shared reader corpus exercises 19 valid and 44 malformed combinations in
Swift, Rust and independent Python. Valid controls include successful signalling
without reap, collection failure with clean leader status, and local clock faults
coexisting with actual waits. The [reader mutation results](../../tests/out/runs/exec-evidence-swift-readers-20261018/suites/runner_unit/exec_reader_mutations/artifacts/controls/results.json)
retain a passing baseline and designated failures for bypassing slot completion
and inventing no-cleanup evidence from absent metadata. The publication fixture
constructs an ABI payload and dies before publication; it establishes decoder
gating, not a real spawned child's result. Separate production C-to-Swift and
CLI tests establish actual transport, status, output and deadline observations.

The ordinary-survivor live control independently observes the same-group child
after later work and worker exit, alongside `cleanup.state: not_requested`.
The worker-death control independently observes survivors while withholding
unpublished exec evidence and preserving earlier results/later-effect absence.
Both final fixture receipts confirm helper and worker exits, no retained cleanup
obligation and removed staging:
[ordinary survivor cleanup](../../tests/out/runs/exec-evidence-extra-20261018/suites/runner_exec_lifecycle/closed_streams_leader_exit/artifacts/cleanup.json),
[worker-death cleanup](../../tests/out/runs/exec-evidence-default-20261018/suites/runner_exec_lifecycle/worker_dies_during_exec/artifacts/cleanup.json).
These fixture cleanup facts are not inserted into product completion evidence.

Final generated-document, changed-document link, source-delta and retention
checks are retained in [implementation-final-checks.log](implementation-final-checks.log).

## Residual lifetime limits

Ordinary leader exit plus both EOFs still requests no termination. Same-group
descendants may survive later steps and worker exit; worker death may interrupt
cleanup; descendants can leave the group. The new object describes worker
observations and requests without a descendant-containment or group-absence
claim. Descriptor lifetime, sysctl, configuration and broader supervision remain
separate work. No supervisor or stronger cleanup policy was selected here.
