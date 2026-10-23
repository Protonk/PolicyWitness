# PolicyWitness: boundaries that do not coincide

## Origin and scope

This report began with a local agent’s read-only assessment of PolicyWitness’s runtime performance. A human and a web agent subsequently examined its findings as descriptions of how PW works, rather than as findings of defects or demonstrated performance problems. This document combines the source observations with that subsequent interpretation.

The source is *PolicyWitness: read-only runtime performance investigation*, dated 2026-10-23. It identifies commit `586ddd4` with a dirty working tree, reports that no files outside `.tmp/` were modified, and states that nothing was built, run, instrumented, or benchmarked during the assessment. Its numerical observations came from existing run envelopes, principally test-battery executions. The dirty-tree qualification matters: the commit alone does not identify the exact source inspected. This synthesis adds no independent repository inspection or runtime verification.

The subject is the relationship among boundaries that do not coincide: caller authorization, request admission, worker execution, recognition of progress, timely completion, the last accepted publication, supplementary observation, final representation, and resource disposal. Their separation is part of what the findings describe. It is not treated here as something to eliminate.

F1–F9 retain their original identifiers, but the headings below describe the mechanisms rather than rank performance opportunities. Each finding has the same three sections: verbatim source excerpts, interpretation, and further investigatory comments. The latter identify unresolved facts and relationships, not proposed changes. Relevant observations from the source’s N-series entries supply supporting context.

Quoted text is reproduced without editorial changes other than Markdown blockquote formatting. Each excerpt has a source-report line reference; code locations inside quotations refer to the working tree described above. Excerpts are selective and do not reproduce the source’s proposed solutions. Interpretations remain interpretations of that report, including where they qualify its conclusions. Recommendations are confined to the two closing sections.

## F1. Execution evidence and supplementary log collection

### 1. Verbatim source excerpts

F1, “Location” and “Present behavior” (source report, lines 54–70):

> **Location.** `controller/src/run_flow.rs:803-873`
> (`attach_sandbox_logs`, `collect_log_evidence`);
> `controller/src/sandbox_log.rs:72-85` (`runner_client_span`, the two-second
> pad) and `447-488` (`capture_sandbox_logs_with_timeout`);
> `controller/src/bin/sandbox-log-observer.rs:100-144` (`sandbox_predicate`,
> `log_show_command`); `controller/src/log_capture.rs:482-713`
> (`capture_with_ops`).
>
> **Present behavior.** After execution evidence is complete, for every run with
> an authoritative worker PID and a valid window, the controller spawns the
> observer in its own process group; the observer spawns
> `/usr/bin/log show --style syslog --info --debug --start S --end E --predicate <PID regex>`
> over the client span rounded outward and padded by two seconds at each end
> (a five-to-seven second window). Collection streams under a shared monotonic
> budget (10 s default, 1 s reserve, 1 s cleanup grace), then the controller
> parses the report and associates events to steps. This happens serially,
> after the host has already replied, once per invocation.

F1, “Risk and uncertainty,” opening clause (source report, lines 93–96):

> The log channel is already defined as optional and
> possibly incomplete, and the assembly seam
> (`attach_sandbox_logs`) hands the collector read-only execution evidence and
> takes back only log-owned fields

### 2. Interpretation

The controller’s receipt of the host reply and its collection of supplementary logs are separate events. “Execution evidence is complete,” in the source’s description, refers to one part of the record; it does not mean that every observation eventually included in the envelope has already been made. Log collection has its own process supervision, budget, eligibility conditions, and association procedure.

Two times consequently matter: when the events of interest occurred and when PW looked for records of them. The padded query interval describes the first. It does not, by itself, describe the second. The collector’s restricted access to log-owned fields establishes a field-ownership boundary, not equivalence among all possible collection histories.

The source’s suggestion that later collection would make evidence more complete assumes more than the described arrangement establishes. Nothing in this report establishes that available records only accumulate with delay. Keeping execution fields unchanged also does not prevent supplementary observations from affecting a reader’s interpretation of the combined envelope.

The PID and window are association inputs. They are not a complete account of association semantics. F1 also reports that parsed events lack structured timestamps, leaving a distinction between the interval submitted to the log query and the time information retained with an individual event. The finding describes an assembly of observations with different collection histories, not one indivisible observation.

### 3. Further investigatory comments

