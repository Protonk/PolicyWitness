# Best-effort deny-log evidence

Status: draft for review. This plan proposes implementation and test changes;
none of those changes has been made. The background is the associated
[sandbox-log investigation](records/SANDBOX-LOG-ISOLATION-INVESTIGATION.md).

## Promise and scope

The [root README](README.md#flow) makes unified-log deny evidence an out-of-band,
best-effort channel. Attempts, validator predictions, comparisons and execution
disposition have their own evidence. This work makes that separation explicit
and effective even when log collection fails to finish or returns bad output.

The resulting behavior must satisfy three requirements:

1. With the same runner reply, changing only logger behavior cannot change the
   CLI's execution result or exit status, any attempt or prediction, comparison
   or drift claim, or the reported process disposition and termination cause.
   An absent log does not establish allowance; a permission-shaped failure does
   not become an attributed sandbox denial merely because collection failed.
2. Log collection consumes a documented, finite resource budget and cannot keep
   an already available execution result waiting indefinitely. Collection and
   cleanup failures appear in the log-evidence channel without replacing the
   runner reply. This is a bound on PW's collection and cleanup behavior, not a
   promise about OS scheduling or arbitrary failures elsewhere in the process.
3. Valid retained records receive the strongest correlation supported by the
   existing contract. Matching events must not be silently dropped. Ambiguous
   candidates remain ambiguous; no match, unavailable evidence and disabled
   collection remain distinguishable.

The default battery must test those requirements without requiring macOS to
emit a particular denial. A dependable OS emission condition, reverse engineering
the kext's reporting rule, or a platform-child substitute is not a prerequisite
for this work. New worker probes, persistent monitors and worker timestamp/ABI
changes are outside the initial scope.

## Findings that constrain the work

- The follow-up investigation reproduced omission with an independent
  `sandbox-exec` control: 9 records for 23 EPERM results, with the same nine on
  delayed re-query. Its kext observations support reporting-side omission.
  Stronger capture code cannot recover a record that the query does not return.
- The earlier loss queries omitted the required `--loss` option and were not
  valid negative controls. Corrected queries found no counted loss overlapping
  the missing attempts. Diagnostic loss searches must use the corrected method;
  absence of a loss notice must not become a production completeness claim.
- Archive wall timestamps display later than `CLOCK_REALTIME` by an offset that
  tracks wall-clock discipline: about +10 ms at 16:34, +35 to +36 ms at 17:25
  and +59 to +62 ms at 18:27 UTC on 2026-09-28, measured on the kernel channel
  and then on a userland `os_log` marker, while `timed` was slewing the clock
  and logd re-mapped its conversion only at clock steps and roughly hourly.
  Whole-second ceiling leaves variable trailing slack and can exclude a
  near-boundary record. Wider searches did not recover the observed omissions,
  so this is a separate coverage issue. The scan padding decision in section 3
  records the measurements and the bound they support.
- Burst and lifetime controls did not establish guaranteed record availability.
  The 32-read condition retained some evidence in each phase of three long runs,
  but lost individual records. Neither repetition nor retries until a record
  appears can serve as the default correctness oracle.

The current source already provides substantial semantic separation:
[run_flow.rs](controller/src/run_flow.rs) obtains the runner reply and derives
`runner_outcome` and `ok` before invoking the collector. Association and log
diagnostics subsequently read the runner result. The Python consumer exposes
denial evidence separately. Preserve and verify that behavior before adding
refactoring; do not assume the verdict calculation needs replacing.

There is a concrete resource-isolation gap.
[sandbox_log.rs](controller/src/sandbox_log.rs) waits for the observer using
`Command::output()`, and the observer's normal `log show` path does likewise in
[sandbox-log-observer.rs](controller/src/bin/sandbox-log-observer.rs). Neither
call supplies a collection deadline. The 8 MiB observer retention cap in
[utils.rs](controller/src/utils.rs) applies after complete output buffering;
it does not bound collection memory. The final envelope is printed afterward.
Consequently, semantic independence alone does not protect delivery of the
execution result from a stalled or excessively verbose logging subprocess.

## Work sequence

### 1. Pin the authority and availability contracts

**Diagnosis.** Audit which envelope fields the log channel writes and which
fields read from it, then record the result as a field-ownership table in the
controller contract. Scouting found a clean field-level split with one shared
object: [run_flow.rs](controller/src/run_flow.rs) derives `result` (`ok`,
`exit_code`, `normalized_outcome`, `error`) from the runner reply and the runner
client's own output capture alone; `data.sandbox_log_capture` is written only by
collector processing; `data.runner_sandbox_diagnostics` mixes six disposition
fields projected from the runner reply (`worker_pid`, `process_disposition`,
`termination_cause`, `stop_reason`, `disposition_integrity`,
`disposition_issues`) with four correlation fields derived from the capture
(`capture_status`, `correlation_status`, `first_deny`,
`permission_failures_without_record`), all built by one function from both
inputs. Log processing reads the reply (steps, submitted plan, disposition
record) but no execution field reads the capture. Confirm this by tracing every
write to those fields and every reader in the repository.

**Design.** The invariant to enforce is field-level single ownership across two
channels in one envelope. The execution channel (runner reply, native
classifications, client capture, disposition projection, result and exit
status) is complete before collection starts and is never rewritten by it. The
log channel may write only `sandbox_log_capture` and the four correlation
fields. Within those, successful empty capture, unavailable capture and
disabled capture stay distinct; `permission_failures_without_record` names
permission-shaped attempts with no captured candidate, is null unless
correlation reached `pid_match` or `no_match` with per-step comparisons
present, and says nothing about the OS store; matching events corroborate and
never rewrite `comparison`, `drift`, failure attribution or termination cause.

**Remediation.** Make the boundary structural where the audit finds the two
channels assembled together: finish the execution half, including the
disposition projection, as a value before the collector runs, then attach
collector output through a step whose only outputs are the log-channel fields,
merged into the existing wire shape without moving or renaming a field. That
step is the seam section 2 bounds. Add a permanent control on the production
assembly path that serializes one runner reply under every collector state
(captured with events, captured empty, blocked, error, parse_error,
window_mismatch, invalid_window, requested_unavailable, disabled and, after
section 2, timeout and overflow) and requires a byte-identical execution half
beside the expected correlation fields. Existing controls cover five states at
the diagnostics function
(`capture_conditions_do_not_change_execution_status_or_cause`) and the window
and no-match states through serialization; the investigation's disposable
ten-state replay is the template. Make no other structural change without an
audit finding of an actual dependency.

**Scope.** This step touches envelope assembly in
[run_flow.rs](controller/src/run_flow.rs), its tests and the contract
documentation. It changes no wire field, status value or contract number, and
it does not depend on sections 2 to 4, which reuse its seam and its control.
The consumer audit covers in-repository readers only:
[consumer.py](tests/lib/consumer.py), whose `denials` block is separate from its
comparison and failure groups; the lifecycle oracle, adapter and contract
modules, which read only the disposition fields out of the shared object; the
blackbox checker and disposition controls; the witness cases that assert on
capture; and the disposition fixtures. Document that scope and that consumers
outside this checkout were not audited.

### 2. Bound and contain collection

Give the optional logging operation an explicit deadline, bounded reads and
bounded retention at both the observer and `log show` boundaries. Choose concrete
default budgets from observed normal costs and test them independently of
`--timeout-ms`, whose existing runner-client meaning must stay intact.

Supervise stdout and stderr without a pipe deadlock. Output overflow, helper
launch failure, nonzero or signaled exit, malformed replies, timeout and cleanup
failure must produce explicit log-channel evidence and still allow the runner
envelope to be emitted. A truncated JSON prefix is never a complete report.
Validate reply shape as well as transport success.

Define ownership and cleanup for both the observer and its log child. A child
holding a pipe open after its leader exits must not defeat the deadline.
Termination requests, confirmed exit and unconfirmed cleanup must remain
distinct observations. Test those paths with owned subprocess fixtures rather
than by hanging a real system log command. Keep the implementation confined to
logging unless a shared primitive can be reused without changing other capture
contracts. No new user-facing flag is assumed.

### 3. Preserve useful records and state the real scan bounds

Keep collection, parsing and correlation separately testable. Retain raw evidence
and its provenance within the declared limits. Match the worker PID embedded in
the sandbox message, not the kernel's `processID` 0. Correlation still requires
the supported operation and path evidence, with valid candidate references and
explicit ambiguity. A child-process record is not a worker record; a duplicate
flush naming a neighbour is not a record of the missing attempt.

Scan padding for the measured timestamp conversion offset is decided below: a
symmetric two-second pad reported as its own window field. Any wider query must
report its actual bounds separately from the original client timestamps and
must not masquerade as the old interval. Test both boundaries with supplied
timestamps; do not derive event timing from path names. A finite pad covers an
explicit allowance, not delivery or exact run membership. Do not silently change
window meaning, claim PID-reuse protection, or add waits/retries as an emission
guarantee.

Specify whether a bounded collector retains usable complete events on partial
collection or marks the entire capture unavailable. Either choice must expose
incompleteness and preserve the null/list and correlation contracts. This choice,
the budget values, and timeout/overflow representation are implementation
decisions to settle before changing the public evidence shape.

#### Scan padding decision

**What the offset is.** `log show` converts a record's `machTimestamp` to wall
time through logd's timesync mapping, while the client span comes from
`CLOCK_REALTIME`. Between re-maps `timed` disciplines the wall clock, slewing
through `adjtime` and stepping through `settimeofday`, so displayed times drift
from the client's clock by the correction applied since the last re-map. On
2026-09-28 logd re-mapped at every clock step (three steps of 63 to 73 ms, each
accompanied within 10 ms by a `=== system wallclock time adjusted` timesync
event) and roughly hourly otherwise (35 timesync events in 24 h). The machine
had been up 147 days with the offset at 60 ms, so the offset does not
accumulate over uptime. Records are stamped inside the denied syscall (mach
latency −2 to −10 µs), so this offset is the only timing error between a record
and the client span.

| Measured at (UTC) | Displayed minus `CLOCK_REALTIME` | Source |
| --- | --- | --- |
| 16:34 | about +10 ms | stream-versus-archive comparison, first round |
| 17:25 to 17:28 | +35.41 to +36.10 ms | kernel deny lines of the instrumented control, 9 records |
| 18:27 | +59.10 to +61.68 ms | userland `os_log` marker, 6 records; the kernel channel recorded none of six denials in the same run; `timed` reported a −68 ms residual in progress |

**Exposure.** The window floors the client start and ceils the client end to
whole seconds, so each bound carries 0 to 1,000 ms of slack. A last-step
denial displayed `offset` ms after the client end is excluded when the end
falls within `offset` of the next whole second: probability `offset / 1000`
per such denial, about 2% at today's largest offset for a one-rule specimen and
0% for the 64-rule cohorts, whose teardown places the last record 7 to 55 ms
before the client end. A negative offset (clock slewed forward) moves records
earlier and exposes the start bound the same way. None of the observed
omissions was a slack exclusion; the ±60 s scans lack them too.

**Options considered.**

1. No pad. Keeps the window derivation; leaves a measured 0 to 2% exclusion of
   real records that grows with the offset, and the case cannot tell that
   exclusion from OS omission.
2. Fixed symmetric pad of N whole seconds. `log show` accepts nothing finer than
   a second, so N is an integer. Cost measured at zero: the original interval's
   PID-predicate scan took 0.03 s at 21 s and at 23 s. Wider bounds admit only
   lines naming the worker PID; PID reuse within seconds does not occur in
   practice and the window already disclaims protection against it.
3. Runtime measurement: emit a controller-side `os_log` marker carrying
   `CLOCK_REALTIME` before the scan and read its displayed time back in the
   same scan, then pad by or report the measured offset. Exact, but it adds a
   marker whose visibility has only been checked at 5 s, a second parse path
   and a dependency on userland log persistence; outside the initial scope.
4. End-only pad. Covers the observed sign only; a forward slew or a step would
   expose the start bound.

**Decision.** Option 2 with N = 2: scan from `floor(client start) − 2 s` to
`ceil(client end) + 2 s`. One second already exceeds every observed offset by
16× and the mechanism's bound (steps observed at 63 to 73 ms plus at most an
hour of slew between re-maps); the second covers a maximum-rate slew hour at no
cost. The value is a documented limit; changing it is an edit to
`docs/limits.json` and its generated copies.

