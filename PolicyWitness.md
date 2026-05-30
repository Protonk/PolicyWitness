# PolicyWitness User Guide

PolicyWitness runs sandbox specimens and prints a single JSON result to stdout.
This guide covers usage only.

## Choose your runner

PolicyWitness supports three runner modes:

1) Standard runner (built-in)
- Default path; minimal entitlements (no debug allowances).
- Select with `runner.mode="standard"` or `--runner-mode standard`.

2) Debuggable runner (built-in)
- Debug-friendly entitlements plus instrumentation ports.
- Select with `runner.mode="debuggable"` or `--runner-mode debuggable`.
- Tested by `tests/suites/runner_debuggable/run.sh`.

3) BYOXPC runner (external XPC bundle)
- Use when you need extra entitlements; supply a signed `.xpc` bundle.
- Service name must match the bundle's `CFBundleIdentifier` (no override).
- Install with `policy-witness runner install --kind byoxpc ...`.
- Tested by `tests/suites/runner_byoxpc/run.sh` (opt-in; GUI session required).

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
- `params_scan_complete`: false when the source contains at least one
  `(param X)` form where `X` is not a quoted string. That's typically
  macro-indirected, e.g.
  `(define (helper pn) (subpath (param pn)))` with `(helper "FOO")` at the
  call site — the literal `"FOO"` is bound to `pn` at a level the surface
  lexer doesn't expand. When this flag is false, treat `params_missing:
  []` as "we couldn't tell" rather than "nothing required". The cryptic
  libsandbox error ("expected pattern, got boolean") then surfaces under
  `compile_error` as before. Resolving these would require real macro
  expansion and is out of scope for the preflight scanner.

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

Runner responses use `schema_version = 4`. The XPC service process stays
unsandboxed and spawns a short-lived worker that applies the specimen policy.
`data.runner_result.pid` names that worker process when
`runner_subprocess` is present; use it for sandbox unified-log correlation.
`runner_subprocess` records `{ pid, term_signal, exit_code, partial_steps }`.

`schema_version = 4` (additive to v3):

- `validator_subprocess: { pid, exit_code, term_signal } | null` — the
  `sb_api_validator --batch` child the host spawns alongside the C
  worker (the default code path after the runner reshape) to collect
  `sandbox_check` verdicts against the sandboxed worker_pid.
  `null` when no validator child was spawned, which happens in three
  cases:
    1. The request opted out of the C-worker path
       (`_test_overrides.use_c_worker: false`, or `instrumentation`
       set — both route to the legacy Swift worker, which doesn't
       spawn a separate validator).
    2. Every probe in the plan had an (operation, filter) pair in
       the `prediction_unavailable` set — the orchestrator skipped
       the validator entirely because there were no probes to send,
       and synthesized the per-step `sandbox_check.outcome =
       "prediction_unavailable"` verdicts locally.
    3. The validator failed to spawn before any metadata could be
       captured (surfaced as `normalized_outcome =
       "validator_spawn_failed"`).
  Otherwise populated, with exactly one of `exit_code` (clean exit)
  or `term_signal` (SIGKILL fallback) non-null.
- `steps[].drift: bool | null` — disagreement between the validator's
  predicted verdict and the attempt's observed verdict for the step.
  `true` when they disagree about allow/deny (libsandbox-drift evidence;
  the property PolicyWitness exists to surface). `false` when they
  agree. `null` when no comparison is possible: the validator wasn't
  run, the validator skipped this step (e.g. an op+filter pair in
  `prediction_unavailable`), or the attempt didn't produce a verdict.
  Encoded as explicit JSON null at v4 — consumers introspecting the
  raw JSON see the key whether or not a comparison was possible, so
  "absent" reliably means "v3 producer."
- Top-level `pid` semantics from v3 are preserved: when
  `runner_subprocess` is present, it names the sandboxed worker
  process for unified-log correlation. `validator_subprocess.pid` is
  the validator's PID and is a separate process.

`data.runner_result.normalized_outcome` values the runner can produce
(controller-level outcomes like `bad_policy`, `missing_params`, and
`policy_too_large` are documented elsewhere on this page):

- `ok` — worker wrote a complete report and exited cleanly.
- `runner_sandbox_denied` — worker spawned, applied the policy, and was
  terminated by a fatal signal before writing a report. The kernel sandbox
  is the overwhelming cause on macOS; the precise signal is preserved in
  `runner_subprocess.term_signal` (commonly `9` for SIGKILL, or `5`/`6` for
  SIGTRAP/SIGABRT from Swift's runtime when an allocation trap fires under
  a `(deny default)` profile that blocks `mach_vm_allocate`-class traps).
  `data.sandbox_log_capture.deny_events` carries the matching unified-log
  evidence when available.
- `runner_timeout` — worker did not exit and did not write a report within
  the host's deadline. The host SIGKILLs the worker before replying.
- `worker_spawn_failed` — host could not `posix_spawn` the worker
  (filesystem/codesign/quota error). Worker never ran.
- `bad_request` — request JSON failed to decode or referenced an unknown
  sandbox operation. No worker is spawned.
- `libsandbox_unavailable` — libsandbox could not be opened on this host.
- `sandbox_apply_failed` — worker reached `sandbox_apply` but libsandbox
  rejected the policy (returned non-zero). The worker reports this and
  exits cleanly; the host forwards it.
- `already_ran` — the XPC service instance only accepts one
  `runSpecimen` call. A second call returns this error.

`xpc_error`, `xpc_timeout`, `xpc_proxy_type_mismatch`, and `xpc_no_reply`
are synthesized by `pw-runner-client` when the XPC peer itself can't be
reached. After the host/worker split they should be rare: the unsandboxed
host always replies unless launchd or codesign reject the bundle outright.

The request schema includes a `_test_overrides` field that exists to
simplify build and test procedures. It is not for public consumption.

The runner echoes step results with additional context:

- `steps[].sandbox_check`: `{ rc, outcome, pid, operation, scope, filter_kind, filter_value, effective_filter_value, filter_type_id, errno, error, path_diagnostics? }`
- `steps[].attempt`: `{ rc, exit_code, errno, syscall_errno, outcome, error, requested_path, normalized_path, observed_path }`

Notes:
- `scope` is `post_sandbox` for runner-hosted checks.
- `requested_path`, `normalized_path`, and `observed_path` are present for file
  attempts; non-file attempts carry explicit `null` for these fields.
- `filter_value` is the exact string the runner passes to `sandbox_check`,
  except when `outcome == "prediction_unavailable"` — in that case no
  `sandbox_check` call is made; `filter_value` is echoed back from the
  request unchanged for cross-referencing with the specimen.
- `effective_filter_value` is a canonicalized/realpath form used for reporting only.
- `filter_type_id`: `1` (path), `2` (mach-lookup global), `17`
  (mach-lookup local). The global-name ID was previously documented
  as `16` based on a now-invalidated external reference; empirical
  verification against actual kernel enforcement (see
  `tests/suites/witness_contract/harness/verify_filter_id.sh`) shows
  `2` works correctly under strict verification (deny on the policy's
  denied value AND allow on a sibling un-denied value). ID `12` also
  passes the same strict verification across the scan to 200 —
  presumably an alias or aliased predicate path — so `2` is the
  selected working ID, not the uniquely correct one. The local-name
  ID (`17`) has not been re-verified by the same methodology and may
  also be incorrect; it is documented here unchanged pending a
  verification fixture. For filter kinds in the
  prediction_unavailable set, no `filter_type_id` is emitted (see the
  next section).
- `outcome`: `allow`, `deny`, `error`, or `prediction_unavailable`. The
  last value is emitted when the runner deliberately skips
  `sandbox_check` for an op+filter combination where the userland
  predicate is empirically known to drift from kernel enforcement.
  Channel A (the `attempt` result) remains the reliable evidence for
  those probes; the prediction is honestly absent rather than wrong.
  When `outcome == "prediction_unavailable"`, `rc` is the sentinel
  `-1` (not `0`) and `errno`/`filter_type_id` are `null` — consumers
  that key on `rc == 0` for "allow" must check `outcome` first so the
  sentinel is not misread.

### Filter kinds where prediction is unavailable

Some `(operation, filter_kind)` pairs have a documented mismatch
between `sandbox_check`'s userland verdict and the kernel's actual
enforcement. For these, the runner accepts the filter in specimens
(so policies can be authored), accepts and enforces the policy
correctly at compile/apply time, but skips `sandbox_check` entirely
and emits `step.sandbox_check.outcome = "prediction_unavailable"`
with `step.sandbox_check.rc == -1` instead of a misleading
`allow`/`deny`. The attempt still runs and provides the real evidence.

The contract is keyed on the `(operation, filter_kind)` pair, not on
the filter kind alone — a filter kind that drifts for one operation
may behave correctly with another, and the verification is
op+filter-specific. A specimen pairing one of these filter kinds with
a DIFFERENT operation gets a normal `sandbox_check` call; the
prediction may still be wrong, but the runner doesn't override a
prediction it hasn't verified to be wrong.

Currently in this category:

- `(iokit-open-service, iokit_registry_entry_class)` — verified
  2026-05-29 unreliable across all candidate filter IDs in 1..200
  against `IOSurfaceRoot`. The cross-check (`--sonoma-cross-check`)
  mirrors with `status="skipped"` and an error that includes the
  literal string `prediction_unavailable`.
- `(iokit-open-user-client, iokit_user_client_class)` — verified
  2026-05-29 with policy filter `IOSurfaceRootUserClient` and probe
  target `IOSurfaceRoot`. `iokit-open-user-client` is the SBPL
  operation `iokit-user-client-class` matches against (see Apple's
  `/System/Library/Sandbox/Profiles/application.sb` for canonical
  usage); `iokit-open-service` is a sibling operation that fires for
  the IOService class itself.
- `(sysctl-read, sysctl_name)` — verified 2026-05-29 unreliable
  across all candidate filter IDs in 1..200 against `kern.osrelease`.
  Confirms the drift pattern is not iokit-specific.

Adding a pair to this set requires empirical verification via
`tests/suites/witness_contract/harness/verify_filter_id.sh`. The
matching code lives in
`runner/ProbeRunner.swift::predictionUnavailableOpFilters` and
`controller/src/sonoma_cross_check.rs::PREDICTION_UNAVAILABLE_PAIRS`;
both lists must agree (source_drift enforces).
- `path_diagnostics` is emitted only for path-filter checks. Introduced in
  runner response `schema_version = 2`; consumers branching on
  `schema_version` can rely on its presence on any path-filter check at v2+.
  It carries the candidate kernel-side forms of the check path so a caller
  can see which prefix libsandbox could have been comparing against when a
  `(subpath ...)` rule denies a path that looked like it should match.
  Fields: `{ input, realpath_resolved, firmlink_resolved, data_volume_form }`.
  The runner still passes the raw `filter_value` to `sandbox_check` — this
  block is observation only.

  Producer: `path_diagnostics` is computed by the unsandboxed runner
  host (`PWRunnerService.enrichPathDiagnostics`) after the worker
  process returns. Earlier builds computed it inside the worker; the
  observable schema is unchanged but `realpath_resolved` is now
  populated more reliably under restrictive policies (the worker's
  stat is blocked by `(deny default)`; the host's is not). Consumers
  that intentionally relied on `realpath_resolved == null` as a
  signal that the worker's enclosing sandbox blocked the stat must
  read another channel for that signal — `path_diagnostics` no
  longer surfaces it.

  At v2+ all four keys are always emitted: a string when computed, an
  explicit `null` when the computation didn't produce a value. Consumers
  can therefore distinguish "computed and the result was null" (key
  present, value `null`) from "diagnostic was not emitted at all" (key
  absent or the entire `path_diagnostics` object absent).
  - `realpath_resolved`: `realpath(3)` of `input`, or null on failure.
    Computed in the unsandboxed host; under normal conditions this is
    populated whenever the file exists. Null only when the host's own
    `realpath` fails (path doesn't exist, permission denied at the
    host level, etc.). The other forms below remain computable in that
    case.
  - `firmlink_resolved`: the realpath result rewritten through
    `/usr/share/firmlinks`. When realpath returned null, the host
    falls back to a pure-string substitution of the standard userspace
    symlinks (`/etc`, `/tmp`, `/var` → `/private/{etc,tmp,var}`)
    before applying firmlinks, so `/etc/hosts` still lands at
    `/System/Volumes/Data/private/etc/hosts` in the rare case the
    host's `realpath` fails. The firmlinks map is loaded eagerly and
    has a built-in fallback mirroring the standard mappings on
    Catalina+.
  - `data_volume_form`: heuristic shortcut that prepends
    `/System/Volumes/Data` to paths under `/private/`. Computed from the
    same fallback basis as `firmlink_resolved`, so it is populated for the
    common case even when realpath is unavailable.

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

The runner is two processes per specimen: an unsandboxed XPC service host
that orchestrates, and a short-lived worker that applies the policy and
runs the probe plan. Attach the debugger to the **worker** to inspect
policy effects; the host never applies the policy and isn't useful for
that purpose.

1. Use the debuggable runner so `debug_wait` and `dylib_load` are honored:
   add `"runner": { "mode": "debuggable" }` to the specimen, or pass
   `--runner-mode debuggable` on the CLI.
2. Add a `debug_wait` instrumentation port at `phase: "pre_sandbox"` (the
   default) to open an attach window in the worker *before* sandbox apply.
   Use `phase: "post_sandbox"` instead if you want to inspect the worker
   *after* the sandbox is in effect.
3. Run the specimen. While the worker is paused in `debug_wait`, find its
   PID through the live process table:
   ```sh
   pgrep -lf -- '--apply-and-probe-worker'
   ```
   The worker's argv includes `--apply-and-probe-worker --specimen-id <id>`
   so multiple concurrent workers are distinguishable by their specimen
   label. The host process has the same Mach-O name but no `--apply-and-probe-worker`
   in its argv — don't attach to that one.
4. `lldb -p <worker-pid>` and proceed. `runner_subprocess.pid` in the
   eventual JSON envelope confirms which worker you attached to.

Run interactive `lldb`, `pgrep`, and `log stream` workflows from an
unsandboxed Terminal. A sandboxed automation harness can block XPC
lookup, process-table inspection, and unified-log capture before any
runner code executes — that's an environment constraint, not a
PolicyWitness behavior.

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

## External runners (BYOXPC)

Use this when you need entitlements that are not in the built-in runner.
BYOXPC is the only external runner kind.

### What you need

- A runner `.xpc` bundle to sign (typically a copy of `PWRunner.xpc` or `PWRunnerDebug.xpc`).
- A signing identity (Developer ID Application) or ad-hoc signing for local use.
- An entitlements plist.
- A logged-in GUI session (launchd bootstrap is not available from non-GUI shells).

### Tested install path (copy/paste)

This sequence matches `tests/suites/runner_byoxpc/run.sh` and is the
recommended starting point.

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
- BYOXPC service name must match the bundle's `CFBundleIdentifier` (no override).
- The bundle must be a valid XPC service (`CFBundlePackageType=XPC!`); plain
  binaries are rejected at install time. The executable is derived from
  `<bundle>/Contents/MacOS/<CFBundleExecutable>`.
- `--entitlements` requires either `--identity <id>` or `--allow-adhoc` so the
  supplied entitlements are actually re-embedded into the binary. Passing
  `--entitlements` without one of those is rejected — the registry would
  otherwise record entitlements that the kernel will not enforce.

The install command writes a launchd plist, bootstraps the service, and records
the runner in the local registry. The registry's `entitlements` field always
reflects what's embedded in the binary (read back via `codesign -d --entitlements`),
not what was supplied on the command line.

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
  "service": "com.yourteam.policy-witness.PWRunner",
  "mode": "byoxpc"
}
```

