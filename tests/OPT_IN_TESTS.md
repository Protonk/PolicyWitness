# Opt-in Tests (dev-only)

Opt-in cases are excluded from the default `tests/run.sh` battery. They remain
part of `--all`; explicit `--suite` selectors include every member of that suite,
including non-default cases. `tests/catalog.json` defines membership and required
equipment, and `tests/run.sh --suite opt_in --list` shows the complete plan.

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

Inspect before choosing resource-sensitive work:

```sh
tests/run.sh --suite opt_in --list
tests/run.sh --case runner_byoxpc/BBX-001 --list
```

Execute with `--case`, an owning `--suite`, `--suite opt_in`, or `--all`.
Selecting a BYOXPC specimen adds `runner_byoxpc/runner_install` as a dependency.
Required app/toolchain/GUI/signing equipment missing causes a failed run with
explicit unrun selections. Run launchd/XPC tests from an unsandboxed, logged-in
GUI session. Signing tests accept `PW_BYOXPC_IDENTITY`, then `IDENTITY`, otherwise
resolve a matching Developer ID from the app's team. Configuration and output
rules are documented in `tests/README.md`.

Direct scripts remain developer entrypoints; use the public dispatcher for
selection, deduplication, configuration validation, and complete accounting.

## Registry (current opt-in tests)

### built-in caller authentication

- **Case:** `smoke/runner_caller_auth`
- **Location:** `tests/suites/smoke/pw_runner_caller_auth.sh`
- **Purpose:** Prove authorization-dependent acceptance/rejection with identical
  candidate bytes, restricted/relaxed service policies, and independent file effects.
  Missing-service and relaxed-policy controls exercise the rejection checker.
- **Resource dependency:** Built app and matching Developer ID for disposable app
  fixtures. Runs real built-in XPC outside the automation sandbox; no BYOXPC install.
- **When to run:** After changing built-in caller authorization.

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
- **Purpose:** Validate installation and verification of an ad-hoc-signed BYOXPC runner
  with its caller-auth keys removed (`PWRunnerRequireSignedCaller`), using the
  normal controller/client. (A BYOXPC runner that
  keeps those keys instead requires a team-matched Developer ID caller — that
  path is covered by `runner_install.sh`.)
- **Opt-in reason:** Requires launchd service install/bootstrapping and an
  unsandboxed caller; can be blocked in sandboxed harnesses.
- **Resource dependency:** `dist/PolicyWitness.app` built + GUI session.
- **When to run:** After changing runner caller-authorization logic.
- **Artifacts:** `tests/out/suites/runner_byoxpc/runner_auth_external/artifacts/*`

### exec inheritance mutation controls

- **Suite name:** `runner_exec_inheritance`
- **Location:** `tests/suites/runner_exec_inheritance/opt_in/mutations.sh`
- **Purpose:** Confirm that the unchanged worker passes and disposable workers
  with environment or descriptor isolation disabled fail the ordinary contract
  assertions with specific leak evidence.
- **Opt-in reason:** Development diagnostic that deliberately transforms and
  rebuilds the current C implementation. Its mutation anchors need review when
  spawn implementation changes; the baseline contract tests remain independent
  of those transformations.
- **Resource dependency:** macOS C toolchain, Python 3, unsandboxed execution.
  No built app or signing identity required.
- **When to run:** After changing exec spawning, process-state inspection, or
  the inheritance assertions; before retiring overlapping coverage.
- **Artifacts:** `tests/out/suites/runner_exec_inheritance/mutation_controls/artifacts/`
- **Gating:** Explicit invocation; missing prerequisites fail rather than skip.

## Adding a new opt-in test

When you add an opt-in test, document it here with:

- **Suite name:** use the runner suite name (for example `runner_byoxpc`)
  so results group under `tests/out/suites/<suite>/`.
- **Location:** the script path under `tests/suites/runner_*/opt_in/`.
- **Purpose:** the behavior under test.
- **Opt-in reason:** the resource or OS behavior that makes it non-default.
- **When to run:** a trigger tied to code changes or regressions.
- **Artifacts:** where the test writes output.
- **Gating:** required equipment and any legitimate case-specific skip code.
  Missing required equipment fails; a skip code must also be declared in the catalog.

If the opt-in reason is removed (for example, you can make it stable without a
PTY), move the test into the smoke suite and remove it from this registry.
