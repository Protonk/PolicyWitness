# AGENTS.md

This file is for contributors and agents.

PolicyWitness is a sandbox runner instrumentation harness. Each run is driven by a specimen — an SBPL policy plus a probe plan — which is handed to a fresh `PWRunner.xpc` instance. The XPC host stays unsandboxed; it spawns a short-lived worker process that applies the specimen policy to itself, executes the probe plan, returns a JSON report, and exits. The host then replies via XPC and exits too.

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
- **Controller**: the host-side orchestrator (`dist/PolicyWitness.app/Contents/MacOS/policy-witness`) that drives the runner and prints a JSON envelope.
- **Runner**: the ephemeral XPC service (`dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc`). The XPC host validates the request, spawns two short-lived children (`pw-probe-runner` for sandboxed attempts + `sb_api_validator --batch` for `sandbox_check` verdicts), joins their outputs into one JSON envelope, and replies. All processes are single-use per specimen.
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

- `policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>]`

Profile-per-service XPC probe commands are not part of the CLI; do not re-introduce them without an explicit design decision.

## Documentation

Documentation should be stateless: describe current behavior without historical change notes. Reserve history for `README.md` only.

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

- Inspect first: `policy-witness runner list` and note `service_name`, `scope`, and `bundle_path`.
- BYOXPC service names are fixed to `CFBundleIdentifier` (no override); update by replacing the bundle and reinstalling.
- Cleanup: `policy-witness runner remove --id ...` (user scope) or use `sudo launchctl bootout system/<service>` + delete `/Library/LaunchDaemons/<service>.plist` + `runner remove --skip-bootout` for system scope.
- Launchd files: `~/Library/LaunchAgents/<service>.plist` (user) and `/Library/LaunchDaemons/<service>.plist` (system).
- Install/verify debugging: `launchctl print "gui/$(id -u)/<service>"` or `launchctl print system/<service>`; check `XPC_SERVICE_PATH` in the plist's `EnvironmentVariables`.
- User scope installs require a logged-in GUI session; sandboxed harnesses may block launchctl/log capture, so request escalation if needed.

## Testing

- Default full run: `tests/run.sh --all`
- Smoke only: `tests/run.sh --suite smoke`
- Opt-in tests (PTY/log-sensitive/expensive) live under `tests/suites/runner_*/opt_in/` (wrappers under `tests/suites/opt_in/`) and are documented in `tests/OPT_IN_TESTS.md`.

Notes:

- Some curses tests require a TTY and will `skip` under non-interactive CI.

### Swift runner unit tests (SwiftPM)

`runner/Package.swift` declares a test-only SwiftPM layout: a `PWRunnerCore` library that compiles the same source set build.sh ships in `PWRunner.xpc`, plus a `PWRunnerCoreTests` executable target. The `runner_unit` suite runs `swift run --package-path runner PWRunnerCoreTests` and asserts on the stdout summary line.

SwiftPM is test-only here. Production builds still go through `build.sh`; the SwiftPM `.build/` tree is gitignored.

**Why an executableTarget, not a testTarget.** XCTest ships with full Xcode, not Command Line Tools, and contributors frequently have only CLT. The hand-rolled `TestKit` harness in `runner/Tests/PWRunnerCoreTests/TestKit.swift` gives us XCTest-shaped assertions (`expectEqual`, `expectThrows`, `expectContains`, etc.) without the XCTest dependency, so `swift run PWRunnerCoreTests` works against either toolchain. `PWRunnerCore` is built with `-enable-testing` so the executable can `@testable import PWRunnerCore` and reach internal symbols.

**When to add a unit test rather than an e2e suite.** Reach for `runner_unit` when:

1. The behavior is a small pure function that backs an outcome decision (e.g. `classifyWorkerResult`, `effectiveWorkerTimeoutSeconds`, `partialStepOutput`, BSD wait-status decoders). A wrong branch here surfaces as the wrong `normalized_outcome` in production, with no obvious crash.
2. The outcome is unreachable from a real specimen because something upstream short-circuits it (`sandbox_apply_failed` is hidden behind controller-side preflight; `runner_failed` requires an intermediate failure no fixture can produce).
3. You're testing a failure mode of a small helper (frame truncation, oversized prefix, EOF before any bytes) where the happy path is already covered by every passing e2e run and you want the failure paths pinned.

Don't reach for `runner_unit` when:

1. The outcome is reachable through a `_test_overrides` injection (use the e2e suite — it exercises more production code).
2. You're testing behavior that depends on the real XPC service host, launchd, or kernel sandbox. Those live in the e2e suites; the unit tests run in a plain process with no XPC.

**Adding a new unit test file.**

1. Drop a `Foo*Tests.swift` file under `runner/Tests/PWRunnerCoreTests/`. Each file exports one function `runFooTests(_ tk: TestKit)`.
2. Inside, group related assertions with `tk.group("name") { tk.run("case") { try expect...(...) } }`.
3. Add a call to `runFooTests(tk)` in `runner/Tests/PWRunnerCoreTests/main.swift`. SwiftPM picks up the new file automatically.
4. Run locally with `swift run --package-path runner PWRunnerCoreTests` or `tests/run.sh --suite runner_unit`.

**Stubbing C function pointers.** `SandboxLib`'s function-pointer slots are `@convention(c)`, which forbids closure capture. To observe side effects (call counts, freed-pointer lists) from a stub, route through file-scope `private var`s and reset them at the top of any test that uses them. `SandboxApplyTests.swift` is the worked example.

**Promoting `private` symbols to `internal`.** `@testable import` reaches `internal` but not `private`. Promote a helper to `internal` (drop the `private`) when a unit test needs it; production behavior is unchanged. The few we currently expose are documented in their files' top comments.

