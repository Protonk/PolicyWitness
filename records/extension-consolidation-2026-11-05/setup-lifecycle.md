# Draft setup, terminal boundary, lifecycle and erasure contract

Review proposal only, 2026-11-05. Baseline:
`4cd1d6c7f14e3ebacfd2dda219dda85967f64680`. This packet records source and
assertion inspection for Stages 1–2 of
[the associated plan](../../runner/EXTENSION-CONSOLIDATION-PLAN.md). No production
edit, build or live test was performed by this packet's author. The root
review packet owns candidate/equipment identity and any executed evidence.
The example JSON files below are constructed proposed records, not observations.

## Recommendation

Add one automatic `authority_setup` reply account with explicit host scopes
and one worker entry per actor. Use independent one-shot publications for
individual observations and a separate immutable setup decision. Required
apparatus failure takes a local terminal branch before policy processing.
Preserve valid late observations without reopening scheduling eligibility.

Accept a narrowly scoped `phases[].after_termination: {"actor_id":"issuer"}`
dependency. It asks for owned observation of termination after the source's
final visit, before dependent activation and collection. Abnormal termination
can satisfy this condition; clean completion is not the public condition.
Keep the exit status and how termination was observed. Host-induced departure
cannot make an unsatisfied dependency true.

## Baseline producer and reader trace

