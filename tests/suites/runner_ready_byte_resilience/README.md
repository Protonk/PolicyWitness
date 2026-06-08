# runner_ready_byte_resilience

Regression guard for the `com.apple.WebProcess` SIGPIPE bug. A large
profile's `sandbox_compile_string` runs longer than the host's
`readyByteTimeout` (default 1000ms). The worker writes its pre-apply
ready byte only *after* that compile, by which point the host has
closed `--ready-fd`. The worker must **not** die of SIGPIPE on that
write — it must continue to `sandbox_apply` and report through the shm
sentinels, so the run still scores normally.

The suite models the slow compile deterministically with
`_test_overrides.worker_pre_ready_hang_ms = 2000` (no 13s WebProcess
compile needed): `pw-probe-runner` `nanosleep`s 2000ms before the ready
byte, so the host's 1000ms `readyByteTimeout` fires first and closes the
read end. Under `(allow default)` the worker then applies cleanly and
scores a one-step probe plan.

## Invariants

- `pw-probe-runner` ignores SIGPIPE (set in `main`), so the ready-byte
  write to a host-closed pipe returns EPIPE instead of killing the
  worker. Its "Continue anyway" comment after `write_ready_byte` then
  holds: apply + the shm sentinel path still run.
- On the **pre-fix** worker this exact path SIGPIPEs the worker before
  apply: no `applied`, `apply_rc` reads zero-init 0,
  `normalized_outcome="sandbox_apply_failed"`, `term_signal=13`. So a
  regression fails this suite loudly.

## Success criteria

- `result.ok == true`.
- `runner_result.normalized_outcome == "ok"`.
- `runner_subprocess.term_signal == null` (no SIGPIPE) and `exit_code == 0`.
- `validator_subprocess` present and exactly one scored step (the worker
  applied, so the validator ran).
- `runner_result.test_overrides.worker_pre_ready_hang_ms == 2000`.

## Fixtures

- Specimen generated inline by `run.sh`.

## Artifacts

- `tests/out/suites/runner_ready_byte_resilience/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_ready_byte_resilience
```

Suite runs in ~2-3s wall-clock.
