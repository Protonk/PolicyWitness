# Ordering predictions before attempts

## Status: gate 2 complete and remediated; gate 3 next

The working tree now uses **request schema 1, response schema 8, worker ABI 7**.
Batch 0 remains the audited baseline. The worker release barrier, host release and
acknowledgement evidence, typed comparison model, consumers and initial controls
are implemented and verified through **gate 2**. Gates 3–4 remain pending.
This is the handoff point; no batch-3 bridge or bypass mutation build is credited.

An independent audit upheld gate 2 and raised five items; its report was
reviewed and retired once remediation was verified. The remediation covers all
five: reply-failure handling/shared eligibility; deterministic late
acknowledgement; manual encoder field coverage; documentation/parser/naming
cleanup; and the compiled-C budget relation with uncapped validator fault
injection. All five are implemented and verified on a fresh signed build, and
the reply-failure contract and implementation were reviewed on 2026-09-26.
Gate 3 work starts from here.

| Batch | State | Acceptance |
| --- | --- | --- |
| 0: conservative classification | Complete | Audited gate 1 retained below |
| 1: ABI 7 and worker wait | Complete | Gate 2 passed |
| 2: host release and response 8 | Complete | Gate 2 passed |
| 3: ordered witnesses and negative controls | Not complete; some prerequisite coverage brought forward | Gates 3 and 4 pending |

### Current implementation

- The worker acquires host `proceed` and release-publishes `proceed_observed`
  before attempting any slot. Monotonic expiry or native clock failure publishes
  a proceed failure and `done`, with no attempts. Late release cannot revive it.
- The host releases after the synchronous validator driver returns, including
  missing queries or failed spawn/collection/cleanup. Collection closure is
  separate from validator termination. The final acquired acknowledgement and
  worker ownership through it determine the lifetime evidence; later cleanup
  failure does not erase established order.
