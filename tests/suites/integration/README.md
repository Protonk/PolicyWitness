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
- With `HOME` and the registry location supplied to the child: a registry
  path with no entry lists and reconciles as empty, reports a lookup miss in
  its own envelope and creates nothing. The same recorded registry is read
  while its directory can be searched; under a directory that cannot be
  searched, below a file, as an unreadable file and as a symlink to a missing
  target, `runner list`, `reconcile`, `status` and `verify` exit 2 with an
  empty stdout and one stderr line naming the path and the system error, and
  `run` with an external selector returns `tool_error` with that text and no
  client capture. `validate` and `remove` under the unsearchable directory are
  refused at the lock, and `validate` leaves the symlink in place.
- A completed `runner list`, `reconcile` or `validate` reports `ok`, true and
  exit 0; a usage or argument refusal of a runner command writes its reason
  to stderr, prints no envelope, exits 2 and creates no registry. Of the three
  completed commands only `validate` creates the registry directory and file.
- `--version`, `version`, `run` and `test-input run` on a missing request,
  `runner list`, `reconcile` and `status`, and `sbpl-check` with `--help` and
  with a request on stdin, each given a stdout pipe with no reader, exit 2
  with exactly one line on stderr, and exit 2 when stderr has no reader
  either. With stdout closed at launch the same commands keep their own
  status and write nothing to stderr: the process then holds a descriptor
  that discards what it is given. `sbpl-check` without arguments and with a
  stderr that cannot be written exits 2 with an empty stdout.
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
