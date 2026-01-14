# unit

Rust unit tests for the controller binaries.

## Invariants

- Runs `cargo test --bins` only.
- Does not require a built `.app` bundle.

## Success criteria

- All unit tests pass (exit code 0).

## Fixtures

- None.

## Artifacts

- `tests/out/suites/unit/rust.unit/artifacts/cargo-test-bins.log`

Run:

```
./tests/run.sh --suite unit
```