**Representation.** `window.start` and `window.end` keep their meaning, the
whole-second UTC strings handed to `log show` and mirrored back by the
observer, now padded. `started_at_unix_ms` and `ended_at_unix_ms` keep the raw
client span. Add `window.pad_seconds` (2). An absent field in an older envelope
means 0, which is what those envelopes did, so the change is additive and needs
no envelope contract bump under the rule in [docs/CONTRACT.md](docs/CONTRACT.md);
the documented derivation "widened to whole seconds" gains the pad. The
window's four disclaimers stay false.

**Touchpoints.**

- `SandboxLogWindow::runner_client_span` in [sandbox_log.rs](controller/src/sandbox_log.rs)
  applies the pad and carries `pad_seconds`; `observer_argv` and
  `observer_window_matches` need no change. [runner_client.rs](controller/src/runner_client.rs)
  and [run_flow.rs](controller/src/run_flow.rs) construct the window and their
  tests assert the derived strings.
- Rust controls `run_span_window_floors_start_ceils_end_and_never_collapses`,
  `run_span_window_claims_coverage_and_nothing_stronger`,
  `observer_is_asked_for_the_window_and_never_for_a_trailing_lookback` and
  `requested_intervals_select_independently_timed_events`; the fixture
  [observer.py](tests/fixtures/deny_capture/observer.py) needs its `/before` and
  `/after` events outside the padded bounds so the exclusion controls stay
  meaningful.
