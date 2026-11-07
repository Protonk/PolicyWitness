# Resource footprint

Each row is one of three kinds. A measured row reports an observation under
its stated conditions. A logical row states a capacity that follows from the
compiled layout and the admitted plan, not a measurement. A source row
describes a mechanism and carries no quantity of its own. Conditions and
intervals belong to each row; no row establishes a universal memory ceiling.
Add quantities only when their units, backing and overlapping lifetimes
support the sum; native memory metrics are never added to logical capacity or
encoded bytes.

## Provenance of measured rows

Every measured row was transcribed into the manifest from the receipts of one
managed test run: run id `20261106T210300Z_381f3d39`, output directory
`footprint-targeted-20261106-01`, cases `witness_contract/held_phase_footprint`,
`witness_contract/response_footprint` and `run_effects/aftermath_footprint`.
That run is archived as `historical-footprint-measurements.tar.gz`, with an
index of file hashes beside it, in the finished evidence of the retained run
`runs/finished-targeted-20261106`. The retention record
[tests/RETAINED.json](../tests/RETAINED.json) lists that retained run. Test
output is gitignored, so the archive exists only in a checkout that retained
it. Its artifact inventory records the hashes of the binaries that were
measured. The app in `dist/` and the later retained run were built after that
measurement and carry different binary hashes; the later run's own response
measurement is not what these rows describe.

The generator and the footprint drift case verify the manifest's structure,
its citations and the freshness of the rendered copy. Nothing verifies that a
row's numbers agree with a receipt. A row changes only when someone reruns its
case and transcribes the new receipt.

## Using the rows as a baseline

A change is compared against a fresh measurement of the same signed binaries
before and after, under the same case and conditions. These rows fix the shape
of that comparison and its limits; they are the before side only if the
archived binaries are the ones rebuilt.

| Change class | Compare | Rows | Outside the baseline |
| --- | --- | --- | --- |
| Controller serialization or capture ownership | Host reply, client stdout and envelope bytes for equality outside dynamic fields; sampled resident and physical footprint maxima for demand | fr9–fr13 | Peaks shorter than the spacing between sample starts; stage attribution; host, worker and observer demand |
| Worker wait or activation | Per-worker CPU per hold class against the matched busy and sleeping controls | fw10–fw13 | Idle waiting; host demand, which these rows observe through an instrumented host |
| Evidence region geometry | Logical capacity and layout agreement only | fw4, fw5, fr14 | Residency; no measured row covers host or worker memory |
| Authority region or custody sizing or disposal | Logical capacities and the accepted custody length | fw6, fw7, fw14, fr14 | Residency; erasure after CLI return, which fa3 leaves unknown |
| Any change | Process presence at the first post-return snapshot | fa7, fa8 | Mapping disposal and reap |

## Waiting and retained resources

Elapsed waiting does not establish idle CPU. Measured actor rows come from a
disposable instrumented host with unchanged signed workers; their timing does
not describe an uninstrumented host.

<!-- BEGIN GENERATED FOOTPRINT WAITING -->

