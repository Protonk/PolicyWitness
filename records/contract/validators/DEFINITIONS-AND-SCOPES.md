# Disputed meanings and scopes behind the validators' disagreement

A draft for review, for register row `R-36` in
`records/contract/CONTRACT-LEDGER.md`. It follows the maintainer's position
of 2026-11-10: keep the finding, do not settle the architecture by counting
validators, and make the disputed meanings and scopes explicit before
choosing which implementation to change. It decides nothing. Sibling
artifacts are named by path without links, under the records link rule.

It is organized the way the maintainer described the contract's intended
shape: **definitions** say what the records mean; **applicability** says
which rules govern an ordinary reply, a preparation-failure reply and a
reporting-failure reply; **obligations** say what each component checks and
what it does on failure.

**What this rests on.** `records/contract/validators/COMPARISON.md`, a
delegated reading, for what each reader checks ("row N" below is a row of
its table B), and `records/contract/validators/RUN.md` for what was
observed ("D1" to "D13" are its candidates). The coordinator has not
re-read the readers' source for this sheet. Statements about the contract
and the guide were read by the coordinator.

S is the host's self-check, R the controller, P the test harness's reader.

## What the run does and does not establish

- Each reply was built once as a typed Swift record. S judged that record.
  It was then encoded to the binary reply format, decoded by the Rust
  reader, and presented as JSON; R judged the decoded record and P judged
  that JSON. "The same bytes" in the ledger was shorthand for this chain.
- Twelve candidates were compared across all three readers, and the
  readers' final judgments differed on each. The thirteenth concerns a JSON
  null, which the typed Swift record cannot hold: it was compared between R
  and P only.
- The run shows that the three definitions of validity differ. It does not
  show how often, or whether, production emits such replies.
- Five candidates come from general checks on any actor-form reply. Those
  checks were not compared exhaustively.

## Definitions in dispute

Each definition below would settle a family of cases at once. For each:
the question, what each reader now assumes, the cases it settles, and what
the public text says today.

### 1. What a preparation failure is

**Question.** Does `preparation_failure` mean that execution never began?
If so, which records does that rule out?

**Agreed by all three readers.** Every actor is `launch_refused` with no
launch and no subprocess record; there are no steps, no extension events,
no transfers and no resource rows; the host's run disposition is
`not_attempted`; every phase is `not_reached`.

**Not agreed.**

| A reply that also has | S | R | P | Case |
| --- | --- | --- | --- | --- |
| a host region row (row 13) | objects | objects | accepts | D1 |
| a phase marked as arrived (row 17) | objects | objects | accepts | D2 |
| a phase ordering record with proceed set (row 16) | accepts | objects | objects | D3 |
| a custody row, or a phase marked complete (rows 14, 18) | objects | objects | objects, through a general rule | none |

**Public text today.** C:198-202: "no launched actors. Observation arrays
are empty." It does not say execution never began, and does not name the
arrays.

**What a definition would settle.** If a preparation failure means nothing
was launched and nothing ran, then a region row, an arrival and a proceed
flag each contradict it, and D1 to D3 follow without three separate
rulings. Whether a host region row can exist before any launch is a fact
about the host that this sheet has not established.

### 2. Which replies may carry the record

**Question.** Is `preparation_failure` defined only for the actor form?

**Readers.** S and R object to an ordinary reply that carries it. P does
not examine the field on an ordinary reply (row 2). Case D11.

**Public text today.** C:198-202 sits under "Actor evidence ownership" and
does not say.

### 3. What an identifier is

**Question.** Is every identity in a reply nonempty, within one byte bound
and free of NUL? Which identities does that govern?

| Identity | S | R | P | Case |
| --- | --- | --- | --- | --- |
| declared action identity (row 20) | no bound | bounded, in the preparation rule only | bounded, in the preparation rule only | D4 |
| `phase_id` (row 23) | no bound | no bound | bounded | D6 |
| `actor_id` (row 30) | not found | bounded | bounded | none run |

**Public text today.** C:200-201 says "unique bounded declarative phase and
action identities may remain", without saying what bounded means or where
else it holds. Request admission bounds identities on the way in; nothing
public says a reply's identities are bounded.

**What a definition would settle.** One statement of what an identity is,
and that it holds for every identity in every reply, settles D4 and D6 and
removes the oddity that action identities are bounded only inside the
preparation rule.

### 4. Absent, null and empty

**Question.** For a list or record that may be omitted, do absent, null
and empty mean the same thing?

| Field | S | R | P | Case |
| --- | --- | --- | --- | --- |
| `extension_events` absent where an empty list is expected (row 9) | treats absent as empty | requires it present | requires it present | D5 |
| `preparation_failure` given as JSON null | cannot be asked | reads null as absent | tests for the key's presence | D13 |

**Public text today.** C:326: "Optional fields are absent, never filled
with fabricated defaults", said of the binary frame. Nothing says whether
an absent list equals an empty one, or whether public JSON may carry null.

