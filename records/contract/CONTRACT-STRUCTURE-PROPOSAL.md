# Proposed structure for the restructured CONTRACT.md

A proposal for review before stage one of `docs/CONTRACT-STAGING-PLAN.md` is
drafted. It gives the table of contents, what each section establishes for
the reader, how the surfaces fit, and one worked section. It says nothing
about the machinery behind the document; that discussion comes after this
one. Sibling artifacts are named by path without links, under the records
link rule.

## The organizing idea

The document follows the reader's route and then the order of a run.

1. A reader first needs to know **which contract applies** to what they
   hold. That comes first and is short.
2. They then need to know **how to read a rule**: who the components are,
   where the boundaries between them fall, and what kinds of reply exist.
   This is stated once, so that no later section has to re-explain who is
   speaking.
3. The body is the **surfaces**, in the order a run meets them: what goes
   in, what the host reports, what the controller adds, how it travels,
   and how a runner is installed.

Every surface section has the same internal order, so a reader who has
read one knows where to look in the next.

## Table of contents

```
PolicyWitness public contract

1  Which contract applies                          [identity]
   1.1  The identity and its three forms
   1.2  Where an application, an envelope and a reply report it
   1.3  What is compared at each admission
   1.4  What a match establishes, and what it does not
   1.5  Moving a specimen to another contract

2  How to read this contract
   2.1  A run, in order: components and boundaries
   2.2  How a rule is written
   2.3  Kinds of reply, and which rules apply to each
   2.4  The surfaces                               (generated table)

3  What you send
   3.1  The request                                [request]
   3.2  Policy                                     [policy]
   3.3  Probe steps                                [probes]
   3.4  Actors and phases                          [actors]
   3.5  Sandbox extensions                         [extensions]
   3.6  Refusals                                   [refusals]

4  What the host reports
   4.1  The report and its outcome                 [reply]
   4.2  Steps: query, attempt, comparison          [steps]
   4.3  Worker lifecycle                           [lifecycle]
   4.4  Actor records                              [actor_evidence]
   4.5  Equipment                                  [equipment]
   4.6  Compiled-profile receipt                   [profile]

5  What the controller adds
   5.1  The envelope, the result and the exit status   [envelope]
   5.2  The controller's findings                  [diagnostics]
   5.3  The specimen dossier                       [dossier]

6  How it travels
   6.1  Reservation, submission and capture        [transport]
   6.2  The binary frame                           [wire]

7  Runners
   7.1  Installation and the registry              [installation]

Appendix  Maintaining this document                (not a surface)
```

## What each section establishes

| Section | The reader leaves knowing |
| --- | --- |
| 1.1 | The identity is a string in one of three forms: release, development, unbound. What each form means about the build. |
| 1.2 | Where to read it off a thing they hold: `--version`, an envelope's `build.contract`, a reply's `producer.contract`, the bundle's `PWContract`. This answers "which contract governs this application" before any derivation detail. |
| 1.3 | At each admission, the two values compared and the consequence of a mismatch: a specimen names the contract it requests; a received artifact reports the contract of the build that produced it. |
| 1.4 | What equal strings do not establish: equal binaries, an authentic peer. The present contract says this only of the internal identity. |
| 1.5 | The review is a decision about whether the selected contract suits the specimen; changing the string only supplies the admission condition. What the surface table records and what it does not. What to do when the specimen asserts a development identity. |
| 2.1 | The cast (specimen author, controller, client, runner host, worker, validator, consumer) and the boundaries in the order a run crosses them: the contract gate, selection, reservation, submission, execution, the host's encoding of its report, capture, reply admission, publication. Every rule's "who" and "where" refers back to this. |
| 2.2 | That each rule states its four particulars, what a Known gap paragraph is, and that each example names the check behind it. |
| 2.3 | The kinds of reply (ordinary, preparation failure, reporting failure, and the cases with no admitted report), what each means, and one table of which families of rule apply to each. |
| 2.4 | What each surface contains and where its section is, with its last-changed stamp. Generated. |
| 3 | What a specimen may contain, what each part means, and what is refused, with what code, at which point. |
| 4 | What each record in the host's report means, what the host checked before reporting it, and what the report does not establish. |
| 5 | Which component supplies each part of the output; what success means; what the controller checks in a report and where its findings appear. |
| 6 | What is exchanged between client and host and when a specimen is submitted; how a frame is laid out and what a reader rejects. |
| 7 | What installing, executing and removing an external runner requires. |
| Appendix | How the document is generated and checked. For maintainers; nothing in it is a commitment to a specimen author or a consumer. |

## The template for a surface section

