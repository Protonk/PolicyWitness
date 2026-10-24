# Opt-in test survey: revision 2f23cad

A read-only survey of which PolicyWitness tests are outside the default
battery, how that exclusion is implemented, and how faithfully the
implementation follows the documented opt-in convention. It establishes the
current situation and does not propose a replacement.

## Summary

The opt-in mechanism is one boolean per catalog case. `tests/catalog.json`
marks 39 of 235 registered cases `default: false`; the public dispatcher
selects the other 196 when invoked with no selectors, every case with `--all`,
and the 39 through `--suite opt_in`, an owning suite or an exact `--case`. The
`opt_in` group is a hand-maintained include list, and a default-battery control
(`dispatcher/test_command_controls`) fails if that list ever differs from the
set of non-default cases. At this revision the list, the README tier column and
the registry's coverage all agree with the catalog, and every non-default case
has been non-default since it first appeared.

What does not agree is the surrounding prose. The registry's criteria list
dates from January 2026, when opt-in tests were standalone scripts under
`tests/suites/opt_in/`; it still cites CI instability (the repository has no
CI configuration), tells the author to put scripts under `opt_in/` (23 of the
39 cases are driven by scripts elsewhere) and to move a test "into the smoke
suite" when its reason lapses. Its "specified red test" criterion has no
current instance, while a default script still describes itself as a
non-default red. One contract sentence says acceptance selects every
registered case including opt-ins; no entry point does that. Several reasons
the registry actually records for individual cases (mutation anchors that need
review, exploratory observations that assert no product behavior, optional
equipment, shared default state) are not among the criteria it lists.

Nothing surveyed excludes a test silently under the public command: missing
equipment is an explicit unrun case, an undeclared skip is a harness error, and
the only declared live skip is the menagerie's absent annotated mismatch. The
direct suite scripts have no notion of default membership at all: invoked by
hand, `tests/suites/preflight/run.sh` runs the opt-in build controls and
`tests/suites/smoke/run.sh` runs one of the suite's three cases.

## Scope, revision and method

- Revision examined: `2f23cad3cf5ac10a4d87f75d9bd1a2c2a026bc09` (2026-10-24,
  "Record the pre-touch investigation"), branch `main`.
- Working tree: clean at the start and at the end of the survey, apart from
  this report. No source, test, documentation or build file was modified.
- Executed: five read-only planning invocations of the public command, which
  write nothing (`tests/README.md` lines 66-73):
  `./tests/run.sh --list`, `./tests/run.sh --all --list`,
  `./tests/run.sh --suite opt_in --list`, `./tests/run.sh --suite smoke --list`
  and `./tests/run.sh --case runner_byoxpc/BBX-001 --list`. Their case counts
  are the executed evidence in this report. No test case was run.
- Static inspection: `tests/catalog.json` was parsed with the dispatcher's own
  loader (`catalog()` and `select()` in `tests/lib/test_cli.py`) so that
  suite-level inheritance of `default`, `requires`, `command` and `context`
  matched the implementation exactly; the catalog's history was walked with
  `git show <commit>:tests/catalog.json` over every commit touching it; the
  registry, READMEs, suite scripts, the Rust and Swift test sources and the
  selection and executor code were read.
- Investigative artifacts (parsed plans, the catalog walk) lived in the
  session scratch directory outside the checkout and are not retained; every
  count below can be regenerated from the commands named beside it.
- Retained local runs under `tests/out/runs/` (ignored by git, present only in
  this checkout) are cited only for dates of past opt-in executions; the
  committed index is `tests/RETAINED.json`.

Terminology collision to keep out of the inventory: the `opt_` prefix in the
menagerie case names (`opt_vfs_tmp_only`, `opt_metafilter_any`,
`opt_bucket5_subpath`) is the PAWL fixture category, not opt-in status, and
"opt-in" in `docs/PolicyWitness.md` names a product feature (the
compiled-object receipt). Neither is part of this survey.

## A. Current policy

### Sources and what each says

1. `tests/OPT_IN_TESTS.md` ("Opt-in Tests (dev-only)"), the registry. Lines
   7-10 define the mechanism: opt-in cases are excluded from the default
   `tests/run.sh` battery, remain in `--all`, are included by an explicit
   `--suite` selector, and `tests/catalog.json` defines membership and
   equipment. Lines 12-26 give the criteria, "any of the following is usually
   sufficient": a TTY or PTY; network, GUI services or other host capabilities
   "unstable in CI"; a Developer ID identity or notarization; long or heavy
   runtime; Unified Logging or other sandbox-sensitive telemetry; a specified
   red test for planned behavior, kept non-default until green. Lines 531-546
   give the entry template (suite name, location "under
   `tests/suites/runner_*/opt_in/`", purpose, opt-in reason, when to run,
   artifacts, gating) and the exit rule: when the reason is removed, "move the
   test into the smoke suite and remove it from this registry".
2. `tests/README.md`. Lines 59-64: no selectors runs the default battery,
   `--all` selects every registered case including opt-ins, a suite selects
   all its members including opt-in members. Lines 96-99: opt-in cases are
   selectable by exact case, owning suite, `--suite opt_in` or `--all`; direct
   suite scripts are developer entrypoints without the public command's
   guarantees. Lines 313-319, "Tiers": Baseline is "ordinary default cases on
   supported hosts"; Opt-in is "resource-sensitive signing/launchd work or
   implementation mutation controls", and some Baseline suites also own opt-in
   cases. Lines 329-331: missing prerequisites fail the run with explicit unrun
   cases; the only supported live skip is the menagerie's absent annotated
   mismatch. Lines 321-376: the suite table's Tier column (`Baseline`,
   `Baseline + opt-in`, `Opt-in`).
