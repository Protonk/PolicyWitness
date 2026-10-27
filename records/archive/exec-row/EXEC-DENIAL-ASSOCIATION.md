# Exec denial-log association

Historical record of the retired collector. Source and contract links below
use the pinned pre-retirement archive. The recorded revisions and captured
bytes retain their original provenance. `live_probe_existing.py` requires
the former application; maintained PolicyWitness cannot reproduce its log
observations.

Command examples retain the original `records/exec-row/` layout. The archived
script and patch preserve their recorded bytes; using them requires that layout
and the pinned former application in a separate checkout.

Problem record for the `exec/spawn` row of the controller's denial-log
eligibility table. The kernel records a denied worker `posix_spawn` under an
operation name the row does not admit, so a captured exec denial is never
associated with its step. This record gives the evidence, the reasons no
existing check detects it, and the smallest control found that distinguishes
correct from incorrect handling. It proposes no change.

Observed 2026-10-22 on macOS 26.7.1 (25G241), arm64, during an investigation of
attempt-kind integration. The captures came from a signed build of `f468200`
(build stamp `0.3.2 (821) v0.3.2-30-gf468200`) in a disposable worktree. The
control was verified at `99bb6be`. The files this record cites are identical at
both revisions. Everything cited under this directory is committed. That
investigation's other run directories were kept in a session scratch directory
and are not retained.

## The problem

### What the contract and code say

