# `runner/` (Rust launcher: specimen-first CLI)

This is developer documentation for the Rust code in `runner/`. It builds the command-line launcher that ships as:

- `PolicyWitness.app/Contents/MacOS/policy-witness`

PolicyWitness is now **specimen-first**. The launcher’s job is to drive the embedded runner service (`PWRunner.xpc`) and to produce stable, evidence-oriented artifacts for each run.

For the XPC runner implementation details, see `xpc/README.md`.

## What lives in `runner/`

- `runner/src/main.rs` — CLI parsing and specimen evaluation orchestration
- `runner/src/json_contract.rs` — JSON key sorting helper (used by other bins)

Standalone helper tools (embedded into the `.app`):

- `runner/src/bin/sandbox-log-observer.rs` → `PolicyWitness.app/Contents/MacOS/sandbox-log-observer`
  - Captures unified-log sandbox deny lines by PID + process name
- `runner/src/bin/signpost-log-observer.rs` → `PolicyWitness.app/Contents/MacOS/signpost-log-observer`
  - Captures signpost spans from unified logging (supporting evidence channel)

## CLI surface (contract)

The launcher intentionally exposes a minimal surface:

```text
policy-witness inside [--service-name <mach-service-name> ...] [--bare]
policy-witness specimen <specimen.json> [--outdir <dir>] [--timeout-ms <n>] [--log-last <dur>] [--force]
```

### `inside`

Fail-closed preflight for “am I running inside a sandboxed harness that will invalidate XPC lookup and/or evidence capture?”

- If `--bare` is set, prints `true`/`false`.
- Otherwise prints a JSON object with `inside`, `trigger`, and a `checked` sensor list.

This is primarily used by agents and CI harnesses.

### `specimen`

Runs a **single specimen evaluation** against the embedded `PWRunner.xpc` runner:

- Reads a specimen JSON file that contains:
  - a sandbox policy (`sbpl` source or compiled bytes),
  - and a probe plan (steps with `sandbox_check` + an attempted operation).
- Executes two runs:
  - **canonical**: applies the policy as provided
  - **instrumented**: for SBPL policies, automatically injects a `message` marker into each `(deny …)` form so denies can be correlated deterministically in unified logs
- Captures supporting evidence (best-effort) using `sandbox-log-observer`.
- Writes a labbook-style output directory (`lab_summary.json` + raw artifacts) and prints the summary JSON to stdout.

Exit codes:

- `0`: run completed (`lab_summary.status=pass`)
- `1`: run failed (`lab_summary.status=fail`)
- `3`: blocked (`inside=true`)

## Why the Rust launcher still shells out

The launcher does not speak NSXPC directly. It drives the Swift client helper embedded in the app bundle:

- `PolicyWitness.app/Contents/MacOS/pw-runner-client`

The Swift client is responsible for `NSXPCConnection` wiring; the Rust launcher owns run orchestration and evidence capture.

