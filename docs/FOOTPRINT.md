# Resource footprint

This document records what a run demands, holds and leaves behind, one row
per resource. Each row is one of three kinds. A measured row reports an
observation under its stated conditions. A logical row states a capacity that
follows from the compiled layout and the admitted plan, not a measurement. A
source row describes a mechanism and carries no quantity of its own; it may
cite the LIMITS allowance that bounds it. Conditions and intervals belong to
each row; no row establishes a universal memory ceiling. Add quantities only
when their units, backing and overlapping lifetimes support the sum; native
memory metrics are never added to logical capacity or encoded bytes.

## Examination

Examine PW's footprint through three questions:

1. What work, resource retention or timing obligations does PW impose unnecessarily?
2. Can we remove them or express the condition we actually need, while preserving
   witnessing and bounded progress?
3. What freedom does that give the system to schedule PW, and what costs or
   response changes do we observe?

## Provenance of measured rows

Response rows fr9–fr13 describe the historical JSON/base64 implementation. Their
values are unavailable as footprint evidence for this typed/binary prototype;
no fresh prototype measurement is asserted here. They were transcribed from run id
`20261107T035203Z_446642a9`, output directory
`runs/footprint-opt-targeted-final-02`, case
`witness_contract/response_footprint`. Its artifact inventory identifies the
signed binaries measured; its response receipts retain the samples, transported
bytes, conditions and observer cost.

The other measured rows retain observations from run id
`20261106T210300Z_381f3d39`, output directory
`footprint-targeted-20261106-01`, cases `witness_contract/held_phase_footprint`
and `run_effects/aftermath_footprint`. That run is archived as
`historical-footprint-measurements.tar.gz`, with an index of file hashes beside
it, under `optimization-evidence/` in the retained response run above. The
archive preserves the original run identity and binary hashes; those rows do
not describe the later response run's binaries.

[tests/RETAINED.json](../tests/RETAINED.json) lists the run holding the identified
copy below. Test output is gitignored, so these receipts and the archive exist
only in a checkout that retained them.

The response run and its two historical evidence directories are preserved
byte-for-byte in `footprint-opt-targeted-final-02.tar.gz` under
`tests/out/runs/worker-wait-review-final-01/worker-wait-review/archives/`.
`worker-wait-review/archive-index.json` records the original run identity and file
hashes. This identified copy replaces the original output directory; it does
not change the provenance or quantities of these measurements.

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
| Authority region or custody sizing or disposal | Logical capacities and the accepted custody length | fw6, fw7, fw14, fr14 | Residency; erasure after CLI return, which no measured row observes |
| Any change | Process presence at the first post-return snapshot | fa7, fa8 | Mapping disposal and reap |

## Waiting and retained resources

Elapsed waiting does not establish idle CPU. Measured actor rows come from a
disposable instrumented host with unchanged signed workers; their timing does
not describe an uninstrumented host.

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

<!-- BEGIN GENERATED FOOTPRINT WAITING -->

