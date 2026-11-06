# Extension consolidation verification selection

Draft Stage 2 selection for baseline `4cd1d6c7f14e3ebacfd2dda219dda85967f64680`, supporting [the associated plan](../../runner/EXTENSION-CONSOLIDATION-PLAN.md) and [the disposition ledger](disposition-ledger.md). This file specifies future Stage 4 execution. No test execution is credited by this document. Root owns serialized build and test execution; do not run these concurrently in this checkout or unlink `tests/.checkout.lock`.

Catalog facts below were inspected from `tests/catalog.json`, not inferred from README labels. All 38 distinct `--case`/`--suite` selectors in the command blocks were validated by parsing that baseline catalog; no unknown selector was found. This validates registration only, not equipment or behavior. Before execution inspect every exact selection with `--list` against the implemented catalog, then execute the identical selectors with a fresh output directory. Suite selectors include opt-in cases. Unset `PYTHONOPTIMIZE`; use a normal signed candidate app that contains consolidation. Commands assume repository root and distribution candidate; set the same explicit `PW_APP_DIR` on each command if selecting another app.

## Coordinated contracts and readers

Required unchanged selection from Stage 4:

```sh
tests/run.sh --suite unit --suite integration --suite source_drift \
  --suite runner_abi_layout --suite runner_unit \
  --suite runner_c_worker_harness --suite failure_boundaries --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-contracts \
  tests/run.sh --suite unit --suite integration --suite source_drift \
  --suite runner_abi_layout --suite runner_unit \
  --suite runner_c_worker_harness --suite failure_boundaries
```

This includes new assertions inside `runner_unit/pwrunner_core_unit_executable`, `runner_c_worker_harness/actor_operations`, `/authority_binding`, `/terminal_erasure` and `failure_boundaries/admission`; keep these IDs when replacing their fixtures. It includes opt-in `runner_unit/actor_handoff_mutations`, `host_setup_oracle_sensitivity`, `exec_reader_mutations` and `reaped_ack_mutation` through the suite. Do not omit the known sensitivity case or call a retry its resolution.

Equipment union for this selection: signed `app`, matching `worker`, `cargo`, `swift`, `clang`, `meson`, and pytest where declared by individual cases. `runner_unit` base requires app/Swift/clang/Cargo; ABI base clang; unit Cargo; integration app/Cargo; source-drift has no base equipment but `runner_source_manifests_agree` requires Meson and build documentation reaches Swift discovery. Native socket/process controls may need unsandboxed execution even if catalog does not require an app. Missing equipment means failed/unrun accounting, not a new skip.

## Live authority, ordinary behavior and independent readers

```sh
tests/run.sh --case witness_contract/extensions \
  --case witness_contract/extension_directory \
  --case witness_contract/extension_boundaries \
  --case witness_contract/extension_combinations \
  --case witness_contract/extension_policy_qualification \
  --case witness_contract/extension_redelegation \
  --case witness_contract/actor_compositions \
  --case witness_contract/actor_timing_qualification \
  --case witness_contract/max_targets_reply_survives \
  --case witness_contract/dossier_witness \
  --case runner_outcome_bad_request/accepted_input_contract \
  --suite runner_validator_failure --suite blackbox_e2e --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-authority \
  tests/run.sh --case witness_contract/extensions \
  --case witness_contract/extension_directory \
  --case witness_contract/extension_boundaries \
  --case witness_contract/extension_combinations \
  --case witness_contract/extension_policy_qualification \
  --case witness_contract/extension_redelegation \
  --case witness_contract/actor_compositions \
  --case witness_contract/actor_timing_qualification \
  --case witness_contract/max_targets_reply_survives \
  --case witness_contract/dossier_witness \
  --case runner_outcome_bad_request/accepted_input_contract \
  --suite runner_validator_failure --suite blackbox_e2e
```