| ID | Resource / owner | Quantity / mechanism | Conditions | Interval | At CLI return |
| --- | --- | --- | --- | --- | --- |
| fw1 | Release-word polling — active worker | source: [LIMITS `worker_proceed_wait`](LIMITS.md) Continuously samples release/cancellation and expiry, with batches of yield hints. Requested-action quiescence is not CPU idleness. | Arrived phase awaiting collection release. | phase arrival → release accepted, expiry sampled or cancellation observed | — |
| fw2 | Parked actor polling — parked worker | source: Polls its activation word and can service inbound authority while parked. | Actor prepared before its next scheduled visit. | setup or previous visit completion → named activation, cutoff or exit request | — |
| fw3 | Collection orchestration — host / validator | source: Host polls/sleeps while collecting; an eligible phase launches a separate validator. Their demand is separate from worker polling. | Ordinary and actor collection; validator only for eligible queries. | worker readiness or arrival → collection ends; validator ends independently | — |
| fw4 | Evidence backing / host view — host | logical: 3,675,920 bytes One fixed evidence backing per worker, initialized before spawn; host and worker mappings are views of the same object. | Each ordinary worker or actor, independent of requested action count. | mapping preparation → host session teardown | — |
| fw5 | Evidence worker view — worker | source: Aliases the evidence backing; do not add its logical capacity to the host view as a second backing object. | Each launched worker. | worker maps launch descriptor → worker process exit | — |
| fw6 | Authority regions — host / actor workers | source: Per actor: 1152 + (inbound slots + outbound slots) × 16448 requested logical bytes, including actors with no slots. The worker maps the observed object size, which can include page padding; it remains a view of the same backing. Bearer bytes are outside the encoded reply. | Authority-bearing actor plan; one distinct backing per actor, host/worker views. | authority setup before launch → host detachment and worker exit, independently | — |
| fw7 | Private token custody — host | logical: 16,384 bytes One fixed private buffer per admitted token; delivery copies it into the recipient actor's inbound slot. Last-use erasure resets payload state but retains its allocation. | Authority-bearing actor plan; accepted lengths are separate from capacity. | custody preparation → custody finish | — |
| fw8 | Candidate handles / fixed table — actor worker | logical: 512 bytes Fixed handle table storage remains after native release. Candidate count and native result do not measure private kernel storage. | Each worker; successful consumes populate named candidates. | worker static storage → worker exit | — |
| fw9 | Launch-only descriptors — host | source: Evidence/authority launch descriptors close after spawn; policy/ready pipes have their own close boundaries. Mapping references survive descriptor close. | Prepared host resources; actual setup failures retain their own cleanup outcomes. | host setup → spawn or setup failure closes each descriptor | — |
| fw10 | ordinary held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,107,987,125–1,128,846,875 ns; worker:0 CPU 1,101,612,917–1,123,613,417 ns. Hold class 3: conservative elapsed 3,115,067,458–3,144,625,083 ns; worker:0 CPU 3,108,671,500–3,143,494,666 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw11 | actor_1 held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,119,694,584–1,130,162,833 ns; worker:0 CPU 1,114,585,833–1,131,120,833 ns. Hold class 3: conservative elapsed 3,118,528,958–3,141,749,458 ns; worker:0 CPU 3,114,453,583–3,144,314,292 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw12 | actor_3 held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,118,848,333–1,129,527,459 ns; worker:0 CPU 1,109,434,708–1,132,191,750 ns; worker:1 CPU 1,124,444,624–1,129,185,792 ns; worker:2 CPU 1,109,997,583–1,130,167,250 ns; worker aggregate 3,343,876,915–3,391,544,792 ns. Hold class 3: conservative elapsed 3,100,499,666–3,148,954,292 ns; worker:0 CPU 3,101,086,792–3,157,780,833 ns; worker:1 CPU 3,097,857,250–3,144,838,583 ns; worker:2 CPU 3,104,895,124–3,145,675,708 ns; worker aggregate 9,303,839,166–9,448,295,124 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw13 | actor_lifecycle held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,128,085,959–1,131,137,792 ns; worker:0 CPU 1,126,848,958–1,131,069,249 ns; worker:1 CPU 1,127,899,542–1,133,016,542 ns; worker aggregate 2,255,967,001–2,264,085,791 ns. Hold class 3: conservative elapsed 3,148,305,250–3,151,015,291 ns; worker:0 CPU 3,146,478,041–3,157,893,791 ns; worker:1 CPU 3,145,107,374–3,151,512,042 ns; worker aggregate 6,291,585,415–6,307,922,750 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw14 | Held actor custody / delivery / candidate — issuer / subject / host | measured: 212 bytes Actual accepted custody length and equal settled first delivery length, not buffer capacity. Across six holds, issuer is parked after its first transfer; subject has completed H1, holds the read-bearing visit without release, and has H2 and both releases pending. Private custody remains mapped and unerased for a later transfer; D2 is unpublished. No bearer bytes were captured. | Instrumented pre-collection metadata bound to the acknowledged held gate and unchanged marker/target; named references retained. | completed first consume and held next visit → post-measurement gate release | — |

<!-- END GENERATED FOOTPRINT WAITING -->

Waiting CPU rows report cumulative native user-plus-system counters, converted
from Mach ticks with each sample’s recorded timebase and validated at that scope
by independent busy-process getrusage observations; the conversion does not
establish a universal scheduler quantum. CPU accumulates across
generation-qualified held intervals while independent targets and markers stay
unchanged, with controls matched within each hold. Recorded machine load is a
condition, not a claim of quietness. Each receipt also records the observer’s
native child CPU; the Python driver’s demand was not measured. Actor metadata
comes from the pre-collection instrumented host, associated with the subsequent
acknowledged gate.

## Response storage and transport

