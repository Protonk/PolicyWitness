# Meson migration plan

## Recommendation and scope

Introduce Meson in three chunks: a C pilot, the Swift compilation slice, then
production integration. Meson will own four native executables and one shim
library. Keep `make` as the operator interface, Cargo as the Rust builder, and
`build.sh` plus the existing release helpers as the assembly and release path.

The benefit is an explicit, inspectable source/dependency graph, header-aware
incremental builds, and native outputs outside the source tree. The recorded
unchanged build takes about seven seconds; compilation accounts for most of
that, but signing, evidence generation and packaging will still run.

| Chunk | Scope and resulting ownership | Promotion gate | Difficulty confidence |
| --- | --- | --- | --- |
| 1: C pilot | Meson builds comparison copies of the worker and validator. Production still uses `build.sh` compiles. | Structural/incremental checks and a signed-copy pilot | High: the probe exercised the compilation and a signed-copy rehearsal. |
| 2: Swift slice | Meson also builds the shim, client and host; source checks read both manifests. Production still uses `build.sh` compiles. | Default battery on a substituted copy; source and barrier controls | Medium: Swift compiled in the probe; reader changes remain untried. |
| 3: cutover | `build.sh` consumes Meson outputs and removes its native compile commands. | Signed artifact, behavioural comparison and release-chain acceptance | Medium: integration is small; acceptance is the substantial work. |

