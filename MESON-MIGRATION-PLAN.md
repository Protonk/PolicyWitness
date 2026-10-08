# Meson migration plan

A staged plan for letting Meson own the compiled parts of the PolicyWitness
build while `make`, `build.sh`, Cargo and the release helpers keep everything
they guard today. It answers the planning brief that asked for a graduated,
chunkable migration rather than an implementation; nothing in this document
has been applied to the build.

Two kinds of statement appear below and are labelled. **Observed** means a
command was run against this checkout and the result is reported. **Proposed**
means a change the plan recommends, which a later commit may make differently.

## Summary

- The build is already fast and almost entirely procedural. **Observed:** an
  unchanged tree rebuilds, signs and zips in about 7 s wall, of which about
  4.6 s is the two `swiftc` invocations and about 1.3 s is seven `codesign
  --timestamp` calls. Meson can remove the compile time on an unchanged tree
  and almost nothing else; the floor is signing, evidence and zipping.
- The real gain is structural: an explicit, introspectable source list for the
  five native executables, header tracking the shell script does not have,
  binaries that leave the source tree, and a typed `inspection` option instead
  of a string-compared environment variable. Two repository checks today
  parse `build.sh` with regular expressions to learn the Swift source list,
  and a third copies it into a disposable checkout for the same reason; a
  Meson build file read through `meson introspect` gives them a JSON manifest.
- Five of the sixteen steps in `build.sh` are compilation. The other eleven are
  gates (generator checks, identity regeneration, identity verification),
  procedure (the git stamp, bundle assembly, plist stamping, guide staging,
  zipping) or security (identity selection, inside-out signing, evidence over
  signed bytes, outer seal). None of those belong in Meson and the plan leaves
  every one of them where it is.
- Recommended shape: a pilot over the two C tools and the C shim (no change to
  the shipped app), then the two Swift executables with the drift checks
  reading the Meson manifest while both owners still exist, then a cutover in
  which `build.sh` compiles nothing itself and copies from the Meson build
  directory. Cargo is never touched. A smaller migration that stops after the
  C tools is a legitimate resting point and is described.
- One identity rule changes meaning if it is not updated in the same commit.
  The host/worker source identity digests `build.sh` and `runner/Package.swift`
  as compile-flag owners; `meson.build` and `meson.options` must join that list
  when they take over the flags.

## What was examined

**Observed** on 2026-10-07 at commit `06fc25e` on macOS 26.7.1 (Darwin 25.6.0),
Xcode 27 (Apple clang 21.0.0, Swift 6.4), cargo 1.99 from a keg-only rustup,
`/usr/bin/python3` 3.9.6, Meson 1.12.1 and Ninja 1.13.2 from Homebrew.

- Read: [Makefile](Makefile), [build.sh](build.sh), [docs/SIGNING.md](docs/SIGNING.md),
  [tests/build-evidence.py](tests/build-evidence.py), [tests/lib/artifact.py](tests/lib/artifact.py),
  the four generators under [docs/](docs/) and [docs/generator_common.py](docs/generator_common.py),
  [controller/build.rs](controller/build.rs), [controller/Cargo.toml](controller/Cargo.toml),
  [runner/Package.swift](runner/Package.swift), [docs/architecture.json](docs/architecture.json),
  the source_drift suite ([check.py](tests/suites/source_drift/check.py),
  [generators.py](tests/suites/source_drift/generators.py), [limits.py](tests/suites/source_drift/limits.py),
  [contract.py](tests/suites/source_drift/contract.py), [check_planner.py](tests/suites/source_drift/check_planner.py)),
  [tests/suites/witness_contract/opt_in/mutations.py](tests/suites/witness_contract/opt_in/mutations.py),
  [tests/lib/suite_run.py](tests/lib/suite_run.py), [tests/lib/release_preflight.py](tests/lib/release_preflight.py),
  [tests/lib/release_accept.py](tests/lib/release_accept.py), [tests/catalog.json](tests/catalog.json),
  [tests/OPT_IN_TESTS.md](tests/OPT_IN_TESTS.md) and the test fixture builders under
  [tests/fixtures/](tests/fixtures/).
