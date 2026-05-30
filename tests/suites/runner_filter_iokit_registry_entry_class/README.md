# runner_filter_iokit_registry_entry_class

Pins the contract for the `(iokit-open-service,
iokit_registry_entry_class)` pair: the runner accepts the filter in
specimens, deliberately skips the `sandbox_check` userland predicate
(which is empirically known to drift from kernel enforcement for this
op+filter, see
`tests/suites/witness_contract/harness/verify_filter_id.sh`), and
emits `outcome="prediction_unavailable"` with `rc=-1` (sentinel)
instead.

## What this suite does NOT cover

The attempt slot in this specimen is a benign file `open_read`
placeholder — there is no Channel A coverage of the
`iokit-open-service` operation today (the C probe-runner doesn't
implement iokit attempts yet). The suite asserts
`attempt.outcome != "unsupported"` so a regression to an
unsupported action would fail the suite loudly rather than silently
passing.

## Invariants

- `validateSandboxChecks` accepts `iokit_registry_entry_class` as a
  filter kind alongside `none`, `path`, `global_name`, `local_name`.
- `runSandboxCheck` short-circuits before calling `sandbox_check` for
  this (op, filter) pair. The result has
  `outcome == "prediction_unavailable"`, `rc == -1` (sentinel),
  `filter_type_id == null`, `errno == null`, `error == null`.
- The attempt portion of the step runs to completion with a supported
  action so the envelope shape is exercised.

## Success criteria

- `result.ok == true`.
- `runner_result.steps[0].sandbox_check.outcome == "prediction_unavailable"`.
- `runner_result.steps[0].sandbox_check.rc == -1`.
- `runner_result.steps[0].attempt.outcome` is not `"unsupported"` and
  `attempt.rc` is populated.

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
