# Worker wait pilot

Shared quantitative pilot for the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md)
and the [ARM wait option plan](../runner/ARM-WAIT-OPTION-PLAN.md). It decomposes
the interval during which a sandboxed worker waits for the host, on the
production planning and validator path, and records the response and polling
behavior that later candidates are compared against. Protocol sections are
frozen before the first quiet window; result sections are filled from the
window's evidence and name the run that holds it. Raw evidence under
`tests/out/` is gitignored and available only in the local checkout.

## Status

| Item | State |
| --- | --- |
| Protocol | frozen in the commit that adds this record; later changes are recorded as revisions below |
| Apparatus dry run | complete, mechanics only: run `20261107T202616Z_eba9d80a` (`tests/out/runs/worker-wait-pilot-dryrun-06`), 48 trials accepted, host sleep events complete, cleanup settled; independent referee review applied in two passes |
| Calibration | pending the window; dry-run calibrations credited the gate at 1.0 to 5.2 µs busy combined uncertainty under ordinary load |
| Quiet window 1 | requested |
| Decomposition | pending |

## Questions the pilot answers

1. Of the interval from a worker's arrival publication to its acknowledgement
   of release, how much is host detection, planning, frame serialization,
   validator launch, duplex I/O, decoding, EOF to reap, and release to
   acknowledgement, per cell and pacing regime?
2. How late does each host observe the worker's publications, and through
   which wait? In the ordinary form the host observes readiness, application
   and the first arrival on the same pass after its readiness wait, which
   polls at 10 ms; the sentinel loop, polling at 2 ms, samples a later phase's
   arrival only from the pass after the previous release, and detects the
   worker's terminal publication; the actor host detects arrival, recipient
   acknowledgement and completion by 1 ms polls. An observation with no
   earlier negative sample is reported as first-check-positive and placed in
   the host sleep that contained the publication, when one did. How long do
   the requested sleeps last?
3. How often does the validator exit grace sleep at all, and for how long?
4. How many worker poll passes occur in each release, parked-activation and
   exchange wait, and what is each wait's mean pass period? For release and
   activation waits the period is the interval from the wait's first pass
   sample to its accepting pass sample divided by the passes between them;
   for exchange waits, which record no first-pass sample, it is an upper
   bound from the preceding stamp to the answer divided by the passes.
5. How many inbound slot visits and acquire loads does the parked scan perform
   in the two-actor cell?
6. Can the instrument resolve a 0.5 ms combined uncertainty for the
   publication-to-observation and release-to-acknowledgement comparisons?

The pilot does not accept or reject any candidate. Branch 2 nominates at most
two material delays from it; branch 1 applies its pre-build rejection rule to
the serialization interval of the query-dense cells; the ARM plan selects its
minimum worthwhile improvement from it.

## Instruments

### Production-shaped timestamp fixture

- **Worker side.** A seam-built copy of the production worker
  (`tests/fixtures/worker_wait/stamp_worker.c`) that includes
  `pw_probe_runner.c` unchanged and defines its compiled-away observation seams
  to store `mach_continuous_time` stamps into a page of the evidence region's
  capture bytes prepared before application. It acquires no resource after
  application, refuses to stamp when a profile capture is requested, and
  reports the production worker identity although it is not the production
  worker; records name its own executable hash as a substitution.
- **Host side.** A disposable copy of the XPC host built from the Meson source
  list with stamps at the boundaries listed in the apparatus contract,
  including a stamp immediately before and after each release and activation
  store, a burst of sixteen consecutive stamps at request start that measures
  the host's own stamp cost in situ, the worker stamp page copied out before
  each session's unmapping, and the stamps exported to a fixture-owned
  directory after children are reaped, immediately before the reply is sent,
  followed by a small marker that records the export's own duration. The
  export adds no wire or evidence field; its cost lies inside the instrumented
  host's request latency. One pre-spawn marker write lets the fixture watch
  the live host's exit with a generation check.
- **Observer overlap.** The fixture registers that exit watch as soon as the
  marker appears: it watches the stamp directory for writes and also polls
  every millisecond for the first 20 ms after launch, then every 10 ms. The
  marker appears some tens of milliseconds after launch, once the XPC service
  is up, and the first held interval begins several milliseconds after that,
  so registration normally completes while the worker is still compiling its
  policy. A trial whose registration span overlapped any held interval is
  retained as diagnostic, excluded from aggregation under the declared
  exclusion `observer_overlap`, and never replaced by result. After
  registration the fixture keeps waking every 10 ms to check for the CLI's
  exit, with two clock reads per wake; those wakes continue through the trial,
  are recorded per trial, and are not grounds for exclusion. The neighbor,
  which writes no marker, is polled for one on every wake throughout its run;
  the instrumented app is not once its marker has been read.
