# C — final boundary review

## Review scope and present disposition

Reviewed integrated source `424f3c73` against frozen originals `079b7cd7`, including the new controller tour, navigation and X12 corrections, authored/public contract changes, X07 checker diff and source-drift registration. Read the integration crosswalk and accepted M01–M05 dispositions against C01–C12 and the cross-examination. Generated public JSON was additionally compared in memory by surface/node ID, distinguishing local changes, shared referenced views and unchanged history; this avoids mistaking reordered/removed generated copies for independent deleted obligations. No tests, builds, source edits, worktrees, services or helper agents were used by C.

**Source-review disposition: no consequential unresolved boundary objection.** One already identified factual wording correction remains: CONTROLLER's actor-selection sentence should say “carried actor labels and each matching phase's action IDs,” not imply phase IDs participate in that selection. This is consistent with B's reported correction and changes no meaning or code. Final receipt review is recorded separately below when the coordinator reports the consolidated run complete.

The frozen originals remain unchanged. The public policy choices raised by C06/X03–X05 now have explicit maintainer acceptance; they are not unresolved objections that require stronger native behavior.

## Challenge dispositions

| Original challenges | Final account and review judgment |
| --- | --- |
| C01 admission/refusal ordering | The tour distinguishes identity gating before selector/augment interpretation from earlier environment/provenance reads. Target-resolution failure precedence is explicit. It does not turn the controller gate into host grammar admission. Retain. |
| C02 held bytes and mutable environment | Held request, held actor policy objects, separate imports and selected binary observations have separate scopes. Eligible whole-request and carried-policy-object fallback is stated before host mode admission. No frozen filesystem or exact signed pipe/host receipt is claimed. Retain. |
| C03 example origin/admission | Same-build admission promise, no native-success promise, source-owned constant, test callback equality and signed pipe-count evidence remain distinct. Host grammar is still the downstream owner. Retain. |
| C04 invocation uncertainty | Acquisition retries and execution invocation are separate; the original deadline is not reset; invoked is not receipt/effect; absent capture does not establish not_invoked. No safe caller replay, rollback, cancellation or total-return-time guarantee appears. Retain. |
| C05 rejected evidence | Ordered delivery/capture/frame/producer/context admission and retention of uninterpreted bytes are described without fallback semantic recovery. Fallback eligibility is qualified separately by admitted xpc_error and successful delivery. Retain. |
| C06 actor/degraded/result contradictions | M01–M03 now explicitly retain host-completion success, row-scoped actor projections and degraded-form checking. Attribution/ordinary joins are not independently certified by a local clean ending or retained fallback. Raw evidence remains retained. With the small selection-wording correction, retain. |
| C07 result consistency | The consumer remains unchanged, retains independent applicability and exposes its geometry-domain limit. X07 now requires complete independently authored error multisets with actual control-route sensitivity. Source approval remains as in C-ORACLE-REVIEW; execution credit awaits the final receipts below. |
| C08 effects without publication | Missing worker publication, missing reply and missing public envelope remain uncertainty boundaries. No native result is reconstructed from external effects or absent records. Retain. |
| C09 equipment scope | Recorded entitlement read-back, selected file metadata and later host live actor inspection remain separate. No effective privilege proof is inferred from a role, path or signature. Retain. |
| C10 cleanup | Pending ownership before actions, current service/plist checks, immediate plist recheck, observed absence and saved retirement remain distinct. Remove/validate success is not cleanup/validity success. No foreign-prefix or native-resource cleanup authority is invented. Retain. |
| C11 output | Example's explicit write/flush/exit-2 discard rule remains command-specific. General println output does not acquire that stronger guarantee or downstream durability. Architecture's former “envelope whatever host does” overstatement is corrected. Retain. |
| C12 secondary evidence | Independent compile cannot establish worker progress or lost-reply cause. Worker tour's unsupported active log-gathering description is removed. Operation-specific native evidence and PID meanings remain distinct. Retain. |

## Public changes and evidence honesty

The five accepted gap-to-definition changes are meaning decisions with explicit authority, even though runtime bytes and owners remain unchanged. The two sibling relocations are recorded: `envelope.data.select.success_findings` becomes `envelope.data.success_findings`, and `reply.failure.publish.associations` becomes `reply.failure.associations`. The current tour links to the new nodes. The new contextual prose preserves the operative result and preservation rules; it does not erase raw evidence or make existing checks optional.

The inspected public snapshot changes are confined to the accepted definitions, carried/request distinction, actor attribution language and consumer-domain qualification, plus their generated shared-reference effects. History and format compare unchanged. The broad shared-view diff is not evidence of an implementation change. Authoritative generation/history/shape validation remains the coordinator's consolidated check, not a consequence of this JSON comparison.

`INTEGRATION.md` retains the 56 initial families and distinguishes initial inventory wording from accepted final dispositions. Its old references and open-choice text are identified as original inventory history; current accepted-node realization and decisions govern the final account. The crosswalk does not claim that source citations or one combined evaluation execute every native family. I reviewed it for C's consequential boundaries, not as a fresh independent proof of every native numeric predicate.