The source rows describe representations in the order they arise: validator
records (fr3), host collection copies (fr2), the encoded reply (fr4), client
capture and stdout (fr5), the controller’s raw streams (fr1), generic and typed
capture (fr6), decoded host bytes (fr7) and the envelope (fr8).

A retention allowance does not bound collection memory. The measured rows use
fresh shipped controllers.

<!-- BEGIN GENERATED FOOTPRINT RESPONSE -->

| ID | Resource / owner | Quantity / mechanism | Conditions | Interval | At CLI return |
| --- | --- | --- | --- | --- | --- |
| fr1 | Complete child stream collection — controller | source: [LIMITS `controller_output`](LIMITS.md) Collects complete stdout/stderr before making retained prefixes. Raw Output remains borrowed through capture and host parsing, then drops before final rendering. | Client reply or failure output; complete received counts differ from retained counts. | child pipes opened → run_client_stdin returns | — |
| fr2 | Collection copies from mappings — host | source: Copies published slots/profile/phase values while source mappings still exist; session teardown precedes later reply assembly. Actor reply metadata survives authority teardown. | Ordinary and actor outputs; authority contents are not response payload. | output collection → last reply-model use; source mappings end earlier | — |
| fr3 | Validator framing and decoded records — host | source: Raw bounded validator output and decoded records coexist during decoding; returned records/counts outlive the temporary raw Data. | Eligible query phases; repeated results contribute metadata to the final reply. | validator output drain → raw Data last use; decoded records retained separately | — |
| fr4 | Reply model, encoded bytes and XPC — host / client | source: [LIMITS `runner_reply_maximum`](LIMITS.md) Reply model overlaps encoded host Data; XPC and Foundation physical copy/backing behavior is unestablished. The synthesized maximum bounds encoded reply size, not live memory. | Successful encoding, including actor setup/events/resources metadata. | reply assembly → callback and representation last use | — |
| fr5 | Base64 capture and client stdout — client | source: Incoming host Data, retained prefix and base64 text overlap during capture. Capture and encoded capture bytes coexist during emit; stdout adds a newline. Prefix backing identity is unestablished. | Versioned client capture; host bytes and client stdout bytes are different representations. | reply capture → client emit and exit | — |
| fr6 | Generic and typed capture — controller | source: Retained text is made before parsing. Generic capture JSON survives a clone into typed Capture; generic and typed base64 coexist during validation. Lossy text length need not equal retained source-byte count. | Accepted capture; malformed/oversized paths have separate retention behavior. | capture parsing → typed capture scope ends; generic capture survives into assembly | — |
| fr7 | Decoded bytes and parsed host reply — controller | source: Strict base64 decode allocates host bytes. Raw client Output, generic capture, typed base64 and decoded bytes coexist; parsed host Value is added before decoded bytes leave scope. | Successful capture validation and host JSON parsing. | base64 decoding → decoded vector scope ends; parsed reply retained | — |
| fr8 | Envelope and rendered text — controller | source: Borrowed input and envelope coexist. Recursive sorting clones subtrees; pretty serialization adds a String while the Value remains live. Sort temporaries are not claimed to survive the sort. | Final envelope rendering; successful stdout adds a newline. | envelope construction → print returns and CLI exits | — |
| fr9 | ordinary_small — fresh shipped controller | measured: 9,435 bytes Host reply bytes; client stdout 13,420 bytes; final envelope 32,035 bytes. Sampled maximum resident 6,750,208 bytes and physical footprint 1,556,816 bytes; 32 successful samples over 43,041,375 ns, starting 1,277,166–1,458,000 ns apart against a requested 1,000,000 ns cadence. | Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr10 | independent_query — fresh shipped controller | measured: 1,826,055 bytes Host reply bytes; client stdout 2,435,586 bytes; final envelope 4,737,755 bytes. Sampled maximum resident 57,966,592 bytes and physical footprint 52,593,048 bytes; 138 successful samples over 187,629,834 ns, starting 1,340,792–1,468,791 ns apart against a requested 1,000,000 ns cadence. | Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr11 | eight_phase_maximum — fresh shipped controller | measured: 1,830,373 bytes Host reply bytes; client stdout 2,441,346 bytes; final envelope 4,751,545 bytes. Sampled maximum resident 57,606,144 bytes and physical footprint 52,232,600 bytes; 150 successful samples over 202,997,208 ns, starting 1,129,000–1,465,916 ns apart against a requested 1,000,000 ns cadence. | Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr12 | actor_maximum — fresh shipped controller | measured: 603,354 bytes Host reply bytes; client stdout 805,316 bytes; final envelope 1,904,230 bytes. Sampled maximum resident 38,879,232 bytes and physical footprint 31,506,816 bytes; 300 successful samples over 424,208,000 ns, starting 1,213,000–3,434,375 ns apart against a requested 1,000,000 ns cadence. | Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr13 | control_character_exec — fresh shipped controller | measured: 9,491,469 bytes Host reply bytes; client stdout 12,656,138 bytes; final envelope 22,740,116 bytes. Sampled maximum resident 159,973,376 bytes and physical footprint 154,665,464 bytes; 578 successful samples over 786,891,792 ns, starting 1,112,750–1,546,875 ns apart against a requested 1,000,000 ns cadence. | Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr14 | Actor backing and page-padded views — host / actor workers | logical: 30,995,584 bytes Logical evidence-plus-authority backing capacity, counted once; separate private custody 524,288 bytes. Issuer authority requested 132,736 bytes, worker mapped 147,456 bytes; subject requested 264,320 bytes, mapped 278,528 bytes. Observed page size 16,384 bytes explains padding. These are capacities/view lengths, not reply bytes or measured residency. | Actor maximum response workload; distinct backing per actor. Source geometry and native worker mapping metadata corroborate each other. | actor setup → owner-specific teardown | — |