3. `tests/AGENTS.md`. Line 17 routes "resource-sensitive or mutation controls"
   to the registry; line 26 repeats that a suite selector includes its opt-in
   members; lines 58-60 name `witness_contract/order_barrier_mutations` as a
   control to rerun on specific changes; line 115 requires the registry to be
   kept aligned when tests change.
4. `tests/suites/opt_in/README.md`: the group contains "every non-default
   case, including signing, BYOXPC, mutation controls and exploratory
   worker-resource observations".
5. `tests/catalog.json` and `tests/lib/test_cli.py`: the implementation. A
   case's `default` is its own value, else its suite's, else `true`
   (`test_cli.py` lines 32-40). `select()` (lines 71-102): `--all` selects
   every case; no selectors selects cases with `default` true; a suite
   selector selects every key listed for that suite, including an `include`
   list; dependencies are added transitively and labelled `dependency`.
6. `docs/DEPENDENCIES.md` lines 44-56: the equipment table maps `identity` to
   "opt-in cases only", `gui` to "opt-in BYOXPC cases", `rosetta` to one named
   opt-in case, and points to the registry for the list.
7. `tests/FAILURE-PROPAGATION-CONTRACT.md` lines 1461-1463: "Acceptance selects
   every registered canonical case in the catalog, including opt-ins and both
   runner contexts; required skips or unrun cases prevent completion."

### What opt-in means in the project's own terms

Normatively: a case the default battery omits because of a listed resource,
cost or telemetry dependency, or because it is a registered red. Mechanically:
`default: false` in the catalog, which the dispatcher reads; nothing else
(directory placement, script naming, the registry) affects selection.

### Disagreements among sources, preserved

- Three characterizations of the population coexist. The registry's criteria
  list names equipment, cost, telemetry and reds. The README "Tiers" section
  names signing/launchd work and mutation controls. The `opt_in` README names
  signing, BYOXPC, mutation controls and exploratory observations. Mutation
  controls and exploratory observations are absent from the registry's
  criteria; equipment-only and telemetry reasons are absent from the README's
  tier definition.
- The registry template says scripts live under `opt_in/`; two registry
  entries that have since been removed said explicitly that red cases live
  "beside their suite's default cases, not under `opt_in/`, because each is
  promoted in place" (`git show 831596b:tests/OPT_IN_TESTS.md`, lines 161-168).
  The current file keeps the template and has lost the exception.
- The failure-propagation contract's acceptance sentence describes a selection
  (every case, opt-ins included) that `tests/README.md` lines 101-109 and
  `docs/SIGNING.md` line 353 do not: release acceptance runs two cases and the
  release battery is the default battery.
- The registry header still frames the GUI/network criterion around CI
  instability. No CI configuration exists in the repository (no `.github/`,
  no other CI files; the word "CI" occurs in exactly one Markdown line in the
  tree, that one).

## B. Test inventory

### B.1 Entry points and their selection behavior

| Entry point | How selection is decided | Cases selected at this revision | Evidence |
| --- | --- | --- | --- |
| `make test` | Sets `PW_APP_DIR` to `$(DIST_DIR)/PolicyWitness.app` and runs `./tests/run.sh` with no selectors | 196 (default) | `Makefile` `test` recipe; executed `--list` |
| `./tests/run.sh` | Catalog cases with `default` true | 196 requested, 0 dependencies | executed `./tests/run.sh --list` |
| `./tests/run.sh --all` | Every catalog case | 235 | executed `--all --list` |
| `./tests/run.sh --suite opt_in`, `tests/suites/opt_in/run.sh` | The `opt_in` include list plus dependencies | 40: 39 requested plus `runner_exec_inheritance/contaminated_worker` (a default case) as a dependency | executed `--suite opt_in --list` |
| `./tests/run.sh --suite NAME` | Every member of the suite, opt-in members included | e.g. `smoke`: 3, of which `runner_caller_auth` is non-default and needs `identity` | executed `--suite smoke --list` |
| `./tests/run.sh --case SUITE/CASE` | The exact case plus `depends_on` closure | e.g. `runner_byoxpc/BBX-001`: 2 (adds `runner_install`) | executed `--case ... --list` |
| `make release` | Runs `./tests/run.sh` with no selectors against the stapled app after acceptance | 196 | `Makefile` `release` recipe |
| `tests/accept-release.sh` | `tests/run.sh --case` for a fixed pair | 2: `smoke/specimen_file_read_deny`, `witness_contract/happy_path_baseline` | `tests/lib/release_accept.py` line 19 |
| `bash tests/suites/<suite>/run.sh` (direct) | Whatever the script enumerates; `test_selected` returns true for everything when `PW_TEST_CASES` is unset | Varies; see B.6 | `tests/lib/testlib.sh` lines 173-180 |
| `cargo test` in `controller/` (by hand) | Cargo's own discovery | 221 of 223 `#[test]` functions run; 2 are `#[ignore]` | `controller/src/run_flow.rs` lines 932, 1092 |
| `swift run PWRunnerCoreTests` in `runner/` (by hand) | `main.swift` calls every test file's entry unconditionally | All blocks; missing equipment throws a failure, never a skip | `runner/Tests/PWRunnerCoreTests/main.swift`, `TestKit.swift` |
| CI | None configured | n/a | no CI files in the tree |

The public command rejects `PW_TEST_CASES`, `PW_TEST_SUITE_OVERRIDE`,
`PW_TEST_EVENTS` and `PW_TEST_RUNNER_*` as caller settings
(`test_cli.py` lines 113-116), so there is no undocumented selection channel
through the environment.

### B.2 Catalog population

