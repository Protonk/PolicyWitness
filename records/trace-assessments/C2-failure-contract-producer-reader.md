# C2 — Failure contract: producer and reader obligations

Read-only assessment at HEAD `837296af` on 2026-11-17. Entries assessed from
`records/DOCUMENTATION-TRACE-REVIEW.md`: the failure-contract investigation's
identity/conventions section, DT-45, DT-47, DT-49, DT-52, DT-54, DT-55, DT-56,
DT-58 and that investigation's coverage/limits section. Coverage-map rows:
DT-45/47/49/52, DT-54/58 and DT-55/56.

`FPC` below means `tests/FAILURE-PROPAGATION-CONTRACT.md`. All `file:line`
references are to the current tree.

## Basis for every row

**Revision relation.** The review inspected source `b8df8953` and an app built
at `8b5de2b2`. `git diff --stat b8df8953 HEAD` over `controller`, `runner`,
`FPC`, `tests/lib/consumer.py`, the lifecycle readers and the four suites named
in the task shows only the regenerated worker identity
(`controller/tools/pw_probe_runner/pw_probe_runner_abi.h:50-51`,
`runner/Sources/PWRunnerCore/CWorker.swift:52-53`) and three added lines in
`tests/suites/runner_c_worker_harness/test_exec_control_states.py`. FPC has the
same 1,627 lines. The review's line numbers are within three lines of the
current ones; each claim was re-read at the current location.

**Evidence availability.** `/private/tmp/pw-failure-trace-elssragi/` is absent.
`dist/PolicyWitness.app` now reports commit `2f4d76e4`, contract
`development:b55acb20…`; its executables do not have the review's SHA-256
values. None of the review's executed observations can be replayed against the
binary that produced them. They remain accounts of what the `8b5de2b2` build
did.

**What this pass did.** Source reading at HEAD, read-only git history, and three
constructed checks through `tests/lib/python.sh` (Python 3.14.9, assertions
enabled). None is a PolicyWitness run:

1. `consumer._step_record_shape` and `blackbox.validate_step` on one in-memory
   step with and without `attempt.errno` (DT-52).
2. Direct execution of the review's five exec argument arrays
   (`/usr/bin/printf`, `/usr/bin/awk`) and a Python model of
   `drain_one`/marker placement/`readString` written from the source as read
   (DT-55/56). The direct sizes were 2,052, 2,053, 9, 4,002 and 4,001 bytes; the
   model gave 1,023 bytes with marker, `HEAD` without marker, `HEAD` without
   marker, absent, and 1,023 bytes/520 characters with marker. These equal the
   review's five rows. This supports the source explanation; it is not an
   observation of the product.
3. `porcelain.decode(b'')` raises `ValueError: wrong porcelain magic or short
   header` (DT-58, recipient side, Python reader only).

**Build-contract inputs.** `docs/build_contract.py:15-27` selects
`controller/src`, `controller/tools`, `controller/interface`, `runner/Sources`,
`runner/Clients`, `runner/Services`, `runner/augments` (suffixes
`.rs .c .h .swift .sb .plist .ent`) and a file list. `FPC`,
`docs/contract/*.surface.md`, `docs/limits.json`, `docs/porcelain.json`,
`runner/Tests/**`, `tests/lib/consumer.py`, `tests/suites/**` and
`tests/fixtures/**` are not inputs. The worker identity
(`docs/generate_worker_identity.py:27-31`) additionally hashes every `.c/.h/.swift`
under `controller/tools/pw_probe_runner` and `runner/Sources`.

**Shared regions.** FPC's copied regions are lines 270-303, 1399-1456 and
1483-1531. No edit proposed below falls inside them. FPC:1101 contains a
generated limit span; only the authored words around it are discussed.

---

## Investigation identity, conventions and limits (review lines 1368-1454, 1918-1960)

These sections qualify every entry below. They are assessed once.

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| FI-1 | Source inspection used `b8df8953`; CLI reproductions used the `dist` app reporting commit `8b5de2b2` with four stated executable hashes. | Record of the review's inputs; 2026-11-16 | Unverifiable by reading: that app is no longer at `dist/`. The commit exists. | Review: recorded identity. Now: `--version` of the current app, `shasum`. | Accurate observation needing no change |
| FI-2 | `git diff --stat 8b5de2b2 b8df8953` shows no change to product sources or the readers used. | Source comparison, not a build | Yes: the only non-record change is `tests/suites/preflight/opt_in/build_refusals.py`. | Re-run of the same read-only git command. | Accurate observation needing no change |
| FI-3 | Requests, fixture scripts, child output and envelopes were under `/private/tmp/pw-failure-trace-elssragi/`, outside retained evidence; the decisive inputs and results are in the record. | Local scratch | Yes as stated; the directory is absent. The record's inputs were sufficient to rebuild the direct child controls for DT-55/56. | Path check. | Accurate observation needing no change |
| FI-4 | The first baseline inside the automation sandbox ended `xpc_acquisition_failed` (4099/159); the same command outside it returned `finished`. This supports an environmental explanation for that lookup failure only. | One command, two environments | Unverifiable by reading; consistent with `runner/AGENTS.md` guidance. | Review: executed, unavailable. | Accurate observation needing no change |
| FI-5 | The baseline request (one `file/open_read` of `/etc/hosts` under `(allow default)`) gave one completed attempt, an associated native allow record, `query_first` and valid disposition diagnostics. | Ordinary form, that build and machine | Unverifiable by reading. | Review: executed, unavailable. | Accurate observation needing no change |
| FI-6 | Controlled-validator probes add `_test_overrides.validator_executable_path`; the scripts call no `sandbox_check`, so they show handling of controlled transcripts through the real host, client and controller beside a real worker attempt, and supply no native prediction evidence. | Constructed validator transcript, live host | Yes as a convention. `validator_executable_path` is one of the eight controls the management plan moves to `test-input run`; after that migration this reproduction route is refused on an ordinary submission. | Plan reading. | Accurate observation needing no change |
| FI-7 | Reader mutations are constructed JSON given directly to a named reader, not host replies. | Saved JSON, Python readers | Yes. | Reading. | Accurate observation needing no change |
| FL-1 | The contract was read end to end; listed traces were followed; selected history was examined; no past battery was re-credited. | Scope statement | Not re-verifiable; nothing contradicts it. | — | Accurate observation needing no change |
| FL-2 | Within their inputs: the baseline preserved query, slot and ordered comparison; controlled invalid or overlarge validator output kept worker results and earlier accepted records; the exec output losses left process observations intact; the lifecycle oracle rejected two constructed claim faults the consumer accepted. | Named build and specimens | Unverifiable by reading for the executed parts. The exec statement agrees with the source: stream text and `exec_observation` are read from separate slot fields (`runner/Sources/PWRunnerCore/ActorSession.swift:672-680`). | Review: executed, unavailable. | Accurate observation needing no change |
| FL-3 | Not established: exhaustive branch coverage; actor authority, custody, equipment, capture, reservation and fallback beyond context; native-call substitutions, clock or cleanup faults, mutation battery, build pipeline, BYOXPC, kernel denial; the scalar-only failure and the unused encoded bytes were inspected, not executed. | Limits | Yes; this pass did not execute them either. | — | Accurate observation needing no change |
| FL-4 | Live observations apply to the named build, machine and specimens; controlled validator output is not a sandbox verdict; a direct child control is a different process from the one PolicyWitness spawned; saved-JSON mutations are not reachability evidence. | Interpretation limits | Yes. The same limits apply to this pass's model check. | — | Accurate observation needing no change |

Disposition for all eleven: retain as written. They need no product, test or
account change. An implementer who needs an executed observation from this
investigation must rerun the applicable control on an identified build; the
review's descriptions are enough to rebuild the inputs.

---

## Subject A — DT-45/47/49/52: four separate producer/reader obligations

The four entries share only the document that states them. Each has its own
statement, producer and checking assertion.

