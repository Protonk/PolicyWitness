# Proposed structure for the restructured CONTRACT.md

This proposal gives the table of contents, the working rule model and two
worked sections: a termination gate and a compiled-profile receipt. Both
sections are included here; reading an earlier revision is unnecessary.
Sibling artifacts are named by path without links, under the records link
rule.

**Status.** The maintainer accepted the direction on 2026-11-10. How the
document is authored and generated, as a tree of nodes with structured
facts beside prose, is set out in `docs/CONTRACT-STAGING-PLAN.md`, which
governs. This file remains the source for the table of contents, the
surfaces, the model of a rule and the two worked sections.

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
`docs/contract/`. Definitions establish the components, boundaries and
artifacts. Each operation then states accepted input, what PolicyWitness
does and reports, and what its assessments establish. Surface names and
the placement of the internal identity remain working choices.
The staging plan's entry-path inventory must account for direct XPC callers,
shipped helpers such as `sbpl-check --request`, and instrumented requests
before this outline is treated as complete.

## What changed from the second version

| Review point | Change |
| --- | --- |
| The form must hold commitments beyond validation | The working kinds are **acts**, **reports** and **checks**. Actions and reports can also depend on conditions. Production carries obligations of its own. |
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

Every rule also has an identifier, a responsible component (section 2.1),
the records or actions it governs, and its boundary (section 2.2). The
categories are authoring tools, not an assertion that all commitments fit
three disjoint classes.

Applicability identifies the entry path and recipient as well as the
operation or run state, admission state, report kind and record presence.
A direct host caller receives no controller assessment. A check may require
a record that is missing, or apply only on specified paths; presence alone is not its
universal trigger. A producer's ability to emit a record does not determine
a reader's obligation when it receives that record. Each rule states its
own conditions, including any degraded-report exception.

Definitions state what a value establishes and the limits of that meaning,
including when the value succeeds. These limits belong beside the value;
they need not be an action or a failure effect. For example, matching public
contract identities establish the reported identity match used for admission,
not identical builds or authenticated origin. Moving implementation detail
to a reference must preserve the limits needed to interpret a public field.

### The reach of a consequence

Four statements, each made separately wherever it is not empty.

| Statement | Answers |
| --- | --- |
| **Reads** | Which records and fields the rule looks at. |
| **Decides** | Which objects' states the rule sets: fields, actions, or admission. Multiple effects are named separately. |
| **Prevents** or **withholds** | Which later actions do not happen, or which conclusions the component declines to state. |
| **Leaves** | Which records remain published, and separately which assessments remain supported. Retention alone does not certify a retained assertion. |

This is what "dependent claims" needs in order to mean something: for each
finding, the object decided, the conclusions withheld, and what still
stands.

### Four relationships with a defined expression

These are working forms of statement. The stage one spike tests their
representation and revises them where necessary. Explicitly identified
free text remains free text until its relationships can be expressed.

1. **Object.** A path into a defined artifact, or a reference to a defined
   action or event. Index variables name their domain and binding, including
   joins by actor or phase identity. Example: `report.phases[p].termination_gate`.
2. **Condition.** Comparisons name their operands; presence tests name one
   object. The initial relations are `=`, `≠`, `<`, `≤`, `present`,
   `absent`, `in`. Conjunctions and conditional requirements also need an
   explicit representation, as the gate's S and C conditions demonstrate.
   Value sets say whether admitted values are closed or open; displayed
   lists separately say whether they are exhaustive or illustrative.
3. **Dependency.** `X requires C1, C2, …`: an assertion or an action, and
   the conditions it rests on. Check order and refusal precedence also need
   explicit relations between named actions, including across surfaces;
   prerequisite lists and tree nesting do not specify that order.
4. **Effect.** An action or result with named affected objects. Initial
   verbs include `refuses`, `does not`, `cancels`, `reports`, `flags` and
   `withholds`. Successful and failure effects both have a place; an effect
   need not be an `otherwise` clause. Its **prevents** and **leaves** lists
   distinguish stopped actions, withheld conclusions and retained evidence.

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

Evidence grade: source and test read; no gate test was executed for this
proposal. The account follows `ActorScheduler.walkSchedule` and
`observeTermination`, `ActorTerminationGateRecord` in
`runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift`, assembly in
`runner/Sources/PWRunnerCore/ActorOrchestration.swift`, and the controller's
`gates` and `execution_diagnostics` functions. The example below states the
assertions and limits of its named test.

