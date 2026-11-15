# Plain help: verification of the implementation

Record of sequence step 4 of `PLAIN-HELP-PLAN.md`, made on 2026-11-15. The
implementation is commit `b16f32d0`. The decisions it follows are in the
plan's appendix; [RESULTS.md](RESULTS.md) records the experiments before it.

## Build and suites

`make build` on a clean checkout at `b16f32d0` produced
`v0.3.7-135-gb16f32d0`, build 1469, contract
`development:4bda040de8e9d2512e6117807580f34ac12ee4f8762b499f59b84cb383148b94`
([build-b16f32d0.txt](verification/build-b16f32d0.txt)). Against that app:

| Run | Selection | Result |
| --- | --- | --- |
| `tests/out/runs/plain-help-acceptance-b16f32d0` | the default battery | 233 cases selected, 233 completed and passed, none skipped or unrun, no harness error, no case overlapped system sleep ([battery-b16f32d0.txt](verification/battery-b16f32d0.txt)) |
| `tests/out/runs/plain-help-byoxpc-b16f32d0` | `runner_byoxpc/runner_install`, `runner_byoxpc/registry_recovery` | both passed; `runner list` and `runner reconcile` showed no record or candidate before and after ([byoxpc-b16f32d0.txt](verification/byoxpc-b16f32d0.txt)) |

The run directories are gitignored development output in the local checkout
and are disposable under the ordinary pruning policy. The battery includes
`unit` (249 controller unit tests, rustfmt), `integration` (26 tests) and all
eleven `source_drift` cases.

Two earlier batteries on earlier forms of the commit are not evidence for it.
The first found two wrong expectations of the executor's own: a selector
conflict is a controller `bad_request`, not a tool failure, and a copy of the
signed binary cannot run outside its bundle. The second found three controls
that still listed the generators without the new one. Each was corrected in
the commit before the run above.

## Against the plan's minimum evidence

**Cards and linkage.** The four cards are in
`controller/interface/inventory.json` with the entries each references. The
generator requires the base card to be exactly the topic addresses, and
`help_cards_agree_with_execution` requires each base line to address a card
headed by that line. The linkage controls are the mutation record below.

**Help behavior.** The corpus,
`controller/integration/interface_cases.json`, has 90 cases with literal
expectations and holds on the signed controller. It contains every row of the
plan's grammar table as amended by the repairs: `version --help`,
`--version --help`, `runner list --help` and `runner validate --help` are now
refusals. `help_needs_no_app_home_registry_or_valid_tail` compares help bytes
from the Cargo-built binary, which has no bundle, with the signed binary's,
for seven tails including non-UTF-8 ones, with no `HOME`, an absent `HOME`,
an unwritable `HOME` and an absent registry: status 0, identical stdout,
empty stderr. By inspection, `cli::run` reaches `help::cmd_help` through
`Command::recognize` and the tail rule alone; neither calls host-fact
collection, app-root resolution, the manifest loader, the registry or the
client.

*Deviation.* The plan asks for "a copy outside its bundle" of the signed
controller. macOS kills a copy of the bundle's signed main executable at
launch (exit 137; the system log names the missing outer bundle). The
Cargo-built binary stands in for it.

**Flag guard.** `--help` and `-h` are in the corpus at the top level, after
`help`, `run`, `example`, `test-input`, `test-input read`, `version`,
`--version`, `runner` and each of the seven `runner` subcommands, with status
and each stream asserted. Rejected controls: a restored `--help` arm
(`restored_flag_help_arm`: the literal rule refuses it and `top.help_flag`
fails with status 0) and a flag-shaped topic address (`flag_shaped_topic`: the
build stops). The parser-library control is not applicable; it is recorded
from the clap prototype in RESULTS.md.

**Publishers.** The existing publication, refusal, write-failure and
publication-versus-admission tests are retained and pass. `example` refusals
now assert the one-line reason. `help example` prints the stored card; the
corpus case `help.example` has no publisher output in it.

**Result obligations.**
`each_result_class_agrees_in_fields_process_status_and_card` drives sixteen
dispositions through production orchestration with literal expectations and
compares the three result fields, the returned process status and the stored
card. It includes a delivery failure and three admission refusals beside a
decoded `finished` reply, and `finished` replies with a failed attempt and
with integrity findings, which stay `true` and 0. The mutation
`result_exit_status` moved the fields, the process status and the card
together and the contract check refused it.

