# Ordering predictions before attempts

## Status: plan only

Nothing below is implemented. This document fixes the promise PolicyWitness will
make about the order of its two channels, and lists the tests that would hold
that promise to account before, during and after the change. The implementation
sketch at the end is deliberately thin; a separate action plan will own it.

## The observation that started this

`run_effects/file_actions_have_exact_effects` runs an allowed `unlink` under
`(version 1) (allow default)`. The attempt succeeds and the target is gone. The
prediction for the same operation and path is `deny`, five runs out of five,
and the envelope reports `drift: true`. Two controls locate the cause: querying
`file-write-unlink` on a file that persists returns `allow`; querying
`file-write-data` on the file that gets unlinked returns `deny`. The query is
evaluated after the attempt has removed its subject.

The mechanism is in two places. `pw-probe-runner` publishes the `applied`
sentinel and immediately begins its attempt loop. `CWorker.run` fires the
post-applied hook, which runs the validator synchronously, on the first polling
iteration after it observes `applied`. Nothing orders the validator's queries
against the worker's attempts. The comparison builder attaches
`query_attempt_order_unestablished` and `state_stability_unestablished` to every
comparison unconditionally, and `tests/lib/consumer.py` requires both on every
response-7 step. A limitation present on every step cannot tell a reader which
step is the one where the state actually changed.

`drift: true` is therefore a claim about the sandbox that the evidence does not
support: the two channels were asked about different worlds. The FAQ, the README
and the user guide describe `true` as disagreement. Under "no dishonest
attribution", this row must project to `null` today, and the durable fix is to
make the order a fact rather than a disclaimer.

## The promise

After this work, PolicyWitness promises, for every run in which the worker
applied its policy:

1. The worker attempts nothing until the host has released it, and the host
   releases it only after the validator has finished, whether by clean exit,
   partial output, decode failure, I/O deadline, spawn failure or kill.
2. Every prediction that appears in the envelope was obtained from
   `sandbox_check` against the sandboxed worker PID, under the applied policy,
   before the worker's first attempt of the plan began.
3. The envelope carries the evidence for 1 and 2 as observations of the worker
   and the host, not as a host assertion, and a consumer can check those
   observations against each other within one envelope.

The promise is about PolicyWitness's own actions. It does not promise:

- that the target's state is unchanged between the query and the attempt by
  anything other than the worker (`state_stability_unestablished` remains a
  blanket limit, honestly);
- that the path spelling names the same runtime object at both times
  (`runtime_target_identity_unestablished` remains);
- that a query was requested: planning exclusions (a target that does not
  resolve on the host, unrecognized filter kinds, prediction-unavailable pairs)
  keep their existing `missing_reason` and the step keeps `drift: null`;
- anything about attempts whose prediction was excluded or never returned;
- per-step interleaving. All queries of the plan complete before any attempt
  of the plan begins. A later step's prediction is about the state before the
  plan ran, not the state its earlier siblings produced. This is a design
  decision recorded in "Open decisions" and pinned by tests below.

## Starting points

- `controller/tools/pw_probe_runner/pw_probe_runner.c`: `applied` store, the
  attempt loop that follows it, `spin_for_exit`, the `prepared` refusal, the
  existing `clock_gettime` deadline pattern, the argv seams
  (`--post-apply-hang-ms`, `--post-apply-kill-signal`, `--pre-ready-hang-ms`).
- `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`: header sentinels,
  ABI 6 evidence record (`PW_OP_*`, `PW_PROGRESS_*`, `PW_FAILURE_*`),
  `PW_PROBE_RUNNER_ABI_VERSION`.
- `runner/Sources/PWRunnerCore/CWorker.swift`: the polling loop, the
  post-applied hook, the rule that the hook fires before `done` is checked, the
  sentinel budget that excludes synchronous hook time.
