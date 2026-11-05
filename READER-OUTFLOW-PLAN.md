# Documentation lookback: decisions and follow-up

Status: C1–C6 resolved and acceptance refreshed; paused for the user's pre-retirement review. The lookback includes I1, a production host-admission diagnostic correction, as well as documentation and test changes; build 1121 carries that behavior and its regenerated worker identity. The critique follow-up makes no further production behavior change. F1 remains the sole accepted deferral. No retirement or pruning has occurred. This is the single outflow of [DOC-LOOKBACK-PLAN](docs/DOC-LOOKBACK-PLAN.md).

The [critique resolution](records/doc-lookback-2026-11-04/critique/RESOLUTION.md) and [closing identity](records/doc-lookback-2026-11-04/critique/final-state.json) are the current acceptance handoff. A fresh default battery passed all 216 cases against build 1121, followed by four supplemental passes. The first full run's static owner-registration failure is retained; its correction did not weaken an assertion. Across the seven required limit-change suites, 89 of 90 cases now pass on the final inputs; the remaining case is explicitly deferred F1. Both passing run trees and the preceding failure are preserved in the [current evidence manifest](records/doc-lookback-2026-11-04/critique/current-evidence/manifest.json). The [historical evidence report](records/doc-lookback-2026-11-04/critique/evidence-report.md) and [manifest](records/doc-lookback-2026-11-04/critique/historical-evidence/manifest.json) preserve earlier credited observations with explicit omissions and provenance limits. No pin was replaced.

The [earlier acceptance record](records/doc-lookback-2026-11-04/ACCEPTANCE.md) remains an unchanged historical checkpoint. It records the original completed actions and reading evidence; the critique resolution qualifies and supplements it. The plans, records, reader artifacts and managed test evidence remain in place. Prior work is committed as `f25c18ed`; critique follow-up changes and new records are pending commit.

The signed build passed and the first coordinated selection completed all 83 cases: 82 passed and the setup sensitivity control failed. Subsequent authorized runs retained both passes and failures. Additive fixture diagnostics passed both setup controls in run 05; the final two authorized focused runs, 06 and 07, both reproduced missing observer receipts alongside exhausted waits, a successful SIGKILL request and signal-9 reap. The user authorized deferring further investigation on recurrence. That deferral is applied; the completed repair-verification tranche does not claim a wholly passing battery. No further F1 runs were performed during documentation validation or final reading.

The [documentation checkpoint](records/doc-lookback-2026-11-04/documentation/PRETEST-CHECKPOINT.md) records candidate preparation and generation. The earlier [documentation handoff](records/doc-lookback-2026-11-04/implementation/READY-FOR-DOCUMENTATION.md) records final fixture observations and the accepted deferral. The [diagnostic observation](records/doc-lookback-2026-11-04/implementation/DIAGNOSTIC-OBSERVATION.md) records the two-file fixture change and passing validation; the [flakiness characterization](records/doc-lookback-2026-11-04/implementation/FLAKINESS-CHARACTERIZATION.md) preserves the preceding four-run comparison. The [focused rerun checkpoint](records/doc-lookback-2026-11-04/implementation/VERIFICATION-02.md) preserves the second failure; the [first verification checkpoint](records/doc-lookback-2026-11-04/implementation/VERIFICATION-01.md) records the build and direct repair passes. The original ten files in the [pre-build checkpoint](records/doc-lookback-2026-11-04/implementation/PREBUILD-CHECKPOINT.md) remain unchanged; the two added fixture changes also match their tested snapshot. Twenty-three specialists completed the original stages and three completed the critique follow-up, for 26 total; all are finished. Distribution build 1121 contains the prepared implementation and passes fresh signature and unchanged-artifact checks. The standalone distribution guide now matches the revised source through its owning staging tool; the signed app and ZIP were not rebuilt. The original Swift diagnostic-bound assertions and the new Rust checks pass in the fresh default run.

