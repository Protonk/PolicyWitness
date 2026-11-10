> Deposited by the coordinator on 2026-11-10 for register row `R-14` in
> `records/contract/CONTRACT-LEDGER.md`. This is the return of a delegated
> read-only pass, unchanged except for this note and Markdown links turned
> into literal text. It is a reading: nothing in it was run. The run of its
> candidates is `records/contract/validators/RUN.md`.

# R14 — three readers on `preparation_failure`, `reporting_failure` and the observation partition

Source comparison only. Nothing was built or run. Every divergence below is a reading of the code and is marked INFERRED; none was executed.
Paths are repository-relative. `CONTRACT.md` 198-202 was read at `docs/CONTRACT.md:198-202`.

Abbreviations: **R** = Rust controller, **S** = Swift host self-check, **P** = Python harness reader.

## 0. Final judgment: how each reader objects, and what a consumer sees

| Reader | Entry point | Objection | Consumer-visible form |
| --- | --- | --- | --- |
| R | `admit_reply` (`controller/src/porcelain_admission.rs:1416-1486`), called only from `execution_diagnostics` (`:1556-1638`, call at `:1631`) outside tests; `execution_diagnostics` is called from `complete_execution` (`controller/src/run_flow.rs:749`). | `Err(Vec<IntegrityIssue>)`, each `{kind, detail}`. Issues accumulate, except a geometry failure, which returns one `reply_capacity` issue before any other check (`:1418-1421`). | `execution_diagnostics` sets `process_disposition: "withheld"`, `termination_cause: "unknown"`, `disposition_integrity: "invalid"` and appends the issues to `disposition_issues` (`:1631-1636`). The raw reply stays in the envelope; `result.ok` and the exit code come from `runner_outcome == "finished"` (`run_flow.rs:759-760`), not from the issues. INFERRED: these fields are published as `data.runner_sandbox_diagnostics` (name seen at `tests/lib/consumer.py:894`; the Rust mapping in `execution_envelope` was not read). On acceptance of a reply with no worker the fields are `process_disposition: "no_worker"`, `disposition_integrity: null` (`:1559-1566`, `:1608`), not `"valid"`. |
| S | `validateForReporting()` (`runner/Sources/PWRunnerCore/PWRunnerReply.swift:241-369`), called from `pwRunnerReportData` (`runner/Sources/PWRunnerCore/PWRunnerService.swift:123-157`, call at `:127`). | Throws `PWRunnerReportingValidationError(message:)` at the first failing guard: one diagnostic per reply. An encoder error takes the same path (`:128-135`). | The host re-issues the reply: `rc: 1`, `normalized_outcome: "runner_reporting_failed"`, `error: "runner host could not encode its result: <diagnostic>"`, `reporting_failure{diagnostic, original_rc, original_normalized_outcome, original_error, evidence_retained: true}`, every step's `comparison` removed (`:136-144`). Nothing else is cleared, so `preparation_failure` stays in the re-issued reply. That copy is validated again on the degraded path (`:146`); if that fails, a minimal reply with empty `steps`/`phases` and `evidence_retained: false` is written, or empty bytes (`:148-155`, `:178-200`). |
| P | `consumer.validate(document, expected_contract)` (`tests/lib/consumer.py:900-914`); `validate_fixture` (`:992-994`). Actor rules: `validate_extensions` (`tests/lib/extension_evidence.py:377-382`) → `validate_actor_evidence` (`tests/lib/actor_evidence.py:442-459`). | Returns a list of strings; empty list = accept. Errors accumulate; a version error returns alone (`:902-904`). | Whatever the calling test does with the list (the callers read assert on it). |

`run_flow::admit_reply` (`controller/src/run_flow.rs:332-360`) is a different function: the delivery/version gate that precedes the semantic reader.

## A. The partition rule, stated positively

Rule common to all three, for a reply with neither `preparation_failure` nor `reporting_failure`: the identities declared in `phases[].action_ids`, taken together, are exactly the `step_id`s of `steps` plus the `step_id`s of `extension_events`; no identity repeats on either side; the declared order restricted to step identities equals the order of `steps`, and restricted to event identities equals the order of `extension_events`; each record's own `phase_id` names a phase whose `action_ids` contains it.