---

### Termination dependencies

*Surface `actor_evidence`. Section 3.3. The request side, how a phase
declares a dependency and when the declaration is refused, is in "Actors
and phases", section 3.1.*

**Covers.** A phase may run only after another actor has terminated. The
host decides this at a *termination gate* when the schedule reaches the
phase, and reports the gate on that phase.

In this section `p` indexes the dependent phase in `report.phases`, `s`
indexes the actor whose `actor_id` matches the gate's `source_actor_id`,
and `f` indexes that source's final phase. References to `s` and `f` in
conditions are conditional on those lookups succeeding; failed lookups are
themselves findings under C2.

**Records.**

| Object | What it is |
| --- | --- |
| `report.phases[p].termination_gate` | The gate: `condition`, `source_actor_id`, `source_final_phase_id`, `outcome`, `activation_eligible`, `observation.capture_ordinal`, `capture_ordinal`, `wait`. |
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
The runner host, during execution, evaluates a declared dependency after
the schedule and dependent actor pass their availability checks. The wait
budget is the lesser of the termination allowance and the remaining
execution allowance, expressed in whole milliseconds. Deadline and final
elapsed-time checks govern satisfaction; they do not promise that the host
returns within a strict wall-clock bound. The gate wait requests no source
departure. Subsequent cleanup can request departure independently.

**`gate.outcome` — the host reports what the wait found.** *reports*
The host initializes a declared gate as `not_reached` when it creates the
phase's visit record. If evaluation occurs, it replaces that value with
the outcome of the wait. `outcome` is one of eight values.

- **Decides:** `report.phases[p].termination_gate.outcome`
- `outcome = satisfied` **requires**

  | | Condition |
  | --- | --- |
  | S1 | `report.phases[f].activation_observation` `present` |
  | S2 | `report.actors[s].owned_reap` `present`, with `ownership_unbroken = true` |
  | S3 | `report.actors[s].owned_reap.departure_requested = false` |
  | S4 | `observed_ns` `present` on both the final activation and the reap |
  | S5 | final activation `capture_ordinal` < reap `capture_ordinal`, and final activation `observed_ns` ≤ reap `observed_ns` |
  | S6 | the budget is positive, deadline samples permit the reap, and final wait accounting has no clock fault and has elapsed time ≤ budget |

- **otherwise** the host reports one of these. Each value has one meaning;
  the last column lists what gives rise to it, where that helps a reader
  find the supporting record.

  | `outcome` | Meaning | Arises when |
  | --- | --- | --- |
  | `source_unavailable` | The source session or the required order of final activation and termination was not established. | The source session or final activation is missing, or S5 fails. |
  | `execution_allowance_exhausted` | No positive whole-millisecond gate budget remained when evaluation began. | If the schedule's earlier allowance check stops the phase before evaluation, its gate instead stays `not_reached`. |
  | `clock_unavailable` | The timing evidence needed to establish the gate was unavailable or unusable. | A deadline sample failed or went backwards; S4 fails; or final wait accounting cannot establish elapsed time without a clock fault. The retained timing fields provide context but do not necessarily identify one unique branch. |
  | `timed_out` | Gate evaluation did not establish timely satisfaction within its allowance. | The deadline or wait expires, including after a reap; or final elapsed time exceeds the budget. A retained `observation` does not establish timely satisfaction. |
  | `ownership_lost` | The host could no longer treat the source's termination as its own observation. | Its ownership of the source process was broken, or its wait for the source failed (S2). |
  | `source_departure_requested` | The host had asked the source to exit, so its termination would not be natural. | S3 fails. |
  | `not_reached` | The gate was not evaluated and no gate wait took place. | Cancellation, the schedule's allowance check, or an unavailable dependent actor or visit prevents evaluation. The initialized record keeps `activation_eligible: false`, without a wait, observation reference or gate capture ordinal. |

- An evaluated gate takes the next ordinal in its source process's
  observation sequence when it closes, if that session exists. An
  observation reference, when present, names the owned reap retained during
  evaluation. A skipped gate captures neither. The table describes the
  outcomes, not an exhaustive ordering of every failing branch.

