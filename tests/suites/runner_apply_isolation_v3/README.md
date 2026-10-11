# runner_apply_isolation_v3

Empty-plan smoke test for application and reply survival under an SBPL v3
`(deny default)` policy with syscall and file-existence allowances. It checks
reported application, worker PID consistency and clean termination; it does not
exercise populated attempt slots.

## Invariants

- The worker reports `sandboxed_after_apply == true`, and the host returns
  the completed reply through the ordinary CLI route.
- `runner_subprocess` is present and records clean worker termination.
- `runner_result.pid` agrees with `runner_subprocess.pid` (top-level
  pid names the worker).

## Success criteria

- `result.ok == true`, `runner_result.normalized_outcome == "ok"`.
- The envelope and response use the currently supported contract versions.
- `sandboxed_after_apply == true` and `steps == []`.
- `runner_subprocess.exit_code == 0`, `term_signal == null`,
  `partial_steps == false`.
- `runner_result.pid == runner_subprocess.pid`.

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/runner_apply_isolation_v3/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_apply_isolation_v3
```
