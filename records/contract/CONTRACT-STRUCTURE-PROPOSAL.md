# Proposed structure for the restructured CONTRACT.md

Third version, revised on the maintainer's two reviews of 2026-11-10 (both
kept in `records/contract/CONTRACT-MAINTAINER-NOTES.md`). The table of
contents and the placement of surfaces stand from the second version and
are repeated here unchanged. What this version changes is the model inside
a section: what counts as a rule, how the reach of a consequence is stated,
and which relationships have a defined expression now. It adds a second
worked example, a termination gate. Serialization and generators are still
deferred. Sibling artifacts are named by path without links, under the
records link rule.

## Table of contents (unchanged)

```
1  The contract identity                               [identity]
2  Definitions
   2.1 Components   2.2 Boundaries   2.3 Artifacts
   2.4 Kinds of report   2.5 Surfaces (generated)
3  Running a specimen
   3.1  Accepted input         request (with runner selection), policy,
                               probes, actors, extensions, refusals
   3.2  Delivery to the host   transport, wire
   3.3  The host's report      reply, steps, lifecycle, actor_evidence,
                               equipment, profile
   3.4  The controller's assessment and output
                               envelope, diagnostics, dossier
4  Managing runners                                    [installation]
5  Reporting the version                               [identity]
```

Nineteen surfaces: the thirteen present names and `identity`, `extensions`,
`reply`, `actor_evidence`, `diagnostics`, `wire`. Maintenance moves to
`docs/contract/`. What each section establishes is as in the second version.

## What changed from the second version

| Review point | Change |
| --- | --- |
| The form must hold commitments beyond validation | A rule is a commitment of one of three kinds: the component **acts**, **reports** or **checks**. Only a check is made of comparisons. Production is a kind of rule with obligations of its own, not a preface to the rules. |
| "Bears on" must separate the object inspected from the reach of the consequence | Replaced by four separate statements: what a rule **reads**, what it **decides**, what its failure **prevents or withholds**, and what it **leaves standing**. |
| Some machine-readable meaning should shape the model now | Four relationships have a defined expression: a reference to an object, a condition, a dependency, and an effect with its scope. Each rule in the worked example carries them. |
| Growth and repetition | A section's parts are used only where they add something. A field's row says what the field is; what a value rests on is said once, in the rule that produces it. No closing paragraph restates the rules. |
| A second example | A termination gate: an ordering commitment, a produced record, a check, and consequences that cross record boundaries. |

## The model

### Three kinds of rule

| Kind | The commitment | Its parts |
| --- | --- | --- |
| **acts** | A component does something, or does not, in a stated order relative to other events. Creating a fresh worker, waiting, activating a phase, never replaying a submission. | When; the action; the ordering it keeps; the effect when the precondition fails. |
| **reports** | A component produces a record or a value with a stated meaning. | When it is produced; each value and what that value rests on. |
| **checks** | A component examines records it has received. | When it applies; the conditions; the effect of a failure. |

Every rule also has an identifier, one component (section 2.1) and one
boundary (section 2.2).

"When" is stated differently by kind, which is how production and
interpretation stay apart. For **acts** and **reports** it is a state of
the run: a commitment about the producer. For **checks** it is the presence
of a record: a commitment about the reader that holds wherever the record
appears.

### The reach of a consequence

Four statements, each made separately wherever it is not empty.

| Statement | Answers |
| --- | --- |
| **Reads** | Which records and fields the rule looks at. |
| **Decides** | Which one object's state the rule sets: a field's value, an action taken or not, a report admitted or not. |
| **Prevents** or **withholds** | Which later actions do not happen, or which conclusions the component declines to state. |
| **Leaves** | Which records and assessments are unchanged by a failure, and so remain as they were reported. |

This is what "dependent claims" needs in order to mean something: for each
finding, the object decided, the conclusions withheld, and what still
stands.

### Four relationships with a defined expression

These are forms of statement, not a file format. Each is written the same
way wherever it occurs, so that it can later be held as data without being
reinterpreted.

1. **Object.** A path into a defined artifact, with named index variables
   bound once in the section. Example: `report.phases[p].termination_gate`.
