# L relationship trace

Current behavior at `cf0136bbb6366d5f787c3547ec69d757772898c0`.
`l-facts.json` contains the seven hash comparisons, ten capability records and
fixed-tree retention index. It is compact committed evidence; no unavailable
raw capture is silently assumed.

| Claim site | Evidence/conditions | Existing binding and applicability judgment |
| --- | --- | --- |
| WORKER Launch observation L | Receipt L: run 20261018T223601Z_85d8418b, source f85c7b0, runtime a458b28, worker 4cb19db0; two empty allow-default workers, no extensions/queries, 20s selected sleep seams, timed external inspection | Dated census. Link/citation validation checks location, generated ownership checks copied graph prose; neither compares receipt identity or hashes to current code. Host/tool/launch conditions limit reuse. |
| WORKER Starting authority | Source citations to spawn/selection paths plus L's null stdio, protocol endpoints and matching ps outputs | Source pointer plus dated observation explicitly separate in prose. Reusing L as current coverage still requires judgment. Whole-document currency is not a new observation. |
| receipt worker-launch-observation.json | Seven source hashes, app-inventory hash, selected captures/final evidence and 59 artifact hashes | Committed record with no automated applicability check. Five changed source files: worker C, ABI, CWorker, launch_inventory.py, suite run.sh; orchestrator and run_capture unchanged. Current identity 1df328dc differs. Hashes identify represented bytes; receipt does not prove every relevant dependency captured. |
| capability s7 | launch_inventory plus terminal_exit_without_request | Generated identity/pointer checks plus two behavioral witnesses. Launch case requires identified worker, ready/completion/reap/absence; terminal-exit control covers its separate scope. |
| s13a | launch_inventory only | fd0 inventory contents depend on L; existing case does not assert descriptor identity. |
| s13b, s13c | launch_inventory plus host_setup check | L inventory plus independent setup controls of requested destinations, child descriptor metadata, argv and cleanup. Those controls do not establish shared-object identity. The separate host-setup oracle project is excluded here. |
| s14a, s15, s16g | launch_inventory only | Stdout/stderr, environment and cwd contents remain observation, not assertions. No exact fd set, null-device mode, cwd '/' or plain/environment ps equality assertion exists. |
| s16e, s16f | launch_inventory only | Mapping/port commands are attempted and their failures retained. Case does not assert vmmap success or lsmp refusal, nor complete mappings/Mach rights. |
| s17 | launch_inventory only | Actual behavioral assertion: pre-ready window records readiness rc -1/errno EPIPE after host ready deadline; worker completes with exit0, done and confirmed reap. This is more than a pointer. |
| catalog and CHANGE-VERIFICATION | Opt-in case, contaminated-worker dependency, signed app and same-user process observers | Registration/navigation checked; controls must be selected for actual evidence. Case's two observation windows are separate processes, not within-process before/after. |
| suite production launch inventory account | ps/lsof mandatory success; selected seam flag; identity, done, collection_after_reap, no wait errors and subsequent absence | Source assertions support this scoped account. vmmap/lsmp optional outcomes retained. About40s is existing account, not D1 measurement. |
| receipt/WORKER retention claims | Receipt calls run pinned; app inventory points to validator-selection-receipts-20261018 | Neither run appears in fixed RETAINED. This invalidates current availability/pin claim, not historical capture. D1 does not alter pins or reobserve. Selected committed content remains readable. |

The launch script additionally requires an unambiguous new worker PID, captures
within18s, exact20s override, CLI/runner success and clean exit. These assertions
do not imply the contents of an otherwise successful observer capture.

The original audit at51487f7 (WA-05 in historical initial-report) reported a
different worker build and missing provenance.69c7dfe supplies provenance and
conditions, not an automated rerun rule. Later changed identities do not falsify
the old census. They remove any automatic claim of current applicability.

No newly unasserted contents will be promoted to universal expectations in D1.
The paper design can register lifecycle assertions separately from census facts,
require review when represented support changes, and retain source/host/tool
scope in any acceptance decision. The exact fd/cwd/environment observations are
not promised invariant behavior and do not justify a new default native test.
