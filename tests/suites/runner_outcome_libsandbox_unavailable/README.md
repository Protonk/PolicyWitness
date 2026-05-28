# runner_outcome_libsandbox_unavailable

Drives `normalized_outcome = "libsandbox_unavailable"` end-to-end by
pointing `_test_overrides.libsandbox_path` at a nonexistent file. The
real `dlopen` returns NULL with a real `dlerror`; the host's pre-spawn
libsandbox check short-circuits and returns the outcome without
spawning a worker.

## Invariants

- The override is honored only at the `SandboxLib.load(path:)`
  boundary. The classifier and envelope assembly run for real.
- The override is mirrored back into `runner_result.test_overrides` so
  the resulting envelope is self-describing.

## Success criteria

- `result.ok == false`.
- `runner_result.normalized_outcome == "libsandbox_unavailable"`.
- `runner_result.error` mentions the override path (proves the real
  loader was exercised, not a stub returning a constant).
- `runner_result.test_overrides.libsandbox_path` equals the value sent.
- `runner_result.runner_subprocess == null` (host short-circuits before
  posix_spawn).
- `runner_result.steps == []`.

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_outcome_libsandbox_unavailable/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_libsandbox_unavailable
```
