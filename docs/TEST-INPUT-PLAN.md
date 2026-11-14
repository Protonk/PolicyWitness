# Transform lesson into a controlled-input test seam

Status: design direction accepted; implementation has not begun. The first
implementation task is the acceptance checkpoint below, before expanding
fixtures or building a candidate. This plan is based on source and check
inspection at `55a7c35b`; no native execution establishes the proposed workload.

## Purpose and boundary

Replace `lesson` with a developer command for investigating the signed app:
does this build preserve submitted intent, report refusals precisely, and
return observations belonging to the resource and execution supplied by the
caller? Completion is tied to the three uses below, not to adding selectors or
publishing a larger collection of examples.

The [example workload plan](EXAMPLE-WORKLOAD-PLAN.md) exercises resources and
operations selected by the build. This seam supplies a fixed read workload
whose resources and conditions the harness controls. Both use ordinary `run`;
neither gains another execution or admission path.

Remove creation from the emitted workload. The harness owns fixture creation,
content changes, observations and cleanup. The app performs a fresh read.
Existing creation operations and unrelated grammar tests retain their own
purposes. This work introduces no native action, actor form, custom result
format, automatic fixture preparation or general lesson catalog.

## Existing implementation and dependencies

The [current emitter](../controller/src/lesson.rs) embeds
[two input bodies](../controller/src/lessons/README.md), inserts the compiled
identity and patches the caller's target into two fixed positions. Publication
does not inspect the filesystem or invoke admission. The
[public rule](CONTRACT.md#contract-request-specimen-emit_lesson) promises complete
publication, not admission or execution. Both JSON resources are explicit
inputs of [the build identity](build_contract.py).

The [request corpus](../tests/fixtures/request_contract/examples.json) references
those bodies and owns the expected refusals. Its
[Python loader](../tests/lib/request_examples.py) and
[Swift loader](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift)
replace markers recursively. The live
[accepted-input case](../tests/suites/runner_outcome_bad_request/contract.py)
also submits actual emitted bytes and retains a substitution control. Its
accepted branch observes file presence and selected result fields; it is not
the fuller independent read checker proposed here.

The [guide workflow](../tests/suites/witness_contract/opt_in/guide_workflows.py)
already validates replies and observes files with metadata and content, but
its native passage is bundled with external-runner installation. The
[suite account](../tests/suites/witness_contract/README.md#guide-workflows)
describes its equipment and ownership requirements. The new default seam
must not acquire those requirements merely to reuse its observations.

## Command and input ownership

The proposed interface is:

```text
policy-witness test-input read --target PATH
policy-witness test-input unknown-field --target PATH
```

Replace the `lesson` dispatch rather than retaining an alias. Document this
as a developer interface tied to the emitting build, separately from ordinary
usage. Remove the lesson entry from ordinary help; a malformed test-input
invocation can explain its own usage. Developer status does not exempt the
command from identity accounting, publication checks or an accurate contract
account. It adds no cross-build stability promise for selectors or documents.

Both selectors emit one ordinary request object with the binary's contract.
The read input has an allow-default policy and one step pairing a
file-read-data path query with a file/read_fresh attempt on the supplied target.
The unknown-field input differs only by one unknown policy member. Initially
retain `capture_compiled_profiel: true`, with the independently authored
unknown-field expectation at that member. Removing that member is the repair;
renaming it to the real capture option would introduce another prerequisite.
Set the final specimen and step labels at the acceptance checkpoint.

Preserve the existing target discipline: one nonempty absolute UTF-8 path
without NUL, inserted verbatim. Emission does not normalize or inspect the
target, prepare a directory, supply fixture bytes or decide host capacities.
Exit zero means a complete serialized document, one framing newline and a
successful flush. Usage, target, identity, rendering and output failures return
exit two; discard stdout even if it contains complete JSON. Stderr remains
best effort. Neither selector makes an unconditional admission promise.

Keep app-owned inputs and independently authored expectations separate. Choose
one explicit substitution rule and make the emitter and test loaders agree
on it. Validate the expected input structure before substitution so malformed
embedded data fails publication rather than panicking or silently leaving a
marker. Test malformed template and target-binding controls in-process; no
extra signed fixture build is needed for them. Do not grow a generic template
language or a second request interpreter.

## Goals and acceptance

### Qualify the signed package through its actual published input

Obtain the request from the selected app and submit its bytes unchanged to
`run`. Repeat publication under the same arguments to check deterministic
materialization. The harness first verifies the intended read-only structure,
identity and owned target; unexpected write-capable work or another target
must stop submission, not redefine the experiment.

Acceptance requires separate observations for publication, admission, reply
identity, association, process status and native results. Compare the captured
process status with the independently expected status and the published one.
Require the submitted specimen/step identifiers and operands to be preserved,
and use the existing independent consumer for general reply semantics. Do not
copy that consumer into the seam checker.

For accepted reads, require finished completion, a qualifying native allow
answer and query-first order. Check the fresh open, stat, bounded read and
close, including the descriptor's nonnegative open return. Match identity,
read count and content against independent observations of the intended file.
The documented fresh-read capacity determines the observed prefix; the emitter
does not supply expected bytes or hashes.

For the refused input, independently require the host's unknown-field code and
path, captured refusal status, consistent published refusal and the reported
absence of worker, validator and step observations. Preserve the refused
request, remove exactly the unknown member into a new document, and require
structural equality with the accepted input at the same target. Submit the
repair and establish its successful read independently.

A read leaves no reliable file-effect marker. Unchanged bytes and absent
execution records do not independently prove no execution occurred. This seam
credits the reported refusal and its records; stronger non-execution evidence
remains with the existing execution-boundary controls. Do not import the
instrumented multi-build experiment merely to add that claim.

### Expose wrong-target and stale-data behavior

Prepare ordinary regular files in a private harness-owned directory. Retain
their contents and metadata as experiment inputs, not as replacement goldens.
Require distinguishable payloads within the recorded prefix. Observe identity
and content through the same independently opened descriptor and close all
fixture descriptors before submission.

The proposed native sequence is:

| Passage | Harness preparation | Independent expectation |
| --- | --- | --- |
| Initial read of A | Create A with known content | The returned identity and bounded bytes belong to A. |
| Read A again | Change its content in place, verify retained identity, reuse the exact emitted request | The next reply carries the new bytes, not the earlier observation. |
| Read B | Prepare a different inode with content identical to current A; emit for B | The reply names B's identity even though the byte comparison alone cannot distinguish it. |
| Refused input for B | Leave B unchanged and emit the unknown-field form | The host reports the specified refusal without execution records. |
| Repaired input for B | Delete exactly the unknown member in a saved copy | The repaired document is admitted and the read corresponds to B. |

Make the controlled content change between runs, never concurrently with a
read. Verify the identity-retention premise rather than assuming an in-place
write preserved it. Sample before and after every native passage. Identity or
content instability withholds the dependent correspondence claim and cannot
earn a native pass; keep other established failures visible. Access-time
changes alone are not evidence that file content changed.

The successful sequence establishes these particular controlled transitions.
It does not identify the object consulted by the query, establish continuous
filesystem stability, attribute a failure to the sandbox or declare prediction
and enforcement agreement.

### Qualify changes to readers and assertions

The accepted native capture must pass the independent consumer and the seam's
external checks. Constructed passing and rejected captures then qualify the
checker without additional native executions for each fault:

| Control | Required distinction |
| --- | --- |
| Correct echoes, but coherent identity from the other same-content file | The consumer accepts internal structure; external identity correspondence fails. |
| Correct target and identity, but coherent content from the earlier read of A | The consumer accepts internal structure; the current-content assertion fails. |
| Correct observations with a wrong echoed target or step | Submitted association fails independently of native correspondence. |
| Accepted publication substituted for the refused selector | The independently specified refusal expectation rejects the accepted run. |
| Nonzero captured status beside a published successful result | Observed process status fails even when the envelope still claims success. |
| Missing prerequisite or combined independent faults | Missing evidence receives no native credit; existing failures are not hidden. |

Keep the current substitution control's distinction between the process status
and the envelope's exit code. Its new passing and rejected observations must
follow the read workload; file creation can no longer qualify a rejection.
Adapt or replace that control once, rather than keeping a second native copy.

Each control specifies the intended diagnostic and classification. An
unrelated malformed-record rejection cannot establish external correspondence.
Keep observation records, captures and assertion results in existing harness
artifacts. Neither native captures nor the emitted body become permanent
cross-build goldens; replay preserves their source/build identity and labels
constructed alterations explicitly.

## Migration and public account

Replace the emitter, dispatch and relevant CLI integration tests together.
Update resource ownership, explicit build-identity inputs and their mutation
checks. Preserve grammar and direct-XPC coverage: corpus rows that still need
a creation effect can own their existing bodies independently of the new
read seam. Do not force every request-corpus case through the new command.
If loader changes are needed, update and verify their Python and Swift readers
together, retaining independently authored expected diagnostics.

Move end-user workflows onto `example` and `run`. The quick start obtains the
public example. Refusal and capture exercises modify saved requests explicitly
and keep the original inputs. Review downstream path-observation explanations,
saved-result names and external-runner examples that currently assume an empty
created file. The ordinary guide and usage must require neither `lesson` nor
`test-input`; developer material such as
[REQUEST-GRAMMAR.md](REQUEST-GRAMMAR.md) can use the new seam.

Execute the changed guide passages as written. Reuse the existing extraction
and guard controls; select or factor their ordinary workflow without silently
crediting unexecuted external-runner behavior. If the migration changes the
external-runner commands themselves, include the owning workflow with its
actual equipment and cleanup obligations, or pause with that verification
cost before implementation.

Retire the old lesson rule and document the new build-bound developer
interface at its proper owner. Review whether it needs a replacement stamped
rule; hiding it from ordinary usage is not a way to retain stale promises.
Regenerate affected contract snapshots, support descriptions and staged guide
through their owners, preserving release history. No support grade rises from
the rename or source inspection alone.

Coordinate with the example plan: both touch CLI notes, guide workflows,
publication rules and build identity. Use its current result as the basis for
the guide migration; do not overwrite ongoing work or make example acquire
targets, selectors or test-specific output. A shared final build is useful
only if both changes are ready and their validation scopes are explicit.

## Acceptance checkpoint and execution budget

Before implementation, present a compact table for maintainer agreement:

- The exact input pair, substitution rule and independently owned expectations.
- Each native passage, fixture preparation and external observation above.
- Each checker control, expected diagnostic/classification and existing
  coverage reused; identify any control needing a new fixture.
- The canonical owning cases, their default membership, and any native
  invocations removed or added. Choose strengthening the existing subcase or
  extracting one small default case, without duplicate native coverage.
- The concrete guide replacements, developer/public contract placement and
  selected checks, including any equipment needed by changed guide workflows.

This checkpoint settles the reviewable acceptance design, not permission for
routine implementation details. Then implement in one checkout, develop
offline controls before the signed candidate, and prefer one candidate build
with one combined final dispatcher selection. The proposed read/refusal
sequence uses five ordinary run submissions; publication and constructed
controls are accounted for separately. Existing corpus and guide checks have
their own costs and must be included in the agreed selection.

Start test selection from `unit`, `integration` and `source_drift`, the
new or adapted seam cases, `runner_outcome_bad_request/accepted_input_contract`
and `blackbox_e2e/checker_controls`. Include `runner_unit` and
`runner_c_worker_harness` if their corpus inputs or loaders change, following
[test guidance](../tests/AGENTS.md). Include the affected guide workflow and
example cases when their dependencies change. Inspect the actual selection
with `--list`. Do not select the entire bad-request suite accidentally: its
opt-in same-shape experiment builds separate signed variants.

No ordering or admission implementation change is planned. If one becomes
necessary, apply the corresponding coordinated checks, including the ordering
mutation control when its rule applies. A newly exposed runtime defect earns
a small preserved counterexample and a pause with the proposed repair and
verification impact; do not weaken an expectation to hide it. Repeat testing
when a changed dependency, failure or unresolved observation warrants it.

Completion requires evidence for all three goals, independently effective
controls, the migrated user workflows and accurate publication/contract
accounts. Record source/build/run identities, remaining blind spots, public
changes and maintenance added or removed in a compact acceptance account.
Inspect disposable evidence and use normal pruning. Keep this plan available
for maintainer review; no automatic retirement rule is introduced.
