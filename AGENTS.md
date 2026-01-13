# AGENTS.md

This file is for contributors and agents.

PolicyWitness is a sandbox runner instrumentation harness. Variation is supplied at runtime as SBPL / compiled profile bytes plus a probe plan. A single ephemeral XPC runner (`PWRunner.xpc`) self-applies the sandbox per specimen, executes the plan, and exits.

## Quick Router (open first)

Pick what you’re changing:

- **CLI behavior / JSON contract / labbook writer** → `controller/README.md`, `controller/src/main.rs`
- **Runner service (self-sandboxing witness)** → `runner/README.md`, `runner/services/PWRunner/`
- **Runner API types** → `runner/PWRunnerAPI.swift`
- **Runner client (NSXPCConnection wrapper)** → `runner/runner-client/`
- **Build + signing** → `build.sh`, `SIGNING.md`
- **Evidence generation / manifests** → `tests/build-evidence.py`
- **Tests** → `tests/README.md`, `tests/run.sh --all`
- **Opt-in tests registry** → `tests/OPT_IN_TESTS.md`
- **Lab tooling (viewer/TUI)** → `laboratory/README.md`, `laboratory/pw-lab`
- **User guide** → `PolicyWitness.md`

## What Ships (bundle layout contract)

The `.app` layout is a contract: tests and evidence generation assume these paths.

- `PolicyWitness.app/Contents/MacOS/policy-witness` (Rust controller / orchestrator)
- `PolicyWitness.app/Contents/MacOS/pw-runner-client` (Swift client that talks to `PWRunner.xpc`)
- `PolicyWitness.app/Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper for sandbox denials)
- `PolicyWitness.app/Contents/MacOS/signpost-log-observer` (Rust signpost capture helper)
- `PolicyWitness.app/Contents/XPCServices/PWRunner.xpc` (Swift runner; one specimen per instance)
- `PolicyWitness.app/Contents/Resources/Evidence/manifest.json` (embedded inventory: hashes + signing/entitlements metadata)
- `PolicyWitness.app/Contents/Resources/Evidence/symbols.json` (best-effort marker inventory)

If you rename/move anything here, expect downstream breakage (build script, evidence, tests, tooling).

## Product Surfaces (current)

The shipped CLI is intentionally small:

- `policy-witness inside [--service-name <name> ...] [--bare]`
- `policy-witness specimen <specimen.json> [--outdir <dir>] [--timeout-ms <n>] [--log-last <dur>] [--force]`

Legacy “profile-per-service” XPC probe commands have been removed; do not re-introduce them without an explicit design decision.

## Core ideas

- **One-way sandbox per process**: the runner applies exactly one sandbox per instance. A new specimen means a fresh runner process.
- **Witness over interpretation**: “rc == 0” is never sufficient evidence of effect; the system must record the observation that supports a claim.
- **No dishonest attribution**: permission-shaped failures must not be collapsed into “sandbox denied” unless the run includes supporting evidence.
- **Runner simplicity**: runner Swift code is meant to be inspectable and boring (avoid clever abstractions and avoid hidden pre-sandbox resource acquisition).
- **Labbook summary is canonical**: `lab_summary.json` is the stable “overview” surface for a run directory; other files are raw or derived views.

## Specimen + Labbook (what gets written)

`policy-witness specimen` writes a run directory (default under `.pw_lab/out/…`) containing:

- `specimen.json` (copy of input specimen)
- `canonical.request.json` / `instrumented.request.json` (what was sent to the runner)
- `canonical/` and `instrumented/` subdirectories containing `run.json` and raw stdout/stderr
- `canonical_sandbox_logs.json` / `instrumented_sandbox_logs.json` (best-effort deny capture)
- `inside.json` (preflight result)
- `lab_summary.json` (the primary summary surface the lab tooling consumes)

The specimen file format is documented by example under `tests/fixtures/pw_runner/`.

## Dev Workflow (fast path)

- Build: `make build` (or `./build.sh`)
  - Requires `IDENTITY` to be set to a **Developer ID Application** identity in your keychain (see `SIGNING.md`).
  - If you are in a sandboxed automation harness, signing/keychain access may fail; ask for approval/escalation and rerun.
- Run: `PolicyWitness.app/Contents/MacOS/policy-witness specimen tests/fixtures/pw_runner/<specimen>.json --force`
- View: `laboratory/pw-lab tui <run_dir>`
- Inspect/diff: `laboratory/pw-lab inspect --json <run_dir>` and `laboratory/pw-lab diff <run_a> <run_b>`

Build knobs worth knowing (debugging/iteration):

- `BUILD_XPC=0` skips building/embedding `PWRunner.xpc` + `pw-runner-client` (Rust-only iteration).
- `PW_INSPECTION=1` (default) keeps symbols/frame pointers; set `PW_INSPECTION=0` for a more optimized build.
- Evidence is generated during build by `tests/build-evidence.py` and embedded under `Contents/Resources/Evidence/`.

## Testing

- Default full run: `tests/run.sh --all`
- Smoke only: `tests/run.sh --suite smoke`
- Opt-in tests (PTY/log-sensitive/expensive) live under `tests/suites/opt_in/` and are documented in `tests/OPT_IN_TESTS.md`.

Notes:

- Some curses tests require a TTY and will `skip` under non-interactive CI.
- Some runs will be blocked inside sandboxed automation harnesses (see next section).

## Agent Note: “inside” (sandboxed harness / nested sandbox)

Some automation harnesses run commands inside an OS sandbox. In those environments:

- XPC lookup can fail early with `NSCocoaErrorDomain` 4099 / error 159 `"Sandbox restriction"` (before the runner launches).
- Unified Logging access can be restricted, making deny-evidence capture unavailable from the harness.

This is an environment constraint, not a normal developer environment issue.

Always preflight with:

```sh
PolicyWitness.app/Contents/MacOS/policy-witness inside --bare
```

If it prints `true`, **ask for approval/escalation and re-run the task once** outside the harness sandbox to confirm behavior before debugging PolicyWitness itself.

Advanced (agent/dev-only) override:

- `PW_LAB_ALLOW_INSIDE=1` disables the `specimen` command’s “inside” guardrail. Use only to confirm the harness constraint (expect missing/blocked evidence).
