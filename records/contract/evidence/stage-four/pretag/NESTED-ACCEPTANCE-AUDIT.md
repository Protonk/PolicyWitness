# Nested release acceptance audit — 2026-11-11

The completed nested acceptance has a coherent ZIP → built app → extracted app → default battery join. I found no discrepancy in the inspected completed records. This supports the `sequence/release_battery` portion of the full build-refusal rehearsal. The outer case's 16 mutation demonstrations and terminal result remain root's separate audit. This report grants no real `v0.3.8` release, notarization or publication credit.

## Evidence locations and method

All relative paths below start at:

`A = tests/out/runs/contract-v038-build-refusals-20261111/suites/preflight/build_refusal_controls/artifacts`

- `F = A/full-release-battery`: disposable fixture build command, stdout/stderr, fixture configuration, tool receipts, provenance, toolchain/session and output hash inventory.
- `B = A/release-battery/acceptance`: copied, completed acceptance, assessments, version output, extraction/integrity, controlled notarization and rehearsal records.
- `T = B/tests`: the nested default battery, canonical run **20261111T205355Z_357efdcc**.
- `A/release-battery/driver`: enclosing real rehearsal command and its successful completion.

Grade: direct reading of retained execution records; independent JSON, SHA-256 and ZIP-member calculations; current source reading to interpret ownership and scope. No checker CLI, build, test, product executable, signature command, Git mutation, Apple operation, output cleanup or evidence copy was performed for this audit. Only this private report was written. Parent reports the source/app freeze at `e30cf4c3c182f96482664671327ffa1f2fe78ecf`; the audit's narrower independently verified source joins are stated below.

## Build, public identity and archive joins

The disposable fixture build command is `bash /private/tmp/pw-release-battery-euu32zfg/checkout/build.sh`, recorded exit 0, no timeout, 58.80915983300656 seconds. `F/fixture.json` says full build, `fresh = "1"`, empty version/build overrides, no injected hooks. `F/result.json` says status 0, no fired hooks and free build lock. Provenance records `BUILD_XPC=1`, `PW_INSPECTION=1`, `PW_FRESH_BUILD=1`. Its build/Cargo directories were newly created; fresh mode here does not demonstrate removal of pre-existing caches. Separate refusal sequences own that behavior.

Actual embedded ZIP plist, ZIP provenance, retained actual `--version` response and the two standard-run envelopes agree on:

| Identity | Value |
|---|---|
| Public contract | `release:v1.0.0` |
| Version / describe | `1.0.0` / `v1.0.0` |
| Build number | `1335` |
| Fixture source commit | `45815df6a28ffe41ce6f0ebd0eb7160b8d48bd32` |
| Fixture source dirty | `false` |
| Worker identity | `52bbda618677886b6c59dcf5dd999e2b2a5021cbd2c8dc4f08aa0ba66ef2dd38` |

`control_release_battery` seeds actual annotated historical trees into a new disposable repository using `contract_fixture.seed_release_history`, renders prospective outputs, commits and annotates a fresh synthetic major tag. The fixture's `v1.0.0` and build 1335 are therefore expected. They are not real main's prospective `v0.3.8`, nor development build 1339. I read this source path and the emitted identity evidence; I did not re-run or inspect a surviving temporary Git repository.

The actual retained `B/controlled-notarization/submitted.zip` has SHA-256:

`7b7866cb80fcfa5881ce4bf6ed0a44df2eb73de750a8a23c85ace8a6a42aa99e`

I recalculated it and joined it to `F/result.json`'s ZIP hash, acceptance's before/after hashes, rehearsal's archive hash and the controlled-notarization receipt. Reading the ZIP without extraction found 119 entries and no duplicate filenames. Its app member set exactly matches all 47 inventory paths, including modes; all 22 retained app file hashes match the actual ZIP contents and `F/result.json`. ZIP provenance bytes equal `F/provenance.json` exactly. The extra ZIP root is `__MACOSX`.

