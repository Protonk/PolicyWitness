# Generate `policy-witness help` cards from the executable interface

Status: proposed. Nothing here is implemented. The main sections state the
requirements, first deliverable and work to perform. Detailed source and
crate observations, with their provenance limits, are in the
[findings appendix](#appendix-current-findings).

The [settled requirements](#settled-requirements) are maintainer decisions.
Card sketches and mechanisms remain proposals; [experiments](#experiments)
supply evidence for the [open decisions](#open-decisions). Keep those statuses
distinct when recording results and choosing the implementation.

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
delivered at invocation without consulting operational state. Help is the
word `help` as the first argument and nothing else: such an invocation exits
0 whatever follows it, and no `--help` or `-h` flag is help anywhere.

The primary purpose is to force explicit, testable projections of executable
behavior and obligations into a plain view. Reader usefulness is secondary.
Those projections can later replace duplicated descriptive material in the
CONTRACT while retaining the explanation of their boundaries and meaning.
This plan establishes the projections; reducing the CONTRACT is later work.

## Settled requirements

These are the maintainer's decisions. They are not reopened by this plan.

1. **Bare card output.** Help selects and prints simple cards: specific
   information for recognized subjects and a bare fallback, the base card,
   for anything unrecognized. The base card lists available help topics.
   Selection stays deliberately limited. An incidental help invocation adds
   text to a CI log and causes no usage failure.
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
5. **Word form only.** The [help grammar](#help-grammar) is settled: `help`
   prints the base card, `help` followed by a topic prints that topic's
   card, and `help` followed by anything else prints the base card. The
   topics are `run`, `example` and `result`. Help has no
   flag form and takes no flags. Requirement 1's protection for an
   incidental invocation therefore covers the word form; `--help` and `-h`
   are ordinary arguments wherever they appear, and the implementation is
   guarded against acquiring a flag form.

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
- Observed query answers, attempt outcomes and transcripts are excluded
  from the first cards. E4 still assesses their ownership and build-order
  implications for later work.
- No release, notarization or publication step.

## First implementation and card ledger

Completion requires four cards: the base card and the `run`, `example` and
`result` topic cards. Their addresses and responsibilities are fixed; approve
the exact projections and governing mechanisms before implementation begins.
Completion also requires the [interface inventory](#interface-inventory-and-residue)
built from the same definitions, with its joins and ratchet.

The base card's responsibility in this implementation is to list every
available help topic, one address per line, from the same definitions that
select their cards. Its initial order is:

```text
run
example
result
```

It has no heading, command directory or placeholder for an unavailable topic.
Additional responsibilities can be considered later.

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
attempt or guarantees its outcome. Both end with one newline. Review the
sketches for usefulness before selecting their final content.

The `result` card projects `run`'s result-selection obligations: how a selected
controller disposition determines `result.normalized_outcome`, `result.ok`,
`result.exit_code` and the corresponding process status. It is a help topic,
not an additional operational command. Its
[projection and controls](#result-projection) are defined below.

| Element | Governing source and status | Reader purpose and linkage work |
| --- | --- | --- |
| Base-card entries and topic addresses | The topic definitions consumed by help selection; declared addressing behavior. Command topics share their command's spelling definition. | Lists exactly what the reader can ask for. Render the complete registered topic set through typed references; renaming a command moves its topic address and displayed name together. |
| `run`, `example` on their cards | Dispatch definitions currently expressed in `cli::run` in [cli.rs](controller/src/cli.rs); declared command recognition. | Identifies each card. E1 compares the hand-table and clap ways to make these definitions enumerable and usable by both dispatch and rendering. |
| `--runner-mode`, `standard`, `byoxpc` | `parse_arguments` in [run_flow.rs](controller/src/run_flow.rs) and `RunnerKind::parse` in [runner_manager.rs](controller/src/runner_manager.rs); declared argument admission. | Shows the option and accepted values. Share the governing spelling and vocabulary with rendering; legacy serde registry aliases do not establish CLI acceptance. |
| Example phases, attempt actions and targets | `EXAMPLE_DOCUMENT` in [example.rs](controller/src/example.rs), which the publisher emits; declared content of this build's specimen. | Shows the requested file workload. Project the same constant and preserve its phase/action associations; do not maintain a second specimen summary. |
| `result` topic address | The topic definition consumed by help selection; declared addressing behavior. | Names the result projection without adding a `result` command or a `run-result` alias. |
| Result conditions, outcome labels, `ok` and exit statuses | Local refusal helpers, `admit_reply`, `runner_outcome`, completion and envelope/exit selection in [run_flow.rs](controller/src/run_flow.rs); declared controller reporting obligations. Field names belong to [json_contract.rs](controller/src/json_contract.rs). | Makes the relation between disposition and published result explicit. One governing selection mechanism must determine the fields and process status and supply their card projection; copied prose or a rendering-only classification table does not qualify. |
| Order, indentation and final newline | Editorial arrangement and renderer layout. | Group elements according to relationships in their governing definitions. Layout cannot imply an unsupported relationship or an observed outcome. |

A tested command line that saves the example and passes it to `run` remains
an alternative candidate for the `example` card. E4 evaluates its reuse of
cases; file placeholders and labels still need the token decision below.
Observed workload results are assessment material for E4, not first-card
content.

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
These are declared selection rules, not observed workload results.

The later CONTRACT reduction has a bounded target: the repeated mapping of
dispositions to outcome, boolean and exit status can become an executable
projection. Prose explaining admission and what run success establishes still
has a role. This plan does not replace that explanation with a list of labels.

### Editorial representation

Selection and ordering live in a card specification containing typed
references to governing definitions, never spelling lists, replacement text,
display-name fields or lookups such as `lookup("run")`. Internal identifiers
are not printed. A schematic `Command::Run` supplies both the command-topic
address and its displayed name; `RunOption::RunnerMode` selects the option
while omitting `RunOption::TimeoutMs`. The base card includes every registered
topic; editorial ordering cannot advertise a missing card or omit a topic.

The recognizer, dispatcher and parser must consume the same definitions on
the relevant paths. A help-only table beside literal parsing matches does
not qualify. For specimen content, rendering selects fields from the same
app-owned constant the publisher emits. Renaming a selected spelling or
changing a selected specimen field changes both behavior and the card without
editing its selection. Removed or misassociated references are rejected by
compilation or build validation.

Changing selected references or their order changes the projection. It does
not author new wording for a fixed element. Labels and placeholders such as
`<request.json>`, `<n>`, `Usage:` and `default:` remain unresolved exceptions
unless derived substitutes exist. A governing default value alone does not
supply the word explaining that it is a default.

### Interface inventory and residue

The build that renders the cards also writes an interface inventory: a
machine-readable record of every definition the governing tables hold,
whether or not a card selects it. A card is a selection from the inventory;
the residue is what remains. The inventory is a build product for review and
checks. It is not help output, adds no topic or flag, and is not read at
invocation.

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
| Refuses always | The spelling is recognized so that it can be refused. | `--runner-mode machme`; `runner install --executable` and `--bundle-id` |
| Discards | Input is accepted and ignored. | The tail after `version`, `runner list` and `runner validate` |
| Reader-specific alias | One reader accepts a spelling another refuses. | The registry reader's `machme` and `debuggable` |
| Unenumerated | A command's tail is still parsed by hand and its contents are not listed. | `runner` and `test-input` until a table governs them |

Enumeration is exhaustive on every path a governing table covers: there the
recognizer, dispatcher and parser match no spelling that is not a
definition, and a check rejects a literal match placed beside the table. A
path no table covers appears as one unenumerated entry for its command.
The first implementation covers top-level dispatch, help selection, all
`run` argument handling, the runner-mode vocabulary across CLI and registry
readers, and the definitions needed for the `example` and `result` projections.
The `runner` and `test-input` tails remain unenumerated. In particular,
`--executable`, `--bundle-id` and the `runner list` tail stay within the
unenumerated `runner` entry rather than receiving individual entries.

Enumeration and behavioral repair are separate decisions. Moving a refusal
or discarded argument into a governing definition preserves its behavior;
changing that behavior requires the permitted-repair decision. Reader-qualified
rules preserve distinctions such as `machme` being refused by CLI parsing and
accepted by registry reading.

Commit the generated inventory beside its generator's README and residue
baseline. The build regenerates into temporary output and compares it with
the committed copy before signing. Offline contract checks read the committed
copy. E2 must establish that the cards and inventory can be generated without
a signed app or the controller's contract stamp, avoiding a dependency cycle
between inventory generation and contract checking.

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
  prose. In this implementation the citing nodes are the
  ones for the elements the four cards project: the
  [controller pre-invocation refusal](docs/CONTRACT.md#contract-refusals-controller-consequence)
  and the envelope's outcome and exit rules, the runner-mode option and the
  example emission. No contract meaning changes and no text is removed.
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
  for each check. Run inexpensive renderer, contract and focused behavioral
  checks wherever applicable; choose additional signed executions from E3's
  cost measurements. Report when a mutation changes a case and leaves the
  other checked outputs unchanged, with any omitted checks explicit.

A residue baseline records member identifiers and counts separately for:

- Non-`Admits` entries, by admission kind and reader.
- Entries referenced by no card.
- Entries with reaching cases that all use test-owned inputs.
- Explicit non-derived token exceptions, by card and token role. Whitespace
  is layout and is not counted as a token exception.

Compare membership as well as totals: removing one member cannot silently
authorize a different member. Generation accepts reductions and lowers the
committed baseline to the current sets; it refuses additions until an explicit
refresh, following the reduction rule of
[free_text.json](docs/contract/free_text.json). Expanded enumeration has a
refresh path that records which opaque entry was replaced and distinguishes
newly exposed behavior from changed behavior.

The inventory generator owns the baseline. Its adjacent README documents one
refresh command; refresh requires a maintainer-reviewed diff of members and
counts. Normal generation never accepts additions automatically. An uncarded
option or a reader alias may remain intentionally; a baseline reduction does
not authorize enlarging cards or changing admission behavior.

## Help grammar

This grammar is settled (requirement 5):

- Compare the first argument with `help` as an exact `OsString`, before host
  facts, app-root resolution or operational dispatch. A match invokes help.
- The second argument alone selects a registered topic. An absent, unknown,
  differently cased, empty, flag-shaped or non-UTF-8 address selects the base
  card. Ignore every later argument.
- Nothing else invokes help. `--help` and `-h` are ordinary arguments, and
  the word `help` has no special meaning after a command.

Recognized help exits 0 with one card on stdout and empty stderr, subject to
the settled stdout-failure exclusion. The table specifies streams separately.
For refusals, "diagnostic" means the text selected at the decision checkpoint
when stderr is writable; it may include the base card on stderr. That does
not make the invocation help or change its failing status.

| Arguments after `policy-witness` | Status | stdout | stderr |
| --- | --- | --- | --- |
| `help` | 0 | Base card. | Empty. |
| `help run`, `help run junk`, `help run --bad`, `help run -- x` | 0 | `run` card. | Empty. |
| `help example`, `help example extra` | 0 | `example` card; no publisher is invoked. | Empty. |
| `help result`, `help result extra`, `help result --bad` | 0 | `result` card; no run or result evaluation is performed. | Empty. |
| `help bogus`, `help bogus run`, `help RUN`, `help run-result`; any other unregistered address | 0 | Base card. | Empty. |
| `help --run`, `help --help`, `help -h`, `help -- run`, `help ''`, `help` followed by a non-UTF-8 token | 0 | Base card. | Empty. |
| `--help`, `-h`; no arguments, `bogus`, `HELP`, `result` | 2 | Empty. | Usage diagnostic. |
| `run --help`, `run -h`, `run x --help` | 2 | Ordinary `tool_error` argument-refusal envelope. | Empty. |
| `runner help`, `runner --help` | 2 | Empty. | Unknown-runner-command diagnostic. |
| `runner install --help`, `runner status --help`, `runner reconcile --help`, `example --help`, `example -h`, `example help`, `test-input --help`, `test-input help` | 2 | Empty. | Each command's refusal diagnostic. |
| `runner list --help`, `runner validate --help`, `version --help`, `--version --help` | Ordinary command status. | Ordinary output, not help output. | Ordinary command diagnostics. |
| `run help` | Ordinary `run` status. | Ordinary envelope for the request path `help`. | Ordinary `run` behavior. |

The accepted CLI changes: top-level flag forms, `run` flag forms and
`runner help`/`runner --help` become refusals. Scripts using them under
`set -e` can start failing. This does not narrow the existing contract's
publisher promises: exit 0 from `example` or `test-input` still means a
complete document. Ordinary `run` argument parsing keeps its contracted
`tool_error` envelope, losing the current unstated help exception.

Commands that discard trailing arguments still do so: `runner list --help`
lists the registry and `runner validate --help` locks and validates it.
Changing that behavior is a separate repair decision. `run help` still reads
the file named `help`; the help-input promise applies only to leading `help`.

### Flag guard

- Remove existing help recognition from `cli::run`, `parse_arguments` and
  `cmd_runner`, including `Arguments::Help` and `RunOutput::Help`, leaving the
  single leading-word path. A flag cannot select a help card on stdout;
  refusal diagnostics may reuse the base card on stderr.
- Exercise `--help` and `-h` at the top level and after every command and
  subcommand, asserting ordinary status and streams separately.
- Reject topic addresses beginning with `-`. If a parser library is used,
  inspect its declaration for a long `help` flag, short `h` flag or enabled
  built-in help subcommand and reject them.
- Demonstrate each guard with a rejected control: a restored flag-help arm,
  a flag-shaped topic address and a parser declaration with built-in help
  enabled.

## What would demonstrate a real connection

Every selected element names its governing source and satisfies these five
properties. E3 supplies one shared control procedure for both parser candidates.

| Property | Required evidence |
| --- | --- |
| Behavior uses the source | The definition actually admits, refuses, dispatches or emits what the card describes. A rendering-only declaration does not qualify. |
| The card follows the source | A governing-source mutation changes the independently observed behavior and card, or a named freshness/linkage check refuses the build. No help-specific input is edited. |
| A fixed element has no independent text | The editorial specification selects references or source fields and cannot rewrite their text. Named label/placeholder exceptions remain explicit. |
| The check can reject a fault | Each supporting check has a rejected control, including the disconnected-copy trial in E3. An unrelated failure supplies no linkage evidence. |
| Status is stated | Record declared obligations separately from observations. First-card content contains no observed workload results. |

A snapshot establishes output equality, and a citation establishes that a
source exists; neither establishes this connection. Likewise, passing help
cases in a broken environment does not alone prove absence of operational
work. The [verification](#verification) requires both executions and structural
inspection. E3's controls demonstrate the tested disconnection, not every
possible independent edit.

## Sequence

1. Review the card sketches and ledger for usefulness and derivation gaps.
   Fix the common elements and cases for comparison, including the `result`
   relation, the inventory's entry form and the paths it enumerates. The three topic names, help grammar and base card's topic-listing
   responsibility are settled.
2. Perform E1–E3 as the shared comparison below, and E4 as the execution-tool
   comparison. All four remain required for the small initial inventory.
3. Bring the results and [open decisions](#open-decisions) to the maintainer.
   Approve the exact four-card projections and the implementation, dependency
   and output decisions. Amend the plan with
   those choices before implementation. Missing comparisons remain unfinished
   work; a concrete incompatibility or rejected control can establish a
   negative result for a candidate.
4. Implement the chosen approach, update affected materials together, and
   complete the [verification](#verification). Completion requires all four
   cards, the inventory with its joins and ratchet, and their supporting
   evidence.

Reconsider if no useful element can meet the connection standard, linking
it requires an unapproved contract change, or the useful inventory depends
on observations excluded from the first implementation.

## Experiments

### E1–E3: one comparison of definitions, build and linkage

Use the same selected cards, typed references, ordinary argument cases and
independent expected results for both candidates:

| Candidate | Governing implementation |
| --- | --- |
| Hand table | Definitions supply typed identities, spellings and relationships; ordinary dispatch and `run`'s parsing loop consume them. |
| clap | Declarations govern the same admission paths through `try_get_matches_from`, with typed references for rendering. Disable built-in help flags, help subcommands and version output; preserve the explicit version-envelope path and apply the flag guard. Other command tails retain their existing parsers. |

Both use the settled leading-word help rule, the same app-owned specimen
projection and the same governing result-selection mechanism. Both must
enumerate every definition on the paths they govern and express each
admission kind as the value the parser acts on; record a kind a candidate
cannot express. The parser
comparison does not make clap responsible for result classification.
Prototype in scratch worktrees. Apply the following stages to
each candidate that reaches them; record concrete blockers for the others.
A working hand table or a small card inventory is not a finding against clap.

**E1 — Behavior.** Compare the help grammar cases and ordinary `run` inputs:
repeated options and paths, `--`, non-UTF-8 paths, `--timeout-ms 0`,
`--timeout-ms=5`, invalid values and the `machme` refusal. Include unprinted
options so the card selection cannot hide parser changes. Preserve argument
refusals before app-root access, `kind: "run"` envelopes on stdout, and
`OsString` request paths. Separate the settled help changes from additional
behavior changes; identify contract and test constraints on each difference.

**E2 — Build.** Choose a plausible placement and embed the cards there for
both candidates. Write the inventory from the same definitions in the same
step. Verify the committed generated copy against temporary build output
before signing, and exercise the offline contract join against that copy.
Establish generation without a signed app or the controller's contract stamp.
The first hand-table build is a comparison baseline, not an
architecture decision. Consider shared declaration source in `build.rs`, a
shared dependency/build-dependency crate, compile-time assembly, or a
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

The shared result compares behavior differences, build placement, linkage
controls, remaining handwritten adaptation and dependency/maintenance cost.
It supports the mechanism and dependency decisions without repeating separate
acceptance rules for each candidate.

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
  observed workload result in later work. Assess the cycle in which a binary
  would embed a result produced by executing itself; no result-embedding
  stage is added to the first implementation.

The result compares assertion strength, adapters, corpus reuse and dependency
cost, and recommends a test approach. Excluding observations from the first
cards does not omit this comparison or decide against either test dependency.
Keep findings about future observed content separate from first-card acceptance.

## Open decisions

Resolve these at sequence step 3 using the ledger and completed comparisons.
The word-only grammar, topic names and responsibilities, base-card purpose,
four-card completion requirement and exclusion of observed workload results
from the first cards are fixed for this plan.

| Decision | Evidence and required outcome |
| --- | --- |
| Exact projections | Review the `run` and `example` sketches and choose the flat rendering of the governing `result` relation, including how admission conditions are expressed without help-only wording. Confirm the obligation or declared content each element exposes. The base card lists exactly `run`, `example` and `result`. |
| Implementation and dependencies | E1–E4 support the governing argument definitions and result-selection mechanism, rendering/build placement, test approach and adoption or rejection of clap, trycmd and snapbox. Missing comparison evidence cannot close a decision. |
| Permitted repair | E1 identifies additional behavior changes. Decide explicitly whether to repair discarded trailing arguments, always-refused matched flags, timeout clamping or last-path-wins behavior; they are not implicit help work. |
| Inventory implementation | E2 establishes the committed-copy check and generation without a signed app or controller contract stamp. Resolve any demonstrated need for operand bindings in the contract join. E3's cost measurement selects additional signed mutation checks; inexpensive renderer, contract and focused behavioral checks remain required wherever applicable. Inventory reach, custody, citation status and baseline ownership are fixed in the inventory section. |
| Non-derived tokens and build identity | Decide any individually named label/placeholder exception and whether contract identity is useful on a topic card. No general text override is permitted. |
| Refusal and write-failure output | Choose exact diagnostics per affected command and the failed-stdout-write policy. A base card may be included on stderr for a refusal while status and stdout remain those in the grammar table. Distinguish this reuse from successful help. |
| Public status of help | Decide whether help's promises become contract rules. Publisher meanings remain intact; a public-contract addition requires the authored-tree procedure, stamps and support. |

## Verification

After the decisions, name the checks and expected outputs for the chosen
mechanism. The minimum acceptance evidence is:

- **Cards and linkage:** the complete four-card inventory; equality between
  the base card's entries and selectable topic addresses; the five connection
  properties for every selected element and E3's rejected controls.
- **Help behavior:** every grammar-table case on the signed controller and a
  copy outside its bundle. Compare recognized help byte for byte in working
  and absent-prerequisite states: missing/unwritable `HOME`, no registry,
  malformed and non-UTF-8 tails. Require status 0, exact card stdout and empty
  stderr. For ordinary commands use explicit fixtures and their own expected
  status and streams. Inspect the help path for absence of host facts,
  app-root, manifest, registry and runner access; fixed passing cases alone
  do not establish that structural property.
- **Flag guard:** the checks and rejected controls in its owning section,
  including disabled parser-library help defaults.
- **Publishers:** retain publication, refusal, write/flush-failure and
  publication-versus-admission assertions. `help example` invokes no publisher.
- **Result obligations:** cover every selected result class, delivery/admission
  precedence, agreement of emitted fields with the returned process status,
  and independence from failed attempts or integrity findings on admitted
  `finished` replies. Retain E3's result-rule and disconnected-copy controls.
  `help result` only prints the stored projection.
- **Inventory and residue:** every definition on a table-governed path is an
  entry and every other command has its unenumerated entry; the rejected
  literal-match control; agreement between each card and the entries it
  references; derived result-relation facts recomputed from the rows; the
  contract check resolving every cited identifier, with a rejected control
  for a fact, admission condition or row order that disagrees with its entry;
  identifier-only changes leaving the public snapshot unchanged; the case
  and mutation joins produced from retained data with omitted checks explicit;
  the baseline accepting reductions, refusing new members even at unchanged
  totals, and recording expanded enumeration through a reviewed refresh.
- **Build and comparison:** current cards in fresh and incremental builds,
  a stale-card control, and the E1–E4 decision records with failures and any
  unfinished work stated. The first cards contain no observed workload results.
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
  and [refusal](docs/contract/15-refusals.surface.md) accounts. Preserve their
  meanings; later CONTRACT reduction is outside this implementation.
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
  nodes in the refusal, envelope, request and specimen surfaces. Exclude the
  `interface` support metadata from the public snapshot; retain comparisons
  of inherited conditions and first-match ordering.
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
was made on and is cheap to repeat.


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
  Both publishers give exit 0 a publication meaning: one complete JSON
  document on stdout. The `example` guarantee also covers admission by the
  build's own `run`; `test-input` establishes publication without admission,
  execution or an effect. Recognizing a trailing help flag would therefore
  change both exit-0 promises, not just an argument-refusal rule.
- The contract also states `run`'s argument handling. The
  [controller pre-invocation refusal](docs/CONTRACT.md#contract-refusals-controller-consequence)
  selects `tool_error` for argument parsing and puts argument parsing before
  input reading. The
  [selection precedence rule](docs/CONTRACT.md#contract-request-options-precedence)
  says `--runner-mode` is parsed before the request is read and `machme` is
  refused. Neither states an exception for a help flag, although
  `run --help` already exits 0 without an envelope. The
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
