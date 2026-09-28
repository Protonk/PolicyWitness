# Best-effort deny-log evidence

Status: Ready to run. 

## Promise and scope

The [root README](README.md#flow) makes unified-log deny evidence an out-of-band,
best-effort channel. Attempts, validator predictions, comparisons and execution
disposition have their own evidence. This work makes that separation explicit
and effective even when log collection fails to finish or returns bad output.

The resulting behavior must satisfy three requirements:

1. With the same runner reply and runner-client capture, changing only logger
   behavior cannot change the CLI's execution result or exit status, any attempt
   or prediction, comparison or drift claim, or the reported process disposition
   and termination cause. An absent log does not establish allowance; a
   permission-shaped failure does not become an attributed sandbox denial
   merely because collection failed.
2. Log collection consumes a documented, finite resource budget and cannot keep
   an already available execution result waiting indefinitely. Collection and
   cleanup failures appear in the log-evidence channel without replacing the
   runner reply. This is a bound on PW's collection and cleanup behavior, not a
   promise about OS scheduling or arbitrary failures elsewhere in the process.
3. For successful complete captures within the declared budgets, valid retained
   records receive the strongest correlation supported by the existing contract.
   Matching events must not be silently dropped. Failed or incomplete captures
   retain available diagnostics but withhold correlation. Ambiguous candidates
   remain ambiguous; no match, unavailable evidence and disabled collection
   remain distinguishable.

The default battery must test those requirements without requiring macOS to
emit a particular denial. A dependable OS emission condition, reverse engineering
the kext's reporting rule, or a platform-child substitute is not a prerequisite
for this work. New worker probes, persistent monitors and worker timestamp/ABI
changes are outside the initial scope.

## Work sequence

### 1. Pin the authority and availability contracts

**Diagnosis.** Audit which envelope fields the log channel writes and which
fields read from it, then record the result as a field-ownership table in the
controller contract. Trace every write to those fields and every reader in the
repository.

**Design.** The invariant to enforce is field-level single ownership across two
channels in one envelope. The execution channel (runner reply, native
classifications, client capture, disposition projection, result and exit
status) is complete before collection starts and is never rewritten by it.
Within `data.runner_sandbox_diagnostics`, execution owns `worker_pid`,
`process_disposition`, `termination_cause`, `stop_reason`,
`disposition_integrity` and `disposition_issues`. The log channel owns the entire
`data.sandbox_log_capture` subtree, including `window`, `observer`,
`observed_deny`, `deny_events`, `step_denies` and transport diagnostics, plus
the diagnostics' `capture_status`, `correlation_status`, `first_deny` and
`permission_failures_without_record`. `step_denies` references candidate step
IDs; it is not a field inside the runner's steps or comparisons. Log processing
may write only those owned fields. Successful empty capture, unavailable capture
and disabled capture stay distinct; `permission_failures_without_record` names
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
(captured with events, captured empty, blocked, error, capture_error, parse_error,
invalid_reply, window_mismatch, invalid_window, requested_unavailable, disabled
and, after section 2, timeout and overflow) and requires a byte-identical
execution half beside the expected correlation fields. Include failed captures
that retain diagnostic events and replies without an authoritative worker PID;
neither may acquire associations. Make no other structural change without an
audit finding of an actual dependency.

**Scope.** This step touches envelope assembly in
[run_flow.rs](controller/src/run_flow.rs), its tests and the contract
documentation. It changes no wire field, status value or contract number, and
it does not depend on sections 2 to 4, which reuse its seam and its control.
The consumer audit covers in-repository readers only:
[consumer.py](tests/lib/consumer.py); the lifecycle oracle, adapter and contract
modules; the blackbox checker and disposition controls; the witness cases that
assert on capture; and the disposition fixtures. Document that scope and that
consumers outside this checkout were not audited.

### 2. Bound and contain collection

Give the optional logging operation an explicit deadline, bounded reads and
bounded retention at both subprocess boundaries: observer capture in
[sandbox_log.rs](controller/src/sandbox_log.rs) and `log show` capture in
[sandbox-log-observer.rs](controller/src/bin/sandbox-log-observer.rs). Enforce
retention limits while reading output. Choose concrete default budgets from
observed normal costs and test them independently of `--timeout-ms`, whose
existing runner-client meaning must stay intact.

Count raw bytes crossing each pipe before decoding, event parsing or controller
PID/candidate filtering. For `log show`, these are bytes emitted after its query
predicate, not all records in the time window. Give stdout and stderr separate
limits at each boundary. Account for JSON escaping and duplicated raw evidence
when sizing the observer-response budget; a successful inner capture within its
limits must fit the outer report budget, including metadata. Bound derived
event arrays and serialization allocations as well as retained stream text.
Record the boundary, configured limit or deadline, observed byte counts and
cutoff reason. Counts after an interrupted read describe bytes actually read,
not an invented total size for the unavailable remainder.

Require the query predicate to select supported Sandbox worker process/PID
tokens. Remove bare-PID-digit matching that can admit unrelated messages;
retain exact parsed-PID validation before association. Preserve supported worker
message forms with controlled positive cases and reject unrelated PID digits
in paths or other text. Keep filtering in the OS query so irrelevant records
are excluded before they consume output budgets; a cap only on post-filter
events would leave transport and parsing unbounded.

Use controlled input volumes to establish capacity, including a representative
256-step workload, and measure normal collection costs with the padded window.
Specimen admission does not bound OS log volume or query cost. Reaching a
documented collection limit can therefore withhold correlation even for a small
specimen; report that limit outcome without changing execution evidence. Do not
make complete live capture a capacity guarantee.

Supervise stdout and stderr without a pipe deadlock. Output overflow, helper
launch failure, nonzero or signaled exit, malformed replies, timeout and cleanup
failure must produce explicit log-channel evidence and still allow the runner
envelope to be emitted. A truncated JSON prefix is never a complete report.
Validate reply shape as well as transport success.

Define ownership and cleanup for both the observer and its log child. A child
holding a pipe open after its leader exits must not defeat the deadline.
Termination requests, confirmed exit and unconfirmed cleanup must remain
distinct observations for each process. Account for the log child even if the
observer exits or is terminated before delivering a reply. Test those paths
with owned subprocess fixtures rather than by hanging a real system log command.
Keep the implementation confined to logging unless a shared primitive can be
reused without changing other capture contracts. No new user-facing flag is
assumed.

### 3. Preserve useful records and state the real scan bounds

Keep collection, parsing and correlation separately testable. Retain raw evidence
and its provenance within the declared limits. Match the worker PID embedded in
the sandbox message, not the kernel's `processID` 0. Correlation still requires
the supported operation and path evidence, with valid candidate references and
explicit ambiguity. A child-process record is not a worker record; a duplicate
flush naming a neighbour is not a record of the missing attempt.

Report the padded query bounds separately from the original client timestamps.
Test both boundaries with supplied timestamps; do not derive event timing from
path names. A finite pad covers an explicit allowance, not delivery or exact run
membership. Do not silently change window meaning, claim PID-reuse protection,
or add waits/retries as an emission guarantee.

#### Partial collection

**Action.** In the CLI's `log show` capture path, treat locally incomplete
collection as unavailable for correlation. At either subprocess boundary,
timeout, read failure, output truncation or overflow, or failure to observe
completion prevents `capture_status: captured`.
Report the failure reason so partial collection remains distinguishable from
collection that never started. Set `correlation_status` to `unavailable`, and
`step_denies`, diagnostics `first_deny` and
`permission_failures_without_record` to null. Use one success gate for
correlation; do not introduce partial associations or per-step completeness.

**Retention.** Keep available stdout/stderr diagnostics within the collection
budgets, with their source, observed byte counts, truncation and failure reasons,
and cleanup facts. Preserve an intact, shape-valid observer reply, including
its events and metadata, as diagnostic evidence even when collection failed.
If the observer JSON is incomplete, retain its bounded raw prefix without
repairing it or extracting events from fragments. Do not add a second transport
to recover output held by a terminated observer. Some valid deny records may
therefore remain uncorrelated; that is the accepted cost of avoiding a separate
event-recovery and partial-correlation contract.

**Boundary.** Incompleteness here means PW failed to finish collecting the
requested query's output. A successful complete query returning early-only,
late-only or no deny records remains eligible for normal correlation and
missing-record diagnostics. The number of permission-shaped failures does not
determine whether collection completed, and completion does not certify OS
delivery.

Choose the numeric budgets and public representation of timeout/overflow
details under section 2 before changing the evidence shape. Those choices must
preserve this retention policy and unavailable-correlation behavior.

#### Scan padding

**Structure.** For ordered client timestamps, use a symmetric two-second pad:
scan from `floor(client start) − 2 s` to `ceil(client end) + 2 s`. Document it in
`docs/limits.json` and regenerate its copies. Floor/ceil accommodates the query
interface's whole-second precision. The additional pad allows for differences
between the client's wall clock and the archive's displayed event timestamps;
rounding alone can leave arbitrarily little slack at either boundary. State
that purpose in the limit's `counting` text without promising delivery or
coverage under every clock condition. Reversed client timestamps still produce
`invalid_window`, null scan bounds and no query; padding must not repair them.

**Representation.** `window.start` and `window.end` keep their meaning, the
whole-second UTC strings handed to `log show` and mirrored back by the
observer, now padded. `started_at_unix_ms` and `ended_at_unix_ms` keep the raw
client span. Add `window.pad_seconds` (2). An absent field in an older envelope
means 0, which is what those envelopes did, so the change is additive and needs
no envelope contract bump under the rule in [docs/CONTRACT.md](docs/CONTRACT.md);
the documented derivation "widened to whole seconds" gains the pad. The
window's four disclaimers stay false.

**Membership.** Supported records anywhere in the padded query interval are
eligible for correlation, including both padding regions. The live case must
independently calculate `query_start_s` and `query_end_s`, check the reported and
mirrored bounds against them, and use those padded bounds for returned-record
membership. Keep the retired control's separate `retired_end_s` at the unpadded,
rounded client end, with `retired_start_s = retired_end_s - 10`; its argv,
timestamp checks and reported interval must all use that pair. Neither interval
establishes that a record was caused by an attempt in this run.

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
  [observer.py](tests/fixtures/deny_capture/observer.py) must include independently
  timed events in both padding regions and immediately outside both query
  bounds. Require inclusion and supported correlation inside the pad, and
  exclusion outside it. Preserve equal-span and rollback controls.
- `documented_controller_limits` in [run_flow.rs](controller/src/run_flow.rs)
  and a new `docs/limits.json` entry (section `evidence`, value 2, unit
  seconds, value and boundary checks) regenerated by `docs/generate_limits.py`;
  the prose in [LIMITS.md](docs/LIMITS.md) and the user guide.
- The live case's window assertions, padded membership assertion
  (`query_start_s <= at <= query_end_s`) and separately bounded retired-interval
  replay; the catalog description ("requests the full client interval");
  [controller/README.md](controller/README.md) and
  [docs/PolicyWitness.md](docs/PolicyWitness.md) `window` descriptions.
- The consumer passes the window through; the shape validator must accept the
  new key.

### 4. Make the default battery independent of OS emission

Implement the following controls as ordinary repository tests and fixtures,
reusing existing coverage. Permanent tests must not require gitignored evidence
or refer back to the investigation record.

The preservation oracle is controlled input with independently specified
expected records and associations. A live capture establishes only what that
invocation returned; checks of its contents do not prove that PW retrieved every
record the OS could supply. Keep these claims separate in test assertions and
coverage descriptions.

- Replay complete, early-only, late-only and empty inputs through the actual
  parser, receiver, correlation, serialization and consumer paths. Include
  disabled/unavailable capture, wrong bounds, malformed replies, unrelated PIDs,
  operation/path mismatches, ambiguous candidates and truncated output.
- Exercise collector process faults with bounded fixtures: no exit, no EOF,
  excessive stdout/stderr, failure to launch, nonzero/signal exit, and cleanup
  errors. Assert preserved native/execution evidence, the expected collection
  status, bounded retention, and independently observed cleanup where possible.
  Cover both subprocess boundaries and budget edges, including JSON expansion,
  a valid diagnostic reply after inner failure and an incomplete outer reply.
  Give filtering and normal-capacity cases fixed expected outputs; limit-fault
  cases must exercise the declared cutoff rather than merely accept any error.
- Require positive supplied-event cases to retain all eligible events and
  associations. Deliberately dropping a line or supplied event, inventing an
  association, suppressing every capture, or changing an execution answer must
  cause a default correctness test to fail. Accepting empty OS output must not
  make a broken collector pass these positive controls.
- Rework `witness_contract/deny_capture_covers_the_run`: preserve native-attempt,
  scan-contract and diagnostic checks; remove the requirement that the OS store
  the final denial. Check records returned by that capture invocation against
  the padded query bounds, expected candidate associations and missing-record
  diagnostics. A successful empty capture is admissible. Do not infer retrieval
  completeness from those checks; controlled cases supply the positive coverage.
- In `witness_contract/worker_termination_and_log_correlation`, assert the
  capture state and its supporting facts as well as correlation, using the
  live-result rules below. A generic `unavailable` correlation is insufficient.
- Preserve `witness_contract/max_targets_reply_survives`' runner-reply survival
  checks. Replace its unconditional live observer non-truncation requirement
  with the same live-result rules. Establish observer capacity for the chosen
  256-step input in a controlled case; no live log-volume bound follows from
  the specimen's step count.

For live cases, distinguish a successful capture (including empty output) from
documented budget exhaustion and unexpected failures. Budget exhaustion is an
admissible log-channel outcome only with supporting boundary, limit/deadline and
cutoff observations, preserved execution evidence, and the required unavailable
correlation/null associations. It is not positive capture coverage. Missing
required helpers, blocked required access, malformed complete replies or
wrong-window replies, unexplained process failures, and violations of supervision
or cleanup contracts still fail the relevant check. A generic unavailable status
cannot excuse them.

The retired-window query checks its own invocation and interval;
it is not an oracle for record presence in the earlier capture. Do not require
cross-query record equality or inclusion. A record first observed by a later
query is an availability difference between observations, not proof of delayed
OS delivery or of a PW defect. Preserve such differences as diagnostics without
making them a default correctness failure.

Keep real record-availability measurements separate from the default correctness
gate. If a registered OS-behavior probe is retained, make it explicitly opt-in,
retain every initial result, and report its sample and environment. It must not
serve as a required dependency of the default case or retry until green.

### 5. Document and validate the resulting contract

Update the root description, controller contract, user guide, limits inventory,
test catalog and suite documentation where behavior actually changes. Change
`docs/limits.json` and regenerate its copies for new enforced limits. If envelope
fields, statuses or window semantics require a contract version change, use
`docs/contract.json` and its generator; preserve historical envelope meaning and
update consumer fixtures. No runner-response or worker-ABI change is presumed.

For `deny_capture_covers_the_run`, update its module docstring, the description
in [tests/catalog.json](tests/catalog.json) and the case's section in
[tests/suites/witness_contract/README.md](tests/suites/witness_contract/README.md)
to describe conditional live-record checks and mandatory supplied-event
coverage. Keep their scan-bound descriptions consistent with the padding.

Document the query predicate, byte-counting boundaries, budget relationships,
failure reasons and cleanup observations in the permanent contracts. State the
partial-collection policy and the distinct claims of live and controlled cases
there so deletion of this plan leaves no implementation or test dependency on
it. Keep repository links to the investigation record confined to associated
`*-PLAN.md` files.

Run the affected Rust/consumer checks and meaningful collector failure controls,
then build and validate a signed app containing the implementation. Run the
relevant live witness cases and the integrated default battery against that
artifact, retaining all failures rather than crediting only a passing retry.
The evidence must distinguish implementation correctness, equipment failures,
documented collection-limit outcomes and measured OS record availability.

## Acceptance

- **Execution authority.** For a fixed runner reply and runner-client capture,
  changing log contents, availability or collector behavior leaves the runner
  reply, execution result, CLI exit status, predictions, native attempts,
  comparisons, drift, disposition and termination cause unchanged. This holds
  for matching records, no records and collector failures.
- **Collection budgets.** Collection and cleanup have finite, documented and
  enforced time and output budgets at both the observer and `log show`
  boundaries. Byte limits apply to each raw stdout/stderr stream before parsing
  or controller filtering; `log show` output is already query-filtered. Derived
  data and serialization remain bounded, and the outer budget accommodates an
  inner capture within its limits. A stalled process, a pipe held open or
  excessive output cannot make PW wait indefinitely to emit an available runner
  result. Truncating a buffer after an unbounded read fails this condition.
- **Query selection.** The OS query admits the supported Sandbox worker
  process/PID message forms. Unrelated messages containing the PID's digits in
  a different PID, path or other text do not qualify on that basis. Exact
  parsed-PID checking remains required before association.
- **Record preservation.** For complete valid inputs within the declared
  budgets, every supported deny record emitted by the query survives collection
  and parsing with its raw evidence and provenance. Losing even one such
  supplied record fails this condition, regardless of live OS record
  availability.
- **Correlation.** For a successful complete capture, each retained record
  receives all and only the candidate associations supported by the worker PID,
  operation and path evidence. Ambiguity remains explicit. Unrelated PIDs,
  unsupported matches and invalid candidate references cannot acquire worker
  or step attribution.
- **Capture state.** The envelope and consumer distinguish successful empty
  collection, partial collection, unavailable evidence and disabled collection.
  Incomplete collection retains available diagnostics but yields unavailable
  correlation and null associations; incomplete output never passes as complete.
  `permission_failures_without_record` is null unless correlation reaches
  `pid_match` or `no_match` with per-step comparisons present. When those
  conditions hold, it lists exactly the permission-shaped steps without a
  captured candidate, or `[]` if none qualify. That list makes no claim about
  the OS store.
- **Scan bounds.** For ordered client timestamps, the requested bounds are
  `floor(client start) - 2 s` through `ceil(client end) + 2 s`; successful capture
  requires the observer to mirror them. Raw client timestamps remain separate,
  `pad_seconds` is 2, and its absence in an older envelope means 0. Records in
  both padding regions are eligible for supported correlation, and live
  membership checks use the padded bounds. The retired control uses its own
  unpadded client-end interval. Clock rollback retains null bounds and prevents
  querying. Neither padding nor successful capture asserts complete delivery,
  exact run membership or protection against PID reuse.
- **Cleanup evidence.** The logging operation accounts for both the observer
  and its log child. A termination request, confirmed exit and unconfirmed
  cleanup remain distinguishable in the reported evidence. Sending a signal
  or observing only the observer's exit does not establish that both exited.
- **OS-independent default battery.** No default correctness assertion requires
  macOS to emit a selected denial, and passing does not depend on retries until
  a record appears. Empty results and supported budget-exhaustion outcomes are
  admissible; software or equipment contract failures cannot pass as generic
  unavailable evidence. A later query cannot make record absence in an earlier
  capture a correctness failure or establish its cause.
- **Positive capture coverage.** The default battery exercises the production
  parser, receiver, correlation, serialization and consumer paths using
  controlled input with independently specified positive results, including
  query selection, pad-region records and declared capacity. Dropping a supplied
  eligible record, inventing an association or suppressing all capture must fail
  a correctness assertion even when every live query returns no records or
  exhausts its collection budget. Live conditional checks alone cannot satisfy
  this condition.
- **Plan removal.** Permanent tests and contract documentation remain usable
  after this plan is deleted and without gitignored investigation artifacts.
  Implemented limits, field meanings and partial-collection behavior are
  documented outside the plan. Repository links into the investigation record
  occur only in associated `*-PLAN.md` files.
