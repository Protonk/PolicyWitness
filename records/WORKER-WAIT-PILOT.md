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
| Calibration | established in the window: busy combined uncertainty 1.29 µs, instrument gate credited |
| Quiet window 1 | complete: 2026-11-07 20:39:33Z to 20:41:39Z, run `20261107T203933Z_74f4feba` |
| Decomposition | complete: 144 trials accepted, none excluded or skipped, every group at six |

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

Run `20261107T203933Z_74f4feba` in `tests/out/runs/worker-wait-pilot-01`
(gitignored, local checkout only). Announced quiet window, battery power at 97
to 96 percent throughout, low power mode off, no system sleep in any trial, no
other load started or stopped. 144 trials accepted: six per app, cell and
regime; none excluded, skipped, refused or failed; no observer overlap; no
clock-order inversion in any trial. Actual gaps: `rapid` 0.5 to 18.1 ms
(median 5.2 ms), `idle` 1005.2 to 1005.5 ms. Window used 96.5 s of 240 s.
Final cleanup found no surviving staged process.

### Executable and source identities

Source `28137609` (production sources unchanged since the seam commit
`ce6e35d2`, worker identity `160149e8…c2cf`). Baseline app: the distribution
build of that source. Fixture builds, not production bytes: instrumented host
`cd4c19ac…`, stamp worker `232a1d00…`; neighbor host `2a6be0a6…`, plain worker
`aec2fc57…`; clock pair `beef03b5…`; recorder source `6e9885e4…`; reader
`2724f3b4…` (version 3). Hosts are `-Onone -g` rebuilds of the Meson source
list, the same optimization as the distribution host. Full hashes, inodes and
receipts are in the run's `staging/`, `host-*/`, `worker-build/` and
`summary.json`.

### Calibration

Tick 41.67 ns; read cost 15.5 ns, so a stamp costs one tick. Busy reader:
combined uncertainty 1.29 µs (endpoint term 624 ns, alignment bound 83 ns);
gate credited. Sleeping readers: 1.17 ms (1 ms pacing) and 5.9 ms (2 ms
pacing), which is polling response and does not meet the gate, as expected.
Every interval below carries a combined uncertainty of 1.2 to 1.3 µs unless
stated; values at or below it are reported as below the instrument floor.

### Decomposition: ordinary form

Medians of six trials, microseconds unless marked ms; `rapid` / `idle`.

| Component | O1 | O64 | O256 | O0 | O2P p0 | O2P p1 |
| --- | --- | --- | --- | --- | --- | --- |
| Arrival published to first host sample (no negative sample; host inside its readiness sleep) | 7185 / 5855 | 7295 / 6446 | 7391 / 6816 | 7324 / 6369 | 7267 / 6170 | 2446 / 2436 (host inside a sentinel sleep) |
| Planning (realpath per path query) | 33 / 39 | 376 / 416 | 1345 / 1440 | 53 / 61 | 79 / 85 | 52 / 58 |
| Frame serialization | 142 / 163 | 323 / 364 | 788 / 848 | none | 175 / 194 | 29 / 32 |
| Pipes and spawn | 128 / 146 | 125 / 144 | 127 / 130 | none | 128 / 151 | 114 / 129 |
| Spawn to first verdict byte | 1054 / 1154 | 1052 / 1127 | 1074 / 1113 | none | 1086 / 1195 | 965 / 1017 |
| Spawn to EOF | 1226 / 1328 | 1799 / 1921 | 3350 / 3472 | none | 1325 / 1438 | 1209 / 1267 |
| Decode | 97 / 106 | 1160 / 1240 | 4263 / 4374 | none | 231 / 257 | 147 / 160 |
| Exit grace (validator already exited) | 3 / 4 | 4 / 6 | 4 / 5 | none | 4 / 7 | 2 / 4 |
| Collection total | 1641 / 1822 | 3786 / 4108 | 9889 / 10333 | 55 / 63 | 1965 / 2164 | 1571 / 1656 |
| Collection closure to release store | 2 / 3 | 9 / 9 | 25 / 28 | 7 / 8 | 4 / 4 | 2 / 2 |
| Release store to worker acknowledgement | 0.3 / 0.2 (below floor) | 0.1 / 0.2 (below floor) | 0.2 / 0.2 (below floor) | 0.2 / 0.3 (below floor) | 0.2 / 0.2 (below floor) | 0.2 / 0.2 (below floor) |
| Held total (arrival published to acknowledgement), ms | 8.9 / 7.7 | 11.1 / 10.6 | 17.4 / 17.2 | 7.4 / 6.5 | 9.3 / 8.3 | 4.0 / 4.1 |
| Worker release-wait passes (median) | 32141 / 25147 | 41535 / 35362 | 66334 / 61207 | 27179 / 21371 | 34169 / 27094 | 15605 / 14075 |
| Terminal publication to host done observation (2 ms poll) | 2508 / 2505 | 2067 / 2046 | 825 / 771 | 1995 / 1946 | 2461 / 2460 (one value per trial) | |
| Whole request, ms | 50.7 / 73.0 | 64.3 / 87.9 | 125.6 / 149.8 | 57.3 / 81.8 | 57.5 / 81.5 | |

