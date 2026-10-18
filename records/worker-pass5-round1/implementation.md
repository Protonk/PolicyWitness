# Implementation auditor — independent first report

Frozen revision: `5124b4309b6f7b0041c55318312a9ee18f579868`.

I preserved `implementation-initial.md` before opening `docs/WORKER.md`, `docs/architecture.json` or the capability map. Source, documentation, assertions and cited line numbers in this report refer to the frozen revision. I did not read the documentation plan, sibling reports or coordinator discussion, and did not build, run tests, change repository source/docs/tests, commit or start agents. This report is immutable after delivery; subsequent reproduction belongs in a separate file.

**Result:** one source-supported omission in the tour's cleanup limit. The endpoint-delivery and native-publication qualifications I challenged are largely already present and supported. No new implementation change is recommended from this read-only review alone.

## I1 — the descendant limit omits a same-group survivor after normal completion

**Label:** source-supported; not reproduced. **Impact:** documentation scope, with an experimentally relevant lifetime limit. A nominally successful exec attempt need not imply that the exec process group is empty. This does not show a sandbox escape or a false native leader-exit observation.

**Challenged sentence / omission.** `docs/WORKER.md:398–400` says:

> Known gap: an exec child's descendant that leaves the child's process group can outlive the run unobserved. The worker targets the child's process group when sending cleanup signals at the exec deadline and at cleanup.

The final Known gaps list repeats the leaving-the-group condition (`docs/WORKER.md:535`). The missing case is a descendant that **stays in the same process group, closes the captured streams, and outlives a normally exiting leader**. The preceding text correctly says cleanup is exceptional (`391–396`), and node S36b correctly permits a group to live “possibly beyond attempt/worker” (`134`). Thus this is an incomplete named limit, not a claim that every sentence or map row promises complete containment.

**Exact implementation branch.** In `controller/tools/pw_probe_runner/pw_probe_runner.c`, `attempt_exec_spawn` observes the leader with `waitid(...WEXITED|WNOHANG|WNOWAIT)` (`1044–1051`). It breaks the observation loop as soon as `child_exited && !stdout_open && !stderr_open` (`1053`). The only group-kill branch requires `deadline_expired || observation_errno || local_fault`, plus retained ownership (`1123–1130`). A natural leader exit with both streams at EOF has none of those conditions. The function then reaps only the leader (`1142–1152`) and reports its zero exit as slot success (`1179–1183`). There is no process-group absence observation or normal-path group termination. The host's `ChildProcessState` supervises the worker PID, not this exec descendant (`runner/Sources/PWRunnerCore/CWorker.swift:867–895,1359–1381`).

**Counterexample.** A helper leader forks a child in the inherited group; both close stdout/stderr; the leader exits zero without waiting for the child; the child remains responsive on a test-owned socket. The worker can see leader exit and EOF, reap the leader, publish `rc=0`, continue later steps and terminate while that child remains in the original group. No `setsid` or `setpgid` call is needed. The code path supports that expectation; the live outcome remains unobserved in this review.

**Actual assertions and what they do not assert.**

- `tests/suites/runner_exec_lifecycle/check_edges.py:43–44` establishes that the fixture leader and child initially share a group led by the leader.
- `closed_streams_continue` closes both peers' streams, checks they are still alive, and then deliberately releases both for normal termination (`46–52`). Its later `assert_stopped()` (`71–72`) follows that release.
- `leader_exit_descendant` exits the leader while the descendant retains the streams (`53–55`), then requires both exit observations and a deadline in the attempt error (`71–72,94–105`). This exercises the exceptional cleanup branch.
- The combined condition is absent from those branches. The C control independently asserts that EOF followed by leader exit permits `!group_kills`, exit code 0 and slot rc 0 (`tests/fixtures/worker_lifecycle/exec_control.c:149–156`), but models no surviving real descendant.
- The existing independent helper already supports both needed actions: command `c` closes stdout/stderr and acknowledges; command `x` exits immediately without waiting (`tests/fixtures/exec/helper.c:137–148`). Its forked child preserves the group (`154–168`). These are useful equipment capabilities, not proof the proposed combined run occurred.

**What would refute it.** A traced production path that observes/terminates remaining same-group members after leader exit plus both EOFs would refute the source claim. For the concrete probe, an independently observed descendant exit caused by PW before external fixture release/cleanup, with unchanged source and group identity, would refute the predicted survivor. An exit caused by the fixture's alarm, socket closure, test release or external cleanup would not.