- `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift`: the hook that runs
  `runValidator`, `computeComparison` and its unconditional limits.
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
- `tests/lib/consumer.py`, `tests/lib/blackbox.py`,
  `tests/FAILURE-PROPAGATION-CONTRACT.md` § "Public representation and meaning"
  and § "Permanent consumer enforcement": what consumers currently require.
- `docs/LIMITS.md`, `docs/limits.json`: every budget below must be inventoried.

## Evidence design, briefly

No wall clocks. Order is a happens-before chain through the shared-memory
protocol PolicyWitness already uses, and each link is an observation owned by
one party:

| Link | Owner | Observation |
| --- | --- | --- |
| Validator finished before release | Host | The host stores the release sentinel only after `runValidator` returns; it records that the store happened and the validator disposition it saw at that moment. |
| Release before first attempt | Worker | The worker publishes that it observed the release sentinel, and does so before its first `PW_OP_ATTEMPT` started record. A worker that never observes release publishes a proceed failure and attempts nothing. |
| Verdict belongs to the ordered set | Host | A verdict record counts as ordered only if it was received before the release store. Under the design above that is every received verdict, and the envelope says so per step. |

Provisional names, to be settled by the action plan: header sentinels
`proceed` (host to worker) and `proceed_observed` (worker to host); worker
operation `PW_OP_PROCEED`; failure `PW_FAILURE_PROCEED_TIMEOUT`; a worker wait
budget `worker_proceed_wait`; a worker argv seam `--proceed-wait-ms`; run-level
`runner_subprocess.ordering` with the three observations; per-step
`comparison.order` in `{"query_first", "unestablished"}`, with the limitation
`query_attempt_order_unestablished` present exactly when `order` is not
`query_first`. ABI 6 becomes 7. Response 7 becomes 8. Request schema stays 1.

## Interim classification, independent of ordering

Before any ABI change, the raced row must stop projecting to `true`. The host
already holds the evidence: the attempt is an `unlink` that reported success,
the query was planned (so the path resolved before the run), and the
post-orchestration path diagnostics show it no longer resolves. That triple is
step-specific.

- [ ] `runner_unit` / `DriftClassifierTests`: constructed rows for
  (`unlink`, `ok`, planned query, path unresolved after) yield
  `conclusion: "unavailable"`, a specific limitation
  (`target_removed_by_attempt`, name provisional), `drift: null`, and the
  `deny` prediction retained as recorded. Rows with the same attempt but a
  path that still resolves keep `disagreement`. Rows where the attempt failed
  keep their existing conclusions. A row with the limitation but no
  supporting triple is rejected by the encoder controls.
- [ ] `witness_contract/removed_target_prediction_is_not_drift`: the
  `run_effects` unlink row through the CLI, asserting `drift: null`, the
  specific limitation, the retained `deny`, and independent absence of the
  file. This case is expected to change again when ordering lands (below);
  say so in its README.
- [ ] `run_effects/file_actions_have_exact_effects`: the `raced` expectation
  becomes `drift: null` with the specific limitation. Recording continues.
- [ ] `blackbox_e2e/checker_controls` and `tests/lib/consumer.py`: a fabricated
  envelope with `disagreement` and the removed-target triple is rejected; one
  with `unavailable` plus the limitation is accepted; legacy response-7
  fixtures are unchanged.

## Tests that enforce the promise

Every case names what would make it fail and what it does not establish. Live
cases run through the public CLI unless a boundary is not reachable that way,
in which case the harness or the driver tests own it and the coverage row says
so. No override may fake a result; every seam re-routes a real boundary.

### A. The worker alone (`runner_c_worker_harness`)

The harness plays host. It can set sentinels in any order, at any time, or
never. New scenarios:

- [ ] `proceed_never_set`: harness sets `prepared`, observes `applied`, never
  sets `proceed`. Expect: no slot completes; the worker publishes
  `PW_OP_PROCEED` started and a `PW_FAILURE_PROCEED_TIMEOUT` record after its
  budget; `done` flips; `proceed_observed` stays 0; clean exit on
  `exit_requested`. Fails if any slot completes or the worker hangs past its
  budget plus grace. Does not establish host behavior.
