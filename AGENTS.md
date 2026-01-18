# AGENTS.md

This file is for contributors and agents.

PolicyWitness is a sandbox runner instrumentation harness. Each run is driven by a specimen — an SBPL policy plus a probe plan — which is handed to a fresh `PWRunner.xpc` instance that self-applies the sandbox, executes the plan, and exits.

## Quick Router (open first)

Pick what you’re changing:

- **CLI behavior / JSON contract** → `controller/README.md`, `controller/src/main.rs`
- **Runner service (self-sandboxing witness)** → `runner/README.md`, `runner/services/PWRunner/`
- **Runner API types** → `runner/PWRunnerAPI.swift`
- **Runner client (NSXPCConnection wrapper)** → `runner/runner-client/`
- **Build + signing** → `build.sh`, `SIGNING.md`
- **Evidence generation / manifests** → `tests/build-evidence.py`
- **Tests** → `tests/README.md`, `tests/run.sh --all`
- **Opt-in tests registry** → `tests/OPT_IN_TESTS.md`
- **User guide** → `PolicyWitness.md`

## Vocabulary (repo-anchored)

- **Specimen**: the unit of input for a run — policy (SBPL + params) plus a probe plan.
- **Controller**: the host-side orchestrator (`PolicyWitness.app/Contents/MacOS/policy-witness`) that drives the runner and prints a JSON envelope.
- **Runner**: the ephemeral XPC service (`PolicyWitness.app/Contents/XPCServices/PWRunner.xpc`) that applies one sandbox policy, executes the probe plan, returns JSON, and exits.
- **Probe step**: a `sandbox_check` query paired with an attempted operation (`file` or `mach_lookup`).

## What Ships (bundle layout contract)

The `.app` layout is a contract: tests and evidence generation assume these paths.

- `PolicyWitness.app/Contents/MacOS/policy-witness` (Rust controller / orchestrator)
- `PolicyWitness.app/Contents/MacOS/pw-runner-client` (Swift client that talks to `PWRunner.xpc`)
- `PolicyWitness.app/Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper for sandbox denials)
- `PolicyWitness.app/Contents/MacOS/sb_api_validator` (C sandbox_check cross-check helper)
- `PolicyWitness.app/Contents/XPCServices/PWRunner.xpc` (Swift runner; one specimen per instance)
- `PolicyWitness.app/Contents/Resources/Evidence/manifest.json` (embedded inventory: hashes + signing/entitlements metadata)
- `PolicyWitness.app/Contents/Resources/Evidence/symbols.json` (best-effort marker inventory)

If you rename/move anything here, expect downstream breakage (build script, evidence, tests, tooling).

## Product Surfaces (current)

The shipped CLI is intentionally small:

- `policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>]`

Legacy “profile-per-service” XPC probe commands have been removed; do not re-introduce them without an explicit design decision.

## Core ideas

- **One-way sandbox per process**: the runner applies exactly one sandbox per instance. A new specimen means a fresh runner process.
- **Witness over interpretation**: “rc == 0” is never sufficient evidence of effect; the system must record the observation that supports a claim.
- **No dishonest attribution**: permission-shaped failures must not be collapsed into “sandbox denied” unless the run includes supporting evidence.
- **Runner simplicity**: runner Swift code is meant to be inspectable and boring (avoid clever abstractions and avoid hidden pre-sandbox resource acquisition).

## Dev Workflow (fast path)

- Build: `make build` (or `./build.sh`)
  - Requires `IDENTITY` to be set to a **Developer ID Application** identity in your keychain (see `SIGNING.md`).
  - If you are in a sandboxed automation harness, signing/keychain access may fail; ask for approval/escalation and rerun.
- Run: `PolicyWitness.app/Contents/MacOS/policy-witness run tests/fixtures/pw_runner/<request>.json > result.json`

Build knobs worth knowing (debugging/iteration):

- `BUILD_XPC=0` skips building/embedding `PWRunner.xpc` + `pw-runner-client` (Rust-only iteration).
- `PW_INSPECTION=1` (default) keeps symbols/frame pointers; set `PW_INSPECTION=0` for a more optimized build.
- Evidence is generated during build by `tests/build-evidence.py` and embedded under `Contents/Resources/Evidence/`.

## Testing

- Default full run: `tests/run.sh --all`
- Smoke only: `tests/run.sh --suite smoke`
- Opt-in tests (PTY/log-sensitive/expensive) live under `tests/suites/runner_*/opt_in/` (wrappers under `tests/suites/opt_in/`) and are documented in `tests/OPT_IN_TESTS.md`.

Notes:

- Some curses tests require a TTY and will `skip` under non-interactive CI.

## Note: sandboxed automation harnesses

Some automation/agent harnesses run commands under a macOS sandbox. In that context, PolicyWitness runs can fail before any runner code executes (for example XPC lookup `NSCocoaErrorDomain=4099` / error `159` “Sandbox restriction”), and unified logging capture can be unavailable (`log: Cannot run while sandboxed`).

Treat these as environment constraints, not PolicyWitness regressions. If you see them, request escalation and rerun the same command once from an unsandboxed Terminal context to confirm behavior before debugging the project.

## Maintenance checklist (when changing things)

- If you change the specimen schema: update `runner/PWRunnerAPI.swift`, `runner/PWRunnerServiceHost.swift`, fixtures under `tests/fixtures/`, and any controller parsing assumptions.
- If you change shipped paths: update `build.sh`, `tests/build-evidence.py`, tests that locate binaries, and any docs that enumerate the bundle layout.
- If you change evidence fields: update `controller/src/main.rs`, any tests that validate output, and the docs that describe evidence channels.
