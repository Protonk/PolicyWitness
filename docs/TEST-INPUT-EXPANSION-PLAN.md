# Expand the controlled-input seam into several independent views

Status: complete. All three increments and the independent retirement are
implemented and accepted. This document records the implementation scope
and acceptance work. The statements about existing owners were checked against
the cited sources; native acceptance is recorded by increment below.

## Purpose

The [controlled read input](../tests/suites/witness_contract/README.md#controlled-read-input)
takes one small build-owned request through seven passages and compares what
the run reports with what the harness observed for itself. Extend it so that
one request and two files are looked at from several directions: replace an
object without changing its name or bytes, move the file's end across the read
bound, cross the query and attempt operands, and send the same rows through a
returning actor.

The work should answer three questions.

1. Which observations distinguish the queried target, the attempted target,
   the opened object and the returned content, and which changes does a given
   observation not see?
2. Does the returning-actor form carry the same observations, with ownership
   that stays correct where an actor's visit number and the global phase
   ordinal differ?
3. For each neighbouring case, what does this expansion add beside it, and
   what does that case keep owning?

The answer to the first two is a retained
[distinction table](#the-distinction-table): for each pair of passages, which
observations are equal and which differ, compared with an independently
authored expectation. The answer to the third is the
[account of existing owners](#what-existing-cases-already-establish) and one
[independent retirement](#one-independent-retirement).

This is harness expansion. `test-input read --target PATH`, its embedded
one-step body and ordinary `run` remain the product interface. The derived
specimens are harness-authored uses of the existing request grammar. No new
selector, action, evidence field, runner mode, limit or production code is
required; a step that turns out to need one is outside this plan. The guide
overhaul and release tagging are separate work.

## What existing cases already establish

Several parts of this experiment resemble cases that exist. The expansion is
worth its cost only where it observes something those cases do not, so each
increment below is stated against this table.

| Existing owner | Already established | What the seam adds beside it |
| --- | --- | --- |
| [`comparison_matrix`](../tests/suites/witness_contract/README.md#comparison-matrix), rows S05, S06, S26 and S27 of [the scenario matrix](../tests/fixtures/comparison/matrix.json) | The relation record for a crossed target (`matched`, `different_submitted`), a crossed operation (`different`, `same_submitted`), and an allowed and a denied `read_fresh`. It owns the relation classification. | A fresh read's descriptor identity beside a crossed query, where both files hold the same bytes. The seam pins relations only as part of associating a reply step with its submitted row. |
| [`prediction_target_is_independent_of_attempt_target`](../tests/suites/witness_contract/README.md#independent-prediction-and-attempt-targets) | Swapped prediction targets for write attempts, with external byte observations of the effect. | Read attempts, which leave no effect to observe externally and therefore rest on descriptor identity. |
| [`example_round_trip`](../tests/suites/witness_contract/README.md#the-apps-own-example) | A `file-read-metadata` query on a path whose data read is denied, pinned to `allow`; a `read_fresh` whose identity is the attempt target's while the query names another file; flat and one-actor derivatives. Its account states that one actor's visit numbers equal the global ordinals and that it observes no failed fresh read. | Two actors with a returning visit, so visit number and ordinal differ; failed fresh reads; a query that denies the path beside a read of the other object. |
| [`actor_compositions`](../tests/suites/witness_contract/README.md#principal-re-delegation-acceptance) and the extension cases | Multi-actor schedules, distinct policies per actor, gates and extension transfers. | Nothing in that territory. The returning passage uses equal policies, no gate and no extension. |
| [The shared consumer](../tests/lib/consumer.py), whose `validate` checks each retained passage | Internal validity of the reply, and reader agreement: [the client-capture reader](../tests/lib/runner_client_capture.py) decodes the exact retained host bytes with the independent Python wire reader under the expected identity and requires type-sensitive equality with the controller's `runner_result`. The actor rules join launch, subprocess, phase owner and application records. | The seam's own submitted association and native expectations. It does not repeat the consumer's joins. |

## Current owners and constraints

| Owner | Current behavior to preserve |
| --- | --- |
| [Publisher](../controller/src/test_input.rs) and [embedded input](../controller/src/test_inputs/read.json) | The publisher checks the two assigned target positions, substitutes the caller's absolute path, inserts the compiled identity and renders completely before writing. It keeps no second copy of the workload. |
| [Driver](../tests/suites/witness_contract/test_input.py) | Publication preflight precedes sampling and derivation. Each submission is registered in the ownership record before `run`, and retains its input, command, output and before/after samples. An unwitnessed worker exit stops fixture changes and retains staging. |
| [Checker](../tests/suites/witness_contract/check_test_input.py) | Independently authored publication and passage expectations, one obligation per row: status, build, consumer, association, worker, collections, query, order, attempt, identity and content. A missing prerequisite leaves dependent rows `not_evaluated`. |
| [Controls](../tests/suites/witness_contract/test_input_controls.py) | Coherent accepted and rejected captures with exact diagnostic sets, preparation controls through the real acquisition path, cleanup controls, one capture from another build, and the rule that every obligation kind is failed by some control. |
| [File observation helper](../tests/lib/file_observation.py) | Same-descriptor identity, full-content and bounded-prefix samples; comparisons take independently supplied expectations. It already admits a zero-length read and descriptor zero. |

Preserve a fresh host per submission and a fresh worker per named sandboxed
process. A returning actor keeps its worker across its own visits within one
submission. No sampler descriptor reaches a sandboxed process: every sampler
and writer descriptor is closed before `run`. All fixture changes happen
between submissions, after the previous worker exit is witnessed; this plan
introduces no race between a query and its attempt.

The original seven passages stay individually visible with their present rows:
`initial_a`, `updated_a`, `b`, `refusal`, `repair`, `denied_b` and `allowed_a`.
Keep the fresh-process deny/allow contrast, the exact refusal and repair, the
repeated publication and the literal-target operand. The rule that A's inode
survives its in-place updates stays as strict as it is.

## Increments and submission budget

The work is three increments. Each can be implemented, verified and committed
without the next, and the plan can stop after any of them. They are ordered by
what they cost: the first reuses a saved request unchanged, the second adds a
multi-step request, the third adds a second execution form.

Use the existing owned directory and A/B files. Let `N` be the checker's
independently authored `read_fresh` bound; keep it independent of the
implementation and the limits manifest. Existing payloads are `a^(N-1)`,
`b^(N-1)` and `b^(N-1) + c + d`. Define `P = b^(N-1) + c`, exactly `N` bytes,
so the existing long payload is `P + d`.

Passages run in this order whichever increments are present. The two matrix
passages change no file, so adding them later does not disturb the passages
after them.

| Passage | Increment | Submitted request | Fixture and distinguishing obligation |
| --- | --- | --- | --- |
| `crossed` | 2 | Five-step ordinary derivative | A and B both hold `P + d` under distinct inodes. Separates query target, attempt target and query operation. |
| `returning` | 3 | The same five rows in the actor form | Same files and policy. Exposes actor, visit and phase ownership. |
| `replaced_a` | 1 | Exact saved bytes of the `allowed_a` request | Original A is parked; a separately created object with the same bytes occupies A's name. Requires the new inode. |
| `suffix_a` | 1 | The same saved bytes | Replacement A changes in place from `P + d` to `P + e`. The full digest changes; the returned content does not. |
| `empty_a` | 1 | The same saved bytes | Replacement A is truncated in place. A successful zero-length read is an observation. |
| `bound_a` | 1 | The same saved bytes | Replacement A holds exactly `P`. The returned content equals the long payload's prefix. |

| Increments present | `run` submissions | Executions | Selected-app commands |
| --- | --- | --- | --- |
| None (baseline) | 7 | 6 | 12 |
| 1 | 11 | 10 | 16 |
| 1 and 2 | 12 | 11 | 17 |
| 1, 2 and 3 | 13 | 12 | 18 |

The publisher is still invoked four times and `--version` once. Keep deriving
the accounting from recorded argv and observed results, then compare it with
the expected totals for the increments present. Offline controls have their own
accounting. Do not multiply payloads by execution forms: the boundary passages
run in the ordinary form only.

### Increment 1: same name, same bytes, new object; content boundaries

After the last passage that uses original A, observe it again. Create a
separate file holding `P + d` with A's device, mode, owner, group and size, and
establish that its inode differs from original A's and from B's. Rename
original A to `A.previous` inside the owned directory, then rename the
replacement to A's pathname. Keep the parked object until the last replacement
passage finishes. Record both renames and sample A, B and the parked object.

Submit the saved `allowed_a` request byte for byte, including its deny-B
policy. This is what makes the passage a control: the earlier `allowed_a`
capture has the right input, path, policy and content, and the wrong opened
identity. A newly authored allow-default request would differ in more than the
object.

Represent two A identity generations. The original covers every earlier A
observation and both matrix passages; the replacement covers `replaced_a`
through `bound_a`. Require one identity within each generation and the declared
change between them. No other inode change is acceptable. The parked file
keeps the original identity and bytes, and B is unchanged.

The four boundary classes are then all observed natively: empty (`empty_a`),
shorter than the bound (the existing `updated_a`), exactly the bound
(`bound_a`) and longer (`replaced_a`, `suffix_a`). For the empty file require a
successful open and stat, a returned count of zero, the empty-content digest
and a completed close. For `bound_a` require count `N`, the independently
computed digest of `P` and the replacement inode.

Two indistinguishable pairs are part of the result. Across `replaced_a` and
`suffix_a` the full digests differ while the returned count, returned digest
and descriptor identity agree. Across `suffix_a` and `bound_a` the lengths
differ and the returned content agrees. The fresh-read content row therefore
accepts either capture's read record in the other's place, and the distinction
table states that. It accepts the read record only: the before/after samples
stay required, and a missing or stale full sample fails its own row. A changed
byte inside `P` is the rejected neighbour.

### Increment 2: crossed operands and operations

Clone the published B input, keep its contract, and derive five steps with
explicit IDs. Use the existing allow-default policy with the literal
`file-read-data` denial for B, including its `with no-report` clause. Every
attempt is `file/read_fresh`; every query uses the path filter.

| Step ID | Query operation and target | Attempt target | Expected query | Expected attempt |
| --- | --- | --- | --- | --- |
| `read-aa` | `file-read-data`, A | A | allow | successful fresh read of A |
| `read-ab` | `file-read-data`, A | B | allow | open fails with `EPERM` |
| `read-ba` | `file-read-data`, B | A | deny | successful fresh read of A |
| `read-bb` | `file-read-data`, B | B | deny | open fails with `EPERM` |
| `metadata-b` | `file-read-metadata`, B | B | allow | open fails with `EPERM` |

Reuse the existing per-step rows. Allow is a validator answer with native
return zero and errno zero; deny is native return one with errno zero. A failed
fresh open is outcome `read_failed`, return -1, errno 1, with open return -1
and open errno 1 in the fresh-read record. A successful read requires the
syscall chain, descriptor identity, returned count and prefix correspondence.
Both files keep their bytes and identity across the submission, and the run
finishes with exit 0 and a confirmed reap although three attempts fail.

`operation_relation` is `matched` for the first four rows and `different` for
`metadata-b`. `target_relation` is `same_submitted` for `read-aa`, `read-bb`
and `metadata-b` and `different_submitted` for the crossed rows. Check these in
the association row. `query_first` keeps its own row, credited only beside the
expected answer.

Because A and B hold equal bytes, `read-ba` is the row no existing case has:
the query answer concerns B and denies, and the only observation that says
which object was read is the descriptor identity, which must be A's. `read-ab`
is its mirror: an allow answer about A beside a failed open of B.

The `metadata-b` expectation has a precedent. The example pins `allow` for a
`file-read-metadata` query on a path under the same kind of data-read denial.
That observation is for another path, so the first run of this passage is
still the first observation for B. A different answer is a counterexample to
investigate in the fixture. Do not change the expectation from observed output
to pass, and do not accept either answer: a row that accepts both tests
nothing.

These rows establish independent observations and submitted relationships.
They do not establish that a prediction and an enforcement agree, or that the
sandbox caused a failure.

### Increment 3: returning actors

Use two applied actors, `Left` and `Right`, with the same deny-B policy and
`selected` equipment. Partition the five rows unevenly:

| Phase | Actor | Steps | Global ordinal | Actor visit |
| --- | --- | --- | --- | --- |
| `left-first` | Left | `read-aa`, `read-ab` | 1 | 1 |
| `right-only` | Right | `read-ba` | 2 | 1 |
| `left-second` | Left | `read-bb`, `metadata-b` | 3 | 2 |

Left's second visit is the point of the form: its `actor_visit` is 2 and its
ordinal is 3, and Right's only visit is 1 at ordinal 2. The example's single
actor cannot separate those two numbers.

The seam asserts the submitted association and leaves internal joins to the
consumer, which must accept the capture:

- Left's `visits` are `[1, 3]` and Right's are `[2]`; each phase carries its
  declared owner, ordinal, `actor_visit` and exact step IDs, and its validator
  expected exactly those IDs.
- The two actors' launch PIDs differ. Left has one launch and one subprocess
  record for both visits. PID inequality is required between the two
  concurrently live actors only, not across submissions.
- Each actor is `apply`, set up as applied, with `application_count` 1 and the
  submitted policy digest; equipment is requested and resolved as `selected`.
- Every phase arrived, was collected, released, acknowledged and completed;
  both workers exited 0 and were reaped. The existing
  [worker exit witness](../tests/lib/worker_exit_witness.py) already requires
  every launched actor's reap before fixtures change.
- Each step meets the same native expectations as in `crossed`, found by its
  submitted ID.

Run `returning` only when `crossed` met its native expectations in the same
case execution. A failure in `returning` then concerns the form and not the
matrix.

Equal policy contents cannot show whether the two policies reached the right
actors. Record that limit; `actor_compositions` owns distinct policies. Do not
add extensions, gates, an unapplied actor or a second actor/payload product.

This increment costs the most. Its offline controls need a constructed
two-actor capture that the full consumer accepts, as the example's
[authored actor run](../tests/fixtures/example_round_trip/README.md) does for
one actor. The existing seam checker, controls and driver are each a few
hundred lines, and the example's three-form checker and controls are about
3,500. If the returning-form checker, its controls and that capture cannot stay
near the size of the existing seam files, stop and report what the form
demands before building a second example checker.

## The distinction table

Have the checker extract a small fixed set of facts per passage and step:

| Observation | Facts compared |
| --- | --- |
| Submitted request | The input bytes; for a step, its query operation, query target and attempt target. |
| Query record | Result source, outcome, native return and errno. |
| Attempt record | Outcome, return, errno, and whether the open, the descriptor stat and the close each succeeded. |
| Descriptor identity | The fresh read's device and inode, or their absence after a failed open. |
| Returned content | The returned count and the digest of the returned bytes, or their absence. |
| External sample | Device, inode, length, full digest and prefix digest from the harness's own descriptor. |
| Ownership | Phase, ordinal, actor and actor visit. |

For each named pair below, compare each observation and record `equal` or
`different` in `distinctions.json` beside the report. Author the expected table
in the checker, independently of the captures, and give each pair one report
row that fails when any cell differs from its expectation.

| Pair | Expected to differ | Expected equal |
| --- | --- | --- |
| `allowed_a`, `replaced_a` | Descriptor identity; external inode. | Request bytes, query, attempt, returned content, external digests. |
| `replaced_a`, `suffix_a` | External full digest. | Everything the run reports, and the external identity and prefix digest. |
| `suffix_a`, `bound_a` | External length and full digest. | Everything the run reports. |
| `bound_a`, `empty_a` | Returned content; external length and digests. | Request bytes, query record, attempt record, descriptor identity. |
| `read-aa`, `read-ba` | Submitted query target; query record. | Attempt record, descriptor identity, returned content, external sample. |
| `read-aa`, `read-ab` | Submitted attempt target; attempt record; descriptor identity and returned content, which the failed open leaves absent. | Query record. |
| `read-bb`, `metadata-b` | Submitted query operation; query record. | Submitted targets, attempt record. |
| Each step in `crossed` and in `returning` | Request bytes; ownership. | The step's submitted operands, query record, attempt record, descriptor identity, returned content. |

The step pairs are compared within `crossed`, and the last row compares each
of the five steps across the two forms.

The table is the plan's product for the first two questions. It reports which
observation a change reaches on this build and machine, and nothing about why.
A pair whose run-reported observations are all equal is an accepted
indistinguishability, stated as such, not a gap to close by adding fields.

## Checker and controls

Keep the two catalog cases, `witness_contract/test_input` and
`witness_contract/test_input_controls`. Extend acquisition in `test_input.py`.
Whether the matrix and actor evaluation live in the existing checker or a
private module beside it is the executor's choice; either way they are
helpers of the two cases, not new catalog cases. Keep derivation separate from
expected-request construction: a constructor's own output is not an oracle for
its transformation. Do not merge the example and test-input evaluators into a
configurable workload engine.

Keep one obligation per row, as the checker does now, with stable IDs by
passage, phase, actor and step. The existing rule that every obligation kind is
failed by some control then extends to the new rows unchanged, and it already
fails a checker that accepts everything. Introduce named conditions inside a
row only where an obligation cannot be split. Keep `passed`, `failed` and
`not_evaluated`, and keep reporting every independently inspectable failure.
The refusal passage has no execution rows; that is inapplicability and needs
no status.

Controls stay coherent wherever the seam's own row is the intended rejector:
change every dependent field, require the consumer to accept the capture, and
state the exact diagnostic set. A fault the consumer owns is not repeated here.
Constructed captures remain labeled constructed; they show what the checker
distinguishes, not what a native runner emits.

| Increment | Rejected controls | Accepted controls |
| --- | --- | --- |
| 1 | The whole earlier `allowed_a` capture in `replaced_a`'s place; the old identity with current content; a replacement sharing original A's inode or B's; an inode change inside a generation; a missing or changed parked-object sample; an empty read reported as unavailable; a wrong count or digest at zero, `N - 1` and `N`; a stale full sample; a changed byte inside `P`. | `suffix_a`'s read record in `replaced_a`'s place and `bound_a`'s in `suffix_a`'s, each beside its own samples. |
| 2 | A wrong query operand alone, a wrong attempt operand alone and a wrong query operation alone in the derivative; an omitted, duplicated or reordered row; a wrong query answer beside a correct attempt and the reverse; correct bytes with B's identity in `read-ba`; another step's coherent evidence under this step's ID; a wrong relation; an expected answer without established order. | None beyond the baseline. |
| 3 | Actors exchanged; Left's second visit numbered 1 or 3; correct steps in the wrong phase; a wrong visit list; validator expected IDs from another phase; one PID for both actors; a second application; an unreaped actor, which must also withhold cleanup. | Every actor, phase and step renamed consistently. |

Across increments, keep the existing masking controls: combined query,
identity, lifecycle and sample faults retain every applicable diagnostic, a
missing prerequisite withholds only its dependent rows, and a bad publication
does not hide faults in retained captures. Preparation controls must still
show that a wrong publication reaches no sampling, derivation or `run`.

Ownership needs little new machinery. The parked and replacement objects live
inside the one owned directory and are removed with it. Keep `session.json`,
registration before `run`, and per-attempt exit evidence. Cleanup decisions
keep using admitted host evidence and the worker exit witness, never a passing
checker summary.

## Not included

These were considered and are left out. Each names what would change the
decision.

- **A Rust replay of the native captures.** The envelope under test is already
  the shipped Rust reader's decoding of the host bytes, and the consumer
  already decodes the same retained bytes with the independent Python reader
  and requires equality with that projection. A test build of the controller
  has [the test identity](../controller/src/json_contract.rs) compiled into
  its admission, so replaying a capture bound to the candidate's identity
  needs either a second controller compiled under that identity inside a
  default native case, or production admission that takes the identity as a
  parameter. Both exceed a harness expansion, and the result would be the same
  decoder agreeing with itself. The
  [runner-unit replays](../tests/suites/runner_unit/README.md) work because
  their producer and reader share the test identity. Reconsider if admission
  gains an identity parameter for another reason.
- **A second report of views.** The checker's rows already separate the
  submitted request, the reply's observations, the controller's account and
  the external samples. The distinction table is the one new artifact.
- **The lifecycle oracle and actor evidence reader as extra per-passage
  readers.** Every passage here ends in a clean exit, the least informative
  input for the oracle, and their own cases own those readers' controls.
- **Wire and producer mutation controls.** Changed, truncated and foreign
  reply bytes are owned by the consumer's controls in
  `blackbox_e2e/checker_controls`. The seam keeps its one capture from another
  build, which shows that its reply rows are withheld.
- **A Swift bridge.** The Swift corpus validates typed records before writing
  them; it is not an independent decoder of native reply bytes.

## One independent retirement

`witness_contract/bug_report_returns_attempts` is entailed by
`witness_contract/bug_report_returns_verdicts`. The two scripts submit the same
policy, query and attempt under different specimen IDs. The first asserts a
nonempty `steps` and an integer first `attempt.rc`; the second fails on empty
`steps`, asserts the same integer, and adds the allow answer, application, the
release chain, publication, `query_first`, a confirmed clean exit and an
allow-default neighbour.

This does not depend on the expansion and can land before it, after it or
without it, in its own commit. Run both cases once on the current candidate,
remove the script and its catalog row together, repeat the repository search
for references, and run the surviving case and `source_drift`. Tighten the
survivor's integer check to exclude booleans in the same commit if wanted. A
new offline controls case for this historical regression is not part of the
retirement: the survivor's assertions do not change. If the comparison at
implementation time finds an assertion the survivor lacks, keep the old case
and record the difference.

The expansion retires nothing else. These neighbours keep obligations it does
not reach:

| Existing case or family | Why it stays |
| --- | --- |
| `happy_path_baseline` | The suite's required sentinel, with a successful `open_read` and descriptor-derived path evidence. `read_fresh` observations do not replace that action. |
| `prediction_target_is_independent_of_attempt_target` | Observes changed and preserved bytes for write attempts before reading any capture. |
| `comparison_matrix` | Owns the relation classification across every action and filter kind. |
| `queries_precede_attempts`, `phases` and the barrier and gate controls | Read/unlink sequencing, timeouts, acknowledged gates and between-query mutation are conditions absent here. A `query_first` row is not a substitute. |
| `example_round_trip` | Owns the published example's exact bytes, its refusals and the one-actor derivative. |
| Capacity, creation and guide workflows | Full-capacity retention, create/preserve behavior and external-runner workflows are independent. |

## Implementation sequence and verification

For each increment, in order:

1. **Author offline expectations first.** Write the derivative or fixture
   transition, the expected rows, the distinction pairs and the accepted and
   rejected controls. Qualify `test_input_controls` before spending native
   runs.
2. **Extend acquisition.** Add the passages, the samples of every file a
   passage names, and the command accounting for the increments present.
3. **Run the native case** on one current signed candidate with recorded
   identity. Build through the normal signed pipeline if the app is absent or
   stale; never relabel an old app as current. Retain failing captures and
   stop on an unwitnessed exit. A native counterexample may lead to a
   documented fixture correction and another run; widening a query, errno or
   completion expectation to pass is not allowed.
4. **Review** the report rows, the distinction table, the accepted
   indistinguishable pairs, the cleanup record and the accounting. A native
   pass alone does not qualify the checker; the offline controls must pass on
   the same source.
5. **Update the current documentation**: the owning suite README, catalog
   descriptions, the suite map and any coverage or change-verification entry
   the increment touches. Commit the increment with its acceptance.

Record acceptance in this plan as each increment closes: case IDs, candidate
identity, run paths, the native answers observed, the distinction table's
outcome and the limits found. Development runs are disposable and are cited
with that limit.

Use [test guidance](../tests/AGENTS.md) and the dispatcher for every case;
builds and test executions in one checkout are serial.

| Changed boundary | Required verification |
| --- | --- |
| Seam checker, controls or driver | `witness_contract/test_input_controls`, `witness_contract/test_input` and `source_drift`. |
| `tests/lib/file_observation.py` or another shared helper, if changed | Its other owners as well: `witness_contract/example_round_trip_controls`, `witness_contract/example_round_trip` and `blackbox_e2e/checker_controls`. Prefer not changing shared helpers; the existing primitives appear sufficient. |
| Regression retirement | Both native cases before deletion, then the survivor and `source_drift`. |
| Catalog and documentation | `source_drift` and `docs/generate_limits.py --check` through the repository Python wrapper; the owning generator if one of its inputs changes. |

Inspect `--list` before running a selection. Do not select the whole
`witness_contract` suite for these cases: a suite selector includes its opt-in
members. No guide-workflow run, release battery or barrier mutation run is
required by this expansion. A change to the worker wait, release store or
query eligibility would require `witness_contract/order_barrier_mutations` and
is outside this plan. A prior pass is reusable only with recorded source
applicability.

## Completion and limits

Each increment is complete when its passages run natively with the earlier
passages intact, its controls reject and accept as stated, its distinction
pairs match, cleanup is verified, the suite accounts are current and the work
is committed. The plan is complete when the maintainer has taken or declined
each increment and the retirement. Record source review, constructed controls
and native observations separately. Do not promote support grades or claim
release evidence from development captures.

The expanded seam stays finite. It does not show that a file was read past the
bound, that a file was unchanged between a sample and the instant of an
attempt, that a prediction and an enforcement agree, that a policy caused a
failure, that unequal policies reach the right actors, or that execution forms
are equivalent in general. Those limits belong beside the observations that
expose them. The value of the expansion is a controlled set of observations
that are known to distinguish some changes and known not to distinguish
others, with rejected and accepted controls that show which conclusions each
can carry.

## Execution acceptance

Increment 1: source review and constructed controls establish the two identity
generations, four content classes, exact saved request and four independently
expected distinction pairs. `witness_contract/test_input_controls` passed in
`tests/out/runs/input-expansion-1-controls`; the native
`witness_contract/test_input` passed in
`tests/out/runs/input-expansion-1-native`. The selected signed candidate reports
`development:c2b33f9eca0cb15a83addf93fc0072f646b12a5cd1c579fc5fbb0664ea0192bc`,
which matches current `docs/build_contract.py` derivation. Its build number is
1447; its recorded build commit is `7cd93676` with dirty sources. The matching
selected-input identity, rather than that commit alone, establishes source
applicability for the unchanged product.

Native observations: allow queries returned 0/errno 0; the deny-B query returned
1/errno 0 beside open -1/EPERM. All successful reads published descriptor
identity, bounded bytes and close; the empty read returned zero bytes. The four
distinction pairs matched, including both accepted indistinguishable returned
contents. Accounting recorded 11 submissions, 10 executions, one refusal and
16 selected-app commands. Cleanup confirmed all exits and removed the owned
directory. These development captures are disposable, not release evidence.

Increment 1 final checks: `witness_contract/test_input_controls` and all ten
`source_drift` cases passed in `tests/out/runs/input-expansion-1-accept`;
`tests/lib/python.sh docs/generate_limits.py --check` passed. The native run
used the same checker, helpers and acquisition code; subsequent changes only
updated case descriptions and documentation.

Increment 2: source review keeps derivation independent of the five authored
request/native expectation rows. The 77 constructed controls passed in
`tests/out/runs/input-expansion-2-controls-b`; the preceding controls run caught
an incomplete expected diagnostic set for the existing B-shares-A control:
the new matrix's independent B sample correctly added `crossed.peer`. Its
expectation now includes that independently inspectable fault.
`witness_contract/test_input` passed in
`tests/out/runs/input-expansion-2-native` on the same candidate identity as
increment 1. The five query answers were allow, allow, deny, deny, allow, with
native rc 0, 0, 1, 1, 0 and errno 0. A opens succeeded with A's descriptor
identity and prefix; B opens returned -1/EPERM. All workers completed/reaped;
all seven distinction pairs matched. Accounting recorded 12 submissions,
11 executions, one refusal and 17 selected-app commands; owned staging was
removed. Equal bytes do not distinguish A from B; descriptor identity does.
The metadata expectation was observed unchanged, not widened. Development
captures remain disposable.

Increment 2 final acceptance: `witness_contract/test_input_controls` and all ten
`source_drift` cases passed in `tests/out/runs/input-expansion-2-resume-accept`.
`docs/generate_limits.py --check` passed. The earlier
`input-expansion-2-accept` run was deliberately interrupted for machine sleep;
its finalized interrupted result supplies no acceptance credit. Native acquisition,
checker and control sources are unchanged from the passing increment-2 native
run; subsequent edits only updated descriptions and the plan's checkpoint.
The resumed review confirmed all 244 report rows, seven distinctions, 12/11/17
accounting and verified cleanup. No product or shared-helper source changed.

Independent retirement: source comparison found no assertion in
`witness_contract/bug_report_returns_attempts` absent from
`witness_contract/bug_report_returns_verdicts`. Both passed before deletion in
`tests/out/runs/input-expansion-1-native` on the candidate identity above.
The redundant script and catalog row are removed together; the survivor's
assertions are unchanged. A repository search after removal found only this
plan and the historical `records/tests/TEST-WORK-SURVEY-REPORT.md` references,
which describe their recorded source snapshot and remain intact.

The surviving case and all ten `source_drift` cases passed after removal in
`tests/out/runs/input-expansion-final-accept` (run
`20261115T131759Z_d80074cb`). The regression still observed its allow query,
published integer attempt return, established order and clean worker exit,
plus the successful allow-default neighbour. No case overlapped system sleep.
This final run also covers the independently implemented returning-form work;
retirement changes only the redundant script and catalog membership.

Increment 3 source review: returning acquisition uses the same five crossed
rows and equal policies in the prescribed 2+1+2 partition. The actual
acquisition gate requires the same run's crossed expectations before actor
derivation; final evaluation checks all retained captures. Internal actor joins
remain owned by the consumer. The actor-specific checker and constructed
capture/controls occupy 84 and 139 lines respectively, keeping this increment
near the size of an existing seam file rather than creating another example
engine. Shared helpers, product code and public interfaces are unchanged.
The final review also pins B's identity between the refusal, repair and denied
submissions with a coherent replacement control.

Constructed acceptance: `witness_contract/test_input_controls` passed all 91
controls in `tests/out/runs/input-expansion-3-final-controls`, including the
accepted suffix/bound read substitutions, consistent actor/phase/step renaming,
the actual crossed gate and an unreaped actor withholding cleanup. Malformed
internal actor joins remain explicitly consumer-rejected controls; coherent
correspondence faults are required to pass that consumer. The two-actor capture
is constructed from the existing authored actor template and separately
constructed matrix observations, not from a native output.

Native acceptance: `witness_contract/test_input` passed all 302 report rows in
`tests/out/runs/input-expansion-final-accept`, under the same current candidate
identity recorded above. `source_drift` passed all ten cases in that run, and
`docs/generate_limits.py --check` passed. Left's PID was 45544 with visits
`[1, 3]`; Right's was 45545 with visits `[2]`. Both applied once and exited 0
with confirmed reap. Phase ownership was Left/1/1, Right/2/1, Left/3/2
(actor/global ordinal/visit), with exactly the planned step partitions.
Both forms observed query answers allow, allow, deny, deny, allow with native
rc 0, 0, 1, 1, 0 and errno 0. Reads of A succeeded with A's descriptor
identity and bounded content; B opens failed with -1/EPERM.

All twelve distinction pairs matched their independently authored cells.
Accounting recorded 13 submissions, 12 execution passages, one refusal,
four publications and one version command: 18 selected-app commands. Every
launched worker's exit was witnessed and the owned fixture directory was
removed. No case overlapped system sleep. This supersedes the preliminary
299-row `input-expansion-3-native` run by including the final B-continuity rows.
The checker, driver, controls and fixtures are identical between the final
control run and native acceptance; only acceptance prose is appended afterward.

The observed limits are retained: suffix-only changes and shortening to the
bound can leave returned content indistinguishable; samples do not establish
continuous stability or a read beyond the bound. Equal actor policies cannot
identify a swapped policy destination. These results establish neither general
form equivalence, prediction/enforcement agreement nor sandbox causation.
All run paths above contain disposable development evidence, not release
acceptance evidence. The owning accounts and catalog describe the final scope.