| Owner and source | Actual operations, publications and current limits |
| --- | --- |
| `prepare_authority`, [worker](../../controller/tools/pw_probe_runner/pw_probe_runner.c) | For actor mode, three independent `dlsym` calls, `setrlimit(RLIMIT_CORE)`, descriptor presence, `fstat`, `getpagesize`, size validation, `mmap`, `close`, header validation and private assignment snapshots. Core/fstat failures call bare `close`; mmap path calls substituted close; close failure/header rejection call `munmap`. Only `authority_status`, `authority_detail`, `native_symbols` survive. Primary returns/errno and cleanup returns are lost. There is no dedicated authority release publication. |
| `main`, same worker | Calls `prepare_authority` before parameter bounds, timing setup, policy read, params/compile/capture/application. Present failure returns from preparation into this flow; it does **not** exclude application. `actor_setup` publishes applied or unapplied only later. Generic failure is single-record storage, unsuitable for simultaneous setup and cleanup facts. |
| [AuthorityCustody](../../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | One host core-limit call per authority session. Creates every actor's authority object before launch, using `shm_open(O_EXCL)`, `shm_unlink`, CLOEXEC `fcntl`, `ftruncate`, `mmap`; initializes header/assignments. Creates one private anonymous mapping per issued token. Region setup currently collapses into a string; cleanup close/unmap returns are discarded. Construction maps all actor regions even if an earlier one failed; `setupFailure` picks one summary. |
| `ActorAuthorityRegion` / `TokenCustody`, same file | Descriptor lasts through spawn, mapping through final collection. Host clears published outbound bytes before acknowledgement; private custody clears at last declared transfer or teardown. Shared teardown erasure requires quiescence; private custody does not. `tearDown` discards mapping/descriptor ownership even if native cleanup fails; proposal must retain unresolved ownership rather than label this successful cleanup. |
| [ActorSession](../../runner/Sources/PWRunnerCore/ActorSession.swift) | Separately creates reporting apparatus. Duplicates authority descriptor with `F_DUPFD_CLOEXEC` minimum 64 and installs FD 5 through spawn actions. Original and duplicate references are distinct. Actor launch also relocates policy/evidence/ready sources; those existing observations remain outside the new authority-only inventory. `waitChild` records native child observations and breaks ownership on a terminal wait error. `requestExit` publishes cancellation; `finishCleanup` can SIGKILL and reap. Neither is a natural-termination gate. |
| [ActorScheduler](../../runner/Sources/PWRunnerCore/ActorScheduler.swift) | Authority preparation precedes all launches. Setup resolution precedes schedule traversal. Normal visits advance on completed phase without reap. Failed active visits establish quiescence or cancel. Final cleanup gathers output and recomputes `applicationCount` from an eligible late applied publication without changing `setupTimeout`. Current setup authority check is conditional on `actorSetup != 0`; terminal authority refusal needs its own branch. |
| [ABI](../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h), [Swift mirror](../../runner/Sources/PWRunnerCore/CWorker.swift) | Shared header 768 bytes; authority status/detail/symbols at 180/184/188; 16 phase records start at 192. Generic evidence header 64 bytes. Current Swift output reads authority fields without a dedicated authority publication. Authority bearer layout is separate: 1,152-byte header, 16,448-byte slots, 16,384-byte token capacity. |
| [Actor reply assembly](../../runner/Sources/PWRunnerCore/ActorOrchestration.swift) | Retains actor setup status/application count/subprocess but does not expose a full authority setup account. It derives inherited FD 5 from host region string `mapped`; future launch observations must use actual completed launch binding. |
| Independent readers | [Rust disposition](../../controller/src/disposition.rs), [Python consumer](../../tests/lib/consumer.py), [extension reader](../../tests/lib/extension_evidence.py), [lifecycle oracle](../../tests/lib/lifecycle_oracle.py) currently relate action eligibility to established actor setup. Preserve that rule for requested actions while admitting separately published setup/cleanup facts. Rust/Python also already allow application_count=1 beside setup_timeout. Swift reply invariants and shape/size fixtures are additional consumers, not substitutes for independent readers. |

`getpagesize` has no errno failure contract here. `dlsym` availability is a
pointer/non-null observation, not a native sandbox operation and not a numeric
syscall result. `mmap` success is MAP_FAILED inequality, not a native integer
return of zero. `posix_spawn_file_actions_adddup2` reports its error in the
return value; do not copy ambient errno. Byte clearing returns no status.

## Proposed shape and ownership

Use `data.runner_result.authority_setup` with these fixed families:

```text
authority_setup
  host
    run {disposition, primary_operation?, operations[]}
    regions[] {actor_id, actor_index, disposition, primary_operation?, operations[], ownership}
    custody[] {token_ref, token_index, disposition, primary_operation?, operations[], ownership}
  workers[] {actor_id, actor_index, required, publication, disposition?, primary_operation?, operations[], ownership}
```

`run` exists once. `regions` has at most eight entries in admitted actor order;
`custody` at most 32 in token-table order; `workers` exactly one entry per admitted
actor, even for unlaunched actors (publication `not_observed`, empty observations).
When the actor specimen has no authority session, the host run disposition is
`not_required` and its region/custody arrays are empty. The workers still report
their independent symbol/core-limit attempts. Ordinary single-worker execution
does not acquire actor authority apparatus and omits this actor account.
An internal resolved-plan inconsistency before preparation yields host run
`not_attempted`, empty host arrays and no worker observations; the separately
owned preparation_failure supplies stage `resolved_plan` and code
`inconsistent_assignment`. Do not reconstruct invalid associations for this
account. The version proposal is request 6, response 26, envelope 11, protocol 3.

An operation record has closed vocabulary: `slot`, `operation`, `role`
(`setup` or `cleanup`), `state` (`succeeded`, `failed`, `accepted`, `rejected`,
`available`, `unavailable`, `performed`, `not_attempted`), optional
`native_kind`, `native_rc`, `errno`, `detail`, `value`. Integer-returning calls
retain the actual signed return. Only failure for errno-reporting calls has
`errno`; zero errno, if actually saved on a failing call, remains zero. Mapping
calls use `native_kind: "mapping"` and state succeeded/failed, without a
fabricated success rc or pointer address. Symbol calls use `symbol` kind and
available/unavailable state, with no errno. Validation uses `validation` kind,
accepted/rejected and finite detail codes. Clear uses `memory` kind, performed,
the byte capacity/count and no native return. Missing operations are
unobserved, never successful or unattempted by inference. A producer can publish
explicit not_attempted only after it irrevocably skips that operation.

The container scopes actor/token identity. No operation emits bearer bytes,
addresses, arbitrary text or repeated actor identifiers. Host native observations
do not require worker publication. `primary_operation` names the causal setup
refusal cell, not a replacement for the other cells. Cleanup never overwrites
the original failure. A successful inspection followed by rejected validation
retains two records, without fabricating a failed inspection or errno.

Worker `publication` is `observed` only after acquire of its setup decision;
it can be `not_observed` beside individually published operations. Proposed
decision dispositions are `ready`, `not_required`, `terminal_required_failure`.
Host `disposition` is independently `ready`, `failed`, `not_required` or
`not_attempted`. Actor `setup_status` remains the scheduler's decision; add
`authority_setup_failed` to distinguish a timely terminal authority refusal.
Late terminal refusal remains a fact beside `setup_timeout`.

`ownership` retains separate object-name linkage, descriptor reference,
mapping reference, shared erasure and private custody states where applicable.
Use finite states `not_acquired`, `held`, `released`, `unresolved` for references,
and `not_present`, `performed`, `withheld_not_quiescent`, `unobserved` for erasure.
These are producer summaries derived from cells and lifecycle; readers must
validate their support. No `released` on failed close/unmap. A failed close
can leave the exact descriptor's state unresolved; never blindly retry an
ambiguous close or close an integer that may have been reused. A failed unlink
retains the owned name for controlled recovery; O_EXCL failure confers no
ownership of the preexisting name. Failed munmap retains the actual address and
extent privately for cleanup ownership; those addresses never enter replies.
If an acquired POSIX name remains linked, retain a bounded cleanup reference
(kind `posix_shm_name`, original name at most 31 ASCII bytes, successful creation
observation, host PID/session nonce, `recovery_state: "unresolved_manual"`).
Preserve this receipt after host exit as an unresolved resource account. The
name, successful earlier creation and session association do **not** establish
the identity of the object currently bound to that name: another process may
have unlinked the original and reused the name. This proposal supplies no
post-exit identity-verification protocol and authorizes **no automatic unlink**
from the receipt. Manual recovery must independently establish current identity
and ownership before acting; otherwise retain unresolved status. Do not claim
settlement from matching a name/session or from a subsequent successful unlink
of an unverified object. Do not attach a cleanup reference to an O_EXCL failure.
Worker ownership
states describe its last eligible cleanup publication; a subsequent reap is
separate evidence and does not rewrite a failed munmap or close into success.

New structured Swift types belong in `PWRunnerAuthoritySetup.swift`, compiled
by host/client, Meson and SwiftPM. Host collection belongs in AuthorityCustody
and the authority-specific ActorSession acquisition/cleanup paths. `CWorkerOutput`
and ActorSession own decoding worker cells; ActorOrchestration owns one final
assembly after custody teardown (currently outcomes expose transfers/custody
only). Update PWRunnerReply/PWRunnerActors checks, CWorkerDisposition and the
three independent reader families together. The final reply must copy host
cleanup observations **after** explicit teardown, never depend on deinit to
produce evidence after encoding.

## Exact bounded storage proposal

Append an 832-byte setup trailer after the existing evidence header and diagnostic
buffer in the reporting region. Do not store evidence in the bearer region.
Keep existing offsets except the total reporting-region length; declaration
field retirement may separately change the header under the coordinated ABI
revision. Define `PW_SHM_AUTHORITY_SETUP_BYTES=832`,
`PW_AUTHORITY_SETUP_OPERATION_CAPACITY=16`,
`PW_AUTHORITY_SETUP_OPERATION_BYTES=48` in C and independently in Swift.

The trailer header is exactly 64 bytes (8-byte aligned): decision publication
atomic u32 at 0; disposition u32 at 4; primary slot-plus-one u32 at 8;
applicability/required host input u32 at 12; actor index u32 at 16;
reserved u32 at 20; 40 reserved bytes at 24. No pointers or variable-length
strings. Cells start at 64 and each has:

| Offset | Field |
| --- | --- |
| 0 | atomic u32 `published` (0/1) |
| 4 | u32 `native_kind` |
| 8 | u32 `operation` (slot-specific enum) |
| 12 | u32 `state` |
| 16 | i64 `native_rc` |
| 24 | i32 `saved_errno` |
| 28 | u32 flags: bit 0 rc present, bit 1 errno present, bit 2 value present, bit 3 cleanup role |
| 32 | u32 finite `detail` |
| 36 | reserved u32 zero |
| 40 | u64 `value` (stage-specific size/count; never an address) |

Worker slots are fixed by operation, not a growing log:
0 issue symbol; 1 consume symbol; 2 release symbol; 3 core limit;
4 descriptor presence; 5 fstat; 6 page-size observation; 7 object-size validation;
8 authority mmap; 9 descriptor close; 10 header/binding validation;
11 terminal owned-inbound erasure summary; 12 rejected-mapping munmap;
13–15 reserved. Descriptor close occurs at most once on a branch, whether
its causal role is setup descriptor closure after mapping or cleanup after an
earlier refusal. Bit 3 explicitly records that role in the cell: set means
cleanup, clear means setup. The worker decides and writes it before publishing
the cell. After acquiring that cell, the reader decodes its role without reading
an unpublished setup decision or primary slot. In particular, closure after
mapping is setup whether it succeeds or becomes the primary failure; closure
after a failed fstat is cleanup. JSON exposes the role directly. Bits 4–31 and
the reserved word must be zero; unknown flags are integrity failures. Validate
the role against the slot's allowed roles (both for descriptor-close; fixed
setup for acquisition/symbol/validation slots and fixed cleanup for terminal
erase/rejected-mapping unmap). The erasure summary is published once at terminal
cleanup, even though operation-specific erasure can have occurred earlier;
it is not a cumulative log of each consume.

