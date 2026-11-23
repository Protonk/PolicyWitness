# Decisions behind the 0.3.8 trace and guide

November 23, 2026 · Source reviewed through `2bc70a43` · Writer's handoff. After reading the guide, the maintainer will decide on a separate trace review. Release acceptance belongs to the tagged build.

## Changes a maintainer could accidentally undo

The DT identifiers identify findings in the trace dispositions. The commits identify the implementations and their controls. Each row names the boundary that determined the decision.

| Remedy and findings | Decision, evidence and continuing limit |
| --- | --- |
| R1 · DT-55/56 · `0cbdb557` | Preserve embedded NUL and decode all retained exec bytes. The stream observer counts received and retained bytes and flags truncation and exactness. The exec-reader controls distinguish marker text, invalid sequences and scalar-boundary cuts. Recovering arbitrary binary bytes would need a different public representation. |
| R2 · DT-74 · `321bb6c5` | Registry loading treats absence as empty and refuses inspection errors, including a dangling symlink. The loader and recovery controls distinguish the two. Reconcile remains report-only because removing an owned service requires the durable record and an absence check. |
| R3 · DT-08/88–94 · `a4d49249` | Refuse an incomplete traversal when deriving build or worker identity. The source enumerator and literal-tree digest controls cover selected on-disk inputs including eligible untracked files. Equal digests leave the compiler, SDK and signer outside the comparison. |
| R4 · DT-23/51 · `feeeaf7b` | Apply the same validator-failure classification to declared-unapplied and applied actors. Removing the broad prefix filter also exposes failed pipe setup and query serialization. The independent consumer checks a necessary condition for `finished`. It cannot establish every part of lifecycle honesty. |
| R5 · DT-22/57 · `2cc7e32f` | Associate a valid validator record with the unique empty-ID ordinary step. The live empty/nonempty pair and actor-form refusal distinguish receiver behavior from admission. |
| R6 · DT-28 · `5906c0ac` | Report an unwritable stdout with exit 2 and a stderr diagnostic. A failed publication can follow a successful machine change. The command's checked write cannot provide downstream delivery confirmation. |
| R7 · DT-34 · `113e1e49` | Refuse a conflicting `XPC_SERVICE_PATH` before changing the machine. The installer knows the canonical bundle location it will own. The final BYOXPC opt-ins checked install and recovery with empty registry/reconcile before and after. |
| R8 · DT-108/110 · `7b2b030b` | Reject a wire dependent whose guard is missing in both readers. Retain the refused bytes. Generator and malformed-frame controls keep the readers aligned. The schema fingerprint identifies declarations and does not adjudicate compatibility. Keep public-JSON path compaction separate from wire encoding. |
| R9 · DT-25/50/131 · `cb00a2bd` | Associate validator identifiers and query metadata by UTF-8 bytes across readers. Keep canonical-equivalence rules for uniqueness and submitted target relation. Controls deliberately distinguish equal-looking spellings at these two boundaries. |
| R10/R11 · DT-31/32/42/113–119 · `1bba0e37`, `b3c89046` | Remove the inapplicable flat helper call on actor requests and unreachable fallback calls on an admitted reply. Retain per-actor captures because users lack the resolved actor policy text in the envelope. Host loss can coexist with actual worker effects. Read the client submission separately. |
| R12 · DT-29/81–85 · `227e5fc2` | Flag import forms the helper saw and could not follow. Keep a hash when scanning the file succeeded but a form inside it caused an error. The lexer controls and compiler contrasts establish that textual discovery and compiler evaluation answer different questions. The followed-set trials used the compiler on macOS 25G241. |
| R13 · DT-46/120/121/129 · `a887c986` | Derive `cleanup_trigger` at final collection. Three actor scheduler stop reasons map to completion. Inspect kill/reap facts independently. Timeout and failed setup can still yield unknown cause. A new cause for allowance-expiry kills would need an actual actor-timeout observation. |
| R14 · DT-01/02 · `fc4586fc` | Refuse nested generated regions and regions in unmapped documents. Coverage checks inspect anchors on disk. Two unsupported link-rebasing spellings retain documented limits. |

The receipt host binds the worker's capture to the application. A returned apply failure can satisfy completion while leaving the application guard unsatisfied. The trace had no observed real apply failure to justify copying bytes there. Controller receipt admission checks labels. A second comparison within the product would establish internal consistency. A detached receipt still needs an independently retained nonce. In three signed captures a reused nonce matched two requests. [Receipt semantics](../docs/RESPONSE.md#read-compiled-profile-receipts)

For extensions, the native issuer's oversized return is inspected over a bounded prefix. Last-use clearing has no public observer, and accepted host custody can have no public carrier after an unpublished issue slot. The trace narrowed the credited claims. A design that promises more would need the observation at the point of custody or clearing. Two fresh reads and recipient reversal can test access independently of those internal events. [Extension semantics](../docs/EXTENSIONS.md)

## Test interfaces and the evidence they earn

