# Failure propagation audit (after steps 0–2)

Independent review of [the plan](FAILURE-PROPAGATION-PLAN.md), the
[routing inventory](FAILURE-PROPAGATION-INVENTORY.md) and the
[field contract](FAILURE-PROPAGATION-CONTRACT.md) against the accepted source
and signed build. Two questions: whether any path still reports `ok`, a native
result, or a sandbox cause without a supporting observation; and whether the
retained tests and build provenance substantiate the inventory's claims.

Everything below was executed against the build recorded in
[`out/failure-propagation-2/provenance/accepted-build.json`](out/failure-propagation-2/provenance/accepted-build.json).
All 356 source files in `final-source.json` and all seven signed executables in
`accepted-build.json` hash-match the current working tree, so the results here
describe the same implementation the step-2 acceptance describes. No production
or test file was modified; scratch equipment lives outside the repository.

## Question 1 — unsupported `ok`, native results and sandbox causes

**Yes. Seven reachable paths remain.** Three are in the runner's step assembly
and reach the CLI in an `ok` run; one substitutes a host PID; three are in the
controller's other two capture paths, which did not receive the step-2 repair
the runner reply received.

The classifier itself is not the weak point. `classify`
(`CWorkerOrchestrator.swift:896-1041`) gates `ok` on published application,
completion, per-slot completion, a successfully reaped clean exit, no
termination request, resolved wait observations, and — on the validator side —
complete unique ID coverage with no association issue and a confirmed clean
disposition. I could not construct an `ok` run that violates any of those. The
residue is in what happens *inside* an otherwise clean run, and in the two
controller capture paths.

### C1. `ok` plus `drift=true` from a verdict that answers a different query

`associateValidatorVerdicts` (`ValidatorClient.swift:481`) joins a record to a
step by step ID alone. `validatorStructureError` (`ValidatorClient.swift:457`)
requires `operation` and `filter_type` to be present, nonempty strings for
allow/deny — never that they match the probe that was submitted.
`buildSandboxCheckResult` then publishes `operation` from the record
(`CWorkerOrchestrator.swift:574`) while `filter_kind`, `filter_value`,
`effective_filter_value` and `path_diagnostics` come from the request.

Real signed CLI, one step querying `file-read-data` on `/etc/hosts`, with a
validator (selected through the existing `validator_executable_path` override)
that answers step `s` with a `mach-lookup` / `GLOBAL_NAME` /
`com.apple.not.asked` verdict:

```
envelope ok = True | normalized_outcome = ok
association_issues = []
sandbox_check: operation "mach-lookup", filter_kind "path",
               filter_value "/etc/hosts", outcome "deny", rc 1,
               native_rc 1, result_source "validator"
attempt: outcome "ok"        drift = True
```

`drift=true` is the single claim PolicyWitness exists to make, and here it is
made for a `file-read-data`/`/etc/hosts` query that nothing answered. The
validator's actual `filter_value` survives only in
`validator_subprocess.records[].raw_line`; the step-level object is a hybrid no
observer produced. The plan's own standard for step 2 — "syntactically valid
JSON and a matching step ID are insufficient" — is not met: structural
validation checks types and presence, not agreement.

### C2. `sandbox_check.rc = -1` fabricated on a record that reports no native call

`rc: v.rc ?? -1` (`CWorkerOrchestrator.swift:571`) applies to every accepted
record, including diagnostic outcomes that carry no native result at all.
`native_rc` is correctly null, but `result_source` is `validator` and
`missing_reason` is absent because a verdict does exist, so nothing in the step
marks the `-1` as host-synthesized.

This is the shipped, blessed case, not a hypothetical. Running the checked-in
`tests/fixtures/validator/diagnostic.json` transcript (the
`failure_boundaries/validator_frames` unfamiliar-diagnostic control) through the
signed CLI:

```
normalized_outcome = ok
record:  {"outcome":"future_937","error":"unfamiliar diagnostic", ...}   # no rc
step:    rc -1, errno null, outcome "error", native_rc null,
         result_source "validator", error "unfamiliar diagnostic"
```

`-1` is not a neutral value here: it is the documented `prediction_unavailable`
sentinel (`PolicyWitness.md:515`) and it is what the real `sb_api_validator`
emits when `sandbox_check` actually returned `-1`
(`sb_api_validator.c:279-283`). The suite asserts `native_rc is None` and
`drift is None` for this step but never asserts `rc`, so the synthesized value
is unchecked. The contract's "Missing step evidence" section defines the
synthetic `rc=0`/`result_source=synthetic` shape and says nothing about `rc` for
a received non-native record.