- [ ] `proceed_late_after_expiry`: as above, then the harness sets `proceed`
  after the failure record. Expect: still no slot completes; the failure record
  is unchanged. Pins that a late release cannot resurrect attempts.
- [ ] `proceed_before_applied`: harness sets `proceed` together with
  `prepared`. Expect: attempts run only after `applied`; under
  `SCEN_DENY_DEFAULT_POLICY` every slot is denied, proving the policy was
  applied before the attempt even though release was already visible. Fails if
  a slot succeeds. Does not establish that the host ever sets release early.
- [ ] `proceed_delayed_observed_quiescence`: harness observes `applied`, then
  for 500 ms polls every slot's `completed` flag and the evidence record,
  asserting nothing changes, then sets `proceed` and expects normal completion.
  Fails if any slot completes, or any `PW_OP_ATTEMPT` started record appears,
  before release. This is the direct witness of link 2.
- [ ] `proceed_under_bare_deny_default`: `SCEN_DENY_DEFAULT_POLICY` with a
  delayed release. Pins that the wait loop needs nothing the policy can deny:
  CPU-only spin with a `clock_gettime` deadline, like `spin_for_exit`. Fails
  if the worker dies or times out while waiting.
- [ ] `proceed_wait_budget_short`: pass `--proceed-wait-ms 100`, delay release
  500 ms. Expect the timeout failure record. Then pass `--proceed-wait-ms
  2000` with the same delay and expect success. Boundary control for the
  budget; the production value is inventoried separately.
- [ ] `max_slots_proceed`: `PW_SHM_MAX_STEPS` slots, delayed release. Expect
  every slot completes after release and none before. Fails on any early
  completion at scale.
- [ ] `abi_mismatch` (existing): an ABI 6 worker binary against an ABI 7
  header is refused before application, as today. Add the reverse in the
  driver tests below.
- [ ] `printer.c` in `runner_abi_layout`: emits the new header offsets; the
  Swift `PWShmLayout` mirror must agree. `LimitsContractTests` and
  `ABI_LIMITS` carry `worker_proceed_wait`.

### B. The host driver alone (`runner_unit`, lifecycle fixture)

The fixture plays worker. New stdin tokens:

- [ ] `proceed_wait_then_report`: the fixture waits for release, publishes
  `proceed_observed`, records `mach_absolute_time()` at that instant in its
  diagnostic text, then reports. The driver test supplies a hook that sleeps
  300 ms and records its own return instant. Expect the fixture's instant to
  be at or after the hook's return, `ordering.proceed_set` true,
  `ordering.validator_completed_before_proceed` true, `proceed_observed` true.
  Fails if the driver stores release before the hook returns. Same-machine
  monotonic instants are acceptable inside a unit test; the CLI witnesses use
  no clocks.
- [ ] `proceed_wait_expire`: the fixture's own short budget expires while the
  test's hook blocks on a test-owned gate. Expect the fixture to publish the
  proceed failure and `done`; after the gate opens and the hook returns, the
  driver stores release anyway, observes `done` with zero completed slots and
  `proceed_observed` false, and classifies `runner_failed` with the worker's
  proceed failure as the reported failure. The predictions the hook returned
  survive in the result. Fails if the driver reports a policy cause, drops the
  verdicts, or reports order as established for any step.
- [ ] `hook_throws_before_release`: the hook returns a validator spawn
  failure. Expect release stored, fixture proceeds, attempts complete,
  `ordering.validator_completed_before_proceed` true with disposition
  `spawn_failed`, every step `order: unestablished` because no verdict exists,
  `drift: null` everywhere. Fails if attempts do not run.
- [ ] `signal_while_waiting`: the fixture self-signals after `applied` and
  before observing release (token `signal_awaiting_proceed`). Expect
  `applied` 1, `proceed_observed` 0, `done` 0, confirmed signal status,
  `runner_failed`, no attempt evidence, retained verdicts, no policy cause.
  Complements the existing post-attempt self-signal seam.
