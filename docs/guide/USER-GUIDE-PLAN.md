# User guide plan for 0.3.8

Stage 1 is in progress. Stages 2–4 have not started.

This plan prepares the 0.3.8 rewrite of the user guide,
[docs/PolicyWitness.md](../PolicyWitness.md). Before rewriting, it works out
what a user must do for a result to mean what they intend, what work they can
leave to PW, and what they must arrange around it. It then drafts a
substantially shorter guide from that material. The plan ends at draft 0: a
complete, readable guide that the next round of guide writing can press
against when looking for problems in the app.

## Sources and constraints

- [Requirements and expectations](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md)
  is the working record. Each section poses a question with its own procedure
  and standard. Its findings are numbered and carry their evidence. Findings
  cite each other by number (finding 20 independently identifies the assertion
  in finding 9), so keep numbers stable. When two findings combine, keep the
  survivor and leave the other pointing to it.
- [Writing a PolicyWitness bug report](../../records/guide/BUG-REPORT.md) is a
  second stage 1 record. It gives a user one report they could file and shows
  how to write another.
- The guide is frozen. Development builds refuse a `docs/PolicyWitness.md`
  that differs from `3d3f8e65` ([publication boundary](../publication.py)).
  Nothing in this plan edits that file, lifts the freeze or changes the
  publication boundary.
- [GUIDE-REWRITE-OUTFLOW](../../records/GUIDE-REWRITE-OUTFLOW.md) is a
  placeholder and carries no requirements into this work.

## Stage 1 — Explore and enrich the requirements and expectations

**Purpose.** Make the record's findings ready to use, so that later stages
select from findings instead of discovering them.

Work through each section's question with its procedure. Collect new findings,
and refine, combine or discard existing ones. Judge each finding by its own
section's standard:

- A user responsibility identifies the test decision it would change: which
  outcome can vary while PW still owes the same evidence, and which assertions
  survive.
- A finding about what PW can be trusted to do identifies work the user can
  leave to PW. It says what they can omit, under which conditions, and where
  their own effort or judgment resumes.
- A lesson stands on its own for a reader who never sees the FAQ.
- A finding about arrangements outside PW supplies the recipe line a colleague
  would have to write, in enough detail to try by hand or script, with any
  tradeoff that would change whether they use it.
- A finding about scope names the detail whose removal makes the smaller
  experiment answer a different question.
- A handoff finding takes a claim about one run and identifies which words a
  colleague can defend from the envelope and which need an outside observation.

Keep the evidence and reasoning beside each finding, including run IDs and
their availability, so a reader can judge which findings are ready to use.
Leave a discarded finding as one line giving the reason.

Accepting a user responsibility is the maintainer's decision, because it
changes what the tests demand of PW. A responsibility that would also change a
public statement names that statement.

Use the worked bug report to test the utility of `help`, `example` and
`test-input` together. Starting with the installed app, can a reporter find a
specimen they can share, reduce it while preserving the symptom, and show a
recipient which result matters? In the worked report, give the commands and
observations a user can reproduce today. In the requirements and expectations
record, capture where a transition needed knowledge the preceding command
didn't supply. For instance, this build's `help` lists `run`, `example` and
`result`. How would someone who has just run the example discover
`test-input read --target`? Use gaps like this to judge proposed improvements
to the commands together.

**Result.** Every finding in the record either meets its section's standard
or says what it lacks. The maintainer's acceptance of each user responsibility
is recorded beside it. The worked report includes a replayable comparison and
the original evidence a recipient needs to check its claim.

## Stage 2 — Create `docs/REQUIREMENTS.md`

**Purpose.** Publish the user's obligations in one place, as the authority
for stages 3 and 4.

Distill the accepted responsibilities into a clear, declarative list. Each
requirement states when it applies and what the user must do, so that a reader
can tell whether they have met it. Exclude all tracing to tests or code: no
links to them, no case, suite or symbol identifiers, no implementation
rationale and no proposed test dispositions. The record, not this document,
notes which finding each requirement came from.

