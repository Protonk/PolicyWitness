# Validation memo 1: observation-time report (draft-1)

Validator: Sonnet 5.5, read-only. Report: `records/contract-trio/observation-time/draft-1.md`.
Source snapshot: HEAD `cc55288d`. Artifacts: `.tmp/contract-trio/observation-time/`.
No native experiment was run and no rerun of a CLI specimen was needed. I read the report, the plan's
instructions, DT-46/62/63/66/68, the cited source, tests and docs, `git log -S/-G` and `git show` output, and
the saved captures (`runs/*/stdout.json`, `runs/e6/*.json`) through `/usr/bin/python3 -I`.

## Concerns

### C1. OT-6: "the actor form has no equivalent store-time copy" (incorrect)
- Location: "Smaller observations", OT-6 ("`sentinel_wait.stop` is the only copy of the stop reason taken before
  `requestExit`").
- Checked: `ActorScheduler.swift` 545-551 (`stopActor`). It writes `records[index].stopReason = reason` at 548,
  then `session.pollStopReason = reason`, then `session.requestExit()`. The field is declared at line 69.
  `grep "\.stopReason\|stopReason:" runner/Sources` finds no reader of the record field.
- Finding: the actor form does keep a copy of the stop reason made before the exit-request store. It is internal,
  unread, and written only by `stopActor`, not by `finish()` (562). The report's own writer list cites line 549 and
  never mentions 548. The statement is wrong as written. The narrower claim holds that no such copy reaches the
  reply or is read. Classification: incorrect.

### C2. OT-8: "The test bypasses public equipment binding through `checkedActorSchedule`" (incorrect citation of what the helper does)
- Location: OT-8.
- Checked: `ActorReplyTests.swift` 27-35. `checkedActorSchedule` calls `ActorEquipmentPreparation.bind(...)` with
  `signedEquipmentCalls()` and installs a `didSetUp` hook that calls `equipment.inspect`. Lines 112-133 use the real
  `pw-probe-runner`.
- Finding: the test performs equipment binding and live inspection through the production type. It bypasses only the
  XPC and public orchestration, validator collection and encoding. "Bypasses public equipment binding" overstates
  the gap. This also bears on E6's own description, which I could not verify for the driver (see limits).
  Classification: incorrect.

### C3. DT-46 section: mapping-change detection (scope not justified)
- Location: "No reader treats the copies as corroboration": "That fixture therefore cannot detect a mapping change";
  "`TRIGGER_FOR_STOP` ... used only for a vocabulary self-check and an export (752, 801)".
- Checked: `DispositionResolverTests.swift` 44 and 527. Line 527 is
  `expectEqual(mapping(export["trigger_for_stop"]), PWDisposition.triggerForStop)`. It compares the Python export
  with the production Swift map. Python 801 produces that export.
- Finding: the statement is true of the fixture at line 44, which builds from the production map. Mapping drift
  between Swift and Python is detected at 527, so "used only for ... an export" omits that the export has a Swift
  consumer. The report's central point (no reader treats the copies as corroboration) is unaffected. The sentence
  about detecting a mapping change needs "that fixture alone", plus mention of 527. Classification: scope not
  justified. Related: `tests/lib/lifecycle_contract.py` 105-106 carries a third "recorded at the exit-request
  store" comment, not listed among the report's wording sites.

### C4. E4 paragraph: "The only code that ever assigns the string `sentinel_deadline` is the initializer" (incorrect, internally inconsistent)
- Location: Anchor DT-46, E4 section, last paragraph.
- Checked: `ActorSession.swift` 70 and 411. Line 411 assigns `"sentinel_deadline"` when the policy transfer
  succeeded. The report itself lists "70, then 411" in its writer list.
- Finding: two assignments exist, both before the loop. The inference drawn (presence of the string at reply time
  shows only that no loop exit replaced it) still follows. The sentence is wrong as stated. Classification:
  incorrect.

### C5. OT-2: reader search scope and "only ... read it" (supported with caveat)
- Location: OT-2.
- Checked: grep for `custodyStatus|custodyNames|ext_custody_status|worker_custody_status` over runner, controller,
  tests and docs. The Swift-side result matches the report: decode at `ActorSession.swift` 690, `custodyNames` at
  `ActorOrchestration.swift` 295 with no use, and the three test reads. The `git log -G` history matches
  (c686a05f, deb67eff, bc3abe2f). deb67eff touches only the host-observation string; bc3abe2f's `custodyNames` is
  the unrelated local.
- Caveat: the raw C slot word is read by `tests/fixtures/extension_controls/authority_binding.c` 99 and 104
  (`PW_CUSTODY_TIMEOUT` then `PW_CUSTODY_ACCEPTED`), and appears in
  `tests/suites/runner_unit/actor_handoff_mutations.py` 140-141. The report searched only runner, controller and
  `tests/lib`, and its "Only ActorAuthorityTests ... read it" is about the decoded Swift field. The report also
  says the worker-side timeout case was not executed, but a C-level control for that status exists. This does not
  disturb the "no public or assembly reader" conclusion. The report should state that the search excluded
  `tests/fixtures` and `tests/suites`. Classification: supported with a caveat on search scope.

### C6. E6 V2: "In V2 it was cleared only at teardown" and "real-worker counterexample to what the line-468 assertion means" (overstated)
- Location: E6 "What this establishes" and "Tests that read only the final state".
- Checked: `runs/e6/issuer_killed.json` and `last_transfer.json`, summarized by a Python reader. V1 hooks:
  `b_after_first` accepted/208, `a_last` accepted/208, `b_after_last` erased/0, `b_after_consume` erased/0. B inbound
  (d1,d2): [208,0], [208,0], [208,208], [0,208]. V2 hooks: no `a_last` hook; the last hook, `b_after_consume`, shows
  accepted, not erased, 208. The final `erased` is true in both, and PIDs are absent. The table matches the capture.
- Findings:
  - "Cleared only at teardown" is bounded only as "after the phase-4 hook and before `run()` returned". The B
    visit after the hook, B's exit and `finish()` all lie inside that interval. The report states elsewhere that
    intervals are bounded by collection points, but this sentence drops the bound. Source (`finish()` ->
    `custody.finish()`) makes teardown the likely site, but the capture does not show it.
  - In V2 the declared last transfer (d2) is never serviced because A died. The final flag is therefore compatible
    with the production code for this input. V2 shows that the flag does not distinguish the two erasure sites
    when the last-transfer site never ran. That is the same relationship as DT-63's constructed counterexample, now
    with real workers. It is not a case where the assertion at 468 would be false in the case it tests (a run where
    the self-transfer executes). "Counterexample to what the assertion means" needs that qualification.
- Not contradicted: V1's observation (cleared inside the A phase-2 to B phase-3 interval) is supported by the
  capture. Classification: overstated.

### C7. Undisclosed difference between E6 and E3/DT-62 values (unresolved, minor)
- Checked: in `runs/e6/*.json`, B's `consume_d1` has `native_result` 0, and B's reads succeed before the consume
  (B is unapplied there). In E3 both consumes returned 1. DT-62's driver printed accepted length 216 where E1a, E2
  and E6 show 208.
- Finding: the report says consume and release are real calls in E6 but does not mention that the consume return
  differs from E3, or that the earlier driver's 216 differs from 208. Per the C code (`pw_probe_runner.c` 933-940)
  the last-use erase runs on any result, so the erasure inference is unaffected. The 216-versus-208 difference is
  not explained (token class, path or framing). Classification: scope not stated; unresolved.

### C8. OT-4 / DT-68 judgment: reader description incomplete (minor)
- Location: DT-68 anchor, "The cost is interpretive ... check only that `released` is backed".
- Checked: `tests/lib/actor_evidence.py` 100-114 and `controller/src/porcelain_actor.rs` 312-345. Both also require a
  `performed` erasure state to be backed by an operation (`shared_clear`, `final_erase` or
  `terminal_owned_inbound_clear`). The `performed` check does not constrain the value, so the report's OT-4 point
  (a value of 0 still reads `performed`) stands. The sentence should say "released and performed". Classification:
  supported with a caveat.

## Consequential claims checked and found supported

- E1a/E1b/E2/E3/E4/E5 tables: every cited field compared with the saved captures (`summarize.py` output and direct
  JSON reads). The matches cover exit codes, issue events and token records, custody and worker scopes, stages and
  `departure_requested`, triggers, E4's budget/elapsed/excluded values and E5's diagnostics. All stderr files are
  empty. The overrides in each `specimen.json` match the report.
- E3: A's natural reap at `termination_gate` (ordinal 2, `departure_requested` false), B's `b_use` activation 3 us
  after the reap (3531166987247000 minus 3531166987244000), `exit_requested: true`/`completion`/`not_entered` for A,
  and equal native handle 1 with release 0/0. The fresh-read values and identities match, and the handle records
  differ only in references. All four validator records are `deny`.
- OT-1 mechanics: `PWRunnerDisposition.swift` 21-23 (six-entry map), `ActorScheduler.swift` 545-563 (all stop reasons
  assigned before `requestExit`), 249 and `ActorSession.swift` 411 (transfer-failure path only), and
  `porcelain_admission.rs` 1342-1419 (`_ => "unknown"`). `schedule_complete` and `died_before_completion` are
  absent from the map, and `sentinel_deadline` cannot reach `stopActor` (the only caller with the initial value
  carries a transfer failure). E5's `unknown` with a full kill chain matches the capture. No document mentions
  `schedule_complete`, which supports the "no stated rationale" remark (the search scope is unstated but my own
  grep over `docs`, `tests/*.md`, `runner/*.md` and `controller/*.md` agrees). Related gap not discussed: the
  documented trigger vocabulary is six values (32-lifecycle line 92) and the actor reply carries other values as
  `supported` claims.
- Single-worker loop exits (CWorker 1160-1275): the four expiry exits leave the default; `child_reaped`,
  `wait_error` and `done` assignments are as listed.
- History: 0b6e191e (2026-09-27 13:37) wording "recorded at the exit-request store"; 0ed4ae7a (14:41) added the
  comment and the derivation immediately after `storeRelease`; c686a05f (2026-11-03) removed them from `CWorker.swift`.
  RESPONSE "Host fact recorded when it requests exit" first appears in f6551bf9 (2026-11-10), as does "reported
  independently". Quoted doc lines (41-diagnostics 972 and 1014-1017, 14-extensions 377/429/623/776/948, 34-equipment
  870, 408-421) match at HEAD.
