# integration

Rust integration tests that exercise the CLI contract against a built app.

## Invariants

- Uses the resolved app/controller configuration from `tests/run.sh` to run specimens.
  Bundled `sbpl-check` comes from the same app.
- Validates the controller envelope and runner result shape.
- Test source lives at `controller/integration/cli_contract.rs`.

## Success criteria

- Integration test binary passes (`cargo test --test cli_contract`).

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`

## Artifacts

- `tests/out/suites/integration/cli.integration/artifacts/cargo-test-integration.log`

Run:

```
./tests/run.sh --suite integration
```
