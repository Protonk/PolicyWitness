# Trace acceptance plan

**Handoff, November 19.** All four rehearsals have an
[implemented-arrangement comparison](#implemented-arrangements).
The last two landed in `8ca3e6db`. The
[management checkpoint](TRACE-MANAGEMENT-PLAN.md#product-group-checkpoint)
owns the outstanding technical-account edits and final outflows.

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
reject the shared rule. The rehearsal bounded the expected saving to choosing equality.
The implemented association comparison below records the retained cardinality
and metadata decisions, the reader results and the additional lookup found
during verification.

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
retirement inferred from rehearsal. The implemented seam comparison below follows
the flags, adapter, receipts and retired paths on the executed routes.

## Implemented arrangements

The comparisons began November 17 and were completed November 18. Each subsection names its revision. Observed results are
separated from predictions; a rehearsal whose hypothesis was not selected
stays a hypothesis.

### Validator-substitution seam, as implemented

Compared at `eeb76c1b`. The rehearsal's hypothesis, retiring validator
substitution, is still a hypothesis: the migration kept all eight controls.
What can be compared is the predicted arrangement with the implemented one,
and what retiring one control would now touch.

Observed. The old and new routes were run on the same 104 scenarios; 103 are
equal in component execution, intervention, independent effects, fault
rejection, identity, command accounting and cleanup, and one changed route
(below). The evidence is local development output named in the overhaul plan.

Where availability is decided, as implemented:

- `Control` in `controller/src/interface/run_args.rs` decides a control's
  flag, JSON key and value rule.
- The host's `PWRunnerTestOverrides.experimentalControls` list decides both
  admission of a member in the controls object and refusal of that member in
  an ordinary request's block. The prediction named two host conditions
  (experimental admission, old-key refusal); they are one list read twice.

What only transmits: the controller's controls object and submission
arguments, the client's experimental submission, the XPC entry point
`runReservedExperiment`, the host's submission decoding and the service's
validator-path selection. None decides when substitution is allowed.

What retiring validator substitution would now touch, from source reading:
one `Control` row; one member of the host list and of the record, after which
the old key in an ordinary block is refused as an unknown member, a different
code from today's `inapplicable_field`; the dossier's validator-control
selection; one row of the experimental table in `runner/README.md`, which the
drift rule compares with the host list; the control's rows in
`witness_contract/test_input` and their rejecting controls; and the callers
in the overhaul's caller map that use a substituted transcript. No help card
names a control, so the predicted help edit does not exist. The contract
rules `request.overrides.experimental`, `request.overrides.test_input_run`
and `request.overrides.ordinary_refusal` state the mechanism without listing
the control's meaning and would need review, not necessarily an edit.

Decisions removed by the migration: the eight keys' separate type and domain
outcomes on an ordinary submission (one presence rule replaces them: the
corpus example with a fractional value is now refused for presence, not for
type), and the caller-written override dictionaries (callers give the adapter
an ordinary request and a controls mapping).

Decisions retained: each control's native rejection boundary; the ordinary
worker-timeout floor against the actor execution allowance; the reading of
the echo as supplied intent, never activation (the activation rows read the
intervention itself); the two unselected worker substitutions.

Work the prediction did not name, displaced or added:

- Value domains differ by route. A command-line argument cannot carry a NUL,
  so one admission scenario travels through the client's controls object and
  the adapter refuses a NUL for the controller; a fractional value is a usage
  refusal for the flag and a `type_mismatch` at the client. One invalid value
  now has route-specific expectations that are maintained separately.
- The controller's `run` had its own reading of the request's validator key
  for the dossier. It was a second, unlisted reader of the old key and was
  retired with the route.
- A Swift admission test submitted an encoded override through the ordinary
  call; it was a live submission, not a direct construction, and moved to the
  experimental call.
- The client capture does not record which XPC call was made. A reader
  identifies an experimental submission from the client's argument vector and
  from the reply's echo, which is reader inference the old arrangement did
  not need.
- The limits manifest names the controls in eight texts copied into the
  guide. Correcting the owner while the guide is frozen is the first real
  divergence between them, and it was blocked by controls that presumed a
  copy of the checkout is publication-fresh. The correction therefore carries
  a revision of those controls. This is publication-boundary maintenance the
  rehearsal predicted in kind but not in place.

Judgment. The migration removed one family of independently maintained
decisions (ordinary-route activation semantics per key) and concentrated
availability in two declarations. It added a route-dependent value domain,
an adapter, per-control refusal rows and three contract rules. Independent
review is still needed for each control's native boundary and for every
caller's own expectation. No saving is claimed beyond the decisions named.

### Capture despite failed application, not selected

Compared at `147fc10f`. The hypothesis was not selected: `captured` keeps its
two host conditions, and no product source changed for this subject. The
rehearsal therefore stays a hypothesis, and this subsection records one
correction to its premise and what the decision leaves in place.

Correction to the rehearsal, from the receipts assessment
([I-receipts.md](trace-assessments/I-receipts.md), T2 and its first note
outside the review). The rehearsal said the hypothetical needs the completion
condition replaced as well as the application condition removed. By source
and by an existing executed assertion on the production C main with a
substituted application call, a returned application failure ends with `done`
published and exit status 0. The completion condition already holds on that
path; the application condition alone withholds a completed copy. The
completion condition governs signal, deadline and unreaped paths, which are
not failed application. What is still only source-read: no test requests
capture on the application-failure companion, so the receipt a real run
reports on that path has not been observed.

What selecting the hypothesis would have touched, from that assessment: one
host condition and two comments in build inputs; the receipt surface's
application condition, reason values, status and stage; two architecture
rows and their authored prose; one limits row and a sentence in a region the
frozen guide copies; three Swift tests and three suite accounts. `captured`
would no longer imply observed application, and a compile failure would
change its reported reason. That list is a prediction; nothing was executed
for it.

Decisions retained by not selecting it: `captured` implies the host observed
successful application and clean completion; an `unavailable` receipt does
not say whether the worker copied the object. The receipt surface's Status
statement carries that limit in one place. The comparison the rehearsal
favored, one explicit eligibility statement with referenced consequences
instead of a repeated "successful application" premise, is an editorial
arrangement that does not depend on the product choice. This stage makes no
separate editorial pass for it; the repeated premise stays where it is true.

The technical-account pass still owns the assertions for the reasons,
first-failure order and withheld fields of an `unavailable` receipt. Its
owner must distinguish the executed checks from source inspection. The
separate Rust label-admission assertion was corrected in `560a5a35`.

### Actor fallback, as implemented

Compared at `6d2d8ebd`. The hypothesis, removing both automatic compilations
for actor requests, was not selected. What was selected is narrower: the
whole-request helper call is no longer made for a request with an `actors`
array, so `policy_check` is present and null there, and the two fallback
calls on the admitted-reply branch are deleted. Per-actor compilation and
`actor_policy_checks` stay.

Observed, from the thread's runs and one by-hand probe on shipped binaries:
with the new assertions on the unchanged product the three actor-form tests
failed because the helper received the held request; with the host killed
during an actor action the old envelope carried a helper `tool_error` for the
missing top-level policy and the new one carries null, while the actor's own
capture was `ok` both times. The probe's envelopes are scratch only.

Against the rehearsal's table:

- Fallback and helper subjects. The predicted narrowing of automatic
  invocation happened for the whole-request call only. The helper's grammar,
  limits and capture meaning did not change, as predicted.
- Envelope. Present-null `policy_check` for actor requests is as rehearsed.
  The rehearsed omission of `actor_policy_checks` did not happen. Result and
  error precedence were restated as produced, a correction the rehearsal did
  not predict because it assumed those statements were already true.
- Dossier. Unchanged: the per-policy serialization and the helper's later
  import walk remain, since per-actor compilation remains.
- Mechanism accounts. One helper launch per actor request disappears from the
  inventories, not all of them.
- Tests. The prediction held and was the larger part of the work: the actor
  fallback tests no longer let a call count stand for input provenance. They
  assert membership from independently authored policy objects, attribution
  and order from the envelope, and invocation separately. An ordinary-form
  held-input control was added, which the rehearsal did not name.
- Limits. The per-capture bounds stay true; the accumulation statement
  changed by one capture.

Decision removed: whether an actor request also gets a whole-request helper
call whose only possible result was a decode failure. Removed with it: one
statement that the fallback "does not depend on host admission", which was
false, and the unreachable admitted-branch calls, whose deletion rests on a
control over every combination of the members eligibility reads.

Decisions retained, each still maintained in its own owner: the field
presence rule; the held-serialization rule; per-actor compilation and its
resource bound; fallback eligibility, which still establishes nothing about
worker progress or the cause of a lost reply.

Lost observation: none that carried information. The whole-request capture
for an actor request was always a helper refusal. The observations the
rehearsal said removal would lose, the independent per-actor captures and
their import scans, are kept.

Work displaced: a reader of an actor envelope with no policy-bearing actor
now finds no fallback capture at all and reads eligibility from the client
capture. The frozen guide's fallback paragraphs do not say `policy_check` is
null for actor requests.

Judgment. The implemented change removes one decision and two unreachable
calls and corrects statements; it is a product simplification, not the
editorial consolidation the rehearsal weighed. The rehearsal's proposed
single applicability statement was not needed: applicability now differs
between the whole-request and per-actor calls, which is one more reason the
three rules stay separately stated.

### Validator association equality, as implemented

Compared at `43c2896d`. The hypothesis was selected (ruling R9) and is now
behavior, so observed results replace the rehearsal's predictions.

Observed. Before the change the host accepted every new corpus row while the
Rust reader and the independent consumer refused the four byte-different
ones; the three readers now agree on all of them. A canonically equivalent,
byte-different record gives a missing and an unexpected identifier, or a
query mismatch, then `validator_unavailable` and exit 1; byte-identical
neighbours associate. The order-barrier mutation control passed with no
anchor moved.

What the rehearsal predicted and what was found:

- It named two places where the equality was decided, association and order
  eligibility, with reporting validation reusing the production predicates.
  Found: reporting validation held its own `String` lookup of a reply step
  by identifier. After the first change production and reporting disagreed
  on a respelled slot identifier, and a second commit applied the rule
  there. The predicted reuse was not complete.
- It did not name the worker-slot identity join. Found: one side is
  child-supplied, because a completed slot's identifier is read back from
  the shared mapping the worker can write, so the rule applies there too.
- It expected the rule to live in the step and lifecycle association
  statements, with eligibility referring to it. That is how it is stated.
  Request-name uniqueness and submitted-target equality remain canonical and
  are stated as such; path-form compaction is untouched. No comparison
  outside validator and slot association was changed.
- It suggested a shared association helper could remove duplicate choices in
  Swift. None was introduced: the lookups were changed where they stand, and
  the independent Rust and Python readers were left independently authored.

Decision removed: which equality joins a child-supplied identifier or query
metadata value to the request. It had been made implicitly, and differently,
by the Swift host and by the two independent readers.

Decisions retained: cardinality; which metadata a record may omit; the
composition of the query tuple; the two canonical comparisons named above.

Review that continues: any new host lookup by identifier needs the question
"is one side child-supplied?" asked again; nothing enforces it mechanically.
Three comparisons stay on `String`, with their reasons in the management plan:

- the identity term beside the changed lookup, which compares the pair that
  lookup already matched;
- the extension-event lookup of a record step in
  `actorExtensionEvidenceProblem`, which refuses under either equality by
  source reading only;
- the comparisons in `validateForReporting` among step, action and event
  identifiers, all of which come from the request.

Judgment. The saving is the one the rehearsal bounded: a single stated
equality in place of two implicit ones. The work it did not predict was
finding every place the choice had been made; the second commit exists
because source reading by the rehearsal and by the first implementation
both missed one.