<!-- END GENERATED FOOTPRINT RESPONSE -->

The native response rows describe single repetitions. Memory values are maxima
among successful samples with verified lifetime coverage; resident and physical
footprint maxima can occur in different samples and are not added. A sampled
maximum cannot show a peak shorter than the spacing between sample starts, and
samples cannot locate parser stages. A later failed inspection stays a failed
inspection, not zero memory. Unit assertions establish representation
coexistence at their own boundaries, in a separate process.

## State remaining after a run

Source rows here describe what can remain after a run and who owns its ending;
only a measured row carries a state. At CLI return, `present`,
`absence confirmed` and `unknown` refer to the stated inventory and boundary,
and a failed inspection remains unknown. Erasure, native release, unmapping,
exit and reap are different endings, and CLI return establishes none of them.

<!-- BEGIN GENERATED FOOTPRINT AFTERMATH -->

| ID | Resource / owner | Quantity / mechanism | Conditions | Interval | At CLI return |
| --- | --- | --- | --- | --- | --- |
| fa1 | Asynchronous host retirement — host | source: [LIMITS `host_exit_delay`](LIMITS.md) Schedules retirement after replying. A live host at CLI return may still be in this interval; its generation needs an independent end observation. | Completion with delivered reply. | reply sent → host exit | — |
| fa2 | Submitted work after client timeout — host / workers | source: A post-invocation client deadline ends the client wait without cancelling submitted work. Gate release, signalling and fixture cleanup are later interventions. | Client deadline after submission, including actor form. | irreversible submission → resource-specific completion or failure | — |
| fa3 | Authority erasure and detachment — host / actor workers | source: Shared erasure requires a reaped or never-launched owner; unresolved workers withhold erasure while host detachment proceeds. Private custody is erased/disposed separately. Native release does neither. Native process exits do not directly observe shared-byte erasure, host unmapping, private disposal, native release or parent reap in the timed-out run. | Authority-bearing actor teardown; component receipts do not establish this run’s native unmapping. | actor cleanup → each owner-specific ending | — |
| fa4 | Baseline installation state — registry / launchd files | source: Plain run inventory compares registry state and directory names. Pre-existing installed services are baseline, not run-created apparatus. Name equality does not establish every object identity. | Explicit baseline inventory around a plain run. | before invocation → post-run inventory comparison | — |
| fa5 | Requested effects and descendants — specimen | source: Requested file effects and surviving exec descendants remain separate from apparatus residue. Leader exit or stream EOF does not establish descendant exit. | Specimens that request writes or exec. | requested operation → effect-specific removal or descendant exit | — |
| fa6 | Requested output and observer resources — caller / harness | source: Envelope files, gates, meters, staging and exit watchers have caller/harness ownership. Their removal cannot substitute for the pre-intervention product snapshot. | Artifacts explicitly requested or created for observation. | caller/harness preparation → recorded owned cleanup | — |
| fa7 | Serial completion process observations — inventoried hosts / workers / validators | measured: 6 observations Three ordinary and three actor completions: every inventoried host, worker and validator generation had exited in its first post-return snapshot. Snapshot starts 87,334–145,583 ns and ends 5,234,792–6,125,000 ns after the recorded CLI-return observation. Repetitions are serial with intervening fixture cleanup; no accumulation or instant-return claim. | Ordinary shipped app; actor disposable instrumented host with unchanged signed workers. Snapshot follows return and precedes fixture cleanup. | CLI return observed → first post-return snapshot complete | absence confirmed |
| fa8 | Held timeout process observations — invoked host / worker(s) / validator | measured: 2 observations One ordinary and one actor timeout: every inventoried required generation remained present through the primary post-return snapshot. Later independent exits followed explicitly recorded harness gate release; they establish assisted continuation, not autonomous teardown at CLI return. | Held invoked work; actor metadata retains accepted custody, settled delivery and a candidate handle with releases pending. | CLI return observed while gate remains closed → primary snapshot completes before gate release | present |

