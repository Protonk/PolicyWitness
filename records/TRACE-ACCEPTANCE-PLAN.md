# Trace acceptance plan

## Scope and dependencies

Assess whether the selected documentation arrangements require fewer independently
maintained judgments about the same rule. This supplies evidence for the
[management plan](TRACE-MANAGEMENT-PLAN.md), which owns product decisions,
implementation authority, the editorial freeze, sequencing and outflows. It adds
no numerical threshold or completion gate. An inconclusive rehearsal creates no
obligation to extend the investigation.

Rehearse before changing the thread's accounts. Use one hypothetical and trace
across management, this plan and the [overhaul](TEST-OUTCOME-OVERHAUL-PLAN.md),
including enforcing tests and credited claims. Apply justified arrangement
changes with the thread's product/account edits after its management assessment.

A judgment is independently maintained where someone must choose or reconstruct
a rule's meaning, scope or consequence without a dependable relationship to its
owner. Compare scoped propositions: who establishes what, at which boundary,
for which inputs/recipients, under which conditions and with what consequence.
Include observation time and representation where material. Ask whether one
proposition could change while the other remained true; similar wording does
not establish sameness.

## Rehearsals

### Actor fallback

Rehearse removing both whole-request and per-actor automatic compilation while
retaining ordinary fallback and standalone `sbpl-check`. Specify omission, null
or diagnostic treatment of `policy_check` before tracing consequences.

Follow the [helper](../docs/contract/11-policy.surface.md),
[envelope](../docs/contract/40-envelope.surface.md) and
[dossier](../docs/contract/42-dossier.surface.md) accounts, CONTROLLER,
ARCHITECTURE and the limits on accumulated output. Distinguish selection from
input provenance, output presence and accumulation consequences. Identify useful
observations and consumers that removal would lose.

### Capture despite failed application

Rehearse reporting valid pre-application captured bytes when application fails.
The [receipt surface](../docs/contract/35-profile.surface.md) and
[decodeProfileCapture](../runner/Sources/PWRunnerCore/CWorker.swift) require both
successful application and clean completion; changing only one guard is
insufficient. Identify eligible failure paths and retained publication, identity,
integrity and collection requirements. Keep capture, application, host
qualification and controller admission distinct. Trace repeated application
requirements through technical surfaces, architecture prose and data.

### Validator association equality

Rehearse byte-exact equality for validator identifiers and query metadata,
holding request-name uniqueness and submitted-target comparison fixed. Follow
[step](../docs/contract/31-steps.surface.md) and
[lifecycle](../docs/contract/32-lifecycle.surface.md) association, cardinality and
eligibility into readers and host outcomes. Preserve the distinction from
submitted-target canonical Unicode equality and path-compaction UTF-8 equality;
an inconsistency with another boundary needs a separate product decision.

### Rehearsing a migrated test seam

Rehearse retiring validator substitution while retaining ordinary validator
execution. Use the overhaul's [caller map](TEST-OUTCOME-OVERHAUL-PLAN.md#selected-seam-callers).
Trace current and migrated arrangements through command definitions/help,
admission, transport, native inputs, evidence, callers, assertions and accounts.
Distinguish independent availability/meaning decisions from transmission or
rendering. Include unreached interventions, remaining controls and the distinct
ordinary/actor timeout behavior. Update the comparison against the implemented
arrangement; include added flag, adapter, provenance and publication-boundary
maintenance.

## Compare arrangements

For each rehearsal:

1. Record the inspected revision, changed premise, behavior held fixed and
   concrete reader questions. Credit source reading, drafts and executed
   experiments separately; identify local or gitignored evidence.
2. Start with the [surface tree and presentation map](../docs/contract/README.md).
   Trace affected manual accounts, generated views, examples, support and tests.
   Distinguish restatement, dependent consequence, specialization, explanation,
   evidence and rendering. Identify the premise and additional reasoning behind
   each relationship; keep uncertain relationships visible.
3. Compare a plausible arrangement under the same hypothetical and reader
   questions. Hold guarantees, audiences, failure cases and useful explanations
   fixed unless management separately assesses a product change. Seek independent
   premises within this mechanism, not a repository-wide proposition registry.
4. Name the decision expected to disappear and trace it through definitions,
   generators, accounts, tests and readers. Search beyond declared dependencies
   for missed or unnecessarily affected statements. Check supposedly unaffected
   claims. Count continuing semantic review even where no edit is needed.
5. Account for work removed, retained or displaced into generators, applicability
   rules, adapters, navigation and reader inference. Compare the same reading
   paths before and after. A further hypothetical may test generality where
   useful; no fixed number is required.

Keep independently authored oracles where they provide scrutiny. Generated
agreement establishes consistency, not independent evidence. Shared terminology
must not conceal different observation scopes or obligations.

