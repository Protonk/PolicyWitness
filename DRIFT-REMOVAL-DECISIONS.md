# Drift removal: decision log

Review material for the operator, kept after `DRIFT-REMOVAL-PLAN.md` was deleted at closeout, while the
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

### Matrix fixture

- `tests/fixtures/comparison/matrix.json` carries 33 rows (S01–S25 without
  S04, B1–B7, C1, T). Every row was cross-checked against a response 12 reply
  on disk: the five comparison values, the limitations pruned to the D1
  vocabulary and the query column agreed for all 33 (`matrix-review/` in the
  retained receipts). Row inputs are the matrix's own choices, reviewed
  against D1; where they differ from the retained control that supplied the
  response 12 match (service name, child exit code 1 instead of 3, read
  instead of write, stub error text) the comparison shape is identical.
- C1's raw shape came from a compile-failure probe against the shipped app
  (`pre-i1-captures/c1_compile_failure.nolog.json`): `runner_failed`, exit 1,
  validator not invoked, worker slot incomplete with lifecycle `not_reached`.
  The retained `pre_apply_failure_reports_no_policy_verdict` case uses a
  pre-ready hang (`runner_timeout`), not a compile failure, so it is not C1's
  live owner; `comparison_matrix` will own C1.
- Two row facts were verified against retained output before writing them:
  the native query accepts `process-exec-interpreter` (allow under allow
  default, relation `different`, `query_first`), and a validator diagnostic
  record yields `result_source: validator`, `outcome: error`, no
  `missing_reason`, null `native_rc` and `order: unestablished` (B4).
- The assert convention says null means absent or JSON null because the Swift
  encoder omits nil optionals (`missing_reason` is absent, not null, on a
  validator error record).

### I1 completed (2026-10-01)

- Source commit `e010509`. Signed build from that commit
  (`build/build-e010509.log`); the app inventory recorded by the run is
  unchanged across the battery.
- Default battery `tests/out/runs/drift-i1-baseline-01`, run ID
  `20261001T232648Z_b2156eef`: 166 selected, 166 completed, 0 skipped, 0
  unrun, no harness errors, `ok: true`. Registered in `tests/RETAINED.json`
  with source `e010509` and the run-relative `artifact-integrity/before.json`.
- Receipts attached under the checkout lock after verifying the run ID, at
  `supplemental/drift-i1/` inside that run: `pre-i1-captures/` (the three
  existing specimens, two modes, against the shipped `ff2b192` app; the two
  new specimens; the compile-failure probe), `response12-baseline/` (the five
  specimens, two modes, against the I1 build; `app_identity.txt`;
  `validation/consumer_response12.json` with zero shape, current-build or
  ordering errors for all ten captures; `nm-receipt/` for the I1 build),
  `sbpl-check-identity/` (corpus, shipped helper copy, old/new outputs,
  `identity_report.txt`), `nm-receipt/` (shipped `PWRunner`: `_sandbox_check`
  undefined), `matrix-review/`, `build/` and `console/`.
- Both `nm -u` receipts (shipped `ff2b192` and the I1 build) report exactly
  one undefined `_sandbox_*` symbol, `_sandbox_check`, so the planned binary
  check fails on the pre-removal service and will have a before/after pair.
- I1 exit conditions: shared Rust modules exist with byte-identical helper
  output (16-input corpus; only the build stamp and timestamp differ); the two
  specimens are added; the five response 12 captures and the `nm -u` receipt
  are retained and registered; the matrix fixture is written against D1; the
  default battery is green. Nothing was deleted; no active contract check was
  retired.
- Observation for later increments: the dispatcher's own `PYTHONOPTIMIZE`
  guard and the `cargo fmt --check` case both passed with the new Rust files;
  the first `cargo test` flake (`launch_exit_and_closed_pipe_hang_have_explicit_facts`)
  did not recur in the battery's `unit/rust.unit` case.

### Next: I2–I4 on one integrated candidate

Order chosen (dependencies): Swift producer and unit tests with the response
13 bump; then the controller (dossier, delivery, version gates, manifest
selection) with the envelope 5 bump; then the Python equipment, checker
controls, new live cases and registries; then build, `runner_unit`,
`source_drift`, `unit`, the default battery, repair, `--all` with
`order_barrier_mutations`; then I5 documentation. Each landing is a commit on
`main`; the response and envelope numbers move in the same commit as the
producer that emits the new shape. Drafts written during the I1 battery
(outside the tree) are the consumer rewrite, the Swift matrix reader, the
live matrix checker and the dossier module.