- [ ] `hang_while_waiting`: the fixture ignores release (token
  `ignore_proceed`) and never reports. Expect the sentinel deadline,
  termination request, reaping, `runner_timeout`, `proceed_set` true and
  `proceed_observed` false. Fails if the classifier calls it a worker
  attempt hang.
- [ ] `legacy_worker_abi6`: an ABI 6 fixture binary against the ABI 7 host is
  refused before spawn or at header check, with the existing mismatch
  evidence. Pins that an old worker cannot run unordered under a new host.
- [ ] `EnvelopeInvariantTests`: `ordering` encodes exactly its three booleans
  plus disposition; per-step `order` is present on every step of a new
  response; legacy decodes keep their blanket limitations and gain no `order`.

### C. The validator's failures (`runner_validator_failure`, `witness_contract`)

Each existing validator-failure case gains ordering assertions, because the
promise is only interesting when the validator misbehaves.

- [ ] `validator_spawn_failed_reports_degraded`: attempts still run;
  `ordering.validator_completed_before_proceed` true with disposition
  `spawn_failed`; every step `order: unestablished`; `drift: null` on every
  step; independent file effects present.
- [ ] `validator_unavailable_reports_degraded` (2 of 3 verdicts, clean EOF):
  the two received verdicts are `order: query_first`; the third is
  `unestablished` with its existing missing reason; all three attempts ran
  after release; file effects independently observed.
- [ ] `validator_decode_failure_reports_degraded` (malformed JSON after two
  verdicts): same shape as above with the decode fault retained.
- [ ] `validator_io_deadline_releases_worker` (new): a checked-in transcript
  validator that emits one verdict then hangs. Expect the I/O deadline, kill,
  reaping, release stored afterwards, the one verdict `query_first`, the rest
  `unestablished`, attempts completed, `runner_subprocess` normal. This case
  takes the full validator deadline unless a `validator_io_timeout_ms`
  override is added; see "Open decisions". Fails if the worker's own proceed
  budget expires first: pin the documented relation `worker_proceed_wait >
  validator_io_wait + validator_exit_grace` as a value check in
  `LimitsContractTests`.
- [ ] `validator_killed_mid_stream` (new, transcript fixture that dies by
  signal after one verdict): as above with a signaled disposition.

### D. The promise end to end (`witness_contract`)

- [ ] `queries_precede_attempts`: the `run_effects` unlink row, now expected
  to report prediction `allow`, `drift: false`, `order: query_first`, the
  three ordering observations true, and the target independently absent
  afterwards. This is the regression sentinel for the whole effort; the
  interim case from the section above is retired into it.
- [ ] `plan_order_is_pre_plan_state`: two plans. Plan 1: step 1 `create` A
  (absent at planning), step 2 `unlink` A. Expect both predictions
  `prediction_unavailable` with `query_not_requested`, both attempts succeed,
  both `drift: null`, and independent observation that A is absent at the end
  and existed in between (the harness cannot see "in between"; use the
  attempt evidence plus a third step `open_read` A after the unlink that fails
  ENOENT). Plan 2: step 1 `unlink` A (exists at planning), step 2 `open_read`
  A. Expect step 1 `allow`/`drift: false`; step 2 prediction `allow`, attempt
  `open_failed` with ENOENT, observation `other_failure`, conclusion
  `unavailable`, `drift: null`, and no `disagreement` anywhere. Fails if the
  system reports step 2 as drift in either direction. Pins the batch decision.
- [ ] `exec_attempt_after_all_queries`: plan = [`unlink` A (allow), `exec`
  helper in `--tree` socket mode]. The test-owned observer, on the helper's
  connection, (a) confirms A is already gone, (b) walks ancestry to the
  worker and host, and (c) asserts via libproc that the host has no live
  `sb_api_validator` child. PW's step 1 prediction must be `allow`. This is an
  external witness of ordering that reads none of PW's ordering fields until
  after the fact. Fails if a validator child is alive while an attempt runs.