- Response 8 has per-step `comparison.order` and a worker `ordering` object.
  In addition to the planned booleans/disposition, that object carries
  `worker_lifetime_established` and `protocol_violations` so consumers can check
  these prerequisites without interpreting later cleanup as earlier ownership.
  Construction and validation now share one eligibility rule, including unique
  record association, native NONE normalization and worker PID/lifetime.
  The service reply boundary reports `runner_reporting_failed` if normal encoding
  fails, retains the original summary and observations, and withholds every
  comparison with explicit drift nulls. The narrow exception and explicit
  evidence-loss backstop are in the [reply construction contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#reply-construction-failure).
- `ComparisonEvidence` replaces the temporary `orderEstablished` boolean.
  State and path identity have no established case, so no current path can
  derive disagreement/true. Unordered same-target unlink still scans all attempts
  in the run; established order restores only supported allow/success agreement.
- Enrichment still reads the planning sentinel and appends host nonresolution
  without changing conclusions. Consumers retain legacy response-7 semantics
  while enforcing the stronger response-8 chain and disagreement prohibition.
- Budgets selected: 60,000 ms worker proceed wait, 30,000 ms validator I/O,
  1,000 ms validator exit grace, 5,000 ms nominal release margin. The relation is
  a configuration guard, not a bound on host scheduling, final reap or orphan
  lifetime. The validator I/O clock is monotonic; its new request override is
  floored at 50 ms and echoed, intentionally without a ceiling. The default-only
  inequality consumes the compiled C probe directly. Short-budget controls cover
  collection outlasting worker expiry without reviving attempts.

### Latest verification: gate 2 audit remediation

Completed on 2026-09-26 using `YOLO=1 ./build.sh` and unsandboxed test execution.
Request schema remains 1, response schema 8 and worker ABI 7.

- Signed ZIP SHA-256:
  `2e54d96bc1dfbc27d9f33bf4c6ce55c26c43f43746af259e941d430c4e4cee68`.
- Embedded evidence-manifest SHA-256:
  `90c7687115b930a4878f447213d73b6729fb7999642bbfebe720a65c2e4ab372`.
- Focused selection: **67/67** canonical cases, **333/333** Swift checks,
  **25/25** C harness cases and **115** Rust tests passed.
- Default battery: **131/131** canonical cases passed, including all focused
  cases and the same **333/333** Swift checks. Both runs have zero failures,
  skips or unrun cases, valid initial artifact integrity and an unchanged app.

The [remediation record](../tests/out/order-gate2-remediation-build/remediation.json)
contains exact case IDs, commands, hashes, source/equipment snapshots, retained
diagnostics and review scope. The [focused report](../tests/out/order-gate2-remediation-focused/run.json)
and [default report](../tests/out/order-gate2-remediation-default/run.json) belong to
this build. The original gate-2 acceptance and audit remain intact below/on disk.

`ReplyFailureTests` adds twelve constructed serializer controls: ordinary and
legacy preservation, eight invariant-fault variants, rejection of surviving
claims or successful summaries under a failure marker, an explicit minimal reply
after repeated encoding failure, and reflection/round-trip field coverage.
These exercise the production reply serializer, not a native sandbox failure or
a request override that forces a result. The shared eligibility helper includes
association uniqueness, NONE normalization, PID and lifetime. Consumer controls
independently accept degraded evidence and reject misuse of the exception.

The ownership test now actually preserves a late raw acknowledgement: polling
EIO breaks ownership, the subsequent cleanup wait opens a fixture acknowledgement
gate, and ECHILD ends cleanup after the receipt. The final acknowledgement is true
while lifetime and per-step order remain unestablished. Tests also exercise the
real validator I/O boundary beyond a short worker budget and the new argv error
diagnostic. The budget inequality reads the compiled production C limit probe;
the independent native inventory check remains in place. The validator override
is intentionally uncapped, with its over-budget behavior documented and tested.

Only two documentation corrections followed the focused source snapshot:
`tests/README.md`'s harness count and `tests/COVERAGE.md`'s ABI wording. They changed
no production code, test implementation, inventory membership or build input.
The default run re-executed every focused case on the final snapshot, including
`source_drift`. The record preserves this explicit applicability review and both
snapshots. Only this plan's final handoff changed after default verification.
The tracked worker binary stays as built. No barrier-bypass mutation or gate-3
bridge/witness coverage is credited by these passing runs.

Review the [reply construction contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#reply-construction-failure),
[service reply serializer](Sources/PWRunnerCore/PWRunnerService.swift),
[wire invariants/shared eligibility](Sources/PWRunnerCore/PWRunnerAPI.swift), and
[preservation controls](Tests/PWRunnerCoreTests/ReplyFailureTests.swift) before
continuing. The evidence-loss backstop deliberately uses only JSON-native
scalars/containers, independent of the result encoders.

### Original gate 2 verification

Completed on 2026-09-26 with the signed build from
`tests/out/order-gate2-build/build5.log` (`YOLO=1 ./build.sh`) and unsandboxed
execution. Request schema remains 1; response schema is 8; worker ABI is 7.

- Signed ZIP SHA-256:
  `fef4b37efa751a01442da199defe46bf06669874a17874e318a4966d043a827a`.
- Embedded evidence-manifest SHA-256:
  `86e96d772f3770dc2c4a46e5f4449ec07751cd893c9eaf778df697485de71f48`.
- Focused selection: **67/67** canonical cases passed, including **319/319**
  Swift checks, all **25/25** C worker harness cases and **115** Rust tests.
- Default battery: **131/131** canonical cases passed. Both runs have zero
  failures, skips and unrun cases, valid initial artifact integrity and an
  unchanged app inventory through completion.

Exact canonical IDs, commands/configuration, results, hashes and the source
snapshot are in the local [gate record](../tests/out/order-gate2-build/gate-2.json),
[focused report](../tests/out/order-gate2-focused3/run.json),
[default report](../tests/out/order-gate2-default2/run.json),
[source snapshot](../tests/out/order-gate2-build/source-snapshot.json) and
[build hashes](../tests/out/order-gate2-build/build-hashes.json).
At that acceptance point only this plan's final handoff changed after the final
source snapshot; the original gate record checked all other hashes/modes and
recorded the plan delta. That snapshot predates audit remediation. Focused3 has
its own snapshot: two test scripts outside that selection changed afterward
(the filter adapter's schema controls and native exec comparison expectations).
Their helpers, callers, registry and all focused inputs are unchanged. This is
an explicit reviewed reuse of focused3, not an inference from hashes alone;
every focused case also passes again in the final full default run.

The default battery and the focused selection rerun the audited batch-0
classifier, enrichment and consumer controls. The live read/unlink and file-effects
cases now require native allow, `query_first` and agreement/false; later host
nonresolution remains visible. Those ordinary witnesses do not substitute for
section D's held-collection observer or section G's mutation controls.

Coverage placement differs slightly from the proposed file names: the new host
lifecycle, eligibility and encoder cases are in `OrderingTests.swift`, registered
under `runner_unit/pwrunner_core_unit_executable`, beside the existing
`EnvelopeInvariantTests`. Initial and subsequent native clock failures use two
production-C companions. The original ownership-loss control used `ignore_proceed`
and never observed a later acknowledgement; the remediation above supplies that
missing branch. Cleanup failure after an already observed acknowledgement has a
separate control. The
unconfirmed-validator controls exercise failed kill/reap/ECHILD, independent file
effects and a surviving child's late write returning EPIPE after collection closes.

The real I/O deadline case is registered as
`runner_outcome_validator_no_reply/validator_io_deadline_releases_worker`, with
`tests/fixtures/validator/deadline.json`; this follows the new-override contract in
`runner/AGENTS.md`. It checks exact outcome/error/echo, partial-record eligibility,
normal worker completion and independent effects on both files.

The 500 ms override case took 1,860 ms for the entire CLI invocation in the
focused acceptance run, including 1,000 ms exit grace and successful cleanup.
That is a measured healthy-path check for the 5,000 ms nominal release margin,
not a scheduling or final-reap bound. Defaults satisfy
`60,000 > 30,000 + 1,000 + 5,000`; short/long worker-budget controls, expiry during
a held hook, clock failures and host-loss cleanup pin the separate failure paths.
The default-run timing and boundary outputs are linked from the gate record.

Preserved diagnostic runs are not acceptance: the interruption left build3 and
focused1 (54/58, 316/316 Swift), with NONE-filter encoding and stale unordered
expectations corrected but unverified. Resumption's focused2 passed 66/67
(318/319 Swift); its new late-output fixture failed to recognize a JSON-escaped
gate path. A UUID token fixed that test-only boundary. Focused3 and the default
battery reran all credited cases with the corrected fixture against the unchanged
signed build5. The first default run passed 129/131; the filter-checker controls
still called schema 7 current and the native exec witness still required the
blanket unknown-order limitation. Both test expectations were corrected. The
filter controls now exercise response 8 and retain explicit legacy-7 acceptance;
all 188 direct adapter controls pass. Default2 reruns all 131 cases on the final
test snapshot. No production or embedded documentation changed after build5.
[Expected semantic failure states](../tests/out/order-gate2-build/expected-failure-states.json)
are recorded per scenario; an ABI-version refusal is not credited as a red
ordering test. Actual barrier-bypass mutation tests remain pending.

Reproduction commands (use fresh output directory names to retain this evidence):

```sh
YOLO=1 ./build.sh
PW_TEST_OUT_DIR=tests/out/order-gate2-focused-new tests/run.sh --suite runner_unit --suite runner_c_worker_harness --suite runner_abi_layout --suite witness_contract --suite runner_validator_failure --suite runner_outcome_validator_no_reply --suite runner_ready_byte_resilience --suite run_effects --suite blackbox_e2e --suite source_drift --suite failure_boundaries --suite unit
PW_TEST_OUT_DIR=tests/out/order-gate2-default-new tests/run.sh
```

### Gate 1 verification

Verification completed on 2026-09-25, using `YOLO=1 ./build.sh` and unsandboxed
test execution. The signed build's ZIP SHA-256 is
`90881cacf436fb4a318c63f87bcffbcbef25d60f4631bbfda19364caf43b00b8`.
Its embedded evidence-manifest SHA-256 is
`8ac6002bcb10f25d88ea1178a02c2b86b4c385f077cf7e0de8bef27f17bc19f7`.

- Focused gate: **22/22 canonical cases passed**, including all 15 existing
  C worker harness cases and **286/286 Swift assertions**.
- Default battery: **120/120 canonical cases passed**, zero failures, skips or
  unrun cases. Both runs confirmed valid initial signatures/manifests and an
  unchanged app inventory through completion.
- Both live unlink witnesses returned native deny on the read row and on the
  unlink row, with successful attempts, unavailable/null and both supported
  limitations on each row; the file was independently observed absent.

This is a rerun. The first gate 1 run, on ZIP
`4f16f9cc4727eecc5392a3f79ccf95fa0321fc77065585f5df59ed7dafd64254`, passed
22/22, 120/120 and 282/282 with the same selections; its records remain intact
under `tests/out/order-batch0-build/`, `order-batch0-focused/` and
`order-batch0-default/`. Its regression control compiled and failed in the six
intended assertion cases (276/282) before the production changes; that red run
is diagnostic evidence, not acceptance of a build. An audit of that run found
that the mutation confound was scanned only over the current and preceding
steps, although with unestablished order a later step's unlink precedes an
earlier step's query just as easily. A two-step live specimen against that
build showed the read row returning native deny with
`host_path_resolution_changed` and no mutation limitation; it is retained under
`tests/out/order-batch0b-build/prefix-observation/`. The scan now covers every
attempt in the run, enrichment reads the planner's outcome sentinel instead of
a limitation label, the consumer requires `host_path_resolution_changed` in
both directions, the live witness gained the read row, and `runner_unit` gained
rows for the later-step confound, the sentinel gate and the production
builder's deny/success path. Under the reuse rules in `tests/README.md`, the
affected cases were rerun rather than credited.

Exact selections, configuration and outcomes are retained in the local
[gate record](../tests/out/order-batch0b-build/gate-1.json),
[focused report](../tests/out/order-batch0b-focused/run.json) and
[default report](../tests/out/order-batch0b-default/run.json). The gate record
contains every canonical case ID; the reports include invocation commands.
[Source hashes and modes](../tests/out/order-batch0b-build/source-snapshot.json),
[build hashes](../tests/out/order-batch0b-build/build-hashes.json) and
[build output](../tests/out/order-batch0b-build/build.log) bind these results to
the implementation and signed artifact.

Reproduction commands from the repository root:

```sh
YOLO=1 ./build.sh
PW_TEST_OUT_DIR=tests/out/order-batch0b-focused tests/run.sh --suite runner_unit --suite runner_c_worker_harness --case blackbox_e2e/checker_controls --case witness_contract/removed_target_prediction_is_not_drift --case witness_contract/drift_determination_via_validator_seam --case run_effects/file_actions_have_exact_effects --suite source_drift
PW_TEST_OUT_DIR=tests/out/order-batch0b-default tests/run.sh
```

These evidence directories are gitignored local artifacts. Preserve them with
separate `PW_TEST_OUT_DIR` selections; if unavailable or dependencies change,
rerun the relevant checks. The gate-1 production/test snapshot belongs to that historical verification,
not the current ABI-7 tree. `build.sh` rewrites the tracked
`controller/tools/pw_probe_runner/pw-probe-runner`; its earlier description as
“different only by link UUID” was incorrect (text/constant sections also differed
from HEAD). Preserve the build-produced binary and identify shipped evidence by
the signed bundle-local worker hash, not that UUID claim.

### Next work

The reply-failure contract and implementation were reviewed after remediation:
host reporting failure is distinct from execution failure, raw evidence and the
original summary are preserved, every comparison is withheld, the consumer
exception is narrow, and the evidence-loss backstop for repeated serialization
failure is explicit. Batch 3 begins here.
The tracked worker binary is a build output; keep it as produced and use the
signed bundle hashes when identifying evidence.

Then complete the unchecked C/D/G items: add the gated native validator bridge and
its direct controls; add the held-collection external observer, pre-attempt interval,
external mutation and maximum-step witnesses; finish the signaled-validator and
CLI spawn-failure/pre-apply ordering assertions; retire the interim witness name
into `queries_precede_attempts`; and run both disposable barrier-bypass builds.
The ordinary read/unlink witness already expects ordered agreement, but its
current name remains until that batch. Keep all unordered classifier and consumer
controls. Finish registry/docs and `--all` acceptance at gate 4. Neither gate 3
nor gate 4 is passed by the default battery recorded above.

## The observation that started this

`run_effects/file_actions_have_exact_effects` runs an allowed `unlink` under
`(version 1) (allow default)`. The attempt succeeds and the target is gone. The
original prediction for the same operation and path was `deny`, five runs out
of five, and the envelope reported `drift: true`. Batch 0 changed that unordered
row to unavailable/null under either prediction; gate 2 now establishes order
and the live witness reports allow/agreement. Two controls support a timing explanation:
querying `file-write-unlink` on a file that persists returns `allow`; querying
`file-write-data` on the file that gets unlinked returns `deny`. A query after
removal explains those observations; the response-7 envelope did not establish
order in an individual run. Five repetitions do not make the race deterministic.

Before ABI 7, the mechanism was in two places. `pw-probe-runner` published the
`applied` sentinel and immediately began its attempt loop. `CWorker.run` fired the
post-applied hook, which runs the validator synchronously, on the first polling
iteration after it observed `applied`. Nothing ordered the validator's queries
against the worker's attempts. The response-7 comparison builder attached
`query_attempt_order_unestablished` and `state_stability_unestablished` to every
comparison unconditionally, and `tests/lib/consumer.py` requires both on every
response-7 step. A limitation present on every step cannot tell a reader which
step is the one where the state actually changed.

The removal supplied another explanation for that unordered difference. Under
"no dishonest attribution", that unordered row projects to `null`. Establishing order removes
one possible explanation; it does not by itself establish sandbox drift.

## Protecting the meaning of drift

`drift: true` is reserved for a difference between `sandbox_check` and observed
kernel enforcement for which no other explanation remains supported or materially
unresolved by the run's evidence. It must not mean merely that two recorded
outcome labels differ. Historical response-7 replies permit that weaker reading;
the current producer and explicit conformance controls enforce the conservative
interim rule. Batch 2 preserves the stronger meaning when order is established.

A positive drift claim requires a usable native verdict, an observed attempt,
established query order and worker policy context, corresponding operation and
runtime target, and evidence sufficient to exclude relevant state changes,
incomplete query coverage and other enforcement mechanisms as explanations.
Missing evidence is not evidence that an alternative did not occur. In
particular, identical path strings, absence of a captured denial event and
`query_first` do not discharge those obligations.

For differing outcomes, unresolved material explanations yield
`conclusion: "unavailable"` and `drift: null`, with all raw observations and
applicable limitations retained.
Permission-shaped failure alone still cannot establish sandbox enforcement.
`directional_consistency` continues to project to `null`. An allow verdict and
successful corresponding attempt may retain `agreement` / `drift: false` as
agreement of those observations; it does not certify identical state or the
absence of every possible policy defect. One known confound overrides even
that weaker claim: a worker-reported mutation of the submitted target whose
order against the query is unestablished yields `unavailable` / `drift: null`
under either verdict, because the two channels may not have been asked about
the same object. Established order lifts it; see the interim rule and batch 2.

This ordering change adds no target-identity or state-equivalence evidence.
Consequently, deny/success path rows that retain material
`runtime_target_identity_unestablished` or `state_stability_unestablished`
limitations cannot become `drift: true`, even with `query_first`. No positive
drift claim is required to demonstrate success of this plan. Future evidence
that discharges those limits must have its own reviewed contract and controls;
an empty limitations array or an unknown limitation is not a substitute. The
batch-2 mechanism is typed evidence, not label absence: the
conclusion is computed from evidence values, the limitations array is rendered
from those same values afterwards, and the value that would permit
`disagreement` has no constructible form in this schema. Batch 2 specifies it.

## The promise

After this work, PolicyWitness promises, for every run in which the worker
applied its policy:

1. The worker attempts nothing until it observes host release. The host releases
   only after query collection is closed and the validator phase returns,
   including no planned queries, partial output, decode failure, I/O deadline
   and pre-spawn failure.
   No record received after release can enter a step prediction.
2. `comparison.order: "query_first"` means an eligible native allow/deny record
   was received against this worker's applied policy before the worker observed
   release, and that observation precedes every attempt in the plan. Eligibility
   and the worker-lifetime evidence required for this claim are defined below.
   Other records survive without acquiring that claim.
3. The envelope exposes the host's collection/release observations, the worker's
   release acknowledgement and the associated verdicts. Consumers can check the
   evidence chain within one envelope. These are observations from cooperating,
   tested protocol participants, not independent attestation against a lying host
   or worker.

Collection closure is the chosen barrier; confirmed validator termination is a
separate fact. `runValidator` can return after failed kill/reap with disposition
unconfirmed. The host still releases the worker after collection closes, preserving
the attempt channel and cleanup diagnostics. A surviving validator might continue
making queries, but none of those later records is collected or used. This plan
does not promise that no validator process is alive during attempts.

The promise is about PolicyWitness's own actions. It does not promise:

- that the target's state is unchanged between a query and its corresponding
  attempt: external activity or earlier worker steps may change it
  (`state_stability_unestablished` remains);
- that the path spelling names the same runtime object at both times
  (`runtime_target_identity_unestablished` remains);
- that a query was requested: planning exclusions (a target that does not
  resolve on the host, unrecognized filter kinds, prediction-unavailable pairs)
  keep their existing `missing_reason` and the step keeps `drift: null`;
- a comparison for attempts whose prediction was excluded or never returned;
  these attempts still obey the same release barrier;
- per-step interleaving or one shared snapshot. Each eligible query occurs in
  an interval before the first attempt. External state can change within that
  interval; earlier attempts can then change the state faced by later attempts.
  A later step's prediction does not incorporate its siblings' effects.

## Starting points

- `controller/tools/pw_probe_runner/pw_probe_runner.c`: `applied` store, the
  attempt loop that follows it, `spin_for_exit`, the `prepared` refusal, the
  existing `clock_gettime` deadline pattern, the argv seams
  (`--post-apply-hang-ms`, `--post-apply-kill-signal`, `--pre-ready-hang-ms`).
- `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`: header sentinels,
  ABI 7 evidence record (`PW_OP_*`, `PW_PROGRESS_*`, `PW_FAILURE_*`),
  `PW_PROBE_RUNNER_ABI_VERSION`.
- `runner/Sources/PWRunnerCore/CWorker.swift`: the polling loop, the
  post-applied hook, the rule that the hook fires before `done` is checked, the
  sentinel budget that excludes synchronous hook time.
- `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift`: the hook that runs
  `runValidator`, `buildOrdering`, `ComparisonEvidence` and its rendered limits.
- `runner/Sources/PWRunnerCore/ValidatorClient.swift`: `ValidatorOutput`, the
  I/O deadline, partial-evidence returns.
- `runner/Sources/PWRunnerCore/PWRunnerAPI.swift`: `PWRunnerComparison.drift`,
  `PWRunnerSandboxCheckResult`, response schema constant.
- `tests/suites/runner_c_worker_harness/harness.c`: hand-built shm scenarios
  and corruption knobs; this is where a host that misbehaves is written.
- `tests/fixtures/worker_lifecycle/`: the ABI fixture and its stdin tokens;
  this is where a worker that misbehaves is written.
- `tests/suites/witness_contract/`, `tests/suites/run_effects/`,
  `tests/suites/runner_live_worker_identity/`: the CLI witnesses and the
  external-observer pattern.
- `tests/fixtures/validator/`: the transcript validator and its checked-in
  transcripts; the gated bridge below is built beside it, not from it.
- `tests/suites/runner_exec_inheritance/opt_in/mutations.sh` and its entry in
  `tests/OPT_IN_TESTS.md`: the existing opt-in mutation machinery that section
  G's controls register under.
- `runner/AGENTS.md` § "Adding a new override": the recipe the
  `validator_io_timeout_ms` seam must follow, including the README table row
  that `source_drift` checks.
- `tests/lib/consumer.py`, `tests/lib/blackbox.py`,
  `tests/FAILURE-PROPAGATION-CONTRACT.md` § "Public representation and meaning"
  and § "Permanent consumer enforcement": what consumers currently require.
- `docs/LIMITS.md`, `docs/limits.json`: every budget below must be inventoried.

## Evidence design, briefly

No wall clocks. Order is a happens-before chain through the shared-memory
protocol PolicyWitness already uses, and each link names the party or parties
whose observations establish it:

| Link | Owner | Observation |
| --- | --- | --- |
| Collection closed before release | Host | The host closes collection before storing release, after the validator driver returns or a terminal decision needs no validator. It records the store and the independently observed child disposition. |
| Release before first attempt | Worker | The worker publishes that it observed the release sentinel before its first `PW_OP_ATTEMPT` started record. Without release it attempts nothing; expiry publishes a proceed failure if the worker survives to observe it. |
| Verdict belongs to the ordered set | Host and worker | A uniquely associated eligible verdict was received before release; successful application and the worker's subsequent release acknowledgement anchor it to this worker's policy lifetime. |

Implemented protocol names: header sentinels
`proceed` (host to worker) and `proceed_observed` (worker to host); worker
operation `PW_OP_PROCEED`; failure `PW_FAILURE_PROCEED_TIMEOUT`; a worker wait
budget `worker_proceed_wait`; a worker argv seam `--proceed-wait-ms`; run-level
`runner_subprocess.ordering` with `collection_closed_before_proceed`,
`proceed_set`, `proceed_observed`, `validator_disposition`,
`worker_lifetime_established` and `protocol_violations`; per-step
`comparison.order` in `{"query_first", "unestablished"}`, with the limitation
`query_attempt_order_unestablished` present exactly when `order` is not
`query_first`. ABI is 7, response schema is 8 and request schema stays 1.

`validator_disposition` records the disposition at release, or `not_invoked` if
the collection phase never began: `not_needed` for no planned queries,
`not_spawned` for setup or spawn failure, `reaped` for confirmed child exit, or
`unconfirmed` for a spawned child whose disposition is unknown. Existing transport, decode, exit, signal,
kill and wait observations remain separate; this field cannot erase any of them.
Collection closure includes a terminal no-query or pre-spawn decision and does
not imply that a stream or child ever existed. A false observation boolean means
the corresponding observation was not established, not proof of nonoccurrence.

### Eligibility and policy lifetime

`query_first` requires all three ordering booleans, confirmed successful policy
application, unbroken ownership of the worker through its release acknowledgement,
and a structurally valid allow/deny record with coherent native rc/errno, uniquely
associated by step ID and the exact planned query tuple.
`result_source: "validator"` alone is insufficient.
Synthetic results, pre-query errors, unsupported-operation diagnostics, unfamiliar
outcomes and rejected or ambiguous associations remain `unestablished`. Raw
records and association faults survive independently. A native error may report
a real call without supplying the usable prediction this field promises.

A worker that acknowledges release after collection closed was alive through the
query interval under the protocol's one-way policy application. A worker that dies
before that acknowledgement supplies no such evidence: retain received records,
but report `unestablished` order and no certified live policy context for them.
Death after acknowledgement does not erase already established order; it can
still leave attempts unavailable. A later cleanup fault likewise does not erase
earlier established observations. No query is launched against a reaped worker.

Transcript validators and lifecycle fixtures test interpretation and transport.
Their verdict-shaped records can exercise these joins, but cannot establish
native sandbox behavior or justify a positive drift claim. Live prediction
controls use the real validator; test provenance remains visible.

### Evidence states and field presence

Ordinary response 8 includes `comparison.order` on every emitted step. `ordering` is
required exactly when `runner_subprocess` is an object; it is absent when that
object is null/absent. Older responses gain neither field on decode. In the
table, C/S/O are collection closed before release, release stored, and release
observed. The rows describe the final observations for the stated scenario.

The sole exception is an explicit `runner_reporting_failed` reply with a valid
`reporting_failure` diagnostic: all comparisons are absent and drift is null.
When `evidence_retained` is true, the original queries, attempts and subprocess
observations survive unchanged, including incomplete ordering diagnostics; none
certifies per-step order. If degraded serialization also fails, the minimal
reply explicitly sets `evidence_retained: false` and carries no steps/subprocesses.

| Scenario | C/S/O | Validator disposition | Per-step order |
| --- | --- | --- | --- |
| No worker spawned | No ordering object | No snapshot | `unestablished` on any emitted step |
| Worker exists, application not confirmed | false/false/false | `not_invoked` | `unestablished` |
| Applied, no planned queries, release acknowledged | true/true/true | `not_needed` | `unestablished`; no prediction exists |
| Setup/spawn failed, release acknowledged | true/true/true | `not_spawned` | `unestablished`; retain the actual failure |
| Eligible records, release acknowledged | true/true/true | `reaped` or `unconfirmed` | `query_first` for eligible records only |
| Partial/diagnostic/rejected records, release acknowledged | true/true/true | `reaped` or `unconfirmed` | `query_first` only for eligible associated records; all others `unestablished` |
| Proceed expired or worker died before acknowledgement; hook later returned | true/true/false | Actual terminal disposition | `unestablished`; received records survive |
| Worker died or hung after acknowledgement | true/true/true | Actual terminal disposition | Eligible records retain `query_first`; missing attempts remain unavailable |

Consumers reject a `query_first` claim without every eligibility prerequisite,
with the order limitation still present, or with a synthetic/diagnostic record.
They also reject `unestablished` for an eligible record whose full chain is
established. Claimed release without collection closure, acknowledgement without
release, and release before successful application violate the protocol. If a
faulty fixture publishes contradictory sentinels, preserve the raw diagnostic
evidence, mark the protocol violation, and derive no established order; do not
repair the evidence by inventing missing observations. An observed proceed
timeout and a later release store are compatible, but cannot resurrect attempts.

## Interim classification, independent of ordering

This section is implemented and gate 1 is passed. Before any ABI change, a
deny/success difference with unestablished ordering stops projecting to `true`;
this rule is not limited to unlink. The unlink row
also has a specific explanation: a worker-reported successful mutation of the
submitted target could precede the query. Record `attempt_mutation_order_unestablished`
without claiming that the envelope proves removal preceded
the query. While order is unestablished the limitation is material to
agreement as well as disagreement: an `allow` verdict beside a successful
same-target unlink yields `unavailable` / `drift: null` just as a `deny` does,
so the gate-1 live unlink cases asserted one outcome whichever side of the race
the validator landed on. Their gate-2 forms now require ordered agreement. Once order is
established, a same-target mutation that follows its own query is no
confound and `agreement` returns. The current read/unlink witness pins that;
its rename to `queries_precede_attempts` remains in batch 3. Planned resolution and later host resolution failure supply a separate
`host_path_resolution_changed` observation, not a query-time observation. It is
emitted by the host's post-orchestration path enrichment, which runs after
every conclusion is fixed; see batch 0 for the call chain.

Successful unlink does not require later nonresolution to be relevant: recreation
can make the path resolve again. While order is unestablished the step position
of the unlink is irrelevant: the worker's attempt loop can complete every step
before the validator issues its first query, so a later step's unlink can precede
an earlier step's query. Established order discharges this confound for every
row, because each eligible query precedes every attempt. Distinct submitted
targets retain their existing scope
limits; never attribute mutation of B to query A merely because they share a
step. Unknown aliasing is not repaired by host canonicalization.

- [x] `runner_unit` / `DriftClassifierTests`: constructed rows for
  successful same-target unlink with unknown order yield `unavailable`,
  `attempt_mutation_order_unestablished` and `drift: null`, one row per
  native prediction so the choice is pinned deterministically:
  `same_target_unlink_allow_unordered_is_unavailable` and
  `same_target_unlink_deny_unordered_is_unavailable`. Beside them,
  `open_write_allow_unordered_keeps_agreement` shows the rule is specific to
  the mutation table, not to allow/success in general. Cover different query/attempt targets, failed unlink and
  same-target unlink in another step, earlier or later, separately. Later absence and later resolution or
  recreation are enrichment-time observations; their rows belong to the
  enrichment tests named in batch 0 and must show the appended observation
  never changes conclusion or drift. Other deny/success rows
  with unknown order also yield `null`. Reject limitations without their own
  supporting observations; later host nonresolution is a separate observation,
  not a precondition for the mutation limitation.
  Update existing current-build deny/success expectations, including supplied
  verdict interpretation controls, at this interim gate; response 8 later adds
  the established-order variants rather than postponing protection of `true`.
- [x] `witness_contract/removed_target_prediction_is_not_drift`: the
  `run_effects` unlink row through the CLI, preceded by a read of the same
  target, asserting on both rows `drift: null`, the mutation limitation, the
  retained native `allow` or `deny`, and independent absence of the file. No
  particular race outcome is required. The ordered
  unlink case below supersedes this interim live case; the classifier controls
  for unestablished order remain.
- [x] `run_effects/file_actions_have_exact_effects`: the `raced` expectation
  becomes `drift: null` with the specific limitation. Recording continues.
- [x] `blackbox_e2e/checker_controls` and `tests/lib/consumer.py`: a fabricated
  current-build response with `disagreement` and a material ordering/state
  explanation is rejected; one with `unavailable` plus supported limitations is
  accepted. During the schema-7 interim, these are explicit current-build
  conformance controls, not a schema-only rule imposed on historical replies.
  Generic legacy decoding and stored response-7 fixtures remain unchanged;
  consumers must not silently reinterpret their historical `drift` values.

## Tests that enforce the promise

Checked items are implemented and verified by the gate-2 or remediation records above. Unchecked
items remain required for gates 3–4. The interim-classification and batch-0
checklists describe their historical gate; current adaptations are stated above.

Every case names what would make it fail and what it does not establish. Live
cases run through the public CLI unless a boundary is not reachable that way,
in which case the harness or the driver tests own it and the coverage row says
so. No override may fake a result; every seam re-routes a real boundary. Existing
transcript fixtures remain interpretation controls, explicitly distinguished from
native prediction witnesses. Test-owned gates acknowledge readiness and completion;
fixed sleeps are not evidence that a query or mutation has occurred. Bounded waits
are test failure deadlines, not a claimed order between processes.

### Test equipment the cases assume

Each item is test-only, built outside the inspected app, and gets direct
controls of its own before any case credits it.

- Gated validator bridge: a test-owned executable selected through the existing
  `validator_executable_path` override. It speaks the batch NDJSON protocol,
  makes real `sandbox_check` calls against the worker PID, and holds each
  verdict, and collection closure, on a test-owned socket gate that acknowledges
  readiness. Direct controls: gate acknowledgement before any verdict, exact
  forwarding of native results, holding collection open without exiting, and
  refusal to emit after the gate is closed. It lives beside
  `tests/fixtures/validator/` with its own README.
- Lifecycle fixture tokens (`tests/fixtures/worker_lifecycle/`): release wait,
  release acknowledgement, expiry under a short budget, self-signal while
  waiting, ignoring release, and signal after acknowledgement. Direct controls
  extend the fixture's existing ones.
- A `.clock-failure` companion from the lifecycle builder, in the style of
  `.apply-failure`: production C main with the deadline clock substituted.
- Harness release-timing knobs in `harness.c`: withhold release, delay it, set
  it early, set it after expiry, withhold exit request.

### A. The worker alone (`runner_c_worker_harness`)

The harness plays host. It can set sentinels in any order, at any time, or
never. Implemented scenarios:

- [x] `proceed_never_set`: harness sets `prepared`, observes `applied`, never
  sets `proceed`. Expect: no slot completes; the worker publishes
  `PW_OP_PROCEED` started and a `PW_FAILURE_PROCEED_TIMEOUT` record after its
  budget; `done` flips; `proceed_observed` stays 0; clean exit on
  `exit_requested`. Fails if any slot completes or the worker hangs past its
  budget plus grace. Does not establish host behavior.
- [x] `proceed_late_after_expiry`: as above, then the harness sets `proceed`
  after the failure record. Expect: still no slot completes; the failure record
  is unchanged. Pins that a late release cannot resurrect attempts.
- [x] `proceed_before_applied`: harness sets `proceed` together with
  `prepared`. Expect: attempts run only after `applied`; under
  `SCEN_DENY_DEFAULT_POLICY` every slot is denied, proving the policy was
  applied before the attempt even though release was already visible. Fails if
  a slot succeeds. Does not establish that the host ever sets release early.
- [x] `proceed_delayed_observed_quiescence`: harness observes `applied`, then
  for 500 ms polls every slot's `completed` flag and the evidence record,
  allowing the initial `PW_OP_PROCEED` publication but no attempt activity, then
  sets `proceed` and expects normal completion.
  Fails if any slot completes, or any `PW_OP_ATTEMPT` started record appears,
  before release. This witnesses the "release before first attempt" link in
  the worker harness.
- [x] `proceed_under_bare_deny_default`: `SCEN_DENY_DEFAULT_POLICY` with a
  delayed release. Pins that the wait loop needs nothing the policy can deny:
  CPU polling with a monotonic deadline and no sleep or I/O dependency. The
  existing `spin_for_exit` has no clock deadline, so its safety alone does not
  establish the new clock path. Fails if the worker dies or unexpectedly expires
  before the harness releases within budget.
- [x] `proceed_clock_failure`: a controlled native-clock failure must publish
  a wait failure and attempt nothing. An unusable clock must not authorize
  release or turn the deadline into an unbounded proceed wait. This is an
  isolated C boundary control, not a policy-attribution test. The harness
  drives the shipped worker and cannot substitute a native call, so this runs
  against the `.clock-failure` companion and is credited under `runner_unit`
  beside `WorkerEvidenceTests`, in the same way `.apply-failure` is.
- [x] `proceed_wait_budget_short`: pass `--proceed-wait-ms 100`, delay release
  500 ms. Expect the timeout failure record. Then pass `--proceed-wait-ms
  2000` with the same delay and expect success. Boundary control for the
  budget; the production value is inventoried separately.
- [x] `proceed_expiry_release_boundary`: a release seen before the deadline
  permits attempts; expiry already published forbids them even after release.
  At an unresolved scheduling boundary either terminal branch is acceptable,
  but timeout evidence and subsequent attempts may never coexist.
- [x] `host_lost_while_waiting`: the harness withholds both release and exit
  request. Expect a proceed failure and zero attempts, not worker self-exit.
  The test owns eventual termination and reaping. This pins the limited lifetime
  claim: the existing post-done exit spin can outlive the host.
- [x] `max_slots_proceed`: `PW_SHM_MAX_STEPS` slots, delayed release. Expect
  every slot completes after release and none before. Fails on any early
  completion at scale.
- [x] `abi_mismatch_refused`: the ABI 7 worker refuses an ABI 6 header
  before application. The reverse, an ABI 6 fixture with an ABI 7 host,
  is covered in the driver tests below.
- [x] `printer.c` in `runner_abi_layout`: emits the new header offsets; the
  Swift `PWShmLayout` mirror must agree. `LimitsContractTests` and
  `NATIVE_LIMITS` carry `worker_proceed_wait`; the Swift inequality consumes the
  same existing compiled C probe directly, rather than a second literal.

### B. The host driver alone (`runner_unit`, lifecycle fixture)

The fixture plays worker. Cases below are implemented in `OrderingTests.swift`;
the existing `EnvelopeInvariantTests` retains legacy/enrichment coverage.

- [x] `proceed_wait_then_report`: a test-owned gate holds the hook after
  readiness is acknowledged. While held, the fixture must neither observe
  release nor report attempts. Open the gate, let the hook return, then expect
  release acknowledgement and completion, with all three ordering observations
  true. Fails if the driver stores release while the hook is still held.
- [x] `proceed_wait_expire`: the fixture's own short budget expires while the
  test's hook blocks on a test-owned gate. Expect the fixture to publish the
  proceed failure and `done`; after the gate opens and the hook returns, the
  driver stores release anyway, observes `done` with zero completed slots and
  `proceed_observed` false, and classifies `runner_failed` with the worker's
  proceed failure as the reported failure. The predictions the hook returned
  survive in the result. Fails if the driver reports a policy cause, drops the
  verdicts, or reports order as established for any step.
- [x] `hook_spawn_failure_before_release`: the hook returns a validator spawn
  failure. Expect release stored, fixture proceeds, attempts complete,
  `ordering.collection_closed_before_proceed` true with disposition
  `not_spawned` and the actual spawn error retained; every step
  `order: unestablished` because no verdict exists,
  `drift: null` everywhere. Fails if attempts do not run.
- [x] `signal_while_waiting`: the fixture self-signals after `applied` and
  before observing release (token `signal_awaiting_proceed`). Expect
  `applied` 1, `proceed_observed` 0, `done` 0, confirmed signal status,
  `runner_failed`, no attempt evidence, retained records, no policy cause.
  Gate validation so death occurs before a subsequent query: records before
  and after death cannot acquire certified live policy context or `query_first`
  without release acknowledgement. Do not require any particular native answer
  for a dead PID. Also cover worker ownership loss before acknowledgement.
  Complements the existing post-attempt self-signal seam.
- [x] `hang_while_waiting`: the fixture ignores release (token
  `ignore_proceed`) and never reports. Expect the sentinel deadline,
  termination request, reaping, `runner_timeout`, `proceed_set` true and
  `proceed_observed` false. Fails if the classifier calls it a worker
  attempt hang.
- [x] `signal_after_release_before_attempt`: acknowledge release, then signal
  before publishing an attempt. Eligible predictions retain `query_first` while
  attempts are unavailable and `drift` remains null. Post-release death does not
  retroactively erase the query interval's lifetime evidence.
- [x] `legacy_worker_abi6`: an ABI 6 fixture binary against the ABI 7 host is
  refused before spawn or at header check, with the existing mismatch
  evidence. Pins that an old worker cannot run unordered under a new host.
- [x] `OrderingTests` encoding and builder controls: exercise every row of the evidence-state table,
  including all queries excluded, setup failure, no worker and failed application.
  Pin field presence, record eligibility and the distinction between protocol
  faults and established order. Synthetic results, pre-query errors, native-error
  diagnostics, incoherent native fields, unknown outcomes, duplicate IDs and
  mismatched query tuples never acquire `query_first`. Legacy decodes gain no
  ordering fields.
- [x] Ownership loss followed by a late acknowledgement: `proceed_ack_gate`
  cannot acknowledge until the polling wait failure has broken host ownership.
  Cleanup then permits the acknowledgement and returns ECHILD. Preserve the raw
  acknowledgement and both wait errors, but require unestablished lifetime/order.
  The test owns cleanup of the child the driver could not reap.
- [x] `ReplyFailureTests`: real reply serializer with constructed invariant
  faults, field-complete raw-evidence preservation, absent comparisons/null drift,
  original-summary retention, failure-marker rejection controls, repeated encoder
  failure and manual-field coverage. No request override fabricates these errors.

### C. The validator's failures (`runner_validator_failure`, `witness_contract`)

Each existing validator-failure case gains ordering assertions, because the
promise is only interesting when the validator misbehaves.

- [ ] `validator_spawn_failed_reports_degraded`: attempts still run;
  `ordering.collection_closed_before_proceed` true with disposition
  `not_spawned` and the spawn error retained; every step `order: unestablished`
  and `drift: null`; independent file effects present.
- [x] `validator_unavailable_reports_degraded` (2 of 3 verdicts, clean EOF):
  the two received verdicts are `order: query_first`; the third is
  `unestablished` with its existing missing reason; all three attempts ran
  after release; file effects independently observed.
- [x] `validator_decode_failure_reports_degraded` (malformed JSON after two
  verdicts): same shape as above with the decode fault retained.
- [x] `validator_io_deadline_releases_worker` (registered under
  `runner_outcome_validator_no_reply`, using `deadline.json`): a checked-in transcript
  validator that emits one verdict then hangs. Expect the I/O deadline, kill,
  reaping, release stored afterwards, the one verdict `query_first`, the rest
  `unestablished`, attempts completed, `runner_subprocess` normal. Add the
  mirrored `validator_io_timeout_ms` request override at the real I/O boundary
  so this case uses a short deadline, following `runner/AGENTS.md` § "Adding a
  new override". Value checks pin the production budget
  relationship described below; this healthy-cleanup fixture must release before
  worker expiry. The relationship is not a bound on every cleanup path.
- [ ] `validator_killed_mid_stream` (new, transcript fixture that dies by
  signal after one verdict): as above with a signaled disposition.
- [x] `validator_cleanup_unconfirmed_releases_worker` (`runner_unit`): extend
  the real driver controls for failed kill, failed reap and ECHILD ownership
  loss, including EOF from a child that remains alive. Once the driver returns,
  expect collection closure and release, disposition `unconfirmed`, retained
  errors and eligible partial records, and independent attempt effects. No later
  output can join a step. Do not infer validator exit from EOF, a kill request or
  function return. The test owns cleanup of any child left alive or unreaped.
- [x] `validator_collection_does_not_return_before_worker_expiry`
  (`runner_unit`, the `proceed_wait_expire` case): hold a real lifecycle
  boundary beyond the worker's short
  proceed budget. Expect no attempts and durable proceed failure; release after
  the gate opens cannot revive the plan. This complements the healthy-cleanup
  deadline case and does not claim to bound a stuck production reap.

### D. The promise end to end (`witness_contract`)

- [ ] `queries_precede_attempts`: the `run_effects` unlink row, now expected
  to report prediction `allow`, `drift: false`, `order: query_first`, the
  three ordering observations true, and the target independently absent
  afterwards. This is the regression sentinel for the whole effort; the
  interim case from the section above is retired into it.
- [ ] `queries_use_a_pre_attempt_interval`: two plans. Plan 1: step 1 `create` A
  (absent at planning), step 2 `unlink` A. Expect both predictions
  `prediction_unavailable` with `query_not_requested`, both attempts succeed,
  both `drift: null`, and independent observation that A is absent at the end.
  Intermediate existence is worker-reported evidence only; final absence or a
  third failed read cannot independently prove it. Plan 2: step 1 `unlink` A
  (exists at planning), step 2 `open_read` A. Expect step 1 `allow`/`drift: false`;
  step 2 prediction `allow`, attempt
  `open_failed` with ENOENT, observation `other_failure`, conclusion
  `unavailable`, `drift: null`, and the known earlier-step mutation retained
  beside the blanket state limit. Fails if the system reports step 2 as drift
  in either direction. Add unlink/recreate/read coverage: later resolution must
  not erase the earlier mutation or certify runtime identity.
- [ ] `attempt_effects_wait_for_collection`: a test validator bridge forwards
  real native queries and gates their completion using a test-owned side
  channel. Plan = [`unlink` A, `exec` helper in `--tree` socket mode]. After
  the bridge acknowledges its gate, keep collection active and independently
  observe that A remains intact and no helper has connected. Then release the
  gate and expect unlink followed by the helper's connection, ancestry and file
  observations. Inspect PW's ordering fields only afterward. A late snapshot
  showing no validator child is insufficient: it could miss overlap with unlink.
  The required bypass controls in section G must produce an early observable
  effect while this gate is held. This test establishes the barrier for these
  effects, not absence of every possible syscall or validator process.
- [ ] `query_interval_is_not_a_snapshot`: use the bridge to pause between two
  real queries, and independently change a test-owned target before permitting
  the second query. Both queries still precede attempts; their input state need
  not be equal. Assert retained native observations, `query_first` where eligible
  and the state/identity limits, without crediting test-only mutation knowledge
  as an observation in a production envelope or requiring an unsupported native
  verdict for a missing target.
- [ ] `max_steps_ordered`: 256 file steps on distinct existing targets, half
  allowed, half denied by literal. Every step `query_first`; allowed successes
  report `agreement` / false, while deny/permission-failure pairs report
  `directional_consistency` / null, not established sandbox denial. File effects
  are independently observed. Fails on any `unestablished` order or any prediction
  taken from a state already changed by the worker's attempts.
- [x] `ready_byte_interplay` (extend `runner_ready_byte_resilience`): with
  `worker_pre_ready_hang_ms` past the ready-byte wait, the worker still
  waits for release after `applied`; expect `order: query_first` and
  all three ordering observations true.
- [x] `post_apply_seams_still_after_attempts`: `worker_post_apply_hang_ms`
  and `worker_post_apply_kill_signal` fire after attempts, therefore after
  release; expect `proceed_observed` true in both, and unchanged outcomes
  (`runner_timeout`, `runner_failed`). The release/complete-slot assertions
  are in the real-worker `CWorkerTests` cases.
- [ ] `deny_default_ordered`: `(deny default)` with one allowed and one denied read; expect
  `query_first` on both steps and the usual verdicts. Pins that a hostile
  policy cannot break the wait.
- [ ] `external_mutation_between_query_and_attempt`: the bridge acknowledges
  receipt of the real verdict for A, then holds collection open. The test removes
  A and confirms absence before allowing collection to close and release the
  worker. No worker sleep seam or timing guess is needed. Expect
  prediction `allow` (queried while A existed), attempt `open_failed` ENOENT,
  `order: query_first`, `state_stability_unestablished` still present,
  conclusion `unavailable`, `drift: null`. This pins what the promise does
  not cover, so a future reader cannot read `query_first` as "same state".
- [ ] `pre_apply_failure_reports_no_policy_verdict` (existing): unchanged
  expectations plus the exact field-presence rule from the evidence-state table:
  no ordering object without a worker subprocess, otherwise all-false with
  `not_invoked`. No step is `query_first`.
- [x] `ordered_difference_does_not_imply_drift`: retain the existing supplied
  deny/success interpretation controls, now expecting `unavailable` / null when
  runtime identity, state stability or fixture provenance leaves another
  explanation. Constructed classifier controls remove each prerequisite in turn
  and must never yield true. An all-true ordering object is insufficient, and
  deleting limitation strings cannot manufacture the missing evidence: one row
  builds the comparison from evidence values and then empties the rendered
  limitations array before asking for the conclusion, and one row hands the
  public struct a `disagreement` with an empty array and requires the encoder
  invariant to reject it. Both exist because the conclusion function must
  never read the array; batch 2 states the mechanism.

### E. Consumers and offline controls

- [x] `tests/lib/consumer.py`: response 8 enforces the evidence-state table,
  native-record eligibility and conditional object presence; require
  `query_attempt_order_unestablished` exactly when `order` is not `query_first`.
  Controls in `blackbox_e2e/checker_controls` reject `query_first` with missing
  acknowledgement, failed application, lost worker ownership during the interval,
  a synthetic/diagnostic record, an ambiguous association or the order limitation
  still present. Reject `unestablished` only when every eligibility prerequisite
  is established, not merely because the booleans are true. Cover contradictory
  sentinel diagnostics without upgrading their claims. Valid no-worker replies
  are accepted; ordinary replies with a worker but no ordering object are rejected.
  The documented reporting-failure exception requires a failed summary and
  diagnostic and forbids every comparison/drift claim; consumer controls pin it.
  Reject `drift: true` with a material alternative explanation or missing required
  evidence, even if order is established. On response 8 that means rejecting
  `disagreement` outright: the schema defines no vocabulary for established
  state or established runtime identity, so no envelope can carry the evidence
  the claim requires, and a control that deletes every limitation string from a
  `disagreement` step with `order: query_first` must still be rejected. A legacy
  7 retains its historical projection and blanket limitations without inventing
  new evidence.
- [x] `tests/lib/blackbox.py`: same version gate; the three live filter
  callers pass `--expected-schema-version 8`.
- [x] `unit/rust.unit` (`runner_client`): response versions 4 through 8
  round-trip; unfamiliar `order` values survive as strings.
- [x] `runner_unit` Swift encoding: the whole `limitations` array survives
  including unfamiliar values; `order` is a plain string.

### F. Budgets, registry and documentation obligations

The worker's proceed budget starts after successful application and measures
elapsed monotonic time until release is observed or expiry is published. The
validator I/O deadline covers only its I/O phase. Document the nominal relation
`worker_proceed_wait > validator_io_wait + validator_exit_grace + release_margin`,
with a positive, inventoried margin for observation, setup, decoding and scheduling.
The action plan owns the numeric value and its measured justification. Inventory
the effective test override as well as the production defaults. Align elapsed
deadline clock semantics; wall-clock adjustment must not silently extend the
validator I/O phase relative to the worker's monotonic budget.

This inequality covers production defaults, not test overrides; the validator
override has a 50 ms floor and deliberately no ceiling. A short-budget real-driver
control preserves predictions after worker expiry and forbids revived attempts.
The inequality is a configuration guard, not a worst-case lifecycle bound.
Host scheduling and setup can overrun the margin, and the existing final blocking
reap has no total-duration bound. In those cases the safety obligation is no
attempts without release, followed by a durable failure if the worker remains
able to run its deadline check. Successful progress, prompt host reply and eventual
orphan cleanup are not guaranteed by that obligation. After proceed expiry the
worker uses the existing unbounded exit-request spin; a dead host can leave it
alive. Bounding that lifetime would require a separate lifecycle change.

- [x] `docs/limits.json`: `worker_proceed_wait` with value checks in
  `NATIVE_LIMITS` and `LimitsContractTests`, the release margin, clock/counting
  semantics and the nominal relation above. Boundary notes point at the short
  budget, release/expiry, clock-failure and delayed-cleanup controls. Explicitly
  exclude final-reap latency and post-done lifetime from the claimed bound.
  `docs/LIMITS.md` and the guide regenerate.
- [x] `tests/COVERAGE.md`: proceed timeout and
  death while waiting map to `runner_failed`: timeout uses the published worker
  failure, death uses observed process disposition and the last available
  progress. Do not require a dead worker to publish a failure record. Add those
  rows to the ABI 7 evidence table in the contract. Audit remediation separately
  adds `runner_reporting_failed` for host reply construction, with its own outcome
  matrix row and preservation tests; it supplies no new worker-failure cause.
- [ ] `tests/README.md`, `tests/catalog.json`, per-suite READMEs: every case
  above registered; `source_drift` enforces. All implemented cases are registered;
  the remaining batch-3 cases and opt-ins still need entries.
- [x] `tests/FAILURE-PROPAGATION-CONTRACT.md` § "Public representation and
  meaning": replace "Every comparison reports
  `query_attempt_order_unestablished`" with the per-step rule; add the
  ordering observations with their separate owners, the record-eligibility and
  lifetime requirements, and the stronger positive-drift rule. Update the C1/C3/C4
  dispositions and supplied deny/success controls accordingly. Preserve the
  historical response-7 contract as legacy semantics rather than silently
  reclassifying stored replies.
- [x] `README.md` Flow: define the evidence required for `drift: true`, and
  explicitly say that `query_first` establishes order only. No claim that the
  new barrier alone supplies strong evidence of differing kernel enforcement.
- [x] `docs/PolicyWitness.md`: `steps[].comparison.order`,
  `runner_subprocess.ordering`, the batch semantics, response 8.
- [x] `docs/QUESTIONS.md`: the proposed "Which happens first" pair changes
  its answer to the qualified promise for eligible `query_first` records, with
  missing predictions, death before acknowledgement and unconfirmed validator
  cleanup explained. Describe an interval, not a common state snapshot.
- [x] `runner/README.md` "Run result highlights": the new fields.
- [x] `runner/README.md` test-seam table and `PWRunnerTestOverrides`:
  `validator_io_timeout_ms` is mirrored and re-routes only the real I/O deadline.
  Gate fixtures use the existing validator executable override; they do not add
  a production flag that manufactures results or require hidden worker resources.

### G. Required negative controls (opt-in execution)

- [ ] A worker built from a patched source copy that bypasses the release wait
  must fail `proceed_delayed_observed_quiescence` and
  `attempt_effects_wait_for_collection` with an actual early effect. Preserve
  ordinary attempt behavior so the failure demonstrates barrier sensitivity.
- [ ] A host built from a patched source copy that releases while validation is
  gated must fail the host-driver gate control and the external effect control.
  Merely setting the expected JSON fields cannot satisfy the independent test.

These controls are required for acceptance, registered under the existing opt-in
mutation machinery (`runner_exec_inheritance/opt_in/mutations.sh` and its
`tests/OPT_IN_TESTS.md` entry are the model). Build candidates outside the
inspected app and record their
own hashes; never patch the signed artifact during a dispatcher run. Each control
must fail for its named ordering violation, not missing equipment, signing or
transport failure. Neither the ungated unlink race nor a snapshot of child
absence is a substitute. This tests ordinary synchronization regressions, not
resistance to arbitrary malicious evidence forgery.

## Acceptance gates

Gates 1 and 2 are passed with the evidence recorded at the top of this document.
Gates 3–4 remain pending; the default battery does not establish their new
ordering obligations or replace the required opt-in barrier-bypass controls.

1. Interim classification: the four items in "Interim classification" pass on
   a signed build with no ABI or schema change, and the default battery is
   green. `run_effects` retains whichever native prediction was observed with
   `drift: null`; current-build conformance and legacy decoding are distinct.
2. Worker and driver: sections A and B pass. The worker cannot attempt without
   release, cannot be resurrected by a late release, and survives a bare
   deny-default wait. The host cannot release before the hook returns.
3. Validator failures and the end-to-end promise: sections C and D pass,
   including the gated external observer and both required negative controls
   from G. `queries_precede_attempts` replaces the interim live case. Eligible
   predictions remain ordered through validator cleanup failures, and order alone
   never upgrades a difference to `drift: true` while material alternatives remain
   unresolved.
4. Consumers and documentation: sections E and F pass; `source_drift`,
   `runner_abi_layout`, `runner_unit`, `runner_c_worker_harness`,
   `failure_boundaries` and the Rust unit tests pass; `--all` reports no
   unrun case that this plan added.

Each gate records its signed build hash and the exact case list, following the
reuse rules in `tests/README.md` § "Reusing verification results".

## Implementation

Four batches. Each names the production change, the exact anchors in the tree,
the tests from the sections above that it must make pass, and which of those
tests can be written before the change and are expected to fail until it lands.
A batch is complete only when its gate in "Acceptance gates" is recorded with a
signed build hash. Batch 0 changes no ABI and no schema. Batches 1 and 2 may be
developed in either order for the worker and the host, but the gate for batch 2
requires batch 1's worker.

Where work can run. The harness, the driver tests, the classifier tests, the
consumer controls and the Rust tests need no XPC service; they do apply real
sandboxes and spawn real children, so an automation harness that sandboxes the
session can still refuse them. Every case in sections C and D, and the
`run_effects` flip, needs the built app and live XPC and must run unsandboxed.
A session that cannot run live cases can still write them, run
`tests/run.sh --list` to prove registration, and run `source_drift` to prove
the registry agrees.

### Batch 0: classification without new evidence

Complete and verified through gate 1. The checked items below describe the
historical interim behavior. Batch 2 replaces its temporary order boolean with
typed evidence and establishes the release barrier; those current rules are above.

The batch-0 call chain, in `runner/Sources/PWRunnerCore/`: `PWRunnerService.runSpecimen`
calls the orchestrator, which runs `planValidatorQueries` (resolving each path
filter on the host and excluding unresolved ones with the code
`path_unresolved_at_planning`), then `runCWorker` with the validator hook, then
`buildStepResults`, which joins both channels for every step and then calls
`computeComparison` once per step with the step's planning decision as
`queryExclusionReason`, `orderEstablished: false` and every step's attempt
result as `runAttempts`. The orchestrator returns
the result; only then does the service call `enrichPathDiagnostics`, which
resolves each path filter again and writes `path_diagnostics` with phase
`after_orchestration`, and replies. Every conclusion is therefore fixed before
the later resolution exists. Nothing in this batch moves that observation
earlier, and nothing reads a field that has not been written yet.

Implemented production changes:

- [x] `computeComparison`: add an `orderEstablished: Bool` input, false for
  every caller in this batch. `conclusion == "disagreement"` requires it. With
  it false, every deny/success row yields `unavailable` and `drift: null`,
  which is the interim rule. Keep `directional_consistency` as it is, and
  keep `agreement` except where the next bullet's limitation applies.
- [x] `computeComparison`: the mutation observation, from every
  worker-reported attempt in the run, whatever its step position, because an
  unordered attempt loop can finish before the first query. The
  `reportsTargetRemoval` switch is a
  small table of attempt (`requested_kind`,
  `requested_action`, outcome) triples that remove or replace the submitted
  target's object; it holds one row, (`file`, `unlink`, `ok`), requiring worker
  provenance and `rc=0`. When the row matches, the path query was planned,
  and its submitted target equals that attempt's, append
  `attempt_mutation_order_unestablished`. Whether the query was planned is
  already visible here: `queryExclusionReason` is nil exactly when a probe
  existed. Do not condition the limitation on later host resolution. In this
  batch the limitation is material to both conclusions: when it applies, an
  `allow` verdict beside the successful attempt yields `unavailable` /
  `drift: null` exactly as a `deny` does. This is what makes the two live
  unlink cases independent of which side won the race; they assert
  `unavailable`, null and the limitation, and record the verdict. The
  deterministic pin is the pair of classifier rows named in "Interim
  classification".
- [x] `enrichPathDiagnostics`: the later-resolution observation, where the
  later resolution actually happens. When the step's filter kind is path, the
  query was planned (its `sandbox_check.outcome` is not the planner's
  `prediction_unavailable` sentinel, which only a planning exclusion produces
  for a path filter, so the planner resolved it), and the fresh
  `realpath_resolved` is nil, append
  `host_path_resolution_changed` to `comparison.limitations`. The function
  never touches `conclusion` or `drift`; it appends an observation after the
  fact. No new field is added in this batch.
- [x] Response schema stays 7. Existing supplied-verdict controls that
  expected `disagreement` are updated to `unavailable`/null in the same
  change, because the interim rule is a current-build rule.

Implemented tests (classifier/enrichment regressions were written first):

- [x] `runner_unit` / `DriftClassifierTests` rows from "Interim
  classification" for the two `computeComparison` changes. Written first; the
  rows for `unavailable` fail until the change lands, the rows for
  `agreement` and failures pass before and after.
- [x] `runner_unit` / `DriftClassifierTests` "host path provenance" group and
  `EnvelopeInvariantTests` "consumer evidence survives encoding without
  reclassification": enrichment rows for later absence, later resolution and
  recreation. Each feeds `enrichPathDiagnostics` a step whose conclusion is
  already fixed and requires the observation to be appended, or not, with
  `conclusion` and `drift` unchanged either way. Offline.
- [x] `witness_contract/removed_target_prediction_is_not_drift`, a copy of the
  `run_effects` unlink row preceded by a read of the same target, with
  `RunCapture`, log capture disabled, both native predictions accepted on each
  row, `drift: null` and the mutation limitation required on each row,
  independent absence of the file. Live.
- [x] `run_effects/check_file_actions.py`: the `raced` expectation asserts
  `drift: null`, `comparison.conclusion == "unavailable"` and the mutation
  limitation; keep recording the prediction. Live.
- [x] `blackbox_e2e/checker_controls` and `tests/lib/consumer.py`: the
  projection rule already there stays; add the current-build conformance
  control that rejects `disagreement` on a step carrying the mutation
  limitation, and require both limitations in both directions, including a
  later step's unlink confounding an earlier row. Offline.
- [x] `drift_determination_via_validator_seam` and any other case that
  supplied a deny verdict against a successful attempt and expected
  `disagreement`: expect `unavailable`/null. Live.

Gate 1 is the four interim items plus a green default battery.

The new live witness is registered in `tests/catalog.json` and
`witness_contract/run.sh`; its shell entry point is executable. Current-build
expectations in `check_comparison.py` and the validator-seam shell control now
require unavailable/null for deny/success. The seam supplies coherent native
rc-shaped input records, while remaining explicitly an interpretation control.

### Batch 1: ABI 7 and the worker

`controller/tools/pw_probe_runner/pw_probe_runner_abi.h`:

- [x] `PW_PROBE_RUNNER_ABI_VERSION` 6 to 7.
- [x] The header has exactly two reserved words left, at offsets 56 and 60
  (ten 32-bit fields plus the 16-byte nonce fill 56 bytes of the 64). Take
  them: `_Atomic uint32_t proceed;` at 56 and `_Atomic uint32_t
  proceed_observed;` at 60. Remove `reserved` rather than leave a zero-length
  array, and add a static assertion that `sizeof(pw_shm_header_t) ==
  PW_SHM_HEADER_BYTES`. No other offset moves; `PW_SHM_HEADER_BYTES` stays 64.
- [x] `PW_OP_PROCEED = 11` in the operation enum,
  `PW_FAILURE_PROCEED_TIMEOUT = 8` in the failure enum, and a native kind for
  the deadline clock so a `clock_gettime` failure is a `PW_FAILURE_NATIVE`
  record with the real return and errno.
- [x] `PW_PROCEED_WAIT_MS_DEFAULT`, next to `PW_EXEC_CHILD_DEADLINE_MS_DEFAULT`
  in `pw_probe_runner.c`, so `worker_limits.c` and `NATIVE_LIMITS` in
  `tests/suites/runner_abi_layout/limits.py` can read it the way they read the
  exec deadline. The value is the action plan's; it must satisfy the relation
  in section F against the validator defaults in
  `runner/Sources/PWRunnerCore/ValidatorClient.swift`.

`controller/tools/pw_probe_runner/pw_probe_runner.c`, between the `applied`
store and the attempt loop:

- [x] Publish `PW_OP_PROCEED` started. Take the deadline with
  `clock_gettime(CLOCK_MONOTONIC)` exactly as the exec-child deadline does; on
  a nonzero return publish the native failure, publish `done`, and
  `spin_for_exit`. Do not fall back to a permissive deadline here, unlike the
  exec path; an unusable clock forbids attempts.
- [x] Poll `proceed` with acquire ordering and the same `cpu_relax` primitive as
  `spin_for_exit`, re-reading the clock each round. On release, store
  `proceed_observed` with release ordering, publish `PW_OP_PROCEED` returned,
  and fall through to the unchanged attempt loop. On expiry, publish
  `PW_FAILURE_PROCEED_TIMEOUT` with the budget in `detail` and a diagnostic
  naming the budget, store `done`, and `spin_for_exit`. Nothing in the wait
  makes a system call; `clock_gettime` on macOS reads the commpage.
- [x] Argument `--proceed-wait-ms N`, parsed beside the three existing seams
  with the same bounds style, overriding only the budget. It is harness
  equipment; no request override plumbs it, because the host always releases
  after its hook and a seam that stopped the host releasing would fake a
  result.
- [x] Leave the pre-ready hang, the post-apply hang and the post-apply kill
  seams where they are. Their positions relative to the new wait are what
  `ready_byte_interplay` and `post_apply_seams_still_after_attempts` pin.

Mirrors and equipment:

- [x] `PWShmLayout` in `runner/Sources/PWRunnerCore/CWorker.swift`:
  `abiVersion` 7, `proceedOffset` 56, `proceedObservedOffset` 60.
  `printer.c` in `runner_abi_layout` emits both offsets.
- [x] `tests/fixtures/worker_lifecycle/worker.c`: the `transport_incompatible`
  mode now uses the header constant plus one, so it remains incompatible
  after the bump to ABI 7.
- [x] `tests/suites/runner_c_worker_harness/harness.c`: after observing
  `applied`, store `proceed` unless a knob says otherwise. New scenario knobs
  beside the corruption knobs: `withhold_proceed`, `proceed_delay_ms`,
  `proceed_at_prepare`, `proceed_after_expiry`, `withhold_exit_request`; a
  quiescence poll that records any slot completion or attempt progress seen
  before release; and the evidence record's operation and code in the
  scenario's JSON so `run.sh`'s Python assertions can name
  `PW_OP_PROCEED` and `PW_FAILURE_PROCEED_TIMEOUT`. The `.clock-failure`
  companion is built by `tests/fixtures/worker_lifecycle/build.sh` next to
  `.apply-failure`, substituting the clock call.
- [x] `docs/limits.json`: `worker_proceed_wait` in the execution section with
  a source reference to the C default, value checks in `NATIVE_LIMITS` and
  `runLimitsContractTests`, and a path check naming the harness budget
  scenario. `python3 docs/generate_limits.py --check` must pass, which means
  every referenced symbol must exist in the referenced file.

Tests: all of section A, the `runner_abi_layout` agreement, the
`LimitsContractTests` value row. The harness scenarios can be written before
the worker change; every one of them fails against an ABI 6 worker at the
version check, which is the wrong failure, so record the expected-failure
state per scenario rather than crediting a red run.

Gate 2 covers this batch together with batch 2.

### Batch 2: host, orchestrator and response 8

`runner/Sources/PWRunnerCore/CWorker.swift`:

- [x] `CWorkerOutput` gains `hookInvoked`, `proceedSet` and `proceedObserved`.
- [x] In `runCWorker`, immediately after the post-applied hook returns, and
  also when no hook was supplied, store `proceed` with release ordering and
  set `proceedSet`. The polling loop and the sentinel budget are otherwise
  unchanged; the loop is iteration-counted, so hook time is still outside
  the budget. Read `proceed_observed` in the same final acquire snapshot that
  reads `done` and the slots, after cleanup.
- [x] No new `CWorkerInput` field. The worker budget seam is harness-only.

`runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift`:

- [x] The hook closure records that collection closed when it returns, for
  both the empty-probe early return and the `runValidator` return, and
  records the validator disposition it can see at that moment:
  `not_needed` when probes were empty, `not_spawned` for
  `ValidatorClientError.spawnFailed` and any failure with no partial output,
  `reaped` when the output's `reaped` is true, else `unconfirmed`. A worker
  that never published `applied` never fires the hook and gets
  `not_invoked`.
- [x] Build `runner_subprocess.ordering` from those two sources and attach it
  to the subprocess object after `buildWorkerSubprocess`; present exactly
  when the subprocess object is present.
- [x] Per-step `order` in `buildStepResults`: `query_first` when all three
  ordering observations and worker lifetime are true, there are no protocol
  violations, `applied` is true with `applyRC == 0`, the
  step's verdict is validator-sourced with outcome allow or deny and a
  coherent native rc, and `associateValidatorVerdicts` reports no association
  issue for the step. Otherwise `unestablished`. Pass the result into
  `computeComparison` as typed evidence, below. Audit remediation shares the
  full eligibility predicate with encoding, including native NONE normalization
  and worker PID/lifetime.
- [x] Conclusion from typed evidence, never from labels. Introduce an internal
  `ComparisonEvidence` value with one enum per obligation: `order`
  (`queryFirst` or `unestablished`, from the rule above), `state`, `identity`,
  `attribution`, `mutation` (`none`, `sameTargetUnordered`,
  `sameTargetAfterQuery`), plus the existing relations and observation.
  `agreement` requires `mutation != .sameTargetUnordered`; with `order ==
  .queryFirst` the same-target case becomes `.sameTargetAfterQuery`, the
  limitation is not rendered, and agreement returns. In this schema
  `state` has exactly one case, `unestablished`, and `identity` has
  `unestablished` for path filters and `notApplicable` otherwise; the
  `established` cases do not exist yet and are added only by the future
  contract that defines their evidence. `conclusion` is a pure function of
  this value: `disagreement` requires `order == .queryFirst`, `state ==
  .established` and `identity != .unestablished`, so it cannot be constructed
  today. The public `limitations` array is rendered from the same value after
  the conclusion is fixed: `state_stability_unestablished` is emitted for
  `.unestablished`, and so on. A refactor that drops a string from the
  renderer changes what the array says; it cannot change the conclusion,
  because the conclusion never reads the array and the case it needs is not
  there to construct.
- [x] Negative controls for that mechanism. In `DriftClassifierTests`,
  `ordered_difference_does_not_imply_drift` builds the evidence value with
  every other prerequisite satisfied, empties the rendered array, and requires
  `unavailable`; a derivation row requires `limitations == render(evidence)`
  for every constructed comparison; and
  `same_target_unlink_allow_ordered_is_agreement` is the counterpart of the
  batch-0 pair, showing that established order, not a changed verdict, is
  what restores agreement. In `OrderingTests`, a public
  `PWRunnerComparison` carrying `disagreement` with an empty array, or with
  `order: query_first` alone, fails the encoder invariant. In
  `tests/lib/consumer.py`, `disagreement` on response 8 is rejected for want
  of evidence the schema cannot express, and the control that deletes the
  strings is still rejected. State this consequence in the contract and the
  guide: no current producer path yields `drift: true` after this batch.
- [x] `classify`: add 11 to the operation-name table as "proceed wait" so the
  timeout detail reads as such; death while waiting and a deadline that
  expires with `proceedSet` true and `proceedObserved` false already reach
  `runner_failed` and `runner_timeout` through the existing disposition and
  deadline branches; extend their detail strings to say release was not
  observed. No new `NormalizedOutcome`.
- [x] `validator_io_timeout_ms` in `PWRunnerTestOverrides`, plumbed from
  `PWRunnerService.runSpecimen` to `ValidatorClientInput.verdictReadTimeoutMs`
  where the real deadline is computed, floored like `worker_timeout_ms`,
  mirrored back on every result path, with its row in `runner/README.md`'s
  test-seam table. Follow `runner/AGENTS.md` § "Adding a new override";
  `source_drift` fails until the table row exists.

`runner/Sources/PWRunnerCore/PWRunnerAPI.swift`:

- [x] `PWRunnerComparison.order: String?` (required on ordinary new replies);
  `PWRunnerOrdering` with the three booleans, `validator_disposition`,
  `worker_lifetime_established` and `protocol_violations`; `PWRunnerSubprocess.ordering:
  PWRunnerOrdering?`; `PWRunnerRunResult.schema_version` default 8. Legacy
  decoding needs nothing: both new fields are optional on decode and the
  encoder controls pin that new responses always emit them where the table
  requires.
- [x] Audit remediation: `PWRunnerReportingFailure`, the narrow comparison-free
  failure envelope, strict encoding guards, shared eligibility and an explicit
  manual-field maintenance contract with reflection only in tests.

`runner/Sources/PWRunnerCore/PWRunnerService.swift`:

- [x] Audit remediation: `pwRunnerReplyData` replaces the silent `{}` fallback.
  It retains observations and the original summary, removes every derived step
  comparison, and reports host reply failure. Repeated encoding failure emits a
  minimal diagnostic reply with explicit evidence loss. Review this contract and
  implementation before batch 3.

Fixtures and consumers:

- [x] `tests/fixtures/worker_lifecycle/worker.c` tokens: `proceed_wait`
  (wait, acknowledge, report), `proceed_expire:<ms>` (short budget, publish
  the timeout and `done`), `signal_awaiting_proceed`, `ignore_proceed`,
  `signal_after_ack`, plus audit remediation's `proceed_ack_gate`. Each publishes through the same release/acquire
  protocol as the worker. The fixture README documents them.
- [x] `tests/lib/consumer.py`: version-gated rules from section E. On ordinary 8,
  require `order` on every step and `ordering` on every subprocess object,
  require the order limitation exactly when `order` is not `query_first`,
  reject `query_first` when any prerequisite the envelope carries is
  missing, and keep the response-7 blanket rule for stored fixtures.
  Explicit reporting failures follow the narrow exception above.
- [x] `tests/lib/blackbox.py` shape checks gain `order` when the version is
  at least 8; the three live filter callers pass
  `--expected-schema-version 8`.
- [x] `controller/src/runner_client.rs` tests: a version-8 round trip with
  the new fields and with an unfamiliar `order` string.

Tests: section B, the `runner_unit` items in section C, section E, and the
encoding/builder rows in `OrderingTests`. The driver tests can be written before the
host change against the new fixture tokens; `proceed_wait_then_report` fails
until the driver stores release, `proceed_wait_expire` fails until it reads
`proceed_observed`. The consumer controls are offline and can be written
first against hand-written envelopes.

Gate 2 passed: sections A and B green on a signed ABI-7/response-8 build,
with the batch-0 classifier/enrichment/consumer controls and adapted live
witnesses also green. Exact evidence is recorded at the top of this plan.

### Batch 3: witnesses, equipment and negative controls

- [ ] Gated validator bridge, beside `tests/fixtures/validator/`: a C program
  linked against libsandbox that reads the batch probes, connects to
  `--gate SOCKET`, announces readiness, and then emits each verdict only when
  the gate sends one byte for it and closes collection only when the gate
  says so. `control.py` in `tests/fixtures/exec/` is the socket and PID
  pattern to copy. A `validator_bridge` suite, Baseline, requiring clang,
  owns its direct controls: readiness before any verdict, exact native
  forwarding compared with a direct `sandbox_check` call from the test,
  holding collection open without exit, and no output after close.
- [ ] Finish section C's CLI cases: add `signal_after_one.json` in
  `tests/fixtures/validator/` and its registered case, update the transcript
  README, and strengthen the existing spawn-failure case with exact ordering
  assertions and independent effects. The deadline case (`deadline.json`)
  and both partial-output ordering cases are already implemented and verified.
- [ ] Section D, each registered in `witness_contract/run.sh`'s script list
  and `tests/catalog.json` with its own script, `RunCapture`, log capture
  disabled, external observation before decoding. `queries_precede_attempts`
  retires `removed_target_prediction_is_not_drift`.
- [x] `run_effects/check_file_actions.py`: the `raced` expectation becomes
  `allow`, `drift: false`, `order: query_first`; the README paragraph about
  the race becomes a sentence pointing at the witness.
- [x] `runner_ready_byte_resilience` and the two post-apply seam cases gain
  their ordering assertions.
- [ ] Section G, under `witness_contract/opt_in/` following
  `runner_exec_inheritance/opt_in/mutations.sh`: a patched worker with the
  wait removed and a patched host driver with the release stored before the
  hook, each built from a disposable source copy. The worker control runs the
  harness quiescence scenario and, with the `identity` prerequisite, a signed
  app copy under `/private/tmp` with the patched worker swapped in, against
  `attempt_effects_wait_for_collection`. The host control runs the SwiftPM
  driver gate test against the patched core; the CLI half needs a rebuilt,
  re-signed service and is registered with `identity` as equipment. Both
  must fail for the named violation and pass with the unpatched sources.
  Entry in `tests/OPT_IN_TESTS.md`.
- [ ] Finish section F after the remaining witnesses and mutation controls land.
  The current protocol, budget, guide, README and FAQ changes are already checked
  above; remaining registry/per-suite documentation and final acceptance must
  describe the completed batch-3 coverage. No additional normalized outcome is
  needed for batch 3.

Gate 3 and gate 4 as written in "Acceptance gates".

### Names in one place

All protocol, budget and schema names below are implemented. Only the
batch-3 bridge fixture and suite remain provisional.

| Thing | Name | Where |
| --- | --- | --- |
| Release sentinel | `proceed` | header offset 56 |
| Acknowledgement sentinel | `proceed_observed` | header offset 60 |
| Worker operation | `PW_OP_PROCEED` = 11 | ABI header |
| Worker failure | `PW_FAILURE_PROCEED_TIMEOUT` = 8 | ABI header |
| Worker budget | `PW_PROCEED_WAIT_MS_DEFAULT`, limit id `worker_proceed_wait` | `pw_probe_runner.c`, `docs/limits.json` |
| Worker argv seam | `--proceed-wait-ms` | harness only |
| Request override | `validator_io_timeout_ms` | `PWRunnerTestOverrides` |
| Run-level evidence | `runner_subprocess.ordering` | response 8 |
| Per-step evidence | `comparison.order` | response 8 |
| Host reply failure | `runner_reporting_failed`, `reporting_failure` | response 8; comparisons absent, drift null |
| Interim limitations | `attempt_mutation_order_unestablished`, `host_path_resolution_changed` | response 7 and later |
| Bridge fixture and suite | `tests/fixtures/validator/bridge.c`, `validator_bridge` | batch 3 |

## Design decisions

- Batch ordering of collected eligible predictions before all attempts; no
  shared snapshot and no per-step interleaving.
- Collection closure, not confirmed validator termination, is the release
  condition. Child disposition remains independently reportable.
- Bounded proceed wait with failure on expiry or unusable clock; no new bound
  on the existing post-done spin or host's final reap.
- Add `validator_io_timeout_ms` at the real deadline, with request mirroring.
  Use acknowledged validator gates for controlled timing, not worker sleeps.
- Keep both the explicit per-step `order` field and its consistent limitation.
  Their derivation includes record eligibility and worker policy lifetime.
- On host reply-construction failure, retain diagnostic observations and the
  original summary while withholding all comparisons. Do not turn an encoder
  rejection into `{}` or a worker/policy failure. Explicitly mark evidence loss
  if even the degraded result cannot be serialized.
- Keep supported mutation and resolution-change observations after ordering
  lands. A same-step mutation ordered after its own query is not a pre-query
  confound; while its order is unestablished it is a confound for agreement
  and disagreement alike; earlier-step mutations can still explain a later
  comparison.
- Preserve the strong meaning of `drift: true`. Ordering cannot discharge
  material state, identity, scope or enforcement-attribution uncertainty.
- Require the two barrier-bypass controls for acceptance; their opt-in registry
  placement controls when mutation builds run, not whether they are necessary.

Numeric budgets and protocol names are settled and inventoried. Remaining
batch-3 sequencing and fixture names must preserve these decisions. Gates 1–2
and their retained evidence are recorded above; gates 3–4 remain pending.
