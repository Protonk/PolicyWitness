# PolicyWitness User Guide

PolicyWitness runs sandbox specimens and prints a single JSON result to stdout.
This guide covers usage only.

## Choose your runner

You have two ways to run a specimen:

1) Plain runner (built-in)
- Use this when you only need SBPL (source or compiled bytes) and do NOT need
  extra entitlements beyond what ships in the app.
- This is the default path: no extra setup.

2) External runner (BYOSig)
- Use this when your probes or environment require entitlements that the
  built-in runner does not have.
- You sign a runner yourself and register it as a launchd service.
- The specimen selects that runner by id or service name.

## Quick start (plain runner)

Set a convenience variable:

```sh
PW="$PWD/PolicyWitness.app/Contents/MacOS/policy-witness"
```

Create a specimen:

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

Run it:

```sh
$PW run /tmp/pw_specimen_file_read_deny.json > /tmp/pw_result.json
```

## Specimen format (request JSON)

Top-level fields:

- `schema_version`: number
- `specimen_id`: string
- `run_kind`: string (optional)
- `policy`: object
- `probe_plan`: array of steps
- `runner`: object (optional, for external runners)
- `instrumentation`: object (optional, instrumentation port)

### Policy

SBPL source:

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1) (allow default) (deny file-read-data)",
  "params": { "DENY_DIR": "/tmp/deny" }
}
```

Compiled bytes:

```json
"policy": {
  "format": "compiled_bytes",
  "compiled_profile_b64": "BASE64_BYTES_HERE"
}
```

### Probe plan steps

Each step has:

- `step_id`
- `sandbox_check`: `{ operation, filter }`
- `attempt`: `{ kind, action, target }`

Example:

```json
{
  "step_id": "read_etc_hosts",
  "sandbox_check": {
    "operation": "file-read-data",
    "filter": { "kind": "path", "value": "/etc/hosts" }
  },
  "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
}
```

## Instrumentation (opt-in)

Instrumentation ports provide a user-friendly way to exercise the runner’s
entitlement-backed capabilities. This field is optional; if omitted, behavior
is unchanged. Results are reported under `instrumentation` in the run JSON and
do not change the run outcome.
Each port can specify an optional `phase`:

- `pre_sandbox` (default)
- `post_sandbox`

Example specimen fragment:

```json
"instrumentation": {
  "version": 1,
  "ports": [
    { "kind": "debug_wait", "sleep_ms": 5000 },
    { "kind": "dylib_load", "path": "/path/to/lib.dylib", "symbol": "pw_instrumentation_init" },
    { "kind": "execmem_probe", "size_bytes": 4096 },
    { "kind": "dyld_env", "keys": ["DYLD_INSERT_LIBRARIES"] }
  ]
}
```

Notes:
- `dylib_load` expects an optional no-arg symbol (C `void func(void)`).

Ports (v1):
- `dylib_load`: load a dylib and optionally call a symbol (uses `com.apple.security.cs.disable-library-validation`).
- `debug_wait`: sleep before sandbox apply for debugger attach (uses `com.apple.security.get-task-allow`).
- `execmem_probe`: attempt an RWX `mmap` and report success/failure (uses `com.apple.security.cs.allow-unsigned-executable-memory`).
- `dyld_env`: report expected `DYLD_*` env vars (uses `com.apple.security.cs.allow-dyld-environment-variables`).

Convenience flag (injects instrumentation into the request JSON at runtime):

```sh
$PW run /path/to/request.json --instrumentation @/path/to/instrumentation.json
```

Example specimen (full, minimal):

```json
{
  "schema_version": 1,
  "specimen_id": "instrumentation_debug_wait",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default)"
  },
  "instrumentation": {
    "version": 1,
    "ports": [
      { "kind": "debug_wait", "sleep_ms": 1 }
    ]
  },
  "probe_plan": []
}
```

Explanation: this pauses briefly before sandbox apply; the run JSON includes an
`instrumentation` report with the port status and `sleep_ms`, and the overall
run outcome remains `ok`.

Guide (quick start):

1. Pick a port and add it to your specimen or create a small `instrumentation.json`.
2. Run with `policy-witness run <request.json> --instrumentation @instrumentation.json`.
3. Inspect `data.runner_result.instrumentation` in the output JSON for per-port status.

Note: `dyld_env` is a check only. To actually set `DYLD_*` variables, use an
external runner and set launchd `EnvironmentVariables` at install time:

```sh
$PW runner install --bundle /path/to/PWRunner.xpc --env DYLD_INSERT_LIBRARIES=/path/to/lib.dylib
```

## External runner (BYOSig) flow

Use this when you need entitlements that are not in the built-in runner.

### What you need

- A runner bundle or binary to sign (typically a copy of `PWRunner.xpc`).
- A signing identity (Developer ID Application) or ad-hoc signing for local use.
- An entitlements plist.

### Install an external runner

```sh
$PW runner install \
  --bundle /path/to/PWRunner.xpc \
  --identity "Developer ID Application: Your Name (TEAMID)" \
  --entitlements /path/to/entitlements.plist \
  --scope user
```

Notes:
- Use `--allow-adhoc` for local ad-hoc signing.
- Use `--scope system` if you want a system-wide service (requires admin).
- Use `--skip-bootstrap` if you will run `launchctl` manually.
- Use `--env KEY=VALUE` to set launchd `EnvironmentVariables` (for `DYLD_*`).

The install command writes a launchd plist, bootstraps the service, and records
the runner in the local registry.

### Verify the runner

```sh
$PW runner verify --service-name com.policywitness.runner.<id>
```

### Use the runner in a specimen

Preferred: include a `runner` object:

```json
"runner": {
  "id": "runner-<id-from-install>",
  "required_entitlements": [
    "com.apple.security.cs.disable-library-validation"
  ]
}
```

Alternative: select by service name:

```json
"runner": {
  "service": "com.policywitness.runner.<id>"
}
```

`required_entitlements` enforces a superset check before dispatch.

### List or remove runners

```sh
$PW runner list
$PW runner remove --id runner-<id>
```

Registry location:

```
~/Library/Application Support/PolicyWitness/runners.json
```

## Common flags

- `--timeout-ms <n>`: runner RPC timeout (default 240000)
- `--log-last <dur>`: unified log lookback window for deny capture (default 10s)
- `--instrumentation <json|@path>`: inject instrumentation ports into the request

## Troubleshooting

- Service not found: run `policy-witness runner list` and confirm the service name.
- System scope install fails: use `--scope user` or run with admin privileges.
- Verify fails with no reply: check launchd state and the service plist.
- If you are running inside a sandboxed automation harness, XPC lookup can be blocked;
  run from a normal Terminal to confirm behavior.