| Population | Count | How counted |
| --- | --- | --- |
| Suites in the catalog | 42 (41 with their own `cases`, plus the `opt_in` include-only group) | `catalog()` |
| Unique canonical cases | 235 | `catalog()`; `--all --list` |
| Default cases | 196 | `select()` with no selectors; `--list` |
| Non-default cases | 39 | `default` false after inheritance |
| `opt_in` include entries | 39, equal to the non-default set | catalog `suites.opt_in.include` |
| Cases with a declared skip reason | 16, all `annotated_mismatch_absent`: the 8 `blackbox_menagerie` specimens and their 8 `runner_byoxpc` copies | catalog `skip_reasons` |
| Cases with `depends_on` | 12: 11 `runner_byoxpc` leaves on `runner_install`, and `launch_inventory` on `contaminated_worker` | catalog |
| Cases with `context: byoxpc` | 19, the whole `runner_byoxpc` suite | catalog |
| Suite-level `default: false` | 1 suite, `runner_byoxpc` | catalog |
| Cases listed in two suites besides `opt_in` | 2: `runner_validator_failure/validator_decode_failure_reports_degraded` and `.../validator_unavailable_reports_degraded`, also included by `witness_contract` | catalog `include` |

Non-default cases by owning suite: `runner_byoxpc` 19, `preflight` 5,
`witness_contract` 5, `runner_unit` 3, `runner_exec_inheritance` 3,
`runner_c_worker_harness` 1, `runner_exec_lifecycle` 1, `smoke` 1,
`sandbox_extensions_native` 1. The other 32 suites with cases are entirely
default.

Equipment among the 39 (case-level `requires` replaces the suite's list when
present): 21 need `gui` (all 19 BYOXPC cases and the two BYOXPC witness
cases); 16 need `identity`; 1 needs `rosetta`; 5 need neither the app nor an
identity nor a GUI session (`exec_reader_mutations`, `reaped_ack_mutation`,
`host_setup_oracle_sensitivity`, `native_clock`, `mutation_controls`); 4 need
the app or worker without identity or GUI (`closed_streams_leader_exit`,
`launch_inventory`, `closed_worker_stderr`, `path_query_integrated`).

### B.3 The 39 non-default cases

"Registry" names the heading under which `tests/OPT_IN_TESTS.md` documents the
case, and "recorded reason" condenses what that entry gives as the opt-in
reason, or the equipment it lists when no reason field is present. "Since" is
the first commit in which the case appears in `tests/catalog.json`; every one
of the 39 was `default: false` in that first commit and in every later commit
(catalog history walk over all 108 commits touching the file).

