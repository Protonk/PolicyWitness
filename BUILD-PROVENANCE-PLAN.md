# Build provenance plan

Make build provenance a bounded, inspectable part of every PolicyWitness
build. A maintainer should be able to identify the selected tools, SDK,
effective configuration and relevant inputs behind an artifact, connect that
account to the signed bytes, and recover the same account from an accepted
release. The build must detect incompatible reuse, provide an explicit fresh
release-build mode and verify signing guarantees on the resulting artifacts.

Acceptance requires:

- Each claimed distinction between materially different builds has a recorded
  field and an independent control that demonstrates the distinction. Cover
  changed compilers, SDKs and configuration with retained caches, and missing
  or inconsistent records; successful fresh builds alone are insufficient.
- Recorded settings describe actual selection and observed state. Required
  unknowns cannot establish compatibility, and fresh mode must safely replace
  its owned cache areas before claiming freshness.
- The embedded record, artifact checks and release archive agree about which
  bytes they describe. Signing claims come from the signatures actually made,
  with the outer seal's facts recorded outside the evidence it seals.
- Recording rules, build guards, embedded evidence, operator documentation and
  the signing/release procedure form one coherent account. Published fields
  and probe failures are bounded and exclude unrelated credentials and machine
  configuration.
- Simplifying refusal bookkeeping preserves each enforced predicate, protected
  boundary and behavioral control, including every Meson policy option. A
  recorded fact does not enforce it; reducing the row count is not a target.

Implement B1 through B4 as one coherent increment, including the manifest,
controls, fixtures, generated documentation and registries. Regenerate the
worker identity after the final edits to its inputs. Every retained or new
refusal must have its manifest row and control. B5 accepts the integrated
result against the gates below.

The record trusts the tools' reports about their inputs and outputs. It does
not prove reproducibility, compiler correctness, execution of particular bytes
or an exhaustive account of private runtime dependencies.

## Shared implementation requirements

- Keep the load-bearing guards: the configured source lists and identity
  closure ([native_sources.py](tests/lib/native_sources.py)), the per-output
  minimum and executable checks, the pre-sign source-identity recheck, the
  signer check, deep verification and the sealed evidence manifest. This plan
  adds facts and comparisons beside them and removes only refusals whose
  predicate and protected boundary another check preserves.
- Preserve "refuse instead of repair". A recorded fact that contradicts the
  policy or another recorded fact is a refusal with the fact in its message,
  never a silent correction.
- Edit [build.json](docs/build.json) with every script change and regenerate
  with `python3 docs/generate_build.py`; the build runs the check before
  compiling. Every refusal row keeps a control that produces it; the
  [build baseline](tests/fixtures/docs/build_baseline.json) stays empty. The
  release preflight allows that baseline to shrink, never to grow.
- Bound the recorded environment to named variables: `BUILD_XPC`,
  `PW_INSPECTION`, the fresh-build knob, `DEVELOPER_DIR`, `SDKROOT`,
  `MACOSX_DEPLOYMENT_TARGET`, `RUSTFLAGS`, `PW_VERSION` and `PW_BUILD_NUMBER`.
  Record effective compiler selection and Rust flags separately as structured
  tool/configuration observations; the environment allowlist does not imply
  that those variables are the only inputs the tools honor. Never dump `PATH`,
  the home directory, other variables, keychain contents or raw tool output.
  Normalize home-prefixed paths in published fields with an explicit redaction
  marker; retain exact paths privately where compatibility comparison needs
  them. Bound every field and probe, including failure diagnostics. Optional
  missing metadata is unknown; unavailable comparison inputs cannot establish
  toolchain compatibility.
- Follow [test guidance](tests/AGENTS.md): fresh output directories, controls
  that establish the boundary they claim, fixture bundles built outside the
  inspected app, no skips for missing equipment. Builds and signing need the
  unsandboxed shell; cargo lives under the Homebrew rustup prefix on the
  development machine.
