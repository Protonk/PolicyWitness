# Test work survey: revision 31b8195

A read-only account of what PolicyWitness's tests and test-like procedures
do, what a passing result establishes, what a failing result establishes or
fails to establish, and where activities that share the name *test* do
different jobs or where differently named activities do the same job. It
describes the tree at one revision. It proposes nothing; findings are
statements about what a check does and does not do, cited to its lines.
All 235 catalog cases are accounted for. The batch-group reading is recorded in Appendix B,
including materially different work inside a group. The inspection limits
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
  Section 2 contains seventeen investigations (2.0 through 2.16).
- Review used detached worktrees at the same revision, traced findings to
  assertions and shared helpers, and enumerated batch members from source
  without importing or executing their tests. Assertion reading covers all
  223 Rust test functions, 277 Swift `tk.run` sites and 205 Python unittest
  methods in the listed batches. Names, comments, equipment guards, scenario
  tables and relevant setup/helpers distinguish the jobs those assertions
  perform. Expected-answer sources, shared checker dependencies and the actual
  paths from observation to reader were traced for 2.15–2.16. Appendix A
  accounts for cases; Appendix B accounts for their
  groups. Neither the survey nor the review ran a case or credited a runtime
  result.
- Older accounts: the opt-in survey (`records/archive/tests/OPT-IN-REPORT.md`)
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
- `records/archive/performance/` harnesses: historical investigation equipment for a
  retired application (`records/archive/performance/README.md`); not registered, not
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
| Read through a table or batch | 23 | The driver/checker and its nested assertions were read: 8 menagerie specimens and 8 BYOXPC reuses; `comparison_matrix` and `extension_combinations`; the Rust unit and CLI integration batches; the Swift executable; `clock_arithmetic` and `proceed_precedence`. Appendix B identifies the groups, member counts and fixture boundaries. |
| Read by checker group | 11 | Large Python checkers accounted for by class or scenario: `build_provenance_controls` (16 classes, 68 methods), `build_refusal_controls` (49 control/sequence functions), `release_publish_controls` (4 scenarios), `release_rotation_controls` (9 scenarios), and seven `source_drift` cases. Assertion reading covers every method or listed scenario; shared rules and planner controls are accounted for separately in Appendix B. |

Appendix B records assertions read in all 21 Rust test-bearing files, all 32
registered Swift functions with their 55 group names, and all 31 test-bearing
Python classes. No member of those groups is credited on its name or equipment
guard alone. The two ignored Rust receipt replays, real-worker Swift blocks,
constructed comparisons and native fixtures are distinguished explicitly.

### Limits of inspection

- Static counts: `tk.run` call sites and `#[test]` attributes are counted in
  source; a block inside a loop would run more than once and is counted once.
- No case was executed, so nothing here says a case passes on this machine.
  Retained runs in the original checkout were not consulted for results.
- BYOXPC, signing and build-driving cases were read, not run; their equipment
  paths (launchd, keychain, notarization stand-ins) are described from code.
- Batch-member reading means reading assertion expressions, rejection paths
  and relevant setup/helpers, not every line of every body or a transitive
  audit of every called implementation. The five native control fixtures in
  Appendix B were read in full. Table assertions were read with their scenario
  distinctions; this is not an independent derivation of every expected value
  in the shared corpora, nor proof that all possible behaviours are covered.
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
Two Swift mutation controls observe different boundaries in disposable
package copies:

- `runner_unit/exec_reader_mutations` requires the unmodified
  `runExecObservationTests` to pass all three blocks, with no `FAIL` or `SKIP`.
  Its baseline preserves independent exec facts and absent metadata through
  decoding/encoding, refuses malformed present facts or degrades the reply,
  and gates C-slot payload on completion. The native lifecycle fixture
  publishes constructed exec evidence; it does not launch an exec child.
  Bypassing the completion gate must leave exactly two blocks passing and
  fail the named unpublished-payload assertion. Inventing absent metadata
  must fail the named `absence cannot become not_requested` assertion in the
  independent-combinations block; that variant requires at least one failure,
  not an exact failure count. A generic nonzero exit is insufficient, and
  `SKIP` is forbidden for every variant
  (`tests/suites/runner_unit/opt_in/exec_reader_mutations.py:80-103`;
  `runner/Tests/PWRunnerCoreTests/ExecObservationTests.swift:24-107`).
- `runner_unit/reaped_ack_mutation` requires all three baseline scenarios to
  pass: clean exit, signal exit and ownership loss. The first two establish
  that final reconciliation recovers an acknowledgement not seen before
  the native reap; the third preserves the raw acknowledgement while
  withholding established ordering after an injected ownership fault.
  They use a real fixture child and native wait, constructed query/attempt
  evidence, and no sandbox application. Independent `waitpid` must report
  `ECHILD` after the driver has reaped the child. Removing reconciliation
  must fail **both** clean and signal acknowledgement assertions, with
  exactly two failures and the ownership-loss scenario the sole passing
  control (`tests/suites/runner_unit/opt_in/reaped_ack_mutation.py:89-99`;
  `runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift:96-203`).

The planner controls inside
`source_drift/runner_source_manifests_agree` (`check_planner.py:156-162`)
rewrite sources in a disposable checkout, run the real `check.py`, and
require the expected return code and diagnostic for each mutation before
confirming the working inputs are unchanged. `runner_unit/host_setup_oracle_sensitivity`
is the inverse: it runs the preserved `host_setup_controls` checker as a
`legacy` module against three deliberately wrong host variants and passes
only if that checker still accepts all 22 cases for every variant
(`host_setup_oracle_sensitivity.py:334-336`); a sharper oracle would fail it.
It also requires ten rejected legacy controls and independent descriptor,
argv and native mapping observations, including positive mapping detection,
the partial-unmap suffix and its successful fixture cleanup
(`tests/suites/runner_unit/host_setup_oracle_sensitivity.py:306-370`).
The pass pins the old oracle's insensitivity while establishing that the
supplemental observers detect the particular wrong operations.

### 2.6 Passing by observing a counterexample

The registry's “Worker resource challenge probes” entry names three cases
and says a pass means the stated counterexample was observed, not a safety
guarantee (`tests/OPT_IN_TESTS.md:75-92`). Its separate launch-inventory entry
explicitly requires mandatory observations and production cleanup to succeed
(94-106). These are bounded claims, consistent with assertions about the
observed execution. The following cases illustrate different pass conditions:

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