The user guide's correlation table
([PolicyWitness.md, "Denial-log correlation"](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/docs/PolicyWitness.md#denial-log-correlation),
line 2096) states:

```text
| exec spawn | process-exec, worker PID only |
```

The [failure contract](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/FAILURE-PROPAGATION-CONTRACT.md#public-compatibility-and-correlation)
(line 626) makes that mapping part of the public contract. The controller
implements it in `attempt_operations`
([sandbox_log.rs:181](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/sandbox_log.rs)):

```rust
(Some("exec"), Some("spawn")) => &["process-exec"],
```

Matching requires exact operation equality. The guide says "There are no
wildcard or prefix aliases" (line 2098), and the code comment at
`sandbox_log.rs:167-168` says the same.

The comparison record uses `process-exec*` for exec, in
`comparisonEvidence` ([CWorkerOrchestrator.swift:1016](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift))
and the consumer's `ATTEMPT_OPERATIONS` ([consumer.py:72](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/lib/consumer.py)).
That table answers a different question: which `sandbox_check` query an attempt
corresponds to. On the query side, the guide also records that `sandbox_check`
rejects the bare `process-exec` as `unsupported_operation` and accepts
`process-exec*` (lines 1477-1488; comparison-matrix row S11). SBPL source
accepts the bare name, as in `(deny process-exec)` (lines 659-660).

### What the kernel records

One specimen, [live_probe_existing.py](live_probe_existing.py), run three times
with default log capture. Policy:

```scheme
(version 1) (allow default)
(deny mach-lookup (global-name "com.apple.logd"))
(deny sysctl-read (sysctl-name "kern.osrelease"))
(deny process-exec (literal "/usr/bin/true"))
(deny file-read-data (literal "<temporary file>"))
```

Its four steps attempt each denied operation: `mach_lookup/bootstrap_look_up`,
`sysctl/read`, `exec/spawn` of `/usr/bin/true` and `file/open_read`. The
captures are under [captures/](captures/), byte-identical to the CLI output,
with hashes in [SHA256SUMS](captures/SHA256SUMS).

| Run | Worker PID | Records in `deny_events` (all under the worker PID) | Delivered by | Associated steps | `permission_failures_without_record` |
| --- | --- | --- | --- | --- | --- |
| [run-1](captures/run-1/envelope.json) | 66112 | `mach-lookup com.apple.logd`, `process-exec* /usr/bin/true` | `sandboxd` violation reporting | mach | `sysctl`, `exec`, `read` |
| [run-2](captures/run-2/envelope.json) | 66145 | mach, `sysctl-read kern.osrelease`, `process-exec* /usr/bin/true`, `file-read-data <file>` | `kernel[0]` | mach, sysctl, read | `exec` |
| [run-3](captures/run-3/envelope.json) | 66156 | same four | `kernel[0]` | mach, sysctl, read | `exec` |

The exec record in run 2 reads:

```text
2026-10-22 07:13:19.040197-0700  localhost kernel[0]: (Sandbox) Sandbox: pw-probe-runner(66145) deny(1) process-exec* /usr/bin/true
```

In every run the exec attempt failed with `outcome: exec_failed`, `rc: -1`,
`errno: 1` and `child_pid: 0`. Its comparison is `permission_failure` /
`permission_errno`, with `operation_relation: matched` against its
`process-exec*` query. The denial was recorded in all three runs, under the
worker's own PID, with the operation spelled `process-exec*`. The parser
(`log_show::parse_sandbox_deny_line`) extracts `operation: "process-exec*"` and
`path: "/usr/bin/true"`, and the matcher compares that operation to
`process-exec` and rejects it. Runs 2 and 3 also confirm the mach, sysctl and
file rows against real records. Run 1 shows that delivery varies: two records
are absent, and the rest arrived by a different reporting path with the same
message text.

### Effect on the envelope

For every captured exec denial:

- `sandbox_log_capture.step_denies` names no candidate for the exec step. The
  record remains, unassociated, in `deny_events`.
- `runner_sandbox_diagnostics.permission_failures_without_record` lists the
  exec step. `correlation_status` is `pid_match` because of this and other
  events.
- `consumer.validate` returns no errors and
  `log_capture_contract.check_live_capture` accepts the capture. This was
  rechecked with the readers at `99bb6be`.

Execution fields, comparisons and `normalized_outcome` are unaffected. Log
evidence does not feed them.

The guide's reading of the list is hedged: "Missing candidates establish
neither absence of denial records from the OS log store nor absence of sandbox
enforcement" (reading rule 3, lines 1586-1588). It also says "A record can exist in the
OS log store under another path form" (line 2064). Neither anticipates the
case here: the record is in the same capture, under the same PID and path,
and is missed because of the operation spelling. A reader who takes the list
at face value would conclude that this capture holds no record for the exec
failure. It holds one.

## Why nothing detects it

Three artifacts state the bare spelling: the guide table, the Rust row, and one
line of the log-archive corpus,
`PWQP: Sandbox: pw-probe-runner(42) deny(1) process-exec /usr/bin/true`
([query_predicate.json:17](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/fixtures/deny_capture/query_predicate.json)).
That corpus line is a declared message written by the fixture's emitter
([deny_capture README](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/fixtures/deny_capture/README.md)), not a
kernel record. The archive was generated on macOS 14.8.7 (`9b09ad9`), and it
tests OS query selection, not association. The row dates from `0670db1`
(2026-09-18). The three artifacts agree with one another. Nothing in the
repository compares them with a record the kernel produced.

The tests do not reach the row:

- Every constructed input to the matcher is a file attempt.
  `reply_fixtures::step`, `incomplete_step` and `fresh_open_permission_failure`
  ([reply_fixtures.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/reply_fixtures.rs)) and the
  `sandbox_log` test helper `request` (`sandbox_log.rs:1190`) all hardcode
  `kind: "file"`. The supplied-text replay in
  [log_replay_tests.rs](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/controller/src/log_replay_tests.rs) plans file
  attempts only.
- The live correlation checkers plan only `open_read` and `open_write`
  ([check_deny_capture_window.py:89](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/suites/witness_contract/check_deny_capture_window.py),
  [check_termination_correlation.py:46](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/suites/witness_contract/check_termination_correlation.py)).
  They assert associations only for records the OS returns. The comparison
  matrix's live driver runs with `--no-log-capture`
  ([check_comparison_matrix.py:36](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/tests/suites/witness_contract/check_comparison_matrix.py)).
- The readers check associations for consistency with `deny_events` and the
  reply, not for eligibility. `tests/AGENTS.md` keeps consumers independent of
  the production classifier.

The dispatcher selection below is the Rust batch, `unit` (6 cases), plus
the two app-free cases that read log capture
(`witness_contract/log_capture_controls`, `log_query_predicate_archive`) and
two app-free classification cases (`witness_contract/attempt_outcome_matrix_enforced`,
`blackbox_e2e/comparison_controls`). It was run at `99bb6be` with the row in
three states:

| Exec row | Result | Run | Evidence |
| --- | --- | --- | --- |
| unmodified (`process-exec`) | 10/10 pass | `20261022T172404Z_178ced8b` | [battery-unmodified](verification/battery-unmodified/) |
| row deleted | 10/10 pass | `20261022T172326Z_aee470fa` | [battery-row-removed](verification/battery-row-removed/) |
| observed spelling (`process-exec*`) | 10/10 pass | `20261022T172345Z_149fdb09` | [battery-observed-spelling](verification/battery-observed-spelling/) |

No case depends on the row, and no case can tell which spelling it holds.
Every case reports `system_sleep_ms: 0`.

## The smallest distinguishing control

### Definition

Replay a captured kernel record through the production parser and matcher,
against a constructed submitted attempt and reply step naming the record's
target and the record's PID as the worker. Require exactly one candidate,
naming that step.

[control.patch](control.patch) adds two tests to
`controller/src/log_replay_tests.rs`, inside the `log_replay` module included in
`run_flow::tests`. It applies to `f468200` and `99bb6be` alike.

- `exec_row_observed_records_name_their_attempts` is the control: about 35
  lines. It replays three lines captured in run 2 through
  `log_show::parse_sandbox_deny_line` and `match_step_denies`. It asserts the
  parsed PID and target, then requires a candidate for each step. The exec line
  alone distinguishes the row. The mach and sysctl lines show that the same
  replay associates records whose rows are right, so a red names the row and
  not the harness.
- `exec_row_documented_operation_names_a_candidate` writes the exec expectation
  from the guide's table (`process-exec`) instead of an observed record. It is
  included to show that this oracle does not distinguish.

### Verification

`tests/lib/checkout_lock.sh -- cargo test --manifest-path controller/Cargo.toml exec_row_ -- --test-threads=1`
in a disposable worktree at `99bb6be` with the patch applied:

| Exec row | Observed-record control | Documented-table variant | Log |
| --- | --- | --- | --- |
| unmodified (`process-exec`) | **fails**: `exec-row red [observed records]: no candidate for exec/spawn (process-exec*)` | passes | [cargo-unmodified.log](verification/cargo-unmodified.log) |
| observed spelling (`process-exec*`) | passes | **fails**: `exec-row red [documented table]: process-exec event names no candidate` | [cargo-observed-spelling.log](verification/cargo-observed-spelling.log) |
| row deleted | **fails** (exec) | **fails** | [cargo-row-removed.log](verification/cargo-row-removed.log) |

The observed-record control is red exactly when the row does not admit the
kernel's record. The documented-table variant inverts the result on the first
two rows: it passes on the row that misses real records and fails on the row
that matches them. A control whose expectation comes from the guide, the code
or the corpus inherits their shared error. The distinguishing input is a record
the kernel actually produced.

During the investigation, the same observed-record test also went red for mach
when the `mach_lookup` row was deleted. That run is not retained.

### What the control does not establish

- That macOS produces or delivers a record for a given denial. The control
  replays text; delivery varies (run 1).
- The spelling on other macOS releases, or for exec forms other than a
  `posix_spawn` of a Mach-O binary denied by `(deny process-exec (literal …))`.
  It establishes nothing about interpreter execs or `process-exec-interpreter`.
- The envelope-level diagnostic. The matcher-level control stops before
  `permission_failures_without_record`. The captures show that consequence.
  The shared reply builders produce file steps only (`reply_fixtures::operation`
  panics on `spawn`), so no exec step went through the replay seam.

## Scope beyond the exec row

The same investigation found the gap is not specific to exec. Those runs are
not retained; the observations are summarized here:

- Deleting the `mach_lookup` row, or the mach, sysctl and exec rows together,
  passed every case of the selection above. Deleting `read_fresh` from the file
  row failed the six registered `read_fresh` reds. The file rows have
  constructed coverage; the mach, sysctl and exec rows have none.
- A hypothetical `file/stat` attempt kind was added with its C, Swift routing,
  outcome and comparison mappings, but without the Python reader's entries or a
  log-eligibility row. After the normal worker-identity regeneration and the
  one `tests/COVERAGE.md` row the outcome rule demands, all 16 drift rules, the
  five generators and the Rust and Swift unit suites passed. Live runs captured
  its `file-read-metadata` record, left it unassociated and listed the step in
  `permission_failures_without_record`. With the Python entries added, the
  consumer accepted those envelopes, leaving the log row as the only gap.
- An earlier stage of the same kind had only C/Swift routing, with no Swift
  failure outcome. The same checks passed, including the Swift unit suite
  (467/467). `AttemptOutcomeMappingTests` iterates a hand-written list of
  eight pairs, which already omits `read_fresh`. A kernel-denied `stat` was
  published as `outcome: "unsupported"` with `result_source: "worker"` and
  classified `other_failure`, so it also dropped out of
  `permission_failures_without_record`. Swift and the consumer agreed, and
  nothing flagged it.

## Evidentiary limits

- One OS build (26.7.1, 25G241) and one deny form. The repository's only
  older-OS material, the macOS 14.8.7 archive corpus, is constructed and says
  nothing about what that release recorded.
- Three live runs. One delivered a partial set by another path. The exec record
  was present in all three.
- The captures came from a disposable worktree build of `f468200`, signed with
  the project's Developer ID identity. That bundle no longer exists. The
  envelopes' provenance fields name its former path.
- The control was run with `--test-threads=1`. In the investigation, two replay
  tests run in parallel read each other's supplied text. The `replay` helper names its
  temp file from the PID, fault and `CLOCK_MONOTONIC` nanoseconds, which have
  1 µs resolution on this machine. The two tests in `control.patch` do not use
  that helper.

## Reproduction

Control, from the root of a checkout containing this record:

```sh
patch="$PWD/records/exec-row/control.patch"
tree="$(mktemp -d)/pw-exec-row"
git worktree add --detach "$tree" 99bb6be
cd "$tree"
git apply "$patch"
tests/lib/checkout_lock.sh -- cargo test --manifest-path controller/Cargo.toml exec_row_ -- --test-threads=1
```

The observed-record test must fail with the message above. Replacing
`&["process-exec"]` with `&["process-exec*"]` in the exec row of
`attempt_operations` must flip both results. Remove the worktree with
`git worktree remove` afterward.

Live capture, against a signed build ([build guide](https://github.com/Protonk/Observer/blob/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source/docs/BUILD.md)):

```sh
/usr/bin/python3 -I records/exec-row/live_probe_existing.py \
  dist/PolicyWitness.app/Contents/MacOS/policy-witness /private/tmp/pw-exec-row-run
jq '.data.sandbox_log_capture.deny_events[] | [.pid, .operation, .path]' /private/tmp/pw-exec-row-run/envelope.json
jq '.data.sandbox_log_capture.step_denies, .data.runner_sandbox_diagnostics.permission_failures_without_record' \
  /private/tmp/pw-exec-row-run/envelope.json
```

The script creates and removes its own directory under `/private/tmp`. Its
output directory must not exist beforehand.

## Files

| Path | Content |
| --- | --- |
| [captures/run-1/](captures/run-1/), [run-2/](captures/run-2/), [run-3/](captures/run-3/) | `request.json`, `envelope.json`, `observations.json` (CLI status and temporary root) and the empty `stderr.txt` of each live run |
| [captures/SHA256SUMS](captures/SHA256SUMS) | hashes of the capture files |
| [live_probe_existing.py](live_probe_existing.py) | the probe that produced them, unchanged |
| [control.patch](control.patch) | the control and its documented-table variant |
| [verification/](verification/) | Cargo logs for the three control states; console transcript and `run.json` for each dispatcher run |
