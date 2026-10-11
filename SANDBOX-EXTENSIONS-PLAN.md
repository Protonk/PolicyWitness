# PolicyWitness 0.3.0 sandbox extensions implementation plan

Implement a bounded experiment that observes file sandbox extensions during
one disposable worker's lifetime under one fixed, once-applied SBPL policy.
The result must retain issuance, delivery, consumption, release, phase-specific
predictions, and fresh access attempts as independent observations. Successful
native calls do not establish the worker's effective permissions.

This is the active implementation plan. Update its checkpoint and milestone
status as work proceeds. It carries the requirements of the initial agent brief;
the brief is retired. Current behavior remains defined by the repository's
contracts until each implementation increment changes them.

## Current checkpoint

| Milestone | Status | Completion evidence |
| --- | --- | --- |
| Repository investigation | Complete | Baseline and findings below |
| M1 Native feasibility and independent controls | Pending | Required before settling issuer authority and native integration |
| M2 Ordered phases in the existing worker | Pending | Requires M1 design decisions; phase ordering, interruption, and ordinary one-phase controls |
| M3 Minimal extension experiment through PW | Pending | Requires M1 and M2; real CLI specimen, incomplete native results, and token confinement controls |
| M4 Failure combinations and adversarial coverage | Pending | Requires M3; extends the boundary controls already required in M2 and M3 |
| M5 Contract completion and integrated acceptance | Pending | Requires all preceding milestones |

**Next action:** build the M1 native experiment and its independent controls,
starting with a controlled read-only file extension and an ordinary unprivileged
issuer. Establish the actual signing and entitlement baseline before interpreting
any outcome.

After each increment, update this table and next action, link the implementation
commit and applicable evidence, and state unresolved decisions. Put detailed
empirical findings, negative results, and reproduction instructions in an
associated `records/SANDBOX-EXTENSIONS.md` record when M1 produces evidence.
Follow [record guidance](records/AGENTS.md); link that record from this plan.
Keep permanent documentation focused on current behavior, with history in git.

## Scope and constraints

- Keep a fresh host and worker per specimen, with exactly one policy application
  in that worker. Consumption and release execute in that same worker.
- Keep the XPC host free of native sandbox API calls. Issuance happens outside
  the sandboxed worker under separately recorded authority.
- Establish ordering with observed protocol boundaries. A phase is an ordered
  interval, not a stable state snapshot or proof that a target retained its identity.
- Keep native results, missing observations, partial publication, and uncertain
  cleanup visible. Do not add `extension_active`, prediction/enforcement agreement,
  drift verdicts, or unsupported sandbox-cause claims.
- Keep raw tokens out of specimens, command arguments, environment variables,
  ordinary diagnostics, envelopes, logs, and retained artifacts. Use local token
  and handle references; keep authority-bearing bytes in transient channels.
- Begin with investigator-owned files and the smallest demonstrated extension
  class. Broader classes, process-bound issuance, overlapping grants, and arbitrary
  stateful programs remain outside initial scope without being declared impossible.
- Keep ordinary stateless specimens simple. Use one canonical execution model
  with a one-phase path in which all eligible queries finish collection before
  any attempt begins. Do not introduce historical schema translation.
- Limit the initial model to a bounded sequence of phases, queries, and ordered
  actions. Exclude branches, loops, arbitrary dependency graphs, and user-defined
  conditions. Token/handle references and a release that cannot run after failed
  consumption need fixed operation semantics, not a general dependency engine.
- Preserve bounded admission and collection, explicit refusals, partial evidence,
  and optional denial logging that cannot change execution results.

PW maintains bounded operational state to route references, coordinate execution,
and identify published observations. Claims about the apparatus still require
observations: a host release request and a worker acknowledgement are separate
facts. This state supplies no model of the kernel's effective permissions. As
the implementation lands, explain this distinction under the existing evidence
and runner principles in the architecture account; do not describe proposed
behavior as already implemented.

## Baseline and findings

The repository investigation used source commit
`8ae8024f60b16dc4918969339c63cc4b11c0ab71`. No product implementation was changed.
The host reports macOS 26.7.1, build 25G241. Dynamic symbol lookup found
`sandbox_extension_issue_file`, `sandbox_extension_consume`, and
`sandbox_extension_release`; this establishes availability only. Issuer authority,
consumption effects, release effects, and query sensitivity remain untested here.

The following findings determine the work:

- [CWorkerOrchestrator.swift](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
  plans queries once and invokes one validator collection. The
  [worker driver](runner/Sources/PWRunnerCore/CWorker.swift) releases all attempts
  through one `proceed` and `proceed_observed` pair. Phases require a new protocol.
- [PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift) requires a
  query/attempt pair per step. Lifecycle interventions need their own meaningful
  records, without invented queries. Ordering is currently interpreted at run
  scope by both the producer and [independent consumer](tests/lib/consumer.py).
- The [C worker](controller/tools/pw_probe_runner/pw_probe_runner.c) promises no
  allocation after application. Private extension calls require investigation
  before retaining or revising that promise. Pretouching PW's shared memory does
  not establish the behavior of code inside a native library.
- `attempt_file_open_read` opens a fresh descriptor but discards read and close
  results. Its successful status establishes an open, not verified retrieval of
  known contents. The experiment needs stronger observations if it claims a read.
- Query eligibility currently includes host path resolution before execution.
  Decide its phase-specific timing explicitly; later host diagnostics cannot
  substitute for the observation used to admit a query.
- A prior [project investigation](https://github.com/Protonk/PolicyWitness/issues/1)
  reports release calls without reliable access revocation on Sonoma 14.4.1.
  Treat this as a lead for controls, not a finding about the current host.

Three baseline cases passed: `source_drift/contract_versions`,
`source_drift/architecture_documentation`, and `source_drift/generator_contract`.
Their [run summary](tests/out/runs/extensions-brief-review-20261011/run.json) is
gitignored and available only in this local checkout. These checks establish
mechanical agreement and generator controls, not live extension behavior or
general product acceptance.

## Proposed execution design

Use a bounded sequence of phases. At each phase entry the worker publishes its
arrival and waits. The host observes arrival and worker ownership, plans and
collects eligible queries for that phase, closes collection on every terminal
path, and publishes release. The worker acknowledges that release before running
the phase's declared actions in order. It then publishes arrival at the next
boundary or final completion.

Use numbered boundaries and immutable phase/event publications so a previous
release or acknowledgement cannot satisfy a later phase. Distinguish reaching a
native call boundary, the call's return, and publication of its result. A marker
written immediately before a call establishes only that execution reached that
boundary; it cannot prove the call entered or completed. A worker can also die
after a native return but before publishing it. A later phase arrival must not
manufacture a missing earlier call result. Failed predictions can leave an
informative execution history; no phase should wait indefinitely for a usable
verdict.

The first specimen has this conceptual sequence, independent of final JSON names:

| Phase | Queries while the worker waits | Worker actions after release |
| --- | --- | --- |
| Before consumption | Query access to the controlled file | Fresh access attempt, then consume the referenced token |
| After consumption attempt | Query the same access against the same worker | Fresh access attempt, then release the handle if one was obtained |
| After release attempt | Query the same access against the same worker | Fresh access attempt and terminal publication |

Phase names describe placement in the experiment. Only event records establish
whether consume or release was attempted or returned successfully. Resolve
runtime dependencies explicitly: failed consumption leaves no invented handle;
a dependent release records why it could not run. Keep later observations useful
when safe to continue, and record where a terminal failure stopped execution.

A disposable native issuer supervised by the host is the initial topology to
evaluate. Use a dedicated bounded transient channel for tokens, separate from
retained evidence. Choose issuance timing and helper lifetime from M1 evidence;
do not assume the issuer must stay alive or can safely exit before consumption.
Keep the worker's handle table limited to routing references and observed call
outcomes. It must not model kernel permission state.

Initially prefer a fresh validator collection per phase, reusing the current
bounded driver. Measure the cost and cleanup behavior before considering a
persistent validator protocol. Each accepted native record must be associated
with its phase, query, and observed worker lifetime; late records cannot migrate
into a subsequent collection.

## M1 Native feasibility and independent controls

Build a small native harness independent of PW's result classifier and phase
implementation. Register its controls through the test harness and preserve
source, build commands, OS/SDK facts, signing and entitlement read-backs, native
results, and independent effects. Keep tokens entirely transient.

1. Create a regular file with known contents and controlled permissions. Record
   its identity and verify it is accessible before introducing the experimental
   policy. The sandboxed worker must not inherit an open descriptor to this target.
2. Issue a read-only extension outside the worker. Apply one fixed policy with
   the relevant extension predicate in the worker. Observe access before consume,
   after consume, and after release, using a fresh open/read/close sequence each
   time. Retain native returns and errno with their validity conditions, file
   identity, and bounded content observations sufficient to verify the read.
3. Query the live worker externally at each paused boundary. Record answers even
   when unchanged or unavailable; require neither prediction agreement nor a
   deny/allow/deny pattern for evidence validity.
4. Run separate controls for no consumption, a policy without the extension
   predicate, a different target, unsuccessful issuance/consumption, and retained
   descriptor access after release. Hold other conditions fixed within each
   comparison and distinguish retained access from a fresh open.
5. Test the issuer lifetime and authority relevant to the shipped app. Record its
   credentials, signature, entitlements, and demonstrated authority as experiment
   inputs. Do not infer entitlement requirements from symbol availability or a
   failed call. Distinguish incorrect inputs, signing conditions, and automation
   sandbox restrictions before concluding that ordinary issuance is unavailable.
   Running an ordinary process outside the automation sandbox does not itself
   give the product new privileges.
6. Inspect and, where practical, instrument native allocation/resource behavior
   after application, including first-call behavior. Document what is measured
   and what remains uncertain. Resolve the existing allocation claim explicitly.

**Completion gate:** a reproducible native lifecycle experiment and controls,
with findings supporting the chosen issuer authority, token transport, call
signatures, result widths, and worker invariant. In particular, preserve the
consume API's handle width separately from PW's existing 32-bit status fields.
If evidence indicates that issuance requires elevated privileges, a privileged
service, or an entitlement unavailable to ordinary PW distribution, report the
finding and obtain an explicit user decision before designing or implementing
that authority expansion. Continue independent diagnostics that do not require
it. Any other failed essential premise also requires reporting the evidence and
revising this plan before building dependent features. Retaining access after
release or unchanged queries does not by itself invalidate the witness objective.

## M2 Ordered phases in the existing worker

Introduce phases using existing file operations before adding production
extension calls. Exercise the smallest provisional request and evidence
representation needed for this increment, informed by M1. Internal harnesses may
establish the phase protocol before new public syntax is settled. Let the native
extension experiment integrated in M3 determine the public representation;
provisional wire formats still require explicit versioning and coordinated readers.

- Define phase/action identities, legal ordering, reference admission, and the
  ordinary one-phase authoring path. Decide request and response version changes
  through [the wire contract](docs/CONTRACT.md); change the envelope version only
  if its reading rules require it.
- Implement phase arrival, collection closure, release, acknowledgement, and
  terminal handling in C and Swift. Associate predictions and comparisons with
  the correct phase. Define eligibility at that boundary and preserve unavailable
  queries separately from access attempts.
- Bound phase count, total actions/queries, publication storage, and total
  collection time as well as individual waits. Specify how phase waits interact
  with worker execution, cleanup, exec budgets, and the client RPC timeout.
- Update producers and independent readers together, including lifecycle
  interpretation, shape fixtures, ABI layout, and generated worker identity.
- Use independently observed file effects and held validator gates to establish
  that actions cannot run early and later queries follow completed interventions.
  Include stale/wrong-phase acknowledgement, interrupted collection, worker death,
  and missing-prediction controls. A missed boundary or premature worker death
  must not produce a fictitious completed phase. Extend and run
  `witness_contract/order_barrier_mutations` whenever its governed code changes.

**Completion gate:** independently controlled execution through the production
C/Swift phase protocol with multiple real boundaries in one worker, mutation
controls that reject premature execution, and interruption controls that withhold
unsupported phase completion while retaining earlier evidence. A signed CLI
one-phase regression must establish that every eligible query finishes collection
before any attempt begins. A multi-phase public CLI experiment is required in M3;
it need not force a public grammar commitment in M2.

## M3 Minimal extension experiment through PW

Integrate the M1 issuer and native calls with the M2 protocol. Implement the
three-phase experiment above using local references and structured lifecycle
events. Record issuance and delivery independently from worker consumption,
including explicit unavailable or skipped dependent actions. Use this integrated
experiment to settle the minimal public syntax, subject to M4's adversarial
checks before treating the interface as final.

Provide the access evidence established in M1. If a new action or changed action
meaning is needed, apply the request-contract rules rather than silently
reinterpreting `open_read`. Preserve native results and local handle association
without treating them as a permission state.

Add the issuer to Meson, bundle assembly, signing, evidence inventories, native
source checks, helper resolution, and BYOXPC signing/read-back as applicable.
Do not grant it the worker's entitlements by accident. Cover missing helpers and
unsupported native capability explicitly. Keep host sandbox-import guards intact.

Test token confinement on success and failure, including malformed transport,
truncation, diagnostics, and cleanup. Compare captured output with token bytes
inside the test process without printing the token or placing it in a retained
fixture. Bound token storage, close inherited channels deliberately, and erase
buffers at the chosen lifecycle boundary. Resolve exec/inheritance interactions
explicitly; refuse unsupported combinations rather than silently expanding scope.

Exercise interruption around consumption and release in this milestone. Include
death after the pre-call marker, during the operation where a controlled seam
can establish that position, and after native return but before result
publication. Use observations to distinguish the test intervention from what PW
can know. No published native result means the result remains unresolved even
when the test knows the call returned.

**Completion gate:** the public CLI retains the native lifecycle and three sets
of queries/access attempts for one applied policy and worker. Independent controls
identify the target, worker, signing baseline, and fresh descriptor use. Issuer
failure remains an inspectable result with no fabricated consumption or release.
Interruption controls preserve unresolved native outcomes and earlier published
observations; the producer and independent readers reject invented completion.

## M4 Failure combinations and adversarial coverage

The boundary controls below belong to the earliest indicated milestone. M4
extends them with combined faults, adversarial timing and inputs, and failures
that are difficult to reproduce naturally. Each case must establish its
intervention independently and assert retained observations as well as withheld
claims. Revisit the interface if these controls expose an unrepresentable outcome.

| Boundary | First required | Required controls |
| --- | --- | --- |
| Phase admission | M2 | Duplicate/unknown phase or action identities, unsupported combinations, oversized counts/strings, embedded NUL |
| Extension admission | M3 | Duplicate/unknown references, forward/invalid handle use, unsupported combinations, unavailable helper/API |
| Issuance and delivery | M3, building on M1 native refusals | Native refusal, issuer death, timeout, partial/oversized token transfer, delivery without consumption, unknown cleanup |
| Consumption and release | M3, building on M1 native calls | Rejected token, failed consume without a handle, failed release, repeated release policy, missing result publication |
| Phase ordering | M2 | Delayed/missing predictions, validator failure, late/wrong-phase records, stale release/acknowledgement, phase exhaustion, host loss while worker waits |
| Worker lifetime | M2 for phase interruption; M3 for native calls | Death before/inside/after consume or release, death before acknowledgement, failure after a completed earlier phase, unresolved termination/reap |
| Independent readers | M2 for phases; M3 for extensions | Reject fabricated lifecycle success, cross-phase prediction association, unsupported versions, and unsupported ordering claims while retaining raw evidence |
| Optional logs | M3 with multi-phase CLI integration | Repeated target/PID across phases remains ambiguous unless evidence narrows it; log presence, absence, or capture failure cannot change execution |

Observe native-call failures through controlled seams where live reproduction
is unreliable; do not confuse injected return values with kernel behavior.
Preserve an observed call boundary without a published native result as unresolved.
Do not infer explicit release from worker exit or successful cleanup from EOF.

**Completion gate:** failures at every new boundary retain the evidence they
actually produced, prevent unsupported claims, and leave explicit cleanup facts.
All token confinement controls pass without retaining real token bytes.

## M5 Contract completion and integrated acceptance

Update documentation as each milestone changes behavior; this milestone checks
the complete account. Maintain architecture/process/channel boundaries in
[docs/architecture.json](docs/architecture.json), build behavior in
[docs/build.json](docs/build.json), versions in
[docs/contract.json](docs/contract.json), and bounds in
[docs/limits.json](docs/limits.json). Regenerate through the owning tools and
review generated layout, identity, diagrams, and shape changes. Update the user
guide, request grammar, FAQ, failure contract, test catalog, coverage, and opt-in
guidance with implementation-grounded claims and independent checks.

Follow [test guidance](tests/AGENTS.md) throughout. For changed admission and
transport, run `failure_boundaries`, `runner_unit`, `runner_abi_layout`,
`runner_c_worker_harness`, and `unit`, plus affected validator and witness cases.
Run the signed default battery against the final candidate, the new lifecycle
cases, the required ordering mutation control, and applicable BYOXPC controls.
Select signing/build/maximum-reply controls when their boundaries changed.
Verify aggregate limits and the largest admitted reply through real transport.

Use fresh `PW_TEST_OUT_DIR` directories. For each credited case retain its
canonical ID, command/configuration, source snapshot, applicable signed build,
and independent observations. Reuse results only under the documented evidence
reuse rules. Never remove the checkout lock or bypass cleanup ownership. Follow
the sandboxed-harness retry guidance before attributing environmental failures
to the product; retain failed runs and unresolved resource ownership.

**Completion gate:** PW demonstrates the controlled experiment under its supported
signing environment, all applicable checks pass against the accepted source and
build, and the investigative record identifies empirical findings, design
decisions, and accepted limitations. Predictions may remain unavailable or
unchanged, and release may leave access observable; those outcomes must remain
informative. Report the implementation commits and evidence locations without
claiming a reconstructed kernel permission state. Packaging or publishing a
release is separate from this implementation plan.