- Do not state a new value or count in scanned prose outside a span; the
  build document's counts are spans the generator renders.
- Preserve acceptance controls as regression coverage in the owning suites.
  Unit tests cover parsing and state decisions; forwarding wrappers and real
  signed artifacts establish invocation, mutation and seal behavior. Expected
  observations must come from independent receipts or final bytes, not the
  helper being tested. Removing or bypassing a check must make its control
  fail, including an individual option in a collapsed Meson assertion row.

## B1 — Produce the sealed provenance record

**Current claim.** [build-evidence.py](tests/build-evidence.py) writes
`Contents/Resources/Evidence/manifest.json` and `symbols.json`: each helper's
hash as signed, its load-command UUID and entitlements, the augment hashes and
the time of writing. The plists carry the git describe string and commit.
Nothing records the compilers, the SDK, the effective configuration or the
build directories' state, and `builddir/meson-info`, Cargo's artifact report
and the load commands the minimum check parses are discarded.

**Change.** The evidence step also writes
`Contents/Resources/Evidence/provenance.json`, schema version 1, listed in the
manifest as an entry like `symbols.json` so the manifest and the app seal cover
it. Build the record from existing sources, extracting bounded parsing and
collection functions from the receipt recorder rather than copying its whole
output. Its current `tools()` captures `PATH`, and `Recorder.text()` embeds
stderr on failure; neither behavior belongs in the shipped record.

- `source`: commit, describe string, dirty flag, version, build number, the
  generated worker identity, and the hashes of `meson.build`, `meson.options`,
  `controller/Cargo.lock`, `Info.plist` and the two entitlement plists.
- `toolchain`: the developer directory and selected SDK path, version and
  build; Xcode's version and build when available; the configured C and Swift
  compiler commands and identities from Meson's introspection; the selected
  Rust compiler's version, commit hash and host; and the selected `cargo`,
  `meson` and `ninja` paths and versions. Probe the commands actually selected
  for compilation in the same configuration and working-directory context.
  Meson's empty Swift full version requires probing its configured command,
  not an unrelated `swiftc` found later. Distinguish discovery, configured
  identity and current observation instead of substituting one for another.
