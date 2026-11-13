# integration

Rust integration tests that exercise the CLI contract against a built app.

## Invariants

- Uses the resolved app/controller configuration from `tests/run.sh` to run specimens.
  Bundled `sbpl-check` comes from the same app.
- Validates the controller envelope and runner result shape.
- The denied file-read specimen reports `finished` at both run-summary levels
  and exit 0 while retaining `open_failed` and a permission-failure observation.
- `example` on the resolved app exits 0 with empty stderr and prints one JSON
  object and one newline carrying the app's `PWContract`; two emissions are
  byte-identical, and every argument is exit 2 with usage and empty stdout.
- `example` whose stdout is a pipe with no reader exits 2 without a panic,
  whether or not stderr can be written; the reason reaches stderr when that
  stream is writable. An argument refused beside an unwritable or closed
  stderr is still exit 2, and a closed stderr beside a writable stdout still
  exits 0 with the complete document.
- Isolated Cargo builds without an identity print nothing for `example` and
  exit 2. Builds given another identity emit it, and the resolved app's `run`
  refuses each emitted document with `unsupported_contract`, its own expected
  identity and no client capture.
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