<!-- END GENERATED FOOTPRINT AFTERMATH -->

The state column refers to the first post-return snapshot, not the
mathematical instant of CLI exit. Established process exit is distinct from
parent reap or disappearance of every process record. No measured row observes
erasure, unmapping, native release or parent reap after CLI return; the
measured rows observe process presence only. Owned staging cleanup and
retained evidence belong to the harness; neither rewrites the primary snapshot.

## Shared backing

A backing identity denotes one object; its mappings are views, not additional
backing.

<!-- BEGIN GENERATED FOOTPRINT BACKING -->

| Backing | Views / owners |
| --- | --- |
| evidence_per_worker | fw4: host; fw5: worker |
| authority_per_actor | fw6: host / actor workers |

<!-- END GENERATED FOOTPRINT BACKING -->

## Ending conditions

<!-- BEGIN GENERATED FOOTPRINT ENDINGS -->

| Ending event | Rows |
| --- | --- |
| release, expiry or cancellation | fw1 |
| activation, expiry or cancellation | fw2 |
| collection completion and validator exit | fw3 |
| host unmapping attempted; native success not recorded | fw4 |
| worker exit ends its references | fw5 |
| shared erase eligibility, host unmap and worker exit are separate | fw6 |
| final erase and private buffer disposal | fw7 |
| native release and table disposal are separate | fw8 |
| descriptor close, not mapping disposal | fw9 |
| raw Output drops on caller return | fr1 |
| source mappings detach before later encoding | fr2 |
| validator receive scope ends | fr3 |
| host/client representation disposal is not externally observed | fr4 |
| client representation lifetime ends with exit | fr5 |
| typed capture disposal before final rendering | fr6 |
| decoded bytes drop before envelope rendering | fr7 |
| Value/String disposal after last use | fr8 |
| host process exit | fa1 |
| each identified process exits independently | fa2 |
| shared erasure, host unmap, private disposal and worker exit | fa3 |
| baseline comparison; no run-owned removal implied | fa4 |
| independent descendant exit or owned effect removal | fa5 |
| explicit output/observer cleanup | fa6 |
| independently observed controller exit | fr9, fr10, fr11, fr12, fr13 |
| host detach and worker exit are separate | fr14 |
| independent generation-qualified NOTE_EXIT events | fa7 |
| recorded gate release followed by independent exits | fa8 |
| gate release follows completed measurement | fw10, fw11, fw12, fw13 |
| last-use erasure, native release and disposal remain distinct | fw14 |

<!-- END GENERATED FOOTPRINT ENDINGS -->

## Grounding and coverage

Checks identify assertions to inspect after a change. An assertion pins its
stated relation; a receipt check validates observations without imposing a
machine-dependent threshold. Source citations identify mechanisms, not
measured consumption.

<!-- BEGIN GENERATED FOOTPRINT COVERAGE -->

