# User guide plan for 0.3.8

Move toward a PolicyWitness that asks less of its users while preserving the
experiments they need, and a shorter guide that explains the decisions they
still own.

**Draft 0, November 23.** The [draft](PolicyWitness.md) now runs from a first specimen through result interpretation, repair, handoff, retries, actor comparisons and external-runner cleanup. The [product ledger](../../records/guide/PRODUCT-CHANGES.md#investigation-decisions-for-draft-0) gives decisions on all nine guide investigations.

The [admission comparison](../../records/guide/work/evidence/draft-closeout/admission-comparison.tsv) gives one row per refusal, including the diagnostic route and the structured answer that matched the saved signed run. The [result extracts](../../records/guide/work/evidence/draft-closeout/observations.json) include the repaired specimen's digest and the host and worker path fields. The [prototype source snapshots](../../records/guide/work/evidence/draft-closeout/probe-sources.md) show where admission stopped and where the phase observer waited. The [trace handoff](../../records/TRACE-CLOSEOUT-PLAN.md) locates the writer’s conclusions and original evidence.

The first two shell blocks were exercised together with `PW` pointing to signed development build 1666. The fixture printed `66697273740a`. The external-runner recipe uses the previously exercised install, verify and recovery path. Its installation evidence comes from the November 20 opt-ins on build 1634.

## Reader and maintainer pass

Start with the draft and the executable. Can the reader make the first specimen, judge a result and explain what a colleague would need to reproduce it? Note the first place the reader had to guess and what they tried. The maintainer will read the guide, decide what needs correction for 0.3.8 and determine whether to commission a separate trace review. Publication follows the editorial decision.

Carry requests for better interactive access into the [CLI and guide transition](../../CLI-TRANSITION-PLAN.md). Once the reader and maintainer have used the guide studies, keep the inputs a continuing investigation needs, including the four saved runs for `compare`. Retire the consumed working papers to their Git revision as the trace handoff does.

## Ways to make progress

- **Press on an instruction.** Take something a user must learn today. What
  could PW do that would let the instruction disappear? Try the simpler
  behavior against two cases the user still needs to distinguish. For a bug
  report, give the evidence to someone who already knows `help`, `example`,
  `test-input` and `run`. Which question can they resolve? Which observation
  or one-field comparison could the app supply? [Repair passage](PolicyWitness.md#repairing-a-refused-specimen) · [Checking a repair before its effects](../../runner/Sources/ADMISSION-CHECK-PLAN.md)
- **Read a saved run as its recipient.** Start with the user's symptom and two
  plausible explanations. Read one envelope before looking at the fixture notes
  or a second run. Write down what it settles, the fields supporting that answer,
  and the observation that would distinguish the remaining explanations. When
  reading stalls, record where the fact lives. An existing field may need a
  clearer presentation, a fact PW observed may be worth retaining, or the
  deciding observation may belong to the app or caller. For a proposed field,
  identify who could observe it and when. Find two cases in which knowing it
  would change the reader's next decision. [Draft passage](PolicyWitness.md#why-couldnt-my-app-open-this-file) · [Saved runs and open question](../../records/guide/GUIDE-STUDIES.md#what-can-a-saved-run-tell-me-about-a-failed-open) · [Handoff section](PolicyWitness.md#handing-a-run-to-someone-else) · [Host's later path view](../../runner/Sources/HOST-PATH-OBSERVATION-PLAN.md)
- **Settle a responsibility.** When a choice belongs to the user, state when
  it applies and what they do in [User responsibilities](../REQUIREMENTS.md). Keep the reasoning
  in the working record. If this changes a test, identify which assertion can
  go and how we still check the evidence PW owes. Update any affected public
  statement along with its implementation and tests.
- **Draft or study a passage.** Write a piece of [draft 0](PolicyWitness.md) when
  the evidence supports it. Try its example against the signed app. A passage
  that's hard to write can reopen an app question. A lesson whose scope is
  uncertain can go to guide studies with the observation that would settle it.

Use these methods where reader feedback calls for an investigation. For a
0.3.8 correction, record the decision beside the finding and enter changes
to behavior, public statements or test assertions in the product-change
ledger. Carry later work in the plan for the affected verb.

## Sources and constraints

- [Requirements and expectations](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md) collects current behavior to scrutinize.
  Its [handoff findings](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md#what-can-a-colleague-establish-about-a-run-they-did-not-see)
  include how a recipient can match a compiled-profile receipt to a saved request.
- The [test decisions](../../records/guide/USER-RESPONSIBILITIES-AND-TESTS.md#decisions-for-the-guide) group the numbered findings by the assertion they affect. The [Responsibilities section](PolicyWitness.md#responsibilities) is the common reading path.
- [Experiments to preserve](../../records/guide/EXPERIMENTS-TO-PRESERVE.md) gives paired cases for testing a simplification.
- [Guide studies](../../records/guide/GUIDE-STUDIES.md) explores when a lesson holds in a reader's application.
- [Writing a PolicyWitness bug report](../../records/guide/BUG-REPORT.md) supplies a worked report to try from both sides of the handoff.
- Investigations into what PW could take on sit beside the code they would change, as `*-PLAN.md` files under `controller/` and `runner/`. The guide ledger records their 0.3.8 decisions. Later investigations can conclude that today's behavior is preferable.
- The [product-change ledger](../../records/guide/PRODUCT-CHANGES.md) lists every change this work makes to PW's behavior, its public statements or its tests, with the passage that teaches it and its compatibility effect. It gives the command for listing changed public statements.

Keep section and finding numbers stable for the next reader. Use the checks
that exercise the changed behavior. [Verification guidance](../../tests/CHANGE-VERIFICATION.md)

Draft 0 is the review copy. The published guide stays frozen at
`3d3f8e65` during this work.
[Publication boundary](../publication.py)