Host scopes have bounded slots too:

| Scope | Capacity | Assigned operations |
| --- | --- | --- |
| Run | 4 | 0 core limit; 1–3 reserved |
| Each authority region | 16 | 0 shm_open; 1 unlink; 2 FD_CLOEXEC; 3 ftruncate; 4 mmap; 5 header initialization; 6 F_DUPFD_CLOEXEC authority launch source; 7 spawn adddup2 authority FD; 8 close launch duplicate; 9 close original descriptor; 10 final shared clear; 11 munmap; 12–15 reserved |
| Each private custody mapping | 4 | 0 mmap; 1 final erase; 2 munmap; 3 reserved |

No retries of setup acquisition enter these arrays. Recovery attempts belong
to retained cleanup ownership and a separate bounded recovery receipt, not an
unbounded append to the run result. Memory initialization records execution,
not an invented system-call return. Custody final erase is idempotent; earlier
last-use erasure remains the existing transfer/custody fact. Existing generic
host launch failure accounts still cover file-action init, process attributes,
evidence mapping/pipes and actual posix_spawn; avoid widening this authority
inventory into a duplicate launch audit.

Maximum cells: host `4 + 8*16 + 32*4 = 260`; worker `8*16 = 128`; total 388.
Maximum worker trailer storage across eight evidence regions: 6,656 bytes,
independent of 256 actions. Swift host objects are not promised to occupy
48 bytes per record: the storage proof is bounded counts and scalars, not a
Swift heap footprint claim. The constructed encoded-reply budget must add
388 worst-case operation records plus bounded containers/ownership fields
without subtracting mutually exclusive combinations. All new fixed vocabulary
strings have an explicit 64-byte ASCII ceiling; admitted identifiers retain
63-byte UTF-8 cap. Record keys and arrays need policies in reply-size controls.
Use `limits.json` for these capacities and value checks independent in C,
Swift, Rust and Python; they must not import the manifest as their oracle.