- [ ] `max_steps_ordered`: 256 file steps on distinct existing targets, half
  allowed, half denied by literal. Every step `query_first`; predictions and
  attempts agree per policy; file effects independently observed. Fails on
  any `unestablished` order or any prediction taken from a mutated state.
- [ ] `ready_byte_interplay` (extend `runner_ready_byte_resilience`): with
  `worker_pre_ready_hang_ms` past the ready-byte wait, the worker still
  waits for release after `applied`; expect `order: query_first` and
  `ordering` true.
- [ ] `post_apply_seams_still_after_attempts`: `worker_post_apply_hang_ms`
  and `worker_post_apply_kill_signal` fire after attempts, therefore after
  release; expect `proceed_observed` true in both, and unchanged outcomes
  (`runner_timeout`, `runner_failed`).
- [ ] `deny_default_ordered`: `(deny default)` with one allowed read; expect
  `query_first` on both steps and the usual verdicts. Pins that a hostile
  policy cannot break the wait.
- [ ] `external_mutation_between_query_and_attempt` (adversarial, needs a
  seam `worker_post_proceed_hang_ms` that sleeps after observing release and
  before the first attempt): the test removes A during the sleep. Expect
  prediction `allow` (queried while A existed), attempt `open_failed` ENOENT,
  `order: query_first`, `state_stability_unestablished` still present,
  conclusion `unavailable`, `drift: null`. This pins what the promise does
  not cover, so a future reader cannot read `query_first` as "same state".
- [ ] `pre_apply_failure_reports_no_policy_verdict` (existing): unchanged
  expectations plus `ordering` absent or all-false, no `order: query_first`
  on any step. Fails if a run that never applied claims order.

### E. Consumers and offline controls

- [ ] `tests/lib/consumer.py`: on response 8, require per-step `order` and
  run-level `ordering`; require `query_attempt_order_unestablished` exactly
  when `order` is not `query_first`; require that no step is `query_first`
  unless all three run-level observations are true; keep the response-7 rule
  for stored fixtures. Controls in `blackbox_e2e/checker_controls`: a
  fabricated 8 with `query_first` but `proceed_observed` false is rejected; a
  step with `query_first` and the blanket limitation both present is
  rejected; a legacy 7 with blanket limitations is accepted; an 8 missing
  `order` is rejected; an 8 with `order: unestablished` on a step that has a
  validator verdict while `ordering` is all true is rejected (a verdict that
  arrived before release is ordered by construction).
- [ ] `tests/lib/blackbox.py`: same version gate; the three live filter
  callers pass `--expected-schema-version 8`.
- [ ] `unit/rust.unit` (`runner_client`): response versions 4 through 8
  round-trip; unfamiliar `order` values survive as strings.
- [ ] `runner_unit` Swift encoding: the whole `limitations` array survives
  including unfamiliar values; `order` is a plain string.

### F. Budgets, registry and documentation obligations

- [ ] `docs/limits.json`: `worker_proceed_wait` with value checks in
  `ABI_LIMITS` and `LimitsContractTests`, a boundary note pointing at
  `proceed_wait_budget_short`, and the documented relation to
  `validator_io_wait`. `docs/LIMITS.md` and the guide regenerate.
- [ ] `tests/COVERAGE.md`: no new `NormalizedOutcome`. Proceed timeout and
  death while waiting map to `runner_failed` with the worker's failure record
  as evidence; add those rows to the ABI 7 evidence table in the contract, not
  the outcome matrix. If the action plan decides a new outcome is warranted,
  `source_drift` will demand the matrix row.
- [ ] `tests/README.md`, `tests/catalog.json`, per-suite READMEs: every case
  above registered; `source_drift` enforces.