| Case | Script | Requires | Registry heading | Recorded reason | Since |
| --- | --- | --- | --- | --- | --- |
| `preflight/signed_artifact_controls` | `preflight/run.sh` → `check_signed_artifacts.py` | app, identity | signed artifact controls | No reason field; needs a matching Developer ID, uses disposable copies | 5d66bfe 2026-09-16 |
| `preflight/build_guard_controls` | `preflight/run.sh` → `opt_in/build_guards.py` | app, identity, cargo, meson, clang, swift | build guard controls | Multiple builds, signs both variants with keychain access | 110ea02 2026-10-10 |
| `preflight/build_refusal_controls` | `preflight/run.sh` → `opt_in/build_refusals.py` | same six | build refusal controls | Many builds, several fresh; keychain signing; one control needs unified-log access | a0b2871 2026-10-14 |
| `preflight/translated_build_refusal_controls` | `preflight/run.sh` → `opt_in/translated_build_refusals.py` | rosetta | translated build refusal controls | Rosetta is optional on Apple Silicon; the general controls must stay runnable without it | cb8a110 2026-10-21 |
| `preflight/build_toolchain_switch_controls` | `preflight/run.sh` → `opt_in/build_toolchain_switch.py` | same six | build toolchain switch controls | Two fresh full builds under different toolchains with keychain access | a785007 2026-10-15 |
| `runner_unit/exec_reader_mutations` | `runner_unit/opt_in/exec_reader_mutations.sh` | swift, clang | Exec reader publication and absence mutations | Three isolated Swift package compilations | 924a6ed 2026-10-18 |
| `runner_unit/reaped_ack_mutation` | `runner_unit/opt_in/reaped_ack_mutation.sh` | swift, clang | Confirmed-reap acknowledgement mutation | Two isolated Swift package builds | f382cf6 2026-10-18 |
| `runner_unit/host_setup_oracle_sensitivity` | `runner_unit/host_setup_oracle_sensitivity.sh` | swift, clang | Worker resource challenge probes | Exploratory native resource and failure observations; multiple disposable Swift builds; run outside the automation sandbox | 2d63c98 2026-10-17 |
| `runner_c_worker_harness/native_clock` | `runner_c_worker_harness/opt_in/native_clock.sh` | clang | Native worker clock applicability | Reads unified logging; OS-sensitive native behavior scoped to the recorded machine | 085e23e 2026-10-17 |
| `runner_exec_lifecycle/closed_streams_leader_exit` | `runner_exec_lifecycle/closed_streams_leader_exit.sh` | app, clang | Worker resource challenge probes | As above; the suite README calls it a characterization of an observation limit | 2d63c98 2026-10-17 |
| `runner_exec_inheritance/mutation_controls` | `runner_exec_inheritance/opt_in/mutations.sh` | clang | exec inheritance mutation controls | Development diagnostic that transforms and rebuilds the C implementation; anchors need review when spawning changes | ed922f7 2026-09-15 |
| `runner_exec_inheritance/launch_inventory` | `runner_exec_inheritance/run.sh` → `launch_inventory.py`; depends on `contaminated_worker` | app, worker | Production worker launch inventory | Exploratory process inspection, optional task-port access, two twenty-second holds | 90fcb1b 2026-10-17 |
| `runner_exec_inheritance/closed_worker_stderr` | `runner_exec_inheritance/closed_worker_stderr.sh` | app, worker, clang | Worker resource challenge probes | As above; the suite README calls it a characterization | 2d63c98 2026-10-17 |
| `smoke/runner_caller_auth` | `smoke/pw_runner_caller_auth.sh` | app, identity | built-in caller authentication | No reason field; needs a matching Developer ID for disposable app fixtures and real built-in XPC outside the automation sandbox | ed922f7 2026-09-15 |
| `witness_contract/order_barrier_mutations` | `witness_contract/opt_in/mutations.sh` | app, clang, swift, identity, meson | Order barrier mutation controls | Builds source mutations and signs disposable app copies; anchors require review when the implementation changes; a required acceptance control | 5f0fbc3 2026-09-26 |
| `witness_contract/dossier_witness_byoxpc` | `witness_contract/opt_in/dossier_witness_byoxpc.sh` | app, identity, gui | BYOXPC dossier witness | launchd service install, GUI session, matching identity | ed0bd3d 2026-10-01 |
| `witness_contract/extensions_byoxpc` | `witness_contract/opt_in/extensions_byoxpc.sh` | app, identity, clang, gui | BYOXPC extension and phase witness | Installs a launchd service in a GUI session; needs the app's identity | 21b01d6 2026-10-12 |
| `witness_contract/path_query_observations` | `witness_contract/opt_in/path_query_observations.sh` | app, clang, identity | Native path-query observations | Exploratory OS-sensitive native behavior and Developer ID signing; no agreement asserted | ffa6935 2026-10-14 |
| `witness_contract/path_query_integrated` | `witness_contract/opt_in/path_query_integrated.sh` | app | Integrated extra path queries | Exploratory OS-sensitive interpretation with extra query instrumentation; no product assertion | 4be8be2 2026-10-14 |
| `runner_byoxpc/runner_install` | `runner_byoxpc/run.sh` → `runner_install.sh` | app, gui, identity | runner_byoxpc (suite entry) | launchd service install and bootstrapping; an unsandboxed caller | ed922f7 2026-09-15 |
| `runner_byoxpc/specimen_file_read_deny` | `runner_byoxpc/run.sh` → `smoke/pw_specimen_smoke.sh`; depends on `runner_install` | app, gui | runner_byoxpc (suite entry) | As above | ed922f7 2026-09-15 |
| `runner_byoxpc/core_strict_tmp`, `core_read_only`, `core_mach_simple`, `opt_vfs_tmp_only`, `opt_vfs_private_tmp_only`, `opt_vfs_both_paths`, `opt_metafilter_any`, `opt_bucket5_subpath` (8 cases) | `runner_byoxpc/run.sh` → `blackbox_menagerie/run.sh`; depend on `runner_install`; skip reason `annotated_mismatch_absent` | app, gui | runner_byoxpc (suite entry) | As above | ed922f7 2026-09-15 |
| `runner_byoxpc/BBX-001`, `BBX-002` | `runner_byoxpc/run.sh` → `blackbox_e2e/bbx_00N.sh`; depend on `runner_install` | app, gui | runner_byoxpc (suite entry) | As above | ed922f7 2026-09-15 |
| `runner_byoxpc/runner_auth_external` | `runner_byoxpc/opt_in/runner_auth_external.sh` | app, gui | runner_auth_external | launchd install and an unsandboxed caller | ed922f7 2026-09-15 |
| `runner_byoxpc/registry_recovery` | `runner_byoxpc/opt_in/registry_recovery.sh` | app, gui | Registry recovery | Creates and removes launchd services in the GUI domain | 92891a5 2026-09-26 |
| `runner_byoxpc/single_use` | `runner_byoxpc/opt_in/single_use.sh` | app, gui, identity | BYOXPC single-use admission | No reason field; equipment is a signed app, matching identity and GUI launchd session | 40c520c 2026-10-06 |
| `runner_byoxpc/bad_neighbor_claims` | `runner_byoxpc/opt_in/bad_neighbor_claims.sh` | app, gui, identity | BYOXPC occupied-claim attribution | Live launchd service, timing-sensitive schedules, a same-UID foreign client | 9dc5340 2026-10-17 |
| `runner_byoxpc/entitlement_readback` | `runner_byoxpc/opt_in/entitlement_readback.sh` | app, gui, identity | BYOXPC entitlement read-back | launchd install, GUI session, matching identity | 5240a6a 2026-10-06 |
| `runner_byoxpc/entitlement_transfer` | `runner_byoxpc/opt_in/entitlement_transfer.sh` | app, gui, identity | BYOXPC entitlement transfer | As above | 7de5062 2026-10-06 |
| `runner_byoxpc/default_location` | `runner_byoxpc/opt_in/default_location.sh` | app, gui, identity | BYOXPC default location | Uses the shared default registry and a live signed user service | 6fd44fb 2026-10-17 |
| `sandbox_extensions_native/feasibility` | `sandbox_extensions_native/run.sh` | clang, identity | Native sandbox extensions | No reason field; needs a Developer ID with timestamp signing and unsandboxed execution | e8effbd 2026-10-12 |

All script paths are under `tests/suites/`. For every one of the 39, the
equipment the registry entry names agrees with the catalog's `requires` list
after inheritance (read side by side; this is a reading, not a mechanical
check, because the registry has no machine-readable key).

Grouping that affects the count: the eight menagerie specimens and the two
BBX specimens under `runner_byoxpc` are distinct catalog cases with distinct
report paths and are counted as ten; the registry documents them only through
its suite-level `runner_byoxpc` entry.

