# Trace review management plan

## Purpose and scope

[DOCUMENTATION-TRACE-REVIEW.md](DOCUMENTATION-TRACE-REVIEW.md) is a deliberately
broad investigation record. Its investigators were encouraged to find problems
that would not look like problems from every perspective. The overlapping
entries, differing interpretations and appended qualifications preserve that
search. They are useful inputs to assessment, including when an apparent
implementation defect becomes a question about a specification, a test's
assertion scope, or the inference a reader can draw.

This plan makes those findings usable for careful remediation while preserving
their ability to challenge the existing arrangement. It establishes a route
from observations to bounded decisions and verifiable changes. It does not
select the implementation, the specifications or the tests as automatically
correct when they disagree. Agreement among all three can also rest on an
undesirable rule or a shared assumption.

A finding can disappear under one interpretation while leaving a consequential
problem under another. Record what the explanation settles and what remains.
For example, deliberate delegation can explain why one reader accepts a record;
it does not establish that callers run the reader responsible for the remaining
checks, or that coverage claims accurately describe that arrangement.

The initial groupings and examples below are assessments of the recorded
investigations. Preparing this plan supplies no fresh execution evidence or
independent confirmation of their findings. The review currently contains
DT-01 through DT-135 and two unnumbered import/receipt investigations. Its
source snapshots, builds and evidence limits remain attached to their claims.

## Working materials

