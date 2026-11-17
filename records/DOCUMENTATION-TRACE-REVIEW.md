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

### DT-12 — Historical execution counts accompany links to the current, larger corpus

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
`tests/suites/witness_contract/opt_in/mutations.sh` or the case
`order_barrier_mutations`. CONTRACT contains no reference to that case. The root
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
(lines 1386–1394) route only `runCWorker` to this commitment. The index therefore
offers broader file and driver associations, but no row for the worker wait
itself. From the commitment, the cited support reaches eligibility and driver
sources and unit-test entry points; it does not identify the integrated
execution owners its limits text refers to. ARCHITECTURE supplies an indirect
route to the mutation control. This observation concerns those missing direct
associations, not whether the barrier holds. Related: DT-06, DT-14, DT-17.

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

### DT-15 — The failure evidence contract lacks direct links from the reading paths and differs on one row

[tests/FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
(1,627 lines, titled "Failure evidence contract") "specifies host
observations, diagnostic preservation and derived comparisons". The working
guidance sends readers to it: [tests/AGENTS.md](../tests/AGENTS.md) lines
14–18 for evidence assertions and [runner/AGENTS.md](../runner/AGENTS.md)
lines 26–28 as the document that "assigns claim ownership to the observations
and readers". ARCHITECTURE links it five times and WORKER three. CONTRACT,
REQUEST, RESPONSE, CONTROLLER and the user guide have no direct link to it
(source inspection by search). It remains reachable through ARCHITECTURE.
The complete returned-record statements in RESPONSE do not link readers to
this second account of their rules and test ownership.

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

### DT-28 — Publication commands under a broken pipe and stdout closed at launch

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
cited controls close stderr at launch, not stdout. This observation records
the launch condition and exit status; the descriptor's state at the time of
publication was not inspected. It does not establish a failed write reported
as successful publication.

### DT-29 — The helper's import inventory has no explicit nonliteral-import incompleteness signal

[Literal import inventory](../docs/RESPONSE.md#contract-policy-imports) (RESPONSE
line 862) says "an unevaluable import argument, unreadable/nonregular file or
invalid UTF-8 scan input records an incomplete inventory." Reproduced with the
shipped `sbpl-check`: a source containing
`(import (string-append "bsd" ".sb"))` returned `normalized_outcome: "ok"`, a
successful compile, and
`import_inventory: {records: [], truncated: false, cycle: null, …}`. The same
source with the literal `(import "bsd.sb")` returned three records. The
record's fields are `records`, `truncated`, `cycle` and
`policy_closure_sha256`. The first three carry no indication that a nonliteral
import was encountered. The hash identifies the submitted source bytes and
collected records; it does not expose whether the scan encountered a
nonliteral import. The helper's inventory construction
([sbpl-check.rs](../controller/src/bin/sbpl-check.rs), lines 347–355) omits
the resolver's `nonliteral_imports` flag. A comment at
[sbpl_imports.rs](../controller/src/sbpl_imports.rs) lines 113–115 notes that
the controller dossier, not the helper, reports `nonliteral_imports`. What the
native compiler imported in the first run was not examined.

### DT-30 — Response vocabulary lists differ from the inspected producer assignments

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

### DT-31 — Two documented result paths are not reached through the inspected client-admission path

Source inspection of [runner_client.rs](../controller/src/runner_client.rs)
and [run_flow.rs](../controller/src/run_flow.rs). Client-capture admission
requires a `runner_reply` terminal if and only if host bytes are present
(`runner_client.rs` lines 478–481). An accepted capture can have another
terminal and no host reply. `failure()` then selects a refusal for that
terminal (lines 623–650), and `run_flow::admit_reply` applies it before
execution admission (lines 330–342). For present host bytes, the parser either
returns a typed reply or sets `runner_reply_error` (lines 744–778), which also
produces a refusal. These inspected paths therefore do not produce an
execution-admitted run with no host result. Statements that describe that
state:
`runner_response_unavailable` "Completion has no host result to supply an
outcome" ([RESPONSE](../docs/RESPONSE.md#contract-envelope-data-select) line
300), "An admitted execution with no host report can still produce the
controller's no-worker assessment" (line 252), the hand-authored line 89, and
the verify rule at line 3808. The interface join lists
`result.admitted_unavailable` among `entries_no_case_reaches`. The unit test
that produces the label injects the pair directly.

Second, [porcelain.rs](../controller/src/porcelain.rs) lines 218–219 return
`UnsupportedContract` from frame decoding when the producer contract differs,
before any typed body exists, so `runner_result` is null on that path for a
foreign producer. [controller/README.md](../controller/README.md) lines 185–190
says
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

### DT-38 — Check-read support combines different assertion scopes

Check reading by the response pass, with the cited lines confirmed:

- [Assemble the two channels](../docs/RESPONSE.md#contract-steps-assessment-assembly):
  pins "Completed, incomplete, absent and unsupported slots map to distinct
  provenance and outcomes". The cited
  [AttemptOutcomeMappingTests.swift](../runner/Tests/PWRunnerCoreTests/AttemptOutcomeMappingTests.swift)
  calls `buildAttemptResult` and checks outcome mapping for completed,
  incomplete, missing and unsupported slots, plus preservation of an exec
  child PID. It does not call `buildStepResults` or assert `result_source` or
  `missing_reason`. The support also cites the assembly source; the provenance
  part of the pin is not established by these test assertions.
- [Submitted operation and target](../docs/RESPONSE.md#contract-steps-assessment-relations):
  pins "The scenario matrix checks mapped operations, submitted relations,
  order and limitation values". In
  [ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift)
  lines 73–83 the `order` argument is read from the fixture row and passed
  through, and the lifecycle limitation is appended by the test helper.
  Lines 123–130 explicitly compare the resulting order and limitations with
  fixture expectations. This supports the stated check of values; it does not
  test how production derives order from native observations or whether the
  production step builder appends the lifecycle limitation. The owner labels
  the controls constructed and assigns live scenarios to separate cases.
- [Publish a report or fallback](../docs/RESPONSE.md#contract-reply-failure-publish):
  pins "Independent minimal/empty paths are read in source", while the cited
  [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift)
  has cases titled "independent minimal binary report survives repeated rich
  writer failure" and "minimal emission failure returns an undecodable empty
  receipt". Their bodies assert the minimal frame against a constructed
  expectation after two rich-writer failures, and empty output after a
  controlled minimal-writer failure. The support names only source reading
  for paths these checks also exercise; no execution of those checks is
  credited by this review.

The response pass also reported that the support for "A timeout followed by
cleanup" pins "later source reap and unchanged timeout" while the cited test
asserts one timeout value twice and does not order the reap; that was not
re-verified. Related assertion-scope observations: DT-04, DT-22 and DT-32.

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
what it traced and found consistent. DT-22 through DT-43 distinguish the
primary review's source checks and repeated reproductions from pass
observations it did not re-verify. DT-44 collects further unverified pass
observations.

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
`tests/run.sh` case was run; the manual reproductions supply observations,
not new suite or battery results. Local runs under `tests/out/runs/` were
read as retained output and are subject to
pruning. Reproduction inputs and envelopes are under the session scratch
directory
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/1b7c19fb-c395-4c94-9f87-0906550f66e3/scratchpad/`
(`main/`, `request-side/`, `protocols/`, `response-evidence/`,
`controller-side/`), which a reboot or cleanup can remove. These temporary
outputs have no retention guarantee. Producer and reachability observations
(DT-30, DT-31, DT-32) are limited to the inspected paths. Counts produced by
scripts are stated with what was counted; heuristic scans are
labeled as such. The entries carry no judgment about which layer should
change, and no fix accompanies this record.

## Additional findings: tracing the failure evidence contract

This investigation read [FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
in full and followed selected claims into the C publications, Swift drivers and
assembly, Rust admission/projections, Python readers and test assertions. The
statements were treated as claims to check, including where another document
or a passing assertion describes something different. Entries below are
independent observations, including overlaps with earlier entries; none resolves
which layer should change.

### Investigation identity and reproduction conventions

Source inspection used clean HEAD
`b8df8953fd9d9afc2a9679319a7bd8e6c852280e` on 2026-11-16. Source line numbers
below refer to that snapshot. Manual CLI reproductions used the existing
`dist/PolicyWitness.app`, on macOS 26.7.1 arm64. Its `--version` reported:

```json
{"commit":"8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855",
 "contract":"development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18",
 "describe":"v0.3.7-148-g8b5de2b2","number":"1482","version":"0.3.7"}
```

`git diff --stat 8b5de2b2 HEAD` showed records, retirement of the tracing plan
and its evidence, and a preflight build-refusal script change; no change to
the product sources or the readers used here. This is a source comparison,
not a fresh build or release acceptance. SHA-256 of the inspected executables:

| App-relative executable | SHA-256 |
| --- | --- |
| `Contents/MacOS/policy-witness` | `4bcd308bc323516bfd4008eb7d125e6ffe3167b5b6f53d6a042f112b910b8d28` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner` | `706d9a6c8138677a4a337a77e50d642da46056512bcf29c193cba1bba8745501` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner` | `d6d38f09fa99768a6b1279503e1fb0fa2465bf0b1ab9d8e2120b759620242116` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator` | `ccbf98033321296e7e6e82145fa0f271a6e2161f9c66b56dbf0f9f2304c00890` |

Temporary requests, fixture scripts, direct child output, envelopes and stderr
are in `/private/tmp/pw-failure-trace-elssragi/`. They are local development
observations, outside retained release evidence, and can disappear on cleanup.
The inputs and decisive results below do not depend on keeping that directory.
No registered suite was executed, and no suite pass is claimed. Python reader
probes used `tests/lib/python.sh`, which selected Python 3.14.9 at
`/opt/homebrew/Cellar/python@3.14/3.14.9/bin/python3.14`, with assertions enabled.

The initial baseline command, inside the automation sandbox, ended with
`xpc_acquisition_failed`; its capture recorded `NSCocoaErrorDomain` 4099 and
lookup error 159, `Sandbox restriction`. The same command and input, retried
outside that sandbox with the app unchanged, returned `finished`, exit 0.
The first capture is `baseline.stdout.json`; the retry is
`baseline.unsandboxed.json`. Subsequent live probes ran outside the automation
sandbox. This supports an environmental explanation for that initial lookup
failure only.

Unless an entry specifies otherwise, the reproduction starts with this input
(`CONTRACT` is the exact build contract above):

```json
{"contract":"CONTRACT","specimen_id":"baseline",
 "policy":{"format":"sbpl","sbpl_source":"(version 1)(allow default)"},
 "probe_plan":[{"step_id":"s",
   "sandbox_check":{"operation":"file-read-data",
                    "filter":{"kind":"path","value":"/etc/hosts"}},
   "attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}}]}
```

Each invocation was equivalent to
`dist/PolicyWitness.app/Contents/MacOS/policy-witness run INPUT.json`, capturing
stdout, stderr and exit status separately. The baseline had one completed
worker attempt, an associated native allow record, `query_first`, and valid
disposition diagnostics. Controlled-validator probes add
`_test_overrides.validator_executable_path` naming an executable Python script.
For each stdin JSON line `p`, the script normally prints this JSON record,
flushes, and exits after EOF:

```python
dict(kind="sb_api_validator_verdict", schema_version=1,
     step_id=p["step_id"], operation=p["operation"],
     filter_type=p["filter_type"], filter_value=p.get("filter_value"),
     rc=0, errno=0, outcome="allow")
```

Each entry states its changes to that record. These scripts make no
`sandbox_check` call. They establish handling of controlled transcripts through
the real host, XPC client and controller, alongside a real worker attempt;
they supply no native prediction evidence. Reader mutations described below
are a third category: constructed JSON submitted directly to the named reader,
not a reply emitted by the host.

### DT-45 — The status-word failure promise is contradicted by the current producer and its tests

**Promise.** The failure contract, lines 19–41 and its classification table,
says parameter allocation, setting, the defensive NUL check and compilation
can write `apply_rc=-1`. For a terminal status-word failure without a failure
record, it requires retaining R and nonzero `apply_errno` in `error`, without
calling either an observed library result. The coverage table still describes
`reported_failure_hang` as preserving a published status-word failure.

**Source and assertions inspected.** In
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
lines 1535–1589, those preparation/compile branches publish structured failure
records and call `publish_done_and_exit`; they do not assign `apply_rc`.
The actual application assigns it at lines 1641–1651. In
[ActorSession.collectOutput](../runner/Sources/PWRunnerCore/ActorSession.swift),
lines 639–643, an unapplied worker's `applyRC` comes only from an eligible
native apply-failure record, otherwise zero; `done` does not authorize reading
the scalar. [classify](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift),
lines 351–354, emits the same generic completed-without-application message
regardless of the scalar.

This is explicitly asserted, not merely untested. In
[HostOutcomeClassifierTests.swift](../runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift),
lines 233–247, constructed done/unapplied outputs with `applyRC=-1` and
`applyErrno` 0, 1 or 4567 must have the same diagnostic as zero storage, with
neither `status=-1` nor `apply_errno=`.
[CWorkerLifecycleTests.swift](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift),
lines 414–435, sends the real driver the ABI fixture's
`reported_failure_hang` publication and requires decoded `applyRC=0`,
`applyErrno=0` and no failure record. The fixture writes the scalar; it does
not call the native apply API.

**History and limit.** `0670db1d` (2026-09-18) already contains the retention
promise. `bc3abe2f` (2026-11-06), before the release-stamped contracts, changes
the implementation and assertions to the present behavior. This entry is
source/test inspection; those unit/fixture cases were not rerun here. It does
not claim that an ordinary current worker produces a terminal scalar-only
failure. Related to DT-15's second-contract concern, but a different rule with
explicitly opposing assertions.

### DT-46 — A claimed independent cleanup-trigger observation is derived during final collection

The failure contract's “Raw host facts the record needs,” lines 359–378,
calls `cleanup_trigger` a fact recorded at the exit-request store, “not
conclusions reconstructed from a final status.”
[RESPONSE's field statement](../docs/RESPONSE.md#contract-lifecycle-worker-cleanup_trigger)
also places its recording when exit is requested. The cause table then uses
this field as one witness in the host-cleanup chain.

Source inspection finds a different recording point.
[ActorSession.requestExit](../runner/Sources/PWRunnerCore/ActorSession.swift),
lines 558–562, sets departure/request flags and performs the store, without
saving a trigger. `collectOutput`, line 626, later computes
`PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason`.
[ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift),
lines 549–563, supplies the stop reason before calling `requestExit`.
Thus the two raw fields are projections of one stored reason on these paths;
their agreement is not an independently captured second observation.

The Rust test
`typed_host_cleanup_cause_requires_all_independent_observations`
([porcelain_admission.rs](../controller/src/porcelain_admission.rs), lines
2660–2730) constructs both raw strings and their claims, then asserts cause
selection and withholding when `reaped` changes. It establishes the projection
conditions, not when the production trigger was captured. History search finds
the derived expression already in `0ed4ae7a` (2026-09-27).

No executed case here demonstrated an incorrect trigger value or incorrect
signal attribution. The discrepancy is the described provenance of the value.
Related to DT-30's trigger vocabulary and DT-43's resolution observations;
neither earlier entry examined this recording point.

### DT-47 — Two coverage rows credit encoded facts whose assertions inspect the pre-encoding object

The failure contract's coverage table, lines 676–677, credits the late-done and
post-apply-self-signal `CWorkerTests` with process facts through actual
subprocess encoding. The actual cases still drive a real worker and make
substantive assertions about acquired publications, reap, kill absence and
classification.

Their serialization assertions have a narrower scope. In
[CWorkerTests.swift](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift),
lines 417–425 and 463–470, `decoded` is assigned
`buildWorkerSubprocess(out)`, then `data = try pwPorcelainEncode(decoded)` is
unused. The assertions read `decoded`, not `data` or a reader's projection of
it. A writer that returned successfully while dropping one of those fields
would not be detected by these assertions alone.

`git show 2d5080d7 -- runner/Tests/PWRunnerCoreTests/CWorkerTests.swift`
shows the 2026-11-08 binary migration replacing an encode/decode round trip
with these assignments. This is source/history inspection, not a mutation run.
The separate constructed receipts in
[ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift)
and their independent readers provide other binary coverage; this entry makes
no claim that the writer drops fields or that serialization is wholly untested.
Related to DT-38's distinction between check scopes, with two specific changed
assertion paths identified here.

### DT-48 — A contradictory allow record can yield a clean `finished` run and an “allow” query column

The failure contract says `finished` requires completed evidence collection
(lines 15–18), describes allow/deny as classifications of native returns
(lines 1229–1236), and separately requires coherent returns for `query_first`.
The distinction matters: structural record acceptance and complete ID coverage
do not establish a coherent answer label.

**Executed controlled transcript.** The `incoherent` probe changes the normal
fixture record to `outcome="allow", rc=-1, errno=13`. The CLI exited 0 with
`finished`; the query retained `outcome: allow`, `rc: -1`, `native_rc: -1`,
`errno: 13`, `result_source: validator`. Its attempt completed and its order
was correctly `unestablished`. Controller disposition integrity was `valid`.
Both `consumer.validate(envelope, CONTRACT)` and
`lifecycle_oracle.check_record(envelope, CONTRACT)` returned `[]`.
`consumer.query_column(step)` selects `allow` from those two source/outcome
fields without testing the native return.

**Trace and assertions.** [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift),
lines 526–546, checks required types and fields, not label/return consistency.
[classify](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift), lines
438–461, checks process/transport/association problems, not that consistency.
The ordering gate in
[PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift),
lines 5–8, does check it. The native validator's
[emit_verdict](../controller/tools/sb_api_validator/sb_api_validator.c), lines
403–426, would label this return pair `error`, not `allow`.
[ValidatorEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift),
lines 154–163, explicitly constructs this allow/-1/13 combination and asserts
acceptance and preservation. The checker control `incoherent_native`
([checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py), line
453) changes the native return under a surviving `query_first` claim, so its
rejection does not establish rejection of this unestablished-order case.

The structural acceptance pattern is already present in `6885cb42`
(2026-09-18). The observed gap is between record coverage/labels and their
native meaning, not loss of raw evidence or a false ordering claim. This
fixture did not establish a contradictory native sandbox result.

### DT-49 — A received diagnostic with null `native_rc` need not have the promised `rc=-1`

The failure contract, lines 1111–1115, says a received diagnostic without a
native return retains `native_rc=null` and `rc=-1`. In contrast,
[RESPONSE's `rc` statement](../docs/RESPONSE.md#contract-steps-query-rc) says an
associated record supplies its carried return, with -1 only when that return
is omitted.

**Executed controlled transcript.** The `diagnostic` probe changes the fixture
record to `outcome="future_937", error="constructed diagnostic", rc=17,
errno=5`. The raw phase record retained that unfamiliar outcome and the
numbers. The step projected `outcome: error`, `result_source: validator`,
`native_rc: null`, `rc: 17`, `errno: 5`, with no missing reason. It remained
`finished`, exit 0, order unestablished. Both Python readers returned `[]`.

[CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift),
lines 46–49 and 128–138, independently selects `native_rc` by the original
outcome vocabulary and `rc` by `v.rc ?? -1`. The former excludes `future_937`;
the latter preserves 17. The failure-boundaries diagnostic assertion
([check.py](../tests/suites/failure_boundaries/check.py), lines 346–352) requires
-1 for its fixture, whose diagnostic omits rc. It does not establish the
unqualified null-native-rc rule. The carried-return expression predates the
current contract; it is present in the June 2026 source layout.

This is forwarding/interpretation of a constructed diagnostic, not an observed
native return of 17. Related to DT-24's query-field discrepancies, but concerns
the independent `rc`/`native_rc` selection and a different input.

### DT-50 — Swift and the independent readers disagree on canonically equivalent validator step IDs

The failure contract, lines 605–622 and 1018–1026, says every semantic reader
checks phase ownership/association the same way and that only unique matching
records enter the join. Its “exact” relationship spans different string
equality rules.

**Executed controlled transcript.** The `canonical` request uses step ID
`s-\u00e9`. Its fixture returns that ID normalized to NFD,
`s-e\u0301`, leaving the operation, path and allow/0/0 fields unchanged.
The host retained the decomposed record ID and composed expected ID, reported
`association_issues: []`, and emitted `query_first`. The CLI nevertheless
reported `finished`, exit 0, while Rust diagnostics were
`process_disposition: withheld`, `disposition_integrity: invalid`, with
`phase_collection: validator association issues disagree with records` and
`ordering: query_first lacks eligible prediction and complete ordering chain`.
Python `consumer.validate` rejected both association and order; the lifecycle
oracle reported the phase-collection discrepancy.

**Trace and assertion scope.** Swift's grouping and equality in
[validatorAssociationIssues](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift),
lines 161–185, and `eligibleOrderedStep` use canonically equivalent Swift
String equality. Python's
[phase_evidence.py](../tests/lib/phase_evidence.py), `association_issues` and
`ownership_problem`, groups literal strings; the Rust association/ordering
checks in [porcelain_admission.rs](../controller/src/porcelain_admission.rs)
also distinguish these spellings. The failure-boundaries controls read here
use IDs `first`, `middle`, `last` and assert duplicate/unexpected/query-mismatch
cases. They do not cover this equality boundary.

Related to DT-25, which concerns submitted **target** equality; that reader
has an explicit Unicode-normalization helper. This entry concerns **record
identity**, where readers reach different conclusions. The transcript is
steered; no claim is made that the shipped native validator rewrites an ID
this way. The execution does show a single real host reply receiving opposed
assessments without changing its successful summary.

### DT-51 — An unapplied actor's real validator decode failure also disappears from the aggregate summary

The failure contract, lines 1025–1026, says run-level framing/association gaps
fail the run; lines 1043–1052 assign receiver JSON failures to
`validator_decode_failure`. DT-23 previously reproduced an unapplied actor's
failed validator **spawn** becoming `finished`, and left other validator
failures as a source-level suspicion.

**Executed reproduction.** This pass used one actor `A`, one phase `p`, and
the baseline `s` action, with no top-level policy or probe plan. Actor sandbox
mode was varied between `apply` (the baseline allow-default policy) and
`unapplied`. The executable validator fixture consumed stdin to EOF, then
printed `{not JSON}\n` and exited 0. Both runs carried a collected phase,
a reaped validator, a JSON decode fault at byte 0 with `frame_bytes: 10`,
`retained_bytes: 10`, `context_b64: "e25vdCBKU09OfQ=="`, and a completed `ok`
worker attempt. Applied mode returned exit 1 / `validator_decode_failure`;
unapplied mode returned exit 0 / `finished`, `ok: true`, null result error.
Both full envelopes passed `consumer.validate` and the lifecycle oracle.
Inputs/results are `actor_apply.*` and `actor_unapplied.*` in the common
scratch directory.

The source is the same asymmetry identified by DT-23:
[classifyActor](../runner/Sources/PWRunnerCore/ActorOrchestration.swift), lines
278–284, supplies a declared-setup view to worker classification; the phase
call at lines 370–374 uses raw unapplied output and retains only outcomes
beginning with `validator`. It stops at the worker's absent application before
classifying the decoder result. The record/claim readers do not recompute the
host's aggregate outcome from every retained validator fault.

This standalone finding confirms another reached production boundary behind
the earlier suspicion; it is not a second spawn test or evidence about every
actor schedule. The native query was replaced by malformed fixture output;
host JSON decoding and worker execution were real.

### DT-52 — The independent consumer accepts a missing attempt errno key despite the presence promise

The failure contract, lines 635–637 and 866–867, requires key presence for a
null step errno. The baseline host actually supplies `attempt.errno: null`.
The Python reader does not preserve that distinction when validating a saved
reply.

**Executed constructed control.** Copy the baseline's
`data.runner_result`, delete only `steps[0].attempt.errno`, then call
`consumer.validate(reply, CONTRACT)`. The result was `[]`. The unmodified
bare reply also returned `[]`. Putting the mutated reply into a copy of the
envelope and calling the lifecycle oracle likewise returned `[]`; that oracle
does not validate the client-capture/JSON equality. This is a mutation of a
saved reply, not a host omission or a claim that the intact capture matches it.

[consumer.py](../tests/lib/consumer.py), lines 471–490, uses
`attempt.get('errno') is not None`, which equates absence and null. Its shape
goldens deliberately allow absent keys. In the checker controls, lines
495–504, missing attempt rc and fractional attempt errno are rejected, but
the deletion above is not one of those controls. The same optional-errno
test is already present at `f7bcb493` (2026-10-02).

A companion diagnostic-reply mutation deleting query errno also passed
(its order was already unestablished), whereas deleting query errno from the
ordered baseline was rejected for missing order evidence. Thus rejection in
the latter case establishes an ordering dependency, not a general required-key
check. No product serialization change is inferred from these reader controls.

### DT-53 — Consumer acceptance does not establish completeness or truth of the lifecycle claim record

The failure contract's nesting and witness rules, lines 380–430, require all
seven run questions, matching claim values and resolved sufficient references.
Its reader-responsibility section distinguishes the consumer from the lifecycle
oracle, but `consumer.validate` alone supplies much less lifecycle validation
than its general shape/semantic description might suggest.

**Executed constructed controls.** Starting from the valid baseline bare
reply, each of these independent edits still returned `[]` from
`consumer.validate(reply, CONTRACT)`:

- Delete `runner_subprocess.disposition.questions.final_status`.
- Change only that claim's `value` from 0 to 17, leaving the raw reaped exit
  code at 0.
- Replace that required claim with null.

The lifecycle oracle, given a copy of the baseline envelope with the respective
reply substituted, rejected the first as `D8/malformed_record`,
`record.questions lacks final_status`, and the second as `D1/wrong_answer`,
expected exit code 0 but record says 17. These controls deliberately do not
claim consistency with the original binary capture. The positive unmodified
envelope passed both readers.

**Scope traced.** [consumer._validate_worker](../tests/lib/consumer.py), lines
749–801, requires the disposition object but does not run the claim oracle;
`validate_shape`, lines 322–357, allows missing keys and null at any recorded
path. [lifecycle_adapter.py](../tests/lib/lifecycle_adapter.py), lines 108–118,
and [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py), `_compare_claim`,
own the checks that rejected the mutations. Swift's
[DispositionResolverTests.swift](../runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift),
including “missing run question” at line 345, separately checks producer
rejection. Those paths should not receive credit merely because the full
consumer returned no errors. Related to DT-38's support-scope distinctions;
separate from DT-52's errno rule, which neither Python reader rejected.

### DT-54 — The validator collection-stop list omits a reached byte-limit stop

The failure contract, lines 1126–1133, lists `stdout_collection_stop` as `eof`,
`deadline`, `read_error` or `poll_error`. The current
[RESPONSE field](../docs/RESPONSE.md#contract-lifecycle-validator-stdout_collection_stop)
also lists `clock_error` and `byte_limit`; the guide's validator-storage limit
describes the latter.

**Executed controlled transcript.** The `bytecap` fixture writes the normal
allow record, then 20,000 spaces and LF. With one query, the host retained the
valid record, recorded `stdout_collection_stop: byte_limit`,
`stdout_bytes_received: 20200`, and identical I/O/read diagnostics:
`validator stdout exceeds bounded retention (16384 bytes); received 20200`.
`decode_fault` was null, validator exit code was 0 with confirmed reap, and
the envelope returned `validator_no_reply`, exit 1. The step retained
`query_first`. Both Python readers accepted this envelope.

[ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift),
lines 359–372, records the byte-limit branch before decoding and removes the
cutoff fragment. Lines 278–281 separately produce `clock_error`, not exercised
here. The byte-limit assignment appears in `66d41b5e` (2026-10-12), predating
the release-stamped contract work. This is an incomplete vocabulary account,
not lost partial prediction evidence or a decoder fault. Related to DT-30 and
DT-44's vocabulary observations, with a different field/value and a live host
boundary now reproduced.

### DT-55 — Embedded NUL hides exec output and its truncation marker

The failure contract, lines 1098–1103, promises bounded exec stream text “with
truncation marker.” [The guide](../docs/PolicyWitness.md), line 147, suggests
using a helper's bounded stdout/stderr to report native results and supporting
effects. The stream representation has an additional, unmarked cutoff at NUL.

**Executed native child output.** Replace the baseline action/query with
`exec/spawn` and `process-exec*` on `/usr/bin/printf`. The exact argument arrays
and observations were:

| Args (JSON spelling) | Direct subprocess stdout | PW `attempt.stdout` |
| --- | --- | --- |
| `["HEAD%02048d", "0"]` | 2,052 bytes | 1,023 bytes ending `\n... [truncated]` |
| `["HEAD\\000%02048d", "0"]` | 2,053 bytes, prefix hex `4845414400` | `HEAD`, four bytes, no marker |
| `["HEAD\\000TAIL"]` | Nine bytes, hex `48454144005441494c` | `HEAD`, four bytes, no marker |

Direct controls used Python `subprocess.run` on the same absolute executable
and args and retained its raw stdout. PW runs all returned `finished`, exit 0,
attempt rc 0, child exit code 0, observed leader exit plus both stream EOFs,
no termination request, and successful reap. The NUL envelopes passed both
Python readers. Files are `exec_plain.*`, `exec_nul.*`, `exec_small_nul.*`;
`.direct.stdout` contains the independent child bytes. These controls establish
the behavior of these commands on this build, not the full child transcript
of every execution.

**Trace/history/assertions.** [pw_worker_exec.h](../controller/tools/pw_probe_runner/pw_worker_exec.h),
`drain_one` at lines 171–179, copies bytes including NUL. Lines 379–402 append
an overflow marker by byte offset. [ActorSession.readString](../runner/Sources/PWRunnerCore/ActorSession.swift),
lines 806–813, stops at the first NUL, so even a stored overflow marker later
in the buffer cannot reach JSON. The exec implementation and this decoder
behavior are already in `ae277d0c` (2026-05-31), at the then-current
`runner/CWorker.swift` and worker entry source.
[CWorkerTests.swift](../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift), lines
831–860, checks `/bin/echo` yields `hello world\n`, not NUL handling.
[limits.json](../docs/limits.json), `exec_stream`, explicitly credits small
output tests and source inspection for overflow. No claim is made that the
existing test asserts preservation of binary child output.

### DT-56 — Truncating valid UTF-8 can erase the whole exec stdout field

This is related to DT-55's stream decoder but is a distinct input and failure:
the child emits valid UTF-8 without embedded NUL. The failure contract's
truncation-marker account and the same exec-stream limit apply.

**Executed reproduction with adjacent control.** Use `exec/spawn` and a
`process-exec*` path query for `/usr/bin/awk`, with one argument:

```text
BEGIN {printf "xx";for(i=0;i<2000;i++)printf "é"}
```

The independent direct invocation exited 0 and emitted 4,002 bytes, all valid
UTF-8 (2,002 characters). The PW invocation also exited 0 / `finished`, with
attempt rc 0, child exit 0, `leader_exit_and_eof`, both EOF flags true, no
cleanup request and confirmed reap, but the `stdout` key was **absent**.
Both Python readers returned `[]`. With only the prefix changed from `xx` to
`x`, the direct output was 4,001 bytes and PW retained 1,023 bytes, 520
characters, including the marker. These are `exec_utf8_split.*` and
`exec_utf8.*`, respectively; direct raw outputs were retained separately.

**Source explanation.** The C marker is 16 bytes, placed at byte 1007 in the
1024-byte buffer on overflow. For the `xx` prefix, this cuts a two-byte `é` in
half. `readString` in
[ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift), lines
806–813, uses strict `String(data:encoding:.utf8) ?? ""`; its caller at lines
704–705 converts the empty result to nil. It neither preserves a valid prefix
nor reports that decoding discarded the buffer. The same historical marker
and decoder mechanisms cited in DT-55 predate the failure contract itself.
The inspected small-ASCII assertion and source-only overflow credit do not
establish this boundary's behavior. This execution does not show loss of
process/EOF/reap evidence; it shows loss of the retained textual channel,
including its truncation indication.

### DT-57 — An admitted empty ID with an excluded query succeeds, then fails the lifecycle oracle's ID rule

DT-22 left the empty ordinary step ID with a planner-excluded query untested.
This pass reached that branch. The request-side promise still permits one
unique empty ordinary ID, and the failure contract says disposition entries
join every declared action by identity (lines 187–192).

**Executed production path.** Change the baseline step ID to `""`, and set
both query path and attempt target to the nonexistent
`/private/tmp/pw-failure-trace-elssragi/never-created`. No overrides are used.
The result was exit 0 / `finished`, `query_not_requested`,
`prediction_unavailable`, order unestablished, and a completed worker
`open_failed` result with errno 2. The reply and disposition both retained the
empty step ID, and controller disposition integrity was valid.
`consumer.validate(envelope, CONTRACT)` returned `[]`, but
`lifecycle_oracle.check_record` returned:

```json
{"rule":"D8","kind":"malformed_record","question":null,
 "step_index":null,"detail":"steps[0] lacks a string step_id"}
```

The path remained absent. Input/output are `empty_excluded.*`.
[lifecycle_adapter.py](../tests/lib/lifecycle_adapter.py), lines 132–133,
rejects a falsey string in addition to nonstrings, while
[PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift), lines
300–309, explicitly permits empty ordinary action IDs. The validator's
nonempty-ID receiver gate is bypassed because this query is excluded; the
native attempt and lifecycle publication still run. This confirms a different
reader disagreement from DT-22's validator-frame refusal, and is independent
of DT-50's Unicode-equivalent-ID fixture. It does not show that every empty-ID
specimen fails or that the lifecycle oracle rejected a missing publication.

### DT-58 — The failure contract's “final” minimal report has a further empty-byte fallback

The failure contract's “Reply construction failure,” lines 106–114, says a
second serialization failure produces a minimal `runner_reporting_failed`
reply retaining identity and original summary with `evidence_retained: false`,
and calls this the “final path.” The current
[RESPONSE publication rule](../docs/RESPONSE.md#contract-reply-failure-publish)
describes another branch: failure of the minimal writer returns empty bytes.

**Source and assertions inspected.**
[PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift),
lines 124–154, attempts ordinary and rich reporting, then evaluates
`(try? minimal(result, finalDiagnostic)) ?? Data()`. Empty data carries neither
the original summary nor a reporting-failure object. This does not substitute
the literal JSON object `{}`, which the older wording forbids, but it also
does not supply the promised final structured account.
[ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift),
lines 314–329, injects throwing rich and minimal closures, asserts two rich
calls and one minimal call, and requires `data.isEmpty`. This is an explicit
constructed boundary control, separate from the actual text-cap test at lines
247–311, whose large attempt diagnostic permits the minimal writer to succeed.

The empty-data branch appears in `8bdeec73` (2026-11-08). No encoder failure,
empty reply or native specimen reaching this branch was executed in this
investigation. Its production reachability remains unresolved here; source
and the internal test nevertheless describe a branch absent from the failure
contract's final-path account. Related to DT-15's differing statement owners
and DT-47's serialization evidence scope, without asserting an actual loss in
any live run examined above.

## Coverage and limits of the failure-contract investigation

**Ground covered.** The contract was read end to end. Detailed source traces
covered worker progress/failure/readiness/receipt decoding and publication;
status-word and worker/validator classification; final collection and child
cleanup observations; ordinary and actor phase result assembly; validator
framing, capacity, association and ordering eligibility; service reporting
admission/degradation; Rust lifecycle/phase projections; Python shape,
comparison, phase and lifecycle readers; and exec stream collection and final
decoding. The record cites the assertions inspected, including constructed
classifier and encoder inputs, ABI fixtures, real-worker driver cases and
controlled-validator CLI cases. Selected historical revisions were examined
to establish mechanisms or changes; no past battery was re-credited.

The observed normal baseline preserved its query, completed slot and ordered
comparison through the actual CLI. Controlled invalid/overlarge validator
output retained independent worker results and, where applicable, earlier
accepted records. The tested exec output losses left process observations
intact. The Python oracle caught the two constructed claim-integrity faults
that the consumer accepted. These are affirmative observations within their
specific inputs, not a conclusion that all other promises hold.

**Not established.** This was not exhaustive branch coverage of the 1,627-line
contract or a security audit. Actor authority setup, custody/transfer,
equipment inspection, natural-termination gates, compiled-profile capture,
client reservation/replay and helper fallback received only the context
inspection needed for these traces, not full independent revalidation. No
new native-call substitutions, worker ABI fixtures, clock faults, cleanup
kill/wait faults, mutation battery, signing/build pipeline, BYOXPC installation
or kernel-denial experiment was run. The scalar-only failure and cleanup
recording-point observations remain source/test inspections; no native
specimen establishes an erroneous scalar-only diagnostic or cleanup cause.
The unused encoded-byte assertions were inspected, not tested with a corrupt
writer. Most historical transitions were not bisected or executed.

Live observations apply to the named build, machine and specimens. Controlled
validator outputs are not sandbox verdicts, direct child output controls do
not observe the same individual child process as the PW run, and saved-JSON
mutations are not production reachability evidence. The entries preserve these
distinctions and earlier findings. Only this investigation record was changed;
no implementation, contract, reader, test or generated-document fix accompanies
it.

## Additional findings: authority acquisition and lifetime

This continuation starts from REQUEST, RESPONSE, WORKER, EXTENSIONS and
ARCHITECTURE, including the authored owners in
[14-extensions.surface.md](../docs/contract/14-extensions.surface.md),
[33-actor_evidence.surface.md](../docs/contract/33-actor_evidence.surface.md)
and [34-equipment.surface.md](../docs/contract/34-equipment.surface.md).
The entries distinguish declared resources, worker publications, host
observations, derived records and native file observations. Earlier entries
remain intact; apparent relatives are recorded separately.

### Authority investigation identity and reproduction conventions

Source inspection used initially clean HEAD
`57d2375a1aff0f9b674f4fe8c08071c6765a1cfd` on 2026-11-16. Line numbers below
refer to that snapshot. The existing signed app still reports commit
`8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`, version `0.3.7`, build `1482`,
describe `v0.3.7-148-g8b5de2b2`, contract
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
The comparison from that commit to HEAD changes records, retired tracing
material and the preflight build-refusal script, not the product sources or
readers examined here. This is source correspondence, not a new signed build.
The machine reports macOS `26.7.1`, build `25G241`, arm64. The additional
unentitled worker used here has SHA-256
`ee2a42488009f46581358db3076ec35c7cd013af9e7d800113841db74433312c`.
The other app executable hashes are recorded in the preceding investigation.

Temporary material is under `/private/tmp/pw-authority-trace-3QC3qQ/` and has
no retention guarantee. It includes `probe.py`, requests, raw envelopes,
stderr/process captures, reader variants, `issue_tail.c`, and a copied Swift
package with an investigative `main.swift`. No registered suite was executed
or credited. Live CLI calls and the real-worker host exercise ran under
`tests/lib/checkout_lock.sh` outside the automation sandbox, whose XPC
restriction was established in the preceding investigation. The Python
launcher was `tests/lib/python.sh`, with assertions enabled.

The Swift exercise copied `runner/Sources` and `runner/Package.swift`
unchanged into the temporary package and supplied only its own executable
main. Its command was:

```sh
swift build --jobs 2 --package-path /private/tmp/pw-authority-trace-3QC3qQ/runner \
  --scratch-path /private/tmp/pw-authority-trace-3QC3qQ/swift-build \
  --product PWRunnerCoreTests
```

The first sandboxed build failed opening the compiler module cache with
`Operation not permitted`; the same build outside the sandbox succeeded.
The first custody exercise failed its setup precondition in the sandbox;
the unchanged executable succeeded outside it. That assertion alone did not
identify the rejected native setup call. An intermediate extension of the
main refused the app request because SwiftPM's contract was `unbound`;
setting `JSONDecoder.userInfo[.expectedContract]` to the app contract allowed
the later exercise. These failures are harness observations, not native
authority outcomes.

The final Swift executable SHA-256 is
`de9a40bd29a494a0308fba900bcf0eb87a4953c7fbde7bdb32095057cd16c246`.
It was invoked as `tests/lib/checkout_lock.sh --
/private/tmp/pw-authority-trace-3QC3qQ/swift-build/debug/PWRunnerCoreTests`.
It used Apple Swift `6.4.2` (`swiftlang-6.4.2.1.9`) and the selected macOS
`27.2` SDK. The C exercise used Apple clang `21.0.0`
(`clang-2100.4.1.1`), `-Wall -Wextra -Werror
-Wno-deprecated-declarations -O2 -std=c11 -lsandbox`; its executable SHA-256 is
`65e01aa3e4047032b86974d6b6b88ea0ee86a034eb1f7e1579f259deb99f4283`.
These are temporary investigative builds, not replacement app artifacts.

### DT-59 — Self-transfer consumption can occur in the same visit

**Statement examined.** [EXTENSIONS](../docs/EXTENSIONS.md), lines 79–81,
says the recipient accepts while parked and consumes “only in a later visit
of its own.” The authored
[custody delivery rule](../docs/contract/14-extensions.surface.md), lines
379–391, also describes self-transfer servicing inside the sender's wait,
and requires settlement, commitment and acceptance. REQUEST's reference
rules require prior production in action order, not a different visit.

**Source and assertions.** [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift),
lines 451–497, accumulates resources while walking actions and admits a
self-transfer followed by consumption in the same phase.
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
lines 800–829 and 892–939, services inbound work inside the exchange wait
and then permits consumption of settled bytes. In
[ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift),
lines 421–468, the self-transfer input deliberately puts `a_consume` in
visit 2 after the transfer in visit 0. Its assertions establish that
particular later-visit placement and parked B's lack of completed actions;
they do not establish the word “only.”

**Executed reproduction.** `same_visit/specimen.json` declared one
unapplied, unentitled actor `A`, one phase `one`, and these actions in order:
issue read authority for `/private/tmp/pw-authority-trace-3QC3qQ/target` as
`t`; transfer `t` to `A` as `d`; consume `d` as `h`; `file/read_fresh` of the
target; release `h`. Issue operands were `family:file`, `authority:read`;
the paired read query was `file-read-data` with the identical path filter.
The target contained the 27 bytes `authority lifetime witness\n`.
`policy-witness run INPUT.json` returned exit 0, `finished`; events in the
one phase were issue `returned/1`, transfer `delivered`, consume
`returned/0`, release `returned/0`. The read returned those 27 bytes, device
`16777233`, inode `277408216`, with successful stat and close. The Python
consumer and lifecycle oracle returned `[]`; after return `kill(28752,0)`
reported process absence.

**History and scope.** `git blame` dates the later-visit prose to
`49a14688` (2026-11-05); it is present in `v0.3.5`, before the 0.3.6 contract
release. This run establishes admitted same-visit self-consumption, not
that consuming changed this unapplied actor's access. DT-66 separately
examines native access under an applied policy. This also extends DT-38's
distinction between an exercised arrangement and a broader claim.

### DT-60 — A mismatched raw setup association is flagged but its decision is still projected

**Promise.** The authored equipment rule, lines 880–898 of
[34-equipment.surface.md](../docs/contract/34-equipment.surface.md), and its
[RESPONSE presentation](../docs/RESPONSE.md#contract-equipment-authority_scope-acquire)
say to validate the raw actor/required association before projecting an
observed decision and primary operation. Its support points to
`decodeAuthoritySetup` and the independently published cleanup-cell test.

**Executed constructed input.** The copied production decoder received a
zeroed `PWShmLayout.regionBytes` allocation with valid evidence magic and
ABI identity. Relative to `authoritySetupOffset`, the main set disposition
at `+4` to `1` (ready), required at `+12` to `1`, actor at `+16` to `7`,
and release-stored decision publication `1` at `+0`. No operation cell was
published. It called `decodeAuthoritySetup(raw, actor:0, required:true)`.
Decisive output was:

```text
publication=observed disposition=ready actor_index=0 required=true
operations=0 errors=["setup_association_mismatch"]
```

Changing only raw actor to `0` and raw required to `0` produced the same
projected decision and association error. The public association comes from
the decoder's arguments; the mismatching raw value is not retained.

**Source and downstream limits.** In
[AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift),
line 66 inserts an error but does not gate lines 95–102, which set
`publication` and `disposition` using the expected `required` argument.
This does **not** establish activation of a mismatched worker:
[ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift),
lines 284–288, returns setup failure when integrity errors exist, and
[PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift),
lines 149–151, reports publication integrity. The experiment invokes the
decoder, not that scheduler or final encoder. The worker's production
header checks also reject an initially inconsistent actor association
before setup (`pw_probe_runner.c`, lines 1363–1377).

The cited [test](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift),
lines 155–178, supplies matching actor/required words, an independently
published failing close cell, and then malformed flags. It asserts partial
cell retention and `invalid_setup_cell`, not mismatched decision handling.
The decoder behavior dates to `bc3abe2f` (2026-11-06) and exists in
`v0.3.5`. Related to DT-47's support-scope concern, but about a different
decoder and a directly executed constructed input.

### DT-61 — Setup readiness can be decoded and assessed without its acquisition prerequisites

**Relationship examined.** The
[prepare-before-use rule](../docs/ARCHITECTURE.md#contract-extensions-custody-prepare)
requires core-limit success and required mapping/validation before ready;
the authored equipment condition, lines 912–917, requires observed ready
to imply `required:true`. These are distinct from merely possessing the
string `ready`.

**Executed constructed decoder control.** Repeat DT-60's buffer with raw
actor `0` and required `1`, matching the decoder arguments, but still no
published operation cells. It returned:

```text
publication=observed disposition=ready actor_index=0 required=true
operations=0 errors=[]
ownership: descriptor=not_acquired mapping=not_acquired shared_erasure=not_present
```

The decoder checks an optional primary against a failed cell, but does not
require ready's core-limit, mapping, close or header-binding cells. The C
producer normally publishes those prerequisites first
([pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
lines 676–761). This constructed state is not evidence that its ordinary
setup path skipped acquisition or that a release/acquire operation lost
earlier publications.

**Executed reader controls.** Starting from the real two-actor envelope in
DT-66, independently make each of these changes to the decoded runner body:
remove B's `core_limit` operation; replace that operation with
`state:failed,native_rc:-1,errno:1` while retaining ready and no primary;
set B's `required:false` while retaining ready; or empty
`authority_setup.host.regions`. For each, direct
`actor_evidence.validate_actor_evidence`,
`extension_evidence.validate_actor_extensions` and
`consumer._validate_reply` returned `[]`. `lifecycle_oracle.check_record`
also returned `[]` on the modified envelope. The full consumer **did**
reject each modified envelope with
`host result differs from exact captured host reply bytes`; the captured
wire reply was deliberately left unchanged. These results establish the
body checks' scope, not acceptance of altered bytes through the whole
capture path.

**Source and test limits.** Python
[actor_evidence.py](../tests/lib/actor_evidence.py), lines 39–159,
checks present operation shapes and terminal-failure support. Swift
[PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift),
lines 142–215, and Rust
[porcelain_actor.rs](../controller/src/porcelain_actor.rs), lines 404–468,
likewise check terminal applicability without enforcing ready's
`required:true` relationship or its complete prerequisite prefix. These
Swift/Rust observations are source inspection, not executed mutated-wire
trials. The [actor evidence fixture](../tests/fixtures/contract/actor_evidence.json)
includes wrong associations, wrong kinds, unpublished decisions and
primary/cleanup confusion; those named assertions concern different
relationships. Related to DT-53's distinction between consumer acceptance
and evidence completeness, and separate from DT-60's explicit integrity
error. No production reachability of the contradictory ready states is
claimed.

### DT-62 — Accepted host custody disappears from the reply when the issue slot is unpublished

**Promise and tension.** The authored custody rule, lines 364–375 of
[14-extensions.surface.md](../docs/contract/14-extensions.surface.md), says
the native return and host custody acceptance are reported independently.
The token-status definition at lines 824–834 instead makes missing issue
publication unresolved. The latter is what the assembly preserves, even
when the host has its own accepted-custody observation.

**Executed public reproduction.** Starting from DT-59, retain only its issue
action and add `_test_overrides:{"worker_kill_before_publish_slot":0}`.
The unchanged signed app returned exit 1, `runner_failed`, worker signal 9
and `reaped:true`. Its issue event had `call_boundary_observed:true`,
`result_published:false`, `status:unresolved`, with native result and length
absent. Token `t` was unresolved with no length. Its host custody setup scope
reported successful allocation, `final_erase/performed` for 16,384 bytes and
successful unmap, but no acceptance status or accepted length. The request
and output are `interrupted-specimen.json` and `interrupted-run.json`.

**Independent host-level observation.** The copied Swift package decoded
that same request with the app contract, normalized it, translated it to
the actual signed `pw-probe-runner-unentitled`, and invoked
`ActorScheduler.run` with the translation's authority plan and a no-op
collection hook. It then passed the outcome to `assembleActorReply` with
one empty query plan, nil validator result and `not_needed` collection.
Its output was:

```text
custody=[["accepted", "216", "true"]]
events=[["unresolved", "false", "nil"]]
token=unresolved length=nil quiescence=reaped
```

Here 216 is the host's accepted payload length and true is final erasure.
The native worker was real; this supplementary driver invocation bypassed
the public equipment-binding/live-inspection orchestration and did not
encode/admit a full reply. The separate CLI run above traversed that public
path. Neither run printed or retained bearer bytes.

**Source and assertions.** The worker's test seam kills after the attempt
function returns but before `completed` is stored (`pw_probe_runner.c`,
lines 1090–1097). Issue returns after its custody acknowledgement wait.
[AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift),
lines 455–501, retains accepted length independently;
[ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift),
lines 642–651, correctly withholds unpublished slot payloads. But
[ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift),
lines 462–474, chooses unresolved before consulting custody; no separate
acceptance record is emitted. Delivery assembly at lines 476–487 does retain
host observations without source publication.
[ActorReplyTests.swift](../runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift),
lines 112–157, asserts unresolved issue and retained interrupted-transfer
delivery in separate cases; the issue case does not assert retained host
acceptance. This asymmetry is present in `v0.3.5`. It extends DT-47's
publication/support question but concerns actual native custody and its
loss during assembly, not an unused encoding result. It does not justify
publishing an unobserved native return.

### DT-63 — A final erased flag cannot establish erasure at the last declared transfer

**Relationship examined.** The
[retirement promise](../docs/ARCHITECTURE.md#contract-extensions-custody-erase)
distinguishes last-use erasure from teardown. In
[ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift),
lines 467–468, the comment says custody was erased “at the token's last
declared transfer,” but the assertion reads only final
`outcome.custody.map { $0.erased } == [true]` after `scheduler.run`.

**Source.** [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift),
lines 183–193, calls `finish()` before constructing the outcome.
[AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift),
lines 632–638, always finishes private buffers and sets every custody
observation's `erased=true`. The separate last-transfer defer at lines
514–523 really does erase in the inspected source, including a failed
recipient lookup. The assertion does not distinguish those two sites.

**Executed constructed counterexample to the assertion's meaning.** The
Swift main created one token assigned to actor 0, issue slot 0, final
transfer slot 1, one self-delivery and one inbound/outbound slot. It supplied
a framed synthetic outbound payload `ABC\0`, length 3, committed it, and
called `custody.service(active:0,phaseIndex:0)`. It never published the
transfer request. Output before teardown was `accepted=true erased=false`;
after `custody.finish()` it was `transfers=0 erased=true`. Thus the same
final boolean is obtained without executing the declared last transfer.
This exercise used actual host buffer allocation/service/cleanup with
constructed bytes; it issued no native sandbox extension.

The assertion and unconditional final flag date to `c686a05f`
(2026-11-03). The inspected handoff mutation list in
[actor_handoff_mutations.py](../tests/suites/runner_unit/actor_handoff_mutations.py)
targets slot aliasing, premature outbound erasure, answers, inbound scans
and termination gating; it does not remove last-transfer retirement.
This is a support-scope finding related to DT-38 and DT-47, not evidence
that production currently omits last-transfer erasure. Nor does the boolean
alone constitute an independent scan of the cleared memory.

### DT-64 — Rejected oversized native allocations are erased only through the inspected prefix

**Statements examined.** ARCHITECTURE's issue rule says “Erase the native
allocation after copying”; WORKER's supplied-extension section more
narrowly says erase “to its inspected length.” The capability inventory
also uses inspected allocation wording. The distinction matters when
issuance returns a non-null payload outside the supported bound, before
any custody copy occurs.

**Source and executed constructed native return.** In
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
lines 858–865, `strnlen(token,16384)` caps the inspected length; the rejected
branch erases that length and frees the allocation. The temporary C main
included this unchanged source with its `main` renamed, assigned
`extension_issue` to a replacement returning `malloc(16393)` containing
16,392 `x` bytes plus NUL, and supplied one assigned outbound slot to an
unapplied actor. `free` was intercepted solely to scan that known allocation
immediately before the real free. Calling `attempt_extension_issue` gave:

```text
native_nonnull=1 length=0 custody=4 free_observed=1
first_16384_zero=1 remaining_payload_nonzero=8
```

`custody=4` is `PW_CUSTODY_NOT_PUBLISHED`. The returned allocation was freed,
but eight known nonzero payload bytes remained at that boundary. The
command compiled `issue_tail.c` with the flags and identity above, then ran
the resulting executable directly. It called no real native issue API and
read no freed memory. This demonstrates the implementation's bounded
clearing behavior, not that Apple's current issuer returns oversized
payloads or that those bytes were subsequently recovered.

**Assertions and history.** In
[control.c](../tests/fixtures/extension_controls/control.c), lines 117–124,
the issuer erasure observer scans only the `length` passed to the eraser.
Its oversized mode (lines 160–164) constructs exactly 16,384 nonzero bytes
followed by NUL, so it supplies no nonzero tail beyond that scan. The
[boundary checker](../tests/suites/witness_contract/check_extension_boundaries.py),
lines 326–333, checks returned nonnull, non-issued custody and unavailable
dependent operations for that mode. The recipient-side observer separately
scans full slot capacity; it does not establish issuer-allocation extent.
The bounded issue implementation dates to `c686a05f` and predates 0.3.6.
Related to DT-63's erasure-evidence scope, but this is a different storage
owner and a directly observed nonzero tail. No layer's wording or clearing
policy is selected for change here.

### DT-65 — Body readers accept uncustodied issuance beside successful delivery of that token

**Promise.** RESPONSE's authored token definition requires accepted host
custody for `issued` and its absence for `issued_uncustodied`.
[FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md),
lines 280–285, additionally says the latter token's transfers read
`custody_unavailable`. Delivered transfers require held custody, copying,
equal bytes and recipient acknowledgement.

**Executed constructed reader input.** Change only
`resources.tokens[0].status` from `issued` to `issued_uncustodied` in the
real DT-66 runner body. Keep its completed non-null issue, length, delivered
transfer with `custody_status:held`, equal bytes and both acknowledgements,
and successful consumption. Direct calls to
`actor_evidence.validate_actor_evidence`,
`extension_evidence.validate_actor_extensions` and
`consumer._validate_reply` all returned `[]`; the lifecycle oracle returned
`[]`. The full consumer rejected the edited envelope because its body
differed from the unchanged captured host reply bytes. The saved variant
is `issued_without_custody.json`; no complete-envelope admission is claimed.

**Source.** Python [extension_evidence.py](../tests/lib/extension_evidence.py),
lines 348–361, accepts either issuance status for a completed non-null
event without joining token custody to its transfers. Swift
[PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift),
lines 599–615, and Rust
[porcelain_actor.rs](../controller/src/porcelain_actor.rs), lines 1549–1580,
have the corresponding alternatives. Their delivered-transfer checks
validate that transfer's fields separately. The Swift/Rust paths were read,
not executed with a mutated wire fixture.

Production assembly, in contrast, derives the status from
`outcome.custody.status == accepted` when issue completion exists; the
inspected host erases custody rather than accepting it a second time.
The experiment therefore establishes an unchecked record relationship,
not production of this contradictory combination. Related to DT-52 and
DT-53's reader-scope findings, and to DT-62's missing independent acceptance
record, but not merged with them: here the issue result is complete and
the contradiction is between two retained claims.

### DT-66 — Distinct handle declarations can share one native value and have different release boundaries

**Relationship examined.** REQUEST permits repeated consumption of one
delivery with distinct handle references and one release per reference.
The [authored handle definition](../docs/contract/14-extensions.surface.md),
lines 929–951, calls the returned value a candidate handle and says
`raw_equal_handles` relates numbers, not reference identity. WORKER says
handles persist separately from erased token bytes, with no automatic
exit-time native release. These qualifications are necessary to read the
apparently distinct resources and their `produced` status.

**Executed lifetime exercise.** The input used an unapplied unentitled
issuer A and applied selected worker B. B's exact policy was:

```text
(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension "com.apple.app-sandbox.read"))
```

The global phases were B's baseline fresh read; A's read-class issue `t`
and transfer to B as `d`; then B's phase with
`after_termination:{"actor_id":"A"}` and actions
`consume d→h1`, `consume d→h2`, fresh read `during`, release `h1`, fresh
read `after_r1`, release `h2`, fresh read `after_r2`. Each read had a paired
`file-read-data/path` query for the exact target. Commands and target bytes
are as in DT-59; `repeat/specimen.json` and `repeat/run.json` retain them.

The run returned `finished`. Both consumes returned native handle `1`;
each resource listed the other in `raw_equal_handles`. Both releases
returned `0`. Fresh-open results were baseline `-1/errno 1`, during
successful, after first release successful, after second release
`-1/errno 1`. Both successful reads returned the independently prepared
27 bytes and matching device/inode, with successful stat/close. The target
still contained the same bytes afterward. Issuer PID `28759` had an owned
natural reap (`native_rc:28759`, raw status 0, no departure request), with
capture ordinal 2 before satisfied gate ordinal 3. B was PID `28760`;
both PIDs were absent to `kill(pid,0)` after the CLI returned. Consumer and
lifecycle oracle returned `[]`.

All four query outcomes were deny with `query_first`: the final phase's
queries preceded its two consumes and releases, rather than describing
each later action's authority state. Both handle resources still reported
`status:produced,release_attempted:true` in the final reply. Those values
record production and observed call boundaries, not present validity or
access. The gate established source termination order; the later native
consume/read supplied the separate evidence that the delivered token
remained usable in this experiment.

**Source, tests and limits.** The worker stores each candidate under its
declared handle index, clears the inbound bytes after the final declared
consume, and calls release with the stored number
([pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
lines 908–957). It does not invalidate that table entry after release;
admission prevents a second release of the same logical reference.
[ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift),
lines 421–461, checks completed repeated consumes and release availability,
not equality, native release results or access between releases. The
ordinary lifecycle CLI test in
[check_extensions.py](../tests/suites/witness_contract/check_extensions.py),
lines 100–119, explicitly permits either post-release access result.
This observation does not establish the private library's reference-count
implementation, universal revocation behavior, or the cause of errno 1.
Related to DT-59's phase placement and DT-63/64's token-memory lifetime;
neither erased bytes nor numeric equality substitutes for these file
observations. The per-reference table and repeated-consume test originate
in `c686a05f`, before 0.3.6.

### DT-67 — Two redelegation contrasts record credit without enforcing the documented negative result

**Promise.** [witness_contract/README.md](../tests/suites/witness_contract/README.md),
lines 793–798, describes four contrasts and says each must publish its
remaining links and “must not be credited.” This sits beside the separate
statement that kernel results are recorded rather than forced.

**Inputs and assertions read.** In
[check_extension_redelegation.py](../tests/suites/witness_contract/check_extension_redelegation.py),
`contrast_specs` removes B's consume and cleanup actions, removes B's
issuance allowance, removes C's consume and release, or removes C's
extension read predicate. Lines 284–297 calculate `credited` for every
contrast, but assert `not complete and not credited` only for the two
omitted-consume cases. The weakened-issuance and omitted-predicate branches
merely attach a comparison description and save the observations. A true
credit result in either branch is not itself a failing assertion there.
The common apparatus checks still require exact submitted policy hashes,
distinct processes, setup, publication, phase order and reap.

This is not a claim that `chain()` credits reads alone: lines 149–158
explicitly require both non-null issues, issued custody, delivered/equal
transfers, returned candidate results other than -1, known
fresh bytes and failed baselines. Nor does the principal case require
principal credit to pass: it separately requires a successful native
calibration and prints the principal's actual credit/first-break result.
The [authored executed support](../docs/contract/14-extensions.surface.md),
lines 484–496, names a particular historical credited run; that stronger
historical observation cannot be recovered from a suite pass alone.

**History and limits.** The branch distinction is present from `c686a05f`
(2026-11-03) and in `v0.3.5`. This entry is source/assertion inspection;
neither negative native policy variant was newly executed and no unexpected
native credit is alleged. Related to DT-11/12's execution-evidence scope
and DT-38/47's assertion-scope findings, but a standalone comparison of
these authority-dependency promises and these four actual test inputs.

### DT-68 — Final worker ownership can say mapping held beside confirmed process termination

**Relationship examined.** The authored equipment scope describes an
“ownership state” and lists `not_acquired`, `held`, `released` and
`unresolved` for mapping/descriptor/name. WORKER's resource account says
the accepted worker authority mapping lasts through worker exit. These
are different temporal scopes: a retained worker operation account is not
necessarily a current resource inventory at CLI return.

**Executed observation.** In DT-66's final decoded reply, both worker
authority scopes reported
`descriptor:released,mapping:held,shared_erasure:performed`; their host
region scopes reported mapping release. Both workers were reported reaped
and independently absent by the post-run PID probe. The worker scope does
not convert its earlier successful mapping to `released` on host-observed
reap. `produced` handles likewise remain historical, as DT-66 records.

**Source and assertion scope.**
[AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift),
lines 105–110, sets mapping held from successful slot 8. Only rejected
mapping cleanup in slot 12 can replace that with released or unresolved.
The normal C path holds the mapping and erases settled inbound bytes
before `_exit`; it does not publish a successful normal unmap
(`pw_probe_runner.c`, lines 579–596, 743–761).
[ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift),
lines 558–591, collects that worker publication account and separately
tears down host mappings after reap/quiescence handling. Python
[actor_evidence.py](../tests/lib/actor_evidence.py), lines 100–114, requires
a corresponding cleanup observation for a reported released mapping;
it does not derive that state from reap. The quiescence test in
[ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift),
lines 180–205, constructs an independent host mapping and checks bytes
under supplied quiescent/nonquiescent sets; it does not inspect a worker's
mapping after termination.

The observed field combination therefore cannot establish that a mapping
remains accessible through the terminated worker, or that erasing a slot
released its mapping. This entry records the temporal ambiguity of the
general ownership wording and the concrete producer behavior, not a leak
claim. It is distinct from DT-46's derived cleanup trigger, DT-63's erasure
timing, and DT-66's native handle lifetime.

### Authority coverage and remaining investigative limits

The trace followed request normalization and ownership/index assignments;
global authority-required selection; pre-launch host core-limit, region and
custody allocation; worker symbol lookup, core-limit, mapping, descriptor
closure and assignment snapshots before policy setup; static/live equipment
bindings; issue allocation, outbound publication, host custody, transfer
request/answer, parked/self acknowledgement and settlement; repeated
consumption, per-reference release, normal-exit erasure and host teardown.
It followed selected records into Swift assembly/integrity checks, Rust
body admission and Python body/capture/lifecycle checks, including the
different outcomes of direct body checks and whole-envelope validation.
The native issue/transfer/consume/release calls and fresh file observations
were exercised only in the named specimens. Setup and erasure controls
used deliberately constructed states where identified.

Several inspected relationships have narrower affirmative evidence: the
live examples used separate fresh actors, setup preceded activation, real
delivery was usable after the issuer's owned natural reap, repeated native
consumption and release had independently observed fresh-read boundaries,
and the interrupted issue withheld unpublished native fields. Host custody
and memory erasure are separate from effective authority; stable target
identity in these samples does not establish identity across all intervals.

No registered battery, signing rebuild, BYOXPC installation, native
allocation instrumenter or broad mutation selection was run. Static/live
equipment failure controls, failed close/unmap, unresolved named-object
recovery, symbol absence, cancellation races, release failure, escaped
descendants, retained file descriptors across release and abnormal native
library allocation remain source/test inspections or unexercised limits
here. In particular, the oversized-return control does not characterize
Apple's allocator or actual token maximum; the ready controls do not
establish production-reachable skipped prerequisites; and the temporary
driver's extra custody observation is not a signed public response field.
Historical inspection establishes presence before 0.3.6, not execution of
the older binaries. Only this record was changed; no repair, deduplication
or choice of authoritative layer accompanies these entries.

## Additional findings: `runner reconcile`

This continuation examines one command, `policy-witness runner reconcile`:
the registry and machine state it reads, how its observations become
classifications, any state it changes, its returned fields and exit status,
and the assertions offered for those meanings. It starts at
`cmd_runner_reconcile` and follows the shared registry loader, location
check, service and plist inspectors and ownership classifiers. Installation
and removal code was read only where reconcile shares a record or classifier.
The promises examined are in
[controller/README.md](../controller/README.md) lines 340–345, the authored
[installation surface](../docs/contract/50-installation.surface.md) and its
RESPONSE presentation, [limits.json](../docs/limits.json) and its renderings,
[ARCHITECTURE](../docs/ARCHITECTURE.md), and the
[user guide](../docs/PolicyWitness.md). They were treated as claims to
check. Earlier entries, including DT-34 and DT-35, remain unchanged;
relatives are recorded separately below.

### Reconcile investigation identity and reproduction conventions

Source inspection used clean HEAD `87422530b7c739740bd1325c16c72be698fa32d5`
on 2026-11-16; line numbers below refer to that snapshot. Executed
observations used the existing signed app's
`dist/PolicyWitness.app/Contents/MacOS/policy-witness` in place (SHA-256
`4bcd308bc323516bfd4008eb7d125e6ffe3167b5b6f53d6a042f112b910b8d28`), which
reports commit `8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`, version `0.3.7`,
build `1482`. `git diff 8b5de2b2 HEAD` is empty for `controller/`,
`docs/contract/50-installation.surface.md`, `docs/limits.json`,
`docs/LIMITS.md`, `docs/PolicyWitness.md` and `tests/suites/runner_byoxpc/`.
This is source correspondence, not a new build. The machine reports macOS
`26.7.1`, build `25G241`, arm64, uid 501. No registered case was run, and no
service was installed, bootstrapped, booted out or removed.

**Constructed controls.** The driver
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/814e589d-80a6-4084-9828-4122fc530e4c/scratchpad/scripts/reconcile_trace.py`
(SHA-256 `33f8698a9d719704679bf0fc73e718c951803108486b6c4827a83e613e83276f`)
was run as:

```sh
tests/lib/checkout_lock.sh -- tests/lib/python.sh -I \
  <scratchpad>/scripts/reconcile_trace.py \
  "$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness" <scratchpad>/rt-1
```

It created a fresh root, `<scratchpad>/rt-1`, and supplied
`HOME=<root>/home` and `PW_RUNNER_REGISTRY=<root>/reg/runners.json` only to
the child. The real registry and LaunchAgents directory were therefore not
read by these controls. The real `/Library/LaunchDaemons` was scanned and
added no candidate or inspection error. Every label was
`com.policywitness.trace.reconcile.5d0b9c86a914.<state>` and was never
bootstrapped; the only launchd contact was the product's own
`launchctl print gui/501/<label>`. Each recorded runner was user scope,
`kind: byoxpc`, with bundle `<root>/bundles/<state>/PWRunner.xpc`,
executable `<bundle>/Contents/MacOS/PWRunner` and recorded ownership
`gui/501`, uid 501. Unless noted, its plist path was
`<root>/home/Library/LaunchAgents/<label>.plist` and the recorded hash was
that of the written bytes. A "matching" plist has the label, the arguments
`[<executable>, "--mach-service", <label>]`, `MachServices {<label>: true}`,
`EnvironmentVariables.XPC_SERVICE_PATH = <bundle>`, `RunAtLoad` and
`ThrottleInterval 1`.

| State | Collection | Recorded plist path holds |
| --- | --- | --- |
| `match` | `runners` | matching plist |
| `absent` | `pending_cleanup`, with `cleanup_started_at_unix_ms: 2` and one retained observation | nothing |
| `unreadable` | `runners` | matching plist, mode 000 |
| `unconvertible` | `runners` | bytes `not a plist\n` |
| `symlink` | `runners` | symlink to a matching plist outside LaunchAgents |
| `xpcpath` | `runners` | matching except `XPC_SERVICE_PATH=/caller/supplied` |
| `foreignlabel` | `pending_cleanup` | matching except `Label=unrelated.owner.5d0b9c86a914` |
| `uidmismatch` | `runners` | matching plist; recorded uid 502 and domain `gui/502` |
| `symlinkparent` | `runners` | matching plist; recorded path spelled through `/tmp`, a symlink to `private/tmp` |

The same LaunchAgents directory also held unrecorded files: `orphan`
(its own label, `ProgramArguments ["/unowned/PWRunner"]`), `shadow` (label
of the recorded `match` runner, `["/elsewhere/PWRunner"]`), `locked`
(orphan-like, mode 000), `link` (symlink to an orphan-like plist) and
`org.example.trace.5d0b9c86a914.plist` (`ProgramArguments ["/usr/bin/true"]`
plus a `<data>` value).

The run exited 0 with empty stderr; the envelope had
`kind: "runner_reconcile"`, `result.ok: true`, `exit_code: 0`,
`normalized_outcome: "ok"`. Rows:

| State | Service presence / ownership | Plist presence / ownership | Also a candidate |
| --- | --- | --- | --- |
| `match` | absent / ambiguous | present / owned | no |
| `absent` | absent / ambiguous | absent / ambiguous | no |
| `unreadable` | absent / ambiguous | unknown (`regular: true`, `owner_uid: 501`, `Permission denied (os error 13)`) / unknown | yes, `unknown` |
| `unconvertible` | absent / ambiguous | present (hash, `config: null`, `plutil failed: …`) / unknown | yes, `unknown` |
| `symlink` | absent / ambiguous | present (`regular: false`, `plist is not a regular file`) / unowned | yes, `unknown` |
| `xpcpath` | absent / ambiguous | present / unowned | no |
| `foreignlabel` | absent / ambiguous | present / unowned | yes, `unowned` |
| `uidmismatch` | `{"presence":"unknown"}` | `{"presence":"unknown"}`; row `ownership: "unknown"` | no |
| `symlinkparent` | `{"presence":"unknown"}` | `{"presence":"unknown"}`; row `ownership: "unknown"` | no |

Unrecorded candidates were `orphan` (`unowned`, service `absent`), `locked`
and `link` (`unknown`, null label and service). Neither `shadow` nor the
`org.example` file was a candidate. There were six inspection errors
(`org.example`, `unconvertible`, `unreadable`, `symlink`, `link`, `locked`),
each with `presence: "unknown"`. The registry SHA-256
`f29a6e090b73b80cdb693c4019a9ccf0c1f1b920a1a72abaa1e77bce055ad650` was the
same before and after, and no `runners.json.lock` appeared. An lstat
inventory of every fixture path (mode, inode, size, mtime, ctime, and hash or
link target) was identical before and after. Output SHA-256:
`b84da49eca8ea540b201230add7cf5bca561deb9f712770c663b8501db6fd99d`.

The same unchanged fixture was then run twice under
`tests/lib/checkout_lock.sh -- /usr/bin/env HOME=… PW_RUNNER_REGISTRY=…
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny process-exec
(literal "<tool>"))' <pw> runner reconcile`, once with `<tool>` set to
`/bin/launchctl` (output SHA-256 `355aa89d…65f9`) and once with
`/usr/bin/id` (`10b6ee6d…19bc7`). Both runs exited 0 with `ok`, and the
registry hash did not change. These are constructed environmental failures,
not observations of a restrictive harness. The registry-path variants are
described in DT-74.

**Read-only live observation.** `runner reconcile` was run once with this
user's real environment. The registry at
`~/Library/Application Support/PolicyWitness/runners.json` contained
`{"schema_version":1,"runners":[],"pending_cleanup":[]}`, and
`/Library/LaunchDaemons` held one file, `net.mullvad.daemon.plist`. The run
exited 0 with `ok`, 0 records, 0 candidates and 0 inspection errors (output
SHA-256 `d0de9c51…6b33`). `stat` of the registry and lock (inode, mtime,
ctime, mode) and a listing of their directory were unchanged.

**Retained development run.** `tests/out/runs/plain-help-byoxpc-b16f32d0`
(run ID `20261115T184049Z_7d0a72b1`) passed `runner_byoxpc/registry_recovery`
and `runner_byoxpc/runner_install` against an app reporting commit
`b16f32d044efe9df49014a45f1d1de541c0c0462`, build `1469`.
`git diff b16f32d0 HEAD` is empty for `controller/src`,
`tests/suites/runner_byoxpc` and `tests/fixtures/byoxpc`. Its reconcile
outputs are `registry_recovery/artifacts/{234,254,258,259,279,294}-command/stdout`.
These are live launchd observations from real installations; the run is
pruneable development evidence with no retention guarantee. Temporary
material for the constructed controls also has no retention guarantee, so the
decisive excerpts are reproduced in the entries.

### DT-69 — A later reconcile is said to continue recovery; it leaves even a cleanup-complete record in place

**Statement examined.** The `runner_remove_teardown_wait` effect in
[limits.json](../docs/limits.json) line 1441 is rendered at
[LIMITS](../docs/LIMITS.md) line 145 and in the guide at line 1142: "A
service still listed at expiry retains its cleanup record with a warning; a
later `runner remove` or `runner reconcile` continues recovery." Against it
stand [controller/README.md](../controller/README.md) lines 340–345
("Reconcile is report-only … makes no machine changes"), the authored
reconcile rule
([50-installation.surface.md](../docs/contract/50-installation.surface.md)
line 172, "Leave installation resources and registry records as observed")
and the retained cleanup example (line 220). The example assigns continuation
to repeated removal and inspection to reconcile.

**Executed constructed control.** The `absent` pending-cleanup record had no
plist and a never-bootstrapped label. Its row was:

```json
{"launchd_domain":"gui/501","plist":{"config":null,"error":null,"owner_uid":null,"presence":"absent","regular":false,"sha256":null},"plist_ownership":"ambiguous","recorded_state":"pending_cleanup","service":{"error":null,"executable_path":null,"presence":"absent"},"service_ownership":"ambiguous"}
```

Both resources were observed absent, the state in which removal retires a
record. The registry bytes were nonetheless unchanged and the record stayed
in `pending_cleanup`. The retained live run contains the limits row's own
situation. After `remove --skip-bootout`, artifact `294-command` reports the
record as `pending_cleanup`, service `present`/`owned` and plist
`absent`/`ambiguous`. The test's following `runner remove`, not reconcile,
booted the service out and retired the record
([registry_recovery.py](../tests/suites/runner_byoxpc/opt_in/registry_recovery.py)
lines 446–466).

**Source.** `cmd_runner_reconcile`
([runner_commands.rs](../controller/src/runner_commands.rs) lines 751–870)
calls `load_registry_or_default`, `record_location`, `inspect_service`,
`inspect_plist`, the two classifiers, `launchctl_target`, `read_dir` and
`print_envelope`. It contains no lock, save, bootout or unlink. Its children
are `launchctl print`, `/usr/bin/id -u` and `plutil -convert json -o - -`,
fed on stdin (`plutil_json_from_bytes`,
[runner_manager.rs](../controller/src/runner_manager.rs) lines 784–805).

**History.** Reconcile has had this report-only form since its introduction
in `92891a50` (2026-09-26). The "continues recovery" wording entered with
`cefed899` (2026-10-02) and is present from `v0.3.0` through `v0.3.7`. The
`v0.3.5` guide carries both it and "Reconcile never removes anything."

**Related.** DT-34's third bullet records the contradiction from source
inspection. This entry adds the executed cleanup-complete state; DT-70
concerns how that state is labeled.

### DT-70 — Observed absence and an unattributable present service share the `ambiguous` ownership label

**Statement examined.** README line 341 lists reconcile ownership as
"`owned`, `unowned`, `ambiguous`, `unknown`"; the `service_ownership` field
(surface line 946, [RESPONSE](../docs/RESPONSE.md) line 4135) is an "Owned,
unowned, ambiguous or unknown classification". The classifier statements do
give the mapping: absent becomes `ambiguous` (surface lines 207 and 777–781),
and so does present without a usable executable (lines 795–799).

**Observation.** In the constructed control, every never-bootstrapped label
produced service `absent`/`ambiguous`, and the `absent` row's missing plist
produced plist `absent`/`ambiguous` (DT-69 excerpt). For services, the same
label also covers `present` with zero or several `program = ` lines:
`classify_service_output` keeps a path only for exactly one such line
(runner_manager.rs lines 1236–1243), and `service_ownership` maps a missing
path to `ambiguous` (line 1426). Ownership values therefore do not separate
observed absence from a service that launchd lists but that could not be
attributed. A caller must read `presence` alongside them. No ownership value
marks the both-absent combination that `cleanup_complete` (line 1432)
requires for retirement.

**Evidence scope.** Absence was executed. The present-without-program branch
is source-read plus `service_absence_requires_specific_observation_not_any_nonzero_exit`
(runner_manager.rs lines 2488–2525), which supplies an empty synthetic
stdout. No real `launchctl print` output with zero or several `program = `
lines was observed.

**History.** Both mappings date to `92891a50`; the authored classifier
statements date to `f6551bf9` (2026-11-10, first released in `v0.3.7`).

**Related.** DT-69, DT-75.

### DT-71 — Reconcile output cannot confirm absence of a retired or unrecorded service

**Statement examined.** Guide lines 3206–3208: "After list/reconcile confirm
retirement and service/plist absence, the staging bundle can be removed".
Guide line 3005: "Inspect `runners`, `pending_cleanup` and reconcile's
observed service/plist state. Resolve ownership of an existing service before
reusing its label or bundle path."

**Source.** Reconcile issues `launchctl print` only for a recorded row whose
location resolves (runner_commands.rs lines 775–781) and for a candidate plist
whose label could be parsed (lines 856–860). Candidate discovery enumerates
plist files in `/Library/LaunchDaemons` and `$HOME/Library/LaunchAgents`
(lines 791–846). It never lists launchd services. After removal retires a
record, reconcile inspects that label only if a recognizable plist file
remains.

**Executed observations.** The read-only live run against this user's empty
registry returned `records: []`, `candidates: []`, `inspection_errors: []`
and exit 0. It contains no service observation. This is what reconcile reports
for a retired service whose plist is gone, and it is identical to the report
for a service that was never installed. In the constructed registry variants
of DT-74, the services appear only as plist-file candidates: the 12
candidates come from the scanned files, and each `service` observation is the
lookup of a parsed label. A loaded `com.policywitness.*` service with neither
a record nor a plist file in the scanned directories was not constructed,
because that would require a launchd installation. That it would be missing
from the output is established by source inspection.

**Assertions.** In
[guide_workflows.py](../tests/suites/witness_contract/opt_in/guide_workflows.py)
lines 566–586, the post-removal reconcile envelope is checked only for `kind`
and build contract (`envelope`, lines 356–362, without an exit argument).
Service and plist absence are established by the test's own
`launchctl print` (`session.service_present`) and `os.path.lexists`.

**History.** The guide sentence is from `897be512` (2026-11-11, after
`v0.3.7`). Candidate discovery has been plist-only since `92891a50`.

**Related.** DT-73 and DT-75 record present resources that reconcile output
does not observe.

### DT-72 — A recorded plist path can also be reported as an unregistered candidate

**Statement examined.** README lines 342–343 say reconcile "scans … for
unrecorded `com.policywitness.*` labels or `PWRunner` executables". The
`candidates` field (surface line 871) holds "Recognizable unregistered
launchd plist candidates", and the candidate rule (line 176) says
"Registered label/scope pairs are suppressed from candidates." Guide lines
3214–3221 give administrative cleanup steps for "an unregistered candidate
reported by reconcile".

**Source.** Suppression compares only a candidate's parsed `Label` and the
scanned directory's scope with recorded `service_name` and `scope`
(runner_commands.rs lines 848–852). It does not compare the candidate path
with any record's resolved plist path. A plist without a readable label
becomes a candidate by filename prefix (lines 837–844), and its `None` label
never matches a record.

**Executed observations.** In the constructed control, four recorded plist
paths were also reported with `recorded_state: "unregistered"`:
`unreadable`, `unconvertible` and `symlink` as `ownership: "unknown"`, and
`foreignlabel` as `ownership: "unowned"` with
`service_name: "unrelated.owner.5d0b9c86a914"` and service `absent`. The
retained live run shows the same for a real installation. In artifact
`234-command`, the `pending_cleanup` row for
`com.policywitness.test.registry.sf59a79ee8e23f27dde9dd138` has
`plist_ownership: "unowned"`. The run's only candidate has
`service_name: "unrelated.owner"` and `ownership: "unowned"`, with the same
`plist_path` and plist SHA-256 as that row. Its executable is the recorded
bundle's `Contents/MacOS/PWRunner` (stdout SHA-256
`496d2adc7eace07cd5a4b433a1a6b14a84147aafbf4df67b192509ac081c1a77`).

**Assertions.** The test that produced artifact 234 (`registry_recovery.py`
lines 299–301) selects the record row and asserts `recorded_state` and
`plist_ownership`. It does not inspect that report's `candidates`.

**History.** Label/scope suppression dates to `92891a50`, the README wording
to `625c9051` (2026-10-11), and the authored rule to `f6551bf9`.

**Related.** DT-73 is the opposite consequence of the same rule.

### DT-73 — An unregistered plist carrying a registered label is reported nowhere

**Statement examined.** The candidate rule (surface line 176) and the
reconcile effect (line 172): "report recognizable unregistered plist
candidates plus inspection errors."

**Executed constructed control.**
`com.policywitness.trace.reconcile.5d0b9c86a914.shadow.plist` was an
unrecorded file in the scanned LaunchAgents directory. Its `Label` was the
recorded `match` service and its `ProgramArguments` were
`["/elsewhere/PWRunner"]`. The string `shadow` does not occur in the main
constructed output. It appears only in the DT-74 variants, where no records
were loaded.
The file was suppressed from candidates by label, the `match` row inspected
only its recorded path, and the file produced no inspection error. The
present, readable plists at the `uidmismatch` and `symlinkparent` recorded
paths were also suppressed as candidates, while their rows held only location
placeholders (DT-75). Neither file's observation appears anywhere.

**Scope.** Launchd's handling of two plists claiming one label was not
examined. If the extra plist were the loaded one, the recorded row's service
observation would report its different executable as `unowned`
(`service_ownership`, runner_manager.rs lines 1419–1429); this is
source-inspected.

**History.** Since `92891a50`.

**Related.** DT-72, DT-71, DT-75.

### DT-74 — An inaccessible registry is read as an absent one

**Statement examined.** The read rule (surface line 34; RESPONSE line 3780)
says: "The registry is readable with schema_version 1, or its path is absent.
… An absent file yields schema_version 1 with empty runners and
pending_cleanup." Line 39 says "Unsupported registry schemas and malformed
known fields refuse loading." The `retained_free` note on line 36 treats
"Registry absence, unreadability and decoded schema version" as separate
outcomes and observes that "an empty decoded registry cannot distinguish an
absent file."

**Source.** `load_registry` (runner_manager.rs lines 540–557) returns the
empty registry when `path.exists()` is false (line 541). Rust's
`Path::exists` returns false whenever metadata cannot be read, including
permission denial on an ancestor and a dangling symlink. Only a regular file
that exists but cannot be read reaches the failing `read_to_string`.

**Executed constructed controls.** A copy of the fixture registry (seven
runners, two cleanup entries) was placed at three paths; a fourth path named
an absent directory. Each was supplied through `PW_RUNNER_REGISTRY`:

| `PW_RUNNER_REGISTRY` under `<root>/registries/` | Exit | Output |
| --- | --- | --- |
| `locked/runners.json`, parent mode 000 | 0 | `ok`, `records: []`, 12 candidates, 6 inspection errors; `registry_path` names the supplied path |
| `dangling.json`, symlink to a missing file | 0 | same |
| `never/runners.json`, parent absent | 0 | same; `never/` still absent afterward |
| `unreadable.json`, mode 000 | 2 | no stdout; stderr `failed to read …/registries/unreadable.json: Permission denied (os error 13)` |

All three exit-0 outputs are identical apart from `registry_path`. In the
first two cases, the unreadable registry held seven runners and two cleanup
entries. With no records loaded, every fixture plist in the scanned
LaunchAgents directory became an `unregistered` candidate. This included the
plists at the recorded paths of `match`, `xpcpath`, `foreignlabel`,
`uidmismatch` and `symlinkparent`, reported as `ownership: "unowned"` with
service `absent`. The plists at the recorded paths of `unreadable`,
`unconvertible` and `symlink` were reported as `unknown`. Nothing in these
outputs indicates that the registry could not be read. The guide's
administrative cleanup steps for unregistered candidates (lines 3214–3221)
would then apply to installations that the unreadable registry still owns.

**Scope.** Only reconcile was executed. `runner list` uses the same
`load_registry_or_default` (runner_commands.rs line 456), and status, verify
and remove reach the same `load_registry`; their consequences were not
exercised.

**History.** The `exists()` check is present in the first commit containing
the loader, `4ca7ff81` (2026-01-13), and in every release tag. The authored
rule dates to `f6551bf9`; the retained note to `5c1c63dc` (2026-11-11, after
`v0.3.7`).

**Related.** DT-72 (recorded plists reported as candidates through another
route), DT-71, DT-35 (exit 2 without an envelope for the unreadable-file
case).

### DT-75 — Location refusal reports uninspected resources as unknown and merges identity contradiction with environmental failure

**Statement examined.** The reconcile record fields (surface lines 911, 919
and 964; RESPONSE lines 4131–4138) say `service` and `plist` hold the "Full
… Observation after valid location resolution; otherwise only
{"presence":"unknown"}", and that `ownership` is "unknown on location
error". The ownership check's condition (surface line 201) is: "The recorded
service name, user/scope/domain and paths pass location checks." The service
`presence` field (line 740) defines `unknown` as a `launchctl print` outcome,
and `error` (line 748) is the "Inspection diagnostic for unknown presence".

**Executed constructed observations.** Three conditions produced the same
row form: `ownership: "unknown"`, with service and plist both
`{"presence":"unknown"}` and no observation inside either:

- `uidmismatch`, recorded installer uid 502 and domain `gui/502`:
  `error: "recorded cleanup ownership is inconsistent with this user, scope or paths"`.
  A matching readable plist was present at the recorded path.
- `symlinkparent`, the same directory named through `/tmp`:
  `error: "recorded plist parent is a symlink"`. A matching readable plist
  was present.
- With exec of `/usr/bin/id` denied by `sandbox-exec`, all nine rows had
  `error: "failed to run id -u: Operation not permitted (os error 1)"`. These
  included `match` and `absent`, whose plist states the unconfined run had
  observed. Candidate `service` values became null.

By contrast, denying exec of `/bin/launchctl` preserved every plist
observation and classification. In each resolved row it gave
`service.presence: "unknown"`, `service_ownership: "unknown"` and
`service.error: "Operation not permitted (os error 1)"`.

`unknown` thus has three sources: an inspection that failed and carries its
error inside the observation; a resource not inspected because the recorded
identity contradicts the current user or path; and a resource not inspected
because the environment prevented location. Only the free-text row `error`
separates the last two. A recorded identity that contradicts the current
user or path is not reported as a mismatch (`unowned`).

**Source.** In `record_location` (runner_manager.rs lines 1322–1378),
`launchctl_target`, which runs `id -u`, precedes the ownership checks. The uid
comparison is at line 1339 and the symlinked-ancestor refusal at lines
1360–1366. The placeholder row is built at runner_commands.rs lines 784–787.

**Assertions.** No reconcile assertion covering a location error was found.
The classify note (surface line 770) says such a row "has no typed ownership
association".

**History.** The location checks and placeholder date to `92891a50`; the
field statements to `f6551bf9`.

**Related.** DT-73 (the suppressed present plists), DT-70.

### DT-76 — Executed plist classifications outside the statement's cases

**Statement examined.** Surface lines 202 and 207 (RESPONSE line 3856)
derive plist ownership from "a regular file with matching Label, complete
ProgramArguments, MachServices and XPC_SERVICE_PATH". They classify absent
resources `ambiguous` and say "Unknown presence produces unknown ownership."
The candidate `ownership` field (line 1050) is `unknown` "when config is
unavailable".

**Executed constructed observations.**

- `symlink`: the recorded path is a symlink to a matching plist, observed as
  `presence: "present"`, `regular: false`,
  `error: "plist is not a regular file"`, with `plist_ownership: "unowned"`.
  The same path reported as a candidate (DT-72) and the unrecorded `link`
  symlink both have `ownership: "unknown"`. One kind of object is therefore
  `unowned` on the recorded path and `unknown` as a candidate.
- `unconvertible`: `presence: "present"`, `regular: true`, a SHA-256,
  `config: null`,
  `error: "plutil failed: <stdin>: Property List error: Unexpected character n at line 1 …"`,
  and `plist_ownership: "unknown"`. Here `unknown` ownership accompanies
  `present` presence.
- `xpcpath`: identity fields and the recorded hash match except
  `XPC_SERVICE_PATH=/caller/supplied`, giving `plist_ownership: "unowned"`.
  This agrees with the statement and executes the classification half of
  DT-34's first bullet. Installation's `--env` handling and the effect on
  removal were not exercised.
- `unreadable`: `presence: "unknown"` alongside `regular: true` and
  `owner_uid: 501` from successful metadata, then
  `Permission denied (os error 13)` on read. This matches the presence
  definition (surface line 818).

**Source.** `plist_ownership` (runner_manager.rs lines 1387–1392);
`inspect_plist` (line 1315); candidate ownership (runner_commands.rs
line 863).

**Related.** DT-34's second bullet records the first two branches from source
inspection only.

### DT-77 — Inspection errors report `unknown` presence for present plists and include non-candidates

**Statement examined.** The `inspection_errors` field (surface line 879)
holds "Directory, path or plist inspection failures encountered during
candidate discovery", with presence "unknown for each inspection error"
(line 1074). The plist presence definition (line 818) is `present` for
"observed metadata, including invalid content".

**Executed constructed observation.** All six inspection errors had
`presence: "unknown"`. Four concern files observed as present: the
`unconvertible`, `symlink` and `link` paths, which also appear as candidates
with `plist.presence: "present"`, and
`org.example.trace.5d0b9c86a914.plist`. That last file is a valid property
list with `Label`, `ProgramArguments ["/usr/bin/true"]` and a `<data>` value.
Its error was `plutil failed: <stdin>: Invalid object in plist for JSON
format`, and it is not a candidate. The other two errors (`unreadable` and
`locked`) are read failures, which the plist observation also reports as
`unknown`.

**Source.** runner_commands.rs lines 824–828 append an inspection error for
every `*.plist` in both directories whose observation carries an error. This
happens before the candidate filter, with a fixed `"presence":"unknown"`.
`plutil -convert json` exited 1 with the same message for a separately piped
property list containing `<data>`.

**Live and assertions.** The read-only live run had one file in
`/Library/LaunchDaemons` and no inspection errors. `registry_recovery.py`
lines 336–343 assert an inspection error with `presence: "unknown"` only for
a mode-000 candidate, which is a read failure.

**History.** Since `92891a50`.

**Related.** DT-76.

### DT-78 — The ARCHITECTURE reconcile row describes listing and owned-looking resources, and cites a check that asserts only `ok`

**Statement examined.** [ARCHITECTURE](../docs/ARCHITECTURE.md) line 1127
(from [architecture.json](../docs/architecture.json) line 6791) says
reconcile "reports launchd services and plists that look owned, changing
nothing". Lines 1158–1159 (architecture.json lines 7463 and 7484) give X24,
"inspect_service lists candidate services without changes", and X25,
"inspect_plist lists candidate plists without changes". All three cite
`runner_install` in `tests/suites/runner_byoxpc/run.sh` as their check.

**Source.** `inspect_service` runs `launchctl print <domain>/<label>` for one
supplied label and lists nothing (runner_manager.rs lines 1259–1276).
Candidate services are only labels parsed from plist files. Reconcile reports
every recorded row regardless of ownership. Candidate ownership is only
`unknown`, `ambiguous` or `unowned` (runner_commands.rs line 863), so no
candidate is reported as owned.

**Assertions.** `runner_install` reaches reconcile only through
`session.install` ([session.py](../tests/fixtures/byoxpc/session.py)
line 234). There, `envelope` (lines 28–32) requires exit 0 through
`caller_auth/bundle.py` `command` (lines 44–45) and `result.ok is True`, then
returns `data` without examining it. The session scopes `PW_RUNNER_REGISTRY`
to a per-service path under `test-sessions/` that does not yet exist
(`session_invoke`, lines 101–111), so this call reads an absent registry. The
retained `runner_install/artifacts/reconcile-before` output has 0 records,
0 candidates and 0 inspection errors. The substantive reconcile assertions
are in the opt-in `registry_recovery` case, which these rows do not cite.

**History.** The row and edges entered with `e2115cf3` (2026-10-06) and are
present from `v0.3.0` onward.

**Related.** DT-79.

### DT-79 — The reconcile rule's check-read support cites no reconcile assertion; executed assertions are opt-in and joint

**Statement examined.** RESPONSE line 3769 grades the subtree support for
"Managing runners and its descendants", which includes
[Reconcile observations](../docs/RESPONSE.md#contract-installation-commands-reconcile),
as **check read**. Its evidence limit says live launchd needs "separately
recorded execution evidence". The dynamic support (line 3772) is source read
for field shapes. The surface's fenced block (line 7) declares
`checks: ["unit", "runner_byoxpc"]`.

**Observation.** The six checks cited by the subtree owner (surface line 18)
are `install_failure_boundaries_preserve_observed_pending_state`,
`legacy_metadata_survives_unrelated_writes_and_pending_cleanup`,
`historical_flattened_cleanup_remains_readable_and_rewrites_with_nested_runner`,
`registry_save_refuses_duplicate_known_metadata_before_publication`,
`atomic_registry_replace_preserves_old_open_readers_and_failed_write` and
`bootout_waits_out_launchd_teardown_within_the_budget`. They exercise
install, save and removal paths with supplied observations. None calls
`cmd_runner_reconcile`, `record_location`, `inspect_service`, `inspect_plist`
or `load_registry` on an absent or inaccessible path. The classifier unit
tests (`service_absence_requires_specific_observation_not_any_nonzero_exit`
and `plist_and_service_evidence_independently_gate_cleanup_retirement`) are
not cited for the reconcile rule.

The executed reconcile assertions are in opt-in `registry_recovery.py`:

- lines 299–301: a pending-cleanup foreign label gives `plist_ownership: "unowned"` (DT-72);
- lines 314–321: reconcile exits 0 while the lock is held; registry and plist
  bytes are compared after list, status, reconcile and a `verify` attempt
  that exits 1 (the service was installed with `--skip-bootstrap`);
- lines 333–343: an unregistered candidate is `unowned`, and a mode-000 file
  yields an inspection error;
- lines 429–435: a legacy record is `installed` and owned/owned, with the
  compatibility snapshot compared after refused `run` and `verify` (exit 2),
  list, status and reconcile together;
- lines 450–453: after `--skip-bootout`, the record is `pending_cleanup` with
  service present and plist absent.

Every no-change assertion includes reconcile together with other commands.
The README's "Reconcile creates no registry or lock" (line 344) has no
assertion; in that test the lock already exists from earlier installations.
The constructed control executed this claim (no lock, no created directory),
but it is not a registered case. The retained run cited above passed both
cases.

**Related.** DT-14 (surface-level check declarations versus owner
citations), DT-38 (check-read scope), DT-78.

### DT-80 — Smaller observations on reconcile output

- Pending-cleanup rows report only the nested runner. The `absent` fixture
  entry carried `cleanup_started_at_unix_ms: 2` and the retained observation
  `{"phase":"before","fixture":"retained observation"}`. Neither the key
  `cleanup_started_at_unix_ms`, the key `observations`, nor that value occurs
  in the reconcile output, because runner_commands.rs line 772 maps each
  cleanup entry to `&r.runner`. The `records` field says "Recorded runners and
  retained cleanup entries" (surface line 863), and README line 317 says
  cleanup "retains this identity and before/after observations"; `runner list`
  exposes them. Executed constructed.
- Candidate recognition depends on a `com.policywitness.` label, a `PWRunner`
  executable filename, or that filename prefix on an unparsed plist
  (runner_commands.rs lines 837–844). Installation accepts any
  `CFBundleIdentifier` as the service name and any `CFBundleExecutable`
  (lines 251–255). A lost record for a differently named service is
  therefore not recognizable. The statements present this as a heuristic
  ("Recognizable", "can identify"), and the guide's recipe uses
  `com.policywitness.guide.…` (line 3035). Source inspection only.
- Reconcile reads the registry once and without a lock, then performs
  launchctl and filesystem reads for each row. The output carries only the
  envelope's `generated_at_unix_ms`. A concurrent modifier can therefore
  produce rows that pair an earlier registry state with later resource
  observations. Lock-free reading is documented (surface line 39). Source
  inspection; not exercised.
- The `launchctl print`, `id -u` and `plutil` children it starts have no
  time bound, and [LIMITS](../docs/LIMITS.md) has no reconcile entry. Source
  inspection; not exercised.

### Reconcile coverage and remaining investigative limits

The trace covered the dispatch (`cmd_runner`, `runner reconcile accepts no
arguments`), registry path selection and loading, record location, service
and plist inspection, both ownership classifiers, candidate discovery and
classification, inspection-error assembly, the envelope and exit status, and
the CLI's mapping of an `Err` to stderr and exit 2. Reconcile writes nothing.
Its effects are child processes (`launchctl print`, `id -u`, `plutil`) and
reads of the registry, plist files and two launchd directories. The executed
evidence is the constructed fixture run, two constructed environmental-denial
runs, four registry-path variants, one read-only live run and the retained
2026-11-15 development run.

Live present-service evidence (`present`/`owned` and present beside an absent
plist) comes only from the retained artifacts `279-command` and
`294-command`. The constructed controls observed no present service.
Present-without-program, system-scope records, legacy records without
ownership, `HOME` unset, a broken stdout (DT-28), concurrent modification,
launchd's handling of duplicate labels, and the reconcile consequences for
list/status/verify/remove of an inaccessible registry were not executed.
Historical inspection establishes when mechanisms and statements appeared,
not how older binaries behaved. Only this record was changed. These entries
contain no repair, deduplication or choice of authoritative layer.

## Additional findings: `sbpl-check` import-inventory completeness

This continuation asks what the helper's `import_inventory` reveals about
whether its import scan was complete. It follows the shared lexer
([sbpl_lex.rs](../controller/src/sbpl_lex.rs)), the resolver
([sbpl_imports.rs](../controller/src/sbpl_imports.rs)) and the helper's
projection ([sbpl-check.rs](../controller/src/bin/sbpl-check.rs)). It also
examines the [Literal import inventory](../docs/RESPONSE.md#contract-policy-imports)
statements and their authored source
([11-policy.surface.md](../docs/contract/11-policy.surface.md) lines 540–604),
the helper passage of the [user guide](../docs/PolicyWitness.md) (lines
867–894) and the tests that exercise the scanner or the helper's output. The
controller dossier was read only where it shares the resolver. The statements
were treated as claims to check. DT-29 remains unchanged; DT-81 to DT-87
extend it and stand alone.

### Import-inventory investigation identity and reproduction conventions

Source inspection used clean HEAD `1413c20eb5fe60a6e7696d43440d80993cdfeecd`
on 2026-11-16; line numbers below refer to that snapshot. Executed helper
observations used the existing signed app's
`dist/PolicyWitness.app/Contents/MacOS/sbpl-check` in place (SHA-256
`1d4470289c9f155e6ff7e19ea8da7f5e45c89bd9905bf64c425063d2405b8988`). Every
helper envelope carried build commit
`8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`, version `0.3.7`, build `1482`.
`git diff 8b5de2b2 HEAD` is empty for the three scanner and helper sources,
`digest.rs`, `host_facts.rs`, `json_contract.rs`, `dossier.rs`,
`controller/integration/cli_contract.rs`, `Cargo.toml`, `Cargo.lock`,
`docs/contract/11-policy.surface.md`, `docs/contract/42-dossier.surface.md`
and `docs/RESPONSE.md`. This is source correspondence, not a new build. The
machine reports macOS `26.7.1`, build `25G241`, arm64. No registered case
was run, and nothing was built in the checkout.

**Helper drivers.**
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/1f71e0b5-7b7d-4892-80b4-1b0de6e79d07/scratchpad/scripts/inventory_trace.py`
(SHA-256 `112531e053d22fde1e138378f6b255131ab717584ec3b8cf52927a0854e1da65`)
was run as:

```sh
tests/lib/checkout_lock.sh -- tests/lib/python.sh -I \
  <scratchpad>/scripts/inventory_trace.py \
  "$PWD/dist/PolicyWitness.app/Contents/MacOS/sbpl-check" <scratchpad>/it-2
```

For each case it wrote
`{"policy":{"format":"sbpl","sbpl_source":S},"probe_plan":[]}` to a file and
ran `sbpl-check --request <file>` with only `PATH=/usr/bin:/bin` in the
environment. `helper_over_files.py` (SHA-256 `4d2f1899…0708b`) does the same
for named source files; it produced `<scratchpad>/bc-deny-helper` and
`<scratchpad>/utf8-helper`. Afterward, one pass over all 20 envelopes
recomputed `policy_sha256` as SHA-256 of the submitted source bytes. It also
recomputed the documented closure framing from each envelope's own records,
and checked the data and inventory key sets. The first driver additionally
compared each recorded hash with a separate read of its `resolved_path`.
Below, `<D>` is `<scratchpad>/it-2/files`, which held:

| File | Bytes |
| --- | --- |
| `marker.sb` | `(allow pw-trace-marker-operation)\n` (SHA-256 `30c8c5e0…69df9`) |
| `wrapper-bsd.sb` | `(import (string-append "bsd" ".sb"))\n` (`45444b5e…9b4a`) |
| `wrapper-marker.sb` | `(import (string-append "<D>" "/marker.sb"))\n` |
| `wrapper-literal-marker.sb` | `(import "<D>/marker.sb")\n` |

`marker.sb` names no SBPL operation. When the compiler evaluates it,
compilation fails with a diagnostic naming that file. The compile outcome
therefore shows whether the compiler evaluated the file.

**Lexer probe.** `lex_probe.rs` (SHA-256 `409a4457…cd22`) includes the
checked-in `controller/src/sbpl_lex.rs` (SHA-256
`5339d1237b65a8605e4fa3cd07e9e4478f25e77a26d134836272d9221441a978`) through
`#[path]`, unmodified. It was compiled in the scratchpad with
`rustc 1.99.0 --edition 2024 -O`. For each source and import file, it prints
`import_scan`'s `scan_complete` and `refs`, the internal distinction the
resolver turns into `nonliteral_imports`.

**Native bytecode probe.** `bytecode_digest.c` (SHA-256 `a75d71e6…7f88`) was
compiled with `/usr/bin/clang -O1 … -lsandbox`. It calls
`sandbox_compile_string` with NULL parameters and reads the returned profile
through the worker's 24-byte view: type, reserved, bytecode pointer and length
([pw_profile_capture.h](../controller/tools/pw_probe_runner/pw_profile_capture.h)
lines 15–22). Each read uses `mach_vm_read_overwrite`. The probe prints the
bytecode length and SHA-256 and involves neither `sbpl-check` nor the
scanner. Two consecutive runs printed identical lines.

Every helper invocation exited 0 with `ok` or 1 with `compile_error`. Each
wrote empty stderr, emitted exactly the seven `data` keys and four inventory
keys, and published a `policy_sha256` equal to the source hash. Each
recomputed closure equaled the published one, and each separate file read
matched its recorded hash. Temporary material has no retention guarantee, so
the decisive excerpts are reproduced in the entries.

### DT-81 — `import_inventory` carries four of the scanner's distinctions; nonliteral forms, the bound name and the first problem are dropped

**Statements examined.** The subject statement
([RESPONSE](../docs/RESPONSE.md#contract-policy-imports) line 862; authored
at [11-policy.surface.md](../docs/contract/11-policy.surface.md) line 547)
says "an unevaluable import argument, unreadable/nonregular file or invalid
UTF-8 scan input records an incomplete inventory." The helper's published
inventory has four fields: `records`, `truncated`, `cycle` and
`policy_closure_sha256` (lines 864–867).

**Source inspection.** `ResolvedImports`
([sbpl_imports.rs](../controller/src/sbpl_imports.rs) lines 117–132) carries
six members. The helper's `ImportInventory` (sbpl-check.rs lines 86–92) is
built at lines 346–355 from `records`, `truncated` and `cycle`, plus a closure
computed over `records`. Lines 113–115 say that the helper reports `truncated`
and that the controller dossier reports `exceeded` and `nonliteral_imports`.

| Scanner condition | Internal record | What `import_inventory` shows |
| --- | --- | --- |
| Name not found | Error record and `failure` (lines 273–292) | Record with null path and `error: "not found in search path"` (executed: M3 in DT-82) |
| Open/fstat failure or nonregular file | Record with the `read_regular_file` error and `failure` (lines 76–92, 233–237) | Record error |
| Invalid UTF-8 import | Record keeps hash and size, has error `not valid UTF-8; its imports were not scanned`, and sets `failure` (lines 242–253) | Record error (executed: DT-87) |
| Depth bound | `truncated`, `exceeded: "depth"`, a record with `depth limit exceeded (8)`, and `failure` (lines 219–230) | `truncated` and the record error |
| Count bound | `truncated`, `exceeded: "count"`, no record, and `failure` (lines 155–163, 213–216, 277–280) | `truncated` only |
| Cycle | `cycle` chain and `failure` (lines 196–206) | `cycle` |
| Nonliteral form in submitted source | `nonliteral_imports` and `failure` (lines 313–317) | Nothing (DT-82) |
| Nonliteral form in an imported file | `nonliteral_imports` and `failure`; the file's record error is unchanged (lines 259–265) | Nothing; that file's record has `error: null` (DT-83) |
| First problem | `failure` | Dropped |
| Which bound stopped the walk | `exceeded` | Dropped. A depth hit leaves an error record and a count hit leaves none. If both occur, their order is lost |

The helper inventory has no field meaning "incomplete." A consumer can infer
an unreadable, nonregular or invalid-UTF-8 input only from `records[].error`
text. A nonliteral argument cannot be inferred. The lexer's own documentation
([sbpl_lex.rs](../controller/src/sbpl_lex.rs) lines 13–18) says consumers
treat empty `refs` with `scan_complete = false` as "not followed" rather than
"no imports." No reader of the helper envelope can make that distinction. The
guide's helper passage ([PolicyWitness.md](../docs/PolicyWitness.md) lines
867–870) promises only that "Resolution errors, truncation and cycles stay in
the inventory," which matches the projection.

**History.** The helper has never published a nonliteral-import signal. The
lexer was introduced in `b9c02792` (2026-05-19). Its import scan returned only
a name set (`import_refs`, verified at `e0105092^`) until `ed0bd3da`
(2026-10-01). That commit added the scan's completeness flag and the
resolver's `nonliteral_imports`, `exceeded` and `failure`, with the comment
assigning the latter two to the dossier. `7a0dcbac` (2026-10-03) grouped the
helper's fields into the current four-field `import_inventory`; both commits
are in v0.3.5. The sentence "records an incomplete inventory" first appears in
`f6551bf9` (2026-11-10). That commit is in v0.3.7 but not v0.3.6, and v0.3.6's
RESPONSE contains no `nonliteral`, `unevaluable` or `import_inventory` text.
The projection therefore predates the 0.3.6+ contract changes, while the
sentence it contradicts arrived with them. Related: DT-29, DT-82 and DT-83.

### DT-82 — A computed import argument that the compiler follows yields the inventory of a policy with no imports

**Executed constructed control.** The three required inputs share the base
`(version 1)\n(deny default)\n` and differ only in the third line:

| Case | Third line | Source SHA-256 = `policy_sha256` | Helper result | `records` | `truncated` / `cycle` | `policy_closure_sha256` | Lexer `scan_complete` / `refs` | Native bytecode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | none | `6906c7cd…1d5f` | `ok`, exit 0 | `[]` | false / null | `f6aa3063…8f6c` = SHA-256(A ‖ 0x1F) | true / `[]` | 456 bytes, `2cc1b84c…8b74` |
| B | `(import "bsd.sb")` | `a5292b6e…5580` | `ok`, exit 0 | `bsd.sb`, `dyld-support.sb` and `system.sb` under `/System/Library/Sandbox/Profiles`, each with `error: null` | false / null | `7fddbed8…d84c` | true / `["bsd.sb"]` | 2420 bytes, `bb152ee6…0d9e` |
| C | `(import (string-append "bsd" ".sb"))` | `91f3e8b7…a1fa` | `ok`, exit 0 | `[]` | false / null | `17601787…b6d1` = SHA-256(C ‖ 0x1F) | **false** / `[]` | 2420 bytes, `bb152ee6…0d9e` |

B's record hashes were `f69ffbef…f8c8` (858 bytes), `06215a5d…bf1c` (2655
bytes) and `1b2c4487…846f` (12024 bytes). The full bytecode digests were
`2cc1b84cc42cf1e2d5fbed099a0c722dfcf6644b41f785a05abadae58b028b74` for A and
`bb152ee600934e1e09091c10f3b4e80ff17f235f64748dff5d0b4342e1cf0d9e` for both B
and C.

C's native compilation produced bytecode identical to B's and different from
A's. The compiler therefore incorporated the same imported rules through the
computed argument as through the literal one. The scanner recorded this
distinction internally (`scan_complete: false`). The helper's inventory for C
nevertheless matched A field for field except for the closure hash. That
difference does not encode the scan state. Each of A's and C's closures is
SHA-256 of its own source followed by 0x1F, with no path/hash line; they
differ only because the third source line differs. B's closure covers three
path/hash lines and was recomputed from its records and from independent
reads of the three files. Compilation succeeded for A, B and C, so the result
says nothing about imports.

Marker controls on the base `(version 1)\n(allow default)\n` show that the
compiler opens a computed path:

- M2, `(import (string-append "<D>" "/marker.sb"))`: `compile_error`, "unbound
  variable: pw-trace-marker-operation at <D>/marker.sb, line 1, column 8";
  `records: []`, `truncated: false`, `cycle: null`. The literal form M1,
  `(import "<D>/marker.sb")`, produced the same diagnostic and one
  `marker.sb` record.
- M4, `(import (string-append "<D>" "/absent.sb"))`: `compile_error`, "unable
  to open <D>/absent.sb: No such file or directory"; `records: []`. The
  literal form M3 produced the same diagnostic and the record
  `{"name":"<D>/absent.sb","resolved_path":null,…,"error":"not found in search path"}`.

The allow-default versions of A, B and C in `it-2` produced the same
inventory shapes. All three compiled to identical 492-byte bytecode
(`b2056ef2…97e0`), so an allow-everything base cannot reveal imported rules
in a bytecode comparison.

**What each field establishes for C.** `records: []` means that no literal
name was collected, not that nothing was imported. `truncated: false` means
that no bound was reached, and `cycle: null` means that the walked files
formed no cycle. The closure identifies the source and an empty set of read
files. No field, alone or with the others, distinguishes C from A. This
extends DT-29, which left native imports unexamined. Related: DT-81, DT-83 and
DT-86.

### DT-83 — A nonliteral import inside an imported file leaves that file's record error-free

**Source inspection.** When an imported file is not valid UTF-8, the resolver
writes `not valid UTF-8; its imports were not scanned` into that file's record
([sbpl_imports.rs](../controller/src/sbpl_imports.rs) lines 242–253). When a
nonliteral form makes the file's own scan incomplete (lines 259–265), it sets
only `nonliteral_imports` and `failure`. The file's record keeps
`error: null`, along with its hash, size and mtime. The
[records statement](../docs/RESPONSE.md#contract-policy-imports-records)
(line 864) says each resolved file's held bytes are "both hashed and scanned."
The record shows that a scan happened, but not whether it was complete.

**Executed constructed control.**

- Nd is `(version 1)\n(deny default)\n(import "<D>/wrapper-bsd.sb")\n`. The
  helper returned `ok` with one record, `wrapper-bsd.sb` (`45444b5e…9b4a`,
  `error: null`), `truncated: false`, `cycle: null` and closure
  `1966a6c6…5a87`. The native bytecode was 2420 bytes, `bb152ee6…0d9e`,
  identical to B in DT-82. The compiler followed the nested computed import
  of `bsd.sb`.
- N2 imports `wrapper-marker.sb` literally on the allow-default base. It
  produced a `compile_error` naming `<D>/marker.sb`; its only record is
  `wrapper-marker.sb`, with `error: null`. N3 imports
  `wrapper-literal-marker.sb`, produced the same diagnostic and recorded both
  files.
- The lexer probe reports `scan_complete: false` for `wrapper-bsd.sb` and
  `wrapper-marker.sb`. It reports `true` for the top-level Nd, N1 and N2
  sources.

The per-record errors are therefore not a complete account of files whose
imports went unscanned: the invalid-UTF-8 case is marked, but the
computed-argument case is not. No test exercises lines 259–265. The
[sbpl_imports.rs](../controller/src/sbpl_imports.rs) tests contain no
nonliteral form, and the helper's constructed variants fix
`nonliteral_imports: false` ([sbpl-check.rs](../controller/src/bin/sbpl-check.rs)
line 992). From source, the dossier would report `incomplete` with failure
`import "<name>": a nonliteral (import ...) form could not be followed`; this
was not executed. The nested branch was added in `ed0bd3da`. Related: DT-29,
DT-81 and DT-82.

### DT-84 — A literal import that the compiler follows can escape the scanner with no incompleteness signal

**Executed constructed control.** L2 adds the third line
`(import "<D>/marker.sb" ; note\n)` to the allow-default base. Native
compilation failed with "unbound variable: pw-trace-marker-operation at
<D>/marker.sb, line 1, column 8," so the compiler read and evaluated
`marker.sb`. The helper reported `records: []`, `truncated: false`,
`cycle: null` and a closure equal to SHA-256(source ‖ 0x1F) (`05cdf968…` in
`it-2`). The lexer probe gave `scan_complete: true` and `refs: []`. Unlike
DT-29 and DT-82, this miss also reaches the internal record: the resolver's
`nonliteral_imports` would be false.

**Source inspection.** In `try_match_form`
([sbpl_lex.rs](../controller/src/sbpl_lex.rs) lines 82–106), an argument
beginning with `"` goes to `try_match_keyword_form`. After the closing quote,
that function skips only space, tab, CR and LF (lines 191 and 204–206), then
requires `)` (lines 192–194). A `;` comment there produces `None`, and
`try_match_form` returns `None` at line 105 rather than `NonLiteral`. The
outer scan advances one byte (line 62), skips the string and records neither
a name nor incompleteness. The dossier rule (`dossier.rs` lines 159–171)
would give the same source `status: "complete"` with no records; that
consequence is derived from source and was not executed. The
[dossier status](../docs/RESPONSE.md#contract-dossier-imports-status) (line
3341) defines `complete` as having "exhausted the literal closure without a
reported problem." Source reading also shows that a comment between `import`
and its argument would reach the `NonLiteral` path and be flagged. The `)`
rule has existed since the lexer's introduction in `b9c02792` (2026-05-19).

**Bounding controls.** L1, `(IMPORT "<D>/marker.sb")`, failed natively with
"unbound variable: IMPORT at <input string>, line 3, column 2." Scanner and
compiler agree that this is not an import form. O2,
`#| (import "<D>/marker.sb") |#`, failed with "undefined sharp expression,"
so block comments are not accepted syntax here. Other spellings the reader may
accept, such as other whitespace bytes, were not tested natively. Related:
DT-81, DT-82 and DT-85.

### DT-85 — Inventory records include imports the compiler did not evaluate

**Executed constructed control.** Od is
`(version 1)\n(deny default)\n(if #f (import "bsd.sb"))\n`. The helper
returned `ok` with the same three Profiles records and hashes as B in DT-82,
each with `error: null`, and closure `47eb6312…055c`. The native bytecode was
456 bytes, `2cc1b84c…8b74`: identical to A and different from B. O1 places
`(if #f (import "<D>/marker.sb"))` on the allow-default base. It compiled
`ok`, although M1 shows that evaluating `marker.sb` fails, and its inventory
still contains one `marker.sb` record (`30c8c5e0…`, `error: null`). The lexer
collects literal names in every position;
[sbpl_lex.rs](../controller/src/sbpl_lex.rs) lines 233–238 assert that both
branches of an `if` are collected.

Together with DT-82 to DT-84, this shows that the records are neither a
subset nor a superset of the files the compiler incorporated. These controls
establish that the untaken import was not evaluated; whether the compiler
opened the file was not observed. The
[policy section](../docs/RESPONSE.md#read-policy-observations) (line 854) and
the reads statement (line 874) say that inventories describe their own reads,
which agrees with this result.
[Literal import evidence scope](../docs/RESPONSE.md#contract-policy-imports-native_import_agreement)
(line 879) says "Native compilation examples establish their selected literal
imports." The record does not identify those examples or say whether
"selected" covers conditional evaluation. Od's closure covers bytes from three
files that did not contribute to the compiled profile. As a result, Od and A
compile identically but have different closures. No statement found here
claims that records are compiler reads; this entry bounds what a record
establishes. Related: DT-82 and DT-84.

### DT-86 — The tests establish projection, traversal and hashing under constructed inputs, not scan completeness

The subtree [support](../docs/RESPONSE.md#contract-policy-imports-support)
(line 885) is `source_read`. It cites `resolve_imports`, `read_regular_file`,
`compute_closure_hash` and the helper's `ImportInventory`, which has no
completeness carrier, and it cites no check. The tests read here establish the
following:

- `sbpl_check_records_import_provenance_for_system_sb`
  ([cli_contract.rs](../controller/integration/cli_contract.rs) lines
  1468–1557) asserts at lines 1513–1516 that `policy_sha256 !=
  policy_closure_sha256`, with the message "closure hash should differ from
  policy_sha256 when imports were resolved." `compute_closure_hash` appends
  0x1F unconditionally (sbpl_imports.rs lines 346–349 and 353), so the two
  hashes always differ. In executed case A, which has no imports,
  `policy_sha256` is `6906c7cd…` and the closure is `f6aa3063…`. The two
  hashes differed in all 20 helper envelopes produced here. The unit test
  `closure_hash_differs_from_policy_sha_when_imports_resolved`
  (sbpl_imports.rs lines 447–453) has the same property. The test's other
  assertions require at least one record, a `system.sb` record with the
  Profiles path and a 64-character hash, `truncated: false`, `cycle: null`
  and a successful compile. It does not compare the hash with file bytes,
  recompute the closure or check transitively imported records. The
  independent recomputation here matched in every case, so the behavior
  holds, but this test does not establish it.
- `sbpl_check_verdicts_follow_the_native_compiler` (lines 619–810) runs 14
  import-free sources. It asserts empty records, `truncated: false`,
  `cycle: null` and a 64-character closure for each (lines 787–795). The
  "nonliteral parameter name" case (lines 702–708) computes a `param` name.
  The matrix contains no import form, literal or computed.
- `inventory_findings_survive_in_their_group_and_never_change_the_verdict`
  ([sbpl-check.rs](../controller/src/bin/sbpl-check.rs) lines 1013–1072)
  replaces the walk with constructed `ResolvedImports` values (lines
  987–1011). Its "errors" variant sets `failure`, its "truncated" variant
  sets `exceeded: "depth"`, and every variant has
  `nonliteral_imports: false`. The test asserts `records`, `truncated`,
  `cycle`, a closure computed by the same `compute_closure_hash`, and the
  verdict's independence from those fields. It does not assert whether
  `failure` or `exceeded` is present or absent. It establishes the three-field
  projection and verdict independence, not traversal.
- `absent_null_and_empty_params_compile_without_setup_calls` (lines 765–822)
  runs the real resolver over an import-free source. It compares the closure
  with `compute_closure_hash(source, &[])`, the function the producer calls,
  so it does not check the framing independently. The closure-hash unit tests
  (sbpl_imports.rs lines 392–453) use constructed records to check stability,
  sensitivity, order invariance and exclusion of unresolved records.
- The resolver tests (sbpl_imports.rs lines 495–725) establish cycle, diamond,
  count and depth traversal; read errors including invalid UTF-8 and a
  directory; and FIFO handling. None contains a nonliteral form or asserts
  `nonliteral_imports`. The lexer tests flag an identifier argument
  (sbpl_lex.rs lines 347–374). They contain no computed-expression argument
  and no comment inside a form.
- `import_scan_statuses_never_report_an_unscanned_closure_as_complete`
  ([dossier.rs](../controller/src/dossier.rs) lines 1426–1467) is the only
  executed check that the resolver's nonliteral flag reaches a published
  field. That field is the dossier's `status`, not the helper's inventory.
- `fallback_helper`
  ([check.py](../tests/suites/failure_boundaries/check.py) lines 415–439)
  covers only the refusal path: null groups and absent retired names.
  [checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py)
  lines 39–52 construct a helper envelope with an empty inventory to test the
  consumer's admission of the capture.

No test sends the helper a computed import argument and examines the
resulting envelope. No test compares inventory records with what the
compiler read. These conclusions come from source and test reading; DT-82 to
DT-85 hold the executed contrasts. Related: DT-29.

### DT-87 — Smaller observations on inventory hashes and wording

- An error record can contribute a closure line. U1 adds
  `(import "<scratchpad>/utf8/bad-utf8.sb")` to the allow-default base. The
  imported file contains `(version 1)\n(allow default)\n\xff\n` (30 bytes,
  SHA-256 `390ca7ba…fcd4`). The helper produced one record with that hash and
  `error: "not valid UTF-8; its imports were not scanned"`. The closure,
  `617a6312…b359`, equals SHA-256(source ‖ 0x1F ‖ "<path> 390ca7ba…"), not
  the empty-inventory framing. Native compilation failed with a diagnostic
  located in that file. The
  [closure statement](../docs/RESPONSE.md#contract-policy-imports-policy_closure_sha256)
  (line 867) says that "each successfully hashed resolved path" contributes
  and that "Failed imports remain error records and contribute no path/hash
  line." The executed record meets the first clause yet is an error record
  under the second. `compute_closure_hash` (sbpl_imports.rs lines 354–360)
  selects lines by the presence of a path and hash, not by the absence of an
  error. Executed constructed control.
- The guide (PolicyWitness.md lines 878–879) says "A performed walk over a
  source with no imports is an empty list, distinct from the null of a
  refusal." Executed cases C, M2, M4 and L2 contained imports that the
  compiler followed, and each also produced an empty list.
  [`import_inventory`](../docs/RESPONSE.md#contract-policy-check_data-import_inventory)
  (line 3534) says "an empty records list is a performed walk with no import
  records," which describes records only.
- The guide's closure description (lines 889–893), "sha256 of the source plus
  the sorted `resolved_path + " " + sha256`," omits the 0x1F separator stated
  in RESPONSE. Its statement that "Unresolved imports are excluded" also omits
  read failures and depth-limit records, which are excluded too. The separator
  framing matched all 20 executed closures. Source and executed.

### Import-inventory coverage and remaining investigative limits

The trace covered:

- the lexer's import matcher;
- the resolver's traversal and its error, bound, cycle and nonliteral
  branches;
- the helper's path from admission to inventory, including its envelope
  fields and closure framing;
- the RESPONSE subject and its authored source;
- the helper passage of the guide;
- the dossier's use of the resolver flags;
- every test in the tree that names `import_inventory`, the nonliteral flag or
  the helper.

History was traced for the lexer, the resolver flags, the helper's field
grouping and the subject statement. The executed evidence consists of 14
allow-default helper cases, 5 deny-default helper cases, 1 invalid-UTF-8 case,
lexer-probe output for every source and import file, and two identical native
bytecode runs.

Native import behavior was observed through compile diagnostics naming files
and through identical compiled bytecode, not through file-access tracing.
Identical bytecode shows equal compiled output, not which path was opened.
Untaken imports were shown to be unevaluated, not unopened. The dossier
consequences in DT-83 and DT-84 come from source and were not executed
through `policy-witness run`. The investigation did not exercise:

- search-order collisions;
- the count and depth bounds;
- unreadable and FIFO imports;
- changes to imported files between reads;
- other reader-accepted spellings;
- worker-side compilation.

Historical inspection establishes when mechanisms and statements appeared,
not how older binaries behaved. Only this record was changed. These entries
contain no repair, deduplication or choice of authoritative layer.

## Additional findings: development build identity coverage

This continuation asks which paths and bytes the `development:<sha256>` form
of `build.contract` covers. It follows the generator
([build_contract.py](../docs/build_contract.py)) and the walker it shares with
worker identity ([source_identity.py](../docs/source_identity.py)). It examines
the [Release and development forms](../docs/CONTRACT.md#contract-identity-public-forms),
[Selected build inputs](../docs/CONTRACT.md#contract-identity-public-inputs) and
[Build derivation](../docs/CONTRACT.md#contract-identity-public-derive)
statements, their authored source
([00-identity.surface.md](../docs/contract/00-identity.surface.md) lines
35–108), and the four checks the derivation support cites in
[build_contracts.py](../tests/suites/source_drift/build_contracts.py). Other
helpers were read only where they explain selection or hashing. Release-tag
selection, signing, worker identity and surface stamps were excluded. Where
the shared walker is exercised only through worker identity, the entries say
so and do not evaluate those checks. The statements were treated as claims to
check. DT-08 remains unchanged; DT-91 extends it with executed controls and
stands alone.

### Development-identity investigation identity and reproduction conventions

Source inspection used clean HEAD `458fcbb2c6a6f8caabd2b84dd2d317d83c8eafed`
on 2026-11-16; line numbers below refer to that snapshot. File hashes:
`docs/build_contract.py` `ce4a4ef2…d2c2`, `docs/source_identity.py`
`41412b7c…9946`, `tests/suites/source_drift/build_contracts.py`
`d3cc66b4…a0e5`. Every Python command ran through `tests/lib/python.sh`, the
pinned interpreter build.sh uses (Python 3.14.9, started with `-B -S`). Git was
2.54.0 (Apple Git-157); the machine reports macOS `26.7.1`, build `25G241`.
Nothing was built, no registered case was run, and the working checkout was
only read. Its `git status` was clean before and after.

**Disposable checkout.** `git clone --no-hardlinks --no-tags <checkout>
<scratchpad>/clone`, where `<scratchpad>` is
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/cc77ea91-900e-4bb1-b90b-f9633a3b29b8/scratchpad`.
No tag points at HEAD in the checkout, and the clone has no tags, so the
release form was unreachable there. Every successful control printed a
`development:` value.

**Drivers.** All are under `<scratchpad>/scripts`; temporary material has no
retention guarantee, so the decisive values are reproduced below.

- `devid_trace.py` (SHA-256 `f1a96499…8c33`) imports `build_contract` from a
  named `docs/` directory. It records `build_contract.inputs(root)` (the
  selected inventory), each selected file's SHA-256 and
  `build_contract.identity(root)`. It also recomputes the documented framing
  independently:

  ```python
  h = hashlib.sha256(b'PolicyWitness public build contract' + b'\x00')
  for p in sorted(paths):
      for part in (p.encode('utf-8'), (root / p).read_bytes()):
          h.update(len(part).to_bytes(8, 'big', signed=False)); h.update(part)
  ```

- `devid_controls.py` (SHA-256 `b28a3d6a…ebba`) ran as
  `tests/lib/python.sh -I <scratchpad>/scripts/devid_controls.py
  <scratchpad>/clone <scratchpad>/run-final`. For each control it applies one
  change to the clone. It then runs the clone's own generator as build.sh lines
  252 and 682 do (`$PW_PYTHON -B -S docs/build_contract.py`, no arguments, with
  the clone as the working directory). It runs the trace driver against the
  clone's `docs/` and records `git status --porcelain --ignored
  --untracked-files=all`. Restoration resets directory and file modes,
  removes FIFOs explicitly, empties `.git/info/exclude`, then runs
  `git reset --hard 458fcbb2` and `git clean -fdx`. The driver requires the
  restored digest and Git status to equal the baseline. Two baseline
  observations agreed, and all 25 controls restored. In an earlier run, the
  FIFO from C3d remained because Git neither lists nor cleans FIFOs. The
  restore check reported it for every later control, and explicit FIFO
  removal was added before the final run.
- `devid_copy.py` (`37529ef3…f579`) copies only the selected files with
  `shutil.copy2`, as `fixture_inputs.copy_declared` does.
- `devid_order.py` (`f9b1105b…6132`) and `devid_history.py`
  (`41a131bb…fb28`) are described in DT-92 and DT-91.

For every successful control, the generator's printed value equaled
`identity()` from the trace and the independent recomputation.

**Baselines (executed).** The working checkout, the clone, the 118-file
inventory copy and a `git archive HEAD` extraction (1112 files) each selected
the same 118 paths. Each produced
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`,
which is also the identity recorded above for the `8b5de2b2` app. The
inventory has 41 paths under `runner/Sources`, 40 under `controller/src`, 11
under `controller/tools`, 3 under `runner/Services`, 2 under
`controller/interface`, 2 under `runner/Clients`, 1 under `runner/augments`,
and 18 explicit files outside those roots. Every selected path in the checkout
is tracked. Eight tracked files under the roots are not selected:
`controller/interface/{README.md,inventory.json,joins.json,mutations.json,residue.json}`,
`controller/src/test_inputs/README.md`,
`controller/tools/sb_api_validator/build.sh` and `runner/augments/README.md`.
The only ignored file under a root,
`controller/tools/sb_api_validator/sb_api_validator`, has no suffix. All 118
paths are ASCII.

**Controls.** Each row starts from the clean clone. The expectation column
reads only the [Selected build inputs](../docs/CONTRACT.md#contract-identity-public-inputs)
statement (CONTRACT lines 80–96): the seven suffixes, the six named roots, the
explicit files, and refusal of "missing declared inputs, symlinks under the
selected roots and nonregular source objects." `ctrl` stands for the 32 bytes
`// development identity control\n` (SHA-256 `33d45db3…0279`). Git status uses
the porcelain codes; "none" means empty output.

| ID | Change | Documented expectation | Actual inventory | Generator result | Git |
| --- | --- | --- | --- | --- | --- |
| C1a | `runner/augments/exec_baseline.sb`: first `posix_spawn` → `POSIX_spawn` (`25e448d6…1761` → `96f5a1af…a436`) | selected; changes | 118; that file changed | `5ed92493…85f1` | ` M` |
| C1b | `controller/src/main.rs`: mode 0755, mtime 1000000000; bytes unchanged | paths and bytes only; unchanged | 118; no change | `bdefcb44…fb18` (baseline) | ` M` |
| C1c | rename `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift` → `PWRunnerClientSessionRenamed.swift`; bytes unchanged | path is hashed; changes | 118; one removed, one added | `2715b735…4892` | ` D`, `??` |
| C2a | add `controller/src/zz_identity_control.rs` = `ctrl`, untracked | `.rs` under a named root; included | 119; added | `ebb85798…4a0e` | `??` |
| C2b | as C2a, listed in the clone's `.git/info/exclude` | not stated | 119; added | `ebb85798…4a0e` | `!!` |
| C2c | as C2a, committed (clone HEAD `3d93fd08`, no tag) | not stated | 119; added | `ebb85798…4a0e` | none |
| C2d | `ctrl` at `runner/Sources/PWRunnerCore/.build/zz_identity_control.swift`, ignored by the tracked `runner/.gitignore` rule `.build/` | `.swift` under a named root; included | 119; added | `48bc4d12…d4a5` | `!!` |
| C2e | `runner/augments/nested/zz_identity_control.sb` = `(version 1)\n` (`edd74546…bfc7`) | "discovered under"; included | 119; added | `8114e7fe…a4d5` | `??` |
| C2f | `ctrl` as `controller/src/zz_identity_control.RS`, `…rs.orig`, `…rs~` and `controller/src/.rs` | suffix not listed; excluded | 118; no change | baseline | four `??` |
| C3a | `controller/interface/cards.rs`: first `help` → `HELP` (`9a68c368…f50a` → `5ca8a9a8…545e`) | root not named; unchanged | 118; that file changed | `062f3438…db57` | ` M` |
| C3b | `controller/interface/inventory.json`: first `help` → `HELP` (`9bb9f3d2…1ab7` → `d23eefea…6f01`) | unchanged | 118; no change | baseline | ` M` |
| C3c | `controller/src/test_inputs/README.md`: first `read.json` → `READ.json` | `.md` not listed; unchanged | 118; no change | baseline | ` M` |
| C3d | FIFO `controller/src/zz_identity_control.fifo` | "nonregular source objects refuse"; its suffix is not selected | none | exit 1, `build contract: nonregular identity source: controller/src/zz_identity_control.fifo` | none |
| C3e | symlink `controller/src/zz_identity_control.md` → `../README.md` | symlink under a selected root; refuse | none | exit 1, `build contract: symlink under identity sources: controller/src/zz_identity_control.md` | `??` |
| C3f | FIFO `controller/integration/zz_identity_control.fifo` | outside the roots; unchanged | 118; no change | baseline | none |
| M1 | delete `controller/src/test_inputs/read.json` | missing declared input; refuse | none | exit 1, `build contract: missing identity source: controller/src/test_inputs/read.json` | ` D` |
| M2 | delete `runner/augments/exec_baseline.sb`, the root's only `.sb` | root still exists; not stated | none | exit 1, `build contract: missing protocol sources: runner/augments` | ` D` |
| M3 | delete `runner/Clients/PWRunnerClient/main.swift` | not a declared path; not stated | 117; removed | `bc257d64…1aad` | ` D` |
| M4 | `controller/src/interface` mode 0000 | not stated | 113; five removed | exit 0, `60c8813b…5210` | none |
| M4b | `controller/src/interface/mod.rs`: first `mod ` → `MOD ` (`a7e9934b…e409` → `03fb3b9d…10d6`), then the directory mode 0000 | not stated | 113; the same five removed | exit 0, `60c8813b…5210` (= M4) | none |
| M5 | `controller/src/main.rs` mode 0000 | not stated | 118 listed | exit 1, `build contract: [Errno 13] Permission denied: '<clone>/controller/src/main.rs'` | ` M` |
| T1 | `controller/src/porcelain.rs`: `fn value(kind: u8` → `fn VALUE(kind: u8`, inside `#[cfg(test)] mod tests` (lines 447–450) (`70b7648c…2cb1` → `514fc59b…84a0`) | `.rs` under a named root; included | 118; that file changed | `e318ef5b…439c` | ` M` |
| T2 | `tests/fixtures/contract/ordinary_phase_reply.json`: first `"` → space (`a54f4235…077e` → `23d2d848…c5c3`) | outside; unchanged | 118; no change | baseline | ` M` |
| T3 | `tests/lib/signer_check.py`: first `import` → `IMPORT` (`83846e9b…f8b5` → `bbc5cb21…aabc`) | named helper; included | 118; that file changed | `0cc4a482…0a0e` | ` M` |
| T4 | `runner/Tests/PWRunnerCoreTests/TestKit.swift`: first `import` → `IMPORT` (`9be1c908…94fa` → `501e845e…cba7`) | outside the roots; unchanged | 118; no change | baseline | ` M` |

Full digests: C1a `5ed92493d53d2d2ec8fa9b0b26af8742ff9b262869ee0f8f301d643e767f85f1`,
C1c `2715b7355e42b46b983542999cb4e596054a660ba90109ba2b0963de0c734892`,
C2a–C2c `ebb8579813a122d0b6a12aec1bb5ff63e34e0f85bb14dbec006b0fdca9064a0e`,
C2d `48bc4d12445417d970422a3c6e966ea0701bcced42b5952200360338d801d4a5`,
C2e `8114e7feb67d9a9dfaaf2e1f2a15286d50ced45a0478504c0272f3194be0a4d5`,
C3a `062f34380a313fded747bbd69d252ad5af9f4e24d07330c697b5e637f105db57`,
M3 `bc257d64f82dba805d4742e4717b596f0437f65a9400e70da59cf9332b971aad`,
M4 and M4b `60c8813b979c88e1915604ceaa171de05811fa8090a1b53745080ffcfe735210`,
T1 `e318ef5bc56fba1aa90c32a12da4e07f9f265483b4a3c5203a6538607c28439c`,
T3 `0cc4a4828ebab33f5acc82af00cc71c1713afc813bfbaad6b27d65fe005a0e0a`.

The three requested contrasts are C1a (bytes of an existing selected file),
C2a (an addition that is eligible under the documented rules) and C3b/C3c (a
file outside the stated selection). The other rows separate path, metadata,
Git status, object kind, readability and test-code effects.

### DT-88 — The selected inventory is whatever is on disk under the roots; Git tracking and ignore status do not enter it

**Statements examined.** "`development:<sha256>` identifies the selected
source paths and bytes in other source trees" (CONTRACT line 68; authored at
surface line 48); files "discovered under" the named roots (line 80; surface
line 63); and "Discovery uses the same inventory in a checkout and a source
copy" (line 92; surface line 75). The generator's comment (build_contract.py
lines 21–23) says the declaration "is independent of Git and applies equally
to source copies."

**Source inspection.** `source_paths` (source_identity.py lines 17–28)
walks each root with `Path.rglob('*')`. It keeps regular files whose final
suffix (`path.suffix`, compared case-sensitively) is in `SUFFIXES`, and adds
the explicit `FILES` regardless of suffix (line 7). The walk includes hidden
files and directories. No Git command takes part in selection or hashing. Git
is consulted only after the digest is computed, for the release decision
(build_contract.py lines 82–90).

**Executed.** C2a, C2b and C2c place the same path and bytes in an untracked,
an ignored and a committed state. The three inventories and digests are
identical. C2d puts an eligible file in a directory that the tracked
`runner/.gitignore` ignores. The file enters the inventory, and Git reports it
only when ignored files are requested. C2f shows that the suffix rule uses the
final suffix exactly: `.RS`, `.rs.orig`, `.rs~` and a file named `.rs` are
excluded. C3d (DT-90) shows that an object Git does not list at all can still
determine the result.

**What "the same inventory" covers.** At clean HEAD, the checkout, a clone,
an inventory copy and a `git archive` extraction gave the same 118 paths and
digest. During C2b and C2d, the clone's HEAD was still `458fcbb2`. An archive
of that commit therefore contains neither added file and corresponds to the
baseline digest. The clone instead produced `ebb85798…` or `48bc4d12…`. A
development identity thus identifies the files present in the working tree,
not a commit, and the same rule can select different sets in a checkout and a
source copy of one commit. The statements do not say whether untracked or
ignored files are selected. The check named
`test_source_copies_ignore_artifacts_and_release_checks_actual_bytes`
(build_contracts.py lines 181–198) excludes its two artifacts by suffix:
neither name has one (line 185). Its first assertion (line 187) runs before a
repository exists. Its `.gitignore` (line 188) prepares the later release
step. No cited check adds an eligible untracked or ignored file.

**History.** The walk, suffix rule and Git independence are unchanged since
`cbf5f298` (2026-11-09, v0.3.6). `source_identity.py` has only that commit.
The v0.3.6 CONTRACT said "The source scope uses declared language/resource
suffixes and explicit build helpers equally in Git checkouts and source
copies." Before v0.3.6, the public identity was a set of generated contract
versions (`git show v0.3.5:build.sh` line 226, "Checking contract versions"),
not a source digest. Related: DT-89, DT-90 and DT-94.

### DT-89 — An unreadable directory under a selected root is omitted without refusal, so different bytes can share one development identity

**Statements examined.** "Missing declared inputs, symlinks under the selected
roots and nonregular source objects refuse derivation" (CONTRACT lines 92–94;
surface lines 75–77), and the development form's identification of "the
selected source paths and bytes" (line 68).

**Executed.** In M4, `controller/src/interface` (five selected `.rs` files)
had mode 0000. The generator exited 0 with `development:60c8813b…5210` and no
diagnostic, and the inventory had 113 paths. In M4b, one of those files,
`mod.rs`, changed bytes before the directory became unreadable. The generator
printed the same `60c8813b…5210`. The working trees in M4 and M4b differed in
a file under a named root and selected by suffix, yet received one identity.
For contrast, M5 made one selected file unreadable. That file remained in the
inventory, and reading it failed with exit 1 and the raw errno text. M3
deleted a tracked file the walk would have selected. The inventory shrank to
117 and the digest changed without refusal.

In a separate run in the M4 state, `git status --porcelain --ignored
--untracked-files=all` exited 0 with empty standard output. Standard error
listed `controller/src/interface/<name>: Permission denied` for all five files
and `warning: could not open directory 'controller/src/interface/': Permission
denied`. The generator emitted nothing comparable.

**Source inspection.** The walker checks existence only for roots and
declared files (source_identity.py lines 15–16). It refuses a root with no
selected file (lines 26–27), but has no check for directories it could not
list. The skipped directory was observed with the pinned Python 3.14.9;
pathlib's handling of listing errors was not traced in Python's source.

**Limits.** The investigation did not establish whether a packaged build
could compile with such a directory. The Rust modules in this example would be
unreadable to the compiler too. The same derivation also supplies Meson's
`--swift-stdout` context and the fixture inventories built from
`build_contract.inputs(ROOT)` (DT-93). Those paths were not executed in this
state. Related: DT-88 and DT-90.

### DT-90 — Refusal depends on object kind for every entry under a root, and only declared paths and empty roots count as missing

**Statement examined.** The same refusal sentence (CONTRACT lines 92–94).

**Source inspection.** Symlinks are refused for any path component between
the repository root and a root or declared file (source_identity.py lines
8–14), and for every walked entry (lines 20–21). Any walked entry that is
neither a regular file nor a directory is refused (lines 24–25). Both checks
apply before the suffix filter can exclude an entry, because line 22 tests the
suffix only for regular files. Missing-input refusals come only from the
existence check for roots and declared files (lines 15–16), from a root with no
selected file (lines 26–27), and from a declared path that is not a regular
file (lines 29–31).

**Executed.** C3d placed a FIFO named `.fifo` in `controller/src` and was
refused. The same FIFO in `controller/integration`, outside the roots (C3f),
changed nothing. The statement's "nonregular source objects" therefore
describes a refusal that also covers objects whose suffix is not a source
suffix. Git listed neither FIFO, even with ignored and untracked files
requested. A checkout whose status is empty can therefore fail derivation, and
`git clean -fdx` does not remove the cause. C3e's symlink named `.md` was
refused, matching "symlinks under the selected roots."

For missing inputs, M1 removed a declared file and was refused. M2 left
`runner/augments` present but removed its only `.sb`; the message
`missing protocol sources: runner/augments` uses vocabulary from the walker
shared with worker identity (docstring, line 1), although that root has no
protocol role. M3 removed a tracked, discoverable file and was not refused.
M4 (DT-89) was not refused. M5 was refused by an `OSError` while reading, not
by the walker's checks.

**Checks.** No public-contract check exercises a missing declared input, an
empty root, a nonregular object, an unreadable file or an unreadable
directory. The messages `missing identity source`, `missing protocol sources`
and `nonregular identity source` occur in the tree only in
`source_identity.py`. Symlink refusal is checked by replacing `main.rs` with a
symlink and matching `ValueError` on `symlink` (build_contracts.py lines
255–259). The worker identity's
`test_symlinks_under_identity_sources_are_refused` (lines 128–143) runs the
shared walker with worker roots; it is outside this remit. Related: DT-88,
DT-89 and DT-93.

### DT-91 — Executed: a change under `controller/interface` changes the development identity although the inputs statement omits that root

This entry extends DT-08 with executed contrasts and history.

**Statement and source.** The inputs statement names six discovery roots
(CONTRACT lines 80–82; surface lines 63–65). `DIRECTORIES` names seven
(build_contract.py lines 15–16). The baseline inventory contains
`controller/interface/cards.rs` and `controller/interface/inventory.rs`.

**Executed.** C3a changed four bytes in `cards.rs`. Under the statement this
file is outside the selection and the identity should not change. The
inventory included it, and the digest changed to `062f3438…db57`. C3b changed
`controller/interface/inventory.json`, which is outside both selections; the
digest stayed at the baseline.

**Why these files reach shipped bytes (source inspection).**
[build.rs](../controller/build.rs) lines 24–27 compile `interface/cards.rs`
and `interface/inventory.rs`. Lines 72–80 render the help cards into
`OUT_DIR`, and [help.rs](../controller/src/help.rs) lines 11–14 embed them
with `include_str!`. Under the documented list, a help-card edit would
therefore be a shipped change that the stated selection does not cover. Under
the code, the identity covers it. `inventory.json` is read at build.rs lines
69 and 87–97, where a stale copy stops the build. C3b is thus an edit the
build refuses while the identity ignores it. That is a generated-output
freshness check, not a selection rule (DT-93).

**History.** `devid_history.py` ran over every commit in `f6551bf9^..HEAD`
that touched `build_contract.py` or `00-identity.surface.md`. For each commit,
it parsed `DIRECTORIES`, `FILES` and `SUFFIXES` with `ast`, then compared them
with the backticked names in the paragraph beginning "The development digest
includes" (helper names relative to `tests/lib`):

| Commit | Date | In code but not in the statement |
| --- | --- | --- |
| `f6551bf9`, `eac1482e`, `5c1c63dc`, `d18d4925`, `8435e5d3` | 2026-11-10 to 11 | none |
| `d04a3819` | 2026-11-13 | `FILES`: `controller/src/lessons/create.json`, `controller/src/lessons/capture_typo.json` |
| `ba3a9043` | 2026-11-14 | none; the lesson files were replaced by `controller/src/test_inputs/read.json`, which the statement gained in the same commit |
| `b16f32d0` | 2026-11-15 | `DIRECTORIES`: `controller/interface` |
| `33806e55` | 2026-11-15 | `DIRECTORIES`: `controller/interface` |

The statement never named an input missing from the code, and the suffixes
always agreed. The explicit list first appeared in `f6551bf9`, which is in
v0.3.7 but not v0.3.6, and code and statement agreed at v0.3.7. `b16f32d0`
created `controller/interface` and added it to `DIRECTORIES`. Its edits to the
identity surface concern only version dispatch. Neither divergence occurs in
a tagged release. `b16f32d0` precedes `2fcf9dbc`, consistent with DT-08's
statement that the omission predates the documentation-trace reorganization.

**Checks.** No check compares the statement's list with the code. Every test
that uses `build_contract.inputs` copies whatever the code selects into a
fixture: build_contracts.py line 215, generators.py lines 982 and 1021,
check_release_publish.py lines 61 and 264, build_refusals.py line 1944 and
fixture_inputs.py line 97. Such fixtures cannot reveal a difference between
the code and the documented list. Related: DT-08 and DT-93.

### DT-92 — The digest framing matches the statement; the statement leaves the path order and the metadata scope to the code

**Statement examined.** The statement defines the digest as SHA-256 with
domain prefix `PolicyWitness public build contract`, followed by a NUL byte.
"For each sorted repository-relative path, the generator appends the UTF-8
path and file bytes, each preceded by its unsigned eight-byte big-endian
length" (CONTRACT lines 68–72; surface lines 48–52).

**Executed.** The independent recomputation equaled the generator for all
four baselines and all 20 successful controls. C1c renamed a file without
changing its bytes and changed the digest, so path names are hashed. C1b
changed mode and mtime only and did not change the digest. Git reported
` M` for the mode change. Both results agree with "paths and bytes."

**Order.** The generator sorts Python strings by code point
(source_identity.py line 32), which for UTF-8 is also byte order.
`devid_order.py` recomputed the baseline under alternative orders. Code-point,
UTF-8 byte and per-path-component orders all produce `bdefcb44…` for this
inventory. Case-folded order moves 109 of 118 positions: the generator begins
with `Info.plist`, while case-folded order begins with `build.sh`. That order
gives `10ce11c4…`. The statement says "sorted" without naming the order.
Unicode normalization of non-ASCII names was not exercised because every
current path is ASCII.

**Determinism.** The checkout, the clone, the inventory copy and the archive
have different absolute roots and gave one digest. Two consecutive baselines
in the clone also agreed.

**Checks.** No test asserts the domain prefix, length encoding, order, an
expected digest value or an independently recomputed digest. The prefix string
occurs only at build_contract.py line 75. The cited checks compare outputs of
`identity()` with one another (DT-93). Related: DT-93.

### DT-93 — The cited checks establish byte sensitivity for four files, two suffix exclusions and symlink refusal, using fixtures built by the code under test

The [derivation support](../docs/CONTRACT.md#contract-identity-public-derive-support)
(CONTRACT line 109; surface lines 99–108) pins "Selected-source mutations
change the digest." The Selected build inputs definition has no support block
of its own; it is used by the Build derivation statement. Reading the four
cited checks gives the following:

- **Fixture construction.** `checkout()` (build_contracts.py lines 209–217)
  copies `build_contract.inputs(ROOT)` with `fixture_inputs.copy_declared`
  (fixture_inputs.py lines 105–130). That is the inventory selected by the code
  under test from the developer's checkout, and only that inventory. Unselected
  files under the roots, such as `inventory.json` or the READMEs, are absent
  unless a test writes them.
- **Selection.** `test_source_copies_ignore_artifacts_and_release_checks_actual_bytes`
  writes two unsuffixed names and asserts an unchanged identity (lines
  185–187). `test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release`
  asserts that a root-level `notes.md`, both uncommitted and committed, leaves
  the development digest unchanged (lines 241–244), and that a symlinked
  `main.rs` is refused (lines 255–259). No cited check adds an eligible file,
  renames or deletes a selected file, touches `controller/interface`, places a
  nonregular object, or makes a path unreadable.
- **Byte sensitivity.** Lines 246–254 append `\n` to four files and require
  each digest to differ from the previous one. The second name,
  `runner/augments/mach-register.sb`, does not exist. `git log --all --
  runner/augments/mach-register.sb` is empty, so it never existed in this
  repository's history. The loop silently substitutes
  `next((root / 'runner/augments').glob('*.sb'))` (lines 249–250), which is
  `exec_baseline.sb` at HEAD. The literal dates from `cbf5f298`.
- **Determinism.** The same test requires the loose digest to survive
  `git init`, a commit and a lightweight tag (lines 232–237), and a
  documentation-only commit (line 244), in one directory. No public-contract
  check compares digests across locations. The worker identity has such a
  check, outside this remit.
- **Framing.** No check covers framing (DT-92).
- **Swift context.** `test_swift_context_refuses_a_different_compilation_identity`
  (lines 200–207) asserts only exit statuses for three `PW_BUILD_CONTRACT`
  values. It does not concern selection.
- **Pre-sign guard.** `test_presign_contract_guard_refuses_changed_sources`
  (lines 271–291) executes the build.sh fragment and requires refusal after
  `main.rs` gains a line. Source inspection shows the guard compares two
  whole-tree derivations (build.sh lines 252 and 682–686). An edit that is
  present during compilation and reverted before line 682 leaves the values
  equal. The CONTRACT sentence "The pre-sign comparison refuses a
  selected-source change during compilation" (lines 105–106) covers changes that
  persist until the second derivation. This was not executed.
- **Generated-output freshness is separate.** C3b's `inventory.json` edit
  leaves the digest unchanged, while build.rs refuses a stale copy. Generated
  sources under the roots are selected, but the generator inputs outside
  them, such as `docs/porcelain.json`, are not. Their agreement belongs to the
  build's generator checks (BUILD line 145), not to identity.
- **Compiler consumption.** No check compares compiler-consumed files with
  this inventory. `closure_problems` in
  [native_sources.py](../tests/lib/native_sources.py) (lines 184–215) compares
  Ninja's dependency log with `identity_inputs` (lines 152–156), which loads
  the worker identity generator's `source_paths`, not `build_contract.inputs`.

These tests establish byte sensitivity for four selected files, two suffix
exclusions, one documentation exclusion, symlink refusal and Git-state
stability. They do not establish discovery of additions, path sensitivity,
the refusal set, Git independence, agreement between the statement's list and
the code, or the framing. Related: DT-38, DT-88 to DT-92.

### DT-94 — Selection follows roots and suffixes, not compiler use; test code is partly selected

**Statements examined.** REQUEST line 326 says "A shipped-source edit changes
the development identity, including an optional addition or an implementation
fix." Its v0.3.6 ancestor was "Every shipped-source change changes a
development contract." The v0.3.6 CONTRACT (`cbf5f298`) also said "Ordinary
documentation and test edits do not change that digest"; `f6551bf9` removed
that sentence. The generator comment (build_contract.py lines 22–23) says
"New source files in these languages and bundled resources are discovered;
executables, editor/OS files and documentation are not compiler inputs."
BUILD line 147 describes the check stage as reading "shipped sources and build
inputs through docs/build_contract.py."

**Executed.** These changes altered the digest without altering a shipped
input:

- T1 edited a `#[cfg(test)]` module.
- T3 edited a named `tests/lib` helper.
- C2a added a `.rs` file named by no `mod` declaration.
- C2e added a nested `.sb`. build.sh lines 597–603 copy only the top-level
  `runner/augments/*.sb` into the bundle.

T2 changed a fixture embedded by `include_str!` in the test-only
`reply_fixtures` module (main.rs lines 27–28; reply_fixtures.rs lines
245–248). T4 changed a Swift unit-test source. Neither changed the digest. The
inventory therefore includes some test code, unreferenced files and unbundled
resources, while excluding data that test code compiles in. Source inspection
also shows that `controller/tools/sb_api_validator/debug.ent` is selected by
suffix. Its only user is the manual helper `controller/tools/sb_api_validator/build.sh`
line 6, whose output BUILD line 1028 describes as git-ignored and for direct
local use.

**History.** At v0.3.6, `FILES` already named `tests/build_equipment.py`,
`tests/build-evidence.py` and five `tests/lib` helpers, and 25 files under
`controller/src` contained `#[cfg(test)]` (`git grep -l` at v0.3.6). The
v0.3.6 sentence about test edits therefore did not describe that release's
selection. T1 and T3 exercise the same unchanged rule at HEAD. The current
statements make no claim about test edits.

**Shipped inputs outside the selection (source inspection; none found).**
The production `include_str!` targets are `test_inputs/read.json`, which is in
`FILES`, and the `OUT_DIR` help cards rendered from `controller/interface`.
The other `include_str!` sites are in `#[cfg(test)]` code, including
utils.rs line 233, `porcelain.rs`'s test module from line 448, `sbpl-check.rs`'s
test module from line 449 and the `reply_fixtures` module. The bundle copies
`Info.plist`, PWRunner's `Info.plist` and `Entitlements.plist`, the top-level
augments and compiled outputs, all of which are selected. Every file name
quoted in `meson.build` is selected except the generated
`PWBuildContext.swift`. Measured against the documented list rather than the
code, `controller/interface/cards.rs` is the exception (DT-91). This was not a
build-closure audit. Cargo registry sources, the SDK, toolchains and the
environment are outside the selection by statement. Related: DT-88 and DT-91.

### Development-identity coverage and remaining investigative limits

The trace covered:

- the generator's selection declarations and digest construction;
- the shared walker's existence, symlink, nonregular, empty-root and suffix
  rules;
- the forms, inputs and derivation statements and their authored source;
- REQUEST's contract-change sentence and the v0.3.6 predecessors;
- the four cited checks, with their fixture construction;
- every test that calls `build_contract.inputs`;
- build.sh's two derivation calls and the build.rs and help.rs path for help
  cards.

History covered every commit since the explicit list appeared, the origin of
the walker and of the v0.3.6 statement, and the v0.3.5 mechanism that preceded
it. The development digest has no predecessor before v0.3.6, so no earlier
discrepancy exists for this form. The executed evidence consists of 25
controls in a disposable clone and four baseline derivations. It also includes
a reordering recomputation, a historical code/statement comparison and one Git
observation in the M4 state.

The investigation did not exercise:

- non-ASCII or normalization-differing path names;
- case-only name collisions;
- a directory symlink at a root;
- the release form or the release byte check, which were excluded;
- `--swift-stdout`;
- Meson's invocation;
- a build in any changed state.

DT-89's unreadable-directory behavior was observed with one Python version;
its effect on a build was not established. The pre-sign window in DT-93 and
the shipped-input survey in DT-94 come from source inspection. Historical
inspection establishes when declarations and statements appeared, not how
older builds behaved. Only this record was changed. These entries contain no
repair, deduplication or choice of authoritative layer.

## Additional findings: compiled-profile receipts for an ordinary `run` request

This continuation follows one compiled-profile receipt through the ordinary
(non-actor) request form. It covers the capture declaration, the worker's
native production, the host's receipt assembly and controller admission for
`run`. It starts from the
[`capture_compiled_profile`](../docs/REQUEST.md#contract-policy-spec-capture_compiled_profile)
and [`capture_nonce`](../docs/REQUEST.md#contract-policy-spec-capture_nonce)
declarations (REQUEST lines 732–733), the
[Compiled-profile receipts](../docs/RESPONSE.md#contract-profile) section
(RESPONSE lines 2516–2638), and its authored owner,
[35-profile.surface.md](../docs/contract/35-profile.surface.md). It also reads
the receipt's restatements in ARCHITECTURE (lines 437–442, 569, 612 and 637),
LIMITS (lines 191 and 364) and the
[guide](../docs/PolicyWitness.md#compiled-object-receipt-opt-in) (lines
718–757). Shared helpers were followed where they carry a receipt input or
projection. Actor execution, BYOXPC and `runner verify` were excluded. Where a
cited check uses an actor record or a loop shared with actors, the entry says
so. The statements were treated as claims to examine. Close relatives in this
record are DT-37 (the form of the run label-failure effect) and DT-81 to DT-87
(import inventory, including a native bytecode probe). The new entries stand
alone and cross-reference them.

### Receipt investigation identity and reproduction conventions

Source inspection used clean HEAD `eccd5de97fa68752432a6108a44bc102a9fb5d23`
on 2026-11-16; line numbers below refer to that snapshot. File hashes:
`runner/Sources/PWRunnerCore/CWorker.swift` `93138d53…f27e`,
`controller/tools/pw_probe_runner/pw_profile_capture.h` `d598ae17…91b8`,
`controller/src/porcelain_admission.rs` `19f071e8…230f`,
`runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift`
`4453ac78…11d0` and `docs/contract/35-profile.surface.md` `e059cd62…4013`.
The machine reports macOS 26.7.1, build 25G241 (Darwin 25.6.0). Python ran
through `tests/lib/python.sh` (Python 3.14.9) with `-I`.

**Build used for live observations.** All live observations used
`dist/PolicyWitness.app`. Its `policy-witness --version` reports commit
`8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855` and contract
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
`codesign --verify --deep --strict` passed, and the team is `42D369QV8E`.
`docs/build_contract.py` printed the same development identity for HEAD.
`git diff --stat 8b5de2b2 HEAD` touches only `records/`, the retired plan and
one line of `tests/suites/preflight/opt_in/build_refusals.py`. No runner,
controller, worker or fixture source changed. Nothing was rebuilt.

**Registered cases.** The pinned pytest target under `.tmp/pytest/` was
absent, and `tests/run.sh --list` refused without it, so
`tests/setup-pytest.sh` ran first. Then
`PW_TEST_OUT_DIR=tests/out/runs/profile-receipt-trace tests/run.sh --case
runner_outcome_bad_request/accepted_input_contract --case
runner_unit/pwrunner_core_unit_executable --case unit/rust.unit` produced run
`20261116T192345Z_79fbbaf4` against `dist/PolicyWitness.app`. All three cases
passed, each with `system_sleep_ms` 0.

- The Swift batch reported 606/606. Its log lists all 20 tests in the group
  `Compiled-profile capture: bounded worker receipt` as `ok`.
- The Rust log lists three receipt tests as `ok`:
  `compiled_profile_labels_determine_the_public_admission_outcome`,
  `compiled_profile_context_is_gated_after_the_response_version` and
  `typed_profile_context_gate_includes_actor_captures_and_degradation`.

This development output is in the gitignored `tests/out/runs/` and is
disposable under the retention policy. The decisive values are reproduced
below.

**Direct probes.** The drivers are under `<scratchpad>/scripts`, where
`<scratchpad>` is
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/0a1dcc1e-63de-41a4-a483-053ae1a48be4/scratchpad`.
Scratch material has no retention guarantee.

- `receipt_probe.py` (SHA-256 `88fbe2dd…9c5f`) writes one ordinary request per
  probe and runs `policy-witness run <request>`. It records stdout, stderr,
  the exit status and whether the target exists. Each request has one step: a
  `file-write-create` query and a `file`/`create` attempt on a fresh path.
- `receipt_check.py` (`3d4695e3…97ac`) reads the saved envelopes. It decodes
  `bytecode_b64` with `base64.b64decode(…, validate=True)` and recomputes the
  length and SHA-256. It also hashes the request's `sbpl_source`. The
  parameter digest is recomputed with a separate implementation of the
  documented framing: `struct.pack('<I', …)` lengths, sorted pair digests and
  a LE32 count prefix.
- `receipt_mutations.py` (`b0def4a2…eada`) runs `consumer.validate` and
  `consumer.admitted_reply` from `tests/lib/consumer.py`. It reads the saved
  envelopes and edited copies of B's saved `runner_result`.
- `receipt_repeat.py` (`cd736919…03de`), `receipt_import.py`
  (`d08277c3…ab4e`) and `receipt_compile_fail.py` (`aa6b47a4…437b`) are
  described in DT-97, DT-98 and DT-100.

**Contrasts (executed).** Every probe used the dist app above.

| Probe | Request | Exit, outcome and worker | Receipt |
| --- | --- | --- | --- |
| A | no capture fields; source `(version 1) (allow default)` | 0, `finished`; worker 7540 exit 0 | key absent from the JSON and from the retained host bytes |
| B | as A, plus capture with nonce `179c2dcf…329d` | 0, `finished`; `sandboxed_after_apply: true`; worker 7545 exit 0 | `captured`; 492 bytes `b2056ef2…97e0`; source `c3f48dc8…74b3` (27 bytes); parameters `df3f6198…1119` (count 0); `request_nonce` = request; `worker_pid` 7545 |
| B2 | capture; 96-byte source using `(param "ROOT")`; parameters `ROOT=/etc`, `Z=é` | 0, `finished`; worker 7549 exit 0 | `captured`; 524 bytes `a2b35cd2…d4b0`; source `ad8bc3d2…039a`; parameters `2a4f1d69…95fd` (count 2); `worker_pid` 7549 |
| C | as B, plus `_test_overrides.worker_post_apply_kill_signal: 9` | 1, `runner_failed`; `sandboxed_after_apply: true`; worker 7554 `term_signal` 9, `done_observed: false`; target created | only `{status: unavailable, reason: worker_not_complete, worker_pid: 7554}` |

B and B2 passed every independent comparison:

- The decoded length equals `bytecode_length`, and the decoded SHA-256 equals
  `bytecode_sha256`.
- `source_sha256` equals the SHA-256 of the request source and the reply's
  `policy_sha256`. For B2 it also equals the dossier's
  `augmentation.original_sha256` and `applied_sha256`.
- `source_length` equals the source byte count.
- `params_sha256` equals the independent recomputation.
- `request_nonce` equals the request's nonce, and `worker_pid` equals
  `runner_subprocess.pid`.

`consumer.validate` returned no errors for any of the four envelopes.
`consumer.admitted_reply` decodes the receipt independently from the retained
host bytes (`runner_client.transport.runner_reply.data_base64`). That receipt
equaled the controller's JSON receipt in all four envelopes, including its
absence in A. The registered case's `repair-cli-capture-2-enabled` and
`repair-xpc-capture-2-enabled` receipts (worker PIDs 13039 and 13043) carried
the same 492 bytes, `b2056ef2…97e0`, and passed the same length and digest
check. Its `capture_worker_death` receipt was `{unavailable,
worker_not_complete, worker_pid 13075}`.

The controlled failure is the existing `worker_post_apply_kill_signal: 9`
control. The registered case runs it too (contract.py lines 498–512). Among
existing tests, it is the only ordinary-form live control that asserts an
`unavailable` receipt. No other guard was forced live.

Full digests:

- B bytecode
  `b2056ef25b6c4e72bcd45bb018452bde93d05afcbdb9813fee8698551cf397e0`
- B2 bytecode
  `a2b35cd2cc1ea2174fe04ed7e97889f387d3a42da3acf309841efd007f30d4b0`
- B2 parameters
  `2a4f1d69b5f51c89ed0f08aaae8f5996737877b49463a4f2baae736009c195fd`
- zero parameters
  `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`,
  which is the SHA-256 of four zero bytes

### DT-95 — The controller checks the status and two constant labels; a `captured` receipt that contradicts its request and its own fields is admitted as `finished`

**Statements examined.** The labels rule (RESPONSE lines 2607–2620; surface
lines 299–337) says: "After public producer admission and reply-capacity
checks, the controller applies these conditions to every present receipt…. The
retained nonce, bytecode, digests, lengths and counts remain the host's
assertions; their production checks belong to the host capture rule." The
`request_nonce` field (line 2540) adds that the label check has no
request-nonce operand. Two receipt conditions are stated as requirements with
no checking actor:

- Captured byte extent: when captured, `bytecode_length` is present, greater
  than 0 and at most 1,048,576 (line 2554; surface line 76).
- Captured payload extent: the decoded length of `bytecode_b64` equals
  `bytecode_length` (line 2560; surface line 91).

Receipt presence (line 2567) is conditioned on "Capture was requested for this
worker." The Successful receipt effect withholds `reason` (line 2602).

**Source.** `admission_problem`
([porcelain_admission.rs](../controller/src/porcelain_admission.rs) lines
1308–1331) first runs the geometry check. It then examines the top-level
receipt and each actor receipt. It requires `status` to be `captured` or
`unavailable`. A captured receipt needs `producer == "worker"` and
`capture_stage == "before_apply"`, and an unavailable receipt may carry
neither label. `reply_contract` and `admit_reply`
([run_flow.rs](../controller/src/run_flow.rs) lines 99–107 and 330–355) turn
a problem into `malformed_runner_response`. The binary reader
([porcelain_records.rs](../controller/src/porcelain_records.rs) lines 51–104)
requires only `status` and `worker_pid` and accepts any subset of the other
twelve fields.

No controller code compares a receipt with:

- the delivered request;
- `runner_subprocess.pid`;
- `policy_sha256`;
- the dossier;
- its own bytes.

The independent consumer's `_validate_capture`
([consumer.py](../tests/lib/consumer.py) lines 575–588) applies the same three
conditions, and `admitted_reply` (lines 1027–1052) uses only those. The host's
`contextProblem`
([PWRunnerProfileCapture.swift](../runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift)
lines 31–44) applies the same check before encoding.

**Executed, constructed (the cited check).**
`compiled_profile_labels_determine_the_public_admission_outcome` (run_flow.rs
lines 2967–3013) sends the request built by `request_file` (lines
2608–2623): `"policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow
default)\n"}`. The request has no capture fields. The `captured` row of
[compiled_profile.json](../tests/fixtures/contract/compiled_profile.json)
carries:

- `request_nonce` `0123456789abcdef0123456789abcdef`;
- `source_length` 24, although the request source is 28 bytes with SHA-256
  `d130f968…765c`;
- `source_sha256` and `params_sha256` each set to 64 `f` characters, with
  `parameter_count` 0, whose framing digest is `df3f6198…1119`.

Its bytes `ChQe` (`0a141e`) do match its `bytecode_sha256` `6951bbd9…2925`.
For this row the test requires exit 0, `ok: true`, `finished` and present
diagnostics, and it passed in run `20261116T192345Z_79fbbaf4`. The receipt was
admitted although:

- the request did not ask for capture;
- the request could not carry a nonce, because a nonce without capture is
  `inapplicable_field` (ProbeRunner.swift lines 64–70);
- its source fields disagree with the request.

`typed_profile_context_gate_includes_actor_captures_and_degradation`
(porcelain_admission.rs lines 2732–2780) asserts that `admission_problem`
returns none for a `captured` receipt with no nonce, type, length, bytes or
digests. That receipt is on an actor record, but the loop is the same.

**Executed, saved-reply mutations read by the independent consumer.** Each
change below was applied separately to B's saved `runner_result`, and
`consumer.validate` returned no errors for each:

- different 492 bytes with the length and digest unchanged;
- `bytecode_b64`, `bytecode_sha256` and `bytecode_length` removed;
- `bytecode_length` set to 2,000,000 or to 0;
- `request_nonce` replaced or removed;
- `worker_pid` set to 1;
- `profile_type` set to 7;
- `reason` added to the captured receipt;
- `source_sha256` zeroed;
- B's receipt inserted into A's reply, which did not request capture;
- an `unavailable` receipt carrying `bytecode_b64` and `bytecode_length`;
- an `unavailable` receipt without `reason`.

As controls, `status: "future"` and `producer: "host"` were rejected, with
`invalid compiled_profile status` and `compiled_profile requires
worker/before_apply context` respectively. These are edits of saved JSON read
by the Python consumer, not controller executions. The controller's outcome
for the same edits is inferred from the source and the two constructed tests
above.

**Where the receipt conditions are checked.** No reader checks the two extent
conditions, or presence against the request. Specific live tests assert them
on their own outputs:

- [contract.py](../tests/suites/runner_outcome_bad_request/contract.py) lines
  322–332 check the nonce, the PID against `runner_subprocess.pid`, the source
  digest, the decoded length and digest, and zero parameters. Lines 430–435
  and 483–488 check that the receipt is absent when capture was not requested.
- [check_response_footprint.py](../tests/suites/witness_contract/check_response_footprint.py)
  lines 235–241 check the decoded length and digest.
- [guide_workflows.py](../tests/suites/witness_contract/opt_in/guide_workflows.py)
  lines 461–470 check the receipt from the guide workflow.

CONTRACT's checker index (CONTRACT line 2793) lists only `status`, `producer`
and `capture_stage` under the labels rule. The two field conditions are
credited only to the source-read owner over the Receipt subject (RESPONSE
line 2636).

**History.** At v0.3.5 the controller applied the same check (`git show
v0.3.5:controller/src/porcelain_admission.rs`, lines 1299–1316). The v0.3.5
guide said: "Readers require the nested receipt version and the exact
producer/stage values for a captured receipt." Line 308 of the v0.3.5 tree's
`RELEASE-STAMPED-CONTRACTS-PLAN.md` expected that, for a "detached
compiled-profile receipt", a "wrong nonce, worker or hash binding still
fails". Which reader that plan row meant was not established. No reader at
v0.3.5 or HEAD makes those comparisons. Related: DT-96 and DT-101.

### DT-96 — The host decoder writes `producer` and `capture_stage` as constants; no record observes who copied the bytes or when

**Statements examined.** "`worker` on a captured receipt identifies the
component that captured the bytes." "`before_apply` on a captured receipt
identifies when the worker captured the bytes." (RESPONSE lines 2538–2539;
surface lines 55 and 59.) The labels rule checks these two values. The guide
(lines 739–741) says that the controller "requires the exact producer/stage
labels for a captured receipt", and that "This label admission and the host's
byte/input checks are separate boundaries."

**Source.** The worker's capture record `pw_shm_capture_t`
([pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
lines 575–588) holds completion, status, type, length, PID, source length,
parameter count, three digests and the nonce. It has no producer or stage
field. On its single success path, `decodeProfileCapture`
([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) lines 712–716)
writes the literals `producer: "worker", capture_stage: "before_apply"`.

The stage is true because of the worker's straight-line order:

1. compile (pw_probe_runner.c line 1574);
2. capture (lines 1594–1601);
3. an optional pre-ready sleep;
4. the ready byte;
5. `sandbox_apply` (line 1641).

The worker's progress word records `PW_OP_CAPTURE` (6). It is one value that
later operations overwrite (abi line 389). In probe C it read operation 9
(attempt), stage 2, at collection.

**Consequence for the check.** The controller's two label comparisons can
detect only a reply whose producer writes different constants, such as one
from a different build or one with altered bytes. They test no observation of
the capturing process or of the order. Capture before application rests on a
reading of the worker's source, together with the host's separate requirement
that application succeeded afterwards (CWorker.swift line 685). The cited
label test (DT-95) and the Swift label test (CompiledProfileCaptureTests.swift
lines 37–54) change these constants after construction.

**History.** The labels were added in `b6e6c313` (2026-10-16, "Name
compiled-profile capture and expose its worker stage"). The original decoder
in `660de67b` (2026-09-14, first tagged in v0.2.3) had neither label.
Related: DT-95.

### DT-97 — The capture nonce travels from the host's header to the host's comparison and enters no compiled byte or digest

**Statements examined.**

- REQUEST line 733: `capture_nonce` is "exactly 32 lowercase hexadecimal
  characters encoding the caller's nonce."
- RESPONSE line 2540: "The host returns the request's capture nonce after
  comparing it with the worker's recorded bytes. A comparison with a
  separately retained request nonce supplies a consumer's request
  association."
- The Nonce association guard (line 2593): "The recorded nonce bytes equal the
  valid request nonce."
- The source owner (line 2636) pins: "Fields bind the observed worker, nonce
  and consumed input bytes."
- ARCHITECTURE line 612 describes an "opt-in copy of the compiled object with
  a nonce."
- The guide asks for "a fresh per-application `capture_nonce`" (line 720) and
  says that "Consumers must join the nonce and worker identity to their own
  request" (lines 756–757).

**Path (source).**

1. The host admits the request string by format only. `policyMeaningFailure`
   ([ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift)
   lines 64–70) calls `captureNonceBytes` (CWorker.swift lines 672–677),
   which requires 32 UTF-8 bytes from `0-9a-f`.
2. `CWorkerOrchestrator` passes the string as `captureNonce` (lines
   124–125).
3. `ActorSession` zeroes the per-worker mapping (line 133), then writes
   `capture_requested` and the 16 decoded bytes into the header (lines
   152–155).
4. Before parameter setup, the worker copies the header bytes to a local
   array (pw_probe_runner.c lines 1531–1532).
5. `pw_capture_profile` copies them into the capture record
   (pw_profile_capture.h line 64).
6. The host decodes the request string again and compares the result with the
   record (CWorker.swift lines 694–697).
7. On success the host emits the request string, not the recorded bytes (line
   713).

The nonce is not passed to `sandbox_compile_string`, `sandbox_set_param` or
any digest. Both operands of the comparison come from bytes the host wrote
into one mapping. The comparison can detect a capture record that was not
written from this mapping's header, such as a zeroed record. The record's PID
is checked separately against the reaped worker (line 693).

**Executed.** `receipt_repeat.py` ran B's and B2's policies three times each,
with `probe_plan: []` and a fresh `secrets.token_hex(16)` nonce for every run.
Every receipt was `captured`, and each `request_nonce` equaled its request's
nonce. The six worker PIDs fell between 9386 and 9409.

- Every B receipt had 492 bytes, `b2056ef2…97e0`.
- Every B2 receipt had 524 bytes, `a2b35cd2…d4b0`.

These are the same digests as in probes B and B2 and in the registered case,
all of which used other nonces. The bytes and their digest therefore do not
vary with the nonce. No receipt field combines the nonce with the bytes.
`request_nonce` thus associates a receipt with a request only together with
the reply in which the host placed it.

**Freshness.** The refusal text is "capture_compiled_profile requires a fresh
32-character lowercase hex capture_nonce" (CWorker.swift line 744;
PWRunnerRequest.swift line 41). The host keeps no record of earlier nonces; it
checks only length and alphabet (source reading). Reuse of a nonce was not
executed.

**Checks.**

- The Swift fixture flips one bit of the recorded nonce and asserts
  `unavailable`, without checking the reason (DT-101).
- `capture.c` asserts that the copy equals its input (lines 29 and 57).
- Live tests assert that `request_nonce` equals the request's nonce
  (contract.py lines 326, 431 and 484).

No test supplies a valid but different nonce. No test establishes what the
association adds beyond the PID check and the per-worker mapping.

**History.** The header copy, the record copy and the comparison are
unchanged since `660de67b`. Related: DT-95 and DT-98.

### DT-98 — The receipt's input identity covers source and parameters; a changed imported file changes the bytes and no identity field

**Statements examined.**

- The Consumed input guard (RESPONSE line 2599; surface line 263): "The
  recorded source length and digest and parameter count and digest equal the
  host's supplied inputs."
- The source owner (line 2636): "Fields bind the observed worker, nonce and
  consumed input bytes."
- The guide (line 746): "The receipt identifies compiler output."
- RESPONSE line 874: "Files named by imports can change between these
  independent reads. A literal inventory describes the producer's walk; the
  worker compiled-profile receipt has its own observation boundary."

**Executed.** `receipt_import.py` used the 155-byte source `(version
1)\n(import "<probe3>/inc.sb")\n`, with capture and no parameters. It ran
twice and rewrote `inc.sb` between the runs:

| Run | `inc.sb` contents | `source_sha256` and `source_length` | `params_sha256` | Bytecode | Dossier `imports.closure_sha256` |
| --- | --- | --- | --- | --- | --- |
| 0 | `(allow default)\n` (`f59a5f95…7bbf`) | `37dbde4d…0791`, 155 | `df3f6198…1119` | 492 bytes, `b2056ef2…97e0` | `238dfe52…e5bd` |
| 1 | the same, plus `(deny file-write* (literal "/private/var/empty/pw-import-control"))` (`1b5fb7c6…38db`) | `37dbde4d…0791`, 155 | `df3f6198…1119` | 548 bytes, `f7dbbaca…8718` | `5553e2c6…51a2` |

Both receipts were `captured`, and both runs finished with exit 0. Every
identity field in the receipt was equal across the two runs, while the
bytecode differed. Run 0's bytes equal those from probe B's inline source
`(version 1) (allow default)`. The controller makes a separate read of the
imported file for the dossier, and its closure digest changed with the file.
No receipt field refers to it.

**Limits.** The two compilations were separate runs, not two reads within one
run. The worker's reads of imported files were not traced. The statements
describe consumed source and parameters; none of them claims imported bytes.
"Consumed input bytes" in the source owner and "identifies compiler output" in
the guide are the passages a reader could take as complete identity. Related:
DT-84 and DT-85 (inventory records are not the compiler's reads), and the
import-inventory limits, where changes to imported files between reads and
worker-side compilation were not exercised. See also DT-103.

### DT-99 — Three worker capture failures share one host reason; the host's extent/type reason is reachable only through a record the shipped worker does not publish

**Statements examined.** The host rule orders its guards and reasons (RESPONSE
lines 2574–2602; surface lines 127–279). Capture status, "The recorded capture
status was accepted," gives `worker_capture_refused`. The later Extent and
type guard, "The profile type is zero and its raw byte count is positive and
at most 1,048,576 bytes," gives `capture_extent_or_type_invalid`. LIMITS line
191 says "Oversized or unsupported objects leave capture unavailable without
preventing policy application." LIMITS line 364 says "Capture supports
nonempty single-profile (type 0) objects."

**Source.** The worker records one of four status values (abi lines 573–574;
pw_profile_capture.h lines 64–86):

- 1: captured;
- 2: "unsupported layout/type/length";
- 3: "unreadable object";
- 4: "malformed consumed input".

The worker publishes 1 only after all of these hold: type 0, a zero
`reserved` word, a length that is nonzero and at most 1 MiB, a nonnull
pointer and a complete payload read. The host maps any status other than 1 to
`worker_capture_refused` (CWorker.swift line 692). It checks type and extent
only afterwards (lines 698–701).

With the shipped worker, an oversized, bundle-typed, empty or unreadable
compiled object therefore yields `worker_capture_refused`. The only route to
`capture_extent_or_type_invalid` is a record with status 1 and an invalid
extent or type, which the worker's own checks prevent. The receipt has no
field for the worker's status code, so a consumer cannot tell "unsupported"
(the oversized and unsupported cases in LIMITS) from "unreadable". No
statement mentions the `reserved == 0` requirement.

Status 4 also appears unreachable. Before `sandbox_set_param`, the worker
refuses any parameter that lacks a NUL within its fixed buffer
(pw_probe_runner.c lines 1547–1554). Those buffers are 128 and 384 bytes (abi
lines 112–113 and 566–567). The source length is bounded far below
`UINT32_MAX`.

**Checks.** `capture.c`
([runner_abi_layout/capture.c](../tests/suites/runner_abi_layout/capture.c))
calls the production `pw_capture_profile` on constructed memory. It asserts:

- status 2 for 1 MiB + 1 and for type 1 (lines 36–42 and 71–76);
- status 3 for invalid pointers (lines 77–81);
- status 4 for an unterminated key (lines 82–84).

The Swift tests reach `capture_extent_or_type_invalid` only with constructed
status-1 records (DT-101). No test names `worker_capture_refused`; `git grep`
over `tests`, `runner/Tests` and `controller/src` finds none. None of these
cases was executed live.

**History.** The status codes, the collapse into one reason and the guard
order date from `660de67b` (v0.2.3). Apart from field types, the decoder at
v0.3.5 is identical. The reason strings first appear in the documentation at
v0.3.7 (`f6551bf9`). Related: DT-100 and DT-101.

### DT-100 — The first-failure order starts with application and completion; a capture that never ran and one that completed and was withheld report the same three fields

**Statements examined.** "`unavailable` states that a capture condition
failed" (RESPONSE line 2535), and "The host names the first failing capture
condition" (line 2536). The guide (lines 735–746) says:

- "Missing capture, failed apply, worker death or capture corruption is
  unavailable."
- "An opt-in request alone does not establish that capture ran."
- "An unavailable capture does not establish application failure."

The Capture failure effect withholds eleven fields and retains
`reply.normalized_outcome` (line 2601).

**Source.** `decodeProfileCapture` checks application (`applied && applyRC ==
0`, line 685) and worker completion (line 686) before it reads any capture
word. `collectOutput` takes `applied` from the worker's published flag
(ActorSession.swift lines 630–642). No classifier reads `profileCapture`. It
is used only where it is constructed (ActorSession.swift lines 737–741) and in
reply assembly (CWorkerOrchestrator.swift line 226).

**Executed.**

- **Compile failure.** This is an ordinary input, not a control
  (`receipt_compile_fail.py`). The source `(version 1) (allow
  no-such-operation)` was sent with capture requested. The run exited 1 with
  `runner_failed` and `sandboxed_after_apply: false`. Worker 16870 exited 0
  with `done_observed: true`. `worker_evidence.failure` showed operation 5
  (compile) with `native_kind` 2, and `progress` showed operation 5, stage 2.
  The worker exits at pw_probe_runner.c lines 1582–1589, before the capture
  block at line 1594. The receipt was `{status: unavailable, reason:
  successful_application_unconfirmed, worker_pid: 16870}`.
- **Kill after application.** Probe C and the registered
  `capture_worker_death` show `progress` operation 9, stage 2;
  `readiness.rc` 0; `sandboxed_after_apply: true`; and `term_signal` 9. In
  the worker's straight-line code, capture (operation 6) precedes readiness
  (7) and application (8), so the capture function had returned before
  application. The receipt was `{status: unavailable, reason:
  worker_not_complete, worker_pid}`. The capture record's completion and
  status words are not projected.

In neither case does the receipt alone say whether capture was attempted. The
reply's worker evidence does: a published compile failure in the first case
and observed application in the second. Neither unavailable receipt changed
the reply outcome. In both cases `runner_failed` came from the worker
failure, whereas B, whose capture succeeded, finished. This agrees with
`retain_assessments(reply.normalized_outcome)`. In probe C, the controller and
the consumer admitted the receipt. The envelope kept the diagnostics, the
completed `create` step and the created file.

**Checks.** The registered case (contract.py lines 498–512) asserts:

- `unavailable` with `worker_not_complete`;
- no `producer`, `capture_stage` or `bytecode_b64`;
- `sandboxed_after_apply`;
- `term_signal` 9;
- the created file.

It does not assert the absence of the other eight withheld fields, although
both observations here lacked them. No test requests capture for a policy
that fails to compile. Related: DT-99.

### DT-101 — The host-check support constructs every receipt premise; its corruption loop asserts unavailability but no reasons, and six of nine reasons occur in no test

**Support examined.** The check-read owner (RESPONSE line 2604; surface lines
281–290) pins: "The read checks construct worker bytes, corrupt each capture
input and assert unavailability and withheld bytecode." Its limit says the
fixture "establishes host checks; the native same-pointer capture is
source-supported here." ARCHITECTURE line 637 cites the same check for
"admitted only after successful application, completion, PID, nonce, input
identity and payload integrity checks."

**Fixture construction.**
[CompiledProfileCaptureTests.swift](../runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift)
lines 12–29 build one 144-byte header followed by a payload. They use literal
offsets, not `PWShmLayout` constants; only the buffer size uses the
constants. The header holds:

- completion 1, status 1, length 3 and PID 4321;
- the source length, a parameter count of 1 and the source digest;
- a parameter digest for `TARGET=/a`, built from literal LE lengths;
- the payload digest and the nonce `00 11 … ff`.

The payload is `[10,20,30]`. `read` (lines 30–36) calls
`decodeProfileCapture` directly with injected `applied`, `applyRC`, `done`,
`exitCode` and `termSignal` values. No worker, compilation, capture code,
mapping or reaping is involved. The test supplies every premise of the
receipt, including the application and completion facts.

**Assertions.**

- The corruption loop (lines 67–76) flips bit 0 at 11 offsets. For each, it
  asserts `status == "unavailable"`, `bytecode == nil` and
  `bytecode_sha256 == nil`. By the source order, these 11 corruptions reach
  seven different reasons:
  - completion: `capture_not_complete`;
  - status: `worker_capture_refused`;
  - type: `capture_extent_or_type_invalid`;
  - PID: `capture_worker_mismatch`;
  - nonce: `capture_nonce_mismatch`;
  - payload digest and payload: `capture_bytecode_digest_mismatch`;
  - source length, parameter count, source digest and parameter digest:
    `capture_consumed_input_mismatch`.

  The loop asserts neither these reasons nor the absence of the other nine
  withheld fields.
- The extent loop (lines 77–83) asserts `capture_extent_or_type_invalid` for
  lengths 0, 1,048,577 and `UInt32.max`, each with status 1 (DT-99).
- Application and completion (lines 84–91): `successful_application_unconfirmed`
  is asserted once, for `applied: false`. The `applyRC: -1`, `done: false` and
  signal 9 cases assert only the status. A nonzero exit without a signal is not
  exercised.
- The label test (lines 37–54) and the round trip (lines 98–110) change the
  constant labels after construction (DT-96).
- Lines 111–119 call `runCWorker` with `/nonexistent` and four invalid nonces,
  and require `.captureNonceInvalid`. This path reaches `ActorSession`'s check
  before any mapping or spawn (ActorSession.swift lines 71–73).

No case combines two failing conditions, so the first-failure order has
source support only. `git grep` over `tests`, `runner/Tests` and
`controller/src` finds no file naming any of six reasons:

- `capture_not_complete`;
- `worker_capture_refused`;
- `capture_worker_mismatch`;
- `capture_nonce_mismatch`;
- `capture_bytecode_digest_mismatch`;
- `capture_consumed_input_mismatch`.

`capture_nonce_mismatch` is one of the three values RESPONSE displays.
`worker_not_complete` is asserted live (DT-100).

The other constructed receipts in the Swift tests are encoding fixtures. One
of them, `value46` at ReplyFailureTests.swift line 88, is `captured`, has
`reason: "constructed"`, and carries a digest that does not match its bytes.
The host's reporting validation accepts it.

The support's pin matches these assertions. The guard-specific reasons, the
order and the eleven withheld fields named in the rule go beyond them.
Related: DT-38 (assertion scopes combined in check-read support), DT-99 and
DT-100.

### DT-102 — No live test captures with parameters; C/Swift agreement on a nonempty parameter digest was observed once here

**Statements examined.** The Captured input identity definition (RESPONSE
lines 2562–2565; surface lines 110–112). The guide (lines 753–755) says: "The
worker hashes its private copy of the strings passed to `sandbox_set_param`;
the host independently recomputes the identity."

**Checks.** Every live capture assertion about parameters uses none:
contract.py line 332, check_actor_compositions.py lines 134–135
(`params_sha256 == sha256(bytes(4))`) and guide_workflows.py line 470.
`capture.c` lines 65–70 assert that the C digest is independent of order and
sensitive to a changed value, but do not check its value. The Swift test
checks the host's value against an independently framed digest for one pair
(lines 21–24) and checks order independence (lines 92–97). No test compares
the C value for a nonempty parameter set with the Swift value or with an
independent value. A disagreement would appear live only as
`capture_consumed_input_mismatch`, a reason no test names (DT-101).

**Executed.** In B2 (`ROOT=/etc`, `Z=é`), the worker's `params_sha256` was
`2a4f1d69…95fd`, equal to the recomputation by `receipt_check.py`. The receipt
was `captured`, which by the guard order also means that the host's Swift
recomputation agreed. This establishes agreement for one input with two
parameters and one non-ASCII value, not agreement in general. Related:
DT-101.

### DT-103 — The bytes come through a private 24-byte view; available checks establish consistency and repeatability, not the object's layout or what application consumed

**Statements examined.** `bytecode_b64`: "The bytes copied from the compiler
object passed to `sandbox_apply`" (RESPONSE line 2544). The source owner's
limit (line 2636): "Live capture behavior and platform private-layout
compatibility require their native checks." `capture.c` lines 1–2:
"Construct the private layout independently; live authored controls
separately qualify that layout." The guide (lines 746–747): "None is a
readback of the kernel's effective policy."

**Source.** The worker reads the returned `profile` through
`pw_compiler_profile_t`
([pw_profile_capture.h](../controller/tools/pw_probe_runner/pw_profile_capture.h)
lines 15–22): a `uint32_t` type, a `uint32_t` reserved word, a bytecode
pointer and a `size_t` length. Only the 24-byte size is asserted statically.
Each read uses `mach_vm_read_overwrite` (lines 53–58), so an invalid pointer
is refused rather than dereferenced. The same `profile` pointer goes to
`sandbox_apply` (pw_probe_runner.c lines 1574, 1598–1600 and 1641). Between
capture and application there are only the optional pre-ready sleep, the
ready-byte write and progress stores (lines 1603–1640).

**Executed.** The decoded length and SHA-256 matched the receipt for every
capture: B, B2, the two registered captures, the six repeats and the two
import runs. Equal inputs gave equal bytes, and different policies gave
different bytes. An imported `(allow default)` gave the same bytes as the
inline form.

The import-inventory investigation's "Native bytecode probe"
(`bytecode_digest.c`) read 492 bytes, `b2056ef2…97e0`, for an allow-default
source. It ran in a separate process but through the same 24-byte view. This
is agreement across processes under the same layout reading, not an
independent decoding.

**What qualifies the layout.** The WORKER inventory rows s27, x5, W14, W38
and W54 cite `max_targets_reply_survives` as their live control. That control
requires `status == "captured"` and `bytecode_length > 0`
(check_max_target_reply.py lines 253 and 378). Other live tests add the
decoded length and digest check. Together these establish two facts on this
macOS build. First, the four words read as type 0, reserved 0, a readable
pointer and a length within the limit. Second, the copied bytes are
deterministic.

No check compares the bytes with a reference compilation, decodes them, or
shows that `sandbox_apply` submits those bytes. The source owner's limit does
not name the native checks it refers to. Related: DT-98.

### DT-104 — Smaller observations on the receipt admission tests and statements

- **Decode failures stand in for label failures in eight fixture rows.**
  Eight of the 17 invalid rows in `compiled_profile.json` fail the test-only
  serde reader before admission: `producer` false or 7, `capture_stage` false
  or 7, and `status` null, false, 7 or absent. In
  `compiled_profile_labels_determine_the_public_admission_outcome`,
  `observe_client` (run_flow.rs lines 2658–2676) turns such a row into a
  client `runner_reply_error` with `Malformed`. For those rows,
  `runner_result` is null and the outcome is still
  `malformed_runner_response`. Nine rows reach `admission_problem`.
  `compiled_profile_context_is_gated_after_the_response_version` (line 1929)
  counts a serde failure as not accepted. The cited run test never uses the
  binary reader: it types replies from JSON through the `cfg(test)`
  `Deserialize` derive. The support's context says "Constructed typed
  replies."
- **The run test cannot tell withhold from null.** DT-37 records that the
  label-failure effect for `run` withholds the diagnostics, while the
  context-refusal effect sets them to null. The run test checks
  `wire["data"]["runner_sandbox_diagnostics"].is_null()`. `serde_json`
  indexing returns `Null` for a missing key as well as for a JSON null, so the
  test cannot distinguish the two forms.
- **The credited run.** The run-label support names run
  `20261110T195016Z_0d197151` at `5e51300d`. That run is not under
  `tests/out/runs/` in this checkout. At HEAD the test body is byte-identical:
  the MD5 of the extracted function is unchanged. `compiled_profile.json` and
  `admission_problem` are also unchanged since `5e51300d`. The test passed in
  `20261116T192345Z_79fbbaf4`.
- **`reason` presence.** The host always supplies `reason` on `unavailable`
  and never on `captured` (CWorker.swift lines 682–683 and 712). No reader
  requires either; the mutations in DT-95 that added a reason to a captured
  receipt and removed it from an unavailable one were accepted. The field's
  type is `string?`.

### Receipt coverage and remaining investigative limits

The trace covered:

- the declaration and the host's admission of it;
- the path of the nonce, source and parameters from the request to the worker
  header, the policy pipe and the parameter snapshot;
- the worker's compile, capture and apply order, and its capture function;
- the shared-memory record and the host decoder;
- insertion of the receipt into the ordinary reply;
- the controller's binary reader, admission and envelope path for `run`;
- the independent consumer's receipt rules;
- every test that names a receipt reason or asserts receipt bytes or
  parameters.

Affirmative observations within their tested scope:

- When capture was not requested, the receipt key was absent from both the
  JSON and the host bytes. The registered corpus asserts the same for its
  non-capture examples through the CLI and XPC.
- For the captured contrasts, each of the following agreed with the request
  and the reply: the decoded length and digest, the source digest and length,
  the independently computed parameter digest, the nonce and the worker PID.
- The controller's JSON receipt equaled the receipt decoded independently
  from the retained host bytes.
- The kill-after-application control produced the documented `unavailable`
  receipt with reason `worker_not_complete`, and every capture field was
  withheld. Application, the attempt's result and its effect were reported
  separately.
- The three registered cases passed without system sleep.

These observations do not establish:

- that the bytes come from the compiler's object, beyond the private layout
  reading;
- how the bytes relate to what `sandbox_apply` submitted;
- any kernel state (DT-103).

Not exercised:

- live `worker_capture_refused` or `capture_not_complete`;
- live PID, nonce, digest or consumed-input failures; for ordinary inputs, the
  shipped worker does not publish the records these need;
- an oversized or non-type-0 compiled object;
- a reused nonce;
- augments with capture; the dossier's `applied_sha256` equaled
  `source_sha256` only without augments;
- the controller's response to edited receipts, which is inferred from source
  and the two constructed Rust tests rather than run through
  `policy-witness run`;
- actor receipts, BYOXPC and `runner verify`.

The saved-reply mutations exercised the Python consumer, not the controller.
Historical inspection covered:

- the origin of capture (`660de67b`);
- the labels (`b6e6c313`);
- the decoder, controller check and guide at v0.3.5;
- the first documentation of the reasons (v0.3.7).

It establishes when mechanisms and statements appeared, not how older
binaries behaved.

Only this record was changed among tracked files. The registered run added
development output under `tests/out/runs/profile-receipt-trace/`, and the
pinned pytest target was provisioned under `.tmp/pytest/`. These entries
contain no repair, deduplication or choice of authoritative layer.

## Additional findings: wire identity and public JSON projection

This continuation examines two mechanisms: the wire-schema fingerprint
(`wire.frame.identity`) and the public JSON projection
(`wire.frame.projection`). It follows their immediate producers, readers and
checks:

- the authored schema [porcelain.json](../docs/porcelain.json) and its
  generator [generate_porcelain.py](../docs/generate_porcelain.py);
- the Swift writer ([PWPorcelain.swift](../runner/Sources/PWRunnerCore/PWPorcelain.swift)
  and the generated `PWPorcelainRecords.swift`);
- the Rust reader ([porcelain.rs](../controller/src/porcelain.rs) and the
  generated `porcelain_records.rs`);
- the Python reader ([porcelain.py](../tests/lib/porcelain.py) and the
  generated `porcelain_schema.py`);
- the checks cited for them.

The statements read were:

- [21-wire.surface.md](../docs/contract/21-wire.surface.md) lines 33, 53, 61,
  97–103 and 105–111, and its support owner (lines 13–23);
- ARCHITECTURE lines 699, 733–735 and 743–750, and rows 611, 942–943 and
  D78–D80 (lines 1027–1029);
- CONTRACT's "Wire-schema fingerprint" (lines 190–197);
- RESPONSE definitions of the path forms (lines 1049–1051 and 1061–1063),
  the conditional-null fields (lines 961–962, 2235–2236 and 2324–2325), the
  claim value variant (lines 1894 and 1899–1907) and the validator record
  (lines 978–989).

The public build contract and semantic admission were read only where they
bound the fingerprint's role or consumed projected values. Transport, actor
execution and BYOXPC were excluded. The leads were DT-18, DT-31, DT-47,
DT-52–53 and DT-95–104; the entries below cross-reference them where they add
evidence.

### Wire-identity investigation identity and reproduction conventions

Source inspection used clean HEAD `b377cb8a7c7182051e8ff320c4741e26316704f4`
on 2026-11-16. Line numbers below refer to that snapshot. File hashes:

- `docs/porcelain.json` `538b3cf5…09c2`;
- `docs/generate_porcelain.py` `0f0c1470…ab86`;
- `tests/lib/porcelain.py` `c1bc3bcf…ebdb`;
- `tests/lib/porcelain_schema.py` `7cb5a0df…f6f7`;
- `controller/src/porcelain.rs` `70b7648c…2cb1`;
- `controller/src/porcelain_records.rs` `f9e67dbe…409f`;
- `runner/Sources/PWRunnerCore/PWPorcelain.swift` `b8e6d4ee…ec6c`;
- `docs/contract/21-wire.surface.md` `02333ece…45b9`;
- `tests/suites/source_drift/porcelain_codec.py` `55cd8440…44f5`;
- `tests/suites/runner_unit/porcelain_replies.py` `f5491ef3…4614`.

The schema, generator and readers last changed in `897be512`
(2026-11-11), an ancestor of the app's commit. The machine reports macOS
26.7.1, build 25G241. Python ran through `tests/lib/python.sh` (Python 3.14.9)
with `-I`.

**Build.** `dist/PolicyWitness.app` reports commit
`8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855` and contract
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
`docs/build_contract.py` printed the same identity for HEAD.
`codesign --verify --deep --strict` passed, and the team is `42D369QV8E`.
Outside `records/`, `git diff 8b5de2b2 HEAD` touches only the retired plan and
one line of `tests/suites/preflight/opt_in/build_refusals.py`. Nothing was
rebuilt.

**Registered run.** `PW_TEST_OUT_DIR=tests/out/runs/wire-identity-trace
tests/run.sh --case source_drift/porcelain_codec --case unit/rust.unit --case
runner_unit/pwrunner_core_unit_executable` produced run
`20261116T213728Z_d05f0e15`. All three cases passed, each with
`system_sleep_ms` 0.

- The Swift batch reported 606/606.
- The Rust log lists every `porcelain::tests` control as `ok`, including the
  four the wire support owner cites and
  `byte_projections_spell_bytes_only_at_presentation`.
- `reader_definition_corpus_cross_readers` passed.

This output is disposable development output under the retention policy. The
decisive values are reproduced below. The Swift-emitted frames used by the
probes are the 261 `.pwp` files under that run's
`suites/runner_unit/pwrunner_core_unit_executable/artifacts/`.

**Direct probes.** Drivers are under `<scratchpad>/scripts`, where
`<scratchpad>` is
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/084cf250-b2e9-4675-b565-8bc3e3b83e81/scratchpad`.
Scratch material has no retention guarantee.

- `wiretlv.py` (`a69b4cb5…7e33`) is a separate TLV parser and writer written
  from the ARCHITECTURE frame grammar. It does not use `tests/lib/porcelain.py`.
  It re-encoded all 261 Swift frames byte-identically.
- `identity_probe.py` (`210f96a9…b781`) recomputes the fingerprint with its
  own canonical JSON writer and its own type-descriptor construction. It then
  applies one-property mutations to the schema in memory. For each it records:
  - whether `validate()` refuses;
  - whether the fingerprint changes;
  - whether the generated Swift, Rust and Python text changes apart from the
    fingerprint line;
  - whether any Swift source region changes;
  - whether the 260 reply-rooted Swift frames decode and project differently
    under the mutated Python tables, with the header ignored.

  The 261st frame, `porcelain-disposition/unknown-progress.pwp`, has a
  `PWRunnerSubprocess` root.
- `generator_cli_probe.py` (`6cd89feb…7f3f`) runs the actual generator command
  in disposable copies made with `fixture_inputs.copy_declared`, and diffs the
  three outputs.
- `build_probe_frames.py` (`922b5089…9f0d`) and `build_probe_frames_2.py`
  (`7eb10f53…0d21`) build 40 probe frames by editing Swift-emitted corpus
  frames. Each edit changes one property; the nine Swift path-state frames
  were added unedited. The drivers add each probe frame as a case row to a
  scratch copy of the reader corpus.
- Rust projections came from a copy of the current controller test binary
  (`controller/target/debug/deps/policy_witness-bb8137965490ffba`,
  `ce8d8051…91be`, copied under `tests/lib/checkout_lock.sh`). It ran
  `run_flow::tests::reader_definition_corpus_cross_readers` with
  `PW_POLICY_TRANSFER_REPLIES` pointing at the scratch corpus. That test:
  - decodes each frame with `porcelain::decode`;
  - serializes the typed record;
  - runs `admit_reply`;
  - assembles the `run` envelope;
  - writes `rust.json`;
  - then runs the Python replay.

  The test exits 101 here by design. Every reported problem names a probe row:
  10 Rust and 38 Python problems. The 153 original rows reported none.
- `analyze_probe.py` (`b39ef223…4525`) compares the Rust JSON with
  `porcelain.decode_bound(…, 'reply', 'test:policy-witness')`. It records key
  presence explicitly, with absent spelled `<absent>`. It also runs
  `consumer.validate_fixture` and `lifecycle_oracle.check_record`.
- `golden_probe.py` (`3fbfd0ac…d283`) recomputes the reply shape from the 64
  `porcelain-shapes` frames under mutated tables, using the production
  `collect_shape`, and compares it with `response_shape.json`.
- `precedence_probe.py` (`28cf5e6b…1577`) is described in DT-110.

One live `policy-witness run` used the dist app; see DT-109.

**Independent recomputation (executed).** The fingerprint is SHA-256 of
compact, sorted-key JSON. The recomputation built that JSON with its own
writer and its own descriptors: `text`, `i64`, `i32`, `bytes`,
`{"record": id}`, `{"variant": name}` and `{"optional"|"list"|"map": …}`.
The result, `80013e5b…e224`, equaled:

- `wire_identity`'s output;
- `SCHEMA_FINGERPRINT`;
- the Swift `fingerprint` array;
- the Rust `FINGERPRINT` array;
- the header bytes of all 261 Swift frames.

The identity JSON is 48,563 bytes. The descriptor spellings are not in any
statement. The surface says "type descriptor" without defining one, so the
recomputation is independent code but not an independent specification.

### DT-105 — The fingerprint changes for names, ordering and presentation rules that producers do not consume, and every frame it refuses also fails the exact contract check

**Statements examined.**

- Surface line 103 and ARCHITECTURE line 745: the fingerprint covers "records
  in schema order with ID, name and fields; each field's tag, public name,
  type descriptor, null rule and any byte projection; path-form and
  conditional-null rules; root names mapped to record IDs; and declared
  variant cases." "Changes to a field's name, tag, type, optionality,
  null/projection rule or a newly added optional field change the fingerprint
  and require exact receiver agreement."
- The generator's comment (generate_porcelain.py lines 276–277): "Source
  locations, defaults and prose … do not change what a received record means
  and must not force wire churn."
- CONTRACT lines 192–197: "A matching fingerprint establishes the selected
  wire-schema match; the public producer identity is then checked
  separately."

**Executed (one-property schema mutations).** Every recomputed fingerprint
matched production. The "frames" column counts how many of the 260
reply-rooted Swift frames project differently under the mutated tables.

| Change | Fingerprint | Generated text changed apart from the fingerprint | Frames projecting differently | Statement |
| --- | --- | --- | --- | --- |
| Last tag of `CompiledProfileCapture` 15→16 | changed | Swift writer, Rust, Python | 49 (all refused) | covered |
| `parameter_count` `Int?`→`String?` | changed | Swift region, Rust, Python | 49 (refused) | covered |
| `reason` `String?`→`String` | changed | Swift region, Rust, Python | 10 (refused) | covered |
| Added optional field (tag 16) | changed | all three, Swift region | **0** | covered |
| `worker_pid` `Int`→`Int64` | unchanged | Swift region only | 0 | silent |
| `PWExecWaitObservation.rc` `Int32`→`Int64` | changed | Swift region, Rust, Python | 0 | descriptor |
| Added variant case 3 (`String`) | changed | Rust, Python | 0 | covered |
| Public name `reason`→`reason_text` | changed | Swift tag constant, Rust, Python | 40 (none refused) | covered |
| `reason` `json_null` false→true | changed | Rust, Python | 10 | covered |
| `source_sha256` hex→base64 | changed | Rust, Python | 49 | covered |
| `PWRunnerPathDiagnostics` path-form order reversed | changed | Rust, Python | 1 | covered |
| `conditional_null` removed from `PWRunnerSandboxCheckResult` | changed | Rust, Python | **0** | covered |
| Storage name `bytecode`→`bytecode_data` | unchanged | Swift writer and region, Rust field name | 0 | — |
| Doc comment; default of `PWRunnerEquipmentExecution.reason`; `mutable`; local-only field type; unknown field key | unchanged | Swift region at most | 0 | provenance |
| Source path (fingerprint only; outputs need the region in the new file) | unchanged | — | — | provenance |
| `records` list reversed | changed | Swift, Rust, Python (declaration order) | 0 | covered |
| Record rename `PWRunnerTerminationRequest`→`PWRunnerKillRequest` (fingerprint only; outputs need renamed regions) | changed | — | — | covered |
| Variant case `Integer`→`Number` | changed | Rust enum case | 0 | covered |
| Root key `reply`→`response` | changed | Rust and Python constant names | 0 | covered |

The insensitivities agree with the statement: provenance, storage names, and
`Int`/`Int64` in a field, which have the same wire kind and range. Each
statement-covered change moved the fingerprint.

**What the receiver needs.** The Swift writer consumes only record IDs, field
tags, stored types and optionality. The generated `porcelainWrite` bodies hold
no public name other than a tag constant's identifier, no null rule, no
projection, no path form and no conditional rule. A producer from an older
schema therefore writes the same bytes after:

- a rename;
- a null-rule flip;
- a projection change;
- a path-form or conditional-null edit;
- a record reorder or rename;
- a variant-case rename;
- a root-key rename.

The receiver projects those bytes with its own rules. After an added optional
field, every one of the 260 old frames decodes and projects identically, yet
the new fingerprint refuses them all. The same holds for a removed
conditional-null rule, which also changed no frame.

**Relation to the public contract (source).** The fingerprint constants live
in `controller/src/porcelain_records.rs` and
`runner/Sources/PWRunnerCore/PWPorcelainRecords.swift`. Both are inputs to the
development contract digest (CONTRACT lines 80–86), and release identity
requires tag-equal bytes. Any fingerprint change therefore changes the public
contract. After the fingerprint, both `decode_bound` implementations require
the exact contract: porcelain.rs lines 174–221 and porcelain.py lines
158–186. The controller passes `BUILD_CONTRACT` for both the client capture
and the host reply (runner_client.rs lines 715 and 752–756). In the
controller, the fingerprint check therefore refuses no frame that the contract
check would admit.

Its distinct effects are three:

1. A different refusal message. Both refusals map to
   `unsupported_runner_response` (runner_client.rs lines 627–629).
2. A refusal before the producer context is decoded.
3. It is the only identity check for unbound readers. These include
   `porcelain.decode`, used by most Python replay helpers, and
   `porcelain::decode`, used by the Rust corpus test.

**Cost.** A schema mismatch reports "runner reply frame names an unsupported
porcelain schema; this controller reads only the schema it was built with"
(lines 760–765). It does not name the foreign producer, although the contract
string sits at a fixed position the controller could read. A contract mismatch
reports "runner reply has foreign contract {value}". Most build differences
that reach a receiver change the schema too. The guide's recovery row (line
2977) asks the operator to compare the runner's contract with `--version`
from elsewhere.

The statement that presentation edits "require exact receiver agreement"
treats a receiver-local rendering choice as a producer/receiver protocol
change.

**Judgment (tentative).** The arrangement looks needlessly broad rather than
wrong. The exact-contract rule already forces lockstep builds, so the cost is
small in operation. The cost lies in interpretation and maintenance: the
identity mixes protocol structure with presentation and generator-local
names. An identity over binary structure alone would say what a receiver must
share with the producer: IDs, tags, kinds, ranges, optionality, and variant
tags with their payload types. Presentation rules could then be versioned
with the receiver. Alternatively, reading the producer context before refusing
would make the schema refusal name the producer. Related: DT-31, the contract
path that leaves `runner_result` null, and DT-106.

### DT-106 — Inert null flags and verbatim variants make the fingerprint more sensitive than the projection, and the statement's provenance boundary has an exception

**Inert null flags (executed and source).** Three implementations interpret
`json_null`, and each ignores it on path-form and conditional-null fields:

- The Rust generator checks the path-form and conditional-null branches before
  the `json_null` branch (generate_porcelain.py lines 235–245).
- The Python reader applies `json_null` first (porcelain.py lines 90–91).
  Path-form handling (lines 93–101) and conditional handling (lines 102–106)
  then overwrite the result in every case.
- The documentation generator forces `json_null=True` for both kinds
  (record_definitions.py lines 377–381).

The authored flags differ: `native_rc` and `team_id` carry `json_null: true`,
and every path form carries `false`. Flipping `native_rc`, `team_id` or
`realpath_resolved` changed the fingerprint. The generator command in a
disposable copy changed exactly two lines in each of the Swift and Rust
outputs, both of them the fingerprint constant, and four lines of the Python
tables. Projection of the 260 frames was unchanged. The same holds for
`json_null: true` on a required field (`CompiledProfileCapture.status`):
`validate()` accepts it, and only the fingerprint changes.

**Variants are fingerprinted verbatim.** `wire_identity` passes
`schema['variants']` through unchanged (line 298). Field types, by contrast,
go through `descriptor`. As a result:

- `Int`→`Int64` on a field leaves the fingerprint unchanged, but the same
  change in a variant case's `type` changes it. Rust and Python output were
  unchanged apart from the fingerprint.
- A `doc` key added to a variant case changes the fingerprint; an unknown key
  on a field does not. `validate()` accepts both. Surface line 103 says
  "descriptive text remain[s] source provenance."
- Case names are not on the wire or in public JSON. They name Rust enum cases,
  RESPONSE's "Alternative" column (lines 1904–1907) and `is_variant(…,
  "Integer")` in authored conditions (RESPONSE lines 1651–1652). They do
  change the fingerprint.

**Checks.** The fingerprint tests in
[porcelain_codec.py](../tests/suites/source_drift/porcelain_codec.py) are:

- a doc-comment control (lines 470–489);
- five structural mutations (lines 491–539): add, drop, renumber, kind change
  and an added record.

None mutates a public name, a null rule, a projection, a path-form or
conditional rule, a default, a source path, record order, a variant or a root.
ARCHITECTURE row 942 cites the comment control for "typed record fields, tags,
primitive kinds and public presentation rules". Row D78 cites the structural
test for "record schema and presentation rules". Before this probe, the
presentation half of surface line 103 had only source-read support.

### DT-107 — The Swift variant writer is hand-written, so the frame's fingerprint asserts variant tags the producer does not derive; the untagged projection depends on distinct JSON types

**Source.** `swift()` (generate_porcelain.py lines 154–171) emits record
writers only. `PWDispositionValue` and its writer are hand-written:
PWRunnerDisposition.swift lines 48–52 and PWPorcelain.swift lines 115–126,
with literal case tags 1 and 2. The Rust enum and reader (lines 183–190) and
the Python `VARIANTS` table come from the schema.

**Executed.** Swapping the two case tags in a disposable copy and running the
generator succeeded:

- The Swift output changed only in the fingerprint array.
- Rust swapped the enum order.
- Python's `VARIANTS` became `{1: {'record': 63}, 2: 'i64'}`.

`--check` compares generated text only, so the build accepts the result. A
Swift build from that tree would stamp the new fingerprint while writing the
old tags. Under the swapped tables, 153 of the 260 Swift frames were refused,
namely every frame with a disposition claim value. The registered checks would
catch this at test time, not at build time. Three of them would fail:

- the Rust test with literal tags (porcelain.rs lines 553–595);
- the Python variant control (porcelain_codec.py lines 125–129), which reads
  the real `VARIANTS`;
- the runner_unit corpus replay.

The case payload types are also hand-written in Swift: `integer(Int)` and
`request(PWRunnerTerminationRequest)`.

**Projection.** Surface line 61 says "Public JSON serializes the selected value
directly." The Rust enum is `#[serde(untagged)]`, and Python returns the bare
value. The case is recoverable from JSON only because the two cases have
different JSON types: a number and an object. `validate()` accepts a variant
with two `Int` cases; in-memory control: case 3 `Signal(i64)` was accepted and
rendered. Such a variant's cases would be indistinguishable in JSON.

**Executed, frame-level variant edits.** These are one-property edits of
`ordering-ordinary`; Rust and Python JSON were identical.

| Edit | Rust `admit_reply` | Envelope `disposition_integrity` | `consumer.validate_fixture` | Lifecycle oracle |
| --- | --- | --- | --- | --- |
| `final_status` value set to the Request variant | no issue | `invalid` | "value is object, not number" | D1 |
| `final_status` value set to Integer 17 beside `exit_code` 0 | no issue | `invalid` | none | D1 |
| `final_status` value removed | no issue | `invalid` | none | D1 |
| `final_status` claim removed | no issue | `invalid` | none | D8 |

The last three repeat DT-53's JSON-level results on actual binary frames and
add the Rust view: semantic admission does not refuse them, and the
diagnostics mark the disposition invalid. The run outcome stayed
`validator_unavailable` in all four.

### DT-108 — The conditional-null projection discards a carried dependent; a contradicting value disappears, and nothing in the stated chain refuses it

**Statements examined.** Surface line 111: "Conditional-null fields are carried
only when their guard has a value." RESPONSE line 962 gives `native_rc` as
"present when result_source has a value; may be null" and adds "Synthetic
results carry explicit null when result_source is present." RESPONSE line
2236 gives the equivalent rule for `team_id`.

**Source.** On the wire, the dependent and the guard are independent optional
tags. Structural admission accepts any combination. Projection then drops the
dependent whenever the guard is absent: generated `serialize` (for example
porcelain_records.rs line 3523) and porcelain.py lines 102–104. No reader
compares the two before projection.

Rust semantic admission reads typed values, so it can see a dependent the JSON
omits. The Python readers read the projection. The shipped host sets
`result_source` on every built query (CWorkerStepResults.swift lines 46–48).
In the 260 Swift frames the guard-absent state never occurs. Removing the rule
changed no frame (DT-105) and no shape-golden document (DT-111).

**Executed.** Each probe is a one-property edit. Rust and Python JSON were
identical for every probe, including key presence.

| Base | Edit | `result_source` / `native_rc` in JSON | Rust `admit_reply` | Python general reader |
| --- | --- | --- | --- | --- |
| `ordering-ordinary` (query_first) | none | `validator` / `0` | admitted | no finding |
| same | `native_rc` removed | `validator` / `null` | "query_first lacks eligible prediction…" | matching finding |
| same | `result_source` removed, `native_rc` 0 kept | absent / absent | same issue | same finding |
| same | both removed | absent / absent | same issue | same finding |
| same | `native_rc` 7 beside `rc` 0 | `validator` / `7` | same issue | same finding |
| same | `result_source` removed, `native_rc` 7 | absent / absent | same issue | same finding |
| `ordinary` (synthetic, no ordering claim) | none | `synthetic` / `null` | admitted | no finding |
| same | `result_source` removed, `native_rc` 5 | absent / absent | **admitted** | **no finding** |
| same | `result_source` removed | absent / absent | admitted | no finding |
| same | `native_rc` 5 with `synthetic` | `synthetic` / `5` | **admitted** | **no finding** |

On the query_first base, three different wire states project to the same JSON
and draw the same issue. That issue comes from the ordering rule's
`result_source == "validator"` requirement (porcelain_admission.rs lines
1204–1208), not from a presence check. On the synthetic base, a carried
`native_rc` of 5 with no guard reaches the envelope invisibly. Only the
retained host bytes show it. A synthetic result with a non-null `native_rc`
contradicts RESPONSE line 962, and every reader accepts it. In each case the
lifecycle oracle returned no finding, and the outcome was unchanged
(`validator_unavailable` or `worker_spawn_failed`).

The `team_id` probes on `preparation-0`:

- `identifier` removed with `team_id` kept: both keys were absent from the
  JSON. Rust admission refused with "equipment bound observations", because a
  bound binding needs an identifier. The Python general, actor and extension
  readers returned no finding. That is a semantic-reader difference outside
  this pass, recorded as a lead.
- `team_id` removed: projected `team_id: null`, admitted by all readers.

**Judgment (tentative).** The rule turns an internally inconsistent record into
a consistent-looking public one. A carried value is lost from the JSON, and
nothing in the stated chain says so. The shipped producer never builds the
guard-absent state, so the rule's only effect is on states the producer does
not produce. A stated presence relation would more naturally be refused at
structural or semantic admission, or projected visibly. Related: DT-52 and
DT-53 (consumer tolerance), and DT-110.

### DT-109 — Path-form compaction preserves information and both readers agree, but its size rationale no longer applies: the wire and the envelope carry every path

**Affirmative (executed).** Swift's nine path-state frames combine
equal/NFD-different/absent for both forms of both records, with input
`/café`. The Rust and Python projections were identical. Each form was
in exactly one state:

- listed in `same_as_input` with its key absent;
- present as a different string;
- explicit `null`.

The NFD spelling `/café` stayed a separate string. These frames had been
replayed only by Python (porcelain_replies.py lines 65–82). In the passing
corpus, the cross-reader comparison never contained the null state, while the
equal and different states occurred 264 and 248 times.

**Rationale.** Commit `085bffc7` (2026-09-26, response schema 9) introduced
`same_as_input` because a maximum JSON reply exceeded the then 1 MiB
retention cap. JSON was then the transport. Today the host writes every
resolved form onto the binary wire whether or not it equals the input
(`enrichPathDiagnostics`, PWRunnerService.swift lines 422–447). Only the
projection compacts.

**Executed (live).** One `policy-witness run` with a `file-read-data` query
and an `open_read` attempt on `/private/etc/hosts` exited 0 with `finished`:

- query: `same_as_input: ["realpath_resolved"]`, with a different
  `firmlink_resolved`;
- attempt: `same_as_input: ["realpath_resolved", "parent_realpath_resolved"]`.

The retained host frame is 3,663 bytes and contains the path 11 times.
Its Python projection equaled `data.runner_result`. The 19,809-byte
envelope carries that frame as `runner_client.transport.runner_reply.data_base64`,
24.7% of the envelope, alongside the compacted projection. Compaction saved
three path strings in the JSON. The binary frame and its base64 copy in the
envelope still carry them.

**Cost.** Consumers decode a three-state encoding:

- the guide spends about 40 lines on it (PolicyWitness.md lines 2700–2740);
- `consumer.py` carries a dedicated exclusivity checker (lines 105–136);
- the Rust test path needs a `#[cfg(test)] same_as_input` field to represent
  the compacted state through JSON deserialization (generated lines
  2890–2892 and 2929–2930).

In that test path, `reply_fixtures.rs` lines 28–37 build typed records whose
path forms are `None` while being listed as equal to the input. Production
typed records cannot have that state. The override also accepts a listing for
a form that carries a different value, and then silently drops the value.
No controller code reads these typed fields today.

**Judgment (tentative).** The compaction is lossless and consistently
implemented. Its stated benefit no longer applies at either the wire or the
envelope, while the interpretive cost remains. Emitting each form as a string
or null would keep the byte-identity distinction: a consumer can compare with
`input`.

### DT-110 — Rust and Python apply the presentation rules in different orders; a schema that `validate()` accepts makes them disagree

**Source.** The orders differ:

- Generated Rust (generate_porcelain.py lines 227–247) handles each field by
  the first matching branch: path form, conditional null, optional without
  `json_null`, otherwise always.
- Python (porcelain.py lines 86–106) applies `json_null` to all fields, then
  path forms, then conditional rules. It reads the guard from the
  already-projected result.

`validate()` (lines 105–111) checks that conditional fields are optional and
path forms are optional text. It does not prevent a guard from being a path
form, or a dependent from being one.

**Executed (constructed schema).** `PWRunnerPathDiagnostics` was given
`conditional_null: {"observer": "realpath_resolved"}`. `validate()` accepted
it. The generated Rust line is `if self.realpath_resolved.is_some() {
map.serialize_entry("observer", …) }`. On the Swift frame `0-0`, the realpath
is present on the wire and equal to the input. Python deleted it as
same-as-input, read the guard as `None` and dropped `observer`; the Rust branch
would keep it. On `1-0` (different) and `2-0` (absent), the two agree. The
Rust side is generated code read, not compiled for this schema.

The current schema has no such combination, so the agreement observed in DT-109
and DT-108 is partly accidental: it depends on authored data that neither
`validate()` nor any test constrains. The Python projection control
(porcelain_codec.py lines 157–181) exercises each rule alone.

### DT-111 — What the projection checks establish: shared flags, a shape golden blind to presence and spelling, and a subset comparison that hides one disagreement

**Shared definitions versus separate traversal.** The binary traversal is
implemented separately in Rust (generated readers over porcelain.rs) and in
Python (`Reader`). The projection logic is also implemented twice: generated
Rust and hand-written Python. Every field rule is shared, however:

- names, `json_null`, projections, path forms and conditional rules come from
  `porcelain.json`;
- RESPONSE's presence phrases derive from the same flags
  (record_definitions.py lines 494–509; DT-18).

The cross-reader corpus compares complete dicts, so key presence counts
(reader_corpus.py lines 56–61). It cannot detect a mistaken flag, because both
readers apply it.

**The shape golden does not encode presence or byte spelling (executed).** The
golden is `response_shape.json`, checked at porcelain_replies.py lines
109–125. It was recomputed from the 64 shape frames under mutated tables:

| Mutation | Shape documents changed | Golden changes |
| --- | --- | --- |
| `CompiledProfileCapture.reason` `json_null`→true | 7 | no |
| `PWRunnerSandboxCheckResult.pid` `json_null`→false | 2 | no |
| `ValidatorVerdict.error` `json_null`→true | 22 | no |
| `source_sha256` hex→base64 | 30 | no |
| `PWRunnerSandboxCheckResult` conditional rule removed | 0 | no |
| `PWRunnerPathDiagnostics` path forms removed | 23 | yes |

Two specific assertions would catch particular flips:

- the `pid` flip, by `null_pid` (porcelain_replies.py lines 292–294);
- the base64 change, by live digest comparisons such as contract.py lines
  322–332.

The general readers accept missing and null alike (DT-52 and DT-53). A wrong
omit/null rule on most other fields would pass every registered check.

**A subset comparison hides a fixture/statement disagreement (executed).**
`require_subset` (porcelain_replies.py lines 24–37, applied at line 291)
treats an authored `null` as satisfied by an absent key, and ignores extra
keys. Comparing `tests/fixtures/contract/normal_reply.json` with the decoded
`normal.pwp` found one authored null that the projection omits:
`phases[0].validator_subprocess.records[1].error` (fixture line 387). It also
found one projected key absent from the fixture:
`request_failure.expected_contract`, set by ReplyFailureTests.swift line 90.

RESPONSE line 988 says the validator record's `error` is "omitted when
absent", and the schema has `json_null: false`. The projection follows the
statement; the authored fixture states the other form. The comparison cannot
see the difference.

**Comparisons before or around encoding.** DT-47's two `CWorkerTests`
assertions still read the pre-encoding object (lines 417–425). `run_flow.rs`
has 15 `serde_json::from_value` sites that type replies from JSON through the
`cfg(test)` `Deserialize` derive. Some read authored fixtures; others re-type
the projected `data.runner_result` of an envelope. The derive maps `null` and
absence to the same `None` (DT-104). Outside porcelain.rs's own primitive
tests, the controller decodes binary frames only in the `run_flow.rs`
corpus/driver replays and `runner_client.rs`.

**What a plausible incorrect implementation could still pass.** The following
would pass all registered checks:

- a wrong `json_null` on any field without a dedicated assertion;
- a guard/dependent pair that hides a carried value (DT-108);
- a hex/base64 swap on a digest that no live comparison reads;
- a schema combining path forms with conditional rules (DT-110).

A projection that renders bytes as uppercase hex would fail the Rust spelling
test (porcelain.rs lines 764–776) and the Python control (porcelain_codec.py
lines 72–76).

### DT-112 — Smaller observations on identity and projection

- **Digest width is unchecked for most hex fields (executed).** Root
  `policy_sha256` set to 0 bytes, 1 byte (`ab`) or 32 zero bytes was projected
  as `""`, `"ab"` or 64 zeros. Rust admission and every Python reader accepted
  all three. RESPONSE line 387 calls the field the "SHA-256 … as lowercase
  hexadecimal". Commit `0cdba835` says that, after digests became bytes, "both
  readers check a length". The inspected readers check 32 or 20 bytes only for
  the four equipment-binding digests (porcelain_actor.rs lines 1860–1863);
  other digest fields were not each traced. The same commit's parent checked
  no `policy_sha256` length either.
- **Empty and zero values survive (executed).** These pairs were distinct in
  both readers:
  - empty text (`error: ""`) and `null`;
  - empty bytes (`""` in hex and in base64) and an absent key;
  - `pid: 0` and `pid: null`;
  - `sandboxed_after_apply: false` and an absent key.

  Base64 spellings for 0 to 4 bytes (`""`, `/w==`, `/wA=`, `++++`,
  `////AA==`) and hex agreed between Rust's hand-written encoders and
  Python's.
- **Validator `null` and absence merge before encoding (source).** The native
  validator writes `"error": null` for a native-call record (surface line
  225). The host's admitted
  record has optional fields, "absent or null" (line 202), and the projection
  omits them. Only `raw_line` keeps the native spelling.
- **A local-only field occupies a wire tag.**
  `PWRunnerAttemptResult.execObservationDecodeProblem` holds tag 9, which no
  frame carries. `validate()` requires local-only tags to keep the ascending
  order.
- **Public names name Swift identifiers.** A public-name rename changes the
  Swift writer's tag-constant names (the "Swift writer" column for the rename
  row in DT-105), although the bytes written are identical.

### Wire-identity coverage and remaining investigative limits

The trace covered:

- `wire_identity` and the generator outputs;
- the Swift record writer and the hand-written variant writer;
- both frame decoders and both bound readers;
- generated Rust serialization and the Python projection;
- the documentation generator's presence derivation;
- the controller's two frame-refusal paths;
- the checks cited by the wire surface and ARCHITECTURE rows 611, 942 and
  D78–D80;
- the porcelain replay helpers.

**Answers to the starting questions.**

1. *What changes the fingerprint, and does that boundary match what receivers
   need to distinguish?* Each property the statement names changes it:
   - structure: tags, descriptors, optionality, added fields, records and
     variant cases;
   - presentation: public names, null flags, projections, path-form and
     conditional rules;
   - local names and ordering: record names and order, variant case names
     and types, root keys.

   It does not change for storage names, defaults, comments, source paths,
   `mutable`, local-only fields or `Int`/`Int64` on a field. The boundary is
   wider than what a receiver needs from a producer. Producers consume only
   IDs, tags, kinds and optionality. Several fingerprinted properties are
   inert or invisible on the wire and in JSON (DT-105, DT-106). Operationally
   the exact public-contract check already subsumes it in the controller.
   The fingerprint's own role is a labeled early refusal, and identity for
   unbound test readers.
2. *Which distinctions survive from a producer's value to public JSON?* These
   survive:
   - present versus absent, as omission or `null` per field;
   - zero, false and empty text or bytes against absence;
   - exact UTF-8, including NFC and NFD;
   - byte values, as hex or base64;
   - variant cases, only because their JSON types differ.

   Path forms are compacted losslessly. Lost or merged are a conditional
   dependent carried without its guard (DT-108); the validator's native `null`
   against absence, merged by the host before encoding (DT-112); and the
   variant case tag (DT-107). Digest width is carried but checked for few
   fields (DT-112).
3. *What do the tests establish, and could every implementation agree on an
   undesirable rule?* The tests establish three things: structural refusals
   on constructed bytes; byte-identical cross-reader projection of the Swift
   corpus; and fingerprint sensitivity to comments and five structural edits.
   Every field rule has one source, shared by Rust, Python and RESPONSE. The
   shape golden and the general consumers are insensitive to presence and
   spelling. All layers can therefore agree on an undesirable rule, and do so
   today for the conditional-null suppression (DT-108) and the compaction
   (DT-109). The DT-110 precedence divergence shows agreement that holds
   because of the current schema data.

**Affirmative results within tested scope.**

- The independent fingerprint recomputation equaled every generated constant
  and every Swift frame header.
- The independent codec re-encoded all 261 Swift frames byte-identically.
- For all 40 probe frames and all 153 corpus rows, Rust and Python JSON were
  equal, including key presence.
- The nine path states, including the NFD contrast, followed the documented
  three states in both readers.
- The live envelope's projection equaled an independent projection of its
  retained host bytes.
- The registered cases passed without system sleep.

**Not exercised.**

- A compiled Rust or Swift build from a mutated schema; generated text was
  compared instead.
- The controller's live `run` path with edited frames. Rust projections came
  from the unit-test binary's corpus test, which uses unbound
  `porcelain::decode` and the same generated serializer.
- A foreign-schema or foreign-contract frame through the live controller.
- Client-capture-root projections, except where existing tests cover them.
- Actor-form records beyond the equipment-binding probes.

The `team_id` reader difference in DT-108 is an unresolved lead. Whether an
identity over binary structure alone would serve the Python and Rust test
readers equally well was not established. Neither was whether any external
consumer relies on `same_as_input`.

Only this record was changed among tracked files. The registered run added
development output under `tests/out/runs/wire-identity-trace/`. Scratch probes
and the copied test binary are under the scratchpad. These entries contain no
repair, deduplication or choice of authoritative layer.

## Additional findings: transport failure and helper fallback

### Transport investigation identity and evidence classes

This pass traced transport failure for `policy-witness run`, from client
capture through public result selection, and the independent `sbpl-check`
fallback. It starts from DT-31, DT-32 and DT-42.

**Snapshot and build.**
- Source: `main` at `cc55288d` (2026-11-16), clean tree. `controller/`,
  `runner/`, `docs/` and `tests/` are byte-identical to `4816b0e4`, the tree
  DT-31, DT-32 and DT-42 cite, so their line numbers still apply.
- Shipped app: `dist/PolicyWitness.app`, built from `8b5de2b2` (build 1482,
  `development:bdefcb44…fb18`). Since that commit, those four directories
  differ only in `tests/suites/preflight/opt_in/build_refusals.py`.
- Platform: macOS 26.7.1, build 25G241 (`sw_vers`), Darwin 25.6.0, arm64.
  XPC lookup worked from the investigating shell.

**Cargo-built controller for controlled client runs.**
- `policy-witness` and `sbpl-check` were built from HEAD with an isolated
  `CARGO_TARGET_DIR` and `CARGO_BUILD_BUILD_DIR` under
  `.tmp/contract-trio/transport/target`.
- `PW_BUILD_CONTRACT` was set to the output of `docs/build_contract.py`,
  as `build.sh` does. That output is `development:bdefcb44…fb18`, equal to the
  app's. The built binary's `--version` reports that contract.
- The scratch app `.tmp/contract-trio/transport/b/app/` holds this
  controller and a scripted `pw-runner-client`.
- Its `Contents/MacOS/sbpl-check` is a symlink to the shipped helper, which
  ran in place. The shipped helper hashes to `1d447028…`, matching the app
  manifest.

**Evidence classes.** Every claim below carries one of these labels:

| Label | Meaning |
| --- | --- |
| **N** | Native execution of shipped binaries: the shipped controller, client, host, worker and helper. |
| **C** | Controlled client output. The Cargo-built controller read bytes written by a scripted client. The bytes were recorded from the shipped client and then used verbatim, edited by same-length substitution, truncated (B5a only), or constructed. The controller's own decoding, admission, selection and fallback all ran. |
| **T** | Typed injection in Rust unit tests. A `RunnerClientRun` or `PWRunnerRunResult` is constructed directly, bypassing production decoding. |
| **S** | Source inspection. |

**What ran, and what did not.**
- No case was run through `tests/run.sh`.
- The orchestration tests discussed below were read, not executed. The claims
  made about them concern what they construct and assert, not whether they
  currently pass.

**Artifacts.** All are under `.tmp/contract-trio/transport/` in the local
checkout. That directory is gitignored, disposable and carries no retention
guarantee. It contains:
- `a/`: helper probes.
- `d/`: shipped-controller runs.
- `captures/`: raw native captures `r1` and `r2`.
- `b/`: controlled cases, `summary.json`, and per-case envelopes under
  `b/runs/`.
- `c/`: the native host-loss run and its process log.
- `tools/`: `pwire.py`, a wire reader and writer written independently of the
  generated readers, and the case scripts.

#### Native observations

| ID | Command (shipped binaries) | Observed |
| --- | --- | --- |
| baseline | `policy-witness run --timeout-ms 3000`, ordinary request | `finished`/0. Capture accepted, `invoked`, `runner_reply`. `policy_check` key present and null. `actor_policy_checks` absent. |
| d1 | Same request with `--timeout-ms 1` | `xpc_timeout`/1, `not_invoked`, 0 attempts, `acquisition_stop: overall_deadline`, error stage `acquisition`. Keys `runner_result`, `policy_check` and `runner_sandbox_diagnostics` present and null. `actor_policy_checks` absent. |
| d2 | `_test_overrides.worker_post_apply_hang_ms: 4000`, `--timeout-ms 1500` | `xpc_timeout`/1, `invoked` (elapsed 29 ms), error stage `submission`. `policy_check` null. The control reported host PID 43112. Seen at the terminal, not saved: shortly after the run, `ps -o … -p 43112` printed no process. |
| r1 | `pw-runner-client run --request -` with the built-in service name | Client exit 0, `runner_reply` with 2,575 host bytes. Ordinary request with `capture_compiled_profile`. Saved as `captures/r1.capture`. |
| r2 | `pw-runner-client` with a nonexistent service name, `--timeout-ms 2000` | Client exit 1. 20 attempts, each `transport_error` with stage `acquisition` and reason `xpc_error`. Every attempt carries NSCocoaErrorDomain 4099 "…lookup with error 3 - No such process". Final stop `overall_deadline`, terminal `xpc_timeout`. Saved as `captures/r2.capture`. |
| (c) | Single-actor request, exec `sleep 8`; this run's PWRunner host sent SIGKILL | `xpc_error`/1. See "Native host loss" below. |

For d2, no worker PID was recorded during the run, so nothing is established
about the worker after the client's timeout. A later check was seen at the
terminal and not saved. At 14:43:16, 3 minutes 12 seconds after d2 started,
`ps -axo pid=,ppid=,lstart=,command=` filtered by the pattern
`PWRunner\.xpc/Contents/MacOS/(pw-probe-runner|PWRunner)` matched nothing.
That pattern can match a host, whose argv[0] is its full path. It cannot
match a worker: run (c) later showed that a worker's argv[0] is the bare name
`pw-probe-runner`. So the check shows only that no PWRunner host with that
path in its argv remained. It says nothing about workers.

#### Controlled cases

Every case ran the Cargo-built controller in the scratch app on one request
file. Its scripted client wrote the named capture. Results are in
`b/runs/<case>/envelope.json` and `b/summary.json`.

| Case | Capture written by the scripted client | Request | Client exit |
| --- | --- | --- | --- |
| B1 | r1 verbatim | ordinary, augment `exec_baseline` | 0 |
| B9 | r1 verbatim | same | 1 |
| B8 | r1 verbatim | actor form | 0 |
| B2, B3a, B3b, B3c | r1 with one same-length edit to the embedded host frame (DT-114) | ordinary | 0 |
| B5a, B5b, B5c | r1 truncated by one byte; r1 with its capture contract replaced; r1 with `submission.state` edited | ordinary | 0 |
| B6 | r2 verbatim | ordinary | 1 |
| B4i, B4u, B4s | constructed `xpc_error` capture (DT-118) | ordinary | 1 |
| B4ii | the same constructed capture | actor form | 1 |
| B4iii | the same constructed capture | actor form with invalid parts (DT-117) | 1 |
| B7 | constructed `xpc_error` capture; the client closed stdin unread | ordinary, about 200 KB | 1 |

For B4u the helper was absent. For B4s it was replaced by a script that sends
itself SIGKILL.

Line citations to "Session" refer to
[PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift).
Citations to `main.swift` refer to
[the client entry point](../runner/Clients/PWRunnerClient/main.swift), at HEAD
unless an earlier commit is named.

### Transport answers to the three questions

**1. Which states can reach execution admission and result selection.**
- Every `run` envelope passes through the one selection relation.
- Execution admission (`Disposition::Admitted`) is reached only when all of
  these hold: request delivery succeeded; the current capture was accepted;
  the capture records `invoked` and terminal `runner_reply`; the complete host
  frame decoded under the current schema and contract; and the reply passed
  geometry and compiled-profile admission.
- So in the shipped command, execution admission always comes with
  `submission: invoked` and a decoded host reply. The row for an admitted run
  with no host reply (`runner_response_unavailable`) cannot be selected
  (DT-113).
- Every other combination ends in one of the refusal rows. A decoded host
  projection appears beside a refusal in only one case: the decoded reply
  fails geometry or compiled-profile admission (DT-114).

**2. Which failed boundary decides the outcome.** Precedence runs in this
order, each step evaluated only if all earlier ones passed:
1. request delivery;
2. client-capture retention, presence, decoding and semantics;
3. for an accepted capture, exactly one of two alternatives:
   - (a) with terminal `runner_reply`, the embedded host frame (truncation,
     schema, contract, structure);
   - (b) with any other terminal, that terminal itself.

   An accepted capture has a host frame exactly when its terminal is
   `runner_reply` (runner_client.rs 478–481). The two cannot co-occur, so
   neither has precedence over the other. `failure()` happens to test (a)
   first (623–634).
4. for a decoded reply, host geometry and then compiled-profile labels.

The earliest failed boundary selects outcome, error and exit. It also fixes
what is retained: rejected capture bytes, typed capture, retained host bytes,
or decoded projection. Fallback runs only for an accepted capture whose
terminal is `xpc_error` (DT-116). A combined-fault control confirmed that
delivery failure suppresses capture interpretation and fallback (B7). Other
semantic integrity findings never change the outcome; they change only the
diagnostics.

**3. Fallback: what permits it, what it receives, what it establishes.**
- It is permitted only for an accepted capture whose terminal is `xpc_error`
  and whose request delivery succeeded. The client emits that terminal only
  after it has invoked execution.
- The ordinary-form check receives the held, pretty-printed, augment-resolved
  request.
- For an actor request the host would admit, that same whole-request call
  always fails in the helper's decoder with exit 2. This was observed
  natively (DT-117).
- Each actor whose `sandbox.policy` is a JSON object gets its own policy-only
  check, whatever its mode.
- Each result establishes only that the helper's own process did, or did not,
  compile those bytes. In the native host-loss run, the worker was observed
  running its exec action while the envelope carried only fallback compile
  results.

### DT-113 — The admitted-without-host-reply row cannot be reached through either shipped caller

**Settled (S, with callers checked).**

The client-failure function returns no failure under exactly one condition. In
[runner_client.rs](../controller/src/runner_client.rs),
`parse_runner_client_output` (lines 667–794) and `RunnerClientRun::failure`
(602–650) return `None` only when all of these hold:
- there is no delivery error;
- `transport_admission == "accepted"`;
- there is no `runner_reply_error`;
- the terminal is `runner_reply`.

Under the same condition, the parser returns `Some(typed reply)`. Capture
admission requires a host reply if and only if the terminal is `runner_reply`
(478–481). An untruncated frame either decodes or sets `runner_reply_error`
(744–778).

The search for other constructors and callers:
- `RunnerClientRun` derives only `Serialize` (line 25). Its fields
  `OutputCapture` and `RequestDelivery` also derive only `Serialize` (utils.rs
  lines 15 and 102). Neither `runner_client.rs` nor `runner_commands.rs`
  mentions `Deserialize`.
- `git grep RunnerClientRun -- controller` finds three struct literals:
  - runner_client.rs line 678, in the parser;
  - line 970, `test_client_run_bytes`, which is `#[cfg(test)]`;
  - [run_flow.rs](../controller/src/run_flow.rs) line 4186, inside
    `#[cfg(test)] mod tests` (lines 788 to the end of the file).
- Its only containers are `ExecutionData` and `RunnerVerifyData`. Both derive
  only `Serialize`.
- `run_flow::admit_reply` has two callers: `run` (run_flow.rs 693) and
  `cmd_runner_verify`
  ([runner_commands.rs](../controller/src/runner_commands.rs) 612–626). Both
  take their input from `run_pw_runner_client`.

Consequences:
- `select(&Disposition::Admitted { host_outcome: None, .. })` cannot occur in
  `run`. That is the `AdmittedUnavailable` row of
  [result.rs](../controller/src/interface/result.rs).
- The no-worker assessment `execution_diagnostics(None)` cannot occur in
  `run`.
- Verify's `None` branch, which reports `runner_response_unavailable`
  (`project_verify_typed_reply`, runner_commands.rs 531–545), cannot occur in
  verify.

Statements that describe the unreachable state:
- RESPONSE lines 89, 252 and 300, and the verify rule at 3808, as DT-31
  listed.
- The shipped `policy-witness help result` card prints
  `runner_response_unavailable false 1` (N).

Only typed injections reach the label:
- `each_result_class_agrees_in_fields_process_status_and_card` builds the
  pair `(client_run(Some(&controlled_reply())), None)`.
- `execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields`
  calls `complete_execution` with no reply.
  [CONTRACT](../docs/CONTRACT.md) line 965 credits the latter to Execution
  diagnostics. The failure contract's row at line 687 describes it as
  "Constructed replies cross production assembly". `complete_execution` is
  production code; the assembler `execution_envelope` is a test helper
  (run_flow.rs 793).

**About DT-31's interface-join evidence.**
`controller/interface/joins.json` lists `result.admitted_unavailable` under
`entries_no_case_reaches`. The generator computes that list as entries no
case in the corpus `controller/integration/interface_cases.json` reaches
(`docs/generate_interface.py` 366). The interface README (117–128) describes
the join as a derivation from each case's argument vector and result fields.
For the companion list it says that it reports "a fact about the retained
cases, not a claim that production inputs cannot reach the entry."

The same list also holds `result.admission_refusal` and
`result.admitted_other`. Both are reachable natively:
- d1 selected the admission-refusal row (`xpc_timeout`/1).
- `c/baseline0_bad_request_envelope.json`, the first actor-form baseline,
  selected the admitted-other row. Its accepted, invoked capture carried a
  host reply labelled `bad_request`, and the run ended `bad_request`/1.

(The native ordinary baseline is `finished`/0, the admitted-finished row, not
admitted-other.)

So the list cannot tell an unreachable entry from a reachable one that the
corpus does not cover. The unreachability claim rests on the caller trace
above, not on the join.

**History (S).** `runner_response_unavailable` was introduced in
`2d5080d7` (2026-11-08). Before that, a missing reply fell through to
`runner_output_not_json`. This pass did not establish whether the state was
reachable at that time.

### DT-114 — A foreign producer leaves only retained bytes; the typed-version branch exists only for injected replies

**Settled for the shipped decoder (S); executed through binary decoding (C).**

`decode_bound` ([porcelain.rs](../controller/src/porcelain.rs) 174–222) reads
the host frame in this order:
1. It checks the fingerprint, returning `UnsupportedSchema` on mismatch.
2. It reads root record tag 1, `PWProducer`, and that record's tag 1,
   `contract`.
3. It compares that contract with the build contract and returns
   `UnsupportedContract` on mismatch.
4. Only then does it decode the whole frame.

The generated reader maps tag 1 to `producer` and `PWProducer` tag 1 to
`contract`. `RecordReader` rejects duplicated or out-of-order tags. So any
`PWRunnerRunResult` produced from bytes carries the current contract.

The branch `ReplyVersion::Unsupported` in `run_flow::admit_reply` (343–349)
is therefore reachable only from typed injection. So is the
`unsupported_runner_response` projection in verify.

Controlled-client results (C, `b/runs/`; capture edits made by
`tools/make_captures.py`):

| Case | Host-frame change (same length) | Result | `runner_result` | `runner_reply_error` | Retained host bytes |
| --- | --- | --- | --- | --- | --- |
| B2 | producer contract → `development:fff…` | `unsupported_runner_response`/1, error "runner reply has foreign contract development:fff…" | present, null | that message | equal to the edited frame |
| B3a | first fingerprint byte flipped | `unsupported_runner_response`/1 | present, null | "…unsupported porcelain schema…" | equal |
| B3c | reply record id 55 → 56 | `malformed_runner_response`/1 | present, null | "…not a complete typed record: wrong record identity" | equal |
| B3b | `compiled_profile.capture_stage` `before_apply` → `after__apply` | `malformed_runner_response`/1, error "compiled_profile context is inconsistent" | **decoded record present** | null | equal |

In every case the capture was accepted and `submission` was `invoked`. The
diagnostics key and the `policy_check` key were present and null, and
`actor_policy_checks` was absent.

So a decoded projection beside a refusal exists in production only for the
semantic gate `admission_problem`
([porcelain_admission.rs](../controller/src/porcelain_admission.rs)
1308–1331), which checks geometry and then compiled-profile labels.

**Statements that describe a decoded foreign record:**
- [controller/README.md](../controller/README.md) 184–190: "…or a decoded
  reply carrying another producer contract, produces
  `unsupported_runner_response` … `data.runner_result` holds the decoded
  record's projection when decoding succeeded".
- Guide line 1409: "A decoded but refused producer/context can remain there".
  The *context* half is accurate (B3b). The *producer* half is not.
- 40-envelope `admit`: "then decoded host producer identity and host
  capacity/profile-label admission". This lists producer identity as a
  separate gate after decoding.

**Error text differs by path.**
- Production foreign-contract text (B2): "runner reply has foreign contract
  X".
- The typed path's text, which `delivery_failure_takes_precedence…` asserts:
  "runner reply carries contract X; this controller reads only Y".

**A foreign host is refused earlier (S, plus one N observation).**
- In the shipped host, the control reply's contract
  ([PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
  57) and the reply producer (`PWProducer.current`,
  [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
  175–177) both read `PWBuildContext.contract`.
- Packaged builds generate that value as a single constant
  (`docs/build_contract.py` 96–97).
- The client refuses a control whose contract does not match its own as
  `unsupported_protocol`, giving terminal `protocol_error`
  ([PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
  205–216).
- In r1 the client admitted a granted control, and the embedded frame
  carried the current contract (N).
- So a host from another build is refused during acquisition, as
  `xpc_protocol_error`. The host-frame contract refusal can be reached only
  when a host's control and frame identities disagree, or when bytes have been
  altered, as in B2.
- This connects to DT-105, which examined what the fingerprint covers. The
  schema-then-contract order of the same `decode_bound` gate is what makes a
  typed foreign reply impossible. B2 and B3a reach the same public label from
  those two different checks; only `runner_reply_error` text separates them.

### DT-115 — Tests and controls that build combinations production cannot produce

These tests are T unless marked otherwise. Each item gives what the test
constructs and how that differs from production. The costs are design
judgment and are labelled as such.

1. **`each_result_class_agrees_in_fields_process_status_and_card`** (run_flow.rs 3626–3869).
   - The rows "capture missing", "capture unsupported" and "capture
     malformed", and the three reply-refusal rows, return `Some(typed reply)`
     beside the refusal. The comment reads: "The capture carries a decoded
     `finished` reply beside the refusal."
   - The refused branch passes `runner_result` into the envelope (line 715).
     Those rendered envelopes therefore carry a decoded host record beside
     `missing_runner_client` and similar refusals. Production cannot emit
     that pairing.
   - "Delivery failure beside a received finished reply" pairs a delivery
     error with a typed reply. Production cannot do this: a delivery error is
     checked first and stops all decoding (line 705).
   - "Reply contract foreign" injects a typed foreign record, the DT-114 branch.
   - "Admitted completion with no host reply" is the DT-113 pair.
   - The test asserts outcome, `ok`, exit and card line, not data presence.
     So the impossible pairings neither fail it nor are pinned by it.
   - Cost (judgment): the test reaches every card line, including
     `runner_response_unavailable`, by reaching unreachable states. A reader
     who takes coverage as reachability would be misled.

2. **`delivery_failure_takes_precedence_and_retains_the_client_frame_unread`** (1971–2037).
   - It asserts `admit_reply(&intact, None)` is `Admitted`. Here `intact` is a
     constructed capture with terminal `runner_reply`.
   - It asserts that a typed foreign record is refused with the typed-path
     message.
   - Its envelope uses a hand-built `JsonResult::new(false, 2, …)` rather
     than `select`.

3. **`refused_reply_versions_request_no_fallback_compilation`** (3016–3110).
   - The comment (3017–3024) begins: "Through production admission: a reply
     under another response version is refused before anything reads it, so
     no helper is requested and `policy_check` is null."
   - Production code it exercises: `run` and everything it calls (`admit_reply`,
     `fallback_policy_check`, `actor_fallback_checks`, `select`, rendering),
     `evidence::load_manifest`, and `run_policy_check`. The helper is never
     found beside the unit-test binary, so the fallback capture is
     `unavailable`.
   - Not production: the client dependency returns `client_run(..)`, whose
     embedded host bytes are JSON. The typed reply comes from serde
     `from_value`, which is test-only and skips `decode_bound`.
   - In the narrow sense, the comment is accurate: the label matches
     production, and nothing reads the reply before admission.
   - The gap: the "previous" and "next" rows assert
     `wire["data"]["runner_result"] == reply`, a retained typed record. For
     the same host bytes, production reports `runner_result: null` (B2).
   - The "string" and "missing" rows map fixture-reader failure to
     `ReplyRefusal::Malformed` with a null projection. That matches
     production.

4. **Consumer `policy_check_controls`**
   ([checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py)
   39ff, through `envelope_skeleton` in
   [blackbox.py](../tests/lib/blackbox.py) 54–112).
   - These controls wrap helper captures in an envelope whose `runner_result`
     has `normalized_outcome: "xpc_error"` and whose capture terminal is
     `runner_reply`.
   - Since `34496c0f` (2026-10-29), fallback in production has never
     accompanied a host reply or a `runner_reply` terminal.
   - History (S): the fixture form predates that change. `git log -S` finds it
     back to `4e02cf51` (2026-10-03). At `29e3ead0` the client synthesized an
     `xpc_error` *reply*, and fallback keyed on that reply's outcome (run_flow
     line 380 at that commit).
   - The consumer's helper-envelope admission does not depend on the outer
     state. So the control still tests that admission, and the surrounding
     envelope is a leftover from the earlier design.
   - [ARCHITECTURE](../docs/ARCHITECTURE.md) row B9 credits these controls,
     with `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`,
     for "associated with the selected policy/actor". Neither contains an
     actor or checks association. The consumer has no `actor_policy_checks`
     handling (`git grep` in `tests/lib/consumer.py`).

5. **The field-complete shape fixture** (run_flow.rs 3940–4243). It combines
   mutually exclusive fields, including both client stdout errors on an
   accepted capture, but it says so ("Field-complete shape fixture"). It
   feeds the shape golden only. It is listed here for completeness and is not
   a finding.

### DT-116 — Fallback eligibility coincides exactly with an invoked client `xpc_error`; the fallback calls on the admitted branch can never run

**Settled (S), with N and C confirmation.**

The admitted-branch fallback calls are dead code.
- `fallback_eligible` (runner_client.rs 651–661) requires an accepted
  capture, no delivery error and terminal `xpc_error`.
- For any `RunnerClientRun`, however it was built, those conditions make
  `failure()` return `Some(Refused(..))`.
- So the calls on the `Admitted` branch (run_flow.rs 699–701) cannot run for
  any value. Fallback runs only on the refused branch (715–724), with
  `runner_result` and `runner_sandbox_diagnostics` null.

`xpc_error` always means `invoked`.
- `validate_capture` requires `invoked` for that terminal (516–529).
- The Swift session emits it only from `connectionFailed` during the submitted
  phase (Session 192–197).
- With the shipped client, outcome `xpc_error`, fallback invoked, and
  `submission: invoked` therefore always occur together.

Fallback does not track whether execution may have happened.
- A native invoked timeout (d2) has the same receipt uncertainty and gets no
  fallback.
- A lookup failure never yields fallback. Lookup errors are acquisition-stage
  attempts, as r2 shows: the same NSCocoaErrorDomain error class as an
  eligible `xpc_error`, but at the acquisition stage.
- Conversely, `proxy_type_mismatch` during submission is an eligible
  `xpc_error`, yet `proxy()` returned nil and nothing was sent. `invoked` was
  recorded before the proxy was acquired (Session 248–252; session control
  "proxy failure during submission…", `PWRunnerClientSessionTests/main.swift`
  158–167).

What `submission: invoked` establishes.
- The client process records it in `reservationReply`, on its serial queue
  (Session 223–252), after admitting a granted control and re-sampling the
  clock, and before it calls `submit` (251–252).
- It is the client's own report, checked by `validate_capture` 446–473.
- It establishes that the client crossed its one execution-call boundary. It
  does not establish that a message was sent or received, that the host
  admitted the credential, or that anything executed.

Rationale and history (S).
- The fallback was introduced in `ba483826` (2026-06-11). That commit's
  message says the host compile "now runs only on `xpc_error` (to tell a
  never-compiled policy from one that compiled but blocked the XPC reply)".
- The same commit put the rationale in two other places:
  - the guide, then `PolicyWitness.md` at the repository root (line 110 at
    that commit): "only to disambiguate an `xpc_error` (a policy that
    compiled but then blocked the XPC reply vs. one that never compiled)";
  - a module comment in `controller/src/run_flow.rs`: "only to disambiguate
    an `xpc_error` (compiled-but-reply-blocked vs. never-compiled)".
- Current documents disclaim that inference: the fallback "establishes
  neither worker progress nor the cause of a lost reply" (README 224; guide
  767–768).
- No current statement gives another reason for restricting fallback to
  `xpc_error`.
- Cost (judgment): a present `policy_check` implies only
  `submission: invoked`, which the capture already records. An absent one
  says nothing about whether the specimen may have executed: d2 was invoked
  and has none. So the field adds nothing about possible execution beyond the
  submission state.

Statements implying a pairing that cannot occur:
- 11-policy line 392: the capture reports the attempt "alongside the
  transport result and any retained worker evidence". No worker evidence is
  ever present.
- Guide 1515: "an independent fallback compiler result may also be present"
  for `xpc_error`. With the shipped host it is always present (see DT-119 for
  the host-label case).
- README 232–234 says `execution_envelope` "assembles the dossier,
  transport, acquisition history, independent fallback compilation and
  execution diagnostics". ARCHITECTURE 462–466 says `execution_envelope`
  "assembles the execution records". That function is a `#[cfg(test)]`
  helper (run_flow.rs 793). In production, fallback and diagnostics never
  coexist in one envelope.

**ARCHITECTURE 467**: "The client's timeout ends the controller's wait and
yields a synthetic `xpc_timeout` reply." This wording entered at `29e3ead0`
(2026-10-05). At that time the client did synthesize a `PWRunnerRunResult`
with `xpc_timeout` (`runner/Clients/PWRunnerClient/main.swift` 156–170 at that
commit). `34496c0f` replaced
that with the capture. The sentence describes the earlier design. d1 and d2
show that `runner_result` is null on timeout (N).

**Combined-fault control (C, B7).**
- Inputs: the constructed `xpc_error` capture and a 200,241-byte request. The
  scripted client closed stdin and then wrote the capture.
- Result: `tool_error`/2, error "request delivery failed after 65536 bytes:
  Broken pipe (os error 32)", `transport_admission: delivery_failed`,
  `submission: unknown`, transport `Rejected` with bytes equal to the
  capture, `policy_check` present and null, `actor_policy_checks` absent.
- Two readings of the 40-envelope `admit` effect are ruled out:
  - that an `xpc_error` terminal inside the capture can authorize fallback
    beside a delivery refusal ("another refused boundary … Eligible
    xpc_error can add independent fallback compilation");
  - that the client's terminal takes precedence over delivery.
- With the shipped client, this pairing is unlikely natively, because the
  client reads stdin to EOF before connecting (main.swift 104–108).

### DT-117 — DT-42 settled: the actor-form whole-request helper fails to decode, beside ordinary per-actor compilations

**Native host loss (N, `c/`).**
- Request: one applied actor `zeta`, whose policy is `(version 1) (allow
  default)` with augment `exec_baseline`. Its one action runs `/bin/sh -c
  "/bin/sleep 8; true" trio-transport-k8b2d4`.
- Baselines without a kill:
  - The single-actor request used for the kill, with `sleep 1`, finished/0
    (`c/single_baseline_envelope.json`).
  - A three-actor variant with `sleep 1` finished/0 in 1.1 seconds
    (`c/baseline_envelope.json`).
  - An earlier three-actor variant omitted `sandbox_check` and was refused by
    the host as `bad_request`, reaching the admitted-other row
    (`c/baseline0_bad_request_envelope.json`).

Target identification (`kill_driver.py`, `kill_log.json`):
- The process with the nonce (PID 71752) had parent W = 71750.
  `proc_pidpath(W)` was the app's `pw-probe-runner`.
- W's parent H = 71748 had `proc_pidpath` equal to the app's `PWRunner`.
- H's only child was W.
- H was absent from a process snapshot taken before the controller was
  launched.
- `launchctl print pid/71747` (the controller's `pw-runner-client`) listed
  `71748 … com.policywitness.policy-witness.PWRunner` in that client's
  per-process domain.
- The service's Info.plist declares `ServiceType = Application`.

SIGKILL was sent once, to 71748, 0.19 s after launch. The controller exited
19 ms after the signal, 0.21 s after launch (`kill_log.json` event times). In
that interval it ran both helper calls. Its envelope:
- result `xpc_error`/1, error "connection to service named
  com.policywitness.policy-witness.PWRunner";
- capture accepted, `invoked` (elapsed 23 ms), `acquisition_stop: granted`;
- error stage `submission`, reason `xpc_error`, NSCocoaErrorDomain 4097;
- the control-reported host PID was 71748;
- `runner_result` and `runner_sandbox_diagnostics` present and null.

The fallback captures:
- **`policy_check`**: `status: "tool_error"`, `tool_exit_code: 2`, envelope
  null, stdout 0 bytes, stderr "failed to parse request.json: missing field
  `policy` at line 44 column 1".
- **`actor_policy_checks`**: `[{"actor_id": "zeta", "policy_check": {status:
  "ok", tool_exit_code: 0, …}}]`. The helper's `policy_sha256` was
  `7a3962a7…`. That equals the dossier's `applied_sha256` and the
  independently computed SHA-256 of the source plus `"\n"` plus
  `exec_baseline.sb`.

Process aftermath:
- Saved in `kill_log.json`: immediately after the controller exited, the
  host was gone. W (now with parent 1), the `sh` child and its `sleep` were
  still present, with the same PIDs, start times and commands.
- Seen at the terminal, not saved: at 14:48:43 (`date`), 20 seconds after
  start, `ps -o pid=,ppid=,lstart=,command= -p 71750,71752,71753` printed no
  process and exited 1. So no process with any of those PIDs existed then. I
  sent no cleanup signal. The only record of this check is the
  investigation transcript.
- An earlier attempt sent no signal: its identification predicate failed
  because the worker's argv[0] is not a path. That run finished normally
  (`kill_attempt0_no_signal_*`).
- During the observed run, the worker ran the exec action. `kill_log.json`
  records the nonce-carrying `sh` as W's child, before and after the signal.
  The envelope holds no host evidence of that execution. Its only policy evidence is the dossier
  and two helper results.

**Controlled replay (C, B4).** A constructed `xpc_error` capture was used
(DT-118 gives its derivation and acceptance). Each fallback call ran the shipped
helper through the symlink.

| Case | Request (held bytes) | `policy_check` | `actor_policy_checks` |
| --- | --- | --- | --- |
| B4i | ordinary with `exec_baseline` (1,794 B) | `ok`/0, helper hash `7a3962a7…` = spliced expectation | absent |
| B4ii | actors: zeta (augmented), middle unapplied, alpha `(allow no-such-operation)` with params (2,556 B) | `tool_error`/2, stderr "…missing field `policy` at line 52 column 1" | `zeta ok/0` (hash `7a3962a7…`), `alpha compile_error/1` (hash `a8cf11b5…`) |
| B4iii | actors plus non-null top-level `(deny default)`; modes `"future"` and `9`, `actor_id: 17`, scalar policy, unapplied with policy (1,002 B) | `ok`/0, hash `46f655c8…`: the top-level policy, which the host refuses as `exclusive_plan_forms` | `future ok`, `null ok`, `unapplied_with_policy ok` (`(deny default)` hash); the scalar policy is omitted |

Helper-only probes (N, `a/`), shipped `sbpl-check --request -`:

| Input | Exit | Output |
| --- | --- | --- |
| Actor held request, no top-level policy | 2 | stdout empty, "missing field `policy`" |
| `"policy": null` | 2 | "invalid type: null, expected struct CheckPolicy" |
| Non-null top-level policy | 0 | `ok` |
| Per-actor objects | — | `ok`/0 and `compile_error`/1 |

**What each invocation receives (S, confirmed by helper hashes).**

*Whole-request call.*
- It receives the held string from `serde_json::to_string_pretty` (run_flow
  678), after augment resolution and selector stripping. That is the same
  string the client receives.
- `sbpl-check`'s `CheckRequest { policy }` has no `deny_unknown_fields`
  ([sbpl-check.rs](../controller/src/bin/sbpl-check.rs) 48–58, 433–439). It
  reads only `policy.format`, `policy.sbpl_source` and `policy.params`.
- A host-admissible actor request has no top-level policy, because the host
  refuses a non-null one
  ([PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift)
  127–132: `exclusive_plan_forms` at path `["policy"]`; sibling refusals at
  138 and 141).
- So for every such request the whole-request result is a decode failure:
  exit 2, empty stdout, `tool_error`
  ([policy_check.rs](../controller/src/policy_check.rs) 84–93).
- Controller admission has no form check: it checks only object, contract,
  mode injection, selector, selection and augments (request_patch.rs 47–100;
  run_flow 576–670). An actor request with a non-null top-level policy
  therefore reaches the client, and on fallback its top-level policy is
  compiled (B4iii).

*Per-actor calls.*
- `actor_policies` is collected after actor augment resolution and before
  delivery (run_flow 616–643). It contains every actor whose
  `sandbox.policy` is a JSON object, whatever its mode, so invalid and
  `unapplied` modes are included.
- Each call receives compact `{"policy": <object>}` (377–394).
- The calls run sequentially after the whole-request call (716–724).

*Association.*
- `actor_id` is the declaration's string label, or null.
- A check is tied to its actor only by that label and by its position among
  policy-bearing actors. In B4iii the dossier lists four actors
  (`future`, null, `scalar`, `unapplied_with_policy`) against three checks.
  Only the null label at check index 1 depends on order.

*Exit-code provenance (C).*
- B4u, helper absent: `status: "unavailable"`, `tool_exit_code: 1`, stderr
  "embedded tool not found in Contents/MacOS: \"sbpl-check\" …", stdout and
  stderr byte counts null.
- B4s, helper replaced by a script that reads stdin and then sends itself
  SIGKILL: `status: "tool_error"`, `tool_exit_code: 1`, stderr empty, counts
  0.
- A helper killed by a signal is therefore recorded as exit 1 (`code()
  .unwrap_or(1)`, policy_check.rs 78). That is indistinguishable from a helper
  that printed nothing and exited 1.
- The 11-policy `tool_exit_code` text ("Helper process exit code, or the
  capture's fallback value when unavailable") omits the signal case.
- A helper delivery failure returns `Err` and discards the helper's actual
  output (policy_check.rs 69–73). This is source only; the helper reads
  stdin to EOF first.

**What the statements say.**
- controller/README 5–8: "it checks the held whole request and each carried
  actor policy object". For actor requests the whole request is not checked;
  it fails to decode.
- No statement says that `policy_check` is `tool_error` for every eligible
  actor-form fallback:
  - 40-envelope `policy_check` (RESPONSE 254);
  - 11-policy `classify` (688) and `actor_check` (713);
  - guide 861–864 and 1073–1075.
- 11-policy `read` (236) does state, for `controller_helper_stdin`, that
  decode errors exit 2 and are reported on stderr. So the helper side of the
  outcome is documented, while the run-level consequence is not.
- Guide 1074–1075: "These independent compile diagnostics can run before host
  admission". In the native run, the fallback ran after the host had admitted
  the request and the actor's worker had begun its action. The checks are
  independent of host admission; they are not ordered before it. The
  contract's wording, "Collection of these policy objects precedes host
  admission", is accurate.
- Cost (judgment): one actor-form envelope carries a `policy_check` with
  status `tool_error` and exit 2 beside per-actor `ok` or `compile_error`
  captures. No statement explains how they relate. A reader can mistake the
  decode failure for a helper or controller fault.

**What the tests credited for this establish.**
- `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`
  (run_flow 3237–3406) substitutes the helper. Call index 0, the whole
  request, always returns `Err`. The test therefore asserts
  `policy_check.status == "unavailable"`, where production gives
  `tool_error`/2. It does establish the inputs: the held string first, then
  the resolved policies in order, then the labels.
- `actor_fallback_uses_held_policy_objects_before_host_mode_admission`
  (3113–3234) returns `Err` for every call. It establishes collection
  independent of mode, and the held bytes. It is credited in 42-dossier and
  CONTROLLER 313–319.
- ARCHITECTURE T12 (229) cites `fallback_compilation_…` and
  `refused_reply_versions…`, which contain no actor input, for "independently
  associated actor-policy diagnostics".
- `failure_boundaries/fallback_helper`
  ([check.py](../tests/suites/failure_boundaries/check.py) 415–438) runs the
  shipped helper with a file path on a source over 4 MiB and asserts
  `policy_too_large`. That establishes the helper's own admission, not the
  controller's fallback path, stdin delivery or the actor form.

### DT-118 — The constructed `xpc_error` capture, and what nothing binds

**Derivation (S, C).**
- B4 and B7 use `B4_constructed_xpc_error.capture`, 782 bytes. It keeps r1's
  root fields 1–12 byte-for-byte: identity, clock, the granted attempt with
  its admitted control, `acquisition_stop: granted`, and
  `submission: invoked` at 31 ms.
- It then adds terminal `xpc_error` (tag 13) and an error record (tag 14,
  record 67). That record has stage `submission`, reason `xpc_error`, domain
  NSCocoaErrorDomain, code 4097, the message "constructed: …" and two false
  truncation flags.
- This follows the Swift emission:
  - `connectionFailed` sets stage `submission` in the `.submitted` phase and
    completes `"xpc_error"` (Session 192–197);
  - `complete` leaves `acquisition_stop`, attempts and submission as recorded
    (276–283);
  - `PWRunnerTransportError.init` records the NSError domain and code
    (PWRunnerTransport.swift 105–116);
  - no `runner_reply` is present.
- The controller *accepted* it: `transport_admission: accepted`,
  `submission: invoked`.
- Its acceptance is part of the result. The native capture from (c) has the
  same shape, with message "connection to service named …" and code 4097.

**No binding between capture and request (C).**
- B8 used r1's capture, from an ordinary request with
  `specimen_id: trio-transport-r1`, under an actor-form request
  (`trio-b-actor`).
- Result: admitted `finished`/0. The dossier listed three actors, the reply
  carried no `execution_form`, diagnostics were an ordinary `clean_exit`, and
  the reply's `specimen_id` differed from the request's.
- Nothing compares the capture or reply with the held request.
- B9 shows that the client's exit code is recorded and not consulted: r1 with
  scripted exit 1 was admitted as `finished`/0, with
  `runner_client.exit_code: 1`.
- With the shipped client, the binding holds by construction: one process
  reads the held bytes from stdin and submits them. These results are not a
  native fault. They show that the controller's admission does not itself
  check that binding.

### DT-119 — Smaller observations on labels, error precedence, notation and host bytes

- **Refusal spellings shared with host labels.** AdmittedOther copies any
  host label. A current-contract reply labelled `xpc_error` therefore
  produces outcome `xpc_error`/1 with `runner_result` present and no
  fallback. `refused_reply_versions…` asserts this (T). The shipped host
  never emits that label (`git grep` finds `xpc_error` in no file under
  `runner/Sources`). The guide's row for `xpc_error` (1515) describes only
  the client capture.
- **DT-32, error precedence (S).** `stdout_parse_error` is set only in the
  decode-failure arm, which returns `Err` (runner_client.rs 724).
  `stdout_capture_error` forces `Err("malformed")` (708–710). B5a and B5b set
  `stdout_parse_error` with a refused capture; B5c refused on semantics with
  no `stdout_parse_error` (C). The second and third precedence tiers in
  40-envelope (RESPONSE 243) cannot follow execution admission. No test
  passes those errors through `complete_execution`.
- **DT-32, collection bound.** `git grep` for `reply_capacity` or
  `reply_geometry` in `controller/` and `tests/` outside
  `porcelain_admission.rs` finds nothing. No test carries an over-capacity
  reply through `run`. The capacity gate shares `admission_problem` with the
  label gate. B3b exercised that path through binary decoding for the label.
  Capacity remains source-only for `run`.
- **DT-32, label effect notation.** RESPONSE 2619 renders the label effect
  as `withhold(envelope.data.runner_sandbox_diagnostics)`. 2866 and 2885 use
  `set_value(…, null)`. The notation table defines `withhold` only as
  "Withhold that target" (tree.py 1450). The surface golden
  `tests/fixtures/contract/surfaces/envelope.json` records the field as
  `json_null: true, omission: null`, meaning always present. The shape golden
  `envelope_shape.json` is an allowlist and blind to presence (DT-111). B3b's
  real envelope has the key present with null (C). The two statements differ
  in notation only.
- **Integrity findings do not select the outcome** (relayed by the
  acceptance pass; verified, S). `select` never reads
  `Disposition::Admitted.integrity_issues` (result.rs 202–237; only run_flow
  730–742 computes it). This matches 40-envelope 189–194. Only geometry and
  compiled-profile problems refuse admission. Every other semantic finding
  changes diagnostics only.
- **Host reporting fallback** (relayed; verified, S). `pwRunnerReportData`
  ([PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
  123–155) always emits something:
  - first the validated report;
  - then a rich `runner_reporting_failed` reply;
  - then a minimal reply;
  - then, at line 154, empty `Data()`.

  Every writer uses `PWProducer.current`. Whatever bytes result are sent
  with `reply(true, data)` (339).

  What happens to empty bytes is partly source and partly inference:
  - **Client side (S, Swift client).** `submissionReply` does not check
    length when `isResult` is true. It stores `PWRunnerReplyCapture(data)` and
    completes `"runner_reply"`
    ([PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
    260–262). For empty data, `PWRunnerReplyCapture.init` records
    `bytes_received` 0, `bytes_retained` 0 and `truncated` false
    ([PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
    163–168). `emit` exits 0 for terminal `runner_reply` (main.swift 30).
  - **Controller side (S).** `validate_capture` tests whether a host reply is
    present by the `Option`, not by length (runner_client.rs 478–481). Its
    retention checks hold for zero (575–587). `decode_bound` refuses a frame
    shorter than 36 bytes as `Malformed` (porcelain.rs 179–181), which yields
    `malformed_runner_response` with a null projection. Through the real
    parser, `arbitrary_rejected_host_bytes_survive_and_do_not_become_claims`
    constructs a capture with empty host bytes and asserts that label.
  - **Inference, not observed.** That NSXPC delivers a zero-length `Data`
    argument to the client's reply block as an empty `Data`, rather than
    failing. No path that reaches the empty writer was executed.

  The rich and minimal replies would be admitted with the host label
  `runner_reporting_failed`/1.

  If the NSXPC inference above holds, the empty writer gives a native route
  by which a shipped client delivers malformed host bytes. It is the only
  such route I found in the host writers I traced. That is a judgment from
  the trace, not the result of a search designed to rule out others. The
  route was not exercised.
- **Accepted-but-unproduced client vocabulary.** The client never emits
  error reasons `interrupted` or `invalidated`
  (`git grep` in `runner/Clients` and `runner/Sources` finds them only in the
  host's own connection handlers). `validate_error` accepts both
  (runner_client.rs 126–143).

### Transport precedence and retention (question 2)

The first failing row decides the outcome. Each cell is marked with its
evidence class.

| Boundary that failed first | Outcome / exit | `submission` | `runner_client.transport` | `runner_result` | Fallback | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Client launch, deadline setup or tool resolution | `tool_error`/2 | — (`runner_client` null) | — | null | no | S |
| Request delivery | `tool_error`/2 | unknown | rejected bytes, never decoded | null | no | C (B7) |
| Retention loss (>272 MiB) | `malformed_runner_client`/1 | unknown | rejected prefix | null | no | unit test through the real parser (`retention_loss_precedes_decode_and_keeps_exact_prefix`) |
| Empty stdout | `missing_runner_client`/1 | unknown | null | null | no | S |
| Capture schema or contract | `unsupported_runner_client`/1 | unknown | rejected bytes | null | no | C (B5b) |
| Capture frame malformed | `malformed_runner_client`/1 | unknown | rejected bytes | null | no | C (B5a, r1 truncated by one byte) |
| Capture semantics | `malformed_runner_client`/1 | unknown | rejected bytes | null | no | C (B5c) |
| Accepted; host reply truncated | `runner_reply_truncated`/1 | invoked | typed, prefix retained | null | no | S |
| Accepted; host schema or contract | `unsupported_runner_response`/1 | invoked | typed, bytes retained | null | no | C (B2, B3a) |
| Accepted; host bytes malformed or empty | `malformed_runner_response`/1 | invoked | typed, bytes retained | null | no | C (B3c), T |
| Accepted; terminal not `runner_reply` | that refusal/1 | `not_invoked` or `invoked` | typed | null | only `xpc_error` | N (d1, d2, c), C (B6, B4) |
| Decoded; geometry or profile labels | `malformed_runner_response`/1 | invoked | typed | **decoded, retained** | no | C (B3b) |
| Admitted | host label; `finished`/0, otherwise 1 | invoked | typed | decoded | no | N (baseline), C (B1) |

The four rows beginning "Accepted; host …" and "Accepted; terminal not
`runner_reply`" are alternatives, not a sequence. The three host-frame rows
apply only with terminal `runner_reply`; the terminal row applies only
without it. Of the three host-frame rows, truncation is tested before
decoding, and the fingerprint before the contract.

For every row except the last, `runner_sandbox_diagnostics` is present and
null. For rows with N or C evidence, the saved envelopes show it. For the
S and unit-test rows, it follows from source: `tool_error` and
`execution_only` both set it to `None` (run_flow.rs 154–164 and 715), and
`RunData` has no skip rule. `actor_policy_checks` is omitted unless fallback ran for an
actor request.

### How DT-31, DT-32 and DT-42 relate

The three findings share one mechanism (S). Client-capture admission
(`failure()`) gates `complete_execution`, and fallback eligibility is a
subset of the `failure()` refusals. Three consequences follow from that
single gate:
- execution admission always carries a decoded host reply (DT-31);
- the client stdout errors never reach the post-admission precedence (DT-32);
- a fallback capture never shares an envelope with a host report or with
  execution diagnostics (DT-42 / DT-116).

The same states survive in code and tests because injected constructors and
JSON-decoded fixtures produce them (DT-115).

DT-31's foreign-producer half and DT-42's actor-form branch are different
boundaries:
- the first concerns the order of `decode_bound`;
- the second concerns the helper's decoder and the absence of a form check
  in the controller.

In the paths I traced, I found no further dependency they share. That is a
judgment from this trace. It is not the result of a search designed to rule
one out.

### Transport coverage and remaining limits

**Traced.**
- The client parser, capture validation and `failure()`.
- `admit_reply`, `complete_execution`, the fallback functions and `run`.
- `select`, `policy_check.rs` and `sbpl-check.rs`.
- Verify's use of the admission path.
- The Swift session and entry point.
- The host's control and report writers.
- The stated contracts:
  - 20-transport, 40-envelope, 41-diagnostics (admit and geometry), and the
    11-policy helper and fallback sections;
  - the corresponding passages in the controller README, guide, ARCHITECTURE
    and CONTROLLER;
  - the failure contract's transport paragraph.

**Not done.**
- No `tests/run.sh` case was run. Statements about tests rest on reading
  their bodies.
- A native truncated host reply (between 96,468,992 and 134,217,728 bytes), a
  native empty reply and a native reply over the capacity bound were not
  produced.
- A native `xpc_error` for the ordinary form was not produced. B4i covers that
  path with controlled output.
- `runner verify` was traced only as a second caller.
- Whether `runner_response_unavailable` was reachable before `34496c0f` is
  open.

**Limits of the evidence.**
- The C cases establish how the controller handles bytes. They do not
  establish native client or host behaviour.
- The (c) run is one native observation, made with a forced host kill. It
  establishes that the run-level outcome exists. It does not show how often
  such failures occur.
- The constructed capture's acceptance is an observation. Its resemblance to
  the native (c) capture was compared by fields, not by bytes.
- No change to code, tests or documentation accompanies this report.

## Additional findings: observation ownership and time

### Observation-time investigation identity and evidence classes

This pass asks whose observation each returned field records and what time it
describes. It starts from DT-46, DT-62, DT-63, DT-66 and DT-68. Those entries
keep their own scope. The entries below extend them, qualify one history note in
DT-46, and record new findings as DT-120 to DT-129. No layer is chosen to change
and no repair is proposed.

**Snapshot and build.**
- Source inspection used clean `main` at `cc55288d033023ce2f18e8c02cd51a400ef2b530`
  on 2026-11-16, with macOS 26.7.1 (25G241) on arm64. Line numbers below refer
  to that snapshot.
- The existing `dist/PolicyWitness.app` reports commit `8b5de2b2`, version
  0.3.7, build 1482, and contract
  `development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
- `git diff --stat 8b5de2b2 HEAD -- controller runner tests docs` shows only the
  one-line change to `tests/suites/preflight/opt_in/build_refusals.py`.
- The executable hashes match the failure-contract investigation's table:
  - `policy-witness` `4bcd308b…`
  - `PWRunner` `706d9a6c…`
  - `pw-probe-runner` `d6d38f09…`
  - `sb_api_validator` `ccbf9803…`
  - `pw-probe-runner-unentitled` is `ee2a4248…`.
- The app was neither rebuilt nor modified.

**Kinds of evidence.** Four kinds appear below, and each claim names its kind.

1. *Public CLI execution.* E1–E5, and two path-length checks (E7a/E7b) made
   after the first validation, ran
   `dist/PolicyWitness.app/Contents/MacOS/policy-witness run SPECIMEN`, capturing
   stdout, stderr and exit status separately.
   - The runs were made outside the automation sandbox from the start, because
     earlier passes recorded XPC lookup error 159 inside it. No in-sandbox
     attempt was made in this pass.
   - Every capture has empty stderr.
2. *Internal driver observation (E6).* This is not a public response. Its build
   and execution:
   - `runner/Sources` and `runner/Package.swift` were copied unchanged; `diff -r`
     reported no difference before and after the build.
   - The only addition is my own `Tests/PWRunnerCoreTests/main.swift` (SHA-256
     `7d88c93f…`).
   - Build command: `swift build --jobs 2 --package-path … --scratch-path …
     --product PWRunnerCoreTests`, run outside the sandbox with Apple Swift 6.4.2
     and the macOS 27.2 SDK. The executable SHA-256 is `2750ec0e…`.
   - It ran against the signed app's `pw-probe-runner-unentitled` and
     `pw-probe-runner`. Those executables were used in place and read only.
   - It decodes the request with the app contract, normalizes and translates it
     with the production `ActorTranslation`, and runs `ActorScheduler`.
   - Its `ActorScheduleInput` (driver `main.swift` line 40) sets no `didSetUp`
     hook, so equipment binding and live code inspection do not run. Validator
     collection, reply validation and encoding are also absent.
   - It reads host custody state from the collection hook (line 88) and again
     after `run()` returns.
   - It counts nonzero bytes only (lines 43–49); no token byte was printed or
     written. It reaches the private custody buffer pointer through `Mirror`
     (lines 51–56) without changing any access control.
3. *Source and test inspection.* This covers the cited lines.
4. *History inspection.* This uses `git log -S/-G` and `git show`.

All live runs (E1–E5, E7a/E7b and E6) were invoked through
`tests/lib/checkout_lock.sh`. That is recorded only in this pass's command
history; the saved captures do not record it. No registered test case was
executed, and no suite pass is claimed.

**Artifacts and availability.**
- Specimens, the specimen generator, the CLI runner, the summarizer, captures
  and driver outputs are under `.tmp/contract-trio/observation-time/` in the
  local checkout. That directory is gitignored, disposable and has no retention
  guarantee. The E7a/E7b captures are `runs/c7_len45` and `runs/c7_len55` there.
- The main target file is `/private/tmp/pw-trio-ot-xVGRMW/target`. The E7a/E7b
  targets sit in sibling `pw-trio-ot-len45-*` and `pw-trio-ot-len55-*`
  directories. On this machine `/private/tmp` does not survive a reboot.
- Each target holds the 27 bytes `authority lifetime witness\n` (SHA-256
  `7482bce4…`). The main target (device 16777233, inode 278532339) was unchanged
  after E3.

**Rebuilt specimens.**
- E1 rebuilds DT-62's issue-only specimen and E3 rebuilds DT-66's two-actor
  specimen from the record's descriptions; the original scratch is gone.
- The target content and length match DT-59. The target path and inode differ
  from DT-59/DT-66 (`/private/tmp/pw-authority-trace-3QC3qQ/target`, inode
  277408216).
- The original files' mode and the original step and phase identifiers are
  unknown. The rebuilt identifiers are in the specimen files.
- Actor A is unapplied with `equipment: "unentitled"`. B in E3 is applied with
  the default selected equipment and DT-66's exact policy.
- Token lengths varied with the target path's byte length in these runs.
  - DT-62's driver printed an accepted length of 216, while E1a, E2 and E6 show
    208.
  - E7a and E7b reran E1a's specimen with target paths of 45 and 55 bytes. They
    gave issue `token_length` 216 and 226.
  - With E1a's 37-byte path giving 208, the published length equals 171 plus the
    path's byte length in all three runs. The constant is not explained here.
  - DT-62's path (`/private/tmp/pw-authority-trace-3QC3qQ/target`) is 45 bytes.
  - This is a length correlation only; no token content was inspected.

**Terms used here.**
- *Native operation*: the private-library or system call itself.
- *Publication*: a worker or host release store that makes a value eligible to
  read (slot `completed`, call-boundary marker, setup cell, outbound
  `committed`, host acknowledgement).
- *Host observation*: a value the host records from its own call or read
  (waitpid, kill, custody acceptance, transfer answer).
- *Assembly decision*: a value computed while building the reply.
- A *copy* repeats one stored value. A *derivation* maps it. An *independent
  observation* comes from a different call or read.

### DT-120 — `cleanup_trigger` is derived from the stored stop reason and has been fixed at final collection since `c686a05f`; one string fills seven reply values

This entry adds to DT-46 and leaves its scope intact.

**Producers and copies.** A single stored string, `ActorSession.pollStopReason`,
produces all of these values:

| Reply value | How it is obtained | Fixed at |
| --- | --- | --- |
| `poll_stop_reason` | copy (`ActorSession.swift` 742) | last assignment to `pollStopReason` |
| `sentinel_wait.stop` (single-worker only) | copy taken when the polling loop ends ([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) 1271) | loop exit, before `requestExit` at 1276 |
| `cleanup_trigger` | `triggerForStop[pollStopReason] ?? pollStopReason` (`ActorSession.swift` 626) | `collectOutput`, after grace, termination and reap |
| claim `stop_reason.answer` | copy of `poll_stop_reason` ([CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift) 117–121) | resolution |
| claim `cleanup_trigger.answer` | copy of `cleanup_trigger` (127) | resolution |
| `normalized_outcome: runner_timeout` | selected when the stop-reason claim is `sentinel_deadline` (361–366) | classification |
| diagnostics `stop_reason`, `termination_cause` | Rust `project` ([porcelain_admission.rs](../controller/src/porcelain_admission.rs) 1342–1419) | controller projection |

The writers of `pollStopReason` are:
- the initializer default `"sentinel_deadline"` (`ActorSession.swift` 70, then 411);
- the single-worker polling loop (`CWorker.swift` 1191, 1192, 1204, 1205, 1221, 1232, 1235);
- `ActorScheduler.stopActor` ([ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift) 549);
- `finish()` (562).

Every one of them runs before the matching `requestExit`
([ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift)
558–562). Nothing writes the field between that store and `collectOutput`, so
the value mapped at collection is the value held at the store. That equality
follows from how the code is structured; nothing captures the value at the
store.

**Exits that keep the default.**
- The single-worker loop (`CWorker.swift` 1162–1270) has four exits that leave
  `pollStopReason` untouched: 1247, 1253, 1259 and 1269. Each goes through
  `expiredAfterResampling`, `expiredAfterWaiting(exit:)` or
  `expiredAfterSleeping()`, and each returns true only when the allowance is
  exhausted (`fallbackRemainingNs == 0`, lines 955–1027).
- The breaks at 1193, 1206, 1238 and 1267 only leave a `switch`.
- The protocol-violation branch (1188) continues the loop.
- With an unusable clock, `elapsedNs()` returning nil changes only the cadence of
  the periodic waitpid (1227). The loop still ends through an expiry exit, once
  nominal charged sleeps exhaust the allowance.
- So in the single-worker form the string `deadline_expiry` always means the
  allowance was exhausted. It is never actively recorded: it is the default that
  no other exit replaced. Under a clock fault that exhaustion was counted in
  nominal sleeps, not measured; only `sentinel_wait.clock_fault` and the absent
  `elapsed_ms` show this. That is the single-worker counterpart of DT-10.
- The actor form never keeps the default. `stopActor` or `finish()` assigns every
  spawned session.

**History: two separate properties.**

(i) *Recording time.* The derivation was introduced in `0ed4ae7a` (2026-09-27).
At that point it sat immediately after the store. `git show
0ed4ae7a:runner/Sources/PWRunnerCore/CWorker.swift`, lines 933–938:

```swift
    // ---- Request worker exit (a no-op if it already died on its own).
    storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)
    // The cleanup trigger is recorded here, at the store, as the reason polling
    // stopped; it is a host fact for the disposition record, not reconstructed
    // from a final exit code.
    let cleanupTrigger = PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason
```

`c686a05f` (2026-11-03), which introduced `ActorSession` and the actor form,
deleted those lines and moved the same expression into `collectOutput`. So the
value was fixed at the store from `0ed4ae7a` until `c686a05f`, and at final
collection since then. Because no later write intervenes, the move changed when
the value is fixed, not the value.

(ii) *Independence from the stop reason.* The trigger has never been independent
of the stop reason. Both placements derive it through `triggerForStop` from
`pollStopReason`.

What the documents claimed:
- The failure contract's wording dates from `0b6e191e`, about an hour before
  `0ed4ae7a` on the same day. In
  [the contract](../tests/FAILURE-PROPAGATION-CONTRACT.md), lines 359–367, it
  claims three things: the trigger is "recorded at the exit-request store"; the
  raw facts are "not conclusions reconstructed from a final status"; and "today
  it corresponds one-to-one with `poll_stop_reason`, and both are retained".
- The first claim matched the code only between `0ed4ae7a` and `c686a05f`. The
  second has always held. The third openly states that the trigger depends on
  the stop reason.
- RESPONSE's "Host fact recorded when it requests exit"
  ([32-lifecycle.surface.md](../docs/contract/32-lifecycle.surface.md) line 92;
  `docs/RESPONSE.md` 1633) was authored in `f6551bf9` (2026-11-10), after the
  move.
- Two code comments carry the same recording-point wording and were not changed
  by the move:
  - the doc comment on `CWorkerOutput.cleanupTrigger`
    ([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) 559–562,
    "Direct host observations … why exit was requested (recorded at the
    exit-request store)"), from `0ed4ae7a`;
  - the comment on Python `TRIGGER_FOR_STOP`
    ([lifecycle_contract.py](../tests/lib/lifecycle_contract.py) 105–106, "the
    host records the trigger at the exit-request store"), from `0b6e191e`.
- The actor cause surface's fallback paragraph
  ([41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
  1014–1017; RESPONSE 3167) names "the request result, exhausted grace and owned
  final status" as the independent observations in the chain. It does not include
  the trigger.

DT-46's "already in `0ed4ae7a`" is accurate for the expression. The placement at
collection begins with `c686a05f`.

**No reader treats the copies as corroboration.**
- I found no statement or reader that treats any pair of these copies as
  corroborating each other.
- Rust (`porcelain_admission.rs` 463–475) and the Python oracle
  ([lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) 139–145) each check a
  claim only against its own raw field.
- Python `TRIGGER_FOR_STOP` ([lifecycle_contract.py](../tests/lib/lifecycle_contract.py)
  107) is used for a vocabulary self-check (752) and an export (801). The Swift
  test at
  [DispositionResolverTests.swift](../runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift)
  527 compares that export with `PWDisposition.triggerForStop`. That detects
  disagreement between the Swift and Python tables. It checks no reply value.
- The Swift resolver fixture at line 44 builds its expected trigger with the
  production map, so that fixture alone cannot detect a mapping change.
- The cited Rust cause test (lines 2660–2730) builds matched pairs by hand.

**What enters the cause label.** In `project`, `termination_cause` requires four
things:
- a supported `final_status` of `signal`, which comes from waitpid status
  recorded at reap;
- supported `grace_end: exhausted`, recorded when the grace loop ends;
- `kill_request_and_result: requested`, recorded at the kill call, with `rc == 0`
  and a signal equal to the final status;
- a supported trigger, which only selects the label.

`owned_reap` and its `departure_requested` are not inputs. In the ordinary form,
where the map is deterministic, the derivation therefore changes only how the
value's provenance is described. No cause selection changes.

**Executed, public CLI, E4 (shortened-timeout control).**
- Specimen: the ordinary baseline from the failure-contract investigation plus
  `_test_overrides.worker_timeout_ms: 50` and `worker_post_apply_hang_ms: 3000`.
- `worker_timeout_ms` is a supported override. The host floors it at 50 ms
  (`timeoutMsForCWorker`, `CWorkerRequestPlanning.swift` 62–66) and passes it as
  the same `HostWaitClock` budget, so the production loop runs with a smaller
  allowance. This control does not test the 120,000 ms production duration.
- Result: exit 1, `runner_timeout`.

| Field | Value |
| --- | --- |
| `sentinel_wait` | `budget_ms` 50, `elapsed_ms` 53, `excluded_ms` 2, `clock_fault` false, `stop` `sentinel_deadline` |
| `poll_stop_reason` and the stop claim | `sentinel_deadline` |
| `cleanup_trigger` and its claim | `deadline_expiry` |
| `exit_grace_wait` | 1001 ms, `exhausted` |
| `termination_request` | `{signal:9, rc:0}` |
| status | reaped with signal 9 |
| diagnostics | `termination_cause: host_sentinel_deadline`, `stop_reason: sentinel_deadline` |

Only the initializer assigns the string `sentinel_deadline`
(`ActorSession.swift` 70 and 411; line 411 reassigns it when the policy
transfer succeeded). Both assignments precede the polling loop, so the string's
presence shows only that no loop exit replaced it, which means one of the expiry
exits ended the loop. `elapsed_ms ≥ budget_ms` with a working clock shows the
expiry was measured. One stored string reaches seven reply values plus the
outcome.

### DT-121 — In the actor form, scheduler stop reasons pass through the trigger unmapped, so a fully witnessed host kill projects `unknown` under the documented recognized-value rules

- *Source.* Every actor stop reason comes from the scheduler. The full list:
  `done`, `schedule_complete`, the visit failures, setup statuses, transfer
  failures (`policy_write_error`/`policy_transfer_deadline`) and `wait_error`.
  Only `done`, `wait_error` and the two transfer reasons appear in
  `triggerForStop`. All other values pass through as the trigger.
- `sentinel_deadline` cannot occur in the actor form, so the actor cause table's
  "Deadline expiry" row cannot be reached. That row is at
  [41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md) 972
  and `docs/RESPONSE.md` 3162.
- *Executed, public CLI, E5.* One unapplied actor with one `read_fresh` and
  `worker_post_apply_hang_ms: 3000`.
  - The override applies in the actor form. `ActorTranslation` copies it into
    every actor's input (`ActorOrchestration.swift` 186); `ActorSession` passes
    it to the worker on its command line (335–338); the worker sleeps after its
    visits and before `done` (`pw_probe_runner.c` 1675–1688).
  - Result: exit 1, `runner_failed`. The phase completed and `done_observed` is
    false.
  - The full chain is present: `grace_end: exhausted` (1000 ms),
    `termination_request {signal 9, rc 0}`, reaped signal 9, and
    `owned_reap.departure_requested: true` at stage `after_termination`.
  - The trigger and the stop reason are both `schedule_complete`. Diagnostics
    give `process_disposition: signaled`, `termination_cause: unknown` and
    `stop_reason: null`.
- *Why `stop_reason` is null in the same reply.* This comes from a separate
  projection rule with the same root.
  - The actor diagnostics `stop_reason` is defined as "the actor worker's
    supported stop reason from the recognized set listed for execution
    diagnostics. Null when no supported recognized answer was projected"
    ([41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
    803–806).
  - Its first-match rule (932–943) projects the answer only when it is one of the
    six ordinary values.
  - So `schedule_complete` projects null. E1b's `died_before_completion` likewise
    projects null, while E3's `done` projects `done`.
  - The cause table (972–1011) is a different first-match rule over the trigger's
    recognized values, ending in `unknown`.
  - Both rules apply recognized sets drawn from the ordinary-worker vocabulary to
    values the actor scheduler produces.
- *Documented rules and what they leave unstated.* Both outcomes follow
  documented rules.
  - `poll_stop_reason` declares an open vocabulary: "an unfamiliar reason
    establishes only that recorded reason, and gains no known timeout or cause
    meaning" ([32-lifecycle.surface.md](../docs/contract/32-lifecycle.surface.md)
    64–70).
  - The cause rule's last case is "No eligible recognized cleanup cause".
  - `cleanup_trigger` itself has no vocabulary block. Its field statement lists
    six values (line 92) while actor replies carry others as `supported` claims.
    DT-30 recorded that difference.
  - What I did not find is any statement that the actor scheduler's own routine
    reasons fall into the "unfamiliar" class. These include `schedule_complete`
    for every actor not stopped earlier that has not published `done`.
  - Nor did I find a statement that the actor form's deadline row cannot be
    reached. "No stated rationale" is limited to those two points.
- Related to DT-30 (vocabulary lists): this entry records the executed
  consequence for cause and stop projection. Related to DT-10 for timeout labels.
- *Limit.* The run shows only `schedule_complete`. `completion_timeout`,
  `arrival_timeout` and `setup_timeout` with an exhausted grace were not executed.

### DT-122 — Accepted custody has no public carrier when the issue slot is unpublished, while delivery observations survive an unpublished transfer slot

This entry extends DT-62 to the public CLI.

**Observers of the issue.**
1. The worker's native `sandbox_extension_issue_file` return and errno are
   written to its slot ([pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c)
   851–856). The host may read them only after the slot `completed` publication
   (store at 1096).
2. The worker publishes the outbound slot (`committed`, 878).
3. The host decides acceptance while servicing during the issuer's visit. It
   records a `CustodyObservation` with status, length and phase, clears the
   outbound token field, and acknowledges
   ([AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
   456–501).
4. The worker records its own view of that acknowledgement as
   `ext_custody_status` (C 877–883). That value becomes readable only through the
   same slot `completed` publication.
5. The host custody setup scope holds mmap, `final_erase` and munmap only.

**What reaches the reply.**
- `CustodyObservation` is used only for the token status
  (`ActorOrchestration.swift` 466–468), after the check that the slot completed,
  and for `delivered_length` (486), only when the transfer acknowledgement was
  `delivered`.
- Its `status`, `length`, `rejectDetail`, `erased` and `phaseIndex` are never
  encoded on their own.
- The surface's statement that "The native return and host custody acceptance are
  reported independently"
  ([14-extensions.surface.md](../docs/contract/14-extensions.surface.md) 377,
  authored in `f6551bf9`) describes what the host observes. It does not describe
  what the reply reports.

**Executed, public CLI, E1a against E1b.** The issue-only specimen was run without
the seam (E1a) and with `worker_kill_before_publish_slot: 0` (E1b).

| Field | E1a | E1b |
| --- | --- | --- |
| exit, outcome | 0, `finished` | 1, `runner_failed` |
| issue event | `returned`, `native_nonnull` true, `token_length` 208 | `call_boundary_observed` true, `result_published` false, `unresolved`, native fields absent |
| token record | `issued`, length 208 | `unresolved`, no length |
| host custody scope `t` | mmap 16384, `final_erase` performed 16384, munmap 0; `{mapping: released, private_erasure: performed}` | identical |
| worker scope | `{descriptor: released, mapping: held, shared_erasure: performed}`, cell 11 value 0 | `{…, mapping: held, shared_erasure: not_present}`, no cell 11 |
| actor trigger | `completion`; reaped exit 0 during grace | `died_before_completion`; reaped signal 9 at stage `schedule`, `departure_requested` false |

In E1b no public field distinguishes "the host accepted custody" from "no
publication ever reached the host". DT-62's driver output shows that the host did
accept in this configuration. That driver run is internal evidence and was not
repeated here.

**Executed, public CLI, E2: the asymmetry at the public boundary.**
- Specimen: one actor that issues and then transfers to itself, with
  `worker_kill_before_publish_slot: 1`. The seam kills the worker after the
  transfer attempt returns and before its slot is published.
- Result: exit 1, `runner_failed`.
- The issue event is `returned` with length 208, and the token is `issued`.
- The transfer event is `unresolved` and `result_published` is false.
- `transfers[0]` reads `held`, `copied`, `equal`, recipient acknowledged,
  `source_acknowledged: false`, `delivered`.
- The delivery is `delivered` with `delivered_length` 208.
- So the host's delivery observations survive an unpublished source slot, while
  the host's acceptance does not survive an unpublished issue slot.
- `ActorReplyTests` 135–156 asserts the transfer side only in-process, through
  `assembleActorReply`. This run is the public-CLI observation.
- `delivered_length` is the host's custody length. The host read it from the
  worker-written outbound length word and checked it against the framing.
  `token_length` comes from the worker's evidence slot. Both lengths were written
  by the same worker through two channels. Their equality is a consistency check,
  not two independent measurements.

**Statement ambiguity.**
- "The host custody record carries token acceptance" appears at
  [14-extensions.surface.md](../docs/contract/14-extensions.surface.md) line 623
  (the `pins` of the issue-projection source support) and is rendered at
  `docs/RESPONSE.md` 2680.
- Read as `authority_setup.host.custody`, it is false: that scope never contains
  acceptance, and E1a and E1b give identical scopes.
- Read as `resources.tokens[].status`, which the failure contract calls "Custody
  status" (lines 272–281), it holds only when the issue slot was published.
- Line 429 ("Host custody records describe the controlled publication, copying
  and erasure protocol") does not settle which record is meant.

### DT-123 — The worker's own observation of the custody answer is decoded and discarded

- `ext_custody_status` reports what the worker saw:
  `none/accepted/rejected/timeout/not_published/clock_fault`
  ([pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
  164–167).
- `collectOutput` decodes it into `CWorkerExtensionPublication.custodyStatus`
  (`ActorSession.swift` 690). In the E6 driver output (DT-124) this decoded value
  is labelled `worker_custody_status`; it is the same field. This record calls it
  `ext_custody_status` throughout.
- I first searched `runner/Sources`, `controller/src`, `controller/tools` and
  `tests/lib`. That covers assembly, the `PWRunnerReply` integrity checks, the
  classifiers and the readers. The search found no other reference to the
  decoded field; the other `custodyStatus` hits are the host's
  `TransferObservation` string.
- A later search of `tests/suites` and `tests/fixtures` found the raw C slot word
  in three test places, none of which reads the decoded Swift field:
  - [authority_binding.c](../tests/fixtures/extension_controls/authority_binding.c)
    99 and 104, a constructed C control that drives `attempt_extension_issue` to
    `PW_CUSTODY_TIMEOUT` and then `PW_CUSTODY_ACCEPTED`;
  - the `early_erase` mutation anchor in
    [actor_handoff_mutations.py](../tests/suites/runner_unit/actor_handoff_mutations.py)
    140–141;
  - the layout printer.
- The `custodyNames` table at `ActorOrchestration.swift` 295 has no reader.
- `git log -G'custodyStatus|custodyNames' -- runner/Sources` shows the decode and
  the table were added in `c686a05f` and that no reader was ever added.
  `deb67eff` touched only the transfer field. `bc3abe2f`'s `custodyNames` is a
  different local in `PWRunnerAuthoritySetup.swift`.
- Only [ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
  305, 394 and 400 read it, in-process. E6 (DT-124) recorded value 1 (`accepted`)
  for the issue slot.
- Consequence: the token status is built from the host's acceptance record
  combined with the worker's slot publication. The worker's view of whether it
  received an answer, which is what a timeout or clock fault would change, is
  retained only internally.
- I did not execute an end-to-end timeout case. The C control above produces a
  worker-side timeout status, but no test follows that word through the Swift
  decode, assembly or reply. This entry concerns which fields exist; it is not a
  demonstrated disagreement.

### DT-124 — No public field reports last-use clearing; the internal final erased flag is the same whether or not the last declared transfer ran

This entry extends DT-63.

**Clearing sites.**

| Site | Extent | When | Where it is visible |
| --- | --- | --- | --- |
| Host outbound clear | the outbound slot's token field | at acceptance (`AuthorityCustody.swift` 490) | internal |
| Host private custody, issue-only last use | the custody buffer | at acceptance (482–485) | internal flag |
| Host private custody, last transfer | the custody buffer | `defer` in `serviceTransfer` (514–521) | internal flag |
| Host private custody, teardown | the custody buffer | `finish()` (633–639; `TokenCustody.finish` 311–322) | `final_erase` cell, `private_erasure: performed` |
| Host shared region, teardown | every slot's token field | `finish()` after reap, for quiescent owners (225–242) | region `shared_clear` with byte count |
| Worker inbound, last consume | that inbound slot's token field | C 936–939 | not published |
| Worker exit sweep | settled inbound slots | `erase_authority` (C 579–590), first call published once as cell 11 | worker `terminal_owned_inbound_clear` value, `shared_erasure: performed` |

The authored erase rule lists `report: runner_reply`
([14-extensions.surface.md](../docs/contract/14-extensions.surface.md) 408–421).
The reply contains only the teardown and exit rows. Neither last-use clearing
appears in any public field.

**Executed internal driver, E6 (not a public response).**
- Request:
  - A (unapplied, unentitled) issues `t` and transfers it to B as `d1`.
  - B (unapplied, selected) runs `read_fresh`.
  - A transfers `t` to B as `d2`, its last declared use.
  - B consumes `d1` (last use) and releases `h1`.
  - B runs `read_fresh`.
- Native issue, consume and release are real calls in the signed workers.
  Transfers are real host servicing.
- Each collection-hook row below is taken after the scheduler observed the
  active actor's arrival and before its release store (`ActorScheduler.swift`
  405–415). The scheduler activates one actor at a time. That rests on its design
  and source comment (4–17, 406–407), not on a traced path for each actor.
- The other actor's state differs by row:
  - Before a later visit it is parked in `wait_for_activation`
    (`pw_probe_runner.c` 1148), which services inbound slots.
  - After its final visit it runs its exit path or has exited (1673–1702). That
    applies to A at V1's phase-3 and phase-4 rows.
  - In V2, A is reaped from phase 1 on.
- A's exit path erases only A's own settled inbound slots (none) and touches
  neither host custody nor B's region (`erase_authority`, C 579–590). The
  measured quantities therefore do not depend on A's state.
- Each interval runs from one hook row to the next.
- V1 runs unchanged.
- V2 sets `killBeforePublishSlot = 1` on A's input only, in the driver. This is
  the same `CWorkerInput` field, and the same worker argument
  `--kill-before-publish-slot`, that the CLI override becomes. The CLI override,
  however, applies to every actor; the driver confines it to A. A dies after
  `send_d1` returns, so the last declared transfer is never serviced.

| Collection point | V1: custody flag / buffer nonzero bytes | V2: custody flag / buffer nonzero bytes | B inbound `d1`, `d2` nonzero (V1) |
| --- | --- | --- | --- |
| phase 0, A arrives | no observation / 0 | no observation / 0 | 0, 0 |
| phase 1, B arrives after `send_d1` | accepted, not erased / 208 | accepted, not erased / 208 | 208, 0 |
| phase 2, A arrives | accepted, not erased / 208 | A unavailable; no hook | 208, 0 |
| phase 3, B arrives after `send_d2` | **erased / 0** | accepted, not erased / 208 | 208, 208 |
| phase 4, B arrives after `consume_d1` | erased / 0 | accepted, not erased / 208 | **0**, 208 |
| after `run()` (teardown done) | `erased: true`, buffer unmapped | `erased: true`, buffer unmapped | regions unmapped |

What this establishes:
- In V1, with a real worker and real native token, the private custody buffer was
  cleared inside the interval from A's phase-2 arrival to B's phase-3 arrival.
  That is before teardown and consistent with the `serviceTransfer` defer.
- In V2 it was still uncleared (208 nonzero bytes, flag not set) at the last
  hook, B's phase-4 arrival. It was cleared and unmapped by the time `run()`
  returned. That interval also contains B's last visit, B's exit and `finish()`.
  Source attributes the clearing to `finish()` → `custody.finish()`, but the
  capture does not isolate it.
- The final internal `erased` flag is identical in both variants. The driver
  produces no public reply; in the public CLI runs (E1a, E1b, E3) the custody
  scope likewise shows only `final_erase` performed, the same in each.
- In V1, B's `d1` inbound slot was zero at phase 4 while `d2` stayed nonzero.
  This places the worker's last-consume erase before its exit sweep.
- V2 also shows the worker's own published `ext_custody_status` (1, accepted)
  and A's unpublished `send_d1` slot beside a delivered host transfer.
- B exited 0 in both variants, and both PIDs were absent to `kill(pid,0)` after
  the run.
- B's `consume_d1` returned native 0 in both variants. B is unapplied here and
  uses the selected worker. In E3, where B is applied, both consumes returned 1;
  DT-59 recorded 0 for an unapplied, unentitled self-consumer. Both 0 and 1 are
  candidate handles; only −1 means failure. The last-use erase runs whatever the
  result (C 933–940), so the erasure observation does not depend on the value.
  No claim about native handle numbering is made.
- Limits: equipment binding, live inspection, validator collection and reply
  encoding do not run in the driver. Each interval is bounded by collection
  points, not exact instants.

**Tests that read only the final state, and the observers.**
- [ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
  467–468 credits clearing at the last declared transfer but reads the
  post-teardown flag. Line 307, in the calibration case, also reads that flag
  after teardown, without a timing comment.
- E6 V2 shows, with real workers, the relationship DT-63 showed with a
  constructed input. When the last-transfer site never ran (the declared transfer
  was never serviced), the final flag is the same as when it ran. The flag
  therefore cannot tell the two sites apart.
- V2 is not a case in which the line-468 assertion would fail for the input that
  test runs (its self-transfer does execute). The point concerns what the
  assertion's comment credits, not its verdict.
- The footprint snapshot ([actor_snapshot.swift](../tests/fixtures/footprint/actor_snapshot.swift)
  46–50, asserted in [footprint_workloads.py](../tests/lib/footprint_workloads.py)
  118) reads `TokenCustody.erased` as false *before* the last transfer. It reads
  flags only, not memory.
- No existing observer covers the interval between the last transfer and
  teardown on the host side.

### DT-125 — The boundary observer of worker inbound clearing keeps only a cumulative result; a synthetic fixture counts erase calls

This is the worker-side counterpart of DT-124, with a qualification.
- [control.c](../tests/fixtures/extension_controls/control.c) 117–130 rewrites
  one word, `worker_token_erased = clear && !failures`, on every erase call over
  the observed inbound slot. Each call scans the full 16,384-byte field. It keeps
  only a cumulative failure count, with no call site, count or interval.
- [check_extension_boundaries.py](../tests/suites/witness_contract/check_extension_boundaries.py)
  336–338 reads only those words.
- The worker erases that slot at the last consume and again in the exit sweep. So
  that observer would also pass if only the exit sweep ran.
- However, [terminal_control.c](../tests/fixtures/extension_controls/terminal_control.c)
  100–105 counts every erase call and checks the full buffer after each.
  [check_terminal_erasure.py](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py)
  91 requires `erase_calls >= 3` for `consume`. In that fixture the three calls
  are the last consume, the sweep after the visits, and `publish_done_and_exit`
  (one settled slot of two). Without the last-use erase the count would be 2.
- That guard is synthetic and count-based, not a timing observation. No mutation
  was executed here.
- E6 (DT-124, V1) supplies the timing observation internally. The host side has
  no equivalent guard.

### DT-126 — Two handle records and their release events are identical while access after each release differs

This entry extends DT-66 with a rebuilt run.

**Executed, public CLI, E3 (rebuild of DT-66).**
- Result: exit 0, `finished`.
- Both consumes returned native 1, and each handle lists the other in
  `raw_equal_handles`. Both releases returned 0 with errno 0.
- Fresh reads:
  - `baseline`: open −1, errno 1;
  - `during`: open 5, read 27;
  - `after_r1`: read 27;
  - `after_r2`: −1, errno 1.
- Both successful reads returned the target bytes with device 16777233 and
  inode 278532339.
- All four queries were `deny` with `query_first`. The queries were collected at
  B's arrival, before any of the phase's consumes or releases.
- The gate was satisfied, with capture ordinals: A activation 1 < A owned reap 2
  (natural, `termination_gate`) < gate 3. B's `b_use` activation timestamp is 3 µs
  after A's reap timestamp.
- Both PIDs (43783, 43784) were absent afterward.
- This reproduces DT-66's pattern on the rebuilt specimen.

**What each handle field records.**

| Field | Producer | Observation time |
| --- | --- | --- |
| `status: produced` | consume slot publication | the consume |
| `native_handle` | consume slot publication | the consume |
| `raw_equal_handles` | assembly comparison of two consume slots' numbers | reply assembly |
| `release_attempted` | the release slot's `call_boundary` marker | stored before `extension_release` (C 948–950); read at final collection even when the slot never completed (`ActorSession.swift` 652) |

- 14-extensions line 948 defines `release_attempted` as "an observed native
  call-boundary marker". So "attempted" means the worker reached the pre-call
  store. It is not evidence of entry into, return from, or the effect of the
  native call.
- The worker never clears `handle_valid` after a release (C 943–957).
- No handle field changes on release, on access loss, or on process exit.
- Apart from references, step IDs and each listing the other in
  `raw_equal_handles`, the two handle records are identical (`produced`, native
  handle 1, `release_attempted: true`), and so are their release events
  (`returned`, 0, errno 0). Yet access after `release_h1` succeeded and access
  after `release_h2` failed.
- Only the `read_fresh` observations, each a separate worker publication, carry
  the access boundary. The handle records describe production and release-call
  reachability, not present usability. After the reap, the process that held
  these numbers no longer exists.

### DT-127 — Worker ownership values are pre-exit publications reported beside host values recorded at teardown

This entry extends DT-68.

**Established observation time of each value.**
- The worker scope is decoded from the worker's evidence region during
  `collectOutput`, after reap (`ActorSession.swift` 489, 768).
  - `descriptor` comes from cell 9 (setup).
  - `mapping: held` comes from cell 8 `mmap` succeeded (setup).
  - Only cell 12, `rejected_mapping_munmap`, could change `mapping` (setup
    failure path).
  - `shared_erasure: performed` comes from cell 11, published at the first exit
    sweep before `done` or before an exit-request `_exit`
    ([AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift)
    104–108; C 600–606, 820, 1673).
- Host region and custody scopes are read after `custody.finish()`, which follows
  every actor's stop and reap (`ActorScheduler.swift` 557–583, 184–193). Their
  `released` values are host calls observed before assembly.

**Executed observations.**
- In E1a, E1b and E3 every worker scope reads `mapping: held` while the same
  reply reports that actor reaped and the host region `mapping: released`.
- This holds for a clean exit (E1a, E3), for a SIGKILL before publication (E1b,
  where `shared_erasure` is `not_present`), and for a natural reap at the gate
  (E3 A).
- E5, with no authority plan, shows `not_required` and `not_acquired`.
- [WORKER.md](../docs/WORKER.md) row a2 ("Mapping through worker exit") and
  line 65 state the rationale: the worker keeps its mapping until exit and never
  publishes a normal unmap. Exit itself is observed as the host's reap.

**Judgment, kept apart from the established timing above.**
- One field, `ownership`, documented as "Named ownership states" with no time
  anchor ([34-equipment.surface.md](../docs/contract/34-equipment.surface.md)
  line 870), carries two kinds of value:
  - host values that record the outcome of the host's own last call on the
    resource;
  - worker values that describe the last state the worker published before it
    exited.
- For host values, "last call" means the munmap, close, unlink, `shared_clear`
  or `final_erase` in `ActorAuthorityRegion.tearDown` or `TokenCustody.finish`.
  `ActorScheduler.finish()` runs these before it builds the outcome, so they
  happen before assembly.
- PW makes no later call on these resources. The deinitializers that call
  `tearDown`/`finish` again return at once (`tornDown`/`finished` guards,
  `AuthorityCustody.swift` 226, 312, 634).
- A host `released` value therefore stays accurate after the reply as far as PW
  is concerned.
- An `unresolved` value records a failed call. The resource then remains held
  by the host process with no further PW action; what happens to it when that
  process ends is outside these records.
- `withheld_not_quiescent` records that the host did not erase. It says nothing
  about the region object's later state.
- WORKER.md explains the worker value, but the ownership definition does not
  point to that explanation. A reader of the final JSON must join
  `mapping: held` with `reaped`, the gate, or `collection_basis` to place it in
  time.
- The cost is interpretive: no reader or classifier uses worker `held`.
  - Python [actor_evidence.py](../tests/lib/actor_evidence.py) 100–114 and Rust
    `porcelain_actor.rs` 312–345 check that `released` is backed by a successful
    cleanup operation and that `performed` is backed by a performed erasure cell
    (`shared_clear`, `final_erase` or `terminal_owned_inbound_clear`).
  - The `performed` check does not constrain the cell's value, which is why a
    value of 0 passes (DT-128).
  - I found no decision that depends on worker `held`.
- This is not a leak claim. Process absence does not establish the disposition
  of other resources.

### DT-128 — Worker `shared_erasure: performed` does not show that bytes existed or were cleared then, and the same key covers different extents

- Cell 11's public `value` counts bytes overwritten in settled inbound slots.
- In E1a and in E3's A, which have no inbound slot, it is 0 with
  `performed`.
- In E3's B it is 16,384. B's only inbound slot had been cleared by its last
  consume, according to source (C 936–939); E6 V1 (DT-124) observed exactly that
  ordering in the driver (zero after the last consume, before the exit sweep).
  The sweep value counts bytes overwritten, including bytes that were already
  zero.
- The host region's `shared_clear` under the same `shared_erasure` key covers
  every slot: 16,384 for E1a's single outbound slot and 32,768 in E2.
- `final_erase: performed` is likewise recorded whenever the custody buffer
  exists, whether or not it ever held accepted bytes (`TokenCustody.finish`
  311–322).
- No statement gives `performed` a meaning that a value of 0 contradicts. RESPONSE
  lists the states without an extent.

### DT-129 — Smaller observations on a gate-reaped actor's trigger, stop-reason copies, transfer phases and test scope

- *A combination that needs joining (E3, public CLI).*
  - Actor A was reaped naturally at the termination gate:
    `owned_reap.stage: termination_gate`, `departure_requested: false`, capture
    ordinal 2.
  - `finish()` then still assigned `done`, because it checks only
    `doneObserved` (`ActorScheduler.swift` 562). A's record therefore shows
    `exit_requested: true`, `cleanup_trigger: completion` and `grace_end:
    not_entered`.
  - Each value is accurate as recorded. "Exit was requested because of
    completion" does not mean the request caused the departure;
    `departure_requested: false` and the grace state establish that the reap came
    first.
  - The ordinary form has no `owned_reap`. There, `child_reaped` or `not_entered`
    carry that ordering.
- *Stop-reason copies taken before the store.* Copies taken before
  `requestExit` exist in both forms, but only the single-worker copy is
  published.
  - Single-worker form: `sentinel_wait.stop` (`CWorker.swift` 1271) is published.
  - Actor form: `stopActor` keeps an internal copy in
    `ActorSessionRecord.stopReason` (`ActorScheduler.swift` 548) before it sets
    `pollStopReason` and calls `requestExit`. `finish()` does not set this copy
    for actors it stops (562).
  - No production code reads it. `ActorSchedulerTests.swift` 572 and 607 do. It
    never reaches the reply. (The E6 driver printed it as `stop_reason`.)
- *Transfer phase.* For a transfer, the published `phase_id` is the declared
  delivery phase (`ActorOrchestration.swift` 453). The host's servicing phase
  (`TransferObservation.phaseIndex`) is internal.
  - By source the two match: `service` is called only during the source actor's
    active visit, with that visit's phase (`ActorScheduler.swift` 444).
  - No run here printed the internal value.
- *Test scope.* `ActorReplyTests` 112–133 asserts the interrupted issue's
  `unresolved` token and event, and does not assert host acceptance (as DT-62
  notes).
  - That test does run the production equipment binding and live inspection
    through `checkedActorSchedule` (27–35). It also runs Swift reply validation
    and encoding (`admittedReplyData`, `ReplyFailureTests.swift` 110–113).
  - It skips the XPC service entry, `runActors` orchestration and validator
    collection. It sets the kill seam on actor 0 only.
  - E1b (DT-122) is the public-CLI counterpart.

### Observation-time cross-anchor account

**Timeline of one executed reply (E3).** Each step names the observer.

1. The host creates and maps the authority regions and custody before launch
   (region and custody setup cells, host time).
2. The worker publishes setup cells 8 and 9: mapping held, descriptor released.
   They are read at final collection.
3. B: activation (capture ordinal 1), validator query at arrival, release, then
   `baseline` read published.
4. A: activation, issue native return (slot), outbound commit. The host accepts
   (internal record) and clears the outbound slot. The transfer is serviced and
   delivered (host observation, later public). A's last-use defer clears
   custody (internal; not public). A's slot is published. A's exit sweep (cell 11,
   value 0) and `done`.
5. Gate: A's natural reap is observed (capture ordinal 2, `departure_requested`
   false). The gate closes (ordinal 3).
6. B: `b_use` activation and query collection, which provides the `query_first`
   outcomes for all four reads. Then two consumes, `during`, release h1,
   `after_r1`, release h2, `after_r2`. According to source, the last consume
   (`consume_h2`) clears B's inbound slot; this is not published and was not
   observed in E3. Slot publications follow each action.
7. B's exit sweep (cell 11, value 16,384) and `done`.
8. `finish()`:
   - A is already reaped, yet it gets the `done` stop reason, an exit-request
     store and `grace_end: not_entered`.
   - B gets an exit request and is reaped during grace (ordinal 3,
     `departure_requested` true).
   - `collectOutput` maps each trigger and decodes the worker scopes.
   - `custody.finish()` erases custody (`final_erase`), sets the internal
     `erased` flags, erases and unmaps the shared regions.
9. Assembly computes token `issued` from the slot plus the host record,
   `delivered_length` from the host record, and handle `produced` and
   `raw_equal_handles`.

The temporal claims that survive into the reply as explicit ordering are:
- capture ordinals with `observed_ns` (activations, owned reaps, gates);
- visit intervals and wait records with `elapsed_ms`;
- `collection_basis`;
- `owned_reap.departure_requested`.

These carry no recorded time in the reply and keep only a final value: custody
acceptance (and only through token status), the cleanup trigger, handle
production and release, and the worker mapping. Last-use clearing on either side
is not reported at all.

**Answers to the three questions.**

1. *Observers and derived values.*
   - The worker observes native returns, call markers, fresh-read effects, setup
     cells and its own custody and transfer answers.
   - The host observes waitpid, kill, grace end, custody acceptance, transfer
     servicing, region and custody setup and cleanup, gate ordinals and query
     collection.
   - Derived from one stored value: `cleanup_trigger`, the stop-reason claim,
     `sentinel_wait.stop`, `runner_timeout` and the diagnostics stop and cause
     (from `pollStopReason`, DT-120); token status (slot plus host record);
     `raw_equal_handles` (two slots).
2. *What survives, and what is withheld, overwritten, merged or internal.*
   - Withheld: host acceptance when the issue slot is unpublished (DT-62,
     DT-122).
   - Also withheld: the worker's unpublished slot payload (native result, errno,
     length, custody word). This follows the stated publication rule:
     - `collectOutput` reads slot payloads only after the slot's `completed`
       acquire (`ActorSession.swift` 645–655: "Read only confirmed slots");
     - the `result_published` definition: "A false value withholds native
       result fields even if a call boundary was observed"
       ([14-extensions.surface.md](../docs/contract/14-extensions.surface.md)
       line 544);
     - the failure contract's `unresolved` row (no native return, errno or
       unavailability decision is inferred, line 315) and its rule that "A call
       whose return was not published remains unresolved even when an
       independent test intervention knows that it returned"
       ([FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
       lines 317–319).
   - Overwritten: the internal `erased` flag, by teardown (DT-124).
   - Merged: last-use and teardown clearing, into teardown cells; host and worker
     scopes under one `ownership` vocabulary (DT-127); trigger and stop reason
     (DT-120).
   - Internal only: `CustodyObservation` status, length, reject detail and phase;
     worker `ext_custody_status` (DT-123); `TransferObservation.recipientRejectDetail`
     and service phase; `TokenCustody` state.
3. *Combinations that invite unsupported inference.*
   - `exit_requested: true` with `cleanup_trigger: completion` for an actor reaped
     earlier (E3 A, DT-129), read as a departure caused by the request.
   - `issued` with `last_use_step_id` and `final_erase: performed`, read as
     clearing at last use (DT-63, DT-124, DT-128).
   - `produced`, `release_attempted: true` and release `0`, read as revocation
     (DT-126).
   - Worker `mapping: held` with reaped, read as a present mapping (DT-68,
     DT-127).
   - `shared_erasure: performed`, read as "token bytes cleared at exit" (DT-128).
   - Equal `token_length` and `delivered_length`, read as two independent
     measurements (DT-122).
   - A full kill chain with `unknown`, read as missing evidence rather than an
     unmapped trigger (DT-121).

**How the findings bear on each other.**
- *Tension between DT-62/DT-122 and DT-46/DT-120.* The record withholds an
  independently observed host fact (acceptance) because a different publication
  is missing, while it presents a derived value (trigger) as a fact recorded at
  the store. The two are not symmetric:
  - The trigger's documents acknowledge its one-to-one dependence on the stop
    reason, and the cause fallback text does not count it among the independent
    observations. The inaccuracy is the recording time, which has existed since
    `c686a05f`.
  - The acceptance case loses a host observation the statements say is "reported
    independently".
- *Shared mechanism between DT-63/DT-124 and DT-128.* Teardown and exit records
  stand in for every clearing. The final flag (internal), the custody cell and the
  worker's cell 11 all describe the last clearing, not the declared one. E6 V1/V2
  show that the same final values arise either way.
- *Different boundary between DT-66/DT-126 and DT-68/DT-127.* Both concern
  historical values after reap. Handles are explicitly scoped by their
  definitions ("candidate handle", "relates raw numbers"). Worker `held` is not.
- *Historical labels.* They do not uniformly suggest the present tense:
  - Host scope values record the host's last call on each resource, made before
    assembly, with no later PW action (DT-127).
  - The resource tables are explicitly "observed production"
    ([14-extensions.surface.md](../docs/contract/14-extensions.surface.md)
    line 776).
  - The present-tense risk is concentrated where no time anchor is stated: worker
    `ownership`, `performed`, and the cleanup-trigger recording wording.

### Observation-time coverage and remaining limits

- Executed:
  - six public CLI specimens (E1a, E1b, E2, E3, E4, E5);
  - two path-length checks (E7a, E7b);
  - one internal driver with two variants (E6).
- Not executed:
  - the actor-form `completion_timeout`/`arrival_timeout`/`setup_timeout`
    variants of DT-121;
  - an end-to-end worker custody timeout or clock fault, for DT-123 (a
    constructed C control exists; see DT-123);
  - a clock-fault deadline;
  - mutation of either last-use erase;
  - any registered suite.
- I did not rerun DT-62's internal acceptance print. The pass did not
  characterize native release reference counting, revocation, or the cause of
  errno 1.
- E4 is a shortened-timeout control, not evidence about the production duration.
- History findings rest on `git log -S/-G` and `git show` of the named commits.
  No older binaries were executed.
- This pass changed no tracked source, test or document. Its drafts, validation
  memos and responses are kept under `records/contract-trio/observation-time/`.

## Additional findings: what acceptance establishes

This pass follows DT-48, DT-50, DT-53, DT-61 and DT-95 from their raw or
constructed input to the outer `run` result. For each accepting boundary it
records the proposition checked, the representation of the evidence it reads,
and the consequence of a failure. The five findings concern different
boundaries. The entries below explain how they relate and add six findings,
DT-130 to DT-135. Earlier findings keep their scope; where this pass
re-executes one, it says so. No implementation, test, contract or
document was changed, and nothing here proposes a repair, an authoritative
layer or a consolidation of findings.

### Acceptance investigation identity and reproduction conventions

**Snapshot.** Source inspection used clean HEAD
`cc55288d033023ce2f18e8c02cd51a400ef2b530` on 2026-11-16. Line numbers below
refer to that snapshot. The machine reports macOS 26.7.1, build 25G241, arm64.
`dist/PolicyWitness.app` reports commit `8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`,
version 0.3.7, build 1482, contract
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
`git diff --stat 8b5de2b2 HEAD -- controller runner tests docs` shows only a
one-line change to `tests/suites/preflight/opt_in/build_refusals.py`. The five
app executables hashed identically before and after this pass's runs
(`policy-witness` `4bcd308b…8d28`, `PWRunner` `706d9a6c…8501`, `pw-probe-runner`
`d6d38f09…2116`, `pw-probe-runner-unentitled` `ee2a4248…312c`,
`sb_api_validator` `ccbf9803…0890`). Nothing was rebuilt or re-signed. Python ran
through `tests/lib/python.sh` (Python 3.14.9) with assertions enabled.

**Evidence categories.** Each result below names one of these:

- *Live*: `policy-witness run REQUEST` against the dist app, capturing stdout,
  stderr, exit status and the exact host reply bytes retained by the admitted
  client capture. Controlled-validator runs set
  `_test_overrides.validator_executable_path` to a copy of one Python script
  whose transcript mode is selected by file name. It reads each JSON query
  line and prints one verdict record (two in `dup` mode). It makes no
  `sandbox_check` call. These runs exercise the real host, worker, client and
  controller with a steered validator transcript; they are not native
  predictions.
- *Seam*: the existing ignored Rust test
  `run_flow::tests::reader_definition_corpus_cross_readers`
  ([run_flow.rs](../controller/src/run_flow.rs) lines 1250–1510) and the
  Python replay it launches
  ([reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py)), both
  unmodified. Details and limits are below.
- *Unit*: one existing Rust test run from the same binary (DT-95).
- *Source*: reading at the snapshot, with no execution.
- *Listing*: `tests/run.sh --all --list`, which listed 283 cases (232
  default) without a lock refusal. No registered case was executed, and no
  case pass is claimed.

**Environment.** The first live run (`base`) was made inside the automation
sandbox and returned `finished`, exit 0. Earlier passes saw lookup error 159
there; this run did not. All live runs and the seam execution therefore ran
inside the automation sandbox. No conclusion is drawn about the earlier
refusals.

**Live runs.** All used the request skeleton of the failure-contract
investigation: SBPL `(version 1)(allow default)`, one step per query, a
`file-read-data` path query, and a `file`/`open_read` attempt on the same path.
`é` below is U+00E9 (NFC). Its NFD form is `e` followed by U+0301.

| Run | Variation | Exit, outcome | Host frame SHA-256 (prefix), bytes |
| --- | --- | --- | --- |
| `base` | shipped validator, step `s`, `/etc/hosts` | 0, `finished` | `a5700b04ed25`, 3551 |
| `base_fixture` | controlled coherent record `allow`/0/0 | 0, `finished` | `ea1d250747d6`, 3636 |
| `incoherent` | controlled record `allow`, `rc` −1, `errno` 13 | 0, `finished` | `9001b5744b17`, 3642 |
| `nfc_id` | step `s-é`; record ID byte-identical | 0, `finished` | `2de88839aa36`, 3648 |
| `nfd_id` | step `s-é`; record ID in NFD | 0, `finished` | `3ca88d804093`, 3650 |
| `nfc_value` | path `…/files/café.txt`; record value byte-identical | 0, `finished` | `3cbb136d21b1`, 4484 |
| `nfd_value` | same path; record `filter_value` in NFD | 0, `finished` | `404e10fc643d`, 4489 |
| `dup_id` | step `s-é`; two records, NFC and NFD IDs | 1, `validator_unavailable` | `ba4277a91350`, 4174 |
| `both_ids` | two steps, `s-é` NFC and NFD | 1, `bad_request` | `551a7d270b9c`, 528 |
| `capture` | `capture_compiled_profile`, nonce `ad881d6a…9ae8` | 0, `finished` | `2b6efe373bbb`, 4340 |
| `actor` | issuer (unapplied, unentitled) issues and transfers a read extension; subject (applied) reads, consumes, reads | 0, `finished` | `7b729668604c`, 23352 |

**Seam method.** The Rust test reads `reader-corpus/swift.json` under
`$PW_POLICY_TRANSFER_REPLIES`. For each listed frame it:

- decodes the frame with `porcelain::decode`;
- runs `admit_reply`;
- assembles the run envelope with `complete_execution(driver_execution(typed, &raw))`;
- checks that the outer result follows the host label;
- writes `rust.json`;
- runs the Python replay. The replay records, per row:
  - independent `porcelain.decode_bound` equality;
  - `consumer.validate_fixture` on the bare reply and on the Rust-assembled envelope (binary bytes, so the JSON-fixture path is not taken);
  - `actor_evidence`, `extension_evidence` and `lifecycle_oracle.check_record`.

  It writes `python.json`.

The test binary was built from the unmodified crate:
`CARGO_TARGET_DIR=.tmp/contract-trio/acceptance/cargo-target cargo test
--manifest-path controller/Cargo.toml --locked --offline --no-run`, with cargo
and rustc 1.99.0. The resulting binary `policy_witness-bb8137965490ffba` has
SHA-256 `b64ac21a…7fe97`. `controller/build.rs` writes only under `OUT_DIR`,
and `git status` stayed clean.

Seam limits that apply to every seam result below:

- **Constructed contract binding.** Under `cfg(test)` the controller's
  `BUILD_CONTRACT` is the constant `test:policy-witness`
  ([json_contract.rs](../controller/src/json_contract.rs) lines 21–22). The
  Python replay admits frames only under that identity. Every seam row,
  including each baseline, is therefore a live frame with one constructed edit:
  `producer.contract` changed to `test:policy-witness`. The builder decoded each
  live frame and its rebound copy and required the difference to be exactly
  that field. Each further edit was likewise verified to differ from its
  rebound base only in the intended field (`corpus/edits.json`).
- **No `reply_contract`.** The seam calls `complete_execution` directly. A
  receipt-label failure therefore appears there as a `reply_admission`
  integrity finding, whereas the production run path refuses the reply first.
- **Placeholders.** The test panics unless rows named `ordinary`,
  `actor-complete` and `preparation-0` exist. It also unconditionally reads
  `../porcelain-replies/writer-cap-{minimal.pwp,receipt.json}`, and the replay
  reads `../porcelain-replies/normal.pwp`. `ordinary` and `actor-complete` are
  the rebound `base` and `actor` frames. `preparation-0` is a second copy of
  the rebound `actor` frame. The writer-cap pair and `normal.pwp` are
  constructed (`seam_placeholders.py`; `normal.pwp` copies `ordinary`). All of
  these exist only so the seam can run. Their rows, and the seam's JSON-only
  rows derived from them, are disregarded.
- **Fidelity control.** For every unedited rebound row with a live envelope
  (twelve rows: eleven distinct live frames, plus `preparation-0`), the
  seam's `runner_result` (with `producer.contract` normalized),
  `runner_sandbox_diagnostics`, and
  `result.normalized_outcome`, `ok`, `exit_code` and `error` were identical to
  the live CLI envelope's. No field disagreed. `porcelain.decode_bound` and the
  Rust JSON agreed on all 25 rows.
- **Expectation failures.** The test exited 101 by design, because I gave
  every row `expected_semantic: true`. Its own failure list names exactly the
  rows where Rust found issues (`f48-claimed-order`, `nfd-id`, `nfd-value`,
  `dup-id`, `f95-producer-host`), plus placeholder mismatches. The replay's list
  names the consumer findings tabulated below, plus placeholder and corpus
  inventory mismatches. The test's check that "semantic findings changed outer
  result/exit" (line 1352) raised nothing: for every row, result and exit
  followed the host label.

The Swift reporting validator and the Swift setup decoder were not run on any
edited frame. Every Swift judgment about an edited frame below is source
reading.

**Availability.** Scripts, requests, envelopes, frames, the corpus,
`rust.json`, `python.json`, `analysis.json`, the catalog listing and the reader
map are under `.tmp/contract-trio/acceptance/` in this checkout. That directory
is gitignored scratch with no retention guarantee. SHA-256 of the main
artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `scripts/live_probe.py` | `388bd987…89ee` |
| `scripts/validator_fixture.py` | `7e5b1a97…6489` |
| `scripts/frame_edit.py` | `6b2bba47…9f69` |
| `scripts/build_corpus.py` | `bb952dc2…6739` |
| `scripts/seam_placeholders.py` | `548e9afd…6f49` |
| `scripts/analyze_seam.py` | `c442d6d6…f916` |
| `scripts/reader_case_map.py` | `e8517f42…22fb` |
| `corpus/reader-corpus/rust.json` | `ed61060c…0226` |
| `corpus/reader-corpus/python.json` | `83557186…b57d` |
| `corpus/edits.json` | `2f0f2e3f…44eb` |
| `reader-case-map.jsonl` | `0da5ed35…acbb` |

The frame editor re-encoded three unrelated old frames byte-identically before
use; those frames were a tool check only. The decisive values are reproduced
here.

### Acceptance boundary map: what each accepting boundary checks, and over which representation

Rows are in pipeline order. "Result" means `result.normalized_outcome`,
`result.ok` and the exit status.

| Boundary | Representation read | Proposition checked | Failure consequence |
| --- | --- | --- | --- |
| Validator verdict production ([21-wire](../docs/contract/21-wire.surface.md) lines 172–185; `emit_verdict`, [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c) lines 365–410) | native `sandbox_check` return and errno | *Producer obligation*: rc 0 → `allow`; rc 1, errno 0 → `deny`; rc −1, EINVAL → `unsupported_operation`; otherwise `error` | none checked downstream (see DT-48) |
| Host line admission ([ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift) lines 461–548; 21-wire lines 187–201) | raw stdout bytes | LF framing, strict UTF-8, JSON object, kind/schema, field types, string bounds; allow/deny require IDs and integer rc/errno. Not label/return coherence. | stops at the first refused frame; `decode_fault`; host outcome `validator_decode_failure` |
| Host association (`validatorAssociationIssues`, [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift) lines 157–187) | accepted verdict structs and the probes actually sent | unique group per expected ID; supplied metadata equal to the sent tuple, under Swift `String` equality (canonical equivalence) | issues are retained; host outcome `validator_unavailable` via `classify` ([CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift) lines 432–455) |
| Host order eligibility (`eligibleOrderedStep`, [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift) lines 4–24) | typed step query plus records | chain, setup, PID, coherent native return, unique canonical-equal record and tuple | sets `order`; nothing else |
| Host shared-memory decoders | raw worker region bytes plus host arguments | setup: decision snapshot, raw actor/required association, cell validity, primary cell (`decodeAuthoritySetup`, [AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift) lines 55–111); receipt: nine ordered capture conditions (`decodeProfileCapture`, [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) lines 679–714) | `integrity_errors`; receipt `unavailable` with a reason |
| Actor scheduler (`setupDisposition` and its caller, [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift) lines 257–288) | decoded setup scope plus the header words `actor_setup` and `authority_status` | no integrity errors; not terminal; applied/declared setup; then `actorSetup != 0 && (status >= 3 \|\| (authorityFD != nil && status != 1))` refuses. By source, every launched actor in a run with an authority plan has a descriptor, so for those actors the gate requires `status == 1` (MAPPED). | actor not activated (`setup_failed` and similar) |
| Host reporting validation (`validateForReporting`, [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift) lines 241–378, called by `pwRunnerReportData`, [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift) lines 122–155) | assembled typed reply | claims vs basis, phase partition, collection/validator consistency, validator ownership (shared join), `query_first ⇒` eligibility (shared predicate), exec/fresh observations, actor and authority shapes, receipt status/labels | rich fallback: `runner_reporting_failed`, `rc` 1, comparisons removed; then minimal reply; then empty bytes |
| Controller structural decode ([21-wire](../docs/contract/21-wire.surface.md) lines 72–86) | client and host frame bytes | grammar, fingerprint, required fields, kinds | client/host refusal; result exit 1 |
| Controller `reply_contract` / `admission_problem` ([run_flow.rs](../controller/src/run_flow.rs) lines 99–107, 330–355; [porcelain_admission.rs](../controller/src/porcelain_admission.rs) lines 1308–1330) | typed reply | producer contract; collection geometry; each receipt's status and `producer`/`capture_stage` labels | `unsupported_runner_response` or `malformed_runner_response`; result exit 1; diagnostics null |
| Controller semantic admission (`admit_reply` 1436–1505, `validate_lifecycle` 385ff, actor `setup` [porcelain_actor.rs](../controller/src/porcelain_actor.rs) 385–466) | typed reply (sees dependents the JSON projection can hide, DT-108) | phase partition; literal association recomputation; `query_first ⇒` eligible; lifecycle claims vs raw fields; actor/authority shapes; terminal setup ⇒ required ∧ primary | `process_disposition: withheld`, `disposition_integrity: invalid`, findings; **result unchanged** |
| Result selection ([result.rs](../controller/src/interface/result.rs) lines 142–237) | admitted host label | `Admitted { integrity_issues }` is carried, but no row reads it; only exact `finished` gives true/0 ([40-envelope](../docs/contract/40-envelope.surface.md) lines 185–194) | n/a |
| Python `porcelain.decode_bound` | frame bytes | same grammar, independently generated tables | decode error |
| Python `consumer.validate` ([consumer.py](../tests/lib/consumer.py) lines 1085–1104) | envelope JSON, plus captured bytes decoded and compared for equality ([runner_client_capture.py](../tests/lib/runner_client_capture.py) lines 366–450) | shape allowlists; client admission; result consistent with admitted label; phases and literal association ([phase_evidence.py](../tests/lib/phase_evidence.py) lines 38–107); comparisons; `order ⇔ eligible` (lines 555–558); extension and actor evidence; receipt status/labels. Not lifecycle claims; not the values of Rust diagnostics. | test verdict only |
| Lifecycle oracle ([lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) lines 531–700) | envelope JSON | every claim against the value it computes from its own raw field; projection form (an invalid record must be `withheld`); phase ownership via the consumer's own `ownership_problem`; extension evidence via the shared reader | test verdict only |
| `actor_evidence`, `extension_evidence` | reply body JSON | operation shapes; terminal setup ⇒ required ∧ primary; custody relationships | test verdict only |

Two features of this map matter for the anchors.

- **Which layers can change the result.** Host receiver, classification and
  reporting validation change the host label, and so the result. Controller
  capture, frame and `reply_contract` checks refuse the reply. Once a decoded
  reply passes the producer-contract gate, the receipt status/label check
  (with collection geometry) is the only semantic-record check that changes
  outcome and exit. Every other controller check only adds findings, by
  documented design (40-envelope lines 185–194; 41-diagnostics lines 657–666).
  A relationship that the host does not test, or tests under its own rule,
  reaches only the layer that cannot change the result. This is the common
  route for DT-48, DT-50, DT-53, DT-61 and DT-95.
- **Same predicate, different inputs.** Swift reporting validation re-checks
  association and order with the same functions the host used to produce them.
  It supplies different inputs: the reply's own step tuples instead of the
  sent probes (PWRunnerReply.swift lines 64–73), and the reply's projected
  setup and PID instead of the live ones (lines 357–368). The stated rationale
  is uniform phase ownership (PWRunnerReply.swift lines 51–57;
  [FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
  lines 605–622) and checking reported rather than live inputs
  ([31-steps](../docs/contract/31-steps.surface.md) "Order association
  source"). So the reporting check can detect a misattached or copied block,
  expected IDs that differ from the reply's plan, records altered after
  association, and an order claim whose reply-visible prerequisites fail. It
  cannot disagree with the production rule itself. This describes its scope;
  it is not a defect.

### Acceptance anchor traces

#### Acceptance trace of DT-48: label/return coherence is an emitter obligation, checked only inside order eligibility

**Sequence.** The emitter rule (21-wire lines 172–185) assigns labels from the
native pair. Host line admission (lines 187–201) states a type-and-presence
check and does not test the pair. `classify` does not test it either.
`buildSandboxCheckResult` copies `outcome`, `rc` (default −1) and `errno`, and
sets `native_rc` from any allow/deny/error record (CWorkerStepResults.swift
lines 44–49, 128–139). The coherence test exists only inside the order rule's
"Native answer" condition (31-steps lines 613–617). Swift construction and
reporting (PWRunnerStepEvidence.swift lines 5–9), Rust (porcelain_admission.rs
lines 1204–1208) and Python (`eligible_order`, consumer.py lines 256–284)
implement it only there.

**Executed (live and seam).** The DT-48 result reproduces at this snapshot.
The four combinations of coherence and order claim behave as follows. The two
edited rows are seam frames with the constructed contract binding:

| Row | Record | `order` | Result | Rust | Python consumer | Oracle |
| --- | --- | --- | --- | --- | --- | --- |
| `base_fixture` (live) | allow/0/0 | `query_first` | `finished`, 0 | `clean_exit`, `valid` | `[]` | `[]` |
| `incoherent` (live) | allow/−1/13 | `unestablished` | `finished`, 0 | `clean_exit`, `valid` | `[]` | `[]` |
| `f48-claimed-order` (seam: `incoherent` with order → `query_first`) | allow/−1/13 | `query_first` | `finished`, 0 | `withheld`, `invalid`: "query_first lacks eligible prediction and complete ordering chain" | "query_first lacks eligible record or ordering chain" | `[]` |
| `f48-withheld-order` (seam: `base_fixture` with order → `unestablished`) | allow/0/0 | `unestablished` | `finished`, 0 | `clean_exit`, `valid`, no finding | "eligible record with complete chain requires query_first" | `[]` |

On the live incoherent run, `consumer.query_column` returns `allow`. The
public step carries `outcome: allow`, `rc` −1, `native_rc` −1, `errno` 13 and
`result_source: validator`. The raw record and its `raw_line` are retained.

**What this establishes.**
- *Incoherent record with a claimed order.* The order-checking readers that
  were run reject it: Rust with `withheld`/`invalid`, and the consumer. The
  lifecycle oracle does not check `order` and returned `[]`. Swift reporting
  was not run on this frame. By source it would reject the claim
  (PWRunnerReply.swift lines 365–368), and the host does not produce it,
  because construction computes `order` with the predicate that includes
  coherence.
- *Incoherent record without an order claim.* On the live run every
  boundary accepted it: Swift host classification and reporting, Rust, the
  consumer and the oracle. The label is then "the raw query answer" under
  reading rule 1 (FAILURE-PROPAGATION-CONTRACT.md lines 1401–1411) and "the
  associated answer" under the steps `outcome` meaning (31-steps line 69).

The arrangement is deliberate delegation: the host's receiver statement
assigns itself only types and presence, and the label rule belongs to the
emitter. The cost is interpretive. The only reply value that reflects the
incoherence is `order: unestablished`. That value is shared with a broken
chain, failed setup, missing association and a PID mismatch, so a reader who
wants to know *why* an answer is not credited must recompute coherence from
`rc`, `native_rc` and `errno`.

A search of `tests` (excluding `tests/out`) for `query_column` in `*.py` found
three uses. The first is the consumer's own `select` helper (consumer.py line
1142). The second is `runner_exec_dac/check_query_scope.py` line 166, which
asserts `unavailable`. The third is `witness_contract/check_comparison_matrix.py`
line 151, which compares the column with the matrix row's expected `query`
beside all six comparison keys, including `order` (lines 148–152). A search for
`select(` calls with a `query=` argument found one,
`check_query_scope.py` line 190, which also requires `order='query_first'`.
None of these relies on the label without the order or an expected row.

DT-108's conditional-null rule does not arise in these rows: the host sets
`result_source` on every built query, so `native_rc` stays visible.

The last row is a separate result, DT-130.

#### Acceptance trace of DT-50: one identity rule in Swift, another in Rust and Python

**Sequence.**
- *Swift.* Canonical equivalence governs: request duplicate refusal
  ([ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift) lines
  112–117), association grouping and metadata equality, order matching,
  lifecycle step joins (CWorkerStepResults.swift line 55) and every
  reporting-validation `Set`.
- *Rust.* `BTreeMap<&str>` grouping and `==` on bytes (porcelain_admission.rs
  lines 1030–1091, `query_matches` at 776).
- *Python.* Dictionaries and `==` (phase_evidence.py lines 38–67; consumer.py
  lines 256–284).
- *Statements.* Two rules write identity as an unqualified `==`: "Unique
  association" (31-steps lines 619–630) and the cardinality conditions
  ([32-lifecycle](../docs/contract/32-lifecycle.surface.md) lines 1168–1252).
  The ownership paragraph that begins "Every semantic reader checks
  ownership … the same way" (FAILURE-PROPAGATION-CONTRACT.md lines 605–622)
  fixes a shared procedure and states no equality relation (quoted under
  DT-135). Only two explicit equality definitions exist in the stated rules:
  canonical for `same_submitted` (reading rule 4, line 1419; implemented in
  Python as `same_submitted_string`, consumer.py line 176) and bytes for
  path-form `same_as_input`.

**Executed (live; seam rows match the live envelopes field for field).**

| Run | Host association issues | Host outcome | Order | Rust findings | Consumer findings | Oracle |
| --- | --- | --- | --- | --- | --- | --- |
| `nfc_id` | `[]` | `finished` | `query_first` | none, `valid` | `[]` | `[]` |
| `nfd_id` | `[]` | `finished` | `query_first` | association disagree; `query_first` lacks eligible…; `withheld`/`invalid` | `query_first` lacks eligible…; association disagree | D6 association disagree |
| `nfc_value` | `[]` | `finished` | `query_first` | none | `[]` | `[]` |
| `nfd_value` | `[]` | `finished` | `query_first` | the same two as `nfd_id` | the same two | D6 |
| `dup_id` | `duplicate_id` `s-é` count 2 | `validator_unavailable`, exit 1 | `unestablished` (query synthetic) | association disagree | association disagree | D6 |
| `both_ids` | n/a | `bad_request` `duplicate_step_id` at `probe_plan.1.step_id` (host refusal; no worker) | n/a | none | `[]` | `[]` |

**What this establishes.**
- DT-50 reproduces at this snapshot.
- The split is not specific to step IDs: it applies equally to the record's
  `filter_value` (DT-131).
- In `dup_id`, the layer that changed the result was host classification,
  under Swift's canonical grouping. Swift saw one group of two records, so it
  associated neither and the step's query is synthetic. Rust and Python, which
  group literally, recompute one associated NFC record and one `unexpected_id`
  NFD record. They flag only the disagreement in the stored issue list. By
  source inference, the literal issue list would also make `classify` report
  `validator_unavailable`, but it would have associated the NFC record with
  the step.
- Python did not flag a withheld order in `dup_id`, although its order check
  runs in both directions. Its eligibility test reads the step's own query,
  and that query is synthetic.
- `both_ids` shows that Swift also applies canonical identity at request
  admission. That is a different boundary: the request, not the evidence
  reply. Its consequence is that a reply can never carry two canonically
  equivalent step IDs. The literal step/phase joins in Rust and Python
  therefore agree with Swift on step identity only because Swift restricted
  the input. Identities that enter through child output (validator records)
  are where the readers diverge.
- In `nfd_id` and `nfd_value` the reply carries host `association_issues: []`
  and `query_first`, while Rust withholds the disposition. The result stays
  true/0.
- The number of readers that object overstates the number of independent
  judgments. The oracle's D6 finding is the consumer's `ownership_problem`
  ([lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) lines 556–560).
  Swift's non-objection is its production join, re-applied by reporting.

These transcripts are steered. No claim is made that the shipped validator
rewrites IDs or values.

#### Acceptance trace of DT-53: lifecycle claim checks belong to Rust and the oracle, not the general consumer

**Sequence.**
1. The host producer rejects a missing claim
   ([DispositionResolverTests.swift](../runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift)
   line 345 constructs that case). By source, such a record reaches the wire
   only in a degraded reply.
2. All seven run questions are optional in the binary schema
   (`PWDispositionRunQuestions`, [porcelain.json](../docs/porcelain.json)), so
   decoding accepts absence.
3. Rust `validate_lifecycle` reports a missing claim as `malformed_record`
   (porcelain_admission.rs line 204) and a value that differs from the raw
   reaped status as "final_status contradicts reaped status" (lines 433–460).
4. `project` withholds the disposition. Result selection ignores it.
5. The general consumer neither checks claims nor reads the values of
   `disposition_integrity` or `process_disposition`. It checks only the
   `subject_path` references of issues (consumer.py lines 954–972).
6. The oracle checks every claim against the value it computes from that
   claim's own raw field, and checks that an invalid record is projected as
   `withheld` (lifecycle_oracle.py lines 118–150, 665–676).
7. Claim "truth" in both Rust and the oracle means agreement with the retained
   raw field. Whether those raw fields are independent observations is
   outside both checks. For example, DT-46 and DT-120 show that the raw
   `cleanup_trigger` is derived from the stored stop reason.

**Executed (seam; frames are `base` with the constructed contract binding and
one further edit).**

| Row | Result | Rust diagnostics | Consumer (bare and envelope) | Oracle |
| --- | --- | --- | --- | --- |
| `f53-final-status-absent` | `finished`, 0 | `withheld`, `invalid`: "final_status: missing claim" | `[]`, `[]` | D8 `malformed_record` "record.questions lacks final_status" |
| `f53-final-status-17` | `finished`, 0 | `withheld`, `invalid`: "final_status contradicts reaped status" | `[]`, `[]` | D1 `wrong_answer` |

DT-53's controls edited saved JSON, and the full consumer refused those
envelopes because they differed from the retained bytes. Here the edit is in
the frame and passes through the actual Rust decode and admission path, so
captured bytes and JSON agree. The consumer then accepts an envelope that
carries Rust's `withheld`/`invalid`. DT-53's third edit (a null claim) has no
separate binary form; absence covers it.

**Which callers run which readers.** Scope: the 283 listed cases; each case's
command script and the `.sh`/`.py` files it names (resolving `${ROOT_DIR}` and
`${SUITE_DIR}`). Reader calls were found by source-text patterns:
`consumer.validate(`, `validate_fixture`, `from consumer import … validate`,
`check_record`/`check_actor_records`/`check_fixture_record`,
`witness_capture`. One false positive was removed: `shell_helpers` defines an
unrelated local `check_record`. Source-drift cases that merely share a
`run.sh` were excluded. The map is in
`.tmp/contract-trio/acceptance/reader-case-map.jsonl`.

- Thirteen default cases, plus two opt-in ones, run the oracle:
  - through `witness_capture.capture`, which runs the consumer and then the
    oracle ([witness_capture.py](../tests/lib/witness_capture.py) lines 13–26),
    or by direct calls beside the consumer: `witness_contract/` `phases`,
    `extensions`, `extension_directory`, `extension_policy_qualification`,
    `extension_redelegation`, `extension_boundaries`, `actor_compositions`,
    `actor_timing_qualification`, `worker_killed_before_slot_publication`;
  - `witness_contract/worker_attempt_in_flight_at_deadline`, which calls the
    oracle without the consumer and asserts `process_disposition` itself;
  - `blackbox_e2e/checker_controls`, on constructed JSON envelopes;
  - `source_drift/porcelain_codec`, offline;
  - `runner_unit/pwrunner_core_unit_executable`, through the Rust corpus test,
    on constructed Swift frames;
  - opt-in: `witness_contract/actors_byoxpc`, `witness_contract/worker_wait_pilot`.
- Thirty default cases are attributed, by checker file, to the consumer
  without the oracle:
  - `runner_validator_failure/*` (3 cases);
  - `runner_outcome_validator_no_reply/validator_io_deadline_releases_worker`;
  - `runner_exec_dac/execute_permission_controls_spawn`;
  - four `runner_exec_lifecycle` cases;
  - `sbpl_allowdeny_consistency/sbpl_allowdeny_v1`;
  - twenty `witness_contract` cases, including the seven that use
    `check_ordering.py`, `comparison_matrix`, `test_input` and
    `max_targets_reply_survives`.
- Two of those thirty are offline.
  - `runner_validator_failure/transcript_controls` runs `check.py fixture`. Its
    `check_fixture` (runner_validator_failure/check.py line 53) does not call
    the consumer. The file calls the consumer only in its CLI mode (lines
    107–114), so this case is attributed to the consumer by file only.
  - `witness_contract/example_round_trip_controls` reads authored envelopes
    "in place of the app's emission"; no process runs
    (example_round_trip_controls.py lines 4–12). It tests the round-trip
    checker on constructed envelopes, not a live run's diagnostics.
- The catalog lists `app` among the requirements of each of the other
  twenty-eight. Of those twenty-eight, two assert a Rust diagnostics value
  that a withheld projection would change:
  - `witness_contract/example_round_trip`: `disposition_integrity == valid` and
    no issues (check_example_round_trip.py lines 1123, 1321);
  - `witness_contract/worker_termination`: `process_disposition`, line 94.
- Two more mention diagnostics, but their assertions would not detect a
  withheld projection. `pre_apply_failure_reports_no_policy_verdict` admits
  `termination_cause: unknown` (check_pre_apply_failure.py lines 67–80), and
  `dossier_witness` asserts null diagnostics only on refusal paths.
- This was a text search of each checker file for `runner_sandbox_diagnostics`,
  `termination_cause`, `disposition_issues`, `process_disposition` and
  `disposition_integrity`. An `ok` or exit assertion cannot substitute,
  because Rust findings do not change the result.
- Twelve opt-in cases are consumer-only (six `runner_byoxpc`, `guide_workflows`
  and others).
- `failure_boundaries/*` uses neither Python reader.

For the other twenty-six live default cases attributed to the consumer without
the oracle, a lifecycle-claim fault that only Rust and the oracle check would
not fail the case. This is a
statement of checked scope, not an observed miss: those cases were not run.

#### Acceptance trace of DT-61: readiness, as checked by the decoder, the scheduler and the body readers

**Sequence.**
1. *C worker* (`prepare_authority`,
   [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c)
   lines 676–752). It publishes each prerequisite cell and records a primary
   failure if any step fails. At the decision point it writes, together: the
   setup disposition, `primary_plus_one` and the header word
   `authority_status` (`MAPPED` iff the region pointer was bound after header
   validation). Then it release-stores `g_setup->published`. For required
   setup, READY and MAPPED come from the same program path and coincide.
2. *Host decoder.* It acquires the decision first and checks raw
   actor/required against its arguments and ready ⇒ required against the
   *argument* (line 98). It requires no prerequisite cell (DT-61's constructed
   control).
3. *Scheduler.* It requires a decoded decision that is free of integrity
   errors and not terminal. For a required actor, the decoder's argument
   check leaves `ready` as the only such decision. It then refuses when
   `actorSetup != 0 && (authorityStatus >= 3 || (authorityFD != nil &&
   authorityStatus != 1))` (ActorScheduler.swift lines 257–266).
   - The status values ([pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
     lines 161–162) are 0 none, 1 MAPPED, 2 DESCRIPTOR_MISSING, 3 REJECTED
     and 4 LOCAL_FAILED.
   - The current worker writes only 1, 4 or 2 (pw_probe_runner.c line 751):
     MAPPED when the region was bound, LOCAL_FAILED when required and not
     bound, DESCRIPTOR_MISSING when not required.
   - The host reads 0 unless the decoder has observed the decision
     (ActorSession.swift line 490).
   - For a launched actor, `authorityFD` is nil exactly when the run has no
     authority plan, which is also when `authorityRequired` is false
     (ActorScheduler.swift lines 231–232). With a plan, `descriptor(for:)` is
     nil only after a core-limit or region failure, or for an index outside
     `regions` (AuthorityCustody.swift lines 407–410). When the core limit
     succeeds, the custody builds one region for every actor index (lines
     359–362), so only the two failures remain. Either failure sets
     `setupFailure` (lines 390–398), and then the scheduler refuses every
     actor's launch (ActorScheduler.swift lines 208–217).
   - So, by source, every launched actor with required authority has a
     descriptor, and the gate requires status 1. Without a plan, status 0 or
     2 passes and 3 or more refuses.
   - The scheduler reads no prerequisite cell.
4. *Reply.* `authority_status` is not a wire field: `docs/porcelain.json` has
   no such name. When the gate refuses, the word appears only inside the
   classifier's error text, `shm setup: worker authority setup: status=…
   detail=…` (ActorScheduler.swift line 264; CWorker.swift line 749). The
   reply carries the decoded scope, with its decision and cells, and the
   actor's `setup_status`.
5. *Body readers.* Swift `authoritySetupIntegrityErrors`
   (PWRunnerAuthoritySetup.swift lines 142–213), Rust `setup` (porcelain_actor.rs
   lines 385–466) and Python `_setup` (actor_evidence.py lines 121–160) all check
   terminal ⇒ required ∧ primary. None checks ready ⇒ required
   ([34-equipment](../docs/contract/34-equipment.surface.md) lines 912–917) or
   the prerequisite prefix that the producer rule assigns to host and worker
   ([14-extensions](../docs/contract/14-extensions.surface.md) lines 349–360).
   Rust `application` (porcelain_actor.rs lines 468–603) and Python
   `_application` (actor_evidence.py lines 162–225) relate an actor's
   application to its scope in one direction only. An `applied` actor must not
   carry an observed `terminal_required_failure` scope, and the
   `terminal_authority_setup_refusal` assessment requires one. No reader
   relates a `ready` decision to its prerequisite cells or to `required`.

**Executed (seam; the live `actor` frame with the constructed contract binding
plus one edit to the subject's worker setup scope).** The live baseline: both
workers `ready`, `required: true`, 12 cells including `core_limit` succeeded,
`mmap` succeeded and `header_binding` accepted; subject `setup_status: applied`;
query `before` deny / `after` allow, both `query_first`. The Swift host
accepted the live run, and the Rust and Python readers returned no finding.

| Row | Result | Rust | Consumer | `actor_evidence` / `extension_evidence` | Oracle |
| --- | --- | --- | --- | --- | --- |
| `f61-core-limit-absent` (cell 3 removed; `ready` kept) | `finished`, 0 | `per_actor`, `valid`; both actors `clean_exit`; no finding | `[]` | `[]` / `[]` | `[]` |
| `f61-core-limit-failed` (cell 3 `failed`, `native_rc` −1, `errno` 1) | `finished`, 0 | the same | `[]` | `[]` / `[]` | `[]` |
| `f61-not-required` (`required: false`; `ready` kept) | `finished`, 0 | the same | `[]` | `[]` / `[]` | `[]` |

These confirm DT-61's JSON-body observations for Rust and Python on frames
that pass through the actual Rust decode, admission and assembly path. **The
Swift side remains source-only:** neither the Swift reporting validator nor the
Swift decoder was run on these frames. DT-133 states the consequence.

#### Acceptance trace of DT-95: the outcome-changing receipt check reads constants; the binding checks run once, in the host decoder

**Checked by the host decoder** (CWorker.swift lines 679–714, in order):
1. observed application with rc 0;
2. `done`, exit 0, no signal;
3. capture-completion publication;
4. capture status 1;
5. recorded PID equal to the host-owned worker PID;
6. valid request nonce equal to the recorded nonce bytes;
7. profile type 0 and 0 < length ≤ the buffer;
8. SHA-256 of the copied bytes equal to the recorded digest;
9. recorded source length and digest, and parameter count and digest, equal
   to the host's supplied inputs.

These nine conditions are source-read here. DT-101 found that the cited unit
check asserts `unavailable` for eleven corruptions but asserts no reason. It
also found that six of the nine reasons are named in no test, and that no case
combines two failing conditions, so the first-failure order has source support
only.

The decoder then emits the request nonce string, the recomputed digest, the
copied bytes, its own source length and parameter count, the recorded digests,
and constant labels. Presence is decided by the host's capture flag
([35-profile](../docs/contract/35-profile.surface.md) lines 114–125, `who: host`).

**Delegated to "the host capture rule" (35-profile line 309) and re-checked by
no recipient:**
- presence ⇔ capture requested;
- `request_nonce` = the request nonce;
- `worker_pid` = `runner_subprocess.pid` or the actor launch PID;
- decoded length of `bytecode_b64` = `bytecode_length` (stated condition, lines
  87–91, no checker);
- 0 < `bytecode_length` ≤ 1,048,576 (lines 73–79, no checker);
- `bytecode_sha256` = SHA-256 of the bytes;
- `source_sha256` = SHA-256 of the request source = `policy_sha256`;
- `source_length` = request source length;
- `params_sha256` and `parameter_count` match the request parameters;
- `profile_type` = 0;
- no `reason` on `captured`; a `reason` and no capture fields on `unavailable`.

**Checked by recipients:** status ∈ {captured, unavailable}; captured ⇒
`worker`/`before_apply`; unavailable ⇒ neither label. This is the same
predicate in the host's `contextProblem`
([PWRunnerProfileCapture.swift](../runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift)
lines 31–44), Rust `admission_problem` and Python `_validate_capture`
(consumer.py lines 575–588).

**Executed.** Seam rows carry the constructed contract binding:

| Row | Edit | Result | Rust | Consumer | Oracle |
| --- | --- | --- | --- | --- | --- |
| `capture` (live) | none | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-receipt-unrequested` | `capture`'s receipt (worker PID 51003) inserted into `base`, whose request has no capture | `finished`, 0 | `valid`, no finding | `[]` | `[]` |
| `f95-nonce` | `request_nonce` → 32 `f` | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-byte` | one byte of 492 flipped; length and digest kept | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-length-zero` | `bytecode_length` 0 | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-producer-host` (label control) | `producer` → `host` | seam: `finished`, 0, `withheld`/`invalid` with `reply_admission` "compiled_profile context is inconsistent" | — | "compiled_profile requires worker/before_apply context" | `[]` |

The production run path refuses the label control before semantic admission.
To confirm that at this snapshot, the existing test
`run_flow::tests::orchestration::compiled_profile_labels_determine_the_public_admission_outcome`
was run from the same isolated binary, with `TMPDIR` set to scratch, and
passed. It injects typed replies, deserialized from JSON, into the real `run`
orchestration: label failures give `malformed_runner_response` and exit 1;
the fixture's contradictory `captured` row gives `finished`. The seam row shows
how the same check reads where `reply_contract` is bypassed. It is not the
production outcome. The receipt edits confirm DT-95's saved-JSON and typed
observations on frames read by Rust and Python. DT-134 states the cross-anchor
consequence.

### Acceptance agreement classification: deliberate division, restricted inputs or shared code, and questionable rules

| Agreement | Basis | Classification | Concrete cost |
| --- | --- | --- | --- |
| Every boundary accepts an incoherent allow record without an order claim on the live run (DT-48) | Emitter obligation (21-wire 172–185); host receiver states types only; reading rule 1 names the label as the raw answer | Deliberate delegation to the native emitter, faithfully followed by the readers | With a steered or foreign validator, `allow` beside rc −1 is reported as the raw answer. The only signal, `order: unestablished`, has several causes. |
| Swift objects to nothing in `nfd_id`; Rust and Python object (DT-50) | Swift association and reporting share one join; Python consumer and oracle share another | Shared code inside each language | Three objections from Rust, the consumer and the oracle are two independent judgments. Swift's silence is not an independent confirmation of its own association. |
| Rust and Python agree with Swift on step-to-phase joins (DT-50) | Swift request admission refuses canonically equivalent IDs (`both_ids`) | Agreement through restricted inputs | Holds only for identities that pass request admission; validator-record identities fall outside it. |
| The readers that were run (Rust, the consumer, `actor_evidence`, `extension_evidence`, the oracle) accept `ready` without prerequisites or with `required: false` (DT-61); Swift's body check, by source, also does | No recipient check is assigned. Ready ⇒ required is a condition of a `who: host` report (34-equipment 912–917), and the prefix is a host/worker act (14-extensions 349–360). In production the decoder projects `ready` only when its required argument is true, and copies that argument into `required`. The C worker writes READY only after every prerequisite. | **Shared assumption.** The readers agree because they rely on the producer: the decoder's projection rule and the C program order. It is not deliberate delegation: unlike DT-95, no statement delegates the check, and no rationale for leaving recipients out was found. It is not a questionable rule: the condition itself holds in production. | A final reply that breaks the condition is reported as valid by every reader run; see DT-133. |
| The readers that were run accept receipts whose association is wrong (DT-95); Swift's `contextProblem`, by source, also does | Stated delegation (35-profile line 309) | Deliberate division of responsibility | A `captured` receipt in a `finished` envelope asserts association only through the host decoder; recipients cannot tell a correct receipt from a detached one. See DT-134. |
| Three layers apply the same receipt-label predicate, and it alone changes the result (DT-95, DT-96) | The host writes `producer` and `capture_stage` as constants (DT-96) | Design judgment, labeled as such: a questionable allocation, faithfully implemented | The checks that decide the outcome read values that carry no observation, while the request-binding checks run once, before the reply. A refusal says the reply is malformed; acceptance says nothing about the receipt's binding. |
| Lifecycle claims: Rust withholds, the oracle reports D1/D8, the consumer accepts (DT-53) | The reader-responsibility paragraph assigns claim checks to the oracle (FAILURE-PROPAGATION-CONTRACT.md lines 594–597) | Deliberate division across readers | Accepted by the consumer and invalid by Rust on the same envelope. Of the thirty default cases attributed to the consumer without the oracle, twenty-eight run the app. Twenty-six of those run no oracle and assert no Rust diagnostics value that a withheld projection would change (see DT-53). |

### Acceptance results: differently named successes, and identical results that hide different checks

- `finished`/`ok: true`/exit 0 establishes the host label. In this pass it
  co-occurred with:
  - Rust `withheld`/`invalid` (`nfd_id`, `nfd_value`, `f48-claimed-order`, the
    `f53` rows);
  - Python rejection with Rust `valid` (`f48-withheld-order`);
  - acceptance, by every Rust and Python reader that was run, of setup and
    receipt records that contradict their producer obligations or the request
    (`f61` and `f95` rows). Swift was not run on these frames.
- `disposition_integrity: valid` certifies the controller's checks
  (41-diagnostics lines 50–60; FAILURE-PROPAGATION-CONTRACT.md line 586). It
  does not certify withheld-order consistency (DT-130), ready-setup
  prerequisites (DT-133) or receipt binding (DT-134).
- `consumer.validate == []` certifies shape, capture equality, result
  consistency and the consumer's semantic families. On the same envelope it
  does not certify the lifecycle claims or the Rust verdict (DT-132).
- `association_issues: []` in the reply is the host's join under canonical
  equality. Rust's recomputation under byte equality can disagree on the same
  frame (`nfd_id`, `nfd_value`).
- Swift reporting acceptance means the stored result agrees with reply-visible
  inputs under the production predicate. Rust acceptance means agreement under
  an independently written predicate.
- Two `unestablished` orders can mean an incoherent record (DT-48), a missing
  association, a synthetic query after a Swift duplicate (`dup_id`), or a
  broken chain. No field states which condition failed. A reader can tell
  them apart only by recomputing the conditions from `result_source`, `rc`,
  `native_rc`, `errno`, the phase ordering and the records.
- `ready` from the decoder means a published decision consistent with the
  host's expected-required argument. For an actor in a run with an authority
  plan, scheduler activation means, by source, that the MAPPED word was
  observed. The reply shows the first, and implies the second only through
  `setup_status`.

### DT-130 — Rust and Python accept different order propositions; a withheld order on an eligible record is valid for Rust and invalid for the consumer

**Statements.** The producer obligation is an if-and-only-if. The host
"Establish query order" rule (31-steps lines 573–596) sets `query_first` on
success and `unestablished` on failure, and the record table says "only when
… `unestablished` otherwise" (FAILURE-PROPAGATION-CONTRACT.md line 1226). The
recipient statements differ. The controller's family is "the complete
`query_first` chain" (41-diagnostics line 678), one direction. The consumer
"validates … `order` against the raw channel fields and `ordering`" (line
1378), with no direction stated. No statement assigns any recipient the check
that an eligible record's order was not withheld.

**Implementations.** Rust skips steps whose order is not `query_first`
(porcelain_admission.rs line 1185). Swift reporting checks only claimed
`query_first` (PWRunnerReply.swift lines 365–368; source). Python checks both
directions (consumer.py lines 555–558), and its checker control
`unestablished_despite_chain` (`checker_controls.py` line 457) pins that. That
control feeds a JSON envelope whose "host bytes" are compact JSON text:
`recapture_host_reply`, [blackbox.py](../tests/lib/blackbox.py) lines 16–31,
read through `validate_fixture`. Rust never sees it.

**Executed (seam, constructed contract binding).** `f48-withheld-order`: Rust
`valid`, no finding; consumer "eligible record with complete chain requires
query_first", on both the bare reply and the Rust envelope; oracle `[]`;
result `finished`.

**Scope and cost.** Each implementation stays within its own statement. This
is a difference in checked proposition, not a broken statement. By source, the
host computes `order` with the eligibility predicate, so it does not produce
the state. A reader cannot treat Rust `valid` as covering under-credited order,
and the Python checker control establishes nothing about Rust.

### DT-131 — The canonical/literal split also governs validator filter values and the host's own failure outcome; request admission confines it to child-output identities

**Executed (live).**
- `nfd_value` repeats DT-50's pattern on `filter_value`. Swift associates and
  emits `query_first`. Rust reports "association issues disagree" and "query_first
  lacks eligible…", the consumer reports both, the oracle reports D6. Result
  `finished`.
- `dup_id`: Swift grouped the NFC and NFD records as one duplicate group,
  withheld the step's validator answer (synthetic query, `unestablished`) and
  classified the run `validator_unavailable`, exit 1, with error "duplicate_id:s-é".
  Rust and Python recompute one associated record plus one unexpected record
  and flag the disagreement.
- `both_ids`: the host refused the request as `duplicate_step_id` at
  `probe_plan.1.step_id`. The controller has no duplicate check of its own
  (no `duplicate_step_id` in `controller/src`).

**Statements.** Identity is an unqualified `==` (31-steps lines 619–630;
32-lifecycle lines 1168–1252). The step ID is "unique across all actions"
([12-probes](../docs/contract/12-probes.surface.md) line 23) without an
equality relation. Explicit equality is defined only for `same_submitted`
(canonical) and path forms (bytes). The comment on `validatorAssociationIssues`
(PWRunnerPredictionEvidence.swift line 157), "shared with every reader that
recomputes it", is accurate for the Swift readers, which share the code. As a
statement of the rule every reader applies, it matches the ownership
paragraph quoted under DT-135. The Rust and Python readers implement that rule
independently. The implementations diverge because the rule does not state
its string equality.

**Cost.** The host's result-changing decision (`dup_id`) and its non-decision
(`nfd_id`) apply the association procedure under canonical equality, while the
independent readers apply the same procedure under byte equality. A reader
of the public envelope sees a host outcome and a controller finding that
disagree about how many records were associated. Steered transcripts; no
native rewrite is claimed.

### DT-132 — On a byte-consistent envelope, the general consumer accepts lifecycle-claim faults that Rust reports as withheld and invalid

**Executed (seam, constructed contract binding).** A missing `final_status`
claim, and a `final_status` value of 17 beside a raw exit code 0, each passed
the actual Rust path to `withheld`/`invalid` with the matching finding, and
`finished`/0. `consumer.validate` returned `[]` for the bare reply and for the
complete envelope, whose captured bytes are the edited frame. The oracle
reported D8 and D1.

**Scope.** This extends DT-53 from saved-JSON edits to a frame read by the
Rust and Python readers. The reader-responsibility paragraph
(FAILURE-PROPAGATION-CONTRACT.md lines 594–597) describes the consumer's checks
as shape, required-field and semantic checks, and assigns lifecycle claims to
the oracle. I read that as deliberate division, so this is not an unmet
consumer promise. The consequence is in the registry. Thirty default cases are
attributed, by checker file, to the consumer without the oracle, and
twenty-eight of them run the app. Two of those twenty-eight assert a Rust
diagnostics value that a withheld projection would change. Lifecycle
claim faults that only Rust and the oracle detect would pass the other
twenty-six, by checked scope. No live omission was observed.

### DT-133 — Required-authority activation is gated on a header word the reply does not retain; reply readers relate application only to a terminal setup scope, never `ready` to its prerequisites

**Source.** The scheduler admits an actor's setup when four conditions hold
(ActorScheduler.swift lines 257–288):
- the decoded scope has no integrity errors;
- the decision is not terminal;
- `actor_setup` shows an applied or declared setup;
- the gate `actorSetup != 0 && (status >= 3 || (authorityFD != nil && status
  != 1))` does not refuse.

For a launched actor under an authority plan, the descriptor is present by
source (DT-61 trace, step 3), so the gate reduces to `status == 1` (MAPPED).
MAPPED is written by the same C decision block as the disposition
(pw_probe_runner.c lines 748–753), from the bound region pointer rather than
the primary-failure variable. It is a second
encoding of one decision, not an independent observation. It is absent from
the wire schema and appears only inside the classifier's error text when the
gate refuses.

**Executed (seam, constructed contract binding).** A frame with `ready` and a
missing or failed `core_limit` cell, or `required: false`, beside
`setup_status: applied`, was `finished` with Rust `valid` per actor and `[]`
from the consumer, `actor_evidence`, `extension_evidence` and the oracle.
Swift reporting was not run on these frames. By source, it does not check
these relationships.

**What a final-reply reader cannot distinguish.** Rust and Python do require
an applied actor's scope not to be terminal (DT-61 trace, step 5). No reader
relates a `ready` scope to its cells or to `required`. From `ready`,
`setup_status: applied` and a missing or failed prerequisite cell, a reader
cannot tell whether the worker's MAPPED word was observed and a cell was lost
before the reply, or whether the cells are accurate and the scheduler
activated on a different fact. The C program order makes the two coincide in
production. That shared assumption is the only thing joining the activation
decision to the retained cells.

### DT-134 — After producer admission, only geometry and the receipt's constant labels change the run result; the receipt's request binding is checked once, before the reply, and nowhere after

**Map.** The acceptance boundary map lists every boundary that can change the
result. After the controller holds a decoded reply under the expected producer
contract,
collection geometry and the receipt status/label check are the only
semantic-record checks that refuse the reply. Every other relationship adds
diagnostics or is unchecked. That includes the receipt's request association
and its internal byte, length and digest relations.

**Executed (seam, constructed contract binding; and unit).** A receipt
inserted into a reply whose request did not ask for capture (carrying a
different worker PID), a replaced nonce, a flipped bytecode byte and a zero
length were each `finished` with Rust `valid` and consumer `[]`. The existing
label test passed at this snapshot.

**Cost (design judgment, labeled).** The outcome-changing check reads two
values the host writes as constants (DT-96). The association checks run once,
in `decodeProfileCapture`, and nothing in the reply lets a recipient
distinguish a correct receipt from a detached one without the request. The
live tests that do compare (contract.py lines 323–332, 430–435, 483–488) do so
for their own outputs. The statement acknowledges the delegation, so this is
not an unmet promise. The concern is that the only receipt check visible in
the outcome is the one with the least evidential content.

### DT-135 — Swift reporting re-checks association and order with the production predicate, and the oracle's phase finding is the consumer's; agreement counts overstate independent judgments

**Source.** `validatorOwnershipProblem` recomputes issues with
`validatorAssociationIssues` (PWRunnerReply.swift line 77), and the order
check calls `eligibleOrderedStep` (line 365), the functions that produced the
values. The oracle's D6 comes from `phase_evidence.ownership_problem`, the
consumer's function (lifecycle_oracle.py lines 556–560). The oracle's
extension check is the consumer's `validate_extensions` (line 591).

**Executed.** In `nfd_id`, `nfd_value` and `dup_id`, three readers object:
Rust, the consumer and the oracle. Only Rust and Python are independent
implementations, and Swift's silence is its production rule restated.

**Statement.** FAILURE-PROPAGATION-CONTRACT.md lines 605–614 read in full:

> Every semantic reader checks ownership of a phase's validator subprocess the
> same way. The block carries `phase_id` and `ordinal`, stamped by the host from
> the collection it ran, and both must equal the containing phase's. Its
> `expected_step_ids` must name exactly the phase's eligible query plan: the
> phase's ordinary steps whose retained query decision is not
> `query_not_requested`, read from the reply rather than by resolving paths again,
> so a block beside a phase without eligible queries carries an empty plan. Step
> order is the partition and step-order checks' question, not ownership's. Its
> `association_issues` must be the
> issues its retained `records` and that plan imply, recomputed by the reader.

The paragraph continues to line 622. That remainder says a copied block fails
validation, that unexpected, duplicate and null-ID records remain diagnostic
evidence, and that PID uniqueness is not an invariant. It states no equality
relation either. The paragraph promises one ownership procedure: the stamp
comparison, the plan comparison, and recomputation of the issues the records
and the plan imply. It does not state the equality relation that the
recomputation uses.

**Scope.** The rationale for sharing code is stated: uniform ownership checks,
and reporting validated against reply-visible inputs (see the acceptance
boundary map). That uniformity holds within each language. Across languages the readers apply
the same procedure with different equality relations, so on canonical-variant
inputs they compute different implied issues (DT-50, DT-131). I read "the same
way" as fixing the procedure, not the equality. On that reading the
disagreement is an unstated relation that the implementations bind
differently, rather than a contradicted promise. Either way, counting reader
verdicts does not measure independent confirmation.

### Acceptance cross-references to earlier findings

- **DT-23 and DT-51** (unapplied-actor validator failures become `finished`)
  are another route by which a host classification decision, not a reader
  judgment, sets the result. The `dup_id` run shows the converse: a Swift-only
  rule changing the result.
- **DT-24** (`missing_reason` and `pid` meanings) is a neighbor of the `dup_id`
  step. That step carries `missing_reason: validator_no_verdict` and the error
  "no validator verdict for this step", while its phase retains two records:
  one byte-identical to the step ID and one canonically equal to it. The
  reason fits its definition ("produced no associated record"), because no
  record was uniquely associated. The error text does not distinguish an
  ambiguous association from absent output.
- **DT-25** found canonical target equality in Swift. Reading rule 4 adopts it
  and Python implements it with NFC. DT-50 and DT-131 concern record identity,
  where no rule states the relation and the readers diverge. The difference
  between the two is that one has a stated equality and the other does not.
- **DT-38 and DT-47** (support-scope findings) bear on DT-130. The Python
  order control `unestablished_despite_chain` establishes the consumer's
  behavior through a JSON fixture, a narrower path than the frame path
  executed here, and says nothing about Rust.
- **DT-101** bears on the DT-95 trace and DT-134 in two ways. Its finding
  limits the "Checked by the host decoder" list: the unit check asserts
  unavailability but no reasons, six of nine reasons occur in no test, and
  no case combines two failures. Separately, the Rust receipt-label test
  establishes the run outcome through typed injection, not frame decoding.
- **DT-49** (a diagnostic's `rc` versus `native_rc`) is a sibling of DT-48:
  both concern how the query projection forwards record values without
  re-deriving them from the native pair. DT-49's input is a diagnostic record;
  DT-48's is a prediction label.
- **DT-52 and DT-53** (consumer tolerance) are extended by DT-132 to a
  byte-consistent envelope. DT-52's missing-errno tolerance was not re-tested.
- **DT-57** (empty ID rejected only by the oracle) is another oracle-only
  judgment. Under DT-132's registry map, it is visible only in the cases that
  run the oracle.
- **DT-60** (a mismatched raw association still projected) concerns the same
  decoder as DT-61 and DT-133, where the decoder's checks against its arguments
  are its whole readiness check.
- **DT-96 and DT-97** (constant labels; nonce never in the compiled bytes)
  explain why the label check in DT-134 has little evidential content.
- **DT-108** (conditional-null projection) did not arise in these rows,
  because host-built queries always carry `result_source`. Rust's typed
  checks and Python's projected checks saw identical values on every seam
  row (`decode_bound` equality).

### Acceptance coverage and remaining investigative limits

- The Swift reporting validator, `decodeAuthoritySetup` and
  `authoritySetupIntegrityErrors` were not run on any edited frame. Their
  judgments of the f48, f61 and f95 edits are source reading.
- Every seam row carries a constructed `producer.contract` edit. The seam
  bypasses `reply_contract`. Its placeholder inputs (`preparation-0`, the
  writer-cap pair and `normal.pwp`) produced rows that were disregarded.
  Fidelity was checked only on the twelve unedited rebound rows.
- All non-native validator transcripts are steered. No claim is made that the
  shipped validator emits incoherent labels or rewrites Unicode spellings.
- The reader map is a static text search over command scripts and the files
  they name. It does not establish that each named check executes on every
  invocation, and no registered case was run. Their current pass status is not
  claimed.
- The reduction of the scheduler gate to `status == 1` for every launched
  required actor is source reading. No launch with a missing descriptor was
  attempted.
- The `actor` specimen is this pass's own. It was not coordinated with other
  passes and covers one required-authority configuration.
- No Swift package, mutated app or registered battery was built or run. The
  only build was the unmodified controller test binary in an isolated target.

## Additional investigation: interdependencies of import inventories and compiled-profile receipts

The investigator supplied the following report in `.tmp/82-103-OBSV.md`.
It is preserved here with only heading levels adjusted and source links
rebased for this directory; citation labels retain the submitted line
references. The executions and judgments below are the investigator's;
the experiments were not rerun during incorporation. The source report
and its named scratch artifacts are disposable local material.

### The outcome

The advance is modest. It's mostly a clearer account of how the five findings relate, plus one joint observation that hadn't been run before.

1. **Nothing observes the compiler's file inputs, and the two identities that come close share only one key.** The controller's literal walk names files, but it isn't the compilation. The worker's receipt comes from the compiling process, but it names no files. The source digest is the only value they have in common, and I found no reader that compares the two.
2. **Newly executed:** one ordinary `run` envelope can report the dossier as `complete` with no records beside a captured receipt whose checked fields are all correct. That receipt's bytes match a compilation that included the imported rule, and its applied policy refused the write that rule denies (R2/E2 below). The reverse case (R4/E4) reports `complete` with a record for a file whose rule was neither compiled nor enforced.
3. **DT-103 limits only the bytecode parts of the import findings.** Each import finding also has evidence that doesn't depend on the private 24-byte layout, and E2/E4 add such evidence for the worker's own compilation.
4. **DT-82 never appears beside a receipt in a `run` envelope.** In a run, the dossier keeps the signal the helper drops.

I changed no tracked files and built nothing.

---

#### 1. The five findings, within their evidence

|            | Where it arises                                                                                                                                                                                                                                                                                                   | What was observed                                                                                                                  | Evidence type                                                                       | Not observed                                                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **DT-82**  | The helper's projection. The lexer flags the computed argument and the resolver sets `nonliteral_imports`; `ImportInventory` drops it (DT-81).                                                                                                                                                                    | The helper inventory for computed import C has the same shape as import-free A. The compiler incorporated the import.              | Bytecode C = B ≠ A (host-side probe through the 24-byte view); M2 marker diagnostic | File opens; dossier (source and unit test only)                             |
| **DT-84**  | Lexer grammar. After the closing quote it requires `)` following only whitespace ([sbpl_lex.rs:192](../controller/src/sbpl_lex.rs)), and a miss returns `None` rather than `NonLiteral`.                                                                                                                         | L2 marker diagnostic from the helper's compile; empty inventory; the lexer probe reports `scan_complete: true`                     | Diagnostic only                                                                     | Dossier result (derived from source); worker compilation                    |
| **DT-85**  | Lexer collects literal names in every position. This is designed and tested.                                                                                                                                                                                                                                      | Od's bytes equal A's. O1 compiles although evaluating the marker would fail. Its record is present.                                | Bytecode (Od) and compile success (O1)                                              | Whether the compiler opened the file                                        |
| **DT-98**  | The receipt's identity covers the compile arguments: the C-string source ([pw_profile_capture.h:71](../controller/tools/pw_probe_runner/pw_profile_capture.h)) and the parameter snapshot. The host compares these with its supplied inputs ([CWorker.swift:706](../runner/Sources/PWRunnerCore/CWorker.swift)). | Across two separate runs the imported file changed: identity fields stayed equal, bytes differed, and the dossier closure changed. | Receipt fields                                                                      | A change within one run; the worker's file reads                            |
| **DT-103** | The capture reads the object through a 24-byte view, and the same pointer goes to `sandbox_apply`.                                                                                                                                                                                                                | Decoded bytes match the reported length and digest; repeat runs give the same bytes; different policies give different bytes.      | Consistency and repeatability                                                       | Whether the layout is correct; how the bytes relate to what apply submitted |

#### 2. What each identity in a run envelope covers

| Field                                                       | Bytes covered                                                     | Computed by, when                                                                              | What it is checked against                                                                                                     |
| ----------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `specimen.policy.augmentation.applied_sha256`               | Selected source string                                            | Controller, before delivery ([run_flow.rs:609](../controller/src/run_flow.rs))                | Nothing found                                                                                                                  |
| `specimen.policy.imports.{status, records, closure_sha256}` | Source plus each literal-walk file's bytes as read at that moment | Controller, before delivery (client call at [run_flow.rs:681](../controller/src/run_flow.rs)) | Nothing. The consumer checks shape only ([consumer.py:994](../tests/lib/consumer.py))                                         |
| `runner_result.policy_sha256`                               | Request source as the host parsed it                              | Host                                                                                           | Nothing found against the dossier                                                                                              |
| `compiled_profile.source_sha256` / `source_length`          | The C string passed to `sandbox_compile_string`                   | Worker, after compile and before apply                                                         | Host compares it with its supplied source. This is the only source association that is checked                                 |
| `params_sha256` / `parameter_count`                         | The parameter snapshot given to `sandbox_set_param`               | Worker                                                                                         | Host recomputes independently                                                                                                  |
| `bytecode_*`                                                | Bytes read through `view.bytecode` / `view.bytecode_length`       | Worker; host re-hashes                                                                         | Worker's own digest of the copied bytes                                                                                        |
| Imported bytes the worker's compiler consumed               | —                                                                 | Nobody                                                                                         | —                                                                                                                              |
| What `sandbox_apply` submitted                              | —                                                                 | Nobody                                                                                         | —                                                                                                                              |
| Helper `import_inventory` and verdict                       | Its own walk, then its own compile; no bytes published            | `sbpl-check`                                                                                   | In a run, present only when fallback is eligible, which means a client `xpc_error` (DT-116). Then there's no admitted receipt. |

The separation is documented:

- The policy surface says each digest belongs to its own read, and that "final equal hashes do not establish read ownership or simultaneity" ([11-policy.surface.md:565–577](../docs/contract/11-policy.surface.md)).
- The resolver header says neither walk "identifies what the worker's compiler read" ([sbpl_imports.rs:6](../controller/src/sbpl_imports.rs)).
- A code comment says `complete` "does not mean compiler-complete" ([dossier.rs:117](../controller/src/dossier.rs)).

The dossier walk always runs before delivery, so a window for a file to change exists by construction. Nothing exercised a change inside that window during one run, and DT-98's change between two runs doesn't show one.

#### 3. The new executed contrast

**Setup:**
- **Build:** `dist/PolicyWitness.app`, commit `8b5de2b2`; `codesign --verify --deep --strict` passed.
- **Correspondence:** HEAD is `263c06c8`. Since `8b5de2b2`, outside `records/`, only the deleted plan and one line of `build_refusals.py` changed.
- **Machine:** macOS 26.7.1 (25G241).
- **Execution:** direct `policy-witness run` probes under `tests/lib/checkout_lock.sh`, one run per case. These are not registered cases and have no sleep accounting.

**R (`joint-1`).** `inc.sb` holds `(deny file-write* (literal "/private/var/empty/pw-import-control"))` (`c313d21c…`). The base is `(version 1)\n(allow default)\n`, with capture and an empty probe plan.

| Case | Third line                                 | Dossier status / records / failure                                      | Closure covers source only? | Receipt bytes            |
| ---- | ------------------------------------------ | ----------------------------------------------------------------------- | --------------------------- | ------------------------ |
| R0   | none                                       | complete / 0 / null                                                     | yes                         | 492, `b2056ef2…97e0`     |
| R1   | `(import "<D>/inc.sb")`                    | complete / 1 / null                                                     | no                          | 548, `f7dbbaca…8718`     |
| R2   | `(import "<D>/inc.sb" ; note\n)`           | **complete / 0 / null**                                                 | yes                         | **548, `f7dbbaca…8718`** |
| R3   | `(import (string-append "<D>" "/inc.sb"))` | incomplete / 0 / "a nonliteral (import ...) form could not be followed" | yes                         | 548, `f7dbbaca…8718`     |
| R4   | `(if #f (import "<D>/inc.sb"))`            | **complete / 1 / null**                                                 | no                          | **492, `b2056ef2…97e0`** |

All five runs exited 0 with `finished` and a captured receipt. In every case these held under independent checks:

- The decoded length and SHA-256 match the receipt.
- The source digest equals the request source and `policy_sha256`.
- The source length matches.
- The parameter digest is the zero-parameter value.
- The worker PID and nonce match.

**E (`joint-2`).** `inc.sb` denies `file-write*` on `<E>/target`. Each run has one step: a `file-write-create` query and a file create on the target, which was removed before each run.

| Case                  | Dossier              | Receipt bytes        | Attempt                | Target after the run |
| --------------------- | -------------------- | -------------------- | ---------------------- | -------------------- |
| E2 (commented import) | complete / 0 records | 644, `8b16fceb…66a9` | `open_failed`, errno 1 | absent               |
| E4 (untaken import)   | complete / 1 record  | 492, `b2056ef2…97e0` | ok                     | present              |
| E1 (literal import)   | complete / 1 record  | 644, `8b16fceb…66a9` | `open_failed`, errno 1 | absent               |
| E0 (no import)        | complete / 0 records | 492, `b2056ef2…97e0` | ok                     | present              |

The query was `prediction_unavailable` in every case, because the target didn't exist when the query was planned. The enforcement evidence is therefore the attempt alone. Attributing the E1 and E2 refusals to the applied policy rests on the matched contrast: same path, parent, worker kind and build, with only the source text differing, and E0/E4 created the file. No kernel log or query observed the denial.

**What this adds:**
- DT-84's dossier consequence and its effect on the worker's compilation are now executed. Both were previously derived from source or observed only on the host side.
- E2 and E4 show that the worker's applied policy included or excluded the imported rule, without relying on the 24-byte view. They don't show that the captured bytes are what apply consumed. They show only that enforcement and capture sort the four cases into the same two groups.
- **Cross-observation:** R1–R3's bytes (548, `f7dbbaca…8718`) equal DT-98 run 1's bytes. DT-98 put `(allow default)` inside the imported file, at a different path, under a different source digest; the app build and OS were the same. So the bytes carry neither the import path nor the split between source and import, and the missing import identity can't be recovered from them. Put together with DT-98:
  - Identity doesn't determine the bytes. That is the coverage limit.
  - The bytes don't determine the identity. That is expected of compilation, not a defect.

#### 4. How the findings relate

**One finding supplies a premise for another**
- **DT-103 → the bytecode parts of DT-82 and DT-85, and DT-98's interpretation.** DT-82's C = B ≠ A and DT-85's Od = A came from `bytecode_digest.c`, which reads through the same view in a host process. DT-103 itself calls that agreement under the same reading rather than an independent decoding.
- **DT-103 is not a premise for the rest.** That covers M2 and L2 (diagnostics), O1 (compiles although evaluation would fail) and E2/E4 (enforcement). It also covers DT-98's field-level claim: equal identity fields beside different reported bytes is true however the view is read.
- **DT-85 → reading DT-98's closure change.** In DT-98 the dossier closure changed along with the bytes, which looks like confirmation. R4 shows the closure can cover a file the compiler never evaluated, so that co-variation doesn't establish an association by itself.

**Findings that share a mechanism**
- **DT-84 and DT-85** share the lexer's grammar: what it counts as an import form, independent of position or evaluation. Both reach the helper and the dossier identically (R2, R4).
- **DT-82 has a different mechanism.** The lexer handles computed arguments as designed and flags them; the loss is in the helper's projection. R3 shows the dossier keeps the flag.
- **DT-98 and DT-103** share `pw_capture_profile`, but in different parts: argument digests versus the object view.

**Different mechanisms leave the same question unanswered**
- The question is: which file bytes did this compilation consume?
  - The scanner answers which files a literal walk read. DT-82, DT-84 and DT-85 bound how far that can be from the compilation.
  - The receipt answers which arguments went in and which bytes came out (DT-98).
  - No component observes what the compiler opens.
- DT-103 leaves a different, adjacent question: what application consumed.

**Accurate statements whose combination invites a stronger inference**
- A dossier `complete` plus a captured receipt with a matching source digest invites "compiled from this source, these parameters and these files."
- R2 and R4 are executed counterexamples in which every field checks out.

#### 5. Your four questions

**1. If the literal inventory were complete, what would still be unknown about the worker's consumed inputs?** Assume "complete" means it matched the files the compiler evaluated. Still unknown:
- **Same bytes?** The walk is a separate, earlier read by the controller, so whether the compiler read the same bytes is unobserved.
- **Which directory?** For relative names, which search directory the compiler used. On this host, `BTLEServer.sb` exists in both directories. This contradicts the resolver comment's "no overlapping filenames," which it records as a macOS 14.8.3 observation. The two copies are byte-identical (`597f62bc…`), though, so no hash or bytecode contrast can expose the search order here.
- **The receipt.** It would still carry no import identity, and joining it to the inventory would still go across processes through a key no reader checks.
- **What application consumed** (DT-103).

**2. Can every reported digest be accurate while their apparent association stays unestablished?** Yes, executed in both directions:
- R2: every digest is accurate, and the compiled bytes include a file the closure omits.
- R4: every digest is accurate, and the closure covers a file the bytes exclude.
- DT-98 shows a consistent association that is still unchecked.

**3. Which uncertainty is missing information, and which is the meaning assigned to available information?**
- **Observed by no component:** the compiler's file reads; the layout and what apply submitted (DT-103). The form DT-84 misses isn't even known internally.
- **Observed but dropped:** DT-82. The helper's projection drops the flag; the dossier keeps it.
- **Meaning:**
  - DT-85's records are accurate as reads; the error is reading them as imports.
  - DT-87's guide sentence "a source with no imports is an empty list" assigns a meaning that R2 and R3 contradict.
  - DT-98's phrases "consumed input bytes" and "identifies compiler output" claim more coverage than the receipt has.
- **Judgment:** DT-84 is the only case where the dossier's own definition fails on a natural reading. `complete` "exhausted the literal closure without a reported problem" ([42-dossier.surface.md:229](../docs/contract/42-dossier.surface.md)), and R2's import has a string-literal argument. DT-82 (dossier says `incomplete`) and DT-85 (the walk did read those literal names) don't contradict that definition. Whether DT-84 does depends on whether "literal closure" means the compiler's syntax or the lexer's grammar.

**4. Does each finding remain meaningful when the others are set aside?** Yes, all five do:
- **DT-82** contradicts the subject statement whatever the compiler does. Its relevance to what was compiled is limited to the standalone helper and fallback captures, where the verdict comes from the helper's own compile and no bytes are published.
- **DT-84** stands alone as a scanner miss that leaves `complete`.
- **DT-85** alone is a bound that agrees with the statements. Its weight comes in combination.
- **DT-98 and DT-103** don't depend on the inventory findings.

#### 6. A possible narrower formulation

> In an ordinary run envelope, no field observes the compiled bytes' file inputs. The dossier identifies a literal walk made before delivery. The receipt identifies the compile's arguments and output. The only shared term is the source digest, which no reader compares.

**It clarifies:**
- why DT-84 and DT-85 matter to receipt readers;
- why completing the inventory wouldn't close DT-98;
- that no component holds the compiled file inputs.

**It risks hiding:**
- that DT-84 is a scanner miss against the dossier's own definition, while DT-85 is designed and stated behavior;
- that DT-82 is a helper-only projection gap that never meets a receipt;
- that DT-98 concerns the receipt's own statements;
- that DT-103 concerns layout and application, which is orthogonal to file inputs;
- that the separation is deliberate and documented.

#### 7. The arrangement (judgment, labeled)

**Observation.** The two identities come from different processes at different times. They share only the source digest, and the inventory side disclaims any association in three places (section 2).

**Judgment.** This isn't an unmet promise. The interpretive cost lies in where the disclaimers sit:
- The disclaimers are on the inventory side. The receipt's source owner pins "consumed input bytes" ([35-profile.surface.md:394](../docs/contract/35-profile.surface.md)), and the guide says "identifies compiler output" ([PolicyWitness.md:746](../docs/PolicyWitness.md)). Neither points at the inventory's limits.
- A reader asking what was compiled gets two partial identities side by side, and the one that names files is the less authoritative about compilation.
- R2 is the concrete cost: nothing in the envelope signals the divergence.

I found no stated reason for the receipt carrying no import identity beyond the statement that the inventory and the receipt have separate observation boundaries.

#### 8. What should stay distinct

- **Stages:** lexer grammar, helper projection, the walk's reads, compiler evaluation (seen only through diagnostics, bytes and enforcement), file opens (never observed), capture (bytes through the view) and application (enforcement contrast only).
- **Compilations:** host-side ones (helper, `bytecode_digest.c`) versus the worker's.
- **Changes over time:** a file change between runs (DT-98) versus the window within one run, which is established by source only.
- **Equality:** equal bytes don't mean the same files were opened.

#### Limits and files

- Single runs per case, no file-access tracing, and the query was unavailable in E.
- Run R4 shows its import wasn't evaluated, not that the file wasn't opened.
- The scripts and outputs are below. The scratchpad isn't durable, so the decisive values are in the tables above.

Files:
- Script for R: `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/8e36ddab-fa42-4f22-aaa7-9c8a136b8fe2/scratchpad/scripts/joint_import_receipt.py` (`f47f1f54…c7ca`)
- Script for E: `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/8e36ddab-fa42-4f22-aaa7-9c8a136b8fe2/scratchpad/scripts/joint_enforcement.py` (`f72fe9de…3593`)
- Output for R: `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/8e36ddab-fa42-4f22-aaa7-9c8a136b8fe2/scratchpad/joint-1`
- Output for E: `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/8e36ddab-fa42-4f22-aaa7-9c8a136b8fe2/scratchpad/joint-2`

## Follow-up investigation: boundaries of the shared import and receipt interpretation

The investigator supplied the following report in
`.tmp/SHARED-INTERP-FOLLOW-UP.md`. It is preserved here with only heading
levels adjusted and source links rebased; links to the preceding investigation
use its section anchor, and citation labels retain the submitted line
references. This follow-up qualifies that investigation; the earlier text
remains intact. The executions and judgments below are the investigator's;
the experiments were not rerun during incorporation. The source report
and its named scratch artifacts are disposable local material.

### Follow-up: where the shared interpretation holds

**Outcome: a modest clarification plus one small new contrast.**

- **The interpretation holds as a description of a documented separation.** No field links the dossier's file records to the compiled bytes, in all five cases.
- **Divergence is narrower than the earlier account implied.** It was observed only through the DT-84 and DT-85 mechanisms, and only by comparing with runs whose composition I knew. No single envelope shows it.
- **Several passages in the appended account need narrower wording.** I list them at the end.
- **The new contrast was one small run series.** I changed no tracked files and built nothing.

#### 1. The cases compared

**The source association is already established.** In every run these three digests were equal:
- `augmentation.applied_sha256`
- `runner_result.policy_sha256`
- `compiled_profile.source_sha256`

That equality holds by construction:
- The dossier is built from the resolved request value ([run_flow.rs:609](../controller/src/run_flow.rs)).
- The same value is serialized once into the string delivered to the runner (`:678`, `:681`).
- The host checks the worker's digest against what it received ([CWorker.swift:706](../runner/Sources/PWRunnerCore/CWorker.swift)).

So the earlier phrase "which no reader compares" pointed at the wrong weak spot. A missing comparison there would only confirm what the code already guarantees. One test also joins the receipt to the request source ([check_actor_compositions.py:132](../tests/suites/witness_contract/check_actor_compositions.py)). The association that remains unestablished is between the dossier's records and the compiled file inputs, and no field covers it.

**What the envelope leaves out.** It carries `specimen.request_path` and the digests, but not the source text. To see the import forms, or to recompute the closure hash, a reader needs the retained request. They can confirm it's the right file by checking it against `original_sha256`.

| Case                              | From the envelope alone                                                                                                       | Adding the request and prepared files                                                                                                                                                                       | Divergence                                                                                                                                                          |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R0/E0 (no import)                 | `complete`, no records; 492 bytes                                                                                             | No import form; E0 created the file                                                                                                                                                                         | Nothing to associate                                                                                                                                                |
| R1/E1 (literal import)            | `complete`, one record: path, hash `c313d21c…`, size, mtime, all from the walk before delivery. Nothing links it to the bytes | `inc.sb` was written once before the runs and its hash matches. Bytes differ from R0 and equal DT-98 run 1, which evaluates the same rules in the same order. E1 refused the target and created the sibling | **Not observed.** Possible by construction: the walk is a separate, earlier read of a file on a writable volume. Unsignaled, because nothing is known to be missing |
| R3 (computed import)              | `incomplete`, no records, "a nonliteral (import ...) form could not be followed"                                              | `string-append` evaluates by hand to `inc.sb`; bytes equal R1                                                                                                                                               | **Signaled** by the dossier, then confirmed by contrast                                                                                                             |
| R2/E2 (comment inside the import) | Same status, records and failure as R0                                                                                        | The import form is visible in the source; bytes equal R1; E2 refused                                                                                                                                        | **Observed only by contrast** with R0/R1/E0; not signaled                                                                                                           |
| R4/E4 (untaken import)            | Same status and records as R1                                                                                                 | `(if #f …)` is visible; bytes equal R0; E4 created the file                                                                                                                                                 | **Observed by contrast**, between the record and the compiled content. Compiler reads are not observed                                                              |

**What's left when no scanner miss is involved (R1, R3).** Two facts remain: the receipt names no files, and the walk is a separate, earlier read. Both are documented ([11-policy.surface.md:565–577](../docs/contract/11-policy.surface.md), [sbpl_imports.rs:6](../controller/src/sbpl_imports.rs), [dossier.rs:117](../controller/src/dossier.rs)). Together they leave an unverified association. No run with an ordinary literal import showed divergence. The two ways such a source could diverge weren't exercised:
- a file change within one run;
- which directory a relative name resolves to.

Section 4 bounds both.

**The guide's own route for consumers.** It says consumers "compare actual decoded bytecode with any independently retained expected object" ([PolicyWitness.md:756–758](../docs/PolicyWitness.md)). My contrasts caught R2 and R4 only because I knew what the baselines contained (R0 has no import, R1 has a literal one) independently of the inventory. An expected object made by compiling the same source on the same host would match R2's bytes and wouldn't reveal the missed import. That last point is reasoning; I didn't run it.

**Where the formulation needs narrowing.**
- Its first three sentences hold in every case.
- The fourth should say the source association holds by construction.
- Any claim that the separation leaves divergence unsignaled should name DT-84 and DT-85 as the only observed sources.

#### 2. The two directions of the identity argument

**Identity doesn't determine the bytes (DT-98).**
- **Equal across both runs:**
  - `source_sha256` `37dbde4d…0791`
  - `source_length` 155
  - `params_sha256` `df3f6198…1119`
  - `parameter_count` 0
  - `profile_type` 0

  `worker_pid` and `request_nonce` identify the run, not the inputs.
- **Fixed:** the build, the OS, the source text including the absolute import path, and the absence of parameters.
- **Changed:** the imported file's content, rewritten between two separate runs.
- **Result:** the bytes went from 492 `b2056ef2…97e0` to 548 `f7dbbaca…8718`, and the dossier closure changed.
- **Supported:** for a source with an import, these fields don't determine the bytes; the imported content matters too. This rests on one absolute import, changed between runs. It says nothing about a change within one run.

**Bytes don't determine the identity.**
- **Four arrangements produced 548 `f7dbbaca…8718`:**
  - R1, R2 and R3: the source holds `(version 1)` and `(allow default)` and imports `joint-1/inc.sb`, which holds only the deny rule. There are three spellings, with three different source digests.
  - DT-98 run 1: the source is `(version 1)` plus an import of `<probe3>/inc.sb`, which holds both `(allow default)` and the deny rule.
- **What all four share:** the same rules, evaluated in the same order: `(version 1)`, `(allow default)`, `(deny file-write* (literal "/private/var/empty/pw-import-control"))`.
- **What differs:** the source text, digest and length; the import directory; the spelling; and which file holds `(allow default)`.
- **The same pattern at 492 `b2056ef2…97e0`:** R0, R4, E0 and E4 in both E series, and DT-98 run 0.
- **Supported:** on this build and OS, arrangements that evaluate the same rules in the same order gave identical bytes, as read through the capture view. For these arrangements the bytes carry nothing about the import path, spelling or split, so the import identity can't be recovered from them.

**Not supported: that compiled bytes never carry import-path information.** The new run is a counter-observation:
- The `joint-2` and `joint-3` series differ only in that directory name. The name appears in the import argument and in the imported rule's literal path.
- Their 644-byte outputs differ: `8b16fceb…66a9` versus `0861b817…dbd7`.
- R1 = DT-98 run 1 shows that changing the import directory (and the split) left the bytes unchanged when the rule literal stayed the same. So the change is attributable to the one-character change in the rule's literal, which is a path inside the import's own directory.

The bytes therefore carry path text that rules supply. One more observation I don't rely on: the R1 and E literals differ in length by 96 (36 versus 132), exactly the difference between 548 and 644. I didn't decode anything. Other ways location could enter the bytes are untested. All the equalities here are of what the private 24-byte view reads (DT-103).

#### 3. How strong the application inference is

**The new contrast (`joint-3`)** repeats the E series with a second step that creates `other`, a sibling in the same directory that no rule names. Runs alternated between deny and allow in the order E2, E4, E1, E0.

| Case | Bytes               | Create `target`        | Create `other` | After the run (target / other) |
| ---- | ------------------- | ---------------------- | -------------- | ------------------------------ |
| E2   | 644 `0861b817…dbd7` | `open_failed`, errno 1 | ok             | absent / present               |
| E4   | 492 `b2056ef2…97e0` | ok                     | ok             | present / present              |
| E1   | 644 `0861b817…dbd7` | `open_failed`, errno 1 | ok             | absent / present               |
| E0   | 492 `b2056ef2…97e0` | ok                     | ok             | present / present              |

In every run:
- exit 0, `finished`, `sandboxed_after_apply: true`;
- receipt captured, and the length, digest, source and nonce checks all held.

The queries were again `prediction_unavailable`. The product's comparison reads `permission_failure`, `operation_relation: unresolved`, `order: unestablished`, and it makes no claim about cause. The attribution below is mine.

**What the matched observations support, across the two series:**
- After application, the worker's policy refused to create exactly the path named by `inc.sb`'s rule. In the same run it allowed creating a sibling in the same directory. This happened only in the runs whose bytes match an evaluated import (E1, E2).
- The refusal follows compiler evaluation, not the dossier. E4 recorded the file but allowed the write; E2 recorded nothing but refused it. So the controller's walk didn't cause the difference.
- Several things were held fixed: the build, the worker kind, the parent directory, the step shape, and removing the targets before each run.
- Alternating the order rules out drifting conditions.
- The sibling rules out a refusal of all creation in the directory, or a broken worker.

**Conclusion:** the imported rule's effect, a refusal confined to its literal path, was in force in E1 and E2 and absent in E4. The contrast supplies that; the lack of a kernel log doesn't take it away.

**What it doesn't support:**
- **How the compiler got the file.** The rule could only have come from `inc.sb`, since nothing else names that path. But how and when the compiler obtained it, and which version of the file, is unobserved.
- **Which bytes application consumed.** Capture and enforcement sort the cases the same way, and between `joint-2` and `joint-3` both followed the changed literal. That is co-variation, not evidence that apply submitted the captured bytes (DT-103). The guide itself says none of this is "a readback of the kernel's effective policy" ([PolicyWitness.md:746–748](../docs/PolicyWitness.md)).
- **The mechanism in kernel terms:** there's no log and no query result.
- **Breadth:** one operation, one deny form, one pair of paths, and one run per case in each series.

#### 4. Scope across time and paths

**`BTLEServer.sb`.** The resolver comment is explicitly scoped: "Verified empirically on macOS 14.8.3 build 23J220". It says the search order "could not be confirmed by collision on this host (no overlapping filenames)" ([sbpl_imports.rs:15–24](../controller/src/sbpl_imports.rs)).

On this host (26.7.1, 25G241), `BTLEServer.sb` is the only name present in both directories, which hold 59 and 511 entries. But the two paths are a single file, on the sealed system snapshot:
- same device (16777233) and inode (1152921500312489006);
- link count 2;
- 3398 bytes.

What follows:
- **A changed condition, not a contradiction.** Nothing here observed 14.8.3. My earlier "contradicts" ([review:8509](#additional-investigation-interdependencies-of-import-inventories-and-compiled-profile-receipts)) was too strong, and "byte-identical" understated a hard link.
- **The comment's conclusion still holds here.** One file under two names offers no real collision, so no hash, bytecode or enforcement contrast can reveal the search order. Only a trace of which directory entry the compiler looked up could. Its consequence would be limited to the path string: the dossier's `resolved_path` names the Profiles entry either way.
- **The contract already carries this limit.** It calls the directory order "a platform convention" ([11-policy.surface.md:585](../docs/contract/11-policy.surface.md)) and says the search-order observations are "inherited from the source comments, not reproduced here" (`:603`).
- **Related narrowing, inferred from the mount (I didn't test writes).** Both search directories are on the read-only snapshot, so files found there can't change between the walk and the compile within one boot. The window within a run ([review:8436](#additional-investigation-interdependencies-of-import-inventories-and-compiled-profile-receipts), `:8508`) matters for imports outside that snapshot, such as the writable-volume absolute paths used in every run here.

**"DT-82 never appears beside a receipt."** What I examined:
- **Callers.** The single-policy fallback ([run_flow.rs:360](../controller/src/run_flow.rs)) and the actor-form fallback (`:374`), each called on the admitted branch (`:699–701`) and the refused branch (`:715–724`).
- **Eligibility.** [runner_client.rs:651–661](../controller/src/runner_client.rs) requires terminal `xpc_error`. DT-116 established that this always leads to the refused branch with a null `runner_result`.
- **Fields.** `data.policy_check…import_inventory` and `data.actor_policy_checks[]`.

Within that scope, the statement holds for both forms. I didn't examine external (BYOXPC) runners separately; they share the client record.

Outside that scope:
- **The guide's direct workflow.** It documents running `sbpl-check --request` on the same saved request a run uses ([PolicyWitness.md:768–772](../docs/PolicyWitness.md)). That puts the helper's projection beside a receipt in the reader's hands, though not in one envelope. For a computed import, the helper shows the no-import shape while the receipt's bytes include the import.
- **A fallback envelope.** It also contains the dossier, so DT-82 does sit beside an inventory there, and the two would disagree for a computed import. This comes from reading the source; I didn't execute it.

#### Passages in the appended account that need narrower wording

| Review line | As written                                        | Narrower reading supported                                                                                                                                           |
| ----------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 8397, 8535  | Source digest shared, "which no reader compares"  | The source join holds by construction. Nothing joins records to compiled inputs                                                                                      |
| 8398, 8556  | R2 as the concrete cost                           | Holds. Observed divergence comes only from DT-84/DT-85; ordinary literal imports give an unverified association                                                      |
| 8477        | E2/E4 show the imported rule included or excluded | Supported, and now shown to be confined to the rule's path. It's still a matched-contrast inference and says nothing about which bytes apply consumed                |
| 8478        | Bytes carry neither the import path nor the split | True only for arrangements that evaluate the same rules in the same order. Bytes do carry rule-supplied paths                                                        |
| 8436, 8508  | Separate, earlier read                            | Matters for imports outside the sealed system snapshot                                                                                                               |
| 8509        | Contradicts the 14.8.3 comment                    | A changed condition. One file under two names, and the comment's conclusion still holds                                                                              |
| 8400, 8528  | DT-82 never appears beside a receipt              | Holds for `run` envelopes in the examined callers. The guide's direct workflow pairs them outside an envelope, and a fallback envelope puts DT-82 beside the dossier |

#### Distinctions that still matter

- **Four statuses:**
  - documented separation, which is always present;
  - unverified association, whenever there are imports;
  - observed divergence, only for DT-84 and DT-85 and only by contrast;
  - signaled incompleteness, as in R3.
- **Source join versus file join:** the source join holds by construction; for the file join no field exists.
- **"Same rules, same order, same bytes"** versus "bytes never carry path information".
- **Three different claims:** a rule's effect on one path (supported); file opens (unobserved); which bytes application consumed (unobserved).
- **Changed OS conditions versus contradiction**, and one file under two names versus two files.
- **Appearing together in one envelope** versus a reader putting two outputs side by side.

#### Evidence for the new contrast

- **Run conditions:** build `8b5de2b2` with `codesign --verify --deep --strict` passing; macOS 26.7.1 (25G241); run under the checkout lock.
- **Limits:** one run per case; these are not registered cases.
- **Reuse:** the `joint-1` and `joint-2` outputs were reused unchanged.
- **New `inc.sb`:** `e2a3448b…`.
- **Files** (the scratchpad isn't durable, so the decisive values are in the tables above):
  - Script (`2bd4427e…832b`): `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/8e36ddab-fa42-4f22-aaa7-9c8a136b8fe2/scratchpad/scripts/joint_enforcement_paths.py`
  - Output: `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/8e36ddab-fa42-4f22-aaa7-9c8a136b8fe2/scratchpad/joint-3`
