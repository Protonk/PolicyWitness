# witness_contract

Pins the load-bearing behaviors PolicyWitness contracts to provide:
answers in the envelope, attempts in the envelope, the relation between
the two recorded explicitly, validator failures attributed honestly, removed
fields rejected, the specimen dossier collected, the test seam functioning,
and the source-drift guardrail enforcing the audit trail.

Cases assert contract claims independently. The suite reads as a
behavior specification — what PolicyWitness promises, regardless of
the architecture behind it.

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
See the [fixture](../../fixtures/path_query/README.md) and opt-in registry.

The separate opt-in `path_query_integrated` case retains extra native query
receipts against the actual PW worker through a validator wrapper. It forwards
only requested verdicts to the host, so the planner's unavailable results remain
unchanged. Three specimens cover same-worker unlink/recreate, absent-leaf create
and dangling-symlink unlink; independent effects, production consumer validation
and cleanup are checked. The validator's copied executable bytes are unchanged.
This isolates integration relevance while explicitly changing collection timing.

## Native extension boundaries

`extensions` executes the public guide's actual extension example as well as
ordinary-authority issuance, native consumption and release
in one worker, with fresh descriptor identity, bounded bytes and syscall results
on either side of both interventions. Each phase collects its own queries.
Native return values and observed access remain independent evidence.

The same case covers omitted lifecycle actions, same-phase and cross-phase
placement, intervention-only phases, failed path preparation, symlink resolution
and replacement between issuance preparation and consumption. An independently
held, non-inherited descriptor keeps the removed identity observable while the
worker creates a replacement. Later reads report their actual identity and bytes;
the test does not require release success to revoke access.

The opt-in `extensions_byoxpc` case runs this workload and the ordinary `phases`
controls through an owned installed runner. Independent signing and entitlement
read-backs establish that the issuer receives the selected identity without the
worker's supplied entitlements. Envelope provenance must match the registry's
per-binary records, and issuer dossier hashes must match independently read
installed bytes and the shipped baseline. A missing issuer path must produce
the named capability refusal before worker launch. The owned installed-copy
control removes the actual issuer, retains a restoration receipt, checks public
validation, then restores and verifies the exact bytes. The same BYOXPC session
runs the maximum-reply workloads. Cleanup verifies service removal. These workloads place
their targets in owned temporary directories to avoid requesting Desktop access.

`extension_boundaries` compiles the production issuer and worker with the
[controlled native entrypoints](../../fixtures/extension_controls/README.md).
The clang test build uses `PW_EXTENSION_OBSERVE` outside the inspected app.
These controls establish boundary behavior of those instrumented sources;
they do not interrupt the shipped executable bytes or observe private API internals.
It drives native refusal, absent APIs, issuer death/deadline, malformed transport
and interrupted consumption/release through the CLI, and forces each worker
delivery failure class individually: every local setup failure (`core_limit`,
`descriptor_metadata`, `mapping`, `descriptor_close`), a cleanup close failure
after an earlier failure, an undersized channel and each header and token
rejection. The published `delivery_status` and `delivery_failure` must identify
the controlled failure with its native return and errno where a call supplied
them, and consumption must stay unavailable. Independent receipts
distinguish death after the pre-call marker, inside a replacement function, and
after the real native return but before publication. PW must retain unresolved
results and earlier completed evidence regardless of what the fixture knows.

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
expectations. Token validation interruption occurs before delivery publication;
the channel is mapped, not copied as a byte stream. No new worker setup status
is needed: unobserved delivery remains distinct from a published setup refusal.

The ordinary-phase combined control is in `runner_unit` (`PhaseProtocolTests`):
a real validator times out, a substituted termination call fails, and its late
write observes EPIPE while a fresh next-phase validator runs. The retained reply
keeps the first child unreaped and each phase’s records separate; the test owns
independent child cleanup. Rust assembly and the Python consumer/oracle replay
that production-encoded reply. The fixture’s query answers are controlled data.

## Invariants

