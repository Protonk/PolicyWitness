# Trace dispositions

Disposition record for `records/TRACE-MANAGEMENT-PLAN.md`, written on
2026-11-17 against `837296af`. It gives a present-tense disposition for every
coverage-map row, the thirteen DT-44 leads and both unnumbered import/receipt
investigations: 1,036 claims, counting each DT entry, lettered subfinding and
qualification. The management plan holds the decisions and an index of these
rows; the twelve assessment files beside this one hold the per-claim tables,
comparisons and worklists. Product source under `controller/`, `runner/` and
`docs/` equals `3d3f8e65` apart from generated worker-identity lines and the
publication support of `bba8bca3`–`2f4d76e4`; the signed app assessed is the
`2f4d76e4` build, contract `development:b55acb20…744719e`.

Dispositions here state the chosen treatment. Whether a selected remedy has
landed and been verified is recorded in the management plan as work
proceeds; line references are those of `837296af`.

Each subsection states what is established and by which evidence class.
The classes are: *review execution no longer available* (the review ran
it and its output is gone; the review's text is an account, not a
replayable observation); *re-executed now* (run during assessment on the
`2f4d76e4` app, or in memory over current source); *retained run*
(gitignored development output with ordinary retention, read now);
*source reading*; and *constructed* (input built by hand or by editing a
capture). An accepted uncertainty does not establish the underlying
fact.

### Selected behavior changes

A treatment that changes product or tool behavior cites one of these
rulings. Each lands with its checks and the accounts that state its
changed behavior; each product thread writes or revises its checks
first and runs them against the app before the product edit.

| Id | Findings | Selected change |
| --- | --- | --- |
| R1 | DT-55/56 | Exec stream text is the decoding of every retained byte (NUL as U+0000, invalid sequences as U+FFFD), cut on a scalar boundary before the marker; the per-stream observation gains bytes received, bytes retained, truncated and an exactness indication. |
| R2 | DT-74 | `load_registry` treats only an absent path as an empty registry; any other inspection failure, and a registry symlink whose target is missing, refuses, naming the path and the system error. Reconcile stays report-only. |
| R3 | DT-89 (with DT-88, DT-90–94 and the DT-08 statement) | Development-identity derivation refuses an unlistable directory or uninspectable entry under a selected root; the inputs statement names what is selected. The identity of the unchanged tree changes. |
| R4 | DT-23/51 | A declared-unapplied actor's phases are classified through the declared-setup view; the prefix filter that also drops a pipe or serialization failure for applied actors is decided in the same edit; the independent consumer gains the necessary condition for `finished`. |
| R5 | DT-22/57 | The validator receiver accepts an allow or deny record whose `step_id` is an empty string; request admission is unchanged; the lifecycle adapter rejects only a non-string. |
| R6 | DT-28 | `version`, `run`, the runner commands and `sbpl-check` publish with a checked write; an unwritable stdout is exit 2 with one stderr line. |
| R7 | DT-34.a | `runner install` refuses an `--env XPC_SERVICE_PATH` value that differs from the bundle path, before any machine change. |
| R8 | DT-108, DT-110 | A reply frame that carries a conditional dependent without its guard is a malformed reply, refused by both readers with the bytes retained; generator-side schema validation refuses the ambiguous rule combinations. |
| R9 | DT-50/131 | Swift validator association and `query_first` eligibility compare identifiers and query metadata as UTF-8 bytes; request-name uniqueness and submitted-target equality stay canonical and are stated as such. |
| R10 | DT-42/117 | `policy_check` is null for a request with an `actors` array; per-actor compile captures are unchanged. |
| R11 | DT-113/116 | The fallback calls on the admitted-reply branch are deleted; statements say a fallback capture never shares an envelope with a host reply. |
| R12 | DT-29/81–85 | `import_inventory` gains a required boolean for import forms seen and not followed; the scanner follows literal spellings with comments or other whitespace and reports other `import`-headed forms as unfollowed; a scanned file containing an unfollowed form gets a record error with its hash kept. |
| R13 | DT-121 | The host maps the actor scheduler's `schedule_complete`, `ended_before_arrival` and `ended_before_completion` stop reasons to `completion`, so a witnessed host kill at schedule end or after an early end names its cause. Stops for a timeout, a protocol violation, a withheld release or a failed setup keep the scheduler's reason and an `unknown` cause. |
| R14 | DT-01/02 | Contract generation refuses nested generated regions and contract regions in unmapped documents. |

Considered and not selected, each retained with its limit stated in the
owner named in its subsection: capture despite failed application;
controller comparison of receipt fields against the request; removal of
all actor automatic compilation; clearing an over-length native
extension return beyond the inspected prefix; a pre-teardown observer
for host last-use clearing; a public carrier for accepted host custody
under an unpublished issue slot; removal of path-form compaction,
generation of the Swift variant writer and a narrower fingerprint; a new
cause label for actor allowance-expiry kills.

### DT-01–04 — contract generation: nested regions, moved destinations, link bytes, condition scope

**Established.** All ten claims reproduce at `837296af` by source reading
and by constructed in-memory renders over the checked-out tree; the
generator code they concern is byte-identical to what the review read. The
review's disposable-copy reproductions are no longer available. No committed
document exhibits any of the four behaviors. Two details are narrower than
the review states. After a nested-region render the request markers and 25
of 115 anchors are gone, but the string `contract-request-specimen` survives
in link targets written by other regions (DT-01.a). A percent-encoded link
that rebasing does not rewrite is refused afterwards by the existing link
check when its node lives in another document; the refusal names the
generated document, not the surface (DT-03.b).

**Remaining defect, limit or uncertainty.** Destination validation compares
marker names and counts in mapped documents only, so a nested pair and a
region left in an unmapped document both pass it. Rebasing rewrites by
destination text inside any paragraph that holds a link. The
scope-preservation control checks phrase presence anywhere in a document.
No suite was run on a mutated checkout by the review or by the assessment.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-01.a | Behavior change in the generator (R14): refuse nested or overlapping declared regions before assembly. | `docs/contract/presentation.py` `render`; nested-marker mutation in `source_drift/generator_contract` |
| DT-01.b | Retained qualification: a rendering reproduction; committed regions are sequential. | none |
| DT-02.a | Behavior change in the generator (R14): refuse a `GENERATED CONTRACT` marker in a `docs/*.md` document the map does not name; the scanned documents join the declared inputs. | `presentation.py`, `docs/generate_contract_stamps.py` `input_paths`; moved-destination pair in the same test |
| DT-02.b | Assertion repair: count each node anchor across `docs/*.md` on disk as well as the rendered mapping. | `contract_tree_controls.py`; `source_drift/build_contracts` |
| DT-02.c | Retained as the observation's limit. | none |
| DT-03.a | Reasoned retention. Limit stated in `docs/contract/README.md`: "Rebasing matches destination text within a paragraph that holds a link; show literal link syntax in a code span, not behind an escaped bracket." | `docs/contract/README.md` |
| DT-03.b | Reasoned retention. Limit in the same paragraph: "Write contract links with unencoded destinations." | existing `broken_links` assertion in `source_drift/generator_contract` |
| DT-03.c | No change; accurate. | none |
| DT-04.a | Assertion repair: each required phrase must lie between its own rule anchor and the next contract anchor. | `contract_tree_controls.py`; `source_drift/build_contracts` |
| DT-04.b | No change; accurate. | none |

**Discriminating check.** In `source_drift/generator_contract`: a
nested-marker document and a renamed destination whose old file keeps its
regions are both refused by generation and `--check` with an unchanged
checkout snapshot, and the renamed destination is accepted once the old
file's regions are removed. In `source_drift/build_contracts`: a required
phrase moved out of its rule is rejected. For DT-03 further evidence would
not change the decision: no authored instance exists and the link check
already refuses the encoded form.

**Consequence accepted.** Users: none. Documentation authors get a named
refusal for a nested region or a region in an unmapped document, and two
link spellings (an escaped bracket beside a live link, a percent-encoded
destination) stay unsupported by rebasing.

**Record.** `records/trace-assessments/A-docs-generation-reading.md`,
Subject 1.

### DT-05–08 — ownership label, changed-item lookup, example provenance, development-input inventory

**Established.** All nine claims hold at `837296af` by source reading,
values computed from the loaded tree and a read-only set comparison. The
changed-item index labels twelve records the model marks `authored` as
"imported record declaration". The index carries interface identifiers, not
interface file paths. The RESPONSE opening fence lies outside every
generated region and matches the second action of `EXAMPLE_DOCUMENT` today;
the review's overlay probe was not repeated because the mechanism follows
from placement. DT-08 is wider than the review states: the inputs statement
omits the selected directory `controller/interface` and also the file
`docs/publication.py`, which `bba8bca3` added to `FILES` after the review.

**Remaining defect, limit or uncertainty.** The label is false for twelve
rows. The "excerpt of `EXAMPLE_DOCUMENT`" claim has no check. The inputs
statement has drifted from `docs/build_contract.py` twice and nothing
compares them. The per-commit history behind DT-08.b is not re-derived
here; DT-88–94 carries it.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-05.a | Behavior change in the generator: label a row "authored record declaration" when the record is authored. | `docs/contract/presentation.py`; label assertion in `source_drift/build_contracts` |
| DT-05.b | Closed by DT-05.a. | none |
| DT-06.a–c | Reasoned retention. The limit is already stated in `docs/contract/trace-introduction.md`: "Source and interface associations are partial: an absent association is an unknown". | none |
| DT-07.a, .b | Assertion repair: a drift rule compares the fence under "Read the published example" with the second action of phase `initial-reads`. | `tests/suites/source_drift/check.py` `RULES`, `check_planner.py`; `source_drift/runner_source_manifests_agree` |
| DT-08.a | Account correction in `docs/contract/00-identity.surface.md`, definition `identity.public.inputs`. It is the same single edit as the DT-91 statement under DT-88–94; that subsection gives the wording. | `00-identity.surface.md` |
| DT-08.b | No separate change; the history and the standing statement/code agreement control are disposed of under DT-88–94. | DT-88–94 |

**Discriminating check.** `source_drift/build_contracts` rejects a renderer
that labels every record row imported. The fence rule rejects a fence that
differs from the second action in any operand, with a passing and a
rejected planner control. For DT-08.a the set comparison of the statement's
names with `DIRECTORIES`, `FILES` and `SUFFIXES` returns empty both ways.

**Consequence accepted.** Users: none. Developers still follow an interface
identifier to its reader through the interface account by hand.

**Record.** `records/trace-assessments/A-docs-generation-reading.md`,
Subject 2.

### DT-09–10 — optional log collection; unavailable-clock timeout semantics

**Established.** All seven claims hold by source reading. The
single-worker sequence in `docs/ARCHITECTURE.md` still carries
`optional logs;`, and no log reader exists under `controller/src` or the
runner; `docs/CONTROLLER.md` and `docs/QUESTIONS.md` match the code. For
DT-10 the scheduler maps an unavailable remaining value to zero at three
sites, not one: at the start of each schedule entry, where it selects
`execution_allowance_exhausted` with neither collection nor a reap, after
collection, and in the completion loop. DT-10.c's condition (collection
reached and the actor later reaped) is therefore narrower than the code
requires. The published `schedule.execution_wait` already separates the
two cases: `clock_fault` is true and `elapsed_ms` absent after a fault.

**Remaining defect, limit or uncertainty.** No clock-fault trial has been
executed and no scheduler test injects a failing clock; the production
clock is `clock_gettime(CLOCK_MONOTONIC)`. The operator statement and the
`cancelled` meaning do not tell a reader that the label is a
classification.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-09.a | Account correction: delete `optional logs;` from the sequence block. | `docs/ARCHITECTURE.md` (authored, outside generated regions) |
| DT-09.b | No change; CONTROLLER matches the code. | none |
| DT-09.c | No change; history. | none |
| DT-10.a, .d | Account correction in two owners: the operator rule says an arrival or completion wait that ends with no remaining allowance, including one whose clock can no longer supply a remaining value, cancels under the execution-allowance label; `cancelled` says the value is the scheduler's classification and that `execution_wait.elapsed_ms` and `execution_wait.clock_fault` show whether exhaustion was measured. | `docs/contract/13-actors.surface.md` `actors.phase.order`; `docs/contract/33-actor_evidence.surface.md` `schedule.cancelled` |
| DT-10.b | Recorded as established by source at all three sites; the corrected wording covers the pre-visit site. | same edit |
| DT-10.c | Retained as the evidence limit. The new clause stays source-read in its support owner unless the constructed scheduler control below is added. | `13-actors.surface.md` schedule support |

The `actors.phase.order` sentence is also edited for DT-36 (see DT-36/43);
one edit serves both.

**Discriminating check.** DT-09: none needed; there is no log-reading code
to exercise. DT-10: optional constructed control in
`ActorSchedulerTests.swift` (`runner_unit/pwrunner_core_unit_executable`)
whose clock returns nil after the collection hook and which expects
`cancelled == "execution_allowance_exhausted"`, `stop == "deadline"`,
`clock_fault == true` and no `elapsed_ms`, beside the existing measured
contrast. A separate cancellation value for the unavailable clock is not
selected.

**Consequence accepted.** A user reading
`schedule.cancelled: "execution_allowance_exhausted"` reads
`execution_wait` before concluding that the allowance was measured as
exhausted. Developers: none.

**Record.** `records/trace-assessments/A-docs-generation-reading.md`,
Subject 3.

### DT-11–14 — executed evidence availability, historical counts, barrier support, declared check links

**Established.** All eighteen claims hold by search, read-only git and
values computed from the loaded tree. Nine owners carry
`grade: "executed"` and name three development runs that this checkout
does not hold. Six owners, not five, identify their source as a
`reviewed-inputs` digest; the surfaces are unchanged since the review, so
five was a miscount. The three per-file SHA-256 values of the
direct-validator owner reproduce now. The run behind DT-12.a's frame
counts is gone; the retained development run `20261118T011154Z_5cfcec0a`
holds 152 Swift, 153 Rust and 153 Python cases, and the 621-byte fallback
receipt was re-read there (the 42/12/30 count was not). Over all 22 files
the executed owners cite, 13 have later commits and 9 have none; the
review's fourteen are not identified. DT-14.a is narrowed: the
`source_drift` README already says the `checks` entries establish no
coverage.

**Remaining defect, limit or uncertainty.** What the two `reviewed-inputs`
digests covered is recorded neither in the tree nor in history; only the
author of `eac1482e` could supply it. Unavailable execution stays
unavailable: no present run is substituted for the three named runs.
Whether `failure_boundaries` exercises each of the eleven surfaces that
declare it was read lightly, not case by case.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-11.a, .d, .e | Account correction at the grade definition, keeping the nine grades: "**executed:** The named run exercised the stated assertions with its identified source or build. A development run is disposable test output and may no longer be held; source and check links name the current files, which can differ from that source." | `docs/contract/tree.py` `SUPPORT_GRADES` |
| DT-11.b | Account correction in six owners' `limits`: "The reviewed-inputs digest names an input set and framing this tree does not record; it cannot be recomputed here." The underlying fact stays unknown. | `21-wire`, `33-actor_evidence`, `41-diagnostics` surfaces |
| DT-11.c | No change; reproduces. | none |
| DT-12.a, .c | Covered by the grade definition; the two `context` strings stay, scoped to their run. | `tree.py` |
| DT-12.b | No change. | none |
| DT-13.a | Account correction: the two `limits` strings say no owner in the tree credits integrated collection/release or mutation execution and name `witness_contract/order_barrier_mutations` as the routed control. | `docs/contract/13-actors.surface.md` |
| DT-13.b | No change; guidance and the architecture manifest are accurate. | none |
| DT-13.c | Coverage repair: add the source citation `pw_probe_runner.c: wait_for_proceed` to the barrier's source-read owner. A check citation for the mutation control is added only by an author who reads `mutations.sh` and states its limits. | `13-actors.surface.md` |
| DT-13.d | Retained qualification. | none |
| DT-14.a, .b, .f | Account correction of the two descriptions; the declarations are retained. Limit: "A surface's `checks` list is validated only as catalog suite names; it is not compared with the checks its owners cite and selects no verification for a surface change." | `tests/suites/source_drift/README.md`, `docs/contract/README.md` |
| DT-14.c, .d | Reasoned retention under the corrected introduction; the owners' limits already say integrated cases own the live rows. | none |
| DT-14.e | Account correction: "Source, check and interface associations are partial". | `docs/contract/trace-introduction.md` |

**Discriminating check.** The barrier itself is exercised by
`witness_contract/order_barrier_mutations` (non-default). The other edits
are checked by owning generation and `source_drift`. Searching other
machines for the three runs would change availability on one machine, not
the account.

**Consequence accepted.** Users: none. A developer following an executed
citation does not expect the named run to be present in a checkout, and
the two reviewed-inputs digests cannot be recomputed.

**Record.** `records/trace-assessments/A-docs-generation-reading.md`,
Subject 4.

### DT-15–21 — reading routes, commitment placement, changed-file coverage, presence rules, field ownership, known-gap navigation, link labels

**Established.** The twenty-three claims hold by search, source reading and
values computed from the loaded tree, with four corrections to the review.
DT-15: the failure contract's reading rule 9 and matrix row S12 are
correct; only the hand-authored `operation_relation` row is wrong. The
review's signed-app specimen for DT-15.b is not available and was not
repeated; `witness_contract/comparison_matrix` passed with 33 live rows in
the retained development run. DT-16.b: `worker-equipment.json` does occur
in BUILD, once, in a generated step row; no section prose mentions it.
DT-17.c: `rust.` rows sort after the product paths and before `tests/`
rows. DT-18.b: a keyword scan finds 32 entries without a presence rule,
not 28; the count depends on the keyword set. The four unnumbered
qualification claims in this range (RC.a–c, AF.a) are historical: the
three `documentation-trace-*` run directories are absent, and guide bytes
were re-verified against the frozen digest.

**Remaining defect, limit or uncertainty.** Per-field admission behavior
for the entries without a presence rule has not been exercised; the import
fact per field is decoder storage, not admission. No other row of the
failure contract's table was compared with source. The `v0.3.8` link in
the frozen guide names a tag that does not exist; publication is recorded
as withheld.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-15.a | Reasoned retention; nothing stated is false. | none |
| DT-15.b | Account correction: the `unresolved` cell gains "or a query operation containing `*` other than the exact `process-exec*` match". | `tests/FAILURE-PROPAGATION-CONTRACT.md` (authored row, outside the shared regions) |
| DT-15.c | Account correction: "`unresolved` means the action has no single mapped operation, or the query is a wildcard spelling other than the matched `process-exec*`." | `docs/contract/31-steps.surface.md` |
| DT-15.d | Recorded as open coverage, not a finding. | none |
| DT-16.a, .c | Account correction: prune `equipment.binding` from the signing list, `equipment.inventory` and `equipment.manifest` from the evidence list and `identity.public.derive` from the identity list; one sentence in BUILD's "Order." paragraph says each service's `worker-equipment.json` is written after that service's nested signatures and before its seal. | `docs/contract/presentation.json`, `docs/BUILD.md` |
| DT-16.b | The review is corrected on one fact, as above. | none |
| DT-16.d | Retained qualification. | none |
| DT-17.a–c | Reasoned retention under the limit already in `trace-introduction.md`. | none |
| DT-18.a | Account correction, landed with DT-18.b: the notation says that for an input record "as defined below" means the entry's meaning states whether the key is required, optional or may be null. The phrase is not renamed. | `docs/contract/tree.py` `NOTATION` |
| DT-18.b | Account correction per field: each listed meaning gains its presence rule after its decoder and admission are read. | six surface files; keyword ratchet in `source_drift/build_contracts` |
| DT-18.c | Account correction after DT-18.b: the null rule names fields by what their entries say, not by `decodeIfPresent`. | `docs/contract/10-request.surface.md` |
| DT-18.d | Retained as the evidence limit on the per-field rules. | none |
| DT-19.a, .b | Reasoned retention under the guide freeze. The limit is stated here and in the maintainer-judgment outflow, not in permanent documentation: the frozen guide names CONTRACT as the place that defines the fields; CONTRACT's introduction and commitment index route each field statement to REQUEST, RESPONSE or ARCHITECTURE. | none |
| DT-20.a | No change to the tours. | none |
| DT-20.b | Account correction: one sentence says the Known gaps view lists the tree's gap nodes and that ARCHITECTURE, CONTROLLER, WORKER and BUILD each end with an index of their own gaps. No tour gap becomes a tree gap node (see DT-31/32/42/113–119 for the lost-reply gap). | `docs/contract/trace-introduction.md` |
| DT-21.a–c | Reasoned retention. Limit stated here only: index rows carry node titles; where two nodes share a title the link target, and in Find a commitment the identity column, distinguishes them. | none |
| DT-21.d | Account correction of the generated sentence: "A row names the record members its check's structured conditions read and links each structured consequence with what it reaches; where the rule states these in prose, the row refers to the linked rule." | `docs/contract/tree.py` |
| RC.a–c, AF.a | Retained as historical observations; no present run is substituted and nothing is reused from the absent runs. | none |

DT-16 and DT-41 concern the same generated lead-in ("Commitments explained
here:"). Pruning the false associations serves both; the lead-in stays. See
DT-37–41.

**Discriminating check.** `witness_contract/comparison_matrix` row S12 and
the constructed matrix reader in `runner_unit/pwrunner_core_unit_executable`
already assert the wildcard rule. The presence ratchet counts input-record
fields whose presence renders the phrase and whose meaning has none of the
presence words, expected zero; it is a keyword heuristic and is described
as one. Other edits: owning generation and `source_drift`.

**Consequence accepted.** A user reading
`operation_relation: "unresolved"` for a wildcard query does not conclude
that the attempt has no mapped operation. Per-field presence rules stay
source-derived until an admission pass exercises them. Developers: the
changed-item index stays partial for thirty source files.

**Record.** `records/trace-assessments/A-docs-generation-reading.md`,
Subject 5 and "Unnumbered qualification sections in the range".

### DT-22/57 — empty ordinary step identity

**Established.** All nine claims hold at `837296af` by source reading. The
review's two live specimens (eligible query: exit 1,
`validator_decode_failure`; planner-excluded query: exit 0, `finished`)
ran on the `8b5de2b2` app and their outputs are no longer available;
neither was re-executed. The mechanism is read in source: host admission
tests uniqueness only, the native validator echoes any non-NULL
identifier, and the receiver rejects an allow or deny whose `step_id` is
an empty string. The reader disagreement of DT-57.b is reproduced now on a
constructed envelope: `consumer.validate` returns no finding and the
lifecycle oracle returns D8 `malformed_record`. No registered case submits
an empty ordinary identifier, and the actor refusal code `empty_step_id`
has one producer and no test.

**Remaining defect, limit or uncertainty.** An admitted request cannot
carry an allow or deny for its empty-ID step, although the field is stated
as associating a query with its attempt and result. The lifecycle adapter
rejects an identifier that no statement forbids and three other readers
accept. That an eligible query with a diagnostic outcome would finish is
an inference; nobody ran it. The oracle finding is not evidence that the
request should have been refused.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-22.a, .b | Behavior change (R5): the validator receiver accepts an allow or deny whose `step_id` is an empty string and joins it to the unique empty-ID step; `operation` and `filter_type` stay nonempty; request admission is unchanged. The wire rule and the failure contract sentence change from "nonempty step_id" to "a string step_id". Refusing an empty identifier at admission is not selected. | `ValidatorClient.swift`; `21-wire.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md`; live pair in `failure_boundaries` |
| DT-22.c | Coverage repair after R5: the identifier rule's support owner cites the live pair and the actor refusal control; the reader-corpus citation stays only for the reply-reader claim. | `13-actors.surface.md` support owner |
| DT-22.d | Coverage repair: an actor-form request with one empty action identifier expects `bad_request`, `request_failure.code: "empty_step_id"`, the action path and no actor launch. | `runner_outcome_bad_request/accepted_input_contract` |
| DT-22.e | Retained qualification; superseded for the excluded branch by DT-57.a. | none |
| DT-57.a | No change; under R5 the result is the stated behavior. | none |
| DT-57.b | Assertion repair (R5): the lifecycle adapter rejects only a non-string `step_id`. | `tests/lib/lifecycle_adapter.py`; `blackbox_e2e/checker_controls` |
| DT-57.c | Retained qualification. | none |
| DT-57.d | No separate change; the crediting question is disposed of under DT-53/132/135. | DT-53/132/135 |

