# PolicyWitness

PolicyWitness is a macOS tool to instrument App Sandbox (seatbelt) policy effects without hand‑waving. It is now **specimen‑first**: sandbox variation is supplied at runtime as SBPL / compiled profile bytes plus a probe plan, executed by a single ephemeral runner service, rather than by proliferating many differently‑entitled XPC services.

For sandbox instrumentation, the “API” you usually get back is just EPERM/EACCES (or a killed process), which rarely tells you what policy check fired, which operation/path/class triggered it, or whether you even reached the code you think you reached. Seatbelt/unified-log deny lines are often the only concrete explanation the OS will give you, but they’re easy to miss (wrong PID, process exits fast, log filtering, “deny” is silent for some paths) and easy to mis-correlate after the fact. 

PolicyWitness avoids these issues by treating the sandbox boundary as an **ephemeral runner process**:

- The controller starts a fresh `PWRunner.xpc` instance per specimen.
- The runner starts unsandboxed, applies the requested sandbox profile **exactly once**, runs the probe plan, returns a structured result, and exits.
- The controller correlates supporting evidence (unified-log deny lines, signposts, etc.) by PID and window.

What’s hard in computing security is making correct claims about boundaries. The sandbox is an especially hard boundary to make a claim about because it often collapses into ambiguous signals, depends on identity and context, and frequently requires external evidence to attribute a denial. PolicyWitness makes claims by producing per-phase, per-process witnesses with durable-session context and explicit lifecycle signals.

## The Core Model
>Specimens → Runs → Steps → Evidence

Each specimen evaluation records mandatory, multi-channel evidence:

- **A**: in-band operation attempt result (rc/errno/kr)
- **B**: deterministic deny marker (SBPL `message` on deny for the instrumented run)
- **C**: unified-log correlation (captured outside the sandbox boundary)
- **D**: `sandbox_check` prediction / “am I sandboxed” confirmation

The preferred execution surface is in-process probes dispatched by `probe_id` (not arbitrary path execution). If you want a three-way comparison (baseline vs `sandbox-exec` vs XPC), the tri-run harness under `experiments/` produces a mismatch atlas.

## Commitments

* **Specimen-first**: sandbox variation is SBPL / compiled bytes + parameters + plan, not “one XPC service per entitlement set.”
* **One-way sandbox**: the runner applies one profile per process instance; a new specimen means a new runner instance.
* **Witness over interpretation**: outcomes are supported by multi-channel evidence (A–D), not return codes or narrative attribution.

## What ships

This repo builds a single distributable specimen:

- `PolicyWitness.app` — the bundle you run and inspect
  - `Contents/MacOS/policy-witness` (Rust launcher; host-side)
  - `Contents/MacOS/pw-runner-client` (Swift; NSXPCConnection wrapper for `PWRunner.xpc`)
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
  - CLI behavior/output contracts: [`runner/README.md`](runner/README.md)
  - the runner XPC service: [`xpc/README.md`](xpc/README.md)
