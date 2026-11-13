# C — cross-examination after the initial freeze

The initial reports remain unchanged at freeze `079b7cd7`. This response reviews A's obligation inventory and relevant exact-node/context appendix entries, B's implementation account, C's original challenges, `CROSS-EXAMINATION.md` and `EVIDENCE.md`. It then follows the named source paths and reads scoped raw receipts from the single fresh evaluation. No tests, builds, production edits, worktrees, helper agents or external operations were performed. Only this response is written.

Production/test/contract subject remains `dcc7dd0b` / accepted implementation `a5de0c63`. The fresh run is `20261113T152200Z_6453a261` under `tests/out/runs/controller-authority-evaluation`; its artifacts are local/disposable. Reading those artifacts now does not retroactively enlarge any original's evidence grade. Large original reports were reviewed by their substantive inventories, questions and targeted appendices; this is not an independent rederivation of A's entire 1,907-node extraction.

## X02/X04 — A local projection does not independently establish actor identity

**Agreement with A21/A24/A27/A31 and B-REPLY-ASSESS, with one wording correction:** “independent actor endings” must mean separately computed lifecycle assessments of retained actor rows. It must not mean independently established attribution of each ending to the originally requested actor. The latter reading is too strong even when the ending's native-status fields are internally sound.

`porcelain_admission.rs::execution_diagnostics` builds an actor's action list by selecting carried phases whose `actor_id` equals that row's label, then finding each action ID in carried steps or extension events. It passes only the row's subprocess, that list, and the degraded-form flag to `project`. `validate_lifecycle` checks subprocess PID range, claims/native-status/reap support, progress, slot count/order, action identity and lifecycle copies. It does not receive the actor launch record, the original request or the entire actor identity table. The output label is then copied from the retained actor row. Only afterward do `actor_associations` and other reply-wide checks compare actor indexes/unique labels, launch versus subprocess PIDs, visits and cross-record relationships. Their findings withhold the aggregate without revising actor projections.

This gives three discriminating cases, with different implications:

| Case | Minimal constructed change, after an independently valid actor control | Expected current boundary and consequence |
| --- | --- | --- |
| X04-PID | Change one actor's `launch.pid` to a different valid positive PID; leave its subprocess and all local lifecycle/action inputs unchanged. | `actor_associations` must emit `actor_evidence` with the launch/subprocess disagreement. Other actor/equipment relationships may also fail, and their exact set must be authored after choosing the valid fixture. The local `project` inputs are byte-for-byte unchanged, so its ending stays as before by source inspection; the aggregate is withheld. This is not evidence that the named actor's launch and ending identify the same process. |
| X04-ACTION | Change a phase action ID to an absent ID without changing the subprocess disposition's step list. | `filter_map` drops the missing action, so a nonempty baseline reaches local `disposition/action count mismatch` as well as reply-wide partition/association checks. This directly rebuts a blanket claim that every action-association fault leaves local endings untouched. Exact combined findings depend on the baseline. |
| X04-TRANSFER | Damage only a transfer's source association while preserving actor labels, phases, actions and subprocess records. | Reply-wide transfer finding; local lifecycle inputs unchanged, so their endings remain. It would be overbroad to describe that preservation as inherently incorrect. |

These are unexecuted designs, not three new native observations. The fresh Cargo log does show passes for `typed_invalid_actor_account_keeps_independent_actor_endings` and `typed_actor_references_reject_other_source_without_erasing_transfer`; their inspected assertions cover constructed preservation, not specifically the new launch-PID-only variant or every combined finding. A fabricated contradiction need not be emitted by a normal host to be a meaningful receiver challenge, but its interpretation does not establish native reachability.

**X02 request operands:** the diagnostics entry accepts only `Option<&PWRunnerRunResult>`. Its action associations are among carried records, not a comparison with the caller's held request. `admission_problem` checks profile status/producer/stage labels and geometry, not requested nonce, source digest or actual bytecode. A17 and `profile.receipt.labels` correctly distinguish this from the host's capture-production checks. `actor_evidence.actor.account` explicitly assigns assembling declarations and actual outputs to the host; `actor_evidence.gate.check` resolves carried reply operands. No missing original-request operand has been shown to violate those targeted controller rules. Coherently changing every carried label can remain internally consistent; that would test request binding, which this reader does not promise to reconstruct independently.

**Proposed decision wording, retain current scope:**

> Each actor diagnostic is the lifecycle assessment of the subprocess and action records selected from that retained actor row. Its actor label is copied from that row. Reply-wide association findings withhold the aggregate and remain beside these local assessments; a local assessment does not independently establish the row's association with the requested actor, launch or schedule. Raw records remain available.