### A.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-45.a | FPC says parameter allocation, parameter setting, the parameter NUL check and compilation can write `apply_rc = -1`, and requires a status-word failure without a failure record to keep R and nonzero `apply_errno` in `error`. The worker's preparation and compile branches publish failure records and do not assign `apply_rc`. | C worker, pre-application failure branches; shared-memory header word | Yes. Statement: FPC:27-41, rows at FPC:57 and FPC:67. Producer: `controller/tools/pw_probe_runner/pw_probe_runner.c:1540-1545`, `:1548-1553`, `:1558-1565`, `:1576-1588` call `pw_failure` then `publish_done_and_exit`; the only assignment is `:1644`. | Review: source inspection. Now: re-read; `git show bc3abe2f` removes four `hdr->apply_rc = -1;` lines. | Contradicted explicit commitment |
| DT-45.b | For an unapplied worker the host takes `applyRC` only from an eligible native apply-failure record, otherwise zero; `done` does not authorize reading the scalar; `classify` gives one message whatever the scalar holds. | Swift host final collection and classifier | Yes. `runner/Sources/PWRunnerCore/ActorSession.swift:640-643`; `runner/Sources/PWRunnerCore/CWorkerDisposition.swift:352-355`. | Review: source inspection. Now: re-read. | Contradicted explicit commitment |
| DT-45.c | Two tests assert that behavior explicitly: constructed done/unapplied outputs with `applyRC = -1` and errno 0, 1 or 4567 must equal the zero-storage diagnostic; the ABI fixture's `reported_failure_hang` must decode as `applyRC = 0`, `applyErrno = 0`, no failure record. | Constructed `CWorkerOutput`; test-only ABI child through the real driver | Yes. `runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift:234-250` (and row `:72-75`); `runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift:414-434`; fixture write at `tests/fixtures/worker_lifecycle/worker.c:470-471`. | Review: read, not run. Now: re-read, not run. | Accurate observation needing no change |
| DT-45.d | FPC's coverage table still describes `reported_failure_hang` as a published status-word failure that is preserved. | Authored coverage row | Yes. FPC:684 ("published status-word failure then cleanup"). | Re-read. | Overstated coverage credit |
| DT-45.q | Qualification: the promise dates from `0670db1d`; `bc3abe2f` changed implementation and assertions; this is inspection, the cases were not rerun; no claim that an ordinary current worker produces a scalar-only terminal failure. | History and limit | Yes. `bc3abe2f` is first contained in `v0.3.5`; `0670db1d` in `v0.2.3`. | Read-only git. | Accurate observation needing no change |
| DT-47.a | Two FPC coverage rows credit process facts "through actual subprocess encoding"; the tests assign `decoded = buildWorkerSubprocess(out)`, leave `data = try pwPorcelainEncode(decoded)` unused, and assert on `decoded`. A writer that succeeded while dropping a field would pass these assertions. | Swift unit cases with a real worker; typed record before encoding versus encoded bytes | Yes. Rows FPC:675 and FPC:676. `runner/Tests/PWRunnerCoreTests/CWorkerTests.swift:417-424` and `:461-466`. | Review: source inspection. Now: re-read. | Overstated coverage credit |
| DT-47.b | `2d5080d7` replaced an encode/decode round trip with these assignments. | History | Yes: the diff removes `pwRunnerDecodeJSON(PWRunnerSubprocess.self, from: data)` at both sites. | Read-only git. | Accurate observation needing no change |
| DT-47.q | Qualification: the cases still drive a real worker and assert acquired publications, reap, kill absence and classification; `ReplyFailureTests` receipts and their independent readers give other binary coverage; no claim that the writer drops fields; not a mutation run. | Limit | Yes. Receipt replay: `tests/suites/runner_unit/run.sh:57-59`, `tests/suites/runner_unit/porcelain_replies.py`. | Re-read. | Accurate observation needing no change |
| DT-49.a | FPC says a received diagnostic without a native return keeps `native_rc = null` and `rc = -1`; RESPONSE says an associated record supplies its carried return and -1 only when the record omits it. | Query channel; an accepted validator record whose outcome is outside `allow`/`deny`/`error` | Yes. FPC:1111-1113; `docs/contract/31-steps.surface.md:65-67` (rendered at `docs/RESPONSE.md:964`). | Re-read. | Inaccurate mechanism account (FPC) |
| DT-49.b | A controlled transcript with `outcome = "future_937"`, `rc = 17`, `errno = 5` projected `outcome: error`, `result_source: validator`, `native_rc: null`, `rc: 17`, `errno: 5`; the run stayed `finished`, order unestablished; both Python readers accepted. | Substituted validator through the real host and CLI; `8b5de2b2` build | Unverifiable by reading as an execution. The source gives the same result: `runner/Sources/PWRunnerCore/CWorkerStepResults.swift:47-49` selects `native_rc` by outcome spelling and `:129` selects `rc` by `v.rc ?? -1`. | Review: executed, unavailable. Now: source. | Accurate observation needing no change |
| DT-49.c | The `failure_boundaries` diagnostic assertion requires -1 for a fixture whose diagnostic omits `rc`; it does not establish the unqualified rule. | Registered case, constructed transcript | Yes. `tests/suites/failure_boundaries/check.py:346-352`; `tests/fixtures/validator/validator.py:46-49` (`verdict.pop('rc')`). | Re-read. | Accurate observation needing no change |
| DT-49.q | Qualification: this is forwarding of a constructed diagnostic, not a native return of 17; the carried-return expression predates the contract. | Limit | Yes for the first part. The June 2026 history statement was not re-verified and does not affect the disposition. | — | Accurate observation needing no change |
| DT-52.a | FPC requires key presence for a null step `errno`; the host supplies `attempt.errno: null`; `consumer.validate` returns `[]` for a saved bare reply with `steps[0].attempt.errno` deleted. | Saved public JSON given to `tests/lib/consumer.py`; hand mutation | Yes. FPC:637, FPC:866-867. `tests/lib/consumer.py:485` tests `attempt.get('errno') is not None`. Constructed check today: `_step_record_shape` returns `[]` with and without the key. | Review: executed constructed control, unavailable. Now: constructed in-memory check. | Consequential ambiguity (which reader holds the presence obligation is unstated) |
| DT-52.b | The lifecycle oracle also returned `[]` for the mutated reply inside an envelope copy; it does not validate capture/JSON equality. | `tests/lib/lifecycle_oracle.py` | Not re-run. Consistent with FPC:595-596, which says the oracle is not a complete shape validator. | Review: executed, unavailable. | Accurate observation needing no change |
| DT-52.c | Mechanism: the consumer equates absence and null; shape goldens allow absent keys; the checker controls reject a missing attempt `rc` and a fractional attempt `errno`, but the deletion is not one of them. | Reader source and its controls | Yes. `tests/lib/consumer.py:322-357` (allowlist), `:483-486`; `tests/suites/blackbox_e2e/checker_controls.py:498-500`. | Re-read. | Accurate observation needing no change |
| DT-52.d | Deleting query `errno` from a diagnostic reply passed; deleting it from the ordered baseline was rejected, through the ordering dependency, not through a required-key check. | Saved JSON, query channel | Consistent with source: `tests/lib/consumer.py:268-270` requires `type(err) is int` only inside order eligibility. Not re-run. | Review: executed, unavailable. | Accurate observation needing no change |
| DT-52.q | Qualification: a mutation of a saved reply, not a host omission; no product serialization change is inferred. | Limit | Yes, and stronger: both projections emit the key by construction (see A.2). | Re-read. | Accurate observation needing no change |

### A.2 Comparison

**DT-45 — status word.**

- Obligation as stated (owner FPC, authored prose outside the copied regions).
  FPC:27-30: "Parameter allocation, parameter setting, the defensive parameter
  NUL check, and compilation can all write -1. `apply_errno` is populated only
  for an actual failed application". FPC:35-37: "For a published status-word
  failure (no failure record), retain R and any nonzero `apply_errno` in the
  runner's `error` diagnostic as published status values". Row FPC:57 gives
  "A=false, D=true, R nonzero" its own account; row FPC:67 keeps "the reported
  failure" through later cleanup; the precedence list at FPC:73-76 names
  "published status-word worker failure".
- Producer. The worker writes `apply_rc` once, with the return of
  `sandbox_apply` (`pw_probe_runner.c:1641-1644`). Every earlier failure branch
  publishes a failure record with operation, code and native result and then
  `done`. `apply_errno` is written only after a failed application (`:1651`).
- Host reader. Without A the host does not read the header word: `applyRC` is
  the failure record's native result when that record is a published native
  apply failure, otherwise 0, and `applyErrno` comes from the same record
  (`ActorSession.swift:640-643`). `classify` reports a failure record first
  (`CWorkerDisposition.swift:289-334`), then an incomplete failure publication
  and the authority-setup refusals (`:335-347`), then an applied worker with a
  nonzero word as inconsistent (`:348-351`), then any `done` without `applied`
  as "completed without an observed application; no native apply return is
  inferred" (`:352-355`), all before the sentinel-deadline branch (`:361`).
  `CWorkerDisposition.swift:286` says the precedence is specified in FPC.
- Assertions. `HostOutcomeClassifierTests.swift:234-250` requires the
  diagnostic for stored -1/errno to equal the zero-storage diagnostic and to
  contain neither `status=-1` nor `apply_errno=`.
  `CWorkerLifecycleTests.swift:414-434` requires the driver to decode the
  fixture's written word as 0 with no failure record and still preserve `done`
  and the cleanup SIGKILL. `runner_c_worker_harness/compile_failure`
  (`tests/suites/runner_c_worker_harness/run.sh:454-481`) asserts the published
  compile failure record and deliberately asserts nothing about the scalar.