## 2026-10-01 — I2–I4 landed on one integrated candidate

Source snapshot: the working tree on `main` after `4d3fdf4`, committed as the
landing commit named under Closeout. `docs/contract.json` is at response 13 and
envelope 5 with every generated copy regenerated. The signed build, `cargo
test`, `runner_unit`, `source_drift` and the witness, dossier and barrier
cases are green; the battery evidence is listed below.

### Judgment calls

- **Dispatcher fixture host is a compiled Mach-O.** The artifact inspector's
  `nm -u` host-invariance receipt cannot read a shell-script stub, so
  `tests/fixtures/dispatcher/artifacts.py` compiles a one-line C host for the
  fixture bundle and `dispatcher/artifact_controls` gained the
  `host_imports_sandbox` control: an intact, sealed bundle whose host links
  libsandbox and calls `sandbox_check` must fail with `host_invariance` and
  `sandbox_symbols == ['_sandbox_check']`; the valid bundle's receipt must be
  `returncode 0` with no symbols. Alternative rejected: tolerating an
  unreadable host in the inspector, which would let a damaged host pass.
- **Matrix helpers are compiled, not copied.** A copy of `/usr/bin/false` is
  killed at launch on this host (exit 137) while a copy of `/usr/bin/true`
  runs; the fixture's `helper_true`, `helper_false` and `helper_locked` are
  now compiled (`int main(void) { return N; }`), the `copy_of` state is gone
  and the row/control text says so. `check_dossier.py` copies the
  `/usr/bin/true` bytes with `copyfile` because `copy2` fails on the system
  file's flags. Recorded as host behaviour; not investigated further.
- **S24's effect is one byte, not zero.** The worker's `open_write` writes
  one byte after `O_TRUNC`; the fixture said "zero bytes". The row, its
  control text and the live check's effect parser (`present, N bytes`) were
  corrected. No producer change.
- **Bare `process-exec` beside a spawn is `operation_relation: different`.**
  The producer's rule (`matched` when the submitted operation is the mapped
  one, `different` otherwise, `unresolved` only for compound create and
  unsupported attempts) predates the plan and D1 keeps the relations
  unchanged; the C-worker case's `unresolved` expectation was corrected and
  the guide's `unsupported_operation` note states the rule.
- **A policy without `sbpl_source` is `bad_policy`.** The request is
  delivered and the runner's structural check refuses it; the dossier witness
  had expected `bad_request`. D2 fixes only the dossier state
  (`not_applicable`), so the runner-owned outcome was recorded as observed
  and the diagnostic must name `sbpl_source`.
- **Exact-version mirrors.** `DispositionResolverTests` dropped its
  `response_with_disposition == 10` and `responseSchema >= 10` checks (the
  Python contract module no longer exports introduction versions); the three
  filter suites dropped `--minimum-schema-version 8` (the rewritten adapter
  accepts only the current versions); `order_barrier_mutations` no longer
  compiles `PWSandboxCheckShim`; the smoke, `testlib.sh`, release-acceptance
  and menagerie readers of `runner_kind` moved to
  `data.specimen.runner_provenance`.
- **Integration tests follow the D2 shapes.** A refusal has
  `data.runner_client: null` (no `(runner not invoked)` placeholder) and the
  dossier's `failed` augmentation record with `imports.failure:
  augmentation_failed`; disabled capture has a null capture with
  `correlation_status: not_attempted`; applied and absent augments are read
  from `data.specimen.policy.augmentation`; an invalid `--log-timeout-ms`
  prints the uniform envelope with null execution records and the dossier.
- **Status-word diagnostic.** The classifier's diagnostic for a worker that
  published only the status word now reads "published a
  preparation/application failure through the status word (status=-1;
  apply_errno=N)"; the word "legacy" was removed from the runner's
  diagnostics, comments, test labels and contributor text (the `.abi6`
  ordering control is `abi6_worker`). `HostOutcomeClassifierTests` pins the
  new text.
- **Pre-existing warning left alone.** `log_capture::capture_reserving` is
  unused in the `policy-witness` binary (the observer binary and the tests
  use it); the module is shared through `#[path]` and unchanged by this work.

