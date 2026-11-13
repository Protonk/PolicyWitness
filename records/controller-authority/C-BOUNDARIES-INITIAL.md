# C — independent boundary challenges

## Baseline and first-pass protocol

Investigation source baseline: `dcc7dd0bd0634a603379ff185228abca70b5d22f`; accepted implementation `a5de0c63`; dispatch HEAD `9b579bf7` adds records only. Historical prerequisite completion is accepted by the maintainer despite pruned raw CLI runs. This report claims no new executed evidence. Only this report is writable. No builds, tests, external-service operations or auxiliary agents are authorized for C.

The scenario list below was written before targeted contract or production-code inspection. Prior exposure: the complete integration plan and required repository guidance, root README and controller README (which expose architectural summaries and contract wording). Those summaries are navigation, not findings. No A/B artifacts, coordinator source inspection, or emerging conclusions were consulted. BASELINE is restricted to its entry decision and identity. The scenario outline is independently framed around public inputs and observable consequences.

## Initial scenarios (before targeted inspection)

| ID | Entrance and varied input | Possible outcome requiring discrimination | Required observations |
| --- | --- | --- | --- |
| C01 | `run`: invalid identity plus malformed/shadowed runner selector or failed augment | Early refusal versus interpretation/launch before admission | Exact refusal; reader/helper call counts; original and delivered document |
| C02 | `run`: replace source or augment after preparation; ordinary and actor forms | Selected bytes versus later filesystem contents; fallback compiles wrong policy | Held callback input, dossier hash basis, compile input and call count |
| C03 | `example`, then `run`: emit under same build; altered host grammar input | Self-gate versus actual grammar admission; emission does not promise native completion | Exit/stdout/flush; exact callback string; pipe count; host response as distinct observations |
| C04 | `run`: reservation reply lost, execution reply lost, deadline or helper capture lost | Safe pre-submission reconnect versus prohibited replay; unknown versus no invocation | Client state, independent execution count/effect, host generations, original deadline |
| C05 | `run`: unsupported/malformed/truncated capture or host frame, combined with failed stdin | Rejected bytes accidentally acquiring semantic authority or fallback compilation | Raw retained bytes, typed diagnostics, invocation/delivery, null/withheld projections |
| C06 | `run`: finished reply plus integrity contradiction or incomplete actor/phase records | Successful command with unusable dependent claims; local versus global withholding | Raw contradictory records, per-process derived claims, diagnostics and final exit |
| C07 | Existing offline consumer: corrupt result fields independently and alongside record faults | Result mutation disables checking; unrelated error masks mismatch; rejected bytes improperly supply mapping | Independently expected exact diagnostic sets; admitted/non-admitted control pairs |
| C08 | `run`: completed effect, missing worker observation or publication interrupted | Effect happened without usable result; absence of evidence treated as evidence of absence | Independent disposable target/process observation plus capture/public output |
| C09 | `runner`/`run`: stale path/read-back versus actual running identity, changed entitlements | Registry assertion mistaken for current effective equipment | Installed/read-back identity, selected bytes, actual worker provenance and limitations |
| C10 | `runner remove/reconcile`: foreign service, unknown status, partial cleanup | Prefix mistaken for ownership; unknown mistaken for absent; lost recovery authority | Ownership checks, before/after inspection, durable cleanup record, no foreign mutation |
| C11 | `example`/`run`: short write, complete-looking stdout followed by flush failure/interruption | Apparently parseable document wrongly accepted despite failed publication | Process exit, actual bytes, explicit flush error and caller submission count |
| C12 | `run`: independent compile success or log candidate alongside missing execution reply | Secondary observation improperly establishes execution or sandbox cause | Compile/run separation; PID provenance; raw timing; supported/withheld conclusions |

These cover all eight plan families; C06 deliberately challenges a plausible code/contract agreement (finished status with integrity findings), rather than assuming agreement determines the desired public responsibility.