| Row | Sources | Check / scope |
| --- | --- | --- |
| fw1 | [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`cpu_relax`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`proceed_delayed_observed_quiescence`](../tests/suites/runner_c_worker_harness/run.sh) (assertion): Selected effects remain absent across delayed release and occur afterward; no CPU measurement. |
| fw2 | [`wait_for_activation`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`activation_named_ordinal`](../tests/suites/runner_c_worker_harness/run.sh) (assertion): Setup is published with no early action/arrival; named activation then permits the visit. |
| fw3 | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`walkSchedule`](../runner/Sources/PWRunnerCore/ActorScheduler.swift); [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run. |
| fw4 | [`PWShmLayout`](../runner/Sources/PWRunnerCore/CWorker.swift); [`tearDown`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`c_swift_layout_agreement`](../tests/suites/runner_abi_layout/run.sh) (value): Compiled C and Swift layout constants agree; logical geometry, not residency.; [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run. |
| fw5 | [`mmap`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`init`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run. |
| fw6 | [`PWAuthorityLayout`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`ActorAuthorityRegion`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`c_swift_layout_agreement`](../tests/suites/runner_abi_layout/run.sh) (value): Compiled C and Swift layout constants agree; logical geometry, not residency.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fw7 | [`TokenCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`erase`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fw8 | [`handle_table`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_extension_release_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`terminal_erasure`](../tests/suites/runner_c_worker_harness/run.sh) (assertion): Terminal/last-use erasure controls distinguish authority publications from process storage. |
| fw9 | [`init`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) (assertion): Object identity, descriptor reuse and mapping teardown component controls. |
| fr1 | [`run_with_stdin`](../controller/src/utils.rs); [`run_client_stdin`](../controller/src/runner_client.rs) | [`response_footprint_success_boundaries`](../controller/src/runner_client.rs) (assertion): Ordered parser/render boundaries assert lengths, capacity at least length and scoped coexistence in the unit process.; [`valid_oversized_producer_is_receiver_loss_not_malformed_json`](../controller/src/runner_client.rs) (assertion): Oversized producer reports full received count and receiver loss, not malformed JSON. |
| fr2 | [`collectOutput`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`finish`](../runner/Sources/PWRunnerCore/ActorScheduler.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fr3 | [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) (assertion): Validator evidence controls assert accepted records and malformed/oversized framing refusal. |
| fr4 | [`replyAndExit`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`PWRunnerReplyCapture`](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift) | [`runReplyMaximumTests`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift) (assertion): Constructed field-complete reply fits transport allowance; not a reachable specimen or memory measurement.; [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fr5 | [`PWRunnerReplyCapture`](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift); [`emit`](../runner/Clients/PWRunnerClient/main.swift) | [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fr6 | [`capture_json_output`](../controller/src/utils.rs); [`parse_runner_client_output`](../controller/src/runner_client.rs) | [`response_footprint_success_boundaries`](../controller/src/runner_client.rs) (assertion): Ordered parser/render boundaries assert lengths, capacity at least length and scoped coexistence in the unit process.; [`multibyte_cut_counts_bytes_before_lossy_conversion`](../controller/src/runner_client.rs) (assertion): Retained source bytes are counted before lossy conversion. |
| fr7 | [`validate_capture`](../controller/src/runner_client.rs); [`decode_base64`](../controller/src/runner_client.rs) | [`response_footprint_success_boundaries`](../controller/src/runner_client.rs) (assertion): Ordered parser/render boundaries assert lengths, capacity at least length and scoped coexistence in the unit process. |
| fr8 | [`sort_value`](../controller/src/json_contract.rs); [`render_envelope`](../controller/src/json_contract.rs) | [`response_footprint_success_boundaries`](../controller/src/runner_client.rs) (assertion): Ordered parser/render boundaries assert lengths, capacity at least length and scoped coexistence in the unit process. |
| fa1 | [`replyAndExit`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fa2 | [`deadline`](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift); [`replyAndExit`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fa3 | [`tearDown`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`finish`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`finish`](../runner/Sources/PWRunnerCore/ActorScheduler.swift) | [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fa4 | [`inventory`](../tests/suites/run_effects/check_installs_nothing.py) | [`main`](../tests/suites/run_effects/check_installs_nothing.py) (assertion): Registry digest/reported registry and plist-directory inventory remain unchanged in this scoped control. |
| fa5 | [`observe_survivor`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) | [`main`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) (assertion): Same-generation descendant answers after CLI return; later fixture release is separate. |
| fa6 | [`close`](../tests/lib/run_capture.py); [`cleanup`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) | [`main`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) (assertion): Survivor observation precedes owned cleanup; failures retain cleanup ownership. |
| fr9 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr10 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr11 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr12 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr13 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr14 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fa7 | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) (assertion): Requires held-state/generation binding, exact inventory and primary-before-intervention order; process exits do not prove mapping disposal or reap. |
| fa8 | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) (assertion): Requires held-state/generation binding, exact inventory and primary-before-intervention order; process exits do not prove mapping disposal or reap. |
| fw10 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw11 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw12 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw13 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw14 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |

<!-- END GENERATED FOOTPRINT COVERAGE -->
