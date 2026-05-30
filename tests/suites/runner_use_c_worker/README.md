# runner_use_c_worker

End-to-end coverage for the C-worker code path gated by
`_test_overrides.use_c_worker=true` (RUNNER-RESHAPE-PLAN Step 6.8a).
PWRunnerService still routes through the legacy Swift worker by
default; this suite exercises the alternative path while it sits
behind the flag, ahead of Step 6.8b's default flip.

The gated path runs `pw-probe-runner` (attempts) + `sb_api_validator
--batch` (sandbox_check verdicts) as two children of the XPC service,
joined into a single `PWRunnerRunResult` envelope by
`CWorkerOrchestrator`. Step 6.4's v4 schema additions
(`validator_subprocess`, `steps[].drift`) carry the new evidence.

## What's pinned

Three test_ids, each driving a real specimen through the
controller → XPC service → orchestrator → both children:

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
   - `_test_overrides.use_c_worker` mirrored back

2. **bare_deny_default** — the downstream bug-report shape: bare
   `(deny default)` with one file read. The Swift worker dies here
   without producing step results; the C worker survives. Asserts:
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

## What this suite does NOT cover

- **Validator failure outcomes** (`validator_spawn_failed`,
  `validator_no_reply`, `validator_decode_failure`,
  `validator_unavailable`). Step 6.5 added the constants and
  classifier rules; coverage for each lands as a separate suite
  driven via `_test_overrides.validator_executable_path` and similar
  seams (analogous to the existing `runner_outcome_*` suites).
- **`runner_timeout` on the C-worker path.** Driven by
  `_test_overrides.worker_post_apply_hang_ms` once a dedicated suite
  lands (the unit test `postApplyHangMs > sentinelTimeoutMs produces
  done=false` already pins the underlying mechanism).
- **`sandbox_apply_failed`.** The Step 6.5 vocabulary handles it;
  e2e coverage via a malformed-SBPL specimen is straightforward but
  not yet scripted.
- **The default flip.** Step 6.8b makes the C-worker path the
  default; until then, this suite is the only consumer of the
  gated path.

## Run

```
./tests/run.sh --suite runner_use_c_worker
```

## Artifacts

Per test_id: `specimen.json`, `run.json` (the full controller
envelope), `assert.log` (Python assertion output).
