# runner/AGENTS.md

Deep contract for the runner's test machinery. The repo-root [AGENTS.md](../AGENTS.md) and [runner/README.md](README.md) orient you; this file is the reference you consult when you are actually adding a runner unit test or a new `_test_overrides` boundary.

## Swift runner unit tests (SwiftPM)

[Package.swift](Package.swift) declares a test-only SwiftPM layout: a `PWRunnerCore` library that compiles the same source set build.sh ships in `PWRunner.xpc`, plus a `PWRunnerCoreTests` executable target. The `runner_unit` suite runs `swift run --package-path runner PWRunnerCoreTests` and asserts on the stdout summary line.

SwiftPM is test-only here. Production builds still go through [build.sh](../build.sh); the SwiftPM `.build/` tree is gitignored.

**Why an executableTarget, not a testTarget.** XCTest ships with full Xcode, not Command Line Tools, and contributors frequently have only CLT. The hand-rolled [`TestKit`](Tests/PWRunnerCoreTests/TestKit.swift) harness in TestKit.swift gives us XCTest-shaped assertions (`expectEqual`, `expectThrows`, `expectContains`, etc.) without the XCTest dependency, so `swift run PWRunnerCoreTests` works against either toolchain. `PWRunnerCore` is built with `-enable-testing` so the executable can `@testable import PWRunnerCore` and reach internal symbols.

**When to add a unit test rather than an e2e suite.** Reach for `runner_unit` when:

