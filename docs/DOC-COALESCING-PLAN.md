# Repeated documentation coalescing passes

Reduce the number of independently maintained descriptions that must change
when a public meaning or app representation changes. Work through the passes
below in order for a bounded topic, verify the result, then repeat on another
topic. A smaller reference is useful; fewer synchronization obligations are
the main measure of progress.

The app-owned [example](../controller/src/example.rs) and
[controller tour](CONTROLLER.md) provide starting patterns. Additional example
material can be useful before the planned `policywitness help` replacement.
Keep that material and its verification separable from today's command, so
the future interface can reorganize them without inheriting its design.

## Pass 1 — Establish ownership

For each selected concept, identify its authoritative definition, audiences,
other presentations and supporting checks. Start with this allocation:

| Content | Owning account |
| --- | --- |
| Public meanings, applicability, refusals and preservation | [Authored contract](contract/README.md) |
| Concrete build-specific specimens | App source, with extracted presentations |
| Implementation mechanisms and rationale | Controller, worker and architecture tours |
| User tasks and interpretation exercises | [User guide](PolicyWitness.md), later help |
| Evidence supporting a commitment | Existing graded support records |

Record a compact map: concept, owner, current copies, audience needs, checks,
and proposed treatment. Distinguish intentional audience explanation from
duplicated facts. Retain unresolved ownership questions explicitly.

## Pass 2 — Consolidate explanations

Use that map to retain, extract, shorten, move or link repeated material.
Keep public conditions and consequences with their normative meanings;
mechanism and rationale can live in the tours. Derive repeated reader-facing
explanations where useful, preserving the standalone guide's usability.
Review inherited contract scope and public snapshot changes. Obtain a concrete
maintainer decision before changing a public commitment's meaning or owner.

## Pass 3 — Replace maintained examples with app-owned material

Choose small examples that eliminate existing copies or alignment duties.
Extract documents and useful fragments from their actual owner. Keep expected
refusals and independent effect observations separately authored, and establish
admission through the existing execution path. Preserve distinct purposes such
as apply-only verification. Defer permanent catalogs, selection syntax and the
future help interface to their own design; migration itself can be an exercise.

## Pass 4 — Compact the support presentation

Keep a useful support reference and consequential evidence limits beside each
claim. Consider rendering detailed citations, check scopes and execution
provenance in an evidence appendix or companion view from the same records.
Consolidate entries only when their assertions and scopes actually coincide.
Distinguish reduced reading volume from reduced authoring work; preserve the
differences between source inspection, constructed checks and native evidence.

## Complete a cycle

Review the exact definitions, copies and alignment duties removed, any new
machinery required, and the public distinctions preserved. Use existing
generators and checks where they fit. Regenerate owned outputs and run the
documentation checks; add applicable behavioral verification when code or
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
inputs while retaining independent expectations and observations. Support
presentation remains the next pass; the first map's limits on merging distinct
assertions still apply.