- The suite is included in the default battery, including regression guards
  against re-introduction of removed request fields (`instrumentation`) and
  runner modes (`runner.mode=debuggable`).
- `happy_path_baseline.sh` is the regression sentinel — it must pass
  in every run. If it fails, stop and investigate before continuing.
- Tests are stateless: named for what they assert, not for any
  plan-row number.

## Success criteria

- Every test passes.

## Fixtures

- Specimens are generated inline per test.
- `happy_path_baseline` uses a stable `(version 1) (allow default)`
  policy with one file read step.
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
Shared black-box checks collect both prediction failures rather than stopping
after the first mismatch. `RunCapture` retains each request, raw envelope,
stderr, and capture metadata under `matching/` and `swapped/`; these directories
also contain expectations, byte snapshots, and diagnostics. The case needs the
built app and live XPC; missing equipment fails. Log capture is disabled.

Run it independently with:

```sh
tests/run.sh --case witness_contract/prediction_target_is_independent_of_attempt_target
```

## Deny capture covers the run

`deny_capture_covers_the_run` denies one read, holds two `/bin/sleep` exec
children to the worker's exec deadline, then denies another read. Its allowed
metadata queries are independent of those read attempts; all validator queries
use `SANDBOX_CHECK_NO_REPORT` and produce no denial records.
The native attempts, worker exit and elapsed span are mandatory witnesses.
One denied read goes through a symlinked directory: the policy names the
resolved path, the attempt names the link, and the host's
`attempt.path_diagnostics` must resolve the link form to the denied path. A
returned record for that step must be admitted through the host form, never
the submitted target.
`capture.window` retains the raw client milliseconds and requests
`floor(client start) - 2 s` through `ceil(client end) + 2 s`, with `pad_seconds: 2`.
The observer must mirror those bounds without a trailing lookback. Returned
read-denial records must lie in the padded interval and name the expected
candidate step. A complete empty query is valid; early/late record availability
is recorded and does not determine whether this case passes. These checks do
not establish retrieval completeness or complete OS delivery.

The retired ten-second query ends at the unpadded, rounded client end and checks
its own invocation. Timestamp parsing establishes membership in each interval;
path names do not establish timing. No record equality or inclusion is required
between the queries. `observations.json` retains their availability differences,
including records first seen by the retired query, without inferring their cause.
Artifacts also include the native run, consumer answers and raw retired reply.

The three live log cases (`deny_capture_covers_the_run`,
`worker_termination_and_log_correlation`, `max_targets_reply_survives`) share
[`log_capture_contract.py`](../../lib/log_capture_contract.py). Completed queries
must have intact replies, matching identities/windows/budgets, finished pipes,
observed successful exits and confirmed cleanup. Supported timeout/overflow
requires a cutoff at the identified boundary, the documented deadline or
limit with its observations, bounded retention and confirmed cleanup. Such
capture is unavailable for correlation: candidates and missing-record
diagnostics are null. It is not positive capture coverage. Missing helpers,
blocked access, malformed complete replies, wrong bounds, unexplained process
failures and unconfirmed cleanup remain failures. Generic `unavailable` is
insufficient. `log_capture_controls` supplies complete/early/late/empty replies,
cutoffs and deliberate corruptions to enforce these distinctions without an app.

Positive preservation coverage is mandatory and independent of live emission:

- Rust window controls run actual argv against `observer.py`'s fixed event
  timestamps: both padding regions, exact/exterior boundaries, equal spans and
  rollback. Wrong/missing/trailing bounds withhold correlations without losing
  diagnostic records.
- `log_replay_tests.rs` replaces only the inner query command with supplied text,
  calls the production `log_show.rs` parser/collector, transports a bounded reply
  through the supervised receiver, and runs real assembly and consumer recovery.
  Full, early-only, late-only and empty inputs have fixed expected records and
  candidates. Child/neighbour PIDs, mismatched operation/path and duplicate
  records cannot gain invented associations; repeated attempts remain ambiguous.
  Failed inner queries retain intact diagnostics without correlations. Disabled,
  unavailable, malformed and wrong-window cases preserve execution evidence.
