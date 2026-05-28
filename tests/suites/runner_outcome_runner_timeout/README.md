# runner_outcome_runner_timeout

Drives `normalized_outcome = "runner_timeout"` end-to-end by combining
`_test_overrides.worker_timeout_ms = 2000` with a post-sandbox
`debug_wait` of 8000ms. The worker survives sandbox apply but hangs in
the instrumentation port; the host's deadline fires first and SIGKILLs
the worker.

## Invariants

- Wall-clock elapsed time matches the host deadline (~2s), not the
  worker's natural sleep (~8s). This distinguishes a real timeout from
  a worker that exited on its own.
- `term_signal == 9` (SIGKILL, host-issued). The `timedOut` flag in
  `classifyWorkerResult` takes precedence over the term_signal=9 path
  that would otherwise produce `runner_sandbox_denied`.

## Success criteria

- `result.ok == false`.
- `runner_result.normalized_outcome == "runner_timeout"`.
- `runner_subprocess.term_signal == 9` and `exit_code == null`.
- `runner_result.test_overrides.worker_timeout_ms == 2000`.
- Elapsed time under 6000ms (proves the host shortened the worker's
  life rather than waiting for the natural exit).

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_outcome_runner_timeout/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_runner_timeout
```

Suite runs in ~2s wall-clock.
