# `controller/` (Rust controller: specimen-first CLI)

This is developer documentation for the Rust code in `controller/`. It builds the command-line controller that ships as:

- `dist/PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to print a stable, machine-readable JSON witness for each run. The runner is an unsandboxed XPC host with two short-lived children: `pw-probe-runner` applies the policy and attempts operations; `sb_api_validator --batch` queries that worker PID. Their observations are joined into one envelope. The controller treats that as an implementation detail of the runner — it only consumes the host's reply.

For the Swift runner implementation details, see `runner/README.md`.

## What lives in `controller/`

Core controller modules:

- `controller/src/main.rs` — entry point and module wiring
- `controller/src/cli.rs` — CLI usage text + top-level dispatch
- `controller/src/run_flow.rs` — run orchestration and JSON envelope assembly
- `controller/src/runner_select.rs` — runner selection + provenance
- `controller/src/runner_client.rs` — wrapper around `pw-runner-client`
- `controller/src/sandbox_log.rs` — unified-log capture mapping for sandbox denials
- `controller/src/runner_commands.rs` — external runner install/list/status/verify/remove/validate

Support modules:

- `controller/src/app_layout.rs` — app bundle layout + embedded tool resolution
- `controller/src/plist.rs` — PlistBuddy helpers for Info.plist lookups
- `controller/src/bundle.rs` — bundle metadata reader for external runners
- `controller/src/request_patch.rs` — request JSON injection helpers
- `controller/src/policy_check.rs` — host-side `sbpl-check` wiring
- `controller/src/utils.rs` — shared time + output helpers
- `controller/src/evidence.rs` — evidence manifest parsing + verification
- `controller/src/json_contract.rs` — JSON envelope rendering with sorted keys
- `controller/src/runner_manager.rs` — external runner registry + launchd wiring

Standalone helper tools (embedded into the `.app`):

- `controller/src/bin/sandbox-log-observer.rs` → `dist/PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name
- `controller/src/bin/sbpl-check.rs` → `dist/PolicyWitness.app/Contents/MacOS/sbpl-check`
  - Compiles SBPL policies and reports compiler errors before the runner launches
- `controller/tools/sb_api_validator/sb_api_validator` — embedded inside
  each XPC service bundle as `…/Contents/MacOS/sb_api_validator`. The
  runner host launches it once per run in `--batch` NDJSON mode to
  cross-check `sandbox_check` verdicts inline alongside the C worker.