M02's row scope addresses the concrete launch-PID and action-join challenges without pretending the constructed tests establish every contradictory producer path. M03 preserves the useful reporting conflict rather than forcing ordinary association validity onto degraded evidence. M04 keeps underlying host states while merging the controller vocabulary; M05 does not equate separate source code or shared schema with universal semantic independence. No additional product permission is needed to retain these accepted choices.

The tour and suite account distinguish constructed interpretation, source support and native observation. The previous evaluation's single ordinary example is not credited for actor misassociation, lost execution replies, output interruption, cleanup races or all capacity inputs. No new spontaneous native-failure evidence is claimed. The unchanged worker wait/release/eligibility mechanism does not trigger the conditional order-barrier mutation requirement. No broad native rerun is required solely to explain unchanged source paths.

## X07 final source check

The integrated X07 diff matches the reviewed implementation: literal semantic expectations, explicit structural/profile/capture companion tables, `Counter` differences in both directions, and full expected/actual error retention. The five test-owned sensitivity calls go through `control()` itself, substitute only its diagnostic source, require baseline/restoration acceptance and extra/missing/duplicate rejection with exact differences. They remain separate from the 134 real consumer-input controls. This fixes the originally identified oracle-completeness issue without changing consumer/runtime semantics or creating another interpreter.

A test name or pass total alone cannot close X07. Final receipt inspection must show all ordinary expected/actual multisets match and the five sensitivity records contain only their independently expected differences. Until that inspection, this section grants source-review approval only.

## Consolidated evidence

Pending coordinator completion notification for `tests/out/runs/controller-authority-verification`. No active/incomplete output is credited as a final result. This section will receive a scoped addendum after receipt inspection; no original report will be rewritten.

### Final evidence addendum and disposition

After the coordinator's completion notification, I read `run.json`, the
`blackbox_e2e/checker_controls/report.json`, both result-control receipts and
the CONTROLLER entries in the planner-control receipt from run
`20261113T155111Z_8ba29955`, executed at `424f3c73`. The run summary records
11/11 passing cases, zero failures/skips, and valid unchanged app inventory;
the checker case report is pass. The coordinator separately reports no
unrun/harness/sleep conditions. This grants no new native failure-path credit.

The independently inspected result receipts establish:

- `result-consistency-controls.json`: 134 unique controls and 189 retained
  diagnostic strings. Every row has empty `missing` and `unexpected` lists.
  An independent in-memory `Counter` comparison of each recorded
  `expected_errors` and `errors` also found no difference. This is execution
  of the new complete-multiset predicate, not reuse of the old category-only
  pass. Source review already checked where those expectations originate.
- `result-oracle-controls.json`: five separate rows. Baseline/restored have
  matching two-message lists and no difference. Extra retains exactly the
  unrelated `unexpected diagnostic sentinel` as unexpected. Missing retains
  exactly `fs_write_allowed: missing comparison` as missing. Duplicate retains
  exactly one extra copy of that comparison diagnostic. The reviewed caller
  requires rejection on the three damaged rows and acceptance on the two
  neighbors; the passing case and exact receipts show the intended boundary,
  not a generic earlier failure. These substitutions test the oracle route,
  while the 134 ordinary rows exercise the real consumer.
- `source_drift/runner_source_manifests_agree/artifacts/planner-controls/controls.json`:
  all five CONTROLLER scenarios have `problems: []` and an evaluated
  `known_gap_index` rule. Unindexed and spurious-index mutations each produce
  exactly the `known_gaps.index_order` diagnostic naming CONTROLLER; missing
  final heading produces `known_gaps.final_section`; indexed and restored
  variants produce no records. Thus the added document is actually exercised
  by the structural mutation family, not merely registered by name.

BR01 is now corrected in the working tree. I inspected its exact diff from
`424f3c73`: only the two-line sentence changes from “carried actor labels,
phase IDs and action IDs” to “carried actor labels and each matching phase's
action IDs.” This matches the traced `execution_diagnostics` action selection.
It changes no heading, link, span, fence, known-gap marker, executable source,
test or generator. I accept the coordinator's reviewed applicability exception
under `tests/AGENTS.md`: the executed structural mutations and result controls
remain applicable to this factual prose correction. This is a specific
applicability judgment, not a claim the corrected bytes were executed in that
run. A third run would add no discriminating observation for this delta.

**Final C disposition: accept.** C01–C12 are resolved through accurate retained
limits, explicit M01–M05 decisions, documentary corrections and the executed
X07 oracle fix. No consequential objection or C-requested experiment remains.
Raw output is local/disposable and may be pruned through the repository's
normal cleanup procedure after the other reviews. This record preserves its
provenance and scope without retaining a private copy or claiming future raw
availability. Frozen originals were not edited.