**Discriminating check.** New live pair in `failure_boundaries` beside
`validator_association`: two ordinary requests differing only in
`step_id` (`""` and `"s"`) both finish with an associated validator
record, `native_rc` 0 and `query_first`. With the controlled validator: an
allow with `"step_id": null` stays a `structure` fault; an allow with
`"step_id": ""` against a plan without an empty identifier yields
`unexpected_id` and `validator_unavailable`. The pair runs first against
the current app, where the empty-ID row is expected to fail. Because the
eligibility predicate's input domain widens,
`witness_contract/order_barrier_mutations` runs with the change.

**Consequence accepted.** Users: no admitted request changes for the
worse. An allow or deny record with an empty `step_id` that matches no
step now ends `validator_unavailable` with the record retained, where it
ended `validator_decode_failure`. Developers: the two-form identifier
rule and its reader branches remain.

**Record.**
`records/trace-assessments/C1-identity-classification-vocabulary.md`,
section 1.

### DT-23/51 — declared-unapplied actor classification

**Established.** All nine claims hold by source reading. The review's two
live pairs (failed validator spawn; controlled validator printing
`{not JSON}`) ran on the `8b5de2b2` app; their outputs are no longer
available and were not re-executed. `assembleActorReply` classifies each
phase with the actor's raw output and keeps the result only when its
outcome begins with `validator`; `classifyActor` substitutes an applied
view for a declared-unapplied actor and the phase call does not. DT-23.d
is wider than the review states: every outcome of the validator section
(`validator_spawn_failed`, `validator_decode_failure`,
`validator_no_reply`, `validator_unavailable`) is unreachable for an
unapplied actor's phase. No reader relates the aggregate to phase faults.
In the retained development run none of 144 actor-form envelopes with an
unapplied actor's collected phase carries a validator fault.

**Remaining defect, limit or uncertainty.** A failed prediction collection
in an unapplied actor's phase yields exit 0 and `finished`, against
unqualified statements in the reply surface and the failure contract.
Outside the review and by source only: the same prefix filter also drops
a validator pipe, descriptor-setup or probe-serialization failure for an
applied actor's phase, leaving `finished` with no record of the failure.
No registered case runs an actor-form validator failure for any mode. The
native query was replaced by fixture output in DT-51; the observations
are not evidence about every actor schedule.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-23.a, DT-51.a, DT-51.d | Behavior change (R4): a declared-unapplied actor's phases are classified through the declared-setup view, so a failed validator spawn, decode or read gives the applied actor's outcome and exit 1. The prefix filter that also drops a pipe or serialization failure for applied actors is decided in the same edit. | `ActorOrchestration.swift` |
| DT-23.b, DT-51.c | Accurate mechanism accounts; no account change beyond R4. | none |
| DT-23.c | Account correction with R4: the reply statement gains the actor ladder (actor failures in actor order, then validator failures and collection exhaustion in schedule order, then cancellation) for both modes; its support owner is updated. | `30-reply.surface.md` |
| DT-23.d | Covered by R4; the control exercises spawn and decode, and the other validator outcomes share the one classifier section. | none |
| DT-51.b | Assertion repair (R4): the independent consumer gains the necessary condition that a `finished` reply has no phase with a spawn failure, decode fault or validator I/O error. It does not reproduce the classifier. | `tests/lib/consumer.py`; `blackbox_e2e/checker_controls` |
| DT-51.e | Retained qualification. | none |

**Discriminating check.** New live case in `runner_validator_failure`,
four specimens through the CLI: one actor, one phase, one `open_read`
probe, `sandbox.mode` `apply` or `unapplied`, validator a nonexistent path
or the transcript fixture returning `{not JSON}`. Each gives exit 1,
`ok: false`, the applied row's outcome, a completed worker attempt and
`unestablished`; an all-success unapplied row stays `finished`. A
constructed unit row calls `assembleActorReply` with an injected spawn
failure for both modes, and a second with an injected pipe failure
distinguishes the prefix-filter decision. The live rows run first against
the current app, where the unapplied rows are expected to fail. The
validator substitution is one of the eight controls moving to
`test-input run`; the control is written against the route current when
it lands and joins the caller map. Host-thread changes also run
`witness_contract/order_barrier_mutations`.

**Consequence accepted.** An actor-form run in which an unapplied actor's
collection failed changes from exit 0 to exit 1; no request form, record
shape or vocabulary changes. Developers: none beyond the new controls.

**Record.**
`records/trace-assessments/C1-identity-classification-vocabulary.md`,
section 2 and "Outside the review".

### DT-24/30 — query meanings and response vocabulary

**Established.** All ten claims hold by source reading, and DT-24.a,
DT-24.b and DT-30.d are confirmed in live envelopes of the retained
development run `20261118T011154Z_5cfcec0a`: `validator_not_invoked`
beside a `collected` phase with a failed spawn; a worker `pid` on an
excluded query in a `not_needed` phase; `schedule_complete` as
`cleanup_trigger` on three actors. The review's own executions are no
longer available. For each field three sets differ: values a producer
assigns, values a reader accepts and values the statement lists. DT-30.b
is narrowed: `host_timeout` and `clock_fault` are emitted, in the
transfer event's `status`, not the transfer record's. DT-30.g is now
verified by search: no reader constrains `decode_fault.kind`.

**Remaining defect, limit or uncertainty.** Five statements list values no
producer assigns to that field or omit values that are emitted; one
closed vocabulary has no rejecting boundary. None of the five lists is
declared closed (DT-30.f), so no exhaustiveness declaration is broken.

**Treatment.** No product behavior changes for this row. `cleanup_trigger`
is the one field whose values change, through R13 under DT-46/120/121/129.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-24.a | Account correction: `validator_not_invoked` "when no validator process supplied output for the phase, whether collection never ran or it ran and could not start one". Assertion added for the reason in the spawn-failure check. | `31-steps.surface.md`; `witness_contract/validator_spawn_failed_reports_degraded` |
| DT-24.b | Account correction: `pid` is the worker PID recorded when worker output exists, including for an excluded query; `collection_status` and `validator_subprocess` say whether a collection addressed it. Assertion added for the excluded step. | `31-steps.surface.md`; `witness_contract/phases` |
| DT-24.c | No change; `association_issues` carries the distinction. | none |
| DT-30.a | Account correction: the seven assigned names; readers also accept four others; an error after a failed service-seal inspection names the static inspection call. Assigning `service_seal` is not selected. | `34-equipment.surface.md` |
| DT-30.b | Account correction: seven host answers for the transfer record; `host_timeout` and `clock_fault` are the source worker's wait results in the transfer event's `status`; `none` is dropped. | `14-extensions.surface.md` |
| DT-30.c | Account correction: two assigned values, absent when no basis was recorded; readers also accept `unavailable`, which no producer assigns. | `32-lifecycle.surface.md` |
| DT-30.d | Account correction worded after R13; one edit with DT-46/120/121/129, which gives the wording. | `32-lifecycle.surface.md` `cleanup_trigger` |
| DT-30.e | Account correction: `bad_policy` is defensive; admission refuses a missing source or another format as `bad_request` first. | `30-reply.surface.md` |
| DT-30.f | Retained qualification. | none |
| DT-30.g | Assertion repair in the independent consumer, with the limit in the field's support owner: "The host receiver assigns only these three kinds. Product recipients do not re-check the value; the independent consumer rejects any other." | `tests/lib/consumer.py`; `32-lifecycle.surface.md`; `blackbox_e2e/checker_controls` |

**Discriminating check.** The two existing witness cases with their added
assertions; a rejected `decode_fault.kind` control in
`blackbox_e2e/checker_controls`. For the vocabulary corrections further
evidence would not change the decision: the assignments are literals at
the cited lines.

**Consequence accepted.** A user does not read `validator_not_invoked` as
"collection did not run" or a non-null `sandbox_check.pid` as evidence
that a validator queried that process. Product readers keep accepting
values no producer assigns.

**Record.**
`records/trace-assessments/C1-identity-classification-vocabulary.md`,
section 3.

### DT-25/50/131 — submitted-target equality, validator association, literal reader equality

**Established.** All twenty-four claims hold at `837296af`; the cited
files are unchanged since the review. The retained live and seam
envelopes under `.tmp/contract-trio/acceptance/` (old app `8b5de2b2`;
seam frames carry a constructed contract binding) match their recorded
hashes, and the current Python readers re-run in memory over them
reproduce every Python cell of the review's tables. No Swift or Rust
code was run; Swift and Rust statements are source reading plus retained
output. Three different equality questions are kept apart.
Submitted-target equality relates two request strings under canonical
Unicode equivalence; the producer, a unit test, the Python reader and
two shared owners agree, and only the complete statement is silent.
Validator association and order eligibility use Swift `String` equality
in the host and UTF-8 byte equality in the Rust and Python readers, so
on one steered reply the host reports no association issue and the
controller withholds the disposition. Path-form `same_as_input` is
stated and implemented in bytes. Request admission refuses canonically
duplicate identifiers. Reachability of the disagreement is read from
source: request strings cannot supply it, and the shipped validator
echoes parsed bytes, so it needs child output that differs from the
request's bytes (a substituted validator, or an external runner whose
validator is not the shipped one). It is not limited to non-ASCII
requests: three code points are canonically equivalent to ASCII
characters.

**Remaining defect, limit or uncertainty.** The statements say "exact"
and name no equality relation for association; step identifiers are
"unique across all actions" with no relation stated. A request spelled
in NFD has never been executed through the shipped validator; across the
retained checkpoint run no validator record is non-NFC. No Swift
reporting validator was run on any edited frame. Worker-slot identity
joins also use `String` keys and no reply field exposes that identifier;
the decision for them follows the same principle as R9 and is stated
below the table.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-25.a, .c | Account correction: the target relation "compares submitted strings under canonical Unicode equivalence"; the failure contract's working table says "Submitted strings that are not canonically equivalent establish different submitted targets, not distinct runtime objects." Behavior unchanged (R9 keeps target equality canonical). | `31-steps.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md`; `blackbox_e2e/checker_controls` |
| DT-25.b, .d, .x | No change; `same_as_input` stays a byte comparison and a separate question. | none |
| DT-50.a, .t2; ACC-MAP.assoc; ACC-RES.assoc | Behavior change (R9): Swift validator association and `query_first` eligibility compare identifiers and query metadata as UTF-8 bytes, as the Rust and Python readers do. The association statements say so. Making Rust and Python canonical, and retention with the split stated, are not selected. | `PWRunnerPredictionEvidence.swift`, `PWRunnerStepEvidence.swift`, `PWRunnerReply.swift`; `31-steps`, `32-lifecycle` surfaces; failure contract |
| DT-50.b, .d, .e, .t1, .t3–.t6; DT-131.a–c, .e; ACC-CLS.3 | No change to the record; the steered rows change as R9 specifies and all four readers then agree on those frames. | reader corpus |
| DT-50.c; DT-131.d (source comment) | Comment corrected with the host thread, which edits that file for R9. | `PWRunnerPredictionEvidence.swift` |
| DT-131.d (identifier statement) | Account correction: "Uniqueness is under canonical Unicode equivalence: identifiers that differ only in normalisation are duplicates." The phase and actor identifier statements take the same sentence where equally silent. | `12-probes.surface.md` |

Worker-slot identity joins. R9's principle is that an identifier or query
metadata value received from a child process is compared with the
submitted request as UTF-8 bytes. A join whose two sides are both
request-derived strings may stay keyed by `String`, because admission
keeps request identifiers unique under canonical equivalence. The host
thread reads the worker-slot join and applies the byte rule only if one
side is child-supplied.

**Discriminating check.** Reader-corpus rows built from Swift-encoded
frames, so each has a consistent binary capture: byte-identical record
(NFC id, NFC value) accepted with `query_first`; request spelled in NFD
with a byte-identical record accepted; record canonically equivalent and
byte-different (NFD id, NFD value, a Kelvin-sign id against `K1`)
produces the issue list, an `unestablished` order and
`validator_unavailable`; two records, one associated and one
`unexpected_id`. The byte-different rows run first against the current
app, where the Rust and consumer expectations fail. Matching ordering
tests assert eligibility for a byte-different record id and value.
`witness_contract/order_barrier_mutations` runs with the change because
the eligibility rule changes. Two consumer controls pin the canonical
target relation.

**Consequence accepted.** For canonically equivalent, byte-different
validator output the run now ends `validator_unavailable` with exit 1
where it ended `finished`; no shipped validator produces such output. A
user gives actions step identifiers that are distinct under canonical
Unicode equivalence, and does not conclude from `same_submitted` that
two strings have identical bytes.

**Record.** `records/trace-assessments/L-readers-acceptance.md`,
section 1.

### DT-26–28 — augment and selector refusal names; publication under broken or closed stdout

**Established.** All eleven claims hold. Codes, by source reading: the
controller refuses an invalid augment name with `invalid_value`, as
`v0.3.7` did, and the stated `invalid_augment_name` has never been
produced; `conflicting_selector` is emitted for three selector conditions
and stated for none by name; the controller refusal list ends in
`admission_refused`, which only the host assigns, and omits four of the
ten controller codes. Publication, re-executed now on the `2f4d76e4`
app: with a reader-less stdout `--version`, `version` and `sbpl-check`
exit 101 with a panic message, while `help`, `example` and
`test-input read` exit 2. `run` and the runner commands use the same
`println!` writer by source and were not run. With stdout closed at
launch every publisher exits 0. DT-28.e is narrowed by observation on the
helper: the process holds `/dev/null` on descriptor 1, so no write fails.

**Remaining defect, limit or uncertainty.** A status of 101 contradicts
the version statement and the envelope's enumeration of 0, 1 and 2. For
`runner install`, `remove` and `validate` the machine changes precede the
write, so a failed write follows completed changes; that order is read
from source. The `/dev/null` substitution was observed on the helper
only.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-26.a | Account correction: the augment rule names `invalid_value`. The path assertion `["policy","augments","0"]` joins the existing integration test. | `11-policy.surface.md`; `integration/cli.integration` |
| DT-26.b | No change; supported by the added path assertion. | none |
| DT-27.a, .b | Account correction: "Refuse with `conflicting_selector`: standard mode with an external selector, or byoxpc mode without an ID or service (at the root path), and a `--runner-mode` value that differs from the file's nested `runner.mode` (at `runner.mode`)." One interface case is added for the third condition. | `10-request.surface.md`; `controller/integration/interface_cases.json` |
| DT-27.c | Account correction: the controller record's `values` list the ten controller codes and stay open and illustrative. | `15-refusals.surface.md` |
| DT-27.d | Retained qualification. | none |
| DT-28.a, .b | Behavior change (R6): `version`, `run`, the runner commands and `sbpl-check` publish with a checked write and flush; an unwritable stdout is exit 2 with one stderr line. The version, envelope, installation and helper exit statements and `controller/README.md` state the write-failure form. | `json_contract.rs`, `cli.rs`, `run_flow.rs`, `bin/sbpl-check.rs`; `controller/integration/cli_contract.rs` |
| DT-28.c, .e | Reasoned retention with the limit beside each exit-0 sentence: "Exit 0 reports that every write and the flush to the process's standard output succeeded. A command launched with standard output closed writes to a discarding descriptor and also exits 0." | `10-request.surface.md`; `>&-` rows in the two integration tests |
| DT-28.d | No change; the support text does not overstate. | none |

**Discriminating check.** For R6, with a reader-less stdout: `--version`,
`version`, `sbpl-check --help` and a `run` on a missing request file each
exit 2 with exactly one stderr line, and the status does not change when
stderr is also unwritable. These rows run first against the current app,
where they exit 101. The closed-stdout rows expect exit 0.

**Consequence accepted.** A caller matches an invalid augment name on
`invalid_value` and separates the three selector conditions by `path`.
After a write failure from `runner install`, `remove` or `validate` the
machine may already have changed. Exit 0 from `example` or
`test-input read` establishes a complete document only for a caller that
supplied and read standard output.

**Record.**
`records/trace-assessments/C1-identity-classification-vocabulary.md`,
section 4.

### DT-29/81–87 — import scanner, resolver and helper projection

**Established.** All sixty-eight claims hold at `837296af`; the scanner,
resolver, helper and their statements are byte-identical to what the
review read. The review's helper outputs are absent. Every helper-side
contrast was re-executed now on the signed `2f4d76e4` helper with
constructed inputs (53 envelopes, macOS 26.7.1), and the hashes the
review recorded for its four base cases reproduce exactly. The native
witness is a compile diagnostic naming an imported marker file; it shows
that the helper's host-side compiler evaluated the file, not which file
was opened, and it is not the worker's compiler. The bytecode
comparisons of the review were not repeated and depend on the private
capture view (DT-95–104/134). Observed: a computed import argument
leaves the helper inventory identical to the no-import inventory while
the compiler evaluates the file (DT-29, DT-82); a nonliteral form inside
an imported file leaves that file's record error-free (DT-83); a literal
import followed by a comment is neither recorded nor flagged, even
internally (DT-84); a literal import the compiler never evaluates is
recorded (DT-85). Corrections to the review: DT-81.e is imprecise, since
no `docs/RESPONSE.md` exists at `v0.3.6`; DT-84.g's "other spellings
untested" is now tested, and eleven further spellings the compiler
evaluates are neither followed nor flagged, including a computed
`(import(...))` that is not flagged even internally; files also reach
the compilation through an aliased or applied `import`, `eval` and
`load`, with no `import`-headed form at all.

**Remaining defect, limit or uncertainty.** The helper statement says an
unevaluable import argument "records an incomplete inventory", and the
helper drops the resolver's flag. The closure statement says failed
imports contribute no line, and an invalid-UTF-8 record does. One
integration assertion (`policy_sha256 != policy_closure_sha256`) cannot
fail. No text scan can be made complete: evaluation is undecidable from
text, and one observed spelling contains no `import` token. The native
reader's grammar is private; the followed set is established for macOS
26.7.1 and the helper's host-side compiler only. The compiler's file
opens are observed by no component. The dossier consequence for a
nonliteral form inside an imported file has never been executed.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-29.a; DT-81.a, .b, .t7; DT-82.a, .d | Behavior change (R12): `import_inventory` gains a required boolean for import forms seen and not followed; the helper statement is rewritten with it. | `sbpl-check.rs`, envelope shape golden; `11-policy.surface.md` |
| DT-29.b | Reasoned retention; limit L-C below. | `11-policy.surface.md` |
| DT-29.c | Closed by R12 (resolver comment updated). | same thread |
| DT-29.d | No action; discharged by DT-82. | none |
| IC.a, .b, .d; IL.a, .b, .f | No action; the review's outputs are absent and the re-execution is gitignored. The new registered contrasts become the durable evidence. | none |
| IC.c | The marker diagnostic is adopted as the native witness, with its limit. | helper and dossier contrasts |
| IC.e; DT-82.c | No action here; contrasts do not rely on allow-default bytecode. | DT-95–104/134 |
| DT-81.t1–t6 | No change; each cause has a carrier. | `unit/rust.unit` |
| DT-81.t8; DT-83.a | Behavior change (R12): the flag covers nested forms, and a scanned file containing an unfollowed form gets a record error with its hash kept. | `sbpl_imports.rs`; `42-dossier.surface.md` |
| DT-81.t9, .t10 | Reasoned retention; limit L-D: "The helper inventory carries no first-problem text and does not name which bound was reached; each cause is read from its own field." | `11-policy.surface.md` |
| DT-81.c | No change beyond comment updates with R12. | none |
| DT-81.d; DT-87.b (guide), DT-87.c (guide) | No action; frozen. The guide's narrower promise stays true. | none |
| DT-81.e; DT-83.f; DT-84.f | No action; history, with the one imprecision recorded. | none |
| DT-82.b; DT-83.c | Adopted as registered helper contrasts. | `integration/cli.integration` |
| DT-83.b | Account correction with R12: scanning collects import forms; an unfollowed form is reported by the flag and the record error. | `11-policy.surface.md` |
| DT-83.d; DT-86.f | Coverage repair: lexer tests per observed spelling and a resolver test with a wrapper file. | `unit/rust.unit` (R12 rebuild) |
| DT-83.e; IL.d | Coverage repair: dossier contrasts through `run`. | `witness_contract/dossier_witness` |
| DT-84.a, .b | Behavior change (R12): the scanner follows literal spellings with comments or other whitespace and reports every other `import`-headed form as unfollowed. An escape other than `\"` and `\\` is reported unfollowed. | `sbpl_lex.rs` |
| DT-84.c | Covered by the dossier contrasts. | `witness_contract/dossier_witness` |
| DT-84.d | Account correction with R12; limit L-B below; the dossier scan and scope sentences say "import forms the scan did not follow". | `42-dossier.surface.md` |
| DT-84.e | Followed after R12. | unit tests |
| DT-84.g | The followed set is scoped by the observed table and stated as established for macOS 26.7.1 only. | `11-policy.surface.md` support |
| DT-85.a–d, .h | Reasoned retention; limits L-A and L-C. Dropping nested forms would lose imports that are evaluated. | `11-policy.surface.md` |
| DT-85.e; IL.c | Retained as a stated unknown inside L-A. | same |
| DT-85.f, .i | No change. | none |
| DT-85.g | Account correction: "Native compilation examples establish their selected literal imports" is removed; the new checks are cited with their limit once they exist. | `11-policy.surface.md` |
| DT-86.a | Support stays source-read until the contrasts land, then cites them. | same |
| DT-86.b | Assertion repair: the assertion that cannot fail is replaced by record hashes equal to independent file hashes, an independently recomputed closure and presence of the transitive record. The matching unit test is removed with the R12 rebuild. | `controller/integration/cli_contract.rs` |
| DT-86.c–e, .g, .h | No change to existing tests; extended for the new field. | none |
| DT-86.i | Coverage repair; "what the compiler read" is closed only to "what the compiler evaluated". | `integration/cli.integration` |
| DT-87.a | Account correction: a closure line is contributed by every record carrying both a resolved path and a hash, including one whose `error` reports that its text could not be scanned or fully followed. Changing the digest is not selected. | `11-policy.surface.md` |
| DT-87.b (`11-policy`) | Small addition with R12: the flag says whether the scan saw a form it did not follow. | same |
| IL.e | Recorded per item: bounds, unreadable and FIFO stay unit-level; collisions and in-run file changes stay unexercised; worker-side compilation becomes the dossier contrasts. | none |

Limits stated beside the technical claims, with wording the implementer
settles. L-A (evidence scope): the inventory is a scan of source text
and of the files that scan read; it is not an observation of the
compiler's file reads; a record does not state that the compiler
evaluated the form or read the file; an inventory with no record and no
unfollowed form does not state that the compiler read no file. L-B
(dossier `status`): `complete` describes the scan, not the compiler's
inputs. L-C (`records`, both closure digests): literal names are
collected in every syntactic position; the closure digest is not a
digest of the compiler's inputs. A token-mention signal, a compiler-file
observer, a dedicated dossier boolean and projection of `failure` and
`exceeded` into the helper are not selected.

