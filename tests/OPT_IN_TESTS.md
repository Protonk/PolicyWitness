# Opt-in Tests (dev-only)

This file is the registry for **opt-in** tests. Opt-in tests are excluded from
the default `tests/run.sh --all` run because they depend on resources or OS
behaviors that are not reliably available in CI or on every developer machine.

Goals:

- Give a single place to see **what** opt-in tests exist and **why**.
- Make each test's **resource dependency** explicit (PTY, signing identity,
  network, system logs, long runtime, etc).
- Provide a clear **when to run** trigger so the test is not forgotten.

Opt-in tests live under `tests/suites/runner_*/opt_in/` and are invoked directly.
Compatibility wrappers remain under `tests/suites/opt_in/`.

## What makes a test opt-in

Any of the following is usually sufficient:

- Requires a **TTY/PTY**, window size ioctls, or UI interaction.
- Requires **network access**, GUI services, or other host capabilities that are
  unstable in CI.
- Requires a **Developer ID identity** or notarization.
- Takes a long time or is intentionally heavy (multi-minute).
- Reads from **Unified Logging** or other sandbox-sensitive telemetry streams.

If the test depends on one of these, make it opt-in and document the dependency.

## How to run opt-in tests

Run the script directly:

```sh
tests/suites/runner_*/opt_in/<test>.sh
# or a compatibility wrapper:
tests/suites/opt_in/<test>.sh
```

There is intentionally no `opt_in` suite runner; opt-in tests are meant to be
invoked explicitly so resource-heavy or flaky tests are never run by accident.

GUI session note: tests that install or bootstrap launchd services (for example
`runner_instrumentation_dyld_env`) require a logged-in desktop session. Run
them from a local Terminal.app window; SSH/CI or sandboxed harnesses will skip
with a non-GUI session message.

If you see `permission denied`, either invoke with `bash` or make the script
executable (these tests are regular shell scripts).

Optional standard overrides:

- `PW_TEST_OUT_DIR` (default `tests/out`)
- `PW_TEST_RUN_ID` (for stable run ids)

## Registry (current opt-in tests)

### runner_byoxpc

- **Location:** `tests/suites/runner_byoxpc/run.sh`
- **Purpose:** Run smoke + blackbox suites through a BYOXPC runner.
- **Opt-in reason:** Requires launchd service install/bootstrapping and an
  unsandboxed caller; can be blocked in sandboxed harnesses.
- **Resource dependency:** `PolicyWitness.app` built + GUI session.
- **When to run:** After changing BYOXPC install/verify behavior or runner-mode selection.
- **Artifacts:** `tests/out/suites/runner_byoxpc/*/artifacts/*`

### runner_machme

- **Location:** `tests/suites/runner_machme/run.sh`
- **Purpose:** Run smoke + blackbox suites through a MachMe runner.
- **Opt-in reason:** Requires launchd service install/bootstrapping and an
  unsandboxed caller; can be blocked in sandboxed harnesses.
- **Resource dependency:** `PolicyWitness.app` built + GUI session.
- **When to run:** After changing MachMe install/verify behavior or runner-mode selection.
- **Artifacts:** `tests/out/suites/runner_machme/*/artifacts/*`

### pw_runner_specimen

- **Location:** `tests/suites/runner_debuggable/opt_in/pw_runner_specimen.sh`
- **Purpose:** Validate the PWRunner “run” execution lane:
  - SBPL apply + probe execution (single runner instance),
  - Channel D (`sandbox_check`) vs Channel A (attempt outcome) consistency,
  - Channel B deny-signal accounting (only if the policy uses SBPL `send-signal`),
  - Channel C unified-log correlation via `sandbox-log-observer`.
- **Opt-in reason:** Requires Unified Logging access and an unsandboxed caller
  (in sandboxed harnesses, XPC lookup and log capture can be blocked).
- **Resource dependency:** `PolicyWitness.app` built + `log show` access.
- **When to run:** After changing `runner/PWRunner*` runner behavior or `policy-witness run`.
- **Artifacts:** `tests/out/suites/runner_debuggable/pw_runner_specimen/artifacts/*`

### runner_instrumentation_dylib

- **Location:** `tests/suites/runner_debuggable/opt_in/runner_instrumentation_dylib.sh`
- **Purpose:** Validate the `dylib_load` instrumentation port by building a tiny
  dylib, loading it pre-sandbox, and verifying the symbol runs.
- **Opt-in reason:** Requires a compiler toolchain and dynamic library loading.
- **Resource dependency:** `PolicyWitness.app` built + Xcode Command Line Tools.
- **When to run:** After changing instrumentation port handling or runner entitlements.
- **Artifacts:** `tests/out/suites/runner_debuggable/runner_instrumentation_dylib/artifacts/*`

### runner_instrumentation_dyld_env

- **Location:** `tests/suites/runner_byoxpc/opt_in/runner_instrumentation_dyld_env.sh`
- **Purpose:** Validate BYOXPC runner env injection and the `dyld_env` port.
- **Opt-in reason:** Requires launchd service install/bootstrapping and an
  unsandboxed caller; can be blocked in sandboxed harnesses.
- **Resource dependency:** `PolicyWitness.app` built + Xcode Command Line Tools.
- **When to run:** After changing `policy-witness runner install` or
  instrumentation env handling.
- **Artifacts:** `tests/out/suites/runner_byoxpc/runner_instrumentation_dyld_env/artifacts/*`

## Adding a new opt-in test

When you add an opt-in test, document it here with:

- **Suite name:** use the runner suite name (for example `runner_debuggable` or
  `runner_byoxpc`) so results group under `tests/out/suites/<suite>/`.
- **Location:** the script path under `tests/suites/runner_*/opt_in/`.
- **Purpose:** the behavior under test.
- **Opt-in reason:** the resource or OS behavior that makes it non-default.
- **When to run:** a trigger tied to code changes or regressions.
- **Artifacts:** where the test writes output.
- **Gating:** the explicit `test_skip` condition when the required resource is
  not available (PTY missing, identity missing, etc).

If the opt-in reason is removed (for example, you can make it stable without a
PTY), move the test into the smoke suite and remove it from this registry.
