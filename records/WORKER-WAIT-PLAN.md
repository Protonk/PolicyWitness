# Plan: pace worker waits while preserving live witnesses

## Result and boundary

Investigate [outflow Direction 3](FOOTPRINT-OUTFLOW.md#direction-3-pace-the-sandboxed-workers-waits):
can the worker remain alive, queryable and correctly ordered while spending much
less CPU between protocol observations? The first production candidate paces
`wait_for_proceed` and `wait_for_activation`. Qualify the pause first, introduce
it at release waiting, then extend it to parked activation only after release
controls pass. Release-only pacing is an acceptable outcome if parked pacing
fails its own qualification or responsiveness checks. A failure in the shared
pause dependency also disqualifies release pacing wherever that failure applies.
Deliver a matched CPU and responsiveness account for the final changed waits,
or an evidenced decision to retain the current implementation.

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

The recollection that `nanosleep` replaced another problematic sleep/wait
mechanism remains an unresolved historical lead. Do not equate it with the
documented clock failure or assume a direct native wait avoids the original
problem. Review earlier choices before trying the alternative; establish what
is known about their failure modes and qualify the proposed path independently.

## Execution

1. **Preserve the comparison and qualify one pause.** Record the baseline source,
   signed app, worker identity, equipment and power state. Begin with a requested
   1 ms relative `nanosleep` between unsuccessful polls. This is an experimental
   cadence, not a deadline or responsiveness guarantee: Apple's
   [API account](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/nanosleep.2.html)
   permits overshoot and signal interruption. Inspect the installed call path
   and first-use behavior, including resource acquisition and failure paths.
   Published [Apple libc source](https://github.com/apple-oss-distributions/Libc/blob/55b54c0a0c37b3b24393b42b90a4c561d6c606b1/gen/nanosleep.c)
   is a lead, not proof of the installed implementation.

   A qualification failure or failure of the CPU/response acceptance criteria
   can justify one alternative, direct `mach_wait_until`, only when inspection
   or measurements identify a cause specific to the `nanosleep` path that the
   alternative could remove. Record that causal hypothesis before the trial.
   Compare installed paths and their initialization, acquired resources,
   clock domains, interruption/restart behavior, native failures and behavior
   across system sleep. Explicitly separate the alternative's deadline clock
   from PW's continuous clock. A lower-level call is not automatically a safer
   or faster one. If the paths share the relevant mechanism and the observed
   problem is scheduling or the chosen cadence, stop rather than switching
   names. Apply the full qualification and acceptance criteria to any alternative
   that would ship; keep the experiment to these two candidates at the same
   requested cadence, without a survey of wakeup mechanisms.

   Add a registered opt-in native applicability control beside
   [`native_clock`](../tests/CHANGE-VERIFICATION.md#native-worker-clock-applicability).
   Use fresh children, the intended production initialization order and first
   pause after apply. Cover allow-default, bare deny-default, the historical
   version-2 deny-default plus file-read-data policy, and unapplied actor mode;
   retain three repetitions per configuration. Required observations are
   successful application or declared unapplied setup, actual return/error,
   elapsed and CPU intervals, live process generation, interruption behavior
   and independent exit/reap. Demonstrate an actual pause rather than treating
   zero return as proof. In the integrated candidate,
   have the validator query the same held generation while pacing; process
   existence alone is insufficient. Scope applicability to the observed system
   and profiles, not all possible policies or OS versions.

   Unified logs are supplemental diagnostics, not a qualification prerequisite
   or a trusted absence detector. The [logging account](../docs/QUESTIONS.md#can-policywitness-collect-sandbox-denial-logs)
   identifies PW's former observer as archived; this investigation does not
   restore it or make its availability part of the worker protocol. Attempt
   bounded worker-PID log collection and a known-denial control when available,
   separately from the matched CPU/response windows. If the automation sandbox
   refuses access, retry the same query once outside it as prescribed. If logs
   remain unavailable, record the command/status, reason and unavailable control,
   then proceed with qualification from the required direct observations.
   Distinguish unavailable collection, an unobserved positive control and a
   successful query with no matching records; none establishes absence of
   sandbox denials or complete log coverage. A positive control only establishes
   that its own event was observed.

   Report successful qualification with its explicit limit: the pause worked
   under the recorded policies and equipment, but log silence, missing logs
   and a permission-shaped failure establish no sandbox-cause attribution.
   Retain and investigate relevant positive log evidence without automatically
   assigning it to the pause or a requested action. Missing logs cannot excuse
   failed native calls, missing generation/query evidence, ordering or lifecycle
   failures, or failure of the CPU/response bars. Give the applicability checker
   independent controls showing that unavailable logs permit otherwise complete
   qualification and do not mask a simultaneous failure of required evidence.

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
   reporting active and parked workers. Fix matching, uncertainty accounting
   and response probe repetitions before candidate measurements. For this
   1 ms cadence, acceptance requires both:

   - At least 90% lower worker CPU per elapsed time in each changed wait role,
     in each hold class and valid matched repetition, after accounting for
     measurement uncertainty. Unchanged parked workers in a release-only build
     have no reduction requirement; retain their measurements separately.
   - At most 2 ms additional worst-observed response latency in each matched
     workload and response class from step 3, including cancellation and expiry
     endings. Compare the candidate maximum's upper observation bound with the
     baseline maximum's lower bound, so uncertainty cannot conceal a regression.
     Report every sample and both maxima; do not infer a population tail bound
     from this finite experiment.

   These are engineering acceptance bars chosen before measurement, not values
   established by existing observations or changes to runtime limits. Preserve
   the existing actor timing qualification's allowance margin and all correctness
   requirements. Review diagnoses breaches; it does not waive a repeatable
   breach or unresolved uncertainty. Retain failed observations and any justified
   diagnostic rerun. Do not discard unfavorable valid samples, widen allowances,
   loosen observers or search for a favorable cadence. If the alternative's
   causal condition is met, evaluate it under the same bars; otherwise stop the
   failing stage. A source change alone cannot establish the CPU benefit.

5. **Accept the integrated candidate.** If parked pacing fails independently,
   remove it and keep release pacing only if its own qualification and acceptance
   criteria hold. Rebuild, remeasure and verify that exact release-only candidate;
   passing results from an earlier stage do not accept a different final build.
   Retain actor and parked-delivery regression coverage even when parked polling
   is unchanged. A common primitive failure cannot be isolated by merely removing
   parked pacing. Regenerate worker identity, build through the signed pipeline
   and inspect the exact candidate. Through `tests/run.sh`
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
   equipment failures without changing the artifact to conceal them. Report
   log availability separately from the applicability verdict; unavailable
   supplemental logs do not skip the native case or block an otherwise
   supported acceptance.

6. **Publish the supported result and retire the plan.** Update the changed
   mechanism rows (fw1 for release-only; fw1–fw2 for both waits) and affected
   measured rows through [footprint.json](../docs/footprint.json), regenerate
   FOOTPRINT and identify the exact provenance behind each measurement group.
   Review the [worker capability inventory](../docs/WORKER.md#detailed-capability-inventory)
   through architecture.json and its generator for the new post-apply dependency.
   Keep budgets in LIMITS and measured demand in FOOTPRINT. Claim lower measured
   CPU only for the observed changed waits; identify any unchanged parked
   polling and retain its measured cost. Exchange polling remains. Actual system
   sleep/wake remains unverified unless separately arranged and observed. Carry
   the log-availability and attribution limits into the retained acceptance
   evidence; do not promote qualified operation into a denial-free claim.
   Retain current default and complementary evidence through the normal helpers,
   commit implementation, tests and documentation, remove the consumed part of
   outflow Direction 3 while retaining its exchange question and any unresolved
   parked-wait question with its rejection evidence, and retire this plan and
   any temporary acceptance records. If no candidate meets qualification and
   acceptance, record the reason in the outflow and retire the completed
   investigation without a production change. Retiring a release-only plan does
   not accept parked pacing or erase what disqualified it.

## Coordination and stops

Use one implementer and an independent reviewer if delegated; the coordinator
owns source integration, evidence and acceptance. Serialize builds and native
runs, cap compiler concurrency at two, and request a quiet interval for matched
CPU/response measurements. Limit sustained holds to three workers; announce the
existing short eight-actor qualification before running it. Record battery/AC
changes and do not pair runs across changed conditions. Do not induce system
sleep; any dedicated sleep/wake experiment needs an arranged window.

No scheduled approval pause is needed during execution. Stop dependent work for
unqualified native behavior, changed query eligibility or ordering, unsupported
causal claims needed for acceptance, a new resource/authority requirement,
unresolved cleanup, missing required direct observations or failure of the
stated CPU/response acceptance bars. Unavailable supplemental logs, or an
explicitly withheld sandbox-cause claim, are not blockers by themselves.
An independently failing parked stage permits the release-only outcome above.
Preserve the baseline and the negative evidence so stopping remains an
informative result.