- **Neighbor.** The same host and worker recipes with zero patches, staged
  identically, run on the same cells in both regimes. It bounds observer
  effects only through whole-request latency and the envelope's existing
  integer-millisecond host fields (readiness wait, sentinel wait, visit
  timing), whose noise is of the order of milliseconds. It cannot resolve a
  sub-millisecond instrument effect inside a held interval, and it cannot
  separate the export's cost; the exported marker records that cost directly.
- **Clock.** Both sides stamp `mach_continuous_time`; the host's own waits keep
  using `CLOCK_MONOTONIC`. Alignment is checked on every trial at tick
  resolution, under the rule stated with the resolution gate below.
- **Host sleeps.** Every host sleep updates per-key registers (count, last
  pre and post stamps, requested and actual sums and extremes), and the first
  64 sleeps of each key are also appended as stamped begin and end events, so
  a publication can be placed in the exact sleep that contained it.
- **Calibration pair.** `tests/fixtures/worker_wait/clock_pair.c` runs a writer
  and a reader on a shared page outside PolicyWitness: read overhead,
  publication-to-observation latency for a busy poller and for 1 ms and 2 ms
  sleeping pollers, and injected delays of 0, 1, 2 and 3 ms with the actual
  injected interval measured. It establishes the instrument's finite-run
  sensitivity on this machine, not any PolicyWitness behavior.

### Held-footprint fixture

`witness_contract/held_phase_footprint` measures worker CPU rate during
deliberately extended holds through a gated bridge validator. Its rates are
labeled separately and never spliced into the production-shaped intervals.
It is not run in the pilot window; its historical observations remain where
`docs/FOOTPRINT.md` cites them.

## Cells

| Cell | Form | Content |
| --- | --- | --- |
| O1 | ordinary | one phase, one eligible `file-read-data` path query on an existing file, one read attempt |
| O64 | ordinary | one phase, 64 eligible queries on 64 existing short-path files |
| O256 | ordinary | one phase, 256 eligible queries on 256 existing short-path files |
| O0 | ordinary | the O64 layout with zero eligible queries |
| O2P | ordinary | two phases of 8 eligible queries each |
| A2 | actor | the two-actor lifecycle specimen: unapplied issuer, applied subject, two deliveries, parked activation, exchange and inbound service |

Held workers are busy processes. The two-actor cell keeps the held workers
within the two-busy-process cap; larger compositions are not pilot cells.

## Conditions and pacing

- Power source and charge from `pmset -g batt`, low power mode from `pmset -g`,
  load average, and continuous-versus-uptime clock difference are recorded per
  trial. A trial overlapping system sleep or a power transition is retained as
  diagnostic and replaced.
- Regimes: `rapid` launches the next trial immediately after observed cleanup;
  `idle` launches at least 1.0 s after observed cleanup. Requested and actual
  gaps are recorded. Observed cleanup is the CLI exit plus the generation-checked
  host exit event for the instrumented app, or the CLI exit plus a 100 ms margin,
  labeled, where the host watch was unavailable. Eligible actual gaps are 0 to
  100 ms for `rapid` and 1.00 to 1.25 s for `idle`; a trial outside its range is
  retained as diagnostic and does not count. Each trial has a 15 s watchdog.
- Six repetitions per app, cell and regime are scheduled; a group is complete
  when at least five of them are accepted. Fewer accepted trials in any group
  is an incomplete pilot for that group, reported as such.
- Grouping keys are app, cell, regime, power source, low power mode and host
  build flavour; nothing crosses a key.
- Each staged app receives one excluded warm execution with an eligible query
  before counted trials; staged executables are reused through fresh processes.
- Regimes, cells, instrumented and neighbor results are never pooled.

## Trial schedule for quiet window 1

Five minutes. Builds, staging, warm executions, dry runs and checker controls
are complete before the window opens. Order:

1. Calibration pair: the full matrix of busy, sleep1 and sleep2 readers by
   injected delays of 0, 1, 2 and 3 ms, 100 trials per cell, 100,000 read-cost
   samples, injection by `nanosleep`; at most 60 s including process starts.
2. Both apps, both regimes, six repetitions: one `rapid` block holding every
   repetition over the six cells, then one `idle` block, with the instrumented
   and neighbor apps alternating per cell and their order alternating per
   repetition, so neither app always follows the other.
