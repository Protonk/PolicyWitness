# E-custody-setup-trigger — read-only assessment

Branch `main`, HEAD `837296af`. Every `file:line` below is at HEAD.
Product source under `runner/` and `controller/` is the reviewed source: the only
differences from `3d3f8e65` and from the review snapshots (`b8df8953`, `57d2375a`,
`cc55288d`) are the generated worker-identity lines (`runner/Sources/PWRunnerCore/CWorker.swift:52-53`,
four lines of `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`).
`tests/lib/extension_evidence.py`, `actor_evidence.py`, `consumer.py`, `lifecycle_oracle.py`
and `lifecycle_contract.py` are unchanged since `cc55288d`.

Nothing was built, and nothing was run against the app. This pass wrote only this file and two probe
scripts under `work-E-custody-setup-trigger/`.

Tree state: `git status` was clean when the pass started. At 19:24 on 2026-11-17 it showed nine modified
tracked files and one untracked file that this pass did not write: `docs/ARCHITECTURE.md`,
`docs/DEPENDENCIES.md`, `docs/architecture.json`, `tests/CHANGE-VERIFICATION.md`, `tests/README.md`,
`tests/catalog.json`, `tests/suites/source_drift/README.md`, `tests/suites/source_drift/check_planner.py`,
`tests/suites/source_drift/run.sh` and new `tests/suites/source_drift/test_markdown_reader.py`
(modification times 19:14–19:23; the diffs move the `source_drift/markdown_reader` case to a pytest
module). Another writer is active in the checkout. Those edits touch none of the lines cited here;
`docs/ARCHITECTURE.md:358` and the case identifiers used below were re-checked after they appeared.

## Evidence used and its availability

| Evidence | State on 2026-11-17 | Use here |
| --- | --- | --- |
| `/private/tmp/pw-failure-trace-elssragi/` (DT-46 investigation) | absent | none; DT-46 is source/test/history reading and was re-read |
| `/private/tmp/pw-authority-trace-3QC3qQ/` (DT-59–62, DT-65: CLI runs, copied Swift driver, reader variants) | absent | none; executed claims of that investigation are **not re-observable**; source re-read |
| `.tmp/contract-trio/observation-time/runs/{e1a,e1b,e2,e3,e4,e5,c7_len45,c7_len55}` (public CLI captures, app build `8b5de2b2`) | present | parsed in memory; they show what that investigation recorded, not current behavior |
| `.tmp/contract-trio/observation-time/runs/e6/{issuer_killed,last_transfer}.json` (internal driver) | present | read; internal observation only |
| `.tmp/contract-trio/acceptance/corpus/analysis.txt` rows `f61-core-limit-absent`, `f61-core-limit-failed`, `f61-not-required` | present | read; seam frames with a constructed contract binding |
| Target file `/private/tmp/pw-trio-ot-xVGRMW/target` | absent | specimens cannot be replayed as recorded |
| History (`git show 0ed4ae7a`, `c686a05f`, `0b6e191e`, `f6551bf9`) | available | re-checked for DT-46.d / DT-120.d |

Two constructed, in-memory probes were run with `tests/lib/python.sh -I` (scripts in
`.tmp/trace-integration/assessments/work-E-custody-setup-trigger/`; they read files and print):

- `reader_probe.py`: the **current** `actor_evidence.validate_actor_evidence` and
  `extension_evidence.validate_actor_extensions` over edits of the retained E3 body.
  Results: baseline `[]`/`[]`; token `issued_uncustodied` beside the delivered transfer `[]`/`[]`;
  B's `core_limit` removed, `core_limit` failed, `required:false`, host `regions` emptied (each with
  `ready` kept) `[]`/`[]`; `ready` beside `integrity_errors:["setup_association_mismatch"]` →
  `['invalid setup cells cannot establish readiness']`.
- `rule_probe.py`: the consumer relations proposed below, applied to seven
  `tests/fixtures/contract/actor_*_reply.json` files, `tests/fixtures/example_round_trip/constructed_actor_run.json`,
  the 16 accepted rows of `tests/fixtures/contract/actor_evidence.json`, five retained captures and the
  acceptance `live/actor` capture: no row is newly rejected.

"Constructed" below means input built by hand or by editing a capture; "live" means a run of the signed app.
No live observation was made in this pass.

---

## Subject 1 — DT-36 / DT-43: gate reap before ownership-loss classification; lifecycle rendering and resolution

### 1.1 Claims

| id | Claim | Boundary (form; representation; observer; time) | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-36.a | After a failed visit the scheduler cancels as `unresolved_termination` whenever the failed actor is not reaped and reaches `ownership_lost` only for a reaped actor; an ECHILD wait error leaves the child unreaped, so that case reports `unresolved_termination`. | actor form; `schedule.cancelled` and the `schedule cancelled:` error text; host scheduler; at the failed visit | yes — `runner/Sources/PWRunnerCore/ActorScheduler.swift:465-480`, `:545-554`; `CWorker.swift:1098-1107`, `:1112`; `ActorSession.swift:574` | review: source read at `bfc74b6b`, not executed, nothing retained. Now: re-read | consequential ambiguity |
| DT-36.b | No test asserts `ownership_lost` as a schedule cancellation; the "lost ownership" test injects ECHILD and asserts `quiescence == "unresolved"` and `cancelled != nil` without naming a label. | runner unit test; constructed wait fault through `ChildProcessCalls` | yes — `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift:365-407` (assertions at 394, 397); no comparison of `cancelled` with `"ownership_lost"` or `"unresolved_termination"` exists in `runner/Tests` or `tests/` | review: test read. Now: re-read and grep | overstated coverage credit (narrow: `docs/contract/13-actors.surface.md:247` credits "cancellation conditions") |
| DT-36.q | The preceding sentence ("unresolved termination cancels the remaining schedule") is consistent with the producer when the sentences are read in order; this is the wait-error counterpart of DT-10. | reading of one rule | yes | reading | accurate observation needing no change |
| DT-43.a | Actor-form dispositions are resolved with `plan: nil`, while the rule says resolution uses the "submitted plan"; `attempt_support` is then `supported` for every slot, including extension actions. | actor form; `actors[].subprocess.disposition.steps[]`; host resolver; at assembly | yes — `ActorOrchestration.swift:307`; `CWorkerDisposition.swift:80-82`, `:148-149`, `:359`. Retained captures E1a, E2, E3 show `attempt_support: supported` for issue, transfer, consume and release steps | review: source read; envelope cited by a sub-pass, not re-read then. Now: source re-read and retained captures read | inaccurate mechanism account |
| DT-43.b | "Lifecycle answer value" renders alternatives labelled `Integer` and `Request`; the JSON is a bare integer or a bare request object and the labels are not keys. | public JSON; rendered RESPONSE table | yes — `docs/RESPONSE.md:1899-1907`; subject without prose at `docs/contract/32-lifecycle.surface.md:810-815`; `#[serde(untagged)]` at `controller/src/porcelain_records.rs:12`; captures show `"value": {"rc":0,"signal":9}` and integers | reading; retained captures read | consequential ambiguity (minor) |
| DT-43.c | The lifecycle surface's support says "explicit rule and evidence gaps preserve scope"; the surface declares no gap node. | support metadata of one surface | yes — `docs/contract/32-lifecycle.surface.md:1534`; `grep -c ': gap}'` on that file is 0 | counted | inaccurate mechanism account (of the support) |

### 1.2 Comparison

**DT-36.** Owner: `docs/contract/13-actors.surface.md:225` (rule "Collect, release and advance",
rendered at `docs/REQUEST.md` `#contract-actors-phase-order`):

> After a failed active visit establish that actor's reap before any further activation; unresolved termination cancels the remaining schedule. Arrival or completion timeout cancels for exhausted execution allowance, and a wait error cancels for lost ownership.

Producer (`ActorScheduler.swift:472-480`): `stopActor`, then `quiescence != "reaped"` →
`unresolved_termination`; else timeout → `execution_allowance_exhausted`; else `wait_error` →
`ownership_lost`. `stopActor` skips grace and kill when the wait reported ECHILD
(`ActorSession.swift:574`, `CWorker.swift:1112`), so the process is recorded unreaped.
`ownership_lost` is reachable only when a wait fails with an errno other than ECHILD (or a third EINTR)
and a later wait in grace or after the kill reaps the child. Observation: both labels exist and are
ordered this way. Inference (mine): with the production wait (`WNOHANG`, valid options) the non-ECHILD
branch is unlikely outside an injected fault.

Readers and tests: `schedule.cancelled` is an open string (`docs/contract/33-actor_evidence.surface.md:544-546`,
"such as …"); Rust and Python bound its length only. The unit test asserts no label.
The support paragraph (`13-actors.surface.md:241-250`) credits a check for "cancellation conditions".

Which is right: the producer's order is the defensible one. An unreaped child is the stronger fact, and
reporting it first keeps the reply from naming a cause for a process whose ending is unknown. The statement
is true when read in order and omits that the two later reasons apply only after the reap is confirmed.

**DT-43.a.** Owner: `docs/contract/32-lifecycle.surface.md:659`:

> Resolve each question from the owning worker's acquired output, unique slot identities and submitted plan.

Producer: the ordinary form passes the plan; the actor form calls `resolveDisposition($0, plan: nil)`
(`ActorOrchestration.swift:307`), which takes the step list from the collected slots and marks each
`supported` (`CWorkerDisposition.swift:148-149`). The code comment at `CWorkerDisposition.swift:80-81`
says "production passes the plan", which is not true of the actor form. Both forms refuse an unsupported
attempt at admission (`ProbeRunner.swift:119-121`, `ActorPlan.swift:437`), so the two resolutions give the
same `attempt_support` for every admitted request. They differ only for a worker that rewrites a completed
slot's step identifier: plan-based resolution reports `slot: absent`, slot-based resolution lists the
rewritten identifier and the readers then reject the step count/identity join
(`controller/src/porcelain_admission.rs:516-520`, `tests/lib/extension_evidence.py:272-280`).
Which is right: the behavior is acceptable; the rule's wording and the code comment are inaccurate for the actor form.

**DT-43.b.** The field meaning already says "as an integer, or the observed termination-request object"
(`32-lifecycle.surface.md:794-796`). The subject page shows only the generated alternatives table
(`docs/contract/tree.py:1552-1557`). The comparable transport subject carries one authored sentence
(`docs/RESPONSE.md:836`: "The Rust enum is untagged: JSON contains the chosen alternative's fields directly").
Producer is right; the rendered subject is incomplete.

**DT-43.c.** The sentence is false for this surface. The identical sentence is in
`34-equipment.surface.md:1052` (also no gap node) and `33-actor_evidence.surface.md:880` (one gap node at `:840`).

### 1.3 Plausible treatments

