# Meson migration plan

## Recommendation and scope

Introduce Meson in three chunks: a combined native compilation pilot,
source-manifest integration, then production cutover. Meson will own four
native executables and one shim library. Keep `make` as the operator interface,
Cargo as the Rust builder, and `build.sh` plus the existing release helpers as
the assembly and release path.

The benefit is an explicit, inspectable source/dependency graph, header-aware
incremental builds, and native outputs outside the source tree.

| Chunk | Scope and resulting ownership | Promotion gate |
| --- | --- | --- |
| 1: native pilot | Meson builds comparison copies of all four executables and the shim. Production still uses `build.sh` compiles. | Structural/incremental checks and the default battery on a signed copy |
| 2: manifest integration | Source checks compare disk, `build.sh` and Meson in the integration worktree; the mutation control reads the new manifest. This checkpoint does not land separately. | Source-drift and barrier controls; applicable signed-copy regression checks |
| 3: cutover | `build.sh` consumes Meson outputs; Meson files enter the identity digest. | Local signed-artifact and behavioural checks before landing; user-run release validation afterward |

**Landing units.** Chunk 1 may land independently as an optional experiment.
Chunks 2 and 3 are sequential implementation/validation steps that land together
as one production-integration commit, so the production build and the default
test battery acquire their Meson requirement in the same commit. The three-way
source check is exercised in the integration worktree before removing the old
reader. Do not make failed introspection optional.

Adopt Swift and C together or abandon the migration; C-only adoption is not a
fallback.

The migration has not been implemented. Each chunk below includes its required
code, documentation and verification work. Shared verification procedures are
references used within each chunk, not a final phase after cutover.

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

Generation stays outside Meson. Identity changes can update both the worker's
ABI header and the host's Swift source; Meson must track both.

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
  executable targets. Check effective optimization/debug settings, not just the
  `buildtype` label; reject unsupported native argument injection or
  instrumentation that would bypass the declared target policy. Keep the policy
  in the Meson files selected for identity at cutover, without a second flag
  table in `build.sh`.
- **Supported variants remain caller choices.** `build.sh` passes `inspection`
  and `xpc` explicitly on every setup/reconfigure. Meson maps those choices to
  target settings and membership; the shell does not repair or re-assert fixed
  settings.
- **Toolchain changes are an operator responsibility.** Preserve Apple's
  `xcrun --sdk macosx` selection, including `DEVELOPER_DIR`. Use separate build
  directories for CLT and Xcode, and require a fresh directory or explicit reset
  when changing the selected compiler or SDK. Reuse a directory for incremental
  builds under the same selection. This convention is documented, not enforced:
  do not add a toolchain fingerprint, a mismatch refusal or a toolchain-identity
  input from `build.sh`.

Check fixed native settings on setup, reconfiguration and compile-triggered
regeneration. Supported build recipes reconfigure to pass the current variants;
reconfiguration alone does not validate a toolchain switch. Source-manifest
introspection discovers membership across branches; configured-directory
introspection reports active targets and configuration. Global options alone
do not describe target overrides.

### Compiler/linker policy

Require explicit consequential settings plus a documented, narrow set of
accepted backend additions. Preserve optimization/debug levels, language and
module settings, sandbox linkage, and Apple compiler/macOS SDK selection;
compare effective compile/link commands and platform targets as well as output
structure. Compiler and platform defaults that the direct `clang` and `swiftc`
invocations also rely on need no explicit flag.

