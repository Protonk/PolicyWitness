# Host lifetime investigation: build 853

> Archive availability: original raw runs are not retained. Reproduction
> procedures describe the original `records/performance/` layout and pinned
> environment; committed derived evidence remains available.

On the built-in runner, launchd started a separate host generation for every
client process, in a launchd domain named for that client. For all 49
invocations that received a reply, launchd recorded that the host exited from
a `SIGKILL` sent by launchd during teardown of the client's domain, not from
the host's own scheduled `exit(0)`. In the 27 with process observation, the
kill message followed the client's exit by 0.05–0.14 ms and the host's exit
followed the message by 0.42–0.97 ms. The 50 ms post-reply delay never
elapsed. No request was refused as `already_ran`, no XPC error occurred, and
no observed worker or validator outlived its host. In a bounded
client-timeout control, launchd sent `SIGTERM` instead. Each host continued
until its worker and validator had exited, then the host process sent itself
`SIGKILL`, 3.4–6.2 ms after launchd's signal. The external runner was
not tested. These are observations of one executable, specimen and machine
interval, not a throughput estimate or an optimization proposal.

## Evidence and conditions

The application was `dist/PolicyWitness.app`, version 0.3.3, build 853,
commit `1bf0341cd06c48122af1635e8aa8cac77517d9e1` (`v0.3.3`), reported by
`policy-witness --version` and both Info.plists. Repository HEAD was
`aeb0389`; it differs from the build commit only in `tests/RETAINED.json`.
The working tree was clean apart from untracked files: the investigation
brief, this report, the harness and its evidence. The host and client carry
Developer ID Application signatures with TeamIdentifier `42D369QV8E`; the host
CDHash was `df6ee9bd9d0f00425b69128ef8225d0e2afe2252` and the client's
`6a8efe4ab6f2e4174748c88839b6c0d2e2f8ea33`. SHA-256 values for every
executable are in each run's `run-record.json`.

The selected runner was the built-in service
`com.policywitness.policy-witness.PWRunner` (`runner_kind: standard`). Its
XPC Info.plist declares `XPCService.ServiceType = Application`,
`PWRunnerRequireSignedCaller = true` and the allowed identifiers
`pw-runner-client` and `com.policywitness.policy-witness`. `runner list`
reported no external runners and `runner reconcile` no candidates or pending
cleanup.

The machine was a Mac17,3 (arm64, 10 logical CPUs, 16 GiB) running macOS
26.7.1 (25G241), Darwin 25.6.0. It was on battery power (`pmset`:
discharging, 100%), unlike the first cycle's AC condition. All work was
interactive, with this agent session active; there was no operator-run stage.
The pilot 1 start snapshot shows a Python process not started by this
harness (parent PID 96824) at 100% CPU, absent from later snapshots.

Every invocation used
[`specimen_mach_deny.json`](../../../tests/fixtures/pw_runner/specimen_mach_deny.json)
(SHA-256 `fe7c5e04…e604`): `(version 1) (allow default) (deny mach-lookup)`,
one step, one validator collection. Each run therefore has one worker and one
validator. The harness
([`host-lifetime/`](host-lifetime/README.md)) recorded SHA-256
`6a6fe0847376fd353406aa6cb98c247ba68b6f1444af36800385b3954a946eb5` for
`observe.py` in every measured series and ran on Python 3.14.8 through
`tests/lib/python.sh`. It held `tests/.checkout.lock` during each series.

