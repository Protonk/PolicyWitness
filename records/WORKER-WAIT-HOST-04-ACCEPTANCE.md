# HOST-04: ordinary final completion

This record belongs to the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md).
The candidate has passed its initial correctness selection and mechanics
rehearsal. No performance comparison or adoption is credited. The decision rule
and schedule below are frozen before comparison; exact staged identities are
added while the prepared driver waits at its coordinator gate. Raw runs are dispatcher-owned, gitignored and local.

## Candidate and claim

Accepted source is main at `6b8d7f0c`, including HOST-01 through HOST-03 and SCAN.
The first candidate is `1198cfc5` on `wait/host-04`, in
`/private/tmp/pw-wait-host04`; worker identity is
`6e8e46469c1ebf0677b799ad63adac5af20be68b20902e18450c5b6e70a8a9ba`.
Its generated identity changes with the host source; worker behavior and shared
layout do not change. Subsequent source repairs must be identified before freeze.

After the last ordinary collection, the host can wait on its already-retained
readiness pipe instead of an unconditional timer sleep. The same remaining
sentinel allowance and 2 ms maximum wait preserve periodic publication checks.
Notification returns to the existing decision: observe acknowledgement and done,
then sample owned child status. A notification is consumed once. If it precedes
publication/reap, bounded sleeping passes check both until an existing stop;
an unusable pipe falls back to sleeping. Missing readiness still closes the
read end so a late ready write meets EPIPE.

The structural claim is that an available exit notification can end the final
wait without waiting for the next timer expiry. It acquires no new descriptor,
thread, registration or post-apply worker communication resource. Ordinary
intermediate phases and actor scheduling retain their existing paths. This
does not remove all timer checks, observe descheduling/coalescing/energy, or
establish a reduction in held-worker CPU. An early hangup with a live worker
causes owned status checks on each remaining bounded pass instead of the former
50 ms cadence; controls and the cost account must retain that consequence.

## Decision rule

Accept only if independent controls and signed live traces establish the claimed
event-driven ending, complete witnessing and owned cleanup. A mere replacement
of one wait API with another is insufficient. Retain plain sleeps, notified
waits, timed-out waits, unusable waits and missing/truncated observations apart.
For each claimed ordinary workload/regime, require at least one observed
notification ending an entered final wait and complete final-wait accounting
on every accepted trial. A trial that observes completion before entering the
wait remains valid and is reported separately; it supplies no notification claim.

Report terminal-publication detection, terminal-to-reap, whole-request time,
host resource residence and observer cost. A shorter detection interval is
optional for structural acceptance; any quantitative improvement claim needs
improvement beyond uncertainty in every matched pair of its named workload.
Use the common uncertainty-expanded 2 ms response bound and 0.5 ms resolution
gate for applicable responses. Resolved worsening of aggregate latency, CPU,
memory or peer interference needs a written tradeoff decision. Leave unmeasured
CPU, memory, scheduling and energy quantities unestablished.

The intended comparison has O0, O1, O64, O256 and O2P ordinary cells, with A2
as an unchanged actor control, in rapid and idle regimes. Five alternating
matched pairs per cell/regime give 60 pairs. Keep contrary pairs. Use identical
inspection flavour and readers on both sides, one excluded first execution per
exact staged executable, fixed power state within each block and the existing
declared actual-gap ranges. Prepare calibration, mechanics and cleanup before
announcing a bounded quiet window; never extend its schedule silently.

## Required controls and verification

`CWorkerFinalWaitTests` uses the real host with a gated, unsandboxed ABI fixture:
one/two-phase final waiting, already-readable exit notification, publication
before delayed exit, early hangup, no done publication, unusable/missing pipe,
late ready-write EPIPE, interrupted return, deadline and clock failure. The
fixture has its own alarm and the test owns independent failure cleanup.
These controls do not establish restrictive-profile operation or performance.
Existing clock, readiness, lifecycle, phase and actor controls remain required.

The first signed-candidate selection is:

```sh
tests/run.sh --case runner_unit/pwrunner_core_unit_executable \
  --suite runner_abi_layout --case witness_contract/order_barrier_mutations \
  --suite source_drift
```

Before acceptance, run applicable held-footprint/actor timing qualification,
failure/framing/phase controls and the default battery on the integrated signed
candidate, following the plan's workload inspection and quiet-window rules.
The intentionally failing native-pause applicability case is not a passing
prerequisite. Pin/prune decisions wait for acceptance.

## Preparation

- Swift test executable compiled with two jobs; no tests were executed by that
  build. Its optional-Boolean assertion was repaired before compilation passed.