Catalog equipment: extension basic/directory/policy/re-delegation/compositions/timing cases override to `app`; boundaries/combinations/max-target require app/clang; dossier inherits app/clang. The CLI/direct-XPC shared request corpus case requires app. Validator suite app, with `transcript_controls` requiring no app. Blackbox suite app, `comparison_controls` no equipment, `native_comparison_controls` clang. This selection deliberately includes ordinary reader/validator checks extracted from declaration fixtures and independently owned blackbox rejection controls.

Retain baseline-before-consume, later-phase query/fresh-read separation, native release result and later fresh-access evidence in basic calibration. A successful complete calibration is required. Store re-delegation `principal.credited` and `first_break` separately: a case pass with `credited:false` is apparatus/contrast plus calibration evidence only. Source-only direct-body controls never receive dispatch credit. Finite timing case retains quarter-margin checks and identifies exhausted boundary before any allowance adjustment.

## Ordering and termination controls

Consolidation changes query eligibility and accepted gate behavior, so include the opt-in ordering mutation case rather than treating it as optional:

```sh
tests/run.sh --case witness_contract/order_barrier_mutations --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-ordering \
  tests/run.sh --case witness_contract/order_barrier_mutations
```

Catalog requires app/clang/Swift/identity/Meson. Fixture builds and mutations remain outside the inspected app. Require unmodified baselines plus named behavioral rejection of each successfully compiled mutation. The proposed termination gate's direct controls belong in the existing actor unit batch, actor handoff mutation family and public `witness_contract/extensions` case, selected above. Register no new case merely to give a test-group a public name. If a new public owner becomes necessary, update catalog, suite map, README and this selection before execution.

## Equipment selection, installation and signed inventory

Stage 3 proposal: move useful declaration BYOXPC workloads into `witness_contract/actors_byoxpc`, sharing one durable installation/session, then remove `witness_contract/extensions_byoxpc` catalog entry. At the Stage 2 baseline both entries exist; any baseline comparison that claims both workloads must list/select both. Post-consolidation candidate uses only the surviving owner below, which must contain successful mixed-equipment calibration, principal observation/contrasts, inherited restriction, provenance/readback and restoration assertions.

```sh
tests/run.sh --case witness_contract/actors_byoxpc \
  --case witness_contract/dossier_witness_byoxpc \
  --case runner_byoxpc/entitlement_readback \
  --case runner_byoxpc/entitlement_transfer \
  --case runner_byoxpc/runner_install \
  --case runner_byoxpc/registry_recovery \
  --case runner_byoxpc/reservation_controls \
  --case runner_byoxpc/retirement_observations \
  --case preflight/codesign.preflight \
  --case preflight/byoxpc_verification_controls \
  --case preflight/signed_artifact_controls \
  --case preflight/build_provenance_controls \
  --case preflight/native_source_controls \
  --case preflight/build_guard_controls \
  --case preflight/build_refusal_controls --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-equipment \
  tests/run.sh --case witness_contract/actors_byoxpc \
  --case witness_contract/dossier_witness_byoxpc \
  --case runner_byoxpc/entitlement_readback \
  --case runner_byoxpc/entitlement_transfer \
  --case runner_byoxpc/runner_install \
  --case runner_byoxpc/registry_recovery \
  --case runner_byoxpc/reservation_controls \
  --case runner_byoxpc/retirement_observations \
  --case preflight/codesign.preflight \
  --case preflight/byoxpc_verification_controls \
  --case preflight/signed_artifact_controls \
  --case preflight/build_provenance_controls \
  --case preflight/native_source_controls \
  --case preflight/build_guard_controls \
  --case preflight/build_refusal_controls
```

Equipment union: app, Developer ID `identity`, logged-in `gui`, Cargo/Meson/clang/Swift and pytest. Catalog `actors_byoxpc` currently requires app/identity/gui; migrated boundary workloads add clang, so update its requirements to app/identity/clang/gui when consolidation lands. Dossier BYOXPC requires app/identity/gui. Reservation controls additionally Swift/clang/Meson. Preflight signed artifacts need app/identity; guard/refusal require app/identity/Cargo/Meson/clang/Swift (refusal also pytest). Unified Logging and keychain/signing may require unsandboxed execution. Do not add unrelated Rosetta/toolchain-switch controls unless their source dependencies change; default preflight/build-entry/native-policy checks run in final battery, while the targeted guard/refusal selection above covers changed inventory/build flows.