| Element | R | S | P |
| --- | --- | --- | --- |
| Record identities distinct (steps + events) | `porcelain_admission.rs:810-820`, "duplicate action identity" | `PWRunnerReply.swift:298` (`Set(allIDs).count == allIDs.count`) | No separate clause; follows from `sorted(actions) == sorted(all_ids)` with unique `actions` (`consumer.py:773`, `:785`) |
| Declared identities distinct across all phases; phase IDs distinct | `:821-831`, "phase ordinal/partition identity conflict" (same clause carries the ordinal) | `:296-297` | `:773-774`, 'duplicate phase/action identity' |
| Declared = recorded | `:1076-1082`, set equality, "phase actions do not partition reply" | `:298`, set equality | `:785`, sorted-list (multiset) equality |
| Order of steps, order of events | `:1083-1096`, `:1097-1109` (two details) | `:299-300` | `:786` |
| Record belongs to the phase it names | steps `:1110-1118` (kind `ordering`); events `actor_associations` `:1520-1533` | steps `:336-338`; events `:496-497` | `:787` via `_step_phase` (`:179-185`, exactly one match); events also `extension_evidence.py:202-205` |
| Count bound on declared identities (256) | `reply_geometry` `:1699-1704` (returns before every other check); records `:807` | `:297` | `:784` |
| Phase count bound, ordinal = position | `:802-808`, `:822` | `:295-296`, `:311` | `:726`, `:740-741` |
| Diagnostic | several kinds/details | one message for the whole guard (`:302`), "phase identities and ordered actions must partition the reply" | one message for the block (`:788`), 'phase actions do not partition the ordered steps' |
| Skipped when | `preparation_failure.is_some()` — only the equality clause (`:1076`); order and association clauses still run | `preparation_failure != nil` — only the equality term (`:298`) | `preparation_failure_valid(runner)` is true — early return (`:781-783`) skips equality, the 256 bound, order and association together |
| Under `reporting_failure` | not run (`phase_issues` is in the `else`, `:1449-1457`) | not run (`:246-256`) | not run (`:587-589`) |

Same rule: yes, by reading (INFERRED equivalence). Set equality plus separate uniqueness (R, S) and multiset equality with unique declared identities (P) accept the same replies. The implementations differ in decomposition, in diagnostics and in the skip condition, not in the rule.

Does the skip-condition difference alone change a final judgment? No, by reading. In each reader a `preparation_failure` that fails that reader's own rule is itself an objection (R `porcelain_actor.rs:1677-1682`; S `PWRunnerReply.swift:410-420`; P `actor_evidence.py:450-451`), so whether the partition is then applied changes only which diagnostics appear. The final-judgment differences in section D come from the three validity rules not being the same rule.

## B. Conditions applied to a reply carrying `preparation_failure` (no `reporting_failure`)

Where the three rules sit: R `preparation_failure_valid` (`controller/src/porcelain_actor.rs:1066-1116`), required by `validate` (`:1677-1683`), failure → issue `actor_evidence` / "invalid before-launch preparation failure". S one guard in `actorExtensionEvidenceProblem` (`PWRunnerReply.swift:410-421`), failure → throw "preparation refusal contains execution evidence". P `preparation_failure_valid` (`tests/lib/actor_evidence.py:423-439`), failure → 'invalid before-launch preparation failure' (`:450-451`) and, separately, the partition block is no longer skipped (`consumer.py:782`).

"prep" in a cell means the condition is a term of that function/guard and fails as just described. "general" means a check that applies to every actor-form reply and is not relaxed here.