The two CLI cases assert product lifecycle facts, while the native-clock case
asserts the applicability of production helpers in a standalone probe. The
survivor case requires its stated limitation. These observations do not
establish a general safety guarantee beyond the tested host and OS.
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

The harness contains an equivalent scenario pair and a pair with different
delivery checks. Scenario rows
`proceed_delayed_observed_quiescence` and `proceed_wait_budget_long` are
identical in parameters apart from their names (`harness.c:344, 347`) and
take the same checker branch (`check_proceed.py:21`): no difference in the
worker stimulus or oracle was identified. Names and per-run conditions can
still distinguish their executions. `policy_overflow_refused` constructs
307200 bytes consisting of a version-only prefix followed by whitespace;
`policy_capacity_plus_one_refused` pads an allow-default policy to exactly
262144 bytes (`tests/suites/runner_c_worker_harness/harness.c:692-718`).
Both require the same overflow refusal,
a header expectation of 262143 and no EOF receipt, but the first requires
`policy_bytes_written > 262143` while the second requires exactly 262144
(`tests/suites/runner_c_worker_harness/run.sh:118-127`). Their source content,
submission length and delivery-count
assertions differ; they share the refusal being tested, not every expectation.
And `witness_contract/bug_report_returns_attempts`
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

### 2.14 Different work inside the batches

`unit/rust.unit` is not uniformly a constructed-input batch. The `sbpl-check`
parameter tests use `FakeNative` and assert its call ledger, including cleanup
after injected errors; the integration suite instead invokes the selected
native compiler (`controller/src/bin/sbpl-check.rs:653-1160`;
`controller/integration/cli_contract.rs:73-1115`). Within the Rust unit batch,
`runner_client` starts real Python children to test pipes, failed request
delivery and transport timing, beside tests of constructed capture buffers
(`controller/src/runner_client.rs:133-474`). `host_facts` reads live sysctl
values, and `sbpl_imports` resolves real platform paths beside temporary import
graphs and lexical checks (`controller/src/host_facts.rs:69-98`;
`controller/src/sbpl_imports.rs:392-725`). Their passes establish different
boundaries: a fake-call sequence, an actual child exchange, or an observation
of the current host. None alone is a CLI witness run.

The same distinction occurs inside one Swift function. `runCWorkerTests`
contains 24 `tk.run` sites: real-worker file and sysctl attempts, parameter
transfer, exec outcomes, deadline and post-apply controls, plus pre-spawn
admission checks (`runner/Tests/PWRunnerCoreTests/CWorkerTests.swift:41-860`).
`runCWorkerLifecycleTests` uses real child processes but a no-sandbox ABI
fixture, with injected wait/kill faults; its acknowledgement controls require
an independent final reap check. `runWorkerEvidenceTests` exercises production
C compiled with native-call substitutions and also decodes constructed
publications
(`CWorkerLifecycleTests.swift:98-335`; `WorkerEvidenceTests.swift:24-294`).
A child process is therefore not enough to identify a native policy
observation. The failure contract's ownership table is useful at these
boundaries, but its constructed-ordering row is not an inventory of all
`OrderingTests` work: that function also drives the real host against a
lifecycle fixture and uses the shipped validator
(`tests/FAILURE-PROPAGATION-CONTRACT.md:617-629`;
`OrderingTests.swift:69-88, 257-345`).

`runComparisonEvidenceTests` feeds all 43 matrix rows through
`comparisonEvidence`, checking all six fields, their exact encoded keys and
the limitation vocabulary (`ComparisonEvidenceTests.swift:1-193`). These
are constructed channel inputs, including S09's unsupported attempt, not
observations of those actions. The matrix's live S/B/C cases, extension
combinations M01–M07, in-flight deadline row T and combined-phase driver M08
observe different routes before comparing the same record shape. M08's
production-driver block separately checks failed validator cleanup, late
EPIPE, distinct phase-local records and an independently prepared fresh read
(`PhaseProtocolTests.swift:321-417`). The two ignored Rust tests then replay
Swift-produced policy-transfer and clock replies through Rust assembly and
the Python consumer (`controller/src/run_flow.rs:931-1213`). Replay adds a
reader/transport boundary; it does not repeat the original native observation.

The provenance batch similarly mixes host operations and constructed
decisions. `ResolverTests` probes the actual pinned interpreter beside fake
resolver inputs; `LockTests` and `ShimContainmentTests` exercise real process,
lock and restrictive-profile boundaries. `SdkTests` and `OutputTargetTests`
compile native fixtures, and the latter reads their bytes independently of
the production decision. `SignatureDisplayTests` instead parses constructed
display text, while stamp and Cargo-judgment tests supply controlled tool
observations (`tests/suites/preflight/check_build_provenance.py:255-1093,
1249-1471, 1820-1934, 2171-2608`). A pass of the display parser is not
cryptographic verification; a pass of a stamp decision is not evidence that
an actual compiler produced a particular app.

The `source_drift` name also includes execution. Alongside text, manifest and
generated-copy comparisons, build-documentation and planner controls run
real Meson configurations in disposable copies and require specific refusal
diagnostics; architecture controls render SVG with Graphviz
(`tests/suites/source_drift/build.py:65-540`;
`tests/suites/source_drift/check_planner.py`;
`tests/suites/source_drift/architecture.py:58-293`). A failed batch can thus
mean an assertion failure, missing equipment, compiler/configuration failure
or failed fixture cleanup. The case status alone does not separate them;
the batch log and named failing member do. Appendix B accounts for all member
assertions and these distinct jobs without crediting any runtime outcome.

### 2.15 What justifies an expected answer

Agreement across readers establishes conformance to their shared expectations.
It does not by itself establish that the expectations correctly describe a
native operation or justify a conclusion about it. Independence here is
specific: a checker can be independent of the production implementation while
sharing its contract, vocabulary, observations and assumptions.

