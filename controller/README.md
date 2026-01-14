# `controller/` (Rust controller: specimen-first CLI)

This is developer documentation for the Rust code in `controller/`. It builds the command-line controller that ships as:

- `PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is now **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to print a stable, machine-readable JSON witness for each run.

For the Swift runner implementation details, see `runner/README.md`.

## What lives in `controller/`

- `controller/src/main.rs` — CLI parsing and specimen evaluation orchestration
- `controller/src/json_contract.rs` — JSON key sorting helper (used by other bins)
- `controller/src/runner_manager.rs` — external runner registry + launchd wiring

Standalone helper tools (embedded into the `.app`):

- `controller/src/bin/sandbox-log-observer.rs` → `PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name

## CLI surface (contract)

The launcher intentionally exposes a minimal surface:

```text
policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--instrumentation <json|@path>]
policy-witness runner <command> [options]
```

### `run`

Runs a **single runner evaluation** against the selected runner service:

- Reads a request JSON file (runner request schema) that contains:
  - a sandbox policy (`sbpl` source or compiled bytes),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Starts a fresh runner instance, applies the policy exactly once, executes the probe plan, and returns the runner’s structured JSON result.
- Captures supporting evidence (best-effort) using `sandbox-log-observer` and attaches it to the output.
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
- `data.runner_provenance`: runner identity + entitlements metadata
- `data.app_provenance`: embedded app evidence metadata (and optional verification)

Optional:

- `PW_VERIFY_EVIDENCE=1` runs a manifest hash verification pass and includes a
  `data.app_provenance.evidence_verify` report in the output.

### Runner selection (external entitlements)

`run` can target an external runner by adding one of the following to the request:

- `runner: { id, service, required_entitlements }` (preferred)
- Legacy top-level fields: `runner_id`, `runner_service`, `required_entitlements`

If `required_entitlements` is present, the controller enforces a **superset**
check against the runner’s recorded entitlements before dispatch.

### `runner` (external runner manager)

These commands manage external runners signed with user entitlements:

```text
policy-witness runner install --bundle <path> [--service-name <name>] [--scope user|system]
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

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.
