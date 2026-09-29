# Best-effort deny-log evidence

Status: Complete. Sections 1–5 are implemented and accepted on macOS 14.8.3
(23J220). The final integrated default battery passed all 165 cases with no
skips or unrun cases against the unchanged signed development app. No open
prerequisites or acceptance failures remain. Earlier failures retain their
original results; the checkpoints below distinguish them from final acceptance.
The isolated archive prerequisite is resolved; see
[LOG-ARCHIVE-FIXTURE-PLAN.md](LOG-ARCHIVE-FIXTURE-PLAN.md).
This plan remains on disk for review; permanent contracts and tests do not
depend on it.

## Associated commits

The table groups the planning revisions and lists each implementation/fixture
commit. `git log -- BEST-EFFORT-LOG-PLAN.md LOG-ARCHIVE-FIXTURE-PLAN.md` gives the
individual planning edits. The commit carrying this final status and table is
the plan-only completion record.

| Commit | Scope | Review summary |
| --- | --- | --- |
| `facbe77` through `3794562` | Planning | Diagnosis, ownership, budgets, scan padding, acceptance criteria and the required archive oracle. |
| `97f4d09` | Sections 1–2 | Separate execution/log ownership; bounded supervision, timeout override, exact worker-token predicate and source controls. Archive acceptance was still pending. |
| `298692d` | Archive prerequisite | Scope isolated fixture generation and reader acceptance. |
| `9b09ad9` | Archive fixture | Commit the real 14.8.7 archive, independent corpus/manifest, generation recipe and provenance. |
| `d17d289` | Fixture review | Abort generation on corpus comparison failure; accepted fixture branch brought into main. |
| `a50164c` | Section 3 | Pad client-span queries by two seconds, preserve raw bounds and candidate evidence, and cover historical windows. |
| `fbcb9bf` | Section 4 | Supplied-text preservation/capacity controls, both-boundary failure coverage and live checks independent of OS emission. |
| `72f0516` | Section 5 | Finish permanent contracts, correct direct-wrapper registration, pass the integrated default battery and protect evidence. |

## Execution checkpoint