| # | Condition | R | S | P |
| --- | --- | --- | --- | --- |
| 1 | stage/code is `resolved_plan/inconsistent_assignment` or `equipment/equipment_binding_refused` | prep `:1076-1078` | prep `:411-412` | prep `:425-427` |
| 2 | a reply carrying the field is actor form | prep `:1079`; ordinary form: `:1656-1671` "ordinary reply carries actor authority evidence" | no term in the guard; the guard is reached only in actor form (`:644`); ordinary form: `:646-647` "actor evidence in ordinary reply" | prep `:431` in actor form. Ordinary form: **not examined** — `validate_actor_evidence` returns at `:446-449` before `:450`, objecting only if the reply also has events, `authority_setup` or `equipment_inventory` |
| 3 | `normalized_outcome == "runner_failed"` and `rc == 1` | prep `:1080-1081` | prep `:413` | prep `:431` |
| 4 | no `request_failure` | prep `:1097` | prep `:413` | prep `:437` |
| 5 | `actors` nonempty | prep `:1082`; also `custody` `:1163-1173` | general `:381-382` ("actor form carries singular projections"); runs before the prep guard | prep `:431`; also `consumer.py:610-611`, `extension_evidence.py:168-169` |
| 6 | every actor `launch_refused`, no `launch`, no `subprocess` | prep `:1083-1085` | prep `:414` | prep `:432` |
| 7 | `steps` empty | prep `:1086` | prep `:415` | prep `:433` |
| 8 | no extension-event records | prep `:1087` | prep `:415` | prep `:433` |
| 9 | `extension_events` present (not null/absent) | prep `:1087` (`is_some_and`) | **not enforced**: `extension_events ?? []` at `:277`, `:380` | prep `:433` (`!= []`) |
| 10 | `transfers` present and empty | prep `:1088`; presence also `custody` `:1147-1154` | presence general `:383`; empty prep `:415` | prep `:433`; presence also `extension_evidence.py:168` |
| 11 | `resources.tokens/deliveries/handles` empty | prep `:1089-1092` (absent `resources` passes this term; `custody` `:1147-1154` objects to it) | presence general `:383`; empty prep `:415-416` | prep `:434` (absent passes this term; `extension_evidence.py:168` objects) |
| 12 | `authority_setup.host.run.disposition == "not_attempted"` | prep `:1093-1096` | prep `:417` | prep `:435` |
| 13 | `authority_setup.host.regions` empty | prep `:1105-1108` | prep `:418` | **not found** in `:423-439`. `_setup` (`:125-148`) checks a region row's shape and owner only; a well-formed row owned by an existing actor passes |
| 14 | `authority_setup.host.custody` empty | prep `:1108` | prep `:418` | not in `:423-439`. Indirect: a custody row's `token_index` must index `resources.tokens`, which is empty here (`:137`, `:143-146`) → 'custody setup owner association' |
| 15 | every phase `collection_status == "not_reached"` | prep `:1099` | prep `:419` | prep `:437` |
| 16 | no phase has `ordering.proceed_set` or `proceed_observed` | prep `:1100-1103` | **not found** in the guard (`:419`); `collectionEvidenceConsistent` (`:134-154`) and the phase loop (`:311-320`) do not read these flags without completion | prep `:436` |
| 17 | every phase `arrival_observed == false` | prep `:1109-1112` | prep `:419` | **not found** in `:423-439`. General rule only: arrival needs the previous phase complete when the previous phase is the same actor's (`consumer.py:766-769`); phase 0, or a phase following another actor's phase, passes |
| 18 | every phase `completion_observed == false` | prep `:1109-1112`; general `:956-964` | prep `:419`; general `:314` fires first ("invalid phase boundary account") | not in `:423-439`. Indirect: completion needs `proceed_observed` (`consumer.py:761-762`), which term 16 forbids |
| 19 | at most 256 declared action identities | prep `:1113`; `reply_geometry` `:1699-1704` fires first with a lone `reply_capacity` | general `:297` | prep `:439`; then `consumer.py:784` |
| 20 | each declared action identity 1-63 bytes, no NUL | prep `:1114`, `bounded` `:9-11` | **not found**: `:296-298` test uniqueness and count only; no byte bound on action identities in `PWRunnerReply.swift` (the `utf8.count` uses are `:399`, `:473`) | prep `:439`, `bounded` `:22-23`. (Outside this rule neither R nor P bounds action-identity bytes: `porcelain_admission.rs:784-1126`, `consumer.py:742-746`.) |
| 21 | declared action identities distinct | prep `:1115`; general `porcelain_admission.rs:824` | general `:297` | prep `:439`; general `consumer.py:773` |
| 22 | phase identities distinct | general `porcelain_admission.rs:823` | general `:296` | general `consumer.py:773` |
| 23 | each `phase_id` 1-63 bytes, no NUL | **not found** (`porcelain_admission.rs:784-1126`, `porcelain_actor.rs:1066-1116`, `:2257-2368`; grep of `porcelain_actor.rs`, `porcelain_admission.rs`, `porcelain_native.rs`) | **not found** (grep of `runner/Sources/PWRunnerCore`; only request admission tests emptiness, `ProbeRunner.swift:87`, `ActorPlan.swift:362`) | general `consumer.py:736-738`, 'invalid phase_id' |
| 24 | at most 16 phases | `reply_geometry` `:1677-1678`; `:802-808` | general `:295-296` | general `consumer.py:726-727` |
| 25 | phase `ordinal` = position | general `porcelain_admission.rs:822` | general `:311` | general `consumer.py:740-741` |
| 26 | each phase names an actor of the reply | general `porcelain_actor.rs:2343-2347`; `porcelain_admission.rs:1515-1519` | general `:475` | general `consumer.py:654-657` |
| 27 | `actor_visit` = that actor's running visit count | general `porcelain_actor.rs:2348-2354` | **weaker**: `actor_visit >= 1` only (`:475`) | general `consumer.py:658-660` |
| 28 | `actors[].visits` = ordinals of that actor's phases | general, exact equality `porcelain_actor.rs:2329-2340`; `porcelain_admission.rs:1504-1513` | **not found** (grep for `visits` in `PWRunnerReply.swift`, `PWRunnerActors.swift`, `PWRunnerAuthoritySetup.swift`, `PWRunnerEquipment.swift`, `PWRunnerDisposition.swift`) | **one direction**: each phase ordinal is in its actor's `visits` (`consumer.py:661-662`); entries are ints ≥ 1 (`:646-648`); extra entries pass |
| 29 | actor identities distinct | general `porcelain_actor.rs:2266`; `porcelain_admission.rs:1492` | general `:474-475` | general `consumer.py:649-650` |
| 30 | actor `index` = position; `actor_id` 1-63 bytes | general `porcelain_actor.rs:2264-2268` | **not found** (same five files searched) | general `consumer.py:616-621` |
| 31 | collection status agrees with ordering disposition and validator records (so no validator record on a `not_reached` phase) | general `porcelain_admission.rs:927-955` | general `:305`, `:134-154` | general `phase_evidence.py:4-35` via `consumer.py:749-751` |
| 32 | no singular projections (`runner_subprocess`, `policy_sha256`, `sandboxed_after_apply`) | general `porcelain_actor.rs:1156-1162` | general `:381-382` | general `consumer.py:606-608`; `extension_evidence.py:170-171` |
| 33 | `authority_setup` present, one worker scope per actor, scopes well-formed | general `setup` `:369-451` (`scope` `:164-368` not read) | general `:384-385`, `:389-390`; `authoritySetupIntegrityErrors` read at `PWRunnerAuthoritySetup.swift:142-160` only | general `_setup` `:125-160`, `_scope` `:40-122` |
| 34 | binding and entitlement tables present, bounded, internally consistent (not required empty by any reader) | general `equipment`, read at `:589-640` and `:830-850` only; call at `:1686` | general `:384-388`; `pwRunnerEquipmentProblems` body not read | general `_equipment` `:205-344` |
| 35 | each actor's `application` pair has its source | general, call at `:1687-1696`; `application` `:452-588` not read | general `:391-394`; `actorApplicationIntegrityErrors` body not read | general `_application` `:163-195` |
| 36 | termination gates, owned reaps, activation observations | general, call at `:1697`; `gates` read at `:1055-1064` only | general `:395-409`, `:436-468` | general `_gates` `:363-420` |
| 37 | `compiled_profile` context (reply and actors) | `admission_problem` `:1289-1312` | `:365-368` | `consumer.py:555-560`, `:538-551` |
| 38 | table capacities | `reply_geometry` `:1675-1789` (read to 1789) | `:469-472`; `PWRunnerAuthoritySetup.swift:145` | `extension_evidence.py:173-175`; `actor_evidence.py:131-133`, `:209-211` |
| 39 | producer contract is the reader's | `run_flow.rs:346-359`, before the semantic reader (`reply_version` not read) | `:243-245` | `consumer.py:902-904` (`version_errors` not read) |
| 40 | `preparation_failure.actor_id`, `binding_ref`, `reason` examined | not found | not found | not found |
| 41 | a `schedule` value required because of the failure | not found in `:1066-1116` | not found in `:410-421`; `schedule.cancelled` is required only under the failed-inspection rule `:422-435` | not found in `:423-439` |
| — | **skip:** declared = recorded | skipped on presence, `porcelain_admission.rs:1076` | skipped on presence, `:298` | skipped on validity, `consumer.py:781-783` |
| — | **skip:** order and phase-association clauses | still run (`:1083-1118`); vacuous with no records | still run (`:299-300`); vacuous | skipped with the equality (`:783`) |

