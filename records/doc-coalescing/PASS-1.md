# First ownership pass

This is the first pass of [DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md),
against `9eb81540`. It maps owners and proposes edits; it changes no public
meaning, implementation, example or permanent guide. The next pass is bounded
by the edit sequence below.

## Ownership and treatment

“Owner” below identifies where a description is authored. The contract still
distinguishes the component that produces a claim from the receiver that checks
it. Audience-specific explanation is retained when it serves a different need.

| Concept | Authoritative account | Other presentations and audience need | Treatment |
| --- | --- | --- | --- |
| Completion success | `envelope.data.select` and `.success_findings`; host `reply.record.outcomes` supplies the reported outcome's meaning | Guide result-reading, catalog and exit summaries help users decide what to inspect; CONTROLLER explains separate diagnostic/result computation | Keep the normative mapping and the guide's short operational explanation. Use internal guide links for secondary summaries; the tour keeps the implementation boundary. Do not turn host completion into evidence certification. |
| Actor withholding and attribution | `diagnostics.execution.reply_checks`, `diagnostics.issue.subject.withholding_scope`, actor-local failure rules and `actor_evidence.actor.reader_scope` | Guide scope table; tour's carried-label/action selection and projection order | Keep effects and applicability in the contract. Put the carried-row attribution limit beside the guide's retention statement. Preserve the tour's mechanism and the limited scope of its constructed test. A reference may replace a duplicate full paragraph only while its consequential qualification stays visible. |
| Reporting degradation | `reply.failure.publish`, `reply.failure.associations`, retention fields and reader applicability | Guide rich/minimal account, outcome catalog, comparison-reading warning; tour's writer/receiver branches | Correct the guide's encoding-only description to validation or encoding. Keep rich/minimal, no-comparison and unchecked-association distinctions locally. Shorten secondary summaries with links; producer fallback and recipient checking are distinct obligations. |
| Accepted/refused lesson inputs | Currently the `create`/`capture_typo` corpus requests and repository materializer; guide independently authors its shell inputs | REQUEST-GRAMMAR invokes the renderer; standalone guide teaches work-directory setup, saved results and independent effects | App ownership is a proposed destination, not current reality. Move input definitions only when both consumers can obtain them; then remove the literal guide request, typo-construction recipe and manual alignment duty. Preserve the teaching workflow. |
| Lesson expectations | Separately authored corpus expected code/path data; explicit live CLI/direct-XPC and guide-workflow assertions | Guide explains expected refusal and observes effects; Swift tests exercise decoding/admission | Keep semantic expectations independent of app input production. Shared input acquisition does not justify deriving expected verdicts from the producer or merging distinct entry-boundary controls. |
| Current emitted example | `controller/src/example.rs::EXAMPLE_DOCUMENT`; contract extracts the request and its probe member | Current app prints a read-hosts specimen; contract demonstrates its form; checks exercise emission and admission | Retain this successful pattern. It is a different example from the create/refusal lesson. Its no-argument, same-build-admission promise cannot silently acquire deliberately refused output. |
| Evidence accounts | Existing graded support owners, each attached to an assertion and scope | Contract renders detailed support; tours explain the particular checks they cite | Compact rendering can follow later. The emitter's publication support and the example's extraction/admission support overlap in citations but establish different things; do not merge them merely because a test path repeats. |

Exact nodes, source paths, assertion scopes and presentation anchors are in the
two narrow reports, RESULT-READING and REQUEST-LESSON. They distinguish
source/check inspection from execution; no new behavioral evidence is claimed.

## Ordered edit sequence

1. **Correct existing guide wording.** Beside retained actor rows, state that
   identity, launch and action findings still qualify attribution. In both
   reporting-failure descriptions, include validation as well as encoding.
   Qualify the reported outcome/exit by receipt of an admitted fallback: failed
   rich and minimal writers can leave no decodable report. Link to the existing
   no-admitted-report account. These align the guide with already accepted
   meanings; the public policy choices remain settled.
