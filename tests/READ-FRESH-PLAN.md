# Correct `read_fresh` denial-log association

Restore the documented eligibility of a `file/read_fresh` attempt for a
`file-read-data` denial-log event. The implementation change belongs in the
controller's candidate matcher. Establish it with constructed evidence, retain
the separation between log association and execution evidence, and clarify the
shared reading rule for permission failures without a candidate record.

At the investigated source revision, `653e049`,
[`attempt_operations`](../controller/src/sandbox_log.rs) omits `read_fresh`,
although the [denial-log correlation contract](../docs/PolicyWitness.md#denial-log-correlation)
explicitly includes it. With an otherwise usable matching event, the controller
retains the event and reports `correlation_status: "pid_match"`, but omits the
step from `sandbox_log_capture.step_denies`. A permission-failing step remains
in `runner_sandbox_diagnostics.permission_failures_without_record`. An event
shared with another eligible attempt can also lose its ambiguous association.

The other mappings have different responsibilities. Swift's
[`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
and Python's [`expected_relations`](lib/consumer.py) relate submitted query and
attempt scopes. Rust selects exact event operations eligible for association.
For example, `create` has no single comparison operation but admits both
`file-write-create` and `file-write-data` events; exec compares against
`process-exec*` but associates `process-exec`. Preserve those distinctions.
The fresh-read worker's open, stat, read and close observations do not imply
eligibility for every operation that those calls could encounter.

Existing fresh-read coverage does not establish log association. The
[comparison matrix](fixtures/comparison/README.md) includes S26 and S27, but
its [live driver](suites/witness_contract/check_comparison_matrix.py) disables
log capture. The [extension controls](suites/witness_contract/check_extensions.py)
also disable it. Rust's matcher and assembly controls establish other candidate
matching behavior, while [`consumer.denials`](lib/consumer.py) resolves supplied
associations without discovering omitted candidates. Consumer validation alone
therefore cannot serve as the regression's success criterion.

The intended scope is the Rust eligibility arm, focused tests and their owning
suite description, and the shared reading-rule clarification. Admission, worker
execution, comparison production, log collection, and matching gates retain
their current behavior. A common mapping generator or cross-language mapping
refactor is outside this change.

1. **Correct the existing Rust eligibility arm.**

   In `attempt_operations` in
   [sandbox_log.rs](../controller/src/sandbox_log.rs), add `read_fresh` alongside
   `open_read` and `access` for the exact event operation `file-read-data`.
   Preserve matching against submitted attempts, positive worker PID, unique
   request/reply step-ID joins, exact operation/path matching, provenance checks,
   availability gates and collection budgets. In particular, do not add a
   completed-result or permission-failure prerequisite: candidates can survive
   interrupted result publication, and association does not classify execution.

   Prepare the regression below before retaining the correction, so its failure
   on the original arm is observed. If the arm is already corrected when this
   plan is executed, temporarily remove only this eligibility entry to establish
   the same discriminating failure, then restore it.

2. **Add a matcher regression with an independent expected result.**

   Add a focused test beside `match_step_denies` and the existing
   `attempt_operation_and_paths_are_independent_of_query` control in
   [sandbox_log.rs](../controller/src/sandbox_log.rs). Use one submitted
   `file/read_fresh` attempt with step ID `s` and target `/attempt`, one uniquely
   joined reply step, authoritative worker PID `42`, and a constructed event
   with PID `42`, operation `file-read-data` and path `/attempt`. Give the
   submitted query a different operation and target, such as `file-write-data`
   and `/query`.

   Assert literally that event index `0` has candidate IDs `["s"]`, association
   `"candidate"`, and matching evidence naming `file`, `read_fresh`,
   `file-read-data`, `submitted_attempt`, `/attempt`, and the applicable path
   sources. The expected operation, candidate IDs, cardinality and provenance
   come from this explicit fixture and the documented contract. Do not derive
   them by calling, enumerating, copying programmatically, or generating from
   `attempt_operations`, the comparison mappings, or the matcher output. Reusing
   fixture constructors is fine only when their inputs and expected values stay
   independent of eligibility logic. An `open_read` case with the same event is
   a useful positive control, but its output must not become the fresh-read
   case's oracle.

   Include negative events for a wrong PID, unrelated path, query-only
   operation/target match, and unlisted `file-read-metadata` or wildcard
   operation. Require the exact association list, so unexpected extra candidates
   also fail. Exercise a reply without completed attempt evidence to preserve
   the matcher contract. Existing duplicate-ID and path-provenance controls can
   continue to own those unchanged rules.

   The original eligibility arm must fail the explicit positive assertion with
   zero candidates despite the supplied matching event. Compilation, fixture
   validation or capture failures do not establish this regression.

3. **Verify the serialized envelope and distinguish evidence states.**

   Add a focused control at the existing `attach_sandbox_logs` test seam in
   [run_flow.rs](../controller/src/run_flow.rs), using
   `observer_windows_survive_association_serialization_and_consumer_recovery`
   and `collector_states_preserve_the_serialized_execution_half` as patterns.
   Feed constructed observer output through the existing observer parser and
   production assembly, then serialization and the independent Python consumer.
   This needs no unified-log access or new production override.

   Use a valid current-schema reply for step `s`: a completed worker fresh open
   failure with `fresh_read.open_rc: -1`, `open_errno: 1`, absent later syscall
   observations, `attempt.outcome: "read_failed"`, and comparison observation
   `"permission_failure"` with basis `"permission_errno"`. Include the required
   lifecycle and phase evidence. Keep the query scope different from the attempt
   scope. The shared [reply helpers](../controller/src/reply_fixtures.rs) currently
   lack full fresh-read construction; provide explicit native evidence or a
   narrow fixture extension rather than inheriting an open-only failure result.

   For the same fixed execution reply, assert these literal expectations. The
   single relevant event has PID `42`, operation `file-read-data` and path
   `/attempt`; all rows with a capture use admitted observer versions.

   | Constructed log evidence | Capture status | Correlation status | `step_denies` | `permission_failures_without_record` |
   | --- | --- | --- | --- | --- |
   | Valid requested window and the relevant event | `captured` | `pid_match` | One candidate for `s` at event index `0` | `[]` |
   | Valid window, empty events and `observed_deny: false` | `captured` | `no_match` | `[]` | `["s"]` |
   | Valid window, relevant operation/path but event PID `99` | `captured` | `no_match` | `[]` | `["s"]` |
   | Valid window, worker PID but unrelated operation or path | `captured` | `pid_match` | `[]` | `["s"]` |
   | The relevant event retained in a reply for the wrong window | `window_mismatch` | `unavailable` | `null` | `null` |
   | Capture disabled; collector must not be called | Capture object `null` | `not_attempted` | No capture object | `null` |

   Assert capture admission, window, retained event contents, authoritative PID
   and `observed_deny` independently of candidate assertions. In the first row,
   require the matching event and usable capture before checking the candidate;
   never condition the positive expectation on whether matching returned
   anything. In the wrong-window row, require the retained matching event as
   well as withheld association. These controls distinguish an eligibility
   defect from genuine absence, irrelevant evidence and unusable evidence.
   Do not calculate the expected missing-record list by subtracting the
   producer's returned candidates; use the literal lists above.

   Cover both `probe_plan` and explicit `phases`. Add a repeated fresh-read case
   with distinct IDs `s1` and `s2` on the same target, preferably in successive
   phases: one event must produce `["s1", "s2"]` and `"ambiguous"`, with two
   matching-evidence entries. No event timestamp or phase ownership establishes
   a unique occurrence. Include a mixed `open_read`/`read_fresh` pair if it fits
   the same fixture, with the same explicit two-candidate expectation.

   Across capture variants, require identical runner replies, comparisons,
   native fresh-read observations, CLI status, execution result and disposition
   fields. Reuse `execution_bytes` to compare serialized execution after removing
   only its established log-owned fields and envelope timestamp. Require raw
   events to survive and the Python consumer to validate each envelope and
   recover the explicitly expected candidates and missing-record diagnostics.
   Reader acceptance is supplementary to those expectations. Keep the existing
   signaled-run and incomplete-result controls that establish no causal
   inference from a candidate.

4. **Clarify the shared reading rule and run the owning checks.**

   Edit rule 3 in the shared reading rules of
   [FAILURE-PROPAGATION-CONTRACT.md](FAILURE-PROPAGATION-CONTRACT.md#reading-rules).
   State that permission-shaped failures alone do not establish sandbox cause,
   candidate associations do not prove causation, and
   `permission_failures_without_record` names permission-failing steps without
   a candidate in this capture when correlation is available. Its contents say
   nothing about absence from the OS log store. Preserve the existing rule's
   treatment of other failures and nonzero spawned-child exits.

   Regenerate the copied guide with `python3 docs/generate_limits.py` and check
   it with `python3 docs/generate_limits.py --check`. The guide's event-operation
   table already describes the intended behavior. Update the
   [unit suite README](suites/unit/README.md) to identify what the new controls
   establish. Inline Rust tests run in the existing `unit/rust.unit` case and
   need no additional catalog case.

   Retain the original-arm failure and corrected result separately. Use fresh
   output names for each invocation; for final verification, run from the root:

   ```sh
   PW_TEST_OUT_DIR=tests/out/runs/read-fresh-candidates \
     tests/run.sh --suite unit --case source_drift/limits_documentation
   ```

   The source-drift check establishes that the shared rule and generated guide
   agree; it does not establish candidate eligibility. The Rust controls supply
   that behavioral evidence. A live run would test OS event production and
   delivery, a different question, so it is not an acceptance prerequisite for
   this correction. Broaden verification only if the implementation reaches
   another boundary.

5. **Confirm contract scope and acceptance.**

   This restores an already specified event eligibility rule. Under
   [contract evolution](../docs/CONTRACT.md#when-a-number-moves), request,
   response and envelope versions remain unchanged, as do shape goldens. The
   Rust matcher and test changes require no worker-identity regeneration. The
   documented output change is a candidate where the event qualifies, a smaller
   missing-record list for affected permission failures, and ambiguity where
   multiple attempts qualify. `correlation_status` remains based on captured
   PID matches, not candidate membership.

   Acceptance requires the positive regression to fail specifically at missing
   eligibility on the original arm and pass with the correction, the evidence
   state controls to retain their distinct results, consumer recovery and
   execution-preservation assertions to pass, and the selected suite and
   generator checks to succeed. No result may upgrade a candidate to proof of
   sandbox cause or prediction/enforcement agreement. If implementation requires
   changing field meanings, native execution, collection gates or comparison
   mappings, reconsider the scope and contract decision before extending it.