**Smallest decisive probe.** Reuse the public allow-default exec specimen and existing `TreeControl`; obtain peer identities and register exit observations before intervention. Invoke `close_streams('P')`, `close_streams('C')`, then `exit_leader()`. Wait for the CLI to finish without fixture release. Before cleanup, require the leader exit event, ping the child, read its group ID and stable process identity, and compare it with the originally observed leader/group. Retain the envelope's exec status and following file effect independently. Then explicitly release/clean the surviving child and require its exit observation. Run a negative control that releases both peers and causes the child-liveness assertion to fail. No shipped implementation or helper edit is necessary; only a focused coordinator-owned driver is needed.

**Recommendation.** Broaden the prose and final gap list to say descendant lifetime is not fully observed: escaped descendants can survive exceptional group cleanup, and same-group descendants can survive normal leader/EOF completion. Keep node S36b's distinction between group signaling and absence proof. Add the combined lifecycle control if the follow-up reproduces the expected path. Do not change the attempt's leader status into a descendant claim or silently change cleanup behavior as part of a documentation repair.

## Deliberate challenges that did not produce additional findings

### Endpoint delivery: requested actions are not assumed to prove receipt

The initial account identified unchecked worker spawn action returns and the possibility that ordinary inheritance differs from exec-child isolation. The tour already names these (`docs/WORKER.md:284–336`), including the fd-0 overwrite and fd-4 self-dup observation; nodes S5/S6/S13b/S13c/S13d retain the relevant qualifications. The graph's terse W3/W5/W25 labels should be read with those node facts and the stated selected-edge scope, not as universal receipt assertions.

Source agrees: worker endpoint actions at `CWorker.swift:1091–1097` are unchecked, the evidence descriptor clear at `930–931` is unchecked, and the token channel is deliberately duplicated above fd 63 before endpoint placement (`1079–1089`). Issuer action/flag results are accumulated before spawn (`ExtensionIssuer.swift:86–104`), with a separate high duplicate (`77–80`). Actual worker token acceptance is subsequently published by `prepare_extension` (`pw_probe_runner.c:1268–1351`), not inferred from the host spawn result.

I inspected retained **native setup receipts**, not only their pass labels, in `tests/out/runs/worker-p4-setup-final/suites/runner_unit/host_setup_controls/artifacts/controls/`. `worker-collision.json` records child PID 68828 with identical object identity for fd 0 and fd 3 and absent fd 4. `worker_token-dup2.5.json` records a spawned/reaped child with a different fd-5 object after the injected action failure. `issuer-collision.json` retains its channel at fd 3. `worker-nosigpipe.json` has no spawn/child and cleanup observations. This is retained reproduction of the tour's existing caveats, not a new finding.

The checker requires intervention identity, real child PID/receipt, endpoint identity mismatch for injected dup failures, host reap, and cleanup evidence (`tests/suites/runner_unit/host_setup_controls.py:24–75`). Its rejected controls separately remove injection, child, reap and cleanup facts (`139–160`). I compared the two instrumented production input hashes and all six fixture/checker hashes in the retained snapshot with the frozen revision; all matched. This verifies the implicated bytes, not an exhaustive dependency or installed-library equivalence proof. I make no new whole-suite acceptance credit from that comparison.

### Cleanup on failure: the tour generally names calls and bounded observations

`docs/WORKER.md:50–56` explicitly distinguishes cleanup calls from retained native outcomes. Its host setup text preserves unchecked unlink failure and fixture-owned invalid-handle containment (`311–327`). The retained worker and issuer unlink receipts show names still present before fixture cleanup and separately recorded fixture removal. The production source itself ignores those unlink returns (`CWorker.swift:929`; `ExtensionIssuer.swift:66`). No absence claim is justified before the fixture's check/removal.

Extension preparation distinguishes failure stage and cleanup failure, closes once and does not infer absence after failed close (`pw_probe_runner.c:1273–1278,1290–1341`). The tour correctly says “attempts to close its descriptor once” (`423–426`), identifies early main refusals and erasure bypass paths (`434–443`), and does not claim a universal worker erasure receipt. The host session erasure scope is independently exercised by `ExtensionEvidenceTests.swift:127–142`; unconfirmed host reap keeps a published native token from delivery (`145–170`). The tests' injected wait/kill facts characterize handling, not a real failure of the native issuer API.

The shared child observer can block after successful termination and leave unconfirmed disposition on errors (`CWorker.swift:843–895`). The tour delegates execution budgets and ordering to their owners and does not itself promise a total lifecycle deadline. I1 is the additional cleanup limit the existing prose should name.

### Scope of native publication: ordinary summaries remain narrower than all native calls

