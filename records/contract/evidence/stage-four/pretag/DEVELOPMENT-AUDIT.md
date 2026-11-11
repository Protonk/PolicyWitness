# Independent final-development audit — 2026-11-11

**The completed resumed development battery is complete and passing at its recorded scope.** Canonical run `20261111T191123Z_094abff3` selected/completed 229 cases, all passing, with zero skips, unrun cases or harness errors and zero recorded sleep for every case. The selected signed app's retained before/after inventory is identical. This supports the last development rehearsal; it supplies neither final `.8` release identity nor Apple acceptance.

Let **D** mean `tests/out/runs/contract-v038-resumed-development-20261111`. Let **R** mean `tests/out/runs/contract-v038-build-refusals-20261111`, and **A** mean `R/suites/preflight/build_refusal_controls/artifacts`. The required refusal case is active and root-owned. I did not open its changing receipts, poll it, wait for it or credit any part as complete. Its nested acceptance map below is prepared from source only.

## Independently checked completion

- D/run.json is terminal and `ok: true`, with 229 unique case results in exactly the plan's order. Its selection is `default` with empty requested case/suite lists. I independently derived the default membership/dependency order from the current catalog, whose bytes match the captured catalog hash: all 229 IDs and order match. The catalog serialized inside the report sorts object keys, so its object insertion order is not the command order; the retained plan and matching original catalog supply that order.
- All 229 invocations exited zero, report no harness/sleep-read errors, and record zero sleep. D/plan.json equals the plan embedded in run.json; D/dispatch.json's invocation records equal the run's. All 228 referenced legacy report files exist, exactly equal the captured report objects and report pass. The summary's legacy count 228 is explicitly labelled `legacy reports only`; it is not a missing canonical case.
- The remaining canonical case is `runner_c_worker_harness/exec_control_states`. Its selection, family and ownership receipts show nine selected items in the same order, all nine passed; all 27 setup/call/teardown phases passed; the 16 declared operation IDs exactly match its 16 ownership commands. All commands are closed with authority revoked, group absence, no launch error and no timeout; ownership has no problems. The selection digest matches the family manifest digest. These are retained controller observations, not a fresh OS process inspection in this audit.
- The captured execution contract identity `acbc187c5e673e0307684bf5696f7141aa27c821d94e4e0c44a4d60f5fa750c1` independently matches canonical hashing of its contents. Its source catalog SHA-256 is `0239035c9a8fcea048225ce4842b5c56d1301d2b186238349074b9428b357c75`, and execution-contract reader SHA-256 is `877c853db5c3f37784a592dc5237e4485e469809f531ef345b3a6ce1e56f2d06`; both match current files. All seven family-selected source hashes also match current files. These records identify their declared selection/reader inputs, not the whole repository's test dependency closure.
- `runner_unit/pwrunner_core_unit_executable` logs 604 separate `ok` lines and `604/604 tests passed`, with no internal SKIP/FAIL or “system slept” line. TestKit emits sleep lines for measured gaps of at least 1 ms; absence is that bounded observation. The dispatcher also records zero sleep for the enclosing case and all others; its idle-sleep assertion was launched and running at the end.
- Runner-unit's transfer, worker-clock, actor and definition replay logs each record their exact intended Rust test, `running 1 test`, and one pass. Independent porcelain replay also passed. The definition corpus receipts contain 142 Swift records and 143 Rust/Python records including real writer fallback, plus seven JSON-only inputs; Rust and Python failure arrays are empty. Their stated domain is constructed typed replies without sandboxed worker execution. This audit checks completeness/summaries, not a fresh adjudication of every corpus predicate.

## App and build attribution

D's inspection has `ok: true`, empty errors, nine matching manifest entries, seven thin arm64 macOS executable observations without target problems, and eight successful retained `codesign --verify --strict --deep` invocations. Host sandbox-symbol and worker-clock observations also have their expected empty forbidden sets. The before/after inventories are equal across all 47 paths; changes.json is `{}`. I compared the presently frozen app with that retained inventory before using its embedded records: all 47 paths/modes and 22 file hashes match, with no additional paths. No new signature command was invoked.

The matching plist, embedded provenance and actual retained dossier/standard-run envelopes report:

| Identity | Retained value |
|---|---|
| Source commit | `e30cf4c3c182f96482664671327ffa1f2fe78ecf` |
| Describe / dirty | `v0.3.7-5-ge30cf4c3` / `false` in provenance |
| Version / build | `0.3.7` / `1339` |
| Public contract | `development:84448fb421a5a0e4acdbce236dae143e04df6d425c7a258c12df447e9b762444` |
| Worker identity | `52bbda618677886b6c59dcf5dd999e2b2a5021cbd2c8dc4f08aa0ba66ef2dd38` |
| SDK | 27.2, build 26B118 |
| Build knobs | `BUILD_XPC=1`, `PW_INSPECTION=1`, `PW_FRESH_BUILD=0` |
| Signer | Developer ID Application: Adam Hyland (42D369QV8E) |

The build stdout begins with `make build`'s signed entry, checks current generated outputs/worker identity and records the same build stamp. It ends with successful packaging, guide staging and a report of seven executables plus two enclosing seals carrying Developer ID chain, hardened runtime, team and secure timestamp. The coordinator reports terminal status zero from session 98434; the separate stdout/stderr files are retained logs rather than a machine command-status receipt in D. Embedded provenance is independently bound to D by the retained file hash. Its six declared input hashes all match current files. The observed `PW_FRESH_BUILD=0` must not be described as a fresh-cache rehearsal; the plan's fresh tagged rehearsal still follows review and tagging.

The current source and staged guide are byte-equal, SHA-256 `31944ef9cd04d131e1cf2314ba1bb3e0f67322a4f58a5a828bcb08136f3fa3a4`. Build stdout records staging that guide. D's app inventory covers the bundle, not the adjacent guide, so this is a current source/staging comparison joined to the coordinator's frozen-tree record, not a retained in-run guide hash. The separate guide-workflow evidence owns actual displayed-command execution.

`D/suites/witness_contract/dossier_witness/artifacts/ordinary/run.json` independently reports the same full build stamp. The two acceptance-designated standard-run envelopes, `smoke/specimen_file_read_deny/artifacts/policy_witness.run.stdout.json` and `witness_contract/happy_path_baseline/artifacts/run.json`, report this development identity and `runner_kind: standard`.

### Limits on the source/build join

There is no whole-repository source snapshot in D/run.json. Its execution contract captures the catalog/reader, and the family selection captures seven further source files. The build provenance reports a clean commit and six source input hashes; its identity is an observed build claim, not source-to-binary attestation. The matching retained app bytes, actual envelopes, build log and root's explicit frozen `e30cf4c3` coordination support candidate attribution. This audit did not independently recalculate the entire public/worker identity closure, compare every source path with the Git tree, or re-open every case's dependency graph. A claim that “the run cryptographically attests all source and every compiled byte to e30cf4c3” would exceed these records. I found no conflicting identity in the inspected joins.

The full default has no `guide_workflows`, `build_refusal_controls` or other opt-in credit. Individual cases still distinguish source-built controls, substituted native returns, constructed replies and actual signed/kernel effects. Counting all 229 passes does not promote those observations into a uniform native claim.

## Nested release-battery path map — execution still pending here

`control_release_battery` creates a fresh disposable source copy independent of earlier refusal mutations, imports actual local annotated release history, prepares a new synthetic release (the helper chooses the next major, e.g. `v1.0.0` for a source with only v0 releases), commits/tags that disposable copy, and builds it with fresh mode. Its fixture tag/commit/public identity are deliberately distinct from root HEAD, build 1339 and the future real `v0.3.8`. It clears fixed fixture version/build overrides so the disposable tagged build supplies those fields. The built app, signatures, ZIP extraction, inspector and every default test are real.

After the outer run ends, inspect these exact locations without treating the existence of a partial file as completion:

| Location relative to A | Required meaning/check |
|---|---|
| `controls.json`, `mutations.json`, `assertions.log`; outer R/run.json and case report | Whole case terminal/pass, no skipped/unrun/harness/sleep errors; all 76 variant records plus all 12 sequences = 88 records, and 16 top-level bypass/displacement demonstrations. Refusal records often have expected nonzero statuses; judge their owning assertions. Nested default's 229 is a separate count. |
| `full-release-battery/fixture.json`, `build/command.json`, `build/stdout`, `build/stderr`, `result.json` | Full fixture variant and fresh mode `1`, actual build command completion/no timeout, signing/packaging, tools/hooks and output inventory. `result.json` stores build status and before/after distribution hashes. |
| `full-release-battery/provenance.json`, `pw-build-session.json`, `pw-toolchain.json` | Synthetic clean fixture source/tag/version, worker/public identities, selected toolchain and fresh/rebuild judgments. The original fixture source is a copied working tree, followed by prospective stamps and a synthetic commit; do not label it the exact root commit. |
| `release-battery/driver/{command.json,stdout,stderr}` | Real live-battery driver completed without its 7500-second outer timeout; stdout identifies the nested acceptance/run. |
| `release-battery/acceptance/acceptance.json` | `ok: true`, no errors, matching ZIP hashes before/after, actual synthetic `release:v…` contract, nested battery run ID/completion and elapsed/timeout result. This is fixture acceptance, not Apple's acceptance. |
| `release-battery/acceptance/rehearsal.json` | Fixture explicitly names controlled notarization, staple validation and Gatekeeper. Calls show one actual default dispatcher invocation. ZIP hash agrees with acceptance/build inventory. |
| `release-battery/acceptance/controlled-notarization/` and `staple-validation/command.json`, `gatekeeper/command.json` | Controlled local responses, with `controlled: true` on assessment receipts and stand-in call records. A recognized fixture Accepted response is not evidence of a remote Apple submission, ticket or assessment. |
| `release-battery/acceptance/{before.json,after.json,changes.json,inspection.json}` | The extracted app passed real inspection and stayed byte/mode-identical. Compare its inventory with the nested dispatcher inventory. The driver additionally re-extracts the same ZIP and compares that independent extraction's inventory before returning. |
| `release-battery/acceptance/version/{stdout,command.json}` | Actual extracted controller version agrees with its plist and the synthetic tagged release identity. |
| `release-battery/acceptance/execution/command.json` | Exact `bash <fixture>/tests/run.sh` with no selectors; actual command finished without 7200-second acceptance timeout or interruption. |
| `release-battery/acceptance/tests/{run.json,plan.json,dispatch.json}` | Full default membership, terminal success, 229 selected/completed at the present catalog, no skips/unrun/harness errors, zero per-case sleep, extracted app selected, unchanged integrity. Compare captured acceptance execution contract with the nested run. Check legacy 228 plus the required family separately. |
| `release-battery/acceptance/tests/suites/runner_c_worker_harness/exec_control_states/{selection.json,family.json,ownership.json}` | Complete nine-item/27-phase/16-operation account and resolved ownership against that fixture's captured selection. Retained report pass alone is insufficient. |
| `release-battery/acceptance/tests/suites/runner_unit/pwrunner_core_unit_executable/artifacts/` | Swift 604/604, no SKIP/FAIL/sleep markers, exact-one replay logs, corpus counts/failure arrays; keep their constructed/native scopes. |
| The two standard-run envelope paths above beneath nested `tests/suites/` | Both used the bundled standard runner and synthetic fixture build rather than a local app or external runner. |

The outer source asserts the copied acceptance inventory equals the temporary original before the fixture is removed. The fixture does not create `dist/archive/v0.3.8`, does not execute the real release archival/prune chain, and does not replace the tagged fresh rehearsal/final Apple/notarized-ZIP acceptance. Real `.8` tagging and submission remain behind the directed pre-tag review pause. I have not checked whether any listed active-run path exists yet and supply no partial-run execution credit.

## Hash anchors

All hashes below were calculated from files read in this audit. Relative paths are within D; private paths are absolute. File hashes bind these observations to a retained report, not its correctness.

| Evidence file | SHA-256 |
|---|---|
| `run.json` | `532f0b8b052a2705b5cf5af9f886b1d75d308dcf3c2341063461247d79d05faf` |
| `plan.json` | `533fe655b25e7e934641657faf9be2d125680a5bd73529d94d7a5b14eceb3e15` |
| `dispatch.json` | `cbe45abbc19055c89632105a0e244c5dcd4cd7af4cf5d359f2288dad9cfdee72` |
| `artifact-integrity/inspection.json` | `71dc3d4280ffc69dfcf7e31050e954dd434f1015666ce74230eeffe1962a1a88` |
| `artifact-integrity/before.json` | `f19f387a5dffb412bb5073ee2421c189d212dbdc79af8b5f86d09d3cfa383403` |
| `artifact-integrity/after.json` | `f19f387a5dffb412bb5073ee2421c189d212dbdc79af8b5f86d09d3cfa383403` |
| `artifact-integrity/changes.json` | `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356` |
| `suites/runner_unit/pwrunner_core_unit_executable/artifacts/pwrunner_core_tests.log` | `d3a64aabca97e829f5aed3bd41ef0f7b98a7a47812690513dfec45862a8ff1c1` |
| `suites/runner_unit/pwrunner_core_unit_executable/artifacts/definition-readers.log` | `389e4fd9a63070b609979af50d78c14017275a9540231c9698c528fdbd1e4e35` |
| `suites/runner_c_worker_harness/exec_control_states/selection.json` | `f6c7cb8c35d3eab937c9ea902c0d462e7fd50ff8f795414568a989f4ac270af7` |
| `suites/runner_c_worker_harness/exec_control_states/family.json` | `da2ed9f05d7765acf432d5e41854c32c7105debe39255d387397e4623eb0abb5` |
| `suites/runner_c_worker_harness/exec_control_states/ownership.json` | `dc69fc01aa603e305606d63e93706625bad9c6ceb5c6af4e8f044a39af96514a` |
| `/private/tmp/pw-contract-v038-resumed-build-20261111.stdout` | `f735552440aab51c4a7a11f1082d83d71531fe19acba039159cfa876ac99cb41` |
| `/private/tmp/pw-contract-v038-resumed-build-20261111.stderr` | `8ce4964a293dee95a681cb56f702d886ef7f3853152b7de68c45689ecd97c264` |
| `/private/tmp/pw-contract-v038-resumed-development-20261111.stdout` | `c977e615673cbb24ad0a3e660de0c50ef76b08cdc9e1be772372cb19697ce54e` |
| `/private/tmp/pw-contract-v038-resumed-development-20261111.stderr` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The following embedded/output hashes are from D's retained inventory and were matched against the frozen current bundle before its records were used:

| App-relative path | SHA-256 |
|---|---|
| `Contents/MacOS/policy-witness` | `6852fbf0dfc6af329f0deae95fa2cd16ad6bb09398d4b1fbaf4d75d2ca3d40ea` |
| `Contents/MacOS/pw-runner-client` | `fd23bc52f80b8831baf6522d4f48edfac814b1bfa920a8041b47a0ada779dccd` |
| `Contents/MacOS/sbpl-check` | `43c60ac9f2e880d25cd2d576a5556346beb78dcd28ca72da30a8684abd5c5e34` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner` | `dc15e3c2979a4cd914b3f5cb3ad721ba6c7645e1b6d1a78ca94f4b3e415cb45f` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner` | `4b79de1182f6da418b8357063279374c0d8d1faa9497edd92d0c55cd3476905a` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner-unentitled` | `4d3b536072ebf2241547d9c53736c63f5a22f9b5311d1f23cb5d83c585f84a7f` |
| `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator` | `666c6ce4e695bbaecf1f51196df2ecdcbc5ad3602cc517e48155be1a8e15545b` |
| `Contents/Info.plist` | `4439f6c8df668bbdfae3159b62ccdd364c01ee39c7247cc717c69c52511a3bba` |
| `Contents/Resources/Evidence/provenance.json` | `514044f41325afc75aa991ae4ea036ae24476206e847926f6f666280fe0e7bd0` |
| `Contents/Resources/Evidence/manifest.json` | `84878cd2276a2fd5ab52df5fc5d378c7ad6fd338e385aed89f8e390ba36fe553` |
| `Contents/XPCServices/PWRunner.xpc/Contents/Resources/worker-equipment.json` | `d34a63265a1b018e18d5d47720dcdaf8d88925b8c33f6b46a65c01c5bc9d3dae` |

Reader corpus receipt hashes: Swift `4a59de6b1459275250a49d46e573a6f7cef1ff23ed5ae9a83ea578b915d7f192`; Rust `6e2a982ff0d2bc29fadd236805dc59a9cad4e07eec9db7f65112ae687d26b80c`; Python `3c3924cb00ae64a8efa382a79b2b5ef31a949df6cc80a0d1d0f200cde0055a5c`.

## Reading/execution grade

Opened and parsed D's run/plan/dispatch, all referenced legacy report objects, required family selection/account/ownership, integrity inspection and inventories; read the actual build and default logs, Swift summary/sleep and exact replay logs, corpus receipt summaries and selected real envelopes. Compared only the named captured source hashes and bundle inventory; did not execute their validators. Read current `tests/AGENTS.md` evidence-reuse rules, CHANGE-VERIFICATION's full refusal requirements, `test_cli` selection, `execution_contract` family rules, TestKit sleep reporting, runner-unit entry, `build_refusals` copy/build/nested battery path, `contract_fixture.seed_release_history`, `live_battery.py`, and release acceptance/battery rules. The nested path map is a source reading.

Not performed: tests/builds/checker CLIs, product/signature commands, source or tag mutations, Apple operations, cleanup, active-run inspection or monitoring. No complete per-case semantic re-audit, archive verification or whole source-to-binary proof is claimed. Report written only under `/private/tmp`.
