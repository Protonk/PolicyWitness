# Opt-in Tests (dev-only)

This file is the registry for **opt-in** tests. Opt-in tests are excluded from
the default `tests/run.sh --all` run because they depend on resources or OS
behaviors that are not reliably available in CI or on every developer machine.

Goals:

- Give a single place to see **what** opt-in tests exist and **why**.
- Make each test's **resource dependency** explicit (PTY, signing identity,
  network, system logs, long runtime, etc).
- Provide a clear **when to run** trigger so the test is not forgotten.

Opt-in tests live under `tests/suites/opt_in/` and are invoked directly.

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
tests/suites/opt_in/<test>.sh
```

There is intentionally no `opt_in` suite runner; opt-in tests are meant to be
invoked explicitly so resource-heavy or flaky tests are never run by accident.

If you see `permission denied`, either invoke with `bash` or make the script
executable (these tests are regular shell scripts).

Optional standard overrides:

- `PW_TEST_OUT_DIR` (default `tests/out`)
- `PW_TEST_RUN_ID` (for stable run ids)

## Registry (current opt-in tests)

### pw_lab_tui_pty

- **Location:** `tests/suites/opt_in/pw_lab_tui_pty.sh`
- **Purpose:** Validate that the TUI can launch under a pseudo-terminal, survive
  resize storms, and exit cleanly (process-level stability).
- **Opt-in reason:** Requires a PTY, terminal ioctls, and timing-sensitive resize
  behavior that is known to be flaky in CI.
- **Resource dependency:** PTY + TTY window sizing + SIGWINCH handling.
- **When to run:** After TUI resize logic changes or when debugging TUI crashes.
- **Artifacts:** `tests/out/suites/opt_in/pw_lab_tui_pty/artifacts/*`

### pw_runner_specimen

- **Location:** `tests/suites/opt_in/pw_runner_specimen.sh`
- **Purpose:** Validate the PWRunner “specimen” execution lane:
  - canonical SBPL apply + probe execution,
  - Channel D (`sandbox_check`) vs Channel A (attempt outcome) consistency,
  - Channel B deny markers (SBPL `message` marker emitted on deny),
  - Channel C unified-log correlation via `sandbox-log-observer`.
- **Opt-in reason:** Requires Unified Logging access and an unsandboxed caller
  (in sandboxed harnesses, XPC lookup and log capture can be blocked).
- **Resource dependency:** `PolicyWitness.app` built + `log show` access.
- **When to run:** After changing `xpc/PWRunner*` runner behavior or `pw-lab specimen`.
- **Artifacts:** `tests/out/suites/opt_in/pw_runner_specimen/artifacts/*`

## Adding a new opt-in test

When you add an opt-in test, document it here with:

- **Suite name:** set `PW_TEST_SUITE="opt_in"` so results group under
  `tests/out/suites/opt_in/`.
- **Location:** the script path under `tests/suites/opt_in/`.
- **Purpose:** the behavior under test.
- **Opt-in reason:** the resource or OS behavior that makes it non-default.
- **When to run:** a trigger tied to code changes or regressions.
- **Artifacts:** where the test writes output.
- **Gating:** the explicit `test_skip` condition when the required resource is
  not available (PTY missing, identity missing, etc).

If the opt-in reason is removed (for example, you can make it stable without a
PTY), move the test into the smoke suite and remove it from this registry.