- Inference kept apart: no specimen was shown to reach a record-less terminal
  failure with the shipped worker. By reading, R is written only at
  `pw_probe_runner.c:1644`, and a nonzero value there is accompanied by the
  application failure record at `:1646`. "R nonzero, no failure record"
  (FPC:35-41, FPC:57) therefore arises only from a different worker program;
  the lifecycle ABI fixture is one. Two record-less terminal publications
  without A do exist in the actor form, both with R still zero: a required
  authority-setup refusal (`pw_probe_runner.c:766`, classified at
  `CWorkerDisposition.swift:340-343`) and an unapplied actor's ordinary
  completion (`:1702`; `runner/Sources/PWRunnerCore/ActorOrchestration.swift:278-284`
  gives the classifier a view with the declared setup in place of A). A
  corrected ordinary-form statement must not be worded so as to cover them.

**DT-47 — encoded facts.**

- Obligation as stated (owner FPC coverage table, authored). FPC:675: the late
  `done` case "records `sentinel_deadline`, reaped exit 0, and no termination
  request through actual subprocess encoding". FPC:676: the self-signal case
  "asserts applied/not-done/no-host-kill/SIGKILL, `child_reaped` and encoded
  process facts".
- What the tests do. Both build the typed `PWRunnerSubprocess`, encode it
  without using the bytes, and assert on the typed record
  (`CWorkerTests.swift:417-424`, `:461-466`). What is established: the real
  worker, the driver's final snapshot, the assembler's fields, and that the
  writer accepts the record. Not established by these assertions: any property
  of the bytes.
- Where encoded facts for the same two situations are asserted. Through the
  CLI, Swift writer, XPC client and Rust reader:
  `witness_contract/worker_attempt_in_flight_at_deadline` requires
  `poll_stop_reason == 'sentinel_deadline'`, `exit_code == 0`, `reaped`,
  `done_observed` and `termination_request is None` for a worker that exits
  during grace (`tests/suites/witness_contract/check_attempt_in_flight.py:236-246`);
  `witness_contract/worker_termination` requires `term_signal == 9`,
  `poll_stop_reason == 'child_reaped'`, `reaped` and no termination request for
  a self-signalled worker
  (`tests/suites/witness_contract/check_worker_termination.py:66-71`).

**DT-49 — diagnostic `rc`.**

- Obligations as stated. FPC:1111-1113 (authored): "A received diagnostic
  without a native return retains `result_source="validator"`,
  `native_rc=null` and `rc=-1`". Public owner
  `docs/contract/31-steps.surface.md:67`: "An associated record supplies its
  carried return, or -1 if that record omits the return."
  `docs/contract/31-steps.surface.md:59`: `native_rc` is the "Native return
  carried by an associated allow, deny or error record".
- Producer. `CWorkerStepResults.swift:47-49` and `:129`, two independent
  selections. The shipped validator emits `rc` on every record that reached
  `sandbox_check` and classifies `rc == -1 && errno == EINVAL` as
  `unsupported_operation`
  (`controller/tools/sb_api_validator/sb_api_validator.c:396-408`); records that
  failed earlier omit `rc` (`:439-450`). So for every record the shipped
  validator writes, `native_rc == null` coincides with `rc == -1`. The two
  statements diverge only for a record carrying a return under an outcome
  outside the three spellings, which the shipped validator does not write.
- Assertions. `failure_boundaries/validator_frames` covers the omitted-return
  diagnostic only (`check.py:346-352`). `runner_exec_dac` requires `rc == -1`
  for a real `unsupported_operation`
  (`tests/suites/runner_exec_dac/check_query_scope.py:148`). No registered
  assertion was found for a diagnostic that carries a return.

**DT-52 — attempt `errno` key.**

- Obligation as stated. FPC:637: "a null per-step `errno` requires key
  presence." FPC:866-867 repeats it. Public notation:
  `docs/CONTRACT.md:1641-1643` — "`T ∪ null` keeps the key present"; RESPONSE
  renders attempt `errno` as `integer ∪ null` (`docs/RESPONSE.md:1005`).
  FPC:594-595 describes the consumer as combining "shape-golden checks with
  required-field and semantic checks" and does not say which reader checks
  nullable-key presence.
- Producer. `docs/porcelain.json` marks `PWRunnerAttemptResult.errno`
  `json_null: true`. The generated Rust serializer writes the key
  unconditionally (`controller/src/porcelain_records.rs:1491`; the query
  `errno` at `:3517`). The Python structural reader also inserts `None` for an
  absent `json_null` field (`tests/lib/porcelain.py:87-92`). An absent key can
  therefore appear only in JSON edited after projection.
- Readers. `tests/lib/consumer.py:485` checks the type of a present value.
  `tests/lib/blackbox.py:231-233` requires the keys `rc`, `errno`,
  `requested_path`, `observed_path` on the attempt and `:202-204` requires
  `pid`, `operation`, `filter_value`, `filter_type_id`, `errno`, `error` on the
  query. Constructed check today: `blackbox.validate_step` reports
  `missing attempt.errno` for the deleted key.
- Assertions. Rejected controls for the deletion exist where
  `validate_step` is the reader: `blackbox_menagerie/validation_controls`
  (`tests/suites/blackbox_menagerie/checker_controls.py:167-177`, attempt and
  query `errno`) and `runner_specimen_isolation/overlapping_runs_keep_evidence_separate`
  (`tests/suites/runner_specimen_isolation/check.py:193-195`, `:257-260`). The
  review's "neither Python reader rejected" is true of the two readers it
  named (`consumer.validate`, the lifecycle oracle); it did not examine
  `validate_step`.

### A.3 Plausible treatments

**DT-45**

| Treatment | Files | Build-contract input | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- |
| T45-1 Correct the account in its owner | FPC:20-41 (definition of R and the retention paragraph), rows FPC:57-58 and FPC:67, precedence FPC:73-76, FPC:641-642, coverage row FPC:684. Authored prose; no generator owns these lines. | No | The contract stops promising R and `apply_errno` in `error` for a record-less terminal publication. Diagnostics are as they have been since `v0.3.5`. Readers are told to use `runner_subprocess.worker_evidence.failure`. | A host that reads the header word without A: existing `runner_unit/pwrunner_core_unit_executable` (`HostOutcomeClassifierTests.swift:234-250`, `CWorkerLifecycleTests.swift:414-434`). A worker that fails compilation without a failure record: `runner_c_worker_harness/compile_failure`; at the CLI `witness_contract/worker_progress_and_failure`. |
| T45-2 Restore the scalar path in the product | `pw_probe_runner.c` (four branches), `ActorSession.swift:642-643`, `CWorkerDisposition.swift:352-355`, and reversal of the two tests in DT-45.c | Yes; worker identity regeneration and a signed rebuild | Adds a second, imprecise failure channel beside records that already name operation, code and native result. No user gains information from the shipped worker. | — |

**DT-47**

| Treatment | Files | Build-contract input | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- |
| T47-1 Correct the two coverage rows | FPC:675, FPC:676 | No | The rows credit the real worker, driver snapshot, assembled record and classifier, say that encoding completes, and name the CLI cases that assert the encoded facts. | Already rejected at the CLI by `witness_contract/worker_attempt_in_flight_at_deadline` and `witness_contract/worker_termination`: a reply whose process facts differ after encoding and decoding. |
| T47-2 Assert on the bytes | `CWorkerTests.swift:417-418`, `:461-462` write `data` under `PW_TEST_ARTIFACTS` (the pattern of `retainDispositionReceipt`, `DispositionResolverTests.swift:104-111`); `tests/suites/runner_unit/porcelain_replies.py` decodes a `PWRunnerSubprocess` at offset 36 (as `:98-103` does) and asserts the facts | No (`runner/Tests` and `tests/suites` are not inputs); needs the signed app's worker to run | Adds unit-level encoded coverage that duplicates the CLI assertions. | A writer that returns successfully while dropping or changing `poll_stop_reason`, `exit_code`, `term_signal`, `reaped` or `termination_request`. |

**DT-49**

| Treatment | Files | Build-contract input | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- |
| T49-1 Correct the FPC sentence to the public meaning | FPC:1111-1113 | No | One statement of `rc` for a diagnostic: the record's carried return, or -1 when the record carries none. RESPONSE is unchanged. | — |
| T49-2 Add the carried-return control | `tests/fixtures/validator/validator.py` (a diagnostic tail that keeps `rc`/`errno`), `tests/suites/failure_boundaries/check.py` beside `:346-352` | No; needs the signed app. `failure_boundaries/check.py` is a caller of the validator-substitution seam and follows that migration. | Pins what RESPONSE already says. | A host that forces `rc` to -1 for a carried return, or that fills `native_rc` from a record whose outcome is not `allow`, `deny` or `error`. |
| T49-3 Change the product so `rc` is -1 whenever `native_rc` is null | `CWorkerStepResults.swift:129`; `docs/contract/31-steps.surface.md:67`; goldens | Yes | Changes a public meaning and removes a carried value from the step (the raw record keeps it). | — |

