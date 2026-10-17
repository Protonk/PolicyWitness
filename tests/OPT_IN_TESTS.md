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
- Is a specified red test for planned behavior. Keep it non-default until it
  turns green, so the default battery stays green on main while the red is
  demonstrable through explicit selection.

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

### Native path-query observations

- **Case:** `witness_contract/path_query_observations`
- **Location:** `tests/suites/witness_contract/opt_in/path_query_observations.sh`
- **Purpose:** Investigate host-resolution eligibility using the shipped
  validator and independent native targets, with retained query returns, file
  operations, path state and same-process unlink/recreate observations.
- **Opt-in reason:** Exploratory OS-sensitive native behavior and Developer ID
  signing. No expected prediction/enforcement agreement is asserted.
- **Equipment:** Built app, clang and an explicit `IDENTITY` or
  `PW_BYOXPC_IDENTITY`. Run outside the automation sandbox. No service install,
  GUI, TCC-protected target or network timestamp is required.
- **Artifacts:** `<run>/suites/witness_contract/path_query_observations/artifacts/`
  retains signed target/source, commands, policies, raw streams, per-boundary
  observations, equipment hashes and exact child/workspace cleanup.

### Integrated extra path queries

- **Case:** `witness_contract/path_query_integrated`
- **Location:** `tests/suites/witness_contract/opt_in/path_query_integrated.sh`
- **Purpose:** Observe extra native queries against actual PW workers through a
  validator wrapper, preserving the current planner's reports and separately
  retaining the extra transcript. Covers unlink/recreate, create and symlink unlink.
- **Opt-in reason:** Exploratory OS-sensitive interpretation with extra query
  instrumentation; no product behavior change or universal agreement assertion.
- **Equipment:** Built app and live XPC outside the automation sandbox. Uses
  owned `/private/tmp` targets, no service installation or signing.
- **Artifacts:** `<run>/suites/witness_contract/path_query_integrated/artifacts/`
  retains specimens, raw envelopes, native receipts, independent state and cleanup.

### signed artifact controls

- **Case:** `preflight/signed_artifact_controls`
- **Location:** `tests/suites/preflight/check_signed_artifacts.py`
- **Purpose:** Verify that real signature damage fails inspection and validly
  re-signing a copied runner cannot conceal a stale embedded manifest.
- **Resource dependency:** Built app and matching Developer ID. Uses disposable
  copies under `/private/tmp`; never launches or modifies the selected source app.
- **When to run:** After changing artifact inspection, inventory, or signing setup.

### build guard controls

- **Case:** `preflight/build_guard_controls`
- **Location:** `tests/suites/preflight/opt_in/build_guards.py`
- **Purpose:** Drive the unchanged build script through Cargo and native minimum
  mismatches, one or every shipped output replaced by a Mach-O whose
  `LC_BUILD_VERSION` names another SDK version (linked with the selected SDK,
  the version stamped by the linker's `-platform_version`: a controlled
  metadata mismatch, not a compile against a second SDK),
  an ad hoc helper after successful deep verification, and a helper, the
  service seal or the app seal signed with `--timestamp=none` (omitting the
  flag is not a reliable fault). Assert the diagnostics, statuses, the
  signatures made (inspected independently) and preserved or absent outputs,
  alongside successful full and partial builds.
- **Resource dependency:** Built app for identity resolution, matching Developer
  ID, Cargo with cached dependencies, Meson, Ninja and the C/Swift toolchains
  with one installed macOS SDK. Builds run offline in a disposable checkout under
  `/private/tmp`; signing still needs the timestamp service and an
  unsandboxed shell. No app is launched.
- **Opt-in reason:** Runs multiple builds and signs both variants with keychain
  access. The source checkout's caches and distribution are untouched.
- **When to run:** After changing the minimum, SDK or signing checks or their
  placement relative to compilation, assembly and packaging.
- **Artifacts:** `<run>/suites/preflight/build_guard_controls/artifacts/` holds
  each build's raw output, status, tool and injection receipts, the wrong-SDK
  equipment, signature displays and output hashes.

### build refusal controls

