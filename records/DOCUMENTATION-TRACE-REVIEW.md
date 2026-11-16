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
