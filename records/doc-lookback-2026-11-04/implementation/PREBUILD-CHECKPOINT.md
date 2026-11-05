# Sleep checkpoint — prepared, before build/tests

User requested this exact pause. I1–I3 source/test changes are prepared and reviewed; all three implementation agents are finished. No build, compiler, test, formatter/check, dispatcher listing, native trial or external-runner action has started. Resume requires the user's return from this pause. Nothing from this session needs the machine to remain awake.

Root performed source/diff review and `git diff --check` only, plus the required write-mode generator `tests/lib/python.sh docs/generate_worker_identity.py`. That generator updated three copies to `c1f66cc04bf60846bcddcee5d765e965d75c1e6a8d682d116f14439dc9b93bf7`. Generator output is source preparation, not build or behavioral test evidence. No guide/ARCHITECTURE/WORKER/LIMITS edits have begun; only the capture suite's local assertion description was updated.

## Reviewed changes

- I1: `ActorPlan.swift` preserves actor ownership in `admission_failure.field` as `actors.<index>.sandbox.policy.value`; `CWorkerRequestPlanning.swift` maps it to the exact actor policy parameter path. Legacy value paths, key withholding, parameter count distinction and admission order remain. Existing bounded path construction still withholds the whole path when a component exceeds 63 UTF-8 bytes, independently of the 127-byte admission key echo. Existing RequestContractTests adds boundary/precedence/legacy controls. Six authored corpus cases flow through the existing Swift and public CLI/direct-XPC loops, which independently inspect file creation/absence and empty refusal evidence.
- I2: native `capture.c` now supplies an independently sized readable 1 MiB payload, verifies status/length/full content/source-derived checksum and guard byte, and uses readable cap+1 input for refusal/no-copy assertions. Production capture logic is unchanged. This constructed object tests native memory capture, not compiling/applying a 1 MiB real policy or qualifying a new OS compiler layout.
- I3: `run_flow.rs` adds one private compiler-invocation dependency bound to the same production function. One six-scenario orchestration control checks independent resolved policies, declaration order around an unapplied actor, exact held whole/per-actor inputs after the request file changes, associated helper results, preserved client/host evidence, no replay and no helper invocation for ineligible captures. It does not call a native compiler or establish host admission.
- Generated identity only: `pw_probe_runner_abi.h`, `CWorker.swift`, `tests/lib/contract.py`. No layout change or new source target. No wire version bump: I1 repairs existing location semantics; I2/I3 add coverage/seams without changing record meanings.

Root read all three final diffs and reports. Reviewed points include safe key as one path component (dotted names), actor parameter-count path remaining distinct, omitted unsafe keys, independent capture byte/extent expectations, fresh receipts, exact fallback result association and default dependency binding. Compilation, Rust formatting and all runtime assertions remain unverified. In particular, the live exact multibyte parameter case must establish native acceptance rather than have it inferred from source admission.

The final tracked-file patch and hashes are in inert sibling paths `prebuild.patch` and `prebuild-state.json`; base HEAD is `ea64218be2549fd034096f53ac23d79afac711ae`. No changes were staged or committed. Existing distribution and retained evidence were untouched. Their old identity/artifact cannot be used as execution evidence for this patch.

## Pending sequence after resume

First inspect status and compare the saved source hashes; account for any edits made while paused. The prepared sources require a new matching signed app. Existing provenance records the signing identity below; its present keychain availability has not been probed. The build owns cache/toolchain compatibility and signature checks. Use documented sandbox retry handling on a diagnosed refusal, preserving the artifact under investigation.

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

Then inspect and run this coordinated selection through `tests/run.sh`, serialized in the checkout with a fresh managed output directory. The full five suites are required by `tests/AGENTS.md` for admission changes; they also contain I2/I3's cases, avoiding repeated execution. The two additional cases supply public exact-refusal/no-effect observations and normal actor behavior. Static catalog inspection counted 83 selected cases before dependency expansion; suite selection includes its opt-in members. No dispatcher planning has run yet, so its actual plan/equipment result remains pending.

```sh
PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-01 tests/run.sh \
  --suite failure_boundaries \
  --suite runner_unit \
  --suite runner_abi_layout \
  --suite runner_c_worker_harness \
  --suite unit \
  --case runner_outcome_bad_request/accepted_input_contract \
  --case witness_contract/actor_compositions
```

After resume, use the identical selection with `--list` first to inspect exact equipment and dependencies. Ensure `PYTHONOPTIMIZE` is unset and let the dispatcher own/create output; choose another fresh name if the suggested path exists. App/worker cases require an unsandboxed invocation per repository guidance; other selected equipment includes Swift, clang, Cargo and Meson. No BYOXPC installation is selected. Preserve any failure and diagnose before changing artifacts. Do not unlink locks or use direct case scripts. No worker wait, release-store or eligibility change was made, so the order-barrier mutation rerun is not triggered by this patch.

A passing run can then support I1–I3 acceptance. Failed assertions or a broader contract issue require a concrete review before expansion. The next planned work is two documentation owners (ARCHITECTURE/WORKER/input and LIMITS/input), coordinated guide regeneration, mechanical checks and rendered artifact review. Update controller README's dependency inventory for the new helper seam. The two newly surfaced request-path retention bounds need inventory/value/coverage treatment there; existing guide says paths are bounded but does not give those numbers. Do not claim exact-size native capture success before its test executes.

Root READER-OUTFLOW-PLAN.md remains the single decision plan. No work is deferred out of this review. The eventual six fresh paired-reader roles have not been launched.
