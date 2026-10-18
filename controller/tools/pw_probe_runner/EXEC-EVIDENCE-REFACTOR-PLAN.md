# Exec observation and cleanup evidence

Status: implementation specified; awaiting review, not implemented. This plan
implements the evidence separation selected after the
[exec investigation](EXEC-SUPERVISION-PLAN.md), under the
[worker redesign plan](../../../WORKER-REDESIGN-PLAN.md). The
[investigation report](../../../records/worker-exec-supervision/investigation.md)
retains source analysis, live survivor observations and the external-group
experiment. Planning baseline: `dcb16d1cb5a0fc585a8d0e824e33024841f3b634`.

## Result and scope

Publish the worker's exec observation, cleanup requests and leader reap as
separate structured facts. Preserve the existing execution and cleanup policy:
ordinary observation ends at leader exit plus both stream EOFs; deadlines and
observation faults can request group termination; ordinary completion does not.
The existing leader-only fallback and bounded nonblocking reap remain in place.

Keep actual pipe acquisition and spawning after sandbox application. Add no
native calls, clock samples, waits, signals, deadlines, resources, processes,
request controls or authority. Record results of calls already made. Keep
their ordering, ownership checks, retry behavior and error precedence. Native
scheduling can still change; preserving the call sequence is not a claim of
identical elapsed time or identical results across executions.

This change does not terminate background work on ordinary completion, clean
exec descendants after worker death, contain escaped descendants, establish
group absence or ensure descendants exit before a later step. An external
supervisor, earlier live child registration and stronger cleanup sequencing
remain separate design choices. Descriptor ownership, sysctl, configuration and
environment refactors are outside this implementation.

## Existing meanings to preserve

The producer is [attempt_exec_spawn](pw_probe_runner.c); the host decodes the
completed slot in [CWorker.swift](../../../runner/Sources/PWRunnerCore/CWorker.swift)
and maps it in [CWorkerOrchestrator.swift](../../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift).
Keep these distinctions through every layer:

| Existing field or boundary | Retained meaning |
| --- | --- |
| `child_pid > 0` in a completed worker result | `posix_spawn` produced that child. It establishes neither target user-code entry nor reap. |
| `child_exit_code` / `child_term_signal` | Decoded leader status only after `waitpid` returns that child; otherwise retain the existing sentinels. |
| `rc`, `errno`, `outcome` | Existing aggregate attempt status and error selection, including observation, cleanup and reap failures. A zero leader exit can coexist with `rc: -1` and `exec_failed`. |
| Slot `completed`, lifecycle summary `completed` | Immutable result publication, including a failed result. It is not process or descendant completion. |
| Comparison `succeeded`, basis `spawned_child` | Successful spawning independently of later observation or cleanup. Preserve its precedence over permission-shaped post-spawn errors. |
| Run classification and phase qualification | Existing worker disposition and collection/release/acknowledgement rules. Do not derive a new run outcome, comparison or ordering claim from the added object. |

The current producer preserves leader status but discards stream EOF state,
collapses successful group signalling, `ESRCH` and no request into a zero
cleanup-error variable, and discards the fallback signal result. Its aggregate
error can also contain a synthetic reap timeout rather than a native wait
errno. The new record exposes those distinctions without redefining the old
fields or parsing their diagnostic text.

## Additive response contract

Add optional `steps[].attempt.exec_observation`, populated by the new producer
only for a completed worker `exec/spawn` result after successful spawning.
The object has required `collection`, `cleanup` and `reap` sections. It describes
the worker's own observations; it contains no host or fixture cleanup facts.

Absence or null means structured exec evidence is unavailable. Keep valid
current-format replies without the object valid, including older producers'
successful exec replies. Do not interpret absence as no spawn, no cleanup
request, EOF, successful reap or clean completion. Pre-spawn admission/setup/
spawn failures, synthetic results and non-exec attempts omit the object; their
existing evidence remains unchanged. An unpublished slot supplies none of it,
even if the worker wrote a PID or some new payload bytes before dying.

### Collection section: the snapshot before cleanup

Take this snapshot when the existing observation loop stops, before the first
cleanup signal or final reap. Never update it from a later cleanup/reap result.