- `configuration`: the three knobs; the fixed-policy subset of Meson's
  effective options from `intro-buildoptions.json` plus `inspection` and `xpc`;
  effective Rust flag arguments and the kind of source that selected them;
  `MACOSX_DEPLOYMENT_TARGET`; `SDKROOT`; each build directory's observed fresh
  or reused state; and a sanitized projection of the B3 configuration stamp
  with its scope identified.
  [Cargo honors compiler overrides and flag sources](https://doc.rust-lang.org/cargo/reference/config.html)
  beyond `RUSTFLAGS`, including `CARGO_ENCODED_RUSTFLAGS` and Cargo
  configuration. Resolve them without copying unrelated configuration or
  secrets into the record. If an observation cannot establish effective
  settings, record that limitation;
  do not label requested settings as effective.
- `outputs`: for each shipped Mach-O, its bundle-relative path, UUID, platform
  minimum, SDK and linker tool version from `LC_BUILD_VERSION`. Include final
  signed hashes for the nested executables already signed at this point and
  compare them with the manifest and actual bundle bytes. The controller is
  explicitly excluded from this hash set: signing the outer app changes its
  signature, so its final hash cannot live inside the record that signature
  seals. The external release record carries its final signed hash instead.
- `signing`: the identity string and, for each nested signature made before
  the record, the leaf authority, team identifier and whether a timestamp is
  present, read from `codesign -dvv`. The app seal is made after the record
  and is verified by B2; its facts go to the release record, not into the
  sealed file.

A tool that cannot be read records a bounded failure entry for that field.
Nonzero exits, empty or malformed successful output, output overflow and
timeouts are distinct failures. Informational metadata failure does not stop
the build; a required identity or compatibility observation does. In the
partial build Swift compilation is not applicable and must not become a new
tool prerequisite. Define these field categories, size caps and deadlines
before implementing the reader; unknown values never compare as compatible.

The inspector ([artifact.py](tests/lib/artifact.py)) requires the file, checks
its schema and validates the output inventory, paths and unique entries before
comparing hashes with the manifest and final bytes. Matching incomplete lists
are insufficient. It checks directly observable output metadata as well as
hashes. The dispatcher fixture bundles
([fixture_bundle.py](tests/fixtures/dispatcher/fixture_bundle.py),
[selection.py](tests/fixtures/dispatcher/selection.py)) carry a record.
No embedded evidence is rewritten after the outer seal.

[release_archive.py](tests/lib/release_archive.py) reads the record from the
accepted final ZIP, copies those exact bytes into the archive's evidence and
records their hash in `release.json` beside the ZIP hash. The controller hash
and outer-signature facts are read from that same artifact. Verify the copied
record and its binding during staged archive verification before publication
by rename; never source provenance from a possibly newer working app. The
controller does not read the record; `app_provenance` is unchanged.

**Acceptance gate.** Retain the following controls in the provenance builder,
inspector, signed-artifact and release-archive suites:

- A real signed build passes deep verification and inspection. Independently
  hash final executables: nested hashes agree with both records, and the
  controller's final hash is external. Record write/sign ordering and require
  no embedded evidence writes after the seal; an unsealed evidence edit fails
  verification.
- Reject absent or unsupported records, missing or duplicate output entries,
  invalid paths, swapped records, contradictory load-command metadata and
  mismatched hashes. Include validly re-signed faulty copies so semantic
  rejection is established independently of signature failure.
- Forwarding compiler wrappers record real invocations. Configure with A,
  expose B to later discovery and exercise fresh and reused builds. Compatible
  builds identify the selected commands; an incompatible binding refuses
  under B3 rather than producing a misleading record. Name any observation
  that could not be established. Exercise Rust compiler overrides and
  conflicting flag sources, including encoded flags and configuration files;
  expected settings come from independent invocation receipts. Substituted
  version text alone tests
  parsing, not build attribution.
- Plant canaries in unrelated environment values, `PATH`, home-prefixed paths
  and tool stderr. Exercise nonzero, empty, malformed, excessive and hung
  probe output, including `worker --version`. Assert bounded completion,
  bounded failure entries and no forbidden data in embedded or archived
  records. A missing optional Xcode version remains informational; missing
  required comparison data refuses; a partial build does not require Swift.
- Build distinguishable A and B artifacts, retain A's accepted ZIP and replace
  the working app with B. Archive A's embedded record and final controller
  hash, or refuse a mismatch. Verify the staged copy and all recorded hashes
  against the accepted ZIP, including rejection of a swapped archive record.

**Retirement.** The build document's known gap narrows from "relies on the
tools' records to establish whether cached outputs are current" to "records
what the selected tools reported and the directories' state; it still relies
on the build tools for cache validity and does not establish source-to-binary
reproducibility". The evidence inventory in [SIGNING.md](docs/SIGNING.md)
lists the record and distinguishes sealed facts from final app facts held
outside the seal.

## B2 — Verify the signing guarantees on the final artifacts

**Current claim.** `IDENTITY` must begin with `Developer ID Application: `
and appear in the keychain listing; every signature passes `--options runtime
--timestamp`; [signer_check.py](tests/lib/signer_check.py) reads each
executable's leaf authority and runtime flag. The certificate's class and the
presence of a secure timestamp are never verified on the signed bytes.

**Change.** Extend the signer check to read the full authority chain, the team
identifier and the timestamp line for every executable it already lists and
for both seals: the chain must contain the Developer ID certification
authority and the Apple root, the team identifier must be the one the leaf
names, and a secure timestamp must be present. `Signed Time` is not a secure
`Timestamp`, as described in [Apple's signing diagnostics](https://developer.apple.com/documentation/security/resolving-common-notarization-issues).
Unreadable or ambiguous display output cannot establish either the chain or
timestamp guarantee. Retain real signature verification beside these parser
checks. Record bounded observations in the step's output. With
that, the identity prefix check before Cargo goes; the keychain presence
check stays, because it also tells a sandboxed harness's unreadable
keychain apart from a missing identity, and it refuses before any compile.

**Acceptance gate.** The build guard controls explicitly sign with
`--timestamp=none` to manufacture missing secure timestamps; merely omitting
`--timestamp` is not a reliable fault. Independently inspect the resulting
signature before crediting the control. Exercise a helper, the XPC seal and
the outer app seal separately, with enclosing seals valid where applicable.
The real deep verification and signer checks run; the latter names the
affected artifact and stops before standalone observer signing and packaging.
Unit controls cover wrong teams, inappropriate authority chains, missing
timestamps, `Signed Time` alone and malformed display output, beside valid
signatures. The signed build passes; the inspector's existing signer
consistency rule remains enforced. A tool/fixture failure is not evidence
that the intended signature fault was detected.

**Retirement.** The signing contract in the build document states that class
and timestamp are verified on the artifacts, replacing the sentence that says
they are not.

## B3 — Detect incompatible reuse and define the fresh release build

**Current claim.** The build refuses a Meson directory configured for another
checkout and otherwise trusts both directories as incremental state. The build
document says a compiler or SDK change needs a fresh directory because the
toolchain is not fingerprinted; `make release` and `make notarize` reuse both
directories.

**Change.** After successful Meson setup and observation of its actual selected
toolchain, atomically publish a versioned `builddir/pw-toolchain.json`. It
records the SDK path, version and build, developer directory, configured
compiler commands and versions, and the selected Rust compiler observation.
Its scope is the Meson configuration and the compatibility inputs observed
at setup; it does not attest to how independently retained Cargo outputs
were produced. Record each cache's state independently.

On reuse, validate the stamp and compare its applicable fields with the
current selected tools before compilation or reconfiguration. Refuse changed
or unavailable required observations, naming the field and remedy. An existing
configured directory with a missing, malformed or unsupported stamp requires
explicit fresh mode; never adopt unknown existing state by writing today's
values over it. Two failed observations do not establish equality. A failed
setup must not publish a successful configuration stamp. A successful setup
followed by a compile failure may be retried only under a matching validated
configuration. Unchanged reuse leaves the stamp intact. Inspection/XPC option
changes remain permitted through ordinary Meson configuration; when enabling
Swift, validate the newly applicable compiler before atomically extending the
stamp after successful configuration. An existing compiler binding is not
silently replaced. Keep the source-directory checks on every reused directory.

Add `PW_FRESH_BUILD`, exactly 0 or 1 and 0 when unset. After read-only input,
tool and identity admission, fresh mode removes only the checkout's
`builddir/` and `controller/target/release/`, then recreates their build state.
Validate deletion roots and parents without following a redirect into an
unowned location. Serialize with other users of those caches, including
build/test invocations; define ownership for nested invocations without
deadlocking or unlinking the existing test checkout lock. Refuse unsafe paths,
unavailable ownership or failed removal. Preserve unrelated files, other
cache areas and prior distribution outputs until assembly. These are new
refusals with manifest rows and controls, not reasons to continue cleaning.

The record distinguishes requested fresh mode from observed replacement of
each directory. Freshness means those cache areas were replaced; it does not
claim a hermetic build or the absence of compiler-wrapper caches elsewhere.
`make notarize`, and therefore `make release`, enforce fresh mode through
their recursive Make calls. Conflicting caller settings must not silently
disable it: enforce the release setting or refuse explicitly. In successful
fresh mode the old directory is not reused, but path, ownership, removal and
new-setup failures still remain possible.

Before assembly, require each shipped Mach-O's `LC_BUILD_VERSION` SDK to
agree with the selected SDK's numeric version, not merely with the other
outputs. Parse and normalize numeric versions; missing or malformed values
are failures, never equal unknowns. This check does not establish SDK build
identifier equality: that identifier is a separate tool observation. Keep
the independent per-output minimum check.

**Acceptance gate.** Retain state-transition and filesystem controls beside
the existing build guards:

- Unchanged incremental reuse succeeds without rewriting its stamp. Changed
  compiler/SDK selection, missing or corrupt stamps, unsupported versions and
  unavailable comparison fields refuse before compilation/reconfiguration.
  Preserve previous distribution bytes on these failures.
- Interrupt setup and stamp publication on each side of their boundaries;
  retry after a compile failure. Recovery either uses a demonstrably matching
  configuration or refuses with a remedy. It never silently stamps unknown
  state as compatible. Exercise Meson and Cargo caches surviving independently.
- Plant sentinels outside the deletion roots and behind symlinked parents,
  inject removal failure, and hold a concurrent build/test user. Require safe
  serialization or refusal, no deletion outside the admitted roots and no
  false `fresh` record. Independently witness removed cache sentinels and new
  build invocations, not just new directory mtimes or the requested knob.
- Exercise fresh, reused and changed-option builds, including full/partial and
  inspection variants, with explicit coverage of enabling/disabling Swift.
  The partial build neither invents Swift observations nor requires Swift.
- Drive actual recursive `make notarize` and `make release` entrypoints with
  controlled external steps, including conflicting environment and Make
  command-line settings. Verify the build invocation enforces fresh mode or
  refuses before building; never submit to Apple as part of this control.
  The knob controls cover unset, empty, valid and invalid values.
- Substitute one wrong-SDK output, then a set that all agree on the wrong SDK.
  Both refuse before assembly and preserve the previous distribution. Unit
  cases cover equivalent numeric representations, missing/malformed load
  commands and the distinction between SDK version and SDK build identifier.

**Retirement.** The build document's inputs section replaces "a compiler or SDK
change needs a fresh build directory because the toolchain is not
fingerprinted" with the stamp, the comparison and the fresh mode.

## B4 — Prune refusals the record and earlier checks make redundant

**Current claim.** 65 refusals, each with a manifest row, a behavioral control
and registry text.

**Change.** Each candidate removal names the replacement predicate and the
boundary it protects. Retain a guard if its control shows a lost guarantee;
eventual `cp` or `codesign` failure alone does not establish equivalence.
Review these candidates independently:

- The 21 Meson policy rows become one row, `meson_policy`, with the template
  message and the asserted options listed in its description. The `assert`
  loops in `meson.build` are unchanged; the generator models the assertion family
  rather than one row per option. Keep the parameterized behavioral controls
  for every option, including compile-triggered regeneration. One row does
  not mean one sampled option test.
- `missing_controller`, `missing_observer`, `missing_sbpl_check`: retain their
  executable-output predicate before assembly, either as the existing guards
  or a shared output check. Cargo's path report and a valid Mach-O parse do
  not establish executable permission; later `chmod +x` must not silently
  repair an output the current build refuses.
- `missing_client_output`, `missing_host_output`: the Meson output loop before
  assembly already checks every output the variant ships.
- `missing_service_bundle`: the same run created it in the step before.
- `sign_target_missing`, `sign_target_not_macho`: the minimum check parsed each
  target as a Mach-O, the inventory rule grounds the list, and codesign's own
  failure covers a missing file. Remove only if controls establish that the
  replacement still refuses the condition before the protected signing
  operation; do not assume codesign refuses every non-Mach-O input.
- `missing_info_plist`, `missing_augments_dir`, `missing_service_dir`,
  `missing_service_plist`, `missing_entitlements`,
  `missing_service_entitlements` become one admission row, `missing_tree_input`,
  naming the first absent tracked input before any check runs.
- `stale_identity_presign`: retain the source recheck and its existing control.
  Add a bounded invocation of the built worker's `--version`, refusing a
  reported identity that differs from the generated one as
  `worker_identity_mismatch`. The checks establish different facts: a worker
  and an unchanged generated constant can agree after source inputs change.
  The binary check does not replace recomputing the current source identity.
- `make_identity_unset`: the script's own refusal names the `make build`
  invocation in its message.
- `identity_class`: replaced by B2's verification on the artifacts.

New rows include `meson_policy`, `missing_tree_input`,
`worker_identity_mismatch`, B3's `builddir_toolchain_changed` and
`sdk_disagreement`, and the stamp, probe and fresh-mode admission failures
defined during implementation. Record the actual count in the acceptance report;
there is no target count. For every removed row, preserve or retarget its
behavioral scenario in
[build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py), compare
refusal timing and filesystem/tool effects, and update its mutation control.
Update the [opt-in registry](tests/OPT_IN_TESTS.md), preflight README and
catalog descriptions to identify that coverage without duplicate bookkeeping.

**Acceptance gate.** `source_drift/build_documentation` passes with the new
rows and the collapsed rule; `preflight/build_refusal_controls` produces every
remaining row in every variant it applies to and the mutated-script controls
still fail their matching control; `preflight/build_guard_controls` passes
with B2's and B3's faults added; `release_preflight.py --report` reports the
build baseline unchanged and empty. The build document's refusal count span
renders the new number. In particular, the existing post-compile source edit
still refuses before signing, nonexecutable Cargo outputs refuse before
assembly, and bypassing any one Meson policy assertion fails that option's
control. Compare effects at the protected boundary, not just final exit status.

**Retirement.** The refusal account groups shared mechanisms and removes only
proven redundancy. Its smaller representation preserves the conditions and
boundaries established by behavioral controls.

## Documentation included with B1 to B4

Update together, through the owning generators where a region is generated:
[build.json](docs/build.json) steps, refusals, knobs, invocations and the
evidence inventory, then `python3 docs/generate_build.py`; the authored
sections of [BUILD.md](docs/BUILD.md) on inputs beyond the tree, the signing
contract, the evidence the build embeds and the known gaps; the evidence
inventory and release procedure in [SIGNING.md](docs/SIGNING.md); the
[Makefile](Makefile) help card for the third knob; the preflight suite README,
the [opt-in registry](tests/OPT_IN_TESTS.md) and the catalog; the fixture
README for the dispatcher bundles; and the cache ownership, stamp migration,
bounded-probe and failure/recovery contracts. Update descriptions of the
retained pre-sign recheck and per-option controls without weakening their
claims. The worker identity regenerates into its three copies.

## B5 — Verify the integrated change and close the plan

**Current claim.** B1 through B4 require integrated acceptance against the
signed build; the generator's textual comparison establishes agreement, not
behavior.

**Change.** Review the script, the manifest, the controls, the fixtures and the
documentation as one account; resolve inconsistencies before crediting
acceptance. For each new refusal, record the injected fault, independent
observation, protected operation and expected surviving filesystem state.
Keep these controls in their owning regression suites; a smaller manifest
must not make them disappear from the selected acceptance work.

**Acceptance gate.** Against a signed build of the final increment made with
the fresh knob, run the default battery in a fresh output directory, including
`source_drift/build_documentation`. Explicitly select all three opt-in cases:
`preflight/signed_artifact_controls`, `preflight/build_guard_controls` and
`preflight/build_refusal_controls`; the default battery does not select
`signed_artifact_controls`. Run
`cargo test --manifest-path controller/Cargo.toml` and
`release_preflight.py --report`.

Before closure, credit this sequence through the actual build entrypoints:
fresh build → unchanged reuse → permitted inspection/XPC configuration change
→ refused incompatible reuse → explicit fresh recovery. Cover each supported
full/partial and inspection variant in the applicable controls. Observe tool
invocations, filesystem changes and final artifact bytes independently of the
provenance builder. Exercise interruption and deletion faults, absent legacy
stamps, optional versus required metadata failure, and the A/B archive swap.
Reader tests must include semantically invalid but validly signed artifacts.
Mutation controls must fail if the matching protection is bypassed, including
an individual Meson policy option. A run of only fresh successful builds or
only substituted tool text does not satisfy these gates.

`witness_contract/order_barrier_mutations` is not forced, since no wait,
release store or eligibility rule changes. The acceptance report must identify
implementation commits, run identifiers, the refusal count, the worker
identity, reviewed fixtures and goldens, state-transition evidence and any
remaining findings. Keep implementation history in commits and execution
evidence in the report; product documentation describes the resulting behavior.

**Retirement.** Close the plan when all five gates pass, or when the user
explicitly accepts a documented change of scope. The acceptance report must
account for each goal criterion and any remaining limitation. The record still
trusts the tools, and nothing here claims reproducibility.

## Decisions recorded before editing

- **Version effect.** None. The request, response and controller envelope are
  unchanged; the controller does not read the record and `app_provenance` keeps
  its two fields. The worker identity regenerates because `build.sh`,
  `meson.build` and `meson.options` are identity inputs.
- **A separate file, not a manifest extension.** The manifest's schema is read
  by the controller at run time; the record is read only by people, the
  inspector and the release archive. Listing the record as a manifest entry
  connects it to the signed hashes without changing the manifest's reader.
- **Where the app seal's facts live.** The record is sealed, so it cannot
  describe the seal that covers it. B2 verifies the seal's chain and timestamp
  after signing. The release record carries those facts and the controller's
  final signed hash, sourced from the accepted final ZIP. Nested executable
  hashes are recorded after their signatures and before the outer seal. No
  embedded record is rewritten after sealing.
- **Collapse by modeling, not by weakening.** The Meson `assert` loops keep
  refusing every departure at configuration/regeneration time. Group the
  manifest rows, retain parameterized controls for every asserted option and
  retain mutation sensitivity. Guard removals require equivalent predicates
  and protected boundaries; there is no refusal-count target.
- **Source identity remains checked before signing.** The binary's reported
  identity adds evidence; it does not replace checking that the generated
  identity still describes the current tree. Preserve the existing source-edit
  control and the early executable-output checks.
- **Fresh mode replaces both owned cache areas.** Replace `builddir/` and
  `controller/target/release/` only after path and ownership admission. Record
  observed state per directory, serialize with cache users, and stop on failed
  removal. Other Cargo state and external compiler caches are outside this
  freshness claim. Release entrypoints enforce the knob.
- **Unknown stamps are not adopted.** Missing or invalid stamps beside
  existing configuration require explicit fresh mode. Publish valid setup
  stamps atomically and never compare failed tool observations as equal.
- **Reported settings describe selection.** Record configured compiler
  commands and effective flag observations with their source, not convenient
  rediscovery or environment values presented as effective settings. Bound
  and sanitize probes and distinguish optional failure from a required
  comparison failure. Partial builds do not acquire Swift prerequisites.
- **SDK comparison has a defined limit.** Every output must agree with the
  selected SDK's normalized numeric version. SDK build identifiers remain
  separately reported observations, not a fact inferred from load commands.
- **Trust boundary.** The record is the tools' testimony with hashes beside
  it. It distinguishes builds; it does not certify them.

## Out of scope

Reproducible or hermetic builds; a vendored toolchain; changes to Apple's
notarization/stapling protocol or the existing witness behavior exercised by
release acceptance; BYOXPC installation provenance beyond reading the shipped
record; a controller-visible `app_provenance` field for the record, which would
be an additive response change for a later plan; and the order-barrier and
policy-transfer controls, which this work does not touch. Provenance inspection
and its binding to the accepted release artifact are in scope. Historical
evidence keeps its original bytes and is never backfilled with a new record.