- The lifecycle C fixture passes `-Wall -Wextra -Werror -fsyntax-only`.
- Worker identity and footprint generator checks pass.
- All 63 existing timestamp patches apply to both accepted and candidate source.
- Candidate correctness run `/private/tmp/pw-wait-host04/tests/out/runs/host04-correctness-01`
  passed all 12 selected cases: 587 runner assertions, ABI agreement, ordering
  mutations and nine source-drift checks. The signed build passed verification.
- Apparatus commit `40e70a70` adds final-only wait accounting and direct
  terminal-to-reap, terminal-to-teardown and spawn-to-teardown intervals.
  Teardown is a program point after cleanup calls, not native absence evidence.
  Reader version 11 and its independent controls pass in
  `tests/out/runs/host04-reader-controls-03`.
- A first controls run under the temporary candidate worktree stopped at the
  stager's durable-location check. No native trial or timing claim was made.
  The successful run uses durable main-checkout evidence storage.
- Mechanics run `tests/out/runs/host04-mechanics-01` passed four selected cases,
  completed all 24 trial receipts, established calibration, and settled both
  staged apps with no surviving processes. Every ordinary receipt had complete
  final-wait accounting. It is marked dry-run and supplies no performance credit.
- The comparison uses a 240-second native window, 100 clock-pair trials, a
  15-second trial watchdog and the driver's cleanup reserve. Five pairs in
  each of six cells and two regimes give 120 accepted trial obligations.
  Exactly one initial execution per staged executable is excluded; the ordinary
  and actor warm cells also establish those separate paths. Pacing uses the
  existing rapid actual-gap range [0, 250 ms] and idle [1000, 1250 ms].
  No excluded trial is silently replaced inside this run. AC power and low-power
  mode are recorded per trial; transitions, sleep and incomplete coverage withhold
  credit. Alternating pair order and all contrary pairs are retained.
- Apparatus commit `a16ca672` adds a five-minute preparation gate before the
  native window. It allows exact staged identities to be committed before the
  coordinator releases the trials. Compile concurrency remains at most two.
- This comparison supports fixture-build observations in inspection flavour
  (`-Onone -g`), not production-byte speed or energy claims. In-situ stamp cost
  and export span are retained. A separate baseline/unstamped-neighbor run with
  this same apparatus checks observer effects before adoption; it is not pooled
  with the candidate comparison.

## Frozen comparison equipment

Run: `tests/out/runs/host04-comparison-01`. The prepared gate was still closed
when these identities were recorded. Signed source apps are unchanged; these
are the substituted instrumented executables.

| Side | Host SHA-256 | Stamp worker SHA-256 |
| --- | --- | --- |
| baseline | `75ab796359d6bf5a6735217380ed4dc7746af0652786e101b80d2cf99c848a26` | `5113835f17ef3e681f86887f16776b0d42911170ead8246157dd848ab1dffec6` |
| candidate | `35f08832eeb81e669827d8e2ad28e68c4ccd79c57eb77b1879ae58b497513da6` | `308d775ebf43671593dd1e3044cf3c4467d7038a82316de03aee6d7f46fd4230` |

| Input or receipt | SHA-256 |
| --- | --- |
| `tests/out/runs/host04-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/staged-identity-before.json` | `b73c6aed483ff4548c7c2b7b44b23405a3244410c7c37c1234d946b01d31acc2` |
| `tests/out/runs/host04-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/schedule.json` | `87cdb1db960b10f8a618df5766d47a3871e24c864ed2a50e7912f3176ab59043` |
| `tests/out/runs/host04-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/host-baseline/host-build.json` | `127e23d1d55cd4a8defe86ff54a3b31eaeb9a0765dadd172af12e4b26a6d6b2e` |
| `tests/out/runs/host04-comparison-01/suites/witness_contract/worker_wait_pilot/artifacts/host-candidate/host-build.json` | `6350092f401407fbb4b88cf10f29c7a75d73d1e97541e401553c0a85f7edf70e` |
| `tests/suites/witness_contract/worker_wait_pilot_reader.py` | `3615d6e6679d1b08d0f027c5afd7cd415dd87359ca939f695f776efe58de904c` |
| `tests/suites/witness_contract/worker_wait_pilot_controls.py` | `a56177211e7cc79f32666a28f7c150c3d996e99948efd6489f8ce2885919de71` |
| `tests/suites/witness_contract/check_worker_wait_pilot.py` | `5b60a0d6cd723c713b35467045bfa29d08f590c8899ac8df3ac2489622e0c899` |
| `tests/fixtures/worker_wait/host_stamps.py` | `5888f04806ba21f4ec10dd42388f08de721ee6a694855d4bfa746aa375076f5f` |
| `tests/fixtures/worker_wait/HostStamps.swift` | `dc46c088d2aa8bc2f742d3af1c1961c91e0517d7fb3d1e110fd0a6e8c580e4a0` |
