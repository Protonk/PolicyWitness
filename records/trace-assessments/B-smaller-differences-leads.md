# B — Smaller differences (DT-37–41), unverified leads (DT-44) and the CONTRACT-tracing coverage statement

Read-only assessment pass `B-smaller-differences-leads` at HEAD `837296af`
(2026-11-17). Three subjects, as the coverage map groups them:

- **Subject A** — DT-37–41 (one coverage-map row; every subfinding keeps its own row and disposition).
- **Subject B** — DT-44 (thirteen leads, each verified now).
- **Subject C** — "Coverage and limits of the CONTRACT tracing investigation".

Claim identifiers are the review's, with `.a/.b…` in the review's bullet order
and a digit where one bullet carries more than one claim (`DT-40.a1`). Nothing
is renumbered. 56 claims are assessed.

## Method and evidence available

- The review traced tree `4816b0e4` with the app built at `8b5de2b2`.
  `git diff --stat 4816b0e4 HEAD -- docs/contract controller/src controller/tools runner/Sources runner/Clients`
  shows four files: `docs/contract/README.md`, `docs/contract/runtime.py`, and the
  generated worker identity in `runner/Sources/PWRunnerCore/CWorker.swift` and
  `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`. No surface file and no
  hand-written product source differs. Every statement/producer comparison
  below therefore applies to the reviewed tree and to HEAD alike; only line
  numbers moved. All `file:line` below are HEAD.
- The review's reproduction outputs were under
  `/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/1b7c19fb-c395-4c94-9f87-0906550f66e3/scratchpad/`.
  That directory is absent. Every "reproduced" item in these entries is now an
  account of an earlier observation, not replayable evidence.
- Evidence codes in the tables:
  - `R-src` review, source inspection at `4816b0e4`.
  - `R-run(lost)` review reproduction on the `8b5de2b2` app; output no longer on disk.
  - `R-pass` reported by a sub-agent pass, not re-verified by the review.
  - `N-read` re-read at HEAD by this pass.
  - `N-exec` executed by this pass (side-effect free; listed below).
  - `L-run` local development run present under `tests/out/runs/`
    (`trace-instrument-before`, run `20261117T233807Z_b25fa0ec`, and
    `trace-instrument-after-corrected`, run `20261118T011154Z_5cfcec0a`, both
    against the `2f4d76e4` app). Both record `pass` for
    `failure_boundaries/admission`, `validator_batch_mode/batch_ndjson_roundtrip`,
    `runner_unit/pwrunner_core_unit_executable` and `unit/rust.unit`; the first
    also records `pass` for `runner_unit/client_session_controls`,
    `witness_contract/comparison_matrix` and the
    `runner_filter_*/prediction_unavailable_attempt_observed` cases checked
    here. They are disposable development observations, not release evidence.
- Executions by this pass:
  1. The shipped validator
     (`dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator`,
     app build 1519 at `2f4d76e4`) run as `--batch <pid of the invoking shell>`
     with two constructed lines. Neither line reaches `sandbox_check`. Output is
     quoted under DT-37.a.
  2. `tests/lib/python.sh docs/generate_contract_stamps.py --check` and
     `--check --require-history`: both print `ok: contract surface stamps current`.
     The working tree stayed clean.
  3. In-memory recounts: `work-B-smaller-differences-leads/index_counts.py`,
     `tree_counts.py`, `anchor_count.py`.
- Build-contract inputs (`docs/build_contract.py:15-27`): files under
  `controller/src`, `controller/tools`, `controller/interface`, `runner/Sources`,
  `runner/Clients`, `runner/Services`, `runner/augments` with suffix
  `.rs .c .h .swift .sb .plist .ent`, plus a fixed file list (which includes
  `docs/build_contract.py`, `docs/source_identity.py` and `docs/publication.py`).
  No Markdown or JSON file under `docs/`, no generator under `docs/contract/`,
  nothing under `tests/suites/` or `runner/Tests/`, and no README is an input.
  A `#[cfg(test)]` module or a comment inside `controller/src/*.rs` or
  `runner/Sources/**/*.swift` is an input. The recommended worklist touches no
  build-contract input; two optional items that would are marked.
- During this pass another process left uncommitted edits in the shared
  checkout, and the set grew while the pass ran: `docs/ARCHITECTURE.md` (lines
  936 and 1018, replaced in place), `docs/DEPENDENCIES.md`,
  `docs/architecture.json`, `tests/CHANGE-VERIFICATION.md`, `tests/README.md`,
  `tests/catalog.json`, and under `tests/suites/source_drift/` the files
  `README.md`, `check_planner.py`, `run.sh` and a new
  `test_markdown_reader.py`. This pass made none of them. None touched a line
  cited below when last checked; line numbers in those files may move.

---

# Subject A — DT-37–41

## A.1 Claims table

### DT-37 — statement versus source or neighbor

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-37.a | The validator emit statement says an unsupported filter uses `bad_filter`; a line with an unsupported `filter_type` and no `filter_value` returns `parse_error`, because value presence is checked before the filter name is resolved. | Direct `sb_api_validator --batch` input (admitted host queries never carry an unknown filter type); validator stdout record; observer: the helper's caller; time: line parse. | Yes. Statement `docs/contract/21-wire.surface.md:185` (`wire.validator.emit`), rendered `docs/ARCHITECTURE.md:778`. Producer `controller/tools/sb_api_validator/sb_api_validator.c:345-355` (presence check inside `parse_probe_line`) runs before `:507-512` (`resolve_filter_type_id`, `bad_filter`). | R-run(lost); N-read; N-exec (constructed, below). | Inaccurate mechanism account (case order incomplete). |
| DT-37.b | The typed "Granted reservation fields" condition bounds `control.lease_ms` by the 5,000 ms limit; the client requires `lease <= requestedLease`, the smaller of that limit and the remaining allowance. Field text and free effect state the stricter form. | Reservation control reply; client admission; reachable only with a host that does not cap (the shipped host returns `min(request, limit)`). | Yes. Condition `docs/contract/20-transport.surface.md:101` (ARCHITECTURE.md:99); free effect `:80`; field `transport.control.lease_ms` `:220` (ARCHITECTURE.md:150). Client `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift:142`, `:232`. Host cap `runner/Sources/PWRunnerCore/PWRunnerReservation.swift:42`. | R-src; N-read. | Accurate observation needing no change. |
| DT-37.c | The statement says retries "wait up to 100 milliseconds"; the limits account says "Minimum delay … Fixed minimum"; the source schedules `min(retryDelay, remaining)`. | Client acquisition retry; timer value versus gap before another connection. | Yes, and both accounts hold. `20-transport.surface.md:68` (ARCHITECTURE.md:86); `docs/limits.json` id `reservation_retry_delay` (LIMITS.md:153); `PWRunnerClientSession.swift:168-178`, then `:129-131`. | R-src; N-read; L-run (`runner_unit/client_session_controls`). | Accurate observation needing no change. |
| DT-37.d | "Excluded prediction pairs" renders its set as "Requires ((…) or (…))", the phrasing adjacent admission rows use; a matching query is planned without a validator query, not refused. | Rendered REQUEST statement; reader of the table. | Yes. `docs/contract/12-probes.surface.md:112-124` (`probes.query.excluded`, `.pairs`), rendered `docs/REQUEST.md:882-889`. The label comes from `docs/contract/tree.py:1282`. Behavior `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift:325-327`. | R-src; N-read. | Consequential ambiguity. |
| DT-37.e | The validator subject's support says "Duplicate query-key behavior is source-read"; the child definition's support is check-read on `batch_ndjson_roundtrip` and says both member orders are checked. | Support metadata (outside the public digest). | Yes. `21-wire.surface.md:235` versus `:211-220`. The check does assert both orders: `tests/suites/validator_batch_mode/run.sh` `direct-batch` step, `duplicate_order{0,1}`. | R-src; N-read; L-run. | Inaccurate account of support (stale, understated). The child owner is right. |
| DT-37.f | `sandbox_check.filter.kind`, `attempt.kind`, `attempt.action` and `policy.format` state their vocabulary refusal without the byte limit whose capacity refusal precedes it. | Ordinary and actor requests; host admission; reply `admission_failure` / `request_failure`. | Yes. `12-probes.surface.md:163-171` (`probes.filter.kind`), `:197-205` (`probes.attempt.kind`), `:207-209` (`probes.attempt.action`); `docs/contract/11-policy.surface.md:21-29` (`policy.spec.format`). Producer `CWorkerRequestPlanning.swift:180`, `:193-195`, `:215`, `:222`, `:228-232`, all before meaning admission (`runner/Sources/PWRunnerCore/ProbeRunner.swift:29`, `:59`, `:120`). Limits rows `probe_plan_label` (127 UTF-8 bytes) and `request_label` (63). | R-run(lost); N-read; L-run: `failure_boundaries/admission` (`tests/suites/failure_boundaries/check.py:68-69`, `:157`, `:166-167`). | Consequential ambiguity (omitted precondition; the bound is stated only in LIMITS). |
| DT-37.f-q | Qualification: "Those runs were not repeated." | — | The 128-byte and 64-byte reproductions were never repeated and are no longer on disk. The default case `failure_boundaries/admission` exercises the same boundary with constants independent of the limits manifest. | L-run. | Accurate observation needing no change. |