| Expected answers | Support separate from the implementation under test | Shared premise or limit |
| --- | --- | --- |
| Acceptance flags and valid/invalid forms in the shared corpora of 2.12 | Fixed JSON examples are supplied to distinct language boundaries. They are not obtained by asking that boundary whether the current input is valid. Type, range, absence and phase-consistency assertions can refute a reader that violates those examples. | The flags encode the repository's chosen contract. A retained native envelope supplies a starting document, not independent justification for the acceptance of every constructed mutation. A common mistake in the contract and its readers can survive. |
| Comparison matrix | Literal expected records accompany constructed inputs and live specimens. The live checker independently prepares files, observes mode-000 open/spawn failures and helper exit statuses, and checks file effects. | Those observations justify particular input/effect facts. They do not independently derive every comparison label, operation relation or ordering claim. The fixture and multiple readers share those meanings. |
| Hand-reviewed lifecycle examples | `lifecycle_contract.EXAMPLES` stores observations beside explicit expected claims and projections; the oracle must reproduce them. | “Hand-reviewed” is the module's account of their provenance, not a separate proof of its semantic rules. The examples and producer implement the same disposition contract. |
| The 2,880-row lifecycle model | Python computes expected answers without invoking the Swift resolver; Swift runs its actual resolver on each constructed observation row. | The expected-answer generator and Python acceptance checker both call `expected_claims`. Agreement with that model does not validate the model's assumptions or the fidelity of real publications to its inputs. |

The lifecycle model is a Cartesian product of five status choices, six
interventions, eight progress values, four two-slot configurations and three
collection bases, with `exit_requested=True` fixed
(`tests/lib/lifecycle_oracle.py:614-657`). It is exhaustive over those axes,
not over process histories, phase combinations or all representable inputs.
`--model-json` derives claims, issues and projections from `expected_claims`
and `expected_projections` (864-873); `check_record` uses the same claim
calculation (501-505). The Swift loop compares claim state/answer/value/reason,
issue fields, lifecycle summaries, `partial_steps` and the invalid-basis result.
Its `comparable` helper removes `basis` and `issue` from each claim before that
comparison; it is not a comparison of every projection and reference field
(`runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift:178-185,
463-509`). Other integrity assertions check those fields separately.

There is useful checking of the oracle itself. Its self-check compares against
the separately written examples, requires accepted records and named mutation
rejections, and checks properties such as an unrelated exit-code change leaving
step claims unchanged (`tests/lib/lifecycle_contract.py:460-627`;
`tests/lib/lifecycle_oracle.py:770-858`). These constrain an incorrect or
indiscriminately accepting/rejecting checker. They still depend on the stated
disposition rules. For example, the inference from terminal progress and an
incomplete slot to `not_reached` depends on the protocol ordering and collection
semantics used by both the model and production. A mistaken premise shared by
the contract, examples, model and producer need not create any disagreement.
The C2/C5 fixture observations add real publication/collection examples, but
their no-sandbox child does not validate every possible native execution
(`DispositionResolverTests.swift:189-251`).

The comparison matrix has similarly mixed grounding. Its README says the
expectations were reviewed against rules and independent controls, not generated
from the producer. Its provenance account also records comparison against the
older response-12 producer, including a corrected S22 row
(`tests/fixtures/comparison/README.md:3-10, 103-116`;
`tests/fixtures/comparison/baseline_response12/README.md:3-34`). Matching an
older producer supports continuity with that producer; it is not an external
derivation of the comparison's meaning. The current live check's direct
controls observe file access, spawns and initial absence, while its effect
checks inspect file bytes/existence; they do not independently observe every
fact named in every row (`tests/suites/witness_contract/check_comparison_matrix.py:83-112,
172-193`). In the Swift unit reader, `order` is supplied by the fixture and
the lifecycle limitation is appended through the production
`PWDisposition.limitationForSummary` mapping before comparison. That loop
tests record construction under those inputs, not the collection/release
barrier that would justify them in a real run
(`runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift:75-85, 107-137`).

Nor are the two Python entry points two independent implementations of every
rule. The consumer and lifecycle oracle both use `lifecycle_adapter`,
`phase_evidence` and `extension_evidence`; both receive facts from the same
document (`tests/lib/consumer.py:23-31`;
`tests/lib/lifecycle_oracle.py:24-28, 457-480, 506-510`). Agreement on a shared
helper's decision is one implementation observed through two entry points.
Independent filesystem/process observations constrain claims about those
observed executions. They do not make every contract assumption independent.
Thus a common mistaken premise can leave the relevant agreement checks green;
no such mistake is established merely by identifying this dependency.

### 2.16 Which boundaries one execution crosses

A continuous CLI case and a chain of component checks support different claims.
The following accounts trace the paths relevant to 2.12–2.15. “Selected app”
means the app passed to the dispatcher, whose integrity and inventory gates
must also pass; this survey did not run it or credit a retained execution.

| Claim / cases | Path exercised by the case | Boundary of the resulting claim |
| --- | --- | --- |
| Ordinary comparison, phase and extension observations: matrix S/C, `witness_contract/phases` ordinary branches, `witness_contract/extensions` | Public CLI through the selected app's client, XPC host and applicable worker/validator/issuer, back to the controller envelope and Python readers. Cases also compare prepared file bytes, effects or identities. | These are continuous app paths for those specimens. A consistent envelope alone still cannot independently verify all of its reported native facts or timing; the external checks cover the particular facts they observe. |
| `attempt_effects_wait_for_collection` | Selected CLI/client/host/worker with a test-owned native validator bridge. The gate, file contents, exec connection, process ancestry and exit events are observed before the final envelope is checked. | Continuous transport and host/worker ordering under a substituted validator. The held observations cover a 0.5 s interval; they do not exercise the shipped validator or prove every schedule obeys the barrier. |
| Matrix B, phase aggregate/cutoff controls, extension combinations M01–M07 | Public CLI and envelope path, with a validator transcript/fixture or compiled issuer/worker substitutions at declared override boundaries. | Integrated handling of the controlled failures is exercised. The substitute's facts are not observations that the corresponding unmodified native component naturally produces those failures. |
| M08, policy-transfer and worker-clock replies followed by Rust/Python replay | Swift test executable drives real children and production helpers/orchestration, saves encoded replies, then the wrapper requires Rust assembly and Python reader checks of those replies. | A connected data path through the saved reply exists. The host is built into the test executable, and the replay bypasses service admission, XPC, the client process and the built controller executable. |
| Exec-reader and reaped-acknowledgement controls | Test-built Swift package with a native ABI fixture; baseline plus targeted source mutations, as in 2.5. | Reader/publication and host lifecycle boundaries are exercised. This is neither a native exec-child experiment nor a CLI traversal of the same exceptional state. |
| Barrier mutation CLI controls | Public CLI path through a signed app copy with rebuilt worker and/or host, alongside separate C and Swift controls. | The CLI observation is integrated for that copy. Source reuse and equal before/after inventories of the selected app do not make the rebuilt pair its shipped bytes (2.5). |

