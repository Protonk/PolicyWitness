# Plain help: E1–E4 results

Record of sequence steps 1 and 2 of `PLAIN-HELP-PLAN.md`, made on 2026-11-15
from `2cb34aeb`. Everything here was observed on prototypes in scratch
worktrees under `.tmp/`, which are disposable; the patches in
[candidates/](candidates/) reproduce them. Nothing in this record is
implemented on `main`.

## Artifacts

| Candidate | Patch | Signed build | Lock packages | `policy-witness` bytes |
| --- | --- | --- | --- | --- |
| Baseline | none | 1447, `v0.3.7-113-g7cd93676-dirty` (the existing `dist` app) | 22 | 2,848,384 |
| Hand table | [hand-table.patch](candidates/hand-table.patch) over `2cb34aeb` | 1472, `v0.3.7-138-g06ce3801` | 22 | 2,849,264 |
| clap 4.6.7 | [clap-over-hand-table.patch](candidates/clap-over-hand-table.patch) | 1474, `v0.3.7-140-ga7612d9f` | 26 | 3,468,064 |
| Hand table with trycmd 1.2.1 and snapbox 1.2.2 as test dependencies | [e4-tools-over-hand-table.patch](candidates/e4-tools-over-hand-table.patch), lock file omitted | 1473, `v0.3.7-139-g0b726bcf` | 73 | 2,849,232 |

Build numbers and describes are of scratch commits that exist only in the
worktrees. Each signed build ran `make build` with the Developer ID identity;
[builds/](builds/) keeps each log's step, refusal and judgment lines. The
clap patch is the difference from the hand-table candidate: both share the
result-selection mechanism, the example projection, the card renderer's
layout, the inventory format, the contract join, the generator and the case
corpus. `controller/src/interface/result.rs` and `controller/src/run_result.rs`
are byte-identical in the two.

## Step 1: common elements

**Cards.** Both candidates produce these bytes, and the corpus states them
as literal expectations:

```text
run
example
result
```

```text
run
  --runner-mode
    standard
    byoxpc
```

```text
example
  initial-reads
    open_read /etc/hosts
    read_fresh /usr/share/dict/connectives
  restricted-read
    open_read /usr/share/dict/propernames
```

```text
result
  normalized_outcome ok exit_code
  bad_request false 1
  tool_error false 2
  missing_runner_client false 1
  unsupported_runner_client false 1
  malformed_runner_client false 1
  runner_reply_truncated false 1
  unsupported_runner_response false 1
  malformed_runner_response false 1
  xpc_error false 1
  xpc_timeout false 1
  xpc_acquisition_failed false 1
  xpc_submission_refused false 1
  xpc_protocol_error false 1
  runner_client_error false 1
  finished true 0
  runner_response_unavailable false 1
```

The `result` rendering is one candidate for the open decision; it has no
non-derived token. Each line is the three selected fields of the result that
`run`'s own constructor builds from the relation's selection, serialized.
The field names come from serializing `JsonResult` with one field changed
at a time. A condition is expressed by the outcome label the contract
already defines; the row for another admitted host label has no fixed label
and prints nothing.

**Typed references.** A card specification is a tree of enum values:
`Command::Run`, `RunOption::RunnerMode`, `Topic::Result`, a result-field
selector and so on. It holds no string that is printed. The renderer refuses
a child whose definition does not belong to its parent.

**Result relation.** Six rows in first-match order over a typed disposition:
local request refusal, tool failure, admission refusal (twelve enumerated
labels), admitted `finished`, admitted other label, admitted completion with
no host reply. `select` returns the label, `ok` and one exit status;
`envelope` takes that selection and nothing else, so the result's exit field
and the process status cannot be chosen separately. `print_escaped_tool_error`
returns the same selection's status to `cli.rs`.

**Inventory entry form.** `id`, `kind`, `reader` (path and symbol of the
consuming code), `spellings`, `relationships`, `cards`. The result relation
has its own section with rows (`inputs`, `outputs`, `order`), field names and
derived facts; the example has a section with the projected phases. Card
bytes and each card's references are in the inventory, so a card change is a
reviewed diff of a committed file.

**Cases.** One JSON corpus,
`controller/integration/interface_cases.json`, 64 cases: every row of the
help grammar table, the ordinary `run` inputs E1 names, both publishers, a
stdout without a reader, and `example` saved and submitted to `run`. Each
case states arguments (text or hex bytes), status, exact stdout or JSON
pointer values, and exact stderr or a stderr prefix. Against the baseline
build 1447, 34 of 64 fail; those 34 are the proposed behavior and are listed
in [corpus-on-baseline-build-1447.txt](candidates/corpus-on-baseline-build-1447.txt).