- **Case:** `preflight/build_refusal_controls`
- **Location:** `tests/suites/preflight/opt_in/build_refusals.py`
- **Purpose:** Drive the unchanged build script through every refusal the
  build manifest lists, one disposable fault at a time, in each variant the
  refusal applies to: a tracked input gone, a held checkout lock, a claim
  without a live owner's handoff or an owner killed mid-build, a build
  launched by a Python owner without the caller's requests, a developer
  directory without the SDK or without a numeric SDK version, a missing,
  malformed or foreign toolchain stamp, forwarding Rust and C compiler
  wrappers relabelled after the stamp recorded them, a probe that fails,
  hangs or floods stderr past its cap, a Cargo configuration that cannot be
  resolved or whose `[env]` forces another deployment target or SDK, a Cargo
  judgment that is not a literal boolean, redirected Cargo intermediates, a symlink at a cache path component
  or the session destination, a path replaced after an earlier helper's
  admission, a failed removal, Cargo outputs that vanish, lose
  their executable bit or land under a target triple, a reused judgment in
  fresh mode, a missing or old Ninja, a Meson directory departing from the
  policy, sources that do not compile, a worker reporting another identity,
  outputs and inputs removed at the boundary a tool wrapper hooks, damaged or
  tampered signatures, a session gone before evidence, and a record edited
  after the seal. Also runs the fresh-mode state sequence (fresh build,
  unchanged reuse, enabling the XPC pieces, refused incompatible reuse,
  explicit fresh recovery, interruptions, a retried compile failure, caches
  surviving independently), plants environment and stderr canaries no record
  may carry, replaces a cached Cargo output before capture to show the stated
  limit of the record, and drives `make notarize` and `make release` with a
  controlled build step to show fresh mode enforced or refused. A lock
  lifetime sequence kills the owner, the script and a tool wrapper while a
  protected holder runs beyond the wrapper and observes from outside that a
  competing build, battery and standalone Cargo command are refused until it
  exits, that a wrapper dropping the descriptor fails that control, that
  SIGINT and SIGTERM stop the build's process group, that the compilers the
  real Cargo and Meson run hold the descriptor, that a nested build and owned
  command share one acquisition while an independent worktree is held, and
  that the lock is held through packaging. A Cargo oracle builds a scratch
  crate with real Cargo through recording forwarders for every configuration
  form the resolver reads and requires the compilers, wrapper chain, working
  directory and child environment Cargo used to be the predicted ones; a
  selection sequence drives the script with retained caches through an
  included compiler selection, a change to only that file, a forced `[env]`
  `PATH`, and flag precedence. Mutated copies of the script with
  a guard removed or moved past its operation, and of the session helper
  with path admission disabled, must fail their control.
- **Resource dependency:** Built app for identity resolution, matching Developer
  ID, Cargo with cached dependencies, Meson, Ninja and the C/Swift toolchains.
  Builds run offline in a disposable checkout under `/private/tmp`; signing
  still needs the timestamp service and an unsandboxed shell. No app is
  launched and nothing is submitted to Apple.
- **Opt-in reason:** Runs many builds, several of them fresh, and signs with
  keychain access. The source checkout's caches and distribution are untouched.
- **When to run:** After changing a refusal, its placement, the tool wrappers'
  boundaries, the stamp, fresh mode, path admission, the lock, its handoff or
  launch boundaries, the request capture or the generated refusal table.
- **Artifacts:** `<run>/suites/preflight/build_refusal_controls/artifacts/` holds
  each build's raw output, status, tool and forwarding-wrapper receipts with
  the hooks that fired and the lock descriptor each compiler held, the
  session, stamp and record copies, the output inventory, the outside-tree
  snapshots of the path controls, the lock lifetime observations, the make
  entrypoint receipts and the mutation results.

### build toolchain switch controls

- **Case:** `preflight/build_toolchain_switch_controls`
- **Location:** `tests/suites/preflight/opt_in/build_toolchain_switch.py`
- **Purpose:** Make the toolchain switch real: build under the selected
  developer directory with fresh mode, reuse under it, be refused reuse under
  `/Library/Developer/CommandLineTools` by a field the control's own probes of
  both directories show to differ, and recover under it with fresh mode. The
  control records which stamped fields differed and credits only those;
  different compiler builds do not imply different SDK versions. For each
  developer directory it first checks that the SDK xcrun selects links a C
  and a Swift program with that directory's own tools; when it does not, the
  newest SDK of that directory that does link is named through `SDKROOT`,
  which the build resolves and records as a caller's selection, and every
  probe is kept in the equipment report.
