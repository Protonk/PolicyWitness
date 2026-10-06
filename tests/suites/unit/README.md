# unit

Rust unit tests and formatting for the controller crate.

## Invariants

- `rust.unit` runs `cargo test --bins` only.
- `rust.fmt` runs `cargo fmt -- --check` and fails on any difference; fix with
  `cargo fmt` in `controller/`.
- `rust.disposition_reds` selects the four disposition record controller tests by
  their full names with `cargo test --bin policy-witness -- --include-ignored --exact`
  (B1's status-conflict report and E1's projection and withholding of the carried
  record). They also run inside `rust.unit`; this case keeps them individually
  selectable and classifies build, equipment and unrelated failures separately.
- No case requires a built `.app` bundle.

## Success criteria

- All unit tests pass (exit code 0) and the crate is rustfmt-clean.

## Fixtures

- None.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/unit/rust.unit/artifacts/cargo-test-bins.log`
- `<run>/suites/unit/rust.fmt/artifacts/cargo-fmt-check.log`
- `<run>/suites/unit/rust.disposition_reds/artifacts/cargo-test-ignored.log`

Run:

```
./tests/run.sh --suite unit
```

`rust.observer_admission` selects the promoted observer marker regression by
exact name. The default Rust batch also carries rejected-frame and inner-version
receipts through real supervised pipes, assembly and independent consumers,
including outer timeout/overflow without semantic use of the rejected body.
