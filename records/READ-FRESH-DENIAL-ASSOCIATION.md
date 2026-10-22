# read_fresh denial-log association

Problem and verification record for the `tests/READ-FRESH-PLAN.md` correction,
executed 2026-10-21 (local time; runs dated 2026-10-22 UTC). It keeps the defect,
the expected envelope behavior, the commits, the two credited runs and how to
reproduce them. The product documentation describes the resulting behavior and
does not link here.

Run evidence under `tests/out/runs/` is gitignored and available only in the
local checkout that produced it. Both credited directories are pinned in
[tests/RETAINED.json](../tests/RETAINED.json), which protects them from ordinary
pruning but does not publish them. The account and the reproduction below do not
depend on that local evidence.

## Defect

Through `0ba24b3`, `attempt_operations` in
[sandbox_log.rs](../controller/src/sandbox_log.rs) admitted `file-read-data`
events for `file/open_read` and `file/access` attempts but not for
`file/read_fresh`. The
[denial-log correlation contract](../docs/PolicyWitness.md#denial-log-correlation)
lists all three. Given an otherwise usable event with the worker PID, operation
`file-read-data` and the submitted target as its path:

- the controller retained the event and reported `correlation_status: "pid_match"`;
- `sandbox_log_capture.step_denies` named no candidate for the `read_fresh` step;
- `runner_sandbox_diagnostics.permission_failures_without_record` still listed
  a permission-failing `read_fresh` step;
- an event shared with an eligible `open_read` attempt on the same target was a
  single `candidate` for the `open_read` step instead of `ambiguous`.

Swift's `comparisonEvidence` and Python's `expected_relations` already mapped
`read_fresh` to `file-read-data`. They relate query and attempt scopes, not log
eligibility, and were not changed. Existing fresh-read coverage missed the
defect because the comparison matrix's live driver (S26, S27) and the extension
controls disable log capture.

## Expected envelope behavior

The constructed reply holds one completed fresh open that failed with EPERM:
`fresh_read: {open_rc: -1, open_errno: 1}`, `outcome: read_failed`, comparison
`permission_failure`/`permission_errno`. Its query is `file-write-data` on
`/query`, worker PID is 42 and the client span is 1,000–2,500 ms. The relevant
event has PID 42, operation `file-read-data` and path `/attempt`.

| Constructed log evidence | Capture status | Correlation status | `step_denies` | `permission_failures_without_record` |
| --- | --- | --- | --- | --- |
| Valid window, relevant event | `captured` | `pid_match` | One `candidate` for `s` at event index 0 | `[]` |
| Valid window, no events, `observed_deny: false` | `captured` | `no_match` | `[]` | `["s"]` |
| Valid window, relevant operation and path, PID 99 | `captured` | `no_match` | `[]` | `["s"]` |
| Valid window, PID 42, `file-read-metadata` on `/attempt` | `captured` | `pid_match` | `[]` | `["s"]` |
| Valid window, PID 42, `file-read-data` on `/unrelated` | `captured` | `pid_match` | `[]` | `["s"]` |
| Relevant event in a reply for the wrong window | `window_mismatch` | `unavailable` | `null` | `null` |
| Capture disabled; collector not called | capture `null` | `not_attempted` | no capture object | `null` |

Two `read_fresh` attempts on one target, in successive phases, share the event as
`ambiguous` (`["s1", "s2"]`). So does an `open_read`/`read_fresh` pair
(`["o", "f"]`). Each has two matching-evidence entries. Serialized execution
evidence is identical across every log variant. `correlation_status` stays
based on PID matches, not candidate membership. A candidate records a
PID/operation/path correspondence. Under reading rule 3 it does not establish
that the attempt produced the record or that the denial caused the failure.

## Commits

| Commit | Content |
| --- | --- |
| `7183d3700fe2414fbe8bb7cb532dda5ea7dd154c` | Registered baseline: matcher and envelope tests with the six positives ignored, the `fresh_open_permission_failure` reply builder, the `unit/rust.read_fresh_reds` selector and its opt-in registration. Production arm unchanged. |
| `4ec0a52b3420d26176054199d620708d82134dae` | Correction: `read_fresh` added to the `file-read-data` arm. Ignores removed and case promoted to default membership. Reading rule 3 replaced, guide copy regenerated, and the S02/S27 matrix controls and the guide's jq caption brought in line with the rule. |

Between the two tested commits, `git diff 7183d37 4ec0a52 -- controller/src
tests/suites/unit/read_fresh_reds.sh` shows exactly the arm line and six removed
`#[ignore]` lines. The selector is byte-identical: blob
`3c5209840c7693ad9028ffcb28032b4e14e4be9f` in both commits.

The S02/S27 `control` prose in `tests/fixtures/comparison/matrix.json` and the
caption at the guide's `permission_failures_without_record` jq example went
beyond the plan's text. They restated the replaced clause ("no attribution
without a captured denial record"), which the plan explicitly removes. Nothing
reads either text as data. `source_drift/limits_documentation` checks the
generated copies.

## Selected tests

Six positive tests, each with its registered missing-candidate message:

| Test | Registered message |
| --- | --- |
| `sandbox_log::tests::read_fresh_attempt_is_a_file_read_data_candidate` | `read_fresh red [matcher, completed attempt]: file-read-data event 0 on /attempt names no candidate` |
| `sandbox_log::tests::read_fresh_candidate_needs_no_completed_attempt_evidence` | `read_fresh red [matcher, unpublished attempt]: file-read-data event 0 on /attempt names no candidate` |
| `run_flow::tests::fresh_read_candidate_survives_probe_plan_assembly` | `read_fresh red [envelope, probe_plan]: the relevant event names no candidate for s` |
| `run_flow::tests::fresh_read_candidate_survives_phased_assembly` | `read_fresh red [envelope, phases]: the relevant event names no candidate for s` |
| `run_flow::tests::repeated_fresh_reads_share_one_ambiguous_event` | `read_fresh red [envelope, repeated phases]: the relevant event names neither s1 nor s2` |
| `run_flow::tests::open_read_and_fresh_read_share_one_ambiguous_event` | `read_fresh red [envelope, mixed open_read]: the relevant event names o but not f` |

The matcher positives include seven events that must stay unmatched, and each
requires the exact association list. Each envelope positive checks capture
admission, the window, retained events, PID, execution bytes and consumer
validation before its candidate assertion. Nonignored companions ran on both
commits:

- `sandbox_log::tests::open_read_attempt_is_a_candidate_for_the_fresh_read_event`
- `sandbox_log::tests::fresh_read_attempt_has_no_candidate_among_irrelevant_events`
- `run_flow::tests::fresh_read_absent_irrelevant_and_unusable_log_evidence_stay_distinct`

The selector classifies a failure as red only when the test's own failure
section in the Cargo log carries its message. `byoxpc_reds.sh` instead searches
the whole log.

## Credited runs

Tools for both runs: cargo 1.99.0, rustc 1.99.0, rustfmt 1.10.0,
`/usr/bin/python3` 3.9.6, Xcode 27.1 (27A9275), macOS 26.7.1 (25G241) on
arm64. Neither run selects the app. Every case reports `system_sleep_ms: 0`.

### Red baseline

- **Run:** `20261022T052707Z_a8741b11` at
  `tests/out/runs/read-fresh-candidates-red/`.
- **Source:** `7183d3700fe2414fbe8bb7cb532dda5ea7dd154c`.
  `git status --porcelain=v1 --untracked-files=all` was empty before
  (05:27:00Z) and after (05:30:06Z).
- **Command:**

  ```sh
  PW_TEST_OUT_DIR=tests/out/runs/read-fresh-candidates-red \
    tests/run.sh --case unit/rust.read_fresh_reds --case unit/rust.unit \
      --case source_drift/runner_source_manifests_agree
  ```

- **Result:** dispatcher exit 1 with one failed and two passed cases.
  `source_drift/runner_source_manifests_agree` and `unit/rust.unit` passed;
  the batch ran with the positives ignored and the companions active.
  `unit/rust.read_fresh_reds` failed: "read_fresh association reds: 6 of 6
  failed at their registered missing-candidate assertion (0 pass); expected only
  without read_fresh eligibility".
- **Observed failures:** `artifacts/cargo-test-ignored.log` (SHA-256
  `334a99b76fee3412c25b1684b79f5be0715b1720a053ec16ca4f2e4ed03eb76d`) shows six
  FAILED lines, each panicking with its registered message. The matcher tests
  panic at `src/sandbox_log.rs:1272` and `:1302`. All envelope tests panic in
  their shared candidate assertion at `src/run_flow.rs:2355`, with `left: Null`
  (no association) or, for the mixed pair, `left: ["o"]`.
- **Attachments:** `attachments/` holds the console transcript, command, exit
  status, tool versions and the before/after source receipts.
  `attachments/selector-controls/` is described below.

### Green verification

- **Run:** `20261022T053225Z_6dec0839` at
  `tests/out/runs/read-fresh-candidates-green/`.
- **Source:** `4ec0a52b3420d26176054199d620708d82134dae`, clean before
  (05:32:24Z) and after (05:36:03Z).
- **Command:**

  ```sh
  PW_TEST_OUT_DIR=tests/out/runs/read-fresh-candidates-green \
    tests/run.sh --suite unit --case source_drift/limits_documentation \
      --case source_drift/runner_source_manifests_agree
  ```

- **Result:** dispatcher exit 0, all eight cases passed, no harness errors.
  `unit/rust.read_fresh_reds` reported "all 6 read_fresh association tests
  pass" (log SHA-256
  `6dd667e7e6c6cab19bb498afb2fea72487033e45cfc101a7f64ad954543b4cb4`).
  `unit/rust.unit` passed 255 tests, including the six positives and the
  companions; its two ignored tests are the existing Swift driver-receipt
  controls. `source_drift/limits_documentation` confirmed that the reading-rule
  and matrix copies agree. `rust.fmt`, `rust.disposition_reds`,
  `rust.observer_admission` and `rust.byoxpc_reds` passed.
