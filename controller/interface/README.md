# `controller/interface/`

The interface inventory: a committed, machine-readable record of every
definition that governs the controller's command line and `run` result,
together with the build-time code that renders it and the help cards.
The definitions themselves are Rust tables in
[../src/interface/](../src/interface/); dispatch, help selection, the
`test-input` form selection, the argument parser `run` and `test-input run`
share, every reader of the runner-kind vocabulary and result selection read
them. The [controller README](../README.md#cli-surface-contract)
describes the command line they produce.

| File | Owner | Content |
| --- | --- | --- |
| [cards.rs](cards.rs) | authored | Each card's explicit layout, selected definitions and typed references. |
| [inventory.rs](inventory.rs) | authored | The inventory writer and the facts it derives by evaluating result selection. |
| [inventory.json](inventory.json) | generated | The inventory: entries, the result relation, the example projection and the four cards. |
| [joins.json](joins.json) | generated | Which entries each corpus case reaches and what each recorded mutation moved. |
| [residue.json](residue.json) | generated baseline | Named members of the residue classes, the inventory's identifiers and recorded expansions. |
| [mutations.json](mutations.json) | authored record | Retained mutation observations and the declared case associations. |

## How the cards and the inventory are built

[build.rs](../build.rs) compiles the binary's own definition files a second
time, with [example_document.rs](../src/example_document.rs),
[json_contract.rs](../src/json_contract.rs) and
[run_result.rs](../src/run_result.rs). It renders the four cards and the
inventory into Cargo's output directory. The binary embeds the cards from
there, and `policy-witness help` prints those bytes.

The renderer has one branch per card. `RUN_OPTION` selects the run card's
option and its reader supplies the admitted words. `RESULT_FIELDS` selects
the result columns in order. The example card reads named phase and attempt
fields from the constant `example` publishes. Each result line uses the
serialized fields of the result that `run`'s constructor builds from one
selection; serialized column names are resolved once for the card.

Rendering records typed references alongside the text. The inventory writer
converts those references to external identifiers; rendering does not read
the inventory or construct identifiers. Command headings must agree with the
topic's command, and the selected run option must take runner-kind words.
The renderer also refuses a topic address that is empty, shared or starts
with the flag prefix, and a base card that is not exactly the topic addresses.

The build script then compares the inventory with `inventory.json` and stops
Cargo when they differ. Every `cargo build`, `cargo check` and `cargo test`
of the package makes that comparison, so a build cannot embed a card that
the committed inventory does not show.

## Entries

Each entry of `entries` records:

- `id`: the table and variant the card specifications reference, such as
  `run.option.runner_mode`. It does not change when a spelling does, and it is
  never printed on a card.
- `spellings`: what the reader compares an argument or value with; empty for
  a rule that has no spelling of its own, such as the request path.
- `relationships`: the command an option belongs to, an option's value rule,
  a command's or a form's tail rule, the form a test control belongs to with
  its member name and value rule, the kind a word resolves to.
- `reader`: the path and symbol of the code whose behavior the entry
  describes, and for a runner-kind word the reader it is qualified by.
- `kind`: the admission kind, taken from the value dispatch or parsing acts
  on. `admits`: the spelling is accepted and used. `refuses_always`: what
  matches is refused. `discards`: accepted and ignored. `alias`: the named
  reader resolves the spelling to a canonical value. `unenumerated`: the
  arguments go to a parser whose definitions are not in the tables.
- `cards`: the cards that reference the entry, possibly none.

Enumeration covers top-level dispatch, help selection, the forms of
`test-input`, all of the argument handling of `run` and `test-input run`, and
the runner-kind vocabulary for its four readers. A `run.control` entry is an
argument of `test-input run` alone: under `run` its spelling is an unknown
flag, and the inventory writer refuses a definition that classifies otherwise.
The `runner` tail and the tail of `test-input read` are one `unenumerated`
entry each. No card references a form or a control.

`result` holds the relation that selects `result.normalized_outcome`,
`result.ok` and the one exit status that is both `result.exit_code` and the
process status. Each row has its inputs, its outputs and its place in
first-match order. `derived` is computed by evaluating the selection function
over every class, every refusal and, for an admitted capture, an absent host
label, each label the controller spells and one it spells nowhere: which
output is a function of which, which rows can produce the same outputs, and
which inputs change no output. `example` holds the projected phases and
attempts. `cards` holds each card's bytes and references.

The offline generator recomputes every ordered output dependency and every
pair of rows sharing outputs, including their counterexamples and shared
values. Inputs absent from row predicates, such as the integrity-issue
count, are evaluated only by the build script: it holds the class and host
label fixed while varying the count. The build's inventory comparison holds
those derived facts; the offline row check does not independently establish
them.

## Joins

**Contract.** A node of the [contract tree](../../docs/contract/README.md)
cites entries in an `interface` fact, which is support metadata outside the
public snapshot. The contract generator resolves each identifier and compares
the node's structured facts with the entry: literal `set_value` effects on
result fields, `test` comparisons with literals, listed `values`, the effects
and applicability the node inherits, and the order of first-match cases.
Two operand roots are bound by name, `envelope.result.` for the result fields
and `envelope.data.runner_result` for the admitted host reply.
`docs/generate_contract_stamps.py --interface-report` prints, for each citing
node, what was compared and which `free.*` facts and prose stand beside it.
Resolving an identifier gives that prose no credit. The report includes
inherited `free.when` text and lists the row's admission class as uncompared:
the contract has no structured operand bound to that class. A positive host
presence conjunct can support the fallback test; negated or disjunctive
mentions of presence cannot. The complete applicability expression remains
uncompared.

Follow [selector precedence](../../docs/REQUEST.md#contract-request-options-precedence)
from a run-option change and
[result selection](../../docs/RESPONSE.md#contract-envelope-data-select) from a
result-row change. [CONTRACT](../../docs/CONTRACT.md) indexes these associations
alongside source and check support. The complete statement retains the
applicability and free conditions that the join leaves uncompared.

**Cases.** `joins.json` associates each case of the
[case corpus](../integration/interface_cases.json) with the entries it
reaches. The association is derived from the case's argument vector, a
successful `example` and, for a `run` envelope, the three required result
fields. Argument derivation stops at the first refusal or terminator; for a
control that is a missing value, a value its rule does not admit or a second
occurrence.
Where two rows select the same fields, or a word is read beyond the
enumerated CLI, `mutations.json` holds a declared association with its
reason. Request-file staging alone establishes no reader reach: request
admission and selector ordering are outside the inventory. The join
reports entries no case reaches, and separately entries whose reaching cases
all supply test-owned files or environment. The second is a fact about the
retained cases, not a claim that production inputs cannot reach the entry.

**Mutations.** `mutations.json` retains each mutation that was applied to a
governing source: the entry, the change, and for each of the card, the
contract check and the cases one of `not_run`, `unchanged`, `changed` or
`failed`. The join reports a mutation that moved the cases while both other
checks ran and stayed unchanged,
and entries no mutation names.

## Residue

`residue.json` records named members and counts for four classes: entries
whose kind is not `admits`, by kind and reader; entries no card references;
entries reached only by cases with test-owned inputs; and non-derived tokens
on a card, by card and role. Whitespace is layout and is not a token.
Membership is compared, not totals: a member that moves between classes is an
addition.

## Commands

Run from the repository root.

| Command | Effect |
| --- | --- |
| `tests/lib/python.sh docs/generate_interface.py --check` | Writes nothing. Refuses an inconsistent inventory, a stale `joins.json` or `residue.json` and any residue addition. It does not run Cargo; the build script is the check that `inventory.json` matches the definitions. |
| `tests/lib/python.sh docs/generate_interface.py` | Rewrites `joins.json` and `residue.json` from the committed inventory. Accepts residue reductions and refuses additions. |
| `tests/lib/python.sh docs/generate_interface.py --refresh-inventory` | First replaces `inventory.json` from a build-script run in an isolated Cargo target directory, then the above. The build script's stale refusal names this command. |
| `tests/lib/python.sh docs/generate_interface.py --refresh-residue` | Also accepts residue additions. Combine with `--refresh-inventory` after a definition change that adds members. |
| `tests/lib/python.sh docs/generate_interface.py --refresh-residue --expand ENTRY` | Records that `ENTRY`, an `unenumerated` entry of the baseline that is gone, was replaced by the entries that are new. The record separates newly enumerated behavior from changed behavior. |

A refresh is reviewed as a diff of `residue.json`: each added member is read
against the definition change that produced it, and a changed card is read in
`inventory.json`. Changing what a card selects, and changing behavior, each
need their own review; accepting the baseline approves neither.

## What the checks establish

The [interface literal rule](../../tests/suites/source_drift/README.md#interface-literals)
refuses a string or character literal that is compared, matched or searched
for inside a function the inventory names as a reader, a literal in the card
renderer equal to a card token or line, and an aliased runner-kind word
written outside the tables. It is a token scan. A comparison against a
constant defined elsewhere, or a card element assembled from pieces or
printed from a number, is outside it; the generator's check that every card
token comes from a referenced entry catches the second once the definition
and the copy disagree.

The corpus and the unit test of the result classes state their expectations
literally. They hold the behavior; the inventory holds what the definitions
say. Agreement between a card and execution is tested from the binary's own
output in `help_cards_agree_with_execution`.
