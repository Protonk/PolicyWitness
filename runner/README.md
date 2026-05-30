# `runner/` (Swift runner: specimen-first sandbox witness)

This directory contains the Swift implementation of the **ephemeral sandbox runner** shipped inside `dist/PolicyWitness.app`.

PolicyWitness is **specimen-first**:

- The controller (`policy-witness`) starts a fresh XPC runner instance per specimen.
- The runner XPC host starts unsandboxed, spawns a short-lived worker, and the
  worker applies the requested seatbelt profile exactly once (SBPL source +
  parameters), executes the probe plan, returns JSON to the host, and exits.
- The host never applies the specimen policy, so default-deny policies cannot
  block the XPC reply path.

## Key files

- `runner/PWRunnerAPI.swift`
  - `PWRunnerProtocol` (`runSpecimen(Data) -> Data`)
  - Codable JSON types: `PWRunnerRunSpec`, `PWRunnerPolicySpec`, `PWRunnerProbeStep`, and the returned `PWRunnerRunResult`
- `runner/SandboxLib.swift`
  - Explicit `dlopen` + `dlsym` bindings for libsandbox.
  - `SandboxLib.load(path:)` defaults to `/usr/lib/libsandbox.dylib`;
    re-routed by `_test_overrides.libsandbox_path` (see "Test seam"
    below).
- `runner/SandboxApply.swift`
  - Policy hashing and single-shot `sandbox_apply` path.
- `runner/ProbeRunner.swift`
  - `sandbox_check` and probe attempts (file + mach-lookup).
- `runner/PathUtils.swift`
  - Path normalization and fd-based observation helpers.
- `runner/Signals.swift`
  - Deny-signal handler and counters.
- `runner/CWorker.swift`
  - Host-side driver for `pw-probe-runner`: shm_open + mmap + posix_spawn,
    sentinel polling, and the post-apply hook.
- `runner/ValidatorClient.swift`
  - Host-side driver for `sb_api_validator --batch`: concurrent
    stdin/stdout via `poll()` to avoid pipe deadlock, partial-evidence
    failure result.
- `runner/CWorkerOrchestrator.swift`
  - Joins the C worker and the validator child into a single
    `PWRunnerRunResult`. Owns probe-plan validation,
    `prediction_unavailable` host mirror, classification, and drift.
- `runner/PWRunnerService.swift`
  - Orchestrates the host flow (decode → validate → drive C worker +
    validator → reply).
  - The host enforces caller authorization, loads libsandbox once to fail
    fast on missing dynamic loaders, computes `policy_sha256`, and never
    calls `sandbox_apply` on itself.

## Unit tests (SwiftPM)

`Package.swift` declares a test-only SwiftPM layout that mirrors the
source set build.sh ships in `PWRunner.xpc`. The `runner_unit` suite
runs the `PWRunnerCoreTests` executable via:

```sh
swift run --package-path runner PWRunnerCoreTests
```

The executable hand-rolls a small XCTest-shaped harness so the test
target works on Command Line Tools alone (full Xcode not required).
`PWRunnerCore` is built with `-enable-testing` so tests can
`@testable import` it. Production builds keep going through `build.sh`;
SwiftPM's `.build/` tree is gitignored.

See `AGENTS.md` → "Swift runner unit tests (SwiftPM)" for the contract,
when to reach for a unit test vs an e2e suite, the rules around stubbing
`@convention(c)` C function pointers, and how to add a new test file.

## Test seam: `_test_overrides`

The request JSON accepts an optional `_test_overrides` block that
re-routes narrow boundaries through real production code so the test
suite can reach failure outcomes (`libsandbox_unavailable`,
`worker_spawn_failed`, `runner_timeout`) without stubbing returns.
Every honored override is mirrored back into
`data.runner_result.test_overrides`; production runs leave that field
unset.

| Key | Default | Re-routed boundary | Outcome it lets you reach |
| --- | --- | --- | --- |
| `libsandbox_path` | `/usr/lib/libsandbox.dylib` | `dlopen` in `SandboxLib.load(path:)` (host pre-spawn check) | `libsandbox_unavailable` |
| `worker_executable_path` | bundle-local `pw-probe-runner` | `posix_spawn` path in `CWorker.spawn` | `worker_spawn_failed` |
| `worker_timeout_ms` | 60000 (floored at 50) | Host-side sentinel deadline in `CWorker.run` | `runner_timeout` |
| `validator_executable_path` | bundle-local `sb_api_validator` | `posix_spawn` path in `ValidatorClient.runValidator` | `validator_spawn_failed` |
| `worker_post_apply_hang_ms` | 0 (disabled) | `--post-apply-hang-ms` argv to `pw-probe-runner` | `runner_timeout` |