**DT-52**

| Treatment | Files | Build-contract input | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- |
| T52-1 State the reader's scope in the owner | FPC:594-603 ("Reader validation responsibilities") | No | Says where nullable-key presence is established and checked. No reader changes. | Existing: `blackbox_menagerie/validation_controls` rejects a deleted attempt or query `errno`. |
| T52-2 Add the presence check to the consumer | `tests/lib/consumer.py:483-486`; `tests/suites/blackbox_e2e/checker_controls.py` beside `:498-500` with a passing null control (`:205`) and a rejected deletion | No | `consumer.validate` mirrors `validate_step` for this key. Every caller of `consumer.validate` over hand-authored steps must carry the key; `tests/fixtures/contract/exec_observation.json` omits it in 51 attempt objects, which Python reads through `validate_exec_observation` only (`checker_controls.py:144-155`). | `consumer.validate` returning `[]` for a step whose attempt lacks `errno`. |

### A.4 Recommended disposition per claim

| Id | Disposition | Reason and check |
| --- | --- | --- |
| DT-45.a, DT-45.b | T45-1. Correct FPC to: R is the header's `apply_rc` word, written only with the return of the application call and read by the host only beside A; preparation and compilation failures publish a failure record and leave R unwritten; in the ordinary form a terminal publication without A and without a failure record is reported as completed without an observed application, and neither R nor `apply_errno` is read (the actor form's setup account keeps its own section, FPC:194-240). Merge row FPC:57 into FPC:58; reword FPC:67 to "terminal publication without application followed by …"; replace "published status-word worker failure" in FPC:73-76 with "terminal publication without an observed application"; adjust FPC:641-642 so it no longer refers to an imprecise published status. | The product behavior is deliberate, asserted and, since `v0.3.5`, released. The older promise retains less than the failure records now carry. Checks: the two `runner_unit` cases in DT-45.c and `runner_c_worker_harness/compile_failure`. Further evidence would not change this: the question is which statement is current, and the source and tests agree. This withdraws a stated commitment and must be recorded as that, not as a test reclassification. |
| DT-45.c | No change to the tests. | They assert the current behavior with constructed and fixture inputs and say so. |
| DT-45.d | Reword FPC:684 from "published status-word failure then cleanup" to "terminal publication with a written status word and no failure record, then cleanup: the word is not read". | Same owner as T45-1; lands with it. |
| DT-45.q | Retain. | Accurate. |
| DT-47.a | T47-1. Reword FPC:675 and FPC:676 to credit the assembled record and successful encoding, and to name `witness_contract/worker_attempt_in_flight_at_deadline` and `witness_contract/worker_termination` for the encoded facts. | Smallest treatment that leaves the rows true; the encoded facts already have more integrated owners. T47-2 remains available if unit-level byte coverage of real-worker records is wanted; it is not required for any stated claim. |
| DT-47.b, DT-47.q | Retain. | Accurate. |
| DT-49.a | T49-1 with T49-2. | FPC is the less precise of two statements and the producer follows the public one. T49-2 gives the corrected sentence a registered check; the review's execution is no longer available. |
| DT-49.b, DT-49.c, DT-49.q | Retain. | Accurate. The observation in DT-49.b becomes the T49-2 control's expected result. |
| DT-52.a | T52-1. Add beside FPC:594-596: key presence for a nullable step field is produced by the schema projection, which writes `null` for an absent value in both the Rust serializer and the Python structural reader; on public envelopes `tests/lib/blackbox.py` `validate_step` rejects a missing key; `consumer.validate` checks the type of a present value and accepts an absent one. | No stated claim is false; the gap is that the contract names one reader and the presence check lives in another. Check: `blackbox_menagerie/validation_controls`. T52-2 is a legitimate strengthening and may be taken with it; nothing recommended here depends on it. |
| DT-52.b, DT-52.c, DT-52.d, DT-52.q | Retain. | Accurate. DT-52.d's ordering dependency is unchanged. |

Accepted limit for DT-52, to stand in FPC's reader section: "`consumer.validate`
does not establish that a nullable step key is present; it accepts an absent
`errno` as it accepts `null`."

### A.5 Resulting user duties

- DT-45: read a pre-application failure from
  `runner_subprocess.worker_evidence.failure`; do not expect a status value or
  `apply_errno` in `error` text.
- DT-47: none.
- DT-49: recognise a diagnostic without a native return by `native_rc: null`
  and its outcome, not by `rc == -1`.
- DT-52: when validating saved JSON with `consumer.validate` alone, do not
  conclude that nullable keys were present.

### A.6 Implementation worklist

1. FPC, DT-45: edit FPC:20-41, FPC:57-58, FPC:67, FPC:73-76, FPC:641-642 and
   FPC:684 as in A.4. Also correct FPC:678 (see "Outside the review", item 1).
2. FPC, DT-47: edit FPC:675 and FPC:676 as in A.4.
3. FPC, DT-49: edit FPC:1111-1113. Then add the carried-return tail to
   `tests/fixtures/validator/validator.py` and its branch to
   `tests/suites/failure_boundaries/check.py`, expecting `native_rc is None`,
   `rc == 17`, `errno == 5`, `outcome == 'error'`, `result_source ==
   'validator'`, `finished`, order `unestablished`, with the raw record under
   `phases[0].validator_subprocess.records` keeping `future_937`. Sequence this
   with the seam migration of `validator_executable_path`.
4. FPC, DT-52: add the reader-scope sentence at FPC:594-603.
5. Regeneration: none owns these lines. Run
   `tests/lib/python.sh docs/generate_limits.py --check` because FPC is a span
   document.
6. Verification: `tests/run.sh --suite source_drift` for the documentation
   edits; `tests/run.sh --case failure_boundaries/validator_frames` for item 3
   on a signed app. No `tests/CHANGE-VERIFICATION.md` control is triggered by
   items 1, 2, 4.

---

## Subject B — DT-54/58: account corrections

### B.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-54.a | FPC lists `stdout_collection_stop` as `eof`, `deadline`, `read_error` or `poll_error`; RESPONSE also lists `clock_error` and `byte_limit`; the guide's validator-storage limit describes the latter. | Validator stdout collection, per phase | Yes. FPC:1131-1132; `docs/contract/32-lifecycle.surface.md:1109-1111`; `docs/limits.json` `validator_reply_bytes_per_query` (`effect`). | Re-read. | Inaccurate mechanism account (FPC) |
| DT-54.b | A fixture writing one allow record and 20,000 spaces produced `stdout_collection_stop: byte_limit`, `stdout_bytes_received: 20200`, matching I/O and read diagnostics naming 16,384 bytes, null `decode_fault`, validator exit 0 with confirmed reap, `validator_no_reply`, exit 1; the valid record and `query_first` were kept; both Python readers accepted. | Substituted validator, real host and CLI, one query; `8b5de2b2` build | Unverifiable by reading as an execution. Consistent with source and with a registered case (B.2). | Review: executed, unavailable. | Accurate observation needing no change |
| DT-54.c | The byte-limit branch runs before decoding and removes the cut fragment; `clock_error` is produced separately and was not exercised. | Swift collector | Yes. `runner/Sources/PWRunnerCore/ValidatorClient.swift:363-375`; `:279-283`. | Re-read. | Accurate observation needing no change |
| DT-54.q | Qualification: an incomplete vocabulary account, not lost prediction evidence or a decoder fault; the assignment dates from `66d41b5e`. | Limit | Yes (`66d41b5e` is first contained in `v0.3.0`). | Read-only git. | Accurate observation needing no change |
| DT-58.a | FPC calls the minimal `runner_reporting_failed` reply the "final path"; RESPONSE describes a further branch in which a failing minimal writer returns empty bytes. | Host reply encoding | Yes. FPC:108-114; `docs/contract/30-reply.surface.md:273`, `:277-278`. | Re-read. | Inaccurate mechanism account (FPC) |
| DT-58.b | The service evaluates `(try? minimal(result, finalDiagnostic)) ?? Data()`; a test injects throwing rich and minimal closures and requires two rich calls, one minimal call and empty data; this is separate from the text-cap test in which the minimal writer succeeds. | Swift service function; constructed closures | Yes. `runner/Sources/PWRunnerCore/PWRunnerService.swift:149-154`; `runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift:314-330`; text-cap case from `:247`. | Re-read, not run. | Accurate observation needing no change |
| DT-58.q | Qualification: empty data is not the literal `{}` the wording forbids; no encoder failure, empty reply or specimen reaching the branch was executed; production reachability is unresolved. | Limit | Yes. This pass found no route by reading and ran none. | — | Accurate observation needing no change |

