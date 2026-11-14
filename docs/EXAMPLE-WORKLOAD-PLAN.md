# A discriminating two-step CLI example

Status: proposed; implementation has not begun. Prepared against `495ecf25`
by reading the emitter, round-trip checker, controls and existing fresh-read
records. A local file inspection found the three proposed targets readable,
with distinct descriptor identities and bounded-content prefixes. No native
PolicyWitness execution establishes the proposed workload yet.

## Intended result and boundary

Make `example` a small workload whose parts are difficult to confuse. One
end-to-end passage should distinguish more wrong associations and wrong-target
observations while leaving its material useful for future presentations.
Documentation rendering and the eventual help interface are separate work.

The current [emitter](../controller/src/example.rs) prints one read-hosts pair
under an allow-all policy. The [round-trip checker](../tests/suites/witness_contract/check_example_round_trip.py)
already joins results by step ID, checks their order and echoed operands, and
compares the observed process status with the published result. Its native
expectations are uniform: validator allow, query-first order and a successful
attempt. Another indistinguishable success would add little discrimination.

Keep the no-argument CLI and its complete-publication protocol. The build
continues to guarantee that its own `run` admits the example; emission observes
no host admission. Contents, layout and labels remain build-specific. Emission
reads no file and launches nothing. The work adds no selector, target argument,
validation mode, fixture preparation, actor form, phase, write operation or
second submission path. The separate lesson command keeps its existing purpose.

## Workload

Keep the current policy and first step. Append one paired step:

| Step | Query operation and path | Attempt action and path |
| --- | --- | --- |
| `read-hosts` | `file-read-data`, `/etc/hosts` | `open_read`, `/etc/hosts` |
| `metadata-protocols-read-services` | `file-read-metadata`, `/etc/protocols` | `read_fresh`, `/etc/services` |