- **Resource dependency:** Everything the guard controls need, plus both Xcode
  (or the selected developer directory) and the Command Line Tools installed
  with distinct C compiler identities. Indistinct or missing equipment is a
  failure, never a skip or a wrapper fallback. No second Rust toolchain is
  needed.
- **Opt-in reason:** Two fresh full builds under different toolchains with
  keychain access.
- **When to run:** After changing the stamp's fields or comparison, and for
  acceptance of the build provenance work.
- **Artifacts:** `<run>/suites/preflight/build_toolchain_switch_controls/artifacts/`
  holds the equipment probes, the distinct and equal fields, each build's raw
  output, receipts, stamp and record, and the switch summary.

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

### BYOXPC extension and phase witness

- **Case:** `witness_contract/extensions_byoxpc`
- **Location:** `tests/suites/witness_contract/opt_in/extensions_byoxpc.sh`
- **Purpose:** Run the shared native lifecycle, placement, omission, target
  preparation and ordinary-phase controls through an owned BYOXPC runner.
  Compare issuer and worker authority read-backs with registry and envelope
  provenance; exercise maximum replies and an actual missing installed issuer
  with exact-byte restoration; verify removal afterward.
- **Opt-in reason:** Installs a launchd service in a logged-in GUI session and
  requires the selected app's Developer ID identity.
- **Resource dependency:** Signed app, signing identity, GUI session and clang.
  Targets live in the owned `/private/tmp` staging directory. The shared session
  helper retains durable ownership until removal is verified.
- **When to run:** After changing native extension execution, phase handling,
  issuer signing, provenance or runner installation.
- **Artifacts:** `<run>/suites/witness_contract/extensions_byoxpc/artifacts/`

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

### Native worker clock applicability

- **Suite name:** `runner_c_worker_harness`, case `native_clock`.
- **Location:** `tests/suites/runner_c_worker_harness/opt_in/native_clock.sh`
  and `native_clock.c`.
- **Purpose:** Run the production continuous-clock helpers in fresh processes
  under the original version-2 policy, bare deny-default and allow-default, in
  the production order and with the first explicit raw read after application.
  Every sample must validate and no continuous-clock process may have a deny
  record. The standalone `CLOCK_MONOTONIC` neighbour is recorded as observed;
  its intermittent failure need not recur in a given run.
- **Opt-in reason:** Reads unified logging and observes OS-sensitive native
  behavior; its claims are scoped to the recorded machine and implementation.
- **Resource dependency:** clang and an unsandboxed shell for `log show`. A
  refused log query leaves deny records unavailable, which is not proof of
  safety. No app, identity or service install is needed; the worker's Mach-O
  architecture is recorded when the app is present.
- **When to run:** After a change to the worker's clock source, timebase setup
  or sample validation, an OS or SDK update, or on another supported machine.
  Select with `tests/run.sh --case runner_c_worker_harness/native_clock`.
- **Artifacts:** `<run>/suites/runner_c_worker_harness/native_clock/artifacts/`:
  `platform.txt`, `installed-disassembly.txt` (a separate lldb process),
  `results.ndjson` (setup returns, factors, sample counts, PIDs and reaps),
  `summary.json` and the raw `deny-log.ndjson` with its status.
- **Gating:** Required for worker clock changes; it does not test an actual
  system sleep/wake, which needs separately arranged equipment.

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

### Native sandbox extensions

- **Case:** `sandbox_extensions_native/feasibility`
- **Location:** `tests/suites/sandbox_extensions_native/run.sh`
- **Purpose:** Independent signed native lifecycle, fresh file-access and failure
  controls, issuer lifetime, transient-token handling and allocation observations.
- **Resource dependency:** macOS C toolchain, Developer ID Application identity
  and unsandboxed execution; signing uses the timestamp service. No app or GUI
  service installation is required. Set `IDENTITY` or `PW_BYOXPC_IDENTITY`.
- **When to run:** Before choosing production file-extension authority, native
  call representation, issuer lifetime or allocation assumptions; after changing
  the native experiment or its checker.
- **Artifacts:** The case retains source/build/signing provenance, target
  metadata, native reports and checker controls under its managed artifact
  directory. Token bytes remain transient.