Representative independently joined app byte hashes:

- Controller: `45c280fccd63464f83a86916a90d055917a3c06df602c56739fecde684581ab7`
- Host: `1926b78cc68bd2d34486d698544e8398fcdc7654e1e55a30f2a14ebb9ce65498`
- Standard worker: `7ea3d82206d45bc8caf367e5ce4058243ee49ae9c61ba18abb840fb00684163f`
- Build provenance: `0a16455dbccb357efd39402bf5a94b276097e6ba543845005b8313582c80857f`

The acceptance and battery `before.json`/`after.json` inventories are all equal; both change records are empty. Both retained inspection reports are byte-identical, `ok: true`, with no errors. Their eight real codesign verification commands returned 0; all seven native targets are thin arm64 with empty target/problem lists. Host invariance and worker-clock symbol inspection commands also returned 0 with no forbidden results. This is retained execution evidence, not a new signature verification.

## Acceptance and the Apple boundary

`B/acceptance.json` schema 3 records acceptance **accept-dc41eca6368e475eb0c1005dfe998477**, `ok: true`, errors `[]`, and matching ZIP hashes. Its owner is terminal and names the same acceptance. The actual extracted app was `/private/tmp/pw-release-rznz_kqo/PolicyWitness.app`.

`A/release-battery/driver/command.json` records the real `tests/lib/python.sh tests/fixtures/release/live_battery.py` driver, exit 0, no timeout, 1940.3025269589853 seconds. The driver encloses real extraction, actual version execution, real artifact/signature inspection, and exactly one actual `bash .../tests/run.sh` invocation. `B/execution/command.json` records that unselected default command, exit 0, no timeout/interruption, 1938.5038220419083 seconds under its 7200-second bound. `B/rehearsal.json` lists exactly five acceptance commands: extraction, version, staple validation, Gatekeeper and the battery. Source additionally requires a second real independent extraction and equal inventory before the driver can return 0; my ZIP member calculations independently corroborate that binding.

Only notarization, staple validation and Gatekeeper are controlled. The notarization receipt uses the fixture's fixed submission ID and locally supplied `Accepted` result. Stapler/Gatekeeper command records explicitly say `controlled: true`, with synthetic zero elapsed time. Their command stdout says no real assessment occurred. This rehearses the handling and archive binding of those responses; it establishes no Apple submission, Apple acceptance, real staple or real Gatekeeper approval.

## Complete nested default accounting

The canonical run and acceptance agree on **229 selected, 229 completed, 229 pass, zero skipped/unrun**, terminal `true`, `ok: true`, no harness errors. All 229 invocations exited 0. The separate count of 228 is explicitly scoped to legacy reports; the remaining canonical case is the pytest family.

I independently reconstructed defaults and dependency ordering from the current catalog after joining its SHA-256 to the captured source. All 229 case IDs and their order match the captured execution contract, plan and results. The carried `plan.json` equals the run's plan; `dispatch.json` invocations equal the run's invocations; their complete planned case records agree. I reread each of the 228 retained legacy report files: each equals its captured report object and reports pass.

The acceptance, run and plan execution contracts are equal. Their canonical JSON digest independently recomputes to:

`acbc187c5e673e0307684bf5696f7141aa27c821d94e4e0c44a4d60f5fa750c1`

The captured catalog hash `0239035c9a8fcea048225ce4842b5c56d1301d2b186238349074b9428b357c75` and execution-contract reader hash `877c853db5c3f37784a592dc5237e4485e469809f531ef345b3a6ce1e56f2d06` match current files.

Required family `runner_c_worker_harness/exec_control_states` has all nine selected items, in order, with 27 passed setup/call/teardown phases, complete accounting, engine return 0 and no errors. Its selection canonical digest equals recorded manifest `246cda6c0f4218654844a0c9a3c230167b88d635785fe5580afac82d6e713566`. All 16 operation IDs join ownership; commands are closed, authority revoked and process groups absent, without cancellation or timeout. All seven captured family-source hashes match current files. Controlled mutation/native negative commands may return nonzero while their owning item correctly passes; their observations are distinct from the parent engine result.