## Reading results and challenge designs

Evidence notation: **S** means inspected source/contract; **C-read** means inspected constructed-control assertions, not executed checks; **N-design** means a native experiment proposed but not run. No row below claims native execution. Public node identifiers below follow the authored surfaces, not a generated controller index. Reproducers are designs for coordinator scheduling through the dispatcher; they are not reports of commands executed by C.

### C01 — Admission does not mean that nothing was read

**Targeted sources:** `request.specimen.emit_example`, request selector rules in `docs/contract/10-request.surface.md`; `run_flow.rs::run`, `inject_runner_mode`; `runner_select.rs::parse_runner_selector_value`; orchestration controls `runner_mode_option_cannot_overwrite_a_malformed_selector` and `builtin_manifest_failures_refuse_before_the_client_with_one_load`.

**Observed boundary (S/C-read):** the request contract precedes selector interpretation and augment resolution, but app-root/manifest/provenance work precedes reading and admitting the request. Selection resolution is attempted before augments; its error is returned before the recorded augmentation error. An invalid identity therefore prevents semantic selector/augment use and client invocation, not all environment reads. CLI argument processing has its own earlier boundary. Shadowed aliases still require validation.

**Authority:** Rust has the raw request and controls these reads/refusals; the host alone admits host grammar after submission. Rust owes refusal ordering and preservation. Neither can conclude that no machine access happened merely from a request refusal.

**Discriminating fixture:** at the `RunDependencies` seam, combine foreign contract, malformed nested selector, malformed legacy alias, missing augment, and missing manifest. Count app-root, manifest, client and compiler callbacks. Independently require contract refusal before selector/augment diagnostics; zero client/compiler calls; manifest read permitted. Then restore identity and isolate each selector/augment fault. Combine a resolvable selector with missing augment, then a missing runner with that augment: establish the documented selection-before-augmentation failure precedence. Do not treat an earlier app-root failure as evidence for identity precedence.

**Counterevidence/limit:** existing ordering and selector controls already rebut much of the proposed leakage. This is primarily a precision challenge for the new account, not evidence of an implementation defect. Host grammar is not exercised by callback controls.

### C02 — Held source is not a frozen filesystem closure

**Targeted sources:** `docs/contract/10-request.surface.md` opening specimen account and selector/augmentation rules; `run_flow.rs::run`, `actor_fallback_checks`, tests `actor_fallback_uses_held_policy_objects_before_host_mode_admission` and `emitted_example_reaches_the_client_as_the_emitted_document`.

**Observed boundary (S/C-read):** one in-memory ordinary request supplies client and ordinary fallback. Actor fallback separately serializes each held policy object in actor order; it is not byte-equal to the whole request. The actor control changes the request file inside the client callback and compares independent expected policy objects. Policy import paths and binary dossier reads remain separate filesystem observations; holding the request cannot freeze imported filesystem content or later native path resolution.

**Authority:** Rust holds selected source, augments and serialization; helper/worker independently compile under their own environments; the filesystem owner can change imports. Rust owes a consistent account of selected text and separate helper captures, not a transaction spanning arbitrary path targets.

**Fixture:** replace request and augment files after preparation at the existing callback. Require client string unchanged, ordinary fallback exactly equal to that string, actor fallbacks equal to independently authored per-actor policy objects, and original file contents not restored by production. Separately design an import-file replacement between dossier collection and helper/worker compilation: require observations to remain labeled as samples, not an assertion that every compiler consumed the hashed closure. An independent file digest immediately before each controlled compile would discriminate closure stability; a source digest alone cannot.

**Counterevidence/limit:** source and existing callbacks support the held-input guarantee. The import-race extension is an unexecuted question, not a demonstrated native mismatch or a demand for atomic filesystem snapshots.

### C03 — The example's narrow admission promise

**Targeted sources:** `request.specimen.emit_example`; `example.rs::render/emit/cmd_example`; exact-preparation control in `run_flow.rs`; `witness_contract/example_round_trip.sh`.

