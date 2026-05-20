# PolicyWitness

>Read the [user guide](PolicyWitness.md) for more detail

PolicyWitness is a macOS sandbox witness harness for verifying sandbox policies with observable evidence. Sandbox outcomes are easy to misread without clear attribution and consistent output. PolicyWitness ties each result to a specific runner instance and emits a stable JSON envelope so you can audit, diff, and automate tests without guesswork. 

## Flow

>Specimens -> Runs -> Steps -> Evidence

PolicyWitness operates on specimen, packages of SBPL + entitlements and probe plans. The controller launches a fresh runner for each specimen. The runner starts unsandboxed, loads libsandbox, applies the provided policy once, and then executes the probe plan step by step inside the sandbox. Each step performs an explicit attempt, records rc plus errno or kr, and also runs `sandbox_check` with the same operation and filter so you can compare predicted vs observed outcomes. The runner returns a single JSON result and exits.

Each step may include multiple evidence channels:

- **A**: in-band attempt result (rc/errno/kr)
- **B**: deterministic side effects (for example SBPL `send-signal`)
- **C**: out-of-band unified-log correlation (best-effort)
- **D**: `sandbox_check` prediction and "am I sandboxed" confirmation

## Runner modes

PolicyWitness supports three runner modes. All three return the same JSON envelope and speak the same NSXPC protocol; they differ only in how the runner process is supplied and registered.

- `standard`: built-in XPC service embedded in `dist/PolicyWitness.app`; no install step. Default when no runner is specified.
- `debuggable`: built-in XPC service embedded in `dist/PolicyWitness.app`; no install step.
- `byoxpc`: user-supplied `.xpc` bundle (optionally self-signed) installed with `policy-witness runner install --kind byoxpc`.

PolicyWitness treats entitlements as a first-class input alongside SBPL. Register an externally signed runner with the entitlements your probes require, then apply a per-specimen SBPL policy on top to test temporary restrictions or entitlements + SBPL combinations in a single run.

### Instrumentation

Instrumentation ports are part of the debuggable runner (or external runners with matching entitlements), allowing closer inspection.

- `dyld_env`: report expected `DYLD_*` env vars (observation only); to set them, use an external runner installed with `--env KEY=VALUE`.
- `dylib_load`: load a dylib and optionally call a symbol (`com.apple.security.cs.disable-library-validation`)
- `debug_wait`: pause before sandbox apply for debugger attach (`com.apple.security.get-task-allow`)
- `execmem_probe`: attempt JIT `mmap` (MAP_JIT, PROT_READ|PROT_WRITE) and report success/failure (`com.apple.security.cs.allow-jit`; falls back to legacy RWX if available)

## What Ships

This repo builds a single distributable app bundle:

- `dist/PolicyWitness.app`
  - `Contents/MacOS/policy-witness` (Rust controller)
  - `Contents/MacOS/pw-runner-client` (Swift NSXPCConnection wrapper)
  - `Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper)
  - `Contents/XPCServices/PWRunner.xpc` (Swift runner, standard mode; one specimen per process)
  - `Contents/XPCServices/PWRunnerDebug.xpc` (Swift runner, debuggable mode; one specimen per process)
  - `Contents/Resources/Evidence/*` (generated manifests: hashes/entitlements, `symbols.json`)

## Where To Learn

- Repo orientation: [AGENTS.md](AGENTS.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Testing: [tests/README.md](tests/README.md)
- Implementation details:
  - Signing/distribution: [SIGNING.md](SIGNING.md)
  - Using the app and workflows: [PolicyWitness.md](PolicyWitness.md)
  - CLI contract and controller behavior: [controller/README.md](controller/README.md)
  - Runner service architecture: [runner/README.md](runner/README.md)
