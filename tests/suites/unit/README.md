# unit

Rust unit tests and formatting for the controller crate.

## Invariants

- `rust.unit` runs `cargo test --bins`. Controlled orchestration checks count
  manifest loads and client calls through the real `run` path. The field-complete
  envelope is compared with `tests/fixtures/contract/envelope_shape.json`;
  helper binaries check their nested subtrees.
- `rust.fmt` runs `cargo fmt -- --check` and fails on any difference; fix with
  `cargo fmt` in `controller/`.
- `rust.disposition_reds` selects the four disposition record controller tests by
  their full names with `cargo test --bin policy-witness -- --include-ignored --exact`
  (B1's status-conflict report and E1's projection and withholding of the carried
  record). They also run inside `rust.unit`; this case keeps them individually
  selectable and classifies build, equipment and unrelated failures separately.
- `rust.byoxpc_reds` selects the two BYOXPC selection tests the same way (a required entitlement key present with value `false` is
  refused, naming the worker and the key); promoted from red.
- No case requires a built `.app` bundle.

`collector_states_preserve_the_serialized_execution_half` in
[run_flow.rs](../../../controller/src/run_flow.rs) runs production completion,
log attachment and serialization with eventful, empty and unrelated successful
captures, supported collection failures and disabled capture. After removing
only log-owned fields and the envelope timestamp, execution bytes and CLI status
must remain unchanged. It also checks correlation gating and diagnostic-event
retention, including disposition, withheld-comparison and absent-worker cases.
Supplied-text and window controls in
[log_replay_tests.rs](../../../controller/src/log_replay_tests.rs) carry production
output through the independent Python consumer; their
[fixture reference](../../fixtures/deny_capture/README.md) describes the inputs.

`exit_observation_does_not_replace_pipe_eof` in
[log_capture.rs](../../../controller/src/log_capture.rs) defers real pipe reads
until native exit observation, injects temporary unavailable/interrupted reads,
then requires the original bytes and EOF. A permanently unavailable read must
exhaust the original collection deadline and still establish child cleanup.

## Success criteria

- All unit tests pass (exit code 0) and the crate is rustfmt-clean.

## Fixtures

Current response captures and constructed reply helpers support disposition and
assembly tests. Phase collection controls distinguish wrong JSON types from
optional absence, withhold unsupported projections and retain the raw reply
through assembly. Empty spawn-failure objects exercise claim-validation scope;
the independent full consumer owns their required-field rejection.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/unit/rust.unit/artifacts/cargo-test-bins.log`
- `<run>/suites/unit/rust.fmt/artifacts/cargo-fmt-check.log`
- `<run>/suites/unit/rust.disposition_reds/artifacts/cargo-test-ignored.log`
- `<run>/suites/unit/rust.byoxpc_reds/artifacts/cargo-test-ignored.log`

Run:

```
./tests/run.sh --suite unit
```

`rust.observer_admission` selects the promoted observer marker regression by
exact name. The default Rust batch also carries rejected-frame and inner-version
receipts through real supervised pipes, assembly and independent consumers,
including outer timeout/overflow without semantic use of the rejected body.