`runner_unit/pwrunner_core_unit_executable/artifacts/pwrunner_core_tests.log` contains exactly 604 successful expectation lines and `604/604 tests passed`. The four retained transfer/clock/actor/definition Rust reader logs each record the intended single test passing, with zero failed/ignored. Independent porcelain projection controls report success. The definition corpus has 142 Swift cases, 143 Rust/Python cases and seven JSON-only controls, with empty Rust/Python failure lists. Its recorded domain is constructed typed replies, not sandboxed-worker execution; this audit retains that distinction.

Every canonical case and invocation reports zero system sleep, with no measurement errors. Caffeinate launched successfully and remained running at completion. No Swift per-block system-sleep line appears; the read `TestKit` prints such a line at a measured gap of at least 1 ms. These are the recorded sleep scopes, not a claim of sub-millisecond precision.

## Guide staging

`F/build/stdout` records successful validation of 111 limits, 18 questions and 43 matrix rows and staging at `/private/tmp/pw-release-battery-euu32zfg/dist-full-release-battery/PolicyWitness.md`. `F/result.json` records that staged file's SHA-256 as:

`4c2054a0723d25edc19094bc2f2647fcea5dc5220702d73818a6769009e87fd3`

This is the fixture guide identity, after prospective synthetic-release generation. It differs from the frozen main development guide (`31944ef9cd04d131e1cf2314ba1bb3e0f67322a4f58a5a828bcb08136f3fa3a4`). The fixture source renders contract outputs before building; the read `generate_limits.py::main` stage path validates current generated content and copies the checked guide bytes.

Grade: successful actual staging command plus retained output inventory hash and inspected copy semantics. The standalone staged guide bytes are not retained in the examined `F`/`B` evidence, and the app-only ZIP does not contain that external guide. I therefore cannot independently rehash or review this fixture's complete staged guide from the retained bytes. Its hash must not be substituted for real main's guide or the eventual `.8` archive guide. No additional test is requested on this account; root owns real release archive staging later.

## Completed controls and attribution limits

`A/controls.json` contains exactly the expected 88 distinct records: two valid variants, 37 controls in both full/partial variants, and 12 sequences. I compared this set with literal declarations in the current source. `sequence/release_battery` is present with status 0 and 2087.2 seconds. The source appends each record only after its function assertions return; nonzero or null statuses in other sequence records represent their controlled final command/return values, not failed outer cases. It writes the 16-mutation result and checks final full-case completion afterwards. I did not inspect or credit that active phase or its eventual terminal result.

All six embedded provenance input hashes match current root files, as do the catalog/reader and seven family source hashes above. Source reading shows the disposable checkout copies tracked and eligible untracked inputs, uses real tools with no nested-build mutation hooks, imports release ancestry and then changes release outputs/identity. The copied fixture commit intentionally differs from main. The retained source list does not hash every executed shell/Python/Swift/Rust dependency. It supports the stated source-bound selections, specific hashes and builder mechanism, together with root's freeze assertion; it is not a complete cryptographic source closure or independent proof that every source byte was main HEAD. I have not inferred provenance from current mutable distribution artifacts.

Scope read: relevant tests instructions; `build_refusals.py` checkout/build/evidence helpers, `control_release_battery`, control/sequence declarations and full-case ordering; `contract_fixture.py`; complete `live_battery.py`; controlled Tools/notarization and release acceptance/archive binding paths; execution-contract/default selection/ownership semantics; guide staging; Swift TestKit; retained records listed above, all legacy report objects, and selected detailed family/reader logs. Not reread: every test implementation or every case's raw outputs, the current outer mutation records, current outer terminal status, all historical release trees, every current product source, or the entire guide. The detailed checks here supplement the aggregate default result without recasting all reported passes as individually re-audited behavioral evidence.

