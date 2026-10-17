# BYOXPC coexistence and resource ownership: findings

This report answers the [investigation plan](BYOXPC-BAD-NEIGHBOR-INVESTIGATION-PLAN.md).
It records the resource map, the observed explanations for occupied claims and
the design determinations they support. The
[implementation plan](BYOXPC-COEXISTENCE-IMPLEMENTATION-PLAN.md) carries those
determinations into changes and acceptance checks.

## Applicability

| Item | Value |
| --- | --- |
| Source | `488308ad8c5b55a220dfd2002e70f67fe74869b0` with the `bad_neighbor_claims` case and `fixtures/byoxpc/neighbor_lab.py` sampler uncommitted; no production source changes |
| App | `dist/PolicyWitness.app` 0.3.1 build 684 (`2717a749`, `v0.3.1`); controller envelope 7, request 5, response 23 |
| Platform | macOS 26.7.1 (25G241), SDK 27.0, UID 501 logged into the GUI session |
| Runner plist | `RunAtLoad` true, `ThrottleInterval` 1 s, one `MachServices` entry equal to the label; no `KeepAlive` |

Live runs used the dispatcher outside the automation sandbox. Both claim runs
passed with an unchanged app and verified cleanup, and both are retained in
[RETAINED.json](RETAINED.json). Run 2 executed the committed case script; run 1 executed
an earlier version without schedules E and F. The committed sampler module omits
helpers both runs imported but never called.

| Run | Run ID | Content |
| --- | --- | --- |
| [byoxpc-neighbor-claims-2-20261017](out/runs/byoxpc-neighbor-claims-2-20261017/run.json) | `20261017T180458Z_4b0adfcf` | Schedules A–F below |
| [byoxpc-neighbor-claims-20261017](out/runs/byoxpc-neighbor-claims-20261017/run.json) | `20261017T180009Z_89f725f0` | Replicate of A–D |

Reproduce with:

```sh
PW_TEST_OUT_DIR=tests/out/runs/<fresh-name> tests/run.sh --case runner_byoxpc/bad_neighbor_claims
```

## Resource and lifetime map

A "runner name" is several distinct identities. Every row below is reachable by
any process running under the same UID; none is protected by the checkout lock.

| Resource | Namespace and identity | Acquired by, and what grants it | Who else can discover, use or release it | Durable ownership and staleness |
| --- | --- | --- | --- | --- |
| Default registry and its lock | `$HOME/Library/Application Support/PolicyWitness/runners.json` and `runners.json.lock` (flock) | `runner install`, `remove` and `validate` take `try_lock`; install holds it from the conflict check through signing, timestamping and bootstrap; remove holds it through bootout and up to 1 s of teardown polling | Every PW invocation using that `HOME`. `runner list` exposes every service name and bundle path. A second writer is refused immediately, without waiting | Records survive owner death; pending installation and pending cleanup are durable. Lock lifetime is the holding process |
| Fixture registry | Any path in `PW_RUNNER_REGISTRY` | Same lock code against a different inode | Only processes given that path | As above; `registry_recovery` uses this |
| Plist | `$HOME/Library/LaunchAgents/<service>.plist` | Exclusive creation inside install's lock | Readable and replaceable by the same UID | Ownership compares Label, ProgramArguments, MachServices and `XPC_SERVICE_PATH` |
| launchd job | Label `<service>` in `gui/<uid>` | `launchctl bootstrap gui/<uid> <plist>` | Listed by `launchctl list`/`print`. Any same-UID process can bootout, kickstart or replace it by label | Live ownership compares the observed `program`; removal then addresses the label |
| Mach service name | `<service>` in the per-user lookup namespace, which `launchctl(1)` calls flat across GUI/user | Advertised by the job's `MachServices` | Any same-UID process can look it up and connect. The session helper uses 12 random bytes, so collision is not the risk; advertisement is | None of its own; tied to the job |
| Service port receive right | Held by launchd while no host runs; lent to one host generation at a time | launchd spawn (at load, then on demand, at most once per `ThrottleInterval`) | Messages from any client queue in it. Clients that arrive while no host holds it wait for the next spawn | Observed: messages that arrive during throttle reach the next host |
| Host generation | `PWRunner` process, PID plus kernel start time | launchd spawn | Observable by `proc_pidinfo`; launchd's listing reports its PID | Exits 50 ms after its owner's reply; observed alive 45–123 ms after the requesting process exited |
| Host claim | `PWRunnerAdmission` in one host generation | First `runSpecimen` from any connection the host accepted | Any authorized caller. The host keeps accepting connections until it exits | Terminal. A refusal reports the host's PID, not who holds the claim |
| Caller authorization | Caller Team ID equals host Team ID; identifier in `PWRunnerAllowedIdentifiers` (`pw-runner-client`, `com.policywitness.policy-witness`) | Code signing of the caller | Every PW app signed by this team: other checkouts and other repos' copies | Says nothing about which session or registry a caller belongs to |
| Worker generation | `pw-probe-runner`, child of its host | Host spawn after a successful claim | Observable | Reaped before reply |
| Staging | `/private/tmp/pw-byoxpc-*` (mkdtemp), holding durable `session.json` | Session helper | Same UID | Durable cleanup record |
| Specimen effects | Test-owned paths | Specimen | Same UID | Per request |
| Checkout lock | `tests/.checkout.lock` | Dispatcher | Same checkout only | Not an ownership claim over anything above |