| ID | Resource / owner | Quantity / mechanism | Conditions | Interval | At CLI return |
| --- | --- | --- | --- | --- | --- |
| fw1 | Release-word polling — active worker | source: [LIMITS `worker_proceed_wait`](LIMITS.md) Continuously samples release/cancellation and expiry, with batches of yield hints. Requested-action quiescence is not CPU idleness. | Arrived phase awaiting collection release. | phase arrival → release accepted, expiry sampled or cancellation observed | — |
| fw2 | Parked actor polling — parked worker | source: Polls its activation word and can service inbound authority while parked. | Actor prepared before its next scheduled visit. | setup or previous visit completion → named activation, cutoff or exit request | — |
| fw3 | Collection orchestration — host / validator | source: Host polls/sleeps while collecting; an eligible phase launches a separate validator. Their demand is separate from worker polling. | Ordinary and actor collection; validator only for eligible queries. | worker readiness or arrival → collection ends; validator ends independently | — |
| fw15 | Ordinary final-completion observation — host | source: After the last collection, the retained readiness pipe can end a bounded wait on hangup. Periodic publication checks remain; notification neither establishes done nor replaces owned reap. No descriptor, thread or worker write is added; scheduling and energy effects are unmeasured. | Ordinary final wait with a retained ready pipe; unusable or consumed notification falls back to bounded sleeps. | last collection released → done observed, owned child status ends polling, or allowance expires | — |
| fw4 | Evidence backing / host view — host | logical: 3,675,920 bytes One fixed evidence backing per worker, initialized before spawn; host and worker mappings are views of the same object. | Each ordinary worker or actor, independent of requested action count. | mapping preparation → host session teardown | — |
| fw5 | Evidence worker view — worker | source: Aliases the evidence backing; do not add its logical capacity to the host view as a second backing object. | Each launched worker. | worker maps launch descriptor → worker process exit | — |
| fw6 | Authority regions — host / actor workers | source: Per actor: 1152 + (inbound slots + outbound slots) × 16448 requested logical bytes, including actors with no slots. The worker maps the observed object size, which can include page padding; it remains a view of the same backing. Bearer bytes are outside the encoded reply. | Authority-bearing actor plan; one distinct backing per actor, host/worker views. | authority setup before launch → host detachment and worker exit, independently | — |
| fw7 | Private token custody — host | logical: [LIMITS `extension_token_storage`](LIMITS.md) One fixed private buffer per admitted token; delivery copies it into the recipient actor's inbound slot. Last-use erasure resets payload state but retains its allocation. | Authority-bearing actor plan; accepted lengths are separate from capacity. | custody preparation → custody finish | — |
| fw8 | Candidate handles / fixed table — actor worker | logical: 512 bytes Fixed handle table storage remains after native release. Candidate count and native result do not measure private kernel storage. | Each worker; successful consumes populate named candidates. | worker static storage → worker exit | — |
| fw9 | Launch-only descriptors — host | source: Evidence/authority launch descriptors close after spawn; policy/ready pipes have their own close boundaries. Mapping references survive descriptor close. | Prepared host resources; actual setup failures retain their own cleanup outcomes. | host setup → spawn or setup failure closes each descriptor | — |
| fw10 | ordinary held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,107,987,125–1,128,846,875 ns; worker:0 CPU 1,101,612,917–1,123,613,417 ns. Hold class 3: conservative elapsed 3,115,067,458–3,144,625,083 ns; worker:0 CPU 3,108,671,500–3,143,494,666 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw11 | actor_1 held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,119,694,584–1,130,162,833 ns; worker:0 CPU 1,114,585,833–1,131,120,833 ns. Hold class 3: conservative elapsed 3,118,528,958–3,141,749,458 ns; worker:0 CPU 3,114,453,583–3,144,314,292 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw12 | actor_3 held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,118,848,333–1,129,527,459 ns; worker:0 CPU 1,109,434,708–1,132,191,750 ns; worker:1 CPU 1,124,444,624–1,129,185,792 ns; worker:2 CPU 1,109,997,583–1,130,167,250 ns; worker aggregate 3,343,876,915–3,391,544,792 ns. Hold class 3: conservative elapsed 3,100,499,666–3,148,954,292 ns; worker:0 CPU 3,101,086,792–3,157,780,833 ns; worker:1 CPU 3,097,857,250–3,144,838,583 ns; worker:2 CPU 3,104,895,124–3,145,675,708 ns; worker aggregate 9,303,839,166–9,448,295,124 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw13 | actor_lifecycle held CPU — identified worker generations | measured: 6 holds Hold class 1: conservative elapsed 1,128,085,959–1,131,137,792 ns; worker:0 CPU 1,126,848,958–1,131,069,249 ns; worker:1 CPU 1,127,899,542–1,133,016,542 ns; worker aggregate 2,255,967,001–2,264,085,791 ns. Hold class 3: conservative elapsed 3,148,305,250–3,151,015,291 ns; worker:0 CPU 3,146,478,041–3,157,893,791 ns; worker:1 CPU 3,145,107,374–3,151,512,042 ns; worker aggregate 6,291,585,415–6,307,922,750 ns. Each worker and busy control exceeded its matched sleeping control; no idle-wait claim. Declared accounting quantum 10,000,000 ns. | Two declared duration classes, three repetitions each. Ordinary shipped app; actor instrumented host with unchanged workers. Power observations: battery power, discharging. | acknowledged gate then first endpoint batch → second endpoint batch before release | — |
| fw14 | Held actor custody / delivery / candidate — issuer / subject / host | measured: 212 bytes Actual accepted custody length and equal settled first delivery length, not buffer capacity. Across six holds, issuer is parked after its first transfer; subject has completed H1, holds the read-bearing visit without release, and has H2 and both releases pending. Private custody remains mapped and unerased for a later transfer; D2 is unpublished. No bearer bytes were captured. | Instrumented pre-collection metadata bound to the acknowledged held gate and unchanged marker/target; named references retained. | completed first consume and held next visit → post-measurement gate release | — |
| fw16 | Ordinary first-arrival observation — host | source: After a received ready byte, the host has one bounded resampling opportunity for first arrival or done before its first ordinary sleep. This adds local host work and can avoid a whole poll-period wait; no mapping, descriptor, thread or worker communication is added. CPU, energy and coalescing effects are unmeasured. | Ordinary execution before first collection; no initial resampling without a received ready byte. Clock, sample and remaining-allowance bounds retain the normal sleep fallback. | initial ordinary polling after readiness → arrival or done observed, or resampling bound reached | — |