Counts (41 conditions, the two skip rows excluded): enforced by all three **29** (rows 14 and 18 by P only indirectly); by two **9** (rows 2, 9, 13, 16, 17, 20, 27, 28, 30); by one **1** (row 23); by none **2** (rows 40, 41).

Rows 33-36 are compared at the level "each reader applies its general account check"; they were not compared clause by clause.

The statement to verify — "the Python reader makes no explicit check of host regions, custody, or phase arrival and completion on such a reply": correct for explicit checks (`actor_evidence.py:423-439` has no such term). In effect it holds for region rows and for arrival (rows 13, 17: P accepts). It does not hold in effect for custody rows and completion (rows 14, 18: P objects through a general rule, with a diagnostic that does not mention the preparation failure).

## C. A reply carrying `reporting_failure`

| | R | S | P |
| --- | --- | --- | --- |
| Check that replaces the rest | `porcelain_admission.rs:1426-1448`: outcome `runner_reporting_failed`, `rc == 1`, nonempty `error`, `origin == "runner_host"`, nonempty `diagnostic` and `original_normalized_outcome`, no step `comparison`, and, when `evidence_retained` is false, no steps, `runner_subprocess`, phases or events. Issue kind `reporting_failure`. | `PWRunnerReply.swift:246-255`: the same terms. | `consumer.py:563-577`: the same terms, plus field types of the failure record (`original_rc`, `original_error`, `evidence_retained`); two messages. |
| Outcome `runner_reporting_failed` without the record | `:1450-1456` | `:257-259` | `:563-573` |
| Partition, phase checks | not run (`:1449-1457`) | not run | not run (`:587-588`) |
| Preparation-failure rule (rows 1-21), setup, equipment, application, gates, custody | not run (`actor::validate` is in the `else`, `:1483`) | not run (`extensionEvidenceProblem` is in the `else`, `:323`) | not run (`validate_extensions` at `:589` is under `not failed_reporting`) |
| Actor table and phase/actor association (rows 5 as "bounded nonempty list", 26-30, 32) | not run | not run | **still run**: `_validate_actors` at `consumer.py:590-592`, body `:601-666` |
| Step structure | only "no comparison" | only "no comparison" | `_validate_step` still runs with `failed_reporting` (`:582-586`, `:486-489`) |
| `compiled_profile` | `admission_problem` `:1423-1425` | `:363-368` | `:555-560` |
| Geometry / shape | `reply_geometry` `:1418-1421` | — | `validate_shape` `:912` |
| Worker lifecycle | `execution_diagnostics` still projects each subprocess with `degraded = true` (`:1575`, `:1600-1604`; `validate_lifecycle` not read) | — | `_validate_worker` structure-only (`:688-693`, `:718`) |

