# Worker terminal exit and ordinary token cleanup

Status: implemented, independently reviewed and accepted. The
[implementation acceptance](../../../records/worker-terminal-lifetime/implementation-acceptance.md)
records the signed build, default battery, repaired test oracles, mutation
controls and retained evidence. This plan follows the completed
[terminal-publication investigation](TERMINAL-PUBLICATION-PLAN.md) under the
[worker redesign plan](../../../WORKER-REDESIGN-PLAN.md). The
[decision record](../../../records/worker-terminal-lifetime/decision.md),
[lifecycle investigation](../../../records/worker-terminal-lifetime/lifecycle-investigation.md)
and [token cleanup investigation](../../../records/worker-terminal-lifetime/token-cleanup-investigation.md)
retain source traces and bounded experimental evidence against
`51487f74da15de196d44c4ac571c7b322a2fe83b`.

## Result and scope

A worker reaching an existing terminal publication erases any accepted token
bytes, publishes the same terminal evidence, and calls `_exit(0)` immediately.
It no longer waits for the host's exit-request flag after publishing `done`.
Ordinary early returns and cancellation also erase accepted token bytes while
preserving their existing exit and publication meanings. The host reconciles
phase acknowledgement after confirmed reap so a worker that finishes between
polling samples receives the ordering credit its publications establish.

Retain the host exit-request flag for pre-acknowledgement cancellation, its
grace/termination/reap fallback, and the existing synchronous validator
collection. The host's separate mapping retains worker evidence after exit.
Terminal publication, native exit, and independently observed reap remain
distinct facts. This change removes the intentional post-publication wait; it
does not guarantee that native exit completes, bound native calls that have not
returned, impose a total host lifecycle deadline, or supervise exec descendants.
Watchdogs, parent-loss detection, validator cancellation and broader exec
supervision are outside this plan.

## Phase qualification and output contract

On ordinary replies, use the existing `eligibleOrderedStep` predicate and
`comparison.order: query_first` to qualify an otherwise admissible native query
as a prediction about the live specimen. Qualification requires successful
application, the phase's collection/release/acknowledgement chain, uninterrupted
ownership through acknowledgement, the existing protocol checks, a matching
worker PID and a unique matching phase-local validator record with coherent
native allow/deny data. Collection closes before release; the same worker's
subsequent acknowledgement establishes its survival through that collection.

Without this chain, retain received records as native query observations and
leave order `unestablished`. Missing acknowledgement does not establish that a
particular query reached an exited target. No per-query liveness check or
reconstruction is needed. Successful attempts, phase completion, successful run
completion and confirmed validator cleanup are not additional qualification
requirements. Later failure does not withdraw qualification already established
for a phase.

Preserve raw `sandbox_check` labels, native rc/errno, record association and
existing missing-result behavior. In particular, raw `allow` or `deny` beside
`unestablished` remains valid evidence. Refusal during synchronous collection may
now let the worker exit while queries remain; their native results may differ.
Retain whatever records arrive and close collection through the current bounded
collector. Do not assert a particular native answer for an exited target or
launch another collection against a worker already known to have been reaped.