2. **Condition.** An object, a relation and an object or a literal. The
   relations are a closed list: `=`, `≠`, `<`, `≤`, `present`, `absent`,
   `in`.
3. **Dependency.** `X requires C1, C2, …`: an assertion or an action, and
   the conditions it rests on.
4. **Effect.** `otherwise: <component> <verb> <object>`, with the verbs a
   closed list: `refuses`, `does not`, `cancels`, `reports`, `flags`,
   `withholds`. An effect carries its **prevents** and **leaves** lists.

A rule is written in sentences and carries these expressions beside them.
The sentences are for reading; the expressions are what must not be
ambiguous.

### Parts of a surface section

Covers; Records; Definitions; Rules; Known gaps; Example. A part is written
only if it has something to say that no other part says.

## Worked example: a termination gate

Chosen because it has an ordering commitment, a produced record and a
check, and because its consequences cross records: the gate is reported on
one phase, rests on another actor's record and another phase's
observation, and its failure stops phases that belong to neither.

Everything stated below was read in source by the coordinator on
2026-11-10: the host's gate evaluation and schedule walk in
`runner/Sources/PWRunnerCore/ActorScheduler.swift`, and the controller's
gate checks in `controller/src/porcelain_actor.rs`. Nothing was run. Items
marked *open* were not read.

---

### Termination dependencies

*Surface `actor_evidence`. Section 3.3. The request side, how a phase
declares a dependency and when the declaration is refused, is in "Actors
and phases", section 3.1.*

**Covers.** A phase may run only after another actor has terminated. The
host decides this at a *termination gate* when the schedule reaches the
phase, and reports the gate on that phase.

In this section `p` is the dependent phase, `s` the source actor it waits
for, and `f` the source's final phase.

**Records.**

| Object | What it is |
| --- | --- |
| `report.phases[p].termination_gate` | The gate: `source_actor_id`, `source_final_phase_id`, `outcome`, `activation_eligible`, `observation.capture_ordinal`, `capture_ordinal`, `wait`. |
| `report.actors[s].owned_reap` | The host's record that it collected the source's exit status itself: `capture_ordinal`, `observed_ns`, `ownership_unbroken`, `departure_requested`, `stage`, and the native process identifier and wait status. |
| `report.phases[f].activation_observation`, `report.phases[p].activation_observation` | When the host activated a phase: `capture_ordinal` and, if the clock was read, `observed_ns`. |

**Definitions.**

- *Observation sequence.* The host keeps one counter for each actor. Each
  activation of that actor, its reap, and each gate that waits for it takes
  the next value. Two ordinals are comparable only within one actor's
  sequence. The activation of `p` is in the sequence of the actor that runs
  `p`, not in `s`'s.
- *Natural termination.* The source exited without the host having asked
  it to.

**Rules.**

**`gate.wait` — the host waits for the source.** *acts*
The runner host, during execution, when the schedule reaches a phase that
declares a dependency. It waits for the source to terminate, for no longer
than the termination allowance or the time the run has left, whichever is
less. It never asks the source to exit.

**`gate.outcome` — the host reports what the wait found.** *reports*
The runner host, when the wait ends. `outcome` is one of eight values.

- **Decides:** `report.phases[p].termination_gate.outcome`
- `outcome = satisfied` **requires**

  | | Condition |
  | --- | --- |
  | S1 | `report.phases[f].activation_observation` `present` |
  | S2 | `report.actors[s].owned_reap` `present`, with `ownership_unbroken = true` |
  | S3 | `report.actors[s].owned_reap.departure_requested = false` |
  | S4 | `observed_ns` `present` on both the final activation and the reap |
  | S5 | final activation `capture_ordinal < ` reap `capture_ordinal`, and final activation `observed_ns ≤` reap `observed_ns` |
  | S6 | the wait's clock was usable throughout, and its elapsed time `≤` its budget |

