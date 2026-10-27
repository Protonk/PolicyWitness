# Verification for changes and investigations

This guide connects changes and investigative questions to relevant
verification controls. It records when a control is needed, what its
observations establish, and the conditions required to run and interpret it.
The [test catalog](catalog.json) owns case membership, prerequisites and
dependencies; the [harness README](README.md#how-to-run) describes selection
and execution.

Existing change-triggered requirements retain their force. Investigative entries
describe useful observations; inclusion here does not make a control mandatory.
This guide is not an exhaustive inventory of default or non-default cases.
Use `tests/run.sh --all --list` for the full catalog and
`tests/run.sh --suite opt_in --list` for the non-default selection and its
dependencies. [Contribution guidance](AGENTS.md#add-or-change-tests) explains
how to choose default membership.

## Find verification for a change

Follow the linked accounts for the actual triggers, required observations and
execution conditions. These routes include default and non-default controls;
they do not exhaust the verification relevant to a change.

| Change or investigative question | Verification account |
| --- | --- |
| Admission or validator receivers | [Integrated verification guidance](AGENTS.md#choose-the-most-integrated-test-that-can-establish-the-behavior), including the boundary and its readers. |
| Limits | [Limit-change verification](AGENTS.md#verify-a-limit-change) and the [limits coverage account](../docs/LIMITS.md#grounding-and-coverage). |
| Ordering barriers, worker wait/release, query eligibility or observers | [Required ordering controls](AGENTS.md#choose-the-most-integrated-test-that-can-establish-the-behavior) and [order-barrier mutations](#order-barrier-mutation-controls). |
| Worker clock source, timebase or sample validation; OS/SDK updates or another supported machine | [Native worker clock applicability](#native-worker-clock-applicability), including its required worker-change control and environmental scope. |
| Exec publication, compatible absence handling or confirmed-reap reconciliation and race controls | [Exec-reader mutations](#exec-reader-publication-and-absence-mutations) and [confirmed-reap mutation](#confirmed-reap-acknowledgement-mutation). |
| Exec spawning, process-state inspection, inheritance assertions or retirement of overlapping coverage | [Exec inheritance mutations](#exec-inheritance-mutation-controls). |
| BYOXPC selection, installation, registry or cleanup; shared response/comparison contracts | [Controller verification guidance](../controller/AGENTS.md#verify-the-changed-boundary), [BYOXPC shared cases](#runner_byoxpc), [registry recovery](#registry-recovery) and [default-location control](#byoxpc-default-location). |
| BYOXPC dossier records, native extension execution, phase handling, issuer signing or provenance | [Dossier witness](#byoxpc-dossier-witness) and [extension and phase witness](#byoxpc-extension-and-phase-witness). |
| Built-in or external caller authorization; host admission/exit, client re-acquisition or launchd throttle | [Built-in caller authentication](#built-in-caller-authentication), [external caller authentication](#runner_auth_external) and [occupied-claim attribution](#byoxpc-occupied-claim-attribution), including session-cleanup and registry triggers. |
| Build, toolchain, signing or artifact inspection | [Signed-artifact controls](#signed-artifact-controls), [build guards](#build-guard-controls), [build refusals](#build-refusal-controls), [translated-build refusals](#translated-build-refusal-controls) and [toolchain-switch controls](#build-toolchain-switch-controls). Their individual triggers and equipment conditions apply. |
| Native file-extension authority, call representation, issuer lifetime or allocation assumptions; experiment or checker changes | [Native sandbox-extension experiment](#native-sandbox-extensions). |

## Select and run a control

Inspect a relevant canonical case before execution, then select it through the
public dispatcher, for example:

```sh
tests/run.sh --case runner_byoxpc/BBX-001 --list
PW_TEST_OUT_DIR=tests/out/runs/byoxpc-verification tests/run.sh --case runner_byoxpc/BBX-001
```

Selection adds declared dependencies. Missing required equipment fails with
unrun selections. The [harness](README.md#how-to-run) owns suite and case
selection; its [configuration](README.md#configuration),
[equipment checks](README.md#equipment-checks) and
[output contract](README.md#output-contract-testsout) describe execution and
results. Follow the [test guidance](AGENTS.md#choose-and-run-verification) for
fresh output and sandboxed-harness diagnostics. Case scripts are invoked only
through the dispatcher.

For BYOXPC controls, launchd/XPC needs an unsandboxed, logged-in GUI session.
Signing identity selection uses `PW_BYOXPC_IDENTITY`, then `IDENTITY`, otherwise
an identity matching the app's team, where the case supports that fallback.
Individual entries state stricter identity requirements. Follow the
[external-runner ownership and recovery guidance](../AGENTS.md#external-runner-workflow).

`<run>` below is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

## Controls and their applicability

### Exec reader publication and absence mutations

- **Case:** `runner_unit/exec_reader_mutations`
- **Purpose:** Bypass the completed-slot gate or invent an exec account when
  metadata is absent in disposable Swift host sources. Unchanged reader
  assertions must reject exposed unpublished facts and invented cleanup absence.
- **Execution considerations:** Three isolated Swift package compilations.
- **When to run:** Required when changing exec payload publication or compatible
  absence handling.
- **Equipment:** Swift and clang; no signed app or service installation.
- **Artifacts:** Exact source copies/hashes, native fixture, command logs and
  structured baseline/rejection receipts naming each failed assertion.
- **Details:** [Exec reader mutations](suites/runner_unit/README.md#exec-reader-mutations).

### Confirmed-reap acknowledgement mutation

- **Case:** `runner_unit/reaped_ack_mutation`
- **Purpose:** Remove final acknowledgement reconciliation in a disposable host
  copy. Previously unseen clean and fatal acknowledgements must lose ordering
  credit; prior ownership loss must remain unqualified.
- **Execution considerations:** Two isolated Swift package builds.
- **When to run:** Required when changing confirmed-reap reconciliation or its
  race controls.
- **Equipment:** Swift and clang; no signed app or service installation.
- **Artifacts:** Exact source copies/hashes, build/run commands and logs, both
  host variants, and structured passing/rejected results.
- **Details:** [Confirmed-reap controls](suites/runner_unit/README.md#confirmed-reap-acknowledgement).

### Worker resource challenge probes

- **Cases:** `runner_unit/host_setup_oracle_sensitivity`,
  `runner_exec_lifecycle/closed_streams_leader_exit`, and
  `runner_exec_inheritance/closed_worker_stderr`.
- **Purpose:** Characterize setup-checker sensitivity to deliberately wrong
  disposable host copies, same-group descendant survival after normal exec
  completion, and child stderr delivery with worker fd 2 closed. Passing means
  the stated counterexample was observed; it is not a safety guarantee.
- **Execution considerations:** Exploratory native resource/failure observations and
  multiple disposable Swift builds. Run outside the automation sandbox.
- **Equipment:** Swift/clang for setup controls; signed app/clang for lifecycle;
  signed app, embedded worker and clang for closed stderr. No service install.
- **Artifacts:** Each canonical case's `artifacts/` retains inputs, observations
  and cleanup. The original setup checker and production bytes are unchanged;
  mutations exist only in disposable source copies.
- **Details:** [Setup oracle](suites/runner_unit/README.md),
  [lifecycle](suites/runner_exec_lifecycle/README.md), and
  [inheritance](suites/runner_exec_inheritance/README.md).

### Production worker launch inventory

- **Case:** `runner_exec_inheritance/launch_inventory`
- **Location:** `tests/suites/runner_exec_inheritance/launch_inventory.py`
- **Purpose:** Record descriptors, environment and accessible mappings/ports
  of signed production workers at the pre-ready and post-apply sleep seams.
  The contaminated-worker case is a required positive control.
- **Execution considerations:** Exploratory process inspection, optional task-port access
  and two twenty-second holds. Run outside the automation sandbox.
- **Equipment:** Signed app, embedded worker, clang for the dependency, macOS
  `ps`, `lsof`, `vmmap` and `lsmp`. No service installation or signing mutation.
- **Artifacts:** `<run>/suites/runner_exec_inheritance/launch_inventory/artifacts/`.
  Failed optional task inspection is recorded; mandatory observations and
  production cleanup must succeed. This is not a general clean-launch oracle.

### Native path-query observations

- **Case:** `witness_contract/path_query_observations`
- **Location:** `tests/suites/witness_contract/opt_in/path_query_observations.sh`
- **Purpose:** Investigate host-resolution eligibility using the shipped
  validator and independent native targets, with retained query returns, file
  operations, path state and same-process unlink/recreate observations.
- **Execution considerations:** Exploratory OS-sensitive native behavior and Developer ID
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
- **Execution considerations:** Exploratory OS-sensitive interpretation with extra query
  instrumentation; no product behavior change or universal agreement assertion.
- **Equipment:** Built app and live XPC outside the automation sandbox. Uses
  owned `/private/tmp` targets, no service installation or signing.
- **Artifacts:** `<run>/suites/witness_contract/path_query_integrated/artifacts/`
  retains specimens, raw envelopes, native receipts, independent state and cleanup.

### signed artifact controls

- **Case:** `preflight/signed_artifact_controls`
- **Location:** `tests/suites/preflight/check_signed_artifacts.py`
- **Purpose:** Verify that real signature damage fails inspection and validly
  re-signing a copied runner cannot conceal a stale embedded manifest, and that
  real x86_64 and universal Mach-O signed with the identity, with consistent
  manifest and record hashes, fail for architecture, with a record that
  contradicts the bytes visible as a separate fault. A signed app carrying a
  universal dSYM resource passes without treating its debug slices as code.
- **Resource dependency:** Built app and matching Developer ID. Uses disposable
  copies under `/private/tmp`; never launches or modifies the selected source app.
- **When to run:** After changing artifact inspection, inventory, the output
  target check, or signing setup.

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
  alongside successful full and partial builds. A Cargo output replaced by a
  thin x86_64 and a native output by a universal Mach-O, each carrying the
  plist's minimum and the selected SDK, must be named and refused by the output
  target check alone before assembly; the minimum and SDK faults must not reach
  it.
- **Resource dependency:** Built app for identity resolution, matching Developer
  ID, Cargo with cached dependencies, Meson, Ninja and the C/Swift toolchains
  with one installed macOS SDK. Builds run offline in a disposable checkout under
  `/private/tmp`; signing still needs the timestamp service and an
  unsandboxed shell. No app is launched.
- **Execution considerations:** Runs multiple builds and signs both variants with keychain
  access. The source checkout's caches and distribution are untouched.
- **When to run:** After changing the minimum, SDK, output target or signing
  checks or their placement relative to compilation, assembly and packaging.
- **Artifacts:** `<run>/suites/preflight/build_guard_controls/artifacts/` holds
  each build's raw output, status, tool and injection receipts, the wrong-SDK
  equipment, signature displays and output hashes.

### build refusal controls

- **Case:** `preflight/build_refusal_controls`
- **Location:** `tests/suites/preflight/opt_in/build_refusals.py`
- **Contained shim control:** Runs a shim with a missing SDK request only
  after the shared containment gate passes, and compares an empty-SDK
  neighbour. Requires unified-log access for the installation-service denial
  attributed by PID; records profiles, gate checks, command output and log
  queries. No other control deliberately makes an installation request.
- **Purpose:** Drive the unchanged build script through every refusal the
  build manifest lists, one disposable fault at a time, in each variant the
  refusal applies to: an unreadable `hw.optional.arm64` under a sandbox
  profile, whose native builder refusal must be the only output ahead of
  `--help`, an unknown argument, a bad knob, a missing tracked input, an
  invalid `SDKROOT` under the helper's combined containment and an
  independently held lock, a tracked input gone, a held checkout lock, a claim
  without a live owner's handoff or an owner killed mid-build, a build
  launched with a missing or changed environment witness, a developer
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
  `PATH`, an x86_64 target default overridden by the explicit target, and
  flag precedence with the output triple's target rules. For the output
  target, outputs outside it are substituted at each checked boundary (after
  Cargo, with a corrupted cached unit refused again on reuse; after the native
  compile, before the worker runs; in the assembled bundle beside an unlisted
  universal file, before any signature; before the ZIP). Text, empty and
  truncated-header replacements and missing required
  executables refuse in both variants at the assembled and packaging gates,
  before any signature or the ZIP respectively. A stamp names another target or predates the contract, a cross
  file gives `meson setup` an x86_64 host, and the controller package's target guard is driven by
  direct Cargo builds for x86_64 and iOS with `--keep-going` (whose standard
  libraries this machine lacks, a recorded limit) and its removal or
  weakening shown to fail. Mutated copies of the script with
  a guard removed or moved past its operation (the native builder check
  removed, or moved past Python and SDK setup or past the lock front end), of the session helper
  with path admission disabled, of the output check with its predicate
  reduced to arm64 membership, and of `meson.build` without its output-target
  assertion, must fail their control.
- **Resource dependency:** Built app for identity resolution, matching Developer
  ID, Cargo with cached dependencies, Meson, Ninja and the C/Swift toolchains.
  Builds run offline in a disposable checkout under `/private/tmp`; signing
  still needs the timestamp service and an unsandboxed shell. The final
  release-battery sequence launches the built app through real acceptance
  and the default battery. Notarization, staple validation and Gatekeeper
  responses are controlled locally; nothing is submitted to Apple.
- **Execution considerations:** Runs many builds, several of them fresh, and signs with
  keychain access, then runs the default battery against an extracted build
  ZIP. The source checkout's caches and distribution are untouched.
- **When to run:** After changing a refusal, its placement, the tool wrappers'
  boundaries, the stamp, fresh mode, path admission, the output target, the
  native builder check, the lock, its handoff or launch boundaries, the request
  capture, the generated refusal table or release-acceptance orchestration.
- **Artifacts:** `<run>/suites/preflight/build_refusal_controls/artifacts/` holds
  each build's raw output, status, tool and forwarding-wrapper receipts with
  the hooks that fired and the lock descriptor each compiler held, the
  session, stamp and record copies, the output inventory, the outside-tree
  snapshots of the path controls, the lock lifetime observations, the make
  entrypoint receipts, the mutation results and the complete acceptance
  output from the release-battery sequence.

### translated build refusal controls

- **Case:** `preflight/translated_build_refusal_controls`
- **Location:** `tests/suites/preflight/opt_in/translated_build_refusals.py`
- **Purpose:** Establish the native builder refusal under real translation.
  In a disposable admission fixture, the unchanged script run by
  `arch -x86_64 /bin/bash` and `make build` run by `arch -x86_64 /usr/bin/make`
  refuse naming `sysctl.proc_translated=1` in both variants, with `SDKROOT`
  unset or valid, ahead of `--help`, an unknown argument, a bad knob, a missing
  tracked input and an invalid `SDKROOT`, and ahead of an independently held
  checkout lock. Recording wrappers for cargo, meson, ninja, codesign and cp,
  first on a fixed `PATH`, must record no call, version probes included; the
  session, caches and previous distribution output must not change. A make
  given an invalid `SDKROOT` refuses at parse time without entering the
  script. Invalid SDK requests run under the ordinary shim-probe containment
  with `arch` inside it. Make's own launch and SDK check precede the script
  and are outside the receipt claim.
- **Resource dependency:** Rosetta, required as `rosetta` equipment: a shell
  started with `arch -x86_64` must read `sysctl.proc_translated` as `1`.
  Missing Rosetta leaves the case unrun as an equipment failure; nothing is
  installed. No app, identity, compiler or signing is needed.
- **Execution considerations:** Rosetta is optional on Apple Silicon Macs, and the
  general refusal controls must stay runnable without it.
- **When to run:** After changing the native builder check, its position in
  `build.sh`, the Makefile's build entry or SDK guard, or the `rosetta`
  equipment probe.
- **Artifacts:** `<run>/suites/preflight/translated_build_refusal_controls/artifacts/`
  holds the equipment probe, each run's argv, environment, raw output,
  receipts and inventory results, and the containment gate.

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
- **Execution considerations:** Two fresh full builds under different toolchains with
  keychain access.
- **When to run:** Required after changing the toolchain stamp's fields or comparison.
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
- **Execution considerations:** Requires launchd service install/bootstrapping, a
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
- **Execution considerations:** Installs a launchd service in a logged-in GUI session and
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
- **Execution considerations:** Requires launchd service install/bootstrapping and an
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
- **Execution considerations:** Requires launchd service install/bootstrapping and an
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
- **Execution considerations:** Creates and removes launchd services in the actual GUI domain.
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
- **Execution considerations:** Development diagnostic that deliberately transforms and
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
- **Execution considerations:** Builds source mutations and signs disposable app copies;
  exact mutation anchors deliberately require review when implementation changes.
- **Resource dependency:** Built signed app, matching Developer ID Application
  identity, clang, Swift, Meson and unsandboxed live XPC. Identity resolution follows
  `PW_BYOXPC_IDENTITY`, `IDENTITY`, then the app's team-matched keychain identity.
  The control compiles its unmodified and patched hosts from the source list
  meson.build's `PWRunner` target declares, read by file-mode introspection and
  checked against the on-disk core set, so it cannot silently diverge from the
  production list.
- **When to run:** Required after release/barrier or observer changes, including
  changes to the worker wait, release store or query eligibility rule, as specified
  by the [root ordering guidance](../AGENTS.md#core-ideas) and
  [test guidance](AGENTS.md#choose-the-most-integrated-test-that-can-establish-the-behavior).
  Select with `tests/run.sh --case witness_contract/order_barrier_mutations`.
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
- **Execution considerations:** Reads unified logging and observes OS-sensitive native
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
- **Execution considerations:** Requires launchd service install/bootstrapping, a logged-in
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
- **Execution considerations:** Requires launchd service install/bootstrapping, a logged-in
  GUI session and a matching Developer ID.
- **Resource dependency:** Signed app, GUI session, matching identity; owned
  temporary targets under `/private/tmp`; shared session helper per copy.
- **Artifacts:** `<run>/suites/runner_byoxpc/entitlement_transfer/artifacts/`

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

### BYOXPC occupied-claim attribution

- **Case:** `runner_byoxpc/bad_neighbor_claims`
- **Location:** `tests/suites/runner_byoxpc/opt_in/bad_neighbor_claims.sh`
- **Purpose:** Require deadline-bounded re-acquisition without duplicate effects,
  with each refused attempt attributed to a host generation and its owner: local retirement lag, a foreign authorized client holding a
  host, and clients queued together during launchd's respawn throttle. Also
  observes registry lock contention on a fixture registry.
- **Execution considerations:** Live launchd service, timing-sensitive schedules and a
  same-UID foreign client.
- **When to run:** After changing host admission or exit, client connection or
  re-acquisition, the generated plist's throttle, or the session helper's
  registry handling.
- **Equipment:** Signed app, matching Developer ID and GUI launchd session.
- **Ownership:** Shared session helper; exact removal before staging deletion.
- **Artifacts:** `claims/` holds per-request specimens, replies and effects,
  `processes.json` (sampled generations), `unified-log.ndjson`,
  `checker-controls.json` and `summary.json`.

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

### BYOXPC default location

- **Case:** `runner_byoxpc/default_location`
- **Location:** `tests/suites/runner_byoxpc/opt_in/default_location.sh`
- **Purpose:** Exercise installation, listing, a specimen and verified removal
  without a registry override, including the real user LaunchAgents plist.
- **Execution considerations:** Shared default registry and live signed user service.
- **When to run:** After registry path, installation or session-helper changes.
- **Equipment:** Signed app, matching Developer ID and GUI launchd session.
- **Ownership:** Shared session helper; registry-busy is a failure, never retried.
- **Artifacts:** Default listing, plist observations, run envelope and cleanup receipts.

## Maintaining this guide

Maintain an entry when it clarifies applicability, interpretation or consequential
operating conditions. Use canonical case identifiers and link to the owning
suite account for detailed assertions and fixtures, following
[test contribution guidance](AGENTS.md#add-or-change-tests). New non-default
cases do not automatically need an entry here.

Keep the index's routes aligned with their owning instructions. Preserve the
strength of existing requirements and distinguish them from investigative uses;
explain concrete equipment, cost and cleanup conditions where they affect the
verification choice. Membership and dependencies belong in the catalog, and
selection and execution belong in the harness README.
