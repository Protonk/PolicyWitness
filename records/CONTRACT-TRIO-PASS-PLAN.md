# Contract trio investigation plan

Three independent investigations will extend
[DOCUMENTATION-TRACE-REVIEW.md](DOCUMENTATION-TRACE-REVIEW.md). Their purpose is
to reduce the reconstruction needed by a team approaching that record: explain
relationships between existing findings, establish further consequences, and
identify new findings where the evidence warrants them. This work makes no
repairs, selects no authoritative layer and proposes no consolidation of the
findings.

The passes are:

1. Transport failure through public result and helper fallback: DT-31, DT-32
   and DT-42.
2. What acceptance actually establishes: DT-48, DT-50, DT-53, DT-61 and DT-95.
3. Whose observation a field records, and what time it describes: DT-46,
   DT-62, DT-63, DT-66 and DT-68.

The review also contains a completed wire-identity and projection investigation,
DT-105 through DT-112. Its findings are adjacent evidence, not a fourth pass.
Use the current record and source snapshot when executing this plan; historical
line numbers and recorded experiments retain their stated scope.

## Managing agent instructions

Manage the three independent investigations as an Opus manager. You will receive
the exact technical instructions below for each pass. Your responsibility is to
supervise the reasoning, interrogate the evidence and arrange independent
validation while preserving each report as its author's work.

### Delegate the supplied instructions verbatim

Assign one Opus investigator to each pass. Investigators must not delegate
further. Pass the entire text between that pass's `BEGIN EXACT INSTRUCTIONS`
and `END EXACT INSTRUCTIONS` markers verbatim. You may prepend and append
context, repository guidance, evidence locations, execution constraints and
logistics, including how you will check in and how drafts will be delivered.
Your additions must not override or narrow away the supplied investigation,
authorize repairs, or impose a common report structure. Subsequent questions
and evidence may be supplied in follow-up messages.

Use Sonnet agents afterward to validate the reports. Keep investigation,
validation and author revision sequential within each pass, with only one
subordinate actively working on that pass at a time. Validation is a bounded
check of the report, not a second investigation with an expanding remit.

### Become familiar with the substance yourself

Read the existing findings selected for all three passes and inspect enough
supporting material to question the investigators intelligently. Do not manage
solely through progress summaries.

Check in during tracing, before substantial experiments and when a draft is
available. Ask questions tied to particular claims, inputs, assertions and
source paths. Useful questions include:

- What proposition does this observation establish?
- Which boundary did the experiment actually cross?
- Is this production behavior, a constructed input, source inference or a
  design judgment?
- Does the cited test assert this relationship, or merely exercise nearby code?
- Could the apparent agreement come from shared generated inputs, defaults or
  the same expected-value computation?
- What would distinguish this explanation from a plausible alternative?
- What does the cross-reference add beyond topical similarity?

Challenge both overstated criticism and premature reassurance. Do not steer
investigators toward a common conclusion.

### Protect the investigative scope

These passes explain and extend the record. They do not fix behavior, revise
contracts, choose authoritative layers, propose implementation plans, prioritize
repairs or identify convenient groups to collapse.

Welcome observations about awkward, needless or misleading arrangements,
including arrangements faithfully implemented by code, tests and documentation.
Ask the investigator to explain the concrete interpretive or maintenance cost,
consider existing rationale and distinguish judgment from established behavior.

Permit nearby investigation when it could clarify a consequential relationship
or establish a new implication. Redirect broad surveys and repeated experiments
that no longer resolve a specific uncertainty.

### Manage relationships between threads without merging them

When one thread discovers evidence relevant to another, forward the precise
source, observation and its limitations. Treat emerging interpretations as
provisional.

If reports appear to contradict each other, investigate whether they concern
different inputs, snapshots, observers, boundaries or times. Return the question
to the authors. Preserve unresolved disagreements explicitly rather than
reconciling them through editorial wording.

