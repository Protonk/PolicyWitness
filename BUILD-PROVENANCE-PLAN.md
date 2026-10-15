# Build provenance plan

Status: proposed. Implementation baseline:
`c07911a` (main, 2026-10-15). Nothing in this plan is implemented.

The [parking lot](records/EVIDENCE-CLARITY-PARKING-LOT.md) entry P3 asks that
build provenance become a deliberate artifact: a bounded record of the actual
tool identities, SDK selection, effective configuration and relevant inputs
behind an artifact, connected to the hashes of what was produced; detection of
a configured build directory reused under incompatible settings; a clean
release-build mode; and verification of the signing guarantees on the final
signed artifacts rather than on the requested identity's name. P3 sets the bar
for returning to it: a provenance question expressible as a field and a check
that would distinguish two materially different builds. The investigation
behind this plan found several, and found that the raw material already exists:
Meson writes compiler identities and every effective option under
`builddir/meson-info`, every shipped Mach-O carries its SDK and linker version
in `LC_BUILD_VERSION`, Cargo reports its artifacts, and
[meson_receipts.py](tests/lib/meson_receipts.py) already records most of the
rest as opt-in comparison equipment that the build never runs.

The investigation also found that a deliberate record lets the build shed many
of its refusals. The [build account](docs/BUILD.md) lists 65. Twenty-one are one
`assert` loop in [meson.build](meson.build) modeled as twenty-one rows. About
a dozen of the script's own refuse conditions that an earlier check in the same
run already excludes, that a copy under `set -e` would stop anyway, or that a
build from fresh directories cannot produce. Each has a behavioral control, a
manifest row, a catalog entry and a registry entry to maintain. A recorded fact
with one comparison, and a release mode that starts from fresh directories,
make most of them unnecessary.

The record trusts what the tools report. It is not proof of reproducibility,
compiler correctness or execution of particular bytes, and repeated Swift
builds of identical sources already differ in bytes.

## Checkpoint and order

| Item | Claim to retire or narrow | Status | Completion evidence |
| --- | --- | --- | --- |
| B1 | The build records which bytes it signed but not which tools, SDK, configuration and inputs produced them | Open | |
| B2 | The signing guarantee rests on the requested identity's name, the leaf authority and the runtime flag | Open | |
| B3 | A compiler or SDK change under a reused build directory is the operator's burden and is not detected | Open | |
| B4 | The build carries refusals whose conditions an earlier check, the tools or a fresh build already exclude | Open | |
| B5 | The integrated change still needs final acceptance and evidence review | Open | |

Implement B1 through B4 as one coherent increment, including the manifest, the
controls, the fixtures, the generated documentation and the registries, because
`build.sh`, `meson.build` and `meson.options` are worker identity inputs and the
build document's generator refuses a manifest that disagrees with the script.
Regenerate the worker identity after the last script edit. B5 verifies the
result and closes the plan. Do not leave a refusal in the script without its
manifest row and control, or a row without its refusal.

During execution, update this checkpoint with implementation commits, the
worker identity, the refusal count, test run identifiers, the reviewed
goldens, remaining findings and the next action. The plan closes when all five
gates pass or the user explicitly accepts a documented change of scope. The
parking lot's P3 entry is updated when the plan closes.

## Shared implementation requirements

- Keep the load-bearing guards: the configured source lists and identity
  closure ([native_sources.py](tests/lib/native_sources.py)), the per-output
  minimum check, the signer check, deep verification and the sealed evidence
  manifest. This plan adds facts and comparisons beside them and removes only
  refusals whose condition they or an earlier step already exclude.
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
  Never record `PATH`, the home directory, other variables, keychain contents
  or anything a tool prints beyond its version and resolved path.
- Follow [test guidance](tests/AGENTS.md): fresh output directories, controls
  that establish the boundary they claim, fixture bundles built outside the
  inspected app, no skips for missing equipment. Builds and signing need the
  unsandboxed shell; cargo lives under the Homebrew rustup prefix on the
  development machine.
- Do not state a new value or count in scanned prose outside a span; the
  build document's counts are spans the generator renders.

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
it. Build the record from existing sources, reusing the receipt recorder's
functions rather than duplicating them:

- `source`: commit, describe string, dirty flag, version, build number, the
  generated worker identity, and the hashes of `meson.build`, `meson.options`,
  `controller/Cargo.lock`, `Info.plist` and the two entitlement plists.
- `toolchain`: the developer directory and SDK path, version and build
  `xcrun` reports; Xcode's version and build; the C compiler's id and full
  version from `intro-compilers.json`; `swiftc --version`'s first line, because
  Meson's introspection leaves the Swift full version empty; `rustc -vV`'s
  version, commit hash and host; `cargo`, `meson` and `ninja` versions.
- `configuration`: the three knobs; the fixed-policy subset of Meson's
  effective options from `intro-buildoptions.json` plus `inspection` and `xpc`;
  the effective `RUSTFLAGS`; `MACOSX_DEPLOYMENT_TARGET`; `SDKROOT`; whether
  each build directory was fresh or reused, and the toolchain stamp B3
  records at setup.
