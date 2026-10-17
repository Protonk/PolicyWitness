# Enforce Apple Silicon outputs

PolicyWitness's supported product is macOS code for Apple Silicon. Make that
restriction explicit in target selection, compilation and artifact acceptance:
every executable delivered by the build must be a thin `arm64` Mach-O for
macOS. An Intel-only executable, an `arm64e` executable or a universal binary
containing additional architectures is outside this policy.

This is an implementation plan. Follow
[CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change),
[BUILD.md](docs/BUILD.md) and [tests/AGENTS.md](tests/AGENTS.md) when executing it.
The restriction concerns outputs. It does not require the shell, Python, Cargo,
Meson or compilers to execute natively on Apple Silicon, and it does not reject
a build merely because Rosetta or cross-compilation is involved. Native-build
enforcement is a separate possible extension described below.

## Policy and boundaries

Apply the output rule to the controller, Rust helpers, Swift client and XPC
host, C worker, validator and extension issuer. Check every executable the
pipeline builds, including the C helpers built with `BUILD_XPC=0` and the
standalone observer it signs in Cargo's output directory. Both inspection
settings and both fresh and incremental builds have the same target policy.
Any subsequently shipped framework or dynamic library must join the artifact
inventory and satisfy the same rule. A universal dependency used as a link
input is acceptable when the resulting delivered code is thin arm64.
Debug-symbol files inside dSYM bundles are not executable/library outputs;
their metadata must not be mistaken for a runnable Mach-O's platform contract.

Keep the macOS deployment minimum and selected SDK as separate requirements.
An arm64 iOS binary is not a macOS binary. Preserve the existing minimum, SDK,
signer, source-list and worker-identity checks alongside architecture checking.
Architecture establishes neither signing validity nor source provenance.

This work covers build outputs and app artifacts admitted by the test and
release machinery. It does not add runtime checks, change external-runner
registration/admission, or certify arbitrary previously installed runners.
A thin arm64 executable has no x86_64 slice for Rosetta to execute. Any future
runtime policy for external bundles needs its own scope and tests.

