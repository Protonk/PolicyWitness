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

### BYOXPC dossier witness

- **Case:** `witness_contract/dossier_witness_byoxpc`
- **Location:** `tests/suites/witness_contract/opt_in/dossier_witness_byoxpc.sh`
- **Purpose:** Read `data.specimen` of a run selected through an owned,
  disposable BYOXPC runner copy: `runner_provenance` names the installed
  service and registry id, and every binary record carries the bundle-local
  path, its independently computed hash and the shipped manifest baseline,
  with `match`/`mismatch` agreeing with the hashes.
- **Opt-in reason:** Requires launchd service install/bootstrapping, a
  logged-in GUI session and a matching Developer ID identity.
- **Resource dependency:** `dist/PolicyWitness.app` built + GUI session +
  signing identity. Uses the shared BYOXPC session machinery
  (`tests/fixtures/byoxpc/session.py`) for ownership and verified removal.
- **When to run:** After changing runner selection, the dossier's binary
  records or BYOXPC install/verify behavior.
- **Artifacts:** `<run>/suites/witness_contract/dossier_witness_byoxpc/artifacts/byoxpc/*`

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
  identity, clang, Swift, Meson and unsandboxed live XPC. Identity resolution follows
  `PW_BYOXPC_IDENTITY`, `IDENTITY`, then the app's team-matched keychain identity.
  The control compiles its unmodified and patched hosts from the source list
  meson.build's `PWRunner` target declares, read by file-mode introspection and
  checked against the on-disk core set, so it cannot silently diverge from the
  production list.
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

### BYOXPC entitlement read-back

- **Case:** `runner_byoxpc/entitlement_readback`
- **Location:** `tests/suites/runner_byoxpc/opt_in/entitlement_readback.sh`
- **Purpose:** Install an owned runner with a supplied entitlements plist and read
  the host's, the worker's and the validator's entitlements and signatures back
  from the installed copy and from the registry record. The worker must hold the
  supplied plist; the validator must hold none; every binary carries the team's
  signature.
- **Opt-in reason:** Requires launchd service install/bootstrapping, a logged-in
  GUI session and a matching Developer ID.
- **Resource dependency:** Signed app, GUI session, matching identity; shared
  session helper for ownership and verified removal.
- **Artifacts:** `<run>/suites/runner_byoxpc/entitlement_readback/artifacts/`

### BYOXPC entitlement transfer

- **Case:** `runner_byoxpc/entitlement_transfer`
- **Location:** `tests/suites/runner_byoxpc/opt_in/entitlement_transfer.sh`
- **Purpose:** Install two owned runners, one whose supplied plist sets a key
  `true` and one that sets it `false`. A selector requiring the key is admitted
  by the first and completes an entitlement-conditioned write, with the file's
  bytes read independently; the second is refused before any host is reached,
  naming the worker and the key, and without a requirement its conditioned
  write is denied by the kernel.
- **Opt-in reason:** Requires launchd service install/bootstrapping, a logged-in
  GUI session and a matching Developer ID.
- **Resource dependency:** Signed app, GUI session, matching identity; owned
  temporary targets under `/private/tmp`; shared session helper per copy.
- **Artifacts:** `<run>/suites/runner_byoxpc/entitlement_transfer/artifacts/`

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

### BYOXPC single-use admission

- **Case:** `runner_byoxpc/single_use`
- **Location:** `tests/suites/runner_byoxpc/opt_in/single_use.sh`
- **Purpose:** Two authorized client processes contend for one held host;
  refusal cannot execute a probe or retire its owner. A fresh host then succeeds.
- **Equipment:** Signed app, matching Developer ID and GUI launchd session.
- **Ownership:** Shared session helper; exact service/plist/registry removal
  and unchanged source-app inventory are required before staging deletion.
- **Artifacts:** Replies, specimens, file effects, PID receipts and cleanup
  records under the case artifact directory.
