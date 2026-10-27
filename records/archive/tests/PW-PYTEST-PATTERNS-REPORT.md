# Report: pytest patterns from four projects

The most useful patterns are explicit outer-runner result handling, fixtures
that prepare resources while leaving the tested action visible, independent
malformed-input cases with authored expectations, and small synthetic suites
that check execution and reporting. None requires converting
every test to the same shape. The examples also retain substantial local
machinery where their subject requires it.

This report covers the external-pattern research in investigation item 3, with
limited comparisons to PW. It is source inspection, not execution evidence:
no upstream tests, PW tests, or migration prototypes were run. Integration
design, a complete baseline inventory, and implementation estimates remain
outside this report.

## Sources and method

Inspected on 2026-10-26. Research stopped at these four projects; supporting
fixtures, configuration, and invocation code belong to the same sources.
Links below pin the inspected revisions rather than moving branches.

| Project | Inspected revision | Main question |
| --- | --- | --- |
| [Zephyr](https://github.com/zephyrproject-rtos/zephyr/tree/d1d74eba22d6565eaead5840d2352b74fb4039ff) | `d1d74eba22d6565eaead5840d2352b74fb4039ff` | How does pytest operate beneath another test runner? |
| [meson-python](https://github.com/mesonbuild/meson-python/tree/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51) | `70d921dcb4cc28e80e2b1620e5eb7b0886e48b51` | What stays visible in build and mutation sequences? |
| [PyPA build](https://github.com/pypa/build/tree/4d37ed7edbf629c30500950e1164d21628eb697c) | `4d37ed7edbf629c30500950e1164d21628eb697c` | How are independent malformed inputs arranged and judged? |
| [pytest](https://github.com/pytest-dev/pytest/tree/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c) | `41d12cdbb4a35a7877768d93d8dc50a9117a8d8c` | How is the test runner itself checked against known outcomes? |

PW comparisons use commit `23db75321a548aa1beef15becccc9980e1adcdf2`.
Each example was followed from its test body into the relevant fixtures and
invocation path. Transfer suggestions below are judgments from that inspection,
not demonstrated migration results.

## Zephyr: explicit result translation and prepared resources

Twister's `Pytest.generate_command` selects test roots, writes a YAML context
file, and invokes `sys.executable -m pytest` with a JUnit report destination.
`ReportHarness` handles execution and tool-error statuses; the pytest adapter
translates XML results into Twister case statuses. The command, output, and
return code are also written to a harness log. Report parsing failures fail the
scenario, while the parser has skip paths for an empty report structure and
an all-skipped suite. These are concrete outer-runner policy choices.
[Invocation and result handling](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/scripts/pylib/twister/twisterlib/harness.py#L571-L835).

**Transfer:** an inner test framework can report detail while the outer runner
retains authority over the case. For PW, this supports retaining the catalog
case and its evidence directory. It does not establish that PW needs XML or
Twister's plugin: a structured report is useful only if a PW reader needs its
information. Collection, skip, and tool-error policy still need explicit
decisions; Twister's choices are not PW's acceptance rules.

The MCUboot example makes the preparation/action distinction especially clear.
Its [scenario configuration](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/tests/boot/mcuboot_multiple_keys/tests.yaml)
supplies an expected key ID and, for one scenario, a replacement signing key.
The test obtains build paths through `unlaunched_dut`, optionally re-signs to a
separate image, launches QEMU itself, and checks both the reported verification
key and the application's boot banner. Re-signing reuses the build's signing
arguments with a different key and output; the expected key ID remains supplied
independently. Domain discovery, command extraction, console reading, deadlines,
and termination are ordinary local functions.
[Test and helpers](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/tests/boot/mcuboot_multiple_keys/pytest/test_multiple_keys.py#L47-L163).

The supporting plugin builds configuration during pytest setup.
`unlaunched_dut` initializes logs and closes the adapter after use; the separate
`dut` fixture adds launch. This lets the MCUboot test choose prepared resources
without triggering the ordinary launch operation before its mutation.
[Plugin setup](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/scripts/pylib/pytest-twister-harness/src/twister_harness/plugin.py#L157-L173),
[fixture lifetimes](https://github.com/zephyrproject-rtos/zephyr/blob/d1d74eba22d6565eaead5840d2352b74fb4039ff/scripts/pylib/pytest-twister-harness/src/twister_harness/fixtures.py#L24-L97).

**Transfer limit:** PW could use a fixture for a disposable checkout or baseline
bundle while leaving publication, mutation, and observation in the test. The
device adapters and configurable device lifetimes solve Zephyr-specific work.
The example also shows why local process helpers can remain necessary; adopting
pytest does not make their behavior redundant.

## meson-python: coherent sequences and the cost of shared state

`test_editable_verbose` observes a quiet import, touches a compiled source,
observes rebuild output on import, and observes a quiet subsequent import.
The sequence communicates the transition being tested. The rebuild-error and
reconfiguration-error tests visibly introduce invalid C or a Meson error,
trigger import, and inspect failure diagnostics. Their `finally` blocks undo
import-hook changes and restore source contents.
[Editable tests](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/tests/test_editable.py#L316-L402).

**Transfer:** PW's publish/reuse/refuse/extend sequences can remain coherent
tests. Fixtures can supply the initial checkout and observation without hiding
the operations whose order matters. Independent variants, such as the verbose
flag on the rebuild-error test, can still be parametrized around a sequence.

The fixtures qualify that attractive surface. `package_*` changes into a source
fixture directory; it does not copy it. Editable wheels are built once per
session, while `venv` creates an environment per test. Generated fixture names
hide that setup behind names such as `editable_complex`. Session-wide autouse
fixtures also alter the environment, including removing
`MACOSX_DEPLOYMENT_TARGET`.
[Fixture implementation](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/tests/conftest.py#L98-L199).

**Transfer limit:** sharing expensive preparation entails restoration and
coupling costs. Source restoration in `finally` is useful for ordinary failures
but does not establish recovery after forced termination. PW's disposable
mutation inputs and retained evidence need their own ownership design. Global
environment cleanup would also need special scrutiny where the environment is
itself under examination.

CI installs test dependencies and invokes pytest directly, and project
configuration enables strict markers/configuration and warning errors.
This is useful test organization, not a second example of Twister-style result
translation.
[CI invocation](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/.github/workflows/tests.yml#L154-L160),
[pytest configuration](https://github.com/mesonbuild/meson-python/blob/70d921dcb4cc28e80e2b1620e5eb7b0886e48b51/pyproject.toml#L131-L140).

## PyPA build: constructed artifacts and independent expectations

`test_metadata_path_ambiguous_dist_info` names two parameters, zero and two
metadata directories. It replaces the backend hook interface, makes metadata
preparation unavailable, and supplies a fake wheel-building hook that writes an
actual ZIP. The real metadata reader then has to reject those bytes with the
authored exception expectation. The adjacent build-tag test supplies a valid
wheel and checks extracted metadata. The malformed-input test therefore mocks
artifact production, not the reader whose decision it checks.
[Wheel cases](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tests/test_projectbuilder.py#L665-L714).

The same file pairs malformed configuration values with literal expected
messages, and uses named setup functions for nonexistent and non-directory
backend paths. These are small parameter sets whose inputs and outcomes can be
read together.
[Configuration and path cases](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tests/test_projectbuilder.py#L768-L836).

**Transfer:** PW's record faults can become named independent cases with a fresh
copy of an accepted record. The test can retain the authored fault and expected
diagnostic while exercising the real readers. Accepted neighbouring values
remain important controls. A parameter table should not obtain its expected
answer from the production schema or validator.

Here too, fixture names alone do not establish isolation. Package fixtures copy
setuptools-based projects into `tmp_path`, but return the source directory for
others. A custom `tmp_dir` fixture removes its directory at teardown. Other
fixtures alter environment variables and caches; collection hooks implement
integration selection through skips and ordering.
[Supporting fixtures and hooks](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tests/conftest.py#L30-L173).

Tox supplies test dependencies, invokes pytest with coverage, and defaults to
parallel workers; pytest configuration declares markers and strictness.
[Invocation](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/tox.toml#L14-L37),
[configuration](https://github.com/pypa/build/blob/4d37ed7edbf629c30500950e1164d21628eb697c/pyproject.toml#L199-L223).
Those policies serve that project. PW's dispatcher already owns selection,
equipment, and execution locking, and temporary-directory removal cannot
substitute for its evidence-retention rules.

## pytest: synthetic suites that check execution and reporting

Pytest's own tests provide a useful fourth example for integration verification.
Tox invokes pytest, project configuration loads the `pytester` plugin, and the
test suite's fixture disables third-party plugin autoloading for its nested
runs. The examples therefore come with explicit supporting configuration.
[Tox invocation](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/tox.ini#L65-L78),
[plugin loading](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/pyproject.toml#L422-L429),
[fixture override](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/conftest.py#L160-L163).

The runner tests construct small programs whose outcomes are authored alongside
their source:

| Scenario | What the upstream control checks |
| --- | --- |
| Setup or teardown raises | The failing phase is identified; setup failure yields two reports and teardown failure three. A separate control checks a failing return code after a passing body and failing teardown. |
| Nothing selected, then a passing test, then that test deselected | Empty selection and deselection return `NO_TESTS_COLLECTED`; the positive neighbour returns `OK`. |
| Test failure plus module-fixture teardown failure under `--maxfail=1` | Both the test failure and teardown error remain in the outcome counts. |

[Phase and return-code controls](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py#L251-L324),
[selection control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py#L766-L785),
[combined-failure control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py#L1232-L1254).

The execution boundary matters. `runitem` delegates to an internal protocol
runner, and `inline_runsource` stays in-process. `runpytest` defaults to
in-process execution but supports a subprocess mode; the explicit subprocess
helper invokes the current interpreter with `-m pytest`.
[Execution helpers](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L1061-L1089),
[mode default](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L93-L102),
[subprocess command](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L1493-L1533).

Supporting self-tests independently check that subprocess mode changes PID.
Another supplies an invalid CLI argument and expects outcome parsing to raise
rather than report zero outcomes. These checks support the helpers' specific
contracts; they do not establish execution through PW's launcher.
[Process-boundary control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_pytester.py#L419-L441),
[missing-summary control](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_pytester.py#L298-L307).

**Transfer:** construct a small set of known pytest scenarios and exercise the
eventual PW invocation path, including its outer case result and retained logs.
A passing body with failing teardown must not become a successful case;
combined failures should remain distinguishable in diagnostics. Setup failure
can include a body-execution receipt to establish that the body did not run.
Empty selection and supported skips need expectations derived from PW's chosen
integration contract. Inner outcome counts need not become separate catalog
cases or replace the existing outer accounting.

This extends a pattern PW already uses.
[Dispatcher controls](../../../tests/suites/dispatcher/check.py) run the public
command in fixture repositories, retain stdout/stderr and exit records, inspect
the summary and journal, and check that ordinary failures do not suppress a
later passing case. They already cover passing reports followed by crashes and
failed reports with zero exits. The fourth example contributes pytest-specific
stimuli at the new boundary, not a reason to migrate those controls.

**Transfer limits:** `pytester` changes the working directory and home variables;
its subprocess launcher injects `PYTHONPATH`. Outcome counts are parsed from
terminal summaries. Repeated subprocess runs overwrite the same `stdout` and
`stderr` files. Timeout handling kills and waits for the direct child, without
a process-group cleanup operation in that helper.
[Environment setup](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L680-L725),
[summary parsing](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L556-L623),
[subprocess environment, capture, and timeout](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py#L1361-L1483).

Those policies need separate evaluation against PW's controlled helper
environment, per-run evidence, and cancellation ownership. In-process protocol
checks and a raised `KeyboardInterrupt` also cannot establish OS signal delivery
or descendant exit. PW's
[cancellation controls](../../../tests/suites/dispatcher/check_cancellation.py)
remain the relevant local model for those observations. The fourth source is
worth retaining for its test construction and failure-accounting patterns,
without adopting its helper package as the integration design.

## Comparisons with PW

The following are candidate applications, not an implementation prescription.
All named methods are in
[check_build_provenance.py](../../../tests/suites/preflight/check_build_provenance.py).

| PW example | Useful pattern | Meaning to preserve or question to resolve |
| --- | --- | --- |
| `RecordTests.test_records_are_validated_by_shape_in_every_reader` | Named fault parameters with fresh mutable records. | Each fault currently reaches both the shape checker and the bundle reader. Preserve both checks, accepted neighbours, and the separate metadata/signature cases. |
| `RecordTests.test_records_are_bounded_redacted_and_complete` | Isolated mutation inputs with authored expected diagnostic codes. | Its mutation loop restores the record after assertions inside `subTest`. An assertion failure can bypass that restoration and leave the next variant a changed baseline. This is a source-level risk, not a reproduced failure; isolation would be an explicit behavior improvement to record in a later comparison. |
| `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` | Prepared checkout fixture plus visible stateful sequence. | Preserve publication, unchanged reuse, refusal without rewriting bytes, and extension of only permitted fields. Independent malformed-stamp variants may separate; the lifecycle should remain understandable. |
| `own`, lock/process controls, and environment-preservation checks | Fixtures may acquire resources; specialized observation and cleanup helpers remain explicit. | Lock handoff, descendant lifetime, raw environment comparisons, and deadlines are the subject of the checks, not incidental test-runner machinery. |

Parametrizing every record fault may also multiply setup cost:
`RecordTests.setUp` compiles a native fixture host once per current test method.
Sharing an immutable host could be investigated separately from giving each
case its own mutable bundle. The external examples establish neither the safe
sharing boundary nor the runtime benefit for PW.

PW currently selects one `preflight/build_provenance_controls` catalog case.
Its shell entry invokes the Python checker through `test_check_python`, captures
`assertions.log`, and declares the outer case result. That helper starts Python
with `-B -S`. The checker also sets `PYTHON = sys.executable` for subprocesses
and tests the constrained import/environment boundary itself.
[Case invocation](../../../tests/suites/preflight/run.sh),
[capture and Python launcher](../../../tests/lib/case.sh),
[catalog](../../../tests/catalog.json).

This makes the distinction between the pytest host and tested helpers material:
changing the host environment can change subprocess selection and inherited
inputs. meson-python's environment fixtures and Twister's plugin-path injection
are not ready-made solutions to that boundary. No interpreter migration is
assumed by these findings.

## What this research supports next

The sources provide enough concrete patterns to stop the external survey.
Record mutation cases are the clearest candidate for a later small trial;
stamp sequences are a useful comparison precisely because much of their visible
structure should remain. Further integration work needs to settle:

1. How pytest and its dependencies become available while the tested helpers
   keep their intended interpreter, import path, and environment.
2. What inner outcomes the outer case must account for, including collection
   failure, no tests, skips, setup/teardown errors, and interruption; which
   details belong in retained logs or a structured report. Synthetic-suite
   controls can then check that mapping through the actual invocation path.
3. Which preparation can be shared without sharing mutable state, and how
   scratch files, mutation inputs, and diagnostic evidence retain clear owners.

A later baseline comparison should map named scenarios, assertions, state
transitions, and failure continuation across the migration. Equal method or
parameter counts alone would not establish preservation. This report supports
that focused investigation; it does not yet establish that introducing pytest
will reduce PW's total maintenance work.
