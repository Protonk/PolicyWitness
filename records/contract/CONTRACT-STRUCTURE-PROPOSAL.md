# Proposed structure for the restructured CONTRACT.md

Second version, revised on the maintainer's review of 2026-11-10 (kept in
`records/contract/CONTRACT-MAINTAINER-NOTES.md`). It gives the table of
contents, what each section establishes, how the surfaces fit, the form a
rule takes, and one worked section. The choice of machinery is still
deferred; the document's shape is made to allow it. Sibling artifacts are
named by path without links, under the records link rule.

## What changed from the first version

| Review point | Change |
| --- | --- |
| Let definitions do the orienting | "How to read this contract" is gone. Components, boundaries, artifacts and kinds of report are definitions. Nothing describes the writer's method. |
| Keep the direction of obligation clear | Every rule's subject is a PolicyWitness component. Accepted input is stated as what PolicyWitness accepts and what it refuses, with the refusal as its commitment. Limits on what an output establishes are stated as limits on PolicyWitness's commitment, not as duties of a consumer. |
| Preserve the trio | Kept as the spine of each operation, with a required cross-reference: the controller's findings name the host assertions they bear on. |
| Runners are not an exceptional last subject | The body is organized by public operation. Runner selection is accepted input, reservation and submission are delivery, and runner management is an operation with the same three-part structure as a run. |
| Keep maintenance out | No appendix. Maintenance moves to a `docs/contract/` directory with its own README and working rules. |
| Make the structure reach inside the rules | A rule's conditions are separate items, each with its own identifier and its own consequence. Shown in the worked section. |
| Distinguish production from interpretation | Applicability is two separate statements: where PolicyWitness produces a record, and what it checks whenever the record is present. |
| A firmer boundary with the guide | Each field's meaning, the significance of its absence and what its values support are in the contract. The guide explains use. |

## Table of contents

```
PolicyWitness public contract

1  The contract identity                               [identity]
   1.1  The identity and its forms
   1.2  Where it is reported
   1.3  What PolicyWitness compares at each admission
   1.4  What a match establishes
   1.5  Changing the contract a specimen asserts

2  Definitions
   2.1  Components
   2.2  Boundaries
   2.3  Artifacts
   2.4  Kinds of report
   2.5  Surfaces                                       (generated)

3  Running a specimen
   3.1  Accepted input
        The request, including runner selection        [request]
        Policy                                         [policy]
        Probe steps                                    [probes]
        Actors and phases                              [actors]
        Sandbox extensions                             [extensions]
        Refusals                                       [refusals]
   3.2  Delivery to the host
        Reservation, submission and capture            [transport]
        The binary frame                               [wire]
   3.3  The host's report
        The report and its outcome                     [reply]
        Steps: query, attempt, comparison              [steps]
        Worker lifecycle                               [lifecycle]
        Actor records                                  [actor_evidence]
        Equipment                                      [equipment]
        Compiled-profile receipt                       [profile]
   3.4  The controller's assessment and output
        The envelope, the result and the exit status   [envelope]
        Findings about the host's report               [diagnostics]
        The specimen dossier                           [dossier]

4  Managing runners                                    [installation]
   4.1  Accepted input
   4.2  What is observed and recorded
   4.3  The controller's output

5  Reporting the version                               [identity]
```

Every public operation has a place: `run` is section 3, the `runner`
commands are section 4, and `--version` is section 5. The helper programs a
run starts, such as the fallback compiler, are components defined in 2.1;
their output is covered where the controller reads it.

## What each section establishes

