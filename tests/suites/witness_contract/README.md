# witness_contract

Pins the load-bearing behaviors PolicyWitness contracts to provide:
answers in the envelope, attempts in the envelope, the relation between
the two recorded explicitly, validator failures attributed honestly, removed
fields rejected, the specimen dossier collected, the test seam functioning,
and the source-drift guardrail enforcing the audit trail.

Cases assert contract claims independently. The suite reads as a
behavior specification — what PolicyWitness promises, regardless of
the architecture behind it.

## Guide workflows

The opt-in `guide_workflows` case executes selected `sh` fences from
`docs/PolicyWitness.md`, after verifying that the selected app's adjacent staged
guide has identical bytes. Only `APP`, `IDENTITY` and `ENT` setup values are
substituted. Explicit cuts preserve the displayed command text while allowing
ownership, exit-status capture and independent observations between commands.
The shell state retains the guide's variables and umask; refusal commands keep
their expected nonzero status. Source extraction controls refuse missing or
ambiguous fences and reordered cuts. Preparation controls execute the actual
create fence with a failing writer that leaves partial JSON, and the capture-typo
copy fence with malformed saved input that the actual `plutil` refuses. They
check no submission or target, no new result, and preservation of an earlier
result. Removing the successful preparation guard must make the same oracle reject a recorded submission;
the fake run never performs a native operation. Constructed ownership controls use the
existing fake OS tools and actual cleanup paths to observe refused foreign
owners, uncertain submissions, each absence requirement and interrupted deletion
recovery. The existing dispatcher retention control checks the top-level guide
receipt through ordinary prune.

The sequence authors an ordinary creation request with the current contract
and target, creates a new empty file, observes an existing-target guard,
repairs a misspelled capture flag and a missing nonce, reads a positive compiled
object receipt, checks the policy through `sbpl-check`, and runs the external
runner list/reconcile/install/status/verify/create/validate/remove workflow.
Native file observations include absence before invocation and a regular empty
0600 file afterward. Refused requests retain their inputs, specific failure
codes/paths and absent target. The capture receipt binds nonce, worker PID,
source hash and retained bytecode length/hash; capture unavailability cannot
supply this case's positive-capture observation. Helper success and unchanged
file observations are recorded separately.

The case requires a matching Developer ID identity, a logged-in GUI session and
an empty default runner registry with no concurrent registry changes during the
workflow. Under those equipment conditions, the displayed `runner validate`
refreshes only the owned installation. An additional installed record present at
validation makes the expected updated-record count fail; validation may already
have refreshed that record's metadata before the failure. The supplied
entitlements plist comes from an independent read of the selected worker's
signature. The case is opt-in because it signs and installs a service in the
actual user launchd/default-registry locations. Run it through
`tests/run.sh --case witness_contract/guide_workflows`.

`artifacts/session.json` and the work directory's durable record own the guide's
fresh work directory. `byoxpc-session.json` and the staged runner's durable
record use the existing BYOXPC cleanup helper with an explicit guide layout;
parent/staging inode, exact service, executable, plist and registry ownership
must agree. A submitted run needs a retained worker-exit witness, or the named
host admission refusal before launch, before cleanup can remove its work.
Harness interruptions and unknown dispositions retain both resources and
ownership. Successful removal requires independent launchd, plist and registry
absence; cleanup also compares the selected app's complete inventory.

Artifacts preserve guide bytes/hash and fence line ranges, actual substituted
shell fragments, command stdout/stderr/status, version/contract, all request and
result files, independent file and cleanup observations, equipment readback and
constructed source/ownership controls. The copy fragment records its shell's
`cp` resolution and both bundle inventories. Copy checks preserve contents,
types, paths and owner access, allow the private mask to narrow directory modes,
and reject source aliases; constructed controls retain changed-content and lost
execute-permission refusals. Retained-reader interpretation and
unavailable-capture branches have their own controls; this case records the
native workflows it executes.

## Controlled read input

The default `test_input` case invokes the selected app's developer command
`test-input read --target PATH`. Publication preparation requires the version,
plist identity, independently authored stamped read-input example, deterministic
A emissions and verbatim target binding. A publication-only operand includes
literal `$EFFECT`, quotes, a backslash and Unicode. Failed preparation prevents
sampling, derivatives and submission.

The case owns a resolved private directory under `/private/tmp`, retained byte
recipes and descriptor samples. Thirteen submissions cover initial A,
in-place updated A using the exact saved request, long B, a harness-injected
unknown-field refusal, exact repair, denied B and allowed A under the identical
policy, then the crossed matrix and returning actors, replacement A, a
suffix-only update, an empty file and an exactly bounded file. Twelve execute;
one is refused. Four publications and one version command make eighteen CLI
invocations. A and B have equal long content/device/mode/owner/group and
different inodes; A's inode survives both updates. Before/after
samples establish sampled stability, not continuous stability. The replacement
is created separately with equal bytes and metadata, then installed under A's
name while the original is parked. Samples require two distinct generations,
unchanged parked bytes and an unchanged B. Every replacement passage submits
exactly the saved deny-B/allowed-A request bytes.

`distinctions.json` compares a fixed set of request, query, attempt, descriptor,
content, sample and ownership facts against independently authored equality
expectations. Replacement changes the descriptor inode; a suffix-only change
and removal of the suffix at the bound change external samples but leave the
returned bytes indistinguishable. Empty reads require successful open/stat/close,
zero returned bytes and the empty digest. Controls accept the indistinguishable
read-record substitutions beside each passage's own samples, and reject old
whole captures, identity-generation changes, missing parked samples, stale full
samples and changed prefix/count evidence. The samples do not show that the
worker read beyond the bound or that the path stayed unchanged between samples.

The `crossed` passage keeps both files at the same long bytes, under distinct
inodes and the deny-B policy. Its five rows are:

| Step | Query | Attempt | Query answer | Open |
| --- | --- | --- | --- | --- |
| `read-aa` | data A | A | allow | success |
| `read-ab` | data A | B | allow | EPERM |
| `read-ba` | data B | A | deny | success |
| `read-bb` | data B | B | deny | EPERM |
| `metadata-b` | metadata B | B | allow | EPERM |

Each row separately checks submitted operands/relations, the native query,
order, attempt and successful read identity/content. The consumer owns internal
joins. Three additional distinction pairs compare the crossed query target,
crossed attempt target and changed query operation. In `read-ba`, equal file
bytes leave descriptor identity as the observation identifying A's opened
object beside the deny answer about B. Controls change each derivative operand,
omit/duplicate/reorder rows, exchange coherent step evidence, change query or
attempt results independently, substitute B's identity, change a returned byte
and remove established order. A reply whose records are all reversed together
fails only the passage's association and collection rows; every step is still
found by its identifier. A's inode changed for this passage alone, with reads
that agree with the changed sample, fails the generation row. These
observations do not claim prediction/enforcement agreement.

The `returning` passage submits the same five rows using two applied actors
with equal deny-B policies and explicit `selected` equipment. It runs only
after the same acquisition's `crossed` rows and distinction pairs pass.

| Phase | Actor | Rows | Global ordinal | Actor visit |
| --- | --- | --- | --- | --- |
| `left-first` | Left | `read-aa`, `read-ab` | 1 | 1 |
| `right-only` | Right | `read-ba` | 2 | 1 |
| `left-second` | Left | `read-bb`, `metadata-b` | 3 | 2 |

The checker requires Left's visits `[1, 3]`, Right's `[2]`, distinct launch
PIDs, one application and one reaped subprocess per actor, and each phase's
submitted owner, ordinal, visit, step IDs and validator expected IDs. It reuses
the matrix's native step expectations and leaves internal joins to the consumer.
Five pairs compare each row across the forms: request bytes and ownership
differ while operands, query, attempt, identity and returned content agree.
Together with the four boundary and three within-matrix pairs, the table has
twelve independently expected rows.

The constructed two-actor capture uses the
[authored actor fixture](../../fixtures/example_round_trip/README.md) as a
structural template with separately constructed matrix observations. Controls
exchange actors, misnumber visits, move complete steps between phases, alter
visit/validator lists, share a PID, report a second application or an unreaped
actor, and accept consistent actor/phase/step renaming. The unreaped control
also requires the real cleanup decision to withhold removal. A derivative with
another partition, another policy for one actor or another query operand fails
the transformation row, which the driver requires before submission. In this
form too, a wrong query answer, a refused read, B's identity, a changed
returned byte, an unestablished order and a changed A generation each fail
their own row beside correct ownership. The real crossed-matrix gate has
accepted and rejected controls before actor derivation.

Equal policies do not distinguish whether policies reached the correct actors,
and these finite observations do not establish execution-form equivalence.
`actor_compositions` retains distinct-policy, gate and extension obligations;
`comparison_matrix` retains general relation classification; the independent
prediction-target case retains write effects; and `example_round_trip` retains
its exact published bytes, refusals and one-actor derivative. Beside them this
case adds a fresh read's descriptor identity next to a crossed query when both
files hold the same bytes, failed fresh reads, and a returning visit whose
number differs from its global ordinal. Reader agreement stays with the shared
consumer, which decodes the retained host bytes independently and compares
them with the controller's projection for every passage.

`check_test_input.py` evaluates every passage. Beside it,
`test_input_views.py` holds the generation rows and the distinction table,
`test_input_actors.py` the returning form's expected request and rows, and
`test_input_actor_controls.py` the constructed two-actor capture and its
controls. They are helpers of the two cases, not cases of their own.

The separate checker pins observed and published status, identity admission,
request transformations, policy digest and operand association, completed worker
and phase collections, query answers, independent syscall results and successful
read identity/count/prefix. `query_first` order has its own row, credited only
beside the expected answer. The deny expects query rc 1/errno 0 separately from
open EPERM/read_failed and a completed process exit 0. The consumer validates
internal evidence and unavailable later operations after failed open. These
observations do not identify the queried object or establish sandbox causation.

`test_input_controls` is offline and default. Authored ordinary captures exercise
wrong inode with identical bytes, old bytes with current identity, replay of the
whole previous run capture, omitted refusal injection, exchanged query answers,
observed status distinct from published status, unreaped worker, incomplete
phase and independent faults beside missing observations or bad publication.
Further captures supply another passage's coherent run, a successful read
beside the deny and a refused read beside the allow, an unestablished order,
a replaced A inode, a B sharing A's inode, and publication records with another
target, command or second newline.
Controls require exact diagnostic IDs and statuses (`passed`, `failed`,
`not_evaluated`) and consumer acceptance for coherent correspondence faults.
A capture from another build has its reply rows withheld as `not_evaluated`.
Malformed actor joins remain consumer-owned rejection controls; coherent
association faults must still pass that consumer. The case fails unless every
obligation the checker reports is failed by some control. An obligation is a
row without the names that only select among rows evaluated alike: an
emission, a one-step passage, and a form's step, actor or phase. The crossed
and returning forms keep their own names on their matrix, ownership and
derivative rows, so each needs a control in that form; only the status,
build, consumer, reply, worker and sample rows, which every passage computes
the same way, are shared. Each distinction pair is its own obligation, and
the five pairs across the two forms are one.
The real acquisition path is exercised with recorded stand-in executables;
wrong-target output fails before the observer, and deliberately ignoring the
supplied emitter is detected by that scenario's oracle.

### Submissions with `test-input run`