The same case also falsifies the public prose: `PolicyWitness.md:484-486` states
that `outcome == "error"` means "`sandbox_check` returned a non-EINVAL failure"
and that `error` carries `strerror(errno)`. That is now untrue both for this
record and for every missing-verdict step.

### C3. A host-created prediction gap reported as `validator_no_verdict`, in an `ok` run

`makeValidatorProbe` decides whether to submit a query using
`pathFilterIsUnresolvable` before the run
(`CWorkerOrchestrator.swift:327`). `buildSandboxCheckResult` decides whether to
synthesize `prediction_unavailable` using the same predicate *after* the run
(`CWorkerOrchestrator.swift:522`). `realpath` is evaluated twice, at two
different times, and the worker's own attempt can change the answer between
them. Step 2 fixed the unlink direction by guarding the exclusion branches with
`!queryRequested`; the create direction has no corresponding guard.

Real signed CLI, step `created` = `file-write-create` query and a `create`
attempt on a path that does not exist yet (the ordinary use of `create`), plus a
second normal step:

```
normalized_outcome = ok           envelope ok = True
validator_subprocess.expected_step_ids = ["present"]      # "created" never submitted
step "created": outcome "error", rc 0, result_source "synthetic",
                missing_reason "validator_no_verdict",
                error "no validator verdict for this step"
```

The contract defines `validator_no_verdict` as "process ran without this
verdict". The host decided not to ask. The envelope assigns the host's own gate
decision to the validator, and uses the `rc=0`/`error` shape instead of the
`rc=-1`/`prediction_unavailable` shape the identical condition produces when the
path is absent at both evaluations. `missing_reason` was added precisely to keep
these owners apart; there is no `query_not_submitted` reason for this case.

### C4. `steps[].sandbox_check.pid` substitutes the runner host PID

`let sbCheckPid = Int(workerOutput?.workerPid ?? pid_t(getpid()))`
(`CWorkerOrchestrator.swift:427`). On an admission failure, with an oversize
`step_id`:

```
normalized_outcome = bad_request      runner_subprocess = null
runner_result.pid = 35287
steps[0].sandbox_check.pid = 35287          # the unsandboxed runner host
```

Step 0 required that worker identity "comes only from a positive
`runner_subprocess.pid`, never a host/client top-level PID". That was enforced in
`sandbox_log::worker_pid` (`controller/src/sandbox_log.rs:126`) but not here,
and `sandbox_check.pid` is the per-step PID a consumer would use for its own log
correlation. The field is not described at all in the per-step documentation
(`PolicyWitness.md:450`), so the host fallback is invisible.

### C5. The controller repairs invalid producer bytes into accepted results

Step 2 fixed exactly one of the controller's three capture paths. The runner
reply parses the original bytes (`runner_client.rs:50-55`,
`serde_json::from_slice(&out.stdout)`). The other two convert with
`String::from_utf8_lossy` first and parse the converted text:
`policy_check.rs:88-97` and `sandbox_log.rs:248-258`.

Executed against the real `run_policy_check` and `capture_sandbox_logs_last`
functions, with fake embedded tools planted next to the test binary so the
production tool-resolution and capture code runs unmodified:

```
policy_check  status=compiled  parse_error=None  compiled=Some(true)
              policy_sha256=Some("\u{fffd}\u{fffd}")      # producer emitted 0xff 0xfe

capture       capture_status=captured  parse_error=None
              deny_events[0].path = "/tmp/\u{fffd}"       # producer emitted 0xff
```

The first reaches `runner_startup_diagnostics.policy_check_status` and the note
"sbpl-check compiled ok" — an accepted compilation result assembled from bytes
the receiver rewrote. The second is kernel-denial evidence: that `path` is what
`match_step_denies` compares against attempt targets, and those events back
`observed_deny` and `first_deny`. macOS paths are arbitrary byte sequences, so
an observer path that is not valid UTF-8 is reachable without any misbehaving
component. The inventory rows "Controller UTF-8 / controller — parse original
untruncated bytes; replacement text is context only" and "Controller capture /
controller" are written without scope and are false for both of these.

### C6. The same two paths report receiver truncation as producer parse failure

```
policy_check  stdout_truncated=true  status="parse_error"
              "EOF while parsing a string at line 1 column 1048576"
capture       stdout_truncated=true  capture_status="parse_error"
              -> correlation_status "unavailable"
```

