# `tests/` (test runner + suites)

This directory contains the repository test harness. The test suite is organized to answer three questions:

1. Does the built `dist/PolicyWitness.app` basically work end-to-end?
2. Did we break a contract (CLI shape, evidence artifacts, JSON output schema)?
3. Do queries, attempts and their comparison records retain the observations each scenario establishes?

Cases write structured JSONL events and reports; the public dispatcher assembles
a per-run summary under `tests/out/`. [AGENTS.md](AGENTS.md) explains how to
choose checks, change tests, evaluate evidence and clean up output.

## Directory map

| Path | Contents |
| --- | --- |
| [run.sh](run.sh) and [catalog.json](catalog.json) | Public command and case membership, prerequisites and dependencies. |
| [suites/](suites/) | Suite entrypoints, assertions and local READMEs; indexed in [suite coverage](#suite-coverage). |
| [fixtures/](fixtures/README.md) | Specimens, independent observations and fixture builders. |
| [lib/](lib/) | Shared dispatch, capture, validation, artifact and cleanup helpers. |
| [COVERAGE.md](COVERAGE.md) and [FAILURE-PROPAGATION-CONTRACT.md](FAILURE-PROPAGATION-CONTRACT.md) | Outcome coverage and evidence ownership. |
| [OPT_IN_TESTS.md](OPT_IN_TESTS.md) | Resource-sensitive and mutation controls. |
| [RETAINED.json](RETAINED.json) | Committed retention index, outside disposable output. |
| `out/` | Local run and release-acceptance evidence, including cleanup staging. |

Related docs:

- CLI contract: [controller/README.md](../controller/README.md)
- Runner architecture: [runner/README.md](../runner/README.md)
- Build and signing: [docs/BUILD.md](../docs/BUILD.md)
- Release and notarization: [docs/SIGNING.md](../docs/SIGNING.md)
- Limits inventory and checks: [docs/LIMITS.md](../docs/LIMITS.md)
- Executable request-contract lesson: [docs/REQUEST-GRAMMAR.md](../docs/REQUEST-GRAMMAR.md)

## How to run

The default battery requires a signed app. The build command is:

```sh
make build IDENTITY='Developer ID Application: ...'
```

The public test commands include:

```sh
make test
# or:
./tests/run.sh
./tests/run.sh --suite integration
./tests/run.sh --suite unit
./tests/run.sh --all --list
./tests/run.sh --case blackbox_menagerie/validation_controls
```

Offline selections, such as `unit` and the menagerie validation controls, do
not require an app. Each selection's `--list` plan gives its prerequisites.
Build setup and signing requirements are in [docs/BUILD.md](../docs/BUILD.md).

`tests/run.sh` is the public selection and reporting interface. With no selectors
it runs the default battery. `--all` selects every registered case, including
opt-ins. Repeated `--suite NAME` and `--case SUITE/CASE` selectors form a union;
order and repetitions do not change the work. A suite selects all its members,
including any opt-in members. Case IDs are exact harness identifiers, not
patterns. Rust and Swift unit methods remain inside their respective batch cases.

`--list` prints the selected plan as JSON, including descriptions, default
membership, prerequisites, runner contexts, dependencies, and configuration.
`selection.suites` records the caller's suite selectors; `containing_suites`
maps selected cases to every suite containing them. Membership does not imply
that the caller selected that entire suite.
`--all --list` discovers the complete catalog. Help, inspection, invalid arguments,
invalid configuration, and missing entrypoint scripts leave existing evidence
untouched. `--describe` is not supported.

The catalog is `tests/catalog.json`. A case has one canonical ID; suites may
include the same ID, so shared validator-failure cases execute once even when
both suites are selected. BYOXPC cases have distinct IDs and runner contexts.
Selecting a BYOXPC specimen also selects its installation dependency, visible in
`--list`. Independent cases continue after failures. Required equipment missing
at execution is a failed run with an explicit unrun case, never an implicit skip.
For ordinary cases, Ctrl-C during command execution stops the active command's
process group and cancels queued work. Completed and partial evidence survives;
the failed summary accounts for unfinished selections with an interruption reason.

When a selection requires the app or embedded worker, the dispatcher first
requires the complete bundle layout, valid local codesign signatures, and
matching embedded manifest hashes. Invalid artifacts block those cases; offline
cases can still run. A shared read-only inspector also backs `preflight`.
The dispatcher inventories the selected app before testing and again during
finalization, including after case failures or Ctrl-C. Added, removed, or changed
files, modes, directories, and symlink targets fail the run with a retained diff.
Inspection never repairs the app or regenerates its evidence.
These checks do not certify notarization and cannot detect a transient mutation
restored before the final inventory. Direct suite scripts do not have this guard.

[Opt-in cases](OPT_IN_TESTS.md) are selectable by exact case, owning suite,
`--suite opt_in`, or `--all`. Direct suite scripts
remain developer entrypoints, but do not provide the public command's planning,
configuration validation, or completion guarantees.

Release ZIP acceptance is a separate explicit command:
`bash tests/accept-release.sh dist/PolicyWitness.zip`. It inspects a temporary
extraction, checks the staple and Gatekeeper assessment, runs the existing allow
and deny contracts through the extracted controller, and records the ZIP hash
and before/after integrity. It never builds or signs. `make release` runs it as
part of the notarization chain, then runs the default battery against the final
app and archives the release; `make publish` publishes an archived release. See
[docs/SIGNING.md](../docs/SIGNING.md) for the complete release procedure and the
handling of delayed or uncertain Apple replies.

## Configuration

- `PW_APP_DIR`: app bundle to test; defaults to `dist/PolicyWitness.app` when
  using `tests/run.sh` directly. `make test` uses `$(DIST_DIR)/PolicyWitness.app`
  unless `PW_APP_DIR`, `PW_BIN` or `PW_BIN_PATH` is supplied.
- `PW_BIN` and `PW_BIN_PATH`: compatibility aliases for the controller inside
  that bundle. Either can infer the app when `PW_APP_DIR` is absent. All supplied
  paths must agree after resolution; a standalone controller is rejected because
  tests also exercise its bundled helpers. Rust and shell tests receive the same
  resolved controller and app paths. Whole-app symlinks are supported; a
  controller symlink must stay inside its named bundle, including when a
  controller alias supplies the app path implicitly.
- `PW_TEST_OUT_DIR`: output directory, default `tests/out/runs/default`. Named
  disposable runs use `tests/out/runs/<name>`. Explicit paths must stay within
  `tests/out`, without symlink redirects or path escapes, and cannot overlap the
  tested app. Execution replaces only eligible output; inspection is read-only.
- `PW_TEST_RUN_ID`: evidence label; unset or empty generates one. It does not
  create a separate output directory. Labels start with a letter/digit and use
  at most 128 letters, digits, dots, underscores, or hyphens, because specimen
  fixtures embed them in paths and SBPL literals.
- `PW_TEST_QUIET=1`: suppress routine case messages. `0`, empty, or unset retains
  them. Selection, errors, and the summary remain visible.
- `PW_BYOXPC_IDENTITY`, then `IDENTITY`: signing identity override for signing
  tests; otherwise resolve an available Developer ID matching the app's team.

Shell entry points validate a nonempty inherited `SDKROOT` before starting
any developer-tool shim, and refuse an unresolved SDK request with status 2.
This includes direct suite scripts and release acceptance through the shared
shell test library.
[shim_probe.py](lib/shim_probe.py) provides contained commands and prepared
profiles for SDK/developer-directory probes, with a shared detector for sent
or blocked installation requests; its launch instructions are in
[AGENTS.md](AGENTS.md#sandboxed-automation-harnesses). From Python, a test can
add the one fixed rule that makes `hw.optional.arm64` unreadable, so the build's
native builder check refuses inside the same containment; the profile is then
also gated on both sysctl reads, outside and inside it.

Relative paths resolve from the repository root regardless of the caller's
working directory. The effective paths are recorded in `plan.json` and
`run.json`. Runner-mode/service overrides, suite aliases, case selection state,
and event paths (`PW_TEST_RUNNER_*`, `PW_TEST_SUITE_OVERRIDE`, `PW_TEST_CASES`,
`PW_TEST_EVENTS`) belong to child execution and are rejected as public settings.
The catalog selects BYOXPC runner contexts.

## Retention, ownership and execution locking

`tests/RETAINED.json` is the committed retention index, outside disposable output.
It has `schema_version: 1` and a `runs` array. Each entry records `path` relative
to `tests/out`, `run_id`, a nonempty `reason`, `source` (the full tested commit
hash, or null when unknown), and `app_inventory` (a run-relative evidence path,
or null when unavailable). Paths stay protected even when their directories are
absent locally. A missing, malformed or unreadable index prevents replacement.
Targets equal to, containing or inside a retained path are refused before any
output is changed. Symlink redirects and path escapes are rejected.

An optional `release` field marks a direct managed run or acceptance directory
for release-checkpoint cleanup: a `v<major>.<minor>.<patch>` value identifies its
release. An omitted or null value explicitly pins the entry. The archive helper
marks both the release battery and acceptance for expiration at a later checkpoint.
Ordinary pruning protects all indexed entries, regardless of this field.
Archive helpers replace the validated index atomically while holding the
checkout lock.

The dispatcher writes `owner.json` first, with its run ID, resolved output path
and start time. Only a matching, valid terminal `run.json` establishes completed
output. Failed cases and ordinary Ctrl-C cancellation still produce terminal
records and are disposable when unretained. A missing terminal record leaves an
interrupted run; malformed or inconsistent evidence leaves ambiguous output.
Nonempty output without ownership is unmanaged. Replacement refuses all three.
The explicit unfinished-prune command below handles owned unfinished output.
Placement under `runs/` alone does not establish ownership. Planning refusals exit 2.

After read-only planning, execution takes an OS-held advisory lock on
`tests/.checkout.lock`, rechecks retention and output eligibility, and holds the
lock through finalization. The file stays in place between operations; the held
lock belongs to its inode. PID, start time and the acquisition nonce in the owner
record identify the outermost owner, and its socket identity binds the
admission channel; closing the last descriptor releases the
lock, while run records determine completion. Nothing unlocks explicitly,
because an explicit unlock by one holder would also end a hold shared with a
child that holds the same descriptor.

Acquisition, nested admission and protected launches belong to
`tests/lib/checkout_lock.py`. An owner is a live process whose scope holds the
lock: it took the lock without blocking, or the owner of an inherited claim on
this checkout admitted it by handing over the held descriptor over a private
channel created at launch. Its socket identity must match the acquisition
record and the kernel-reported channel peer PID must match
the acquisition owner; nested scopes pass that original channel onward, so
the original owner's exit ends admission even while descendants hold the
lock. Environment values only locate a claim; a claim
whose owner is gone, a stale, closed or foreign descriptor, a wrong nonce or
another checkout's claim refuses, and admission never takes a free lock. The
dispatcher holds its scope through execution and passes the descriptor to each
case it launches, so a killed dispatcher's case keeps the lock until the case
and its descendants exit; a Python wrapper between a case and a tool that
mutates managed state must pass the claim's descriptors on, because Python
closes them in its children by default.

`build.sh` holds the same lock from its admission through packaging, so one
checkout runs one build or one execution at a time: a competing build or
execution gets a checkout-busy error before any cache or distribution
mutation, even with a different output path. A direct build hands itself to
`tests/lib/checkout_lock.sh`, the shell front end that records the caller's
`SDKROOT`, `CPATH`, `LIBRARY_PATH`, `MANPATH` and `LC_CTYPE` as an exact
environment witness and starts the developer directory's Python directly,
with locale coercion disabled. The CLI owner and build session start refuse
a missing or changed witness; neither restores values. Nested front ends
witness their own caller. The dispatcher resolves the same direct Python
independently and records no witness; cases that build use the front end.
The hold lasts until the last compiler or tool that holds the descriptor
exits, even when the owner and the script are killed first. A standalone Cargo
invocation against the managed `controller/target/` goes through the same
front end, which takes the lock or is admitted under an inherited claim:

```sh
tests/lib/checkout_lock.sh -- cargo test --manifest-path controller/Cargo.toml
```

Alternatively isolate both outputs and intermediates (`CARGO_TARGET_DIR` and
`CARGO_BUILD_BUILD_DIR`) outside the managed areas. Release acceptance, the
battery, archiving and rotation each take the lock in turn; `make release`
holds no outer lock. Separate worktrees have independent locks. Help and
`--list` remain available while a build or an execution holds the lock.

Direct shell entrypoints default to `tests/out/runs/direct`; they do not replace
output or provide dispatcher ownership/completion guarantees. Release acceptance
keeps unique directories under `tests/out/release-acceptance/run-*`; its nested
`tests` output passes the same dispatcher checks. An outer `owner.json` and
`acceptance.lock` protect extraction, tests and finalization as one lifetime;
process exit releases the lock, and normal return records the completion time.
Passing acceptance prints a suggested index entry.

## Pruning disposable output

```sh
tests/run.sh --prune
tests/run.sh --prune --apply
# After inspecting an interrupted or ambiguous managed run:
tests/run.sh --prune --apply --unfinished <name>
make prune
make prune APPLY=1
```

Preview prints a read-only JSON snapshot with `delete`, `keep: retained`,
`keep: interrupted`, `keep: ambiguous`, and `keep: unmanaged` dispositions.
It does not create a lock file or hold the checkout lock while classifying. If
execution holds the lock, `checkout_busy` is true and runs without a terminal
record are labeled `keep: active or interrupted`.

Preview briefly takes and releases the same nonblocking lock to observe
contention. An execution starting during that probe can receive checkout-busy
and exit 2. The reported busy state is a snapshot and can change
before classification or a later apply operation.

Apply takes the checkout lock and re-evaluates eligibility. It removes only
completed, unretained managed directories directly under `tests/out/runs/`.
Failed cases and terminal Ctrl-C runs remain eligible; crashed runs lacking a
terminal record remain available for inspection. `--unfinished <name>` explicitly
removes one interrupted or ambiguous run with valid ownership after the same
retained-overlap checks. It rejects completed, retained, unmanaged, redirected,
or missing targets. This is the supported way to deliberately remove unfinished
output; it preserves serialization with other mutating operations.

Apply reports actual `removed` paths and `failures`; a failed deletion exits 1
and reports the surviving path. Invalid requests, invalid indexes and checkout
contention exit 2. `--apply` requires `--prune`, `--unfinished` also requires
`--apply`, and pruning cannot be combined with selection or `--list`.

Standalone files anywhere in `tests/out`, including inventory JSON files, are
preserved. Output outside `runs/`, including release acceptance, is reported as
unmanaged and kept. Symlink redirects are never traversed or deleted.
`make prune` delegates to the preview command; `make prune APPLY=1` delegates
to `tests/run.sh --prune --apply` and follows exactly these rules. Any other
supplied `APPLY` value, including an empty value, refuses before the pruner
runs. Release acceptance, retained and unfinished evidence stay protected.

Successful release packaging invokes `tests/lib/release_rotate.py` once, after
verifying the new archive. It keeps that release's working acceptance and
battery plus the newest completed local output, including failures; completion
timestamps determine newest and ties are kept. Other owned run and acceptance
directories can be removed, including interrupted or ambiguous output started
before the release battery. Active acceptance, newer unfinished work, explicit
pins, unknown ownership and pending external-runner cleanup remain protected.
Older marked release entries are retired from the index, including absent ones.

Fresh test runs never trigger cleanup of other directories. There is no schedule,
age threshold, size threshold or off-machine backup requirement. Output may
accumulate throughout a refactor until the next successful release packaging.
The ordinary explicit pruner above retains its separate, more conservative
ownership rules and does not select a newest run to keep.

The durable cleanup journal lives at `dist/archive/<tag>/evidence/rotation.json`;
staged deletions live under `tests/out/.release-rotation/`, which ordinary
pruning preserves. Reapplying the same archived release resumes the transaction;
completed journals are no-ops. [The release procedure](../docs/SIGNING.md#portable-test-evidence-and-release-cleanup)
describes recovery.
Scratch contents follow [.tmp/AGENTS.md](../.tmp/AGENTS.md) and are outside this operation.

## Tiers

- **Baseline**: ordinary default cases on supported hosts, including offline
  checker controls and live smoke, black-box, and witness contracts.
- **Opt-in**: resource-sensitive signing/launchd work or implementation mutation
  controls. Some otherwise Baseline suites also own opt-in cases; `--list` gives
  each case's exact default membership and requirements.

## Suite coverage

This map summarizes each suite's observations and limits. Linked suite READMEs
own detailed assertions and fixtures; [COVERAGE.md](COVERAGE.md) maps outcome
values to their checks. [catalog.json](catalog.json) and the selected `--list`
plan are authoritative for exact membership, prerequisites and dependencies.
Equipment below is an overview: cases within a suite can have different needs.

Missing prerequisites fail the public run with explicit unrun cases. The only
supported live skip is an absent annotated menagerie mismatch after the other
evidence checks pass, including when those cases run through BYOXPC.

| Suite | Tier | Coverage and limits | Equipment overview | Reference |
| --- | --- | --- | --- | --- |
| `preflight` | Baseline + opt-in | Bundle signatures, layout, evidence hashes and the provenance record against the bytes; offline controls over the lock, stamp, fresh-mode, Cargo-judgment, SDK, signature-display and record readers; release acceptance, publication and cleanup controls; opt-in build guard, refusal and toolchain-switch controls that drive the unchanged build script, and a translated-build refusal control that needs Rosetta. Inspection is read-only; mutations use copies. | App for inspection; clang for the offline helper controls; signing identity and toolchains for opt-ins, Rosetta alone for the translated-build control; offline release controls vary. | [Suite](suites/preflight/README.md) |
| `source_drift` | Baseline | Source manifests, direct Python ancestry, test registry, documentation contracts, generated copies and their rejection controls. Mechanical agreement does not establish runtime behavior. | Python; Meson for source and build checks. | [Suite](suites/source_drift/README.md) |
| `shell_helpers` | Baseline | Case setup, command/result logging, wrapper sequencing, prerequisite failures and cleanup ownership through independent controls. | Python and shell; codesign for a prerequisite control. | [Suite](suites/shell_helpers/README.md) |
| `dispatcher` | Baseline | Selection, execution, reports, cancellation, artifact integrity, retention and locking determine one accounted result. | Python, clang and macOS process/socket observation; no app. | [Suite](suites/dispatcher/README.md) |
| `unit` | Baseline | Rust controller/helper contracts, orchestration calls, envelope shape and formatting. Constructed inputs cover interpretation and refusal branches. | Cargo and rustfmt. | [Suite](suites/unit/README.md) |
| `runner_unit` | Baseline + opt-in | Swift host admission, drivers, lifecycle and evidence encoding; actual transfer replies cross Rust/Python readers. Constructed build-receipt layouts need only Python. Internal SKIP/FAIL output fails the wrapper. | Swift; driver case also needs clang, Cargo and a signed app, without XPC. Launch-descriptor ownership controls require the signed worker. Isolated host setup faults, descriptor collisions and opt-in oracle-sensitivity, confirmed-reap and exec-reader mutations use Swift/clang without the app. | [Suite](suites/runner_unit/README.md) |
| `integration` | Baseline | CLI and runner envelopes for the request fixtures. | App and XPC. | [Suite](suites/integration/README.md) |
| `runner_apply_isolation_v2` | Baseline | Empty-plan SBPL v2 deny-default application, surviving reply, worker PID consistency and clean exit. No populated attempt results. | App and XPC. | [Suite](suites/runner_apply_isolation_v2/README.md) |
| `runner_apply_isolation_v3` | Baseline | The same empty-plan application and reply contract using SBPL v3. | App and XPC. | [Suite](suites/runner_apply_isolation_v3/README.md) |
| `runner_outcome_worker_spawn_failed` | Baseline | A nonexistent worker path retains the real spawn failure, admitted override and absence of a worker. | App and XPC. | [Suite](suites/runner_outcome_worker_spawn_failed/README.md) |
| `runner_outcome_runner_timeout` | Baseline | Empty-plan timeout retains termination evidence, diagnostics and empty steps; populated-plan controls live elsewhere. | App and XPC. | [Suite](suites/runner_outcome_runner_timeout/README.md) |
| `runner_outcome_bad_request` | Baseline | CLI/direct-XPC admission refusals, current accepted requests, and independent effects only for admitted plans. | App and XPC. | [Suite](suites/runner_outcome_bad_request/README.md) |
| `runner_ready_byte_resilience` | Baseline | A delayed ready-byte write survives a closed reader and still permits application, prediction and a clean reply. | App and XPC. | [Suite](suites/runner_ready_byte_resilience/README.md) |
| `runner_filter_iokit_registry_entry_class` | Baseline | Unavailable prediction with retained file-open attempt evidence; does not establish IOKit enforcement. | App and XPC. | [Suite](suites/runner_filter_iokit_registry_entry_class/README.md) |
| `runner_filter_sysctl_name` | Baseline | Unavailable prediction beside a real denied sysctl attempt; independent checker controls cover all filter callers. | App/XPC for live case; Python for controls. | [Suite](suites/runner_filter_sysctl_name/README.md) |
| `runner_filter_iokit_user_client_class` | Baseline | Unavailable prediction with a file-open placeholder; does not establish IOKit enforcement. | App and XPC. | [Suite](suites/runner_filter_iokit_user_client_class/README.md) |
| `runner_filter_local_name` | Baseline | Unavailable prediction beside a completed Mach lookup; this does not calibrate a local-name filter against enforcement. | App and XPC. | [Suite](suites/runner_filter_local_name/README.md) |
| `sandbox_extensions_native` | Opt-in | Independent native extension lifecycle, file effects, issuer lifetime and allocation observations; no production integration claim. | clang, macOS SDK and Developer ID identity. | [Suite](suites/sandbox_extensions_native/README.md) |
| `validator_bridge` | Baseline | Native query forwarding and acknowledged query/emission/closure gates, with independent native/process observations. | clang and macOS SDK. | [Suite](suites/validator_bridge/README.md) |
| `validator_batch_mode` | Baseline | Batch framing, per-query outcomes and continued processing after errors; native calls retain the no-report flag. | App. | [Suite](suites/validator_batch_mode/README.md) |
| `failure_boundaries` | Baseline | Admission capacities, receiver structure/association, escaped strings, refused-plan effect exclusion and independent helper admission. | App and XPC. | [Suite](suites/failure_boundaries/README.md) |
| `runner_outcome_validator_no_reply` | Baseline | A real validator deadline retains a partial ordered prediction and releases both independently observed attempts. | App, XPC and Python. | [Suite](suites/runner_outcome_validator_no_reply/README.md) |
| `runner_validator_failure` | Baseline | Partial replies retain step association and completed effects across shortfall, malformed output and signal termination. | App, XPC and Python. | [Suite](suites/runner_validator_failure/README.md) |
| `runner_abi_layout` | Baseline | Compiled C layout agrees with Swift, identity copies and the golden; validator query boundaries and Unicode round trips. | clang and macOS SDK; no app. | [Suite](suites/runner_abi_layout/README.md) |
| `runner_c_worker_harness` | Baseline + opt-in | Direct worker application, shared-memory publication, release barrier, refusal, policy delivery acknowledgement and exec-resource/budget controls. Separate deterministic clock, proceed, exec and sysctl controls compile production worker code with controlled time or native calls. The opt-in case observes the continuous clock natively under deny-default profiles. | App, embedded worker and clang; the opt-in case also reads unified logging. | [Suite](suites/runner_c_worker_harness/README.md) |
| `runner_use_c_worker` | Baseline | CLI-to-worker evidence, request refusals, timeout with completed effects, query planning and exec arguments/streams. | App and XPC. | [Suite](suites/runner_use_c_worker/README.md) |
| `runner_mach_service_liveness` | Baseline | Direct Mach-service host launch stays alive; does not establish that it services a connection. | App. | [Suite](suites/runner_mach_service_liveness/README.md) |
| `runner_byoxpc` | Opt-in | Owned external-runner installation, shared smoke/blackbox contracts, authentication, entitlements and registry recovery. Cleanup verifies removal. | App, GUI launchd session and matching signing identity for installation. | [Suite](suites/runner_byoxpc/README.md) |
| `smoke` | Baseline + opt-in | Built-app contract versions, build stamp and ordinary specimens; opt-in caller-auth checks use identical-client controls and independent effects. | App and XPC; whole-suite selection also needs a matching signing identity. | [Suite](suites/smoke/README.md) |
| `blackbox_e2e` | Baseline | Complete correlated envelopes and separate prediction/attempt assertions; independent checker and build-comparison controls. | App/XPC for live cases; controls have separate equipment. | [Suite](suites/blackbox_e2e/README.md) |
| `blackbox_menagerie` | Baseline | Local PAWL policy fixtures, evidence correlation and annotated canonicalization mismatches; checker controls run independently. | App/XPC for live cases; Python for validation controls. | [Suite](suites/blackbox_menagerie/README.md) |
| `sbpl_allowdeny_consistency` | Baseline | Independent file snapshots across restored seeds and reversed policy bindings, then JSON evidence checks. Mach steps establish presence only. | App and XPC. | [Suite](suites/sbpl_allowdeny_consistency/README.md) |
| `runner_live_worker_identity` | Baseline | Kernel socket identity and ancestry locate live worker/host processes; independent sandbox queries are compared with reported records. | App, XPC and clang. | [Suite](suites/runner_live_worker_identity/README.md) |
| `runner_exec_dac` | Baseline | Direct and PW execution retain permission failures without sandbox attribution; native scope controls distinguish target admission and exec prerequisites. | App and XPC. | [Suite](suites/runner_exec_dac/README.md) |
| `exec_fixture` | Baseline | Independent helper output, process identity/exit, state forwarding and file-write controls; tree cleanup must leave unrelated trees alive. | clang, Python and macOS process/socket observation; no app. | [Suite](suites/exec_fixture/README.md) |
| `run_capture` | Baseline | Exact CLI bytes/arguments/status, separate harness deadlines, overlapping captures and cleanup after failure. | Python and macOS process/socket observation; no app. | [Suite](suites/run_capture/README.md) |
| `runner_specimen_isolation` | Baseline | Overlapping specimens with identical step IDs retain separate process identities, file effects and evidence; controls reject swaps and combined faults. | App, XPC, clang and Python. | [Suite](suites/runner_specimen_isolation/README.md) |
| `run_effects` | Baseline | Independent before/after file observations for allowed/denied attempts; plain runs leave the runner registry and launchd plists unchanged. | App/XPC and fixtures for live cases; Python for controls. | [Suite](suites/run_effects/README.md) |
| `runner_exec_lifecycle` | Baseline + opt-in | CLI exec deadlines stop observed helper trees, preserve output and allow later effects; early EOF, surviving descendants and worker death are covered, including an opt-in combined EOF/leader-exit observation. | App, XPC, clang and Python. | [Suite](suites/runner_exec_lifecycle/README.md) |
| `runner_exec_inheritance` | Baseline + opt-in | Children report isolated environments/descriptors and usable streams; controlled resources and opt-in mutations establish leak detection; opt-in production launch inventory records accessible worker state and observer boundaries; a closed-worker-stderr probe characterizes child delivery. | App/XPC for CLI and launch inventory; clang/Python for worker and mutation controls. | [Suite](suites/runner_exec_inheritance/README.md) |
| `opt_in` | Opt-in | Selection of all non-default catalog cases. | Varies by case. | [Registry](OPT_IN_TESTS.md) |
| `witness_contract` | Baseline + opt-in | Per-phase ordering and fresh planning, native extension lifecycle/interruption, combined faults and token confinement, bounded collection, independent query/attempt effects, comparison limits, partial evidence, diagnostics, dossier and log correlation; opt-in barrier mutations, BYOXPC dossier and independent native path-query observations. | App/XPC and toolchains for live cases; signing/GUI for applicable opt-ins; offline cases vary. | [Suite](suites/witness_contract/README.md) |

## Shared test infrastructure

### Shell case setup and checking

Shared shell startup rejects Python with assertions disabled (for example,
`PYTHONOPTIMIZE=1`) with exit 2 before changing output or running cases. Direct
Python helper invocations bypass shell startup. Independent startup controls
live in `shell_helpers`.

`tests/lib/case.sh` provides baseline prerequisite checks, logged command
execution, fixture builds through their existing scripts, and Python checker
invocation. Cases retain their steps, argument lists, artifact paths, and final
pass statements. A failed stage writes a failed report and exits immediately;
it does not depend on the wrapper's `set -e`. Direct scripts retain the optional-app
helpers in `testlib.sh`; the public dispatcher enforces catalog prerequisites and
rejects undeclared skips. [shell_helpers](suites/shell_helpers/README.md) documents
the API and independent controls.

`test_begin` exports `PW_TEST_SCRATCH` as the case's `scratch/` path without
creating it. Public finalizers remove that directory for pass, fail and skip
before writing terminal evidence; interrupted cases retain it inside their run.
Sources, logs and receipts belong in `PW_TEST_ARTIFACTS`.

### SwiftPM build receipts

`tests/lib/build_receipt.py` queries SwiftPM with the producer's own Swift
command and explicit `--scratch-path`, verifies that the named product exists under scratch, that
the package has no `.build`, and that scratch is outside the producer's output
and under `PW_TEST_SCRATCH` when set. It records the resolved scratch/product
paths, product SHA-256 and query command in `build-receipt.json`, with query
diagnostics in `build-location.log`. Receipts survive finalization; products
do not. For successive builds of one copy the receipt describes the final
variant, after its output and outcome checks have been retained and passed.
Host setup and launch-descriptor controls query earlier because they need the
product path to run their checks. Constructed `runner_unit/build_receipt_controls`
independently exercise placement and command forwarding without Swift.

### CLI capture

`tests/lib/run_capture.py` prepares the supplied specimen and captures the public
CLI command, raw stdout/stderr, exit status, timing, and harness intervention.
Separate start/wait operations support overlapping runs. The caller supplies CLI
arguments and a test-side wait deadline, decides when to decode JSON, and owns
all outcome assertions and independent observations. Cleanup runs after those
observations. [run_capture](suites/run_capture/README.md) documents the API,
artifact contract and independent controls.

### Black-box validation

`blackbox_e2e`, `blackbox_menagerie`, `runner_specimen_isolation`, the
`witness_contract` prediction-target case, and the three `runner_filter_*` suites
share `tests/lib/blackbox.py` for envelope checks, step
identity/order, evidence fields and types, and explicit per-step expectations.
Each suite owns its policy, file-observation, denial, and skip rules. The helper only collects
errors; it neither runs PolicyWitness nor chooses expectations. Nullable path
fields remain present, while attempt `error` text is optional.
Black-box and filter controls exercise checker CLIs without importing the helper
or production code. Isolation controls call the suite adapter with separately
recorded witnesses. Both approaches require combined faults to remain visible.
Black-box and isolation controls also compare ordered/reordered response pairs:
only the order diagnostic may change, preserving actual step failures without
inventing others. Diagnostic order is unconstrained.
The filter suites use the `unavailable_prediction.py` CLI adapter, supplying
step identity, operation, filter value and a supported file-open, denied-sysctl
or allowed-mach-lookup attempt contract; the adapter accepts only the current response
and envelope versions. Their independent controls run through
[runner_filter_sysctl_name](suites/runner_filter_sysctl_name/README.md) before
its optional app check.

The menagerie's end-to-end specimens come from local copies of PAWL evidence.
It covers SBPL ingestion, probe execution, and evidence correlation, including
negative controls and canonicalization-boundary cases where mismatches are
recorded as evidence. An absent annotated mismatch can skip only after all
evidence checks pass. Its [suite README](suites/blackbox_menagerie/README.md)
describes the invariants and fixtures.

### Equipment checks

The dispatcher checks visible equipment, including app and worker binaries,
toolchains, a GUI session, a signing identity and Rosetta. It does not
preflight XPC reachability or log access: a blocked live case runs and fails
with evidence, while an unconfirmed `gui` prerequisite leaves the case
explicitly unrun. `rosetta` holds only when a shell started with
`arch -x86_64` reads `sysctl.proc_translated` as `1`; a launch error, timeout,
failure or other value is missing equipment, nothing is installed, and the
probe's record stays with the invocation in `run.json`. Only
`preflight/translated_build_refusal_controls` requires it.
[Automation guidance](AGENTS.md#sandboxed-automation-harnesses) covers diagnosis
and rerunning under an unsandboxed shell.

## Output contract (`tests/out/`)

An executing invocation of `tests/run.sh` replaces eligible output in its selected
directory so tooling can read stable paths. `<run>` defaults to
`tests/out/runs/default` and is configurable through `PW_TEST_OUT_DIR`. Help,
`--list`, and rejected commands preserve it:

```text
<run>/
  owner.json
  plan.json
  run.json
  dispatch.json
  events.jsonl
  artifact-integrity/  # when selected cases require app/worker
    inspection.json
    before.json
    after.json
    changes.json
  suites/<suite>/<test_id>/
    report.json
    events.jsonl
    artifacts/...
    scratch/...       # disposable build state; removed at case finalization
```

`owner.json` establishes run ownership as described in the
[retention contract](#retention-ownership-and-execution-locking).
`plan.json` records the selection before execution. `dispatch.json` journals each
command invocation, expected cases, execution status, report snapshots, and
harness errors. Most cases execute in separate processes; BYOXPC leaves share
installation and cleanup. The installation case is also a selected dependency.

`run.json` retains reports/counts and includes the plan, effective configuration,
invocations, harness errors, and one `case_results` entry per selected case.
The configuration's `python` entry is the interpreter the dispatcher resolved
(path, real path and version); every `report.json` carries an `interpreter`
entry from the case's own resolution, and a report that names another real
path is the `interpreter_mismatch` harness error.
`artifact_integrity` records initial validity, final equality, evidence location,
and artifact errors, or is null for an entirely offline selection. Artifact errors
fail `ok` independently of case reports; incomplete inspections retain diagnostics
instead of claiming equality.
`idle_sleep_assertion` records the `caffeinate -i` helper that blocks idle sleep
while the executor runs, and each invocation and its `case_results` record
`system_sleep_ms`, how long the system slept while the command ran. A `SLEEP:`
line names an invocation that slept and marks a failure in it as not creditable
product evidence; sleep never changes a status or `ok`. The
[dispatcher contract](suites/dispatcher/README.md#contract) describes both.
Distinct catalog cases must use distinct report paths; collisions are rejected
before output is replaced. The executor also refuses ambiguous report ownership
and checks complete, unique selection accounting before reporting success.
`completion` counts selected, completed (pass or fail reports), skipped, and
unrun cases. These are separate from readable-report counts: a missing report
cannot disappear merely because no report was available to count.

Started cases need one terminal event and a matching report. Unselected reports,
reused paths, malformed or contradictory evidence, silent commands, crashes,
unrun selections, and undeclared skips fail. A declared skip requires a matching
`skip_reason` in the report. Current live skips are limited to the menagerie's
absent annotated mismatch after evidence validation. There is no skip-policy flag.
`run.json.ok` and the shell exit agree: zero failed reports and zero harness
errors. Exit 2 means planning/configuration was rejected before execution.
Readable terminal reports also trigger a case-directory scan without following
links: a retained `.build` directory records `build_tree_in_evidence`, and a
remaining case `scratch` path records `scratch_retained`. These harness errors
leave reported case statuses unchanged and make `run.json.ok` false.
The [dispatcher suite](suites/dispatcher/README.md) documents the independent controls.

BYOXPC sessions use durable private registries. The opt-in
`runner_byoxpc/default_location` case alone exercises the shared default registry;
`bad_neighbor_claims` and `single_use` establish re-acquisition under contention.

## Comparing native builds

Four scripts under `tests/lib/` record build inputs, prepare candidate apps
and compare their structure and observed envelopes. `meson_receipts.py BUILDDIR OUT`
records tool versions, the resolved toolchain, the manifest and options,
effective build options, declared and active targets, every compile and link
command, the output hashes and minimum versions, and each output's entry in
Ninja's log. `native_compare.py exe CANDIDATE BASELINE` compares two
executables by structure (libraries with their versions, load commands,
segments and sections, code and data sizes, undefined symbols, `_sandbox_*`
imports and Swift module names) and `native_compare.py app CANDIDATE
BASELINE` compares two assembled apps; with `--across-builds` the sizes are
recorded rather than enforced because the sources differ, and attributing
those differences to source changes is a separate review. The offline
`blackbox_e2e/native_comparison_controls` case checks the structural
comparer's boundaries. `native_substitute.py` makes a signed, disposable
copy of an app with the four native executables replaced, for `PW_APP_DIR`
test runs. `envelope_compare.py` runs the request fixtures through two apps
and compares their envelopes: field presence, types and list lengths must
agree, including empty containers; permitted scalar differences are reported
by class; client commands and arguments must agree except for the executable
path and service name, which must match each envelope's provenance; the log
predicate may differ only in its recorded worker PID. The offline
`blackbox_e2e/comparison_controls` case checks those boundaries.

Structural comparison does not establish behavioral equivalence. Repeated Swift
builds of identical sources can differ in bytes.

These receipts are test evidence about a native build directory, broader
than the shipped record and not shipped: `meson_receipts.py` keeps every
compile command, the environment's `PATH` and tool output on failure, none
of which belongs in the bundle. The provenance record the build embeds
(`Contents/Resources/Evidence/provenance.json`, described under
[evidence artifacts](../docs/SIGNING.md#evidence-artifacts)) is the bounded
counterpart: the selected tools' reports, the configuration, each build
directory's state and the shipped outputs' load commands, architectures and hashes, with
Cargo's reuse judgment per target. A receipt can explain a difference the
record only names; the record can be recovered from an accepted release,
which a receipt cannot.

Two checks read `meson.build` and therefore need Meson on `PATH`, declared as
equipment in the catalog: the `source_drift` suite compares every target's
source list with the tree, and the opt-in order-barrier mutation control
compiles its hosts from the host's list.

## Comparison evidence coverage

Consumer evidence coverage follows the
[comparison record ownership table](FAILURE-PROPAGATION-CONTRACT.md#comparison-record).
`tests/lib/consumer.py` validates one envelope and selects steps by field
using explicit classification tables over the raw channel fields, without
consulting specimen policies or calling the runner classifier.
`tests/lib/phase_evidence.py` checks collection status against validator
disposition and presence for both the consumer and lifecycle oracle. It is
independent of the Swift encoder and Rust disposition reader; all three
implementations exercise the hand-reviewed `contract/phase_collection.json`
fixture through their enclosing reply/claim checks.
Recovered spawn-failure records retain their numeric codes, paths and
diagnostic text. Explicit evidence-loss replies omit that record along with
steps and subprocesses. Controlled scenario expectations stay in the CLI/witness
cases; Swift tests enforce
encoding and absence, and Rust tests enforce receiver/correlation preservation.
Shared blackbox checks enforce universal version/shape guarantees. The blackbox
checker controls retain rejected meaning-loss fixtures beside passing controls.

The comparison record's scenarios live in one fixture,
[tests/fixtures/comparison/matrix.json](fixtures/comparison/matrix.json):
every row names a live or constructed step, the expected six-field record, the
raw fields it rests on and an independent control. `witness_contract/comparison_matrix`
runs the live specimens through the CLI and checks every live row's record, raw
fields and file effects; S09 is constructed-only defensive coverage because
public admission refuses unsupported attempts. `runner_unit`'s
`ComparisonEvidenceTests` reads the same rows against the Swift encoder; the shared `tests/lib/consumer.py`
validates every record against its raw channel fields and `order` against the
ordering chain. The [failure contract](FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
names which case owns which rows and invariants. Step identity, independent
file/process observations, native results and partial-evidence protections
remain separately asserted.

The default `witness_contract/log_query_predicate_archive` case requires the
committed [query archive and independent manifest](fixtures/deny_capture/README.md).
It performs read-only OS queries against that fixture. Missing data or
incompatible readers fail explicitly.