### DT-38 — check-read support

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-38.a | Assembly support pins "Completed, incomplete, absent and unsupported slots map to distinct provenance and outcomes"; the cited test checks outcomes through `buildAttemptResult` and never asserts `result_source` or `missing_reason`. | Support metadata; constructed Swift unit inputs. | Yes. Owner `docs/contract/31-steps.surface.md:562-571` (RESPONSE.md:1136). `runner/Tests/PWRunnerCoreTests/AttemptOutcomeMappingTests.swift` never calls `buildStepResults`. Incomplete and absent slots share one outcome (`no_completed_result`, `runner/Sources/PWRunnerCore/CWorkerStepResults.swift:193-212`). Provenance is assigned at `CWorkerStepResults.swift:56-63`. | R-src; N-read. | Overstated coverage credit. |
| DT-38.b | Relations support pins "checks mapped operations, submitted relations, order and limitation values"; the order is read from the fixture row and passed through, and the lifecycle limitation is appended by the test helper. | Support metadata; constructed matrix rows. | Yes. Owner `31-steps.surface.md:766-774` (RESPONSE.md:1216). `runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift:73-83`, `:129-130`. The producer copies its `order` argument (`runner/Sources/PWRunnerCore/CWorkerComparison.swift:22`); production appends the lifecycle limitation in `CWorkerStepResults.swift:83-86`. | R-src; N-read. | Overstated coverage credit for the order and lifecycle-limitation parts; the rest of the pin holds for constructed inputs. |
| DT-38.c | Publish support pins "Independent minimal/empty paths are read in source" while the cited test exercises both paths. | Support metadata. | Yes, with one correction to the review. The body titled "independent minimal binary report survives repeated rich writer failure" (`runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift:236-246`) asserts two writer calls, the `PWP1` prefix and a smaller size. The comparison with a separately constructed minimal frame is in "actual text budget failure reaches independent minimal reporting" (`:247-312`). Empty output after a minimal-writer failure is asserted at `:314-330`. Owner `docs/contract/30-reply.surface.md:281-288` (RESPONSE.md:478). | R-src; N-read. | Inaccurate account of support (understated). |
| DT-38.d | The "A timeout followed by cleanup" support pins "later source reap and unchanged timeout"; the test asserts one timeout value twice and does not order the reap. | Support metadata; real fixture child, 50 ms allowance. | Yes; verified now. `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift:261-277` reads one final result: gate outcome `timed_out` at `:271` and again at `:276`, `actors[0].quiescence == "reaped"` at `:275`. No ordinal or time comparison. Owner `docs/contract/33-actor_evidence.surface.md:828-838` (RESPONSE.md:1577). | R-pass; N-read. | Overstated coverage credit. |

"Related assertion-scope observations: DT-04, DT-22 and DT-32" is a
cross-reference, not a claim; those entries belong to other passes.

### DT-39 — hand-authored prose

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-39.a | EXTENSIONS says the recipient "consumes only in a later visit of its own"; the complete statement permits a consume later in the same phase after a self-transfer. | Actor form, sender equals recipient; shared region copied into the frozen guide. | Yes. `docs/EXTENSIONS.md:81-83`. Rule `docs/contract/14-extensions.surface.md:206-217` (`q < p or (q == p and b < a)`). Admission `runner/Sources/PWRunnerCore/ActorPlan.swift:451-489` walks actions in order with no different-phase requirement. | R-run(lost; one specimen); N-read. | Inaccurate mechanism account (false for a self-transfer, true for any other recipient). |
| DT-39.b | runner/README says "every actor's region and authority region exist before the first launch". | Actor form; host setup order. | Yes. `runner/README.md:127-128`. Authority regions and custody first (`runner/Sources/PWRunnerCore/ActorScheduler.swift:206-219`); each evidence region is created in `ActorSession.init` (`runner/Sources/PWRunnerCore/ActorSession.swift:62-108`), constructed per actor inside the launch loop (`ActorScheduler.swift:234`). | R-src; N-read. | Inaccurate mechanism account. |
| DT-39.c | controller/README names `execution_envelope` as the assembler; that function exists only in the test module. | Developer reference prose. | Yes. `controller/README.md:232-235`. `controller/src/run_flow.rs:787-801` (`#[cfg(test)] mod tests`). Production: `run` (`:521`, record literal `:702-710`), `complete_execution` (`:728`), `execution_parts` (`:779-785`), `envelope` (`:140`). The same name is in `docs/ARCHITECTURE.md:464` (authored prose). | R-src; N-read. | Inaccurate mechanism account. |
| DT-39.d | WORKER.md says "the host closes its readiness reader after the wait". | Host descriptor lifetime. | Yes. `docs/WORKER.md:142-144`. `ActorSession.swift:443-450` keeps the read end after a received ready byte; it closes at teardown (`:465`). The generated inventory row s3a in the same document (`WORKER.md:583`, from `docs/architecture.json`) states the accurate account. | R-src; N-read. | Inaccurate mechanism account. |
| DT-39.e | The guide describes the owned-reap record "with an optional capture ordinal"; RESPONSE gives a required integer. | Frozen guide text. | Yes. `docs/PolicyWitness.md:1691` (frozen); `docs/RESPONSE.md:1981`. Declaration `runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift:72` is non-optional; producer `runner/Sources/PWRunnerCore/CWorker.swift:1092-1094` always supplies it. | R-src; N-read. | Inaccurate account in a frozen document; the technical owner is right. |
| DT-39.f | The guide quotes the unknown-augment error with single quotes; the source uses Rust debug quoting. | Frozen guide; `result.error` text. | Yes. `docs/PolicyWitness.md:921`; `controller/src/augments.rs:51-57`, `:262` produce `unknown augment "name"`, or `<unreported: N bytes>` above the report bound. No surface states the text. | R-src; N-read. | Inaccurate account in a frozen document; no technical statement of the text exists. |
| DT-39.g | ARCHITECTURE links `runActors` to the file that calls it. | Hand-authored link. | Yes. `docs/ARCHITECTURE.md:258`; call `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift:86`; definition `runner/Sources/PWRunnerCore/ActorOrchestration.swift:17`. | R-src; N-read. | Inaccurate account (link target). |

### DT-40 — index structure

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-40.a1 | "Find a commitment" has 180 rows, all `surface.subject`; the map routes 199 units, 19 of them surfaces; the introduction says "The commitment index covers every routing unit." | CONTRACT index; document reader. | Yes (recounted: 180 / 199 / 19). Sentence `docs/contract/trace-introduction.md:22` (CONTRACT.md:23). `docs/contract/presentation.py:130-131` keeps subjects only; `:38-39` calls both kinds routing units. | R-src (script); N-read; N-exec recount. | Inaccurate account (an explicit statement about the index is false for 19 units). |
| DT-40.a2 | 105 of 930 changed-item rows give a surface root as the candidate commitment, which has no index row. | Same. | Yes (recounted: 930 rows; 105 = 81 source support + 24 check support, over nine surfaces). | N-exec recount. | Accurate observation (follows from a1 and b). |
| DT-40.b | Surface-scoped owners send implementing symbols to the surface root instead of the rule they implement. | Changed-item index. | Yes. `presentation.py:141-146` uses the owner's parent; ten owners have a surface as parent. Examples: CONTRACT.md:1306, 1472, 1481 (transport root in RESPONSE while `transport.delivery` renders in ARCHITECTURE); 1017, 1026, 1028 ("Managing runners"). | R-src; N-read. | Consequential ambiguity (navigation; the link resolves, the scope is not shown in the row). |
| DT-40.c1 | Four citations name a file that only calls or uses the symbol. | Owner citations. | Yes. `docs/contract/10-request.surface.md:361` (`run_flow.rs: validate_request_contract`; defined `controller/src/request_patch.rs:71`), `:467` (`run_flow.rs: strip_runner_selector`; defined `controller/src/runner_select.rs:226`), `docs/contract/13-actors.surface.md:140` (`ActorOrchestration.swift: actorApplicationAssessment`; defined `PWRunnerAuthoritySetup.swift:109`), `docs/contract/14-extensions.surface.md:700` (`ActorOrchestration.swift: PWRunnerTransferRecord`; declared `runner/Sources/PWRunnerCore/PWRunnerActors.swift:221`). | R-src; N-read. | Accurate observation; its consequence is that these owners give the definition file no changed-item row. |
| DT-40.c2 | The citation check is substring presence. | Generator. | Yes. `docs/generator_common.py:105-116`: a source citation needs `symbol in text`; a check citation also needs a definition form. | N-read. | Accurate observation needing no change. |
| DT-40.c3 | `porcelain.rs: pub fn decode` matches three definitions. | Owner citation. | Yes. `controller/src/porcelain.rs:32`, `:155`, `:174`; cited twice in `21-wire.surface.md`. | N-read. | Consequential ambiguity (minor). |
| DT-40.d1 | One symbol appears under two spellings in separate rows. | Changed-item index. | Yes; six symbols at HEAD: `compare` / `fn compare` (CONTRACT.md:867-868), `gates` / `fn gates` (907-912), `admission_problem` / `pub(crate) fn admission_problem` (916-930), `admit_reply` / `pub(crate) fn admit_reply` in `run_flow.rs` (957-979), `reply_contract` / `pub(crate) fn reply_contract`, `identity` / `def identity` (`docs/build_contract.py`). | R-src; N-exec recount. | Consequential ambiguity (minor). |
| DT-40.d2 | Two different functions named `admit_reply` are both indexed under that name. | Same. | Partly. Each row carries its file path (`porcelain_admission.rs: admit_reply`, CONTRACT.md:919; `run_flow.rs: admit_reply`, 957-959), so the two are distinguishable. | N-read. | Accurate observation needing no change. |
| DT-40.e1 | Listed implementing symbols and interface entries have no row (`workerAdmissionFailure`, `planValidatorQueries`, `classifyActor`, `launchAndSetUp`, `collectOutput`, `classify_service_output`, `sign_install_tree`, `cmd_runner_remove`, `result.admission_refusal`, `result.admitted_unavailable`, `@request_selector` kinds). | Index. | Yes for every listed name: zero occurrences in CONTRACT.md and in the surfaces; each exists in source or `controller/interface/inventory.json`. | R-pass (spot-checked); N-read. | Accurate observation; the index is declared partial (`trace-introduction.md:22-25`). |
| DT-40.e2 | No limit identifier or `docs/limits.json` row exists, though statements embed `limit(…)` values. | Index. | Yes. | N-read. | Accurate observation; a gap the partiality sentence does not name. |

"Related: DT-06, DT-13, DT-17" is a cross-reference.

