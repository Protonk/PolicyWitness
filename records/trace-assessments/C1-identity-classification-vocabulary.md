# C1 — identity, classification and vocabulary

Read-only assessment of DT-22, DT-23, DT-24, DT-26, DT-27, DT-28, DT-30, DT-33,
DT-34, DT-35, DT-51 and DT-57 from `records/DOCUMENTATION-TRACE-REVIEW.md`,
grouped by the five coverage-map rows that own them. 49 claims are assessed.

## Pass identity and evidence classes

- Tree: `main` at `837296af`, clean at the start of the pass. Line references
  below are to this tree. The review's RESPONSE and REQUEST line numbers for
  these entries are mostly unchanged; its source line numbers have moved a
  little and are restated here.
- App used for executions: `dist/PolicyWitness.app`; `--version` reports
  `data.contract`
  `development:b55acb20d6a00395f6a422eafef1a4c18fd64e5140b71a1331cbe3b76744719e`;
  retained envelopes from the same app carry `build.commit` `2f4d76e4`.
- Evidence classes used in the tables:
  - **R-exec**: the review executed it. None of that evidence is available
    locally: the session scratchpad `…/1b7c19fb-…/scratchpad/` (DT-22–35),
    `/private/tmp/pw-failure-trace-elssragi/` (DT-51, DT-57) and
    `tests/out/runs/documentation-trace-default` (DT-30) are all absent.
  - **R-src**: the review read source. **R-pass**: a review sub-pass reported
    it and the primary review did not repeat it.
  - **src**: re-read at HEAD in this pass.
  - **exec**: executed in this pass with side-effect-free commands (publication
    commands and `sbpl-check` only; no `run`, no runner command, no build).
  - **retained**: read from `tests/out/runs/trace-instrument-after-corrected`
    (run `20261118T011154Z_5cfcec0a`, 233 passes, same app). This is gitignored
    development output with no retention guarantee. Tallies over that directory
    count every `kind: "run"` JSON document carrying a host reply (1,832 of
    them), live and constructed alike; where a value matters, a specific live
    artifact is named.
  - **constructed**: in-memory input given directly to a reader.
- One temporary file was written:
  `.tmp/trace-integration/assessments/work-C1-identity-classification-vocabulary/sbpl-request.json`.

Build-contract inputs (`docs/build_contract.py:15-27`) are `controller/src`,
`controller/tools`, `controller/interface`, `runner/Sources`, `runner/Clients`,
`runner/Services`, `runner/augments` (suffixes `.rs .c .h .swift .sb .plist
.ent`) and the named files. An edit there forces a signed rebuild; an edit under
`runner/Sources` also requires `tests/lib/python.sh
docs/generate_worker_identity.py` (`docs/generate_worker_identity.py:26`).
`docs/contract/*.surface.md`, `docs/limits.json`, `controller/README.md`,
`controller/integration/`, `runner/Tests/` and `tests/` are not inputs. Surface
shape goldens under `tests/fixtures/contract/surfaces/` carry neither prose nor
vocabulary values (checked by search), so the prose and value-list corrections
below change `docs/contract/public.json`, generated regions and current stamp
tables, and no shape golden.

---

## 1. DT-22 / DT-57 — empty ordinary step identity

### 1.1 Claims

| id | claim | boundary | holds at HEAD? | evidence class | classification |
| --- | --- | --- | --- | --- | --- |
| DT-22.a | Three request-side statements permit an empty ordinary `step_id`; the validator-line rule requires a nonempty `step_id` on allow/deny; no request-side statement mentions the interaction. | Statements; ordinary form | yes. `docs/contract/12-probes.surface.md:23` ("ordinary plans currently accept a unique empty value"), `docs/contract/13-actors.surface.md:416`, frozen guide `docs/PolicyWitness.md:235-236`; receiver rule `docs/contract/21-wire.surface.md:201`, `tests/FAILURE-PROPAGATION-CONTRACT.md:996-998`, `runner/Sources/PWRunnerCore/ValidatorClient.swift:537-540` | R-src; src | consequential ambiguity (two stated rules, each true alone, whose combination is unstated) |
| DT-22.b | An admitted request with `step_id: ""`, an eligible query and a native allow exits 1 with `validator_decode_failure`, error "allow requires step_id"; the attempt stays `ok`, order `unestablished`, query result synthetic. | One live specimen; app `8b5de2b2`; CLI | yes by source: host admission tests uniqueness only (`ProbeRunner.swift:113-118`); the native validator echoes any non-NULL ID (`sb_api_validator.c:338`); the receiver rejects the record (`ValidatorClient.swift:537-540`); classification `CWorkerDisposition.swift:415-419`. Not re-executed (`run` is outside this pass) | R-exec (unavailable); src | contradicted explicit commitment: the field is stated as "associating a query with its attempt and result" and the admitted value cannot associate an allow or deny |
| DT-22.c | The identifier rule's check-read support pins "ordinary meaning admission tests uniqueness without a nonempty condition" and cites `runReaderCorpusTests`, which constructs replies and submits no request. | Support owner; constructed reply | yes. `13-actors.surface.md:418-426`; `ReaderCorpusTests.swift:49-64` builds a no-worker reply and calls `validateForReporting`. The owner's `limits` says "constructed reader evidence" | R-src; src | overstated coverage credit, disclosed by its own limits text: the cited check reads a reply and establishes nothing about request admission |
| DT-22.d | The actor-form refusal code `empty_step_id` has one producer and no test. | Actor form; tree search | yes. Producer `ActorPlan.swift:396`; listed at `15-refusals.surface.md:82`; no occurrence under `runner/Tests`, `tests/` or `controller/integration` | R-src; src | accurate observation; an untested stated refusal |
| DT-22.e | Limit: one specimen; the planner-excluded branch was not run. | — | superseded by DT-57.a for that branch | — | qualification, preserved |
| DT-57.a | Empty ID with a planner-excluded query: exit 0, `finished`, `query_not_requested`, completed worker attempt; reply and disposition retain the empty ID; controller disposition integrity valid. | One live specimen; app `8b5de2b2` | yes by source: no validator record is requested for an excluded query (`CWorkerRequestPlanning.swift:335-336`), so the receiver rule is not reached; Swift and Rust reply readers explicitly allow the empty ordinary ID (`PWRunnerReply.swift:304-312`, `controller/src/porcelain_admission.rs:835-850`) | R-exec (unavailable); src | accurate observation |
| DT-57.b | `consumer.validate` returns `[]` and `lifecycle_oracle.check_record` returns D8 `malformed_record` "steps[0] lacks a string step_id" for the same envelope. | Python readers | yes. `tests/lib/lifecycle_adapter.py:132-133` rejects a falsy string; `tests/lib/consumer.py:860-870` requires only `str`. Reproduced here on a constructed envelope from `lifecycle_oracle.build_envelope` with both IDs set to `""`: the single finding is the D8 text above | R-exec (unavailable); src; constructed | inaccurate mechanism in a test reader: no statement requires a nonempty disposition step ID (`32-lifecycle.surface.md:902-904`, `FAILURE-PROPAGATION-CONTRACT.md:385`), and three other readers accept it |
| DT-57.c | The result is a reader disagreement distinct from DT-22's receiver refusal and from DT-50; it does not show every empty-ID specimen fails or that the oracle rejected a missing publication. | — | yes | — | qualification, preserved. In particular the oracle finding is not evidence that the request should have been refused |
| DT-57.d | (Acceptance cross-reference) The judgment is visible only in cases that run the oracle. | Registered cases | yes; callers of `lifecycle_oracle` are listed by `grep -l lifecycle_oracle tests/suites` (ten files) and no registered case submits an empty ID | R-src; src | accurate observation |

### 1.2 Comparison

Obligation as stated:

- `docs/contract/12-probes.surface.md:23` (owner; rendered at
  `docs/REQUEST.md:828`): "Caller label associating a query with its attempt and
  result. It is unique across all actions … Actor plans require it to be
  nonempty; ordinary plans currently accept a unique empty value." This sentence
  is also in the `v0.3.7` developer contract (`git grep` at that tag:
  `docs/CONTRACT.md:773`). The guide's "including an empty string when used
  once" entered after `v0.3.7` (`897be512`) and is frozen.
- `docs/contract/13-actors.surface.md:416`: "Ordinary-form action identifiers
  may be empty. Actor-form action identifiers must be nonempty so declared
  actions can be resolved in the actor schedule."
- `docs/contract/21-wire.surface.md:201` (rendered `docs/ARCHITECTURE.md:785`):
  "Allow/deny require nonempty step_id, operation and filter_type plus integer
  rc and errno."

