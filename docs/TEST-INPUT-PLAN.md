# Transform lesson into a controlled-input test seam

Status: implemented and verified after maintainer acceptance of the concrete
checkpoint below. The completion account records the signed candidate,
verification credits, corrected selection and remaining limits. Keep this plan
available for review; no release evidence or support-grade promotion is claimed.

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

### Reuse the example observer

The baseline publishes three steps in two ordinary phases and exercises flat
and single-actor derivatives as separate submissions. The controls account
records signed development build 1441, 158 `(form, id)` rows and 170 named
conditions. Its development runs are disposable, not retained release
evidence. This seam needs its own candidate build. Use the current mechanisms
below; the old flat-example baseline and identifier prefixes no longer apply.

Reuse the following mechanisms instead of writing another implementation:

| Landed mechanism and owner | Treatment here |
| --- | --- |
| `check_example_round_trip.observe_target(target, opener=...)`; `observer_controls` in `example_round_trip_controls.py` changes or unlinks the path after open | Extract the same-descriptor sampler with an explicit prefix bound for both callers. Retain identity, full digest/length, bounded-prefix digest/length and error observations. |
| `_target_changes` and the `syscalls`, `identity` and `content` comparisons nested in `_native` | Extract the small sample and successful-read comparisons against independently supplied expected samples. Keep stability and missing-observation decisions with each caller. |
| `consumer.validate` and `extension_evidence.validate_fresh_read`; `blackbox_e2e/checker_controls` | Reuse for internal reply and syscall semantics, including unavailable later calls after a failed open. Do not infer worker reap or phase completion from consumer acceptance. |
| `fresh_read`, `set_fresh`, `fresh_fails` and the coherent controls `fresh_identity_of_A`, `fresh_inode_alone`, `fresh_content_of_A`, `fresh_count_alone_short` | Extract only the record construction/mutation needed by both callers, taking bytes and identity explicitly. The existing helpers select example's step 2 and its A/B/C samples; they are not a general capture API. |
| `prepare`, `preparation_rows`, `one_change_problems`, `diagnostics` and `failed_conditions` | Preserve the preparation boundary and explicit row/condition diagnostics. Author this publisher's target-binding and request-transformation rules separately. |
| `WORKLOAD`, `_prerequisites`, `_structure`, `evaluate` and the three-form capture builder | Keep the workload, expectations, completion assertions and passage association separately authored for this seam. Do not reuse the whole example evaluator or its constructed workload. |

The sampler, comparisons and explicit-byte control constructor now live in
[the shared helper](../tests/lib/file_observation.py). The
[example checker](../tests/suites/witness_contract/check_example_round_trip.py)
keeps its workload and existing diagnostics through small wrappers. Preserve
example's behavior and rerun its live case and controls when their dependencies
change. Do not create a universal workload checker or share expectations with
the product. The acceptance table must name the landed helpers and cases
reused, rather than describe them as work still to be invented.

Example's prerequisites require three distinct files and a distinguishing
fresh-read prefix. This experiment deliberately gives A and B identical bytes,
and its allow-default passages include a single target. Those prerequisites
must not travel with the sampler. Keep the new experiment's explicit inode,
content-transition and per-passage stability requirements below.

Preparation must reject publication, identity, snapshot or target-binding
failures before sampling targets, creating derivatives or invoking `run`.
The current example controls exercise that boundary through `prepare`, while
full evaluation of retained captures keeps independent faults visible beside
a publication mismatch. The new wrong-target emitter control must exercise
the corresponding real preparation path, not only a comparison helper.

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

The guide design and seam acceptance table are reviewed together. Once agreed,
implement the reviewed migration and command replacement;
land the guide changes before or with removal of `lesson`, never afterwards.
If the guide design is unresolved, freeze here with lesson intact. No second
guide architecture or generic harness refactor is included in this budget.

## Command, materialization and public account

