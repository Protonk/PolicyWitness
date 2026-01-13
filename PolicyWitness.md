# PolicyWitness.app (User Guide)

PolicyWitness is a macOS tool to run seatbelt/App Sandbox experiments without hand‑waving about what happened.

PolicyWitness is **specimen-first**: you supply sandbox variation at runtime (SBPL or compiled profile bytes) plus a probe plan. Each specimen is executed by a fresh **ephemeral runner process** that starts unsandboxed, applies the requested policy **once**, runs the plan, returns a JSON witness, and exits.

This guide assumes you have only `PolicyWitness.app` and this file (`PolicyWitness.md`).

## Router (start here)

- Preflight (am I in a sandboxed harness?): `PolicyWitness.app/Contents/MacOS/policy-witness inside`
- Run one specimen (writes a run directory): `... policy-witness specimen <specimen.json>`
- Read results: open the run directory and start from `lab_summary.json`

## Quick start

Set a convenience variable:

```sh
PW="$PWD/PolicyWitness.app/Contents/MacOS/policy-witness"
```

Confirm you’re not running inside an OS sandboxed harness (this should print `false` in a normal Terminal):

```sh
$PW inside --bare
```

Create a specimen that denies reading `/etc/hosts`:

```sh
cat > /tmp/pw_specimen_file_read_deny.json <<'JSON'
{
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

Run it (this writes a run directory under `.pw_lab/out/...` by default):

```sh
$PW specimen /tmp/pw_specimen_file_read_deny.json --force
```

Open the run directory and read `lab_summary.json` first.

## Core model (what PolicyWitness is trying to prove)

### Two runs per specimen

Each `specimen` evaluation produces two runs:

- **canonical**: apply the policy exactly as provided
- **instrumented**: for SBPL, PolicyWitness adds a deterministic `(with message "...")` marker to each `(deny ...)` form so deny evidence can be correlated reliably

Treat the instrumented run as evidence-collection support. Interpret allow/deny semantics from the canonical run.

### A specimen is a list of steps

Each step contains:

- a **Channel D** prediction (`sandbox_check`), and
- a **Channel A** operation attempt (file op, mach lookup, etc.)

PolicyWitness treats “permission-shaped failure” as ambiguous unless it can attach supporting evidence.

### Evidence channels (A–D)

- **A**: in-band attempt result (return code + `errno`/Mach return, plus a normalized outcome)
- **B**: deterministic deny marker (instrumented run only; SBPL `message` marker on deny)
- **C**: unified-log deny evidence correlated by PID + window (captured outside the sandbox boundary)
- **D**: `sandbox_check` prediction (and a post-apply “am I sandboxed?” check)

## CLI (what you can run)

The shipped CLI surface is intentionally small:

```text
policy-witness inside [--service-name <mach-service-name> ...] [--bare]
policy-witness specimen <specimen.json> [--outdir <dir>] [--timeout-ms <n>] [--log-last <dur>] [--force]
```

### `inside` (preflight)

`inside` is a fail-closed “am I running inside a sandboxed automation harness?” probe.

- `--bare` prints `true`/`false`
- without `--bare`, it prints JSON describing which sensor triggered

If `inside` reports `true`, `specimen` will refuse to run (status `blocked`) because:

- XPC lookup can fail before the runner launches, and/or
- unified log access can be restricted (making deny evidence capture meaningless).

### `specimen` (run one specimen and write a labbook)

Usage:

```sh
$PW specimen <specimen.json> [--outdir <dir>] [--timeout-ms <n>] [--log-last <dur>] [--force]
```

Key flags:

- `--outdir <dir>`: where to write the run directory (default: `.pw_lab/out/<timestamp>_specimen_<specimen_id>`)
- `--force`: allows deleting/recreating an existing non-empty `--outdir`
- `--timeout-ms`: runner RPC timeout (default: `240000`)
- `--log-last`: unified log lookback window for deny capture (default: `10s`)

Exit codes:

- `0`: summary status `pass`
- `1`: summary status `fail`
- `3`: summary status `blocked` (inside harness sandbox)

## Specimen format (JSON)

A specimen file has these top-level keys:

```text
specimen_id: string
policy: { ... }
instrumented_policy: { ... }   (optional)
probe_plan: [ ... ]
```

### Policy (`policy` / `instrumented_policy`)

Two policy formats are supported:

- `format: "sbpl"`
  - `sbpl_source`: the SBPL source string
  - `params` (optional): map of parameter key/value strings

- `format: "compiled_bytes"`
  - `compiled_profile_b64`: base64 of compiled profile bytes
  - `params` (optional): map of parameter key/value strings

If `instrumented_policy` is omitted and `policy.format == "sbpl"`, PolicyWitness auto-generates an instrumented policy by adding a `(with message "PW_LAB_DENY_MARKER:<specimen_id>")` marker to each `(deny ...)` form.

If `policy.format != "sbpl"`, you must provide `instrumented_policy` explicitly.

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

## Labbook output (what `specimen` writes)

The run directory contains:

- `inside.json`: the preflight result captured for this run
- `specimen.json`: a copy of your input specimen
- `canonical.request.json` / `instrumented.request.json`: the exact requests sent to the runner
- `canonical/` and `instrumented/`:
  - `run.json`: runner client envelope (argv, timestamps, parsed runner JSON)
  - `outputs.stdout.json`: raw runner stdout (JSON)
  - `outputs.stderr.txt`: raw runner stderr
- `canonical_sandbox_logs.json` / `instrumented_sandbox_logs.json`: unified-log deny capture results (best-effort)
- `lab_summary.json`: the stable “overview” summary for the run

### Reading `lab_summary.json`

Key fields:

- `status`: `pass` / `fail` / `blocked`
- `inside.inside`: whether PolicyWitness detected a harness sandbox
- `uncertainty.confidence`: `high` only when deny evidence was observed and steps were recorded
- `uncertainty.reasons`: why confidence is not high (for example `sandbox_deny_not_observed`)
- `steps[]`: per-step outcomes derived from Channel A + D
  - `normalized_outcome` includes:
    - `ok`
    - `failed_predicted_deny`
    - `failed_predicted_allow`
    - `mismatch_allow_but_predicted_deny`

## Additional example: deny `mach-lookup`

This specimen denies all `mach-lookup` operations and then attempts to look up `com.apple.logd`:

```sh
cat > /tmp/pw_specimen_mach_deny.json <<'JSON'
{
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

$PW specimen /tmp/pw_specimen_mach_deny.json --force
```

## Troubleshooting

### `specimen` is `blocked` / exit code 3

Run `$PW inside` to see which sensor triggered. If `inside=true`, rerun PolicyWitness outside the harness sandbox.

### Log capture is unavailable

If `*_sandbox_logs.json` reports `capture_status: "requested_unavailable"`, unified-log evidence could not be collected from this environment. You can still use the runner’s `sandbox_check` predictions and operation results, but attribution confidence stays low.

### `sandbox_check` and the attempt disagree

- If the attempt failed but `sandbox_check` said `allow`, treat it as “not confirmed sandbox denial” and inspect the attempt error (`errno` / Mach return).
- If the attempt succeeded but `sandbox_check` said `deny`, treat it as a probe mismatch (wrong operation/filter, non-canonical path, or an operation that isn’t governed by the policy string you checked).

### `specimen` refuses to auto-instrument

If you use `policy.format: "compiled_bytes"`, you must provide `instrumented_policy` explicitly (PolicyWitness cannot safely edit compiled profile bytes).

## Safety notes

- PolicyWitness does not execute arbitrary paths; the runner only performs a small, explicit set of operations.
- SBPL / compiled-profile inputs can deny broad classes of behavior. Run PolicyWitness in a controlled environment and expect specimens to fail loudly.
- Treat missing deny evidence as uncertainty: if you did not capture deny evidence, do not claim “sandbox denied.”
