# Result-reading ownership map

Pass 1 of [DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md), baseline
`9eb81540`; mapping only. Meanings and ownership below retain the approved semantics.
Actual dispatch model: `gpt-6.1-sol`, fresh context, confirmed by the coordinator;
review used local source reads only.
No commands executed tests or builds; all assertions below have check-read or
source-read support, with constructed inputs distinguished from native production.
Original controller execution evidence was pruned; no retained execution is credited.

## Completion success

- Canonical public nodes in [40-envelope](../../docs/contract/40-envelope.surface.md):
  `envelope.data.select` (including `.finished` and `.other`) owns the admitted
  exact-`finished` true/0 mapping; `envelope.data.success_findings` owns its
  independence from attempts and relationship findings. `envelope.result.ok`
  and `.exit_code` are field meanings, not alternative classifiers.
- [30-reply](../../docs/contract/30-reply.surface.md) `reply.record.outcomes`
  owns what the host commits to with `finished`; `reply.record.assemble` owns
  ordinary worker-before-validator precedence and actor aggregation.
  `diagnostics.execution.outer_result` in [41-diagnostics](../../docs/contract/41-diagnostics.surface.md)
  already delegates completion to `envelope.data.select`.
- Acting components: host classifies execution/collection; controller selects
  outer result after admission and computes diagnostics separately. Prose owner:
  contract for these commitments; controller tour for the separation mechanism;
  guide for deciding what to read next.
- Current presentations: guide `#what-success-means`, `#normalized_outcome-catalog`,
  exit table under `#output-envelope`; tour `#selecting-a-result-and-publishing-it`.
  The failed-open example and true/0-versus-findings statement repeat facts;
  the guide's reading order and operation-level interpretation are audience work.
- Read assertions: `controller/src/run_flow.rs::complete_execution` computes
  diagnostics separately and compares only exact `finished` for true/0.
  `typed_completion_preserves_native_failure_beside_finished_summary` asserts
  exit 0, preserved rc -1/errno 1 and unchanged typed reply after projection.
  `malformed_phase_claims_withhold_projection_and_preserve_raw_reply` asserts
  ordinary malformed ordering yields withheld/invalid/unknown, preserved raw
  reply and exit 0; degraded branch exits 1 and omits phase-collection findings.
  These constructed checks do not establish native production of contradictions.
- Read source: `runner/Sources/PWRunnerCore/CWorkerDisposition.swift::classify`
  tests worker publication/application/completion and lifecycle before required
  validator collection; validator success needs clean reap, usable complete
  association and no transport/decode faults. Do not substitute this ordinary
  algorithm for the separately owned actor aggregate ladder.
- Treatment: KEEP normative definitions and field links; SHORTEN tour to the
  mechanism plus contract link; KEEP guide's short failed-attempt example and
  explicit integrity-check instruction. LINK catalog/exit summaries back to the
  guide explanation. Do not extract the classifier ladder into the guide.

## Actor withholding

- Canonical nodes in 41: `diagnostics.execution.reply_checks` owns aggregate
  withholding and actor assessment retention; `diagnostics.issue.subject.withholding_scope`
  owns the carried-row attribution limit; `diagnostics.actor.projection.lifecycle_check`
  and `diagnostics.actor.projection.lifecycle_check.local_failure` own worker-local
  withholding. `diagnostics.execution.families`
  assigns the families and applicability. `diagnostics.issue.subject_path` owns
  assertion location independently of withholding scope.
- Canonical node in [33-actor_evidence](../../docs/contract/33-actor_evidence.surface.md):
  `actor_evidence.actor.reader_scope` owns carried-reply versus original-request
  checking; `.account` owns host assembly and distinct preparation/refusal forms.
- Actor: controller selects actions from carried phase actor labels/action IDs,
  projects each subprocess, then applies reply-wide findings. Host owns
  request-to-reply assembly. Public prose belongs in the contract; implementation
  ordering/rationale belongs in the tour; guide explains how to inspect findings.
- Presentations: guide `#how-the-controllers-findings-qualify-the-report` scope
  table and subject-path paragraphs; tour `#receiving-and-evaluating-evidence`;
  41 repeats the attribution limit in `.reply_checks` and `.withholding_scope`.
  Field vocabularies, table consequences and path examples serve different needs;
  full attribution-limit paragraphs repeated in contract are one fact.
- Read source: `controller/src/porcelain_admission.rs::execution_diagnostics`
  selects first matching step/event by carried ID, projects actors before
  `admit_reply`, and preserves actor rows when later findings withhold aggregate.
  `project` returns withheld/invalid/unknown on lifecycle findings.
  `typed_invalid_actor_account_keeps_independent_actor_endings` constructs an
  invalid actor account and asserts withheld aggregate plus retained clean-exit
  actor rows; it does not test sound attribution for every identity/PID/action fault.
- Drift: guide table says rows “remain available independently”; without the
  contract/tour caveat this can imply independent actor attribution. CORRECT to
  “remain as projections of the carried rows; identity/launch/action findings
  still qualify them.” Keep this limitation locally beside retention.
- Treatment: KEEP `.withholding_scope` as the precise limit; SHORTEN
  `.reply_checks` repetition to a reference without losing its effect/order;
  KEEP guide scope table and compact caveat; KEEP tour's selection/join mechanism
  and constructed-control limit. Do not broaden withholding or recertify rows.

## Reporting degradation

- Canonical nodes in 30: `reply.failure.publish` owns validation/encoding, rich,
  minimal and empty-byte fallback sequence; `reply.failure.evidence_retained`
  and `reply.failure.associations` own retention and association meanings;
  `reply.failure.publish.summary`, `.rich`, `.minimal` and `.producer` own the
  reporting effects.
  33 `.actor.reader_scope` owns actor reader applicability; 41
  `diagnostics.execution.families` owns remaining worker checks and waived
  removed-comparison requirement. These are different boundaries, not duplicates.
- Acting components: host validates/writes fallback; controller admits geometry
  and profile context, then checks degradation form and retained worker lifecycle.
  Canonical prose belongs to contract; guide owns salvage/interpretation advice;
  tour owns branching and writer rationale.
- Presentations: guide `#what-a-reporting-failure-preserves`, catalog entry
  `runner_reporting_failed`, `#reading-a-comparison-record` item 1; tour
  `#receiving-and-evaluating-evidence`; 30 associations and 33 reader scope.
  Rich/minimal summaries repeat facts; comparison-reading warning is locally
  necessary because retained raw ordering cannot recover `query_first`.
- Read source/checks: `PWRunnerService.swift::pwRunnerReportData` catches both
  validation and encoding, removes comparisons in rich copy, tries minimal then
  empty bytes. `ReplyFailureTests.swift::runReplyFailureTests` asserts constructed
  defects bypass normal writer, preserve all other projected fields, and remove
  comparisons; invalid profile context reaches minimal. Rust `admit_reply` runs
  ordinary phase/native/actor families only without reporting failure;
  `typed_degradation_never_certifies_surviving_comparison` rejects a surviving
  comparison, accepts its removal and preserves attempt. No native occurrence credit.
- Drift: guide says “If host encoding fails” and catalog “could not encode”;
  CORRECT both to validation or encoding, as the contract and source specify.
- Treatment: KEEP fallback sequence and applicability in existing canonical nodes;
  SHORTEN tour's repeated field enumeration; KEEP guide rich/minimal distinction,
  no-comparison warning and lifecycle/applicability limits. LINK catalog to the
  guide subsection. No new extraction or generator is required for this map.