Place the distinction beside `diagnostics.execution.actor_rows`, `diagnostics.issue.subject` and its withholding-scope disposition, not solely in a remote warning. This preserves current bytes and checks but settles a public meaning/scope question, so the maintainer must approve it.

**Alternative:** withhold affected actor projections when a failed identity/PID/action association is a prerequisite of their attribution, preserving unrelated actor projections and all raw records. Consequence: a launch-PID disagreement would now invalidate the affected actor projection; a transfer-only fault need not. This requires an explicit dependency policy and coordinated implementation/contract/consumer controls. “Withhold all actors for any reply-wide finding” is simpler but discards valid unrelated endings and should not be silently substituted for dependency-sensitive withholding.

**What changes my view:** an existing local validator input/check comparing that launch PID or independently retained request identity would defeat the specific source argument. A reached constructed test showing the PID-only mutation alters local inputs or local projection would require revisiting the fixture. Native evidence is unnecessary to choose between these public projection meanings. I recommend retaining the current row-scoped interpretation explicitly unless the maintainer wants actor-labelled projections to certify stronger attribution.

## X03 — Success is correct under the present rule, not a complete evidence endorsement

A33 and B-OUTER-RESULT agree with C06: `complete_execution` computes diagnostics and independently selects true/0 for admitted exact `finished`. The gap `envelope.data.select.success_findings` expressly leaves the desired product rule open. Fresh executed constructed controls include `malformed_phase_claims_withhold_projection_and_preserve_raw_reply` and `typed_completion_preserves_native_failure_beside_finished_summary`. This is evidence of the current distinction, not a spontaneous contradictory native reply.

**Recommended retain wording:**

> For an admitted host reply, `result.ok` and the selected process exit status report the host completion outcome: only `finished` selects true and zero. They do not certify that every attempt succeeded or that all controller evidence checks passed. Controller findings and withheld assessments remain independently reported. A complete-looking document alone is not a process-exit observation.

Retain the existing result mapping and settle the gap with an explicit maintainer disposition. Callers that need evidence consistency must inspect the assessments/independent reader. This is consistent with a finished experiment containing a failed file open.

**Alternative requiring deliberate implementation work:** success requires admitted `finished` plus no failed applicable controller integrity check. Keep `normalized_outcome` as the host label and choose false/1 when findings invalidate the assessment. This intentionally breaks the existing “true exactly for finished” consumer relationship and must update `envelope.data.select`, result field definitions, independent consumer applicability/expectations and CLI checks together. Define failed checks explicitly; do not use a nonempty issue array, since valid supported conflicts can retain issues. Do not make every failed attempt a command failure.

The fact that both choices are implementable does not choose between them. No broader native rerun is needed merely to retain and explain the current rule; shipped changes would require the plan's applicable validation. A concrete existing public rule promising evidence-valid success would change my current “correct but open” classification; none has been identified.

## X05 — Degradation preserves the conflict rather than certifying its joins

`reply.failure.publish.associations` and `actor_evidence.actor.reader_scope` explicitly permit retained inconsistent associations in rich degradation. In `admit_reply`, presence of `reporting_failure` selects marker/summary/comparison/retention checks and bypasses ordinary phase, native-operation and actor-relationship checks. Geometry/profile admission remains earlier. Worker-local lifecycle projection still runs, using the carried action selection and relaxed comparison-absence requirement. `typed_degradation_never_certifies_surviving_comparison` passed in the fresh unit log.

Consequently, neither an admitted rich fallback nor a valid local lifecycle assessment certifies ordinary actor/phase association. A comparison retained in that form is still a defect found by the degradation checks. The original `finished` is diagnostic context, while the actual reported outcome `runner_reporting_failed` yields false/1. The present targeted contract is not contradicted.

**Recommended retain wording for the association-gap disposition:**

> A rich reporting-failure reply preserves assembled observations, including the association conflict that may have prevented ordinary reporting. Admission certifies its degraded form and applicable receipt context, not ordinary actor/phase/resource consistency. Local lifecycle assessments remain row-scoped as described by the diagnostics rules; no comparison or query-order conclusion is recovered from retained raw records.

**Alternative:** require every degraded reply to establish ordinary joins before retaining it. This would cause precisely the useful association-conflict reports to fall to minimal evidence loss unless the representation/assessment is redesigned. That consequence needs explicit maintainer approval; it is not a harmless validation tightening. A narrower alternative is preserving all rows but withholding projections whose attribution depends on failed/unchecked joins, coupled to X04.

**What changes my view:** an actor/phase ordinary certification actually emitted by the degraded path, or a new promise that degraded association validity is guaranteed. Raw retention alone is not such certification. No native failure reproduction is needed for the current form distinction.