| Run | Series | Invocations | Outcome |
| --- | --- | ---: | --- |
| [`…042144881445Z-hostlife-builtin-separated-b853`](evidence/20261024T042144881445Z-hostlife-builtin-separated-b853/summary.json) | separated, observed | 5 | 5 `ok` |
| [`…042152618416Z-hostlife-builtin-rapid-b853`](evidence/20261024T042152618416Z-hostlife-builtin-rapid-b853/summary.json) | rapid, observed | 12 | 12 `ok` |
| [`…042154988764Z-hostlife-builtin-overlap-b853`](evidence/20261024T042154988764Z-hostlife-builtin-overlap-b853/summary.json) | 5 overlapping pairs, observed | 10 | 10 `ok` |
| [`…042221835930Z-hostlife-control-unobserved-separated-b853`](evidence/20261024T042221835930Z-hostlife-control-unobserved-separated-b853/summary.json) | separated, no polling | 5 | 5 `ok` |
| [`…042229504006Z-hostlife-control-unobserved-rapid-b853`](evidence/20261024T042229504006Z-hostlife-control-unobserved-rapid-b853/summary.json) | rapid, no polling | 12 | 12 `ok` |
| [`…042231829587Z-hostlife-control-unobserved-busyloop-separated-b853`](evidence/20261024T042231829587Z-hostlife-control-unobserved-busyloop-separated-b853/summary.json) | separated, no polling, one busy core | 5 | 5 `ok` |
| [`…042335131650Z-hostlife-control-clienttimeout22-b853`](evidence/20261024T042335131650Z-hostlife-control-clienttimeout22-b853/summary.json) | rapid, observed, `--timeout-ms 22` | 4 | 4 `xpc_timeout` |

Run identifiers begin `20261024T`. All seven series completed their schedules
within their ceilings. Every listed raw checksum verified, with no unattested
files. No observed owned process was alive at any series end. Controller exit
was 0 for every `ok` and 1 for every `xpc_timeout`. Original raw directories under
`records/performance/runs/` are not retained. The committed
`summary.json`, `units.json` and `run-record.json` under each `evidence/` link
were written by `analyze.py` from verified raw files.

## The source-level model

The client ([`main.swift`](../../../runner/Clients/PWRunnerClient/main.swift))
reads the whole request and opens one `NSXPCConnection(serviceName:)`. It
makes one `runSpecimen` call, waits up to `--timeout-ms`, writes the reply
or a synthetic `xpc_timeout`/`xpc_error`, and exits.

In the host ([`PWRunnerService.swift`](../../../runner/Sources/PWRunnerCore/PWRunnerService.swift)),
the listener delegate authorizes the caller when it accepts a connection, and
every connection's service object shares one `PWRunnerAdmission`.
`runSpecimen` first calls `claim()`:

- If the claim is already taken, the host replies `already_ran` with
  `pid: getpid()` and schedules nothing.
- If the claim succeeds, a decode, admission, meaning or policy-hash refusal,
  or a completed orchestration, replies and calls `scheduleExit`. That is
  `exit(0)` 50 ms later on a global queue (`hostExitDelayMs`).

The admission rule is therefore a per-process flag. Process termination is a
separate scheduled event. The reply's `pid` is the worker's when a worker was
launched, and the host's `getpid()` for pre-worker replies. The controller
([`runner_acquisition.rs`](../../../controller/src/runner_acquisition.rs)) retries
after a qualifying `already_ran` only for a Mach-service (external) runner;
the built-in path makes one client attempt.

The documentation states:

- [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md): the host "exits shortly after
  replying" (in the topology table, "50 milliseconds after replying").
- The same document: after a client timeout, "Host work continues
  independently."
- [LIMITS.md](../../../docs/LIMITS.md) `host_exit_delay`: "The unsandboxed host
  exits when the delay elapses."
- LIMITS.md's grounding row: flushing and scheduling are source-inspected, not
  guaranteed.

## Method

Observers and identity:

- **Process table:** about every millisecond, the harness lists all PIDs. It
  identifies each process from the selected app by path, kernel creation time
  and `p_uniqueid`.
- **Lineage:** the parent's `p_puniqueid` links a child to the exact parent
  generation. Every worker and validator has a host as its parent this way, so
  a host is tied to the invocation whose reply names its worker. A PID alone is
  never used for this.
- **Exits:** kqueue `NOTE_EXIT` gives exit observations; hosts also report
  `NOTE_FORK`.
- **launchd's account:** after each series, launchd's own unified-log messages
  for the service are retrieved. They give a second, independent observer of
  instance domain, spawn, signal and exit reason. They are placed on the
  harness's `CLOCK_MONOTONIC_RAW` axis through `machTimestamp`.

The method's limits are in the [harness README](host-lifetime/README.md#limits).

The two observers agree closely:

- launchd's exit message fell within −0.021…+0.076 ms of the kqueue exit
  observation in the separated and overlap series.
- In the rapid series it was −0.446…+0.032 ms. The harness is spawning the
  next controller at that moment, so its kqueue retrieval can lag by up to
  about 0.45 ms.
- Wall-minus-monotonic drift was 5–25 µs per series.

| Interval | Start event (observer) | End event (observer) |
| --- | --- | --- |
| W | before controller `posix_spawn` (harness) | controller `NOTE_EXIT` (harness kqueue) |
| C | controller's clock before client spawn | controller's clock after client exit (whole ms, envelope) |
| client → host creation | client kernel creation | host kernel creation (as `xpcproxy`) |
| host creation → exec | host kernel creation | `xpcproxy` exec `NOTE_EXEC` (harness kqueue) |
| host exec → worker | exec observation | worker kernel creation |
| host lifetime | host kernel creation | host `NOTE_EXIT` (harness kqueue) |
| last child exit → client exit | later of worker/validator `NOTE_EXIT` | client `NOTE_EXIT` |
| client exit → kill message | client `NOTE_EXIT` | launchd "signaled service" (unified log) |
| kill message → host exit | launchd "signaled service" | host `NOTE_EXIT` |
| previous host exit → next start | previous host `NOTE_EXIT` | next controller spawn or client creation |

The host's reply is not directly observed. Its source position, after reaping
the worker and validators and before client receipt, bounds reply→host-exit
between client exit→host exit and last child exit→host exit.

## Pilots and their failures

The method changed four times. Each pilot is retained, and its evidence
summary preserves what it misidentified:

1. **Pilot 1** (`…041208515113Z-hostlife-pilot1-separated-b853`, n=3):
   - Lineage was correct.
   - Hosts were found only through a 20 ms recheck, because launchd creates
     them as `xpcproxy`.
   - The host exited 0.59–0.63 ms after its client, not 50 ms after replying.
   - An ad hoc `log show` then found `signaled service: Killed: 9`.
2. **Pilot 2** (`…041434411682Z-…`, n=3):
   - Two workers were recorded as hosts. A `posix_spawn` child is briefly
     visible under its parent's image before its exec.
   - The log predicate omitted the kill lines, because launchd's domain prefix
     is the `subsystem` field.
3. **Pilot 3** (`…041518215306Z-…`, n=3):
   - One client was recorded as a controller: its exec completed before
     registration.
   - The log's wall timestamps were about 11 ms off the harness wall clock;
     `machTimestamp` matched `CLOCK_MONOTONIC_RAW`.
4. **Pilot 4** (separated, rapid and overlap, n=3, 3 and 4): identification
   and lineage were complete. Its summaries are the basis for the series
   settings above.

During pilot 4's analysis, ad hoc unobserved runs were made and are not
retained as raw files:

- six runs 1 s apart gave W of 40.2 ms, then 73.3–79.1 ms;
- three back-to-back runs gave 39.3–43.8 ms;
- gaps of 0.2–12 s gave 60.8–77.6 ms.

The retained controls below replace them.

## Lineage, instancing and admission

All 27 observed `ok` invocations and the four timeout controls had one
client, one host, one worker and one validator each:

- The host's generation was distinct in every case: 27 distinct
  `(pid, creation time, p_uniqueid)` triples for 27 `ok` invocations.
- The worker's and validator's `p_puniqueid` matched the host's `p_uniqueid`.
- The reply's worker and validator PIDs matched the observed processes.
- Each host reported exactly two `NOTE_FORK` notifications.

launchd named every host's instance `pid/<client pid>/com.policywitness.policy-witness.PWRunner`,
and the client PID it named was the observed client every time. Its
spawn reason was `ipc (mach)`, through `xpcproxy`.

The overlapping pairs had their controllers spawned 1.35–1.89 ms apart:

- controller lifetimes overlapped by 72.1–83.2 ms;
- client lifetimes overlapped by 66.0–77.1 ms;
- host lifetimes overlapped by 49.5–58.9 ms;
- every pair reached two distinct, concurrently live host generations.

