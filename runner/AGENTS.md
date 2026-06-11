# runner/AGENTS.md

Deep contract for the runner's test machinery. The repo-root `AGENTS.md` and `runner/README.md` orient you; this file is the reference you consult when you are actually adding a runner unit test or a new `_test_overrides` boundary.

## Swift runner unit tests (SwiftPM)

`runner/Package.swift` declares a test-only SwiftPM layout: a `PWRunnerCore` library that compiles the same source set build.sh ships in `PWRunner.xpc`, plus a `PWRunnerCoreTests` executable target. The `runner_unit` suite runs `swift run --package-path runner PWRunnerCoreTests` and asserts on the stdout summary line.

SwiftPM is test-only here. Production builds still go through `build.sh`; the SwiftPM `.build/` tree is gitignored.

**Why an executableTarget, not a testTarget.** XCTest ships with full Xcode, not Command Line Tools, and contributors frequently have only CLT. The hand-rolled `TestKit` harness in `runner/Tests/PWRunnerCoreTests/TestKit.swift` gives us XCTest-shaped assertions (`expectEqual`, `expectThrows`, `expectContains`, etc.) without the XCTest dependency, so `swift run PWRunnerCoreTests` works against either toolchain. `PWRunnerCore` is built with `-enable-testing` so the executable can `@testable import PWRunnerCore` and reach internal symbols.

**When to add a unit test rather than an e2e suite.** Reach for `runner_unit` when:

1. The behavior is a small pure function that backs an outcome decision (e.g. the orchestrator's drift computation, `CWorker`'s sentinel-deadline math, `ValidatorClient`'s verdict-by-step-id join). A wrong branch here surfaces as the wrong `normalized_outcome` in production, with no obvious crash.
2. The outcome is unreachable from a real specimen because something upstream short-circuits it or the worker survives the condition (`runner_sandbox_denied` needs a fatal signal the minimal-surface worker rarely takes under `(deny default)`; `runner_failed` requires an intermediate failure no fixture can produce).
3. You're testing a failure mode of a small helper (validator partial-evidence on EOF, prediction-unavailable host-mirror agreement) where the happy path is already covered by every passing e2e run and you want the failure paths pinned.

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

## Testing `normalized_outcome` failure paths via `_test_overrides`

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

**Supported override keys** (defined in `runner/Sources/PWRunnerCore/PWRunnerAPI.swift::PWRunnerTestOverrides`):

| Key | Type | Boundary it re-routes | Outcome it lets you reach |
| --- | --- | --- | --- |
| `libsandbox_path` | string | `SandboxLib.load(path:)` → `dlopen(path)` in the host's pre-spawn check | `libsandbox_unavailable` |
| `worker_executable_path` | string | `posix_spawn(path, ...)` inside `CWorker.spawn` (pw-probe-runner) | `worker_spawn_failed` |
| `worker_timeout_ms` | integer (ms, floored at 50) | Host-side sentinel deadline in `CWorker.run` | `runner_timeout` |
| `validator_executable_path` | string | `posix_spawn(path, ...)` inside `ValidatorClient.runValidator` (C-worker code path) | `validator_spawn_failed` |
| `worker_post_apply_hang_ms` | integer (ms, 0..60000) | Passed as `--post-apply-hang-ms` to `pw-probe-runner`; the C worker `nanosleep`s for N ms after slot results are durable but before flipping `done`, pushing the host past its sentinel deadline | `runner_timeout` |
| `worker_post_apply_kill_signal` | integer (signal, 0..31) | Passed as `--post-apply-kill-signal` to `pw-probe-runner`; the C worker `kill(getpid(), N)`s itself after `applied` but before `done`, so the host sees a foreign termination signal with `done` unset — the same shape a real kernel sandbox kill produces | `runner_sandbox_denied` |
| `worker_pre_ready_hang_ms` | integer (ms, 0..60000) | Passed as `--pre-ready-hang-ms` to `pw-probe-runner`; the C worker `nanosleep`s for N ms *before* the pre-apply ready byte, modelling a slow `sandbox_compile_string` that overruns the host's `readyByteTimeout` so the ready write lands on a host-closed pipe. Pins that the worker survives that (SIGPIPE is ignored) and still reaches `sandbox_apply` | `ok` (resilience, not a failure outcome — see `runner_ready_byte_resilience`) |

A hostile value drives a real failure: a `/nonexistent/...` path makes `posix_spawn` return a real errno; a tight `worker_timeout_ms` paired with a long `worker_post_apply_hang_ms` makes the host's deadline fire before the C worker flips its `done` sentinel. The classifier in `CWorkerOrchestrator` is the same code that runs in production — only its *input* is steered.

**Adding a new override.** When you need to cover another outcome:

1. Add the optional field to `PWRunnerTestOverrides` (additive — no schema bump).
2. Plumb it from `PWRunnerService.runSpecimen` into the boundary it re-routes (either host-side in `CWorkerOrchestrator` / `CWorker` / `ValidatorClient`, or worker-side via a `pw-probe-runner` argv flag). Default to the production value when unset.
3. Make sure the boundary uses the override at the place where the real OS call happens (not a wrapper that returns early on the override). The point is to *trigger* a real condition, not fake a result.
4. Mirror it back: every `PWRunnerRunResult` constructed on the affected code path should pass `test_overrides: parsed._test_overrides` so the audit signal survives.
5. Add a `tests/suites/runner_outcome_<name>/run.sh` suite that follows the four assertions above.
6. Register the suite in `tests/run.sh` (default list + usage line), the suite-coverage table in `tests/README.md`, and (for a new outcome) the matrix in `tests/COVERAGE.md`.

**What overrides should not do.** Don't add an override that fakes a *result* (e.g. `force_normalized_outcome: "x"`). That short-circuits the very code we're trying to verify. If a code path can't be reached by re-routing a boundary, cover it with a Swift unit test against the classifier directly instead.

**Auditing override usage.** `jq '.data.runner_result.test_overrides' run.json` returns `null` for every production run. Any run whose envelope reports a non-null `test_overrides` has been steered; treat its outcome as evidence about the classifier/error-handling path, not about the specimen's policy.
