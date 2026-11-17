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

The freeze is an editorial prohibition. Leave `docs/PolicyWitness.md`, its
distributed copies and the explanatory source regions copied into it unchanged.
Do not collect guide errata, propose replacement passages or publish substitute
user guidance elsewhere. The work prepares a corrected product and its technical
accounts; it does not progressively repair the old guide.

The guide is not an oracle for permissible architecture. Within the selected
subjects, justified changes to signed components, contracts, interfaces,
representations and behavior are authorized even when development intentionally
diverges from the guide. A historical description does not justify retaining
otherwise unnecessary machinery. No tagged release or publication occurs here;
development verification must not claim that the frozen publication is current.

### Handling changes during the transition

Assess remedies on technical merit, evidentiary consequences, product
responsibilities and maintenance cost before choosing their implementation
layer. The implementing agent decides within the trace subjects, selected
conversions, two pytest cohorts and seam boundary in these plans. That includes
changing a public meaning deliberately, moving a technical owner, or retaining
an arrangement when its benefits warrant the cost. It does not authorize an
unbounded redesign or every imagined simplification.

Signed-app rebuilds and verification costs govern sequencing, not desirability.
Do not prefer a test-only repair, prose workaround or indirect mechanism merely
to avoid changing the executable or contract. Correct the relevant technical
accounts with the behavior; retain independently justified tests. Withdrawing
test authority alone does not repair a product defect or withdraw a commitment.
Make the product decision and its consequences explicit in the assessment.

Difficulty, severity or invasiveness does not presumptively require human
approval. Seek input only for authority or information genuinely missing from
the authorized work. Closing outflows transfer consequential understanding of
the resulting product; they are not a queue of otherwise authorized remedies
deferred by implementation layer. Neither the old guide's organization nor a
future guide author's preferences determine these decisions.

### Development and publication checks

Source inspection at `3d3f8e65` found a concrete coupling to address before
affected product changes: `build.sh` runs the limits and contract generators in
check mode and stages the guide; `generate_limits.py` renders current scalar
spans and shared copies into it; `docs/contract/runtime.py` compares its stamp
table with the current contract. `docs/build_contract.py` already distinguishes
development digests from release identities, but that identity alone does not
separate publication freshness. Release preflight also enforces free-text and
prose baselines. These checks are not reasons to choose an inferior remedy.

Establish an explicit, bounded development/publication distinction in these
existing owners before the instrument checkpoint if needed by the selected
work. Preserve the frozen guide and shared explanatory regions against
`3d3f8e65` and their exact bytes. Keep current machine definitions,
technical contract projections, interface inventory and build identities
checked against the actual development product. Where a generated technical
owner also supplies frozen publication content, separate that publication
projection from the current definition instead of editing its frozen prose or
maintaining a second normative explanation. Do not write replacement guide
content. No manual edits to generated copies or unexplained stale-file allowance
are acceptable.

The development path may explicitly report that publication is withheld; it
must still reject accidental drift, altered frozen content, stale technical
outputs, wrong identities and inconsistent evidence. It must not stage the
frozen guide as a freshly verified current manual. A development artifact and
its verification receipt must carry that publication limitation. Use a small
revision/region boundary in the existing generation/build machinery if required,
not an errata inventory. If a free-text or prose guard blocks a justified change,
revise its specific development rule with positive and negative controls;
blanket disabling or accepting arbitrary growth is not authorized.

Release preflight, publication and archive admission must reject a development
publication boundary even if the code is clean and signed, or a release tag is
manufactured. Strict publication freshness remains required for a future
release. Test deliberate divergence beside stale technical outputs, changed
frozen bytes, missing boundary evidence and attempted release promotion. Keep
signing, app/source agreement, provenance, cleanup and historical archive rules
intact. This distinction is implementation work within the current scope, not
permission to claim release readiness. Its build-input changes land before the
unchanged-app comparison, while reporting-reader changes land in the capability
stage; the final verification below exercises both sides without another broad
battery.

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

Implement a justified remedy within scope even when the frozen guide would no
longer describe it. State the resulting product's responsibility in its current
technical owner and verify it. Apply the development/publication distinction
above; do not collect stale guide passages or preserve architecture to vindicate
them. A genuine compatibility cost belongs in the product judgment, independently
of the editorial freeze.

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
| What does the freeze constrain? | Publication of the guide and its explanatory inputs; the development checks needed to preserve them while verifying the changed product. |
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

