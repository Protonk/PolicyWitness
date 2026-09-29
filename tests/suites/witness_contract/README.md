# witness_contract

Pins the load-bearing behaviors PolicyWitness contracts to provide:
verdicts in the envelope, attempts in the envelope, drift between the
two surfaced explicitly, validator failures attributed honestly, removed
fields rejected, the test seam functioning, and the source-drift
guardrail enforcing the audit trail.

Each test asserts one contract claim. The suite reads as a
behavior specification — what PolicyWitness promises, regardless of
the architecture behind it.

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
  and the unanswered prediction to have an explicit error and `drift:null`.
  These two cases also run in the baseline `runner_validator_failure` suite.

## Independent prediction and attempt targets

`prediction_target_is_independent_of_attempt_target` runs two ordinary CLI
specimens with the real validator and no test overrides. Both attempt writes to
two existing files: the policy allows A and denies B. After restoring the same
seed bytes, the second run swaps only the prediction targets. Policy, attempts,
and random step IDs stay fixed. The test reads and retains external file bytes
before decoding PW's JSON: A must change to nonempty data and B must retain every
seed byte in both runs.

The matching run requires allow/success with `drift=false` and
 deny/permission-failure with `drift=null`. The swapped run retains both predictions
and attempts with `drift=null`: different submitted targets prevent comparison.
This checks independent channel routing without promoting pairing to comparability.
Redirecting a validator query to `attempt.target` must fail even if the envelope
continues to echo the requested filter value. The existing classifier and
steered-validator tests retain their separate contracts.