Keep this work independent of [worker timing](docs/LIMITS.md#execution-budgets).
Do not change wait logic, clocks, release stores, query eligibility, shared-memory
layout or specimen contracts. Regenerate worker identity and rebuild the changed
sources before crediting integrated results.

## Basis for the design

Apple documents explicit compiler architecture selection and inspection with
`lipo -archs`. Its normal recommendation is universal distribution; arm64-only
distribution is our narrower support decision. See
[Apple's universal-binary guide](https://developer.apple.com/documentation/apple-silicon/building-a-universal-macos-binary)
and [command-line compilation example](https://developer.apple.com/documentation/xcode/embedding-a-helper-tool-in-a-sandboxed-app).
This pipeline has no Xcode project: setting `ARCHS` alone would not constrain
Cargo or Meson.

Meson's `host_machine` describes where the compiled product runs;
`build_machine` describes where compilation happens. Use the former for the
product restriction and preserve the distinction in diagnostics and records.
See [Meson's cross-compilation documentation](https://mesonbuild.com/Cross-compilation.html).

Cargo's `--target` selects the output platform and changes its artifact layout.
`build.target` is an overridable default. In a build script, `TARGET` and
`CARGO_CFG_*` describe the product; Rust `cfg!` describes the build script itself.
See [Cargo target configuration](https://doc.rust-lang.org/cargo/reference/config.html#buildtarget)
and [build-script inputs](https://doc.rust-lang.org/cargo/reference/build-scripts.html#inputs-to-the-build-script).

## Implementation sequence

### 1. Establish the output predicate

Add a small shared artifact helper under `tests/lib/` using the existing bounded
tool-probe conventions. Inspect bytes without executing the program. Require a
thin Mach-O, exactly the architecture `arm64`, and the macOS platform in its load
commands. Use `lipo -archs` for architecture names and inspect the Mach-O header
to distinguish a thin file from a one-slice fat container. Reuse the existing
load-command reader where appropriate. Substring matching for `arm64` is
insufficient.

Return observed architecture/container/platform separately from the policy
decision. Missing files, failed probes, empty or malformed results, unknown
architectures and unreadable headers refuse with an artifact path and bounded
diagnostic. This helper must not query the builder's CPU or translation state.

Establish its behavior with real small Mach-O fixtures: thin arm64, thin x86_64,
universal arm64/x86_64, one-slice fat, and malformed/non-Mach-O files. Cover a
platform mismatch as well. Independently inspect fixture headers so the checker
is not its own oracle. Complete these controls before integrating the predicate.

### 2. Select and restrict Rust outputs

Change [build.sh](build.sh) to invoke Cargo with the single explicit target
`--target aarch64-apple-darwin`. Keep the selected SDK and deployment target.
Do not require Cargo's or rustc's host triple to equal the output triple.

Add an early package-wide check in [controller/build.rs](controller/build.rs)
requiring `TARGET == aarch64-apple-darwin`. This covers all shipped Rust binaries,
including direct Cargo invocations. Preserve build-stamp invalidation. Do not
use host `cfg!` or duplicate a guard in each binary. No workspace Cargo default
is needed: the managed invocation selects the target and the package check
enforces it.

Treat lower-precedence Cargo target configuration as overridden by the managed
command, not as an automatic error. Direct explicit x86_64 compilation must
fail intentionally. Continue admitting compiler/wrapper selection and child
environment; use the effective output triple, rather than rustc's host triple,
when attributing target-specific Rust flags.

Migrate artifact and cache paths together. Under the existing pinned
`controller/target/`, shipped executables now live in
`aarch64-apple-darwin/release/`; host build scripts and procedural macros can
still use `release/`. Update [build_provenance.py](tests/lib/build_provenance.py),
[cargo_config.py](tests/lib/cargo_config.py), Cargo-message admission,
fingerprint association, standalone observer signing, fixture wrappers and
commands/documentation that assume the old shipped paths. Search for these
assumptions across the repository.

Fresh mode must admit and replace both release areas plus `builddir/` before
compiling. Admit the triple directory and its release child with the existing
ownership, symlink and lock rules. Preserve debug profiles, unrelated target
triples and Cargo downloads. Keep session/messages at their existing parent
location. Require every shipped Cargo target to report rebuilding in fresh
mode, binding each judgment to its new admitted executable.

### 3. Enforce the native compilation target in Meson

In [meson.build](meson.build), require the configured host system to be Darwin
and its CPU family to be `aarch64`. Apply the assertion in both variants and on
configuration/regeneration. Do not assert the build-machine CPU or reject
`meson.is_cross_build()`.

Pass explicit `-arch arm64` through C compilation and linking, including the
shim. Replace the host-derived Swift architecture with the fixed
`arm64-apple-macosx<minimum>` target at compile and link. Keep the deployment
minimum and fixed-options policy. Preserve compiler selection and forwarding
wrappers; target selection must not silently replace the operator's compiler.

Keep the normal native setup entry point. Correctly configured arm64/macOS
cross files remain admissible for direct Meson builds; this task does not add a
new general cross-build interface to `build.sh`. A translated Meson process
whose default configuration selects x86_64 receives a target-configuration
error, not a claim that translation itself is forbidden. Document selecting an
arm64 target environment separately from selecting a native build process.

Extend the toolchain stamp with the configured output system/CPU, fixed target
arguments and Cargo output triple. Compare these on reuse before compilation.
Do not equate a compiler's default target in version output with the target
selected by its effective arguments. Old stamps lacking this contract require
explicit fresh recovery; never relabel an old cache as arm64-compatible.
Unchanged compatible caches remain reusable.

### 4. Gate produced and assembled artifacts

Run the output check after each toolchain produces its executables, before
assembly and before executing the worker for its identity check. Check reused
outputs on every build. Preserve previous distribution bytes on pre-assembly
refusal.

Check the actual assembled executable inventory again before the first
distribution signature, including controller and service mains signed through
bundle seals. This covers the interval between checking a compiler output and
signing its copied bytes. Check the standalone observer at its own signing
boundary. Retain signature verification and check the assembled bundle's
architectures again before packaging. Do not automatically thin or repair a
forbidden output.

Add the byte-level requirement to [artifact.py](tests/lib/artifact.py), which
admits app-dependent tests and release artifacts. Keep it read-only and collect
independent signature, manifest and provenance errors. Inspect every required
executable regardless of the manifest's claims and any additional delivered
Mach-O executable, dynamic library or loadable code bundle; inventory changes
must not provide a bypass. Exclude dSYM debug data from this runnable-code scan.
Partial builds retain their existing incomplete-bundle status while satisfying
the output restriction.

### 5. Record output facts without claiming native construction

Extend the session and embedded provenance with an explicit fixed
`output_target` (macOS, arm64, Cargo triple, thin-container requirement). Record
each shipped executable's architecture/container alongside its existing
platform, minimum, SDK and UUID. Compare those observations with the bytes in
app and archive inspection. The declared target alone cannot satisfy the check.
Include the controller even though its final hash remains outside the embedded
record for the existing signing reason.

Update producers, shape validation, fixture writers, substitution records,
archive readers and documentation together. Bump the provenance and toolchain
stamp schemas for newly required fields, and the session schema for its changed
shape. Current candidate acceptance requires the new contract. Preserve old
signed records intact and keep historical archive reading explicitly
version-aware; never synthesize observations into an old signed record. No
request/reply/envelope version changes are needed.

The output record must make no claim about compiler translation. Retain
compiler-host observations as toolchain facts with their existing meaning.
Do not add a `native_build_verified` field, a disabled enforcement switch or
speculative translation probes in this implementation.

## Build execution and future native-build enforcement

The pipeline executes `pw-probe-runner --version` to compare the built worker's
identity with the generated identity. Preserve that check. Producing arm64 code
and executing this validation are different capabilities: an Intel builder may
compile arm64 successfully and still be unable to complete the signed pipeline.
Do not skip identity validation or replace it with a search for a string in the
binary to make such a build pass.

This work introduces no builder-architecture prohibition, but it does not
promise a newly supported end-to-end Intel-hosted build workflow.
Cross-compilation experiments can establish compilation and inspection without
establishing complete signed-build acceptance. Separating or relocating
execution-dependent validation is additional work requiring its own evidence.

A future native-build requirement belongs in a separate build-execution
admission step before cache mutation and compilation. Define which processes
must be native, obtain observations for those processes, and give the check its
own diagnostic and controls. Apple's
[Rosetta documentation](https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment)
describes `sysctl.proc_translated`; it observes the querying process, not every
descendant. Neither a native launcher nor an arm64 slice in a compiler file
certifies the execution architecture of the whole toolchain.

That extension can add execution-policy fields and compatibility rules without
changing the output target, accepted artifact set or output checks. Keep
function names and fields specific to either output target or build execution.
Implement the separation now without creating an unused policy framework.

## Verification and evidence

Extend existing equipment where it owns the boundary:
`preflight/build_provenance_controls`, `preflight/build_guard_controls`,
`preflight/build_refusal_controls`, `preflight/signed_artifact_controls` and
`source_drift/build_documentation`. Register additional cases with their actual
equipment requirements.

| Control | Required result |
| --- | --- |
| Arm64 success | Fresh full and partial builds produce allowed outputs; inspection on/off preserves the target. A full signed candidate passes artifact inspection and native execution checks. |
| Cargo selection | Managed builds select arm64 despite an overridden x86_64 default. Direct explicit x86_64 compilation fails at the package guard. Check target-specific flag attribution with a differing compiler-host triple where available. |
| Meson selection | x86_64 host configurations fail deliberately, including incompatible regeneration; arm64 cross configurations are not rejected merely for being cross. Partial builds still avoid Swift discovery. |
| Cache transition | Old/incorrect target stamps refuse reuse before compilation; fresh recovery removes only admitted release areas; unchanged arm64 reuse succeeds with every cached executable checked. |
| Artifact substitution | Real x86_64, universal and malformed outputs substituted after compilation fail before assembly. Substitution during copying is caught before distribution signing. |
| Inspector independence | Copies with valid signatures and consistent hashes, but forbidden architectures, fail for architecture. Conflicting provenance and bytes remain visible as separate faults. |
| Guard sensitivity | Removing the output guard, weakening equality to arm64 membership or moving it past its protected operation makes its control fail. Unrelated minimum/SDK/identity failures supply no architecture-guard credit. |
| Builder distinction | Where available, translated build processes configured for arm64 reach target/output checks without a translation-policy refusal. Record full signed-build success separately. |

Use separate checkouts for independent build caches and locks: `DIST_DIR` alone
does not isolate Meson or Cargo state. Use fresh managed `PW_TEST_OUT_DIR`
directories. Retain commands, fixture architectures, configurations, stage
receipts, diagnostics and artifact observations. Follow the existing escalation
rule for harness-blocked signing, Swift discovery, XPC or logs against unchanged
artifacts.

Inspect selections with `--list`, run the affected controls, then run the default
battery against the final full signed candidate. Follow existing native-build
comparison guidance for live worker and ordering coverage. The opt-in ordering
mutations become mandatory if implementation changes the wait, release store or
query eligibility; this plan requires no such change.

No new equipment experiment has been performed in preparing this plan. Record
actual OS/SDK, toolchains, architectures and signing equipment during execution.
Missing Rosetta or an Intel builder is a gap in builder-compatibility evidence,
not an architecture rejection or passing test. Native arm64 success and real
forbidden-output rejection are required local acceptance evidence; missing
equipment for those controls blocks their acceptance. Local success does not
certify untested builders.

## Documentation, generation and completion

Update [docs/build.json](docs/build.json) for target selection, Cargo paths,
fresh-mode ownership, stamp compatibility, checks/refusals, invocations and
controls. Update authored explanations in [docs/BUILD.md](docs/BUILD.md) and
[docs/SIGNING.md](docs/SIGNING.md), prerequisites/support statements in
[README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md) and the user guide,
and affected test/fixture READMEs, catalog, coverage and opt-in registry.
Describe arm64-only outputs and execution prerequisites accurately; an arm64
product does not establish native construction.

Regenerate the build account with `docs/generate_build.py` and affected shared
guide material with its owner. Changes to `build.sh` and `meson.build` require
`docs/generate_worker_identity.py` before each candidate build. Run generator
checks and `source_drift`; never hand-edit generated copies. There is no planned
protocol-layout or process/channel change. Update architecture citations only
where implementation changes their supporting facts.

Completion requires target enforcement in all build variants, safe fresh/reuse
behavior under the new Cargo layout, rejection of forbidden distribution
artifacts, provenance/readers that agree with the bytes, and a signed arm64
candidate passing the required controls and default battery. The handoff must
identify accepted source/build and run IDs, separate observed builder
compatibility from untested configurations, and leave native-build enforcement
explicitly unimplemented.
