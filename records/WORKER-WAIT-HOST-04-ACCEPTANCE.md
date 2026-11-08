# HOST-04: ordinary final completion

This record belongs to the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md).
Accepted after integrated qualification. The frozen decision rule and schedules
below preceded comparison; staged identities were committed before the
coordinator released either window. The first full run and its compiler-setup
failure remain visible alongside the targeted repair. Raw runs are dispatcher-owned, gitignored and local.

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

## Frozen observer comparison

`tests/out/runs/host04-observer-01` uses the same accepted production source,
reader and inspection flags. Instrumented and unstamped neighbors each run all
six cells in both regimes, five repetitions, with the same warm-up, pacing,
100 calibration trials and 240-second native window. It is a separate observer
cost diagnostic, with no performance-adoption claim or pooled candidate pairs.

| Prepared receipt | SHA-256 |
| --- | --- |
| `tests/out/runs/host04-observer-01/suites/witness_contract/worker_wait_pilot/artifacts/staged-identity-before.json` | `aef1699819ed7b892989369605e0c2b7905d0131d7277281fa256b8d1e34d233` |
| `tests/out/runs/host04-observer-01/suites/witness_contract/worker_wait_pilot/artifacts/schedule.json` | `ca8b2af83a5217fdef42c1c06ee111ac3beb6f694e513f8c542cd7d02f79a13a` |
| `tests/out/runs/host04-observer-01/suites/witness_contract/worker_wait_pilot/artifacts/host-instrumented/host-build.json` | `8a2c7e72c5d4e19b5d4a22273123e9c5e3989eafad977c3cdc6831ac8d51265d` |
| `tests/out/runs/host04-observer-01/suites/witness_contract/worker_wait_pilot/artifacts/host-neighbor/host-build.json` | `2bd7b2d91cf483456e95c582f912460237bbf2abd8d7c915a74d833ffb5d9b4a` |

## Comparison and coordinator disposition

`host04-comparison-01` completed its native window in 74.187 seconds, with
120/120 accepted trials, 60 matched pairs, no exclusions or missing responses,
and verified settled cleanup. AC power was stable. Spotlight was using roughly
one core at the pre-window check; per-trial load and power observations remain
in the receipts. Neither side's complete ordinary final-wait trace was truncated.
All 50 baseline ordinary trials used one plain final sleep. All 50 candidate
ordinary trials used one notification-ended final wait, with no timeout,
unusable return or fallback sleep. Actor trials made no final-wait claim.

Across all 50 ordinary pairs, terminal detection, terminal-to-reap and
terminal-to-teardown improved beyond their paired uncertainty. Detection savings
ranged from 119.58 to 2,785.29 microseconds; this is a fixture-build observation.
Every applicable response bound was credited: the largest bound was 4.290
microseconds, with maximum combined uncertainty 3.998 microseconds. Whole-session
residence did not improve in every pair, and whole-request improvement is not
claimed. CPU, memory, energy and scheduler/coalescing effects remain unmeasured.

The whole-request spread rule flagged O2P idle repetition 4: candidate
78.932 ms versus baseline 76.962 ms, a 1.970 ms worsening against the baseline
spread of 1.140 ms. That pair's spawn-to-teardown interval was 2.282 ms shorter;
the extra end-to-end time therefore lies outside that measured interval.
This does not establish its cause or erase the regression flag. The other four
O2P idle pairs were faster. Several component flags also occurred on unchanged
collection/actor paths; all remain in `summary.json`, without an overall-speed
claim or selective trial removal.

`host04-observer-01` completed in 79.496 seconds: 120/120 accepted receipts,
calibration established, no exclusions, settled cleanup. Instrumented minus
unstamped whole-request median differences varied from -3.297 to +26.304 ms
across cells/regimes. Export spans were 224.041–2,553.875 microseconds; in-situ
host stamp-cost medians were 0–41 ns, subject to the calibrated endpoint floor.
There is no universal overhead correction and no claim that these fixture
latencies equal production latency. Both candidate comparison sides used the
same recorder and reader. The source apps' controller bytes differ between
builds despite matching inspection settings; their identities are retained,
another reason not to attribute whole-request differences solely to the wait.

**Written tradeoff decision:** retain the observed end-to-end regression and
accept the structural candidate subject to the integrated verification below.
The user-directed benefit is freedom from an unconditional timer at this final
wait, using the existing descriptor and allowance. Independent controls and all
ordinary live trials establish that mechanism; no response gate failed and no
resource was added. This narrower benefit warrants adoption without a universal
latency win. This decision does not credit lower total CPU, lower energy or
system coalescing, and does not amend the frozen measurement rule. A future
claim of improved whole-request performance needs its own controlled comparison.

No whole-request group worsened beyond spread in every pair. Under the existing
reader rules that is the resolved-increase criterion; the isolated any-pair flag
above prompted investigation and remains part of this disposition.

## Integrated verification and acceptance

Production integration is `1451c488`; current-behavior documentation is
`3d4e5f6a`. The native source identity remains
`6e8e46469c1ebf0677b799ad63adac5af20be68b20902e18450c5b6e70a8a9ba`.
The main signed build passed before verification. The checkout also contained
an unrelated draft plan, so no pristine whole-tree source claim is made.

`host04-main-default-01` (`20261108T195934Z_bf36fffc`) completed all 222
selected cases: 221 passed and `preflight/native_policy_controls` failed at
Swift linker discovery, before the two intended Swift-option refusals. Its raw
failures remain intact. The temporary compiler-cap wrapper called the toolchain
directly without supplying an SDK when none was set. The corrected wrapper
sets the selected macOS SDK only in that case and retains the concurrency cap.
No repository source or app byte changed for the retry.

`host04-main-targeted-01` (`20261108T201629Z_62c102f4`)
passed all six cases: the repaired native-policy control, ordering mutations,
ABI agreement, native observer controls, held-reader controls and 24/24 live
held-footprint measurements. Both runs had no skips, unrun cases or system
sleep, and their artifact-integrity checks established unchanged app bytes.

The default selection includes all 587 runner assertions, validator failure and
framing paths, phase/order effects, restrictive-profile attempts, cleanup and
actor timing qualification. The latter covered one, three and eight actors;
its largest total charged interval was 106 ms. The targeted retry closes the
one equipment failure; the original full run is not relabeled all-pass.

The targeted run completed in 152.190 seconds within its six-minute window. Its held case
retains the unchanged busy-worker interpretation with a 10 ms accounting quantum;
it does not convert final-wait latency savings into a worker CPU claim.

Accepted on the structural and finite-observation evidence above. The retained
controls cover fallbacks absent from the successful live comparison. No new
resource, sandbox exception, worker communication or public evidence field was
introduced. Retention is finalized with the remaining host round.

| Integrated artifact / equipment | SHA-256 |
| --- | --- |
| `dist/PolicyWitness.app/Contents/Resources/Evidence/manifest.json` | `4372eb9e345048516729147434f06124235c9cb915f06e843d03f31aab33f267` |
| `dist/PolicyWitness.app/Contents/Resources/Evidence/provenance.json` | `7978f15445090ad6c712860b2dacdfd192e17c5a2f0af9a60a83da462596f722` |
| `/private/tmp/pw-host-followon-tools-v2/swiftc` | `c46dc9c6964458e43429809332a192ff8b8b3271af7e724c8068696709de66a3` |
| `/private/tmp/pw-host-followon-tools-v2/swift` | `480fdec512a2b1075ccf0ddb3bfaba0eca6e1a33c02be99a45a2974932fee1aa` |
