# Plan: pace worker waits while preserving live witnesses

## Result and boundary

Investigate [outflow Direction 3](FOOTPRINT-OUTFLOW.md#direction-3-pace-the-sandboxed-workers-waits):
can the worker remain alive, queryable and correctly ordered while spending much
less CPU between protocol observations? The first production candidate paces
`wait_for_proceed` and `wait_for_activation`. Qualify the pause first, introduce
it at release waiting, then extend it to parked activation only after release
controls pass. Deliver a matched CPU and responsiveness account, or an evidenced
decision to retain the current implementation.

The lifetime lesson remains: a validator must query the correct live worker,
in its established sandbox state, before the requested attempts. Continuous
execution is a separate implementation choice. Keep the arrival, collection,
release and acknowledgement protocol, process identities, fresh processes and
shared-memory publication order. Do not replace the barrier with a timed delay.

Leave host polling, `wait_exchange`, exec-child supervision, capacities, budgets,
authority transport and teardown unchanged. Exchange waiting occurs during an
operation and has different precedence; it needs a separately isolated hold
and acknowledgement experiment before optimization. Parked pacing still affects
exchange responsiveness through inbound delivery service, so that consequence
belongs in this plan's acceptance work.

## What the source and history establish

The three loops in [the worker](../controller/tools/pw_probe_runner/pw_probe_runner.c)
end unsuccessful polls with 1,000 `cpu_relax` instruction hints. They do not have
one interchangeable decision order:

| Wait | Decision order and work while waiting |
| --- | --- |
| Release | Validate continuous time; check lifetime cutoff, proceed allowance and deadline arithmetic; reject a future release ordinal; observe cancellation; accept the exact release. No inbound delivery service. |
| Parked activation | Validate continuous time; check cutoff and deadline arithmetic; observe cancellation; accept the named activation or reject a future ordinal; service one inbound delivery without consuming it. No separate proceed allowance here. |
| Exchange, unchanged | After initial clock setup, accept a nonzero acknowledgement before sampling time; otherwise check cutoff, exchange allowance and cancellation, then service inbound delivery. |

Release and activation exclude the sampled accepted wait from the local exec
deadline exactly once. [Timing helpers](../controller/tools/pw_probe_runner/pw_worker_timing.h)
own continuous-clock validation and arithmetic; [LIMITS](../docs/LIMITS.md) owns the
allowances. A decision based on a valid sample can be acknowledged later: the
existing guarantees are sampled decisions, not instantaneous responses.

History supplies two distinct reasons for caution. Commit `ab1d9707` removed
`nanosleep` from an earlier exit wait because the policy might refuse it; its
account does not demonstrate such a refusal. The retired clock investigation
in `bfae9d44:records/SAFE-WAIT-TIME-INVESTIGATION.md` does demonstrate
post-apply `CLOCK_MONOTONIC` failures and worker-PID denial events, even after
successful pre-apply reads. Commit `085e23e6` introduced validated continuous
Mach timing. Neither a source comment nor a successful warm-up qualifies a new
post-apply dependency.

## Execution

1. **Preserve the comparison and qualify one pause.** Record the baseline source,
   signed app, worker identity, equipment and power state. Begin with a requested
   1 ms relative `nanosleep` between unsuccessful polls. This is an experimental
   cadence, not a deadline or responsiveness guarantee: Apple's
   [API account](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/nanosleep.2.html)
   permits overshoot and signal interruption. Inspect the installed call path
   and first-use behavior, including resource acquisition and failure paths.
   Published [Apple libc source](https://github.com/apple-oss-distributions/Libc/blob/55b54c0a0c37b3b24393b42b90a4c561d6c606b1/gen/nanosleep.c)
   is a lead, not proof of the installed implementation. If that wrapper adds
   an unsuitable dependency, evaluate direct `mach_wait_until` as the single
   alternative, explicitly separating its deadline clock from PW's continuous
   clock. Do not expand into a survey of wakeup mechanisms.

   Add a registered opt-in native applicability control beside
   [`native_clock`](../tests/CHANGE-VERIFICATION.md#native-worker-clock-applicability).
   Use fresh children, the intended production initialization order and first
   pause after apply. Cover allow-default, bare deny-default, the historical
   version-2 deny-default plus file-read-data policy, and unapplied actor mode;
   retain three repetitions per configuration. Record actual return/error,
   elapsed and CPU intervals, live process generation, interruption behavior,
   independent exit/reap, and worker-PID log observations with a known-denial
   control. Unavailable logging cannot establish absence. Demonstrate an actual
   pause rather than treating zero return as proof. In the integrated candidate,
   have the validator query the same held generation while pacing; process
   existence alone is insufficient. Scope applicability to the observed system
   and profiles, not all possible policies or OS versions.

2. **Insert pacing without moving decisions.** Replace only the unsuccessful
   poll's relax batch. Keep each loop's loads, stores, service and precedence in
   their present order. Do not sleep between a validated release decision and
   acknowledgement. Bound each requested pause by the remaining applicable
   allowance/cutoff from the sample; use checked conversions. After success or
   interruption, return to the complete decision loop instead of retrying the
   unslept remainder. Never renew a deadline, infer elapsed time from requested
   sleep, or feed continuous ticks to an API using another clock basis.

   Unexpected pause errors end the wait without release acknowledgement or
   attempts. Preserve the native result/error as apparatus failure at proceed
   or activation: `PW_FAILURE_NATIVE` with `PW_NATIVE_INTEGER`, the actual
   return value and POSIX errno when applicable. Name the primitive in the
   diagnostic; do not call it a clock failure or a requested operation's sandbox denial.
   Review the host and independent readers and add a forced-error control before
   crediting this path. No silent spin fallback or repeated refused sleep. If
   honest failure publication needs a wider protocol change, stop and revise
   the plan before that change. Revise the no-sleep comment only after the new
   dependency is qualified. No new inherited descriptors, ports, helper threads,
   event channels, policy exceptions or post-apply resource preparation.

3. **Establish ordering, deadlines and responsiveness independently.** Extend
   the [worker harness](../tests/suites/runner_c_worker_harness/README.md) at the
   real pause boundary for success, interruption, unexpected failure, overrun,
   cancellation during the pause and release/activation during the pause.
   Preserve exact-expiry refusal, stale/future ordinal handling, sticky clock
   faults, once-only exclusions and absent effects on refusal. Simulate a
   continuous-time jump across expiry and verify that the next decision refuses;
   this does not establish actual system sleep/wake behavior.

   Add generation-bound timing brackets for release-to-acknowledgement,
   activation-to-observation, parked delivery-to-acknowledgement and
   cancellation/expiry-to-ending. Exercise delivery to a parked recipient,
   self-transfer, revisits and shortened exchange allowances without changing
   `wait_exchange`. Retain raw intervals and observer uncertainty. Use short
   response probes with uncertainty small enough to resolve the requested pause;
   the CPU accounting quantum is not a response-time uncertainty estimate.
   Delayed quiescence alone cannot expose a response regression. Review the source
   anchors and rerun both mutations in the required
   [order-barrier control](../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls);
   a mutation that fails to build or apply has not detected early action.

4. **Measure the tradeoff on matched equipment.** Reuse
   `witness_contract/held_phase_footprint` for ordinary, one-actor, three-actor
   and actor-lifecycle holds, with both duration classes and three repetitions.
   Record per-role CPU/elapsed intervals, host and validator demand, busy and
   sleeping controls, observer cost, effects and actual cadence. Keep generation,
   sampling-skew, hold-length and sleep-overlap checks. Replace the assertion
   that every worker exceeds the sleeper: it describes today's mechanism.
   Preserve independent CPU-unit calibration, busy-versus-sleeper sensitivity,
   and rejection controls for invalid measurements. Version changed receipts
   explicitly; retain the ability to interpret baseline evidence.

   Run baseline and candidate with identical observer/checker code, separately
   reporting active and parked workers. Require a repeatable reduction larger
   than the declared accounting uncertainty in each changed wait role. A source
   change alone cannot establish this optimization's benefit. Report all
   responsiveness samples and their largest observed intervals; investigate a
   repeatable regression exceeding the requested pause plus measurement
   uncertainty. That comparison is a diagnostic trigger, not a scheduler bound.
   Require the existing actor timing qualification's allowance margin as well
   as successful operations. If CPU improvement or response cost remains
   ambiguous, retain the result and stop; do not widen allowances, loosen
   observers or search indefinitely for a favorable cadence.

5. **Accept the integrated candidate.** Regenerate worker identity, build through
   the signed pipeline and inspect the exact candidate. Through `tests/run.sh`
   in fresh managed output, inspect selections with `--list`, then run
   `--suite runner_unit`, `--suite runner_abi_layout`,
   `--suite runner_c_worker_harness` (including its opt-in native controls),
   `--suite source_drift`, and the new native applicability case. Explicitly
   select `witness_contract/order_barrier_mutations`,
   `witness_contract/held_phase_footprint`,
   `witness_contract/response_footprint`, `witness_contract/actor_compositions`,
   `witness_contract/actor_timing_qualification` and
   `witness_contract/extension_boundaries`, then run the default battery
   separately. Include coordinated failure/consumer checks if failure evidence
   or its interpretation changes. These checks must retain cleanup and custody
   endings, not merely final success. Keep failed observations and diagnose
   equipment failures without changing the artifact to conceal them.

6. **Publish the supported result and retire the plan.** Update fw1–fw2 and
   affected measured rows through [footprint.json](../docs/footprint.json), regenerate
   FOOTPRINT and identify the exact provenance behind each measurement group.
   Review the [worker capability inventory](../docs/WORKER.md#detailed-capability-inventory)
   through architecture.json and its generator for the new post-apply dependency.
   Keep budgets in LIMITS and measured demand in FOOTPRINT. Claim lower measured
   CPU only for the observed waits; exchange polling remains. Actual system
   sleep/wake remains unverified unless separately arranged and observed.
   Retain current default and complementary evidence through the normal helpers,
   commit implementation, tests and documentation, remove the consumed part of
   outflow Direction 3 while retaining its exchange question, and retire this
   plan and any temporary acceptance records. If qualification rejects both
   candidates, record the reason in the outflow and retire the completed
   investigation without a production change.

## Coordination and stops

Use one implementer and an independent reviewer if delegated; the coordinator
owns source integration, evidence and acceptance. Serialize builds and native
runs, cap compiler concurrency at two, and request a quiet interval for matched
CPU/response measurements. Limit sustained holds to three workers; announce the
existing short eight-actor qualification before running it. Record battery/AC
changes and do not pair runs across changed conditions. Do not induce system
sleep; any dedicated sleep/wake experiment needs an arranged window.

No scheduled approval pause is needed during execution. Stop dependent work for
unqualified native behavior, changed query eligibility or ordering, ambiguous
attribution, a new resource/authority requirement, unresolved cleanup, missing
required observations or an unacceptable CPU/response tradeoff. Preserve the
baseline and the negative evidence so stopping remains an informative result.
