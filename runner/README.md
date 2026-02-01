# `runner/` (Swift runner: specimen-first sandbox witness)

This directory contains the Swift implementation of the **ephemeral sandbox runner** shipped inside `PolicyWitness.app`.

PolicyWitness is **specimen-first**:

- The controller (`policy-witness`) starts a fresh XPC runner instance per specimen.
- The runner starts unsandboxed, applies a requested seatbelt profile exactly once (SBPL source + parameters), executes a probe plan, replies with JSON, and exits.

## Key files

- `runner/PWRunnerAPI.swift`
  - `PWRunnerProtocol` (`runSpecimen(Data) -> Data`)
  - Codable JSON types: `PWRunnerRunSpec`, `PWRunnerPolicySpec`, `PWRunnerProbeStep`, and the returned `PWRunnerRunResult`
- `runner/SandboxLib.swift`
  - Explicit `dlopen` + `dlsym` bindings for libsandbox.
- `runner/SandboxApply.swift`
  - Policy hashing and single-shot `sandbox_apply` path.
- `runner/Instrumentation.swift`
  - Instrumentation ports and `InstrumentationState`.
- `runner/ProbeRunner.swift`
  - `sandbox_check` and probe attempts (file + mach-lookup).
- `runner/PathUtils.swift`
  - Path normalization and fd-based observation helpers.
- `runner/Signals.swift`
  - Deny-signal handler and counters.
- `runner/PWRunnerService.swift`
  - Orchestrates the run flow (decode → instrumentation → sandbox apply → probes → reply).

- `runner/runner-client/main.swift` → builds `PolicyWitness.app/Contents/MacOS/pw-runner-client`
  - Thin `NSXPCConnection` wrapper that forwards JSON bytes and prints the runner’s JSON reply.

- `runner/services/PWRunner/`
  - `Info.plist`, `Entitlements.plist`, `main.swift` for the standard runner XPC service bundle.
- `runner/services/PWRunnerDebug/`
  - `Info.plist`, `Entitlements.plist`, `main.swift` for the debuggable runner XPC service bundle.

## Specimen inputs

The runner consumes a `PWRunnerRunSpec` which contains:

- `policy`: `sbpl` source (with optional `params`)
- `probe_plan`: ordered probe steps (sandbox_check + attempt)

## Run result highlights

Each probe step reports both a `sandbox_check` and an `attempt` result:

- `sandbox_check` includes `scope` (`post_sandbox`) plus the original
  `filter_value` and a best-effort `effective_filter_value` (for `path` filters,
  this is the runner’s normalized path). It also reports `pid`, `operation`,
  `filter_type_id`, and `errno`/`error` when the check call fails.
- `attempt` always includes `exit_code` and `syscall_errno` (explicit `null` when
  not applicable), and for file attempts it includes `requested_path`,
  `normalized_path`, and `observed_path` (fd-based when available). The `rc`
  and `errno` fields are retained for compatibility.

## Entitlements and sandboxing (important distinction)

The standard built-in runner ships with minimal entitlements. The debuggable
built-in runner (and some external runners) include hardened-runtime exceptions
for inspection and controlled extensibility (debug attach / dynamic loading /
dyld env / executable memory). These do **not** make sandbox policy “dynamic”.

## Caller authorization (built-in only)

Built-in runners can require a signed caller before accepting XPC connections.
The check is controlled via Info.plist keys:

- `PWRunnerRequireSignedCaller` (bool)
- `PWRunnerAllowedIdentifiers` (optional array of code signing identifiers)

When enabled, the runner compares the caller’s Team ID to its own Team ID and
optionally enforces the allowlist. External runners are unaffected unless they
opt in by adding the same keys.

Sandbox policy variation is driven by the specimen itself:

- the controller supplies SBPL,
- the runner applies it once to itself,
- the runner’s witness is defined by mandatory multi-channel evidence (see the controller docs).

## External runner services

PolicyWitness can target **external runner services** when entitlements are
required. An external runner is the same PWRunner implementation, but signed
with user-selected entitlements and registered with launchd in one of two modes:

- **BYOXPC**: a signed `.xpc` bundle, addressed by `CFBundleIdentifier`.
- **MachMe**: a signed raw binary, addressed as a Mach service name.

Invariants:

- The protocol is unchanged (`PWRunnerProtocol` JSON-over-Data).
- One specimen -> one runner process; the runner applies the sandbox once and exits.
- Evidence schema remains identical; the controller records runner provenance.

The controller provides a `policy-witness runner` manager to install/register
these services and to enforce entitlements supersets before dispatch.

## Instrumentation port (opt-in)

The specimen schema includes an optional `instrumentation` object that activates
entitlement-backed adapters in a controlled, auditable way. When present, the
runner executes requested ports at `phase: pre_sandbox` (default) or
`phase: post_sandbox`, then includes `instrumentation` results in the run JSON.

Supported ports (v1):

- `dylib_load`: `dlopen` a specified dylib and optionally call a symbol (uses
  `com.apple.security.cs.disable-library-validation`).
- `debug_wait`: sleep for `sleep_ms` before sandbox apply to allow debugger
  attach (uses `com.apple.security.get-task-allow`).
- `execmem_probe`: attempt a JIT mapping (`MAP_JIT`, `PROT_READ|PROT_WRITE`) and report success/failure (uses
  `com.apple.security.cs.allow-jit`).
- `dyld_env`: report whether expected `DYLD_*` env vars are present; the runner
  cannot set these at runtime, so use an external runner with launchd
  `EnvironmentVariables`.

Default behavior is unchanged: if `instrumentation` is omitted, nothing runs.

## Agent note: “nested sandbox” harnesses

Some development harnesses run tools inside an OS sandbox. In those environments:

- XPC lookup can fail early with `NSCocoaErrorDomain` 4099 / error 159 `"Sandbox restriction"` (before the service launches).
- Unified Logging access can also be restricted, making deny-evidence capture impossible from inside the harness.

Treat this as an environment constraint, not a PolicyWitness regression.

If you suspect you are running under a sandboxed automation harness, re-run from a normal Terminal (or with escalation) before debugging PolicyWitness itself.