Producer: the controller performs no step-identity admission
(`controller/src/run_flow.rs:580-596` checks JSON, the contract assertion and
selectors). The host admits through `admitSpecimen`
(`ProbeRunner.swift:202-220`); ordinary meaning admission inserts each ID into a
set and refuses only a duplicate. The planner sends the ID verbatim in the probe
line. The native validator returns it. The host receiver then rejects an allow or
deny whose `step_id` is an empty string, records a `structure` decode fault and
the classifier selects `validator_decode_failure`. A diagnostic outcome with an
empty ID is accepted (only allow/deny carry the nonempty rule), and an excluded
query sends nothing.

Readers: Swift reporting validation and Rust reply admission each carry an
explicit "ordinary may be empty" branch. The Python consumer has no nonempty
rule. The Python lifecycle adapter rejects it. No test submits an empty ordinary
ID; the reader corpus row `ordinary-empty-step` is a constructed no-worker
reply, so even there the adapter's rule is not reached (no disposition record).

Observation versus inference: the two live results are the review's and are not
re-executed. That an eligible query with a diagnostic outcome would finish is
my inference from `ValidatorClient.swift:537-544`; it was not run by anyone.

### 1.3 Plausible treatments

**A. Refuse an empty `step_id` at host admission (product behavior change).**
One identity rule for every form.

- Files: `runner/Sources/PWRunnerCore/ProbeRunner.swift` `requestMeaningFailure`
  (add the `empty_step_id` refusal beside `duplicate_step_id`);
  `PWRunnerReply.swift:306-310` (drop `allowEmpty`);
  `controller/src/porcelain_admission.rs:835-843` (drop the `empty` parameter);
  `tests/lib/consumer.py` (add the nonempty rule); surface inputs
  `12-probes.surface.md:23`, `13-actors.surface.md:373` and `:387` (condition
  tests), `:416` (definition) and `:418-426` (support); the reader-corpus row at
  `ReaderCorpusTests.swift:64` flips to a refused neighbour.
- Build-contract inputs: yes (Swift and Rust). Regenerate worker identity and
  contract destinations.
- Machinery: removes the form-specific identifier definition and the
  empty-allowed branch in two product readers; the refusal code is already
  public.
- Consequence: withdraws the `v0.3.7` statement that ordinary plans accept an
  empty value. A request that today finishes (empty ID with an excluded query or
  a diagnostic answer) becomes `bad_request`. The frozen guide sentence becomes
  false until the guide is rewritten.
- A check must reject: an ordinary request with `step_id: ""` reaching a worker
  or validator; a reply carrying an empty ordinary action ID passing any reader.

**B. Admit the identifier at the two boundaries that reject it (product behavior
change in the receiver, assertion repair in the oracle).**

- Files: `runner/Sources/PWRunnerCore/ValidatorClient.swift:537-540` (allow/deny
  require `step_id` to be a string, possibly empty; `operation` and
  `filter_type` stay nonempty) and its comment at `:464-467`; surface input
  `docs/contract/21-wire.surface.md:201`; the authored sentence at
  `tests/FAILURE-PROPAGATION-CONTRACT.md:996-998` (outside the shared regions);
  `tests/lib/lifecycle_adapter.py:132` (reject a non-string only).
- Build-contract input: yes (`ValidatorClient.swift`). Regenerate worker
  identity and contract destinations.
- Machinery: keeps the two-form identifier rule and the existing reader
  branches; changes one predicate. Association already keys on the string
  (`PWRunnerPredictionEvidence.swift:160-187`, `tests/lib/phase_evidence.py:42-47`),
  so an empty key joins like any other.
- Consequence: no admitted request changes for the worse. Every request-side
  statement, including the frozen guide sentence, stays true. The receiver's
  stated rule changes: an allow/deny record with `step_id: ""` is no longer a
  structure fault. When no empty-ID step is expected, that record becomes an
  `unexpected_id` association issue and the run ends `validator_unavailable`
  with the record retained, where today it ends `validator_decode_failure` with
  the bytes held as rejected context. No existing test pins the nonempty
  condition (search for an empty `step_id` in validator fixtures and unit tests
  found none).
- A check must reject: an admitted empty-ID specimen with an eligible native
  allow ending anywhere but `finished` with `result_source: "validator"` and
  `comparison.order: "query_first"`; an allow or deny with a null or absent
  `step_id` being accepted; an empty-ID record joining any step when the plan
  has no empty ID; two empty IDs being admitted; the oracle reporting D8 for an
  admitted empty ID.

**C. Reasoned retention.** Keep the product. Repair `lifecycle_adapter.py:132`
(as in B) and state the limit in `12-probes.surface.md` beside the field. No
build-contract input. The admitted request still cannot carry an allow or deny,
and the native answer is still discarded as a structure fault under a validator
label.

### 1.4 Recommended disposition

- **DT-22.a, DT-22.b: treatment B.** It is the smallest change after which every
  stated request-side claim is true and the admitted request does what the field
  says. It retains a native answer the host currently discards. It breaks no
  request that works today.
  This is a choice between two commitments and is the maintainer's to reverse:
  treatment A gives one rule and less reader machinery at the cost of withdrawing
  a released statement and diverging from the frozen guide. The control pair
  below serves either choice; only the expected results differ.
  Discriminating check (new, live): in `failure_boundaries` beside
  `validator_association`, an ordinary pair that differs only in `step_id`
  (`""` versus `"s"`), query `file-read-data` on an existing path, attempt
  `open_read`, policy `(version 1)(allow default)`; both must finish with an
  associated validator record, `native_rc` 0 and `query_first`. With the
  controlled validator fixture: an allow with `"step_id": null` stays a
  `structure` fault; an allow with `"step_id": ""` against a plan without an
  empty ID yields `unexpected_id` and `validator_unavailable`.
- **DT-22.c: assertion/coverage repair.** Rewrite the owner at
  `13-actors.surface.md:418-426` so its check is the new live pair and the actor
  refusal control below; keep the corpus citation only for the reply-reader
  claim it supports.
- **DT-22.d: coverage repair.** Add an actor-form request with one empty action
  ID to `runner_outcome_bad_request/accepted_input_contract`
  (`tests/suites/runner_outcome_bad_request/contract.py`), expecting
  `bad_request`, `request_failure.code: "empty_step_id"`, the action path, and
  no actor launch. Further evidence would not change this: the code is public
  and unexercised.
- **DT-22.e, DT-57.c: retained as qualifications.** They limit what the two live
  observations establish.
- **DT-57.a: no change** under B (the result is the stated behavior).
- **DT-57.b: assertion repair** (`lifecycle_adapter.py:132`), required under B
  and C. Discriminating check: the constructed envelope used in this pass,
  added to `blackbox_e2e/checker_controls` as an accepted control beside a
  rejected neighbour whose `step_id` is not a string.
- **DT-57.d: no separate change.** The crediting question belongs to the
  DT-53/132/135 row.

### 1.5 Resulting user duties

Under B: none. Until it lands, an ordinary plan should not use an empty
`step_id` when the query can return allow or deny; a `validator_decode_failure`
whose fault message is "allow requires step_id" or "deny requires step_id"
reports that case and says nothing about the policy or the validator binary.

### 1.6 Implementation worklist

1. `runner/Sources/PWRunnerCore/ValidatorClient.swift`: in
   `validatorStructureError`, require a string `step_id` for allow/deny and keep
   the nonempty test for `operation` and `filter_type`; correct the noun in the
   comment at `:466`.
2. `tests/lib/lifecycle_adapter.py:132`: reject only a non-string.
3. `docs/contract/21-wire.surface.md:201`: "Allow/deny require a string step_id,
   nonempty operation and filter_type plus integer rc and errno."
   `tests/FAILURE-PROPAGATION-CONTRACT.md:996-998`: the same correction.
4. `docs/contract/13-actors.surface.md:418-426`: support owner as in DT-22.c.
5. Controls: the live pair and fixture rows in
   `tests/suites/failure_boundaries/check.py`; the actor refusal in
   `tests/suites/runner_outcome_bad_request/contract.py`; the oracle control in
   `tests/suites/blackbox_e2e/checker_controls.py`; a unit row in
   `runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift` for the three
   record forms. Update `tests/COVERAGE.md` and the suite READMEs.
6. Regenerate: `tests/lib/python.sh docs/generate_worker_identity.py`, then
   `tests/lib/python.sh docs/generate_contract_stamps.py`.
7. Verify on the rebuilt app through the "Admission or validator receivers"
   route of `tests/CHANGE-VERIFICATION.md`: `failure_boundaries`, `runner_unit`,
   `runner_abi_layout`, `runner_c_worker_harness`, `unit`,
   `runner_validator_failure`, `runner_outcome_bad_request`,
   `blackbox_e2e/checker_controls`, `source_drift`. The eligibility predicate is
   unchanged but its input domain widens, so also run
   `witness_contract/order_barrier_mutations`.

---