The next real `.8` tag, release build, Apple workflow, release ZIP acceptance and archive/publication gates retain their planned places after maintainer review. This audit does not move the user-directed pre-tag pause.

## Evidence hashes

SHA-256 values below identify the exact retained records read. Paths are relative to `A`.

| Record | SHA-256 |
|---|---|
| `controls.json` | `cd549d3674992d1888119506bfeaf180d53ecd6011465671211aeddef6d0cb18` |
| `release-battery/driver/command.json` | `5ca881f178153a8b5f495033a0da41d2dc67cc720d442de09210b8e5265f102f` |
| `full-release-battery/build/command.json` | `ea6bd23de0290a8c641dad0287cad1e884e601c6292a832f144f770bd38dca8d` |
| `full-release-battery/build/stdout` | `c9805ae9f55bf8c7afbca07bce28a701b7a11a1e31aa5ad12bc0c344820630e1` |
| `full-release-battery/result.json` | `ed0ab8c185936a9d3b4a59d552e622b2dbc3de4c7aecb6ec5c22874932aa158a` |
| `full-release-battery/provenance.json` | `0a16455dbccb357efd39402bf5a94b276097e6ba543845005b8313582c80857f` |
| `full-release-battery/fixture.json` | `d2e314223d066b6dbaadcb005c653c584dedbf80ad714701a5fee63fb19744cf` |
| `release-battery/acceptance/acceptance.json` | `eb7a7d240c464505fb967b34d25d8c09f25e82a980efb50850fa64fe05e71483` |
| `release-battery/acceptance/rehearsal.json` | `f25ca32f4ca3a3b15590bfa68b4d814ea4b0fca3a1892349edab5d42562cb92c` |
| `release-battery/acceptance/execution/command.json` | `3f8836cb84d0e1e89515476f2f82777188209ac04a9fb92d514310f3af031644` |
| `release-battery/acceptance/version/stdout` | `07ea49080e5d2752d283afbd901d4bbe95f26b07de91ebd63c68d3c0e9f4a52d` |
| `release-battery/acceptance/inspection.json` | `2d61359a9370a5b5e871ec9d4baa700907c36cb637b2c057bcb5938f5d6ab9cd` |
| `release-battery/acceptance/before.json` | `2e28a4cff356cc18a86ac4ba36ca797574e831e61d505052bfb79434bc93e4ce` |
| `release-battery/acceptance/after.json` | `2e28a4cff356cc18a86ac4ba36ca797574e831e61d505052bfb79434bc93e4ce` |
| `release-battery/acceptance/tests/run.json` | `681e71d0c7cd4cdf2453bac3a0186bced19a18d3c67512c76a58bc7f35e17362` |
| `release-battery/acceptance/tests/plan.json` | `33f4c4f25128a37f887b4a590cc936d1c52900b7b3a87e0ccd05fb1555893a8d` |
| `release-battery/acceptance/tests/dispatch.json` | `607e92f1a170dcfb9110d082814587992f621b6f898fedda938cf397838addab` |
| `release-battery/acceptance/tests/suites/runner_c_worker_harness/exec_control_states/family.json` | `bb9fc36f25cab596cd3769f42d1c02396a9d0b3d934f133e3aae162d0291b6ba` |
| `release-battery/acceptance/tests/suites/runner_c_worker_harness/exec_control_states/selection.json` | `f6c7cb8c35d3eab937c9ea902c0d462e7fd50ff8f795414568a989f4ac270af7` |
| `release-battery/acceptance/tests/suites/runner_c_worker_harness/exec_control_states/ownership.json` | `79ea13f36360e23c103c8181248500ce8da0ea2be773261a55f943954bbeffc3` |
| `release-battery/acceptance/tests/suites/runner_unit/pwrunner_core_unit_executable/artifacts/pwrunner_core_tests.log` | `a243cc6e98ac25cbb7d4b96c59b8ede7a8741b93777598a2b7b551008be62f3a` |
