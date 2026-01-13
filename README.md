# PolicyWitness

PolicyWitness is a sandbox runner instrumentation harness. Variation is supplied at runtime as SBPL / compiled profile bytes plus a probe plan. A single ephemeral XPC runner (`PWRunner.xpc`) self-applies the sandbox per specimen, executes the plan, and exits.

- The controller starts a fresh `PWRunner.xpc` instance per specimen.
- The runner starts unsandboxed, applies the requested sandbox profile **exactly once**, runs the probe plan, returns a structured result, and exits.
- The controller correlates supporting evidence (unified-log deny lines) by PID and window.

What’s hard in computing security is making correct claims about boundaries. The sandbox is an especially hard boundary to make a claim about because it often collapses into ambiguous signals, depends on identity and context, and frequently requires external evidence to attribute a denial. PolicyWitness makes claims by producing per-step, per-process witnesses with explicit lifecycle boundaries.

## The Core Model

>Specimens → Runs → Steps → Evidence

Each specimen evaluation records mandatory, multi-channel evidence:

- **A**: in-band operation attempt result (rc/errno/kr)
- **B**: deterministic deny side-effect (SBPL `send-signal` if the policy uses it)
- **C**: unified-log correlation (captured outside the sandbox boundary)
- **D**: `sandbox_check` prediction / “am I sandboxed” confirmation

## What ships

This repo builds a single distributable specimen:

- `PolicyWitness.app` — the bundle you run and inspect
  - `Contents/MacOS/policy-witness` (Rust launcher; host-side)
  - `Contents/MacOS/pw-runner-client` (Swift; NSXPCConnection wrapper for `PWRunner.xpc`)
  - `Contents/MacOS/sandbox-log-observer` (Rust; unified-log deny capture helper)
  - `Contents/XPCServices/PWRunner.xpc` (Swift runner; self-applies sandbox per specimen)
  - `Contents/Resources/Evidence/*` (generated manifests: hashes/entitlements, `symbols.json`)
- `PolicyWitness.md` — the user guide shipped alongside the app

## Where To Learn

If you're...
- using the app / workflows: [`PolicyWitness.md`](PolicyWitness.md)
- orienting yourself in the repo: [`AGENTS.md`](AGENTS.md)
- contributing: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- signing/distributing: [`SIGNING.md`](SIGNING.md)
- testing: [`tests/README.md`](tests/README.md)
- changing...
  - CLI behavior/output contracts: [`controller/README.md`](controller/README.md)
  - the runner XPC service: [`runner/README.md`](runner/README.md)
