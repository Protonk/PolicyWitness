# integration

Rust integration tests that exercise the CLI contract against a built app.

## Invariants

- Uses `dist/PolicyWitness.app/Contents/MacOS/policy-witness` to run specimens.
- Validates the controller envelope and runner result shape.
- Exercises instrumentation injection and duplicate protection.
- Test source lives at `controller/integration/cli_contract.rs`.

## Success criteria

- Integration test binary passes (`cargo test --tests`).

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`
- `tests/fixtures/pw_runner/specimen_instrumentation_debug_wait.json`
- `tests/fixtures/instrumentation/debug_wait.json`

## Artifacts

- `tests/out/suites/integration/cli.integration/artifacts/cargo-test-integration.log`

Run:

```
./tests/run.sh --suite integration
```
