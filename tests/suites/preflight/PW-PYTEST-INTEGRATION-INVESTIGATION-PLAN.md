# Investigation Plan for Subordinate pytest Integration

## Objective

Investigate the effort required to introduce pytest beneath PolicyWitness's existing test infrastructure, with the specific aim of eventually refactoring [check_build_provenance.py](check_build_provenance.py). The opportunity is to replace ordinary organizational work with familiar machinery where that improves clarity and maintenance.

This plan contains the research findings, rationale, comparison targets, and remaining questions needed for the investigation. The external comparison is bounded to the four projects below. Their source was inspected on 2026-10-26; neither those tests nor a PW migration prototype were executed. The comparison baseline, integration design, and effort estimate remain to be established.

This is an investigation, not implementation. Do not refactor tests, install a new repository dependency, or change the dispatcher while carrying it out. Describe a later trial where experience is needed to resolve a question. Return the assessment in the task response unless a separate destination is requested.

## Current PW boundary and comparison targets

The following observations are grounded in PW source at `95a08b7`. Recheck them against the revision used for the comparison baseline.

- [tests/run.sh](../../run.sh) enters [test_cli.py](../../lib/test_cli.py), which selects work from [catalog.json](../../catalog.json). The public case is `preflight/build_provenance_controls`; its declared equipment is `clang`, without a distribution-app requirement.
- [The preflight entry](run.sh) starts that case, calls `test_check_python`, retains `artifacts/assertions.log`, and emits the outer result. [case.sh](../../lib/case.sh) captures both streams and refuses a nonzero checker exit before the success event. The checker currently ends in `unittest.main(verbosity=2)`.
- [python_start.sh](../../lib/python_start.sh) resolves and checks the Homebrew `python@3.14` interpreter and rejects most inherited `PYTHON*` variables. `test_check_python` starts that interpreter with `-B -S`. The checker sets `PYTHON = sys.executable`, imports production helpers in-process, and launches subprocesses. Introducing a pytest host environment can therefore change tested inputs unless those boundaries are kept explicit. The investigation does not depend on a Python upgrade or interpreter migration.
- The dispatcher owns case selection, prerequisites, checkout locking, outer accounting, interruption, and evidence retention. [suite_run.py](../../lib/suite_run.py) is the execution boundary. [Dispatcher controls](../dispatcher/check.py) already exercise the public command with constructed failures, retain streams and exit receipts, inspect summaries/journals, and check that an ordinary failure does not suppress a later passing case. [Cancellation controls](../dispatcher/check_cancellation.py) separately observe signal delivery and descendant exit.

These are concrete starting points within `check_build_provenance.py`, not a completed inventory:

| Target | Candidate organization | Behavior or uncertainty to preserve |
| --- | --- | --- |
| `RecordTests.test_records_are_validated_by_shape_in_every_reader` | Named independent faults applied to fresh copies of an accepted record. | Each fault reaches both the shape checker and bundle reader. Retain accepted neighbours and the separate metadata/signature cases; expectations must remain independent of the production validator. |
| `RecordTests.test_records_are_bounded_redacted_and_complete` | Isolated mutable input per fault, with authored expected diagnostic codes. | The current loop restores the record after assertions inside `subTest`; a failure can skip restoration and affect the next variant. This is an inspected risk, not a reproduced failure. Any isolation improvement must be identified in the comparison. |
| `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` and `StampFixture` | A prepared checkout plus a visible stateful sequence. | Preserve publication, unchanged reuse, refusal without rewriting bytes, and extension of only permitted fields. Independent malformed-stamp inputs may separate; lifecycle transitions should stay understandable. |
| `own`, lock/process controls, and environment-preservation checks | Fixtures may prepare resources while specialized observations remain explicit. | Lock handoff, descendant lifetime, raw environment comparisons, and deadlines are subjects of the checks, not incidental runner machinery. |

`RecordTests.setUp` compiles a native fixture host once per current test method. Parametrization may multiply that cost. Investigate whether immutable preparation can be shared separately from mutable bundles; the external examples do not establish the safe sharing boundary or runtime benefit for PW.

## Four patterns to evaluate

The links pin the inspected source revisions. The summaries carry the findings needed for this plan; consult the linked implementations and their supporting fixtures when a specific transfer question needs more detail.

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

1. **Establish the current boundary.** Trace how `check_build_provenance.py` is invoked, how its tests are selected and executed, and how failures, output, cleanup, and evidence reach the existing dispatcher. Identify the responsibilities pytest should assume and those that should remain with the surrounding infrastructure. Examine the dependency and interpreter boundary without making the investigation contingent on a particular Python version or interpreter migration.

2. **Inventory the file and freeze a comparison baseline.** Examine its `unittest` classes, fixtures, setup and cleanup behavior, assertions, subprocess controls, and shared helpers. Distinguish organizational machinery from meaningful test-specific behavior. Record the source revision and the selected checks, what they exercise and assert, their inputs and expectations, relevant state transitions, and how outcomes are recorded. This gives a later migration a concrete baseline against which to assess organizational changes. Flag questionable expectations separately: freezing the comparison does not make every expectation a permanent requirement, and revising one must remain distinguishable from changing the machinery that executes it.