Valid, complete producer JSON beyond 1 MiB is labelled a producer parse error.
Neither `PolicyCheckCapture` nor `SandboxLogCapture` carries
`*_bytes_received`/`*_bytes_retained` or a `*_capture_error`, so the
controller's own loss is not stated anywhere. This is the defect the plan
named — "parse failure blamed producer" — and told the implementation not to
reintroduce ("relabeling a receiver's truncation as sender corruption").

Reachability is not purely theoretical for the observer: it caps only its
retained raw text at 1 MiB (`sandbox-log-observer.rs:674-682`) while
`deny_lines` and `deny_events[].raw_line` are unbounded and retain every denial
twice, so its envelope can exceed the controller's cap for a worker that
generates a large number of denials in the trailing window.

### C7. `policy_check.status == "ok"` with no compilation observation

`policy_check.rs:113-129`: when the helper exits 0 and its envelope has no
`data.compiled`, `status` becomes `"ok"` while `compiled` stays null.

```
policy_check  status=ok  compiled=None
```

`fallback_policy_note` correctly renders this as "sbpl-check compilation
unavailable", but `policy_check_status` is published as `ok` beside it. The
inventory's "refusal vs compilation failure vs success" acceptance covers three
of the six values `status` can take.

### Documented residual, not a counterexample

`computeDrift` reports `drift=false` for `(prediction=deny, observation=EPERM or
EACCES)` — directional agreement — although the same code states the errno
cannot distinguish the sandbox from ordinary DAC. This is the one remaining
place where the envelope asserts kernel/prediction agreement without an
observation that establishes the cause, and the optional denial-log evidence
that could disambiguate is never consulted by the drift classifier. It is
documented in `PolicyWitness.md:397-403` and `:752`, and `runner_exec_dac`
protects the allow-side asymmetry, so it is a stated trade-off rather than an
unsupported claim. It is worth re-reading against the step-0 rule that "attempt
completion alone does not make a permission failure a proven policy denial".

### What is genuinely closed

No production code emits `runner_sandbox_denied` or `sandbox_apply_failed`; both
survive only as legacy constants. `worker_pid` refuses a host/client top-level
PID, zero and negative PIDs. `first_deny` and `step_denies` are references with
explicit `candidate`/`ambiguous` association and explicit window limits, and
`termination_cause` is only ever `"unknown"` or absent. Unpublished `apply_rc`
storage no longer becomes a reported failure, process status requires a
successful reap, and a completed report no longer falls through to `ok` after an
abnormal disposition. Those repairs hold under every probe I ran.

## Question 2 — do the tests and provenance substantiate the inventory?

**Provenance: fully. Test coverage: mostly, with six qualifications.** Nothing I
found contradicts a *passing* result the step-2 index reports; the gaps are
scope, fixture shape, one flaky control and one crediting mechanism.

### What is substantiated

- **Build provenance is exact.** All 356 files in `final-source.json` and all
  seven executables in `accepted-build.json` hash-match the working tree today —
  zero mismatches. The claim that the CLI results describe this implementation
  is verifiable, not asserted.
- **The accepted selection reproduces.** Re-running the exact step-2 `accepted`
  selector gives **74 pass, 0 fail**, with the app inspection `valid_before:
  true, unchanged: true`.
- **The Swift suite is clean under the dispatcher.** The retained
  `pwrunner_core_tests.log` from that run shows `254/254 tests passed` with
  **0 internal `SKIP` and 0 `FAIL`** — the condition the handoff procedure
  requires before crediting live rows.
- **Rust counts are right.** `cargo test --bins` (what the `unit` case runs) is
  **104/104**. The separate `cli_contract` integration binary adds 10 more, run
  by the `integration` suite, which also passes.
- **The registry as a whole is in better shape than the acceptance claims.** The
  acceptance exercised 74 of the 129 registered catalog cases. I ran the
  remaining 55 as well: **all 129 executed, 127 pass**, with only the two
  `runner_byoxpc` cases in G4 failing.

### G1. The validator "preceding frames survive" control is timing-dependent, and so is the behavior

On the first of twelve standalone runs of the accepted Swift suite:

```
253/254 tests passed
FAIL closed input retains independent I/O and UTF-8 faults plus preceding
     verdict: expected Optional("utf8"), got nil
     (ValidatorEvidenceTests.swift:216)
```

Eleven subsequent runs, including six under heavy CPU load, passed. The
mechanism is in production code, not the fixture: when the child closes its
stdin, the write side sets `ioError` and the loop exits at
`ValidatorClient.swift:337`, then closes the read end at line 342 **without
draining the remaining stdout**. Any verdict or fault byte not already readable
in that poll iteration is lost, `stdout_bytes_received` undercounts, and
`decode_fault` disappears.

