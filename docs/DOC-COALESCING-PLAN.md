# Repeated documentation coalescing passes

Improve readers' ability to find, understand and apply the required contract.
Work through the passes below in order for one bounded topic, verify the
result, then repeat on another topic. Preserve consequential conditions and
evidence limits. Shorten, expand, repeat or relocate material when that serves
the reader. Fewer words, files or references do not by themselves establish
improvement. Reducing independently maintained descriptions is useful when it
also makes the account clearer or more reliable.

The app-owned [example](../controller/src/example.rs) and
[controller tour](CONTROLLER.md) provide starting patterns. Additional example
material can be useful before the planned `policywitness help` replacement.
Keep that material and its verification separable from today's command, so
the future interface can reorganize them without inheriting its design.

## Pass 1 — Establish ownership

Choose three concrete questions the topic's readers need answered. Identify
where the current account makes those answers ambiguous or difficult to find.
For each selected concept, identify its authoritative definition, audiences,
other presentations and supporting checks. Start with this allocation:

| Content | Owning account |
| --- | --- |
| Public meanings, applicability, refusals and preservation | [Authored contract](contract/README.md) |
| Concrete build-specific specimens | App source, with extracted presentations |
| Implementation mechanisms and rationale | Controller, worker and architecture tours |
| User tasks and interpretation exercises | [User guide](PolicyWitness.md), later help |
| Evidence supporting a commitment | Existing graded support records |

Record one compact map: reader question, concept, owner, current presentations,
checks and proposed treatment. Distinguish useful audience explanation from
duplicated facts. Retain unresolved ownership questions explicitly. Keep the
topic fixed through this cycle; note adjacent opportunities for a later one.

## Pass 2 — Consolidate explanations

Use that map to resolve the identified reading problems by retaining,
explaining, extracting, shortening, moving or linking material.
Keep public conditions and consequences with their normative meanings;
mechanism and rationale can live in the tours. Derive repeated reader-facing
explanations where useful, preserving repetition that makes a guide or
reference usable on its own.
Review inherited contract scope and public snapshot changes. Obtain a concrete
maintainer decision before changing a public commitment's meaning or owner,
or adding or changing a public interface. Routine editorial and implementation
choices remain with the executor; pass boundaries alone do not require approval.

## Pass 3 — Replace maintained examples with app-owned material

Choose small examples whose existing owner can supply a clearer or more
reliable presentation while eliminating copies or alignment duties.
Extract documents and useful fragments from their actual owner. Keep expected
refusals and independent effect observations separately authored, and establish
admission through the existing execution path. Preserve distinct purposes such
as apply-only verification. Defer permanent catalogs, selection syntax and the
future help interface to their own design; migration itself can be an exercise.
Retain the current arrangement when no suitable example serves the selected
reader questions; this pass does not require a new command or abstraction.

## Pass 4 — Clarify the support presentation

Keep a useful support reference and consequential evidence limits beside each
claim so readers can distinguish the commitment from what supports it.
Consider rendering detailed citations, check scopes and execution
provenance in an evidence appendix or companion view from the same records.
Consolidate entries only when their assertions and scopes actually coincide.
Judge relocation by its effect on the selected reading tasks, including the
navigation it adds. Distinguish reduced reading volume from reduced authoring
work; preserve the differences between source inspection, constructed checks
and native evidence.

## Complete a cycle

Answer the original three questions with the resulting reading paths and show
which ambiguities or navigation burdens improved. Record any remaining limits,
copies or alignment duties removed, new machinery required and public
distinctions preserved. These concrete comparisons establish the result;
additional reviews are useful only when they resolve a specific uncertainty.
Use existing generators and checks where they fit. Regenerate owned outputs
and run the documentation checks; add applicable behavioral verification when code or
meaning changes, following [test guidance](../tests/AGENTS.md). Combine checks,
reuse evidence only with reviewed applicability, and prune disposable output
after review. A pass may conclude that the current arrangement should remain.

## First cycle

Begin ownership mapping with completion success, actor withholding and degraded
reporting across the authored envelope/diagnostics/reply surfaces, the guide's
result-reading section and CONTROLLER. Include the accepted/refused request
lesson in [REQUEST-GRAMMAR](REQUEST-GRAMMAR.md), its
[corpus](../tests/fixtures/request_contract/examples.json), guide exercise and
current emitted example. Produce the small ownership map and an ordered set
of concrete edits before rewriting these accounts or extending the app.

The [first ownership map and edit sequence](../records/doc-coalescing/PASS-1.md)
complete Pass 1. Narrow [result-reading](../records/doc-coalescing/RESULT-READING.md)
and [request-lesson](../records/doc-coalescing/REQUEST-LESSON.md) audits, followed
by a [boundary review](../records/doc-coalescing/REVIEW.md), support the map.
The [second pass](../records/doc-coalescing/PASS-2.md) completes the identified
wording corrections and two duplicate removals, with reviewed public dependencies
and documentation verification. Broader projections and app exposure retain
their stated prerequisites; the next pass prepares the lesson's input migration
and its concrete interface decision.

The [Pass 3 proposal](../records/doc-coalescing/PASS-3-PROPOSAL.md) specifies the
two input owners, consumer migration, verification and a narrow acquisition
interface. The maintainer selected the separate `lesson` command; implementation
and [acceptance](../records/doc-coalescing/PASS-3-PROPOSAL.md#implementation-and-acceptance)
complete Pass 3. The corpus and both teaching documents now consume app-owned
inputs while retaining independent expectations and observations.

The [fourth pass](../records/doc-coalescing/PASS-4.md) completes support
presentation for this cycle. Each claim retains its qualifications and links
to citations and execution provenance rendered from its existing owner record.
No owners were merged: this pass reduces citation clutter in the reading path,
while the earlier passes removed maintained copies and input-alignment duties.

## Second cycle

The second cycle takes the per-step comparison record as its topic and is
complete. Its [record](../records/doc-coalescing/COMPARISON-CYCLE.md) states
the scope, the three reader questions and the ownership map, then each pass's
result, the one consultation, verification and the adjacent opportunities kept
for a later cycle.

## Third cycle

The third cycle takes path and object observations as its topic and is
complete: submitted paths, the worker's `observed_path`, fresh-descriptor
identity records and the host's `path_diagnostics`. Its
[record](../records/doc-coalescing/PATH-OBSERVATIONS-CYCLE.md) states the
scope, the three reader questions and the ownership map, then each pass's
result, the one consultation, verification, two decisions left with the
maintainer and the adjacent opportunities kept for a later cycle.
