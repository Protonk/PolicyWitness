# User guide plan for 0.3.8

Move toward a PolicyWitness that asks less of its users while preserving the
experiments they need, and a shorter guide that explains the decisions they
still own.

## Ways to make progress

- **Press on an instruction.** Take something a user must learn today. What
  could PW do that would let the instruction disappear? Try the simpler
  behavior against two cases the user still needs to distinguish. For a bug
  report, give the evidence to someone who already knows `help`, `example`,
  `test-input` and `run`. Which question can they resolve? Which observation
  or one-field comparison could the app supply?
- **Read a saved run as its recipient.** Start with the user's symptom and two
  plausible explanations. Read one envelope before looking at the fixture notes
  or a second run. Write down what it settles, the fields supporting that answer,
  and the observation that would distinguish the remaining explanations. When
  reading stalls, record where the fact lives. An existing field may need a
  clearer presentation, a fact PW observed may be worth retaining, or the
  deciding observation may belong to the app or caller. For a proposed field,
  identify who could observe it and when. Find two cases in which knowing it
  would change the reader's next decision. [Draft passage](PolicyWitness.md#why-couldnt-my-app-open-this-file) · [Saved runs and open question](../../records/guide/GUIDE-STUDIES.md#what-can-a-saved-run-tell-me-about-a-failed-open)
- **Settle a responsibility.** When a choice belongs to the user, state when
  it applies and what they do in [User responsibilities](../REQUIREMENTS.md). Keep the reasoning
  in the working record. If this changes a test, identify which assertion can
  go and how we still check the evidence PW owes. Update any affected public
  statement along with its implementation and tests.
- **Draft or study a passage.** Write a piece of [draft 0](PolicyWitness.md) when
  the evidence supports it. Try its example against the signed app. A passage
  that's hard to write can reopen an app question. A lesson whose scope is
  uncertain can go to guide studies with the observation that would settle it.

Pick up any of these questions in any order, individually or in parallel.
Whoever takes one can investigate it, make and verify a scoped change, and
record the decision and its evidence beside the finding. Leave an open
question with what would resolve it and continue with other work.

## Sources and constraints

- [Requirements and expectations](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md) collects current behavior to scrutinize.
  Its [handoff findings](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md#what-can-a-colleague-establish-about-a-run-they-did-not-see)
  include how a recipient can match a compiled-profile receipt to a saved request.
- The [test decisions](../../records/guide/USER-RESPONSIBILITIES-AND-TESTS.md#decisions-for-the-guide) group the numbered findings by the assertion they affect. The [Responsibilities section](PolicyWitness.md#responsibilities) is the common reading path.
- [Experiments to preserve](../../records/guide/EXPERIMENTS-TO-PRESERVE.md) gives paired cases for testing a simplification.
- [Guide studies](../../records/guide/GUIDE-STUDIES.md) explores when a lesson holds in a reader's application.
- [Writing a PolicyWitness bug report](../../records/guide/BUG-REPORT.md) supplies a worked report to try from both sides of the handoff.

Keep section and finding numbers stable for the next reader. Use the checks
that exercise the changed behavior. [Verification guidance](../../tests/CHANGE-VERIFICATION.md)

The writing target is a complete, readable draft 0. The published guide
stays frozen at `3d3f8e65` during this work.
[Publication boundary](../publication.py)
