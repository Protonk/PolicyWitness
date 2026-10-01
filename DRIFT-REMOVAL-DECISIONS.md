# Drift removal: decision log

Review material for the operator, kept beside `DRIFT-REMOVAL-PLAN.md` while the
plan runs. Not shipped documentation. Entries are dated; each judgment call
names the alternatives and the plan rule applied. On resumption after a context
break, read this file with the plan and the repository instructions.

## 2026-10-01 — I1 started

### Baseline and environment

- Plan inventory baseline `df333b4` is the last source commit before I1: the
  only later commits add plan documents and
  `tests/fixtures/comparison/baseline_response12/`. Plan line numbers were
  exact at I1 start.
- The shipped `dist/PolicyWitness.app` was built from `ff2b192` (v0.2.4,
  build 321). No file under `controller/`, `runner/`, `build.sh` or
  `docs/contract.json` changed between `ff2b192` and `df333b4`; only release
  tooling under `tests/lib/` and the `preflight` suite did. Pre-I1 captures of
  the three existing specimens therefore describe the current producer. App
  identity (hashes, build stamp) is in `pre-i1-captures/app_identity.txt`
  in the retained I1 receipts.
- Git policy applied throughout: commit on `main`, never push (local machine
  instruction, deliberately absent from repository text).
- Checkout lock `tests/.checkout.lock` held a stale PID at start; the lock is
  flock-based and process exit released it. Not unlinked, per `tests/README.md`.

### Judgment calls

- **`comparison_conditions` has no producer site.** The R1/R2 removal lists a
  reply-level `comparison_conditions` key. No Swift, Rust, Python or shell
  source emits or reads it; the only mention is
  `tests/fixtures/comparison/baseline_response12/README.md`, which already
  says no build emits it. Producer-side removal is a no-op; the consumer
  rejection in D3/I3 still applies. Classified as a missing symbol (plan
  preamble: record resolved file when a symbol is missing).
- **Shared Rust modules.** The plan asks for `resolve_imports`,
  `compute_closure_hash` and OS-facts collection extracted from
  `sbpl-check.rs` into shared modules. The controller crate has no `lib`
  target; the existing sharing convention is `#[path = "../x.rs"] mod x;`
  (used for `json_contract`, `log_capture`, `log_show`). Followed it:
  `controller/src/sbpl_imports.rs` (constants, `ImportRecord`,
  `resolve_import_path`, `resolve_imports`, `compute_closure_hash`,
  `sha256_hex`, and the import/closure unit tests moved with them) and
  `controller/src/host_facts.rs` (`sysctl_string`, cached
  `macos_build_version`). `sbpl_lex.rs` moved from `src/bin/` to `src/`
  because the import module depends on it. `main.rs` declares all three with
  `#[allow(dead_code)]` until I4's dossier reads them. Alternative rejected:
  a `lib.rs` crate restructure, which would change every `mod` declaration
  and the integration test for no I1 benefit.
- **`sw_vers` replacement.** `macos_build_version()` now reads
  `kern.osversion` through `sysctlbyname`, cached in a `OnceLock` as before.
  On this host `/usr/bin/sw_vers -buildVersion` and `kern.osversion` both
  return `23J220`.
- **Byte identity of `sbpl-check`.** Compared the shipped helper
  (`ff2b192`) with the rebuilt helper over 16 request inputs (the five
  specimens, resolved and unresolved imports, missing/supplied params, a
  compile error, bad format, missing source, oversized source, non-JSON) plus
  five argument-error invocations. Exit codes, stderr and every stdout were
  identical except the `build` stamp (the direct `cargo build` had no
  `build.sh` stamp environment) and `generated_at_unix_ms`. Report:
  `sbpl-check-identity/identity_report.txt` in the retained receipts.
- **`docs/limits.json` reference paths.** The three `helper_*` rows' `sources`
  now point at `controller/src/sbpl_imports.rs`; the `documented_helper_limits`
  value check stays in `sbpl-check.rs` (the helper remains the owner the
  `source_drift` owner set names); the `mod tests` path checks for depth and
  count follow their tests into `sbpl_imports.rs`. `docs/generate_limits.py`
  regenerated `docs/LIMITS.md`; the guide copy was unchanged. Values and
  descriptions are untouched in I1 (I4/I5 revise descriptions for the
  dossier).
