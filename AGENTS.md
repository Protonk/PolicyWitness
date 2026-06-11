# AGENTS.md

This file is for contributors and agents.

PolicyWitness is a sandbox witness harness. Each run is driven by a specimen — an SBPL policy plus a probe plan — handed to a fresh `PWRunner.xpc` instance. The XPC host stays unsandboxed; it spawns two short-lived children per specimen (`pw-probe-runner` for sandboxed attempts and `sb_api_validator --batch` for `sandbox_check` verdicts), joins their outputs into one JSON envelope, replies, and exits.

## Quick Router (open first)

Pick what you’re changing:

- **CLI behavior / JSON contract** → `controller/README.md`, `controller/src/main.rs`
- **Runner service (self-sandboxing witness)** → `runner/README.md`, `runner/Services/PWRunner/`
- **Runner test machinery (unit tests, `_test_overrides`)** → `runner/AGENTS.md`
- **Runner API types** → `runner/Sources/PWRunnerCore/PWRunnerAPI.swift`
- **Runner client (NSXPCConnection wrapper)** → `runner/Clients/PWRunnerClient/`
- **Build + signing** → `build.sh`, `SIGNING.md`
- **Evidence generation / manifests** → `tests/build-evidence.py`
- **Tests** → `tests/README.md`, `tests/run.sh --all`
- **Opt-in tests registry** → `tests/OPT_IN_TESTS.md`
- **User guide** → `PolicyWitness.md`

## Vocabulary (repo-anchored)

- **Specimen**: the unit of input for a run — policy (SBPL + params) plus a probe plan.
- **Controller**: the host-side orchestrator (`dist/PolicyWitness.app/Contents/MacOS/policy-witness`) that drives the runner and prints a JSON envelope.
- **Runner**: the ephemeral XPC service (`dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc`) described in the intro above. All processes are single-use per specimen.
- **Probe step**: a `sandbox_check` query paired with an attempted operation (`file` or `mach_lookup`).

## What Ships (bundle layout contract)

The `.app` layout is a contract: tests and evidence generation assume these paths.