3. Owned cleanup in the final minute: target files, exit observations, stamp
   directory inventory, and an inventory of any process whose executable lies
   under either staged bundle.

A trial starts only if its watchdog and cleanup fit the remaining time; skipped
trials are recorded as not run. The window is announced at start and end and
is not extended.

## Resolution gate

Every publication is stamped after its store, so its bracket is the interval
from the nearest preceding stamp in the same process to the post-store stamp:
for a worker arrival the same visit's activation store, the applied stamp for
the first ordinary phase, or the previous phase's last stamp; for a host
release or activation the pre-store stamp. Each endpoint term is at least the
calibration pair's measured endpoint term and, for host endpoints, at least
twice the host's in-situ stamp cost. That in-situ cost is measured by
back-to-back records and so understates a store-plus-stamp sequence; the
pre-store stamps and the calibration floor are what bound host publications,
and a window whose calibration endpoint term fell below about 200 ns would
need that caveat applied. Combined timing uncertainty for a cross-process interval
is the sum of its two endpoint terms and the calibration pair's causal bound
on the clock offset between two processes. A value at or below its
uncertainty is reported as below the instrument floor, not as a resolved
duration. A detection bracket set by polling (the host's 10 ms, 2 ms or 1 ms
period, the worker's pass period) is response behavior, reported beside each
latency with its own count and not counted as instrument uncertainty. The
2 ms response bound is credited only where the combined uncertainty is at
most 0.5 ms and the calibration pair's instrument gate is credited. The gate
is judged on the worst observed calibration trial; a preempted trial that
withholds it makes this an incomplete pilot, not a relaxed gate. Where the
gate or the uncertainty is not met, the response claim stays unestablished
and the instrument is improved before any dependent acceptance.

Components are chained or nested, never disjoint: the held total is the chain
from arrival publication to acknowledgement, the validator sub-intervals are
nested inside collection, and EOF to reap overlaps decoding. They are not
summed across rows.

Stamps across processes are ordered at tick resolution: a hop between two
processes can complete within one 41.67 ns tick on this machine, so equal
ticks are accepted and counted, and only an observation stamp strictly earlier
than the publication it observed, beyond a declared 50 µs tolerance, refuses a
trial. Pass-sample stamps taken before a load may legitimately precede the
other side's publication stamp.

## Readers

- Timestamp reader: `tests/suites/witness_contract/worker_wait_pilot_reader.py`,
  with constructed accept-and-reject controls in
  `witness_contract/worker_wait_pilot_controls` (default battery).
- Calibration reader: `tests/suites/witness_contract/worker_wait_clock_pair.py`.
- Reader and fixture identities (sha256) are recorded in the results section;
  both sides of any later comparison must use the same versions.

## Dry-run observations to examine, not evidence

Mechanics dry runs under ordinary machine load, before any quiet window:

- A requested 2 ms `nanosleep` in the calibration pair's sleeping reader
  lasted about 2.25 ms, and a requested 1 ms `mach_wait_until` about 1.13 to
  1.15 ms. The host's poll sleeps are therefore a condition to measure, not a
  constant to assume.
- Clock reads cost about 4.7 to 4.9 ns and the tick is 41.67 ns, so about nine
  in ten consecutive reads return the same tick; the tick, not the read, bounds
  a stamp.
- A seam-built worker driven directly with no host made about 178,000 release
  wait passes in a 54 ms hold, about 0.3 µs per pass.
- In the full-cell dry run through the real CLI, the ordinary host observed
  the worker's first arrival about 6 to 8 ms after the worker published it,
  with no negative arrival sample before the positive one: the worker applied
  and arrived while the host was inside its readiness wait, whose single
  requested 10 ms sleep lasted about 12.5 ms. Requested 2 ms sleeps lasted
  about 2.5 ms and requested 1 ms sleeps about 1.25 ms. The actor host's
  nested recipient-acknowledgement wait showed the same 1.25 ms after the
  parked recipient had acknowledged within a microsecond. These are the
  shapes the window must measure under declared conditions; the dry run
  credits nothing.

## Evidence location and retention

Raw evidence stays in the dispatcher-owned run named in the results, under
`tests/out/runs/`, including the staged apps, every trial's receipts, the
calibration cells and the reader output. The run is gitignored and available
only in the local checkout; it remains unpinned while exploration continues,
and the decision to pin or copy identified evidence is taken at acceptance,
as the plan directs.

## Results

Pending the first quiet window.

### Executable and source identities

Pending.

### Calibration

Pending.

### Decomposition

Pending.

### Nominations and limits

Pending.