<!-- END GENERATED FOOTPRINT WAITING -->

## Response storage and transport

The source rows describe representations in the order they arise: validator
records (fr3), host collection copies (fr2), the encoded reply (fr4), client
capture and stdout (fr5), the controller’s raw streams (fr1), typed capture or
rejected bytes (fr6), retained host bytes and typed reply (fr7), and JSON
presentation (fr8).

A retention allowance does not bound collection memory. Historical measured
rows used fresh controllers running the JSON implementation. The retained
JSON-control instrumentation does not measure the prototype binary path.

The native response rows describe single repetitions. Memory values are maxima
among successful samples with verified lifetime coverage; resident and physical
footprint maxima can occur in different samples and are not added. A sampled
maximum cannot show a peak shorter than the spacing between sample starts, and
samples cannot locate parser stages. A later failed inspection stays a failed
inspection, not zero memory. Unit assertions establish representation
coexistence at their own boundaries, in a separate process.

<!-- BEGIN GENERATED FOOTPRINT RESPONSE -->

| ID | Resource / owner | Quantity / mechanism | Conditions | Interval | At CLI return |
| --- | --- | --- | --- | --- | --- |
| fr1 | Complete child stream collection — controller | source: [LIMITS `controller_output`](LIMITS.md) Collects complete stdout/stderr before making retained prefixes. Raw Output remains borrowed through capture and host parsing, then drops before final rendering. | Binary client capture or failure output; complete received counts differ from retained counts. The retention allowance does not cap collection memory. | child pipes opened → run_client_stdin returns | — |
| fr2 | Collection copies from mappings — host | source: Copies published slots/profile/phase values while source mappings still exist; session teardown precedes later reply assembly. Actor reply metadata survives authority teardown. | Ordinary and actor outputs; authority contents are not response payload. | output collection → last reply-model use; source mappings end earlier | — |
| fr3 | Validator framing and decoded records — host | source: Raw bounded validator output and decoded records coexist during decoding; returned records/counts outlive the temporary raw Data. | Eligible query phases; repeated results contribute metadata to the final reply. | validator output drain → raw Data last use; decoded records retained separately | — |
| fr4 | Typed reply, encoded bytes and XPC — host / client | source: Typed reply fields overlap binary host Data during encoding. Primitive and frame bounds constrain encoded representations, not live memory; XPC and Foundation physical copying remain unestablished. | Production binary reporting, including rich degradation or an independent minimal report. | reply assembly → callback and representation last use | — |
| fr5 | Binary capture and client stdout — client | source: [LIMITS `client_reply_retention`](LIMITS.md) Incoming host Data and the retained byte prefix overlap during capture. The typed capture and its binary encoded Data coexist during emit; client stdout has no newline. Base64 is deferred to controller JSON presentation. Prefix backing identity remains unestablished. | Versioned binary client capture; host reply and capture frame are distinct byte sequences. | reply capture → client emit and exit | — |
| fr6 | Typed capture and rejected bytes — controller | source: The complete raw Output is borrowed while binary decoding allocates owned typed fields. An admitted capture survives into envelope rendering; rejected retained bytes are kept without lossy text conversion. No generic capture JSON tree is built. | Production capture admission; received counts, retained counts and submission evidence remain separate. | binary capture decoding → typed capture or rejected-byte last use during presentation | — |
| fr7 | Retained host bytes and typed reply — controller | source: The admitted capture owns retained host bytes while binary decoding creates typed reply fields. Both survive into final rendering. Decoded collection slots and owned text/byte lengths consume a per-document budget; this is not a process-memory ceiling. | Complete admitted capture and host frame; malformed host bytes remain retained beside a decode diagnostic. | host binary decoding → capture and typed reply last use during rendering | — |
| fr8 | Borrowed envelope and rendered JSON — controller | source: The envelope borrows typed inputs. Generated serializers project converted records directly; public byte fields create base64 text during rendering. Pretty serialization adds a complete String while the typed inputs remain live; converted records do not pass through a generic JSON tree or recursive sorting. | Final envelope rendering; successful stdout adds a newline. | envelope construction → print returns and CLI exits | — |
| fr9 | ordinary_small — historical JSON controller | measured: 9,441 bytes Host reply bytes; client stdout 13,428 bytes; final envelope 32,056 bytes. Sampled maximum resident 6,766,592 bytes and physical footprint 1,573,200 bytes; 36 successful samples over 52,777,333 ns, starting 1,310,875–2,938,375 ns apart against a requested 1,000,000 ns cadence. | Historical JSON/base64 control measurement; unavailable as typed-transport evidence. Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr10 | independent_query — historical JSON controller | measured: 1,826,061 bytes Host reply bytes; client stdout 2,435,594 bytes; final envelope 4,737,776 bytes. Sampled maximum resident 32,784,384 bytes and physical footprint 27,378,048 bytes; 132 successful samples over 180,653,250 ns, starting 1,345,041–1,511,667 ns apart against a requested 1,000,000 ns cadence. | Historical JSON/base64 control measurement; unavailable as typed-transport evidence. Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr11 | eight_phase_maximum — historical JSON controller | measured: 1,830,379 bytes Host reply bytes; client stdout 2,441,354 bytes; final envelope 4,751,566 bytes. Sampled maximum resident 32,882,688 bytes and physical footprint 27,476,352 bytes; 144 successful samples over 195,090,375 ns, starting 1,115,000–1,470,625 ns apart against a requested 1,000,000 ns cadence. | Historical JSON/base64 control measurement; unavailable as typed-transport evidence. Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr12 | actor_maximum — historical JSON controller | measured: 603,360 bytes Host reply bytes; client stdout 805,324 bytes; final envelope 1,904,251 bytes. Sampled maximum resident 21,577,728 bytes and physical footprint 16,138,624 bytes; 290 successful samples over 419,666,542 ns, starting 1,230,500–2,019,083 ns apart against a requested 1,000,000 ns cadence. | Historical JSON/base64 control measurement; unavailable as typed-transport evidence. Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr13 | control_character_exec — historical JSON controller | measured: 9,491,475 bytes Host reply bytes; client stdout 12,656,146 bytes; final envelope 22,740,137 bytes. Sampled maximum resident 91,095,040 bytes and physical footprint 85,737,928 bytes; 572 successful samples over 780,180,041 ns, starting 1,107,416–1,567,709 ns apart against a requested 1,000,000 ns cadence. | Historical JSON/base64 control measurement; unavailable as typed-transport evidence. Single repetition on macOS-26.7.1-arm64-arm-64bit-Mach-O; battery power, discharging; no indicated sleep overlap. Worker, host, exec-child and observer demand excluded. | first successful generation-qualified sample → last successful generation-qualified sample | — |
| fr14 | Actor backing and page-padded views — host / actor workers | logical: 30,995,584 bytes Logical evidence-plus-authority backing capacity, counted once; separate private custody 524,288 bytes. Issuer authority requested 132,736 bytes, worker mapped 147,456 bytes; subject requested 264,320 bytes, mapped 278,528 bytes. Observed page size 16,384 bytes explains padding. These are capacities/view lengths, not reply bytes or measured residency. | Historical JSON response workload geometry; no fresh typed-transport memory observation. Actor maximum response workload; distinct backing per actor. Source geometry and native worker mapping metadata corroborate each other. | actor setup → owner-specific teardown | — |

