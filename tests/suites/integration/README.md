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
  byte-identical, and every argument is exit 2 with one line on stderr and an
  empty stdout.
- `version` equals `--version` apart from its timestamp, and either with any
  argument is exit 2 with an empty stdout.
- Every case of the [interface corpus](../../../controller/integration/interface_cases.json)
  holds on the resolved app: exact status, exact stdout or the stated JSON
  pointer values, and exact stderr or its stated prefix. The corpus covers
  each help card and address form, `--help` and `-h` refused at the top level
  and after every command, `run`'s argument refusals, runner-kind words through
  the option, a request file and `runner install`, an option word that differs
  from the request file's nested mode, both publishers, a help
  card written to a stdout without a reader, and `example` saved and submitted
  to `run`. For `test-input run` it covers each test control admitted with a
  value outside the control's own range, the refusals of a missing value, a
  value of another form, a repeated control and an unknown flag, `run`'s own
  options and refusals under that form, a control flag refused by `run`, a
  request refused by its selector before any client call, and the published
  read input submitted with a control, with none, with a validator path that
  does not exist, whose dossier record and spawn failure name it, and through
  `run`. Its executor rejects a wrong status and output on the wrong
  stream, and refuses a step that states no stderr expectation.
- What each help card shows is what the same binary does: every base-card line
  addresses a card headed by that line, every option and word on the `run`
  card passes argument admission, and the `example` card's lines are the
  phases and attempts of the emitted specimen.
- Help printed by the Cargo-built binary, which has no bundle around it, with
  no `HOME`, an absent or unwritable `HOME`, an absent registry and malformed
  or non-UTF-8 tails, is byte-identical to the bundled binary's, with status 0
  and an empty stderr. The system does not run a copy of the bundle's signed
  executable outside its bundle, so that copy is not the specimen.
- In a copy of the controller package, a changed interface definition and a
  changed committed inventory each stop the build script before the binary
  compiles, naming the stale copy and the command that regenerates it. An option
  without runner-kind words and a topic naming another command are rejected
  by the card renderer before the freshness comparison.
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
