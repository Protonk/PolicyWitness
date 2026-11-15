# Generate `policy-witness help` cards from the executable interface

Status: proposed. Nothing here is implemented. The findings were taken from
source at `60e98ee5` and from `dist/PolicyWitness.app` build 1447. That build
describes itself as `7cd93676-dirty`, so its exact source is not recoverable
from a commit; the behavior observed on it agrees with the argument handling
read at `60e98ee5`. The crate observations come from a throwaway Cargo package
outside the checkout, which was not retained; each one states the version it
was made on and is cheap to repeat.

The plan has four kinds of statement and keeps them apart:
[settled requirements](#settled-requirements) the maintainer has decided,
[current findings](#current-findings) observed in this tree,
[experiments](#experiments) that have not been run, and
[open decisions](#open-decisions) that review and, where needed, experiments
inform and the maintainer makes. An executor should not promote an item
from one kind to another without the evidence the plan names for it. The
remaining sections
(the provisional cards, recognition proposal, connection evidence, sequence,
verification and consequences) are this plan's proposal and can be revised
by review and by what the experiments show.

## Problem

`policy-witness` prints hand-written usage texts: `USAGE` in
[cli.rs](controller/src/cli.rs), `runner_usage` in
[runner_commands.rs](controller/src/runner_commands.rs), and a one-line form
in [test_input.rs](controller/src/test_input.rs). Nothing connects any of
them to the argument handling beside it. A drift check compares the usage
lines of `USAGE` with a block in the controller README, which establishes
that two authored texts agree with each other, not that either agrees with
the parser.

The help invocations themselves are not safe to make carelessly. Top-level
help writes to stderr, the `runner` form writes to stdout, several
help-shaped invocations are usage failures with exit 2, one of them runs the
`run` preparation path, and an unwritable stream ends the process with a
panic and exit 101. An agent or a CI script that adds `help` to a command
line can fail a job or bury a card in the error stream.

## Intended result

`policy-witness help` selects and prints short cards on stdout. A card
carries no explanatory sentences. Its contents are a projection of the
executable interface, assembled and verified while the product is built, and
delivered at invocation without consulting operational state. An invocation
recognized as help exits 0 whatever else is on its command line.

The strictness is deliberate. Cards that can only say what the interface
mechanically supports make the interface's unstated rules visible, and that
is meant to be usable later as a forcing function on the interface. This
plan preserves that use and does not require acting on it.

## Settled requirements

These are the maintainer's decisions. They are not reopened by this plan.

1. **Bare card output.** Help selects and prints simple cards: specific
   information for recognized subjects and a bare fallback for anything
   unrecognized. Selection stays deliberately limited. An incidental help
   invocation adds text to a CI log and causes no usage failure.
2. **No operational prerequisites.** Once an invocation is recognized as
   help, malformed arguments trigger no operational work, no stderr
   diagnostic and no failing usage status. Help does not depend on a valid
   specimen, an available runner, a writable records directory or a working
   execution configuration. It writes to stdout. The promise concerns
   help-input failures. It does not cover an unwritable stdout or external
   termination of the process.
3. **Mechanical linkage.** Card contents come from code that actually
   governs the interface, or from executions connected to it. Independently
   authored help prose that is merely checked against citations, examples or
   snapshots does not qualify, and neither does the same prose moved into
   constants, attributes, templates or generator code. The aim is no
   exceptions. A proposed exception must be extremely narrow, explicit and
   justified as a departure.
4. **Build-time construction and verification.** Help delivers the assembled
   result without discovering or validating operational state at invocation.
   Execution, test fixtures and help must agree, and the mechanism for that
   agreement is not decided here. A declared obligation or guarantee stays
   distinguishable from something observed in an example.

**Editorial responsibility.** Refusing authored text leaves selection and
arrangement as deliberate editorial acts. Each proposed card element, and
each later addition, is examined on two grounds: its use to a reader, and
whether it makes PolicyWitness's functioning clearer. Mechanical
availability does not justify inclusion. The examination also asks whether
selecting the element exposes an implicit rule, an unclear obligation, or an
observable whose status has not been stated.

## Where this stops

- The plan does not mandate a general refactor of the command-line
  interface or generated documentation beyond the cards. A parser change is
  justified here only by a card element that needs its governing code to be
  the code the card is built from. How much such change precedes the first
  implementation is an [open decision](#open-decisions), and its answer may
  be small or large.
- `sbpl-check` has its own usage text in
  [sbpl-check.rs](controller/src/bin/sbpl-check.rs) and is outside this plan.
- The public contract's authored definitions remain the owner of public
  meanings. Cards do not replace them, and this plan does not assume cards
  may quote them: sentences taken from the contract are authored prose, so
  using them would be an exception under requirement 3 for the maintainer to
  decide.
- No release, notarization or publication step.

## Current findings

### What help-shaped invocations do today

Observed on build 1447, stdin at `/dev/null`:

| Invocation | Exit | stdout | stderr |
| --- | --- | --- | --- |
| `help`, `--help`, `-h`, `help run`, `help bogus --x` | 0 | empty | `USAGE` |
| `run --help`, `run -h`, `run x --help` | 0 | empty | `USAGE` |
| `runner help`, `runner --help` | 0 | `runner_usage` | empty |
| no arguments, `bogus`, `HELP` | 2 | empty | `USAGE` |
| `example --help`, `example help` | 2 | empty | `USAGE` |
| `test-input --help`, `test-input help` | 2 | empty | one-line reason |
| `runner install --help`, `runner status --help` | 2 | empty | `unknown argument: --help` |
| `runner reconcile --help` | 2 | empty | `runner reconcile accepts no arguments` |
| `run --timeout-ms --help` | 2 | `tool_error` run envelope | empty |
| `run help` | 2 | `tool_error` run envelope, `request.json not found: help` | empty |

Further observations:

- The first argument alone selects top-level help, so every argument after
  `help` is already ignored.
- `run` collects host facts through `sysctlbyname` before it looks at its
  arguments, and recognizes `-h`/`--help` only if no earlier argument has
  already produced an argument error.
- `run help` treats `help` as the request path. It resolves the app root,
  loads the evidence manifest and prints an envelope whose dossier includes
  host facts and app provenance. A file named `help` is a legal request
  path, so this form cannot become help without changing `run`'s grammar.
- By source, not by execution: `cmd_runner` passes no arguments to
  `runner list` or `runner validate`, so `runner list --help` lists the
  registry and `runner validate --help` takes the registry lock and
  validates.
- With stderr attached to a pipe that has no reader, `help`, `run --help`
  and `bogus` exit 101. `runner help` with such a stdout exits 101 and
  prints a Rust panic message. `print_usage` uses `eprintln!` and the runner
  form uses `println!`. `example` and `test-input` already use the other
  pattern: `write_all`, `flush`, exit 2 on failure, no panic.

### Authored text and what checks it

- `USAGE` is used for help, for the bare and unknown-command failures and
  for `example`'s usage refusal. Its `notes:` block is prose that restates
  promises the contract owns.
- [check_cli_surface_agreement](tests/suites/source_drift/check.py) parses
  `usage: ... notes:` out of `cli.rs` by regular expression and compares the
  `policy-witness` lines with the fenced block under "CLI surface
  (contract)" in the [controller README](controller/README.md). The
  architecture account records this as dependencies `D24` and `D30` and the
  `cli_rs` node in [architecture.json](docs/architecture.json), and
  [controller/AGENTS.md](controller/AGENTS.md) tells contributors to keep
  the two synchronized.
- `runner_usage` has no check of any kind.
- The contract does not mention help. It does state that `example` refuses
  every argument with exit 2
  ([emission rule](docs/CONTRACT.md#contract-request-specimen-emit_example))
  and that `test-input` usage failures exit 2
  ([publication rule](docs/CONTRACT.md#contract-request-specimen-emit_test_input)).
  In [cli_contract.rs](controller/integration/cli_contract.rs),
  `example_prints_one_request_and_refuses_every_argument` pins
  `example --help` and `example -h` to exit 2 and pins top-level `--help` to
  exit 0 with the usage on **stderr**, and
  `test_input_cli_refusals_and_write_failures_exit_2_safely` pins that
  command's usage refusals.
- `refusals_before_selection_load_at_most_once_and_never_invoke_the_client`
  in [run_flow.rs](controller/src/run_flow.rs) pins `run --help` to a help
  result with no manifest load and no client call. Its `observe` seam counts
  manifest loads and client calls only. The app root is not counted and
  host-fact collection is not injected, so the assertion passes today while
  `run --help` collects host facts.

### What governs the interface today

Every command parses by hand: `cli::run` matches the first argument,
`parse_arguments` in `run_flow.rs` and the four `cmd_runner_*` loops match
flag strings, `test_input::render_template` matches a fixed three-argument
shape, and `example::emit` requires no arguments. There is no declaration
that could be enumerated, so today nothing can list "the flags `run`
accepts" except a reader of the match arms.

Some values do have a single governing definition: `RunnerKind::parse` and
`RunnerScope::parse` for their vocabularies, `DEFAULT_TIMEOUT_MS` and
`RUNNER_VERIFY_DEFAULT_TIMEOUT_MS` for defaults, `EXAMPLE_DOCUMENT` for the
example specimen (already extracted by the contract generator), and
`test_inputs/read.json` with its `TARGETS` positions for the developer
input. The `run` exit statuses have no such definition. They arise at many
sites in `run_flow.rs` and their meanings are stated in an authored README
table and in the contract.

Looking at candidate elements already exposes rules the usage texts do not
state. These are examples of what the editorial examination is for, not a
card inventory:

- `runner install` matches `--executable` and `--bundle-id`, takes a value
  for each, and then always refuses them. A card built from "the flags the
  parser matches" would list two flags that cannot succeed.
- `--timeout-ms 0` becomes 1. `--runner-mode machme` has its own refusal
  text. In `run`, the last non-flag argument wins as the request path and
  `--` stops argument processing.
- `help` and `version` are accepted first arguments that `USAGE` does not
  list.

### Build and test constraints that bear on the mechanism

- `build.sh` builds the controller once with `cargo build --release` for the
  pinned triple, before Meson, signing and any test. No stage of `build.sh`
  executes the controller it built; the pre-signing identity step consults
  the built worker only. The signed app's controller is first executed by
  the tests.
- [build.rs](controller/build.rs) exists, refuses any target but
  `aarch64-apple-darwin` and declares the build-stamp variables.
  `PW_BUILD_CONTRACT` is computed from the contract sources before Cargo
  runs, and a plain Cargo build is `unbound`.
- The controller depends on `serde`, `serde_json`, `sha2` and `libc` only.
  `controller/Cargo.lock` is a tracked build input
  (`SOURCE_INPUTS` in [build_provenance.py](tests/lib/build_provenance.py)),
  the build admits Cargo's directories and judges its reuse reports, and
  [DEPENDENCIES.md](docs/DEPENDENCIES.md) accounts for what a build needs.
  A dependency in any section of `Cargo.toml` changes the lock file.
- The unit suite runs `cargo test --bins`. The integration suite runs
  `cargo test --test cli_contract`. Most of its tests execute the signed
  app's binary, located through the dispatcher's resolved configuration; a
  few execute Cargo-built copies to show what an unbound or differently
  bound build does.
- Generated copies in this repository are owned by registered generators
  with a `--check` mode that runs before signing
  ([generator contracts](tests/suites/source_drift/README.md#generator-contracts)).
  A card generator outside Cargo would join that regime. One inside Cargo
  would fall under the Cargo provenance checks instead.

### clap 4.6.7: observed capabilities

Observed with `default-features = false` and features `std`, `help`,
`usage`, `error-context`, which add `clap_builder`, `clap_lex` and `anstyle`
to the shipped dependency tree. Its declared minimum Rust is 1.85; the
controller's is 1.89.

- A `Command` can be read back after `build()`: subcommand names, and for
  each argument its id, long name, required flag, value names, possible
  values, default values and arity.
- `render_usage` and `render_help` produce text from the declaration alone.
  With no `about` or `help` strings set, `render_help` for a `run`-shaped
  command printed the usage line, the positional, and each option with
  `[default: 240000]` or `[possible values: standard, byoxpc]`.
  `help_template` selects and orders the generated sections.
- The same declaration file compiled into the binary and into `build.rs`
  through `include!`, with clap as a build dependency, rendered text into
  `OUT_DIR` that the binary embedded with `include_str!`. The included file
  must then compile on its own, which limits what the declaration can refer
  to.
- `try_get_matches_from` returns errors as values with `kind()`,
  `exit_code()` and `use_stderr()`, so the caller decides what is printed
  and where. Arguments can be taken as `OsString`.
- A subcommand declared with one trailing, hyphen-accepting, `OsString`
  argument matched every tail tried, including `--x`, `-- --help` and a
  non-UTF-8 argument.

Observed limits:

- clap's built-in help subcommand and flag do not meet requirements 1
  and 2. `help bogus` is `InvalidSubcommand`, exit 2, on stderr.
  `run --timeout-ms --help` is `InvalidValue`, exit 2. The catch-all
  subcommand above is the only configuration observed to accept every tail,
  so recognition cannot be left to clap's defaults.
- The rendered text contains words clap supplies (`Usage:`, `[OPTIONS]`,
  `Options:`, `Arguments:`, `[default: ...]`, `[possible values: ...]`).
  `render_usage` collapses options into `[OPTIONS]`.
- Value names such as `<request.json>` and argument ids are labels an author
  types into the declaration. Changing one changes no behavior.
- A clap parser is not behavior-neutral. In the probe it accepted
  `--timeout-ms=5` and reported `machme` with clap's own wording. The
  current parser refuses the first and has a specific message for the
  second.

The consequential point for PolicyWitness: a `Command` declared only so that
cards can be rendered from it is a second authored description of the
interface. clap connects cards to behavior only where the same declaration
is the parser that admits the arguments.

### trycmd 1.2.1 and snapbox 1.2.2: observed capabilities

Both are test-only dependencies. Together they brought the probe's lock file
to 65 packages.

- A `.toml` case names arguments, environment and an expected status, with
  `.stdout` and `.stderr` files beside it. `status.code = 0` requires that
  exact code.
- `TestCases::default_bin_path` ran a binary that is not a Cargo target of
  the package, which is how the signed app's controller would be addressed.
- snapbox's `Command` asserted an exact code, exact stdout and empty stderr
  in one call, and passed a non-UTF-8 argument.
- Case files can be literate Markdown (`.md`, `.trycmd`) whose `console`
  blocks are executed, which is the crate's stated route to pulling tested
  commands into documentation.

Observed limits, each of which lets a case pass without establishing the
promise it appears to cover:

- A case with no `.stderr` file passed while the binary wrote to stderr. The
  crate's documentation says an absent file is not verified. An empty
  `.stderr` file made the same case fail.
- A literate case merges stdout and stderr into one transcript, so it cannot
  show which stream carried the output.
- `status = "failed"` accepts any nonzero code.
- With `TRYCMD=overwrite` in the environment the failing case rewrote its
  own expectation and the run reported success.
- Arguments in case files are strings, so a non-UTF-8 argument and a stream
  without a reader need hand-written tests.
- A snapshot of a card compares the card with an earlier copy of itself. It
  detects change. It does not show that anything governs the card.

## Provisional cards and derivation ledger

These candidates give the editorial examination a concrete starting point.
They do not settle the inventory, a rendering mechanism or any exception to
requirement 3. The subject card for `help run` answers which runner-mode
values the command accepts:

```text
run
  --runner-mode
    standard
    byoxpc
```

This is a vocabulary card; it does not supply a complete invocation or imply
that selecting a mode guarantees a successful run. The bare fallback lists
selected top-level command spellings, including commands whose subject cards
are not yet proposed:

```text
help
run
runner
example
test-input
version
```

Both candidates end with one newline. Their content has the following
ledger; the linkage column describes work still needed, not an established
connection.

| Element | Governing source and status | Use to the reader and what it clarifies | Linkage needed and rule exposed |
| --- | --- | --- | --- |
| `run` on the subject card; `help`, `run`, `runner`, `example`, `test-input`, `version` on the fallback | The recognized first arguments in `cli::run` in [cli.rs](controller/src/cli.rs); declared admission and dispatch behavior. | Names the subject and gives the reader other entry points. | Derive the selected spellings from definitions actually used by dispatch. The current match arms are not an enumerable declaration; a separate list for rendering would duplicate them. Alias selection and ordering are editorial choices. |
| `--runner-mode` under `run` | `parse_arguments` in [run_flow.rs](controller/src/run_flow.rs); declared flag recognition and value consumption. | Identifies the option to which the displayed vocabulary belongs. | Share its governing definition with the card builder. Parsing a flag and successfully completing a run are separate obligations. |
| `standard`, `byoxpc` under `--runner-mode` | `RunnerKind::parse` in [runner_manager.rs](controller/src/runner_manager.rs), called by `parse_arguments`; declared value admission. | Shows the accepted spellings and makes the CLI vocabulary distinct from legacy registry input. | Make the parser's vocabulary enumerable without introducing a rendering-only copy. `as_str` has its own spelling matches today; serde's legacy `machme` and `debuggable` aliases do not establish CLI acceptance. |
| Indentation, ordering and final newline | Renderer layout; editorial arrangement under the settled requirements. | Groups each value with its option and the option with its command. | Derive the command/option/value relationships from the governing interface. Layout must not introduce an unsupported relationship or turn these fragments into a promise of successful execution. |

All semantic elements in these candidates express declared behavior; none is
an execution observation. Labels and placeholders remain explicit unresolved
candidates: `<request.json>`, `<n>`, `Usage:`, and `default:` have no proposed
derivation here and are omitted from the sketches. In particular,
`DEFAULT_TIMEOUT_MS` governs `240000`, but printing that number alone would
not tell the reader it is a default. Adding that element requires resolving
its presentation and any named exception first.

Use this ledger to scope the experiments. E2 and E3 can start with the
runner-mode vocabulary after a minimal shared-definition change. E1 is needed
if the chosen elements justify investigating a governing parser declaration;
these cards do not by themselves require a full `run` parser migration. E4
is needed if executed examples become card candidates or a concrete test
maintenance problem justifies comparing harnesses. Neither sketch contains
an observed transcript, so neither creates a build-order dependency on E4.

## Proposed recognition and address matrix

This is a proposal for the recognition and address decisions, not a new
settled requirement. Resolve it with the maintainer before E1 so the parser
experiment has an explicit compatibility target.

- First-argument `help`, `--help` and `-h` recognize help immediately. The
  next argument alone selects the `run` card when it is exactly `run`;
  anything else, including no argument or a non-UTF-8 argument, selects the
  fallback. Remaining arguments cannot change that selection.
- After a recognized operational command (`run`, `runner`, `example` or
  `test-input`), an exact `--help` or `-h` anywhere before the first exact
  `--` recognizes help before ordinary argument parsing. It overrides
  earlier errors and option-value consumption. `run` selects its card; the
  other commands select the fallback until their cards are chosen.
- The existing `runner help` prefix also recognizes help and selects the
  fallback, ignoring its tail. Other uses of the word `help` retain their
  ordinary meaning. Unknown top-level commands and the version command do
  not acquire help recognition from a trailing flag.

Recognition compares exact `OsString` tokens without requiring the rest to
be UTF-8. It precedes host facts, app-root resolution and all command
dispatch with operational effects. Every recognized row below means exit 0,
the selected card on stdout and empty stderr, subject to the settled stdout
failure exclusion. Excluded rows keep ordinary command behavior, which may
depend on operational state.

| Arguments after `policy-witness` | Proposed recognition and card | Precedence or compatibility consequence |
| --- | --- | --- |
| `help`, `--help`, `-h` | Help; fallback. | Moves top-level help from stderr to stdout. |
| `help run`, `help run junk`, `--help run --bad`, `-h run -- --help` | Help; `run`. | The immediate subject wins; all later tokens are ignored. |
| `help bogus run`, `help -- run`, `help` followed by a non-UTF-8 token | Help; fallback. | Selection never searches the tail for a known subject. |
| `run --help`, `run -h`, `run x --help` | Help; `run`. | No host-fact collection or ordinary run preparation. |
| `run --bad --help`, `run --timeout-ms --help`, `run --runner-mode --help` | Help; `run`. | Help wins over earlier argument errors and a pending option value. These are deliberate behavior changes. |
| `run` followed by a non-UTF-8 token and `--help` | Help; `run`. | Earlier opaque input cannot prevent recognition. |
| `run help` | Ordinary `run`; no card. | `help` remains a legal request path. |
| `run -- --help`, `run request.json -- --help` | Ordinary `run`; no card. | The separator stops the help scan. The existing parser stops processing there; it does not reinterpret the tail as a request path. |
| `run --help --`, `run --timeout-ms -- --help` | First form: help, `run`; second form: ordinary `run`. | A help token before the separator wins; one after it cannot override an invalid option value. |
| `runner help`, `runner --help`, `runner install --help`, `runner status --help`, `runner reconcile --help` | Help; fallback. | Recognizes help before subcommand validation or operational work. |
| `runner list --help`, `runner validate --help` | Help; fallback. | Prevents registry listing, locking and validation for these invocations. |
| `example --help`, `example -h`, `test-input --help` | Help; fallback. | Changes existing refusal behavior; accepting the `example` rows requires revising its contract rule that every argument is refused. |
| `example help`, `test-input help` | Ordinary usage refusal; no card. | The word form is reserved to the explicit prefixes above. |
| No arguments, `bogus`, `HELP`, `bogus --help` | Ordinary top-level usage refusal; no card. | Unknown top-level commands are not promoted to help. |
| `version --help`, `--version --help` | Ordinary version output; no card. | Preserves the version command's existing treatment of trailing arguments. |

The broad flag rule trades ordinary argument interpretation for reliable
help recognition before `--`. Review that tradeoff and the contract changes
explicitly. If a row is revised, update the rule, expected card and affected
contract/test expectations together before interpreting E1's differences.

## What would demonstrate a real connection

This is the proposed standard. E3 tests whether its controls are practical
and may refine it. For each element that appears on a card, the
implementation names the code or execution that governs it and shows all of
the following.

1. **Behavior depends on the same source.** The named code is on the path
   that admits, refuses or performs the thing the element describes. A
   declaration consulted only by the card builder does not satisfy this.
2. **The card follows the interface.** A control changes the governing code
   only (a flag renamed, a vocabulary member added, a default changed) and
   observes the corresponding behavior change independently. The built card
   changes to match, or a named freshness/linkage check refuses the build,
   with no edit to any help-specific input. A compiler or equipment failure
   does not establish this connection.
3. **The card cannot be edited alone.** There is no help-specific input in
   which the element's text could be altered while behavior stays the same.
   Where a label or placeholder makes that false, it is one of the
   [exceptions to decide](#open-decisions), listed by name.
4. **The check can fail.** Each check that supports 1 to 3 has a rejected
   control: a disconnected copy subjected to the same governing-source
   mutation as the connected version, an unlisted token, or a stale card.
   E3 specifies the paired mutation protocol. Immediate rejection of an
   unchanged copy is a separate structural claim and needs a named check;
   identical output cannot establish it. The repository's existing practice
   of pairing passing and rejected controls applies.
5. **Status is stated.** The element is recorded as a declared obligation
   (code enforces it, or a contract rule that a check enforces states it) or
   as an observation (it comes from one execution). This records the
   element's status, not the source of its text. A card does not present an
   observation in the position of an obligation.

Items 1 to 3 are worded for an element governed by code. For an element
taken from an execution, the governing source is the executed case: a test
runs that case against the built binary and requires its result, a change
to the binary's behavior changes the element or fails the check, and the
recorded result cannot be edited without that check failing.

For requirement 2, the evidence is an execution of help-recognized
invocations in a state where operational prerequisites are absent, compared
byte for byte with the same invocations in a working state: the controller
binary copied outside any app bundle, `HOME` naming a missing or unwritable
directory, no registry, malformed and non-UTF-8 trailing arguments. Each
must exit 0 with identical stdout and empty stderr. A structural observation
accompanies it, because a list of passing invocations does not show that an
unlisted one does no work. The existing `observe` seam is a starting point
and is not sufficient as it stands, for the reason given in the findings.

What can pass while leaving the result unestablished:

- A card snapshot that matches, in any snapshot tool.
- A citation or drift check, which shows that a named symbol exists.
- A declaration table that renders cards while hand-written parsing still
  decides behavior.
- A stream that is not checked, a merged transcript, or a loose status, as
  listed under trycmd above.
- A test that runs a plain Cargo build instead of the signed app's binary,
  or one whose expected text tolerates the build identity by eliding more
  than the identity.
- An exit-0 assertion over a fixed list of malformed invocations, taken as
  proof that help performs no operational work.
- An example's recorded result presented as what the command guarantees.

## Sequence

1. **Review the candidates and recognition proposal.** Review the
   [provisional cards and ledger](#provisional-cards-and-derivation-ledger)
   for reader usefulness and derivation gaps; extend the ledger when adding
   an element. Settle the
   [recognition and address matrix](#proposed-recognition-and-address-matrix)
   with the maintainer before E1. Record which elements justify each
   experiment and which experiments are deferred. Keep the ledger here or
   in a record under `records/` linked only from this plan.
2. **Experiments.** Run the [experiments](#experiments) needed for those
   candidates. E2 can start with the vocabulary and a minimal shared
   definition, without waiting for E1. E3 needs the card E2 produces.
   Undertake E1 and E4 when the ledger identifies the question each must
   answer; record the reason if either is deferred.
3. **Decisions.** Bring the [open decisions](#open-decisions) to the
   maintainer with the ledger and the experiment results. Present each
   commitment as the distinction, why it matters and what changes. Amend
   this plan with the resulting MVP, meaning the first slice to implement:
   its resolved recognition rule and address grammar, card inventory,
   linkage and rendering mechanism, permitted repair and dependency
   adoption. Reopen an earlier decision only with the experiment result
   that warrants reconsideration.
4. **Implementation of the MVP** as amended.
5. **Verification and alignment** as described under
   [verification](#verification) and
   [consequences](#consequences-for-existing-material).

Reconsider the approach, instead of pressing on, if no mechanism satisfies
the [connection evidence](#what-would-demonstrate-a-real-connection) for any
element worth printing, if the only way to link an element is to change
behavior the contract states, or if the ledger shows that the useful
elements are mostly observations with no governing declaration.

## Experiments

Each is scoped to answer the candidate ledger's question and stop. None
commits the project to its subject. Record the selected inputs, controls and
remaining uncertainty so a deferred alternative need not be investigated
merely because it appears below.

**E1. Can a clap declaration be the governing parser for a PolicyWitness
command?** After resolving the recognition matrix, replace the hand-written
parsing of one command with a clap declaration through `try_get_matches_from`,
in a scratch branch or worktree.
`run` is the informative first subject because its refusals carry the
strictest existing promises: every refusal is a `kind: "run"` envelope on
stdout, argument refusals never reach the app root, and the request path is
an `OsString`. Compare the matrix cases and ordinary invocations, separating
approved help changes from additional parser changes. Record every observed
difference and classify each as stated by the contract, pinned by a test, or
incidental. The result informs whether clap can govern some, all or none of
the commands, and supplies the list of behavior changes that the
[repair decision](#open-decisions) has to weigh. A declaration that renders
well but cannot replace the parser without unacceptable changes is evidence
against adopting clap for linkage.

**E2. Where can cards be constructed during the build?** Using one ledger
element with a single governing definition, produce card bytes during the
build and embed them so that help prints stored bytes. Assess routes against
that element's needs: the Cargo build script sharing the declaration source,
a separate crate used as both a dependency and a build dependency,
compile-time assembly from the tables the parser reads, and a registered
generator with `--check`. Prototype the plausible routes needed to resolve
the placement decision; record reasons for deferring or ruling out the
others. For each route tried, record what the declaration may refer to
(the `include!` route requires a self-contained file), what the build's
Cargo admission, reuse judgment and fresh-build rules report, and whether an
incremental build can ship a stale card. The result informs the rendering
mechanism and where construction sits in the build.

**E3. Do the connection controls discriminate?** For the card from E2,
choose one exact governing-source mutation and an independent behavior
assertion, such as renaming an admitted flag and checking that the parser
accepts the new spelling and refuses the old one. Keep the mutation and the
assertion identical across the connected and disconnected trials:

1. Establish the connected baseline: the original behavior and card agree,
   and the check passes.
2. Apply only the governing-source mutation and rebuild. Observe the
   intended behavior change and the matching card change without editing
   help-specific inputs or accepting a new snapshot. If the build instead
   refuses stale generated material, name the freshness check, then use the
   owning generator and rebuild to observe the changed behavior and card.
3. Restore the baseline and make the renderer read a private, identical
   copy of the governing table. Confirm the original behavior and card
   bytes are unchanged. Ordinary output checks may pass at this point.
4. Apply the exact same mutation to the actual governing definition, leaving
   the renderer's copy untouched, and rebuild. Require the same check to
   reject the resulting behavior/card mismatch. Confirm that the behavior
   changed while the card retained the old spelling, or record the named
   build check that rejected this disconnection before an artifact could
   be produced.

Record the source patches, build commands, behavior observations, card
bytes, check identity and expected rejection. Compilation errors, missing
equipment and unrelated failures do not count as rejected controls.

If immediate rejection of the unchanged copy in step 3 is also required,
name the structural check and show it accepting the connected baseline and
rejecting that copy for the broken source connection. Keep that result
separate from the output comparison and paired mutation. Source review of
the shared dependency remains necessary: the mutation demonstrates detection
of this disconnection under this change, not every possible independent edit.
If no practical check rejects the mismatch or its disconnected construction,
the mechanism does not meet the proposed connection standard. The result
confirms or refines the acceptance evidence required of every element.

**E4. Can executed cases connect tests, the example work and help?** The
example work is the `example` and `test-input` publishers with their live
cases under
[witness_contract](tests/suites/witness_contract/README.md#the-apps-own-example).
Run
trycmd or snapbox cases against the signed app's controller through the
dispatcher, for a few help-shaped and ordinary invocations. Establish:

- whether separate stdout, stderr and exact status can be required for every
  case, with a guard that refuses a case lacking a `.stderr` expectation and
  refuses to run with `TRYCMD` set;
- how case files, temporary directories and parallel execution sit with the
  dispatcher's output ownership and the checkout lock;
- whether one corpus of cases can be read by three consumers (the test that
  executes it, the `example` and `test-input` material, and the card
  builder) so that a command line shown on a card is one the test proves
  the binary accepts;
- what happens to the build order when a card would contain a result
  produced by executing the binary that embeds the card. The build does not
  execute the controller today, and a recorded result is an observation
  under requirement 4.

The result informs whether trycmd, snapbox alone or the existing
`std::process` tests carry the execution checks, and whether observed
transcripts are card material at all.

## Open decisions

None of these is settled merely by appearing in this plan. The recognition
and address proposals are resolved before E1; the remaining decisions use
the ledger and the applicable experiment results.

| Decision | Informed by | What depends on it |
| --- | --- | --- |
| **Recognition rule.** Accept or revise the [proposed matrix](#proposed-recognition-and-address-matrix), including precedence over errors and option values, the `--` boundary and preservation of `run help` as a path. Resolve before E1. | The findings table; the contract's `example` and `test-input` rules; the maintainer's view of which careless forms occur. | Which existing tests and contract statements change; how much of each command's parsing help recognition must precede. |
| **Address grammar.** Accept or revise immediate-subject selection and the fallback outcomes in the matrix before E1. | The provisional cards; requirement 1's limit on selection. | Card inventory; the selection code. |
| **Card inventory.** Accept, revise or extend the [provisional cards](#provisional-cards-and-derivation-ledger) and their ledger. | The ledger's two-ground examination of each element. | Required experiments and everything downstream. |
| **Linkage architecture.** What "the code that governs" is for each element: a parser declaration, a shared table, typed vocabularies, executed cases, or a mix. | E1, E3, E4. | Parser changes; dependency adoption. |
| **Rendering mechanism and build placement.** | E2. | `build.sh`, `build.json`, generator registration or Cargo provenance. |
| **Repair and refactoring before the MVP.** How much parser change is accepted so that elements have governing declarations, and which exposed rules (arguments discarded by `runner list` and `runner validate`, flags matched only to be refused, `--timeout-ms 0` becoming 1, the last request path winning) are repaired, declared or left off the cards. | E1's difference list; the ledger's exposures. | Scope and risk of the MVP; contract and test changes. |
| **Non-derived tokens.** Whether a card may carry any token that does not come from governing code: section labels, renderer-supplied words, value placeholders, the word that separates an observation from an obligation. The ledger explicitly leaves `<request.json>`, `<n>`, `Usage:` and `default:` unresolved. Each is an exception under requirement 3 unless a derived substitute exists. | The ledger; clap's observed output; E3. | Whether clap's renderer can be used as is; card legibility. |
| **Observations on cards.** Whether any element may be an observation, and how a card marks it without prose. | E4; requirement 4. | Build order; fixture ownership. |
| **Usage failures.** What a non-help usage failure prints: `USAGE`, `runner_usage` and the `test-input` usage line serve failures today. If they stay for failures, authored help prose remains in the binary beside the cards. | Recognition rule; requirement 3. | `example`'s refusal output; bare and unknown-command behavior; the README block. |
| **Public status of help.** Whether the help promises become contract rules. A contract change moves the build identity and requires the authored-tree procedure. | Maintainer. | Contract sources, stamps, shape goldens, support citations. |
| **Build identity on cards.** Whether a card shows the contract identity, which differs in every build. | Ledger. | Expected-output handling in tests. |
| **Failed stdout write.** Outside the promise, but the current result is a panic with exit 101. `example` and `test-input` define exit 2 without a panic. | Existing publisher pattern. | A small part of the help path and its tests. |
| **Dependencies.** Whether clap, trycmd or snapbox are adopted, and in which `Cargo.toml` section. Neither adoption nor rejection is presumed. | E1, E2, E4; the lock file's status as a build input. | `Cargo.lock`, `DEPENDENCIES.md`, provenance. |

## Verification

The amended plan must restate these against the chosen mechanism. They are
the minimum.

- **Connection.** Every card element has the five items of
  [the connection evidence](#what-would-demonstrate-a-real-connection),
  including a rejected control for each check. Retain E3's paired mutation
  evidence and identify any separate structural rejection of an unchanged
  copy; a baseline output match supplies neither result.
- **Help-input promise.** The absent-prerequisite comparison described
  there, executed on the signed app's controller and on a copy of that
  binary outside the bundle, with stdout, stderr and
  exit status asserted separately and exactly. Cover every row of the
  resolved recognition matrix, including its ordering, separator and
  non-UTF-8 cases, as well as the invocations in the findings table that
  the rule covers. For each excluded help-shaped invocation, retain a case
  establishing ordinary behavior under explicit fixture conditions. Check
  selected card identity as well as status and streams.
- **No invocation-time assembly from operational state.** The structural
  observation that the help path reaches no host-fact, app-root, manifest,
  registry or runner code.
- **Build.** A fresh build and an incremental build both carry the current
  card; a stale card is refused or cannot occur, and a control shows which.
- **Suites.** `unit`, `integration` and `source_drift` at least, on one
  signed build from the implementing commit in a fresh `PW_TEST_OUT_DIR`,
  plus any suite the parser changes reach. Follow
  [tests/AGENTS.md](tests/AGENTS.md) for selection and evidence.

## Consequences for existing material

These are the materials in play. Which of them change depends on the open
decisions; those that do change together:

- `USAGE`, `print_usage`, `runner_usage`, the `test-input` usage line and
  their callers in `cli.rs`, `run_flow.rs`, `runner_commands.rs`,
  `example.rs` and `test_input.rs`.
- `example_prints_one_request_and_refuses_every_argument`,
  `test_input_cli_refusals_and_write_failures_exit_2_safely`, the
  `RunOutput::Help` assertions in `run_flow.rs`, and the
  [integration invariants](tests/suites/integration/README.md).
- `check_cli_surface_agreement`, which reads the `usage: ... notes:` text
  directly, the README block it compares, the synchronization rule in
  `controller/AGENTS.md`, and in `architecture.json` the `cli_rs`, `D24`
  and `D30` entries plus the caller and argv-channel entries that cite
  `cli.rs`: `pub fn run`, with the regenerated architecture account.
- Contract support citations that name `cli.rs`: `pub fn run`, if dispatch
  moves out of that function, and new rules with their own support if help
  becomes public.
- `docs/build.json` and `BUILD.md` if a build stage is added,
  `DEPENDENCIES.md` and the lock file if a crate is adopted, and the
  generator contracts if a generator is registered.