Enforce `b_asneeded=false` through Meson target options so that the linker does
not receive Meson's `-dead_strip_dylibs`. Accept and document
`-headerpad_max_install_names` as an Apple-backend addition, subject to the
artifact checks. Do not replace native Meson targets with custom compiler
wrappers to make argument strings identical. Preserve the shim's existing
optimization/debug/ABI settings and inspect the actual command. The
[built-in options](https://mesonbuild.com/Builtin-options.html#base-options)
describe `b_asneeded` and other configurable policies.

Record accepted argument differences with the comparison evidence and explain
their purpose beside the manifest settings. Any new consequential difference
requires explicit review; structural similarity is not blanket acceptance of
new flags.

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
that existing scope.

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

`PW_INSPECTION` and compiler/SDK selection permit different builds of the same
source identity. Keep the ignored build directory outside the digest.
Configuration and command receipts belong with migration acceptance evidence,
not with the shipped evidence schema.

## Entry conditions and review decisions

Start by reading [AGENTS.md](AGENTS.md), `build.sh`, the Makefile,
[signing procedures](docs/SIGNING.md), [test procedures](tests/README.md), and
[source-drift generator contracts](tests/suites/source_drift/README.md#generator-contracts).
Read [runner/AGENTS.md](runner/AGENTS.md) before touching runner test machinery.
Recheck the inspected sources against the current checkout.

The following choices are settled and are not review items:

- **Tooling.** Add Meson and Ninja. The minimum is Meson 1.12.1 and Ninja
  1.13.2, declared as `meson_version: '>=1.12.1'`. A lower minimum is a
  separate change that must be exercised before it is claimed. Preserve Command
  Line Tools support, verified by the fresh-directory CLT compilation gate in
  Chunk 1; full Xcode is not a prerequisite. Preserve Cargo and the system
  Python used by existing scripts.
- **Module cache.** `SWIFT_MODULE_CACHE` retires at cutover. Swift module
  caches and the shim object live under `builddir/`, which is writable
  wherever Meson can build at all. `build.sh` keeps the variable until then.
- **Compilation scope.** The shim and its host consumer enter together in
  the combined Chunk 1 pilot. C-only adoption is not a fallback.
- **Compiler/linker policy.** Make consequential settings explicit, set
  `b_asneeded=false`, and accept only documented, inspected backend additions
  under the [compiler/linker policy](#compilerlinker-policy). Enforce these through
  the [native configuration contract](#native-configuration-contract) from the
  pilot onward.
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

With `BUILD_XPC=0`, `build.sh` builds Cargo and both standalone C executables,
checks a signing identity, recreates the app, and signs/packages it. It skips
the shim, Swift client and service, and never copies those C executables into
that partial app. `build-evidence.py` tolerates missing components, but
`artifact.py:inspect` requires them for normal artifact-dependent tests.
Specimen execution, including BYOXPC, uses the missing `pw-runner-client`, so
the partial bundle is not a runnable or testable app.

Require Swift when XPC is enabled, and reconfigure when the option changes.
Use the partial-build checks below separately from complete-app acceptance.

For all chunks, use fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` directories,
preserve receipts, and serialize test execution under the existing checkout
lock. Cheap compile checks require no signing or notarization credentials.
Signed-copy promotion requires a Developer ID identity. Notarization and
release are user-run steps after the local cutover gate, as specified below.
Follow the repository's sandbox-escalation guidance for keychain, signature,
XPC or log restrictions.

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
do not describe target overrides. Receipts support provenance; Meson's controls
enforce fixed native settings. The shipped evidence manifest and runtime
envelope remain unchanged.

### Baselines and evidence preparation

Choose fresh managed evidence destinations before executing checks.
Before Chunk 1, check identity with `generate_worker_identity.py --check` and
repair any stale starting state separately. Build the complete signed app through
the existing `build.sh` route and establish a green default-battery baseline at
the actual starting commit. Retain an untouched copy of this app, its inventory,
source snapshot, toolchain and inspection settings before later builds replace
`dist`. This supplies the native outputs and app for the pilot's comparisons.

Prepare receipt capture and the comparison scripts before the first Meson
setup/compile; use the requirements above and the shared structural, signed-copy
and envelope procedures. Preserve the baseline and the accepted Meson signed
copy through Chunk 2; rebuild either if its relevant inputs or configuration
change.

Before Chunk 3, select and record the current released app used for the final
artifact/envelope comparison, and verify that it is locally available. That
release baseline is distinct from the same-source pilot baseline.

## Chunk 1: combined native compilation pilot

**Scope and ownership.** Meson builds the worker, validator, client, host and
shim into an ignored build directory. `build.sh` continues to compile every
production native output and to assemble/sign the app. Source-manifest readers
still use `build.sh`. Test compilation and linking as one slice before changing
those readers or the production route.

**Prerequisites.** Current green baseline, Meson 1.12.1/Ninja 1.13.2, Apple's C
and Swift toolchains, and the file/output location choice above. Require a
current identity with `generate_worker_identity.py --check` and the retained
same-source baseline from [preparation](#baselines-and-evidence-preparation).

**Must remain unchanged.** All existing digest inputs and generated identity
copies; production compile commands and source-list readers; core membership,
module names and compiler settings; worker libsandbox linking and the host's
absence of sandbox API imports; bundle layout, signing and evidence semantics.
Ignore the build directory immediately: generator controls copy untracked,
nonignored files into disposable checkouts.

| Target/setting | Required declaration |
| --- | --- |
| Project/languages | C initially; `meson_version: '>=1.12.1'`; conditional Swift registration below |
| Fixed native policy | Effective plain build settings, `warning_level=0`, `b_ndebug=false`, `b_asneeded=false`; enforced by Meson target settings/assertions under the native configuration contract |
| XPC option | Boolean `xpc`, default true; conditionally register Swift and declare the shim, client and host. Worker and validator remain unconditional. |
| `sb_api_validator` | Its one C source; `-Wall -Wextra -O2 -std=c11` |
| `pw-probe-runner` | Its one C source; same flags; `-lsandbox`; compiler dependency tracking for all included headers |
| `PWCWorkerShim` | `static_library` from `runner/Sources/PWCWorkerShim/PWCWorkerShim.c`; preserve optimization/debug/ABI settings under the compiler/linker policy |
| `pw-runner-client` | `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` and `runner/Clients/PWRunnerClient/main.swift`; `swift_module_name: 'main'` |
| `PWRunner` | The ten explicit `runner/Sources/PWRunnerCore/` Swift files listed by `build.sh`, plus `runner/Services/PWRunner/main.swift`; module name `PWRunner`; `link_with: cworker_shim` |
| Both Swift targets | `-module-cache-path` under the writable build directory; boolean `inspection`, default true, selects `-Onone -g` versus `-O` |

A Meson Swift target cannot contain C sources, so the shim is a separate static
library linked into the host. It is not a separate product.

**Work, in order:**

1. Add reusable structural and normalized-envelope comparison scripts under
   test machinery, implementing the [shared verification procedures](#shared-verification-procedures).
   Prepare capture of [configuration and command receipts](#configuration-and-command-receipts),
   binary hashes, raw comparison inputs and explicit differences before invoking
   Meson. The experimental build recipe is not yet represented by source identity.
2. Add root `meson.build`, `meson.options` and the `builddir/` ignore.
   Declare the targets specified above with explicit source lists, keeping the
   current host source order for straightforward review. Keep shim flags distinct
   from the two C executables' flags and apply the settled compiler/linker
   policy. Declare C in `project()`; register Swift with
   `add_languages('swift', required: true)` only inside the `xpc` guard.
   Implement the fixed native policy checks in this pilot, and provide writable
   module caches during compiler discovery as well as target compilation.
3. Update `docs/SIGNING.md` with comparison-build commands and the tool
   requirements for that optional path; production does not require Meson
   yet. Add `meson.build` to the Build + signing router in `AGENTS.md`.
   Do not change `Package.swift`, `build.sh`, the identity generator or
   any production source merely to support the pilot.

**Cheapest useful validation.** Run `meson setup builddir`,
`meson compile -C builddir`, then compile again and require no work. Inspect
`meson introspect meson.build --targets` and compare all native executables
with the retained same-source `build.sh` outputs using the structural check. Match
the baseline's toolchain and inspection setting for this comparison. Check Swift
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

Use mtime-only touches for these dependency checks; production source edits are
outside this chunk.

Exercise the [configuration-state controls](#configuration-state-controls).
Then run the following CLT gate against the root manifest, with the same
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
   or a compilation failure leaves this gate unmet.

In a fresh build directory with Swift discovery deliberately unavailable,
configure `xpc=false` and compile both C executables. Require no Swift discovery
or shim/client/host targets; a fresh `xpc=true` configuration under the same
conditions must fail for the missing compiler. With the normal toolchain,
reconfigure one build directory through true → false → true, checking target
membership and successful compilation at each step. Existing files from a prior
configuration must not stand in for active targets.

Run `tests/run.sh --suite source_drift` and identity `--check`; require
unchanged generated regions. Unexplained structural differences block promotion.

**Acceptance before promotion.** After the configuration controls and alternate
toolchain/no-XPC checks, select the candidate directory matching the baseline's
toolchain, restore `xpc=true` and the baseline's inspection setting, and compile.
Capture its final commands and output hashes. Use the retained baseline app in
the shared signed-copy procedure to replace all four executables. Run the full
default battery:

```sh
PW_APP_DIR='/private/tmp/<copy>/PolicyWitness.app' \
PW_TEST_OUT_DIR='tests/out/runs/<fresh-name>' tests/run.sh
```

Require all selected cases to pass with no skips, unrun cases or harness errors
and an unchanged candidate inventory. This includes the worker harness,
validator batch, ABI/layout, live-identity, Swift-unit and live witness checks.
Compare all five `tests/fixtures/pw_runner/` requests through both apps.
No notarization.

**Rollback/stop.** Revert the new Meson files, comparison tooling, ignore and
documentation changes. There are no migration-generated identity changes to
undo, and production never consumed the new outputs. If Swift equivalence or
the combined graph fails, investigate within this pilot or abandon Meson;
do not ship a reduced C-only migration.

## Chunk 2: source-manifest integration

**Scope and ownership.** Keep the accepted compilation graph and production
route unchanged. Integrate Meson introspection into the source-drift checker,
its disposable-checkout control and the barrier mutation control.

**Prerequisites.** Chunk 1 accepted; read `runner/AGENTS.md` and the existing
readers/controls. Develop this checkpoint in the same integration worktree as
Chunk 3. Its checks require Meson while the intermediate build still uses the
old compiler route; that temporary state is never a standalone commit on main.

**Must remain unchanged.** Existing identity inputs and generated copies,
native compiler settings, production assembly/signing, and the mutation
oracle's positive/negative behaviour. No identity regeneration is part of
this chunk; reader/check changes are outside the selected digest sources.

**Work, in order:**

1. In `tests/suites/source_drift/check.py`, read the relevant host Swift and
   shim C sets through `meson introspect meson.build --targets`. Add them to
   `diff_sets` alongside disk and `build.sh`: three sets during this chunk.
   Filter to the existing source domains; client/service entrypoints are not
   extra core sources. Treat failed introspection or missing targets as errors.
   Always use file-mode introspection here and in the mutation reader: it lists
   the host and shim declarations regardless of the `xpc` guard, whereas a
   configured build directory lists only its active targets.
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

**Prerequisites.** Chunks 1 and 2 accepted, a green current baseline, the
Chunk 3 review choices settled, and the released comparison app selected and
available as described in preparation. Signing credentials and a logged-in GUI
session are needed for the full local artifact/BYOXPC gate. No notarization
credentials or submission are required to land this chunk. The user owns the
later notarization/release run.

**Must remain unchanged.** `sign_macho`, nested signing order, evidence
content model, `EXECUTABLES`, outer seal, guide/ZIP procedure and all release
targets. The stale-guide and stale-contract controls must still fail with
their expected diagnostics before any compiler, Meson invocation, or
distribution output; missing tools must not become the reason they pass.

**Work, in order:**

Complete the implementation and generation steps below before running candidate
builds or validation. Step 2 changes the build recipe; it does not run it yet.

1. Add `meson.build` and `meson.options` to `SOURCE_FILES` in
   `docs/generate_worker_identity.py`, retaining all existing inputs.
   Extend `tests/suites/source_drift/contract.py` so edits to either new
   input change identity and stale generated copies are refused.
2. Edit `build.sh` to set up or reconfigure `builddir/` and run
   `meson compile -C builddir` after its existing documentation, identity, stamp,
   keychain and Cargo steps. Keep `PW_INSPECTION` as the public knob;
   Meson reads its boolean option, not that environment variable.
   Map `BUILD_XPC` to the boolean `xpc` option on every setup/reconfigure.
   Preserve conditional Swift discovery and the partial-bundle workflow;
   keep both C executables unconditional and custom `DIST_DIR` assembly working.
   Propagate Meson's native policy refusals before copying or signing outputs.
   Toolchain changes follow the operator convention above. Do not duplicate the
   fixed native policy in shell flags or assertions.
   If `make native` was selected before this chunk, implement its shared
   generator preparation and option mapping here, alongside the production path.
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
   in `docs/SIGNING.md`, together with supported variants, CLT selection and the
   operator's responsibility to use fresh or explicitly reset directories. If
   selected, document `make native` with accurate header/help comments.
6. In `docs/architecture.json`, update the build node's guard description
   and add the settled source-kind `meson_build` node with an edge to
   `drift_check` labelled "source list equals the tree", citing Chunk 2's
   checking rule. Retain the existing build-generator, guide-staging and
   `sign_macho` anchors. Regenerate with
   `python3 docs/generate_architecture.py` (rendering needs Graphviz).
   Represent the checked source-list relationship only, not a compile graph.
7. Run `python3 docs/generate_worker_identity.py` after all digested edits.
   Include its three generated regions in the eventual cutover commit. This is
   the migration's first change to those regions; keep `build.sh` and
   `Package.swift` in the digest.

Create the factual handoff and pin completed runs after their results exist.
Commit the combined cutover only after the local gate and handoff are complete.

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
3. Perform the shared artifact/envelope comparison against the released app
   selected before implementation.
4. After the checks pass, create the handoff record and pin the completed runs
   as described below, preserving exact tested source and artifact provenance.
   Once these local gates pass and the handoff is complete, the cutover may be
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
receipt, unmanaged run directory or extra status field. The tracked record is
an evidence record, not a second active plan.

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

Exercise supported `inspection`/`xpc` changes as specified in the chunks.
Re-establish these controls and review argument differences after Meson, compiler
or SDK upgrades, using fresh or explicitly reset directories when the compiler or
SDK changes.

### Structural and artifact comparison

For native outputs, compare `otool -L` dynamic libraries, `otool -l`
load-command/segment/section structure, `size`, and undefined `_sandbox_*`
imports from `nm -u`. For Swift, also check the module names in mangled
symbols. Preserve the comparison as a script from Chunk 1 onward and rerun
it when toolchains change, including a review of effective compiler/linker
argument differences against the agreed policy. A compile success alone is
insufficient.

Whole-binary byte equality is not the acceptance gate: repeated direct Swift
builds of identical sources differ in bytes, and the accepted linker additions
change C output bytes without changing measured structure or behaviour.

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

1. Use the untouched baseline app retained during preparation. Check that its
   selected sources, toolchain and inspection setting match the candidate;
   rebuild the baseline through the unchanged production route if they do not.
   Require identity `--check`; only Chunk 3 changes the digest inputs and copies.
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

Expected variable classes: PIDs; wall-clock/monotonic
times and deadlines; durations; observer raw log output and deny lines;
temporary-copy bundle/service names and paths; the client argv; and
`stdout_bytes_*` affected by longer identifiers. Across builds, account for
the four stamp values too. Use explicit field paths and explain every
excluded difference; these classes are not permission to discard arbitrary
strings or evidence records. A changed source identity is an expected
provenance change to verify against its own sources, not a volatile value
to silently erase.

The built-in runner's `data.specimen.binaries` dossier is null; it is populated
only for BYOXPC. Use artifact inspection for the built-in app's manifest
baseline.

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
| A directory silently carries an old compiler/SDK selection | Operator convention: separate CLT/Xcode directories and a fresh directory or explicit reset on compiler/SDK changes; acceptance receipts record actual tools and commands |
| Source readers pass with incomplete manifests or fail for unrelated missing files | Exercise Chunk 2 checks in the integration worktree before removing old readers; land only with Chunk 3 |
| A claimed build edge becomes unchecked documentation | Architecture citations point to source-drift rules; identity controls and ABI/live-identity tests provide distinct evidence |
| Temporary duplicate flag ownership persists | Limit the experimental chunks to one review cycle; cut over the combined graph or remove it |
| An early comment or helper edit changes identity | Keep existing digest inputs unchanged through Chunk 2; defer `Package.swift` comments and generator edits to cutover |
| A landed cutover is mistaken for a release-accepted artifact | Tracked cutover observations separate local checks from user-run, hash-bound release evidence |
| New tool requirements exceed demonstrated compatibility | The declared Meson/Ninja minimum; the root manifest must pass the fresh-directory CLT gate in Chunk 1 |