| Section | What PolicyWitness commits to, or what is defined |
| --- | --- |
| 1.1 | The identity is a string in one of three forms. What each form states about the build that carries it. |
| 1.2 | Where each public artifact and command reports it. A person holding an application can read the governing contract off it before meeting any derivation detail. |
| 1.3 | The two values compared at each admission, and what PolicyWitness does on a mismatch. A specimen names the contract it requests; a received artifact reports the contract of the build that produced it. |
| 1.4 | What equal identities establish and what they do not. |
| 1.5 | What the surface table records and what it does not; that changing a specimen's assertion supplies the admission condition and nothing more. |
| 2.1 | Each component that acts: controller, client, runner host, worker, validator, helpers. Every rule names one of these as its subject. |
| 2.2 | Each boundary a run crosses, in order: the contract gate, runner selection, reservation, submission, execution, the host's encoding of its report, capture, reply admission, publication. Every rule names one of these as its place. |
| 2.3 | Each artifact: specimen, request, report, capture, envelope, receipt, registry record. |
| 2.4 | The kinds of report and what each means: ordinary, preparation failure, reporting failure; and the cases in which no report is admitted. |
| 2.5 | For each surface: what it contains, its section, when it last changed. |
| 3.1 | For each part of a specimen: what PolicyWitness accepts, what it means, and what it refuses, with which code, at which boundary. |
| 3.2 | What the client and the host exchange, the conditions under which a specimen is submitted, and the layout of a frame with what a reader rejects. |
| 3.3 | For each record the host reports: each field's meaning, what the host checked before reporting it, and what the record does and does not establish. |
| 3.4 | What the controller checks in a report, which host assertions each finding bears on, what the result and exit status mean, and what the dossier records. |
| 4 | The same three parts for runner management: what each command accepts and refuses, what is observed and recorded, and what the controller reports. |
| 5 | What the version report contains. |

## The form of a surface section

Each surface section has these parts in this order. A part with nothing to
say is omitted.

1. **Covers.** Which records or inputs, in one or two sentences.
2. **Records and fields.** For each field: its type; when it is present;
   what it means; what its absence means; and what its values support. This
   is where a field's meaning lives. It is not left to the guide.
3. **Definitions.** Terms specific to this surface. Terms shared across
   surfaces are in section 2.
4. **Production.** In which kinds of report, and under which conditions,
   PolicyWitness produces the record.
5. **Rules.** In the form below.
6. **Known gaps.**
7. **Example.** One concrete case, with the check behind it and what that
   check asserts.

## The form of a rule

A rule has a fixed set of parts, each separately identifiable, so that the
same content can later be held as data without being rewritten.

| Part | Content |
| --- | --- |
| Identifier and name | Stable, of the form `surface.rule`. |
| Who | One component from 2.1. |
| Where | One boundary from 2.2. |
| Applies when | The condition under which the rule is evaluated, stated in terms of the record being present or a request field being set, never in terms of what the producer usually emits. |
| Conditions | A list. Each item is one comparison: two named things and the relation required between them. Each has an identifier of the form `surface.rule.n`. |
| Consequence | What the component does when a condition fails, and what appears in the output. Given per condition where conditions differ. |
| Bears on | For a rule of the controller's: the host assertions it concerns. |

In stage one each part is written in sentences. The parts are fixed now so
that a rule cannot be written as one paragraph that runs its conditions
together.

## Applicability: two statements, kept apart

- **Production** says where PolicyWitness produces a record: in which kinds
  of report and under which conditions. It is a commitment about the
  producer.
- **Interpretation** says what a component checks when a record is present,
  and what the record then supports. It is a commitment about the reader
  and holds wherever the record appears, whether or not the current
  producer would put it there.

A rule's "applies when" is always an interpretation statement. A surface's
"Production" part carries the other. Where the present implementation
checks a record only on some paths, that is stated, and where that is not
intended it is a Known gap.

## How the surfaces fit

Nineteen surfaces, as in the first version: the thirteen present names are
kept and six are new (`identity`, `extensions`, `reply`, `actor_evidence`,
`diagnostics`, `wire`). What changed is where they sit.