### B.2 Comparison

**DT-54.** Owner of the public meaning:
`docs/contract/32-lifecycle.surface.md:1111` — "Host reason for stopping stdout
collection: eof, clock_error, deadline, poll_error, byte_limit or read_error.
This is fixed before the exit-grace stage." FPC:1131-1132 restates four. The
collector assigns exactly six values (`ValidatorClient.swift:271`, `:280`,
`:285`, `:312`, `:368`, `:379`). FPC:1130-1131 also says `read_error`
"independently retains a read/poll/deadline failure"; the same variable is set
on the clock and byte-limit branches (`:281`, `:369`).

Support for the corrected scope, value by value:

- `byte_limit`: `witness_contract/phases` through the CLI
  (`tests/suites/witness_contract/check_phases.py:134-138`: stop value, one
  retained record, received bytes in (16384, 24576], reap, attempt `rc` 0) and
  `runner_unit` (`runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift:90-96`).
  Both use a substituted validator.
- `eof`, `deadline`: several cases, for example
  `tests/suites/witness_contract/check_diagnostic_transport.py:130` and
  `tests/suites/runner_outcome_validator_no_reply/check.py:55`.
- `clock_error`, `poll_error`, `read_error`: no assertion on these values was
  found under `runner/Tests`, `tests/suites` or `tests/lib`. They are
  source-read.

**DT-58.** Owner of the public meaning:
`docs/contract/30-reply.surface.md:273` — "If either operation fails again, use
the independent minimal writer … If that writer fails, return empty bytes."
and `:277-278` — "Empty reply bytes reach the recipient's decoding failure."
FPC:108-112 stops at the minimal reply and calls it final. The producer matches
the surface. Support: the constructed test in DT-58.b establishes the return
value of the service function under injected faults. It does not exercise a
recipient. By reading, a host result that fails decoding is refused as
`malformed_runner_response` (`controller/src/runner_client.rs:623-631`), and
the Python reader raises on zero bytes (constructed check 3); no registered
case that submits a zero-length host result was found. The surface's own
support note (`30-reply.surface.md:286`) says the "minimal/empty paths are read
in source", which credits less than the test asserts.

### B.3 Plausible treatments

| Treatment | Files | Build-contract input | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- |
| TB-1 Correct FPC's stop list and the `read_error` clause | FPC:1128-1133 | No | FPC agrees with RESPONSE and the collector. Readers that enumerate the values handle six. | Existing: a collector that crosses the byte allowance and reports another stop value or decodes the cut fragment (`witness_contract/phases`, `runner_unit`). |
| TB-2 Replace FPC's restated list with a reference to the RESPONSE field | FPC:1131-1132 | No | Removes a second statement that can drift. Arrangement change only. | — |
| TB-3 Correct FPC's reply-construction paragraph | FPC:108-114 | No | States the empty-bytes branch and that no structured account exists on it. | Existing constructed control: a service function that returns a nonempty result, or calls the rich writer a third time, when the minimal writer fails (`ReplyFailureTests.swift:314-330`). |
| TB-4 Add a recipient-side control for a zero-length host result | Rust client-capture controls in `controller/src/runner_client.rs` tests or `tests/suites/blackbox_e2e/runner_client_capture_controls.py` | The Rust file is an input; the Python control is not | Would establish the controller's label for the branch. | A controller that admits a zero-length host result or reports a host outcome for it. |

### B.4 Recommended disposition per claim

| Id | Disposition | Reason and check |
| --- | --- | --- |
| DT-54.a | TB-1. FPC:1131-1132 lists `eof`, `clock_error`, `deadline`, `poll_error`, `byte_limit` and `read_error`; the preceding clause says `read_error` keeps the read, poll, deadline, clock or byte-limit diagnostic. | The public statement and the producer agree; FPC omits two reachable values. Checks: `witness_contract/phases` and `runner_unit/pwrunner_core_unit_executable` for `byte_limit`. The corrected text must not say that `clock_error`, `poll_error` or `read_error` are exercised; they are not. TB-2 is an acceptable alternative form of the same correction. |
| DT-54.b, DT-54.c, DT-54.q | Retain. | Accurate. DT-54.b's values are those the registered `phases` case asserts in the same shape. |
| DT-58.a | TB-3. After the minimal-reply sentence add: if the minimal writer also fails, the host returns zero bytes; the recipient cannot decode them and no reporting-failure object, identity or original summary is delivered. Keep "never substitutes `{}`". Change "This final path" to name the minimal reply as the last structured form. Keep the closing sentence that these paths are tested with constructed results and an internal encoder fault, which is true of the empty branch as well. | The public statement and producer agree; FPC stops one branch early. Check: `runner_unit/pwrunner_core_unit_executable` (`ReplyFailureTests.swift:314-330`). The corrected text states the host side only; the recipient's label for zero bytes is source-read. |
| DT-58.b | Retain. | Accurate. |
| DT-58.q | Retain; reachability stays unresolved. | Deciding it needs an encoder fault that defeats the independent minimal writer on a real result. No such input is known, and the account correction does not depend on it. TB-4 is not required for the correction. |

### B.5 Resulting user duties

- DT-54: a reader that switches on `stdout_collection_stop` handles six values.
  `byte_limit` accompanies `validator_no_reply` and keeps complete earlier
  records.
- DT-58: a zero-length host result carries no reporting-failure account. Do not
  read its absence of evidence as a statement about the worker.

### B.6 Implementation worklist

1. Edit FPC:1128-1133 (TB-1).
2. Edit FPC:108-114 (TB-3).
3. Regeneration: none. Run `tests/lib/python.sh docs/generate_limits.py --check`.
4. Verification: `tests/run.sh --suite source_drift`. The behavioral owners
   (`witness_contract/phases`, `runner_unit/pwrunner_core_unit_executable`) are
   unchanged and need a run only where the plan's evidence-reuse rules require
   one.

---

## Subject C — DT-55/56: exec retained output

### C.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-55.a | FPC promises bounded exec stream text "with truncation marker" and the guide suggests reporting native results through a helper's stdout/stderr; the representation has a further, unmarked cut at the first NUL byte. | `attempt.stdout`/`stderr` in the public reply; child output containing byte 0 | Yes. FPC:1101-1102; `docs/PolicyWitness.md:147` (frozen); cut at `runner/Sources/PWRunnerCore/ActorSession.swift:806-814`. | Review: executed, unavailable. Now: source, model check. | Contradicted explicit commitment |
| DT-55.b | `/usr/bin/printf "HEAD%02048d" 0`: direct stdout 2,052 bytes; `attempt.stdout` 1,023 bytes ending `\n... [truncated]`. | ASCII overflow | Model agrees. Not re-executed in the product. | As above. | Accurate observation needing no change |
| DT-55.c | `/usr/bin/printf "HEAD\000%02048d" 0`: direct 2,053 bytes; `attempt.stdout` is `HEAD`, four bytes, no marker. | NUL before an overflow | Model agrees. | As above. | Accurate observation needing no change |
| DT-55.d | `/usr/bin/printf "HEAD\000TAIL"`: direct nine bytes; `attempt.stdout` is `HEAD`, no marker. | NUL, no overflow | Model agrees. | As above. | Accurate observation needing no change |
| DT-55.e | Those runs returned `finished`, exit 0, attempt `rc` 0, child exit 0, leader exit and both EOFs, no termination request, successful reap; the NUL envelopes passed both Python readers. | Other evidence beside the text | Unverifiable by reading as an execution. Consistent: no reader inspects the text (`tests/lib/consumer.py:364-468`, `controller/src/porcelain_native.rs:203-217`). | Review: executed, unavailable. | Accurate observation needing no change |
| DT-55.f | Trace: `drain_one` copies bytes including NUL; the marker is placed by byte offset; `readString` stops at the first NUL, so a stored marker later in the buffer cannot reach JSON; mechanism present since `ae277d0c`. | C worker to Swift decoder | Yes. `controller/tools/pw_probe_runner/pw_worker_exec.h:170-180`, `:382-392`, `:394-402`; `ActorSession.swift:806-814`. | Re-read. | Accurate observation needing no change |
| DT-55.g | Assertions: `CWorkerTests` checks `/bin/echo` output, not NUL handling; `limits.json` `exec_stream` credits small-output tests and source inspection for overflow. | Coverage | Yes as quoted (`runner/Tests/PWRunnerCoreTests/CWorkerTests.swift:856-860`; `docs/limits.json` `exec_stream.behavior`). Incomplete: a registered live case, `runner_use_c_worker/exec_attempt_stdout_truncation_marker` (`tests/suites/runner_use_c_worker/run.sh:834-914`, present since 2026-05-31), exercises ASCII overflow with the marker. It covers neither NUL nor multi-byte text, so the finding stands. | Re-read. | Accurate observation needing no change |
| DT-55.q | Qualification: these commands on that build; no claim that an existing test asserts preservation of binary output. | Limit | Yes. | — | Accurate observation needing no change |
| DT-56.a | `/usr/bin/awk 'BEGIN {printf "xx";for(i=0;i<2000;i++)printf "é"}'`: direct 4,002 bytes of valid UTF-8; the run was `finished` with full process evidence and the `stdout` key absent; both Python readers returned `[]`. | Valid UTF-8, no NUL, overflow, cut inside a two-byte scalar | Model agrees. | Review: executed, unavailable. Now: source, model check. | Contradicted explicit commitment |
| DT-56.b | With prefix `x`: direct 4,001 bytes; 1,023 bytes, 520 characters retained, marker included. | Adjacent control, cut on a scalar boundary | Model agrees. | As above. | Accurate observation needing no change |
| DT-56.c | Source explanation: the 16-byte marker is placed at byte 1,007 of the 1,024-byte buffer; `readString` uses strict UTF-8 decoding with `?? ""`; the caller turns the empty string into nil; no valid prefix is kept and no decode loss is reported. | C worker and Swift decoder | Yes. `pw_worker_exec.h:382-392`; `ActorSession.swift:813`, `:704-705`. | Re-read. | Accurate observation needing no change |
| DT-56.d | The small-ASCII assertion and the source-only overflow credit do not establish this boundary. | Coverage | Yes; the live truncation case uses an `A` fill (`run.sh:901`). | Re-read. | Accurate observation needing no change |
| DT-56.q | Qualification: process, EOF and reap evidence were not lost; what is lost is the text channel including its truncation indication. | Limit | Yes by reading. | — | Accurate observation needing no change |