Reserve **524,288 encoded JSON bytes** for this entire authority_setup component
in the conservative reply budget, independently of native ABI storage. A
reviewable overbound is `388*1024 + 49*2048 + 16384 = 514048` bytes: 1,024 per
operation, 2,048 for the non-operation portion of each of 49 scopes (one host
run, eight host regions, 32 custody entries, eight workers), plus 16,384 for
root/container punctuation and keys. Each operation has at most ten fields,
fixed ASCII values at most 64 bytes and integers at most 20 decimal bytes;
it has no free text. Each scope has at most one 63-byte identifier, charged
as 378 bytes for worst-case JSON escaping, bounded ownership fields and scalar
metadata. The 2,048-byte allowance excludes its already-counted operations.
It also covers a 31-byte cleanup name, conservatively charged as 186 escaped
bytes, its two at-most-20-byte numeric ownership association fields and fixed
`unresolved_manual` state. The explicit cell role uses existing flag storage
and the already-budgeted JSON role field: the trailer remains 832 bytes and
the 514,048-byte calculated overbound remains below the 524,288-byte reserve.
Require independently constructed maximum-capacity production-encoder fixtures
and an independent calculation of these per-record policies. This deliberately
counts mutually exclusive failures/successes and is not a reachable-output or
process-memory claim. No runtime truncation is allowed: excess cells, reserved
slots written, unknown flags/enums, duplicate slots or bound overflow are
explicit evidence integrity failures, with unsafe claims withheld under the
existing reporting-failure path. The component reserve does not replace the
whole-reply transport bound, which must be recomputed with all other components.

Review sizeof/offsetof output and layout golden with the owning ABI suite;
regenerate worker identity after changing ABI and producer/reader source inputs.
The authority-region identity still follows the generated worker identity,
although its bearer slot structure remains unchanged. No extra token storage
or pre-sandbox target acquisition is introduced.

## Publication, terminal control flow and applicability

Each operation cell is filled once and release-published once after saving its
native return and errno immediately. Host acquire-checks each cell before
reading payload, even after reap. A valid worker identity and actor association
are required; reading bytes after exit does not invent publication. An interrupted
call is unobserved in this account unless the existing progress/call-entry owner
separately reports entry. No pending-cell payload is eligible.

The required bit comes from the resolved launch record's assigned authority
region, not merely `fd >= 0`. Preserve present provisioning: an authority plan
creates a region for every actor, including an actor with zero authority actions
in that mixed specimen. These assigned regions are required. In a specimen
with no authority plan, actors have no assigned region: descriptor absence is
not-required, while symbols/core-limit are still attempted. This is an exact,
minimal-change rule; selective region provisioning is not part of consolidation.
A nonrequired core-limit failure is reported but does not prohibit policy
processing because no authority-bearing region will be mapped. An unexpectedly
provided descriptor is closed and recorded without taking ownership of its
payload. A missing required descriptor, core-limit failure, fstat/mmap/close
failure, invalid size or invalid header/binding refuses required setup.

