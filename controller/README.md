# `controller/` (Rust controller: specimen-first CLI)

This is developer documentation for the Rust code in `controller/`. It builds the command-line controller that ships as:

- `dist/PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to print a stable, machine-readable JSON witness for each run. The runner is itself a host/worker pair: the XPC host stays unsandboxed and the worker process applies the specimen policy. The controller treats this as an implementation detail of the runner — it only consumes the host's reply.

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
- `controller/src/policy_preflight.rs` — SBPL preflight runner wiring
- `controller/src/utils.rs` — shared time + output helpers
- `controller/src/evidence.rs` — evidence manifest parsing + verification
- `controller/src/json_contract.rs` — JSON envelope rendering with sorted keys
- `controller/src/runner_manager.rs` — external runner registry + launchd wiring

Standalone helper tools (embedded into the `.app`):

- `controller/src/bin/sandbox-log-observer.rs` → `dist/PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name
- `controller/src/bin/sbpl-preflight.rs` → `dist/PolicyWitness.app/Contents/MacOS/sbpl-preflight`
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
policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--runner-mode <standard|byoxpc>]
policy-witness runner <command> [options]
```

### `run`

Runs a **single runner evaluation** against the selected runner service:

- Reads a request JSON file (runner request schema) that contains:
  - a sandbox policy (`sbpl` source),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Starts a fresh runner instance (one XPC host + one worker process), applies the policy exactly once inside the worker, executes the probe plan, and returns the runner's structured JSON result.
- Captures supporting evidence (best-effort) using `sandbox-log-observer` and attaches it to the output.
- The embedded `sb_api_validator` runs in `--batch` NDJSON mode (one
  process per run) co-launched by the C-worker code path inside the
  runner host. The validator reads NDJSON probes from stdin and writes
  NDJSON verdicts to stdout; the host joins the verdicts into
  `runner_result.steps[*].validator` and surfaces process metadata as
  `runner_result.validator_subprocess`. See
  `tests/suites/validator_batch_mode/README.md` for the wire contract.
  Validator coverage rules:
  - **Predicted** filter kinds (the validator calls `sandbox_check`):
    `path`, `global_name`, `local_name`, `none`. `none`-filter probes
    call `sandbox_check(pid, op, 0)` with no filter argument and emit
    `filter_value: null` / `filter_type_id: 0` in the verdict.
  - **Skipped — prediction unavailable** (verified-unreliable op+filter
    pairs the runner accepts but deliberately does not predict for; see
    `PolicyWitness.md` "Filter kinds where prediction is unavailable"):
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

The controller prints one JSON envelope to stdout (`kind="run"`). It contains:

- `data.runner_result`: the runner's JSON (if parseable)
- `data.runner_client`: argv + stdout/stderr + timing for the client call
- `data.policy_preflight`: SBPL compile report from `sbpl-preflight` (best-effort)
- `data.runner_startup_diagnostics`: extra context when XPC startup fails
  (rare after the host/worker split, since the unsandboxed host always
  replies unless launchd or codesign reject the bundle outright)
- `data.runner_sandbox_diagnostics`: present when
  `normalized_outcome == "runner_sandbox_denied"`. Carries
  `first_deny: { operation, path, raw_line }` — the first unified-log
  kernel deny attributed to the worker PID — or `first_deny: null` when
  log capture was blocked/unavailable or no event matched. PID-filtered;
  no process-name fallback (avoids over-attribution to concurrent
  runners). Consumers can branch on `first_deny != null` directly.
- `data.sandbox_log_capture`: optional unified-log evidence (best-effort)
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
- `runner verify` defaults to a 5-second timeout (override with `--timeout-ms`).
- `runner remove` always persists the registry change. `launchctl bootout` or plist-removal failures are surfaced in the envelope's `data.warnings` rather than aborting the call, so dirty launchd state cannot strand a registry entry.
- `runner status`, `runner verify`, and `runner remove` emit an envelope with the operation's `kind` and `result.normalized_outcome = "not_found"` (exit code 2) when the lookup key is not in the registry, instead of plain-text stderr.
- `runner validate` re-reads each registry entry's on-disk signature and entitlements. It does not reconcile against launchctl or `LaunchAgents/`.

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `dist/PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.
