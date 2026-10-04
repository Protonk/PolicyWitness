# Limits section revamp: goals

How the limits documentation is meant to change, written down so the changes
can be judged against an intent rather than against each other. These are
goals, not acceptance criteria. The mechanics of regeneration stay as described
in [LIMITS.md → Maintaining this document](LIMITS.md#maintaining-this-document).

## Readers

The main reader is a user reading the Limits section inside the
[user guide](PolicyWitness.md#limits), where [LIMITS.md](LIMITS.md)'s shared
block is copied verbatim. Their questions are "will my specimen be admitted?"
and "why was it not?". The secondary reader is a developer working with an
agent, using the document as a forcing function: a stated premise is something
to test, and two bugs were closed in one turn each because the prose stated
their premises plainly (exec pipes opened before apply; prediction queries
writing deny lines). The second reader is served behind the wall, not in the
shared text.

The document should not try to answer "why does my evidence differ from
`sandbox-exec`?". That question invites caveats about system behavior
PolicyWitness does not promise.

## Two editorial rules

1. Shared prose states only what the user can observe with the shipped app: a
   reply field, a refusal's name, a count, a marker. That is its grounding.
   Transclusion into the guide is a commitment, not a check, so the sentence
   has to be checkable from the reader's seat.
2. Mechanism moves, it does not vanish. Every "because" sentence lives in a
   LIMITS-only section beside the symbol it rests on, so the agent can open the
   code and the premise can be reopened when the platform changes.

## Shape of the shared section

- An intro that gives the lookup path: a refusal names a field; the Specimen
  admission table has a "Refusal names" column carrying the exact
  `admission_failure.field` text, measured live, one row per limit.
- A short "How to read the tables" block stating the conventions once (bytes
  not characters, inclusive maxima, monotonic durations), defining the four
  Control words (Fixed, Flag, Derived, Not enforced) and saying which question
  each of the five tables answers and what kind of consequence its limits have.
- The tables, immediately after, so the lookup is short.
- "Interactions that matter" after the tables, trimmed to observable
  consequences. Each bullet names the limits it relates, which bounds the list:
  it is not a place for advice about behavior outside the repository.

## Deliberately not done yet

- No per-row "kind of limit" field. The section descriptions in "How to read
  the tables" carry the kinds; rows that are exceptions already say so in their
  consequence text.
- No lexical guard on shared prose. If developer vocabulary drifts back into
  the shared block, the cheap backstop is a denylist in the generator's check.
- No change to the FAQ beyond the sentences this work made false.

## How to judge a change

Read the shared block as the user: can every sentence be verified by running
the app and reading the reply? Then read the premises as the agent: does every
mechanism sentence name a symbol or admit it is source-inspected? Then check
that nothing was lost: a sentence removed from the shared block should be
findable behind the wall or in the manifest's coverage notes.
