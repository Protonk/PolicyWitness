# Worker wait exploration plan

Explore three ways to reduce the cost of keeping a witness available: prepare
immutable queries before holding workers, remove demonstrated host-side delay,
and reduce repeated worker polling work. Accept useful branches independently;
retaining the current implementation is a valid outcome for any branch.

This plan continues [outflow direction 3](../records/FOOTPRINT-OUTFLOW.md#direction-3-pace-the-sandboxed-workers-waits).
The separate [ARM option plan](ARM-WAIT-OPTION-PLAN.md) investigates a new waiting
mechanism. Neither plan depends on the other succeeding. Keep their candidate
builds and comparisons separate until each accepted change has its own evidence.

## Order of work

This plan's builds and native trials run before the ARM plan's. Open with the
baseline pilot described under measurement, then dispose of branch 2 while its
fixture and decomposition are current, then branch 1, then branch 3. Accepting
or rejecting a branch remains independent of the others; the order fixes
sequence, not outcome.

Within branch 3, the scan cursor may proceed as soon as branch 1 is disposed.
Hint-batch tuning for the release and parked-activation tails waits for the
ARM plan's qualification result for that wait. A qualified ARM candidate at a
tail removes hint tuning there from this plan; a failed qualification leaves
hint tuning as the only remaining tail candidate for it.

The ARM plan's contract research, checker fixtures and pinned-source review run
in parallel as read-only work. Its disposable-child applicability trials use
native trial time this plan is not using and never share a build, output
directory or acceptance record with this plan's candidates. Dispose of
branches 1 and 2 before the ARM plan freezes its production comparison
baseline, so that baseline includes every accepted host-side and preparation
change. Record each of those dispositions in the outflow when it lands.

## Starting point and boundaries

The first-use qualification recorded in the outflow found `nanosleep` returning
`-1/EINVAL` and direct `mach_wait_until` returning `KERN_DENIED` under both tested
deny-default profiles. Production waits remain unchanged. Those results rule
out those candidates on that equipment; they neither assign cause from return
values alone nor establish that all ways of reducing wait cost are unavailable.

Preserve fresh hosts and workers, successful application and live process
identity, fresh per-phase eligibility and validator queries, collection closure,
guarded numbered release, worker acknowledgement, attempts, and independently
observed cleanup. Preserve partial and failed observations. Shared-memory
publication must continue to work under restrictive profiles without acquiring
new post-apply communication resources.

The worker already exits after its final local visit. Parked actors still
serve inbound authority deliveries and enforce their own cutoff. Worker or
validator pooling, delayed actor creation, external suspend/resume, early path
resolution, deferred validator cleanup, and new sandbox-side IPC are outside
these perturbations. A finding that requires one of them becomes a separate
proposal rather than an unreviewed expansion of this plan.

## 1. Move immutable query preparation before worker launch

The phase callbacks in [CWorkerOrchestrator.swift](Sources/PWRunnerCore/CWorkerOrchestrator.swift)
and [ActorOrchestration.swift](Sources/PWRunnerCore/ActorOrchestration.swift)
currently call `planValidatorQueries` and `runValidator` while workers wait.
[CWorkerRequestPlanning.swift](Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
mixes request-only classification with live path eligibility;
`serializeProbes` in [ValidatorClient.swift](Sources/PWRunnerCore/ValidatorClient.swift)
builds dictionaries and JSON frames inside that held interval.

First try preparing one immutable NDJSON frame per static candidate after
admission and before worker launch. Leave the complete `planValidatorQueries`
call, including its static classification, at arrival; select prepared frames
from its decisions and retain the existing contiguous payload assembly. This
moves JSON encoding without splitting the eligibility planner. It does not
eliminate concatenation or justify redesigning the duplex pipe writer.
For actors, prepare before creating the equipment-inspection deadline and
scheduler, leaving their existing clock origins at their lifecycle boundaries.

Preserve these boundaries:

- Resolve paths afresh after the exact phase arrives. Earlier actions can
  unlink or recreate them. Keep the submitted path in the query frame; current
  resolution determines inclusion, not a replacement filter value.
- Keep known operation/filter exclusions ahead of path observation, and keep
  query ordering, optional fields, escaping and newline framing unchanged.
- A prepared frame or failure for an unreached phase supplies no query evidence.
  Surface a preparation failure only at the reached, eligible serialization
  boundary where it would have mattered. Ineligible queries remain ineligible.
- Launch a fresh validator against the same owned live generation after arrival.
  Retain ownership checks, collection closure and release publication in place.

Preserve the aggregate planning-and-collection accounting described by
`phase_collection_wait` and `actor_collection_allowance` in
[limits.json](../docs/limits.json). Current callbacks compute the validator I/O
timeout before serialization, then charge serialization in their exit debit.
Record preparation cost separately and add the selected frames' encoding cost
once to that exit debit when serialization would have been reached. Do not
subtract it before the existing planning guard or timeout calculation: that
would change launch and failure precedence. Budget/clock refusals that prevent
serialization incur no deferred encoding debit; a serialization failure charges
only the selected prefix through the first failing frame. If preparation timing
is unavailable or regresses, discard that cached result and serialize normally
at the reached boundary, under the existing callback accounting. Keep extra
speculative work visible in whole-host measurements. Do not silently grant a
larger aggregate allowance, charge unreached phases, double-charge preparation,
or move the actor lifetime-cutoff origin. Describe deferred charges accurately
in the owning limits account.
Use controlled clocks to establish exhaustion, clock failure, regression and
failure precedence. If preserving these semantics costs more than the work
saved, reject this candidate; changing the counting scope is a separate choice.

Account for earlier allocation and longer retention. Derive a cache bound from
admitted query counts and encoded frame bounds before implementation, keep one
prepared representation, and release it when no later phase needs it. Compare
query-dense workloads with no-eligible-query, early-failure and unreached-phase
controls. Increased memory residence and wasted preparation count against the
gain from shortening the workers' held interval.

## 2. Remove demonstrated host detection or cleanup delay

Instrument a disposable fixture to distinguish these intervals before choosing
a change: worker arrival publication to host observation; static preparation;
live planning; validator launch and duplex I/O; decoding; EOF to owned reap;
and collection closure to release. Use timestamps at both ends where possible;
host observations alone cannot locate an earlier worker publication precisely.

[CWorker.swift](Sources/PWRunnerCore/CWorker.swift) owns ordinary publication
polling, throttled child-death checks and `HostWaitClock`;
[ActorScheduler.swift](Sources/PWRunnerCore/ActorScheduler.swift) owns actor
arrival/completion polling and custody service. Validator `poll()` is
readiness-driven: its timeout cap is not a mandatory delay. Validator exit
grace follows decoding and precedes return from `runValidator`.

The prior review's 24 inspected validator-grace receipts all reported
`elapsed_ms: 0`. That limited sample deprioritizes cleanup tuning; integer
milliseconds do not prove the interval is free. Do not shorten every poll on
the assumption that a constant is a measured bottleneck. More frequent host
wakes can oppose coalescing even when worker response improves.

Choose at most one measured delay for a first candidate. A bounded host exit
notification may be worth investigating if EOF-to-reap delay is material.
Registration must cover a child that already exited; a notification prompts an
owned `waitpid` observation and never substitutes for reap. Preserve EINTR,
ownership-loss, failed-clock, timeout and final-cleanup paths. Charge any new
descriptor, registration, thread or wake activity to the candidate, and prevent
unintended worker inheritance. Do not defer cleanup past release as part of
this change: overlapping validator lifetime changes ownership and accounting.

For polling changes, preserve elapsed allowances, remaining-time bounds and
mandatory ownership checks around collection. Include slow/malformed/partial
validator output, delayed exit, timeout and cleanup failure. If profiling finds
no material avoidable delay, close this branch without changing production.

## 3. Reduce repeated work inside polling

`service_inbound_once` in [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c)
rescans inbound slots from zero on parked-activation and authority-exchange
polls, including already acknowledged slots. The
[authority layout](../controller/tools/pw_probe_runner/pw_authority_region.h)
defines one-shot slots. First measure repeated slot visits with test-only
instrumentation, then try a worker-local completed-prefix cursor. A fixed local
mask is a second candidate only if holes defeat the prefix's useful savings.

Remember completion from this worker's own validation and acknowledgement,
reset the state during authority preparation, and retain immutable association
checks. An uncommitted lower slot must remain eligible later without blocking
eligible higher slots. Preserve lowest-index selection among eligible slots
and at most one acknowledgement per pass. Skipping completed scanning never
skips host settlement, consumption validation, payload erasure or cleanup.

Keep hint-batch tuning separate, and sequence it as fixed under order of
work. All three loops currently end unsuccessful
polls with one thousand `cpu_relax` instruction hints. ARM `yield` here is not
an OS scheduler yield. Try at most one alternative batch per affected wait,
chosen from the baseline response/work measurements. Fewer scans or hints can
establish less repeated work; neither establishes descheduling, lower CPU
accounting, lower energy or better timer coalescing.

Preserve each loop's distinct decision order rather than factoring a common
wait algorithm:

| Wait | Decisions and service to preserve |
| --- | --- |
| Release | Clock, cutoff, proceed allowance and checked deadline extension; future-ordinal refusal; cancellation; exact release and acknowledgement. No inbound service. |
| Parked activation | Clock, cutoff and checked extension; cancellation; named/future activation; inbound service. No separate proceed allowance. |
| Authority exchange | Accept nonzero answer before the next clock sample; otherwise clock, cutoff, exchange allowance, cancellation and inbound service. |

Release and activation exclude their sampled wait once from the execution
deadline; exchange does not. A valid sampled decision may publish later.
Never insert a new delay between accepting a decision and acknowledging it.
Self-transfer depends on exchange-side inbound service. Existing held-phase
measurements do not isolate that loop: changing its tail requires an additional
generation-qualified live hold and response control.

## Measurement, selection and acceptance

Start with a bounded baseline pilot to locate held time and quantify observer
resolution. Commit the pilot's decomposition of held time into worker polling
and each host-side interval before any candidate work; the ARM plan selects
its minimum worthwhile improvement from that record. Then commit an acceptance
record associated with this plan, before candidate measurements. Identify
source/build hashes, workloads, exact trial counts and durations, uncertainty
calculation, cache bounds, the selected branch and its claimed benefit. Use five matched baseline/candidate pairs in
alternating order for each claimed performance workload. Keep contrary pairs;
do not extend sampling until a preferred result appears.

Use [held-footprint equipment and controls](../tests/CHANGE-VERIFICATION.md#footprint-observations):
an acknowledged hold, matching live process generations around observations,
and independent termination/reap. Do not start a short-lived process and then
try to discover its PID. Keep fixture timing effects separate from production
timing and show that instrumentation can detect an injected delay or extra
scan. Avoid permanent wire telemetry and token-content capture. Its current
reader also asserts that workers use more CPU than the matched sleeper. Keep
that baseline characterization separate from candidate acceptance; any new
reader must retain identity, sensitivity, interval and effect checks without
requiring the candidate to remain busy. The ARM plan compares with the same
reader. Record the reader's source identity in every acceptance record, and
treat a reader change after a frozen baseline as invalidating comparisons made
against that baseline until it is re-frozen with the new reader.

The acceptance record must separate these quantities:

| Claim | Required observation |
| --- | --- |
| Shorter held interval | Component and total hold duration, worker CPU during it, and complete query/attempt evidence. |
| Less work | Production-path encoding/scan/load counts with independent behavioral controls; whole-request host, worker and validator CPU. |
| Fewer resources retained | Created resources, lifetimes, bounded retained bytes and separate sampled resident/physical-footprint observations. |
| Better scheduling or coalescing | Attributable wake/context-switch or peer-progress measurements; not an inference from fewer loop iterations. |
| Lower energy | A suitable independent energy observation with observer cost and stated scope; otherwise leave energy unknown. |

For a latency/CPU claim, require improvement beyond declared uncertainty in
every matched pair of the named workload. A scan-only change may instead stand
on strictly reduced production-path work with unchanged behavior even if CPU
or sampled memory is unchanged. Frame preparation needs a measured reduction
in held time or held-worker demand; merely relocating work is insufficient.

For every changed wait role, additional worst-observed release, activation,
cancellation, cutoff and inbound-delivery response, as applicable, must be at
most 2 ms: compare candidate upper bounds with baseline lower bounds. This is
a finite-observation acceptance bound, not a real-time promise. Existing timing
allowances and correctness checks remain mandatory. Exceeding the derived
cache bound rejects the implementation; a corrected bound needs renewed review
and validation. A resolved increase beyond uncertainty in total CPU,
whole-request latency, sampled memory or peer interference requires a written
tradeoff decision before accepting that branch. Do not silently credit a local improvement as an
overall improvement. Other branches may proceed while that decision is open.

## Verification and execution

Use existing integrated controls and extend only the changed boundaries:

- Preparation/host changes: `runner_unit` planning, phase, ordering, clock,
  validator, actor and evidence controls; relevant `runner_validator_failure`,
  `runner_outcome_validator_no_reply`, `failure_boundaries` and framing checks;
  `witness_contract/phases` and `attempt_effects_wait_for_collection`. Add fresh
  path/unlink/recreate, unreached-phase and deferred-charge controls.
- Scan changes: extend `runner_c_worker_harness/authority_binding` with empty,
  single and maximum slot sets, accepted/rejected prefixes, an early hole,
  later eligible slots, late commit and repeated servicing. Assert actual
  acknowledgement, binding, settlement and consumption behavior. Include
  `witness_contract/extension_boundaries`, `actor_compositions`, and existing
  release/activation precedence controls.
- Every wait, release or eligibility change requires
  `witness_contract/order_barrier_mutations`. A mutation that fails to apply or
  build is not a detected ordering fault. Run applicable held-footprint and
  actor-timing qualification against a signed candidate, then the default
  battery and required source/ABI checks.

Inspect dispatcher selections with `tests/run.sh --all --list`; suite selectors
include opt-in cases. In particular, `runner_c_worker_harness/native_pause`
remains an intentionally failing applicability gate on the recorded equipment,
not a required passing result for a scan or host change. Do not weaken its
oracle. Follow [test evidence rules](../tests/AGENTS.md) for applicable reuse,
fresh output, snapshots and retention. Regenerate worker identity for changed
native inputs and update generated resource/limit accounts through their owners.

The coordinator owns integration, evidence and disposition. Read-only research
and review can run in parallel; builds and native trials run serially under the
checkout lock, with compiler concurrency capped at two. Start pilots with at
most two busy processes, including calibration children, and reduce load on
contention. Existing actor-footprint and timing qualification can exceed that
cap; inspect their full workload first and arrange an announced bounded quiet
window for those cases, or leave their acceptance pending. Do not silently
shrink a required case and claim its original coverage.
Capture power state and sleep per trial; do not compare across a transition.
Request and announce a quiet window before sensitive comparisons. Arrange any
actual sleep/wake test explicitly with the user. No generic logger is required:
direct publications, native observations and independent effects are primary;
unified logs are supplemental, and missing logs do not establish absence.

## Closeout

Accept, reject or explicitly block each branch with its evidence and claim
limits. Commit accepted implementation and current-behavior documentation;
preserve compact negative evidence in the outflow where it informs remaining
directions. Update FOOTPRINT only for established mechanism/resource changes,
and LIMITS for counting semantics. Remove completed plan-specific acceptance
records and retire this plan once all three branches are accepted or rejected,
preserving necessary raw evidence through the retention helpers. Do not delete
the shared outflow while the ARM plan or another unfinished direction uses it.
The ARM plan retires independently. Stop for a genuine correctness, attribution
or resource-ownership blocker and keep the plan active unless that scope is
explicitly closed by the user; ordinary negative results require no review
pause before moving to the next branch.
