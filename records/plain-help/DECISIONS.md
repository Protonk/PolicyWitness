# Plain help: decisions for sequence step 3

The seven open decisions of `PLAIN-HELP-PLAN.md`, each with what the
experiments in [RESULTS.md](RESULTS.md) showed, the options and a
recommendation. Three further decisions that the experiments raised follow
them. Nothing here is decided until the maintainer records a choice in the
plan.

## 1. Exact projections

**`run` and `example`.** Both sketches render exactly as the plan shows, with
no non-derived token. Recommended: approve as shown.

**`result`.** Options, all without a token exception:

| Option | Shape | Cost |
| --- | --- | --- |
| A, prototyped | one header line of field names, then one line per fixed label: `bad_request false 1` … (16 lines) | none further |
| B | group by `ok` and `exit_code`, labels indented under each pair | a second layout rule; the same tokens |
| C | A without the twelve admission-refusal labels (4 lines) | the card no longer shows which labels are refusals; the relation still enumerates them |

Recommended: A. Three limits to accept with it:

- The row for another admitted host label prints nothing. Its label is open,
  so a line would need a placeholder, which is a token exception.
- The card does not say "process status". The exit field and the process
  status are one value by construction, and the card's only name for it is
  the field name `exit_code`. Naming the process status needs a label
  exception.
- `tool_error false 2` is the controller's own row. An admitted host reply
  labelled `tool_error` selects `false` and 1; no card line can say so
  without the open-label row.

## 2. Implementation and dependencies

Recommended: the hand table, the `build.rs` placement, the JSON corpus run
by `std::process`, and none of clap, trycmd and snapbox.

- **Hand table over clap.** Both meet the linkage controls and print the same
  cards. clap changes behavior the plan does not ask for (`--timeout-ms=5`
  admitted, the request path lost from argument-refusal dossiers, changed
  diagnostic texts, the `machme` hint gone), cannot take a tail without
  consuming a leading `--`, cannot express three of the five admission
  kinds, needs a guard that was wrong on the first attempt, and adds four
  shipped packages and 618,800 bytes. What it offers in return is refusal
  diagnostics rendered from the declaration.
- **`build.rs` compiling the binary's own definition files.** No new crate,
  no lock change, the existing Cargo judgments unchanged.
- **`std::process`.** It alone holds all 64 cases with exact assertions and
  JSON pointer equality. snapbox adds nothing for those and cannot hold a
  stdout without a reader. trycmd cannot hold four cases, passes an unstated
  stderr, and costs 51 lock packages together with snapbox.

Commitments that come with the recommendation:

- The registry reader of `RunnerKind` becomes a hand-written `Deserialize`
  that asks the table, in place of serde's derive and its two aliases. Stored
  spellings and accepted aliases are unchanged.
- `docs/contract/record_definitions.py` admits that projection by name, as it
  does `ReplyError`.
- `EXAMPLE_DOCUMENT` moves to `controller/src/example_document.rs`.
- `runner install --kind` reads its value through a small function of its
  own, so the literal scan can govern it; the rest of that parser stays
  unenumerated.

## 3. Permitted repair

E1 found no behavior change in the hand table beyond the help grammar. The
four candidates for repair, each present in the residue baseline by name:

| Behavior today | Repair | What it would change |
| --- | --- | --- |
| `version --help`, `--version x` print the envelope; `runner list --help` lists the registry; `runner validate --help` locks and validates | refuse a tail | exit 2 where callers now get exit 0 and an operation; the `runner` two are inside the unenumerated tail and need its parser changed |
| `--runner-mode machme` is matched to be refused with a hint; `runner install` matches `--executable` and `--bundle-id` and refuses them | drop the entries | `machme` becomes an ordinary invalid value; the contract's sentence that it is refused stays true |
| `--timeout-ms 0` becomes 1 | refuse 0 | a refusal where a run now proceeds |
| the last request path wins | refuse a second path | a refusal where a run now proceeds |