**Observed boundary (S/C-read):** render parses an object, inserts identity and validates identity before serialization/output. It does not run the host grammar. The exact-byte control feeds the rendered file through actual run preparation into a controlled client callback. The signed-app case submits the emitted file and separately checks delivery length, reply admission and input relationships. These are three distinct boundaries, not proof of exact signed-app host receipt from a pipe count.

**Authority:** controller owns the constant and emission; host owns grammar; client writer observes accepted pipe bytes; caller uses process exit to decide whether emission is usable. The product owes same-build admission of its successfully emitted document, not successful native execution or fixed labels/layout across builds.

**Fixture:** preserve the existing constant-based live case. For offline host-admission challenge only, alter one permitted outer request member to a grammar-invalid value, retaining the correct identity; self-rendering can succeed but `run` must return host `bad_request`. This contrast does not refute the promise about the actual emitted constant. Require exact controlled callback equality, separate length check, and admitted reply relationships; do not invent a production capture field to collapse them.

**Counterevidence/limit:** current controls explicitly separate these scopes. No new native evidence here. Accepted CLI dispositions remain binding: coherent validator inability is not automatically an emission defect; failed emission means no submission and no execution-unavailable claim.

### C04 — Invocation is a positive commitment, not proof of host execution

**Targeted sources:** transport reservation/submission rules in `20-transport.surface.md`; `PWRunnerClientSession.swift::retry/connectionFailed/submissionReply`; `PWRunnerReservation.swift::submit`; `runner_byoxpc/README.md` reservation-control account.

**Observed boundary (S):** retry requires acquiring state; after grant and a fresh original-deadline check, the client records `invoked` and enters submitted state before calling submit. Submitted transport failure completes without replay. The host consumes a connection-bound reservation and never makes an executing/retiring slot free again. Lost helper stdout supplies no controller submission claim even when invocation happened.

**Authority:** client can prohibit its own second execution call; host can enforce single consumption across connections; Rust invokes one client and cannot recover a missing client's private state. The report reader can conclude only the admitted capture's submission state. No owner can infer nonexecution from a missing result.

**Discriminating native design:** use existing `runner_byoxpc/reservation_controls`, with its owned copied host/client and append target. Lost reservation reply: permit another acquisition but require no execution before a valid later grant. Lost execution reply: independently require exactly one append and one execution trace, retained invoked state and no replay. Kill helper before stdout: require unknown submission in Rust despite the trace's one invocation. Restore each gate. Retain original deadline and generation-qualified identities. A timeout or missing trace alone cannot establish nonexecution.

**Counterevidence/limit:** source strongly supports the split. Catalog/README descriptions locate native checks but C has not inspected raw runs and claims no current execution credit. Instrumented copies alter timing and do not prove production equivalence. No experiment requested solely to recreate historical evidence.

### C05 — Refused bytes remain bytes, including under combined faults

**Targeted sources:** `envelope.data.admit`; transport capture rules; `run_flow.rs::admit_reply`; `runner_client.rs::parse_runner_client_output/fallback_eligible`; controls `producer_gate_precedes_malformed_descendants_and_keeps_raw_bytes`, `arbitrary_rejected_host_bytes_survive_and_do_not_become_claims`, `malformed_capture_keeps_exact_bytes_and_no_recovered_submission`, `delivery_failure_takes_precedence_and_retains_the_client_frame_unread`.

**Observed boundary (S/C-read):** delivery failure is first. Client admission precedes host frame and producer/context admission. Unsupported/truncated capture cannot supply submission claims; unsupported host bytes cannot supply execution diagnostics. Structurally decoded but context-refused records can remain in the envelope, without diagnostic authority. Fallback requires accepted transport, no delivery error, and client terminal `xpc_error`.

