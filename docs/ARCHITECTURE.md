# PolicyWitness architecture

A tour of the internals at the level between the [README](../README.md)'s
Flow paragraph and the directory READMEs: how one run unfolds in time and the
boundaries it crosses. It is for a developer or agent who has read the README
and is about to open a directory. It is not a field reference, a contract, a
module list, a test map or a build guide; each of those exists and is linked
from the section that would otherwise restate it.

The three figures are generated from [architecture.json](architecture.json)
by [generate_architecture.py](generate_architecture.py). Every node and edge in
a figure has an id, and the table beside the figure names, for that id, the
source symbol that implements it and the check that exercises it. The
generator verifies that each cited symbol exists in the named file; a
citation is a place to look, not a proof that the test asserts the whole
row. A node or edge is chased by its id, not by prose. The one figure that
is not a graph, the run timeline, is drawn by hand below and cites its
sources the same way. Behavior that falls short of a stated promise is
written where the promise is stated, in a paragraph that opens with "Known
gap", and indexed in the [last section](#known-gaps).

## Why these processes exist

Two facts about the macOS sandbox shape everything. `sandbox_check` answers
for a live process, and `sandbox_apply` is one-way: a process that has applied
a profile cannot shed it. A specimen therefore needs a process that applies
the policy and then stays alive long enough to be queried and to attempt
things, and that process cannot serve the next specimen. PolicyWitness spawns
one worker per specimen, applies the policy inside it, and queries it from
outside.

The reply path must stay outside the policy under test. A `(deny default)`
profile can deny the worker's own writes and even its exit, so the worker
never reports over a pipe after applying. It publishes into a shared region
the host mapped and pre-touched before the spawn, and the host, which never
applies anything, assembles the reply. The same split makes the worker's exit
status the source of truth about what happened to it, which is what the
[disposition record](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-disposition-record)
is built from.