So the inventory's "Valid prefix records survive receiver/association/process
faults" and the step-2 index's "Valid prefix records survive … competing I/O
faults" are probabilistic, not guaranteed, whenever the I/O fault fires first.
Step 1C told the worker-side pipe controls to test their boundaries "without
requiring one timing-dependent race"; the validator's equivalent control does
depend on one. The run summary is still defensible (`validator_no_reply`), so
this is evidence loss and an unreliable control, not a false claim.

### G2. The validator fixture cannot expose the step-join defect

`tests/fixtures/validator/validator.py:27,36` builds every verdict as
`dict(probe, kind=..., schema_version=1, ...)` — it echoes the submitted
`operation`, `filter_type` and `filter_value` by construction. Every
`failure_boundaries` validator case therefore has perfect query/verdict
agreement, which makes C1 structurally invisible to the entire suite. The
fixture also asserts `len(probes) == case['probe_count']` and unique step IDs,
so it cannot model a validator that answers a question it was not asked. The
inventory row "Validator verdict structure … implemented and verified" is true
for types and presence and untested for agreement.

### G3. Two inventory rows are written unscoped but implemented once

"Controller capture" and "Controller UTF-8" are both marked implemented and
verified. Their Rust controls live entirely in `runner_client::tests`. The two
sibling capture paths in the same controller (C5, C6) have neither the repair
nor a control. The step-2 index sentence "Real subprocess producers establish
controller-owned 1 MiB truncation … contrasted with malformed/invalid-UTF-8
output within the cap" is accurate only for the runner reply.

### G4. `runner_byoxpc` BBX-001/BBX-002 run the specimen workspace inside the checkout, and raise a TCC prompt

`runner_byoxpc/BBX-001` and `BBX-002` fail here with
`fs_write_allowed: expected sandbox_check allow (got 'deny')`. This is not a
failure-propagation defect — both PW channels agree (`sandbox_check` deny,
attempt EPERM, `drift=false`) — but the cause is a test-equipment path bug that
reaches outside the repository's own scratch space.

`tests/suites/blackbox_e2e/bbx_001.sh:34` and `bbx_002.sh:36` root the
specimen's read/write targets at `WORK_ROOT="${PW_TEST_ARTIFACTS}/workspace"`.
`PW_TEST_ARTIFACTS` resolves under `PW_TEST_OUT_DIR`, which the dispatcher
requires to be inside `tests/out/`, so the probe targets always live inside the
checkout. `tests/suites/runner_byoxpc/run.sh:75-76` reuses those two scripts
under a BYOXPC runner, which is a freshly signed, uniquely identified launchd
service (`com.policywitness.test.byoxpc.s<random>`) staged in `/private/tmp`
with no TCC record of its own. When the checkout lives under `~/Desktop` (or
`~/Documents`), its sandboxed `pw-probe-runner` child therefore reaches a
TCC-protected location as an unknown subject.

Running this suite raised a user-facing Desktop-access prompt. `tccd` recorded
exactly one `AUTHREQ_PROMPTING` in the whole session window:

```
13:15:39.220  AUTHREQ_PROMPTING: service=kTCCServiceSystemPolicyDesktopFolder,
  subject=com.policywitness.test.byoxpc.s1745decfff0d29367e69d9ff
  responsible_path=/private/tmp/pw-byoxpc-.../PWRunner.xpc/Contents/MacOS/PWRunner
  accessing={identifier=pw-probe-runner, pid=48520}
13:15:43.639  AUTHREQ_RESULT: authValue=0, authReason=2          # denied by the prompt
13:15:43.640  TCCDEvent type=Create, identifier=com.policywitness.test.byoxpc.s1745decfff0d29367e69d9ff
```

pid 48520 is the worker whose PID also appears in the retained BBX-001 envelope,
so the denial the case reports is the answer to that prompt, not a PolicyWitness
result. BBX-002 (13:15:50) then resolved from the record just created and failed
identically without a second prompt.

Two consequences beyond the failing assertion. The suite has no `tccutil`
cleanup, and the BYOXPC identifier is unique per install, so each run creates a
fresh TCC subject and leaves an orphan entry in Privacy & Security → Files and
Folders; the next run gets a fresh identifier and prompts again. And the
suite's own result is environment-determined rather than policy-determined.

The fix belongs in the two shell scripts, not in the runner: root `WORK_ROOT`
under `/private/tmp` (as `blackbox_menagerie/run_case.py:41-52` already does for
`core_*`/`opt_*`, and as `runner_byoxpc`'s external-auth case already does for
its bundle staging) and keep only logs and rendered specimens under
`PW_TEST_ARTIFACTS`. The `smoke` leaf is unaffected — its specimen targets
`/etc/hosts` — and the menagerie leaves are unaffected for the same reason,
which is why no Desktop request appears for any byoxpc case before BBX-001.