**Authority:** native producers own their bytes; Rust owns receiver gates, preservation and public classification; consumer owns independent refusal checks. Rust owes exact retained bounded bytes and honest withholding, not recovery of meaning from unsupported bodies.

**Fixture:** valid binary neighbor, foreign schema, foreign producer, malformed body, retained-prefix truncation; combine each with EPIPE while writing a large request. Require `tool_error`/2 for delivery refusal with opaque bytes, otherwise the boundary-specific refusal/1; no execution diagnostics, no fallback on unsupported/malformed evidence. Restore faults independently and require the intended gate to be reached. Preserve bytes before any parse. Distinguish complete received length from retained prefix.

**Counterevidence/limit:** existing tests address these combinations directly. No bypass was established. Crafted frames establish receiver behavior only; they do not show the normal host produces those frames.

### C06 — Correctly implemented success and withholding remain product choices

**Targeted nodes:** `envelope.data.select`, `.success_findings`; `diagnostics.execution.reply_checks`, `.outer_result`; `diagnostics.issue.subject`, `.withholding_scope`. Sources: `run_flow.rs::complete_execution`; `porcelain_admission.rs::execution_diagnostics`; `typed_invalid_actor_account_keeps_independent_actor_endings`.

**Observed boundary (S/C-read):** admitted `finished` gives ok/0 independently of integrity findings. Reply-wide findings withhold the aggregate, set unknown cause/invalid integrity, and preserve actor projections and an already derived ordinary stop reason. The actor test explicitly expects `actor_evidence` plus an independently projected `clean_exit`. Code and contract agree on this behavior and openly leave its desirability undecided.

**Challenge:** an automation consuming only success or an actor's clean ending can mistake retained local conclusions for sufficient evidence of the requested experiment, even when association or activation evidence invalidates a relationship needed to identify the actor. Conversely, withholding every ending for an unrelated query fault would discard sound observed reap information. These are distinct fault-dependency questions, not one generic integrity flag.

**Authority:** host holds native observations and emits claims; Rust has the carried relationships and can validate/withhold projections, but cannot manufacture absent native facts. The public result's meaning and scope of withholding belong to the maintainer. A reader must inspect findings under the current contract.

**Fixture design:** use one clean ordinary reply and one valid two-actor reply; (a) damage only phase collection/order evidence, (b) damage actor association/launch PID while preserving locally valid reap records, (c) damage one actor's owned-reap basis. Keep producer/capture admission valid. Require raw-record preservation, exact finding kinds/locations, aggregate invalid/withheld for reply-wide failures, and separately track each actor projection. For a `finished` reply expect ok/0 under current rules; the independent consumer should report integrity violations without claiming result-mapping inconsistency. Restore each relationship. This reveals current scope, not the policy answer.

**Consequential question:** should success continue to mean only admitted host `finished`, and which association failures invalidate attribution of otherwise sound per-process endings? An explicit retain/clarify/change decision is needed; neither existing agreement nor a passing constructed test settles it. No native reachability claim is made for the fabricated contradiction.

### C07 — Result checking has strong applicability, but its controls do not demand the full diagnostic set

**Targeted sources:** `envelope.data.select`; `tests/lib/consumer.py::admitted_reply/_admitted_outcome/_validate_result/validate`; `blackbox_e2e/checker_controls.py::result_consistency_controls`.

**Observed boundary (S/C-read):** the result rule derives applicability from admitted capture/host bytes, version and profile context, not the three result fields or the presence of diagnostics. It checks exact Python types so boolean/integer aliases do not pass. Missing comparison evidence does not disable it. Coherent non-finished replies use false/1 without a consistency failure. Rejected profiles/captures and absent replies supply no mapping. Captured host bytes, not a mismatching JSON projection, determine the result.