- Ran: `make build` twice with an explicit `IDENTITY` (once after a controller
  change, once on an unchanged tree), each `build.sh` compile and signing step
  on its own under a timer, `codesign --verify` and `artifact.inspect` on the
  result, the default battery (`tests/run.sh` into
  `tests/out/runs/meson-plan-baseline`), and a disposable Meson project under
  `.tmp/meson-probe/` that compiles the real C and Swift sources through
  symlinks into the tree. The probe's build file is reproduced under
  [Chunk 1](#chunk-1-pilot-the-c-tools-under-meson) so it can be recreated;
  `.tmp` is disposable.

## Inventory of build boundaries

**Observed.** `build.sh` runs these steps in this order. "Kind" says what the
step is for; "Meson?" is the plan's verdict.

| # | Step (build.sh) | Kind | Inputs | Outputs | Meson? |
| --- | --- | --- | --- | --- | --- |
| 1 | `generate_limits.py --check`, `generate_contract.py --check`, `generate_architecture.py --check` (lines 99 to 103) | gate (G3) | docs, manifests | none | No. Checks over tracked text; a stale copy must stop the build before any compiler runs, and two drift controls prove that by running `build.sh` in a checkout that has no compilers. |
| 2 | `generate_worker_identity.py` in write mode (105) | in-tree generation | protocol sources, `build.sh`, `Package.swift` | regions inside `pw_probe_runner_abi.h`, `CWorker.swift`, `tests/lib/contract.py` | No. Meson outputs live in the build directory; this rewrites sources. It must run before any compile. Meson benefits anyway: a rewritten `CWorker.swift` has a new mtime and only the host recompiles. |
| 3 | Build stamp from git (112 to 128) | procedure | tags, HEAD | `PW_*` values, plist edits | No. One owner for the stamp; it feeds Cargo through environment variables and the plists through PlistBuddy. `release_preflight.py` mirrors this logic. |
| 4 | Identity selection and keychain check (130 to 175) | security gate | keychain | `IDENTITY` | No. |
| 5 | Flag selection from `PW_INSPECTION` (177 to 186) | procedure | env | Swift flags, `RUSTFLAGS` | Partly. The Swift and C flags move with the compiles; `RUSTFLAGS` stays. One knob must drive both (see ownership). |
| 6 | `cargo build --release` for three binaries (190 to 212) | compilation (Rust) | `controller/`, stamp env | `controller/target/release/*` | No, by the brief. Cargo already rebuilds when only the stamp changed (`build.rs`). |
| 7 | `clang` for `sb_api_validator` (226 to 232) | compilation (C) | one `.c` | binary written **into the source tree** (gitignored) | **Yes.** |
| 8 | `clang -lsandbox` for `pw-probe-runner` (234 to 246) | compilation (C) | one `.c` and three headers; only the ABI header's existence is checked | binary written into the source tree (gitignored) | **Yes.** |
| 9 | Bundle skeleton, Info.plist copy and stamp, Rust binaries copied, augments copied (248 to 303) | assembly | 3, 6, `Info.plist`, `runner/augments/*.sb` | bundle layout | No. Layout is a contract checked by `EXECUTABLES`; it stays in the script that also signs it. |
| 10 | `swiftc` for `pw-runner-client` (354 to 361) | compilation (Swift) | 2 Swift files | binary written straight into the bundle | **Yes.** |
| 11 | `clang -c` for `PWCWorkerShim.o` into the Swift module cache directory (364 to 365) | compilation (C) | one `.c` | object | **Yes** (as a static library Meson links). |
| 12 | Per service: plist copy and stamp, `swiftc` for `PWRunner`, copy worker and validator into the service bundle (366 to 412) | compilation + assembly interleaved | 10 Swift files, `main.swift`, shim object | service bundle contents | **Compile yes, assembly no.** The copies and plist stamping stay. |
| 13 | `generate_worker_identity.py --check` (420) | gate | sources | none | No. "Refuse a source edit during compilation." |
| 14 | Inside-out signing: top-level helpers, then the service's embedded helpers, then the service bundle with its entitlements (427 to 469) | security | 9 to 12, `IDENTITY` | signatures | No. |
| 15 | `build-evidence.py` over the signed bytes (471 to 475) | generation over artifacts | signed bundle | `Contents/Resources/Evidence/*` | No. Order-sensitive: it hashes signed helpers and is itself sealed by the outer signature. |
| 16 | Outer app signature, verification, standalone observer signature, guide staging, ZIP (477 to 499) | security, generation, packaging | everything above | the three deliverables | No. |

Outside `build.sh`, four more things compile code and none of them should move:

- The Makefile targets `test`, `clean`, `notarize`, `release` and `publish` are
  procedure and guards over Python helpers; `build` is one path through
  `build.sh`. **Proposed:** the Makefile keeps dispatching to `build.sh`, which
  dispatches to Meson for compilation; no Meson command is added to the
  Makefile's `build` recipe, so the keychain guard, the stamp and the gate order
  keep one owner. An optional `native` target for compiling without an identity
  is discussed under Chunk 3.
- `runner/Package.swift` is a test-only SwiftPM manifest for `runner_unit`; it
  is also an input to the identity digest. It stays.
- The fixture builders under `tests/fixtures/*/build.sh` and the per-suite
  `clang` calls (`runner_abi_layout`, `runner_live_worker_identity`) compile
  test equipment into per-run artifact directories, log the build as evidence,
  and in places deliberately mutate and rebuild production sources. That is test
  machinery, not product build; it stays shell.
- `controller/tools/sb_api_validator/build.sh` builds an ad hoc-signed debugger
  copy of the validator for manual use. It is not on the shipped path. Whether
  to retire it is a human decision listed at the end.

## Where Meson helps and where it would only wrap

**Observed** timings on this machine, wall clock:

| Measurement | Time |
| --- | --- |
| `make build`, controller recompiled by Cargo | 11.4 s |
| `make build`, unchanged tree | 6.9 s |
| the three generator checks together | 0.4 s |
| `cargo build` with nothing to do | 0.04 s |
| the three `clang` invocations together | 0.25 s |
| `swiftc` for the client | 1.4 s |
| `swiftc` for the service | 3.2 s |
| one `codesign --timestamp` (seven per build) | 0.18 s |
| `build-evidence.py` | 0.2 s |
| `ditto` ZIP | 0.3 s |
| Meson probe: `meson setup` (once) | 2.1 s |
| Meson probe: cold build of all five native targets, parallel | 4.3 s |
| Meson probe: no-op `ninja` | 0.0 s |

**Observed** incremental behaviour of the probe: touching
`pw_worker_evidence.h` rebuilt only the worker (Ninja records all three worker
headers as dependencies; `build.sh` checks only that the ABI header exists);
touching `CWorker.swift` rebuilt only the host; touching `PWRunnerAPI.swift`
rebuilt the client and the host; touching the shim rebuilt the shim archive and
relinked the host. `build.sh` recompiles all five on every run and deletes the
bundle first.

Where Meson genuinely helps:

- **A declared source list with a machine-readable form.** Meson refuses
  globbing, so the list in `meson.build` is a manifest in the same sense the
  repository already uses that word. `meson introspect <path to meson.build>
  --targets` returns every target's sources and arguments as JSON without a
  configured build directory (**Observed**). Today
  `check.py` (`build_sh_swift_files`, `build_sh_c_files`) and
  `mutations.py` (`build_host`) recover the same list by regular expressions
  over bash, and `check_planner.py` copies `build.sh` into its disposable
  checkout only so that `check.py` can parse it.
- **Header dependencies and minimal rebuilds**, above.
- **Outputs out of the source tree.** Two `.gitignore` lines exist only because
  `build.sh` writes `pw-probe-runner` and `sb_api_validator` next to their
  sources, and the shim object lands in the Swift module cache directory.
- **One typed knob for inspection builds.** `PW_INSPECTION` becomes a boolean
  option whose value `meson introspect --buildoptions` reports, instead of a
  string compared in two places.
- **Parallel compilation** of independent targets, worth about a second.

Where Meson would only wrap a script and add a layer:

- Cargo. A `custom_target` that shells out to `cargo build` with
  `build_always_stale` gives Meson nothing to reason about and gives Cargo a
  second caller. `build.sh` keeps calling Cargo and copying its outputs.
- The generators. They write into tracked sources and are gated by `--check`;
  a `run_target` would hide the ordering the drift controls prove.
- Stamp, plist stamping, bundle assembly, signing, evidence, outer seal, guide
  staging, ZIP, notarization, acceptance, archiving, rotation, publication.
  Each has an accumulated guard and a required order; putting them behind
  Ninja's scheduler would reintroduce ordering risk for no graph benefit.
- Test fixture builds, for the reasons above.

## Constraints the checkout imposes

These are the places where moving a compile step changes what an existing
check or identity claims. Each one must be handled in the same commit as the
step it concerns.

1. **The identity digest covers `build.sh` and `Package.swift`.** **Observed:**
   `SOURCE_FILES` in [docs/generate_worker_identity.py](docs/generate_worker_identity.py)
   names `docs/generate_worker_identity.py`, `build.sh` and
   `runner/Package.swift`; `SOURCE_DIRS` covers `controller/tools/pw_probe_runner`
   and `runner/Sources`. Today the worker's and host's compile flags are bytes
   of `build.sh`, so a flag change changes the identity. **Proposed:** when a
   Meson file takes over any compile flag, add `meson.build` and
   `meson.options` to `SOURCE_FILES` in that commit. Expect the identity value
   to change at every chunk (it changes on any `build.sh` edit today);
   `runner_abi_layout`, `runner_live_worker_identity` and the identity controls
   in `contract.py` observe the regenerated copies.
2. **Two readers parse `build.sh` for the Swift source list, and one copies it.**
   `check.py` compares the on-disk `runner/Sources` tree with the
   `XPC_RUNNER_*_FILE` declarations and the swiftc block; `mutations.py`
   asserts the same list before compiling a mutated host; the planner control
   copies `build.sh` for `check.py`. **Proposed:** `diff_sets` in `check.py`
   already compares any number of manifests, so Chunk 2 adds the Meson list as
   a third manifest while `build.sh` still has its own, and Chunk 3 removes the
   `build.sh` manifest. `mutations.py` reads the same Meson list.
3. **Two controls run `build.sh` in a checkout with no compilers.**
   `limits.py` (`test_build_refuses_stale_guide_before_signing_or_creating_output`)
   and `contract.py` (`test_build_refuses_stale_contract_copy_before_signing_or_creating_output`)
   copy only documents and `build.sh`, run it, and require exit 1 within 10 s
   with no `dist` created. **Constraint:** the generator checks stay first in
   `build.sh`, before any `meson` command; a Meson invocation placed earlier
   would fail these controls for the wrong reason.
4. **`generators.py` checks that `build.sh` calls every generator's `--check`.**
   `test_build_checks_every_generator_before_signing` reads `build.sh`. The
   gates stay in `build.sh`, so this is unaffected.
5. **The document graph cites `build.sh` symbols.** **Observed:** the `build`
   node and edges D15, D37 to D40 cite `generate_worker_identity.py`,
   `generate_contract.py`, `generate_architecture.py` and `--stage-guide` in
   `build.sh`; the BYOXPC `bundle_copy` node cites `sign_macho`. All remain in
   `build.sh`, so the citations stay valid. `generator_common.FORM_RULES` allows
   `build.sh` by exact path as a `control` file; `meson.build` could be cited as
   a `source` (symbol presence) but not as a check unless that table is widened,
   which is a human decision.
6. **Meson's Swift rules.** **Observed** in the probe: a Swift target may not
   contain a C source, so the shim becomes `static_library` and the host links
   it; the module name defaults to the target name and `pw-runner-client` is not
   an identifier, so `swift_module_name: 'main'` is required to reproduce the
   mangling `build.sh` produces (its `swiftc` falls back to `main`); Meson passes
   `-module-name PWRunner` for the host, which matches the current binary. The
   `swift_module_name` keyword exists since Meson 1.9.
7. **Meson adds linker flags `build.sh` does not pass.** **Observed:** the C
   executables are linked with `-Wl,-dead_strip_dylibs -Wl,-headerpad_max_install_names`,
   so their bytes differ from `build.sh`'s while size, load commands, section
   sizes, undefined `_sandbox_*` imports and no-argument behaviour are identical.
8. **Swift output is not reproducible.** **Observed:** the same `swiftc`
   command on the same sources produced different bytes in two output
   directories, in the same directory at two times, and without `-g`. The C
   compiles were byte-identical across directories and times. Byte equality is
   therefore available as a gate for nothing that `swiftc` produces, under
   either build system.
9. **`files()` is sandboxed to the source root.** `meson.build` must sit at or
   above the sources it names, so the production file lives at the repository
   root (the probe used symlinks). Its build directory must be gitignored;
   `release_preflight.py` ignores untracked files when deciding a tree is dirty
   (`--untracked-files=no`) but the generator-contract controls in
   `generators.py` copy `git ls-files --others --exclude-standard`, so an
   unignored build directory would be copied into their disposable checkouts.
10. **A new development-tool requirement.** Today the documented requirement is
    Xcode Command Line Tools ([docs/SIGNING.md](docs/SIGNING.md#build)) plus
    Cargo; the Makefile uses the system `python3`. Meson and Ninja would be
    added (Homebrew installs them with their own Python). This is a human
    decision.

## Ownership after the migration

**Proposed.** Nothing in this table is ambiguous today except the compile flags,
and the plan keeps it that way.

| Responsibility | Owner | Reads | Writes |
| --- | --- | --- | --- |
| Rust compilation, dependencies, stamp embedding | Cargo, invoked by `build.sh` | `controller/`, `PW_*` env | `controller/target/release/` |
| C and Swift compilation of the five native executables and the shim | Meson, invoked by `build.sh` | `meson.build`, `meson.options`, sources | the ignored build directory only |
| Identity, contract, limits, architecture regions | the four generators, invoked by `build.sh` before Meson | manifests and sources | marked regions in tracked files |
| Stamp, identity selection, inspection knob | `build.sh` | git, keychain, `PW_INSPECTION` | `-Dinspection=` for Meson, `RUSTFLAGS` and `PW_*` for Cargo, plist values |
| Bundle layout, copies from both build outputs, plists, augments | `build.sh` | Cargo and Meson outputs | `dist/PolicyWitness.app` |
| Signing order, evidence, outer seal, guide, ZIP | `build.sh` | the assembled bundle | signatures, `Evidence/`, deliverables |
| Notarize, accept, archive, rotate, publish | Makefile and `tests/lib/release_*.py`, `notarize.py`, `tests/accept-release.sh` | the ZIP | release evidence |
| Source-list agreement with disk | `source_drift` `check.py` | `meson introspect` JSON, the tree | nothing |

The inspection knob: `build.sh` keeps `PW_INSPECTION` as the only public
switch and translates it to `meson setup ... -Dinspection=true|false`
(running `meson configure` when the build directory already exists with the
other value) and to `RUSTFLAGS` as today. Meson never reads `PW_INSPECTION`.

## Chunk 1: pilot, the C tools under Meson

**Scope.** `sb_api_validator`, `pw-probe-runner` and the `PWCWorkerShim`
object, compiled by Meson into an ignored build directory. The shipped app does
not change: `build.sh` is not edited except for the identity file list, and
the Meson outputs are compared against `build.sh`'s, not shipped.

**Why first.** They are the smallest isolated compile responsibility, their
outputs are byte-reproducible (so comparison is strong), one of them is the
sandboxed worker whose flags the identity covers (so the identity question is
settled early and cheaply), and nothing about signing, Swift or bundle layout
is touched.

**Owner now:** `build.sh` steps 7, 8 and 11. **Owner after:** Meson, for these
three outputs in the build directory; `build.sh` still compiles its own copies
and ships them during this chunk.

**Prerequisites.** Meson and Ninja installed; the three decisions on tools,
file location and build-directory name taken (see the end).

**Files.** **Proposed** contents, adapted from the probe that was observed to
build and from the flags in `build.sh`:

```meson
# meson.build (repository root)
project('policywitness-native', 'c', 'swift',
  meson_version: '>=1.9',
  default_options: ['buildtype=plain', 'warning_level=0', 'b_ndebug=false'])

inspection = get_option('inspection')
c_flags = ['-Wall', '-Wextra', '-O2', '-std=c11']

executable('sb_api_validator',
  'controller/tools/sb_api_validator/sb_api_validator.c',
  c_args: c_flags)

executable('pw-probe-runner',
  'controller/tools/pw_probe_runner/pw_probe_runner.c',
  c_args: c_flags,
  link_args: ['-lsandbox'])

cworker_shim = static_library('PWCWorkerShim',
  'runner/Sources/PWCWorkerShim/PWCWorkerShim.c')
```

```meson
# meson.options
option('inspection', type: 'boolean', value: true,
  description: 'PW_INSPECTION=1: -Onone -g for Swift, -O otherwise')
```

Plus one `.gitignore` entry for the build directory and `meson.build`,
`meson.options` appended to `SOURCE_FILES` in `generate_worker_identity.py`
(then regenerate; the regenerated regions are part of the commit).

**Must not change.** `build.sh` behaviour and output; `EXECUTABLES`; the
bundle; the test battery's view of the app. The `-lsandbox` link, which the
R5 note in `build.sh` requires, and the `-std=c11 -Wall -Wextra -O2` flags.

**Cheapest useful validation** (**Observed** to pass in the probe, so the
pilot is confirming it against the root file):

```sh
meson setup builddir && meson compile -C builddir
for t in pw-probe-runner sb_api_validator; do
  cmp <(otool -l builddir/$t | grep -E '^ *(cmd|segname|sectname|name)') \
      <(otool -l controller/tools/*/$t | grep -E '^ *(cmd|segname|sectname|name)')
  cmp <(nm -u builddir/$t | grep _sandbox_) <(nm -u controller/tools/*/$t | grep _sandbox_)
  size builddir/$t controller/tools/*/$t
done
builddir/pw-probe-runner; controller/tools/pw_probe_runner/pw-probe-runner   # both: rc 2, "--shm-fd is required"
meson introspect meson.build --targets | python3 -m json.tool | head
touch controller/tools/pw_probe_runner/pw_worker_evidence.h && meson compile -C builddir  # only the worker rebuilds
```

The byte difference from Meson's two extra linker flags is expected; the
comparison is of load-command structure, section sizes, imports and behaviour.
If the structure differs, stop and investigate before anything else.

**Stronger acceptance before promotion.** Substitute the Meson-built worker
and validator into a disposable copy of the app and exercise the copy through
the existing controls, following the recipe `signed_copy` in
[mutations.py](tests/suites/witness_contract/opt_in/mutations.py) already
uses: `ditto` the app to `/private/tmp`, replace the two helpers inside
`PWRunner.xpc`, give the app and the service fresh `CFBundleIdentifier`s, sign
the helpers, then the service with its entitlements, run `build-evidence.py`,
sign the app with its entitlements, and require `artifact.inspect` to pass.
Then run `tests/run.sh --suite smoke --suite runner_c_worker_harness --suite
validator_batch_mode` with `PW_APP_DIR` pointing at the copy. The harness
suite drives the real worker through the shared-memory ABI with no host, so it
is the most direct check that a Meson-built worker is the same worker. See
[the rehearsal](#rehearsal-of-the-chunk-1-acceptance-check) for what this
looked like when it was tried.

**Revert.** Delete `meson.build`, `meson.options` and the `.gitignore` line,
restore `SOURCE_FILES`, regenerate the identity. No shipped byte depended on
the chunk.

**Confidence in the difficulty estimate:** high. Every element was exercised
by the probe.

## Chunk 2: the native slice, including the Swift executables

**Scope.** Add `pw-runner-client` and `PWRunner` to `meson.build`; make the
source list in `meson.build` the manifest the drift checks compare with the
tree, alongside the `build.sh` list, while both exist; optionally give
developers a compile-only entry point. The shipped app still comes from
`build.sh`'s own compiles.

**Why second.** The Swift compiles are where the time goes and where the
source list lives, so this is where the explicit graph pays. It is larger than
the pilot because the drift checks and the barrier mutation control must learn
a new reader, and because Swift output cannot be compared by bytes.

**The Swift/XPC boundary belongs here for compilation and nowhere for
assembly.** The probe showed Meson compiling the host from the same eleven
files with the same module name, the same dynamic library list, the same
load-command structure and no `_sandbox_*` import (**Observed**). The XPC
bundle itself (its `Info.plist` and stamp, the embedded worker and validator,
its entitlements and signature) is assembly and signing; it stays in
`build.sh` in every chunk. If Meson's Swift support cannot reproduce the host
at this step, the migration stops at the C tools (see stopping points).

**Owner now:** `build.sh` steps 10 and 12 (compile part). **Owner after:**
Meson for the two binaries in the build directory; `build.sh` still ships its
own until Chunk 3.

**Files.** The Swift targets from the probe:

```meson
swift_common = ['-module-cache-path', meson.current_build_dir() / 'swift-module-cache']
swift_opt = inspection ? ['-Onone', '-g'] : ['-O']

executable('pw-runner-client',
  'runner/Sources/PWRunnerCore/PWRunnerAPI.swift',
  'runner/Clients/PWRunnerClient/main.swift',
  swift_module_name: 'main',   # build.sh's swiftc falls back to "main" for this output name
  swift_args: swift_common + swift_opt)

executable('PWRunner',
  files('runner/Sources/PWRunnerCore/PWRunnerAPI.swift',
        'runner/Sources/PWRunnerCore/SandboxApply.swift',
        'runner/Sources/PWRunnerCore/ProbeRunner.swift',
        'runner/Sources/PWRunnerCore/PathUtils.swift',
        'runner/Sources/PWRunnerCore/CWorker.swift',
        'runner/Sources/PWRunnerCore/MonotonicDeadline.swift',
        'runner/Sources/PWRunnerCore/ValidatorClient.swift',
        'runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift',
        'runner/Sources/PWRunnerCore/PWRunnerService.swift',
        'runner/Sources/PWRunnerCore/PWRunnerListener.swift'),
  'runner/Services/PWRunner/main.swift',
  swift_args: swift_common + swift_opt,
  link_with: cworker_shim)
```

Changes to checks, each small:

- `check.py`: a `meson_swift_files()` and `meson_c_files()` reader over
  `meson introspect meson.build --targets`, added as third manifests to the
  two `diff_sets` calls. The README of the suite describes three manifests
  for the duration of the chunk.
- `check_planner.py`: copy `meson.build` and `meson.options` into the
  disposable checkout alongside `build.sh`.
- `mutations.py` (`build_host`): read the host's source list from the Meson
  manifest, keeping the assertion that it equals the on-disk set.
- `generate_worker_identity.py`: no further change (the files were added in
  Chunk 1).
- Optional: a Makefile target `native` that runs `meson setup` if needed and
  `meson compile -C builddir`, for a compile loop that needs no identity. It is
  a developer convenience, not part of the shipped CLI; the Makefile header's
  target list and comments gain one entry.

**Must not change.** The ten-file host source set and its order (the order
is not semantically significant to `swiftc`, but keep it to make diffs
trivial); `-Onone -g` under inspection and `-O` otherwise; the module cache
living under a writable path (`build.sh` uses `.tmp/swift-module-cache`
because sandboxed harnesses block `~/.cache`; the build directory serves the
same purpose).

**Cheapest useful validation.** `meson compile`, then for each Swift binary:
`nm -u | grep -c _sandbox_` is zero for the host, `otool -L` lists equal,
load-command structure equal, module name `main` for the client and
`PWRunner` for the host (`nm | grep '_\$s'` prefixes). Then the incremental
matrix above, and `tests/run.sh --suite source_drift` with the three-manifest
check in place.

**Stronger acceptance before promotion.** The signed-copy substitution of all
four Meson-built binaries (client, host, worker, validator), evidence
regenerated and the copy sealed, then the default battery against the copy:
`PW_APP_DIR=<copy> PW_TEST_OUT_DIR=tests/out/runs/<name> tests/run.sh`. The
dispatcher's artifact check gates the copy exactly as it gates `dist`, so a
layout or seal mistake in the substitution fails before any case runs. Also
run `tests/run.sh --case witness_contract/order_barrier_mutations`, because
that control compiles the host itself from the source list it now reads from
Meson; it must still detect both mutations and pass the unmodified control.

**Revert.** Remove the Swift targets and the third manifests; `mutations.py`
back to the `build.sh` regex. The shipped app never depended on the chunk.

**Confidence in the difficulty estimate:** medium. The compile was observed;
the three reader changes and the barrier control rerun were not.

## Chunk 3: production cutover

**Scope.** `build.sh` stops compiling. After the generator gates and the stamp
it runs `meson setup builddir -Dinspection=...` (or `meson configure` when the
directory exists) and `meson compile -C builddir`, then copies the five
binaries from `builddir/` into the bundle paths it already assembles, in the
same places it copied them before. The `XPC_RUNNER_*` declarations, the three
`clang` calls and the two `swiftc` calls leave `build.sh`; the two in-tree
binary ignores leave `.gitignore`; `check.py` drops the `build.sh` manifest
and compares disk with Meson only.

**Why last.** It is the only chunk that changes shipped bytes and the only one
whose rollback touches the release path, so it should land when the previous
two chunks have made the comparison routine.

**Owner now:** `build.sh`. **Owner after:** Meson for compilation; `build.sh`
for everything else, unchanged in order: gates, stamp, identity, Cargo, Meson,
assembly, identity `--check`, signing, evidence, seal, guide, ZIP.

**Must not change.** The signing order and the `sign_macho` function; the
evidence manifest's content model; `EXECUTABLES`; the ZIP; every Makefile
target; the request/reply semantics, worker and validator separation, process
lifetimes, entitlements and the XPC bundle layout. The two build-refusal
controls must still see exit 1 before any Meson command runs in a checkout
without compilers.

**Cheapest useful validation.** `make build IDENTITY=...` twice; the second
run's `meson compile` reports nothing to do and the app still inspects clean.
`make build PW_INSPECTION=0` reconfigures and produces `-O` binaries. The
`source_drift` suite passes with the two-manifest check. `SWIFT_MODULE_CACHE`,
which `build.sh` accepts today because sandboxed harnesses block `~/.cache`,
is either retired (the cache lives in the build directory) or passed through
to Meson; either way its header comment changes.

**Stronger acceptance before promotion (the cutover gate).**

1. `make build`, then the full default battery against `dist` (`make test`
   or a named run directory), green with no skips, unrun cases or harness
   errors.
2. The opt-in controls that touch what changed: `preflight/signed_artifact_controls`
   (real signatures over copies of the new app),
   `witness_contract/order_barrier_mutations` (compiles the host from the Meson
   manifest), `smoke/runner_caller_auth`, and, from a logged-in GUI session,
   `runner_byoxpc` (the copied XPC bundle with Meson-built host, worker and
   validator installed as a Mach service and verified).
3. The behavioural comparison against the current release in
   [Equivalence](#equivalence-what-the-cutover-can-and-cannot-certify).
4. `make notarize NOTARY_KEYCHAIN_PROFILE=entitlement-jail IDENTITY=...` once,
   as a rehearsal that spends one submission and ends in archive acceptance of
   the Meson-built ZIP. Whether to spend it at the cutover commit or to let the
   next real `make release` be that rehearsal is a human decision; the plan
   recommends spending it, because notarization is the one check that only
   Apple performs and it has refused ad hoc-signed helpers before.

**Cutover and rollback point.** The cutover is one commit. Rolling back is
`git revert` of that commit: `build.sh` compiles again, the identity
regenerates on the next build, the ignored build directory is inert. Because
`build.sh` deletes and recreates the bundle every run, no artifact can mix
binaries from both producers. Do not keep a `PW_NATIVE=` switch that selects
the producer at run time; two producers behind one script is the dual
ownership the brief asks to avoid.

**Documentation that follows the cutover** is listed in the next section but
one. The Makefile's header comment on `build` changes one sentence
("compiles" becomes "runs the generator checks, Cargo and Meson, then signs").

**Confidence in the difficulty estimate:** medium. The mechanics are small;
the gate is the work.

## Equivalence: what the cutover can and cannot certify

The current release is `v0.2.7` in `dist/archive/v0.2.7/` (published, with
`origin.kind: github_release`). A Meson-built app cannot be compared with it by
bytes: the stamp differs, every signature carries its own timestamp, the
evidence manifest carries `generated_at`, and `swiftc` output is not
reproducible even with the same build system (**Observed**). The comparison
that is available, and that the plan proposes as the cutover's
behavioural-equivalence check, is:

- **Artifact structure.** `artifact.inspect` passes; the set of
  `(id, kind, rel_path)` triples in `manifest.json` is equal, and the
  `entitlements` object of every entry is equal; `symbols.json` entries are
  equal (the exported `_pw_*` markers); for every executable, the undefined
  `_sandbox_*` import set, the dynamic library list and the load-command
  structure are equal; `Info.plist` keys are equal with only the four stamp
  values differing.
- **Behaviour.** The default battery passes against the new app; release
  acceptance (`tests/accept-release.sh`) passes on the new ZIP after
  notarization; the five request fixtures under `tests/fixtures/pw_runner/`
  produce envelopes equal to the released app's after removing volatile
  fields. **Observed** in the rehearsal, the volatile classes are PIDs,
  wall-clock and monotonic timestamps and deadlines, elapsed durations, the
  observer's raw `log show` text and deny lines, bundle identifiers, service
  names and paths, the client `argv`, and the `stdout_bytes_*` counts; against
  a different build the four `build` stamp values join them. Everything else,
  including every `comparison` record and verdict, was equal. The consumer in
  `tests/lib/consumer.py` is the reader to validate both envelopes with first,
  since it is the one the suites share.

What the suite cannot certify, and the plan does not claim: notarization
acceptance (only the rehearsal shows it); timing behaviour under load; that
two Swift binaries from the same sources are the same program (no build system
offers this here; the battery and the harness suite are the evidence); and
that the Meson-built app has no behaviour the fixtures and the battery do not
exercise, which is equally true of today's app.

## Documentation and identity changes by chunk

Only ownership changes are updated; no facts are copied into a second place.

| Chunk | File | Change |
| --- | --- | --- |
| 1 | `docs/generate_worker_identity.py` | `SOURCE_FILES` gains `meson.build`, `meson.options`; regenerate the three regions. |
| 1 | `.gitignore` | ignore the build directory. |
| 1 | `docs/SIGNING.md` "Build" | requirements gain Meson and Ninja with the minimum version; one sentence that Meson compiles the native executables (Chunk 3 wording; in Chunks 1 and 2 say it builds a comparison copy). |
| 1 | `AGENTS.md` Quick Router | the "Build + signing" row names `meson.build`. |
| 2 | `tests/suites/source_drift/README.md` and `check.py` | the source-set invariant names three manifests, then two after Chunk 3. |
| 2 | `runner/Package.swift` comment | "must be added to build.sh's swiftc invocation" becomes "to meson.build"; the drift sentence follows. |
| 2 | `tests/OPT_IN_TESTS.md` "Order barrier mutation controls" | the control follows the Meson manifest. |
| 2 | `Makefile` | the optional `native` target and its header lines. |
| 3 | `build.sh` header | the input list drops `SWIFT_MODULE_CACHE` (the cache moves into the build directory) and the outputs paragraph says the binaries come from Meson. |
| 3 | `README.md` "What ships" | the sentence that `./build.sh` assembles the Rust, Swift and C pieces says Meson compiles the Swift and C ones. |
| 3 | `runner/AGENTS.md` and `runner/README.md` | "Production builds still go through build.sh" stays true; add that the compile step is Meson's. |
| 3 | `docs/CONTRACT.md` "Build stamp" | unchanged in substance; the stamp still comes from `build.sh`. |
| 3 | `docs/architecture.json` | **Proposed, needs review:** the `build` node's `Guards` fact says it runs the checks, Cargo and Meson, then signs; a new `source`-kind node `meson_build` ("meson.build") with an edge to `drift_check` labelled "source list equals the tree", cited to the new `check.py` rule. The node's check citation must be a `test` or `rule` (G5); the rule is the one Chunk 2 adds. Regenerate with `python3 docs/generate_architecture.py`. This records a build-graph fact in the document graph only because a drift rule verifies it; it does not draw the compile graph, which `meson introspect` and `ninja -t graph` already render on demand. |

What demonstrates that a documented build edge is real: the drift rule that
compares the Meson source list with the tree (a `rule` citation), the identity
controls that show a flag edit changes the identity (`contract.py`), and the
layout and live-identity suites that compare the compiled worker with the
Swift host (`runner_abi_layout`, `runner_live_worker_identity`). A sentence in
a README is a place to look, not evidence, consistent with G5 and G10.

The prose rules do not scan a root-level Markdown file other than `README.md`
and `AGENTS.md` (`scanned_documents` in `generators.py`), so this plan is not
subject to the span and citation rules. Edits to `docs/SIGNING.md` are; keep
duration and size literals out of the added sentences.

## Decisions and risks for human review

Decisions:

1. Add Meson and Ninja to the development-tool requirements, and pin a
   minimum Meson version (1.9 for `swift_module_name`; 1.12.1 is what was
   observed to work).
2. Name and location of the build directory (`builddir/` at the root is the
   Meson convention) and the `meson.build` at the repository root.
3. Accept that the identity value changes at each chunk, with `meson.build`
   and `meson.options` joining the digested file list from Chunk 1.
4. Whether to widen `FORM_RULES` so `meson.build` can be cited as a `control`
   in the manifests, or to cite it only as a `source` (the plan assumes the
   latter).
5. Whether the Chunk 3 cutover spends a notarization rehearsal or waits for the
   next release.
6. Whether to retire `controller/tools/sb_api_validator/build.sh` once the
   validator is a Meson target (a developer could sign the Meson output ad hoc
   with `debug.ent` instead).
7. Whether the optional `make native` target is wanted at all.

Risks:

- Meson's Swift support is younger than its C support. The probe used
  `swift_module_name`, a `-working-directory` compile and a static-library
  link, all of which behaved; a Swift or Meson upgrade could change the
  implicit arguments. Mitigation: the structural comparison in each chunk's
  cheap validation, kept as a small script so it is rerun after toolchain
  updates.
- Meson's implicit linker flags differ from `build.sh`'s. The probe found no
  structural effect; the comparison must be repeated on the real `meson.build`
  and after Meson upgrades.
- A stale build directory after `PW_INSPECTION` changes. `build.sh` must
  always pass the option and reconfigure; a `meson compile` alone would ship
  the previous flavour.
- The checks that parse `build.sh` fail closed when the file changes shape,
  which is their purpose; Chunk 2 should land the new readers before Chunk 3
  removes the old text, so the suite is never green by accident.
- `check_planner.py` and the two build-refusal controls copy a fixed file
  list; forgetting `meson.build` there makes a control fail for a reason that
  looks like drift.

## Stopping points

- **After Chunk 1, remove it** if the structural comparison fails or if the
  team decides the tool requirement is not worth two C compiles and a shim.
  Nothing shipped depended on it.
- **Cut over the C tools only.** If Chunk 2 shows the Swift host cannot be
  reproduced structurally, or the three readers prove more invasive than
  expected, a reduced Chunk 3 moves only steps 7, 8 and 11 of `build.sh` into
  Meson and leaves the two `swiftc` calls where they are. The identity file
  list is already right; `check.py` keeps parsing `build.sh` for Swift. This is
  a stable end state, smaller than the full candidate scope, and it still
  removes the in-tree binaries and the untracked headers.
- **Do not stop between Chunk 2 and Chunk 3 for long.** That is the state in
  which two files own the same compile flags and three checks compare three
  manifests; it is meant to last one review cycle.

## Rehearsal of the Chunk 1 acceptance check

**Observed** on 2026-10-07, using the probe's Meson-built `pw-probe-runner`
and `sb_api_validator` (unsigned, from `.tmp/meson-probe/build/`) and the
`dist/PolicyWitness.app` that `make build` had just produced from the same
commit. The script lived in the session scratch directory and the copy under
`/private/tmp`; both were removed afterwards, and `dist` was not touched.

1. `ditto` the app to a temporary directory; replace the two helpers inside
   `PWRunner.xpc/Contents/MacOS`; give the app and the service fresh
   `CFBundleIdentifier`s; sign the two helpers, then the service with its
   entitlements plist; run `build-evidence.py`; sign the app with its
   entitlements; `codesign --verify --deep --strict`. Every step exited 0 and
   `artifact.inspect` reported no errors, so the dispatcher admitted the copy.
2. `PW_APP_DIR=<copy> tests/run.sh --case smoke/specimen_file_read_deny --case
   witness_contract/happy_path_baseline --suite runner_c_worker_harness --suite
   validator_batch_mode --suite runner_live_worker_identity` into
   `tests/out/runs/meson-pilot-rehearsal`: 36 of 36 cases passed with no skips
   or unrun cases, the copy inventoried unchanged, in about 28 s. The 31
   harness cases drive the Meson-built worker through the shared-memory ABI
   with no host; the live-identity case observes the worker's PID and
   `sandbox_check` verdicts from the OS side.
3. Each of the five request fixtures under `tests/fixtures/pw_runner/` was
   run through both apps directly. All ten runs exited 0 with
   `normalized_outcome: ok`. Flattening the envelopes and comparing leaf by
   leaf, between 326 and 373 leaves per envelope, 35 to 41 differed, and every
   differing path was one of: a PID, a wall-clock or monotonic timestamp or
   deadline, an elapsed duration, the observer's `log show` output and raw
   deny lines (which carry PIDs and times), the copy's bundle identifiers,
   service name and paths, the client `argv` that names the service, and the
   two `stdout_bytes_*` counts that follow from the longer identifiers. Every
   `comparison` record, `sandbox_check` verdict, attempt outcome and
   disposition field was equal. The `data.specimen.binaries` dossier is
   `null` for the built-in runner in both apps; it is populated only for
   BYOXPC targets, so the manifest-baseline comparison for a built-in app is
   the one `artifact.inspect` performs.

This is the evidence the pilot's promotion gate asks for, obtained once with
probe outputs rather than with a root `meson.build`; Chunk 1 should repeat it
with the real file and keep the normalised-envelope comparison as a small
script beside the structural one.

## Baseline battery

**Observed:** `tests/run.sh` against the freshly built `dist` app, into
`tests/out/runs/meson-plan-baseline`, took about 6.4 minutes and completed
all 168 selected cases: 167 passed, 1 failed, no skips, no unrun cases, the
app inventoried unchanged. The failure is `unit/rust.fmt`: `cargo fmt --check`
reports formatting differences in `controller/src/runner_commands.rs` at
commit `06fc25e`, before and independently of anything in this plan. It is
reported here so the cutover gate's "green battery" is read against a known
baseline; it should be fixed on its own.