## X06 — Keep publication guarantees specific to their command

A34 and B-PUBLIC-WRITE correctly separate `example`'s `write_all`/explicit fallible flush from general `println!` envelope paths. The fresh unit log records `only_complete_output_with_a_successful_flush_succeeds` passing; its full-output-then-flush-error writer establishes complete-looking example bytes can accompany refusal. It does not observe an actual signed-process flush failure.

The fresh live example report records all 67 assertions passing, no consumer errors and no unevaluated assertions, for one build/machine execution. That report does not establish durability, downstream receipt or publication behavior under interruption. This response inspected that report and relevant unit log, not every live input/target file; full raw-native credit stays at the narrower EVIDENCE account.

**Proposed explanatory wording:**

> The example command treats failed writes or flush as exit 2, and its caller discards stdout on that status even if the bytes form a document. General envelopes are serialized before printing, but their output path does not provide the same explicit write/flush refusal protocol. Interruption or failed output can leave no usable report after work has occurred. Missing output does not authorize replay or establish absence of effects. Durable runner cleanup state, when saved, remains separate from stdout.

This describes current mechanisms and limits; it introduces no universal exit-2 or durable-journal promise. If a universal explicit publication protocol is desired, it is a new public guarantee requiring writer changes, partial/flush failure controls and distinct execution/effect observations. Do not make such a change merely to simplify the tour. A new existing clause guaranteeing complete general publication on zero exit would require a closer writer/exit audit; the targeted public text identified by A does not currently make the example's explicit rule universal.

## X07 — Inspecting and closing the complete-error control gap

I read `suites/blackbox_e2e/checker_controls/artifacts/result-consistency-controls.json` from the fresh run using an in-memory JSON summary only. It contains 134 distinct controls, 189 recorded diagnostic strings and seven empty-error controls. This is current executed constructed-input evidence. It corroborates the intended result applicability; it does not close the initial control-completeness limitation.

Representative actual complete error sets are:

| Control | Recorded complete errors |
| --- | --- |
| `finished_exit_other` | `result.exit_code is 1, not 0 for the admitted reply outcome "finished"` |
| `finished_ok_integer` | `envelope.result.ok is number, not boolean`; `result.ok is 1, not true for the admitted reply outcome "finished"` |
| `finished_exit_boolean` | `envelope.result.exit_code is boolean, not number`; `result.exit_code is false, not 0 for the admitted reply outcome "finished"` |
| `finished_record_error_and_exit` | `result.exit_code is 2, not 0 for the admitted reply outcome "finished"`; `fs_write_allowed: missing comparison` |
| `profile_producer_False_refused` | `reply.compiled_profile.producer is boolean, not string`; `compiled_profile requires worker/before_apply context` |
| `rejected_delivery_failed` | `runner client transport admission disagrees with independent admission`; `rejected runner client capture lacks an admission error`; `runner client submission projection requires admitted complete capture`; `rejected client capture cannot supply host result or host-byte diagnostics` |
| `projection_differs_from_bytes` | `host result differs from exact captured host reply bytes`; all three result-field mismatches against captured `finished`, despite projected `worker_timeout` |
| `unsupported_reply_version` | One error: `unsupported runner response: contract 'test:next' (expected 'test:fixture')` |

The foreign-capture and truncated-reply controls have the same three consequence diagnostics as failed delivery, plus a more specific admission-disagreement reason. `rejected_reply_diagnostic` has only `complete parsed host bytes carry a host-byte diagnostic`. Absent reply and absent assessment with coherent result have no errors. The profile invalid-context variants have the semantic error and, only for Boolean/numeric fields, the applicable field-type error. These consequences are explainable from the input differences; they must not be discarded as noise or copied into expectations merely because they appeared in this run.

**Minimal correction design:** change only the owning `result_consistency_controls` oracle and its receipts initially. Leave `consumer.py` and semantic applicability untouched. Supply an independently authored expected complete error multiset per control family, in addition to the existing result-category requirement. Compare sorted lists or `Counter`s so an unrequested duplicate is not erased. Retain expected, actual, missing and unexpected diagnostics in the receipt.

The expectation table can be small:

