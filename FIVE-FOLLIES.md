# Five follies

The drift-removal plan replaces one verdict with a set of records, and records
are easy to add. This document reports what happened when the whole of that new
surface was asked one question, after the question had already claimed a victim.

The victim was `target_mutation.steps`, the list of step IDs whose attempts
removed a query's submitted path. The producer emitted it, the encoder checked
it against the raw attempts, the consumer rederived it from the same attempts
and compared, and the tests checked that defective lists were rejected. Nothing
did anything else with it. It is gone from
[DRIFT-REMOVAL-PLAN.md](DRIFT-REMOVAL-PLAN.md) as of D6.42; the status it
qualified stays, because the producer's query-exclusion guard is knowledge a
reader recomputing from the attempts would not apply.

Then the same question was put to every other object the plan adds. The five
entries below are the whole result, in the order they were examined — including
the last one, which came out clean. A list with nothing clean in it would be a
verdict, not a search, and would say more about the reviewer than the plan.

**The question is not "is this derived."** D0 explicitly permits derived
descriptive fields, and most of what PolicyWitness reports is a derivation over
two channels. The question is narrower: *does anything do something with this
besides checking that it is right?* A field whose only readers are its own
encoder invariant and its own consumer validation has cost, a test surface, and
no consumer.

## 1. `conditions.prediction_unavailable_pairs`

The dossier's one backward glance. The controller reads the reply it just
received, collects every step carrying `query_plan:prediction_unavailable_pair`,
and reports the distinct `(operation, filter_kind)` pairs. The plan mentions it
four times, all definitional — the shape, the rule, and twice what it holds when
there is no usable reply.

Two things make it the strongest case. The set is already published: the guide
lists the unavailable pairs, and `source_drift` checks that list against
`predictionUnavailableOpFilters` in `ProbeRunner.swift`, which holds three pairs
today. And it is the only dossier field computed from the runner's answer —
everything else is gathered before the runner is invoked. That single exception
is why D5 has to rule on what the dossier does with an unsupported reply.
Removing it makes the dossier purely pre-invocation, which is a boundary
statable in one sentence, and costs a reader nothing: the per-step limitations
remain.

## 2. `comparison_conditions`

A run-level object whose value space has exactly one member,
`{ "unestablishable": ["state_stability"] }`, with an encoder invariant that
rejects anything else.

It is not pure ceremony, and the distinction is worth drawing precisely: its
*presence* carries a bit — present beside `steps` on an ordinary reply, withheld
on both `runner_reporting_failed` levels — while its *value* carries none. So
the honest description is a one-bit field encoded as a nested object, plus a
checker for the constant. The bit is real. Whether it is worth the shape, and
whether a checker for a literal earns its place in two implementations, is the
open question.

## 3. `specimen.references`

Ten RFC 6901 pointers — the plan's example lists ten — from the envelope root to
the records the dossier does not own. The keys and values are fixed by envelope 5, "not computed from presence" —
a pointer to a withheld or absent record is still present. So the map is a
constant, and the consumer "requires `references` to carry exactly the fixed keys
and values."

Zero bits, by construction. What it buys is orientation for a person opening a
stored envelope without the contract to hand, which is a real thing to want and
a reason to keep it. The folly here is not the map but the check: an equality
test against a literal can only fail when the producer is broken in a way no
reader would notice, and it adds one more place to edit when a path moves. The
cheapest fix keeps the map and drops the assertion.

## 4. `obligations.sandbox_attribution`

Its rule is a function of two things sitting beside it in the same object:
`observation`, and whether `limitations` contains
`exec_result_failed_after_spawn`. A reader holding the comparison record can
evaluate it with no knowledge the record does not already give them.

Its neighbour is the useful contrast. `runtime_target_identity` also looks like a
restatement, but its rule consults the mapped attempt filter, and that mapping
is producer knowledge — thin, but real, and the same kind of justification that
saved `target_mutation.status`. `sandbox_attribution` has no equivalent. What it
does have is the exact three-way pattern the step list had: the producer emits
it, an encoder invariant checks it against its own inputs, and the consumer
checks it again, so the whole apparatus exists to catch a disagreement only a
producer bug could produce.

## 5. `policy.imports.closure_sha256`

The one that survives, and the reason the criterion above is worth stating.

By the derivability test it looks worse than some of the others: it is a hash
over the applied source and the successfully hashed import records, all of which
ship beside it. It is also the only one of the five that exists today, as
`policy_closure_sha256` in `sbpl-check` output; the plan relocates it into the
dossier rather than inventing it.

It survives because something does something with it. Two runs' closures compare
in one equality test, without diffing record lists — the cheapest possible answer
to "were these the same inputs?" A reader cannot readily recompute it, since the
framing and ordering of the hash are not published and a partial scan changes
what went into it. And its consumer is a person or a diff, not a validator. That
is the shape a derived field should have.

## Also examined

Three more were looked at and left alone, for the record rather than for
balance. `binaries.*.manifest_*` duplicates data that ships inside the app, but
it is what explains a mismatch verdict and what keeps a stored envelope readable
without the app beside it. `library_identity.*.on_disk` is `present: false` with
a null hash for every shared-cache image, which is nearly always, but it is also
the field that distinguishes an override, which is the case someone debugging
would care about. `policy.imports.records[]` is primary observation, not a join.
