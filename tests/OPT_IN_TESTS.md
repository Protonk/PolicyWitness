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
`runner_auth_external`) require a logged-in desktop session. Run them from a
local Terminal.app window; SSH/CI or sandboxed harnesses will skip with a
non-GUI session message.

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
- **Resource dependency:** `dist/PolicyWitness.app` built + GUI session.
- **When to run:** After changing BYOXPC install/verify behavior or runner-mode selection.
- **Artifacts:** `tests/out/suites/runner_byoxpc/*/artifacts/*`

### runner_auth_external

- **Location:** `tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh`
- **Purpose:** Validate that an external BYOXPC runner without auth keys accepts
  an ad-hoc caller (auth gating is built-in only).
- **Opt-in reason:** Requires launchd service install/bootstrapping and an
  unsandboxed caller; can be blocked in sandboxed harnesses.
- **Resource dependency:** `dist/PolicyWitness.app` built + GUI session.
- **When to run:** After changing runner caller-authorization logic.
- **Artifacts:** `tests/out/suites/runner_byoxpc/runner_auth_external/artifacts/*`

## Adding a new opt-in test

When you add an opt-in test, document it here with:

- **Suite name:** use the runner suite name (for example `runner_byoxpc`)
  so results group under `tests/out/suites/<suite>/`.
- **Location:** the script path under `tests/suites/runner_*/opt_in/`.
- **Purpose:** the behavior under test.
- **Opt-in reason:** the resource or OS behavior that makes it non-default.
- **When to run:** a trigger tied to code changes or regressions.
- **Artifacts:** where the test writes output.
- **Gating:** the explicit `test_skip` condition when the required resource is
  not available (PTY missing, identity missing, etc).

If the opt-in reason is removed (for example, you can make it stable without a
PTY), move the test into the smoke suite and remove it from this registry.
