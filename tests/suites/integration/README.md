# integration

Rust integration tests that exercise the CLI contract against a built app.

## Invariants

- Uses the resolved app/controller configuration from `tests/run.sh` to run specimens.
  Bundled `sbpl-check` comes from the same app.
- Validates the controller envelope and runner result shape.
- The denied file-read specimen reports `finished` at both run-summary levels
  and exit 0 while retaining `open_failed` and a permission-failure observation.
- Test source lives at `controller/integration/cli_contract.rs`.

## Success criteria

- The `integration/cli.integration` case passes; it runs `cargo test --test cli_contract`
  under the dispatcher against the resolved app.

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/integration/cli.integration/artifacts/cargo-test-integration.log`

Run:

```
./tests/run.sh --suite integration
```