The [documentation rerun](records/doc-lookback-2026-11-04/documentation/VERIFICATION-02.md) passed `source_drift/architecture_documentation`, `source_drift/limits_documentation` and `source_drift/generator_contract`, all completed with zero recorded sleep. It validates the two corrected citation passages without changing the baseline or test. The [preceding run](records/doc-lookback-2026-11-04/documentation/VERIFICATION-01.md) remains three pass / one fail historically; its 525/525 Swift tests and three downstream reader replays retain their credit. The [applicability review](records/doc-lookback-2026-11-04/documentation/EVIDENCE-APPLICABILITY.md) distinguishes retained I1–I3 observations from fresh checks and records the manifest-input exceptions. The [final reader review](records/doc-lookback-2026-11-04/final-readers/FINAL-REVIEW.md) and [reader closing identity](records/doc-lookback-2026-11-04/final-readers/final-state.json) preserve the pre-decision checkpoint. The [final verification](records/doc-lookback-2026-11-04/acceptance/verification-03.json) adds two fresh passes after R1, with no skipped/unrun cases or recorded sleep, and pins the accepted source state. The reviewed artifacts remain unchanged; the [R1 delta](records/doc-lookback-2026-11-04/acceptance/r1.patch) identifies the ARCHITECTURE change after reading. The critique resolution separately identifies the later LIMITS corrections and their source-review/test basis.


## Resolved critique items

User authorization: resolve the proposed follow-up with sub-agents; tests and
corrective reruns need no intermediate pause. Return before retirement.

| Item | Resolution | Status |
| --- | --- | --- |
| C1 — refusal names | Audited all 30 admission rows against emission sites; literal fields and defined indexed templates now distinguish separate location fields and meaning-refusal paths. | Resolved; source audit plus passing generator controls |
| C2 — parallel-run guide | Replaced the fixed four-process account with form-dependent workers and helper lifetimes; regenerated and staged the standalone guide through its owner. | Resolved; source and staged guide identical |
| C3/C4 — verification selection | Full default battery on unchanged build 1121: 216 passes, including integration and all eight source_drift cases; four additional required controls pass. F1 remains the explicit fifth nondefault exception. | Resolved; 89/90 required-suite cases pass, one accepted deferral |
| C5 — Rust parity | Added independent diagnostic-path value ownership, literal depth/UTF-8 boundaries and serialization checks in Rust; production constructor unchanged. | Resolved; Rust unit case and ownership checks pass |
| C6 — durable evidence | Copied identified raw evidence/provenance and current passing run trees into records, verified bytes, retained failures and explicit historical omissions. | Resolved; no pin changes or pruning |

The user-approved crosswalk/inventory approach remains unchanged. Coordinator
owns manifest integration, generation, staged-guide freshness, serial execution
and acceptance; specialist roles own bounded documentation, Rust tests and
historical evidence preservation. New work does not rewrite old failures or
relabel the old binaries with the follow-up commit.

## Accepted final reader dispositions

The [preparation record](records/doc-lookback-2026-11-04/final-readers/PREPARATION.md) and [artifact manifest](records/doc-lookback-2026-11-04/final-readers/rendering/artifact-manifest.json) record fidelity, hashes and bounded exposure. Each pair used a fresh first reader followed by a fresh skeptical assessor, with no inherited investigation conclusions or external links. The assessor intentionally saw the first report and full interaction history. The PDFs expand collapsible inventories; part of the reported navigation burden is specific to that presentation.

| Document and complete reading artifact | Paired reports and history | Final disposition |
| --- | --- | --- |
| [ARCHITECTURE PDF](records/doc-lookback-2026-11-04/final-readers/artifacts/ARCHITECTURE.pdf) | [First](records/doc-lookback-2026-11-04/final-readers/reports/architecture-first.md), [assessor](records/doc-lookback-2026-11-04/final-readers/reports/architecture-assessor.md), [history](records/doc-lookback-2026-11-04/final-readers/interactions/architecture.md) | Accepted with the recorded R1 source correction after reading. No consequential omission established. |
| [WORKER PDF](records/doc-lookback-2026-11-04/final-readers/artifacts/WORKER.pdf) | [First](records/doc-lookback-2026-11-04/final-readers/reports/worker-first.md), [assessor](records/doc-lookback-2026-11-04/final-readers/reports/worker-assessor.md), [history](records/doc-lookback-2026-11-04/final-readers/interactions/worker.md) | Accepted unchanged since reading, with bounded reading evidence. |
| [LIMITS Markdown](records/doc-lookback-2026-11-04/final-readers/artifacts/LIMITS.md) | [First](records/doc-lookback-2026-11-04/final-readers/reports/limits-first.md), [assessor](records/doc-lookback-2026-11-04/final-readers/reports/limits-assessor.md), [history](records/doc-lookback-2026-11-04/final-readers/interactions/limits.md) | Accepted with C1 accuracy corrections and new Rust citations after reading; source audit and fresh checks cover that delta. The original pair did not read these changes. |

