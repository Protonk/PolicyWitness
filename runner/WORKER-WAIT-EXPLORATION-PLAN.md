# Worker wait exploration plan

Reduce the cost of keeping a witness available through shorter host-held
intervals and less repeated polling work. Accept candidates independently;
retaining accepted source is a valid outcome. This plan continues
[outflow direction 3](../records/FOOTPRINT-OUTFLOW.md#direction-3-pace-the-sandboxed-workers-waits)
and owns the common coordination, measurement and execution rules used by the
separate [ARM option plan](ARM-WAIT-OPTION-PLAN.md).

The [pilot](../records/WORKER-WAIT-PILOT.md),
[HOST-01](../records/WORKER-WAIT-HOST-01-ACCEPTANCE.md),
[HOST-02/03](../records/WORKER-WAIT-HOST-03-ACCEPTANCE.md) and
[SCAN](../records/WORKER-WAIT-SCAN-ACCEPTANCE.md) are complete; their accepted
changes are the starting source. PREPARATION was
rejected on cost grounds and is not reopened here. The
[acceptance review](../records/WORKER-WAIT-REVIEW.md) identifies retained evidence
and the version-10 response corrections; the outflow retains dispositions and
reopening conditions. These observations nominate work, not fresh baselines.

## Order of work

Complete the [host follow-on round](#host-follow-on-round) in order: HOST-04,
HOST-05, then conditional HOST-06. Dispose of each before opening the next
production candidate. Further host candidates require a separate scope decision.
ARM research/native trials and all hint-batch tuning are explicitly deferred
during this round. Deferral is a priority decision, not failed qualification or
evidence of no benefit; deferring ARM does not itself open hint tuning.

Freeze each comparison against identified accepted source, including preceding
accepted changes and excluding other candidates. Keep the two plans' builds,
output directories and acceptance records separate. Any accepted change affecting
a frozen comparison requires a new baseline and comparison on that source
foundation; do not combine observations across it. Dispose of the host round
before freezing ARM's production comparison baseline. Retain reusable measurement
preparation and controls, with their identities, even when a production candidate
is rejected.

### Resuming deferred work

Record explicit resumption and each disposition in the outflow. ARM and hint
changes compete for the release and parked-activation tails separately.
Successful native qualification reserves that tail for ARM deployment and benefit
evaluation; accepted adoption supersedes hint tuning there. Closing ARM without
adoption leaves hint tuning available. Pending qualification does neither.

After resumption, if ARM awaits an external observation or user availability,
the coordinator may explicitly defer that wait's ARM work and open hint tuning.
Record the reason and outstanding observation in the outflow and affected
acceptance records; elapsed time is not qualification failure. Resuming ARM after
an accepted hint change requires a new baseline and repeated affected comparisons.
This option does not override the current deferral or a correctness/ownership
blocker in accepted source or the apparatus.

## Boundaries

The [witness and process constraints](../AGENTS.md#core-ideas) remain in force.
Worker/validator pooling, delayed actor creation, external suspend/resume, early
path resolution, deferred validator cleanup and new sandbox-side IPC require
separate proposals. Preserve restrictive-profile publication without new
post-apply communication resources.

## Host follow-on round

The retained SCAN comparison includes HOST-01 through HOST-03. Its rapid/idle
medians nominate ordinary terminal detection (about 0.8–2.5 ms), decoding
(1.1–1.4 ms for 64 verdicts; 4.1–4.5 ms for 256), and first arrival often detected
after the initial host sleep. These are instrumented machine/build-flavour
observations, not universal costs; the review locates their version-10 outputs.

A nominated delay must exceed combined uncertainty in every repetition of its
named workload. Preserve elapsed allowances, remaining-time bounds, mandatory
ownership checks, EINTR, clock faults, timeout and cleanup. Notifications prompt
owned `waitpid` observations, never replace reap, and must handle already-exited
children. Account for resources and wake activity; prevent unintended descriptor
inheritance. Close a candidate without production changes if no material
avoidable cost is established.

**HOST-04 — ordinary final-completion detection.** Try the retained readiness
pipe's hangup only where no further collection remains. Keep bounded shared-memory
checks so terminal publication can end the wait before delayed exit; preserve
cancellation, allowance, ownership, final cleanup, actual observation order and
stop reason. Hangup is neither terminal publication nor reap. No new descriptor,
thread, registration or post-apply worker write is in scope.

Measure terminal publication to observation and to reap, whole-request latency
and host resource residence. Require reduced final detection beyond uncertainty
in every matched pair of the declared ordinary workloads. This interval follows
the held phase and establishes no held-worker CPU reduction. Controls include
already-exited children, publication before delayed exit, early hangup,
missing/unusable pipes, readiness failure with late write, EINTR, clock failure
and deadline cleanup. Actors and non-final ordinary phases are unchanged-path
controls.

**HOST-05 — decoder work at the collection boundary.** Profile
`decodeValidatorFrames` in [ValidatorClient.swift](Sources/PWRunnerCore/ValidatorClient.swift).
First compare inspection flavour with supported Swift `-O`. The
[timestamp host builder](../tests/fixtures/worker_wait/host_stamps.py) hardcodes
`-Onone -g`: make it honor and record flavour, account for observer cost and
isolate host flags from changes to other executables. Keep this diagnostic
separate from same-flavour implementation comparisons. Changing shipped inspection
policy requires a separate decision.

Select at most one small decoder candidate from that evidence, or reject further
source work. Keep decoding and its charge at the existing boundary; do not reopen
preparation caching or deferred accounting. Preserve framing, strict UTF-8,
integer/Boolean distinctions, size/count bounds, first-fault classification and
offset, step association, unknown fields, diagnostic outcomes, partial results and
raw lines. Pair identical compiler settings and name the adoption flavour.
Require shorter decoding and held intervals beyond uncertainty in every pair of
selected query-dense workloads, with small/no-eligible-query controls and
malformed/partial validator and framing checks. Whole-request cost and unchanged
witness coverage remain part of acceptance.

**HOST-06 — first arrival.** After the first two dispositions, measure readiness
observation, application publication and first arrival separately on accepted
source. Open at most one bounded initial-resampling candidate only if those
distributions support worthwhile savings; otherwise close. Do not shorten every
poll or add a worker notification channel. Freeze the window and clock-fault/
sample-cap behavior before comparison. Preserve failure-before-application,
failed application, ready-byte failure and allowances. Require shorter first-arrival
detection and held time in named workloads; count added host busy time against
waiting time saved. Include no-eligible-query and delayed-application controls.
Faster observation alone is not a total CPU benefit.

## Deferred polling work

SCAN's completed-prefix cursor is accepted. A fixed local mask remains unopened
unless measured holes defeat the prefix's useful savings; correctness coverage
of holes alone does not justify it. Any alternative must beat the cursor on
actual visits/loads in sparse and inbound-dense workloads, with ordinary execution
as a no-benefit control. Preserve worker-owned completion, preparation reset,
immutable associations, later eligibility of holes, lowest-index selection and
one acknowledgement per pass; never skip settlement, consumption checks, erasure
or cleanup.

After explicit resumption, try at most one alternative hint batch per affected
wait, selected from baseline response/work measurements. Current unsuccessful
tails use one thousand `cpu_relax` hints; ARM `yield` is not a scheduler yield.
Fewer hints/scans do not establish descheduling, CPU reduction, energy savings or
coalescing. Preserve each loop's decision order rather than sharing one algorithm:

| Wait | Decisions and service |
| --- | --- |
| Release | Clock, cutoff, proceed allowance, checked deadline extension; future-ordinal refusal; cancellation; exact release and acknowledgement. No inbound service. |
| Parked activation | Clock, cutoff, checked extension; cancellation; named/future activation; inbound service. No separate proceed allowance. |
| Authority exchange | Accept nonzero answer before the next clock sample; otherwise clock, cutoff, exchange allowance, cancellation and inbound service. |

Release/activation exclude sampled wait once from the execution deadline;
exchange does not. A valid sampled decision may publish later; add no delay
between acceptance and acknowledgement. Self-transfer needs exchange-side inbound
service. Changing that unopened tail requires its own generation-qualified live
hold and response control; held-phase measurements do not isolate it. Give each
remaining tail an explicit disposition before retiring this plan.

## Common measurement and acceptance

### Instruments and response resolution

Reuse the production-shaped timestamp fixture on the actual planning/validator
path without artificial collection holds. Bracket publication, observation,
release and acknowledgement in host and worker with continuous-clock stamps,
validated alignment and recorded bracket widths. Recover bounded stamps through
prepared storage after the interval: no post-apply I/O, public wire telemetry,
accelerated observation polling or discovery of a short-lived PID after execution.
Retain independent effects, generation/ownership and cleanup observations.

The [held-footprint fixture](../tests/suites/witness_contract/check_held_phase_footprint.py)
measures CPU during extended holds: accounting quantum at least 10 ms, minimum
hold the greater of 1 s and 100 quanta. These are fixture bounds, not production
hold durations or universal CPU-counter resolution. Its concurrent busy control
changes idle conditions. Label these observations separately; never splice their
rates into short production intervals. Host intervals and worker CPU overlap;
do not add them as disjoint elapsed time or conceal unobserved quantities.

Polling cadence and scheduler delay are response behavior, not instrument
uncertainty to subtract. For the 2 ms response gate, combined baseline/candidate
uncertainty must be at most 0.5 ms, including endpoint brackets, cross-process
alignment and calibrated capture overhead. Sum each side's largest uncertainty;
unknown uncertainty withholds credit. Use zero-delay and injected-delay controls
on both sides of the boundary, measuring actual injected intervals, and
uninstrumented neighbors for observer effects. Calibration establishes finite-run
sensitivity only. Improve insufficient equipment or leave dependent acceptance
unestablished; do not relax the bound.

The shared pilot owns the timestamp reader and its independent controls. Before
freezing the first comparison that could invalidate the held-footprint reader's
busy-worker assertion, its coordinator builds a mechanism-neutral CPU reader.
Hint tuning and ARM require it; scan work does if needed. Preserve independent
generation, sensitivity, interval and effect checks and historical busy-worker
meaning. CPU and timestamp readers remain distinct. Both comparison sides use
the same versions; reader changes require affected comparisons to be re-frozen,
with prior identities/results preserved. Avoid token-content capture.

### Conditions and the pilot window

Prepare builds, mechanics dry runs, checker controls and a finite schedule before
requesting a bounded quiet window for sensitive comparisons. Reserve time for
owned cleanup; start no trial whose watchdog and cleanup will not fit. Announce
start/end and never extend silently; missing coverage/resolution requires a
separately arranged window. Dry runs establish mechanics, not quantitative credit.

Record power source/mode, executable identities, warm/cold status, pacing,
competing load and sleep per trial. Keep blocks stable; never pool battery/AC or
pacing regimes. Battery is acceptable. Interrupted, sleep-overlapping or
power-transition blocks remain diagnostic and need replacement for credit.

Performance series exclude exactly one initial execution of each exact staged
executable, retain its cost and use fresh processes thereafter. Do not discard
additional slow trials as warm-up. A copied executable is not warmed by running
the build output: reuse the staged executable or label trials cold. Warm results
make no cold-start claim; this exclusion never applies to ARM first-use
qualification evidence.

Compare rapid launches after observed cleanup without an added gap and idle
launches requesting at least one second after cleanup. Freeze pacing and eligible
actual-gap ranges before measurement; use the same rule for paired members,
retain out-of-range trials diagnostically and replace only under that rule.
Keep claims scoped by regime and check the other for regression. Idle-gap effects
are conditions, not universal multipliers. No unreported busy helper may erase
them; label concurrent busy controls and finish calibration before an idle gap.

### Records and workloads

Commit `records/WORKER-WAIT-<candidate>-ACCEPTANCE.md` as each candidate opens,
before comparisons: HOST-04, HOST-05, conditional HOST-06, HINT-RELEASE,
HINT-ACTIVATION and conditional HINT-EXCHANGE. Use a separate record for a mask
candidate if justified. Freeze source/build/reader identities, workloads,
durations/counts, uncertainty, bounded state and claimed benefit. Preserve frozen
definitions and superseded observations in explicit revisions. Use five matched
pairs in alternating order per claimed performance workload; retain contrary
pairs and never extend sampling to obtain a preferred result.

Inventory existing footprint, phase, actor and authority controls before adding
needed workloads/checkers. Register new runnable cases and update coverage;
variants need no entry per specimen. Retain exact inputs, reached phases and
independent effects, following fixture ownership rules. The shared pilot informs
ARM's minimum worthwhile benefit; ARM rechecks that rationale at its own freeze.

### Acceptance

| Claim | Required observations, kept separate |
| --- | --- |
| Shorter hold | Component/total hold, worker CPU during it, complete query/attempt evidence. |
| Less work | Production-path counts and independent behavioral controls; whole-request host/worker/validator CPU. |
| Fewer retained resources | Resources created, lifetimes, bounded bytes; separate sampled resident/physical footprint. |
| Scheduling/coalescing | Attributable wake/context-switch or peer-progress observations. |
| Lower energy | Independent suitable energy observations, observer cost and scope; otherwise unknown. |

Latency/CPU improvements must exceed uncertainty in every named matched pair.
A scan-only candidate may stand on strictly reduced production-path work with
unchanged behavior: demonstrate actual slot visits/atomic loads, added state and
bookkeeping, and its saving over the accepted cursor. Source counts or load/hint
ratios do not establish CPU/energy gains. Leave unmeasured quantities unknown.

For each changed wait role, additional worst-observed release, activation,
cancellation, cutoff and inbound-delivery response, as applicable, must be at
most 2 ms: `max(candidate value + uncertainty) - min(baseline value - uncertainty)`.
Require every applicable response on every accepted trial and the declared
matched-pair count; missing endpoints cannot remove obligations. Inbound response
starts at the bracketed commit store. This is a finite-observation bound, not a
real-time promise; existing allowances and correctness remain mandatory.
Exceeding a derived storage bound rejects the candidate; changing the bound needs
renewed review/validation. A resolved increase beyond uncertainty in total CPU,
whole-request latency, sampled memory or peer interference requires a written
tradeoff decision before acceptance. Local improvement is not overall improvement;
other independent branches may proceed while that decision is open.

## Verification and execution

Extend controls at changed boundaries: host changes use `runner_unit` planning,
phase, ordering, clock, validator, actor and evidence controls; relevant validator
failure/no-reply, `failure_boundaries`, framing, `witness_contract/phases` and
`attempt_effects_wait_for_collection`. Include slow/malformed/partial validator
output, delayed exit, timeout and cleanup failure. Polling/scan changes retain
release/activation precedence and authority-binding controls (empty/single/max
slots, accepted/rejected prefixes, holes, late commits and repeated service),
actual acknowledgement/binding/settlement/consumption checks, extension boundaries
and actor compositions.

Every wait, release or eligibility change requires
`witness_contract/order_barrier_mutations`; failure to apply/build a mutation is
not detection. Run applicable held-footprint and actor-timing qualification
against the signed candidate, then the default battery and required source/ABI
checks. Inspect `tests/run.sh --all --list` for opt-ins. `native_pause` remains
an intentionally failing applicability gate on this equipment, not a passing
prerequisite for host/scan changes; preserve its oracle. Follow
[test evidence guidance](../tests/AGENTS.md), regenerate worker identity as required
and update generated resource/limit accounts through their owners.

The coordinator owns integration, evidence and disposition. Builds/native trials
run serially under the checkout lock, compiler concurrency at most two; read-only
research/review may run in parallel. Start pilots with at most two busy processes,
including calibration children, and reduce load on contention. Larger actor
qualification needs an inspected workload and separately announced bounded quiet
window, or acceptance remains pending; never shrink coverage silently. Arrange
actual sleep/wake with the user. Direct publications/native observations/effects
are primary; no generic logger is required. Logs are supplemental and silence
establishes no absence.

Exploration runs may remain unpinned; leave existing pins and defer pruning/pin
maximum decisions until acceptance. Keep raw evidence in dispatcher-owned output,
with identities/locations in records. Missing required raw evidence requires
rebuilding/repeating affected observations and revising changed baselines; summaries
cannot replace it. At acceptance choose necessary runs or identified copies,
decide any exception to the normal pin maximum, then prune through existing
helpers. No pin rotation is prescribed.

## Closeout

Accept, reject or explicitly block remaining candidates with evidence and claim
limits. Commit accepted source/current-behavior documentation; keep useful negative
evidence in the outflow. Update FOOTPRINT only for established mechanism/resource
changes and LIMITS for counting semantics. Retire this plan and completed
plan-specific records after the host round and deferred hint tails have explicit
dispositions, including supersession by accepted ARM adoption; deferral is not
closure. Preserve needed raw evidence through retention helpers.

ARM retires independently. Keep the shared pilot while either plan needs it;
after both retire, carry lasting conclusions/evidence references into the outflow
or behavior documentation and delete the pilot, without a new records archive.
Keep the outflow while an associated direction needs it. Before deleting either
plan, remove reciprocal links and preserve common rules still needed by the other.
Stop for genuine correctness, attribution or resource-ownership blockers and keep
the plan active unless the user closes that scope; ordinary negative results
need no review pause before the next candidate.