- In every one of the 60 ordinary trials the worker applied, arrived and began
  spinning while the host slept in its readiness wait, whose single requested
  10 ms `nanosleep` lasted 12.5 ms (median; 10.3 to 12.5 ms). The host
  observed readiness, application and arrival on the same pass. That interval
  is 45 to 85 percent of the held total in every cell except O256, where it
  is 40 percent.
- The validator exit grace never slept: the validator was reaped on the first
  wait in all 72 eligible phases. The prior 24 receipts are now 72 observed
  intervals of 2 to 15 µs.
- The worker's release wait ran at 0.2 to 0.3 µs per pass in every trial, so
  the passes above are the held interval in units of worker polling work.
- Requested 2 ms sentinel sleeps lasted 2.51 ms (median overshoot 0.51 ms);
  the second phase of O2P arrived during one and was observed 2.44 ms later.
- Decoding at `-Onone` is 17 µs per verdict frame, 4.3 ms for 256.

### Decomposition: actor form (A2, two actors)

Medians of six trials; `rapid` / `idle`. Phases are the specimen's five:
p0 issuer issue and transfer, p1 and p3 subject consumes, p2 issuer's second
issue and transfer with the only eligible queries, p4 subject's final visit.

| Component | p0 | p1 | p2 | p3 | p4 |
| --- | --- | --- | --- | --- | --- |
| Activation store to worker observation | 0.3 / 0.2 (below floor) | 0.1 / 0.2 (below floor) | 0.1 / 0.2 (below floor) | 0.2 / 0.2 (below floor) | 0.1 / 0.1 (below floor) |
| Arrival detection with a negative sample (host 1 ms poll), µs and trials | none | 1256 (2) / 1257 (4) | 1139 (4) / 1257 (5) | 1255 (4) / 1253 (5) | 1256 (2) / 1256 (3) |
| Arrival seen on the first sample, µs and trials | 1.9 (6) / 2.1 (6) | 0.1 (4) / 0.1 (2) | 0.0 (2) / 0.0 (1) | 0.1 (2) / 0.1 (1) | 0.1 (4) / 0.0 (3) |
| Collection | 6.9 / 7.3 | 1.1 / 1.3 | 1647 / 1657 | 1.2 / 1.3 | 1.1 / 1.2 |
| Release store to acknowledgement | 0.2 / 0.2 (below floor) | 0.2 / 0.2 | 0.2 / 0.2 | 0.2 / 0.2 | 0.2 / 0.2 |
| Completion detection (host 1 ms poll) | 3.1 / 3.2 (first sample) | 1254 / 1255 | 1160 / 1158 | 9.2 / 9.4 (first sample) | 1250 / 1252 |
| Held total, ms | 0.014 / 0.015 | 0.005 or 1.26 / 1.26 | 2.67 / 2.90 | 1.26 / 1.26 | 0.004 or 1.26 / 0.63 (bimodal) |

- The parked subject's activation wait ran 55,000 to 70,000 passes per trial
  at 0.3 µs per pass; the issuer's 95,000 to 131,000. Each parked pass visited
  both inbound slots (2.0 visits per pass in every trial) and performed 2.1 to
  2.5 acquire loads per pass: 109,000 to 139,000 visits and 119,000 to
  169,000 loads per trial for a recipient of two deliveries. The issuer has no
  inbound slots and its scan returned at once.
- The host's recipient-acknowledgement wait slept once per delivery, 1.256 ms
  for a requested 1 ms, although the parked recipient acknowledged within
  0.3 µs of its pass sample; the issuer's exchange wait for that delivery ran
  about 5,000 passes (1.25 ms). The second delivery in p0 was answered within
  about 40 passes.