Which times are actually retained: the client span, padded query bounds, collection start and end, and completion of envelope assembly? The source identifies several of these concepts without establishing that all remain recoverable from a finished result or share a clock domain.

What information survives the path from the store query through parsed events to step association? In particular, the relationship among the query window, worker identity, any timestamp in the raw line, and the final association remains a substantive part of this finding.

The collector’s status vocabulary distinguishes some collection outcomes, including timeout and window mismatch. The open question is how those outcomes relate to retained partial records, an empty match set, and supervision failures. The absence of a matched event and the failure to obtain an observation are different circumstances; the report does not supply their complete representation rules.

## F2. Events becoming true and the host recognizing them

### 1. Verbatim source excerpts

F2, “Location” and “Present behavior” (source report, lines 118–126):

> **Location.** `runner/Sources/PWRunnerCore/CWorker.swift:1216-1236` (ready
> byte; `pollNs: 10_000_000` at line 1222) and `1392-1415` (exit grace;
> line 1393); `HostWaitClock.expiredAfterSleeping` at `838-847`.
>
> **Present behavior.** After policy transfer the host sets the ready pipe
> nonblocking and loops: `read` one byte, and if nothing is there, `nanosleep`
> 10 ms (bounded by the remaining 1,000 ms allowance). After observing `done`
> the host stores `exit_requested`, then loops `waitpid(WNOHANG)` with 10 ms
> sleeps for up to 1 s before `SIGKILL`.

F2, “Risk and uncertainty,” stop-vocabulary excerpt (source report, lines 148–149):

> (`received`, `eof`, `read_error`, `deadline`, `setup_failed`;
> `reaped_during_grace`, `exhausted`, `wait_error`)

### 2. Interpretation

The ready-byte wait and the reap wait seek different facts. One seeks a message on a pipe after policy transfer; the other seeks confirmation that a child has been reaped. Both use repeated nonblocking checks separated by sleeps.

An event becoming observable and the host recognizing it are therefore separate moments. A recorded wait includes the operation of that recognition mechanism. It is not directly the duration of sandbox compilation, nor an exact measure of the interval between worker publication and worker exit. The source’s recorded durations are consistent with a polling quantum affecting recognition, but do not reconstruct the exact arrival or exit time within that interval.

The named stop outcomes show that these loops do more than wait for success. They also decide among EOF, errors, deadlines, and exhausted grace. Their observable behavior includes the handling of competing terminal conditions. An unchanged outcome vocabulary alone does not establish that those decisions are insensitive to how the wait operates.

N4 supplies a related distinction: the policy-delivery length receipt has a separate role in detecting a cut submission. Receipt of policy bytes, recognition of worker readiness, and successful child reaping do not establish the same prerequisite or completion fact.

### 3. Further investigatory comments

What starts and ends each reported interval, and which event does each endpoint actually identify? A host timestamp can locate a successful check without locating the underlying event to the same precision. The report does not resolve all of those endpoint meanings.

How are near-simultaneous conditions handled—for example, an available byte near expiry, or child exit when a grace check also expires? The source names the possible outcomes but does not provide a complete account of their precedence or the observations supporting them.

`HostWaitClock` supplies injected clock and sleep behavior for existing fault-injection tests. That identifies a testable abstraction, but leaves open how closely its controlled transitions correspond to the ordinary runtime sequence. The host’s ready/reap waits are also distinct from the shared-memory sentinel polling described in N2 and from the worker’s release wait in F4.

## F3. Single-use host admission and process lifetime

### 1. Verbatim source excerpts

F3, “Location” and “Present behavior” (source report, lines 160–173):

> **Location.** `controller/src/run_flow.rs:560-755` (`run`, one request per
> invocation); `controller/src/runner_client.rs:85-127`
> (`run_pw_runner_client`, one Swift client process per run);
> `runner/Clients/PWRunnerClient/main.swift`;
> `runner/Sources/PWRunnerCore/PWRunnerService.swift:28` (`hostExitDelayMs`),
> `211-220` (`PWRunnerAdmission`, the single terminal claim), `250`
> (`scheduleExit`); `docs/ARCHITECTURE.md` "Why these processes exist";
> `docs/LIMITS.md` `byoxpc_throttle_interval`.
>
> **Present behavior.** Each invocation starts a controller, spawns a 2.4 MB
> Swift client whose only job is `NSXPCConnection`, and has launchd start a
> fresh 3.5 MB Swift host that accepts exactly one request and exits 50 ms
> after replying. With capture, seven processes per specimen (controller,
> client, host, worker, validator, observer, `log show`); five without.