**Inventory and residue.** `source_drift/interface_inventory` passed: nine
inventory defects, the residue refusal of a member moved at unchanged totals,
acceptance of a reduction, the recorded expansion, malformed join records,
ten contract disagreements and seven literal-rule edits. The literal rule and
the README command-block rule run in `runner_source_manifests_agree`, and the
registered generator in `generator_contract` and `build_entry_controls`.

**Build and comparison.**
`stale_interface_inventory_stops_the_build_script` passed in the battery: a
changed definition and a changed committed copy each stop Cargo.
`test_build_refuses_a_stale_interface_copy_before_compiling` passed. The
signed procedure below shows a refused build leaving the previous `dist`
binary in place.

## Mutations

Twenty-one mutations were applied, one at a time, to the implementing tree
before its mutation record existed, by [mutate.py](verification/mutate.py)
from [mutations-applied.json](verification/mutations-applied.json).
[mutations-observed.json](verification/mutations-observed.json) holds every
patch, message and timing; `controller/interface/mutations.json` is the
retained form. Checks ran against unsigned builds in a scratch app directory.

| Outcome | Mutations |
| --- | --- |
| Stale inventory stops the build; after regeneration the card and the behavior change together | `rename_option`, `example_field`, `result_exit_status`, `topic_address`, `command_spelling` |
| The contract check refuses | `example_field` (stale public content), `result_exit_status` (the cited row's exit status) |
| Unchanged private copy builds and passes every ordinary check; the literal rule refuses it | `private_copy_option` |
| Unchanged private copy that no check refuses | `private_copy_result_row`: the copied value is a number, which the literal rule does not see |
| A private copy and then the source change: the generator refuses the card token, no inventory is written, the build stays stopped | `private_copy_option_then_rename`, `private_copy_result_row_then_exit_status` |
| Compile error | `remove_definition` |
| The build script's card validation stops the build | `invalid_relationship`, `admission_condition`, `row_order`, `flag_shaped_topic` |
| The literal rule refuses; cases fail | `literal_beside_run_table`, `restored_flag_help_arm` |
| Only cases moved: no card, contract fact or literal changes | `tail_kind`, `timeout_minimum`, `example_tail_rule`, with the two above |
| Residue addition refused without `--refresh-residue` | `tail_kind`, `example_tail_rule` |
| Residue reduction accepted | `remove_alias` |
| Identifier renamed with its citation: contract check passes, public snapshot byte-identical, cards unchanged | `rename_identifier` |

The contract check's refusal of a changed admission condition, row order,
label and `ok` value is held by `interface_inventory` on inventory facts,
because the build script stops those source changes first. Twenty-six
entries are named by no mutation; `joins.json` lists them.

**Signed procedure.** The three-step rename procedure ran against signed
builds through the dispatcher in a scratch worktree
([signed-procedure.sh](verification/signed-procedure.sh),
[signed-procedure.txt](verification/signed-procedure.txt)):

1. Baseline: build, integration suite passes, `help run` shows
   `--runner-mode`.
2. Rename in the governing source: `make build` exits 2 at the stale
   inventory and the `dist` binary is unchanged. After `--refresh-inventory`
   the build passes, `help run` shows `--runner-kind`, `--runner-kind standard`
   is admitted and `--runner-mode standard` is an unknown argument; the
   integration suite fails on the ten cases that spell the old option or
   card, and on the build-script control, which looks for the old spelling.
3. Private copy in the renderer: the build and the integration suite pass
   with the card unchanged; `source_drift/runner_source_manifests_agree`
   fails on `the card renderer spells a card element itself`.
4. The copy and the rename: `make build` exits 2; the generator refuses
   `card run: token '--runner-mode' comes from no referenced entry`; the build
   still exits 2 and the `dist` binary is unchanged.

Both runs were made at `fa5a19ed`, an earlier form of the commit. It differs
from `b16f32d0` in the mutation record and joins, fifteen added refusal
cases in the corpus, and three test controls; no definition, renderer or
generator code differs.

## Not done

- `preflight/build_refusal_controls` was not run. Its helper that strips the
  generator checks from a script copy now includes the interface check, and
  the default `build_provenance_controls` case checks that helper's anchors.
- The other opt-in cases were not run.
- Help's promises are not public contract rules, by decision.
- No release, notarization or publication step was taken.

## One public sentence changed

The `version` repair changed the public contract's version rule from
"Remaining arguments are ignored" to a statement that an argument after the
command is refused with exit 2. `docs/contract/public.json` changed for the
identity surface accordingly. The `interface` citations and the moved
support citations changed no public content.
