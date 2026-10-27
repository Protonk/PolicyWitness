# Investigating subordinate pytest adoption in PolicyWitness

## Patterns worth investigating

Investigate pytest as a subordinate harness for build and mutation checks, with `tests/run.sh` retaining project-level dispatch. Existing checks already use `unittest`; the opportunity is to replace organizational work with familiar machinery where that improves clarity and maintenance.

The following projects offer different kinds of precedent. Inspect their supporting fixtures and invocation paths, not just individual test bodies. Treat them as leads rather than a prescribed design, and record revisions when relying on source-specific findings.

### Zephyr and the division of responsibility

[Twister’s pytest harness](https://docs.zephyrproject.org/latest/develop/twister/harness/pytest.html) keeps pytest beneath a broader test system. Twister retains discovery, building, parallel execution, and reporting, while selecting pytest tests and consuming their results.

Examine how invocation context reaches pytest, how inner results return to the outer runner, and which responsibilities remain outside fixtures. What is the smallest useful equivalent for PW? Which parts of Zephyr’s integration exist because it manages devices and would add nothing here?

The [multiple-key MCUboot test](https://github.com/zephyrproject-rtos/zephyr/tree/main/tests/boot/mcuboot_multiple_keys) is a related lead. Its README describes re-signing a built application with another test key, then booting it under QEMU and checking the result. Investigate its implementation before drawing conclusions about how its fixtures manage artifact mutation.

### meson-python and visible build sequences

[The editable-install tests](https://github.com/mesonbuild/meson-python/blob/main/tests/test_editable.py) contain concrete examples:

- `test_editable_verbose` touches compiled source, observes a rebuild, and checks an unchanged subsequent import.
- `test_editable_rebuild_error` introduces invalid C and checks the resulting error and diagnostics.
- `test_editable_reconfigure_error` changes `meson.build` to provoke and inspect a reconfiguration failure.

Study what the fixtures supply and what remains visible in each test. How do they distinguish preparing an environment from performing the action under examination? Where does one coherent sequence deserve to remain together?

These are precedents for organizing build work, not for subordinate dispatch. Some restore modified source in `finally`; assess that choice against PW’s needs rather than importing it with the surrounding pattern.

### PyPA build and independent malformed inputs

[The project-builder tests](https://github.com/pypa/build/blob/main/tests/test_projectbuilder.py) demonstrate small, explicit rejection cases. `test_metadata_path_ambiguous_dist_info` parameterizes zero and two metadata directories, arranges for a backend to construct the malformed wheel, and checks rejection. Other cases exercise invalid output paths and missing backends.

Consider the relationship between scenario descriptions, baseline fixtures, and authored expectations. Does parametrization make each case easier to understand and extend? Avoid deriving expected answers from the same production rules the checks are meant to examine.

In PW, the record-shape mutation family in `check_build_provenance.py` is a promising comparison point. Inspect its current form and any existing pytest proposal locally. Stateful stamp and fresh/reuse/recovery checks may benefit from a different arrangement. Also examine the harness dependency boundary: the previously inspected Python launcher used `-B -S`, so introducing pytest must account for the distinction between the harness environment and the helpers being tested.

### pytest and checking the integration itself

[Pytest's runner tests](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/testing/test_runner.py) construct small test programs with known outcomes and check their reports and exit status. This supplies a fourth perspective: how to verify the machinery that will execute PW's checks.

Examine failure phases, empty selection, and combined failures. Distinguish in-process protocol checks from execution through a command boundary. The [supporting pytester implementation](https://github.com/pytest-dev/pytest/blob/41d12cdbb4a35a7877768d93d8dc50a9117a8d8c/src/_pytest/pytester.py) has its own environment, capture, and timeout policies; assess their fit separately from the synthetic-test pattern.

PW already constructs dispatcher failures. The useful comparison is how pytest-specific scenarios could exercise the eventual subordinate invocation and its retained evidence, within the existing dispatcher contract. It does not call for adopting pytest's internal runner APIs or migrating the dispatcher tests.