**R1 — corrected and accepted.** At [ARCHITECTURE's verification transition](docs/ARCHITECTURE.md#how-the-system-verifies-itself), line 622, the previous “The last figure” prematurely introduced the document graph. The first reader recorded a brief distraction before targeted questioning; the assessor and source inspection confirmed it. The coordinator changed the authored opening to “The document graph below shows how those generators and rules connect the documents:” and retained the listed relationships. The diff contains only that referent change outside the following generated region. Both architecture-documentation and generator-contract cases passed in fresh managed output `doc-lookback-docs-03`, run `20261105T050537Z_eee41d84`. No product build or fresh pair was needed. Reviewed artifacts remain immutable evidence, with the post-reading delta recorded separately.

**R2 — retain the reference inventories.** All three readers reported lookup/attention costs; no task-blocking missing explanation or consequential wrong answer followed. ARCHITECTURE's runtime-to-maintenance transition is real; PDF expansion also contributes to its length and WORKER's graph/table burden. This record does not justify a redesign or deferred assignment.

**R3 — qualify the evidence.** The tasks directed attention and included onboarding; ARCHITECTURE explicitly addresses its assigned proposal. WORKER's general pre-opening/revocation cautions preceded document access, and its initial skim covered only the opening rather than all headings/figures. Later reading covered the complete artifact. Its first report misdates a shorthand correction: the whole read already recognized attempt-time reporting resources before targeted questions confirmed the opening. LIMITS questions elaborated before-write sizing and fallback eligibility without correcting a recorded contrary belief. Preserve these limits rather than claim arbitrary unaided clarity. No additional reader round or documentation edit is recommended for them.

No new deferral was added. Unsupported hypothetical concerns about the Known gaps index, citation certification, universal isolation, additive clocks, memory bounds, actor/declaration conflation or erasure-as-revocation do not justify more warnings or duplicated diagrams/grammar; contrary passages are present, and the readers did not make those consequential errors. F1 remains the sole accepted deferred implementation investigation. The user authorized proceeding through final acceptance on these dispositions.

## Review basis

The reviewed revision is `ea64218be2549fd034096f53ac23d79afac711ae`, compared with `990dc322f9278c6ad44f500fc8663b9419a60def` before the actor integration and its repairs. The checkout started clean. The [baseline](records/doc-lookback-2026-11-04/baseline.json) pins twenty documentation, input and figure files; [the change brief](records/doc-lookback-2026-11-04/BASELINE.md) explains the boundary.

The initial audit covered ARCHITECTURE's accepted A01–A22 regions, all of WORKER, and all 93 LIMITS entries plus their coverage statements and shared explanations. Most of ARCHITECTURE's generator graph and administrative installation details were context rather than detailed audit subjects. No broad scope reopening was needed. [Architecture scope](records/doc-lookback-2026-11-04/reports/architecture-scope.md), [worker scope](records/doc-lookback-2026-11-04/reports/worker-scope.md), and the [consistency report](records/doc-lookback-2026-11-04/reports/consistency-report.md) preserve these decisions. Stage 5 covered all three whole documents, including the resulting 95-entry LIMITS account.

Stages 0–3 used ten fresh Astra specialist roles: two scopers, three staged readers, a consistency reader and four investigators. Those specialists wrote review records only. The coordinator reviewed coverage and handoffs; no new builds, tests or native trials were performed during those stages. Source inspection, assertion inspection and applicable retained observations are separate evidence categories throughout the investigations; an entry can be grounded without a new runtime boundary observation.

The [provenance assessment](records/doc-lookback-2026-11-04/investigations/PROVENANCE.md) reconstructs the retained dirty snapshots and identifies exceptions. The default run has 215 passing case outcomes and one failure; the final-control run has ten passes. Their retained app inventories matched all 21 distribution-app file hashes at that investigation checkpoint; build 1121 has since replaced that app. Default-run source-drift, registry-fixture and changed Rust test assertions were not credited as current passes; relevant final controls superseded them. Each build retains its recorded source identity, not current HEAD relabeled. Local test evidence is gitignored. The new build's verification is recorded separately above; no new platform qualification is claimed.

## Accepted D1–D5 decisions and their basis

The user accepted the following remedies; all are implemented and validated in the current candidate. These subsections retain the initial findings and remedy rationale. Their source locations describe the initial review state, not unresolved defects in the candidate. Final reader decisions above are separate.

### D1. Correct the public-form account and make applicability explicit

Recommend documentation correction. Public actor requests reach `runActors`; the internal-only statements at ARCHITECTURE 166–178, WORKER 419–422 and LIMITS `phase_records` are stale. Ordinary/declaration requests reach the single-worker driver. Only the declaration path uses `ExtensionSession` and the pre-worker issuer helper. An unapplied actor has setup without applying a supplied policy. Capacity admission still examines a supplied issuer override even when actor execution does not use it.

Scope the existing timelines and resource descriptions by form. In LIMITS, distinguish eight legacy phases from sixteen global actor phases, one legacy consume/release from aggregate actor counts, and each policy's source/parameter bounds from specimen-wide action bounds. Explain that authority participation excludes exec for that actor, including a recipient, while a separate actor may exec. Correct the actor branches in the published first-refusal ordering; do not imply that every capacity or meaning failure uses the same refusal record.

Evidence: [admission investigation](records/doc-lookback-2026-11-04/investigations/admission-report.md), including actual public accepted/refused specimens and independent file effects. This is more than example or comment inspection. Withdrawing public actor execution to fit the old wording would remove an exercised public capability and has no support from this review.

Owners: authored ARCHITECTURE/WORKER passages; relevant `docs/architecture.json` nodes and edges, including `actor_plan`, worker/T9 and issuer dependency; `docs/limits.json` form/count/phase records; authored LIMITS interactions and premises. Regenerate copied guide content. Check broad issuer wording in ARCHITECTURE's BYOXPC account and the corresponding guide passage for the same distinction between runtime dependence and bundle completeness.

### D2. Supply a short actor sequence and resource crosswalk, then shorten repetition

Recommend a locally understandable actor sequence in ARCHITECTURE and a compact resource/lifetime crosswalk in WORKER. The architecture reader's proposed change—defer parked recipient acknowledgments until its next activation—exposed missing completion/activation dependencies. WORKER's detailed inventory is predominantly declaration-oriented despite actor qualifications elsewhere.

The actor sequence must distinguish custody, recipient framing acknowledgment, host equality/settlement, source-observed answer, action/phase completion and next activation. Successful delivery is not a universal prerequisite for schedule advancement: a timed-out exchange can complete with failure. Do not replace this with an invented all-deliveries-success barrier. Parked workers service apparatus while requested native actions remain held. Failed-actor continuation depends on known quiescence, not merely a termination request.

WORKER should identify common apparatus, declaration token channel/static handle and actor authority regions, one-shot slots/cells, host custody and per-reference handles. Preserve the distinction between fresh action acquisition and setup-held descriptors, and between a native release result and later access observations. Exact wire fields and numeric budgets can remain linked references. Detailed authority conclusions and their limits are in the [authority investigation](records/doc-lookback-2026-11-04/investigations/authority-report.md).

Local release state is resolved: legacy execution sets `release_decided` before the call; actor execution retains the handle-valid bit, but admission rejects a second release of that handle. Neither creates a public retry contract or establishes revocation. Shared authority erasure is permitted only for reaped or never-launched owners; unresolved termination permits host detachment, not clearing bytes under a potentially live process. Private custody is separately erased.

Keep the useful resource categories and observation qualifications. Prefer removing repeated source/check enumerations and joining scattered form explanations over deleting whole inventories or adding a second large graph. Label aggregated diagrams as inventories where their arrows omit reciprocal protocol traffic; the short sequence supplies the missing flow. Add or route to `write_fresh`/`create_fresh` in the file-action orientation table if it remains a selector for contributors. These editorial changes should preserve stable resource IDs and useful checking routes.

Owners: authored ARCHITECTURE/WORKER and relevant generated content in `docs/architecture.json`, especially T8/T16/T17 and B18/B19 plus resource rows S5/S7/S13d/S14b/S19–S22/S37. Exact form qualifications belong with the affected rows. Do not edit generated copies directly. No runtime sequencing change is recommended by this finding.

### D3. Describe budgets and qualification measurements at their actual scope

Recommend documentation correction, retaining numeric allowances. [Timing investigation T1–T7](records/doc-lookback-2026-11-04/investigations/timing-report.md) establishes:

- Readiness, publication and validator exit grace use elapsed monotonic accounting with specified fault fallback; several front-table rows incorrectly call them nominal.
- Actor setup starts before region preparation. Execution is one schedule pool excluding synchronous collection; actor collection is one aggregate pool, also reducible by `validator_total_timeout_ms`. The legacy sentinel and its override are a different path. Actor exec accounting also excludes accepted parked activation waits.
- The 180-second continuous lifetime cutoff is sampled at checked waits; it does not preempt blocked native calls or bound final cleanup. Keep client expiry separate from cancellation and execution evidence.
- Qualification's exchange metric measures host recipient wait, not every worker custody/answer wait. Its reported total is setup plus elapsed schedule execution, including collection but excluding final cleanup and the gap before setup-clock start. Charged execution subtracts collection in a separate metric. The finite recorded workloads passed their actual checks; neither whole-lifetime coverage nor all maximal compositions follows.
- The configured launchd throttle is supported; deterministic request delivery after precisely the remaining interval is not established by that setting or the consulted primary manpage.

Owners: `docs/limits.json`, authored interactions/premises and their guide copies; relevant architecture timing prose; `tests/suites/witness_contract/README.md` for names and scope of qualification metrics. Recommend accurately naming the existing measurements now. Additional worker instrumentation or a hard end-to-end lifecycle contract would be separate implementation/design work, not a prerequisite invented by this review. Increasing durations cannot supply preemption or cleanup guarantees.

### D4. Clarify capture, fallback and receiver bounds; retain the repaired size calculation

Recommend the targeted explanations in [evidence investigation E1–E5](records/doc-lookback-2026-11-04/investigations/evidence-report.md). Actor receipts belong to their opted-in apply actor and require the existing apply/completion/identity/checksum conditions. Fallback helper results are independent diagnostics, associated with selected actor policies, and are not application evidence. Fallback can occur before host admission; malformed requests can supply more policies than the admitted eight-actor bound. Per-helper retention does not bound their cumulative envelope or process memory.

Validator allowance is sized from the query list submitted to the phase collector before writes, not the count of successfully delivered lines. Preserve the difference between expected and written bytes and between complete records and usable associations.

Retain the informative 85,852,557-byte reply bound, 84 MiB raw client retention and 248 MiB controller retention. Inspection found the repaired actor shapes accounted for, including captures, late setup and empty visits. Synthetic fixtures plus public observations provide bounded support, not exhaustive proof of every future producer branch. The 16,448-byte authority slot is correct; a useful region explanation is `1152 + (outbound + inbound) * 16448`, derived from existing counts rather than a newly enforced cap. Allocation/page overhead is outside that formula.

Owners: `docs/limits.json`, authored LIMITS interactions/premises, and ARCHITECTURE prose/input IDs `sbpl_check`, T12, `profile_capture`, `helper_envelope`, B9/B12. No new overall memory policy or changed numeric capacity is recommended. Such a policy would require a deliberate implementation contract and compatibility decision.

### D5. Set the inventory's completeness promise and preserve separate work

Recommend clarifying LIMITS as the numeric capacities/budgets/retention inventory with concise routes to semantic admission and evidence eligibility. The missing-limit search found form/ownership/grammar restrictions mostly already owned by the guide; it did not establish seventeen missing numeric caps. Mention the 32-lowercase-hex capture nonce requirement in the relevant admission/capture route. An exhaustive duplicate grammar in LIMITS would increase maintenance and obscure how counts apply.

I1 preparation exposed two additional diagnostic retention bounds that the initial missing-limit search did not inventory: at most eight request-failure path components and at most 63 UTF-8 bytes per component. Swift `PWRunnerRequestFailure.init` and Rust `RequestError::new` enforce the same all-or-null path rule; a parameter key may separately remain in the admission record up to 127 bytes. Carry these source-established bounds into the LIMITS completeness edit, with independently grounded value checks and honest boundary coverage. The I1 tests passed their 63/64-byte component checks in the first run; complete depth-boundary coverage is not claimed. This supplements the initial search rather than rewriting its historical assessment.

The user accepted all three focused work items below for this tranche, without deferral. They remain separately owned so their actual behavior and coverage are reviewed explicitly. Their direct checks now pass, with the evidence and limits recorded below.

| Work | Implemented result and retained limits | Owner and acceptance evidence |
| --- | --- | --- |
| I1 — actor parameter diagnostic path | Actor parameter-value refusal now retains the offending actor in the diagnostic path. Legacy paths, safe-key echo and refusal precedence remain covered; no executed bad request or unbounded echo was established by the original defect. | `CWorkerRequestPlanning.requestCapacityFailure` and admission/contract consumers. Core and six public contract cases passed, including bounded path and actor/key association checks. New inventory-value assertions also pass in the documentation Swift run. |
| I2 — exact compiled-capture boundary control | Native fixture now captures an independently allocated readable 1 MiB object and verifies status, size and digest, alongside cap-plus-one and unsupported controls. It establishes capture at that boundary, not successful compilation/application of a 1 MiB policy. | `tests/suites/runner_abi_layout/capture.c`, suite assertion owner and `limits.json` coverage. `runner_abi_layout/c_swift_layout_agreement` passed; retained applicability is assessed separately. |
| I3 — actor fallback association control | Six dependency-seam cases now exercise exact actor helper inputs/order/association, eligible terminal-error gating and unchanged runner transport results, including malformed unapplied-plus-policy input. This is controlled invocation coverage, not a live-helper observation. | `controller/src/run_flow.rs` and Rust test owner. `unit/rust.unit` passed; production binding remains unchanged. |

Implementations and source-review limitations: [I1 diagnostic](records/doc-lookback-2026-11-04/implementation/diagnostic-report.md), [I2 native capture](records/doc-lookback-2026-11-04/implementation/capture-report.md), [I3 fallback association](records/doc-lookback-2026-11-04/implementation/fallback-report.md). Their direct checks pass as recorded in the first verification checkpoint and qualified by the documentation applicability review. The separate control-reliability failure is assigned to deferred F1 and no longer blocks documentation under the user's decision. I3 adds one compiler-invocation dependency to the existing controller seam, with unchanged production binding; the controller README dependency inventory is updated.

Expanded timing instrumentation and a hard lifecycle/memory bound remain optional design alternatives, with no implementation assignment recommended now. The current limitations can be described accurately without either redesign.

## F1. Deferred setup-observer reliability investigation

**Disposition:** accepted deferral. The user authorized exhausting two final instrumented runs and deferring further investigation if the issue recurred; both runs reproduced it. This newly identified fixture issue is separate from I1–I3, which were not deferred. It does not block the documentation tranche, and must remain visible in final acceptance rather than being represented as repaired or as a passing historical run.

**Owner and scope:** future test/fixture implementer, owning `tests/fixtures/host_setup/`, `tests/suites/runner_unit/host_setup_controls.py` and `host_setup_oracle_sensitivity.py` plus their documentation. Preserve the diagnostic addition, existing observation-first descriptor behavior, independent child identity/effect/cleanup assertions and the distinction between controlled oracle counterexamples and product behavior. No production deadline change is authorized or implied by this finding.

**Established evidence:** [final observation record](records/doc-lookback-2026-11-04/implementation/final-observation.json). Run 06 (`20261105T031925Z_7088dee4`) failed in wrong-ready-direction and partial-unmap variants; run 07 (`20261105T032015Z_f0ccd56a`) failed in wrong-shared-memory-argument. All three missing receipts occurred at the first worker-baseline scenario, with native spawn success, exhausted 200 ms sentinel and exit grace, SIGKILL request rc 0 and confirmed signal-9 reap. No wait errors, clock faults or sleep overlap were recorded; fixture cleanup completed. All 46 copied inputs match the complete instrumented pass in run 05. The retained [observation-copy manifest](records/doc-lookback-2026-11-04/implementation/setup-flake-evidence/manifest.json) identifies small durable copies by original path/run/hash; managed runs retain their ownership.

**Remaining question:** why the independent observer had not created its receipt before cleanup. The current facts do not locate delay in executable startup, scheduling, observation or receipt creation, and do not establish an operating-system cause. Earlier uninstrumented failures cannot inherit the new termination evidence retrospectively.

**Follow-up approach and acceptance:** inspect the retained host/child lifecycle first; add only the observations needed to locate the delay. Choose fixture synchronization or allowance changes based on that evidence, without weakening the original setup assertions or substituting a warmed process for a fresh observer. Retain positive and controlled delayed/missing-observation cases with bounded independent cleanup; verify that equipment failure stays distinguishable from the intended counterexample. Run both ordinary setup and full sensitivity cases through the dispatcher, preserve rejected-checker controls and all independent observations, and record source/equipment applicability. A few successful reruns alone are not evidence that a repair removed the diagnosed cause. Return to a separate scope decision if product behavior must change.

## Reader evidence and discarded inferences

All first readers received a bounded public actor example, role and basic vocabulary before their consequential tasks. They did not initially receive scope maps, the change brief, implementation or expected answers. [Interaction records](records/doc-lookback-2026-11-04/DISPATCH.md) and the three [architecture](records/doc-lookback-2026-11-04/reports/architecture-interaction.md), [worker](records/doc-lookback-2026-11-04/reports/worker-interaction.md), [limits](records/doc-lookback-2026-11-04/reports/limits-interaction.md) histories distinguish initial work from prompts and corrections.

The LIMITS task combined all actor maxima into 256 actions, then added a 257th; it also used a 63-byte multibyte identifier, a per-actor interpretation of client timeout and a truncated-capture inference. The reader already supplied the arithmetic; the document supplied operational rules while also exposing scope contradictions. WORKER's reader already suspected that one setup-opened FD would not test fresh access; the document added mechanism and evidence qualifications. These are not wholly unaided discoveries attributable to the documents.

ARCHITECTURE's reader initially called a pre-call marker proof that a native call began. After a neutral basis question and consulting the linked evidence contract, it withdrew that claim. Existing prose already says pre-call; a prompt alone does not justify another disclaimer. Retain the distinction and assess it again in stage 5. The hypothetical token-digest proposal does not establish an existing leak, required feature or prohibition. Environment configuration versus retained observation and compact graph arrows are scope/terminology questions, not independently proven runtime defects.

Every selected architecture/worker unit has a recorded retention, clarification, combination or question disposition in the [architecture ledger](records/doc-lookback-2026-11-04/reports/architecture-ledger.md) and [worker ledger](records/doc-lookback-2026-11-04/reports/worker-ledger.md). These are documentary assessments, not comprehensive source verification. Necessity does not depend on whether the initial task happened to visit a row. Figures were inspected as relationships/XML in the initial review; candidate artifact preparation subsequently inspected rendered figure/table fidelity as recorded above.

## Missing-limit search disposition

| Hypothesis | Outcome and proposed treatment |
| --- | --- |
| M01 | Form exclusivity, schema and closed-object rules confirmed in admission; guide-owned semantics, link from inventory scope. |
| M02 | Nonempty actor/phase arrays, unique identities and each actor owning a phase confirmed; empty visits allowed. Do not generalize nonempty actor/lifecycle IDs to every legacy ordinary step. |
| M03 | Typed, single-assignment references and ordered ownership confirmed; guide-owned semantics, not new capacities. |
| M04 | Exec exclusion is per participating actor, including recipients; surface concise composition caveat. |
| M05 | Supported file family/read or read_write and closed raw-token/class/flags interface confirmed; interface restrictions do not assert OS incapability. |
| M06 | Full region/custody geometry derives from existing capacities; explain formula/allocation failure without inventing another admission threshold. |
| M07 | One-shot transport, settlement and erasure belong to authority/lifetime account; no new numeric budget identified. See authority investigation for quiescence limits. |
| M08 | Cutoff is checked, not preemptive; cleanup/native work can exceed it. Qualify existing row, no invented total-runtime cap. |
| M09 | Query representation cannot encode extension class beside path; route to evidence limitation. |
| M10 | Source eligibility exclusions/path rules confirmed as selection rules; no new platform calibration inferred. |
| M11 | Finite attempt/filter combinations and exec-only args confirmed; query operation names are not a closed admitted vocabulary. Link grammar. |
| M12 | Nonce shape and receipt prerequisites confirmed; state per-actor applicability and link conditions. |
| M13 | Complete bytes still require schema/association admission; keep receiver contract owner and concise route. |
| M14 | Retention is not process memory or cumulative fallback envelope bound; no additional independent implemented cap found. |
| M15 | Existing fresh-read/sysctl/exec observations already carry relevant resource limits; preserve prefix/discarded-data/descendant qualifications. |
| M16 | Helper source/import inventory limits are independent of compilation and host admission; preserve those scopes. |
| M17 | Repaired actor reply construction examined; no changed-shape omission found. Retain value with fixture/observation limits. |

This changed-path search is bounded, not proof that every OS resource restriction has been discovered. Existing entries' complete evidence assessments are incorporated below by reference.

## Existing LIMITS entry outcomes

All 93 entries have value/unit, counting/scope, control/enforcement and consequence assessments. The following records are part of this plan's evidence and carry the outcome for each exact ID, source/assertion locations, actual credited observations and remaining gaps:

- [Admission/helper grounding: 33 entries](records/doc-lookback-2026-11-04/investigations/admission-grounding.json).
- [Execution/timing grounding: 30 entries](records/doc-lookback-2026-11-04/investigations/timing-grounding.json).
- [Transport/capture grounding: 30 entries](records/doc-lookback-2026-11-04/investigations/evidence-grounding.json).

All original 93 numerical values are retained in the candidate, with the two existing diagnostic-path bounds added for 95 entries. A `retain` entry does not mean every behavior was observed at production duration or every possible boundary composition executed. D1–D5 and the reports supplied wording corrections even where an entry retained its value, including validator per-query sizing and `phase_records` form scope. Comprehensive grounding is not a claim of comprehensive runtime testing.

## Completion and retirement pause

I1–I3 implementation/review, signed build, bounded direct verification, D1–D5
authored/input changes, centralized regeneration, focused documentation/Swift
validation, faithful artifact preparation and all six final reader roles are
complete. Graph IDs and original limit values were preserved. No worker wait,
release-store or eligibility rule changed in this documentation tranche.

The final user decision authorized R1 correction and acceptance. The correction
and both focused checks are complete; R2/R3 dispositions and acceptance of all
three documents are recorded. Stage 6 is closed. F1 stays assigned and deferred,
with its evidence and acceptance checks intact. Review closure does not close
F1 or turn the earlier broad run into a full pass.

C1–C6 are now resolved, with refreshed acceptance and durable evidence recorded
above. Follow-up changes await review and commit. Plans and records remain in
place at the user's requested pre-retirement pause. F1 remains deferred; no F1
rerun, retirement, pruning or pin replacement occurred in the critique tranche.
Any future pin retirement requires its own replacement-credit and live-cleanup
review; the copied historical receipts do not grant cleanup authority.
