# runner_outcome_runner_timeout

Drives `normalized_outcome = "runner_timeout"` end-to-end by combining
`_test_overrides.worker_timeout_ms = 2000` with
`_test_overrides.worker_post_apply_hang_ms = 8000`. The C worker
survives sandbox apply but hangs in `pw-probe-runner`'s post-apply
seam; the host's deadline fires first and SIGKILLs it.

## Invariants

- The host shortened the worker's life (SIGKILL at its deadline) rather
  than waiting for the worker's ~8s natural sleep. This is proven
  deterministically by the envelope — `runner_timeout` + `term_signal == 9`
  + `exit_code == null` — not by wall-clock: a worker that completed its
  hang would have flipped `done` and clean-exited (`ok`, `exit_code == 0`).
- `term_signal == 9` (SIGKILL, host-issued). The `timedOut` flag in
  `classifyWorkerResult` takes precedence over the term_signal=9 path
  that would otherwise produce `runner_sandbox_denied`.

## Success criteria

- `result.ok == false`.
- `runner_result.normalized_outcome == "runner_timeout"`.
- `runner_subprocess.term_signal == 9` and `exit_code == null`.
- `runner_result.test_overrides.worker_timeout_ms == 2000`.
- `runner_result.steps == []`.

The run uses `--no-log-capture`: the test reads only `runner_result`
fields, and skipping the post-run `log show` scan keeps it fast and
independent of the host's unified-log archive size.

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_outcome_runner_timeout/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_runner_timeout
```

Suite runs in a few seconds (the 2s host deadline + reap grace; no log scan).
