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

This plan's ready builds and native trials take priority over the ARM plan's;
this is scheduling priority, not a requirement to finish this plan before ARM
trials begin. Open with the baseline pilot described under measurement, then
dispose of branch 2 while its fixture and decomposition are current, then
branch 1, then branch 3. Accepting or rejecting a branch remains independent of
the others; the order fixes sequence, not outcome.

Within branch 3, the scan cursor may proceed as soon as branch 1 is disposed.
Hint-batch tuning for the release and parked-activation tails waits for the
ARM plan's result for that wait. Successful native qualification reserves the
tail for ARM deployment and benefit evaluation; it does not establish adoption.
An accepted ARM change supersedes hint tuning at that tail. ARM closure without
adoption, including failed qualification or insufficient benefit, leaves hint
tuning as the remaining tail candidate. Pending observations are not failures;
the deferral rule below permits hint tuning to proceed earlier when recorded
by the coordinator.

Read-only ARM contract research, checker design and pinned-source review can
run in parallel. Its disposable-child applicability trials use native trial
time this plan is not using; their builds and executions remain serialized
with this plan's. They never share a build, output directory or acceptance
record with this plan's candidates. Dispose of branches 1 and 2 before the ARM
plan freezes its production comparison baseline, subject to the blocked-branch
exclusion below. Include every accepted host-side and preparation change and
record each disposition or exclusion in the outflow.

Freeze comparisons against identified accepted source, excluding other candidate
changes. Any later accepted scan, hint or host change that affects a frozen
comparison requires a new baseline and candidate comparison on the same source
foundation; do not combine results from before and after that change.

### Deferred work and baseline exclusions

- When ARM qualification is pending on an external observation or user
  availability, the coordinator may explicitly defer that wait's ARM work and
  open hint tuning. Record the deferral, its reason and the outstanding
  observation in the outflow and affected acceptance records. Preserve ARM's
  pending status; elapsed time is not qualification failure. If ARM resumes
  after an accepted hint change, freeze a new baseline incorporating that
  change and repeat the affected comparisons.
- When branch 1 is blocked solely on a tradeoff decision, the coordinator may
  freeze ARM's baseline on accepted production source with that candidate
  excluded. Record the exclusion in the outflow and ARM acceptance record,
  leaving branch 1 blocked. If it later lands, freeze a new baseline and repeat
  the affected comparisons. This exception does not bypass branch 2's
  disposition or a correctness or ownership blocker in accepted source or the
  measurement apparatus, and does not close branch 1 for plan retirement.

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
If the pilot's query-dense cell shows the whole serialization interval below
the combined timing uncertainty the comparison can achieve, reject this
candidate on that evidence without building it: no comparison could resolve
the reduction it promises. Record the measured interval and the uncertainty as
the rejection's limit, so a later instrument with better resolution can reopen
it deliberately.

## 2. Remove demonstrated host detection or cleanup delay

Build the pilot's production-shaped timestamp fixture before choosing a change.
Distinguish worker arrival publication to host observation; static preparation;
live planning; validator launch and duplex I/O; decoding; EOF to owned reap;
and collection closure to release. Timestamp host and worker boundaries under
the measurement rules below; host observations alone cannot locate an earlier
worker publication precisely. Reuse this fixture for branch 2.

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

The pilot may nominate at most two material delays, each as a separate host
candidate. A delay is material when its measured host-side component exceeds
the pilot's combined timing uncertainty in every repetition of a named cell;
report sub-threshold components as observed but not nominated. Evaluate
`HOST-01`, then `HOST-02` if nominated, before branch 1 while the fixture is
current. Each gets its own acceptance record and baseline on accepted source;
a second candidate includes the first only if accepted.
Further delays go to the outflow for later work, not an open-ended tuning loop.
A bounded host exit notification may be worth investigating if EOF-to-reap
delay is material.
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
This opportunity applies to actor workers with inbound slots: no authority
region means an immediate return, and the admitted slot count is bounded.
Include sparse and inbound-dense actor workloads with repeated completed scans;
ordinary execution is a no-benefit control, not evidence for this branch.

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

### Instruments and response resolution

The pilot needs two instruments with separate claims:

- The production-shaped fixture from branch 2 measures the ordinary and actor
  timelines using the actual planning/validator path, without an artificial
  collection hold. Bracket publication, observation, release and acknowledgement
  in host and worker with validated continuous-clock timestamps; verify clock
  alignment and record bracket widths. Recover the bounded test-only stamps
  through prepared storage after the interval. Do not add post-apply I/O or
  public wire telemetry, accelerate host polling for observation, or depend on
  discovering a short-lived PID after execution. Retain independent effects,
  live-generation/ownership facts and cleanup.
- The existing [held-footprint fixture](../tests/suites/witness_contract/check_held_phase_footprint.py)
  measures worker CPU rate during deliberately extended holds. Its declared
  accounting quantum is at least 10 ms and its minimum hold is the greater of
  1 s and 100 quanta. These are fixture bounds, not production hold durations or a universal
  CPU-counter resolution. Its busy control also changes the workload's idle
  conditions. Label those CPU observations separately; do not splice their
  rates into short production intervals as if directly measured there.

The ordinary host's 2 ms poll and actor host's 1 ms poll are behavior to measure,
not the timestamp instrument's resolution. CPU-accounting increments cannot
establish sub-millisecond response. Before crediting the 2 ms response bound,
require combined timing uncertainty for each baseline/candidate comparison of
at most 0.5 ms, including endpoint brackets, cross-process clock alignment and
calibrated capture overhead. Use zero-delay and injected-delay controls on both
sides of the acceptance boundary; measure the actual injected interval rather
than assuming a requested sleep lasted exactly that long. Check uninstrumented
neighbors for observer effects. Scheduler delay in the workload is response,
not noise to subtract. Calibration establishes finite-run sensitivity, not a
universal bound. If resolution is insufficient, improve the instrument or leave
that response claim and dependent acceptance unestablished; do not relax 2 ms.

### Conditions and the pilot window

Treat the quantitative pilot as sensitive. Prepare builds, fixture dry runs,
checker controls and a finite trial schedule before requesting an initial
five-minute quiet window. Allow up to four minutes for calibration, excluded
warm executions and measurements, reserving the final minute for owned cleanup.
Do not start a trial unless its watchdog and cleanup fit the remaining time.
Announce start/end; do not extend automatically. Missing coverage or inadequate
resolution is an incomplete pilot requiring a separately arranged window.
Opportunistic dry runs establish mechanics, not the quantitative decomposition.
Held workers are busy processes: the pilot's actor cells use two actors, one
active and one parked with inbound delivery, so the held workers are the only
busy processes under the cap below. Three- and eight-actor compositions are
characterized only in a separately announced qualification window with their
load stated.

Name power source, power mode, executable identities, warm/cold status, pacing
and competing load in each pilot cell and acceptance record. Keep conditions
stable within a block; never pool battery/AC or different pacing regimes.
Battery operation is acceptable. Retain power and sleep observations; interrupted
or power-transition blocks remain diagnostic and need replacement for credit.

For performance series, retain one excluded initial execution of each exact
staged baseline/candidate executable before counted trials, using fresh processes for
every run. Do not discard additional slow trials as warm-up. Warming a build
output does not warm a newly copied fixture executable: stage and reuse the
same executable through fresh processes, or label those trials as cold. Keep
first-execution cost separately visible; warm measurements make no cold-start
claim. This exclusion does not apply to ARM's first-use qualification evidence.

Pilot both separated launches, with a requested idle gap of at least one second
after observed cleanup, and rapid launches after cleanup with no added gap.
Record actual gaps and use the same rule for both members of each pair. Freeze
the exact pacing and eligible gap range before candidate measurements; retain
out-of-range trials diagnostically and replace them only under that declared
rule. Treat the historically observed idle-gap effect as a condition to examine,
not a universal timing multiplier. No busy helper may silently keep a core
active to remove it. Label the held-CPU fixture's concurrent busy control as
such; calibration outside a response interval must finish before its idle gap.
Keep benefit claims scoped by regime and check the other regime for regression.

### Records, workloads and readers

Commit the pilot as `records/WORKER-WAIT-PILOT.md` before candidate optimization
work. Report host-side intervals within the held timeline and worker polling
CPU separately: they overlap and must not be added as disjoint elapsed time.
Keep unobserved intervals explicit. Both plans own this shared record; the ARM
plan uses it to select and justify its minimum worthwhile improvement, then
checks that rationale against its later frozen production baseline.