### B.4 Default cases by suite

196 cases across 33 suites. Members per suite: `runner_c_worker_harness` 46,
`witness_contract` 36 own plus 2 included from `runner_validator_failure`,
`runner_use_c_worker` 14, `blackbox_menagerie` 9, `source_drift` 8,
`shell_helpers` 8, `preflight` 7, `failure_boundaries` 7, `dispatcher` 6,
`runner_unit` 6, `blackbox_e2e` 5, `runner_exec_lifecycle` 4,
`runner_validator_failure` 4, `run_effects` 4, `unit` 4,
`runner_outcome_bad_request` 3, `runner_exec_inheritance` 2,
`runner_filter_sysctl_name` 2, `smoke` 2, `validator_batch_mode` 2, and one
each in `integration`, `runner_apply_isolation_v2`, `runner_apply_isolation_v3`,
`runner_outcome_worker_spawn_failed`, `runner_outcome_runner_timeout`,
`runner_ready_byte_resilience`, `runner_filter_iokit_registry_entry_class`,
`runner_filter_iokit_user_client_class`, `runner_filter_local_name`,
`runner_abi_layout`, `runner_mach_service_liveness`,
`sbpl_allowdeny_consistency`, `runner_live_worker_identity`, `runner_exec_dac`,
`exec_fixture`, `run_capture`, `runner_specimen_isolation`,
`runner_outcome_validator_no_reply`, `validator_bridge`. The exact list is
`./tests/run.sh --list`.

The README's suite-coverage Tier column agrees with the catalog for all 42
rows: 32 `Baseline` suites have only default members, 7 `Baseline + opt-in`
suites have both, and `runner_byoxpc`, `sandbox_extensions_native` and
`opt_in` (`Opt-in`) have none. The mechanical check in
`tests/suites/source_drift/check.py` lines 269-279 enforces only one
direction: a suite labelled `Baseline` must have at least one default case. It
would not notice a `Baseline` suite acquiring a non-default case or an
`Opt-in` suite acquiring a default one.

### B.5 Populations inside batch cases

Rust and Swift unit methods are not catalog units; `tests/README.md` line 64
says they "remain inside their respective batch cases". Static counts of
attributes and call sites, not executed counts:

| Batch case (default) | Command | Population | Mechanism |
| --- | --- | --- | --- |
| `unit/rust.unit` | `cargo test --bins` | 209 `#[test]` functions in the two binaries (198 in `policy-witness`, 11 in `sbpl-check`); 207 run, 2 are `#[ignore]` | `tests/suites/unit/run.sh` |
| `integration/cli.integration` | `cargo test --test cli_contract` | 14 `#[test]` functions in `controller/integration/cli_contract.rs` | `tests/suites/integration/run.sh` |
| `unit/rust.disposition_reds` | `cargo test --bin policy-witness -- --include-ignored --exact` with four names | 4 functions in `controller/src/disposition.rs`, also run by `rust.unit` | `tests/suites/unit/disposition_reds.sh` |
| `unit/rust.byoxpc_reds` | same form, two names | 2 functions in `runner_manager.rs` and `runner_select.rs`, also run by `rust.unit` | `tests/suites/unit/byoxpc_reds.sh` |
| `runner_unit/pwrunner_core_unit_executable` | `swift run PWRunnerCoreTests`, then two `cargo test ... --include-ignored --exact` replays | about 277 `tk.run` blocks across 33 Swift files, plus the 2 ignored Rust tests `policy_transfer_driver_replies_cross_assembly_and_consumer` and `worker_clock_driver_replies_cross_assembly_and_consumer` | `tests/suites/runner_unit/run.sh` lines 33-67 |

The two `#[ignore]` attributes (`controller/src/run_flow.rs` lines 932 and
1092) carry the reason "requires real Swift driver receipts; default
runner_unit invokes this exact test". Under cargo's own vocabulary they are
ignored; under the project's, they are default. The Swift harness has no skip
state: `TestKit` records pass or fail, `main.swift` calls every file's entry
unconditionally, and the equipment guards (`workerExists()`,
`bothBinariesExist()`, the `PW_LIFECYCLE_WORKER_FIXTURE` guards) throw a
failure when the app or fixture is absent. No Rust test is gated by a cargo
feature or by an environment variable other than the receipts directory the
two ignored tests read.

### B.6 Conditional skips, equipment exclusions and reachability

Declared skips. Sixteen cases declare `annotated_mismatch_absent`. The
menagerie README lines 25-29 state the rule: the case skips only after every
evidence check passes and the annotated mismatch is absent; a missing or
incorrect result takes precedence. These cases are collected, run, and may end
as `skipped`; the executor counts them separately from pass and fail.

Equipment. `requirements()` in `tests/lib/suite_run.py` lines 295-325 probes
`app`, `worker`, `cargo`, `swift`, `clang`, `gui`, `identity`, `meson` and
`rosetta` before each invocation; `app` and `worker` are credited only when
the bundle inspection passed. A missing requirement blocks the invocation with
`not_run`, and `finish()` fails the run whenever any selected case is unrun.
XPC reachability is not probed; a blocked live case runs and fails with
evidence. Nothing is installed by a probe.