After the thirteen passages and their accounting, the same case submits the
published read input through `test-input run`, in the same owned directory
and under the same cleanup record. [test_input_seam.py](test_input_seam.py)
launches and records; [check_test_input_seam.py](check_test_input_seam.py)
owns the plan and every expectation. Each submission that carries controls
goes through the [seam invocation adapter](../../README.md#seam-invocations),
so its command, controls and delivered request are on disk before launch.

Each of the eight controls has one submission and three separate rows. The
submission row reads the adapter's record: the route, the flags and a
delivered request equal to the ordinary one. The echo row reads the reply's
`test_overrides`. The intervention row reads only what the host or worker
observed of itself and never the echo:

| Control | Submitted | Observation credited |
| --- | --- | --- |
| `worker_timeout_ms` | 7000 | the host's sentinel wait budget is 7000 |
| `worker_post_apply_hang_ms` | 2000 | the sentinel wait lasted at least 1900 ms and ended at `done`, after the read completed |
| `worker_pre_ready_hang_ms` | 400 | the ready wait lasted at least 380 ms and ended at the ready byte |
| `worker_post_apply_kill_signal` | 9 | the worker was reaped with signal 9 after its completed read, with no host termination request |
| `worker_kill_before_publish_slot` | 0 | the worker was reaped with signal 9, its last progress the started attempt, and the read has no completed result |
| `validator_executable_path` | a path that does not exist | the phase's spawn failure names that path, and no validator ran |
| `validator_io_timeout_ms` | 500, with the transcript validator substituted | collection stopped at a 500 ms deadline; the fixture's own receipt names the worker PID and both probes |
| `validator_total_timeout_ms` | 1 | the phase's collection is `budget_exhausted` and no validator was spawned, while the read completed |

The validator path's submission has a fourth row: the dossier's validator
record names the substituted path, and the neighbour's is null.

Beside them the case runs an ordinary `run` of the same input as the
neighbour; `test-input run` with no control, which must show the neighbour's
allowances, collection and read, and echoes an empty object; and six malformed
command lines and one control flag after plain `run`, each refused with exit
2, a `tool_error` envelope and a null client capture.

Further submissions vary what a control meets:

| Submission | Controls | Observation credited |
| --- | --- | --- |
| Two controls together | `worker_timeout_ms` 7000 and `worker_pre_ready_hang_ms` 400 | the sentinel wait budget is 7000 and the ready wait lasted at least 380 ms, each from the host's own wait record |
| A boundary never reached | `worker_kill_before_publish_slot` 5 on the one-step plan | the echo names the control, and the reply shows the neighbour's allowances, collection and completed read |
| The ordinary allowance floor | `worker_timeout_ms` 1 and `worker_post_apply_hang_ms` 2000 | the sentinel wait budget is 50, not 1; it ended at the deadline after at least 50 ms, and the host ended the delayed worker with signal 9 |
| A request refused early | `worker_post_apply_kill_signal` 9 beside a request with an unknown field | `unknown_field` at that field, no worker and no echo |
| Each worker argument range | 60001 for either delay, signal 32, slot 256, one submission each | the launched worker exits 2 before readiness, with no request refusal |

A request carrying its own `_test_overrides` block is submitted with
`test-input run` four ways: with a value, with a null member and with the
worker substitution beside a control, each refused by the host at
`_test_overrides` before any worker; and with an empty block, admitted. Three
submissions go through `pw-runner-client` itself: a controls object the host
applied, a request block the host refused, and a controls object whose
`worker_timeout_ms` is 1.5, refused with `type_mismatch` at
`_test_overrides.worker_timeout_ms`.

Each of the eight controls is also written by hand into an ordinary request's
`_test_overrides` block and submitted three ways: through plain `run` with
the value its activation used, through plain `run` with a value the host would
not forward or would read as absent (null for the three deadlines and the
validator path, zero for the pre-ready delay and the signal, a negative delay
and slot), and through `pw-runner-client run` without a controls object. Two
more blocks hold a control beside the worker substitution and two controls
together, and one puts `validator_total_timeout_ms` alone in the block of the
one-actor form of the same read, through plain `run`. Every one must be
refused with `inapplicable_field` at `_test_overrides` and the control's name,
the first in the host's order when there are two, with no worker record, no
echo and an unchanged target; the controller's envelope carries the same
refusal, and the actor-form reply holds no actor record.

The two substitutions that stay in a request's block are submitted with plain
`run`, without the adapter. `worker_executable_path` naming an absent file
ends in `worker_spawn_failed` with no worker record, a `posix_spawn`
diagnostic and the dossier's worker record at that path. On the one-actor
form of the same read, `actor_equipment_executable_paths` naming an absent
file ends in `runner_failed` with `equipment_binding_refused` at the
equipment stage and an actor that was never launched. Each reply echoes its
block.

`test-input read` is published before and after these submissions
with equal bytes, and once under `sandbox-exec` with a profile that denies
`process-fork`: publication is unchanged there, while `test-input run` under
the same profile cannot launch its client.

These rows establish the route for the values submitted. They do not vary an
external runner or every refusal at the client, and the actor form appears
only in the equipment substitution and in one refused block, with one control
and one entry: `actor_compositions` owns the contrast
between the ordinary allowance and the actor execution allowance under the
same controls. A lower bound on a wait duration shows the delay occurred; the two
duration thresholds for the neighbour are test choices, not product limits.
The fork-denying profile shows that publication needs no new process; it does
not observe file reads.

`test_input_controls` runs [test_input_seam_controls.py](test_input_seam_controls.py)
over hand-written records: each submission with another route or a control
moved into its request, another exit, another build, a refused consumer
reading, a missing echo, the echo beside an ordinary reply, and a target
changed during the submission; each control's observation at and just inside
its bound or with the neighbouring cause; each refusal reported at another
boundary; each request-block refusal located at the whole block, followed by
a worker, echoed, made through the experimental call or answered as a host
that still admitted the block would answer; the actor-form block followed by
a launched actor, delivered in the ordinary form or refused at the equipment
member; and each `read` row. Every row the checker reports must be failed
by some control.

`tests/lib/file_observation.py` shares only the same-descriptor sampler, sample
change checks, fresh-read comparisons and explicit-byte/identity control record
construction with example. Workloads, fixtures and expectations remain separate.
Each run retains raw command captures, submitted inputs, samples, transformations,
reports and owned-resource cleanup receipts. Unknown worker disposition retains
the owned fixture directory for recovery; native deviations are failures, not
permission-class substitutions. These development runs do not create release
evidence or raise contract support grades.

## Public-output interruption

The opt-in `porcelain_output_controls` case runs one read-only specimen with
256 `/etc/hosts` queries/opens across eight phases. Its complete positive run
must succeed, pass the independent consumer, preserve exact binary host bytes
and establish every phase's query order and the worker's reap. Independent
reads confirm that `/etc/hosts` stayed unchanged. Two subsequent invocations
of the same specimen run serially: the harness reads exactly 128 and 4096
stdout bytes respectively, then closes the real pipe. Each CLI must exit
nonzero and leave an incomplete JSON document; harness timeout or cleanup
kill cannot supply that outcome.

This case exercises the binary transport and is opt-in
because it deliberately interrupts public output. Each invocation has a
120-second harness bound and a 60-second client allowance. Only the owned CLI
is signalled on harness timeout. The specimen creates no mutable worker resource.
A partial document establishes no complete envelope or worker disposition.

Artifacts retain source/executable hashes, request files, argv, statuses,
stderr, exact prefixes and the positive `run.json`/`host-reply.pwp` receipts.
`complete/measurements.json` records full public stdout, host and client-capture
byte counts and one elapsed duration; these are descriptive observations, with
no baseline, memory or performance-superiority claim. `output-controls.json`
collects the complete and interrupted outcomes. Run through
`tests/run.sh --case witness_contract/porcelain_output_controls`.

## Footprint observations

The default `held_phase_footprint` case repeats matched ordinary and actor holds
at declared intervals. An acknowledged validator bridge holds collection while
external generation-qualified samples record worker CPU and apparatus demand.
Selected effects remain absent until release. Actor variants include the
custody, delivery and handle hold, with metadata-only publications from a
disposable signed host fixture. Busy and sleeping controls calibrate observable
CPU increments. The case requires complete repeated observations; it establishes
neither idle waiting nor a universal CPU threshold.

`check_wait_measurement` is the mechanism-neutral counterpart: it retains the
same held-generation, effects, sampling, sleep and busy/sleep sensitivity checks
without requiring worker CPU to exceed the sleeping control. The default
`worker_wait_cpu_controls` accepts a constructed quiet worker and refuses bad
generation, missing effects, native errors, early release and invalid intervals.
The existing `check_measurement` and live `held_phase_footprint` case retain
their busy-worker requirement and historical meaning. Neither reader by itself
establishes a matched improvement or converts artificial holds into production
hold durations.

The default `response_footprint` case samples fresh shipped controllers handling a
small known-byte read, the fixed-action independent-query and phased pair, the
control-character exec workload and the existing actor maximum read workload.
The existing maximum-reply checker retains action, transfer, equipment, resource
and profile assertions. Strict decoding preserves exact host bytes and a computed
transport-artifact hash; the transport supplies no independent producer hash.
Host reply, client streams, final envelope, optional bytecode and logical actor
storage remain distinct quantities. Native resident and physical-footprint
samples stay separate and have unknown decoder-stage attribution. Required
same-generation samples and independent exit observations cannot be replaced by
an inspection error or a documented retention limit.

The source-ownership receipt names binary capture bytes, fixed typed transport
and host records, and the public JSON text, with source hashes and explicit
framing, decoded-storage, depth and retention bounds. It makes no allocation,
overlap or decoder-stage timing observation. Base64 is counted only in the
public projection of retained raw bytes. The default `response_footprint_controls`
and `held_phase_footprint_controls` accept constructed valid receipts before
rejecting missing ownership rows, incorrect counts, invalid units, capacities or
measurement claims. The default `footprint_observer_controls` builds the native observer and
checks acknowledged allocation and CPU sensitivity, generation/metric/error
validation and exited-generation inspection; it needs Clang but no app.

Artifacts include observer source/binary identity and raw samples, conditions,
calibration and declared hold repetitions, per-hold `measurement.json`, response
`response-footprint.json`, exact `host-reply.pwp`, `RunCapture` files, the
source-ownership declaration and independent exit receipts. These cases require
native inspection and XPC access; the actor hold also needs a matching Developer
ID identity and disposable-host signing. See the
[execution and interpretation account](../../CHANGE-VERIFICATION.md#footprint-observations)
and the [footprint account](../../../docs/FOOTPRINT.md).


The opt-in `worker_wait_cost` case uses the held workloads and neutral reader
for a bounded CPU screen. Set a fresh `PW_WAIT_COST_GATE`, role
`PW_WAIT_COST_ROLE=release|activation`, and
`PW_WAIT_COST_CANDIDATE=baseline|wfet|hint10000`. Baseline mode takes one
observation per pacing regime; comparison takes five alternating matched pairs
per regime. Each exact staged app first gets one excluded request. After
signing disposable workers, `prepared.json` identifies the bytes; the case
waits up to ten minutes for `begin` in the gate file. Its five-minute window
includes calibration and excludes builds. The ordinary cell has one worker
and a busy control; the actor lifecycle cell has two workers and that control.
Activation CPU belongs to the parked, unapplied issuer; the queried subject
is held in release. Extended holds are not production hold durations.

The WFET prototype changes one unsuccessful tail, reads CNTFRQ before
application and checks a local CNTVCT deadline, capped at 100 microseconds and
the last sampled remaining allowances. Its machine feature prerequisite is
not a production deployment gate. The hint prototype changes one batch to
10,000 hints. Both retain the baseline ABI identity as labelled substitutions;
source and executable hashes identify their actual bytes. Comparison allows
one calibrated quantum per CPU endpoint and brackets elapsed time. Every pair
must save the declared fraction (`PW_WAIT_COST_MINIMUM`, 10% by default)
beyond those bounds. Controls
credit a constructed gain, refuse no-op/contrary-pair credit and reject missing,
excluded or power-mismatched pairs. A positive CPU screen does not qualify
response, whole-request cost, energy, capacity, restrictive parked operation,
migration or sleep/resume. The 60-second measurement watchdog unwinds through
owned cleanup; a default control exercises that path with a real alarm.

## Worker wait pilot

The opt-in `worker_wait_pilot` case decomposes ordinary and actor held phases
on the production planning and validator path, with no test overrides and no
collection hold. It builds a disposable host from patched copies of the runner
sources, which records `mach_continuous_time` stamps in preallocated storage,
and an unpatched neighbor host with the same recipe. Both apps are staged once
into the case artifacts with fresh bundle identifiers and signed with the app
team's Developer ID identity. The stamped app carries the seam-built worker in
both roles; it records publications and pass samples in capture pages of its
region, which the host copies before teardown. After the reply the host writes
its stamps and those pages to a directory fixed at build time. No wire field
or post-apply resource is added.

Inside the declared window, the clock-pair calibration control runs first,
then one excluded first execution of each staged app, with an eligible query
and the actor cell when selected, precedes counted trials. Every trial reuses the
same staged executables in fresh processes. The declared schedule covers one,
64 and 256 eligible queries, a matched zero-eligible layout using the static
prediction-unavailable pair, two phases, the two-actor lifecycle with
deliveries (`A2`) and its inbound-dense form (`A2D`): the same two actors,
with the issuer issuing 32 file tokens (the `actor_issues` capacity) and
transferring each twice, 64 deliveries (`actor_deliveries`) that fill the
subject's 64 inbound slots, before the subject reads its target and consumes
and releases only the first and the last delivery. The excluded first
execution uses the first selected actor cell. A rapid block launches after each observed cleanup; an idle block
requests at least one second after it and alternates with the neighbor. A
trial starts only when its watchdog and cleanup reserve fit the remaining
declared window; otherwise it is recorded as skipped. Observed cleanup is the
CLI exit plus a generation-checked host exit event, or the CLI exit plus
100 ms where no host watch exists, as for the neighbor. Each trial retains
power source and Low Power Mode before and after, observer continuous and
uptime clocks for sleep, load averages, requested and actual gaps, whole-request
latency and the envelope's millisecond fields.

After the window, every envelope must finish and pass consumer and lifecycle
validation, with attempt, eligibility, issuance and delivery checks per cell.
`worker_wait_pilot_reader.py` then writes `decomposition.json`, `summary.json`
and `summary.md`. It never pools apps, cells, regimes, power sources or host
flavours. Sleep-overlapped, power-transition and out-of-range trials stay in
the decomposition and out of aggregates. Stamps describe the disposable
stamped flavour, not production executables. The host poll interval is
reported as detection response, not instrument resolution. A host observation
with no negative sample before it is a separate `*_first_check_positive` row,
attributed where possible to the host sleep that contained the worker's
publication: the exact sleep when the host recorded it as a stamped event pair
(its first 64 sleeps per wait key), otherwise a register pair, otherwise
marked unattributed. The ordinary host's detection of the worker's terminal
publication is a component of its own, and exchange waits appear in the wait
table with their pass counts and an upper-bound period. Per actor, the worker's
terminal publication to the host's exit request, that request to the host's
reaping sample, and the worker exit grace between its begin and finished stamps
are program-point components (`w<actor>.terminal_to_exit_request`,
`exit_request_to_reap`, `grace_wait`); the worker's exit itself has no stamp.
Direct `terminal_to_reap` and `terminal_to_teardown` intervals retain the terminal
publication bracket. `spawn_to_teardown` ends at the session's cleanup program
point; it does not establish successful native deallocation. The ordinary
`final_wait` record separates plain sleeps and notification/timeout/unusable
outcomes after the last release and before the exit request. A complete zero
means no wait was entered; missing boundaries or truncated sleep events leave
the counts unobserved.
Each trial counts how its worker grace waits between samples ended
(`grace_timeouts`, `grace_notified`, `grace_unusable`, `grace_settle_sleeps`): a
wait followed by its outcome event by that outcome, a plain sleep under the
grace key requested at most 100 µs as a settle sleep after a notification, and
a longer plain sleep or a wait past the 64 recorded pairs as a timeout. Groups
sum the counts. An outcome code
other than 0, 1 or 2, an outcome that does not follow its sleep pair, or a grace
that finishes before it begins refuses the trial. Each trial also
carries `detection_total`, the sum of the host's post-publication detection
latencies (arrival after an activation or release, completion after a
release, recipient acknowledgement after an inbound commit), which a
comparison can pair as one quantity when the parts are bimodal. Each interval's uncertainty is the sum of its two endpoint
terms, where a publication's term is the width from the nearest preceding
stamp in the same process to its post-store stamp, floored at the clock-pair
receipt's endpoint term and, for host endpoints, at twice the host's in-situ
stamp cost, plus the receipt's alignment bound across processes; values at or
below it are marked below the instrument floor. Groups are keyed by app, cell,
regime, power source, low power mode and host flavour. A trial whose exit-watch
registration overlapped a held interval is excluded as `observer_overlap`. The
case completes when no trial failed, was incomplete or was refused, every
scheduled entry has a receipt, each app, cell and regime has at least five
accepted trials in one group, the calibration receipt is accepted, the staged
executables are unchanged and no staged process remains; fewer
accepted trials is an incomplete pilot and any of these failures ends the case
`fail`. It declares its observations and judgment in the catalog
(`outcome_contract`) and ends `complete`, not `pass`. `paced_trials` publishes
the raw counts and timings with no verdict. `matched_pair_comparison` holds
the evaluated improvement, written to `conclusion.json`, and the advisory
judgment `candidate_improvement` reads it: favorable only when every compared
cell and regime has held-total pairs and each held-total series improves
beyond instrument uncertainty and beyond spread in every required pair. A
worsening, a withheld verdict, a run that compared no candidate and a dry run
are all recorded as unfavorable with the reason; an unfavorable advisory
judgment is displayed and never fails the case, and a dry run earns no
measurement credit. The default `dispatcher/controls` case runs the driver's
conclusion code on constructed matched-pair records with literal expectations
([dispatcher account](../dispatcher/README.md)).
`PW_WORKER_WAIT_PILOT_ARGS` passes driver options such as `--dry-run`,
`--cells`, `--repetitions`, `--regimes`, `--window-seconds` and
`--clock-pair-trials`; `--host-flavour inspection|optimized` changes only the
disposable hosts, retaining their actual settings in build and trial receipts.
Different flavours remain separate reader groups. `--window-gate` lets the coordinator freeze staged identities
and announce the window before releasing prepared trials. `--no-clock-pair` is accepted only in a dry run. A dry
run establishes mechanics only and removes its staged apps.

Comparison mode measures a baseline and a candidate as matched pairs.
`--compare-app PATH --compare-tree DIR` name the candidate's signed app and the
checkout it was built from; the wrapper then also builds the stamp worker from
that tree's worker source and passes it as `--compare-worker-build`. The two
apps are `baseline`, the selected app staged with the stamped host and stamp
worker built from this checkout, and `candidate`, the compare app staged with
a host built by the same patch set over the compare tree's `runner/` and with
that tree's stamp worker. There is no neighbor. The stager requires each app's
equipment identity and its stamp worker's reported identity to equal the
`WORKER_IDENTITY` its own tree declares, and records each tree's `HEAD` and
porcelain status in `staging.json`; the hosts' skipped optional patches are
announced and recorded. Five repetitions are the default; both regimes run with
baseline and candidate alternating per cell and their order alternating per
repetition, and both observe cleanup by the host exit event or, labeled, the
CLI exit plus 100 ms. `schedule.json` records the mode, the pairing rule and
both sides. The reader pairs a baseline and a candidate trial with the same
cell, regime and repetition index when both are accepted under the same power
source, Low Power Mode and host flavour, and lists every other trial as
unpaired. For each component present on both sides, the arrival, ack,
completion, done and inbound acknowledgement observations under one
`*_to_observation` name whichever form each side took, worker release and
activation passes and whole-request latency, it reports each pair's baseline
minus candidate difference and the sum of both sides' instrument
uncertainties (zero for pass counts; none for whole request), together with
each side's spread of that quantity, its maximum minus minimum over that
side's accepted trials in the group. Four verdicts judge the pairs:
`improves_beyond_uncertainty_in_every_pair` and
`worsens_beyond_instrument_uncertainty` against the instrument uncertainty
alone, and `improves_beyond_spread_in_every_pair` and
`worsens_beyond_spread_in_any_pair`, where an improvement must exceed the
candidate's spread plus that uncertainty and a worsening the baseline's
spread plus it, with `worsens_beyond_spread_in_every_pair` marking a
regression resolved in every required pair. Polled detections vary between
trials by far more than the instrument uncertainty, so identical apps can meet
the instrument worsening verdict and, with few trials, the any-pair spread
verdict; the every-pair spread verdict is the one an acceptance record treats
as a resolved increase.
Whole request has only the spread verdicts, beside the counts of pairs in
which the candidate was faster, slower or equal (`direction`). The grace counts
are paired as exact per-pair differences with each side's sum over the pairs,
without verdicts. Per actor, the worker's inbound scan counters are paired
as exact counts: `w<actor>.scan_visits_per_pass_<role>` and
`w<actor>.scan_loads_per_pass_<role>`, for the parked-activation and exchange
roles. A scan that starts every pass at index 0 visits all `n` inbound slots
except on a pass that ends by acknowledging slot `i`, which visits `i + 1`,
and makes at least one load per visit, so over `P` passes it makes at least
`n * P - n * (n - 1) / 2` visits and loads, its full-scan floor. Its visits
per pass are therefore fixed by its pass count, and the side with fewer passes
has the lower ratio without any change to the scan. A pair is lower only when
the baseline's count is at or above its floor, the candidate's is below its
own, and the candidate's count divided by its passes is strictly below the
baseline's by integer cross-multiplication; a pair that is not lower names the
conditions it failed. The verdict `lower_in_every_pair` is false once an
established pair is not lower and true only when all five declared pairs are
lower; a pair in which either side made no pass in that role is not
established. `w<actor>.scan_zero_visit_passes`, the histogram's zero-visit
bucket, is reported per side with each side's sum. Each actor's
`inbound_count` is the number of deliveries the trial layout addresses to it,
and its page's `INBOUND_ACKNOWLEDGED` events must name each of those slots
once (`inbound_observed`). A pair is refused when its `inbound_count` differs
between the sides (`scan_inbound_count_mismatch`) or either side's
acknowledged slots differ from the layout
(`scan_inbound_acknowledgement_mismatch`), and names each problem it has.
Groups carry each scan counter's sum and median per actor. An improvement verdict is
refuted by any established pair that falls short and is given only when all
five declared pairs pass; a worsening verdict is given by any worse pair and
refuted only when all five are established and none is worse; otherwise the
verdict is withheld. For `release_to_ack`, `activation_response` and the
custody rows' `inbound_response` (commit publication to recipient acknowledgement),
it compares `max(candidate value + uncertainty) - min(baseline value - uncertainty)`
against 2 ms. Credit requires every applicable response in every accepted trial,
the declared matched-pair count, each side's maximum uncertainty summed at most
0.5 ms, and the instrument gate. Missing responses are uncredited; missing
declared phases or deliveries refuse a completed pilot trial. Host export
version 2 requires commit-begin and post-store stamps. For version 1, the
enclosing custody-service start and wait-start stamps bracket the commit
conservatively. Host sleep and bounded-wait
counts and durations are reported per pair. The matched pairs appear in
`summary.json` under `pairs` and in a Matched pairs section of `summary.md`;
the two apps are never pooled. The comparison measures fixture builds of both
trees with one recorder; it does not compare distribution executables.

Artifacts include `conditions-start.json`, the worker build receipt, host
build and staging receipts, the clock-pair build and `clock-pair/` receipt,
`staged-identity-before.json` and `-after.json` (hashes, device and inode),
`schedule.json`, `window.json`, `warm/<app>/<cell>/warm.json`, per-trial
directories `trials/<app>/<cell>/<regime>/<index>/` with `RunCapture` files,
`trial.json` (with every driver wake), `conditions.json`, `started.json`,
`stamps.json`, `exported.json` when the host wrote its export marker,
`host-exit.json` and `validation.json` (with the envelope's millisecond fields
for both apps), the reader outputs, `cleanup.json` (processes found under the
staged bundles and any action taken), `pilot.json` and `conclusion.json`.
The case is opt-in because it builds and signs disposable hosts and its
timings are sensitive to competing load, so it needs a quiet window.

### Worker wait pilot controls

The default `worker_wait_pilot_controls` case is a
[pytest family](../../README.md#pytest-families) in
[test_worker_wait_pilot_controls.py](test_worker_wait_pilot_controls.py).
[worker_wait_pilot_constructed.py](worker_wait_pilot_constructed.py) builds its
receipts, and the dispatcher's constructed comparison takes its bundles from the
same module. Each item's identity is `<Group>.<function>`, followed by a label
where the function runs once per input, so each constructed fault, order rule,
pooled key, missing file and malformed minimal export reports its own result.
Expected values are literals written from the constructed microsecond times;
none is computed by the reader. Collection imports neither the reader, the
clock pair nor the stager and creates nothing. An item that replaces a reader
or stager function does so through a fixture that restores the original at
teardown and checks that it returned. A disk scenario writes its tree into a
temporary directory of its own, registers it before the loader reads it and
captures it before removal. Three stager items run real commands at the
engine's supervised boundary, the `ditto` copy and the stand-in worker's
`--version`, five commands in all; the stager's own receipt directory is each
command's artifact directory, and the constructed inputs and staged copies stay
under `artifacts/stager/<identity>/`. Every other item declares no commands.
The family needs the pinned test packages that `tests/setup-pytest.sh`
provisions.

The family publishes `artifacts/controls.json` after its last item: the
`accepted` names, the `rejected` controls with the status and codes each
reported, `not_established` for every declared name with an item that did not
record it, and `items`, which maps each item identity to the names it declares
and, for a refused control, the status and codes it recorded. A name is listed
as accepted or rejected only when every item declaring it recorded it, so a
failing item moves its names to `not_established`. The account's scope is
constructed reader sensitivity; it credits no live stamp or timing. Beside it,
`summary.txt` lists item and phase outcomes, `family.json` is the family
report and `artifacts/inputs/` holds each item's input snapshots.

The controls construct complete ordinary, actor
and neighbor receipts, with worker events in program order and the clock
pair's own constructed calibration receipt, and checks decoded values,
intervals and uncertainty arithmetic. It then rejects a wrong page magic or version, capture-refused and
overflow pages, non-monotonic worker events, a host observation earlier than
the worker publication, a missing stamp or start file, a truncated page,
dropped host stamps, a page copied before reap, sleep overlap, pacing out of
range, a power transition, neighbor stamps, a page-count mismatch, a rejected
calibration receipt and pooled groups. It also exercises a counted sub-50 µs
inversion that widens the alignment term, a host pid mismatch between the
start marker and the export, an arrival with no negative sample, pooling across
cells, power sources, low power mode and flavours, a calibration receipt whose
endpoint-bracket outlier exceeds the gate, the per-wait pass events and
pre-store host stamps, and the reader with its uncertainty arithmetic replaced
by the earlier formula, which must fail. Combined faults keep every code. Constructed
comparison rows must give an improvement verdict when the candidate's arrival
and held total are shorter beyond uncertainty and spread in every pair, none
when one pair is within uncertainty, an instrument but no spread improvement
when one pair falls within the candidate's spread, an instrument but no spread
worsening for a pair worse within the baseline's spread, both worsening
verdicts for a pair worse beyond it, a withheld
improvement with fewer pairs than required, an uncredited response bound
beyond 2 ms or without the resolution or the gate, unpaired trials for an
excluded side or differing conditions, and neither verdict for identical
receipts, and they must fail when the reader's spread term is replaced by
zero. Candidate-shaped ordinary receipts carry the grace program points and one
exit wait followed by each outcome, or by none; the controls check the counts,
the per-actor intervals and the group sums, count waits past 64 recorded pairs
and 10 ms plain sleeps as timeouts and 100 µs plain sleeps as settle sleeps, and
reject an outcome code of 3, an outcome that
does not follow its pair (moved, another key or another raw) and a grace
finished before it begins. A candidate-shaped A2 receipt gives each actor its
own exit request, reaping sample, grace program points and stop code, with one
notified and one timed-out exit wait; each actor's three intervals and stop
code must come from its own events, and the reader with lookups that match those
events without the actor, or only the stop without it, must fail. Constructed whole-request values check the
direction counts, and constructed counts the paired grace differences.
Constructed A2 receipts with inbound scan counters must give
`lower_in_every_pair` when the candidate's subject visits and loads per pass
are lower in every pair and below its full-scan floor, withhold it with fewer
pairs than required, refute it for a pair equal to its baseline and for
identical scans on both sides whose pass counts differ (two full scans, and
two scans below their floors, each with the lower ratio on the side with fewer
passes), separate a ratio that rounds to the baseline's as a float, refuse a
pair whose subject `inbound_count` differs and a pair whose candidate page
lacks one slot's acknowledgement, and sum and take medians of the counters
per actor in a group; the reader with a float ratio comparison, or with a lower
ratio credited without the floor conditions, must fail. A comparison's receipts go through the loader and writers with
separate app groups. The stager, given a constructed candidate app and source
tree and stopped before any copy is signed, refuses an equipment identity or a
stamp worker identity that differs from the tree's declared one.

## Public phases

`phases` uses the signed CLI with ordinary actions. It unlinks a controlled
file, observes its absence outside PW, then requires fresh planning to withhold
the next native path query while the paired access reports ENOENT. A final
resolvable target requires a fresh validator record and `query_first`. The
reply must retain one worker, distinct collections and all completed phases.
Mutations reject wrong phase association, borrowed records, duplicate IDs,
wrong ordinal, broken completion sequence, a wrong action partition and malformed phase field types.

The same registered case compiles the bounded validator fixture in its owned
temporary target directory and retains a copy with the artifacts. It drives
aggregate timeout and stdout byte cutoff, requiring a received fixture record
before each cutoff so a blocked launch cannot satisfy the control. It asserts
supplied override echoes, real collection stop/reap evidence, unavailable later
predictions, and retained successful attempts. These are driver controls, not
sandbox predictions.

## Native path-query observations

The opt-in `path_query_observations` investigation uses the shipped validator
against a separately signed native target, bypassing host query planning without
changing the app. It pairs default-allow and narrow-deny policies across literal,
subpath and regex predicates, four file operations, and nine path states:
existing, absent leaf/parent, dangling leaf/parent symlink, symlink loop,
non-directory component, non-searchable parent and mode-zero file. Existing
anchor paths accompany each query batch. Separate same-PID controls query and
attempt through unlink/recreate under one fixed policy.

Host `realpath` and errno, raw validator records, syscall results, independent
file state and exact child cleanup remain separate. The case asserts equipment,
framing, coordination and observed effects, not prediction/enforcement agreement
or a universal API outcome. This is exploratory native evidence, not a product
eligibility-rule change or acceptance gate. Targets stay under `/private/tmp`.
See the [fixture](../../fixtures/path_query/README.md) and
[path-query observation account](../../CHANGE-VERIFICATION.md#native-path-query-observations).

The separate opt-in `path_query_integrated` case retains extra native query
receipts against the actual PW worker through a validator wrapper. It forwards
only requested verdicts to the host, so the planner's unavailable results remain
unchanged. Three specimens cover same-worker unlink/recreate, absent-leaf create
and dangling-symlink unlink; independent effects, production consumer validation
and cleanup are checked. The validator's copied executable bytes are unchanged.
This isolates integration relevance while explicitly changing collection timing.

## Native extension boundaries

`extensions` executes the public guide's actual extension example as well as
issuance by an unentitled unapplied actor, native consumption and release
in a selected applied actor, with fresh descriptor identity, bounded bytes and syscall results
on either side of both interventions. Each phase collects its own queries.
Native return values and observed access remain independent evidence.

The same case covers omitted lifecycle actions, same-phase and cross-phase
placement, intervention-only phases, native issuance for missing paths, literal symlink targets
and replacement between issuance and consumption. An independently
held, non-inherited descriptor keeps the removed identity observable while the
worker creates a replacement. Later reads report their actual identity and bytes;
the test does not require release success to revoke access.

`extension_directory` compares directory read-write authority with omitted
consumption, missing predicates, another directory and explicit read authority. Each row first establishes ordinary permissions through
the public fresh-write actions, then restores existing contents and removes the
baseline children before issuance. Separate names serve before-consumption,
during-consumption and post-release attempts. Before-launch absence plus
`create_fresh`'s immediate lstat and exclusive open keep new creation distinct
from opening an earlier child. External final reads happen before reply
interpretation and survive failed assertions; they establish persistence after
release and worker exit. Fresh post-release results have no required pattern.
The absent child keeps its unavailable prediction. A killed-before-publication
write leaves an independently observed effect while withholding its native
result payload. Unknown worker cleanup retains owned staging and a durable
ownership record outside prunable run output.

The opt-in `actors_byoxpc` case uses one owned installed-runner session for
shared lifecycle, directory, ordinary phases, maximum replies and re-delegation.
It independently reads selected and unentitled signatures and entitlement
plists, compares sealed source/installed inventory with registry snapshots,
and checks dossier hashes against installed bytes and the shipped baseline.
An explicit mixed-equipment calibration binds each actor to its static role,
launch PID and live executable inspection; renamed/reordered actors preserve
that association, while a same-selected contrast must fail the expected
unentitled-role assertion. A missing installed selected worker retains an
exact-byte restoration receipt and checks public validation before and after
restore. A service-seal refusal is retained honestly if it precedes role binding.
An ordinary five-actor workload covers all four equipment/application pairs
and omitted equipment selection. Signed false and absent requirement keys
refuse through both the CLI and direct XPC, even when the controller's separate
selected-worker requirement passes; per-actor decisions and absence of launch
and file effects remain independently checked. Unreadable readback branches
belong to controlled Swift inspection tests, not these live signing observations.
These controls establish no prediction/enforcement agreement or revocation claim.
Cleanup verifies service removal. Targets stay in owned temporary directories.

`extension_boundaries` compiles two production actor workers with the
[controlled native entrypoints](../../fixtures/extension_controls/README.md).
The clang test build uses `PW_EXTENSION_OBSERVE` outside the inspected app.
These controls establish boundary behavior of those instrumented sources;
they do not interrupt the shipped executable bytes or observe private API internals.
It drives native refusal, absent issue/consume/release APIs, issuing-actor death,
malformed outbound and inbound slots, and interrupted consumption/release through
the CLI. Required worker setup failures cover the core limit, descriptor
metadata, mapping, close, object size and header binding. `authority_setup`
retains the primary operation and independent cleanup cells with actual native
returns and errno. A terminal required failure excludes policy processing and
produces the corresponding actor application assessment. Missing symbols remain
separate operation-availability facts. Independent receipts distinguish death
after the pre-call marker, inside a replacement function, and after the real
native return but before publication; earlier completed evidence survives.

Termination controls keep an issuing actor alive after final completion and
`done`, exceed the gate deadline, or exit abnormally after completion. Dependent
activation requires the source's owned reap. A timeout stays closed after later
cleanup; a natural abnormal exit can satisfy termination without proving clean
completion. Activation, immutable owned-reap and gate-capture ordinals establish
the observed ordering.

The test compares real token bytes with captured output in memory before saving
output, checks argv/environment confinement, production descriptor closure and
buffer erasure, and retains only observations. A deliberately contaminated
in-memory string checks detector sensitivity. Raw tokens never enter fixtures.
The observer's ownership receipt records cleanup; an unconfirmed native child
retains its named channel and recovery record.

`extension_combinations` reads the M rows of the shared comparison matrix. It combines
published issuance with abnormal exit, worker death during mapped-token validation,
same-phase consume failure with omitted release, cross-phase release failure,
and native-call interruption with earlier ordinary observations. Independent
receipts and both readers check each row; Swift comparison tests read the same
expectations. Recipient validation interruption occurs after usable actor setup but before
inbound acknowledgement. Its unresolved delivery and later unactivated visits
remain distinct from terminal authority setup failure.

The ordinary-phase combined control is in `runner_unit` (`PhaseProtocolTests`):
a real validator times out, a substituted termination call fails, and its late
write observes EPIPE while a fresh next-phase validator runs. The retained reply
keeps the first child unreaped and each phase’s records separate; the test owns
independent child cleanup. Rust assembly and the Python consumer/oracle replay
that production-encoded reply. The fixture’s query answers are controlled data.

## Principal policy qualification

`extension_policy_qualification` compiles the principal re-delegation
specimen's B policy with the bundled `sbpl-check` helper, then applies the same
bytes once in a fresh worker through the ordinary single-worker run path with a
baseline `read_fresh` of a test-owned file. The policy denies ordinary reads of
the target and permits issuance only under a consumed read extension; the
denied baseline read, its `deny` prediction and the collection/release chain
are the application observations. An independent run under an ordinary
allowance shows the same target is readable. The bytes live in
[extension_actors.py](../../lib/extension_actors.py), which the principal
acceptance specimen also uses, so the qualified bytes and the submitted bytes
cannot diverge. Retained: the policy and its hash, helper envelope, both run
envelopes, commands and environment. Compile success alone establishes neither
application nor extension-dependent issuance; this case establishes
compilation and application on the recorded equipment only.

## Principal re-delegation acceptance

`actor_compositions` runs public specimens with distinct file contents and
identities across multiple issuers, fan-out, repeated consumes, separate handles,
self-transfer and empty revisits. A second request reverses actor declarations
and consistently renames references. Exact request-to-reply inventories, full
readers, policy hashes and per-process fresh observations must agree. The case
also retains a recipient's compilation failure while unrelated actors continue.
Optional per-actor compiled-profile receipts are checked against the requested
nonce, process, source and captured bytecode; a failed application remains an
unavailable capture. A changed producer context is rejected by the reader.
The positive cases require issuance/consumption/access coverage; a native refusal is
retained as missing coverage, never reclassified as sandbox enforcement failure.
An intervening release is observed without assuming it revokes access.

Two additional three-actor requests distinguish an evaluated gate failure from
an unreached gate. The first uses the existing post-apply sleep override to
keep the source alive after its final phase completes, through the normal
five-second termination wait. It requires global schedule cancellation: both
the dependent and a later unrelated actor retain unactivated phases,
uninvoked validators and terminal unpublished attempt records. Source cleanup
reaps after the failed gate closes. The second gives the dependent invalid SBPL:
its compilation failure leaves the gate unreached, and a later unrelated actor
must complete a fresh read of the known contents and file identity. Both
requests require output collected after a confirmed reap for all three workers.
The captures exercise the signed candidate's production scheduler and native
workers; the first request supplies a deliberate sleep through the test seam.

A paired ordinary/actor control supplies `worker_timeout_ms: 200` and
`worker_post_apply_hang_ms: 500`. The ordinary empty phase completes after
application, then its recorded 200 ms sentinel allowance expires. The actor
request keeps the normal setup/execution allowances: source completes an empty
phase, a natural owned-reap gate admits reader, and reader obtains the known
fresh-file bytes and identity. Charged actor execution exceeds 200 ms while its
recorded allowance remains 120,000 ms. The file observation and gate/reap
association accompany that timing discriminator; the requested sleep alone
establishes neither its reached boundary nor an elapsed duration. Both captures
require confirmed worker reaps before the existing fixture cleanup. Final done
and natural exit during grace accompany the earlier ordinary sentinel timeout.
Both actors leave on request within the grace: each carries
`cleanup_trigger: completion`, whether its stop reason is `done` or
`schedule_complete`, and a null cause.

Two single-actor requests distinguish how an actor ended. With
`worker_kill_before_publish_slot: 0` the worker signals itself during its
visit: the stop reason `died_before_completion` is carried unchanged as the
trigger, `grace_end` is `not_entered`, no termination request exists,
`owned_reap.departure_requested` is false and the cause is `unknown`. With
`worker_post_apply_hang_ms: 3000` the worker sleeps past the 1,000 ms exit
grace after its phase: the record carries `poll_stop_reason:
schedule_complete`, an exhausted grace, a SIGKILL request with `rc` 0, a reaped
signal 9 and `departure_requested: true`, and must carry `cleanup_trigger:
completion` with `termination_cause: host_exit_grace_exhausted`. The
cancelling gate request's source, which sleeps past the same grace, must carry
the same trigger and cause. The requested sleep and signal are test-seam
controls; the records are the production scheduler's.

`extension_redelegation` runs the principal three-actor specimen through
the public CLI against a test-owned file, then a positive calibration and four
narrow contrasts. The witnessing assertions concern the apparatus: `A`, `B` and
`C` are distinct fresh processes whose parent is the host; `B` and `C` applied
the exact qualified policy bytes once (the host's hash, the worker's hash of
the bytes it read and the hash of the source agree) and `A` applied none;
every phase arrived and completed without protocol violations; every ordinary
query names its actor's PID and established `query_first`; every extension
action published; the second delivery is bound to `B`'s issue and `C`'s
consume to that delivery; every launched actor was reaped. The kernel's
answers are recorded, not forced: a published NULL issue, a failed consume or
a denied read passes those assertions. Re-delegation is credited in the report
only when the whole chain published and the fresh reads returned the known
bytes where the baseline reads had failed; otherwise the report names the first
link that broke. The calibration (an unapplied issuer supplying an applied
reader under a simple consumed-extension allowance) must exercise real
issuance, delivery, consumption and access on the host, or the case fails and
the positive coverage is missing. The contrasts omit `B`'s consume, remove
`B`'s issuance allowance, omit `C`'s consume and omit `C`'s extension
predicate; each must still publish its remaining links and must not be
credited, and their observations are retained beside the principal run for
comparison. Retained: every envelope and specimen, the target's identity and
`report.json`.

`actor_timing_qualification` measures the actor profile on the signed
candidate with the actual polling implementation and every actor launched
before the first phase: three matched rounds of one-, three- and eight-actor
specimens sharing one aggregate fresh-read workload distributed over the
actors, a workload at the aggregate action and phase limits over eight actors,
and the principal re-delegation and calibration shapes with five further live
actors servicing bounded ordinary phases. Every run must complete without
budget exhaustion, and each measured interval must leave at least a quarter of
the allowance it is compared against: setup, charged execution, aggregate
collection, the host arrival-to-release proxy, host recipient wait, and setup
plus elapsed schedule execution. The last measurement includes collection time
but excludes final cleanup and the interval between cutoff creation and setup
clock start; it is not a whole-lifetime measurement. Recipient wait does not
measure the worker's custody-acknowledgement or transfer-answer waits. These
intervals come from the reply's schedule, visit timing and transfer records:
host scheduling and publication measurements, never native call latency. The
finite workloads do not establish margins for every admitted composition. The
eight-actor executions keep the chain and calibration assertions. `report.json`
retains the hardware's CPU topology, OS, power and load, every measurement and
margin, and the actor PIDs. A deliberately slow or hung specimen is a different
control; it is not expected to meet this margin.

The same BYOXPC case also launches an owned selected-worker override in a
minimal App Sandbox-signed bundle. An `unapplied` actor cannot read the owned
target while it reads a system file; the ordinary worker and test process can
read the target. The signed entitlement and per-actor instrumented binding are
read independently. A preexisting container is left untouched; a potentially
new container has a durable receipt outside prunable staging, retained until
process cleanup and container absence are established.

## Invariants

- The suite is included in the default battery, including regression guards
  against re-introduction of removed request fields (`instrumentation`) and
  runner modes (`runner.mode=debuggable`).
- `happy_path_baseline.sh` is the regression sentinel — it must pass
  in every run. If it fails, stop and investigate before continuing. A failed
  envelope expectation ends it `fail`, naming the expectation and
  `artifacts/assertions.log`; any other error in its assertion block ends the
  script without a terminal report, which the dispatcher records as unrun.
- Tests are stateless: named for what they assert, not for any
  plan-row number.

## Success criteria

- Every test passes.

## Fixtures

- Specimens are generated inline per test.
- `happy_path_baseline` uses a stable `(version 1) (allow default)`
  policy with one file read step.
- `bug_report_returns_verdicts` runs the `(version 2)(deny default)(allow
  file-read-data)` specimen whose worker clock once failed after application.
  Beside the `allow` prediction it requires successful application, no worker
  failure record, the collection/release/acknowledgement chain, the worker's
  published attempt, `query_first` and a confirmed clean worker exit. The open's
  actual rc/errno is retained and validated without requiring success: a
  completed permission failure is valid evidence. Descriptor-derived path
  evidence is checked when present. The `(version 2)(allow default)` neighbour
  is the positive open/path control. Prediction and attempt assertions stay
  independent; neither establishes agreement or universal permission.
- The validator shortfall and decode-failure cases share the checked-in
  `tests/fixtures/validator` transcripts and `runner_validator_failure`
  contract checks. Both require reversed partial verdicts to retain step
  association, all three completed attempts to retain their actual outcomes,
  and the unanswered prediction to have an explicit error and missing reason.
  These two cases also run in the baseline `runner_validator_failure` suite.

## Independent prediction and attempt targets

`prediction_target_is_independent_of_attempt_target` runs two ordinary CLI
specimens with the real validator and no test overrides. Both attempt writes to
two existing files: the policy allows A and denies B. After restoring the same
seed bytes, the second run swaps only the prediction targets. Policy, attempts,
and random step IDs stay fixed. The test reads and retains external file bytes
before decoding PW's JSON: A must change to nonempty data and B must retain every
seed byte in both runs.

The matching run requires an allow answer beside `observation: succeeded` and
a deny answer beside `permission_failure`, both `same_submitted`. The swapped
run retains both answers and attempts with `target_relation:
different_submitted`: the record names the difference and judges nothing.
This checks independent channel routing without promoting pairing to comparability.
Redirecting a validator query to `attempt.target` must fail even if the envelope
continues to echo the requested filter value. The existing classifier and
steered-validator tests retain their separate contracts.

The case checks step identity/order, raw attempt evidence, prediction and
attempt paths, worker/validator completion, and the comparison record.
Both run summaries must report `finished` beside the successful and denied writes.
Shared black-box checks collect both prediction failures rather than stopping
after the first mismatch. `RunCapture` retains each request, raw envelope,
stderr, and capture metadata under `matching/` and `swapped/`; these directories
also contain expectations, byte snapshots, and diagnostics. The case needs the
built app and live XPC; missing equipment fails.

Run it independently with:

```sh
tests/run.sh --case witness_contract/prediction_target_is_independent_of_attempt_target
```

## Create on an existing file

`create_existing_file_preserves_contents` submits two `file/create` attempts
through the CLI, using the real validator and no test overrides. Both targets
already contain distinct random bytes. Policy allows writing one and denies
writing the other. The allowed attempt must succeed with its observed path;
the denied attempt must report `open_failed` with a permission errno. Their
predictions must be allow and deny respectively, with `operation_relation:
unresolved` for the compound create scope.
Both children exit cleanly and the steps retain their identities and evidence.

Before decoding the envelope, the test independently reads both files and
checks that every seed byte and each device/inode pair survived. This protects
create's existing-file semantics: open for writing without truncation,
replacement, or an exclusive-create requirement. The denied-write step also
rejects substituting a read-only open that would preserve the bytes.
`runner_c_worker_harness/create_allow` separately covers creating an absent file.

Artifacts include before/after bytes, `identities.before.json` and
`identities.after.json`, the specimen, expectations, raw envelope, stderr,
capture metadata, and assertion log. Run with:

```sh
tests/run.sh --case witness_contract/create_existing_file_preserves_contents
```

## Predictions before attempts

`queries_precede_attempts` runs an allowed read and unlink of
one file with the real validator and no overrides. Both native predictions must
be allow with `query_first` beside `observation: succeeded`. The test observes file
absence before decoding, and retains later host nonresolution separately as
`sandbox_check.path_diagnostics.realpath_resolved: null`. A later-step unlink
in that same phase is read from `order` and the unlink step's own result
(reading rule 6), pinned by the matrix rows and consumer controls. Cross-phase
sequencing instead requires phase boundary publications; `phases` checks an
unlink/recreate followed by a later native query with its own `query_first`. The
stronger gated observer and deliberate barrier-bypass controls are
separate tests; this ordinary run alone does not replace them.

`queries_use_a_pre_attempt_interval` covers absent/create/unlink,
existing/unlink/read, and unlink/recreate/read plans. An absent planning target
has no query; removing an existing target preserves the earlier native allow
prediction beside ENOENT, state and identity limits. Recreating the path cannot
erase the recorded unlink or certify runtime identity. Create remains a compound
attempt with an unavailable comparison even when the native prediction is allow.

`attempt_effects_wait_for_collection` uses the native bridge's acknowledged query
and emission gates. While stdout collection stays open, independent file reads
must retain the target bytes and the exec helper must have no connection. After
closure, unlink and helper connections must occur; kernel peer PIDs, libproc
ancestry and kqueue exit events identify the helper, worker and host. Only then
does the checker inspect the envelope. This proves the barrier for the observed
unlink and exec effects, not the absence of every possible syscall.

`query_interval_is_not_a_snapshot` removes a target between two acknowledged
native queries. `external_mutation_between_query_and_attempt` removes it after
a native allow receipt while collection remains open. Both retain real native
observations and state/identity limits; test-only mutation knowledge is not a
production attribution. No specific native verdict is required for a missing
target. The resulting ENOENT read is an `other_failure` observation beside the
earlier allow answer; the record relates them and judges nothing.

`max_steps_ordered` runs 256 distinct existing targets, half denied for writing
by literal, and independently checks every file's bytes before decoding.
`deny_default_ordered` checks an allowed and denied read under `(deny default)`.
Both require eligible predictions to be `query_first`; allow/`succeeded` and
deny/`permission_failure` records stay distinct, with no judgment of agreement.

`max_targets_reply_survives` measures admitted 256-action workloads: denied
ASCII reads of 511-byte targets, successful reads of
JSON-escaped paths with observed paths, independent 511-byte query paths
against plain attempt targets, 256 execs with stdout/stderr, and 256 native
execs with 511-byte escaped executable targets and independent query paths,
63-byte step IDs, maximal metadata, live profile capture and 1,023-byte
stdout/stderr streams made of U+0001 (six JSON bytes per input byte). The
same workload with streams of 0xFF returns 1,023 U+FFFD for each stream, the
largest binary stream text at three bytes per retained byte, and has the same
margin check.
The explicit phase workload repeats collection across eight boundaries. Fresh-read
workloads use 256 ordinary reads or 254 reads plus consume/release sharing the
same action capacity. They compare returned prefixes and descriptor identities
with independent file observations and require actual native lifecycle results.
These require complete replies and exact targets, outcomes and applicable
output; the control-character workload also requires every prediction to
round-trip through the real validator. Every observed host binary reply must fit
its retention and frame limits; the separate client frame must fit the controller
retention allowance. The maximal-metadata workload adds a conservative profile
receipt allowance to the observed host size and checks the remaining retention
margin. Dense typed fixtures and independent public projection accounting cover
additional constructed populations. These observations are not a proof of a
global reachable binary maximum.
Four refusal workloads submit 32,768-byte query values or filter/attempt labels.
Each requires a host-owned `admission_failure` naming the field, no steps and no
worker or validator subprocess. The label controls place a valid write before
the invalid label and independently require every target to remain unchanged.
Every workload records the host reply's raw bytes and the client's stdout bytes
(the binary capture carrying opaque host bytes, bounded by the receiver budget)
separately and requires an untruncated receiver; refusal replies must be smaller
than 4 KiB. Every echoed request string is
admission-bounded, so these measurements are the evidence for the cap's margin
rather than a closed-form maximum. The exec cases use the independently controlled
`tests/fixtures/exec` helpers and require clang. The byte-stream helper is
checked directly for several fill bytes before the stress workload. Every step execs: the worker
raises its soft descriptor limit pre-apply to fit the four pipe descriptors
each exec step prepares (see `exec_step_descriptors` in `docs/LIMITS.md`).

`max_exec_steps_spawn` runs 256 exec steps of `/usr/bin/true` through the
CLI and requires every attempt to report a clean child. Under launchd's
default soft limit only 62 exec steps could open their pipes before the raise
existed; the case records any step that did not spawn.

The bridge is test equipment selected through the existing executable override;
its direct protocol/native controls live in `validator_bridge`. The opt-in
`order_barrier_mutations` case builds unmodified and patched workers and hosts
outside the inspected app. Baseline component and CLI controls must pass. The
worker wait bypass must fail the ordinary C quiescence assertion; the host early
release must fail the same Swift gate control used by `runner_unit`. Both signed
app copies must produce early unlink and exec effects under the same CLI
effect assertions. The worker bypass publishes arrival, then waits on a test-only
file gate opened by the observer after the validator connects. This places the
fault inside the held collection instead of letting the host reject premature
publication before any collection starts. The direct C control opens that gate
before launch and must still detect the missing worker wait. Hashes, signatures, source patches, command logs and effect receipts
are retained. See [ordering-control applicability and prerequisites](../../CHANGE-VERIFICATION.md#order-barrier-mutation-controls).

The unmodified C scenario must complete its 500 ms hold before release. A bypass
can complete before the first poll: `early_completion` then rejects it immediately,
even with zero held milliseconds and no host release. That observation establishes
premature completion; the baseline supplies the delayed-release coverage.

`validator_spawn_failed_reports_degraded` requires real ENOENT from
`posix_spawn(sb_api_validator)`: the structured native return code, executable
path, operation and nonempty diagnostic, without requiring English wording.
It also requires the mirrored hostile executable path, no validator
subprocess, closed collection with `not_spawned`, unestablished step order,
and an independently changed file after the released write.

## Completed observations after a worker timeout

`worker_post_apply_hang_seam` attempts an allowed write and a denied write,
then uses a post-apply hang longer than the worker deadline and reap grace.
The host reports `runner_timeout` and SIGKILL termination, with CLI/runner
failure, a deadline diagnostic, and both overrides echoed. Independent file
reads must show changed, nonempty bytes for the allowed write and intact seed
bytes for the denied write before the envelope is decoded.

Both completed attempts retain their distinct outcomes, step IDs/order, paths,
errno evidence, matching real validator predictions, `observation: succeeded`
for the allowed write and `permission_failure` for the denied one.
The validator exits cleanly and `partial_steps=false`: failed run completion
does not erase completed observations. The shared checker, timing margins,
and retained artifacts are documented in `runner_outcome_runner_timeout`.
That suite owns the deliberately empty-plan timeout control;
`runner_use_c_worker/worker_timeout_ms_honored` covers a single successful write.

## Attempt in flight at the deadline

`worker_attempt_in_flight_at_deadline` runs three specimens
under `(version 1) (allow default)`:

- `a1`: a FIFO with no writer, then `/etc/hosts`, with `worker_timeout_ms: 2000`.
  Attempt 0 blocks inside the worker until the sentinel deadline; the second
  step is never reached. The envelope records `poll_stop_reason:
  sentinel_deadline`, `termination_request: {rc: 0, signal: 9}`,
  `term_signal: 9`, `reaped: true` and the attempt 0 started progress word.
  The check asserts those witnesses and the echoed override as setup and
  preserves `runner_timeout`, the deadline and SIGKILL error clauses and the
  `signaled` disposition. It then requires
  `runner_sandbox_diagnostics.termination_cause` to equal the
  `HOST_SENTINEL_DEADLINE` constant from `tests/lib/lifecycle_contract.py` and
  forbids `unknown` or any value attributing the signal to the sandbox.
- `a3`: `/etc/hosts`, the FIFO, `/etc/hosts`. The same host witnesses appear with
  progress at attempt index 1, and the completed first step keeps `outcome: ok`,
  `result_source: worker`, `rc: 0`, `order: query_first` and empty limitations.
- `a4`: `/etc/hosts` with `worker_timeout_ms: 300` and
  `worker_post_apply_hang_ms: 800`. The deadline fires and the worker exits 0
  during grace: `sentinel_deadline`, `exit_code: 0`, `done_observed: true`, no
  termination request, `partial_steps: false`, the completed result,
  `runner_timeout`, a `clean_exit` disposition and a null cause all coexist,
  and the error names the deadline with "no termination requested".

The per-step compatibility triples are recorded in `compatibility_triples.json`
without assertion. The lifecycle checks are gated on the reply's response
version (a producer before the record fails as version gating), require an empty finding list from
`tests/lib/lifecycle_oracle.py` on each envelope (written to
`oracle_findings.json`), and assert through `tests/lib/lifecycle_adapter.py`
that `a1` reports `started_without_result` then `not_reached`, `a3` reports
`completed`, `started_without_result`, `not_reached`, and `a4` reports
`completed` with `stop_reason: sentinel_deadline` beside `clean_exit` and a
null cause.

Each FIFO lives in test-owned staging under `/private/tmp` that the check never
opens. Once CLI launch is attempted, staging is removed only when the envelope's
`reaped: true` and valid worker PID witness exit (`tests/lib/worker_exit_witness.py`).
A missing or malformed subprocess record leaves staging retained. `staging.json`
records ownership before capture, and `cleanup.json` records removal or retention.
Setup failure before launch permits removal on the test's own non-spawn observation.
Reused artifact directories are refused before creating staging. Cleanup reporting
failures name the recovery path in stderr and preserve the original failure.

## Death after the native return, before publication

`worker_killed_before_slot_publication` runs one specimen under
`(version 1) (allow default)`: `/etc/hosts`, a `create`
of a fresh file in test-owned staging, then `/etc/hosts` again, with
`worker_kill_before_publish_slot: 1`. The worker's `open(O_CREAT)` returns and
the slot's fields are written; the seam then raises SIGKILL before the slot's
`completed` flag. The check observes the created file itself before reading any
JSON, so the native operation is established independently of the reply.

The reply must withhold what the worker never published: the second step is
`no_completed_result` with `rc: -1`, null `errno`, `result_source: synthetic`,
`missing_reason: slot_incomplete`, lifecycle `started_without_result` and
`observation: unavailable`, and its `error` text makes no claim that the
operation did not run. The completed first step keeps `outcome: ok`,
`result_source: worker` and `observation: succeeded`; the third step is
`not_reached`. Host witnesses establish the position: `poll_stop_reason:
child_reaped`, `term_signal: 9`, `reaped: true`, `done_observed: false`,
`partial_steps: true`, the attempt 1 started progress word and no termination
request; `normalized_outcome` is `runner_failed`, the disposition `signaled`
and the cause `unknown`. The echoed override is setup only. The independent
oracle must return no findings and the adapter must read `completed`,
`started_without_result`, `not_reached`. Staging cleanup follows the in-flight
case's rule: removal requires the envelope's reap witness.

## Failure before published application

`pre_apply_failure_reports_no_policy_verdict` runs the same two-file specimen
twice with real worker/validator binaries. Policy allows one write and denies
the other. The failure run uses `worker_pre_ready_hang_ms=10000` and
`worker_timeout_ms=200`: the delay exceeds the fixed 1s ready-byte wait,
sentinel budget and 1s exit grace by a wide margin. The seam sleeps after
compilation and optional profile capture, before the ready byte and application;
it provides no evidence of compilation failure.

The failure run must retain its subprocess and both overrides while reporting
no observed compile/apply return, allow/deny prediction, completed attempt or
comparison record. The positive control removes only the overrides and requires
allow/`succeeded` and deny/`permission_failure` records. Independent file
reads precede JSON checking: both seeds survive the failure run; the positive
control changes the allowed file and preserves the denied file. Both runs must
avoid a sandbox-termination claim and carry no `deny_signal` or `drift` key on
any step. Missing attempts use the outcome
`no_completed_result`, meaning no completed result, without saying whether the
operation started.

This is the one case steered by a control that is exempt from the exact-outcome
assertion in the recipe of the [runner guidance](../../../runner/AGENTS.md).
It checks that `normalized_outcome` excludes `finished` and `bad_policy`, and the
spellings `sandbox_apply_failed` and `runner_sandbox_denied` that no constant
defines, rather than pinning one replacement outcome, so it protects the
absence of library/policy claims across outcome renames; classifier tests pin
the mapping. It keeps the recipe's other
assertions: a real failure artifact in the error, both mirrored overrides,
subprocess and missing-step evidence checks, and the un-overridden positive
control. Optional subprocess objects may be omitted or null; a null per-step
`errno` requires key presence.

`check_pre_apply_failure.py` collects separate attribution, step/process evidence,
file-effect, lifecycle and cause assertion groups in `assertions.json`. Lifecycle
groups check polling reason, ready/done observations, termination-call results,
successful reaping and wait-error arrays through the signed CLI. A failing
group does not prevent the positive control from running. Any failing group
fails the case normally; it is never converted into a pass or skip. This case
enforces the [failure evidence contract](../../FAILURE-PROPAGATION-CONTRACT.md).
Consumer checks distinguish missing results from observed failures, retaining
both missing reasons and all simultaneous comparison limits.

Artifacts include `pre_apply/` and `positive_control/` requests, raw envelopes,
stderr, CLI capture metadata and before/after file bytes. The checker also
records `prediction_observations.json`. The consumer checks require
`validator_not_invoked` beside `slot_incomplete`; the validator-failure cases
separately require `validator_no_verdict` beside completed worker observations.
Run with:

```sh
tests/run.sh --case witness_contract/pre_apply_failure_reports_no_policy_verdict
```

## Worker termination

`worker_termination` runs repeated writes that fail with permission-shaped
errors beside successful independent read queries, with both probe plans and
ordered phases. A controlled worker self-signal remains separate from those
attempts; a successful worker exit supplies the positive control. The case
checks unchanged target bytes, per-phase release ordering, raw predictions and
attempts, signal/exit facts, observed reaping, independent consumer recovery
and execution diagnostics. It asserts that collection fields are absent.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/witness_contract/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite witness_contract
```

Included in the default battery. The catalog shares the two partial-validator
failure cases with `runner_validator_failure`, executing each canonical case once.

`worker_progress_and_failure` checks real-worker success and compilation failure,
plus an external ABI fixture whose unfamiliar operation/code/native-kind values
survive the host, XPC client and controller. Its fixture establishes transport
only; the success run checks independent file contents.

`worker_sparse_failure` checks admitted-size policy transfer interruption and host EPIPE,
a fixture that closes input with or without a report, real C mapping refusal,
and a real self-signal after completed probes with independent file effects.
Its fixtures are built outside the signed app; selected worker paths remain
mirrored in each reply. `worker_progress_and_failure` also compares diagnostic
availability without changing the justified operation/status classification.

## Unfamiliar diagnostic transport

`unfamiliar_diagnostic_transport` builds the ABI fixture outside the selected
app and runs eleven controls through the standard CLI. Two independently
specified codes and distinct payloads must survive, including a known operation
with an unfamiliar code. The mirrored override, worker/validator PIDs, native
fields, diagnostics, failed/incomplete disposition and independent file effects
are checked separately. Absent/unpublished/invalid/incompatible records are not
promoted to accepted evidence. Numeric records survive truncated or invalid
text; an actual EPIPE and a validator UTF-8 fault survive alongside unfamiliar
records. All controls run before the checker reports aggregate failures.

The validator transcript supplies every record, including the allow/native-result
fields; it does not call `sandbox_check`. The worker file change, receiver UTF-8
fault and child disposition are independently observed. The controls establish
preservation of these records, not attribution or comparability between them.

Fixture inputs and limitations are documented in
[diagnostic transport](../../fixtures/diagnostic_transport/README.md).
Direct Swift and Rust receiver controls complement this CLI route. Temporary
known-code filtering or detail-dropping mutations must fail these controls.
The [unfamiliar diagnostic preservation contract](../../FAILURE-PROPAGATION-CONTRACT.md#unfamiliar-diagnostic-preservation-controls)
records the required distinctions and their test owners; running the controls
requires no retained mutation experiment or acceptance output.

## Comparison matrix

`comparison_matrix` runs the three live specimens of
[comparison matrix](../../fixtures/comparison/matrix.json)
through the CLI: S (real validator, twenty-three rows),
B (the validator steered by `stub_validator.py` through the
`validator_executable_path` test control and the I/O deadline control; its
records are stub output, so expectations come from submitted scopes and
independent file and permission controls, never native verdicts) and C (a
policy that fails to compile). Before any run it records direct controls:
mode-000 opens and spawns fail with EACCES outside PW, the compiled helpers
exit 0 and 1, absent paths are absent. Every file is recreated before every
specimen, because B unlinks the paths it queries. For each row it asserts the
six-field record, the raw fields named beside it, selection of the same step
by field through `tests/lib/consumer.py`, and the file effects after the run
(bytes unchanged, removed, created, or the one byte `open_write` leaves).
Combined failures are reported together in `matrix-summary.json`. The T row
is owned by `worker_attempt_in_flight_at_deadline`; the same fixture rows are
read by `runner_unit`'s `ComparisonEvidenceTests`.
S09's unsupported attempt is constructed-only coverage of the defensive
comparison classifier. Public requests refuse unsupported attempts before
children; the shared request-contract corpus checks that an earlier valid
create in the refused specimen does not run.

## The app's own example

`example_round_trip` acquires its specimen from the selected app. It retains
raw stdout, stderr, observed exit status and command arguments for twelve CLI
calls: one `--version`, two `example` emissions, three workload submissions and
six refusal submissions. `check_example_round_trip.py` reads the captures in
`artifacts/capture/`. Before any submission it requires successful
JSON emissions with empty stderr and one framing newline, an ordinary phased
document with two actions then one, only read-only file attempts, no test
overrides, runner selection, augments or entitlement requirement, and the
three-step workload below.

It submits emitted stdout unchanged, then submits two test-owned derivatives:
flat removes `phases` and places the same actions in `probe_plan`; actor moves
the entire policy object into one applied `selected` actor and assigns both
phases to that actor. Other members, action objects and policy bytes are
preserved. Independent field/membership checks gate the transformations before
submission. `transformations.json` records the permitted changes. The flat
and actor inputs, commands, outputs and samples have their own subdirectories;
refusals remain six single changes to emitted bytes, not eighteen per-form
variants. Each native submission gets its own host and worker.

The checker states the workload once, in its `WORKLOAD` table: the phase
partition, the order of the roles, each role's query operation and attempt
action with the target each concerns, and the answer and attempt result pinned
to the present example. The container bound, the role finder, the
transformation check, the target each native expectation concerns, the native
expectations and the declared conditions all read that table, and `evaluate`
takes it as a parameter. The workload is identified by position and by the
relationships among its submitted operands. No step identifier, path or policy
text decides a role, and the checker does not read the policy source:

| Step | Query | Attempt |
| --- | --- | --- |
| 1 | `file-read-data` on target A | `open_read` of A |
| 2 | `file-read-metadata` on target B | `read_fresh` of target C |
| 3 | `file-read-data` on B | `open_read` of B |

A, B and C are three different submitted paths. A document with another
number of steps, a role missing, repeated, collapsed onto another target or in
another order is another workload and is not run.

Before submission the checker samples every submitted query path and attempt
target, B included, and it samples them again after that submission. All before descriptors are closed before `run`; each form has its own samples. Each sample opens
the path once, takes the device, inode and other metadata from that descriptor,
reads the content from the same descriptor and closes it. It keeps the
SHA-256 digest and length of the content and of its bounded prefix, the first
64 bytes, which is the most one `read_fresh` reads. No content is kept.

The emitted file is then submitted unchanged. Each row of the report has a
form (`emitted`, `flat` or `actor`), a stable identifier, a group and a
classification; one identifier in two forms is two rows. `capture/report.json`
lists every row's result with a one-sentence statement keyed by role, and its
`forms` member names the submitted step identifier and path in each role. The
publication rows (emission, bounds, refusals and the passage rows other than
the delivery length) belong to the emitted form; each derivative has a
`transformation` row in their place:

| Group | Demand |
| --- | --- |
| Passage | The emitted document's identity equals `--version`'s `build.contract` and `data.contract` and the app property list's `PWContract`, in a packaged form; two emissions are byte-identical; `request_delivery.bytes_written` equals the document's length without its framing newline; the document without `contract` equals the example in the contract snapshot. |
| Admission | No `request_failure` and no `bad_request`; the appropriate ordinary or actor dossier's original digest and reply policy digest equal the SHA-256 of the document's policy source. |
| Identity | The envelope's `build.contract`, the client capture's `contract` and the reply's `producer.contract` equal the document's. They are compared before any reply is read. |
| Echo | The reply echoes the document's `specimen_id`, its step identifiers in order, and each submitted operation, filter, attempt kind, action and target. |
| Reported against observed | The process exit status the case captured equals `result.exit_code`. |
| Existing readers | `consumer.validate` reports no error, as the one aggregate assertion `consumer_validation`; the controller's `disposition_integrity` is `valid` with no `disposition_issues`. |
| Prerequisites | A, B and C were each a regular file this user opened and read before the run; they have three distinct device and inode identities; each bounded prefix is nonempty and C's differs from A's and from B's. |
| Native | Listed below; none passes unless every prerequisite holds. |
| Refusals | Six inputs, each the emitted bytes with one change, go through `run`: another development identity, another release, `unbound`, no identity, a removed closing brace and one unknown member. The first five stop at the controller with their code, path, expected identity where one applies and no client capture or reply; the last is refused by the host as `unknown_field` with no step results. |

`bounds.ordinary_form`, each derivative's `transformation` row and every
`structure.*` row are built from named conditions, which the checker declares
for each form. A failing row lists the conditions that failed, such as
`phase2.proceed_observed` or `actor.sandbox.mode`, in its `conditions` member
and its explanation. A member that is absent from a derivative fails its
member set alone; one that is present and changed fails its own condition.

Structure assertions check the submitted phase IDs, ordinals and exact action
partition; each phase must arrive, complete and have its own collected
validator records, release and acknowledgement. The full consumer owns the
internal query, collection and live-worker joins. An internally coherent reply
to a 1+2 partition still fails this case's submitted 2+1 association. Ordinary
execution retains its singular worker; actor execution retains its actual
`actors[]`, top-level `steps[]` and `phases[]`, per-actor dossier and controller
diagnostics. The sole actor must own both visits, apply once, receive the
submitted policy digest, use matched selected equipment, and complete and reap
its owned worker. Numeric PID inequality across sequential reaped children is
not a freshness requirement.

`diagnostic_summary` records each form's query and attempt separately, fresh
read identity/count/digest, independent samples and assertion statuses. A
separate function builds it from the finished report, which it does not
change. A form's observations are withheld when its producer identity or
submitted association is unestablished. It
has no equality assertion or separate acceptance credit; equal independent
passes already imply almost all equal summarized values. Query errno on allow
answers and failed-open `rc` are recorded without adding per-form pins. The
consumer still enforces their record semantics.

The native expectations are pinned to the present example and change with it.
Each is its own assertion:

| Identifier | Expectation |
| --- | --- |
| `native.process_status` | The captured exit status of the `run` process is 0. It is read from the capture and never from the envelope; `reported.exit_code` separately compares the two. |
| `native.completion` | The reply's `normalized_outcome` is `finished`. |
| `native.step1.prediction`, `native.step2.prediction` | The answer is a validator `allow` with `native_rc` 0. |
| `native.step3.prediction` | The answer is a validator `deny` with `native_rc` 1 and a query `errno` of 0. |
| `native.order` | Each step whose answer met its expectation records `order` `query_first`. |
| `native.step1.attempt`, `native.step2.attempt` | A worker result with outcome `ok` and `rc` 0. |
| `native.step2.fresh_syscalls` | The open returned a descriptor, which is any nonnegative integer; the descriptor stat and the close returned 0; the read returned a count within the bound. |
| `native.step2.fresh_identity` | The descriptor's device and inode are those the checker observed for C. |
| `native.step2.fresh_content` | The read count and the SHA-256 of the bytes read are the length and digest of C's bounded prefix as the checker observed it. |
| `native.step3.attempt` | A worker result with outcome `open_failed` and an attempt `errno` of exactly 1 (`EPERM`). `EACCES` fails this assertion as a deviation from the present example; the consumer still reads that record as permission-shaped. |
| `native.targets_unchanged` | Each target's digest, length, bounded prefix, resolved path and `st_dev`, `st_ino`, `st_mode`, `st_uid`, `st_gid`, `st_size`, `st_mtime_ns` and `st_ctime_ns` are equal in the two samples. |

Step 3's answer and its attempt are evaluated apart. No assertion compares
them, none states that a deny answer and a failed open agree, and none
attributes the failure to the policy; the `permission_failure` observation
class stays with the consumer's rules. Step 2's answer concerns B and its
attempt reads C, so that answer predicts nothing about that read.

Reply steps are found by submitted identifier, and their order is the separate
assertion `echo.step_ids`. A step's native expectations are read only from the
one reply step that carries its identifier, and an answer or attempt only from
a record that echoes what that step submitted. When a step has no such reply
step or more than one, its native assertions are unevaluated; when a query or
attempt record echoes something else, the assertions that read that record are
unevaluated. The echo assertion carries the failure in each case. When C's
two samples differ, `native.targets_unchanged` fails and the two
correspondence assertions are unevaluated. When the descriptor stat or the read
did not succeed, the correspondence that needs it is unevaluated and
`native.step2.fresh_syscalls` carries the failure.

The prerequisites bear on the native assertions in two ways. An expectation
about a target is read only when the checker read that target before the run:
A for step 1, B for step 2's answer and for step 3, C for step 2's attempt and
fresh read. Otherwise the assertion is unevaluated, because an unmet
expectation there is what the missing file itself produces, and the
prerequisite carries the failure. Every other expectation is read under the
association rules above. One that is not met fails beside the missing
prerequisite, including the process status, the completion and the comparison
of a fresh read with a sample of C that was taken. One that is met passes only
when all three prerequisites hold and is otherwise unevaluated, so a missing
observation earns no native pass. `native.targets_unchanged` compares the
targets that were read before the run.

Identity, digest and echo expectations come from the emitted document or
another output of the same app. Shape, record, ordering and outcome-mapping
rules belong to the consumer and are not restated; the delivery-length
assertion is a length observation, and exact request bytes at the client
boundary are checked by the controller's orchestration unit test under the
test identity. The target observations establish equality at the sampled
boundaries and assign no writer. They do not establish that a file was stable
between the samples or which object a native query consulted.

The workload does not distinguish everything. Steps 1 and 2 expect the same
answer, so those two answers exchanged leave the capture unchanged. It
exercises `matched` with `same_submitted` and `different` with
`different_submitted`, and never the two relation axes apart; the constructed
rows of the [scenario matrix](../../fixtures/comparison/matrix.json) do. It
holds one literal data-read rule on a path with one spelling, observes no
failed fresh read, and supplies nothing that separates a sandbox cause from
another permission cause beyond this user's own successful read of B.

One actor's two local visit numbers equal the global phase ordinals, so this
case cannot distinguish those axes or prove multi-actor isolation. Read-only
phases do not demonstrate replanning after a file effect. The complete
`phases` and `actor_compositions` cases retain those independent responsibilities.
Matching results here are observations, not a general equivalence of forms.

The case passes or fails and declares no skip. A failure carries its
classification: `consistency` for a relationship that must hold whatever the
native results, `execution_unavailable` when the run yields no admitted reply
(nothing behind the reply is then credited or faulted),
`prerequisite_unestablished` when a target prerequisite was not observed (no
native expectation then passes; no other target is substituted) and
`native_observation` when a pinned native expectation was read and not met.
The log prints each as `FAIL <form> <identifier> [<classification>]`.
Both cases are default members: the native workloads read files, need no signing identity,
GUI session or network, and use the same signed app equipment.

`example_round_trip_controls` runs the same `evaluate` offline over
constructed captures. Its passing model is the phased emission with its flat
and actor derivatives, each with its own run and samples. The ordinary
envelopes are the authored run under
`tests/fixtures/blackbox_e2e/checker/current/` with the allowed and denied file
steps read as steps 1 and 3, and one fresh-read step and three target samples
authored in the control; the actor envelope is the complete authored fixture
described in the [fixture account](../../fixtures/example_round_trip/README.md).
The three-form baseline must satisfy the full consumer and every row before
any control runs.

Each rejected control introduces one logical fault in one form and states the
exact set of identifier and classification pairs that form must produce. The
other forms must hold; when the emission itself is refused, no derivative is
judged. A control that changes one submission's capture runs once in each
form, and a control of the publication runs in the emitted form. For every
expected row built from conditions the control states exactly which conditions
fail. The case spells each row's expected classification itself and fails if
a form's table carries another. The consumer's aggregate diagnostic is
permitted beside another control's set and earns nothing there, and its own
propagation control requires it exactly. Most controls also state the rest of
that form's report: which rows are unevaluated, and that every other one holds.

`example_form_controls.py` holds the condition and ownership rows. For each
condition a control changes one thing: one phase's ordinal, arrival,
completion, collection status, release or acknowledgement; the worker's
application, process identifiers, completion or reap; one projection of the
actor's ownership; one member of its application or equipment; one member of
a derivative. Coherent controls keep a reply to another partition, to another
phase label and to another actor's name internally valid, and the submitted
association still rejects each. A collection borrowed from the first phase,
a query naming another live process and an invented singular worker record
are tied to the consumer rule that reports them. Another form's request in a
derivative's place fails that derivative's member set.

Three controls stand apart from the rows. The same wrong answer in all three
submissions fails each form's own expectation. A constructed 1+2 document,
its derivatives and their replies pass under a 1+2 table handed to `evaluate`
and fail the default table's container, with nothing run; the example in the
committed contract snapshot passes the default table's bounds offline. The
diagnostic summary is built from a finished report and leaves it unchanged,
and one unassociated form withholds only its own observations.

A coherent control changes every dependent field, so the consumer reads the
altered reply without error and only the stated assertion rejects it. The
controls establish what the checker distinguishes, not that a native producer
makes these faults:

| Alteration | What rejects it |
| --- | --- |
| Another workload: a role missing, repeated, collapsed onto another target or out of order | `bounds.workload_roles`; nothing is run. |
| Reply records reordered | `echo.step_ids` alone; every identifier-based assertion keeps its result. |
| A record dropped, renamed or duplicated, including a duplicate that would pass placed first | `echo.step_ids`; that step's native assertions are unevaluated. |
| Whole query or attempt records exchanged under unchanged identifiers | `echo.queries` or `echo.attempts`; nothing is read from the misplaced records. |
| Allow and deny answers exchanged between steps 2 and 3, or 1 and 3, with every echo still its own step's | Each of the two steps' own prediction assertions. |
| Step 3: deny answer with a successful open | `native.step3.attempt` alone. |
| Step 3: allow answer with the `EPERM` failure | `native.step3.prediction` alone. |
| Step 3: failed open with `EACCES`, or with a non-permission errno | `native.step3.attempt` alone. |
| Step 3: deny with a nonzero query errno, an error answer, or another native return | `native.step3.prediction` alone. |
| Captured status and `result.exit_code` disagreeing each way, and agreeing on a nonzero status | `native.process_status`, `reported.exit_code`, or both, as each is true. |
| A fresh read that reads cleanly and carries the identity, the content or both of another sampled file; one byte, the device, the inode or the count alone | `native.step2.fresh_identity`, `native.step2.fresh_content`, or both. |
| A fresh read failing at open, stat, read or close | `native.step2.attempt` and `native.step2.fresh_syscalls`; the correspondence that call supplies is unevaluated. |
| A changed, unreadable or missing second sample of A, B or C | `native.targets_unchanged`; for C the correspondence is also unevaluated. |
| A, B or C unreadable, not regular or unsampled; two targets one file; an identity not observed; C's prefix equal to another's or empty | The prerequisite alone; every native assertion is unevaluated. |
| A missing prerequisite beside an unmet expectation about a target that was read: a fresh read carrying another file's identity or content while A or B is unsampled, a failed or denied step whose own target was read, a nonzero status, an unfinished reply, an unestablished order, a changed target | The prerequisite and that expectation's own assertion; every other native assertion is unevaluated. |
| A missing prerequisite beside an altered step whose own target was not read; a fresh read of another file's identity when C's sample holds none | The prerequisite alone. |
| An association fault beside a native fault; several native faults | Every diagnostic stays. |

Two controls run the checker's observer on files the case writes in its own
directory. Each hands the observer an opener that changes the path as its
open returns: one renames another file over the path and the other unlinks it. The sample must carry the device, inode,
digests and lengths of the file that was opened; the control then reads the
path by name and requires it to name the other file, with another identity,
digest and length, or nothing.

Further controls require the stated assertions to be unevaluated after a failed
emission or bound, behind a differing identity and without an admitted reply,
and require a validator-spawn failure and an unestablished order to be read
cleanly. The expanded structure assertions also report an incomplete collection
or release chain. Each refusal input is judged
against the emitted bytes and its stated change, not against the function that
wrote it. Controls of the checker's `prepare` step show that a failed emission,
identity comparison, packaged identity, snapshot correspondence or bound
writes a report and no target observation, derivative or refusal input, so
nothing can be submitted. Preparation calls `evaluate` with
`preparation_only=True`, leaving every run-dependent row unevaluated.
Flat emission, swapped/collapsed phases and a lost action are rejected at that
boundary. Full evaluation of retained captures still reports independent run
failures beside publication correspondence failures.

Four alterations must pass. Three are made in each form: a fresh read whose
open returned descriptor 0, a fresh read of a target shorter than the bound,
and the answers of steps 1 and 2 exchanged, which is the blind spot stated
above. The fourth renames every step, phase and actor consistently in all
three requests and captures. The case also shows what a
workload with uniform answers could not distinguish, without a second checker:
in a constructed capture where step 3 is allowed and succeeds like the others,
exchanging any two steps' answers leaves the capture identical, so no reader
could tell them apart; in the present capture the same exchange changes it for
both pairs that involve step 3.

The case fails on either of two gaps. Every row of the passing three-form
report, which is what the live case reports, needs a matched rejected control
in its own form. Every condition the checker declares needs a matched control
that fails that condition alone in its row. Every stated condition must belong
to a declared conditioned row expected to fail in that form, including names
in lists that cannot earn singleton coverage. Undeclared rows or conditions,
conditions on unexpected rows and duplicate names fail the case; independent
judgment controls require each rejection. Form-specific conditions live beside
that form's additional expected rows.
`artifacts/example-round-trip-controls.json` holds each control's form,
expected and actual sets, failed conditions and the coverage it earned, with
the observer, table, summary and shared-fault controls, the accepted
alterations and the uniform-answer comparison. Shape and record validity rest
on `blackbox_e2e/checker_controls`; that the app is validly signed and
unchanged rests on the dispatcher's inspection.

## Specimen dossier

`dossier_witness` checks `data.specimen` against facts read independently of
the envelope: the request bytes the controller held, SHA-256 of the submitted
and applied source, the literal import closure (a specimen with an
`(import "system.sb")` and one with a refused augment), `sysctl` host facts,
and the evidence manifest's entries. Nine examples: an ordinary run, a run
with imports, the order of the first import problem (of two absent names
written in reverse order `failure` names the one first in byte order, and an
import form the scan did not follow in the submitted source is reported
before an absent name written above it), an applied augment, a refused augment (`failed` with
`augmentation_failed` imports and no client invocation), a policy without
source (`not_applicable`, delivered and refused by the runner as
`bad_request`), controller refusals (missing arguments and absent files produce
`tool_error` and exit 2; invalid JSON and non-object requests produce
`bad_request` and exit 1 with a structured `request_failure`; all retain the
dossier collected so far without creating a temporary request file), and
executable overrides (a byte-identical worker copy records
`match`; different bytes record `mismatch`; a nonexistent, relative, NUL or
overlong path records `unavailable` with its reason; both helper roles are
independent), and import forms. The last submits one policy per spelling and
compares the dossier with files it hashes itself and with the worker
compiler's own result: an imported marker file holds an operation name the
compiler does not know, so a reply whose diagnostic names that file shows
that the worker's compiler evaluated its content, and not which files it
opened. A literal import, and one with a newline or a comment between or
after its tokens, is `complete` with one hashed record. A computed argument,
with or without a space after `import`, is `incomplete` with no record and a
`failure` naming the source. A file holding a computed import is one record
with its hash and an error, and `failure` names the file. An import in an
untaken branch is `complete` with a record on a finished run, and a renamed
`import` is `complete` with no record although the compiler evaluated the
file: those two rows assert the scan's limits. `request_delivery` must report the held byte count on every
invoked run. The opt-in `dossier_witness_byoxpc` repeats the ordinary example
through an installed BYOXPC copy, where all three
`binaries` records are objects.

The pre-apply case also attempts a real spawn of a nonexistent worker and
requires unchanged files, no worker or validator subprocess, and no ordering
object. Once a worker exists but has not published application, ordering is
all-false with `not_invoked`; no prediction is `query_first`.

The worker-wait pilot reader's version 12 also reports startup program-point
intervals and measured ordinary initial-resampling spans. Resampling pairs end
before fallback sleep and carry a capture marker; missing pairs, dropped events
or an absent marker withhold the measurement. Elapsed resampling includes
possible descheduling and is not a CPU measurement. The independent controls
check separation from sleep, missing versus zero, malformed pairs and the
startup arithmetic. Older frozen reports retain their original reader identity.