## 2. DT-23 / DT-51 — declared-unapplied actor classification

### 2.1 Claims

| id | claim | boundary | holds at HEAD? | evidence class | classification |
| --- | --- | --- | --- | --- | --- |
| DT-23.a | One actor, one phase, one `read_fresh` probe, validator path nonexistent: `mode: "unapplied"` gives exit 0, `ok: true`, `finished`, host `rc` 0; an applied policy gives exit 1, `validator_spawn_failed`. Both carry `collected`, `not_spawned`, a `validator_spawn_failure` record and `unestablished`. The ordinary form also gives `validator_spawn_failed`. | Live pair; app `8b5de2b2`; CLI | yes by source (mechanism below). Not re-executed | R-exec (unavailable); src | contradicted explicit commitment |
| DT-23.b | `assembleActorReply` classifies each phase with the actor's raw output and keeps the result only when its outcome begins with `validator`; `classifyActor` substitutes `applied = true` for a declared-unapplied actor and the phase call does not. | Host source | yes. `ActorOrchestration.swift:278-285` (substitution), `:370-374` (phase call and prefix filter). For raw unapplied output the classifier returns `runner_failed` at `CWorkerDisposition.swift:352-355` (or `:369-370`) before the validator section at `:400` | R-src; src | accurate mechanism account |
| DT-23.c | No statement or test says whether the difference is intended. | Tree | yes. The source comment at `ActorOrchestration.swift:313-314` states the ladder as "actor failures in actor order, then validator failures and collection exhaustion in schedule order, then cancellation", with no exception. Both call sites entered in `c686a05f`. The support owner says the actor ladder has "source support here, without new integrated execution credit" (`30-reply.surface.md:218`) | R-src; src | accurate observation |
| DT-23.d | By the same path other validator outcomes for an unapplied actor's phase would not be selected (not run). | Inference from source | yes, and wider than one outcome: every result of the validator section (`validator_spawn_failed`, `validator_decode_failure`, `validator_no_reply`, and `validator_unavailable` from disposition, association or count) is unreachable for an unapplied actor's phase. The separate status rule at `ActorOrchestration.swift:375-378` (`budget_exhausted`, `clock_unavailable`) still applies | R-src (inference); src | supported inference; decode confirmed live by DT-51.a, the rest by source only |
| DT-51.a | Validator fixture printing `{not JSON}`: applied gives exit 1, `validator_decode_failure`; unapplied gives exit 0, `finished`, `ok: true`, null error. Same phase evidence in both (reaped validator, JSON fault at byte 0, completed worker attempt). | Live pair; app `8b5de2b2`; controlled validator, real host decoding and worker | yes by source. Not re-executed | R-exec (unavailable); src | contradicted explicit commitment |
| DT-51.b | Both envelopes pass `consumer.validate` and the lifecycle oracle; the readers do not recompute the aggregate outcome. | Python readers | yes. `tests/lib/consumer.py:1060-1081` checks only that the envelope's outcome, `ok` and exit follow the reply's outcome; `tests/lib/actor_evidence.py:369` relates `finished` only to equipment refusal. Rust has no such relation either (search of `porcelain_admission.rs` for `"finished"`) | R-exec; src | accurate observation: no reader enforces the commitment |
| DT-51.c | Same source asymmetry as DT-23. | Host source | yes | src | accurate mechanism account |
| DT-51.d | The failure contract says run-level framing/association gaps fail the run and assigns receiver JSON failures to `validator_decode_failure`. | Statements | yes. `tests/FAILURE-PROPAGATION-CONTRACT.md:1024-1026` and `:1045-1049`, both unqualified and outside the shared regions | src | contradicted explicit commitment |
| DT-51.e | Limit: not evidence about every actor schedule; the native query was replaced by fixture output. | — | yes | — | qualification, preserved |

### 2.2 Comparison

Obligation as stated (`docs/contract/30-reply.surface.md`, rendered
`docs/RESPONSE.md:417-432`):

- `:197` `finished`: "Execution and required collection completed under the
  classifier's conditions; each attempt retains its own result."
- `:203` `validator_spawn_failed`: "Worker classification succeeded and
  validator spawn failed." `:205` `validator_decode_failure`: "Worker
  classification succeeded and validator parsing or typed decoding failed."
- `:188-191`: "If the worker side remains successful, the first unsuccessful
  phase collection selects the summary; all collection records remain. Actor
  orchestration reports each actor and selects an aggregate outcome."
- `tests/FAILURE-PROPAGATION-CONTRACT.md:1026`: "Run-level framing/association
  gaps do fail it."

Producer: the ordinary form passes the worker result and each phase's validator
result to one classifier call (`CWorkerOrchestrator.swift:194-200`). The actor
form classifies each actor first; a declared-unapplied actor is judged through a
view with `applied = true`. It then classifies each phase with the raw output.
For an applied actor that call reaches the validator section. For an unapplied
actor it returns `runner_failed` ("completed without an observed application"),
which the prefix filter discards. When the actor has no output at all the same
call already substitutes an applied placeholder (`:371`). The phase call was
therefore written to reach the validator section; the raw unapplied output is
the one input that does not.

The per-step and per-phase evidence is the same and truthful in both modes. Only
the aggregate (`normalized_outcome`, host `rc`, `result.ok`, exit status) differs.

Readers and tests: no reader relates the aggregate to phase faults. Registered
cases exercise the failures only in the ordinary form:
`witness_contract/validator_spawn_failed_reports_degraded`
(`check_ordering.py:272-284`),
`runner_validator_failure/validator_decode_failure_reports_degraded`,
`runner_validator_failure/validator_unavailable_reports_degraded`,
`runner_outcome_validator_no_reply/validator_io_deadline_releases_worker` and
`failure_boundaries/validator_frames`. `HostOutcomeClassifierTests` drives the
classifier with constructed inputs and never calls `assembleActorReply` with a
validator failure. No registered case runs an actor-form validator failure for
an applied actor either. In the retained run, 144 actor-form envelopes contain
one collected phase owned by an unapplied actor and no phase with a validator
fault of any kind (retained; counts include constructed documents).

### 2.3 Plausible treatments

**A. Classify an unapplied actor's phases through the declared-setup view
(product behavior change).** Use one classifier view per actor for both the
actor call and the phase call. With the same view and the same resolved
disposition, the worker side of the phase call returns what the actor call
already returned, so the `validator` prefix filter at `:374` has nothing left to
discard on the worker side; see the first note under "Outside the review" for
what it still discards.

- Files: `runner/Sources/PWRunnerCore/ActorOrchestration.swift` (`classifyActor`
  and the phase call at `:370-374`); surface input
  `docs/contract/30-reply.surface.md:188-191` and its support owner at
  `:209-219`; `tests/COVERAGE.md` validator rows.
- Build-contract input: yes. Regenerate worker identity and contract
  destinations.
- Outcome and summary after the change: an unapplied actor's phase carries the
  same aggregate as an applied actor's for the same validator result. Failed
  spawn: `validator_spawn_failed`, `rc` 1, `ok: false`, exit 1. Failed decode:
  `validator_decode_failure`. Failed read or probe write: `validator_no_reply`.
  Unusable disposition, association or count: `validator_unavailable`. Per-step
  and per-phase evidence is unchanged.
- Consequence: an actor-form run in which an unapplied actor's collection failed
  changes from exit 0 to exit 1. No request form, record shape or vocabulary
  changes. No envelope in the retained run would change (0 of 144).
- A check must reject: `finished`, `ok: true` or exit 0 beside a phase that
  carries `validator_spawn_failure`, a `decode_fault` or an I/O error, whatever
  the owning actor's mode.

**B. Reasoned retention.** State in `30-reply.surface.md` that a declared-unapplied
actor's collection failure does not change the aggregate, and qualify
`FAILURE-PROPAGATION-CONTRACT.md:1026` and `:1045-1049`. No build input. `finished`
would then not mean that required collection completed.

**C. Assertion repair alone.** Add the necessary condition "a `finished` reply has
no phase with a spawn failure, decode fault or validator I/O error" to
`tests/lib/consumer.py`. It makes the defect visible to a reader and does not
repair it.

### 2.4 Recommended disposition

- **DT-23.a, DT-51.a, DT-51.d: treatment A.** The statements are unqualified,
  the source states the intended ladder, the phase call already substitutes an
  applied placeholder for missing output, and exit 0 with `finished` hides a
  failed prediction collection from every caller that reads only the summary.
  Retention would withdraw a commitment through its account.
- **DT-23.b, DT-51.c: accurate; no account change** beyond A.
- **DT-23.c: account correction with A.** State the actor ladder in
  `30-reply.surface.md:188-191` in the source comment's terms, for both modes.
- **DT-23.d: covered by A.** The control exercises spawn and decode; the other
  validator outcomes share the one classifier section and the ordinary-form
  cases above already exercise them. More live rows would not change the
  decision.