The first three paths are visible in `RunCapture`'s actual subprocess launch
(`tests/lib/run_capture.py:25, 48-63`), the matrix loop
(`tests/suites/witness_contract/check_comparison_matrix.py:195-242`), ordinary
phase checks (`check_phases.py:26-37, 57-79`) and extension capture/read checks
(`check_extensions.py:37-51, 67-106`). The held-collection observer ties its
external worker/helper identities and effects to the returned reply
(`check_ordering.py:76-145`). M01–M07 compile control fixtures and select them
through `issuer_executable_path`/`worker_executable_path`, then launch the CLI
(`check_extension_boundaries.py:67-81, 142-172`). These are concrete integration
routes, not an inference from unrelated passing unit cases.

Replay deserves more credit than separate checks of invented examples, but
less than the complete app route. M08 runs `CWorkerOrchestrator` with the
selected worker, fixture validators and an injected failed kill; it explicitly
performs the service's path enrichment, observes late EPIPE and file contents,
then writes `combined-phases.json`
(`runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift:321-417`). The Rust test
reads that file, passes the parsed reply into production assembly, requires
the resulting envelope's `runner_result` to equal that reply, and invokes
Python validation (`controller/src/run_flow.rs:931-1089`). This preserves the
identity of the reply value across the checked stages. However, its surrounding
specimen, client output, timestamps and request-delivery record are constructed
(`controller/src/run_flow.rs:750-802`). Some clock replies are also assembled
by a test helper from actual driver output rather than returned by the service
(`runner/Tests/PWRunnerCoreTests/WorkerClockTests.swift:32-49`). The wrapper
requires both replays to run, but does not insert the omitted app processes
(`tests/suites/runner_unit/run.sh:55-68`).

Consequently, passing these component checks would not alone rule out a defect
in the omitted service/client route for that particular combined failure.
Passing ordinary CLI phases does not supply that missing observation of M08's
failed cleanup and late output; likewise, a constructed encoding check and a
separate native publication check do not establish that the same exceptional
publication survives the shipped service path. Connecting them requires the
untested assumption that the service selects the same assembly/enrichment
path and transports the same facts under those conditions. The continuous CLI
cases constrain that assumption for their own specimens. They do not establish
it for every independently tested component state. This is a limit on combining
results, not evidence that an integration defect exists.

## 3. Consequential contrasts and overlaps

Superficially similar, materially different:

- "Controls": five jobs (2.2). "Validator": two programs (2.2).
- "Unit" and "source drift" batches contain constructed decisions, real
  child/process observations and native-tool execution within the same case
  status (2.14).
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
4. Catalog descriptions overstate the smoke and liveness cases:
   `smoke/specimen_file_read_deny_standard` says “Explicit standard runner
   returns the expected file denial,” although there is no explicit runner
   selector or denial assertion; `runner_mach_service_liveness` claims a
   bound listener from a process-state sample (2.1, 2.10).
5. `tests/suites/witness_contract/README.md` omits six members:
   `attempt_outcome_matrix_enforced`, `bug_report_returns_attempts`,
   `debuggable_mode_rejected`, `instrumentation_field_rejected`,
   `shm_sentinel_under_deny_default`, and `validator_subprocess_populated`.
   Its comparison-matrix account says specimen S has twenty-three rows
   (539-541); the fixture has 25 live rows plus constructed S09. Its dossier
   account says unavailable overrides include relative, NUL and overlong
   paths, while `check_dossier.py:339-346` tests a nonexistent path; it says
   three BYOXPC binary records, while the checker tests four roles (369-370).
6. The witness README promises “no ordering object” after a failed spawn
   (584-586). `check_pre_apply_failure.py:288` checks absence only at the
   top level of `runner_result`, where the current response does not place
   ordering; this does not assert absence at the phase location. The same
   README says `worker_termination` asserts collection fields absent
   (476-482); `check_worker_termination.py:56` checks absence of `log_last`
   in `data`, not the broader collection-field claim.
7. `tests/suites/runner_use_c_worker/README.md:75-81` says
   `access_failure_classified` asserts a `permission_failure` observation,
   while `run.sh:499-505` checks only attempt outcome, rc and errno. It says
   the unsupported-operation case's attempt spawns normally; that specimen's
   attempts are sysctl reads (`run.sh:938-943`). Its `happy_default_allow`
   relations are checked indirectly by the consumer against reported inputs,
   rather than by the inline literal assertions (2.1).
8. Other assertion limits are narrower than their accounts:
   `runner_ready_byte_resilience` omits from its success criteria the 1000 to
   1250 ms ready-wait window enforced by `run.sh:125-129`;
   `blackbox_e2e/README.md` names exactly
   `query_plan:path_unresolved_at_planning` for BBX-002's missing path, while
   its expectation file does not pin that code and `consumer.py:483-487`
   requires exactly one allowed `query_plan` limitation;
   the two IOKit READMEs say three filter callers, while the shared controls
   have four (`runner_filter_sysctl_name/checker_controls.py:23-28`).
9. In-script accounts retain unsupported descriptions:
    `bug_report_returns_attempts.sh:50-52` says bare deny-default for a policy
    that allows `file-read-data`; `check_attempt_in_flight.py:9-10` calls the
    a1 cause red/unknown while the controller has the
    `host_sentinel_deadline` classification (`controller/src/run_flow.rs:852,
    2733`; `controller/src/disposition.rs:66`). `harness.c:7-10` presents five
    scenario choices while its table contains 47 rows. These comments do not
    add assertions to the cases.
10. Equipment declarations exceed or omit the operations reached:
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
11. `tests/COVERAGE.md:27-28` spells the two included validator-failure cases
    under `witness_contract/`; the selector accepts their canonical
    `runner_validator_failure/` IDs, not those aliases (`test_cli.py:71-75`).
12. `tests/suites/shell_helpers/README.md:57-58` says `test_check_python` uses
    `/usr/bin/python3`; `tests/lib/case.sh:53` uses `${PW_PYTHON} -B -S`, the
    pinned Homebrew interpreter. The README elsewhere correctly explains the
    pin. `tests/suites/source_drift/README.md:446` gives the build-control
    wrapper shebang without the final `-S` required by `direct_python.py:19`.
13. `tests/suites/runner_unit/README.md:70-71` states success as exit 0 with a
    matching summary. The wrapper also rejects `SKIP`/`FAIL` lines and
    requires two Cargo replays (2.4).

## 6. Open questions