### Battery evidence (all under `tests/out/runs/`)

- `drift-i4-default-01`: the first default battery on the candidate, 12
  failures, every one repaired above; kept unregistered as repair evidence.
- `drift-i4-repair-live-01`, `-02`, `-03`: targeted reruns; `-03` is the
  `witness_contract` suite green (36/36 including `comparison_matrix` with 32
  rows, `dossier_witness` with 7 examples and the opt-in
  `order_barrier_mutations`); `-02` is `integration` green.
- `drift-i4-repair-sd-01`, `drift-i5-sd-01`, `drift-i5-sd-02`: `source_drift`
  reruns during the documentation pass; the last is green on the final text.
- Receipts for every D1 row are the `comparison_matrix` artifacts
  (`matrix-summary.json`, three raw envelopes, `direct-controls.json`) and,
  for T, `worker_attempt_in_flight_at_deadline`; every D2 failure-table shape
  has its receipt under `dossier_witness` (`controller_refusals`, `refused`,
  `no-source`, `executable_overrides`).

## 2026-10-01 — I5 documentation and R10

- Order followed: `docs/QUESTIONS.md`, `generate_limits.py` (no
  `limits.json` description needed a change; the generator refused the
  guide's `#reading-a-comparison-record` link until that section existed, and
  `contract_versions`' stale-copy control failed through the same link), the
  guide, README, `docs/CONTRACT.md` and `AGENTS.md`, the controller and
  runner READMEs, `runner/AGENTS.md`, `tests/README.md`, `tests/COVERAGE.md`,
  the failure contract (its final chapter replaced; the scenario table is
  generated from `tests/fixtures/comparison/matrix.json`), the suite and
  fixture READMEs, catalog descriptions, `DRIFT-REMOVAL-CANDIDATES.md` and
  `FIVE-FOLLIES.md` status, then the plan's deletion.
- Reviewer step (Method 6): four fresh-context sub-agents reviewed the
  guide; README, CONTRACT and AGENTS; the controller and runner READMEs with
  `runner/AGENTS.md`; and the failure contract with the tests README and
  COVERAGE. Fixes applied from the first two reports: "Channel A" and "rather
  than by a label" wording, the exec stream-field contradiction, the
  reply/envelope distinction in README and AGENTS, and a definition of
  `query_first` in README. Findings not acted on, with reasons: regression
  guards that name rejected request fields (`instrumentation`,
  `path_membership`, `runner.mode=debuggable`) describe current rejections;
  dated filter-ID verifications are the record `source_drift` parses; test
  suite names and `_test_overrides` are project vocabulary outside this
  change. The suite and fixture READMEs had a dedicated document-only pass
  without a separate reviewer (limitation recorded).
- No bridge sentences were proposed; every historical clause was deleted
  rather than bridged.
- R10 remaining matches, by meaning: (1) `verdict` describing the validator's
  `sandbox_check` answer in validator, batch-mode and classifier material is a
  current descriptive use; (2) `drift` in `source_drift`, `runner_abi_layout`,
  `artifact.py` and `runner_manager.rs` means source-set, layout, inventory
  or alias drift, an unrelated use; (3) `legacy` in `runner_select.rs` and
  `runner_manager.rs` names accepted older request and registry spellings
  unrelated to the comparison record; (4) removed-key rejections in
  `consumer.py`, the checker controls, `EnvelopeInvariantTests`,
  `ContractVersionTests` and the failure contract's invariants name the keys
  they reject; (5) `tests/fixtures/comparison/baseline_response12/`,
  `a1_known_loss.json` and `records/` are immutable evidence; (6)
  `app_bundle_id`, `app_binary_rel_path` and `app_entitlements` remain
  manifest fields written by `build-evidence.py` and read by the artifact
  inspection, not by the controller; (7) `macos_build_version` is the
  `sbpl-check` helper's own output field, now described as `kern.osversion`;
  (8) the `_malformed_prediction_and_missing_alias` isolation control was
  renamed `_missing_errno` to say what it mutates.
- `baseline_response12/plan_matrix.md` carries the plan's scenario table as
  of commit 7765be8 so that `match_live.py` and `match_retained.py` still
  parse after the plan's deletion; `match_live.py` reproduces
  `live_row_match.txt` byte for byte.
