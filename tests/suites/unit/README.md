# unit

Rust unit tests and formatting for the controller crate.

## Invariants

- `rust.unit` runs `cargo test --bins` only.
- `rust.fmt` runs `cargo fmt -- --check` and fails on any difference; fix with
  `cargo fmt` in `controller/`.
- Neither case requires a built `.app` bundle.

## Success criteria

- All unit tests pass (exit code 0) and the crate is rustfmt-clean.

## Fixtures

- None.

## Artifacts

- `tests/out/suites/unit/rust.unit/artifacts/cargo-test-bins.log`
- `tests/out/suites/unit/rust.fmt/artifacts/cargo-fmt-check.log`

Run:

```
./tests/run.sh --suite unit
```