The first pair has matched operations and the same submitted target; the second
has different operations and different submitted targets under the existing
[comparison definitions](CONTRACT.md#contract-steps-assessment-relations). These describe submitted
relationships, not prediction/enforcement agreement. The distinct query operands,
attempt actions and targets expose different classes of accidental reuse.
Fresh-read identity and content provide an additional native observation.

These are the initial target choices, not cross-build commitments. Confirm
their suitability on the supported machine during implementation. Observe the
union of query and attempt paths, including the query-only target. Require
readable regular files, distinct device/inode identities, and nonempty
independently observed prefixes that distinguish the intended fresh-read target
from the other two files.
Failure to establish those conditions is a prerequisite failure, not a skip or
permission to silently substitute a target. Reconsider the choice if a proposed
path or query is unsuitable; do not weaken the assertion to make it pass.

Keep `EXAMPLE_DOCUMENT` as the app-owned specimen. The live case obtains its
input from the selected app and supplies no parallel specimen. Its structural
expectations pin this workload's purpose without copying its labels or paths.
Preserving the first step also preserves the existing contract extraction of
`probe_plan[0]` in the [probes surface](contract/12-probes.surface.md).

## Independent observations and assertions

Extend the existing checker and its [suite account](../tests/suites/witness_contract/README.md#the-apps-own-example).
Keep the existing emission, identity, delivery-length, policy-digest, echo,
consumer, result-status and six refusal assertions.

1. Extend the pre-submission bounds to admit `read_fresh` and require the
   intended two-step asymmetry. Keep write-capable actions, test overrides,
   runner selection, augments and entitlement requirements outside the case.
   Derive concrete operands from the emitted request; independently require
   the two action roles and the matching/differing relationships. A collapsed
   or duplicated workload must not redefine the test's purpose into a pass.
2. Observe all three files before and after the run. For each sample, obtain
   identity and content from the same independently opened descriptor and
   close it after observing. Finish the before-run sampling before submission.
   Preserve digest, length and relevant metadata;
   add bounded-prefix digest and length for the fresh-read comparison. Use the
   documented fresh-read bound rather than introducing another capacity rule.
   The observer retains no extra raw file-content copy. The app's own bounded
   `content_hex` remains in the retained raw reply.
3. Match reply steps by submitted IDs and check order separately. Reuse the
   independent consumer for field, comparison, ordering and native-record
   consistency rules. This case owns the connection between the emitted
   request, the reply and its external observations; it adds no general reply
   interpreter or production-classifier dependency.
4. Pin the native expectations for this workload: both queries yield validator
   allow with qualifying order, and both attempts succeed. The fresh-read
   record must contain a successful open, stat, bounded read and close. Its
   open return is a descriptor, so success is nonnegative, not necessarily
   zero. Require its read count and content digest to match the independently
   observed bounded prefix, and its descriptor identity to match the intended
   target. Keep the existing before/after unchanged-target observations.
5. Preserve the distinction between consistency failures, execution unavailable,
   prerequisite unestablished and native-observation failures. Missing external
   observations cannot earn a native pass. If sampled identity/content changes,
   report that uncertainty and withhold the dependent correspondence claim;
   retain any independent failures already established. A missing reply must
   not be replaced by another execution's observations.

Sampled equality does not establish uninterrupted filesystem stability or
identify the object a native query consulted. A fresh-read match supports the
attempt's correspondence under the observed conditions. Swapping two otherwise
indistinguishable native allow answers may still be invisible. An allowed/denied
contrast is later work, not a completion requirement here.

## Controls that establish the added discrimination

Extend [the existing offline controls](../tests/suites/witness_contract/example_round_trip_controls.py)
with a coherent two-step passing capture and independently specified faults.
Keep relevant existing controls and their exact diagnostic/classification sets.

| Alteration | Required distinction |
| --- | --- |
| Reorder complete reply records | Order fails while ID-based checks preserve their own results. |
| Duplicate or drop a record | The missing/duplicated submitted association cannot pass. |
| Exchange query or attempt records while preserving step IDs | Submitted operand/action checks identify the wrong association. |
| Report the query operand as the fresh-read attempt operand, keeping the emission unchanged | The submitted-operand check fails even if the operation succeeds. |
| Keep correct echoes but supply a coherent fresh-read identity and content from another observed file | External correspondence fails even when existing reply readers accept the internal record. |
| Change only fresh-read identity, or only content, coherently | Each independent observation has its own discriminating assertion. |
| Remove a prerequisite, or combine an association fault with another fault | Missing evidence earns no native credit; independent failures remain visible. |

For a coherent wrong-file control, update all dependent record fields and
captures needed to preserve internal consistency. Require the existing consumer
to accept it, then require the intended external assertion to reject it. An
unrelated malformed-record rejection does not establish that distinction.
Constructed controls establish checker sensitivity, not occurrence of a native
producer defect. Demonstrate which faults the former single-step/uniform checks
could not distinguish, without keeping a second implementation of that checker.

## Implementation and public account

Change the constant, the checker, its constructed controls and suite account.
Retain the exact preparation-to-client assertion in
[run_flow.rs](../controller/src/run_flow.rs); its guarantee ends at the controlled
client boundary. Signed-app delivery length remains a count, not exact-byte
transport or receipt evidence. The shell passage should need no additional
native invocations: both steps run within its existing ordinary submission.

Regenerate the contract through [its owning entry point](generate_contract_stamps.py),
review the extracted example and every affected surface, including shared
dependencies, and update support descriptions to their actual assertion scope.
The constant is an identity input and stamped example content; unchanged wire
shape does not imply an unchanged public snapshot. Keep the read-hosts fragment
and its open-boundary explanation accurate. Do not hand-edit generated copies.

Carry the pending wording clarification with this controller source change:
the example rule should say that exit 0 supplies the complete document and the
build guarantees its own `run` admits it, while emission performs no admission.
Align the CLI notes and their README copy. For lesson, state that the typo input
carries a deliberately unknown policy field and successful publication reports
neither admission nor an effect. Preserve the two distinct promises. Any proposed
change to those meanings needs a maintainer decision rather than an editorial
reinterpretation. Unicode contract wording and the operand-capacity probe remain
deferred and outside this work.

## Execution, verification and completion

Use one checkout. Begin with source review and bounded target inspection, then
develop the checker controls before the candidate build. Prefer one signed
candidate build and one combined final dispatcher selection. A failed check or
newly changed dependency can justify another run; repeated passing runs and
additional worktrees are not acceptance requirements. Commit work as needed;
leave release preparation and publication to their own task.

Inspect the selected cases with `--list`. After the candidate build, select
`unit`, `integration` and `source_drift`, plus
`witness_contract/example_round_trip`,
`witness_contract/example_round_trip_controls` and
`blackbox_e2e/checker_controls`, through `tests/run.sh`. Use a fresh output
directory and the [test guidance](../tests/AGENTS.md) for equipment, applicability,
sleep observations and cleanup. An early offline-control run can precede the
build if it resolves a checker uncertainty. Expand verification if shared
readers or runtime boundaries actually change. The ordering mutation case is
required if wait, release or eligibility changes; none is planned here.

If the new observations expose a runtime defect, preserve the smallest
counterexample, trace the responsible boundary, and pause with the proposed
repair and verification impact. Do not make the example less discriminating
to accommodate a defect or silently broaden this into a runner redesign.

Complete with the emitted two-step document, reviewed native observations,
passing independent controls, generator agreement, and a compact acceptance
account naming the build, run, new distinctions and remaining blind spots.
State maintenance added and public surfaces changed. Inspect disposable evidence
before normal pruning and keep the plan available for maintainer review.