- **Unit-test flake under contention.**
  `log_capture::tests::launch_exit_and_closed_pipe_hang_have_explicit_facts`
  failed once while `cargo test` ran concurrently with a release build of the
  helper (its 300 ms child deadline). It passed on three serial reruns, and the
  change set does not touch `log_capture.rs`. Treated as contention, not a
  finding; the pre-commit `cargo test` runs alone.
- **New specimens.** `tests/fixtures/pw_runner/specimen_exec_spawn.json`
  (`process-exec*` query and spawn of `/usr/bin/true`, matrix row S15 shape)
  and `specimen_sysctl_read.json` (`sysctl-read`/`sysctl_name` on
  `kern.osrelease`, row S10 shape). Both use `(allow default)` and only
  system paths so the fixtures stay environment-independent. Neither is
  registered in a suite; the integration suite's `cli_contract` does not glob
  the directory.
- **Baseline capture mode.** Each specimen is captured twice: with the
  default log capture and with `--no-log-capture`. The default form is the
  ordinary invocation and carries the log-capture objects the run-varying
  rule says not to blanket-remove; the no-log form gives a deterministic
  companion. Both are retained and both are diffed on the candidate.

### Documentation requirements captured before deletion (plan: Infrastructure ledger)

Verbatim or near-verbatim text that must survive the retirement of its
current home, with the destination the plan assigns.

1. **Seam case → matrix README.** From
   `drift_determination_via_validator_seam.sh`: the steered validator is
   input-steering through `_test_overrides.validator_executable_path`, not
   result-faking; the run is self-describing because `test_overrides` is
   echoed. From `check_comparison.py`'s docstring: "The transcript is not a
   native sandbox_check result. Expected distinctions below come from the
   submitted scopes and independent file/permission controls." Specimen B's
   transcript is stub output.
2. **DAC EACCES case → `runner_exec_dac` README (keep).** "An
   execute-permission failure is insufficient evidence of sandbox" attribution:
   a permission failure under an allow prediction does not establish sandbox
   attribution; "Neither that pairing nor EACCES establishes sandbox
   attribution"; "Policy interventions establish the test's expected
   observations on the supported system; they do not grant runtime attribution
   to an arbitrary permission failure."
3. **Unknown-service case → guide `lookup_failed` note (keep).** `kr=1102`
   (`BOOTSTRAP_UNKNOWN_SERVICE`) means the service is not registered; it is not
   a permission result. The same note's `kr=1100` sentence currently calls it
   "the sandbox-deny signal"; D4 rule 3 rewords it to a permission result that
   does not attribute by itself.
4. **Checker controls → rebuilt controls' README.** From
   `tests/suites/blackbox_e2e/README.md`: controls run without the app, before
   the live cases; controlled changes must fail; combined failures report each
   independent problem; controls exercise the checker CLI without importing its
   implementation or any production code.
5. **Disposition fixtures → `tests/fixtures/disposition/README.md`.** Label
   captured (`a1_known_loss.json`, real envelope, response 9) and generated
   (`a1_expected.json`, expected-output fixture built before the app produced
   the record) separately; the captured reply becomes an unsupported-version
   rejection control under D5.
6. **Transport test.** Use a current-version reply with unfamiliar strings and
   require unchanged forwarding (replaces the response 4–8 loop in
   `runner_client.rs`).
7. **Production coverage.** Planner coverage stays with
   `PredictionUnavailableTests.predictionUnavailableQueryPlanning` and the
   `source_drift` guide/set check; source-set coverage with `source_drift`'s
   build-versus-tree check; C failure coverage with `runner_c_worker_harness`
   and the real worker/validator failure drivers. State these in the
   runner-unit and failure-contract descriptions when the helper-only tests go.

### Increment progress

- Completed: pre-I1 captures (three specimens, two modes), shipped helper
  corpus and binary copy, pre-removal `nm -u` receipt
  (`_sandbox_check` undefined in the shipped `PWRunner`), shared Rust modules,
  helper rewired with byte-identical output, limits manifest/docs regenerated,
  two new specimens with pre-I1 captures.
- Remaining in I1: matrix fixture and README, `tests/fixtures/README.md`
  entry, commit, signed build, five response 12 baseline captures validated
  by the response 12 consumer, post-build `nm -u` receipt, default battery,
  attach receipts under the checkout lock, `tests/RETAINED.json` entry,
  closing entry here.