These are not results of this survey. Runtime observations would require
separate authorized execution; static inspection boundaries are listed in Appendix B.

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

Review likewise used disposable worktrees at the examined revision and
read-only source/Git commands, plus scratch files and edits to this report.
The final source check (2026-10-25 18:46 UTC) found the examined HEAD, empty
status, no `tests/out` and no checkout lock. Focused review checks parsed the
report, applied the Markdown command rule explicitly (records are normally
excluded), resolved its relative link and reconciled all 235 IDs and inspection
totals against the pinned catalog and saved plan. They also reconciled the
21 Rust, 32 Swift and 31 Python group rows, their 705 members and the 55 Swift
group labels, and checked cited file/line extents. These are not executions
of a catalog case. Citation resolution does not establish semantic support;
that is the purpose of the assertion reading above.

The original notes, ledger and command record remain session-local and are
not committed. Their location is
`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/c8bb3630-28e3-4e53-af2b-2d5a68bc4727/scratchpad/survey/notes`;
review scratch is `/private/tmp/pw-survey-review.GdtY8j` and
`/private/tmp/pw-survey-completion.Gaqd2T` (member inventory, assertion-reading
excerpts and validation record), with the expected-answer and integration-path
review in `/private/tmp/pw-survey-oracles.ynb0Lq`. The disposable source
worktrees were removed.
The appendices preserve the inspection accounting needed to read this report
without those scratch files, but do not reproduce the working ledger's
interpretations.

## Appendix A. Per-case inspection accounting

These levels use the definitions in section 1. The 235 IDs are unique and
equal the saved all-case plan. Totals: 163 Individual, 38 Driver, 23 Table/batch,
11 Groups. Appendix B gives the member-level reading and boundaries for
nested fixtures and batches.

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
| `preflight/build_provenance_controls` | Groups |
| `preflight/build_refusal_controls` | Groups |
| `preflight/build_toolchain_switch_controls` | Individual |
| `preflight/byoxpc_verification_controls` | Individual |
| `preflight/codesign.preflight` | Individual |
| `preflight/release_controls` | Individual |
| `preflight/release_deadline_controls` | Individual |
| `preflight/release_publish_controls` | Groups |
| `preflight/release_rotation_controls` | Groups |
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
| `source_drift/architecture_documentation` | Groups |
| `source_drift/build_documentation` | Groups |
| `source_drift/contract_versions` | Groups |
| `source_drift/direct_python_start` | Individual |
| `source_drift/generator_contract` | Groups |
| `source_drift/limits_documentation` | Groups |
| `source_drift/markdown_reader` | Groups |
| `source_drift/runner_source_manifests_agree` | Groups |
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

“All” below identifies every test member in the cited group at `31b8195`,
not just a representative. Assertions and rejection paths were read for all
223 Rust functions, 277 Swift call sites and 205 Python unittest methods;
none of these members is grouped on names alone. Counts are static, including
loop bodies once and ignored Rust functions. They are not runtime pass totals.
The work column records distinctions found in assertions, with relevant setup
and helper reading; it does not claim every transitive implementation was audited.

### Rust

Paths are under `controller/`. Each row covers all `#[test]` functions in the
file, whether or not they have a `mod tests` wrapper. Ranges locate the members.

| Test-bearing file / member range | Members with assertions read | Work distinguished |
| --- | --- | --- |
| `integration/cli_contract.rs:73-1115` | All 14 | Selected CLI and native policy compiler: versions, smoke envelope, malformed requests, path-byte identity, augmentation admission and import resolution. Every member has the integration gate. |
| `src/app_layout.rs:92-102` | All 1 | Layout constants agree with literal bundle paths; no bundle is inspected. |
| `src/augments.rs:212-366` | All 8 | Temporary fragment files: metadata/source hashes, composition, explicit refusals and no partial request mutation. |
| `src/bin/sbpl-check.rs:653-1160` | All 11 | FakeNative records parameter creation, setting, freeing and injected errors; separate manifest, limit, inventory and envelope checks. No native compile is established by the fake-call tests. |
| `src/disposition.rs:1725-2423` | All 22 | Constructed lifecycle/exec/phase facts and shared corpora: independent facts survive, invalid combinations withhold claims, missing evidence stays missing, and future progress values do not become familiar states. |
| `src/dossier.rs:697-1475` | All 12 | Temporary manifests, files and hash comparisons, override provenance and evidence lookup; host-fact member additionally reads actual sysctl strings. |
| `src/evidence.rs:207-370` | All 5 | Temporary manifest bytes, positive and mismatched hashes, symbol parsing and exact typed lookup. |
| `src/host_facts.rs:69-98` | All 3 | Live kern/hw sysctl strings plus unknown-name and embedded-NUL refusals. |
| `src/json_contract.rs:155-252` | All 4 | Envelope key order, build metadata, result shape and versions against the manifest. |
| `src/policy_check.rs:149-333` | All 5 | Constructed helper output: supported/unfamiliar outcomes, empty or invalid UTF-8, captured bounds, and absence of retired projections independent of exit code. |
| `src/request_patch.rs:102-117` | All 1 | Only the requested JSON field changes; unrelated fields survive. |
| `src/run_flow.rs:829-2826` | All 23 | Constructed admission/assembly and injected dependency-call order; two ignored members instead replay retained Swift driver replies through Rust assembly and an independent Python consumer. |
| `src/runner_acquisition.rs:285-451` | All 6 | Injected generation observations and a simulated elapsed clock: retirement, PID reuse, refusal and shared wait budget; no launchd acquisition is observed. |
| `src/runner_client.rs:133-474` | All 12 | Real Python child pipes, broken-pipe delivery and elapsed transport brackets beside constructed capture buffers, invalid UTF-8 and capture limits. |
| `src/runner_commands.rs:897-989` | All 4 | Verify-request contents and default wait, explicit manifest requirements, missing-client failure and reply projection. |
| `src/runner_manager.rs:1281-2242` | All 21 | Mocked signing/cleanup faults and serialization beside real temporary registry atomicity, open-reader survival and lock-inode preservation. |
| `src/runner_select.rs:558-1273` | All 31 | Nested/top-level/null intent precedence, worker entitlements, temporary manifests/registries, privileged BYOXPC scope and pending-cleanup refusals. |
| `src/sbpl_imports.rs:392-725` | All 15 | Temporary import graphs, identities, byte/file/depth limits and FIFO timeout; separate members resolve real system.sb and the /bin/sh platform path. |
| `src/sbpl_lex.rs:224-381` | All 19 | Lexical import extraction across comments, escapes, quotes and malformed forms; not native SBPL acceptance. |
| `src/shape.rs:250-371` | All 3 | Constructed JSON shape classification and field/type ordering. |
| `src/utils.rs:221-307` | All 3 | Injected writer failure, UTF-8 byte capture and bounded diagnostics. |