- [ ] `tests/FAILURE-PROPAGATION-CONTRACT.md` § "Public representation and
  meaning": replace "Every comparison reports
  `query_attempt_order_unestablished`" with the per-step rule; add the
  ordering observations to the host row of the observer table.
- [ ] `README.md` Flow: "with strong-evidence backing" becomes literally true
  for `query_first` steps; say what backing means.
- [ ] `docs/PolicyWitness.md`: `steps[].comparison.order`,
  `runner_subprocess.ordering`, the batch semantics, response 8.
- [ ] `docs/QUESTIONS.md`: the proposed "Which happens first" pair changes
  its answer to "the prediction, always, and here is the evidence that says
  so"; the deferred user-guide pass and this edit go together.
- [ ] `runner/README.md` "Run result highlights": the new fields.

### G. Optional, last

- [ ] Opt-in mutation control: a worker built from a patched source copy that
  skips the release wait must fail `proceed_delayed_observed_quiescence` and
  `queries_precede_attempts`. The same decision that excluded a lying-worker
  control from `run_effects` may apply here; it is listed so the omission is
  a choice.

## Acceptance gates

1. Interim classification: the four items in "Interim classification" pass on
   a signed build with no ABI or schema change, and the default battery is
   green. `run_effects` records the `deny` prediction with `drift: null`.
2. Worker and driver: sections A and B pass. The worker cannot attempt without
   release, cannot be resurrected by a late release, and survives a bare
   deny-default wait. The host cannot release before the hook returns.
3. Validator failures and the end-to-end promise: sections C and D pass,
   including the external observer case. `queries_precede_attempts` replaces
   the interim case.
4. Consumers and documentation: sections E and F pass; `source_drift`,
   `runner_abi_layout`, `runner_unit`, `runner_c_worker_harness`,
   `failure_boundaries` and the Rust unit tests pass; `--all` reports no
   unrun case that this plan added.

Each gate records its signed build hash and the exact case list, following the
reuse rules in `tests/README.md` § "Reusing verification results".

## Sketch of the fix

Thin by design.

- ABI 7: two header sentinels, `proceed` and `proceed_observed`, in the
  reserved header space; one operation code and one failure code; a wait
  budget constant.
- Worker: after storing `applied`, spin CPU-only until `proceed` or the
  budget expires. On release, store `proceed_observed` (release ordering),
  then run the attempt loop unchanged. On expiry, publish the failure record,
  store `done`, and spin for exit. The wait must precede any syscall the
  policy could deny.
- Host: in `CWorker.run`, after the post-applied hook returns for any reason,
  store `proceed` and record the validator disposition and the fact of the
  store. Continue polling as today; the sentinel budget already excludes hook
  time. Read `proceed_observed` into the subprocess evidence at cleanup with
  the other sentinels.
- Orchestrator: derive per-step `order` from the run-level observations and
  the verdict's `result_source`; drop the blanket order limitation for
  `query_first` steps; keep `state_stability_unestablished` everywhere; add the
  removed-target limitation from the interim step as a defense when order is
  not established.
- Response 8: the two new objects and the version bump; everything else is
  additive.

## Open decisions

- Batch versus per-step ordering. This plan assumes batch: all queries, then
  all attempts. Per-step interleaving would make later predictions reflect
  earlier effects but would need a release per step and a validator that can
  pause; it is not proposed here.
- Bounded versus unbounded worker wait. This plan assumes bounded, so a dead
  host leaves a worker that publishes a failure and waits for exit as it does
  today after `done`. The budget must exceed the validator's deadline plus
  grace by a stated margin.
- Whether to add `validator_io_timeout_ms` as a request override so the
  I/O-deadline case runs in seconds. It re-routes a real deadline and mirrors
  back like the others; it is not a faked result.
- Whether per-step `order` is a field or only a limitation's absence.
  Consumers are easier to write against a field; the contract's style prefers
  limitations. The tests above assume both, so either can be dropped.
- Whether the removed-target limitation survives after ordering lands. It is
  kept as a defense for `unestablished` steps in this plan.
