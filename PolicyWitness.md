# PolicyWitness User Guide

PolicyWitness runs sandbox specimens and prints a single JSON result to stdout.
This guide covers usage only.

## Choose your runner

PolicyWitness supports four runner modes:

1) Standard runner (built-in)
- Default path; minimal entitlements (no debug allowances).
- Select with `runner.mode="standard"` or `--runner-mode standard`.

2) Debuggable runner (built-in)
- Debug-friendly entitlements plus instrumentation ports.
- Select with `runner.mode="debuggable"` or `--runner-mode debuggable`.
- Tested by `tests/suites/runner_debuggable/run.sh`.

3) BYOXPC runner (external XPC bundle)
- Use when you need extra entitlements; supply a signed `.xpc` bundle.
- Service name must match the bundle’s `CFBundleIdentifier` (no override).
- Install with `policy-witness runner install --kind byoxpc ...`.
- Tested by `tests/suites/runner_byoxpc/run.sh` (opt-in; GUI session required).

4) MachMe runner (external Mach service binary)
- Use when you want to launch a raw binary as a Mach service.
- Install with `policy-witness runner install --kind machme --bundle /path/to/PWRunner`.
- Tested by `tests/suites/runner_machme/run.sh` (opt-in; GUI session required).

If no runner is specified, PolicyWitness uses the built-in standard runner.

## Quick start (standard runner)

Set a convenience variable:

```sh
PW="$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness"
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
- `runner`: object (optional; select runner mode and external runners)
- `instrumentation`: object (optional, instrumentation port)

Minimal skeleton (copy/paste):

```json
{
  "schema_version": 1,
  "specimen_id": "skeleton",
  "runner": { "mode": "standard" },
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": []
}
```
Notes:
- All path rules live inside `policy.sbpl_source`; there is no `path_membership` field.
- `instrumentation` (if any) sits next to `policy`, not inside it.
- `probe_plan` can be empty when you only want instrumentation.

### Policy

SBPL source:

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1) (allow default) (deny file-read-data)",
  "params": { "DENY_DIR": "/tmp/deny" }
}
```

`(import "...")` statements compile transparently — `sandbox_compile_string`
resolves them against the system profile search path. `(param "NAME")`
substitution uses values from `policy.params`. `string-append` of param
references is supported by the compiler.

#### Policy preflight diagnostics

Before the runner is invoked, the host compiles the policy with
`sbpl-preflight`. The preflight envelope exposes:

- `params_referenced`: names found in `(param "...")` forms in the source
  (string literals and `;` line comments are skipped).
- `params_supplied`: keys from `policy.params`.
- `params_missing`: referenced but not supplied. If non-empty, preflight
  returns `result.normalized_outcome = "missing_params"` and exits 1 with a
  clean `result.error` listing the names — instead of the cryptic libsandbox
  message ("expected pattern, got boolean") that surfaces when an unbound
  `(param ...)` is folded into a path filter. The libsandbox message is
  still preserved under `data.compile_error` for auditability.
- `params_unused`: supplied but never referenced. Recorded as info only;
  does not fail the preflight.

`policy.sbpl_source` is capped at 4 MiB. Oversized inputs are rejected with
`result.normalized_outcome = "policy_too_large"` and exit code 1; nothing is
sent to libsandbox and no imports are resolved. The cap is in place to bound
preflight work — far above any real-world hand-written profile.

The preflight envelope also records the imports closure:

- `imports`: each entry is `{name, resolved_path, sha256, size_bytes,
  mtime_unix, error}`. The resolver walks `(import "...")` statements
  recursively (depth cap 8, count cap 64), trying
  `/System/Library/Sandbox/Profiles/<name>` first and then
  `/usr/share/sandbox/<name>`. Names must include the `.sb` extension —
  libsandbox does not auto-append. Absolute paths starting with `/` are
  accepted as-is.
- `imports_truncated`: true when either the count cap (64 imports) or the
  depth cap (8 levels) was hit during resolution. Records still include the
  partial result up to the cap.
- `imports_cycle`: when a back-edge to an in-progress import is detected
  during resolution, the chain of import names that closed the cycle —
  `[outer, ..., inner, repeated_name]`. Null when no cycle is present. The
  field is single-valued: only the first cycle observed in a given walk is
  reported. (Diamond imports — the same file reached via two distinct paths
  with no cycle — are deduplicated silently and do not populate this field.)