- **DT-51.b: treatment C in addition**, as the reader-side assertion that the
  live control uses. It is a necessary condition taken from the `finished`
  statement and does not reproduce the classifier.
- **DT-51.e: retained as a qualification.**

Discriminating check (new, live), four specimens through the CLI in
`runner_validator_failure`: one actor, one phase, one `open_read` probe on an
existing file, with `sandbox.mode` either `apply` (allow-default policy) or
`unapplied`, and the validator either a nonexistent path or the existing
transcript fixture returning `{not JSON}`. Each must give exit 1, `ok: false`,
the applied row's outcome, `actors[0].setup_status` `applied` or
`unapplied_declared`, a completed worker attempt and `unestablished`. An
all-success unapplied row must stay `finished`. The validator substitution is
one of the eight controls moving to `test-input run`
(`records/TRACE-MANAGEMENT-PLAN.md` "Bounded test-seam migration"); write the
control against the route current when it lands and add it to the caller map.

### 2.5 Resulting user duties

After A: none. Until then, for an actor-form run, exit 0 and `finished` do not
establish that an unapplied actor's queries were collected; read each phase's
`validator_spawn_failure`, `validator_subprocess.decode_fault` and
`ordering.validator_disposition`.

### 2.6 Implementation worklist

1. `ActorOrchestration.swift`: factor the declared-setup view out of
   `classifyActor` (`:278-285`) and pass it to the phase call (`:371`) when the
   actor does not apply and its setup is declared. Decide the prefix filter at
   `:374` in the same edit (first note under "Outside the review").
2. `docs/contract/30-reply.surface.md:188-191`: state the actor ladder; update
   the support owner's `check`, `pins` and `limits` at `:209-219`.
3. `tests/lib/consumer.py` `_validate_result`: the necessary condition of
   treatment C, with accepted and rejected controls in
   `tests/suites/blackbox_e2e/checker_controls.py`.
4. New case in `tests/suites/runner_validator_failure/` and `tests/catalog.json`;
   a constructed unit row in `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift`
   calling `assembleActorReply` with an injected `.failure(.spawnFailed…)` for
   an unapplied and an applied actor. Update `tests/COVERAGE.md`.
5. Regenerate worker identity and contract destinations.
6. Verify: `runner_unit`, `runner_validator_failure`, `failure_boundaries`,
   `blackbox_e2e/checker_controls`, and the actor route of
   `tests/CHANGE-VERIFICATION.md` ("Actor composition, re-delegation and timing
   qualification": `witness_contract/actor_compositions`,
   `witness_contract/extension_redelegation`,
   `witness_contract/actor_timing_qualification`), then `source_drift`.

---

## 3. DT-24 / DT-30 — query meanings and response vocabulary

Three sets are kept apart for each field: values the producer assigns, values a
reader accepts, and values the statement lists.

### 3.1 Claims

| id | claim | boundary | holds at HEAD? | evidence class | classification |
| --- | --- | --- | --- | --- | --- |
| DT-24.a | `missing_reason` is stated as `validator_not_invoked` "when collection never ran"; the host assigns it whenever the phase has no validator output object, including a failed spawn in a `collected` phase. | Step query record; ordinary and actor | yes. Statement `31-steps.surface.md:63`; assignment `CWorkerStepResults.swift:50-53`; output is nil for every pre-spawn failure (`ValidatorClient.swift:188-252`). Live: `witness_contract/validator_spawn_failed_reports_degraded` in the retained run has `validator_not_invoked` beside `collected` and `not_spawned`; 21 such steps in the tally | R-exec; src; retained | inaccurate mechanism account. `FAILURE-PROPAGATION-CONTRACT.md:852-853` ("no validator process") is accurate |
| DT-24.b | `pid` is stated as the PID "targeted by this phase's validator collection"; it is the worker PID whenever worker output exists, including an excluded query in a `not_needed` phase with no validator. | Step query record | yes. Statement `31-steps.surface.md:75`; `CWorkerStepResults.swift:24`, `:104-108`. Live: `witness_contract/phases/artifacts/ordinary/run.json` in the retained run has `query_not_requested`, `pid` equal to the worker PID, `not_needed`, no validator subprocess; 339 such steps in the tally | R-exec; src; retained | inaccurate mechanism account |
| DT-24.c | (Acceptance cross-reference) With a duplicate-ID pair the step carries `validator_no_verdict` and "no validator verdict for this step"; the reason fits its definition and the error text does not distinguish ambiguous association from absent output. | Step query record; controlled transcript | yes by source (`CWorkerStepResults.swift:113-124`); the phase's `association_issues` carries the distinction | R-exec; src | accurate observation needing no change |
| DT-30.a | Equipment diagnostic `operation` lists eleven names; the host constructs errors with seven; `service_seal` has no producer; three names occur only as native observations; both product readers accept all eleven. | `PWRunnerEquipmentError.operation` | yes. Statement `34-equipment.surface.md:400`. Assigned: `signing_information`, `worker_signature`, `inventory_read`, `inventory_decode`, `worker_path`, `worker_hash`, `worker_entitlements` (`ActorEquipment.swift:221-254`, `:334-357`, `:389-447`). Accepted: eleven (`PWRunnerEquipment.swift:146-149`, `controller/src/porcelain_actor.rs:1758-1771`). A failed service-seal inspection carries the static inspection's own error, named `worker_signature` or `signing_information` (`ActorEquipment.swift:324-329`). Retained tally: only `worker_path` | R-src; src; retained | inaccurate mechanism account: four listed values are accepted and never assigned to this field |
| DT-30.b | Transfer `status` lists ten "Host acknowledgement" names; the host assigns seven; `host_timeout` and `clock_fault` are worker-side; `none` is an initial value replaced on every path. | `PWRunnerTransferRecord.status` | yes. Statement `14-extensions.surface.md:685`; assignments `AuthorityCustody.swift:513-606`; names `PWRunnerActors.swift:99-106`. The same names do reach a neighbouring field: the transfer event's `status` is the worker's published answer (`ActorOrchestration.swift:402`), and the retained tally has `host_timeout` twice there and never in a transfer record | R-src; src; retained | inaccurate mechanism account: three listed values belong to another field |
| DT-30.c | `collection_basis` lists `unavailable`; the one assignment selects between the other two. | Worker subprocess record | yes. Statement `32-lifecycle.surface.md:100`; assignment `ActorSession.swift:629`; accepted by `PWRunnerDisposition.swift:20` and `tests/lib/lifecycle_contract.py:101`. Retained tally: two values, or absent | R-src; src; retained | inaccurate mechanism account: one listed value is accepted and never assigned |
| DT-30.d | `cleanup_trigger` lists six values; the assignment falls back to the poll stop reason, and the actor scheduler writes its own reasons there. | Worker subprocess record; actor form | yes. Statement `32-lifecycle.surface.md:92`; assignment `ActorSession.swift:626`; scheduler reasons `ActorScheduler.swift:249-275`, `:472`, `:545-562`. Live: `witness_contract/actor_compositions/artifacts/gate_cancels_schedule/run.json` in the retained run has `schedule_complete` on all three actors. The tally adds `authority_setup_failed`, `died_before_arrival`, `died_before_completion` and `setup_failed` | R-exec; R-pass (the six further values); src; retained | inaccurate mechanism account: emitted values the statement omits |
| DT-30.e | `bad_policy` is stated in the present tense; public admission refuses a missing source or wrong format as `bad_request` first. | Host outcome | yes. Statement `30-reply.surface.md:199`; the branch `PWRunnerService.swift:376-394` follows `admitSpecimen`, whose `policyMeaningFailure` (`ProbeRunner.swift:54-63`) refuses the same two conditions; `tests/COVERAGE.md:18` calls it defensive | R-src; R-pass (the two refusals); src | inaccurate mechanism account: a defensive branch stated as a reachable outcome |
| DT-30.f | None of these fields declares a closed vocabulary; each list is prose. | Surface declarations | yes for all five | src | qualification, preserved: no exhaustiveness declaration is broken |
| DT-30.g | `decode_fault.kind` is declared closed and exhaustive while no reader rejects another value (not re-verified by the review). | Phase validator record | yes, now verified by search. Declaration `32-lifecycle.surface.md:1269-1273`; the producer assigns three (`ValidatorClient.swift:495-504`); no occurrence of the field in `tests/lib/*.py` reader code, `porcelain_admission.rs` or Swift reporting validation. `docs/CONTRACT.md:478-482` says a closed vocabulary's rule "names the component and boundary that identifies another value as invalid" | R-pass; src | consequential ambiguity: a closed declaration with no rejecting boundary |

### 3.2 Comparison

