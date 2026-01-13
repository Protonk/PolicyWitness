# PolicyWitness.app (User Guide)

PolicyWitness is a macOS tool to run seatbelt/App Sandbox experiments without hand‑waving about what happened.

PolicyWitness is **specimen-first**: you supply sandbox variation at runtime (SBPL or compiled profile bytes) plus a probe plan. Each specimen is executed by a fresh **ephemeral runner process** that starts unsandboxed, applies the requested policy **once**, runs the plan, returns a JSON witness, and exits.

This guide assumes you have only `PolicyWitness.app` and this file (`PolicyWitness.md`).

## Router (start here)

- Run one request and print a JSON result: `... policy-witness run <request.json>`
- Save output for later inspection: `... policy-witness run <request.json> > result.json`

## Quick start

Set a convenience variable:

```sh
PW="$PWD/PolicyWitness.app/Contents/MacOS/policy-witness"
```

Create a request that denies reading `/etc/hosts`:

```sh
cat > /tmp/pw_specimen_file_read_deny.json <<'JSON'
{
  "schema_version": 1,
  "specimen_id": "file_read_deny",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default) (deny file-read-data)"
  },
  "probe_plan": [
    {
      "step_id": "fr1",
      "sandbox_check": {
        "operation": "file-read-data",
        "filter": { "kind": "path", "value": "/etc/hosts" }
      },
      "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
    }
  ]
}
JSON
```

Run it (prints JSON to stdout):

```sh
$PW run /tmp/pw_specimen_file_read_deny.json > /tmp/pw_result.json
```

Open `/tmp/pw_result.json` and start from `data.runner_result`.

## Core model (what PolicyWitness is trying to prove)

### One run per request

Each `run` invocation starts a fresh runner instance, applies the requested policy exactly once, executes the probe plan, and returns a structured JSON witness.

### A specimen is a list of steps

Each step contains:

- a **Channel D** prediction (`sandbox_check`), and
- a **Channel A** operation attempt (file op, mach lookup, etc.)

PolicyWitness treats “permission-shaped failure” as ambiguous unless it can attach supporting evidence.

### Evidence channels (A–D)

- **A**: in-band attempt result (return code + `errno`/Mach return, plus a normalized outcome)
- **B**: deterministic deny side-effect (SBPL `send-signal` if the policy uses it)
- **C**: unified-log deny evidence correlated by PID + window (captured outside the sandbox boundary)
- **D**: `sandbox_check` prediction (and a post-apply “am I sandboxed?” check)

## CLI (what you can run)

The shipped CLI surface is intentionally small:

```text
policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>]
```

### `run`

Usage:

```sh
$PW run <request.json> [--timeout-ms <n>] [--log-last <dur>]
```

Key flags:

- `--timeout-ms`: runner RPC timeout (default: `240000`)
- `--log-last`: unified log lookback window for deny capture (default: `10s`)

Exit codes:

- `0`: runner executed successfully (`result.ok=true`)
- `1`: runner execution failed (`result.ok=false`)

## Request format (JSON)

A request file has these top-level keys:

```text
schema_version: number
specimen_id: string
run_kind: string (optional)
policy: { ... }
probe_plan: [ ... ]
```

### Policy (`policy`)

Two policy formats are supported:

- `format: "sbpl"`
  - `sbpl_source`: the SBPL source string
  - `params` (optional): map of parameter key/value strings

- `format: "compiled_bytes"`
  - `compiled_profile_b64`: base64 of compiled profile bytes
  - `params` (optional): map of parameter key/value strings

### Steps (`probe_plan`)

Each step has:

- `step_id`: string
- `sandbox_check`: `{ operation, filter }`
- `attempt`: `{ kind, action, target }`

Supported `sandbox_check.filter.kind` values:

- `none`
- `path` (use `filter.value` as a path string)
- `global_name` (for `mach-lookup`, use `filter.value` as the Mach service name)

Supported attempts:

- `attempt.kind: "file"`
  - `action: "open_read" | "open_write" | "create" | "unlink"`
  - `target: <path>`

- `attempt.kind: "mach_lookup"`
  - `action: "bootstrap_look_up"`
  - `target: <mach-service-name>` (for example `com.apple.logd`)

**Path canonicalization note**

The runner canonicalizes file paths for the attempted operation (`realpath` when possible). For best results, use canonical paths in `sandbox_check.filter.value` too (avoid `/tmp` vs `/private/tmp` mismatches).

## Additional example: deny `mach-lookup`

This specimen denies all `mach-lookup` operations and then attempts to look up `com.apple.logd`:

```sh
cat > /tmp/pw_specimen_mach_deny.json <<'JSON'
{
  "schema_version": 1,
  "specimen_id": "mach_deny",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default) (deny mach-lookup)"
  },
  "probe_plan": [
    {
      "step_id": "ml1",
      "sandbox_check": {
        "operation": "mach-lookup",
        "filter": { "kind": "none" }
      },
      "attempt": { "kind": "mach_lookup", "action": "bootstrap_look_up", "target": "com.apple.logd" }
    }
  ]
}
JSON

$PW run /tmp/pw_specimen_mach_deny.json
```

## Troubleshooting

### Sandboxed automation environments

Some automation/agent harnesses run commands under a macOS sandbox. In that context, PolicyWitness runs can fail before any runner code executes (for example XPC lookup `NSCocoaErrorDomain=4099` / error `159` “Sandbox restriction”), and unified logging capture can be unavailable (`log: Cannot run while sandboxed`).

Treat these as environment constraints, not PolicyWitness regressions. If you see them, rerun the same command once from a normal Terminal context (or with escalation) before debugging PolicyWitness itself.

### Log capture is unavailable

If `data.sandbox_log_capture.capture_status` is `requested_unavailable`, unified-log evidence could not be collected from this environment. You can still use the runner’s `sandbox_check` predictions and operation results, but attribution confidence stays low.

### `sandbox_check` and the attempt disagree

- If the attempt failed but `sandbox_check` said `allow`, treat it as “not confirmed sandbox denial” and inspect the attempt error (`errno` / Mach return).
- If the attempt succeeded but `sandbox_check` said `deny`, treat it as a probe mismatch (wrong operation/filter, non-canonical path, or an operation that isn’t governed by the policy string you checked).

## Safety notes

- PolicyWitness does not execute arbitrary paths; the runner only performs a small, explicit set of operations.
- SBPL / compiled-profile inputs can deny broad classes of behavior. Run PolicyWitness in a controlled environment and expect specimens to fail loudly.
- Treat missing deny evidence as uncertainty: if you did not capture deny evidence, do not claim “sandbox denied.”