<!-- END GENERATED FOOTPRINT RESPONSE -->

## State remaining after a run

Source rows here describe what can remain after a run and who owns its ending;
only a measured row carries a state. At CLI return, `present`,
`absence confirmed` and `unknown` refer to the stated inventory and boundary,
and a failed inspection remains unknown. CLI return establishes no ending. The
state column refers to the first post-return snapshot, not the mathematical
instant of CLI exit. Established process exit is distinct from parent reap or
disappearance of every process record. No measured row observes erasure,
unmapping, native release or parent reap after CLI return; the measured rows
observe process presence only. Owned staging cleanup and retained evidence
belong to the harness; neither rewrites the primary snapshot.

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

Rows grouped by the event that ends their interval. Erasure, native release,
unmapping, exit and reap are different endings; one does not establish another.

<!-- BEGIN GENERATED FOOTPRINT ENDINGS -->

| Ending event | Rows |
| --- | --- |
| release, expiry or cancellation | fw1 |
| activation, expiry or cancellation | fw2 |
| collection completion and validator exit | fw3 |
| terminal observation or sentinel allowance | fw15 |
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
| raw Output drops before final rendering | fr6 |
| owned records drop after presentation | fr7 |
| typed records and rendered String drop after last use | fr8 |
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
| first observation or bounded fallback | fw16 |

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
| fw15 | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`waitExitNs`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerFinalWaitTests`](../runner/Tests/PWRunnerCoreTests/CWorkerFinalWaitTests.swift) (assertion): Controlled final-only notification, publication before delayed exit, owned reap, fallback and remaining allowance; not CPU, energy or coalescing measurements. |
| fw4 | [`PWShmLayout`](../runner/Sources/PWRunnerCore/CWorker.swift); [`tearDown`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`c_swift_layout_agreement`](../tests/suites/runner_abi_layout/run.sh) (value): Compiled C and Swift layout constants agree; logical geometry, not residency.; [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run. |
| fw5 | [`mmap`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`init`](../runner/Sources/PWRunnerCore/ActorSession.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run. |
| fw6 | [`PWAuthorityLayout`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`ActorAuthorityRegion`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`c_swift_layout_agreement`](../tests/suites/runner_abi_layout/run.sh) (value): Compiled C and Swift layout constants agree; logical geometry, not residency.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fw7 | [`TokenCustody`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`erase`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift) | [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls.; [`runLimitsContractTests`](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift) (value): The extension storage bound and host custody layout agree; not residency. |
| fw8 | [`handle_table`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_extension_release_actor`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`terminal_erasure`](../tests/suites/runner_c_worker_harness/run.sh) (assertion): Terminal/last-use erasure controls distinguish authority publications from process storage. |
| fw9 | [`init`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`check`](../tests/suites/runner_unit/launch_descriptor_controls.py) (assertion): Object identity, descriptor reuse and mapping teardown component controls. |
| fr1 | [`run_with_stdin`](../controller/src/utils.rs); [`run_client_stdin`](../controller/src/runner_client.rs) | [`independent_binary_records_reach_typed_storage_without_text_conversion`](../controller/src/runner_client.rs) (assertion): Authored binary records establish typed admission, exact retained host bytes and byte counts; not a memory measurement.; [`malformed_capture_keeps_exact_bytes_and_no_recovered_submission`](../controller/src/runner_client.rs) (assertion): Malformed binary captures retain their exact bytes and cannot recover a submission claim; not a memory measurement. |
| fr2 | [`collectOutput`](../runner/Sources/PWRunnerCore/ActorSession.swift); [`finish`](../runner/Sources/PWRunnerCore/ActorScheduler.swift) | [`runCWorkerLifecycleTests`](../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift) (assertion): Controlled publications, cleanup ownership and confirmed child reap; not external observation of this run.; [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fr3 | [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`runValidatorEvidenceTests`](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift) (assertion): Validator evidence controls assert accepted records and malformed/oversized framing refusal. |
| fr4 | [`pwRunnerPorcelainReplyData`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`pwPorcelainEncode`](../runner/Sources/PWRunnerCore/PWPorcelain.swift) | [`runReplyFailureTests`](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift) (assertion): Retains binary normal, rich-failure and minimal-failure receipts; component reporting controls do not measure memory or XPC backing. |
| fr5 | [`PWRunnerReplyCapture`](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift); [`emit`](../runner/Clients/PWRunnerClient/main.swift) | [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fr6 | [`parse_runner_client_output`](../controller/src/runner_client.rs); [`TransportCapture`](../controller/src/runner_client.rs) | [`independent_binary_records_reach_typed_storage_without_text_conversion`](../controller/src/runner_client.rs) (assertion): Authored binary records establish typed admission, exact retained host bytes and byte counts; not a memory measurement.; [`malformed_capture_keeps_exact_bytes_and_no_recovered_submission`](../controller/src/runner_client.rs) (assertion): Malformed binary captures retain their exact bytes and cannot recover a submission claim; not a memory measurement. |
| fr7 | [`parse_runner_client_output`](../controller/src/runner_client.rs); [`charge`](../controller/src/porcelain.rs); [`decode`](../controller/src/porcelain.rs) | [`independent_binary_records_reach_typed_storage_without_text_conversion`](../controller/src/runner_client.rs) (assertion): Authored binary records establish typed admission, exact retained host bytes and byte counts; not a memory measurement.; [`arbitrary_rejected_host_bytes_survive_and_do_not_become_claims`](../controller/src/runner_client.rs) (assertion): Arbitrary rejected host bytes survive without a decoded reply or fallback eligibility; not a memory measurement. |
| fr8 | [`render_envelope`](../controller/src/json_contract.rs); [`Base64`](../controller/src/porcelain.rs); [`rust`](../docs/generate_porcelain.py) | [`renderer_borrows_nonclone_typed_payload_and_serializes_it_once`](../controller/src/json_contract.rs) (assertion): A non-clone typed payload is borrowed and serialized once; its public scalar facts are checked independently. This does not measure allocation or residency. |
| fa1 | [`replyAndExit`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fa2 | [`deadline`](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift); [`replyAndExit`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`runReservationAdmissionTests`](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift) (assertion): Reply capture round-trips retained bytes and counts; reservation/retirement ownership controls. |
| fa3 | [`tearDown`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`finish`](../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`finish`](../runner/Sources/PWRunnerCore/ActorScheduler.swift) | [`runActorAuthorityTests`](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift) (assertion): Custody, delivery acknowledgement/equality and quiescence-qualified teardown in component controls. |
| fa4 | [`inventory`](../tests/suites/run_effects/check_installs_nothing.py) | [`main`](../tests/suites/run_effects/check_installs_nothing.py) (assertion): Registry digest/reported registry and plist-directory inventory remain unchanged in this scoped control. |
| fa5 | [`observe_survivor`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) | [`main`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) (assertion): Same-generation descendant answers after CLI return; later fixture release is separate. |
| fa6 | [`close`](../tests/lib/run_capture.py); [`cleanup`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) | [`main`](../tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py) (assertion): Survivor observation precedes owned cleanup; failures retain cleanup ownership. |
| fr9 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Historical JSON-control receipt validation only; no typed/binary transport measurement. Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr10 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Historical JSON-control receipt validation only; no typed/binary transport measurement. Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr11 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Historical JSON-control receipt validation only; no typed/binary transport measurement. Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr12 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Historical JSON-control receipt validation only; no typed/binary transport measurement. Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr13 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Historical JSON-control receipt validation only; no typed/binary transport measurement. Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fr14 | [`main`](../tests/suites/witness_contract/check_response_footprint.py) | [`main`](../tests/suites/witness_contract/check_response_footprint.py) (receipt): Validates same-generation successful native samples, lifetime/units and exact transported representations; sampled values have no fixed threshold. |
| fa7 | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) (assertion): Requires held-state/generation binding, exact inventory and primary-before-intervention order; process exits do not prove mapping disposal or reap. |
| fa8 | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) | [`validate_receipt`](../tests/suites/run_effects/check_aftermath_footprint.py) (assertion): Requires held-state/generation binding, exact inventory and primary-before-intervention order; process exits do not prove mapping disposal or reap. |
| fw10 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw11 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw12 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw13 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw14 | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) | [`check_measurement`](../tests/suites/witness_contract/check_held_phase_footprint.py) (receipt): Checks gate/effects, same-generation endpoint samples, held actor publications, skew/sleep limits and worker/busy CPU above matched sleeping control; no fixed CPU threshold. |
| fw16 | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`expiredAfterResampling`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runCWorkerInitialWaitTests`](../runner/Tests/PWRunnerCoreTests/CWorkerInitialWaitTests.swift) (assertion): Controlled first-arrival, delayed application, published failure, pre-application exit, missing readiness and bounded fallback decisions; not CPU, energy or coalescing measurements. |

<!-- END GENERATED FOOTPRINT COVERAGE -->