Keep the review intact as the evidence record. Develop the coverage map and
working assessments in this associated plan. A targeted remediation plan can
become a separate `TRACE-<topic>-PLAN.md` when it has a concrete decision,
approach and verification. Follow the repository's
[planning guidance](../CONTRIBUTING.md#planning-a-change).

Begin with Markdown tables and short assessments. The work needs a way to find
every observation and understand its disposition; it does not yet need a new
schema, generator or issue-management system. Split the working material only
when its size or execution boundaries make that useful.

Under the [record rules](AGENTS.md), links into investigation records belong
in their associated plans. Put resulting statements of current behavior in
their existing documentation owners within the freeze boundary below, without
links back to this investigation from permanent documentation, source, tests
or indexes.

## Guide freeze and public commitments

The freeze covers the explanatory content of `docs/PolicyWitness.md` and its
distributed copies, including generated or shared content copied into them.
Changing an owning input and postponing regeneration still crosses that
boundary. The narrow exception is generator-required identity and stamp-table
updates that record another authorized change without revising explanatory
content or silently changing a public meaning. Review those outputs explicitly;
do not bypass freshness checks or hand-edit generated copies to preserve the
appearance of a freeze.

The freeze constrains publication and the remedies available now. It does not
establish that the guide is correct or that behavior it describes is desirable.
An assessment may conclude that the guide is wrong without amending it. Keep
that judgment distinct from authorization to change the product's commitments.

Elsewhere, classify an edit by what it does rather than where it appears:

| Proposed edit | Boundary during the freeze |
| --- | --- |
| Correct a mechanism account, citation, test description or support claim | Proceed when it describes established behavior without changing caller obligations or guarantees, and does not alter content copied into the guide. |
| Clarify a public statement | Establish whether the edit expresses an already-settled meaning or chooses between consequential interpretations. The latter is a substantive decision. |
| Change what callers may submit, must do, or may conclude from output | Treat it as a public-meaning change requiring an explicit compatibility decision, regardless of the file that owns it. |
| Supply replacement workflows or instructions for reinterpreting frozen guide passages | This would create a shadow user guide and is outside the freeze boundary. |

REQUEST, RESPONSE and the authored surfaces already carry public meanings.
They cannot provide an indirect route for amending the guide. Ask whether an
edit changes a caller's required behavior or justified conclusion. If it does,
documentation accuracy alone does not justify the change. Where the evidence
and guide disagree, retain the disagreement in the assessment instead of
silently publishing a replacement normative interpretation elsewhere.

### Judge the product before selecting the available remedy

For each affected statement, first establish the behavior and evidential
meaning worth choosing on their merits. Then assess the existing user reliance
that choice would disrupt. Apply this locally to candidate changes; a complete
new inventory of guide commitments is not a prerequisite.

| Kind of statement | Consequence for the decision |
| --- | --- |
| Explicit commitment | Concrete conditions promise behavior or meaning. Removing it can break compatibility even if it was a poor choice. |
| Consequential ambiguity | Reasonable readings produce different expectations. Choosing one requires a decision rather than an editorial clarification. |
| Unsupported inference | A stronger conclusion exceeds what the stated observations establish. The product need not acquire machinery solely to make that inference true. |
| Inaccurate mechanism account | The prose describes an internal operation incorrectly. Correcting the account need not preserve that mechanism, unless it also expresses a user commitment. |

Use the passages and their context to justify the classification. An
unimplemented promise can still be a promise; mention in the guide does not
make every implied interpretation a commitment. Likewise, evidence that a
current rule is faithfully implemented does not settle whether to retain it.

Changes to public meanings remain possible within their agreed scope, but may
not silently contradict a retained commitment. If truthful publication of the
chosen remedy requires revising the frozen guide, that remedy is unavailable
under the freeze. Decide whether to retain the present behavior and its stated
cost or reconsider the freeze before implementing it. Additional architecture
intended to vindicate existing prose needs its own substantive justification.

## Units of assessment and relationships

Use a claim with a particular boundary and consequence as the assessment unit.
An original DT identifier remains its source reference. Several entries can
support one problem, and one entry can supply several problems. DT-34, for
example, contains ownership classification, recovery wording and signing
observations that need separate dispositions. References such as
“DT-34, recovery bullet” are sufficient; renumbering the original review would
discard useful continuity.

Each working assessment should answer these questions:

| Question | What to retain |
| --- | --- |
| What is observed, and what is inferred? | The narrow observation, the interpretation being considered, and competing readings where consequential. |
| Where does it apply? | Input form, observer, representation, execution path and observation time. |
| What supports it? | DT references and follow-ups; inspected snapshot and build; native, controlled, constructed, source-read or historical evidence; artifact availability. |
| What remains problematic? | The practical consequence for behavior, evidence, interpretation, verification or maintenance after qualifications are applied. |
| What decision is needed? | Candidate implementation, specification or test changes; deliberate retention; or the particular uncertainty preventing a decision. |
| What does the freeze constrain? | The affected passage, actual commitment or inference, available corrections, and any remedy that requires a guide change. |
| What is the present disposition? | What is established, what is acceptable or defective, the treatment chosen now, and the consequences accepted or found unacceptable. |
| What would settle a remaining uncertainty? | The discriminating evidence or decision needed, without automatically creating a future work obligation. |

Keep evidence, interpretation and work status separate. A constructed frame can
establish a reader gap without establishing that the shipped producer emits
that frame. A native execution can establish behavior that is already stated
accurately. Neither category determines priority by itself. A source-supported
claim does not become executed because another entry in its group was run.

Record relationships explicitly: confirms, extends, narrows, corrects, shares
a mechanism, depends on, or remains in tension. “Related” by topic is useful
navigation but insufficient grounds for combining decisions. Use “duplicate”
only where the claim, boundary and relevant limits coincide. Even then, retain
the additional evidence rather than counting it as another independent defect.

Later text supplies evidence for a revised assessment, not an automatic
last-writer decision. Resolve apparent disagreement by checking inputs,
snapshots, observers, representations and times. Keep unresolved disagreement
visible when those distinctions do not explain it.

These examples seed the relationship map:

| Sources | Working relationship | Question that survives consolidation |
| --- | --- | --- |
| DT-08 and DT-91 | One omitted discovery root; the later entry adds executed contrasts and history. | How should the stated selection stay aligned with the generator's selection? |
| DT-23 and DT-51 | One classification asymmetry exercised through spawn and decode failures. | What outcome should validator failures produce for a declared-unapplied actor? Preserve both paths in verification. |
| DT-46 and DT-120 | The later trace qualifies the recording history and the independence concern. | Correct the recording-time account; assess actor trigger projection separately under DT-121. The follow-up found no reader treating the copies as independent corroboration. |
| DT-53 and DT-132 | The later frame exercise strengthens the scope result and explains deliberate reader responsibilities. | Which callers omit the responsible oracle or equivalent assertions, and what coverage do their passes actually establish? |
| DT-63 and DT-124/125 | Later observations distinguish last-use clearing from teardown and identify an additional worker-side control. | Can the credited test distinguish the particular clearing boundary it claims to establish? Eventual clearing does not settle that question. |
| DT-31/32/42 and DT-113–119 | One admission gate explains several observations, with separate foreign-decoding and actor-helper boundaries. | Which public states and fixtures remain useful, and which accounts describe unreachable combinations? |

## Initial families

These families are starting navigation, not a complete allocation or a set of
preselected changes. Cross-reference a finding into more than one family when
it answers different questions. Mark temporarily unallocated observations so
an unusual or isolated finding is not excluded by the taxonomy. Assignment is
an intermediate coverage step; it is not a completed disposition.

| Family | Representative findings | Organizing question |
| --- | --- | --- |
| Documentation generation and reading paths | DT-01–07, DT-13–21, DT-39–41 | What must generation preserve, and what relationships must a reader be able to follow? |
| Result selection and transport | DT-23/51, DT-31/32/42, DT-113–119 | Which states are reachable, what selects the result, and what does fallback establish? |
| Reader responsibilities and identity relations | DT-22/57, DT-25, DT-48/50/52/53/60/61, DT-130–135 | Which proposition does each reader check, under which equality rule, with what consequence? |
| Observation ownership and time | DT-46, DT-59–68, DT-120–129 | Who observes a value, when, and which observations survive independently into the reply? |
| Import inventories and compiled receipts | DT-29, DT-81–87, DT-95–104, the two unnumbered follow-ups | What is established about submitted source, imported files, captured bytes and application? |
| Runner reconciliation | DT-34/35, DT-69–80 | How are absence, failed inspection, ownership, candidate discovery and recovery distinguished? |
| Development identity | DT-08, DT-88–94 | Which paths and bytes are selected, and what constitutes failed discovery? |
| Wire identity and public projection | DT-105–112 | What requires producer/reader agreement, and what information survives projection? |
| Exec output retention | DT-55/56 | What representation makes truncation and decoding loss visible? |

Evidence-support findings also belong beside the behavior they concern.
DT-11/12, DT-38/47, DT-67/79/86/93/101/111/135 illustrate recurring questions
about availability, assertion scope, shared expectations and independent
judgment. Use those as a second view across families, without removing their
specific claims from the owning assessments. A general observation that “tests
are incomplete” would lose the distinctions needed to repair them.

## Assessment sequence

### 1. Establish coverage without filtering on severity

Inventory every numbered entry, compound subfinding and unnumbered follow-up.
Give each an assessment destination, keeping any temporary allocation gaps
visible. Include qualifications, affirmative observations and unresolved leads.
DT-44's reported but unverified items need their own treatment; absence of a new
reproduction does not turn them into resolved items.

Record links between earlier and later accounts before shortening their
conclusions. Keep the question that motivated an entry available even when its
first interpretation is withdrawn. Count coverage of observations, not a target
number of surviving defects.

The complete map is a management deliverable. Once a bounded assessment is
ready, it can proceed toward remediation while the remainder is still being
mapped. Coverage work should not become a prerequisite for every small fix.

### 2. Examine each concern from its relevant perspectives

For a selected problem, put the stated obligation, producer behavior, retained
evidence, reader checks and test assertions beside one another. Identify the
user or developer inference at stake. Use the existing
[acceptance boundary map](DOCUMENTATION-TRACE-REVIEW.md#acceptance-boundary-map-what-each-accepting-boundary-checks-and-over-which-representation)
and [observation-time account](DOCUMENTATION-TRACE-REVIEW.md#observation-time-cross-anchor-account)
where they already supply this work.

Ask both what explains the current arrangement and what that explanation leaves
unanswered. “By design,” “the producer cannot emit it,” “another reader checks
it,” and “the suite passes” can each be relevant evidence. None alone settles
a specification's meaning, the scope credited to a test, or whether the chosen
design serves its purpose.

Likewise, a suspicious combination is not automatically a runtime defect.
Preserve distinctions between a false claim, an accurately described limit,
an unspecified relation, lost evidence, an unchecked producer obligation and
an awkward but intentional design. An assessment can retain several of these
at different boundaries.

### 3. Resolve only uncertainty that changes the decision

Check current applicability against the files and dependencies behind a claim
before implementing its remedy. Reuse recorded observations with their stated
limits where applicable. If evidence is missing or a dependency changed, name
the question a new check must settle before running it.

Prefer a small contrast that distinguishes competing explanations. Avoid a
fresh broad audit simply to replace the review with a uniform report. When an
uncertainty cannot yet be settled, retain the competing accounts and judge what
the evidence presently supports, what it leaves unknown, and whether accepting
that uncertainty is justified. Identify further evidence only when it would
change the decision; its absence need not generate a task. A decision that
cannot responsibly be made remains pending, rather than being counted as a
completed assessment through assignment to future documentation work.

### 4. Choose and verify a bounded response

Evaluate candidate remedies on their merits, then select the treatment
available within the guide freeze and existing commitments. Responses include
changing behavior or public meaning within that boundary, correcting a test or
its coverage claim, improving the reading path, or retaining the arrangement
with an explicit rationale. More than one response may be necessary. Narrower
prose is sufficient only when the narrower promise is justified and its
practical consequence has been assessed; it cannot silently withdraw a
commitment or substitute for a frozen guide amendment.

When the preferred remedy is unavailable, complete the present product
judgment. State the remaining defect or limitation and whether its consequences
are accepted. “Update the guide later” is neither that judgment nor a chosen
remedy. If the cost is unacceptable, identify the conflict with the freeze as
the decision to resolve.

Group changes when they share a decision and verification boundary. Keep
separate changes for separate mechanisms even when their symptoms resemble
one another. Priority should consider consequence, reachability, uncertainty,
dependencies and decision readiness. Popularity across reports and ease of
reproduction are not measures of importance.

## First applications of the method

### Transport pilot

Start with DT-31/32/42 and DT-113–119. The
[existing synthesis](DOCUMENTATION-TRACE-REVIEW.md#how-dt-31-dt-32-and-dt-42-relate)
already separates a shared gate from adjacent mechanisms. Answer three reader
questions through one short assessment:

1. Which combinations of submission, capture and host reply can reach the
   shipped result path?
2. What does the first failed boundary leave in the envelope?
3. What purpose and meaning should ordinary and actor fallback have?

Produce separate candidate decisions for unreachable result states and their
fixtures, foreign-producer decoding, and actor-form helper invocation. Do not
infer that every defensive branch should be removed. Establish whether its
purpose is defensive handling, component testing, or an advertised public
possibility, and evaluate the tests on that basis.

Separate availability of fallback output from its explanatory power.
Independent compilation does not establish worker progress or explain a lost
reply; do not expand transport machinery merely to support that inference.
Removing an invocation or changing the presence or status of `policy_check`
can nevertheless alter an observable commitment. Assess that compatibility
question and the actor-form whole-request failure independently. The pilot's
disposition must judge their present utility and cost, even if a preferred
change cannot be published during the freeze.

### Test and specification challenge

Use DT-53/132 and DT-63/124/125 to check that the method preserves findings
whose apparent defect changes with perspective.

For DT-53/132, delegation explains the general consumer's scope. The assessment
still needs to address the callers that do not run the lifecycle oracle and
the claims made about their coverage. Possible responses include changing
which checks run, changing credited scope, or accepting a stated gap. A unified
validator is not implied.

For DT-63/124/125, observed clearing and source order can support the behavior
while a final-state assertion still fails to establish its claimed timing.
Assess host and worker controls separately. The remedy may be a discriminating
observation or a corrected support claim, with no change to erasure behavior.
If the behavior is sufficiently supported and the test's credited scope is
corrected, that narrower assessment can finish without a guide rewrite or an
automatic obligation to add implementation work.

### Import and receipt distinctions

Use this family as a check against excessive merging:

- DT-82 concerns a scanner distinction dropped by the helper's projection.
- DT-84 concerns a literal import form missed by the scanner.
- DT-85 bounds a deliberate walk that includes unevaluated forms.
- DT-98 concerns the receipt's input coverage.
- DT-103 concerns the private object view and the inference about application.

The [final qualifications](DOCUMENTATION-TRACE-REVIEW.md#passages-in-the-appended-account-that-need-narrower-wording)
correct a consequential earlier emphasis: source association holds by
construction; the missing association concerns the compiler's file inputs.
Adding a source-digest comparison would not supply that missing observation.
Preserve the distinction between documented separation, unverified association,
observed divergence and signaled incompleteness. Fixing a scanner miss would
not identify the file bytes consumed by a separate compilation.

Judge whether the lack of compiler-file observations is an accepted limit of
the instrument, and whether its public account overstates the evidence.
Preserving the receipt does not require making the literal inventory identify
those inputs. Conversely, accepting that limit does not dispose of the scanner
miss or the helper's dropped incompleteness signal. A retained documentation
defect must state the mistaken inference readers remain exposed to; an internal
assessment does not repair that user-facing defect.

### Early remediation candidates

These are bounded starting points for assessment, not predetermined solutions
or a final priority order:

| Sources | Candidate decision | Discriminating verification |
| --- | --- | --- |
| DT-55/56 | Decide what exec output promises and how its representation exposes NUL, truncation and decoding loss. | Preserve both the embedded-NUL and split-UTF-8 contrasts; inspect retained content and loss indicators, not only child success. |
| DT-74 | Distinguish an absent registry from failure to inspect its path. | Contrast absent path, inaccessible ancestor and unreadable file; inspect the resulting classification and candidate report. |
| DT-89 | Decide how failed source-directory enumeration affects identity derivation. | Contrast readable and unreadable directories containing selected files; check that omission cannot silently masquerade as complete discovery. |
| DT-23/51 | Decide how declared-unapplied actor classification handles validator failures. | Exercise spawn and decode failures beside their applied counterparts, retaining independent worker observations. |
| DT-09, DT-26, DT-54, DT-58, DT-69, DT-91 | Assess specific inaccuracies and correct accounts within the freeze boundary; give remaining inaccuracies a present disposition. | Check ownership, generated destinations and user commitments, then verify that corrected support establishes the stated scope. |

Broader questions about integrity findings and exit status, receipt validation,
or wire projection need their own decisions. The current separation of result
selection and diagnostics is documented; changing it would require an account
of the desired public meaning and affected consumers.

## Remediation handoff and verification

A remediation proposal should carry the bounded problem, relevant competing
interpretations, chosen behavior or meaning, affected owners and readers,
verification, and explicit exclusions. Include the freeze's effect on the
selected remedy and any residual cost. Explain why the chosen layer changes;
existing agreement with that layer is insufficient justification by itself.
Public-meaning and interface decisions follow
[CONTRIBUTING](../CONTRIBUTING.md#improving-documentation-in-four-passes).

For each proposed check, state the plausible incorrect behavior that could
previously pass and how the new observation distinguishes it. Match the tested
representation to the claim: a pre-encoding object does not establish byte
preservation, a body helper does not establish whole-envelope acceptance, and
captured-byte equality does not establish semantic truth. Shared predicates
and generated definitions should receive credit for consistency without being
counted as independent judgments.

Follow [test guidance](../tests/AGENTS.md) and
[change verification](../tests/CHANGE-VERIFICATION.md) for case selection,
evidence reuse and required controls. In particular, changes to the worker
wait, release store or eligibility rule require
`witness_contract/order_barrier_mutations`. Run registered selections through
the dispatcher with a fresh `PW_TEST_OUT_DIR`, and respect the shared checkout
lock. Direct investigations retain their own evidence class.

The review's development runs and scratch artifacts are local, generally
gitignored or temporary, and have no retention guarantee. Check availability
before crediting them. Preserve decisive observations and provenance in the
assessment, without adding retention exceptions or treating missing artifacts
as either proof or disproof of the recorded result.

For permitted documentation and contract changes, edit the owning inputs and
regenerate through the [documented generators](../docs/AGENTS.md). Inspect all
destinations for guide content changes, including copies from shared inputs;
separate any allowed identity/stamp updates from explanatory changes. Update
affected admission, transport, readers, fixtures and public meanings together
when the decision crosses those boundaries. Mechanical freshness establishes
agreement of copies; review and selected behavioral checks establish the
changed claim.

## Completion and disposition

Complete each assessment with a present-tense judgment:

> We establish X within these limits. We judge Y acceptable or defective
> because Z. We choose this present treatment. It leaves this consequence,
> which we accept or find unacceptable under the freeze.

The judgment may conclude that an alleged defect is not established and a
narrower problem is resolved; that behavior is an accepted limitation with no
additional work warranted; or that a known defect remains deliberately retained.
In the last case, name the affected cases and costs. Assessment completed and
defect repaired are different states. A known defect can remain without an
automatic promise to repair it when the guide changes.

If the residual cost is unacceptable, the required decision concerns the freeze
or the chosen product behavior. Mark that decision pending until it is made;
assigning a future documentation task cannot substitute for it. An unresolved
evidence question can instead receive a completed, bounded judgment when the
present uncertainty and its consequences are explicitly accepted. Do not claim
the underlying behavior was established in that case.

Record which original claims were resolved, narrowed, withdrawn or deliberately
retained, what evidence supports each disposition, and what remains defective
elsewhere. A correction to one passage does not close every concern in its
family. An implementation that meets its current specification does not by
itself close a challenge to that specification or its credited tests. Correcting
internal accounts while freezing misleading guide prose leaves a documentation
defect whose reader impact must be judged explicitly.

The management pass is complete when every observation has a traceable present
assessment, follow-up qualifications are represented, and selected changes have
usable proposals. No observation is complete merely because it has a family,
a future task or an instruction to revisit the guide. Completion requires
accountable judgments, not a target number of defects or future obligations.

Before accepting the synthesis, check it in both directions: every original
observation has a disposition, and every proposed change rests on identified
claims and decisions. Resolve temporary allocation gaps and inspect cases that
seem harmless from one perspective. Further work follows from a chosen product
objective or new evidence; the accounting exercise creates no standing backlog
or requirements for the eventual guide rewrite.