F3, “Risk and uncertainty,” resource-lifetime excerpt (source report, lines 201–204):

> "Fresh host state" is the stated rationale for
> single use. Reading the host, the per-run state is scoped: the region, pipes
> and child observers live in `runCWorker`; `ExtensionSession` erases and closes
> in `deinit`; `FirmlinkMap.shared` is a benign process-wide cache.

F3, “Risk and uncertainty,” instancing question (source report, lines 208–211):

> An open
> question the source does not settle: whether launchd gives each client
> *process* its own instance of an app-embedded `ServiceType: Application` XPC
> service.

### 2. Interpretation

The reported arrangement is more restrictive than a fresh worker for every specimen. A host generation admits one request and schedules its own exit after replying. Receipt of a reply, eligibility to accept another request, and disappearance of the host are therefore different events. Within the described host generation, another request is not admitted merely because the previous request has completed.

Single use is consequently part of the admission model as well as the process topology. The `already_ran` outcome and top-level reply `pid` participate in that model. A request claim associated with a host generation is not the same as a rule about serialization within one connection; the source does not establish how multiple connections would relate beyond the current one-shot claim.

Scoped per-run resources are evidence of local ownership. They do not establish that every completion or failure path leaves a still-running host in an equivalent condition. The report itself identifies stuck validators and unconfirmed worker reaps as consequential possibilities. Its characterization of a process-wide cache as benign is likewise an assessment, not a separate runtime finding. The absence of the specimen’s applied sandbox from the host does not settle the significance of fresh host state.

Conversely, ending the host is not proof that every external effect or child-related obligation has disappeared. Process disposal bounds the lifetime of process-local state; the reach of that reset is a separate question.

The lifetimes of controller, client, host, worker, and supplementary collector are related but not identical. The source’s process count is a summary of its described path, not an established count for every specimen; N3 separately specifies a fresh validator per eligible phase. Its external-runner throttle discussion also remains a reported lifecycle constraint rather than a confirmed throughput result. Built-in XPC instancing is explicitly unresolved.

### 3. Further investigatory comments

What determines host-instance identity for the built-in path and for an external runner: the client process, the connection, the service, or another distinction? The recorded absence of built-in `already_ran` responses does not distinguish these possibilities. The source itself notes that the existing runs may not have exercised the relevant overlap.

What is the ordering among reply dispatch, client receipt, scheduled retirement, actual host exit, and eligibility for another acquisition? A delay outside the current request’s reply interval is not necessarily outside a subsequent request’s acquisition interval. F9 describes that subsequent acquisition as its own procedure.

What remains owned or active when a run ends with an unresolved child or validator? The source’s lexical scopes and cleanup methods describe intended ownership, while their runtime completion remains a separate fact. This question connects to F5 without making host retirement, worker cancellation, and worker reaping one event.

## F4. Phase arrival, release, and the worker’s active wait

### 1. Verbatim source excerpts

F4, “Location” and “Present behavior” (source report, lines 225–232):

> **Location.** `controller/tools/pw_probe_runner/pw_probe_runner.c:1560-1612`
> (`wait_for_proceed`); the spin at line 1609 is 1,000 `yield` instructions per
> iteration with no sleep.
>
> **Present behavior.** After publishing arrival the worker loops reading the
> release ordinal, `exit_requested` and the continuous clock until its ordinal
> appears or the 60 s allowance expires. The comment states the rule: no
> allocation, sleep or I/O after apply.

N2, stated rationale for shared-memory publication (source report, lines 414–416):

> The worker cannot be trusted to signal after
>   apply: a deny-default profile can deny its writes and even its exit, which
>   is why publication is a memory store.

### 2. Interpretation

The worker’s arrival at a phase boundary is not permission to advance. It publishes arrival, then remains within the specimen’s applied conditions while waiting for the corresponding release ordinal. The arrangement describes an explicit ordering barrier rather than reliance on an expected collection duration.

The loop also reads `exit_requested` and the continuous clock. In conjunction with F5, it is a release barrier, a bounded wait, and the identified cooperative cancellation point. Its role is therefore broader than the term “busy-spin” describes. Host-side observation of shared memory and worker-side waiting for release operate in different directions and have different responsibilities.