### DT-41 — tour commitment lists

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-41.a | WORKER's "Starting authority and ambient context" list names `actors.sandbox`; the section does not discuss apply or unapplied. | Tour list from the presentation map. | Yes. List `docs/WORKER.md:276-283` (`docs/contract/presentation.json`, `commitments_authority`). Section `:176-275` contains no "unapplied" and no actor sandbox discussion; "post-apply sleep overrides" is at `:237`, augments at `:185-186`. | R-src; N-read. | Inaccurate account (the association is not borne out by the section). |
| DT-41.b1 | CONTROLLER's "Selecting and directing the apparatus" list names `equipment.binding`, while its prose describes host binding as a separate obligation. | Same. | Yes. Prose `docs/CONTROLLER.md:160-162`; list `:173-178`. | R-src; N-read. | Inaccurate account. |
| DT-41.b2 | "Receiving and evaluating evidence" explains collection bounds, the label check and reply-wide findings; its list omits `diagnostics.execution`, `diagnostics.issue`, `profile.receipt.labels`. | Same. | Yes. Prose `CONTROLLER.md:219-287` (geometry `:221`, label check `:244-248`, reply-wide findings `:261-266`); list `:289-298`. | R-src; N-read. | Accurate observation (lists are navigation, not complete). |
| DT-41.b3 | That list includes `steps.assessment.fresh`, a worker rule. | Same. | Yes. The rule's actor is the worker (`31-steps.surface.md:777-784`). The controller's check of fresh-I/O relationships is stated at `diagnostics.execution` (`docs/contract/41-diagnostics.surface.md:680`). | R-src; N-read. | Inaccurate account (names the wrong rule). |
| DT-41.b4 | Four rules the preparation prose explains appear in no tour list: `request.options.failure_order`, `request.specimen.hold`, `policy.augments.actors`, `refusals.controller.consequence`. | Same. | Yes. Prose `CONTROLLER.md:99-120`. At HEAD 68 of 129 rules are in no tour list, directly or through a listed ancestor. | R-src; N-exec recount. | Accurate observation. |
| DT-41.q | Qualification: the README calls these lists reviewed navigation and does not claim completeness. | — | Yes. `docs/contract/README.md:101-104`; `docs/contract/AGENTS.md` ("Author tour commitment associations by reading the section against each statement"). | N-read. | Accurate qualification. It bounds b2 and b4. It does not cover a, b1 and b3: a present entry says "Commitments explained here". |

## A.2 Comparison

**DT-37.a.** Owner statement (`wire.validator.emit`): "Parse errors use
`parse_error`; an unsupported filter uses `bad_filter`." The neighboring
`wire.validator.query` prose says "NONE requires filter_value absent; other
types require it present." Producer: `parse_probe_line` compares the type with
the literal `NONE` and returns "filter_value required for non-NONE filter_type"
before `run_batch` resolves the name. Observed now on the shipped helper:

```
{"step_id":"a","operation":"x","filter_type":"BOGUS"}
  -> {"kind":"sb_api_validator_verdict","schema_version":1,"step_id":"a","outcome":"parse_error","error":"filter_value required for non-NONE filter_type"}
{"step_id":"b","operation":"x","filter_type":"BOGUS","filter_value":"y"}
  -> {"kind":"sb_api_validator_verdict","schema_version":1,"step_id":"b","outcome":"bad_filter","error":"unsupported filter_type"}
```

The check `validator_batch_mode/batch_ndjson_roundtrip` asserts `bad_filter`
for an unknown type with a value (`e1`) and `parse_error` for `PATH` without
a value (`e2`). It has no unknown type without a value. The source is right;
the statement omits the order.

**DT-37.b.** The typed condition requires `control.lease_ms <= limit("reservation_lease")`.
The free effect of the same rule says the client "checks the echoed attempt
and requested lease", and the field says "A client accepts a positive value no
greater than the requested lease." The client does exactly that. The typed
condition is a true necessary condition; the stricter relation depends on the
request of the same live attempt, which the rule keeps as free text. No reader
or test contradicts either. `runner_unit/client_session_controls` asserts the
requested lease is no longer than the remaining allowance
(`runner/Tests/PWRunnerClientSessionTests/main.swift:214`); no control submits
a grant above the requested lease.

**DT-37.c.** After a failed or occupied attempt the client schedules
`min(100 ms, remaining)` and then calls `beginAttempt`, which ends at the
overall deadline when nothing remains. A shortened wait therefore ends in
`overall_deadline`, never in another connection. "Wait up to 100 milliseconds,
shortened by the remaining allowance" describes the timer; "Minimum delay
between a failed/occupied attempt and another connection, within the remaining
allowance" describes the gap between connections. Both are true.
`client_session_controls` asserts connection times at exact 100 ms steps
(`main.swift:88`, `:104`, `:114`).

**DT-37.d.** `probes.query.excluded` is a definition with `defines: "condition"`.
The renderer prints every `test` as "Requires …" and CONTRACT's notation says
"Expressions state requirements". Under the definition's own title the phrase
can be read as "an excluded pair requires this", but it sits directly below an
admission table whose "Requires" rows refuse the request. The consequence is
stated one paragraph above, in `probes.query.eligibility`: "withhold native
prediction when … its operation/filter pair is excluded; report
prediction_unavailable while leaving the attempt eligible." The planner agrees.

**DT-37.e.** The check body builds each query with every recognized key twice,
in both orders, and asserts the echoed strings equal the second set. The
child owner's account is accurate. The subject owner's limit sentence predates
it and contradicts it.

**DT-37.f.** `refusals.request.select` says "Complete decoded capacity checks
before meaning admission", and sibling fields (`query.operation`,
`filter.value`, `attempt.target`, `attempt.args`, `run_kind`) carry their
limit spans. These four fields do not. `failure_boundaries/admission` submits
each field one byte over its cap and requires `admission_refused` with the
exact counts, then submits an unknown label at the cap and requires
`unknown_filter_kind`, `unsupported_attempt` or `unsupported_policy_format`.
Producer and test agree; the field text omits the bound.

**DT-38.a.** Pin: "Completed, incomplete, absent and unsupported slots map to
distinct provenance and outcomes; action mapping preserves exec child
observations." The cited test asserts three outcomes for four slot states and
one `child_pid`. Other tests do call `buildStepResults` and assert provenance:
`runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift:264-291` (synthetic
query provenance; `slot_incomplete`) and
`runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift:240-247`,
`:286-296` (`slot_incomplete`, `slot_absent`, `result_source: synthetic`). No
Swift control asserts `attempt_not_supported` through the step builder.

**DT-38.b.** Pin: "The scenario matrix checks mapped operations, submitted
relations, order and limitation values, including spawn and unlink
distinctions." The owner's limits already say "Constructed controls were
read." What the assertions establish for order is that the producer copies
the value it is given; for the lifecycle limitation, that the test adapter
appends what the step builder would. Order derivation is exercised elsewhere
(`runner/Tests/PWRunnerCoreTests/OrderingTests.swift`, not read here), and the
step builder's limitation is asserted at `DispositionResolverTests.swift:245-246`.

**DT-38.c.** Pin: "… malformed fallback markers refuse. Independent
minimal/empty paths are read in source." The cited test runs both paths. A
separate executed owner (`21-wire.surface.md:137-149`) already credits the
same test for the minimal writer. The publish owner understates.

**DT-38.d.** The example says "Cleanup later reaps the source; the gate
remains `timed_out`." The test proves the final result holds `timed_out`
beside a reaped source. "Later" follows from scheduler structure, not from an
assertion; reading one field twice cannot show that it stayed unchanged.

**DT-39.a–g.** In each case the source decides and the prose is the inaccurate
party; A.1 gives both sides. Two are in the frozen guide (e, f) and cannot be
edited. For f the structured code `augment_unavailable` at
`request_failure.code` (`docs/contract/11-policy.surface.md:152`) is the
stated machine classification; the error text has no technical statement.

**DT-40.** `indexes()` builds "Find a commitment" from routed subjects only and
changed-item rows from each owner's parent. The introduction's sentence is the
only false statement. The table header says "Candidate commitment" and the
paragraph above it says "A file association identifies candidates for review,
not every behavior that file can affect"; the introduction adds "Source and
interface associations are partial: an absent association is an unknown".
Under those sentences b, c1, d2, e1 are accurate descriptions of a
declared-partial aid. c3 and d1 make a text search for one symbol return an
incomplete or ambiguous set.