Eight controls now enter through `test-input run`. The ordinary worker and actor-equipment substitution fields remain available for their documented purposes. The migration compared old and new behavior. An argv string cannot carry NUL, the combined oversized pair has direct-orchestrator coverage, and the client capture does not identify the selected XPC method. Six earlier comparisons had a recorded exception for an unrelated edit to a test file. Repeating those comparisons requires rebuilding their revisions after the November 18 prune. [Control delivery](../controller/README.md#cli-surface-contract)

The descendant observation still enforces the product's account of signals and the later fixture effect. The retirement observation enforces the sequence, sample validity and owned cleanup. The pilot keeps its comparison advisory and reports when no candidate was compared. The converted inline assertions must record a case failure on a bad envelope. Three pytest family item counts appear in the final reread. An item's failure before launching its recorded command can leave accounting incomplete. Use the complete outcome counts when judging a battery. The accepted pytest work bounds archive reads and shares stored bytes within each family. Per-item source observations continue. [Harness outcomes](../tests/README.md) · [Pytest evidence plan](../tests/PYTEST-EVIDENCE-PLAN.md)

## Guide and publication decisions

The guide ledger's entries 1–5 cover the two narrowed promises, two groups of test assertions, and the request-file digest. Decisions 6–14 concern the behavior as shipped. Take a distinct admission-only operation forward after 0.3.8. It protects an actual effect and matched all 121 saved CLI refusals in the disposable comparison. A production host transaction, external runner restart costs, and a public result still need design. Keep the host path observation because it can resolve an exec operand when the worker has no descriptor path. An interrupted create can still have an indistinguishable later lookup.

Keep the integer return with its source and lifecycle, the required query/attempt pair, the present phase interface, prefix sampling, the existing open operations, and standalone compilation with explicit source scope. The bounded caller-checkpoint trial exposed the cost of adding a second observer to the schedule. The open-only and footer trials exposed genuine differences in what the operations do. For the CLI terminator, teach direct paths today. A later diagnostic can identify ignored suffixes without authorizing a previously ignored execution. Offline `compare` has its own post-0.3.8 plan. [Draft guide](../docs/guide/PolicyWitness.md)

| Closeout items | Owner, decision and missing evidence |
| --- | --- |
| 1–2. Stale opt-in build guard and how it was missed | `preflight/build_guard_controls` still seeds a previous guide with arbitrary bytes. The isolated staging check refused those bytes and accepted the frozen guide. Repair the fixture and run **that** case for success and signer-refusal partial output. The writer recommends including that named opt-in when a change reaches its freeze or staging fixture. The much larger `build_refusal_controls` run exercises a different case. |
| 3–4. Rehearsal and controls with fresh source | Retain the documented distinction between report-mode `make notarize` and strict `make release`. Four strict-release controls construct their own publication-fresh source (`11e93191`). Revisit that fixture helper when publication resumes. [Signing](../docs/SIGNING.md#release-procedure) |
| 5. Previous receipt beside partial assembly | Isolated staging left an earlier `publication.json` byte-identical after refusal. Full assembly also removes earlier deliverables. Run a real failed assembly with a previous receipt before deciding which receipt should survive. Owners are `build.sh` and `docs/generate_limits.py`. This question and the stale opt-in fixture have separate acceptance checks. |
| 6–7. Receipt references and the limits Control column | Use RESPONSE as the receipt definition when publishing the new guide. Revisit ARCHITECTURE/LIMITS navigation and whether the shared reading rule should name test controls at publication. Four affected rows already name their flags. [Receipts](../docs/RESPONSE.md#read-compiled-profile-receipts) · [Limits](../docs/LIMITS.md) |
| 8–13. Frozen copies | Check the new guide against the eight migrated controls, derived cleanup trigger, null actor top-level fallback, incomplete import inventories including hashed errors, canonical install path, and shared limits/extensions/failure-status regions. Regenerate any published copies from their owners when the freeze is lifted. The old distribution guide still belongs to its frozen baseline. |

## Items found outside the trace

| Owner | Open finding |
| --- | --- |
| Controller `runner validate` | Executable inspection still classifies inaccessible as missing. The technical account states this. Distinguishing an inspection error needs an explicit behavior decision and control. |
| `docs/build.json` | The addendum questioned the inventory of derivation refusals beyond R3. Scope and missing rows remain unassessed. |
| `tests/lib/native_sources.py`, `fixture_inputs.py`, `receipts.py` | The addendum identified discarded listing errors. Which incomplete traversals affect evidence, and how to surface them, remain unassessed. |
| Independent consumer | Its order condition also requires `arrival_observed`. Its actor fallback reader now checks `unfollowed_imports`. Sufficiency of either check remains unassessed. |
| `PWRunnerPathEvidence.swift` | The trace found no reader for `formNames`. Removing it changes a build input. A cleanup decision remains open. |

The loader's documentation entry list and the returned spelling of `sandbox_check.operation` were already handled in the technical accounts and R9. None of the unassessed items above carries a new release requirement. The checkout-local final runs and the four reviewed technical-account passes supply the original evidence classifications. The closeout plan locates the original packet if the maintainer requests a separate review.