| Claim | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| DT-36.a | Correct the account: state the precedence | `docs/contract/13-actors.surface.md:225` (generator input; `tests/lib/python.sh docs/generate_contract_stamps.py`) | no | public rule text changes; no behavior change | — (wording) |
| DT-36.a | Product change: report `ownership_lost` for ECHILD | `ActorScheduler.swift:473-480` | yes (signed rebuild) | would name a cause while the child's ending is unknown; not a real candidate under "No dishonest attribution" | — |
| DT-36.b | Assertion repair | `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift` | no | none for users | a scheduler that labels an unreaped actor `ownership_lost`; one that continues the schedule after a wait error on a reaped actor |
| DT-43.a | Correct the account | `32-lifecycle.surface.md:659`; comment `CWorkerDisposition.swift:80-81` | surface no; comment yes | none | — |
| DT-43.a | Product change: pass each actor's declared actions to the resolver | `CWorkerDisposition.swift:82`, `ActorOrchestration.swift:307`, `:273-286` | yes | identical replies for the shipped worker; `slot: absent` for a rewritten identifier | a disposition step whose identifier is not a declared action of that actor |
| DT-43.b | Correct the account: one sentence on the subject | `32-lifecycle.surface.md:810-816` | no | public prose changes (stamp changes) | — |
| DT-43.c | Correct the support text | `32-lifecycle.surface.md:1534` (and `34-equipment.surface.md:1052`) | no; owner metadata, no public payload change | none | — |

### 1.4 Recommended disposition

- **DT-36.a — correct the account in its owner.** Replace the two sentences with:
  "After a failed active visit establish that actor's reap before any further activation; unresolved
  termination cancels the remaining schedule, including after a wait error that leaves the actor unreaped.
  Once the reap is confirmed, an arrival or completion timeout cancels for exhausted execution allowance
  and a wait error cancels for lost ownership." Reason: the producer order is the truthful one.
- **DT-36.b — assertion repair** (new control, `runner_unit/pwrunner_core_unit_executable`):
  (1) in the ECHILD case add `expectEqual(result.cancelled, "unresolved_termination")`;
  (2) add a case whose injected wait fails once with a non-ECHILD, non-EINTR errno for the active child
  and then delegates: expect `quiescence == "reaped"`, `cancelled == "ownership_lost"`, the later
  visit not activated, the failed call retained in `output.waitErrors`, `pollStopReason == "wait_error"`.
  Also narrow nothing in the support text; after the test lands its "cancellation conditions" credit is earned.
- **DT-36.q — no change.**
- **DT-43.a — correct the account.** `free.condition` becomes: "Resolve each question from the owning
  worker's acquired output and unique slot identities. The ordinary form joins them to the submitted plan;
  the actor form takes each actor's steps from that actor's collected slot list, in which every slot is a
  supported operation. A not_reached or unpublished conclusion requires terminal collection where specified below."
  Correct the code comment with the next `runner/Sources` edit of this thread (W-B below). Further evidence
  would not change this: the two resolutions agree for every admitted request by the admission refusals cited.
- **DT-43.b — correct the account.** Add to the `claim_value` subject: "JSON carries the chosen
  alternative's value directly: an integer for an exit code, signal or item index, or the
  termination-request object. The alternative labels are not JSON keys."
- **DT-43.c — correct the support text** to "Imported public field definitions joined to
  producer/decoder/assessment meanings."

### 1.5 Resulting user duties

When `schedule.cancelled` is `unresolved_termination`, treat the failed actor as possibly still running
(`reaped: false`, `collection_basis: execution_may_continue`) and read its `wait_errors`; do not read the
absence of `ownership_lost` as retained ownership. DT-43: none.

### 1.6 Worklist

W-A items A1, A2, A3 and W-C item C1 in the consolidated worklist.

---

## Subject 2 — DT-46 / DT-120 / DT-121 / DT-129: cleanup-trigger derivation and time; actor stop-reason mapping

DT-120 narrows DT-46.d. DT-129 qualifies with the gate-reaped actor and the transfer phase.