2. **Consolidate secondary explanations locally.** Review the result-reading
   section, catalog, exit summaries and tour together. Keep the guide's reading
   order, scope table and short failed-attempt example; secondary summaries
   point to its detailed account. Specifically replace the duplicate attribution
   paragraph under `diagnostics.execution.reply_checks` with a reference to
   `diagnostics.issue.subject.withholding_scope`, preserving the rule's trigger,
   effects, stop-reason/raw-record retention and public dependency. Remove
   CONTROLLER's separate closing completion restatement, keeping its link beside
   the actual computation and constructed-control description. Keep actor joins
   and degraded branching as useful mechanism. These are the first concrete
   deletions; adding a link alone earns no authoring-reduction credit.
3. **Evaluate reusable excerpts only if duplication remains.** Existing compact definitions of
   success, withholding and degraded associations are candidates. Compare direct
   reuse with the local shortening above. Derivation must replace a maintained
   copy rather than introduce another authored summary. If worth doing, extend
   an existing generator with explicit source nodes, destinations and checks;
   the current contract generator only copies the stamp table into the guide.
   General node-to-guide extraction is not an existing capability. Preserve
   standalone reading, inherited applicability, link rebasing and both
   history-aware and source-copy freshness checks. A new canonical summary above
   existing definitions would add another alignment duty. This pass recommends
   the small edits above first; no general excerpt renderer is proposed now.
4. **Prepare the lesson's input migration.** Account for target substitution,
   identity, differing specimen IDs and the guide's dependencies on saved
   `create.json`. The typo, missing-nonce repair, successful capture, compiler
   helper and BYOXPC recipes depend on those inputs or formatting. Moving two
   JSON objects alone does not retire that chain's maintenance. Keep raw,
   malformed and repetition fixtures in their test owners.
5. **Expose the pair only after a concrete interface decision.** Choose how a
   caller obtains each document and supplies its target, which identity is
   inserted, and what publication/refusal means. The current extraction reads
   a fixed Rust JSON constant and optional member; it supplies no generalized
   materialization or command selection. Additional app material remains useful,
   but neither this pass nor the future help announcement selects that API.
   Retain independent corpus and guide-workflow checks during migration.
6. **Compact support after the content boundaries settle.** Prefer a compact
   reference with accessible detail; keep consequential evidence limits beside
   the claim. Existing owner metadata is excluded from the public snapshot,
   while public gap prose is included. A rendering change and a public-meaning
   change therefore need separate review. No concrete support-entry merger is
   justified by this pass, and appendix work is deferred until there is a
   concrete presentation problem or duplicate assertion to address.

## Verification and scope of this pass

The narrow audits read actual production branches and assertions, including
constructed completion/withholding/degradation checks, corpus admission and
live-effect checks, and the guide fence executor. The coordinator checked the
projection and reporting-fallback paths, guide dependencies, existing copy
machinery, generator output ownership and public-payload support exclusion.
The prior controller raw runs are pruned; their historical summaries are not
fresh execution credit here.

Pass 2 needs the documentation/source-drift checks for its actual edits.
Changing guide commands later also requires the owning
`witness_contract/guide_workflows` case; corpus tests do not execute guide shell
text. App changes require their applicable signed-build and behavioral checks
under repository guidance. This mapping pass creates no test run or worktree.
Only record/plan links and diff formatting are checked for its own deliverable.

## Assignments and disposition

| Assignment | Actual model | Output and scope |
| --- | --- | --- |
| Result-reading ownership | `gpt-6.1-sol`, fresh context | RESULT-READING; three semantic boundaries and their exact descriptions/checks |
| Request lesson ownership | `gpt-6.1-sol`, fresh context | REQUEST-LESSON; input/expectation ownership and guide dependencies |
| Consolidation boundary review | `gpt-6-astra`, fresh context | REVIEW; challenge proposed reductions and preserve public scope/independence |

No agent ran tests, changed public files or delegated further. The coordinator
integrated the small reports. REVIEW accepts the ownership allocation with its
local-meaning, input-independence and interface qualifications; the sequence
above incorporates them. Pass 1 is complete. Pass 2's small edits are ready;
the later app-exposure decision remains explicit and does not block them.
