# runner_filter_sysctl_name

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

Exercises `(sysctl-read, sysctl_name)` with a policy denying reads of
`kern.osrelease`. The prediction is explicitly unavailable, while the real
`sysctl` / `read` attempt must report `sysctl_failed`, a nonzero `rc`,
and EPERM or EACCES in `errno`.

## Shared filter contract

The three `runner_filter_*` suites call `tests/lib/unavailable_prediction.py`
with their expected step ID, operation, filter value and attempt contract. The
adapter accepts only the current response and envelope versions. It uses `tests/lib/blackbox.py` to require a successful run envelope, SBPL
policy format, exact step identity/count, and evidence fields with their documented types.
An unavailable prediction has integer `rc=-1`, explicitly null `filter_type_id`
and `errno`, and the comparison carries the planner's `query_plan:*`
limitation with `order: unestablished`. Nullable evidence fields must
remain present, including `sandbox_check.error` and the attempt path fields.

The adapter checks the requested operation and the literal IOKit class or sysctl
name in `filter_value`, and requires a populated integer
`attempt.rc`. Each caller selects its attempt check:
this suite requires the sysctl denial described above; the IOKit suites require
a supported file-open result. Prediction and attempt errors accumulate, so a
broken prediction cannot hide a broken attempt. These checks concern the public
response, not internal function names or proof that a particular API was called.

## Checker controls

The `checker_controls` case runs before the app prerequisite check and exercises
all three callers using hand-authored envelopes and fixed CLI arguments. It
imports neither the checker nor production code. Valid nullable evidence,
supported file failures, and both permitted denial errnos must pass. Missing
fields, wrong sentinel values/types, a removed `drift` key, wrong/duplicate/
missing step IDs, operation/filter-value mismatches, incorrect policy format,
malformed envelopes and broken attempts must fail with relevant diagnostics.
Combined faults must report both channels.

Positive controls carry the comparison record and submitted-attempt evidence;
removing those fields must fail. Another, absent, null or non-integer response
or envelope version is reported as unsupported. Each of the three caller
contracts runs through the checker CLI.

These controls need only Python 3 and run in the default battery through this
suite. They can also be run directly:

```sh
/usr/bin/python3 tests/suites/runner_filter_sysctl_name/checker_controls.py tests/out/filter-controls
```

## Fixtures and artifacts

`run.sh` generates the live specimen inline. Artifacts under
`<run>/suites/runner_filter_sysctl_name/<test_id>/artifacts/` retain the
specimen, raw `run.json`, `pw.stderr`, and assertion log. The control case retains
each input envelope and the checker's arguments, status and diagnostics.

```sh
./tests/run.sh --suite runner_filter_sysctl_name
```