This document specifies proposed work; the migration has not been implemented.
The [evidence appendix](#evidence-appendix) contains observations recorded by the
planning investigation at `06fc25e`, not acceptance of future implementation.
Each chunk below includes its required code, documentation and verification
work. Shared verification procedures are defined once and referenced by name.

Protect request/reply semantics, worker/validator separation, process lifetimes,
entitlements, compiler/platform assumptions and bundle paths. Do not introduce
CI, publication work, a Cargo wrapper target, or another release route.

## Build boundaries and final ownership

[build.sh](build.sh) currently interleaves native compilation with bundle
assembly. Move only the compilation responsibilities in the first three rows.

| Responsibility and inputs | Current output/owner | Owner after cutover |
| --- | --- | --- |
| C worker: `controller/tools/pw_probe_runner/pw_probe_runner.c` and its headers | `build.sh` writes `pw-probe-runner` beside the source | Meson executable in `builddir/` |
| C validator: `controller/tools/sb_api_validator/sb_api_validator.c` | `build.sh` writes `sb_api_validator` beside the source | Meson executable in `builddir/` |
| Swift client, Swift host, C shim: source lists in `build.sh`'s `XPC_RUNNER_*` declarations and compile calls | Client and host compiled directly into the app/XPC bundle; shim object in the Swift module cache | Meson executables `pw-runner-client`, `PWRunner`, and static library `PWCWorkerShim` in `builddir/`; shim linked into host |
| Rust controller, observer and SBPL checker; stamp environment | Cargo writes `controller/target/release/` | Cargo, still invoked directly by `build.sh`; [build.rs](controller/build.rs) retains stamp dependencies |
| Limits, contract and architecture checks | `build.sh` runs the three generators with `--check` before compilation | Unchanged; stale tracked text must refuse the build before any Meson command |
| Host/worker identity | [generate_worker_identity.py](docs/generate_worker_identity.py) writes regions in the ABI header, `CWorker.swift` and `tests/lib/contract.py` | Same generator, run by `build.sh` before compilation and checked again before signing |
| Git stamp, signing identity selection, inspection setting | `build.sh` reads git, keychain and environment | Unchanged; translate `PW_INSPECTION` to Meson's boolean `inspection` option, preserve Cargo's `RUSTFLAGS` handling, and retire `SWIFT_MODULE_CACHE` in favour of a module cache under `builddir/` |
| Bundle skeleton, plists, binary copies, augments | `build.sh` assembles `dist/PolicyWitness.app` | Same owner and destinations; native binary copies read Meson outputs |
| Nested signing, evidence generation, outer seal | `build.sh`, [build-evidence.py](tests/build-evidence.py) | Unchanged order; evidence hashes signed helpers and is sealed by the outer app signature |
| Verification, standalone observer signing, checked guide staging, ZIP | `build.sh` | Unchanged |
| Notarize, staple, accept, archive, retain/rotate, publish | [Makefile](Makefile), `notarize.py`, `tests/lib/release_*.py`, [accept-release.sh](tests/accept-release.sh) | Unchanged procedures and safeguards |

The final build order is: documentation checks → identity generation → git
stamp → signing identity selection → build options → Cargo → Meson → bundle
assembly → identity check → nested signing → evidence → outer seal and
verification → standalone observer signing → guide → ZIP. Keep the Makefile's
`build` recipe dispatching to `build.sh`; retain its useful comments and guards.

Generation stays outside Meson because it writes tracked source regions or
checks them, rather than producing build-directory artifacts. Identity changes
can update both the worker's ABI header and the host's Swift source; Meson must
track both. Cargo already owns its incremental build. Assembly and release
steps have order-sensitive safeguards that a scheduler wrapper would not improve.

Other compilation stays where it is: [runner/Package.swift](runner/Package.swift)
is test-only; fixture builders and per-suite `clang` calls build test equipment,
including deliberately mutated sources, into evidence directories. Keep the
manual ad hoc-signed debugger helper at
[controller/tools/sb_api_validator/build.sh](controller/tools/sb_api_validator/build.sh)
unless its separate retirement is chosen below.

## Entry conditions and review decisions

Start by reading [AGENTS.md](AGENTS.md), `build.sh`, the Makefile,
[signing procedures](docs/SIGNING.md), [test procedures](tests/README.md), and
[source-drift generator contracts](tests/suites/source_drift/README.md#generator-contracts).
Read [runner/AGENTS.md](runner/AGENTS.md) before touching runner test machinery.
Recheck the inspected sources against the current checkout; do not depend on a
scratch probe still existing.

The recorded default baseline at `06fc25e` completed 168 cases: 167 passed and
`unit/rust.fmt` failed on formatting in `controller/src/runner_commands.rs`.
That file has since been formatted with `cargo fmt`, the app rebuilt and
re-signed, and the battery rerun; the [evidence appendix](#evidence-appendix)
records both runs. Re-establish a green baseline at the actual starting
commit before crediting any green-battery promotion gate.

The following choices are settled and are not review items:

- **Tooling.** Add Meson and Ninja. The minimum is the exercised pair, Meson
  1.12.1 and Ninja 1.13.2, declared as `meson_version: '>=1.12.1'`. A lower
  minimum is a separate change that must be exercised before it is claimed.
  Preserve Command Line Tools support, Cargo and the system Python used by
  existing scripts.
- **Module cache.** `SWIFT_MODULE_CACHE` retires at cutover. Swift module
  caches and the shim object live under `builddir/`, which is writable
  wherever Meson can build at all. `build.sh` keeps the variable until then.
- **Shim placement.** The shim is a Chunk 2 target, built alongside its only
  consumer, the host. Chunk 1 compiles the two C executables.
- **Architecture citations.** Chunk 3 adds a source-kind `meson_build` node
  with one edge to `drift_check`, citing `meson.build` as a source and the
  source-drift check as the verifying rule. `generator_common.FORM_RULES`
  stays unchanged.

These are review choices, with recommended assumptions for the implementation.
Settle the applicable choices before their chunk; they are not claims that
approval has already been given.

| When | Decision | Recommended assumption |
| --- | --- | --- |
| Before Chunk 1 | File and output locations | Root `meson.build` and `meson.options`, ignored root `builddir/`. The manifest must be above the sources it names. |
| Before Chunk 1 | Identity coverage | Add both Meson files to the conservative source digest immediately and regenerate after each chunk. Keep existing inputs. |
| Before Chunk 2 | Compile-only `make native` convenience | Optional; omit unless wanted. If added, it must prepare generated identity inputs and use the same option mapping as production. |
| Before Chunk 3 | `BUILD_XPC=0` scope under Meson | Deferred to implementation. Preserving the Swift discovery skip needs a Meson option gating `add_languages('swift')` and a reconfigure on toggle; skipping only the Swift compile is simpler. Prefer the simpler form unless discovery proves costly. Either way a `BUILD_XPC=0` bundle is not a release artifact. |
| Before Chunk 3 | Notarization timing | Recommend one cutover rehearsal. Alternatively use the next real release, with release-chain acceptance explicitly pending until it succeeds. |
| Optional follow-up | Manual validator debugger script | Keep it during this migration; retirement is a separate choice. |

Adding Meson files to the identity digest changes generated identity values
even while production still compiles through `build.sh`. Chunks 1 and 2
preserve the production compiler route and runtime contract; they do not
promise unchanged shipped bytes. Always compare host and worker built from
the same regenerated source state.

For all chunks, use fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` directories,
preserve receipts, and serialize test execution under the existing checkout
lock. Cheap compile checks require no signing or notarization credentials.
Signed-copy promotion requires a Developer ID identity; notarization is
reserved for the final gate. Follow the repository's sandbox-escalation
guidance for keychain, signature, XPC or log restrictions.

## Chunk 1: C compilation pilot

**Scope and rationale.** Build the two C executables under Meson as
comparison outputs. They are small, isolated compilation units; the worker
also exercises identity coverage early. The shim waits for its consumer in
Chunk 2. `build.sh` remains the production compiler, assembler and signer.
Prerequisites are the Chunk 1 decisions above, the current source baseline,
and Meson/Ninja plus Apple's C toolchain.

**Work, in order:**

1. Add the root build manifest and options, and ignore `builddir/`. Declare
   explicit sources using the settings below. The pilot needs only C;
   introduce Swift and the shim when adding their targets in Chunk 2.
2. Add `meson.build` and `meson.options` to `SOURCE_FILES` in
   `docs/generate_worker_identity.py`. Run
   `python3 docs/generate_worker_identity.py` and commit its three generated
   regions together with the inputs. Do not edit generated regions manually.
   Extend the identity controls in `tests/suites/source_drift/contract.py`
   to demonstrate that edits to the new flag/option owners change the digest.
3. Add small, reusable structural and normalized-envelope comparison scripts
   to the test machinery, implementing the [shared verification procedures](#shared-verification-procedures).
   Save raw inputs and explicit differences. These scripts support all three
   chunks; they do not assemble a second production app.
4. Update `docs/SIGNING.md` with the chosen Meson/Ninja requirements and
   comparison-build commands; describe production as still using `build.sh`.
   Add `meson.build` to the Build + signing router in `AGENTS.md`.
   Keep generated-document edits at their authoritative inputs.

| Target/setting | Required declaration |
| --- | --- |
| Project defaults | `buildtype=plain`, `warning_level=0`, `b_ndebug=false`; `meson_version: '>=1.12.1'` |
| `sb_api_validator` | Its one C source; `-Wall -Wextra -O2 -std=c11` |
| `pw-probe-runner` | Its one C source; same flags; `-lsandbox`; compiler dependency tracking for all included headers |
| `inspection` | Boolean option, default true; will select Swift `-Onone -g` versus `-O` in Chunk 2 |

**Must remain unchanged.** Production compile commands, `EXECUTABLES`, bundle
layout, signing, evidence semantics, and worker linking against libsandbox.
Ignore the build directory from the start: generator controls copy untracked,
nonignored files into disposable checkouts.

**Cheapest useful validation.** After identity regeneration, run
`meson setup builddir`, `meson compile -C builddir`, then compile again and
require no work. Compare the C outputs with current `build.sh` outputs using
the structural check. The worker invoked without arguments must retain exit
2 and the `--shm-fd is required` diagnostic. Inspect
`meson introspect meson.build --targets`; touch `pw_worker_evidence.h` and
verify that only the worker rebuilds. Run `tests/run.sh --suite source_drift`
with a fresh output directory, including the extended identity controls.
Do not treat the expected linker-induced byte differences as a failure;
unexplained structural differences block promotion.

**Acceptance before promotion.** Build a baseline app through the existing
signed path after regeneration, then use the signed-copy procedure below to
replace its worker and validator. Against that copy, run:

```sh
PW_APP_DIR='/private/tmp/<copy>/PolicyWitness.app' \
PW_TEST_OUT_DIR='tests/out/runs/<fresh-name>' \
tests/run.sh --suite smoke --suite runner_c_worker_harness \
  --suite validator_batch_mode --suite runner_abi_layout \
  --suite runner_live_worker_identity --case witness_contract/happy_path_baseline
```

Require all selected cases to pass, no skips/unrun cases or harness errors,
and the candidate app inventory to remain unchanged. Compare the five
`tests/fixtures/pw_runner/` requests through both same-source apps using the
envelope procedure. Record results from the real root manifest; the scratch
rehearsal is supporting evidence only. No notarization is needed.

**Rollback/stop.** Revert the pilot files, identity input list, comparison
tooling and documentation changes together, then regenerate identity and
rebuild as needed. Production has never consumed Meson outputs. Stop here if
structural checks fail or the tooling cost is not worth the C slice.

## Chunk 2: Swift compilation and source-manifest readers

**Scope and rationale.** Add the shim library, the client and the host, and
make the Meson source inventory visible to existing checks. This is where
most compile time and source-list maintenance move. XPC compilation belongs
here; XPC bundle assembly remains in `build.sh`. Both build systems still
compile their own outputs, and only `build.sh` outputs ship.

**Prerequisites.** Chunk 1 accepted; read the runner test instructions and
choose whether to add `make native`. Expect more integration work than the
pilot: Swift output requires structural/behavioural comparison and three
source-list consumers must change.

**Work, in order:**

1. Enable Swift and add the shim and both Swift targets below. Preserve the
   explicit source order from `build.sh` so the review can compare lists
   directly.
2. In `tests/suites/source_drift/check.py`, add Meson readers using
   `meson introspect meson.build --targets`. Feed the relevant host Swift and
   shim C sets into `diff_sets` alongside disk and `build.sh`: three sets
   during this chunk. Filter to the same source domains as the existing
   readers; client/service entrypoints are not extra core sources.
3. In `check_planner.py`, copy the Meson files and any inputs their
   introspection needs into its disposable checkout. In
   `tests/suites/witness_contract/opt_in/mutations.py:build_host`, read the
   production host list from Meson and retain the assertion that it equals
   the on-disk core set. Preserve the mutation control's deliberate identity
   handling and its own compilation of test equipment.
4. Update `tests/suites/source_drift/README.md` and its `run.sh` descriptions
   for the three-way check. Update `runner/Package.swift` comments to name
   both temporary production/comparison lists, and `tests/OPT_IN_TESTS.md`
   to say the barrier control follows Meson's manifest.
5. If selected, add `make native` with accurate header/help comments. It
   runs the generator checks, prepares identity inputs, sets up/configures
   Meson and compiles, without signing or bundling. Keep one mapping of
   `PW_INSPECTION` to Meson's option for this entry point and the production
   cutover; do not create competing flag definitions.
6. Regenerate identity after the manifest and `Package.swift` edits.
   Include generated regions in this chunk.

| Target | Sources and settings |
| --- | --- |
| `PWCWorkerShim` | `static_library` from `runner/Sources/PWCWorkerShim/PWCWorkerShim.c`; preserve the current shim compile settings, distinct from the executables' flags |
| `pw-runner-client` | `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` and `runner/Clients/PWRunnerClient/main.swift`; `swift_module_name: 'main'` |
| `PWRunner` | The ten explicit `runner/Sources/PWRunnerCore/` Swift files listed by `build.sh`, plus `runner/Services/PWRunner/main.swift`; module name `PWRunner`; `link_with: cworker_shim` |
| Both Swift targets | `-module-cache-path` under the writable build directory; `inspection` chooses `-Onone -g` or `-O` |

**Must remain unchanged.** Host/core source membership, module names, compiler
optimization/debug settings, the host's absence of sandbox API imports,
test-only SwiftPM ownership, and all production assembly/signing. The probe
used a separate shim static library because its Swift target could not
contain C source directly.

**Cheapest useful validation.** Compile both inspection settings and perform
the structural comparison on client and host. Require matching dynamic
libraries/load-command structure, the stated module names in mangled symbols,
and no undefined `_sandbox_*` imports in the host. Exercise this matrix,
then run `tests/run.sh --suite source_drift`:

| Input change | Required incremental response |
| --- | --- |
| None | No native compile/link work |
| `pw_worker_evidence.h` touched | Worker rebuilds |
| `CWorker.swift` touched | Host rebuilds |
| `PWRunnerAPI.swift` touched | Client and host rebuild |
| Shim source touched | Shim rebuilds; host relinks |
| Identity input content changed, then identity regenerated | Worker and host rebuild from their changed generated inputs |
| `inspection` changed | Swift settings change; a no-op compile must not retain the previous flavour |

The first five rows were exercised by the probe. Content changes requiring
identity regeneration have wider consequences than an mtime-only touch;
verify those separately and restore/regenerate the source state afterward.

**Acceptance before promotion.** Substitute all four Meson executables into
a same-source signed app using the shared procedure. Run the full default
battery with `PW_APP_DIR=<copy>` and a fresh output directory, plus
`tests/run.sh --case witness_contract/order_barrier_mutations` against that
copy. Require the unmodified control to pass and both mutations to be
detected, as well as a green battery and unchanged app inventory. This
exercises the new manifest reader rather than merely its JSON parser.

**Rollback/stop.** Revert the shim and Swift targets, reader/documentation
changes and optional convenience target; restore the mutation reader and
regenerate identity. Keep the accepted C pilot. If Swift equivalence or
reader changes prove unsuitable, use the C-only endpoint below. Keep dual
compilation to one review cycle rather than treating this as a permanent
operating mode.

## Chunk 3: production cutover

**Scope and rationale.** Make `build.sh` consume the accepted Meson outputs
and remove its native compile commands in one reversible commit. This is
the first change to the compiler route used by the shipped app.

**Prerequisites.** Chunks 1 and 2 accepted, a green current baseline, and the
Chunk 3 review choices settled. Signing credentials and a logged-in GUI
session are needed for the full artifact/BYOXPC gate; settle notarization
timing before declaring release-chain acceptance.

**Work, in order:**

1. After the existing documentation, identity, stamp, keychain and Cargo
   steps, set up or reconfigure `builddir/` with the current options and run
   `meson compile -C builddir`. Keep `PW_INSPECTION` as the public knob;
   Meson reads its boolean option, not that environment variable.
   Preserve `BUILD_XPC=0` skipping the client/service build, with the
   discovery scope chosen in the review table, and keep custom `DIST_DIR`
   assembly working.
2. Replace the three `clang` and two `swiftc` invocations with consumption
   of the four executables. The shim is already linked into the host; it is
   not copied into the bundle. Preserve all existing binary destinations,
   plist stamping and source-independent assembly declarations.
3. Remove obsolete native source/flag declarations and the two in-tree
   executable ignores. Remove `build.sh` source readers from `check.py`;
   it now compares disk with Meson. Update copied-checkout inputs where
   necessary. Do not move Meson before the generator refusal gates.
4. Update `build.sh`'s input/output comments for Meson and the retired
   `SWIFT_MODULE_CACHE` variable. Update Makefile build comments while
   preserving its commands/guards; `README.md`'s assembly description;
   `docs/SIGNING.md`'s production build instructions; runner README/AGENTS
   and `Package.swift` comments; and source-drift README/run descriptions
   for the final two-way comparison. The build-stamp contract keeps its
   existing owner and semantics.
5. In `docs/architecture.json`, update the build node's guard description
   and add the settled source-kind `meson_build` node with an edge to
   `drift_check` labelled "source list equals the tree", citing Chunk 2's
   checking rule. Retain the existing build-generator, guide-staging and
   `sign_macho` anchors. Regenerate with
   `python3 docs/generate_architecture.py` (rendering needs Graphviz).
   Represent the checked source-list relationship, not a second compile
   graph; Meson introspection/Ninja can render that graph on demand.
6. Regenerate identity after all digested edits and include the generated
   regions. Keep `build.sh` and `Package.swift` in the digest.

**Must remain unchanged.** `sign_macho`, nested signing order, evidence
content model, `EXECUTABLES`, outer seal, guide/ZIP procedure and all release
targets. The stale-guide and stale-contract controls must still fail with
their expected diagnostics before any compiler, Meson invocation, or
distribution output; missing tools must not become the reason they pass.

**Cheapest useful validation.** Run `make build IDENTITY=...` twice; the second
Meson compile does no work and artifact inspection still passes. Switch
`PW_INSPECTION=0` and back, verifying the corresponding Swift settings.
Check `BUILD_XPC=0` retains its existing scope; a partial bundle is not a
release acceptance artifact. Run `tests/run.sh --suite source_drift`, including
the copied-checkout, generator-order and refusal controls.

**Acceptance before promotion:**

1. Build the complete signed app and require the full default battery against
   `dist` to pass without skips, unrun cases or harness errors.
2. Run `preflight/signed_artifact_controls`,
   `witness_contract/order_barrier_mutations`, `smoke/runner_caller_auth`,
   and the `runner_byoxpc` suite from a logged-in GUI session. Use exact
   `--case` selectors for the first three and `--suite runner_byoxpc`.
   Follow existing installation ownership and cleanup requirements.
3. Perform the shared artifact/envelope comparison against the current
   released build. The investigation used `dist/archive/v0.2.7/`; select
   and record the actual release baseline at implementation time.
4. Run `make notarize NOTARY_KEYCHAIN_PROFILE=<profile> IDENTITY=...` once,
   or credit the agreed next real `make release`. Keep the existing
   submission, stapling, Gatekeeper, re-zip and final ZIP acceptance receipts.
   `make notarize` rebuilds and accepts the ZIP; archiving and rotation
   belong to `make release`. No publication is part of this migration.
   If the rehearsal is deferred, record this gate as pending.

**Cutover and rollback.** Land the production switch as one commit. Reverting
it restores the `build.sh` native compiles; regenerate identity and rebuild
the app afterward. Its existing delete-and-recreate assembly prevents mixing
old bundle contents with new outputs. Do not add a runtime producer-selection
switch such as `PW_NATIVE`. The ignored Meson build directory can remain
inert after rollback.

## Shared verification procedures

### Structural and artifact comparison

For native outputs, compare `otool -L` dynamic libraries, `otool -l`
load-command/segment/section structure, `size`, and undefined `_sandbox_*`
imports from `nm -u`. For Swift, also check the module names in mangled
symbols. Preserve the comparison as a script from Chunk 1 onward and rerun
it when toolchains change. A compile success alone is insufficient.

The probe reported Meson adding
`-Wl,-dead_strip_dylibs -Wl,-headerpad_max_install_names`. Its C output bytes
differed from the old path despite matching measured structure and behaviour.
Repeated direct Swift builds also differed in bytes. Therefore whole-binary
byte equality is not the acceptance gate.

For assembled apps, require `tests/lib/artifact.py:inspect` to pass. Compare
evidence-manifest `(id, kind, rel_path)` inventories and entitlements,
`symbols.json` exported `_pw_*` markers, and per-executable imports,
libraries and load-command structure. Plists should differ only in accounted
build stamps and, for temporary signed copies, their fresh identifiers.
Signatures, timestamps and content hashes need not equal the old artifact;
each manifest must describe its own actual signed bytes.

### Signed-copy substitution

Use the pattern in
[mutations.py:signed_copy](tests/suites/witness_contract/opt_in/mutations.py):

1. Build a baseline app from the current regenerated sources. Copy it with
   `ditto` to a disposable location under `/private/tmp`, replace the
   selected native executables, and assign fresh app/service bundle IDs.
2. Sign replaced helpers/client as applicable, then the service with its
   existing entitlements. Run `tests/build-evidence.py`, sign the outer app
   with its entitlements, and run `codesign --verify --deep --strict`.
3. Require artifact inspection before running the chunk's test selection with
   `PW_APP_DIR` pointing at the copy. Retain receipts and before/after
   inventory under the managed test output. Leave `dist` intact.

The worker and validator remain under
`Contents/XPCServices/PWRunner.xpc/Contents/MacOS/`; the host is alongside
them and the client is under the app's `Contents/MacOS/`. Bundle-local helper
resolution must work for both the built-in service and BYOXPC copies.

### Envelope comparison and its limits

Run all five request fixtures under `tests/fixtures/pw_runner/` through both
apps. Validate envelopes first with [tests/lib/consumer.py](tests/lib/consumer.py).
Retain originals and compare normalized leaves, including every comparison
record, verdict, attempt outcome and disposition.

The rehearsal identified these variable classes: PIDs; wall-clock/monotonic
times and deadlines; durations; observer raw log output and deny lines;
temporary-copy bundle/service names and paths; the client argv; and
`stdout_bytes_*` affected by longer identifiers. Across builds, account for
the four stamp values too. Use explicit field paths and explain every
excluded difference; these classes are not permission to discard arbitrary
strings or evidence records. A changed source identity is an expected
provenance change to verify against its own sources, not a volatile value
to silently erase.

The built-in runner's `data.specimen.binaries` dossier was null in the
rehearsal; it is populated for BYOXPC. Use artifact inspection for the
built-in app's manifest baseline.

Passing these checks supports the tested structural and behavioural claims.
It does not prove program equivalence, timing under load, or behaviour beyond
the exercised cases. Local tests do not certify Apple's notarization
acceptance; only the final release-chain gate supplies that evidence.

## Smaller endpoint and remaining risks

A C-only cutover is an acceptable endpoint if Swift support or reader changes
cost more than they return. Retain the accepted C targets, leave the shim and
Swift compile commands and their source readers in `build.sh`, and adapt
Chunk 3 to consume the two C executables. Preserve C-manifest checks
for any ownership that did move. Repeat the relevant signed-app, identity and
release gates; the fact that the slice is smaller does not waive them.

| Risk | Where it is handled |
| --- | --- |
| Meson/Swift upgrades change implicit arguments or shim linking | Structural comparison in every chunk and after toolchain changes; C-only endpoint if unsuitable |
| Configuration retains the previous inspection setting | Explicit reconfiguration and option-switch checks in Chunk 3 |
| Source readers pass with incomplete manifests or fail for unrelated missing files | Chunk 2 three-way comparison, copied-checkout controls and barrier mutations before removing old readers |
| A claimed build edge becomes unchecked documentation | Architecture citations point to source-drift rules; identity controls and ABI/live-identity tests provide distinct evidence |
| Temporary duplicate flag ownership persists | Chunk 2 is limited to one review cycle; proceed to one production route or revert the Swift slice |
| New tool requirements exceed demonstrated compatibility | The minimum equals the exercised Meson/Ninja pair; preserve Command Line Tools support despite the probe using full Xcode |

## Evidence appendix

These are recorded observations from the original investigation, separated
from the implementation gates above. They have not been rerun merely to
reorganize this plan.

**Environment and scope.** At `06fc25e` on 2026-10-07: macOS 26.7.1
(Darwin 25.6.0), Xcode 27, Apple clang 21.0.0, Swift 6.4, Cargo 1.99 from a
keg-only rustup, system Python 3.9.6, Meson 1.12.1 and Ninja 1.13.2.
The probe compiled real sources through symlinks in `.tmp/meson-probe/`.
Scratch contents are disposable; the implementation must not rely on them.

**Measured cost.**

| Measurement | Recorded wall time |
| --- | --- |
| Build with Cargo recompilation / unchanged build | 11.4 s / 6.9 s |
| Generator checks / unchanged Cargo | 0.4 s / 0.04 s |
| Three C compiles / Swift client / Swift host | 0.25 s / 1.4 s / 3.2 s |
| Signing | About 0.18 s per timestamped call; seven calls |
| Evidence / ZIP | 0.2 s / 0.3 s |
| Meson setup / cold native build / no-op Ninja | 2.1 s / 4.3 s / 0.0 s |

**Probe findings.** Header tracking, isolated Swift rebuilds and shim relinking
behaved as shown in Chunk 2's first five matrix rows. Source introspection
worked without a configured build directory. The client needed module name
`main`; the host used `PWRunner` and a separate shim library. Structural
comparisons matched despite the binary differences described above. These
observations support the chosen scope; they do not establish support for
every earlier toolchain.

**Signed-copy rehearsal.** Meson-built worker and validator were substituted
into a freshly built same-commit app. Signing, evidence generation, signature
verification and artifact inspection succeeded. The selection comprised
`smoke/specimen_file_read_deny`, `witness_contract/happy_path_baseline`,
`runner_c_worker_harness`, `validator_batch_mode` and
`runner_live_worker_identity`: 36/36 cases passed, no skips or unrun cases,
unchanged candidate inventory, about 28 seconds. Evidence was recorded under
`tests/out/runs/meson-pilot-rehearsal`; the temporary script/app were removed.
This was narrower than the full Chunk 1 promotion selection.

The five fixtures were also run through both apps: all ten runs returned 0
with `normalized_outcome: ok`. Each envelope had 326–373 leaves, with 35–41
differences confined to the variable classes listed above; comparison
records, verdicts, attempt outcomes and dispositions matched.

**Default baseline.** `tests/out/runs/meson-plan-baseline` recorded the
168-case run in about 6.4 minutes, unchanged app inventory, no skips or unrun
cases, and the formatting failure described in the entry conditions. After
`cargo fmt` on `controller/src/runner_commands.rs` and a rebuild signed with
the same identity, `tests/out/runs/meson-plan-baseline-fmt` recorded 168 of
168 passing in about 7.0 minutes, with unchanged inventory and no skips,
unrun cases or harness errors.

**Source anchors.** The investigation read the build/signing/artifact sources
linked above; the four `docs/generate_*.py` generators and
[generator_common.py](docs/generator_common.py);
[controller/Cargo.toml](controller/Cargo.toml); `runner/Package.swift`;
[docs/architecture.json](docs/architecture.json); the source-drift
[checker](tests/suites/source_drift/check.py),
[planner control](tests/suites/source_drift/check_planner.py),
[generator controls](tests/suites/source_drift/generators.py),
[limits controls](tests/suites/source_drift/limits.py) and
[contract/identity controls](tests/suites/source_drift/contract.py);
the barrier mutation control; [suite_run.py](tests/lib/suite_run.py),
[release_preflight.py](tests/lib/release_preflight.py),
[release_accept.py](tests/lib/release_accept.py),
[tests/catalog.json](tests/catalog.json), [tests/OPT_IN_TESTS.md](tests/OPT_IN_TESTS.md)
and fixture builders under [tests/fixtures/](tests/fixtures/).