- `controller/tools/pw_probe_runner/pw_probe_runner` → embedded INSIDE
  each XPC service bundle at
  `…/Contents/XPCServices/<svc>.xpc/Contents/MacOS/pw-probe-runner`
  (not in the app's top-level `Contents/MacOS/`). The runner host
  resolves it relative to its own bundle so built-in and BYOXPC
  runners both pick up the correct copy. It owns the post-apply
  syscall surface and is the runner's production code path.

## CLI surface (contract)

The launcher intentionally exposes a minimal surface:

```text
policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--no-log-capture] [--runner-mode <standard|byoxpc>]
policy-witness runner <command> [options]
```

### `run`

Runs a **single runner evaluation** against the selected runner service:

- Reads a request JSON file (runner request schema) that contains:
  - a sandbox policy (`sbpl` source),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Starts a fresh runner instance (one XPC host + two short-lived children), applies the policy exactly once inside the C worker, executes the probe plan and validator batch in parallel, and returns the runner's structured JSON result.
- Captures supporting evidence (best-effort) using `sandbox-log-observer` and attaches it to the output. Pass `--no-log-capture` to skip this scan entirely: the `log show` deny scan is archive-bound and costs seconds per run (independent of `--log-last`), so callers that don't consume the deny evidence can opt out to reclaim it.
- The embedded `sb_api_validator` runs in `--batch` NDJSON mode (one
  process per run), spawned by the runner host alongside the C
  worker. It reads NDJSON probes from stdin and writes NDJSON
  verdicts to stdout; the host folds each verdict into the matching
  `runner_result.steps[*].sandbox_check` block and surfaces process
  metadata as `runner_result.validator_subprocess`. See
  `tests/suites/validator_batch_mode/README.md` for the wire contract.
  Validator coverage rules:
  - **Predicted** filter kinds (the validator calls `sandbox_check`):
    `path`, `global_name`, `local_name`, `none`. `none`-filter probes
    call `sandbox_check(pid, op, 0)` with no filter argument and emit
    `filter_value: null` / `filter_type_id: 0` in the verdict.
  - **Skipped — prediction unavailable** (verified-unreliable op+filter
    pairs the runner accepts but deliberately does not predict for; see
    `docs/PolicyWitness.md` "Filter kinds where prediction is unavailable"):
    `(iokit-open-service, iokit_registry_entry_class)`,
    `(iokit-open-user-client, iokit_user_client_class)`,
    `(sysctl-read, sysctl_name)`. The runner short-circuits to
    `sandbox_check.outcome="prediction_unavailable"` (`rc=-1`); the
    `attempt` result is the reliable evidence.
  - **Rejected upstream**: filter kinds the validator could in
    principle author but the runner refuses to admit into the probe
    plan (`MACH_PORT`, `PREFERENCE_DOMAIN`, …). `validateSandboxChecks`
    rejects requests carrying these as `bad_request` before any worker
    spawn; adding one to the supported set requires empirical
    verification that the userland predicate matches kernel
    enforcement (see `tests/suites/witness_contract/harness/verify_filter_id.sh`).
- Prints a single JSON envelope to stdout (no output directories; stdout is the artifact).
- Emits `data.runner_provenance` and `data.app_provenance` to keep results auditable.

Exit codes:

- `0`: `result.ok=true`
- `1`: `result.ok=false`
- `2`: usage / tool error (prints a JSON error envelope)

### Output contract

Runner responses use version 7: every step contains `deny_signal: null` because
that channel is unobserved. Legacy signal objects remain readable by the Swift
decoder; external typed readers requiring an object must support null. The Rust
controller forwards the runner object without version coercion. Optional
subprocess objects may be omitted/null; per-step signal/errno/drift nulls require
key presence. Worker ABI 6 and request schema 1 are separate contracts.
Response 7 adds an explicit per-step comparison and submitted attempt provenance;
`drift` projects limited recorded-outcome agreement/disagreement, while uncertain
attribution or scope retains null. Older replies preserve their original semantics.
See the [comparison contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#public-representation-and-meaning).


The controller prints one JSON envelope to stdout (`kind="run"`). It contains:

- `data.runner_result`: the runner's JSON (if parseable)
- `data.runner_client`: argv + stdout/stderr + timing, exact received/retained
  stream byte counts and `capture_limit_bytes` (1 MiB). `stdout_capture_error`
  identifies controller prefix loss; `stdout_parse_error` identifies malformed
  untruncated JSON/UTF-8. Full output is collected first; this is not a streaming
  allocation bound. Synthetic non-invocations have null byte counts.
- `data.policy_check`: independent `sbpl-check` report, requested only on
  `xpc_error`. It describes that helper's compilation, not the missing worker's
  progress or the cause of a lost reply. Worker failures use `runner_failed`;
  ABI 6 operation/result evidence identifies compilation, setup and application
  independently. The controller retains `runner_subprocess.worker_evidence` and
  `policy_transfer_error` without interpreting their diagnostic codes.
- `data.policy_augmentation`: present only when `policy.augments` (see
  docs/PolicyWitness.md → Augments) was non-empty. Records
  `{ applied: [name, ...], original_sha256, applied_sha256 }` so
  downstream readers can distinguish the caller's submitted source
  from the spliced source the runner actually compiled. Absent on
  every run that did not opt into augments.
- `data.runner_startup_diagnostics`: extra context when XPC startup fails
  (rare in practice — the unsandboxed host always replies unless launchd
  or codesign reject the bundle outright). This `xpc_error` path is the only
  one that triggers a host-side `sbpl-check` compile (to populate
  `policy_check_status` and disambiguate the failure).
- `data.runner_sandbox_diagnostics`: process disposition and optional denial
  correlation, independent of outcome labels. `worker_pid` comes only from
  `runner_subprocess.pid`. `process_disposition` is `no_worker`, `unconfirmed`,
  `clean_exit`, `nonzero_exit`, or `signaled`; abnormal/unconfirmed disposition
  has `termination_cause="unknown"`. `capture_status` distinguishes disabled,
  no worker and observer availability. `correlation_status` is `not_attempted`,
  `unavailable`, `no_match`, or `pid_match`. `first_deny` is an `{event_index}`
  reference into `sandbox_log_capture.deny_events`, not a termination cause.
- `data.sandbox_log_capture`: optional observer evidence, also captured for
  successful runs; null when disabled or no authoritative worker PID exists.
  `window` records trailing `last` and explicitly disclaims structured event
  timestamps, exact run membership, step ordering and PID-reuse protection.
  `step_denies` contains event references with candidate step IDs: one candidate
  is `candidate`, repeated matching attempts are `ambiguous`. Matching requires
  worker PID, exact attempt-relevant operation and exact target/path evidence.
  Attempt kind/action come from the request joined by unique step ID, never the
  independent sandbox-check query. `matching_evidence` records each candidate's
  mapped operation, submitted kind/action, matched path and path sources.
  Unowned `normalized_path` alone is not a match source. Unmatched events remain
  in `deny_events`.
  [Operation mapping and correlation limits](../docs/PolicyWitness.md#denial-log-correlation).
- `data.runner_provenance`: runner identity + entitlements metadata
- `data.app_provenance`: embedded app evidence metadata (and optional verification)

`data.sandbox_log_capture.capture_status` values:

- `captured`: observer succeeded, no error reported
- `blocked`: unified log access blocked (see `blocked_reason`)
- `error`: observer returned an error or non-zero exit
- `parse_error`: observer stdout was not valid JSON
- `requested_unavailable`: observer could not be executed

Optional:

- `PW_VERIFY_EVIDENCE=1` runs a manifest hash verification pass and includes a
  `data.app_provenance.evidence_verify` report in the output.

### Runner selection (external entitlements)

`run` can target specific runner modes by adding one of the following to the request:

- `runner: { mode, id, service, required_entitlements }` (preferred)
- Legacy top-level fields: `runner_id`, `runner_service`, `required_entitlements`, `runner_mode`

If `required_entitlements` is present, the controller enforces a **superset**
check against the runner’s recorded entitlements before dispatch.

The only built-in mode is `standard` (default). If `runner.mode` is
present and an external runner is selected, it must equal `byoxpc` —
the only supported external runner kind.

### `runner` (external runner manager)

These commands manage external runners signed with user entitlements:

```text
policy-witness runner install --bundle <path-to-xpc-bundle> [--kind byoxpc] [--service-name <name>] [--scope user|system]
                             [--identity <codesign-id>] [--entitlements <plist>]
                             [--allow-adhoc]
                             [--env KEY=VALUE]
                             [--skip-bootstrap]
policy-witness runner list
policy-witness runner status --id <runner-id> | --service-name <name>
policy-witness runner verify --id <runner-id> | --service-name <name> [--timeout-ms <n>]
policy-witness runner remove --id <runner-id> | --service-name <name> [--skip-bootout]
policy-witness runner validate
```

Install writes a launchd plist, bootstraps the service, and records runner
metadata (entitlements + signature) in the local registry. The registry lives
under `~/Library/Application Support/PolicyWitness/runners.json`.

Notes:
- BYOXPC is the only external runner kind. The bundle must be an XPC service
  directory (`CFBundlePackageType=XPC!`); the Mach service name equals the
  bundle's `CFBundleIdentifier`. The executable is derived from
  `<bundle>/Contents/MacOS/<CFBundleExecutable>`.
- `--entitlements` requires either `--identity <id>` or `--allow-adhoc`. Without one of those the supplied entitlements would not be embedded into the binary, so the call is rejected up front.
- A BYOXPC runner copied from the shipped `PWRunner.xpc` inherits its signed-caller check (`PWRunnerRequireSignedCaller`): sign it with a Developer ID whose Team ID matches the caller (`--identity`), or remove those Info.plist keys for an ad-hoc/local runner. An ad-hoc runner that keeps the keys has no Team ID and is rejected at connect time (`xpc_error`). See docs/PolicyWitness.md → "Caller authentication and ad-hoc signing".
- `runner verify` defaults to a 5-second timeout (override with `--timeout-ms`).
- `runner remove` always persists the registry change. `launchctl bootout` or plist-removal failures are surfaced in the envelope's `data.warnings` rather than aborting the call, so dirty launchd state cannot strand a registry entry.
- `runner status`, `runner verify`, and `runner remove` emit an envelope with the operation's `kind` and `result.normalized_outcome = "not_found"` (exit code 2) when the lookup key is not in the registry, instead of plain-text stderr.
- `runner validate` re-reads each registry entry's on-disk signature and entitlements. It does not reconcile against launchctl or `LaunchAgents/`.

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `dist/PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.


Response 6 makes `steps[].sandbox_check.pid` nullable: it is the spawned worker
PID, or explicit null when no worker exists. It never substitutes the host PID.
Typed readers must accept null; stored integer-PID replies remain decodable.
The top-level legacy PID convention is unchanged. Request schema 1 and worker
ABI 6 remain separate.

Per-step `native_rc` is authoritative for native returns. A received diagnostic
without a native return retains `result_source="validator"`, `native_rc=null`
and compatibility `rc=-1`; this is not a synthetic validator record or a claimed
native failure. Missing replies use synthetic `rc=0`, `outcome="error"` with a
missing reason. `outcome="error"` alone does not identify a native call failure.

See [the query and receiver contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#query-and-receiver-evidence)
for immutable query planning, query association, independent pipe collection,
and exact-byte controller capture semantics.
