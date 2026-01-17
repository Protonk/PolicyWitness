# PolicyWitness

PolicyWitness is a macOS sandbox witness harness for verifying sandbox policies with observable evidence. Each run consumes a specimen (policy plus probe plan), executes it in a fresh `PWRunner.xpc` process, and emits a structured JSON report.

Sandbox outcomes are easy to misread without clear attribution and consistent output. PolicyWitness ties each result to a specific runner instance and emits a stable JSON envelope so you can audit, diff, and automate tests without guesswork.

Read the [user guide](PolicyWitness.md) for more detail.

## Flow

>Specimens -> Runs -> Steps -> Evidence

The controller launches a fresh runner for each specimen. The runner starts unsandboxed, loads libsandbox, applies the provided policy once, and then executes the probe plan step by step inside the sandbox. Each step performs an explicit attempt, records rc plus errno or kr, and also runs `sandbox_check` with the same operation and filter so you can compare predicted vs observed outcomes. The runner returns a single JSON result and exits.

Each step may include multiple evidence channels:

- **A**: in-band attempt result (rc/errno/kr)
- **B**: deterministic side effects (for example SBPL `send-signal`)
- **C**: out-of-band unified-log correlation (best-effort)
- **D**: `sandbox_check` prediction and "am I sandboxed" confirmation

## Bring your own entitlements

PolicyWitness treats entitlements as a first-class input alongside SBPL. You can register an externally signed runner with the entitlements your probes require, then apply a per-specimen SBPL policy on top to test temporary restrictions or entitlements + SBPL combinations in a single run.

### Instrumentation port

Specimens may include an `instrumentation` object with ports executed `pre_sandbox` or `post_sandbox`. Results are reported in the run JSON and do not change the run outcome. You can also inject instrumentation at runtime with `policy-witness run <request.json> --instrumentation <json|@path>`.

- `dyld_env`: report expected `DYLD_*` env vars (`com.apple.security.cs.allow-dyld-environment-variables`); set via an external runner with `policy-witness runner install --env KEY=VALUE`.
- `dylib_load`: load a dylib and optionally call a symbol (`com.apple.security.cs.disable-library-validation`)
- `debug_wait`: pause before sandbox apply for debugger attach (`com.apple.security.get-task-allow`)
- `execmem_probe`: attempt RWX `mmap` and report success/failure (`com.apple.security.cs.allow-unsigned-executable-memory`)

## What Ships

This repo builds a single distributable app bundle:

- `PolicyWitness.app`
  - `Contents/MacOS/policy-witness` (Rust controller)
  - `Contents/MacOS/pw-runner-client` (Swift NSXPCConnection wrapper)
  - `Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper)
  - `Contents/XPCServices/PWRunner.xpc` (Swift runner; one specimen per process)
  - `Contents/Resources/Evidence/*` (generated manifests: hashes/entitlements, `symbols.json`)
- `PolicyWitness.md` (user guide)

## Where To Learn

- Using the app and workflows: [PolicyWitness.md](PolicyWitness.md)
- Repo orientation: [AGENTS.md](AGENTS.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Signing/distribution: [SIGNING.md](SIGNING.md)
- Testing: [tests/README.md](tests/README.md)
- Implementation details:
  - CLI contract and controller behavior: [controller/README.md](controller/README.md)
  - Runner service architecture: [runner/README.md](runner/README.md)
