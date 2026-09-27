# Opt-in Tests (dev-only)

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

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
- Is a specified red test for planned behavior. `controller/DISPOSITION-RECORD-PLAN.md`
  registers its reds as non-default until each turns green, so the default battery
  stays green on main while the red is demonstrable through explicit selection.

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

### signed artifact controls

- **Case:** `preflight/signed_artifact_controls`
- **Location:** `tests/suites/preflight/check_signed_artifacts.py`
- **Purpose:** Verify that real signature damage fails inspection and validly
  re-signing a copied runner cannot conceal a stale embedded manifest.
- **Resource dependency:** Built app and matching Developer ID. Uses disposable
  copies under `/private/tmp`; never launches or modifies the selected source app.
- **When to run:** After changing artifact inspection, inventory, or signing setup.

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
- **Purpose:** Run smoke + blackbox suites through an owned, disposable BYOXPC runner copy; preserve the selected app and verify removal, including partial setup.
- **Opt-in reason:** Requires launchd service install/bootstrapping and an
  unsandboxed caller; can be blocked in sandboxed harnesses.
- **Resource dependency:** `dist/PolicyWitness.app` built + GUI session.
- **When to run:** After changing BYOXPC install/verify behavior, runner-mode
  selection, or shared response/comparison contracts and blackbox helpers. Include
  both BBX cases and the applicable menagerie members, with owned cleanup.
- **Artifacts:** `<run>/suites/runner_byoxpc/*/artifacts/*`

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
- **When to run:** After changing runner caller authorization or session cleanup.
  The shared session helper uses a unique service, treats installation failures
  as failures, and retains durable ownership until cleanup is verified.
- **Artifacts:** `<run>/suites/runner_byoxpc/runner_auth_external/artifacts/*`

### Registry recovery

- **Suite/case:** `runner_byoxpc/registry_recovery`
- **Location:** `tests/suites/runner_byoxpc/opt_in/registry_recovery.sh`
- **Purpose:** Exercise actual registry locking and atomic persistence, pending
  installation, ownership refusals, reconciliation, skipped-bootout recovery and
  recovery after diagnostic output deletion. It uses child-process HOME/registry
  overrides and uniquely owned user services; cleanup verifies service and plist
  absence before deleting durable staging.
- **Opt-in reason:** Creates and removes launchd services in the actual GUI domain.
- **Resource dependency:** Signed app, GUI session, unsandboxed execution.
- **When to run:** After changing runner registration, selection or cleanup.
- **Artifacts:** `<run>/suites/runner_byoxpc/registry_recovery/artifacts/` contains
  actual command receipts and final cleanup observations. Failed cleanup retains
  staging with a recovery record outside run output.

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
- **Artifacts:** `<run>/suites/runner_exec_inheritance/mutation_controls/artifacts/`
- **Gating:** Explicit invocation; missing prerequisites fail rather than skip.

### Order barrier mutation controls

- **Suite name:** `witness_contract`, case `order_barrier_mutations`.
- **Location:** `tests/suites/witness_contract/opt_in/mutations.sh`.
- **Purpose:** Unmodified component and signed CLI controls pass; a worker that
  bypasses the release wait and a host that releases before its hook must cause
  early effects detected by the same observers. Both early unlink and exec
  connections must be observed while native collection remains held.
- **Opt-in reason:** Builds source mutations and signs disposable app copies;
  exact mutation anchors deliberately require review when implementation changes.
- **Resource dependency:** Built signed app, matching Developer ID Application
  identity, clang, Swift and unsandboxed live XPC. Identity resolution follows
  `PW_BYOXPC_IDENTITY`, `IDENTITY`, then the app's team-matched keychain identity.
- **When to run:** After release/barrier or observer changes, and for order-plan
  Gate 3 acceptance. Select with `tests/run.sh --case witness_contract/order_barrier_mutations`.
- **Artifacts:** `<run>/suites/witness_contract/order_barrier_mutations/artifacts/`:
  `mutations.json`, component logs, exact patched sources, per-candidate binary
  and manifest hashes, signature/evidence checks, raw envelopes, gate receipts,
  external effects and process ancestry. Disposable apps live under `/private/tmp`
  and are removed after fixture-owned process cleanup.
- **Gating:** Required explicit acceptance control. Missing signing identity
  fails both dispatcher selection and direct wrapper invocation before any build;
  it is never an expected skip. `shell_helpers/mutation_prerequisites` checks the
  direct wrapper with an unsigned fixture app and independent builder receipts.
  A build, signing, transport,
  invariant or equipment error never counts as detecting a mutation. The selected
  production app is inventoried before/after and is never patched or re-signed.

### Disposition record red tests

- **Suite name:** `witness_contract`, case `worker_attempt_in_flight_at_deadline`;
  `unit`, case `rust.disposition_reds`; `runner_unit`, case `disposition_reds`.