A requirement states what the user does; it does not restate product
behavior. Where a requirement makes a published product promise unnecessary,
such as a winner among repeated values, that promise changes in stage 3 with
the tests that enforce it.

`docs/*.md` is inside the `source_drift` prose and link scan
([scan scope](../../tests/suites/source_drift/README.md)). Write a duration
or byte size there as a limit span, or leave it to [LIMITS](../LIMITS.md); a
prose-baseline addition counts as added unverified prose. Add the document to the
[README index](../../README.md#documentation). The frozen guide cannot link
to it.

**Result.** `docs/REQUIREMENTS.md` is committed and indexed, and
`tests/run.sh --suite source_drift` passes.

## Stage 3 — Alter the user-facing tests against the published requirements

**Purpose.** Stop tests from demanding product choices that a requirement
leaves to the user, while keeping every check of evidence that PW still owes a
user who meets it.

User-facing tests are assertions about what a user submits and what PW
returns or does: admission, execution evidence and CLI output, whether they
live in a live suite or in a Rust, Swift or Python check. Build, signing,
release-acceptance, drift and harness checks stay adversarial and are outside
this stage.

Start from the assertions that accepted findings name, then use the record's
procedure to find others. For each affected assertion, state what the
requirement settles and what evidence PW still owes a user who meets it. Use
that distinction to choose one of these:

- Delete an assertion whose expected value the requirement makes unnecessary.
- Restructure a case whose remaining obligations need a different input or
  control. Account for each independent obligation before folding away
  paired controls.
- Keep a useful observation as informational, with no judgment
  ([outcome meanings](../../tests/README.md#declared-observations-and-judgments)).

A single case can contain both an expendable expectation and an essential
check, so decide per assertion. When a public statement changes, update its
authored surface, readers, fixtures and documentation together and regenerate
([maintenance checklist](../../AGENTS.md#maintenance-checklist-when-changing-things)).
A change to query eligibility also reruns the
[order-barrier mutation control](../../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls).
A finding that would add product behavior, such as a new conflict refusal,
needs its own maintainer decision before it joins this stage.

**Verification.** For each deleted or demoted assertion, name the surviving
check that still observes the evidence PW owes. Where a misleading pass is
plausible, show that check rejecting wrong evidence. Run the changed cases
through `tests/run.sh` with a fresh `PW_TEST_OUT_DIR`, then the default battery
against a signed build.

**Result.** The changed tests and public statements are committed. The record
gives each affected finding its disposition and the run that verified it.

## Stage 4 — Write draft 0 of the user guide

**Purpose.** Produce a complete, readable guide that the next round of guide
writing can press against when looking for problems in the app.

Write the draft at `docs/guide/DRAFT-0.md`. `docs/REQUIREMENTS.md` is the
authority for user obligations: the draft can present them or route to them,
but it adds none and contradicts none. Draw on the record for what else a user
needs to understand, arrange or entrust to PW. Select and organize that
material for a guide substantially shorter than the current one. The record's
questions served discovery; the draft can give the material whatever order
serves the reader.

Draft 0 need not reproduce the current guide's generator-copied regions,
stamp tables or scenario rows. How the published guide carries or routes to
that material is the next round's decision.

Run each example against the current signed app. Where the app's behavior
makes a passage hard to write truthfully, keep the passage accurate and note
the difficulty in the record instead of smoothing it over.

Use the worked bug report as a reading check. Could someone coming from
draft 0 produce the specimen, comparison and evidence that made the report
actionable?

**Verification.** `docs/guide/` is outside the drift scan, so check the
draft's links with [docs/markdown_reader.py](../markdown_reader.py). A reader
who knows PW can read the draft from start to finish without meeting a
placeholder.

**Result.** Draft 0 is committed at `docs/guide/DRAFT-0.md`, complete and
readable, with `docs/PolicyWitness.md` unchanged. Producing it completes this
plan.

## Where this plan stops

This plan does not replace `docs/PolicyWitness.md`, lift the guide freeze or
cut a release. The record remains available to the next round.
