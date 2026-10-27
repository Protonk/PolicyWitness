# Host setup oracle: observe verdicts without preserving blind spots

## Problem and proposed result

`runner_unit/host_setup_oracle_sensitivity` copies the current setup recipe and
checker, then runs a baseline and three deliberately wrong disposable host
variants. Despite its `legacy` naming, it does not retrieve an older checker.
A pass requires the current checker to accept every variant. Improving that
checker can therefore fail the experiment even when the correct host and the
independent native observations are unchanged.

The proposed reduction preserves the experiment while withdrawing its
requirement to reproduce three checker limitations. Record whether the current
checker accepts or rejects each wrong variant; keep acceptance mandatory for
the unmodified baseline. Treat the old mapping counter as an observation for
the wrong variants, without requiring its false zero after partial unmapping.

This remains a proposal. The diagnostic tradeoff is giving up the automated
claim that all three blind spots still exist. It does not remove the case,
repair the production host or strengthen the setup checker itself. There is no
PW wire-admission change. The supporting
[investigation, finding 3](../../../records/tests/PW-HISTORICAL-CONTINUITY-INVESTIGATION-REPORT.md#3-the-setup-sensitivity-case-requires-a-past-blind-spot-to-remain-present)
records the rationale and the limits of nearby coverage. Source inspection at
`6c871e1` confirms the coupling below; no native execution establishes this
proposed change yet.

## Owners and the coupling to remove

- [host_setup_oracle_sensitivity.py](host_setup_oracle_sensitivity.py):
  `prepare_variant` substitutes the wrong ready-pipe direction, shared-memory
  descriptor argument or unmapping extent. `inspect_receipts` records checker
  verdicts and independent observations. `assert_observations` requires 22
  accepted receipts, 22 recipe results, ten rejected controls and a zero
  `legacy_maps_before_fixture_cleanup`. `main` also requires
  `legacy_recipe_completed`.
- [host_setup_controls.py](host_setup_controls.py): `run` builds and collects
  the 22 scenarios, calls `check` after each receipt, and stops on the first
  rejection. It then checks ten altered receipts. Simply removing the
  sensitivity case's all-accepted assertion would still leave collection
  coupled to acceptance.
- [Host setup fixtures](../../fixtures/host_setup/README.md): the copied
  `observer.c`, `SetupControls.swift` and `shim.c`, with supplemental
  instrumentation in the sensitivity driver, own the independent argv,
  descriptor-mode, mapping-range and cleanup observations. Production changes
  are outside this proposal.

## Implementation approach

1. Separate complete receipt collection from checker acceptance in the setup
   recipe. Preserve the ordinary `runner_unit/host_setup_controls` case's
   requirement that its unchanged scenarios pass `check`. Give the sensitivity
   driver a way to collect every scenario and retain each verdict without
   stopping merely because a deliberately wrong variant was rejected. Keep
   build errors, child failures, missing or malformed receipts and unexpected
   checker errors distinct from a recorded rejection; none becomes success.
2. Require all 22 expected scenario identities and complete independent
   observations for the baseline and each of the three variants. Preserve
   baseline checker acceptance. For wrong variants, retain verdicts and
   diagnostics without requiring acceptance, and retain the mapping counter
   without requiring its zero value. Keep native observations authoritative
   for the deliberately changed argv, access modes and unmapping extent.
3. Preserve the ten receipt rejection controls using admitted, unaltered
   baseline receipts. Check acceptance before applying each alteration so a
   stronger checker cannot make a negative control pass solely by rejecting
   an unrelated host fault already present in its input. Retain each altered
   input, rejection and its relationship to the admitted receipt.
4. Preserve source copies, exact substitutions, source/input hashes, build
   receipts and logs, original receipts and separate observer results. Keep
   positive mapping observations before unmap, negative observations after
   full unmap, surviving-suffix observations after partial unmap, and confirmed
   fixture cleanup. Missing evidence and failed cleanup still fail the case.
5. Update the script's description and terminal summary, its
   [catalog description](../../catalog.json), the
   [suite account](README.md#host-setup-oracle-sensitivity-opt-in),
   [verification guide](../../CHANGE-VERIFICATION.md#worker-resource-challenge-probes)
   and [outcome coverage](../../COVERAGE.md#worker-resource-challenge-observations)
   to describe the revised experiment. Preserve the canonical case, selection,
   opt-in membership and equipment requirements. Adjust fixture documentation
   if the collection interface changes its account.

The nearby `launch_descriptor_controls` case observes descriptor and mapping
properties and rejects restored defects, but does not replace the full
three-variant experiment. Removing that experiment is outside this reduction.

## Verification and completion

Follow [test guidance](../../AGENTS.md). Run
`runner_unit/host_setup_controls` and
`runner_unit/host_setup_oracle_sensitivity` through `tests/run.sh`, using a fresh
output directory and the required Swift/clang equipment outside the automation
sandbox. These cases do not require a signed app. Keep disposable build state
in the harness scratch directory and retain source/build identities with the
observations.

The changed sensitivity case needs controls that distinguish these outcomes:

- A disposable stronger checker accepts the correct baseline and rejects at
  least one independently observed wrong variant; collection still finishes,
  required observations and fixture cleanup remain available, and the case
  succeeds while retaining that rejection.
- Missing or contradictory independent receipts, incomplete scenario coverage,
  equipment/collection errors and failed cleanup still fail the case. Checker
  rejection must not conceal any of them.
- All ten altered-receipt controls start from accepted inputs and reject for
  their intended distinction. Baseline checker rejection remains a failure.

Keep these controls with the existing dispatcher-reached cases. Review the
retained raw evidence as well as the case status; a zero exit alone does not
establish preservation. Check updated links, case IDs and documentation against
the resulting behavior. Completion requires evidence of both the allowed
stronger-checker result and the retained failure boundaries, with the diagnostic
loss stated explicitly in the change description.