The same selected cases must implement ledger P21/T21: service-local worker-equipment.json emission after worker signing and before the enclosing seal, BYOXPC source verification and post-sign rewrite/reseal, and authoritative host-own-service validation. Signed controls must reject stale hashes after re-signing, missing/duplicate roles, escaping/substituted paths, incompatible identity/protocol and nonempty unentitled read-back. Build call receipts and independent disk/signature reads establish ordering and bytes separately. Do not credit the app-level evidence manifest or cached registry as this new service inventory.

The coordinated runner core batch plus unit/rust.unit and blackbox_e2e/checker_controls must independently exercise all four live Security call failures, exit/deadline/ownership loss, actor/binding/read-back substitution and a runtime failure falsely presented as before-launch preparation_failure. Required live inspection runs while parked after setup and before any scheduled activation/query collection; failure cancels all activation while preserving actual setup/application and cleanup. Its OSStatus observations are not errno. Exact and over-bound XML/inventory/key/diagnostic tests remain independent of generated limit values, and maximal real replies remain separate from the constructed 8-MiB additional allowance.

The mixed-equipment control must fail when issuer and subject silently use the same entitled worker. Independently retain signature/entitlement readback, per-actor process/source hashes and native effects; these support different claims. Require missing-selected-equipment refusal without spawn and independent refusal of substituted actor equipment evidence. Inspect `runner list`/`runner reconcile` first and retain service name/scope/bundle path/pending-cleanup ownership through verified removal. No retained warning or `cleanup_retained:true` may be hidden by deleting staging.

## Independent native controls

```sh
tests/run.sh --case sandbox_extensions_native/feasibility \
  --case sandbox_extensions_native/directory --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-native \
  tests/run.sh --case sandbox_extensions_native/feasibility \
  --case sandbox_extensions_native/directory
```

Both opt-in cases require clang and identity. They do not launch PW or install a service; use the recorded identity/environment and preserve their native source snapshots/readbacks. They establish native lifecycle/authority/lifetime premises, not PW ordering, dispatch, actor equipment selection or transport. Root may cite completed Stage 1 executions only with exact source/equipment applicability; rerun if assumptions/dependencies change and again as required by the accepted design. This packet grants no execution credit from a run name alone.

## Final battery and accounting

Build normal signed candidate through `docs/BUILD.md` after production changes; a baseline app cannot verify candidate deletion. Serially execute:

```sh
tests/run.sh --list
PW_TEST_OUT_DIR=tests/out/runs/extension-consolidation-battery tests/run.sh
```

The no-selector command is the final default selection; `--all` or a union of selected suites is not a default battery. Record canonical IDs after dispatcher reconciliation, including shared validator aliases only once. Rebuild if app inputs change after a correction; rerun affected checks and re-establish final battery applicability using `tests/AGENTS.md`, not an arbitrary file allowlist. Source snapshots include scripts/helpers/fixtures even for app-independent cases.

Credit dimensions remain separate: source inspection; constructed encoder/reader controls; successfully compiled mutation rejection; live signed production observations; independent native observations. Required controls with missing equipment, sleep overlap, unsettled resources or failed harness capture remain uncredited. Keep failures and replacement reasons visible, including host-setup observer receipt failures. An unsandboxed retry may support an environmental explanation only when the same command/artifact passes; it supplies new observations without rewriting history.

The acceptance record must retain candidate app inventory/source identity, exact commands/configuration/catalog snapshot, raw requests/replies/native/file/process receipts and hashes of any copied relied-on evidence. Use normal retention allocation (current default battery plus one complementary pin); if more targeted runs are needed, preserve identified hashed copies under associated records before supported pruning. Copies preserve original run identities and do not transfer active cleanup ownership. No execution result may be credited solely because this selection lists it.