This is also still an unverified registered case: the step-2 acceptance never
ran the suite, so nothing in the retained evidence would have caught a real
regression there either.

### G5. `TestKit` still credits skips, and a missing-equipment run crashes before its summary

`TestKit.run` (`TestKit.swift:23-27`) counts a guarded early return as a pass;
the contract documents this and says newly required live controls must fail
clearly when equipment is absent. Removing both `PW_LIFECYCLE_WORKER_FIXTURE`
and the app:

```
21 explicit FAIL lines naming the missing equipment      (the new controls — correct)
12 SKIP lines counted as passes                          (legacy CWorkerTests / CWorkerValidatorTests)
WorkerEvidenceTests.swift:115: Fatal error: Unexpectedly found nil ...   rc=133
0 summary lines
```

The new requirement holds. Two things still do not. The older real-worker cases
remain silently creditable. And `WorkerEvidenceTests.swift:115` force-unwraps
the fixture environment variable, so the process traps and the log the handoff
procedure tells the next agent to inspect is truncated mid-suite. The
`runner_unit` wrapper does fail the case ("output missing summary line"), so the
public result is honest; the diagnostic is not.

### G6. Documentation drift behind the implemented contract

- `PolicyWitness.md:484-486` still defines `sandbox_check.outcome == "error"` as
  "`sandbox_check` returned a non-EINVAL failure" with `strerror(errno)`
  populated. Two new producers emit it with no native call (C2, C3).
- `sandbox_check.rc` for a received non-native record is undefined; the
  implementation fabricates `-1`, reusing the documented
  `prediction_unavailable` sentinel.
- `steps[].sandbox_check.pid` and its host fallback are undocumented (C4).
- `policy_check.status` has six values; the documented and tested account covers
  admission refusal, compile failure, success and unavailability (C7).

## Reproduction

All commands were run from the repository root with
`PW_APP_DIR="$PWD/dist/PolicyWitness.app"` and a distinct `PW_TEST_OUT_DIR`
under `tests/out/` (git-ignored). Scratch equipment was written outside the
repository.

| Result | How |
| --- | --- |
| Provenance hash match (356 + 7, zero mismatches) | Recompute SHA-256 for every entry in `final-source.json` and `accepted-build.json` |
| 74/74 accepted selection | `tests/run.sh` with the step-2 `accepted` selector, `PW_TEST_OUT_DIR=tests/out/audit-accepted` |
| Remaining 55 catalog cases | Three further `tests/run.sh` selections covering every suite outside that selector |
| Swift 254/254, 0 SKIP | `suites/runner_unit/pwrunner_core_unit_executable/artifacts/pwrunner_core_tests.log` in the run above |
| G1 flake | `swift run --package-path runner PWRunnerCoreTests` with the `worker_lifecycle` fixtures built into a scratch directory, repeated |
| G5 | The same command with `PW_LIFECYCLE_WORKER_FIXTURE` unset and `PW_APP_DIR` pointing at a nonexistent bundle |
| C1, C3, C4 | Signed-CLI runs with hand-written requests; C1 selects a scratch validator through `_test_overrides.validator_executable_path` |
| C2 | Signed-CLI run replaying the checked-in `tests/fixtures/validator/diagnostic.json` transcript |
| C5, C6, C7 | A scratch copy of `controller/` with an added `#[cfg(test)]` module calling the real `run_policy_check` and `capture_sandbox_logs_last`, with fake `sbpl-check` and `sandbox-log-observer` planted at `<target>/debug/MacOS/` so production tool resolution and capture run unmodified |
| G4 TCC prompt | `log show --predicate 'subsystem == "com.apple.TCC"'` over the session window; one `AUTHREQ_PROMPTING`, attributed to the byoxpc identity and `pw-probe-runner` pid 48520 |

## Limits of this audit

Single machine, single macOS version, one signed build. I did not attempt
destructive XPC or reply-encoding faults, native setup exhaustion, a forced
client timer, or early-stderr capture — the inventory already lists all of those
as gaps and I did not test the claim that they are the *only* gaps. The `ok`
classifier was probed by construction and by reading, not exhaustively; C1
through C4 were found by tracing ownership through the step builder, so other
step-assembly paths may carry similar hybrids. Nothing here shows a false claim
in a *reported* step-2 result, and nothing here should be read as a completeness
statement about failures that were never induced.