Each surface section has these parts, in this order. A part with nothing to
say is omitted.

1. **Covers.** One or two sentences: which records or inputs this surface
   is about, and who meets them.
2. **Fields.** The keys and types, rendered from the record definitions.
   Compact; no prose.
3. **Definitions.** What the records and their values mean. A term used in
   a rule is defined here or in section 2.
4. **Rules.** One short paragraph per rule, each under a bold name, each
   stating its particulars in sentences: who acts and where in the run,
   what is compared with what, and what happens when it does not hold.
5. **Applies to.** Only where the rules differ by kind of reply.
6. **Known gaps.** Behavior that is true now and expected to change.
7. **Example.** One concrete case, with the check that owns it.

## How the surfaces fit

Nineteen surfaces. All thirteen present names are kept, so the surface
table gains no removal row; six names are new.

| Surface | Status | Draws on (present lines) | Why |
| --- | --- | --- | --- |
| `identity` | new | C:1-20, C:100-106, C:436-441 | The identity rules are outside every surface today, so editing them moves no stamp. |
| `request` | kept, narrower | C:58-124 less the policy, probe and actor material | The root, the gate, closed objects, nulls, runner selection, plan forms. |
| `policy` | kept | C:126-130; request-side policy rules now in C:77-91 | |
| `probes` | kept | C:132-136; C:87-98 | The step vocabulary and what an attempt does. |
| `actors` | kept | C:138-142; actor and phase rules from C:65-98 and the dependency rule at C:281 | Request side: forms, phases, termination dependencies. |
| `extensions` | new | The one sentence at C:141; the guide's extension regions | Extension transfer and custody have one sentence in the contract and several hundred lines in the guide. |
| `refusals` | kept | C:252-291 | Request refusals only. Exit classification moves to `envelope`. |
| `reply` | new | C:156-160 in part; C:198-202; the guide's outcome catalog | The report as a whole: its outcome, the kinds of reply, the partition rule. The outcome catalog is in the guide's `refusals` region today. |
| `steps` | kept | C:156-160 | Query, attempt, comparison, `query_first`. |
| `lifecycle` | kept | C:162-166; guide text on the disposition record | The host's account of how a worker ended. |
| `actor_evidence` | new | C:173-181, C:204-236 | Launch, application, setup and termination gates. These sit in `equipment` today. |
| `equipment` | kept, narrower | C:168-171, C:183-196 | Inventory, bindings, entitlements. |
| `profile` | kept | C:240-244 | |
| `envelope` | kept, wider | C:144-148, C:256-264, C:436-441 | The parts of the output, the result, the exit status, what success means. |
| `diagnostics` | new | C:165 in part, C:351-355; guide text on the controller's projection | The controller's findings and what withholding covers. |
| `dossier` | kept | C:150-154 | |
| `transport` | kept, narrower | C:246-250 | Reservation, submission, capture, the replay rule. |
| `wire` | new | C:300-358 | The frame format. It is a region with no stamp row today. |
| `installation` | kept | C:293-298 | |

**What leaves the body.**

- *Maintenance procedure* (C:22-32 in part, C:52-56, C:360-377, C:428-434)
  goes to the appendix. What a reader needs from it, namely what the
  surface table records, moves to 1.5.
- *The internal host and worker identity* (C:379-425) is not something a
  specimen author or a consumer can observe, except through one field. The
  proposal is to move it to the worker reference and keep in the contract
  only the meaning of that field, in `lifecycle` and `actor_evidence`. Two
  other documents link to its present heading.
- *Sentences that deny or recall a former mechanism*, as already directed.

## Three judgment calls for review

1. **How much of the guide's substance the contract absorbs.** For the
   contract to be complete without the guide, it has to hold every rule and
   definition that is a commitment. The proposal is: rules and definitions
   in the contract; keys and types rendered compactly per surface; field by
   field explanation, tutorials and worked output stay in the guide as
   explanation. The document would then be considerably longer than its
   present 441 lines. The length has not been estimated with any care.
2. **Nineteen surfaces.** `extensions` could fold into `actors`, and
   `diagnostics` into `envelope`. They are separate here because each is a
   distinct thing a reader might need to re-review on its own, and because
   the names are final after stage one.
3. **Moving the internal identity out.** It makes the public contract
   shorter and more clearly public. It also moves text that other documents
   link to.

## A worked section

This is section 4.6 as it would read, written from what the coordinator
read in source for register rows `R-01` to `R-06`. The Fields block shows
the form a rendered block would take; its content was typed from the record
definition for this proposal.

One part is not established and is marked: whether a receipt can appear in
a preparation-failure reply.