The ignored members are `run_flow::tests::policy_transfer_driver_replies_cross_assembly_and_consumer`
and `worker_clock_driver_replies_cross_assembly_and_consumer`
(`controller/src/run_flow.rs:931-1213`). Both read Swift-produced receipts,
check their assembly/serialization and invoke the Python consumer; their
assertions include constructed corruptions and lifecycle-oracle checks.
They do not independently generate the worker observations. Ordinary
`rust.unit` excludes them; the runner-unit wrapper explicitly invokes both
after Swift has produced the receipts (2.4).

### Swift

The 32 functions and their registry comments in
`runner/Tests/PWRunnerCoreTests/main.swift` were checked against the members.
These are the 55 literal group labels; labels alone are not the evidence for
the work described in the following table.

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

Paths below are under `runner/Tests/PWRunnerCoreTests/`. Every `tk.run`
assertion block in each listed file was read. `ServiceAdmissionTests.swift`
contains two registered functions (three admission blocks and two selection
blocks). Counts for Ordering and Lifecycle include their shared
`runOrderingGateControl` and `runCWorkerReapedAcknowledgementControls` helpers;
those helpers are called by the registered functions and are not extra registry
entries. Loop-generated cases make runtime counts larger than call-site counts.

| Registered function / member source range | Call sites with assertions read | Work distinguished |
| --- | --- | --- |
| `runEnvelopeInvariantTests`; `EnvelopeInvariantTests.swift:36-274` | All 15 | Constructed Codable replies preserve semantic absence, observed false/empty values and unknown diagnostics; reject wrong versions and retired keys. |
| `runPredictionUnavailableTests`; `PredictionUnavailableTests.swift:35-60` | All 2 | Literal excluded operation/filter pairs and unknown kinds beside ordinary query-planning controls. |
| `runFilterKindValidationTests`; `FilterKindValidationTests.swift:23-136` | All 9 | Required/forbidden values, unknown filters, duplicate IDs and unsupported attempts are refused before execution. |
| `runComparisonEvidenceTests`; `ComparisonEvidenceTests.swift:108-238` | All 7 | All 43 matrix rows use constructed channel inputs; compare all six fields, exact keys and limitation vocabulary. Separate host-path provenance blocks read the filesystem. |
| `runOrderingTests`; `OrderingTests.swift:70-652` | All 23 | Real host driver with lifecycle fixture, gate receipts and injected lifecycle faults; shipped validator in the death-during-collection block; constructed ordering/encoding and validator-deadline controls. |
| `runPhaseProtocolTests`; `PhaseProtocolTests.swift:27-417` | All 12 | Constructed type/collection corpora beside production worker/validator phases, eight independently observed unlinks, ordinal refusal and interrupted phases; M08 combines failed cleanup, late EPIPE and fresh-read evidence. |
| `runExtensionEvidenceTests`; `ExtensionEvidenceTests.swift:127-354` | All 11 | Issuer fixture and mapped channel erasure/closed descriptor observations, injected wait/kill faults, and constructed extension-event/wire shapes. |
| `runExecObservationTests`; `ExecObservationTests.swift:24-109` | All 3 | Constructed exec facts and an ABI fixture publishing them: independent cleanup/leader state, malformed metadata and completion gating; no actual exec child. |
| `runReplyFailureTests`; `ReplyFailureTests.swift:397-577` | All 9 | Real reply serializer with constructed contradictions and injected encoding failure; degradation preserves observations, withholds comparisons and accounts for every stored field. |
| `runServiceAdmissionTests`; `ServiceAdmissionTests.swift:28-75` | All 3 | Concurrent in-process exported objects share one-use admission; failed invocation still consumes it and only its owner schedules exit. No XPC transport is exercised. |
| `runValidatorSelectionTests`; `ServiceAdmissionTests.swift:83-133` | All 2 | Temporary bundle-local candidate and app-level decoy; explicit override precedence. |
| `runHostOutcomeClassifierTests`; `HostOutcomeClassifierTests.swift:208-254` | All 4 | Constructed worker/validator/publication table: normalized outcome and diagnostic precedence; no child process observation. |
| `runAttemptOutcomeMappingTests`; `AttemptOutcomeMappingTests.swift:82-189` | All 7 | Constructed kind/action/slot combinations: outcomes, incomplete/unsupported states and child PID/status distinctions. |
| `runLimitsContractTests`; `LimitsContractTests.swift:14-136` | All 2 | Manifest/Swift/native-fixture constants and framed-receiver boundary values. |
| `runQueryAdmissionTests`; `QueryAdmissionTests.swift:30-336` | All 13 | Constructed UTF-8/NUL/count limits and request admission; refusal must precede process work. |
| `runContractVersionTests`; `ContractVersionTests.swift:254-319` | All 4 | Manifest versions, generated constants, shape classification and golden comparison. |
| `runRequestContractTests`; `RequestContractTests.swift:35-178` | All 9 | Shared accepted/rejected request corpus, exact-version-first handling, unknown/null fields and separate structural/resource admission. |
| `runReplyMaximumTests`; `ReplyMaximumTests.swift:369-393` | All 2 | Constructed maximal encoded reply against the receiver budget; an unclassified extra key is a negative control. |
| `runPathDiagnosticsTests`; `PathDiagnosticsTests.swift:8-200` | All 6 | Shared valid/malformed wire fixtures and compact states, real host path resolution, long composed UTF-8 identity and absent observations. |
| `runCWorkerTests`; `CWorkerTests.swift:41-860` | All 24 | Shipped worker file/sysctl attempts, parameter transfer, exec exits/refusal/deadlines and post-apply seams; other blocks check pre-spawn limits. Worker guards throw on absence. |
| `runCWorkerLifecycleTests`; `CWorkerLifecycleTests.swift:98-335` | All 11 | Real ABI fixture child with injected kill/wait/poll faults, independent reap checks and subprocess JSON; clean/signal acknowledgement recovery versus ownership loss. Fixture applies no sandbox. |
| `runCWorkerClockTests`; `CWorkerClockTests.swift:93-239` | All 13 | Controlled monotonic clock/sleep with native fixture children: elapsed allowances, oversleep and lifecycle cleanup. |
| `runWorkerEvidenceTests`; `WorkerEvidenceTests.swift:24-294` | All 15 | Production C main with substituted native calls publishes failures/progress/partial writes; constructed ABI payloads additionally test publication gating and stale errno exclusion. |
| `runPolicyTransferTests`; `PolicyTransferTests.swift:7-266` | All 7 | Stalled/draining fixture pipes, controlled partial-write deadline, shipped-worker truncated-input refusal, contradictory encoder inputs and retained replies for Rust replay. |
| `runWorkerClockTests`; `WorkerClockTests.swift:225-406` | All 8 | Production C main with clock substitutions, real host driver and shipped validator: setup/phase refusals, retained predictions, sticky versus local faults and independently observed child cleanup. |
| `runCWorkerValidatorTests`; `CWorkerValidatorTests.swift:55-290` | All 5 | Real worker plus validator: policy parameters/control characters, 256 probes, compile-failure hook absence; missing executable is a separate native launch-failure control. |
| `runValidatorEvidenceTests`; `ValidatorEvidenceTests.swift:62-279` | All 17 | Constructed byte-frame/record acceptance and real fixture-child pipe/lifecycle observations with injected kill/wait failures; competing evidence survives. |
| `runDiagnosticTransportTests`; `DiagnosticTransportTests.swift:15-104` | All 2 | Unfamiliar diagnostic payloads constructed independently of receiver enums survive worker/validator forwarding. |
| `runAugmentTests`; `AugmentTests.swift:16-64` | All 4 | Codable augment shape and refusal of unresolved fragments; not fragment expansion. |
| `runListenerConfigTests`; `ListenerConfigTests.swift:19-40` | All 4 | Pure argv-to-listener selection. |
| `runCompiledProfileCaptureTests`; `CompiledProfileCaptureTests.swift:37-124` | All 8 | Independently constructed bytes/digests, selected versus ignored bytes, identity and publication gates; invalid nonce refused before spawn. Not a native compiler capture. |
| `runDispositionResolverTests`; `DispositionResolverTests.swift:189-509` | All 16 | Native no-sandbox fixture publications for C2/C5, constructed interpretation/encoder cases, Python mirror and 2880 finite-model rows. |