**`gate.activation` — the host activates the phase only through a
satisfied gate.** *acts*
The runner host, during execution, after evaluating a reached gate.

- `activate(p)` **requires** `report.phases[p].termination_gate.outcome = satisfied`
- **Decides:** `report.phases[p].termination_gate.activation_eligible`
- **otherwise:** the host `does not` activate `p`, and `cancels` every
  phase after `p` in the schedule, whichever actor it belongs to.
- **Prevents:** for `p`, activation, query collection and release of
  attempts. For every later phase, activation.
- **Leaves:** observations already collected. Final report assembly also
  retains a later cleanup `owned_reap`; it does not reopen the gate or add
  that reap to the failed gate's observation reference.
- Later phases remain in `phases[]`, with no activation observation or
  visit timing, false arrival/completion flags and `collection_status:
  "not_reached"`. Their declared gates, if any, stay `not_reached`.
  `schedule.cancelled` carries `termination_dependency:<outcome>`; the
  internal per-visit cancellation string is not a public phase field.
  Action records are still assembled for these phases. Final cleanup and
  evidence collection continue for launched actors.

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
  | C2 | `condition = terminated`; `s` is an actor of the report, is not the actor that runs `p`, and `f` is `s`'s last phase and comes before `p` |
  | C3 | if `outcome = not_reached`: `observation`, `capture_ordinal` and `wait` `absent` |
  | C4 | a present `wait` has budget within 0–5,000 ms and no excluded-time field; if `outcome ≠ not_reached`, it is present and its stop reason equals `outcome` |
  | C5 | if `observation` is present: its ordinal is positive, equals the source's valid owned reap ordinal, and precedes a present gate capture ordinal |
  | C6 | if `outcome = satisfied`: S2–S5 hold as reported; the gate refers to that valid reap and closes after it in the source sequence; the reap's `stage` is `schedule` or `termination_gate`; and the wait has positive budget, no clock fault, no native error and elapsed time ≤ budget |
  | C7 | if `activation_eligible = false`: phase `p` has no activation or visit timing, no arrival or proceed flags, and collection is `not_reached`; if `outcome ≠ satisfied`, eligibility is false |
  | C8 | if `activation_eligible = true`: `outcome = satisfied`, and the actor that runs `p` was set up and its equipment is eligible |
  | C9 | if `outcome = satisfied` and `p` was activated with a timestamp: reap `observed_ns ≤` that timestamp |

  Independently of gate presence, the controller checks every carried owned
  reap against the actor's process identifier and native wait status, and
  every activation observation for a positive ordinal. These requirements
  also apply to phases without a gate, on the same non-reporting-failure path.

- **otherwise:** the controller `flags` the report with `actor_evidence`
  issues carrying detail sentences. The grouped conditions above do not
  promise one issue each: checks may accumulate overlapping findings.
- **Decides:** `envelope.data.runner_sandbox_diagnostics.disposition_integrity = invalid`
  and top-level `termination_cause = unknown`.
- **Withholds:** the controller's top-level `process_disposition`, which
  becomes `withheld`.
- **Leaves:** the whole report as the host sent it, including
  `outcome: satisfied` and `activation_eligible: true` on a gate that failed
  C6; each actor's own disposition under the diagnostics; the result and
  the exit status.

**Known gaps.**

- A gate finding does not say which gate it concerns. The actor-evidence
  helper emits a kind and detail sentence without a structured phase or
  actor reference. Other lifecycle issues can carry rule, question, step
  index and observation fields; the limitation here is the gate finding's
  missing subject. The envelope gives no structured association from that
  finding to the particular `termination_gate`.
- Nothing the controller finds about a gate changes the result or the exit
  status (see "Findings about the host's report").
- The host also checks gate evidence before encoding. `R-36` establishes
  disagreements on actor/preparation and degraded-report cases, not a
  demonstrated gate-specific disagreement. The proposal does not treat it
  as evidence for a particular gate that passes the host and fails the
  controller.

**Example.** The source completes its final phase but remains alive when
the gate times out. The dependent phase is neither activated nor collected
nor released. Cleanup subsequently reaps the source, and the gate remains
`timed_out`.