- `documented_controller_limits` in [run_flow.rs](controller/src/run_flow.rs)
  and a new `docs/limits.json` entry (section `evidence`, value 2, unit
  seconds, value and boundary checks) regenerated by `docs/generate_limits.py`;
  the prose in [LIMITS.md](docs/LIMITS.md) and the user guide.
- The live case's window assertions, its membership assertion
  (`start_s <= at <= end_s`) and the retired-interval replay, which must keep
  using the client-derived end rather than the padded `window.end`; the catalog
  description ("requests the full client interval");
  [controller/README.md](controller/README.md) and
  [docs/PolicyWitness.md](docs/PolicyWitness.md) `window` descriptions.
- The consumer passes the window through; the shape validator must accept the
  new key.

**Left open.** The bound rests on one machine's `timed` behaviour over one day.
A machine without network time or with a different step threshold could differ,
so the limit's `counting` text states an allowance, not a guarantee. The
investigation record routes `offset_probe.py`, which re-measures both channels
in about ten seconds, for use before changing N.

### 4. Make the default battery independent of OS emission

Promote the useful investigation controls into ordinary repository tests and
fixtures, reusing existing tests rather than duplicating them. Permanent tests
must not require gitignored evidence or refer back to the investigation record.

- Replay complete, early-only, late-only and empty inputs through the actual
  parser, receiver, correlation, serialization and consumer paths. Include
  disabled/unavailable capture, wrong bounds, malformed replies, unrelated PIDs,
  operation/path mismatches, ambiguous candidates and truncated output.
