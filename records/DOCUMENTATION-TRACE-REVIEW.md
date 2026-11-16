# Documentation tracing review findings

Reviewed the ten implementation and acceptance commits from `2fcf9dbc` through
`bfc74b6b`. This record collects observations for later assessment. It does not
decide whether the plan was completed, which layer should change, or which
findings should become work. No fixes to the reviewed implementation accompany
this record.

Three sub-agent reviews covered rendering and ownership, reading paths and
public statements, and verification evidence. The primary review reconciled
their findings and inspected the supporting sources. Evidence consists of source
and document inspection, in-memory or disposable-directory reproductions, and
comparison with existing local run records. No build or test suite was rerun.
Line references below refer to the reviewed `bfc74b6b` tree.

The plan and its tracked preparation/acceptance directory are retired with this
review. Their historical contents remain available with, for example,
`git show bfc74b6b:DOCUMENTATION-TRACE-PLAN.md` and
`git show bfc74b6b:records/documentation-trace/verification.md`.
The guide rewrite outflow is reduced to a placeholder; these findings imply no
requirements for that future rewrite.

## Findings

### DT-01 — Nested generated regions can discard a complete statement family

[presentation.py](../docs/contract/presentation.py), lines 159–194, inventories
region names and counts before replacing regions sequentially. The replacement
at lines 119–125 checks each region's own marker order, but the renderer does
not reject overlap or nesting between regions it owns.

In a disposable copy of the presentation inputs, move the policy begin marker
immediately before the request begin marker in REQUEST, leaving both end
markers at their original positions. The request region is now inside the
policy region; each marker still occurs once and each pair is ordered.
`presentation.render` returns successfully, but its returned REQUEST contains
neither the request-region markers nor `contract-request-specimen`. Rendering
the outer policy region overwrites the request region rendered earlier.

This was a rendering reproduction, not a CLI write. The runtime consumes the
returned mapping for output. A later invocation would detect the missing
marker, but that does not prevent the first generation from returning damaged
content. The currently committed regions are not nested. The observation limits
what pre-write destination validation establishes.

### DT-02 — Moving an entire destination can leave an unchecked old statement copy

The destination discovery, marker scan and ownership inventory in
[presentation.py](../docs/contract/presentation.py), lines 76–79, 159–172 and
209–217, inspect the documents currently named by the map. The comment at line
161 says obsolete markers must not preserve old statements outside the declared
inventory, but a document removed from that inventory is no longer inspected.

In a disposable copy, rename the map's `docs/REQUEST.md` key to
`docs/REQUEST-ALT.md`, copy REQUEST's content to the new file, and retain the
original. Every subject still has one mapped destination. Rendering succeeds
and emits the new destination. The old REQUEST retains all its generated
statements, including `contract-request-specimen`, while disappearing from
`destinations`, `ownership` and the returned outputs.

The coverage control in
[contract_tree_controls.py](../tests/suites/source_drift/contract_tree_controls.py),
line 1314 onward, counts statements in the newly rendered mapping. The broader
link check can inspect the old file, but resolving links do not expose a stale
duplicate statement. This reproduction establishes the ownership omission; it
does not claim a complete mutated-checkout test run passed. It bears on future
document moves, including separating a standalone interface from RESPONSE.

### DT-03 — Link rebasing changes literal text and misses an encoded live link

[presentation.py](../docs/contract/presentation.py), lines 82–115, uses the
Markdown reader to discover links, then a separate regular expression to rewrite
their surrounding inline source ranges. Those operations do not always agree
on what text represents the link destination.

With `homes = {'demo': 'docs/RESPONSE.md'}` and source document
`docs/REQUEST.md`, these are the reproduced input/output pairs:

```text
Input:
\[Literal](#contract-demo) and [Live](#contract-demo).

Output:
\[Literal](RESPONSE.md#contract-demo) and [Live](RESPONSE.md#contract-demo).
```

The escaped opening bracket makes the first occurrence literal text. It is
nevertheless rewritten because the live link in the same paragraph supplies
the replacement key.

```text
Input:
[Encoded](#contract%2Ddemo) and [Live](#contract-demo).

Output:
[Encoded](#contract%2Ddemo) and [Live](RESPONSE.md#contract-demo).
```

The Markdown reader decodes the first target to `#contract-demo`. The rewrite
looks up the original encoded spelling instead, leaving the actual link local
to the wrong document. These are verified transformation behaviors, not errors
found in current authored passages. The existing rebasing controls beginning at
[contract_tree_controls.py](../tests/suites/source_drift/contract_tree_controls.py),
line 1268, cover inline code and several reference forms but not these cases.

### DT-04 — Scope-preservation checks accept a condition detached from its rule

The new control at
[contract_tree_controls.py](../tests/suites/source_drift/contract_tree_controls.py),
lines 1350–1392, searches for required phrases anywhere in each destination
document. Its positional assertion checks the order of two result-case anchor
strings. Its rejecting controls remove every occurrence of a phrase or exchange
the anchor names.

A read-only reproduction removed this sentence from the rendered
`transport.delivery.invoke` rule:

> A grant was admitted and a fresh continuous-clock sample is before the original deadline.