| Field | Required meaning |
| --- | --- |
| `stop_reason` | `leader_exit_and_eof`, `deadline`, `observation_error` or `clock_fault`, selected by the branch that actually ended observation. |
| `leader_exit_observed` | Boolean recording whether `waitid(... WNOWAIT)` reported this leader during collection. False means not observed there, not that the leader was alive at its end. |
| `stdout.eof`, `stderr.eof` | Required booleans; true only after the corresponding `read` returned zero during collection. False means no EOF observation. Buffer closure, omitted/empty output and truncation are not EOF. |
| `deadline_kind` | `child` or `plan`, present only for the actual deadline stop, using the existing selected cutoff. Do not add a new clock sample or infer the kind from elapsed wall time. |
| `waitid_errno`, `poll_errno` | Optional terminal native errors from those collection calls. Recovered `EINTR` is not a terminal error. |
| `stdout.read_errno`, `stderr.read_errno` | Optional terminal read errors, excluding the existing retryable `EINTR`/`EAGAIN` cases. Retain each stream independently if both fail in one poll iteration. |
| `stdout.poll_revents`, `stderr.poll_revents` | Optional actual flag mask when the existing stream-error branch handles `POLLERR`/`POLLNVAL`. Preserve its priority relative to `POLLIN`/`POLLHUP`. Do not turn the aggregate's synthetic `EIO` into a native syscall errno. |
| `clock_fault` | Optional nonzero numeric `PW_TIME_REASON_*` reason from the failed collection sample/arithmetic. It is a local fault, not errno. The existing first-fault account remains separate. |

All errors above are bounded scalar observations, not an unbounded event log.
`leader_exit_and_eof` requires all three positive observations and no terminal
collection error/fault. A deadline may coexist with an already observed leader
exit or either EOF. A later successful reap must not change the stop reason.
Output bytes and existing truncation behavior stay unchanged; EOF does not mean
every emitted byte fit in the capture buffer.

### Cleanup section: requests and native returns

Here cleanup records process-termination requests only. Existing descriptor
closes and spawn-handle destruction keep their current behavior; this object
does not claim their success or provide a complete resource-cleanup account.

`cleanup.state` is required and is one of:

- `not_requested`: this completed observation path made no termination request;
- `ownership_unconfirmed`: cleanup was indicated but the existing ownership
  guard withheld signalling;
- `requested`: the worker called the group signal operation.

For `requested`, include `group_request: { target, signal, rc, errno? }` from
the actual `kill` arguments and return, with the signed native target (negative
PGID), signal number and immediate saved errno on failure. Retain `rc: -1` /
`ESRCH` exactly; it is distinct from `rc: 0`. Neither is a verified descendant
absence observation. The existing aggregate treatment of `ESRCH` stays unchanged.

If the current fallback branch runs, include a separate `leader_fallback` with
the same fields and positive leader target. Preserve both failed group and
fallback results; a successful fallback cannot replace the group result or
prove group cleanup. A completed record with no fallback member establishes
that this path made no fallback call. A missing entire exec object establishes
no such negative fact. Errno is omitted/null on successful calls, never copied
from a stale thread-local value. Do not retry or add a call to improve a record.

### Reap section: the final wait observation

`reap.stop_reason` records the branch ending the existing loop: `reaped`,
`wait_error`, `ownership_unconfirmed`, `group_request_failed`, `clock_fault`
or `deadline`. Preserve the loop's current branch order.

Include `last_wait: { rc, errno?, status? }` for the final `waitpid(... WNOHANG)`
call. Its return is the leader PID, zero or -1. Save errno only for -1, including
an unrecovered final `EINTR`; zero is a pending observation without errno.
Include the raw wait status word only when that call returned the owned leader.
Decode the existing child exit/signal fields from that same status. Never
publish zero-initialized status storage after a pending or failed wait.

Keep optional `reap.clock_fault` independently of the stop reason. A clock
sample before the immediate wait can fail even when that wait successfully
reaps the child: record both the fault and the actual status, preserving the
existing aggregate failure. A native wait error and a clock fault may also
coexist. A reap-grace deadline is a local stop; do not report its synthesized
aggregate `ETIMEDOUT` as `last_wait.errno`. A native wait returning that errno is
instead a `wait_error`. A final interrupted wait can coexist with a later local
stop. Earlier recovered interruptions are not an event history in this record.

There is no `cleanup_complete`, `group_absent` or descendant-status field. The
reap section concerns the owned leader only. Its observed signal does not
identify the sender merely because a matching cleanup request exists.

## Implementation boundaries

### 1. Record native boundaries without changing control flow

Keep `attempt_exec_spawn` as the owner. Introduce fixed local/slot storage and
small recording helpers only where they remove repetition; do not build a new
supervisor abstraction. Capture each relevant native return and errno before
another call or formatting can overwrite it. Record actual signal targets,
stream identity and wait returns, rather than filling them from desired results.

Freeze the collection account before cleanup. Capture group and fallback
returns independently. Keep the final reap return, meaningful status word and
its stop branch. Set the exec payload's validity marker only once its complete
account is assembled, before `run_attempt` publishes the existing slot completion.
Initialize the marker explicitly so no pre-spawn return exposes an empty object.