The session helper (`fixtures/byoxpc/session.py`) installs into the default
registry and the real `LaunchAgents`, so every runner it installs is listed by any
neighbor's `runner list`. `runner_select` connects to an external runner only on
an explicit `runner.id` or `runner.service`, so a neighbor reaches the session's
service only after learning the name. The registry is one advertisement channel;
`launchctl list` is another.

## Explanations for an occupied claim

`already_ran` is produced before decoding. Across every refusal in both runs the
reply carried no steps and no worker, and the request's effect file was absent.
The refusal establishes an occupied claim and no effect from the refused request.
It does not say who held the claim.

The case attributes each refusal from independent observations: a 1 ms libproc
sampler of host and worker generations (PID plus start time; ESRCH is the only
absence), the served worker's parent, and the host's own `com.apple.xpc` log
lines, which name every peer connection's PID (`...peer[<pid>]`). Constructed
checker controls reject PID reuse and an unknown holder before any live
schedule runs.

| Schedule | Arrangement | Observed (run 2; run 1 agrees) |
| --- | --- | --- |
| A. Spaced, no neighbor | Each request starts after the previous host is observed gone | 3/3 `ok`, three distinct host generations. Positive control |
| B. Public back-to-back, no neighbor | Each `policy-witness run --no-log-capture` starts when the previous one exits | 4 of 5 follow-on requests refused by the *previous* request's host, which the sampler saw alive at launch (run 1: also 4 of 5) |
| C. Shipped client after a reply, no neighbor | `pw-runner-client` again as soon as a served reply returns | 3/3 refused by the owner's host, alive at launch |
| D. Foreign client holds a host | Neighbor finds the service in `runner list`, holds a fresh host with `worker_post_apply_hang_ms`; session then requests | Session refused by the neighbor's host; neighbor `ok`; a later session request `ok` on a fresh host |
| E. Two clients queued during throttle | Neighbor then session connect 180–300 ms after the last spawn, inside `ThrottleInterval` | 2/2: the fresh host activated the neighbor's peer, then the session's 8 ms later, and refused the session |
| F. Registry lock contention | A fixture registry's lock is held; `runner remove` runs against it | Refused immediately: `runner registry busy or lock unavailable`; the same command without contention reaches its not-found result |

These schedules establish three separate occupied-claim mechanisms:

1. **Local retirement lag (inside the repo).** A host keeps accepting
   connections during its 50 ms exit delay and the teardown after it. A request
   that starts within roughly 45–120 ms of the previous request's exit reaches
   that host and is refused. Nothing in the session helper or the shared suite wrapper
   waits for host retirement between specimen leaves; only setup does, after
   verification. With default log capture the controller usually finishes later,
   which is consistent with the failure being intermittent rather than constant.
   No real-suite leaf timing has been measured.
2. **Foreign admission while a host runs (schedule D).** Any authorized caller
   that knows the name can take the claim of a running host.
3. **Foreign admission in the throttle queue (schedule E).** Each consecutive
   request waits about 1 s in launchd's queue for the throttled respawn
   (served latencies 1.08–1.20 s after a recent spawn, 0.13–0.18 s otherwise). A
   foreign peer that arrives first in that window takes the fresh host. This
   reproduces the record of the 2026-10-07 failure (`opt_metafilter_any`): a
   fresh host activating an unrecognized peer 5 ms before the test's own client.
   That run's output no longer exists, so the match is to the record, not to
   retained evidence. In that record the peer was "unidentified" partly because
   client PIDs were not captured.

Mechanism 1 needs no neighbor. Mechanisms 2 and 3 need a neighbor that knows the
name; the default registry hands it out. The fourth observed dependency,
registry lock contention (F), produces refusal of install or cleanup rather than
`already_ran`. Its duration is bounded by the holder's signing and bootstrap
time, and the code waits for none of it.

Not yet established: which channel an actual neighbor on this machine uses, and
how often mechanism 1 occurs in the real shared suite.

## Design determinations

**No dependence on launchd/libxpc queueing.** One candidate was to have a host
stop accepting connections after its first authorized peer, so later peers wait
in launchd's queue for the next generation. The SDK documents listener
suspension as non-preemptive. It does not say whether a peer libxpc has already
read survives the host's exit, and schedule E shows that peers arrive together
at spawn. If that behavior drifts, a waiting caller would see an interrupted
connection or a timeout instead of `already_ran`. That is no false pass, but the
refusal would no longer be provably pre-admission, and the failure would be
intermittent. The candidate was not pursued and its OS questions were not probed.

**Re-acquire a fresh host after a proven pre-admission refusal.** Every refusal
in both runs reported the refusing host's PID (the source sets it from
`getpid()` before the claim check) and carried no steps, no worker and no effect.
The sampler matched each refusing PID to a live process running the selected
runner's recorded executable. After that process was gone, the next connection
was served by a fresh generation (A, D's continuation, E's primers). Waiting for
the refusing generation to exit and connecting again therefore depends only on
PW's claim ordering and on launchd's on-demand spawn, which BYOXPC already
requires. Following a recent spawn, the wait costs little: the next request
waits about 1 s for launchd's throttle either way (A–E latencies).

**Test registries move; test plists cannot.** Developer ID signing fails when
`HOME` is redirected: `HOME=$(mktemp -d) codesign -f -s "Developer ID
Application: …" <file>` reports `no identity found`, and `runner install` under
a child `HOME` fails the same way before any plist or bootstrap. Signed
installs therefore keep the real `~/Library/LaunchAgents`, where a crashed
session's plist loads again at the next login. A per-session registry in
`/private/tmp` staging would not survive the reboot that follows, and the
leftover plist would then have no ownership record. `runner reconcile` still
reports such a plist as an unregistered candidate, but no tool may remove it by
name. The per-session registry needs a location that survives reboot. Removal
already uses the plist path recorded at installation, so removal needs only
`PW_RUNNER_REGISTRY`, not a redirected `HOME`.

**Default location needs its own live case.** No unit test resolves the default
registry or plist location; Rust selection and registry tests pass explicit
paths. Today only the shared BYOXPC installs exercise it live.

**Out of scope.** Whether a neighbor's job can advertise the session's Mach name
under another label, and whether a client-side peer requirement rejects a
foreign host, were not probed. With random service names neither has been
observed, and neither affects the selected design.