**Concrete control limitation:** `control()` compares the exact set of recognized result diagnostic prefixes and requires each `beside` substring. For fault cases it does **not** reject every other consumer diagnostic. Only a case with neither expected result errors nor beside errors requires `not errors`. Thus these controls establish the intended result diagnostic set and required companions; they do not establish the complete independently expected consumer diagnostic set required by the integration plan. This is source-established test accounting, not a discovered consumer-runtime defect or a reopening of accepted CLI prerequisites.

**Authority:** consumer has admitted bytes and public result; it can independently check the relationship. Controller assessment precedes envelope assembly and cannot independently validate its later output. Test authors own an independent expected diagnostic set; shared codecs do not supply that semantic oracle.

**Small discriminating control request (unexecuted):** through `blackbox_e2e/checker_controls`, inject one unrelated diagnostic into the validation result for a deliberately invalid result case, without changing targeted result prefixes or required companion errors. The current local `control()` would accept it by inspection. A strengthened control must reject the unexpected diagnostic, while ordinary valid, one-field, combined, rejected-profile and projected-versus-captured cases retain their intended sets. Independently enumerate necessary structural consequences before comparing sets. Do not derive the expectation by running the same validator. The CLI example checker allowance for an incidental aggregate `(consumer_validation, consistency)` is not blanket permission for other extra errors.

**Counterevidence/limit:** the existing result-prefix set checking is meaningful and comprehensive on applicability/type mutations. Diagnostic categorization may legitimately group multiple strings; a reviewed classification table is sufficient if it preserves all underlying errors and the plan's required distinctions. No execution or production edit is required to acknowledge this narrower present coverage.

### C08 — Effects can precede missing observations and output

**Targeted sources:** runner README's publication seam; `tests/suites/witness_contract/check_worker_sparse.py`; `porcelain_admission.rs` entered/unreached lifecycle controls; transport loss rules. The sparse case independently compares file bytes and retains completed attempt results despite missing `done`; it is not itself proof of an effect whose attempt publication is missing.

**Authority:** worker performs native operation and owns completion publication; host sees published slots and lifecycle; external observer can see the target; controller can preserve received observations only. No actor owes recovery of unpublished native return values. Controller interruption cannot roll back an already completed operation.

**Native fixture design:** on an owned disposable target, run a writing operation with `worker_kill_before_publish_slot: 0`, separately observe target state, and inspect entered progress, absent completed result and native termination/reap. Require the selected boundary to be reached (override echo alone is insufficient). Compare a neighbor without the seam, and an earlier admission refusal. Independently observed changed bytes may establish a fixture effect, but do not justify synthesizing rc, native errno or sandbox cause. For lost public output, gate controller stdout after invocation and observe target/process separately.

**Counterevidence/limit:** missing `done` after completed attempts is already explicitly tested. The more specific effect-before-slot-publication case needs its own reached-boundary evidence if credited. Target equality is only sampled equality, not proof of no intervening write; difference alone does not identify a writer.

### C09 — Selection read-back versus current execution equipment

**Targeted sources:** request required-entitlement fields; `runner_select.rs::enforce_required_entitlements/resolve_external_target`; installation validation rules; runner equipment account.

**Observed boundary (S):** required selected-worker keys are checked against manifest/registry `granted` observations. Errors/missing read-back refuse selection; host keys are insufficient. This preflight is separate from actor equipment's sealed artifact and owned-live-process checks. The diagnostic wording that a worker “does not hold” a key must be read in that observation scope, not as a fresh kernel privilege measurement.

**Authority:** registry manager can refresh signing metadata; Rust selects using recorded information and observes binary paths/hashes; host has live actor ownership and equipment observations; OS applies effective restrictions. None of a path, entitlement name or signed metadata alone proves effective sandbox permission.

**Fixture design:** with fake registry/OS dependencies, hold a registry entitlement true while replacing the selected worker metadata; prove what selection reads and what it does not. Separately actor equipment controls should reject a sealed/live identity mismatch before activation while retaining already observed setup/application. No unowned service modification is authorized. Require the report to distinguish recorded preflight from live evidence; do not demand all ordinary selection paths promise actor live-verification guarantees.