**What a definition would settle.** This belongs to the record definition,
as the maintainer says: per field, whether it is required, and whether
absence carries a meaning different from empty. D5 and D13 follow.

### 5. An actor's visits

**Question.** Is `actors[].visits` the list of that actor's phases as
declared, or the phases in which it was observed to be activated?

| Relationship | S | R | P | Case |
| --- | --- | --- | --- | --- |
| `visits` equals the ordinals of that actor's phases (row 28) | not checked | exact equality | one direction: each phase is listed; extras pass | D8, D9 |
| a phase's `actor_visit` is that actor's running count (row 27) | at least 1 | exact | exact | D7 |
| an actor's `index` is its position (row 30) | not checked | exact | exact | D10 |

**Public text today.** The guide calls `visits` "the phase ordinals it was
activated in". The preparation-failure baselines, in which nothing was
activated, carry `visits` for their declared phases, and R and P object
when the list is emptied (D8). So the readers treat `visits` as declared
and the guide's words describe it as observed.

**What a definition would settle.** This is the maintainer's distinction
between having a record for an action and having evidence that it ran.
Saying which of the two `visits` is settles D8 and D9 and corrects either
the guide or the readers.

### 6. The partition

Not in dispute as a rule. All three implement: the identities declared in
the phases are exactly the step identities plus the extension-event
identities, none repeats, declared order agrees with record order for each
kind, and each record belongs to the phase it names. The readers differ in
when they skip it, which changes diagnostics and not judgments. It is
listed here because the public text never states it.

## Applicability in dispute

Which rule families each reader applies to each kind of reply, as read.

| Rule family | Ordinary reply | Preparation-failure reply | Reporting-failure reply |
| --- | --- | --- | --- |
| The partition | S, R, P | Equality skipped by all three. R and S keep the order and association clauses; P skips them too. | None of the three |
| The preparation rule (definition 1) | not applicable | S, R, P, each with its own terms | None of the three |
| Setup, equipment, application, gates, custody | S, R, P | S, R, P | None of the three |
| Actor table and phase association (definition 5) | R and P in full; S in part | R and P in full; S in part | **P only** |
| Step structure | S, R, P | vacuous: no steps | R and S check only that no comparison remains; **P still checks structure** |
| The form of the degradation | not applicable | not applicable | S, R, P |

### The reporting-failure reply

The most consequential open question, in the maintainer's words: what this
kind of reply promises, which requirements still apply, and what a consumer
may conclude from the records it retains.

**What happens now.** The host re-issues a result its own check rejected,
keeping the records and removing every comparison. R and S then hold the
re-issued reply only to the form of the degradation. P goes on to check the
actor table, phase association and step structure, and objects to defects
there (D12).

**Two readings, neither established.**

- P is enforcing an ordinary requirement outside its scope. A degraded
  reply exists to preserve evidence that failed ordinary validation, so
  holding it to ordinary structure defeats its purpose.
- Some structural relationships remain mandatory even in a degraded reply,
  because without them a consumer cannot tell which actor or phase a
  retained record belongs to. Then R and S are checking too little.

**Public text today.** The guide says that with `evidence_retained` true,
queries, attempts and child observations survive, every comparison is
omitted, and retained ordering observations are diagnostic: the reply
certifies no per-step order. Nothing says whether a retained record's
association with its actor or phase can be relied on. C:202 calls
preparation failure the "sole exception" to the partition and does not
mention this reply.

**One further case.** A reply can carry both records: the host re-issues a
preparation-failure reply that its self-check rejected. None of the three
applies the preparation rule or the partition to it.

## Obligations as they stand

What each component does when a requirement it checks does not hold. This
is description, from the comparison's section 0 and the run.

| Component | Checks | On failure | What a consumer sees |
| --- | --- | --- | --- |
| Host self-check | before encoding its result; stops at the first failing condition | re-issues the result as a reporting failure, keeping records and removing comparisons; if that fails too, a minimal reply | `runner_reporting_failed`, with the diagnostic and a summary of the original |
| Controller | after admitting a reply; collects every issue | flags the reply and withholds its own disposition; the report is published unchanged and `result.ok` is unaffected | `disposition_integrity: "invalid"` and the issues, beside the host's report |
| Harness reader | when a test asks; collects every error | returns the errors to the calling test | a failing test |

In the run every objection by the controller was a flag. For all 101
replies the report would still have been published.

The three roles differ legitimately in what they do on failure. Where they
assess the same requirement over the same information, the maintainer's
position is that a difference in judgment needs a reason grounded in the
contract. The definitions and scopes above are where those reasons would be
written.

## What settling these would not do

- Agreement among the three is not correctness: all three could agree on a
  wrong rule. The definitions have to come first.
- A corpus of constructed replies run through all three would test stated
  commitments across implementations. The experiment's patch
  (`records/contract/validators/RUN.patch`) drives all three from one
  Swift-built reply and is a possible starting point.
- Generating the three from one implementation would remove the
  independence that exposed these differences. The maintainer has set that
  aside.
