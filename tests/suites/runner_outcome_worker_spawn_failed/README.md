# runner_outcome_worker_spawn_failed

Drives `normalized_outcome = "worker_spawn_failed"` end-to-end by
pointing `_test_overrides.worker_executable_path` at a nonexistent
file. The real `posix_spawn` returns `ENOENT`; the host's spawn-failure
branch translates the error into the outcome without ever observing a
worker.

## Invariants

- The override is honored only at the `posix_spawn` boundary inside
  `CWorker.spawn`. The classifier and envelope assembly run for real.
- The override is mirrored back into `runner_result.test_overrides`.

## Success criteria

- `result.ok == false`.
- `runner_result.normalized_outcome == "worker_spawn_failed"`.
- `runner_result.error` mentions `posix_spawn` or the override path
  (proves the real spawn was attempted).
- `runner_result.test_overrides.worker_executable_path` equals the
  value sent.
- `runner_result.runner_subprocess == null` (no worker spawned).
- `runner_result.steps == []`.

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_outcome_worker_spawn_failed/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_worker_spawn_failed
```