N2 states a rationale for keeping publication independent of ordinary post-apply signaling. A corresponding interpretation of F4 is that the narrow wait avoids introducing another operating-system dependency under the specimen’s conditions. That is an interpretation of the arrangement, not an established history of the design or an independent verification of the source’s sandbox claims.

F4 also reports sleeping operations in an exec reap path and a post-apply test seam. Their presence does not settle the scope of the quoted restriction. The comment mentions allocation, sleep, and I/O; the source’s later discussion broadens this to a rule against post-apply syscalls. Nor does the report establish that the comment is a global invariant rather than a restriction on this coordination path. Operation-specific code, test-only code, and a general phase barrier may have different obligations.

The active wait is not environmentally inert merely because it avoids additional signaling operations. It may consume resources needed by the host or validator whose progress permits release. The report identifies that possible interaction but does not measure worker CPU use. Collection elapsed time is not itself a CPU-consumption measurement.

### 3. Further investigatory comments

What exactly does publication of the release ordinal certify about collection, and what observations are permitted before the worker advances? The source describes the controlling words, but not the full visibility and ordering account at this boundary.

What takes precedence when release, `exit_requested`, and allowance expiry become observable together? F5 identifies this loop as the cancellation-reading location, making the exit condition part of both phase ordering and termination behavior.

Where does the no-allocation/sleep/I/O restriction apply, and what stated obligation does it protect in that scope? The existence of other post-apply operations leaves that question open. Separately, how much resource consumption belongs to the waiting worker rather than the processes performing collection? The current report establishes neither equivalence between waiting mechanisms nor the magnitude of competition among these processes.

## F5. Timeout, cancellation, late publication, and final disposal

### 1. Verbatim source excerpts

F5, “Location,” “Present behavior,” and recorded timeout cases (source report, lines 264–274):

> **Location.** `CWorker.swift:1379-1415`; the worker samples `exit_requested`
> only inside `wait_for_proceed` (`pw_probe_runner.c:1599-1601`).
>
> **Present behavior.** When polling stops for any reason the host stores
> `exit_requested`, then waits up to 1 s with 10 ms polls before `SIGKILL`. The
> worker reads that word only while waiting for a phase release; pre-apply and
> inside an attempt it never does.
>
> **Suspected expense.** Pathological path only: one extra second per hung
> worker. In the 64 recorded `runner_timeout` envelopes (test-override hangs),
> 60 exhausted the full grace (1,001-1,004 ms) before the kill.

F5, “Risk and uncertainty,” late-publication statement (source report, lines 282–284):

> The grace also lets a slow worker publish late slot
> results that the final snapshot retains as immutable publications beside the
> `runner_timeout` outcome.

F5, “Risk and uncertainty,” limit of the recorded cases (source report, lines 285–286):

> Whether late publications ever occur in practice is unknown; the recorded
> cases are deliberate hangs.

### 2. Interpretation

The host can decide that a wait has expired, request cancellation, continue waiting, accept publications into a final snapshot, terminate the worker, and reap it at different moments. These are not interchangeable meanings of stopping the run.

A worker outside `wait_for_proceed` does not read the cancellation word at that point, according to the report. That limits the immediate effect of cooperative cancellation. It does not establish that the ensuing grace serves no other purpose: the worker may finish naturally and publish results during that interval.

A timeout can therefore be terminal for one control-flow decision without being the cutoff for all evidence production or acceptance. An envelope containing `runner_timeout` alongside later-completed slot results is not inherently contradictory. The status describes a completion condition that was not met in time; retained publications describe observations that were nevertheless accepted.

The grace carries more than a cancellation opportunity. It is also an interval during which natural completion and further publication can occur. This is a concrete case where activity described as teardown can still participate in witnessing. The deliberate hangs in the source’s existing envelopes show one behavior of the grace, not the frequency or significance of late publication in other executions.

N7’s nested budgets describe additional limits on different activities. Their nesting does not by itself establish that expiry at an outer boundary immediately preempts inner work or identifies the final accepted publication.

### 3. Further investigatory comments

Where is the last point at which a publication can enter the retained snapshot, relative to sentinel expiry, the cancellation store, termination, and reap? The report describes late acceptance but does not give the complete ordering of final snapshot acquisition on each exit path.

Which observations distinguish a worker that notices cancellation from one that finishes naturally, remains blocked, or is forcibly terminated? The position words identify reported progress, but the extent to which they determine the worker’s current ability to stop is not fully established here.

