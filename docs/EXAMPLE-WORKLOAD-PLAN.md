# A discriminating three-step CLI example

Status: accepted for implementation, which has not begun. The maintainer has
settled the [policy and operands](#policy-operands-and-native-grounding) and
accepted the [acceptance table](#acceptance-table-and-budget) with its budget.
Controls beyond that table, and builds or runs beyond that budget, need the
cause the budget names. No source, checker or build has changed.

Prepared against `495ecf25` by reading the emitter, round-trip checker,
controls and contract definitions, and by submitting candidate documents by
hand to the existing signed development app. Those submissions are recorded
under [Observed native results](#observed-native-results). They were made
outside the dispatcher on one machine and their output is not retained
evidence; they inform the choice of operands and establish no acceptance.

## Intended result and boundary

`example` is a deliberately public end-to-end test specimen: the one request
the app prints about itself, submitted unchanged by the live round-trip case.
Make it a small workload whose parts are difficult to confuse and whose query
answers depend on their operands. Documentation rendering and the eventual help
interface are separate work, and this plan does not turn the example into a
teaching sequence. Because the document is public, the account of what each
step establishes must be clear; the pairs need not demonstrate comparable
operations.

The current [emitter](../controller/src/example.rs) prints one read-hosts pair
under an allow-all policy. The [round-trip checker](../tests/suites/witness_contract/check_example_round_trip.py)
joins results by step ID, checks their order and echoed operands, and compares
the observed process status with the published result. Its native expectations
are uniform: validator allow, query-first order and a successful attempt.
Under that policy no query answer can depend on its operation or path, so a
verdict attached to the wrong query is invisible.

Keep the no-argument CLI and its complete-publication protocol. The build
continues to guarantee that its own `run` admits the example; emission observes
no host admission. Contents, layout and labels remain build-specific. Emission
reads no file and launches nothing. The work adds no selector, target argument,
validation mode, fixture preparation, actor form, phase, write operation,
teaching interface or second submission path. All steps run within one ordinary
submission. The separate lesson command keeps its existing purpose.

## Workload and what each step establishes

Three files take three roles. A is read under no specific rule. B is the one
file the policy names. C is read through a fresh descriptor.

| Step | Query | Attempt | Expected native results |
| --- | --- | --- | --- |
| 1 | `file-read-data` on A | `open_read` A | allow; open succeeds |
| 2 | `file-read-metadata` on B | `read_fresh` C | allow; open, stat, bounded read and close succeed |
| 3 | `file-read-data` on B | `open_read` B | deny; open fails with a permission-shaped errno |

The policy allows by default and denies data reads of B alone.

- **Step 1** establishes a native data-read answer about A and a witnessed
  successful open of A. Operation and submitted target match.
- **Step 2** establishes a native metadata answer about B and an independently
  witnessed read of C: descriptor identity, read count and content. The answer
  about B supplies no prediction about the read of C. The pair is deliberately
  unrelated, and its comparison records `different` and `different_submitted`.
- **Step 3** establishes a native data-read answer about B and a witnessed
  failed open of B. The record holds a deny answer and a permission-shaped
  return side by side. Neither the run nor the checker states that they agree
  or that the sandbox caused the failure; the contract's
  [cause definition](CONTRACT.md#contract-identity-definitions-cause) leaves
  that unresolved.

The query answers are no longer interchangeable across all steps. The same
operation yields allow on A and deny on B; two operations on B yield allow and
deny. A verdict attached to the wrong query now changes a pinned answer in
every pairing that involves step 3. The successful fresh read stays as the
strongest independent witness and is not converted into a failed open.

The relations are [submitted-string comparisons](CONTRACT.md#contract-steps-assessment-relations)
computed from the request. They describe submitted relationships, not
prediction/enforcement agreement, and they are not native evidence.

## Policy, operands and native grounding

### Policy and operands

```
(version 1) (allow default) (deny file-read-data (literal "/usr/share/dict/propernames") (with no-report))
```

`(with no-report)` keeps the worker's refused open out of the kernel log. No
assertion of this workload reads that log. The modifier is a property of this
policy text; it is not a promise that running the example writes no log.

| Step ID | Query operation and path | Attempt action and path |
| --- | --- | --- |
| `read-hosts` | `file-read-data`, `/etc/hosts` | `open_read`, `/etc/hosts` |
| `metadata-propernames-read-connectives` | `file-read-metadata`, `/usr/share/dict/propernames` | `read_fresh`, `/usr/share/dict/connectives` |
| `read-propernames` | `file-read-data`, `/usr/share/dict/propernames` | `open_read`, `/usr/share/dict/propernames` |

Reasons for these operands:

- The first step is unchanged, which preserves the contract extraction of
  `probe_plan[0]` in the [probes surface](contract/12-probes.surface.md) and its
  open-boundary explanation. That is a convenience, not a constraint: change
  the step if a concrete improvement warrants it.
- B has one spelling. On the inspected machine `/usr/share/dict` is on the
  sealed system volume; the submitted path, its realpath and the rule's literal
  are the same string, and the reply reports no firmlink form. The rule that
  governs B is therefore written exactly as B is submitted.
- B and C are regular, world-readable files with distinct identities and
  distinct bounded prefixes. C's prefix also differs from A's and B's.
- Sealed-volume files cannot be edited by the user, which narrows the
  before/after stability question for B and C.

Alternatives, each submitted once without the modifier (see the next section):

| Operands | Rule literal | Consequence |
| --- | --- | --- |
| `/etc/hosts`, `/etc/protocols`, `/etc/services` | `/private/etc/protocols` | Works, but the rule is spelled differently from every submitted path. |
| the same | `/etc/protocols` | The rule denies nothing: both the query and the open are allowed. |
| `/private/etc/...` for all three | `/private/etc/protocols` | Works with one spelling in the request, changes the first step, and a data-volume firmlink spelling still exists. |
| `/usr/share/dict/...` for all three | `/usr/share/dict/propernames` | Uniform single-spelling operands; changes the first step and its contract fragment. |

The last row is the alternative if uniform operands come to matter more than
keeping the read-hosts fragment.

### Observed native results

App: signed development build 1408, `development:e2a3ddf1…`, built from
`5adff9ae`; controller and runner non-test sources are unchanged from there to
`495ecf25`. Machine: Darwin 25.6.0. Each row is one by-hand `run`.

| Submission | Step 1 | Step 2 | Step 3 |
| --- | --- | --- | --- |
| Settled document | allow; `ok` | allow; `ok`, fresh read below | deny, query errno 0; `open_failed`, errno 1 |
| The same without `(with no-report)` | allow; `ok` | allow; `ok` | deny, query errno 0; `open_failed`, errno 1 |
| `/etc` operands, rule `/private/etc/protocols` | allow; `ok` | allow; `ok` | deny; `open_failed`, errno 1 |
| `/etc` operands, rule `/etc/protocols` | allow; `ok` | allow; `ok` | allow; `ok` |
| `/private/etc` operands, rule `/private/etc/protocols` | allow; `ok` | allow; `ok` | deny; `open_failed`, errno 1 |
| `/private/etc` operands, rule `/etc/protocols` | allow; `ok` | allow; `ok` | allow; `ok` |
| `/private/etc` operands, rule `/System/Volumes/Data/private/etc/protocols` | allow; `ok` | allow; `ok` | allow; `ok` |
| `/usr/share/dict` operands, rule on `propernames` | allow; `ok` | allow; `ok` | deny; `open_failed`, errno 1 |

For the settled document:

- The process exited 0 with an empty stderr; `result.exit_code` was 0 and
  `normalized_outcome` was `finished`. [`complete_execution`](../controller/src/run_flow.rs)
  selects success from the admitted `finished` outcome, independently of
  individual attempt results.
- Every step's `order` was `query_first`, including the deny.
- The fresh read returned a positive descriptor, the documented bounded read
  count, and a device, inode and content digest equal to an independent
  observation of `/usr/share/dict/connectives`.
- Step 3's comparison recorded `permission_failure` with basis
  `permission_errno`, `matched` and `same_submitted`.
- No kernel deny line named the file. Without the modifier the kernel logged
  `deny(1) file-read-data /usr/share/dict/propernames` for the worker's open.
  No log line corresponded to a query in either form; the validator queries
  with `SANDBOX_CHECK_NO_REPORT`.

One further submission attempted `access` and `read_fresh` on the denied file:
both failed with errno 1, and the fresh-read record ended at its failed open.

### Native assumptions that remain

1. **Spelling.** On this machine and OS the rule matched the resolved spelling
   for both the query and the open, and no other spelling. The planner checks
   resolution but forwards the submitted query value, and later path
   diagnostics do not establish which object a query consulted or which
   spelling governed its answer. The chosen operand avoids the question for B by
   choosing a single-spelling path; it does not answer it. A keeps a symlinked
   spelling under no specific rule.
2. **Presence across machines.** `/usr/share/dict/propernames` and
   `connectives` were inspected on one machine. Their presence, readability and
   single spelling on every supported installation is assumed. Where B is
   absent the public example still runs, but step 3 reports an unavailable
   prediction and a failed open that is not permission-shaped; the live case
   treats that as a prerequisite failure.
3. **Rule scope.** Denying data reads of B left worker startup, the other
   steps and the metadata answer for B undisturbed in every submission made.
   That rests on these few runs.
4. **Errno.** The failed open returned `EPERM`, and the native checker pins it
   exactly. The contract's permission class also admits `EACCES`; accepting the
   whole class would conceal a changed observation. An `EACCES` result is
   reported as a deviation from this workload's expectation. It is not thereby
   a contract violation or evidence of a sandbox cause.
5. **Admission of the constant.** The existing app's `run` admitted the settled
   document carrying its identity. The build-time guarantee for the new
   constant is established only by the candidate build and its tests.

## Independent observations and assertions

Extend the existing checker and its [suite account](../tests/suites/witness_contract/README.md#the-apps-own-example).
Keep the existing emission, identity, delivery-length, policy-digest, echo,
consumer, result-status and six refusal assertions. The live case obtains its
input from the selected app and supplies no parallel specimen.

1. **Bounds and roles.** Admit `read_fresh` among read-only actions. Derive
   concrete operands from the emitted request, and independently require the
   three roles and their relationships: a matched open of one target; a
   metadata query on a second target paired with a fresh read of a third; a
   matched data-read open of that second target. The roles are identified by
   these relationships, not by copied labels or paths. A collapsed, duplicated
   or reordered workload must not redefine the test's purpose into a pass. The
   checker does not parse the policy source to decide which step is denied.
2. **External observations.** Observe the union of query and attempt paths
   before and after the run, including B. For each sample, obtain identity and
   content from the same independently opened descriptor and close it after
   observing. Finish the before-run sampling before submission. Preserve
   digest, length and relevant metadata; add a bounded-prefix digest and length
   using the documented fresh-read bound. The observer retains no extra raw
   content; the app's bounded `content_hex` remains in the retained raw reply.
3. **Prerequisites.** Require readable regular files, distinct device/inode
   identities, and nonempty prefixes that distinguish C from A and B. B must be
   readable by the test user: otherwise step 3's failed open is uninformative.
   A missing condition is a prerequisite failure, not a skip or permission to
   substitute a target.
4. **Association.** Match reply steps by submitted IDs and check order
   separately. Reuse the independent consumer for field, comparison, ordering
   and native-record consistency rules. This case owns the connection between
   the emitted request, the reply and its external observations; it adds no
   general reply interpreter or production-classifier dependency.
5. **Native expectations, each its own assertion.**
   - The observed process status is 0, read from the capture and kept apart
     from the envelope's `result.exit_code`.
   - The reply's `normalized_outcome` is `finished`.
   - Steps 1 and 2: validator allow with native return 0.
   - Step 3: validator deny with its native return and a query errno of 0.
   - Every qualifying prediction has `query_first` order.
   - Steps 1 and 2: attempt outcome `ok`.
   - Step 2: a successful open, stat, bounded read and close. The open return
     is a descriptor, so success is nonnegative, not zero. Read count and
     content digest equal the independently observed prefix of C, and the
     descriptor identity equals C's.
   - Step 3: a completed worker result with outcome `open_failed` and attempt
     errno exactly `EPERM`. The attempt errno and the query errno are separate
     assertions. Another permission-class errno fails this assertion as a
     native-observation deviation and leaves the consumer's reading of the
     record alone.
   - Targets are unchanged between the two external samples.
6. **No inferred relationship.** No assertion compares step 3's answer with its
   attempt, and none reads the failure as caused by the policy. The
   `permission_failure` observation class stays with the consumer's rules.
7. **Classification.** Preserve the distinction between consistency failures,
   execution unavailable, prerequisite unestablished and native-observation
   failures. Missing external observations cannot earn a native pass. If
   sampled identity or content changes, report that uncertainty and withhold
   the dependent correspondence claim; retain independent failures already
   established. A missing reply must not be replaced by another execution's
   observations.

## Controls that establish the added discrimination

Extend [the existing offline controls](../tests/suites/witness_contract/example_round_trip_controls.py)
with a coherent three-step passing capture and independently specified faults.
Keep relevant existing controls and their exact diagnostic/classification sets.

| Alteration | Required distinction |
| --- | --- |
| Reorder complete reply records | Order fails while ID-based checks keep their own results. |
| Duplicate or drop a record | The missing or duplicated submitted association cannot pass. |
| Exchange query or attempt records while preserving step IDs | Submitted operand/action checks identify the wrong association. |
| Exchange the allow and deny answers between steps 2 and 3, keeping echoes coherent | Each step's own prediction assertion fails; the consumer accepts the record. |
| Give step 1 the deny answer and step 3 the allow answer | The same, across the same-operation pair. |
| Step 3: deny answer with a successful attempt | Only the attempt assertion fails. |
| Step 3: allow answer with the `EPERM` failure | Only the prediction assertion fails. |
| Step 3: failed open with `EACCES`, comparison coherent | Only the attempt errno assertion fails; the consumer accepts the permission-shaped record. |
| Step 3: failed open with a non-permission errno, comparison coherent | The attempt errno assertion fails; no permission-shaped credit. |
| Step 3: deny outcome with a nonzero query errno, or an error outcome | The query assertion fails apart from the attempt's. |
| Observed process status nonzero with an envelope reporting 0, and the reverse | The observed-status assertion and the reported-status comparison stay separate. |
| Correct echoes with a coherent fresh-read identity and content from another observed file | External correspondence fails although reply readers accept the record. |
| Change only fresh-read identity, or only content, coherently | Each observation has its own discriminating assertion. |
| Remove a prerequisite, including B's readability | Missing evidence earns no native credit. |
| Combine an association fault with a native fault | Independent failures remain visible. |

For a coherent control, update all dependent record fields and captures needed
to preserve internal consistency. Require the existing consumer to accept it,
then require the intended assertion to reject it. An unrelated
malformed-record rejection does not establish the distinction. The paired
step-3 controls show that the checker evaluates the answer and the attempt
independently and passes neither on their agreement. Constructed controls
establish checker sensitivity, not occurrence of a native producer defect.
Demonstrate which faults the single-step uniform checks could not distinguish,
without keeping a second implementation of that checker.

## Acceptance table and budget

The table is the agreed scope of fixture and control work and of native
acceptance. Each row connects one added distinction to an expectation authored
apart from the checker's output, the constructed capture that passes, the
control that must be rejected, and the case that runs it. Cases: **C** is
`witness_contract/example_round_trip_controls` (offline), **L** is
`witness_contract/example_round_trip` (live, signed app).

| Added distinction | Independent expectation | Passing input | Rejected control | Case |
| --- | --- | --- | --- | --- |
| The workload has three roles | Role relationships stated in the checker's bounds, without labels or paths | Three-step constructed document | Collapsed step 3 target; duplicated step; missing role | C; L refuses to submit outside bounds |
| A query answer depends on its path | Allow for A and deny for B under one operation | Three-step capture | Answers exchanged between steps 1 and 3 | C, L |
| A query answer depends on its operation | Allow and deny for B under two operations | The same | Answers exchanged between steps 2 and 3 | C, L |
| The deny answer is its own observation | Validator deny, its native return, query errno 0 | The same | Nonzero query errno; error outcome | C, L |
| The failed open is its own observation | `open_failed` with errno exactly `EPERM` | The same | `EACCES`; a non-permission errno; `ok` | C, L |
| Answer and attempt are evaluated apart | Each control's exact identifier set, authored in the control | The same | Deny with `ok`; allow with `EPERM` | C |
| A finished run holds a failed attempt | Captured process status 0 and `finished`, apart from `result.exit_code` | The same | Captured status and envelope disagree, each way | C, L |
| The fresh read is of C: identity | Device and inode from the checker's own descriptor | Capture plus three target samples | Coherent identity of another sampled file | C, L |
| The fresh read is of C: content | Prefix digest and count from the same descriptor | The same | Coherent content of another file; count alone | C, L |
| Query-only target B is observed | B sampled readable before and after | The same | B's sample removed or unreadable | C, L |
| Three records keep their association | Submitted IDs, order and echoes from the emitted document | The same | Reorder; duplicate; drop; exchange with IDs preserved | C |

Reused without new assertions: emission, passage, admission, identity,
reported-status and the six refusal groups with their controls; the shared
consumer, including its fresh-read record rules; the emitter's unit tests and
the preparation-to-client test in `unit`; the CLI cases in `integration`; and
the example extraction controls in `source_drift`. Their expected sets are
re-established against the three-step passing capture.
`blackbox_e2e/checker_controls` is selected because the case shares the
consumer and the authored run; no change to it is planned.

Added: no fixture file. The passing capture is built in the controls from the
authored run under `tests/fixtures/blackbox_e2e/checker/current/`, whose allowed
and denied file steps are read as steps 1 and 3 in the way its first step is
read today, with one fresh-read step and three target samples authored in the
control. If the fresh-read step cannot be built coherently there, add one
authored fixture and record it in the fixture catalog.

Budget: offline control runs as needed while the checker changes; one signed
candidate build; one combined dispatcher selection as listed under
[Execution, verification and completion](#execution-verification-and-completion).
A further build or run needs a named cause: a failed check, a changed shared
dependency, regeneration that moves something beyond the example and its
stamps, or native results that differ from those recorded above. The default
battery is outside this budget unless a shared reader or runtime boundary
changes.

## Remaining blind spots

- **Interchangeable allow answers.** Steps 1 and 2 both expect allow.
  Exchanging those two native answers remains invisible.
- **Correlated relation axes.** The live workload exercises `matched` with
  `same_submitted` twice and `different` with `different_submitted` once. A
  producer deriving one relation from the other would pass here. The
  [scenario matrix](../tests/fixtures/comparison/matrix.json) holds constructed
  rows for `different` with `same_submitted` and `matched` with
  `different_submitted`; that validation is constructed, not live, and the
  public example is not a relation matrix.
- **Consulted object.** Sampled equality does not establish uninterrupted
  filesystem stability or identify the object a native query consulted. Echoed
  query operands are the admitted request values.
- **Cause.** The deny answer and the `EPERM` return coexist in one record. The
  workload supplies no evidence separating a sandbox cause from another
  permission cause beyond the test user's own successful read of B.
- **One policy shape.** One literal data-read rule on a single-spelling path
  says nothing about other rule forms, symlinked or firmlinked operands, or
  other operations.
- **Failed fresh read.** The workload observes no failed fresh-descriptor read.

## Implementation and public account

Change the constant, the checker, its constructed controls and suite account.
Retain the exact preparation-to-client assertion in
[run_flow.rs](../controller/src/run_flow.rs); its guarantee ends at the controlled
client boundary. Signed-app delivery length remains a count, not exact-byte
transport or receipt evidence. The shell passage needs no additional native
invocations.

Regenerate the contract through [its owning entry point](generate_contract_stamps.py),
review the extracted example and every affected surface, including shared
dependencies, and update support descriptions to their actual assertion scope.
The constant is an identity input and stamped example content; the policy text
changes, so the public snapshot and build identity move. Keep the read-hosts
fragment and its open-boundary explanation accurate. Do not hand-edit generated
copies.

Author a short account beside the stamped rendering of the
[emitted example](CONTRACT.md#contract-request-specimen-example), in the
request surface. A few sentences are enough, and they must hold for a reader
who has not seen the checker:

- what each step establishes, as stated under
  [Workload and what each step establishes](#workload-and-what-each-step-establishes),
  including that the second step's answer concerns a file its attempt does not
  read;
- that a finished run exiting 0 contains a failed attempt;
- that the deny answer and the failed open are separate observations, with no
  agreement or cause stated;
- that the described results are observations under stated conditions: the
  three files exist and are readable, on the build and machine that produced
  them.

The account makes no new promise. Paths, labels, step count and order, the
policy text with its `(with no-report)` modifier, the pinned errno and every
native result stay build-specific; the durable commitments remain that exit 0
supplies the complete document and that the same build's `run` admits it. Add
no role field, expected-results document, rendering interface or catalog of
uses. Keep the document self-describing instead: step IDs name each half's
operation and object and never an expected answer, and the policy's one
specific rule spells B as the steps submit it. New assertions keep a stable
identifier and a one-sentence description keyed by role, so `report.json` and
the retained captures can be read without the checker.

The [probes surface](contract/12-probes.surface.md) support text calls the
extracted read-hosts fragment "the teaching step". Replace that phrase with a
literal description of the fragment; the example is a public test specimen.

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

If the native results on the candidate build differ from those observed above,
stop and reconsider the operands or policy; do not weaken an assertion to make
it pass. If the new observations expose a runtime defect, preserve the smallest
counterexample, trace the responsible boundary, and pause with the proposed
repair and verification impact. Do not make the example less discriminating
to accommodate a defect or silently broaden this into a runner redesign.

Complete with the emitted three-step document, reviewed native observations,
passing independent controls, generator agreement, and a compact acceptance
account naming the build, run, new distinctions and remaining blind spots.
State maintenance added and public surfaces changed. Inspect disposable evidence
before normal pruning and keep the plan available for maintainer review.
