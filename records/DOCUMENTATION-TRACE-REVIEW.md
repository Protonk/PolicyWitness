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