Preserve all existing aggregate assignments and their precedence, including a
collection error taking precedence over a cleanup error, and local faults
contributing no fabricated errno. The new per-stream facts may preserve errors
the old aggregate necessarily selects between. Do not change the selection to
match a preferred new field. Diagnostic prose remains supplementary.

### 2. Extend the fixed slot and host decoder

Allocate the fixed payload and validity marker from reserved space at the end
of [pw_shm_slot_t](pw_probe_runner_abi.h). Preserve existing field offsets,
slot size, region size, bootstrap offsets and output capacities. Use explicit
integer enums/presence flags; zero-initialized storage is not an observed
successful call. No post-apply allocation or new reporting channel is needed.

Update `PWShmLayout` and `CWorkerSlotResult` in
[CWorker.swift](../../../runner/Sources/PWRunnerCore/CWorker.swift), the compiled
[ABI printer and checker](../../../tests/suites/runner_abi_layout/README.md),
and the reviewed layout golden. If another accepted change has consumed reserved
space first, use the current layout and regenerate the agreement; do not overlap
payloads or copy stale offsets from this baseline. The existing slot has ample
reserved space; enlarging its capacity is outside this plan.

Read the payload only after the existing acquire-load observes slot completion,
for a host-selected exec slot with a valid marker. Do not inspect its bytes to
salvage an interrupted result. Unknown/malformed present codes or combinations
must reach the existing reporting-integrity failure path, not silently become
absence or a clean default. Map the new value without changing the old outcome
or comparison builders.

### 3. Carry and validate the optional facts together

Add bounded Codable evidence types and the optional attempt property in
[PWRunnerAPI.swift](../../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift),
including initialization, coding keys, encoding and decoding. Add ordinary-reply
integrity checks and independent validation in
[consumer.py](../../../tests/lib/consumer.py) and the Rust admitted-reply
evidence checks in [disposition.rs](../../../controller/src/disposition.rs).
Reuse existing malformed/reporting-failure handling and raw-payload retention;
do not introduce a second attempt classifier.

Validate required types, native integer ranges, conditional fields and the
facts' mutual consistency when the object is present. In particular: a published
worker exec and positive child PID support its presence; group and fallback
targets/signals match their native roles; fallback requires a failed group
request other than `ESRCH`; `reaped` and meaningful wait status require the actual
leader return; decoded legacy status must match that word; EOF and cleanup
cannot substitute for a leader return. Allow collection failure with a clean
leader exit, collection success with a reap fault, and multiple independent
errors. Validate numeric clock reasons as bounded nonzero codes and retain
unfamiliar reasons without inventing an interpretation.

Do not make the object mandatory based on source identity or successful exec.
Keep older valid documents without it valid. A degraded reply may retain
diagnostic evidence under its existing rules but still withholds comparisons;
the new object cannot restore claims the reporting-failure path withheld.

Populate every optional branch in the owning shape fixtures, review the
generated `response_shape.json` candidate, and extend typed malformed-input
fixtures and independent reader controls. Check the largest valid reply with
the new object on every exec slot using the existing maximum-reply owners;
do not quietly increase transport limits to accommodate it.