- `policy_sha256`: sha256 of `policy.sbpl_source` only.
- `policy_closure_sha256`: sha256 of the source plus the sorted
  `resolved_path + " " + sha256` of every successfully resolved import.
  This hash is reproducible iff every resolved file is content-identical
  on the verifying host. Unresolved imports are excluded — check
  `imports[].error` to see which ones failed.
- `macos_build_version`: `sw_vers -buildVersion` for the host that ran the
  preflight. Import contents change between OS builds; this lets a
  downstream auditor decide whether a closure hash is verifiable on their
  machine.

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

## Run output (per step)

The runner echoes step results with additional context:

- `steps[].sandbox_check`: `{ rc, outcome, pid, operation, scope, filter_kind, filter_value, effective_filter_value, filter_type_id, errno, error, path_diagnostics? }`
- `steps[].attempt`: `{ rc, exit_code, errno, syscall_errno, outcome, error, requested_path, normalized_path, observed_path }`

Notes:
- `scope` is `post_sandbox` for runner-hosted checks.
- `requested_path`, `normalized_path`, and `observed_path` are present for file
  attempts; non-file attempts carry explicit `null` for these fields.
- `filter_value` is the exact string the runner passes to `sandbox_check`.
- `effective_filter_value` is a canonicalized/realpath form used for reporting only.
- `filter_type_id`: `1` (path), `16` (mach-lookup global), `17` (mach-lookup local).
- `path_diagnostics` is emitted only for path-filter checks. Introduced in
  runner response `schema_version = 2`; consumers branching on
  `schema_version` can rely on its presence on any path-filter check at v2+.
  It carries the candidate kernel-side forms of the check path so a caller
  can see which prefix libsandbox could have been comparing against when a
  `(subpath ...)` rule denies a path that looked like it should match.
  Fields: `{ input, realpath_resolved, firmlink_resolved, data_volume_form }`.
  The runner still passes the raw `filter_value` to `sandbox_check` — this
  block is observation only.
  - `realpath_resolved`: `realpath(3)` of `input`, or null on failure.
  - `firmlink_resolved`: the realpath result rewritten through
    `/usr/share/firmlinks`. On a stock macOS install `/etc/hosts` lands at
    `/System/Volumes/Data/private/etc/hosts`.
  - `data_volume_form`: heuristic shortcut that prepends
    `/System/Volumes/Data` to paths under `/private/`. Useful when
    `firmlinkResolved` returns nil on a host where `/usr/share/firmlinks` is
    absent.

Capture the sandbox_check argument quickly (no interpose needed):

```sh
jq '.data.runner_result.steps[].sandbox_check | {filter_value, effective_filter_value, filter_type_id, outcome, path_diagnostics}' run.json
```

## Instrumentation (opt-in)

Instrumentation ports provide a user-friendly way to exercise the runner’s
entitlement-backed capabilities. This field is optional; if omitted, behavior
is unchanged. Results are reported under `instrumentation` in the run JSON and
do not change the run outcome.
These ports are part of the debuggable runner mode; use `runner.mode="debuggable"`
(or `--runner-mode debuggable`) or an external runner signed with matching entitlements.
Each port can specify an optional `phase`:

- `pre_sandbox` (default)
- `post_sandbox`

Debug flow (quick recipe):
- Add a short `debug_wait` to give LLDB a window before sandbox apply.
- Add `dylib_load` with your logging shim to capture sandbox_check strings.
- Keep `runner.mode="debuggable"` (or use an external runner with matching entitlements) so these ports are enabled.
- Run: `policy-witness run <request.json> --instrumentation @instrumentation.json` and attach to the runner PID shown in logs.

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
- `execmem_probe`: attempt a JIT mapping (`MAP_JIT`, `PROT_READ|PROT_WRITE`) and report success/failure (requires `com.apple.security.cs.allow-jit`; falls back to legacy RWX if available).
- `dyld_env`: report expected `DYLD_*` env vars (observation only; for actual `DYLD_*` injection use an external runner installed with `--env DYLD_*`).

Convenience flag (injects instrumentation into the request JSON at runtime):

```sh
$PW run /path/to/request.json --instrumentation @/path/to/instrumentation.json
```

Example specimen (full, minimal):