See `AGENTS.md` → "Testing `normalized_outcome` failure paths via
`_test_overrides`" for the full contract, the four-assertion test
recipe, and the rules for adding a new override.

- `runner/runner-client/main.swift` → builds `dist/PolicyWitness.app/Contents/MacOS/pw-runner-client`
  - Thin `NSXPCConnection` wrapper that forwards JSON bytes and prints the runner’s JSON reply.

- `runner/services/PWRunner/`
  - `Info.plist`, `Entitlements.plist`, `main.swift` for the standard runner XPC service bundle. Debug-attach inspection goes through BYOXPC.

- `controller/tools/pw_probe_runner/pw_probe_runner.c` (+
  `pw_probe_runner_abi.h`) — the C worker that owns the post-apply
  syscall surface. Built once and embedded inside each XPC service
  bundle as `…/Contents/MacOS/pw-probe-runner` (not the app's
  top-level `Contents/MacOS/`) so built-in and BYOXPC runners both
  resolve the binary relative to their own bundle. Driven by
  `CWorker.swift`; the `runner_c_worker_harness` suite exercises it
  in isolation as a regression pin.

## Specimen inputs

The runner consumes a `PWRunnerRunSpec` which contains:

- `policy`: `sbpl` source (with optional `params`)
- `probe_plan`: ordered probe steps (sandbox_check + attempt)

## Run result highlights

Each probe step reports both a `sandbox_check` and an `attempt` result:

- `pid` at the top level is the sandboxed worker PID when
  `runner_subprocess` is present. `runner_subprocess` carries the worker's
  `exit_code` or `term_signal` plus a `partial_steps` marker. The
  classifier in `CWorkerOrchestrator` maps the sentinel state + waitpid
  outcome to `normalized_outcome`: `done` sentinel flipped + clean exit →
  `ok`; signal-before-done → `runner_sandbox_denied` (the precise signal
  stays in `runner_subprocess.term_signal`); host SIGKILL after sentinel
  timeout → `runner_timeout`; failure to `posix_spawn` →
  `worker_spawn_failed`.
- `sandbox_check` includes `scope` (`post_sandbox`) plus the original
  `filter_value` and a best-effort `effective_filter_value` (for `path` filters,
  this is the runner’s normalized path). It also reports `pid`, `operation`,
  `filter_type_id`, and `errno`/`error` when the check call fails.
- `attempt` always includes `exit_code` and `syscall_errno` (explicit `null` when
  not applicable), and for file attempts it includes `requested_path`,
  `normalized_path`, and `observed_path` (fd-based when available). The `rc`
  and `errno` fields are retained for compatibility.

## Entitlements and sandboxing (important distinction)

The standard built-in runner ships with minimal entitlements. External
(BYOXPC) runners can carry additional hardened-runtime exceptions for
inspection and controlled extensibility (debug attach / dynamic loading /
dyld env / executable memory). These do **not** make sandbox policy “dynamic”.

## Caller authorization (built-in only)

Built-in runners can require a signed caller before accepting XPC connections.
The check is controlled via Info.plist keys:

- `PWRunnerRequireSignedCaller` (bool)
- `PWRunnerAllowedIdentifiers` (optional array of code signing identifiers)

When enabled, the runner compares the caller’s Team ID to its own Team ID and
optionally enforces the allowlist. External runners are unaffected unless they
opt in by adding the same keys.

Sandbox policy variation is driven by the specimen itself:

- the controller supplies SBPL,
- the runner worker applies it once to itself,
- the runner’s witness is defined by mandatory multi-channel evidence (see the controller docs).

## External runner services

PolicyWitness can target **external runner services** when entitlements are
required. An external runner is the same PWRunner implementation, but signed
with user-selected entitlements and registered with launchd as a **BYOXPC**
runner: a signed `.xpc` bundle, addressed by `CFBundleIdentifier`.

Invariants:

- The protocol is unchanged (`PWRunnerProtocol` JSON-over-Data).
- One specimen -> one runner process; the runner applies the sandbox once and exits.
- Evidence schema remains identical; the controller records runner provenance.

The controller provides a `policy-witness runner` manager to install/register
these services and to enforce entitlements supersets before dispatch.

## Agent note: “nested sandbox” harnesses

Some development harnesses run tools inside an OS sandbox. In those environments:

- XPC lookup can fail early with `NSCocoaErrorDomain` 4099 / error 159 `"Sandbox restriction"` (before the service launches).
- Unified Logging access can also be restricted, making deny-evidence capture impossible from inside the harness.

Treat this as an environment constraint, not a PolicyWitness regression.

If you suspect you are running under a sandboxed automation harness, re-run from a normal Terminal (or with escalation) before debugging PolicyWitness itself.
