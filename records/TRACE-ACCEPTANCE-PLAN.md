# Trace acceptance plan

## Purpose and relationship to trace management

This companion to [TRACE-MANAGEMENT-PLAN.md](TRACE-MANAGEMENT-PLAN.md) develops
the grounds for judging whether a documentation arrangement has **fewer
independently maintained judgments about the same rule**. It asks how we could
establish that improvement, distinguish it from displaced work, and recognize
evidence against it.

The management plan owns assessment of the findings, remediation decisions,
the guide freeze, and completion of the management pass. Acceptance here is a
reasoned judgment about the economy of the documentation system. This plan
adds no completion checklist, numerical threshold, or requirement to run every
investigation before resolving a finding. Its proposed comparisons supply
evidence for that judgment; performing them does not itself establish success.

The deliberately broad [trace review](DOCUMENTATION-TRACE-REVIEW.md) supplies
examples and challenges to current assumptions. Its findings are not the
organizing principle for permanent documentation. An arrangement worth keeping
should remain understandable and inexpensive to change as the product and our
understanding of it change, including in ways the review did not anticipate.

Three questions guide this investigation:

- Does explanation burden reveal product distinctions whose purpose deserves
  reconsideration?
- Which propositions are independent, and which accounts restate or depend on
  them?
- What work does a hypothetical product change require under different
  documentation arrangements?

Begin with the third question. Bounded change rehearsals make the first two
concrete without requiring a complete proposition inventory in advance.

## What an independently maintained judgment is

A judgment is independently maintained when someone must choose or reconstruct
the meaning, scope, or consequence of a rule at a location without a dependable
relationship to its owning statement. Two paragraphs can impose that duty
inside one file. A statement rendered in several files can impose it only once.
Naming an owner does not establish that its other presentations depend on it.

Consider a fallback eligibility rule. A field description that separately
enumerates eligible cases may maintain the same decision again. An explanation
of cumulative helper-output retention may instead reason from that eligibility
rule and the number of invocations. The latter remains a review obligation when
eligibility changes, even if it contains no independent eligibility decision.

The unit of comparison is a scoped proposition: who establishes what, at which
boundary, for which inputs and recipients, under which conditions, and with
what consequence. Observation time and representation belong in that scope
when they affect meaning. Similar wording alone cannot establish sameness.

For two candidate propositions, ask whether one could change while the other
remained true. Host qualification of a receipt and controller admission of its
labels can change independently. Several descriptions of the same actor-policy
selection rule may be restatements. Explain that classification with the actual
conditions; do not obtain a smaller count by dropping qualifications.

Independent scrutiny of a rule remains valuable. Separately authored test
expectations and observations can challenge a shared mistake in code and prose.
Reducing repeated authorship of a commitment does not justify deriving every
test oracle from that commitment or counting agreement among generated copies
as independent evidence of its truth.

## A bounded network of propositions

The [surface tree and presentation routing](../docs/contract/README.md) already
separate public authorship from placement. They also carry explicit references,
conditions and support. Start with those relationships and inspect the manual
accounts around them. Neither a reference nor a shared identifier establishes
that the dependent passage follows from the premise it names.

For each rehearsal, a small table or annotated passage map can distinguish:

| Relationship | What needs to be understood |
| --- | --- |
| Restates | Which scoped proposition is expressed again, and whether its wording is independently authored or mechanically copied. |
| Depends on | Which premise supports a consequence, and what reasoning or additional assumption connects them. |
| Narrows or specializes | Which boundary or applicability condition changes, and whether that introduces a separate decision. |
| Explains or illustrates | Which reader question the passage answers, including assumptions introduced by its example. |
| Supports | Which source, observation or check supplies evidence, with its assertion scope and limits. |
| Routes or renders | How a reader or generator reaches the statement without adding a public meaning. |

Keep uncertain relationships visible. An apparent consequence may contain an
unstated policy choice. Conversely, a manual summary can be useful repetition
whose dependency is clear and whose review cost is small. Consolidation,
distribution and repetition should follow those distinctions.

Look for a small set of independent premises within the examined mechanism.
There is no assumption that the entire documentation has one uniquely minimal
foundation. A broad premise containing many hidden cases can lower the apparent
count while increasing the work of changing any case. A shared term can also
conceal different meanings at different boundaries.

This working map supports the investigation. It does not establish a new
permanent registry, schema or generation system. If an alternative introduces
such machinery, its own authorship, applicability rules and maintenance costs
belong in the comparison.

## Rehearsing changes and comparing arrangements

