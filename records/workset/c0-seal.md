# C0 acceptance and seal

Frozen account: `records/workset/pytest-first.md`, version C0.2, at commit
`0c22d2565b42f543bd6334a1d09f95781ef09386`. Its examined implementation remains
`bf7e97faab75754efe719b0bad20e83b67762c15`. The acceptance record is committed
after that account; its own commit is not the source of a test run or build.

## Acceptance

The primary executor accepts C0 under the user's ordinary-milestone authority.
This is an architectural readiness judgment, with author review and a separate
read-only review by agent `review_initial_counterfactual`, not empirical
validation of a pytest implementation.

| Required result | Established in the frozen account |
| --- | --- |
| A pytest-first arrangement rather than restarting subordinate adoption | Three explicit owners: pytest for collection/fixtures/execution/report phases; PW integration/domain adapters; external session and durable-resource supervision. The current dispatcher is not retained as a second test scheduler. |
| Obligations distinguished from current implementations | Twelve-row responsibility map states framework work, remaining specialized work, and replaced or changed machinery. |
| Consequential scenarios | A–G cover failure continuation and teardown, interruption/descendants/lock lifetime, once-applied extension phases, native source extraction and Swift membership, signed-artifact refusal, BYOXPC recovery, and oracle/documentation limits. |
| Historical findings treated at their actual strength | The rejected trial's costs, incomplete original verification and later citation failures are retained as findings about that attempt. Survey counts are dated; current selection counts are separately observed. |
| Assumptions, expectations and uncertainty | Host/subject interpreter isolation, serial execution, engine/adaptor feasibility, expected benefits and surviving costs are explicit. There is no benchmark, net-benefit conclusion or migration recommendation. |
| Boundary for the later investigator | Frozen questions remain open. No retrospective evaluation or prescribed future experimental program is included. |

The reviewer assessed candidate `6cd868b` and identified one consequential
ambiguity: selection publication appeared before lock acquisition and durable
ownership. C0.2 resolves it by keeping collection/preview in memory and requiring
lock/recheck, ownership publication, then plan publication before execution.
The reviewer reported no other consequential gaps. The primary executor reviewed
the correction against the existing run-ownership contract. The review agent
made no changes and ran no tests; its assignment is complete.

## Verification and limits

`git diff --check` passes. The existing repository link reader's `broken_links`
helper was run directly over the workset plans and records and found no broken
local links. This is a local document check, not a catalog case or battery run.
No build, native experiment, pytest implementation trial or new product runtime
verification is credited to C0.

The diff from the intake source through the frozen account contains only the
workset plans and `records/workset/` material. No implementation, fixture,
generator or test machinery has changed. No active sub-agent can alter this
seal. The original account at `6cd868b` and the review correction at `0c22d25`
remain recoverable in git.

C0 is complete. E1 and the independently ordered documentation lane may now
begin. Corrections to the frozen account, if needed, will be new attributable
records. This seal does not accept any later stage.