| Surface | Section | Note |
| --- | --- | --- |
| `identity` | 1 and 5 | The identity rules and the version report. |
| `request` | 3.1 | Now includes runner selection, which is accepted input. |
| `policy`, `probes`, `actors`, `extensions`, `refusals` | 3.1 | `refusals` is request refusals. |
| `transport`, `wire` | 3.2 | Reservation and submission are rules at their boundaries. |
| `reply`, `steps`, `lifecycle`, `actor_evidence`, `equipment`, `profile` | 3.3 | The host's account. |
| `envelope`, `diagnostics`, `dossier` | 3.4 | The controller's assessment. `diagnostics` carries the "bears on" links to 3.3. |
| `installation` | 4 | Install, inspect and remove, each with accepted input, what is observed and what is reported. |

**What leaves the document.**

- Maintenance procedure, to `docs/contract/`.
- The internal host and worker identity, to the worker reference, leaving
  the meaning of its one public field in `lifecycle` and `actor_evidence`.
  Still a judgment call for review.
- Sentences that deny or recall a former mechanism.

## Consequence for length

With each field's meaning in the contract, the document absorbs most of
what the guide's hashed regions now hold. It will be several times its
present length. The worked section below is the measure available: one
small record with fourteen fields and two rules takes about a page.

## A worked section

The compiled-profile receipt again, in the revised form. The rule content
was read in source by the coordinator for register rows `R-01` to `R-06`.
Three things in it are not established and are marked *open*. The field
table was typed for this proposal; in the finished document it would be
rendered.

---

### Compiled-profile receipt

*Surface `profile`. Section 3.3.*

**Covers.** The `compiled_profile` record in the host's report, and in each
actor record in the actor form: the host's receipt for the compiled policy
a worker was about to apply.

**Records and fields.**

| Field | Type | Present | Meaning | What it supports |
| --- | --- | --- | --- | --- |
| `status` | string | always | `captured`: the host accepted the worker's capture. `unavailable`: it did not, or there was none to accept. | Which of the two the host reports. |
| `reason` | string | when `unavailable` | Which of the host's conditions failed (rule `profile.host` below). | The first failing condition only. |
| `worker_pid` | integer | always | The process identifier of the worker the host collected from. | The host's own observation of that worker. |
| `producer` | string | when `captured` | The string `worker`: the worker made the capture. | Nothing about the build. The report's own `producer` identifies the build. |
| `capture_stage` | string | when `captured` | The string `before_apply`: the bytes were taken before the policy was applied. | That the receipt is of what was about to be applied, not of the kernel's state afterward. |
| `request_nonce` | string | when `captured` | The request's `capture_nonce`. | That the host found the worker's recorded nonce equal to it. |
| `profile_type` | integer | when `captured` | *open: the host requires one value; what the value denotes was not read.* | |
| `bytecode_length`, `bytecode_b64` | integer, string | when `captured` | The compiled policy's length and bytes. | The bytes the host read from the worker's capture. |
| `bytecode_sha256` | string | when `captured` | The host's digest of those bytes. | That the host found it equal to the digest the worker recorded. |
| `source_length`, `source_sha256` | integer, string | when `captured` | The length and digest of the policy source. | That the worker's recorded values equal the host's for the source it supplied. |
| `parameter_count`, `params_sha256` | integer, string | when `captured` | The count and digest of the policy parameters. | The same, for the parameters. |

The record is absent when the request did not ask for a capture. The guide
says it is also absent when no worker result was obtained. *Open: that
second case has not been traced.*

**Definitions.**

- A receipt carries no contract or version. It is read under the contract
  of the report that carries it. Outside its report it does not identify a
  build.

**Production.** The host produces one receipt for each worker whose policy
set `capture_compiled_profile`. *Open: whether the host produces a receipt
in a preparation-failure report, where no worker was launched.*

**Rules.**

**`profile.host` — The host decides the receipt.**
*Who:* the runner host. *Where:* collection of the worker's results, before
the host encodes its report. *Applies when:* the request set
`capture_compiled_profile`.

The host reports `captured` when every condition holds. It evaluates them
in this order and stops at the first that fails.

