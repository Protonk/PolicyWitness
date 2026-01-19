# `controller/` (Rust controller: specimen-first CLI)

This is developer documentation for the Rust code in `controller/`. It builds the command-line controller that ships as:

- `PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to print a stable, machine-readable JSON witness for each run.

For the Swift runner implementation details, see `runner/README.md`.

## What lives in `controller/`

Core controller modules:

- `controller/src/main.rs` — entry point and module wiring
- `controller/src/cli.rs` — CLI usage text + top-level dispatch
- `controller/src/run_flow.rs` — run orchestration and JSON envelope assembly
- `controller/src/runner_select.rs` — runner selection + provenance
- `controller/src/runner_client.rs` — wrapper around `pw-runner-client`
- `controller/src/sandbox_log.rs` — unified-log capture mapping for sandbox denials
- `controller/src/sonoma_cross_check.rs` — `sb_api_validator` cross-check flow
- `controller/src/runner_commands.rs` — external runner install/list/verify/remove/refresh

Support modules:

- `controller/src/app_layout.rs` — app bundle layout + embedded tool resolution
- `controller/src/plist.rs` — PlistBuddy helpers for Info.plist lookups
- `controller/src/bundle.rs` — bundle metadata reader for external runners
- `controller/src/request_patch.rs` — request JSON injection helpers
- `controller/src/utils.rs` — shared time + output helpers
- `controller/src/evidence.rs` — evidence manifest parsing + verification
- `controller/src/json_contract.rs` — JSON envelope rendering with sorted keys
- `controller/src/runner_manager.rs` — external runner registry + launchd wiring

Standalone helper tools (embedded into the `.app`):

- `controller/src/bin/sandbox-log-observer.rs` → `PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name
- `controller/tools/sb_api_validator/sb_api_validator` → `PolicyWitness.app/Contents/MacOS/sb_api_validator`
  - Direct `sandbox_check` cross-check helper (used by `--sonoma-cross-check`)

## CLI surface (contract)

The launcher intentionally exposes a minimal surface:

```text
policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--runner-mode <debuggable|byoxpc|machme>] [--instrumentation <json|@path>] [--sonoma-cross-check]
policy-witness runner <command> [options]
```

### `run`

Runs a **single runner evaluation** against the selected runner service:

- Reads a request JSON file (runner request schema) that contains:
  - a sandbox policy (`sbpl` source),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Starts a fresh runner instance, applies the policy exactly once, executes the probe plan, and returns the runner’s structured JSON result.
- Captures supporting evidence (best-effort) using `sandbox-log-observer` and attaches it to the output.
- If `--sonoma-cross-check` is provided, the controller runs the embedded
  `sb_api_validator` against the runner PID while it is paused post-sandbox
  (a post-sandbox `debug_wait` port is injected to hold the runner open).
- Prints a single JSON envelope to stdout (no output directories; stdout is the artifact).
- Emits `data.runner_provenance` and `data.app_provenance` to keep results auditable.
- If `--instrumentation` is provided, the controller injects the instrumentation object into the request JSON (without modifying the original file).

Exit codes:

- `0`: `result.ok=true`
- `1`: `result.ok=false`
- `2`: usage / tool error (prints a JSON error envelope)

### Output contract

The controller prints one JSON envelope to stdout (`kind="run"`). It contains:

- `data.runner_result`: the runner's JSON (if parseable)
- `data.runner_client`: argv + stdout/stderr + timing for the client call
- `data.sandbox_log_capture`: optional unified-log evidence (best-effort)
- `data.sonoma_cross_check`: optional `sandbox_check` cross-check report (best-effort)
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

If `runner.mode` is present, it must match the registry kind (byoxpc or machme).

### `runner` (external runner manager)

These commands manage external runners signed with user entitlements:

```text
policy-witness runner install --bundle <path> [--kind byoxpc|machme] [--service-name <name>] [--scope user|system]
                             [--identity <codesign-id>] [--entitlements <plist>]
                             [--executable <path>] [--bundle-id <id>] [--allow-adhoc]
                             [--env KEY=VALUE]
                             [--skip-bootstrap]
policy-witness runner list
policy-witness runner status --id <runner-id> | --service-name <name>
policy-witness runner verify --id <runner-id> | --service-name <name> [--timeout-ms <n>]
policy-witness runner remove --id <runner-id> | --service-name <name> [--skip-bootout]
policy-witness runner refresh
```

Install writes a launchd plist, bootstraps the service, and records runner
metadata (entitlements + signature) in the local registry. The registry lives
under `~/Library/Application Support/PolicyWitness/runners.json`.

Notes:
- BYOXPC runners require `CFBundlePackageType=XPC!` and use `CFBundleIdentifier` as the service name.
- MachMe runners accept `--service-name` overrides and use Mach services for NSXPC.

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.