```json
{
  "schema_version": 1,
  "specimen_id": "instrumentation_debug_wait",
  "runner": {
    "mode": "debuggable"
  },
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
$PW runner install --kind byoxpc --bundle /path/to/PWRunnerDebug.xpc --env DYLD_INSERT_LIBRARIES=/path/to/lib.dylib
```

## External runners (BYOXPC + MachMe)

Use these when you need entitlements that are not in the built-in runner.

### What you need

- BYOXPC: a runner `.xpc` bundle to sign (typically a copy of `PWRunner.xpc` or `PWRunnerDebug.xpc`).
- MachMe: a runner binary to sign (typically `PWRunner.xpc/Contents/MacOS/PWRunner` or the debug variant).
- A signing identity (Developer ID Application) or ad-hoc signing for local use.
- An entitlements plist.
- A logged-in GUI session (launchd bootstrap is not available from non-GUI shells).

### Tested install paths (copy/paste)

These sequences match the test suites and are the recommended starting point.

BYOXPC (user scope):

```sh
PW="$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness"
IDENTITY="Developer ID Application: Your Name (TEAMID)"
ENT="$PWD/runner/services/PWRunnerDebug/Entitlements.plist"
BYO="$PWD/runtime/byosig/instances/PWRunner.byoxpc.xpc"

mkdir -p "$(dirname "$BYO")"
rm -rf "$BYO"
cp -R dist/PolicyWitness.app/Contents/XPCServices/PWRunnerDebug.xpc "$BYO"

$PW runner install --kind byoxpc \
  --bundle "$BYO" \
  --identity "$IDENTITY" \
  --entitlements "$ENT" \
  --allow-adhoc \
  --scope user

$PW runner verify --service-name com.yourteam.policy-witness.PWRunnerDebug --timeout-ms 2000
```

MachMe (user scope):

```sh
PW="$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness"
IDENTITY="Developer ID Application: Your Name (TEAMID)"
ENT="$PWD/runner/services/PWRunnerDebug/Entitlements.plist"
BIN="$PWD/dist/PolicyWitness.app/Contents/XPCServices/PWRunnerDebug.xpc/Contents/MacOS/PWRunnerDebug"

$PW runner install --kind machme \
  --bundle "$BIN" \
  --identity "$IDENTITY" \
  --entitlements "$ENT" \
  --allow-adhoc \
  --service-name com.policywitness.runner.machme \
  --scope user

$PW runner verify --service-name com.policywitness.runner.machme --timeout-ms 2000
```

### Install a BYOXPC runner

```sh
$PW runner install \
  --kind byoxpc \
  --bundle /path/to/PWRunnerDebug.xpc \
  --identity "Developer ID Application: Your Name (TEAMID)" \
  --entitlements /path/to/entitlements.plist \
  --scope user
```

Notes:
- Use `--allow-adhoc` for local ad-hoc signing.
- Use `--scope system` if you want a system-wide service (requires admin).
- Use `--skip-bootstrap` if you will run `launchctl` manually.
- Use `--env KEY=VALUE` to set launchd `EnvironmentVariables` (for `DYLD_*`).
- BYOXPC service name must match the bundle’s `CFBundleIdentifier` (no override).
- The bundle must be a valid XPC service (`CFBundlePackageType=XPC!`).
- `--entitlements` requires either `--identity <id>` or `--allow-adhoc` so the
  supplied entitlements are actually re-embedded into the binary. Passing
  `--entitlements` without one of those is rejected — the registry would
  otherwise record entitlements that the kernel will not enforce.

The install command writes a launchd plist, bootstraps the service, and records
the runner in the local registry. The registry's `entitlements` field always
reflects what's embedded in the binary (read back via `codesign -d --entitlements`),
not what was supplied on the command line.

### Install a MachMe runner

```sh
$PW runner install \
  --kind machme \
  --bundle /path/to/PWRunner \
  --identity "Developer ID Application: Your Name (TEAMID)" \
  --entitlements /path/to/entitlements.plist \
  --scope user
```

Notes:
- Use `--service-name` to override the Mach service name (optional).
- Use `--bundle-id` to set an optional provenance identifier.
- If `--bundle` is a directory whose `Info.plist` declares `CFBundleExecutable`,
  `--executable` is optional — the binary is derived from
  `<bundle>/Contents/MacOS/<CFBundleExecutable>`. Pass `--executable` explicitly
  to override, or when the bundle has no readable Info.plist.
- The same `--entitlements` rule as BYOXPC applies: pair it with `--identity`
  or `--allow-adhoc`.