The sentence “Its attempts record native operations and their outcomes” (`docs/WORKER.md:462–464`) is broad in isolation, but the tour's action table explicitly says `open_read`/`open_write` discard read/write/close returns (`353–356`). The Mach paragraph names attempted service-right deallocation and retained bootstrap reference (`402–409`). Source confirms both, and the wire contract explicitly states there is no general ordinary `attempt.native_rc` (`tests/FAILURE-PROPAGATION-CONTRACT.md:823–842`). I do not treat that isolated sentence as a substantive contradiction.

Publication scope is source-supported: `run_attempt` releases completion last (`pw_probe_runner.c:1413–1449`); the host does not decode incomplete slot payload (`CWorker.swift:1402–1411`); extension native results are exposed only for published slots (`CWorkerOrchestrator.swift:213–223`). The ordinary wrapper progress word is not an individual native-entry record. The extension marker precedes native entry, and native result fields follow native return (`pw_probe_runner.c:1363–1372`).

Actual assertion scope is stronger than mere citation: `check_killed_before_publication.py:95–102,126–170` obtains an independent filesystem observation, requires death/progress/publication facts, and requires `no_completed_result` with absent native rc/errno/path and unavailable comparison. Extension boundary assertions require a surviving marker but no native result after interruption (`check_extension_boundaries.py:230–235`). The live extension checker requires native consume/release results and independent read content/identity, while accepting either after-release read outcome (`check_extensions.py:78–98`). I reviewed these assertions but did not rerun or claim current live execution of them.

## Coverage worksheet

| Traced subject | Supported tour/map account | Assertion/evidence boundary and remaining limit |
| --- | --- | --- |
| Host setup, worker/issuer endpoints and inheritance | S1–S15, N1–N7; tour 229–248 and 284–336 distinguish mapping, descriptor, endpoint request, collisions and ambient inheritance. | Host setup checker and selected retained receipts examined; no universal inherited-state census. |
| Policy transport/bootstrap | Expected byte count, EOF receipt and pre-compile refusal in C 1671–1756; host uses one byte array at Swift 971–977,1152–1171. | Source traced. A successful write alone is not receipt. No new transfer execution credited. |
| Compile/parameters/capture/apply | S23–S28; tour 250–269 preserves pre-apply capture and private ownership uncertainty. | C 1758–1901 and host receipt gates 556–595 traced. No private API ownership inference. |
| Phase collection/release/attempt order | C wait 1487–1552 and host guards 1213–1343 match delegated ordering account. | Query-first builder traced; mutation/order suite not executed or fully audited here. |
| File/sysctl/Mach attempt resources | S29–S33, N9; tour action table distinguishes discarded returns, fresh-read payload and retained bootstrap right. | C call placement and payload traced; bare-deny assertions 209–224 prove their one input if executed, not all listed rows. |
| Exec resource timing and isolation | S34–S36, N12; pipes/handles acquired after apply; empty child environment and selected descriptors. | `exec_pipes_per_attempt` asserts 32 successful children under fd ceiling (run.sh 639–654); reuse evidence does not alone prove source placement or every cleanup call. |
| Exec lifetime/cleanup | Exceptional group signaling and independent leader/EOF facts supported. | I1: no combined same-group descendant/EOF/leader-exit control; source predicts survivor after nominal success. |
| Issuance/token delivery/erasure | S8–S12/S19–S22/S37; clean-reap eligibility, separate token channel and bounded erasure account supported. | Selected setup receipts plus test assertions inspected; kernel extension state and private retained allocations remain unknown. |
| Native call/return/publication | Tour 458–484 and action table supported within per-action scope. | Create-then-kill and extension assertion logic examined; no claim that a marker proves entry/effect or missing publication proves no effect. |
| Host teardown/late snapshots | Host owns exit request, grace/kill/reap and final acquire snapshot; partial immutable records survive. | CWorker 1346–1514 traced. Unchecked closes/unmaps, blocking final waits and unconfirmed cleanup remain limits. |
| Graph grounding | Worker graph matches the resource families traced, with explicit source/observation qualifications. | Generator 55–59,211–219 checks citation structure/presence/test definition; it does not prove behavioral coverage. No graph checker was run. |

## Comparison with my preserved initial account

The tour filled in more precise ambient-state and low-descriptor evidence than my initial source account supplied, and already acknowledged the unchecked endpoint and cleanup paths I expected to challenge. My initial account's phrase “The profile object remains until process death” was too strong: source proves no explicit PW free, while private `sandbox_apply` ownership changes remain unknown. The tour is more careful on that point (`260–262`, node S26a). I leave the initial file unchanged and record this correction here.

The one requested next action is the focused I1 reproduction. Agreement among reviewers would not substitute for it. The coordinator should preserve this report and initial account in tracked records, and retain any later execution and cleanup evidence separately.