The host is an XPC service that launchd starts for one specimen and that exits
shortly after replying, so no host state outlives a run. The controller is a
separate process so that an envelope is printed whatever the host does,
including never answering. The controller is Rust and `NSXPCConnection` is an
Objective-C API, so a small Swift client owns the connection
([why the launcher shells out](../controller/README.md#why-the-rust-launcher-still-shells-out)).

The validator is its own process so that `sandbox_check` runs unsandboxed
against the worker's PID while the worker is held between applying and
attempting. The observer runs the unified-log query in its own process group
under a budget, so a stalled `log show` is cut off and cleaned up without
touching execution evidence
([log collection budgets](../controller/README.md#log-collection-budgets-and-cleanup)).
`sbpl-check` compiles the policy in the controller's own context when the
client reported the runner unreachable (`xpc_error`), so the envelope still
carries a compile diagnostic, which matters inside an
[automation sandbox](../AGENTS.md#sandboxed-automation-harnesses). It
establishes nothing about how far a host or worker progressed before the
connection failed.

Exactly three processes call native sandbox APIs: the worker (compile and
apply), the validator (`sandbox_check`) and `sbpl-check` (compile only). The
controller, the client, the host and the observer do not, and for the host
that is enforced rather than assumed (see [Principles](#principles-as-enforced-constraints)).

## Process topology

Who starts whom, over what channel, with what lifetime. Locations are given
at the granularity of "app top level" and "inside the XPC bundle"; the exact
bundle paths are the contract in the README's
[What ships](../README.md#what-ships). The C worker and the validator sit
inside the XPC bundle so that the built-in runner and a BYOXPC copy each
resolve their own helpers relative to their own bundle.

<!-- BEGIN GENERATED ARCHITECTURE GRAPH topology -->
![Process topology](architecture-topology.svg)

*Figure: process topology. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [architecture-topology.dot](architecture-topology.dot). The ids in the figure are the ids in the tables below, and each row cites the source symbol that implements it and the check that exercises it.*

<details>
<summary>Process topology: 11 nodes and 12 edges, with their citations</summary>

#### Process topology nodes

| Id | Node | Kind | Where | Lifetime | Language | Started by | Sandboxed | Native sandbox API | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user | the caller | person | a shell or a harness | owns the request file and reads the envelope |  |  |  |  | [`pub fn run`](../controller/src/cli.rs) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| controller | policy-witness | executable | app top level | one run | Rust | the caller | no | none | [`fn main`](../controller/src/main.rs); [`cmd_run`](../controller/src/run_flow.rs) | [`consumer_controls`](../tests/suites/blackbox_e2e/checker_controls.py); [`EXECUTABLES`](../tests/lib/artifact.py) |
| client | pw-runner-client | executable | app top level | one run | Swift | the controller | no | none | [`readDataToEndOfFile`](../runner/Clients/PWRunnerClient/main.swift); [`NSXPCConnection`](../runner/Clients/PWRunnerClient/main.swift) | [`path_wire_fixtures_survive_capture_serialization_and_independent_consumer`](../controller/src/runner_client.rs); [`client_output_control`](../tests/suites/blackbox_e2e/checker_controls.py) |
| host | PWRunner | executable | inside the XPC bundle | one specimen; exits 50 ms after replying | Swift | launchd: XPC service lookup, or a Mach service for BYOXPC | no | none, by the invariance rule | [`NSXPCListener.service()`](../runner/Services/PWRunner/main.swift); [`runSpecimen`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`milliseconds(50)`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`host_invariance`](../tests/lib/artifact.py); [`check_host_invariance`](../tests/suites/source_drift/check.py); [`runServiceAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ServiceAdmissionTests.swift); [`worker_children`](../tests/suites/runner_byoxpc/opt_in/single_use.py) |
| worker | pw-probe-runner | sandboxed | inside the XPC bundle | until the host requests exit; spins after done | C | the host | yes; applies the specimen policy to itself | sandbox_compile_string, params, sandbox_apply | [`sandbox_compile_string`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`sandbox_apply`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh); [`CWorkerOrchestrator`](../tests/suites/runner_use_c_worker/run.sh) |
| exec_child | exec helper children | sandboxed | the caller's path | the worker's waits are bounded by the exec deadline and the attempt budget; a descendant that leaves the child's process group is not contained | caller-supplied | the worker | inherit the worker's sandbox | none of PolicyWitness's | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`runner_exec_lifecycle`](../tests/suites/runner_exec_lifecycle/run.sh); [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) |
| validator | sb_api_validator | executable | inside the XPC bundle | one batch | C | the host, after applied | no | sandbox_check | [`sandbox_check`](../controller/tools/sb_api_validator/sb_api_validator.c); [`SANDBOX_CHECK_NO_REPORT`](../controller/tools/sb_api_validator/sb_api_validator.c); [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`bothBinariesExist`](../runner/Tests/PWRunnerCoreTests/CWorkerValidatorTests.swift) |
| observer | sandbox-log-observer | executable | app top level | one scan | Rust | the controller, after execution completes, in its own process group | no | none | [`capture_sandbox_logs_with_timeout`](../controller/src/sandbox_log.rs); [`process_group`](../controller/src/log_capture.rs) | [`parsed_event_retains_pid_operation_and_raw_line_without_temporal_claims`](../controller/src/bin/sandbox-log-observer.rs); [`checked_reads`](../tests/suites/witness_contract/check_deny_capture_window.py) |
| log_show | log show | os | /usr/bin/log | one query | OS | the observer | no | none | [`Command::new("/usr/bin/log")`](../controller/src/bin/sandbox-log-observer.rs) | [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) |
| sbpl_check | sbpl-check | executable | app top level | one compile | Rust | the controller, only for an admitted xpc_error reply | no | sandbox_compile_string and params; never applies | [`sandbox_compile_string`](../controller/src/bin/sbpl-check.rs); [`run_policy_check`](../controller/src/policy_check.rs) | [`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`](../controller/src/run_flow.rs) |
| launchd | launchd | os | system |  | OS |  | no | none | [`NSXPCListener(machServiceName:`](../runner/Services/PWRunner/main.swift); [`MachServices`](../controller/src/runner_manager.rs) | [`runner_mach_service_liveness`](../tests/suites/runner_mach_service_liveness/run.sh); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |

#### Process topology edges

| Id | From | To | Kind | Edge | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | user | controller | channel | argv in; one JSON envelope on stdout | [`pub fn run`](../controller/src/cli.rs); [`print_envelope`](../controller/src/json_contract.rs) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py); [`envelope_shape_golden_agrees_with_the_manifest`](../controller/src/run_flow.rs) |
| T2 | controller | client | spawn | spawn; held request on stdin, read to EOF; reply on stdout | [`run_pw_runner_client`](../controller/src/runner_client.rs); [`readDataToEndOfFile`](../runner/Clients/PWRunnerClient/main.swift) | [`path_wire_fixtures_survive_capture_serialization_and_independent_consumer`](../controller/src/runner_client.rs); [`client_output_control`](../tests/suites/blackbox_e2e/checker_controls.py) |
| T3 | client | host | channel | NSXPC runSpecimen(Data) and its reply | [`NSXPCConnection`](../runner/Clients/PWRunnerClient/main.swift); [`runSpecimen`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`authorizedCaller`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`CWorkerOrchestrator`](../tests/suites/runner_use_c_worker/run.sh); [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh) |
| T4 | launchd | host | launch | start on XPC lookup, or as a Mach service (BYOXPC) | [`NSXPCListener.service()`](../runner/Services/PWRunner/main.swift); [`NSXPCListener(machServiceName:`](../runner/Services/PWRunner/main.swift); [`launchctl_bootstrap`](../controller/src/runner_manager.rs) | [`runner_mach_service_liveness`](../tests/suites/runner_mach_service_liveness/run.sh); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |
| T5 | host | worker | spawn | posix_spawn; fd 0 policy pipe, fd 3 shared region, fd 4 ready pipe | [`posix_spawn_file_actions_adddup2`](../runner/Sources/PWRunnerCore/CWorker.swift); [`F_SETNOSIGPIPE`](../runner/Sources/PWRunnerCore/CWorker.swift); [`writePolicy`](../runner/Sources/PWRunnerCore/MonotonicDeadline.swift); [`PW_SHM_ABI_MAGIC`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh); [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh); [`runPolicyTransferTests`](../runner/Tests/PWRunnerCoreTests/PolicyTransferTests.swift) |
| T6 | host | validator | spawn | posix_spawn --batch <pid>; NDJSON probes in, verdicts out | [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift); [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`transcript_controls`](../tests/suites/runner_validator_failure/run.sh) |
| T7 | validator | worker | native | sandbox_check against the worker PID, with SANDBOX_CHECK_NO_REPORT | [`sandbox_check`](../controller/tools/sb_api_validator/sb_api_validator.c); [`SANDBOX_CHECK_NO_REPORT`](../controller/tools/sb_api_validator/sb_api_validator.c) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`independent_worker_and_host_queries`](../tests/suites/runner_live_worker_identity/run.sh) |
| T8 | worker | host | channel | evidence published in the shared region with release ordering; proceed waited for before attempts | [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`CWorkerStepResult`](../runner/Sources/PWRunnerCore/CWorker.swift); [`proceedOffset`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`signal_while_waiting`](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift); [`order_barrier_mutations`](../tests/suites/witness_contract/opt_in/mutations.sh) |
| T9 | worker | exec_child | spawn | posix_spawn after apply; stdout and stderr pipes into bounded slot buffers | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`runner_exec_lifecycle`](../tests/suites/runner_exec_lifecycle/run.sh); [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh) |
| T10 | controller | observer | spawn | spawn in its own process group after execution; budget on argv; JSON report on stdout | [`capture_sandbox_logs_with_timeout`](../controller/src/sandbox_log.rs); [`capture_with_ops`](../controller/src/log_capture.rs); [`process_group`](../controller/src/log_capture.rs) | [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs); [`checked_reads`](../tests/suites/witness_contract/check_deny_capture_window.py) |
| T11 | observer | log_show | spawn | log show over the padded client span; text on stdout, bounded | [`Command::new("/usr/bin/log")`](../controller/src/bin/sandbox-log-observer.rs); [`capture_sandbox_logs_with_timeout`](../controller/src/sandbox_log.rs) | [`run_span_window_floors_start_ceils_end_and_never_collapses`](../controller/src/sandbox_log.rs); [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) |
| T12 | controller | sbpl_check | spawn | spawn only for an admitted xpc_error reply; held request in; helper envelope out | [`fallback_policy_check`](../controller/src/run_flow.rs); [`run_policy_check`](../controller/src/policy_check.rs) | [`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`](../controller/src/run_flow.rs); [`refused_reply_versions_request_no_fallback_compilation`](../controller/src/run_flow.rs) |

Notes:

- `host`: All authorized connections share one terminal, locked request claim. Only its owner schedules host exit; connections racing retirement can still fail before refusal.
- `T5`: Policy delivery uses nonblocking writes under one absolute monotonic deadline (the worker_policy_transfer limit) beginning after spawn. Expiry closes input and enters cleanup before readiness or sentinel polling.

Every node and edge above cites at least one check.

</details>
<!-- END GENERATED ARCHITECTURE GRAPH topology -->

## One run in time

The spine of the architecture is temporal. The host releases the worker's
attempts only after the validator's collection has closed, so every
prediction is made before any attempt is tried; that interval is the only
thing `comparison.order: "query_first"` claims
([the record](../tests/FAILURE-PROPAGATION-CONTRACT.md#the-record)). The
timeline below is the host driver's step list in
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift), the worker's
`main` in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c) and
the controller's `run` in [run_flow.rs](../controller/src/run_flow.rs), laid
side by side.

```text
controller / client            host (PWRunner)                  worker (pw-probe-runner)      validator
-------------------            ---------------                  ------------------------      ---------
read the request; version
gate; select the runner;
resolve augments; dossier;
strip selectors; serialize
the held bytes once
   |
   | client reads stdin to
   | EOF, then NSXPC
   | runSpecimen(Data)
   |-------------------------->| accept only an authorized caller
                               | decode with closed keys; capacity,
                               | then meaning; policy hash
                               | plan validator queries: drop pairs that
                               | cannot be predicted and paths that do
                               | not resolve on the host now
                               | zero the region; identity, counts,
                               | slots, params; pre-touch; prepared=1
                               | ready + policy pipes (CLOEXEC, NOSIGPIPE)
                               |-- posix_spawn, fds 0/3/4 -------->| map the region; refuse on magic
                               |-- policy bytes on fd 0 ---------->| or identity mismatch (exit 4);
                               |                                   | read the policy to EOF; params;
                               |                                   | compile; if asked, copy the compiled
                               |                                   | object into the capture region
                               |<--------- ready byte (fd 4) ------|
                               |                                   | sandbox_apply; applied=1
                               | acquire applied (apply_rc 0,      |
                               | identity match)                   |
                               |-- posix_spawn --batch <pid> --------------------------------->|
                               |-- probes on stdin ------------------------------------------->| sandbox_check
                               |<--------------------------------------------- verdicts (NDJSON)| per probe
                               | hook returns; collection closed;  |
                               | proceed=1 (release)               |
                               |                                   | wait_for_proceed (budget;
                               |                                   | failure code 8 on expiry)
                               |                                   | proceed_observed=1
                               |                                   | attempts in plan order; exec
                               |                                   | children are spawned here;
                               |                                   | completed=1 per slot (release)
                               |                                   | done=1; spin
                               | poll: done, reaped, sentinel      |
                               | deadline, or wait error           |
                               | exit_requested=1 ---------------->| _exit(0)
                               | grace; SIGKILL fallback; waitpid  |
                               | final acquire snapshot; decode
                               | evidence; classify; disposition
                               | record; ordering; per-step query,
                               | attempt and comparison; encode,
                               | degrading if the reply cannot be
                               | built
   |<--------------------------| reply; exit 50 ms later
   | admit the reply version
   | sbpl-check, only for xpc_error
   | complete execution (the
   | disposition projection)
   | observer over the padded client
   | span, in its own process group,
   | runs log show; correlation
   | envelope on stdout
```

Where each phase is pinned:

- **Controller admission and selection.** `run` in
  [run_flow.rs](../controller/src/run_flow.rs): the manifest is loaded once,
  then `parse_request`, `validate_request_version`, selector parsing,
  `resolve_runner_target_with_registry`, `resolve_augments`, the dossier, and
  `strip_runner_selector` before the held bytes are serialized. Checked by the
  `orchestration` tests in the same file.
- **Caller authorization.** `authorizedCaller` runs when the connection is
  accepted, before any request is read
  ([PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)).
- **Host admission.** `runSpecimen` decodes with closed keys, then
  `admissionFailure(for:)` (capacity), `requestMeaningFailure` (meaning) and
  `computePolicyHash`, in that order; a refusal replies without spawning
  anything. Checked by `runner_outcome_bad_request` and `failure_boundaries`.
- **Query planning.** `planValidatorQueries` runs before the spawn. It drops
  a query whose operation and filter pair cannot be predicted, and a path
  query whose target does not resolve on the host at that moment
  (`path_unresolved_at_planning`); the decision holds for the run even if an
  attempt later creates or removes the target, and the step still receives
  an explicit `prediction_unavailable` observation. Checked by `runner_unit`
  and the planner rule in `source_drift`.
- **Spawn and apply.** Steps 1 to 8 of the driver's comment in
  [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) and steps 2 to
  7 of the worker's. The ready byte has its own window
  (`readyByteTimeoutMs`); `runner_ready_byte_resilience` checks it.
- **Compiled-object receipt.** When the request opts in, the worker copies
  the compiled object into the capture region before applying it
  (`pw_capture_profile`). The host admits that copy only after successful
  application, worker completion, PID, nonce, input identity and payload
  integrity checks (`decodeProfileCapture`); the
  [guide](PolicyWitness.md#compiled-object-receipt-opt-in) distinguishes it
  from a kernel readback. Checked by `AppliedProfileCaptureTests`.
- **The barrier.** The validator runs inside the `postApplied` hook of
  [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
  with the worker's PID, or not at all when no step has a predictable
  query. `proceed` is stored when the hook returns; the worker's
  `wait_for_proceed` refuses to attempt anything before it. `PWRunnerOrdering`
  records what was observed. Checked by `OrderingTests` and the opt-in
  `witness_contract/order_barrier_mutations` control
  ([OPT_IN_TESTS.md](../tests/OPT_IN_TESTS.md)).
- **Attempts and publication.** `run_attempt` writes each slot and releases
  `completed`; an exec attempt acquires its pipes and spawn handles after
  apply and releases them before its slot completes. Checked by
  `runner_c_worker_harness` and `runner_exec_lifecycle`.
- **Exit, grace and kill.** Steps 9 to 11 of the driver's comment;
  `runner_outcome_runner_timeout/host_kills_hung_worker` checks the kill path
  and `runner_use_c_worker` the ordinary one.
- **Reply and envelope.** `reply_version` admits the reply or retains it
  unread; `fallback_policy_check` runs only for an admitted `xpc_error`;
  `complete_execution` projects the disposition; `attach_sandbox_logs` adds
  log evidence without touching execution fields. Checked by the Rust unit
  tests named in the boundary tables below.

What a reply does not establish: the client's timeout ends the controller's
wait and yields a synthetic `xpc_timeout` reply, and it cancels nothing in
the host. The host's cleanup can fail: `terminate` makes one blocking wait
after a successful kill request, and when no reap is confirmed the
collection basis reads `execution_may_continue` rather than
`after_confirmed_reap`. The worker kills an exec child's process group; a
descendant that leaves that group is not contained. The
[failure evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#host-observations)
adds no global lifecycle deadline, so a reply, the end of observation and
the end of execution are three different moments, and each record says
which one it describes.

Each budget covers one phase and no more. Policy delivery has its own
absolute monotonic deadline, started immediately after the spawn; the ready
window covers only the wait for the ready byte after
the policy has been written; the sentinel deadline covers application
through `done`, less the collection interval, because the host runs the
hook synchronously between polls and the hook's time is outside it; the
validator I/O deadline covers collection; the proceed budget covers the
worker's wait for release; the grace timer covers exit request to kill; the
exec deadline and attempt budget cover the worker's waits on exec children,
per step and per plan; the log budget covers the observer. The ready and
sentinel budgets are iteration counts over a sleep interval, not wall-clock
guarantees in either direction. Their values and their checks are in
[LIMITS.md](LIMITS.md).

The host sends policy bytes through a nonblocking pipe under the delivery
deadline (`writePolicy` and `MonotonicDeadline` in
[MonotonicDeadline.swift](../runner/Sources/PWRunnerCore/MonotonicDeadline.swift)).
Partial writes, interruptions and backpressure consume the same allowance.
Expiry records `policy_transfer_timeout` separately from any write errno,
closes input and enters cleanup without starting readiness or sentinel polling.
Counts describe accepted writes, not child receipt. `PolicyTransferTests`
checks a stalled reader, exact draining delivery, deadline edge cases and
cleanup failures; the actual driver replies pass through controller assembly
and the independent consumer. The deadline does not bound final reap or cancel
an earlier client timeout.

## Evidence channels and ownership

Seven channels reach the envelope. Each native result has one writer. The
host adds its own observations beside a native result and overwrites none of
them, and the controller does the same with the host's.

| Channel | Native result written by | Host adds | Where it lands | What it is |
| --- | --- | --- | --- | --- |
| Prediction | the validator | an explicit `prediction_unavailable` observation for a step the planner excluded; path diagnostics after orchestration | `steps[].sandbox_check` | one `sandbox_check` verdict per predicted step |
| Attempt | the worker, through the shared region | the lifecycle copies; path diagnostics after orchestration | `steps[].attempt` | the attempted operation's own result, with `rc` and `errno` |
| Comparison | the host | nothing further | `steps[].comparison` | the attempt's classified observation, the submitted-scope relations, the order established, and the limitations |
| Disposition | the host, from raw facts it cites | the controller's projection | `runner_subprocess.disposition`; `data.runner_sandbox_diagnostics` (execution fields) | what happened to the worker process, answered only from the cited facts |
| Compiled-object receipt | the worker, before apply, when asked | admission after application, completion, PID, nonce and integrity checks | `applied_profile` | a copy of the compiled object; not a kernel readback |
| Dossier | the controller | nothing further | `data.specimen` | the request as submitted, augmentation and imports, host facts, runner and app provenance, binary hashes observed before invocation |
| Log capture | the observer | the controller's correlation fields | `data.sandbox_log_capture`; `data.runner_sandbox_diagnostics` (log fields) | deny records the unified log showed in the padded window, with candidate associations; never a verdict |

The rule that holds the channels apart: log evidence never changes execution
evidence. The assembly seam is `attach_sandbox_logs` in
[run_flow.rs](../controller/src/run_flow.rs), where the collector receives
read-only execution evidence and returns only log-owned fields; the unit test
`collector_states_preserve_the_serialized_execution_half` checks it, and the
controller README's
[ownership table](../controller/README.md#execution-and-log-evidence-ownership)
names the owner of every field. The host's additions are
`enrichPathDiagnostics` in
[PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
and the planner's synthesized observations in
[CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift).
No record asserts agreement or disagreement between the prediction and
attempt channels; the reading rules for the comparison record are in the
[failure evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record).
The normative semantics of the reply live in that contract, under `tests/`;
this document links it wherever it needs a rule and never restates one.

## Boundaries

Each node below is a record that crosses from one owner to another, and each
edge is the guard that lets it cross. [contract.json](contract.json) owns the
three wire numbers and the build generates one source identity
([CONTRACT.md](CONTRACT.md)); four records carry a local version field of
their own, each read by exactly one receiver (the observer report, the
evidence manifest, the runner registry and the compiled-object receipt), and
the node table names them. Every other boundary is held by a golden, a
suite, or by being built and shipped together, and the edge table says which.

<!-- BEGIN GENERATED ARCHITECTURE GRAPH boundaries -->
![Boundaries and their guards](architecture-boundaries.svg)

*Figure: boundaries and their guards. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [architecture-boundaries.dot](architecture-boundaries.dot). The ids in the figure are the ids in the tables below, and each row cites the source symbol that implements it and the check that exercises it.*

<details>
<summary>Boundaries and their guards: 12 nodes and 12 edges, with their citations</summary>

#### Boundaries and their guards nodes

| Id | Node | Kind | Owner | Form | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| request_file | request JSON | record | the caller | a JSON file naming the request schema | [`parse_request`](../controller/src/request_patch.rs) | [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh) |
| held_request | held request bytes | record | the controller | one serialization; selectors stripped, augments spliced | [`strip_runner_selector`](../controller/src/runner_select.rs); [`pub fn resolve_augments`](../controller/src/augments.rs) | [`invalid_request_version_stops_before_selection_augments_or_client_invocation`](../controller/src/run_flow.rs) |
| run_spec | decoded request (PWRunnerRunSpec) | record | the host | Codable with closed keys | [`PWRunnerRunSpec`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`CodingKeys`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh); [`admission`](../tests/suites/failure_boundaries/check.py) |
| shm_region | shared region and policy pipe (worker ABI) | record | host writes inputs, worker writes outputs | fixed layout; magic at byte 0, source identity at byte 64 | [`PW_SHM_ABI_MAGIC`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PW_WORKER_ABI_IDENTITY_HEX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PWShmLayout`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh); [`PW_SHM_`](../tests/fixtures/contract/abi_layout.txt) |
| validator_wire | validator NDJSON (probes and verdicts) | record | host and validator, co-shipped in one bundle | NDJSON; kind sb_api_validator_verdict; no version marker | [`sb_api_validator_verdict`](../runner/Sources/PWRunnerCore/ValidatorClient.swift); [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift); [`sandbox_check`](../controller/tools/sb_api_validator/sb_api_validator.c) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`validator_overlong_request`](../tests/suites/failure_boundaries/check.py) |
| reply | runner reply (PWRunnerRunResult) | record | the host | response schema; shape golden | [`PWRunnerRunResult`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`PWContract`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`replyShapeDocuments`](../runner/Tests/PWRunnerCoreTests/ContractVersionTests.swift); [`schema_version`](../tests/fixtures/contract/response_shape.json) |
| profile_capture | compiled-object receipt (applied_profile) | record | the worker, before apply; admitted by the host | opt-in copy of the compiled object with a nonce; its own schema_version on AppliedProfileCapture | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`AppliedProfileCapture`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`runAppliedProfileCaptureTests`](../runner/Tests/PWRunnerCoreTests/AppliedProfileCaptureTests.swift) |
| envelope | controller envelope (kind run) | record | the controller | envelope frame; shape golden | [`SCHEMA_VERSION`](../controller/src/json_contract.rs); [`render_envelope`](../controller/src/json_contract.rs); [`complete_execution`](../controller/src/run_flow.rs) | [`envelope_shape_golden_agrees_with_the_manifest`](../controller/src/run_flow.rs); [`_validate_observer_reply`](../tests/lib/consumer.py); [`observer_admission_precedes_all_body_interpretation`](../controller/src/sandbox_log.rs); [`observer_controls`](../tests/suites/blackbox_e2e/checker_controls.py) |
| observer_report | observer report (nested envelope) | record | the observer | envelope frame; its own observer_schema_version (OBSERVER_SCHEMA_VERSION) inside | [`OBSERVER_SCHEMA_VERSION`](../controller/src/bin/sandbox-log-observer.rs) | [`parsed_event_retains_pid_operation_and_raw_line_without_temporal_claims`](../controller/src/bin/sandbox-log-observer.rs); [`checked_reads`](../tests/suites/witness_contract/check_deny_capture_window.py) |
| helper_envelope | sbpl-check envelope (nested) | record | sbpl-check | envelope frame; kind sbpl_check | [`run_policy_check`](../controller/src/policy_check.rs); [`sandbox_compile_string`](../controller/src/bin/sbpl-check.rs) | [`_validate_policy_check_reply`](../tests/lib/consumer.py); [`policy_check_controls`](../tests/suites/blackbox_e2e/checker_controls.py) |
| evidence_manifest | evidence manifest (in the app) | record | the build | hashes and entitlements of every shipped binary; its own schema_version (EVIDENCE_SCHEMA_VERSION) | [`manifest.json`](../tests/build-evidence.py); [`EVIDENCE_SCHEMA_VERSION`](../controller/src/evidence.rs) | [`codesign.preflight`](../tests/suites/preflight/run.sh); [`VALIDATOR_REL`](../tests/suites/witness_contract/check_dossier.py) |
| runner_registry | runner registry (BYOXPC installs) | record | the runner commands | additive-field loader; retired kind aliases kept for recovery; its own schema_version (RUNNER_REGISTRY_SCHEMA_VERSION) | [`load_registry`](../controller/src/runner_manager.rs); [`RUNNER_REGISTRY_SCHEMA_VERSION`](../controller/src/runner_manager.rs); [`alias = "machme"`](../controller/src/runner_manager.rs) | [`legacy_machme_kind_deserializes_as_byoxpc`](../controller/src/runner_manager.rs); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |

#### Boundaries and their guards edges

| Id | From | To | Kind | Edge | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | request_file | held_request | guard | request version gate; selector parse; augment resolution | [`validate_request_version`](../controller/src/request_patch.rs); [`parse_runner_selector_value`](../controller/src/runner_select.rs); [`pub fn resolve_augments`](../controller/src/augments.rs) | [`invalid_request_version_stops_before_selection_augments_or_client_invocation`](../controller/src/run_flow.rs); [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh) |
| B2 | held_request | run_spec | guard | caller authorization; closed-key decode; capacity, then meaning; policy hash | [`authorizedCaller`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`CodingKeys`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`admissionFailure(for`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestMeaningFailure`](../runner/Sources/PWRunnerCore/ProbeRunner.swift); [`computePolicyHash`](../runner/Sources/PWRunnerCore/SandboxApply.swift) | [`admission`](../tests/suites/failure_boundaries/check.py); [`NormalizedOutcome.badPolicy`](../runner/Tests/PWRunnerCoreTests/EnvelopeInvariantTests.swift) |
| B3 | run_spec | shm_region | guard | host writes identity, counts, slots, params; worker refuses on magic or identity mismatch (exit 4) | [`abiIdentityHex`](../runner/Sources/PWRunnerCore/CWorker.swift); [`PW_WORKER_ABI_IDENTITY`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`return 4`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh); [`independent_worker_and_host_queries`](../tests/suites/runner_live_worker_identity/run.sh); [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh) |
| B4 | shm_region | reply | guard | release/acquire publication; proceed before attempts; disposition record from raw facts | [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`proceedOffset`](../runner/Sources/PWRunnerCore/CWorker.swift); [`PWRunnerOrdering`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | [`signal_while_waiting`](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift); [`order_barrier_mutations`](../tests/suites/witness_contract/opt_in/mutations.sh) |
| B5 | run_spec | validator_wire | guard | planned probes; strict NDJSON decode; association by unique id | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`transcript_controls`](../tests/suites/runner_validator_failure/run.sh) |
| B6 | validator_wire | reply | guard | verdict joined to its step, or an explicit unavailable prediction | [`ComparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`sb_api_validator_verdict`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`transcript_controls`](../tests/suites/runner_validator_failure/run.sh); [`CWorkerOrchestrator`](../tests/suites/runner_use_c_worker/run.sh) |
| B7 | reply | envelope | guard | exact response version; disposition validated and projected; reply retained unread when refused | [`reply_version`](../controller/src/run_flow.rs); [`complete_execution`](../controller/src/run_flow.rs); [`execution_diagnostics`](../controller/src/disposition.rs); [`validate_disposition`](../controller/src/disposition.rs) | [`reply_versions_are_gated_exactly`](../controller/src/run_flow.rs); [`disposition::tests::`](../tests/suites/blackbox_e2e/disposition_controls.py) |
| B8 | observer_report | envelope | guard | nested unchanged; log evidence never changes execution evidence | [`attach_sandbox_logs`](../controller/src/run_flow.rs); [`admitted_observer`](../controller/src/sandbox_log.rs); [`OBSERVER_SCHEMA_VERSION`](../controller/src/bin/sandbox-log-observer.rs) | [`collector_states_preserve_the_serialized_execution_half`](../controller/src/run_flow.rs); [`_validate_observer_reply`](../tests/lib/consumer.py); [`observer_admission_precedes_all_body_interpretation`](../controller/src/sandbox_log.rs); [`observer_controls`](../tests/suites/blackbox_e2e/checker_controls.py) |
| B9 | helper_envelope | envelope | guard | nested unchanged; admitted by kind and frame version | [`fallback_policy_check`](../controller/src/run_flow.rs); [`_validate_policy_check_reply`](../tests/lib/consumer.py) | [`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`](../controller/src/run_flow.rs); [`policy_check_controls`](../tests/suites/blackbox_e2e/checker_controls.py) |
| B10 | evidence_manifest | envelope | guard | dossier compares selected binaries with manifest baselines; lookup by exact path and kind | [`unique_typed_entry`](../controller/src/evidence.rs); [`pub struct Binaries`](../controller/src/dossier.rs) | [`codesign.preflight`](../tests/suites/preflight/run.sh); [`VALIDATOR_REL`](../tests/suites/witness_contract/check_dossier.py) |
| B11 | runner_registry | held_request | guard | selection resolves a BYOXPC target; selector fields stripped before XPC | [`resolve_runner_target_with_registry`](../controller/src/runner_select.rs); [`strip_runner_selector`](../controller/src/runner_select.rs); [`load_registry`](../controller/src/runner_manager.rs) | [`legacy_machme_kind_deserializes_as_byoxpc`](../controller/src/runner_manager.rs); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |
| B12 | profile_capture | reply | guard | admitted only after successful application, worker completion, PID, nonce, input identity and payload integrity checks | [`decodeProfileCapture`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runAppliedProfileCaptureTests`](../runner/Tests/PWRunnerCoreTests/AppliedProfileCaptureTests.swift) |

Notes:

- `validator_wire`: The wire carries no version marker. In the shipped bundle the host and validator are built and signed together and the validator_batch_mode suite checks the shape; the identity digest excludes the validator and the validator_executable_path test seam can pair the host with another validator, so co-shipping is the arrangement, not a guard.
- `B8`: The receiver admits the exact kind, outer envelope version and inner report version before interpretation. Rejected JSON remains opaque; independent transport and execution evidence survive.
- `B11`: Known gap: the installer signs the XPC bundle without --deep, so the supplied entitlements are embedded in the host executable only and that is what the registry records; the embedded worker keeps its build signature, which carries no entitlements.

Every node and edge above cites at least one check.

</details>
<!-- END GENERATED ARCHITECTURE GRAPH boundaries -->

The three nested envelopes (`data.policy_check.envelope`,
`data.sandbox_log_capture.observer` and the controller's own) share the
[envelope frame](CONTRACT.md#what-each-number-identifies), so one version
number covers the controller family, and the observer's report carries its
own number inside the frame.

The observer receiver in [sandbox_log.rs](../controller/src/sandbox_log.rs)
admits `sandbox_log_observer_report`, the exact envelope version and the
supported inner report version before reading report semantics. Rejected
JSON remains under `observer` as opaque evidence. An intact, completely
delivered rejected report yields `invalid_reply`; independent transport
failure keeps its own precedence. No rejected body supplies events, blocked
reasons, correlation or missing-record conclusions. Rust receiver/assembly
controls and Python consumer controls check these boundaries while preserving
serialized execution fields. The helper receiver follows its corresponding
kind/version gate in [policy_check.rs](../controller/src/policy_check.rs).

## Principles as enforced constraints

The six core ideas in [AGENTS.md](../AGENTS.md#core-ideas) are operating
instructions. Each is also a constraint on a particular phase above, and each
has a mechanism that enforces it.

- **One-way sandbox per process.** Every authorized connection shares the
  host's `PWRunnerAdmission` in
  [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift).
  Its locked claim is terminal from the first request's entry, including a
  malformed or refused request. Later requests receive `already_ran` without
  orchestration or exit scheduling. Only the owner schedules exit after the
  normal 50 ms reply-flush delay. Service tests observe entry and retirement
  separately; `runner_byoxpc/single_use` checks two shipped clients, the held
  host's worker relationship, refusal without a file effect, owner completion
  and successful service from a fresh host. A connection racing retirement
  can still fail before refusal; no queue or automatic retry is promised.
- **Host/worker split.** The host never links, loads or calls libsandbox.
  Enforced twice: `check_host_invariance` in the `source_drift` suite rejects
  any binding under `runner/Sources/`, and `host_invariance` in
  [artifact.py](../tests/lib/artifact.py) runs `nm -u` on the shipped host
  before any app-dependent suite runs.
- **Witness over interpretation.** An attempt's `rc` is never the claim; the
  comparison record names its `observation_basis`, and
  [consumer.py](../tests/lib/consumer.py) re-derives every step's expected
  observation from the raw channels before accepting an envelope.
- **Predictions precede attempts.** `proceed` and `proceed_observed` in the
  shared region, `collection_closed_before_proceed` in `PWRunnerOrdering`,
  and the worker's `wait_for_proceed`. Checked by `OrderingTests` and the
  opt-in order-barrier mutation control, which must be rerun whenever the
  wait, the release store or the eligibility rule changes.
- **No dishonest attribution.** No outcome spelling claims a sandbox cause: a
  signal is `runner_failed` with the signal preserved, and
  `termination_cause` is projected only from a disposition record whose cited
  facts support it (`CAUSE_FOR_TRIGGER` in
  [disposition.rs](../controller/src/disposition.rs)). Log correlation is a
  separate observation with its own `correlation_status`. The pre-apply
  witness case forbids `ok`, `bad_policy` and the two spellings no constant
  defines,
  outright.
- **Runner simplicity.** Host orchestration is `PWRunnerService.swift` and
  `CWorkerOrchestrator.swift`; everything after apply is the C worker, which
  allocates nothing after `sandbox_apply` because the host pre-touched every
  page of the region before the spawn. Hidden pre-sandbox acquisition is the
  thing the exec attempt machinery avoids: its pipes and spawn handles are
  acquired after apply, inside the attempt, and released before the slot
  completes.

## How the system verifies itself

The suites are listed in [tests/README.md](../tests/README.md#suite-coverage);
this section names the mechanisms they are built from.

- **Goldens.** `response_shape.json` and `envelope_shape.json` under
  `tests/fixtures/contract/` record every key a reply or envelope can carry
  and its type, collected from field-complete fixtures; they are also the
  readers' allowlists. `abi_layout.txt` is the compiled harvest of the
  worker ABI's sizes and offsets. A difference writes a candidate; replacing
  the golden with the reviewed candidate is the acknowledgement
  ([shape goldens](CONTRACT.md#shape-goldens)).
- **Generators with marked regions.** Four manifests own numbers, limits,
  figures and the identity; four generators copy them into marked regions of
  documents and sources, and each has a check mode that the build or a
  drift case runs. Nothing reads a manifest at run time.
- **Source-drift rules.** Mechanical checks over text that is not generated:
  the host invariance rule, the sandboxed-harness note carried in three
  places, the CLI surface block against the usage text, one coverage row per
  outcome constant, the suite table against the suite directories and the
  catalog, and the test-seam table against `PWRunnerTestOverrides`.
- **The consumer.** [consumer.py](../tests/lib/consumer.py) gates an
  envelope on exact versions, validates every step against its raw channel
  fields through the goldens, and selects steps by field; it is the reader
  the suites share and the reader an external consumer is expected to copy.
- **The test seam.** `_test_overrides` is the only way a test reaches inside
  a run: deadlines, hangs, a self-signal, and replacement worker or
  validator executables, each honored and echoed in the reply. The supported
  keys are the table in [runner/README.md](../runner/README.md), locked to
  the Swift type by a drift rule, and the four-assertion recipe for using
  them is in [runner/AGENTS.md](../runner/AGENTS.md).
- **The C harness.** `runner_c_worker_harness` drives the real worker
  through the shared-memory ABI from a C program with no host, so the
  worker's publication and failure paths are pinned independently of the
  Swift driver.
- **The lifecycle oracle.** [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py)
  constructs envelopes from worker records and raw facts and checks that the
  disposition projection says only what those facts support, with disabled
  log fields so no log evidence can decide a lifecycle claim.
- **The dispatcher's artifact check.** Before any app-dependent case runs,
  the dispatcher verifies the bundle layout against `EXECUTABLES`, the
  signatures, the embedded evidence hashes and the host's undefined symbols;
  fixture bundles with a damaged seal or a sandbox-importing host prove the
  check refuses them.

The last figure is the graph those generators and rules draw over the
documents: which manifest feeds which generator, which regions it writes,
which copies a rule keeps equal, and where the build runs the checks.

<!-- BEGIN GENERATED ARCHITECTURE GRAPH documents -->
![The document graph](architecture-documents.svg)

*Figure: the document graph. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [architecture-documents.dot](architecture-documents.dot). The ids in the figure are the ids in the tables below, and each row cites the source symbol that implements it and the check that exercises it.*

<details>
<summary>The document graph: 33 nodes and 39 edges, with their citations</summary>

#### The document graph nodes

| Id | Node | Kind | Owns | Carries | Guards | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract_json | docs/contract.json | manifest | the request, response and envelope version numbers |  |  | [`controller_envelope`](../docs/contract.json) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| limits_json | docs/limits.json | manifest | every runtime limit with its source and check citations |  |  | [`schema_version`](../docs/limits.json) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| matrix_json | tests/fixtures/comparison/matrix.json | manifest | the comparison scenario matrix |  |  | [`observation`](../tests/fixtures/comparison/matrix.json) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| architecture_json | docs/architecture.json | manifest | the nodes and edges of these figures, each with its citations |  |  | [`schema_version`](../docs/architecture.json) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| catalog_json | tests/catalog.json | manifest | the registered suites and cases |  |  | [`"suites"`](../tests/catalog.json) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| gen_contract | generate_contract.py | generator | the generated contract-version regions |  |  | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| gen_limits | generate_limits.py | generator | the limits tables, the scenario matrix and the guide's copied regions |  |  | [`CONTRACT_NAME`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| gen_identity | generate_worker_identity.py | generator | the host/worker source identity regions |  |  | [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| gen_architecture | generate_architecture.py | generator | these figures, their dot and SVG files and the tables beside them |  |  | [`MANIFEST_NAME`](../docs/generate_architecture.py) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| contract_md | docs/CONTRACT.md | document |  | the version sentence and table |  | [`BEGIN GENERATED CONTRACT VERSIONS`](../docs/CONTRACT.md) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| limits_md | docs/LIMITS.md | document |  | the limits tables and coverage |  | [`BEGIN GENERATED LIMITS`](../docs/LIMITS.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| guide | docs/PolicyWitness.md | document |  | copied limits, questions and reading rules; the version sentence; the only document that ships |  | [`BEGIN COPIED LIMITS`](../docs/PolicyWitness.md); [`BEGIN GENERATED CONTRACT VERSIONS`](../docs/PolicyWitness.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py); [`--stage-guide`](../build.sh) |
| questions_md | docs/QUESTIONS.md | document |  | the shared questions the guide copies |  | [`BEGIN SHARED QUESTIONS`](../docs/QUESTIONS.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| failure_contract | tests/FAILURE-PROPAGATION-CONTRACT.md | document |  | the generated scenario matrix and the shared reading rules |  | [`BEGIN GENERATED SCENARIO MATRIX`](../tests/FAILURE-PROPAGATION-CONTRACT.md); [`BEGIN SHARED READING RULES`](../tests/FAILURE-PROPAGATION-CONTRACT.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| architecture_md | docs/ARCHITECTURE.md | document |  | these three figures and their tables |  | [`BEGIN GENERATED ARCHITECTURE GRAPH`](../docs/ARCHITECTURE.md) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| agents_md | AGENTS.md | document |  | the canonical sandboxed-harness note |  | [`Sandboxed automation harnesses`](../AGENTS.md) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) |
| controller_readme | controller/README.md | document |  | the CLI surface block and the version sentence |  | [`CLI surface (contract)`](../controller/README.md); [`BEGIN GENERATED CONTRACT VERSIONS`](../controller/README.md) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| runner_readme | runner/README.md | document |  | the harness-note copy, the test-seam table and the version sentence |  | [`Sandboxed automation harnesses`](../runner/README.md); [`_test_overrides`](../runner/README.md) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py); [`check_test_overrides_table_agreement`](../tests/suites/source_drift/check.py) |
| tests_readme | tests/README.md | document |  | the harness-note copy and the suite table |  | [`Sandboxed automation harnesses`](../tests/README.md) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py); [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| coverage_md | tests/COVERAGE.md | document |  | the outcome coverage matrices |  | [`Normalized outcome coverage matrix`](../tests/COVERAGE.md) | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) |
| api_swift | PWRunnerAPI.swift | source |  | the Swift contract versions and the outcome vocabularies |  | [`PWContract`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`NormalizedOutcome`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) |
| json_contract_rs | json_contract.rs | source |  | the Rust contract versions; the envelope frame |  | [`SCHEMA_VERSION`](../controller/src/json_contract.rs) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| contract_py | tests/lib/contract.py | source |  | the Python contract versions and the worker identity |  | [`CONTROLLER_ENVELOPE`](../tests/lib/contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| abi_header | pw_probe_runner_abi.h | source |  | the C identity region and the shared-region layout |  | [`PW_WORKER_ABI_IDENTITY_HEX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh) |
| cworker_swift | CWorker.swift | source |  | the Swift identity region and the layout mirror |  | [`abiIdentityHex`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh) |
| cli_rs | cli.rs | source |  | the usage text the controller README mirrors |  | [`pub fn run`](../controller/src/cli.rs) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| identity_sources | worker and runner sources | source |  | every byte the identity digest covers |  | [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| suites | tests/suites/<name>/ | source |  | one run.sh and README per suite |  | [`suites_with_run_sh`](../tests/suites/source_drift/check.py) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| drift_check | source_drift check.py | check |  |  | copies and vocabularies that are not generated | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) | [`scenarios`](../tests/suites/source_drift/check_planner.py) |
| drift_limits | source_drift limits.py | check |  |  | the limits generator's copies and every local documentation link | [`broken_links`](../tests/suites/source_drift/limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| drift_contract | source_drift contract.py | check |  |  | the contract and identity generators' copies | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) | [`contract_versions`](../tests/suites/source_drift/run.sh) |
| drift_architecture | source_drift architecture.py | check |  |  | this manifest against its dot, SVG and document copies | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) | [`architecture_documentation`](../tests/suites/source_drift/run.sh) |
| build | build.sh | check |  |  | runs the generators' checks before compiling and stages the guide | [`generate_worker_identity.py`](../build.sh); [`--stage-guide`](../build.sh) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |

#### The document graph edges

| Id | From | To | Kind | Edge | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | contract_json | gen_contract | reads | version numbers | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D2 | gen_contract | contract_md | writes | version sentence and table | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D3 | gen_contract | api_swift | writes | PWContract | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D4 | gen_contract | json_contract_rs | writes | SCHEMA_VERSION and the schema constants | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D5 | gen_contract | contract_py | writes | version constants | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D6 | gen_contract | guide | writes | version sentence | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D7 | gen_contract | runner_readme | writes | version sentence | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D8 | gen_contract | controller_readme | writes | version sentence | [`TARGETS`](../docs/generate_contract.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D9 | limits_json | gen_limits | reads | limits with citations | [`load_limits`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D10 | matrix_json | gen_limits | reads | scenario rows | [`MATRIX_NAME`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D11 | questions_md | gen_limits | reads | shared questions | [`QUESTIONS_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D12 | failure_contract | gen_limits | reads | shared reading rules | [`RULES_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D13 | gen_limits | failure_contract | writes | scenario matrix | [`MATRIX_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D14 | gen_limits | limits_md | writes | limits tables and coverage | [`COVERAGE_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D15 | gen_limits | guide | writes | copied limits, questions and reading rules; staged copy at build | [`GUIDE_START`](../docs/generate_limits.py); [`--stage-guide`](../build.sh) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D16 | identity_sources | gen_identity | reads | sorted paths and contents, length-framed | [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D17 | gen_identity | abi_header | writes | identity bytes | [`TARGETS`](../docs/generate_worker_identity.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D18 | gen_identity | cworker_swift | writes | identity bytes | [`TARGETS`](../docs/generate_worker_identity.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D19 | gen_identity | contract_py | writes | identity hex | [`TARGETS`](../docs/generate_worker_identity.py) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D20 | architecture_json | gen_architecture | reads | nodes, edges, styles and citations | [`load_manifest`](../docs/generate_architecture.py) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| D21 | gen_architecture | architecture_md | writes | figure regions; dot and stamped SVG files beside the document | [`render_region`](../docs/generate_architecture.py); [`stamp_svg`](../docs/generate_architecture.py) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| D22 | agents_md | runner_readme | copies | harness note, first paragraph | [`HARNESS_NOTE_HEADING`](../tests/suites/source_drift/check.py) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) |
| D23 | agents_md | tests_readme | copies | harness note, first paragraph | [`HARNESS_NOTE_HEADING`](../tests/suites/source_drift/check.py) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) |
| D24 | cli_rs | controller_readme | copies | usage text | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| D25 | api_swift | coverage_md | copies | one matrix row per outcome constant | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) |
| D26 | api_swift | runner_readme | copies | test-seam table from PWRunnerTestOverrides | [`check_test_overrides_table_agreement`](../tests/suites/source_drift/check.py) | [`check_test_overrides_table_agreement`](../tests/suites/source_drift/check.py) |
| D27 | suites | tests_readme | copies | one suite-table row per suite | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| D28 | suites | catalog_json | copies | suite directories equal catalog suites | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| D29 | drift_check | agents_md | checks | harness note equality across three copies | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D30 | drift_check | controller_readme | checks | CLI surface block equals cli.rs usage | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D31 | drift_check | coverage_md | checks | every outcome constant has a row and every row a constant | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D32 | drift_check | tests_readme | checks | suite table equals suites and catalog | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D33 | drift_limits | gen_limits | checks | --check, stale-copy and staging controls; every local link in docs/*.md | [`broken_links`](../tests/suites/source_drift/limits.py) | [`limits_documentation`](../tests/suites/source_drift/run.sh) |
| D34 | drift_contract | gen_contract | checks | --check and generator controls | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) | [`contract_versions`](../tests/suites/source_drift/run.sh) |
| D35 | drift_contract | gen_identity | checks | regeneration, relocation and stale-value controls | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) | [`contract_versions`](../tests/suites/source_drift/run.sh) |
| D36 | drift_architecture | gen_architecture | checks | --check, citation, stale-copy and SVG-stamp controls | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) | [`architecture_documentation`](../tests/suites/source_drift/run.sh) |
| D37 | build | gen_limits | checks | --check before compiling; --stage-guide into dist | [`--stage-guide`](../build.sh) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D38 | build | gen_contract | checks | --check before compiling | [`generate_contract.py`](../build.sh) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |
| D39 | build | gen_identity | checks | regenerate before compiling; --check before signing | [`generate_worker_identity.py`](../build.sh) | [`ContractVersionTests`](../tests/suites/source_drift/contract.py) |

Every node and edge above cites at least one check.

</details>
<!-- END GENERATED ARCHITECTURE GRAPH documents -->

## BYOXPC as a variation on launch and selection

A BYOXPC runner is a copy of the XPC bundle registered as a launchd Mach
service, in user or system scope, by the `runner` subcommands
([controller/README.md](../controller/README.md#runner-external-runner-manager)).
Four things change and nothing else. The client connects with
`NSXPCConnection(machServiceName:)` instead of a bundle lookup. The host binds
`NSXPCListener(machServiceName:)` instead of `NSXPCListener.service()` and
resolves its worker and validator relative to its own bundle, exactly as the
built-in one does. The request names the runner through the selector fields
the controller strips before XPC delivery, and the registry supplies the
service name and scope. The installer signs the bundle with the supplied
identity and entitlements plist, and the registry records the entitlements
it reads back from the host executable. The dossier records the hashes of
the bundle's service, worker and validator files as observed before
invocation and compares them with the manifest baselines
(`byoxpc_run_with_a_manifest_compares_the_bundle_copies_with_its_baselines`
in [run_flow.rs](../controller/src/run_flow.rs)); the
[guide](PolicyWitness.md#the-specimen-dossier) states the limit of that
record: it does not prove which bytes were launched, and a mismatch does
not change the run's outcome. The registry is read by an additive loader
that still accepts retired kind spellings so an old install can be listed
and removed; recovery of a half-removed install is the
[registry ownership](../controller/README.md#registry-ownership-and-recovery)
procedure, not a run-time concern.

Known gap. The installer's `codesign_sign` in
[runner_manager.rs](../controller/src/runner_manager.rs) signs the XPC
bundle without `--deep`, so the supplied entitlements are embedded in the
host executable only; the embedded worker and validator keep the
signatures the build gave them, which carry no entitlements. The worker is
the process the specimen policy applies to, so worker entitlements under a
BYOXPC install are the build's, not the installed plist's, and the
[README](../README.md#entitlements--sbpl)'s route to observing a policy under
different entitlements changes the host's, not the worker's. Read it back
with `codesign -d --entitlements -` on the bundle's `pw-probe-runner` after
an install.

## Known gaps

Each gap is stated in full where the promise it limits is stated; this list
only points there.

- [Worker entitlements under a BYOXPC install](#byoxpc-as-a-variation-on-launch-and-selection)
  are the build's; the installed plist reaches the host executable only.