### C.2 Comparison

**Obligation as stated.**

- Field meaning, public owner `docs/contract/31-steps.surface.md:238-244`:
  "Captured child stdout, omitted when empty. The worker retains at most
  1,023 bytes for this stream; an overflow marker occupies part of that
  allowance." The same words for stderr. Rendered as `string?`
  (`docs/RESPONSE.md:1014-1015`).
- Limit, owner `docs/limits.json` `exec_stream`: `counting` "Retained stdout or
  stderr bytes for each exec child. An overflow marker occupies part of this
  allowance."; `effect` "Excess output is not retained."; `behavior` "Each text
  buffer reserves its terminating NUL outside this payload limit. Additional
  output is drained even after retention stops. Small stdout/stderr capture is
  tested. Overflow truncation and the exact retained-prefix/marker split are
  source-inspected." The row is copied into the frozen guide; `behavior`
  appears only in `docs/LIMITS.md` "Grounding and coverage".
- Shared limits text, `docs/LIMITS.md:73` (copied region): "Excess can retain a
  prefix with a truncation marker or make capture unavailable, as the row
  describes."
- FPC:1101-1102 (authored): "exec stream text (1,023 bytes each, with
  truncation marker) keep their existing refusal/truncation semantics."
- Per-stream observation, owner `docs/contract/32-lifecycle.surface.md:1407-1426`:
  `eof`, `read_errno`, `poll_revents` only.

**Producer, step by step.**

1. C worker, collection. `drain_one` reads up to 256 bytes at a time and copies
   until 1,023 bytes are stored; later reads are discarded and set an overflow
   flag that is a local variable of `attempt_exec_spawn`
   (`pw_worker_exec.h:170-180`, `:297-298`, `:347-353`). NUL bytes are copied like any other.
2. C worker, marker. On overflow the 16 bytes `\n... [truncated]` overwrite
   buffer bytes 1,007-1,022 and byte 1,023 is NUL
   (`pw_worker_exec.h:382-392`; stderr `:394-402`). The overflow flag itself is
   not published. The slot carries no stream length or count: the exec evidence
   words are `exec_stdout_eof`, `exec_stderr_eof`, read errno and poll events
   (`pw_probe_runner_abi.h:495-507`).
3. Shared memory. `child_stdout` and `child_stderr` are 1,024-byte fields at
   slot offsets 3,932 and 4,956 (`pw_probe_runner_abi.h:471-472`;
   `runner/Sources/PWRunnerCore/CWorker.swift:181-182`).
4. Swift decoder. `readString` scans to the first zero byte or 1,024, then
   `String(data:encoding:.utf8) ?? ""` (`ActorSession.swift:806-814`); the
   caller maps an empty string to nil (`:704-705`).
   **A NUL byte ends the retained text here.** **Bytes that are not valid
   UTF-8 as a whole erase the field here**, including a scalar cut by the
   marker at byte 1,007.
5. Reply. `PWRunnerAttemptResult.stdout`/`stderr` are `String?` with
   `json_null: false` (`docs/porcelain.json`); the step builder copies them
   (`runner/Sources/PWRunnerCore/CWorkerStepResults.swift:262-263`).
6. Wire and Rust. Text is length-prefixed and strictly decoded
   (`tests/lib/porcelain.py:56-60`; `controller/src/porcelain.rs:262`). The
   Rust record is `Option<String>` and serializes the key only when present
   (`controller/src/porcelain_records.rs:1409`, `:1506-1507`). The controller
   does not inspect the text.

**Which loss indications survive.**

| Input | `stdout` in the reply | Indications that survive | Indications lost |
| --- | --- | --- | --- |
| ASCII or valid UTF-8, at most 1,023 bytes, no NUL | exact text | `collection.stdout.eof`, stop reason, child status | none |
| ASCII overflow | first 1,007 bytes and the marker | marker text; the same process evidence | number of bytes dropped |
| NUL, no overflow | bytes before the first NUL; absent when the first byte is NUL | process evidence only | that bytes followed the NUL |
| NUL before an overflow | bytes before the first NUL | process evidence only | the marker; that bytes followed |
| Valid UTF-8 overflow whose byte 1,006 starts a multi-byte scalar | absent | process evidence only | every retained byte; the marker |
| Output that is not valid UTF-8, any length | absent | process evidence only | every retained byte |

An absent key is what the statement defines as empty output. In three rows it
accompanies nonempty output.

**Readers and tests.** No reader relates the text to anything. Swift reporting
admission (`runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift:109-124`),
Rust (`controller/src/porcelain_native.rs:203-217`) and the consumer
(`tests/lib/consumer.py:387-393`) validate the three stream words. Existing
assertions on the text:

- `runner_use_c_worker/exec_attempt_stdout_truncation_marker`: 4,096 `A`
  bytes; length below 1,024, marker present, body all `A`
  (`run.sh:889-902`). It does not assert the split point.
- `runner_use_c_worker/exec_attempt_args_and_stderr_round_trip`: exact small
  stdout and stderr for exits 37 and 0 (`run.sh:818-819`).
- `witness_contract/max_targets_reply_survives`: exactly 1,023 bytes of `A` and
  of U+0001 on every step, no overflow
  (`tests/suites/witness_contract/check_max_target_reply.py:178-180`, `:439`,
  `:458-466`).
- Small exact text in `runner_exec_dac`
  (`tests/suites/runner_exec_dac/check_query_scope.py:156`, `:198`, `:202`,
  `:213`), `runner_specimen_isolation`
  (`tests/suites/runner_specimen_isolation/check.py:93-94`),
  `runner_exec_lifecycle` (`tests/suites/runner_exec_lifecycle/check_edges.py:122`)
  and `run_effects/exec_helper_effect_is_real`
  (`tests/suites/run_effects/check_exec_effect.py:91`).
- `runner_c_worker_harness` exec cases assert child status and errors; the
  harness prints the stream fields as C strings
  (`tests/suites/runner_c_worker_harness/harness.c:1167-1168`), so it also
  stops at a NUL.
- `runner_unit`: `/bin/echo` text (`CWorkerTests.swift:856-860`); an
  unpublished slot's text stays hidden
  (`runner/Tests/PWRunnerCoreTests/ExecObservationTests.swift:442-458`).

### C.3 Plausible treatments

Two existing patterns in this product are relevant. The worker diagnostic
carries a worker-published byte length and a complete/truncated state, and the
host decodes exactly that many bytes with replacement
(`runner/Sources/PWRunnerCore/CWorker.swift:621-628`;
`docs/contract/32-lifecycle.surface.md:577-610`). The client error message is
cut on a scalar boundary with a separate `message_truncated` flag
(`runner/Sources/PWRunnerCore/PWRunnerTransport.swift:87-92`). Byte fields with
counts and a truncation flag exist for the validator decode fault
(`context_b64`, `frame_bytes`, `retained_bytes`, `context_truncated`).