1. The behavior is a small pure function that backs an outcome decision (e.g. the orchestrator's comparison record, `CWorker`'s sentinel-deadline math, `ValidatorClient`'s verdict-by-step-id join). A wrong branch here surfaces as the wrong `normalized_outcome` in production, with no obvious crash.
2. A required observation is unreliable from an ordinary specimen, such as a failed host kill/reap or completed publication followed by an abnormal exit. Use narrow driver controls; constructed classifier rows establish interpretation separately.
3. You're testing a failure mode of a small helper (validator partial-evidence on EOF, prediction-unavailable query exclusions) where the happy path is already covered by every passing e2e run and you want the failure paths pinned.

Don't reach for `runner_unit` when:

1. The outcome is reachable through a `_test_overrides` injection (use the e2e suite — it exercises more production code).
2. You're testing behavior that depends on the real XPC service host, launchd, or kernel sandbox. Those live in the e2e suites; the unit tests run in a plain process with no XPC.

**Adding a new unit test file.**

1. Drop a `Foo*Tests.swift` file under [Tests/PWRunnerCoreTests/](Tests/PWRunnerCoreTests/). Each file exports one function `runFooTests(_ tk: TestKit)`.
2. Inside, group related assertions with `tk.group("name") { tk.run("case") { try expect...(...) } }`.
3. Add a call to `runFooTests(tk)` in [main.swift](Tests/PWRunnerCoreTests/main.swift) with a one-line comment saying what the file pins. That registry is the inventory of what each test file covers. SwiftPM picks up the new file automatically.
4. Run with `tests/run.sh --suite runner_unit --suite runner_c_worker_harness` against a normal signed build; the catalog declares `app` for the batch, so without one the dispatcher reports the case unrun. The wrapper builds and warms the required lifecycle fixture and sets `PW_LIFECYCLE_WORKER_FIXTURE`. Direct SwiftPM runs must build `tests/fixtures/worker_lifecycle/build.sh <output>` (which also warms each fixture) and export that executable path first. Required lifecycle and deadline/reap controls fail when their equipment is absent.

**Rules for lifecycle and evidence tests.** Several test files drive the production host driver, the shared child-process observer, or the production C main with controlled faults. Which files do so is recorded in the [main.swift](Tests/PWRunnerCoreTests/main.swift) registry; the suite-level claim is the `runner_unit` row of [tests/README.md → Suite coverage](../tests/README.md#suite-coverage). Three rules apply to any such test, and each follows from "no dishonest attribution" in [AGENTS.md → Core ideas](../AGENTS.md#core-ideas):

1. The lifecycle fixture never applies a sandbox, so a test built on it cannot claim a policy cause. Constructed classifier rows establish interpretation separately. The fixture and its companion executables are built outside the inspected app, because the dispatcher fails a run whose app changed underneath it.
2. A test that injects `kill`/`waitpid` faults through the internal `ChildProcessCalls` closures owns cleanup of any fixture child it leaves unreaped. No request override selects those closures; they exist because real failure at that boundary is unreliable.
3. Controlled native-call failures (isolated substitutions in the C main, policy-write partial results, validator byte-frame and record-structure faults) are transport and lifecycle evidence, not kernel attribution.

The wrapper keeps the Swift log and rejects an internal `SKIP` or `FAIL` before crediting live cases.

**Promoting `private` symbols to `internal`.** `@testable import` reaches `internal` but not `private`. Promote a helper to `internal` (drop the `private`) when a unit test needs it; production behavior is unchanged. The few we currently expose are documented in their files' top comments.

## Testing `normalized_outcome` failure paths via `_test_overrides`

Several `normalized_outcome` values are only reachable when a specific boundary fails (`worker_spawn_failed`, `runner_timeout`, `validator_no_reply`). To exercise the real production error-handling code rather than stubbing return values, the request JSON accepts an optional `_test_overrides` block. Each honored override is mirrored back into `data.runner_result.test_overrides`, so the resulting envelope is self-describing: a reader can tell a production run (`test_overrides: null`) from a test-overridden one at a glance.

**Why request-JSON instead of env vars.** launchd spawns the XPC service host with a stripped environment; a shell-set `PW_*` does not reach the host. The request JSON is the only channel that reliably does. The worker inherits the host's process environment via `posix_spawn`, so if a future override is worker-only we can still use env vars there — but anything the host consumes belongs in the request.

**Anatomy of an override-driven test.**

1. Construct a specimen with a normal `policy` and `probe_plan` plus a `_test_overrides` block.
2. Run through the standard CLI: `policy-witness run <specimen> > out.json`. No special harness, no monkey-patched library.
3. Assert four things:
   - `data.runner_result.normalized_outcome == "<expected>"`.
   - `data.runner_result.error` mentions a real artifact of the failure (the hostile path, the syscall name, etc.). This catches "outcome string is right but came from a fake code path."
   - `data.runner_result.test_overrides.<key>` equals the value you sent. Without this, a stale build that ignores the override would pass.
   - Structural fields downstream of the failure are appropriately empty (`runner_subprocess == null` when the host short-circuits; `steps == []`; etc.).

One case is exempt from the first assertion. `witness_contract/pre_apply_failure_reports_no_policy_verdict` checks that the summary excludes `ok` and `bad_policy`, and the spellings `sandbox_apply_failed` and `runner_sandbox_denied` that no constant defines, rather than pinning one replacement outcome, because it protects the absence of library/policy claims across outcome renames; classifier tests pin the mapping separately. The assertions it retains are listed in [the suite README](../tests/suites/witness_contract/README.md#failure-before-published-application). Every other override-driven case uses the exact-outcome recipe above.

**Supported override keys** are the fields of [`PWRunnerTestOverrides`](Sources/PWRunnerCore/PWRunnerAPI.swift) in PWRunnerAPI.swift. The table of keys, with the boundary each one re-routes and the outcome it reaches, is in [README.md → Test seam](README.md#test-seam-_test_overrides). The `source_drift` suite fails when the struct and that table disagree.

A hostile value drives a real failure: a `/nonexistent/...` path makes `posix_spawn` return a real errno; a tight `worker_timeout_ms` paired with a long `worker_post_apply_hang_ms` makes the host's deadline fire before the C worker flips its `done` sentinel. The classifier in `CWorkerOrchestrator` is the same code that runs in production — only its *input* is steered.

**Adding a new override.** When you need to cover another outcome:

1. Add the optional field to `PWRunnerTestOverrides` (additive — no schema bump).
2. Add its row to the table in [README.md → Test seam](README.md#test-seam-_test_overrides). `source_drift` fails until the struct and the table agree.
3. Plumb it from `PWRunnerService.runSpecimen` into the boundary it re-routes (either host-side in `CWorkerOrchestrator` / `CWorker` / `ValidatorClient`, or worker-side via a `pw-probe-runner` argv flag). Default to the production value when unset.
4. Make sure the boundary uses the override at the place where the real OS call happens (not a wrapper that returns early on the override). The point is to *trigger* a real condition, not fake a result.
5. Mirror it back: every `PWRunnerRunResult` constructed on the affected code path should pass `test_overrides: parsed._test_overrides` so the audit signal survives.
6. Add a `tests/suites/runner_outcome_<name>/run.sh` suite that follows the four assertions above.
7. Register its cases and default membership in [tests/catalog.json](../tests/catalog.json), the suite-coverage table in [tests/README.md](../tests/README.md), and (for a new outcome) the matrix in [tests/COVERAGE.md](../tests/COVERAGE.md).

**What overrides should not do.** Don't add an override that fakes a *result* (e.g. `force_normalized_outcome: "x"`). That short-circuits the very code we're trying to verify. If a code path can't be reached by re-routing a boundary, cover it with a Swift unit test against the classifier directly instead.

**Auditing override usage.** `jq '.data.runner_result.test_overrides' run.json` returns `null` for every production run. Any run whose envelope reports a non-null `test_overrides` has been steered; treat its outcome as evidence about the classifier/error-handling path, not about the specimen's policy.