Which retained fields can locate a slot’s completion relative to timeout, and which support only a partial ordering? The report’s existing timeout cases are deliberate hangs. They do not establish whether the current output can always distinguish a genuinely late publication from one that was already present when the host recognized expiry.

## F6. Held evidence, deterministic representation, and diagnostic text

### 1. Verbatim source excerpts

F6, “Location” and “Present behavior” (source report, lines 294–306):

> **Location.** `controller/src/json_contract.rs:82-103` (`sort_value`),
> `118-122` (`render_envelope`); `controller/Cargo.toml:26`
> (`serde_json = "1"`) and `controller/Cargo.lock` (serde_json 1.0.147 without
> `indexmap`, so `preserve_order` is off and `serde_json::Map` is a `BTreeMap`).
> Related: `controller/src/utils.rs:96-150` (`truncate_output`,
> `capture_json_output`).
>
> **Present behavior.** `envelope_value` builds a `Value` whose objects are
> already key-sorted maps, then `sort_value` rebuilds every object by cloning all
> of its children and recursing into the clones. Each nesting level copies the
> entire subtree below it. Separately, `capture_json_output` lossy-converts the
> complete reply bytes to a `String` before parsing, and discards that string
> unless the parse fails or the capture was truncated.

### 2. Interpretation

This finding describes transformations of information already held, rather than another interaction with the specimen. The source identifies two mechanisms apparently serving key ordering: the map representation used to construct the envelope and the recursive reconstruction performed by `sort_value`. It separately identifies a textual diagnostic representation of reply bytes that is retained only on particular paths.

Those are different responsibilities. Deterministic envelope rendering concerns the representation of a constructed value. Lossy conversion of reply bytes supports a diagnostic account when parsing fails or capture is truncated. The existence of a diagnostic consumer does not establish that the representation is consumed on a successful parse.

For this local rendering responsibility, representational equivalence is a relevant correctness property. That is narrower than treating identical final JSON as proof that two experimental procedures were equivalent. The distinction does not make one kind of equivalence universally sufficient or universally irrelevant.

The source’s account of sorted maps depends on the dependency and feature configuration it inspected. Its description of recursive copying is a code-level claim; the quoted time and memory estimates elsewhere in F6 are not established by a new measurement. This finding separates a representation obligation from the particular transformations presently associated with it.

### 3. Further investigatory comments

What is the complete input-to-output contract of `render_envelope`, including object ordering, array ordering, escaping, and retained diagnostic strings? The report establishes the apparent key-ordering duplication, not every observable property of the rendering path.

Which feature configuration produced the executable associated with any runtime observation? The reported lockfile and source configuration identify the inspected arrangement; they are not, by themselves, a record of every executable’s build configuration.

For failed parsing and truncated capture, which bytes, lossy text, and parsed values remain available to later stages? Their sizes and lifetimes are separate from the question of whether a completed envelope is rendered deterministically. F1 can supply substantial retained log content, but the creation of those observations and their later representation remain different subjects.

## F7. Admission at multiple callable boundaries

### 1. Verbatim source excerpts

F7, “Location” and “Present behavior” (source report, lines 326–334):

> **Location.** `PWRunnerService.swift:290-296` then
> `CWorkerOrchestrator.swift:65-70`; `admissionFailure(for:)` at `293-323`
> builds a throwaway `CWorkerInput` (slots plus sorted params) for the capacity
> check; `run` at `75-100` builds slots and params again; `runCWorker` at
> `CWorker.swift:935` runs `workerAdmissionFailure` a third time.
>
> **Present behavior.** The service gates the request, then calls the
> orchestrator, which gates it again (so the direct-orchestration test seam has
> the same gate), and the driver gates its own input once more.

### 2. Interpretation

The described path contains admission at the service, again at the orchestrator, and again at the worker-input driver. The report supplies a reason for at least one repeated check: direct orchestration can reach the orchestrator without passing through the service’s gate. The driver also guards the input it is about to use.

Repeated computation and repeated responsibility are therefore distinct. A boundary can have a real admission obligation even when a normal route through the application has already established some of the same predicates. The source’s claim that the repetition has no consumer is stronger than its own description supports. Conversely, distinct admission obligations do not establish that every repeated translation serves a distinct purpose.

The reported refusal precedence—capacity before meaning, and top-level strings before plan strings—determines the account returned when several conditions are invalid. It is part of admission behavior, not merely an unordered collection of valid/invalid predicates.

