# Evidence clarity implementation plan

Status: proposed; implementation has not begun. Prepared 2026-10-14 against
`93f82c86ab84247318618e5bb877a93624890f07`.

Six claims survived the documentation review because they describe real limits
of current PW. This plan changes the behavior, interface or evidence that makes
each qualification necessary. A qualification can be retired only after its
replacement claim has passed the corresponding acceptance gate.

The broader interface and architecture ideas are in the associated
[parking lot](records/EVIDENCE-CLARITY-PARKING-LOT.md). They are deferred and do
not add acceptance requirements to these six items. This document plans future
implementation; creating it does not execute that work.

## Checkpoint and order

| Item | Claim to retire or narrow | Status | Completion evidence |
| --- | --- | --- | --- |
| C1 | `not_run_worker_died` does not establish that the operation never started | Planned | None |
| C2 | `malformed_transport` can mean a local setup failure | Planned | None |
| C3 | Readers do not fully validate phase ownership of validator subprocess metadata | Planned | None |
| C4 | Ready and sentinel time budgets count polling iterations | Planned | None |
| C5 | Some build refusals lack behavioral controls | Planned | None |
| C6 | The local-name filter ID lacks equivalent empirical verification | Planned | None |

Implement C1 and C2 first, then C3 and C4. C5 and the C6 investigation are
independent of that sequence. Coordinate contract changes across coherent
increments; each committed increment must have matching producers, readers and
fixtures. Do not leave a partially migrated contract for a later item to fix.

During execution, update this checkpoint with implementation commits, source
and app identities, test receipts, remaining findings and the next action.
Record an inconclusive C6 experiment as inconclusive, with the item still open.
The plan closes when all six gates pass or the user explicitly accepts a
documented change of scope.

## Shared implementation requirements

- Preserve one fresh host and worker per specimen, the host/worker sandbox
  boundary, and collection closure before release. Preserve the limited meaning
  of `query_first` and independent prediction, attempt and diagnostic evidence.
- Follow the [wire contract](docs/CONTRACT.md). A renamed outcome or changed
  interpretation requires the corresponding response or envelope version
  change. Enforcing an existing invariant alone does not. New required ownership
  evidence is a reading-rule change; a new optional diagnostic field alone need
  not be. Decide and record the version effect of each increment before editing.
- Update admission if affected, transport, Swift/Rust/Python readers, fixtures,
  failure and coverage contracts, and user documentation together. Use
  [contract.json](docs/contract.json) and the owning generators. Historical runs
  retain their original bytes and versions; do not translate them into new
  meanings or add compatibility aliases to current semantic readers.
- Regenerate worker identity when its inputs change. Shared-memory layout
  changes also require C/Swift agreement, the layout golden and bounds review.
  Update the limits, build and architecture manifests when their facts change;
  regenerate owned copies rather than editing them directly.
- Follow [test guidance](tests/AGENTS.md), including fresh output directories,
  evidence provenance, resource ownership and cleanup. A fault fixture must
  establish what it actually controls. Source agreement and a plausible error
  string do not establish that a live boundary was exercised.

## C1 — Name the missing result, preserve observed progress

**Current claim.** The attempt outcome `not_run_worker_died` is a compatibility
spelling for no completed result. Its name suggests that the operation did not
run, although the worker may have started or returned from the native call
before dying. The qualification is explicit beside `AttemptOutcome` in
[PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift) and in the
[guide](docs/PolicyWitness.md).

**Change.** Replace the spelling with an outcome describing the missing completed
result; `no_completed_result` is the proposed name. Inventory every synthesis
site before fixing its exact applicability. Keep the reason for missing evidence
and the independently observed lifecycle progress in their existing evidence
channels. A later progress marker must never manufacture the missing native
return value, errno or access result.

Migrate the outcome vocabulary, encoders, comparison rules, consumers, matrix,
goldens and examples in one response-contract increment. Audit user-facing
messages for any remaining inference from the old word `not_run`.

**Acceptance gate.** Exercise death before an attempt, after the pre-call marker,
and after native return but before result publication using controls that can
establish those positions. The reply must preserve the distinctions the worker
published, withhold the unpublished native result, and use the new neutral
outcome consistently in every reader. Completed earlier slots must survive.
Version controls must reject the old response version without reinterpreting it.

**Retirement.** Remove the explanation of the misleading compatibility spelling.
Keep the rule that a missing result does not establish whether an operation ran.

## C2 — Separate channel rejection from local setup failure

