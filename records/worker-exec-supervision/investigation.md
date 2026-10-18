# Exec completion and cleanup investigation

Status: investigation complete and ready for design review; no production design
selected or implemented.
Source baseline: `503156f0693dd8a22acf633efccdc93e300f2ebc`.
Associated handoff: [EXEC-SUPERVISION-PLAN.md](../../controller/tools/pw_probe_runner/EXEC-SUPERVISION-PLAN.md).
The completed terminal-exit rule is a constraint: ordinary terminal publication
erases accepted token storage, publishes `done`, and exits immediately. No
proposal here depends on keeping a completed worker alive.

## Recommendation to take to the design decision

Keep exec completion about the native spawn, the leader's observed status, and
bounded collection of its two captured streams. Record cleanup intervention
and what it establishes separately. Do not make a successful leader exit or
both EOFs imply descendant absence. Do not turn cleanup uncertainty into a
claim that the spawn failed or the sandbox denied it.

The smallest behavioral extension worth considering is a group termination
request on ordinary leader-plus-EOF completion, before reaping the worker's
still-owned leader. This requires no extra process, leaves the actual spawn
and pipe acquisition after sandbox application, and directly addresses the
demonstrated ordinary-completion survivor path. Its contract remains bounded
cleanup effort; a successful signal call alone is not a completed cleanup.
Worker loss and escaped descendants remain explicit limits.

An independently owned, pre-established cleanup group is a materially larger
option if cleanup attempts after worker loss are required. The anchor experiment
below tests its native feasibility, not a production implementation. An anchor
is not justified merely to repair the documentation's incomplete statement of
the current boundary. It also does not establish later-step isolation: with
no verified absence or complete member tracking, reporting the external signal
request remains weaker than proving that no descendant can act later.

The actual decision is therefore whether to extend cleanup effort to ordinary
completion only, or also pay for a surviving owner and group establishment
before each exec spawn. Either choice can retain a narrow, honest completion
contract. Arbitrary descendant containment is a separate capability decision.

There is a real capability tradeoff before choosing ordinary cleanup. An exec
target can intentionally start background work that later probes are meant to
observe. Killing its same-group descendants at leader-plus-EOF completion
changes that experiment, including shell commands that intentionally return
before the work finishes. Existing characterization establishes that capability
today; it does not establish a user's need for it or a promised stable API.
The first decision should explicitly choose whether ordinary exec completion
is intended to end such work. Do not add a background/cleanup mode without a
concrete specimen that needs both policies. If background work is intended,
retaining the present native behavior with accurate limits is a defensible
outcome of this investigation.

## Current production behavior