*Check read:* `ActorSchedulerTests.swift`, test "termination gate timeout
cannot be repaired by final cleanup". It asserts those scheduler observations
with a real fixture child and a shortened execution allowance. It does not
check the public JSON, an additional later actor's phase, or the production
allowance. No execution of this test is claimed by this proposal.

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
  `clock_unavailable`. The reported fields need not identify the exact
  implementation branch. A distinction that changes a consumer's warranted
  conclusion would go to the maintainer with its observable consequence.

## Worked example: a compiled-profile receipt

Evidence grade: source and test read; no capture test was executed for this
proposal. Sources are `decodeProfileCapture` in
`runner/Sources/PWRunnerCore/CWorker.swift`, `ActorSession.collectOutput`,
the ordinary and actor reply assemblers, `actorPreparationRefusal`,
`runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift`,
`controller/tools/pw_probe_runner/pw_profile_capture.h`, and the controller's
`admission_problem` and `run_flow::admit_reply` paths.

---

### Compiled-profile receipt

*Surface `profile`. Section 3.3.*

**Covers.** The optional `compiled_profile` record in an ordinary host
report or in an actor's record. It accounts for the worker's capture of a
compiled policy before application.

**Records.** In the table, "captured" and "unavailable" describe the
host's production rule. They are not additional checks performed by the
controller's label validator.

| Field | Type and presence | Meaning |
| --- | --- | --- |
| `status` | string, always | `captured`: the host's capture checks passed; `unavailable`: the host could not accept a capture. |
| `reason` | string, unavailable | The first failing condition in `profile.host`. |
| `worker_pid` | integer, always | The PID of the worker whose output the host collected. |
| `producer` | string, captured | `worker`, identifying the component that made the capture. |
| `capture_stage` | string, captured | `before_apply`, the point at which the worker captured the bytes. |
| `request_nonce` | string, captured | Copied from the request's `capture_nonce` after the host's comparison with the worker's recorded bytes. The returned value alone is not an independent witness of that comparison. |
| `profile_type` | integer, captured | `0`, the single-profile compiler-result representation supported by the worker's capture layout. |
| `bytecode_length` | integer, captured | Number of captured bytes. |
| `bytecode_b64` | string, captured | Those bytes, presented as base64. |
| `bytecode_sha256` | string, captured | The host's SHA-256 of those bytes, presented as lowercase hexadecimal. |
| `source_length`, `source_sha256` | integer and string, captured | UTF-8 byte length and SHA-256 of the supplied policy source; the digest is lowercase hexadecimal. |
| `parameter_count`, `params_sha256` | integer and string, captured | Parameter count and the order-independent digest of the parameter names and values consumed by the worker. The digest is lowercase hexadecimal. |

The parameter digest is SHA-256 of the little-endian 32-bit count followed
by sorted pair digests. Each pair digest is SHA-256 of the little-endian
32-bit key length, key bytes, little-endian 32-bit value length and value
bytes. These are the UTF-8 strings supplied to the worker's parameter calls.

**Definitions.** A receipt is interpreted under its containing report's
producer contract. It has no independent build identity. The report's
`producer` identifies that build; the receipt's `producer` identifies the
worker component. The receipt's fields state the host's account of a capture;
the controller checks the subset specified below.

**Request association and available comparisons.** Equality between the
receipt's `request_nonce` and the nonce retained with a consumer's own request
associates the receipt with that request. This is separate from establishing
that the host compared the worker's recorded nonce. The controller does not
perform this association for the consumer.

| Available information | What a reader can compare |
| --- | --- |
| Receipt alone | Decode `bytecode_b64`, compare its byte count, and recompute its digest. Current readers do not perform these comparisons. |
| Receipt and the consumer's request | Compare `request_nonce` with the nonce sent. A mismatch exposes a wrong association or altered receipt; a match does not repeat the host's capture comparison. |
| Worker capture and the host's independent observations | The recorded PID and nonce, completion and capture status, and application and exit conditions require evidence unavailable to a receipt reader. |

Whether the consumer can reconstruct the exact source and parameter inputs
used by the host, including request preparation, remains an evidence question
for that comparison. It is not settled by the digest fields being present.

**`profile.presence` — the host reports collected capture results.** *reports*
The runner host, during result assembly. A collected worker output contains
a receipt when capture was requested, including an `unavailable` receipt
when collection cannot establish a valid capture. A request without capture,
or a failure that produces no worker output, has no receipt. In particular,
`actorPreparationRefusal` launches no workers and produces no receipts.
Absence therefore does not by itself establish that capture was unrequested.