---

### 4.6 Compiled-profile receipt

*Surface `profile`.*

**Covers.** The optional `compiled_profile` record in the host's report,
and in each actor record in the actor form. It is a receipt for the
compiled policy a worker was about to apply. It is present only when the
request set `capture_compiled_profile`.

**Fields.**

| Field | Type | Present |
| --- | --- | --- |
| `status` | string | always |
| `reason` | string | when `status` is `unavailable` |
| `worker_pid` | integer | always |
| `producer`, `capture_stage` | string | when `status` is `captured` |
| `request_nonce` | string | when `status` is `captured` |
| `profile_type`, `bytecode_length` | integer | when `status` is `captured` |
| `bytecode_sha256`, `bytecode_b64` | string | when `status` is `captured` |
| `source_sha256`, `source_length`, `params_sha256`, `parameter_count` | string, integer | when `status` is `captured` |

**Definitions.**

- A receipt is `captured` or `unavailable`. A captured receipt carries the
  compiled bytes and their digest. An unavailable receipt carries a
  `reason` and none of the capture data.
- A receipt has no contract or version of its own. It is read under the
  contract of the report that carries it (section 1.3). Taken out of its
  report, it does not identify the build that produced it.
- Two fields are named `producer`. The report's `producer` identifies the
  build that produced the report. The receipt's `producer` is the string
  `worker`, and says that the worker made the capture.

**Rules.**

**The host decides the receipt.** While the runner host collects a worker's
capture, after the worker has exited and before the host encodes its
report, it compares what the worker recorded with what the host knows. It
reports `captured` only if application succeeded and the worker exited with
status 0 and no signal; the worker marked the capture complete; the
recorded process identifier is that of the worker being collected; the
recorded nonce equals the request's `capture_nonce`; the profile type is
the expected one and the byte count is positive and within capacity; the
digest of the bytes read equals the recorded digest; and the recorded
source and parameter identities equal the ones the host supplied. If any of
these fails, the host withholds the capture data and reports `unavailable`
with the `reason`. The report itself is unaffected: its outcome does not
change on this account.

**The controller checks the labels.** When the controller admits a report
(section 2.1), it checks each receipt's labels and nothing else: `status`
is `captured` or `unavailable`; a captured receipt has `producer: "worker"`
and `capture_stage: "before_apply"`; an unavailable receipt has neither. If
a receipt fails this, the controller does not admit the report. The result
is `malformed_runner_response` and the exit status is 1 (section 5.1).

**What nobody downstream compares.** The controller does not compare a
receipt's nonce, process identifier, byte count or digest with anything. A
consumer that holds its own request can compare the nonce it sent with the
receipt's `request_nonce`. A match ties the receipt to that request. It
does not show that the host made its own comparison against the worker's
capture.

**A malformed nonce never reaches capture.** A `capture_nonce` that is not
well formed is refused with the request (section 3.6), before any worker
exists.

**Applies to.**

| Kind of reply | The controller's label check |
| --- | --- |
| Ordinary, in either form | applies |
| Reporting failure | applies |
| Preparation failure | *not established: whether a receipt can be present* |

**Example.** A report from the current build carries a `captured` receipt
whose `producer` is not `worker`. The controller does not admit the report;
the result is `malformed_runner_response`.
*Checked by* the controller unit test
`compiled_profile_context_is_gated_after_the_response_version`, over the
fixture case `producer_future`. That test asserts the report is not
admitted. It does not assert the outcome string.

---

## What the worked section shows

- **Length.** The present paragraph is one line of 332 words. This section
  is 637, a little under twice that. The growth is the field table, the
  definitions and the applicability table, which the present text does not
  have; the rules themselves are about the same length.
- **Who is speaking is in every rule's first clause**, and the boundary
  refers back to section 2.1 instead of being re-explained.
- **Consequences differ by component and are stated with each rule**: an
  unavailable receipt from the host, an unadmitted report from the
  controller.
- **The example names its check and the check's limit.** Whether a reader
  should see that line, and in what form, is a machinery question for the
  next discussion.
- **A stated unknown.** The applicability table has a cell the coordinator
  could not fill. Drafting stage one will produce more of these, and each
  becomes either a reading task or a Known gap.

How a Known gap would read, using the one already identified for section
5.2:

> **Known gap.** The result and the exit status follow the host's outcome
> alone. When the controller finds a report's evidence inconsistent, it
> says so under `data.runner_sandbox_diagnostics` and the result is
> unchanged: one envelope can carry `result.ok: true` and
> `disposition_integrity: "invalid"`. A consumer that needs consistent
> evidence checks both.