**DT-41.** The list header is "Commitments explained here:". For a, the
section is about what an `unapplied` actor runs under
(`actors.sandbox.mode`: "records the inherited process restrictions as its
starting condition"), so the association is real but unexplained. For b1 the
prose disclaims the entry. For b3 the entry is the worker's act rule where the
prose describes a controller check. b2 and b4 are omissions from lists that
claim no completeness.

## A.3 Plausible treatments

Every treatment in this subject is a correction of an account in its owner, a
support-metadata repair, a map-only arrangement change, or retention. No
product behavior change is a real candidate: in each case the producer's
behavior is coherent and already tested. None touches a build-contract input.

| claims | candidates | files (authored inputs) and regeneration | consequence | incorrect behavior a check must reject |
| --- | --- | --- | --- | --- |
| DT-37.a | (1) Correct the statement. (2) Retain. | `docs/contract/21-wire.surface.md:185`, subject `wire.validator.emit`; `generate_contract_stamps.py`. Wire stamp changes. | None for callers; behavior unchanged. | A validator that resolves the filter name before checking value presence (it would answer `bad_filter` for an unknown type with no value). |
| DT-37.b | (1) Retain. (2) Express `control.lease_ms <= reservation.lease_ms` in the typed condition. | (2) would edit `20-transport.surface.md:101` and is a public payload change that needs the request alias resolved for the same attempt. | None. | A client that admits a grant above the lease it requested. |
| DT-37.c | (1) Retain. (2) Reword the surface sentence to the connection-gap form. | (2) `20-transport.surface.md:68`. | None. | A client that reconnects sooner than 100 ms after a failed or occupied attempt. |
| DT-37.d | (1) Add one prose sentence to the definition. (2) Change the renderer label for `test` under a `defines: "condition"` definition. (3) Retain. | (1) `12-probes.surface.md:118`, subject `probes.query.excluded`; probes stamp changes. (2) `docs/contract/tree.py:1282` plus review of the five other condition definitions; no stamp change, three rendered documents change. | None. | A host that refuses, or sends to the validator, a query matching an excluded pair. |
| DT-37.e | (1) Correct the subject owner's limit sentence. | `21-wire.surface.md:235`, owner `wire.validator.support`; metadata only, no stamp change. | None. | A parser that keeps the first of two repeated keys. |
| DT-37.f | (1) Add the limit span and the order to each field. (2) Retain, relying on LIMITS. | `12-probes.surface.md:171`, `:205`, `:209`; `11-policy.surface.md:29`. Run `generate_limits.py` (it owns authored spans), then `generate_contract_stamps.py`. Probes and policy stamps change. | None. | A host that applies the vocabulary check before the capacity check, or admits a label above its bound. |
| DT-38.a–d | (1) Correct pins/limits and citations to what the checks assert. (2) For d, add the ordering assertion so the existing pin stands. | Owners at `31-steps.surface.md:562-571` and `:766-774`, `30-reply.surface.md:281-288`, `33-actor_evidence.surface.md:828-838`; test `ActorSchedulerTests.swift:261-277`. Metadata only; no stamp change. | None. | a: a step builder that reports a non-completed slot as `worker` provenance. d: a scheduler that reaps the source inside the gate after its timeout, or changes the gate outcome during cleanup. |
| DT-39.a | (1) Correct the sentence in the owner. (2) Retain if the DT-59 thread selects a product change that refuses a same-visit self-consume. | `docs/EXTENSIONS.md:81-83` (shared region; the guide's copy stays frozen); `generate_limits.py`. | Guide copy diverges from its owner by design. | Admission that refuses, or a worker that withholds, a consume placed after a self-transfer in the same phase. |
| DT-39.b, c, d, g | Correct each sentence or link. | `runner/README.md:127-128`; `controller/README.md:232-235` and `docs/ARCHITECTURE.md:464`; `docs/WORKER.md:142-144`; `docs/ARCHITECTURE.md:258`. Hand-authored; run the generators' `--check`. | None. | — (reference prose). |
| DT-39.e, f | Retain. | No owner outside the frozen guide states the inaccurate text. | Reader must take the type from RESPONSE and classify by code. | — |
| DT-40.a1, a2 | (1) Correct the introduction sentence. (2) Add 19 surface rows to the index. | (1) `docs/contract/trace-introduction.md:22`. (2) `docs/contract/presentation.py:130-133`. No test pins the row count. | None. | — |
| DT-40.b | (1) Retain with the stated limit. (2) Show the owner's subtree scope in the relationship cell. (3) Move each surface owner's citations to rule owners. | (2) `presentation.py:146`. (3) ten owners, 105 rows, each needing a source reading. | None. | — |
| DT-40.c1, c3, d1 | (1) Cite the definition beside the call site; make `pub fn decode` specific; use one spelling per symbol. (2) Retain. | Owner `source:` lists in `10-request.surface.md:361`, `:467`, `13-actors.surface.md:140`, `14-extensions.surface.md:700`, `21-wire.surface.md`, and the six split symbols' owners. Metadata only. | Changed-item rows change; no stamp change. | — |
| DT-40.c2, d2, e1, e2 | Retain; for e2 optionally add one sentence. | `trace-introduction.md`. | None. | — |
| DT-41.a | (1) Add one sentence to the section. (2) Remove the entry. | (1) `docs/WORKER.md` section at `:176-275`. (2) `presentation.json` `commitments_authority`. | None. | — |
| DT-41.b1–b4 | Map-only edits. | `docs/contract/presentation.json` `commitments` entries for `docs/CONTROLLER.md`; `generate_contract_stamps.py`. No stamp change. | None. | — |

## A.4 Recommended disposition per claim

| id | disposition | reason | check, or why more evidence would not change the decision |
| --- | --- | --- | --- |
| DT-37.a | Correct the account in `wire.validator.emit`. Suggested text: "Grammar refusals use `parse_error`; this includes any filter_type other than NONE without filter_value, whether or not the type is recognized. A line that passes the grammar with an unrecognized filter_type uses `bad_filter`." | The source order is deliberate (value rules shared with direct mode) and tested for the neighboring cases. | New control in `validator_batch_mode/batch_ndjson_roundtrip`, `direct-batch` step: an unknown type without a value must give `parse_error` naming `filter_value`; with a value, `bad_filter`. |
| DT-37.b | Retain; no edit. | Every stated claim is true. Accepted limit, already beside the claim in the field text: "A client accepts a positive value no greater than the requested lease." | Reading suffices. Optional control in `runner_unit/client_session_controls`: a grant of `request.lease_ms + 1` must end `protocol_error`. |
| DT-37.c | Retain; no edit. | Both accounts are true at their own observation point. Accepted reading, already in the limits row: the 100 ms value is the delay before another connection, "within the remaining allowance". | `runner_unit/client_session_controls`. |
| DT-37.d | Add one sentence to `probes.query.excluded`. Suggested: "A query satisfying the condition below is excluded: it is admitted, receives no validator query and reports prediction_unavailable. The condition is not an admission requirement." | Smallest edit that removes the misreading; the renderer change touches five other definitions for no gain. | `runner_filter_sysctl_name/prediction_unavailable_attempt_observed` and the same case id in `runner_filter_local_name`, `runner_filter_iokit_registry_entry_class` and `runner_filter_iokit_user_client_class` require `prediction_unavailable` beside an observed attempt for each excluded pair. |
| DT-37.e | Correct `wire.validator.support` limits: replace the last sentence with "Duplicate query-key behavior has its own check-read support under Repeated native query keys." | The child owner and the check agree. | `validator_batch_mode/batch_ndjson_roundtrip`. |
| DT-37.f | Add the bound and the order to the four fields, using `<!-- span limits.probe_plan_label.value_unit -->` (three probe fields) and `<!-- span limits.request_label.value_unit -->` (`policy.spec.format`). Suggested clause: "A value longer than … is a capacity refusal, decided before the vocabulary check." | Sibling fields state their bound; a reader of these four cannot predict `admission_refused`. | `failure_boundaries/admission`. |
| DT-37.f-q | No action. | The default case covers the boundary. | `failure_boundaries/admission`. |
| DT-38.a | Repair the owner: add checks `WorkerEvidenceTests.swift: runWorkerEvidenceTests` and `DispositionResolverTests.swift: runDispositionResolverTests`; pins "The attempt builder maps completed, non-completed and unsupported slots to their outcomes and preserves an exec child PID; step-assembly controls assert synthetic query provenance and the slot_incomplete and slot_absent attempt reasons."; add to limits "Incomplete and absent slots share one outcome and differ only in missing_reason. No cited control asserts attempt_not_supported provenance through the step builder." | The provenance half of the pin has real checks elsewhere; cite them. | `runner_unit/pwrunner_core_unit_executable`. |
| DT-38.b | Narrow the owner: pins "… checks mapped operations, submitted relations and the producer's limitation values over constructed channel results, including spawn and unlink distinctions; the record's order equals the order supplied to the producer."; add to limits "Each row supplies its order, and the test adapter appends the lifecycle limitation." | States what the assertions establish. | `runner_unit/pwrunner_core_unit_executable`. |
| DT-38.c | Correct the pin's last sentence: "Repeated writer failures reach the independent minimal writer, whose frame equals a separately constructed minimal report, and a failing minimal writer returns empty bytes." | The cited test asserts it. | `runner_unit/pwrunner_core_unit_executable`. |
| DT-38.d | Add the ordering assertion to the cited test and keep the pin; if it is not added, change the pin to "… and a final result that keeps timed_out beside the source's reaped quiescence" with the limit "The control reads one final result and does not order the reap after the gate's timeout." | The public example says "later"; its support should assert it. Tests under `runner/Tests` are not build inputs. | New assertions in `ActorSchedulerTests.swift:261-277`: the gate carries no reap reference, and the source's owned-reap capture ordinal is greater than the gate's capture ordinal. Case `runner_unit/pwrunner_core_unit_executable`. |
| DT-39.a | Correct `docs/EXTENSIONS.md:81-83`: "A recipient other than the sender accepts a delivery while parked between its visits and consumes only in a later visit of its own, after that phase's queries were collected and the host released it. An actor that transfers to itself consumes in a later action, which may be in the same visit." Depends on the DT-59 disposition: if that thread selects refusal of a same-visit self-consume, drop this edit. | A shared region may have a false statement corrected with the needed scope; this adds no workflow or example. | The DT-59 thread's control decides the behavior; this row only follows it. |
| DT-39.b | Correct `runner/README.md:127-128`: "every actor's authority region and the host custody session exist before the first launch, and each actor's evidence region is created when that actor is launched". | Source order. | Reading suffices. |
| DT-39.c | Correct `controller/README.md:232-235` and `docs/ARCHITECTURE.md:464`: name `run` (which fills `ExecutionData` with the dossier, transport, acquisition history and fallback compilation) and `execution_parts` (which joins it with the diagnostics for `envelope`). | `execution_envelope` is a test helper. | Reading suffices. |
| DT-39.d | Correct `docs/WORKER.md:142-144`: "The host closes its readiness reader after the wait unless the ready byte arrived; after a received byte it keeps the reader through polling and exit grace until session teardown." | Matches the generated row s3a in the same document. | Reading suffices. |
| DT-39.e | Retain. Accepted limit: the owned-reap `capture_ordinal` is a required positive integer; the statement at `lifecycle.owned_reap.capture_ordinal` governs. | The guide is frozen; the technical owner is already right. | No evidence changes a frozen text. |
| DT-39.f | Retain. Accepted limit, already stated at `refusals.request`: readers classify by the structured code, here `augment_unavailable`; the error text is a human diagnostic. | The guide is frozen; no technical statement of the text exists to correct. | Same. |
| DT-39.g | Correct the link target at `docs/ARCHITECTURE.md:258` to `../runner/Sources/PWRunnerCore/ActorOrchestration.swift`. | Definition site. | Reading suffices. |
| DT-40.a1, a2 | Correct `trace-introduction.md:22`: "The commitment index has one row for each routed subject. A surface's own heading carries its introduction and surface-wide support, and the changed-item index names that heading where support is declared for the whole surface." | One sentence makes every claim true; identity lookup of a bare surface name is not a reading path any index needs. | Counts recomputed here; `source_drift/generator_contract` after regeneration. |
| DT-40.b | Retain. Accepted limit, to stand in the same paragraph (the second sentence above states it). | Reassigning 105 citations to rules is a per-citation reading task with no false statement to repair. | No evidence changes this; it is a navigation choice. |
| DT-40.c1 | Add the definition citation beside each call site (`request_patch.rs: pub fn validate_request_contract`, `runner_select.rs: pub fn strip_runner_selector`, `PWRunnerActors.swift: struct PWRunnerTransferRecord`); in `13-actors.surface.md:140` cite `PWRunnerAuthoritySetup.swift: func actorApplicationAssessment`. | Gives the definition files their changed-item rows; call sites stay where call order is the evidence. | `source_drift/generator_contract` (citation presence). |
| DT-40.c2 | Retain. | Source citations are deliberately free strings (`text exceeds byte limit`, `for i in &sub.disposition`); a definition requirement would refuse valid evidence locators. | — |
| DT-40.c3 | Make the citation specific: `pub fn decode<T: WireRead>(data: &[u8])`. | One match instead of three. | Same case. |
| DT-40.d1 | Use the definition-like spelling in every owner for the six symbols (`fn compare`, `fn gates`, `pub(crate) fn admission_problem`, `pub(crate) fn admit_reply`, `pub(crate) fn reply_contract`, `def identity`). | Rows for one symbol sort together. | Same case. |
| DT-40.d2 | Retain; no edit. | Rows are path-qualified. | — |
| DT-40.e1 | Retain. Accepted limit, already in the introduction: "an absent association is an unknown". Optional: add `planValidatorQueries` to `probes.query.support` and `workerAdmissionFailure` to `request.specimen.support`. | The index claims partiality. | — |
| DT-40.e2 | Retain, and add one sentence after the corrected one: "Limit identifiers have no rows; a statement that embeds a limit shows its identifier, so a search of the statement documents for that identifier finds it." | States the gap the partiality sentence does not name. | — |
| DT-41.a | Add one sentence to the WORKER section: "An actor declared `unapplied` runs its visits under exactly this starting authority and inherited context; an `apply` actor adds its declared policy to the same starting point." Keep the list entry. | Removing the entry would leave `actors.sandbox` in no tour list. | Reading suffices. |
| DT-41.b1 | In `commitments_selection` replace `equipment.binding` with `request.options`. | The prose explains selection and the controller's entitlement preflight (`request.options`) and disclaims host binding. `equipment.binding` stays listed in BUILD and, through `equipment.binding.bind`, in WORKER. | Reading suffices. |
| DT-41.b2, b3 | In `commitments_admission` replace `steps.assessment.fresh` with `diagnostics.execution`; add `diagnostics.issue` and `profile.receipt.labels`. | The prose describes the controller's checks, which those statements own. | Reading suffices. |
| DT-41.b4 | Add `request.specimen.hold`, `request.options.failure_order`, `policy.augments.actors`, `refusals.controller.consequence` to `commitments_preparation`. | The prose at `CONTROLLER.md:99-120` explains each. | Reading suffices. |
| DT-41.q | No action. | Accurate. | — |

## A.5 Resulting user duties

- Classify a refused request by `request_failure.code`, not by matching
  `result.error` text (DT-39.f).
- Read `actors[].owned_reap.capture_ordinal` as always present (DT-39.e).
- When calling `sb_api_validator --batch` directly, expect `parse_error`, not
  `bad_filter`, for any non-`NONE` filter type sent without a value (DT-37.a).
- Do not read `prediction_unavailable` for an excluded pair as a refusal or as
  a prediction (DT-37.d).
- Do not conclude from CONTRACT's indexes that an unlisted source symbol or a
  limit affects no commitment (DT-40.b, e1, e2).
- Otherwise none.

## A.6 Implementation worklist

All edits are documentation, support metadata, the presentation map or tests
outside the build contract. They can land as one batch on the existing
`2f4d76e4` app.

1. `docs/contract/21-wire.surface.md`: `:185` (DT-37.a); `:235` (DT-37.e);
   the two `pub fn decode` citations (DT-40.c3).
2. `docs/contract/12-probes.surface.md`: `:118` (DT-37.d); `:171`, `:205`,
   `:209` with `limits.probe_plan_label.value_unit` spans (DT-37.f).
3. `docs/contract/11-policy.surface.md:29` with a
   `limits.request_label.value_unit` span (DT-37.f).
4. `docs/contract/31-steps.surface.md`: owners at `:562-571` (DT-38.a) and
   `:766-774` (DT-38.b).
5. `docs/contract/30-reply.surface.md:286` (DT-38.c).
6. `docs/contract/33-actor_evidence.surface.md:835-837` only if step 12 is
   not done (DT-38.d).
7. Citations: `docs/contract/10-request.surface.md:361`, `:467`;
   `docs/contract/13-actors.surface.md:140`;
   `docs/contract/14-extensions.surface.md:700` (DT-40.c1); the six split
   spellings, found with
   `grep -n '"symbol": *"\(compare\|gates\|admission_problem\|admit_reply\|reply_contract\|identity\)"' docs/contract/*.surface.md`
   (DT-40.d1).
8. `docs/contract/trace-introduction.md:22` (DT-40.a1, b, e2).
9. `docs/contract/presentation.json`, `commitments` for `docs/CONTROLLER.md`:
   `commitments_selection`, `commitments_admission`, `commitments_preparation`
   (DT-41.b1–b4).
10. Hand-authored prose: `docs/EXTENSIONS.md:81-83` (DT-39.a, after the DT-59
    decision); `docs/WORKER.md:142-144` (DT-39.d) and one sentence in
    `:176-275` (DT-41.a); `docs/ARCHITECTURE.md:258` (DT-39.g) and `:464`
    (DT-39.c); `controller/README.md:232-235` (DT-39.c);
    `runner/README.md:127-128` (DT-39.b).
11. `tests/suites/validator_batch_mode/run.sh`, `direct-batch` step: the
    unknown-type pair of DT-37.a. Update
    `tests/suites/validator_batch_mode/README.md` and the case description in
    `tests/catalog.json` if they enumerate the controls.
12. `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift:261-277`: the
    two ordering assertions of DT-38.d.
13. Regenerate, from the repository root, in this order:
    `tests/lib/python.sh docs/generate_limits.py` (authored spans, EXTENSIONS,
    READMEs), `tests/lib/python.sh docs/generate_contract_stamps.py`, then
    `--check` on both plus
    `tests/lib/python.sh docs/generate_architecture.py --check` and
    `tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history`.
    Expected: wire, probes and policy stamps change in CONTRACT; the guide's
    stamp table and copied regions stay at their `3d3f8e65` bytes.
14. Verify with a fresh `PW_TEST_OUT_DIR`: `tests/run.sh --suite source_drift`
    (documentation route in `docs/AGENTS.md`), then
    `--case validator_batch_mode/batch_ndjson_roundtrip`,
    `--case runner_unit/pwrunner_core_unit_executable` and, as the behavior
    anchor for DT-37.f, `--case failure_boundaries/admission`.
    `tests/CHANGE-VERIFICATION.md` has no entry specific to surface prose; the
    "Admission or validator receivers" row covers step 11.

---

# Subject B — DT-44

The review confirmed only that each cited statement exists. Each lead was
verified here by reading the statement's owner and the producer at HEAD.
Twelve are confirmed, in whole or in part, by reading. One (f) is confirmed by
reading with its reply-level outcome not executed. None is refuted outright.

## B.1 Claims table

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-44.a1 | `PWHostWait.stop`: the stated meaning of `clock_unavailable` ("failed or backward time with bounded sleep fallback") matches no producer; waits with a sleep fallback keep their stop string and set `clock_fault`. | Any host wait record; reply reader. | Partly. Statement `docs/contract/32-lifecycle.surface.md:290` (RESPONSE.md:1707). The only producer of that stop value is the termination gate (`runner/Sources/PWRunnerCore/ActorScheduler.swift:498-510`, `:518`, `:525`, `:532`). Three of its four paths end the wait at once, with no sleep fallback. The fourth (`:501-503`: reap observed while the wait clock had faulted) does follow fallback sleeps. Every other wait keeps its own stop and sets `clock_fault` (`runner/Sources/PWRunnerCore/CWorker.swift:924-931`, `:960-969`, `:1040-1045`). | R-pass; N-read. | Inaccurate mechanism account. |
| DT-44.a2 | `setup_failed` has a second producer (custody setup failure). | Actor setup wait. | Yes. Stated "setup_failed denotes an unavailable nonblocking prerequisite". Producers: readiness reader could not be made nonblocking (`runner/Sources/PWRunnerCore/ActorSession.swift:423-426`); authority custody setup failure (`ActorScheduler.swift:212-217`). | R-pass; N-read. | Inaccurate mechanism account (incomplete). |
| DT-44.a3 | Stop strings `all_resolved`, `equipment_inspection_failed`, `dependency_failed`, `schedule_complete` are emitted and undocumented. | Actor setup and execution waits. | Yes: `ActorScheduler.swift:254`, `:181`, `:343`, `:308`. The field declares no vocabulary and says "Owning operation's reason for ending this wait". | R-pass; N-read. | Accurate observation; no enumeration is promised. |
| DT-44.b1 | `schedule.cancelled` carries `unresolved_termination`, `actor_quiescence_unresolved` and `equipment_execution_<reason>`, none documented. | Actor form reply. | Yes for emission: `ActorScheduler.swift:474`, `:553`, `:177`; also `ownership_lost` (`:479`), which the lead did not list. The statement (`docs/contract/33-actor_evidence.surface.md:546`, RESPONSE.md:1498) lists "such as preparation_refused, execution_allowance_exhausted, an equipment failure or termination_dependency followed by its outcome". | R-pass; N-read. | Accurate observation (the list is illustrative); two unlisted values report that a stopped worker was not reaped. |
| DT-44.b2 | `setup_status: "setup_timeout"` is reported for an actor that was never spawned. | Actor form; shared setup allowance exhausted before that actor's launch. | Yes. `ActorScheduler.swift:223-226` sets it and skips the launch. Statement `33-actor_evidence.surface.md:51-59` (RESPONSE.md:1320) lists the value with no meaning; `not_launched` is a separate value. The reply shows the difference: no `launch`, no `subprocess`, `application.basis: worker_not_launched` (`runner/Sources/PWRunnerCore/ActorOrchestration.swift:439-445`), error "actor never launched: setup_timeout" (`:276`). | R-pass; N-read. | Consequential ambiguity. |
| DT-44.c | `PWWorkerProgress.index` attributes the wait index to "actor waits"; the ordinary-form release wait publishes it too. | Worker progress word; both forms. | Yes. Statement `32-lifecycle.surface.md:490` (RESPONSE.md:1783). `controller/tools/pw_probe_runner/pw_probe_runner.c:1208` and `:1259` publish `PW_OP_PROCEED` with `phase->first_slot` for every phase of either form (`:1660-1663`); only `wait_for_activation` (`:1152`) is actor-only. | R-pass; N-read. | Inaccurate mechanism account. |
| DT-44.d | `not_reached` is stated to require "an incomplete slot"; the resolver accepts any non-completed slot, including `absent`. | Lifecycle claim; constructed or inconsistent output (the host writes slot identities from an admitted plan, so `absent` does not arise in production). | Yes. Statement `32-lifecycle.surface.md:666-667` (RESPONSE.md:1851). Resolver `runner/Sources/PWRunnerCore/CWorkerDisposition.swift:191` (`!completed`). The Python oracle (`tests/lib/lifecycle_oracle.py:184-185`), the Rust reader (`controller/src/porcelain_admission.rs:600-601`) and the failure evidence contract (`tests/FAILURE-PROPAGATION-CONTRACT.md:475`, "no completed slot") all agree with the resolver. | R-pass; N-read. | Inaccurate mechanism account in RESPONSE only. |
| DT-44.e | Validator collection can record `stdout_collection_stop: "eof"` beside deadline-expiry read-error text. | Validator stdout already at EOF while request bytes remain unwritten at the I/O deadline. | Yes by reading. `runner/Sources/PWRunnerCore/ValidatorClient.swift:284-291`. The shipped validator closes stdout only by exiting (`controller/tools/sb_api_validator/sb_api_validator.c` has no close of stdout), and its exit also closes its stdin, so the state needs a substituted validator or an exit landing within microseconds of the deadline. | R-pass; N-read. Not executed. | Inaccurate mechanism account of `read_error`; the producer's two values are each truthful. |
| DT-44.f | The guide's `runner_timeout` wording ("a host execution allowance expired") does not cover actor schedule-allowance expiry, which yields `runner_failed`. | Actor form; frozen guide. | Yes by reading. `runner_timeout` is produced only for a policy-transfer timeout and a `sentinel_deadline` stop (`CWorkerDisposition.swift:276-277`, `:361-365`); actor stops never carry `sentinel_deadline` (`ActorScheduler.swift:549`, `:562`); a cancelled schedule becomes `runner_failed` (`ActorOrchestration.swift:424-425`). The technical statement is already narrower: "Host sentinel or policy-transfer deadline expired" (`docs/contract/30-reply.surface.md:201`). | R-pass; N-read. The reply-level outcome is not executed anywhere: `ActorSchedulerTests.swift:310`, `:358` assert only `cancelled`. | Consequential ambiguity in a frozen document; the technical owner is accurate and silent on the actor case. |
| DT-44.g | `actor_unavailable` is named in EXTENSIONS and the guide as how visits read; no reply field carries it. | Actor form; shared region. | Yes. `docs/EXTENSIONS.md:126`. The value is the scheduler's internal `endReason` (`ActorScheduler.swift:328`), which no reply assembly reads; phase records carry `arrival_observed`, `completion_observed`, `collection_status`, `activation_observation`, `visit_timing`, `termination_gate` (`ActorOrchestration.swift:349-366`). | R-pass; N-read. | Inaccurate account in a shared region (names a value no reader can observe). |
| DT-44.h | `policy_format: "unknown"` is stated for decode refusal and occurs on capacity refusal as well. | Ordinary form refusal replies. | Partly. Field `30-reply.surface.md:69` (RESPONSE.md:386) names only decode refusal. Producer `CWorkerRequestPlanning.swift:290`: on a capacity refusal the value is the submitted format when it is within its bound, otherwise `unknown` (also when the ordinary policy is absent). The capacity case is stated elsewhere: `refusals.admission.echo`, `docs/contract/15-refusals.surface.md:299` ("use unknown for unsafe ordinary policy format"). | R-pass; N-read; L-run (`check.py:157`). | Accurate observation; the field text is incomplete, the rule text exists. |
| DT-44.i | `arrival_observed` and `completion_observed` are sampled at different points in the ordinary and actor forms under one field text. | Phase record; both forms. | Yes. Ordinary: the final acquisition after cleanup (`ActorSession.swift:632-637` through `CWorkerOrchestrator.swift:186-188`). Actor: the scheduler's observation during the visit (`ActorScheduler.swift:386`, `:462` through `ActorOrchestration.swift:351-352`). Field text `33-actor_evidence.surface.md:429`, `:433` (RESPONSE.md:1457-1458). | R-pass; N-read. | Consequential ambiguity. |
| DT-44.j | `runner validate` persists an inferred `kind`, the current equipment inventory and the unentitled worker hash, which the "Refresh validation metadata" rule does not name. | `runner validate`; registry file. | Yes. `controller/src/runner_commands.rs:717-720` (inventory), `:733-735` (kind), `:738` (save); `controller/src/runner_manager.rs:1068-1076` (hash). Rule `docs/contract/50-installation.surface.md:138` (RESPONSE.md:3824). The field statement "Unentitled-worker file hash retained at installation when available" (`:332`) is not true after a validation. | R-pass; N-read. Not executed (the review ran no `runner validate`). | Inaccurate mechanism account (omitted effects; one field statement false after validation). |
| DT-44.k | Response vocabularies list values only an unmapped attempt or unknown filter kind produces; both request forms refuse those inputs before any child; REQUEST says the handling is defensive, the RESPONSE entries do not. | Reply vocabularies versus request admission. | Yes. Refusals `ProbeRunner.swift:29`, `:120`; `ActorPlan.swift:429`, `:437`. Entries `docs/contract/31-steps.surface.md:180`, `:208`, `:295`; `32-lifecycle.surface.md:916-921`, `:965`. Authored prose `docs/REQUEST.md:300-309` says "defensive". | R-run(lost, two refusals); N-read; L-run (`failure_boundaries/admission`). | Accurate observation needing no change. |
| DT-44.l1 | Adjacent statements describe the readiness result differently. | Worker evidence record. | Yes. Field `32-lifecycle.surface.md:443` "readiness-write native result" (RESPONSE.md:1769); subject `:564`, `:568` "readiness helper result … zero after one byte was written". The helper returns 0 or -1 (`pw_probe_runner.c:394-402`); a native one-byte write returns 1. | R-pass; N-read. | Inaccurate mechanism account (field text). |
| DT-44.l2 | Adjacent statements describe the policy receipt's two counts differently. | Same. | Yes. Subject `:619` "the worker publishes both counts"; field `bytes_expected` `:623` "Host-selected … from the worker's immutable header input". The worker publishes the received count and a flag (`pw_probe_runner.c:1468-1469`); the host reads both counts after the flag (`CWorker.swift:635-641`). | R-pass; N-read. | Inaccurate mechanism account (subject introduction). |
| DT-44.m | A reply with outcome `runner_reporting_failed` and no `reporting_failure` record receives a `reporting_failure` finding; the family table describes that family as applying to "A reply carrying reporting_failure". | Controller reply admission; constructed or foreign reply (the host sets that outcome only with the record). | Yes. `controller/src/porcelain_admission.rs:1469-1476`; table row `docs/contract/41-diagnostics.surface.md:683` (RESPONSE.md:3019). No test reaches that branch. | R-src (confirmed by the review); N-read. | Inaccurate mechanism account (applicability incomplete). |

## B.2 Comparison

**a.** Stop values by producer, read at HEAD. Readiness wait: `setup_failed`,
`deadline`, `received`, `eof`, `read_error`. Sentinel wait: the poll stop
reason. Exit grace: `exhausted`, `reaped_during_grace`, `wait_error`. Actor
setup wait: `setup_failed`, `all_resolved`, `deadline`,
`equipment_inspection_failed`. Actor execution wait: `schedule_complete`,
`deadline`, `dependency_failed`. Termination gate wait: the gate outcome,
including `clock_unavailable`. Custody recipient wait: `acknowledged`,
`recipient_unavailable`, `deadline`. The statement's `clock_unavailable`
sentence was written for the general wait clock, whose fallback never changes
the stop value. The Swift doc comment above `PWHostWait`
(`runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift:128-137`) carries
the same sentence.

**b.** Emitted `cancelled` values: `preparation_refused`,
`execution_allowance_exhausted`, `equipment_execution_<failure>`,
`termination_dependency:<outcome>`, `unresolved_termination`,
`actor_quiescence_unresolved`, `ownership_lost`. `setup_timeout` covers two
situations: a launched actor whose setup publication did not arrive in the
shared allowance, and an actor whose launch was skipped because the allowance
was already spent. `not_launched` is what remains when the launch loop stops
after a cancellation.

**d.** Statement: "A final earlier progress position establishes `not_reached`
only after confirmed reaping and with an incomplete slot; beside a completed
slot it produces D5." Four implementations and the failure contract say "no
completed slot". With an absent slot the result claim is separately
`unresolved: slot_unavailable`. The witness for `not_reached` is terminal
progress; the slot can only contradict it by being completed, and an absent
slot cannot be associated at all.

**e.** `stdout_collection_stop` is stated as "Host reason for stopping stdout
collection"; `eof` is that reason when stdout ended first. `read_error` is
stated as "Host diagnostic for stdout-read failure", but it also carries the
clock, poll, retention-limit and I/O-deadline diagnostics, the last of which
can concern unwritten request bytes. No reader relates the two fields.
Reachability does not affect the disposition: the statement to correct is the
`read_error` meaning, which is too narrow on every one of those branches
whether or not this one can be reached with the shipped validator. The
closing-stdout/held-stdin fixture is therefore not requested. It could
establish reachability under substitution only; it could not establish it for
the shipped validator.

**f.** Guide (frozen): "`runner_timeout` — a host execution allowance expired,
including sentinel polling or policy transfer." Limits row
`actor_execution_allowance`: "Expiry ends the current visit (`arrival_timeout`
or `completion_timeout`) and cancels the remaining schedule". No statement
names the outcome for the actor case. The reply does identify the boundary:
`schedule.cancelled: "execution_allowance_exhausted"` and the execution wait's
`deadline` stop.

**i.** In the ordinary form a publication that arrives after the host's wait
ended but before final collection reads `true`. In the actor form it reads
`false`, and `visit_timing.release_to_completion_ms` is absent.

**j.** After `runner validate` the recorded unentitled-worker hash and
equipment inventory describe the bundle as read at validation, and a record
with no kind has `byoxpc`. A row whose host executable is missing is skipped
before those writes.

**k.** A closed vocabulary lists what the producer can emit, including values
only a plan that bypassed request admission can cause. The request-side
statements say the inputs are refused (`probes.attempt.action`: "An
unsupported pair refuses the complete request before children").

## B.3 Plausible treatments

| claims | candidates | files and regeneration | build-contract input? | consequence | incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| a1–a3 | (1) Correct the field text. (2) Also declare an open, illustrative vocabulary. | `32-lifecycle.surface.md:290`, `lifecycle.host_wait.stop`. (2) may change the shape golden (`--refresh-shapes` and review). | No. The Swift comment is one; correct it only with another rebuild. | None. | A wait that lost its clock and reports `clock_unavailable` instead of its own stop with `clock_fault: true`. |
| b1, b2 | Correct the two field texts. | `33-actor_evidence.surface.md:546`, `:59`. | No. | None. | A reply with `setup_timeout`, no `launch` and an application basis other than `worker_not_launched`. |
| c | Correct the field text. | `32-lifecycle.surface.md:490`. | No. | None. | — |
| d | (1) Correct the statement to "without a completed slot". (2) Product change: answer `unresolved` beside an absent slot. | (1) `32-lifecycle.surface.md:666-667`. (2) `CWorkerDisposition.swift:191`, `lifecycle_oracle.py:184-185`, `porcelain_admission.rs:600-601`, the failure contract row, fixtures. | (1) No. (2) Yes; signed rebuild. | (2) changes a claim readers validate, for a state production does not construct. | A resolver that answers `not_reached` beside a completed slot, or under a non-terminal basis. |
| e | (1) Correct `read_error` and add one clause to `stdout_collection_stop`. (2) Product change: record `deadline` whenever the deadline branch runs. | (1) `32-lifecycle.surface.md:1107`, `:1111`. | (1) No. (2) Yes. | (2) would make the stop value false for stdout, which ended at EOF. | A collector that reports `deadline` after stdout reached EOF, or `eof` with no diagnostic when request bytes were left unwritten at the deadline. |
| f | (1) Retain the behavior and state the actor case in `reply.record.outcomes`. (2) Product change: classify actor schedule allowance expiry as `runner_timeout`. | (1) `30-reply.surface.md:201-202`. (2) `ActorOrchestration.swift:424-425`, the failure contract's precedence account, actor checkers, the DT-121 stop-reason mapping. | (1) No. (2) Yes. | (2) changes the outcome label for every actor-form timeout; callers keyed on `runner_failed` are affected. | A host that reports `finished` after a cancelled schedule. |
| g | Correct the row in the owner. | `docs/EXTENSIONS.md:126`; `generate_limits.py`. | No. | Guide copy diverges by design. | — |
| h | (1) Complete the field text. (2) Retain. | `30-reply.surface.md:69`. | No. | None. | A capacity refusal that echoes a format above its bound. |
| i | (1) State both sampling points. (2) Product change: one sampling point for both forms. | (1) `33-actor_evidence.surface.md:429`, `:433`. (2) host assembly in one of the two forms plus the readers' relations. | (1) No. (2) Yes. | (2) changes values readers validate. | — |
| j | (1) Correct the rule and three field texts. (2) Product change: keep installation-time values and add validation fields. | (1) `50-installation.surface.md:138`, `:302`, `:332`, `:336`. (2) registry schema, `runner list` output, readers. | (1) No. (2) Yes. | (2) adds registry fields and a migration. | A `validate` that leaves a stale hash beside refreshed signatures. |
| k | (1) Retain. (2) Add "defensive" clauses to five entries. | — | No. | None. | A host that runs the recognized subset of a plan containing an unsupported attempt. |
| l1, l2 | Correct the two texts. | `32-lifecycle.surface.md:443`, `:619`. | No. | None. | — |
| m | Correct the table row; optionally add a control. | `41-diagnostics.surface.md:683`. The control would sit in `porcelain_admission.rs`' test module. | Row: no. Control: yes. | None. | An admission that accepts `runner_reporting_failed` without the record. |

## B.4 Recommended disposition per claim

| id | disposition | reason | check, or why more evidence would not change the decision |
| --- | --- | --- | --- |
| a1–a3 | Correct `lifecycle.host_wait.stop`. Suggested: "Owning operation's reason for ending this wait; each owning record defines its values and the set is open. clock_unavailable is the termination gate's stop when a time sample it required failed, moved backward or was absent. A wait that loses the clock elsewhere continues on bounded sleeps, keeps its own stop value and reports clock_fault. setup_failed denotes a prerequisite that could not be established before waiting: the nonblocking readiness reader, or actor authority-region and custody setup." | Describes all producers without promising an enumeration. | `runner_unit/pwrunner_core_unit_executable`: `ActorSchedulerTests.swift:204-259` asserts the gate's `clock_unavailable` with `clock_fault: true` (`:245`, `:252`). No cited control asserts that another wait keeps its stop under a clock fault; that half rests on reading `CWorker.swift:1040-1045`. |
| b1 | Correct `actor_evidence.schedule.cancelled`. Suggested: "Recorded schedule cancellation reason: preparation_refused, execution_allowance_exhausted, equipment_execution_ followed by the inspection failure, termination_dependency: followed by the gate outcome, unresolved_termination or actor_quiescence_unresolved when a stopped actor was not reaped, or ownership_lost after a failed wait on the active actor; absent when no cancellation was recorded." | Two unlisted values tell the reader a worker may still be running. | Reading suffices; the values are string literals at the cited lines. |
| b2 | Append to `actor_evidence.actor.setup_status`: "setup_timeout labels an actor whose setup publication did not arrive within the shared setup allowance, and also an actor whose launch was not attempted because that allowance was already exhausted; the second has no launch or subprocess record and application basis worker_not_launched." | The reply already distinguishes the two; the statement should say how. | New constructed control in `ActorSchedulerTests`: two actors, a setup allowance the first consumes; the second must have `setupStatus == .setupTimeout` and no pid. |
| c | Correct `lifecycle.progress.index`: "… and activation and release waits identify their visit's first slot. Every phase of either request form has a release wait; activation waits occur only in the actor form." | Source. | Reading suffices (two call sites). |
| d | Correct the statement: "… only after confirmed reaping and without a completed slot, whether that slot is incomplete or absent; beside a completed slot it produces D5." No product change. | Producer, oracle, Rust reader and the failure contract agree; the state is not constructed in production; a stricter resolver is a three-reader signed change with no reader that needs it. | New constructed control in `DispositionResolverTests` beside `:286-296`: duplicate slot identities, terminal basis, progress before the step; expect boundary `not_reached` and result `unresolved: slot_unavailable`. |
| e | Correct `lifecycle.validator.read_error`: "Host diagnostic for the condition that ended collection early: a stdout read failure, the retention limit, a poll or clock failure, or expiry of the I/O deadline; separate from accepted record contents." Add to `stdout_collection_stop`: "eof beside a deadline diagnostic records that stdout had already ended when the I/O deadline expired with request bytes still unwritten." No fixture. | The producer's values are each truthful; the `read_error` meaning is too narrow on four branches regardless of this one. | Further evidence would not change the decision: the correction follows from the branch text, and the fixture could not show reachability for the shipped validator. |
| f | Retain the behavior. Add to `reply.record.outcomes`, `runner_timeout` row: "Expiry of the actor schedule's execution allowance is reported as `runner_failed`." Decide together with the DT-121 thread if that thread maps actor stop reasons. | The technical owner already scopes `runner_timeout` to the sentinel and policy-transfer deadlines; the boundary is identifiable in the reply; changing the label is a product decision that belongs with the stop-reason mapping. | Reading suffices for the account. An executed witness needs a control this tree lacks: a reply-level run of `runActors` with a shortened schedule allowance (the allowance is a field of `ActorScheduleInput`, not a parameter of `runActors`). |
| g | Correct `docs/EXTENSIONS.md:126`: "… its visits are not activated: their phases carry no `activation_observation`, `arrival_observed: false` and `collection_status: not_reached`; other actors' evidence stands. The run is `runner_failed`." | Shared prose must name what a user can observe. | Reading suffices: the phase assembly at `ActorOrchestration.swift:349-366` has no field for the scheduler's end reason. |
| h | Complete `reply.record.policy_format`: "The ordinary policy format when available; a decode refusal uses `unknown`, as does a capacity refusal whose ordinary format is absent or exceeds its bound." | One clause; the rule text already says it. | `failure_boundaries/admission` (`check.py:157`). |
| i | State both sampling points. `arrival_observed`: "… The ordinary form reports the final acquisition of the phase's publication after cleanup; the actor form reports what the scheduler observed while that visit was active." `completion_observed`: "… at the same form-specific point; in the actor form a completion published after the visit's wait ended is not included." | A reader comparing forms needs the time of observation. | Reading suffices. |
| j | Correct `installation.commands.validate` free effect to name the three writes; `installation.runner.unentitled_worker_sha256`: "Unentitled-worker file hash from the most recent installation or validation read, when available."; `worker_equipment_inventory`: "Sealed equipment snapshot from installation, replaced by the verified current inventory at a successful validation, retained as JSON. …"; `kind`: add "validation records byoxpc for a record with no kind". | Existing behavior, settled from source; the alternative adds registry machinery nobody has asked for. | Not executed here. A registry-only control (constructed registry and bundle directory, `runner validate`, read back the three fields) would witness it. The opt-in case `runner_byoxpc/registry_recovery` runs `runner validate` live; whether it reads these fields back was not checked. |
| k | Retain; no edit. Accepted limit, already stated at `probes.attempt.action` and in REQUEST's authored prose: unsupported attempts and unknown filter kinds are refused before any child; the reply vocabularies list every value the producer can emit. | No statement is false. | `failure_boundaries/admission`. |
| l1 | Correct `lifecycle.worker_evidence.readiness`: "Worker publication of its readiness-write helper result, independent of the host's receipt of the byte." | Source. | Reading suffices. |
| l2 | Correct `lifecycle.policy_read` introduction: "At EOF the worker publishes the count it received before comparing it with the host-written expected count; the host reports both counts once it acquires that publication." | Source. | Reading suffices. |
| m | Correct the family row: append "A reply whose outcome is runner_reporting_failed without that record receives the same finding kind and continues through the ordinary checks." | Source. | Reading suffices (seven lines). Optional Rust control, to be batched with another signed rebuild because it lives in a build-contract input. |

## B.5 Resulting user duties

- Treat `schedule.cancelled` values `unresolved_termination` and
  `actor_quiescence_unresolved` as reports that a stopped worker was not
  confirmed reaped (b1).
- Do not conclude from `setup_timeout` alone that a worker was launched; check
  for the `launch` record (b2).
- Do not classify actor-form timeouts by `runner_timeout`; read
  `schedule.cancelled` and the execution wait's stop (f).
- Do not look for `actor_unavailable` in a reply (g).
- When comparing `arrival_observed` or `completion_observed` across request
  forms, account for the different observation time (i).
- Do not treat the registry's `unentitled_worker_sha256` or
  `worker_equipment_inventory` as installation-time values after a
  `runner validate` (j).
- Do not read `stdout_collection_stop: "eof"` as "collection ended without a
  fault"; read `read_error` and `io_error` beside it (e).
- Otherwise none.

## B.6 Implementation worklist

No build-contract input is touched. One batch with Subject A is possible.

1. `docs/contract/32-lifecycle.surface.md`: `:290` (a), `:443` (l1), `:490`
   (c), `:619` (l2), `:666-667` (d), `:1107` and `:1111` (e).
2. `docs/contract/33-actor_evidence.surface.md`: `:59` (b2), `:429` and `:433`
   (i), `:546` (b1).
3. `docs/contract/30-reply.surface.md`: `:69` (h), `:201` (f, after the
   DT-121 coordination).
4. `docs/contract/50-installation.surface.md`: `:138`, `:302`, `:332`, `:336`
   (j).
5. `docs/contract/41-diagnostics.surface.md:683` (m).
6. `docs/EXTENSIONS.md:126` (g).
7. Tests (not build inputs):
   `runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift` (d);
   `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift` (b2).
8. Regenerate and check as in A.6 step 13. Expected stamp changes: lifecycle,
   actor_evidence, reply, installation, diagnostics.
9. Verify: `tests/run.sh --suite source_drift`;
   `--case runner_unit/pwrunner_core_unit_executable`;
   `--case failure_boundaries/admission`.
10. Deferred to the next signed rebuild, if one happens for another reason:
    the doc comment at `PWRunnerLifecycleEvidence.swift:128-137` (a) and the
    Rust control for `porcelain_admission.rs:1469-1476` (m).

---

# Subject C — Coverage and limits of the CONTRACT tracing investigation

## C.1 Claims table

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| CL.1 | What was traced: identity statements consistent with their generators apart from DT-08; 526 owner citations classified; 2,033 `contract-…` anchor links all resolve except 19 test fixture strings; the 130 rules in Rule applicability state entry, recipient and report; both stamp checks current; keys of two real envelopes agree with about twenty record signatures. | Review method statement at `4816b0e4`. | Partly. Both stamp checks print current at HEAD. Anchor references in tracked files resolve except strings in `tests/suites/source_drift/` controls and example strings inside the review record. The counts are not reproducible as stated, although the surfaces are unchanged since that tree: this pass counts 129 rule nodes (66 acts, 49 reports, 14 checks), 593 citation entries (445 source, 148 check) or 414 distinct path/symbol pairs, and 2,739 anchor references. The review's counting rules are not recorded. The envelope comparison cannot be repeated; the envelopes are gone. | N-exec; N-read. | Accurate observation with unreproducible counts; nothing rests on them. |
| CL.2 | Four sub-agent passes each traced one family; DT-22–43 distinguish the primary review's checks from pass observations; DT-44 collects unverified pass observations. | Attribution. | Yes for the entries assessed here: every `R-pass` item in DT-37–41 and DT-44 was re-read at HEAD. | N-read. | Accurate observation. |
| CL.3 | Statements traced and found consistent, clause by clause, except as recorded. | Consistency judgments by the passes. | Not re-verified as a set. Clauses this pass read while assessing its entries agree (admission order; capacity before meaning; excluded pairs; lease, retry and attempt limits; validator grammar apart from DT-37.a; classification of fallback writers). | N-read (partial). | Unsupported inference if read as verification; accurate as a record of what the passes reported. |
| CL.4 | Not reached: a list of records, rules, readers, commands and fault paths. | Scope statement. | Yes as a statement about that investigation. Later sections of the same record reached several items (authority setup, the capture rule, wire identity and projection, the failure contract, transport failure, reconcile). No `runner validate` was run by any section assessed here (see DT-44.j). | N-read (headings only). | Accurate observation. |
| CL.5 | Evidence limits: one machine, the `8b5de2b2` app, a few specimens each; no build or battery run; scratch outputs have no retention guarantee. | Evidence class. | Yes, and the stated risk has materialized: the scratch directory is absent. | N-exec (`ls`). | Accurate observation. |

## C.2 Comparison

The section states scope and limits; it promises nothing about the product.
The only reliance it can create is a reader taking "traced and found
consistent" (CL.3) as verification, or taking "reproduced" entries as
replayable. Neither holds at HEAD.

## C.3 Plausible treatments

Reasoned retention only. The record is kept intact by the management plan; no
permanent document cites these counts.

## C.4 Recommended disposition per claim

| id | disposition | reason |
| --- | --- | --- |
| CL.1 | Retain; do not reuse the counts. | They cannot be reproduced and no decision depends on them. |
| CL.2 | Retain. | Accurate. |
| CL.3 | Retain with the limit: a statement listed there is not a verified statement; verification is the per-claim reading recorded in the assessments. | Further evidence would not change this; it is a statement about the record. |
| CL.4 | Retain; the management plan's coverage map, not this list, says what later sections reached. | Accurate for its investigation. |
| CL.5 | Retain; treat every `R-run(lost)` item as an account. | The outputs are gone. |

The accepted limits belong in the management plan's "Evidence availability
and reuse limits" table, as one added row for the CONTRACT-tracing scratch
directory (absent; accounts only).

## C.5 Resulting user duties

None.

## C.6 Implementation worklist

1. `records/TRACE-MANAGEMENT-PLAN.md`, "Evidence availability and reuse
   limits": add the row described in C.4. No other edit.

---

# Outside the review

Noticed while reading; not added to the review.

1. The byte bound that DT-37.f finds missing from four fields is also missing
   from fields the review did not list and that share the same limit rows:
   `actors.sandbox.mode`, the actor policy `format`, and the extension
   `operation`, `family` and `authority` labels (`request_label`, 63 UTF-8
   bytes; `CWorkerRequestPlanning.swift:235-252`). The same span can be added in
   the same batch.
2. `tests/lib/lifecycle_contract.py:241` lists "not_reached from missing
   progress, an unfamiliar opcode, an absent slot or a live snapshot" among
   prohibited inferences, while its positive row (`:234-236`) and the oracle
   accept `not_reached` beside an absent slot when terminal progress supports
   it. If DT-44.d is corrected as recommended, "an absent slot alone" is the
   reading that keeps both true.
3. No cited control submits a granted lease above the requested lease
   (DT-37.b), and no test reaches the "reporting outcome lacks failure
   evidence" branch (DT-44.m). Neither affects a disposition.
4. In the batch parser a filter type spelled `RAW:0` or `RAW:` resolves to
   filter id 0 but, not being the literal `NONE`, must carry a `filter_value`
   that the native call then does not receive. The case
   `validator_batch_mode/batch_ndjson_roundtrip` asserts this; it is noted only
   because the DT-37.a wording ("other than NONE") depends on it.
