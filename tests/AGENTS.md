# Working in `tests/`

Read [README.md](README.md) for the harness, commands, configuration, coverage
map and output contracts. These instructions govern test work alongside the
[root guidance](../AGENTS.md), including test changes outside this directory.

## Find the relevant contract

- Start with the owning [suite README](README.md#suite-coverage), the
  [fixture catalog](fixtures/README.md) and [outcome coverage](COVERAGE.md).
- For runner tests, the C worker or `_test_overrides`, also read
  [runner/AGENTS.md](../runner/AGENTS.md).
- For evidence assertions, use the
  [comparison ownership table](FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
  and the [wire contract](../docs/CONTRACT.md).
- For resource-sensitive or mutation controls, consult the
  [opt-in registry](OPT_IN_TESTS.md).
- For release acceptance and interrupted release cleanup, follow the
  [release procedure](../docs/SIGNING.md#release-procedure).

## Choose and run verification

Use `tests/run.sh` from the repository root for selection, prerequisite checks,
artifact inspection and complete result accounting. Inspect a selection with
`--list`; `--all --list` shows the complete catalog. A suite selector includes
its opt-in members. Case scripts refuse to start outside the dispatcher;
`--case SUITE/ID` runs one case, and `make test` is the default battery against
the distribution app.

The default battery needs a signed app. Build through the
[signed pipeline](../docs/BUILD.md) when the selected app is absent or stale;
offline selections need only their listed equipment. Do not modify the inspected
app or regenerate its evidence to conceal changed bytes. Build fixtures and
mutated app copies outside it.

Use a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` for separate evidence.
Keep Python assertions enabled, including direct helper invocations; unset
`PYTHONOPTIMIZE`. Missing required equipment is a failure with unrun cases,
not grounds for introducing a skip.

Host and worker allowances count system sleep. The dispatcher blocks idle sleep
while it runs and records in `run.json` how long the system slept during each
case; Swift unit tests print the same for each test. A failure that overlapped
sleep is not product evidence, and crediting the case needs a run that did not
overlap sleep.

### Choose the most integrated test that can establish the behavior

Use the public CLI or an existing `_test_overrides` boundary when the behavior
is reachable there. Use runner unit tests for internal helper branches or
observations an ordinary specimen cannot reliably produce. Keep behavior
requiring XPC, launchd or the kernel sandbox in the corresponding live suites.
Constructed inputs establish interpretation separately from live observations.

Select checks for the changed boundary and its readers. For admission or
validator receiver changes, run `failure_boundaries` with `runner_unit`,
`runner_abi_layout`, `runner_c_worker_harness` and `unit`; retain the applicable
`runner_validator_failure` and `witness_contract` assertions.

Rerun `witness_contract/order_barrier_mutations` whenever the worker wait,
release store or query eligibility rule changes. Follow the opt-in registry's
other change-specific controls. When comparing native builds, run the live
battery against the candidate, including worker and ordering cases; structural
comparison alone cannot establish behavioral equivalence.

### Verify a limit change

For a limit change, run `tests/run.sh --suite unit --suite integration
--suite source_drift --suite runner_abi_layout --suite runner_unit
--suite runner_c_worker_harness --suite failure_boundaries` against a normal
signed build, plus the affected behavior owners in the
[limits coverage table](../docs/LIMITS.md#grounding-and-coverage).

New entries need an implementation-value check and an honest coverage note;
a link to source is not enough. Do not label a shortened timeout control as a
test of the production duration, or a constant comparison as proof of its
operational consequences. Keep behavioral oracles independent of the limits
manifest so changing a documented number cannot change their expectations.

### Sandboxed automation harnesses

Use [the contained probe helper](lib/shim_probe.py) for any by-hand probe of
`SDKROOT` or `DEVELOPER_DIR`. Start the helper with those
variables absent and pass the tested values through `--env`, for example:

    env -u SDKROOT -u DEVELOPER_DIR tests/lib/python.sh -I tests/lib/shim_probe.py \
      --fixture /private/tmp/pw-sdk-probe-new --env SDKROOT=/missing.sdk -- /usr/bin/git --version

Use a fresh fixture. The helper refuses unless its containment checks pass;
it records raw checks, command output and detected installation requests.
Its prepare mode returns a command prefix only after checking the profile;
keep that profile unchanged until the caller's final use.

Inspect diagnostics before attributing a test failure to the product or its
execution environment. Use an unsandboxed shell for cases requiring `app` or
`worker`. If the automation sandbox refuses an operation, request escalation
and rerun the same failing command once outside it without changing the
artifact under investigation. A passing retry can support an environmental
explanation; it does not retroactively supply missing observations.

`runner_unit` executes embedded children directly without XPC. Cases without an
app requirement can still need escalation: cancellation and process-observation
controls use local sockets and exit events, and
`source_drift/build_documentation` exercises Meson's Swift compiler discovery.
The [equipment reference](README.md#equipment-checks) explains what the
dispatcher can establish before execution. Follow
[runner diagnostics](../runner/AGENTS.md#sandboxed-automation-harnesses) for XPC
or log failures and [build guidance](../docs/BUILD.md#sandboxed-automation-harnesses)
for compiler discovery, signing or signature verification.

## Add or change tests

Register each case in [catalog.json](catalog.json), with its actual prerequisites,
default membership, dependencies and any supported skip reason. A case is
reached only through `tests/run.sh`: a wrapper script no case names, a
documented direct command or a release-specific selection fails the drift suite. Keep the
[suite map](README.md#suite-coverage), owning suite README, applicable outcome
coverage and opt-in registry aligned. Put detailed assertions and fixture
descriptions beside their suite rather than duplicating them in the map.

Use the [shared test infrastructure](README.md#shared-test-infrastructure) for
setup, command capture and structural validation. Keep case-specific policies,
expected outcomes, independent observations and cleanup ownership in the case.
Retain raw inputs, output and diagnostics; distinguish a harness deadline or
equipment failure from a PolicyWitness result.

Put build intermediates in `PW_TEST_SCRATCH` and retain sources, logs and
receipts in `artifacts/`; reconciliation detects SwiftPM's default `.build`
location, while this rule covers other build state too.

Preserve independent file/process observations and separate assertions for
prediction and attempt evidence. A successful return code alone does not prove
an effect, and a permission-shaped failure alone does not establish a sandbox
cause. Keep consumers independent of specimen policy interpretation and the
production classifier.

Exercise checker changes with independent passing and rejected controls.
Combined faults must remain visible; reordering steps must add only the order
diagnostic without losing actual failures or inventing others. Declare supported
skips narrowly and validate the remaining evidence before taking them.

Default cases must not generate or download replacement fixtures. Follow
fixture-owned build and refresh procedures when deliberately updating inputs.

## Evaluate and reuse evidence

For each credited case, record its canonical ID, command/configuration, source
snapshot and applicable build or equipment. Trace the command's scripts, shared
helpers and fixtures conservatively, then compare their file snapshots with the
accepted implementation. A case not requiring the app can still depend on changed
test code; app independence alone does not justify reusing its result.

Rerun a case when a dependency changed or applicability is uncertain. If an
earlier result is retained despite a changed file, identify the exact delta,
explain why the executed path and inputs are unaffected, and label this as a
reviewed exception. Hash checks establish file identity; they do not establish
complete dependency coverage or prove program reachability. An allowlist of
changed files is likewise a review aid, not proof that every retained case is
unaffected. Acceptance summaries must distinguish mechanically checked facts
from these applicability judgments.

Keep original runs and snapshots intact. Record corrections and replacement
credits explicitly, including the reason for each rerun; do not turn an earlier
failure into a passing historical run.

## Preserve and clean up output

Follow the [retention and locking contract](README.md#retention-ownership-and-execution-locking).
Never unlink `tests/.checkout.lock`: replacing its inode bypasses an existing
holder. Builds hold it too, so wait for the current build or execution or use
a second worktree for concurrent runs; a standalone `cargo test` against the
managed `controller/target/` runs through `tests/lib/checkout_lock.sh` or with
isolated output and intermediate directories, as the
[locking contract](README.md#retention-ownership-and-execution-locking) says.
Such a command, like a standalone `swift run PWRunnerCoreTests`, is local
debugging of the crate or package under its own tool's rules; it is not a run
of the `unit`, `integration` or `runner_unit` case and establishes nothing
about the battery.
A worktree is also the way to make a disposable checkout; an rsync copy that
omits `dist/README.md`, `dist/AGENTS.md` or `.tmp/AGENTS.md` fails the build
and the drift suite.
Inspect interrupted or ambiguous output before choosing a fresh directory
or explicitly removing an owned unfinished run through the pruner.

For a console transcript, capture to a temporary file outside `tests/out/runs/`
and attach it to the completed run under the checkout lock after verifying the
run ID. Do not create or redirect into the selected output directory before
startup: a preexisting transcript makes fresh output unmanaged, and replacement
of an eligible old run would unlink an already-open transcript. If execution
never creates owned output, keep the temporary transcript for diagnosis.

Use `make prune` to preview and `make prune APPLY=1` to apply ordinary cleanup.
The [pruning reference](README.md#pruning-disposable-output) describes eligible
output and the explicit `--unfinished` command. Do not bypass the helpers to
remove protected evidence or resource-cleanup records. Record source provenance
only when established; the commit adding a retention entry is not the source
of an earlier build. Preserve established release tags on indexed release runs
so their checkpoint cleanup remains possible.

Preserve `tests/out/.release-rotation/` after interrupted release cleanup.
Resume the same archive's `release_rotate.py --apply` transaction through the
[recovery procedure](../docs/SIGNING.md#portable-test-evidence-and-release-cleanup).
For external runners, retain staging and durable ownership until removal is
verified, following the [external-runner workflow](../AGENTS.md#external-runner-workflow).
Scratch follows [.tmp/AGENTS.md](../.tmp/AGENTS.md); never move evidence there
to evade retention.