**Discriminating check.** Helper contrasts in
`integration/cli.integration`: no import; literal followed; computed
argument (flag true, no records); nonliteral inside an imported file
(wrapper record with hash and error, flag true); trailing-comment
literal (record present); unevaluated form (record present, compile
succeeds: the stated limit); aliased `import` (no record, flag false:
the stated limit); invalid-UTF-8 import (closure equals an independent
recomputation that includes its line). Dossier contrasts in
`witness_contract/dossier_witness` give the first registered observation
of the worker's compiler for these spellings. Both run first against the
current app, where the missing key, the empty record list for the
trailing-comment literal and its `complete` status are the expected
failures.

**Consequence accepted.** A new required key appears in the helper
envelope and in fallback run envelopes; a strict-schema reader admits
it. For the newly followed spellings `records` and both closure digests
change for unchanged source and files; for newly flagged forms the
dossier status changes from `complete` to `incomplete`. A non-null
record `error` no longer implies the file was not read. A user still
does not conclude from an empty, flag-free inventory that the compiler
read no imported file, or from a record that it read that one.

**Record.** `records/trace-assessments/G-import-inventory.md`, Subject A
and "Outside the review".

### DT-31/32/42/113–119 — transport reachability, error precedence, retained bytes, helper selection and held-input provenance

**Established.** One fallback trace; 104 claims, none reversed. Product
source, surfaces and the cited tests are byte-identical to the transport
investigation's snapshot. The evidence classes are kept apart: native
observations on shipped binaries at `8b5de2b2` (recorded files retained
locally under `.tmp/contract-trio/transport/` and re-read, not
re-executed); controlled client bytes through a Cargo-built controller
(seventeen recorded envelopes re-read); typed injections in Rust unit
tests (read, not run); source reading. Re-executed now on the `2f4d76e4`
app: `help result`, which still prints the
`runner_response_unavailable` line, and the shipped helper on three
constructed inputs, where an actor-form request with no top-level
`policy` exits 2 with empty stdout. Typed constructions are not evidence
that the shipped caller reaches those states. Established by the caller
trace: capture admission returns a typed reply exactly when it reports
no failure, so an admitted completion without a host reply, a typed
reply under a foreign producer contract, a client stdout error after
admission, and a fallback capture beside a host reply or diagnostics are
produced by no client output. Fallback is eligible only for an accepted
capture with terminal `xpc_error` and no delivery error. For every actor
request the host admits, the whole-request helper call fails to decode
and `policy_check` is `tool_error`. Narrowings: DT-114.b is stricter
than stated, since in `runner verify` the unsupported and malformed
projection arms cannot run for any value; LIM.d and DT-31's "not
exercised" are incomplete, since the opt-in
`runner_byoxpc/reservation_controls` already produces an ordinary-form
`xpc_error` through the shipped controller and asserts a null
`runner_result` for an altered producer contract (read, not run);
DT-116.e leaves one residue of the withdrawn "disambiguation" reason in
a test comment.

**Remaining defect, limit or uncertainty.** Statements describe states
no client output reaches and a pairing of fallback with worker evidence
that cannot occur; the controller README says a decoded foreign reply's
projection is retained; the `result.error` precedence lists two tiers
that cannot be selected; one refusal path is stated with two notations.
Several Rust tests are credited beyond what they construct or assert,
and no test observes the helper's input for an ordinary request.
Independent compilation does not establish worker progress or explain a
lost reply: in the one native host-loss run the worker ran its action
while the envelope held only fallback results. Not produced natively: a
truncated, empty or over-capacity host reply. Whether NSXPC delivers a
zero-length reply as empty data is unverified, and no disposition
depends on it. External reliance on a non-null `policy_check` for actor
requests is unknown. Whether the independent consumer should admit
`actor_policy_checks` captures is not decided.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-31.a; DT-113.a–d; Q1.c | Reasoned retention of the reply-less row as defensive code, with the accounts corrected: the classification row says "No client output reaches this row: capture admission yields a decoded host reply whenever it reports no failure"; the row, label and help card stay. | `40-envelope.surface.md`, `50-installation.surface.md`, `docs/RESPONSE.md`; parser-equivalence control in `unit/rust.unit` |
| DT-31.b; DT-114.a, .d, .e; Q1.d | Account correction: a host frame naming another fingerprint or producer contract is not decoded and `runner_result` is null; behavior unchanged. | `controller/README.md`, `40-envelope.surface.md` |
| DT-31.c | No change; superseded by DT-113 and DT-114. | none |
| DT-32.a; DT-119.c | Credited claim narrowed now, coverage repair with the controller thread: the support says what its two controls call; an over-capacity typed reply joins the run-level control. Until then the owner's limit reads "No control carries an over-capacity reply through `run` or `runner verify`". | `41-diagnostics.surface.md`; `unit/rust.unit` |
| DT-32.b; DT-119.b | Account correction: after execution admission `result.error` is the host reply's `error` when present, otherwise a generic unsuccessful-run message; client stdout errors accompany only refused captures. | `40-envelope.surface.md` |
| DT-32.c; DT-119.d | Account correction: the labels rule's effect is stated as exit code 1 and an explicit null diagnostics value, the form the diagnostics surface already states and the producer emits. Same decision as DT-104.b. | `35-profile.surface.md` |
| DT-42.a; Q3.c; DT-117.d, .h (whole-request part) | Behavior change (R10): `policy_check` is null for a request with an `actors` array; per-actor compile captures are unchanged. Retaining the call with a stated consequence, and removing all actor compilation, are not selected. | `controller/src/run_flow.rs`; `40-envelope`, `11-policy`, `42-dossier` surfaces, README, CONTROLLER, ARCHITECTURE |
| DT-42.b; DT-117.g | Account correction: `tool_exit_code` is 1 also when the process status supplies no numeric code, as after a signal, and for an `unavailable` capture; `stderr` then holds the controller's launch or delivery diagnostic. | `11-policy.surface.md` |
| EV.a–h | No change; records of what was executed, under another build identity. | none |
| Q1.a, .b; Q2.a–c; Q3.a, .b, .d, .e | No behavior change; Q3.b gains the ordinary held-input control. | `unit/rust.unit` |
| DT-113.e | Credited claim narrowed: "Constructed replies cross production completion and rendering". | `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-113.f, .g; LIM.f | No change. | none |
| DT-114.b | Reasoned retention of the typed gate as defensive code; limit in the README: a second comparison of the decoded reply's producer contract follows decoding and cannot refuse a frame the decoder accepted. | `controller/README.md` |
| DT-114.c, .g, .h | No change. | opt-in `runner_byoxpc/reservation_controls` |
| DT-114.f | Assertion repair: the production text is asserted where a host-frame contract refusal is constructed. | `unit/rust.unit` (controller thread) |
| DT-115.1–4 | Assertion and credit repair: refusal rows are built in the shape the parser produces; the architecture manifest's association credits are dropped; the consumer control wraps its helper capture in a fallback-shaped envelope. B9 is narrowed to the ordinary capture until the consumer question is decided. | `controller/src/run_flow.rs` tests (controller thread); `docs/architecture.json`; `tests/lib/blackbox.py` |
| DT-115.5 | No change. | none |
| DT-116.a | Behavior-neutral source change (R11): the fallback calls on the admitted branch, which cannot run for any value, are deleted. | `controller/src/run_flow.rs` |
| DT-116.b, .d | No change. | none |
| DT-116.c, .e | Reasoned retention of `xpc_error`-only eligibility with the limit beside the eligibility rule: "Eligibility follows the client's terminal event only. It does not classify whether the specimen ran: an invoked `xpc_timeout` has no fallback capture, and an eligible `xpc_error` can follow a submission call that sent no request." The test comment's noun is corrected. | `11-policy.surface.md`; `controller/integration/cli_contract.rs` |
| DT-116.f | Account correction (R11): "an envelope that carries a fallback capture carries no host reply and no execution diagnostics". | `11-policy.surface.md`, `controller/README.md`, `docs/ARCHITECTURE.md` |
| DT-116.g | Account correction: the client's timeout ends the controller's wait; no reply is synthesized. | `docs/ARCHITECTURE.md` |
| DT-116.h | Account correction of the admission order and the fallback clause. | `40-envelope.surface.md` |
| DT-117.a–c, .e | No change. | none |
| DT-117.f | Reasoned retention with the limit: a capture is associated with its actor by label and by position among the actors that carry a policy object; a null label is identified by position only. | `11-policy.surface.md` |
| DT-117.h ("before host admission") | Account correction in four owners: fallback "does not depend on host admission". The LIMITS sentence is a shared region corrected in its owner. | `docs/limits.json`, `docs/LIMITS.md`, `docs/ARCHITECTURE.md`, `docs/architecture.json` |
| DT-117.i | Assertion and credit repair: the actor fallback tests separate helper invocation policy from byte and input provenance and attribution; the limits row says oversized input is tested through the shipped helper with a request file. | `run_flow.rs` tests (controller thread); `docs/architecture.json`, `docs/limits.json` |
| DT-118.a, .c | No change. | none |
| DT-118.b, .d | Reasoned retention with the limit: admission "does not compare either with the held request; their association rests on the one client invocation that read the held bytes." | `20-transport.surface.md` |
| DT-119.a | Reasoned retention with the limit in the admitted-other row: a host label is copied without comparison with the controller's refusal spellings. | `40-envelope.surface.md` |
| DT-119.e | No change. | none |
| DT-119.f | Reasoned retention; the NSXPC inference stays labelled. | none |
| DT-119.g | Reasoned retention with the limit: the capture readers also accept `interrupted` and `invalidated`, which the shipped client does not emit. | `20-transport.surface.md` |
| PR.1–13, PR.n1, PR.n2 | No change; re-verified row by row. | none |
| REL.a–d; LIM.a–c, .e, .g–i | No change. | none |
| LIM.d | Optional coverage repair: the opt-in lost-execution control asserts the ordinary fallback capture. | `runner_byoxpc/reservation_controls` |

Shared edits. The README and ARCHITECTURE sentence that names
`execution_envelope` is corrected for DT-39.c and for DT-116.f; the
DT-116.f wording is used, because the DT-39.c wording keeps fallback
compilation joined with the diagnostics. DT-20 leaves to this row
whether the lost-reply gap stated in ARCHITECTURE becomes a tree gap
node; the assessment of this row does not take it up. The gap stays a
tour gap, and the eligibility limit above states its content.

**Discriminating check.** Controller-thread controls in
`controller/src`, written first and run against the current source: an
ordinary-form control that replaces the request file inside the client
callback and requires the helper input to be byte-equal to the client
input and `policy_check` to be the capture returned for that input; the
two actor tests with membership, content-keyed attribution and envelope
order asserted separately from a single assertion on whether the held
string is among the helper inputs (expected present before R10, absent
after); a parser-equivalence control; the over-capacity row; the
generic-message assertion. Where a claim is "present with null" the key
is asserted, not `is_null()`. Outside `controller/src`: an actor-form
row for the shipped helper in `integration/cli.integration`. For the
retained unreachable row reachability is a universal negative settled by
the caller trace.

**Consequence accepted.** For an actor request `policy_check` becomes
null, and a reader that treated a non-null `policy_check` as "fallback
ran" reads eligibility from the capture and from `actor_policy_checks`
instead. After `xpc_error` a user does not conclude from a present or
absent fallback capture that the worker ran, stopped or applied the
policy. Developers: the test corrections are `controller/src` edits and
share one signed rebuild.

**Record.** `records/trace-assessments/K-transport.md`.

### DT-33–35 — dossier first-problem and null cases; install ownership, signing and command result forms

**Established.** All ten claims hold by source reading; the review's
executions (argument-error envelopes, `runner list`, `runner reconcile`)
are no longer available and no installation was run by the review or the
assessment. `imports.failure` is first in the scanner's traversal: a
nonliteral form in the submitted source, then imports depth-first in byte
order of their names. `request_path` is null when an option's value is
refused, whether or not a path preceded it. `app_provenance` is null for
a run that ended before the manifest was read. The DT-34.a consequence is
now traced in source: a caller-supplied `XPC_SERVICE_PATH` that differs
from the bundle path makes the plist `unowned`, and `runner remove` then
leaves the plist in place and retains the cleanup record. `runner
reconcile` saves nothing. Every completed runner command reports `ok`
and exit 0, including a remove whose `cleanup_retained` is true.

**Remaining defect, limit or uncertainty.** No install has been executed
with `--env XPC_SERVICE_PATH`, and launchd's behavior with a differing
value is unobserved; neither would change a refusal placed before any
machine change. The frozen guide's sentence that `request_path` is null
"when no path was given" is contradicted and is not editable.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-33.a | Account correction: `failure` is the "first collection problem in the scanner's traversal"; the traversal order is stated and "it is not source order"; `cycle` and `exceeded` gain "in that traversal". The wording is confirmed against R12's scanner. Collecting in source order is not selected. | `42-dossier.surface.md`; order row in `witness_contract/dossier_witness` |
| DT-33.b | Reasoned retention with the limit: "Request-file path parsed from the command line; null when none was established, including when an option's value is refused, whether or not a path preceded it." | `42-dossier.surface.md` |
| DT-33.c | Account correction: null also "when the run ended before the manifest was read". | `42-dossier.surface.md` |
| DT-34.a | Behavior change (R7): `runner install` refuses an `--env XPC_SERVICE_PATH` value that differs from the bundle path, before any machine change; the install statement says so. | `runner_commands.rs`; `50-installation.surface.md` |
| DT-34.b | Account correction: unknown ownership also for a present regular file whose content cannot be converted; a present path that is not a regular file is unowned. One edit with DT-76 under DT-69–73/75–80. | `50-installation.surface.md` |
| DT-34.c | Account correction in the limits manifest; one edit with DT-69 under DT-69–73/75–80, which gives the wording. The guide's copy stays frozen. | `docs/limits.json` |
| DT-34.d | Account correction: the README says install signs the worker with the entitlements, the validator and unentitled worker without them, refreshes the inventory, then signs the enclosing bundle and host executable with the entitlements. | `controller/README.md` |
| DT-35.a–c | Account correction: a completed list, status, install, validate, remove or reconcile reports `ok`, true `ok` and exit 0, for remove also when `cleanup_retained` is true; a usage, argument, registry-load or operation refusal other than a lookup miss writes one reason to standard error, prints no envelope and exits 2. R2's registry-inspection refusal takes this stated form. | `50-installation.surface.md`, `controller/README.md`; `integration/cli.integration` |

**Discriminating check.** R7: a Rust integration row against a scratch
registry and a fixture bundle that fails no earlier check; it rejects an
install that writes a plist `plist_ownership` classifies `unowned` for
its own record, and a refusal issued after the bundle was re-signed or a
pending record saved. Dossier order: two absent import names written in
reverse order. Runner result forms: the usage refusal and `runner list`
under a scratch registry; `runner_byoxpc/registry_recovery` can assert
the `ok` label on a retained-cleanup remove.

**Consequence accepted.** A user reads `imports.records[].error` for each
import problem, does not conclude from a null `request_path` that no path
was given, does not take `ok` from `runner remove` as retirement and
treats exit 2 with empty standard output from a runner command as a
refusal on standard error. A caller that supplied a differing
`XPC_SERVICE_PATH` is refused.

**Record.**
`records/trace-assessments/C1-identity-classification-vocabulary.md`,
section 5.

### DT-36/43 — gate reap before ownership-loss classification; lifecycle rendering and resolution

**Established.** All six claims hold by source reading; the review did
not execute them and nothing was retained. After a failed visit the
scheduler cancels as `unresolved_termination` whenever the failed actor
is not reaped and reaches `ownership_lost` only for a reaped actor; an
ECHILD wait error leaves the child unreaped. The unit test that injects
ECHILD asserts `quiescence == "unresolved"` and a non-nil cancellation
without naming a label. Actor-form dispositions are resolved with no
plan, from each actor's collected slot list, and mark every slot
`supported`; retained captures at `8b5de2b2` show that value for issue,
transfer, consume and release steps. Both request forms refuse an
unsupported attempt at admission, so the two resolutions agree for every
admitted request. The lifecycle surface's support sentence names gap
nodes the surface does not declare; the equipment surface carries the
same sentence with no gap node.

**Remaining defect, limit or uncertainty.** The operator rule omits that
the timeout and wait-error reasons apply only after the reap is
confirmed. `ownership_lost` needs a wait failure other than ECHILD
followed by a later reap; with the production wait that is unlikely
outside an injected fault, which is an inference. The resolution rule
and one code comment say "submitted plan" for both forms.

**Treatment.** No product behavior changes; reporting `ownership_lost`
for an unreaped child would name a cause while the ending is unknown.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-36.a | Account correction stating the precedence: "After a failed active visit establish that actor's reap before any further activation; unresolved termination cancels the remaining schedule, including after a wait error that leaves the actor unreaped. Once the reap is confirmed, an arrival or completion timeout cancels for exhausted execution allowance and a wait error cancels for lost ownership." | `13-actors.surface.md` `actors.phase.order` |
| DT-36.b | Assertion repair: the ECHILD case asserts `unresolved_termination`; a new case with a non-ECHILD wait failure followed by a reap asserts `ownership_lost`. The support's "cancellation conditions" credit is then earned. | `ActorSchedulerTests.swift`; `runner_unit/pwrunner_core_unit_executable` |
| DT-36.q | No change. | none |
| DT-43.a | Account correction: the ordinary form joins acquired output and slot identities to the submitted plan; the actor form takes each actor's steps from that actor's collected slot list, in which every slot is a supported operation. The code comment is corrected with the host thread. Passing the declared actions to the resolver is not selected. | `32-lifecycle.surface.md`; comment in `CWorkerDisposition.swift` |
| DT-43.b | Account correction: "JSON carries the chosen alternative's value directly: an integer for an exit code, signal or item index, or the termination-request object. The alternative labels are not JSON keys." | `32-lifecycle.surface.md` |
| DT-43.c | Account correction of the support text to "Imported public field definitions joined to producer/decoder/assessment meanings." in both surfaces. | `32-lifecycle.surface.md`, `34-equipment.surface.md` |

The `actors.phase.order` sentence is edited for DT-10 as well. The two
proposed wordings need care when merged: the DT-36 text places the
allowance label after a confirmed reap, while DT-10 establishes a
pre-visit site that selects the same label with neither collection nor a
reap. One edit serves both when the DT-10 clause is added as a separate
sentence covering a wait or a schedule entry that begins with no
remaining allowance, including an unavailable clock.

**Discriminating check.** The two scheduler cases above reject a
scheduler that labels an unreaped actor `ownership_lost` and one that
continues the schedule after a wait error on a reaped actor. For DT-43.a
further evidence would not change the decision: the admission refusals
make the two resolutions agree.

**Consequence accepted.** When `schedule.cancelled` is
`unresolved_termination` a user treats the failed actor as possibly still
running and does not read the absence of `ownership_lost` as retained
ownership. Developers: none.

**Record.** `records/trace-assessments/E-custody-setup-trigger.md`,
Subject 1.

### DT-37–41 — smaller statement/source differences, support scope, prose accounts, index spelling, tour commitment lists

**Established.** All thirty-four claims hold at `837296af` by re-reading;
no surface file and no hand-written product source differs from the
reviewed tree. The review's reproduction outputs are absent, so each
"reproduced" item is an account of an earlier observation. One contrast
was re-executed now on the `2f4d76e4` app: the shipped validator answers
`parse_error` for an unknown `filter_type` without `filter_value` and
`bad_filter` for the same type with a value (DT-37.a). Recounts over the
loaded tree confirm 180 index rows, 199 routing units, 19 surfaces and 930
changed-item rows. Corrections to the review: DT-38.c credits the
constructed-frame comparison to the wrong test body (it is the adjacent
"actual text budget failure" test); DT-40.d2's two `admit_reply` rows are
path-qualified and distinguishable; DT-37.c is not a contradiction, since
both accounts hold at their own observation point.

**Remaining defect, limit or uncertainty.** In every case the producer's
behavior is coherent and tested; the defects are in statements, support
metadata, tour lists and two frozen guide sentences. No control submits a
granted lease above the requested lease (DT-37.b). The 128-byte and
64-byte reproductions behind DT-37.f were never repeated;
`failure_boundaries/admission` exercises the same boundary. No
`runner validate`, build or battery was run for these entries.

**Treatment.** No product behavior changes.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-37.a | Account correction: grammar refusals, including any `filter_type` other than NONE without `filter_value`, use `parse_error`; an unrecognized type that passes the grammar uses `bad_filter`. Coverage repair: the unknown-type pair joins the direct-batch control. | `21-wire.surface.md` `wire.validator.emit`; `validator_batch_mode/batch_ndjson_roundtrip` |
| DT-37.b | Reasoned retention; every stated claim is true. Limit already beside the claim: "A client accepts a positive value no greater than the requested lease." | `runner_unit/client_session_controls` |
| DT-37.c | Reasoned retention; the limits row already says the delay is "within the remaining allowance". | `runner_unit/client_session_controls` |
| DT-37.d | Account correction: one sentence says a query satisfying the condition is admitted, receives no validator query and reports `prediction_unavailable`; the condition is not an admission requirement. | `12-probes.surface.md` `probes.query.excluded`; `runner_filter_*/prediction_unavailable_attempt_observed` |
| DT-37.e | Account correction of the stale support limit: duplicate query-key behavior has check-read support under its child owner. | `21-wire.surface.md` `wire.validator.support` |
| DT-37.f | Account correction: the four fields gain their limit span and the order ("a capacity refusal, decided before the vocabulary check"). | `12-probes.surface.md`, `11-policy.surface.md`; `failure_boundaries/admission` |
| DT-37.f-q | No action; the default case covers the boundary. | `failure_boundaries/admission` |
| DT-38.a | Coverage repair in the owner: cite the worker-evidence and disposition-resolver tests that assert provenance; narrow the pin; add the limit that no cited control asserts `attempt_not_supported` provenance through the step builder. | `31-steps.surface.md` |
| DT-38.b | Credited claim narrowed: the record's order equals the order supplied; the test adapter appends the lifecycle limitation. | `31-steps.surface.md` |
| DT-38.c | Account correction of an understated pin: the cited test runs both the minimal and the empty path. | `30-reply.surface.md` |
| DT-38.d | Assertion repair: the cited test gains two ordering assertions and the pin stands. If they are not added, the pin is narrowed with the limit "The control reads one final result and does not order the reap after the gate's timeout." | `ActorSchedulerTests.swift`; `33-actor_evidence.surface.md` |
| DT-39.a | Account correction in the shared-region owner; the guide's copy stays frozen. One edit with DT-59; see DT-59–61/133 for the wording. | `docs/EXTENSIONS.md` |
| DT-39.b, .c, .d, .g | Account corrections of four authored sentences or links. | `runner/README.md`, `controller/README.md`, `docs/ARCHITECTURE.md`, `docs/WORKER.md` |
| DT-39.e | Reasoned retention under the guide freeze. Limit: the owned-reap `capture_ordinal` is a required positive integer; `lifecycle.owned_reap.capture_ordinal` governs. | none |
| DT-39.f | Reasoned retention under the guide freeze. Limit already at `refusals.request`: readers classify by the structured code, here `augment_unavailable`; the error text is a human diagnostic. | none |
| DT-40.a1, .a2 | Account correction: "The commitment index has one row for each routed subject. A surface's own heading carries its introduction and surface-wide support, and the changed-item index names that heading where support is declared for the whole surface." | `docs/contract/trace-introduction.md` |
| DT-40.b | Reasoned retention; the second sentence above states the limit. | same |
| DT-40.c1 | Coverage repair: cite the definition beside each of the four call sites. | four surface owners |
| DT-40.c2 | Reasoned retention; source citations are deliberately free strings. | none |
| DT-40.c3 | Citation made specific: `pub fn decode<T: WireRead>(data: &[u8])`. | `21-wire.surface.md` |
| DT-40.d1 | One definition-like spelling per symbol for the six split symbols. | their owners |
| DT-40.d2 | Reasoned retention; rows are path-qualified. | none |
| DT-40.e1 | Reasoned retention under "an absent association is an unknown". | none |
| DT-40.e2 | Reasoned retention with one added sentence: limit identifiers have no rows; a statement that embeds a limit shows its identifier. | `trace-introduction.md` |
| DT-41.a | Account correction: one sentence in the WORKER section says what an `unapplied` actor runs under; the list entry stays. | `docs/WORKER.md` |
| DT-41.b1 | Arrangement change in the map: `equipment.binding` is replaced by `request.options` in CONTROLLER's selection list. | `docs/contract/presentation.json` |
| DT-41.b2, .b3 | Arrangement change: `steps.assessment.fresh` is replaced by `diagnostics.execution`; `diagnostics.issue` and `profile.receipt.labels` join the admission list. | `presentation.json` |
| DT-41.b4 | Arrangement change: four rules join the preparation list. | `presentation.json` |
| DT-41.q | No action; accurate. | none |

Shared edits. DT-16 and DT-41 concern lists under one generated lead-in.
Both passes keep the lead-in and repair entries, so one edit of
`presentation.json` serves both. The passes' reasons conflict on one
entry: DT-16 removes `equipment.binding` from BUILD's signing list, while
the reason given for DT-41.b1 says it "stays listed in BUILD". Both
removals stand; `equipment.binding` then reaches a tour list only through
`equipment.binding.bind` in WORKER, and the DT-41.b1 reason is corrected
to say so. The DT-14.e, DT-20.b, DT-40.a1 and DT-40.e2 sentences fall in
one paragraph of `trace-introduction.md` and land as one edit. The DT-37.f
spans and the DT-18.b presence rules edit the same four field meanings.
The sentence DT-39.c corrects in `controller/README.md` and
`docs/ARCHITECTURE.md` is also corrected for DT-116.f; the wording
proposed here (name `run`, which fills the record with "fallback
compilation", and `execution_parts`, which joins it with the diagnostics)
keeps a pairing the transport assessment shows cannot occur, so the
DT-116.f wording is used (see DT-31/32/42/113–119).

**Discriminating check.** Existing cases named in the table, plus:
`batch_ndjson_roundtrip` gains an unknown type without a value
(`parse_error` naming `filter_value`) and with a value (`bad_filter`);
`ActorSchedulerTests` asserts that the gate carries no reap reference and
that the source's owned-reap capture ordinal exceeds the gate's. For the
retained items reading suffices: no statement is false.

**Consequence accepted.** A direct caller of `sb_api_validator --batch`
expects `parse_error` for any non-`NONE` type sent without a value. Users
classify refusals by `request_failure.code`, read `capture_ordinal` as
always present and do not read `prediction_unavailable` for an excluded
pair as a refusal. Developers do not conclude from CONTRACT's indexes that
an unlisted symbol or limit affects no commitment.

**Record.** `records/trace-assessments/B-smaller-differences-leads.md`,
Subject A.

### DT-44 — thirteen leads, and the CONTRACT-tracing coverage statement

**Established.** The review confirmed only that each cited statement
exists. Each lead's producer is now read at `837296af` against the
statement's owner: twelve are confirmed in whole or in part by reading,
one (f) is confirmed by reading with its reply-level outcome not executed,
none is refuted outright. Narrowings: a1 is only partly right (one
termination-gate path does follow fallback sleeps); h is partly refuted
(the capacity-refusal `unknown` is stated at `refusals.admission.echo`;
only the reply field omits it); b1 and k are not contradictions. Retained
development runs record `pass` for `failure_boundaries/admission`, which
anchors h and k. The five claims of the review's "Coverage and limits of
the CONTRACT tracing investigation" (CL.1–5) are placed here: both stamp
checks print current; the review's counts (526 citations, 2,033 anchors,
130 rules) are not reproducible and nothing rests on them; its scratch
directory is absent.

**Remaining defect, limit or uncertainty.** All seventeen DT-44 claims are
statement defects or accurate observations; none needs a product change.
Leads e, f and j are not executed: e needs a substituted validator, f a
reply-level actor run with a shortened schedule allowance, j a
`runner validate` with the registry read back. A statement the review
lists as "traced and found consistent" (CL.3) is not thereby verified.

**Treatment.** Each lead has its own subsection under "DT-44 leads" below.
Summary:

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-44.a1–a3 | Account correction of `lifecycle.host_wait.stop`. | `32-lifecycle.surface.md` |
| DT-44.b1, .b2 | Account correction of `schedule.cancelled` and `actor.setup_status`; constructed control for the never-launched actor. | `33-actor_evidence.surface.md`; `ActorSchedulerTests` |
| DT-44.c | Account correction of `lifecycle.progress.index`. | `32-lifecycle.surface.md` |
| DT-44.d | Account correction ("without a completed slot"); constructed control. No product change. | `32-lifecycle.surface.md`; `DispositionResolverTests` |
| DT-44.e | Account correction of `read_error` and `stdout_collection_stop`; no fixture. | `32-lifecycle.surface.md` |
| DT-44.f | Reasoned retention of `runner_failed` for actor schedule-allowance expiry, stated in `reply.record.outcomes`. | `30-reply.surface.md` |
| DT-44.g | Account correction in the shared-region owner. | `docs/EXTENSIONS.md` |
| DT-44.h | Account correction completing `reply.record.policy_format`. | `30-reply.surface.md` |
| DT-44.i | Account correction stating both sampling points. | `33-actor_evidence.surface.md` |
| DT-44.j | Account correction of the validate rule and three registry fields. | `50-installation.surface.md` |
| DT-44.k | Reasoned retention; no statement is false. | `failure_boundaries/admission` |
| DT-44.l1, .l2 | Account correction of two lifecycle texts. | `32-lifecycle.surface.md` |
| DT-44.m | Account correction of the family row. | `41-diagnostics.surface.md` |
| CL.1 | Retained; the counts are not reused. | none |
| CL.2 | Retained; accurate. | none |
| CL.3 | Retained with the limit: a statement listed there is not a verified statement; verification is the per-claim reading in the assessments. | this plan |
| CL.4 | Retained; this plan's coverage map says what later sections reached. | this plan |
| CL.5 | Retained; every lost reproduction is treated as an account. One row is added to "Evidence availability and reuse limits" for the CONTRACT-tracing scratch directory (absent; accounts only). | this plan |

**Discriminating check.** Per lead below. For CL.1–5 further evidence
would not change the decision: they are statements about the record.

**Consequence accepted.** Users: see the lead subsections. Developers:
none.

**Record.** `records/trace-assessments/B-smaller-differences-leads.md`,
Subjects B and C.

### DT-45/47/49/52 — status-word promise, pre-encoding versus encoded checks, diagnostic native return, errno-key presence

**Established.** No claim fails at `837296af`. The review's executed
evidence (`/private/tmp/pw-failure-trace-elssragi/`, the `8b5de2b2` app)
cannot be replayed; every row here rests on source reading, read-only git
and three constructed in-memory checks. The eleven identity and limit
claims of the failure-contract investigation (FI-1–7, FL-1–4) are placed
here and retained as written. DT-45: the worker writes `apply_rc` once,
with the return of the application call; preparation and compilation
failures publish failure records; the host does not read the word without
an observed application, and two unit tests assert exactly that. The
status-word promise dates from `0670db1d`; `bc3abe2f`, first contained in
`v0.3.5`, changed the implementation. DT-47: two coverage rows credit
"actual subprocess encoding" where the tests assert on the typed record
and discard the encoded bytes. DT-49: the failure contract says a
diagnostic keeps `rc = -1`; RESPONSE and the producer give the record's
carried return. DT-52: `consumer.validate` accepts a step whose
`attempt.errno` key is deleted. The review is incomplete on DT-52: it did
not examine `tests/lib/blackbox.py` `validate_step`, which rejects the
missing key and has rejecting controls in two registered cases, so the
gap is confined to `consumer.validate`.

**Remaining defect, limit or uncertainty.** The failure contract states a
commitment the product has not kept since `v0.3.5` (DT-45), overstates
two coverage rows (DT-47), restates `rc` less precisely than RESPONSE
(DT-49) and does not say which reader holds the presence obligation
(DT-52). Outside the review: the contract's compile-failure row says
"R=-1", a third coverage row credits the binary writer, and two source
comments still describe the status-word writes. No shipped worker was
shown to reach a record-less terminal failure with a nonzero word. No
registered assertion covers a diagnostic that carries a return.

**Treatment.** No product behavior changes.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| FI-1–7, FL-1–4 | Retained as written; an executed observation from this investigation needs a rerun on an identified build. | none |
| DT-45.a, .b | Account correction that withdraws a stated commitment: the contract says R is written only with the application call's return and read only beside A; a terminal publication without A and without a failure record is reported as completed without an observed application; neither R nor `apply_errno` is read. The wording does not cover the actor form's two record-less publications. Restoring the scalar path is not selected. | `tests/FAILURE-PROPAGATION-CONTRACT.md` (authored prose); `runner_unit/pwrunner_core_unit_executable`, `runner_c_worker_harness/compile_failure` |
| DT-45.c | No change to the tests. | none |
| DT-45.d | Credited claim narrowed: the coverage row says the written word is not read. The "R=-1" compile-failure row takes the same correction. | same file |
| DT-45.q | Retained qualification. | none |
| DT-47.a | Credited claim narrowed: the two rows credit the assembled record and successful encoding and name the CLI cases that assert the encoded facts; the third row's "binary writer" credit takes the same wording. | same file; `witness_contract/worker_attempt_in_flight_at_deadline`, `witness_contract/worker_termination` |
| DT-47.b, .q | Retained. | none |
| DT-49.a | Account correction to the RESPONSE meaning (the record's carried return, or -1 when it carries none), with a new carried-return control. | same file; `failure_boundaries/validator_frames` |
| DT-49.b, .c, .q | Retained; DT-49.b becomes the control's expected result. | none |
| DT-52.a | Account correction stating reader scope, with the limit: "`consumer.validate` does not establish that a nullable step key is present; it accepts an absent `errno` as it accepts `null`." Adding the presence check to the consumer is optional. | same file; `blackbox_menagerie/validation_controls` |
| DT-52.b–d, .q | Retained. | none |

The two stale source comments are in build-contract and worker-identity
inputs and are corrected with the exec-stream thread's rebuild.

**Discriminating check.** DT-45: the existing unit cases reject a host
that reads the header word without A; `compile_failure` rejects a worker
that fails compilation without a failure record. DT-49: a validator tail
that keeps `rc` 17 and `errno` 5 under an unknown outcome expects
`native_rc` null, `rc` 17, `outcome` `error`, `finished` and
`unestablished`; it follows the validator-substitution route current when
it lands. For DT-45 further evidence would not change the decision: the
question is which statement is current, and source and tests agree.

**Consequence accepted.** A user reads a pre-application failure from
`runner_subprocess.worker_evidence.failure` and does not expect a status
value or `apply_errno` in `error` text. Developers do not take
`consumer.validate` alone as establishing nullable-key presence.

**Record.**
`records/trace-assessments/C2-failure-contract-producer-reader.md`,
"Investigation identity, conventions and limits", Subject A and "Outside
the review".

### DT-46/120/121/129 — cleanup-trigger derivation and time; actor stop-reason mapping

**Established.** No claim fails at `837296af`. By source reading:
`requestExit` stores no trigger; `collectOutput` computes
`triggerForStop[pollStopReason] ?? pollStopReason` after grace, kill and
reap; every writer of the stop reason runs before the matching exit
request, so the value equals what a store-time capture would have given.
One stored string fills seven reply values. DT-120.d is confirmed by git
and narrows DT-46.d: the value was fixed at the store until `c686a05f`
and at final collection since, and was never independent of the stop
reason. Retained public captures at `8b5de2b2` under
`.tmp/contract-trio/observation-time/` were re-read: an ordinary host
kill projects `host_sentinel_deadline` (E4); an actor host kill with the
same request result, exhausted grace and reaped signal projects
`termination_cause: unknown` and `stop_reason: null` under trigger and
stop `schedule_complete` (E5); an actor reaped at the gate still shows
`exit_requested: true` with `cleanup_trigger: completion` (E3). DT-129.c
is narrowed: the declared transfer phase and the host's servicing phase
are not invariantly equal, since a request left pending after a
worker-side timeout or clock fault is serviced in a later visit of the
same source; the published statement ("Phase in which this transfer
action was declared") stays true.

**Remaining defect, limit or uncertainty.** The failure contract and the
lifecycle surface describe the trigger as a host fact "recorded at the
exit-request store" and as a witness; it is a derived restatement. The
six-value lists are false for actor replies. Only `schedule_complete`
was executed in the actor form; an actor stopped for an arrival,
completion or setup timeout and then killed has no executed observation.
No registered case applies the ordinary form's position (an `unknown`
cause beside the host's own kill record is a defect) to the actor form.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-46.a, .b; DT-120.b, .d | Account correction: the trigger is "derived at final collection from the stop reason it held when it stored the request", the map is listed, "any other stop reason is carried unchanged", and "the value restates poll_stop_reason and is not a second observation". The failure contract's three passages take the same account, with the request result, exhausted grace and owned final status named as the independent observations. Two stale comments are corrected. | `32-lifecycle.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md` (authored, outside the shared regions); `tests/lib/lifecycle_contract.py`; comment in `CWorker.swift` |
| DT-46.c | Credited claim narrowed in the support limits: "The test constructs each trigger and stop pair; it does not exercise the host's derivation of the trigger." The Rust test is not renamed. | `41-diagnostics.surface.md` |
| DT-46.d, .q; DT-120.a, .c, .f, .g | No change. | none |
| DT-120.e | Assertion repair: the independent oracle checks that the trigger is the table image of the stop reason. | `tests/lib/lifecycle_oracle.py`; `blackbox_e2e` disposition controls |
| DT-121.a, .c, .e | Behavior change (R13): the host maps `schedule_complete`, `ended_before_arrival` and `ended_before_completion` to `completion`, so a witnessed host kill at schedule end projects `host_exit_grace_exhausted`. `poll_stop_reason` keeps the scheduler's string. | `PWRunnerDisposition.swift`; mirror table in `tests/lib/lifecycle_contract.py`; `witness_contract/actor_compositions` |
| DT-121.b | Account correction: "The actor scheduler never records sentinel_deadline, so no actor reply selects the deadline case." The row stays. | `41-diagnostics.surface.md` |
| DT-121.d | Account correction: the scheduler's own reasons are outside the six projected values and project null; the actor's subprocess record keeps them in `poll_stop_reason`. The failure contract's `stop_reason` row is aligned. | `41-diagnostics.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-121.q | Reasoned retention; no new cause label is added. Limit stated after the actor cause table and after the contract's label table: "An actor stopped for an arrival, completion or setup timeout, a protocol violation, a withheld release or a failed setup keeps the scheduler's reason as its trigger. Its cause stays `unknown` even when the request result, exhausted grace and final status are all carried; read them in that actor's subprocess record." | `41-diagnostics.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-129.a | Reasoned retention with the limit beside `exit_requested`: "The host also performs this store for a child it has already reaped; `grace_end: not_entered` and, for an actor, `owned_reap.departure_requested: false` then record that the ending preceded the request." | `32-lifecycle.surface.md` |
| DT-129.b, .c | No change. | none |
| DT-129.d | Disposed of with DT-62.d under DT-62/65/122/123. | DT-62/65/122/123 |