## E1: behavior

The hand-table build 1472 passes all 64 cases, including every help grammar
row. Its other differences from the baseline are the usage diagnostics, which
are an open decision: an unrecognized or missing command and `example` with an
argument print one line instead of `USAGE`.

On the clap build 1474, 19 cases fail
([corpus-on-clap-build-1474.txt](candidates/corpus-on-clap-build-1474.txt)).
Grouped:

| Input | Baseline and hand table | clap candidate | Constraint |
| --- | --- | --- | --- |
| `run x --help`, `run /r.json --bogus` | `tool_error`; dossier keeps `request_path` | `tool_error`; `request_path` null: clap returns no partial matches with an error | `argument_errors_are_reported_before_any_runner_or_specimen_work` fails |
| `run --timeout-ms=5` | refused, `unknown argument` | admitted | additional admitted form; no way to forbid `=` was found |
| `run --timeout-ms soon`, `--timeout-ms` | `invalid value for --timeout-ms` | clap wording, two different messages | diagnostic text only |
| `run --timeout-ms --help` | `invalid value for --timeout-ms` | `unknown argument: --help`: clap does not take a hyphen value | diagnostic text only |
| `run --runner-mode machme` | `--runner-mode machme is not supported; use --runner-mode byoxpc` | `invalid value 'machme' for '--runner-mode <runner_mode>'` | the [selection precedence rule](../../docs/CONTRACT.md#contract-request-options-precedence) says `machme` is refused, which holds; the specific text is lost unless a hand-written value parser replaces clap's |
| `run --runner-mode fast`, `--runner-mode` | existing texts | clap wording | diagnostic text only |
| `--help`, `-h`, no arguments, `bogus`, `HELP`, `result` | one-line diagnostic (candidate text) | clap's rendered error with a `Usage:` line, derived from the declaration | open decision either way |
| `example --help`, `example -h`, `example help` | one-line diagnostic | on build 1474, clap's own help text on stderr with exit 2 for the two flags | see the guard finding below |

Same in both: repeated options (last wins), repeated paths (last wins),
`run -- x` (ignored), `--timeout-ms 0` (raised to 1), non-UTF-8 path
(retained in the dossier as a lossy string), argument refusals before
app-root access, `kind: "run"` envelopes on stdout, and every help grammar
row once the clap candidate was restructured as described next.

**clap cannot take the tail.** The first clap prototype parsed the whole
argument vector, each command taking its tail as one trailing argument,
which the plan's appendix had found to accept every tail. That argument
consumes a leading `--`: `help -- run` printed the `run` card and
`run -- x` read `x` as the request path. The candidate was restructured so
that the first argument is compared directly with the names the declaration
holds, and clap parses only `run`'s tail and refuses `example`'s. In that
form top-level admission does not pass through `try_get_matches_from`.

**clap's help leaked through a command parsed on its own.** Disabling the
help flag on the root does not reach a command declaration that is parsed by
itself. On build 1474 `example --help` printed
`Usage: example … -h, --help  Print help`. The build-time guard as first
written walked only the root and missed it; the corpus caught it. The guard
now inspects every declaration the controller parses with, each as parsed,
and the declarations disable the flag.

**Admission kinds clap cannot express.** `Discards` and `Unenumerated` are
the same declaration (a trailing argument); what becomes of the tail is a
hand-written marker beside it. `Refuses always` for one value has no
declaration. clap's flag prefix and `--` terminator are properties of the
library, not declarations; the inventory builder states them by hand. A
long name is stored without its prefix, so the printed spelling is the first
word of clap's own display form of the argument. clap's `Debug` output for a
value parser differs between debug and release builds, which made the first
two signed clap builds stop at the stale-inventory check
([build-clap-1.txt](builds/build-clap-1.txt),
[build-clap-2.txt](builds/build-clap-2.txt)).

**Aliases through their readers.** `machme` is refused with its hint by
`run --runner-mode`, the request's `runner.mode` and `runner install --kind`,
and resolved to `byoxpc` by the registry reader; `debuggable` is unknown to
the first three and resolved by the registry reader. Unit tests state each
with literal expectations, and the corpus has the `run` cases. In both
candidates the vocabulary is one hand table with a rule per reader. The
registry's serde aliases are replaced by a `Deserialize` implementation that
asks the table.

**A second selection site.** `runner verify` chooses its outcome and exit
status from `admit_reply` on its own. It is in the unenumerated `runner`
tail and was left as it is; the relation governs `run` only.

## E2: build placement

**Chosen for both candidates: the definitions are the binary's own source
files, compiled a second time by `build.rs`.** `build.rs` declares the
modules by path (`src/interface/`, `src/example_document.rs`,
`src/json_contract.rs`, `src/run_result.rs`), renders the four cards and the
inventory into `OUT_DIR`, and compares the inventory with the committed
`controller/interface/inventory.json`. A difference stops Cargo, before
Meson, signing or packaging. The binary embeds the cards with `include_str!`
from `OUT_DIR`; nothing is rendered at invocation.

Observed:

- **Same placement, both candidates.** clap as a dependency and a build
  dependency compiled the declaration in both places with no change to the
  placement. clap's `string` feature was needed to build a command from a
  name read out of another declaration.
- **Source sharing.** The shared files may use only `std`, `serde`,
  `serde_json` and `crate::` paths to each other. `EXAMPLE_DOCUMENT` moved
  from `example.rs` to `example_document.rs`, because `example.rs` imports the
  request parser; three contract citations follow it. `RunnerKind` became the
  table's kind, so the contract's record importer needs one more admitted
  hand-written string projection beside `ReplyError`
  (`docs/contract/record_definitions.py`).
- **No signed app, no stamp.** `cargo check` with no build variables writes
  the cards and the inventory; the generator's write mode does exactly that
  in an isolated target directory.
- **Cargo provenance and reuse.** `serde` and `serde_json` as build
  dependencies add no lock package. Signed builds were admitted and judged
  as before: a changed source rebuilt both targets
  ([build-hand-2a.txt](builds/build-hand-2a.txt)), an unchanged tree reused
  both ([build-hand-2b.txt](builds/build-hand-2b.txt)), and
  `PW_FRESH_BUILD=1` rebuilt both ([build-hand-2c.txt](builds/build-hand-2c.txt)).
  `build.rs` declares the committed inventory and the refresh variable as
  rerun inputs; a change to an included source recompiles the script.
- **A stale card cannot ship.** The cards are rendered in the build that
  embeds them. In all ten mutations that changed a definition (eight on the hand table,
  two on clap), the first build stopped at the stale inventory. Two signed clap builds stopped there
  too, before signing.
- **Cost.** Signed builds took 25 to 45 seconds here, with or without the
  change.

Alternatives, not tried further:

- **A shared dependency and build-dependency crate.** It would add a path
  package to the lock file, a directory to the build contract's inputs and
  to the Cargo provenance checks. The by-path modules needed none of that.
- **Compile-time assembly.** The example projection parses JSON and the
  result card serializes a record; neither is practical in `const` code.
- **A registered generator as the only owner.** A Python generator cannot
  read Rust definitions without running Rust. It remains the owner of the
  committed copies and the baseline, and obtains the inventory by running
  the build script.

One point for the generator contract: `generate_interface.py --check`
checks the committed copies offline and does not run Cargo, so a stale
inventory is refused by the build script in the same build, not by
`--check` alone. G3 as written asks `--check` to refuse any stale copy.

## E3: linkage controls

The harness [mutate.py](e3/mutate.py) applied each mutation, built,
regenerated a stale inventory with the generator, and ran every check;
[observed-hand-table.json](e3/observed-hand-table.json) and
[observed-clap.json](e3/observed-clap.json) hold the patches, messages and
timings. Checks ran against unsigned builds placed in a scratch app
directory; no signed execution was added. Cost per check, both candidates:
build 0.2–2.1 s, literal scan 0.2 s, contract check 0.4–4.6 s, corpus and
card-versus-execution test 0.3–1.0 s, unit tests 2.0–2.6 s after
compilation.

The common procedure, same result in both candidates:

| Step | Mutation | First build | After regeneration |
| --- | --- | --- | --- |
| 2 | Rename `--runner-mode` to `--runner-kind` in the governing source | stops: stale inventory | `run` card changes; `--runner-kind standard` admitted, `--runner-mode standard` refused as unknown; corpus cases for the old spelling and the old card fail; contract check unchanged |
| 3 | Render the option from a private identical copy in the card renderer | builds; card and behavior unchanged; corpus, contract and unit checks pass | the literal scan refuses: `the card renderer spells a card element itself: "--runner-mode"` |
| 4 | Step 3's copy, then step 2's rename | stops: stale inventory | the generator refuses: `card run: token '--runner-mode' comes from no referenced entry`; no inventory is written and the build stays stopped |

Further controls:

| Control | Hand table | clap |
| --- | --- | --- |
| Remove the referenced `RunnerMode` definition | compile error in the build script | compile error in the build script |
| Invalid relationship: another option's words under `--runner-mode` | build stops: `TimeoutMs does not take a runner-kind word` | build stops: `TimeoutMs lists no values` |
| Flag-shaped topic address `--result` | build stops: `topic Result has an empty or flag-shaped address` | same |
| Literal `--help` comparison in `parse_arguments` | literal scan refuses; `run.help_flag` cases fail | same |
| Restored `--help` arm in `cli::run` | literal scan refuses; `top.help_flag` fails with status 0 | literal scan refuses; the corpus case was already failing on diagnostic text, so only the probe shows status 0 |
| Built-in help flag left enabled | not applicable | build stops: `help declares a help flag; …` for all six commands |
| Built-in help subcommand left enabled | not applicable | debug build: clap's own assertion, `command name help is duplicated`; the guard also checks the setting |

Hand table only, on the shared mechanism:

| Control | Observation |
| --- | --- |
| Example field: first attempt target to `/etc/services` | stale inventory; then the `example` card and the emitted specimen change together (the card-versus-execution test passes, the literal card cases fail); the contract check refuses a stale `CONTRACT.md` and `public.json` |
| Result rule: tool-failure exit 2 to 3 | stale inventory; then `run --bogus` exits 3 with `result.exit_code` 3 and the card says `tool_error false 3`; the contract check refuses `set_value(envelope.result.exit_code, 2) disagrees with result.tool_failure, whose exit_code is 3`; 23 corpus cases and five unit tests with literal expectations fail |
| Private copy of that row's exit status in the renderer | builds, everything passes, and no check refuses the unchanged copy: the literal scan sees strings only |
| That copy, then the rule change | the generator refuses: `card result: token '2' comes from no referenced entry` |
| Rename the identity `AdmittedFinished` and update the citing contract node | stale inventory; then contract check passes, `public.json` byte-identical, cards unchanged |
| Admission condition or row order changed in the source | build stops in card validation, before any contract check: `AdmittedFinished does not select its own disposition` |
| The same two changes, and a changed label, `ok` value and removed row, made in the inventory | the contract check refuses each, naming the node, the fact and the entry |
| Tail rule of `version` from Discards to RefusesAny | the generator refuses the new residue member although the totals are unchanged; with `--refresh-residue` it writes; `version --help` then exits 2 |
| Remove the registry's `debuggable` alias | the generator's write mode accepts the reduction and rewrites the baseline; two registry unit tests fail |

**Independent result cases.** The unit test
`each_result_class_agrees_in_fields_process_status_and_card` drives sixteen
dispositions through production orchestration with controlled dependencies
and literal expectations: each class, a delivery failure and three admission
refusals beside a decoded `finished` reply, and admitted `finished` replies
with a failed attempt and with integrity findings, which stay `true`/0. It
compares the envelope's three fields, the returned process status and the
stored card's line.

**What the contract join compared.** Four nodes have every structured fact
compared: both outcomes of the
[controller pre-invocation refusal](../../docs/CONTRACT.md#contract-refusals-controller-consequence)
and both cases of the envelope's result selection, including the inherited
`ok` effect, the inherited `present(...)` applicability and the case order.
The runner-mode rule and the example emission resolve their identifiers and
have nothing structured to compare: their content is prose and one
`free.effect`. The rename in step 2 therefore leaves the contract check
unchanged while the contract's prose still says `--runner-mode`.

**Operand bindings were needed.** `normalized_outcome` names both a result
field and the host reply's label, so the join binds two operand roots by
name: `envelope.result.` and `envelope.data.runner_result`.

**Derived facts the builder computed by evaluating `select`.**

- `ok` is a function of `exit_code` and of `normalized_outcome`.
- `exit_code` is not a function of `normalized_outcome`: an admitted host
  reply labelled `tool_error` selects exit 1, a controller tool failure
  exit 2. The card's line `tool_error false 2` is the controller's row.
- Three row pairs share outputs: local request refusal and an admitted host
  `bad_request`; an admission refusal and an admitted host reply using a
  refusal label; the no-host-reply row and an admitted host reply labelled
  `runner_response_unavailable`.
- The count of integrity issues is passed to `select` and changes no output.

## E4: execution tools

One corpus, three executors, one signed controller (build 1473), run through
`tests/run.sh --suite integration`
([dispatcher-integration-on-build-1473.txt](e4/dispatcher-integration-on-build-1473.txt)).

| | `std::process` | snapbox | trycmd |
| --- | --- | --- | --- |
| Cases held | 64 of 64 | 63; a stdout without a reader has no form | 60; no form for the two non-UTF-8 arguments, the stdout without a reader, and the two-step case |
| Result | all pass | all pass | 41 pass; 19 JSON-pointer cases fail in the adapter's translation to line patterns |
| Exact status, stdout, stderr | yes | yes, with `raw()` data; unmarked text is a pattern | status yes; text is always a pattern |
| Wrong-status and wrong-stream controls | rejected | rejected | rejected |
| Unstated stderr | the executor refuses a step that states neither form | must be stated by the caller | passes: with `stderr` removed, a case whose command wrote to stderr passed. The adapter always writes it |
| `TRYCMD` set | not applicable | not applicable | the adapter refuses to run |
| JSON pointer equality | native | by hand beside the assertion | none; the line patterns lose the pointer's path |
| Added lock packages | 0 | with trycmd, 51 | with snapbox, 51 |

- **The 19 trycmd failures are not isolated.** The same expectations hold
  under the other two executors. A direct snapbox probe of the same pattern
  shape matched, so the cause is in how trycmd applies the pattern to these
  documents. Pointer equality has no faithful rendering there in any case.
- **Dispatcher compatibility.** All three wrote only to temporary
  directories and the suite's log. trycmd runs its cases in parallel
  internally. Under the suite's parallel tests, the `std::process` control
  test failed once because it shared a scratch directory name with the
  corpus test; the name needs a per-call component.
- **Corpus reuse.** The execution checks read the corpus. The inventory
  generator reads it for the case join. [corpus_readers.py](corpus_readers.py)
  reads the save-and-submit case for documentation and in card layout, and
  shows the limit: a case holds argument vectors and a saved-output name. The
  program name and the `>` are added by the reader.
- **Association.** With the neutral corpus, argument vectors and required
  result fields are data, so the entries a case reaches are derived for all
  three executors: commands, topics, tails, `run` tokens, runner-mode words
  and, from the three required result fields, a result row. Without it, a
  trycmd case gives arguments but only text patterns for results, and
  snapbox or `std::process` assertions written as code give nothing to read.
  Derivation is impossible for a result whose outputs two rows share; no
  corpus case hits one today. The registry and request-selector readers
  are reached by unit tests, not by CLI cases, and are reported as entries no
  case reaches.
- **Embedding an observed result.** A binary that embeds the result of
  running itself needs two builds or a build that executes its own output.
  `build.sh` executes no controller it built, and the embedded bytes would
  enter the build contract that the run reports. The observation would also
  be of the unsigned first build, on the build machine, at build time. No
  such stage was added.

## Remaining hand-written adaptation and cost

| | Hand table | clap |
| --- | --- | --- |
| Governing definitions | five `std`-only files, 562 lines | declarations for commands and `run`, plus the same vocabulary and result files |
| Top-level admission | the table | comparison with the declaration's names; clap parses `run`'s tail |
| Kinds stated by hand | none | Discards, Unenumerated, Refuses always, the flag prefix and terminator |
| Diagnostics | existing texts built from the tables' spellings | clap's for values and usage; one mapped by error kind |
| Behavior changes beyond the help grammar | none | `--timeout-ms=5` admitted, lost partial path, changed texts |
| Guard against the library's help | not applicable | needed, and the first version was wrong |
| Shipped dependencies | none added | clap, clap_builder, clap_lex, anstyle; +618,800 bytes |
| Existing unit tests | pass with updated seams | one fails on the lost partial path |

## Known gaps in the prototypes

- `check_cli_surface_agreement`, the README block, the `cli_rs`, `D24` and
  `D30` records and the integration test that expects `usage:` are not
  updated. Through the dispatcher on build 1472, the hand-table candidate's
  249 unit tests pass, `unit/rust.fmt` fails because the prototype sources
  are not formatted, and the integration suite fails on two tests: the
  `usage:` expectation and the executor control's scratch-directory name.
- The generator is not registered, has no README and no expansion refresh
  path; the literal scan is a standalone script, not a drift rule.
- `docs/build.json` does not describe the build script's new work.
- Help in absent-prerequisite states and on a copy outside the bundle was not
  run.
- Failed attempts are not an input to `select`. The controller has no
  failed-attempt classifier at that point, and adding one would create an
  interpretation that selection then ignores. The unit test covers a
  `finished` reply with a failed attempt.