Any change to `pw_worker_exec.h`, `pw_probe_runner_abi.h` or
`runner/Sources/**` requires worker-identity regeneration and a signed rebuild,
whatever its size.

| | (i) Text field kept; explicit counts and loss indications; scalar-safe truncation | (ii-a) Lossless bytes beside the string | (ii-b) Lossless bytes in place of the string | (iii) Retain; state the limit |
| --- | --- | --- | --- | --- |
| What a reply carries | `stdout`/`stderr` text of every retained byte (NUL as U+0000; invalid sequences as U+FFFD); per stream: bytes read, bytes retained, truncated, and whether the text is the exact decoding | (i)'s counts plus `stdout_b64`/`stderr_b64` | counts plus base64 only | unchanged |
| C/Swift layout | New per-stream words in the slot's tail reserve (640 bytes of `reserved` after `ext_target` by arithmetic from the declared sizes, `pw_probe_runner_abi.h:524-544`); no existing offset moves; `PW_SHM_EXEC_EVIDENCE_BYTES` stays 112. New `PWShmLayout` constants and `runner_abi_layout` printer lines; `tests/fixtures/contract/abi_layout.txt` reviewed | same as (i) | same as (i) | none |
| Worker identity and build | regenerate; signed rebuild | same | same | none |
| Wire schema | fields added to `PWExecStreamObservation` in `docs/porcelain.json`; generated Swift, Rust and Python tables; frame fingerprint changes | (i) plus two byte fields on `PWRunnerAttemptResult` | (i) plus two byte fields, two text fields removed | none |
| Surfaces and limits | `31-steps.surface.md:238-244` restated; fields added at `32-lifecycle.surface.md:1407-1426`; `limits.json` `exec_stream.behavior` and `checks`; the row's `counting` and `effect` stay true if the marker and the 1,023-byte allowance are kept | (i) plus two field statements | (i) plus removal of two field statements; `counting` changes | `31-steps.surface.md:238-244`, `limits.json` `exec_stream` (`counting`, `behavior`), FPC:1101-1102 |
| Shape goldens and fixtures | `tests/fixtures/contract/response_shape.json`, `tests/fixtures/contract/surfaces/lifecycle.json` and `steps.json` (`--refresh-shapes`), `tests/fixtures/contract/exec_observation.json` (51 attempts, two streams each) | (i) plus attempt shape | (i) plus attempt shape; every fixture carrying `stdout`/`stderr` | surface stamps only |
| Readers | the three stream validators gain count relations; the consumer also relates text length to retained bytes | (i) plus a text/bytes agreement rule in each reader | (i); every text assertion rewritten to decode base64 | none |
| Reply-size accounting | replacement can triple the wire bytes of a stream's text (1,023 invalid bytes become 3,069); `ReplyMaximumTests.swift:63-64` `stringPolicy`, `porcelain_replies.py` accounting and `witness_contract/max_targets_reply_survives` recomputed. JSON worst case stays the control-character case | (i) plus 1,364 base64 characters per stream per step | JSON worst case per stream falls from 6,138 to 1,364 characters | none |
| What a consumer of the string sees | identical for valid UTF-8 within the limit and for ASCII overflow. Present, ending on a scalar boundary before the marker, where it was absent (DT-56). Contains U+0000 and what followed where it stopped (DT-55). Present with U+FFFD where it was absent | as (i) | the key is gone; every consumer changes | unchanged, including silent loss |
| Bytes that are not UTF-8 | not recoverable; flagged | recoverable | recoverable | lost, unflagged |
| Frozen guide copy | the limit row and guide line 147 remain true | remain true | the row's wording diverges | the row is known incomplete |

A fifth variant was considered and set aside: a host-only change that scans for
the last nonzero byte instead of the first NUL. It still needs the signed
rebuild, cannot tell trailing NUL output from unused buffer, and leaves
truncation readable only from marker text.

### C.4 Recommended disposition per claim

**Recommendation: alternative (i).** The reasons: the channel's stated purpose
is a helper's textual report; (i) makes both review inputs lossless (a NUL is a
valid scalar, and a boundary-safe cut introduces no invalid sequence); it puts
the truncation indication outside the text, where child output cannot hide or
imitate it; it reuses two patterns the product already has; it leaves every
existing text assertion and the frozen guide's limit row true; and it adds one
record's worth of fields instead of a second copy of every stream. Its accepted
limit is stated below. (ii-a) is the fallback if exact recovery of non-UTF-8
bytes is judged necessary; its extra cost is the second copy, an agreement rule
in three readers and a larger reply maximum.

Shape of (i), with spellings left to the implementer:

1. Worker. Publish per stream the count of bytes read before collection stopped
   and the count stored (0-1,023). A child can write more than 4 GiB within the
   10,000 ms child deadline; use a 64-bit count or saturate at a stated value.
   The buffer holds child bytes only. Either the worker keeps writing the
   marker and the host accounts for it, or the worker stops writing it and the
   host appends it; the checks below pin the public result, not the placement.
2. Host decode. Read by count, not to the first NUL. Reject a stored count
   above 1,023 as a malformed exec payload through the existing
   `execObservationDecodeProblem` route (`CWorker.swift:1361-1365`). On
   overflow keep at most 1,007 child bytes, drop an incomplete trailing scalar
   (at most three bytes), decode with replacement and end with the marker, so
   the text stays within 1,023 bytes when exact. Publish `stdout`/`stderr` when
   at least one byte is retained.
3. Reply. In `exec_observation.collection.stdout` and `.stderr`: bytes
   received, bytes retained (child bytes represented in the text, marker
   excluded), truncated (received exceeds retained), and an indication that the
   text is not the exact decoding of the retained bytes. All required.
4. Statement for `31-steps.surface.md:238-244`: the text of the retained child
   bytes, omitted when none was retained; a NUL byte appears as U+0000; a byte
   sequence that is not valid UTF-8 appears as U+FFFD and the stream
   observation says the text is inexact; on overflow the text ends on a scalar
   boundary followed by the marker, and the stream observation's counts are the
   truncation indication because a child can write the marker's characters.

| Id | Disposition | Reason and check |
| --- | --- | --- |
| DT-55.a | Product behavior change (i), with the surface, limits coverage note and FPC:1101-1102 landed together. | The marker promise and "omitted when empty" are false at the public field for these inputs. Checks: the contrasts below. |
| DT-55.b | Retain as the unchanged control. | `runner_use_c_worker/exec_attempt_stdout_truncation_marker` must pass unmodified; add its counts (received 4,096, retained 1,007, truncated). |
| DT-55.c, DT-55.d | Become the two embedded-NUL contrasts. | See below. |
| DT-55.e | Retain; the new contrasts keep asserting the same process evidence. | The change must not alter `finished`, child status, EOF flags or reap. |
| DT-55.f | Retain as the mechanism the change replaces. | — |
| DT-55.g | Correct `limits.json` `exec_stream.behavior` and `checks` to name the live cases and what each asserts. | The note already under-credits the ASCII case. |
| DT-55.q | Retain. | — |
| DT-56.a | Product behavior change (i); becomes the split-UTF-8 contrast. | See below. |
| DT-56.b | Retain as the adjacent control; its text is unchanged by (i). | — |
| DT-56.c, DT-56.d, DT-56.q | Retain. | — |

**What the contrasts must each demonstrate.** Each runs the review's argument
array through `exec/spawn` and also directly (`subprocess.run` on the same
absolute executable), and compares the reply with the direct bytes. Content
and indications are asserted separately, each against the direct output, never
against each other alone.

| Contrast | Retained content | Loss indication | Incorrect behavior rejected |
| --- | --- | --- | --- |
| Embedded NUL, no overflow: `printf "HEAD\000TAIL"` (9 bytes) | `stdout == "HEAD\u0000TAIL"`, equal to the direct bytes decoded | received 9, retained 9, not truncated, exact | text cut at the NUL; a count of 9 beside four bytes of text |
| Embedded NUL before overflow: `printf "HEAD\000%02048d" 0` (2,053 bytes) | text begins `HEAD\u0000`, equals the first 1,007 direct bytes plus the marker | received 2,053, retained 1,007, truncated, exact | truncated false or marker missing because a NUL preceded it |
| Split UTF-8: awk `xx` + 2,000 `é` (4,002 bytes) | present; equals the first 1,006 direct bytes (`xx` and 502 `é`) plus the marker; no U+FFFD | received 4,002, retained 1,006, truncated, exact | absent field; U+FFFD at the cut; inexact reported for valid child output |
| Aligned control: awk `x` + 2,000 `é` (4,001 bytes) | 1,023 bytes, 520 characters, as today | received 4,001, retained 1,007, truncated, exact | a change to currently correct output |
| Inexact text without truncation: 17 bytes of 0xFF (`tests/fixtures/exec/streams.c`, arguments `17 0 255`) | 17 U+FFFD | received 17, retained 17, not truncated, inexact | exact reported for replaced bytes; inexactness tied to truncation |
| Exact limit: 1,023 `A` (existing `max_targets_reply_survives` input) | unchanged, no marker | received 1,023, retained 1,023, not truncated | marker or truncated at exactly the limit |