- The field-ownership and in-checkout consumer audit is recorded in
  [the controller contract](controller/README.md#execution-and-log-evidence-ownership).
  Production assembly completes execution and disposition before collection;
  typed log output attaches only log-owned fields without changing the wire
  shape, statuses or contract versions.
- The production assembly control covers all current collector states, retained
  diagnostic events, absent authoritative worker identity, legacy replies and
  a witnessed host-cleanup cause. Timeout and overflow are included, alongside real subprocess failure
  controls. Window replay now uses that same assembly path before
  independent consumer recovery.
- Validation: `tests/run.sh --suite unit --case blackbox_e2e/checker_controls`
  passed all four selected cases (160 Rust unit tests, formatting, the four
  explicitly selected disposition controls, and the blackbox/consumer/oracle
  controls). Local evidence is in
  `tests/out/runs/best-effort-log-section1-checks/`. The app has not been rebuilt
  for this section; signed-artifact/live validation remains later work.
- Initial resource measurements on macOS 14.8.3 (23J220) used the existing
  observer with a fixed absent worker PID and a seven-second padded query window.
  All three fixed samples succeeded: 277, 166 and 162 ms; each returned 1,340
  observer-response bytes and 50 inner stdout bytes, with no events or stderr.
  These empty-query samples are cost observations, not defaults, capacity
  evidence or a runtime bound. The script, helper hash, arguments and every
  sample are retained locally at
  `/private/tmp/pw-best-effort-prerequisites-f7dte1_g/`.
- Archive prerequisite is resolved: the isolated 14.8.7 fixture and independent
  manifest pass the 14.8.3 reader, including both required predicate mutation
  controls. No ambient developer archive was collected. Provenance is in the
  [fixture README](tests/fixtures/deny_capture/README.md); local review and
  merged-main acceptance receipts are linked from the archive plan.
- For the later signed build, follow `docs/SIGNING.md`: Developer ID signing
  through `build.sh` (`YOLO=1` can select the identity); `entitlement-jail` is the
  explicitly supplied keychain profile for notarization if that flow is run.

## Section 2 checkpoint

Implementation, local validation and the real OS predicate-selection proof
are complete. The linked archive plan records reader acceptance and mutation
controls.

- `--log-timeout-ms` validates a finite positive allowance before runner work,
  including when logging is disabled. The default is 10,000 ms; both supervisors
  share the same monotonic deadline and one fixed 1,000 ms cleanup grace.
  Runner timeout semantics and all existing contract versions are unchanged.
- Both pipes are bounded during reads: log-show stdout 1 MiB and stderr 128 KiB;
  observer stdout 32 MiB and stderr 128 KiB. Event, JSON-structure, candidate and
  serialization guards bound derived data. Limits and controls are recorded in
  `docs/limits.json`, the generated guide and the controller contract.
- The observer starts in an owned group; its log child inherits that group.
  Non-reaping exit observation preserves ownership until group signalling is
  finished. Bounded reaping and an `ESRCH` probe establish group absence;
  missing replies never invent log-child identity or wait results. Controls
  cover leader death before any reply with orphan pipes open and closed,
  launch/nonzero/signal/read/wait failures, overflow, hangs and failed cleanup.
- Failed/incomplete capture retains bounded raw diagnostics or an intact
  observer reply, but withholds all correlations. Serialized execution evidence
  and exit status remain invariant. The OS predicate now requests complete
  worker/PID message tokens; the accepted archive verifies positive selections
  and rejects the old-bare-digit and false-predicate mutations.
- On macOS 14.8.3 (23J220), three fixed seven-second padded-window queries with
  the rebuilt signed observer took 639, 395 and 372 ms. Each returned 2,499
  observer bytes, 51 inner stdout bytes, no stderr and no events. The 10-second
  default provides headroom over these observations; it is not a maximum OS
  query-cost claim or a guarantee of complete live evidence.
- Controlled capacity preserved 256 records: 142,848 inner stdout bytes and
  3,111,267 observer bytes. Exact inner stdout/stderr caps with maximum JSON
  escaping produced 25,953,682 observer bytes, below 33,554,432. Independent
  candidate controls preserve 256 unique associations and reject excess count,
  charged bytes and step counts. These measurements do not bound kernel volume.
  Scripts, hashes, arguments and raw measurement outputs are retained at
  `/private/tmp/pw-best-effort-section2-8p6n2nm0/`.
- Final source validation passed seven registered cases: 188 Rust unit tests,
  formatting, four explicitly selected disposition controls, source/limits/wire
  drift checks and blackbox/consumer/oracle controls. Evidence:
  [accepted source run](tests/out/runs/best-effort-log-section2-accepted-source/run.json).
- The final app and ZIP were rebuilt and Developer ID signed through
  `YOLO=1 ./build.sh`. Signature/evidence verification, three smoke cases and
  termination/log correlation passed in the
  [signed run](tests/out/runs/best-effort-log-section2-signed/run.json).
  Its integration failure was a new test reading CLI admission errors from
  stderr instead of JSON stdout. The corrected assertion, formatting and all
  14 integration tests passed against unchanged artifact bytes in the
  [replacement integration run](tests/out/runs/best-effort-log-section2-integration-fixed/run.json).
  The integration-test assertion was the only code change after accepted source
  validation; production code and the other tested paths were unaffected.
  Earlier failures and runs remain intact. The final build receipt is
  `/private/tmp/pw-section2-build-accepted.log`. This is a signed development
  build; no notarization submission was made.
- The original [missing-fixture failure](tests/out/runs/best-effort-log-section2-archive-pending/run.json)
  remains intact. The fixture is now present and the required default case
  passes on 14.8.3; this resolves that failure without an implicit skip.

## Section 3 checkpoint

Implementation and section-specific validation are complete. The live case
reaches the existing emission requirement that section 4 will replace.

- Ordered timestamps scan `floor(client start) - 2 s` through
  `ceil(client end) + 2 s`, with `window.pad_seconds: 2` and unchanged raw client
  milliseconds. Missing padding in older envelopes means zero. Equal spans
  remain nonempty; rollback still withholds both bounds and never starts a scan.
  Contract versions and all four window disclaimers are unchanged.
- Independent timestamp controls include both pads, exact query boundaries and
  one millisecond outside each. Complete full, early-only, late-only and empty
  replies retain every eligible candidate and missing-record diagnostic through
  production assembly, serialization and independent consumer recovery.
  Existing bounded-failure controls retain diagnostic replies without correlation.
- The live window case checks the padded query and mirrored bounds. Its retired
  ten-second control ends at the separate unpadded, rounded client end. The
  existing mandatory final-denial assertion remains for section 4 to replace.
- `docs/limits.json` records the two-second allowance and its clock-difference
  purpose, with compiled-value and boundary checks; limits/guide copies and the
  affected controller, evidence and test contracts are updated.
- All eight selected source cases passed: 189 Rust unit tests, four explicitly
  selected disposition controls, formatting, source/limits/wire drift checks,
  consumer controls and the real archive query. Evidence:
  [accepted source run](tests/out/runs/best-effort-log-section3-accepted-source/run.json).
  The [initial source failure](tests/out/runs/best-effort-log-section3-source/run.json)
  is retained: one pre-existing receiver fixture still mirrored unpadded bounds;
  its literal bounds were corrected before the accepted run.
- `YOLO=1 ./build.sh` reached signed app/ZIP completion; the build receipt is
  `/private/tmp/pw-section3-build.vGE1rX`. The surrounding command failed afterward
  when assigning zsh's read-only `status` variable, after the build's `DONE`
  output. Signed-artifact validation checks those unchanged bytes. No
  notarization submission was made.
- The [signed run](tests/out/runs/best-effort-log-section3-signed/run.json)
  completed all ten selected cases: nine passed (signature/evidence and release
  controls, all 14 CLI integration tests, three smoke cases and termination/log
  correlation). The app remained unchanged throughout validation.
- `deny_capture_covers_the_run` verified the 20,083 ms native run, exact padded
  query/mirrored bounds, both real-tool intervals, candidate association,
  consumer recovery and missing-record diagnostics. Both collection boundaries
  completed without cutoff. It then failed the existing mandatory final-denial
  assertion: the early record was present and the late record absent. The
  [observations](tests/out/runs/best-effort-log-section3-signed/suites/witness_contract/deny_capture_covers_the_run/artifacts/observations.json)
  and all raw receipts remain intact; there was no retry. This is the section 4
  live-acceptance work, not a passing default-battery claim.

## Section 4 checkpoint

Implementation, controlled validation and signed live validation are complete.
The section 5 checkpoint records the final contract audit and integrated
default-battery acceptance.

- The observer's unchanged `log show` collector/parser now lives in
  `controller/src/log_show.rs`, used by production and supplied-text replay.
  Full, early-only, late-only and empty cases cross that parser, a supervised
  receiver, production assembly, serialization and independent consumer
  recovery. Fixed expectations cover raw lines, candidate indices, ambiguity,
  unrelated child/neighbour PIDs and operation/path mismatches. Native replies,
  execution answers and CLI status stay invariant across disabled/unavailable,
  wrong-window, malformed, inner nonzero/overflow and interrupted outer replies.
- A fixed 256-record input preserves every 511-byte target and candidate through
  the same path. Its initial unoptimized replay hit the ten-second collection
  budget; the diagnostic run took 10.05 seconds including consumer recovery.
  The capacity oracle now uses a declared, fixed 30-second test allowance, not
  a changed production default. Initial failure and diagnostic receipts remain
  at `/private/tmp/pw-section4-initial-replay.txt` and
  `/private/tmp/pw-section4-capacity-diagnostic.log`. This measures capacity for
  the supplied corpus, not a bound on live volume.
- The finite override replay keeps the same execution and query bounds: a
  100 ms allowance cuts off a slow query, 1,500 ms completes it, and a stalled
  query still exhausts 1,500 ms. Both boundaries use the same decoded absolute
  budget; byte caps and cleanup grace do not change. Existing supervisor tests
  now exercise launch, exit/signal, closed-pipe hang, read and cleanup faults
  at both boundaries, with independent PID/group absence checks. Existing
  orphan, byte-edge, JSON-expansion and derived-limit controls remain mandatory.
- The default `witness_contract/log_capture_controls` case supplies 52 success
  and rejection cases. Shared live assertions require intact successful
  collection or observed deadline/limit exhaustion with correct boundary,
  byte counts and confirmed cleanup. Budget exhaustion has null correlations;
  missing helpers, blocked access, wrong bounds, malformed complete replies,
  unexplained exits and unsupported cleanup cannot borrow an unavailable status.
  Default selection includes both this case and the strict archive case, as
  recorded in `/private/tmp/pw-section4-default-selection.json`.
- The live window case no longer requires the OS to record either denial. It
  preserves native attempts, padded bounds, returned-record candidate checks
  and missing-record diagnostics. Its retired query is a separate invocation;
  differences are retained without cross-query record-presence assertions.
  Termination correlation and maximum-target reply survival use the same
  live acceptance rules. The latter keeps all native reply-capacity assertions.
- Five actual production mutations in an isolated source copy each fail the
  positive replay test: dropped line, dropped event, invented association,
  suppressed capture and changed execution answer. A baseline passed; every
  mutation was restored and the primary checkout was never mutated. Logs,
  source hashes, patches and results are at
  `/private/tmp/pw-section4-mutations-g1tic865/results.json`.
  Existing false-predicate and actual former bare-PID archive mutation proofs
  remain recorded in the completed archive plan; predicate generation is unchanged.
- All nine selected [source cases](tests/out/runs/best-effort-log-section4-accepted-source/run.json)
  passed: 192 Rust unit tests, four disposition controls, formatting, drift and
  limits/contracts checks, consumer controls, live-acceptance controls and the
  real archive query. The final both-boundary exit/hang assertion correction
  passed in [the final unit run](tests/out/runs/best-effort-log-section4-final-unit/run.json).
  The subsequently added interrupted-JSON replay also passed its focused test;
  its receipt is `/private/tmp/pw-section4-prefix-replay.log`.
- `YOLO=1 ./build.sh` rebuilt and Developer ID signed the app and ZIP, with
  receipt `/private/tmp/pw-section4-build.OvpNU9`. No notarization submission
  was made.
- All eight [signed cases](tests/out/runs/best-effort-log-section4-signed/run.json)
  passed: signatures/evidence, all 14 integration tests, three smoke cases and
  all three revised live witnesses. Artifact integrity remained unchanged.
  The 20,080 ms window run captured both early and late records; the two
  enabled termination captures completed, and the maximum-target capture
  returned 231,411 observer bytes. These are observations of those invocations,
  not delivery guarantees or live-volume limits; the earlier section 3 failure
  remains intact.
- Final review made completed-query record checks conditional on complete
  collection, so a path cut inside a retained diagnostic prefix cannot fail
  an otherwise supported budget outcome or acquire a candidate claim. The
  actual live content checker is exercised with full, empty and interrupted
  inputs by [the final 52-control run](tests/out/runs/best-effort-log-section4-final-live-controls/run.json).
  This test-only refinement followed signed validation and did not change app
  bytes. No live capture was retried to obtain a preferred availability result.

## Section 5 checkpoint

Complete. Permanent documentation, generated copies, test registration and the
integrated signed-artifact validation are accepted.

- The root description, controller contract, user guide, limits inventory,
  failure/consumer contract, coverage map and fixture catalog agree on execution
  independence, padded bounds, the exact OS predicate, shared monotonic budget,
  raw-byte counting, cutoff reasons, partial evidence and owned cleanup.
  The guide shows how to recognize `deadline` and use a finite larger
  `--log-timeout-ms` without changing scan bounds, runner timeout or byte limits.
  Obsolete 8 MiB/full-buffer observer descriptions are corrected, while the
  runner-client and sbpl-check receiver contracts remain distinct.
- `docs/limits.json` counting prose was clarified and its document/guide copies
  regenerated; enforced values did not change. Request schema 3, response
  schema 11, worker ABI 7 and controller envelope 3 remain current. The additive
  collection facts do not reinterpret historical envelopes: missing supervision
  remains unknown, missing padding means zero and stored trailing scans remain
  trailing. Existing consumer controls and generated-contract checks pass.
- `YOLO=1 ./build.sh` rebuilt and Developer ID signed the app and ZIP and staged
  the updated guide. The [audit receipts](tests/out/runs/best-effort-log-section5-accepted/contract-audit/README.md)
  retain the build log, build stamp, source snapshots, ZIP/guide hashes, link
  checks and plan-independence check. This is a signed development build; no
  notarization submission was made.
- The [first default battery](tests/out/runs/best-effort-log-section5-default/run.json)
  completed all 165 cases: 164 passed and `shell_helpers/script_groups` failed.
  Its independent wrapper inventory caught the missing `log_capture_controls.sh`
  entry in the direct witness-suite wrapper; the public catalog already included
  the case. The missing entry was added without changing the signed app. The
  failed run remains intact and is not credited as a passing integrated run.
- The [final default battery](tests/out/runs/best-effort-log-section5-accepted/run.json)
  (`PW_TEST_OUT_DIR=tests/out/runs/best-effort-log-section5-accepted tests/run.sh`)
  passed **165/165 cases**, with zero skips, unrun cases or harness errors.
  Coverage includes 192 Rust unit tests, four explicitly selected disposition
  controls, 381 Swift tests, 14 CLI integration tests, 52 independent live
  acceptance controls, the required archive query and all three live log
  witnesses. The archive method is separately registered and executed, even
  though it is excluded from the ordinary Rust unit batch. Signature/evidence
  checks passed, and all four before/after app inventories from the two default
  runs are equal. Source, ZIP and staged guide stayed unchanged during the
  accepted run; subsequent retention-index and plan edits record acceptance only.
- The first default run observed an early record but no late record in its
  20,087 ms window witness. It correctly passed the revised log contract and
  retained the missing-record diagnostic. The final 20,079 ms run observed both.
  Both completed collection without cutoff. These are separate availability
  observations; the second default run was required by the wrapper correction,
  not by a desired log result. The earlier section 3 emission-dependent failure
  remains preserved with its original status.
- The [mutation applicability audit](tests/out/runs/best-effort-log-section5-accepted/contract-audit/mutation-applicability.json)
  verifies unchanged predicate, command builder and archive oracle, and the
  behavior-preserving parser move. Both original predicate mutations still
  provide pre-parser rejection evidence. All five replay-mutated production
  paths match their accepted hashes. Later test-only additions leave the
  decisive positive assertions unchanged; the reviewed differences are retained
  explicitly and do not acquire retrospective mutation credit. The final
  default battery covers those additions. Original mutation commands, patches,
  outputs and archive runs are copied into the retained audit directory.
- The [failure classification](tests/out/runs/best-effort-log-section5-accepted/contract-audit/failure-classification.json)
  distinguishes corrected test/registration errors, resolved missing-archive
  equipment, the debug capacity deadline and observed live-record absence.
  `tests/RETAINED.json` protects all 20 related managed runs, including the
  original failures. No failed result was overwritten or converted to success.
  Permanent tests use checked-in fixtures and constructed input; no permanent
  code or documentation links to either investigation plan. All acceptance
  claims remain usable without this file or the local audit receipts.

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
observed normal costs with headroom; measurements choose defaults, not a maximum
query duration that every machine must meet.

#### Collection deadline and user control

Add `policy-witness run --log-timeout-ms <n>` as a per-run override of the
collection deadline. Accept positive integer milliseconds that can be represented
and added to the monotonic clock without overflow; reject invalid, zero or
unrepresentable values before invoking the runner. There is no unlimited value.
Keep `--timeout-ms`'s runner-client meaning unchanged. With `--no-log-capture`,
validate the option but launch no collector. A larger log timeout lets a user
accommodate a slower archive scan without changing the specimen, query window
or runner timeout; it increases the optional wait before envelope delivery and
does not promise a record.

Start the collection deadline immediately before observer launch. Pass that
same monotonic deadline to the observer for supervising `log show`; startup and
inner collection must consume the shared allowance, not restart it. Use a shared
monotonic clock domain for that argument. A directly invoked observer, including
the retired-window control, uses the documented finite default when no deadline
is supplied. The controller enforces the outer deadline even if the observer
stops responding. On expiry, stop collection and enter a separately documented,
fixed cleanup grace. The maximum supervised wait is the chosen collection
allowance plus that
grace; retries, parsing and reporting must not restart either budget. Record the
effective timeout, whether it came from the default or CLI, elapsed time and
cutoff reason when collection is attempted. Byte caps and cleanup grace remain
independent limits; this override buys waiting time only.

#### Output budgets and query selection

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
in paths or other text. Exercise that selection through the real `log show`
predicate engine against the committed archive fixture specified in section 4;
parser replay and argv string assertions cannot establish this behavior. Keep
filtering in the OS query so irrelevant records are excluded before they consume
output budgets; a cap only on post-filter events would leave transport and
parsing unbounded.

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

#### Ownership and cleanup without an observer reply

Use a dedicated process group created as part of spawning the observer, before
its program runs, with PGID equal to the observer PID. The controller therefore
knows the cleanup target from its own spawn result. Rust's
[`CommandExt::process_group(0)`](https://doc.rust-lang.org/std/os/unix/process/trait.CommandExt.html#method.process_group)
provides this launch-time setup. The observer must launch `log show` in that
inherited group, without creating another group or session. A failure to
establish the group fails collector launch; never fall back to signalling the
controller's own group. No PID announcement on stderr or other lifecycle
transport is required for this design.

The controller owns group cleanup, while the observer normally waits for its
direct log child and includes that child's PID and wait observation in its
reply. On a collection failure or observer exit, finish cleanup of any remaining
group members even if the leader has exited or both pipes reached EOF. Keep the
observer unreaped while group signalling is possible: observe its exit without
reaping (for example, `waitid` with `WNOWAIT`), issue any required group
`SIGKILL`, then perform bounded reaping and group-absence observation. This pins
the leader's PID through signalling and avoids targeting a reused PGID. Never
send a later group signal after releasing that ownership. If ownership cannot
be established or is lost, withhold group signalling and report unconfirmed
cleanup with the reason. A pipe held open by the orphaned log child must not
defeat either deadline.

Report three separate facts: the controller's observer wait result, the
observer-reported log-child identity/wait result if received, and the
controller's group cleanup request and outcome. Without a reply, the individual
log-child PID and exit status may remain unknown; group ownership still permits
cleanup. After signalling and reaping, bounded group probes that report no such
group (`ESRCH`) establish group absence, not an invented child wait status.
Other probe results or exhausted cleanup grace leave group cleanup unconfirmed.
Sending a signal, observer exit or pipe EOF alone cannot confirm group cleanup.
An observer-died-first case must attempt owned-group cleanup and can confirm
absence; it must not automatically become an unconfirmed-cleanup result.

Test this ownership and observation sequence with owned subprocess fixtures,
including observer death before any reply. Keep the implementation confined to
logging unless a shared primitive can be reused without changing other capture
contracts.

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
for deny records or to recover output held by a terminated observer. Cleanup
uses the controller-owned process group from section 2 and requires no such
transport. Some valid deny records may therefore remain uncorrelated; that is
the accepted cost of avoiding a separate event-recovery and partial-correlation
contract.

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
  applies the pad and carries `pad_seconds`; `observer_window_matches` keeps
  checking the mirrored bounds. `observer_argv` separately carries the collection
  deadline from section 2. [runner_client.rs](controller/src/runner_client.rs)
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

#### Archive fixture for OS query selection

Add `tests/fixtures/deny_capture/query_predicate.logarchive`, an independent
`query_predicate.json` expectation manifest and a fixture README. Establish this
fixture before crediting the query-selection change in section 2. The archive
must be a real, small, self-contained archive readable by `/usr/bin/log show`,
committed with all required metadata; saved JSON or syslog text is not a
substitute. Create it once from controlled test messages in an isolated capture
environment and inspect its contents before committing. Do not collect and
commit an ambient developer-machine log store. Record the generation recipe,
source macOS version, verified reader versions and file hashes in the fixture
documentation. Regeneration is a maintenance operation, never a default-test
setup step or a response to a failed assertion.

The manifest specifies fixed worker names/PIDs, UTC query bounds, the complete
test-message inventory and the exact selected message multiset for each query.
Include every supported worker message form, multiple worker/PID queries, and
negative records with another process name, a neighbouring or longer PID, or
the requested PID's digits only in a path or unrelated deny text. Test-only
user-space messages may reproduce the supported Sandbox message forms; include
an actual emitting PID different from the worker PID embedded in the message.
This fixture establishes query behavior for those forms, not kernel emission
or authenticity. Derive expectations from the declared corpus, independently
of PW's predicate, parser and captured output.

Register a required default case, `witness_contract/log_query_predicate_archive`.
Use a test harness that calls the production predicate and `log show` command
builder, substituting only the archive source and the manifest's worker/window
inputs. Keep the production selection and output flags; do not copy the
predicate into the test, bypass generation with the observer's `--predicate`
override, or evaluate it in a substitute engine. Expose archive input through
an internal test seam, without adding a shipped controller flag or reading the
current system store. Require the production observer to use that same builder.

First query the archive without the predicate under test and require every
positive and negative corpus record to be present. Then run the production
query and compare the selected messages and multiplicities directly with the
manifest, before PW's parser or PID filtering can hide missing or extra rows.
Retain both queries' arguments, exit results and bounded raw output as case
evidence. Also pass the selected output through the production parser and
require the independently specified deny events. The positive set must be
nonempty: replacing the production predicate with `FALSEPREDICATE` must fail
this default case, as must restoring the bare-PID-digit alternative that admits
the negative records.

Give this fixed corpus a finite test budget with headroom and verify archive
readability on supported macOS test hosts. Missing/unreadable fixture data,
blocked tool access, nonzero exit, timeout, overflow and an empty or incorrect
selection fail this case; none is an admissible live-availability outcome or an
implicit skip. Use the repository's existing sandboxed-harness rerun procedure
for a tool-access refusal. The test requires the OS query engine, but no new
record emission, privileged collection, network download or later live query.

#### Collection, correlation and live controls

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
- Exercise group ownership with fixtures where the observer dies before any
  child announcement or JSON, while its log child stays alive with an inherited
  pipe, and where the child closes its pipes but remains alive. Independently
  verify group membership and eventual absence, keep individual child status
  unknown when no report supplied it, and reject leader-only cleanup. Include
  unresolved signal/probe failure and exhausted-grace cases that require unconfirmed
  cleanup; verify that no signalling follows release of the leader's PID.
- Exercise `--log-timeout-ms` parsing, the default, invalid values and disabled
  capture. A controlled slow query must reach the short deadline and complete
  under a larger override with the same execution result and query bounds.
  Check that the effective value reaches both supervisors, neither restarts the
  allowance, and output caps and cleanup grace stay unchanged. A still-stalled
  collector must exhaust the larger finite allowance as well.
- Require positive supplied-event cases to retain all eligible events and
  associations. The archive and replay controls must fail when the production
  query excludes all records, a line or supplied event is dropped, an
  association is invented, every capture is suppressed, or an execution answer
  changes. Accepting empty live OS output must not make a broken collector pass
  these positive controls.
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
and archive-query coverage. Register and document the archive case's required
equipment and strict positive/negative oracle; add its corpus, provenance and
regeneration instructions to the permanent fixture documentation. Verify that
the normal default selection includes the case. Keep scan-bound descriptions
consistent with the padding.

Update the CLI usage in [cli.rs](controller/src/cli.rs), the CLI surface in
[controller/README.md](controller/README.md), argument handling in
[run_flow.rs](controller/src/run_flow.rs), CLI integration coverage and the user
guide together for `--log-timeout-ms`. Document how to recognize a collection
deadline and increase it on a slower machine, including the extra cleanup grace
and unchanged byte limits. Publish the default and fixed grace in the limits
inventory, and document the controller-to-observer deadline argument.

Document the query predicate, byte-counting boundaries, budget relationships,
failure reasons and process-group cleanup observations in the permanent
contracts. Distinguish group absence from a received log-child wait result and
unknown child identity when no observer reply arrives. State the partial-collection
policy and the distinct claims of live and controlled cases there so deletion
of this plan leaves no implementation or test dependency on it. Keep repository
links to the investigation record confined to associated `*-PLAN.md` files.

Run the affected Rust/consumer checks, the real archive-query case and meaningful
collector failure controls. Demonstrate that a production predicate selecting
nothing and the removed bare-PID-digit alternative each make the archive case
fail, then restore the implementation. Build and validate a signed app
containing the implementation. Run the relevant live witness cases and the
integrated default battery against that artifact, retaining all failures rather
than crediting only a passing retry.
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
- **User-controlled waiting.** A valid `--log-timeout-ms` override changes the
  collection allowance at both supervisors without restarting it or changing
  the runner timeout, query bounds, output limits or cleanup grace. Effective
  settings and cutoff evidence are reported. Controlled slow input can complete
  under a larger allowance; a hang remains bounded by that allowance plus the
  fixed grace. Invalid values fail before execution, and disabled capture still
  launches no collector.
- **Query selection.** The OS query admits the supported Sandbox worker
  process/PID message forms. Unrelated messages containing the PID's digits in
  a different PID, path or other text do not qualify on that basis. Exact
  parsed-PID checking remains required before association. A required default
  case runs real `log show` against a committed archive using the production
  query builder and requires the manifest's nonempty positive set and exclusion
  of its negative records before PW parsing. A predicate that selects nothing
  or restores bare-digit matching fails; argv text checks alone do not qualify.
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
- **Cleanup evidence.** The controller owns the observer's process group from
  spawn and can clean up its inherited log child after observer death without
  receiving a child PID. Signalling finishes before the leader is reaped.
  Observer wait status, received log-child wait status, group termination
  requests, confirmed group absence and unconfirmed cleanup remain distinct.
  No reply leaves individual child status unknown, not group cleanup unattempted.
  Signal delivery, observer exit and pipe EOF alone never establish group
  absence. Controlled orphan cases require independently verified group cleanup;
  unresolved observation failures retain an explicit unconfirmed result, and loss of
  ownership prevents further group signals.
- **OS-independent default battery.** No default correctness assertion requires
  macOS to emit a selected denial, and passing does not depend on retries until
  a record appears. Live captures may return empty results or supported
  budget-exhaustion outcomes; the fixed archive must meet its manifest's exact
  selection. Software or equipment contract failures cannot pass as generic
  unavailable evidence. A later live query cannot make record absence in an
  earlier capture a correctness failure or establish its cause.
- **Positive capture coverage.** The default battery exercises the production
  query through the real OS engine and the production parser, receiver,
  correlation, serialization and consumer paths using controlled input with
  independently specified positive results, including pad-region records and
  declared capacity. Excluding all fixture records in the query, dropping a
  supplied eligible record, inventing an association or suppressing all capture
  must fail a correctness assertion even when every live query returns no
  records or exhausts its collection budget. Live conditional checks alone
  cannot satisfy this condition.
- **Plan removal.** Permanent tests and contract documentation remain usable
  after this plan is deleted and without gitignored investigation artifacts.
  Implemented limits, field meanings and partial-collection behavior are
  documented outside the plan. Repository links into the investigation record
  occur only in associated `*-PLAN.md` files.

## Deviations recorded after the audit

Noticed during the 2026-09-29 audit of the completed work. Each is a deviation
from the text above and is in place in the permanent contracts and tests.

- Correlation resolves the step-provenance join once per capture instead of per
  event. The 256-record capacity replay runs under the production default
  allowance; the 30-second test allowance named in the section 4 checkpoint is
  gone.
- The log child stops `log_report_reserve` (1,000 ms) before the shared
  deadline so the observer's report, including an inner deadline cutoff,
  reaches the controller. Section 2 passed one deadline to both supervisors
  with no reserve.
- The controller envelope is 4. `timeout`, `overflow`, `supervision`,
  `processing_cutoff` and `window.pad_seconds` are recorded under that bump
  rather than as additive fields of envelope 3.
- The response schema is 12. `steps[].attempt.path_diagnostics` carries the
  host's after-orchestration `realpath_resolved` and `parent_realpath_resolved`
  forms of file and exec targets, correlation admits them as a named
  `path_sources` entry, and `normalized_path` is gone. Section 3 limited targets
  to the submitted, requested and observed paths.
- `permission_failures_without_record` is documented as naming steps without a
  captured candidate, with no claim about the OS store; the earlier wording
  said the log holds no record.
