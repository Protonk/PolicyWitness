# Pass 5, round 1 reconciliation

Review revision: `5124b4309b6f7b0041c55318312a9ee18f579868`.
The three first-review prompts were committed in `abb2e2d`. Reviewers started
without conversation history, the work plan, or one another's reports. The
implementation reviewer preserved its source-derived initial account before
opening the tour and map. `first-reports.json` records byte hashes of all four
immutable reports. Later probe work is a focused reproduction phase of this
round, not another review round or the pass 6 audit.

The coordinator compared each finding with source and the current register.
Reviewer agreement was not counted as behavioral evidence. Probes were assigned
only after first reports were frozen; their prepared code was reviewed before
serial execution through the public dispatcher. Production code, WORKER.md and
the capability manifest were left unchanged. New cases are opt-in
characterizations: a passing counterexample case means the stated limitation
was observed, not that containment or complete verification passed.

## Finding disposition

| First-report item | Register destination | Coordinator assessment |
| --- | --- | --- |
| Implementation I1: same-group survivor after leader exit/EOF | Reopen 10 | Source predicts the omitted normal-completion path. A fresh public CLI probe confirms it; group escape is unnecessary. |
| Tests T2: requested-source/argc oracle | Reopen 19, endpoint subfinding | Original native receipts remain valid at their scope. The old oracle accepts both wrong direction and wrong argument; supplemental native mode/argv observations establish the mistakes. |
| Tests T3: base-only map accounting | Reopen 19, mapping subfinding | Production uses the complete extent today. The partial-unmap variant leaves a natively observed suffix while the old counter reports zero; this tests the oracle, not a claimed production leak. |
| Tests worksheet: per-attempt harness source comment | Reopen 22 | The comment repeats the overclaim already corrected in the guide/README. A bounded descriptor ceiling permits limited retention. Source/assertion review suffices. |
| Claims C1: irrelevant check/owner citations | New 25 | The missing optional paths and wrong owners are concrete. Selected-relationship scope does not make a disabled path a supporting check. No new runtime execution needed to establish this mismatch. |
| Claims C2: exec stdio collision | New 26 | Different boundary from row 23's host collision. Its own unchanged-worker probe confirms child stderr EBADF in the controlled launch; ordinary XPC starting state remains unestablished. |
| Claims C3: compiler-output period | New 27 | The plan ends “before compilation” at call entry; returned compiler outputs need another label. No private allocation timing is measured. |
| Tests T1: ordinary extension-test exceptional cleanup | New 28 | Unconditional directory removal after capture exceptions is source-supported. A live surviving worker on that failure path was not exercised; that consequence remains unobserved. |

Rows 23–24 remain awaiting adjudication. No new finding is auto-adjudicated and
no row closes in this round. Reopening 19 does not erase its historical 22 setup
observations or ten rejected receipt controls; it identifies what those controls
can miss. Reopening 22 preserves the valid guide/README corrections and isolates
the remaining test comment.

## Coverage that survived challenge

The reviewers traced native call/return versus slot publication, incomplete-slot
decoding, ordinary file-open returns versus discarded later returns, host versus
worker token erasure, private API ownership, and bounded inherited-state
observations. They found the authored qualifications generally consistent with
source and the examined assertions. This is scoped review support, not fresh
execution of every cited test or a complete native-resource census.

The claims review found bad citations in the graph while the implementation
review accepted its broad resource families. These findings are compatible:
resource existence and the correctness of a supporting test citation are
separate questions. The source-first review also corrected its own initial
statement about compiled-profile lifetime; no explicit PW free does not settle
private `sandbox_apply` ownership. Both versions remain preserved.

The test worksheet's fresh-read replacement-after-success idea remains a
coverage opportunity. Current source opens on each action; the reviewer did not
find an implementation cache or a tour assertion that the existing repeated-read
case distinguishes one. It therefore does not become a new product-defect row.
A future stronger freshness control can use that proposed counterexample.

## Focused execution

Fresh executions and exact run IDs, inputs, source snapshots, outcomes and
cleanup are recorded in the associated plan's pass 5 ledger. Raw evidence lives
under `tests/out/runs/` and is gitignored/local; `tests/RETAINED.json` protects
those runs. Copied inputs, supplemental observations and unmodified oracle
outputs are retained separately. No historical run is rewritten.

The lifecycle probe pairs the combined case with both existing neighboring
cases. Its observer requires the descendant's stable process identity, a live
socket response and unchanged group after the CLI finishes, then requires exit
following fixture release. The same observer rejects that released child.

The setup probe preserves the old recipe/checker and runs its entire case set
for an observer-augmented baseline and each disposable wrong-host variant.
Supplemental child access modes/argv and native mapping-suffix observations are
separate from the old checker's verdict. Observer additions and source mutations
are anchored, hashed and retained. The old pass 4 run remains the unaugmented
baseline; no observer-neutrality claim is inferred from identical pass counts.

The closed-stderr probe uses the signed worker unchanged. Only its launch
adapter changes fd 2; observations before worker entry must preserve protocol
endpoints. Independent child descriptor/write facts and captured worker payload
must agree. The selected starting state is not attributed to ordinary XPC hosts.

The implementation reviewer subsequently checked the coordinator's register
mapping with access to the plan and sibling reports. It found no lost material
finding or substantive scope overstatement; its table-format correction was
applied. This was reconciliation after independent reports, not another blind
review or a substitute for the recorded probes.

The corrected setup run passed after the original mincore absence assumption
failed. Exact Mach VM range scans distinguish the full-unmap baseline from the
partially unmapped variant and confirm later fixture cleanup. Both runs are
retained. This probe correction is part of the result: adding an observer does
not make its interpretation trustworthy without a control that can refute it.

This round therefore added two native runtime counterexamples and demonstrated
three setup-oracle blind spots, alongside source-established documentation and
test-cleanup findings. The native publication account survived the scoped review;
that is a useful result, but not a reason to close unrelated counterexamples.
No subsequent review round, fix or pass 6 audit was performed.
