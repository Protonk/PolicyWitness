# Meson migration plan

## Recommendation and scope

Introduce Meson in three chunks: a combined native compilation pilot,
source-manifest integration, then production cutover. Meson will own four
native executables and one shim library. Keep `make` as the operator interface,
Cargo as the Rust builder, and `build.sh` plus the existing release helpers as
the assembly and release path.

The benefit is an explicit, inspectable source/dependency graph, header-aware
incremental builds, and native outputs outside the source tree. The recorded
unchanged build takes about seven seconds; compilation accounts for most of
that, but signing, evidence generation and packaging will still run.

| Chunk | Scope and resulting ownership | Promotion gate | Difficulty confidence |
| --- | --- | --- | --- |
| 1: native pilot | Meson builds comparison copies of all four executables and the shim. Production still uses `build.sh` compiles. | Structural/incremental checks and the default battery on a signed copy | Medium: both languages compiled in the probe; its signed-copy rehearsal replaced only the C executables. |
| 2: manifest integration | Source checks compare disk, `build.sh` and Meson in the integration worktree; the mutation control reads the new manifest. This checkpoint does not land separately. | Source-drift and barrier controls; applicable signed-copy regression checks | Medium: the three readers and their disposable checkouts remain to be changed. |
| 3: cutover | `build.sh` consumes Meson outputs; Meson files enter the identity digest. | Local signed-artifact and behavioural checks before landing; user-run release validation afterward | Medium: integration is small; artifact and release acceptance are the substantial work. |

**Landing units.** Chunk 1 may land independently as an optional experiment.
Chunks 2 and 3 are sequential implementation/validation steps that land together
as one production-integration commit. The three-way source check is exercised
in the integration worktree before removing the old reader. Main never has
a state where its default test battery requires Meson but its production build
does not; the combined commit introduces the build/test tool prerequisites
together. Do not make failed introspection optional to bridge that transition.

Adopt Swift and C together or abandon the migration. The recorded C compiles
total about 0.25 s; the Swift compiles total about 4.6 s. More significantly,
`check.py:disk_swift_files` and `disk_c_files` guard the Swift core and its
shim, not the two standalone C executables. A C-only cutover would add build
tools while leaving that source-list maintenance and most rebuild cost intact.
Header tracking alone does not justify that endpoint for this project.

The first chunk therefore tests the useful, riskier slice immediately,
including the shim alongside its host consumer. The probe already established
that both languages can compile; the remaining question is whether the real
root manifest produces acceptable artifacts. These chunks separate compilation,
check integration and production ownership, rather than promising that language
boundaries produce a strictly increasing difficulty progression.

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
| Native compilation policy and supported variants | Native flags in `build.sh`; `PW_INSPECTION` and `BUILD_XPC` select variants | Meson declares and enforces fixed target settings; `build.sh` translates the two public knobs into `inspection` and `xpc` |
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

### Native configuration contract

A Meson directory retains configuration as well as incremental outputs.
`default_options` initializes values; it does not enforce project requirements.

- **Fixed native policy belongs to Meson.** Express mandatory target settings
  in declarations and shared `override_options`; use Meson configuration
  assertions for unsupported settings. Enforce `b_asneeded=false` on the C
  executable targets; defaults alone cannot protect consequential settings.
  Check effective optimization/debug settings, not just the `buildtype` label;
  reject unsupported native argument injection or instrumentation that would
  bypass the declared target policy. Keep the policy in the Meson files selected
  for identity at cutover, without a second flag table in `build.sh`.
- **Supported variants remain caller choices.** `build.sh` passes `inspection`
  and `xpc` explicitly on every setup/reconfigure. Meson maps those choices to
  target settings and membership; the shell does not repair fixed flags or
  duplicate their policy through introspection assertions.
- **A directory belongs to its configured toolchain.** Preserve Apple's
  `xcrun --sdk macosx` selection, including `DEVELOPER_DIR`, and check the selected
  compiler/SDK paths and versions against the directory's recorded configuration
  during setup/reconfiguration. Refuse a mismatch with instructions for a fresh
  directory or explicit reset; preserve matching directories for incremental
  builds. Check only languages needed by the selected variant: `xpc=false`
  must not discover Swift, and first enabling XPC adds Swift to the recorded
  configuration. Separate CLT, Xcode and experimental directories help isolation
  but do not enforce policy by their names.

Apply the policy checks on setup, reconfiguration and compile-triggered
regeneration. Supported build recipes reconfigure before reusing a directory;
changing the shell's toolchain environment then invoking bare Ninja/compile is
not a supported toolchain switch. Source-manifest introspection discovers
membership across branches; configured-directory introspection reports active
targets and configuration. Global options alone do not describe target overrides.

