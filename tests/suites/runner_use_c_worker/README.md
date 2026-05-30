# runner_use_c_worker

End-to-end coverage for the runner's C code path. Specimens here
intentionally carry no `_test_overrides`, so each run also
double-checks that production-shape requests assemble a complete
v4 envelope without test-seam help.

The runner runs `pw-probe-runner` (attempts) + `sb_api_validator
--batch` (sandbox_check verdicts) as two children of the XPC
service, joined into a single `PWRunnerRunResult` envelope by
`CWorkerOrchestrator`. The v4 schema additions
(`validator_subprocess`, `steps[].drift`) carry the new evidence.

## What's pinned

Ten test_ids, each driving a real specimen through the
controller → XPC service → orchestrator → both children. The first
three pin the basic v4 envelope shape; the rest are regression
guards for the request-validation and drift-classification rules:

1. **happy_default_allow** — `(allow default)` + one file read.
   Asserts:
   - `schema_version == 4`
   - `validator_subprocess` populated with clean exit
   - `runner_subprocess` populated, `pid` mirrors back at top level
   - `steps[0].sandbox_check.outcome == "allow"` (validator)
   - `steps[0].attempt.observed_path == "/private/etc/hosts"` (worker
     F_GETPATH; validates path_diagnostics enrichment also fires on
     the new path)
   - `steps[0].drift == false`
   - `test_overrides == null` (production-shape run, no test seam)

2. **bare_deny_default** — the downstream bug-report shape: bare
   `(deny default)` with one file read. The C worker survives this
   policy. Asserts:
   - run completes (`normalized_outcome == "ok"`, both children
     clean-exited)
   - validator predicted `deny`, attempt observed `open_failed` with
     `errno ∈ {EPERM=1, EACCES=13}`
   - `drift == false` (validator and attempt agree on deny)

3. **prediction_unavailable_pair** — `(iokit-open-service,
   iokit_registry_entry_class)` is in `predictionUnavailableOpFilters`,
   so the orchestrator skips the validator probe entirely and
   synthesizes the verdict locally. Asserts:
   - `sandbox_check.outcome == "prediction_unavailable"`, `rc == -1`
     (sentinel, matches `ProbeRunner`'s short-circuit shape)
   - `drift == null` (no comparison possible)
   - the attempt still ran

4. **duplicate_step_id_rejected** — request with two probes that
   share a `step_id`. Asserts `normalized_outcome == "bad_request"`
   before any worker spawn (pre-spawn `validateProbePlanForCWorker`).
5. **unsupported_attempt_per_step_skip** — two-step plan: a valid
   file probe plus a step with an `attempt.kind`/`action` combo the
   C worker doesn't implement. Asserts the run completes (`ok`), the
   good step runs end-to-end, and the unrecognized step gets
   `attempt.outcome == "unsupported"` while its `sandbox_check`
   verdict still runs. `drift` is `null` for the unsupported step.
6. **worker_timeout_ms_honored** — `_test_overrides.worker_timeout_ms`
   paired with `_test_overrides.worker_post_apply_hang_ms` makes the
   host SIGKILL the hung C worker. Asserts `runner_timeout`.
7. **drift_null_for_non_policy_failure** — non-sandbox lookup
   failure (`BOOTSTRAP_UNKNOWN_SERVICE`). Asserts `drift == null`
   because the attempt didn't fail for a sandbox-policy reason.
8. **sandbox_check_pid_matches_worker** — `sandbox_check.pid` is
   the sandboxed worker PID consistently across both
   validator-backed and orchestrator-synthesized verdicts.
9. **drift_null_for_dac_eacces** — DAC EPERM/EACCES on a file
   denied by filesystem perms (not the sandbox). Asserts
   `drift == null` to avoid false libsandbox-drift attribution.
10. **access_failure_classified** — `access(R_OK)` on a denied path
    surfaces as `attempt.outcome == "access_failed"` with errno
    preserved.

## What this suite does NOT cover

- **Validator failure outcomes** (`validator_no_reply`,
  `validator_decode_failure`, `validator_unavailable`). The
  `witness_contract/validator_spawn_failed_reports_degraded` suite
  covers `validator_spawn_failed`; the remaining three are wired in
  the classifier (`CWorkerOrchestrator`) but lack dedicated e2e
  specimens.
- **`sandbox_apply_failed`.** Reachable when `sandbox_apply`
  returns nonzero inside the C worker; not yet driven by an
  e2e specimen.

## Run

```
./tests/run.sh --suite runner_use_c_worker
```

## Artifacts

Per test_id: `specimen.json`, `run.json` (the full controller
envelope), `assert.log` (Python assertion output).
