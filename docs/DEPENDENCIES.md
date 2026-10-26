# Build dependencies

What a machine needs to build PolicyWitness from source, and what each
dependency does. **Enforced** names the check that refuses when a requirement
is unmet; **known to work** is the toolchain the current build was made with,
which every built app records in its
[provenance record](SIGNING.md#the-provenance-record). [BUILD.md](BUILD.md)
describes how a build runs; [SIGNING.md](SIGNING.md#release-procedure) covers
what a release adds.

## For an ordinary build

`make build IDENTITY=...`, or `build.sh` directly, needs:

| Dependency | Role in the build | Enforced | Known to work |
| --- | --- | --- | --- |
| An Apple Silicon Mac, with the build started from a native shell | Every executable the build delivers is thin arm64 macOS code, and the build script's own process must not run translated | `hw.optional.arm64` must read `1` and `sysctl.proc_translated` `0` before anything else runs ([`this build runs only natively on Apple Silicon`](../build.sh)); Meson and the controller's build script refuse any other host or target ([`host_machine`](../meson.build), [`OUTPUT_TRIPLE`](../controller/build.rs)) | macOS 26 |
| Xcode Command Line Tools, or Xcode | `clang` compiles the C worker, validator, issuer and shim; `swiftc` the XPC host and client (`BUILD_XPC=1`); the macOS SDK, `xcrun`, `dsymutil`, `otool`, `git` (the version stamp) and `make` come from the same installation | `xcrun --sdk macosx` must resolve an SDK with a numeric version ([`SDK_REQUEST`](../build.sh)); Meson must find a C compiler and, with the XPC pieces, a Swift compiler; every output must carry that SDK's version and the plist's `26.0` minimum ([`LSMinimumSystemVersion`](../Info.plist), [`sdk_check`](../tests/lib/build_provenance.py)) | Xcode 27.1 with SDK 27.0, Apple clang 21.0.0 and Swift 6.4 |
| Rust: `cargo` and `rustc` on `PATH` with the `aarch64-apple-darwin` standard library, the default installation on Apple Silicon | Builds `policy-witness` and `sbpl-check`; Cargo fetches the crates `controller/Cargo.lock` pins | Cargo refuses a toolchain older than the manifest's [`rust-version`](../controller/Cargo.toml) of 1.89; a rustup-proxied `cargo` needs `rustup` on `PATH` or `RUSTUP_TOOLCHAIN` set, so the build can record the toolchain ([`launcher`](../tests/lib/cargo_config.py)) | rustc and cargo 1.99.0 through rustup 1.29.1 |
| Meson | Configures and compiles the native targets under the fixed flag policy of [`fixed_options`](../meson.build) | `meson` on `PATH` ([`meson and ninja are required for the native build`](../build.sh)); [`meson_version`](../meson.build) `>=1.12.1` | 1.12.1 |
| Ninja | Meson's build backend; its dependency log is what the source-closure check reads after compiling | `ninja` on `PATH` at version 1.13.2 or newer ([`NINJA_MINIMUM`](../build.sh)) | 1.13.2 |
| Homebrew's `python@3.14` formula | Runs every build helper, from the checkout lock to the evidence manifest; the helpers import only the standard library and this tree, so no packages are installed | Exactly `/opt/homebrew/opt/python@3.14/bin/python3.14`, resolving into a `/opt/homebrew/Cellar/python@3.14/3.14.*` keg and reporting that version when probed, with no `PYTHON*` variable set beyond the three the helpers own ([`PW_PYTHON_PIN`](../tests/lib/python_start.sh)) | 3.14.8 |
| A Developer ID Application identity in the login keychain | Signs every executable and both bundle seals with the hardened runtime | `IDENTITY` must name an identity that `security find-identity -v -p codesigning` lists ([`IDENTITY_LISTING`](../build.sh)); every signature must then carry the Developer ID chain, the team and a timestamp ([`signature_problems`](../tests/lib/signer_check.py)), so ad hoc and Apple Development identities fail | |

`brew install meson ninja python@3.14` installs the Homebrew formulae. Rust
comes from rustup or any installation that puts `cargo` on `PATH`; Homebrew's
`rustup` formula is keg-only, so its `/opt/homebrew/opt/rustup/bin` has to be
on `PATH` itself. The Command Line Tools carry every Apple tool this document
names, `swiftc`, `notarytool` and `stapler` included, so full Xcode is not
required. macOS itself supplies the rest of what the scripts call: `bash`,
`sysctl`, `security`, `codesign`, `PlistBuddy`, `ditto`, `spctl`, `launchctl`
and `log`. The Makefile is a thin layer over `build.sh`, written for the
`make` 3.81 the Command Line Tools install.

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

Live cases also need a working XPC lookup, which the dispatcher does not
preflight: a blocked case runs and fails with evidence. The
[change-verification guide](../tests/CHANGE-VERIFICATION.md) explains control
applicability and consequential operating conditions. The catalog and `--list`
record membership and declared equipment requirements. Individual controls can
impose additional conditions, such as the
[toolchain-switch control's distinct developer toolchains](../tests/CHANGE-VERIFICATION.md#build-toolchain-switch-controls).

## Conditions no package supplies

- **Apple Developer Program membership.** The Developer ID Application
  certificate and its private key must be in the login keychain of the user
  who builds. The build selects nothing by itself and accepts no other
  identity class.
- **Network access.** Every `codesign --timestamp` call reaches Apple's
  timestamp service, and Cargo downloads the pinned crates on the first build
  and after `Cargo.lock` changes. A release also reaches Apple's notary
  service and GitHub.
- **A git checkout.** The version stamp is the nearest `v*` tag and the commit
  count. Outside a checkout, `PW_VERSION` and `PW_BUILD_NUMBER` supply them
  and the describe string and commit read `unknown`. A release refuses
  anything but a clean checkout at an annotated tag.
