# runner_sandbox_denied

The bug-report specimen, verbatim: a bare `(version 2) (deny default)`
policy whose worker is terminated by the kernel sandbox before it can
write a report. Proves the host classifier surfaces this as
`runner_sandbox_denied` rather than `xpc_error`, with the terminating
signal preserved.

## Invariants

- The unsandboxed host always replies; the worker dies from a fatal
  signal (SIGKILL, SIGTRAP from libSwift's malloc trap under deny-default,
  or SIGABRT).
- `runner_subprocess.term_signal` records the exact signal observed via
  waitpid.

## Success criteria

- `result.ok == false`.
- `runner_result.normalized_outcome == "runner_sandbox_denied"`.
- `runner_subprocess.term_signal` is a positive integer (one of 5, 6, 9
  observed in practice).
- `runner_result.pid == runner_subprocess.pid`.

## Fixtures

- Specimen generated inline by `run.sh`, taken verbatim from the bug
  report that motivated the host/worker split.

## Artifacts

- `tests/out/suites/runner_sandbox_denied/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_sandbox_denied
```
