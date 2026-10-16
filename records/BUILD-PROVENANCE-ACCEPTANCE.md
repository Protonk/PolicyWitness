# Build provenance acceptance

Acceptance record for the build provenance plan, 2026-10-15 and 2026-10-16.
The plan asked for a sealed provenance record in every build, a stamped and
validated native build directory with an explicit fresh mode, a checkout lock
held by every build, signing guarantees verified on the signatures made, and
refusal bookkeeping collapsed by modeling. This record keeps the conclusions,
the implementation commits, the review map and the references to the
supporting runs; the product documentation describes the resulting behavior
and does not link here.

Run evidence under `tests/out/runs/` is gitignored and available only in the
local checkout; the credited directories are protected through
[tests/RETAINED.json](../tests/RETAINED.json). Direct control runs under
`/private/tmp` are transient and are described, not linked.

## Conclusions

All five gates pass against the final increment. The provenance checks rely
on tool-reported information and do not establish that rebuilding with the
recorded inputs produces identical bytes; the record and the build document
state that limit.

| Goal criterion | Account |
| --- | --- |
| Each claimed distinction has a recorded field and an independent control; changed compilers, SDKs and configuration with retained caches, missing and inconsistent records | Forwarding Rust and C wrappers relabelled after the stamp (`control_builddir_toolchain_changed`, `control_fresh_sequence`), a real developer-directory switch (`test_toolchain_switch`), outputs built against another installed SDK (`test_build_guards` sdk_cargo and sdk_all), missing, malformed, foreign and unconfigured stamps (`control_builddir_stamp_missing`, `control_builddir_stamp_invalid`), and records that disagree with the manifest, the bytes or the load commands (signed artifact and dispatcher artifact controls). Successful fresh builds are the neighbours, never the evidence. |
| Recorded settings describe actual selection and observed state; required unknowns cannot establish compatibility; fresh mode replaces its owned areas safely before claiming freshness | The record keeps Meson's configured command beside the identity probed now, Cargo's judgment beside the fingerprint observation and the requested flags beside the effective ones (`test_records_are_bounded_redacted_and_complete`, `control_builddir_toolchain_changed`). A failed or hung required probe refuses (`control_provenance_probe_failed`); two failed observations never compare equal (`test_stamp_states_are_decided_without_adopting_unknowns`). Fresh mode admits every path component before removing anything and records `removed` per directory only after the removal (`control_fresh_removal_unsafe`, `control_fresh_removal_failed`, `control_fresh_sequence` sentinels). |
| The embedded record, the artifact checks and the release archive describe the same bytes; signing claims come from the signatures made, with the seal's facts outside the evidence it seals | The record's hashes are compared with the manifest and the bytes by the inspector; the release archive copies the record out of the accepted ZIP with the controller's final hash and the app seal's display (release publish controls, A/B swap). The signer check and the record's `signing` section read `codesign -dvv` after each signature. |
| Recording rules, guards, evidence, documentation and the release procedure form one account; published fields and probe failures are bounded and exclude credentials and machine configuration | The review map below; canaries planted in an unrelated environment variable and in every tool's stderr never reach a record, a session or a stamp (`control_none`, `control_provenance_probe_failed`); home-prefixed paths are published as `<home>`. |
| Collapsed bookkeeping preserves every predicate, boundary and control, including every Meson policy option | The Meson family is one row that lists its 21 options; `test_meson_policy_assertions_refuse_each_option` poisons each option and `test_bypassing_one_meson_policy_assertion_fails_its_control` removes one assertion. The tracked-input, Cargo-output and signing-target guards are single rows with loop controls over every member, and each removed row is accounted for below. |

## Implementation commits and identities

