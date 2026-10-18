# Terminal publication and worker lifetime investigation

Source: `51487f74da15de196d44c4ac571c7b322a2fe83b` (2026-10-18).
Scope: WA-04, the terminal-publication daughter plan, and the lifecycle side of
WA-08. Production sources have not been changed. The historical orphan is not
used as evidence of this revision's execution or of its instruction location.

## Recommendation ready for decision

Replace the worker's post-terminal wait with ordinary terminal cleanup,
release publication where that path already publishes `done`, and `_exit(0)`.
Existing ordinary returns from main remain returns with the same exit codes
and publications. Keep host cancellation, grace,
termination, reap observation, and final acquire collection. Accompany the
worker change with final acknowledgement reconciliation after a confirmed
reap under unbroken ownership; immediate worker exit otherwise exposes a
real host sampling race that loses valid ordering credit.

No worker action after `done` is needed to preserve its evidence. The host
owns another mapping until after all decoding. Normal completion has already
finished every phase; a preparation/application failure never authorizes
queries; a proceed refusal terminates that phase without acknowledgement or
attempts. The host must nevertheless observe actual exit independently of
publication. `done` remains a terminal report marker, not successful policy
application, successful operations, confirmed exit, or descendant cleanup.

This is an observable lifetime change. A proceed refusal can now remove the
target while an already-running validator collection is still asking queries.
Later native records can differ or become unavailable. Accept this consequence
explicitly: preserve the records actually collected and withhold the refused
phase's ordering claim/release. Keeping a refused target alive merely to
continue that collection is not a stated capability. If the desired product
instead requires that capability, that is a reason to retain a specifically
bounded diagnostic lifetime, not to retain an unbounded post-done spin by default.

The associated [daughter plan](../../controller/tools/pw_probe_runner/TERMINAL-PUBLICATION-PLAN.md)
links the coordinator's decision brief and separate token-cleanup investigation.

## Current terminal state model

Source locations below name lines in the source revision above.

| Departure | Publications and native status to preserve | Current lifetime |
| --- | --- | --- |
| `--version`, invalid arguments, mapping failure, ABI refusal | Exit 0/2/3/4 respectively; no invented application or terminal publication | Ordinary return; worker has not entered post-apply execution |
| Header/prepared/step/phase/parameter/expected-length refusal | Published failure when the ABI is usable; exits 5/6/9/8/10; no `done`, application, or fabricated `apply_rc` | Ordinary return |
| Timing setup refusal | Operation 12 failure; exit 12, no policy read, application, or `done` | Ordinary return |
| Policy input read/overflow, EOF-length mismatch, embedded NUL | Independent failure; read/overflow exit 7, length exit 11, NUL exit 9; EOF receipt only when actually reached; no `done` | Ordinary return |
| Params allocation/set/encoding or compilation failure | Operation-specific evidence and diagnostic, status word -1, `done=1`, exit 0 | Spin until host exit request |
| Apply failure | Actual native return/errno and failure; `applied=0`, `done=1`, exit 0 | Spin until host exit request |
| Proceed timing/future-release/expiry refusal | Failure and diagnostic, `applied=1`, `done=1`; no acknowledgement/actions for refused phase, exit 0 | Spin until host exit request |
| Cancellation observed at proceed cancellation load | No synthetic failure or `done`; retain all earlier publications, exit 0 | Immediate `_exit(0)` already |
| Normal completion | Each slot and phase completed, finished progress, `done=1`, exit 0 | Spin until host exit request |
| Fatal interruption or nonreturning native call | Whatever was published survives; no synthetic terminal publication or native result | Only independently observed status/host supervision can establish disposition |

