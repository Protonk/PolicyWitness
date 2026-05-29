# runner_filter_iokit_registry_entry_class

Pins the contract for the `iokit_registry_entry_class` filter kind on
`iokit-open-service`: the runner accepts the filter in specimens,
deliberately skips the `sandbox_check` userland predicate (which is
empirically known to drift from kernel enforcement for this op+filter,
see `tests/suites/witness_contract/harness/verify_filter_id.sh`), and
emits `outcome="prediction_unavailable"` instead. The attempt still
runs through channel A. The cross-check mirrors the same signal.

## Invariants

- `validateSandboxChecks` accepts `iokit_registry_entry_class` as a
  filter kind alongside `none`, `path`, `global_name`, `local_name`.
- `runSandboxCheck` short-circuits before calling `sandbox_check` for
  this filter kind. The result has
  `outcome == "prediction_unavailable"`, `filter_type_id == null`,
  `errno == null`, `error == null`.
- The cross-check (`--sonoma-cross-check`) emits a `skipped` step
  whose `error` includes the string `prediction_unavailable`.
- The attempt portion of the step runs unchanged — channel A remains
  the reliable evidence for any iokit-open-service probe.

## Success criteria

- `result.ok == true`.
- `runner_result.steps[0].sandbox_check.outcome == "prediction_unavailable"`.
- `runner_result.steps[0].attempt.rc` is populated.
- `sonoma_cross_check.steps[0].status == "skipped"` with an error
  message containing `"prediction_unavailable"`.

## Fixtures

- Specimen generated inline by `run.sh` using IOSurfaceRoot as the
  iokit class (the discriminator confirmed openable on Apple Silicon
  during verify_filter_id discovery).

## Artifacts

- `tests/out/suites/runner_filter_iokit_registry_entry_class/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_filter_iokit_registry_entry_class
```