- The actor host's 1 ms execution poll lasted 1.256 ms (seven sleeps per
  trial); each actor's readiness wait slept 12.5 ms once.
- Whole request 87.5 / 113.1 ms.

### Neighbor comparison and observer effect

The neighbor ran every cell in both regimes. In `idle`, instrumented minus
neighbor whole-request medians were −0.5 to +3.4 ms, within the trial spread
of either app, so the instrument's whole-request effect is at most a few
milliseconds and sub-millisecond effects are unresolved, as the protocol
states. In `rapid` the instrumented app was 4 to 10 ms slower in every cell.
That regime is confounded by the cleanup rule: the neighbor's cleanup is the
CLI exit plus a 100 ms margin, so the instrumented launch that follows it
begins about 100 ms after the previous process exit, while the neighbor launch
that follows an instrumented trial begins within milliseconds of the observed
host exit. The historically observed idle-gap effect lies in that range. The
`rapid` neighbor comparison is therefore not an observer-effect measurement
and is retained as diagnostic only. The envelope's integer-millisecond fields
agree between apps in every cell (readiness wait 12 ms, sentinel and visit
timings within 1 ms). The host's export took 231 to 280 µs and lies inside
the instrumented request after every stamp.

### Nominations and limits

Branch 2 nominations, each a separate host candidate with its own acceptance
record and baseline on accepted source:

- **HOST-01: the readiness wait polls at 10 ms.** The worker's first arrival
  was observed 5.6 to 8.1 ms after publication in all 60 ordinary trials and
  the actor setup wait slept 12.5 ms per actor; the mechanism is the host's
  10 ms `nanosleep` loop over a nonblocking pipe read while the worker is
  already applied and spinning. The proposed change makes the readiness wait
  readiness-driven on the pipe with the same elapsed allowance, remaining-time
  bound, interrupted-call and clock-fault handling, as the validator's duplex
  loop already is. Expected saving: 6 to 8 ms of held interval per ordinary
  run and the setup wait per actor; the comparison measures it directly.
- **HOST-02: the host sleeps a full 1 ms or 2 ms poll immediately after
  publishing to a worker that responds within a microsecond.** After an
  activation store, a release store or an inbound commit the host samples
  once, finds the response absent, and sleeps; the worker observed the
  publication within 0.3 µs and arrived, completed or acknowledged within a
  microsecond, so the detection took the whole sleep: 1.25 ms per actor visit
  for arrival, 1.25 ms for completion, 1.25 ms per delivery for the recipient
  acknowledgement, and 2.44 ms for a second ordinary phase's arrival. The
  proposed change is a brief bounded re-sampling before the first sleep after
  each such publication, with no added wake and every allowance unchanged.
  Expected saving: about 1.25 ms per actor visit and per delivery, about
  2.4 ms per later ordinary phase.

Not nominated, recorded for the outflow: validator exit grace (never slept);
EOF to reap (2 to 15 µs); the 2 ms detection of the worker's terminal
publication (outside the held interval); decoding cost at `-Onone` (4.3 ms
for 256 verdicts, host work rather than detection delay); the 25 percent
overshoot of every requested host sleep (a condition to measure, not a
constant to tune).

Branch 1 basis: the whole frame-serialization interval is 142 to 163 µs for
one query, 323 to 364 µs for 64 and 788 to 848 µs for 256, in every trial
well above the 1.3 µs instrument uncertainty, so the plan's pre-build
rejection rule does not apply. The interval is 1.8 percent of the O1 held
total, 3.1 percent of O64's and 4.6 percent of O256's, against a derived cache
bound of 1,099,776 encoded bytes retained for the worker's life and a deferred
charge whose precedence needs new controlled-clock controls. The disposition
is recorded in the outflow and the plan.

ARM inputs: held intervals of 4 to 17 ms per ordinary phase and 1.3 to 2.9 ms
per actor visit, during which the worker spins at 0.2 to 0.3 µs per pass; the
parked actor spins for the whole of other actors' phases at the same rate.
Worker response to release and activation is below the instrument floor
(under 1.3 µs) in every trial, so any paced wait adds its whole wake latency to
a response that is now effectively zero.

### Revisions

None. The protocol above is as frozen at the record's commit.