The [read publisher](../controller/src/test_input.rs) embeds
[one body](../controller/src/test_inputs/README.md), replacing the two lesson
inputs. It uses an allow-default policy and one step pairing a file-read-data
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
Replace the [developer publication rule](CONTRACT.md#contract-request-specimen-emit_test_input)
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

For each admitted completed passage, also require the ordinary worker's
positive PID, applied and ready observations, completion, confirmed reap,
exit 0 without a signal and `after_confirmed_reap` collection basis; require
the submitted phase's arrival, completion and collection/release chain.
Use example's `structure.worker` and `structure.collections` conditions as
the review map, with separately authored assertions for this one-step input.
The consumer currently accepts an ordinary unreaped worker or incomplete
final phase in some otherwise valid constructed captures. Example rejects
them through its own structure rows. Include rejected controls for both here;
neither `finished` nor consumer acceptance supplies the missing observations.
These are workload completion expectations, not new universal admission rules.

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

Before implementation, present for maintainer review:

- The concrete guide passages and their reader conclusions, dependency map,
  harness fence changes and confirmed full-workflow equipment.
- The landed observer/comparison helpers and controls reused, with any small
  extraction needed; separately owned expectations and new controls.
- Canonical case IDs, fixture ownership and exact diagnostics, plus invocation
  accounting for the seven submissions (six execution passages and one
  refusal) and publication controls.
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
the production `runner_c_worker_harness` cases when their corpus inputs or loaders
change, following [test guidance](../tests/AGENTS.md). Inspect the actual selection
with `--list`. Select explicit C-worker case IDs, excluding the unrelated opt-in
`native_pause` and `arm_wait` qualification experiments; their default reader
controls remain included. Do not select the whole bad-request suite and
accidentally add its opt-in multi-build experiment. The seven seam submissions exclude the separately
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

## Concrete implementation checkpoint

The guide will continue teaching creation through an ordinary public request.
Its quick-start fence writes a quoted JSON body to `create.json`, then chains
`plutil` replacements for the current contract and the query/attempt target.
The existing preparation status, guarded submission, retained result and
independent empty-file observation remain. The body uses `guide-create`, one
`create` step, allow-default, file-write-create/path and file/create.

The refusal exercise copies that saved request to `capture-typo.json`, changes
its specimen ID and both targets, and inserts
`policy.capture_compiled_profiel`. Its spelling repair, missing-nonce refusal,
nonce insertion and positive capture stay intact. Helper, provenance and
path-reading passages continue using the same create files and observations.
The BYOXPC passage retains its create derivative and full owned installation,
verification, execution and cleanup. No ordinary guide passage uses test-input.
The CLI table drops lesson. The harness selects the actual here-document and
copy fences, checks the exact derivative differences, and exercises failed
preparation with existing-result preservation and guard-removal controls.

Equipment was reconfirmed before implementation: the selected app's Developer
ID team matches the available signing identity (`42D369QV8E`), GUI and console
UID are 501, registry and pending cleanup are empty, reconciliation has no
candidates or inspection errors, and source/staged guide bytes match. Receipts
are disposable local observations under
`/private/tmp/pw-test-input-equipment-implementation`. The guide harness owns
the service it installs through its existing durable session and cleanup path.

| Owner | Concrete mapping |
| --- | --- |
| `tests/lib/file_observation.py` | Extract the example's descriptor sampler, sample-change comparison, successful fresh-read comparisons and explicit-byte/identity record constructor. Bound is supplied by callers; fixture prerequisites remain separate. |
| `witness_contract/example_round_trip` and `example_round_trip_controls` | Preserve the existing 158 rows and 170 conditions; retain observer replacement/unlink controls and coherent fresh-read controls after helper extraction. |
| `witness_contract/test_input` | Own seven passages (`initial_a`, `updated_a`, `b`, `refusal`, `repair`, `denied_b`, `allowed_a`), six executions and one refusal. Retain each command's argv/stdout/stderr/status, exact submitted bytes, transitions and before/after samples outside run captures. |
| `witness_contract/test_input_controls` | Own offline accepted/rejected captures and actual preparation controls. Diagnostics name `publication`, `fixtures`, `transformation`, `status`, `consumer`, `association`, `worker`, `collections`, `query`, `identity`, `content` and `stability` obligations per passage. Classifications are `passed`, `failed`, and `not_evaluated`; missing prerequisites withhold only dependent credit. Controls declare exact failing obligations. |
| Preparation boundary | Version/plist/packaged contract identity, deterministic publication, target binding and literal `$EFFECT`/quote/backslash/Unicode publication precede any native submission. A recorded wrong-target emitter invocation must fail before sampling, derivatives or run. Publication command count is retained separately from seven submissions. |
| Fixture ownership | Case-owned resolved private temporary directory, independent A/B bytes and samples; cleanup only that owned directory. Constructed controls use independently authored ordinary reply expectations and shared wire-capture utilities, not example's workload evaluator. |
| Publisher and corpus | One embedded read body and positional binding with malformed-template controls. Move old creation bodies unchanged into request-corpus ownership, preserving Python/Swift and CLI/direct-host grammar coverage; retire old selector-substitution executions. |
| Public account | Replace stamped `emit_lesson` with build-bound developer `emit_test_input`; update the single shared usage and README, build-identity inputs/mutation checks, support references and generated snapshots without raising evidence grades. |
| Final verification | One signed candidate after offline controls, then the combined selection specified above, including both runner families because corpus loaders change and the whole guide workflow. No native admission or ordering change is intended. |

## Completion account

The maintainer accepted the concrete checkpoint before implementation. Commit
`ba3a90435d5354097514051196374c7f839fef11` implements the publisher, corpus and
guide migration, shared observer extraction and separately authored seam.
One signed candidate was built: development build **1445**, source `ba3a9043`,
contract `development:a4b24cf0d127f8a450050bdde17de8e8ca3415f718cda2858f683dbdd06dbcc9`.
No native admission, worker wait, release store or eligibility code changed.

### Verification credits

The combined run `20261115T004609Z_a4ad194a` at
`tests/out/runs/test-input-acceptance` completed all 95 selected cases:
**92 passed and three failed**, with no skip, unrun case, system sleep or app
inventory change. It is a failed run and remains recorded as such.

- `runner_outcome_bad_request/accepted_input_contract` stopped before its native
  corpus at a missing `CORPUS` import left by the migration. Restoring that one
  import was the only executable-source repair after the combined run.
  `20261115T010037Z_a163d65b` (`test-input-corpus-repair`) then passed that complete
  CLI/direct-host case on the unchanged candidate, with no sleep, harness error
  or app inventory change.
- The whole C-worker suite selector accidentally included `native_pause` and
  `arm_wait`. Their [owner](../tests/suites/runner_c_worker_harness/README.md#native-pause-applicability)
  defines experimental qualification of alternative waits, outside this plan's
  production-worker acceptance. Default nanosleep failed its qualification
  (the deny-default first calls returned -1/EINVAL); all 24 measured children
  were reaped, with no timeout. The ARM screen refused a missing coordinator
  gate before executing children. Both failures remain failed and uncredited;
  no expectation was broadened or production wait changed to obtain a pass.

The corrected acceptance selection contains **93 applicable cases**: the 92
unaffected passing cases plus the repaired corpus case. It includes all ten
source-drift cases, all unit/integration cases, runner-unit cases, production
C-worker cases and both experimental readers' default controls, blackbox checker
controls, both example cases, both test-input cases and the whole guide workflow.
The 92 passing results are reused across the one-line corpus-import repair:
that driver is reached only by the failed corpus case; shared readers, fixtures,
production inputs, selected app and other case commands are unchanged. The
completion prose and selection clarification change no assertions, generated
surface or build input. This is reviewed applicability, not a claim that the
original run exercised a later source revision.

Source-manifest checks were repeated successfully in `20261115T010316Z_ced552fc`.
That run's generator check identified duplicated literal bounds in completion
prose; the prose now refers to the existing recipe. The complete generator case
then passed in `20261115T010656Z_d8115b4f` (`test-input-completion-docs-final`).
This final receipt note changes no link, assertion, public surface or input rule.

Earlier offline runs established the checker and Rust behavior before the
candidate build. The first new fixture lacked required path diagnostics; that
fixture was corrected. The broader offline run exposed stale plan links to the
removed lesson and Rust formatting; both were repaired and the targeted rerun
`20261115T004221Z_bb5b007e` passed. Failed rehearsals remain disposable evidence.

### Observations and limits

The live seam passed all **117 report rows** with exactly **seven submissions**
(six execution passages and one refusal), four publications and one version
command. Initial A returned 63 `a` bytes; the exact same request then returned
63 `b` bytes from the same inode. A's long update and independently created B
had equal `N + 1` payloads and required metadata, with different inodes; reads
returned the exact `N`-byte prefix. Repair matched the emitted B document.
Denied B separately reported query deny/rc 1/errno 0 and fresh-open -1/EPERM,
with aggregate `read_failed` and process exit 0. A under that identical policy
reported allow and its own successful read. All six workers were confirmed
reaped, phases completed, and the refused passage reported the exact unknown
policy member with no execution records.

All **34 offline controls** matched their exact oracles: 21 consumer-accepted
capture cases, seven preparation scenarios and six cleanup-witness controls.
These include whole-capture replay rejected for current-content mismatch,
wrong-target publication through the actual acquisition boundary, and detection
of a driver that ignores the supplied emitter. The example retains its 158 rows,
170 conditions and passing live/constructed coverage after extraction.

The full guide produced independently observed empty 0600 files, retained its
refusal/nonce/compiled-capture exercises, passed eight preparation-guard controls
and completed installation, verification, execution and removal of its owned
external runner. Independent service/plist/registry absence and unchanged app
inventory were recorded. Both guide and seam staging directories were removed
only after their cleanup obligations were discharged; durable receipts say
`removed: true` and the paths were independently observed absent. Two Astra
agents assisted: one focused on publisher/corpus migration, and one stayed
through guide design, implementation, driver review and native evidence audit.

The public change is one build-bound developer publisher and its stamped rule;
ordinary guide teaching and corpus expectations remain separately owned. The
maintenance added is one small shared file-observation helper and two seam
cases. Two embedded lessons and their extra native selector-substitution
executions were removed. Samples establish sampled stability, not continuous
stability; the query contrast does not identify a queried object or establish
sandbox causation. Constructed controls show sensitivity, not native occurrence.
All cited runs are disposable development observations, not retained release
acceptance. The later guide overhaul and 0.3.8 tag remain separate work.

### Review after completion

A review of the two implementing commits changed the seam's test code and test
documentation. No build input changed; build 1445 remains the candidate.

- **Order has its own row.** `query_first` was part of each `.query` row, so an
  order fault read as a wrong answer. Each executed passage now has `.order`,
  credited only beside the expected answer. The retained-A comparison also
  includes A's sample before `allowed_a`.
- **Every obligation has a rejecting control.** No earlier control could fail
  `association`, `attempt`, `build`, `reply` or `consumer`, or the publication
  `targets`, `framing` and `invocation` rows, and `fixtures` failed only through
  a missing sample. Ten coherent captures and one capture from another build
  were added; the consumer accepts the ten and refuses the one. The case now
  fails unless each obligation, taken without its passage or emission name, is
  failed by some control. Removing the single association control made that
  assertion refuse.
- **Accounting is counted.** The driver wrote its submission and publication
  counts as constants. It now counts the recorded command lines and refused
  passages, then compares them with the expected seven, six, one, four and one.
  A second copy of the per-passage request expectations was removed in favor of
  the checker's.

Run `20261115T011916Z_0404749d` at `tests/out/runs/test-input-review-1` passed
its 12 cases without system sleep or harness error: both seam cases and all ten
source-drift cases. The live case passed **123 report rows**, the earlier 117
and six order rows, with the same seven submissions; staging was removed and
observed absent. **45 offline controls** matched: 31 coherent captures, one
unadmitted capture, seven preparation scenarios and six cleanup-witness
controls. Source drift was run again on this section's final text in
`tests/out/runs/test-input-review-docs`.

The other 81 results of the corrected acceptance selection are reused. The
changed files are the seam's checker, driver and controls, read only by the two
seam cases, and three test READMEs. This is reviewed applicability, as above.

Two publisher details were left for a maintainer decision, since either edit
changes the build identity and needs a new candidate:

- `render_template` validates the embedded body by equality with a second
  complete copy in the same source file, so the product holds the body twice
  and the stamped rule promises validation of the complete fixed template.
  Checking only the assigned positions would change that sentence.
- `complete_publication_requires_all_writes_and_flush` loops over a
  one-element selector list left from the two-lesson emitter.