- Exercise collector process faults with bounded fixtures: no exit, no EOF,
  excessive stdout/stderr, failure to launch, nonzero/signal exit, and cleanup
  errors. Assert preserved native/execution evidence, the expected collection
  status, bounded retention, and independently observed cleanup where possible.
- Require positive supplied-event cases to retain all eligible events and
  associations. Deliberately dropping a line or supplied event, inventing an
  association, suppressing every capture, or changing an execution answer must
  cause a default correctness test to fail. Accepting empty OS output must not
  make a broken collector pass these positive controls.
- Rework `witness_contract/deny_capture_covers_the_run`: preserve native-attempt,
  scan-contract and diagnostic checks; remove the requirement that the OS store
  the final denial. Check available real records conditionally, and check an
  explicit unavailable result honestly. Empty, partial or unavailable evidence
  must not be conflated. Real software/equipment contract failures must remain
  failures rather than being swallowed by a blanket “best effort” exception.

Keep real record-availability measurements separate from the default correctness
gate. If a registered OS-behavior probe is retained, make it explicitly opt-in,
retain every initial result, and report its sample and environment. It must not
serve as a required dependency of the default case or retry until green.

#### Audit of the default battery for live-log dependence and timestamp assumptions

Scope: the 163 cases `tests/run.sh --list` selects by default, the Rust unit
batch (`cargo test --bins`), the Rust CLI integration batch
([cli_contract.rs](controller/integration/cli_contract.rs)), and the libraries
and fixtures under `tests/lib` and `tests/fixtures`. Method: every reference to a
log-evidence field, the observer, the `log show` tool or the `--no-log-capture`
flag was located and read; catalog descriptions, suite READMEs and the evidence
documentation were read for coverage claims. Result: one default case requires a
live record; one default case parses displayed timestamps; no unit, integration
or fixture test does either.