### Python unittest groups

Paths are under `tests/suites/`. Each row covers all `test_` methods in the
named class, including the three test-bearing subclasses of the method-free
`StampFixture` base. Assertions in delegated helpers and subtest/scenario
loops were read as part of those methods. The 31 groups contain 205 methods:
68 provenance methods and 137 source-drift methods.

| Module / class and member range | Methods with assertions read | Work distinguished |
| --- | --- | --- |
| `preflight/check_build_provenance.py:255-762` / `LockTests` | All 16 | Real process/socket lock handoff, competitor refusal, cancellation/descendant lifetime and environment/forwarder negative controls. |
| `preflight/check_build_provenance.py:793-864` / `ResolverTests` | All 5 | Actual pinned Homebrew interpreter probe beside fake kegs/probes and path/environment refusals. |
| `preflight/check_build_provenance.py:875-1093` / `ShimContainmentTests` | All 10 | Real restrictive-profile exec and mach-lookup observations, structured-path escaping, injected gate failures and SDK entry-point order. |
| `preflight/check_build_provenance.py:1097-1210` / `ProbeTests` | All 3 | Real bounded child output, timeout and process cleanup; injected unreapable-child deadline is separate. |
| `preflight/check_build_provenance.py:1249-1342` / `StampTests` | All 1 | Constructed tool/Meson observations drive read, publish, reuse, extension and refusal states. |
| `preflight/check_build_provenance.py:1346-1435` / `OutputTargetStampTests` | All 1 | Output-target decisions precede tool probing; incompatible existing stamps remain unchanged. |
| `preflight/check_build_provenance.py:1439-1471` / `FailedObservationTests` | All 1 | Tool failure and oversized output cannot publish an accepted observation or stamp. |
| `preflight/check_build_provenance.py:1506-1568` / `FreshRemovalTests` | All 1 | Temporary owned cache removal, symlink refusal and preservation when admission/removal fails. |
| `preflight/check_build_provenance.py:1574-1767` / `OwnershipAndAdmissionTests` | All 4 | Lock/session scope, path replacement and ownership races; rejected callers preserve outside paths and existing evidence. |
| `preflight/check_build_provenance.py:1820-1934` / `CargoJudgmentTests` | All 3 | Constructed fingerprint freshness, literal boolean and flag-attribution decisions. |
| `preflight/check_build_provenance.py:1940-2129` / `CargoConfigurationTests` | All 5 | Temporary TOML discovery/includes, wrappers, environment and permission/refusal cases; these parser checks do not compare actual Cargo execution. |
| `preflight/check_build_provenance.py:2133-2149` / `OutputTripleSelectionTests` | All 1 | Explicit target overrides lower-priority configuration. |
| `preflight/check_build_provenance.py:2171-2212` / `SdkTests` | All 1 | Constructed load-command text and numeric versions, plus a compiled Mach-O checked against the selected SDK. |
| `preflight/check_build_provenance.py:2333-2564` / `OutputTargetTests` | All 8 | Compiled/mutated Mach-O fixtures, independent byte oracle, malformed/fat/DSYM scans, inconsistent tool reports, required observations and weakened-predicate controls. |
| `preflight/check_build_provenance.py:2581-2608` / `SignatureDisplayTests` | All 1 | Constructed codesign display text; parsing is not cryptographic signature verification. |
| `preflight/check_build_provenance.py:2635-2971` / `RecordTests` | All 7 | Fixture provenance/archive records, hashes/stages/signature metadata, current helper call routes, mutation anchors and unknown-wrapper stamp refusal. |
| `source_drift/architecture.py:58-293` / `ArchitectureDocumentationTests` | All 10 | Generated text and real Graphviz SVG, model/reference refusals, stale copies and transactional publication. |
| `source_drift/build.py:65-540` / `BuildDocumentationTests` | All 16 | Model/document/render checks and source agreement; real Meson configuration refusals and removed-guard controls are distinct work. |
| `source_drift/contract.py:121-560` / `ContractVersionTests` | All 23 | Version/model/corpus checks and generated copies; copied-tree build frontends must refuse stale or unconfirmed inputs before later work; Make forwarding. |
| `source_drift/contract.py:578-678` / `WorkerIdentityTests` | All 7 | Input hashes, relocatable/idempotent generation, symlinks and native source membership; tests are excluded from identity inputs. |
| `source_drift/direct_python.py:137-202` / `DirectPythonTests` | All 2 | Repository source routing and positive/refused direct-start fixtures. |
| `source_drift/generators.py:315-818` / `GeneratorContractTests` | All 21 | Manifest references and command forms, shared-helper refusals, transactional writer/render failures, citation spans and explicit baseline growth. |
| `source_drift/limits.py:62-522` / `LimitsDocumentationTests` | All 22 | Model ranges/ownership, generated document, matrix membership, stale-build refusal, render/staging and transactional-write controls. |
| `source_drift/markdown.py:90-135` / `BlockTests` | All 7 | Fences, indentation, lazy continuation, lists, quotes and code/prose separation in constructed Markdown. |
| `source_drift/markdown.py:139-165` / `CommentTests` | All 5 | Comment-block and inline-comment handling in constructed Markdown. |
| `source_drift/markdown.py:172-200` / `LinkTests` | All 6 | Inline/reference links, titles, escapes and unresolved references. |
| `source_drift/markdown.py:204-243` / `HeadingTests` | All 4 | Heading forms, inline content and anchor/duplicate handling. |
| `source_drift/markdown.py:247-256` / `TableTests` | All 2 | Table recognition and escaped cell separators. |
| `source_drift/markdown.py:260-263` / `LineTests` | All 1 | Source line numbers for parsed constructs. |
| `source_drift/markdown.py:267-318` / `VendorTests` | All 5 | Vendored parser bytes/licenses and static importer boundary; controlled importer violation. |
| `source_drift/markdown.py:347-383` / `ImportGuardTests` | All 6 | Fresh subprocess import isolation under ambient paths/modules and allowed package imports. |

