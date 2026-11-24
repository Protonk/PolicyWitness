# Plan the responsibilities maintainers owe callers when PW changes

The deliverable is `docs/CHANGE-RESPONSIBILITIES.md`, a short statement for
the maintainer changing an observable commitment and the publisher shipping
that change. Refresh this plan during the late README migration. Use the
commands actually shipped, the changes callers encountered and the evidence
from release review. Internal 1.0 is the project's maturity milestone. Any
promise between releases needs an explicit scope and a publisher prepared
to honor it. [Transition and handoff](../CLI-TRANSITION-PLAN.md#internal-10-completion)

## Develop the policy from a caller's use

1. **Identify the commitment.** Take a supported use of the old release and
   state what a caller supplied, what PW undertook to do and which decision
   the caller could make from its answer. Locate the authoritative statement
   and its conditions. Include accepted inputs, defaults, limits, refusals,
   controls, examples, access to the guide and what a result permits a reader
   to infer. A change in the time or source of an observation can matter
   while its field name and type stay the same. [Public meanings](contract/README.md) · [Interface definitions](../controller/interface/README.md)
2. **Classify the difference.** Compare the old and proposed use under each
   build's own contract. A change breaks a supported use if its input, script
   or reader must change, or if a formerly warranted interpretation would
   now be wrong. For an added result value, ask whether a supported reader
   could rely on a closed vocabulary. For a bug fix, distinguish the stated
   promise from the behavior callers actually saw and explain the consequence
   of correcting it. Exact build matching governs admission. Surface stamps
   locate changed declarations. To judge compatibility, say what else the
   caller must change or reconsider once the new binding has been reviewed.
   A change to the binding rule itself also needs classification. [Admission identity](CONTRACT.md#contract-identity-public-contract) · [Surface history](CONTRACT.md#contract-identity-surfaces-stamp)
3. **Specify the work before publication.** The maintainer identifies the
   affected producers, readers, contract owners and projections, obtains
   evidence that distinguishes the old and new behavior, and updates the
   affected owners together. A non-breaking claim names the supported uses
   it covers and the evidence for their preservation. A breaking change
   names what callers must change or reconsider and why the change is
   justified. The publisher checks that account against the app being
   shipped, its bound guidance and acceptance evidence, and puts the caller
   consequence where users of the old release can find it. When the change
   belongs in a signed component, change and verify that component. An alias
   or adapter needs a caller use that justifies maintaining it. [Contributor guidance](../CONTRIBUTING.md#the-command-line-as-an-api) · [Release procedure](SIGNING.md#release-procedure)
4. **Give existing artifacts an explicit disposition.** For a saved specimen,
   determine what must be reviewed before rebinding a working copy. For an
   example, decide when to regenerate from the new build and when a migration
   is warranted. For a saved result, preserve the original bytes, producer,
   applicable meanings and limits. If a reader cannot interpret that producer,
   specify the deliberate refusal and where to find the matching material.
   Show how the diagnostic, help or release notes lead a caller to those
   actions and the guide for the producing release. A fresh run is new
   evidence. [Caller responsibilities](REQUIREMENTS.md) · [Historical and current disposition fixtures](../tests/fixtures/disposition/README.md) · [Publication](SIGNING.md#publication)
5. **Settle the promises between releases.** Decide which command spellings,
   artifact readers, meanings and guide delivery routes have a stability
   commitment, for which releases and supported uses. Decide where and when
   to give notice, where a deprecation interval or migration is owed, and
   when clear release notes and an explicit refusal suffice. State the limits
   of each promise. Use the cost and benefit to actual callers to settle open
   choices such as a rename alias and its lifetime.

## Try the proposed responsibilities on three changes

| Change | What a maintainer and publisher should be able to show |
| --- | --- |
| Rename `test-input` to `test` | Try a saved script with the old spelling and the reviewed spelling. Exercise both specimen emission and execution with a control. Explain the alias or refusal actually shipped, what the script's owner must edit and where they learn this before relying on the new command. [Current CLI](../controller/README.md#cli-surface-contract) |
| Add a named extension example | Try bare `example`, the newly accepted name and an unknown name. Identify which old argument refusals changed and what the build guarantees about the emitted specimen. Run the printed bytes and check the access distinction. Have a guide reader regenerate the specimen under the new contract and retrace the recipient change. Account for the supported reader before calling the addition non-breaking. [Example commitment](REQUEST.md#contract-request-specimen-emit_example) |
| Correct the result of a validator collection failure | Use the 0.3.8 correction for a declared-unapplied actor. A prior trial reported `finished` despite a decode failure. Read the dated observation and the released checker, including the independent file effect. Explain what changed for a reader selecting finished runs, what the worker was still seen to do and how to interpret the old result under its producer. [Release notes](releases/0.3.8.md) · [Atlas account](../tests/atlas/ATLAS-BUILD-PLAN.md#which-reader-would-notice-a-wrong-account-of-how-the-worker-exited) |

At the handoff, replace proposed outcomes in these examples with the actual
decisions and their limits. Have a second maintainer apply the draft to the
examples and a publisher use it to explain the caller action from the release
material alone. Resolve differences about supported use, evidence or notice
before adopting the policy. Keep the settled statement focused on duties.
Caller choices stay in REQUIREMENTS, public meanings in the contract tree,
contribution methods in CONTRIBUTING and publication steps in SIGNING.
Link those owners to the adopted statement where a reader needs it and
retire the plan to Git.
