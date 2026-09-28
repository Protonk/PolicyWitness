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
- Archive wall timestamps ran about +35 to +36 ms later than the instrumented
  control's syscall-time `CLOCK_REALTIME`; the earlier stream-versus-archive
  comparison implies about +10 ms an hour before, so the offset drifts within a
  session. Whole-second ceiling leaves variable trailing slack and can exclude a
  near-boundary record. Wider searches did not recover the observed omissions,
  so this is a separate coverage issue. Those measurements are not a universal
  bound on the offset.
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

Audit the collector-to-controller-to-consumer path and record which fields log
processing may change. Preserve the runner reply, native classifications and
execution result exactly. Make structural changes only where the audit finds
an actual dependency or where an explicit boundary makes the resource guarantee
enforceable.

Keep successful empty capture separate from unavailable or disabled capture.
`permission_failures_without_record` refers to permission-shaped attempts with
no captured candidate, not to a global statement about the OS store. Preserve
its null-versus-list meaning. Valid matching events remain optional corroboration,
not an automatic rewrite of `comparison`, `drift`, failure attribution or cause.
Audit in-repository consumers and document the scope of that audit.

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

Make an explicit decision about bounded scan padding for the measured timestamp
conversion offset. Any wider query must report its actual bounds separately
from the original client timestamps and must not masquerade as the old interval.
Test both boundaries with supplied timestamps; do not derive event timing from
path names. A finite pad can cover an explicit allowance, not guarantee delivery
or exact run membership. Do not silently change window meaning, claim PID-reuse
protection, or add waits/retries as an emission guarantee.

Specify whether a bounded collector retains usable complete events on partial
collection or marks the entire capture unavailable. Either choice must expose
incompleteness and preserve the null/list and correlation contracts. This choice,
the budget values, and timeout/overflow representation are implementation
decisions to settle before changing the public evidence shape.

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
