# runner_use_c_worker

End-to-end coverage for the runner's C code path. Specimens here
normally carry no `_test_overrides`, so those runs also
double-check that production-shape requests assemble a complete
envelope without test-seam help. `worker_timeout_ms_honored` uses the timeout
and post-apply hang overrides to exercise host failure handling.

The runner runs `pw-probe-runner` (attempts) + `sb_api_validator
--batch` (sandbox_check answers) as two children of the XPC
service, joined into a single `PWRunnerRunResult` envelope by
`CWorkerOrchestrator`, with `validator_subprocess` and each step's
`comparison` record carrying the joined evidence.

## What's pinned

Each test_id drives a real specimen through the
controller → XPC service → orchestrator → both children. The first
three pin the basic envelope shape; the rest are regression
guards for the request-validation and comparison rules:

1. **happy_default_allow** — `(allow default)` + one file read.
   Asserts:
   - the current response schema (the envelope shape this case pins)
   - `validator_subprocess` populated with clean exit
   - `runner_subprocess` populated, `pid` mirrors back at top level
   - `steps[0].sandbox_check.outcome == "allow"` (validator)
   - `steps[0].attempt.observed_path == "/private/etc/hosts"` (worker
     F_GETPATH; validates path_diagnostics enrichment also fires on
     the new path)
   - `steps[0].comparison`: `observation: succeeded`, `matched`,
     `same_submitted`, `order: query_first`, no limitations
   - `test_overrides == null` (production-shape run, no test seam)

2. **bare_deny_default** — the downstream bug-report shape: bare
   `(deny default)` with one file read. The C worker survives this
   policy. Asserts:
   - run completes (`normalized_outcome == "ok"`, both children
     clean-exited)
   - validator answered `deny`, attempt observed `open_failed` with
     `errno ∈ {EPERM=1, EACCES=13}`
   - `comparison.observation == "permission_failure"` with basis
     `permission_errno`: the record classifies the failure and does
     not attribute it to the sandbox

3. **prediction_unavailable_pair** — `(iokit-open-service,
   iokit_registry_entry_class)` is in `predictionUnavailableOpFilters`,
   so the orchestrator skips the validator probe entirely and
   synthesizes the answer locally. Asserts:
   - `sandbox_check.outcome == "prediction_unavailable"`, `rc == -1`
     (sentinel, matches `ProbeRunner`'s short-circuit shape)
   - `comparison.limitations == ["query_plan:prediction_unavailable_pair"]`
     with `order: unestablished`
   - the attempt still ran

4. **duplicate_step_id_rejected** — request with two probes that
   share a `step_id`. Asserts `normalized_outcome == "bad_request"`
   before any worker spawn (pre-spawn `validateProbePlanForCWorker`).
5. **unsupported_attempt_per_step_skip** — two-step plan: a valid
   file probe plus a step with an `attempt.kind`/`action` combo the
   C worker doesn't implement. Asserts the run completes (`ok`), the
   good step runs end-to-end, and the unrecognized step gets
   `attempt.outcome == "unsupported"` while its `sandbox_check`
   query still runs; its comparison carries `attempt:unsupported`
   with both relations `unresolved`.
6. **worker_timeout_ms_honored** — a 2-second worker deadline and 8-second
   post-apply hang produce a host SIGKILL timeout after an allowed write.
   Independent file bytes must change before the envelope is checked. The
   completed write retains its ID, paths, successful attempt, real validator
   answer and `observation: succeeded`; `partial_steps=false`. Also checks
   CLI/runner failure, termination, the deadline diagnostic, and both honored
   overrides. Uses the checker and capture described in
   `runner_outcome_runner_timeout`.
7. **sandbox_check_pid_matches_worker** — `sandbox_check.pid` is
   the sandboxed worker PID consistently across both
   validator-backed and orchestrator-synthesized answers.
8. **access_failure_classified** — `access(R_OK)` on a denied path
   surfaces as `attempt.outcome == "access_failed"` with errno
   preserved and `observation: permission_failure`.
9. **sandbox_check_unsupported_operation_diagnostic** — a bare
   `process-exec` query is rejected by the native channel
   (`unsupported_operation`, `rc=-1`, EINVAL, an error naming the
   wildcard spelling) while the attempt spawns normally; the record
   reports `operation_relation: different` (the bare spelling is not
   the attempt's mapped `process-exec*`), `order: unestablished` and
   no limitation. The `process-exec*` sibling step answers `allow`.
10. **sandbox_check_path_unresolved_prediction_unavailable** — a path
    query whose target does not resolve at planning is excluded
    (`query_plan:path_unresolved_at_planning`) while the attempt
    still runs and reports its own result.

The exec cases share `tests/fixtures/exec/helper.c` and its build script.
They check baseline execution, argument and stdout/stderr capture, and
output truncation. `exec_attempt_without_baseline_fails_cleanly` requires a
`(deny default)` spawn to fail with `child_pid: 0` and a permission errno as a
`permission_failure` observation; `exec_attempt_with_baseline_succeeds`
requires the spliced `exec_baseline` policy to spawn the helper with an allow
answer and `observation: succeeded` (basis `spawned_child`).
`exec_attempt_args_and_stderr_round_trip` executes a nonzero exit (37)
followed by a successful exit (0); both must retain their output and status,
and the first keeps `observation: succeeded` beside its failed exec result
without aborting the plan. The fixture's bytes and statuses are checked
directly by `exec_fixture`. Deadline cleanup and output retention are covered
by `runner_exec_lifecycle`.

## What this suite does NOT cover

- **Validator failure outcomes** (`validator_no_reply`,
  `validator_decode_failure`, `validator_unavailable`). The
  `witness_contract/validator_spawn_failed_reports_degraded` suite
  covers `validator_spawn_failed`; the remaining three are wired in
  the classifier (`CWorkerOrchestrator`) but lack dedicated e2e
  specimens.
- **Precise native application failure.** The worker's status word alone
  cannot identify the failed operation; the worker failure record does, and
  `witness_contract/worker_progress_and_failure` owns that coverage. Published
  preparation/application failures use `runner_failed`.

## Run

```
./tests/run.sh --suite runner_use_c_worker
```

## Artifacts

Per test_id: `specimen.json`, `run.json` (the full controller
envelope), `assert.log` (Python assertion output).