No reply in any series was `already_ran`, `xpc_error` or `bad_request`, and
no `runner_acquisition` refusal was recorded. These observations establish
per-client-process instancing for the shipped client, which opens one
connection. They do not test two connections from one client process.

## Retirement

For every host that replied (27 observed; 22 more in unobserved controls by
launchd's account alone), launchd logged the same sequence. At the client
domain's shutdown it logged "removing active service", then
`signaled service: Killed: 9`, `service state: SIGKILLed` and "scheduling
cleanup in 9 sec". Then it logged `exited due to SIGKILL | sent by launchd[1]
during teardown of process-scoped services after host exited`, where "host"
is launchd's term for the domain's owner, the client.

The host's own log has `invalidated because the client process (pid N) either
cancelled the connection or exited`, 0.84–1.41 ms before its exit.

Retirement intervals, in ms. Each row is minimum / median / p90 / maximum
across the separated (n=5), rapid (n=12) and overlap (n=10) series:

| Interval | Separated | Rapid | Overlap |
| --- | --- | --- | --- |
| last child exit → client exit | 3.424 / 3.683 / 3.844 / 3.844 | 3.203 / 3.429 / 3.491 / 3.775 | 3.436 / 3.553 / 3.706 / 3.784 |
| client exit → launchd kill message | 0.083 / 0.124 / 0.142 / 0.142 | 0.071 / 0.116 / 0.124 / 0.142 | 0.048 / 0.085 / 0.118 / 0.123 |
| launchd kill message → host exit | 0.496 / 0.556 / 0.593 / 0.593 | 0.421 / 0.867 / 0.907 / 0.968 | 0.481 / 0.611 / 0.653 / 0.665 |
| client exit → host exit | 0.620 / 0.687 / 0.699 / 0.699 | 0.534 / 0.989 / 1.031 / 1.089 | 0.544 / 0.679 / 0.748 / 0.770 |
| last child exit → host exit | 4.044 / 4.377 / 4.531 / 4.531 | 3.766 / 4.396 / 4.496 / 4.529 | 4.008 / 4.258 / 4.417 / 4.529 |
| controller exit → host exit | −0.064 / −0.052 / 0.053 / 0.053 | −0.607 / 0.459 / 0.486 / 0.490 | −0.104 / −0.065 / 0.000 / 0.075 |

Reply → host exit therefore lies between 0.53 and 4.53 ms in every observed
replied case. Within that bound the host exits about when the controller does. In the
rapid series, the next controller was spawned −0.291 to +0.255 ms from the
previous host's exit (n=11), and the next client was created 1.066–1.806 ms
after it. No new client was observed to coexist with a retiring host after a
successful reply.

## Timing and controls

Again minimum / median / p90 / maximum in ms:

| Interval | Separated (5) | Rapid (12) | Overlap (10) |
| --- | --- | --- | --- |
| W | 40.485 / 72.828 / 78.796 / 78.796 | 37.032 / 39.280 / 39.986 / 43.122 | 72.064 / 81.335 / 83.757 / 84.762 |
| C (whole ms) | 38 / 65 / 70 / 70 | 35 / 37 / 38 / 42 | 66 / 74.5 / 77 / 77 |
| client → host creation | 6.191 / 15.499 / 17.025 / 17.025 | 4.714 / 4.878 / 5.112 / 5.260 | 16.576 / 18.413 / 19.406 / 19.470 |
| host creation → exec | 3.056 / 7.186 / 8.307 / 8.307 | 2.503 / 2.591 / 2.772 / 2.772 (n=8) | 5.615 / 7.072 / 7.749 / 7.749 (n=8) |
| host exec → worker | 12.910 / 23.392 / 27.377 / 27.377 | 11.364 / 11.935 / 15.889 / 15.889 (n=8) | 25.120 / 29.488 / 31.014 / 31.014 (n=8) |
| host lifetime | 32.458 / 50.889 / 53.413 / 53.413 | 31.194 / 33.306 / 33.809 / 36.895 | 50.107 / 55.726 / 58.955 / 59.594 |

The exec observation is absent for 4 rapid and 2 overlap hosts. The poll
found those hosts before their `NOTE_EXEC` was read, so the exec time is
unobserved; it is not recorded as zero.

The separated W is bimodal. The second separated invocation took 40.485 ms,
and the other four 72.757–78.796 ms.
Controls without polling separate the observer from this effect:

| Control | W min / median / p90 / max |
| --- | --- |
| unobserved separated (5) | 74.832 / 80.899 / 81.959 / 81.959 |
| unobserved rapid (12) | 36.366 / 39.091 / 39.411 / 40.218 |
| unobserved separated with one busy core (5) | 38.887 / 40.844 / 41.891 / 41.891 |

Polling made no visible difference to rapid W (median 39.280 against
39.091 ms). The gap-dependent slowing appears without the observer and
disappears when one core is kept busy. That is consistent with a machine
idle-state effect, and not with host retirement: the separated series waits
for retirement to finish, yet is slower. The mechanism, such as frequency or
core scheduling, was not observed. Battery power is a condition here and was
not varied. The observer's longest poll gap was 11.3 ms (overlap; 3 gaps over
5 ms). Every validator was still observed.

## Abnormal path: client timeout

The control used the documented `--timeout-ms 22`, with no test override or
hang. In all four invocations the client gave up while the host was working:

- Each host was linked through launchd's domain for the observed client,
  because a timeout reply names no worker.
- launchd logged `signaled service: Terminated: 15` 0.060–0.065 ms after the
  client exit, `service state: SIGTERMed`, and "scheduling cleanup in 5 sec
  after sending Terminated: 15".
- Workers exited 0.04–3.06 ms after the client.
- Each host exited 3.165–3.407 ms after its last child, and 3.384–6.168 ms
  after the SIGTERM message.
- launchd recorded `exited due to SIGKILL | sent by PWRunner[<host pid>]`.
  The host process signalled itself.

PolicyWitness's host source sends signals only to its children, and its only
self-exit is `exit(0)`. The self-sent `SIGKILL` is therefore not from
PolicyWitness code; which library sends it was not established. No child
outlived its host. In three of four runs, the next invocation's client was
created 1.5–4.1 ms before the previous host exited. Both ran in separate
domains.

## Lifetime boundary

For the exercised cases:

- **Before the reply:** the worker and validator end. The host's own reply
  reported `reaped: true` for both. Independently, the later child's
  `NOTE_EXIT` preceded the client's exit by 3.2–3.8 ms and the host's exit by
  3.8–4.5 ms.
- **Between reply and host exit:** no owned process was observed to end.
- **After host exit:** none survived.

The host's shared region, pipes and other process-local resources are
released with the process. That is inferred from process exit; no separate
observation was made.

The host never ran its own exit path in these cases. Its 50 ms timer and
`exit(0)` did not run; launchd killed it, or it killed itself after SIGTERM.
Cleanup that depends on an orderly exit therefore did not occur, and its
absence is not visible in these outcomes. Reap of the worker and validator
before the reply is confirmed by two observers. Cleanup of everything else is
inferred.

## Agreement with the source-level model

Agreements:

- One request per host generation, no `already_ran`.
- A reply only after both children are reaped.
- A fresh worker per run (31 observed worker generations, all distinct).
- One validator per eligible phase.
- No built-in re-acquisition.

Disagreements and qualifications:

- **Exit timing:** the documented exit "50 milliseconds after replying" did not
  occur. The host was signalled within about 1 ms of client exit. Its observed
  lifetime after the reply is under 4.6 ms.
- **The single-use claim:** the claim never refused anything on the built-in
  path. launchd's per-client-process domains, not the claim, gave each
  invocation a fresh host.
- **Retirement races:** the known gap about connections racing retirement
  depends on a host serving more than one client. That was not observed for
  the built-in runner.
- **"Host work continues independently" after a client timeout:** this held
  only until the in-flight request finished, 3–7 ms here. launchd then had a
  5 s cleanup scheduled; work beyond that interval was not exercised.

## External runner

Untested. No BYOXPC runner was installed. Exercising one would require
installing a new persistent LaunchAgent signed with the Developer ID
identity, which the brief excluded. The one-second relaunch floor at the
host-generation boundary therefore remains a source and documentation
account: the generated `ThrottleInterval` and LIMITS.md's measurement on
macOS 14.8. A Mach service in a user or system domain is not a per-client
domain. Built-in observations do not predict its admission or retirement
sequence.

## Unresolved

- The exit time of a host whose client outlives the reply by more than 50 ms,
  where the scheduled `exit(0)` would come first, was not observed.
- launchd's behavior at its 5 s and 9 s "cleanup" timers is unknown,
  including whether it escalates SIGTERM to SIGKILL while host work
  continues, and whether children would then be orphaned.
- The worker's and validator's exit statuses in the timeout control are
  unavailable to a non-parent; the undeliverable reply was the host's only
  record.
- Two connections from one client process, extension issuers, exec
  descendants and multi-phase specimens were not exercised.
- Host creation → worker creation (14.0–38.8 ms across series) is not
  decomposed into launchd, `xpcproxy`, host startup, caller authorization,
  decode and spawn.
- The library that sends the self-`SIGKILL` after SIGTERM is not identified.
- The gap-dependent slowing has a supported condition (machine idle state)
  but no observed mechanism.

## Answers

1. **Yes, for all 27 observed `ok` invocations and the 4 timeout controls.**
   Each had a distinct `(pid, creation time, p_uniqueid)` host. The worker's
   and validators' `p_puniqueid` tie that host to the reply. launchd named an
   instance domain for each invocation's own client. Overlapping invocations
   ran on concurrently live, distinct hosts. The 22 unobserved invocations
   have launchd's spawn and kill messages, one each, but no host identity.
2. **The rule prevents a second `runSpecimen` reaching the same host process
   from executing.** That request would get `already_ran`, the host PID and no
   scheduled exit. It never triggered here. **The host actually exits when
   launchd signals it at the client's exit:** `SIGKILL` about 0.5–1.0 ms after
   a post-reply client exit. After a client timeout, it exits by self-sent
   `SIGKILL` 3.4–6.2 ms after launchd's SIGTERM. The 50 ms scheduled exit
   never ran.
3. **No observed constraint on the built-in path.** The next controller started
   within ±0.3 ms of the previous host's exit, and its client 1.07–1.81 ms after
   it. Rapid W was not larger than separated W. Overlaps reached separate hosts
   with no refusal. External invocations were not tested.
4. **What is shown:** the worker and validator were reaped before the reply,
   seen by the host and by an independent observer, and no owned process
   outlived any host. **What remains inferred:** release of the host's
   process-local resources. **What is unestablished:** behavior when host work
   outlasts launchd's SIGTERM cleanup timer, exec descendants and extension
   issuers.
5. **What can be measured at these boundaries:**
   - client creation → host creation: 4.7–19.5 ms;
   - host creation → exec: 2.5–8.3 ms;
   - host exec → worker creation: 11.4–31.0 ms;
   - reply → host exit: bounded between 0.53 and 4.53 ms; the host outlived
     its controller by at most 0.49 ms;
   - the 50 ms delay: not paid.

   The fresh-host boundary is measured in aggregate, inside the pre-worker
   intervals, and is not decomposed. Retirement is cheap and is not awaited.
   Whether the one-use claim and the scheduled delay are needed on the
   built-in path is not established: neither took effect in the observed
   cases, so these data cannot show what they prevent.

## Reproduction and cleanup

The procedure and limits are in [host-lifetime/README.md](host-lifetime/README.md).
Each series command appears in its `run-record.json` (`argv`). The analysis
reader is `analyze.py` (SHA-256 `0acd1c8c…7ca3`). Pilot summaries are under
`evidence/20261024T0412*`–`T0417*`. Pilot 1 has no launchd log, and pilots
1–2 have no clock identity, so their log-derived intervals are absent.

Cleanup:

- The harness waited for every owned process to exit before each series ended.
- The busy loop was killed and reaped (status −9).
- The checkout lock was released.
- No external runner was installed or removed.
- Five orientation runs and the ad hoc timing runs launched only ordinary
  invocations; their envelopes are not retained beyond the session scratch
  directory.