- DT-62 anchor: `ActorOrchestration.swift` 462-488 (token status chosen from slot completion first, then custody
  `accepted`; `issued_uncustodied` exists; `delivered_length` taken from the host record only when delivered);
  `outcome.custody` has no other reader. `AuthorityCustody.swift` 482-490 (accept, erase, ack) and 514-521 (defer
  erase). C 851-857, 877-883, 1094-1097. E2 shows delivery observations surviving an unpublished source slot.
- DT-63 sites: `erase_authority` counts `PW_EXTENSION_TOKEN_BYTES` per settled inbound slot, so B's 16384 and A's 0
  follow from source. C 937-940 (last-use erase), `ActorAuthorityTests` 467-468 and 307 read the post-teardown
  flag. The footprint snapshot asserts `not erased` before the last transfer (flags only). `control.c` 117-130 keeps
  a cumulative word, and `terminal_control.c`/`check_terminal_erasure.py` 91 require `erase_calls >= 3`.
- DT-66/68: `handle_valid` is set at 935 and never cleared; the `release_attempted` marker is stored at 948 before
  the native call. Worker `mapping: held` with `reaped` appears in every actor capture. `AuthoritySetupRuntime.swift`
  104-108 supports the `held`/cell 11 derivation.

## Unresolved limits

- E6 driver: I did not rebuild it or inspect `Tests/PWRunnerCoreTests/main.swift`, so the claims that hook rows are
  taken with the active actor parked at arrival, that the driver counts only nonzero bytes, and that V2's seam is
  confined to A are unchecked beyond the capture's field layout.
- I did not verify the build-environment statements (Swift 6.4.2, SDK, hashes of the driver and executables).
- The cross-anchor timeline (step 4 "A's last-use defer clears custody"; step 6 last consume clears B's inbound slot)
  is explicitly source-only. I confirmed it against source but there is no observation for E3.
- The OT-7 claim (published `phase_id` is the declared phase; the host servicing phase is internal) was checked only
  at `ActorOrchestration.swift` 453, not against the schema.
- I did not run the worker-timeout case for OT-2, the actor-form timeout variants for OT-1, or any mutation.