**Counterevidence/limit:** selection's current contract is deliberately read-back-based. This is a scope challenge, not a finding that a stronger freshness guarantee was violated. C did not inspect every native actor-equipment call or run a replacement experiment.

### C10 — Recovery persists after a successful remove command

**Targeted nodes:** `installation.commands.remove`, `.ownership`, `.reconcile`; source `runner_manager.rs::remove_record`, `service_ownership`, `plist_ownership`; registry cleanup tests around `CleanupSystem`.

**Observed boundary (S):** pending cleanup is saved before native actions; service and plist ownership are independent. Plist ownership is rechecked immediately before unlink. Final absence and no warnings are required before retirement; failed registry publication marks cleanup retained. Unknown/foreign ownership does not authorize bootout. Reconcile candidates are not removal authority. The contract explicitly permits remove result.ok/0 with retained cleanup.

**Authority:** controller holds registry lock and durable ownership record, inspects and requests native actions; launchd/filesystem own actual states. Controller owes safe action gating and durable recovery, not absence from command success alone. Caller owes inspection of cleanup fields under the current meaning.

**Fixture:** use the existing fake `CleanupSystem` to vary owned-present → unknown, foreign program with matching prefix, owned plist replaced between inspections, successful bootout but present service, and final registry-save failure. Count bootout/unlink calls independently; require no foreign mutation, retained nested record and warnings, and successful retirement only after independently observed absences plus save. Restart from disk after save failure. Keep a clean absence/restoration neighbor.

**Counterevidence/limit:** the code visibly protects these cases. A race after an ownership observation is still possible in principle; immediate recheck narrows a window rather than providing atomic object identity. This is not a demonstrated foreign deletion. Another public-success boundary exists here, but do not conflate it with run integrity: completed command and completed cleanup are explicitly separated.

### C11 — Publication completion differs between example and envelopes

**Targeted sources:** `request.specimen.emit_example`; `example.rs::emit`, `only_complete_output_with_a_successful_flush_succeeds`; `json_contract.rs::print_envelope`; `witness_contract/example_round_trip.sh`; `example_round_trip_controls.py` emission mutations; catalog `witness_contract/porcelain_output_controls`.

**Observed boundary (S/C-read):** example uses `write_all` then explicit `flush`; flush failure can leave complete-looking bytes and still returns refusal/2. The live case gates preparation before invoking run; its controls mark run groups unevaluated on emission failure. General envelope printing uses `println!` after full serialization, with no equivalent explicit fallible flush-return handling in that function. It is unsound to generalize example's exit-2 publication guarantee to every output path.

**Authority:** producer can attempt/observe writes and flush; downstream caller sees process status and retained bytes; neither can restore effects after output interruption. Example caller must discard stdout on exit 2. Run caller cannot infer nonexecution from an incomplete envelope or abnormal process exit.

**Fixture:** reuse a writer that accepts the whole example then fails flush: independently expect complete bytes plus `Refusal::Write`; wrapper expects exit 2. Feed complete-looking emission plus exit 2 to offline example controls and require emission failure, zero actual submission, all run-dependent groups unevaluated, no execution-unavailable diagnosis. For general run output use `porcelain_output_controls` fixed-prefix closures and require nonzero/incomplete document while independently distinguishing already-completed execution. Do not require an example-specific exit code on this separate path without a public decision.

**Counterevidence/limit:** existing controls cover the relevant design. C inspected the catalog rather than executing public-output interruption and does not claim an exact platform panic/signal exit. Broader durable publication or cancellation promises would need new authority and observations.

### C12 — Secondary observations cannot repair execution loss

**Targeted sources:** `envelope.data.admit`; diagnostics cause-chain rules; `run_flow.rs::fallback_policy_check/actor_fallback_checks`; `runner_client.rs::fallback_eligible`; `policy_check.rs::supported_outcome` and helper receiver controls.