Source anchors are in [attempt_exec_spawn](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
and [runCWorker / ChildProcessState](../../runner/Sources/PWRunnerCore/CWorker.swift).

1. `exec_resources_acquire` creates two pipes and spawn handles during the
   attempt, after application. The child receives an empty environment and
   explicit standard descriptors. `POSIX_SPAWN_SETPGROUP` with group zero
   creates a group whose identifier equals the exec leader's PID.
2. `posix_spawn` returns before `slot->child_pid` is stored. Even that store is
   not a completed result: the host reads exec payload fields only for a
   completed slot. Worker death in either interval can leave a real spawn
   without a published completed attempt.
3. The observation loop uses `waitid(... WNOWAIT)` to observe leader exit
   without reaping, and drains both streams independently. Normal observation
   ends only when the leader has exited and both streams reach EOF. EOF alone
   does not stop a running leader; leader exit alone does not close a pipe held
   by a descendant.
4. A deadline, observation error or local clock fault requests
   `kill(-child_pgid, SIGKILL)` while ownership is known. Ordinary observation
   completion does not. The worker then attempts bounded nonblocking leader
   reap. Neither the group signal result nor the leader's reap is a complete
   process-tree observation.
5. The host writes `exitRequested` after its poll loop and uses grace/reap plus
   a worker-PID SIGKILL fallback. `attempt_exec_spawn` does not poll that shared
   cancellation byte. If it finishes before host grace expires, it may reach
   later steps/phase waits; otherwise the host can kill the worker during exec
   observation. There is no host descendant-cleanup action in either case.
6. Normal completion of all slots now reaches immediate worker terminal exit.
   The independently retained same-group survivor below outlives both the
   successful later step and that normal worker exit. This is not a regression
   in the terminal rule: worker terminal lifetime never established descendant
   cleanup ownership.

The worker account's resource rows already say group cleanup is conditional.
Its prose Known gap at `docs/WORKER.md:394–396` and the summary at `:544` still
name only descendants that leave the group, and incorrectly use the broad
phrase “at cleanup.” The correction needs to include ordinary completion with
closed streams and worker death, regardless of whether a refactor is chosen.
Edit `docs/architecture.json` and regenerate when that documentation change is
authorized; this investigation leaves both inputs and generated files intact.

## Current-build observations

The coordinator executed:

```sh
PW_TEST_OUT_DIR=tests/out/runs/worker-followup-baseline-20261018 \
  tests/run.sh --suite runner_exec_lifecycle --suite exec_fixture \
  --case runner_unit/host_setup_controls
```

Run ID `20261018T192430Z_884b74f5`: seven selected, seven passed, no skips,
unrun cases or harness errors. The signed app was valid before testing and its
inventory was unchanged afterward. Source inspection uses the baseline above;
the relevant production and existing test sources were not modified during the
run. The extra host-setup case belongs to the descriptor investigation and is
not used to establish exec cleanup.

The run and its per-case artifacts are gitignored local evidence under
[worker-followup-baseline-20261018](../../tests/out/runs/worker-followup-baseline-20261018/).
The durable report records the observations without treating a passing case
name as evidence of a stronger guarantee.

| Credited case | Observation established |
| --- | --- |
| `exec_fixture/controls` | Independent helper identity, responsiveness and exit observers; normal release, group kill and a rejected leader-only cleanup control. |
| `runner_exec_lifecycle/timeout_preserves_output_and_continues` | The exercised leader and same-group descendant both have kernel exit events after deadline cleanup; existing output survives and the following file write changes bytes. |
| `runner_exec_lifecycle/closed_streams_continue` | Both peers acknowledge stream closure and remain responsive before fixture release; EOF alone is not completion. |
| `runner_exec_lifecycle/leader_exit_descendant` | The leader exits zero while its child holds streams; deadline cleanup stops the observed descendant and preserves the actual leader status. |
| `runner_exec_lifecycle/worker_dies_during_exec` | The independently identified worker is SIGKILLed; both observed helpers remain responsive after the CLI completes. Earlier file effect survives, unfinished/later attempts have no completed result, and the later target is unchanged. |
| `runner_exec_lifecycle/closed_streams_leader_exit` | Both peers close streams, the leader exits, PW completes cleanly and performs the later write, yet the same-group child still answers with its original identity. Fixture release subsequently yields its exit event and the liveness assertion then rejects it. |

The final case observed leader `68255`, descendant `68260` and worker `68253`.
After the CLI returned zero, descendant `68260` had been reparented to PID 1,
retained PGID `68255` and its start timestamp/path, and answered a ping. The
following file contained `0x78`. Its cleanup account records both helper exits,
the worker exit, closed CLI and removed staging, with no cleanup errors.

The worker-death case observed worker `68162` and helpers `68165`/`68170` in
group `68165`. Neither helper had an exit event when liveness was checked after
the failed run. This case's older `TreeControl.close()` sends fixture release
and attempts cleanup, but does not retain a separate final cleanup account or
require post-fallback exit events. Credit its pre-cleanup survivor observation;
do not cite its pass as durable proof of final helper absence.

A separate read-only check at `2026-10-18T19:30:52Z` found both original helper
PIDs absent: the existing fixture's libproc query returned `ESRCH` and `ps`
reported no entry for each. [baseline-later-absence.json](baseline-later-absence.json)
retains commands and native output. No signal was sent. Original helper start
timestamps were not persisted by the case, but absence of either PID at this
later observation establishes that those original processes no longer exist.
It does not establish when or how they exited or strengthen the original case's
cleanup assertions.

## Alternatives and their exact boundary

| Option | What improves | What remains unestablished | Additional cost / changed experiment |
| --- | --- | --- | --- |
| Keep current native behavior; clarify leader/streams completion and cleanup uncertainty | Correct meaning and documentation; no new native intervention | All currently observed survivor paths | No new process/channel/authority. |
| Always request group cleanup before normal leader reap | Removes the lack of any intervention on ordinary completion in supported cases | Worker death before cleanup; escaped descendants; actual group absence after a successful signal | One additional signal boundary on normal completion, under the worker's sandbox; no new owner or attempt-resource acquisition. |
| Publish PID/group to host after spawn and acknowledge registration before proceeding | Host can clean registered jobs when the worker later dies | Child created before registration; identifier reuse after worker-owned leader is reaped; descendants escaping before tracking | New live publication/ack protocol and unsandboxed signalling authority. Current completed-slot data is too late. |
| Start child suspended, register, then resume | Arbitrary target user code cannot run before successful registration | A suspended child can still exist when the worker dies before registering it; missing identity remains a cleanup problem | Changes spawn flags and startup timing; adds resume/failed-registration paths. It reduces pre-registration effects but does not by itself close the creation gap. |
| Spawn a cooperative wrapper, register, then exec target | Wrapper can enforce a bounded registration handshake and self-exit on channel failure | Wrapper dies before registering, noncooperating descendants, owner loss, and changed operation identity | Actual initial posix_spawn targets the wrapper; the requested executable is a later exec. This changes the existing witness capability. |
| Establish an externally owned group before actual post-apply spawn | A living owner can address group members even when the worker dies before publishing child identity | Escaped members; owner death without another owner; denied/incomplete signalling; total group absence without an observation | Anchor process, group-allocation handshake, different child-visible group/leader relation, ordinary-authority host cleanup. Native feasibility is tested separately. |
| Controlled helper contract instead of arbitrary executable | Can prescribe registration, descendant behavior and cleanup handshakes | Arbitrary program behavior is no longer the offered operation | A narrower product capability, not an interchangeable implementation of existing arbitrary exec. |

A separate leader result and cleanup result must allow combinations such as
“spawn returned success; leader exited zero; streams reached EOF; cleanup
requested; absence unestablished,” or “worker died; no completed leader result;
externally owned group cleanup requested.” A lost cleanup owner is not evidence
of a failed spawn, and external cleanup must not be attributed to the specimen's
policy. Exact public fields and version changes belong to a selected refactor,
with producers and independent readers changed together.

An external owner is not automatically the parent entitled to `waitpid` the
worker's exec leader. After worker loss, its independent process exit event or
group signal does not recover the worker's missing native wait status. Preserve
that absence unless a specifically designed independent status observation
establishes more; never fill a clean leader exit from an anchor's own reap.

## Registration, lifetime and authority constraints

A post-spawn report cannot retroactively cover an earlier fatal interruption.
Atomically assigning an already-established group at creation is one candidate
way to avoid requiring the newly created child's numeric identity for cleanup.
This is not a proof that all alternative handshakes are impossible. A
cooperative launcher changes the relevant target/operation; suspended startup
changes when effects can begin and still needs cleanup of an unknown child.

The proposed group anchor is a direct child retained by the external owner.
The owner would keep it live, or retain its unreaped exit, until the last group
signal and observation are finished. It must never signal the old numeric PGID
after relinquishing that identity. A live anchor itself prevents declaring the
group empty; killing the group also kills the anchor, and reaping it too early
removes the simple direct-child lifetime argument. A numeric snapshot followed
by a signal is not atomic identity validation.

The spawner and anchor must be in compatible sessions for group assignment.
The experiment checks that relationship directly; production XPC host/session
setup and BYOXPC variants still need integration evidence. The actual spawn
must remain in the worker after apply. The anchor cannot open the attempt's
pipes, target or `/dev/null` early to bypass specimen restrictions.

An anchor also changes target-visible state: the exec leader would normally
join a group whose ID is not its PID. A leader in this group can itself attempt
`setsid`, whereas the current group-leader relationship blocks that particular
call until it forks a non-leader descendant. This is a measurable configuration
change, not a transparent cleanup implementation. Additional channels must not
leak evidence/token descriptors to targets, validators or the anchor; the
descriptor investigation settles that inheritance boundary before wiring.

For sequential attempts, killing an anchor's group retires that group's useful
lifetime. Reusing one numerical PGID after reaping is unsafe. One anchor per
attempt needs either many preallocated processes or a host/worker allocation
handshake before each spawn. One group for the whole specimen reduces process
cost but changes the cleanup boundary: killing it must not kill the worker
needed for later steps, and it cannot isolate attempts without another
mechanism. These are design costs, not mere implementation details.

Worker death and supervisor death are different fault models. A host-owned
anchor can outlive a worker while the host still acts. A passive anchor does
not clean anything if that host dies. Making the anchor an active watchdog adds
an independent liveness/deadline channel; if it kills its own group, it cannot
report its own subsequent completion. Another observer must retain that fact.
If both owner and watchdog die, this design offers no cleanup guarantee. No
experiment here claims survival of the external owner itself.

Group membership is not arbitrary containment. A descendant may change groups
or sessions; unrelated same-user processes can also change compatible group
membership. A group signal should be tied to an intentionally established
owned group, not a guessed process-tree snapshot. Kernel process exit events
for registered peers prove those peers exited; a sampled process list or a
successful group signal does not prove all descendants were discovered.

## Native sources and scope

- Apple's [spawn group documentation](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/posix_spawnattr_setpgroup.3.html)
  describes assignment to a created or existing group at process creation.
  [setpgid](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setpgrp.2.html)
  constrains joining an existing group to a compatible session and describes
  failures after exec or for session leaders.
- Apple's [spawn flags documentation](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/posix_spawnattr_getflags.3.html)
  describes suspended startup before user execution. It does not provide an
  atomic publication of that child's identity to a separate supervisor.
- Apple's [setsid documentation](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setsid.2.html)
  permits a non-group-leader to create a new session and group, explaining the
  escaped-descendant negative control.
- Apple's [kill documentation](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/kill.2.html)
  defines group addressing and permission/error results, not a completion
  notification. The [XNU implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c)
  additionally shows why zombie handling and signalling return conventions
  deserve observation rather than assuming that signal zero is an exhaustive
  live-member census.
- Apple's [kqueue documentation](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/kqueue.2.html)
  distinguishes exit and fork notifications. The installed SDK's
  `usr/include/sys/event.h:355–361` explicitly marks `NOTE_TRACK`,
  `NOTE_TRACKERR` and `NOTE_CHILD` unsupported since 10.5. A fork notification
  is not automatic reliable descendant registration.
- The installed SDK declares `proc_signal_with_audittoken` in `libproc.h`, and
  Apple's [libproc source](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c)
  routes it to a distinct audit-token signal operation. That is a candidate for
  safer signalling of separately registered process identities; this work has
  not tested its authority/compatibility or a complete discovery protocol. It
  does not by its existence solve unknown descendants or group escape.

These manuals and inspected upstream sources inform hypotheses and API
semantics; they do not identify the exact implementation of this installed
kernel. Current-platform observations are recorded separately.

## Anchored-group feasibility experiment

Equipment: [anchor_probe.c](anchor_probe.c) and
[run_anchor_probe.py](run_anchor_probe.py). The coordinator reviewed the scaffold
and allocated an exclusive execution window after the descriptor investigation.
The experiment ran outside the automation sandbox under the checkout lock:

```sh
tests/lib/checkout_lock.sh -- python3 -B \
  records/worker-exec-supervision/run_anchor_probe.py \
  /private/tmp/pw-exec-anchor-20261018
```

It exited zero. [anchor-result.json](anchor-result.json) retains the exact
command, build commands/results, platform, source hashes, copied-source mutation,
both complete observation records and both cleanup accounts. Binaries and the
copied fixture source remain local under `/private/tmp/pw-exec-anchor-20261018`;
they are not repository deliverables. All hashed source inputs matched after
execution. Both cases recorded complete cleanup with no errors.

The controller starts and retains an anchor in a fresh group. A separate native
spawner compiles and successfully applies `(version 1)(allow default)`, reports
application, waits for a command, then creates pipes and actually calls
`posix_spawn` into the known anchor group. It reports only a successful-return
marker, withholds child PID publication, and blocks. The test obtains the helper
leader/descendant PIDs from kernel Unix-socket credentials, snapshots their
start times/paths and groups, kills the spawner, and requires both helpers to
remain responsive before any group cleanup.

The controller signals the group while retaining the anchor as an unreaped
direct child. It requires the observed same-group helpers and anchor to have
kernel exit events before reaping the anchor. A separate negative control first
moves the descendant into a new session/group through one explicit copied
fixture mutation. That descendant must survive the original-group signal with
the same identity and answer a ping, then exit after independent fixture release.

All processes have bounded alarms; the controller owns direct children and peer
connections, persists ownership before interventions, and retains a cleanup
account when rendezvous or exit observations are incomplete. Output records
source hashes, exact copied-source mutation, build commands/results, native
observations and cleanup separately. It never changes the app or production
sources. The scaffold is a native capability probe, not a production-worker
mutation: it does not implement real phase handshakes, timing/publication,
arbitrary denying profiles, cancellation, host death or all descendant tracking.

Observed results:

| Control | Native observation | Supported conclusion |
| --- | --- | --- |
| Same group | Applied spawner `72312` and anchor `72310` shared session `72303`; actual helper `72314` and its child `72315` joined group `72310`. After spawner SIGKILL, both helpers still responded. The external group signal then yielded exit events for both helpers and the anchor before anchor reap. | The tested allow-default post-apply spawn can join an externally established group, and a living external owner can stop these observed members without relying on the worker to publish their PIDs. |
| Escaped descendant | Applied spawner `72321` created helpers `72323`/`72324` in anchor group `72319`. Child `72324` successfully entered session/group `72324`, retained its identity and answered a ping after the original-group signal and leader exit. Fixture release later yielded its exit event. | The same external-group operation does not stop an escaped descendant. |

In **both** controls, `killpg(group, 0)` returned `-1 / EPERM` after the
observed group members' exit events while the anchor remained unreaped. This is
a raw observation, not an absence result or evidence that a live process
survived. It directly discourages treating a simple signal-zero probe as a
complete group-emptiness oracle in the proposed ownership protocol. The
experiment's known-peer exit observations establish only the controlled peers.

The result makes an externally owned cleanup-request contract plausible without
claiming group absence. It does not select that contract: the ordinary-completion
change is still much smaller, and the extra anchor is worthwhile only if
worker-loss cleanup requests justify its process/protocol/authority costs.

## Required follow-up before an external-owner refactor

If the design chooses worker-loss cleanup, the next experiment should use copied
production worker/host paths and hold a real spawn at the pre-publication
boundary. It must prove the host knows an owned group before releasing that
spawn, survive worker death there, preserve actual post-apply resource setup,
and independently establish the observed helpers' deaths. Repeat on ordinary
completion, native setup/spawn refusal, no child, registration refusal,
host cancellation, owner/anchor death and escaped descendants. Identity loss
must stop unsafe signalling and remain visible as incomplete cleanup.

Only after that evidence should a plan choose the public cleanup fields and
whether later steps require stronger observed cleanup. The smaller ordinary
cleanup change should verify that the group termination request precedes leader
reap and advancement to later steps, while retaining the actual leader exit
code/output and the request's native result. In the controlled lifecycle fixture,
independently require the known same-group descendant's eventual exit within a
bounded observation window, before fixture cleanup. That observation establishes
the exercised request's effect; it does not establish that the descendant exited
before a later step ran. Require observed absence before a later controlled
effect only if that stronger sequencing contract is separately selected and
implemented. Keep worker-death and escaped-descendant limits explicit.
