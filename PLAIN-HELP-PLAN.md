# Generate `policy-witness help` cards from the executable interface

Status: proposed; implementation has not started.

## Problem

`policy-witness` prints hand-written usage texts: `USAGE` in
[cli.rs](controller/src/cli.rs), `runner_usage` in
[runner_commands.rs](controller/src/runner_commands.rs), and a one-line form
in [test_input.rs](controller/src/test_input.rs). Nothing connects any of
them to the argument handling beside it. A drift check compares the usage
lines of `USAGE` with a block in the controller README without checking
agreement with argument handling.

Help forms differ in stream, status and operational work. Some collect host
facts or access the app before printing; failed writes can panic with exit
101. The [findings appendix](#appendix-current-findings) records the source
and execution evidence.

## Requirements

1. **Bare card output.** Help prints the base card or one of the `run`,
   `example` and `result` topic cards. Cards carry no explanatory sentences.
   The base card lists every available topic, one address per line.
2. **No operational prerequisites.** Once an invocation is recognized as
   help, malformed arguments trigger no operational work, no stderr
   diagnostic and no failing usage status. Help does not depend on a valid
   specimen, an available runner, a writable records directory or a working
   execution configuration. It writes one card to stdout, leaves stderr empty
   and exits 0. This excludes stdout failure and external termination.
3. **Mechanical linkage.** Card contents come from code that actually
   governs the interface. Independently authored help prose checked against
   citations, examples or snapshots does not qualify, including prose stored
   in constants, attributes, templates or generator code. Any token exception
   requires an individually named justification and maintainer approval.
4. **Build-time construction and verification.** Construct and verify cards
   during the build; invocation prints the stored bytes. Check agreement with
   execution using independent expectations.
5. **Word form only.** Only an exact leading `help` invokes help, under the
   [help grammar](#help-grammar). `--help` and `-h` remain ordinary arguments.

## Scope

- Refactor the paths listed under [interface inventory](#interface-inventory-and-residue)
  and the result-selection mechanism. Additional behavior changes require
  the [permitted-repair decision](#open-decisions).
- `sbpl-check` has its own usage text in
  [sbpl-check.rs](controller/src/bin/sbpl-check.rs) and is outside this plan.
- Preserve existing public meanings and contract text. Whether to add public
  help rules is an [open decision](#open-decisions).
- Cards contain declared interface rules and specimen content; observed query
  answers, attempt outcomes and transcripts are excluded.
- No release, notarization or publication step.

## Cards and governing sources

Completion requires four cards: the base card and the `run`, `example` and
`result` topic cards, plus the [interface inventory](#interface-inventory-and-residue),
its joins and residue baseline. For each selected card element, record the
reader question it answers and the rule or declared content it represents.
The `run` and `example` sketches are candidates for their exact projections.

The base card uses the definitions consumed by topic selection, in this order:

```text
run
example
result
```

It has no heading or command directory. Every card ends with one newline.

The `run` candidate answers which values its runner-mode option accepts:

```text
run
  --runner-mode
    standard
    byoxpc
```

The `example` candidate answers which file attempts the emitted specimen
requests in each phase. It projects declared content from `EXAMPLE_DOCUMENT`:

```text
example
  initial-reads
    open_read /etc/hosts
    read_fresh /usr/share/dict/connectives
  restricted-read
    open_read /usr/share/dict/propernames
```

These are partial views: the `run` card is not a complete invocation, and the
`example` card omits the specimen's query definitions. Neither reports an
attempt or guarantees its outcome.

The `result` card projects `run`'s result-selection obligations: how a selected
controller disposition determines `result.normalized_outcome`, `result.ok`,
`result.exit_code` and the corresponding process status. It is a help topic,
not an additional operational command. Its
[projection and controls](#result-projection) are defined below.

| Element | Governing source and status | Projection |
| --- | --- | --- |
| Base-card entries and topic addresses | The topic definitions consumed by help selection; declared addressing behavior. Command topics share their command's spelling definition. | Every registered topic address, in the specified order. |
| `run`, `example` on their cards | Dispatch definitions currently expressed in `cli::run` in [cli.rs](controller/src/cli.rs); declared command recognition. | The command spelling identifying the card. |
| `--runner-mode`, `standard`, `byoxpc` | `parse_arguments` in [run_flow.rs](controller/src/run_flow.rs) and `RunnerKind::parse` in [runner_manager.rs](controller/src/runner_manager.rs); declared argument admission. | The option and CLI-accepted values, excluding registry-only aliases. |
| Example phases, attempt actions and targets | `EXAMPLE_DOCUMENT` in [example.rs](controller/src/example.rs), which the publisher emits; declared content of this build's specimen. | File actions and targets grouped by phase. |
| `result` topic address | The topic definition consumed by help selection; declared addressing behavior. | Names the result projection. |
| Result conditions, outcome labels, `ok` and exit statuses | Local refusal helpers, `admit_reply`, `runner_outcome`, completion and envelope/exit selection in [run_flow.rs](controller/src/run_flow.rs); declared controller reporting obligations. Field names belong to [json_contract.rs](controller/src/json_contract.rs). | The disposition-to-result relation specified below. |
| Order, indentation and final newline | Editorial arrangement and renderer layout. | Group elements according to relationships in their governing definitions. Layout cannot imply an unsupported relationship or an observed outcome. |

### Result projection

The subject is selection of the controller result for `run`, covering every
selected result class. Detailed causes of each refusal, diagnostic wording,
native return values and evidence retention remain with their existing owners.
The relation describes the selected process status on ordinary publication;
it does not promise that status after an output failure or external termination.

The following table specifies the relation to project. Its explanatory
condition descriptions are planning prose, not authorized card strings.
The flat card must derive its conditions and values from the governing
selection mechanism, using the same rules for labels and placeholders as the
other cards.

| Selected controller disposition | `result.normalized_outcome` | `result.ok` | `result.exit_code` and process status |
| --- | --- | --- | --- |
| Local request refusal | `bad_request` | `false` | 1 |
| Controller tool failure, including request-delivery failure | `tool_error` | `false` | 2 |
| Client or reply admission refusal | Selected refusal label. | `false` | 1 |
| Admitted host reply with outcome `finished` | `finished` | `true` | 0 |
| Admitted host reply with another outcome | Retained host label. | `false` | 1 |
| Admitted completion with no host reply | `runner_response_unavailable` | `false` | 1 |

Make this relation govern ordinary result construction and the status returned
to the caller, and construct the card from those same definitions during the
build. Today local refusals, admission and completion make these choices at
separate sites, and `envelope` takes a process status separately from the
result's exit field. The projection must expose and remove that independent
choice, without changing the existing meanings or upstream admission order.

The input is the selected disposition, including delivery and admission state;
a received string saying `finished` is insufficient. Conversely, failed
individual attempts and integrity findings may coexist with an admitted
`finished` result and must not independently change its success classification.

### Editorial representation

Selection and ordering live in a card specification containing typed
references to governing definitions, never spelling lists, replacement text,
display-name fields or lookups such as `lookup("run")`. Internal identifiers
are not printed. A schematic `Command::Run` supplies both the command-topic
address and its displayed name; `RunOption::RunnerMode` selects the option
while omitting `RunOption::TimeoutMs`.

The recognizer, dispatcher and parser must consume the same definitions on
the relevant paths. A help-only table beside literal parsing matches does
not qualify. For specimen content, rendering selects fields from the same
app-owned constant the publisher emits. Renaming a selected spelling or
changing a selected specimen field changes both behavior and the card without
editing its selection. Removed or misassociated references are rejected by
compilation or build validation.

Labels and placeholders such as `<request.json>`, `<n>`, `Usage:` and
`default:` require the token-exception decision unless derived substitutes
exist. A governing default value alone does not supply its label.

### Interface inventory and residue

The build that renders the cards also writes an interface inventory: a
machine-readable record of every definition the governing tables hold,
whether or not a card selects it. The inventory adds no topic or flag and is
not read at invocation.

Each entry records:

- its stable identifier, which is the typed identity the card specifications
  reference and is never printed on a card;
- its spellings and relationships: command, option and value, or for the
  result relation a row's inputs and outputs;
- the parser or reader whose behavior the entry describes; identifiers remain
  stable across spelling changes, and each reader's admission rule is explicit;
- its admission kind;
- the cards that reference it, which may be none.

The admission kind is the value dispatch or parsing acts on. A kind recorded
only for the inventory is an authored label and does not qualify.

| Kind | Behavior | Instance in the current source |
| --- | --- | --- |
| Admits | The spelling is accepted and used. | `--runner-mode standard` |
| Refuses always | The spelling is recognized so that it can be refused. | `--runner-mode machme` |
| Discards | Input is accepted and ignored. | The tail after `version` |
| Reader-specific alias | The selected reader resolves the spelling to a canonical value. | The registry reader's `machme` and `debuggable` |
| Unenumerated | Dispatch delegates the tail to a parser whose definitions are not enumerated. | `runner` and `test-input` |

Enumeration is exhaustive on every path a governing table covers: there the
recognizer, dispatcher and parser match no spelling that is not a
definition, and a check rejects a literal match placed beside the table. A
path no table covers appears as one unenumerated entry for its command.
Enumeration covers top-level dispatch, help selection, all
`run` argument handling, the runner-mode vocabulary across CLI and registry
readers, and the definitions needed for the `example` and `result` projections.
The `runner` and `test-input` tails remain unenumerated. In particular,
`--executable`, `--bundle-id` and the `runner list` tail stay within the
unenumerated `runner` entry rather than receiving individual entries.

Table migration preserves existing admission behavior except for the help
grammar and approved repairs. Reader-qualified rules preserve distinctions
such as `machme` being refused by CLI parsing and accepted by registry reading.

Commit the generated inventory beside its generator's README and residue
baseline. The build regenerates into temporary output and compares it with
the committed copy before signing. Offline contract checks read the committed
copy. Generate cards and inventory without a signed app or the controller's
contract stamp.

For the result relation the inventory holds every row with its inputs and
outputs, and records an input that is consulted without changing any output,
such as failed attempts or integrity findings beside an admitted `finished`
reply. The builder derives two further facts from the rows and records them:
which outputs are functions of other outputs, and which rows no output
distinguishes. These are reported, not refused, and are never authored.

Three joins use the identifiers:

- **Contract.** A contract node that states a projected element cites its
  identifiers in an `interface` list, for example
  `interface: ["result.admitted_finished"]`. These references are support
  metadata excluded from the public snapshot under the
  [authoring rules](docs/contract/AGENTS.md); existing owner records describe
  the check and its limits. The contract generator's check resolves each
  identifier and compares the node's structured facts (`test`, `set_value`
  and listed vocabulary values) with the entry. Comparison includes inherited
  admission conditions and first-match ordering. Start with direct references
  and deterministic comparisons; add operand bindings only where the prototype
  demonstrates ambiguity. Report the compared facts and remaining prose,
  including `free.*` text; resolving a reference supplies no credit to that
  prose. Cite the projected elements in the
  [controller pre-invocation refusal](docs/CONTRACT.md#contract-refusals-controller-consequence)
  and the envelope's outcome and exit rules, the runner-mode option and the
  example emission.
- **Cases.** Each executed case is associated with the entries it exercises.
  The association is derived from the case's arguments and required results;
  a declared association is accepted only where derivation is impossible and
  is then held by the mutation record. The join reports entries no case
  reaches and entries whose reaching cases all use test-owned inputs. The
  latter is a property of retained evidence, not a claim that production
  inputs cannot reach the entry. Keep entries with no reaching case separate.
- **Mutations.** E3's mutations are retained as data: the entry, the
  mutation, and which of the card, the contract check and the cases changed
  or failed. Record `not_run`, `unchanged`, `changed` and `failed` separately
  for each check. E3 specifies the checks and cost measurement. Report when
  a mutation changes a case and leaves the other checked outputs unchanged,
  with any omitted checks explicit.

A residue baseline records member identifiers and counts separately for:

- Non-`Admits` entries, by admission kind and reader.
- Entries referenced by no card.
- Entries with reaching cases that all use test-owned inputs.
- Explicit non-derived token exceptions, by card and token role. Whitespace
  is layout and is not counted as a token exception.

Compare membership as well as totals: removing one member cannot silently
authorize a different member. Generator write mode accepts reductions and
writes the current sets; check mode rejects stale committed copies. Additions
require an explicit refresh, following the reduction rule of
[free_text.json](docs/contract/free_text.json). Expanded enumeration has a
refresh path that records which opaque entry was replaced and distinguishes
newly exposed behavior from changed behavior.

The inventory generator owns the baseline. Its adjacent README documents one
refresh command; refresh requires a maintainer-reviewed diff of members and
counts. Uncarded entries and reader aliases may remain in the baseline;
card selection and behavior changes require their own review.

## Help grammar

- Compare the first argument with `help` as an exact `OsString`, before host
  facts, app-root resolution or operational dispatch. A match invokes help.
- The second argument alone selects a registered topic. An absent, unknown,
  differently cased, empty, flag-shaped or non-UTF-8 address selects the base
  card. Ignore every later argument.
- Nothing else invokes help. `--help` and `-h` are ordinary arguments, and
  the word `help` has no special meaning after a command.

The statuses below exclude stdout failure and external termination. For
refusals, "diagnostic" means the text chosen in the output decision when
stderr is writable; it may include the base card on stderr.

| Arguments after `policy-witness` | Status | stdout | stderr |
| --- | --- | --- | --- |
| `help` | 0 | Base card. | Empty. |
| `help run`, `help run junk`, `help run --bad`, `help run -- x` | 0 | `run` card. | Empty. |
| `help example`, `help example extra` | 0 | `example` card; no publisher is invoked. | Empty. |
| `help result`, `help result extra`, `help result --bad` | 0 | `result` card; no run or result evaluation is performed. | Empty. |
| `help bogus`, `help bogus run`, `help RUN`; any other unregistered address | 0 | Base card. | Empty. |
| `help --run`, `help --help`, `help -h`, `help -- run`, `help ''`, `help` followed by a non-UTF-8 token | 0 | Base card. | Empty. |
| `--help`, `-h`; no arguments, `bogus`, `HELP`, `result` | 2 | Empty. | Usage diagnostic. |
| `run --help`, `run -h`, `run x --help` | 2 | Ordinary `tool_error` argument-refusal envelope. | Empty. |
| `runner help`, `runner --help` | 2 | Empty. | Unknown-runner-command diagnostic. |
| `runner install --help`, `runner status --help`, `runner reconcile --help`, `example --help`, `example -h`, `example help`, `test-input --help`, `test-input help` | 2 | Empty. | Each command's refusal diagnostic. |
| `runner list --help`, `runner validate --help`, `version --help`, `--version --help` | Ordinary command status. | Ordinary output, not help output. | Ordinary command diagnostics. |
| `run help` | Ordinary `run` status. | Ordinary envelope for the request path `help`. | Ordinary `run` behavior. |

Exit 0 from `example` or `test-input` continues to establish publication of one
complete JSON document. Discarded tails retain their operational effects:
`runner list --help` lists the registry; `runner validate --help` locks and
validates it.

### Flag guard

- Remove existing help recognition from `cli::run`, `parse_arguments` and
  `cmd_runner`, including `Arguments::Help` and `RunOutput::Help`, leaving the
  single leading-word path.
- Exercise `--help` and `-h` at the top level and after every command and
  subcommand, asserting ordinary status and streams separately.
- Reject topic addresses beginning with `-`. If a parser library is used,
  inspect its declaration for a long `help` flag, short `h` flag or enabled
  built-in help subcommand and reject them.
- Demonstrate each guard with a rejected control: a restored flag-help arm,
  a flag-shaped topic address and a parser declaration with built-in help
  enabled.

## Linkage requirements

Every selected element names its governing source and satisfies these
properties. E3 supplies the control procedure.

| Property | Required evidence |
| --- | --- |
| Behavior uses the source | The definition actually admits, refuses, dispatches or emits what the card describes. A rendering-only declaration does not qualify. |
| The card follows the source | A governing-source mutation changes the independently observed behavior and card, or a named freshness/linkage check refuses the build. No help-specific input is edited. |
| A fixed element has no independent text | The editorial specification selects references or source fields and cannot rewrite their text. Named label/placeholder exceptions remain explicit. |
| The check can reject a fault | Each supporting check has a rejected control, including the disconnected-copy trial in E3. An unrelated failure supplies no linkage evidence. |

## Sequence

1. Review the card sketches and source table for usefulness and derivation gaps.
   Fix the common elements and cases for comparison, including the `result`
   relation and the inventory's entry form within its specified reach.
2. Complete E1–E4. For a candidate that cannot complete a stage, record the
   concrete incompatibility or failed control; missing comparisons remain
   unfinished work.
3. Bring the results and [open decisions](#open-decisions) to the maintainer.
   Approve the exact four-card projections and the implementation, dependency
   and output decisions. Record those choices before implementation.
4. Implement the chosen approach, update affected materials together, and
   complete the [verification](#verification).

## Experiments

### E1–E3: one comparison of definitions, build and linkage

Use the same selected cards, typed references, ordinary argument cases and
independent expected results for both candidates:

| Candidate | Governing implementation |
| --- | --- |
| Hand table | Definitions supply typed identities, spellings and relationships; ordinary dispatch and `run`'s parsing loop consume them. |
| clap | Declarations govern the same admission paths through `try_get_matches_from`, with typed references for rendering. Disable built-in help flags, help subcommands and version output; preserve the explicit version-envelope path and apply the flag guard. Other command tails retain their existing parsers. |

Prototype both in scratch worktrees with the same app-owned specimen
projection and result-selection mechanism. Use the specified inventory reach
and admission kinds; record any kind a candidate cannot express.

**E1 — Behavior.** Compare the help grammar cases and ordinary `run` inputs:
repeated options and paths, `--`, non-UTF-8 paths, `--timeout-ms 0`,
`--timeout-ms=5`, invalid values and the `machme` refusal. Include unprinted
options so the card selection cannot hide parser changes. Preserve argument
refusals before app-root access, `kind: "run"` envelopes on stdout, and
`OsString` request paths. Separate the specified help changes from additional
behavior changes; identify contract and test constraints on each difference.
Exercise CLI refusal and registry admission of the `machme` and `debuggable`
aliases through their respective readers.

**E2 — Build.** Choose a plausible placement and embed the cards there for
both candidates. Write the inventory from the same definitions in the same
step. Verify the committed generated copy against temporary build output
before signing, and exercise the offline contract join against that copy.
Establish generation without a signed app or the controller's contract stamp.
Consider shared declaration source in `build.rs`, a shared
dependency/build-dependency crate, compile-time assembly, or a
registered generator with `--check`. Try alternatives only as needed to
resolve placement; record reasons for ruling out or deferring each. Check
source-sharing limits, Cargo provenance/reuse, fresh and incremental builds,
and whether a stale card can ship. Record a concrete incompatibility if the
same placement cannot support both candidates.

**E3 — Linkage controls.** Use one exact governing-source mutation and an
independent behavior assertion in both candidates, with editorial references
held fixed. A flag rename can require the new spelling to be admitted and
the old spelling refused. Run this common procedure:

1. Establish the connected baseline: ordinary behavior and card agree and
   the check passes.
2. Mutate the governing source, rebuild and observe both changes. Do not edit
   help inputs or accept a new snapshot. If a freshness check refuses stale
   generated material, record it, regenerate with the owner, then observe the
   changed behavior and card.
3. Restore the baseline and render from a private, identical copy of the
   definition. Confirm unchanged behavior and card bytes; ordinary output
   checks may pass at this point.
4. Repeat the exact source mutation, leaving the copy untouched. Require the
   check to reject the behavior/card mismatch, or record the named build
   check that rejects the disconnected construction before producing an artifact.

Also remove a referenced definition and introduce an invalid relationship
between selected elements. Record the expected compile-time or build-time
rejection. Include the example projection's source and association checks;
changing an example field must change the emitted specimen and its selected
card field together. Inspect specifications for independent text overrides.

For `result`, change a selection rule and require the emitted fields, selected
process status and card to follow together, or the named check to reject the
change. Apply the disconnected-copy control to this relation too. Independently
exercise each result class, a delivery/admission failure beside a received
`finished` label, and admitted `finished` replies with failed attempts and
with integrity findings. Check field/status agreement and preserve the latter
cases' `true`/0 classification; do not derive test expectations from the same
selection definitions under test.

Add a literal spelling match beside the governing table and require the
exhaustiveness check to reject it. Record every mutation in the retained
form the inventory's mutation join uses. Run inexpensive renderer, contract
and focused behavioral checks wherever applicable; measure each check's cost
to select additional signed executions. Omitted checks remain `not_run`.
Rename an inventory identifier and update its references: require an unchanged
public snapshot. Change a governing value, admission condition or row order
without updating the corresponding contract facts: require the contract check
to reject each disagreement, reporting the affected facts and remaining prose.

Record source patches, commands, artifact identity, behavior, card bytes and
check diagnostics once per candidate. Unrelated compilation failures and
missing equipment do not count as rejected controls. Expected invalid-reference
errors establish only their named control, not changed runtime behavior.
Immediate rejection of an unchanged copy is a separate structural claim:
name that check and show its passing and rejected controls if it is claimed.

Report behavior differences, build placement, linkage controls, remaining
handwritten adaptation and dependency/maintenance cost for each candidate.

### E4: execution tools and reuse of cases

Compare existing `std::process` assertions, trycmd cases and snapbox-only
assertions against the same signed controller through the dispatcher. Use one
corpus: each implemented help topic and an unknown address, refused flag forms
at the top level and after `run`, both successful publishers, their trailing
help refusals, and non-UTF-8 and failed-write cases through any needed adapters.
Label baseline expectations when the artifact predates the proposed behavior;
apply the same candidate expectations to all three approaches.

Establish the following for each approach:

- Exact status, stdout and stderr assertions, with rejected wrong-status and
  wrong-stream controls. The trycmd adapter refuses missing `.stderr`
  expectations and refuses to run with `TRYCMD` set.
- Compatibility with dispatcher output ownership, temporary directories,
  parallel execution and the checkout lock.
- Reuse of one case corpus by execution checks, the `example`/`test-input`
  material and a card builder. Prototype the readers using a command line
  that saves the emitted example and submits it to `run`. Retain independent
  expectations and app-owned publisher inputs; invocation must not load test
  files. The existing [example cases](tests/suites/witness_contract/README.md#the-apps-own-example)
  supply the starting point.
- Association of each case with the inventory entries it exercises, derived
  from the case's arguments and required results for all three approaches.
  Record what each approach's case form makes derivable and what would need
  a declared association.
- The ownership, labeling and build-order implications of embedding an
  observed workload result: assess the dependency cycle when a binary embeds
  a result produced by executing itself. This is an assessment only; do not
  add a result-embedding stage.

Report assertion strength, adapters, corpus reuse and dependency cost, and
recommend a test approach.

## Open decisions

Resolve these at sequence step 3 using the card sources and completed comparisons.

| Decision | Evidence and required outcome |
| --- | --- |
| Exact projections | Review the `run` and `example` sketches and choose the flat rendering of the governing `result` relation, including how admission conditions are expressed without help-only wording. |
| Implementation and dependencies | Choose the governing argument definitions and result-selection mechanism, rendering/build placement, test approach and adoption or rejection of clap, trycmd and snapbox using E1–E4. |
| Permitted repair | E1 identifies additional behavior changes. Decide explicitly whether to repair discarded trailing arguments, always-refused matched flags, timeout clamping or last-path-wins behavior; they are not implicit help work. |
| Join and mutation details | Resolve any demonstrated need for operand bindings in the contract join. Select additional signed mutation checks using E3's cost measurements. |
| Non-derived tokens | Approve or reject each proposed label/placeholder exception. No general text override is permitted. |
| Refusal and write-failure output | Choose exact diagnostics per affected command, including any base-card reuse on stderr, and the failed-stdout-write policy. |
| Public status of help | Decide whether help's promises become contract rules; an addition requires the authored-tree procedure, stamps and support. |

## Verification

After the decisions, name the checks and expected outputs for the chosen
mechanism. The minimum acceptance evidence is:

- **Cards and linkage:** the complete four-card inventory; equality between
  the base card's entries and selectable topic addresses; the
  [linkage requirements](#linkage-requirements) for every selected element
  and E3's rejected controls.
- **Help behavior:** every grammar-table case on the signed controller and a
  copy outside its bundle. Compare recognized help byte for byte in working
  and absent-prerequisite states: missing/unwritable `HOME`, no registry,
  malformed and non-UTF-8 tails. Require status 0, exact card stdout and empty
  stderr. For ordinary commands use explicit fixtures and their own expected
  status and streams. Inspect the help path for absence of host facts,
  app-root, manifest, registry and runner access.
- **Flag guard:** the checks and rejected controls in its owning section,
  including disabled parser-library help defaults.
- **Publishers:** retain publication, refusal, write/flush-failure and
  publication-versus-admission assertions. `help example` invokes no publisher.
- **Result obligations:** E3's result cases and mutation controls pass;
  `help result` only prints the stored projection.
- **Inventory and residue:** every definition on a table-governed path is an
  entry and every other command has its unenumerated entry; the rejected
  literal-match control; agreement between each card and the entries it
  references; derived result-relation facts recomputed from the rows; the
  contract join and its E3 controls; case and mutation joins produced from
  retained data with omitted checks explicit; the baseline accepting
  reductions, refusing new members even at unchanged
  totals, and recording expanded enumeration through a reviewed refresh.
- **Build and comparison:** current cards in fresh and incremental builds,
  a stale-card control, and the E1–E4 decision records with failures and any
  unfinished work stated.
- **Suites:** `unit`, `integration` and `source_drift` at least, against one
  signed build from the implementing commit in a fresh `PW_TEST_OUT_DIR`, plus
  suites reached by parser changes. Follow [tests/AGENTS.md](tests/AGENTS.md).

## Consequences for existing material

Update affected owners together:

- Help/usage callers and text in `cli.rs`, `run_flow.rs`, `runner_commands.rs`,
  `example.rs` and `test_input.rs`; remove obsolete flag-help paths and variants.
- Result-selection callers and envelope/process-status construction in
  `run_flow.rs`, field definitions in `json_contract.rs`, and their supporting
  checks and citations in the [envelope](docs/contract/40-envelope.surface.md)
  and [refusal](docs/contract/15-refusals.surface.md) accounts.
- The top-level `--help` assertion in
  `example_prints_one_request_and_refuses_every_argument`, the `-h` assertion
  beside `parse_arguments`, and the `--help` observation in
  `refusals_before_selection_load_at_most_once_and_never_invoke_the_client`.
  Preserve publisher assertions and align the
  [integration invariants](tests/suites/integration/README.md).
- `check_cli_surface_agreement`, the controller README block and its
  synchronization rule in `controller/AGENTS.md`; the `cli_rs`, `D24`, `D30`
  and affected caller/argv citations in `docs/architecture.json`, followed by
  the owning regeneration.
- Contract support citations to `cli.rs`: `pub fn run` if dispatch moves, and
  authored help rules, stamps and support if help becomes public.
- The contract authoring tree for the citation form: allowed facts in
  [tree.py](docs/contract/tree.py), the authoring rules, and the citing
  nodes in the refusal, envelope, request and specimen surfaces.
- The inventory's owner: its generator registration and check, the residue
  baseline, and a README beside it describing the entry fields and the three
  joins as current behavior, the committed-copy check, and the baseline refresh
  command and review procedure.
- `docs/build.json` and `BUILD.md` for build changes; `DEPENDENCIES.md`, Cargo
  manifests and lock file for adopted crates; generator registration when used.

## Appendix: current findings

The findings were taken from source at `60e98ee5` and from
`dist/PolicyWitness.app` build 1447. That build
describes itself as `7cd93676-dirty`, so its exact source is not recoverable
from a commit; the behavior observed on it agrees with the argument handling
read at `60e98ee5`. The crate observations come from a throwaway Cargo package
outside the checkout, which was not retained; each one states the version it
was made on.

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

- The first argument alone selects top-level help; every argument after
  `help` is ignored.
- `run` collects host facts through `sysctlbyname` before it looks at its
  arguments, and recognizes `-h`/`--help` only if no earlier argument has
  produced an argument error.
- `run help` treats `help` as the request path. It resolves the app root,
  loads the evidence manifest and prints an envelope whose dossier includes
  host facts and app provenance.
- By source, not by execution: `cmd_runner` passes no arguments to
  `runner list` or `runner validate`, so `runner list --help` lists the
  registry and `runner validate --help` takes the registry lock and
  validates.
- With stderr attached to a pipe that has no reader, `help`, `run --help`
  and `bogus` exit 101. `runner help` with such a stdout exits 101 and
  prints a Rust panic message. `print_usage` uses `eprintln!` and the runner
  form uses `println!`. `example` and `test-input` use `write_all` and `flush`,
  exiting 2 on failure without a panic.

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
  Both publishers give exit 0 a publication meaning: one complete JSON
  document on stdout. The `example` guarantee also covers admission by the
  build's own `run`; `test-input` establishes publication without admission,
  execution or an effect.
- The contract also states `run`'s argument handling. The
  [controller pre-invocation refusal](docs/CONTRACT.md#contract-refusals-controller-consequence)
  selects `tool_error` for argument parsing and puts argument parsing before
  input reading. The
  [selection precedence rule](docs/CONTRACT.md#contract-request-options-precedence)
  says `--runner-mode` is parsed before the request is read and `machme` is
  refused. Neither states an exception for a help flag, although
  `run --help` exits 0 without an envelope. The
  [installation surface](docs/contract/50-installation.surface.md) likewise
  says `runner install` refuses `--bundle-id` and `--executable`.
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
shape, and `example::emit` requires no arguments. Command and flag spellings
have no enumerable definitions.

Some values do have a single governing definition: `RunnerKind::parse` and
`RunnerScope::parse` for their vocabularies, `DEFAULT_TIMEOUT_MS` and
`RUNNER_VERIFY_DEFAULT_TIMEOUT_MS` for defaults, `EXAMPLE_DOCUMENT` for the
example specimen (extracted by the contract generator), and
`test_inputs/read.json` with its `TARGETS` positions for the developer
input. The `run` exit statuses have no such definition. They arise at many
sites in `run_flow.rs` and their meanings are stated in an authored README
table and in the contract.

Additional parser behavior:

- `runner install` matches `--executable` and `--bundle-id`, takes a value
  for each, and then always refuses them.
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
  Cargo-generated artifacts fall under the Cargo provenance checks.

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

Observed limits:

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

## Appendix: executor questions at the start of execution

Recorded on 2026-11-15 before step 1, from the executor's preparation reply.
None blocked steps 1 and 2. The maintainer approved proceeding on these
recommendations; the step 3 stop for the [open decisions](#open-decisions)
stands.

- **Commit shape.** The experiment records will sit uncommitted in a shared checkout while you decide at step 3. I recommend one records commit at step 3 (E1–E4 records under `records/plain-help/`, linked only from the plan, with the plan's status and your decisions recorded there), then the implementation as a single atomic commit. If you want strictly one commit, I'll hold the records uncommitted through the pause.

- **Runner-mode vocabulary readers.** The plan names the CLI and registry readers, but four sites read this vocabulary:
  - `run --runner-mode` in `run_flow.rs`
  - the request's `runner.mode` in `runner_select.rs`, with its own `machme` refusal
  - `runner install --kind` in `runner_commands.rs`, with its own `machme` refusal
  - the registry's serde aliases in `runner_manager.rs`

  I recommend one table with reader-qualified rules covering all four, which replaces the derive aliases with table-driven deserialization at unchanged behavior. Otherwise two literal `machme` matches stay beside a governing table and the exhaustiveness check has to exempt them. The `runner install` tail itself stays unenumerated.

- **Result card labels.** Two rows of the result relation have variable labels.
  - **Refusal labels:** these are a closed set of static strings in `RunnerClientRun::failure` and `admit_reply`. I recommend enumerating them in the relation, which extends the refactor into `runner_client.rs`; the plan's source table doesn't name that file.
  - **Other admitted host labels:** these are open, defined by the Swift host. I'll bring that row to step 3 as a choice between a token exception and omitting the label.

- **Mutation data for the shipped tree.** E3 runs on prototypes. I recommend rerunning the chosen candidate's mutations against the implementing tree, so the retained mutation join describes shipped entries. The losing candidate's records stay in `records/` only.

- **Parser-library guard control.** The "built-in help enabled" rejected control exists only for a clap declaration. If the hand table is chosen, I recommend recording that control from the prototype and marking it not applicable in final verification, not keeping a standing check for a library the tree doesn't use.

- **Plan closeout.** I recommend leaving retirement of the plan and its records to you after acceptance, as separate commits like the earlier plans.