- **Attachments:** `attachments/` holds the same receipt set as the red run.

## Selector classification controls

A fake `cargo` on `PATH` replayed nine constructed Cargo outputs through the
committed selector (blob `3c52098`). Each scenario required its exit status,
report status, failure message, and the exact `cargo test` argument vector:

| Scenario | Selector result |
| --- | --- |
| all six pass | pass |
| all six at their messages | fail: 6 of 6 reds |
| two pass, four at their messages | fail: 4 of 6 reds (2 pass) |
| one unrelated failure beside five reds | fail: failed without registered assertion (1) |
| a test's message present only in another test's section | fail: failed without registered assertion (1) |
| build error, no tests run | fail: test did not run |
| one test absent, five run | fail: test did not run |
| seven tests run | fail: unexpected test selection |
| all pass, Cargo exit 101 | fail: Cargo exited nonzero |

The driver, fake `cargo`, per-scenario inputs and reports, and `receipts.json`
are under the red run's `attachments/selector-controls/`.

## Uncredited runs

Before the baseline commit, development `cargo test` runs went through
`tests/lib/checkout_lock.sh`. One of them temporarily applied the correction:
all six positives passed. Two existing driver-receipt tests failed only because
an unfiltered `--include-ignored` selected them without their receipt
directories. That run was diagnostic and is not retained.
`tests/out/runs/read-fresh-precheck` ran the red selection plus `rust.fmt` on
the uncommitted baseline tree, with matching results. It is unpinned and
disposable.

## Reproduction

From any checkout containing both commits:

```sh
tree="$(mktemp -d)/pw-read-fresh"
git worktree add --detach "$tree" 7183d3700fe2414fbe8bb7cb532dda5ea7dd154c
cd "$tree"
PW_TEST_OUT_DIR=tests/out/runs/read-fresh-repro \
  tests/run.sh --case unit/rust.read_fresh_reds
```

The case must fail with all six reds at their registered messages. At
`4ec0a52b3420d26176054199d620708d82134dae`, the same command with a fresh output
directory must pass. A worktree has its own checkout lock and Cargo target
directory. Remove it with `git worktree remove` afterward.

## Scope and limits

Request, response and envelope versions and the shape goldens are unchanged.
No protocol or build input changed, so worker identity was not regenerated. The
controls use constructed observer output. They establish eligibility, assembly,
serialization and consumer recovery, but not that macOS produces or delivers a
`file-read-data` record for a denied fresh open. No live capture of a fresh-read
denial was run.