- **otherwise** the host reports one of these. Each value has one meaning;
  the last column lists what gives rise to it, where that helps a reader
  find the supporting record.

  | `outcome` | Meaning | Arises when |
  | --- | --- | --- |
  | `source_unavailable` | The required order, the source's final activation and then its termination, was not established. | S1 fails: no final activation was recorded for the source. Or S5 fails: the reap does not follow the final activation in the source's sequence or in time. |
  | `execution_allowance_exhausted` | The run had no time left when the gate was reached, so the host did not wait. | |
  | `clock_unavailable` | The timing evidence needed to establish the gate was unavailable or unusable. | A clock reading failed or went backwards during the wait; S4 fails; or the wait's elapsed time could not be measured. `wait.clock_fault` and the presence of each `observed_ns` show which. |
  | `timed_out` | The source's termination was not observed within the allowance. | No reap before the budget ran out; or a reap was observed and the wait had by then run past its budget. In the second case `observation` is present. |
  | `ownership_lost` | The host could no longer treat the source's termination as its own observation. | Its ownership of the source process was broken, or its wait for the source failed (S2). |
  | `source_departure_requested` | The host had asked the source to exit, so its termination would not be natural. | S3 fails. |
  | `not_reached` | The gate was not evaluated and no wait took place. | The schedule was cancelled earlier, or the actor that runs `p` could not run. *Open: that this is the value the host writes was taken from what the controller accepts, not read in the host.* |

- The gate's own `capture_ordinal` is the next value in `s`'s sequence,
  taken when the wait ends. `observation.capture_ordinal` is the reap's.

**`gate.activation` — the host activates the phase only through a
satisfied gate.** *acts*
The runner host, during execution, immediately after `gate.outcome`.

- `activate(p)` **requires** `report.phases[p].termination_gate.outcome = satisfied`
- **Decides:** `report.phases[p].termination_gate.activation_eligible`
- **otherwise:** the host `does not` activate `p`, and `cancels` every
  phase after `p` in the schedule, whichever actor it belongs to.
- **Prevents:** for `p`, activation, query collection and release of
  attempts. For every later phase, activation.
- **Leaves:** every record reported before the gate. `owned_reap` if the
  source is reaped later, during cleanup: it is reported, and it does not
  reopen the gate.
- *Open:* how each later, cancelled phase shows in the report that it was
  cancelled and why.

**`gate.check` — the controller checks a gate it is given.** *checks*
The controller, after admitting a report. Applies when
`report.phases[p].termination_gate` is `present` and the report is not a
reporting failure. On a reporting-failure report the controller makes none
of these checks; whether that is intended is part of register row `R-36`.

- **Reads:** the gate, `report.actors[s].owned_reap`,
  `report.phases[f].activation_observation`, and phase `p`'s own records.
- Conditions:

  | | Condition |
  | --- | --- |
  | C1 | `outcome` `in` the eight values above |
  | C2 | `s` is an actor of the report, is not the actor that runs `p`, and `f` is `s`'s last phase and comes before `p` |
  | C3 | if `outcome = not_reached`: `observation`, `capture_ordinal` and `wait` `absent` |
  | C4 | if `outcome ≠ not_reached`: `wait` `present`, its stop reason `=` `outcome`, its budget within the allowance |
  | C5 | if `observation` `present`: `observation.capture_ordinal =` reap `capture_ordinal`, and reap `capture_ordinal <` gate `capture_ordinal` |
  | C6 | if `outcome = satisfied`: S2, S3, S4, S5 hold as reported, the reap's `stage` is `schedule` or `termination_gate`, and the wait had no clock fault, no native error and elapsed `≤` budget |
  | C7 | if `outcome ≠ satisfied`: `activation_eligible = false`, and phase `p` has no activation, no proceed flag and was not collected |
  | C8 | if `activation_eligible = true`: `outcome = satisfied`, and the actor that runs `p` was set up and its equipment is eligible |
  | C9 | if `outcome = satisfied` and `p` was activated with a timestamp: reap `observed_ns ≤` that timestamp |
  | C10 | each `owned_reap` agrees with its actor's process identifier and wait status; each activation `capture_ordinal` is positive |

- **otherwise:** the controller `flags` the report: one issue of kind
  `actor_evidence` for each failing condition, carrying a sentence of
  detail.
- **Decides:** `envelope.data.runner_sandbox_diagnostics.disposition_integrity = invalid`
- **Withholds:** the controller's top-level `process_disposition`, which
  becomes `withheld`.
