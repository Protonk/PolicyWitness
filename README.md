# PolicyWitness

PolicyWitness is a macOS sandbox witness harness. The atomic input is a specimen: a policy (SBPL or compiled profile bytes with params) paired with a probe plan. Running a specimen launches a new `PWRunner.xpc` process; the runner starts unsandboxed, applies the policy once, executes the probes, returns a structured report, then terminates. The controller can also correlate out-of-band evidence such as unified-log denials.

## Why

Sandbox behavior is easy to misinterpret. "rc == 0" is rarely enough to prove an effect, and denials can be ambiguous without context. PolicyWitness focuses on recording what happened, step by step, with evidence that is attributable to a specific process and lifecycle.

## How It Works

A specimen run spins up a fresh `PWRunner.xpc` process. The runner begins unsandboxed, loads libsandbox, compiles the provided policy (SBPL or compiled bytes with parameters), and applies it once—treating sandboxing as a one‑way transition for the lifetime of that process. After the policy is in force, it executes the probe plan step-by-step inside the sandboxed runner, collecting what happened for each probe.

Collection is made possible by executing each probe as a small, explicit attempt and recording its direct rc plus errno/kr. For each step, the runner also runs `sandbox_check` using the same operation and filter so you can compare the kernel’s prediction to the attempted outcome. When the policy uses deterministic side effects like `send-signal`, the runner installs a handler and records before/after signal counts so denials can be observed without relying on logs. The runner emits a single structured JSON report for the specimen—run metadata and per-step results—and exits immediately after replying. The result is a per-step record that favors witnessed facts over inferred explanations.

## Evidence Model

`Specimens → Runs → Steps → Evidence`

Each step can record multiple channels of evidence:

- **A**: in-band attempt result (rc/errno/kr)
- **B**: deterministic deny side-effect (SBPL `send-signal` if configured)
- **C**: unified-log correlation captured outside the sandbox
- **D**: `sandbox_check` prediction and "am I sandboxed" confirmation

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

- Using the app and workflows: `PolicyWitness.md`
- Repo orientation: `AGENTS.md`
- Contributing: `CONTRIBUTING.md`
- Signing/distribution: `SIGNING.md`
- Testing: `tests/README.md`
- Implementation details:
  - CLI contract and controller behavior: `controller/README.md`
  - Runner service architecture: `runner/README.md`