**Current claim.** In `prepare_extension` in the
[C worker](controller/tools/pw_probe_runner/pw_probe_runner.c), delivery status
`malformed_transport` aggregates channel validation failures with failures of
core-dump suppression, descriptor inspection, mapping and close. The aggregate
cannot identify which happened.

**Change.** Give rejected channel data and local setup failures distinct delivery
outcomes. Retain a bounded stage or operation identifier and the native result
and saved errno when a native call supplies them. Distinguish a failed `fstat`
from a successfully inspected but undersized channel. Do the same for mapping,
close and header/token validation. Capture errno at the failing call, before
cleanup can overwrite it; do not invent errno for a format rejection.

Define precedence and retention when more than one failure is observed, including
cleanup failure after an earlier error. Preserve the existing no-delivery and
capability-unavailable distinctions. Carry the evidence through shared memory,
the host decoder and public lifecycle records with explicit publication rules.
Keep token bytes out of replies, diagnostics and retained fixtures.

**Acceptance gate.** Individually force each local failure and each channel
rejection class through the production preparation path. Check that the
published classification and native details identify the controlled failure,
that consumption cannot proceed without accepted delivery, and that interruption
before publication leaves the result unknown. Cover combined failure precedence,
token confinement and successful delivery. Run the shared layout, worker-identity,
reader and signed extension lifecycle checks affected by the new representation.

**Retirement.** Replace the catch-all caveat with the precise status definitions.
Delivery success still does not establish consumption or effective access.

## C3 — Validate validator collection ownership

**Current claim.** The exact step/query join prevents borrowing a prediction for
a differently named action, but readers can accept copied `expected_step_ids`,
raw records or subprocess PID metadata from another phase. See the guide's
validator-subprocess account and the current joins in
[consumer.py](tests/lib/consumer.py).

**Change.** Define an explicit association among the run's phase, its actual query
plan and the child collection that serves it. Start with the producer in
[ValidatorClient.swift](runner/Sources/PWRunnerCore/ValidatorClient.swift), the
orchestrator and all semantic readers. Validate the existing relations first;
add a collection identity where the available fields cannot establish ownership.
Bind that identity to the host's child-lifecycle record and collection, rather
than inferring ownership from numeric PID uniqueness.

Specify how `expected_step_ids` is derived from the actual eligible query plan,
including exclusions and empty plans. Retain that plan independently of returned
records; do not reconstruct historical target eligibility by resolving paths
again. Define consistent handling of missing, contradictory and foreign metadata.
Preserve unexpected, duplicate and null-ID raw records as diagnostics where the
contract permits them, while preventing them from supplying an owned verdict.
An internal collection identifier does not authenticate a replacement validator
executable or prove that it made a native call.

**Acceptance gate.** Transplant whole subprocess blocks and individual identity,
expected-ID and record fields between phases. Include repeated identical query
text under different action IDs, late output, empty collections, spawn failure,
partial replies and unconfirmed cleanup. Contradictory ownership must fail the
specified reader validation; missing ownership must withhold dependent claims.
Valid sequential child instances with a reused numeric PID must remain valid.
All semantic readers must make the same ownership decisions and preserve valid
degraded evidence. Run the ordering mutation control if eligibility changes.

**Retirement.** Remove the documented metadata-ownership hole only after the
transplant controls reject the mismatches for the intended reason. Keep the
separate limits of validator authority and native-call observation.

## C4 — Measure ready and sentinel allowances with a monotonic clock

**Current claim.** The ready-byte and worker-publication loops in
[CWorker.swift](runner/Sources/PWRunnerCore/CWorker.swift) turn milliseconds into
iteration counts. Sleep, syscall and scheduling costs therefore do not consume
the stated allowances as elapsed time.

**Change.** Use monotonic elapsed deadlines, drawing on
[MonotonicDeadline.swift](runner/Sources/PWRunnerCore/MonotonicDeadline.swift).
Define starts, expiry and completion-at-deadline precedence for both waits.
Bound each polling sleep by the remaining allowance; progress and interrupted
calls must not renew it. Ensure the readiness read is nonblocking, with an
explicit setup failure if that prerequisite cannot be established.

Preserve the budget boundaries: readiness follows policy transfer; the sentinel
allowance excludes each synchronous phase collection interval; the aggregate
collection allowance continues to charge its own planning, collection and
cleanup time. Measure excluded intervals explicitly and handle clock failure,
regression and arithmetic limits without extending the wait indefinitely.
Recheck worker ownership and the phase boundary before release after collection.