### Testing `normalized_outcome` failure paths via `_test_overrides`

Several `normalized_outcome` values are only reachable when a specific boundary fails (`libsandbox_unavailable`, `worker_spawn_failed`, `runner_timeout`). To exercise the real production error-handling code rather than stubbing return values, the request JSON accepts an optional `_test_overrides` block. Each honored override is mirrored back into `data.runner_result.test_overrides`, so the resulting envelope is self-describing: a reader can tell a production run (`test_overrides: null`) from a test-overridden one at a glance.

**Why request-JSON instead of env vars.** launchd spawns the XPC service host with a stripped environment; a shell-set `PW_*` does not reach the host. The request JSON is the only channel that reliably does. The worker inherits the host's process environment via `posix_spawn`, so if a future override is worker-only we can still use env vars there — but anything the host consumes belongs in the request.

**Anatomy of an override-driven test.**

1. Construct a specimen with a normal `policy` and `probe_plan` plus a `_test_overrides` block.
2. Run through the standard CLI: `policy-witness run <specimen> > out.json`. No special harness, no monkey-patched library.
3. Assert four things:
   - `data.runner_result.normalized_outcome == "<expected>"`.
   - `data.runner_result.error` mentions a real artifact of the failure (the hostile path, the syscall name, etc.). This catches "outcome string is right but came from a fake code path."
   - `data.runner_result.test_overrides.<key>` equals the value you sent. Without this, a stale build that ignores the override would pass.
   - Structural fields downstream of the failure are appropriately empty (`runner_subprocess == null` when the host short-circuits; `steps == []`; etc.).

**Supported override keys** (defined in `runner/PWRunnerAPI.swift::PWRunnerTestOverrides`):

| Key | Type | Boundary it re-routes | Outcome it lets you reach |
| --- | --- | --- | --- |
| `libsandbox_path` | string | `SandboxLib.load(path:)` → `dlopen(path)` (host first, then worker on the same value) | `libsandbox_unavailable` |
| `worker_executable_path` | string | `posix_spawn(path, ...)` inside `CWorker.spawn` (pw-probe-runner) | `worker_spawn_failed` |
| `worker_timeout_ms` | integer (ms, floored at 50) | Host-side sentinel deadline in `CWorker.run` | `runner_timeout` |
| `validator_executable_path` | string | `posix_spawn(path, ...)` inside `ValidatorClient.runValidator` (C-worker code path) | `validator_spawn_failed` |
| `worker_post_apply_hang_ms` | integer (ms, 0..60000) | Passed as `--post-apply-hang-ms` to `pw-probe-runner`; the C worker `nanosleep`s for N ms after slot results are durable but before flipping `done`, pushing the host past its sentinel deadline | `runner_timeout` |

A hostile value drives a real failure: a `/nonexistent/...` path makes `posix_spawn` return a real errno; a tight `worker_timeout_ms` paired with a long `worker_post_apply_hang_ms` makes the host's deadline fire before the C worker flips its `done` sentinel. The classifier in `CWorkerOrchestrator` is the same code that runs in production — only its *input* is steered.

**Adding a new override.** When you need to cover another outcome:

1. Add the optional field to `PWRunnerTestOverrides` (additive — no schema bump).
2. Plumb it from `PWRunnerService.runSpecimen` into the boundary it re-routes (either host-side in `CWorkerOrchestrator` / `CWorker` / `ValidatorClient`, or worker-side via a `pw-probe-runner` argv flag). Default to the production value when unset.
3. Make sure the boundary uses the override at the place where the real OS call happens (not a wrapper that returns early on the override). The point is to *trigger* a real condition, not fake a result.
4. Mirror it back: every `PWRunnerRunResult` constructed on the affected code path should pass `test_overrides: parsed._test_overrides` so the audit signal survives.
5. Add a `tests/suites/runner_outcome_<name>/run.sh` suite that follows the four assertions above.
6. Register the suite in `tests/run.sh` (default list + usage line) and `tests/INDEX.md`.

**What overrides should not do.** Don't add an override that fakes a *result* (e.g. `force_normalized_outcome: "x"`). That short-circuits the very code we're trying to verify. If a code path can't be reached by re-routing a boundary, cover it with a Swift unit test against the classifier directly instead.

**Auditing override usage.** `jq '.data.runner_result.test_overrides' run.json` returns `null` for every production run. Any run whose envelope reports a non-null `test_overrides` has been steered; treat its outcome as evidence about the classifier/error-handling path, not about the specimen's policy.

## Note: sandboxed automation harnesses

Some automation/agent harnesses run commands under a macOS sandbox. In that context, PolicyWitness runs can fail before any runner code executes (for example XPC lookup `NSCocoaErrorDomain=4099` / error `159` “Sandbox restriction”), and unified logging capture can be unavailable (`log: Cannot run while sandboxed`).

Treat these as environment constraints, not PolicyWitness regressions. If you see them, request escalation and rerun the same command once from an unsandboxed Terminal context to confirm behavior before debugging the project.

## Maintenance checklist (when changing things)

- If you change the specimen schema: update `runner/PWRunnerAPI.swift`, `runner/PWRunnerService.swift`, the worker plumbing (`runner/CWorker.swift`, `runner/CWorkerOrchestrator.swift`, `runner/ValidatorClient.swift`, plus `pw-probe-runner` and `sb_api_validator` if the C side is affected), fixtures under `tests/fixtures/`, and any controller parsing assumptions.
- If you change shipped paths: update `build.sh`, `tests/build-evidence.py`, tests that locate binaries, and any docs that enumerate the bundle layout.
- If you change evidence fields: update `controller/src/main.rs`, any tests that validate output, and the docs that describe evidence channels.
