# P3 adjudication: restatement comparison

**Run.** Workflow `wf_61d89a2f-30c`, 2026-11-20, at `2bcdfeb8`. Eight Sonnet
readers ran as `Explore` agents, which do not receive the repository's
`CLAUDE.md`. Each reported opening only its assigned owner file. Raw answers
are in `answers.json`. Ground truth is in `KEY.md`.

## Result by rule

**Rule A (fallback compilation and `policy_check`).** The three owners agree
with each other and with the code:

- eligibility (accepted admission, no delivery error, terminal `xpc_error`);
- whole-request capture for an ordinary request;
- per-actor captures in request order, with `policy_check` null for an
  `actors` array;
- no host reply alongside a fallback capture;
- the capture establishes neither worker progress nor the cause of the lost
  reply.

`controller/README.md` does not define eligibility; it routes to the
surfaces. `40-envelope` states the null and omission rules without the
eligibility chain. These are differences of scope, not of substance.

**Rule B (`cleanup_trigger`).** The two defining owners give the same fixed
table as `PWDisposition.triggerForStop`: `32-lifecycle` and the failure
contract. Both include the three actor additions and pass-through for
unmapped reasons. Both say the trigger restates the stop reason rather than
being a second observation.

`41-diagnostics` owns the trigger-to-cause table, and its mapping matches
`causeForTrigger`. It states the full chain needed for a named cause. Its
reader correctly reported that the file does not give the trigger's
derivation. No owner contradicts another.

One weak lead has no action. The failure contract lists `cleanup_trigger`
under a heading "Raw host facts the record needs", and the reader
paraphrased it as a "raw fact". The sentence under that heading says the
trigger is derived from the stop reason, and the same file says it is not
independent of `poll_stop_reason`. The reader extracted both.

**Rule C (`query_first`).** `31-steps.surface.md` gives every condition in
`KEY.md`:

- the collection chain;
- setup;
- the native answer;
- unique association by bytes, with the retained query identity.

`docs/QUESTIONS.md` gives the meaning (collection before the phase's actions)
and the limit (earlier actions can change later state), and says the relation
does not settle agreement. It defers the conditions to another section. No
reader drew an agreement or causation claim from either file.

## Dropped rule

Only `35-profile.surface.md` states what a `captured` receipt implies, so the
rule has a single owner and nothing to compare.

## Destinations

- Pass 4 entries: none.
- User-duty draft: none.
- Guide-rewrite note: none.

The restatements of these three rules are consistent across their owners
after Passes 1 and 2.