- `outputs`: for each shipped Mach-O, the path, hash as signed, UUID, platform
  minimum, SDK and linker tool version from `LC_BUILD_VERSION`; these repeat
  the manifest's hashes by construction and the inspector checks agreement.
- `signing`: the identity string and, for each nested signature made before
  the record, the leaf authority, team identifier and whether a timestamp is
  present, read from `codesign -dvv`. The app seal is made after the record
  and is verified by B2; its facts go to the release record, not into the
  sealed file.

A tool that cannot be read records a failure entry for that field, as the
manifest already does for entitlements; the build does not refuse on a missing
version string, except where B3 compares one. The inspector
([artifact.py](tests/lib/artifact.py)) requires the file, checks its schema and
checks that its output hashes agree with the manifest; the fixture bundles the
dispatcher controls build ([fixture_bundle.py](tests/fixtures/dispatcher/fixture_bundle.py),
[selection.py](tests/fixtures/dispatcher/selection.py)) carry a record.
[release_archive.py](tests/lib/release_archive.py) copies the record into the
archive's evidence and records its hash in `release.json` beside the ZIP hash.
The controller does not read the record; `app_provenance` is unchanged.

**Acceptance gate.** A signed build writes the record; `codesign --verify
--deep --strict` covers it; the inspector refuses an app without it, with a
schema the reader does not accept, or whose output hashes disagree with the
manifest, and accepts the built app. A unit control drives the record builder
with substituted tool outputs and asserts the bounded field set, the failure
entries and that no environment beyond the named variables appears. The
preflight `signed_artifact_controls` gain a corrupted-record copy. The release
archive controls show the record copied and hashed. Two builds from the same
commit under a changed SDK or compiler differ in the record; the control
substitutes the tool output rather than installing another toolchain.

**Retirement.** The build document's known gap narrows from "relies on the
tools' records to establish whether cached outputs are current" to "records
what the tools reported and the directories' state; it does not establish
reproducibility". The evidence inventory in [SIGNING.md](docs/SIGNING.md)
lists the record.

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
names, and a timestamp must be present. Record what it read in the step's
output. With that, the identity prefix check before Cargo goes; the keychain
presence check stays, because it also tells a sandboxed harness's unreadable
keychain apart from a missing identity, and it refuses before any compile.

**Acceptance gate.** The build guard controls gain a wrapper that signs one
helper without `--timestamp`: the seal and deep verification pass, the signer
check names the helper and exits 1 before observer signing. A unit control
feeds the check fixed `codesign -dvv` text for a leaf with the right name but a
chain without the Developer ID authority, and for a missing timestamp, and
asserts each is named. The signed build passes the extended check; the
inspector's signer consistency rule is unchanged.

**Retirement.** The signing contract in the build document states that class
and timestamp are verified on the artifacts, replacing the sentence that says
they are not.

## B3 — Detect incompatible reuse and define the fresh release build

**Current claim.** The build refuses a Meson directory configured for another
checkout and otherwise trusts both directories as incremental state. The build
document says a compiler or SDK change needs a fresh directory because the
toolchain is not fingerprinted; `make release` and `make notarize` reuse both
directories.

**Change.** At Meson setup, write `builddir/pw-toolchain.json` with the SDK
path, version and build, the developer directory, and the C, Swift and Rust
compiler versions the record's toolchain section names. On a reused directory,
compare the stamp with the current toolchain before configuring and refuse a
difference, naming the changed tool and the remedy. Add a third knob,
`PW_FRESH_BUILD`, exactly 0 or 1 and 0 when unset, that removes `builddir/`
and the three pinned Cargo outputs' release directory before building; the
record states `fresh` for each directory. `make notarize`, and therefore
`make release`, set it. In fresh mode the two build-directory refusals and the
new one cannot fire, and the record says so.

Add one more comparison that the record makes cheap: every shipped Mach-O
reports the same SDK in `LC_BUILD_VERSION`, read where the minimum check
already parses that load command. A stale Cargo output built against another
SDK beside fresh native outputs is exactly the difference P3 asks to
distinguish; refuse it before assembly.

**Acceptance gate.** A control edits the toolchain stamp of a configured copy
to another compiler version and shows the refusal before Meson configures; a
control runs a fresh build and shows both directories recreated and the
record's `fresh` fields; a guard control substitutes a Cargo output whose SDK
field differs and shows the SDK refusal before assembly, leaving the previous
distribution bytes intact. The knob control covers the third knob's values.
`make notarize` runs with the knob set.

**Retirement.** The build document's inputs section replaces "a compiler or SDK
change needs a fresh build directory because the toolchain is not
fingerprinted" with the stamp, the comparison and the fresh mode.

## B4 — Prune refusals the record and earlier checks make redundant

**Current claim.** 65 refusals, each with a manifest row, a behavioral control
and registry text.

**Change.** Each removal names the check that already covers its condition, so
review can veto any one. Remove or collapse:

