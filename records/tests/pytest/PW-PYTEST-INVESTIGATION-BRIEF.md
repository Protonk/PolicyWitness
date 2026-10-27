# Investigating subordinate pytest adoption in PolicyWitness

## 1. Patterns worth investigating

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

## 2. Freezing a baseline and learning from the variants

Freeze a comparison baseline: the selected checks, what they exercise and assert, and how their outcomes are recorded. This gives later changes something concrete to be compared with. It does not turn every existing expectation into a permanent requirement. If an expectation deserves revision, make that decision distinguishable from changing the machinery that executes it.

Adopt a recognizable common pattern far enough to experience its advantages and constraints. The purpose is partly to stop maintaining ordinary infrastructure ourselves, and partly to discover which choices become unnecessary when another tool supplies the organization. Reconstructing the old framework through elaborate fixtures and hooks would obscure that distinction.

Then examine the variants that remain. Resistance might reveal a real PW requirement, an inherited arrangement that can change, or a poor framework fit. Keep necessary exceptions understandable and local. Over time, compare which exceptions persist, disappear, or move as more work adopts the common pattern.

Success is not the proportion migrated. It is less machinery that requires PW-specific knowledge, with clearer reasons for what remains particular to PW. Ordinary tests should demonstrate that practice through their structure, while retaining the different forms their jobs require.