One edit of the `cleanup_trigger` meaning serves DT-30.d, DT-46, DT-120
and DT-121.a. The two assessments each leave the vocabulary-block
question to the other. It is settled here: because unmapped scheduler
reasons still pass through after R13, the field takes an open,
illustrative vocabulary block in the form `poll_stop_reason` uses, beside
the derivation text above with the three actor reasons named after
`done`. The host thread writes the block from the mapping it implements. The DT-44 lead f sentence on `runner_failed` is consistent with
this row.

**Discriminating check.** The oracle derivation check lands first with
the current table and runs against the current app, where it passes;
table and product then change together. After the rebuild,
`witness_contract/actor_compositions` gains an actor hang longer than the
exit grace and asserts `poll_stop_reason: schedule_complete`,
`cleanup_trigger: completion`, `grace_end: exhausted`, the kill request
and `termination_cause: host_exit_grace_exhausted`; the existing
clean-exit row keeps a null cause, and an actor that ended on its own
signal stays `unknown` with `grace_end: not_entered`. The order-barrier
control is not triggered by the table change; it runs with the host
thread because R9 changes eligibility.

**Consequence accepted.** Actor replies change: `cleanup_trigger` reads
`completion` where it read `schedule_complete` or `ended_before_*`, and a
consumer comparing the actor trigger with the stop reason for equality
sees a difference. A user does not count the trigger as an observation
beyond the stop reason, and for timeout, violation and failed-setup stops
still reads the kill record because the cause stays `unknown`.

**Record.** `records/trace-assessments/E-custody-setup-trigger.md`,
Subject 2 and "Outside the review".

### DT-48/130 — native label/return coherence versus order eligibility; implication versus equivalence in order readers

**Established.** All twenty-two claims hold. The Python cells of the
review's tables are reproduced now on the retained live and seam
envelopes; Rust cells come from retained output; Swift is source
reading. The shipped validator derives `allow` or `deny` from the native
pair, so label and pair cohere for every record it emits. The host
admits a record by type and presence, projects label and pair side by
side, and tests their agreement only as a condition of `query_first`. A
steered record `allow` with `rc` -1 and `errno` 13 is accepted by every
boundary when no order is claimed: `finished`, `unestablished`,
controller `valid`. The order rule is an equivalence stated of the
producer. Rust and Swift reporting check one direction (a claimed
`query_first` needs an eligible record and the complete chain); the
Python consumer checks both. On a constructed frame with an eligible
record and a withheld order, Rust reports `valid` and the consumer
rejects. By source, no host-produced reply is consumer-eligible and
host-ineligible. A valid unfavorable operation is not invalid evidence.

**Remaining defect, limit or uncertainty.** No statement says that
admission does not compare a label with its return, or which direction
each recipient checks. `unestablished` has several causes and no field
states which. Outside the review: the consumer's chain also requires
`arrival_observed`, one condition more than the stated chain. The
structural acceptance pattern's history was not re-read.

**Treatment.** No product behavior and no reader changes. Refusing an
incoherent frame at line admission, making Rust check both directions
and narrowing the consumer to the implication are not selected.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-48.a–g, .t1–.t3, .t5–.t7; ACC-MAP.wire; ACC-CLS.1; ACC-XREF.48 | Reasoned retention; accurate. | `runner_unit/pwrunner_core_unit_executable` (ordering tests); `blackbox_e2e/checker_controls` |
| DT-48.t4 | Reasoned retention with the limit stated: "Admission does not compare an `allow` or `deny` label with its `rc` and `errno`; that relation is the emitter's, and the host tests it only as a condition of `query_first`." The failure contract says the labels are "the validator's classification of its native returns". | `21-wire.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-130.a; ACC-RES.order | Account correction naming each recipient's direction: the controller compares "each claimed `query_first` against its complete chain. An `unestablished` order is not compared with eligibility."; the consumer checks `order` "in both directions". | `41-diagnostics.surface.md`; `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-130.b–d | Reasoned retention of both reader behaviors, pinned by a reader-corpus row with a consistent binary capture. | `ReaderCorpusTests.swift`; `runner_unit/pwrunner_core_unit_executable` |

The wire sentence that gains the limit is the one R5 rewords for the
empty identifier; the two edits are made together.