### Verify the runner

```sh
$PW runner verify --service-name <service-name>
```

`runner verify` defaults to a 5-second timeout; pass `--timeout-ms <n>` for
slow cold-spawn cases.

### Use the runner in a specimen

Preferred: include a `runner` object:

```json
"runner": {
  "id": "runner-<id-from-install>",
  "mode": "byoxpc",
  "required_entitlements": [
    "com.apple.security.cs.disable-library-validation"
  ]
}
```

Alternative: select by service name:

```json
"runner": {
  "service": "com.policywitness.runner.<id>",
  "mode": "machme"
}
```

`runner.mode` is optional; when present it must match the registry kind for external runners.
Valid modes: `standard`, `debuggable`, `byoxpc`, `machme`.
`required_entitlements` enforces a superset check before dispatch.

Quick smoke request (save as `/tmp/pw_byoxpc_smoke.json`):

```json
{
  "policy": { "sbpl": "(version 1) (deny default)" },
  "probe_plan": [],
  "runner": {
    "service": "com.yourteam.policy-witness.PWRunner",
    "mode": "byoxpc"
  }
}
```

Replace `service` and `mode` for MachMe runners.

Then run:

```sh
$PW run /tmp/pw_byoxpc_smoke.json --timeout-ms 20000
```

### List, validate, or remove runners

```sh
$PW runner list
$PW runner validate
$PW runner remove --id runner-<id>
```

External runners install a launchd background item. `runner remove` is the
preferred uninstall path and removes the launchd entry and registry record.
It is also self-healing: if `launchctl bootout` fails (e.g. the service was
already booted out) or the plist file is already gone, the registry entry is
still removed and the failure is surfaced in the envelope's `data.warnings`
array. This means `remove` is safe to call defensively before a fresh
`install`.

`runner validate` re-reads each registry entry's on-disk signature and
entitlements (registry-internal only — it does not reconcile against launchctl
or `LaunchAgents/`).

`runner status`, `runner verify`, and `runner remove` emit an envelope with
`result.normalized_outcome = "not_found"` and exit code 2 when the lookup key
isn't present in the registry; the envelope `kind` still matches the operation
so consumers can dispatch by `kind` and then branch on `normalized_outcome`.

If you no longer have the registry entry, uninstall manually:

User scope:

```sh
launchctl bootout "gui/$(id -u)/<service-name>"
rm -f "$HOME/Library/LaunchAgents/<service-name>.plist"
```

System scope:

```sh
sudo launchctl bootout "system/<service-name>"
sudo rm -f "/Library/LaunchDaemons/<service-name>.plist"
```

Registry location:

```
~/Library/Application Support/PolicyWitness/runners.json
```

## Common flags

- `--timeout-ms <n>`: runner RPC timeout (default 240000)
- `--log-last <dur>`: unified log lookback window for deny capture (default 10s)
- `--runner-mode <standard|debuggable|byoxpc|machme>`: inject `runner.mode` into the request
- `--instrumentation <json|@path>`: inject instrumentation ports into the request
- `--sonoma-cross-check`: run an sb_api_validator cross-check against the runner PID
  while it is paused post-sandbox; results are attached under `data.sonoma_cross_check`

## Troubleshooting

- Service not found: run `policy-witness runner list` and confirm the service name.
- System scope install fails: use `--scope user` or run with admin privileges.
- Verify fails with no reply: check launchd state and the service plist.
- BYOXPC crashes at launch: confirm `XPC_SERVICE_PATH` is set and the bundle is a valid XPC service (`CFBundlePackageType=XPC!`).
- If you are running inside a sandboxed automation harness, XPC lookup can be blocked;
  run from a normal Terminal to confirm behavior.
- If `--sonoma-cross-check` reports `blocked` or `unavailable`, rerun from an
  unsandboxed Terminal context (the helper needs to observe a live runner PID).

Common decode errors (quick fixes)
- `missing field 'policy'`: add a top-level `policy` object with `format` and `sbpl_source`.
- `keyNotFound(... "specimen_id" ...)`: add a top-level `specimen_id` string.
- `unknown field 'path_membership'`: path rules belong in `policy.sbpl_source` as SBPL, not as JSON fields.
- Instrumentation ignored: ensure `instrumentation` is top level and `runner.mode` is `debuggable` (or use `--runner-mode debuggable`, or an external runner with matching entitlements).
