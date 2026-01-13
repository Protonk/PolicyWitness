# `xpc/` (Swift runner: specimen-first sandbox witness)

This directory contains the Swift implementation of the **ephemeral sandbox runner** shipped inside `PolicyWitness.app`.

PolicyWitness is now **specimen-first**:

- The controller (`policy-witness`) starts a fresh XPC runner instance per specimen.
- The runner starts unsandboxed, applies a requested seatbelt profile exactly once (SBPL source + parameters, or compiled profile bytes), executes a probe plan, replies with JSON, and exits.

## Key files

- `xpc/PWRunnerAPI.swift`
  - `PWRunnerProtocol` (`runSpecimen(Data) -> Data`)
  - Codable JSON types: `PWRunnerRunSpec`, `PWRunnerPolicySpec`, `PWRunnerProbeStep`, and the returned `PWRunnerRunResult`

- `xpc/PWRunnerServiceHost.swift`
  - Runner implementation:
    - loads libsandbox dynamically (`dlopen` + `dlsym`)
    - applies the requested policy (`sandbox_compile_*` + `sandbox_apply`)
    - confirms sandbox state via `sandbox_check`
    - executes a small set of probe attempts (file + mach-lookup)

- `xpc/runner-client/main.swift` → builds `PolicyWitness.app/Contents/MacOS/pw-runner-client`
  - Thin `NSXPCConnection` wrapper that forwards JSON bytes and prints the runner’s JSON reply.

- `xpc/services/PWRunner/`
  - `Info.plist`, `Entitlements.plist`, `main.swift` for the runner XPC service bundle.

## Entitlements and sandboxing (important distinction)

The runner’s **codesign entitlements** are fixed hardened-runtime exceptions (debug attach / dynamic loading / dyld env / executable memory). They enable inspection and controlled extensibility, but they do **not** make sandbox policy “dynamic”.

Sandbox policy variation is driven by the specimen itself:

- the controller supplies SBPL (or compiled profile bytes),
- the runner applies it once to itself,
- the runner’s witness is defined by mandatory multi-channel evidence (see the controller docs).

## Agent note: “nested sandbox” harnesses

Some development harnesses run tools inside an OS sandbox. In those environments:

- XPC lookup can fail early with `NSCocoaErrorDomain` 4099 / error 159 `"Sandbox restriction"` (before the service launches).
- Unified Logging access can also be restricted, making deny-evidence capture impossible from inside the harness.

Treat this as an environment constraint, not a PolicyWitness regression.

Preflight with `policy-witness inside` (or `laboratory/pw-lab inside`). If `inside=true`, ask for approval/escalation and re-run once outside the harness sandbox to confirm the behavior.