`runner.mode` is optional; when present it must equal `byoxpc` for external
runners. Valid modes: `standard`, `debuggable`, `byoxpc`.
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
- `--runner-mode <standard|debuggable|byoxpc>`: inject `runner.mode` into the request
- `--instrumentation <json|@path>`: inject instrumentation ports into the request
- `--sonoma-cross-check`: run an sb_api_validator cross-check against the runner PID
  while it is paused post-sandbox; results are attached under `data.sonoma_cross_check`

## Troubleshooting

- Service not found: run `policy-witness runner list` and confirm the service name.
- System scope install fails: use `--scope user` or run with admin privileges.
- Verify fails with no reply: check launchd state and the service plist.
- BYOXPC crashes at launch: confirm `XPC_SERVICE_PATH` is set and the bundle is a valid XPC service (`CFBundlePackageType=XPC!`).
- `normalized_outcome` is `runner_sandbox_denied` and you expected `ok`: the
  worker was terminated by the kernel sandbox (or by a Swift-runtime trap
  triggered by a denied `mach_vm_allocate`) before writing its report.
  - **Quickest read:** `data.runner_sandbox_diagnostics.first_deny` carries
    the first kernel deny attributed to the worker PID — `operation`,
    `path` if applicable, and the raw unified-log line. Use this when you
    want one line that names the cause.
  - `data.runner_sandbox_diagnostics.first_deny` is `null` when log capture
    was blocked/unavailable or when no deny event matches the worker PID
    (rare; usually means the capture window missed the event). The outer
    `runner_sandbox_diagnostics` object is present whenever the outcome is
    `runner_sandbox_denied`, so consumers can branch on `first_deny != null`
    directly.
  - For the full deny list (when one isn't enough), see
    `data.sandbox_log_capture.deny_events`.
  - `data.runner_result.runner_subprocess.term_signal` carries the exit
    signal; a bare `(deny default)` policy almost always produces this
    outcome unless the specimen adds enough `(allow ...)` entries to keep
    the worker's encode-and-write path alive.
- `normalized_outcome` is `worker_spawn_failed`: the host could not
  `posix_spawn` the worker. Verify the bundle is signed and on a writable
  filesystem; `pgrep -fl PWRunner` should show no stragglers.
- If you are running inside a sandboxed automation harness, XPC lookup can be blocked;
  run from a normal Terminal to confirm behavior.
- If `--sonoma-cross-check` reports `blocked` or `unavailable`, rerun from an
  unsandboxed Terminal context (the helper needs to observe a live runner PID).

Common decode errors (quick fixes)
- `missing field 'policy'`: add a top-level `policy` object with `format` and `sbpl_source`.
- `keyNotFound(... "specimen_id" ...)`: add a top-level `specimen_id` string.
- `unknown field 'path_membership'`: path rules belong in `policy.sbpl_source` as SBPL, not as JSON fields.
- Instrumentation ignored: ensure `instrumentation` is top level and `runner.mode` is `debuggable` (or use `--runner-mode debuggable`, or an external runner with matching entitlements).