| Relationship to the log channel | Default cases | What holds today |
| --- | --- | --- |
| Requires the OS store to hold a record | `witness_contract/deny_capture_covers_the_run` | Covered by the preceding bullet. It is also the only test that parses `raw_line` timestamps ([check_deny_capture_window.py](tests/suites/witness_contract/check_deny_capture_window.py) lines 49–56): every worker read must satisfy `start_s <= at <= end_s`, and reads displayed before the retired interval must be disjoint from the retired replay. With the measured +10 to +36 ms display offset, a record of an attempt in the run's final tens of milliseconds can display past `end_s` and fail the membership assertion while present, a second failure path independent of omission. |
| Capture enabled, channel asserted, no record required | `witness_contract/worker_termination_and_log_correlation`, `witness_contract/max_targets_reply_survives` | [check_termination_correlation.py](tests/suites/witness_contract/check_termination_correlation.py) requires the observer to be invoked and the window mirrored, then branches: `captured` with an events list checks presence-dependent status, `permission_failures_without_record == ([] if matches else ids)` and ambiguous associations; every other status only requires `correlation_status == "unavailable"` (lines 171–174), so an equipment or observer failure passes silently there. [check_max_target_reply.py](tests/suites/witness_contract/check_max_target_reply.py) lines 159–165 require `capture_status != "capture_error"` and an untruncated observer reply for 256-step workloads; a bounded-retention policy from section 2 must keep that reply inside its budget or this assertion changes. Neither parses timestamps. |
| Capture enabled, nothing asserted about it | `smoke/*` (2), `blackbox_e2e/BBX-001`, `BBX-002`, `runner_apply_isolation_v2/*`, `runner_apply_isolation_v3/*`, the eight live `blackbox_menagerie/*` cases ([run_case.py](tests/suites/blackbox_menagerie/run_case.py)), and the `cli_contract` functions that omit the flag | They pay the `log show` cost and depend on the channel only through the CLI exit status, which [run_flow.rs](controller/src/run_flow.rs) derives before capture. A stalled collector delays their envelopes; an absent record cannot fail them. |
| Capture disabled with `--no-log-capture` | 26 case scripts: twelve in `witness_contract` (including the drift seam script), three in `run_effects`, two each in `runner_exec_dac`, `runner_exec_lifecycle` and `runner_validator_failure`, and one each in `runner_exec_inheritance`, `runner_live_worker_identity`, `runner_outcome_runner_timeout`, `runner_outcome_validator_no_reply`, `runner_specimen_isolation`, `sbpl_allowdeny_consistency` and `failure_boundaries` | Log-independent by construction. `check_pre_apply_failure.py` asserts `sandbox_log_capture is None`; [lifecycle_oracle.py](tests/lib/lifecycle_oracle.py) expects the disabled projection (`disabled`, `not_attempted`, null list). |
| Constructed evidence, no live log | `blackbox_e2e/checker_controls`, `unit/rust.unit`, `unit/rust.disposition_reds` | [checker_controls.py](tests/suites/blackbox_e2e/checker_controls.py) drives the consumer with captured/no_match, blocked/unavailable and disabled envelopes, a dropped `operation_source` and a forged `exact_run_membership`. `sandbox_log::tests` run the real argv against [observer.py](tests/fixtures/deny_capture/observer.py), whose fixed event times are independent of the requested bounds (window selection, not attempt timing). The observer's parser test asserts that a parsed event carries no timestamp field. These are the base for the replay and positive controls above. |

