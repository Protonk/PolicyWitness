# runner_filter_iokit_user_client_class

Same contract as `runner_filter_iokit_registry_entry_class` and
`runner_filter_sysctl_name`, applied to the `iokit_user_client_class`
filter on `iokit-open-user-client`. Empirically verified
2026-05-29 with `verify_filter_id.sh iokit_open_user_client
iokit-user-client-class IOSurfaceRootUserClient --probe-target
IOSurfaceRoot`: kernel enforces the deny but no `sandbox_check`
filter ID in 1..200 produces a verdict matching the kernel. The
runner accepts the filter, short-circuits `sandbox_check`, and emits
`step.sandbox_check.outcome="prediction_unavailable"` with
`step.sandbox_check.rc==-1` (sentinel — see PolicyWitness.md).

Operation note: IOServiceOpen triggers two SBPL operations,
`iokit-open-service` (matched by `iokit-registry-entry-class`) and
`iokit-open-user-client` (matched by `iokit-user-client-class`). The
prediction_unavailable contract is keyed on the (op, filter) pair, so
this suite uses the correct second operation.

The two IOKit-filter suites together document that the
prediction_unavailable contract covers both registry-entry-class
matching (filtering on the IOService class hierarchy) and
user-client-class matching (filtering on which user-client subclass
the open creates).

## Success criteria

- `result.ok == true`.
- `runner_result.steps[0].sandbox_check.outcome == "prediction_unavailable"`.
- `runner_result.steps[0].sandbox_check.rc == -1` (sentinel that
  disambiguates "no prediction" from rc=0 "allow").
- `runner_result.steps[0].attempt.rc` is populated.
- `sonoma_cross_check.steps[0].status == "skipped"` with an error
  containing `"prediction_unavailable"`.

## Fixtures

- Specimen generated inline using `IOSurfaceRootUserClient` as the
  user-client class (the conventional user-client name IOSurfaceRoot
  exposes for connect-type=0).

## Artifacts

- `tests/out/suites/runner_filter_iokit_user_client_class/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_filter_iokit_user_client_class
```