- The 21 Meson policy rows become one row, `meson_policy`, with the template
  message and the asserted options listed in its description. The `assert` loop
  in `meson.build` is unchanged; only the generator's rule changes from one row
  per option to one row per assertion statement, and one control produces it.
- `missing_controller`, `missing_observer`, `missing_sbpl_check`: Cargo's
  artifact report already established each path; a missing file stops at the
  copy under `set -e`.
- `missing_client_output`, `missing_host_output`: the Meson output loop before
  assembly already checks every output the variant ships.
- `missing_service_bundle`: the same run created it in the step before.
- `sign_target_missing`, `sign_target_not_macho`: the minimum check parsed each
  target as a Mach-O, the inventory rule grounds the list, and codesign's own
  failure covers a missing file.
- `missing_info_plist`, `missing_augments_dir`, `missing_service_dir`,
  `missing_service_plist`, `missing_entitlements`,
  `missing_service_entitlements` become one admission row, `missing_tree_input`,
  naming the first absent tracked input before any check runs.
- `stale_identity_presign`: the build states that it assumes a stable checkout.
  The evidence step instead runs the built worker's `--version` and refuses a
  reported identity that differs from the generated one, a check of the binary
  rather than the tree; this is the new propagated row `worker_identity_mismatch`.
- `make_identity_unset`: the script's own refusal names the `make build`
  invocation in its message.
- `identity_class`: replaced by B2's verification on the artifacts.

New rows: `meson_policy`, `missing_tree_input`, `worker_identity_mismatch`,
B3's `builddir_toolchain_changed` and `sdk_disagreement`. The expected count is
about 32; the checkpoint records the actual number. For every removed row,
delete its control in [build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py)
or retarget it, update the mutated-script controls that depend on the removed
guard, and update the [opt-in registry](tests/OPT_IN_TESTS.md), the preflight
README and the catalog descriptions.

**Acceptance gate.** `source_drift/build_documentation` passes with the new
rows and the collapsed rule; `preflight/build_refusal_controls` produces every
remaining row in every variant it applies to and the mutated-script controls
still fail their matching control; `preflight/build_guard_controls` passes
with B2's and B3's faults added; `release_preflight.py --report` reports the
build baseline unchanged and empty. The build document's refusal count span
renders the new number.

**Retirement.** The refusals table no longer carries rows whose coverage
column describes a `cp` or `codesign` wrapper deleting a file the same run
produced.

## Documentation included with B1 to B4

Update together, through the owning generators where a region is generated:
[build.json](docs/build.json) steps, refusals, knobs, invocations and the
evidence inventory, then `python3 docs/generate_build.py`; the authored
sections of [BUILD.md](docs/BUILD.md) on inputs beyond the tree, the signing
contract, the evidence the build embeds and the known gaps; the evidence
inventory and release procedure in [SIGNING.md](docs/SIGNING.md); the
[Makefile](Makefile) help card for the third knob; the preflight suite README,
the [opt-in registry](tests/OPT_IN_TESTS.md) and the catalog; the fixture
README for the dispatcher bundles; and, if the generated worker identity
changes, nothing else, because the identity regenerates into its three copies.
The parking lot's P3 status note changes on closure, after B5 passes.

## B5 — Verify the integrated change and close the plan

**Current claim.** B1 through B4 require integrated acceptance against the
signed build; the generator's textual comparison establishes agreement, not
behavior.

**Change.** Review the script, the manifest, the controls, the fixtures and the
documentation as one account; resolve inconsistencies before crediting
acceptance.

**Acceptance gate.** Against a signed build of the final increment made with
the fresh knob: the default battery in a fresh output directory, which includes
`source_drift/build_documentation` and the preflight `signed_artifact_controls`;
the opt-in `preflight/build_guard_controls` and `preflight/build_refusal_controls`;
`cargo test --manifest-path controller/Cargo.toml`; `release_preflight.py
--report`. `witness_contract/order_barrier_mutations` is not forced, since no
wait, release store or eligibility rule changes. Record run identifiers, the
refusal count, the worker identity and the reviewed inspector fixtures in the
checkpoint table.

**Retirement.** Update the parking lot's P3 status with the completed work and
its evidence. The record still trusts the tools, and nothing here claims
reproducibility.

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
  after signing and the release record carries them.
- **Collapse by modeling, not by weakening.** The Meson `assert` loop keeps
  refusing every departure at configure time; only the manifest's one-row-per-
  option modeling and its 21 controls go.
- **Fresh mode removes both directories.** A release pays a full Cargo and
  Meson build. Partial cleaning would reintroduce the reuse question the mode
  exists to remove.
- **Trust boundary.** The record is the tools' testimony with hashes beside
  it. It distinguishes builds; it does not certify them.

## Out of scope

Reproducible or hermetic builds; a vendored toolchain; changes to
notarization, stapling or acceptance; BYOXPC installation provenance beyond
reading the shipped record; a controller-visible `app_provenance` field for the
record, which would be an additive response change for a later plan; and the
order-barrier and policy-transfer controls, which this work does not touch.