Recommended: none in this change. Each stays visible as a named residue
member, and a later repair is then a reduction the generator accepts.

## 4. Join and mutation details

- **Operand bindings.** Needed, and two suffice: `envelope.result.` for the
  result fields and `envelope.data.runner_result` for the admitted host reply.
  Recommended: accept these two, stated in the join.
- **Which nodes cite.** Four nodes have structured facts and are fully
  compared. The runner-mode rule and the example emission only resolve. The
  envelope's `exit_code` and `normalized_outcome` field meanings and the
  classification table are prose; citing them adds resolution and a report
  line, no comparison. Recommended: cite all of them, since the report then
  names the prose that stands uncompared.
- **Signed mutation checks.** Every control ran against unsigned builds in
  0.2 to 5 seconds per check. A signed build takes 25 to 45 seconds and the
  integration suite 24. Recommended: rerun the whole mutation set unsigned
  against the implementing tree, and run the three-step common procedure
  once more against signed builds through the dispatcher.

## 5. Non-derived tokens

No card in the recommended set needs one. Recommended: approve none. The two
places where one would be needed are named under decision 1.

## 6. Refusal and write-failure output

| Invocation | Options | Recommended |
| --- | --- | --- |
| no command, unknown command, `--help`, `-h` | (a) one line naming `help`; (b) the base card on stderr; (c) both | (a): ``policy-witness: no command recognized; `policy-witness help` prints the help topics``, with `help` taken from the command table. The base card lists topics, not commands, so alone it does not say what was wrong |
| `example` with an argument | one line | `policy-witness example: accepts no arguments` |
| `runner help`, an unknown runner command | keep the existing text, which appends the hand-written runner usage; or drop that block | keep: the `runner` tail is outside this plan |
| `test-input` usage | unchanged | unchanged |
| `run` argument refusals | unchanged texts | unchanged |

Write failures:

- **Help.** Recommended: a failed write or flush of the card is exit 2, with
  no panic and nothing on stderr. The prototype does this.
- **Diagnostics.** Recommended: the top-level and `runner` diagnostics are
  written without panicking on an unwritable stderr, as `example` and
  `test-input` already do. The prototype does this; it removes the exit 101
  the appendix records for `bogus` with an unreadable stderr.
- **Envelopes.** `run`, `version` and `runner` still print with `println!`
  and exit 101 when stdout has no reader. Recommended: leave them; it is
  existing behavior outside the help path.

## 7. Public status of help

Options:

- **Not public.** No contract rule. The grammar is held by the integration
  corpus and the unit tests. The contract changes only by support metadata
  and `interface` citations, and the public snapshot is unchanged.
- **Public.** A rule for the `help` invocation and its promises in the
  authored tree, a stamp change for the surface that carries it, and support.
  Once stamped, the exit status, the stream and the topic addresses are
  commitments to callers.

Recommended: not public in this change. The cards' contents follow
definitions that may change, and the plan's own scope preserves existing
public meanings.

## Raised by the experiments

**8. What `generate_interface.py --check` covers.** The build script refuses
a stale inventory in every Cargo build and test. `--check` validates the
committed copies offline: card and entry agreement, recomputed result facts,
joins and residue. G3 asks every generator's `--check` to refuse any stale
copy.

- Offline `--check`, with the build script as the freshness check: no Cargo
  run before the build's Cargo admission; the generator contract states the
  split.
- `--check` runs the build script itself: G3 as written, at the cost of a
  Cargo run in an isolated target directory before `build.sh` reaches its own
  Cargo step.

Recommended: the first.

**9. Inputs recorded as changing no output.** The count of integrity issues
is passed to `select` so that the builder can show it changes nothing.
Failed attempts are not, because the controller has no failed-attempt
classifier at selection. Recommended: keep it so; the unit test holds the
failed-attempt case with a literal expectation.

**10. `runner verify`.** It selects its own outcome and exit status from the
same admission. Recommended: leave it; it is in the unenumerated tail.