Undeclared skip paths in scripts. `test_skip` is called at
`tests/suites/runner_unit/run.sh` lines 13-21 (no Swift, no `Package.swift`),
`tests/suites/validator_batch_mode/run.sh` lines 17-20 (validator binary
missing), `tests/suites/runner_c_worker_harness/run.sh` lines 47-49 and 853
(app or ABI header missing), `tests/suites/runner_use_c_worker/run.sh` lines
654, 754 and 840 (exec fixture failed to build), and through
`require_pw_app`, which skips and returns 1 when the controller is absent
(`tests/lib/testlib.sh` lines 289-300). Under the public command these are not
silent: a skip whose reason is not in the case's `skip_reasons` is the
`unexpected_skip` harness error (`suite_run.py` lines 348-349), and a script
that exits before starting a selected case leaves `unrun_case`. The catalog's
`requires` make most of them unreachable there anyway. Under direct
invocation they are ordinary skips, which `tests/README.md` lines 389-393
describe ("Direct scripts retain the optional-app helpers").

Direct suite scripts and default membership. `test_selected` returns true for
every identifier when `PW_TEST_CASES` is unset, so a directly invoked suite
script runs whatever it enumerates, with no reference to `default`:

- `bash tests/suites/preflight/run.sh` runs all 12 preflight cases, including
  the five opt-in build and signing controls, gated only by `test_require_pw`
  and identity resolution (`preflight/run.sh` lines 64-118).
- `bash tests/suites/runner_exec_inheritance/run.sh` runs `launch_inventory`
  (opt-in: two twenty-second holds and process inspection) together with the
  two default cases (`run.sh` lines 9-17).
- `bash tests/suites/runner_byoxpc/run.sh` without `PW_TEST_CASES` runs
  `runner_auth_external`, `runner_install`, the smoke specimen, the menagerie
  wrapper and the `blackbox_e2e` wrapper (`run.sh` lines 23-24 and 84-88).
- `bash tests/suites/smoke/run.sh` runs only `pw_specimen_smoke.sh`: one of
  the suite's three cases, not the standard-runner specimen and not the
  opt-in caller-auth case.
- `bash tests/suites/witness_contract/run.sh` lists 36 top-level scripts and
  none under `opt_in/`; `runner_exec_lifecycle/run.sh` loops over its four
  default identifiers; `runner_c_worker_harness/run.sh` covers its 46 shared
  cases while `native_clock` has its own script.
- Opt-in cases with their own scripts (`runner_unit/opt_in/*.sh`,
  `witness_contract/opt_in/*.sh`, `runner_byoxpc/opt_in/*.sh`,
  `native_clock.sh`, `mutations.sh`, `host_setup_oracle_sensitivity.sh`,
  `closed_streams_leader_exit.sh`, `closed_worker_stderr.sh`,
  `pw_runner_caller_auth.sh`) are reachable directly by path.

Registry membership control. `tests/suites/dispatcher/check_selection.py`
lines 30-47 and 350-371 (`opt_in_problem`) run the real `--suite opt_in
--list` and require the requested set to equal the catalog's non-default set
and the full selection to equal its dependency closure. This default-battery
control is the one mechanical check that binds the `opt_in` include list to
the `default` flags. The related `shell_helpers/mutation_prerequisites`
control (`check_mutation_prerequisites.py`) exercises the direct
`order_barrier_mutations` wrapper's refusal without an identity.

### B.7 Scripts and manifests outside the catalog

- Every literal case identifier found in the suite scripts (135, by a
  pattern match over `test_begin`, `test_selected`, `run_harness_case` and
  `for test_id in` lists) is a catalog case. The match cannot see identifiers
  built from variables, so it establishes no absence of unregistered
  identifiers; it found no positive instance.
- The menagerie manifest `tests/fixtures/blackbox_menagerie/cases/core.json`
  has 8 `case_id` entries, equal to the 8 menagerie specimen cases; the two
  `tests/fixtures/blackbox_e2e/BBX-*` directories match the two BBX cases.
- Two Python files under `tests/suites/` are named by no catalog command and
  by no shell script: `blackbox_e2e/extension_controls.py` and
  `runner_exec_lifecycle/exec_observation.py`. Both are imported as modules
  (`blackbox_e2e/checker_controls.py` line 237;
  `runner_exec_lifecycle/check.py` line 14, `check_edges.py` line 16 and
  `check_closed_streams_leader_exit.py` line 22) and are reachable through
  default cases. Nothing under
  `tests/suites/` was found to be unreachable.
- `tests/atlas/` holds a plan document, not tests. The harnesses under
  `records/performance/` are investigation equipment outside the test
  system and are not registered anywhere; `records/performance/README.md`
  says so.
- `source_drift/check.py` lines 258-260 fail the default battery if the set
  of `tests/suites/<name>/` directories differs from the catalog's suite set,
  so an unregistered suite directory cannot exist silently. No check reads
  `tests/OPT_IN_TESTS.md`.

### B.8 Inventory gaps

- Swift block count (277) is a count of `tk.run(` call sites, not a count
  from an executed summary line; blocks inside loops or helpers would differ.
- Equipment agreement between registry and catalog was established by
  reading, not by a parser, because registry entries use several identifier
  forms (`Case:`, `Cases:`, `Suite/case:`, `Suite name:` with or without a
  case name).
- No case was executed, so nothing here establishes that a selectable case
  currently passes, or that its equipment probe succeeds on this machine.

## C. Discrepancies and uncertainties

### C.1 Confirmed: documentation describes mechanisms or states no longer in use

1. `tests/suites/unit/disposition_reds.sh` lines 7-12 say the case is
   "Non-default", that the four Rust tests "carry `#[ignore]`", that it keeps
   "the default battery green while `--all` and `--suite opt_in` still exercise
   them", and that it is "Red by design until the controller change lands. See
   `tests/OPT_IN_TESTS.md`." Its red-path failure message (line 52) repeats
   "expected until the controller change lands". The catalog has had the case
   default since `0ed4ae7` (2026-09-27), the registry has no entry for it, and
   the four functions in `controller/src/disposition.rs` (lines 2132-2216)
   carry no `#[ignore]`. The sibling `byoxpc_reds.sh` was updated at its
   promotion ("promoted from red"); this one was not. The selection is correct;
   the in-script account is stale.