Appending it under an unrelated final heading in the same ARCHITECTURE document
still satisfies every required-phrase predicate and the case-anchor ordering
predicate. The sentence is authored at
[20-transport.surface.md](../docs/contract/20-transport.surface.md), line 125,
and currently appears with its rule at
[ARCHITECTURE](../docs/ARCHITECTURE.md#contract-transport-delivery-invoke),
lines 103–108.

No such detachment was found in the committed output. The finding is that these
controls establish presence and selected ordering, without establishing that a
qualifying condition still governs the obligation it belonged to.

### DT-05 — Authored record definitions are labeled as imported declarations

The changed-item index labels every `node.record` as an “imported record
declaration” in [presentation.py](../docs/contract/presentation.py), lines
147–148. The model also contains records synthesized from typed fields in the
surface tree. `_inline_records` in [tree.py](../docs/contract/tree.py), lines
630–665, marks those records `authored=True` and records their surface file as
the source.

Twelve current records receive the imported label despite that authored status:
`VersionData`, `ControllerSelectionOptions`, `ControllerRunnerSelector`,
`ValidatorDirectStatus`, `ValidatorDirectResult`, `ValidatorDirectError`,
`RunnerReconcileData`, `RunnerReconcileRecord`, `RunnerReconcileCandidate`,
`RunnerReconcileInspectionError`, `RunnerCleanupObservation` and
`RunnerCleanupWait`. For example, the two controller selector records appear
with the imported label in [CONTRACT](../docs/CONTRACT.md#follow-a-changed-item),
lines 706–707, while their definitions are authored in
[10-request.surface.md](../docs/contract/10-request.surface.md).

The index presents a different provenance relationship from the one the model
records. A reader could infer independent source-declaration extraction where
the shape is authored in the same tree as its meaning.

### DT-06 — The changed-item lookup omits available interface-source relationships

[CONTRACT](../docs/CONTRACT.md#follow-a-changed-item) invites review starting from
a changed implementation or generated interface. Its index has no route for
`controller/src/interface/result.rs`, `controller/interface/inventory.json`,
`cards.rs`, `joins.json` or `mutations.json`. It does list
`result.admitted_finished`, at line 1301, as an identifier linking to the result
commitment.

[presentation.py](../docs/contract/presentation.py), lines 149–150, emits each
interface identifier without resolving the inventory relationship. The
[inventory](../controller/interface/inventory.json), near line 731, already
names `controller/src/interface/result.rs` as the result relation's reader;
the [joins](../controller/interface/joins.json) also hold case and mutation
associations. Those existing relationships do not become routes in this index.

The general interface README link still permits manual investigation, and the
introduction explicitly calls the associations partial. The concrete remaining
difficulty is that a reviewer beginning with a changed `result.rs` must recover
its inventory relationship before using the advertised lookup. This observation
does not assume that every source or command should have a complete impact map.

### DT-07 — The RESPONSE example excerpt can drift from its named source

[RESPONSE](../docs/RESPONSE.md#read-the-published-example), lines 121–140,
describes its JSON fragment as the second action's operands from
[EXAMPLE_DOCUMENT](../controller/src/example_document.rs). That fragment is
authored outside generated regions; the first generated region begins at line
215. The corresponding complete REQUEST example is extracted from the constant.

An in-memory source overlay replaced `/usr/share/dict/connectives` in the
constant with `/private/tmp/review-new-read-target`. Loading the tree with that
overlay and calling `presentation.render` changed the generated REQUEST
example, while the RESPONSE opening retained the original path and contained
none of the replacement path. No repository file was changed for the probe.

The current excerpt matches its source. The observed gap is that regeneration
can update the cited owner while leaving this claimed excerpt behind. Existing
extraction controls exercise the surface tree's examples; no freshness check
tying this authored fragment to the second action was found.

### DT-08 — The development-identity input description omits a selected directory

[00-identity.surface.md](../docs/contract/00-identity.surface.md), lines 63–73,
and its rendering in
[CONTRACT](../docs/CONTRACT.md#contract-identity-public-inputs), lines 80–90,
list the source roots included in the development identity without naming
`controller/interface`.

[build_contract.py](../docs/build_contract.py), lines 15–16, includes that
directory in `DIRECTORIES`. Its selected `.rs` files include
[cards.rs](../controller/interface/cards.rs) and
[inventory.rs](../controller/interface/inventory.rs). A change to those sources
therefore changes identity through a discovery root absent from the public
description. The omission predates this reorganization and remains visible in
the identity statement that supports the new tracing path.

### DT-09 — The run sequence and controller account disagree about optional logs

The current-run sequence in
[ARCHITECTURE](../docs/ARCHITECTURE.md#one-run-in-time), lines 298–303, ends with:

```text
decode typed records;
admit reply version;
complete execution;
optional logs;
print envelope
```

[CONTROLLER](../docs/CONTROLLER.md#receiving-and-evaluating-evidence), lines
239–240, says the run path does not gather external log candidates. Inspection
of `run` and `complete_execution` in
[run_flow.rs](../controller/src/run_flow.rs) likewise found no intervening
log-collection stage. The diagram describes a current run, not a proposed
extension. The optional-log line was retained from the older tour; the surviving
accounts give different expectations about what the run collects.

### DT-10 — Timeout cancellation wording does not distinguish unavailable clock evidence

The revised `actors.phase.order` statement in
[13-actors.surface.md](../docs/contract/13-actors.surface.md), line 225, says
arrival or completion timeout cancels for exhausted execution allowance. Its
complete rendering is in
[REQUEST](../docs/REQUEST.md#contract-actors-phase-order).

There is also a source path to that cancellation label when the clock cannot
establish remaining allowance. `HostWaitClock.excludeSince` can mark the clock
faulty following collection; `remainingNs()` then returns `nil` in
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift), lines 923–950 and
1034. The pre-release check in
[ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift),
line 425, evaluates `(clock.remainingNs() ?? 0) == 0` and selects
`completion_timeout`. If cleanup establishes reap, lines 475–477 select
`execution_allowance_exhausted`.

This is a source-established path conditional on reaching collection and later
reaping the actor; no clock-fault specimen was executed for this review. A raw
wait record can retain `clock_fault`. The cancellation label alone therefore
does not establish measured allowance exhaustion. The public wording does not
make clear whether it describes the selected classification or establishes
that time was actually exhausted.

## Review coverage and limits

The evidence review matched the three recorded final-run `run.json` hashes,
run IDs, outcome counts, completion, harness-error and artifact-integrity
summaries against the local files. The default run remains recorded as 232
passes and one failure; the combined ledger draws 227 credits from it, six
from the replacement run and four extra cases from the selected run. No
contradictory pass count was found. This is a comparison of retained evidence,
not a fresh execution or a new acceptance verdict.

The inspected runs are under `tests/out/runs/documentation-trace-final-controls`,
`tests/out/runs/documentation-trace-default` and
`tests/out/runs/documentation-trace-fixture-recheck`. They are gitignored,
local-only evidence subject to the repository's existing retention rules.
Retiring the tracked acceptance directory does not remove these managed outputs.

A direct baseline comparison also found no changes in the user-guide bytes,
surface shape goldens, free-text counts, interface inventory/joins, porcelain
schema or ABI layout golden. That preservation does not resolve the findings
above. The review did not exhaust every native failure path or every possible
document arrangement, and the findings intentionally carry their own evidence
limits rather than a collective completion judgment.

## Additional findings: tracing through CONTRACT

A second, independent investigation used [CONTRACT](../docs/CONTRACT.md) as the
starting point: from its commitment index to the complete statements, from
those to the cited sources and checks, and from changed sources back through
the changed-item index. It was made against tree `4816b0e4`; line references
below refer to that tree. The signed app used for reproductions is
`dist/PolicyWitness.app`, built from `8b5de2b2` (`build.number` 1482,
`development:bdefcb44…`); the three later commits changed only `records/` and
one preflight test file. Run outputs and scratch inputs named below are local
and gitignored or temporary.

Each entry states how it was established: **reproduced** (a command was run and
its output read), **source inspection** (files compared by reading or by a
read-only script), or **unresolved** (a suspicion, with what would settle it).
DT-01 through DT-10 above are unchanged; entries below cross-reference them
where they touch the same ground.

### DT-11 — Executed support names runs that this checkout does not hold

Nine owners carry `grade: "executed"`. They name three runs:
`20261111T155411Z_29ef0802` (five owners), `20261111T162345Z_3d6c7242` (three)
and `20261110T195016Z_0d197151` (one). The authored facts are in
[14-extensions.surface.md](../docs/contract/14-extensions.surface.md) lines
483–494, [21-wire.surface.md](../docs/contract/21-wire.surface.md) lines
123–149 and 282–294, [33-actor_evidence.surface.md](../docs/contract/33-actor_evidence.surface.md)
lines 154–166, [35-profile.surface.md](../docs/contract/35-profile.surface.md)
lines 340–351 and [41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
lines 758–770 and 1151–1177. CONTRACT renders them as `Run:` entries under
[Evidence support](../docs/CONTRACT.md#evidence-support), at lines 2109, 2291,
2298, 2319, 2473, 2571, 2620, 2634 and 2641.

Source inspection and local search: no `run.json` under `tests/out/` carries
any of the three identifiers (the eighteen retained runs there are dated
20261115–20261116); `acceptance/tests/run.json` in each of the four release
archives under `dist/archive/` carries a different identifier; `records/` and
`dist/evidence/` do not mention them. The only local occurrences outside the
contract documents are generator-receipt blobs that are copies of those
documents. Several contexts name artifacts of the run (`cargo-test-bins.log`,
`writer-cap-receipt.json`, `consumer_subject_*.json`, `control.log`); files
with those names exist locally only under later runs.

Five owners identify the exercised source as
`reviewed-inputs sha256:<digest> (b6ce6d26 dirty)`. The string
`reviewed-inputs` occurs in no tracked file other than the surfaces and their
renderings, so the tree states neither the input set nor the framing of that
digest. `b6ce6d26` exists as a commit; the `dirty` state it qualifies is not
recorded. By contrast, the direct-validator owner at
[21-wire.surface.md](../docs/contract/21-wire.surface.md) line 293 lists three
per-file SHA-256 values, and `shasum -a 256` of the current
`sb_api_validator.c`, `no_report.c` and `validator_batch_mode/run.sh`
reproduces all three (reproduced).

The profile owner states that "its development run is disposable"; the other
eight state no availability limit. [tree.py](../docs/contract/tree.py), lines
789–799, requires only that `run` and one of `source_snapshot`/`build` be
nonempty strings. The grade definition in CONTRACT says the named run
"exercised the stated assertions with its identified source or build". The
observation is that a reader following an executed citation reaches a run
identifier and, for five owners, a source identifier, neither of which can be
opened or recomputed from this checkout. Limit: only this checkout was
searched; other machines or backups were not.

### DT-12 — Counts quoted in executed support differ from the present corpus

Two executed owners share one context sentence: "Swift judgments over 142
typed frames were retained before encoding; exact-one Rust replay carried 143
frames … and seven JSON-only controls"
([33-actor_evidence.surface.md](../docs/contract/33-actor_evidence.surface.md)
line 161; [41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
line 765; rendered in [RESPONSE](../docs/RESPONSE.md) at lines 1376 and 3083).

The local run `tests/out/runs/documentation-trace-default` (run
`20261116T004927Z_ed1d41ef`) holds the same case's reader-corpus receipts:
`swift.json` records 152 cases, `rust.json` and `python.json` record 153 with
`json_only: 7`, and the directory holds 152 `.pwp` frames (source inspection of
retained output). `git log b6ce6d26..HEAD` shows three later commits to
`ReaderCorpusTests.swift` and `reader_corpus.py` on 2026-11-13 (`8eeae6c7`,
`59d2709d`, `2cee133b`).

The quoted sentence is attributed to its named run, and nothing shows it was
wrong for that run. The cited check symbols, however, are links to the present
files, whose corpus is ten frames larger than the one described. The other
quoted counts that could be compared agree with later local runs: 42 subject
controls with 12 accepting and 30 refusing
(`plain-help-acceptance-d978d47d`), and a 621-byte fallback with two writer
failures at a 134,217,729-byte input (`documentation-trace-default`). Of
fourteen source and check files cited by the executed owners that were
examined, nine have between one and five commits after `b6ce6d26` and five
have none. Related: DT-11.

### DT-13 — The barrier's support defers to execution owners the tree does not contain

[Collect, release and advance](../docs/REQUEST.md#contract-actors-phase-order)
states "Close the active phase's eligible prediction collection before
releasing its actions". Its first support paragraph (REQUEST line 1040; authored
at [13-actors.surface.md](../docs/contract/13-actors.surface.md) lines 232–239)
is source-read, cites one symbol, `eligibleOrderedStep` in
`PWRunnerStepEvidence.swift`, and ends: "Integrated collection/release and
mutation observations retain their own execution owners." The second (REQUEST
line 1043) is check-read over `runActorSchedulerTests` and ends: "The
collection/release eligibility and native mutation observations retain their
separate owners." The support for
[Establish query order](../docs/RESPONSE.md#contract-steps-assessment-order)
(RESPONSE line 1157) is check-read over `runOrderingTests` and says "no new
execution or mutation-control run is credited."

Source inspection: no owner in any surface cites
`tests/suites/witness_contract/opt_in/mutations.sh`, the case
`order_barrier_mutations`, or any other integrated ordering case. The strings
`order_barrier` and `barrier` do not occur in CONTRACT. The root
[AGENTS.md](../AGENTS.md) line 37, [tests/AGENTS.md](../tests/AGENTS.md) line
64 and [runner/AGENTS.md](../runner/AGENTS.md) line 17 each name that control
as the one to rerun when the worker wait, release store or eligibility rule
changes. The control is cited by [architecture.json](../docs/architecture.json)
(lines 921 and 1841, rendered in ARCHITECTURE rows T8 and B4), which the
statement and its support do not link.

In the other direction, the worker's wait is `wait_for_proceed` in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
line 1205. The changed-item index has 26 rows for that file (CONTRACT lines
1061–1086) and none for that function; the nine rows for `CWorker.swift`
(lines 1386–1394) route only `runCWorker` to this commitment. A reviewer who
starts in CONTRACT from a changed wait or release store therefore reaches no
commitment, and a reader who starts from the commitment reaches eligibility
source and two unit-test entry points. The "execution owners" the limits text
points to are an unknown at that point of the path. This is an observation
about the tracing route; it makes no claim about whether the barrier holds.
Related: DT-06, DT-14, DT-17.

### DT-14 — Surface-level check declarations are not shown and do not match what owners cite

Each surface's root fence declares `checks`, a list of catalog suites; the
[contract README](../docs/contract/README.md), lines 79–81, says "`checks`
names catalog suites". [tree.py](../docs/contract/tree.py), lines 927–935,
verifies only that the list is nonempty and that each name is a suite in the
catalog; line 80 excludes the key from public content, and no renderer reads
it. No suite name from these declarations appears in CONTRACT as a suite.

A read-only script mapped every owner's `check` citation to its suite and
compared the sets per surface (source inspection). Eleven surfaces declare
`failure_boundaries`; no owner in any surface cites a check under
`tests/suites/failure_boundaries/`. `10-request` declares only
`failure_boundaries`, while its owners cite checks in `integration`,
`runner_outcome_bad_request`, `runner_unit`, `source_drift`, `unit` and
`witness_contract`. `13-actors` declares only `failure_boundaries`; its owners
cite `runner_unit`. `32-lifecycle` declares `runner_unit`; its seven owners
are source-read and cite no check.

Two concrete consequences for a reader. The
[Capacity refusal](../docs/RESPONSE.md#contract-refusals-admission) support
(RESPONSE line 617) is check-read over the Swift entry point
`runRequestContractTests`; the suite README for
[failure_boundaries](../tests/suites/failure_boundaries/README.md) describes an
`admission` case that "exercises all twenty capacity checks through the signed
CLI", and CONTRACT offers no route to it. The comparison rules
([Classify an observation](../docs/RESPONSE.md#contract-steps-assessment-observe),
[Submitted operation and target](../docs/RESPONSE.md#contract-steps-assessment-relations))
cite only `runComparisonEvidenceTests`, while the ownership table in
[FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md),
lines 1533–1548, names `witness_contract/comparison_matrix` as their live
owner.

Counts for scale: 152 owners (82 source-read, 61 check-read, 9 executed) cite
checks in 16 files under `tests/suites/`; the catalog holds 283 cases in 42
suites. CONTRACT's introduction describes source and interface associations as
partial; it makes no corresponding statement about check associations. Limit:
whether `failure_boundaries` in fact exercises each of the eleven declaring
surfaces was not examined. Related: DT-13, DT-15.

### DT-15 — A second contract document is outside every CONTRACT path, and one restated row differs from the source

[tests/FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
(1,627 lines, titled "Failure evidence contract") "specifies host
observations, diagnostic preservation and derived comparisons". The working
guidance sends readers to it: [tests/AGENTS.md](../tests/AGENTS.md) lines
14–18 for evidence assertions and [runner/AGENTS.md](../runner/AGENTS.md)
lines 26–28 as the document that "assigns claim ownership to the observations
and readers". ARCHITECTURE links it five times and WORKER three. CONTRACT,
REQUEST, RESPONSE, CONTROLLER and the user guide do not link it at all (source
inspection by search). A reader who follows CONTRACT to a returned record is
not told that a second document restates that record's rules and holds its
ownership table.

The comparison section defers to RESPONSE for definitions and calls its table
"the working summary for test authors" (lines 1202–1207). Its
`operation_relation` row (line 1224) gives `different` "when it is another
operation" and `unresolved` "for compound `file`/`create` or
`file`/`create_fresh`, or an unsupported attempt".
[CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift),
lines 139–145, also selects `unresolved` when the query operation contains `*`
and is not the exact `process-exec*` match.

Reproduced with the signed app: a two-step ordinary specimen under
`(version 1) (allow default)`, both steps attempting `file`/`open_read` on
`/etc/hosts`, one querying `file-read*` and one `file-read-metadata`, returned
`operation_relation: "unresolved"` for the wildcard query and `"different"`
for the other (`normalized_outcome: finished`, exit 0). The failure contract's
row predicts `different` for the first.

In RESPONSE the same case is stated, in two places that differ. The rule text
at line 1202 says "Other wildcard query spellings have an unresolved operation
relation." The field meaning at line 1024 says "`unresolved` means the mapping
cannot assign a single operation", which does not describe the wildcard query:
the mapping assigns `file-read-data` to `open_read`. Limit: only this row of
the failure contract was compared with source; the rest of that document was
not checked row by row. Related: DT-14.

### DT-16 — BUILD commitment lists name equipment commitments in sections that do not discuss them

[presentation.json](../docs/contract/presentation.json), lines 509–533, attaches
`equipment.manifest` and `equipment.binding` to BUILD's
[signing section](../docs/BUILD.md#the-signing-contract) and `identity.build`,
`equipment.inventory` and `equipment.manifest` to
[the evidence section](../docs/BUILD.md#the-evidence-the-build-embeds). The
generated lists (BUILD lines 1030–1035 and 1097–1103) open with "Commitments
explained here".

Source inspection: `equipment.manifest` is the service-sealed
`worker-equipment.json`; `equipment.binding` and `equipment.inventory` are
records the host produces at run time. The string `worker-equipment` does not
occur in BUILD. The word "equipment" occurs in three generated table rows (the
`sign_services` step at line 167, the `equipment_inventory_failed` refusal at
line 697 and the `inv_equipment` invocation at line 1180), none inside either
section's prose. In the signing section "inventory" means the signing list and
`EXECUTABLES`; in the evidence section "the manifest" means
`Contents/Resources/Evidence/manifest.json`. A reader arriving from "Sealed
equipment inventory file" finds a different manifest described under the same
word.

The first list (BUILD lines 87–92) attaches `identity.public.derive` to
[Why the build is shaped this way](../docs/BUILD.md#why-the-build-is-shaped-this-way).
That section describes the host/worker source identity and says "identity
checks run before any compile"; it does not mention the public build contract,
`build_contract.py` or `PW_BUILD_CONTRACT`, which BUILD covers in the step
table, the refusal table and the verification section. The README says these
associations are "reviewed navigation, not test coverage". Limit: the lists in
ARCHITECTURE, CONTROLLER and WORKER are covered by other entries below where
they were read; this entry concerns BUILD only.

### DT-17 — Thirty product source files have no row in the changed-item index

A read-only script compared the file paths in
[Follow a changed item](../docs/CONTRACT.md#follow-a-changed-item) (930 rows:
433 source support, 180 authored declaration, 162 imported record declaration,
143 check support, 10 interface association, 2 extracted example) with tracked
`.rs`, `.c`, `.h`, `.swift`, `.sb` and `.sh` files under the build-identity
directories (source inspection). Thirty files have no row:

`controller/interface/cards.rs`, `inventory.rs`;
`controller/src/app_layout.rs`, `bundle.rs`, `digest.rs`, `help.rs`,
`host_facts.rs`, `interface/commands.rs`, `interface/mod.rs`,
`interface/result.rs`, `interface/run_args.rs`, `plist.rs`,
`porcelain_records.rs`, `reply_fixtures.rs`, `run_result.rs`, `sbpl_lex.rs`,
`shape.rs`; `controller/tools/pw_probe_runner/pw_authority_bytes.h`,
`pw_authority_region.h`, `pw_authority_setup.h`, `pw_worker_evidence.h`;
`controller/tools/sb_api_validator/build.sh`;
`runner/Clients/PWRunnerClient/main.swift`; `runner/Services/PWRunner/main.swift`;
`runner/Sources/PWCWorkerShim/PWCWorkerShim.c` and its header;
`runner/Sources/PWRunnerCore/PWPorcelainRecords.swift`, `PWRunnerListener.swift`,
`PWRunnerPathEvidence.swift`, `PWRunnerProfileCapture.swift`.

Some of these hold behavior that public statements describe. The runner
client's `main.swift` selects the client's exit status from the capture's
terminal value, reads the whole request before opening a connection and builds
the `input_read_failed` and `clock_error` local captures.
`PWRunnerPathEvidence.swift` holds the path-observation records and their
`same_as_input` omission. `run_result.rs` is the constructor `run` uses for
its published result. `host_facts.rs` reads the sysctl values the dossier
carries, and `sbpl_lex.rs` is the lexer behind the import scans. Records
declared in these files are reachable by type name through the "imported
record declaration" rows, which carry no path.

CONTRACT's introduction says an absent association is an unknown, so the index
does not claim these files are irrelevant. The observation is the size and
content of the unknown set. Imported Rust records are listed with a `rust.`
prefix and sort after every path row, while Swift and authored records have no
prefix and sort first. Related: DT-06 (which covers the interface sources),
DT-13.

### DT-18 — "as defined below" is an undefined presence phrase, and 28 entries state no presence rule

Sixty-four field entries in REQUEST (50), RESPONSE (11) and ARCHITECTURE (3)
carry the signature phrase `as defined below`, for example
"**`step_id`** (string; as defined below)" at REQUEST line 828.
[record_definitions.py](../docs/contract/record_definitions.py), lines 494–498,
emits it for any field of an input record without a `required_key` fact.
[Reading the notation](../docs/CONTRACT.md#reading-the-notation) defines the
bare type, `T?` and `T ∪ null` and says "Exceptional omission and input
requirements remain explicit"; it does not mention this phrase, nor
`required; may be null`, `omitted when empty` or `present when … has a value`,
which the same function emits. The definition the phrase points to is the
field's own meaning on the same line, not text below it.

A keyword scan of those meanings, with sampled entries then read, found 28
that state no required, optional, omission or null rule (source inspection;
the scan is a heuristic). They include a paired probe's `step_id`,
`sandbox_check` and `attempt` (REQUEST lines 828–830), an attempt's `kind`,
`action` and `target` (lines 918–920), an actor's `actor_id` and `sandbox`,
a phase's `phase_id` and `actions`, the helper policy's `format` and
`sbpl_source`, every field of the sealed equipment inventory and its worker
rows except `contract` and `team_id` (RESPONSE lines 2196–2215), and the
reservation request's three fields (ARCHITECTURE lines 135–137). For these a
reader cannot tell from the entry whether the key may be omitted or null.

The shared rule [Null and omission](../docs/REQUEST.md#contract-request-specimen-nulls)
(REQUEST line 424; authored at
[10-request.surface.md](../docs/contract/10-request.surface.md) line 100)
reads "Treat optional null as absent where decodeIfPresent is used." It
identifies the affected fields by a Swift decoding call, so applying it
requires reading the decoder. Limit: admission behavior for the 28 fields was
not exercised here; entries from the request-side pass below record what
source inspection found for particular fields.

### DT-19 — The user guide describes CONTRACT as the place that defines the fields

[PolicyWitness.md](../docs/PolicyWitness.md), lines 3229–3236, says: "The
release's [developer contract](https://github.com/Protonk/PolicyWitness/blob/v0.3.8/docs/CONTRACT.md)
defines the fields, applicability and obligations behind these surfaces."
`git log -S` dates the sentence to `897be512` (2026-11-11), when CONTRACT held
every statement. In the present tree CONTRACT holds identity, shared
definitions, the stamp table and indexes; field entries and rules are in
REQUEST, RESPONSE and ARCHITECTURE. The guide is also staged as the standalone
`dist/PolicyWitness.md`, where this link is the only route to developer
statements.

The link names `v0.3.8`. Local tags end at `v0.3.7`
(`git tag --list 'v0.3.8'` prints nothing; reproduced), and
[SIGNING](../docs/SIGNING.md) lines 214–224 use `v0.3.8` as the next release in
its example commands. The link was not fetched, so its present state on GitHub
is unknown. The earlier review recorded that the guide's bytes were unchanged
across the reorganization; this entry records what those unchanged bytes now
say about a document whose content moved.

### DT-20 — CONTRACT's known-gap view lists two items; the tours list others about public behavior

[Known gaps](../docs/CONTRACT.md#known-gaps) has two rows, both of kind
`behavior`: the ordinary-build history requirement and termination
cancellation reach. They are the tree's only `gap` nodes (source inspection).

The tours keep their own indexes. ARCHITECTURE line 154: "the terminal reply
flush delay is best effort. A completed specimen can lose its reply if the
host or connection disappears; no result retrieval or safe execution replay is
available." CONTROLLER line 205: "after submission, effects can occur without a
usable reply or public envelope." WORKER line 339: "exec descendants can
outlive later steps and worker exit." ARCHITECTURE's index (line 1186) says
each gap "is stated in full where the promise it limits is stated"; the first
of these sits directly after the generated transport statements, outside the
generated region. No surface contains "retrieval", and the transport rule's
"never replay the specimen" states the client's obligation, not the loss.

CONTRACT's view has no heading text or link indicating that it covers tree
gap nodes only, or that the tours hold further gaps. Whether those tour gaps
belong in the tree is not assessed here.

### DT-21 — Distinct rules share one link text in CONTRACT's indexes

In [Find a commitment](../docs/CONTRACT.md#find-a-commitment) and the
changed-item index, "Termination dependency" labels both
`actors.after_termination` (REQUEST) and `actor_evidence.gate` (RESPONSE). In
[Rule applicability](../docs/CONTRACT.md#rule-applicability) and
[Controller findings](../docs/CONTRACT.md#controller-findings), six titles
each label two different rules: "Worker lifecycle validation", "Ending
mapping", "Supported stop reason", "Host-cleanup attribution", "Copy validated
host conflicts" and "Local lifecycle findings" (the ordinary and per-actor
forms). The rows are distinguishable only by link target. In Evidence support,
36 headings end in "— Support", 22 in "— Disposition support" and 17 in
"— Source support"; each is unique once its subject title is included (source
inspection by script).

The sentence introducing Controller findings says "Each row names the record
members a check reads"; five of its nine rows say "See the linked rule."

### DT-22 — An admitted empty ordinary `step_id` ends the run as `validator_decode_failure`

Three statements say an ordinary plan may use an empty step identifier:
"ordinary plans currently accept a unique empty value"
([REQUEST](../docs/REQUEST.md#contract-probes-step), line 828), "Ordinary-form
action identifiers may be empty" (REQUEST line 1106; authored at
[13-actors.surface.md](../docs/contract/13-actors.surface.md) line 416), and
the guide's "including an empty string when used once"
([PolicyWitness.md](../docs/PolicyWitness.md) lines 236–238). The host's line
admission for validator replies says "Allow/deny require nonempty step_id"
([ARCHITECTURE](../docs/ARCHITECTURE.md#contract-wire-validator-read), line
785), implemented at
[ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift)
lines 537–540. None of the three request-side statements mentions the
interaction.

Reproduced with the signed app: one `probe_plan` step with `step_id: ""`,
query `file-read-data` on path `/etc/hosts`, attempt `open_read` on the same
path, policy `(version 1)(allow default)`. The request was admitted
(`request_failure` null); the process exited 1 with
`normalized_outcome: "validator_decode_failure"` and error "validator
structure failure at byte 0: allow requires step_id". The step retained
`attempt.outcome: "ok"`, `comparison.order: "unestablished"` and a synthetic
query result; the phase's `decode_fault.message` was "allow requires step_id".

The check-read support for the identifier rule (surface lines 418–427) pins
"ordinary meaning admission tests uniqueness without a nonempty condition" and
cites `runReaderCorpusTests`. That check constructs replies and passes them
through `validateForReporting`
([ReaderCorpusTests.swift](../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift)
line 64); it submits no request. The owner's limits text says so ("through
reporting admission; it is constructed reader evidence"). The actor-form
refusal code `empty_step_id` occurs once in the tree, at its producer
([ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift) line 396),
and in no test (source inspection by search). Limits: one specimen; an empty
identifier whose query the planner excludes sends no validator record and was
not run.

### DT-23 — In the actor form a failed validator spawn yields `finished` for an unapplied actor

[RESPONSE](../docs/RESPONSE.md#contract-reply-record) line 424 gives `finished`
as "Execution and required collection completed under the classifier's
conditions" and line 430 gives `validator_spawn_failed` as "Worker
classification succeeded and validator spawn failed." Line 417 says "Actor
orchestration reports each actor and selects an aggregate outcome."

Reproduced with the signed app. Two actor-form specimens differ only in
`sandbox.mode`; each has one actor, one phase, one `read_fresh` probe and
`_test_overrides.validator_executable_path: "/nonexistent/sb_api_validator"`.
With `mode: "unapplied"` the envelope has `result.ok: true`, exit 0,
`normalized_outcome: "finished"`, host `rc` 0. With an applied policy it has
exit 1 and `validator_spawn_failed`. Both carry the same phase evidence:
`collection_status: "collected"`, `validator_disposition: "not_spawned"`, a
`validator_spawn_failure` record, a synthetic query result and
`comparison.order: "unestablished"`. The ordinary form with the same override
also ends `validator_spawn_failed`.

Source inspection:
[ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift)
lines 370–374 classify each phase with the actor's raw output and keep the
result only if its outcome begins with `validator`. `classifyActor` (lines
278–284) substitutes `applied = true` for a declared-unapplied actor in its own
call; the per-phase call does not, so the phase classification for an unapplied
actor does not reach the validator result. No statement or test was found that
says whether the difference is intended. By the same path other validator
outcomes for an unapplied actor's phase would also not be selected; those were
not run. The specimens and envelopes are in the scratch directory named under
coverage.

### DT-24 — Two query-result meanings differ from what the host records

`missing_reason` is stated as "`validator_not_invoked` when collection never
ran" ([RESPONSE](../docs/RESPONSE.md#contract-steps-query), line 963).
[CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift),
lines 50–53, assigns it whenever there is no validator output object. In the
three spawn-failure runs of DT-23 the step carries
`missing_reason: "validator_not_invoked"` while its phase carries
`collection_status: "collected"`, which the phase statement defines as "an
invoked collection even when validator I/O or decoding later fails"
(reproduced). The guide's wording, "no validator process", matches the source.

`pid` is stated as "PID targeted by this phase's validator collection when
worker output supplies it" (line 966). In a two-phase run whose first phase
held one planner-excluded query (a path filter on a nonexistent path), that
step carried `missing_reason: "query_not_requested"` and a `pid`, while its
phase had `collection_status: "not_needed"` and no validator subprocess
(reproduced). The value is the worker PID whenever worker output exists
(source lines 24 and 105–118); the guide says so.

### DT-25 — `target_relation` treats canonically equivalent spellings as the same submitted string

The field meaning says the relation "compares submitted strings" and the rule
says "Target equality compares submitted strings"
([RESPONSE](../docs/RESPONSE.md#contract-steps-comparison), lines 1025 and
1203). Reproduced: a query path ending in the bytes `636166c3a9` and an attempt
target ending in `63616665cc81` (precomposed and decomposed "café") are unequal
as UTF-8 and returned `target_relation: "same_submitted"`.

The comparison is Swift `String ==`
([CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift)
lines 150–156). The unit test comment at
[ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift)
lines 142–145 and the shared question text
([QUESTIONS.md](../docs/QUESTIONS.md) line 41, copied into the guide) state
"canonically equivalent Unicode spellings compare equal"; the complete
statement does not. In the same record family `same_as_input` is stated in
UTF-8 bytes.

### DT-26 — The augment rule names a refusal code the controller does not produce

[REQUEST](../docs/REQUEST.md#contract-policy-augments-resolve) line 785
(authored at [11-policy.surface.md](../docs/contract/11-policy.surface.md) line
152) says "Invalid names produce `invalid_augment_name`."
[augments.rs](../controller/src/augments.rs), lines 238–248, refuses an invalid
name with code `invalid_value`. The string `invalid_augment_name` occurs
otherwise only as the name of an integration test, whose body asserts
`invalid_value` (source inspection by search). The request-side pass ran
`augments: ["../x"]` through the signed app and recorded exit 1, `bad_request`
and `request_failure.code: "invalid_value"` at
`["policy","augments","0"]`; that run was not repeated by the primary review.

### DT-27 — A selector conflict has an undocumented code, and the controller's code list shows one it never emits

Reproduced: a request whose file carries `runner: {"mode":"byoxpc","id":"nope"}`
run with `--runner-mode standard` exits 1 with `bad_request` and
`request_failure: {"code":"conflicting_selector","path":["runner","mode"]}`.
The string `conflicting_selector` occurs in no document under `docs/`, no
surface and not in `controller/README.md`.
[Selector precedence](../docs/REQUEST.md#contract-request-options-precedence)
lists two refusal conditions ("standard mode with an external selector and
byoxpc mode without an ID or service") and does not state this third. Source:
[run_flow.rs](../controller/src/run_flow.rs) lines 481–510.

The controller refusal's `code` field
([RESPONSE](../docs/RESPONSE.md#contract-refusals-controller), line 548)
displays an illustrative list ending in `"admission_refused"`. No non-test
controller source contains that string. Non-test controller code passes these
codes: `invalid_json`, `missing_value`, `type_mismatch`, `missing_field`,
`unsupported_contract`, `unknown_field`, `invalid_value`,
`conflicting_selector`, `augment_unavailable`, `missing_policy_source` (source
inspection; the enumeration is the request-side pass's and was spot-checked).
The field is declared open and illustrative, so no exhaustiveness claim is
broken; the observation is that the displayed example for the controller
record is a host-only code.

### DT-28 — Exit-status statements do not cover two stdout conditions

[Version command](../docs/RESPONSE.md#contract-identity-version-emit) (RESPONSE
line 3500) says the command returns "process exit 0 after successful
rendering, or 2 when envelope rendering returns an error." Reproduced: with a
reader-less stdout pipe, `policy-witness --version` prints a Rust panic
("failed printing to stdout: Broken pipe") and exits 101, while `example`
under the same condition prints "failed to write stdout" and exits 2. The
request-side pass recorded exit 101 for `run` and `sbpl-check` as well; those
were not repeated. No developer document mentions 101.

[10-request.surface.md](../docs/contract/10-request.surface.md) line 194 says
of `example`, "Process exit 0 supplies the complete document", and line 229
says of `test-input`, "Process exit 0 establishes complete publication".
Reproduced: with stdout closed at launch (`>&-`), both commands exit 0. The
cited controls close stderr at launch, not stdout. The caller in this case
closed its own stdout, so the case is an edge of the claim.

### DT-29 — The helper's import inventory cannot show that a nonliteral import was not followed

[Literal import inventory](../docs/RESPONSE.md#contract-policy-imports) (RESPONSE
line 862) says "an unevaluable import argument, unreadable/nonregular file or
invalid UTF-8 scan input records an incomplete inventory." Reproduced with the
shipped `sbpl-check`: a source containing
`(import (string-append "bsd" ".sb"))` returned `normalized_outcome: "ok"`, a
successful compile, and
`import_inventory: {records: [], truncated: false, cycle: null, …}`. The same
source with the literal `(import "bsd.sb")` returned three records. The
record's fields are `records`, `truncated`, `cycle` and
`policy_closure_sha256`; none distinguishes the first result from a source
with no imports. A comment at
[sbpl_imports.rs](../controller/src/sbpl_imports.rs) lines 113–115 notes that
the controller dossier, not the helper, reports `nonliteral_imports`. What the
native compiler imported in the first run was not examined.

### DT-30 — Listed values with no producer, and produced values that are not listed

Source inspection, with one retained envelope:

- Equipment diagnostic `operation`
  ([RESPONSE](../docs/RESPONSE.md#contract-equipment-error) line 2291) lists
  eleven failing boundaries.
  [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift)
  constructs errors with seven: `signing_information`, `worker_signature`,
  `inventory_read`, `inventory_decode`, `worker_path`, `worker_hash`,
  `worker_entitlements`. `service_seal` has no producer; a failed service-seal
  inspection carries the inspection's own error (line 328). `guest_code`,
  `dynamic_validity` and `associated_static_code` are recorded only as native
  observations (lines 263–284). Both readers accept all eleven.
- Transfer `status`
  ([RESPONSE](../docs/RESPONSE.md#contract-extensions-transfer) line 2701) lists
  ten "Host acknowledgement" names. The host assigns seven
  ([AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
  lines 524–604). `host_timeout` and `clock_fault` are written by the worker
  into its own slot
  ([pw_authority_region.h](../controller/tools/pw_probe_runner/pw_authority_region.h)
  lines 44–46 call them "Worker-side outcomes"), and `none` is an initial value
  replaced on every path before the record is produced.
- Worker subprocess `collection_basis` (RESPONSE line 1635) lists
  `unavailable`; the one assignment
  ([ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift) line
  629) selects between the other two.
- Worker subprocess `cleanup_trigger` (RESPONSE line 1633) lists six values.
  The assignment at line 626 falls back to the poll stop reason, and the actor
  scheduler writes its own stop reasons there. A retained actor-form envelope
  (`tests/out/runs/documentation-trace-default/…/actor_compositions/artifacts/gate_cancels_schedule/run.json`,
  local) carries `cleanup_trigger: "schedule_complete"`. The response pass
  tallied six further unlisted values across retained runs; that tally was not
  repeated.
- Host outcome `bad_policy` (RESPONSE line 426) is stated in the present
  tense. [tests/COVERAGE.md](../tests/COVERAGE.md) line 18 calls it a
  "defensive host policy-hash failure" and says "Public admission refuses
  missing source or wrong format as `bad_request` before this boundary." The
  response pass reproduced both refusals.

None of these fields declares a closed vocabulary; each list is prose. The
response pass also reported that `decode_fault.kind` is declared closed and
exhaustive while no reader rejects another value; that was not re-verified.

### DT-31 — Two controller result paths described in statements have no production route

Source inspection of [runner_client.rs](../controller/src/runner_client.rs).
An accepted capture must satisfy "terminal disagrees with host reply capture"
(lines 478–481): a `runner_reply` terminal if and only if host bytes are
present. For present bytes, lines 744–778 either return the typed reply or set
`runner_reply_error`, which `failure()` (lines 623–650) turns into a refusal.
The combination "admitted, no reply" is therefore not produced by
`parse_runner_client_output`. Statements that describe it:
`runner_response_unavailable` "Completion has no host result to supply an
outcome" ([RESPONSE](../docs/RESPONSE.md#contract-envelope-data-select) line
300), "An admitted execution with no host report can still produce the
controller's no-worker assessment" (line 252), the hand-authored line 89, and
the verify rule at line 3808. The interface join lists
`result.admitted_unavailable` among `entries_no_case_reaches`. The unit test
that produces the label injects the pair directly.

Second, [porcelain.rs](../controller/src/porcelain.rs) lines 218–219 return
`UnsupportedContract` from frame decoding when the producer contract differs,
before any typed body exists, so `runner_result` is null for a foreign
producer. [controller/README.md](../controller/README.md) lines 185–190 says
"a decoded reply carrying another producer contract" yields the refusal and
that `runner_result` "holds the decoded record's projection when decoding
succeeded"; the guide (line 1409) says "A decoded but refused producer/context
can remain there". The branch in `run_flow::admit_reply` that would refuse a
typed reply with another contract (lines 343–349) is reached in tests that
inject a typed reply. The label-context half of the guide's sentence is
accurate. Limits: neither path was exercised; other constructors of the
client-run value outside `runner_client.rs` were not searched for.

### DT-32 — Collection-bound support, `result.error` precedence and the label effect

- The [collection-bound rule](../docs/RESPONSE.md#contract-diagnostics-execution-geometry)
  states refusal with `malformed_runner_response`, exit 1 and null diagnostics
  on `run`. Its check-read support
  ([41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
  lines 320–330) cites two tests in `porcelain_admission.rs` that call the
  diagnostics function directly and assert `process_disposition: "withheld"`
  with one `reply_capacity` finding (lines 3188–3197). On `run`, such a reply
  is refused before `complete_execution`
  ([run_flow.rs](../controller/src/run_flow.rs) lines 693–725), so that
  diagnostics value is not published. The controller pass found no test that
  carries an over-capacity reply through `run`; that search was not repeated.
- `result.error` (RESPONSE line 243): "After execution admission, precedence is
  host error, client `stdout_capture_error`, client `stdout_parse_error`, then
  a generic unsuccessful-run message." The controller pass reports that both
  client errors make the capture a refusal, so the middle two tiers cannot
  occur after admission (source inspection by the pass; lines cited were
  `runner_client.rs` 708–726).
- The failed-label effect for `run`
  ([35-profile.surface.md](../docs/contract/35-profile.surface.md) line 334)
  sets outcome and `ok`, uses `withhold(…runner_sandbox_diagnostics)` and omits
  the exit code; the context refusal for the same path
  ([41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md) line
  355) uses `set_value(…exit_code, 1)` and `set_value(…diagnostics, None)`.
  CONTRACT's Controller findings rows inherit the difference. On tool-error
  envelopes the key was present with null (reproduced); a label refusal was not
  produced.

### DT-33 — Dossier fields: which problem is "first", and two null cases

`imports.failure` is the "First collection problem"
([RESPONSE](../docs/RESPONSE.md#contract-dossier-imports) line 3346). Imports
are visited in name order, because the scan collects references in a
`BTreeSet` ([sbpl_lex.rs](../controller/src/sbpl_lex.rs) line 40;
[sbpl_imports.rs](../controller/src/sbpl_imports.rs) lines 313–320). The
controller pass ran a source importing `zz-pw-trace-absent.sb`, `bsd.sb`,
`aa-pw-trace-absent.sb` in that order; its retained envelope shows
`failure: import "aa-pw-trace-absent.sb": not found in search path` while
`result.error` carries the worker's compiler message naming
`zz-pw-trace-absent.sb` (envelope re-read; run not repeated). The statements
do not say what order "first" refers to; the same order decides which cycle or
bound is reported first.

Reproduced on argument errors (all exit 2, `tool_error`):
`run FILE --timeout-ms 0` and `run FILE --runner-mode nope` give
`specimen.request_path: null`; `run FILE --bogus` and `run FILE extra.json`
give the path. The guide says "`request_path`: the path given to `run`, or
null when no path was given" (line 1964). In all four,
`specimen.app_provenance` is null although nothing attempted to read the
manifest; the field is stated as "null when its read or supported-schema parse
failed" (RESPONSE line 3290). A malformed request file (exit 1, `bad_request`)
carried both.

### DT-34 — Installation: ownership classification, recovery wording and signing

Source inspection; no install, validate or remove command was run.

- [runner_commands.rs](../controller/src/runner_commands.rs) lines 379–385
  insert `XPC_SERVICE_PATH` only when the caller's `--env` did not supply it.
  [runner_manager.rs](../controller/src/runner_manager.rs) lines 1395–1408
  classify a plist `unowned` unless that variable equals the recorded bundle
  path. The statements say install "defaults XPC_SERVICE_PATH to the bundle"
  and that ownership requires a "matching … XPC_SERVICE_PATH"
  ([50-installation.surface.md](../docs/contract/50-installation.surface.md)
  lines 85 and 202); neither says that a caller-supplied value makes the later
  classification `unowned`. The controller pass reports that removal then
  refuses and retains cleanup; that consequence was not traced by the primary
  review, and launchd's behavior with a differing value was not examined.
- The same function returns `unowned` for a present non-regular path and
  `unknown` for a regular file whose conversion failed (lines 1386–1391). The
  statement gives `unknown` only for unknown presence (surface line 207).
- [limits.json](../docs/limits.json), rendered at
  [LIMITS](../docs/LIMITS.md) line 145 and in the guide, says "a later `runner
  remove` or `runner reconcile` continues recovery."
  [controller/README.md](../controller/README.md) lines 340–345 says "Reconcile
  is report-only … makes no machine changes", the rule says "Leave installation
  resources and registry records as observed", and `cmd_runner_reconcile`
  contains no registry save, lock or removal call.
- The statement says install "signs the selected worker and host with the
  supplied entitlements" (surface line 70), which the code does
  (`sign(bundle, identity, entitlements)`). `controller/README.md` line 288 and
  the guide (lines 3058–3060) describe the entitlements only on the worker and
  the bundle as sealed.

### DT-35 — Runner-command success label and refusal form are not in the installation statements

Reproduced: `runner list` and `runner reconcile` return
`result.normalized_outcome: "ok"` with exit 0, and `policy-witness runner`
with no subcommand prints usage on stderr and exits 2 with no envelope. The
controller pass reports the same `ok` label for status, install, validate and
remove, and that every refusal other than `not_found` returns one stderr line
and exit 2 ([cli.rs](../controller/src/cli.rs) lines 64–70); those were read,
not run. Within the installation statements `normalized_outcome` is stated
only for `not_found` and verify; the guide (lines 3224–3227) does state the
stderr-only form. Exit 2 is therefore shared by an enveloped `not_found` and
unenveloped refusals.

### DT-36 — `ownership_lost` is selected only after the failed actor was reaped

[Collect, release and advance](../docs/REQUEST.md#contract-actors-phase-order)
says "a wait error cancels for lost ownership".
[ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift)
lines 472–480 select `unresolved_termination` whenever the failed actor's
quiescence is not `reaped`, and reach the `wait_error` → `ownership_lost`
branch only otherwise. An `ECHILD` wait error marks the child unavailable
([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) lines
1098–1112), after which no further wait or signal is issued and quiescence
stays `unresolved`. The scheduler test titled "lost ownership cancels later
activations and never invents confirmed cleanup" injects `ECHILD` and asserts
`quiescence == "unresolved"` and `cancelled != nil`, without naming the label
(lines 380–406).

The statement's preceding sentence ("unresolved termination cancels the
remaining schedule") is consistent with this if the sentences are read in
order. The observation is that the case in which ownership is actually lost
reports `unresolved_termination`, and that no test asserting
`ownership_lost` as a schedule cancellation was found. Source inspection; not
executed. This is the wait-error counterpart of DT-10.

### DT-37 — Smaller differences between a statement and its source or neighbor

- Validator batch errors: "Parse errors use `parse_error`; an unsupported
  filter uses `bad_filter`"
  ([ARCHITECTURE](../docs/ARCHITECTURE.md#contract-wire-validator-emit) line
  778). Reproduced on the shipped validator: a line with `filter_type: "BOGUS"`
  and no `filter_value` returns `parse_error` ("filter_value required for
  non-NONE filter_type"); the same line with a value returns `bad_filter`. The
  value-presence check precedes filter-name resolution.
- Granted lease: the typed condition bounds `control.lease_ms` by the 5,000 ms
  limit (ARCHITECTURE line 99). The client requires
  `lease <= requestedLease`, where the requested lease is the smaller of that
  limit and the remaining allowance
  ([PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
  lines 142 and 232). The field text and the rule's free effect state the
  stricter form.
- Retry delay: the statement says retries "wait up to 100 milliseconds"
  (ARCHITECTURE line 86); the limits account says "Minimum delay … Fixed
  minimum" ([LIMITS](../docs/LIMITS.md) line 153). The source schedules
  `min(retryDelay, remaining)`.
- [Excluded prediction pairs](../docs/REQUEST.md#contract-probes-query-excluded)
  renders the exclusion set as "Requires ((…) or (…))", the phrasing the
  adjacent admission rows use for requirements. A query matching a pair is
  planned without a validator probe, not refused.
- Duplicate query keys: the validator subject's support says "Duplicate
  query-key behavior is source-read"
  ([21-wire.surface.md](../docs/contract/21-wire.surface.md) line 235), while
  the child definition's support is check-read on `batch_ndjson_roundtrip` and
  says both member orders are "checked against independently selected final
  strings" (lines 211–220).
- The request-side pass reported that `sandbox_check.filter.kind`,
  `attempt.kind`, `attempt.action` and `policy.format` state their vocabulary
  refusal without the byte limit whose capacity refusal precedes it, and
  reproduced `admission_refused` for a 128-byte filter kind and a 64-byte
  format. Those runs were not repeated.

### DT-38 — Check-read support whose cited check does not assert the pinned claim

Check reading by the response pass, with the cited lines confirmed:

- [Assemble the two channels](../docs/RESPONSE.md#contract-steps-assessment-assembly):
  pins "Completed, incomplete, absent and unsupported slots map to distinct
  provenance and outcomes". The cited
  `AttemptOutcomeMappingTests.swift` contains no occurrence of
  `result_source`, `missing_reason` or the cited source function
  `buildStepResults`.
- [Submitted operation and target](../docs/RESPONSE.md#contract-steps-assessment-relations):
  pins "The scenario matrix checks mapped operations, submitted relations,
  order and limitation values". In
  [ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift)
  lines 73–83 the `order` argument is read from the fixture row and passed
  through, and the lifecycle limitation is appended by the test helper before
  comparison.
- [Publish a report or fallback](../docs/RESPONSE.md#contract-reply-failure-publish):
  pins "Independent minimal/empty paths are read in source", while the cited
  `ReplyFailureTests.swift` has cases titled "independent minimal binary
  report survives repeated rich writer failure" and "minimal emission failure
  returns an undecodable empty receipt". Here the support understates its
  check.

The response pass also reported that the support for "A timeout followed by
cleanup" pins "later source reap and unchanged timeout" while the cited test
asserts one timeout value twice and does not order the reap; that was not
re-verified. See also DT-22 and DT-32 for the same pattern, and DT-04.

### DT-39 — Hand-authored prose that differs from the statement or the source

- [EXTENSIONS.md](../docs/EXTENSIONS.md) lines 79–81, copied into the guide:
  the recipient "consumes only in a later visit of its own". The complete
  statement permits a consume later in the same phase for a self-transfer
  (`q == p and b < a`). The protocol pass ran a single-actor, single-phase
  issue/transfer/consume/release and recorded exit 0, `finished`, and all four
  events in phase `p1` with the consume `returned` (envelope re-read; run not
  repeated).
- [runner/README.md](../runner/README.md) lines 127–128: "every actor's region
  and authority region exist before the first launch". Authority regions and
  custody are created first
  ([ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift)
  lines 206–219); each actor's evidence region is created in
  `ActorSession.init`, constructed per actor inside the launch loop (line 234).
- [controller/README.md](../controller/README.md) lines 232–235 names
  `execution_envelope` as the assembler; that function is defined only inside
  `#[cfg(test)] mod tests` in `run_flow.rs` (line 793).
- [WORKER.md](../docs/WORKER.md) lines 142–143: "the host closes its readiness
  reader after the wait".
  [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift) lines
  446–450 keep the read end when the ready byte was received.
- The guide (line 1691) describes the owned-reap record "with an optional
  capture ordinal"; RESPONSE line 1981 gives `capture_ordinal` as a required
  integer.
- The guide (line 921) quotes the unknown-augment error with single quotes
  around the name; the source formats the name with Rust debug quoting.
- [ARCHITECTURE](../docs/ARCHITECTURE.md) line 258 links `runActors` to
  `CWorkerOrchestrator.swift`, which calls it; the definition is in
  `ActorOrchestration.swift` line 17.

### DT-40 — Index structure: no surface rows, call-site citations and split spellings

- [Find a commitment](../docs/CONTRACT.md#find-a-commitment) has 180 rows, all
  of the form `surface.subject`. The presentation map routes 199 nodes, 19 of
  them surfaces. The introduction says "The commitment index covers every
  routing unit." Of the 930 changed-item rows, 105 give a surface root as the
  candidate commitment (for example "Delivery to the host",
  `RESPONSE.md#contract-transport`), which has no index row (counted by
  script).
- Surface-scoped owners send implementing symbols to the surface root instead
  of the rule they implement. Examples from the passes: `PWRunnerAdmission`,
  `reserveRunner` and `PWRunnerClientSession` land on
  `RESPONSE.md#contract-transport`, while the rules they implement are
  rendered in ARCHITECTURE; `remove_record`, `install_record` and
  `save_registry` land on "Managing runners".
- Some citations name a file that only imports and calls the symbol:
  `run_flow.rs: validate_request_contract` (defined in `request_patch.rs`),
  `run_flow.rs: strip_runner_selector` (defined in `runner_select.rs`),
  `ActorOrchestration.swift: actorApplicationAssessment` (defined in
  `PWRunnerAuthoritySetup.swift` line 109) and
  `ActorOrchestration.swift: PWRunnerTransferRecord` (declared in
  `PWRunnerActors.swift` line 221). The citation check is substring presence
  ([generator_common.py](../docs/generator_common.py) line 116), so these
  pass. `porcelain.rs: pub fn decode` matches three definitions (lines 32, 155
  and 174).
- One symbol can appear under two spellings in separate rows: `compare` and
  `fn compare` (CONTRACT lines 867–868), `gates` and `fn gates`,
  `admission_problem` and `pub(crate) fn admission_problem`. Two different
  functions named `admit_reply` (`run_flow.rs` and `porcelain_admission.rs`)
  are both indexed under that name.
- The passes listed further implementing symbols with no row, among them
  `workerAdmissionFailure` (capacity bounds), `planValidatorQueries`,
  `classifyActor`, `launchAndSetUp`, `collectOutput`,
  `classify_service_output`, `sign_install_tree`, `cmd_runner_remove`, and the
  interface entries `result.admission_refusal`, `result.admitted_unavailable`
  and the `@request_selector` runner kinds. No limit identifier or
  `docs/limits.json` row exists, though statements embed `limit(…)` values.
  The lists were spot-checked, not re-derived.

Related: DT-06, DT-13, DT-17.

### DT-41 — WORKER and CONTROLLER commitment lists

- WORKER's "Starting authority and ambient context" list (lines 276–283) names
  `actors.sandbox`. A search of that section (lines 176–275) for "unapplied",
  "apply" or the actor policy returns one line, about sleep overrides; the
  apply/unapplied discussion is elsewhere in WORKER.
- CONTROLLER's "Selecting and directing the apparatus" list names
  `equipment.binding`, while its prose (lines 160–162) describes host binding
  as a separate obligation. "Receiving and evaluating evidence" explains
  collection bounds, the label check and reply-wide findings in prose; its list
  (lines 289–298) does not include `diagnostics.execution`,
  `diagnostics.issue` or `profile.receipt.labels`, and does include
  `steps.assessment.fresh`, a worker rule. Its "preparation" prose (lines
  108–120) explains selection-versus-augmentation failure order and the held
  request; `request.options.failure_order`, `request.specimen.hold`,
  `policy.augments.actors` and `refusals.controller.consequence` appear in no
  tour list.

Source inspection by the passes, with the WORKER and presentation-map parts
confirmed. The README calls these lists reviewed navigation and does not claim
completeness. Related: DT-16.

### DT-42 — Fallback capture: the actor-form whole-request check and the unavailable path

Partly reproduced. The shipped `sbpl-check`, given a request with `actors` and
no top-level `policy`, prints "failed to parse request.json: missing field
`policy`" and exits 2 with empty stdout. `run_flow.rs` passes the held whole
request to the fallback helper without a form condition (lines 699 and
716–719), and [policy_check.rs](../controller/src/policy_check.rs) lines 86–91
classify absent parsed output as `tool_error`.
[controller/README.md](../controller/README.md) lines 5–8 says fallback "checks
the held whole request and each carried actor policy object". If this reading
is right, `data.policy_check.status` is `tool_error` for every eligible
actor-form fallback; the `policy_check` field statement (RESPONSE line 254)
does not say so. Unresolved: an actor-form run ending in an eligible client
`xpc_error` would settle it, and none could be forced here because XPC lookup
worked.

The request-side pass also reported, by source inspection, that on the
`unavailable` path the capture's `stderr` holds the controller's own launch or
delivery error text and `tool_exit_code` is the constant 1, also used when the
helper has no exit code. Not re-verified.

### DT-43 — Lifecycle rendering and resolution details

- Actor-form dispositions are resolved with `plan: nil`
  ([ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift)
  line 307), while the rule says each question is resolved from "the owning
  worker's acquired output, unique slot identities and submitted plan". The
  response pass reports that `attempt_support` is then `supported` for every
  slot, including extension actions, and cites a retained envelope; the
  retained envelope was not re-read.
- [Lifecycle answer value](../docs/RESPONSE.md#contract-lifecycle-claim_value)
  renders a table of alternatives labeled `Integer` and `Request`. The pass
  cites retained envelopes where the JSON is a bare integer or a bare request
  object; the labels are not keys.
- The lifecycle surface's support paragraph (RESPONSE line 1610) says "explicit
  rule and evidence gaps preserve scope"; the surface declares no gap node
  (counted).

### DT-44 — Reported by a pass and not re-verified

These were reported with locations by one of the four sub-agent passes. The
primary review confirmed only that the cited statement text exists. They are
recorded as unresolved so that they are not lost.

- `PWHostWait.stop`: the stated meaning of `clock_unavailable` ("failed or
  backward time with bounded sleep fallback") is reported to match no
  producer; waits with a sleep fallback keep their stop string and set
  `clock_fault`. `setup_failed` is reported to have a second producer (custody
  setup failure). Stop strings `all_resolved`, `equipment_inspection_failed`,
  `dependency_failed` and `schedule_complete` are reported as emitted and
  undocumented. (RESPONSE lines 1706–1710; `ActorScheduler.swift` lines
  212–217 and 518–532.)
- `schedule.cancelled` is reported to carry `unresolved_termination`,
  `actor_quiescence_unresolved` and `equipment_execution_<reason>`, none
  documented; `setup_status: "setup_timeout"` is reported for an actor that
  was never spawned. (RESPONSE lines 1320 and 1498.)
- `PWWorkerProgress.index` attributes the wait index to "actor waits"; the
  ordinary-form release wait is reported to publish it too. (RESPONSE line
  1783.)
- `not_reached` is stated to require "an incomplete slot"; the resolver is
  reported to accept any non-completed slot, including `absent`. (RESPONSE
  lines 1850–1851.)
- Validator collection is reported able to record
  `stdout_collection_stop: "eof"` beside deadline-expiry read-error text
  (`ValidatorClient.swift` lines 284–291). A fixture validator that closes
  stdout and holds stdin until the deadline would settle reachability.
- The guide's `runner_timeout` wording ("a host execution allowance expired")
  is reported not to cover actor schedule-allowance expiry, which yields
  `runner_failed`. No seam shortens that allowance, so it was not run.
- `actor_unavailable` is named in EXTENSIONS line 126 and the guide as how
  visits read; no reply field is reported to carry it.
- `policy_format: "unknown"` is stated for decode refusal and is reported to
  occur on capacity refusal as well.
- `arrival_observed` and `completion_observed` are reported to be sampled at
  different points in the ordinary and actor forms under one field text.
- `runner validate` is reported to persist an inferred `kind`, the current
  equipment inventory and the unentitled worker hash, which the "Refresh
  validation metadata" rule does not name.
- Response vocabularies list values that only an unmapped attempt or unknown
  filter kind produces (`attempt.outcome: unsupported`,
  `attempt:unsupported`, `query_plan:unrecognized_filter_kind`,
  `attempt_support: "unsupported"`), and both request forms refuse those
  inputs before any child. REQUEST lines 300–309 say the handling is
  defensive; the RESPONSE entries that enumerate the values do not. The pass
  reproduced the two refusals.
- Adjacent lifecycle statements are reported to describe the readiness result
  and the policy receipt's two counts differently from each other (RESPONSE
  lines 1769 and 1805–1807; 1827 and 1829).
- A reply with outcome `runner_reporting_failed` and no `reporting_failure`
  record receives a `reporting_failure` finding
  (`porcelain_admission.rs` lines 1470–1476, confirmed), while the family table
  describes that family as applying to "A reply carrying reporting_failure".

## Coverage and limits of the CONTRACT tracing investigation

**What was traced.** The primary review read CONTRACT in full for structure
and its identity, definitions and index sections in detail; compared the
identity statements with `build_contract.py`, `source_identity.py`,
`generate_worker_identity.py`, the worker bootstrap check and the pre-sign
guard, and found them consistent apart from DT-08; classified all 526 owner
citations for definition-like occurrence; checked 2,033 `contract-…` anchor
links across tracked files (all resolve; the 19 exceptions are test fixture
strings); checked that the 130 rules in Rule applicability state entry,
recipient and report; ran `generate_contract_stamps.py --check` and
`--check --require-history` (both report current); and compared the keys of
two real envelopes from the signed app with the rendered signatures of about
twenty record types (all agree, including the stated `same_as_input`
omission).

Four sub-agent passes each traced one family against source and checks:
request, policy, probes and refusals; actors, extensions, transport and wire;
reply, steps, lifecycle and actor evidence; envelope, diagnostics, dossier,
installation, equipment and profile. Each returned findings and a list of
what it traced and found consistent. The primary review re-read the cited
statement and source for every item recorded in DT-22 through DT-43 and
repeated the reproductions it labels "reproduced". Items it did not re-verify
are labeled where they appear or collected in DT-44.

**Statements traced and found consistent** (by the passes, clause by clause,
except as recorded above): request admission order, nulls for the decoders
read, capacity conditions and their limit values, overrides, policy
parameters, helper admission and verdict cases, query eligibility and the
excluded pairs; actor normalization, phase order, extension references,
capacity and custody rules; transport authorization, acquisition, control
admission, invocation and deadline; the validator line grammar and direct
commands; frame headers and budgets; the comparison classification order and
relation table, the order rule, both fresh-descriptor aggregates and path
observations; result selection and its classification table, the collection
bounds and their limit values, ending mapping and cleanup attribution, the
service-ownership classification, and the label check.

**Not reached.** Authority-setup records and `decodeAuthoritySetup`; the host
profile-capture rule against the C headers; `wire.frame.identity` and
projection against `generate_porcelain.py`; `envelope.helper`; the Python
retained-byte reader; `bundle.rs` and runner selection logic; the worker's
`wait_for_proceed` and `wait_for_activation` bodies; most of
[tests/FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
beyond one row; the guide beyond passages a trace led to; `public.json` and
the shape goldens. No `runner install`, `verify`, `validate`, `remove` or
`status` was run, and no BYOXPC run. Transport timeouts, occupied or expired
reservations, clock faults, wait errors, custody failures and schedule
allowance expiry were read in source and not exercised.

**Evidence limits.** Reproductions used the app built from `8b5de2b2` on this
machine (macOS 26, arm64) with XPC lookup available; each is one or a few
specimens and is not a statement about every input. No build and no
`tests/run.sh` case was run, so nothing here is a test result. Local runs
under `tests/out/runs/` were read as retained output and are subject to
pruning. Reproduction inputs and envelopes are under the session scratch
directory
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/1b7c19fb-c395-4c94-9f87-0906550f66e3/scratchpad/`
(`main/`, `request-side/`, `protocols/`, `response-evidence/`,
`controller-side/`), which a reboot or cleanup can remove; nothing there is
retained evidence. Unreachability claims (DT-30, DT-31, DT-32) rest on reading
the production paths named and could be wrong about a path not read. Counts
produced by scripts are stated with what was counted; heuristic scans are
labeled as such. The entries carry no judgment about which layer should
change, and no fix accompanies this record.