| Item | Value |
| --- | --- |
| Implementation commit | `a785007327a4532f33b9f407e2893b5ad6a5e655`, "Record build provenance, stamp the build directory and verify signing guarantees" |
| Control correction commits | `4cb989f569a271aa13e19f7d94866b6980f66d5a`, "Correct two sequence-control expectations in the build refusal controls"; `de5034b0977cafc914b44c49458b635dbb59fae2`, "Restore the valid neighbour between mutation stages of the build refusal controls" |
| Tested source snapshot | `de5034b0977cafc914b44c49458b635dbb59fae2` (the acceptance build's record names this commit with `dirty: false`) |
| Worker identity | `d3637d000349de5a2d554f266cb4e7b1cf38eddffc0a13cc2a4b2a47a2a6de2f`, regenerated after the final edits to `build.sh`, `meson.build` and `meson.options` |
| Refusal count | 47 manifest rows: 17 the script's own, one Meson assertion family over 21 options, 29 propagated; the baseline of rows with only a grounding rule is empty |
| Steps, invocations, knobs, signing calls | 33 steps (one fresh-mode only), 35 helper and tool invocations, 3 knobs, 9 signing calls |
| Acceptance app | `dist/PolicyWitness.app` built fresh at the tested snapshot; its record names Xcode 27.0 (27A266a), SDK 27.0 build 26A425 from `xcrun --sdk macosx default`, Apple clang 21.0.0 (clang-2100.3.34.2), Apple Swift 6.4, rustc 1.99.0 from PATH, and `builddir` created with a published stamp and `cargo_release` replaced by fresh mode |

The commit adding this record and the retention entries is not evidence of
those identities; the record embedded in the app and the run directories are.

Between the implementation commit and the final correction, the user
committed three changes to `CONTRIBUTING.md`
(`bd444e54ff29cac1a88fb2381b0a2e510ca9ba33`, which also retired
`PLANNING-DOC-PLAN.md`, `4aeb3079e31f5024698a71703abd6087955a10c7` and
`d69dbaafaea69ecc2dbd6633a49aa4348521309f`); none touches a build input, a control or a fixture.

## Refusal inventory change

The manifest went from 65 rows to 47. Added rows: `builddir_stamp_invalid`,
`builddir_stamp_missing`, `builddir_toolchain_changed`,
`cargo_build_dir_redirected`, `cargo_build_dir_unknown`, `cargo_target_reused`,
`checkout_busy`, `fresh_removal_failed`, `fresh_removal_unsafe`,
`lock_claim_invalid`, `meson_policy` (the family row), `missing_cargo_output`
(one row for the loop), `missing_tree_input` (one row for the loop),
`provenance_probe_failed`, `provenance_required_unknown`, `sdk_disagreement`,
`sdk_version_unreadable` and `worker_identity_mismatch`. Messages changed on
`sdk_unavailable` (names the request), `sign_target_not_macho` (one row for a
missing or non-Mach-O target) and `signer_mismatch` (chain, team and
timestamp).

Removed rows and where each predicate lives now:

| Removed row(s) | Predicate preserved by |
| --- | --- |
| `meson_optimization` through `meson_swift_link_args` (21 rows) | the `meson_policy` family row; every assertion remains in `meson.build` and every option keeps its per-option control and the mutation control |
| `missing_info_plist`, `missing_entitlements`, `missing_service_plist`, `missing_service_entitlements`, `missing_service_dir`, `missing_augments_dir` | `missing_tree_input`: one admission loop before the first check, controlled per input by `control_missing_tree_input` and by the mutation that moves the loop after the first check |
| `missing_controller`, `missing_observer`, `missing_sbpl_check` | `missing_cargo_output`: one loop over the shipped Cargo outputs, controlled per output by `control_missing_cargo_output` and by the guard-removal mutation |
| `missing_client_output`, `missing_host_output` | `missing_native_output`: one loop over the Meson outputs the variant ships, controlled per output and by the moved-guard mutation |
| `sign_target_missing` | `sign_target_not_macho`: a missing target and a non-Mach-O target are one predicate in `sign_macho`, controlled by `control_sign_target_not_macho` and the moved-check mutation |
| `identity_class` | the signer check after the seal verifies the class, chain, team and timestamp on the signatures made (`test_build_guards` signer and timestamp faults, `test_signature_displays_establish_class_team_and_timestamp`); the keychain presence check before Cargo stays and refuses an identity of another class as absent |
| `make_identity_unset` | the script's `identity_unset` refusal names the make invocation; `test_make_build_runs_the_script_which_names_the_make_invocation_in_its_identity_refusal` drives `make build` |

## New refusals: fault, observation, protected operation, surviving state

Every control runs the unchanged script in a disposable copy of the checkout
(`Checkout` in `build_refusals.py`), with forwarding tool wrappers that record
each invocation to a receipt file the control reads, and compares the
distribution directory's inventory before and after. "Preserved" means the
previous app, ZIP and guide bytes are unchanged and no banner of the protected
step printed.

| Refusal | Injected fault | Independent observation | Protected operation | Surviving state |
| --- | --- | --- | --- | --- |
| `missing_tree_input` | each tracked input moved aside in turn | the message names the input; no banner, no tool receipt | the lock, the checks, every tool | preserved; the input is restored by the control |
| `checkout_busy` | a separate process holds the lock with its own owner record | the lock inode and owner record are unchanged; a separate open still cannot take the lock; no receipt | every mutation, including fresh mode's removal (`build.ninja` survives) | preserved; the holder keeps the lock |
| `lock_claim_invalid` | a claim naming a closed descriptor, a separately opened descriptor on the real inode with the holder's nonce, and another checkout's root | the refusal names the reason; the real holder still holds and its owner record is unchanged | the checks and every tool | preserved |
| `sdk_version_unreadable` | an `xcrun` that reports a non-numeric version | the message carries the reported text; no Cargo, Meson or codesign receipt | the build directory check and everything after | preserved |
| `builddir_stamp_missing` | the stamp removed beside a configured directory; a stamp beside an unconfigured directory | no stamp is written; `build.ninja` mtime unchanged; no compile receipt | identity check, Cargo, reconfiguration | preserved; fresh mode recovers with Cargo rebuilding every target |
| `builddir_stamp_invalid` | malformed, unsupported-schema, other-checkout and other-compiler stamps | the stamp bytes are unchanged after the refusal; no compile receipt | identity check, Cargo, reconfiguration | preserved |
| `builddir_toolchain_changed` | a forwarding `rustc` relabelled B after the stamp recorded A; the C wrapper likewise in the sequence; the real developer-directory switch | the message names the field and both values; the stamp is byte-identical; no `cargo build` or `meson` receipt | identity check, Cargo, reconfiguration | preserved; fresh mode recovers under B |
| `provenance_probe_failed` | the Rust wrapper fails its version probe, then hangs it | the message names the field and the kind; the hang is bounded by the probe deadline; the stderr canary is absent from the session | identity check, Cargo | preserved |
| `cargo_build_dir_redirected` | `CARGO_BUILD_BUILD_DIR` pointing at an external directory holding a sentinel | the sentinel and the directory listing are unchanged; `cargo metadata` ran and `cargo build` did not; in fresh mode both caches survive | fresh removal and Cargo | preserved |
| `cargo_build_dir_unknown` | `cargo metadata` answering non-JSON, then exiting 101 | the hook fired once; no `cargo build` receipt | fresh removal and Cargo | preserved |
| `fresh_removal_unsafe` | `controller/target/release` replaced by a symlink to an external directory | the external sentinel survives; the admitted sibling `builddir` survives; the session carries no `fresh` entry; no record | the removal | preserved |
| `fresh_removal_failed` | an immutable file planted under `builddir/` | the session names the failed directory; no `cargo build` receipt; no record | Cargo and everything after | preserved; the next fresh build recovers once the file is removable |
| `missing_cargo_output` | each shipped Cargo output deleted by the wrapper right after Cargo reports it | the message names the path; exactly one `cargo build`; no Meson, Ninja, codesign or copy receipt | the native toolchain check and everything after | preserved |
| `cargo_target_reused` | Cargo's artifact message for one target rewritten as reused in fresh mode; a message dropped | the replacement is recorded per directory; the judgments show the rewritten target; no Meson receipt | Meson and everything after | preserved (the caches were replaced, as the message says) |
| `sdk_disagreement` | one Cargo output, then every shipped output, replaced by a binary compiled against another installed SDK with the plist's minimum | the message names every disagreeing path with both versions; the minimum check passed the substitute; no codesign receipt | assembly | preserved |
| `worker_identity_mismatch` | the built worker replaced after compile by a stub reporting an identity of zeros | the source recheck passed ("stale" absent); the session records the reported identity; no codesign receipt | signing | the previous outputs were removed at assembly; an unsealed partial app remains |
| `sign_target_not_macho` | a signing-list target removed or rewritten as text after the embedded observer copy is signed in the tools step | the next `sign_macho` refuses before codesign runs on it; the signed list ends at the observer copy | the signature | an unsealed partial app |
| `provenance_required_unknown` | the build session deleted by the codesign wrapper after the last nested signature | no record or manifest in the app; the app was not sealed; no ZIP | the seal | an unsealed partial app |
| `signer_mismatch` (broadened) | a helper signed ad hoc; a helper, the service seal or the app seal signed with `--timestamp=none` | deep verification passed first; the signature actually made is displayed and shows a Signed Time without a Timestamp; the message names the signature | observer signing, guide staging and the ZIP | a sealed app that failed the signer check; no ZIP or guide |

A control that establishes an evidence limitation rather than a refusal:
`control_replaced_cached_output_is_recorded_not_detected` replaces a cached
Cargo output with distinguishable bytes before capture. Cargo reports the
unit as reused, the record's hash describes the replacement, its note and the
record's `limits` state that the hash does not authenticate compilation
history, and the build succeeds. The same control then shows the boundary
the inspector does enforce: on a copy, the helper swapped after capture and
sealing for the previous build's helper, validly signed by the same identity,
passes every signature check, including the seal's deep verification, and is
refused by the manifest hash and the record hash. The control's first
version expected a signature failure there as well; the observation
corrected it, in agreement with the documented fact that the seal and deep
verification accept a validly re-signed helper.

## Subprocess ownership review

The lock is taken by `tests/lib/checkout_lock.py` once, before the script
runs again under it with the descriptor inherited, and the script verifies
the claim through the descriptor (open on this checkout's lock file, holding
the lock on its open file description, owner record carrying the nonce).
Nothing unlocks explicitly. Independent observations:

- `control_checkout_busy` and `control_lock_claim_invalid` observe the real
  holder's lock and owner record after each refused build, through a
  separately opened descriptor.
- `control_fresh_sequence` step 12 kills the script's shell before the compile
  from inside the Meson wrapper and then runs the compile itself; the control
  observes the lock still held after the parent died and released only after
  the descendant exited (`lock-lifetime.json` in that step's directory).
  Step 9 kills the script after setup and before publication and observes a
  configured, unstamped directory with the lock free.
- The dispatcher's helper (`checkout_lock` in `tests/lib/retention.py`) keeps
  the same rule: the owner record carries a nonce and no explicit unlock.

Cache-location evidence: `cargo-admit` records Cargo's reported target and
build directories under the pinned target directory and refuses one outside
it with nothing removed (`control_cargo_build_dir_redirected`, both modes).
Cargo's artifact messages are kept in `controller/target/pw-build-messages.jsonl`
and read by `cargo-judge`; the forwarding wrappers' compilation receipts
distinguish compilations from version and capability probes, and the effective
flags the record reports per output are compared with the compilations the
wrapper received (`control_builddir_toolchain_changed`).

## State-transition evidence

`control_fresh_sequence` drives the entrypoint through the required sequence
with a forwarding C compiler selected as A at setup:

1. fresh partial build: both cache sentinels gone, `meson setup` without
   `configure`, every Cargo judgment rebuilt, stamp scope `xpc: false`,
   Swift recorded as not applicable, `builddir` created with the stamp
   published;
2. unchanged reuse: stamp byte-identical, `meson configure` without `setup`,
   every judgment reused, stamp validated;
3. enabling the XPC pieces: the stamp extended with the Swift compiler and
   no other field changed, `published_at` kept and `extended_at` set;
4. reuse under the full variant: stamp unchanged;
5. inspection off: permitted, stamp unchanged, knob recorded;
6. partial again: the Swift binding stays in the stamp;
7. the wrapper relabelled B: refused by `compilers.c.identity` with no Meson
   call and the stamp intact;
8. fresh recovery under B;
9. killed after setup before publication: configured, unstamped, lock free;
10. the unstamped directory refused with the fresh-mode remedy;
11. fresh again;
12. killed before the compile after publication: the stamp exists and the
    orphaned compile holds the lock until it exits;
13. retry: the matching stamp validates and the build configures;
14. a compile failure under the validated configuration: the stamp unchanged;
15. retry after the failure: the stamp unchanged;
16. the Cargo cache removed alone: every target rebuilt, Meson configured,
    `cargo_release` created;
17. the Meson cache removed alone: every judgment reused, `meson setup`,
    `builddir` created;
18. a build without `CC` on the directory set up with the wrapper: the record
    names the wrapper as the configured command and the stamp is byte-identical;
19. a fresh build without `CC`: the stamp names the ordinary compiler.

Step 18 was corrected during acceptance: the first version expected a refusal,
but `CC` is read only at setup and an unchanged configured directory reuses
cleanly, which the build document already said; the corrected control asserts
that account. The mutation phase was corrected as well, after the first
dispatcher run of the case failed there with every refusal control and
sequence passing: a mutated run can leave the stamp missing or the directory
configured, so a fresh build with the original script now precedes the
guard stage and the repeat; each stage records its own build's status and
stderr, and whether a self-check refused the script, instead of reading
that from the control's assertion text, since a guard displaced ahead of the
documentation check (the tracked-input admission) fails its control by the
displacement before any self-check runs; and the old-ninja control accepts
the stamp check's own version probe beside the toolchain step's refusing
one. None of these corrections changes what the build does; the first
dispatcher run's evidence stays under `provenance-acceptance-optin-20261016`
and is not credited.

`control_release_entrypoints_enforce_fresh_mode` drives `make notarize` and
`make release` in a disposable repository with a controlled build step: both
invoke the build with `PW_FRESH_BUILD=1` and stop the chain at the controlled
step; a conflicting value in the environment or on the command line is
refused before the build runs; an explicit `1` passes; plain `make build`
leaves the knob unset.

## Real toolchain switch

`test_toolchain_switch` builds under the selected developer directory
(`/Applications/Xcode.app/Contents/Developer`), reuses, is refused under
`/Library/Developer/CommandLineTools` and recovers fresh there. The fields the
independent probes of the two directories distinguish, and which the stamps
distinguish: `compilers.c.identity`, `compilers.swift.identity`,
`developer_dir`, `sdk.build`, `sdk.path` and `sdk.version`. The refusal named
`developer_dir`. Every output of the B build carries B's SDK version.

Equipment finding: the Command Line Tools on this machine cannot link
against the newest SDK they carry (their linker rejects an architecture
named in that SDK's text stubs) but link against the older SDK they also
carry. The control therefore probes which SDK each developer directory can
link with, names that SDK through `SDKROOT` when it is not xcrun's default,
records the probes in `equipment.json`, and the build honors a caller's
`SDKROOT` as the SDK request and records `SDKROOT named by the caller` as the
selection source. The system Python shim under Xcode sets `SDKROOT` in its
own environment; the launcher therefore relays the caller's request to the
script it runs under the lock, so that a selection made by the caller is a
recorded input and one made by the shim is not mistaken for it.

## Acceptance runs

Every command ran from the repository root in an unsandboxed shell with
`/opt/homebrew/opt/rustup/bin` prepended to `PATH`, and with
`IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'` where a
build was made.

| Gate | Command | Output directory and run id | Result |
| --- | --- | --- | --- |
| Signed build of the final increment, fresh | `make build IDENTITY=... PW_FRESH_BUILD=1` | `dist/PolicyWitness.app`; record commit `de5034b0977cafc914b44c49458b635dbb59fae2` | passed; build stamp 0.3.0 (646) v0.3.0-24-gde5034b, record `dirty: false`, every step banner in the documented order |
| Default battery, including `source_drift/build_documentation` | `PW_TEST_OUT_DIR=tests/out/runs/provenance-acceptance-default-20261016-credited ./tests/run.sh` | `20261016T031038Z_1d401a82` in `tests/out/runs/provenance-acceptance-default-20261016-credited` | passed: 188 selected, 188 completed, 188 passed, no skips, no unrun cases, no harness errors |
| Opt-in build and artifact controls | `PW_TEST_OUT_DIR=tests/out/runs/provenance-acceptance-optin-20261016-credited ./tests/run.sh --case preflight/signed_artifact_controls --case preflight/build_guard_controls --case preflight/build_refusal_controls --case preflight/build_toolchain_switch_controls` | `20261016T032013Z_7e84a8ad` in `tests/out/runs/provenance-acceptance-optin-20261016-credited` | passed: 4 selected, 4 completed, 4 passed; the refusal controls produced every manifest row in both variants, the five sequences and the eight mutation demonstrations |
| Controller unit tests under the lock | `python3 -B tests/lib/checkout_lock.py -- cargo test --manifest-path controller/Cargo.toml` | the managed `controller/target/` | exit 0 through the helper, which held the lock for the whole run; every batch passed (235, 27, 56 and 15 tests, one ignored test in two batches), no failures |
| Release preflight report | `python3 -B tests/lib/release_preflight.py --report` | stdout | exit 0; one warning, that HEAD is not at a release tag (it would stamp v0.3.0-24-gde5034b); no prose or build baseline problem; the build baseline holds no entries |

After this record, the retention entries and the parking-lot note were
written and the plan was removed, the `source_drift` suite ran through the
dispatcher once more (`tests/out/runs/provenance-acceptance-drift-20261016`,
run `20261016T034204Z_1b2b6a11`, every case passing) as the closure check
that the documentation and link rules hold without the plan; that run is
disposable and not retained.

Earlier runs that informed the work and are not credited:
`provenance-offline-01` through `provenance-offline-05` (suite selections
during implementation); `provenance-acceptance-default-20261016` (the default
battery against a build made at the implementation commit with the user's
pending CONTRIBUTING edit; one case failed, see the clock finding below;
retained for that evidence); `provenance-acceptance-default-20261016-final`
(run `20261016T023046Z_5874e99e`, the default battery at
`4cb989f569a271aa13e19f7d94866b6980f66d5a`, every case passing, superseded by
the credited run at the final commit); and
`provenance-acceptance-optin-20261016` (run `20261016T024114Z_a553834b`, the
four opt-in cases at the same commit: three passed and the refusal controls
failed in the mutation phase, which the second correction addresses). Direct
runs of `build_refusals.py` and `build_toolchain_switch.py` under
`/private/tmp` established each control before the dispatcher runs and are
transient.

## Review map (documentation task)

| Changed behavior | Generated rows or figure | Authored explanation | Operator commands | Acceptance control |
| --- | --- | --- | --- | --- |
| Tracked-input admission before any check | refusal `missing_tree_input`; step `admission` | BUILD.md, Inputs beyond the tree, "The tracked inputs" | none | `control_missing_tree_input`; mutation "admission moved after the first check" |
| Checkout lock held by every build, verified through the inherited descriptor | steps `admission`, `lock`; refusals `checkout_busy`, `lock_claim_invalid`; invocations `inv_lock_launch`, `inv_lock_verify` | BUILD.md, The checkout lock; tests/README.md locking contract; tests/AGENTS.md; root AGENTS.md | `python3 -B tests/lib/checkout_lock.py -- cargo test ...` | `control_checkout_busy`, `control_lock_claim_invalid`, `test_lock_claims_are_verified_through_the_descriptor` |
| Build session and toolchain stamp: publish, validate, extend, refuse unknown state | steps `stamp`, `builddir`, `configure`, `native_check`; refusals `builddir_stamp_missing`, `builddir_stamp_invalid`, `builddir_toolchain_changed`, `provenance_probe_failed`; directory row `builddir/` | BUILD.md, Cache compatibility, replacement and recovery | `PW_FRESH_BUILD=1 make build ...` | `control_builddir_stamp_missing`, `control_builddir_stamp_invalid`, `control_builddir_toolchain_changed`, `control_provenance_probe_failed`, `control_fresh_sequence`, `test_stamp_states_are_decided_without_adopting_unknowns`, `test_toolchain_switch` |
| Fresh mode and its knob | knob `PW_FRESH_BUILD`; step `fresh` (dotted node); refusals `fresh_removal_unsafe`, `fresh_removal_failed`, `cargo_target_reused` | BUILD.md, One build in time "Fresh mode", Cache compatibility; Makefile help; SIGNING.md release procedure | `make notarize`, `make release` enforce it | `control_fresh_removal_unsafe`, `control_fresh_removal_failed`, `control_cargo_target_reused`, `control_fresh_sequence`, `control_release_entrypoints_enforce_fresh_mode`, `test_fresh_removal_admits_only_owned_real_directories` |
| Cargo directory admission and per-target judgment | step `cargo_admit`; refusals `cargo_build_dir_redirected`, `cargo_build_dir_unknown`; directory row `controller/target/` | BUILD.md, Inputs beyond the tree "Cargo's environment" | none | `control_cargo_build_dir_redirected`, `control_cargo_build_dir_unknown`, `test_cargo_judgments_bind_fingerprints_without_guessing`, `control_replaced_cached_output_is_recorded_not_detected` |
| SDK selection, caller SDKROOT relay, numeric agreement before assembly | step `sdk`; refusals `sdk_unavailable`, `sdk_version_unreadable`, `sdk_disagreement` | BUILD.md, Inputs beyond the tree "The SDK and the developer directory" | `SDKROOT=... make build` | `control_sdk_unavailable`, `control_sdk_version_unreadable`, `test_build_guards` (sdk_cargo, sdk_all), `test_sdk_versions_normalize_and_unknowns_never_agree` |
| Worker identity reported by the built binary | refusal `worker_identity_mismatch`; step `presign` | BUILD.md, The signing contract "Gates before any signature" | none | `control_worker_identity_mismatch` |
| Signature guarantees verified on the artifacts (class, chain, team, secure timestamp) | refusal `signer_mismatch` (broadened); step `signer` | BUILD.md, The signing contract "After the seal"; Makefile header | none | `test_build_guards` (signer, timestamp_helper, timestamp_seal, timestamp_app), `test_signature_displays_establish_class_team_and_timestamp`, signed artifact controls |
| Refusal bookkeeping collapsed by modeling | row `meson_policy` with `asserts`; rows `missing_cargo_output`, `sign_target_not_macho`; removed rows above | BUILD.md, Refusals "The Meson assertion family"; source_drift README | none | `control_meson_policy`, `test_meson_policy_assertions_refuse_each_option`, `test_bypassing_one_meson_policy_assertion_fails_its_control`, `control_missing_cargo_output`, `control_sign_target_not_macho`, mutation controls |
| Provenance record written, listed and sealed; inspector validates it | step `evidence`; refusals `evidence_failed`, `provenance_required_unknown`; invocation `inv_evidence` | BUILD.md, The evidence the build embeds; SIGNING.md, Evidence artifacts and The provenance record; README.md inventory | none | `control_none`, `control_provenance_required_unknown`, `test_records_are_bounded_redacted_and_complete`, signed artifact controls (re-signed faulty records), dispatcher artifact controls |
| Release archive binds the record, controller hash and seal facts to the accepted ZIP | none (release tooling) | SIGNING.md, The release record and Preserved release archives; dist/README.md | `make release` | release publish controls (A/B working app, swapped record, controller hash, missing record) |

Owning sections: BUILD.md owns the build order, inputs, cache compatibility,
the lock, the signing contract and the evidence timing; SIGNING.md owns the
evidence inventory, the record format and limits, the release record and the
release procedure; tests/README.md owns the locking and retention contract;
the preflight README, the opt-in registry, the catalog and the fixture
catalog own what each control establishes and requires. Other documents link
to those sections.

## Documentation walkthrough

Reviewed as an operator against the rendered documents and the figure, after
`python3 docs/generate_build.py --check` reported the figure, the scalar spans
and every region current:

| Walkthrough | Documented account | Reconciled with |
| --- | --- | --- |
| Fresh build | BUILD.md "Fresh mode": admission, tools and identity first, then the `fresh` step replaces the two areas and Cargo must report rebuilding; the figure's dotted node and edges | the acceptance build's banners and record (`builddir` created, stamp published, both replacements `removed: true`, every Cargo judgment rebuilt); `control_fresh_sequence` step 1 |
| Unchanged reuse | "Cache compatibility": the `builddir` step validates the stamp before any compile or reconfiguration and leaves it byte-for-byte intact | sequence steps 2 and 4; `control_builddir_toolchain_changed` reuse |
| Permitted configuration change | enabling the XPC pieces extends the stamp with the Swift compiler after a successful compile; inspection never touches it; disabling leaves the binding | sequence steps 3, 5 and 6 |
| Incompatible or unstamped reuse and recovery | a differing field refuses by name before Cargo with the remedy; a missing, malformed, unsupported or foreign stamp is refused, never adopted; one fresh build recovers | sequence steps 7, 8, 10 and 11; the stamp controls; the real switch |
| Interrupted build | "Interruption follows the same rule": killed after setup leaves an unstamped directory the next build refuses; killed after publication leaves a stamped directory the next build validates; the lock outlives the killed parent while a child compiles | sequence steps 9 to 13 and the lock-lifetime observation |
| Accepted-release archival | SIGNING.md "The release record" and "Release procedure": the record is read out of the accepted ZIP with the controller's final hash and the seal's display; archive verification reads them back before exposure and before publication; the release build is fresh | release publish controls; `control_release_entrypoints_enforce_fresh_mode` |
| Direct Meson work | "Native compile with Meson": a build directory of your own; `builddir/` belongs to the script and a hand-configured one is refused as unstamped until a fresh build | `control_builddir_stamp_missing` |
| Standalone Cargo cache isolation | "The checkout lock": the helper command, or both `CARGO_TARGET_DIR` and `CARGO_BUILD_BUILD_DIR` outside the managed areas | the `cargo test` acceptance run through the helper; `control_cargo_build_dir_redirected` |
| Recursive release commands | `make release` holds no outer lock; each phase takes and releases it; notarize and release pass `PW_FRESH_BUILD=1` and refuse a conflict | `control_release_entrypoints_enforce_fresh_mode` |
| Descendant lifetime | the hold belongs to the open file description and ends when the last sharer exits | sequence step 12 |
| Redirected intermediates | Cargo is asked for its effective intermediate directory and refused outside the pinned one before any mutation | `control_cargo_build_dir_redirected` |
| Reused output explanation | BUILD.md "The evidence the build embeds" known gap and SIGNING.md "What the hashes mean": current probes and newly captured hashes are not attributed backward to a reused output's compilation history | `control_replaced_cached_output_is_recorded_not_detected` |

Generated and authored boundaries were read together: the step table's Reads
and Writes columns, the directory table, the knob table and the refusal
table agree with the prose around them and with the script's banners in the
acceptance build log. No contradiction remained at closure.

Reviewed fixtures: `tests/fixtures/build_refusals/forward.py` (forwarding
compiler wrapper with labels, probe failure and hang modes and a stderr
canary), `tests/fixtures/build_refusals/tools.py` (hook wrapper with chmod,
copy, judge and kill-parent actions; the receipt is written before the
after-actions), `tests/fixtures/build_refusals/wrong_worker.c` (the stub
reporting an identity of zeros), `tests/fixtures/build_guards/tools.py`
(substitution and codesign faults), `tests/fixtures/dispatcher/controller_stub.c`
(replaces the Python controller stand-in so the fixture bundle carries a
Mach-O with load commands) with `fixture_bundle.py`, `build.sh` and
`repository.py`. Goldens: `tests/fixtures/docs/build_baseline.json` stays
empty; the layout golden is unchanged because only the generated identity
constants changed in the C header and the Swift worker.

## Procedural notes

Three of the assistant's responses during this work were stopped by a safety
classifier and withheld. No product content was lost: each stop happened
while reasoning or issuing tool calls, and the work was redone from the
visible state. The design consequence is that no control patches Mach-O
headers: the "unreadable SDK" branch of the SDK comparison is covered by unit
controls over constructed `otool` text, and the wrong-SDK build controls use
a binary genuinely compiled against another installed SDK
(`-isysroot /Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk`). The
user said they or someone else will manage the classifier issue.

## Remaining findings

- **A worker clock read denied under a deny-default profile (pre-existing,
  outside this plan).** In the preliminary default battery
  (`provenance-acceptance-default-20261016`, run `20261016T021725Z_87b7a565`,
  187 of 188 cases passing), `witness_contract/bug_report_returns_verdicts`
  failed: the worker reported `proceed wait: CLOCK_MONOTONIC failed` with
  errno 1 and the run's deny capture holds one event for that worker pid,
  `deny(1) syscall-unix 116`, which is `SYS_gettimeofday` in the SDK's
  syscall table. The worker reads its proceed-wait clock with
  `clock_gettime(CLOCK_MONOTONIC)` ([pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c),
  `wait_for_proceed`), expecting a commpage read; the denied syscall shows
  that the library took a system-call path at least once under
  `(deny default)(allow file-read-data)`. The worker failed closed, the
  controller reported `runner_failed` with the diagnostic and no verdict or
  attempt was fabricated. The case passed in every earlier battery on this
  machine and in the credited run; the wait, release store and
  eligibility rules are untouched by this plan, so the condition is reported
  here with its evidence rather than changed. The preliminary run is
  retained for that evidence, not credited for acceptance.
- `docs/architecture.json` was left unchanged: the build introduces no
  process, channel or boundary at run time, and the controller does not read
  the record.
- The toolchain switch control depends on the acceptance machine's
  equipment: two developer directories with distinct C compiler identities,
  each able to link against one of its SDKs. It fails, never skips, when that
  is absent.
- The release archive binding was exercised by the offline publish controls
  with a working app; no release was made or submitted during this plan.
- The controller's `app_provenance` response field is unchanged; a
  controller-visible field for the record remains a later, additive change.