Missing individual symbols do not refuse apparatus setup and do not suppress
other symbols or operations. Issue/consume/release dispatch checks its own
symbol. Retain supported consume or release evidence when another symbol is
missing. Availability establishes neither entitlement nor native success.

Required failure locally fills disposition/primary slot, release-publishes the
decision, performs and independently publishes applicable cleanup, then takes
a `_Noreturn` terminal path. Place its branch immediately after preparation and
before string/parameter processing, timing/policy read, compile, capture or apply.
Preparation must not unmap rejected mappings before the terminal decision is
published: retain a private cleanup reference, publish decision first, clean it
up second. This guarantees the refusal remains visible if cleanup fails or is
interrupted. No malformed region's counts authorize payload traversal or erase;
an unvalidated mapping is detached, not interpreted as slot storage.

`done` can follow applicable terminal cleanup attempts and does not certify that
cleanup succeeded. The host may resolve a published refusal before done/reap.
It may request departure during subsequent cleanup, but the decision already
excluded policy processing. A worker with terminal required failure has
`application.state = not_attempted`, with basis `terminal_authority_setup_refusal`
and no native apply return. Without eligible terminal-before-apply or
never-launched evidence below, absence of application publication means
`unobserved`, not `not_attempted`. Keep native apply failure
and successful applied publication in their existing evidence owners; do not
turn zero-initialized `apply_rc` or generic done into a native call result.

Header/input/parameter/compile terminal branches need similarly explicit
stage support when producing not-attempted application. Ready-byte failure and
optional capture failure remain auxiliary and can precede application. This
packet does not alter those native behaviors. Proposed `actors[].application`
is a small closed assessment `{state, basis}` (`not_attempted`, `observed`,
`unobserved`, or `not_requested` for unapplied) referencing the existing native
owner; it avoids duplicating apply rc/errno. Application_count continues to mean
successful applied publication, not call-entry count.

The following table is the complete state/basis vocabulary. Worker evidence
requires matching worker identity and actor association plus acquisition of its
own publication; a payload value without its publication is ineligible.

| State | Basis | Eligible source and exact meaning |
| --- | --- | --- |
| `not_requested` | `unapplied_declaration` | Admitted actor request has sandbox mode unapplied. This describes request meaning, even if launch failed; it is not a native observation or proof that a worker ran. An observed apply from that actor is a contradictory protocol fact, not permission to reinterpret the request. |
| `not_attempted` | `worker_not_launched` | Host launch accounting establishes that no worker was created for this apply actor. A missing PID field by itself, missing reply, or unknown spawn disposition is insufficient. |
| `not_attempted` | `terminal_authority_setup_refusal` | Acquired immutable setup decision is terminal_required_failure in the named worker, whose local branch excludes policy processing/application. Cleanup need not succeed or finish. |
| `not_attempted` | `terminal_input_refusal` | Acquired worker failure publication identifies a header/input or policy-read rejection whose exact operation/code and control-flow site terminate before application. Malformed ABI data without an eligible identity/publication does not qualify. |
| `not_attempted` | `terminal_parameter_refusal` | Acquired worker failure publication identifies a parameter-capacity, parameter-validation, parameter-object creation or parameter-set refusal on a terminal pre-apply branch. Retain its actual native result when any; it is not an apply result. |
| `not_attempted` | `terminal_compile_refusal` | Acquired failure publication identifies the compilation refusal on the branch that cannot reach sandbox_apply. A compile result from a separate controller helper says nothing about this worker and is ineligible here. |
| `not_attempted` | `terminal_timing_refusal` | Acquired failure publication identifies this worker's initial timing-setup refusal before policy processing. A later clock refusal after application cannot use this basis. |
| `observed` | `applied_publication` | Acquired worker applied publication establishes successful native application and makes its actual apply return eligible. This remains valid beside a host setup timeout. |
| `observed` | `apply_failure_publication` | Acquired worker failure publication names the native apply operation and carries its actual returned failure and immediately saved errno. A done publication alone or a synthesized apply_rc does not qualify. Application_count remains zero. |
| `unobserved` | `apply_call_boundary_without_result` | Eligible worker evidence identifies the pre-call apply boundary (or returned-stage progress) but no eligible apply result. The boundary means execution reached that marker; it cannot establish native return, application success, or that the call executed after interruption immediately following the marker. |
| `unobserved` | `no_eligible_apply_publication` | Apply was requested and no preceding eligible source establishes either a result or nonattempt. Includes reporting loss, process death, host timeout and an unobserved terminal branch. These conditions alone do not prove the native call was omitted. |