The fifth row is not a review input. It is needed so that the exactness
indication is exercised independently of truncation.

Constructed reader controls, separate from the live contrasts: in
`tests/fixtures/contract/exec_observation.json` add accepted records for each
combination above and rejected records for retained above received, truncated
disagreeing with the counts, retained above 1,023, text present with retained
zero, text absent with retained nonzero, and exact text whose UTF-8 length
differs from retained (plus 16 when truncated). The Swift and Rust validators
take the count relations; the consumer takes the text relation as well.

**Accepted limit under (i)**, to stand beside the field statement in
`docs/contract/31-steps.surface.md`: "Retained bytes that are not valid UTF-8
are shown as U+FFFD and reported as inexact; the reply does not carry the
original bytes."

**If the product change is not taken**, alternative (iii) is the only treatment
that leaves the statements true. Its sentence, for
`docs/contract/31-steps.surface.md:238-244` and `limits.json`
`exec_stream.counting`: "The reply's text ends before the first NUL byte and is
omitted when the retained bytes are not valid UTF-8, which includes an overflow
cut inside a multi-byte character; in those cases the overflow marker is not
shown, and an omitted field does not establish that the child wrote nothing."
This pass does not recommend it: it leaves an absent field with two meanings
and no observation to tell them apart.

### C.5 Resulting user duties

Under (i):

- Read truncation from the stream observation's counts, not from the marker
  text.
- A helper that must report bytes outside UTF-8 encodes them as text itself
  (hex, for example); the reply will not return them.
- A consumer comparing `stdout` for equality with a pre-NUL prefix, or treating
  a missing key as "wrote nothing", must be updated: the key is missing only
  when no byte was retained.

Until the change is in a build, and under (iii): do not conclude from an absent
or short `stdout`/`stderr` that the helper wrote nothing or wrote only that;
keep helper reports short, ASCII and free of NUL.

### C.6 Implementation worklist

Ordered; items 1-7 are build-contract or worker-identity inputs and land in one
rebuilt candidate.

1. `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`: per-stream count
   words in the slot tail reserve with a `_Static_assert` on their offsets;
   update the comments at `:104-107` and `:460-472`.
2. `controller/tools/pw_probe_runner/pw_worker_exec.h`: accumulate bytes read
   in the drain loop (`:347-353`); publish the counts before `exec_valid`
   (`:474`); marker handling per the chosen placement (`:379-402`).
3. `runner/Sources/PWRunnerCore/CWorker.swift`: `PWShmLayout` constants beside
   `:204-231`; `decodeExecObservation` (`:1361-1408`) reads and bounds the
   counts.
4. `runner/Sources/PWRunnerCore/ActorSession.swift:675-678`, `:704-705`: a
   count-based stream decode with scalar-safe truncation; leave `readString`
   for the other slot strings.
5. `docs/porcelain.json`: fields on `PWExecStreamObservation`; run
   `tests/lib/python.sh docs/generate_porcelain.py` (Swift regions and
   writers, `controller/src/porcelain_records.rs`, `tests/lib/porcelain_schema.py`).
6. Readers: `runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift:118-124`,
   `controller/src/porcelain_native.rs:203-217`,
   `tests/lib/consumer.py:387-393`. Keep them separately written.
7. `tests/lib/python.sh docs/generate_worker_identity.py`.
8. `tests/suites/runner_abi_layout/printer.c`: a line per new offset; review
   `tests/fixtures/contract/abi_layout.txt`.
9. `tests/suites/runner_c_worker_harness/harness.c:1164-1169`: print the counts
   and the stream bytes by count (hex) so worker-level cases can assert them.
10. Account owners: `docs/contract/31-steps.surface.md:238-244`;
    `docs/contract/32-lifecycle.surface.md:1407-1426`; `docs/limits.json`
    `exec_stream` (`behavior`, `checks`); FPC:1101-1102. Then
    `tests/lib/python.sh docs/generate_limits.py` and
    `tests/lib/python.sh docs/generate_contract_stamps.py --refresh-shapes`,
    then every generator's `--check`. The guide stays byte-frozen.
11. Fixtures and accounting: `tests/fixtures/contract/exec_observation.json`;
    `tests/fixtures/contract/response_shape.json`;
    `runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift:63-64` and the
    accounting in `tests/suites/runner_unit/porcelain_replies.py`;
    `tests/suites/witness_contract/check_max_target_reply.py` margins.
12. New cases in `tests/catalog.json` under `runner_use_c_worker`, beside
    `exec_attempt_stdout_truncation_marker`, for the contrasts in C.4; update
    `tests/suites/runner_use_c_worker/README.md` and `tests/COVERAGE.md`.
    Constructed decoder controls in `ExecObservationTests.swift` using new
    `exec_payload_*` modes of `tests/fixtures/worker_lifecycle/worker.c:247-270`.
13. Verification on the rebuilt signed app. Exercise the revised cases against
    the existing app first where the plan requires it (the new contrasts fail
    there by construction; record that as the pre-change observation). Routes
    in `tests/CHANGE-VERIFICATION.md`:
    - "Porcelain schema or binary representation": `source_drift/porcelain_codec`,
      `source_drift/generator_contract`, `preflight/build_entry_controls`.
    - "Exec publication, compatible absence handling":
      `runner_unit/exec_reader_mutations`.
    - "Exec family engine boundary":
      `runner_c_worker_harness/exec_control_states`.
    - "Limits": the coverage note and check list change, so
      `source_drift/limits_documentation`. If the row's value or counting
      changes, the full limit route applies: `tests/run.sh --suite unit --suite
      integration --suite source_drift --suite runner_abi_layout --suite
      runner_unit --suite runner_c_worker_harness --suite failure_boundaries`.
    - Layout: `runner_abi_layout/c_swift_layout_agreement`.
    - "response representation/retention": `witness_contract/response_footprint`
      and `witness_contract/max_targets_reply_survives`.
    - Behavior owners: `runner_use_c_worker`, `runner_exec_dac`,
      `runner_exec_lifecycle`, `runner_specimen_isolation`,
      `run_effects/exec_helper_effect_is_real`, `blackbox_e2e`, `exec_fixture`.
    - A worker change is compared by the live default battery on the candidate.
    The order-barrier mutation control is not triggered: the wait, release
    store and eligibility rule are untouched.

---

## Outside the review

Noticed while re-verifying; not findings of the review and not added to it.

1. FPC:678 says `runner_c_worker_harness/compile_failure` shows "A=false,
   D=true, R=-1". By reading, the worker does not write R on a compile failure
   and the case does not assert it
   (`tests/suites/runner_c_worker_harness/run.sh:454-481`). The same correction
   as DT-45 applies to this row; leaving it would keep a false statement beside
   the corrected ones.
2. Two source comments still describe the status-word writes:
   `controller/tools/pw_probe_runner/pw_probe_runner_abi.h:207-219` and
   `controller/tools/pw_probe_runner/pw_probe_runner.c:21-22`. Both files are
   build-contract and worker-identity inputs. Correct them in the rebuild that
   Subject C already requires.
3. `runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift:58-60` and
   `:192-193` have the DT-47 shape (encode, discard, assert on the typed
   record), and FPC:684 says "The actual subprocess assembler and binary writer
   preserve reports and missing status". The T47-1 rewording should cover this
   row.
4. `docs/limits.json` `exec_stream.behavior` says overflow truncation is
   source-inspected while `runner_use_c_worker/exec_attempt_stdout_truncation_marker`
   exercises ASCII overflow through the CLI.
5. The marker is written into the same bytes as child output. A child that
   prints `\n... [truncated]` as its last 16 bytes produces text identical to a
   truncated stream. Alternative (i)'s counts remove the ambiguity.
6. `readString` serves `step_id`, `observed_path` and `error` as well
   (`ActorSession.swift:656-663`). A worker-reported path that is not valid
   UTF-8 would become absent by the same rule. Reachability was not examined.
7. `docs/contract/30-reply.surface.md:286` describes the empty-bytes path as
   read in source although `ReplyFailureTests.swift:314-330` asserts it. The
   note credits less than the check establishes; no change is needed for any
   claim above.
8. The review's reproduction route for DT-49 and DT-54
   (`_test_overrides.validator_executable_path` on an ordinary `run`) is one of
   the controls the management plan moves to `test-input run`. Controls
   recommended here follow that route once it exists.

## Count

48 claims assessed: 11 identity and limit claims, 17 in Subject A, 7 in
Subject B, 13 in Subject C.
