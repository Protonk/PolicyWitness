# One example through flat, phased and actor execution

Status: proposed; no implementation or native qualification of the expanded
workload has begun. Prepared against `3fd340d1`, including the three-step
example in `b4e00762` and the checker review in `9e14a1c6`. The earlier plan is
retired; its reusable machinery lives in the
[example case and controls](../tests/suites/witness_contract/README.md#the-apps-own-example).
The accepted local file assumptions are in
[DEPENDENCIES.md](DEPENDENCIES.md#files-used-by-the-emitted-example).

## Result and boundary

Make the app's emitted example an ordinary two-phase specimen, then execute
that document unchanged and two explicitly derived forms through the same
public `run` command. All three perform the current three actions under the
current policy. Each must meet independently authored expectations before
agreement between executions can earn credit.

This adds a second collection/release boundary to the public example and
exercises both ordinary and actor orchestration with a small, comparable
experiment. It connects publication, held-request preparation, native
observations and reply interpretation so later modularization can be checked
against behavior at those boundaries.

Keep `example` argument-free and preserve its publication and admission
promises. Emission still reads no file and launches nothing. Add no selector,
target parameter, runtime operation, expected-results interface or alternative
execution path. The app publishes one specimen; the test owns the two
derivatives. Actor execution is exercised by the test, not added to the
published example. Production scheduling, admission, transport and worker
code are outside this change.

The [controlled-input plan](TEST-INPUT-PLAN.md) owns target binding and changing
file contents across submissions, along with the lesson/guide migration.
This plan owns request structure and execution ownership. Neither needs the
other's command change. If either extracts observation helpers first, use the
landed helpers and rerun their dependent cases; do not maintain two observers.

## Workload and exact transformations

Keep the policy source byte-for-byte:

```sbpl
(version 1) (allow default) (deny file-read-data (literal "/usr/share/dict/propernames") (with no-report))
```

Keep the three action objects and their step IDs from
[EXAMPLE_DOCUMENT](../controller/src/example.rs). Change only the container
from `probe_plan` to `phases`, partitioned as follows:

| Phase | Step | Query | Attempt | Independent native expectation |
| --- | --- | --- | --- | --- |
| `initial-reads` | `read-hosts` | Data read of A, `/etc/hosts` | `open_read` A | Validator allow, successful open. |
| `initial-reads` | `metadata-propernames-read-connectives` | Metadata read of B, `/usr/share/dict/propernames` | `read_fresh` C, `/usr/share/dict/connectives` | Validator allow; successful fresh read whose identity, count and bytes correspond to the observer's C sample. |
| `restricted-read` | `read-propernames` | Data read of B | `open_read` B | Validator deny with native return 1 and query errno 0; separately, `open_failed` with attempt errno exactly `EPERM`. |

Each phase is an ordinary `{phase_id, actions}` object. All three executions
should finish with observed process status 0 despite the failed final attempt.
The second step's metadata answer concerns B and predicts nothing about its
read of C. No assertion compares a prediction with its attempt to declare
agreement or assigns the failed open a sandbox cause.

| Form | Construction from emitted phased document P | Required execution structure |
| --- | --- | --- |
| Emitted | Submit the exact saved stdout bytes. | One worker, two phases with action counts 2 and 1. |
| Flat | Deep-copy P; remove `phases`; set `probe_plan` to its action objects in phase order. Preserve every other member. | One worker, the implicit `main` phase, three actions. |
| Actor | Deep-copy P; move its entire `policy` object into one actor's `sandbox.policy`; remove the top-level `policy`; add `actors: [{actor_id: "example-reader", equipment: "selected", sandbox: {mode: "apply", policy: P.policy}}]`; add that actor ID to both phases. | One applied selected-equipment worker, two visits, the same action partition. |

Keep contract, specimen ID, phase IDs where present, step IDs, policy bytes,
query operands and attempt operands unchanged in both derivatives. Each
submission gets a fresh host and fresh worker; a worker persists only across
its own two phases or visits. The actor variant has no extensions, termination
dependency, unapplied mode, entitlement requirement or compiled-profile
capture. Use the bundled standard runner for all three.

Retain P's raw bytes, both derivative files and a transformation account that
names the permitted member additions, removals and relocation. Validate the
transformations before submission using independently specified field and
membership assertions. Do not use the transformation function itself to
produce its expected answer, or production normalization to construct the
test's oracle. A malformed derivative fails preparation before it reaches
`run`; a valid derivative's admission is established by its actual execution.

The final emitter is phased. During control development the current flat
document can supply the unchanged action objects; no extra native rehearsal
is required. Promote the constant before the one candidate build. The final
live case requires phased emission and refuses a flat or actor document in
its place, even though those forms are exercised as derivatives.

## Observation and comparison

### Independent assertions within each execution

Extend `witness_contract/example_round_trip`, keeping its two emissions,
version observation, publication checks and six refusal passages. Add the flat
and actor submissions to this case so the three captures share one explicit
experiment without depending on another case's output or execution order.

For each form, retain the submitted bytes, command, stdout, stderr, observed
exit status and observer samples. Sample the union of query and attempt paths
before and after that submission. Finish and close the before samples before
invoking `run`. Reuse `observe_target` and its rename/unlink controls; retain
digests and lengths, not another copy of raw file content. The app's bounded
`content_hex` remains in its raw reply.

Keep identity admission before reply interpretation. Compare the submitted
policy digest with the appropriate ordinary or actor policy records and
controller dossier, rather than manufacturing singular policy/worker fields
for an actor reply. Check each action by submitted ID and its query/attempt
echoes, with order checked separately. Duplicate IDs remain visible before
any dictionary lookup can discard them. Read the actor's application,
equipment and subprocess evidence at their actual locations.

Reuse the reviewed prerequisite behavior: the target concerned by an
unobserved step half withholds that half's native expectation; an independent
failure remains a failure beside a missing prerequisite; a met native
expectation receives no pass while a workload prerequisite is missing. A
missing expected C identity withholds identity correspondence. Changed C
samples withhold dependent correspondence, preserving unrelated faults.
Extend these controls to all forms instead of restoring an all-or-nothing
gate during helper extraction.

Require the common native expectations separately for each form: allow,
allow, deny; successful open, successful fresh read, failed open with EPERM;
query-first order; observed status 0 and a finished reply. Successful fresh
open means a nonnegative descriptor, not descriptor zero. Keep successful
stat, bounded read and close observations and independent identity/content
comparisons. Reuse the independent consumer for internal record semantics.

### Structure is checked before extracting common observations

The submitted structure supplies each expected action/phase/actor association.
An assertion must reject a coherent reply to another valid partition even
when all three actions and native outcomes are present.

- Flat has one implicit phase containing all three submitted IDs. Phased and
  actor have exactly two phases, with the first two IDs then the third, in
  that order. All phases arrive and complete with their declared ordinals.
- Every phase in this workload has eligible queries and its own collected
  validator evidence. Bind the collection to that phase's exact expected
  query IDs, operations, operands and live worker. Require collection closure,
  release, acknowledgement and lifetime evidence supporting `query_first`.
  Earlier collection records cannot supply the second phase.
- Ordinary phases retain one owned worker. Actor phases name the sole actor,
  its two visits and its owned worker; its setup reports applied once, its
  selected equipment matches the launched process, and its policy received
  digest equals the submitted source digest. Check observed cleanup/reap.
- Actor replies retain actor-specific policy, equipment and process records,
  with the corresponding per-actor controller diagnostics. They must not gain
  a fabricated singular worker/policy account during projection.

Use observed ownership and lifecycle relationships. Numeric PID inequality
across sequentially reaped processes is not a freshness proof: the OS can
reuse a PID. Do not require identical descriptors, timestamps, PIDs, timing
intervals or whole envelopes between submissions.

### Cross-form correspondence

Only after each record's identity and submitted association are established,
extract a small per-role comparison of query result/source/native return/query
errno, attempt result/source/return/errno, and the fresh read's device/inode,
read count and content digest. Preserve query and attempt as separate values.
Use explicit readers of the ordinary and actor record locations; never
rewrite an actor reply into an ordinary reply to make the ordinary checker
accept it.

Compare those observations across forms only when the required external
samples establish the same files and contents across all three passages.
Missing or changed samples withhold that correspondence and report the
prerequisite or stability failure. Independently established per-form faults
remain visible. Different evidence structures are validated within each form
and are not discarded merely to produce equal summaries.

Equal summaries alone earn no success. A control in which all forms carry
the same wrong answer must fail each independent native expectation even
though cross-form equality holds. A control with an identical common summary
but a wrong phase partition must still fail association. Those two controls
protect against a comparison layer concealing a shared error.

## Existing owners and the small extraction

| Owner | Reuse or change |
| --- | --- |
| [Example checker](../tests/suites/witness_contract/check_example_round_trip.py) and [controls](../tests/suites/witness_contract/example_round_trip_controls.py) | Keep publication/refusal assertions, per-role native expectations, observer controls and reviewed evidence gating; add per-form structure and cross-form assertions. |
| [Independent consumer](../tests/lib/consumer.py), [phase evidence](../tests/lib/phase_evidence.py), [actor evidence](../tests/lib/actor_evidence.py) | Read all three full envelopes through the existing validators. They own internal record, ordering and equipment consistency. The example case owns correspondence to its submitted documents and external samples. |
| [Phase case](../tests/suites/witness_contract/check_phases.py) | Retain its action partition and collection checks, and its live filesystem-change discriminator. This example does not replace that experiment. |
| [Actor compositions](../tests/suites/witness_contract/check_actor_compositions.py) | Use its existing application, equipment, policy receipt, lifecycle and request-to-reply associations as the reference for selecting observations. Keep its multi-actor and extension-specific expectations there. |
| [Controller preparation test](../controller/src/run_flow.rs) | Preserve `emitted_example_reaches_the_client_as_the_emitted_document`; extend controlled preparation coverage to the declared flat/actor transformations, including actor policy preservation. Its exact-byte claim ends at the controlled client boundary. |

Extract only the observer and scalar fresh-read comparisons if needed by both
forms and the pending test-input work. Keep expected outcomes, role concerns,
request shapes and diagnostic classifications owned by their cases. Existing
consumer rules remain the shared semantic reader; introduce no universal
workload description language, production classifier dependency or second
general reply interpreter.

Keep existing assertion identifiers for the emitted case where their meanings
hold. Give added flat, actor, structure and cross-form assertions stable
identifiers and one-sentence statements. Report which form, role, submitted
ID, phase and actor supplied each observation. If an existing assertion's
meaning changes, update its controls and account explicitly; a count of
assertions is not the acceptance criterion.

## Acceptance table and discriminating controls

Use constructed passing captures for all three forms and independently
authored expected diagnostic/classification sets. Reuse the existing fixture
builders where their records apply. If coherent actor captures require a new
authored fixture, give it a fixture-catalog owner; do not freeze a development
run or generate an expected answer from the checker under test.

For a control aimed at external association or correspondence, update all
dependent capture fields and require the full consumer to accept the record
before crediting the intended rejection. For malformed evidence controls,
identify the reader rule expected to reject it. Preserve combined faults and
withheld observations explicitly.

| Distinction | Passing observation | Required control |
| --- | --- | --- |
| The app publishes the phased workload | Two phases with partition 2+1 and unchanged role relationships | Flat emission, swapped phases, collapsed partition or lost action fails preparation. |
| Derivatives preserve the experiment | Only the declared container and policy relocation changes | Changed policy byte, operand, action or identity is refused by the independent transformation check. |
| Every form has its own native oracle | Each separately meets allow/allow/deny and its attempt expectations | All three carry allow for the denied query: equality holds, each form's prediction assertion fails. |
| Phase membership survives projection | Exact submitted phase/action association | Coherent 1+2 partition with the same common observations fails submitted association. |
| Collections belong to the right phase | Per-phase accepted records and collection/release chain | Borrowed first-phase collection, missing completion or altered acknowledgement is rejected at its responsible association or reader boundary. |
| Actor ownership reaches every projection | Submitted actor, applied policy, equipment, process and both visits agree | Internally coherent capture for another actor name fails request association; wrong live-process binding or invented singular evidence fails its reader. |
| Names are labels | Consistent alternative step/phase/actor labels preserve all results | A one-sided rename fails association; a fully consistent rename passes the constructed transformation/checker controls. |
| Fresh-read evidence remains independent | Own C samples match the read for each form | Coherent wrong file identity, old content, absent C identity, or changed C samples retains the reviewed distinctions. |
| Independent faults survive missing evidence | Missing B plus an unrelated wrong C identity reports both | Repeat the reviewed combined-fault controls through each form; missing evidence cannot produce a native pass. |
| Structure cannot disappear in comparison | Structural assertions run even when common values are identical | Reorder/drop/duplicate an action or change phase ownership; an equal extracted summary cannot make the case pass. |
| Observer provenance survives extraction | Sample follows the descriptor after pathname replacement/unlink | Existing real-file observer controls still reject path-stat or path-read substitutions. |

Consistent renaming here is constructed coverage. Native renamed/reordered
multi-actor coverage remains with `actor_compositions`; the new case adds no
fourth native run for renaming. Replacing a transformed request/capture with
another form must fail the form-specific admission/structure checks before
the cross-form reader can silently treat it as the intended execution.

## Public surfaces and implementation sequence

1. Develop three-form passing captures, transformation checks and rejected
   controls against the current three action objects. Read the ordinary and
   actor ownership fields before extracting a comparison. Keep observations
   distinct from interpretation and withheld results.
2. Extend the existing checker and shell case with separately retained captures
   and samples for emitted, flat and actor forms. Keep the original six
   refusal derivatives tied to emitted bytes; do not multiply them per form.
   Preserve the selected-app acquisition boundary and the controller's exact
   preparation-to-client test.
3. Move the constant to the specified two-phase shape. Update emitter unit
   assertions and any fixture/extraction assumptions about `probe_plan`.
   Change the probes surface's `document.member` from `["probe_plan", 0]` to
   `["phases", 0, "actions", 0]`; the read-hosts fragment itself stays the same.
4. Update the authored [request surface](contract/10-request.surface.md),
   [probes surface](contract/12-probes.surface.md), suite account and catalog
   descriptions. Explain the two collection boundaries beside the emitted
   rendering, with the same native-result and cause qualifications. Review
   [DEPENDENCIES.md](DEPENDENCIES.md#files-used-by-the-emitted-example) for
   continued agreement. CLI syntax and lesson publication are unchanged.
5. Regenerate with `tests/lib/python.sh docs/generate_contract_stamps.py` and
   review every changed surface, public snapshot and identity stamp. Use the
   generator owners for shared guide copies/staging if affected. Do not edit
   generated files, change record shapes or update a shape golden merely to
   accommodate a new example container.
6. Build one signed candidate, execute the selection below, inspect raw
   observations and reports, and record compact acceptance. Actual production
   modularization is subsequent work measured against these assertions.

The constant is a build-identity input. Its new content and stamped rendering
need a fresh signed build even though the native implementations are unchanged.
Document citations and source-list checks establish mechanical agreement;
the three submissions establish the compared native behavior on that build.

## Execution budget and verification

Extend the existing canonical cases rather than adding a second acquisition
case: `witness_contract/example_round_trip` for the three live forms and
`witness_contract/example_round_trip_controls` for the constructed controls.
Keep their current catalog equipment/default choices unless their requirements
actually change; all added native passages need only the same signed app.

The live case's complete invocation budget is twelve CLI calls: one
`--version`, two `example` emissions, three workload `run` submissions and the
existing six refusal `run` submissions. This is two additional native workload
submissions over the current case. The existing companion cases have their
own invocations and are not included in this count. Samples launch no app.

Offline control development can run as needed through the dispatcher. Then
use one signed candidate build and one combined final selection in a fresh
`PW_TEST_OUT_DIR`, inspecting the same selection with `--list` first:

```sh
tests/run.sh --suite unit --suite integration --suite source_drift \
  --case witness_contract/example_round_trip \
  --case witness_contract/example_round_trip_controls \
  --case witness_contract/phases \
  --case witness_contract/actor_compositions \
  --case blackbox_e2e/checker_controls
```

This deliberately reruns the ordinary phase and actor composition cases on
the same signed candidate. They cross-check the established ordering,
application and association meanings beyond the example's read-only inputs.
Keep these cases whole; do not reduce them to convenient happy paths.
Preserve resource ownership and cleanup through their existing helpers.

A failed check, changed dependency, generator movement beyond the planned
surfaces or unexpected native observation is a named cause for another build
or run. Do not weaken EPERM, structural membership or observer assertions to
obtain a pass. If a new observation exposes a runtime defect, retain the
smallest counterexample and identify the responsible boundary and additional
verification before repairing it in a separately scoped change.

No wait, release or query-eligibility change is planned. Such a change requires
`witness_contract/order_barrier_mutations`. A shared admission, receiver or
runner implementation change also requires the coordinated selections in
[tests/AGENTS.md](../tests/AGENTS.md); the narrow budget is not authority to
omit those checks. Follow that file for sandbox escalation, sleep observations,
evidence applicability, retention and pruning.

## Limits and completion

The expected cross-form native results are a hypothesis to qualify on the
candidate, not existing evidence or a public equivalence promise. Ordinary
and actor execution have different setup, evidence and allowance structures;
this test compares selected observations under stable sampled conditions.

The following remain outside its evidence:

- Two allow answers remain interchangeable if their operands/association
  records stay coherent. The relation axes are still correlated in this
  workload; the comparison matrix owns the other constructed combinations.
- Two visits to one actor have actor-local visit numbers equal to global phase
  ordinals. This cannot distinguish those axes or demonstrate isolation,
  declaration-order independence or handoff between multiple actors. Existing
  actor composition cases retain those responsibilities.
- Read-only actions do not show that replanning notices a prior phase's file
  effect. The existing phase case supplies that distinct native observation.
- Before/after samples do not establish continuous filesystem stability or
  identify the object a query consulted. They cannot authenticate an entire
  replayed experiment whose trusted observations were also replaced.
- Shared worker code, native APIs and consumer rules can share defects.
  Independent expectations and coherent controls reduce misleading passes;
  equal results do not prove general semantic equivalence or sandbox cause.
- Dictionary-file availability across supported macOS installations remains
  the accepted local limitation. Missing prerequisites fail visibly, with no
  substituted operand or claim of broad platform verification.

Complete with the phased emitted document, exact derivative transformations,
three independently checked native captures, discriminating controls, preserved
companion-case coverage and generator agreement. Name the source/build/run,
changed public surfaces, helper maintenance and these remaining limits in the
acceptance account. Distinguish native execution from constructed sensitivity;
do not raise a support grade just because a source/check was inspected.
Inspect disposable output before ordinary pruning and retire this plan when
its implementation is accepted.