- The controlled capacity case retains 256 distinct 511-byte targets and all
  candidate references through the entire replay under the production default
  allowance. A separate control correlates the maximum event volume against a
  256-step plan inside that allowance. Both prove capacity for supplied input,
  not a live-volume bound.
- Supervisor controls cover both boundaries' byte edges, launch/read/wait/exit
  faults, hangs and cleanup failures. Owned-group controls check orphan pipes,
  leader death before a reply, membership, eventual absence and no signals after
  reaping. Deadline controls preserve execution and bounds under short/long
  overrides and still bound a permanently stalled query; the log child's
  1,000 ms report reserve lets an inner deadline arrive as an intact observer
  reply. JSON expansion,
  incomplete outer replies and derived-data limits have separate exact oracles.
- The required archive case tests real OS predicate selection before parsing;
  suppressing every selected record cannot pass it. Positive replay assertions
  reject dropped lines/events, invented associations, blanket capture suppression
  and changed execution answers even though empty live captures are admissible.

```sh
tests/run.sh --case witness_contract/deny_capture_covers_the_run
tests/run.sh --suite unit --case witness_contract/log_capture_controls --case witness_contract/log_query_predicate_archive
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
ASCII reads of 511-byte targets with log capture, successful reads of
JSON-escaped paths with observed paths, independent 511-byte query paths
against plain attempt targets, 256 execs with stdout/stderr, and 256 native
execs with 511-byte escaped executable targets and independent query paths,
63-byte step IDs, maximal metadata, live profile capture and 1,023-byte
stdout/stderr streams made of U+0001 (six JSON bytes per input byte).
The explicit phase workload repeats collection across eight boundaries. Fresh-read
workloads use 256 ordinary reads or 254 reads plus consume/release sharing the
same action capacity. They compare returned prefixes and descriptor identities
with independent file observations and require actual native lifecycle results.
These require complete replies and exact targets, outcomes and applicable
output; the control-character workload also requires every prediction to
round-trip through the real validator. Every admitted workload must stay under
the synthesized maximal reply recorded in `docs/limits.json`
(`runner_reply_maximum`, computed by `runner_unit` from the field-complete reply
fixture with every string at its limit), and the receiver budget must equal three
times that bound rounded up to 4 MiB. The maximal-metadata workload also adds a
conservative receipt allowance (`2 * 4 * ceil(capture / 3) + 4096`, capture from
the manifest) and must still fit under the bound; Swift independently tests that
allowance with maximal slash-heavy bytes. The corpus is evidence that real
replies stay inside a bound that follows the schema, not the source of the bound.
The optional deny-log channel follows the shared live-capture rules above:
complete empty queries and evidenced budget cutoffs are admissible, while native
runner replies must still survive intact. The separate 256-record supplied-text
control proves observer/candidate capacity for its fixed corpus; the specimen's
step count does not bound live log volume.

Four refusal workloads submit 32,768-byte query values or filter/attempt labels.
Each requires a host-owned `admission_failure` naming the field, no steps and no
worker or validator subprocess. The label controls place a valid write before
the invalid label and independently require every target to remain unchanged.
Every workload records its reply size and requires an untruncated receiver;
refusal replies must be smaller than 4 KiB. Every echoed request string is
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
are retained. See [opt-in prerequisites](../../OPT_IN_TESTS.md).

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
under `(version 1) (allow default)` with `--no-log-capture`:

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
`(version 1) (allow default)` with `--no-log-capture`: `/etc/hosts`, a `create`
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
it provides no evidence of compilation failure. Both runs disable log capture.

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

This is the one override-driven case exempt from the exact-outcome assertion in
the `_test_overrides` recipe in [`runner/AGENTS.md`](../../../runner/AGENTS.md).
It checks that `normalized_outcome` excludes `ok` and `bad_policy`, and the
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

## Termination and denial-log correlation

`worker_termination_and_log_correlation` uses two repeated denied writes with
independent read queries, then an unrelated self-SIGKILL. Its delay seam gives
the validator time to answer before the signal. The case retains completed
attempts and unchanged file bytes, requires `runner_failed`, confirmed signal
status and no host termination request, and makes no sandbox-cause claim.

The same failure runs with capture disabled and enabled; both retain the same
execution status. An un-overridden run verifies successful-run capture. Each
variant also runs with the repeated writes in separate explicit phases, asserting
phase completion, separate query collections and phase-local query ordering.
The checker verifies worker identity in observer output, explicit capture/window
limits and any actual event associations. Repeated attempts reference each event
once with ambiguous candidate IDs. Completed logs can contain no match, while
evidenced budget exhaustion must withhold correlation; unexpected collection or cleanup failures fail the case.
Rust tests deterministically cover populated, missing/mismatched PID, unrelated
operation, independent query, repeated-attempt and unavailable-capture cases.
The collector-state controls exercise both request forms: a shared worker PID
and target across phases still yields ambiguous candidates, while populated,
empty and failed captures leave serialized execution evidence unchanged.
Artifacts retain each request, raw envelope, stderr, capture metadata, file bytes
and `observations.json`. No signed app is altered to steer observer output.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

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
[`diagnostic_transport`](../../fixtures/diagnostic_transport/README.md).
Direct Swift and Rust receiver controls complement this CLI route. Temporary
known-code filtering or detail-dropping mutations must fail these controls.
The [unfamiliar diagnostic preservation contract](../../FAILURE-PROPAGATION-CONTRACT.md#unfamiliar-diagnostic-preservation-controls)
records the required distinctions and their test owners; running the controls
requires no retained mutation experiment or acceptance output.

## Comparison matrix

`comparison_matrix` runs the three live specimens of
[`tests/fixtures/comparison/matrix.json`](../../fixtures/comparison/matrix.json)
through the CLI with `--no-log-capture`: S (real validator, twenty-three rows),
B (the validator steered by `stub_validator.py` through
`_test_overrides.validator_executable_path` and the I/O deadline seam; its
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

## Specimen dossier

`dossier_witness` checks `data.specimen` against facts read independently of
the envelope: the request bytes the controller held, SHA-256 of the submitted
and applied source, the literal import closure (a specimen with an
`(import "system.sb")` and one with a refused augment), `sysctl` host facts,
and the evidence manifest's entries. Seven examples: an ordinary run, a run
with imports, an applied augment, a refused augment (`failed` with
`augmentation_failed` imports and no client invocation), a policy without
source (`not_applicable`, delivered and refused by the runner as
`bad_request`), controller refusals (missing arguments and absent files produce
`tool_error` and exit 2; invalid JSON and non-object requests produce
`bad_request` and exit 1 with a structured `request_failure`; all retain the
dossier collected so far without creating a temporary request file), and
executable overrides (a byte-identical worker copy records
`match`; different bytes record `mismatch`; a nonexistent, relative, NUL or
overlong path records `unavailable` with its reason; both helper roles are
independent). `request_delivery` must report the held byte count on every
invoked run. The opt-in `dossier_witness_byoxpc` repeats the ordinary example
through an installed BYOXPC copy, where all three
`binaries` records are objects.

The pre-apply case also attempts a real spawn of a nonexistent worker and
requires unchanged files, no worker or validator subprocess, and no ordering
object. Once a worker exists but has not published application, ordering is
all-false with `not_invoked`; no prediction is `query_first`.

## Archive query selection

`log_query_predicate_archive` is a required default case that runs the production
`log show` command builder against a committed, self-contained `.logarchive`.
It checks the complete unfiltered corpus, then selected message multiplicities
before parsing, then independent expected events. It does not depend on new
live denial emission. Missing/unreadable data, blocked access, timeout, overflow,
nonzero exit and wrong or empty selection fail; none is an availability skip.
The Rust test is excluded from the generic unit batch and explicitly selected
by this case. See [the fixture contract](../../fixtures/deny_capture/README.md)
for the manifest and producer/reader compatibility requirements.
