# runner_filter_sysctl_name

Same contract as `runner_filter_iokit_registry_entry_class`, applied
to the `(sysctl-read, sysctl_name)` pair. Empirical verification (see
`tests/suites/witness_contract/harness/verify_filter_id.sh`) confirms
the same `sandbox_check` unreliability pattern: no numeric filter ID
in 1..200 produces a verdict matching kernel enforcement. The runner
accepts the filter in specimens, skips `sandbox_check`, and emits
`step.sandbox_check.outcome = "prediction_unavailable"` with `rc=-1`
(sentinel). Cross-check mirrors.

This suite documents that the prediction_unavailable contract is not
iokit-specific — the userland predicate's drift from kernel
enforcement applies to syscall-level operations too.

## Invariants

- `validateSandboxChecks` accepts `sysctl_name` as a filter kind.
- `runSandboxCheck` short-circuits before calling `sandbox_check` for
  this (op, filter) pair. The result has
  `outcome == "prediction_unavailable"`, `rc == -1` (sentinel),
  `filter_type_id == null`, `errno == null`, `error == null`.
- The cross-check emits a `skipped` step with an error containing
  `"prediction_unavailable"`.
- The attempt slot runs a real `sysctl` / `read` attempt against
  `kern.osrelease` and reports the kernel denial as
  `attempt.outcome == "sysctl_failed"`.

## Success criteria

- `result.ok == true`.
- `runner_result.steps[0].sandbox_check.outcome == "prediction_unavailable"`.
- `runner_result.steps[0].sandbox_check.rc == -1`.
- `runner_result.steps[0].attempt.outcome == "sysctl_failed"` with
  `attempt.errno` set to EPERM or EACCES.
- `runner_result.steps[0].drift == null` because the prediction
  channel is deliberately unavailable for this op+filter pair.

## Fixtures

- Specimen generated inline using `kern.osrelease` (read-only,
  always present on macOS, safe to deny).

## Artifacts

- `tests/out/suites/runner_filter_sysctl_name/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_filter_sysctl_name
```