**Discriminating check.** A reader-corpus row with an eligible record,
the complete chain and `order` set to `unestablished`: the host accepts,
Rust admits with `valid`, the consumer rejects with "eligible record
with complete chain requires query_first". The incorrect behavior that
stays rejected is an incoherent record acquiring `query_first` (existing
ordering tests and the consumer's claimed-order control). Further
evidence would not change the retention: the incoherent state needs a
validator other than the shipped one.

**Consequence accepted.** A user reads a validator-sourced `allow` or
`deny` together with `native_rc`, `rc` and `errno`, treats it as a
prediction about the live specimen only when `comparison.order` is
`query_first`, and does not conclude from `disposition_integrity: valid`
that every `unestablished` order was unavoidable. Developers: the
controller does not detect a producer that under-credits order; the
consumer does.

**Record.** `records/trace-assessments/L-readers-acceptance.md`,
section 2.

### DT-53/132/135 — lifecycle-claim coverage, byte-consistent envelope readers, shared predicates

**Established.** No product claim fails at `837296af`. Thirty claims,
plus the eleven identity and limit claims of the acceptance
investigation (ACC-ID.a–h, ACC-LIM.a–c), which are placed here.
Re-executed now with the current Python readers: deleting
`final_status`, changing its value to 17 beside raw exit 0, or nulling
it leaves `consumer.validate` at no finding on the bare reply, while the
lifecycle oracle reports D8 `malformed_record` or D1 `wrong_answer`; on
the retained byte-consistent seam frames Rust projects `withheld` and
`invalid` and the public result is unchanged (`finished`, exit 0).
Editing a live envelope's JSON while leaving its binary bytes makes the
consumer object for a different reason, the capture comparison. The
review's registry counts are understated: about forty-nine default live
cases reach the consumer with no oracle (the review says twenty-eight),
because the static map did not follow `blackbox.validate_run_shape`,
`unavailable_prediction.py`, the footprint workloads or inline shell
Python; and `witness_contract/extension_combinations` also runs the
oracle. On every live envelope retained by the checkpoint run the oracle
reports no finding, so invoking it in a consumer-only case would pass on
current output. Shared predicates: the oracle's phase-collection,
ownership and extension findings are the consumer's own functions, and
Swift reporting validation calls the production association and
eligibility functions over reply-visible inputs; repeated use of one
predicate is one judgment.

**Remaining defect, limit or uncertainty.** The failure contract's
reader paragraph does not say outright that the consumer checks no
lifecycle claim. One default live case carries lifecycle credit without
the responsible check. Three statements credit independence the code
does not have. The reader corpus holds one verdict for three readers and
so no ordinary-form claim fault. The case map is a static text search
and a lower bound. No Swift reporting validator was run on an edited
frame.

**Treatment.** No reader is added and the consumer is not broadened.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| ACC-ID.a–h; ACC-LIM.a, .c | No change; accurate records. The seam and Swift limits stay attached to every seam-derived statement. | none |
| ACC-LIM.b; DT-53.t8, .t9; DT-132.c | The corrected reader population is recorded here; the retained case map is not reused as a complete list. No tree change. | this plan |
| DT-53.a; DT-132.b | Account correction in the reader paragraph: "The consumer does not check lifecycle claims: a record whose claim is absent or contradicts its raw field passes it. The lifecycle oracle and the controller's lifecycle checks reject such a record, and the envelope result is unchanged." | `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-53.b–f, .t1–.t7; DT-132.a; ACC-RES.readers; ACC-XREF.53 | Coverage repair: the accepted baseline, the missing `final_status` and the wrong value beside unchanged raw status are retained in the reader corpus on a consistent binary capture, with per-reader expectations (host rejects; Rust admits while its projection withholds; consumer accepts; oracle rejects). | `ReaderCorpusTests.swift`, `tests/suites/runner_unit/reader_corpus.py` |
| DT-53.g, .t10; ACC-CLS.7 | Assertion repair for the one caller whose lifecycle credit lacks the responsible check: the oracle is invoked in `witness_contract/pre_apply_failure_reports_no_policy_verdict`. The consumer-only cases with no lifecycle-claim credit are narrowed once, by the reader-paragraph sentence. Four other callers assert the controller's projection against their own expectation and are unchanged. | `check_pre_apply_failure.py` |
| DT-135.a, .d; ACC-MAP.same; ACC-MAP.readers; ACC-CLS.2 | Reasoned retention with the limit: agreement between the consumer and the oracle on phase collection, ownership or extension evidence is one judgment; agreement between host reporting and host production on association or order is one predicate over two inputs. | `tests/lib/lifecycle_oracle.py` docstring |
| DT-135.b | Credited claims narrowed in three statements. | `tests/COVERAGE.md`, `extension_controls.py` comment, oracle docstring |
| DT-135.c | Resolved with DT-25/50/131: the missing equality relation is stated with R9. | DT-25/50/131 |

DT-57.d and DT-107.f point here: an empty-identifier judgment and four
variant edits are oracle-only or controller-only judgments of the same
kind and need no separate treatment. The reader paragraph is also edited
for DT-52 (nullable-key presence); the section is written once.

**Discriminating check.** The corpus rows reject an oracle or controller
that accepts an absent or wrong `final_status`, a consumer verdict
credited as a claim check, and a result that changes with the finding.
The revised `pre_apply_failure` checker runs first against the current
app; replay over its seven retained envelopes predicts no finding. The
oracle's own sensitivity stays with `blackbox_e2e/checker_controls`.

**Consequence accepted.** Users: none beyond what the envelope surface
already states (`result.ok` and exit 0 do not certify the controller's
relationship checks). Test authors do not take `consumer.validate == []`
as establishing lifecycle claims, and do not count a consumer rejection
of a JSON-edited live envelope as a claim check.

**Record.** `records/trace-assessments/L-readers-acceptance.md`,
sections 0 and 3 and "Outside the review".

### DT-54/58 — collection byte-limit stop; empty-byte fallback beyond the minimal report

**Established.** All seven claims hold by source reading; the review's
substituted-validator run is not available. The collector assigns six
`stdout_collection_stop` values and RESPONSE lists six; the failure
contract lists four. `byte_limit` is asserted through the CLI by
`witness_contract/phases` and in `runner_unit`, both with a substituted
validator. The service function returns empty bytes when the minimal
writer also fails, RESPONSE says so, and a constructed test asserts it;
the failure contract calls the minimal reply the "final path".

**Remaining defect, limit or uncertainty.** `clock_error`, `poll_error`
and `read_error` have no assertion anywhere; they are source-read.
Production reachability of the empty-bytes branch is unresolved: it needs
an encoder fault that defeats the independent minimal writer on a real
result, and no such input is known. The controller's label for a
zero-length host result (`malformed_runner_response`) is source-read; no
registered case submits one.

**Treatment.** Account corrections only; neither accepted uncertainty
establishes the underlying fact.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-54.a | Account correction: the contract lists `eof`, `clock_error`, `deadline`, `poll_error`, `byte_limit` and `read_error`, and says `read_error` keeps the read, poll, deadline, clock or byte-limit diagnostic. The corrected text does not say the three unasserted values are exercised. | `tests/FAILURE-PROPAGATION-CONTRACT.md` (authored, outside the shared regions) |
| DT-54.b, .c, .q | Retained; accurate. | `witness_contract/phases` |
| DT-58.a | Account correction: after the minimal reply, if the minimal writer also fails the host returns zero bytes; the recipient cannot decode them and no reporting-failure object, identity or original summary is delivered. The minimal reply is named as the last structured form. | same file |
| DT-58.b | Retained; accurate. | `runner_unit/pwrunner_core_unit_executable` |
| DT-58.q | Retained; reachability stays unresolved. A recipient-side control for a zero-length host result is not required for the correction. | none |

The DT-44 lead e correction of `lifecycle.validator.read_error` lists the
same five conditions; the two edits use the same list.

**Discriminating check.** Existing: `witness_contract/phases` and
`runner_unit/pwrunner_core_unit_executable` reject a collector that
crosses the byte allowance and reports another stop value or decodes the
cut fragment; `ReplyFailureTests` rejects a service function that returns
a nonempty result when the minimal writer fails.

**Consequence accepted.** A reader that switches on
`stdout_collection_stop` handles six values. A zero-length host result
carries no reporting-failure account, and its absence of evidence is not
a statement about the worker.

**Record.**
`records/trace-assessments/C2-failure-contract-producer-reader.md`,
Subject B.

### DT-55/56 — exec retained output: embedded NUL and split UTF-8

**Established.** All thirteen claims hold. The review's five runs on the
`8b5de2b2` app are not available. The mechanism is read in source: the
worker copies bytes including NUL, places the 16-byte marker by byte
offset, and the host's `readString` stops at the first NUL and returns an
empty string, which the caller turns into an absent field, when the bytes
are not valid UTF-8 as a whole. A model written from that source, fed the
direct output of the review's five argument arrays, reproduces all five
rows; it is a constructed check, not a product run. The review is
incomplete on DT-55.g: a registered live case,
`runner_use_c_worker/exec_attempt_stdout_truncation_marker`, exercises
ASCII overflow with the marker; it covers neither NUL nor multi-byte
text.

**Remaining defect, limit or uncertainty.** An absent `stdout` is stated
as empty output and accompanies nonempty output in three input classes;
a NUL hides the truncation marker; no count of dropped bytes exists.
Undecided for the implementer: whether the worker or the host composes
the marker, and the reply-maximum margins once replacement can triple a
stream's wire bytes (`ReplyMaximumTests`,
`witness_contract/max_targets_reply_survives`), which need recomputation
on a build.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-55.a, DT-56.a | Behavior change (R1): stream text is the decoding of every retained byte (NUL as U+0000, invalid sequences as U+FFFD), cut on a scalar boundary before the marker; `exec_observation.collection.<stream>` gains required bytes received, bytes retained, truncated and an exactness indication. The field statement, the stream-observation fields, the limits coverage note and the failure contract sentence land with it. | C worker, layout, Swift decode, wire schema, three readers; `31-steps`, `32-lifecycle` surfaces, `docs/limits.json`, `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-55.b | Retained as the unchanged control; the existing truncation case passes unmodified and gains its counts. | `runner_use_c_worker/exec_attempt_stdout_truncation_marker` |
| DT-55.c, .d | Become the two embedded-NUL contrasts. | new `runner_use_c_worker` cases |
| DT-55.e | Retained; the contrasts keep asserting the same process evidence. | same |
| DT-55.f | Retained as the mechanism R1 replaces. | none |
| DT-55.g | Account correction with R1: the `exec_stream` limits row's `behavior` and `checks` name the live cases and what each asserts. | `docs/limits.json` |
| DT-55.q | Retained qualification. | none |
| DT-56.b | Retained as the adjacent control; its text is unchanged. | new case |
| DT-56.c, .d, .q | Retained. | none |

Accepted limit, stated beside the field: "Retained bytes that are not
valid UTF-8 are shown as U+FFFD and reported as inexact; the reply does
not carry the original bytes." Lossless bytes beside or in place of the
string, and retention with a stated limit, are not selected.

**Discriminating check.** Six live contrasts beside the existing
truncation case, each comparing the reply with the direct bytes of the
same argument array and asserting content and indications separately:
embedded NUL without overflow; embedded NUL before overflow; split UTF-8
(present, no U+FFFD, exact); the aligned control; 17 bytes of 0xFF
(inexact without truncation); exactly 1,023 bytes (no marker, not
truncated). Constructed reader controls reject retained above received,
`truncated` disagreeing with the counts, retained above 1,023, and text
presence disagreeing with a zero or nonzero retained count. The contrasts
run first against the current app, where they fail by construction. The
order-barrier control is not triggered.

**Consequence accepted.** A consumer reads truncation from the stream
observation's counts, not from marker text; a missing key now means no
byte was retained; `stdout` can contain U+0000 and U+FFFD where it
previously stopped or was absent. A helper that must report bytes outside
UTF-8 encodes them as text itself. Developers: a layout, schema and
worker-identity change with one signed rebuild.

**Record.**
`records/trace-assessments/C2-failure-contract-producer-reader.md`,
Subject C.

### DT-59–61/133 — self-transfer visit timing, raw setup association, decoder prerequisites, scheduler authority gate

**Established.** All fifteen claims hold by source reading. The authority
investigation's executions (the same-visit self-consume run, the
constructed decoder buffers, the reader edits) are no longer available;
DT-61.c was re-made now with the current Python readers on a retained
reply body, and the three seam frames behind DT-133.b are retained and
were re-read. The private header word and the public record are kept
apart. DT-59: admission walks actions in order with no different-visit
requirement, and the worker services a self-transfer inside its own wait;
both registered placements put the self-consume in a later visit, so
same-visit consumption has no registered execution. DT-60: the decoder
records `setup_association_mismatch` and still projects the decision
under the session's own index and flag. DT-60.c gains a fact: the Rust
controller and the Python consumer already reject `ready` or
`not_required` beside integrity errors, as the scheduler, classifier and
Swift reporting do. DT-61/133: the decoder checks `ready` against
`required` only; no reader checks that `ready` rests on its cells; the
scheduler's gate also consults a header status word that is not a reply
field.

**Remaining defect, limit or uncertainty.** EXTENSIONS says "only in a
later visit", which is false for a self-transfer. The equipment rule says
the association is validated "before projecting". A mismatched
association, and a `ready` decision without its cells, are unreachable
with the shipped host and worker; they need a constructed reply or a
substituted worker. From `ready`, `setup_status: applied` and a missing
prerequisite cell a reader cannot tell a lost cell from an activation on
a different fact.

**Treatment.** No product behavior changes.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-59.a | Account correction in the shared-region owner; the guide's copy stays frozen. It is the same edit as DT-39.a. Refusing a same-phase self-consume at admission is not selected. | `docs/EXTENSIONS.md` |
| DT-59.b, .c | Coverage repair: a one-actor, one-phase composition (issue, transfer to self, consume, `read_fresh`, release) is registered. | `witness_contract/actor_compositions` |
| DT-59.q | No change. | none |
| DT-60.a, .b | Account correction: the decoder compares the raw association with the session's and records `setup_association_mismatch`; "the decision and its primary operation are still projected, under the session's own actor index and required flag"; a scope carrying integrity errors supports no readiness. Withholding the decision at the decoder is not selected. | `34-equipment.surface.md`; constructed mismatch controls in `ActorAuthorityTests.swift` |
| DT-60.c, .d | No change. | none |
| DT-61.a, .d | No change. | none |
| DT-61.b | Reasoned retention with the limit after the `decision` condition: "The worker publishes ready only after its core-limit, descriptor, size, mapping, close and header-binding cells succeeded. The host decoder checks the decision against `required` and does not re-check those cells." | `34-equipment.surface.md` |
| DT-61.c, DT-133.c | Assertion repair in the independent consumer: `ready` requires `required`, no primary operation and its seven successful cells; `not_required` requires `required` false; a `ready` worker scope requires that actor's host region scope `ready`; an applied or declared-unapplied actor with a required scope has an observed `ready` scope without integrity errors. Rust and Swift are unchanged. | `tests/lib/actor_evidence.py`; Python-only rows in `blackbox_e2e` extension controls |
| DT-133.a | Reasoned retention with the limit in the same place: the scheduler also requires the worker's private header status word; "That word is not a reply field"; "The controller relates an actor's application to a terminal scope only and does not re-derive ready from its cells." | `34-equipment.surface.md` |
| DT-133.b | No change; after the consumer rule those frames are rejected by the consumer and still `valid` for Rust. | none |

The two passes propose different text for the EXTENSIONS sentence. The
DT-59 wording is used because it keeps the query-collection and release
condition on both cases and says where a self-transfer is accepted: "A
recipient other than the sender accepts a delivery while parked between
its visits and consumes it in a later visit of its own. A self-transfer
is accepted inside the sender's own wait and can be consumed later in
that same visit. Either way consumption follows that phase's query
collection and the host's release."

**Discriminating check.** The new composition asserts `finished`, the
transfer `delivered` with source equal to recipient, the consume
`returned` in the same phase as the transfer, and no finding from the
consumer or the oracle; it runs against the current app. The constructed
decoder controls require `setup_association_mismatch` for a differing raw
actor and a differing raw required flag. The consumer rule rejects the
four constructed bodies and none of the listed fixtures and captures; it
is also run over the Swift-built reader-corpus frames before landing.

**Consequence accepted.** A user orders actions, not visits, to keep a
sender from consuming its own delivery; reads no readiness from a scope
that carries integrity errors; and does not take the controller's `valid`
as a check of `ready` against its cells. Developers: the controller and
the independent consumer differ on four constructed shapes.

**Record.** `records/trace-assessments/E-custody-setup-trigger.md`,
Subject 3.

### DT-62/65/122/123 — host custody acceptance, publication gating, delivery relationships, discarded worker custody observation

**Established.** All seventeen claims hold. Host and worker observers are
separate. Retained public captures at `8b5de2b2` under
`.tmp/contract-trio/observation-time/` were re-read: with the issue slot
unpublished the token is `unresolved`, and the host custody scope is
identical to the scope of a run whose token is `issued` (E1b against
E1a), so no public field distinguishes "the host accepted custody" from
"no publication reached the host"; delivery observations survive an
unpublished source slot (E2). The internal driver output that printed an
accepted custody beside the unresolved token is not retained; source
agrees with it. DT-65.b is reproduced now with the current Python readers
on a constructed body: a token edited to `issued_uncustodied` beside a
delivered transfer with held custody is accepted. The worker's own view
of the host's answer is decoded and read by no production code. The
six cross-anchor claims of the observation-time account and the two
investigation-identity sections (XA.1–6, ID.1–2) are placed here and are
accurate.

**Remaining defect, limit or uncertainty.** The custody rule says the
native return and host custody acceptance "are reported independently";
the reply reports acceptance only through the token status of a published
non-null issue and through transfer records. Accepted custody beside an
unpublished issue slot needs the worker to end between the host's
acknowledgement and its own completion store. No end-to-end worker
custody timeout or clock fault has been executed, so `issued_uncustodied`
with shipped components is unobserved. No product reader compares token
custody with transfer custody.