Overlap is acceptable. A finding may illuminate several different questions.
Do not move material between reports, assign a single owner merely to eliminate
repetition, or ask authors to make their narratives fit together.

### Preserve evidence and execution boundaries

Follow the repository's [working rules](../AGENTS.md),
[record rules](AGENTS.md), [controller rules](../controller/AGENTS.md),
[runner rules](../runner/AGENTS.md) and [test rules](../tests/AGENTS.md), with
the applicable implementation and suite READMEs. Use
[planning guidance](../CONTRIBUTING.md#planning-a-change) and
[investigation verification guidance](../tests/CHANGE-VERIFICATION.md) for
evidence and handoff decisions.

Require reports to identify the inspected source snapshot, relevant build,
commands, inputs, decisive observations and availability of artifacts.
Distinguish fresh execution, retained evidence, source inspection and
constructed controls. Existing development outputs and scratch artifacts named
by the review are local, generally gitignored or temporary, and have no
retention guarantee. Check availability and applicability before crediting them.

Coordinate shared checkout use under repository locking rules. Serialize builds
and test executions in one checkout; use separate worktrees when concurrency
requires them. Keep investigative mutations isolated from the inspected
implementation and app. Do not repair the subject of investigation during
validation.

Inspect registered selections with `tests/run.sh --list`, then use fresh
`PW_TEST_OUT_DIR` destinations for executed cases. Select checks that can settle
the particular question. A direct probe does not become a registered case pass,
and a passing case does not establish every claim in its surrounding prose.

Require cross-references to identify their relationship: stronger evidence,
shared mechanism, different boundary, tension, consequence or unresolved
dependency. Citation existence alone does not establish support.

### Give Sonnet validators concrete validation assignments

Supply each validator with the complete authored draft, original pass
instructions and relevant artifacts. Ask for independent examination of
consequential claims and the evidence supporting them.

Validation should check:

- Whether quoted statements and source paths support the claimed behavior.
- Whether test assertions establish the credited scope.
- Whether experiments isolate the claimed distinction and retain an
  appropriate baseline.
- Whether claimed acceptance passed the actual named reader or only a
  narrower helper.
- Whether negative searches justify their stated scope.
- Whether new implications follow from the observations.
- Whether cross-references preserve differences and earlier evidence limits.
- Whether design criticisms identify a concrete cost without presenting
  preference as fact.

Validators must return a separate memo locating each concern in the report,
explaining what they checked and recording unresolved limits. They must not
rewrite, summarize or reorganize the report. A passing suite or agreement with
the author is not sufficient validation.

### Return substantive issues to the original author

Send validation concerns and your own questions back to the investigator. The
investigator owns corrections, qualifications, additions and withdrawals.

Require material unsupported claims to be corrected or explicitly left
unresolved. Allow authors to disagree with validators when they provide evidence
and reasoning. Obtain targeted revalidation where a consequential dispute
remains.

Do not impose a common template, tone, ordering, length or taxonomy. Shared
standards of evidence do not require shared report structure.

### Deliver the reports intact

Preserve original drafts, validation memos and author-revised final versions
separately under the existing evidence rules; this does not create a retention
exception. Deliver each final report in full, exactly as its author supplied it.
For this plan, append the three author-approved final reports intact to
`records/DOCUMENTATION-TRACE-REVIEW.md`, under neutral pass boundaries. Serialize
the appends and have authors apply any necessary final identifier assignments
before supplying their final text. Leave all existing findings unchanged.

Do not summarize, hybridize, deduplicate, harmonize terminology or add a
synthesis that makes the reports appear to form one argument. Do not silently
repair them yourself. Preserve their independently chosen structures and
conclusions.

Your accompanying note should be limited to provenance and validation status:
who authored and validated each report, what remains unresolved, and where the
evidence lives. Completion requires three intact authored reports, their
separate validation memos, and explicit disposition of material validation
concerns. A minimum number of new findings is not required.

## Exact investigator instructions: transport failure and helper fallback

<!-- BEGIN EXACT INSTRUCTIONS: transport -->

Investigate transport failure through public result selection and independent
helper fallback for `policy-witness run`. Start with DT-31, DT-32 and DT-42 in
`records/DOCUMENTATION-TRACE-REVIEW.md`. Establish the relationships between
these findings and any new consequences their joint trace reveals. Treat their
reachability claims and unresolved branches as questions to verify.

Answer three questions:

1. Which combinations of client capture, submission knowledge and host reply
   can reach execution admission and public result selection?
2. Which failed boundary determines the outcome, error, exit status and
   retained evidence when several problems are present?
3. Exactly what permits fallback compilation, what input each helper invocation
   receives, and what its result establishes for ordinary and actor requests?

Read the admission and capture statements in
`docs/contract/20-transport.surface.md`, result and fallback statements in
`docs/contract/40-envelope.surface.md`, relevant diagnostic statements in
`docs/contract/41-diagnostics.surface.md`, and helper admission in
`docs/contract/11-policy.surface.md`. Compare their complete presentations and
the operating accounts in `controller/README.md` and `docs/PolicyWitness.md`.

Trace `parse_runner_client_output`, `RunnerClientRun::failure` and
`fallback_eligible` in `controller/src/runner_client.rs`; `admit_reply`,
`fallback_policy_check`, `actor_fallback_checks`, `complete_execution` and their
callers in `controller/src/run_flow.rs`; public result selection in
`controller/src/interface/result.rs`; and capture construction in
`controller/src/policy_check.rs`. Follow the Swift client session and entry
point where needed to establish which client captures can actually be emitted.
Follow `controller/src/bin/sbpl-check.rs` for the helper's input and output
behavior. Keep client-capture admission distinct from host structural decoding,
host semantic admission and execution completion.

For DT-31, determine whether an execution-admitted result without a host reply
is reachable through the shipped caller, or only through internal constructors
and injected typed inputs. Trace the foreign-producer refusal before and after
typed construction: establish when a decoded host projection can exist and
when only rejected bytes exist. Check callers rather than treating a branch in
`admit_reply` or the result relation as proof of reachability.

For DT-32, examine whether `stdout_capture_error` or `stdout_parse_error` can
participate in the documented post-admission error precedence through the
production path. Trace reply-capacity or label refusal only far enough to
establish public result selection and diagnostic presence. Use explicit key
presence checks when distinguishing withheld diagnostics from a present null.

For DT-42, compare the held whole-request fallback with per-actor policy-object
fallback. Establish the bytes sent, resolved augments, actor association and
request order, including carried policy objects collected before host sandbox
mode admission. Determine the actor-form whole-request helper outcome and how
it coexists with individual actor captures. Examine helper launch/delivery
failure, malformed or empty output and compiler refusal only where they affect
the promised capture status, envelope, stderr or exit-code provenance.

Use a compact set of contrasts: a valid reply; an admitted client `xpc_error`
without host bytes; a nearby noneligible terminal such as acquisition failure
or timeout; malformed or unsupported client capture; and malformed or
foreign-contract host bytes. Add one combined-fault control that distinguishes
competing precedence explanations. Use ordinary and actor inputs for the
fallback-specific contrast. Choose existing seams and the narrowest execution
that can settle the uncertainty; separate typed injections from actual binary
decoding and controlled client output from a native XPC failure. Do not make
forced live reachability a prerequisite for reporting a source-established
limit.

Read the existing orchestration tests, including
`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`,
`refused_reply_versions_request_no_fallback_compilation`,
`actor_fallback_uses_held_policy_objects_before_host_mode_admission` and
`actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`.
Inspect their dependency substitutions and fixture decoding. Compare the
client's terminal controls and the `failure_boundaries/fallback_helper`
assertions with the claims credited to them. A helper-only admission refusal
does not establish the controller's complete fallback path.

Make the report usable by a reader reconstructing these boundaries. Explain
which earlier uncertainty has been settled, which paths remain source-only or
constructed, and what retained evidence supports submission knowledge. Keep a
helper compilation result separate from evidence of worker execution or policy
application. Investigate awkward agreement too: unreachable result vocabulary,
test fixtures that normalize impossible combinations, or several faithfully
implemented fallback reports whose relationship is hard to interpret are valid
leads if their concrete costs can be established.

Report disagreements, agreement caused by restricted fixtures or shared
assumptions, and questionable agreements whose rule itself deserves scrutiny.
Distinguish evidence from design judgment and consider existing rationale.
Explain each cross-reference rather than merely listing related identifiers.
Preserve affirmative observations and unresolved alternatives. Do not repair
code, tests or documentation, prescribe a replacement design, choose the correct
layer, propose merges, or expand into general reservation timing, BYOXPC
installation or import-inventory completeness. The deliverable is an
investigation report with its supporting evidence and limits.

<!-- END EXACT INSTRUCTIONS: transport -->

## Exact investigator instructions: what acceptance establishes

<!-- BEGIN EXACT INSTRUCTIONS: acceptance -->

Investigate the different propositions established by acceptance, validity and
successful completion. Start with DT-48, DT-50, DT-53, DT-61 and DT-95 in
`records/DOCUMENTATION-TRACE-REVIEW.md`. These findings concern different
boundaries; establish their relationships without treating all accepted
contradictions as one defect or assuming every reader should repeat every
check.

Answer three questions:

1. What proposition does each accepting boundary actually check, and over
   which representation of the evidence?
2. Which relationships are delegated, unchecked, contradicted or lost before a
   later reader can assess them, and what does the public result retain?
3. Where does agreement reflect a deliberate division of responsibility,
   restricted inputs or shared assumptions, or a questionable rule faithfully
   implemented by every layer?

Use these five anchors:

- DT-48: structural acceptance of a contradictory validator outcome/native
  return, successful completion, and separately withheld ordering credit.
- DT-50: canonical Unicode equality in Swift versus literal record identity
  in downstream association and ordering checks.
- DT-53: consumer acceptance of incomplete or incorrect lifecycle claims
  versus the lifecycle oracle's additional obligations.
- DT-61: a ready authority-setup decision without the recorded acquisition
  prerequisites, including the difference between decoder, scheduler and body
  reader checks.
- DT-95: compiled-profile status/label admission versus receipt presence,
  request association and relationships among the receipt's own fields.

Read the relevant statements in `docs/contract/21-wire.surface.md`,
`31-steps.surface.md`, `32-lifecycle.surface.md`, `34-equipment.surface.md`,
`35-profile.surface.md` and `41-diagnostics.surface.md`, all under
`docs/contract/`, together with the corresponding portions of
`tests/FAILURE-PROPAGATION-CONTRACT.md`. Treat statements assigning obligations
to a producer separately from statements assigning checks to a recipient.

Trace validator admission and association through
`runner/Sources/PWRunnerCore/ValidatorClient.swift`,
`PWRunnerPredictionEvidence.swift`, `PWRunnerStepEvidence.swift`,
`CWorkerStepResults.swift` and `CWorkerDisposition.swift`. Trace setup through
`AuthoritySetupRuntime.swift`, `PWRunnerAuthoritySetup.swift`, the scheduler and
the applicable reply validation. Trace receipt context through
`PWRunnerProfileCapture.swift` and its reporting check. These Swift files are
under `runner/Sources/PWRunnerCore/` unless otherwise stated.

Follow the corresponding Rust checks in
`controller/src/porcelain_admission.rs` and `porcelain_actor.rs`, their use by
`run_flow.rs`, and result selection in `controller/src/interface/result.rs`.
Follow Python checks in `tests/lib/consumer.py`, `phase_evidence.py`,
`actor_evidence.py`, `extension_evidence.py`, `lifecycle_adapter.py` and
`lifecycle_oracle.py`. Determine which of these are actually invoked on each
tested path. An available checker is not necessarily a checker the caller ran.

For each anchor, reconstruct the sequence from raw or constructed input to
producer validation, binary structural reading, context admission, semantic
findings, JSON projection and outer result, where those stages apply. Identify
whether a failure rejects the whole reply, withholds a particular assessment,
adds a diagnostic, changes completion, or has no further checked consequence.
Do not assume that similarly named admission functions perform equivalent work.

Inspect the exact assertions cited by each finding. Select small controls that
settle uncertainties in this sequence: coherent and incoherent native-return
records with and without an ordering claim; equivalent Unicode spellings used
as record identities; a missing or changed lifecycle answer; ready setup with
a missing or failed prerequisite; or a receipt with valid labels and a changed
association. Reuse applicable observations where their dependencies are
established; new experiments should answer an unresolved question rather than
repeat the entire earlier pass.

Keep whole-envelope checking distinct from bare-reply and helper checking. A
saved JSON edit rejected because it differs from retained host bytes does not
establish rejection of its semantic relationship. Conversely, acceptance by a
body helper does not establish acceptance of a complete captured envelope.
When a claimed disagreement depends on actual frame admission, compare the
same frame through the applicable readers or state why only a narrower
constructed path was exercised.

DT-108 is a nearby lead: conditional-null projection can hide a carried
dependent, leaving Rust's typed semantic checks and Python's projected checks
with different information. Follow it only where it clarifies one of the five
anchors or establishes a consequential additional relationship. Do not repeat
the wire-fingerprint investigation or turn this pass into an exhaustive schema
audit.

Explain the checking responsibilities and their consequences so a teammate can
distinguish deliberate delegation, missing enforcement of a stated obligation,
and agreement that rests on a questionable obligation. An annotated map or
table may help, but choose the form that best supports the investigation.
Describe where differently named successful results establish different things
and where identical results obscure different checked propositions.

Report disagreements, accidental agreement and awkward or needless agreement.
An unchecked relationship is not automatically a requirement to add another
check: state the promise, the actual checking scope and the practical
interpretive cost. Consider existing rationale and label design judgments.
Make cross-references explanatory and preserve the scope of each earlier
finding. Do not repair readers, strengthen tests, revise meanings, design a
unified validator, assign fixes to a layer, or propose findings to collapse.
The deliverable is an investigation report with its supporting evidence,
affirmative results and remaining uncertainties.

<!-- END EXACT INSTRUCTIONS: acceptance -->

## Exact investigator instructions: observation ownership and time

<!-- BEGIN EXACT INSTRUCTIONS: observation-time -->

Investigate whose observation a returned field records and what time it
describes. Start with DT-46, DT-62, DT-63, DT-66 and DT-68 in
`records/DOCUMENTATION-TRACE-REVIEW.md`. Follow the acquisition, publication,
collection and final representation of their facts. Preserve the differences
between events, derived summaries, resource ownership accounts and observations
of effective access.

Answer three questions:

1. Who observes each fact, at which operation or publication boundary, and
   which later values are derived from the same observation?
2. What temporal claims survive into the final reply, and what information is
   withheld, overwritten, merged or retained only internally?
3. Which combinations of individually accurate fields invite an unsupported
   inference about timing, independence, current ownership or authority?

Use these five anchors:

- DT-46: the described cleanup-trigger capture at the exit-request store
  versus its derivation from the stop reason during final collection.
- DT-62: host-accepted custody that does not appear as acceptance in the final
  reply when the issue slot remains unpublished.
- DT-63: last-transfer erasure and teardown erasure producing the same final
  flag, with a test crediting a particular retirement point.
- DT-66: distinct logical handles sharing one native value, with separate
  consume/release events and observed fresh-read boundaries.
- DT-68: worker mapping ownership reported as held alongside host-observed
  termination and separate host resource cleanup.

Read the relevant custody and retirement statements in
`docs/contract/14-extensions.surface.md`, lifecycle and actor statements in
`32-lifecycle.surface.md` and `33-actor_evidence.surface.md`, and setup/ownership
statements in `34-equipment.surface.md`, all under `docs/contract/`. Compare
their REQUEST, RESPONSE and ARCHITECTURE presentations with `docs/WORKER.md`,
`docs/EXTENSIONS.md` and the relevant observation and cleanup claims in
`tests/FAILURE-PROPAGATION-CONTRACT.md`.

Trace `ActorSession.requestExit` and `collectOutput`, scheduler stop/cleanup
ordering, `AuthorityCustody.serviceOutbound`, `serviceTransfer` and `finish`,
`decodeAuthoritySetup`, and `assembleActorReply`. These implementations are in
`runner/Sources/PWRunnerCore/ActorSession.swift`, `ActorScheduler.swift`,
`AuthorityCustody.swift`, `AuthoritySetupRuntime.swift` and
`ActorOrchestration.swift`. Follow the C issue, transfer, consume, release and
exit paths in `controller/tools/pw_probe_runner/pw_probe_runner.c` and its
authority headers, including the relevant publication words and test seams.
Inspect downstream ownership and cleanup assessments only where they use the
facts being traced.

For each anchor, distinguish the native operation, its return, the publication
that authorizes reading it, independent host observations, assembly decisions
and final public fields. Record the producer of each fact and its observation
interval. Determine whether two fields are independent observations, copies or
derivations of one stored value. Logical declaration identity, native numeric
equality, token-byte custody, memory erasure, native release, mapping lifetime,
process reap and effective file access must retain their separate meanings.

Examine which distinctions a final snapshot cannot recover. For cleanup,
determine what establishes the claimed trigger and its recording time. For
interrupted issue, locate the independently observed custody state and the
assembly condition that prevents its publication. For erasure, distinguish
evidence of eventual clearing from evidence that clearing happened at the
declared last use. For handles and mappings, determine whether final statuses
describe historical production/publication or resources presently usable after
the reply.

Read the cited assertions in `ActorAuthorityTests.swift`,
`ActorReplyTests.swift`, the cleanup-cause tests in
`controller/src/porcelain_admission.rs`, and the relevant extension controls in
`tests/suites/witness_contract/` and `tests/fixtures/extension_controls/`.
Check whether an asserted final boolean or constructed claim can establish the
specific recording point, independence or lifetime credited to it. Follow
existing erasure observers far enough to identify exactly which memory extent
and interval they inspect.

Use bounded contrasts where they distinguish competing explanations: observation
before and after final teardown; accepted host custody with an unpublished issue
slot versus a published slot; or different release boundaries for equal native
handle values. Preserve the distinction between actual native calls and
constructed publications or substituted returns. A driver that exposes an
internal custody observation is not a public CLI response. A successful native
release is not by itself proof of revocation; an erased buffer is not proof of
released authority; process absence does not establish the disposition of every
descendant or separate host resource. Use the supporting observations needed
for the particular claim, without expanding into a general native-library or
descendant-lifetime investigation.

Explain how the findings constrain one another's interpretation. In particular,
investigate whether the record hides an independently observed fact in one
place while describing a derived value as independent elsewhere, and whether
historical ownership labels consistently encourage an unsupported present-tense
reading. These are questions, not assumed conclusions or a demand for a common
state model. A compact timeline and precise terminology may reduce the next
reader's reconstruction effort; choose the report's form independently.

Report disagreements, apparent agreement produced by final-state-only tests,
and arrangements that seem misleading or needless despite agreement across
layers. Establish the concrete cost and consider existing rationale before
offering a design judgment. Explain cross-references and keep the experimental
scope of each finding intact. Do not fix recording points, add fields, propose
a unified lifecycle representation, change erasure or release policy, choose
an authoritative layer, or suggest findings to merge. The deliverable is an
investigation report with its evidence, affirmative observations and unresolved
limits.

<!-- END EXACT INSTRUCTIONS: observation-time -->