For DT-24 the statements are narrower than the producer. "When collection never
ran" omits a collection that ran and could not start a validator;
`collection_status` is defined so that `collected` "identifies an invoked
collection even when validator I/O or decoding later fails"
(`33-actor_evidence.surface.md:443`), so the two fields disagree as written.
`pid` describes a collection target, while the value is recorded whether or not
any collection addressed that PID. Readers: the consumer requires `pid` to equal
the worker's only inside its order check (`consumer.py:280`) and checks
`missing_reason` only for exclusions (`consumer.py:561`). Three live checks
assert `validator_not_invoked` where collection did not run
(`check_worker_evidence.py:63`, `check_pre_apply_failure.py:96`,
`check_actor_compositions.py:271`); the spawn-failure check
(`check_ordering.py:272-284`) does not assert the reason.

For DT-30 each list mixes the three sets:

| field | assigned by a producer | accepted by a reader and never assigned | emitted and unlisted |
| --- | --- | --- | --- |
| equipment `operation` | 7 | `service_seal`, `guest_code`, `dynamic_validity`, `associated_static_code` | none |
| transfer record `status` | 7 | `none`, `host_timeout`, `clock_fault` (assigned only to the event's `status`) | none; an unrecognized raw number is kept as a string |
| `collection_basis` | 2 | `unavailable` | none |
| `cleanup_trigger` | 6 mapped, plus every scheduler stop reason | — | `schedule_complete` and the setup and visit failure names |
| `normalized_outcome: bad_policy` | defensive branch only | — | — |
| `decode_fault.kind` | 3 | no reader constrains it | none |

### 3.3 Plausible treatments

For every row the candidates are correction of the account in its owner, or a
product change that makes the list true (narrow a reader, assign the unassigned
value, or map the unlisted ones). None of the account corrections touches a
build-contract input. Regeneration is `tests/lib/python.sh
docs/generate_contract_stamps.py`.

- DT-24.a, DT-24.b: correct `31-steps.surface.md:63` and `:75`. A product
  change (a fourth reason for a failed spawn, or a null `pid` for excluded
  queries) would alter values that live checks assert and the frozen guide
  describes correctly.
- DT-30.a: correct `34-equipment.surface.md:400`; or assign `service_seal` at
  `ActorEquipment.swift:324-329` so a failed service inspection is named for the
  object inspected (build input; readers already accept the value).
- DT-30.b, DT-30.c: correct `14-extensions.surface.md:685` and
  `32-lifecycle.surface.md:100`; or narrow the readers (build input for Swift
  and Rust).
- DT-30.d: correct `32-lifecycle.surface.md:92`; or map scheduler reasons, which
  is DT-121's subject.
- DT-30.e: correct `30-reply.surface.md:199`; or remove the outcome (changes a
  public vocabulary and the controller's result relation).
- DT-30.g: add a rejecting check to the independent consumer
  (`tests/lib/consumer.py`); or add it to Swift reporting validation and Rust
  admission (build inputs); or restate the declaration.

### 3.4 Recommended disposition

- **DT-24.a: account correction.** Text for `31-steps.surface.md:63`:
  "`query_not_requested` for a planner exclusion; `validator_not_invoked` when no
  validator process supplied output for the phase, whether collection never ran
  or it ran and could not start one; `validator_no_verdict` when a validator ran
  and produced no uniquely associated record." Existing discriminating check:
  `witness_contract/validator_spawn_failed_reports_degraded`; add the
  `missing_reason` assertion to `check_ordering.py` `spawn_failed`.
- **DT-24.b: account correction.** Text for `:75`: "Worker PID recorded for this
  step when worker output exists, including for a query the planner excluded.
  Whether a collection addressed that PID is stated by the phase's
  `collection_status` and `validator_subprocess`." Existing check:
  `witness_contract/phases`; add the excluded-step `pid` assertion to
  `check_phases.py`.
- **DT-24.c: no change.** The distinction is carried by
  `phases[].validator_subprocess.association_issues`.
- **DT-30.a: account correction.** State the seven assigned names, that product
  readers also accept the other four, and that an error in
  `equipment_inventory.error` after a failed service-seal inspection names the
  static inspection call. The product alternative is real and small; it is not
  recommended here because the record's location and `seal_osstatus` already
  identify the inspected object and no reader depends on the name.
- **DT-30.b: account correction.** List the seven host answers for the transfer
  record; say that `host_timeout` and `clock_fault` are the source worker's own
  wait results and appear in the transfer event's `status`; drop `none`.
- **DT-30.c: account correction.** "`after_confirmed_reap` or
  `execution_may_continue`; absent when the host recorded no basis. Readers also
  accept `unavailable`, which no producer assigns."
- **DT-30.d: account correction, worded after the DT-46/120/121/129 row
  decides the mapping.** If that row leaves the fallback, the field needs an
  open vocabulary block in the form `poll_stop_reason` uses
  (`32-lifecycle.surface.md:64-70`) and the statement that an actor-form reply
  carries the scheduler's stop reason unmapped. I have not chosen the wording
  because it depends on that decision.
- **DT-30.e: account correction.** "Defensive: the host's policy-hash step could
  not identify the ordinary source after admission. Admission refuses a missing
  source or another format as `bad_request` first, so no admitted request
  reaches it." More evidence would not change this: the two conditions and the
  guard are the same two tests in source.
- **DT-30.f: retained as a qualification.**
- **DT-30.g: assertion repair in the independent consumer, and a stated limit.**
  The controller admits only a reply from its own build, whose producer has
  three assignments, so a product-side rejection would be unreachable. Limit
  sentence for the field's support owner: "The host receiver assigns only these
  three kinds. Product recipients do not re-check the value; the independent
  consumer rejects any other." Check: rejected control in
  `blackbox_e2e/checker_controls`.

### 3.5 Resulting user duties

- Do not read `missing_reason: "validator_not_invoked"` as "collection did not
  run"; read the phase's `collection_status` and `validator_spawn_failure`.
- Do not read a non-null `sandbox_check.pid` as evidence that a validator
  queried that process.
- Treat an unfamiliar `cleanup_trigger` in an actor-form reply as the recorded
  scheduler stop reason and nothing more.
- Do not branch on `service_seal`, `guest_code`, `dynamic_validity` or
  `associated_static_code` in an equipment error, on `unavailable` in
  `collection_basis`, or on `bad_policy`; no current producer supplies them.

### 3.6 Implementation worklist

1. `docs/contract/31-steps.surface.md:63`, `:75`.
2. `docs/contract/34-equipment.surface.md:400`.
3. `docs/contract/14-extensions.surface.md:685`.
4. `docs/contract/32-lifecycle.surface.md:100`; `:92` after the DT-121 decision;
   the `decode_fault` support owner's `limits`.
5. `docs/contract/30-reply.surface.md:199`.
6. `tests/lib/consumer.py`: `decode_fault.kind` membership; controls in
   `tests/suites/blackbox_e2e/checker_controls.py`. Two added assertions in
   `tests/suites/witness_contract/check_ordering.py` and `check_phases.py`.
7. `tests/lib/python.sh docs/generate_contract_stamps.py`.
8. Verify: `source_drift` (`build_contracts`, `generator_contract`),
   `blackbox_e2e/checker_controls`, `witness_contract/phases`,
   `witness_contract/validator_spawn_failed_reports_degraded`.

---

## 4. DT-26 / DT-27 / DT-28 — refusal names and publication

Codes, command-line behavior and output completion are assessed separately.

### 4.1 Claims

| id | claim | boundary | holds at HEAD? | evidence class | classification |
| --- | --- | --- | --- | --- | --- |
| DT-26.a | The augment rule says "Invalid names produce `invalid_augment_name`"; the controller refuses with `invalid_value`; the other occurrence of the string is an integration test's name, whose body asserts `invalid_value`. | Controller augmentation; `run` | yes. Statement `11-policy.surface.md:152` (rendered `docs/REQUEST.md:785`; present at `v0.3.7`); producer `controller/src/augments.rs:238-248`; test `controller/integration/cli_contract.rs:1395-1430`. `v0.3.7` also produced `invalid_value` | R-src; src | contradicted explicit commitment (a named code that has never been produced) |
| DT-26.b | `augments: ["../x"]` gives exit 1, `bad_request`, code `invalid_value` at `["policy","augments","0"]`. | Live; sub-pass | consistent with source; the integration test asserts the code for `["../etc/passwd"]` and not the path | R-pass; src | accurate observation |
| DT-27.a | A file with `runner.mode: "byoxpc"` run with `--runner-mode standard` exits 1, `bad_request`, `request_failure` `conflicting_selector` at `["runner","mode"]`; the code is in no document. | Controller selector processing | yes by source: `controller/src/run_flow.rs:498-505`. The code appears only in source and in `controller/integration/interface_cases.json:1111`, `:1131`. Not re-executed | R-exec (unavailable); src | emitted value the documents omit |
| DT-27.b | Selector precedence states two refusal conditions and not this third. | Statement | yes. `10-request.surface.md:441`; the two stated conditions are produced at `controller/src/runner_select.rs:207-223` with the same code at the root path and are asserted by the two interface cases; the third has only a unit test on its message (`run_flow.rs:2392-2395`) | R-src; src | inaccurate mechanism account (omitted branch) |
| DT-27.c | The controller refusal `code` list ends in `admission_refused`, which no controller source produces; the controller passes ten codes. | Controller refusal record | yes. List `15-refusals.surface.md:138`. Controller codes re-enumerated: `invalid_json`, `missing_value`, `type_mismatch`, `missing_field`, `unsupported_contract` (`request_patch.rs:50-95`), `unknown_field`, `invalid_value`, `conflicting_selector` (`runner_select.rs`, `run_flow.rs:485-501`), `augment_unavailable`, `missing_policy_source` (`augments.rs:224-260`). `admission_refused` is assigned only by the host (`CWorkerRequestPlanning.swift:308-316`) | R-src; src | inaccurate account: a displayed example the producer never emits, and four emitted codes it omits |
| DT-27.d | The field is open and illustrative, so no exhaustiveness claim is broken. | Declaration | yes | src | qualification, preserved |
| DT-28.a | The version statement gives exit 0 after successful rendering or 2 on a rendering error; with a reader-less stdout `--version` panics and exits 101, while `example` prints "failed to write stdout" and exits 2. | Publication; reader-less pipe | yes. Statement `00-identity.surface.md:797`. Executed here: `--version` and `version` exit 101 with "failed printing to stdout: Broken pipe (os error 32)"; `example` and `test-input read` exit 2 with their one line; `help` exits 2 with empty stderr. Source: `json_contract.rs:118-126` uses `println!` | R-exec; exec; src | contradicted explicit commitment for the case rendering succeeded and the write failed |
| DT-28.b | `run` and `sbpl-check` also exit 101 (sub-pass); no developer document mentions 101. | Same | yes for `sbpl-check`, executed here (`--help` and `--request FILE` both 101). `run` by source only: `run_flow.rs:190`, `:514`. Every runner command prints through the same function (`runner_commands.rs:82`, `:451`, `:458`, `:502`, `:638`, `:689`, `:747`, `:868`). No technical document states 101 | R-pass; exec (helper); src | inaccurate account by omission; for `run` the envelope field says the exit is 0, 1 or 2 (`40-envelope.surface.md:96-100`) |
| DT-28.c | `example` "Process exit 0 supplies the complete document" and `test-input` "Process exit 0 establishes complete publication"; with stdout closed at launch both exit 0. | Publication; fd 1 closed at launch | yes. Statements `10-request.surface.md:194`, `:229`. Executed here: every publishing command exits 0 with empty stderr | R-exec; exec | consequential ambiguity: true of the stream the process holds, and no document reaches the caller |
| DT-28.d | The cited controls close stderr at launch, not stdout. | Support owners | yes. `cli_contract.rs:408-423`; the owners' `pins` and `limits` say stderr | R-src; src | accurate observation; the support text does not overstate |
| DT-28.e | The observation records the launch condition and exit status; the descriptor's state at publication was not inspected; it does not establish a failed write reported as success. | — | narrowed here: `sbpl-check --request -` launched with fd 1 closed holds `/dev/null` open read-write on fd 1 before it reads its input (`lsof`: `1u CHR 3,2 /dev/null`). Observed on the helper only; the controller binary is built with the same toolchain and exits too quickly to inspect | exec | qualification, preserved and narrowed: no write fails; the runtime supplies a discarding descriptor |

### 4.2 Comparison

**Codes.** `11-policy.surface.md:152` names a code that neither HEAD nor
`v0.3.7` produces. `10-request.surface.md:441` states two of the three selector
refusals and names no code. `15-refusals.surface.md:138` copies the host list
into the controller record. The frozen guide names none of these codes.

**Command-line behavior under a write failure.** Publishers fall into two
groups:

| command | writer | reader-less pipe (observed unless noted) | stated |
| --- | --- | --- | --- |
| `help` | `write_all` + `flush` (`help.rs:27-33`) | exit 2, empty stderr | `controller/README.md:73` |
| `example` | `write_all` + `flush` (`example.rs:58-60`) | exit 2, one line | `10-request.surface.md:194` |
| `test-input read` | `write_all` + `flush` (`test_input.rs:73-75`) | exit 2, one line | `10-request.surface.md:229-234` |
| `--version`, `version` | `println!` | exit 101, panic text | exit 0 or 2 (`00-identity.surface.md:797`) |
| `run` | `println!` (`run_flow.rs:514`, `:190`) | exit 101 by source; not run | exit 0, 1 or 2 |
| `runner …` (seven commands) | `println!` through `print_envelope` | exit 101 by source; not run | not stated |
| `sbpl-check` | `println!` (`sbpl-check.rs:388`, `:444`) | exit 101 | not stated |

For `runner install`, `remove` and `validate` the registry and launchd changes
precede the write, so a failed write follows completed machine changes. That is
a consequence of the same mechanism, read from source, not a separate finding.

**Output completion with stdout closed at launch.** Every publisher exits 0. No
write fails, because the process holds `/dev/null` on descriptor 1. "Complete
publication" is true of that stream and delivers nothing.

### 4.3 Plausible treatments

- DT-26: correct the code name in `11-policy.surface.md:152`; or change the
  producer to emit `invalid_augment_name` (build input; changes a code that
  `v0.3.7` emitted and the integration test asserts).
- DT-27: correct `10-request.surface.md:441` and the controller `values` list at
  `15-refusals.surface.md:138`. No product candidate.
- DT-28.a/b: (1) product change: write envelopes with a checked write and flush,
  and map a failure to exit 2 with one stderr line, as the three sibling
  publishers do. Files `controller/src/json_contract.rs` (shared with the
  helper), `run_flow.rs:190`, `:514`, `cli.rs:50-57`, `bin/sbpl-check.rs:388`,
  `:444`; all build inputs. (2) account correction only: state exit 101 in the
  four owners.
- DT-28.c/e: a stated limit beside the two exit-0 sentences; a product change
  (refusing a discarding stdout) is not a real candidate, since redirecting to
  `/dev/null` is an ordinary invocation.

### 4.4 Recommended disposition

- **DT-26.a: account correction** to `invalid_value`. The plan already places
  DT-26 in its account-correction thread; the producer, the released behavior
  and the test agree. Existing discriminating check: `integration/cli.integration`
  (`invalid_augment_name_rejected_as_bad_request`). Add the path assertion
  `["policy","augments","0"]` there, which also supports DT-26.b.
- **DT-26.b: no change.**
- **DT-27.a, DT-27.b: account correction.** Text for the rule: "Refuse with
  `conflicting_selector`: standard mode with an external selector, or byoxpc
  mode without an ID or service (at the root path), and a `--runner-mode` value
  that differs from the file's nested `runner.mode` (at `runner.mode`)." Check:
  the two existing interface cases, plus one new case in
  `controller/integration/interface_cases.json` for the third condition
  asserting code and path (regenerate joins with `tests/lib/python.sh
  docs/generate_interface.py`).
- **DT-27.c: account correction.** Replace the controller record's `values` with
  the ten controller codes; keep it open and illustrative.
- **DT-27.d: retained as a qualification.**
- **DT-28.a, DT-28.b: product change (1).** The build already commits to, and
  tests, exit 2 without a panic for three publishers
  (`example_write_failures_exit_2_without_a_panic`), and the envelope's
  `exit_code` statement enumerates 0, 1 and 2. The account-only alternative
  would make a runtime panic status part of the stated behavior of the remaining
  commands. If the product change is declined, the limit sentence is: "When
  standard output cannot be written, `version`, `run`, the `runner` commands and
  `sbpl-check` end with exit status 101 and a runtime panic message on standard
  error; no envelope is delivered and no `result.exit_code` describes that
  status."
  A check must reject: any status other than 2, or more than one stderr line,
  from `--version`, `version`, `sbpl-check --help` and a `run` that ends before
  runner selection, each with a reader-less stdout; and a changed status when
  stderr is also unwritable. `run` with a missing request file reaches the
  writer without starting the client, so it serves as the `run` row.
- **DT-28.c, DT-28.e: reasoned retention with a stated limit**, in
  `10-request.surface.md` beside each exit-0 sentence: "Exit 0 reports that every
  write and the flush to the process's standard output succeeded. A command
  launched with standard output closed writes to a discarding descriptor and
  also exits 0." Check: add the `>&-` rows to the two integration tests that
  already close stderr.
- **DT-28.d: no change.**

### 4.5 Resulting user duties

- Match an invalid augment name on `invalid_value` at its list element.
- Treat `conflicting_selector` as covering all three selector conditions and use
  `path` to tell the CLI/file disagreement from the other two.
- Until the product change: a status of 101 from `version`, `run`, a `runner`
  command or `sbpl-check` means the envelope was not written; for `runner
  install`, `remove` and `validate` it does not mean nothing changed. Read
  `runner list` and `runner reconcile` afterwards.
- Exit 0 from `example` or `test-input read` establishes a complete document
  only for a caller that supplied and read standard output.

### 4.6 Implementation worklist

1. `docs/contract/11-policy.surface.md:152`: `invalid_value`.
2. `docs/contract/10-request.surface.md:441` (`free.effect` text; the count of
   free-text relationships does not change), `:194`, `:229-234` and the two
   support owners' `limits`.
3. `docs/contract/15-refusals.surface.md:138`: controller `values`.
4. `controller/src/json_contract.rs` `print_envelope`: checked write and flush
   returning an error; `cli.rs` version arm, `run_flow.rs` `cmd_run` and
   `print_escaped_tool_error`, `bin/sbpl-check.rs`: exit 2 and one line through
   `cli::diagnose` (or the helper's equivalent) on failure. `runner_commands.rs`
   already propagates the error to exit 2.
5. `docs/contract/00-identity.surface.md:797`, `40-envelope.surface.md:96-100`,
   `50-installation.surface.md:39`, the helper's exit statement in
   `11-policy.surface.md`, and `controller/README.md:84-90`: the write-failure
   form.
6. Controls in `controller/integration/cli_contract.rs` (version, `run` on a
   missing file, helper, `>&-` rows) and `interface_cases.json`.
7. Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`;
   `tests/lib/python.sh docs/generate_interface.py` for `joins.json` after the
   new corpus case (`--refresh-inventory` only if the build script reports a
   stale inventory after the writer change).
8. Verify through "Interface definitions and help cards" in
   `tests/CHANGE-VERIFICATION.md`: `unit`, `integration`, `source_drift`.

---

## 5. DT-33 / DT-34 / DT-35 — dossier and installation result forms

No installation evidence here bears on transport fallback, and none is merged
with it.

### 5.1 Claims

| id | claim | boundary | holds at HEAD? | evidence class | classification |
| --- | --- | --- | --- | --- | --- |
| DT-33.a | `imports.failure` is the "First collection problem"; imports are visited in name order, so with imports written `zz…`, `bsd.sb`, `aa…` the failure names `aa…` while the compiler's message names `zz…`; the statements do not say which order; the same order selects the first cycle and bound. | Controller dossier | yes. Statement `42-dossier.surface.md:247-249` (and `:239-245`); order `controller/src/sbpl_lex.rs:20`, `:40` (`BTreeSet<String>`) and `sbpl_imports.rs:313-320`, `:259-268`; the first assignment wins (`get_or_insert_with`), after a root nonliteral form (`:314-317`) | R-pass (envelope re-read by the primary review); src | consequential ambiguity: an undefined order behind "first" |
| DT-33.b | `run FILE --timeout-ms 0` and `run FILE --runner-mode nope` give `request_path: null`; `run FILE --bogus` and `run FILE extra.json` give the path; the guide says null "when no path was given". | Controller argument errors | yes. `controller/src/run_flow.rs:443`, `:455` pass `None`; `:421`, `:431`, `:450` pass the parsed path. `v0.3.7` behaved the same. The surface says "null when preparation did not establish one" (`42-dossier.surface.md:104-106`) | R-exec (unavailable); src | accurate observation against the technical statement, which is loose and not false; the frozen guide sentence is contradicted and is not editable |
| DT-33.c | In all four `app_provenance` is null although nothing read the manifest; the field is stated as null "when its read or supported-schema parse failed". | Controller dossier | yes. Argument errors return at `run_flow.rs:524-531`, before the manifest load at `:543-545`; statement `42-dossier.surface.md:120-122` | R-exec (unavailable); src | inaccurate mechanism account (an omitted null case) |
| DT-34.a | Install inserts `XPC_SERVICE_PATH` only when `--env` did not supply it; ownership requires that variable to equal the recorded bundle path; no statement says a caller value makes the plist `unowned`. The sub-pass reports removal then refuses and retains cleanup; launchd's behavior was not examined. | Installer and cleanup classifier; no install run | yes, and the removal consequence is now traced: `runner_commands.rs:379-385`; `runner_manager.rs:1399-1408` returns `unowned`; removal then records "plist ownership is Unowned; removal refused", leaves the plist and retains the cleanup record (`runner_manager.rs:1593-1626`), after the record has moved to `pending_cleanup` (`:1540-1549`). Statements `50-installation.surface.md:85`, `:202`. No test or document passes `--env` | R-src; R-pass; src | consequential ambiguity with a product consequence: the installer accepts an input after which its own removal will not unlink the plist |
| DT-34.b | `plist_ownership` returns `unowned` for a present non-regular path and `unknown` for a regular file whose conversion failed; the statement gives `unknown` only for unknown presence. | Cleanup classifier | yes. `runner_manager.rs:1380-1392`; statement `50-installation.surface.md:207`. The review's DT-76 executed both branches | R-src; src | inaccurate mechanism account (omitted branches) |
| DT-34.c | `limits.json` says a later `runner remove` or `runner reconcile` continues recovery; reconcile is report-only. | Limits manifest | yes. `docs/limits.json:1441` (rendered `docs/LIMITS.md:145`); `controller/README.md:340-345`; `cmd_runner_reconcile` saves nothing | R-src; src | contradicted explicit commitment between two accounts; the limits text is the false one |
| DT-34.d | The statement says install signs the selected worker and the host with the supplied entitlements, which the code does; `controller/README.md` and the guide describe entitlements only on the worker. | Installer signing | yes. `runner_manager.rs:978-982`; statement `50-installation.surface.md:70`; `controller/README.md:287-288` | R-src; src | the surface is accurate; the README is an incomplete account |
| DT-35.a | `runner list` and `runner reconcile` return `normalized_outcome: "ok"` and exit 0; the same label is used by status, install, validate and remove. | Runner commands | yes by source: `runner_commands.rs:450`, `:457`, `:501`, `:688`, `:746`, `:867`. Remove uses it whatever `cleanup_retained` says (`:688`) | R-exec (list, reconcile; unavailable); R-pass; src | accurate observation; unstated |
| DT-35.b | `policy-witness runner` with no subcommand prints usage on stderr and exits 2 with no envelope; every refusal other than `not_found` is one stderr line and exit 2. | Runner commands | yes by source: `runner_commands.rs:872-905`; `cli.rs:62-68` | R-exec (unavailable); R-pass; src | accurate observation; unstated in technical accounts |
| DT-35.c | Within the installation statements `normalized_outcome` is stated only for `not_found` and verify; exit 2 is shared by an enveloped `not_found` and unenveloped refusals. | Statements | yes. `50-installation.surface.md:39`, `:607-660`; `controller/README.md:304-305` | R-src; src | inaccurate account by omission |

### 5.2 Comparison

**Dossier.** "First" is first in the scanner's traversal: a nonliteral form in
the submitted source, then imports depth-first in byte order of their names at
each level. It is not source order and not the compiler's order. The technical
statement for `request_path` does not conflict with the producer; the guide's
does and stays frozen. `app_provenance` has a third null case, a run that ended
before the manifest was read.

**Installation ownership.** The statement at `:85` says install "defaults
XPC_SERVICE_PATH to the bundle" and the statement at `:202` requires a
"matching … XPC_SERVICE_PATH". Together they imply the consequence without
stating it. Elsewhere the installer refuses caller values for bundle-derived
identities ("`--bundle-id` and `--executable` are refused; those identities come
from the bundle", `:70`). The registry record keeps no copy of the install
environment (`runner_manager.rs:431-476`), so the classifier can compare only
with the bundle path.

**Signing.** The surface and the code agree. The README sentence omits that the
enclosing bundle's signature also carries the entitlements and that the
unentitled worker is signed.

**Command result forms.** Exit 2 has three meanings for a runner command: an
enveloped `not_found`, an enveloped verify `tool_error`, and an unenveloped
refusal. Exit 0 with `ok` from `runner remove` includes a report with
`cleanup_retained: true`; from `runner validate` it includes positive
`missing` or `invalid` (the latter is stated at `:142`).

### 5.3 Plausible treatments

- DT-33.a: state the order in `42-dossier.surface.md`; or collect references in
  source order (`sbpl_lex.rs`, a build input, changing which failure, cycle and
  bound are reported).
- DT-33.b: (1) pass the parsed path at `run_flow.rs:443` and `:455` (build
  input); the guide sentence would then hold when the path precedes the option
  and still fail when the option precedes it. (2) State the case in the surface.
- DT-33.c: correct `42-dossier.surface.md:120-122`.
- DT-34.a: (1) refuse an `--env XPC_SERVICE_PATH` value that differs from the
  resolved bundle path, before signing (`runner_commands.rs`, a build input).
  (2) Change the classifier to compare with a recorded value or rely on the
  recorded plist hash (alters cleanup authority). (3) State the consequence in
  `50-installation.surface.md:85`.
- DT-34.b: correct `50-installation.surface.md:207`.
- DT-34.c: correct `docs/limits.json:1441`; the DT-69 row owns the same sentence.
- DT-34.d: correct `controller/README.md:287-288`.
- DT-35: state the success label and the refusal form in
  `50-installation.surface.md` and `controller/README.md`.

### 5.4 Recommended disposition

- **DT-33.a: account correction.** Text for `failure`: "First collection problem
  in the scanner's traversal, scan setup failure or reason for a not-applicable
  scan; null when none was recorded. The traversal reports a nonliteral form in
  the submitted source first, then visits imports depth-first in byte order of
  their names; it is not source order." Add "in that traversal" to `cycle` and
  `exceeded`. Existing check to extend: `sbpl_imports.rs`
  `import_errors_keep_the_first_failure_and_successfully_read_hashes` covers the
  first-failure rule; an order assertion belongs in
  `witness_contract/dossier_witness` with two absent names written in reverse
  order. The source-order alternative is not recommended: each record already
  carries its own `error`, so the summary's order loses nothing.
- **DT-33.b: reasoned retention with a stated limit**, in
  `42-dossier.surface.md:104-106`: "Request-file path parsed from the command
  line; null when none was established, including when an option's value is
  refused, whether or not a path preceded it." The two-site product change is a
  real candidate if a controller rebuild is already scheduled, and cannot make
  the frozen guide sentence true for every argument order. More evidence would
  not change this.
- **DT-33.c: account correction.** "…null when the run ended before the manifest
  was read, or when its read or supported-schema parse failed."
- **DT-34.a: product change (1), refusal at install.** No documented or tested
  use passes the variable; the installer already refuses caller values for the
  other bundle-derived identities; the alternative leaves a plist that `runner
  remove` will not unlink. Machinery added: one comparison and one refusal
  string. Friction: a caller who supplies the variable must supply the canonical
  bundle path or omit it. What is missing: no install has been executed with
  this option by the review or this pass, and launchd's behavior with a
  different value is unobserved; neither would change a refusal placed before
  any machine change. If refusal is declined, the limit sentence for `:85` is:
  "A caller-supplied `XPC_SERVICE_PATH` that differs from the recorded bundle
  path makes the installed plist `unowned`; `runner remove` then refuses to
  unlink it and retains the cleanup record."
  A check must reject: an install that writes a plist which `plist_ownership`
  classifies `unowned` for its own record; and a refusal issued after the bundle
  was re-signed or a pending record saved.
- **DT-34.b: account correction.** "…Unknown presence produces unknown
  ownership, as does a present regular file whose content cannot be converted. A
  present path that is not a regular file is unowned."
- **DT-34.c: account correction** in `docs/limits.json:1441`: "…a later `runner
  remove` continues recovery; `runner reconcile` reports the retained record."
  This is one edit shared with DT-69's disposition; land it once. The guide's
  copy stays frozen.
- **DT-34.d: account correction** in `controller/README.md:287-288`: "Install
  signs the selected worker with the entitlements, the validator and the
  unentitled worker without them, refreshes the equipment inventory, then signs
  the enclosing bundle and its host executable with the entitlements".
- **DT-35.a, DT-35.b, DT-35.c: account correction.** Add to
  `50-installation.surface.md` after `:39`: "A completed list, status, install,
  validate, remove or reconcile command reports `result.normalized_outcome:
  "ok"`, true `ok` and exit 0; for remove this includes a report whose
  `cleanup_retained` is true. A usage, argument, registry-load or operation
  refusal other than a lookup miss writes one reason to standard error, prints
  no envelope and exits 2." Checks: `integration/cli.integration` for the usage
  refusal and `runner list` under a scratch `PW_RUNNER_REGISTRY`;
  `runner_byoxpc/registry_recovery` already produces a retained-cleanup remove
  and can assert its `ok` label.

### 5.5 Resulting user duties

- Read `imports.records[].error` for every import problem; `imports.failure`
  names one of them in name order.
- Do not conclude from a null `request_path` that no path was given.
- Do not pass `--env XPC_SERVICE_PATH=…` to `runner install` with any value
  other than the bundle path.
- Exit 0 and `ok` from `runner remove` do not establish retirement; read
  `cleanup_retained` and `warnings`. Exit 2 from a runner command with an empty
  standard output is a refusal reported on standard error, not `not_found`.
- `runner reconcile` reports and does not continue a recovery.

### 5.6 Implementation worklist

1. `docs/contract/42-dossier.surface.md`: `failure`, `cycle`, `exceeded`
   (`:239-249`), `request_path` (`:104-106`), `app_provenance` (`:120-122`).
2. `docs/contract/50-installation.surface.md`: `:39` (result forms), `:85`
   (variable), `:207` (classification).
3. `controller/src/runner_commands.rs` `cmd_runner_install`: after the canonical
   bundle path is resolved and before signing, refuse a supplied
   `XPC_SERVICE_PATH` that differs from it.
4. `docs/limits.json:1441`; `controller/README.md:287-288` and `:304-307`.
5. Controls: a Rust integration row for the install refusal against a scratch
   registry and a fixture bundle that fails no earlier check (or the refusal
   asserted in `runner_byoxpc/registry_recovery`, which is opt-in and needs a
   GUI session); the dossier order row in
   `tests/suites/witness_contract/check_dossier.py`; the runner-command rows in
   `controller/integration/cli_contract.rs`.
6. Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`;
   `tests/lib/python.sh docs/generate_limits.py`.
7. Verify: `source_drift` (`limits_documentation`, `build_contracts`), `unit`,
   `integration`, `witness_contract/dossier_witness`; for the installer change
   the "Registry recovery" and "BYOXPC default location" entries of
   `tests/CHANGE-VERIFICATION.md` (`runner_byoxpc/registry_recovery`,
   `runner_byoxpc/default_location`).

---

## Combined sequencing

Four recommendations edit build-contract inputs: 1.B (`ValidatorClient.swift`),
2.A (`ActorOrchestration.swift`), 4 DT-28 (`json_contract.rs`, `run_flow.rs`,
`cli.rs`, `sbpl-check.rs`) and 5 DT-34.a (`runner_commands.rs`). They are
independent of one another and can share one signed rebuild and one worker
identity regeneration. Every other recommendation is an account or test edit
that needs no rebuild. The plan asks that a revised test be exercised against
existing behavior first: the new live controls for 1 and 2 should be run once
against the current app, where the empty-ID row and the unapplied rows are
expected to fail, before the product edits land.

## Outside the review

These were noticed while tracing and are not findings of the review.

- **The actor form drops a validator pipe or serialization failure for every
  actor mode** (source only; not executed). For a failed `pipe`, a failed
  descriptor setup or a probe serialization failure the classifier returns
  `runner_failed` (`CWorkerDisposition.swift:425-429`). The ordinary form takes
  that result (`CWorkerOrchestrator.swift:195`). The actor form keeps a phase
  result only when its outcome begins with `validator`
  (`ActorOrchestration.swift:374`), so the same failure in an applied or an
  unapplied actor's phase leaves `finished`. The phase then shows `collected`,
  `not_spawned` and no `validator_spawn_failure` record, and the failure's
  text appears nowhere in the reply. Reaching it needs descriptor exhaustion or
  a failing `fcntl`, so no specimen is proposed. Once treatment 2.A supplies the
  declared view, taking every nonzero phase result (removing the prefix test)
  would make the two forms agree; a constructed unit row with an injected
  `.failure(.pipeFailed…)` would distinguish the two behaviors.

- **Legacy `runner_mode` beside `--runner-mode`** (source only,
  `run_flow.rs:481-510`, `runner_select.rs:143-205`). The CLI/file conflict
  refusal compares only the nested `runner.mode`. A file that carries the legacy
  top-level `runner_mode` and a different `--runner-mode` is not refused for the
  disagreement: the injected nested value replaces the legacy one under the
  stated precedence. The DT-27 wording above says "nested" for this reason.
- **Service inspection named for the worker** (source only,
  `ActorEquipment.swift:221-254`, `:324-329`). The static inspection used for
  the service bundle labels its errors `worker_signature` or
  `signing_information`. This is stated under DT-30.a as part of the account
  correction; the product alternative there would remove it.
- **No actor-form validator failure is registered for an applied actor either**
  (catalog and retained run). The DT-23/51 control therefore supplies both rows,
  not only the unapplied one.