This is an optional additive response field with unchanged legacy meanings and
absence-as-unknown. Under [CONTRACT.md](../../../docs/CONTRACT.md#when-a-number-moves),
keep request, response and envelope numbers unchanged. The shared layout does
change: regenerate source identity and review compiled C/Swift agreement.
Making metadata mandatory, changing `rc` semantics or introducing a new
completion requirement would require a separate contract decision.

## Verification and acceptance

Extend the production-source native-call controls in
[exec_control.c](../../../tests/fixtures/worker_lifecycle/exec_control.c).
Their independent call ledger must capture actual arguments, return values,
meaningful errno and order; assertions must not derive their expected facts
from the new payload. Keep real process/liveness checks in
[runner_exec_lifecycle](../../../tests/suites/runner_exec_lifecycle/README.md).

| Control | Required independent distinction |
| --- | --- |
| Ordinary completion | Leader exit and both EOFs observed; no signal call; confirmed reap. Legacy status/output unchanged. |
| EOF with a live leader; exited leader with an open stream | Neither observation alone ends ordinary collection. Preserve the actual deadline/stop and pre-cleanup snapshot even after cleanup reaps the leader. |
| Clean leader exit with failed group cleanup | Independently return leader exit zero, group failure and a separate fallback result. Retain all facts beside aggregate `exec_failed`; cleanup cannot overwrite leader status. |
| Group result variants | Distinguish no request, return zero, `ESRCH`, other failures, and ownership loss with no signal. Check actual negative group target and positive fallback target; preserve fallback success and failure. |
| Successful signal without reap | Force pending/error waits; retain the successful signal without fabricating status or cleanup completion. |
| Reap faults and stops | Cover genuine wait error, native `ETIMEDOUT`, locally expired grace, final `EINTR`, and clock fault with both immediate successful reap and unconfirmed reap. Keep native and local facts distinct. |
| Collection faults | Cover waitid/poll/read failures, error revents, both streams failing in one iteration, and collection clock/arithmetic faults. Verify stream identity, retained combined facts and unchanged aggregate error precedence. |
| Publication | Kill after payload construction but before slot publication. Host withholds the entire exec payload and old unpublished outputs. Completed pre-spawn failures, synthetic and non-exec results omit it. |
| Ordinary survivor | Existing closed-stream/leader-exit live fixture still observes the same-group descendant after successful later work and worker exit. The new record reports no cleanup request and makes no absence claim. Fixture cleanup remains independently owned. |
| Worker death during exec | Existing live control still observes survivors; no completed slot means no recovered exec object. Keep prior results and later-effect absence. Retain an independent final fixture cleanup/exit receipt. |
| Transport and readers | Exercise production C-to-Swift decoding and encoded CLI replies, not only constructed Swift objects. Accept old replies without metadata; reject impossible present combinations and wrong types/ranges in each owning reader. Preserve comparison and run/disposition behavior. |

Add deterministic mutations that make the unchanged assertions fail: overwrite
the collection snapshot from final reap; conflate `ESRCH` with successful kill;
substitute the group result for fallback; publish status after a non-child wait
return; turn revents or a local deadline into native errno; decode an unpublished
payload; infer cleanup absence from missing metadata. Test a reader control that
accepts successful signalling plus unconfirmed reap, so overstrict validation
cannot pass by rejecting every difficult combination.

Use the existing native control ledger to pin signal/wait/clock call order and
counts across the refactor. Preserve current retry/deadline controls; no new
sample, poll, wait or signal may be introduced just to populate the record.
Live tests require independently identified peer exits or responsiveness before
fixture cleanup; neither JSON nor a successful signal is its own effect oracle.
Do not require descendant exit before a later step: that is not this contract.

## Documentation, build and completion

Update the exec field account in [PolicyWitness.md](../../../docs/PolicyWitness.md),
the [evidence contract](../../../tests/FAILURE-PROPAGATION-CONTRACT.md), runner
reference and affected source comments. State publication completion, aggregate
attempt status, spawn observation, leader status and cleanup effort separately.
Explain absent metadata and the lack of a total cleanup or descendant-isolation
guarantee. Do not describe a post-spawn permission-shaped cleanup failure as
failed sandbox admission.

Update [architecture.json](../../../docs/architecture.json) and regenerate the
worker/architecture accounts. Correct the exec Known gap and group-resource
prose: ordinary completion and worker death can leave same-group survivors,
in addition to descendants escaping the group. Preserve graph IDs; no graph
schema redesign is part of this change. Update limits inputs only where the
owning evidence paths or verified representation require it; native capacities
and budgets remain unchanged.

Regenerate worker identity and affected owning documentation inputs with
`docs/generate_worker_identity.py`, `docs/generate_architecture.py` and, where
affected, `docs/generate_limits.py`. Review generated output, C/Swift layout and
response shape. New native source files require their Meson target update.

Build through the [signed pipeline](../../../docs/BUILD.md). During development,
select the affected worker harness, runner unit, ABI, reader/failure-boundary,
source-drift and exec lifecycle cases. Final acceptance uses the signed
candidate's full default battery plus the opt-in normal-completion survivor and
maximum-exec controls, with fresh output and inspected selections:

```sh
PW_TEST_OUT_DIR=tests/out/runs/exec-evidence-default tests/run.sh
PW_TEST_OUT_DIR=tests/out/runs/exec-evidence-extra tests/run.sh \
  --case runner_exec_lifecycle/closed_streams_leader_exit \
  --case witness_contract/max_exec_steps_spawn
```

Select any newly registered opt-in mutations explicitly. The worker release
wait, host release store and eligibility predicate are unchanged; if an
implementation touches them, run the mandatory ordering mutation control as
required by repository guidance. Follow [test guidance](../../../tests/AGENTS.md)
for locking, native-harness escalation, exact source/app provenance, evidence
retention and applicability of any reused results. Preserve failures and unrun
cases honestly.

Completion requires independent separation controls, publication gating,
preserved native call policy and legacy classifications, compatible absence
handling, integrated transport/reader acceptance, reviewed generated contracts
and passing signed acceptance. Record acceptance and residual lifetime limits
in an associated record. No broader supervision decision is required to finish
this refactor.