2. `tests/OPT_IN_TESTS.md` lines 531-546 (the entry template and exit rule)
   predate the catalog: "Location: the script path under
   `tests/suites/runner_*/opt_in/`" and "move the test into the smoke suite and
   remove it from this registry" are unchanged since `d74bef1` (2026-01-12).
   At this revision 16 of the 39 cases have scripts under an `opt_in/`
   directory and 23 do not; the `smoke` suite is one owning suite among nine.
   Four registry entries (`single_use`, `bad_neighbor_claims`, `feasibility`,
   `default_location`) follow the template section instead of preceding it.
3. The criterion "unstable in CI" (line 18) names an environment the
   repository does not have. It is also unchanged since `d74bef1`.
4. The criterion "Is a specified red test for planned behavior" (lines 22-24)
   has no current instance. Every registered red was promoted in place within
   hours or days (D.3), and the last one's case was removed on 2026-10-23. The
   convention's only remaining traces are the generic bullet and the stale
   comment in item 1.
5. `tests/FAILURE-PROPAGATION-CONTRACT.md` lines 1461-1463 state that
   acceptance selects every registered case including opt-ins and both runner
   contexts. No implemented entry point does so: release acceptance runs two
   cases (`tests/lib/release_accept.py` line 19), `make release` runs the
   default battery, and only a manual `--all` selects everything. The sentence
   was added by `3a914e7` (2026-09-26) and the document does not define which
   acceptance it means. Whether this is an unmet obligation or a statement
   about change acceptance by hand is an interpretation this survey cannot
   settle.

### C.2 Confirmed: registry entries without a stated opt-in reason

Four entries have no "Opt-in reason" field although the template requires
one: signed artifact controls (`preflight/signed_artifact_controls`), built-in
caller authentication (`smoke/runner_caller_auth`), BYOXPC single-use
admission (`runner_byoxpc/single_use`) and Native sandbox extensions
(`sandbox_extensions_native/feasibility`). Each lists a Developer ID identity
among its equipment, so the reason is inferable from the criteria list, but it
is not stated.

### C.3 Confirmed: selection behavior that differs between entry points

6. Direct suite scripts ignore default membership (B.6). The README documents
   that direct scripts lack the public command's planning and completion
   guarantees; it does not say that a direct preflight invocation runs the
   opt-in build controls, or that a direct smoke invocation runs one case of
   three. These follow from the documented contract rather than contradicting
   it.
7. Cargo's `#[ignore]` and the project's opt-in status point in opposite
   directions for two tests (B.5): ignored under `cargo test`, run by a
   default catalog case. The attribute text explains it; the registry, which
   describes non-default work, has no reason to list them, and the unit README
   does not mention them. A developer running the standalone Cargo command
   the AGENTS guidance names sees two ignored tests with an explanation and no
   way to run them without the Swift receipts.