### Other tables, drivers and nested fixtures

- Menagerie: all eight manifest rows and their eight BYOXPC reuses, the
  driver and shared checker were read. All annotated `attempt_ok`/policy
  combinations were traced for 2.11.
- Comparison matrix: all 43 row expectations, scenario/control descriptions
  and the Swift producer loop were read. The live `comparison_matrix` uses
  S/B/C rows except constructed-only S09; `extension_combinations` uses
  M01–M07. T belongs to the in-flight deadline case; M08 belongs to the Swift
  combined-phase driver and its Rust/Python replay. Sharing a comparison
  expectation does not make these the same observation (2.14).
- `preflight/build_refusal_controls`: assertions and relevant helpers in all
  37 `CONTROLS` and 12 `SEQUENCES` functions in
  `tests/suites/preflight/opt_in/build_refusals.py`, plus the 16 mutation entries,
  were read. They distinguish early admission refusal, cache preservation,
  real build/reuse transitions, compiler/tool-call receipts, signing/evidence
  boundaries, interrupted recovery and a real nested release battery. The
  Cargo-configuration sequence checks actual compiler invocation; the
  post-build output-tamper sequence instead requires accepted provenance to
  describe the changed bytes, limiting what freshness establishes. No listed
  control or sequence is accounted for on its name alone.
- `preflight/release_publish_controls`: all four scenarios in
  `check_release_publish.py` (`check_preflight`, `check_archive`,
  `check_publish`, `check_branch_names`) and their rejection assertions were
  read. Local Git pushes, archive/provenance bytes and branch/build-stamp
  handling are distinct from the fake GitHub replies. Shared compiler fixture
  setup was traced.
- `preflight/release_rotation_controls`: all nine scenarios in
  `check_release_rotation.py` (`portable`, `battery_contract`, `ordinary`,
  `protections`, `checkpoint_policy`, `acceptance_lifetime`, `interrupted`,
  `legacy`, `atomic_and_locking`) were read to their assertions. Fixture
  archives and inventories exercise selection/protection; real filesystem
  locks and controlled interruptions exercise exclusion and recovery.
- `source_drift/runner_source_manifests_agree`: shared drift/build rules and
  `check_planner.py` were read, including every named mutation and configured
  control. Copied-tree public-command selection/refusal is distinct from six
  real C-only Meson configurations and their expected source/policy refusal
  diagnostics. Markdown command and attempt-outcome rules were traced to
  their exact comparisons.
- Dispatcher: `check_selection.py`'s scenario list, `exercise` and final
  assertions were read, including aliases, context, dependency/equipment
  refusal and app-path/environment cases. `check_retention.py`'s locking,
  orphaned-grandchild, pruning and final assertions were read: they test real
  lock lifetime and descendant cleanup, and preservation/re-evaluation of
  retained, interrupted, ambiguous and unmanaged fixture evidence.
- `runner_unit/host_setup_oracle_sensitivity`: the variant preparation and
  observation assertions were read. Baseline and wrong-ready-direction,
  wrong-shared-memory-argument and partial-unmap variants are checked through
  native descriptor/argv/mapping observations beside the old accepting oracle.
- `runner_outcome_bad_request/accepted_input_contract`: driver/checker and
  corpus groups were read, including malformed, unknown-field/kind, version,
  structural versus resource-limit and valid-request paths. Not every JSON
  example was independently re-derived; all share the traced table checker.
- Five native fixtures were read in full, beside their owning checkers:
  `tests/fixtures/worker_lifecycle/clock_control.c` checks controlled timebase
  arithmetic, sample rejection, fault provenance and setup publication without
  a child or sandbox; `proceed_control.c` uses fresh forked children, controlled
  clock/release/cancel inputs and real ordinary-authority file opens across
  17 modes, without applying a sandbox; `exec_control.c` substitutes native
  exec/process/clock calls, checks a separate call ledger and published facts,
  and launches no exec child. These do not establish native clock or policy
  behaviour. `tests/fixtures/extension_controls/terminal_control.c` substitutes
  native calls and a token, observing full mapped-buffer erasure at publication
  and after reap. `tests/fixtures/worker_lifecycle/first_touch_control.c`
  instead reaches the production worker's post-apply boundary; its terminal
  touch and pre-touch variant distinguish actual backing-page observations.
- `blackbox_e2e/checker_controls`: checker and disposition/extension control
  modules were read; `consumer.py` was traced at relevant rules, not line by
  line. Shared-corpus readers in 2.12 were read to their assertion loops.
  Agreement over those rows is not an independent proof of each corpus's
  expected value or exhaustiveness.