- `dist/PolicyWitness.app/Contents/MacOS/policy-witness` (Rust controller / orchestrator)
- `dist/PolicyWitness.app/Contents/MacOS/pw-runner-client` (Swift client that talks to `PWRunner.xpc`)
- `dist/PolicyWitness.app/Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper for sandbox denials)
- `dist/PolicyWitness.app/Contents/MacOS/sb_api_validator` (diagnostic copy of the validator CLI; production traffic uses the bundle-local copy below)
- `dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc` (Swift XPC host; one host + two short-lived children per specimen)
  - `…/PWRunner.xpc/Contents/MacOS/pw-probe-runner` (C worker helper embedded bundle-locally — the runner host resolves it relative to its own bundle so built-in and BYOXPC runners both pick up the correct copy)
  - `…/PWRunner.xpc/Contents/MacOS/sb_api_validator` (sandbox_check batch validator, also bundle-local for BYOXPC parity)
- `dist/PolicyWitness.app/Contents/Resources/Evidence/manifest.json` (embedded inventory: hashes + signing/entitlements metadata)
- `dist/PolicyWitness.app/Contents/Resources/Evidence/symbols.json` (best-effort marker inventory)

If you rename/move anything here, expect downstream breakage (build script, evidence, tests, tooling).

## Product Surfaces

The shipped CLI is intentionally small:

- `policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--no-log-capture]`

## Documentation

Describe current behavior. Don't add change-history notes to docs — `git log` is authoritative.

## Core ideas

- **One-way sandbox per process**: the worker applies exactly one sandbox to itself and exits. A new specimen means a fresh XPC host plus a fresh worker.
- **Host/worker split**: the XPC host never applies the specimen policy. That keeps the reply path alive under arbitrary `(deny default)` profiles and makes worker exit status (signal vs clean exit, partial vs full report) the source of truth for `runner_subprocess` + `normalized_outcome`.
- **Witness over interpretation**: “rc == 0” is never sufficient evidence of effect; the system must record the observation that supports a claim.
- **No dishonest attribution**: permission-shaped failures must not be collapsed into “sandbox denied” unless the run includes supporting evidence.
- **Runner simplicity**: runner code is meant to be inspectable and boring (avoid clever abstractions and avoid hidden pre-sandbox resource acquisition). Host-side orchestration belongs in `PWRunnerService.swift` and `CWorkerOrchestrator.swift`; post-apply work belongs in `pw-probe-runner` (the C worker).

## Dev Workflow (fast path)

- Build: `make build` (or `./build.sh`)
  - Requires `IDENTITY` to be set to a **Developer ID Application** identity in your keychain (see `SIGNING.md`).
  - If you are in a sandboxed automation harness, signing/keychain access may fail; ask for approval/escalation and rerun.
- If you add a helper under the app or XPC bundle `Contents/MacOS`, update the `build.sh` signing list; notarization fails if any embedded tool is left ad hoc-signed.
- Run: `dist/PolicyWitness.app/Contents/MacOS/policy-witness run tests/fixtures/pw_runner/<request>.json > result.json`

Build knobs worth knowing (debugging/iteration):

- `BUILD_XPC=0` skips building/embedding `PWRunner.xpc` + `pw-runner-client` (Rust-only iteration).
- `PW_INSPECTION=1` (default) keeps symbols/frame pointers; set `PW_INSPECTION=0` for a more optimized build.
- Evidence is generated during build by `tests/build-evidence.py` and embedded under `Contents/Resources/Evidence/`.

## External runner workflow (agents)

Use this when you are asked to install, verify, or clean up BYOXPC runners.

The `runner` subcommands (install/list/status/verify/remove/validate) and the manual launchctl/plist cleanup recipes for both user and system scope live in `controller/README.md` and `PolicyWitness.md`. Agent-specific guidance:

- Inspect first: `policy-witness runner list` and note `service_name`, `scope`, and `bundle_path` before acting.
- User-scope installs require a logged-in GUI session; sandboxed harnesses may block launchctl/log capture, so request escalation if needed.

## Testing

- Default full run: `tests/run.sh --all`
- Smoke only: `tests/run.sh --suite smoke`
- Opt-in tests (PTY/log-sensitive/expensive) live under `tests/suites/runner_*/opt_in/` (wrappers under `tests/suites/opt_in/`) and are documented in `tests/OPT_IN_TESTS.md`.

Notes:

- Some curses tests require a TTY and will `skip` under non-interactive CI.

### Runner test machinery (deep contract)

Two runner-specific testing contracts live in `runner/AGENTS.md`: the **Swift runner unit tests (SwiftPM)** layout (when to add a `runner_unit` test vs an e2e suite, stubbing `@convention(c)` pointers, adding a test file) and **`normalized_outcome` failure paths via `_test_overrides`** (the four-assertion recipe, the supported override keys, and the rules for adding a new override). Read that file before touching either.

## Note: sandboxed automation harnesses

Some automation/agent harnesses run commands under a macOS sandbox. In that context, PolicyWitness runs can fail before any runner code executes (for example XPC lookup `NSCocoaErrorDomain=4099` / error `159` “Sandbox restriction”), and unified logging capture can be unavailable (`log: Cannot run while sandboxed`).

Treat these as environment constraints, not PolicyWitness regressions. If you see them, request escalation and rerun the same command once from an unsandboxed Terminal context to confirm behavior before debugging the project.

## Maintenance checklist (when changing things)

- If you change the specimen schema: update `runner/Sources/PWRunnerCore/PWRunnerAPI.swift`, `runner/Sources/PWRunnerCore/PWRunnerService.swift`, the worker plumbing (`runner/Sources/PWRunnerCore/CWorker.swift`, `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift`, `runner/Sources/PWRunnerCore/ValidatorClient.swift`, plus `pw-probe-runner` and `sb_api_validator` if the C side is affected), fixtures under `tests/fixtures/`, and any controller parsing assumptions.
- If you change shipped paths: update `build.sh`, `tests/build-evidence.py`, tests that locate binaries, and any docs that enumerate the bundle layout.
- If you change evidence fields: update `controller/src/main.rs`, any tests that validate output, and the docs that describe evidence channels.
