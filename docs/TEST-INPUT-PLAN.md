# Transform lesson into a controlled-input test seam

Status: proposed revision; no implementation has begun. Land and accept the
[example workload](EXAMPLE-WORKLOAD-PLAN.md) first. Then review concrete guide
replacements and this seam's acceptance table before removing `lesson` or
building this plan's candidate. Source inspection is against `5415dc14`;
the proposed native experiments have not been executed.

## Purpose and what needs the command

Replace `lesson` with one build-bound developer input publisher:

```text
policy-witness test-input read --target PATH
```

The app publishes a fixed read workload; the harness controls its resources,
conditions and expected results. Execution uses ordinary `run`. The emitted
workload contains no creation action. Fixture creation, modification and
cleanup belong to the harness; unrelated creation tests keep their purpose.

| Goal | What the command contributes | What the harness establishes |
| --- | --- | --- |
| Qualify publication and target binding in the signed package | Actual build-owned bytes containing the compiled identity and caller's target | Publication, submitted-byte retention, admission and correspondence of the resulting observations. |
| Distinguish wrong targets, changed content and target-dependent query answers | A convenient starting request; this goal also works with a harness-authored request | Controlled files and policy changes, independently observed inputs and pinned native results. |
| Qualify readers and assertions against misleading captures | A source of ordinary native captures; this goal does not require an emitter | Independently authored expectations, coherent rejected controls and exact diagnostics. |

The command's additional value over `example` is target binding in the shipped
publisher. Do not credit it with the independent experiments' conclusions or
turn their expectations into publication promises. There is no second selector,
answer key, new execution path, native action or general lesson catalog.

## Sequence and guide migration gate

### Land example and reuse its observer

Complete the example plan and record its accepted commit/build before starting
this implementation. Its build budget is separate; this plan does not claim a
shared candidate build. Rebase the proposed checks onto the actual landed
observer, fresh-read assertions and controls.

Reuse the following mechanisms instead of writing another implementation:

| Mechanism from example | Treatment here |
| --- | --- |
| Same-descriptor sampling of identity, full digest/length and bounded-prefix digest/length | Reuse the observer for harness-owned A and B. |
| Successful fresh-read identity, prefix and count correspondence | Reuse the scalar comparisons against independently supplied expected samples. |
| Internal fresh-read and reply semantics | Continue using the existing independent consumer. |
| Coherent wrong-identity/content controls and missing-observation handling | Reuse their helper machinery and existing coverage; add only controls specific to this experiment. |
| Workload roles, policy expectations, target prerequisites and passage association | Keep separately authored for this seam. |

If these mechanisms remain private to the
[example checker](../tests/suites/witness_contract/check_example_round_trip.py),
extract the small observer/comparison helpers for both callers. Preserve
example's behavior and rerun its live case and controls when their dependencies
change. Do not create a universal workload checker or share expectations with
the product. The acceptance table must name the landed helpers and cases
reused, rather than describe them as work still to be invented.

### Design the guide before removing lesson

The guide migration is a separate review stage with concrete passages, not a
rename bundled into seam implementation. Keep `lesson` working throughout
that review. Using example output in a guide can explain an existing public
artifact, but does not make a teaching sequence an obligation of the example
producer. Do not assume it is the right first teaching input.

The reviewer must choose between explaining the real landed example, including
its denied attempt and unrelated pair, and authoring a separate ordinary
request using public interfaces. Neither choice may require `test-input` or
change example's workload to satisfy a lesson. Existing creation-based lessons
can remain ordinary requests if that is the clearer guide design; creation is
removed from this developer seam, not from the instrument.

Prepare the following replacements together:

| Current dependency | Required design and acceptance |
| --- | --- |
| Quick start's `lesson create`, saved request/result and empty created file | A runnable first passage, its intended reader conclusions and independent observations; no assumption that the new example creates a file or that every step succeeds. |
| Typo, missing-nonce and positive-capture exercise | Explicit edits of saved requests, original inputs retained, exact refusal and capture expectations preserved or deliberately replaced. |
| Helper, provenance and path-reading commands using the saved create files | Consistent filenames and selectors, and explanations supported by the replacement's actual records. An absent-to-created path explanation cannot describe a read-only run. |
| External-runner workflow copying the create request and retargeting its first step | A valid replacement request and independent observation, with the same installation and cleanup ownership accounted for. |
| Guide harness fence selectors and preparation guards | Match the real new command text and validate failed preparation, preserved earlier results and the new native observations. |

Inventory the references in [the guide](PolicyWitness.md) and in
[its workflow case](../tests/suites/witness_contract/opt_in/guide_workflows.py).
That case currently finds the quick-start fence by the literal
`"$PW" lesson create`, assumes creation in subsequent passages and executes
the external-runner lifecycle. File renaming alone does not migrate it.

Budget one full `witness_contract/guide_workflows` execution in this plan's final
selection. Keep the case whole for this change. As documented by its
[owner](../tests/suites/witness_contract/README.md#guide-workflows), it requires
a signed selected app, matching Developer ID identity, a logged-in GUI session,
an empty default runner registry and no concurrent registry changes. It signs,
installs, verifies and removes an owned service. The adjacent staged guide must
match the source guide. Confirm that equipment and cleanup ownership before
implementation; lack of equipment leaves the work unverified, not skipped.

The guide design and seam acceptance table are reviewed together after example
lands. Once agreed, implement the reviewed migration and command replacement;
land the guide changes before or with removal of `lesson`, never afterwards.
If the guide design is unresolved, freeze here with lesson intact. No second
guide architecture or generic harness refactor is included in this budget.

## Command, materialization and public account

The [existing emitter](../controller/src/lesson.rs) embeds
[two bodies](../controller/src/lessons/README.md). Replace them with one read
input, using an allow-default policy and one step pairing a file-read-data
path query with file/read_fresh on the caller's target. Use specimen ID
`test-input` and step ID `read-target`; they are build-specific content.

Use positional substitution, matching the current emitter's operation:

```text
contract
probe_plan[0].sandbox_check.filter.value
probe_plan[0].attempt.target
```

Validate the expected template structure before assignment. No recursive
marker replacement runs over the supplied value. An in-process control and a
selected-app publication control must preserve a target containing the literal
text `$EFFECT`, alongside quotes, backslashes and non-ASCII text. Malformed
template controls require a rendering refusal rather than a panic or a
partially bound document; they need no extra signed fixture build.

Preserve one nonempty absolute UTF-8 target without NUL, inserted verbatim.
The publisher does not normalize or inspect it, prepare fixtures or decide
host capacity. It renders completely before output. Exit zero requires the
whole document, one framing newline and successful flush; usage, target,
identity, rendering, write and flush failures exit two. Discard stdout on
failure, even if it contains complete JSON. Stderr remains best effort.
Publication makes no unconditional admission or execution promise.

Replace lesson dispatch without an alias once the guide gate is met. List
test-input under a developer heading in the single shared CLI usage text and
its README copy. Do not maintain a hidden alternative usage account.
Replace the [lesson publication rule](CONTRACT.md#contract-request-specimen-emit_lesson)
with a stamped test-input rule covering its arguments, publication and failure
promises. Developer designation does not remove it from the contract account;
state its build-bound scope explicitly.

Remove the old embedded resources and their explicit
[build-identity inputs](build_contract.py); add the single new input and update
identity mutation checks. Preserve independently authored grammar expectations
in the [request corpus](../tests/fixtures/request_contract/examples.json).
Its old creation bodies can move back into corpus ownership. The
[Python](../tests/lib/request_examples.py) and
[Swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift) loaders may
retain recursive substitution for their existing corpus templates; they must
not claim to materialize the new publisher by that rule. Any loader of the
new body uses the positional rule. Update changed readers together.

Regenerate contract snapshots, support accounts and staged guide through their
owners. Preserve release history; neither the rename nor check inspection
raises an evidence grade. Ordinary guide workflows require only public user
interfaces; [developer material](REQUEST-GRAMMAR.md) may use test-input.

## Controlled fixtures and native passages

Create a private owned directory under `/private/tmp`, resolve its spelling,
and use the resolved absolute paths for submitted operands and policy literals.
Verify the submitted spelling equals realpath for each ordinary file. Do not
use the Desktop checkout for native targets. Retain the prepared bytes and
metadata as experiment inputs, not as replacement goldens.

Let N be the documented fresh-read bound. The exact payload recipe is:

```text
short_0 = N - 1 copies of byte 'a'
short_1 = N - 1 copies of byte 'b'
long    = short_1 followed by bytes 'c', 'd'
```

Require N greater than one. A's first update changes bytes within the returned
prefix without changing length or inode. Before the B passage, extend A in
place to the long payload and independently create B with that same payload.
Verify equal device, mode, owner, group, content and length and different
inodes. Among the fresh-read identity fields, only inode distinguishes A and B.
Do not use a hard link. Timestamp equality is not a prerequisite.

Sample through the shared same-descriptor observer before and after each
passage; close fixture descriptors before submission. Harness writes happen
only between passages. Verify retained identity after each in-place change.
Instability withholds dependent correspondence credit while preserving other
failures. This establishes sampled conditions, not continuous stability.

| Passage | Input and preparation | Independently expected result |
| --- | --- | --- |
| Initial A | Emit for A containing short_0; repeat emission to check determinism; submit unchanged bytes | Allow, successful fresh read of A, count N - 1 and short_0 bytes. |
| Updated A | Write short_1 in place; reuse the exact saved request | Same target identity, count N - 1 and new bytes. |
| B | Prepare A and B with the long payload as above; emit for B and submit unchanged | B's identity, count N and exactly the bounded prefix; file length remains N + 1. |
| Refusal | In a saved B document, inject `policy.test_input_unknown_field: true` | Host unknown-field refusal at that exact member, independently expected status and reported absence of execution records. |
| Repair | Delete precisely that member into a new file | Structural equality with the emitted B document, admission and a successful read of B. |
| Denied B | Change only the B document's policy to allow-default plus literal data-read denial of resolved B, with no-report | Native deny with query errno zero; fresh open fails with EPERM and aggregate read_failed; completed run still exits zero. |
| Allowed A under the same policy | Apply exactly that policy source to the saved A request; A still contains the long payload | Native allow, successful read of A, count N and the same prefix as B. |

The refusal and policy variants are harness-authored derivatives, never
described as unchanged app output. Retain each transformation and verify its
declared differences before submission. The synthetic member tests closed
field admission, not spelling correction.

Pin the deny's query result separately from the fresh-read failure. Require
query-first order where its prerequisites hold. Validate the failed-open
record's unavailable later operations through the existing consumer; do not
invent successful stat/read/close evidence. EPERM is a workload expectation,
not a general contract or cause claim. The new temporary-file policy has not
been observed natively yet: a different result requires investigation, not
automatic acceptance of a broader permission class. The resolved literal and
no-report modifier do not establish path-spelling behavior or log silence in
general. The two policy passages add two ordinary submissions.

These contrast query answers for one operation across A and B. They do not
identify the object consulted by a query, discriminate all equal allow
answers, establish operation-dependent answers or prove agreement or sandbox
causation. The allow-default passages alone have no query-verdict distinction.
Unchanged files and absent execution records do not independently prove that
a refused read never ran; credit the reported refusal, leaving stronger
non-execution evidence to existing execution-boundary controls.

## Capture association and independent controls

Every run starts a fresh host and worker. Updated A does not test memory
persisting in one worker. It tests whether the next passage reports current
bytes. Accidental reuse of a previous capture by the harness is a concrete
failure to discriminate; no cross-run product cache is presumed to exist.
If native stale data appears, preserve the input, independent observations and
raw capture, then trace the responsible boundary before attributing a cache.

For every passage compare observed process status, independently expected
status and published result separately. Check build identity before reading
the reply, and bind submitted IDs/operands, policy digest and capture to the
current passage. Successful reads must match independent identity, byte count
and prefix observations. Use the existing consumer for internal semantics.

| Rejected control | Required distinction and reuse |
| --- | --- |
| Coherent other-file identity with correct echoes and identical bytes | Reuse example's identity comparison and coherent-control helper; consumer accepts, external identity assertion rejects. |
| Coherent old content with current identity | Reuse example's prefix/count comparison; consumer accepts, current-content assertion rejects. |
| Previous A passage's whole run capture supplied to updated A | New passage-association control: replace the raw reply, process capture and associated request records together; keep the current experiment's independent observations and expected transition. Internal validity cannot substitute for current bytes. |
| Emitter publishes for B when invoked for A | New binding control: the actual acquisition/preflight path rejects the wrong target before run. Ignoring the supplied emitter must defeat the control and be detected. Use a recorded invocation boundary; no native run is needed. |
| Unknown-field injection omitted | The independently authored refusal oracle rejects an accepted capture; the app needs no refused-input selector. |
| Query answers exchanged across the policy contrast | Reuse example's independent query-result checks with this seam's own expectations; correct echoes cannot excuse wrong answers. |
| Nonzero captured status with a successful envelope | Reuse observed-versus-published status checks, retaining the lesson control's previously corrected distinction. |
| Missing prerequisites or combined faults | Reuse missing-observation handling and require the exact independent failures to remain visible. |

The whole-capture control includes an internally valid previous observation,
not just a spliced content field. A filename or passage-label mismatch alone
does not earn current-content coverage. Expectations and fresh external
observations live outside the replaceable run capture. Replaying that entire
trusted experiment as well is outside this freshness claim.

Constructed controls establish checker sensitivity, not native occurrence of
a product defect. Specify exact diagnostics/classifications, and require the
consumer to accept coherent controls aimed at external correspondence. Adapt
or retire the old selector-substitution control; do not keep its native
executions merely to preserve its implementation.

## Acceptance checkpoint, verification and completion

After example lands, present for maintainer review:

- The concrete guide passages and their reader conclusions, dependency map,
  harness fence changes and confirmed full-workflow equipment.
- The landed observer/comparison helpers and controls reused, with any small
  extraction needed; separately owned expectations and new controls.
- Canonical case IDs, fixture ownership and exact diagnostics, plus invocation
  accounting for the seven native passages and publication controls.
- The stamped developer rule and shared usage changes, and the migration of
  old corpus resources without losing grammar or direct-host coverage.

Do not defer the settled choices above to this checkpoint. It reviews the
guide design and concrete implementation/verification mapping. Once accepted,
implement in one checkout, develop offline controls first, then make one
signed candidate build after the already accepted example build. No overlapping
one-build budget is claimed. A failed check or changed dependency can justify
another build or run; record that cause.

The final combined selection includes `unit`, `integration`, `source_drift`,
the seam's owning cases,
`runner_outcome_bad_request/accepted_input_contract`,
`blackbox_e2e/checker_controls`, `witness_contract/example_round_trip`,
`witness_contract/example_round_trip_controls` and the full
`witness_contract/guide_workflows`. Include `runner_unit` and
`runner_c_worker_harness` when their corpus inputs or loaders change, following
[test guidance](../tests/AGENTS.md). Inspect the actual selection with `--list`;
do not select the whole bad-request suite and accidentally add its opt-in
multi-build experiment. The seven seam submissions exclude the separately
budgeted existing corpus, example and guide passages; no second native lesson
subcase is retained.

No ordering or admission implementation change is planned. Apply the relevant
coordinated checks, including ordering mutation controls, if those boundaries
change. A discovered runtime defect earns a small preserved counterexample and
a pause with proposed repair and verification impact, not weaker assertions.

Completion requires evidence for each goal at its stated owner, independently
effective controls, working migrated guide passages, removal of lesson and an
accurate stamped publication rule. Record source/build/run identities,
remaining blind spots, public changes and maintenance added or removed in a
compact acceptance account. Inspect disposable evidence before normal pruning
and keep the plan available for maintainer review.