Other findings:

- The remaining `raw_line` references ([failure_boundaries/check.py](tests/suites/failure_boundaries/check.py), [check_diagnostic_transport.py](tests/suites/witness_contract/check_diagnostic_transport.py)) are validator transcript records, unrelated to the log channel.
- `tests/lib/testlib.sh` defines `skip_sandbox_log_observer_unavailable`, but no case calls it; a missing observer binary is a preflight failure through `EXECUTABLES` in [artifact.py](tests/lib/artifact.py).
- Text that states the mandatory-presence or timing claim and must change with the case: the `deny_capture_covers_the_run` description in [tests/catalog.json](tests/catalog.json), the "Deny capture covers the run" section of [tests/suites/witness_contract/README.md](tests/suites/witness_contract/README.md) ("the final denied read is the minimum witness … fails the case with a named reason"; "test-only parsing of raw event timestamps checks membership in both intervals"), and the case's module docstring.
- [docs/PolicyWitness.md](docs/PolicyWitness.md#denial-log-correlation) and [controller/README.md](controller/README.md) already state that `captured` does not certify every denial was logged, that parsed events have no structured timestamps and that a complete interval does not guarantee delivery. No permanent documentation claims record presence. The window wording in [docs/LIMITS.md](docs/LIMITS.md) and the user guide ("widened to whole seconds") changes only if section 3 adopts padding.

### 5. Document and validate the resulting contract

Update the root description, controller contract, user guide, limits inventory,
test catalog and suite documentation where behavior actually changes. Change
`docs/limits.json` and regenerate its copies for new enforced limits. If envelope
fields, statuses or window semantics require a contract version change, use
`docs/contract.json` and its generator; preserve historical envelope meaning and
update consumer fixtures. No runner-response or worker-ABI change is presumed.

Run the affected Rust/consumer checks and meaningful collector failure controls,
then the relevant live witness cases against a valid signed, unchanged app.
Run the default battery after integration, retaining all failures rather than
crediting only a passing retry. The evidence must distinguish implementation
correctness, equipment failures and measured OS record availability.

## Acceptance

- Logger-only variation preserves the same runner reply, execution result,
  exit status, prediction/attempt/comparison evidence, disposition and cause.
- A stalled or noisy collector is bounded by its documented supervision and
  retention policy; its failures do not replace an available runner result.
- For complete inputs within the declared budgets, every eligible supplied
  event is retained and correlated correctly; invalid and ambiguous inputs do
  not acquire stronger meaning. Partial collection follows its explicit policy.
- Empty, partial, unavailable and disabled evidence remain distinguishable
  through the public envelope and consumer.
- No default correctness assertion depends on the OS emitting a selected
  denial. Positive capture coverage remains mandatory through controlled input.
- Actual query bounds, collection limits and observed cleanup are represented
  honestly, including any chosen padding or partial-capture policy.
- Permanent tests and documentation stand on their own after this temporary
  plan is deleted. Inbound links to the associated prose record remain confined
  to associated `*-PLAN.md` files.