3. **Apply the four pattern families.** Use the findings above to identify a few patterns worth trying, the conditions that make them work, and important differences from PW. Consult the linked test bodies and supporting fixtures or invocation paths for unresolved transfer questions. The external survey is complete; keep further comparison bounded to these four projects.

4. **Evaluate subordinate integration.** Determine how pytest could execute within the existing catalog and dispatcher without replacing their authority. Compare running the current tests largely unchanged with gradually adopting pytest fixtures, parametrization, and assertions. Settle how dependencies and plugin/configuration discovery are controlled, which interpreter runs the tested helpers, and whether a structured inner report supplies information the outer case needs. Consider temporary-directory and cache ownership, execution ordering, diagnostics, cleanup, interruption, and retained evidence. Distinguish a useful transitional step from an organizational improvement; do not assume that swapping the invocation alone reduces maintenance.

5. **Examine representative refactors and the variants that remain.** Select several tests with materially different characteristics. Include independent variations and an intentionally stateful sequence where the file provides them. Describe how each might look under a recognizable common pytest pattern, what existing machinery could disappear, and what might become harder to understand or verify. Propose a later trial that adopts the pattern far enough to experience its advantages and constraints. The purpose is both to reduce ordinary infrastructure maintained by PW and to discover which inherited choices become unnecessary when pytest supplies the organization; reconstructing the old framework through elaborate fixtures and hooks would obscure that learning. Examine necessary departures: do they preserve a real requirement, accommodate an inherited arrangement that can change, or indicate a poor fit? Keep necessary exceptions understandable and local while retaining the different forms the tests' jobs require. Identify which judgments need the trial rather than source inspection. Do not implement examples in the repository.

6. **Estimate the work.** Identify the changes needed for initial integration, subsequent file-local refactoring, and verification. Distinguish mechanical work from changes requiring judgment. Explain how a later implementation could compare the frozen baseline with the migrated checks while keeping deliberate expectation changes identifiable. Include how successive stages within this file could show which exceptions persist, disappear, or move as more checks adopt the common patterns.

## Verification to design, and evidence limits

The assessment must explain how a later trial would compare named scenarios, assertions, state transitions, and failure continuation with the frozen baseline. Equal method/parameter counts or a zero exit do not establish preservation. Keep deliberate expectation revisions and isolation improvements identifiable. Label source-derived findings separately from measured behavior; no passing migration evidence exists from this investigation yet.

For the integration boundary, propose small synthetic suites through the actual PW invocation path with passing, failing, setup-error, teardown-error, combined-failure, empty/deselected, and supported-skip cases. Include a malformed invocation or collection failure. Check the outer result and retained diagnostics, not just inner totals. A passing body with failing teardown must not become success; multiple faults must remain distinguishable. Settle PW's skip and no-test policy explicitly. A body-execution receipt can establish nonexecution after setup failure. Preserve selection and identity accounting without making each inner parameter a new catalog case.

Identify how interruption and fixture cleanup would be checked through the existing process ownership boundary. A raised `KeyboardInterrupt`, normal `finally` cleanup, or observation of a different PID does not establish OS signal delivery or descendant exit. Identify which raw inputs, output, and receipts the trial must retain and which build intermediates belong in scratch.

If current-case execution is needed to resolve an investigative question, run from the repository root through `tests/run.sh --case preflight/build_provenance_controls` (add `--list` to inspect selection). Use a fresh `PW_TEST_OUT_DIR=tests/out/runs/<unique-name>`, keep `PYTHONOPTIMIZE` unset, and preserve evidence. Do not run the case script directly. Builds and test execution share `tests/.checkout.lock`; do not unlink it. Retained sources/logs/receipts belong in case `artifacts/`, intermediates in `PW_TEST_SCRATCH`. For a sandbox refusal, inspect the diagnostic and retry the same command once with escalation before attributing the failure. Existing evidence needs an applicability check against current scripts, helpers, fixtures, configuration, and equipment; source identity alone does not prove completeness.

## Deliverable

Write a short assessment containing:

- A proposed integration boundary, dependency/interpreter arrangement, and recorded comparison baseline.
- A few useful external patterns, with source references and their transfer limits.
- Promising and unpromising refactor targets within `check_build_provenance.py`.
- Significant variants likely to remain, with reasons or unresolved questions and a proposed trial to resolve judgments that need experience with the patterns.
- A staged effort estimate, including important uncertainties.
- A verification design covering preservation, reporting failures, cleanup, and evidence ownership; for each unresolved consequential question, the observation or trial that would answer it and the work depending on that answer.
- The smallest productive first implementation step.
- Reasons to defer or reject the refactor, if warranted.

Preserve the possibility that pytest integration is worthwhile even if substantial portions of the file remain unchanged. Judge the proposal by whether it reduces infrastructure that requires PW-specific knowledge and makes the remaining special cases clearer, rather than by the proportion converted.

## Scope

Keep proposed migration work within `check_build_provenance.py` and the integration changes necessary to run it subordinately. Inspect surrounding code and related projects as needed to understand that boundary.

Do not propose migrating other test files, replacing PolicyWitness’s dispatcher, or restructuring the wider test system. Leave implementation and changes to existing expectations for a subsequent decision.