**Treatment.** No product behavior changes. A public carrier for accepted
host custody under an unpublished issue slot, publication of the worker's
view, and mirrored reader rules in Swift and Rust are not selected.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-62.a, DT-122.b | Account correction withdrawing "reported independently": the host records acceptance separately; the reply reports it through the token status of a published non-null issue and through the transfer records that used the custody; "While the issue result is unpublished the token is `unresolved` or `not_reached` and the reply reports no acceptance observation, whether or not the host accepted the published bytes." The failure contract gains "Custody acceptance has no field of its own". | `14-extensions.surface.md` `extensions.custody.issue`; `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| DT-62.b, .c; DT-122.a, .c | No change. | none |
| DT-62.d, DT-129.d | Assertion repair: the unit case asserts the host's `accepted` custody observation and a nil `token_length`, pinning "host accepted, reply unresolved". | `ActorReplyTests.swift`; `runner_unit/pwrunner_core_unit_executable` |
| DT-65.b, .c | Assertion repair in the independent consumer: a transfer row with `custody_status: held` requires its token to be `issued` or `unresolved`. Limit stated with the custody paragraph: "The host and controller checks relate a token's status to its issue event and a delivered transfer to its own fields; they do not compare the two." | `tests/lib/extension_evidence.py`; Python-only rows in `blackbox_e2e` extension controls; `14-extensions.surface.md` |
| DT-65.a, .q | No change. | none |
| DT-122.d | Reasoned retention with the limit at `delivered_length`: "The issuing worker wrote this length to its outbound slot and `token_length` to its evidence slot; their equality checks one writer's consistency." | `14-extensions.surface.md` |
| DT-122.e | Account correction of the support text: token acceptance is carried by the token resource's status. | `14-extensions.surface.md` |
| DT-123.a–c | Reasoned retention; limit in the custody paragraph: "The issuing worker's own record of the host's answer is not a reply field." The unread name table is removed only with the host thread. | `14-extensions.surface.md` |
| DT-123.q | Evidence limit carried. | none |
| XA.1–6, ID.1–2 | Accurate; covered by the limits in this row and in DT-46/120/121/129. | none |

Outside the review, the shared block of the failure contract says the
host "rejected, timed out on or never saw the publication"; the host has
no timeout branch, and "timed out on" is removed in the owner while the
guide's copy stays frozen. The custody paragraph is also edited for
DT-64 under DT-63/64/124/125/128; the edits touch different sentences of
one rule.

**Discriminating check.** The consumer control rejects
`issued_uncustodied` beside a held delivered transfer and accepts the
unchanged body. The unit case fails if assembly reports `issued`, a
length or a native result for an unpublished issue slot, or if the host
did not accept. For the withdrawn sentence further evidence would not
change the decision: the two captures already show the cases are
indistinguishable, and the decision turns on consequence, not
reachability.

**Consequence accepted.** A user does not read `unresolved` as "the host
never held this token", reads no cause into `issued_uncustodied`, does
not treat equal `token_length` and `delivered_length` as two
measurements, and does not take a clean controller result as agreement
between token custody and transfer custody. Developers: the consumer
checks one relation the controller does not.

**Record.** `records/trace-assessments/E-custody-setup-trigger.md`,
Subject 4, "Entries that span subjects" and "Outside the review".

### DT-63/64/124/125/128 — host last use and final teardown, native allocation prefix, worker observers, terminal byte extent

**Established.** Nothing stops holding at `837296af`; product source
differs from the reviewed revisions only in regenerated identity bytes.
The authority pass's captures (`/private/tmp/pw-authority-trace-3QC3qQ/`)
are absent; the observation-time captures under
`.tmp/contract-trio/observation-time/` (build `8b5de2b2`) are retained
locally and were re-read; three retained default batteries at `2f4d76e4`
supply local observations. The ten scope statements of the two
investigations (S-1–10) are placed here and hold. Call counts, flags,
scanned bytes and time are kept as four separate observations. Host: the
last-transfer `defer` and `finish()` both set the custody flag, and the
test at `ActorAuthorityTests.swift:467-468` reads it after teardown under
a comment that credits last-transfer clearing. The retained internal
driver run (E6) recorded private custody nonzero before the last transfer
and zero before teardown, and nonzero until teardown when that transfer
never ran; it is not a registered result. Worker: the native return is
cleared through its inspected length (at most 16,384 bytes) and freed.
Corrections to the review: DT-125.e is incomplete, since the terminal
fixture also asserts the full inbound buffer is zero at the release call
in `explicit_release`, a byte-state observation between the last consume
and the exit sweep (synthetic; sensitivity source-read); for DT-64.c the
checker never asserts the issuer-erase word for the oversized and maximum
fixture returns, although the retained output shows it true.

**Remaining defect, limit or uncertainty.** No public reply field reports
either last-use clearing, and host last-use clearing has no registered
check; worker last-consume clearing has synthetic guards only. The issue
rule promises erasure of "the native allocation", which is false for a
return longer than the inspected bound; such a return has been produced
only by a replaced issuer, and every observed real token is 208 to 226
bytes. Whether the native issuer can return more than 16,383 bytes is
unknown. Neither last-use erase has been removed in an executed mutation.
Outside the review: the limits manifest says larger native results report
`token_oversized`, and nothing emits that string.

**Treatment.** No product behavior changes. A pre-teardown host observer,
a public last-use cell, an executed worker last-use mutation and clearing
of the whole native return are considered and not selected.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| S-1–10 | Retained as the inspected revisions, availability and limits. | none |
| DT-63.a, DT-124.g (`:467`) | Coverage repair: the comment says custody reads erased after the run and that teardown sets the flag whether or not the last declared transfer ran. The assertion stays as a final-state check. | `ActorAuthorityTests.swift` |
| DT-124.g (`:307`) | Retained unchanged; it carries no timing claim. | none |
| DT-63.b–e; DT-124.a, .c, .d, .f, .h, .i | Accurate; no change. E6 stays local evidence at `8b5de2b2`. | none |
| DT-124.b, X-1, X-3 | Reasoned retention with the limit under the erase rule: "The reply's `final_erase`, `shared_clear` and `terminal_owned_inbound_clear` cells record teardown and worker-exit clearing; last-use clearing has no reply field." | `14-extensions.surface.md` |
| DT-124.j | Reasoned retention with the limit in the custody support owner: "Host last-use custody clearing has no registered check; worker last-consume clearing is exercised by synthetic controls only." | `14-extensions.surface.md` |
| DT-64.a | Account correction narrowing the issue rule: "Erase the returned token through its inspected length and free the allocation, after copying a bounded token or on refusing an empty or longer one; bytes of a longer return beyond the inspected length are freed without being erased." | `14-extensions.surface.md` |
| DT-64.b | Accurate; retained as the stated limit of the narrowed rule. | none |
| DT-64.c | Assertion repair: assert the issuer-erase word for the oversized and maximum fixture returns. | `check_extension_boundaries.py`; `witness_contract/extension_boundaries` |
| DT-64.d | Accurate; the native issuer's maximum stays unknown. | none |
| DT-124.e, DT-125.f, X-4 | Accurate; no change. | none |
| DT-125.a–c | Accurate; the boundary observer is retained and credited for no more than it shows. | none |
| DT-125.d, .e | Retained with the correction above recorded; both sensitivities stay source-read. | none |
| DT-128.a, .b, .e, X-2 | Reasoned retention with the meaning stated: "`performed` records that the scope's clearing operation ran over its assigned storage; it does not state that token bytes were present."; `value` adds "or the bytes a clearing operation overwrote, which can be zero". | `34-equipment.surface.md` |
| DT-128.c, .d | Accurate; covered by the same sentences. | none |

The limits row for the extension token payload is corrected in its owner
so that it no longer names `token_oversized`; the guide's copy stays
frozen. The `ownership` definition is edited once for this row and for
DT-68/127.

**Discriminating check.** `witness_contract/extension_boundaries` with the
added assertion rejects a worker that frees an over-length return without
clearing its inspected length. For the retained limits further evidence
would not change the decision: no public statement credits a check or run
for host last-use clearing once the comment is narrowed. The smallest
host observer, should the decision be revisited, is specified in the
assessment.

**Consequence accepted.** A user cannot learn from a reply whether token
bytes were cleared at the declared last use, and does not read
`performed`, an erase `value` or `last_use_step_id` as saying so. Bytes
of a native return beyond 16,384 would be freed without being erased.
Developers: host last-use clearing can regress without a registered case
failing.

**Record.** `records/trace-assessments/D-erasure-handles-ownership.md`,
sections 0 and 1 and "Outside the review".

### DT-66/126 — equal raw handles and per-release access effects

**Established.** All fourteen claims hold. The two-consume run was
executed twice: the authority pass's capture is absent, and the rebuilt
run under `.tmp/contract-trio/observation-time/` (build `8b5de2b2`)
records the same pattern and was re-read. Both consumes returned the same
number and both releases returned 0; fresh reads were denied at baseline,
succeeded during and after the first release, and were denied after the
second. Both handle records still read `produced` with
`release_attempted: true`. The worker keeps per-reference bookkeeping
only and derives nothing from access. No reader or test requires a
post-release access result.

**Remaining defect, limit or uncertainty.** None in the statements: each
definition a reader needs is present and scoped. Not established: why
access survived the first release. A counting implementation in the
private library is a consistent explanation, not an observation; nothing
here establishes reference counting, universal revocation or the cause of
errno 1.

**Treatment.** Reasoned retention without edit for DT-66.a–g,
DT-126.a–e, X-5 and X-6. The accepted limit already stands beside the
technical claim in `docs/contract/14-extensions.surface.md`: "A release
return records that native call; subsequent access is established by the
corresponding access observation." Invalidating the table entry after a
release, or recording a per-release access probe, is not selected: the
worker cannot observe kernel state after a release.

**Discriminating check.** None added. The discriminating observation
exists as a schedule shape (`read_fresh` after each release), and
enforcing either access result would force a kernel answer.

**Consequence accepted.** A user who needs to know whether access remains
after a release schedules a `read_fresh` after it, and does not infer
revocation from a release result of 0, `release_attempted: true`,
`status: produced` or equal raw handles. Developers: none.

**Record.** `records/trace-assessments/D-erasure-handles-ownership.md`,
section 2.

### DT-67 — redelegation contrasts: assertion authority versus credited negative effects

**Established.** All five claims hold by source reading. The suite README
says each of four contrasts "must not be credited". The checker asserts
that for the two omitted-consume contrasts, where it follows from the
absence of the omitted event alone, and only records the computed credit
for the two weakened-policy contrasts. The principal case does not
require principal credit to pass. Three retained default batteries at
`2f4d76e4` record `credited: false` for both weakened-policy contrasts;
that value is recorded, not asserted, and the reports are development
output.

**Remaining defect, limit or uncertainty.** The suite account credits an
assertion two contrasts do not have. No native negative effect is
asserted for any contrast. The authored executed support names one
historical credited run that a suite pass cannot recover.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-67.a | Credited claim narrowed in the suite account: the omitted-consume contrasts must lack the omitted action's event, so their chain is incomplete and not credited; the weakened-policy contrasts publish all six links, and whether their chain is credited "is computed and recorded in `report.json` beside the principal run and is not asserted". The checker comment is aligned. | `tests/suites/witness_contract/README.md`; `check_extension_redelegation.py` |
| DT-67.b, .c | Accurate; no change. | none |
| DT-67.d | Accurate; the support entry stays scoped to its one inspected run. | none |
| DT-67.e | Accurate; no change. | none |

Asserting `not credited` for the weakened-policy contrasts is not
selected: the suite's rule is that kernel answers are recorded, not
forced, and a different OS answer would fail the case with no product
fault. Reporting those credits as advisory judgments is not among the
selected conversions.

**Discriminating check.** None added. Further evidence would not change
the decision: the retained reports agree with either treatment, and the
choice concerns authority, not the observed value.

**Consequence accepted.** Users: none. A developer reading a pass of
`witness_contract/extension_redelegation` reads `contrasts.*.credited`
and `principal.credited` in the case's `report.json`; the pass
establishes neither.

**Record.** `records/trace-assessments/D-erasure-handles-ownership.md`,
section 3.

### DT-68/127 — pre-exit worker resource publications beside host teardown observations

**Established.** All sixteen claims hold. The field combination (worker
scope `mapping: held` beside a reaped actor and host `mapping: released`)
is recorded in three retained public replies under
`.tmp/contract-trio/observation-time/` (build `8b5de2b2`) for a clean
exit, a SIGKILL before publication and a natural reap at the gate; the
authority pass's own capture is absent. Source fixes the time each value
describes: the host decodes each worker's published cells after that
worker is stopped and reaped; the worker publishes no unmap on the
ordinary path; host scopes record the host's own teardown calls. Readers
require a cleanup cell for `released` and use `held` in no decision.

**Remaining defect, limit or uncertainty.** One field, `ownership`,
carries host values (the outcome of the host's own last call) and worker
values (the last state the worker published before exit) with no time
anchor in its definition. Nothing here establishes the state of any
mapping after a worker's exit; this is a temporal ambiguity, not a leak
claim.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-68.a, DT-127.e, .h, X-7, X-8 | Reasoned retention with the time anchor stated in the definition: "Each value records the last operation published for that resource in its scope, not an inventory at reply time. Host region and custody values come from the host's own setup and teardown calls. A worker scope's values come from cells that worker published before it exited, so worker `mapping: held` records a successful setup mapping with no published unmap, including for a worker the same reply reports reaped." | `34-equipment.surface.md` `ownership` |
| DT-68.b–d; DT-127.a–d, .f, .g, .i, .j | Accurate; no change. | none |

Rewriting worker `mapping` to `released` at reap, or adding a distinct
worker value, is not selected: the host observed an exit, not an unmap.
The definition is edited once for this row and for the `performed`
sentence of DT-63/64/124/125/128.

**Discriminating check.** None needed; no behavior changes. Both
independent readers already refuse `released` without a succeeded
cleanup cell.

**Consequence accepted.** A user does not read a worker scope's
`mapping: held` as a mapping that exists after the run, and joins it with
that actor's `subprocess.reaped` and `owned_reap`. Developers: none.

**Record.** `records/trace-assessments/D-erasure-handles-ownership.md`,
section 4.

### DT-69–73/75–80 — reconcile recovery, classification, candidate discovery and credited coverage

**Established.** Every product-behavior claim holds by source reading at
`837296af`; the cited files are byte-identical to the reviewed snapshots.
The review's executed evidence is gone: the constructed-control driver
and outputs, the retained run `plain-help-byoxpc-b16f32d0` and the build
1482 binary. Nothing was replayed; `runner list` and `runner reconcile`
were run once on the `2f4d76e4` app for orientation, against an empty
default registry. The ten unnumbered convention and coverage claims
(RC.a–e, RL.a–e) are placed here and stand as a record of how the
observations were made. `cmd_runner_reconcile` calls no function that
writes, locks, boots out or unlinks. One clause of the review is
mistaken: DT-79.a says none of the six cited checks calls `load_registry`
on an absent path, but four do and one asserts empty `runners` from it;
the reconcile and inaccessible-path gaps hold.

**Remaining defect, limit or uncertainty.** The limits manifest says a
later `runner reconcile` continues recovery; reconcile is report-only by
standing rule. The architecture manifest misstates the reconcile node and
two edges and credits `runner_install`, which asserts only exit 0 and
`ok` on an absent registry. The subtree support is graded check-read
while no cited check exercises reconcile. Several consequences of stated
rules are unstated: what `ambiguous` and `unregistered` cover, the
location-error placeholders, the inspection-error constant, two
plist-ownership branches. Unexamined: launchd's handling of two plists
with one label; a loaded service with neither record nor plist; native
`launchctl` output without exactly one `program` line. The frozen guide
says list and reconcile "confirm retirement and service/plist absence";
no technical owner makes that claim.

**Treatment.** No product behavior changes for this row; reconcile stays
report-only (R2). Reporting each scanned plist exactly once, typing the
location error and copying observed presence into inspection errors are
not selected.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| RC.a–e, RL.a–e | Reasoned retention as the evidence record; no executed output can be reused. | none |
| DT-69.a | Account correction: the limits row's `effect` loses "or `runner reconcile`"; it cites the removal-recovery unit test and says a repeated removal retires a retained record once absence is observed. Same edit as DT-34.c. The guide's copy stays frozen. | `docs/limits.json` `runner_remove_teardown_wait` |
| DT-69.b | Behavior retained; the new integration control asserts it. | `controller/integration/cli_contract.rs` |
| DT-69.c–f | No change. | none |
| DT-70.a | Reasoned retention with the limit at the ownership fields: "`ambiguous` is assigned to an absent service and to a listed service without exactly one `program` line; read it with `service.presence`." | `50-installation.surface.md` |
| DT-70.b | Reasoned retention; same field: "Reconcile reports no retirement decision; `runner remove` decides retirement from its own observations." | same |
| DT-70.c | Credited claim scoped: the qualification joins the classify owner's limits. | same |
| DT-70.d, 71.e, 72.e, 73.d, 75.g, 77.f, 78.e | No change; history. | none |
| DT-71.a | Reasoned retention with the limit in the candidate paragraph: reconcile "does not enumerate launchd services, so a report with no row for a service is not an observation that the service is absent." The guide is not edited. | same |
| DT-71.b–d | No change. | none |
| DT-72.a–c | Account correction, behavior retained: suppression compares the parsed Label and the scanned directory's scope only; a plist at a recorded path whose Label cannot be read or differs is reported in its record row and again as a candidate; "`unregistered` means that no record in that scope has the candidate's parsed Label." | same |
| DT-72.d | Recorded in the reconcile owner's limits: no assertion reads `candidates` for an overlapping path. | same |
| DT-73.a, .b | Reasoned retention with the limit: "Another plist file that carries a registered Label in the same scope is reported in neither place, and on a location error the plist at the recorded path is not inspected." | same |
| DT-73.c | Retained as an open qualification. | none |
| DT-75.a, .c | Reasoned retention with the limit: the placeholders mean "the resource was not inspected", and the row's `error` text is the only field that separates a recorded identity that disagrees from a location that could not be determined. | same |
| DT-75.b, .d–f | No change. | none |
| DT-76.a, .b | Account correction of the two unstated ownership branches (same edit as DT-34.b); the candidate `ownership` field adds "Assigned without reference to any record." | same |
| DT-76.c–e | No change here; the `XPC_SERVICE_PATH` consequence is disposed of under DT-33–35 (R7). | DT-33–35 |
| DT-77.a | Reasoned retention with the limit: the inspection-error `presence` is "The constant `unknown`, marking a failed inspection. It is not the file's observed presence". | same |
| DT-77.b, .d | Limit stated: an inspection error is recorded for every `.plist` entry in the scanned directories whether or not it is a candidate; a property list that cannot be represented as JSON is one such failure. | same |
| DT-77.c, .e | No change. | none |
| DT-78.a–c | Account correction of the node text and both edge labels. | `docs/architecture.json` |
| DT-78.d | Credited check replaced: the three entries cite `runner_byoxpc/registry_recovery` and the new integration control in place of `runner_install`. | same |
| DT-79.a | Credited claim scoped: the subtree owner's limits say its cited controls exercise neither reconcile, record location, service or plist inspection nor a registry load refusal. The review's absent-path clause is recorded as mistaken. | `50-installation.surface.md` |
| DT-79.b | The two classifier unit tests are cited on their owners with constructed-input limits. | same |
| DT-79.c, .d | A reconcile owner graded check-read states that its assertions are opt-in and that no-change comparisons are joint. | same |
| DT-79.e | Assertion added: reconcile on an absent registry path creates no registry, lock or directory. | `integration/cli.integration` |
| DT-79.f | No change. | none |
| DT-80.a | Account correction: one row for each recorded runner and for the nested runner of each retained cleanup entry; a cleanup entry's start time and observations are not repeated; `runner list` returns them. | same |
| DT-80.b–d | Limits stated: a service with neither the label prefix nor the `PWRunner` executable name is not recognizable without its record; the registry is read once without the lock, so a report is not a snapshot taken at one time; reconcile waits without a time bound for each child. No LIMITS row is added. | same |

The passes propose different wording for two shared edits. For the
limits row the DT-69 form (remove the clause) is used over the DT-34.c
form (which adds "`runner reconcile` reports the retained record"),
because it corrects the shared region without adding a statement. For
the ownership branches the DT-34.b sentence is used; the two texts state
the same branches.

**Discriminating check.** New control in `integration/cli.integration`
with `HOME` and the registry redirected into a canonicalized scratch
path: reconcile on an absent path leaves path, lock and parent absent;
reconcile on a constructed registry with one installed and one
pending-cleanup record exits 0, reports both recorded states and leaves
registry bytes and directory listing identical with no lock. It runs
against the current app and is expected to pass. A classifier unit
control (non-regular object `unowned`, unconvertible file `unknown`,
absent `ambiguous`, differing `XPC_SERVICE_PATH` `unowned`, two
`program` lines `ambiguous`) is a `controller/src` edit and lands with
the R2 rebuild. For the retained limits no further evidence would change
the decision; each follows from the absence of any launchd enumeration
or write in the reconcile path.

**Consequence accepted.** A user repeats `runner remove`, not `runner
reconcile`, to finish a retained cleanup; does not take a report with no
row for a service as absence; compares a candidate's `plist_path` with
recorded paths before treating it as unregistered; and keeps the registry
record for a service whose bundle identifier or executable name does not
follow the defaults. The limits row and the guide's frozen copy differ.

**Record.** `records/trace-assessments/F-reconcile.md`, Subject 1.

### DT-74 — absent registry versus failed inspection

**Established.** All nine claims hold by source reading. `load_registry`
returns the empty registry whenever `path.exists()` is false, which
includes an inaccessible ancestor, an ancestor that is a regular file, a
symlink loop and a symlink whose target is missing; only an existing
file that cannot be read reaches the failing read. The review's four
registry-path variants were executed on build 1482 and their output is
gone. An errno probe made now on this machine establishes which system
errors each path state produces. One sentence of the review cannot be
true as written: a symlink to a missing file has no registry of seven
runners behind it; the classification does not depend on it. The scope
is wider than the review states and is read from source: `runner
install`, `remove` and `validate` take the lock first and refuse on an
inaccessible ancestor, while `runner list`, `status`, `verify`,
`reconcile` and an external-runner `run` read the uninspectable path as
empty. With a registry symlink whose target is missing, install and
validate replace the link.

**Remaining defect, limit or uncertainty.** A registry that cannot be
inspected is reported as empty, so reconcile presents installations the
registry still owns as `unregistered` candidates with no signal, against
the stated condition "The registry is readable with schema_version 1, or
its path is absent" and the standing rule that unknown inspection is not
absence. No test asserts the unreadable-file, unparseable, unsupported
schema or inaccessible-ancestor outcomes. Every caller row except
reconcile is read, not executed. A restrictive automation sandbox that
denies the metadata read was not probed.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-74.a, .b, .f | Behavior change (R2): `load_registry` returns the empty registry only when inspecting the path finds no entry; any other inspection failure refuses, naming the path and the system error. Runner commands then exit 2 with one stderr line and empty stdout; an external-runner `run` keeps `tool_error` with that text. The registry condition, its retained note, the refusal sentence and the README state the three outcomes. | `controller/src/runner_manager.rs`; `50-installation.surface.md`; `controller/README.md` |
| DT-74.c | Behavior change (R2): a registry symlink whose target is missing refuses. Keeping it as absent is not selected. | same |
| DT-74.d | Retained and asserted. | integration control |
| DT-74.e | Classification retained; the refusal keeps the stderr-only, exit 2 form stated under DT-33–35. | DT-33–35 |
| DT-74.f (quoted sentence) | Recorded as imprecise; no action. | none |
| DT-74.g | Retained; the caller table in the assessment closes the reading. | integration control |
| DT-74.h, .i | No change. | none |

Reporting the failure inside the reconcile envelope, a single read that
matches only "not found", and retention with a stated limit are not
selected.

**Discriminating check.** Unit controls on `load_registry`: empty for a
path with no entry and for a path under an absent directory; an
inspection error for a registry under a mode-000 directory; the read
error for a mode-000 file; refusal of a symlink to a missing target, of a
path whose parent is a regular file, of a directory at the path, of
unparseable JSON and of an unsupported schema. A selection control: with
the registry under a mode-000 directory and an external selector, the
error is not "external runner not found in registry". An integration
control on the signed app with the registry redirected: for an
inaccessible ancestor and for an unreadable file, `runner list`,
`reconcile` and `status` exit 2 with empty stdout and a stderr line
naming the path, and the two prefixes differ; an external-runner `run`
returns `tool_error` with the inspection text. The controls run first
against the current source and app, where the inaccessible-ancestor,
not-a-directory, symlink and `run` rows fail. After the rebuild the
`runner_byoxpc` opt-ins (`registry_recovery`, `runner_install`,
`default_location`) run in a logged-in GUI session with owned resources
verified absent afterwards.

**Consequence accepted.** `runner list` and `runner reconcile` on a path
that cannot be inspected exit 2 with empty stdout where they exited 0
with an empty report; `status` and `verify` stop returning a `not_found`
envelope there; install and validate stop replacing a registry symlink
whose target is missing, so such a target is created by hand. In a
restrictive automation sandbox that denies the metadata read, cases that
call `runner list` fail with the inspection diagnostic and are rerun
outside it.

**Record.** `records/trace-assessments/F-reconcile.md`, Subject 2.

### DT-88–94 — source inventory, traversal refusal, selected suffixes and roots, framing, metadata and support

**Established.** Nothing in these entries is mistaken; fifty-three claims
are assessed, including DT-08's executed counterpart and the
investigation's conventions and limits (Conv.a–d, Lim.a–d). The review's
disposable-clone drivers and outputs are absent. The non-Git controls
were re-executed now at `837296af` on constructed copies and literal
trees with the pinned interpreter; none is a build or a registered case.
The checkout derives 119 paths and
`development:b55acb20…719e`, which equals the signed app's
`build.contract`. DT-89 reproduces: a directory under a selected root
that cannot be listed is omitted with exit 0 and no diagnostic, and two
trees that differ in a selected file under it print one identity. The
mechanism is now read in the pinned standard library, which discards the
listing error. Three items are stale or narrower than HEAD: the review's
baseline of 118 paths is 119 since `bba8bca3` added
`docs/publication.py`; that file is a third code-only input the
statement omits, so DT-91's history is incomplete; DT-93's "two
derivations" are four sample points. DT-89 is wider than stated: a
searchable but unlistable directory (mode 0111) is also omitted while
its files still open by name, so DT-89.e's remark that the compiler
could not read such files holds only for mode 0000. The shared walker
also serves the worker identity, where an unlistable directory produces
a "stale" refusal whose named regeneration would record the incomplete
tree. Unicode normalization is now exercised: names are hashed as the
volume returns them.

**Remaining defect, limit or uncertainty.** Different selected bytes can
share an identity (DT-89). The inputs statement omits two selected
inputs, does not say that Git state does not enter selection, names no
sort order and lists an incomplete refusal set. No check compares the
statement with the declarations, asserts the framing, or supplies an
inventory oracle independent of the code under test; one test names a
file that never existed and silently substitutes another. Not executed:
a full build with an unlistable source directory, and a complete
compiler-closure audit. The pre-sign guard compares point samples.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| DT-08.a; DT-91.a | Account correction: the inputs statement names seven roots and twenty files in full. One edit serves DT-08 and DT-91. | `docs/contract/00-identity.surface.md` `identity.public.inputs` |
| DT-08.b, .c; DT-91.b–d | No change; the recurrence is the reason for the statement-as-oracle check. | none |
| Conv.a–d | No owner change; HEAD values are used in the working record. | none |
| DT-88.a, .b | Behavior retained; the statement says "Git tracking and ignore rules do not enter it: an untracked, ignored or hidden file with a listed suffix under a listed root is included." | same surface |
| DT-88.c | Account correction: the identity names files "present in a source tree when it is derived; it does not identify a commit". | same surface, `forms` |
| DT-88.d; DT-91.e; DT-93.a, .b, .d, .j | Coverage repair: the statement becomes the oracle for the real declarations, and a literal tree supplies an inventory and a pinned digest the code does not. The support owner is revised to pin only what the checks assert. | `source_drift/build_contracts`; same surface |
| DT-88.e | No change. | none |
| DT-89.a | Behavior change (R3): the walker refuses a directory it cannot list and an entry it cannot inspect under a selected root, including an empty one, naming the path. The identity of the unchanged tree changes, as does the worker identity. The refusal joins the build manifest. | `docs/source_identity.py`; `docs/build.json`; `source_drift/build_contracts`, `preflight/build_entry_controls` |
| DT-89.b | Retained; an unreadable selected file already refuses. The refusal list names it and a control asserts it. | same |
| DT-89.c; DT-90.b | No change; Git is a second observer with its own blind spots. | none |
| DT-89.d | Closed by reading; R3 moves the error handling into repository code. | none |
| DT-89.e | Retained as an unexecuted limit: a packaged build with a searchable, unlistable source directory was not run. | this plan |
| DT-90.a | Behavior retained; the statement says a symlink or special file is refused "whatever its name". | same surface |
| DT-90.c | No change. | existing check |
| DT-90.d | Account correction: the refusal list adds a root holding no selected file and a selected file that cannot be read; the diagnostic "missing protocol sources" is renamed in the R3 edit. | same surface; `docs/source_identity.py` |
| DT-90.e; DT-92.f; DT-93.e | Coverage repair: each listed refusal and the framing are asserted on the literal tree. | `source_drift/build_contracts` |
| DT-92.a, .b, .e | No behavior change; framing and relocation assertions added. "File modes, timestamps and extended attributes do not enter it." | same |
| DT-92.c | Account correction: paths are taken "in ascending Unicode code-point order, which is also the byte order of the UTF-8 paths". | same surface |
| DT-92.d | Reasoned retention with the limit: "path names are hashed as the file system returns them, without Unicode normalization." | same surface |
| DT-93.c | Assertion repair: the byte-sensitivity loop names `runner/augments/exec_baseline.sb`, asserts each named path exists and drops the fallback. | `source_drift/build_contracts` |
| DT-93.f, .h | No change. | none |
| DT-93.g | Account correction, mechanism retained: "A change made and reverted between the two derivations is not detected." | same surface, `derive` |
| DT-93.i; DT-94.e | Reasoned retention with the limit in the new support owner: "No check compares the selection with compiler dependency records." REQUEST's shipped-source sentence stays; the complete compiler closure is unknown. | same surface |
| DT-94.a–c | Reasoned retention: the selection "is not derived from what the compilers read, and it includes test-only code and files that no build step consumes." | same surface |
| DT-94.d, .f | No change; no erratum for a released document. | none |
| Lim.a–d | Retained as limits; case-only collisions, the release form, the Swift entry and a build in a changed state remain unexercised. | none |

The DT-05–08 pass proposed adding the two missing names; this row's text
subsumes it and spells every path in full so that the oracle test needs
no interpretation. The refusal sentence is true only once R3 lands, so
the statement and the walker land together. Deriving the lists from the
generator's declarations, a compiler-closure check of the public
identity, hashing a marker for an unlistable directory and taking the
inventory from Git are not selected.

**Discriminating check.** On a literal tree: the readable inventory
equals a literal list; with a subdirectory at mode 0000, at mode 0111,
unsearchable, an unlistable root and an added empty unlistable directory,
derivation raises naming the path and never prints the digest of the
tree without that directory; the generator's digest equals a pinned
literal value, which also fixes prefix, length encoding and order. A
build-entry control places an unlistable directory under a root only the
public identity walks and requires exit 1 before the build stamp, with a
second variant for the worker roots. The statement-oracle test fails at
HEAD naming `controller/interface` and `docs/publication.py`. All run
first against the unchanged walker, where the unlistable rows return the
subset inventory. Each control confirms its own precondition and fails,
not passes, when run as uid 0.

**Consequence accepted.** Every development identity changes when R3
lands: the current app no longer matches the tree until a signed
rebuild, saved specimens asserting the earlier identity are reviewed and
reasserted, and external runners installed from the earlier app are
reinstalled. A directory under a selected root that the building user
cannot list stops the build with a message naming it. A user does not
read a development identity as a commit identifier.

**Record.** `records/trace-assessments/H-development-identity.md`.

### DT-95–104/134 — receipt host binding, application/completion/publication guards, constant labels, input coverage, capture view

**Established.** Eighty-five claims are assessed; every source claim was
re-read at `837296af`, where the receipt source differs from the
review's snapshot only in generated identity lines. The review's live
probes on the `8b5de2b2` app and its registered run are absent. The
retained development run `20261118T011154Z_5cfcec0a` at `2f4d76e4`
re-shows three captured receipts whose length, digest, source digest,
parameter digest, nonce and PID agree with request and reply, and the
kill-after-application receipt
`{reason: worker_not_complete, status: unavailable, worker_pid}`; the
Rust and Swift receipt tests pass there. Three in-memory digest
computations reproduce the review's values. By source: the host decoder
applies nine ordered conditions to the raw worker record; the
controller, the Python consumer and Swift reporting each apply one
predicate (status vocabulary and two labels); the two labels are
literals the host writes on its one success path; the nonce enters no
compile call and no digest; the receipt has no member for a file; the
worker reads the compiled object through a private four-member view.
Corrections to the review: DT-100.e holds for the ordinary form only,
since `witness_contract/actor_compositions` requests capture on a
failing actor policy and asserts a truthy reason; DT-104.b's
cross-reference is to DT-32's third bullet, not DT-37, and the producer
emits the diagnostics key as JSON null; DT-104.c's executed credit names
a run at `5e51300d`, after which `run_flow.rs` changed how the refusal
is typed and the result selected, so that execution did not exercise the
current path. The acceptance and overhaul plans' premise about the
capture rehearsal is corrected: after a returned apply failure the
worker publishes done and exits 0, so the completion guard already holds
on that path and the application guard alone withholds the copy.

**Remaining defect, limit or uncertainty.** A recipient cannot tell a
correct receipt from a detached one without the request: the Rust label
test admits a `captured` row whose nonce, source and parameter fields do
not correspond to its request, and constructed seam frames with another
PID, a replaced nonce, a flipped byte and a zero length are `finished`
and `valid`. Six of nine failure reasons are named in no test, and the
first-failure order is source-supported only. No observation exists of
`sandbox_apply` returning failure for a real specimen, so the receipt
outcome on that path is source-read. Not established: that the bytes
come from the compiler's object beyond the private layout reading, how
they relate to what application submitted, or any kernel state. Nonce
reuse was never executed.

**Treatment.** No product behavior changes. Capture despite failed
application, a controller comparison of receipt fields against the
request, a split of `worker_capture_refused` and any new observer of the
compiled object are considered and not selected.

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| RC.a–d; DT-95.b, .c, .e, .f, .h, .i, AT.a, AT.c, AT.d; DT-96.c, .e, .f; DT-97.a; DT-98.c; DT-99.e; DT-101.a, .c, .e, .f, .i; DT-134.b; CL.a1–a5, CL.c5, CL.c7, CL.d | Accurate observations; no change. | none |
| DT-95.a, .g, AT.b, AT.e, AT.f; DT-104.d; DT-134.a, .c; CL.c6 | Reasoned retention of status-and-label admission. Limit in the labels rule: "The controller compares no receipt field with the request it delivered, with the reply's worker record or with the receipt's own bytes, and evaluates neither extent condition. A `finished` result beside a `captured` receipt reports the host's capture checks, not a controller comparison." | `35-profile.surface.md`; `unit/rust.unit` |
| DT-95.d; DT-104.a, .b | Assertion repair and credited claim narrowed; enforcement retained. The Rust test asserts which boundary refused each row and the diagnostics key's actual form, and names the admitted disagreeing row; its owner and the unit README say eight of seventeen refused rows are refused by the test's typed reader and that the admitted captured row is unrelated to the request. | `controller/src/run_flow.rs` (controller thread); `35-profile.surface.md`; `tests/suites/unit/README.md` |
| DT-104.c | Account correction: the executed credit is refreshed from the `unit/rust.unit` run at the commit carrying the corrected test, or the owner is graded check-read until then. | `35-profile.surface.md` |
| DT-96.a, .b, .d | Account correction: `producer` and `capture_stage` name the component and program position; "The host writes this value on every captured receipt"; neither is a recorded observation. | same |
| DT-97.b, .c, .d; CL.c4 | Account correction, behavior retained: "The nonce enters no compiled byte and no digest; the comparison associates the receipt with the reply that carries it."; the request side says the host checks the nonce's form only and keeps no record of earlier nonces. | `35-profile.surface.md`; `11-policy.surface.md` |
| DT-98.a, .b | Reasoned retention with the limit in "Captured input identity"; see the shared sentence below. | `35-profile.surface.md` |
| DT-99.a–d | Account correction, vocabulary retained: `worker_capture_refused` covers every worker capture status other than captured, and the receipt does not say which. | same |
| DT-100.a–d | Reasoned retention of both guards. Limit in Status: "The host evaluates application and worker completion before it reads any capture record. An `unavailable` receipt therefore does not report whether the worker copied the object, and a completed copy is withheld when application was not observed to succeed or the worker did not complete cleanly." | same |
| DT-97.e; DT-99.f; DT-100.e; DT-101.b, .d, .g, .h, .j; DT-102.a–c; CL.c1–c3 | Assertion and coverage repair: each corruption asserts its reason and the exact `unavailable` key set; adjacent two-fault cases pin the order; one known-answer parameter digest is asserted in C and Swift; live rows add an ordinary compile failure with capture requested and a two-parameter capture. Until they land the owner's limits say reasons, order and withheld fields are source-read. CL.c1–c3 stay unexercised live. | `CompiledProfileCaptureTests.swift`, `capture.c`, `runner_outcome_bad_request` |
| DT-103.a–e; CL.b1–b3 | Reasoned retention with the limit at `bytecode_b64`: the worker reads the object through a fixed four-member view of a private structure; the receipt "does not establish the structure's layout on the running system, or which bytes application submitted." The owner's limits name the controls. | `35-profile.surface.md` |

Shared edits. The receipt-side input-identity sentence and the
inventory-side sentence form one linked pair with DT-29/81–87 and the
unnumbered investigations; the wording is given under "First
investigation" below. DT-104.b and DT-32 are one decision: the labels
rule's effect is stated as an explicit null with exit 1 (see
DT-31/32/42/113–119), and the corrected test asserts that form. One
suite README credits a "nested receipt version" check that does not
exist and is corrected.

**Discriminating check.** `unit/rust.unit` with the corrected label test,
which fails if a label row is refused by the decode path instead of
admission or if the diagnostics key changes form;
`runner_unit/pwrunner_core_unit_executable`,
`runner_abi_layout/c_swift_layout_agreement` and
`runner_outcome_bad_request/accepted_input_contract` for the coverage
repairs, which reject a decoder that swaps two guards or two reason
strings or leaves a capture field on an `unavailable` receipt. For the
retained admission further evidence would not change the decision: every
operand and both outcomes are determined by source already read.

**Consequence accepted.** A consumer that relies on a `captured` receipt
joins it to its own request (nonce, PID, source digest, re-hashed
bytes); `finished`, `result.ok` and `disposition_integrity: valid`
establish none of these. `captured` keeps implying observed application
and clean completion. Developers: the corrected Rust test is a
`controller/src` edit and lands with a controller thread's rebuild.

**Record.** `records/trace-assessments/I-receipts.md`, Subject 1 and
"Outside the review".

### DT-105–112 — wire fingerprint, variant production, conditional-null projection, path compaction, reader rule order, shape and support coverage

**Established.** Fifty-eight claims are assessed and nearly all hold at
`837296af`; the ten files the review hashed are byte-identical. The
review's run and probe drivers are absent. Re-executed now: the
schema-mutation probes in memory over mutated copies of the schema, and
the projection probes with the Python reader over 261 Swift-written
frames and 608 live envelopes retained from run
`20261118T011154Z_5cfcec0a` at `2f4d76e4`; the counts match the
review's. No Rust or Swift code was compiled or run, so the Rust-side
executed rows rest on source reading and on the Rust projection recorded
in the retained envelopes. Identity sensitivity and admission
discrimination are kept apart: the fingerprint moves for declarations no
producer writes, and a mismatch establishes only that two builds' schema
declarations differ. Six review statements are narrower than written.
CONV.d and DT-106.f: the whole identity JSON is retained in the wire
shape golden and the contract generator's check refuses on drift, a
registered support the review did not count. DT-107.c: the literal-tag
tests read the schema, not the hand-written Swift variant writer; only
replay of Swift-written frames rejects a Swift-side edit. DT-109.b: the
null path state is cross-compared between Rust and Python in live
envelopes (37 retained, all equal). DT-111.c and DT-111.g: a hex to
base64 change on `source_sha256` is already rejected by the registered
normal-fixture comparison. DT-110: only a hypothetical schema makes the
two readers disagree.

**Remaining defect, limit or uncertainty.** A frame that carries a
conditional dependent without its guard is admitted and the carried
value is absent from public JSON; no shipped producer can build that
state (0 instances in 261 frames and 608 live envelopes). Schema
validation accepts rule combinations on which the two readers' rule
orders differ, a variant whose JSON does not identify its case, and
unknown variant-case keys that enter the fingerprint. The shape golden
encodes neither presence nor byte spelling, and the normal-fixture
comparison accepts an authored `null` for an absent key. Not exercised:
a compiled build from a mutated schema, edited frames through the live
controller, a foreign-schema frame through the live controller. Whether
any external consumer relies on `same_as_input` cannot be learned from
the repository.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| CONV.a–c | No change; executed values of the review are unavailable and the retained later run is used with its availability limit. | none |
| CONV.d | The correction is recorded: the identity JSON is retained in the wire shape golden and checked. | this plan |
| DT-105.a–c, .g, .h; DT-106.a–c | Reasoned retention of fingerprint breadth, with the limit beside the identity definition: "The fingerprint identifies the schema declarations and is not a compatibility test." It also changes for a declaration no producer writes; "A match shows that both builds carry the same declarations; structural admission, applied to each frame, checks the bytes." | `21-wire.surface.md` |
| DT-105.d–f | Accurate; no change. | none |
| DT-106.d; DT-107.e; DT-110.a–d | Arrangement change in the generator (R8): schema validation refuses a conditional rule that names a path form as guard or dependent, a guard that is also a dependent, a variant whose cases do not have pairwise different JSON types, and a variant case with a key other than `name` and `type`. No output or fingerprint changes. | `docs/generate_porcelain.py`; `source_drift/porcelain_codec` |
| DT-106.e | No change. | none |
| DT-106.f | Assertion repair: the fingerprint test gains presentation mutations (public name, null rule, projection, path-form order, conditional rule, variant case name, root key). | `source_drift/porcelain_codec` |
| DT-107.a–d | Reasoned retention of the hand-written variant writer with the account corrected: "Swift record writers", and "The variant writer in `PWPorcelain.swift` is hand-written. Check mode does not compare its case tags or payload types with the schema". | `docs/architecture.json`; `tests/suites/source_drift/README.md` |
| DT-107.f | No disposition here; it is the DT-53 observation on binary frames. | DT-53/132/135 |
| DT-108.a, .b, .d, .e, .h | Behavior change (R8): both readers refuse a frame that carries `native_rc` or `team_id` (or any conditional dependent) without its guard as a malformed reply, with the bytes retained; the wire refusal list names it. | generated Rust reader, `tests/lib/porcelain.py`; `21-wire.surface.md` |
| DT-108.c | No change; it bounds the exposure to non-shipped producers. | none |
| DT-108.f | Reasoned retention with the limit: "No reader checks this relation: a result marked `synthetic` that carries a native return is admitted and projected as received." | `31-steps.surface.md` |
| DT-108.g | Assertion repair: the Python actor reader requires a nonempty identifier on a bound row, as Rust and Swift do, with one shared fixture row. | `tests/lib/actor_evidence.py` |
| DT-109.a, .d, .e | No change. | none |
| DT-109.b | No change; the live cross-comparison is recorded. | this plan |
| DT-109.c, .f | Reasoned retention of path-form compaction with the limit: "The compaction applies to public JSON only; the frame, and the envelope's retained copy of it, carry each derived form." No non-frozen document states the size rationale, so nothing stale is removed. | `21-wire.surface.md` |
| DT-111.a, .d | Reasoned retention; limit in the fixtures README: the omit or null rule of an optional field is compared with an authored expectation only where the normal fixture leaves that field absent or a dedicated assertion names it. | `tests/fixtures/README.md` |
| DT-111.b, .e | Assertion repair and credited claim narrowed: the normal fixture is corrected and compared exactly; the accounts say shape checks record key names and JSON types and do not distinguish an omitted key from an explicit null. | `normal_reply.json`, `porcelain_replies.py`, `tests/fixtures/README.md` |
| DT-111.c, .g | No change; the fixture already pins byte spelling for the fields it carries. | none |
| DT-111.f | No disposition here; owned by DT-45/47/49/52 and DT-95–104/134. | those rows |
| DT-112.a | Reasoned retention with the limit: "The projection spells the bytes received; digest length is checked only by the equipment and control-observation readers." | `21-wire.surface.md` |
| DT-112.b–e | No change. | none |
| COV.a–d | No change beyond the entries above; the `team_id` reader difference is resolved by reading. | none |

An identity over binary structure alone, removal of path compaction,
generation of the Swift variant writer, a semantic rule against a
synthetic result with a native return and a declared byte width per
digest are considered and not selected.

**Discriminating check.** R8: the codec control that today asserts a
dependent without its guard projects to `{}` becomes an expected
refusal, and a literal-frame Rust test returns a malformed-frame error
for the state; both run first against the current readers, where they
fail. A sketch of the refusal projects all 261 retained Swift frames and
all 608 retained live host frames identically. Five generator refusal
controls (guard is a path form; dependent is a path form; chained guard;
variant with two integer cases; variant case with an extra key) each
require the diagnostic and unchanged fixture bytes. The exact
normal-fixture comparison rejects an omit/null flip on any optional
field the frame leaves absent.

**Consequence accepted.** No shipped output changes. A reply from a
producer other than the shipped host that carries a dependent without
its guard is refused as `malformed_runner_response` where it was
admitted with the value missing. A user who sees "unsupported porcelain
schema" concludes only that runner and controller were built from
different schema declarations. Developers: authoring one of the refused
schema combinations stops the generator and the build.

**Record.** `records/trace-assessments/J-wire-identity.md`.

### Both unnumbered import/receipt investigations

**Established.** Two passes assess these investigations from their two
sides: the import-inventory side (70 claims) and the receipt side (64
claims). Both the first synthesis and the follow-up narrowing are
retained. Their live run series (`joint-1`, `joint-2`, `joint-3`, build
`8b5de2b2`, one unregistered run per case) are absent and not
replayable; `.tmp/82-103-OBSV.md` and `.tmp/SHARED-INTERP-FOLLOW-UP.md`
are accounts, not raw observations. The helper-side analogues of the
divergence cases were re-executed now on the `2f4d76e4` helper. The
source join holds by construction; the file join is unobserved;
divergence was observed only by selected contrasts; effects, file opens
and bytes applied are different claims.

**Remaining defect, limit or uncertainty.** No component observes the
compiler's file reads or the bytes application submitted, and no field
could join an import record to a receipt.

**Treatment.** The two investigations are disposed of individually under
"Unnumbered investigations" below. No product behavior changes for
either beyond R12's scanner and helper changes under DT-29/81–87. The
distinction between held-source association and compiler-file-input
association is retained; no dossier/receipt source-digest comparison and
no compiler-file observer is added.

**Discriminating check.** See the two subsections.

**Consequence accepted.** A user does not read a dossier reporting
`complete` beside a `captured` receipt as "compiled from this source,
these parameters and these files".

**Record.** `records/trace-assessments/G-import-inventory.md`, Subject B;
`records/trace-assessments/I-receipts.md`, Subject 2.

### DT-44 leads

Each lead is disposed of separately. The record for all thirteen is
`records/trace-assessments/B-smaller-differences-leads.md`, Subject B; the
evidence class is source reading at `837296af` unless a subsection says
otherwise. None of the corrected surfaces is a build-contract input.

#### DT-44 lead a — host-wait stop vocabulary (DT-44.a1–a3)

**Established.** The only producer of `clock_unavailable` is the
termination gate. Three of its four paths end the wait at once; the fourth
(reap observed while the wait clock had faulted) follows fallback sleeps,
so the lead is partly right. Every other wait keeps its own stop value
and sets `clock_fault`. `setup_failed` has two producers (the nonblocking
readiness reader; authority-region and custody setup). `all_resolved`,
`equipment_inspection_failed`, `dependency_failed` and `schedule_complete`
are emitted; the field promises no enumeration.

**Remaining defect, limit or uncertainty.** The stated meaning of
`clock_unavailable` matches no producer. No cited control asserts that a
non-gate wait keeps its stop under a clock fault; that half is source-read.

**Treatment.** Account correction of `lifecycle.host_wait.stop` in
`docs/contract/32-lifecycle.surface.md`: the set is open and each owning
record defines its values; `clock_unavailable` is the termination gate's
stop when a required time sample failed, moved backward or was absent; a
wait that loses the clock elsewhere continues on bounded sleeps, keeps its
stop and reports `clock_fault`; `setup_failed` names both prerequisites.
The Swift doc comment above `PWHostWait` carries the old sentence and is a
build input; it is corrected with the host thread. R13 changes which
disposition cause three actor stop reasons map to; it does not change the
stop strings this meaning describes.

**Discriminating check.** `runner_unit/pwrunner_core_unit_executable`
(`ActorSchedulerTests` asserts the gate's `clock_unavailable` with
`clock_fault: true`).

**Consequence accepted.** None for users; no closed vocabulary is promised.

#### DT-44 lead b — schedule cancellation and setup-timeout vocabulary (DT-44.b1, .b2)

**Established.** `schedule.cancelled` also carries
`unresolved_termination`, `actor_quiescence_unresolved`,
`equipment_execution_<reason>` and `ownership_lost` (the last not in the
lead). The stated list is illustrative, so b1 is not a contradiction.
`setup_status: "setup_timeout"` is also set for an actor whose launch was
skipped because the shared setup allowance was already spent; the reply
distinguishes it (no `launch`, no `subprocess`, application basis
`worker_not_launched`).

**Remaining defect, limit or uncertainty.** Two unlisted cancellation
values mean a stopped worker was not reaped, and the statement does not
say so. No test constructs the never-launched `setup_timeout` actor.

**Treatment.** Account correction of `actor_evidence.schedule.cancelled`
(the full value list, with the two not-reaped values named) and of
`actor_evidence.actor.setup_status` (both situations and how the reply
separates them) in `docs/contract/33-actor_evidence.surface.md`. The
`cancelled` meaning also takes the DT-10 clause on `execution_wait`; one
edit serves both.

**Discriminating check.** New constructed control in `ActorSchedulerTests`:
two actors and a setup allowance the first consumes; the second has
`setup_timeout` and no pid.

**Consequence accepted.** A user treats `unresolved_termination` and
`actor_quiescence_unresolved` as reports that a stopped worker was not
confirmed reaped, and checks for the `launch` record before concluding
from `setup_timeout` that a worker was launched.

#### DT-44 lead c — ordinary wait progress index (DT-44.c)

**Established.** The worker publishes the proceed-wait index with the
phase's first slot for every phase of either request form; only the
activation wait is actor-only.

**Remaining defect, limit or uncertainty.** The field text attributes the
index to "actor waits".

**Treatment.** Account correction of `lifecycle.progress.index` in
`32-lifecycle.surface.md`: activation and release waits identify their
visit's first slot; every phase of either form has a release wait.

**Discriminating check.** Reading suffices (two call sites).

**Consequence accepted.** None.

#### DT-44 lead d — absent versus incomplete `not_reached` slot (DT-44.d)

**Established.** The Swift resolver, the Python oracle, the Rust reader
and the failure evidence contract all accept `not_reached` beside any
non-completed slot; only RESPONSE says "an incomplete slot". The host
writes slot identities from an admitted plan, so an absent slot does not
arise in production.

**Remaining defect, limit or uncertainty.** The RESPONSE statement is
narrower than the four implementations. The state is reachable only with
constructed or inconsistent output.

**Treatment.** Account correction in `32-lifecycle.surface.md`: "only
after confirmed reaping and without a completed slot, whether that slot
is incomplete or absent". A stricter resolver is not selected. The
prohibited-inference line in `tests/lib/lifecycle_contract.py` reads "an
absent slot alone" so that both it and the positive row stay true.

**Discriminating check.** New constructed control in
`DispositionResolverTests`: duplicate slot identities, terminal basis,
progress before the step; expect boundary `not_reached` and result
`unresolved: slot_unavailable`.

**Consequence accepted.** None; the result claim beside an absent slot is
separately `unresolved`.

#### DT-44 lead e — EOF beside collection deadline (DT-44.e)

**Established.** By reading, validator collection can record
`stdout_collection_stop: "eof"` beside deadline-expiry text in
`read_error` when stdout had already ended and request bytes remained
unwritten at the I/O deadline. The shipped validator closes stdout only
by exiting, so the state needs a substituted validator or an exit within
microseconds of the deadline.

**Remaining defect, limit or uncertainty.** Not executed. The `read_error`
meaning is too narrow on four branches (read failure, retention limit,
poll or clock failure, I/O deadline) whether or not this one is reachable.

**Treatment.** Account correction of `lifecycle.validator.read_error` and
one clause on `stdout_collection_stop` in `32-lifecycle.surface.md`. The
closing-stdout/held-stdin fixture is not built: reachability does not
affect the disposition, and the fixture could establish it only under
substitution. A producer change that records `deadline` is not selected;
it would make the stop value false for stdout.

**Discriminating check.** None added; the correction follows from the
branch text.

**Consequence accepted.** A user does not read
`stdout_collection_stop: "eof"` as "collection ended without a fault";
`read_error` and `io_error` are read beside it.

#### DT-44 lead f — actor schedule versus worker allowance (DT-44.f)

**Established.** By reading, `runner_timeout` is produced only for a
policy-transfer timeout and a `sentinel_deadline` stop; actor stops never
carry `sentinel_deadline`, and a cancelled schedule becomes
`runner_failed`. The technical statement is already scoped to the
sentinel and policy-transfer deadlines and is silent on the actor case.
The frozen guide's wording is broader.

**Remaining defect, limit or uncertainty.** The reply-level outcome for an
actor allowance expiry is not executed anywhere; the scheduler tests
assert only `cancelled`.

**Treatment.** Reasoned retention of the behavior. `reply.record.outcomes`
gains: "Expiry of the actor schedule's execution allowance is reported as
`runner_failed`." R13 maps three scheduler stop reasons to `completion`
and adds no label for allowance-expiry kills, so this sentence stands
after R13 and is confirmed against its final behavior.

**Discriminating check.** Reading suffices for the account. An executed
witness would need a reply-level run of `runActors` with a shortened
schedule allowance, which the tree lacks.

**Consequence accepted.** A user does not classify actor-form timeouts by
`runner_timeout`; `schedule.cancelled` and the execution wait's stop
identify the boundary.

#### DT-44 lead g — `actor_unavailable` wording (DT-44.g)

**Established.** `actor_unavailable` is the scheduler's internal end
reason; no reply assembly reads it. EXTENSIONS, a shared region copied
into the frozen guide, names it as how visits read.

**Remaining defect, limit or uncertainty.** The shared-region owner names
a value no reader can observe.

**Treatment.** Account correction in `docs/EXTENSIONS.md`: the visits are
not activated; their phases carry no `activation_observation`,
`arrival_observed: false` and `collection_status: not_reached`; the run
is `runner_failed`. The guide's copy stays frozen.

**Discriminating check.** Reading suffices; the phase assembly has no
field for the end reason.

**Consequence accepted.** A user does not look for `actor_unavailable` in
a reply.

#### DT-44 lead h — capacity-refusal policy format (DT-44.h)

**Established.** Partly refuted. `refusals.admission.echo` already states
"use unknown for unsafe ordinary policy format"; only the reply field text
names decode refusal alone. `failure_boundaries/admission` passes in the
retained development runs.

**Remaining defect, limit or uncertainty.** The field text is incomplete.

**Treatment.** Account correction completing `reply.record.policy_format`
in `docs/contract/30-reply.surface.md`: a capacity refusal whose ordinary
format is absent or exceeds its bound also uses `unknown`.

**Discriminating check.** `failure_boundaries/admission`.

**Consequence accepted.** None.

#### DT-44 lead i — arrival/completion sampling points (DT-44.i)

**Established.** The ordinary form reports the final acquisition after
cleanup; the actor form reports what the scheduler observed during the
visit. A publication arriving after the host's wait ended reads `true` in
the ordinary form and `false` in the actor form.

**Remaining defect, limit or uncertainty.** One field text covers two
observation times.

**Treatment.** Account correction of `arrival_observed` and
`completion_observed` in `33-actor_evidence.surface.md`, stating both
sampling points. One sampling point for both forms is not selected.

**Discriminating check.** Reading suffices.

**Consequence accepted.** A user comparing these fields across request
forms accounts for the different observation time.

#### DT-44 lead j — validation metadata persistence (DT-44.j)

**Established.** By reading, `runner validate` rewrites the
unentitled-worker hash and the equipment inventory and records `byoxpc`
for a record with no kind. The field statement "retained at installation
when available" is false after a validation.

**Remaining defect, limit or uncertainty.** Not executed; no
`runner validate` was run by the review or the assessment. Whether
`runner_byoxpc/registry_recovery` reads these fields back was not checked.

**Treatment.** Account correction in
`docs/contract/50-installation.surface.md`: the validate rule names the
three writes; the hash is "from the most recent installation or validation
read"; the inventory is replaced by the verified current inventory at a
successful validation; `kind` notes the recorded `byoxpc`. Adding
installation-time and validation-time fields is not selected.

**Discriminating check.** A registry-only control (constructed registry
and bundle directory, `runner validate`, read back the three fields) would
witness it; until one exists the corrected text is source-read.

**Consequence accepted.** A user does not treat the registry's
`unentitled_worker_sha256` or `worker_equipment_inventory` as
installation-time values after a `runner validate`.

#### DT-44 lead k — defensive unsupported vocabulary (DT-44.k)

**Established.** Both request forms refuse an unmapped attempt or unknown
filter kind before any child; the reply vocabularies list every value the
producer can emit. Not a contradiction.

**Remaining defect, limit or uncertainty.** None; the RESPONSE entries do
not repeat the word "defensive".

**Treatment.** Reasoned retention without edit. The limit is already
stated at `probes.attempt.action` and in REQUEST's authored prose.

**Discriminating check.** `failure_boundaries/admission`.

**Consequence accepted.** None.

#### DT-44 lead l — adjacent readiness and count statements (DT-44.l1, .l2)

**Established.** The readiness helper returns 0 or -1, not a native write
result. The worker publishes the received count and a flag; the host
reads both counts after the flag.

**Remaining defect, limit or uncertainty.** One field text and one subject
introduction describe the mechanism inaccurately.

**Treatment.** Account correction of `lifecycle.worker_evidence.readiness`
and of the `lifecycle.policy_read` introduction in
`32-lifecycle.surface.md`.

**Discriminating check.** Reading suffices.

**Consequence accepted.** None.

#### DT-44 lead m — reporting-failure family applicability (DT-44.m)

**Established.** Controller admission gives a `reporting_failure` finding
to a reply whose outcome is `runner_reporting_failed` without the record.
The host sets that outcome only with the record, so the branch needs a
constructed or foreign reply. No test reaches it.

**Remaining defect, limit or uncertainty.** The family table's
applicability is incomplete.

**Treatment.** Account correction of the family row in
`docs/contract/41-diagnostics.surface.md`. An optional Rust control lives
in a build input and is added only with a controller thread that already
rebuilds.

**Discriminating check.** Reading suffices (seven lines).

**Consequence accepted.** None.

### Unnumbered investigations

The claim identifiers below are the assessments' own labels for passages
of the two investigations; the same label (for example `U1.o1`) names the
import-side reading in one assessment and the receipt-side reading in the
other. Both readings are disposed of.

#### First investigation — interdependencies of import inventories and compiled-profile receipts

**Established.** Evidence class: source reading at `837296af`, plus
constructed helper runs re-executed now on the `2f4d76e4` helper; the
investigation's live runs are dated observations whose outputs are gone.
The controller builds the dossier from the resolved request value,
serializes that value once and delivers it; the host hashes the source
it received and refuses a capture whose worker digest differs; so the
dossier's applied-source digest, the reply's policy digest and a
captured receipt's source digest are equal by construction. The import
walk is a controller read made before delivery; the worker's compiler
reads imported files later, in another process. The investigation is
mistaken in two places: "no reader compares" the shared source digest,
when several registered tests compare it with their own request source
and the host enforces it on every captured receipt; and "the separation
is documented in three places", when the rendered public text is one
sentence (the second is an unrendered authoring reason and the other two
are source comments). Its statement that a file in both search
directories "contradicts" the resolver comment is corrected by the
follow-up. Its generalization that compiled bytes "carry neither the
import path nor the split" is narrowed by the follow-up.

**Remaining defect, limit or uncertainty.** Accurate statements combine
to invite "compiled from this source, these parameters and these files".
The receipt owner's pin says its fields bind "consumed input bytes".
Unobserved by any component: the compiler's file opens, the bytes it
read, the bytes application consumed. A file change inside one run was
never exercised. One import-side observation is new: a computed import
written without a space after `import` is not flagged even internally.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| Import side: U1.o1 (first half), U1.2c, U1.4f, U1.5q1a, U1.5q1c, U1.5q2 | Reasoned retention of the separation, with the inventory-side sentence below. | `11-policy.surface.md` |
| Import side: U1.o1 (second half), U1.6 (fourth sentence), U1.2a | Narrowed reading adopted and corrected further: the source join holds by construction and is compared by tests. | existing `witness_contract/dossier_witness`, `integration/cli.integration`, `witness_contract/actor_compositions` |
| Import side: U1.o2, U1.3a, U1.3d, U1.5q3a | Accurate; the scanner-miss divergence is removed for the observed spellings by R12, and the unevaluated-form divergence is retained under the stated limit. | dossier contrasts |
| Import side: U1.o3, U1.4a, U1.4b | No action. | none |
| Import side: U1.o4, U1.2d | Narrowed reading adopted; R12 removes the disagreement between a fallback envelope's helper inventory and its dossier for a computed import. That pairing itself stays unexecuted. | helper contrasts |
| Import side: U1.1-82, U1.1-84, U1.1-85, U1.4d, U1.5q3b, U1.5q4 | Disposed of under DT-29/81–87. | DT-29/81–87 |
| Import side: U1.4e | Adopted, with the exception that `(import(…))` is not flagged today; closed by R12. | unit tests |
| Import side: U1.2b | No change. | none |
| Import side: U1.2e | Account correction: the inventory-side sentence puts the non-inference into rendered text. | `11-policy.surface.md` |
| Import side: U1.2f | Reasoned retention; the limit is already stated: "Files named by imports can change between these independent reads." | none |
| Import side: U1.3b, U1.3c, U1.3e | Retained as stated; the product makes no cause claim and gains none. | none |
| Import side: U1.3f | Narrowed reading adopted. | none |
| Import side: U1.4c | Adopted; reflected in the closure limit. | helper contrasts |
| Import side: U1.4g, U1.7 | Judgment adopted: not an unmet promise; the exclusion is stated on both sides. | both surfaces |
| Import side: U1.5q1b | Corrected reading adopted; no change. | none |
| Import side: U1.5q3c | Frozen guide sentence; no action. | none |
| Import side: U1.5q3d | Adopted and extended: every unflagged spelling fails the dossier's definition as the trailing-comment literal does. | unit tests |
| Import side: U1.8, U1.L | Adopted as conventions. | none |
| Receipt side: U1.o1, U1.s2.a, U1.s2.b, U1.s5.q1 (join clause), U1.s6 | Reasoned retention; the narrowed statement is adopted and no comparison is added. | existing `runner_outcome_bad_request/accepted_input_contract`, `witness_contract/actor_compositions` |
| Receipt side: U1.o2, U1.s1.98, U1.s1.103, U1.s2.d–f, U1.s2.h, U1.s3.c, U1.s4.c, U1.s4.e, U1.s4.f, U1.s5.q1 (other clauses), U1.s5.q2, U1.s5.q3, U1.s7 | Reasoned retention with the limit stated in the receipt's owner. | `35-profile.surface.md` |
| Receipt side: U1.o3, U1.o4, U1.s2.c, U1.s2.g, U1.s2.i, U1.s3.a, U1.s3.b, U1.s3.d, U1.s4.a, U1.s4.b, U1.s4.d, U1.s5.q4, U1.s8, U1.lim | Accurate observations or reasoning that holds; no change. | none |

One linked pair of sentences states the limit, one in each owner. The
inventory side, in "Separate reads and their identities": "No field of a
run envelope or a helper envelope associates an import record with the
bytes the worker's compiler read. The dossier's applied-source digest,
the reply's policy digest and the receipt's source digest are digests of
one held source string; their equality says nothing about imported
files." The receipt side, in "Captured input identity", linking to the
first: "The identity covers the source string and the parameter strings
passed to the compiler. No receipt field identifies a file the compiler
reads for an `import` form, so equal source and parameter identities do
not imply equal bytecode." The two proposals agree in placement and
conflict in one phrase: the import-side evidence shows files reaching
the compilation with no `import` form (`load`, `eval`, an aliased
`import`), so the receipt-side sentence and its pin say "a file the
compiler reads" without the qualifier "for an `import` form". The
receipt owner's pin becomes "The host compares the worker-recorded PID,
nonce, source identity and parameter identity with its own values before
emitting them; files the compiler reads are outside these identities."

**Discriminating check.** A source-digest comparison would restate
construction and would not change the decision. The dossier contrasts
registered under DT-29/81–87 replace reliance on the absent live runs
for the import-side facts. An optional live control for the receipt
side (one source importing a scratch file by absolute path, two runs,
the file rewritten between them: equal identity fields, different byte
digests) would give the structural limit executed support; the limit
holds without it.

**Consequence accepted.** A user keeps the request file, since the
envelope carries its path and digests and not the source text, and does
not treat an enforcement result or matching bytes as showing which bytes
application consumed. A consumer who needs to know which imported bytes
were compiled has no field for it.

**Record.** `records/trace-assessments/G-import-inventory.md`, Subject B
(U1 rows); `records/trace-assessments/I-receipts.md`, Subject 2 (U1
rows).

#### Follow-up investigation — boundaries of the shared import and receipt interpretation

**Established.** Evidence class as above; the `joint-3` series is
absent. The follow-up's narrowing is adopted in full: the source
association holds by construction; divergence was observed only through
the two scanner mechanisms of DT-84 and DT-85 and only by comparison
with runs of known composition; no single envelope shows it; an ordinary
literal import gives an unverified association, not an observed
divergence. Re-verified now by `stat`: `BTLEServer.sb` is one file under
two names in the two search directories (same inode, link count 2); the
device number differs from the one the follow-up recorded. After the
re-executed helper contrasts the DT-84 class has more members than the
follow-up knew. The follow-up's list of tests that join the receipt to
the request source is incomplete; three live tests do.

**Remaining defect, limit or uncertainty.** Two statements are untested
inferences and are not written as fact: that a same-source recompilation
on the same host could not reveal a scanner miss, and that imports under
the read-only system snapshot cannot change within a boot. Not
supported: how the compiler obtained a file, which bytes application
consumed, the mechanism in kernel terms, or breadth beyond one
operation and one pair of paths. External runners were not examined
separately for the claim that the helper projection never appears beside
a receipt.

**Treatment.**

| Claim | Disposition | Owner or check |
| --- | --- | --- |
| Import side: U2.o, U2.1e, U2.D1, U2.D2 | Reasoned retention of the separation; inventory-side sentence as above. | `11-policy.surface.md` |
| Import side: U2.1a | Adopted as an assessment convention. | none |
| Import side: U2.1b, U2.N1 | Narrowed reading adopted and corrected further (tests compare the digests). | existing cases |
| Import side: U2.1c | Becomes a user duty: keep the request. | user-responsibility outflow |
| Import side: U2.1d, U2.N2 | Accurate; see the first investigation. | dossier contrasts |
| Import side: U2.1f | Recorded as an unexecuted inference and a candidate user restraint. | this plan |
| Import side: U2.1g | Adopted and extended to every unflagged spelling. | unit tests |
| Import side: U2.2b, U2.2c, U2.N4, U2.D3 | Narrowed reading adopted; no statement says compiled bytes carry no path information. | none |
| Import side: U2.3a, U2.3b, U2.N3, U2.D4 | Retained as stated: a rule's effect on one path is supported by matched contrast; file opens and bytes applied are unobserved. | none |
| Import side: U2.4a, U2.4b, U2.N6, U2.D5 | Corrected reading adopted; no change. The resolver comment is scoped to its OS version and stays. | none |
| Import side: U2.4c, U2.N5 | Reasoned retention; the mount inference is not asserted in the contract. | none |
| Import side: U2.4d, U2.4e, U2.N7 | Narrowed reading adopted; closed for computed imports by R12. | helper contrasts |
| Import side: U2.D6, U2.E | Adopted as conventions; no action. | none |
| Receipt side: U2.s1.a, U2.s1.b, U2.s1.g, NW1, DX2 | Reasoned retention; the narrowed statement is adopted. The added sentences do not reintroduce "no reader compares". | existing cases |
| Receipt side: U2.s1.c–f, U2.s2.a, U2.s3.b, NW2, NW3, DX1, DX4 | Reasoned retention with the limit stated in the receipt's owner: the identity excludes files the compiler reads; the dossier's records come from a separate earlier read; which bytes application submitted is not observed. | `35-profile.surface.md` |
| Receipt side: U2.o, U2.s2.b, U2.s2.c, U2.s3.a, U2.s4.a–d, U2.ev, NW4–NW7, DX3, DX5, DX6 | Accurate observations or reasoning that holds; the narrowings are preserved as written and constrain future wording. | none |

**Discriminating check.** None added beyond those of the first
investigation. A constructed same-source recompilation would settle the
recompilation inference; it is not needed for any product decision. An
in-run file change during a live run would not change the decision,
since the contract already disclaims simultaneity.

**Consequence accepted.** For imports outside the system profile
directories a user keeps the imported files unchanged from before the
run until it ends, or does not treat the dossier record as describing
what the worker compiled. Whether an expected object compiled from the
same source can check an inventory stays unsettled.

**Record.** `records/trace-assessments/G-import-inventory.md`, Subject B
(U2 rows); `records/trace-assessments/I-receipts.md`, Subject 2 (U2, NW
and DX rows).

### Statements edited for more than one row

Each of these statements is edited once. Where two assessments propose
different text, the row named in the last column records the choice.

| Statement | Rows served | Wording used; conflict | Recorded under |
| --- | --- | --- | --- |
| `identity.public.inputs` and neighbours, `00-identity.surface.md` | DT-08; DT-88–94 | The DT-88–94 text (seven roots and twenty files in full, Git independence, refusal list). It subsumes the DT-08 proposal to add two names. No conflict. | DT-88–94 |
| Input-identity limit: "Separate reads and their identities" in `11-policy.surface.md` and "Captured input identity" in `35-profile.surface.md` | DT-29/81–87; DT-95–104/134; both investigations | One linked pair, one sentence in each owner. Conflict: the receipt-side proposal says "a file the compiler reads for an `import` form"; import-side evidence shows files read with no `import` form, so the qualifier is dropped. | First investigation |
| `cleanup_trigger` meaning, `32-lifecycle.surface.md` | DT-24/30; DT-46/120/121/129 | The derivation text with R13's three actor reasons. Each assessment left the vocabulary-block question to the other; the field takes an open, illustrative block. | DT-46/120/121/129 |
| Self-transfer sentence, `docs/EXTENSIONS.md` | DT-37–41 (DT-39.a); DT-59–61/133 | Two different proposals; the DT-59 text is used because it keeps the collection-and-release condition on both cases. | DT-59–61/133 |
| Retained-cleanup recovery row, `docs/limits.json` | DT-33–35 (DT-34.c); DT-69–73/75–80 | Two different proposals; the DT-69 form removes the false clause and adds no statement to the shared region. | DT-69–73/75–80 |
| Plist ownership branches, `50-installation.surface.md` | DT-33–35 (DT-34.b); DT-69–73/75–80 (DT-76) | Two wordings of the same two branches; the DT-34.b sentence is used. No conflict in content. | DT-69–73/75–80 |
| Labels-rule effect, `35-profile.surface.md`, and the Rust label test's diagnostics assertion | DT-31/32/42/113–119 (DT-32.c); DT-95–104/134 (DT-104.b) | Explicit null with exit 1. The receipt assessment's interim pin ("without distinguishing an absent key") is superseded once the key-presence assertion lands. | DT-31/32/42/113–119 |
| Known-gap scope, `trace-introduction.md`, and the lost-reply gap in ARCHITECTURE | DT-15–21 (DT-20); DT-31/32/42/113–119 | DT-20 leaves to the transport row whether the lost-reply gap becomes a tree gap node; the transport assessment does not take it up. It stays a tour gap. | DT-31/32/42/113–119 |
| Tour commitment lists, `presentation.json` | DT-15–21 (DT-16); DT-37–41 (DT-41) | Both keep the generated lead-in and repair entries. Conflict in reasons: DT-41.b1 assumes `equipment.binding` stays in BUILD's signing list, which DT-16 removes. Both removals stand. | DT-37–41 |
| Envelope assembly sentence, `controller/README.md` and `docs/ARCHITECTURE.md` | DT-37–41 (DT-39.c); DT-31/32/42/113–119 (DT-116.f) | Two different proposals; the DT-116.f text is used because the DT-39.c text keeps fallback compilation joined with the diagnostics. | DT-31/32/42/113–119 |
| `actors.phase.order`, `13-actors.surface.md` | DT-09–10 (DT-10); DT-36/43 (DT-36) | The DT-36 precedence text plus a separate sentence for DT-10. Conflict: the DT-36 text places the allowance label after a confirmed reap; DT-10 establishes a pre-visit site that selects it with no reap. | DT-36/43 |
| `schedule.cancelled`, `33-actor_evidence.surface.md` | DT-09–10 (DT-10); DT-44 lead b | The lead b value list followed by the DT-10 clause on `execution_wait`. No conflict. | DT-44 lead b |
| "Reader validation responsibilities", failure contract | DT-45/47/49/52 (DT-52); DT-53/132/135 | Two additions to one section (nullable-key presence; lifecycle claims). No conflict. | DT-53/132/135 |
| Host line admission, `21-wire.surface.md` | DT-22/57 (R5); DT-48/130 | R5 rewords the sentence; the DT-48 limit is added to the reworded sentence. No conflict. | DT-48/130 |
| `probes.step.step_id` and three other field meanings | DT-15–21 (DT-18.b presence rules); DT-37–41 (DT-37.f bounds); DT-25/50/131 (canonical uniqueness) | Additions to the same meanings; each meaning is written once. No conflict. | DT-37–41 |
| `imports.failure`, `42-dossier.surface.md` | DT-33–35 (DT-33.a); DT-29/81–87 | The DT-33.a order sentence says "nonliteral form"; R12 renames these to forms the scan did not follow. The sentence uses R12's final term. | DT-33–35 |
| `ownership` definition, `34-equipment.surface.md` | DT-63/64/124/125/128; DT-68/127 | Two additions (the meaning of `performed`; the time anchor). No conflict. | DT-68/127 |

### Completeness check

Claims are counted as the assessments' claims tables count them: one per
DT subfinding, qualification or unnumbered-section row. The unnumbered
identity, convention and coverage sections of each investigation are
placed with the row shown.

| Coverage-map row | Pass | Claims counted | All dispositioned |
| --- | --- | --- | --- |
| DT-01–04 | A | 10 | yes |
| DT-05–08 | A (DT-08 also H) | 9 | yes |
| DT-09–10 | A | 7 | yes |
| DT-11–14 | A | 18 | yes |
| DT-15–21 | A | 27 (23, and RC.a–c, AF.a) | yes |
| DT-22/57 | C1 | 9 | yes |
| DT-23/51 | C1 | 9 | yes |
| DT-24/30 | C1 | 10 | yes |
| DT-25/50/131 | L | 24 | yes |
| DT-26–28 | C1 | 11 | yes |
| DT-29/81–87 | G | 68 (including IC.a–e, IL.a–f) | yes |
| DT-31/32/42/113–119 | K | 104 (including EV, Q1–Q3, PR, REL, LIM) | yes |
| DT-33–35 | C1 | 10 | yes |
| DT-36/43 | E | 6 | yes |
| DT-37–41 | B | 34 | yes |
| DT-44 | B | 22 (17 in thirteen leads, and CL.1–5) | yes |
| DT-45/47/49/52 | C2 | 28 (17, and FI-1–7, FL-1–4) | yes |
| DT-46/120/121/129 | E | 22 | yes |
| DT-48/130 | L | 22 | yes |
| DT-53/132/135 | L | 41 (30, and ACC-ID.a–h, ACC-LIM.a–c) | yes |
| DT-54/58 | C2 | 7 | yes |
| DT-55/56 | C2 | 13 | yes |
| DT-59–61/133 | E | 15 | yes |
| DT-62/65/122/123 | E | 25 (17, and XA.1–6, ID.1–2) | yes |
| DT-63/64/124/125/128 | D | 44 (34, and S-1–10) | yes |
| DT-66/126 | D | 14 | yes |
| DT-67 | D | 5 | yes |
| DT-68/127 | D | 16 | yes |
| DT-69–73/75–80 | F | 67 (57, and RC.a–e, RL.a–e) | yes |
| DT-74 | F | 9 | yes |
| DT-88–94 | H | 53 (including DT-08.a–c, Conv.a–d, Lim.a–d) | yes |
| DT-95–104/134 | I | 85 (including RC.a–d, CL rows) | yes |
| DT-105–112 | J | 58 (including CONV.a–d, COV.a–d) | yes |
| Both unnumbered investigations | G and I | 134 (70 import side, 64 receipt side) | yes |
| Total | twelve passes | 1,036 | yes |

Every DT identifier from DT-01 to DT-135 appears in a row; DT-08 appears
in two (its statement in DT-05–08, its executed counterpart in DT-88–94). The
thirteen DT-44 leads carry the seventeen DT-44 claims: a (3), b (2),
c, d, e, f, g, h, i, j, k (1 each), l (2), m (1).

Claims that could not be placed: none. Four points need care when the
records are read against this file:

- The assessments' labels for unnumbered sections collide across files.
  `RC.x` names different sections in the A, F and I files; `CL.x` in the
  B and I files; `U1.x` and `U2.x` name import-side passages in the G
  file and receipt-side passages in the I file. Each is disposed of in
  the row of its own file.
- `DT-08.b` names different sentences in two files (the omission's
  history in the A file; the unnamed-root consequence in the H file,
  where the history is `DT-08.c`). Both are disposed of.
- `DT-57.d`, `DT-107.f` and `DT-111.f` are observations that their own
  assessments hand to another row (DT-53/132/135, and for `DT-111.f`
  also DT-45/47/49/52 and DT-95–104/134). They are placed in their own
  rows with that reference and need no separate treatment there.
- Three points that the assessments left open are settled in their rows:
  worker-slot identity joins under R9 (DT-25/50/131), the
  `cleanup_trigger` vocabulary block (DT-46/120/121/129) and the
  lost-reply gap's place (DT-31/32/42/113–119).