Evaluate candidate remedies on their merits, then implement the justified
response within the selected subject. Responses include changed product
behavior or commitments, corrected assertions and coverage claims, better
reading paths, and deliberate retention. More than one may be necessary. The
[transition authority](#handling-changes-during-the-transition) applies equally
to signed components, contracts, interfaces and tests. Neither a small patch
nor a reduction is presumptively better.

When a remedy cannot responsibly be completed within scope, judge the present
product: what remains defective or limited, what evidence is missing and whether
accepting that consequence is justified. Name a real authority, information or
scope limit if one prevents action; cost or guide divergence alone is not one.
A referral or future documentation task does not complete an unresolved product
decision. Narrowing a test claim cannot conceal a continuing product violation.

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
disposition must judge their present utility and cost and implement any selected
remedy. Publishing a release remains outside this work.

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
verification, and explicit exclusions. Include any development/publication
boundary needed and the resulting product's residual cost. Explain why the
chosen layer changes;
existing agreement with that layer is insufficient justification by itself.
Public-meaning and interface decisions follow
[CONTRIBUTING](../CONTRIBUTING.md#improving-documentation-in-four-passes), with
the authority granted in this plan; a separate human approval is not presumed.

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
destinations under the development/publication split; leave the frozen guide,
including its stamp table, and shared explanatory regions unchanged. Update
affected admission, transport, readers, fixtures and public meanings together
when the decision crosses those boundaries. Mechanical freshness establishes
agreement of copies; review and selected behavioral checks establish the
changed claim.

## Working the three plans together

[TRACE-ACCEPTANCE-PLAN.md](TRACE-ACCEPTANCE-PLAN.md) and
[TEST-OUTCOME-OVERHAUL-PLAN.md](TEST-OUTCOME-OVERHAUL-PLAN.md) reach some of
the passages, tests and decisions assessed here. This section owns the order in
which shared work settles and the selection of its broad verification; the
companions refer to it instead of restating it.

The sequencing rests on source and catalog inspection at `a9de3ccf`; the seam,
dependency and development/publication decisions were checked at `3d3f8e65`.
No catalog case, build or native experiment was executed for these readings.
The durations below are approximate figures from earlier development
runs on the maintainer's machine, not retained evidence; `run.json` records
the actual ones.

### Shared threads

Six threads need more than one plan. Elsewhere each plan proceeds alone.

| Thread | This plan | Acceptance plan | Overhaul plan |
| --- | --- | --- | --- |
| Actor fallback and transport result paths | Transport pilot | Fallback-compilation rehearsal | Run-flow fallback tests and the fallback-removal observation |
| Compiled-profile receipts | Import and receipt distinctions | Rehearsal of a capture reported despite unsuccessful application | Label-admission test and its credited claim |
| Association and reader responsibilities | DT-53/132 with the identity-relation findings | Association-equality rehearsal | Consumer and oracle callers and their credited coverage |
| Exec descendant lifetime | Remaining evidence and effect obligations | None planned | Survivor conversion and removal of inherited aftermath dependencies |
| Authority erasure timing | DT-63/124/125 | None planned | Credited last-use claim and any observation before teardown |
| Executable test seams | Selected admission changes, scope and transition costs | Change or remove one migrated seam; compare maintained decisions | Command implementation, caller migration and preservation of experimental evidence |

Take a shared thread in this order:

1. **Read once.** Where a rehearsal is planned, make its trace and this plan's
   comparison of perspectives one reading. Both inspect the same statements,
   producers, readers and assertions. Include the tests that enforce the
   rehearsed subject, so the overhaul's local rehearsal is not a second pass.
2. **Decide once.** Record the product disposition here, including any
   development/publication boundary. The rehearsal is evidence for it and not
   a gate: a thread without a planned
   rehearsal does not wait for one.
3. **Change once.** Implement the selected product, contract and test response
   through its actual owners. The overhaul owns its test changes; justified
   arrangement changes travel with the affected accounts. Preserve separate
   evidence for changed authority and changed behavior. Do not reserve an
   authorized remedy for the closing collection because of its implementation
   layer.

A disposition recorded before its rehearsal can correct a passage that the
arrangement judgment then moves or removes. A test response chosen before the
disposition selects authority after seeing the result, which the overhaul
rules out.

Where a thread produces both a test response and a product change, land the
test response first and exercise it against the existing behavior. A test and
a product changed in one step cannot show that the revised test still
distinguishes the old behavior from the new.

For the seam migration, establish the existing experiment's observations and
checks before changing its entry point. The new command and its callers may
then land together, with old/new evidence compared. Keep any change to judgment
or enforcement separate from that interface migration.

The exec-descendant conversion is not the subject of a DT entry. Assess its
remaining evidence and effect obligations with the
[same method](#judge-the-product-before-selecting-the-available-remedy), early
enough to support the selected removal of the survival requirement.
Handle other commitment questions the overhaul hands in the same way. They do
not join the DT coverage map.

### Bounded test-seam migration

Move a selected set of executable test seams into an explicit experimental
execution route under `test-input`, completing that work before final integrated
verification. This is part of the combined implementation, not a recommendation
to develop in the closing outflow. This plan owns selection and admission
decisions; the [overhaul](TEST-OUTCOME-OVERHAUL-PLAN.md#migrating-executable-test-seams)
owns implementation, caller migration and experimental equivalence. The
[acceptance companion](TRACE-ACCEPTANCE-PLAN.md#rehearsing-a-migrated-test-seam)
examines whether the arrangement reduces independently maintained decisions.

The selection is settled by caller combinations inspected at `3d3f8e65`,
using the [ten-field reference](../runner/README.md#test-seam-_test_overrides)
and the overhaul's [caller mapping](TEST-OUTCOME-OVERHAUL-PLAN.md#selected-seam-callers).
Migrate eight controls in two coherent groups:

- Worker interventions: `worker_timeout_ms`, `worker_pre_ready_hang_ms`,
  `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`, and
  `worker_kill_before_publish_slot`.
- Validator interventions: `validator_executable_path`,
  `validator_io_timeout_ms`, and `validator_total_timeout_ms`.

The narrower initial three-field selection would split existing experiments.
Pre-ready hang uses the worker timeout; timeout and attempt-in-flight cases pair
it with post-apply hang; kill-before-publication also uses it. Post-apply hang
pairs with self-signalling in sparse-failure and termination experiments.
Validator replacement pairs with its I/O deadline in no-reply/comparison cases
and with the aggregate allowance in phase cases. Moving these combinations
avoids maintaining two activation routes within one experiment.

Leave `worker_executable_path` and `actor_equipment_executable_paths` on their
existing admission paths. Their live substitution experiments do not need a
selected control in the same invocation. Sharing a checker or catalog family
with a selected invocation does not pull them into scope. This accounts for all ten
fields without requiring whole-family migration. Preserve their coverage and
explain the two remaining ordinary-request controls in the owning reference.

Preserve the existing semantic distinctions: `worker_timeout_ms` changes the
ordinary sentinel but does not change actor execution's separate allowance;
actor delay and kill controls still reach actor worker inputs. The paired
ordinary/actor controls in `timeout_applicability_specimens` establish that
contrast. Migration is an interface change, not permission to homogenize it.

Use `test-input run REQUEST` with explicit flags for the eight selected
controls, reusing ordinary run selection/orchestration and keeping `test-input
read` publication-only. Use one explicit experimental execution mode carried
outside the ordinary request through client transport and host admission.
Exact flag spelling is an interface-definition detail, not an open scope
question. Do not infer experimental intent merely from an override field.

Ordinary `run` and lower-level ordinary submissions reject any selected legacy
key, including inert values, before activating it. The experimental route takes
controls only through its explicit control arguments and rejects a request
also carrying a nonempty legacy override block. The two unselected substitutions
remain ordinary-only for this bounded migration; no existing selected experiment
requires combining them. Reuse internal driver representations where useful,
without leaving an ordinary activation bypass. This distinguishes interfaces;
it is not a new authentication claim.

The authorization covers only that selected route, retirement of its old
ordinary-request entry points, the evidence needed to identify experiments,
and the corresponding definitions, help, tests and developer accounts. It does
not authorize new fault mechanisms, fabricated outcomes, weaker cleanup or a
separate test-only build as a substitute for testing the normal executable.
Controls left outside the subset keep their explicit disposition; the migration
must not accidentally remove their coverage.

Apply the editorial freeze and development/publication checks above. Correct
the developer command, admission and evidence accounts through their current
owners without collecting guide errata. The selected migration does not depend
on making the old guide agree.

Use the settled scope and callers from the start. Supply any shared reporting
requirements to the overhaul's capability stage before the instrument checkpoint.
Land the executable and caller changes after that checkpoint, on an identified
rebuilt app, with their routed evidence. Complete the selected migration before
the final integrated run. The closing records receive its implemented boundary,
accepted costs and specifically retained limitations; they do not initiate another
engineering investigation.

### What proceeds independently

- From the start, with no result needed from another plan: this plan's
  coverage map and assessments; the rehearsals; the overhaul's reporting
  comparison, its capability and the cohort equivalence mapping; the selected
  seam mapping and command design; the development/publication split.
- A conversion or correction on a shared thread waits for that thread's
  disposition. Conversions and pure-computation cohort items also wait for the
  reporting capability.
- A selected product change waits for its substantive disposition and for any
  open instrument checkpoint. Necessary development/build check support lands
  before its baseline; seam and other behavioral changes land afterward unless
  already included in that baseline. Implementation layer creates no deferral.
- A remedy that adds controls to a population being migrated to pytest lands
  after that cohort's equivalence is established, so the mapping does not
  follow a moving population.

### Selecting verification by consequence

Use the existing routes. [Change verification](../tests/CHANGE-VERIFICATION.md)
maps a changed boundary to its selections, and `tests/run.sh --list` shows a
selection's prerequisites and dependencies. No further classification is
needed. What the combined work adds is a judgment about where breadth belongs.

An incremental signed build takes a few minutes and one case can be selected
alone. A product failure found late can therefore be located by rebuilding at
an intermediate commit and running that case. Breadth is the expensive part:
the default battery, 233 cases of which 165 need the app or worker, takes
roughly thirty to forty minutes. `preflight/build_refusal_controls`, with its
fresh builds, real acceptance and nested battery, takes about two hours. Each
holds the checkout lock, and tracked files stay unedited while it runs; a
second worktree is the existing way to keep working.

Settle at the start how many executors will work in this checkout at once.
With more than one, run the broad selections from a worktree pinned to a
commit, and name quiet windows for the live worker-wait pilot, which a
concurrent build or battery disturbs. With one, neither is needed.

Run the routed selection with each change, at the commit that carries it. Run
the default battery at the boundaries below. Keep one reason per commit; one
verification run may cover several commits.

Four kinds of change cannot rely on late localization. Give them their broader
evidence when they land:

| Change | Why it cannot wait | Evidence when it lands |
| --- | --- | --- |
| Outcome reporting and release readers, the overhaul's second stage | Every later result is read through them. | The constructed controls the overhaul names, then the instrument checkpoint below. |
| Runner installation, registry, reconciliation or cleanup (DT-34/35, DT-69–80) | A failed removal leaves launchd services and registry records that obstruct later selections and pruning. | The applicable `runner_byoxpc` opt-ins in a logged-in GUI session, with owned resources verified absent before other work continues. |
| Worker wait, release store, query eligibility or observers | The mutation anchors are exact; two accumulated changes make a failed anchor ambiguous. | `witness_contract/order_barrier_mutations` with each change. |
| Wire, layout, schema or identity derivation (DT-105–112, DT-88–94, DT-08/91) | Generated identities, goldens and every later build depend on them. | Regenerate through the owner; run `source_drift`, `runner_abi_layout` and the default build controls; rebuild before the next change. |

A document-only change needs its generator and `source_drift`, and no app.
Check [the build contract inputs](../docs/build_contract.py) before assuming a
change is document-only or test-only. `controller/src` holds the Rust unit
tests, so correcting a test's message there changes the development contract,
and the app must be rebuilt for the tree and the app to agree. `runner/Tests`
and most of `tests/` are outside those inputs.

### Three boundaries for broad runs

**Instrument checkpoint.** The overhaul's reporting capability changes the
path every result passes through. A defect in it can touch any case and cannot
be located by running one. Product remediation changes what is read. Keep the
two apart with one rule: a change to the shared reading path and a change to a
build-contract input never fall between the same two default batteries.
[The build contract](../docs/build_contract.py) prints one digest over those
inputs, and an unchanged digest shows that nothing held has moved.

Complete any required development/build publication split first, then take
a default battery immediately before the reporting capability lands. Land the
capability with no conversions or build-contract changes and run the default
battery again against the same app. Identify the old and new reporting revisions
and retain both batteries' raw inputs.

Supplement these two live runs with deterministic replay: give the old and new
reporting interpretations identical retained case reports, events, family/control
receipts, command accounts and selection/authority expectations. Exercise the
actual reconciliation, dependency and aggregation functions and the battery
validator in isolated scratch outputs. For unchanged authority, independently
specified counts, decisions and failure reasons must agree. Use separately
constructed informational/advisory fixtures with explicit expected differences;
the old reader's refusal of an unsupported new form is not a regression. Include
corruption, omission, contradictory authority and incomplete accounting beside
valid unfavorable judgments. Reuse the overhaul's controls rather than adding
a parallel replay framework or a new result schema just for this comparison.

A live status difference must be explained from the observations and replay.
Unexplained differences prevent crediting the checkpoint. A changed observation
is not automatically a reporting regression, and an explained failed required
check remains a failure requiring its appropriate resolution. Prefer replay and
affected-case verification to another broad battery. Replays are identified
investigations, not replacement live executions or reinterpretations of archived
releases; original evidence and producer semantics remain untouched.

After the checkpoint, conversions, cohorts and product changes proceed with
their own routed evidence. Finish shared reading support for those changes,
including seam evidence, in the capability stage. A later shared-reader change
needs the same deterministic comparison; add a new unchanged-app live pair only
when it affects live collection or has an integration uncertainty replay and
existing runs cannot resolve, stating that reason. Do not mix its verification
with a simultaneous build-contract change.

Read a completed battery with the revised release battery validator as a
direct investigation that credits no case: once at the checkpoint, and again
at the first battery that contains a converted case and the migrated
families. These are the least expensive places for that reader to meet real
output.

**Signed-app checkpoints.** After that, group product changes whose routed
selections do not overlap, and run one default battery for the group instead
of one per change. Locate a failure outside every routed selection with an
intermediate build.

**Final integrated verification.** Run once when the selected changes from all
three plans are in: source-drift and offline controls, a current signed build,
the default battery plus relevant opt-ins, then
`preflight/build_refusal_controls`. Its existing long acceptance experiment is
adapted, not supplemented with another broad battery. The publication split may
require building before an app-bound drift selection; respect admission and use
only offline checks before the build.

The current `control_release_battery` creates an annotated rehearsal tag,
regenerates guide stamps and runs real acceptance on the ZIP in a copied tree.
That is not an adequate positive control for intentional publication divergence.
Use its one live nested battery on an extracted, normally built development
candidate through the same extraction, artifact, command-accounting and battery
validation machinery. Record development identity and publication withheld;
that receipt cannot be admitted as release acceptance. Preserve app/signature,
source identity, provenance and cleanup checks. The existing Apple-response
stand-ins remain identified controls, not notarization evidence.

In the same case, strict release preflight/acceptance must reject the development
publication boundary, including attempted relabeling/tagging, before an expensive
battery or publication. Retain separate constructed positive and negative
controls for genuine release identity and strict publication freshness. Do not
rewrite the frozen guide in a fixture to manufacture a positive release result
for the changed product, or weaken real release acceptance to accept development
receipts. The overhaul owns the shared reporting/acceptance-reader changes;
this plan owns the development/publication distinction. These parts land before
the final run, with routed controls, not as a late release investigation.

Thus the long case establishes candidate execution and evidence interpretation
plus actual refusal of publication, not release readiness. Read its nested
output closely and credit those scopes separately. The future tagged release
requires the [release procedure](../docs/SIGNING.md#release-procedure) after the
guide rewrite and full publication checks. No release is cut here.

Retained archives keep their original evidence formats and producing contracts.
At the instrument checkpoint, run the read-only prune preview against them;
replay must not change their identities, outcomes or retention eligibility.
Retain interrupted resource and evidence ownership throughout.

## Completion and disposition

Complete each assessment with a present-tense judgment:

> We establish X within these limits. We judge Y acceptable or defective
> because Z. We choose this present treatment. It leaves this consequence,
> which we accept or find unacceptable for the resulting product.

When the accepted consequence falls on a user, say so in the judgment: what
they must do, avoid, arrange, check or refrain from concluding. The
[closing collection](#user-responsibility-outflow) reads these statements.

The judgment may conclude that an alleged defect is not established and a
narrower problem is resolved; that behavior is an accepted limitation with no
additional work warranted; or that a known defect remains deliberately retained.
In the last case, name the affected cases and costs. Assessment completed and
defect repaired are different states. A known defect can remain without an
automatic promise to repair it when the guide changes.

If a residual cost is unacceptable, select a justified remedy within scope or
state the specific missing authority, information or evidence that prevents a
responsible decision. A referral alone does not close that decision. Do not
route it to the maintainer merely because it changes signed code or a contract.

State an accepted limit beside the claim it qualifies in the current technical
owner, including contract and test accounts where appropriate. Leave frozen
publication material untouched; it does not prohibit a truthful technical
statement about the resulting product.

An unresolved evidence question can receive a completed, bounded judgment when
the present uncertainty and its consequences are explicitly accepted. Do not
claim the underlying behavior was established in that case.

Record which original claims were resolved, narrowed, withdrawn or deliberately
retained, what evidence supports each disposition, and what remains defective
elsewhere. A correction to one passage does not close every concern in its
family. An implementation that meets its current specification does not by
itself close a challenge to that specification or its credited tests. Correcting
technical accounts does not make the frozen publication current. Establish the
development/publication boundary without creating a guide-errata collection.

The management pass is complete when every observation has a traceable present
assessment, follow-up qualifications are represented, selected changes have
implemented and verified remedies or reasoned present retention decisions, and
the consequential [reserved material](#material-reserved-beyond-this-work) is
recorded. The combined work also requires the overhaul's conversions, cohorts
and selected seam migration, not merely their assignment to a closing record.
No observation is complete merely because it has a family, a future task or an
instruction to revisit the guide. Completion requires
accountable judgments, not a target number of defects or future obligations.

Before accepting the synthesis, check it in both directions: every original
observation has a disposition, and every proposed change rests on identified
claims and decisions. Resolve temporary allocation gaps and inspect cases that
seem harmless from one perspective. Further work follows from a chosen product
objective or new evidence; the accounting exercise creates no standing backlog
or requirements for the eventual guide rewrite.

## User-responsibility outflow

Near the end of the combined work, collect the responsibilities that the three
plans' judgments leave with users, considered together. Record them in
`records/USER-RESPONSIBILITY-OUTFLOW.md`, following the existing outflow
records: a date, the source revision and a status line. This plan owns the
activity because a responsibility follows from the product dispositions and
compatibility decisions it owns. The companions contribute what their own work
established.

### What belongs

An entry is a consequential condition under which someone who submits
requests, reads results, or installs and operates runners must do more than
follow the declared schemas. They must act, refrain, arrange their
environment, run a particular command or check, keep a conclusion within a
stated scope, or take responsibility for something PolicyWitness does not
establish for them.

Test each candidate by naming the action or restraint and what goes wrong for
that user without it. A candidate that supplies neither is one of these, and
stays in its assessment without being listed:

- **Implementation assumption.** The product's own producer, reader or
  maintainer upholds the condition. The user can neither meet nor violate it.
- **Optional practice.** It helps, but nothing false or harmful follows from
  omitting it.
- **Limitation without a user consequence.** It narrows what the instrument
  observes without changing an action or conclusion open to the user. A
  limitation becomes an entry when a user must restrict a conclusion because
  of it.

Duties of people building, testing or releasing PolicyWitness belong to the
working guidance, not here.

### Execution overrides

Someone using `_test_overrides` is not a user in this sense. The fields are an
instrument seam: a run through them is an experiment on PolicyWitness, not an
observation by it. For external runners, an intact copy of the app's service
is the supported use, and supplying one is a candidate responsibility.

The [bounded seam migration](#bounded-test-seam-migration) resolves the selected
interface and engineering work before this collection. Read its established
boundary and retained limitations here. Experimental operators' duties belong
to developer and test guidance; include an outflow entry only when there is a
consequence for an ordinary user's action or conclusion. A state that only a
substituted executable can produce does not become an ordinary caller's duty
merely because the experiment can produce it. Keep the shipped component's
obligations distinct from the experiment's evidence.

### Sources

Use the accumulated judgments of all three plans, including dispositions that
changed no code or test:

- This plan's completed assessments, particularly accepted limitations,
  deliberately retained defects and checks delegated to another party.
- The rehearsal assessments, for obligations the current arrangement places on
  a caller that surfaced only by reconstruction across documents. An
  obligation that exists only in a rehearsed hypothetical establishes nothing.
- The overhaul's preservation and reduction account, for what stops being
  established on a user's behalf when enforcement is withdrawn or a credited
  claim is narrowed.

Read them together. One responsibility can rest on several findings. Some
appear only in combination: an accepted limitation here and a relinquished
assertion there can bear on the same conclusion.

### Entries

Write one entry per responsibility, not per finding:

- the condition and the responsibility, stated for the role that carries it;
- the consequence of not meeting it;
- what in the product's own output indicates that the condition applies, or
  that nothing does;
- its standing, established or unsettled, with the reason;
- support from the resulting behavior and evidence, with its scope and class.
  Refer to a decisive experiment where necessary, not a history of the finding
  or why an older arrangement differed.

A responsibility is **established** when the evidence supports the condition
within stated limits and a completed disposition leaves it with the user. It
is **unsettled** when the condition rests on an observation that was not
traced or reproduced, or a product decision genuinely lacks required authority
or information. An obligation existing only in a hypothetical is excluded.
For a pending decision, name what is missing and its consequence.
Do not promote an unsettled candidate because listing it as an obligation
seems the cautious choice.

### Guide freeze

The outflow states what users are responsible for. It does not compare those
responsibilities with guide passages, record where the guide omits or
misstates one, propose wording, or carry requirements to the guide rewrite.
Include or exclude a responsibility on the product's behavior and the
dispositions alone.

### Timing

Draft it once the last disposition, rehearsal assessment and reduction account
are recorded. It depends on judgments, not on the final runs. Finalize it
after the [final integrated verification](#three-boundaries-for-broad-runs):
restate an entry, or move it to unsettled, when that run did not bear out the
change or observation it rests on.

## Material reserved beyond this work

Keep the user-responsibility and maintainer-judgment outflows as temporary
handoffs about the resulting product. Git retains findings, plans, commits and
abandoned alternatives; do not build another comprehensive development history.
The guide author need not reconstruct the old guide's organization or defend
the new product against it.

Before retaining a historical statement beyond Git, name the consequential
mistake a competent future maintainer could make without it. If there is no
convincing answer, omit it. Useful exceptions include decisive experiments or
evidence limits that cannot be reconstructed, deliberate non-obligations that
might look like missing checks, consequential design reasons not reasonably
discoverable in code, and failed experiments establishing a durable limit on
observation or inference. Prefer present-tense limits and reasons in their
natural permanent owners. Preserve necessary experimental evidence through
existing ownership/retention mechanisms, not a new archive policy.

### Judgments for the maintainer

Draft `records/MAINTAINER-JUDGMENT-OUTFLOW.md` with the user-responsibility
outflow and finalize both from verified results. Collect only consequential
choices, reasons and genuinely unresolved matters needed to transfer
understanding to the resulting product and its accounts. It is not an approval
queue or a mandatory entry for every change. Reference user duties in their
outflow rather than repeating them.

For each necessary entry, state the present responsibility or limitation, its
reason and evidence, its current owner, and any authority or information still
missing. Use revision, symbol, case or statement identifiers where needed.
Transfer lasting understanding to that owner during the work. Reasons for a
test's non-enforcement belong in its suite account and changing commit; shared
observation/judgment/enforcement principles belong in test working guidance.
Do not create a permanent registry of withdrawn assertions or dispositions.

Where multiple suites depend on a proposition, use the acceptance plan to
establish whether there is one shared premise or distinct scoped obligations.
Preserve that distinction without duplicating normative choices or centralizing
away the observation boundaries. The future maintainer must understand present
authority without consulting this investigation. The temporary outflows are
consumed by the subsequent guide/release work and then retired.

### Release account

Record briefly what a release after this work will meet because of it: the
changes a reader of test results or release evidence encounters, such as
outcome semantics, the evidence-format boundary, the converted cases and the
new experimental execution route with its retired ordinary-request controls.
Include anything the release procedure must do differently. It supplies the
release notes.

### What outlasts the release

No routine dependency on `records/` should remain after the release. Retire the
plans and temporary handoffs once consumed; Git preserves them. Lasting product
limits, deliberate non-obligations, consequential reasons and useful verification
rules live in their current contract, suite or working-guidance owners. Additional
historical explanation must meet the consequential-mistake test above.