This admission concerns the request and its representation. It is different from F3’s one-request claim on a host generation and F8’s authorization of a caller. N5 identifies still further checks performed by the worker before application, including identity, layout, length, and symbol prerequisites. Passing host admission does not mean that every later prerequisite has already been established.

### 3. Further investigatory comments

Which representations reach each gate, and which properties does each gate establish? The report identifies repeated construction of slots and parameters, but does not fully establish that the inputs or predicates are identical at all three boundaries.

Which entry paths can bypass an earlier gate? The direct-orchestration seam is one explicit example. The relationship between those entry paths, the driver's ABI-local obligations, and the worker's own pre-apply checks remains a concrete part of the finding.

How is refusal precedence expressed when more than one condition fails, and which layer supplies the reported refusal? This concerns the observable behavior of admission, even though admission is not an observation of sandbox enforcement. It also distinguishes a rejected request from an admitted request whose worker later fails a prerequisite.

## F8. Caller authorization and connection acceptance

### 1. Verbatim source excerpts

F8, “Location” and “Present behavior” (source report, lines 351–359):

> **Location.** `PWRunnerService.swift:73-105` (`authorizedCaller`), invoked in
> `shouldAcceptNewConnection`; `runner/Services/PWRunner/Info.plist`
> (`PWRunnerRequireSignedCaller` true, identifier allowlist).
>
> **Present behavior.** Per connection: `SecCodeCopyGuestWithAttributes` by
> PID, `SecCodeCopyStaticCode` and `SecCodeCopySigningInformation` for the
> caller and for the host itself, then a team ID comparison and an identifier
> allowlist. Because the host is fresh per specimen, Security framework
> initialization is paid every time.

### 2. Interpretation

The described check is an authorization policy: it compares signing information and applies an identifier allowlist before accepting a connection. It does not primarily decide whether a specimen could execute or produce useful evidence. A feasible request and a request from an authorized caller are different categories.

The source places the check at connection acceptance and describes obtaining signing information for both caller and host. That identifies the policy’s implementation location and identity inputs. Its repeated execution is related to F3’s host and connection lifetimes, but the gate’s role does not reduce to initialization cost.

The PID-keyed lookup identifies a particular identity-resolution step. The report does not establish a complete runtime account of identity changes, process lifetime, or the relation between a lookup and the connection being accepted. Its proposed alternative elsewhere in the source is not evidence that the current acceptance policy has already been characterized completely.

The source’s suggestion that the implementation location is historical remains an explanation without a demonstrated history. Likewise, uncertainty about built-in service instancing does not by itself establish that explicit authorization is unnecessary there. The reported policy is a finding; its complete reach and rationale remain less settled.

### 3. Further investigatory comments

To what object and lifetime does an authorization decision attach: a connection, a caller process, a host generation, or another entity? The location in `shouldAcceptNewConnection` answers part of that question, but not every subsequent relationship between accepted connections and admitted requests.

Which signing attributes and identifier rules determine each acceptance or rejection, and what happens when an identity lookup itself fails? The source lists the operations and comparison but does not provide the entire decision table or its runtime failure record.

How do the reachable connection paths differ between built-in and external services, and which identities appear at this gate on each path? That connects F8 to F3 without merging authorization with the service’s single-use claim. It also differs from F9’s observation of selected executable files: caller authorization and artifact provenance identify different things.

## F9. Artifact provenance and external-runner acquisition

### 1. Verbatim source excerpts

F9, “Location” and “Present behavior” (source report, lines 382–391):

> **Location.** `controller/src/dossier.rs:256-295` (`compare`) and `419-478`
> (`Binaries::observe`); `controller/src/runner_manager.rs:215`
> (`load_registry`); `controller/src/runner_acquisition.rs:168-199`.
>
> **Present behavior.** For an external runner the controller reads the
> registry JSON and SHA-256 hashes the selected service binary (3.5 MB) and the
> three bundle-local helpers on every run; the built-in path hashes nothing
> because the manifest entry is the selected path. After a qualifying
> `already_ran` the controller polls `proc_pidinfo` every 10 ms until the old
> generation disappears, then connects again.

N6, built-in dossier work (source report, lines 431–436):

