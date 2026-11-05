# Documentation lookback accepted; retirement held

The user authorized the remaining wording correction and final acceptance of
the plan actions, with a pause immediately before retirement. The correction
is applied and its focused checks pass. Stages 0–6 of
`docs/DOC-LOOKBACK-PLAN.md` are complete. ARCHITECTURE, WORKER and LIMITS are
accepted with the evidence qualifications below. No documentation action
remains open; F1 remains an accepted, separately assigned implementation
deferral. Neither plan nor the supporting records have been retired.

## Accepted actions

| Actions | Final disposition |
| --- | --- |
| D1–D5 | Accepted documentation corrections, actor sequence/resource crosswalk, scoped budgets/capture/fallback account and inventory-completeness changes are implemented and regenerated. All original 93 numerical values remain; two existing diagnostic-path bounds bring the inventory to 95 entries. |
| I1 | Actor parameter refusal paths now retain actor identity. Direct internal and public checks pass with their recorded scope and applicability. |
| I2 | Exact-cap native capture control passes. It establishes capture of a constructed readable 1 MiB object, not compilation/application of a 1 MiB policy. |
| I3 | Six controlled fallback-association cases pass. They establish dependency-seam inputs/order/association and gating, not a live-helper observation. |
| R1 | Corrected the premature “last figure” reference in authored ARCHITECTURE prose. Fresh architecture-documentation and generator-contract cases pass. |
| R2 | Reference inventories retained. Observed navigation effort did not establish a missing central explanation or justify redesign. |
| R3 | Reader evidence accepted with the recorded onramp, task, skim, prompting and PDF-presentation limitations. No extra reading round is required. |
| F1 | Remains open and deferred under the earlier explicit user decision. The root outflow retains its owner, evidence, unknown cause, proposed investigation and acceptance checks. |

## Final correction and identity

The only source change since the paired-reader checkpoint is at
`docs/ARCHITECTURE.md:622`:

```diff
-The last figure is the graph those generators and rules draw over the
+The document graph below shows how those generators and rules connect the
 documents: which manifest feeds which generator, which regions it writes,
```

This is authored text outside the following generated region. It changes a
figure referent, with no behavioral, source-citation, generator-input or
figure change. `acceptance/r1.patch` preserves the exact delta;
`acceptance/before-r1.json` and `acceptance/tested-candidate.json` pin its
before/after identity. `acceptance/verification-03.json` records the accepted
source state and test result. The tested candidate remained unchanged through
execution and acceptance recording.

The complete reading artifacts, six reports, three histories and coordinator
review remain unchanged at the hashes in `final-readers/final-state.json`.
That file and `final-readers/FINAL-REVIEW.md` are historical records of the
pre-decision checkpoint, including their then-pending acceptance status. The
ARCHITECTURE PDF consequently retains the old wording; the one-line delta
above is the accepted post-reading change. WORKER and LIMITS source hashes
still match the reader manifest. No fresh pair or replacement PDF is needed
for this correction.

## Verification credited at acceptance

The final command was inspected with `--list`, then executed once outside the
automation sandbox:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-docs-03 tests/run.sh \
  --case source_drift/architecture_documentation \
  --case source_drift/generator_contract
```

Run `20261105T050537Z_eee41d84` completed both cases in 43,578 ms: two passes,
zero skipped/unrun cases, zero recorded sleep overlap and no harness errors.
The transcript and requested selection were attached under the checkout lock
after verifying owner/run identity, resolved path and terminal accounting.
Original managed evidence is gitignored and available in this checkout.

The three-case documentation rerun in `documentation/VERIFICATION-02.md`
remains the limits-documentation credit; its architecture/generator results
are supplemented by the fresh checks above. The intervening source delta
changes only the figure referent, with limits inputs, copied guide, generators,
tests and executable source unchanged. The 525/525 Swift tests and three
downstream reader replays retain their prior credit. I1–I3 historical execution
remains qualified by `documentation/EVIDENCE-APPLICABILITY.md`, including its
explicit manifest-input exceptions. No other old case acquires new execution
credit from this acceptance.

The earlier broad selection remains 82 passes and one failure out of 83; F1's
later failures remain failures. This is acceptance of the completed lookback
actions with a visible deferred fixture investigation, not a wholly passing
battery or a claim that the observer-startup cause was resolved. No new
distribution build, Swift run or F1 execution occurred for R1.

## Document acceptance and review limits

All three documents are accepted as accurate and useful within the reviewed
scope and stated evidence bounds. ARCHITECTURE and WORKER received scoped
initial audits, targeted factual investigations and complete final paired
readings; comprehensive source verification of every claim is not asserted.
All 93 original LIMITS entries received distinct evidence assessments and a
changed-path missing-limit search; the two diagnostic bounds were subsequently
grounded and checked. This does not establish every runtime boundary or every
possible OS resource restriction.

The six final roles support the assigned work and whole-document accounts,
with assessors intentionally informed by first reports. They do not establish
arbitrary unaided discoverability, measured misunderstanding rates or the truth
of a cited claim merely because its symbol/check exists. Their actual
interventions, WORKER skim and correction chronology, and PDF expansion costs
remain visible in the accepted evidence. No reader concern is silently
converted into an implementation defect or new deferred assignment.

## Pause before retirement

The single root `READER-OUTFLOW-PLAN.md` now records completed review and
document acceptance separately from open F1. The execution plan, outflow,
all review records, reader artifacts and managed test evidence remain in place.
No archiving, deletion, pruning, retention-index change, staging or commit was
performed. No build, test or agent is active.

The next user review is the retirement decision. Any later retirement must
preserve F1's actionable handoff and any still-needed unreplaced observations;
review closure itself does not authorize discarding them. This turn stops
before that decision or any retirement operation.