| Condition | Required | `reason` when it fails |
| --- | --- | --- |
| `profile.host.1` | The policy was applied successfully. | `successful_application_unconfirmed` |
| `profile.host.2` | The worker exited with status 0 and no signal. | `worker_not_complete` |
| `profile.host.3` | The worker marked its capture complete. | `capture_not_complete` |
| `profile.host.4` | The worker recorded that it accepted the capture. | `worker_capture_refused` |
| `profile.host.5` | The recorded process identifier equals that of the worker being collected. | `capture_worker_mismatch` |
| `profile.host.6` | The recorded nonce equals the request's `capture_nonce`. | `capture_nonce_mismatch` |
| `profile.host.7` | The profile type is the expected one, and the byte count is positive and within capacity. | `capture_extent_or_type_invalid` |
| `profile.host.8` | The digest of the bytes read equals the recorded digest. | `capture_bytecode_digest_mismatch` |
| `profile.host.9` | The recorded source length and digest, and parameter count and digest, equal the host's. | `capture_consumed_input_mismatch` |

*Consequence.* On a failure the host reports `status: "unavailable"` with
that `reason` and `worker_pid`, and no other field. The capture data is not
reported. The report's outcome is unaffected.

**`profile.controller` — The controller checks a receipt's labels.**
*Who:* the controller. *Where:* reply admission. *Applies when:* an
admitted-contract report carries a receipt, in any kind of report.

| Condition | Required |
| --- | --- |
| `profile.controller.1` | `status` is `captured` or `unavailable`. |
| `profile.controller.2` | A captured receipt has `producer: "worker"` and `capture_stage: "before_apply"`. |
| `profile.controller.3` | An unavailable receipt has neither. |

*Consequence.* On any failure the controller does not admit the report. The
result is `malformed_runner_response` and the exit status is 1. The decoded
report remains in the envelope.

*Bears on.* The receipt only. It concerns no other assertion in the host's
report.

**What these rules do not establish.** The controller compares no receipt
field with the request or with the bytes: it does not check
`request_nonce`, `worker_pid`, `bytecode_length` or `bytecode_sha256`. An
admitted `captured` receipt therefore establishes that the host reported it
and that its labels are well formed. That the nonce, extent and digest were
compared rests on the host (rule `profile.host`) and is not re-examined
after the report is encoded.

**Example.** A report from the current build carries a `captured` receipt
whose `producer` is not `worker`. The controller does not admit it; the
result is `malformed_runner_response`.
*Checked by* the controller unit test
`compiled_profile_context_is_gated_after_the_response_version`, over the
fixture case `producer_future`. It asserts that the report is not admitted.
It does not assert the outcome string.

---

## What the worked section shows

- **Each condition can be pointed at.** `profile.host.6` is the nonce
  comparison and has its own reason. The first version ran nine conditions
  into one sentence.
- **Consequences are per rule and, where they differ, per condition.**
- **Production and interpretation are apart.** "Applies when" for the
  controller's rule is "a report carries a receipt", so the open question
  about preparation-failure reports sits under Production and no longer
  makes the rule's reach uncertain.
- **The direction of obligation.** The passage on what the rules do not
  establish states the limit of PolicyWitness's commitment. The first
  version said what a consumer could do about it.
- **Fields carry their meaning.** The table is no longer keys and types.
  It also shows the cost: one field's meaning could not be given from what
  has been read.
- **It is longer.** About a page for one small record. The rules are
  shorter to scan and longer to print.
- **Three open items**, each a reading task for stage one: the meaning of
  `profile_type`, absence when a capture was requested, and production in a
  preparation-failure report.

## Still for review

1. Whether organizing by operation, with the trio inside each, is the
   broadening intended for runner management.
2. Whether the internal host and worker identity leaves the contract.
3. Whether nineteen surfaces stand, or `extensions` and `diagnostics` fold
   into their neighbors.
4. Whether the rule form above is the right set of parts to fix now, given
   that it is what a later machine-readable form would hold.