The case checks step identity/order, raw attempt evidence and compatibility
aliases, prediction and attempt paths, worker/validator completion, and drift.
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
children to the worker's exec deadline, then denies another read. Its metadata
queries are allowed, avoiding query-generated denials for the attempted reads.
It requires the recorded
`capture.window` to be the runner client's own span (`runner_client_span`), with
`start`/`end` equal to an independent whole-second UTC rendering of the client's
timestamps, mirrored back by the observer with `last` null and a zero `log show`
exit. Each available read-denial event must be associated with its step.
The retired trailing interval (the ten seconds before the client's end) is then
replayed through the embedded observer against the same log store. Test-only
parsing of raw event timestamps checks membership in both intervals; path names
are never used to infer timing. The final denied read is the minimum witness:
it happened last, inside the scanned span, so a log store with no record of it
fails the case with a named reason after every artifact is written, and the
envelope's `permission_failures_without_record` must name exactly the denied
reads the log did not record. The early denial is not required; its
availability is recorded. `observations.json` records early/late availability
and any timestamped events outside the shorter interval. A blocked unified log
still fails the real-tool check with a pointer to the harness note. Artifacts include
the run capture, consumer answers, `retired-window.json` and `observations.json`.

Rust controls independently exercise the actual outgoing argv against
`tests/fixtures/deny_capture/observer.py`, whose fixed event timestamps require
early/late inclusion, whole-second widening, and exclusion outside the bounds.
Short, long, equal-endpoint and ten-second intervals share the same event corpus.
Injected clock rollbacks must retain raw readings with null bounds and no helper
invocation. Receiver-to-consumer controls send mismatched and missing bounds and
trailing replies containing matching events through production association,
diagnostics and serialization, then the Python consumer. Both successful and
signaled runs, and old/current runner replies, must preserve execution evidence
without inventing correlations. Historical controller-envelope fixtures retain
their trailing-window meaning in the blackbox consumer controls. Run with:

```sh
tests/run.sh --case witness_contract/deny_capture_covers_the_run
tests/run.sh --suite unit --case blackbox_e2e/checker_controls
```

## Create on an existing file

`create_existing_file_preserves_contents` submits two `file/create` attempts
through the CLI, using the real validator and no test overrides. Both targets
already contain distinct random bytes. Policy allows writing one and denies
writing the other. The allowed attempt must succeed with its observed path;
the denied attempt must report `open_failed` with a permission errno. Their
predictions must be allow and deny respectively, with `drift=null` for the
compound create scope.
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
be allow with `query_first` and allow/success agreement. The test observes file
absence before decoding, and retains later host nonresolution separately as
`host_path_resolution_changed`. Unordered same-target mutation uncertainty,
including later-step unlink, remains pinned by Swift and offline consumer
controls. The stronger gated observer and deliberate barrier-bypass controls are
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
target. The resulting ENOENT read is unavailable/null rather than drift.

`max_steps_ordered` runs 256 distinct existing targets, half denied for writing
by literal, and independently checks every file's bytes before decoding.
`deny_default_ordered` checks an allowed and denied read under `(deny default)`.
Both require eligible predictions to be `query_first`; allow/success is limited
agreement, and deny/permission failure is directional consistency with null drift.

`max_targets_reply_survives` measures five admitted 256-step workloads: denied
ASCII reads of 511-byte targets with log capture, successful reads of
JSON-escaped paths with observed paths, independent 511-byte query paths
against plain attempt targets, 256 execs with stdout/stderr, and 256 native
execs with 511-byte escaped executable targets and independent query paths,
63-byte step IDs, maximal metadata, live profile capture and 1,023-byte
stdout/stderr streams made of U+0001 (six JSON bytes per input byte).
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
app copies must produce early unlink and exec effects under the unchanged CLI
observer. Hashes, signatures, source patches, command logs and effect receipts
are retained. See [opt-in prerequisites](../../OPT_IN_TESTS.md).

The unmodified C scenario must complete its 500 ms hold before release. A bypass
can complete before the first poll: `early_completion` then rejects it immediately,
even with zero held milliseconds and no host release. That observation establishes
premature completion; the baseline supplies the delayed-release coverage.

`validator_spawn_failed_reports_degraded` requires real ENOENT from
`posix_spawn(sb_api_validator)`: the structured native return code, executable
path, operation and nonempty diagnostic, without requiring English wording.
It also requires the mirrored hostile executable path, no validator
subprocess, closed collection with `not_spawned`, unestablished step order/null
drift, and an independently changed file after the released write.

## Completed observations after a worker timeout

`worker_post_apply_hang_seam` attempts an allowed write and a denied write,
then uses a post-apply hang longer than the worker deadline and reap grace.
The host reports `runner_timeout` and SIGKILL termination, with CLI/runner
failure, a deadline diagnostic, and both overrides echoed. Independent file
reads must show changed, nonempty bytes for the allowed write and intact seed
bytes for the denied write before the envelope is decoded.

Both completed attempts retain their distinct outcomes, step IDs/order, paths,
errno evidence, matching real validator predictions, and `drift=false` for
allow/success versus null for the unattributed permission failure.
The validator exits cleanly and `partial_steps=false`: failed run completion
does not erase completed observations. The shared checker, timing margins,
and retained artifacts are documented in `runner_outcome_runner_timeout`.
That suite owns the deliberately empty-plan timeout control;
`runner_use_c_worker/worker_timeout_ms_honored` covers a single successful write.

## Attempt in flight at the deadline

`worker_attempt_in_flight_at_deadline` holds the area A tests of
[controller/DISPOSITION-RECORD-PLAN.md](../../../controller/DISPOSITION-RECORD-PLAN.md).
It runs three specimens
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
  `result_source: worker`, `rc: 0` and `conclusion: agreement`.
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
drift comparison. The positive control removes only the overrides and requires
allow/success with `drift=false` and deny/permission-failure with null. Independent file
reads precede JSON checking: both seeds survive the failure run; the positive
control changes the allowed file and preserves the denied file. Both runs must
avoid a sandbox-termination claim and explicitly emit `deny_signal: null` on
every step. Missing attempts use the current compatibility spelling
`not_run_worker_died`, meaning no completed result, without proving that the
operation never started.

This is the one override-driven case exempt from the exact-outcome assertion in
the `_test_overrides` recipe in [`runner/AGENTS.md`](../../../runner/AGENTS.md).
It checks that `normalized_outcome` excludes `ok`, `sandbox_apply_failed`,
`bad_policy`, and `runner_sandbox_denied` rather than pinning one replacement
outcome, so it protects the absence of library/policy claims across outcome
renames; classifier tests pin the mapping. It keeps the recipe's other
assertions: a real failure artifact in the error, both mirrored overrides,
subprocess and missing-step evidence checks, and the un-overridden positive
control. Optional subprocess objects may be omitted or null; explicit per-step
signal/errno/drift nulls require key presence.

`check_pre_apply_failure.py` collects separate attribution, step/process evidence,
file-effect, lifecycle, cause and signal assertion groups in `assertions.json`. Lifecycle
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
execution status. An un-overridden run verifies successful-run capture. The
checker verifies worker identity in observer output, explicit capture/window
limits and any actual event associations. Repeated attempts reference each event
once with ambiguous candidate IDs. Logs can be unavailable or contain no match;
Rust tests deterministically cover populated, missing/mismatched PID, unrelated
operation, independent query, repeated-attempt and unavailable-capture cases.
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

The steered-validator case also runs ten bounded comparison scenarios through the
CLI. `check_comparison.py` records independent expectations, direct DAC EACCES and
file witnesses. It covers supported agreement and unavailable ordered
deny/success differences, both permission-failure
predictions, different target and operation, missing queries, successful attempts
without predictions, compound create and unsupported attempts. It checks comparison
scope, provenance and simultaneous limits. The transcript supplies verdicts; the
worker attempts and direct OS/file witnesses are real. These are interpretation
controls, not native compiler-drift discoveries. Swift controls separately cover
legacy absence, unusual errors, exec child evidence and deterministic later host
path disappearance.

The removed-target control now expects both native queries to precede read/unlink:
`query_first`, allow/success agreement, and independent host nonresolution after
unlink. Unordered same-target mutation protections remain covered by classifier
and offline consumer controls. Ordered deny/success remains unavailable.

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