8. Whole-suite selection carries the suite's opt-in equipment: `--suite
   smoke` needs an identity, `--suite preflight` needs Rosetta, a signing
   identity and every toolchain, and the failed-run-with-unrun-cases rule
   applies when any of it is absent. The README says so for `smoke` and in
   general (lines 62-64, 363); `tests/atlas/ATLAS-BUILD-PLAN.md` line 508
   warns against selecting the whole witness suite for this reason. This is
   the documented design, with a cost that falls on anyone who reads a suite
   name as its baseline content.

### C.4 Mechanical limits that are not defects

9. The `opt_in` include list duplicates information already in the `default`
   flags. Drift is caught by the `dispatcher/test_command_controls` oracle
   when the default battery runs, not when the catalog is edited.
10. The README tier check is one-directional (B.4).
11. The registry's alignment with the catalog is a manual obligation
    (`tests/AGENTS.md` line 115) with no reader: no check parses
    `tests/OPT_IN_TESTS.md`, and its entries have no fixed key. At this
    revision the coverage is complete (every non-default case is documented
    individually or by the `runner_byoxpc` suite entry, and no default case is
    documented as opt-in; `shell_helpers/mutation_prerequisites` is named only
    as the control that guards a direct wrapper).

### C.5 Faithful implementation whose intended applicability is unclear

12. `preflight/translated_build_refusal_controls` is opt-in because Rosetta
    is optional equipment. Under the catalog's rules a missing requirement
    fails the run, so a default case with an optional requirement would fail
    the battery on machines without it; the registry states this reason
    exactly. The criteria list does not contain "optional equipment", and the
    same reasoning would apply to `meson`, which two default `source_drift`
    cases require. Whether Rosetta is different in kind from Meson is a
    policy question the sources do not answer.
13. Seven cases are opt-in because they are exploratory or characterize an
    observation without asserting product behavior
    (`host_setup_oracle_sensitivity`, `closed_streams_leader_exit`,
    `closed_worker_stderr`, `launch_inventory`, `path_query_observations`,
    `path_query_integrated`, `native_clock`). Their entries say so; the
    criteria list has no such criterion, and the README tier definition
    ("resource-sensitive signing/launchd work or implementation mutation
    controls") does not cover them.
14. Four cases are opt-in because they mutate and rebuild implementation
    sources with anchors that must be reviewed when the implementation changes
    (`mutation_controls`, `order_barrier_mutations`, `exec_reader_mutations`,
    `reaped_ack_mutation`). The README tier definition names this class; the
    criteria list does not. `order_barrier_mutations` is also the one opt-in
    case the AGENTS guidance requires to be rerun on specific changes, which
    makes it mandatory under conditions while remaining non-default.
15. `runner_byoxpc/default_location` is opt-in in part because it touches the
    shared default registry and the real user LaunchAgents plist, a
    shared-state reason distinct from its equipment.

### C.6 Not established

- Whether the four registered reds were ever executed red through the
  dispatcher before promotion, or only through direct Cargo selection; the
  commits do not say and no retained run covers them.
- Whether any opt-in case currently passes on this machine (none was run).
- The original reason `mutation_controls` and `runner_caller_auth` were made
  non-default at `ed922f7`: the registry entries give reasons, but both
  entries were written in the same commit that introduced the flag, so the
  reason and the status cannot be dated separately.

## D. Historical findings

### D.1 Opt-in began as a directory, became a flag

At `d74bef1` (2026-01-12) the registry defined opt-in tests as scripts under
`tests/suites/opt_in/`, invoked directly, "excluded from the default
`tests/run.sh --all` run", and said "There is intentionally no `opt_in` suite
runner". The criteria list (five bullets), the "unstable in CI" phrase and the
"move the test into the smoke suite" rule all date from this commit. The five
scripts that lived there (`pw_lab_tui_pty.sh`, `pw_runner_specimen.sh`,
`runner_instrumentation_dylib.sh`, `runner_instrumentation_dyld_env.sh`,
`runner_machme_smoke.sh`) were all removed by `fac72d5` (2026-05-30); none of
the TTY, network or instrumentation reasons they carried survives in the
current population. `67baf3a` (2026-01-18) added an `opt_in` suite runner
despite the earlier sentence.

`ed922f7` (2026-09-15, "Make test selection explicit and account for every
selected case") introduced `tests/catalog.json`, the per-case `default` flag,
the `opt_in` include group (then 15 members: `mutation_controls`,
`runner_caller_auth` and 13 `runner_byoxpc` cases) and rewrote the registry's
header and "How to run" sections to the catalog mechanism, keeping the
criteria list verbatim. The template and exit rule at the end of the file
were not revised then or later.

### D.2 Every current opt-in case was born opt-in

Walking every commit of `tests/catalog.json`, each of the 39 current
non-default cases was `default: false` in the commit that first registered it
and in every commit since. No current opt-in case was demoted from the
default battery, and none inherited its status from a suite other than the
`runner_byoxpc` cases, whose suite-level `default: false` has been in place
since `ed922f7`.

### D.3 The red-test convention was used three times and left no instance

- `1b1868d` and `831596b` (2026-09-27) added the "specified red test" bullet,
  then citing `controller/DISPOSITION-RECORD-PLAN.md`, and registered three
  reds non-default in place: `witness_contract/worker_attempt_in_flight_at_deadline`,
  `unit/rust.disposition_reds` and `runner_unit/disposition_reds`. The entry
  stated that they live beside default cases "because each is promoted in
  place". `0ed4ae7`, the same day, promoted all three, dropped the `#[ignore]`
  attributes and the Swift `PW_DISPOSITION_REDS` gate, and removed the entry;
  the `runner_unit/disposition_reds` case no longer exists. The script
  comment in `disposition_reds.sh` was not updated.
- `5240a6a` (2026-10-06) registered `unit/rust.byoxpc_reds` red; `7de5062`
  the same day promoted it and the script was reworded.
- `7183d37` (2026-10-21 22:26) registered `unit/rust.read_fresh_reds` red,
  citing `tests/READ-FRESH-PLAN.md`; `4ec0a52` (22:32) promoted it;
  `19e580b` (2026-10-23) removed the case with the unified-log observer.

In each use the red period lasted hours; the generic bullet remained after
the plan-specific wording was dropped.

### D.4 Last recorded executions of opt-in cases

`tests/RETAINED.json` (committed) indexes runs whose reasons name opt-in
work: `apple-silicon-repair-optin-1` and `-2` (2026-10-19; signed-artifact,
build guard and refusal controls), `observer-retirement-build-controls-01`
and `observer-retirement-refusals-02`/`-03` (2026-10-24). The run directories
under `tests/out/runs/` are ignored by git and exist only in this checkout.
No retained run records a BYOXPC, path-query, native-clock or launch-inventory
execution; their most recent executions, if any, are not indexed.

## E. Questions left open

1. Is the red-test convention still policy? It has been used three times,
   always for hours, and has no instance now; the bullet, the stale
   `disposition_reds.sh` comment and the template's silence about in-place
   location are its remaining traces.
2. What does "Acceptance selects every registered canonical case ...
   including opt-ins" in the failure-propagation contract bind? If it is a
   release obligation, no entry point implements it; if it is a change
   acceptance obligation, nothing names who runs `--all` or when.
3. Should direct suite scripts honor default membership? A direct
   `preflight/run.sh` runs the heavy opt-in build controls, while a direct
   `smoke/run.sh` runs one of three cases. Both are consistent with "direct
   scripts are developer entrypoints without guarantees", and neither is
   stated.
4. Is manual alignment of the registry enough? Twelve cases are documented
   only through a suite-level entry, four entries omit their reason, and no
   check reads the file. The membership oracle guards the include list, not
   the prose.
5. Which criteria does the project mean to keep? The current population's
   recorded reasons fall into equipment (Developer ID, GUI session, Rosetta),
   cost (multiple or fresh builds), telemetry (unified logging), review-bound
   mutation controls, exploratory characterizations with no product
   assertion, and shared default state. The registry's list names the first
   three and reds; the README tier names equipment and mutation; the `opt_in`
   README names equipment, mutation and exploration. The inventory contains
   distinctions the present convention does not express, and the sources
   disagree about which ones count.
6. Is "optional equipment" a reason on its own? Rosetta makes one case
   opt-in; Meson is required by two default cases. The sources do not say
   what distinguishes them.