- **Leaves:** the whole report as the host sent it, including
  `outcome: satisfied` and `activation_eligible: true` on a gate that failed
  C6; each actor's own disposition under the diagnostics; the result and
  the exit status.

**Known gaps.**

- A finding does not say which gate it concerns. An issue carries a kind
  and a sentence, and no reference to a phase or an actor. A reader of the
  envelope cannot tell from the finding which `termination_gate` not to
  rely on.
- Nothing the controller finds about a gate changes the result or the exit
  status (see "Findings about the host's report").
- The host checks its own report before sending it, with rules that are
  not the same as the controller's (register row `R-36`). A gate the host
  considers sound can be one the controller flags.

**Example.** *Open.* The inventory's rows for these lines name default
checks for a satisfied gate, an abnormal exit and a timed-out gate. Which
single case best stands for the section, and exactly what its check
asserts, has not been settled.

---

## What the gate example shows

- **All three kinds of rule are needed, and they fit.** Two rules are
  actions with an ordering, one produces a value, one checks. The second
  version's template could have expressed only the last.
- **The reach of a consequence can be stated exactly, and here it is wider
  than the present contract says.** C:234-236 says a failed gate withholds
  activation, collection and release. The host also cancels every later
  phase of every actor. Writing "prevents" as its own statement is what
  surfaced that.
- **"Leaves" does real work.** The controller's rule leaves `outcome:
  satisfied` in the report after finding the gate unsound. Stating that
  beside the rule is the precise form of the problem behind `R-20` and
  `R-34`, and it makes the first Known gap concrete: the finding has no
  object.
- **The dependency is shared, not repeated.** S2 to S5 are written once,
  under the rule that produces the value, and the controller's C6 refers to
  them. That is the kind of reuse the growth concern asks for. It also
  shows where the two implementations must agree, which is the subject of
  `R-36`.
- **The defined expressions carried most of the content.** Objects,
  conditions, one dependency and three effects cover every rule here. What
  stayed in plain sentences is the description of the wait and the meaning
  of each outcome.
- **An outcome value gets one meaning, stated from the branches that
  produce it.** Several causes arriving at one value is not a strain when
  the value's meaning covers them, as "the timing evidence needed to
  establish the gate was unavailable or unusable" covers
  `clock_unavailable`. In this section no grouping hides a distinction a
  reader needs: where the causes differ, another reported field shows
  which. A grouping that did hide one would go to the maintainer as a
  concrete distinction, with why it matters and what commitment would
  change.

## The receipt, restated in this model

The second version's worked section is in this file's history at commit
`024ae402`. It stands as written there, with these changes.

| Second version | Now |
| --- | --- |
| A "Production" part before the rules | A rule of kind **reports**: `profile.host`, whose nine conditions are the dependency of `status = captured`. |
| "Bears on: the receipt only" | **Reads:** the receipt's `status`, `producer`, `capture_stage`. **Decides:** whether the report is admitted. **Prevents:** every reading of the report by the controller, and its diagnostics. **Leaves:** the decoded report in the envelope. |
| A field table with a "what it supports" column | A field's row says what it is. What `request_nonce` and `bytecode_sha256` rest on is said once, as conditions 6 and 8 of `profile.host`. |
| A closing passage on what the rules do not establish | Kept, as the one place that states the limit: no rule of kind **checks** reads the nonce, the process identifier, the byte count or the digest. |

The receipt's controller rule is the case the second review pointed at: it
reads three fields of one receipt and decides the admission of the whole
report.

## What goes to the maintainer, and what does not

Following the maintainer's direction of 2026-11-10. The three kinds of rule
are a working model, adjusted as the material gives reason; writing
preservation as an action is an authoring choice. The meaning of an
existing outcome is established from source and stated. Neither waits for a
decision. The surfaces and the placement of the internal identity are
likewise carried as working choices; the surface names get a last look
before the stage one release makes them permanent.

Two findings from the gate reading are behavioral commitments and are in
the register for the maintainer:

- **`R-37`, the reach of a failed gate.** The host cancels every later
  phase of every actor, not only the dependent phase.
- **`R-38`, findings without a subject.** A controller finding names no
  phase, actor or record, so a reader cannot tell which of the host's
  assertions it concerns.