A rehearsal begins with a concrete counterfactual and the behavior held fixed.
State the intended difference in caller obligations or justified conclusions,
as well as the mechanism being varied. Where several interpretations would
produce different work, examine them separately instead of silently changing
the hypothetical during the comparison. A rehearsal does not select or
authorize that product change.

Trace the current arrangement from the owning propositions through affected
manual explanations, generated views, examples and support claims. Include
REQUEST, RESPONSE, CONTRACT, ARCHITECTURE and other affected documents according
to their dependencies. Record the inspected revision and whether an implication
was inferred from reading, demonstrated by a draft, or observed through tooling.
A source trace is useful evidence but cannot establish measured editing effort
or a complete dependency map.

Compare that account with the smallest plausible alternative arrangement under
the same hypothetical and the same reader questions. Follow the repository's
[documentation improvement guidance](../CONTRIBUTING.md#improving-documentation-in-four-passes)
when selecting those questions. A comparison loses its force if the alternative
quietly removes a guarantee, an audience, a failure case, or a useful explanation.
If product simplification is also being considered, assess that separately so
its savings and losses are distinguishable from reorganizing the documentation.

For the alternative, identify the work expected to disappear and why. Then
trace the change again. A passage can avoid an edit while still requiring
substantial semantic review. Count that review as continuing work. Likewise,
one owning edit may require generator changes or manual decisions about where
the resulting statement applies; those are part of its cost.

Search beyond the declared dependencies for statements left inconsistent by
the hypothetical, and for statements unnecessarily reconsidered. Record how
they were found. A map that looks economical only because it omitted a manual
account provides evidence against the map. Compare claims that should remain
unaffected as well: a general definition that accidentally changes unrelated
boundaries has achieved a misleading reduction.

An additional change chosen after shaping the alternative can challenge whether
the arrangement merely accommodates the initial examples. Useful variations
include changing applicability, an evidence guarantee, or a responsibility at a
different boundary. This is a way to probe generality, not a prescribed number
of cases or a new prerequisite for trace-management completion.

## Initial counterfactuals

These examples give the investigation a bounded starting point. Their source
connections identify questions to examine; they are not completed comparisons
or proposals to change the product.

### Remove automatic fallback compilation for actor requests

Consider actor-form requests invoking no automatic fallback compiler, while
ordinary fallback and standalone `sbpl-check` remain. This includes the
whole-request helper invocation on actor input as well as per-actor calls.
Specify the hypothetical output-field treatment before comparing arrangements;
omission, null and a retained diagnostic can have different public meanings.

The [helper surface](../docs/contract/11-policy.surface.md),
[envelope fields](../docs/contract/40-envelope.surface.md) and
[dossier account](../docs/contract/42-dossier.surface.md) describe selection,
presence and held-input provenance. CONTROLLER and ARCHITECTURE also explain
actor fallback; the limits account discusses accumulation before host
admission. Examine which passages repeat selection and which derive a distinct
consequence. Removing actor-specific accumulation does not settle every limit
on the remaining helper output.

This rehearsal can expose both repeated authorship and a product question:
what useful independent observation does automatic actor compilation supply,
who relies on it, and what would its removal lose? A smaller explanation is
insufficient grounds to remove useful evidence.

### Report a valid capture despite unsuccessful application

Consider allowing a valid pre-application capture to be reported when policy
application fails. The [receipt surface](../docs/contract/35-profile.surface.md)
currently requires successful application and clean worker completion as well
as capture publication, identity and integrity checks. The separate guards in
[decodeProfileCapture](../runner/Sources/PWRunnerCore/CWorker.swift) show why
removing the application requirement alone would not establish the proposed
behavior.

Investigate which failure paths could supply usable captured bytes, what
publication and collection conditions remain necessary, and what `captured`
would establish. Keep capture, application, host qualification and controller
admission distinguishable. Those responsibilities may warrant several accounts
even if their shared premises have one owner.

Compare the repeated successful-application requirement in the surface,
architecture prose, architecture data and guide with the distinct reasoning
each audience needs. The rehearsal should reveal whether repetition maintains
the same rule again or makes a necessary consequence understandable. It also
tests whether changing receipt meaning leaves an obsolete inference elsewhere
despite mechanically fresh generated documents.

### Change validator association equality

Consider byte-exact equality for validator record identifiers and query
metadata used in association, initially holding request-name uniqueness and
submitted-target comparison fixed. The association and cardinality accounts in
the [step surface](../docs/contract/31-steps.surface.md) and
[lifecycle surface](../docs/contract/32-lifecycle.surface.md) use unqualified
equality. Submitted-target comparison explicitly uses canonical Unicode
equivalence; path-form compaction specifies UTF-8 byte equality.

Examine whether one scoped association premise can support joining, group
cardinality and dependent eligibility claims. Follow its consequences into
reader checks and host outcomes. If the proposed scope proves inconsistent
with another boundary, that exposes an additional product decision rather than
authorizing an unnoticed expansion of the rehearsal.

A universal definition of identity could conceal these different relations.
The useful reduction would make the intended shared premise explicit while
preserving separately justified equalities. The initial trace review's reader
disagreement is a reason to investigate that premise, not proof that every
identity relation should become identical.

## Pairing rehearsals with the companion plans

The three initial counterfactuals are shared threads in the management plan's
[combined sequence](TRACE-MANAGEMENT-PLAN.md#working-the-three-plans-together),
which owns their order and verification. Three consequences follow for the
rehearsals themselves.

**Make one trace per hypothetical.** The management assessment compares the
same statements, producers and readers, and the overhaul
[rehearses the same changes](TEST-OUTCOME-OVERHAUL-PLAN.md#acceptance-argument-preservation-and-reduction)
through the tests that enforce them. Use one statement of the hypothetical for
all three, including its output-field treatment. Extend the trace through the
enforcing tests and their credited claims instead of leaving them to a second
reading.

**Rehearse before the thread's accounts change.** Record the inspected
revision and trace the current arrangement before that thread's permitted
corrections land. The comparison and the later correction then describe the
same passages. An arrangement change that a rehearsal justifies travels with
the thread's other account edits under the management plan's handoff, when it
stays within developer-facing accounts and moves no ownership. It is not a
separate later pass over the same documents. Outside the management plan's
explicitly authorized seam migration below, one that would move ownership,
alter what the app does or prints, or add a promise is not adopted here; it
goes to the management plan's
[collection for the maintainer](TRACE-MANAGEMENT-PLAN.md#judgments-for-the-maintainer).
That collection also records, for each matter, which presentations are
rendered from one owner and which are separately authored. A rehearsal's
relationship map supplies this for its thread.

**Hand caller obligations to the outflow.** While tracing the current
arrangement, note each condition a caller must meet, or scope a caller must
respect, for a stated conclusion to hold. Note in particular those a reader has
to reconstruct from several accounts. They are inputs to the management plan's
[user-responsibility outflow](TRACE-MANAGEMENT-PLAN.md#user-responsibility-outflow).
An obligation that exists only under the hypothetical belongs to the
comparison and establishes nothing about the product. What reaches the outflow
is the obligation and its evidence; a rehearsal's account of guide dependencies
stays with the rehearsal.

None of this adds a gate. A thread proceeds without a rehearsal that was not
planned for it, and an inconclusive rehearsal still creates no obligation to
complete it.

## Rehearsing a migrated test seam

The management plan brings a
[bounded executable seam migration](TRACE-MANAGEMENT-PLAN.md#bounded-test-seam-migration)
into the combined implementation; the
[overhaul owns its implementation and experimental equivalence](TEST-OUTCOME-OVERHAUL-PLAN.md#migrating-executable-test-seams).
Use that thread to examine whether moving controls out of ordinary requests
also reduces maintained decisions. A more explicit entry point may be useful
even if it adds maintenance duties; the account should distinguish those gains
and costs.

Choose one selected seam and rehearse changing or removing its intervention,
holding the underlying ordinary experiment fixed. For example, if validator
substitution is selected, suppose it is later retired while ordinary validator
execution remains. Trace the change once through the current arrangement and
again through the proposed command arrangement: admission, command definitions
and help, host/internal transport, native inputs, retained evidence, test callers,
independent assertions and developer accounts. Use the overhaul's caller mapping
instead of rebuilding it here. Rehearse before editing those accounts, then
update the comparison against the implemented arrangement.

Which locations independently decide whether the control is available, what it
means, or what its presence establishes? Which merely transmit the selected
value or render its owning definition? Which need separate reasoning because
they observe different boundaries? Include ordinary/experimental admission,
unreached interventions and unselected controls in that account. A command that
still forwards an ordinary request with all the old activation rules may have
added a second explanation without retiring a decision. Conversely, one internal
representation serving both routes need not be a duplicate public meaning.

Compare the actual duties removed with those introduced in flags, adapters,
provenance and reporting. Preserve independent oracles; generating every
expectation from command definitions does not establish economy. Include the
cost of frozen guide passages made inaccurate by the authorized migration,
separately from structural change costs. This rehearsal neither authorizes the
further hypothetical change nor turns the migration into a new numerical
acceptance gate. Its result is an accountable judgment about where maintenance
work went, handed back during implementation rather than reserved as a closing
engineering question.

## Interpreting the evidence

The comparison needs an account of where work went. These distinctions help
explain it without converting the exercise into a score:

| Work encountered | Bearing on the judgment |
| --- | --- |
| A substantive product choice | May be unavoidable even under an economical documentation arrangement; it can also motivate reconsidering the mechanism. |
| Another authored version of the same scoped choice | A candidate synchronization duty; identify how the alternative removes or bounds it. |
| A consequence needing separate reasoning | Continuing review work, even when it follows from a single owner and needs no edit. |
| Generated propagation | Saves repeated editing, while leaving generator maintenance, scope and rendered-output review visible. |
| An accidentally discovered dependency | Evidence that change impact cannot yet be found reliably through the proposed arrangement. |
| A reader reconstructing omitted meaning | Work transferred to use of the documentation; concision may have made the system more expensive. |

Counts can summarize identified instances, but the instances and their
classification carry the argument. File counts, word counts, link counts and
successful regeneration cannot substitute for it. A single total would obscure
the difference between a removed editorial duty and a removed product guarantee.

Evidence for improvement becomes stronger when the comparison identifies a
specific repeated decision that disappears, explains the dependable relation
that replaces it, and shows that dependent consequences remain discoverable.
Evidence against it includes hidden applicability decisions in a generator,
manual summaries still requiring reconstruction, broad premises that couple
unrelated rules, or reader paths that omit essential qualifications.

Use the same concrete reader questions before and after the proposed change.
Observe where answering them requires inference, extra navigation or knowledge
outside the documentation. Where useful, ask a reader unfamiliar with the
proposal to follow those paths. Familiarity and repeated exposure can make an
arrangement seem easier, so distinguish those effects from structural gains.
Convenient authoring and understandable reading are both parts of the judgment.

Mechanical checks establish their stated properties, such as current copies,
links and preserved structure. A still-plausible but false explanation can
survive them. Deliberately tracing a changed premise into examples and manual
accounts helps reveal that limitation. Any experimental generator or document
patch needs the owning tools and checks appropriate to its scope; this framework
does not prescribe new tests for ordinary prose edits.

## From explanation burden to product judgment

Several documents needing coordinated explanation is a signal to inspect the
mechanism. Ask what observation, guarantee or user need each state,
representation and responsibility serves now. Consider what information would
be lost if a distinction disappeared, which consumers depend on it, and whether
its original purpose still applies. Historical rationale and present usefulness
are separate evidence questions.

Some burdens follow from irreducible differences: observation versus inference,
capture versus application, production versus admission, or different actors
observing at different times. Others may follow from redundant representations,
unreachable states or responsibilities that no longer justify their costs.
Documentation can make those choices visible, but a large explanation does not
establish that its subject is unnecessary. Equally, faithful implementation and
passing tests do not establish that the subject is worth retaining.

## Constructing and bounding the assessment

An assessment should make an argument another maintainer can examine: name the
scope and compared arrangements, identify the decisions removed or retained,
explain the evidence for that classification, and state where work moved. Keep
observed results separate from predicted savings and unresolved dependencies.
This can be a short account beside the relevant rehearsal; it need not become
a second inventory of the trace review.

For example, a justified conclusion might be that selection now has one
maintained definition, while field presence and resource consequences still
need separate review; a particular repeated selection decision has therefore
been removed, with no established reduction in those remaining duties. Another
comparison may justify retaining distributed explanations, rejecting a proposed
consolidation, or investigating product simplification. An inconclusive result
can identify the missing evidence without creating an automatic obligation to
collect it.

Apply conclusions at the scope their evidence supports. A favorable rehearsal
does not establish economy across all of `docs/`, and an additional case can
narrow an earlier conclusion. The useful result is an accountable present
judgment about maintenance and reading costs, including accepted tradeoffs.
Completion and disposition of trace findings remain with the management plan.

The [guide freeze](TRACE-MANAGEMENT-PLAN.md#guide-freeze-and-public-commitments)
remains a publication and remediation constraint. Rehearsals can identify guide
dependencies and the cost of leaving them frozen without amending the guide,
its shared inputs or its commitments. Record those costs separately from an
arrangement's structural economy; an unavailable edit is still an affected
dependency. A preferable hypothetical arrangement does not authorize adoption
or create a standing obligation for a future guide rewrite.

Keep investigation material under the [record guidance](AGENTS.md), with links
to the actual owners and evidence. Credit source reading, drafted alternatives
and executed experiments separately, and state when supporting artifacts are
local or gitignored. Permanent documentation continues to describe the chosen
current product through its existing owners.