## Identity policy

**Add `meson.build` and `meson.options` to the digest only in Chunk 3, in
the same commit that makes them production compile inputs.** Experimental
manifests in Chunks 1 and 2 remain outside it. Record their contents, options,
tool versions and output hashes with the comparison evidence instead.

The [identity contract](docs/CONTRACT.md#internal-hostworker-identity) and
[generator](docs/generate_worker_identity.py) describe a conservative source
identity, not a computed dependency closure. It hashes the selected files in
full, excluding only generated identity bodies. It already includes the
test-only `runner/Package.swift`, and even comments change its value. Retain
that existing scope; the decision here is when to admit a new compile owner,
not to redefine the digest as production-only or include every experimental
file that could compile these sources.

Chunks 1 and 2 must leave all existing identity inputs and the three generated
copies unchanged. In particular, defer `Package.swift` comments, `build.sh`
edits and generator changes to Chunk 3. New comparison scripts belong outside
the digested source directories. Use
`python3 docs/generate_worker_identity.py --check` to check the starting state;
do not regenerate merely because an experimental Meson file changed.

At cutover, add the two inputs, extend the identity controls, update the
contract's input list and regenerate all copies together. Thus this migration
changes identity once, provided no separate source change is mixed into its
first two chunks. Unrelated changes to existing digest inputs still require
normal regeneration. Equal identities during the pilot establish agreement on
the selected sources; they do not certify equal compile flags or output bytes.

This remains true after cutover: `PW_INSPECTION` and compiler/SDK selection
already permit different builds of the same source identity. Keep the ignored
directory outside the digest. Configuration and command receipts belong with
migration acceptance evidence; expanding the shipped evidence schema into a
build-provenance record is a separate change.

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
  Preserve Command Line Tools support as an existing compatibility requirement,
  with the fresh-directory CLT compilation gate in Chunk 1. Full Xcode is not a
  new prerequisite. Preserve Cargo and the system Python used by existing scripts.
- **Module cache.** `SWIFT_MODULE_CACHE` retires at cutover. Swift module
  caches and the shim object live under `builddir/`, which is writable
  wherever Meson can build at all. `build.sh` keeps the variable until then.
- **Compilation scope.** The shim and its host consumer enter together in
  the combined Chunk 1 pilot. C-only adoption is not a fallback.
- **Compiler/linker policy.** Make consequential settings explicit, set
  `b_asneeded=false`, and accept only documented, inspected backend additions
  under the [compiler/linker policy](#compilerlinker-policy). Enforce these through
  the [native configuration contract](#native-configuration-contract) from the
  pilot onward; manifest defaults alone do not satisfy it.
- **No-XPC compatibility.** Preserve `BUILD_XPC=0`, including its lack of
  Swift discovery and its signed partial-bundle output. Gate Swift language
  registration and the shim/client/service targets with a boolean `xpc`
  option, default true. Replacing this workflow is outside this migration.
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
| Before Chunk 3 | Compile-only `make native` convenience | Optional; omit unless wanted. Add it with production integration so it can share the preparation and option mapping from the outset. Direct Meson commands suffice for the pilot. |
| Optional follow-up | Manual validator debugger script | Keep it during this migration; retirement is a separate choice. |

The preserved no-XPC workflow still builds Cargo and both standalone C
executables, checks a signing identity, recreates the app, and signs/packages
it when `BUILD_XPC=0`. It skips the shim, Swift client and service, and never
copies those C executables into that partial app. `build-evidence.py` tolerates
missing components, but `artifact.py:inspect` requires them for normal
artifact-dependent tests. Specimen execution, including BYOXPC, uses the
missing `pw-runner-client`. The AGENTS description "Rust-only iteration"
therefore does not describe a complete runnable/testable app or the actual
compile work.

Require Swift when XPC is enabled, and reconfigure when the option changes.
Use the partial-build checks below separately from complete-app acceptance.
Direct Cargo compilation already exists; replacing the partial-bundle workflow
with it or selected Meson targets requires a separate change.

For all chunks, use fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` directories,
preserve receipts, and serialize test execution under the existing checkout
lock. Cheap compile checks require no signing or notarization credentials.
Signed-copy promotion requires a Developer ID identity. Notarization and
release are user-run steps after the local cutover gate, as specified below.
Follow the repository's sandbox-escalation guidance for keychain, signature,
XPC or log restrictions.

## Chunk 1: combined native compilation pilot

**Scope and ownership.** Meson builds the worker, validator, client, host and
shim into an ignored build directory. `build.sh` continues to compile every
production native output and to assemble/sign the app. Source-manifest readers
still use `build.sh`. Test compilation and linking as one slice before changing
those readers or the production route.

**Prerequisites.** Current green baseline, Meson 1.12.1/Ninja 1.13.2, Apple's C
and Swift toolchains, and the file/output location choice above. Require a
current identity with `generate_worker_identity.py --check`. A stale starting
tree needs its own repair before beginning this chunk.

**Work, in order:**

1. Add root `meson.build`, `meson.options` and the `builddir/` ignore.
   Declare all targets below with explicit source lists, keeping the current
   host source order for straightforward review. Keep shim flags distinct
   from the two C executables' flags and apply the settled compiler/linker
   policy. Declare C in `project()`; register Swift with
   `add_languages('swift', required: true)` only inside the `xpc` guard.
   Implement the native configuration contract in this pilot, including
   toolchain-directory reuse checks and writable module caches during compiler
   discovery as well as target compilation.
2. Add reusable structural and normalized-envelope comparison scripts under
   test machinery, implementing the [shared verification procedures](#shared-verification-procedures).
   Preserve the [configuration and command receipts](#configuration-and-command-receipts),
   binary hashes, raw comparison inputs and explicit differences. The
   experimental build recipe is not yet represented by the source identity.
3. Update `docs/SIGNING.md` with comparison-build commands and the tool
   requirements for that optional path; production does not require Meson
   yet. Add `meson.build` to the Build + signing router in `AGENTS.md`.
   Do not change `Package.swift`, `build.sh`, the identity generator or
   any production source merely to support the pilot.

| Target/setting | Required declaration |
| --- | --- |
| Project/languages | C initially; `meson_version: '>=1.12.1'`; conditional Swift registration below |
| Fixed native policy | Effective plain build settings, `warning_level=0`, `b_ndebug=false`, `b_asneeded=false`; enforced by Meson target settings/assertions under the native configuration contract, not merely `default_options` |
| XPC option | Boolean `xpc`, default true; conditionally register Swift and declare the shim, client and host. Worker and validator remain unconditional. |
| `sb_api_validator` | Its one C source; `-Wall -Wextra -O2 -std=c11` |
| `pw-probe-runner` | Its one C source; same flags; `-lsandbox`; compiler dependency tracking for all included headers |
| `PWCWorkerShim` | `static_library` from `runner/Sources/PWCWorkerShim/PWCWorkerShim.c`; preserve optimization/debug/ABI settings under the compiler/linker policy; do not add an ineffective `pic: false` override on macOS |
| `pw-runner-client` | `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` and `runner/Clients/PWRunnerClient/main.swift`; `swift_module_name: 'main'` |
| `PWRunner` | The ten explicit `runner/Sources/PWRunnerCore/` Swift files listed by `build.sh`, plus `runner/Services/PWRunner/main.swift`; module name `PWRunner`; `link_with: cworker_shim` |
| Both Swift targets | `-module-cache-path` under the writable build directory; boolean `inspection`, default true, selects `-Onone -g` versus `-O` |

The probe used a separate shim static library because its Swift target could
not contain C source directly. Preserve this connection to the host rather
than treating the shim as a separate product.

**Must remain unchanged.** All existing digest inputs and generated identity
copies; production compile commands and source-list readers; core membership,
module names and compiler settings; worker libsandbox linking and the host's
absence of sandbox API imports; bundle layout, signing and evidence semantics.
Ignore the build directory immediately: generator controls copy untracked,
nonignored files into disposable checkouts.

**Cheapest useful validation.** Run `meson setup builddir`,
`meson compile -C builddir`, then compile again and require no work. Inspect
`meson introspect meson.build --targets` and compare all native executables
with same-source `build.sh` outputs using the structural check. Check Swift
module names and require no undefined `_sandbox_*` imports in the host.
The worker without arguments must retain exit 2 and the
`--shm-fd is required` diagnostic. Compile both inspection settings and
exercise this matrix:

| Input change | Required incremental response |
| --- | --- |
| None | No native compile/link work |
| `pw_worker_evidence.h` touched | Worker rebuilds |
| `CWorker.swift` touched | Host rebuilds |
| `PWRunnerAPI.swift` touched | Client and host rebuild |
| Shim source touched | Shim rebuilds; host relinks |
| `inspection` changed | Swift settings change; a no-op compile must not retain the previous flavour |

The first five rows were exercised by the probe. Use mtime-only touches for
these dependency checks; production source edits are outside this chunk.

Exercise the [configuration-state controls](#configuration-state-controls).
Then run the following CLT gate against the real root manifest, with the same
Meson/Ninja versions and `xpc=true`:

1. Select `DEVELOPER_DIR=/Library/Developer/CommandLineTools` for both setup
   and compilation in a fresh, separate ignored build directory. Use Apple's
   compiler selection and writable module caches; remove inherited overrides
   that would select Xcode tools or an Xcode SDK. Do not reuse an Xcode directory.
2. Record resolved C/Swift compiler and SDK paths/versions and verify they
   select CLT. Compile both C executables, the shim, client and host; inspect
   generated commands for accidental Xcode-app paths. Require a no-op second
   compile and run the same structural comparison against direct `build.sh`
   compile commands under the same CLT selection.
3. Preserve receipts with the pilot evidence. Missing CLT, a missing compiler,
   or a compilation failure leaves this gate unmet. The earlier scratch probe
   does not accept the root manifest.

In a fresh build directory with Swift discovery deliberately unavailable,
configure `xpc=false` and compile both C executables. Require no Swift discovery
or shim/client/host targets; a fresh `xpc=true` configuration under the same
conditions must fail for the missing compiler. With the normal toolchain,
reconfigure one build directory through true → false → true, checking target
membership and successful compilation at each step. Existing files from a prior
configuration must not stand in for active targets.

Run `tests/run.sh --suite source_drift` and identity `--check`; require
unchanged generated regions. Unexplained structural differences block promotion.

**Acceptance before promotion.** Build the baseline app through the existing
signed path, then replace all four executables using the shared signed-copy
procedure. Run the full default battery:

```sh
PW_APP_DIR='/private/tmp/<copy>/PolicyWitness.app' \
PW_TEST_OUT_DIR='tests/out/runs/<fresh-name>' tests/run.sh
```

Require all selected cases to pass with no skips, unrun cases or harness errors
and an unchanged candidate inventory. This includes the worker harness,
validator batch, ABI/layout, live-identity, Swift-unit and live witness checks.
Compare all five `tests/fixtures/pw_runner/` requests through both apps.
Record results from the real root manifest: the prior C-only signed-copy
rehearsal does not discharge this combined pilot's gate. No notarization.

**Rollback/stop.** Revert the new Meson files, comparison tooling, ignore and
documentation changes. There are no migration-generated identity changes to
undo, and production never consumed the new outputs. If Swift equivalence or
the combined graph fails, investigate within this pilot or abandon Meson;
do not ship a reduced C-only migration.

## Chunk 2: source-manifest integration

**Scope and ownership.** Keep the accepted compilation graph and production
route unchanged. Integrate Meson introspection into the source-drift checker,
its disposable-checkout control and the barrier mutation control. This isolates
the check machinery from the compiler experiment and from production cutover.

**Prerequisites.** Chunk 1 accepted; read `runner/AGENTS.md` and the existing
readers/controls. Develop this checkpoint in the same integration worktree as
Chunk 3. Its checks require Meson while the intermediate build still uses the
old compiler route; that temporary state is never a standalone commit on main.

**Work, in order:**

1. In `tests/suites/source_drift/check.py`, read the relevant host Swift and
   shim C sets through `meson introspect meson.build --targets`. Add them to
   `diff_sets` alongside disk and `build.sh`: three sets during this chunk.
   Filter to the existing source domains; client/service entrypoints are not
   extra core sources. Treat failed introspection or missing targets as errors.
   Always use file-mode introspection here and in the mutation reader. It sees
   the host and shim declarations across the `xpc` guard; introspection of an
   `xpc=false` build directory correctly omits them and is not a substitute.
2. In `check_planner.py`, copy the Meson files and any inputs introspection
   requires into the disposable checkout. Verify that its unmodified fixture
   still passes and its intended source mutations cause the expected refusals.
3. In `tests/suites/witness_contract/opt_in/mutations.py:build_host`, read
   the host list from Meson, preserve the assertion against the on-disk core
   set, and resolve those paths into the disposable mutated package. Preserve
   the control's deliberate identity handling and its own test compiles.
4. Update source-drift README/`run.sh` descriptions for the three-way check,
   `tests/OPT_IN_TESTS.md` for the barrier reader, and `docs/SIGNING.md`
   for Meson-dependent checks. Leave `Package.swift` comments alone: its
   description of the production `build.sh` list is still true.
   Its final owner wording changes only at cutover.

**Must remain unchanged.** Existing identity inputs and generated copies,
native compiler settings, production assembly/signing, and the mutation
oracle's positive/negative behaviour. No identity regeneration is part of
this chunk; reader/check changes are outside the selected digest sources.

**Cheapest useful validation.** Run `tests/run.sh --suite source_drift` and
identity `--check`. Exercise source-list mismatch and missing-target cases in
disposable manifests so the new reader cannot silently ignore an absent file.
Retain proof that planner refusals concern the intended rule rather than
incomplete copied inputs. Check that file-mode source membership is unchanged
whether no build directory exists or a local directory has `xpc=false`; check
active target membership separately through that configured directory.

**Acceptance before promotion.** Run
`tests/run.sh --case witness_contract/order_barrier_mutations` against the
accepted same-source Meson signed copy, with a fresh output directory.
Require the unmodified control to pass and both mutations to be detected.
Credit the Chunk 1 default battery only under
[the existing result-reuse rules](tests/README.md#reusing-verification-results):
identify changed readers/fixtures and rerun their affected cases. Rebuild the
copy and repeat affected artifact checks if any compilation input changed.
Do not automatically repeat unrelated cases or silently reuse changed ones.

**Completion/stop.** Keep this checkpoint's validation receipts, then proceed
directly to Chunk 3 in the integration worktree. Do not land Chunk 2 by itself.
If integration is abandoned, discard its reader/control changes and revert
Chunk 1; do not retain a permanent parallel compiler route. Keep the
experimental period within one review cycle before cutover or removal.

## Chunk 3: production cutover

**Scope and rationale.** Make `build.sh` consume the accepted Meson outputs
and remove its native compile commands. Land these changes with Chunk 2 as
one reversible commit, introducing the production and default-test Meson
requirements together. This is the first change to the compiler route used
by the shipped app.

**Prerequisites.** Chunks 1 and 2 accepted, a green current baseline, and the
Chunk 3 review choices settled. Signing credentials and a logged-in GUI
session are needed for the full local artifact/BYOXPC gate. No notarization
credentials or submission are required to land this chunk. The user owns the
later notarization/release run.

**Work, in order:**

1. Add `meson.build` and `meson.options` to `SOURCE_FILES` in
   `docs/generate_worker_identity.py`, retaining all existing inputs.
   Extend `tests/suites/source_drift/contract.py` so edits to either new
   input change identity and stale generated copies are refused.
2. After the existing documentation, identity, stamp, keychain and Cargo
   steps, set up or reconfigure `builddir/` with the current options and run
   `meson compile -C builddir`. Keep `PW_INSPECTION` as the public knob;
   Meson reads its boolean option, not that environment variable.
   Map `BUILD_XPC` to the boolean `xpc` option on every setup/reconfigure.
   Preserve conditional Swift discovery and the partial-bundle workflow;
   keep both C executables unconditional and custom `DIST_DIR` assembly working.
   Reuse only a directory accepted by Meson's configuration controls, and
   propagate any refusal before copying or signing native outputs. Do not
   migrate the fixed native policy back into shell flags or assertions.
3. Replace the three `clang` and two `swiftc` invocations with consumption
   of the four executables. The shim is already linked into the host; it is
   not copied into the bundle. Preserve all existing binary destinations,
   plist stamping and source-independent assembly declarations.
4. Remove obsolete native source/flag declarations and the two in-tree
   executable ignores. Remove `build.sh` source readers from `check.py`;
   it now compares disk with Meson. Update copied-checkout inputs where
   necessary. Do not move Meson before the generator refusal gates.
5. Update `build.sh`'s input/output comments for Meson and the retired
   `SWIFT_MODULE_CACHE` variable. Update Makefile build comments while
   preserving its commands/guards; `README.md`'s assembly description;
   `docs/SIGNING.md`'s production build instructions; runner README/AGENTS
   and `Package.swift` comments; and source-drift README/run descriptions
   for the final two-way comparison. Update `docs/CONTRACT.md`'s explicit
   identity input list; the build-stamp contract keeps its existing owner
   and semantics. Correct `AGENTS.md`'s "Rust-only iteration" shorthand and
   document the preserved no-XPC output, tool requirements and limited checks
   in `docs/SIGNING.md`, together with supported variants, CLT selection and
   toolchain-directory reset requirements. If selected, add `make native` with
   accurate header/help comments and shared generator preparation/inspection-option mapping.
6. In `docs/architecture.json`, update the build node's guard description
   and add the settled source-kind `meson_build` node with an edge to
   `drift_check` labelled "source list equals the tree", citing Chunk 2's
   checking rule. Retain the existing build-generator, guide-staging and
   `sign_macho` anchors. Regenerate with
   `python3 docs/generate_architecture.py` (rendering needs Graphviz).
   Represent the checked source-list relationship, not a second compile
   graph; Meson introspection/Ninja can render that graph on demand.
7. Run `python3 docs/generate_worker_identity.py` after all digested edits
   and commit its three generated regions with the cutover. This is the
   migration's first change to those regions; keep `build.sh` and
   `Package.swift` in the digest.
8. Prepare the factual cutover record and evidence pins described under
   Handoff below; they accompany the local gate, not a simulated release run.

**Must remain unchanged.** `sign_macho`, nested signing order, evidence
content model, `EXECUTABLES`, outer seal, guide/ZIP procedure and all release
targets. The stale-guide and stale-contract controls must still fail with
their expected diagnostics before any compiler, Meson invocation, or
distribution output; missing tools must not become the reason they pass.

**Cheapest useful validation.** Run `make build IDENTITY=...` twice; the second
Meson compile does no work and artifact inspection still passes. Switch
`PW_INSPECTION=0` and back, verifying the corresponding Swift settings.
Repeat the configuration-state controls through the production entry point,
requiring policy refusals to prevent bundle consumption of stale native outputs.
Repeat the pilot's missing-Swift and option-toggle checks through `build.sh`'s
option mapping. Build with `BUILD_XPC=0` into a separate `DIST_DIR`: require
both C outputs in the Meson directory, no shim/Swift targets, and a signed
partial bundle without the XPC service, client or embedded C helpers. Check
the expected partial evidence inventory and successful packaging separately;
the full artifact inspector must still reject this incomplete app. Restore
`BUILD_XPC=1` and verify complete-app acceptance. A partial bundle is not a
release acceptance artifact. Run `tests/run.sh --suite source_drift`, including
the copied-checkout, generator-order and refusal controls. In a disposable
source copy, change a Meson identity input, regenerate, and verify that the
changed ABI header and Swift identity cause both worker and host to rebuild.
Restore the candidate state before artifact acceptance.

**Local gate before landing on main:**

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
4. Finish the handoff record below, preserving exact tested source and
   artifact provenance. Once these local gates pass, the cutover may be
   committed with Chunk 2 and land on main even though release validation
   is pending. Do not leave an uncommitted implementation waiting for the user.

**Handoff and where pending is recorded.** At cutover, create the tracked
`records/MESON-CUTOVER-OBSERVATIONS.md` and link it from this plan only, following
[records/AGENTS.md](records/AGENTS.md). Record observed results and their limits:
the tested commit or base commit plus exact diff for a precommit build; build
stamp and artifact inventory/ZIP hashes; commands and paths to completed local
runs; and "local cutover checks passed; notarization and final ZIP acceptance
not run" if that is the state. Do not relabel precommit evidence with the SHA
of a later commit. State that linked test and distribution evidence is
gitignored and local.

Keep raw results in dispatcher-owned test directories. Pin the actual local
gate runs needed by the handoff in `tests/RETAINED.json`, under the checkout
lock and using its existing schema, with no `release` value. The index protects
evidence; it does not track pending tasks. Do not invent an unrun case, terminal
receipt, unmanaged run directory or extra status field. The tracked record
makes the handoff recoverable without chat and keeps historical observations
out of permanent behaviour documentation. It is an evidence record, not a
second active plan.

**User-run release validation after landing.** Hand the user the cutover commit,
local evidence record and the command
`make notarize NOTARY_KEYCHAIN_PROFILE=<profile> IDENTITY=...`, or defer to
their next real `make release`. The implementation agent does not run either
automatically. Recommend one rehearsal, but main need not wait for it and later
work may land. The user can rehearse the pinned cutover from a clean checkout
or validate the later release candidate; record which source was actually used.

The [Makefile](Makefile) deliberately has `make notarize` rebuild, then submit,
staple, validate, re-zip and accept that final ZIP. Its report-mode preflight
allows a rehearsal without a release tag. `make release` instead requires a
clean annotated release tag and also runs the battery, archive and rotation.
Neither requires an uncommitted cutover. Preserve both paths as they are.

When the user runs it, link the actual `dist/evidence/<attempt>/` receipts and
final `tests/out/release-acceptance/<run>/acceptance.json` from the record;
use the archive's paths if the attempt was archived. Record the accepted ZIP
hash and source. The [release evidence helper](tests/lib/release_evidence.py)
explicitly does not transfer acceptance to rebuilt bytes. If later changes
affect the compiled inputs or verification, rerun affected local checks under
the existing result-reuse rules. Failed or missing release evidence leaves
release validation outstanding; it does not retroactively erase the local
gate. A migration-caused failure must be fixed and revalidated or rolled back.
No publication is part of this migration.

**Cutover and rollback.** Land Chunks 2 and 3 as one commit. Reverting the
combined implementation restores both the `build.sh` native compiles and
the original source-list/mutation readers; regenerate identity and rebuild
the app afterward. Preserve the factual cutover/release record and evidence
pins when reverting implementation changes; record the rollback and any failed
acceptance rather than erasing those observations. The existing delete-and-recreate
assembly prevents mixing old bundle contents with new outputs. Do not add a
runtime producer-selection switch such as `PW_NATIVE`. The ignored Meson build
directory can remain inert after rollback.

## Shared verification procedures

### Compiler/linker policy

Require explicit consequential settings plus a documented, narrow set of
accepted backend additions. Preserve optimization/debug levels, language and
module settings, sandbox linkage, and Apple compiler/macOS SDK selection;
compare effective compile/link commands and platform targets as well as output
structure. Bare `clang -c` already relies on compiler/platform defaults, so
requiring every compiler decision to appear as an explicit flag is not a
meaningful equivalence rule.

Enforce `b_asneeded=false` through Meson target options to remove Meson 1.12.1's
additional `-dead_strip_dylibs`: unused-library removal is a semantic link decision
that this migration does not need. Accept and document
`-headerpad_max_install_names` as an Apple-backend addition, subject to the
artifact checks; there is no independent header-padding switch in that backend.
Do not replace native Meson targets with custom compiler wrappers merely to
make argument strings identical.

The shim's proposed PIC discrepancy does not occur on this Darwin toolchain.
The recorded shim command and a fresh minimal probe contain no added
`-fPIC`; bare Apple clang already selects PIC. Meson's
[static-library `pic` option](https://mesonbuild.com/Reference-manual_functions.html#static_library)
has no effect on macOS. Preserve the shim's existing optimization/debug/ABI
settings and inspect the actual command; `pic: false` would add no protection.
The [built-in options](https://mesonbuild.com/Builtin-options.html#base-options)
describe `b_asneeded` and other configurable policies. Record accepted argument
differences with the comparison evidence and explain their purpose beside the
manifest settings. Any new consequential difference requires explicit review;
structural similarity is not blanket acceptance of new flags.

### Configuration-state controls

In a disposable configured directory, change `b_asneeded` to true with
`meson configure`, then reconfigure and compile without passing a corrective
value. Require the C target link commands still to omit `-dead_strip_dylibs`
because of their declared overrides. A global introspection value of true is
not itself a failure when the target override is effective.

Change an asserted consequential setting to an unsupported value and require a
clear Meson refusal before compilation; exercise injected native arguments as
well. Restore the accepted configuration and require a successful build followed
by no work. These checks must work through direct Meson commands as well as the
Chunk 3 production entry point, without a shell repair step.

Exercise supported `inspection`/`xpc` changes as specified in the chunks. Change
the developer directory or compiler/SDK context, reconfigure, and require stale
directory reuse to be refused; a fresh directory under that selection must
configure and compile. Preserve the old directory. Re-establish these controls
and review argument differences after Meson/compiler upgrades.

### Configuration and command receipts

Keep these with managed migration acceptance output, linked from the pilot or
cutover record and bound to the exact compared native outputs by hashes:

- Manifest/options contents, selected public variants, effective build options
  and active target information from the configured directory.
- Meson/Ninja versions, resolved compiler paths/versions, selected developer
  directory and SDK path/version.
- Effective per-target compile and link commands, including target overrides,
  and the documented explanation of accepted differences from the old route.

Capture generated commands even for a no-op build. Global build options alone
do not describe target overrides. Receipts support provenance; configuration
controls enforce policy. The shipped evidence manifest and runtime envelope
remain unchanged.

### Structural and artifact comparison

For native outputs, compare `otool -L` dynamic libraries, `otool -l`
load-command/segment/section structure, `size`, and undefined `_sandbox_*`
imports from `nm -u`. For Swift, also check the module names in mangled
symbols. Preserve the comparison as a script from Chunk 1 onward and rerun
it when toolchains change, including a review of effective compiler/linker
argument differences against the agreed policy. A compile success alone is
insufficient.

The probe reported Meson adding
`-Wl,-dead_strip_dylibs -Wl,-headerpad_max_install_names`. Its C output bytes
differed from the old path despite matching measured structure and behaviour.
Repeated direct Swift builds also differed in bytes. Therefore whole-binary
byte equality is not the acceptance gate. Recheck outputs under the settled
flag policy; the probe's default link arguments are not the production policy.

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

1. Build a baseline app from the same current sources. Require identity
   `--check`; only Chunk 3 changes the digest inputs and generated copies.
   Copy it with `ditto` to a disposable location under `/private/tmp`, replace the
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

## Stop conditions and remaining risks

Proceed with the combined native graph or revert the experimental work.
Do not cut over if Swift structure/behaviour, source-list controls, the local
signed-artifact gate or identity coverage cannot be established. Chunks 1 and
2 may be removed without changing the production build or regenerating its
identity. After Chunk 3, rollback restores the prior compile route and
regenerates identity as described above.

| Risk | Where it is handled |
| --- | --- |
| Meson/Swift upgrades change implicit arguments or shim linking | Exercise both languages in Chunk 1; investigate failures or revert the migration |
| Persistent configuration overrides fixed policy or retains an old variant | Meson target overrides/assertions plus configuration-state controls; `build.sh` explicitly maps only supported variants |
| A directory silently carries an old compiler/SDK selection | Toolchain-context reuse checks; fresh separate directories for CLT/Xcode; preserve receipts of actual tools and commands |
| Source readers pass with incomplete manifests or fail for unrelated missing files | Exercise Chunk 2 checks in the integration worktree before removing old readers; land only with Chunk 3 |
| A claimed build edge becomes unchecked documentation | Architecture citations point to source-drift rules; identity controls and ABI/live-identity tests provide distinct evidence |
| Temporary duplicate flag ownership persists | Limit the experimental chunks to one review cycle; cut over the combined graph or remove it |
| An early comment or helper edit changes identity | Keep existing digest inputs unchanged through Chunk 2; defer `Package.swift` comments and generator edits to cutover |
| A landed cutover is mistaken for a release-accepted artifact | Tracked cutover observations separate local checks from user-run, hash-bound release evidence |
| New tool requirements exceed demonstrated compatibility | The minimum equals the exercised Meson/Ninja pair; the real root manifest must pass the fresh-directory CLT gate in Chunk 1 |

## Evidence appendix

The original build timings and signed rehearsals, and the subsequent disposable
identity/configuration/CLT probes below, are investigation evidence, not
acceptance of the proposed root manifest. Existing run summaries establish the
reported baseline counts; no new signed app or live battery was run for the
configuration and CLT investigation.

**Identity-scope check.** Against disposable copies of
`generate_worker_identity.py:source_paths` and its targets, adding root Meson
files left the current digest unchanged; adding a comment to `Package.swift`
changed it. Extending `SOURCE_FILES` with both Meson files changed the digest,
and subsequent edits to either file changed it again. This supports postponing
both new membership and existing-input edits to cutover. Repository source
and generated regions were untouched.

**Flag and optional-language checks.** The retained probe's compile database
has no PIC flag on the shim. Installed Meson 1.12.1's `GnuLikeCompiler.get_pic_args`
returns no arguments on Darwin; `BuildTarget._extract_pic_pie` treats PIC as
always enabled there. In a fresh disposable C project using the existing
`xcrun --sdk macosx clang` route, default linking added both
`-dead_strip_dylibs` and header padding; `b_asneeded=false` removed only
the former. Both default and `pic: false` shim declarations added no PIC flag,
and Apple's `clang -### -c` reported PIC relocation.

The same project configured successfully with Swift explicitly unavailable
and its language-registration guard off; reconfiguration with that guard on
refused the missing compiler. This verifies the configuration mechanism,
not a full `BUILD_XPC=0` signed build. No app or repository source was modified.

**Persistent-configuration checks.** In a disposable Meson 1.12.1 C project,
changing `b_asneeded` to true survived reconfiguration despite the manifest's
false default. The ordinary target acquired `-dead_strip_dylibs`; a target with
`override_options: ['b_asneeded=false']` did not. A manifest assertion against
the changed value caused the next compile's regeneration to refuse.

**CLT compilation check.** Against copied current sources at `d37f248`, the
existing probe configured and compiled all four executables and the shim using
Meson 1.12.1/Ninja 1.13.2, `DEVELOPER_DIR=/Library/Developer/CommandLineTools`,
Apple's system compiler shims, `b_asneeded=false` and writable temporary module
caches. Resolution selected CLT's Apple clang 21.0.0, Swift 6.4 and
`/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`. Generated commands had no
Xcode-app paths and the second compile did no work. Temporary files were
discarded; this is an observation of scratch-manifest compilation, not retained
acceptance receipts or signed/runtime acceptance of the future root manifest.

**Release/record grounding.** `release_preflight.py:inspect` requires a clean,
tagged source for release; the Makefile uses its report mode for a notarization
rehearsal. `release_evidence.py` binds attempts to submitted bytes and records
only steps actually observed; `release_archive.py:archive_locked` requires
accepted notarization and matching final ZIP acceptance. `retention.py:index_paths`
allows only retention fields, and `disposition` requires real ownership and
terminal evidence. `records/AGENTS.md` permits tracked development observations
with links from their associated plan. These are the boundaries used by the
cutover handoff above.

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
behaved as shown in Chunk 1's first five matrix rows. Source introspection
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
