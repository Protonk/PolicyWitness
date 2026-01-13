# `controller/` (Rust controller: specimen-first CLI)

This is developer documentation for the Rust code in `controller/`. It builds the command-line controller that ships as:

- `PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is now **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to print a stable, machine-readable JSON witness for each run.

For the Swift runner implementation details, see `runner/README.md`.

## What lives in `controller/`

- `controller/src/main.rs` — CLI parsing and specimen evaluation orchestration
- `controller/src/main.rs` — CLI parsing and run orchestration
- `controller/src/json_contract.rs` — JSON key sorting helper (used by other bins)

Standalone helper tools (embedded into the `.app`):

- `controller/src/bin/sandbox-log-observer.rs` → `PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name

## CLI surface (contract)

The launcher intentionally exposes a minimal surface:

```text
policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>]
```

### `run`

Runs a **single runner evaluation** against the embedded `PWRunner.xpc` runner:

- Reads a request JSON file (runner request schema) that contains:
  - a sandbox policy (`sbpl` source or compiled bytes),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Starts a fresh runner instance, applies the policy exactly once, executes the probe plan, and returns the runner’s structured JSON result.
- Captures supporting evidence (best-effort) using `sandbox-log-observer` and attaches it to the output.
- Prints a single JSON envelope to stdout (no output directories; stdout is the artifact).

Exit codes:

- `0`: `result.ok=true`
- `1`: `result.ok=false`
- `2`: usage / tool error (prints a JSON error envelope)

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.
