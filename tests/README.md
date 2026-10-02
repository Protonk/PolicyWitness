# `tests/` (test runner + suites)

This directory contains the repository test harness. The test suite is organized to answer three questions:

1. Does the built `dist/PolicyWitness.app` basically work end-to-end?
2. Did we break a contract (CLI shape, evidence artifacts, JSON output schema)?
3. Do `sandbox_check` verdicts stay consistent with kernel-observed attempt outcomes?

The harness is machine-readable: every test writes structured JSONL events and a per-run summary under `tests/out/`.

Related docs:

- CLI contract: `controller/README.md`
- Runner architecture: `runner/README.md`
- Signing/build: [docs/SIGNING.md](../docs/SIGNING.md)
- Limits inventory and checks: [docs/LIMITS.md](../docs/LIMITS.md)
- Outcome coverage matrices: `tests/COVERAGE.md`
- Fixtures catalog: `tests/fixtures/README.md`
- Opt-in registry: `tests/OPT_IN_TESTS.md`

Consumer evidence tests follow the
[comparison record ownership table](FAILURE-PROPAGATION-CONTRACT.md#comparison-record).
`tests/lib/consumer.py` validates one envelope and selects steps by field
without consulting policies, native errno rules or the runner classifier.
Recovered spawn-failure records retain their numeric codes, paths and
diagnostic text. Explicit evidence-loss replies omit that record along with
steps and subprocesses. Controlled
scenario expectations stay in the CLI/witness cases; Swift tests enforce
encoding and absence, and Rust tests enforce receiver/correlation preservation.
Shared blackbox checks enforce universal version/shape guarantees. The blackbox
checker controls retain rejected meaning-loss fixtures beside passing controls;
no acceptance document or generated test output is required to run them.

## How to run

Build first (signed pipeline):

```sh
make build
```

Then run tests:

```sh
make test
# or:
./tests/run.sh
./tests/run.sh --suite preflight
./tests/run.sh --suite unit
./tests/run.sh --suite integration
./tests/run.sh --suite runner_byoxpc
./tests/run.sh --suite sbpl_allowdeny_consistency
./tests/run.sh --all --list
./tests/run.sh --case blackbox_menagerie/validation_controls
```

`tests/run.sh` is the public selection and reporting interface. With no selectors
it runs the default battery. `--all` selects every registered case, including
opt-ins. Repeated `--suite NAME` and `--case SUITE/CASE` selectors form a union;
order and repetitions do not change the work. A suite selects all its members,
including any opt-in members. Case IDs are exact harness identifiers, not patterns. Rust and Swift unit
methods remain inside their respective batch cases.

`--list` prints the selected plan as JSON, including descriptions, default
membership, prerequisites, runner contexts, dependencies, and configuration.
`selection.suites` records the caller's suite selectors; `containing_suites`
maps selected cases to every suite containing them. Membership does not imply
that the caller selected that entire suite.
`--all --list` discovers the complete catalog. Help, inspection, invalid arguments,
invalid configuration, and missing entrypoint scripts leave existing evidence
untouched. `--describe` is not supported.

The catalog is `tests/catalog.json`. A case has one canonical ID; suites may
include the same ID, so shared validator-failure cases execute once even when
both suites are selected. BYOXPC cases have distinct IDs and runner contexts.
Selecting a BYOXPC specimen also selects its installation dependency, visible in
`--list`. Independent cases continue after failures. Required equipment missing
at execution is a failed run with an explicit unrun case, never an implicit skip.
For ordinary cases, Ctrl-C during command execution stops the active command's
process group and cancels queued work. Completed and partial evidence survives;
the failed summary accounts for unfinished selections with an interruption reason.

When a selection requires the app or embedded worker, the dispatcher first
requires the complete bundle layout, valid local codesign signatures, and
matching embedded manifest hashes. Invalid artifacts block those cases; offline
cases can still run. A shared read-only inspector also backs `preflight`.
The dispatcher inventories the selected app before testing and again during
finalization, including after case failures or Ctrl-C. Added, removed, or changed
files, modes, directories, and symlink targets fail the run with a retained diff.
Inspection never repairs the app. Rebuild through `build.sh` to replace a stale
artifact; regenerating evidence over a mutated app would hide the defect.
These checks do not certify notarization and cannot detect a transient mutation
restored before the final inventory. Direct suite scripts do not have this guard.

Opt-in cases are documented in `tests/OPT_IN_TESTS.md`; use an exact case, an
owning suite, `--suite opt_in`, or `--all` to select them. Direct suite scripts
remain developer entrypoints, but do not provide the public command's planning,
configuration validation, or completion guarantees.

Release ZIP acceptance is a separate explicit command:
`bash tests/accept-release.sh dist/PolicyWitness.zip`. It inspects a temporary
extraction, checks the staple and Gatekeeper assessment, runs the existing allow
and deny contracts through the extracted controller, and records the ZIP hash
and before/after integrity. It never builds or signs. `make release` runs it as
part of the notarization chain, then runs the default battery against the final
app and archives the release; `make publish` publishes an archived release. See
[docs/SIGNING.md](../docs/SIGNING.md) for the complete release procedure and the
handling of delayed or uncertain Apple replies.

## Reusing verification results

For each credited case, record its canonical ID, command/configuration, source
snapshot and applicable build or equipment. Trace the command's scripts, shared
helpers and fixtures conservatively, then compare their file snapshots with the
accepted implementation. A case not requiring the app can still depend on changed
test code; app independence alone does not justify reusing its result.

Rerun a case when a dependency changed or applicability is uncertain. If an
earlier result is retained despite a changed file, identify the exact delta,
explain why the executed path and inputs are unaffected, and label this as a
reviewed exception. Hash checks establish file identity; they do not establish
complete dependency coverage or prove program reachability. An allowlist of
changed files is likewise a review aid, not proof that every retained case is
unaffected. Acceptance summaries must distinguish mechanically checked facts
from these applicability judgments.

Keep original runs and snapshots intact. Record corrections and replacement
credits explicitly, including the reason for each rerun; do not turn an earlier
failure into a passing historical run. This procedure does not require a generic
dependency-analysis framework.

## Configuration

- `PW_APP_DIR`: app bundle to test; defaults to `dist/PolicyWitness.app`.
- `PW_BIN` and `PW_BIN_PATH`: compatibility aliases for the controller inside
  that bundle. Either can infer the app when `PW_APP_DIR` is absent. All supplied
  paths must agree after resolution; a standalone controller is rejected because
  tests also exercise its bundled helpers. Rust and shell tests receive the same
  resolved controller and app paths. Whole-app symlinks are supported; a
  controller symlink must stay inside its named bundle, including when a
  controller alias supplies the app path implicitly.
- `PW_TEST_OUT_DIR`: output directory, default `tests/out/runs/default`. Named
  disposable runs use `tests/out/runs/<name>`. Explicit paths must stay within
  `tests/out`, without symlink redirects or path escapes, and cannot overlap the
  tested app. Execution replaces only eligible output; inspection is read-only.
- `PW_TEST_RUN_ID`: evidence label; unset or empty generates one. It does not
  create a separate output directory. Labels start with a letter/digit and use
  at most 128 letters, digits, dots, underscores, or hyphens, because specimen
  fixtures embed them in paths and SBPL literals.
- `PW_TEST_QUIET=1`: suppress routine case messages. `0`, empty, or unset retains
  them. Selection, errors, and the summary remain visible.
- `PW_BYOXPC_IDENTITY`, then `IDENTITY`: signing identity override for signing
  tests; otherwise resolve an available Developer ID matching the app's team.

Relative paths resolve from the repository root regardless of the caller's
working directory. The effective paths are recorded in `plan.json` and
`run.json`. Runner-mode/service overrides, suite aliases, case selection state,
and event paths (`PW_TEST_RUNNER_*`, `PW_TEST_SUITE_OVERRIDE`, `PW_TEST_CASES`,
`PW_TEST_EVENTS`) belong to child execution and are rejected as public settings.
Select BYOXPC cases through the catalog instead.

## Retention, ownership and execution locking

`tests/RETAINED.json` is the committed retention index, outside disposable output.
It has `schema_version: 1` and a `runs` array. Each entry records `path` relative
to `tests/out`, `run_id`, a nonempty `reason`, `source` (the full tested commit
hash, or null when unknown), and `app_inventory` (a run-relative evidence path,
or null when unavailable). Paths stay protected even when their directories are
absent locally. A missing, malformed or unreadable index prevents replacement.
Targets equal to, containing or inside a retained path are refused before any
output is changed. Symlink redirects and path escapes are rejected.

The dispatcher writes `owner.json` first, with its run ID, resolved output path
and start time. Only a matching, valid terminal `run.json` establishes completed
output. Failed cases and ordinary Ctrl-C cancellation still produce terminal
records and are disposable when unretained. A missing terminal record leaves an
interrupted run; malformed or inconsistent evidence leaves ambiguous output.
Nonempty output without ownership is unmanaged. Replacement refuses all three;
inspect the evidence and choose a fresh output directory or use the explicit
unfinished-prune command below. Placement under
`runs/` alone does not establish ownership. Planning refusals exit 2.

After read-only planning, execution takes an OS-held advisory lock on
`tests/.checkout.lock`, rechecks retention and output eligibility, and holds the
lock through finalization. The file stays in place between operations. Never
unlink it: the held lock belongs to its inode, so a replacement file would let
later operations bypass the holder. PID and start information is diagnostic;
process exit releases the lock, while run records determine completion.

One checkout runs one execution at a time. Competing execution gets a
checkout-busy error even with a different output path. A smoke run must wait
for a long `--all` to finish before retrying; parallel work needs a second
worktree. Help and `--list` remain available while execution holds the lock.

Direct shell entrypoints default to `tests/out/runs/direct`; they do not replace
output or provide dispatcher ownership/completion guarantees. Release acceptance
keeps unique directories under `tests/out/release-acceptance/run-*`; its nested
`tests` output passes the same dispatcher checks. Passing acceptance prints a
suggested index entry. Record source provenance only when established; the
commit that adds an index entry is not the source of an earlier build.

For a console transcript, capture to a temporary file outside `tests/out/runs/`
and attach it to the completed run under the checkout lock after verifying the
run ID. Do not create or redirect into the selected output directory before
startup: a preexisting transcript makes fresh output unmanaged, and replacement
of an eligible old run would unlink an already-open transcript. If execution
never creates owned output, keep the temporary transcript for diagnosis.

## Pruning disposable output

```sh
tests/run.sh --prune
tests/run.sh --prune --apply
# After inspecting an interrupted or ambiguous managed run:
tests/run.sh --prune --apply --unfinished <name>
make clean
```

Preview prints a read-only JSON snapshot with `delete`, `keep: retained`,
`keep: interrupted`, `keep: ambiguous`, and `keep: unmanaged` dispositions.
It does not create a lock file or hold the checkout lock while classifying. If
execution holds the lock, `checkout_busy` is true and runs without a terminal
record are labeled `keep: active or interrupted`.

Preview briefly takes and releases the same nonblocking lock to observe
contention. An execution starting during that probe can receive checkout-busy
and exit 2; retry it after preview finishes. This safe refusal is an accepted
tradeoff of the probe. The reported busy state is a snapshot and can change
before classification or a later apply operation.

Apply takes the checkout lock and re-evaluates eligibility. It removes only
completed, unretained managed directories directly under `tests/out/runs/`.
Failed cases and terminal Ctrl-C runs remain eligible; crashed runs lacking a
terminal record remain available for inspection. `--unfinished <name>` explicitly
removes one interrupted or ambiguous run with valid ownership after the same
retained-overlap checks. It rejects completed, retained, unmanaged, redirected,
or missing targets. This is the supported way to deliberately remove unfinished
output; it preserves serialization with other mutating operations.

Apply reports actual `removed` paths and `failures`; a failed deletion exits 1
and reports the surviving path. Invalid requests, invalid indexes and checkout
contention exit 2. `--apply` requires `--prune`, `--unfinished` also requires
`--apply`, and pruning cannot be combined with selection or `--list`.

Standalone files anywhere in `tests/out`, including inventory JSON files, are
preserved. Output outside `runs/`, including release acceptance, is reported as
unmanaged and kept. Symlink redirects are never traversed or deleted. `make
clean` delegates to `tests/run.sh --prune --apply` and follows exactly these
rules; it preserves release acceptance, retained and unfinished evidence.

## Tiers

- **Baseline**: ordinary default cases on supported hosts, including offline
  checker controls and live smoke, black-box, and witness contracts.
- **Opt-in**: resource-sensitive signing/launchd work or implementation mutation
  controls. Some otherwise Baseline suites also own opt-in cases; `--list` gives
  each case's exact default membership and requirements.

## Suite coverage

This is the canonical map of what each suite covers, what you can claim when it
passes, and when it legitimately skips. For exact invariants and fixtures, see
the per-suite README files under `tests/suites/<suite>/`. For the per-outcome
coverage matrices (which suite exercises each `NormalizedOutcome` /
`AttemptOutcome` value), see `tests/COVERAGE.md`.

A blank **Skips when** cell means the suite has no expected skips: missing
prerequisites should fail, not skip.

| Suite | Tier | Primary claim | Requires | Skips when | Notes / artifacts |
| --- | --- | --- | --- | --- | --- |
| `preflight` | Baseline + opt-in signing controls | Enforce bundle layout, signatures, and manifest hashes; release continuation, real deadline, and offline tag/archive/publish controls | Built app for inspection; signing controls also need matching Developer ID; release controls need no app, with macOS socket/process observation for deadlines | — | Read-only inspection; signing controls mutate disposable copies only. Select `preflight/codesign.preflight` for inspection alone. |
| `source_drift` | Baseline | The runner source manifest is consistent between the on-disk `runner/Sources/` tree and `build.sh`'s `XPC_RUNNER_*` set. (The SwiftPM package auto-discovers by convention, so its set equals disk; build.sh vs the tree is the comparison that can ship a broken `PWRunner.xpc`.) Catches a compiled file added to one but not the other before the drift ships. Also checks the limits inventory, copied user guide, standalone staging, stale-document build refusal, documentation links (including both AGENTS files), the `_test_overrides` key table in `runner/README.md` against `PWRunnerTestOverrides`, the shared paragraph of the sandboxed-harness note across its three copies, the `policy-witness` usage lines in `cli.rs` against the README's CLI surface block, the host invariance rule (no libsandbox binding, call or dynamic lookup under `runner/Sources/`, with controls), and the contract version manifest (`docs/contract.json`) against every generated copy in code and documents. | Python 3 | — | `tests/out/runs/default/suites/source_drift/.../check.log` |
| `shell_helpers` | Baseline | Case helpers retain arguments, logs and identity; failures stop case stages. Result helpers preserve matching terminal evidence and logging/exit behavior. Wrapper groups preserve child order, streams, and failure status while continuing later children | Bash + Python 3; macOS codesign for mutation prerequisite control | — | Independent receipts and subprocess observations; covers case/equipment failures, separate build logs, quiet output, result serialization, wrapper phase gates/cleanup, and explicit skips. No built app or toolchain; mutation prerequisites inspect an unsigned fixture and forbid later builds; BYOXPC ownership controls use fake OS/CLI commands; wrapper and worker-setup controls use simulated children. |
| `dispatcher` | Baseline | Requested suite execution, case reports, and lifecycle events determine the same shell exit status and `run.json.ok` | Bash + Python 3; cancellation also needs macOS local sockets and process observation | — | Separate reconciliation, accounting, cancellation, and selection controls. Includes kernel-observed cleanup of an interrupted ordinary case and its helper, plus executable receipts from two usable stub apps. No app or compiler. |
| `unit` | Baseline | Controller logic is correct at the unit level, and the controller crate is rustfmt-clean | Cargo toolchain with rustfmt | — | `tests/out/runs/default/suites/unit/.../cargo-test-bins.log`, `cargo-fmt-check.log` `rust.disposition_reds` runs the four disposition record controller tests by exact name and separates their assertions from equipment failures. |
| `runner_unit` | Baseline | Swift runner internals: `CWorkerOrchestrator` envelope invariants, scoped comparison and consumer-encoding guarantees, `classify` worker/validator→normalized-outcome table, `buildAttemptResult` (kind, action, slot)→attempt-outcome table, shared prediction_unavailable exclusions and query planning, and CWorker + ValidatorClient drivers. Lifecycle controls retain independent polling, termination and confirmed-reap observations through the driver and JSON assembler. Native spawn controls retain unfamiliar return codes through release, worker-failure precedence and reply degradation. `ContractVersionTests` compares the generated Swift versions with `docs/contract.json` and the encoded reply shape with the golden `tests/fixtures/contract/response_shape.json`. `WorkerEvidenceTests` covers worker evidence publication, native call failures, diagnostic availability, cleanup-time snapshots, missing steps and EPIPE partial output. `HostOutcomeClassifierTests` exercises the production classifier with constructed results. `ComparisonEvidenceTests` reads every row of `tests/fixtures/comparison/matrix.json` and checks the encoder's record for constructed inputs; `source_drift` and the artifact inspection separately enforce that the host never touches libsandbox. | Swift + clang; signed app for required live controls | — | `tests/out/runs/default/suites/runner_unit/.../pwrunner_core_tests.log`. Wrapper builds `worker_lifecycle`; select with an app-dependent suite for integrity evidence and inspect the Swift log for internal SKIP. |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | — | Uses fixtures under `tests/fixtures/pw_runner/` |
| `runner_apply_isolation_v2` | Baseline | v2 deny-default specimens complete cleanly: the unsandboxed XPC host posix_spawns the C worker, the worker applies the policy and writes its slot results to shared memory, and the host replies with a full envelope | Built app + XPC | — | Asserts `runner_subprocess` and worker PID semantics |
| `runner_apply_isolation_v3` | Baseline | Same shape as `runner_apply_isolation_v2` but with SBPL v3 grammar, which has stricter validation | Built app + XPC | — | Asserts `runner_subprocess` and worker PID semantics |
| `runner_outcome_worker_spawn_failed` | Baseline | `_test_overrides.worker_executable_path=/nonexistent` makes `posix_spawn` return `ENOENT`; host returns `normalized_outcome="worker_spawn_failed"` | Built app + XPC | — | Asserts `runner_subprocess` is null (no worker observed) and override is mirrored back |
| `runner_outcome_runner_timeout` | Baseline | Deliberate empty-plan timeout control: host SIGKILL, failure diagnostic, honored overrides, explicit empty steps, and no validator metadata | Built app + XPC | — | Shares a focused checker with the single-write and mixed-outcome timeout cases; populated plans independently verify file effects and retained step evidence. Uses a 2s worker deadline and 8s hang; no log capture or tight wall-clock assertion. |
| `runner_outcome_bad_request` | Baseline | Two e2e cases that drive `normalized_outcome="bad_request"` through both emit sites in `PWRunnerService.runSpecimen` — Swift decode failure and `validateSandboxChecks` rejection. No `_test_overrides` needed. | Built app + XPC | — | Asserts `runner_subprocess` is null and that the error message identifies the rejected field |
| `runner_ready_byte_resilience` | Baseline | `_test_overrides.worker_pre_ready_hang_ms=2000` makes the C worker write its pre-apply ready byte after the host's 1000ms `readyByteTimeout` has closed `--ready-fd`. The worker must survive that SIGPIPE-prone write (SIGPIPE is ignored), still `sandbox_apply`, and score the probe — `normalized_outcome="ok"`. Regression guard for the `com.apple.WebProcess` slow-compile SIGPIPE bug. | Built app + XPC | — | Runs ~2-3s. Asserts `term_signal=null`, `exit_code=0`, validator ran, and the override is mirrored back. The seam delays after compilation/capture; this case has sufficient sentinel budget. The pre-apply witness uses a short budget and requires `runner_timeout`. |
| `runner_filter_iokit_registry_entry_class` | Baseline | The `(iokit-open-service, iokit_registry_entry_class)` pair returns `prediction_unavailable` with explicit sentinel/null evidence and the exact requested step. A supported file `open_read` placeholder retains attempt evidence; it does not establish IOKit enforcement. | Built app + XPC | — | Documents the prediction-unavailable op+filter pair contract (`query_plan:prediction_unavailable_pair`) |
| `runner_filter_sysctl_name` | Baseline | The `(sysctl-read, sysctl_name)` pair retains unavailable-prediction evidence and a real denied `sysctl` / `read` attempt against `kern.osrelease`. Independent checker controls exercise all three filter callers. | Built app + XPC; controls need only Python 3 | — | Shared envelope/step checks plus supported-file and sysctl-denial contracts |
| `runner_filter_iokit_user_client_class` | Baseline | `(iokit-open-user-client, iokit_user_client_class)` pair. Same `prediction_unavailable` contract; complements `runner_filter_iokit_registry_entry_class` to cover both registry-entry and user-client class matching modes. Same attempt placeholder caveat. | Built app + XPC | — | |
| `validator_bridge` | Baseline | Native query forwarding and acknowledged query/emission/closure gates, with independent native and process observations. | clang + macOS SDK | — | Test equipment; see [suite contract](suites/validator_bridge/README.md). |
| `validator_batch_mode` | Baseline | Pins the `sb_api_validator --batch <pid>` NDJSON-over-stdin/stdout contract: 10 mixed-filter probes against a `sandbox-exec` child cover all four verdict outcomes (3 allow + 1 deny + 1 error + 1 bad_filter + 4 parse_error including trailing-garbage + overlong-line regressions). Per-probe failures don't abort the run; step_id is preserved when known. The production runner uses this shape per run. Per-probe CLI mode preserved unchanged for diagnostic tooling. | Built app | — | |
| `failure_boundaries` | Baseline | Every capacity limit (worker, host-only plan strings, top-level and test-seam strings) with capacity-before-shape precedence and no echo of the refused string, validator UTF-8/structure/association, admission refusal of an overlong query with the largest admitted probe measured, control-character round trip through the real validator, submitted-ID join after unlink, and independent helper admission. | Built app + XPC | — | [Suite contract](suites/failure_boundaries/README.md); raw requests, producer transcripts and CLI envelopes are retained per case. Driver lifecycle and receiver byte accounting have separate Swift/Rust controls. |
| `runner_outcome_validator_no_reply` | Baseline | A real validator I/O deadline closes collection, preserves one ordered prediction and releases both attempts. | Built app + XPC + Python 3 | — | Exact outcome, diagnostic, override echo, cleanup and independent file effects. |
| `runner_validator_failure` | Baseline | Partial validator replies survive clean shortfall, malformed JSON or a real signal, attach to the correct step IDs, and preserve all completed attempts. The unanswered prediction has an explicit error and missing reason; its comparison stays `unestablished` beside the completed attempt's observation. | Built app + XPC + Python 3 | — | Checked-in validator transcripts have direct controls; CLI cases independently check file effects, degradation, honored overrides, and subprocess completion. Shared with the corresponding `witness_contract` entry points. |
| `runner_abi_layout` | Baseline | Layout-drift guard between the C ABI header and Swift `PWShmLayout`. Compiles a tiny `printer.c` against `pw_probe_runner_abi.h` at test time, harvests every `sizeof`/`offsetof`/macro value, parses the mirrored Swift enum, and asserts bidirectional agreement. Catches what parser-only `source_drift` can't model (compiler struct padding). Checks compiled C values against the limits inventory and exercises the validator query-size boundary and the control-character round trip (escaped input decoded, output re-escaped, surrogate pairs, malformed escapes as per-probe parse errors). Compares the compiled ABI number and the whole layout harvest with `docs/contract.json` and the golden `tests/fixtures/contract/abi_layout.txt`. | `xcrun clang` + macOS SDK; no app | — | Companion to `source_drift`'s enum-agreement check; both belong in the Baseline tier. |
| `runner_c_worker_harness` | Baseline | Proves `pw-probe-runner` (the C worker) in isolation across 34 hand-built-shm scenarios, including ten release-barrier controls, seven exec descriptor-budget controls (inherited descriptors, hard caps, policy imports and mixed-plan reads) and two exec attempt-budget controls (deadline-hitting helpers cut at the budget, later execs refused before spawn, a trailing read still completing): `(allow default)` happy path, bare `(deny default)` isolation, clean exit-byte teardown, SIGKILL fallback, a 256-slot multi-page shared-memory run, an SBPL-params round-trip that proves `policy.params` reach the kernel (kernel-observed deny on `/etc/hosts` when `TARGET=/private/etc` is passed through `sandbox_create_params` + `sandbox_set_param`), the file unlink/create attempt kinds (allow + deny), and the worker's pre-apply self-defense exits (compile failure survives with `apply_rc=-1`; abi/prepared/step_count/param_count/policy-overflow refusals → exit 4/5/6/7/8). | Built app + harness | — | Compiles `harness.c` once per suite run into `tests/out/.../harness.runner_c_worker` |
| `runner_use_c_worker` | Baseline | End-to-end coverage of the runner's C code path. Drives real specimens through `controller → XPC service → CWorkerOrchestrator → pw-probe-runner + sb_api_validator --batch` normally without `_test_overrides` (the timeout case deliberately uses the deadline and hang seams). Covers: the envelope shape (`validator_subprocess` populated, comparison records present, prediction_unavailable answers synthesized locally), bug-report `(deny default)` survival, and regression cases for duplicate step_ids (plan-killer), unsupported attempt combos (per-step skip), worker timeout with completed write evidence and independent file effects, sandbox_check.pid = worker PID, the access_failed outcome, bare `process-exec` queries, unresolved planning paths, and exec argument, stream and truncation round trips. | Built app + XPC | — | |
| `runner_mach_service_liveness` | Baseline | The built `PWRunner` executable, launched directly with `--mach-service <name>` (the BYOXPC LaunchAgent launch shape), binds `NSXPCListener(machServiceName:)` and stays alive instead of aborting under `xpc_main`. Regression guard for the BYOXPC `xpc_timeout` crash: a host that calls `NSXPCListener.service()` for this launch aborts immediately (`"An XPC Service cannot be run directly."`), which is what made `runner verify` time out. Complements `runner_unit`'s `pwListenerConfig` table (which pins the argv→listener selection) by asserting the shipped binary itself does not abort. | Built app | — | Launches the host binary without launchd, so it never services a connection here — it only asserts the process does not abort. `tests/out/runs/default/suites/runner_mach_service_liveness/.../artifacts/pwrunner.stderr.log` |
| `runner_byoxpc` | Opt-in | Smoke + blackbox coverage through a BYOXPC runner | Built app + launchd (GUI session) | Annotated mismatch condition in shared menagerie cases only | Uses an owned, uniquely named runner copy; signing preserves the selected app and cleanup verifies removal. Shared smoke/blackbox assertions include checker controls. BBX expectation failures do not suppress attempt validation. |
| `smoke` | Baseline + opt-in caller-auth case | Quick end-to-end checks against a built app bundle; the default case is also the one exact contract check (`docs/contract.json` versus the built app's reported response schema and worker ABI) and verifies the envelope build stamp against the app's Info.plist | Built app + XPC; selecting the whole suite also requires a matching Developer ID | — | `--suite smoke` includes `runner_caller_auth`. For ordinary smoke without signing equipment, select `--case smoke/specimen_file_read_deny --case smoke/specimen_file_read_deny_standard`. Ordinary specimens also run under `runner_byoxpc`. Caller-auth checks use signed app copies, identical-client restricted/relaxed controls, independent file effects, and a missing-service control. |
| `blackbox_e2e` | Baseline | End-to-end black-box cases (BBX-*) validate the returned JSON envelope, attempts, and step identity/order. Expected answers and attempts are asserted by field; independent checker controls ensure one failure cannot hide another. | Built app + XPC; checker controls need only Python 3 | — | Live cases also run under `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_e2e` `checker_controls` also runs the disposition contract's structural self-check and the independent lifecycle oracle's self-check (`tests/lib/lifecycle_oracle.py`): hand-reviewed rows reproduced, built records accepted, mutations rejected, D-model total. |
| `blackbox_menagerie` | Baseline | Real SBPL fixtures exercising specimen ingestion and evidence correlation; controls drive both black-box checkers against independent envelopes and faults | Built app + XPC; validation controls need only Python 3 | Annotated mismatch is absent after all evidence checks pass | Live cases also run under `runner_byoxpc`; runs standalone via `tests/run.sh --suite blackbox_menagerie`. See `tests/suites/blackbox_menagerie/README.md` for invariants and fixtures. |
| `sbpl_allowdeny_consistency` | Baseline | Independently reads randomized file targets after writes, checks changed/nonempty bytes vs byte-for-byte preservation, restores seeds and reverses policy parameter bindings with the same probe plan, then cross-checks JSON verdicts. The fixture retains two Mach steps, checked for presence only. | Built app + XPC | — | Two specimens/envelopes plus external before/after byte snapshots; no log dependency or test overrides. |
| `runner_live_worker_identity` | Baseline | Test-owned observer obtains the exec helper PID from the kernel socket peer, follows OS ancestry to the worker and host, independently queries libsandbox while they live, and checks PW reports that worker and those verdicts. | Built app + XPC + macOS C toolchain | — | Bounded handshake; no PW source dependencies or test overrides. `observer.json` records independent PIDs, start times, and raw queries. |
| `runner_exec_dac` | Baseline | Direct execution and PW both reject a non-executable helper with EACCES and succeed after execute permission is restored; the failed attempt retains its raw evidence as a `permission_failure` observation without sandbox attribution. | Built app + XPC | — | Native exec scope controls separate target admission from fork/interpreter prerequisites, preserve child failure after spawn, and record a different submitted target as `different_submitted`. Direct permission controls retain unattributed EACCES. |
| `exec_fixture` | Baseline | Independently verifies the shared helper's output/status, socket rendezvous, OS process identity/exit observation, environment/descriptor inspection, state-preserving exec forwarding, and the `--write` marker mode (exact bytes at 0600, exclusive-create refusal, missing-directory failure). A leader-only kill must be rejected while its child still answers; releasing one tree must leave another alive. | macOS C toolchain + Python 3 | — | Direct controls; no app dependency. Normal release and group kill must pass the same exit assertion. |
| `run_capture` | Baseline | Shared CLI capture preserves exact bytes, arguments and exit/signal status; distinguishes harness deadlines from PW results; keeps overlapping runs separate; and reaps the CLI after assertion failure | macOS + Python 3, Unix sockets and OS exit observation | — | No app or C compilation. Independent fixture, socket acknowledgements and exec fixture exit observer. Retains raw output and `capture.json`, including launch/JSON/cleanup errors. |
| `runner_specimen_isolation` | Baseline | Two bundled-runner specimens with identical step IDs overlap; B completes while A remains held. OS identities, independent file effects, and each run's output/attempt/prediction evidence stay separate. | Built app + XPC + macOS C toolchain + Python 3 | — | Shared envelope/step validation plus independent observations. Controls cover cross-run swaps, missing/invalid evidence, legitimate optional fields, and combined failures; direct release controls live in `exec_fixture`. |
| `run_effects` | Baseline | Each file attempt action has one exact, externally observed effect: `open_write` truncates the target in place to one byte, `create` produces an empty 0600 file or leaves an existing one untouched, `unlink` removes it, `open_read`/`access` change nothing; a denied twin of each mutating action leaves the target identical. An allowed exec helper's own file write is real and a denied helper runs but leaves no file. A plain run adds no launchd plist and does not change the runner registry. | Built app + XPC + macOS C toolchain + Python 3; controls need only Python 3 | — | Snapshots (bytes, size, mode, device/inode, links, mtime/ctime) are taken outside PW before and after each run, retained, and checked before the envelope is decoded. Expectations are pure functions with direct controls that must reject fabricated wrong observations. Allowed unlink records its native answer and `query_first` order beside the observed removal. `launchctl list` labels are recorded as diagnostics only. |
| `runner_exec_lifecycle` | Baseline | A public CLI exec deadline stops both observed helper processes, preserves output, and permits a subsequent file write with independently checked effects. | Built app + XPC + macOS C toolchain + Python 3 | — | No test overrides or worker ABI dependency. Includes early stream EOF, leader exit with a live descendant, and worker death during an unpublished exec. Artifacts retain PID/group/exit observations and before/after bytes. |
| `runner_exec_inheritance` | Baseline | Exec children report empty environments, only standard descriptors, stdin EOF, and usable output. The CLI case uses ordinary specimens; a controlled worker launch proves random environment/descriptor resources existed to leak. | Built app + XPC + macOS C toolchain + Python 3 | — | Shared observer and assertions have direct contamination controls. The worker adapter owns the ABI dependency; opt-in mutation checks verify real leak detection. |
| `opt_in` | Opt-in | Select all non-default catalog cases | See registry | — | `tests/OPT_IN_TESTS.md` |
| `witness_contract` | Baseline | Ordered native queries, held-collection file/process effects, interval/state limits, 256-step and deny-default witnesses; required opt-in worker/host bypass controls. Pins verdicts, attempts, independent query/attempt routing, removed-target mutation uncertainty, validator-failure attribution, completed observations after worker timeout, absence of policy claims before application, existing-file create semantics, rejected fields, test seams, and audit rules. | Built app + XPC | — | The routing case swaps real prediction targets while independently observed writes stay fixed; its intentional target mismatch must retain both channels without claiming a comparison. The pre-apply case requires the current response schema and no invented library/policy result, with a populated positive control. `worker_termination_and_log_correlation` combines denied writes with self-signal, capture disabled/enabled, successful-run capture, and ambiguous event references; Rust controls pin captured-event association independently of log availability. `deny_capture_covers_the_run` holds a run past twenty seconds and checks the requested client interval through the real observer, using allowed queries; one denied read goes through a symlinked directory and must resolve through the host's attempt path forms; it records early/late availability without requiring emission, checks the padded bounds and collection/cleanup facts, and, for complete collection, requires `permission_failures_without_record` to name exactly the unrecorded reads; incomplete collection leaves it null. The offline `log_capture_controls` case rejects unsupported unavailable/budget claims. Deterministic Rust controls require full/early/late/empty preservation, padding-boundary exclusion, rollback refusal, and mismatched-window suppression through parsing, serialization and consumer recovery. `comparison_matrix` runs the live specimens of `tests/fixtures/comparison/matrix.json`, including the steered-validator specimen, and checks every row's record, raw fields and independently observed file effects; `dossier_witness` checks `data.specimen` across ordinary, import, augmented, refused, no-source, controller-refusal and executable-override runs (`dossier_witness_byoxpc` is the opt-in BYOXPC copy). `worker_progress_and_failure` checks real compiler diagnostics and opaque fixture-code forwarding. `worker_sparse_failure` checks admitted-size transfer interruption and EPIPE, absent reports/mapping failure, and retained completed file effects. `unfamiliar_diagnostic_transport` checks two open diagnostic codes through worker and validator forwarding, independent failures, publication rejection and text truncation. `max_targets_reply_survives` covers five complete 256-step workloads (denials, escaped paths, 511-byte independent query paths, 256 execs with output, and 256 execs with control-character query paths and streams, the worst admitted escaping) and requires 32,768-byte query values and filter/attempt labels to be refused at admission with no reply loss or file effects. `max_exec_steps_spawn` requires every exec step of a 256-step plan to spawn, which the worker's pre-apply descriptor-limit raise makes possible. `happy_path_baseline` is the regression sentinel. `worker_attempt_in_flight_at_deadline` blocks attempt 0 on a writerless FIFO until the host deadline and requires the controller to project the witnessed deadline, SIGKILL request and reaped signal as `termination_cause: host_sentinel_deadline`, the completed prefix and voluntary exit during grace to survive, and every lifecycle claim to satisfy the independent oracle (`tests/lib/lifecycle_oracle.py`); after CLI launch, FIFO staging is removed only on the envelope's `reaped: true` with a valid worker PID. |

## Conventions

### Shell case setup and checking

Shared shell startup rejects Python with assertions disabled (for example,
`PYTHONOPTIMIZE=1`) with exit 2 before changing output or running cases. Unset
`PYTHONOPTIMIZE` to run tests. Direct Python helper invocations bypass shell
startup; invoke those with assertions enabled. Independent startup controls live
in `shell_helpers`.

`tests/lib/case.sh` provides baseline prerequisite checks, logged command
execution, fixture builds through their existing scripts, and Python checker
invocation. Cases retain their steps, argument lists, artifact paths, and final
pass statements. A failed stage writes a failed report and exits immediately;
it does not depend on the wrapper's `set -e`. Direct scripts retain the optional-app helpers in `testlib.sh`; the public
dispatcher enforces catalog prerequisites and rejects undeclared skips. Direct controls live
in `shell_helpers`; see `tests/suites/shell_helpers/README.md` for the API.

### CLI capture

`tests/lib/run_capture.py` prepares the supplied specimen and captures the public
CLI command, raw stdout/stderr, exit status, timing, and harness intervention.
Separate start/wait operations support overlapping runs. The caller supplies CLI
arguments and a test-side wait deadline, decides when to decode JSON, and owns
all outcome assertions and independent observations. Cleanup runs after those
observations. The initial users are `runner_validator_failure`,
`runner_exec_lifecycle`, and `runner_specimen_isolation`; independent controls
live in `run_capture`. See `tests/suites/run_capture/README.md` for the API and
artifact contract.

### Black-box validation

`blackbox_e2e`, `blackbox_menagerie`, `runner_specimen_isolation`, the
`witness_contract` prediction-target case, and the three `runner_filter_*` suites
share `tests/lib/blackbox.py` for envelope checks, step
identity/order, evidence fields and types, and explicit per-step expectations. Each suite owns its
policy, file-observation, denial, and skip rules. The helper only collects
errors; it neither runs PolicyWitness nor chooses expectations. Nullable path
fields remain present, while attempt `error` text is optional.
Black-box and filter controls exercise checker CLIs without importing the helper
or production code. Isolation controls call the suite adapter with separately
recorded witnesses. Both approaches require combined faults to remain visible.
Black-box and isolation controls also compare ordered/reordered response pairs:
only the order diagnostic may change, preserving actual step failures without
inventing others. Diagnostic order is unconstrained.
The filter suites use the `unavailable_prediction.py` CLI adapter, supplying
step identity, operation, filter value and either a supported file-open or
denied-sysctl attempt contract; the adapter accepts only the current response
and envelope versions. Their independent controls run through
`runner_filter_sysctl_name` before its optional app check; see its README.

The menagerie's end-to-end specimens come from local copies of PAWL evidence.
It covers SBPL ingestion, probe execution, and evidence correlation, including
negative controls and canonicalization-boundary cases where mismatches are
recorded as evidence. An absent annotated mismatch can skip only after all
evidence checks pass. See `tests/suites/blackbox_menagerie/README.md` for
suite invariants and fixtures.

### Sandboxed automation harnesses

Some automation and agent harnesses run commands under a macOS sandbox. Inside
one, XPC lookup of the runner can be refused (`NSCocoaErrorDomain` code 4099,
or error 159 “Sandbox restriction”), so no runner launches; the unified log
tool can refuse to run (`log: Cannot run while sandboxed`), so deny evidence
cannot be captured; and `codesign --verify` can report “invalid signature (code
or signature have been modified)” for an unchanged, validly signed app. These
refusals can be environment constraints. Request escalation and rerun the same
command once outside the automation sandbox against unchanged artifact bytes.
Treat a signature failure as environmental only after the unsandboxed check
passes; debug any failure that remains.

The dispatcher checks the equipment it can see: the built app and worker
binaries, toolchains, a GUI session, a signing identity. XPC reachability and
log access are not prerequisites, so inside a harness a live case runs and fails
as an ordinary failure, with the `xpc_error` envelope in its artifacts, while a
`gui` prerequisite that cannot be confirmed is reported as missing equipment
with the case unrun. Neither is a PolicyWitness defect. Suites that declare no
`app` or `worker` requirement (`source_drift`, `shell_helpers`, `dispatcher`,
`run_capture`, `unit`, `exec_fixture`, and `runner_unit` against its own
fixture) never launch the XPC service, though the cancellation and
process-observation controls among them may still need escalation for local
sockets and exit events. Run everything that declares `app` or `worker` from an
unsandboxed Terminal; `--all --list` shows each case's requirements.

## Output contract (`tests/out/`)

An executing invocation of `tests/run.sh` replaces its output directory so tooling
can read stable paths. Help, `--list`, and rejected commands preserve it:

```text
tests/out/
  plan.json
  run.json
  dispatch.json
  events.jsonl
  artifact-integrity/  # when selected cases require app/worker
    inspection.json
    before.json
    after.json
    changes.json
  suites/<suite>/<test_id>/
    report.json
    events.jsonl
    artifacts/...
```

`plan.json` records the selection before execution. `dispatch.json` journals each
command invocation, expected cases, execution status, report snapshots, and
harness errors. Most cases execute in separate processes; BYOXPC leaves share
installation and cleanup. The installation case is also a selected dependency.

`run.json` retains reports/counts and includes the plan, effective configuration,
invocations, harness errors, and one `case_results` entry per selected case.
`artifact_integrity` records initial validity, final equality, evidence location,
and artifact errors, or is null for an entirely offline selection. Artifact errors
fail `ok` independently of case reports; incomplete inspections retain diagnostics
instead of claiming equality.
Distinct catalog cases must use distinct report paths; collisions are rejected
before output is replaced. The executor also refuses ambiguous report ownership
and checks complete, unique selection accounting before reporting success.
`completion` counts selected, completed (pass or fail reports), skipped, and
unrun cases. These are separate from readable-report counts: a missing report
cannot disappear merely because no report was available to count.

Started cases need one terminal event and a matching report. Unselected reports,
reused paths, malformed or contradictory evidence, silent commands, crashes,
unrun selections, and undeclared skips fail. A declared skip requires a matching
`skip_reason` in the report. Current live skips are limited to the menagerie's
absent annotated mismatch after evidence validation. There is no skip-policy flag.
`run.json.ok` and the shell exit agree: zero failed reports and zero harness
errors. Exit 2 means planning/configuration was rejected before execution.
See `tests/suites/dispatcher/README.md` for the independent controls.

`failure_boundaries` covers the admission and validator receiver routes in
[the receiver contract](FAILURE-PROPAGATION-CONTRACT.md#admission-and-validatorcontroller-receiver-contract). Run it with `runner_unit`,
`runner_abi_layout`, `runner_c_worker_harness` and `unit` for driver/ABI/controller
controls. Existing `runner_validator_failure` and `witness_contract` retain their
partial evidence and attribution assertions.

## Comparison evidence coverage

The comparison record's scenarios live in one fixture,
`tests/fixtures/comparison/matrix.json` ([its README](fixtures/comparison/README.md)):
every row names a specimen step, the expected six-field record, the raw fields
it rests on and an independent control. `witness_contract/comparison_matrix`
runs the live specimens through the CLI and checks every row's record, raw
fields and file effects; `runner_unit`'s `ComparisonEvidenceTests` reads the
same rows against the Swift encoder; the shared `tests/lib/consumer.py`
validates every record against its raw channel fields and `order` against the
ordering chain. The [failure contract](FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
names which case owns which rows and invariants. Step identity, independent
file/process observations, native results and partial-evidence protections
remain separately asserted.

The default `witness_contract/log_query_predicate_archive` case requires the
committed [query archive and independent manifest](fixtures/deny_capture/README.md).
It performs read-only OS queries; no default case may generate or download a
replacement fixture. Missing data or incompatible readers fail explicitly.