**Observed boundary (S/C-read):** only admitted client-terminal `xpc_error` with successful delivery permits fallback compilation; helper captures remain separate and retain unsupported/incomplete envelopes without manufacturing compilation. The ordinary/actor held-policy distinction from C02 persists. A successful compiler cannot tell whether an invoked worker applied policy or whether execution happened before reply loss. Worker PID provenance cannot be replaced by host/client PID; a log candidate is not authoritative causal evidence merely by temporal proximity.

**Authority:** compiler observes its own compile; host/worker produce execution evidence; controller can correlate carried observations under their limits. It owes separate provenance and unknown causes when supporting observations are absent. OS/kernel causation is not visible merely from permission-shaped failures.

**Fixture:** admitted `xpc_error` with invoked state and compile success, contrasted with identical helper output under unsupported capture and with failed stdin. Require fallback only for eligible case, no fabricated runner result/disposition or execution claim. Add unfamiliar helper outcome and nonzero helper status to ensure separate retention without recategorizing worker execution. For any log correlation experiment retain independent worker identity/generation and competing unrelated log candidate; do not install or perturb services for this initial report.

**Counterevidence/limit:** existing helper tests intentionally copy admitted helper outcomes without a second verdict. C has not established a current log-derived execution-classification path; that part remains a negative constraint on the new narrative, not an alleged bug.

## Exposure, coverage and consequential questions

All eight prescribed boundary families have scenarios and targeted review: admission/preparation C01–C03; uncertain invocation C04; rejected evidence C05; contradictory/degraded reports C06; result consistency C07; effects without publications C08; equipment/cleanup C09–C10; output/helpers C11–C12. Ordinary and actor forms are distinguished where shared mechanisms differ. Version/example/runner entrances are navigation context; this is not an exhaustive obligation inventory (A's assignment) or every-call implementation audit (B's assignment).

Exposure after the initial list includes targeted authored request, transport, envelope, diagnostics and installation surfaces; contract authoring guidance; controller production and inline tests; client reservation state machine; runner/reference and fixture/test catalogs; selected consumer/checker code. Required summaries exposed architecture before the list and are declared above. No A/B report or conclusions were read. No independent native observation was supplied or created; no historical raw evidence was re-created, and no test execution, build, worktree or service action occurred. The few README/catalog-only control references locate proposed evidence and earn no assertion-level or native credit. Source-supported and constructed-input claims do not establish native reachability.

Prioritize these questions for cross-examination:

1. **C06, public decision:** retain or change host-outcome-only success? Distinguish ordinary failed attempts from integrity findings. Separately specify which association failures invalidate actor attribution versus merely an aggregate relationship. Existing code/contract agreement does not settle either question.
2. **C07, evidence accounting:** obtain complete independently expected diagnostic sets for consequential result-checker controls, or explicitly limit present credit to exact result-prefix sets plus required companions. The current helper leaves unexpected non-result diagnostics unchecked in fault cases. This source-level limitation is concrete and does not require accumulating native runs.
3. **C04/C08/C11, information limits:** ensure the account never equates nonpublication with nonexecution, never replays after invocation, and never promises cancellation or rollback from timeout/output loss. Existing copied-service and interrupted-output controls are the discriminating routes if new claims or changes need execution.
4. **C02/C09, observation scope:** describe held text and recorded/read-back equipment as such; do not imply frozen imports, current effective entitlements or verified live identity on paths lacking those observations.
5. **C10, public meaning:** preserve the explicit difference between a completed remove command and completed cleanup, including durable ownership after output loss. No change is proposed without maintainer judgment.

No additional experiment is necessary to finish this initial report. The C07 discriminating control is the smallest proposed follow-up; C06 needs a concrete maintainer decision after reconciliation. Native experiments should be scheduled only for consequential changed claims or unresolved factual questions, through the coordinator, with one owned output and cleanup route rather than accumulating exploratory runs.
