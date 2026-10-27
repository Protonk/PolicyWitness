# Investigation Plan for Subordinate pytest Integration

## Objective

Investigate the effort required to introduce pytest beneath PolicyWitness's existing test infrastructure, with the specific aim of eventually refactoring [check_build_provenance.py](check_build_provenance.py). The opportunity is to replace ordinary organizational work with familiar machinery where that improves clarity and maintenance.

Judge the proposal by whether it reduces infrastructure that requires PW-specific knowledge and makes the remaining special cases clearer. Substantial portions of the file may remain unchanged; the proportion converted is not a success criterion.

## Scope and invariants

- **Scope.** Limit proposed migration work to `check_build_provenance.py` and the integration changes necessary to run it subordinately. Preserve the dispatcher's authority over the responsibilities described below. Other test migrations and wider test-system restructuring are outside scope. Inspect surrounding code as needed; keep external comparison within the four projects below. A Python upgrade or interpreter migration is not a prerequisite.
- **Investigation only.** Do not refactor tests, add repository dependencies, change the dispatcher, or create or run pytest prototypes in any location. The current case may be run under the [execution-reference rules](#execution-reference).
- **Evidence.** Label source-derived findings separately from measured behavior, and ground claims about pytest behavior in the pinned source. Method/parameter counts and passing status are cross-checks, not proof of preservation, unconditional collection, absence of skips, `subTest` coverage, execution of individual assertions, per-method cost, or isolation behavior.
- **Unresolved questions.** For each consequential uncertainty, identify the observation or later trial that would resolve it and the work depending on that answer.
- **Trial preservation.** The later trial preserves every baseline expectation. Isolation improvements are permitted and labeled. If preserving an expectation requires reconstructing the old machinery, record blocked preservation and leave its test unmigrated. Corrections to flagged expectations follow the trial as separate labeled changes.

## Current PW boundary and comparison targets

The following observations are grounded in PW source at `95a08b7`. Recheck them against the revision used for the comparison baseline.

- [tests/run.sh](../../run.sh) enters [test_cli.py](../../lib/test_cli.py), which selects work from [catalog.json](../../catalog.json). The public case is `preflight/build_provenance_controls`; its declared equipment is `clang`, without a distribution-app requirement.
- [The preflight entry](run.sh) starts that case, calls `test_check_python`, retains `artifacts/assertions.log`, and emits the outer result. [case.sh](../../lib/case.sh) captures both streams and refuses a nonzero checker exit before the success event. The checker currently ends in `unittest.main(verbosity=2)`.
- [python_start.sh](../../lib/python_start.sh) resolves and checks the Homebrew `python@3.14` interpreter and rejects most inherited `PYTHON*` variables. `test_check_python` starts that interpreter with `-B -S`. The checker sets `PYTHON = sys.executable`, imports production helpers in-process, and launches subprocesses. Introducing a pytest host environment can therefore change tested inputs unless those boundaries are kept explicit.
- The dispatcher owns case selection, prerequisites, checkout locking, outer accounting, interruption, and evidence retention. [suite_run.py](../../lib/suite_run.py) is the execution boundary. [Dispatcher controls](../dispatcher/check.py) already exercise the public command with constructed failures, retain streams and exit receipts, inspect summaries/journals, and check that an ordinary failure does not suppress a later passing case. [Cancellation controls](../dispatcher/check_cancellation.py) separately observe signal delivery and descendant exit.

Candidate targets within `check_build_provenance.py`:

| Target | Candidate organization | Behavior or uncertainty to preserve |
| --- | --- | --- |
| `RecordTests.test_records_are_validated_by_shape_in_every_reader` | Named independent faults applied to fresh copies of an accepted record. | Each fault reaches both the shape checker and bundle reader. Retain accepted neighbours and the separate metadata/signature cases; expectations must remain independent of the production validator. |
| `RecordTests.test_records_are_bounded_redacted_and_complete` | Isolated mutable input per fault, with authored expected diagnostic codes. | The current loop restores the record after assertions inside `subTest`; a failure can skip restoration and affect the next variant. This is an inspected risk, not a reproduced failure. |
| `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` and `StampFixture` | A prepared checkout plus a visible stateful sequence. | Preserve publication, unchanged reuse, refusal without rewriting bytes, and extension of only permitted fields. Independent malformed-stamp inputs may separate; lifecycle transitions should stay understandable. |
| `own`, lock/process controls, and environment-preservation checks | Fixtures may prepare resources while specialized observations remain explicit. | Lock handoff, descendant lifetime, raw environment comparisons, and deadlines are subjects of the checks, not incidental runner machinery. |

`RecordTests.setUp` compiles a native fixture host once per current test method. Parametrization may multiply that cost. Investigate whether immutable preparation can be shared separately from mutable bundles; the external examples do not establish the safe sharing boundary or runtime benefit for PW.

## Four patterns to evaluate

The external findings are source-derived from the revisions pinned below, inspected on 2026-10-26. No external tests or PW migration prototypes were executed. Consult the linked implementations, supporting fixtures, and invocation paths when a transfer question needs more detail.

### Zephyr: outer authority and prepared resources

At `d1d74eba22d6565eaead5840d2352b74fb4039ff`, Twister's pytest adapter selects roots, writes YAML context, invokes pytest, retains a command/output log, and translates JUnit results into outer statuses. Tool errors and report-parsing failures have explicit paths; empty/all-skipped results can become skips. The transferable pattern is explicit translation under outer-runner authority. It does not establish a need for JUnit, a PW plugin, or Zephyr's skip policy.
[Adapter and report handling](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/scripts/pylib/twister/twisterlib/harness.py#L571-L835).

The MCUboot multiple-key test obtains a prepared build through `unlaunched_dut`, optionally re-signs to a separate image, launches QEMU itself, and checks an independently supplied key ID and boot banner. The fixture supplies configuration and log/resource lifetime; the action remains visible in the test. Local command, deadline, and process helpers remain necessary.
[Test and helpers](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/tests/boot/mcuboot_multiple_keys/pytest/test_multiple_keys.py#L47-L163),
[fixture lifetimes](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/scripts/pylib/pytest-twister-harness/src/twister_harness/fixtures.py#L24-L97).

For PW, evaluate prepared checkout/bundle fixtures that leave publication, mutation, and observation explicit. Device adapters and configurable device lifetimes solve additional Zephyr requirements and need not transfer.

### meson-python: visible build sequences

At `70d921dcb4cc28e80e2b1620e5eb7b0886e48b51`, `test_editable_verbose` observes a quiet import, touches compiled source, observes rebuild output, then observes a quiet import. Other tests introduce invalid C or a Meson error and check diagnostics, restoring source/import hooks in `finally`. This supports keeping coherent PW publish/reuse/refuse/extend sequences together while parametrizing genuinely independent variants.
[Editable tests](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/tests/test_editable.py#L316-L402).

Its package fixtures change into shared source directories rather than copying them; editable wheels are session-scoped, virtual environments are per test, and autouse fixtures alter environment variables. These choices introduce restoration and coupling costs. Ordinary `finally` cleanup does not establish recovery after forced termination, and global environment cleanup may change PW's subject of observation.
[Fixtures](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/tests/conftest.py#L98-L199).

CI installs dependencies and invokes pytest directly. This example supplies test organization, not another subordinate-dispatch architecture.
[Invocation](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/.github/workflows/tests.yml#L154-L160).

### PyPA build: independent malformed inputs

At `4d37ed7edbf629c30500950e1164d21628eb697c`, `test_metadata_path_ambiguous_dist_info` parametrizes zero/two metadata directories. A substituted backend hook writes actual wheel ZIP bytes; the real reader must reject them with an authored expectation. An adjacent valid-wheel case checks accepted metadata. Malformed configuration and path cases similarly keep inputs, labels, and expected errors together.
[Wheel cases](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tests/test_projectbuilder.py#L665-L714),
[configuration/path cases](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tests/test_projectbuilder.py#L768-L836).

This is a useful model for PW's record faults: construct the artifact at a controlled boundary, preserve accepted neighbours, and exercise the real readers with independent expected answers. Fixture names do not establish isolation: this project copies some package inputs but shares others, removes temporary directories, and changes environment/caches. Tox invokes pytest with coverage and parallel workers; collection hooks implement project-specific selection. PW already has selection, locking, and retention owners.
[Fixtures and hooks](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tests/conftest.py#L30-L173),
[invocation](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tox.toml#L14-L37).

### pytest: synthetic suites that verify execution and reporting

At `41d12cdbb4a35a7877768d93d8dc50a9117a8d8c`, pytest's runner tests create tiny programs with known outcomes. They check failing setup/teardown phases, a failing exit after a passing body and failing teardown, empty/deselected versus passing selections, and both a test failure and teardown error under `--maxfail=1`.
[Phase controls](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py#L251-L324),
[selection control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py#L766-L785),
[combined-failure control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py#L1232-L1254).

The project loads `pytester` explicitly and disables third-party plugin autoloading for nested runs. Some controls call the protocol in-process; others can use subprocess mode. Supporting tests check changed PIDs and refusal to parse missing outcome summaries.
[Plugin configuration](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/pyproject.toml#L422-L429),
[fixture override](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/conftest.py#L160-L163),
[subprocess control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_pytester.py#L419-L441),
[missing-summary control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_pytester.py#L298-L307).

Borrow the synthetic-scenario technique to test the eventual PW invocation and retained evidence. Internal protocol checks do not exercise the outer launcher. `pytester` changes working directory/home variables and injects `PYTHONPATH`; its outcome assertions parse terminal summaries. Repeated subprocess runs overwrite capture files, and timeout handling kills the direct child without a process-group cleanup operation. Those policies do not substitute for PW's environment, retention, or cancellation contracts.
[Environment setup](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L680-L725),
[summary parsing](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L556-L623),
[capture and timeout](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L1361-L1483).

## Investigation

1. **Establish the current boundary.** Trace how `check_build_provenance.py` is invoked, how its tests are selected and executed, and how failures, output, cleanup, and evidence reach the existing dispatcher. Identify the responsibilities pytest should assume within that boundary.

2. **Freeze a whole-file comparison baseline.** Inventory the `unittest` classes, fixtures, setup and cleanup behavior, assertions, subprocess controls, and shared helpers. Distinguish organizational machinery from meaningful test-specific behavior. Derive the baseline from source: record the revision and every test method and meaningful variant, including `subTest` variants, what they exercise and assert, their inputs and expectations, relevant state transitions, and how outcomes are recorded. Compact tables may describe variants without repeating each loop iteration. Flag questionable expectations in the record.

3. **Apply the four pattern families.** Select a few patterns worth trying, identifying the conditions that make them work and important differences from PW.

4. **Evaluate subordinate integration.** Design pytest execution within the existing catalog and dispatcher. Compare running the current tests largely unchanged with gradually adopting pytest fixtures, parametrization, and assertions. Propose how dependencies and plugin/configuration discovery are controlled, which interpreter runs the tested helpers, and whether a structured inner report supplies information the outer case needs. Consider temporary-directory and cache ownership, execution ordering, diagnostics, cleanup, interruption, and retained evidence. Assess the value of an invocation-only transition separately from file-local refactoring.

5. **Examine representative refactors and remaining variants.** Select tests with materially different characteristics, including independent variations and an intentionally stateful sequence. Describe each under a recognizable common pytest pattern: what machinery could disappear, and what might become harder to understand or verify. For necessary departures, distinguish real requirements, inherited arrangements that can change, and poor fits. Keep exceptions understandable and local. Propose a later trial that adopts the patterns far enough to evaluate these tradeoffs.

6. **Estimate the work.** Estimate initial integration, subsequent file-local refactoring, and verification, distinguishing mechanical work from changes requiring judgment. Explain how successive stages could show which exceptions persist, disappear, or move as more checks adopt the common patterns.

## Verification to design

Design the later trial's comparisons of named scenarios, assertions, state transitions, and failure continuation against the frozen baseline.

For the integration boundary, propose small synthetic suites through the actual PW invocation path with passing, failing, setup-error, teardown-error, combined-failure, empty/deselected, and supported-skip cases. Include a malformed invocation or collection failure. Check the outer result and retained diagnostics, not just inner totals. A passing body with failing teardown must not become success; multiple faults must remain distinguishable. Settle PW's skip and no-test policy explicitly. A body-execution receipt can establish nonexecution after setup failure. Preserve selection and identity accounting without making each inner parameter a new catalog case.

Identify how interruption and fixture cleanup would be checked through the existing process ownership boundary. A raised `KeyboardInterrupt`, normal `finally` cleanup, or observation of a different PID does not establish OS signal delivery or descendant exit. Identify which raw inputs, output, and receipts the trial must retain and which build intermediates belong in scratch.

## Execution reference

Record an execution reference separately from the source baseline: the run's path, source revision, command/configuration, interpreter, duration, method count compared with the inventory, and the shape of retained evidence.

An existing run can supply the execution reference after an applicability check against current scripts, helpers, fixtures, configuration, and equipment. Record the dependency trace and any reviewed exceptions for changed files under [the evidence reuse guidance](../../AGENTS.md#evaluate-and-reuse-evidence); source identity alone does not prove completeness. Run fresh only when no applicable execution reference is available or a named investigative question needs a current observation that the case can supply.

When running the current case, use the repository root and `tests/run.sh --case preflight/build_provenance_controls` (add `--list` to inspect selection). Use a fresh `PW_TEST_OUT_DIR=tests/out/runs/<unique-name>`, keep `PYTHONOPTIMIZE` unset, and preserve evidence. Do not run the case script directly. Builds and test execution share `tests/.checkout.lock`; do not unlink it. Retained sources/logs/receipts belong in case `artifacts/`, intermediates in `PW_TEST_SCRATCH`. For a sandbox refusal, inspect the diagnostic and retry the same command once with escalation before attributing the failure.

## Deliverable

Write the baseline from step 2 as a separate record at `records/tests/pytest/`, titled with its revision and linked only from this plan. It is a snapshot; current-behavior corrections it reveals go to the suite README as separate changes. It names no direct invocation of the checker. Each later trial or migration stage appends its comparison row by row, using only the labels preserved, isolation-improved, blocked and revised. A flagged expectation stays in the record until its correction lands, when the row is updated and the commit named. Archive the record under `records/archive/tests/` when this plan closes.

Return a short assessment in the task response unless a separate destination is requested. Cite the record by path with its summary counts and flagged expectations. Include:

- The proposed integration and dependency/interpreter arrangement, with the execution reference and its applicability assessment.
- Useful external patterns and their source references, transfer limits, promising and unpromising refactor targets, and remaining variants.
- The proposed trial, staged effort estimate, and verification design.
- The smallest productive first implementation step.
- Reasons to defer or reject the refactor, if warranted.
