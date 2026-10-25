# Test work survey: revision 31b8195

A read-only account of what PolicyWitness's tests and test-like procedures
do, what a passing result establishes, what a failing result establishes or
fails to establish, and where activities that share the name *test* do
different jobs or where differently named activities do the same job. It
describes the tree at one revision. It proposes nothing; findings are
statements about what a check does and does not do, cited to its lines.
Catalog-case accounting is complete; the [survey plan](../../tests/TEST-WORK-SURVEY-PLAN.md)'s
representative reading inside every batch group is not. The inspection limits
below apply to all claims about coverage.

## 1. Scope and coverage

### Revision, tree and method

- Examined revision: `31b81951c9c8c4124089aa4dd342b2b63c0a86de` ("Record that
  the survey plan's reference counts hold through f1e96a2", 2026-10-25
  09:24 -0700), the tip of `main` when the survey began.
- Inspected in a detached worktree of that commit under the session scratch
  directory. At the start `git status --porcelain` was empty there,
  `tests/out` did not exist and `tests/.checkout.lock` did not exist. The
  same observations were repeated before the worktree was removed ("Footprint"
  below).
- Executed in the worktree: `./tests/run.sh --list` and `./tests/run.sh --all
  --list`, which print the selected plan and return before the checkout lock
  is taken (`tests/lib/test_cli.py:169, 210-212`); read-only `git log`, `git
  show`, `git diff`, `git blame`, `git merge-base`; `grep`, `sed`, `find`,
  `wc`, `diff`; and Python with `-I -B` for parsing JSON and counting. The
  dispatcher's own catalog loader (`catalog()` and `select()` in
  `tests/lib/test_cli.py`) was imported to derive membership with suite-level
  inheritance. No catalog case, build, `cargo`, `swift`, `meson` or prune
  command was run. The command record is retained with the survey's notes
  outside the checkout.
- Compilation of the per-case ledger: five parallel read-only passes over
  disjoint suite sets wrote one row per case (command, entry point, what is
  started, what is read before asserting, where the decisive assertions live
  with line citations, reachable terminal paths, equipment handling, side
  effects, documentation discrepancies). The author merged the rows, confirmed
  one row per plan ID, resolved a random sample of citations against the
  worktree (269 of 284 citations in a 40-row sample resolve to an existing
  file and line range; the other 15 are abbreviated paths the resolver
  did not search, and the files exist), re-read 20 rows from all five passes
  beside the source text at their cited lines. Citation resolution establishes
  that a location exists, not that it supports the row's interpretation.
  Section 2 contains fourteen investigations (2.0 through 2.13).
- Review used a second detached worktree at the same revision, traced the
  findings to their assertions and shared helpers, and recounted the Python
  groups without importing or executing their tests. Appendix A preserves
  the original per-case inspection levels; subsequent targeted reading is
  identified in Appendix B. Neither the original survey nor the review ran
  a case or credited a runtime result.
- Older accounts: the opt-in survey (`records/tests/OPT-IN-REPORT.md`)
  examined `2f23cad`, thirteen commits earlier; the intervening commits are a
  wording change, the commit recording that survey, the test-execution
  consolidation (`bcc21fa` to `87d5fb2`, which closed direct invocation of
  case scripts and moved the release battery into acceptance) and six commits
  to the survey plan. Its counts were re-derived here, and its claims are
  used below only as comparison texts.

### Levels of granularity and the population

| Level | At `31b8195` | How counted |
| --- | --- | --- |
| Public interface | `tests/run.sh`; `make test` forwards with no selectors; `tests/accept-release.sh` runs the default battery against an extracted release ZIP | `tests/run.sh`; `Makefile` targets `test`, `notarize`, `release`; `tests/lib/release_accept.py` |
| Suites | 42 in `tests/catalog.json`: 41 with cases, plus the `opt_in` include group of 39 | `catalog()` |
| Canonical cases | 235; 196 default; 39 non-default; 216 standard context, 19 BYOXPC | `--all --list`, `--list` |
| Command scripts | 111 distinct; 96 cases have their own script; 139 share 15 multi-case drivers | `command[1]` over the `--all` plan |
| Largest drivers | `runner_c_worker_harness/run.sh` 46; `runner_use_c_worker/run.sh` 14; `preflight/run.sh` 12; `runner_byoxpc/run.sh` 12; `blackbox_menagerie/run.sh` 9; `source_drift/run.sh` 8; `shell_helpers/run.sh` 8; `failure_boundaries/run.sh` 7; `dispatcher/run.sh` 6 | same |
| Dependencies and skips | 12 `depends_on` edges; 16 cases declare `annotated_mismatch_absent`, the only declared skip reason | catalog |
| Equipment | 24 cases need nothing; 49 cases have `requires` differing from their suite's; nine recognized names (`test_cli.py:56`) | plan |
| Rust functions | 223 `#[test]`: 198 in `policy-witness`, 11 in `sbpl-check`, 14 in `cli_contract.rs`; 2 `#[ignore]` | static grep |
| Swift blocks | 277 `tk.run` call sites in 32 registered `run*Tests` functions, 55 `tk.group` groups | static grep |
| Python `unittest` methods | 68 in 16 test-bearing classes in `preflight/check_build_provenance.py`; 137 in 15 classes across the seven `source_drift` modules; one `def test_` each in the three opt-in build drivers | AST enumeration of methods and their containing classes; the provenance module also has a method-free `StampFixture` base |
| Scenario tables | `harness.c` rows behind the 46 harness cases; `comparison/matrix.json` rows; the menagerie manifest's 8 specimens; the build manifest's refusal list; the shared `contract/*.json` corpora | fixtures |

The catalog counts equal the reference counts the plan recorded at `87d5fb2`;
the commits between changed only the plan file (`git diff --stat
87d5fb2..31b8195`). The provenance class count includes the three test-bearing
subclasses of `StampFixture`, and excludes that method-free base. Counting
only direct `unittest.TestCase` subclasses gives fourteen, not the number of
test groups.
Twenty-two cases have no `description` in the catalog; the loader shows the
ID with underscores replaced by spaces (`test_cli.py:37`).

### Procedures that are not catalog cases

- Release acceptance (`tests/accept-release.sh` → `tests/lib/release_accept.py`
  `accept`, lines 77-164): inventories the extracted app, validates the
  staple, assesses with Gatekeeper, runs `tests/run.sh` with no selectors
  against the extracted app under a 7200 s bound, requires a passing default
  battery against that app with no skips, unrun cases or harness errors
  (`battery_problems`, 35-58), reads two battery envelopes to require
  `runner_kind == standard` (25-27, 117-122), re-inventories, and prints a
  retention entry. `preflight/release_controls` exercises acceptance with
  faked tool replies (2.2); the other release controls test deadlines,
  publishing and rotation.
- The dispatcher's artifact gate (`tests/lib/suite_run.py:412-432, 496-511`):
  `artifact.inspect` and `artifact.inventory` before any case needing `app` or
  `worker`, the `app` and `worker` equipment credited only when the inspection
  passed (432), inventory again at the end. `preflight/codesign.preflight`
  runs the same inspector as a case (2.7).
- `make test`, `make notarize`, `make release` (`Makefile:120-206`): the first
  forwards to `tests/run.sh`; the others build, submit, staple and call
  acceptance; none selects cases.
- Standalone `cargo test` and `swift run PWRunnerCoreTests`: local debugging
  of the crate or package under the tool's own rules; `tests/README.md:238-246`
  says they are not runs of any catalog case.
- `records/performance/` harnesses: historical investigation equipment for a
  retired application (`records/performance/README.md`); not registered, not
  inspected. `tests/build-evidence.py` is a build tool and
  `tests/compare_json_fixture.py` a two-file JSON differ; neither is a test.

### Inspection levels

Every one of the 235 cases has a scratch ledger row stating what its command runs,
what it reads before asserting, where its decisive assertions are (with line
citations), its reachable terminal paths and how equipment failures are
reported. Appendix A maps every canonical ID to its inspection level. These
are levels of reading, not a classification of test purposes:

| Level | Cases | What it means |
| --- | --- | --- |
| Read individually | 163 | The case's own script or branch and its checker were read to the decisive assertions. |
| Read through its driver function | 38 | One branch of a multi-case driver; the shared driver, the branch and the shared helper were read once. |
| Pointer to a table or batch | 23 | The driver and checker were read; per-case expectations are rows of a table or members of a batch: the 8 menagerie specimens and their 8 BYOXPC copies (manifest rows), `comparison_matrix` and `extension_combinations` (matrix rows), `rust.unit` (209 functions counted per module, bodies not read), `cli.integration` (14 functions named, one gate body read), the Swift executable (32 functions named from the registry with their comments; `TestKit` and every equipment guard read; bodies not read), `clock_arithmetic` and `proceed_precedence` (the C fixtures' headers and assertion excerpts). |
| Groups partly read | 11 | Large Python checkers whose classes or scenario functions were enumerated and partly read: `build_provenance_controls` excerpts from 6 of 16 test-bearing classes (68 methods); `build_refusal_controls` 3 of 49 control functions plus its tables; `release_publish_controls` 1 of 4 scenario functions fully; `release_rotation_controls` 2 of 9; seven `source_drift` cases with selected methods or rules read, and `build_rules.py` and the planner's `main` read in full. |

The original notes enumerate 21 Rust test-bearing files, the 32 registered
Swift functions with their comments and 55 group names, and Python classes.
Reading a Rust test's `#[ignore]` attribute or a Swift equipment guard is
not reading that member's assertions. The original passes did not read a
representative body in every Rust, Swift or Python group, and did not identify
every differently marked member for assertion reading as Stage 1 requires.
Appendix B records the available group-level accounting and its gaps. These
limits prevent claiming completion of that part of the plan.

### Limits of inspection

- Static counts: `tk.run` call sites and `#[test]` attributes are counted in
  source; a block inside a loop would run more than once and is counted once.
- No case was executed, so nothing here says a case passes on this machine.
  Retained runs in the original checkout were not consulted for results.
- BYOXPC, signing and build-driving cases were read, not run; their equipment
  paths (launchd, keychain, notarization stand-ins) are described from code.
- Inside the native control fixtures (`clock_control.c`, `proceed_control.c`,
  `terminal_control.c`, `first_touch_control.c`, `exec_control.c`) and the two largest Python drivers
  (`build_refusals.py`, `check_build_provenance.py`), assertions were read at
  group level and by excerpt; per-property coverage there is accounted for by
  pointer to the fixture, not established.
- Where a pass's own words are quoted (registry, README, script comment), the
  quotation is the document's claim; what the code asserts is stated beside
  it.

## 2. Representative investigations

Each account states operational facts first (what runs, what is read, how
the result is recorded), then what a pass supports and leaves open, then what
a failure establishes, in the vocabulary the code implements. Citations are
repository-relative paths at the examined revision.

### 2.0 How a result is recorded, and a gap in the recording

A case ends with `test_pass`, `test_fail` or `test_skip`
(`tests/lib/testlib.sh:269-292`), each writing a terminal event and a
`report.json`; `test_fail` exits 1 immediately. The dispatcher
(`tests/lib/suite_run.py`) separately produces `unrun` for missing equipment
or a failed dependency, the harness errors `unexpected_skip` (348-349),
`unrun_case` (350-351), `suite_exit` (469-470), `case_end` and
`missing_report` (101-110), `reused_case`, `interpreter_mismatch`,
`build_tree_in_evidence` and `scratch_retained`; an artifact-integrity
failure independent of case statuses; and a `system_sleep_ms` record whose
nonzero value marks a failure as not creditable product evidence without
changing its status (`tests/suites/dispatcher/README.md`, "Contract"). Every
standard-context case runs in its own invocation; only consecutive BYOXPC
cases sharing a command are grouped (`execute`, 387-393). These are the
implemented vocabularies for "the machinery failed" and "nothing was
established"; the report uses them rather than inventing others.

Nine assertion blocks in eight default case scripts bypass the case-level
`fail` path. Each runs the CLI inside `set +e`/`set -e`
and routes an unexpected CLI exit to `test_fail`, then runs its envelope
assertions as a bare Python heredoc with `errexit` active and no handler:
`runner_apply_isolation_v2/run.sh:53-91`, `_v3` the same,
`runner_outcome_bad_request/run.sh:65-97` and `158-190`,
`runner_outcome_worker_spawn_failed/run.sh:62-110`,
`runner_ready_byte_resilience/run.sh:84-154`, `smoke/pw_specimen_smoke.sh:44-93`,
`smoke/pw_specimen_smoke_standard.sh:40-52` and
`witness_contract/happy_path_baseline.sh:46-73`. A failed assertion raises
`AssertionError` or `SystemExit`, the script exits without a terminal event, and the dispatcher
records `suite_exit`, `case_end`, `missing_report` and `unrun_case`; the
case's result is `state: unrun, status: null` and `run.json.ok` is false. The
failure is not hidden, but it is recorded as a failure of the machinery: a
reader of `run.json` alone cannot distinguish an envelope assertion failure
in these nine default cases from another script error. The affected cases are the two apply-isolation
cases, two of the three bad-request cases, the spawn-failure case, the
ready-byte case, both smoke specimens (and the BYOXPC copy of the first,
which reuses the script) and the witness baseline: ten canonical cases in all.
Release acceptance reads the first smoke case and the witness baseline for
`runner_kind`; acceptance would still
fail, through `battery_problems`' "harness errors" and "not every selected
case completed" rules. Other scripts route inline assertions through a
captured status, an `if !` (`runner_abi_layout/run.sh:64-267`), or
`test_check_python`. This finding concerns the named assertion blocks, not
every setup command that could exit without a report.

Two further recording facts set the meaning of equipment failures. Reachable
`test_skip` calls exist in scripts whose cases declare no skip reason (the
harness and C-worker drivers on a failed fixture build or a missing ABI
header, `runner_c_worker_harness/run.sh:48, 853`, several sites in
`runner_use_c_worker/run.sh`); under the dispatcher such a skip is the
`unexpected_skip` harness error. The dispatcher normally pre-empts in-script
`require_pw_app` skips: every such case requires `app`, credited only after
artifact inspection. A later disappearance or permission change can still
reach an in-script missing-app path.

### 2.1 One specimen, three claims

Three default cases run a single-step specimen through the signed CLI and
pass on an envelope. Their scripts share a shape and establish different
things.

`smoke/specimen_file_read_deny` (`tests/suites/smoke/pw_specimen_smoke.sh`)
copies the `specimen_file_read_deny.json` fixture through
`render_specimen_with_runner` (`tests/lib/testlib.sh:396-430`, which injects a
runner selector only when a BYOXPC wrapper set `PW_TEST_RUNNER_MODE`), runs
`policy-witness run`, and requires: `kind == run`; the envelope's
`build.version/number/describe/commit` nonempty and equal to the app's
`Info.plist`; `result.ok`; `runner_result.schema_version` equal to
`contract.RESPONSE_SCHEMA` and `worker_evidence.abi_identity` equal to
`contract.WORKER_IDENTITY`; one step; `sandbox_check.outcome == deny`;
`attempt.get("rc") != 0` and a non-null errno (48-93). The rc check admits a
missing rc and neither field's numeric type is checked here. Its comment names the last two
as the point: "Witness the OBSERVED denial, not just the validator's
predicted verdict". `assert_runner_kind` (`testlib.sh:431-451`) then checks
the runner kind only when `PW_TEST_RUNNER_EXPECT_KIND` is set, which the
BYOXPC wrapper does.

A pass supports agreement between reported build fields and the selected
bundle's metadata, and equality of two reported contract identifiers. These
are not byte-identity checks or full schema validation. For the
`(deny file-read-data)` specimen the envelope reports a deny prediction and
attempt fields accepted by the above failure checks. It leaves open whether the
failure was the sandbox's (any errno is accepted), what the comparison record
says (not read), and the runner selection in the standard context.

`smoke/specimen_file_read_deny_standard` (`pw_specimen_smoke_standard.sh`)
copies the same fixture unchanged, runs the CLI, and requires only `kind ==
run`, `result.ok` and `runner_provenance.runner_kind == "standard"` (40-51).
No step field is read and no `runner` key is set. A pass supports that a plain
run selected the bundled standard runner and completed. The catalog describes
it as "Explicit standard runner returns the expected file denial"; the script
sets no explicit runner and asserts no denial. The two smoke cases are the
same fixture and the same CLI invocation, sharing `kind` and `result.ok`
checks but adding different assertions.

`witness_contract/happy_path_baseline` (`happy_path_baseline.sh`) generates an
`(allow default)` specimen with one `open_read` and requires `result.ok`,
`normalized_outcome == ok`, one step, `sandbox_check allow`, `attempt.rc ==
0`, a non-empty `observed_path` and an integer `runner_subprocess.pid`
(44-70). A pass supports a report of a successful read with a nonempty
observed path; it does not independently observe bytes read.
`witness_contract/validator_subprocess_populated`
submits the same policy and probe plan under a different specimen ID and
asserts the validator subprocess fields instead.

`runner_use_c_worker/happy_default_allow` (`run.sh:37-115`) runs the same
specimen shape and requires `consumer.validate(env)` to return no errors;
`normalized_outcome == ok`, `rc == 0`; `phases[0].validator_subprocess`
present with exit 0; `runner_subprocess` present with exit 0;
`test_overrides` null; top-level `pid` equal to the worker's; one step with
`sandbox_check allow`, `attempt.outcome ok`, `observed_path ==
/private/etc/hosts`, and a comparison record `observation: succeeded`,
`order: query_first`, empty `limitations` (75-104). The suite README (31-32)
and the catalog say it also asserts `matched` and `same_submitted`; the
inline block does not, and those relations are checked only generically by
the shared reader against raw fields (`tests/lib/consumer.py:472-477`). The
cases make different claims over one kind of run; the first smoke case
also compares build metadata and contract identifiers. Release acceptance
reads `smoke/specimen_file_read_deny` and
`witness_contract/happy_path_baseline` to require the standard runner
(`tests/lib/release_accept.py:25-27, 117-122`).

### 2.2 "Controls": one word, several jobs

Forty-two case IDs contain `control` or `mutation`. Five, read to their
assertions, do different work.

- `blackbox_menagerie/validation_controls` (`checker_controls.py`) runs the two
  black-box checker CLIs on fabricated envelopes with no app and requires each
  to accept the right document and reject each wrong one, including a later
  failure's precedence over a pending mismatch skip (218-234). Evidence about
  the checker's sensitivity.
- `runner_exec_dac/execute_permission_controls_spawn` (`check.py:36-92`) runs
  the exec helper directly with execute bits removed and restored, recording
  spawned/exit or errno (45-49) before each PolicyWitness run, then requires
  the direct records exactly (66-68) beside the envelope's `exec_failed` with
  EACCES, `child_pid 0`, `posix_spawn` in the error and a
  `permission_failure`/`permission_errno` record with no sandbox attribution.
  Here "controls" are experimental baselines performed outside PolicyWitness.
- `validator_bridge/protocol_controls` (`run.sh:5-12`, `check.py`) builds a
  test-only native bridge and an exec helper, calls `sandbox_check` through
  `ctypes` as the native oracle (17-29) and drives the bridge through a socket
  gate requiring readiness before stdout, receipts before emission, exact
  native records and closure behaviour. No PolicyWitness process. The README:
  "equipment controls, not evidence that the runner obeys its barrier".
- `preflight/release_controls` (`check_release.py`) imports the real
  `release_accept.accept` and `notarize.py`, drives them with fake tool
  replies (`tests/fixtures/release/tools.py`) over notarization modes
  (`accepted`, `agreement`, `unknown_submit`, `pending`, `rejected`) and
  archive modes (`valid`, `missing_helper`, `stale_manifest`, `missing_staple`,
  `corrupt_zip`), and requires acceptance only for `valid`, no
  `selected_cases`, and the 7200 s bound (107-179). Evidence about release
  tooling under faked replies.
- `dispatcher/controls` (`check.py:14-30, 53-83`) installs a copy of the public
  runner into a fixture repository and runs the real `tests/run.sh` over
  fixture suites that pass, skip, crash, exit silently, write malformed
  reports, leave `.build` trees or scratch, requiring the exact `run.json.ok`
  and harness-error codes for each. Evidence about the dispatcher's
  reconciliation.

Mutation controls (2.5) are a sixth sense. "Controls" therefore names at least
five jobs: checker sensitivity on fabricated input, an experimental baseline
beside a live run, equipment verification, tooling verification under fakes,
and detector sensitivity under source mutation. Both the DAC baseline case
and the barrier mutation case run PolicyWitness specimens. The word
"validator" likewise names two
programs: `validator_bridge` tests a test-only Objective-C bridge
(`tests/fixtures/validator/bridge.m`), while `validator_batch_mode` runs the
shipped `sb_api_validator`.

### 2.3 A documentation check inside a live suite

`witness_contract/attempt_outcome_matrix_enforced`
(`tests/suites/witness_contract/attempt_outcome_matrix_enforced.sh`) needs no
equipment. It reads `runner/Sources/PWRunnerCore/PWRunnerAPI.swift`,
`tests/COVERAGE.md` and `tests/suites/source_drift/check.py` as text and
makes four checks (20-62): the substring `enum AttemptOutcome` occurs in the
API file; `## Attempt outcome coverage matrix` occurs in the coverage
document; `AttemptOutcome` occurs in the drift checker; and the set of
`static let` constants inside the enum body equals the set of backticked
names in the first column of table rows, both found with regular expressions
over raw text, the rows between the heading and the next `## ` heading.

`source_drift/check.py` `check_attempt_outcomes_have_matrix_rows` (429-446)
compares the same two sets: the constants with the same regular expressions
(`_parse_swift_enum_constants`, 335-348), the names through the Markdown
reader (`required_section`, `section_rows`, `code_cell`, 283-333), which takes
table rows inside that section only and accepts a cell that is exactly one
code span. It runs inside `source_drift/runner_source_manifests_agree`.

The proposition "every AttemptOutcome constant
has a matrix row and every row names a constant" is asserted by both, over
the same two files, through different readers. Differential failures, from
the two parsers: a row-shaped line inside a fenced block or an HTML comment
under that heading counts for the regex and not for the reader. The witness
case's third check is a proposition the drift rule does not make, and a
string-presence test: `AttemptOutcome` occurs in `check.py` in the rule, in
`parse_attempt_outcomes` and in comments, so it would pass with the rule
deleted. History: the case arrived in `e1c42b5` (2026-05-29, "failing tests
as refactor spec") as item R13, "AttemptOutcome enum + matrix + source_drift
integration land together"; the drift rule arrived the same day in
`a1e5758`. It was a pre-registered specification that the integration exists
and has remained a default member. The witness README does not name it (one
of six witness cases it omits). The pair shares a proposition, but the parser
differences and extra check admit differential failures. It is therefore
not an overlap under the plan's stricter "same job" standard. The sources
read do not document the pair as independent checks by design.

### 2.4 Batch cases as populations, and a guarded block

`unit/rust.unit` (`tests/suites/unit/run.sh`) runs `cargo test --bins` and
passes only on exit 0, retaining one log. Its source population has 209
functions, two ignored by this ordinary invocation; the case records only
pass or fail, and the log is the only
place a reader learns which function failed. `unit/rust.disposition_reds` and
`unit/rust.byoxpc_reds` select four and two of those functions by exact name
with `--include-ignored`, require that exactly that many ran, and classify
each result as green, red-with-expected-message, or unexpected
(`disposition_reds.sh:32-57`), failing on any red or unexpected. Their job is
failure classification of tests `rust.unit` also runs: an unexpected failure
is reported as "build, equipment or unrelated failure". The header of
`disposition_reds.sh` (7-12) still describes the case as non-default, its
functions as `#[ignore]`d and the case as "red by design until the controller
change lands"; the catalog makes it default, the four functions in
`controller/src/disposition.rs` carry no `#[ignore]`, and the header was last
changed in `5f6c619` (2026-09-27), the day the case was promoted.

`unit/run.sh:7-9` contains `if test_selected "rust.fmt"; then bash fmt.sh ||
true; fi`. Under the dispatcher this branch cannot run: `rust.fmt` has its own
catalog command and every standard case is its own invocation, so
`PW_TEST_CASES` for `run.sh` holds only `rust.unit`. The branch dates from
`82aeaef` (2026-09-26).

`runner_unit/pwrunner_core_unit_executable` (`tests/suites/runner_unit/run.sh`)
builds the lifecycle fixture, runs `swift run PWRunnerCoreTests`, fails on a
nonzero exit, on any line matching `^\s*(SKIP|FAIL)\s`, or on a missing `N/M
tests passed` summary (33-52), then replays the two `#[ignore]` Rust tests by
exact name against the Swift artifacts (55-67). The Swift population is 277
`tk.run` blocks in 32 registered functions. `TestKit.run`
(`TestKit.swift:35-60`) counts a block as failed when it throws and prints
`FAIL`; it has no skip state. Every equipment guard throws: `guard
workerExists() else { throw TestFailure("required equipment: ...") }` at
fifteen sites in `CWorkerTests.swift` (56, 88, 119, ...), `bothBinariesExist()`
at `CWorkerValidatorTests.swift:56-58, 160-162, 223-225`, and the
`PW_LIFECYCLE_WORKER_FIXTURE` guards in `CWorkerClockTests.swift:57-59`,
`CWorkerLifecycleTests.swift:10-12, 99-101`, `ExecObservationTests.swift:69-71`
and `DispositionResolverTests.swift:62-64`. Absent equipment is therefore a
`FAIL` line, which the wrapper rejects. The failure contract's sentence
"`TestKit.run` counts a guarded early return as passed"
(`tests/FAILURE-PROPAGATION-CONTRACT.md:643`) was written in `0670db1`
(2026-09-18 08:23) when the guards wrote `SKIP` and returned
(`CWorkerTests.swift` at `6885cb4^`, lines 43-46); `6885cb4` (14:06 the same
day) changed them to throw. The sentence was accurate for six hours. The
wrapper's `SKIP` grep now matches nothing TestKit emits; the only `SKIP` in
the test tree is the comment at `CWorkerLifecycleTests.swift:7` recording the
change. A passing Swift batch cannot silently credit those guards as passes
when their required worker, validator or lifecycle fixture is absent.
`report.json` gives no per-block accounting; the log identifies executed
blocks, and their source distinguishes production-worker, fixture-child and
constructed-input work.

Two other case wrappers map a tool's exit status to the case status and
nothing else: `unit/rust.fmt` (`fmt.sh:12-19`) and `integration/cli.integration`
(`run.sh:14-21`), so a compile error and a failing test are the same `fail`
with a log path. Every `cli_contract` test begins `if !integration_enabled()
{ return; }` (`controller/integration/cli_contract.rs:104-107`, fifteen
uses); `run.sh:9` exports `PW_INTEGRATION=1`, so under the dispatcher the 14
tests are enabled. A standalone `cargo test --test cli_contract` without
`PW_INTEGRATION=1` can report all fourteen as passed after early returns.
The `--include-ignored` flag in `disposition_reds.sh:29` and
`byoxpc_reds.sh:26` is now a no-op, since none of the six functions is
ignored. The runner_unit README (70-71) states the success criterion as exit
0 and a matching summary line; the script also fails on any `SKIP` or `FAIL`
line and requires the two Cargo replays to have run (44-48, 57-68). A
`FAIL` line in the Swift log may be absent equipment rather than a defect,
and the shell message does not say which.

### 2.5 Mutation controls and their unmodified baselines

`witness_contract/order_barrier_mutations` (`opt_in/mutations.sh` →
`opt_in/mutations.py`) runs a baseline stage before any mutant: it recompiles
the production worker source (`compile_worker`, `clang -O2 ... -lsandbox`),
runs the production Swift host driver against the ABI-compatible lifecycle
fixture in a copy of `runner/` whose `main.swift` is replaced by a one-test
driver, requiring exit 0 and `1/1 tests passed` (`driver`, 66-77;
`runner/Tests/PWRunnerCoreTests/OrderingTests.swift:69-88`), runs the C harness
scenario `proceed_delayed_observed_quiescence` against the rebuilt worker and
requires `applied`, `apply_rc 0`, `done`, exit 0, every slot completed with rc
0 and the proceed oracle accepting (`harness_control`, 79-91), rebuilds the
host with `swiftc -Onone -g` from the source list `meson introspect` reports
(`build_host`, `meson_host_sources`, 94-128), signs a copy of the selected app
with the rebuilt worker and host (`signed_copy`, 131-148), and runs
`held_effects` against that copy requiring no early unlink or exec connection
while collection is held (`cli_control`, 150-165). Each is an assertion that
fails the case. Then two mutants: a worker whose `wait_for_proceed` is
bypassed (`worker_source`, 32-39) must fail the harness oracle with
`early_completion` or `early_attempt` and must produce exactly `early unlink
while collection held` or `early exec connection while collection held` with
held-sample evidence; a host whose release is moved before its hook
(`host_source`, 42-49) must fail the Swift driver with `early worker
publication while hook held` and an `ack\nattempt` receipt. `replace_once`
requires each anchor to occur exactly once (29-31). The CLI observer must
reject both mutants (189-205). Finally the selected production app's
inventory must equal its starting inventory (209).

The unmodified controls are assertions in their own right. The Swift control
observes the host driver with a lifecycle fixture, the C harness observes a
rebuilt worker, and the baseline CLI run observes a rebuilt worker and host
signed into an app copy. Their compilation recipes do not establish the
behaviour of the selected app's unmodified host/worker pair. Other app
components are retained, and the worker-mutant CLI run retains the selected
app's host because `signed_copy` is called without a host replacement (195).
A pass supports each baseline assertion, rejection of the worker bypass by
the harness and CLI observers, rejection of the host bypass by the Swift and
CLI observers, and equal before/after inventories of the selected app. A failure
in a mutant stage can be a detector miss, anchor drift (`mutation anchor
changed`), a build/signing error or another unexpected execution failure.
Requiring specific rejection evidence prevents an unrelated error from
counting as successful detection; the diagnostics must be read to distinguish
those failures. `runner_exec_inheritance/mutation_controls`
has the same shape (`opt_in/mutations.py`, reusing `check.run_worker` from
the `contaminated_worker` case) and fails on any refactor that moves its two
anchors regardless of behaviour, which its README (54-55) says.
`runner_unit/exec_reader_mutations` and `reaped_ack_mutation` apply the
pattern to disposable copies of the Swift package (three and two
compilations, per the registry); the planner controls inside
`source_drift/runner_source_manifests_agree` (`check_planner.py:156-162`)
rewrite sources in a disposable checkout, run the real `check.py`, and
require the expected return code and diagnostic for each mutation before
confirming the working inputs are unchanged. `runner_unit/host_setup_oracle_sensitivity`
is the inverse: it runs the preserved `host_setup_controls` checker as a
`legacy` module against three deliberately wrong host variants and passes
only if that checker still accepts all 22 cases for every variant
(`host_setup_oracle_sensitivity.py:334-336`); a sharper oracle would fail it.
It pins the oracle's insensitivity, as 2.6's cases pin a limitation.

### 2.6 Passing by observing a counterexample

The registry calls seven non-default cases characterizations that assert no
product behaviour. Three read to their assertions:

- `runner_exec_lifecycle/closed_streams_leader_exit`
  (`check_closed_streams_leader_exit.py`): the docstring says it "pins a
  current observation limit, not desired process-tree containment".
  `observe_survivor` (34-45) requires that the leader's exit event was
  observed, that the descendant has not exited, that its identity and process
  group are unchanged and that it acknowledges a ping; the case also requires
  the helper paths, the child's parent and the worker executable's name
  (173-181). A pass requires the survivor: if PolicyWitness ever stopped the
  same-group descendant, this case would fail. It asserts a limitation as
  expected behaviour. `runner_exec_lifecycle/worker_dies_during_exec`, a
  default case, likewise passes only when the helper tree outlives the run
  (`check_edges.py:81`, "absence of publication is not proof of no spawn").
- `runner_c_worker_harness/native_clock` (`opt_in/native_clock.sh:70-112`)
  requires exactly 27 fresh-process rows, each reaped with exit 0, compiled
  and applied; for continuous-clock rows a valid timebase, every sample valid
  and none rejected, monotone elapsed values; it records `log show` status
  and fails if a deny record names a continuous-clock PID when records are
  available (108). The executable is a standalone probe compiled from
  `native_clock.c` with production clock helpers, not the shipped worker or
  a CLI run. Without log access the deny check has no records to inspect;
  the summary writes `deny_records: 0` beside the failing `deny_log_status`,
  which does not establish absence of denials. Old-clock failures are counted and
  reported, not asserted; that is the only part the registry's "need not
  recur" describes.
- `runner_exec_inheritance/launch_inventory` (`launch_inventory.py`): "an
  inventory, not an isolation oracle"; mandatory `ps`/`lsof` observations must
  succeed (113), `vmmap`/`lsmp` are retained either way; the envelope must
  show outcome ok, the worker pid, exit 0, reaped, `done_observed`,
  `collection_basis == after_confirmed_reap`, the ready byte received or not
  per seam, the override echoed, and the worker gone after reap (100-117).

The blanket claim that these cases assert no product behaviour is too broad:
the two CLI cases assert product lifecycle facts, while the native-clock case
asserts the applicability of production helpers in a standalone probe. The
survivor case requires its stated limitation. Neither a pass nor the registry's
label makes those observations general beyond the tested host and OS.
Old-clock failures, unlike the survivor, need not occur for a pass.
`witness_contract/path_query_observations`
is a different kind of member of the group: it never submits a PolicyWitness
request at all, running the shipped `sb_api_validator` against its own signed
native target (`check_path_queries.py:171, 200-217`).

### 2.7 Tests of the instrument

Some cases exercise the harness, builders, release tooling, generators or
readers without running a specimen through the selected app. Others rebuild
production code into controls, or invoke a nested live battery. The boundary
must be traced through fixture setup and imported helpers; a case's name or
an empty equipment list does not establish which programs it starts.

- `dispatcher/controls` runs the real public command in a fixture repository
  (2.2). A pass establishes reconciliation on the constructed evidence
  shapes. A failure requires diagnosing the affected accounting path or
  fixture before deciding which other results it calls into question.
- `shell_helpers/controls` `refusal_controls` (`check.py:133-181`) invokes real
  case scripts without the dispatcher's context and requires exit 2, the
  message `not started by the test dispatcher` naming `tests/run.sh --case`,
  and no output written; with context but an unselected ID the same script
  exits 0 silently.
- `preflight/codesign.preflight` (`preflight.sh:49-64`) runs
  `tests/lib/artifact.py` on the app and retains `preflight.json`. The
  dispatcher runs `artifact.inspect` and `artifact.inventory` on the same app
  before any case that needs it and credits `app` and `worker` only when the
  inspection passed. When the case runs, the same inspection has already
  passed once; when the initial inspection fails, the case requires `app`
  and is unrun. The case can still fail its later inspection if the app or
  inspection environment changes after the gate.
- `preflight/release_controls` models the release tool calls and the test command.
  The `Tools` fixture (`tests/fixtures/release/tools.py:60-70`) answers
  `stapler` and `spctl`, intercepts the `bash` call, requires its argv to be
  exactly `tests/run.sh` and writes the run record itself; the checker's
  "executed" assertion is over argv (`check_release.py:196-198`). A pass is
  evidence that the release code makes the recorded decisions on constructed
  archives and modelled replies. Its catalog `requires` is empty, yet the
  shell builds a clang fixture first (`preflight/run.sh:17-20`), so on a
  machine without clang the case fails rather than being unrun. Fixture
  preparation does invoke Apple tools, including clang and ad-hoc codesign
  (`tests/fixtures/dispatcher/build.sh:19-41`). Rotation controls reach the
  same compiler fixture through `make_release` → `make_dist` →
  `prepare_provenance_fixture` (`check_release_rotation.py:33-37`,
  `check_release_publish.py:194-200, 220-228`); their `clang` requirement is used.
- `preflight/build_refusal_controls`, an opt-in case, contains the default
  battery: `tests/fixtures/release/live_battery.py:38-58` runs the real
  `release_accept.accept` against a real build ZIP with only `ditto` and
  `bash tests/run.sh` permitted, and requires the nested `run.json` to be a
  passing default selection with no skipped or unrun cases. A default-battery
  failure anywhere fails this case; the real coupling between acceptance and
  the battery is tested here and only modelled in `release_controls`.
- Two layers for one rule: `runner_unit/sleep_record_controls` (Swift
  TestKit) and `dispatcher/accounting_controls` (Python `suite_run`) check the
  same clock-pair sleep rule (`sleep_record_controls.py:57-71`;
  `check_accounting.py:89-106`); `preflight/signed_artifact_controls` and
  `dispatcher/artifact_controls` inject near-identical bundle faults into
  `artifact.inspect`, the first with real `codesign` on copies of the real
  app, the second with fixture bundles; the `PYTHON*` refusal is asserted in
  `shell_helpers/python_startup`, `shell_helpers/interpreter_boundary` and a
  `check_build_provenance.py` class; the build's native-builder refusal is
  asserted in `source_drift/contract_versions`, `build_refusal_controls` and
  the provenance controls' shim gate.
- Equipment declared against equipment used: `codesign.preflight` and
  `dispatcher/{controls, accounting_controls, retention_controls}` inherit
  `clang` from their suites and compile nothing, so a clang-less machine
  leaves them unrun; `source_drift/runner_source_manifests_agree` declares
  `meson` only while its planner controls run `meson compile`
  (`check_planner.py:483`), which needs a compiler. `sandbox_extensions_native/feasibility`
  declares `clang` and `identity` but not `app`, while the dispatcher's
  `identity` probe reads the app's team unless `IDENTITY` or
  `PW_BYOXPC_IDENTITY` is set (`suite_run.py:312-318`).
- `dispatcher/accounting_controls` deliberately bypasses the catalog and
  feeds `suite_run.account` and `finish` constructed records in-process; its
  pass is about the accounting code's separate defence, not about any
  selection.

### 2.8 Prediction unavailable, attempt observed

The four `runner_filter_*` suites each run one specimen whose query names an
(operation, filter kind) pair the host planner does not send to the validator,
then call `tests/lib/unavailable_prediction.py` with one of three attempt
contracts. The adapter (`validate_run`, 20-100) requires a step with
`sandbox_check.outcome prediction_unavailable`, `result_source synthetic` and
`missing_reason query_not_requested`; a comparison with `order unestablished`
and the limitation `query_plan:prediction_unavailable_pair`; and an attempt
per contract: `file_open` accepts `ok` or `open_failed`; `sysctl_denied`
requires `sysctl_failed` with errno EPERM or EACCES and a
`permission_failure`/`permission_errno` record; `mach_lookup_allowed` requires
`ok`, `rc 0`, null errno, `requested_kind mach_lookup`, `requested_path` equal
to the filter value, `succeeded`/`completed_worker_status`, `operation_relation
matched` and `target_relation unresolved`.

A pass supports: the planner excluded the pair, recorded a synthetic
unavailable prediction with its reason, the attempt completed with the
contracted outcome, and the record declared no order and the limitation. It
establishes nothing about enforcement of the filter: the two IOKit cases
attempt a file open under a policy whose only rule is an IOKit deny
(`runner_filter_iokit_registry_entry_class/run.sh:19`: "Default allow keeps
the paired file attempt independent of the IOKit deny"); the local-name case
attempts a global bootstrap lookup that the `local-name` rule does not govern
(`runner_filter_local_name/run.sh:21-23`), and it fails as a product failure
if `com.apple.logd` cannot be looked up on the host. The sysctl case is the
one whose attempt the policy governs; its denial is observed by errno without
attribution. The two IOKit scripts differ only in IDs, one comment, and the
operation, filter kind, class and adapter arguments (2.13); the filter
READMEs say controls cover "all three filter callers" while the control's
table has four (`runner_filter_sysctl_name/checker_controls.py:23-28`).

### 2.9 Independent observation before decoding

`run_effects/file_actions_have_exact_effects` (`check_file_actions.py`)
snapshots each target (digest, size, mode, device, inode, links, mtime,
ctime; `effects.py:16-30`) before the run and again after, applies the row's
expectation to the two snapshots (118) before decoding the envelope (120
onward), then requires `ok`, one step, the expected prediction (validator
`allow`/`deny`, or `prediction_unavailable` with `query_not_requested` for a
target absent when the query was planned), `order query_first` or
`unestablished`, and the attempt's outcome, rc and errno (78-96). Its
`checker_controls` case feeds each expectation function fabricated snapshots.

`sbpl_allowdeny_consistency/sbpl_allowdeny_v1` (`check.py`) seeds two files
with random bytes, runs the fixture plan, reads both files back (50) and
requires the allowed file to hold changed nonempty data and the denied file
to equal its seed (53-55) before any envelope check (57 onward); the second
round reverses the allow/deny parameter bindings and requires the effects to
reverse. The two Mach steps are checked for presence only. Its fixture
profile denies with a `send-signal SIGUSR1` modifier whose effect no assertion
observes, and the worker ignores only SIGPIPE
(`controller/tools/pw_probe_runner/pw_probe_runner.c:1623`). Whether that
modifier delivers a signal in these runs was not observed by this survey (6).

`runner_c_worker_harness/unlink_deny` (`run.sh:406-425`): the unsandboxed
harness creates the target, drives the worker over the shared-memory ABI, and
afterwards reports `target_exists_after` from its own `access()` call
(`harness.c:1093-1096`); the case requires `applied`, `done`, exit 0, the slot
completed with `rc 1` and errno EPERM or EACCES, and `target_exists_after ==
true`. The independent observer here is the test equipment in the same
process tree. Every harness case's `rc`, `errno`, `observed_path` and failure
record are the worker's own shared-memory writes re-emitted by the harness
(`harness.c:1003-1100`); `exec_pipes_per_attempt`'s assertion that
`rlimit_soft` and `rlimit_hard` equal 64 compares against values the harness
printed from its own scenario constants (`run.sh:647`, `harness.c:1006`).

Contrast: `witness_contract/happy_path_baseline`, the filter cases, both
apply-isolation cases, the spawn-failure and ready-byte cases and all
`runner_use_c_worker` cases but one rest on envelope fields rather than an
independent effect observer. Some also check CLI exit status. The
apply-isolation comment (`run.sh:71-74`) says the `sandboxed_after_apply`
check prevents a short-circuited apply from passing; the field is the
worker's own report. For "the kernel denied", an errno in the envelope is the
worker's report of a failed call; a surviving file or an unchanged seed is a
fact about the disk. The run_effects and consistency cases check that the
effect matches the report; neither an unchanged file nor a permission-shaped
failure alone establishes sandbox causation. Envelope-only cases establish
the expected reported fields, with no independent observation of that effect.

### 2.10 A liveness check with a fixed window

`runner_mach_service_liveness/pwrunner_survives_mach_service_launch`
(`run.sh`) launches the shipped `PWRunner` directly with `--mach-service
com.pw.test.liveness.<pid>`, sleeps 0.5 s, reads the process state with `ps
-o stat=`, kills and waits for the process, then records failure for an empty
state or a zombie and otherwise passes (34-61); stderr is captured and never
read. An unsuccessful `ps` pipeline can instead exit the script under
`errexit`/`pipefail` before that explicit result path. The host binds
`NSXPCListener(machServiceName:)` for this argument
(`runner/Services/PWRunner/main.swift:13-23`); the alternative traps in
`xpc_main`. The case was added with the fix for that trap (`c220467`,
2026-07-06: "The host crashed on every launch (EXC_BREAKPOINT), so `runner
verify` returned xpc_timeout").

A pass supports: at the state sample following a 0.5 s sleep, the process
had a nonempty, non-zombie state. The intended regression is a startup trap;
the survey did not measure the broken variant's latency. The pass message,
the catalog description and the README say
the host "bound a mach-service listener"; nothing checks a binding. The
sample would not catch a later abort and does not establish that the
listener accepts a connection (the README says so). Runtime question: the
abort latency of the broken variant on this machine.

### 2.11 The one declared skip

`blackbox_menagerie/run.sh` maps `run_case.py` exit 3 to `test_skip ...
annotated_mismatch_absent` (76-83). `validate_run.py` decides the exit: it
builds a common expectation from `attempt_ok`, `errno` and `comparison`
(21-23) and passes it to `blackbox.validate_step`, which fails a step whose
`(rc == 0)` differs from `attempt_ok` (`blackbox.py:57-58`); for a step
annotated with `mismatch_reason` and `policy` it appends a pending skip when
the attempt agrees with the policy and a note when it does not (48-55);
errors return 1 before pending skips return 3 (59-63). Every annotated step in
`tests/fixtures/blackbox_menagerie/cases/core.json` carries `attempt_ok` in
the direction of the expected mismatch (seven steps in six specimens;
`core_strict_tmp` and `opt_vfs_private_tmp_only` have none yet declare the
reason). For such a step the pending skip is reached only when the attempt
disagrees with `attempt_ok`, which has already produced an error. Exit 3 is
therefore unreachable from the live manifest for all eight specimens and
their eight BYOXPC copies; an absent mismatch fails as `expected attempt_ok=...
(got ...)`. The checker control reaches the pending skip only by deleting
`attempt_ok` from a fabricated expectation (`checker_controls.py:218-223`,
"The first step intentionally has no attempt_ok expectation here"). The one
remaining producer of exit 3 is `run_case.py:174-176`, a missing
`policy-witness` binary, which `run.sh:79-80` would report under the same
skip reason; `run.sh:49-58` and the dispatcher's `app` gate normally pre-empt
it, provided the binary does not disappear between checks. The README's rule
(`blackbox_menagerie/README.md:25-27`) and the sixteen `skip_reasons`
entries describe a skip the manifest cannot produce. A pass with the current
manifest means the attempt has the expected relation to the manifest's policy
annotation ("ok (mismatch evidence: ...)") or the step had no annotation.
That label is not independent proof of a discrepancy between sandbox
prediction and enforcement.

### 2.12 Same constructed facts, three readers

`tests/fixtures/contract/phase_collection.json` is a list of 21 rows `{name,
status, disposition, reaped, spawn_failure, accepted}`. Readers:
`PhaseProtocolTests.swift:68-110` appends a carrier phase per row to a decoded
baseline reply and checks the encoder's acceptance; `controller/src/disposition.rs`
`phase_collection_issues` (1418-1475) implements the allowed status and
disposition combinations the rows encode and its tests read the fixture;
`tests/lib/phase_evidence.py` `collection_problem` and `ownership_problem` are
used by `tests/lib/lifecycle_oracle.py:471-480` and the consumer, and
`blackbox_e2e/extension_controls.py:78-106` drives every row through the
consumer and `check_record`, requiring `(not findings) == accepted`.
Passing all three checks would establish agreement on those 21 constructed
rows. It would not establish that real runs produce every combination; live
cases such as `witness_contract/phases`, the extension cases and the
validator-failure cases supply a separate kind of evidence. The survey did
not execute either kind.

`exec_observation.json` likewise feeds Swift `ExecObservationTests`, Rust
`disposition.rs:1724-1757` and Python `blackbox_e2e/checker_controls.py:137`
through their respective readers. `evidence_types.json` contains 50 patch
rows over a retained abnormal-issuer envelope: Swift decodes and re-encodes
the modified reply (`PhaseProtocolTests.swift:26-61`); Rust checks disposition
integrity and withholds the disposition on rejected rows
(`disposition.rs:1953-1985`); Python requires the consumer and lifecycle oracle
to agree with each acceptance flag and leave the input unchanged
(`extension_controls.py:15-29`). These are constructed mutations of a
retained capture, not new native observations.

`path_diagnostics.json` has 24 rows and a different division of work. Swift
checks decoding, malformed-row rejection and byte-preserving encoding
(`PathDiagnosticsTests.swift:49-80`). Rust tests capture and forwarding of
both valid and malformed representations, then invokes the Python contract
reader (`controller/src/runner_client.rs:134-173`); Rust is not a third
independent validator of these path forms. Python's `check_cases` also runs
from `blackbox_e2e/checker_controls.py:613`. Sharing a corpus establishes the
particular agreement or preservation each assertion checks; it does not make
all of these tests interchangeable. The repository documents shared-corpus
checks as independent readers (`tests/README.md`, "Comparison evidence coverage").

### 2.13 Same script, different input or context

`runner_apply_isolation_v2/run.sh` and `v3/run.sh` differ only in IDs, the
step message, the specimen ID, `(version 2)` versus `(version 3)` and the pass
message. The two IOKit filter suites differ only in IDs, one comment, the
operation, filter kind, class name and adapter arguments. Each pair asserts
the same proposition about a different input; the second copy adds a second
member of a documented set exercised live. Neither is an overlap: a change
to version-3 handling, or to one pair's membership, fails one copy and not
the other.

The eleven BYOXPC leaves (`runner_byoxpc/run.sh:13-80`) run the standard
scripts unchanged under `PW_TEST_SUITE_OVERRIDE=runner_byoxpc`,
`PW_TEST_RUNNER_MODE=byoxpc`, the installed service name and
`PW_TEST_RUNNER_EXPECT_KIND=byoxpc`, after `runner_install.sh` has copied,
inspected, signed, installed and verified an owned runner through
`tests/fixtures/byoxpc/session.py`. The standard scripts inject the runner
selector into the specimen (`testlib.sh:396-430`; `run_case.py:99-111`) and
require `runner_kind == byoxpc` (`testlib.sh:431-451`; `run_case.py:185`). The
copy adds exactly that assertion and the route through a launchd-registered,
team-signed external runner and the session's private registry. The remaining
assertions are shared, but now apply to that runner context. Wrapper setup
or cleanup can fail the invocation (`suite_exit`) without changing a leaf
report already written; installation also has its own catalog case.

Two pairs in the harness are closer than these. Scenario rows
`proceed_delayed_observed_quiescence` and `proceed_wait_budget_long` are
identical in parameters apart from their names (`harness.c:344, 347`) and
take the same checker branch (`check_proceed.py:21`): no difference in the
worker stimulus or oracle was identified. Names and per-run conditions can
still distinguish their executions. `policy_overflow_refused` (307200 bytes) and
`policy_capacity_plus_one_refused` (262144) differ only in the oversize and
share every expectation; a fault sensitive to input length could distinguish
them. And `witness_contract/bug_report_returns_attempts`
requires only a non-empty `steps` and an integer first
`attempt.rc` (`bug_report_returns_attempts.sh:49-58`), over the same policy and
probe plan as the main `bug_report_returns_verdicts` specimen, under a
different ID. The latter requires the allow verdict, rc/errno consistency,
an absent or expected observed path, `query_first`, release links, a completed
lifecycle and a clean disposition (59-91). It also runs an allow-default
neighbour and requires a successful read and the exact resolved path there
(93-97). A withheld `no_completed_result` slot with rc -1 would pass the first. The
first case's proposition is entailed by the second's over the same run, but
the first can pass when the second fails. This is a weaker check of shared
input, not strict equivalence under the plan's overlap standard.

`step_count_overflow_refused` supplies 257 in the header and 1 in argv
(`harness.c:675-677, 791-802`). The worker first refuses a header count over
capacity with exit 6; the argv disagreement is a later diagnostic, not the
refusal that this case observes
(`controller/tools/pw_probe_runner/pw_probe_runner.c:1676-1687`).

## 3. Consequential contrasts and overlaps

Superficially similar, materially different:

- "Controls": five jobs (2.2). "Validator": two programs (2.2).
- The two smoke cases: same fixture, same invocation, different added assertions
  (2.1). `happy_path_baseline` and `validator_subprocess_populated`: same
  plan, different fields.
- `bare_deny_default` exists in the harness (shared-memory fields and
  `exit_requested == 0`) and in `runner_use_c_worker` (envelope, consumer,
  record): same policy and attempt, different observation channel.
- Equipment-free cases inside app suites: `attempt_outcome_matrix_enforced`
  (source text), `transcript_controls`, `checker_controls`,
  `comparison_controls`, `validation_controls` (fabricated inputs) sit beside
  live cases; their passes are about readers and texts.
- The four filter cases share one adapter and establish three different
  things (2.8).
- "Independent observation" in two senses: a channel outside PolicyWitness
  reading the disk, and the test equipment's own view in the same process
  tree (2.9).
- A mutation case that contains a product observation (2.5); characterizations
  that assert product lifecycle facts and, in one case, the limitation (2.6).
- Three edge cases in `runner_exec_lifecycle` share one driver with a mode
  switch; `runner_outcome_runner_timeout` runs the empty variant of a checker
  shared with `runner_use_c_worker` and the witness hang case, and its file
  check is vacuous for that variant (`check.py:19-24`).

Superficially different, same job or shared proposition:

- `attempt_outcome_matrix_enforced` and the drift rule: same sets, same files,
  different reader, plus one string-presence check (2.3).
- `rust.disposition_reds` and `rust.byoxpc_reds` re-run six functions that
  `rust.unit` runs; they add classification, not coverage (2.4).
- `codesign.preflight` and the dispatcher's gate: one inspector, two roles
  (2.7).
- Shared contract corpora across readers and forwarding checks (2.12).
- Two harness scenarios with the same parameters and checker under different
  IDs; the bug-report pair instead has a strict difference in assertion
  strength (2.13). The interval cases
  `query_interval_is_not_a_snapshot` and
  `external_mutation_between_query_and_attempt` share `mutation_interval`
  and differ by one extra bridge query (`check_ordering.py`).
- Same script, different input or context: the apply-isolation pair, the IOKit
  pair, the BYOXPC copies (2.13): not overlaps.
- `runner_validator_failure`'s decode and unavailable cases: one parameterized
  checker, different fixture transcripts; `failure_boundaries`
  `validator_frames` and `validator_association`: one driver, different
  transcript lists.

Cases that resist a simple account:

- `closed_streams_leader_exit` and `worker_dies_during_exec`: a pass requires
  a product limitation to hold (2.6).
- The menagerie skip: declared, documented, exercised by a control, unreachable
  from the live manifest (2.11).
- `rust.fmt`: a formatting check registered as a test case; its branch inside
  `rust.unit`'s script is dead under the dispatcher (2.4).
- `runner_mach_service_liveness`: a pass is a nonempty, non-zombie state at
  the sample after a 0.5 s sleep (2.10).
- `validator_batch_mode/batch_ndjson_roundtrip`: its only deny verdict probes
  `/tmp/foo` under a profile that denies only `/etc`, because, in the
  script's words, the verdict "drifts from the policy structure" and the
  property tested is the classifier's deny on `rc=1 errno=0` (`run.sh:35-45`).
  The pass rests on a libsandbox behaviour the script calls reproducible.
- `path_query_observations`: an opt-in member of a suite about the witness
  contract that never submits a PolicyWitness request (2.6).
- `proceed_expiry_release_boundary`: the oracle accepts either outcome of the
  race and checks internal consistency (`check_proceed.py:11-20`).

## 4. Relationships

Recorded where they change what a result means.

- Positive control as dependency: `launch_inventory` depends on
  `contaminated_worker`. The latter checks a deliberately supplied environment
  canary; the inventory itself checks the selected seam flag in `ps` output
  (`launch_inventory.py:115`), not that canary.
- Mutation controls and the baselines they prove sensitive (2.5):
  `order_barrier_mutations` with `attempt_effects_wait_for_collection`
  (`held_effects`), the proceed harness cases (`check_proceed.py`) and the
  Swift driver; `mutation_controls` with `contaminated_worker`.
- Checker controls and the live cases that trust the checker:
  `blackbox_e2e/checker_controls`, `blackbox_menagerie/validation_controls`,
  `runner_filter_sysctl_name/checker_controls`, `run_effects/checker_controls`
  and `runner_validator_failure/transcript_controls` test the sensitivity of
  checkers used by live cases. A failure needs diagnosis to identify the
  reader path, fixture or equipment involved and which live conclusions rely
  on it; it does not automatically invalidate every other observation.
- The shared reader: `tests/lib/consumer.py` `validate` gates many CLI cases;
  others use inline field checks, including smoke, apply-isolation and several
  `runner_use_c_worker` cases. Its `query_first` eligibility rule (195-221)
  checks the reported chain. Separate observations include
  `attempt_effects_wait_for_collection` (libproc, kqueue and bridge gate in
  `tests/fixtures/exec/control.py`) and `order_barrier_mutations` observe the
  barrier through external effects, and component controls such as
  `OrderingTests.swift:69-88` and the C proceed harness.
- The dispatcher's artifact gate and `codesign.preflight` (2.7); the `app`
  and `worker` equipment credits derive from the gate.
- Release acceptance reads two battery envelopes (2.1);
  `preflight/release_controls` exercises acceptance with fakes (2.2).
- `witness_contract` includes two `runner_validator_failure` cases by
  canonical ID: one execution, counted in both suites' `containing_suites`;
  `tests/COVERAGE.md:27-28` also spells them under `witness_contract/`, a
  spelling `--case` does not accept (`test_cli.py:71-75`).
- `witness_contract/worker_post_apply_hang_seam` runs
  `runner_outcome_runner_timeout/check.py`; seven witness cases dispatch
  through `check_ordering.py:286-295`; `check_extensions.py` exports the
  capture and probe helpers for `check_phases.py`,
  `check_extension_boundaries.py` and `check_missing_issuer.py`.
- `tests/fixtures/comparison/matrix.json` feeds `comparison_matrix` (S, B and
  C rows), `extension_combinations` (M01 to M07) and the Swift
  `ComparisonEvidenceTests`.
- Documents as fixtures: `extensions` reads `docs/PolicyWitness.md`
  (`check_extensions.py:102-106`); `max_targets_reply_survives` reads
  `docs/limits.json`; `attempt_outcome_matrix_enforced` reads
  `tests/COVERAGE.md`.
- Interpreters: the dispatcher pins `PW_PYTHON` without changing `PATH`
  (`tests/lib/python_start.sh:56-58`); the live BBX and menagerie cases invoke
  their checkers by path (`bbx_001.sh:15, 111`; `blackbox_menagerie/run.sh:12,
  67`), whose shebang is `#!/usr/bin/env python3`, so those checkers run
  under whatever `python3` is first on `PATH`, and the fixture validator the
  host spawns uses `#!/usr/bin/python3` (`tests/fixtures/validator/validator.py:1`),
  the developer-tool shim. `report.json`'s `interpreter` entry describes the
  case's own resolution, not these children's.
- The disposition fixture rows are read by Swift, Rust and Python (2.12).
- Signing: `tests/fixtures/caller_auth/bundle.py:60-67` requests a secure
  timestamp for every identity except the ad-hoc `-` identity. Thus the
  Developer ID branch of caller-auth/signing controls requests timestamping;
  a review of the script alone does not establish its availability on a host.
- Exec inheritance: the CLI checker compares the helper report's PID with
  `attempt.child_pid`, both transported in the envelope
  (`runner_exec_inheritance/check.py:47-48`). The nonce and content checks
  correlate the report with the request, but are not an independent process
  observation. `contaminated_worker` separately checks a deliberately supplied
  resource before inspecting the child's reported state.
- Containment: `preflight/build_refusal_controls` runs the whole default
  battery inside itself (2.7), so every default case is also a part of that
  one opt-in case's pass.
- Guards of the run itself: `shell_helpers/python_startup` and
  `interpreter_boundary` test the startup refusal that every case's shell
  library performs (`tests/lib/testlib.sh:5-18`; `python_start.sh:21-59`);
  `dispatcher/controls` and `accounting_controls` test the code that wrote
  every other case's `run.json` entry. A demonstrated defect in a shared path
  can affect multiple results; its reach depends on the failing assertion
  and the path each result actually took.
- Equipment credits: the `app` and `worker` credits come from the dispatcher's
  gate; the `identity` credit comes from the app's team or an environment
  variable; `rosetta` from an `arch -x86_64` probe. A case's `requires` list
  decides whether a missing tool is `unrun` or, when the list is incomplete,
  a `fail` inside the case (2.7).

## 5. Documentation versus implementation

These discrepancies change either the claimed scope of a check or the
interpretation of its result. Section 2 separately records limits of
otherwise accurate claims.

1. `tests/FAILURE-PROPAGATION-CONTRACT.md:643` says `TestKit.run` counts a
   guarded early return as passed; the equipment guards throw (2.4).
   Absent guarded equipment cannot silently hide inside a passing Swift batch.
2. `tests/suites/unit/disposition_reds.sh:7-12` describes a non-default,
   ignored, intentionally failing population; the case is default, its four
   functions are not ignored, and it must be green (2.4). Its failure message
   still says “expected until the controller change lands.”
3. `tests/suites/blackbox_menagerie/README.md:25-27` and sixteen catalog
   `skip_reasons` describe an absent-annotated-mismatch skip. The current
   manifest's `attempt_ok` expectations make that skip unreachable (2.11).
4. `tests/OPT_IN_TESTS.md`, “Worker resource challenge probes,” says the
   characterization cases assert no product behaviour. The CLI examples
   assert lifecycle facts, and `closed_streams_leader_exit` requires the
   descendant to survive (2.6). The native-clock case instead exercises a
   standalone probe containing production clock helpers.
5. Catalog descriptions overstate the smoke and liveness cases:
   `smoke/specimen_file_read_deny_standard` says “Explicit standard runner
   returns the expected file denial,” although there is no explicit runner
   selector or denial assertion; `runner_mach_service_liveness` claims a
   bound listener from a process-state sample (2.1, 2.10).
6. `tests/suites/witness_contract/README.md` omits six members:
   `attempt_outcome_matrix_enforced`, `bug_report_returns_attempts`,
   `debuggable_mode_rejected`, `instrumentation_field_rejected`,
   `shm_sentinel_under_deny_default`, and `validator_subprocess_populated`.
   Its comparison-matrix account says specimen S has twenty-three rows
   (539-541); the fixture has 25 live rows plus constructed S09. Its dossier
   account says unavailable overrides include relative, NUL and overlong
   paths, while `check_dossier.py:339-346` tests a nonexistent path; it says
   three BYOXPC binary records, while the checker tests four roles (369-370).
7. The witness README promises “no ordering object” after a failed spawn
   (584-586). `check_pre_apply_failure.py:288` checks absence only at the
   top level of `runner_result`, where the current response does not place
   ordering; this does not assert absence at the phase location. The same
   README says `worker_termination` asserts collection fields absent
   (476-482); `check_worker_termination.py:56` checks absence of `log_last`
   in `data`, not the broader collection-field claim.
8. `tests/suites/runner_use_c_worker/README.md:75-81` says
   `access_failure_classified` asserts a `permission_failure` observation,
   while `run.sh:499-505` checks only attempt outcome, rc and errno. It says
   the unsupported-operation case's attempt spawns normally; that specimen's
   attempts are sysctl reads (`run.sh:938-943`). Its `happy_default_allow`
   relations are checked indirectly by the consumer against reported inputs,
   rather than by the inline literal assertions (2.1).
9. Other assertion limits are narrower than their accounts:
   `runner_ready_byte_resilience` omits from its success criteria the 1000 to
   1250 ms ready-wait window enforced by `run.sh:125-129`;
   `blackbox_e2e/README.md` names exactly
   `query_plan:path_unresolved_at_planning` for BBX-002's missing path, while
   its expectation file does not pin that code and `consumer.py:483-487`
   requires exactly one allowed `query_plan` limitation;
   the two IOKit READMEs say three filter callers, while the shared controls
   have four (`runner_filter_sysctl_name/checker_controls.py:23-28`).
10. In-script accounts retain unsupported descriptions:
    `bug_report_returns_attempts.sh:50-52` says bare deny-default for a policy
    that allows `file-read-data`; `check_attempt_in_flight.py:9-10` calls the
    a1 cause red/unknown while the controller has the
    `host_sentinel_deadline` classification (`controller/src/run_flow.rs:852,
    2733`; `controller/src/disposition.rs:66`). `harness.c:7-10` presents five
    scenario choices while its table contains 47 rows. These comments do not
    add assertions to the cases.
11. Equipment declarations exceed or omit the operations reached:
    `clock_arithmetic`, `proceed_precedence` and `exec_control_states` inherit
    `app`, `clang`, `worker`, although their checks compile production C into
    controls without launching the selected app or worker; witness cases
    including `happy_path_baseline`, `dossier_witness`,
    `create_existing_file_preserves_contents` and `max_exec_steps_spawn`
    inherit `clang` without invoking a compiler. Conversely,
    `preflight/release_controls` declares no equipment but builds a clang
    fixture (2.7). The preflight README says `release_deadline_controls` needs
    the suite compiler prerequisite (298-299), while its catalog entry and
    Python fixture require no compiler.
12. `tests/COVERAGE.md:27-28` spells the two included validator-failure cases
    under `witness_contract/`; the selector accepts their canonical
    `runner_validator_failure/` IDs, not those aliases (`test_cli.py:71-75`).
13. `tests/suites/shell_helpers/README.md:57-58` says `test_check_python` uses
    `/usr/bin/python3`; `tests/lib/case.sh:53` uses `${PW_PYTHON} -B -S`, the
    pinned Homebrew interpreter. The README elsewhere correctly explains the
    pin. `tests/suites/source_drift/README.md:446` gives the build-control
    wrapper shebang without the final `-S` required by `direct_python.py:19`.
14. `tests/suites/runner_unit/README.md:70-71` states success as exit 0 with a
    matching summary. The wrapper also rejects `SKIP`/`FAIL` lines and
    requires two Cargo replays (2.4).

## 6. Open questions

These are not results of this survey. Runtime observations would require
separate authorized execution; source-reading gaps are listed in Appendix B.

1. What margin does `runner_mach_service_liveness` have against its intended
   regression? A measured abort latency for the broken variant, under stated
   host conditions, would answer that. An abort after the sample can pass;
   that possibility is already clear statically.
2. Was the menagerie skip ever taken by a live run? A retained case report
   naming `annotated_mismatch_absent`, its checker output, and the executed
   revision and manifest would distinguish an absent mismatch from a missing
   binary or an older expectation. A top-level skipped count alone would not.
3. Is the assertion-to-`unrun` behaviour in the eight scripts of 2.0 intended?
   The history of `test_check_python` adoption and the harness owner's
   interpretation would settle intent; the implemented result path is clear.
4. Does `(with send-signal SIGUSR1)` deliver a signal in the consistency and
   BBX-001 specimens, and under what conditions? No assertion observes this
   modifier's effect. Native semantics and an independent signal observation
   would settle it; worker source alone does not establish delivery.
5. Which interpreter do the `env python3` checker shebangs select in an actual
   dispatcher child environment, and does the `/usr/bin/python3` fixture
   validator start successfully in an automation harness? Capture the child
   interpreter identity and startup result for that execution (4).
6. Does the a1 specimen carry `host_sentinel_deadline` end to end? The
   controller contains the classification, but a run of
   `worker_attempt_in_flight_at_deadline` with its retained envelope would
   establish the delivered value for that execution.
7. How often do the 250 ms sentinel window
   (`check_attempt_in_flight.py:115`), the 1 s and 2 s harness windows
   (`harness.c:871-878, 895`) and the 1000 to 1250 ms ready-wait window fail?
   Retained timing and failure records can establish frequency for the
   observed runs. Attributing failures to host load or first-execution cost
   needs corresponding observations; neither was measured here.
8. Does the post-release fresh read in `extensions` fail on a given OS?
   `access-observations.json` records it but the case does not assert its
   outcome (`check_extensions.py:92-93`). Inspecting a separately authorized
   run would answer that host-specific question.
9. Do installed BYOXPC binaries match their shipped baselines in a given
   installation? `check_dossier.py:376-378` accepts either `match` or
   `mismatch` according to independently computed hashes. A retained dossier
   and the compared binaries would show which occurred.
10. What is the runtime of `runner_outcome_bad_request/accepted_input_contract`,
    and do its repeated CLI/XPC launches fail intermittently? Recorded
    invocations, durations and diagnostics from actual runs would answer
    those questions; static launch structure is not a timing measurement.

## Footprint

Observed in the detached worktree before its removal (2026-10-25 17:23 UTC):
`git rev-parse HEAD` equal to the examined revision; `git status --porcelain`
empty; `tests/out` and `tests/.checkout.lock` absent; the two `--list` plans
regenerated and byte-identical to the Stage 0 copies (`diff` empty). These
establish unchanged tracked content, no visible untracked paths and no run
directory in that worktree. They do not inventory ignored paths. The command
record, kept with the survey's notes outside the checkout, holds worktree
setup and removal, the discovery commands, the scratch writes and this
report's write into the original checkout. Worktree setup/removal and
scratch/report writes were deliberate mutations; no case, build or prune
command ran. The original checkout was not required to stay clean or at the
examined revision, and nothing there besides this file is attributed to the
survey.

The review likewise used a disposable worktree at the examined revision and
read-only source/Git commands, plus scratch files and edits to this report.
At its final check (2026-10-25 17:51 UTC), that worktree still had the
examined HEAD, empty status, no `tests/out` and no checkout lock. Focused
review checks parsed the report, applied the Markdown command rule, resolved
its relative link and reconciled all 235 IDs and inspection totals against
the pinned catalog and saved plan. These are not executions of a catalog case. The original notes, ledger and command
record remain session-local and are not committed. Their location is
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/c8bb3630-28e3-4e53-af2b-2d5a68bc4727/scratchpad/survey/notes`;
review scratch is `/private/tmp/pw-survey-review.GdtY8j`. The appendices
preserve the inspection accounting needed to read this report without those
scratch files, but do not reproduce the working ledger's interpretations.

## Appendix A. Per-case inspection accounting

These levels describe the original passes, using the definitions in section 1.
They do not imply every nested fixture or batch member was read. The 235 IDs
are unique and equal the saved all-case plan. Totals: 163 Individual, 38 Driver,
23 Table/batch, 11 Partial groups. Appendix B qualifies nested and batch reading.

| Canonical case | Inspection |
| --- | --- |
| `blackbox_e2e/BBX-001` | Individual |
| `blackbox_e2e/BBX-002` | Individual |
| `blackbox_e2e/checker_controls` | Individual |
| `blackbox_e2e/comparison_controls` | Individual |
| `blackbox_e2e/native_comparison_controls` | Individual |
| `blackbox_menagerie/core_mach_simple` | Table/batch |
| `blackbox_menagerie/core_read_only` | Table/batch |
| `blackbox_menagerie/core_strict_tmp` | Table/batch |
| `blackbox_menagerie/opt_bucket5_subpath` | Table/batch |
| `blackbox_menagerie/opt_metafilter_any` | Table/batch |
| `blackbox_menagerie/opt_vfs_both_paths` | Table/batch |
| `blackbox_menagerie/opt_vfs_private_tmp_only` | Table/batch |
| `blackbox_menagerie/opt_vfs_tmp_only` | Table/batch |
| `blackbox_menagerie/validation_controls` | Individual |
| `dispatcher/accounting_controls` | Individual |
| `dispatcher/artifact_controls` | Individual |
| `dispatcher/cancellation_controls` | Individual |
| `dispatcher/controls` | Individual |
| `dispatcher/retention_controls` | Driver |
| `dispatcher/selection_controls` | Driver |
| `exec_fixture/controls` | Individual |
| `failure_boundaries/admission` | Individual |
| `failure_boundaries/fallback_helper` | Individual |
| `failure_boundaries/validator_association` | Individual |
| `failure_boundaries/validator_control_characters` | Individual |
| `failure_boundaries/validator_frames` | Individual |
| `failure_boundaries/validator_overlong_request` | Individual |
| `failure_boundaries/validator_removed_target` | Individual |
| `integration/cli.integration` | Table/batch |
| `preflight/build_guard_controls` | Individual |
| `preflight/build_provenance_controls` | Partial groups |
| `preflight/build_refusal_controls` | Partial groups |
| `preflight/build_toolchain_switch_controls` | Individual |
| `preflight/byoxpc_verification_controls` | Individual |
| `preflight/codesign.preflight` | Individual |
| `preflight/release_controls` | Individual |
| `preflight/release_deadline_controls` | Individual |
| `preflight/release_publish_controls` | Partial groups |
| `preflight/release_rotation_controls` | Partial groups |
| `preflight/signed_artifact_controls` | Individual |
| `preflight/translated_build_refusal_controls` | Individual |
| `run_capture/controls` | Individual |
| `run_effects/checker_controls` | Individual |
| `run_effects/exec_helper_effect_is_real` | Individual |
| `run_effects/file_actions_have_exact_effects` | Individual |
| `run_effects/run_installs_nothing` | Individual |
| `runner_abi_layout/c_swift_layout_agreement` | Individual |
| `runner_apply_isolation_v2/deny_default_v2_worker_reply` | Individual |
| `runner_apply_isolation_v3/deny_default_v3_worker_reply` | Individual |
| `runner_byoxpc/BBX-001` | Driver |
| `runner_byoxpc/BBX-002` | Driver |
| `runner_byoxpc/bad_neighbor_claims` | Individual |
| `runner_byoxpc/core_mach_simple` | Table/batch |
| `runner_byoxpc/core_read_only` | Table/batch |
| `runner_byoxpc/core_strict_tmp` | Table/batch |
| `runner_byoxpc/default_location` | Individual |
| `runner_byoxpc/entitlement_readback` | Individual |
| `runner_byoxpc/entitlement_transfer` | Individual |
| `runner_byoxpc/opt_bucket5_subpath` | Table/batch |
| `runner_byoxpc/opt_metafilter_any` | Table/batch |
| `runner_byoxpc/opt_vfs_both_paths` | Table/batch |
| `runner_byoxpc/opt_vfs_private_tmp_only` | Table/batch |
| `runner_byoxpc/opt_vfs_tmp_only` | Table/batch |
| `runner_byoxpc/registry_recovery` | Individual |
| `runner_byoxpc/runner_auth_external` | Individual |
| `runner_byoxpc/runner_install` | Individual |
| `runner_byoxpc/single_use` | Individual |
| `runner_byoxpc/specimen_file_read_deny` | Driver |
| `runner_c_worker_harness/abi_mismatch_refused` | Driver |
| `runner_c_worker_harness/bare_deny_default` | Individual |
| `runner_c_worker_harness/clock_arithmetic` | Table/batch |
| `runner_c_worker_harness/compile_failure` | Individual |
| `runner_c_worker_harness/create_allow` | Individual |
| `runner_c_worker_harness/exec_attempt_budget_remainder` | Driver |
| `runner_c_worker_harness/exec_attempt_budget_sequence` | Driver |
| `runner_c_worker_harness/exec_control_states` | Individual |
| `runner_c_worker_harness/exec_pipes_per_attempt` | Individual |
| `runner_c_worker_harness/exec_setup_post_apply_denied` | Individual |
| `runner_c_worker_harness/first_touch_after_apply` | Individual |
| `runner_c_worker_harness/happy_default_allow` | Individual |
| `runner_c_worker_harness/max_slots_deny_default` | Individual |
| `runner_c_worker_harness/max_slots_proceed` | Driver |
| `runner_c_worker_harness/native_clock` | Individual |
| `runner_c_worker_harness/param_count_overflow_refused` | Driver |
| `runner_c_worker_harness/params_round_trip` | Individual |
| `runner_c_worker_harness/policy_at_capacity` | Driver |
| `runner_c_worker_harness/policy_capacity_plus_one_refused` | Driver |
| `runner_c_worker_harness/policy_empty_expected` | Driver |
| `runner_c_worker_harness/policy_empty_short_refused` | Driver |
| `runner_c_worker_harness/policy_expectation_out_of_range_refused` | Driver |
| `runner_c_worker_harness/policy_nul_refused` | Driver |
| `runner_c_worker_harness/policy_overdelivered_refused` | Driver |
| `runner_c_worker_harness/policy_overflow_refused` | Driver |
| `runner_c_worker_harness/policy_truncated_prefix` | Individual |
| `runner_c_worker_harness/policy_utf8_bytes` | Driver |
| `runner_c_worker_harness/policy_whole_submission` | Driver |
| `runner_c_worker_harness/policy_zero_expected_refused` | Driver |
| `runner_c_worker_harness/prepared_unset_refused` | Driver |
| `runner_c_worker_harness/proceed_before_applied` | Driver |
| `runner_c_worker_harness/proceed_delayed_observed_quiescence` | Driver |
| `runner_c_worker_harness/proceed_expiry_release_boundary` | Driver |
| `runner_c_worker_harness/proceed_late_after_expiry` | Driver |
| `runner_c_worker_harness/proceed_never_set` | Driver |
| `runner_c_worker_harness/proceed_precedence` | Table/batch |
| `runner_c_worker_harness/proceed_under_bare_deny_default` | Driver |
| `runner_c_worker_harness/proceed_wait_budget_long` | Driver |
| `runner_c_worker_harness/proceed_wait_budget_short` | Driver |
| `runner_c_worker_harness/proceed_without_host_release` | Driver |
| `runner_c_worker_harness/sigkill_fallback` | Individual |
| `runner_c_worker_harness/step_count_overflow_refused` | Driver |
| `runner_c_worker_harness/sysctl_read_capacity` | Individual |
| `runner_c_worker_harness/terminal_erasure` | Individual |
| `runner_c_worker_harness/terminal_exit_without_request` | Individual |
| `runner_c_worker_harness/unlink_allow` | Individual |
| `runner_c_worker_harness/unlink_deny` | Individual |
| `runner_exec_dac/execute_permission_controls_spawn` | Individual |
| `runner_exec_inheritance/cli` | Individual |
| `runner_exec_inheritance/closed_worker_stderr` | Individual |
| `runner_exec_inheritance/contaminated_worker` | Individual |
| `runner_exec_inheritance/launch_inventory` | Individual |
| `runner_exec_inheritance/mutation_controls` | Individual |
| `runner_exec_lifecycle/closed_streams_continue` | Driver |
| `runner_exec_lifecycle/closed_streams_leader_exit` | Individual |
| `runner_exec_lifecycle/leader_exit_descendant` | Driver |
| `runner_exec_lifecycle/timeout_preserves_output_and_continues` | Individual |
| `runner_exec_lifecycle/worker_dies_during_exec` | Driver |
| `runner_filter_iokit_registry_entry_class/prediction_unavailable_attempt_observed` | Individual |
| `runner_filter_iokit_user_client_class/prediction_unavailable_attempt_observed` | Individual |
| `runner_filter_local_name/prediction_unavailable_attempt_observed` | Individual |
| `runner_filter_sysctl_name/checker_controls` | Individual |
| `runner_filter_sysctl_name/prediction_unavailable_attempt_observed` | Individual |
| `runner_live_worker_identity/independent_worker_and_host_queries` | Individual |
| `runner_mach_service_liveness/pwrunner_survives_mach_service_launch` | Individual |
| `runner_outcome_bad_request/accepted_input_contract` | Individual |
| `runner_outcome_bad_request/missing_required_filter_value` | Individual |
| `runner_outcome_bad_request/swift_decode_failure` | Individual |
| `runner_outcome_runner_timeout/host_kills_hung_worker` | Individual |
| `runner_outcome_validator_no_reply/validator_io_deadline_releases_worker` | Individual |
| `runner_outcome_worker_spawn_failed/posix_spawn_enoent_propagates_to_outcome` | Individual |
| `runner_ready_byte_resilience/slow_compile_ready_byte_survives_sigpipe` | Individual |
| `runner_specimen_isolation/overlapping_runs_keep_evidence_separate` | Individual |
| `runner_unit/build_receipt_controls` | Individual |
| `runner_unit/exec_reader_mutations` | Individual |
| `runner_unit/host_setup_controls` | Individual |
| `runner_unit/host_setup_oracle_sensitivity` | Driver |
| `runner_unit/launch_descriptor_controls` | Individual |
| `runner_unit/pwrunner_core_unit_executable` | Table/batch |
| `runner_unit/reaped_ack_mutation` | Individual |
| `runner_unit/service_admission_controls` | Individual |
| `runner_unit/sleep_record_controls` | Individual |
| `runner_use_c_worker/access_failure_classified` | Individual |
| `runner_use_c_worker/bare_deny_default` | Individual |
| `runner_use_c_worker/duplicate_step_id_rejected` | Individual |
| `runner_use_c_worker/exec_attempt_args_and_stderr_round_trip` | Individual |
| `runner_use_c_worker/exec_attempt_stdout_truncation_marker` | Individual |
| `runner_use_c_worker/exec_attempt_with_baseline_succeeds` | Individual |
| `runner_use_c_worker/exec_attempt_without_baseline_fails_cleanly` | Individual |
| `runner_use_c_worker/happy_default_allow` | Individual |
| `runner_use_c_worker/prediction_unavailable_pair` | Individual |
| `runner_use_c_worker/sandbox_check_path_unresolved_prediction_unavailable` | Individual |
| `runner_use_c_worker/sandbox_check_pid_matches_worker` | Individual |
| `runner_use_c_worker/sandbox_check_unsupported_operation_diagnostic` | Individual |
| `runner_use_c_worker/unsupported_attempt_rejected` | Individual |
| `runner_use_c_worker/worker_timeout_ms_honored` | Individual |
| `runner_validator_failure/transcript_controls` | Individual |
| `runner_validator_failure/validator_decode_failure_reports_degraded` | Driver |
| `runner_validator_failure/validator_killed_mid_stream` | Individual |
| `runner_validator_failure/validator_unavailable_reports_degraded` | Driver |
| `sandbox_extensions_native/feasibility` | Individual |
| `sbpl_allowdeny_consistency/sbpl_allowdeny_v1` | Individual |
| `shell_helpers/byoxpc_setup` | Individual |
| `shell_helpers/controls` | Individual |
| `shell_helpers/finalizers` | Individual |
| `shell_helpers/interpreter_boundary` | Individual |
| `shell_helpers/mutation_prerequisites` | Individual |
| `shell_helpers/python_startup` | Individual |
| `shell_helpers/script_groups` | Individual |
| `shell_helpers/worker_setup` | Individual |
| `smoke/runner_caller_auth` | Individual |
| `smoke/specimen_file_read_deny` | Individual |
| `smoke/specimen_file_read_deny_standard` | Individual |
| `source_drift/architecture_documentation` | Partial groups |
| `source_drift/build_documentation` | Partial groups |
| `source_drift/contract_versions` | Partial groups |
| `source_drift/direct_python_start` | Individual |
| `source_drift/generator_contract` | Partial groups |
| `source_drift/limits_documentation` | Partial groups |
| `source_drift/markdown_reader` | Partial groups |
| `source_drift/runner_source_manifests_agree` | Partial groups |
| `unit/rust.byoxpc_reds` | Individual |
| `unit/rust.disposition_reds` | Individual |
| `unit/rust.fmt` | Individual |
| `unit/rust.unit` | Table/batch |
| `validator_batch_mode/batch_ndjson_roundtrip` | Individual |
| `validator_batch_mode/predictions_do_not_report` | Individual |
| `validator_bridge/protocol_controls` | Individual |
| `witness_contract/attempt_effects_wait_for_collection` | Individual |
| `witness_contract/attempt_outcome_matrix_enforced` | Individual |
| `witness_contract/bug_report_returns_attempts` | Individual |
| `witness_contract/bug_report_returns_verdicts` | Individual |
| `witness_contract/comparison_matrix` | Table/batch |
| `witness_contract/create_existing_file_preserves_contents` | Individual |
| `witness_contract/debuggable_mode_rejected` | Individual |
| `witness_contract/deny_default_ordered` | Individual |
| `witness_contract/dossier_witness` | Individual |
| `witness_contract/dossier_witness_byoxpc` | Individual |
| `witness_contract/extension_boundaries` | Individual |
| `witness_contract/extension_combinations` | Table/batch |
| `witness_contract/extensions` | Individual |
| `witness_contract/extensions_byoxpc` | Individual |
| `witness_contract/external_mutation_between_query_and_attempt` | Individual |
| `witness_contract/happy_path_baseline` | Individual |
| `witness_contract/instrumentation_field_rejected` | Individual |
| `witness_contract/max_exec_steps_spawn` | Individual |
| `witness_contract/max_steps_ordered` | Individual |
| `witness_contract/max_targets_reply_survives` | Individual |
| `witness_contract/order_barrier_mutations` | Individual |
| `witness_contract/path_query_integrated` | Individual |
| `witness_contract/path_query_observations` | Individual |
| `witness_contract/phases` | Individual |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` | Individual |
| `witness_contract/prediction_target_is_independent_of_attempt_target` | Individual |
| `witness_contract/queries_precede_attempts` | Individual |
| `witness_contract/queries_use_a_pre_attempt_interval` | Individual |
| `witness_contract/query_interval_is_not_a_snapshot` | Individual |
| `witness_contract/shm_sentinel_under_deny_default` | Individual |
| `witness_contract/unfamiliar_diagnostic_transport` | Individual |
| `witness_contract/validator_spawn_failed_reports_degraded` | Individual |
| `witness_contract/validator_subprocess_populated` | Individual |
| `witness_contract/worker_attempt_in_flight_at_deadline` | Individual |
| `witness_contract/worker_killed_before_slot_publication` | Individual |
| `witness_contract/worker_post_apply_hang_seam` | Individual |
| `witness_contract/worker_progress_and_failure` | Individual |
| `witness_contract/worker_sparse_failure` | Individual |
| `witness_contract/worker_termination` | Individual |

## Appendix B. Group and nested-fixture reading

A named group is an inventory entry, not assertion coverage. Unless a member
or excerpt is identified below, its assertions have no recorded reading in
this survey. The additional reading during review was targeted at the findings;
it did not complete Stage 1's representative-per-group requirement.

### Rust

The original passes counted attributes by file and read the integration gate
and the two ignored-test attributes. They did not read representative bodies
in every module. All files below are under `controller/`; a file can contain
test functions without a `mod tests` wrapper. Review assertion reading is
listed explicitly; other members remain unexamined at body level.

| Test-bearing file | `#[test]` count | Assertions read during review |
| --- | --- | --- |
| `integration/cli_contract.rs` | 14 | None recorded |
| `src/app_layout.rs` | 1 | None recorded |
| `src/augments.rs` | 8 | None recorded |
| `src/bin/sbpl-check.rs` | 11 | None recorded |
| `src/disposition.rs` | 22 | `exec_observations_preserve_independent_facts_and_refuse_malformed_combinations`, `phase_collection_states_gate_disposition_without_requiring_success`, `shared_evidence_type_corpus` |
| `src/dossier.rs` | 12 | None recorded |
| `src/evidence.rs` | 5 | None recorded |
| `src/host_facts.rs` | 3 | None recorded |
| `src/json_contract.rs` | 4 | None recorded |
| `src/policy_check.rs` | 5 | None recorded |
| `src/request_patch.rs` | 1 | None recorded |
| `src/run_flow.rs` | 23 | None recorded |
| `src/runner_acquisition.rs` | 6 | None recorded |
| `src/runner_client.rs` | 12 | `path_wire_fixtures_survive_capture_serialization_and_independent_consumer` |
| `src/runner_commands.rs` | 4 | None recorded |
| `src/runner_manager.rs` | 21 | None recorded |
| `src/runner_select.rs` | 31 | None recorded |
| `src/sbpl_imports.rs` | 15 | None recorded |
| `src/sbpl_lex.rs` | 19 | None recorded |
| `src/shape.rs` | 3 | None recorded |
| `src/utils.rs` | 3 | None recorded |

### Swift

All functions below are registered in
`runner/Tests/PWRunnerCoreTests/main.swift`; their one-line descriptions were
read as hypotheses about the work. The original passes read `TestKit` and
equipment guards, not each guarded block's assertion body. Group names below
are literal source labels, not verified descriptions of every member.

| Registered function | `tk.group` names |
| --- | --- |
| `runEnvelopeInvariantTests` | `consumer evidence survives encoding without reclassification`; `exact response version`; `PWRunnerSubprocess: additive host observations`; `PWRunnerRunResult: Codable round-trip preserves semantic absence`; `PWRunnerRunResult: production-shaped result`; `PWRunnerRunResult: host short-circuit result`; `PWRunnerRunResult: post-spawn failure result` |
| `runPredictionUnavailableTests` | `predictionUnavailableQueryPlanning` |
| `runFilterKindValidationTests` | `validateSandboxChecks`; `requestMeaningFailure` |
| `runComparisonEvidenceTests` | `comparison matrix rows through comparisonEvidence`; `limitations vocabulary at the producer`; `host path provenance` |
| `runOrderingTests` | `bundle-local validator launch boundaries`; `release barrier: real host driver and independent lifecycle fixture`; `ordering eligibility and response-8 encoding`; `validator deadline override at the production boundary`; `collection closure independent of validator cleanup` |
| `runPhaseProtocolTests` | `ordered phases: production C/Swift and independent file effects` |
| `runExtensionEvidenceTests` | `issuer cleanup and physical channel erasure`; `extension publication and reference evidence` |
| `runExecObservationTests` | `exec observation readers and publication` |
| `runReplyFailureTests` | `host reply failure contract` |
| `runServiceAdmissionTests` | `host single use admission` |
| `runValidatorSelectionTests` | `service validator selection` |
| `runHostOutcomeClassifierTests` | `classify: worker/validator → normalized outcome`; `classify: publication validity and independent diagnostics` |
| `runAttemptOutcomeMappingTests` | `buildAttemptResult: (kind, action, slot) → attempt outcome` |
| `runLimitsContractTests` | `Documented limits` |
| `runQueryAdmissionTests` | `sandbox_check query admission`; `request-level admission` |
| `runContractVersionTests` | `Wire contract versions` |
| `runRequestContractTests` | `developer request examples through the runner boundary`; `accepted request contract` |
| `runReplyMaximumTests` | `maximal reply and receiver budget` |
| `runPathDiagnosticsTests` | `path diagnostics wire states and byte identity`; `attempt path diagnostics: shared wire rule and host resolution` |
| `runCWorkerTests` | `CWorker driver` |
| `runCWorkerLifecycleTests` | `CWorker host lifecycle observations` |
| `runCWorkerClockTests` | `host waits are elapsed monotonic allowances` |
| `runWorkerEvidenceTests` | `worker evidence publication` |
| `runPolicyTransferTests` | `policy delivery` |
| `runWorkerClockTests` | `worker clock setup refusal: production main through the real host driver`; `worker timing faults across phases: production orchestration and shipped validator`; `clock fixture handshake failure and cleanup` |
| `runCWorkerValidatorTests` | `CWorker + ValidatorClient orchestration` |
| `runValidatorEvidenceTests` | `validator byte frames and structural contract`; `validator driver lifecycle and competing observations` |
| `runDiagnosticTransportTests` | `unfamiliar diagnostic transport` |
| `runAugmentTests` | `PWRunnerPolicySpec.augments: Codable round-trip` |
| `runListenerConfigTests` | `ListenerConfig` |
| `runCompiledProfileCaptureTests` | `Compiled-profile capture: bounded worker receipt` |
| `runDispositionResolverTests` | `disposition observations (fixture, no sandbox)`; `disposition interpretation (constructed)`; `disposition contract mirror (tests/lib/lifecycle_contract.py)` |

Targeted review read these assertion blocks (paths under
`runner/Tests/PWRunnerCoreTests/`):

- `OrderingTests.swift:69-88`: `runOrderingGateControl`, the hook/receipt
  control also called by `runOrderingTests`.
- `PhaseProtocolTests.swift:26-110`: the shared evidence-type corpus and
  collection-state corpus blocks.
- `ExecObservationTests.swift:24-67`: valid-combination preservation and
  malformed-present-fact rejection/degradation.
- `PathDiagnosticsTests.swift:8-110`: composed long paths, shared valid and
  malformed fixtures, nine compact states, and missing-marker rejection;
  assertion excerpts from the two attempt-path blocks at 114 onward.

Other Swift member bodies have no recorded assertion reading; equipment-guard
inspection alone is not credited as reading those members.

### Python unittest groups

Counts below include subclasses of the method-free `StampFixture`. They are
static method counts, not observed execution counts. Paths are under
`tests/suites/`. “Excerpt” identifies the methods intersecting source ranges
the original notes record as read; it does not claim their full bodies or
all helper paths were inspected. Other members have no recorded assertion
reading. The generator module has 21 `test_` methods in source.

| Module / class | Methods | Recorded assertion reading |
| --- | --- | --- |
| `preflight/check_build_provenance.py` / `LockTests` | 16 | Excerpts: `test_claims_are_admitted_only_by_a_live_owners_handoff` |
| `preflight/check_build_provenance.py` / `ResolverTests` | 5 | Excerpts: `test_the_pin_resolves_and_probes_here` |
| `preflight/check_build_provenance.py` / `ShimContainmentTests` | 10 | Excerpts: `test_profiles_apply_and_keep_exec_restrictions`, `test_structured_paths_cannot_add_profile_rules` |
| `preflight/check_build_provenance.py` / `ProbeTests` | 3 | None recorded |
| `preflight/check_build_provenance.py` / `StampTests` | 1 | Excerpts: `test_stamp_states_are_decided_without_adopting_unknowns` |
| `preflight/check_build_provenance.py` / `OutputTargetStampTests` | 1 | None recorded |
| `preflight/check_build_provenance.py` / `FailedObservationTests` | 1 | None recorded |
| `preflight/check_build_provenance.py` / `FreshRemovalTests` | 1 | None recorded |
| `preflight/check_build_provenance.py` / `OwnershipAndAdmissionTests` | 4 | None recorded |
| `preflight/check_build_provenance.py` / `CargoJudgmentTests` | 3 | None recorded |
| `preflight/check_build_provenance.py` / `CargoConfigurationTests` | 5 | None recorded |
| `preflight/check_build_provenance.py` / `OutputTripleSelectionTests` | 1 | None recorded |
| `preflight/check_build_provenance.py` / `SdkTests` | 1 | None recorded |
| `preflight/check_build_provenance.py` / `OutputTargetTests` | 8 | Excerpts: `test_weakened_predicates_fail_these_controls` |
| `preflight/check_build_provenance.py` / `SignatureDisplayTests` | 1 | None recorded |
| `preflight/check_build_provenance.py` / `RecordTests` | 7 | Excerpts: `test_helper_subcommands_are_the_ones_the_script_invokes`, `test_opt_in_mutation_anchors_match_current_sources`, `test_unknown_wrapper_hashes_never_establish_stamp_compatibility` |
| `source_drift/architecture.py` / `ArchitectureDocumentationTests` | 10 | Excerpts: `test_document_and_figures_are_current` |
| `source_drift/build.py` / `BuildDocumentationTests` | 16 | Excerpts: `test_document_and_figure_are_current_and_the_rules_agree`, `test_meson_output_target_assertion_refuses_other_hosts` |
| `source_drift/contract.py` / `ContractVersionTests` | 23 | Excerpts: `test_every_generated_copy_is_current`, `test_build_refuses_a_builder_it_cannot_confirm_before_anything_else` |
| `source_drift/contract.py` / `WorkerIdentityTests` | 7 | Excerpts: `test_identity_is_current_relocatable_and_regeneration_is_idempotent` |
| `source_drift/direct_python.py` / `DirectPythonTests` | 2 | Individual checker reading recorded for both methods |
| `source_drift/generators.py` / `GeneratorContractTests` | 21 | Excerpts: `test_build_checks_every_generator_before_signing`, `test_prose_baseline_is_consistent_and_growth_is_explicit` |
| `source_drift/limits.py` / `LimitsDocumentationTests` | 22 | Excerpts: `test_document_is_current`, `test_build_refuses_stale_guide_before_signing_or_creating_output` |
| `source_drift/markdown.py` / `BlockTests` | 7 | None recorded |
| `source_drift/markdown.py` / `CommentTests` | 5 | None recorded |
| `source_drift/markdown.py` / `LinkTests` | 6 | None recorded |
| `source_drift/markdown.py` / `HeadingTests` | 4 | None recorded |
| `source_drift/markdown.py` / `TableTests` | 2 | None recorded |
| `source_drift/markdown.py` / `LineTests` | 1 | None recorded |
| `source_drift/markdown.py` / `VendorTests` | 5 | Excerpts: `test_only_the_reader_imports_the_parser`, `test_another_importer_is_named` |
| `source_drift/markdown.py` / `ImportGuardTests` | 6 | None recorded |

### Other tables, drivers and nested fixtures

- Menagerie: all eight manifest rows are identified by their cases in
  Appendix A, with eight BYOXPC reuses. The driver and shared checker were
  read; review traced all annotated `attempt_ok`/policy combinations for 2.11.
- Comparison matrix: `comparison_matrix` uses the S, B and C rows and
  `extension_combinations` uses M01–M07. The driver/checker was read; the
  ledger credits pointers to row expectations rather than separate per-row
  assertion accounts.
- `preflight/build_refusal_controls`: the `CONTROLS` and `SEQUENCES` tables
  were enumerated; recorded function reading is `shim_install_detector`,
  `release_battery`, `demonstrate_bypass` and shared assertion helpers. Other
  control bodies and mutation effects were not individually traced.
- `preflight/release_publish_controls`: `check_preflight` read in full,
  `check_archive` and `check_publish` partly, `check_branch_names` named only.
  Review additionally traced `make_dist` and `prepare_provenance_fixture`.
- `preflight/release_rotation_controls`: `portable` and `interrupted` read;
  `battery_contract`, `ordinary`, `protections`, `checkpoint_policy`,
  `acceptance_lifetime`, `legacy`, and `atomic_and_locking` named only. Review
  traced `make_release` into the shared compiler fixture.
- `source_drift/runner_source_manifests_agree`: selected rules and planner
  `main` read; individual scenario builders were not all traced. Review
  additionally read the attempt-outcome matrix rule and the documentation
  command rule. `build_rules.py` was read in full by the original pass.
- `dispatcher/selection_controls`: `exercise` and the final assertion block
  read; the scenario list at `check_selection.py:131-300` was not.
  `dispatcher/retention_controls`: `run` read; locking, pruning and orphaned
  descendant scenarios were not individually traced.
- `runner_unit/host_setup_oracle_sensitivity`: `main` and
  `assert_observations` read; variant preparation named only.
- `runner_outcome_bad_request/accepted_input_contract`: driver/checker read,
  corpus example IDs enumerated; not every example was read separately.
- `runner_c_worker_harness/clock_arithmetic` and `proceed_precedence`:
  `clock_control.c` and `proceed_control.c` read by header and assertion
  excerpts. `terminal_erasure`, `first_touch_after_apply`, and
  `exec_control_states` have individually read Python checkers, but only
  headers/excerpts of `terminal_control.c`, `first_touch_control.c` and
  `exec_control.c`. An Individual entry in Appendix A does not establish
  per-property review of these nested native fixtures.
- `blackbox_e2e/checker_controls`: its checker and the disposition/extension
  control modules were read. `consumer.py` was inspected at relevant rules,
  not line by line. The four contract corpora in 2.12 were traced to readers,
  without a new assertion-by-assertion survey of every corpus row.