- **Location:** `tests/suites/witness_contract/worker_attempt_in_flight_at_deadline.sh`
  with `check_attempt_in_flight.py`; `tests/suites/unit/disposition_reds.sh`;
  `tests/suites/runner_unit/disposition_reds.sh`. Each lives beside its suite's
  default cases, not under `opt_in/`, because it is promoted in place.
- **Purpose:** The red tests of `controller/DISPOSITION-RECORD-PLAN.md`. The
  witness case runs specimens `a1` (a FIFO with no writer blocks attempt 0 until
  the host deadline; the witnessed deadline, SIGKILL request and reaped signal 9
  must project `termination_cause: host_sentinel_deadline`, the wave-1 red), `a3`
  (a completed first step must survive) and `a4` (voluntary exit 0 during grace
  after the deadline, no invented kill); the `a3`/`a4` preservation halves pass
  today and run before the red. After the red, the version-gated wave-2 checks
  read the record through `tests/lib/lifecycle_adapter.py`, require an empty
  finding list from `tests/lib/lifecycle_oracle.py`, and assert the per-step
  summaries and the `stop_reason` projection. `rust.disposition_reds` runs the
  four `#[ignore]`d controller tests by exact name: B1's refusal and its wave-2
  status-conflict report, and E1's projection of a carried record and withholding
  of a record that contradicts its basis. `runner_unit/disposition_reds` runs the
  Swift unit executable with `PW_DISPOSITION_REDS=1`, which registers the
  `disposition gap:` blocks in `DispositionResolverTests.swift`: the record and
  host facts in `runner_subprocess`, `attempt.lifecycle`, and the C2/C5 fixture
  claims. The same file's observation and preservation blocks run in the default
  battery.
- **Opt-in reason:** Red by design against the unchanged runner and controller,
  per the plan's registration-while-red convention. Promote to default membership,
  drop the `#[ignore]` attributes and the `PW_DISPOSITION_REDS` gate in the change
  that turns each green. The Rust wrapper's exact selectors and the Swift gate
  keep the tests running after promotion.
- **Resource dependency:** Built app and unsandboxed live XPC for the witness case;
  cargo for the Rust case; swift and clang for the Swift case (it builds the
  lifecycle fixture).
- **When to run:** During the disposition record's test and app-code stages, and
  after changes to `synthesize_runner_sandbox_diagnostics`, the host's cleanup path
  or the step builder. Select with
  `tests/run.sh --case witness_contract/worker_attempt_in_flight_at_deadline --case unit/rust.disposition_reds --case runner_unit/disposition_reds`.
- **Artifacts:** `<run>/suites/witness_contract/worker_attempt_in_flight_at_deadline/artifacts/`
  holds `assertions.log` and one directory per specimen (`a1/`, `a3/`, `a4/`) with
  `specimen.json`, `run.json`, `pw.stderr`, `capture.json`, `witnesses.json`,
  `diagnostics.json`, `compatibility_triples.json`, `oracle_findings.json` once
  wave 2 runs and, for the FIFO specimens, `staging.json` and `cleanup.json`. After
  CLI launch is attempted, FIFO staging under `/private/tmp` is removed only when
  `reaped: true` beside a valid worker PID witnesses exit
  (`tests/lib/worker_exit_witness.py`); otherwise it is retained. Setup failure
  before CLI launch permits removal on the test's own non-spawn observation.
  Cleanup reporting errors preserve the original failure and name the staging path
  in stderr. `<run>/suites/unit/rust.disposition_reds/artifacts/cargo-test-ignored.log`
  and `<run>/suites/runner_unit/disposition_reds/artifacts/pwrunner_core_tests.log`
  hold the Rust and Swift runs.
- **Gating:** Missing app, cargo or swift fails; no skip code. A specimen that does
  not reach its boundary fails as setup, not as the behavioral red; a producer that
  predates the record fails the wave-2 checks as version gating. The Rust wrapper
  requires every named test to run and identifies each expected assertion; build
  failures, other assertions and zero-test runs fail separately. The Swift wrapper
  requires the gap blocks to have run and fails any unrelated `FAIL` separately.

## Adding a new opt-in test

When you add an opt-in test, document it here with:

- **Suite name:** use the runner suite name (for example `runner_byoxpc`)
  so results group under `<run>/suites/<suite>/`.
- **Location:** the script path under `tests/suites/runner_*/opt_in/`.
- **Purpose:** the behavior under test.
- **Opt-in reason:** the resource or OS behavior that makes it non-default.
- **When to run:** a trigger tied to code changes or regressions.
- **Artifacts:** where the test writes output.
- **Gating:** required equipment and any legitimate case-specific skip code.
  Missing required equipment fails; a skip code must also be declared in the catalog.

If the opt-in reason is removed (for example, you can make it stable without a
PTY), move the test into the smoke suite and remove it from this registry.
