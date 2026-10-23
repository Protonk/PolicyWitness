# Build dependencies

What a machine needs to build PolicyWitness from source, and what each
dependency does for the build. [BUILD.md](BUILD.md) describes how a build
runs, [SIGNING.md](SIGNING.md#release-procedure) the release procedure and
[tests/README.md](../tests/README.md) the test commands. What a user needs to
run the app is in the [user guide](PolicyWitness.md).

Each table separates what the build **enforces** (a check that refuses when
unmet, with its source) from versions **known to work**. The known-to-work
values are the toolchain named by the provenance record of a current build on
the maintainer's machine, and that machine's versions of the few tools the
record does not cover. Every build embeds its record at
`Contents/Resources/Evidence/provenance.json` ([the provenance
record](SIGNING.md#the-provenance-record)), and a build's own record is the
authoritative statement of what built it. Where nothing enforces a minimum,
none is claimed.

## For an ordinary build

`make build IDENTITY=...`, or `build.sh` directly, needs:

| Dependency | Role in the build | Enforced | Known to work |
| --- | --- | --- | --- |
| An Apple Silicon Mac, with the build started from a native shell | Every executable the build delivers is thin arm64 macOS code, and the build script's own process must not run translated | `hw.optional.arm64` must read `1` and `sysctl.proc_translated` `0` before anything else runs ([`this build runs only natively on Apple Silicon`](../build.sh)); Meson refuses a host machine other than arm64 macOS ([`host_machine`](../meson.build)); the controller's build script refuses any Cargo target but `aarch64-apple-darwin` ([`OUTPUT_TRIPLE`](../controller/build.rs)) | macOS 26 |
| Xcode Command Line Tools, or Xcode | `clang` compiles the C worker, validator, issuer and shim; `swiftc` the XPC host and client (`BUILD_XPC=1`); the macOS SDK, `xcrun`, `dsymutil`, `otool`, `git` (the version stamp) and `make` come from the same installation | `xcrun --sdk macosx`, or the caller's `SDKROOT`, must resolve an SDK with a numeric version ([`SDK_REQUEST`](../build.sh)); Meson must find a C compiler and, for the XPC pieces, a Swift compiler; every output must carry that SDK's version and the `26.0` minimum the plist declares ([`LSMinimumSystemVersion`](../Info.plist), [`check_minimum_macos`](../build.sh), [`sdk_check`](../tests/lib/build_provenance.py)) | Xcode 27.1 with SDK 27.0, Apple clang 21.0.0 and Swift 6.4 |
| Rust: `cargo` and `rustc` on `PATH` with the `aarch64-apple-darwin` standard library, the default installation on Apple Silicon | Builds `policy-witness`, `sandbox-log-observer` and `sbpl-check`; Cargo fetches the crates `controller/Cargo.lock` pins | Cargo refuses a toolchain older than the manifest's [`rust-version`](../controller/Cargo.toml) of 1.89; when `cargo` is a rustup proxy, `rustup` must be on `PATH` or `RUSTUP_TOOLCHAIN` set so the build can record the toolchain it selects ([`the Cargo launcher cannot be resolved without rustup on PATH or an explicit RUSTUP_TOOLCHAIN`](../tests/lib/cargo_config.py)) | rustc and cargo 1.99.0 through rustup 1.29.1 |
| Meson | Configures and compiles the native targets under the fixed flag policy of [`fixed_options`](../meson.build) | `meson` on `PATH` ([`meson and ninja are required for the native build`](../build.sh)); [`meson_version`](../meson.build) `>=1.12.1` | 1.12.1 |
| Ninja | Meson's build backend; its dependency log is what the source-closure check reads after compiling | `ninja` on `PATH` at version 1.13.2 or newer ([`NINJA_MINIMUM`](../build.sh)) | 1.13.2 |
| Homebrew's `python@3.14` formula | Runs every build helper: the checkout lock, the provenance, output and identity checks, the generated-copy checks, the evidence manifest and the staged guide | Exactly `/opt/homebrew/opt/python@3.14/bin/python3.14`, resolving into a `/opt/homebrew/Cellar/python@3.14/3.14.*` keg and reporting that version when probed; no `PYTHON*` variable may be set other than `PYTHONCOERCECLOCALE`, `PYTHONDONTWRITEBYTECODE` and `PYTHONOPTIMIZE` ([`PW_PYTHON_PIN`](../tests/lib/python_start.sh)). Helpers start with `-B -S` and import only the standard library and this tree, so no packages are installed | 3.14.8 |
| A Developer ID Application identity in the login keychain | Signs every executable and both bundle seals with the hardened runtime and a secure timestamp | `IDENTITY` must name an identity that `security find-identity -v -p codesigning` lists ([`codesigning identity not found in your keychain`](../build.sh)); after the seal every signature must carry the Developer ID chain, the identity's team and a timestamp ([`executables or seals not signed by`](../tests/lib/signer_check.py)), so an ad hoc or Apple Development identity fails there | |

`brew install meson ninja python@3.14` installs the Homebrew formulae. Rust
comes from rustup or any installation that puts `cargo` on `PATH`; Homebrew's
`rustup` formula is keg-only, so its `/opt/homebrew/opt/rustup/bin` has to be
on `PATH` itself. The Command Line Tools carry every Apple tool this document
names, `swiftc`, `notarytool` and `stapler` included, so full Xcode is not
required. macOS itself supplies the rest of what the scripts call: `bash`,
`sysctl`, `security`, `codesign`, `PlistBuddy`, `ditto`, `spctl`, `launchctl`
and `log`. The Makefile is a thin layer over `build.sh`, written for the
`make` 3.81 the Command Line Tools install.

## Conditions no package supplies

- **Native Apple Silicon.** A shell running under Rosetta (`arch -x86_64`) is
  refused before any other check.
- **Apple Developer Program membership.** The Developer ID Application
  certificate and its private key must be in the login keychain of the user
  who builds. The build selects nothing by itself and accepts no other
  identity class.
- **Network access.** Every `codesign --timestamp` call reaches Apple's
  timestamp service, and Cargo downloads the pinned crates on the first build
  and after `Cargo.lock` changes. A release also reaches Apple's notary
  service and GitHub.
- **An unsandboxed shell.** A restrictive automation sandbox can hide the
  keychain, block the per-user module cache `swiftc` uses during Meson's Swift
  discovery, make `codesign --verify` fail for unchanged bytes, and refuse the
  XPC lookup and unified-log access the live tests need.
  [BUILD.md](BUILD.md#sandboxed-automation-harnesses) and
  [AGENTS.md](../AGENTS.md#sandboxed-automation-harnesses) say how to diagnose
  it.
- **Homebrew at `/opt/homebrew`.** The interpreter pin is a path under
  Homebrew's default Apple Silicon prefix; a Homebrew installed elsewhere does
  not satisfy it.
- **A git checkout.** The version stamp is the nearest `v*` tag and the commit
  count. Outside a checkout, `PW_VERSION` and `PW_BUILD_NUMBER` supply them
  and the describe string and commit read `unknown`. A release refuses
  anything but a clean checkout at an annotated tag.

## For the tests

The default battery (`make test` or `tests/run.sh`) runs against the signed app
the build wrote. The dispatcher checks each case's declared equipment before
running it; missing equipment fails the run with the case left unrun, never an
implicit skip ([equipment checks](../tests/README.md#equipment-checks)).
`tests/run.sh --all --list` prints every case's requirements.

| Dependency | Role in the tests | Cases that need it |
| --- | --- | --- |
| A signed app from the build (`dist/PolicyWitness.app`, or `PW_APP_DIR`) | The subject of every live case; the dispatcher verifies its layout, signatures and evidence hashes before the run and inventories it again afterwards | `app` and `worker`: most of the default battery |
| `clang` | Compiles test fixtures and native controls | `clang`: most default suites |
| Cargo with `rustfmt` | `cargo test --bins` and `cargo fmt -- --check` on the controller crate | `cargo`: the `unit` suite; rustup's default profile includes `rustfmt` |
| Swift with SwiftPM (`swift run`) | Builds and runs [`PWRunnerCoreTests`](../runner/Package.swift) from the runner's package manifest; the tests are an executable target rather than XCTest, so the Command Line Tools suffice | `swift`: `runner_unit` |
| Meson | Introspects `meson.build` for the source-list and build-documentation checks; `source_drift/build_documentation` also configures Swift, so it needs an unsandboxed shell | `meson`: two `source_drift` cases |
| A Developer ID identity matching the app's team | Signs external (BYOXPC) runners and the build controls' fixtures; `PW_BYOXPC_IDENTITY` or `IDENTITY` names it, otherwise the keychain is searched for the app's team | `identity`: opt-in cases only |
| A logged-in GUI session | User-scope launchd registration of external runners; checked with `launchctl print gui/<uid>` | `gui`: opt-in BYOXPC cases |
| Rosetta 2 | One control runs the build script translated and requires the refusal; `softwareupdate --install-rosetta` installs it | `rosetta`: `preflight/translated_build_refusal_controls`, opt-in |

Live cases also need a working XPC lookup and unified-log access through
`/usr/bin/log`, which the dispatcher does not preflight: a blocked case runs
and fails with evidence. The opt-in cases and their equipment are listed in
[tests/OPT_IN_TESTS.md](../tests/OPT_IN_TESTS.md).

## For a release

`make notarize`, `make release` and `make publish`
([release procedure](SIGNING.md#release-procedure)) add:

| Dependency | Role in the release | Needed by |
| --- | --- | --- |
| `notarytool` with a stored keychain profile | Submits the ZIP to Apple's notary service once and waits for the verdict once; `xcrun notarytool store-credentials <name>` stores App Store Connect credentials under the name `NOTARY_KEYCHAIN_PROFILE` passes | `make notarize` and `make release`, which refuse without the profile name |
| `stapler`, `spctl` and `ditto` | Staple Apple's ticket, assess the stapled app with Gatekeeper, re-zip it, and extract the final ZIP for acceptance | the notarize chain and `tests/accept-release.sh` |
| `git` with the release tag and the remote | Preflight requires a clean tree at an annotated `v*` tag that the remote does not already hold under another commit; publication pushes the tag | [release_preflight.py](../tests/lib/release_preflight.py), [release_publish.py](../tests/lib/release_publish.py) |
| `gh`, authenticated to GitHub | Creates the GitHub release from the archive, downloads every asset back and compares digests before recording the release | `make publish` |

`notarytool` and `stapler` come with Xcode or the Command Line Tools; `gh`
from Homebrew (`brew install gh`), known to work at 2.102.0.

## Not needed for the build

- **Graphviz (`dot`).** Only [`generate_architecture.py`](generate_architecture.py)
  and [`generate_build.py`](generate_build.py) use it, to re-render the SVG
  figures when a document is regenerated. Their `--check` mode, the build and
  the tests read the SVG stamps and need no Graphviz, and `--skip-svg`
  regenerates without it. Known to work: 16.1.0.
- **Full Xcode.** The build uses no Xcode project and the tests no XCTest.
- **Python packages.** The helpers import only the standard library and this
  tree; the Markdown parser they use is vendored under `tests/lib/vendor/`.
  No `pip`, `uv` or virtual environment is involved.
- **Swift packages.** `Package.swift` declares no dependencies; the crates
  Cargo fetches are the only code downloaded.
- **CI.** The repository carries no CI configuration; the checks in this
  document are the build's own and the local battery's.