Use request meaning first for unapplied mode, then established no-launch,
then eligible native result or terminal nonattempt evidence; the two must not
contradict. Contradictory apply-result and terminal-pre-apply publications are
an integrity failure, not a precedence choice that silently discards one.
The two unobserved bases differ only in whether the call-boundary evidence is
eligible. They do not turn a sampled progress marker into a native result.

Implementation must maintain an explicit operation/code/control-flow whitelist
for the header/input, parameter, compile and initial timing terminal bases,
checked by independent native-call counters at the application boundary.
Published stage alone is insufficient if its code can also arise on a continuing
or post-apply branch. If current fields do not uniquely identify a branch that
excludes application, add an explicit terminal-before-apply publication or keep
the assessment unobserved; never infer nonattempt from fabricated applyRC,
generic failure, done, or reap. Reader mutations must reject forged terminal
bases and valid-looking failure codes from later execution stages.

If the reporting mapping itself is unavailable, no worker setup publication can
be claimed. Host launch/equipment/setup failure and child termination records
remain available through the XPC host. A process that never launched has an
empty worker operations array. Host failure before launch does not manufacture
worker not-attempted cells. Retain all attempted host regions/custody facts even
if the first failing region supplies the summary. If a deadline settles an
actor's setup_timeout first, subsequent setup decisions, per-cell facts and
application facts are collected but cannot enable any visit.

## Termination dependency: precise request and schedule contract

Request syntax (draft):

```json
{"phase_id":"subject_consume","actor_id":"subject",
 "after_termination":{"actor_id":"issuer"},"actions":[]}
```

Closed object with exactly one actor_id, existing identifier rules, one optional
dependency per phase, at most 16 in the entire specimen. No array, clean flag,
user timeout, PID or executable selector in this object. Refuse unknown actor,
self dependency, ordinary-form usage, nonobject/wrong type/unknown keys, and any
reference whose final scheduled phase is not strictly before this phase.
Explicit null is refused; omission alone means no dependency.
Resolve to source actor index/final phase index during admission; execution does
not resolve strings again. This forward-order condition also excludes cycles.
Use semantic refusal `invalid_termination_dependency` with the offending
`phases/{index}/after_termination/actor_id` path for unknown, self or remaining-
visit references; closed-object/type failures retain their decoder ownership.

Both actors launch and resolve setup before any visit. The subject can have an
earlier baseline visit and remains parked while the issuer issues/transfers.
The gate is evaluated before dependent activation, arrival collection or release.
The source's final visit must have been reached (activated); merely skipping a
source whose setup failed cannot satisfy an "after final visit" dependency.
Completion of that visit is recorded independently, not a requirement for the
termination condition. Existing failed-visit rules still prohibit later
activation unless quiescence/ownership permits it.
The principal abnormal-exit positive control completes its final phase and
then exits abnormally. This proposal does not override an earlier cancellation,
does not turn a failed visit into success, and does not use gate success to
restore eligibility lost under existing failed-visit rules.

Use a fixed `actor_termination_gate_wait = 5000` ms allowance, capped by remaining
aggregate execution allowance (120,000 ms). Gate time is charged to that
allowance, never excluded like validator collection, and does not extend the
180,000 ms shared worker lifetime cutoff. It starts when the gate is reached,
not at source launch. Sample a monotonic deadline before accepting each new
wait result; if the call returns after deadline, retain the reap fact but close
the gate as timed_out. Clock failure fails closed. No blocking wait, kill,
requestExit or finishCleanup inside the gate. Poll through `waitChild` with
WNOHANG; preserve its bounded EINTR retry behavior.

Retain an immutable **successful native reap observation** in ChildProcessState:
PID, native waitpid rc (equal to owned pid), raw wait status, stage, monotonic
observation ordinal/time, unbroken ownership, and whether exit/termination had
been requested before that observation. Do not call waitpid again on a known
reaped child. The existing `status` alone lacks when/why it was obtained. A prior
owned reap after the source's final activation can satisfy immediately if no
host departure request preceded it. A later housekeeping request on an already
reaped source does not rewrite its earlier natural observation. A failed wait
that already broke ownership cannot be repaired by a later reap for gate credit.

Public `phases[].termination_gate` is absent without a dependency; otherwise:
`{source_actor_id, source_final_phase_id, condition:"terminated", outcome,
wait?, observation?, activation_eligible}`. Outcome vocabulary:
`not_reached`, `satisfied`, `timed_out`, `ownership_lost`, `clock_unavailable`,
`source_unavailable`, `source_departure_requested`, `execution_allowance_exhausted`.
An observation references the source actor's owned reap record and includes the
gate's capture ordinal; it does not copy token/delivery evidence. `activation_eligible`
is true only for satisfied plus the dependent actor's independent usable setup.
A satisfied gate can coexist with no activation if another eligibility rule fails;
encode the actual activation separately. `wait` uses PWHostWait conventions and
records the actual clipped budget and stop, including immediate zero-elapsed
satisfaction if an earlier eligible observation is cached.