These paths are in [worker main](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
at lines 1557–1945, with proceed refusal/cancellation at 1487–1552. The current
post-done loop at 1464–1475 repeatedly loads `exit_requested`, uses CPU relax
instructions, and calls `_exit(0)` only after the flag. It has no worker-side
time bound or parent-loss input. All paths that call it already choose exit 0;
that choice does not turn their published failures into success.

The post-loop token erase at 1915 precedes the post-apply hang and signal test
seams at 1925–1940. Preserve that timing even if erasure is also centralized.
The separate token investigation linked from the daughter plan covers the
accepted-channel guard, early returns and alternatives. A terminal helper
must accept the existing publication/exit decision; it must not convert every
departure into `done=1` or rewrite distinct early refusal exit codes.

## Why a living worker is unnecessary for final evidence

The host unlinks the shared object's name after opening it but retains its own
mapping and descriptor through decoding. Its `defer` unmaps/closes only when
`runCWorker` returns ([CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift),
lines 923–953). Worker exit therefore does not invalidate the host mapping.
Payloads are read only after their release/acquire publication markers.

Host cleanup records the actual polling stop, release-stores the exit request,
attempts grace/reaping and only then takes final acquired application, done,
phase and slot observations (lines 1346–1407). `collection_basis` records
whether a successful reap preceded those reads. A snapshot collected while
execution may continue retains immutable positive publications but cannot
establish terminal negative claims. Neither `waitpid` alone nor a shared
memory load alone substitutes for the other channel.

The published failure and classifier rules already separate these axes.
[CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
lines 1356–1454 prioritizes actual worker failure evidence, preserves sentinel
expiry, then checks missing publication, abnormal/unconfirmed status, host
termination requests and wait errors. It does **not** require
`poll_stop_reason=done` for success. Thus `child_reaped` beside a final
`done=true`, successful application, complete slots and clean exit is valid.
An already-observed deadline remains `runner_timeout` even if final acquisition
later sees completion; a reported worker failure retains its own precedence.

The compiled-profile receipt similarly does not need a living worker:
[CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift) lines 556–595
requires successful application, `done`, clean observed exit, capture
publication and all identity/integrity checks. The receive buffer is host
memory. Removing the wait changes no receipt condition.

The wire contract already defines `done_observed` as final acquisition,
`poll_stop_reason` as the actual earlier stop, `exit_requested` as the store
having occurred rather than an acknowledged instruction, and `reaped` as a
wait returning this PID. See the
[host observations](../../tests/FAILURE-PROPAGATION-CONTRACT.md#host-observations)
and [disposition contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-disposition-record).
Retain the host store even after spontaneous completion; it remains useful
for live cancellation and keeping its current public meaning requires no new
causal claim. Do not rename `child_reaped` to `done` after discovering a late
publication, or call the exit request the cause of a voluntary exit.

## The host race that must be fixed with immediate exit

At [CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift) lines
1312–1330 the host samples acknowledgements, samples `done`, and later calls
nonblocking wait. A worker can acknowledge, complete and publish `done`
between the samples and the successful reap. The host correctly stops at
`child_reaped` and its final acquire retains all publications. But final
acquisition only copies `acknowledged`; it never revisits
`ownershipEstablished`. The already-reaped child skips the grace loop, where
that credit would ordinarily have been established.

The proposed reconciliation is deliberately small: after cleanup, when
`process.status != nil`, call the existing `observeAcknowledgement()` before
final snapshot assembly. That helper credits only a host-recorded release,
an acquired acknowledgement and still-unbroken ownership (lines 1216–1223).
No later reap may repair an earlier ownership fault. Already established
earlier phases remain established after a later fault.

This is consistent with existing semantics: the grace loop already calls
`observeAcknowledgement()` **after** a successful reap at line 1378. Ownership
through acknowledgement does not require the observation itself to precede
reaping. The mapping belongs to this execution, the acknowledgement preceded
its exit, and a successful reap of the owned child closes its lifetime. The
final step must retain this distinction from a fresh liveness check or another
validator call against a potentially reused PID.

There is also no new cancellation violation to infer. The worker samples
cancellation before acknowledging; a later host store can lose that race.
Keep the actual deadline/stop and publication observations. The existing
sample-precedence controls in
[proceed_control.c](../../tests/fixtures/worker_lifecycle/proceed_control.c)
cover that decision ordering. The proposed change does not move the worker's
release or cancellation load, but it does affect the host evidence supporting
query eligibility and therefore requires the ordering mutation control during
production validation.

## Bounded investigation experiment

Command:

```sh
tests/lib/checkout_lock.sh -- /usr/bin/python3 -B records/worker-terminal-lifetime/run_experiment.py
```

The [script](run_experiment.py), [ABI fixture](experiment-fixture.c) and
[Swift driver](experiment-driver.swift) are retained. The script copies the
host sources to fresh `/private/tmp` directories and builds two isolated
Swift executables. The candidate differs at one line, adding
`if process.status != nil { observeAcknowledgement() }` before collection-basis
recording. No production source, shipped app, generated identity, catalog or
permanent fixture was edited. The copied host and fixture use the current
generated ABI values; this is not an identity-verified production build.

The fixture waits for host release and an independently controlled gate, then
publishes acknowledgement, slot/phase completion and done and immediately
exits 0 without consulting `exit_requested`. The existing injectable native
wait boundary opens the gate only after the host's preceding acknowledgement
and done samples, and returns a genuine native reap. In the negative case a
poll wait first reports EIO, and only the subsequent cleanup wait opens the
gate and performs a genuine reap. The driver has independent native cleanup,
the gate wait has a two-second watchdog, and the fixture has a ten-second
alarm. The script forwards checkout-lock descriptors to child commands.

Initial execution failed during Swift manifest compilation because the
automation sandbox refused the module-cache write. The unchanged command was
rerun once with escalation as required by repository guidance. The
[original build refusal](experiment-20261018T171011.803258Z/baseline-build.stderr)
is preserved separately. The escalated run completed all four controls:

| Host copy / schedule | Final done, complete slot, clean reap | Actual stop retained | Lifetime credit / constructed comparison | Classification without required validator |
| --- | --- | --- | --- | --- |
| Baseline / publication between samples and reap | Yes | `child_reaped` | false / `unestablished` | `ok` |
| Candidate / same race | Yes | `child_reaped` | true / `query_first` | `ok` |
| Baseline / ownership fault before publication | Yes | `wait_error`, EIO retained | false / `unestablished` | `runner_failed` |
| Candidate / same ownership fault | Yes | `wait_error`, EIO retained | false / `unestablished` | `runner_failed` |

All four recorded `after_confirmed_reap`. No host kill or watchdog fired.
All independent post-driver waits returned ECHILD, observing that the driver
had already reaped its child. Raw
[baseline](experiment-20261018T171602.901016Z/baseline.jsonl) and
[candidate](experiment-20261018T171602.901016Z/candidate.jsonl) JSON,
[source hashes](experiment-20261018T171602.901016Z/source.json),
[commands](experiment-20261018T171602.901016Z/commands.json), compiler/run
stdout/stderr and the
[result](experiment-20261018T171602.901016Z/result.json) are retained.
Evidence under this records directory is not gitignored; temporary compiled
copies named by the metadata are local, disposable equipment, not the sole
copy of the experiment or its results.

These are investigation controls outside the registered battery. The fixture
does not apply a sandbox or perform the represented file attempt. Its
validator record is explicitly constructed to exercise production order
projection. The experiment establishes the host race, payload retention,
status/stop preservation, proposed reconciliation, and the negative ownership
case. It establishes no real query result, kernel policy behavior, signed-app
acceptance, token cleanup, native production immediate-exit behavior, or
host-loss containment. No registered acceptance case is claimed as run.

## Observable effects

**Normal finish.** All phases are finished before terminal publication, so
there is no remaining scheduled validator collection that needs a live PID.
The host may observe `done` first or reap first, and may enter or skip grace.
Both are valid observations; tests must not demand one scheduling outcome.

**Preparation/application refusal.** A new EOF can reach the ready pipe sooner
than its current one-second allowance: the existing compile-failure spin
retains its write descriptor without sending readiness. This changes observed
readiness stop/elapsed time, not the compiler failure or the need to retain it
([CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift), 1173–1198).

**Proceed refusal during collection.** The synchronous phase callback can
outlast the worker's local proceed allowance. Immediate exit can then race
later queries already being collected. At callback return the host already
closes the collection, checks wait status and rechecks the phase before any
release (lines 1287–1308); a reaped child gets no release and no next query
phase. Records received before/after death remain actual observations but
the missing acknowledgement withholds `query_first`. The contract explicitly
allows death/expiry during collection and preserves received records. Existing
[OrderingTests](../../runner/Tests/PWRunnerCoreTests/OrderingTests.swift),
199–234, query across observed target death without asserting a specific
native result. Immediate exit trades a possible extra live diagnostic window
for terminating the refused execution; this is an accepted cost to decide,
not an invariant failure.

Immediate exit adds no new exit primitive: `_exit(0)` is already the final
operation of the current spin and the proceed-cancellation path. That is
source support for a small change, not empirical acceptance under every
profile. Existing restrictive-profile controls can establish the production
candidate's behavior after implementation.

## Remaining limits and implementation boundary

This removes indefinite **waiting after terminal publication**. It also lets
a worker whose bounded proceed wait expires finish without its lost host
releasing it from a second unbounded wait. It does not bound native compile,
apply, attempt or exit internals, recover unpublished observations after fatal
termination, guarantee erasure under SIGKILL, reap a worker whose host is gone,
or contain/reap exec descendants. The host's blocking final wait after a
successful termination request remains; there is no new total lifecycle
deadline. Descendant cleanup is a separate exec-supervision decision.

Keep together in production: terminal worker departure, final host
acknowledgement reconciliation, removal of comments that infer no done from a
polling reap, and controls that distinguish terminal evidence from exit.
Ordinary accepted-token erasure is independently useful, but a common terminal
routine is a natural place to implement it with explicit preservation of
current failure codes, missing-publication meanings and earlier erasure.
The token investigation owns its boundary details.

The existing public fields can describe this model without changing their
reading rules. A source-identity regeneration is mandatory because worker/host
sources change. No request or envelope change is needed; no response bump
appears necessary if the current meanings are preserved under
[the version rules](../../docs/CONTRACT.md#when-a-number-moves). Revisit that
judgment if implementation changes a field's meaning rather than its observed
value. Review controller and Python readers/fixtures for accidental scheduling
assumptions and add the legitimate `child_reaped` plus done/clean-exit case.
Update the architecture/worker source manifest and regenerate its account,
plus runtime prose, limits and harness expectations, to describe actual exit.

Existing coverage establishes suitable regression starting points, not results
executed for this investigation. `runner_unit` has normal/restrictive-profile
driver paths, failures, phase ordering and the lost-ownership control
([OrderingTests.swift](../../runner/Tests/PWRunnerCoreTests/OrderingTests.swift),
280–312). Its real-worker late-done-during-grace control
([CWorkerTests.swift](../../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift),
380–424) pins deadline preservation. `runner_c_worker_harness` has early no-done
refusals, compile failure and proceed controls. Its `sigkill_fallback` and
`host_lost_while_waiting` expectations rely on withholding the exit request
from the spin, so they must be reworked; fallback kill still needs a genuine
stuck/nonterminal fixture.

Remaining implementation coverage includes the exact race as a maintained
control, restrictive-profile production exit without a request, host loss with
independent cleanup, refusal during ongoing collection, empty final phase,
compiled receipt, combined token cleanup and independent readers. The
coordinator's decision brief owns the consolidated implementation gate.