Use a separate acceptance record for each independently evaluated candidate,
committed as that candidate opens and before its comparison measurements:
`records/WORKER-WAIT-<candidate>-ACCEPTANCE.md`. Use candidate names `HOST-01`,
`HOST-02` if nominated, `PREPARATION`, `SCAN`, `HINT-RELEASE`,
`HINT-ACTIVATION`, and, if reached,
`HINT-EXCHANGE`. This lets hint workloads be fixed after the relevant ARM result
without rewriting another branch's frozen protocol. Record the current source,
reader and build identities, workloads, trial counts/durations, uncertainty,
cache bounds where applicable, and the benefit claimed. Preserve frozen
definitions and superseded observations when recording a revision; do not
silently replace them. Use five matched baseline/candidate pairs in
alternating order for each claimed performance workload. Keep contrary pairs;
do not extend sampling until a preferred result appears.

New specimens, timestamp fixtures and checker controls needed to cover the
declared workloads are in scope. Inventory existing coverage before authoring
them: `tests/lib/footprint_workloads.py`, phase controls, actor compositions and
authority-binding controls are starting points, not proof that query-dense,
no-eligible-query, early-failure, unreached-phase and inbound-dense workloads
already exist. Register new runnable cases and update their coverage accounts;
variants within an existing registered case need no separate catalog entry per
specimen. Retain exact inputs, observed phase reachability and independent
effects. Follow fixture ownership rules rather than regenerating default
fixtures during ordinary test execution.

The pilot owns the timestamp reader and its independent controls. Existing
held-footprint readers may serve busy baseline characterization in the pilot
and branches 1/2. Build the shared mechanism-neutral CPU measurement reader
when the first candidate could invalidate their busy-worker assertion, before
freezing that comparison's baseline; the coordinator executing that candidate
owns this work. Hint tuning and ARM must use it, and scan work must do so if
needed. Preserve generation, sensitivity, interval and effect checks and the
meaning of historical busy-worker evidence. Keep the CPU reader distinct from
the timestamp reader; each acceptance record identifies all readers it uses.
Both sides of a comparison use the same versions. A reader change invalidates
affected frozen comparisons until re-frozen with that reader; do not rewrite
earlier records to pretend they used it. Avoid token-content capture.

### Acceptance

Each acceptance record must separate these quantities:

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
or sampled memory is unchanged. For the small cursor, demonstrate fewer actual
slot visits/atomic loads in the declared inbound workloads with behavioral
controls; an unused cache or a source-code count alone is insufficient. Report
its state and added bookkeeping, and do not infer a CPU/energy benefit from
the ratio of loads to instruction hints. Additional scan-state complexity needs
its own demonstrated saving over the simpler cursor. Frame preparation needs a
measured reduction in held time or held-worker demand; merely relocating work
is insufficient.

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

The coordinator is whoever is running the plan and owns integration, evidence
and disposition. Read-only research and review can run in parallel; builds and
native trials run serially under the
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

Exploration runs may remain unpinned. Leave existing pins in place and defer
pruning and decisions about the normal pin maximum until acceptance. Keep raw
evidence in dispatcher-owned output, with identities and locations in the
records; do not move runs under `records/` to avoid retention rules. If required
raw evidence disappears, rebuild and repeat the affected observations, revising
the baseline if conditions changed. A surviving summary cannot replace it.
At acceptance, choose which runs or identified copies remain necessary, decide
whether an ongoing dependency warrants exceeding the normal maximum, and only
then prune through the existing helpers. No pin rotation is prescribed now.

## Closeout

Accept, reject or explicitly block each branch with its evidence and claim
limits. Commit accepted implementation and current-behavior documentation;
preserve compact negative evidence in the outflow where it informs remaining
directions. Update FOOTPRINT only for established mechanism/resource changes,
and LIMITS for counting semantics. Remove completed plan-specific acceptance
records and retire this plan once all three branches are accepted or rejected,
including hint tails superseded by accepted ARM changes. Preserve necessary raw
evidence through the retention helpers. Keep the shared pilot record while
either plan needs it; once both plans retire, delete the pilot record after
carrying forward any lasting conclusions and evidence references into the
outflow or current-behavior documentation as appropriate. Do not create a
separate records archive for it. Keep the outflow while an associated direction
needs it; raw-evidence retention is decided separately at acceptance.
Before deleting either plan, remove its reciprocal links from the remaining
plan and retain any coordination facts that still apply there.
The ARM plan retires independently. Stop for a genuine correctness, attribution
or resource-ownership blocker and keep the plan active unless that scope is
explicitly closed by the user; ordinary negative results require no review
pause before moving to the next branch.