An abnormal exit observed without a host departure request satisfies termination
while retaining signal/nonzero status; it does not prove clean completion,
successful issuance, delivery or consume. `done` or final phase completion while
alive cannot satisfy. A never-launched source, unreaped source, lost ownership,
or a cleanup-only reap cannot satisfy. Any reached gate failure closes that
visit and cancels later activations with a dependency-specific reason, then
ordinary cleanup runs. This conservative choice avoids creating a second
conditional schedule language. Cleanup observations can add termination facts
but never rewrite the retained gate outcome. Collection and release remain false
for the failed dependent visit.

## Storage ownership and erasure remain distinct

| Storage/reference | Owner and observation |
| --- | --- |
| POSIX authority object name | Host until successful unlink; unlinked object can live through mappings/descriptors. Name absence is not mapping absence. |
| Original host descriptor / high launch duplicate / worker FD 5 | Separate close results. Closing one does not close another or unmap. Preserve the high duplicate used to avoid 0/3/4/5 collisions. |
| Host and worker shared mappings | Separate acquisition/unmap observations. Worker process exit can reclaim its references; it is not a successful munmap return. |
| Issuer native token allocation | Worker inspects bounded length, copies to outbound, clears inspected allocation and frees it; no full-capacity claim about a differently sized native allocation. |
| Committed outbound payload | Host owns after publication. Worker terminal cleanup must not erase it, even after worker timeout or done. Host clears full 16,384-byte slot before acknowledgement. |
| Host private custody | Host clears independently at last declared use or teardown, even if some actor is not quiescent. Its final unmap is a separate native observation. |
| Inbound payload before settlement | Host retains last read/compare rights. Worker framing acknowledgement alone does not authorize erase/consume. Failure withdrawal publishes settled=2; successful equality publishes settled=1. |
| Settled inbound payload | Recipient owns it. Last-use erasure follows a returned native consume call, including the -1 sentinel; early symbol/channel/delivery returns do not prove last-use erasure. Terminal cleanup can clear settled slots. |
| Shared region final erasure | Host may clear only after actor reap/established quiescence, or if no actor ever launched. Unknown termination withholds shared clear while private custody still clears. |
| Native extension handle | Explicit release action is independent of buffer erase, close, unmap, done and reap. Do not invent release during cleanup. |

Eager setup, parked delivery service and overlapping process lifetimes remain.
An actor may finish and exit after its own final visit before overall schedule
completion. The dependency imposes an observation order; it does not defer
subject creation or imply the issuer lived until the gate began.

## Assertions inspected; adaptations required before acceptance