> - **N6. Controller dossier work for the built-in runner**: four `sysctl`
>   reads, a 3.6 KB manifest parse, the literal import closure scan (reads and
>   hashes only files the policy imports; `system.sb` is about 150 KB), a
>   1.5 KB augment splice, one serialization of the held request. About a
>   millisecond. `PW_VERIFY_EVIDENCE=1` hashes every manifest entry per run but
>   is opt-in.

### 2. Interpretation

F9 contains two procedures: observing selected artifacts for the dossier, and acquiring a service generation. Reading the registry and hashing executable content records information before a run. Waiting for an old process generation to disappear concerns whether another connection can be attempted. They share an execution path without establishing the same fact.

Hashing here is provenance production, not merely a feasibility preflight. A statement about bytes observed before this invocation has a temporal meaning as well as a digest value. Equal digest values do not erase the difference between observations made at different times.

The direct observation is of the content read at that stage. By itself, it does not establish every subsequent fact about which bytes execute, which helper is used, or what happens after selection. The report does not demonstrate a failure of those relationships; it leaves their full account unstated.

Read literally as a claim about all built-in dossier work, “the built-in path hashes nothing” would be too broad: N6 explicitly describes hashing policy imports and opt-in manifest verification. The supported interpretation confines F9’s contrast to the ordinary binary-identity path. Built-in and external execution then have different bases for that aspect of identity—a manifest entry and fresh content observation—without establishing that one is deficient.

The reacquisition procedure adds another temporal distinction. Disappearance of an old generation, availability of a new connection, and acceptance of a request by the selected service are not the same event. This is the external-runner continuation of the lifetime questions in F3.

### 3. Further investigatory comments

What binds the registry selection, observed file content, selected service, and eventual execution in the retained record? The source names these stages without fully specifying which associations are directly observed and which follow from the procedure.

When reacquisition follows `already_ran`, which earlier observations still describe the selected execution, and which stages occur again? The report identifies a process-disappearance check followed by reconnection, but does not provide the complete relationship between that retry and dossier construction.

Which provenance claims refer to artifact content, declarations, invocation-time environment, or a particular process generation? N9 offers a related example of temporal separation elsewhere: path resolution at planning and after orchestration are described as different observations, with the planning result also affecting a named decision. Work performed before execution can already be evidence-producing; its position in the sequence does not make it only a preflight.

## Conclusion 1. Findings worth investigating together

I recommend two joint investigations, with the remaining findings initially kept separate. These are groupings by shared runtime events, not proposals to combine the boundaries they describe.

**F2, F4, and F5: recognition, phase release, and stopping.** These findings concern different participants in the worker’s progress and termination history. A common account of readiness, arrival, release, cancellation, publication, and reap can serve all three. The host’s recognition of a fact, the worker’s permission to proceed, and the last accepted publication remain separate endpoints. An unresolved reap also connects this group to F3, without making host retirement part of the same endpoint.

**F3, F8, and the acquisition portion of F9: service generations, connections, and identity.** Host instancing and lifetime affect which connection reaches authorization, which request encounters an exhausted admission claim, and which process generation is involved in reacquisition. These questions benefit from a common record of process and connection identities. F9’s artifact observations remain a distinct part of that record; caller authorization, selected-file provenance, and service-generation identity are not interchangeable checks.

**F1, F6, and F7: separate starting points, with shared material where useful.** F1 concerns when supplementary observations enter the record. F6 concerns transformations of already-held data. They can use some of the same captured envelopes without requiring the same investigation. F7 concerns request-content and representation gates, not F3’s single-use request claim. Its entry paths and refusal behavior form a coherent investigation of their own. F9’s provenance questions likewise need not wait for the acquisition questions to be resolved.

## Conclusion 2. How to begin a runtime investigation of any finding

Start with one existing specimen that reaches the relevant path, using the ordinary CLI and a known executable. Record the exact command, specimen, executable identity, source revision and dirty-tree state if applicable, macOS version, runner selection, and log-capture settings. Save stdout, stderr, exit status, and the complete envelope. Use the existing telemetry first; leave the mechanism under investigation unchanged.

For that run, identify the process or component responsible for each relevant event and the field or observation that locates it. Put the available events in order, retaining their clock domains and distinguishing event time from the time another component noticed the event. Repeat the same invocation a few times to determine which parts of that account are stable. If an endpoint cannot be located from the retained output, name that missing event before choosing additional tracing. Establish what an interval starts and stops on before treating its duration as a measurement of the activity inside it.