**Acceptance gate.** Controlled-clock tests must cover irregular polling costs,
oversleep, interrupted calls, zero remaining allowance, clock failure and multiple
excluded collection intervals. Live delayed-worker controls must confirm the
configured budgets and partial-evidence behavior with stated scheduling tolerance.
Run `witness_contract/order_barrier_mutations`, affected worker/validator failure
and lifecycle cases, and limit-contract checks. Update the generated budget
account and authored explanation together.

**Retirement.** Replace the iteration-count warning with the elapsed-budget
definition. Expiry starts the documented stop/cleanup path; it does not promise
an exact total response time or instantaneous process termination. Broader cleanup
ownership and cancellation remain parked.

## C5 — Establish the untested build refusals behaviorally

**Current claim.** Some build refusals have source checks but no behavioral
control. [build_baseline.json](tests/fixtures/docs/build_baseline.json) enumerates
the remaining entries, affected variants and proposed experiments.

**Change.** Treat that baseline as the work inventory. Group entries by setup
cost and protected operation, and add controls to the existing build-guard and
source-drift harnesses. For each applicable full/partial build variant, arrange
the fault in a disposable checkout, run the actual guard, and observe that the
operation it protects did not happen.

Use command receipts, tool-call records and before/after artifact inventories
as appropriate. A tool wrapper may inject a missing or invalid output, but the
production refusal must make the decision. Include a valid neighboring case to
show that the test did not merely fail at an earlier prerequisite. Where a
claim concerns real signatures or toolchain output, use that real artifact.

**Acceptance gate.** Every baseline refusal has a passing registered control for
its applicable variants. Demonstrate that bypassing or moving the guard beyond
its protected operation makes the control fail. Update [build.json](docs/build.json)
and its generated account with the actual control owners, and remove each
baseline entry only when its behavioral evidence exists. Keep the baseline file,
including when empty. Run the build-documentation and selected preflight/build
guard cases; do not enlarge another baseline to accommodate the work.

**Retirement.** The caveat about these untested refusals can disappear when the
inventory is empty. Compiler trust, cache provenance and reproducibility remain
separate issues in the parking lot.

## C6 — Establish the supported scope of the local-name filter

**Current claim.** PW emits local-name filter ID `17`, but the guide says it has
not received the empirical verification described for global-name filtering.

**Change.** Build an experiment that actually exercises the relevant local Mach
namespace. Establish the service and target identity, policy and native operation
before comparing candidate filter IDs. A global-name lookup of a similarly named
service is insufficient. Inspect and extend the
[filter harness](tests/suites/witness_contract/harness/verify_filter_id.sh) as
needed: its `--allowed-value` check alone observes a sibling query answer, not
the sibling's kernel operation.

Observe native attempts under controlled allow and deny policies for the target
and an independently exercised sibling. Retain query results separately, with
macOS/build, architecture, executable/signing provenance, policy, namespace setup
and cleanup receipts. Register a repeatable regression for the supported case.
Follow the [runner guidance](runner/AGENTS.md) before changing an excluded
operation/filter pair.

**Acceptance gate.** Resolve the experiment to one of two supported dispositions:
a bounded, reproducible working mapping for the tested environment, or evidence
supporting explicit prediction unavailability for the affected operation/filter
pair. In the latter case, update the shared exclusion set, readers, fixtures and
documentation while retaining supported attempts. A failed fixture, unreachable
service or nondiscriminating result is inconclusive and leaves this item open.
Neither disposition establishes general prediction/enforcement agreement.

**Retirement.** Replace the unverified-ID sentence with the demonstrated scope
and the resulting capability decision. Do not generalize one environment's
result to all macOS releases or operation/filter combinations.

## Integrated acceptance

After the affected checks pass for each increment, run the signed default test
battery and the opt-in controls required by the final changes, including the
ordering mutation control and build guards. Use the repository's evidence-reuse
rules for unchanged dependencies and retain a clear ledger of fresh and reused
results. Verify current wire versions, worker identity, layout/bounds, generated
documentation and the exact six retirement decisions together.

Read the resulting guide, architecture, build and signing accounts as a user.
Each removed qualification must have a named replacement behavior and passing
evidence. Keep uncertainty about unpublished results, hidden native state,
effective access and unavailable logs wherever it remains true. Record unresolved
findings and cleanup ownership before closing the plan; release publication is
outside its scope.