| Existing owner | Assertions actually inspected | Required extension / coverage limit |
| --- | --- | --- |
| `runner_c_worker_harness/terminal_erasure`, [checker](../../tests/suites/runner_c_worker_harness/check_terminal_erasure.py), [fixture](../../tests/fixtures/extension_controls/terminal_control.c) | Parent checks all 16,384 bytes (tail deliberately seeded), not requested clear length. At production done-release seam the child blocks while parent observes zeros. Shortened-clear mutation fails full-capacity oracle; erase-after-done mutation passes post-reap check but fails boundary oracle. Early branches, cancel/no done, failed consume, explicit release and fatal interruption have distinct expected shapes. | Present fixture is declaration-channel based. Replace its storage with actor inbound/outbound regions and keep both rejected mutations. Add settled/withdrawn/unsettled cells: terminal worker clears settled inbound, preserves host-owned outbound and unsettled inbound; host after reap clears remaining shared bytes. Assert no implicit native release. Fatal consume can leave bytes. |
| `runner_unit/ActorAuthorityTests` through unit executable | Separate retained mapping proves full shared payload stays 0x5a for unknown quiescence and clears for known quiescence; second finish cannot turn prior unknown into erase permission. Copy-boundary and one-shot answer checks distinguish host delivery from source acknowledgement. | Keep these independent observers. Add private-custody clearing proof while shared erasure is withheld; expose close/unmap failures independently without clearing ownership claims. Existing assertions do not prove every host cleanup syscall succeeded. |
| `witness_contract/extension_boundaries`, [checker](../../tests/suites/witness_contract/check_extension_boundaries.py), [native control](../../tests/fixtures/extension_controls/control.c) | Modes 107–112 compare exact core/fstat/mmap/close primary failure rc and errno; mode111 combines fstat EIO with close EBADF; size rejection retains fstat rc0/no errno. Symbol absence and cleanup mode118 are separate. Controlled close actually closes then substitutes failure, so it does not prove a real leaked fd. | Port to actor production dispatch and new setup cells. Add mmap failure plus independent close failure, header rejection plus munmap failure, success acquisition plus cleanup failure; three individually missing symbols; no-authority mode. Independent call counters assert **zero** policy-read/compile/capture/apply calls on terminal authority refusal. Removing terminal branch must fail that oracle even if scheduling still refuses. |
| `runner_unit/ActorReplyTests` | O_EXCL name collision yields all launch=nil/subprocess=nil/launch_refused, no extension calls/results and unresolved token; reply encoded and retained. Late setup timeout test keeps applied=true/application_count1 and excludes subject arrivals. | Collision assertion does not explicitly reopen/check that unrelated object survived. Add that independent ownership assertion, per-region later attempted successes, host core failure scoped once, custody failure and all independent cleanup records. Keep timeout-plus-late-observation control through Swift/Rust/Python readers. |
| `runner_unit/ActorSchedulerTests` | Late setup application remains counted without collection/activation; lost ownership keeps unresolved state even after fixture independently cleans child; eight actor and interleaved visit controls. | Add source done while alive, completed final phase while alive, abnormal natural reap, source unavailable, prior host-requested departure, lost ownership and gate timeout followed by successful cleanup. Gate-removal mutation must fail independent child wait/reap-to-dependent-activation ordering assertion. No sleeps as the ordering oracle. |
| `runner_unit/host_setup_controls` / `host_setup_oracle_sensitivity` | Sensitivity script preserves old checker and adds separate receipts for argv/access direction and complete VM extent. Partial-unmap mutation reconstructs native address-range queries, sees remainder, cleans fixture remainder and verifies it gone; it demonstrates legacy checker accepted the faulty variant. | These cover general worker/validator reporting apparatus, not all AuthorityCustody native calls. Adapt authority paths with separate FD/mapping/native observers; preserve existing receipt schema/known observer-receipt issue as separately owned. Do not credit a passing retry as resolving it. |
| `runner_c_worker_harness/authority_binding` and actor operations controls | Production binding, one-shot transfer association and page-rounded maximum authority mapping. | Add setup publication withheld/partial/late cells, exact slot capacity, malformed indices/flags/association and independent field-value checks; full C entry path controls establish refusal before policy, not isolated prepare calls alone. |

New native/setup controls should publish their own counters/FD checks and
hold an independent mapping; checking the proposed JSON against itself is not
an oracle. Add deliberate corruptions for cleanup replacing primary failure,
unpublished cells being accepted, fabricated errno on size validation, and
timeout being upgraded by late setup/reap. Readers must reject each independently.
Also publish a close-cleanup cell while withholding the setup decision and
assert that its explicit cleanup role remains eligible; mutate its reserved
flag bits and require rejection without reading unpublished primary metadata.
For an unresolved linked-name receipt, replace the object under the same name
in an isolated fixture and assert that no recovery unlink is attempted or
settlement claimed from the old receipt. These controls establish the absence
of unsafe automatic recovery, not an identity-verification mechanism.
Update the coordinated ABI/limit/admission suites and run
`witness_contract/order_barrier_mutations` because the gate and terminal setup
change activation/query eligibility. New Stage 4 controls are obligations, not
claimed existing passes.

The integrated specimen sequence is baseline subject fresh access; issuer final
issue+transfer; subject gate+consume; next subject phase queries then fresh access;
release; final fresh access. Independent source reap and dependent activation
observations establish gate ordering. Native issuer-exit evidence supports only
its own arrangement. Gate success never substitutes for delivery settlement,
consume native result or observed file access.

## Constructed failed-setup records and review conditions

See [host failure](setup-examples/host-failure.json),
[worker primary plus cleanup failure](setup-examples/worker-primary-cleanup.json),
[validation rejection](setup-examples/worker-validation.json), and
[late setup](setup-examples/late-setup.json), plus
[unresolved linked-name cleanup](setup-examples/host-unlink-unresolved.json).
Each contains a complete proposed
`authority_setup` object plus the associated actor/phase assessment. These are
schema design examples, deliberately not valid current-version full runner
replies; production fixtures must be rebuilt through their owning encoder.

Review must accept or revise the public dependency, 5-second clipped budget,
termination rather than clean-completion condition, cancel-remaining policy,
per-assigned-region applicability, exact operation inventories/capacities and
publication/ownership rules together. No production implementation before that
checkpoint. Failed setup does not need to sacrifice otherwise valid evidence;
adding evidence does not grant action eligibility.