Where several documents require coordinated explanation, identify the purpose
of the underlying states, representations and responsibilities and what their
removal would lose. Assess product simplification separately from editorial
reorganization.

## Record the judgment

State the compared scope, decisions removed or retained, evidence for that
classification, remaining review duties and where work moved. Distinguish
observed results from predicted savings. File/word counts or successful
regeneration cannot substitute for the identified decisions and dependencies.
Retaining distributed accounts or rejecting consolidation is permissible.

Give management only resulting user obligations and their evidence; hypothetical
obligations and guide comparisons do not belong in the user outflow. Apply its
[retention rule](TRACE-MANAGEMENT-PLAN.md#material-reserved-beyond-this-work):
lasting reasons belong with the suite or technical owner, shared principles in
working guidance. Before sharing a rationale across suites, distinguish one
shared premise from separately justified boundary obligations.

## Preparation rehearsals — 2026-11-17

Status: source-based hypothetical rehearsals at `887b485f`, before any account
or product change in these threads. Implementation files are unchanged from
the planning snapshot `3d3f8e65`. These are dependency and meaning comparisons,
not executed equivalence or observed maintenance savings. Evidence availability
and the one bounded survivor disposition are in the management plan. No guide
errata or substitute guide prose is produced.

### One actor-fallback trace

Hypothesis: remove both whole-request and per-actor automatic compilation for
actor requests, keep ordinary fallback and standalone `sbpl-check`, preserve
`data.policy_check` as present-null for actor envelopes, and omit
`actor_policy_checks`. Preserve transport result, admitted client capture and
any host bytes. Those explicit presence choices are part of this hypothetical,
not decisions already applied to the product.

The questions are whether a helper ran, which bytes it received, what its
capture establishes, and what observations disappear. `run_flow.rs` holds one
request serialization after normalization and runner-selector removal.
`fallback_policy_check` uses admitted client-terminal `xpc_error` eligibility;
`actor_fallback_checks` additionally iterates held policy objects. The current
whole actor request has no top-level helper policy and its helper decode fails;
the per-actor calls can compile independently. The eligibility condition does
not establish worker progress or cause of the lost reply. The review's DT-116
reachability qualification matters: the typed admitted branch contains helper
calls but cannot supply this combination through the shipped client path.

| Reading/implementation path | Meaning under the hypothetical |
| --- | --- |
| `11-policy.surface.md` fallback and helper subjects | Standalone helper grammar, limits, result and capture remain. Automatic invocation applicability narrows to ordinary form. Helper capture is still independent compilation. |
| `40-envelope.surface.md` execution fields and result selection | Actor `policy_check` becomes present-null and the per-actor field is omitted. Result/error precedence and available transport evidence are unchanged; independent helper success never repairs transport failure. |
| `42-dossier.surface.md` held request/input rules | The whole held serialization continues to bind ordinary delivery/fallback. Actor delivery still uses held bytes; the extra per-policy serialization and later helper import walk disappear. Dossier import observations still precede the worker's independent reads. |
| CONTROLLER/ARCHITECTURE and `architecture.json` | Actor helper launches and their accumulation cost disappear from inventories and explanations. Ordinary and standalone launches remain. Current invocation counts cannot stand in for byte/input provenance. |
| `run_flow.rs` tests and capture readers | Rewrite only actor helper-selection expectations. Keep independent checks of submitted form, actual input bytes/calls, capture presence, retained host/client bytes and side effects. A fake client callback is not shipped-client reachability evidence. |
| Limits and support | Per-capture bounds stay true; total automatic actor helper accumulation changes. Generated tables only render the owning condition; authored descriptions need semantic review even where their text remains true. |

A plausible arrangement states automatic invocation applicability once in the
fallback subject and routes the field-presence and dossier consequences to
their existing owners. The removed decision is whether actor requests invoke
the helper, repeated in mechanism prose and tests that currently imply helper
invocation proves input provenance. The field-presence rule, source-ownership
rule and resource-bound consequence remain independently maintained because
each could change while invocation eligibility stayed fixed. Generating all
three from a single Boolean would conceal that distinction. Lost observations
are independent actor-policy compile captures and their later import scans;
keeping ordinary/standalone helper access does not preserve those automatic
observations. No product disposition selecting this loss is credited here.

### One captured-profile trace

Hypothesis: publish a completed, valid pre-application capture after failed
application. Hold nonce, PID, extent/type, byte digest, source/parameter binding,
publication acquire and bounded collection fixed. `decodeProfileCapture` first
requires `applied && applyRC == 0`, then `done && exitCode == 0 && termSignal == nil`.
The rehearsal removes the first condition and replaces the second with a
specific collection/ownership condition that permits application-failure exit;
merely deleting the application guard does not reach the hypothetical.

Eligible failures must occur after successful compilation/copy/publication,
with safe collection of the owned worker region. Compile refusal or incomplete
capture remains unavailable. A process signal/deadline does not automatically
satisfy the retained collection condition. Exact eligible terminal paths need
live/constructed contrasts when management selects the product behavior.

`35-profile.surface.md` owns captured versus unavailable meaning and reason
precedence; `11-policy.surface.md` owns the request; `CWorker.swift` qualifies
the worker publication; `pw_profile_capture.h` owns the private copy and input
digests; `porcelain_admission.rs` admits receipt status/constant labels. The
envelope result remains based on the host completion outcome, so a captured
receipt does not make failed application successful. The receipt is no
observation of the kernel's effective policy. Architecture prose and data
describe the same transport mechanism but add process/channel responsibilities;
they cannot replace the receipt's qualification rule.

The arrangement comparison favors one explicit receipt eligibility statement
with referenced consequences over repeating a generic "successful application"
premise in the request, architecture and receipt account. That would remove
re-deciding capture eligibility in explanations. It would retain separate
decisions about worker publication, safe collection after failure, result
classification and consumer trust. Current host tests construct receipt
premises; label-admission tests observe labels, not authenticity or request
association. They remain independent controls of their own boundaries.
Deleting redundant prose without identifying both guards would save an edit
while leaving behavior unchanged; it does not satisfy this rehearsal. No
capture guarantee is withdrawn or expanded during checkpoint preparation.

### One validator-association trace

Hypothesis: use byte-exact UTF-8 equality for validator step identifiers,
operation, filter type and supplied filter value, while retaining request-name
uniqueness, submitted-target comparison and path-compaction rules.
`validatorAssociationIssues` currently groups and joins with Swift `String`
equality. `eligibleOrderedStep` repeats that equality for the reporting tuple;
`validateForReporting` reuses the production predicates over reply-visible
inputs. Rust and Python perform literal association. A canonical-equivalent
but byte-different child identifier/value would therefore cease associating
under the hypothetical Swift rule, affecting association findings, host outcome
and `query_first` eligibility. Byte-identical positive neighbors must continue
to associate. Request admission still rejects canonically duplicate names;
there is no new reachable duplicate-name request implied by this change.

The rule belongs in the association conditions of `31-steps.surface.md` and
the lifecycle association subject, with order eligibility referring to the
same scoped relation. Cardinality, allowed diagnostic metadata omission and
query tuple composition remain separate rules. `CWorkerComparison.swift`'s
submitted-target canonical equality and path-form compaction's UTF-8 equality
answer different questions. Making every string comparison identical would
be an additional product change, not consolidation.

A shared association helper can remove duplicate implementation choices in
Swift production/reporting, and a shared statement can remove an ambiguously
reconstructed equality rule. The Python/Rust independent assertions should
remain independently authored; converting them to generated agreement would
remove scrutiny. Repeated Swift validation still checks different inputs, so
the repetition can detect misattachment even though it cannot independently
reject the shared rule. Expected savings are bounded to choosing equality;
membership, cardinality, metadata and reader-result effects still need review.

### One validator-substitution seam trace

Hypothesis: after the planned seam migration, retire validator substitution
from the experimental command while retaining ordinary validator execution,
the other seven selected controls and the two unselected worker substitutions.
The pre-migration source trace runs from `PWRunnerTestOverrides` decoding,
through controller request preservation/client transport and host validator
path selection, to native validator launch. The current echo records supplied
intent and can survive when no validator runs; it is not proof of activation.

In the proposed migrated arrangement, the availability decision has one CLI
control declaration and a host experimental-mode admission condition. Removing
substitution removes that flag's definition/help and host acceptance, not the
validator executable's ordinary bundle inventory or the query protocol. Client
transport and internal request/planning fields transmit the decision; they do
not independently define when substitution is allowed. Old-key refusal must
remain at ordinary CLI and lower-level host admission even after retirement.
Current validator-failure, phase, ordering, comparison and identity callers
lose their substituted-transcript technique; ordinary valid neighbors and
internal framing/association controls remain, but are not equivalent live
coverage. Unreached substitution requests remain experimental attempts.

The eight-control boundary adds flag spelling/domain declarations, invocation
adapter logic, separate ordinary-input/control capture and mode provenance.
It removes selected ordinary JSON activation rules and their caller-written
override dictionaries. Native rejection boundaries and ordinary-versus-actor
timeout applicability remain independent decisions; one generic integer parser
must not erase them. Publication support adds a current technical/frozen-guide
distinction without becoming a second explanation of control meaning.

The one worker/validator combined oversize pair cannot cross the new admission
boundary. Its retained direct-orchestrator assertion is internal coverage, not
CLI/XPC coverage. This exception is already management's decision, not a new
retirement inferred from rehearsal. After executable migration, compare this
source prediction with actual flags, adapter, receipts and retired paths;
that implemented-arrangement comparison is intentionally pending at the pause.
