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

All five gates pass against the final increment. Later review found five
boundaries where these runs did not establish the distinction claimed;
[Repair of the acceptance boundaries](#repair-of-the-acceptance-boundaries)
lists the claims below that it qualifies, the repair and the runs that now
carry the credit. The provenance checks rely
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
(`-isysroot /Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk`). This
note first named the 26.5 SDK; the retained receipt
`tests/out/runs/provenance-acceptance-optin-20261016-credited/suites/preflight/build_guard_controls/artifacts/compile-wrong-sdk/command.json`
shows the successful command naming the 15.4 SDK with `-isysroot` and
minimum 26.0, and the same run's `artifacts/equipment.json` records other
SDK version 15.4 against the selected SDK 27.0. Those guards now need one
SDK; the repair section describes the metadata fixture that replaced the
second one. The record holds no raw classifier decisions, so their exact
causes cannot be diagnosed from it. The user said they or someone else will
manage the classifier issue.

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

## Repair of the acceptance boundaries

Review of this record after `e845b02` found counterexamples at five
boundaries the account above claimed. The runs above establish the cases
they exercised and stay retained unchanged; they do not establish the
distinctions below. This section records the repair, made on 2026-10-16,
and its credited runs. The subsequent [review corrections](#review-corrections)
qualify this closure: those passing runs did not exercise every boundary the
implementation claimed.

### What the original account did not establish

- **Ownership and lifetime.** The `lock` step verified a claim by taking
  `LOCK_EX | LOCK_NB` on the descriptor the claim named. A stale, separately
  opened descriptor on a free lock therefore passed as an inherited hold; the
  `lock_claim_invalid` row above tried such a descriptor only while the real
  holder held the lock. Session nonces were compared without a hold, and two
  absent nonces compared equal, so `fresh-remove` run by hand deleted both
  caches. The dispatcher's descriptor was not inheritable and its cases did
  not receive it, so a killed dispatcher freed the lock while a case still
  ran. `control_fresh_sequence` step 12 recorded `held_after_kill` without
  asserting it; the credited value happened to be true.
- **Path admission.** `build.sh` created `controller/target/` and the session
  helper wrote the session before fresh mode checked any path. Through a
  symlinked `controller/target`, review saw a file outside the checkout
  overwritten before the later `fresh_removal_unsafe` refusal.
- **Cargo selection and freshness.** The collector read Cargo settings with
  line-oriented regular expressions, starting from the manifest directory.
  It missed inline tables, included files and `[env]`, and refused a
  recognized file setting even when `RUSTC` overrode it. It read a missing
  or null `fresh` as `false`, so an absent judgment counted as a rebuild.
- **Record validation and effective settings.** `record_problems` accepted
  `null` sections and ignored the recorded linker tools. The accepted app's
  record carried `deployment_target: null` beside an enforced 26.0. The
  caller's `SDKROOT` was relayed only on the unclaimed path, and the
  `/usr/bin/python3` shim inserts `SDKROOT` when the caller leaves it unset,
  so a Python owner could not tell an absent request from the shim's value.
- **Probe bounds.** Probes wrote both streams to files until the tool exited.
  Only stdout's size was checked, and only afterward; stderr was never
  bounded. Some comparison identities and effective flag lists were
  truncated, so values that differed only after the cut compared equal.

This qualifies the first four rows of the Conclusions table,
the `lock_claim_invalid` and `fresh_removal_unsafe` rows of the refusal
table, the Subprocess ownership review, and the relay paragraph under Real
toolchain switch. The account below replaces them.

### Repaired boundaries and their controls

Every control named here ran in the credited runs below. The unit tests are
in `tests/suites/preflight/check_build_provenance.py` (default case
`preflight/build_provenance_controls`). The build controls are in
`tests/suites/preflight/opt_in/build_refusals.py` (opt-in case
`preflight/build_refusal_controls`); they run the unchanged script in a
disposable checkout, with forwarding tool wrappers whose receipts serve as
the oracle.

| Boundary | Repair | Reproducing controls |
| --- | --- | --- |
| Ownership and lifetime | `checkout_lock.py` owns acquisition, nested admission and protected launches. An owner hands its held descriptor, nonce and requests over a private socket pair it creates when it launches the protected child; admission never takes the lock. Every managed launch passes the descriptor explicitly, including the dispatcher's cases and the test wrappers. The launcher supervises its command in a new session and forwards SIGINT, SIGTERM and SIGHUP. Each helper that writes the session, removes a cache, or publishes or extends the stamp is admitted the same way and requires the session's acquisition nonce. | `test_claims_are_admitted_only_by_a_live_owners_handoff` (stale claim, unheld descriptor on the inode, another open beside a real holder, wrong nonce, closed descriptor, other worktree), `test_owner_exit_during_admission_creates_no_hold`, `test_protected_children_keep_the_hold_after_the_owner_dies`, `test_helpers_refuse_without_ownership`; `control_lock_claim_invalid`, `control_checkout_busy`, `control_lock_lifetime` (signals; a holder beyond a killed owner, shell and wrapper, with a passing and a dropping wrapper; standalone Cargo refused while held and admitted after; nested success; packaging; an independent worktree); `control_fresh_sequence` step 12, which now asserts `held_after_kill`; `dispatcher/retention_controls` (a killed dispatcher's grandchild beyond a passing and a dropping wrapper) |
| Path admission | Under the verified hold, the session helper admits every component of `builddir/`, `controller/target/`, `controller/target/release/` and the session and stamp destinations before any write. It refuses symlinked, foreign-owned and non-directory components and unsafe destination files. Writes and removals go through the admitted directory descriptors, with identity rechecks, and fresh mode admits both removal roots before removing either. The script no longer creates `controller/target/` itself. `cache_path_unsafe` replaces `fresh_removal_unsafe`. | `test_cache_paths_are_admitted_before_any_write`, `test_fresh_removal_admits_only_owned_real_directories`; `control_cache_path_unsafe` (each component and the session destination, in incremental and fresh mode; outside sentinels, hashes and inventories; a path replaced between helpers; an owned missing directory); `control_fresh_removal_failed`; the mutation "path admission disabled in the session helper", which brings back the original outside-session overwrite and fails the control |
| Cargo selection and freshness | `tests/lib/cargo_config.py`, with tomli 2.4.1 vendored unmodified under `tests/lib/vendor/`, reads Cargo's configuration the way a single invocation from the caller's directory does. That covers ancestors and Cargo home; `config` over `config.toml`; includes in Cargo's order under byte, file, depth and cycle bounds; the merge rules; value origins for relative paths; environment overrides and an empty wrapper reset; `[env]` with `force` and `relative`; and the rustup proxy. The compiler is probed in Cargo's child environment at the workspace root. A configuration that cannot be read refuses as `cargo_configuration_unresolved`. A forced input that conflicts with the build's selection refuses as `cargo_environment_conflict`. A shipped target without exactly one literal boolean judgment refuses as `cargo_judgment_unknown`. Requested flags are attributed by precedence. | `test_toml_forms_discovery_and_precedence`, `test_program_paths_resolve_as_cargo_resolves_them`, `test_includes_follow_cargo_order_and_refuse_what_cannot_be_read`, `test_env_entries_apply_as_cargo_applies_them`, `test_fresh_judgments_are_literal_booleans_bound_to_the_admitted_executable`, `test_requested_flags_are_attributed_by_precedence`; `control_cargo_configuration_oracle` (24 configurations: 19 checked against the compiler, wrapper chain, directory and environment real Cargo used; one checked to compile without the manifest directory's file when run from another directory; and 4 the resolver refused, each of which Cargo also failed with status 101); `control_cargo_selection_sequence` (with retained caches: an included relative compiler, a change to only that file, the review's forced `[env]` `PATH` counterexample, encoded flags over `RUSTFLAGS`, target rules over `build.rustflags`, recovery); `control_cargo_configuration_unresolved`, `control_cargo_environment_conflict`, `control_cargo_judgment_unknown` |
| Record validation and effective settings | One typed validator for the documented record runs in the producer before sealing, in the artifact inspector and in the release-archive reader. Linker tools are compared with the load commands, and the signing section with independently read signature displays. `tests/lib/checkout_lock.sh` records `SDKROOT`, `CPATH`, `LIBRARY_PATH`, `MANPATH` and `LC_CTYPE` with shell builtins before `/usr/bin/python3` runs. The owner carries these requests, and nested builds receive them through the handoff. A build launched by an owner without requests refuses as `build_requests_missing`. The record keeps `configuration.requests` apart from the effective deployment target and SDK, which are taken after selection and after Cargo's `[env]`. The fixture records are authored independently. | `test_records_are_validated_by_shape_in_every_reader`, `test_the_archive_reader_validates_the_record_and_binds_its_outputs`, `test_the_producer_validates_before_sealing`, `test_requests_are_captured_before_python_and_handed_to_nested_owners`; `signed_artifact_controls` (re-signed copies with missing, null and mistyped sections and a changed linker-tool version); the release publish and dispatcher artifact controls with migrated fixture records; `control_build_requests_missing`; `control_sdk_requests` (absent, default named, empty, an explicit path nested under another owned command, and an invalid request refused without a shim seeing it; each compared with the compilations, their environment and the outputs' load commands) |
| Probe bounds | Probes drain both streams through a selector, with live byte limits and one deadline. Overflow on either stream, or the deadline, fails the observation even after exit 0. The process group then gets SIGTERM, then SIGKILL after a grace period, under a bounded cleanup that reports failure rather than waiting. Failure entries carry only kind, stream, status and sizes. Oversized compiler commands, identities and flag lists become failed observations instead of truncated values. | `test_probes_are_bounded_and_failures_carry_no_output` (overflow on each stream and on both, exact limit, nonzero exit, empty and malformed output, timeout, ignored SIGTERM, an orphaned pipe writer), `test_comparison_inputs_are_complete_within_their_bounds`, `test_failed_required_observations_refuse_compatibility_and_publication`; `control_provenance_probe_failed` with a stderr flood and a canary |

The core build guards now need only one installed SDK.
`tests/suites/preflight/opt_in/build_guards.py` links a small Mach-O with
`-Wl,-platform_version,macos,<minimum>,<next major>` and reads its load
commands before substituting it; in the credited run it stamped SDK 28.0
beside the selected 27.0, with minimum 26.0. This is a controlled metadata
mismatch, not evidence of compiling against a second SDK. The
developer-directory switch remains the separate, equipment-dependent case.

### Commits and identities

| Item | Value |
| --- | --- |
| Implementation commits | `b410ac3ba1ba89d0db80750fd48f9cf470ba399e` (ownership handoff and early path admission), `5bdd4852fce2fec328916019c92827d0028cae26` (probe bounds; unvalidated SDK requests kept away from the shims), `cc903757b325cc849e82a4a389d50fb40ad961b7` (Cargo selection and literal freshness), `44220dfba0cbdad2d1688ff322aac9974634606e` (record validation; requests kept apart from effects), `5265772c9bb56dfe3a2794f04e181d428fa1654a` (one-SDK build guards; a partial build's Swift recorded as not applicable), `b7b24b41cebfb463fd3ed4487e0d03f46280446d` (a Cargo release directory that fresh mode replaced recorded as created) |
| Control correction commit | `6f0802cb788dbb2de001e788e66f706dad5df945`: the `builddir_stamp_missing` and `worker_identity_mismatch` mutations still named helper arguments that `b410ac3` removed, so the mutation phase would have failed its own precondition. The Cargo oracle recorded, but did not assert, that Cargo fails each configuration the resolver refuses. The lifetime control never ran a standalone Cargo command after the holder exited. The build document already claimed the last two. |
| Tested source snapshot | `6f0802cb788dbb2de001e788e66f706dad5df945`; the acceptance build's record names it with `dirty: false` and `describe` `v0.3.0-36-g6f0802c` |
| Worker identity | `b3b5f50a1f90e5cf11f864dfaa85b752961b115d773abf49ce00e28dba19f5be` |
| Refusal count | 51 manifest rows: 17 the script's own, the Meson family row and 33 propagated; the baseline stays empty. Added: `build_requests_missing`, `cache_path_unsafe` (replacing `fresh_removal_unsafe`), `cargo_configuration_unresolved`, `cargo_environment_conflict` and `cargo_judgment_unknown`. Changed: `lock_claim_invalid` (now produced at every admitting step), `cargo_target_reused` (a missing literal judgment is not a rebuild) and `provenance_required_unknown` (also raised when a record fails its own validation). |
| Steps, invocations, knobs, signing calls | unchanged at 33, 35, 3 and 9 |
| Acceptance app | `dist/PolicyWitness.app`, built with `make build PW_FRESH_BUILD=1` at the tested snapshot as build 0.3.0 (658); ZIP sha256 `da30cf57894fc415234b8af281d1fd899a0f5e64ceb20f73fe37ba0df065826b`. Its record names Xcode 27.1 (27A9275), SDK 27.0 build 26A425 from `xcrun --sdk macosx default`, Apple clang 21.0.0 (clang-2100.3.34.2), Apple Swift 6.4, and rustc 1.99.0 as Cargo's default selection through the rustup proxy (`stable-aarch64-apple-darwin`). It records `deployment_target` 26.0. The requests show `SDKROOT` unset and `MANPATH` set, recorded by state only. `builddir` and `cargo_release` were both replaced by fresh mode and recorded as created, and every Cargo judgment says rebuilt. |

The App Store updated Xcode from 27.0 (27A266a) to 27.1 between about 17:22
and 17:30 PDT, during the work. The user completed Xcode's first launch
before the acceptance build. The SDK, C and Swift compiler identities
reported before and after the update are the same.

### Replacement acceptance runs

Every command ran from the repository root in an unsandboxed shell, with
`/opt/homebrew/opt/rustup/bin` prepended to `PATH` and `PYTHONOPTIMIZE`
unset.

| Gate | Command | Output directory and run id | Result |
| --- | --- | --- | --- |
| Signed build, fresh | `make build PW_FRESH_BUILD=1 IDENTITY=...` | `dist/PolicyWitness.app`; record commit `6f0802cb788dbb2de001e788e66f706dad5df945` | passed; every step banner in the documented order; 8 executables and 2 seals signed with the hardened runtime, the Developer ID chain, its team and a secure timestamp |
| Default battery | `PW_TEST_OUT_DIR=tests/out/runs/provenance-repair-default-20261016-credited tests/run.sh` | `20261017T004857Z_5cce7d04` in `tests/out/runs/provenance-repair-default-20261016-credited` | passed: 188 selected, 188 completed, 188 passed; no skips, unrun cases or harness errors; app unchanged |
| Opt-in build and artifact controls | `PW_TEST_OUT_DIR=tests/out/runs/provenance-repair-optin-20261016-credited tests/run.sh --case preflight/signed_artifact_controls --case preflight/build_guard_controls --case preflight/build_refusal_controls --case preflight/build_toolchain_switch_controls` | `20261017T005926Z_348917a8` in `tests/out/runs/provenance-repair-optin-20261016-credited` | passed: 4 selected, 4 completed, 4 passed. The refusal controls made 75 control runs (33 in each variant, including the valid neighbour, plus 9 sequences) and 9 mutation demonstrations, every guard stage failing its control. The toolchain switch refused reuse by `developer_dir` and recovered fresh under the Command Line Tools with SDK 26.5 |
| Controller unit tests under the lock | `tests/lib/checkout_lock.sh -- cargo test --manifest-path controller/Cargo.toml` | the managed `controller/target/` | exit 0 through the front end; every batch passed (235, 27, 56 and 15 tests, with one ignored test in each of two batches) |
| Release preflight report | `/usr/bin/python3 -B tests/lib/release_preflight.py --report` | stdout | exit 0; one problem reported, that HEAD is not at a release tag (it would stamp `v0.3.0-36-g6f0802c`) |

These runs replace the credits of `provenance-acceptance-default-20261016-credited`
and `provenance-acceptance-optin-20261016-credited` for the boundaries above;
those runs and their receipts are kept. The lock lifetime observations are in
`full-lock-lifetime.json`, the oracle's results in `cargo-oracle.json`, and
the mutation results in `mutations.json`, all under the opt-in run's
`suites/preflight/build_refusal_controls/artifacts/`.

The following runs informed the work and are not credited:

- `provenance-repair-default-20261016` (run `20261017T001346Z_08a40e69`), the
  default battery at `b7b24b4` against a build made under Xcode 27.0. All 188
  cases passed, but its last minutes overlapped the Xcode update and the
  control correction followed it, so it is superseded and not retained.
- `tests/out/runs/dev-*` and `.tmp/dev-runs/`, selections and direct control
  runs during the repair. Among them, `.tmp/dev-runs/final-1` stopped when
  the Xcode update removed the interpreter's library during a restore build.
  `.tmp/dev-runs/final-2` ran the mutation phase, the lifetime control and
  the oracle at the correction before it was committed.

### Documentation walkthrough

The documents were read as an operator would read them, after
`docs/generate_build.py --check` reported the figure, the scalar spans and
every region current:

| Path | Manifest | Authored account | Evidence |
| --- | --- | --- | --- |
| One valid build | steps `admission`, `lock`, `stamp`, `builddir`, `cargo_admit`, `fresh`, `cargo`, then native compilation, assembly, signing and `evidence`; invocations `inv_lock_launch` and `inv_lock_verify` | BUILD.md "The checkout lock" (front end, handoff, protected launches); "Inputs beyond the tree" (the SDK request, the two build directories, Cargo's environment); "Cache compatibility, replacement and recovery"; SIGNING.md "The provenance record" (requests apart from effects, validation) | the acceptance build's banners and record above; `control_none`; `control_sdk_requests` |
| `lock_claim_invalid` | produced at `lock` and at every helper step that admits | BUILD.md "The checkout lock", second paragraph | `control_lock_claim_invalid`; the handoff unit tests |
| `build_requests_missing` | step `lock` | BUILD.md "The checkout lock", second paragraph; tests/README.md, the locking contract | `control_build_requests_missing` |
| `cache_path_unsafe` | steps `stamp` through `evidence` | BUILD.md "Inputs beyond the tree", the two build directories; "Cache compatibility", fresh mode's replacement | `control_cache_path_unsafe`; the admission mutation |
| `cargo_configuration_unresolved`, `cargo_environment_conflict` | steps `builddir`, `cargo_admit`, `configure` and `native_check` | BUILD.md "Inputs beyond the tree", Cargo's environment | `control_cargo_configuration_unresolved`, `control_cargo_environment_conflict`, `control_cargo_configuration_oracle` |
| `cargo_judgment_unknown`, `cargo_target_reused` | step `cargo` | BUILD.md "Cache compatibility", fresh mode's replacement; "The evidence the build embeds" | `control_cargo_judgment_unknown`, `control_cargo_target_reused`, `control_cargo_selection_sequence` |
| `provenance_probe_failed` | every step that probes | BUILD.md "The evidence the build embeds", the probe bounds | `control_provenance_probe_failed`; the probe unit tests |
| `provenance_required_unknown` | step `evidence` | SIGNING.md "The provenance record", the validation paragraph | `control_provenance_required_unknown`; `test_the_producer_validates_before_sealing` |
| Lifetime of the hold | none | BUILD.md "The checkout lock", third paragraph and its known gap; tests/README.md, the locking contract | `control_lock_lifetime`; `dispatcher/retention_controls` |

The step table's Reads and Writes columns place path admission ahead of every
session and cache write, as the prose does. Nested ownership, request
capture, Cargo includes and the child environment, and probe bounds mean the
same in the generated rows and the surrounding sections. Two statements in
BUILD.md's account of the refusal controls described outcomes the controls
did not assert: that Cargo fails each configuration the resolver refuses,
and that a standalone Cargo command succeeds after the holder exits.
`6f0802c` added both assertions rather than changing the prose.

### Limitations recorded at `6f0802c`

- The worker clock finding stays open under `runner/SAFE-WAIT-TIME-PLAN.md`.
  `witness_contract/bug_report_returns_verdicts` passed in both repair
  batteries; a passing rerun does not resolve the finding.
- The lock is a managed-entrypoint guarantee. It does not serialize direct
  tool invocations, and a protected descendant that outlives its command
  keeps the lock until it exits. A caller that was itself started through the
  Python shim passes the shim's values to the front end unless it removes
  them first.
- The Cargo resolver covers the configuration forms the controls exercise,
  and refuses an unrecognized value type rather than guessing. Its oracle
  compares it only with this machine's Cargo 1.99, and only for variables the
  shim leaves alone, so a forced `SDKROOT` is covered by the resolver tests
  and the conflict refusal, not by observed compilations.
- Mutation anchors are checked only when the opt-in refusal controls run. A
  helper interface change can leave them stale until then, as `b410ac3` did.
- Cargo's judgment and the current probes describe a reused output's state,
  not its compilation history; the record and the build document say so.
- The single-SDK guard fixture is a controlled metadata mismatch. Genuine
  compilation against another SDK is exercised only by the toolchain switch,
  which needs two developer directories and fails without them.

## Review corrections

Review of `e398c38` reproduced additional defects in the implementation tested
at `6f0802c`. The retained summaries do report 188/188 and 4/4 passing with
unchanged artifacts; the issue was what those controls established. Their
receipts remain intact. The replacement acceptance below now carries the
credit for the reviewed implementation.

- **Channel identity and nested admission.** A separate process could copy
  the public owner record, create an unrelated socket pair and hand over an
  independently opened, unheld descriptor on the correct inode. Admission
  accepted it. A nested scope also served admissions after the acquisition
  owner exited. Admission now binds the channel's socket identity to the
  acquisition record and its kernel-reported peer PID to the acquisition
  owner; nested scopes pass the original channel on.
  The new impostor and surviving-nested-scope controls fail against the
  previous helper and pass with the repair.
- **Cancellation and handoff bounds.** The supervisor waited indefinitely
  for a command ignoring the forwarded signal before reaching its bounded
  group wait. The new stubborn-command control times out against the old
  helper; the repaired supervisor returns the original signal status after
  at most 10 seconds of grace and 5 seconds observing SIGKILL cleanup.
  Admission now bounds its send, reads complete stream replies, and rejects
  request snapshots too large for the complete handoff. Controls cover a
  full queue, a large request reply and an oversized combined snapshot.
  Probe cleanup also uses one deadline across TERM, KILL and the final
  observation; it previously restarted its allowance for each wait. A
  constructed unreaped-group control exercises that otherwise rare path.
- **Admission before creation.** A refused session start created a missing
  `controller/target` before checking the sibling `builddir`, or before
  noticing missing preserved requests. The helper now verifies requests and
  all existing cache components first. Both refusals leave that parent absent.
- **Record structure and consistency.** The old validator accepted an empty
  stamp projection, string-valued Meson booleans, an arbitrary replacement
  value and empty Cargo profiles. These counterexamples were reproduced
  against the previous module using the credited app's real record. Typed
  fields now cover those structures, set requests require their permitted
  values, private requests retain presence only, and fresh-mode observations
  agree with the knob, directory states and Cargo's literal rebuild judgments.
  Cargo admission also refuses malformed or test-harness artifact profiles.
- **Independent archive observations.** A ZIP's matching hashes did not
  establish that its recorded linker tools or signature claims were true.
  The archive reader now observes load commands and signatures on temporary
  copies of its named executables. Both record readers limit bytes before
  parsing. Release fixtures now carry real linker-signed Mach-O stand-ins
  and independently authored metadata, rather than arbitrary text members.
- **Unknown observations.** Two missing wrapper hashes compared equal
  inside an otherwise populated compatibility field. Recursive unknowns
  now prevent reuse. Failed launcher observations no longer silently select
  the standalone-Cargo model. Resolving the launcher requires an explicit
  `RUSTUP_TOOLCHAIN` or an active toolchain reported by `rustup` on `PATH`.
- **Mutation maintenance.** The default provenance controls now apply all
  nine opt-in mutations in memory and require each anchor to match. The
  opt-in execution still establishes that each mutated guard fails its
  control. This removes the mutation-anchor limitation listed above.

The owning build and signing documentation, build manifest and generated
account, locking reference, suite reference and fixtures describe these
repairs. The worker identity inputs did not change. The worker-clock finding,
the managed-entrypoint scope, Cargo's reused-output history limit, and the
Cargo oracle's Python-shim limitation remain as described above.

### Acceptance of the reviewed implementation

The implementation and regression controls are in `be14f3a`; `c23dd42`
corrects the shared release fixture's initialization for every consumer.
Acceptance ran against clean commit
`c23dd42588dbf48714c9f984c267a00af203d4e5`, before this reporting update.
The signed full build is **0.3.0 (662)**, describing
`v0.3.0-40-gc23dd42`, with `source.dirty: false`. Both cache areas were
replaced and all three shipped Cargo targets reported `fresh: false`.
Xcode 27.1 (`27A9275`) selected SDK 27.0 (`26A425`).

| Gate | Evidence | Result |
| --- | --- | --- |
| Fresh signed full build | `review-acceptance/build.log` and `provenance.json` in the credited default run | Exit 0; commit and clean stamp checked; every shipped Cargo target rebuilt. |
| Default battery | `runs/provenance-review-default-20261017-credited`, run `20261017T025051Z_98fb0575` | 188/188 passed, no skips, unrun cases or harness errors; valid app unchanged. Includes 35 provenance helper tests, dispatcher controls, source drift, and release publication/rotation. |
| Four required opt-ins | `runs/provenance-review-optin-20261017`, run `20261017T021818Z_99467b08` | 4/4 passed, no skips, unrun cases or harness errors; valid app unchanged. Includes 17 build-guard checks, 75 refusal runs, nine state sequences and nine guard mutations. |
| Managed Cargo tests | `review-acceptance/cargo-test.log` in the credited default run | Exit 0; every batch passed. The two ordinarily ignored fixture entrypoints are exercised explicitly by their owning default cases. |
| Release preflight report | `review-acceptance/release-preflight.json` and `.stderr` in the credited default run | `--report` exited 0; its only warning is that HEAD is not at a release tag. This is not strict release authorization. |

The opt-in toolchain switch used Xcode's SDK 27.0 and the CLT's SDK 26.5
(`25F70`). Its equipment probes found that the CLT's default SDK 27.0 did
not link with its own tools, so the control explicitly selected the installed,
linkable SDK 26.5. The developer directory, C and Swift identities, SDK
path, version and build differed; incompatible reuse was refused and fresh
recovery passed. `switch.json`, `equipment.json`, and the link receipts under
that case retain the observations. The older SDK 15.4 note earlier in this
record describes its original receipts, not this replacement run.

The default run's `review-acceptance/receipt.json` binds the manual commands,
their exit statuses, the two credited run IDs and these final identities:

| Item | SHA-256 or identity |
| --- | --- |
| Worker source identity | `b3b5f50a1f90e5cf11f864dfaa85b752961b115d773abf49ce00e28dba19f5be` |
| Final ZIP | `031aa866d747df58a9fc368bf97a670773782ec9700e284a321de06e1087d0d7` |
| Final controller | `48a376393b835a43c92c00fb9b1be4b683de5002c341be45a02102a0ea42fef8` |
| Embedded provenance record | `21c8a42b51bfb56f1daa3bfccd162fc2e002a4f39d1a9b163a400aadcbb15345` |

The same directory retains `regression-baseline.log` and
`regression-fields.json`: the unrelated-socket and surviving-nested-owner
controls reject the previous implementation, its stubborn-command test
times out, and the malformed-record, premature-directory-creation and
unknown-wrapper-hash counterexamples reproduce against the previous module.
These review receipts were added after the managed battery completed;
they supplement its original case reports.

The first review battery, `runs/provenance-review-default-20261017`, run
`20261017T021436Z_c03c0675`, is retained without acceptance credit. It found
that release rotation imported the shared ZIP fixture without running its
new initializer. That run was interrupted after the failure: 10 cases passed,
one failed and 177 remained unrun, with the app unchanged. `c23dd42` makes
initialization automatic and declares clang for that consumer. Both release
fixture consumers then passed together, followed by the fresh build and
complete replacement runs above. No failed or incomplete battery is counted
as passing.

The build manifest still describes 33 steps and 51 refusals, with none in
the refusal baseline. Its ownership row now names the acquisition's socket
identity and peer PID; its Cargo row names a typed non-test profile. The
authored lock and cache sections explain the same ordering and lifetime.
SIGNING.md describes typed nested records, bounded readers and independent
archive observations. Their generating and citation checks passed; the
review added no unverified prose-baseline entries.

Reviewed evidence-reuse exception: the reporting changes after `c23dd42`
only update this record and `tests/RETAINED.json`, remove the completed plan,
and redirect its link in the worker-clock plan. The executed scripts, helpers,
fixtures and signed app bytes are unchanged; these reporting changes do not
alter the exercised build, admission, probe or archive-validation paths.
The affected documentation checks were rerun with
`PW_TEST_OUT_DIR=tests/out/runs/provenance-review-closure-docs-20261017 tests/run.sh --case source_drift/limits_documentation --case source_drift/generator_contract`:
run `20261017T030604Z_9de468c2` passed both cases without skips or harness
errors. Its retained entry leaves the source null because it checked the
uncommitted reporting edits, rather than claiming a clean source commit.

These repairs and acceptance gates complete the provenance repair plan;
its planning text is retired into this record and the owning documentation.
The worker-clock finding remains open in `runner/SAFE-WAIT-TIME-PLAN.md`;
its bug-report case passed again without resolving the finding. The remaining
scope limits are the managed-entrypoint lock guarantee, the lack of historical
compiler attribution for reused outputs, and the Cargo 1.99 oracle's inability
to independently observe shim-affected SDKROOT. The latter remains covered
by resolver and pre-Cargo conflict controls. No release or publication was
performed, and unrelated disposable output was left in place.
