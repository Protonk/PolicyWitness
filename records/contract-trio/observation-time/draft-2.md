### Observation-time investigation: scope, snapshot and evidence

This pass asks whose observation each returned field records and what time it
describes. It starts from DT-46, DT-62, DT-63, DT-66 and DT-68. Those entries
keep their own scope. What follows extends them, qualifies one history note in
DT-46, and records new observations under provisional labels (OT-1 to OT-8).
These labels will be replaced by record identifiers in the final text. No layer
is chosen to change and no repair is proposed.

**Snapshot and build.**
- Source inspection used clean `main` at `cc55288d033023ce2f18e8c02cd51a400ef2b530`
  on 2026-11-16, with macOS 26.7.1 (25G241) on arm64. Line numbers below refer
  to that snapshot.
- The existing `dist/PolicyWitness.app` reports commit `8b5de2b2`, version
  0.3.7, build 1482, and contract
  `development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
- `git diff --stat 8b5de2b2 HEAD -- controller runner tests docs` shows only the
  one-line change to `tests/suites/preflight/opt_in/build_refusals.py`.
- The executable hashes match the failure-contract investigation's table:
  - `policy-witness` `4bcd308b…`
  - `PWRunner` `706d9a6c…`
  - `pw-probe-runner` `d6d38f09…`
  - `sb_api_validator` `ccbf9803…`
  - `pw-probe-runner-unentitled` is `ee2a4248…`.
- The app was neither rebuilt nor modified.

**Kinds of evidence.** Four kinds appear below, and each claim names its kind.

1. *Public CLI execution.* E1–E5, and two path-length checks (C7a/C7b) made
   during revision, ran
   `dist/PolicyWitness.app/Contents/MacOS/policy-witness run SPECIMEN` under
   `tests/lib/checkout_lock.sh`, capturing stdout, stderr and exit status
   separately.
   - The runs were made outside the automation sandbox from the start, because
     earlier passes recorded XPC lookup error 159 inside it. No in-sandbox
     attempt was made in this pass.
   - Every capture has empty stderr.
2. *Internal driver observation (E6).* This is not a public response. Its build
   and execution:
   - `runner/Sources` and `runner/Package.swift` were copied unchanged; `diff -r`
     reported no difference before and after the build.
   - The only addition is my own `Tests/PWRunnerCoreTests/main.swift` (SHA-256
     `7d88c93f…`).
   - Build command: `swift build --jobs 2 --package-path … --scratch-path …
     --product PWRunnerCoreTests`, run outside the sandbox with Apple Swift
     6.4.2 and the macOS 27.2 SDK. The executable SHA-256 is `2750ec0e…`.
   - It ran under the checkout lock against the signed app's
     `pw-probe-runner-unentitled` and `pw-probe-runner`. Those executables were
     used in place and read only.
   - It decodes the request with the app contract, normalizes and translates it
     with the production `ActorTranslation`, and runs `ActorScheduler`.
   - Its `ActorScheduleInput` (driver `main.swift` line 40) sets no `didSetUp`
     hook, so equipment binding and live code inspection do not run. Validator
     collection, reply validation and encoding are also absent.
   - It reads host custody state from the collection hook (line 88) and again
     after `run()` returns.
   - It counts nonzero bytes only (lines 43–49); no token byte was printed or
     written. It reaches the private custody buffer pointer through `Mirror`
     (lines 51–56) without changing any access control.
3. *Source and test inspection.* This covers the cited lines.
4. *History inspection.* This uses `git log -S/-G` and `git show`.

No registered test case was executed, and no suite pass is claimed.

**Artifacts and availability.**
- Specimens, the specimen generator, the CLI runner, the summarizer, captures
  and driver outputs are under `.tmp/contract-trio/observation-time/` in the
  local checkout. That directory is gitignored, disposable and has no retention
  guarantee.
- The target file is `/private/tmp/pw-trio-ot-xVGRMW/target`; the C7a/C7b
  targets sit in sibling `pw-trio-ot-len45-*` and `pw-trio-ot-len55-*`
  directories. On this machine `/private/tmp` does not survive a reboot.
- Each target holds the 27 bytes `authority lifetime witness\n` (SHA-256
  `7482bce4…`). The main target (device 16777233, inode 278532339) was unchanged
  after E3.

**Rebuilt specimens.**
- E1 rebuilds DT-62's issue-only specimen and E3 rebuilds DT-66's two-actor
  specimen from the record's descriptions; the original scratch is gone.
- The target content and length match DT-59. The target path and inode differ
  from DT-59/DT-66 (`/private/tmp/pw-authority-trace-3QC3qQ/target`, inode
  277408216).
- The original files' mode and the original step and phase identifiers are
  unknown. The rebuilt identifiers are in the specimen files.
- Actor A is unapplied with `equipment: "unentitled"`. B in E3 is applied with
  the default selected equipment and DT-66's exact policy.
- Token lengths depend on the target path. DT-62's driver printed an accepted
  length of 216, while E1a, E2 and E6 show 208. A targeted check (C7a/C7b:
  E1a's specimen with target paths of 45 and 55 bytes) gave issue `token_length`
  216 and 226. With E1a's 37-byte path giving 208, the published length equals
  171 plus the path's byte length in all three runs. DT-62's path
  (`/private/tmp/pw-authority-trace-3QC3qQ/target`) is 45 bytes. This is a length
  correlation only; no token content was inspected.

**Terms used here.**
- *Native operation*: the private-library or system call itself.
- *Publication*: a worker or host release store that makes a value eligible to
  read (slot `completed`, call-boundary marker, setup cell, outbound
  `committed`, host acknowledgement).
- *Host observation*: a value the host records from its own call or read
  (waitpid, kill, custody acceptance, transfer answer).
- *Assembly decision*: a value computed while building the reply.
- A *copy* repeats one stored value. A *derivation* maps it. An *independent
  observation* comes from a different call or read.

### Anchor DT-46: what establishes `cleanup_trigger` and when it is fixed

**Producers and copies.** A single stored string, `ActorSession.pollStopReason`,
produces all of these values:

| Reply value | How it is obtained | Fixed at |
| --- | --- | --- |
| `poll_stop_reason` | copy (`ActorSession.swift` 742) | last assignment to `pollStopReason` |
| `sentinel_wait.stop` (single-worker only) | copy taken when the polling loop ends ([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) 1271) | loop exit, before `requestExit` at 1276 |
| `cleanup_trigger` | `triggerForStop[pollStopReason] ?? pollStopReason` (`ActorSession.swift` 626) | `collectOutput`, after grace, termination and reap |
| claim `stop_reason.answer` | copy of `poll_stop_reason` ([CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift) 117–121) | resolution |
| claim `cleanup_trigger.answer` | copy of `cleanup_trigger` (127) | resolution |
| `normalized_outcome: runner_timeout` | selected when the stop-reason claim is `sentinel_deadline` (361–366) | classification |
| diagnostics `stop_reason`, `termination_cause` | Rust `project` ([porcelain_admission.rs](../controller/src/porcelain_admission.rs) 1342–1419) | controller projection |

The writers of `pollStopReason` are:
- the initializer default `"sentinel_deadline"` (`ActorSession.swift` 70, then 411);
- the single-worker polling loop (`CWorker.swift` 1191, 1192, 1204, 1205, 1221, 1232, 1235);
- `ActorScheduler.stopActor` ([ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift) 549);
- `finish()` (562).

Every one of them runs before the matching `requestExit`
([ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift)
558–562). Nothing writes the field between that store and `collectOutput`, so
the value mapped at collection is the value held at the store. That equality
follows from how the code is structured; nothing captures the value at the
store.

**Exits that keep the default.**
- The single-worker loop (`CWorker.swift` 1162–1270) has four exits that leave
  `pollStopReason` untouched: 1247, 1253, 1259 and 1269. Each goes through
  `expiredAfterResampling`, `expiredAfterWaiting(exit:)` or
  `expiredAfterSleeping()`, and each returns true only when the allowance is
  exhausted (`fallbackRemainingNs == 0`, lines 955–1027).
- The breaks at 1193, 1206, 1238 and 1267 only leave a `switch`.
- The protocol-violation branch (1188) continues the loop.
- With an unusable clock, `elapsedNs()` returning nil changes only the cadence of
  the periodic waitpid (1227). The loop still ends through an expiry exit, once
  nominal charged sleeps exhaust the allowance.
- So the string `deadline_expiry` always means the allowance was exhausted. It is
  never actively recorded: it is the default that no other exit replaced. Under
  a clock fault that exhaustion was counted in nominal sleeps, not measured; only
  `sentinel_wait.clock_fault` and the absent `elapsed_ms` show this. That is the
  single-worker counterpart of DT-10.
- The actor form never keeps the default. `stopActor` or `finish()` assigns every
  spawned session.

**History: two separate properties.**

(i) *Recording time.* The derivation was introduced in `0ed4ae7a` (2026-09-27).
At that point it sat immediately after the store. `git show
0ed4ae7a:runner/Sources/PWRunnerCore/CWorker.swift`, lines 933–938:

```swift
    // ---- Request worker exit (a no-op if it already died on its own).
    storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)
    // The cleanup trigger is recorded here, at the store, as the reason polling
    // stopped; it is a host fact for the disposition record, not reconstructed
    // from a final exit code.
    let cleanupTrigger = PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason
```

`c686a05f` (2026-11-03), which introduced `ActorSession` and the actor form,
deleted those lines and moved the same expression into `collectOutput`. So the
value was fixed at the store from `0ed4ae7a` until `c686a05f`, and at final
collection since then. Because no later write intervenes, the move changed when
the value is fixed, not the value.

(ii) *Independence from the stop reason.* The trigger has never been independent
of the stop reason. Both placements derive it through `triggerForStop` from
`pollStopReason`.

What the documents claimed:
- The failure contract's wording dates from `0b6e191e`, about an hour before
  `0ed4ae7a` on the same day. In
  [the contract](../tests/FAILURE-PROPAGATION-CONTRACT.md), lines 359–367, it
  claims three things: the trigger is "recorded at the exit-request store"; the
  raw facts are "not conclusions reconstructed from a final status"; and "today
  it corresponds one-to-one with `poll_stop_reason`, and both are retained".
- The first claim matched the code only between `0ed4ae7a` and `c686a05f`. The
  second has always held. The third openly states that the trigger depends on
  the stop reason.
- RESPONSE's "Host fact recorded when it requests exit"
  ([32-lifecycle.surface.md](../docs/contract/32-lifecycle.surface.md) line 92;
  `docs/RESPONSE.md` 1633) was authored in `f6551bf9` (2026-11-10), after the
  move.
- Two code comments carry the same recording-point wording and were not changed
  by the move:
  - the doc comment on `CWorkerOutput.cleanupTrigger`
    ([CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) 559–562,
    "Direct host observations … why exit was requested (recorded at the
    exit-request store)"), from `0ed4ae7a`;
  - the comment on Python `TRIGGER_FOR_STOP`
    ([lifecycle_contract.py](../tests/lib/lifecycle_contract.py) 105–106, "the
    host records the trigger at the exit-request store"), from `0b6e191e`.
- The actor cause surface's fallback paragraph
  ([41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
  1014–1017; RESPONSE 3167) names "the request result, exhausted grace and owned
  final status" as the independent observations in the chain. It does not include
  the trigger.

This adds to DT-46 and leaves its scope intact. DT-46's "already in `0ed4ae7a`"
is accurate for the expression. The placement at collection begins with
`c686a05f`.

**No reader treats the copies as corroboration.**
- I found no statement or reader that treats any pair of these copies as
  corroborating each other.
- Rust (`porcelain_admission.rs` 463–475) and the Python oracle
  ([lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) 139–145) each check a
  claim only against its own raw field.
- Python `TRIGGER_FOR_STOP` ([lifecycle_contract.py](../tests/lib/lifecycle_contract.py)
  107) is used for a vocabulary self-check (752) and an export (801). The Swift
  test at
  [DispositionResolverTests.swift](../runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift)
  527 compares that export with `PWDisposition.triggerForStop`. That detects
  disagreement between the Swift and Python tables. It checks no reply value.
- The Swift resolver fixture at line 44 builds its expected trigger with the
  production map, so that fixture alone cannot detect a mapping change.
- The cited Rust cause test (lines 2660–2730) builds matched pairs by hand.

**What enters the cause label.** In `project`, `termination_cause` requires four
things:
- a supported `final_status` of `signal`, which comes from waitpid status
  recorded at reap;
- supported `grace_end: exhausted`, recorded when the grace loop ends;
- `kill_request_and_result: requested`, recorded at the kill call, with `rc == 0`
  and a signal equal to the final status;
- a supported trigger, which only selects the label.

`owned_reap` and its `departure_requested` are not inputs. In the ordinary form,
where the map is deterministic, the derivation therefore changes only how the
value's provenance is described. No cause selection changes.

**Executed, public CLI, E4 (shortened-timeout control).**
- Specimen: the ordinary baseline from the failure-contract investigation plus
  `_test_overrides.worker_timeout_ms: 50` and `worker_post_apply_hang_ms: 3000`.
- `worker_timeout_ms` is a supported override. The host floors it at 50 ms
  (`timeoutMsForCWorker`, `CWorkerRequestPlanning.swift` 62–66) and passes it as
  the same `HostWaitClock` budget, so the production loop runs with a smaller
  allowance. This control does not test the 120,000 ms production duration.
- Result: exit 1, `runner_timeout`.

| Field | Value |
| --- | --- |
| `sentinel_wait` | `budget_ms` 50, `elapsed_ms` 53, `excluded_ms` 2, `clock_fault` false, `stop` `sentinel_deadline` |
| `poll_stop_reason` and the stop claim | `sentinel_deadline` |
| `cleanup_trigger` and its claim | `deadline_expiry` |
| `exit_grace_wait` | 1001 ms, `exhausted` |
| `termination_request` | `{signal:9, rc:0}` |
| status | reaped with signal 9 |
| diagnostics | `termination_cause: host_sentinel_deadline`, `stop_reason: sentinel_deadline` |

Only the initializer assigns the string `sentinel_deadline`
(`ActorSession.swift` 70 and 411; line 411 reassigns it when the policy
transfer succeeded). Both assignments precede the polling loop, so the string's
presence shows only that no loop exit replaced it, which means one of the expiry
exits ended the loop. `elapsed_ms ≥ budget_ms` with a working clock shows the expiry was
measured. One stored string reaches seven reply values plus the outcome.

**OT-1 (new). In the actor form, scheduler stop reasons pass through the trigger
unmapped, and a fully witnessed host kill projects `unknown`, following the
documented recognized-value rules.**
- *Source.* Every actor stop reason comes from the scheduler. The full list:
  `done`, `schedule_complete`, the visit failures, setup statuses, transfer
  failures (`policy_write_error`/`policy_transfer_deadline`) and `wait_error`.
  Only `done`, `wait_error` and the two transfer reasons appear in
  `triggerForStop`. All other values pass through as the trigger.
- `sentinel_deadline` cannot occur in the actor form, so the actor cause table's
  "Deadline expiry" row cannot be reached. That row is at
  [41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md) 972
  and `docs/RESPONSE.md` 3162.
- *Executed, public CLI, E5.* One unapplied actor with one `read_fresh` and
  `worker_post_apply_hang_ms: 3000`.
  - The override applies in the actor form. `ActorTranslation` copies it into
    every actor's input (`ActorOrchestration.swift` 186); `ActorSession` passes
    it to the worker on its command line (335–338); the worker sleeps after its
    visits and before `done` (`pw_probe_runner.c` 1675–1688).
  - Result: exit 1, `runner_failed`. The phase completed and `done_observed` is
    false.
  - The full chain is present: `grace_end: exhausted` (1000 ms),
    `termination_request {signal 9, rc 0}`, reaped signal 9, and
    `owned_reap.departure_requested: true` at stage `after_termination`.
  - The trigger and the stop reason are both `schedule_complete`. Diagnostics
    give `process_disposition: signaled`, `termination_cause: unknown` and
    `stop_reason: null`.
- *Why `stop_reason` is null in the same reply.* This comes from a separate
  projection rule with the same root.
  - The actor diagnostics `stop_reason` is defined as "the actor worker's
    supported stop reason from the recognized set listed for execution
    diagnostics. Null when no supported recognized answer was projected"
    ([41-diagnostics.surface.md](../docs/contract/41-diagnostics.surface.md)
    803–806).
  - Its first-match rule (932–943) projects the answer only when it is one of the
    six ordinary values.
  - So `schedule_complete` projects null. E1b's `died_before_completion` likewise
    projects null, while E3's `done` projects `done`.
  - The cause table (972–1011) is a different first-match rule over the trigger's
    recognized values, ending in `unknown`.
  - Both rules apply recognized sets drawn from the ordinary-worker vocabulary to
    values the actor scheduler produces.
- *Documented rules and what they leave unstated.* Both outcomes follow
  documented rules.
  - `poll_stop_reason` declares an open vocabulary: "an unfamiliar reason
    establishes only that recorded reason, and gains no known timeout or cause
    meaning" ([32-lifecycle.surface.md](../docs/contract/32-lifecycle.surface.md)
    64–70).
  - The cause rule's last case is "No eligible recognized cleanup cause".
  - `cleanup_trigger` itself has no vocabulary block. Its field statement lists
    six values (line 92) while actor replies carry others as `supported` claims.
    DT-30 recorded that difference.
  - What I did not find is any statement that the actor scheduler's own routine
    reasons fall into the "unfamiliar" class. These include `schedule_complete`
    for every actor not stopped earlier that has not published `done`.
  - Nor did I find a statement that the actor form's deadline row cannot be
    reached. "No stated rationale" is limited to that.
- Related to DT-30 (vocabulary lists): this records the executed consequence for
  cause and stop projection. Related to DT-10 for timeout labels.
- *Limit.* The run shows only `schedule_complete`. `completion_timeout`,
  `arrival_timeout` and `setup_timeout` with an exhausted grace were not executed.

**A combination that needs joining (E3, public CLI).**
- Actor A was reaped naturally at the termination gate:
  `owned_reap.stage: termination_gate`, `departure_requested: false`, capture
  ordinal 2.
- `finish()` then still assigned `done`. A's record therefore shows
  `exit_requested: true`, `cleanup_trigger: completion` and `grace_end:
  not_entered`.
- Each value is correct. "Exit was requested because of completion" does not mean
  the request caused the departure; `departure_requested: false` and the grace
  state establish that the reap came first.
- The ordinary form has no `owned_reap`. There, `child_reaped` or `not_entered`
  carry that ordering.

### Anchor DT-62: accepted custody with an unpublished issue slot

**Observers of the issue.**
1. The worker's native `sandbox_extension_issue_file` return and errno are
   written to its slot ([pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c)
   851–856). The host may read them only after the slot `completed` publication
   (store at 1096).
2. The worker publishes the outbound slot (`committed`, 878).
3. The host decides acceptance while servicing during the issuer's visit. It
   records a `CustodyObservation` with status, length and phase, clears the
   outbound token field, and acknowledges
   ([AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
   456–501).
4. The worker records its own view of that acknowledgement as
   `ext_custody_status` (C 877–883). That value becomes readable only through the
   same slot `completed` publication.
5. The host custody setup scope holds mmap, `final_erase` and munmap only.

**What reaches the reply.**
- `CustodyObservation` is used only for the token status
  (`ActorOrchestration.swift` 466–468), after the check that the slot completed,
  and for `delivered_length` (486), only when the transfer acknowledgement was
  `delivered`.
- Its `status`, `length`, `rejectDetail`, `erased` and `phaseIndex` are never
  encoded on their own.
- The surface's statement that "The native return and host custody acceptance are
  reported independently"
  ([14-extensions.surface.md](../docs/contract/14-extensions.surface.md) 377,
  authored in `f6551bf9`) describes what the host observes. It does not describe
  what the reply reports.

**Executed, public CLI, E1a against E1b.** The issue-only specimen was run without
the seam (E1a) and with `worker_kill_before_publish_slot: 0` (E1b).

| Field | E1a | E1b |
| --- | --- | --- |
| exit, outcome | 0, `finished` | 1, `runner_failed` |
| issue event | `returned`, `native_nonnull` true, `token_length` 208 | `call_boundary_observed` true, `result_published` false, `unresolved`, native fields absent |
| token record | `issued`, length 208 | `unresolved`, no length |
| host custody scope `t` | mmap 16384, `final_erase` performed 16384, munmap 0; `{mapping: released, private_erasure: performed}` | identical |
| worker scope | `{descriptor: released, mapping: held, shared_erasure: performed}`, cell 11 value 0 | `{…, mapping: held, shared_erasure: not_present}`, no cell 11 |
| actor trigger | `completion`; reaped exit 0 during grace | `died_before_completion`; reaped signal 9 at stage `schedule`, `departure_requested` false |

In E1b no public field distinguishes "the host accepted custody" from "no
publication ever reached the host". DT-62's driver output shows that the host did
accept in this configuration. That driver run is internal evidence and was not
repeated here.

**Executed, public CLI, E2: the asymmetry at the public boundary.**
- Specimen: one actor that issues and then transfers to itself, with
  `worker_kill_before_publish_slot: 1`. The seam kills the worker after the
  transfer attempt returns and before its slot is published.
- Result: exit 1, `runner_failed`.
- The issue event is `returned` with length 208, and the token is `issued`.
- The transfer event is `unresolved` and `result_published` is false.
- `transfers[0]` reads `held`, `copied`, `equal`, recipient acknowledged,
  `source_acknowledged: false`, `delivered`.
- The delivery is `delivered` with `delivered_length` 208.
- So the host's delivery observations survive an unpublished source slot, while
  the host's acceptance does not survive an unpublished issue slot.
- `ActorReplyTests` 135–156 asserts the transfer side only in-process, through
  `assembleActorReply`. This run is the public-CLI observation.
- `delivered_length` is the host's custody length. The host read it from the
  worker-written outbound length word and checked it against the framing.
  `token_length` comes from the worker's evidence slot. Both lengths were written
  by the same worker through two channels. Their equality is a consistency check,
  not two independent measurements.

**OT-2 (new). The worker's own observation of the custody answer is decoded and
discarded.**
- `ext_custody_status` reports what the worker saw:
  `none/accepted/rejected/timeout/not_published/clock_fault`
  ([pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
  164–167).
- `collectOutput` decodes it into `CWorkerExtensionPublication.custodyStatus`
  (`ActorSession.swift` 690). In the E6 driver output this decoded value is
  labelled `worker_custody_status`; it is the same field. This report calls it
  `ext_custody_status` throughout.
- I first searched `runner/Sources`, `controller/src`, `controller/tools` and
  `tests/lib`. That covers assembly, the `PWRunnerReply` integrity checks, the
  classifiers and the readers. The search found no other reference to the
  decoded field; the other `custodyStatus` hits are the host's
  `TransferObservation` string.
- A later search of `tests/suites` and `tests/fixtures` found the raw C slot word
  in three test places, none of which reads the decoded Swift field:
  - [authority_binding.c](../tests/fixtures/extension_controls/authority_binding.c)
    99 and 104, a constructed C control that drives `attempt_extension_issue` to
    `PW_CUSTODY_TIMEOUT` and then `PW_CUSTODY_ACCEPTED`;
  - the `early_erase` mutation anchor in
    [actor_handoff_mutations.py](../tests/suites/runner_unit/actor_handoff_mutations.py)
    140–141;
  - the layout printer.
- The `custodyNames` table at `ActorOrchestration.swift` 295 has no reader.
- `git log -G'custodyStatus|custodyNames' -- runner/Sources` shows the decode and
  the table were added in `c686a05f` and that no reader was ever added.
  `deb67eff` touched only the transfer field. `bc3abe2f`'s `custodyNames` is a
  different local in `PWRunnerAuthoritySetup.swift`.
- Only [ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
  305, 394 and 400 read it, in-process. E6 below recorded value 1 (`accepted`)
  for the issue slot.
- Consequence: the token status is built from the host's acceptance record
  combined with the worker's slot publication. The worker's view of whether it
  received an answer, which is what a timeout or clock fault would change, is
  retained only internally.
- I did not execute an end-to-end timeout case. The C control above produces a
  worker-side timeout status, but no test follows that word through the Swift
  decode, assembly or reply. This observation concerns which fields exist; it is
  not a demonstrated disagreement.

**Statement ambiguity.**
- "The host custody record carries token acceptance" appears at
  [14-extensions.surface.md](../docs/contract/14-extensions.surface.md) line 623
  (the `pins` of the issue-projection source support) and is rendered at
  `docs/RESPONSE.md` 2680.
- Read as `authority_setup.host.custody`, it is false: that scope never contains
  acceptance, and E1a and E1b give identical scopes.
- Read as `resources.tokens[].status`, which the failure contract calls "Custody
  status" (lines 272–281), it holds only when the issue slot was published.
- Line 429 ("Host custody records describe the controlled publication, copying
  and erasure protocol") does not settle which record is meant.

### Anchor DT-63: eventual clearing versus clearing at the declared last use

**Clearing sites.**

| Site | Extent | When | Where it is visible |
| --- | --- | --- | --- |
| Host outbound clear | the outbound slot's token field | at acceptance (`AuthorityCustody.swift` 490) | internal |
| Host private custody, issue-only last use | the custody buffer | at acceptance (482–485) | internal flag |
| Host private custody, last transfer | the custody buffer | `defer` in `serviceTransfer` (514–521) | internal flag |
| Host private custody, teardown | the custody buffer | `finish()` (633–639; `TokenCustody.finish` 311–322) | `final_erase` cell, `private_erasure: performed` |
| Host shared region, teardown | every slot's token field | `finish()` after reap, for quiescent owners (225–242) | region `shared_clear` with byte count |
| Worker inbound, last consume | that inbound slot's token field | C 936–939 | not published |
| Worker exit sweep | settled inbound slots | `erase_authority` (C 579–590), first call published once as cell 11 | worker `terminal_owned_inbound_clear` value, `shared_erasure: performed` |

The authored erase rule lists `report: runner_reply`
([14-extensions.surface.md](../docs/contract/14-extensions.surface.md) 408–421).
The reply contains only the teardown and exit rows. Neither last-use clearing
appears in any public field.

**Executed internal driver, E6 (not a public response).**
- Request:
  - A (unapplied, unentitled) issues `t` and transfers it to B as `d1`.
  - B (unapplied, selected) runs `read_fresh`.
  - A transfers `t` to B as `d2`, its last declared use.
  - B consumes `d1` (last use) and releases `h1`.
  - B runs `read_fresh`.
- Native issue, consume and release are real calls in the signed workers.
  Transfers are real host servicing.
- Each collection-hook row below is taken after the scheduler observed the
  active actor's arrival and before its release store (`ActorScheduler.swift`
  405–415). Every other live actor is parked; in V2, A is already reaped from
  phase 1 on. Each interval runs from one hook row to the next.
- V1 runs unchanged.
- V2 sets `killBeforePublishSlot = 1` on A's input only, in the driver. This is
  the same `CWorkerInput` field, and the same worker argument
  `--kill-before-publish-slot`, that the CLI override becomes. The CLI override,
  however, applies to every actor; the driver confines it to A. A dies after
  `send_d1` returns, so the last declared transfer is never serviced.

| Collection point | V1: custody flag / buffer nonzero bytes | V2: custody flag / buffer nonzero bytes | B inbound `d1`, `d2` nonzero (V1) |
| --- | --- | --- | --- |
| phase 0, A arrives | no observation / 0 | no observation / 0 | 0, 0 |
| phase 1, B arrives after `send_d1` | accepted, not erased / 208 | accepted, not erased / 208 | 208, 0 |
| phase 2, A arrives | accepted, not erased / 208 | A unavailable; no hook | 208, 0 |
| phase 3, B arrives after `send_d2` | **erased / 0** | accepted, not erased / 208 | 208, 208 |
| phase 4, B arrives after `consume_d1` | erased / 0 | accepted, not erased / 208 | **0**, 208 |
| after `run()` (teardown done) | `erased: true`, buffer unmapped | `erased: true`, buffer unmapped | regions unmapped |

What this establishes:
- In V1, with a real worker and real native token, the private custody buffer was
  cleared inside the interval from A's phase-2 arrival to B's phase-3 arrival.
  That is before teardown and consistent with the `serviceTransfer` defer.
- In V2 it was still uncleared (208 nonzero bytes, flag not set) at the last
  hook, B's phase-4 arrival. It was cleared and unmapped by the time `run()`
  returned. That interval also contains B's last visit, B's exit and `finish()`.
  Source attributes the clearing to `finish()` → `custody.finish()`, but the
  capture does not isolate it.
- The final internal `erased` flag is identical in both variants. The driver
  produces no public reply; in the public CLI runs (E1a, E1b, E3) the custody
  scope likewise shows only `final_erase` performed, the same in each.
- In V1, B's `d1` inbound slot was zero at phase 4 while `d2` stayed nonzero.
  This places the worker's last-consume erase before its exit sweep.
- V2 also shows the worker's own published `ext_custody_status` (1, accepted)
  and A's unpublished `send_d1` slot beside a delivered host transfer.
- B exited 0 in both variants, and both PIDs were absent to `kill(pid,0)` after
  the run.
- B's `consume_d1` returned native 0 in both variants. B is unapplied here and
  uses the selected worker. In E3, where B is applied, both consumes returned 1;
  DT-59 recorded 0 for an unapplied, unentitled self-consumer. Both 0 and 1 are
  candidate handles; only −1 means failure. The last-use erase runs whatever the
  result (C 933–940), so the erasure observation does not depend on the value.
  No claim about native handle numbering is made.
- Limits: equipment binding, live inspection, validator collection and reply
  encoding do not run in the driver. Each interval is bounded by collection
  points, not exact instants.

**Tests that read only the final state, and the observers.**
- [ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
  467–468 credits clearing at the last declared transfer but reads the
  post-teardown flag. Line 307, in the calibration case, also reads that flag
  after teardown, without a timing comment.
- E6 V2 shows, with real workers, the relationship DT-63 showed with a
  constructed input. When the last-transfer site never ran (the declared transfer
  was never serviced), the final flag is the same as when it ran. The flag
  therefore cannot tell the two sites apart.
- V2 is not a case in which the line-468 assertion would fail for the input that
  test runs (its self-transfer does execute). The point concerns what the
  assertion's comment credits, not its verdict.
- The footprint snapshot ([actor_snapshot.swift](../tests/fixtures/footprint/actor_snapshot.swift)
  46–50, asserted in [footprint_workloads.py](../tests/lib/footprint_workloads.py)
  118) reads `TokenCustody.erased` as false *before* the last transfer. It reads
  flags only, not memory.
- No existing observer covers the interval between the last transfer and
  teardown on the host side.

**OT-3 (new; worker-side counterpart, qualified). The boundary observer for
inbound erasure records only a cumulative result; a separate synthetic fixture
counts erase calls.**
- [control.c](../tests/fixtures/extension_controls/control.c) 117–130 rewrites
  one word, `worker_token_erased = clear && !failures`, on every erase call over
  the observed inbound slot. Each call scans the full 16,384-byte field. It keeps
  only a cumulative failure count, with no call site, count or interval.
- [check_extension_boundaries.py](../tests/suites/witness_contract/check_extension_boundaries.py)
  336–338 reads only those words.
- The worker erases that slot at the last consume and again in the exit sweep. So
  that observer would also pass if only the exit sweep ran.
- However, [terminal_control.c](../tests/fixtures/extension_controls/terminal_control.c)
  100–105 counts every erase call and checks the full buffer after each.
  [check_terminal_erasure.py](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py)
  91 requires `erase_calls >= 3` for `consume`. In that fixture the three calls
  are the last consume, the sweep after the visits, and `publish_done_and_exit`
  (one settled slot of two). Without the last-use erase the count would be 2.
- That guard is synthetic and count-based, not a timing observation. No mutation
  was executed here.
- E6 V1 supplies the timing observation internally. The host side has no
  equivalent guard.

### Anchor DT-66: equal native handles and their release boundaries

**Executed, public CLI, E3 (rebuild of DT-66).**
- Result: exit 0, `finished`.
- Both consumes returned native 1, and each handle lists the other in
  `raw_equal_handles`. Both releases returned 0 with errno 0.
- Fresh reads:
  - `baseline`: open −1, errno 1;
  - `during`: open 5, read 27;
  - `after_r1`: read 27;
  - `after_r2`: −1, errno 1.
- Both successful reads returned the target bytes with device 16777233 and
  inode 278532339.
- All four queries were `deny` with `query_first`. The queries were collected at
  B's arrival, before any of the phase's consumes or releases.
- The gate was satisfied, with capture ordinals: A activation 1 < A owned reap 2
  (natural, `termination_gate`) < gate 3. B's `b_use` activation timestamp is 3 µs
  after A's reap timestamp.
- Both PIDs (43783, 43784) were absent afterward.
- This reproduces DT-66's pattern on the rebuilt specimen.

**What each handle field records.**

| Field | Producer | Observation time |
| --- | --- | --- |
| `status: produced` | consume slot publication | the consume |
| `native_handle` | consume slot publication | the consume |
| `raw_equal_handles` | assembly comparison of two consume slots' numbers | reply assembly |
| `release_attempted` | the release slot's `call_boundary` marker | stored before `extension_release` (C 948–950); read at final collection even when the slot never completed (`ActorSession.swift` 652) |

- 14-extensions line 948 defines `release_attempted` as "an observed native
  call-boundary marker". So "attempted" means the worker reached the pre-call
  store. It is not evidence of entry into, return from, or the effect of the
  native call.
- The worker never clears `handle_valid` after a release (C 943–957).
- No handle field changes on release, on access loss, or on process exit.
- Apart from references, step IDs and each listing the other in
  `raw_equal_handles`, the two handle records are identical (`produced`, native
  handle 1, `release_attempted: true`), and so are their release events
  (`returned`, 0, errno 0). Yet access after `release_h1` succeeded and access
  after `release_h2` failed.
- Only the `read_fresh` observations, each a separate worker publication, carry
  the access boundary. The handle records describe production and release-call
  reachability, not present usability. After the reap, the process that held
  these numbers no longer exists.

### Anchor DT-68: worker ownership beside host-observed termination

**Established observation time of each value.**
- The worker scope is decoded from the worker's evidence region during
  `collectOutput`, after reap (`ActorSession.swift` 489, 768).
  - `descriptor` comes from cell 9 (setup).
  - `mapping: held` comes from cell 8 `mmap` succeeded (setup).
  - Only cell 12, `rejected_mapping_munmap`, could change `mapping` (setup
    failure path).
  - `shared_erasure: performed` comes from cell 11, published at the first exit
    sweep before `done` or before an exit-request `_exit`
    ([AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift)
    104–108; C 600–606, 820, 1673).
- Host region and custody scopes are read after `custody.finish()`, which follows
  every actor's stop and reap (`ActorScheduler.swift` 557–583, 184–193). Their
  `released` values are host calls observed before assembly.

**Executed observations.**
- In E1a, E1b and E3 every worker scope reads `mapping: held` while the same
  reply reports that actor reaped and the host region `mapping: released`.
- This holds for a clean exit (E1a, E3), for a SIGKILL before publication (E1b,
  where `shared_erasure` is `not_present`), and for a natural reap at the gate
  (E3 A).
- E5, with no authority plan, shows `not_required` and `not_acquired`.
- [WORKER.md](../docs/WORKER.md) row a2 ("Mapping through worker exit") and
  line 65 state the rationale: the worker keeps its mapping until exit and never
  publishes a normal unmap. Exit itself is observed as the host's reap.

**OT-4 (new). The worker's `shared_erasure: performed` does not imply that bytes
existed or were cleared then, and its extent differs from the host key with the
same name.**
- Cell 11's public `value` counts bytes overwritten in settled inbound slots.
- In E1a and in E3's A, which have no inbound slot, it is 0 with
  `performed`.
- In E3's B it is 16,384. B's only inbound slot had been cleared by its last
  consume, according to source (C 936–939); E6 V1 observed exactly that ordering
  in the driver (zero after the last consume, before the exit sweep). The sweep
  value counts bytes overwritten, including bytes that were already zero.
- The host region's `shared_clear` under the same `shared_erasure` key covers
  every slot: 16,384 for E1a's single outbound slot and 32,768 in E2.
- `final_erase: performed` is likewise recorded whenever the custody buffer
  exists, whether or not it ever held accepted bytes (`TokenCustody.finish`
  311–322).
- No statement gives `performed` a meaning that a value of 0 contradicts. RESPONSE
  lists the states without an extent.

**Judgment, kept apart from the established timing above.**
- One field, `ownership`, documented as "Named ownership states" with no time
  anchor ([34-equipment.surface.md](../docs/contract/34-equipment.surface.md)
  line 870), carries two kinds of value:
  - host values that record the outcome of the host's own last call on the
    resource;
  - worker values that describe the last state the worker published before it
    exited.
- For host values, "last call" means the munmap, close, unlink, `shared_clear`
  or `final_erase` in `ActorAuthorityRegion.tearDown` or `TokenCustody.finish`.
  `ActorScheduler.finish()` runs these before it builds the outcome, so they
  happen before assembly.
- PW makes no later call on these resources. The deinitializers that call
  `tearDown`/`finish` again return at once (`tornDown`/`finished` guards,
  `AuthorityCustody.swift` 226, 312, 634).
- A host `released` value therefore stays accurate after the reply as far as PW
  is concerned.
- An `unresolved` value records a failed call. The resource then remains held
  by the host process with no further PW action; what happens to it when that
  process ends is outside these records.
- `withheld_not_quiescent` records that the host did not erase. It says nothing
  about the region object's later state.
- WORKER.md explains the worker value, but the ownership definition does not
  point to that explanation. A reader of the final JSON must join
  `mapping: held` with `reaped`, the gate, or `collection_basis` to place it in
  time.
- The cost is interpretive: no reader or classifier uses worker `held`.
  - Python [actor_evidence.py](../tests/lib/actor_evidence.py) 100–114 and Rust
    `porcelain_actor.rs` 312–345 check that `released` is backed by a successful
    cleanup operation and that `performed` is backed by a performed erasure cell
    (`shared_clear`, `final_erase` or `terminal_owned_inbound_clear`).
  - The `performed` check does not constrain the cell's value, which is why a
    value of 0 passes (OT-4).
  - I found no decision that depends on worker `held`.
- This is not a leak claim. Process absence does not establish the disposition
  of other resources.

### Cross-anchor account

**Timeline of one executed reply (E3).** Each step names the observer.

1. The host creates and maps the authority regions and custody before launch
   (region and custody setup cells, host time).
2. The worker publishes setup cells 8 and 9: mapping held, descriptor released.
   They are read at final collection.
3. B: activation (capture ordinal 1), validator query at arrival, release, then
   `baseline` read published.
4. A: activation, issue native return (slot), outbound commit. The host accepts
   (internal record) and clears the outbound slot. The transfer is serviced and
   delivered (host observation, later public). A's last-use defer clears
   custody (internal; not public). A's slot is published. A's exit sweep (cell 11,
   value 0) and `done`.
5. Gate: A's natural reap is observed (capture ordinal 2, `departure_requested`
   false). The gate closes (ordinal 3).
6. B: `b_use` activation and query collection, which provides the `query_first`
   outcomes for all four reads. Then two consumes, `during`, release h1,
   `after_r1`, release h2, `after_r2`. According to source, the last consume
   (`consume_h2`) clears B's inbound slot; this is not published and was not
   observed in E3. Slot publications follow each action.
7. B's exit sweep (cell 11, value 16,384) and `done`.
8. `finish()`:
   - A is already reaped, yet it gets the `done` stop reason, an exit-request
     store and `grace_end: not_entered`.
   - B gets an exit request and is reaped during grace (ordinal 3,
     `departure_requested` true).
   - `collectOutput` maps each trigger and decodes the worker scopes.
   - `custody.finish()` erases custody (`final_erase`), sets the internal
     `erased` flags, erases and unmaps the shared regions.
9. Assembly computes token `issued` from the slot plus the host record,
   `delivered_length` from the host record, and handle `produced` and
   `raw_equal_handles`.

The temporal claims that survive into the reply as explicit ordering are:
- capture ordinals with `observed_ns` (activations, owned reaps, gates);
- visit intervals and wait records with `elapsed_ms`;
- `collection_basis`;
- `owned_reap.departure_requested`.

These carry no recorded time in the reply and keep only a final value: custody
acceptance (and only through token status), the cleanup trigger, handle
production and release, and the worker mapping. Last-use clearing on either side
is not reported at all.

**Answers to the three questions.**

1. *Observers and derived values.*
   - The worker observes native returns, call markers, fresh-read effects, setup
     cells and its own custody and transfer answers.
   - The host observes waitpid, kill, grace end, custody acceptance, transfer
     servicing, region and custody setup and cleanup, gate ordinals and query
     collection.
   - Derived from one stored value: `cleanup_trigger`, the stop-reason claim,
     `sentinel_wait.stop`, `runner_timeout` and the diagnostics stop and cause
     (from `pollStopReason`); token status (slot plus host record);
     `raw_equal_handles` (two slots).
2. *What survives, and what is withheld, overwritten, merged or internal.*
   - Withheld: host acceptance when the issue slot is unpublished (DT-62, E1b).
   - Also withheld: the worker's unpublished slot payload (native result, errno,
     length, custody word). This follows the stated publication rule:
     - `collectOutput` reads slot payloads only after the slot's `completed`
       acquire (`ActorSession.swift` 645–655: "Read only confirmed slots");
     - the `result_published` definition: "A false value withholds native
       result fields even if a call boundary was observed"
       ([14-extensions.surface.md](../docs/contract/14-extensions.surface.md)
       line 544);
     - the failure contract's `unresolved` row (no native return, errno or
       unavailability decision is inferred, line 315) and its rule that "A call
       whose return was not published remains unresolved even when an
       independent test intervention knows that it returned"
       ([FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
       lines 317–319).
   - Overwritten: the internal `erased` flag, by teardown.
   - Merged: last-use and teardown clearing, into teardown cells; host and worker
     scopes under one `ownership` vocabulary; trigger and stop reason.
   - Internal only: `CustodyObservation` status, length, reject detail and phase;
     worker `ext_custody_status`; `TransferObservation.recipientRejectDetail` and
     service phase; `TokenCustody` state.
3. *Combinations that invite unsupported inference.*
   - `exit_requested: true` with `cleanup_trigger: completion` for an actor reaped
     earlier (E3 A), read as a departure caused by the request.
   - `issued` with `last_use_step_id` and `final_erase: performed`, read as
     clearing at last use (DT-63, OT-4).
   - `produced`, `release_attempted: true` and release `0`, read as revocation
     (E3).
   - Worker `mapping: held` with reaped, read as a present mapping (DT-68).
   - `shared_erasure: performed`, read as "token bytes cleared at exit" (OT-4).
   - Equal `token_length` and `delivered_length`, read as two independent
     measurements (E2).
   - A full kill chain with `unknown`, read as missing evidence rather than an
     unmapped trigger (OT-1).

**How the findings bear on each other.**
- *Tension between DT-62 and DT-46.* The record withholds an independently
  observed host fact (acceptance) because a different publication is missing,
  while it presents a derived value (trigger) as a fact recorded at the store.
  The two are not symmetric:
  - The trigger's documents acknowledge its one-to-one dependence on the stop
    reason, and the cause fallback text does not count it among the independent
    observations. The inaccuracy is the recording time, which has existed since
    `c686a05f`.
  - The acceptance case loses a host observation the statements say is "reported
    independently".
- *Shared mechanism between DT-63 and OT-4.* Teardown and exit records stand in
  for every clearing. The final flag (internal), the custody cell and the
  worker's cell 11 all describe the last clearing, not the declared one. E6 V1/V2
  show that the same final values arise either way.
- *Different boundary between DT-66 and DT-68.* Both concern historical values
  after reap. Handles are explicitly scoped by their definitions ("candidate
  handle", "relates raw numbers"). Worker `held` is not.
- *Historical labels.* They do not uniformly suggest the present tense:
  - Host scope values record the host's last call on each resource, made before
    assembly, with no later PW action (see DT-68 above).
  - The resource tables are explicitly "observed production"
    ([14-extensions.surface.md](../docs/contract/14-extensions.surface.md)
    line 776).
  - The present-tense risk is concentrated where no time anchor is stated: worker
    `ownership`, `performed`, and the cleanup-trigger recording wording.

### Smaller observations

- OT-5: In E3, A's `stop_reason` and trigger reflect `doneObserved` at `finish()`
  even though A was already reaped. `finish()` checks only `doneObserved`
  (`ActorScheduler.swift` 562), and the gate's reap is recorded separately.
- OT-6: Copies of the stop reason taken before `requestExit` exist in both forms,
  but only the single-worker copy is published.
  - Single-worker form: `sentinel_wait.stop` (`CWorker.swift` 1271) is published.
  - Actor form: `stopActor` keeps an internal copy in
    `ActorSessionRecord.stopReason` (`ActorScheduler.swift` 548) before it sets
    `pollStopReason` and calls `requestExit`. `finish()` does not set this copy
    for actors it stops (562).
  - No production code reads it. `ActorSchedulerTests.swift` 572 and 607 do. It
    never reaches the reply. (The E6 driver printed it as `stop_reason`.)
- OT-7: For a transfer, the published `phase_id` is the declared delivery phase
  (`ActorOrchestration.swift` 453). The host's servicing phase
  (`TransferObservation.phaseIndex`) is internal.
  - By source the two match: `service` is called only during the source actor's
    active visit, with that visit's phase (`ActorScheduler.swift` 444).
  - No run here printed the internal value.
- OT-8: `ActorReplyTests` 112–133 asserts the interrupted issue's `unresolved`
  token and event, and does not assert host acceptance (as DT-62 notes).
  - That test does run the production equipment binding and live inspection
    through `checkedActorSchedule` (27–35). It also runs Swift reply validation
    and encoding (`admittedReplyData`, `ReplyFailureTests.swift` 110–113).
  - It skips the XPC service entry, `runActors` orchestration and validator
    collection. It sets the kill seam on actor 0 only.
  - E1b is the public-CLI counterpart.

### Coverage and remaining limits

- Executed:
  - six public CLI specimens (E1a, E1b, E2, E3, E4, E5);
  - two path-length checks (C7a, C7b);
  - one internal driver with two variants (E6).
- Not executed:
  - the actor-form `completion_timeout`/`arrival_timeout`/`setup_timeout`
    variants of OT-1;
  - an end-to-end worker custody timeout or clock fault, for OT-2 (a constructed
    C control exists; see OT-2);
  - a clock-fault deadline;
  - mutation of either last-use erase;
  - any registered suite.
- I did not rerun DT-62's internal acceptance print. The pass did not
  characterize native release reference counting, revocation, or the cause of
  errno 1.
- E4 is a shortened-timeout control, not evidence about the production duration.
- History findings rest on `git log -S/-G` and `git show` of the named commits.
  No older binaries were executed.
- Only the drafts and the response file under
  `records/contract-trio/observation-time/` were written. No tracked source, test
  or document was changed.