- Four explicit baseline rows: `finished` → true/0; `worker_timeout`, `bad_request`, `unfamiliar_outcome` → false/1. These are test-authored expectations, never obtained through `_admitted_outcome` or another production classifier.
- Each result mutation names its intended result diagnostic. Numeric outcome/integer ok/Boolean exit/string exit/array result also name the exact structural diagnostic above. Missing/null result members currently add the semantic mismatch only; do not invent a shape consequence the actual declared optionality does not demand.
- Missing comparison contributes exactly `fs_write_allowed: missing comparison`, alone or unioned with the exit fault. Combined faults use the independent union and retain multiplicity; no broad “at least these” matcher.
- Profile cases explicitly state status/context expectations and required type diagnostics for the altered field. `None`/absent/future-string differ from Boolean/number in shape consequences. Valid captured/unavailable contexts still bind all three mismatched result fields; invalid context binds none.
- Each rejected capture names its full four-diagnostic set; reply-diagnostic-only names its one error. Projection disagreement names its byte/projection error plus all three result mismatches. Foreign reply remains exactly one version error. Empty-error cases require the empty set.

Do not generate this expected table from current `errors`, filter unknown errors away, accept arbitrary substrings, or share consumer semantic classification. Parameter substitution for an explicitly authored outcome/value is fine; a separate interpreter is unnecessary. Keep the CLI example aggregate exception local to that checker; it is not an exception for these direct consumer errors.

**Control that proves the matcher is sensitive:** factor only the test-owned expected-versus-actual comparison into a pure helper. Give it the independently literal error list for `finished_record_error_and_exit` above and require acceptance. Append the unrelated literal `unexpected diagnostic sentinel` to the actual list while keeping expected unchanged; require rejection specifically with that string in `unexpected`. Restore and require acceptance. Also remove the missing-comparison item and duplicate it in separate controls, requiring `missing` and unexpected multiplicity respectively. The helper's accepted result must not be used to derive expected consumer behavior.

For reachability through `control()` itself, temporarily substitute only that call's validator result with the same two valid expected errors plus the sentinel, or provide a narrow injected error-source argument in the test helper. Require the real `control()` call to reject the sentinel, not merely a helper unit test that its caller ignores. Keep this inside the existing checker-control case. No native run or production mutation is needed to demonstrate this oracle boundary. These are designs, not executed additions.

**Disposition:** a bounded test-coverage defect relative to this plan's complete-set requirement, not an observed consumer relationship bug and not a reason to reopen historical CLI prerequisite acceptance. Current raw receipts show the expected intended result failures and necessary companions; the missing piece is an assertion that excludes additional unplanned diagnostics. I would change this view if another executed wrapper is shown to enforce complete sets on these very 134 rows; the current local helper and receipt do not.

## X08/X09/X10/X11/X12 — Narrow factual dispositions

- **X08:** accept B's explicit reader-domain qualification. No claim that the Python consumer and Rust geometry gate admit identical domains should enter the tour. A capacity-only constructed refusal may expose differing judgments without proving a native producer emits it. No broad reader unification is justified by this review.
- **X09:** preserving merged `unconfirmed` and independent classifiers is coherent if explicitly accepted as the current meaning/maintenance choice. Do not infer semantic independence merely from separate code, or require shared classifier generation without a product decision. C raises no new counterexample to the merged vocabulary.
- **X10:** verify's admitted reply `pid` retains the reply's host-or-worker meaning; it is not universally `runner_subprocess.pid`. Remove/validate success describes command completion, with separate cleanup/validity fields. These are factual distinctions already documented, not grounds to introduce new administrative status semantics. Unknown inspection must still retain recovery.
- **X11:** the fresh evaluation cannot substitute for lost-reply controls or universal no-replay/native attribution evidence. Preserve the source/check-read limits on unchanged claims. No broad native rerun is requested.
- **X12:** accept both documentary corrections. `WORKER.md` currently labels the controller as associating external log candidates in its authored diagram and says it gathers them in prose; the inspected run path and B's read/launch inventory do not contain that operation. Replace with “Controller admits and assesses the reply, then publishes the envelope.” Retain the general prohibition on causal strengthening without portraying current log collection. The README's “one fallback per apply actor” should become “separate fallback checks for carried actor policy objects, in request order, before host mode admission is known,” while also describing the eligible whole-held-request helper call. Neither correction requires runtime change. A current reachable log collector or mode-filtering call would reopen these factual findings.

## Proposed adjudication

Retain current owners and mechanisms unless the maintainer chooses stronger success/attribution/degradation meanings. Settle X03, X04 and X05 with explicit wording rather than calling their existing agreement a defect or quietly resolving their public gaps. Correct X07's bounded oracle completeness and X12's inaccurate explanations. X02 is presently an observation-scope clarification, not demonstrated missing controller input enforcement.

The most consequential remaining choice is whether actor-labelled diagnostics certify only a retained row's local lifecycle consistency or also its association with the requested actor. Once that meaning is explicit, the success and degradation accounts can remain coherent without invented native evidence or blanket withholding. The single fresh evaluation supplies useful constructed and one-execution support; it does not decide that product question.
