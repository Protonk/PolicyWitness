# AGENTS.md

This file is for people and agents working in this repo: where to make changes, what contracts exist, and what to open first when something breaks.

## Quick Router

Pick what you’re changing:

- **User-facing workflows** → `PolicyWitness.md` (note: this document will be rewritten for the specimen-first product; treat legacy sections as stale)
- **CLI behavior contract** → `runner/README.md`
- **Runner XPC architecture** → `xpc/README.md`
- **Build/sign/notarize** → `SIGNING.md` then `build.sh`
- **Tests** → `tests/README.md` then `tests/run.sh --all`
- **Lab tooling (TUI, fixtures)** → `laboratory/README.md`

## Repo Layout (mental model)

This repo is intentionally multi-language:

- `runner/` (Rust): builds the shipped CLI `PolicyWitness.app/Contents/MacOS/policy-witness`
  - Owns: specimen orchestration, run directories, evidence capture wrappers.
- `xpc/` (Swift): builds the shipped runner service and its client
  - Owns: `PWRunner` protocol, self-sandboxing runner implementation.
- `tools/` (Python): development tooling for viewing run directories (TUI, signpost timeline renderers).
- `tests/` (bash + python): suite runners and fixtures.
- `build.sh` (bash): builds `PolicyWitness.app`, generates Evidence, codesigns, zips.

## App Bundle Layout (contract)

`PolicyWitness.app` ships as a single specimen with a small, stable layout:

- `PolicyWitness.app/Contents/MacOS/policy-witness` (Rust controller)
- `PolicyWitness.app/Contents/MacOS/pw-runner-client` (Swift NSXPC client)
- `PolicyWitness.app/Contents/MacOS/sandbox-log-observer` (Rust unified-log deny capture helper)
- `PolicyWitness.app/Contents/MacOS/signpost-log-observer` (Rust signpost capture helper)
- `PolicyWitness.app/Contents/XPCServices/PWRunner.xpc` (Swift runner; applies sandbox per specimen; exits after one request)
- `PolicyWitness.app/Contents/Resources/Evidence/manifest.json` (hash/entitlements inventory)
- `PolicyWitness.app/Contents/Resources/Evidence/symbols.json` (exported `_pw_*` markers; best-effort)

If you change names/paths here, expect downstream breakage (build script, evidence generation, tests).

## Core Invariants (treat these as contracts)

- **Specimen-first**: sandbox variation is driven by SBPL / compiled profile bytes + a probe plan, not by “one XPC service per entitlement set”.
- **One-way sandbox**: the runner applies exactly one sandbox per process instance; a new specimen means a new runner instance.
- **No arbitrary path exec surface**: the controller does not provide “execute arbitrary Mach-O by path” features.
- **Evidence discipline**: permission-shaped failures are not automatically attributed to “sandbox denied” without supporting evidence.

## Build + Signing (how it ships)

Preferred entrypoints:

- `make build` → runs `./build.sh`
- `make test` → runs `tests/run.sh --all`

Build facts:

- `build.sh` requires `IDENTITY` to be set to a Developer ID Application identity present in your keychain.
- `BUILD_XPC=0` skips building/embedding `PWRunner.xpc` and `pw-runner-client` (useful when iterating only on Rust).
- `PW_INSPECTION=1` (default) keeps symbols/frame pointers; set `PW_INSPECTION=0` for a more optimized build.
- Evidence is generated during build by `tests/build-evidence.py` and embedded under `Contents/Resources/Evidence/`.

## Agent Note: sandboxed harnesses (“nested sandbox”)

Some development harnesses run tools inside an OS sandbox. In those environments:

- XPC lookup can fail early with `NSCocoaErrorDomain` 4099 / error 159 `"Sandbox restriction"` (before the service launches).
- Unified Logging access can also be restricted, making deny-evidence capture impossible from inside the harness.

This is an environment constraint, not a normal developer environment issue.

- Preflight: run `PolicyWitness.app/Contents/MacOS/policy-witness inside --bare` before specimen runs. If it prints `true`, ask for approval/escalation and re-run the task once outside the harness sandbox to confirm behavior.