**`profile.host` — the host decides the receipt.** *reports*
The runner host, while collecting a worker's output when capture was
requested. It reads the worker capture and the independent observations
listed below. It evaluates the conditions in order and stops at the first
failure.

| Condition | Required | `reason` on failure |
| --- | --- | --- |
| `profile.host.1` | Application was observed and its return code is zero. | `successful_application_unconfirmed` |
| `profile.host.2` | The worker published `done`, was reaped with exit code zero, and has no termination signal. | `worker_not_complete` |
| `profile.host.3` | The worker published capture completion. | `capture_not_complete` |
| `profile.host.4` | The worker's capture status is accepted. | `worker_capture_refused` |
| `profile.host.5` | The recorded PID equals the collected worker's PID. | `capture_worker_mismatch` |
| `profile.host.6` | The recorded nonce bytes equal the valid request nonce. | `capture_nonce_mismatch` |
| `profile.host.7` | The recorded profile type is zero and the byte count is positive and within capture capacity. | `capture_extent_or_type_invalid` |
| `profile.host.8` | SHA-256 of the captured bytes equals the worker's recorded digest. | `capture_bytecode_digest_mismatch` |
| `profile.host.9` | The recorded source length/digest and parameter count/digest equal the host's values for its supplied input. | `capture_consumed_input_mismatch` |

- **Decides:** the receipt's `status` and content. Passing every condition
  produces `captured` with the captured fields above. Failure produces only
  `status: unavailable`, the corresponding `reason` and `worker_pid`.
- **Withholds on failure:** capture bytes and the associated capture fields.
- **Leaves:** the report's independently classified outcome. A capture failure
  does not itself change it; a worker/application failure can independently
  affect both the outcome and the receipt.

**`profile.controller` — the controller checks receipt labels.** *checks*
The controller, at reply admission after structural decoding and exact
producer-contract admission. It examines each present receipt, including
those in reporting-failure and preparation-failure reports, regardless of
whether the host normally produces a receipt on that path.

- **Reads:** `status`, `producer`, `capture_stage`.
- **Requires:** `status` is `captured` or `unavailable`; a captured receipt
  has `producer: worker` and `capture_stage: before_apply`; an unavailable
  receipt has neither label.
- **Decides on failure:** admission of the whole containing host report.
  The controller classifies it as `malformed_runner_response`, with a failed
  result and exit status 1.
- **Prevents:** controller execution diagnostics derived from that report.
- **Leaves:** the decoded report retained in the envelope. Its retained
  assertions have not gained admission by being preserved.

These label checks do not compare the nonce with the request or validate
the PID, extent or digests against capture evidence. Those comparisons
belong to `profile.host`. Structural decoding and the label check establish
different properties from the host's capture checks.

The host's own reporting self-check also enforces these label relationships,
including on degraded reports. Its failure follows the host's reporting-
failure path, not the controller's `malformed_runner_response` path. A
malformed request nonce is refused during request admission before capture.

**Example.** A report from the current build contains a captured receipt
with a producer label other than `worker`. The controller refuses admission
of the report as `malformed_runner_response`.

*Check read:* `compiled_profile_context_is_gated_after_the_response_version`
in `controller/src/run_flow.rs`, fixture case `producer_future`. It asserts
that the reply version is not supported, and separately that a foreign
producer takes precedence. It does not assert the final outcome string;
that missing assertion remains `R-06`. No execution of the test is claimed
by this proposal.

---

## What goes to the maintainer, and what does not

Following the maintainer's direction of 2026-11-10. The three kinds of rule
are a working model, adjusted as the material gives reason; writing
preservation as an action is an authoring choice. The meaning of an
existing outcome is established from source and stated. Neither waits for a
decision. The surfaces and the placement of the internal identity are
likewise carried as working choices; the surface names get a last look
before the unpublished stage one release makes them permanent in release
history.

Two findings from the gate reading are behavioral commitments and are in
the register for the maintainer:

- **`R-37`, the reach of a failed gate.** The host cancels every later
  phase of every actor, not only the dependent phase.
- **`R-38`, gate findings without a subject.** Gate checks emit no
  structured phase or actor reference identifying the affected assertion.