Keep the degraded-reply exception: on `runner_reporting_failed`, including
`evidence_retained: true`, comparisons are absent and retained ordering is
diagnostic. Consumers must not reconstruct qualification from that retained
chain. This is specified by the
[reply construction failure contract](../../../tests/FAILURE-PROPAGATION-CONTRACT.md#reply-construction-failure).

There is no wire-schema or shared-layout change and no version bump in this
plan. These are the existing eligibility and reading rules; the host correction
supplies evidence previously missed in one race. Keep the
[wire contract](../../../docs/CONTRACT.md) unchanged in that respect. Do not add
a liveness field, a competing classifier, a new query outcome or a new
unavailability reason. Worker source identity must still be regenerated.

## Implementation

### 1. Preserve departures while adding ordinary erasure

In [pw_probe_runner.c](pw_probe_runner.c), add one bounded accepted-token erase
primitive using the existing volatile `pw_extension_erase` over the full
`PW_EXTENSION_TOKEN_BYTES` buffer when `extension_channel` is non-null. Keep
the borrowed mapping, `prepare_extension` placement and rejection-path cleanup.
A rejected mapping is not an accepted channel; do not dereference it after the
preparation path has cleared the pointer. Erasure does not consume or release a
native extension handle. Release remains an explicit specimen action.

Apply the following departure policies without consolidating their different
publication meanings:

| Departure | Required behavior |
| --- | --- |
| Existing parameter setup, compilation, apply, proceed-refusal and normal `done` paths | Preserve each payload/progress publication; erase accepted bytes before the existing release-store of `done`; then `_exit(0)` without reading `exit_requested`. |
| Ordinary returns from `main` after token preparation | Erase accepted bytes, then return the same code. Preserve existing failure/progress publications and absence of `done`. Earlier returns before preparation remain unchanged. |
| Cancellation observed in `wait_for_proceed` | Erase accepted bytes and `_exit(0)`. Add no failure, acknowledgement, completion or `done` publication. |
| Extension consumption | Preserve erasure at its current boundary before slot-result publication, including native consumption failure. |
| Normal path before post-apply hang/signal test interventions | Preserve its existing earlier erasure even though the terminal path also erases. |
| Fatal termination or a native call that does not return | Do not fabricate ordinary cleanup or publications. Existing independent host cleanup remains separately observed. |

Audit every ordinary departure after preparation, including parameter capacity,
policy-length expectation/read/length-mismatch/NUL checks and clock setup. Preserve
return versus `_exit` behavior on these early paths, the exit codes, failure
precedence, and untouched status words. Keep any existing cleanup that precedes
terminal publication in its current order. A small terminal helper may own
erase/store/exit; it must not absorb paths that currently omit `done`.

Remove `spin_for_exit` and its call sites. Keep `cpu_relax`, which is still used
by the pre-release wait. In `wait_for_proceed`, preserve the complete sampled
decision order, timing-fault stickiness, budget edge, future-release refusal,
cancellation sample and acknowledgement publications. Change only departure
cleanup and the post-publication exit. In particular, a late release cannot
revive a refusal, and a cancellation store racing after the worker's sampled
decision does not create a new protocol violation.

### 2. Reconcile acknowledgement after confirmed reap

In [CWorker.swift](../../../runner/Sources/PWRunnerCore/CWorker.swift), after
process cleanup and before computing `collectionBasis` or taking the final
snapshot, call `observeAcknowledgement()` when `process.status != nil`. This
covers both polling-loop reap and cleanup reap. Retain the existing observations
during polling and grace. Reconciliation applies after abnormal termination as
well as clean exit; do not condition it on `done`, exit code zero, completed
phases or successful run classification.

Use the existing predicate, `ownershipUnbroken && phase.releaseSet && ack == 1`.
The resulting credit describes ownership through the worker's acknowledgement;
it does not claim the reaped worker is still alive. A final acknowledgement
cannot repair a previously broken ownership chain, invent a release or qualify
an unreleased phase. Preserve previously established phase credit if ownership
is lost later, and preserve protocol violations as a separate veto.

Keep the final acquire snapshot and existing host mapping ownership. Do not
rewrite `pollStopReason`, manufacture an exit status, treat a termination
request as a reap, or turn a real deadline into timely success after late `done`.
Clean exit with completed evidence can be accepted with `child_reaped` as the
poll stop. Early terminal failure may instead expose readiness EOF; preserve
that actual observation with the published failure.

### 3. Preserve producer and reader responsibilities

Use [CWorkerOrchestrator.swift](../../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
and [PWRunnerAPI.swift](../../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
as the producer and encoder owners of phase ordering and `eligibleOrderedStep`.
Keep their existing predicate rather than adding a second qualification path.
Preserve phase-local treatment of proceed failures when deriving ordering; do
not withdraw credit from earlier phases. Keep run-level failure classification
and the treatment of other worker failures unchanged.

Retain the independent checks in [consumer.py](../../../tests/lib/consumer.py).
Its `query_column` and `select(query=...)` expose raw labels and keep that
meaning. The Swift encoder rejects unsupported `query_first` claims; Python
also rejects `unestablished` when the complete ordinary-reply predicate holds.
Preserve both checks without claiming their validation coverage is identical.
The Rust controller transports the observations and checks phase association
and disposition; do not expand it into another full eligibility classifier.

## Verification and test changes

Put regression equipment in the existing test owners, not in `records/`.
The four retained investigation controls used a copied host and a constructed
ABI child; they are source/race evidence, not acceptance of the signed product.
Use public CLI controls where reachable and deterministic internal fixtures for
races or branches an ordinary specimen cannot reliably force.

| Boundary | Required control and observation |
| --- | --- |
| Terminal exit without permission | Direct production-worker harness retains its mapping, leaves `exit_requested` zero and independently reaps exit 0 after normal completion and terminal refusal. Observe `done`, relevant failure/slots and no cleanup kill. Include allow-default, bare deny-default and an empty final phase. A bounded deadline must fail the old spin behavior. |
| Fast-exit acknowledgement race | In `CWorkerLifecycleTests.swift`/`PhaseProtocolTests.swift`, force acknowledgement between the host's last samples and polling reap, with ownership intact and no earlier host acknowledgement observation. Cover both clean exit with `done` and fatal termination without `done` or phase completion. Both require `child_reaped`, confirmed reap and `query_first`; the abnormal variant must retain its observed signal and `runner_failed` classification. Removing final reconciliation must lose ordering credit in both variants. |
| Ownership and phase boundaries | Force a wait error before acknowledgement, then later acknowledgement and confirmed reap; retain the error and withhold credit. Also retain an earlier established phase when a later phase loses ownership; unreleased phases and protocol violations never qualify. |
| Deadlines and failures after acknowledgement | Retain an actual deadline despite late `done`. Retain qualified earlier queries when attempts fail or the worker dies after acknowledgement; do not require completed phase/run. Confirm real exit/signal independently. |
| Refusal during collection | Delay the collector across worker refusal. Preserve received raw records, missing results and collector stop facts with order `unestablished`; perform no refused-phase actions. Use constructed allow/deny records to pin reader interpretation, and live execution to observe actual collection/exit behavior without fixing its native answer. |
| Early departures and cancellation | Exercise accepted-channel early-return branches and pre-ack cancellation. Verify original codes, failures, unchanged status-word/publication rules, no acknowledgement or actions, and accepted-byte erasure. Retain timing/expiry/future-release precedence controls. |
| Token erasure | Inspect the accepted channel's fixed buffer capacity independently of the erase call's length, with nonzero fixture bytes beyond the token's terminating NUL and host-side erasure withheld. Require the full buffer zero after ordinary departures; a shortened erase must fail. Verify consume-time and pre-hang/signal erasure separately, rejected-channel handling and null-channel safety. Native release-call observations must show no implicit release. |
| Erasure before terminal publication | On a terminal refusal before consumption, observe the full accepted buffer at the actual `done` publication boundary, before any later cleanup can run. Require zero bytes when `done` first becomes visible. A deterministic control that moves erasure after publication must fail even if the buffer is zero after reap. |
| Evidence and readers | Preserve completed slots, application/failure evidence and valid compiled-profile receipts after clean worker exit. Test raw allow/deny with unestablished order through supported readers. A degraded reply with an apparently complete retained chain still has no comparisons or recovered qualification. |

Use the existing
[worker harness](../../../tests/suites/runner_c_worker_harness/README.md),
[extension controls](../../../tests/fixtures/extension_controls/README.md),
[ordering tests](../../../runner/Tests/PWRunnerCoreTests/OrderingTests.swift) and
[failure-boundary suite](../../../tests/suites/failure_boundaries/README.md).
Extend existing test groups where possible. Register any new Swift group in
`runner/Tests/PWRunnerCoreTests/main.swift` and any new harness case in the
catalog with its actual prerequisites and coverage.

Strengthen the worker erasure oracle in
[control.c](../../../tests/fixtures/extension_controls/control.c): its existing
`controlled_erase` scans only the length passed to the erase function and cannot
detect an erroneously shortened call. The new oracle must inspect
`sizeof(channel->token)` through the independently held worker-channel mapping,
without deriving its scan bound from the erase argument, `token_length` or a
string scan. Seed and confirm nonzero bytes in the padding after the valid
terminating NUL, including the end of the buffer, before worker cleanup can
run. Preserve valid channel framing. Keep the issuer's separately allocated
string observation distinct from this fixed-capacity worker-channel oracle.

Attach a compile-time observation gate directly to the terminal `done`
release-store in the production-source test build. Hold the worker immediately
after that store and before any subsequent cleanup or exit; the independent
observer must acquire `done` and inspect the whole retained channel while the
worker is held. Exercise a refusal path with an accepted, unconsumed token so
earlier consumption cannot make the assertion pass. Withhold host erasure until
the observation is complete. The gate compiles away in the shipped worker.
Run negative controls that shorten erasure and that move erasure after the
store/gate, keeping the independent observations unchanged. Require the
respective full-buffer and publication-boundary assertions to fail; a final
post-reap zero scan alone does not establish erasure order.

Update controls that depend on the old handshake:

- Replace `exit_byte_clean` with a no-exit-request terminal-exit assertion.
  Update the bare-deny assertion and other descriptions of host-permitted exit.
- Replace `sigkill_fallback`'s completed worker waiting for permission with a
  controlled worker genuinely stalled before `done`; keep independent proof
  of the termination request and reap. Withholding permission after `done`
  must now establish prompt exit, never force a kill.
- Rename `host_lost_while_waiting` to `proceed_without_host_release` and require
  clean self-exit without a release or exit request. It simulates an absent
  host; the independent harness owns
  the mapping, deadline and cleanup, observes the refusal and reaps the child.
  Do not credit this as actual XPC-host death. Any separate real host-loss
  experiment needs independent process identity and durable cleanup ownership.

Do not use host erasure as proof of worker erasure. Extension fixtures must
retain exact resource ownership and recoverable cleanup records; observe bytes
in memory without writing raw tokens to logs or retained artifacts. Fatal
termination controls can establish absence of ordinary worker cleanup; they
must not be reinterpreted as promises of worker erasure on every termination.

## Documentation, generation and acceptance

Update current-behavior documentation in the implementation change:

- Edit `docs/architecture.json` and regenerate the architecture/worker accounts
  and diagrams. Update publication/exit edges, mapping/token lifetimes and
  source/check citations. Close applicable worker findings only against the
  implemented behavior and acceptance evidence, not this plan's adoption.
- Edit `docs/limits.json` where worker-release refusal and exit-grace behavior
  describe the old wait. Keep the existing allowances and scope of guarantees.
- Update `runner/README.md` and authored reading rules in
  `tests/FAILURE-PROPAGATION-CONTRACT.md`; regenerate their derived user-guide
  content. Explain phase qualification, raw observations after refusal and the
  degraded-reply exception without adding prediction/enforcement agreement.
- Align affected suite READMEs, coverage and catalog entries with their actual
  assertions. Permanent documentation and tests must not link to the records.

Run the owning generators after source/documentation edits:

```sh
python3 docs/generate_worker_identity.py
python3 docs/generate_architecture.py
python3 docs/generate_limits.py
```

Review generated C/Swift identity agreement and the layout golden; this change
must leave the shared layout unchanged. Do not edit generated copies directly.
Build a matching signed candidate through `make build IDENTITY='...'` using the
configured Developer ID identity and the [build guide](../../../docs/BUILD.md).
If a native source is added or moved, update its Meson target.

Acceptance uses the signed candidate's default live battery plus the mandatory
ordering mutation control, each with fresh output. Inspect the selections first
with `tests/run.sh --list` and
`tests/run.sh --case witness_contract/order_barrier_mutations --list`.

```sh
PW_TEST_OUT_DIR=tests/out/runs/terminal-exit-default tests/run.sh
PW_TEST_OUT_DIR=tests/out/runs/terminal-exit-order-mutations \
  tests/run.sh --case witness_contract/order_barrier_mutations
```

Use fresh suffixes if those output directories already exist. The default
battery must include the changed runner unit/worker harness cases, ABI/layout,
source-drift, failure-boundary, independent-reader and black-box checks, and the
phase/extension/compiled-profile controls. If a new required control is opt-in,
select it explicitly as well. Targeted runs during development do not substitute
for the candidate's final live acceptance. Follow
[test guidance](../../../tests/AGENTS.md) for locks, provenance, evidence reuse,
equipment failures and the prescribed retry outside an automation sandbox.

Completion requires the production worker's no-permission exit and independent
reap observations, independent full-buffer and pre-publication token-erasure
controls, recovery of previously unseen acknowledgement after both clean and
abnormal exit, negative ownership controls, preserved reader/qualification
semantics and passing signed acceptance. Record any unrun or failed checks as
such. Report residual native
exit/call and descendant limitations for the later exec investigation. This
refactor can be implemented before that investigation without selecting a
descendant supervision design.