### 2.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-46.a | The failure contract calls `cleanup_trigger` a fact "recorded at the exit-request store", one of three "facts, recorded where the host acts, not conclusions reconstructed from a final status"; RESPONSE places its recording when exit is requested; the cause table uses it as a witness. | both forms; `runner_subprocess.cleanup_trigger` / `actors[].subprocess.cleanup_trigger`; host; exit request | yes — `tests/FAILURE-PROPAGATION-CONTRACT.md:361-367`, `:469`, `:508-522` ("Witnessed trigger"); `docs/contract/32-lifecycle.surface.md:90-92`, `:869-871` | review: reading at `b8df8953`. Now: re-read | inaccurate mechanism account |
| DT-46.b | `requestExit` stores no trigger; `collectOutput` later computes `triggerForStop[pollStopReason] ?? pollStopReason`; the scheduler assigns the stop reason before `requestExit`; the two raw fields are projections of one stored reason. | host source | yes — `ActorSession.swift:558-562`, `:625-626`; `ActorScheduler.swift:545-551`, `:560-564`; `CWorker.swift:1271-1278` | source read; re-read | inaccurate mechanism account (same statement as DT-46.a) |
| DT-46.c | The Rust test `typed_host_cleanup_cause_requires_all_independent_observations` constructs both raw strings and their claims; it establishes projection conditions, not when the production trigger was captured. | Rust unit test; constructed typed record | yes — `controller/src/porcelain_admission.rs:2659-2730`; cited as support at `docs/contract/41-diagnostics.surface.md:1052` | test read; re-read | overstated coverage credit (narrow: the name and the "independent observations" wording) |
| DT-46.d | The derived expression is already in `0ed4ae7a` (2026-09-27). | history | yes for the expression (`git show 0ed4ae7a:…/CWorker.swift:938`); **narrowed by DT-120.d** | history; re-checked | accurate observation needing no change |
| DT-46.q | No executed case showed an incorrect trigger value or signal attribution; the discrepancy is the described provenance. | scope note | yes | — | accurate observation needing no change |
| DT-120.a | One stored string, `ActorSession.pollStopReason`, fills seven reply values (`poll_stop_reason`, `sentinel_wait.stop`, `cleanup_trigger`, the two claims, `runner_timeout`, diagnostics `stop_reason`/`termination_cause`). | both forms (`sentinel_wait.stop` ordinary only); reply and envelope | yes — `ActorSession.swift:742`, `:626`, `:756`; `CWorker.swift:1271`; `CWorkerDisposition.swift:116-127`, `:361`; `porcelain_admission.rs:1392-1419` | source read; re-read | accurate observation needing no change |
| DT-120.b | Every writer of `pollStopReason` runs before the matching `requestExit`; nothing writes between the store and `collectOutput`; the equality follows from code structure and nothing captures the value at the store. | host source | yes — writers: `ActorSession.swift:70`, `:411`; `CWorker.swift:1191`, `1192`, `1204`, `1205`, `1221`, `1232`, `1235`; `ActorScheduler.swift:549`, `:562` (and `:249`, which passes the session's own value) | source read; re-read | accurate observation needing no change |
| DT-120.c | Single-worker exits at `CWorker.swift:1247`, `1253`, `1259`, `1269` keep the default, so `deadline_expiry` is never actively recorded; under a clock fault exhaustion is counted in nominal sleeps (counterpart of DT-10). The actor form never keeps the default. | ordinary form; host loop | yes — same lines; `ActorScheduler.swift:549`, `:562` assign every spawned session | source read; re-read | accurate observation needing no change (DT-10 belongs to another row) |
| DT-120.d | History: the value was fixed at the store from `0ed4ae7a` until `c686a05f` (2026-11-03) and at final collection since; it was never independent of the stop reason. The contract's three claims; RESPONSE's wording was authored (`f6551bf9`) after the move; two code comments still carry the store wording; the actor cause fallback paragraph does not count the trigger as an independent observation. | history; comments; statements | yes — `git show c686a05f` removes the store-time lines and `ActorSession.swift` gains the expression; comments at `CWorker.swift:559-562` and `tests/lib/lifecycle_contract.py:105-106`; `41-diagnostics.surface.md:1014-1017` | history re-checked; comments re-read | inaccurate mechanism account (the two comments); otherwise accurate |
| DT-120.e | No statement or reader treats a pair of the copies as corroboration; Rust and the Python oracle check each claim against its own raw field; the table-agreement test compares tables, not reply values; the Swift resolver fixture builds its expected trigger with the production map. | readers and tests | yes — `porcelain_admission.rs:463-476`; `tests/lib/lifecycle_oracle.py:135-146`; `tests/lib/lifecycle_contract.py:752`, `:800-804`; `runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift:44`, `:527` | source/test read; re-read | accurate observation needing no change |
| DT-120.f | `termination_cause` requires a supported signal final status, exhausted grace and a successful kill request with the same signal; the trigger only selects the label; `owned_reap` is not an input. In the ordinary form the derivation changes no cause selection. | controller projection | yes — `porcelain_admission.rs:1379-1401` | source read; re-read | accurate observation needing no change |
| DT-120.g | Executed E4 (ordinary, `worker_timeout_ms: 50`, `worker_post_apply_hang_ms: 3000`): `runner_timeout`; stop `sentinel_deadline`, trigger `deadline_expiry`, grace exhausted, kill rc 0, reaped signal 9, cause `host_sentinel_deadline`. | ordinary form; public CLI; build `8b5de2b2` | recorded as stated (retained capture read); current behavior unverifiable by reading, source agrees | live then; capture available | accurate observation needing no change |
| DT-121.a | In the actor form every stop reason comes from the scheduler; only `done`, `wait_error` and the two transfer reasons are in `triggerForStop`; all others pass through as the trigger. | actor form; `actors[].subprocess.cleanup_trigger` and its claim | yes — `PWRunnerDisposition.swift:21-23`; reasons at `ActorScheduler.swift:249`, `266`, `275`, `370-458`, `562` | source read; re-read | inaccurate mechanism account in the statements that list six values (list disposition belongs to DT-30) |
| DT-121.b | `sentinel_deadline` cannot occur in the actor form, so the actor cause table's "Deadline expiry" row cannot be reached. | actor form; diagnostics rule | yes — `ActorScheduler.swift:549`, `:562`; row at `41-diagnostics.surface.md:972-977` | source read; re-read | consequential ambiguity |
| DT-121.c | Executed E5 (one unapplied actor, `worker_post_apply_hang_ms: 3000`): `runner_failed`; grace exhausted, SIGKILL rc 0, reaped signal 9 at `after_termination` with `departure_requested: true`; trigger and stop both `schedule_complete`; diagnostics `signaled`, `termination_cause: unknown`, `stop_reason: null`. | actor form; public CLI; build `8b5de2b2` | recorded as stated (retained capture read); source at HEAD produces the same values | live then; capture available | consequential ambiguity with reliance (see 2.2) |
| DT-121.d | `stop_reason` is null because the actor diagnostics rule projects only the six ordinary values; `died_before_completion` also projects null, `done` projects `done`. | controller projection | yes — `porcelain_admission.rs:1403-1419`; `41-diagnostics.surface.md:803-807`, `:932-943`; E1b, E2 captures | source read; captures read | accurate observation needing no change to the rule; account needs the qualification |
| DT-121.e | Both outcomes follow documented rules. Not stated anywhere: that the scheduler's routine reasons fall in the "unfamiliar" class, and that the actor deadline row cannot be reached; `cleanup_trigger` has no vocabulary block. | statements | yes — `32-lifecycle.surface.md:63-72`, `:90-92`; `41-diagnostics.surface.md:798-807`, `:1007-1017` | reading | consequential ambiguity |
| DT-121.q | Only `schedule_complete` was executed; `completion_timeout`, `arrival_timeout` and `setup_timeout` with an exhausted grace were not. | evidence limit | still true; not executed here | — | evidence limit, carried into 2.4 |
| DT-129.a | E3 actor A was reaped at the termination gate (`departure_requested: false`), yet `finish()` assigned `done` and stored an exit request, so its record shows `exit_requested: true`, `cleanup_trigger: completion`, `grace_end: not_entered`. Each value is accurate; the combination needs joining. | actor form; reply; host; schedule end | yes — `ActorScheduler.swift:560-565`; `ActorSession.swift:558-562`, `:574`; E3 capture | live then (capture read); source re-read | accurate observation needing no change; a limit to state |
| DT-129.b | A stop-reason copy taken before the store is published only in the single-worker form (`sentinel_wait.stop`); the actor form's `ActorSessionRecord.stopReason` is internal, is not set by `finish()`, and has no production reader. | both forms | yes — `CWorker.swift:1271`; `ActorScheduler.swift:69`, `:548`; readers only at `ActorSchedulerTests.swift:572`, `:607`; E6 outputs show `stop_reason: null` for an actor stopped by `finish()` | source read; driver output read | accurate observation needing no change |
| DT-129.c | A transfer's published `phase_id` is the declared delivery phase; the host's servicing phase is internal; by source the two match. | actor form; `transfers[].phase_id` | partly — `ActorOrchestration.swift:453`; `AuthorityCustody.swift:427-433`. The match is not an invariant: a request left pending when its visit ends (worker-side timeout or clock fault, `pw_probe_runner.c:804-819`, `:902`) is serviced during a later visit of the same source actor with that visit's phase | source read; re-read | accurate observation needing no change; the "match" is narrower than stated |
| DT-129.d | `ActorReplyTests` 112–133 asserts the interrupted issue's `unresolved` token and event, not host acceptance; it runs production equipment binding, live inspection, Swift reply validation and encoding, and skips the XPC entry, `runActors` and validator collection. | runner unit test | yes — `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift:27-35`, `:113-134`; `ReplyFailureTests.swift:110-113` | test read; re-read | accurate observation needing no change (coverage item under Subject 4) |

### 2.2 Comparison

**Stated obligation.** `tests/FAILURE-PROPAGATION-CONTRACT.md:361-367`:

> Three host observations join `runner_subprocess` … They are facts, recorded where the host acts, not conclusions reconstructed from a final status.
> `cleanup_trigger` — Host string recorded at the exit-request store: `deadline_expiry`, `completion`, `child_reaped`, `poll_wait_error` `policy_transfer_error` or `policy_transfer_timeout`. It names why exit was requested; today it corresponds one-to-one with `poll_stop_reason`, and both are retained.

`docs/contract/32-lifecycle.surface.md:92`: "Host fact recorded when it requests exit: deadline_expiry, completion, child_reaped, poll_wait_error, policy_transfer_error or policy_transfer_timeout."
`:871`: "Recorded reason for requesting exit". Witness table, `FAILURE-PROPAGATION-CONTRACT.md:469`:
"direct host observation of why exit was requested". Cause labels, `:508-510`: "`termination_cause` projects
host cleanup that the account witnesses end to end. A label requires all of: `cleanup_trigger` supported with
the trigger in the table …". Actor cause rule, `41-diagnostics.surface.md:798-801`: "otherwise `unknown` unless
the validated host-cleanup chain supplies a named cause below".

**Producer.** The trigger is `PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason`, computed in
`collectOutput` (`ActorSession.swift:626`) after grace, kill and reap. The stop reason it reads was last
written before the exit-request store on every path, so the value equals what a store-time capture would
have given. It is the host's own stored reason passed through a six-entry table
(`PWRunnerDisposition.swift:21-23`); it is not read from a final status and it is not a second observation.
In the actor form the scheduler's reasons are: `done`, `schedule_complete` (`ActorScheduler.swift:562`);
visit end reasons `ended_before_arrival`, `died_before_arrival`, `wait_error`, `arrival_timeout`,
`protocol_violation`, `died_before_collection`, `died_during_collection`, `completion_timeout`,
`release_withheld`, `ended_before_completion`, `died_before_completion` (`:370-458`); setup statuses
`setup_failed`, `authority_setup_failed`, `exited_before_setup`, `setup_timeout` (`:266`, `:275`); and the
two policy-transfer reasons (`:249`). Four of these are table keys.

**Readers.** Rust (`porcelain_admission.rs:463-476`) and the Python oracle (`lifecycle_oracle.py:135-146`)
compare each claim with its own raw field. Neither checks the trigger against the stop reason. The cause
is selected by the trigger answer among five values, otherwise `unknown` (`porcelain_admission.rs:1392-1399`;
`lifecycle_oracle.py:221-226`); `stop_reason` projects only six values (`porcelain_admission.rs:1403-1419`).
The Rust cause test includes `("future_trigger", "future_stop", "unknown")`, so `unknown` for an unlisted
trigger is asserted behavior.

**What is established and what is inferred.**
- Observed (retained captures): E4 ordinary host kill → `host_sentinel_deadline`; E5 actor host kill with the
  same three observations (request rc 0, exhausted grace, reaped signal 9) → `unknown`, `stop_reason: null`.
- By source: any actor host kill other than after `done`, `wait_error` or a transfer failure projects `unknown`.
- Not observed: actor allowance expiry followed by a kill (DT-121.q).
- Reliance: the registered ordinary case `witness_contract/worker_attempt_in_flight_at_deadline` fails a
  reply whose cause is `unknown` beside the host's own kill record
  (`tests/suites/witness_contract/check_attempt_in_flight.py:263-272`, "discards the host's own termination
  record"). No registered case applies that position to the actor form. The frozen guide tells readers that
  endings "remain `unknown` until their supporting chain establishes one of these causes" and that "Actor
  causes live in their actor entries" (`docs/PolicyWitness.md:1374-1380`); it cannot be edited.
- The statements are not symmetric in their error: the one-to-one dependence on the stop reason is stated
  openly, and the actor cause paragraph does not count the trigger as an independent observation. What is
  wrong is the recording time, the words "host observation"/"direct host observation"/"Witnessed trigger",
  and the six-value lists read against actor replies.

**DT-129.a.** `exit_requested`'s meaning (`32-lifecycle.surface.md:74-76`: "Whether the host performed the
release store asking the worker to exit. Worker receipt is a separate observation") is true of a store made
after the child was reaped. Nothing beside it says the store can follow the ending.

### 2.3 Plausible treatments

| # | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| (i) | Product change, host table: add `schedule_complete`, `ended_before_arrival`, `ended_before_completion` → `completion` to `triggerForStop`. These are the actor reasons whose documented trigger has the same literal meaning (exit requested because the scheduled work, or the worker, finished). | `runner/Sources/PWRunnerCore/PWRunnerDisposition.swift:21-23`; mirror `tests/lib/lifecycle_contract.py:107-109`, `:752`; `DispositionResolverTests.swift:527` passes unchanged once both tables agree | **yes**: signed rebuild, and worker-identity regeneration (`docs/generate_worker_identity.py` hashes all of `runner/Sources`) | actor replies: `cleanup_trigger` becomes `completion` where it is `schedule_complete` or `ended_before_*` today; an actor killed by the host after exhausted grace at schedule end projects `host_exit_grace_exhausted`. `poll_stop_reason` and the stop claim keep the scheduler's string. A consumer comparing the actor trigger with the stop reason for equality would see a difference | an actor reply carrying request rc 0, exhausted grace and a reaped signal equal to the requested one, with `termination_cause: unknown`, for a `schedule_complete` stop; and, in the other direction, a named cause for an actor that ended on its own signal (E1b/E2 shape: `grace_end: not_entered`, no request) |
| (i-b) | Same effect at the controller: recognize the actor triggers in the cause table | `controller/src/porcelain_admission.rs:1392-1399`, `PWRunnerDisposition.swift:32-34`, `lifecycle_contract.py:292-295`, `41-diagnostics.surface.md:972-1012` | yes (both components) | raw trigger stays equal to the stop reason; three tables change instead of one | same |
| (i-c) | Name actor allowance expiry (`arrival_timeout`, `completion_timeout`, `setup_timeout`) | host table plus a **new** cause label in Rust, Swift, Python and both surfaces | yes | new public value. `host_sentinel_deadline` cannot be reused: `docs/LIMITS.md:127` assigns the sentinel wait to ordinary execution and says actor execution uses `actor_execution_allowance` | an actor allowance kill labelled with the ordinary worker's allowance |
| (ii) | Correct the account: the trigger is derived from the stop reason at final collection; list the map; say unmapped actor reasons pass through, which actor kills stay `unknown`, and that the actor deadline row is not reached | `docs/contract/32-lifecycle.surface.md:90-92`, `:869-871`; `docs/contract/41-diagnostics.surface.md:798-807`, `:1014-1017`, `:1055`; `tests/FAILURE-PROPAGATION-CONTRACT.md:132`, `:361-367`, `:468-469`, `:508-522` (none in a shared region); comments `CWorker.swift:559-562`, `tests/lib/lifecycle_contract.py:105-106` | surfaces and contract no; the Swift comment yes | public meanings narrow; no behavior change | — (wording); see the derivation check below |
| (ii-check) | Assertion repair: make the independent oracle check the derivation it documents | `tests/lib/lifecycle_oracle.py` (near `:135-146`), controls in `tests/suites/blackbox_e2e/disposition_controls.py` | no | none for users | a reply whose `cleanup_trigger` is not the table image of its `poll_stop_reason` (for example `completion` beside `sentinel_deadline`), which every reader accepts today |
| (iii) | Retain everything | — | no | leaves "recorded at the exit-request store" false and the six-value lists false for actor replies | — |
| DT-129.a | State the limit beside `exit_requested` | `32-lifecycle.surface.md:74-76` | no | none | — |

Treatment (iii) is not available for DT-46/DT-120: a statement of recording time that the code contradicts stays false.

### 2.4 Recommended disposition

- **DT-46.a, DT-46.b, DT-120.b, DT-120.d — correct the account (ii).** Proposed owner text:
  - `32-lifecycle.surface.md` `cleanup_trigger`: "Why the host requested exit, derived at final collection
    from the stop reason it held when it stored the request: sentinel_deadline gives deadline_expiry; done
    gives completion; child_reaped gives child_reaped; wait_error gives poll_wait_error; policy_write_error
    and policy_transfer_deadline give policy_transfer_error and policy_transfer_timeout. Any other stop
    reason is carried unchanged. The value restates poll_stop_reason and is not a second observation."
    (With (i) adopted, add "and, in the actor form, schedule_complete, ended_before_arrival and
    ended_before_completion" after "done".) Leave the vocabulary-block question to DT-30's disposition;
    this wording is compatible with an open, illustrative list.
  - `32-lifecycle.surface.md` run question: "Reason for requesting exit, copied from the worker's
    cleanup_trigger; inapplicable when exit_requested is false."
  - `FAILURE-PROPAGATION-CONTRACT.md:361-367`: "Three host values join … `grace_end` and `collection_basis`
    are recorded where the host acts. `cleanup_trigger` is derived from the stop reason the host held when
    it stored the exit request. None is reconstructed from a final status." Row: "Host string derived at
    final collection from `poll_stop_reason` through a fixed table (…); a reason outside the table is carried
    unchanged. It names why exit was requested and is not an observation independent of `poll_stop_reason`;
    both are retained."
  - `:469`: witness "the stop reason the host held when it requested exit, through the fixed table".
  - `:508-522`: column "Trigger"; add "The trigger selects the label and restates the stop reason. The
    independent observations are the request result, the exhausted grace and the owned final status."
  - Comments: `lifecycle_contract.py:105-106` now; `CWorker.swift:559-562` with W-B.
  Reason: the value is truthful and reproducible; only its described provenance is wrong. Further
  evidence would not change this, because the writers and the single derivation site are closed by reading.
- **DT-46.c — narrow the credit.** Add to the support `limits` at `41-diagnostics.surface.md:1055`: "The
  test constructs each trigger and stop pair; it does not exercise the host's derivation of the trigger."
  Do not rename the Rust test (a `controller/src` edit for a name).
- **DT-46.d, DT-46.q, DT-120.a, DT-120.c, DT-120.e, DT-120.f, DT-120.g — no change.** DT-120.e's gap is closed by (ii-check).
- **(ii-check) — adopt.** Land it first with the current table, run it against the existing app
  (it passes: pass-through is `table.get(stop, stop)`), then change table and product together.
- **DT-121.a, DT-121.c, DT-121.e — product change (i), with (ii).** Reason: the reply carries the same
  three independent observations the ordinary form labels, the suite already treats `unknown` beside the
  host's own kill record as a defect in the ordinary form, and the mapping uses existing documented values
  in their literal sense. It is one table entry set in one file; (i-b) reaches the same projection with
  more surface. Discriminating check: extend `witness_contract/actor_compositions`
  (`check_actor_compositions.py:346-360` already builds the two-actor `worker_post_apply_hang_ms`
  specimen) with a hang longer than the 1,000 ms exit grace and assert, for the killed actor,
  `poll_stop_reason: schedule_complete`, `done_observed: false`, `cleanup_trigger: completion`,
  `grace_end: exhausted`, `termination_request {signal 9, rc 0}`, `owned_reap.departure_requested: true`,
  `termination_cause: host_exit_grace_exhausted`; keep the existing 500 ms row (clean exit, cause null);
  assert `unknown` with `grace_end: not_entered` for a `worker_kill_before_publish_slot` actor.
  Fallback if (i) is declined: (ii) alone, with the accepted limit below extended to `schedule_complete`.
- **DT-121.b — correct the account.** Keep the row (it is a true rule over a carried record) and add to the
  prose at `41-diagnostics.surface.md:1014-1017`: "The actor scheduler never records sentinel_deadline, so
  no actor reply selects the deadline case."
- **DT-121.d — correct the account.** Add to the actor `stop_reason` field (`:803-807`): "The scheduler's own
  reasons, such as schedule_complete or a visit end reason, are outside that set and project null; the
  actor's subprocess record keeps them in poll_stop_reason."
- **DT-121.q and allowance expiry — reasoned retention.** Accepted limit, to stand in
  `41-diagnostics.surface.md` after the actor cause table and in `FAILURE-PROPAGATION-CONTRACT.md` after
  the label table: "An actor stopped for an arrival, completion or setup timeout, a protocol violation, a
  withheld release or a failed setup keeps the scheduler's reason as its trigger. Its cause stays `unknown`
  even when the request result, exhausted grace and final status are all carried; read them in that actor's
  subprocess record." Reason: no existing label names these truthfully, a new label is a new public value,
  and there is no executed actor-timeout observation. This is a present decision to retain, not a referral;
  (i-c) remains available and needs a label name.
- **DT-129.a — reasoned retention with the limit stated.** Add to `exit_requested`: "The host also performs
  this store for a child it has already reaped; `grace_end: not_entered` and, for an actor,
  `owned_reap.departure_requested: false` then record that the ending preceded the request."
- **DT-129.b — no change.** The internal copy has test readers only.
- **DT-129.c — no change.** The owning statement already says "Phase in which this transfer action was
  declared" (`docs/contract/14-extensions.surface.md:635-637`), which is true in both cases.
- **DT-129.d — see Subject 4 (DT-62.d).**

### 2.5 Resulting user duties

- Do not count `cleanup_trigger` as an observation beyond `poll_stop_reason`.
- In an actor entry, `signaled` with `termination_cause: unknown` does not show that the host made no kill:
  read `termination_request`, `grace_end` and `owned_reap.departure_requested`/`stage`. (After (i) this
  duty remains for the timeout, violation and failed-setup stops.)
- In an actor entry, `stop_reason: null` is not a missing stop reason; read `actors[].subprocess.poll_stop_reason`.
- `exit_requested: true` with `cleanup_trigger: completion` does not show that the request preceded the
  ending.

### 2.6 Worklist

W-A items A4–A9, W-C items C2–C3, W-B items B1–B3, W-D item D1.

---

## Subject 3 — DT-59 / DT-60 / DT-61 / DT-133: self-transfer visit timing; raw setup association; decoder prerequisites; scheduler authority gate

The private header word (`authority_status`, `authority_detail`) and the public record (`authority_setup.workers[]`)
are kept apart throughout.

### 3.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-59.a | EXTENSIONS says the recipient "consumes only in a later visit of its own"; the authored custody rule describes self-transfer servicing inside the sender's wait; REQUEST requires prior production in action order, not a different visit. | actor form; request admission and worker execution; statement in a shared region | yes — `docs/EXTENSIONS.md:79-81` (shared region, copied to the frozen guide at `docs/PolicyWitness.md:489`); `docs/contract/14-extensions.surface.md:391`; `:193-230` | reading; re-read | inaccurate mechanism account |
| DT-59.b | Admission accumulates resources while walking actions and admits a self-transfer followed by consumption in one phase; the worker services inbound work inside its exchange wait and then permits consumption of settled bytes; the unit test places `a_consume` in a later visit and does not establish "only". | host admission; C worker; unit test | yes — `ActorPlan.swift:451-500`; `pw_probe_runner.c:802-824`, `:908-923`; `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift:421-468`. The CLI composition also consumes in a later phase (`tests/suites/witness_contract/check_actor_compositions.py:33-50`) | source/test read; re-read | accurate observation needing no change |
| DT-59.c | Executed: one unapplied actor, one phase: issue, transfer to itself, consume, `read_fresh`, release → exit 0, `finished`; transfer `delivered`, consume `returned/0`; consumer and oracle `[]`. | actor form; public CLI; build `8b5de2b2` | unverifiable by reading as an execution (scratch absent, no retained capture); source admits and executes this order | live then; **not available** | accurate observation (source agrees) |
| DT-59.q | The later-visit prose dates from `49a14688` and is in `v0.3.5`; the run establishes admitted same-visit self-consumption, not that consuming changed the unapplied actor's access. | scope | yes | — | accurate observation needing no change |
| DT-60.a | The equipment rule says to validate the raw actor/required association before projecting an observed decision and primary operation. | host decoder; statement | yes — `docs/contract/34-equipment.surface.md:890-891` | reading | contradicted explicit commitment (at the decoder; state unreachable with the shipped worker) |
| DT-60.b | Constructed buffer with raw actor 7 against argument 0: decoder returns `publication=observed disposition=ready` with `errors=["setup_association_mismatch"]`; the mismatching raw value is not retained. | constructed region through the copied production decoder | by source yes — `AuthoritySetupRuntime.swift:66` inserts the error; `:95-102` project regardless; scope is built from the arguments at `:56` | executed then on a temporary build; **not available**; source re-read | contradicted explicit commitment (same) |
| DT-60.c | This does not establish activation of a mismatched worker: the scheduler returns setup failure on integrity errors, reporting flags publication integrity, and the worker's header checks reject an inconsistent association before setup. | host scheduler; Swift reporting; C worker | yes — `ActorScheduler.swift:287`; `PWRunnerAuthoritySetup.swift:151`; `pw_probe_runner.c:1364-1373`. **Addition from this pass:** both JSON readers also reject a `ready` or `not_required` decision beside integrity errors (`controller/src/porcelain_actor.rs:181-190`; `tests/lib/actor_evidence.py:44`; probe result above) | source read; one constructed reader probe now | accurate observation needing no change |
| DT-60.d | The cited test supplies matching words and asserts cell retention and `invalid_setup_cell`, not mismatched-decision handling; the behavior dates to `bc3abe2f`. | unit test | yes — `ActorAuthorityTests.swift:155-178`; no test names `setup_association_mismatch`, `invalid_setup_decision` or `setup_primary_unpublished` | test read; grep | accurate observation needing no change (the support's limits already confine the test's scope, `34-equipment.surface.md:926-928`) |
| DT-61.a | Prepare-before-use requires core-limit success and required mapping/validation before `ready`; the equipment condition requires observed `ready` to imply `required: true`. | statements | yes — `14-extensions.surface.md:358`; `34-equipment.surface.md:912-917` | reading | accurate observation needing no change |
| DT-61.b | Constructed buffer with matching association, decision `ready` and no cells: decoder returns `ready` with `errors=[]`. The decoder checks an optional primary against a failed cell and requires none of ready's cells. | constructed region; host decoder | by source yes — `AuthoritySetupRuntime.swift:95-102` | executed then; not available; source re-read | unsupported inference (that a decoded `ready` rests on host-checked cells) |
| DT-61.c | On a real two-actor body, removing `core_limit`, failing it, setting `required:false`, or emptying `host.regions` (each with `ready` kept) leaves `actor_evidence`, `extension_evidence`, `consumer._validate_reply` and the oracle at `[]`; the full consumer rejects only because the captured wire bytes were left unchanged. | constructed JSON to the Python body readers | yes — reproduced now for `actor_evidence` and `extension_evidence` on the retained E3 body (probe above) | constructed then (not available) and now | unsupported inference (that reader acceptance covers readiness) |
| DT-61.d | Python, Swift and Rust check terminal applicability without `ready ⇒ required` or the prerequisite prefix; the Swift/Rust statements are source reading; the fixture's named assertions concern other relationships; no production reachability is claimed. | three readers | yes — `tests/lib/actor_evidence.py:149-159`; `PWRunnerAuthoritySetup.swift:196-205`; `controller/src/porcelain_actor.rs:427-466` | source read; re-read | accurate observation needing no change |
| DT-133.a | The scheduler admits setup on four conditions; for a launched actor under an authority plan the gate reduces to header status == MAPPED; MAPPED is written by the same C decision block as the disposition, is absent from the wire schema, and appears only in the classifier's error text. | host scheduler; private header word | yes — `ActorScheduler.swift:258-266`, `:284-302`; `ActorSession.swift:490-491`; `pw_probe_runner.c:748-753`; `grep -c authority_status docs/porcelain.json` is 0; text at `ActorScheduler.swift:264`, `CWorker.swift:748` | source read; re-read | accurate observation needing no change |
| DT-133.b | Seam frames with `ready` and a missing or failed `core_limit`, or `required:false`, beside `setup_status: applied` are `finished`, Rust `valid`, and `[]` from the Python readers; Swift reporting was not run on them. | constructed frames with a constructed contract binding, through Rust decode/admission/assembly | recorded as stated (retained `analysis.txt` rows 16–18 read) | constructed then; available | accurate observation needing no change |
| DT-133.c | From `ready`, `setup_status: applied` and a missing or failed prerequisite cell, a reader cannot tell a lost cell from an activation on a different fact; only the C program order joins the activation decision to the retained cells. | final-reply reader | yes by source | reasoning from source | unsupported inference |

The DT-61 acceptance trace (review lines 7928–8005) is the source of DT-133's "step 3" and "step 5"
references and of the three seam rows; it was read and agrees with HEAD.

### 3.2 Comparison

**DT-59.** `docs/EXTENSIONS.md:79-81`:

> The recipient accepts a delivery while parked between its visits; it consumes only in a later visit of its own, after that phase's queries were collected and the host released it.

For a recipient other than the sender this follows from serial scheduling. For a self-transfer the host
copies into the sender's own inbound slot while the sender is inside `wait_exchange`, which calls
`service_inbound_once` (`pw_probe_runner.c:821`); the sender acknowledges, the host compares and settles
(`AuthorityCustody.swift:579-590`), and the next action may consume. The same document says so two
paragraphs earlier ("a delivery the recipient accepts while parked or during its own wait", `:45`;
"a self-transfer cannot consume or erase bytes while the host compares them", `:76-77`). No admission rule
separates the visits. Both registered placements (unit and CLI) put the self-consume in a later visit, so
same-visit consumption has no registered execution.

**DT-60.** `34-equipment.surface.md:890`:

> For an observed decision, validate its raw actor/required association before projecting the decision and its primary operation.

Producer: compares, records the error, projects anyway under the session's own index and flag. Reachability:
the host writes both words before spawn (`ActorSession.swift:142-143`); the shipped worker never writes them
and refuses to start when they disagree with its header (`pw_probe_runner.c:1364-1373`). A shipped host and
worker cannot reach the state. A worker executable substituted through `_test_overrides.worker_executable_path`
or `actor_equipment_executable_paths`, or a constructed buffer, can. Downstream of the decoder every
component declines to use the decision: scheduler (`setup_failed`), classifier
(`CWorkerDisposition.swift:344-347`), Swift reporting (`authority_publication_integrity`), Rust and Python
("invalid setup cells cannot establish readiness"). The record still says `ready` beside the error.

**DT-61 / DT-133.** Producer chain: the worker publishes cells 0–10 and then the decision
(`pw_probe_runner.c:690-753`); the retained E3 scope shows all twelve cells with `core_limit succeeded`,
`descriptor_presence accepted`, `fstat succeeded`, `object_size accepted`, `mmap succeeded`,
`descriptor_close succeeded`, `header_binding accepted`. The decoder checks `ready` against the `required`
argument only (`AuthoritySetupRuntime.swift:98`). The scheduler requires no integrity error, a non-terminal
decision, the worker's setup word, and the private header word. For a required actor an observed
non-terminal decision can only be `ready` (the decoder rejects `not_required` there), so
"usable and required ⇒ observed `ready` without integrity errors" holds for every reply of the shipped host
without the header word. What nothing checks is "`ready` ⇒ its cells succeeded". Reachability of a `ready`
reply without those cells: not with the shipped worker (cells precede the decision's release store and the
decoder reads the decision first); only a constructed reply or a substituted worker.

Readers: all three check `terminal_required_failure ⇒ required ∧ primary`; none checks `ready ⇒ required`,
the cells, or the host region scope.

### 3.3 Plausible treatments

| Claim | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| DT-59 | Correct the account in the shared-region owner | `docs/EXTENSIONS.md:79-81` (correction with the needed scope; no added workflow); `tests/lib/python.sh docs/generate_limits.py --check` verifies owner and frozen guide bytes | no | owner and frozen guide copy diverge, as the plan allows | — |
| DT-59 | Coverage: register a same-visit self-transfer and consume | `tests/suites/witness_contract/check_actor_compositions.py` | no | none | a returned self-consume whose delivery is not `delivered`; a refusal of the admitted request |
| DT-59 | Product change: refuse same-phase self-consume at admission | `ActorPlan.swift:479-490` | yes | refuses requests admitted today; no evidentiary gain (a phase's predictions already precede all of its actions for every recipient) | — (not recommended) |
| DT-60 | Correct the account: say the decoder records the mismatch beside the projected decision | `34-equipment.surface.md:890-899` | no | statement becomes true; behavior unchanged | a decoder that returns a mismatched block's decision with **no** integrity error |
| DT-60 | Product change: withhold the decision on a mismatch (`publication: not_observed`, error kept, valid cells kept) | `AuthoritySetupRuntime.swift:95-102` | yes | no change on any shipped path; aligns with the `invalid_setup_decision` branch | a decoder that returns `observed`/`ready` for a block whose raw words differ from the session's |
| DT-61.b | Product change: decoder requires ready's cells, else an integrity error | same function | yes | no change on any shipped path; couples the decoder to the worker's setup sequence | `ready` with no integrity error when `core_limit` is absent or failed |
| DT-61.c/d, DT-133.c | Reader rule in the independent consumer | `tests/lib/actor_evidence.py:149-159` plus an actor cross-check; controls in `tests/suites/blackbox_e2e/extension_controls.py` | no | consumer rejects the four constructed bodies | the three `f61-*` shapes and emptied host regions accepted |
| DT-61.c/d | Mirror the rule in the Rust controller | `controller/src/porcelain_actor.rs:427-466`; shared corpus `tests/fixtures/contract/actor_evidence.json` | yes | controller reports `invalid` for those frames | same |
| DT-133.a | State the limit: the header word is private | `34-equipment.surface.md` after `:917` | no | none | — |
| DT-133.a | Product change: publish the header word | record, three readers, goldens | yes | a second encoding of one decision becomes public; not a real candidate | — |

### 3.4 Recommended disposition

- **DT-59.a — correct the account in `docs/EXTENSIONS.md`.** "A recipient other than the sender accepts a
  delivery while parked between its visits and consumes it in a later visit of its own. A self-transfer is
  accepted inside the sender's own wait and can be consumed later in that same visit. Either way
  consumption follows that phase's query collection and the host's release." Reason: the producer and the
  authored custody rule agree; "only" is the outlier.
- **DT-59.b, DT-59.c — coverage repair.** The execution behind DT-59.c is gone, so the corrected sentence
  needs a registered observation. Add to `witness_contract/actor_compositions` a one-actor, one-phase
  composition (issue; transfer to self; consume; `read_fresh`; release) asserting `finished`, the transfer
  row `delivered` with `source_actor_id == recipient_actor_id`, the consume event `returned` with the same
  `phase_id` as the transfer, and `[]` from consumer and oracle. It runs against the existing app.
- **DT-59.q — no change.**
- **DT-60.a, DT-60.b — correct the account.** `free.effect`: "Retain independently valid operation cells
  even when the decision is absent. For an observed decision, compare its raw actor/required association
  with the session's and record `setup_association_mismatch` on a difference; the decision and its primary
  operation are still projected, under the session's own actor index and required flag." Add to the prose
  at `:894-899`: "A scope carrying integrity errors supports no readiness: the scheduler treats that
  actor's setup as failed, and the controller reports a ready or not_required decision beside integrity
  errors as invalid." Update the `retained_free` reason ("checked during projection").
  Reason: every consumer of the decision already refuses it, so withholding it at the decoder would change
  no outcome; the smaller treatment makes the statement true. What the decoder should do in the
  unreachable case: keep recording the error; projecting or withholding the decision is equivalent for
  every reader, and withholding becomes worthwhile only if the decoder is edited for another reason.
  Discriminating check (new, `runner_unit/pwrunner_core_unit_executable`): extend the constructed-buffer
  test at `ActorAuthorityTests.swift:155-178` with a published `ready` decision and raw actor ≠ argument,
  then raw required ≠ argument; require `integrity_errors` to contain `setup_association_mismatch` in both.
- **DT-60.c, DT-60.d — no change.**
- **DT-61.a, DT-61.d — no change.**
- **DT-61.b — reasoned retention.** Accepted limit, to stand in `34-equipment.surface.md` after the
  `decision` condition: "The worker publishes ready only after its core-limit, descriptor, size, mapping,
  close and header-binding cells succeeded. The host decoder checks the decision against `required` and
  does not re-check those cells." Reason: no statement is false and the state needs a non-shipped worker.
  What the decoder should do if it is changed: treat a `ready` decision without those successful cells as
  an integrity error, by analogy with `setup_primary_unpublished`; that is the stronger alternative and is
  not required.
- **DT-61.c, DT-133.c — add the reader rule to the independent consumer.** In `actor_evidence._setup`:
  (a) `ready` requires `required is True`, no `primary_operation`, and cells 3, 4, 5, 7, 8, 9, 10 present
  as succeeded/accepted/succeeded/accepted/succeeded/succeeded/accepted; (b) `not_required` requires
  `required is False`; (c) a `ready` worker scope requires that actor's host region scope to be `ready`;
  (d) an actor whose `setup_status` is `applied` or `unapplied_declared` and whose scope is `required`
  must have an observed `ready` scope without integrity errors. Controls (Python-only rows beside the
  corpus loop in `extension_controls.py`, **not** in `actor_evidence.json`, which the Rust test
  `typed_setup_equipment_application_and_gate_corpus` also reads): the four DT-61.c edits rejected; the
  unchanged body, a `terminal_required_failure` scope with a partial prefix, and a `not_observed` scope
  with cells accepted. The rule rejects none of the fixtures and captures listed under "Evidence used".
  Before landing, also run it over the Swift-built frames of `tests/suites/runner_unit/reader_corpus.py`.
  The Rust controller is left unchanged; that is stated as a limit under DT-133.
- **DT-133.a — reasoned retention with the limit stated**, same place: "Before a required actor's setup
  counts as usable the scheduler also requires the worker's private header status word to report the
  mapped region. That word is not a reply field; a refusal on it is reported as setup_failed and its value
  appears only in the run's error text. The controller relates an actor's application to a terminal scope
  only and does not re-derive ready from its cells."
- **DT-133.b — no change;** after the consumer rule those frames are rejected by `actor_evidence` and still `valid` for Rust.

### 3.5 Resulting user duties

- Do not rely on visit boundaries to keep a sender from consuming its own delivery; order the actions.
- Read no readiness from a scope that carries `integrity_errors`, whatever its `disposition`.
- `ready` is the worker's decision. Its support is the scope's own cells; the controller's `valid` does not
  check them, and the header word the scheduler consulted is not in the reply.

### 3.6 Worklist

W-A items A10–A12, W-C items C4–C6.

---

## Subject 4 — DT-62 / DT-65 / DT-122 / DT-123: host custody acceptance, publication gating, delivery relationships, discarded worker custody observation

Host observer: `CustodyObservation` and `TransferObservation` (`AuthorityCustody.swift:93-124`).
Worker observer: the issue slot's `ext_custody_status` (`pw_probe_runner_abi.h:164-167`). They are separate.

### 4.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-62.a | The custody rule says the native return and host custody acceptance are reported independently; the token-status definition makes a missing issue publication unresolved, and assembly follows the latter even when the host accepted custody. | actor form; `resources.tokens[].status`; host; assembly | yes — `docs/contract/14-extensions.surface.md:377` (rendered `docs/ARCHITECTURE.md:358`), `:826-828`; `ActorOrchestration.swift:462-470` | reading; re-read | contradicted explicit commitment (when the issue slot is unpublished) |
| DT-62.b | Executed: issue-only actor with `worker_kill_before_publish_slot: 0` → exit 1, `runner_failed`, signal 9 reaped; issue event `call_boundary_observed: true`, `result_published: false`, `unresolved`; token `unresolved`, no length; host custody scope shows mmap, `final_erase` 16,384 and munmap, no acceptance. | public CLI; build `8b5de2b2` | recorded as stated: original scratch absent; the rebuilt run E1b is retained and shows the same fields | live then; E1b capture available | accurate observation needing no change |
| DT-62.c | A copied-package driver on the same request printed `custody=[accepted, 216, true]` beside an unresolved event and token. | internal driver (not a public response); real worker | unverifiable by reading as an execution (output not retained; not rerun by the later pass). By source the seam fires after the acknowledgement wait returns (`pw_probe_runner.c:880-883`, `:1094`) | internal then; **not available** | accurate observation (source agrees) |
| DT-62.d | The seam kills after the attempt returns and before `completed`; `AuthorityCustody` retains the accepted length; `collectOutput` withholds unpublished slot payloads; assembly chooses unresolved before consulting custody; delivery assembly keeps host observations without source publication; `ActorReplyTests` asserts the two cases separately and no host acceptance; present in `v0.3.5`; it does not justify publishing an unobserved native return. | source and unit tests | yes — `pw_probe_runner.c:1090-1096`; `AuthorityCustody.swift:456-502`; `ActorSession.swift:645-655`; `ActorOrchestration.swift:462-488`; `ActorReplyTests.swift:113-157` | source/test read; re-read | accurate observation needing no change (coverage item) |
| DT-65.a | The token definition requires accepted custody for `issued` and its absence for `issued_uncustodied`; the failure contract adds that the latter token's transfers read `custody_unavailable`; delivered transfers require held custody, copying, equal bytes and recipient acknowledgement. | statements | yes — `14-extensions.surface.md:828`, `:704-721`; `tests/FAILURE-PROPAGATION-CONTRACT.md:280` (shared region), `:263-264` | reading | accurate observation needing no change |
| DT-65.b | Changing only `tokens[0].status` to `issued_uncustodied` beside a delivered transfer with `custody_status: held` leaves `actor_evidence`, `extension_evidence`, `consumer._validate_reply` and the oracle at `[]`; the full consumer rejects only for the unchanged wire bytes. | constructed JSON to Python body readers | yes — reproduced now on the retained E3 body for `actor_evidence` and `extension_evidence` | constructed then (not available) and now | unsupported inference (that reader acceptance covers the custody relationship) |
| DT-65.c | Python accepts either issuance status for a completed non-null event without joining custody to transfers; Swift and Rust have the same alternatives; their delivered-transfer checks look at the transfer alone. | three readers | yes — `tests/lib/extension_evidence.py:348-351`, `:299-302`; `PWRunnerReply.swift:607-609`, `:588-591`; `controller/src/porcelain_actor.rs:1562-1570`, `:1525-1534` | source read; re-read | accurate observation needing no change |
| DT-65.q | Production assembly derives the status from the host's accepted custody; the experiment shows an unchecked record relationship, not production of the contradictory combination. | producer | yes — `ActorOrchestration.swift:468`; a rejected token never becomes accepted (`AuthorityCustody.swift:458-460`, `:528-533`) | source read | accurate observation needing no change |
| DT-122.a | Five observers of an issue: worker native return (slot), worker outbound commit, host acceptance, worker's view of the answer (`ext_custody_status`), host custody setup scope (mmap, erase, munmap only). | actor form | yes — `pw_probe_runner.c:851-856`, `:878`, `:879-883`, `:1096`; `AuthorityCustody.swift:456-502`, `:259-322` | source read; re-read | accurate observation needing no change |
| DT-122.b | `CustodyObservation` reaches the reply only as token status (after the slot-completed check) and as `delivered_length` (only for a delivered transfer); its status, length, reject detail, erased flag and phase are never encoded; "reported independently" describes what the host observes, not what the reply reports. | reply assembly | yes — `ActorOrchestration.swift:464-468`, `:486`; no other reader of those members in `runner/Sources` | source read; grep | contradicted explicit commitment (same statement as DT-62.a) |
| DT-122.c | E1a against E1b: with the seam, no public field distinguishes "the host accepted custody" from "no publication reached the host"; the two host custody scopes are identical. | public CLI; build `8b5de2b2` | recorded as stated (both captures read: scopes identical; token `issued`/208 against `unresolved`) | live then; captures available | accurate observation needing no change |
| DT-122.d | E2 (issue, transfer to self, seam on slot 1): issue `returned`, token `issued`; transfer event `unresolved`; `transfers[0]` held, copied, equal, recipient acknowledged, `source_acknowledged: false`, `delivered`, `delivered_length` 208. Delivery observations survive an unpublished source slot; acceptance does not survive an unpublished issue slot. `token_length` and `delivered_length` both originate with the issuing worker. | public CLI; build `8b5de2b2` | recorded as stated (capture read) | live then; capture available | accurate observation needing no change; a limit to state for the lengths |
| DT-122.e | "The host custody record carries token acceptance" is false if read as `authority_setup.host.custody` and conditional if read as `tokens[].status`; line 429 does not settle which record is meant. | support metadata and one definition | yes — `14-extensions.surface.md:623` (rendered `docs/RESPONSE.md:2680`), `:429` | reading | consequential ambiguity |
| DT-123.a | `ext_custody_status` is decoded into `CWorkerExtensionPublication.custodyStatus`; no production code reads the decoded field; the `custodyNames` table has no reader; neither ever had one. | host collection and assembly | yes — `ActorSession.swift:690`; `ActorOrchestration.swift:295`; grep finds no other use in `runner/Sources`, `controller/src`, `controller/tools`, `tests/lib` | source read; grep | accurate observation needing no change |
| DT-123.b | The raw C word appears in three test places; only `ActorAuthorityTests` reads the decoded field, in-process; E6 recorded value 1 for the issue slot. | tests | yes — `tests/fixtures/extension_controls/authority_binding.c`, `tests/suites/runner_unit/actor_handoff_mutations.py:140-142`, `tests/suites/runner_abi_layout/printer.c:98`; `ActorAuthorityTests.swift:305`, `:394`, `:400`; E6 outputs show `worker_custody_status: 1` | test read; driver output read | accurate observation needing no change |
| DT-123.c | The token status is built from the host's acceptance record and the slot publication; the worker's view of whether it received an answer is retained only internally. | reply | yes | source read | accurate observation needing no change; a limit to state |
| DT-123.q | No end-to-end worker timeout was executed; the entry concerns which fields exist and is not a demonstrated disagreement. | evidence limit | still true | — | evidence limit |

### 4.2 Comparison

**Stated obligation.** `14-extensions.surface.md:377`:

> The slot owns one declared issue. A worker timeout or exit leaves its published bytes available for the host's later copy and erasure. Another issue uses another slot. The native return and host custody acceptance are reported independently.

`:828`: "`issued` requires a completed non-null issue result and accepted host custody; `issued_uncustodied`
retains a completed non-null result without accepted custody … Missing publication becomes `not_reached`
only with supported boundary evidence, otherwise `unresolved`." `:544`: "A false value withholds native result
fields even if a call boundary was observed." `FAILURE-PROPAGATION-CONTRACT.md:260-261`: "Custody acceptance,
delivery acceptance and native consumption remain three observations."

**Producer.** The host records acceptance (status, length, reject detail, erased, phase) in its own list.
Assembly publishes: token status, in which acceptance is consulted only after the issue slot is complete and
non-null; `transfers[].custody_status` (`held` when accepted and unerased at service time); and
`delivered_length`. The worker's `ext_custody_status` is decoded and not used.

**Readers.** All three accept `issued` or `issued_uncustodied` for a completed non-null issue and check a
delivered transfer's own fields. None relates the two.

**What a user reading the envelope cannot conclude today.**

1. From `tokens[].status: unresolved` (or `not_reached`): whether the host accepted, rejected or never saw a
   published token. E1a and E1b differ in no host custody field.
2. From `issued_uncustodied`: why custody is absent. The host's reject detail and the worker's view
   (accepted, rejected, timeout, not published, clock fault) are both unpublished. With shipped components
   the status needs a worker clock fault or an out-of-range native token; neither was executed.
3. From `issued`: whether the worker saw the host's answer. A host that accepts after the worker's wait
   timed out or lost its clock still yields `issued`.
4. From equal `token_length` and `delivered_length`: two measurements. Both were written by the issuing worker.
5. From `valid` diagnostics or an empty consumer result: that token custody and transfer custody agree.
6. In which visit the host accepted or serviced; only the declared phase is published.

What the envelope does support: with a published non-null issue, `issued` means the host accepted the bytes;
a transfer row with `held` means accepted, unerased custody existed when the host serviced that request;
`final_erase: performed` means the host's custody buffer was cleared at teardown in every case.

**Reachability.** Accepted custody beside an unpublished issue slot needs the worker to end between the
host's acknowledgement and its own `completed` store (`pw_probe_runner.c:883-1096`): the kill seam, or a
kill landing in that interval. Nothing downstream can use the custody then; the shipped worker requests no
transfer after a slot it did not publish. Uncustodied issuance beside a held transfer cannot be assembled
from a shipped worker; a substituted worker that commits an outbound token while publishing a null or
unavailable result could produce `null` or `unavailable` beside `held`.

### 4.3 Plausible treatments

| Claim | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| DT-62.a, DT-122.b | Correct the account: say how acceptance is reported and when it is not | `14-extensions.surface.md:377`, `:826-828`; `FAILURE-PROPAGATION-CONTRACT.md:260-261` (outside the shared block) | no | withdraws "reported independently" for the unpublished-issue case | — |
| DT-62.a, DT-122.b | Product change: a public carrier of host acceptance independent of the issue slot (for example `resources.tokens[].host_custody` with status and length) | `docs/porcelain.json` → `docs/generate_porcelain.py` (Swift, Rust, Python records); `ActorOrchestration.swift:462-474`; `PWRunnerReply.swift:597-614`; `controller/src/porcelain_actor.rs:1550-1580`; `tests/lib/extension_evidence.py`; `14-extensions.surface.md` token subject; shape goldens (`--refresh-shapes`); actor fixtures; `witness_contract/response_footprint` | yes; wire fingerprint changes | acceptance visible beside `unresolved`; it would stand next to a withheld native return and invite reading it as that return | a reply that drops an accepted custody observation when the issue slot is unpublished |
| DT-62.d, DT-129.d | Coverage: make the unit case assert the state it exercises | `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift:113-134` | no | none | an assembly that reports `issued`, a length or a native result for an unpublished issue slot because the host accepted; and a run of the case in which the host did not accept (which would make the case vacuous) |
| DT-65.b, DT-65.c | Reader rule in the independent consumer | `tests/lib/extension_evidence.py` after `:306`; controls in `tests/suites/blackbox_e2e/extension_controls.py` | no | consumer rejects the contradiction | a token `issued_uncustodied`, `null`, `unavailable` or `not_reached` beside a transfer row with `custody_status: held` |
| DT-65.c | Mirror in Swift admission and the Rust controller | `PWRunnerReply.swift:581-596`, `controller/src/porcelain_actor.rs:1550-1580` | yes | a reply from a substituted worker with that contradiction degrades to a reporting failure and is `invalid` | same |
| DT-122.d | State the limit for the two lengths | `14-extensions.surface.md:882-884` | no | none | — |
| DT-122.e | Correct the support text | `14-extensions.surface.md:623` (owner metadata) | no | none | — |
| DT-123 | State the limit | `14-extensions.surface.md:377` paragraph | no | none | — |
| DT-123 | Product change: publish the worker's view on the issue event | record and three readers as above | yes | explains `issued_uncustodied` and a worker-side timeout | an issue event that omits a published `ext_custody_status` |
| DT-123 | Remove the unread `custodyNames` table | `ActorOrchestration.swift:295` | yes | none | — |

### 4.4 Recommended disposition

- **DT-62.a, DT-122.b — correct the account; retain the behavior (a limit to state, not a missing carrier
  worth a product change).** Replace the last sentence of `:377` with: "The host records custody acceptance
  separately from the worker's native return. The reply reports acceptance through the token status of a
  published non-null issue and through the transfer records that used the custody. While the issue result
  is unpublished the token is `unresolved` or `not_reached` and the reply reports no acceptance
  observation, whether or not the host accepted the published bytes. The issuing worker's own record of
  the host's answer is not a reply field." Add after `FAILURE-PROPAGATION-CONTRACT.md:261`: "Custody
  acceptance has no field of its own: it is carried by `issued` against `issued_uncustodied` on a
  published non-null issue and by the transfer records." Reason: the state needs the worker to end inside
  one short interval; nothing downstream depends on the withheld fact; erasure is reported regardless; a
  carrier beside `unresolved` would invite the native-return inference the contract refuses
  (`FAILURE-PROPAGATION-CONTRACT.md:317-320`); and the carrier costs a record change in three languages.
  Further evidence would not change this: E1a/E1b already show the two cases are indistinguishable, and
  the decision turns on consequence, not on reachability.
- **DT-62.b, DT-62.c, DT-122.a, DT-122.c — no change.**
- **DT-62.d, DT-129.d — assertion repair.** In the unit case add
  `expectEqual(outcome.custody.first { $0.tokenIndex == 0 }?.status, "accepted")` and
  `expectNil(reply.resources!.tokens[0].token_length)`, so the case pins "host accepted, reply unresolved".
  Existing case: `runner_unit/pwrunner_core_unit_executable`.
- **DT-65.b, DT-65.c — add the reader rule to the independent consumer.** For every transfer row with
  `custody_status == "held"`, the token named by `token_ref` must have status `issued` or `unresolved`.
  Controls (Python-only, base `tests/fixtures/contract/actor_authority_reply.json`, whose token is
  `issued` beside a `held` delivered transfer): status `issued_uncustodied` rejected with the new
  diagnostic; unchanged body accepted; `issued` beside a transfer and delivery rewritten to
  `custody_unavailable`/`unavailable` accepted. `extension_controls.py` must call
  `validate_actor_extensions` for these rows (today its corpus loop calls only `validate_actor_evidence`).
  Swift admission and the Rust controller stay unchanged; accepted limit, to stand with the `:377`
  paragraph: "The host and controller checks relate a token's status to its issue event and a delivered
  transfer to its own fields; they do not compare the two."
- **DT-65.a, DT-65.q — no change.**
- **DT-122.d — reasoned retention with the limit stated** at `delivered_length`: "The issuing worker wrote
  this length to its outbound slot and `token_length` to its evidence slot; their equality checks one
  writer's consistency."
- **DT-122.e — correct the support text** to "A published issue native value projects to native_nonnull;
  token acceptance is carried by the token resource's status."
- **DT-123.a, DT-123.b, DT-123.c — reasoned retention.** The limit is the last sentence of the `:377`
  replacement above. The decode has test readers and stays. Remove the unread `custodyNames` table only
  inside W-B. Reason: no statement promises the worker's view; publishing it is a record change whose
  only use is explaining a status that needs a clock fault or an out-of-range token to occur.
- **DT-123.q — evidence limit carried:** no end-to-end worker custody timeout or clock fault has been executed.

### 4.5 Resulting user duties

The six "cannot conclude" items in 4.2, as duties to refrain. In particular: do not read `unresolved` as
"the host never held this token", do not read a cause into `issued_uncustodied`, and do not treat a clean
consumer or controller result as agreement between token custody and transfer custody (the consumer will
check it after C8; the controller will not).

### 4.6 Worklist

W-A items A13–A16, W-C items C7–C9.

---

## Entries that span subjects

### Observation-time cross-anchor account (review lines 7326–7449)

| id | Claim | Owner here | Holds? | Disposition |
| --- | --- | --- | --- | --- |
| XA.1 | Nine-step timeline of the E3 reply naming each observer. | Subjects 2 and 4; steps on clearing, handles and worker mapping belong to rows DT-63/64/124/125/128, DT-66/126, DT-68/127 | yes against the E3 capture for the fields read here (gate ordinal 2, `departure_requested` false then true, triggers, token and transfer rows) | accurate observation needing no change |
| XA.2 | Explicit ordering survives as capture ordinals with `observed_ns`, visit intervals, `collection_basis` and `owned_reap.departure_requested`; custody acceptance, the cleanup trigger, handle production/release and the worker mapping keep only a final value; last-use clearing is not reported. | Subjects 2 and 4 for acceptance and trigger | yes | covered by the limits recommended in 2.4 and 4.4 |
| XA.3 | Answer 1: which values the worker observes, which the host observes, and which are derived from one stored value. | Subject 2 (`pollStopReason` family); token status (Subject 4) | yes | accurate observation needing no change |
| XA.4 | Answer 2: withheld (acceptance with an unpublished issue slot; unpublished slot payload, by the stated publication rule), overwritten, merged, internal-only values. | Subject 4 for acceptance, `CustodyObservation`, `ext_custody_status`, reject details and service phase | yes | the withheld slot payload is the stated rule and needs no change; acceptance per 4.4 |
| XA.5 | Answer 3: combinations that invite unsupported inference. | here: `exit_requested` with `completion` for an early-reaped actor (DT-129.a); equal lengths (DT-122.d); a full kill chain with `unknown` (DT-121.c). The other four belong to the erasure, handle and ownership rows | yes | 2.4 and 4.4 |
| XA.6 | The tension between DT-62/122 and DT-46/120 is not symmetric: the trigger's dependence is acknowledged and only its recording time is wrong, while acceptance loses an observation the statements call independently reported. | Subjects 2 and 4 | yes; this assessment follows the same asymmetry (correct the time wording; withdraw "reported independently") | accurate observation needing no change |

### Investigation identity sections

| id | Content | Disposition |
| --- | --- | --- |
| ID.1 | Authority investigation conventions (review lines 1972–2027): app `8b5de2b2`, temporary Swift and C builds, scratch under `/private/tmp/pw-authority-trace-3QC3qQ/`, sandbox-related harness failures recorded as harness observations. | Scratch is absent. DT-59.c, DT-60.b, DT-61.b, DT-61.c, DT-62.b, DT-62.c and DT-65.b cannot be re-observed from it; each is treated above as a recorded observation that current source agrees with, and DT-61.c and DT-65.b were re-made with constructed input. |
| ID.2 | Observation-time evidence classes (lines 6570–6676), including: rebuilt specimens differ in path and inode from DT-59/DT-66; published token length equals 171 plus the target path's byte length in three runs, unexplained. | Captures are present and were read. The length correlation is an observation about captures, explains DT-62's 216 against 208, and needs no disposition. |

---

## Outside the review

Noted while re-reading; none is added to the review.

1. `tests/FAILURE-PROPAGATION-CONTRACT.md:280` (shared block) says the host "rejected, timed out on or never
   saw the publication". `serviceOutbound` has no timeout branch (`AuthorityCustody.swift:456-502`); only the
   worker's wait can time out, and a host that accepts afterwards yields `issued`. Removing "timed out on"
   is a correction the shared-region rule permits.
2. `tests/FAILURE-PROPAGATION-CONTRACT.md:541` says diagnostics `stop_reason` is "the `stop_reason` answer
   when supported; otherwise null". The producer and the owning surface project it only for six values
   (`controller/src/porcelain_admission.rs:1403-1419`); line 570 of the same file says so. The DT-121.d
   correction is incomplete without aligning this row (worklist A9).
3. By source, an actor whose last visit completes before its worker stores `done` is stopped as
   `schedule_complete` (`ActorScheduler.swift:562`), so a clean actor run can carry diagnostics
   `stop_reason: null` depending on that order. The registered specimen at
   `check_actor_compositions.py:346-360` (500 ms hang) takes this path for its second actor. Not executed here.
4. The decoder also projects `ready` or `not_required` beside other integrity errors such as
   `invalid_setup_cell` (`AuthoritySetupRuntime.swift:95-102`); both JSON readers reject that shape. Same
   mechanism as DT-60.
5. `34-equipment.surface.md:1052` carries the DT-43.c sentence and that file has no gap node either.
6. `setupDisposition` returns `exited_before_setup` for a failed wait as well as for a reap
   (`ActorScheduler.swift:297-298`). Relevant to anyone who later maps that reason to `child_reaped`.

---

## Consolidated implementation worklist

Order: W-A and W-C need no rebuild and can be verified against the existing app. W-B is the only
product change and needs one signed rebuild. W-D is the control that must follow W-B.

### W-A — accounts (generator inputs and authored owners; none is a build-contract input)

| # | File and place | Change | Claim |
| --- | --- | --- | --- |
| A1 | `docs/contract/13-actors.surface.md:225` `free.effect` | precedence wording (1.4) | DT-36.a |
| A2 | `docs/contract/32-lifecycle.surface.md:659` `free.condition`; `:810-816` subject prose | actor-form resolution wording; untagged-value sentence | DT-43.a, DT-43.b |
| A3 | `32-lifecycle.surface.md:1534` pins (and `34-equipment.surface.md:1052`) | drop the gap clause | DT-43.c |
| A4 | `32-lifecycle.surface.md:90-92`, `:869-871` | trigger is derived; map; pass-through | DT-46, DT-120, DT-121.a |
| A5 | `32-lifecycle.surface.md:74-76` | store can follow the ending | DT-129.a |
| A6 | `docs/contract/41-diagnostics.surface.md:803-807`, prose `:1014-1017`, support limits `:1055` | scheduler reasons project null; deadline case not reached by actors; retained-`unknown` limit; test constructs its pairs | DT-121.b, .d, .q; DT-46.c |
| A7 | `tests/FAILURE-PROPAGATION-CONTRACT.md:361-367`, `:469`, `:508-522` | derivation wording; "Trigger" column; independent observations named; retained-`unknown` limit | DT-46, DT-120, DT-121 |
| A8 | `tests/FAILURE-PROPAGATION-CONTRACT.md:132`, `:468` | stop-reason rows name the actor scheduler's reasons | DT-121.a (coordinate the lists with DT-30's disposition) |
| A9 | `tests/FAILURE-PROPAGATION-CONTRACT.md:541` | "when supported and one of the six ordinary values" | outside-review 2 |
| A10 | `docs/EXTENSIONS.md:79-81` (shared region) | self-transfer wording (3.4) | DT-59.a |
| A11 | `docs/contract/34-equipment.surface.md:890-891`, prose `:894-899` | mismatch is recorded beside the projected decision; integrity errors support no readiness | DT-60 |
| A12 | `34-equipment.surface.md` after `:917` | ready's cells are not re-checked by the decoder; private header word | DT-61.b, DT-133 |
| A13 | `docs/contract/14-extensions.surface.md:377` | replacement paragraph (4.4), including the reader limit | DT-62.a, DT-122.b, DT-123, DT-65 |
| A14 | `14-extensions.surface.md:623` pins | acceptance is carried by the token status | DT-122.e |
| A15 | `14-extensions.surface.md:882-884` | one-writer sentence | DT-122.d |
| A16 | `tests/FAILURE-PROPAGATION-CONTRACT.md` after `:261`; optionally `:280` | acceptance has no field of its own; remove "timed out on" | DT-62.a; outside-review 1 |

Regeneration, in this order, then check every owner:

```sh
tests/lib/python.sh docs/generate_limits.py            # shared regions and spans; development mode keeps the guide frozen
tests/lib/python.sh docs/generate_contract_stamps.py   # REQUEST, RESPONSE, ARCHITECTURE regions, CONTRACT, public.json
tests/lib/python.sh docs/generate_limits.py --check
tests/lib/python.sh docs/generate_contract_stamps.py --check
```

A2, A4, A5, A6, A11, A12, A13 and A15 change public prose and therefore the canonical payload and the
CONTRACT stamp table; A3 and A14 are owner metadata. No shape golden should change; if the generator
reports one, review it before `--refresh-shapes`. `docs/PolicyWitness.md` and its copies are not touched.

### W-C — tests and readers (no build-contract input)

| # | File | Change | Claim |
| --- | --- | --- | --- |
| C1 | `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift:365-407` and a new neighbor case | label assertions (1.4) | DT-36.b |
| C2 | `tests/lib/lifecycle_contract.py:105-106` | comment: the host derives the trigger from this stop reason | DT-120.d |
| C3 | `tests/lib/lifecycle_oracle.py` near `:135-146`; rows in `tests/suites/blackbox_e2e/disposition_controls.py` | trigger must equal `TRIGGER_FOR_STOP.get(stop, stop)`; mismatched pair rejected, unknown pair accepted | DT-120.e, DT-46 |
| C4 | `tests/suites/witness_contract/check_actor_compositions.py` | same-visit self-transfer and consume composition | DT-59 |
| C5 | `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift:155-178` | constructed mismatch controls | DT-60 |
| C6 | `tests/lib/actor_evidence.py:149-159` and actor cross-check; Python-only rows in `tests/suites/blackbox_e2e/extension_controls.py` | readiness relations (a)–(d) | DT-61.c, DT-133.c |
| C7 | `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift:113-134` | pin accepted custody beside the unresolved token | DT-62.d, DT-129.d |
| C8 | `tests/lib/extension_evidence.py` after `:306` | held custody requires `issued` or `unresolved` | DT-65 |
| C9 | `tests/suites/blackbox_e2e/extension_controls.py` | Python-only rows for C8; call `validate_actor_extensions` | DT-65 |

Do not add C6 or C9 rows to `tests/fixtures/contract/actor_evidence.json`: the Rust unit test reads that
file and would see rows it accepts marked rejected. C1 and C5 edit files that the opt-in
`runner_unit/actor_handoff_mutations` compiles into disposable packages; rerun it. If
`witness_contract/actor_compositions` is in a planned pytest cohort, add C4 and D1 after that cohort's
migration equivalence is established.

### W-B — product change (build-contract input; one signed rebuild)

| # | File | Change | Claim |
| --- | --- | --- | --- |
| B1 | `runner/Sources/PWRunnerCore/PWRunnerDisposition.swift:21-23` | add `schedule_complete`, `ended_before_arrival`, `ended_before_completion` → `completion` | DT-121 |
| B2 | `tests/lib/lifecycle_contract.py:107-109`, `:752` | same three entries; widen the self-check to the mapped actor reasons | DT-121 |
| B3 | `runner/Sources/PWRunnerCore/CWorker.swift:559-562`, `CWorkerDisposition.swift:80-81`; optionally `ActorOrchestration.swift:295` | comments say derived / actor form resolves from slots; drop the unread table | DT-120.d, DT-43.a, DT-123.a |

Then: `tests/lib/python.sh docs/generate_worker_identity.py` (it hashes every `runner/Sources` file and
rewrites the generated regions in `pw_probe_runner_abi.h`, `CWorker.swift` and `tests/lib/contract.py`),
the A4 wording variant that names the three actor reasons, the two contract generators again, and
`make build IDENTITY=…`. `controller/src` is not edited. No porcelain record, layout or limit changes.

Sequence inside this batch: land C3 with the current table and run it against the existing app first;
then B1 and B2 together with the rebuild.

**Order barrier:** none of the recommended edits changes the worker wait, the release store or the
query-eligibility rule, so `witness_contract/order_barrier_mutations` is not triggered by the root rule.
B3 edits `CWorker.swift`, which that control patches at exact anchors; the comment is not an anchor, but
the control must be reviewed if an anchor moves.

### W-D — control that follows the rebuild

| # | File | Change | Claim |
| --- | --- | --- | --- |
| D1 | `tests/suites/witness_contract/check_actor_compositions.py:346-360` and its assertions | actor hang beyond the exit grace → `completion`, `host_exit_grace_exhausted`; self-ended actor stays `unknown`; `poll_stop_reason` unchanged | DT-121.c |

### Routed verification

`tests/CHANGE-VERIFICATION.md` entries: "Actor composition, re-delegation and timing qualification";
"Actor authority ownership and operation controls"; the "Admission or validator receivers" route
(boundary and its readers); documentation through `source_drift`.

| After | Cases |
| --- | --- |
| W-A | `source_drift` (all default cases; in particular `limits_documentation`, `build_contracts`, `generator_contract`) |
| W-C, existing app | `blackbox_e2e/checker_controls`; `runner_unit/pwrunner_core_unit_executable`; opt-in `runner_unit/actor_handoff_mutations`; `witness_contract/actor_compositions`; `witness_contract/extensions`, `extension_boundaries`, `extension_combinations`, `extension_redelegation` (new consumer rules run on their envelopes); `witness_contract/worker_attempt_in_flight_at_deadline` and `worker_killed_before_slot_publication` (oracle rule); `unit/rust.unit` (shared fixtures unchanged, confirm) |
| W-B, rebuilt app | `source_drift/build_contracts`, `source_drift/runner_source_manifests_agree`; `runner_abi_layout/c_swift_layout_agreement`; `runner_unit/pwrunner_core_unit_executable`; `runner_c_worker_harness/authority_binding`, `actor_operations`; `unit/rust.unit`, `unit/rust.disposition_reds`; `witness_contract/actor_compositions` with D1, `actor_timing_qualification`, `extension_redelegation`; `failure_boundaries`; then the default battery once, grouped as the management plan's verification sequence requires |

## Count

68 claims assessed: Subject 1, 6; Subject 2, 22; Subject 3, 15; Subject 4, 17; cross-anchor account, 6;
investigation identity sections, 2.