A reply carrying both records (what S re-issues after rejecting a preparation-failure reply): none of the three applies the preparation-failure rule or the partition to it.

## D. Candidate divergences in final judgment

All INFERRED from the lines cited. "Baseline" = a preparation-failure reply all three accept: actor form, `runner_failed`, `rc: 1`, every actor `launch_refused` with no `launch`/`subprocess`, `steps`, `extension_events`, `transfers` and the three resource tables empty, host run `not_attempted`, no region or custody rows, phases `not_reached` with no ordering, arrival or completion, declared action identities retained. (INFERRED that the producer makes this; `ActorOrchestration.swift` was not read. The Swift fixture at `runner/Tests/PWRunnerCoreTests/ActorShapeFixtures.swift:426-433` is such a reply for S.)

### D.1 From the preparation-failure rule

| # | Baseline with this one change | R | S | P |
| --- | --- | --- | --- | --- |
| D1 | one well-formed `authority_setup.host.regions` row owned by actor 0 | objects, `porcelain_actor.rs:1105-1108` | objects, `PWRunnerReply.swift:418` | **accepts**, row 13 |
| D2 | `phases[0].arrival_observed: true` (or any phase whose predecessor is another actor's) | objects, `:1109-1112` | objects, `:419` | **accepts**, row 17 |
| D3 | a phase gains `ordering` with `proceed_set: true`, `collection_closed_before_proceed: false`, `proceed_observed: false`, `validator_disposition: "not_invoked"` | objects, `:1100-1103` | **accepts**, row 16 | objects, `actor_evidence.py:436` |
| D4 | one declared action identity of 64 bytes (or empty, or containing NUL) | objects, `:1114` | **accepts**, row 20 | objects, `:439` |
| D5 | `extension_events` null/absent instead of `[]` | objects, `:1087` | **accepts**, row 9 | objects, `:433` |

### D.2 From general checks that also apply to such a reply (found while filling B; not an exhaustive comparison of the general checks)

| # | Baseline with this one change | R | S | P |
| --- | --- | --- | --- | --- |
| D6 | a `phase_id` of 64 bytes (or empty) | **accepts**, row 23 | **accepts**, row 23 | objects, `consumer.py:736-738` |
| D7 | a phase's `actor_visit` wrong but ≥ 1 | objects, `porcelain_actor.rs:2348-2354` | **accepts**, `:475` | objects, `consumer.py:658-660` |
| D8 | `actors[0].visits: []` | objects, `:2329-2340` | **accepts**, row 28 | objects, `consumer.py:661-662` |
| D9 | `actors[0].visits` with one extra ordinal | objects, `:2329-2340` | **accepts** | **accepts**, `consumer.py:646-648`, `:661` |
| D10 | `actors[0].index` not its position | objects, `:2264-2268` | **accepts**, row 30 | objects, `consumer.py:620-621` |

D6-D10 do not depend on `preparation_failure`; the same change to any actor-form reply reads the same way.

### D.3 Not starting from the baseline

| # | Reply | R | S | P |
| --- | --- | --- | --- | --- |
| D11 | a valid ordinary (non-actor) reply with a `preparation_failure` object added and no other actor field | objects, `porcelain_actor.rs:1656-1671` | objects, `PWRunnerReply.swift:646-647` | **accepts**, row 2; the key is in the shape allowlist (`tests/fixtures/contract/response_shape.json`, `reply.preparation_failure`) |
| D12 | a degraded actor-form reply (`reporting_failure`, `evidence_retained: true`) with an actor-table defect (`actors: []`, wrong `index`, wrong `actor_visit`) | **accepts**, section C | **accepts**, section C | objects, `consumer.py:590-592` |
| D13 | JSON only: a valid actor-form reply with `"preparation_failure": null` | accepts (INFERRED: null decodes to `None`; the JSON deserializer was not read; the Rust serializer omits the key when `None`, `controller/src/porcelain_records.rs:3427`) | not expressible (no JSON input) | objects: the test is key presence, `actor_evidence.py:450` |

### D.4 Differences in diagnostic only (all three object)

- Any reply whose `preparation_failure` fails all three rules while declared action identities remain (wrong stage/code pair, outcome `finished`, an actor with `launch`): P reports 'invalid before-launch preparation failure' **and** 'phase actions do not partition the ordered steps' (`consumer.py:782-788`); R reports the first without a partition issue; S reports one message. This is the only effect found of the presence/validity difference.
- A custody row added: R and S name the preparation failure; P reports only 'custody setup owner association' and still treats the failure as valid (partition skipped).
- `completion_observed: true`: R "completion lacks arrival and observed proceed" plus the preparation issue; S "invalid phase boundary account" (`:314`, before the preparation guard); P 'phase completion lacks arrival or acknowledgement'.
- `actors: []`: R preparation issue plus "actor extension record capacity"; S "actor form carries singular projections" (`:381-382`); P several.
- More than 256 declared identities: R a lone `reply_capacity` issue (`porcelain_admission.rs:1418-1421`); S the partition message (`:297-302`); P preparation and partition errors.
- A repeated declared identity: R "phase ordinal/partition identity conflict" plus the preparation issue; S the partition message; P 'duplicate phase/action identity' plus both others.
- In general S reports the first failing guard and R and P accumulate.

## E. Driving each reader with a constructed reply

**Corpus 1 — `tests/fixtures/contract/actor_evidence.json`.** JSON array of 77 cases (16 accepted, 61 rejected); each `{name, accepted, patches: [{path, value}], fixture?, diagnostic?}`, a JSON-pointer patch list over one of seven sparse baselines `tests/fixtures/contract/actor_{authority,setup_failure,gate,override,unclocked,required,compound_failure}_reply.json` (default `actor_authority_reply.json`). One case carries `preparation_failure`: `runtime_failure_cannot_be_preparation` (rejected; the field is added to a launched, `finished` baseline with `inspection_failed`). No case is or starts from a valid preparation-failure reply. The baselines are not complete replies: `actor_authority_reply.json` has no `producer`, its phases have no `action_ids`, and it has four events and no steps.
- R: `controller/src/porcelain_actor.rs:2025-2083`, `tests::typed_setup_equipment_application_and_gate_corpus`, through `account_only` (`:2007-2024`) = `setup`, `equipment`, `application`, `gates` only. It does not call `validate`, so `preparation_failure_valid`, `identity`, `custody` and `phase_issues` are not exercised; `fixture()` sets every phase's `action_ids` to `[]` (`:1990-1992`). The one preparation case is rejected there by the equipment clause at `:839-850`. Catalog `unit/rust.unit` (`tests/suites/unit/run.sh:18`, `cargo test --bins`).
- P: `tests/suites/blackbox_e2e/extension_controls.py:184-197`, calling `validate_actor_evidence` only — not `consumer.validate`, so no partition, no `_validate_phases`, no `_validate_actors`. Reached from `tests/suites/blackbox_e2e/checker_controls.py:224-225`; catalog `blackbox_e2e/checker_controls`.
- S: not run on it. No Swift test names the file, and no Swift test decodes a reply from JSON (grep of `runner/Tests/PWRunnerCoreTests` for `JSONDecoder`: request, limits and policy-spec uses only).

**Corpus 2 — `tests/fixtures/contract/evidence_types.json`.** 24 cases (2 accepted), patches over an ordinary reply; no actor or preparation case, none touching `action_ids`. R: `porcelain_admission.rs:2558-2590` through `execution_diagnostics` (the whole Rust reader) on `reply_fixtures::ordinary_template()`. P: `extension_controls.py:45-54` through the whole consumer and `check_record`. Not S.

**Swift-authored replies.** `actorShapeDocuments()` (`runner/Tests/PWRunnerCoreTests/ActorShapeFixtures.swift:116`) includes three valid preparation-failure replies, each passed to `validateForReporting()`: `:426-433` (`resolved_plan/inconsistent_assignment`), `:468-479` and `:480-494` (`equipment/equipment_binding_refused`). All shape documents are encoded to `$PW_TEST_ARTIFACTS/porcelain-shapes/NNN.pwp` (`ContractShapeTests.swift:163-171`). `tests/suites/runner_unit/porcelain_replies.py:109-135` decodes them and compares the collected shape with the golden; that script never calls the consumer (no `validate`/`consumer` in the file), and nothing under `controller/src` reads `porcelain-shapes`. So those three replies are judged by S only. Negative control: `ActorAccountTests.swift:93-104` (a preparation failure added to a launched reply is refused). Catalog `runner_unit/pwrunner_core_unit_executable` (`tests/suites/runner_unit/run.sh:32`).

**The one existing path with all three readers.** `run_flow::tests::actor_driver_replies_cross_readers` (`controller/src/run_flow.rs:1250-1418`, `#[ignore]`, run by `tests/suites/runner_unit/run.sh:74-78`): reads Swift-produced `actor-review-{complete,setup,interrupted,transfer-interrupted,late-setup,failed-setup}.pwp` (written at `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift:87`), decodes them in Rust, applies JSON-pointer changes, runs `execution_diagnostics` on each (`:1332-1341`), then pipes the same list to `consumer.validate_fixture` in a Python child (`:1353-1366`). S has judged only the six unmodified replies (by encoding them); the changed variants are judged by R and P. None of the six is a preparation-failure reply (INFERRED from the names; `ActorReplyTests.swift` not read).

**Running the D candidates without product changes.**
- R: test code calling `porcelain_admission::execution_diagnostics(Some(&fixture_reply(json)))` as at `run_flow.rs:1333` (`fixture_reply` `:807-809`); the JSON must decode as the typed record, so a complete reply is needed, not a corpus-1 baseline.
- P: `consumer.validate_fixture(reply)` on the bare reply JSON (`consumer.py:912-913`), as at `run_flow.rs:1353-1366`.
- S: Swift test code that mutates a typed `PWRunnerRunResult` (for example the document from `ActorShapeFixtures.swift:426-433`) and calls `validateForReporting()`, or `reportedReply`/`admittedReplyData` (`ReplyFailureTests.swift:102-113`). No way was found to hand S a JSON or encoded reply.
- A complete preparation-failure baseline shared by R and P exists only as bytes: the `.pwp` files from `ActorShapeFixtures.swift` in `porcelain-shapes/`. Decoding one in Rust (`crate::porcelain::decode`, as at `run_flow.rs:1270`) gives the JSON both R and P can take. D3-D5 and D7-D10 need the changed reply built on the Swift side, because S is the reader expected to accept. D5 and D13 depend on null/absent handling in the JSON path, which was not read.

One corpus through all three readers: no. Corpus 1 and corpus 2 go through R and P (corpus 1 through a subset of each); Swift-authored documents go through S, and six of them, none a preparation failure, go on to R and P.

## Against the leads (`records/contract/claims/U11.md`, rows K-198-1 to K-202-1)

- K-198-1: agree. Addition: P does not examine the field at all on an ordinary-form reply (row 2, D11).
- K-199-1: "all three require `execution_form == "actors"`" — S has no such term in the guard; it gets there only through the actor-form dispatch (`PWRunnerReply.swift:644-648`).
- K-199-2: "non-empty `actors` (Rust, Python)" — S also requires it, at `:381`.
- K-200-1: agree on the three lists. Additions: R and P require `extension_events` present, S does not (row 9); P refuses custody rows indirectly (row 14).
- K-200-2: agree; `bounded` is now read (`porcelain_actor.rs:9-11`: nonempty, at most the byte count, no NUL). Additions: S has neither the proceed term nor the byte bound (rows 16, 20); P bounds `phase_id` in a general check that R and S lack (row 23).
- K-202-1: agree on the skip conditions. Addition: P's early return also skips the order and association clauses, which R and S keep.

## Not read

Cited or relied on without opening, or opened only in part:
- `runner/Sources/PWRunnerCore/ActorOrchestration.swift` (the producer of the refusal reply) — not opened; the "baseline" in D rests on the lead and on the Swift fixture.
- `controller/src/porcelain_actor.rs`: `scope` (`:164-368`), `application` (`:452-588`), `equipment` between `:641-829` and `:851-863`, `gates` except `:1055-1064`, `custody` after `:1201`, `equipment_bounds` (`:1730-`).
- `controller/src/porcelain_admission.rs`: `phase_issues` after `:1126`, `policy_read_issues`, `validate_lifecycle`, `reply_geometry` after `:1789`; the tests at `:1900-3293` except `:2556-2592`.
- `controller/src/run_flow.rs`: `reply_version`, `execution_envelope` (the mapping of diagnostics into the envelope).
- `controller/src/porcelain_records.rs` JSON deserialization of `PWRunnerRunResult` (null/absent handling for D5, D13).
- `runner/Sources/PWRunnerCore`: bodies of `pwRunnerEquipmentProblems`, `actorApplicationIntegrityErrors`, `terminationGateIntegrityErrors`, `dispositionIntegrityProblems`; `authoritySetupIntegrityErrors` after `:160`; `PWActorLimits` values; the porcelain encoder beyond the grep of `PWPorcelain.swift` (its text limit is the whole-reply byte limit, `:62`).
- `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift`, `ActorPlanTests.swift`; `ActorShapeFixtures.swift` outside `:396-515`.
- `tests/lib/document_versions.py`, `tests/lib/lifecycle_oracle.py` (outline only), `tests/lib/consumer.py:336-553` (`_validate_step`, exec observation) and `:849-897` (envelope).
- `tests/suites/blackbox_e2e/checker_controls.sh`, `tests/suites/unit/run.sh` and `tests/suites/runner_unit/run.sh` beyond the lines cited; how the dispatcher maps a case without its own `command` to the suite command (INFERRED for `unit/rust.unit` and `runner_unit/pwrunner_core_unit_executable`).
- Live checks named in the lead that feed real refusal replies to the Python consumer (`tests/suites/failure_boundaries/check.py`, `tests/suites/witness_contract/opt_in/check_actor_equipment.py`, `check_missing_equipment.py`) — not opened.
- Nothing under `records/contract/` other than `claims/U11.md:360-459`.

Looked for and not found:
- A constructed case, in any corpus or test read, that starts from a valid preparation-failure reply and changes one field (the cases behind D1-D10).
- A Rust test that reaches `preparation_failure_valid`: the field appears in `controller/src` only at `porcelain_actor.rs:844`, `:1066-1067`, `:1664`, `:1677-1680` and in `porcelain_records.rs`.
- A Swift check of `actors[].visits`, actor `index`, or a byte bound on `phase_id`, `actor_id` or action identities in the self-check sources searched. Whether S bounds `actor_id` bytes elsewhere was not established.
- A Python check of region rows or arrival tied to `preparation_failure`.
- Any difference between the readers on a failed-inspection actor without `launch` (S `PWRunnerReply.swift:422-435` does not require `launch`; R `porcelain_actor.rs:838-850` and P `actor_evidence.py:338` do) was noticed and not followed to a judgment, because the R equipment body between those lines was not read.
