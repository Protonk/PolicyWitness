# Documentation candidate: pause before tests/builds

The user authorized documentation work and required return before any tests or
builds. That preparation is complete. No build, test, dispatcher (including
listing), native probe or generator `--check` ran during this tranche. No final
readers have started, and none of the three documents has final acceptance.

## Prepared changes

Two fresh Astra owners completed their bounded assignments, bringing the total
to seventeen specialists. Their reports are `documentation/architecture-worker-report.md`
and `documentation/limits-report.md` under this record directory's parent.
Root reviewed their source changes and coordinated generation.

- ARCHITECTURE now describes public actor routing and a local handoff sequence,
  separating custody, recipient acknowledgement, settlement, source observation,
  phase completion and advancement. Generated process/boundary/resource rows
  retain all IDs and qualify ordinary/declaration versus actor applicability.
- WORKER adds a form/resource crosswalk, scopes the declaration channel and
  actor regions, and distinguishes byte erasure, native release and fresh access.
- LIMITS retains every original numeric value, corrects scope and timing/retention
  accounts, and adds the existing whole-path diagnostic bounds: eight components
  and 63 UTF-8 bytes per component. The inventory has 95 entries. New independent
  Swift value observations and literal boundary assertions await execution.
- Shared guide prose and generated tables are updated, along with the controller
  dependency inventory and witness timing-qualification account. No product
  implementation or generator implementation changed in this tranche.

Root corrected inherited qualification-total shorthand after inspecting its
checker: total is setup elapsed plus schedule execution elapsed, including
collection during execution. Charged execution is a separate metric. Total
excludes final cleanup and the earlier cutoff-to-setup interval. This correction
is reflected in current docs/outflow; historical investigation records remain
historical.

## Authoring and review performed

Write commands, executed centrally:

```sh
tests/lib/python.sh docs/generate_limits.py
tests/lib/python.sh docs/generate_architecture.py
```

The first two limits-generation attempts refused authoring inputs: a scalar
marker at the beginning of a continuation line, then external links inside the
standalone shared-limits block. Root fixed marker placement and moved linked
semantic routes immediately below that block; the shared explanation remains
standalone. The third invocation succeeded: 95 limits, 15 questions, 43 matrix
rows. These were write-mode authoring refusals, not test executions.

Architecture generation succeeded, updating the two tours and four DOT/SVG
pairs. Root rendered those four changed SVGs to 2000-pixel-wide PNG previews
using `rsvg-convert`, inspected them, and shortened the B18 figure-only label to
avoid overlap while retaining the complete table claim. A second architecture
write invocation regenerated only that DOT/SVG pair. The boundary preview was
then refreshed and inspected. Previews are in `documentation/rendered/`.

This was an initial figure review; the large WORKER figure was inspected as an
overview. Whole-document rendered fidelity, including detailed tables and zoomed
figures in final reader artifacts, remains part of stage 5 preparation. No
claim of fresh reader comprehension or complete rendered-artifact fidelity is
made here.

Read-only source/diff review confirmed all original 93 values and all graph IDs
are preserved. `git diff --check` reported no whitespace errors. The original
ten implementation files and two diagnostic-fixture files retain their recorded
hashes. `documentation/pretest-state.json` and `documentation/candidate.patch`
pin the current candidate and review observations. No evidence cleanup, lock
removal, commits or staging occurred.

## Resume

First recheck candidate identity. Then run the two generators with `--check`
and the following serialized selection in a fresh managed output directory,
under the documented automation-sandbox guidance:

```sh
PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-docs-01 tests/run.sh \
  --case source_drift/architecture_documentation \
  --case source_drift/limits_documentation \
  --case source_drift/generator_contract \
  --case runner_unit/pwrunner_core_unit_executable
```

This includes compilation of the changed Swift test owner. None of it has
started. The changed entries describe existing enforced bounds; no runtime
limit value or behavior changed. Earlier limit/repair controls retain only their
recorded scope and need an explicit dependency/applicability assessment before
being credited to this candidate. Do not repeat the broad battery merely for
prose changes, or treat its prior 82/83 outcome as wholly passing.

Build 1121 remains the earlier signed implementation equipment, not a newly
staged distribution of the revised guide. No distribution rebuild has been
performed. Any later distribution refresh follows the signed build workflow.
F1 remains deferred with its original failure evidence; no more setup-oracle
observations are queued. After validation and evidence review, return before
launching the six fresh stage-5 readers/assessors. Prepare faithful complete
artifacts and keep those readers unexposed to this implementation discussion.
