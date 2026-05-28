# runner_apply_isolation_v3

Positive smoke test for the host/worker split under an SBPL v3
`(deny default)` policy that pre-allows the syscalls the worker's
encode-and-write path needs. v3 is the strictest grammar today; this
suite proves the architectural split survives it.

## Invariants

- The XPC service host stays unsandboxed and posix_spawns the worker;
  the worker applies the policy to itself and writes a report.
- `runner_subprocess.pid` is the worker's PID, distinct from the XPC
  service host PID.
- `runner_result.pid` agrees with `runner_subprocess.pid` (top-level pid
  now names the worker).

## Success criteria

- `result.ok == true`, `runner_result.normalized_outcome == "ok"`.
- `runner_result.schema_version >= 3`.
- `runner_subprocess.exit_code == 0`, `term_signal == null`,
  `partial_steps == false`.
- `runner_result.pid == runner_subprocess.pid`.

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_apply_isolation_v3/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_apply_isolation_v3
```
