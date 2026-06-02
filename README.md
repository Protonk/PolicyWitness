# PolicyWitness

>Read the [user guide](PolicyWitness.md) for more detail, or the [FAQ](QUESTIONS.md) for shorter answers to common questions.

PolicyWitness is a macOS sandbox witness harness for verifying sandbox policies with observable evidence. Sandbox outcomes are easy to misread without clear attribution and consistent output. PolicyWitness ties each result to a specific runner instance and emits a stable JSON envelope so you can audit, diff, and automate tests without guesswork.

## Flow

>Specimens -> Runs -> Steps -> Evidence

PolicyWitness operates on specimens: an SBPL policy plus a probe plan. The controller launches a fresh runner per specimen. The runner is an unsandboxed XPC host plus two short-lived children: `pw-probe-runner` (sandboxed C worker that applies the specimen policy to itself and runs the probe plan) and `sb_api_validator --batch` (queries `sandbox_check` for each probe against the worker's sandboxed PID). The host stays unsandboxed so the XPC reply path survives even under a strict `(deny default)` profile, joins both children's outputs into one JSON envelope, and replies.

Each step records two parallel verdicts:

- **Attempt** (`steps[].attempt`): in-band kernel response — `rc`, `errno`, mach `kr` — from actually performing the operation inside the sandboxed worker.
- **Prediction** (`steps[].sandbox_check`): the userland `sandbox_check` verdict for the same operation + filter against the same PID, supplied by the validator.

`steps[].drift` flags disagreement between the two. Unified-log evidence for kernel denies is attached out-of-band (best-effort) via `data.sandbox_log_capture` and `data.runner_sandbox_diagnostics.first_deny`.

## Runner modes

PolicyWitness supports two runner modes. Both return the same JSON envelope and speak the same NSXPC protocol; they differ only in how the runner process is supplied and registered.

- `standard`: built-in XPC service embedded in `dist/PolicyWitness.app`; no install step. Default when no runner is specified.
- `byoxpc`: user-supplied `.xpc` bundle (optionally self-signed) installed with `policy-witness runner install --kind byoxpc`. Use this when probes require entitlements the standard runner doesn't ship — debug-attach (`com.apple.security.get-task-allow`), custom dylib loading, JIT, DYLD env, etc.

PolicyWitness treats entitlements as a first-class input alongside SBPL. Register an externally signed runner with the entitlements your probes require, then apply a per-specimen SBPL policy on top to test temporary restrictions or entitlements + SBPL combinations in a single run.

## What Ships

This repo builds a single distributable app bundle:

- `dist/PolicyWitness.app`
  - `Contents/MacOS/policy-witness` (Rust controller)
  - `Contents/MacOS/pw-runner-client` (Swift NSXPCConnection wrapper)
  - `Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper)
  - `Contents/MacOS/sbpl-preflight` (SBPL compile/preflight helper)
  - `Contents/MacOS/sb_api_validator` (diagnostic copy of the validator CLI; production traffic uses the bundle-local copy embedded inside each XPC service)
  - `Contents/XPCServices/PWRunner.xpc` (Swift XPC host; one host + two short-lived children per specimen)
    - `Contents/MacOS/pw-probe-runner` (bundle-local C worker that applies the policy and runs probe attempts)
    - `Contents/MacOS/sb_api_validator` (bundle-local validator launched once per run for sandbox_check verdicts)
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
