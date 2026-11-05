# Architecture reader transcript

## Task 1 — received: bounded onramp

Read only `packets/architecture-onramp.md` and `actor-example.json`. Inventory actors and setup modes, ordered schedule, ordinary query/attempt and extension counts, connecting references and unknowns. Do not evaluate the target document, execute the specimen or inspect other materials. Record tasks and answers here; stop at this checkpoint.

## Task 1 — initial understanding / answer

The request declares schema version 5 and specimen `extension_redelegation`. There are three actors: A has sandbox mode `unapplied`; B and C have mode `apply` and inline SBPL policies. Both B and C name default allow, file-read-data deny, file-write* deny, and a read allowance using `com.apple.app-sandbox.read`. B also names a file-issue-extension deny and a conditional allowance involving that extension class and extension. These are declarations, not observed effects.

Declared phase/action order:

1. `b_before` (B): `b_read_before`, a file-read-data path query paired with a `read_fresh` attempt.
2. `c_before` (C): `c_read_before`, the same query/attempt shape.
3. `initial_supply` (A): `a_issue` declares issuance of a file/read extension for the target as `ta`; `a_to_b` declares transfer of `ta` to B as delivery `db`.
4. `b_consume` (B): `b_consume_first` consumes `db`, naming handle `hb`.
5. `b_redelegate` (B): `b_read_after` query/attempt; `b_issue` declares a file/read extension as `tb`; `b_to_c` transfers `tb` to C as `dc`.
6. `c_consume` (C): `c_consume_second` consumes `dc`, naming handle `hc`.
7. `c_effect` (C): `c_read_after` query/attempt, then `c_release` releases `hc`.
8. `b_cleanup` (B): `b_release` releases `hb`.

Counts: 12 actions total: four ordinary actions containing four sandbox checks and four attempts, plus eight extension actions (two issue, two transfer, two consume, two release). Every ordinary check and attempt and both issue actions name `/private/tmp/pw-lookback-example/target`.

Connections: phase `actor_id` values refer to actors; transfer `recipient` values also refer to actors. The reference chains are `a_issue` → `ta` → `a_to_b` → `db` → `b_consume_first` → `hb` → `b_release`, and `b_issue` → `tb` → `b_to_c` → `dc` → `c_consume_second` → `hc` → `c_release`. Phase and step IDs label schedule entries. No explicit reference from `b_issue` to `hb` is present; their relationship is suggested by ordering and policy, not a direct handle link.

Unknown from this request alone: the exact meanings of `unapplied` and `read_fresh`; how actors map to processes, where policy is applied, how queries and attempts are scheduled within/across phases, and what completion/failure does to later actions. The representations, lifetimes and transport of tokens, deliveries and handles, the precise extension-policy semantics, and release effects are not specified here. There is no result evidence, target-file content or existence guarantee, so no success, denial, effective authority or prediction/enforcement relationship can be concluded.

No prompted or corrected understanding yet. Awaiting the next checkpoint.

## Task 2 — received: need checkpoint; target withheld

A teammate proposes acknowledging recipient delivery only when its scheduled phase starts, to simplify parked-worker work. Eventually prepare a review memo tracing the example through processes/channels, locating touched responsibilities and ordering, interpreting transfer timeout with later progress, and identifying compilation/application and final-cleanup evidence. For now provide only a tentative approach and information needs; consult nothing else and stop.

## Task 2 — prompted understanding / need checkpoint

Tentative approach: map the actor schedule onto actual process lifetimes and message paths, then mark each transfer's send, receive, acknowledgment, completion and recipient phase start. Compare the current ordering with the proposed acknowledgment timing at A→B and B→C. Check whether advancing the schedule depends on transfer acknowledgment, whether a recipient can receive while its phase is inactive, and what a timeout permits the sender, recipient and scheduler to do next. I cannot yet judge the proposal: the request shows intended action order but no execution or acknowledgment protocol.

For a partly reported run I would distinguish requested actions, emitted observations and unreported outcomes. I would correlate the transfer and subsequent events using the named actors, phases, steps and reference chains. Timeout plus later progress would call for identifying what timed out and what the later evidence actually establishes; it would not by itself establish non-delivery, successful consumption or successful file access.

Information needed:

- Process inventory and lifetimes: where the controller, scheduling, sandbox application, actor operations and reply handling live, and whether actors have separate processes.
- Channel topology and ownership: how requests, policy data, extension tokens, deliveries, acknowledgments and observations travel; what a parked worker does and can receive.
- Scheduling and synchronization contract: phase eligibility, transfer completion conditions, acknowledgment meaning, timeout scope, late-message handling, and continuation after failure or timeout.
- Output/evidence model: which fields report issue/transfer/consume/release and ordinary operations, whether missing output means unattempted or merely unreported, and how to correlate partial records with process/channel events.
- Compilation/application boundaries and evidence locations: which component compiles policy, which applies it, and which records distinguish those outcomes.
- Cleanup responsibilities and evidence: explicit releases versus process termination or other finalization, ownership of outstanding tokens/handles/resources, and how completion or incomplete cleanup is reported.

No corrected understanding yet. No target document or additional materials consulted; stopped at the need checkpoint.

## Task 3 — received: first-impression checkpoint

Skim the 24-page ARCHITECTURE.pdf candidate's title, opening, headings and prominent summaries/figures with limited attention. In at most 150 words state purpose, central account and expected understanding/use. Do not perform the full review task; only PDF, direct derivatives, supplied onramp/example and own history allowed.

Material exposure: created a direct text derivative at `/tmp/pw-arch-reader.txt`; read its first 150 lines (opening, topology diagram text and beginning of topology table), extracted heading-like lines, and viewed supplied page 02 image. No external links followed or other materials consulted.

## Task 3 — prompted first impression

This is an implementation-orientation tour for contributors tracing a run across processes, channels, evidence ownership and guarded boundaries. Its central account is that one-way sandboxing requires fresh workers, while orchestration and replies stay outside the tested policy; actor workers exchange extension authority through host-managed channels without making the host a sandbox-API caller. Ordering and evidence distinctions matter as much as topology.

I expect to leave able to locate responsibility for a proposed protocol change, trace actor handoffs and query/attempt sequencing, distinguish worker observations from host cleanup observations, and find the implementation/check references that warrant further review. The document also appears to explain verification, external-runner variation and known gaps. Its generated diagrams and citation tables promise navigation and mechanical consistency, expressly not proof that cited tests establish every claim.

Stopped at first impression; full consequential work task not yet performed.

## Task 4 — received: work-result checkpoint

Use the complete PDF to answer the previously supplied delivery-acknowledgment review task. Read naturally for that job; distinguish change requirements from partial-observation interpretation, cite headings/pages, preserve initial result without correction, and stop before whole-document review.

Material exposure: read direct PDF text for topology rows/notes (pp. 3–4), run sequence, actor handoff, implementation routes, budgets and evidence ownership (pp. 5–8), boundary guards and notes (pp. 10–12), and the known-gap index (p. 24). The relevant text was extracted from the complete supplied PDF. No citation targets were followed.

## Task 4 — initial work result after artifact reading

### Recommendation and proposed-change implications

Do not treat delayed recipient acknowledgment as a local parked-worker simplification. Today the source waits synchronously while the recipient acknowledges framing while parked, before host equality checking and usable/failed settlement, before the host answers the source. The source then records its observed answer or timeout and completes its phase. Only then can the host advance the serial schedule (Actor handoff and schedule advancement, p. 6).

In this specimen A's `initial_supply` visit precedes B's `b_consume` visit, and B's `b_redelegate` precedes C's `c_consume`. Waiting for those recipient visits to acknowledge would hold up the earlier source's exchange. This is not necessarily an endless deadlock: the document explicitly allows an exchange timeout to complete as failure and phase completion to permit advancement. It nevertheless changes successful handoff into delayed or failed exchange behavior under the existing protocol. Earlier B/C read-before visits do not provide acknowledgment opportunities for deliveries that have not yet been sent.

The proposal needs an explicit replacement completion/activation protocol or a narrower way to simplify servicing that retains parked acknowledgment. Review responsibilities spanning `ActorScheduler.swift`/`walkSchedule`, host `serviceOutbound`, `serviceTransfer`, `recordSourceAcknowledgements`, and worker `wait_exchange`/`service_inbound_once`. Preserve the distinct gates of framing acceptance, host byte equality, usable settlement, source-observed answer and phase completion. Preserve per-operation cells, custody lifetime/erasure and failed-visit quiescence. If activation or release rules move, the phase arrival/collection/numbered release/acknowledgment barrier must still precede requested actions. Pages 6 and 10–12 point to actor authority/handoff controls, scheduler tests, reply validation and order-barrier controls; these are review destinations, not checks I have executed or audited.

### Trace of this request

The Rust controller holds/admit-checks the request and sends it on stdin to the Swift client. The client obtains an effect-free NSXPC reservation and invokes execution once; launchd supplies the fresh XPC host. The host orchestrates and produces the reply without sandbox API calls. It launches three fresh C actor workers, each retained across its visits. A declares unapplied setup; B and C compile/apply their own policies once. There is no declaration-form issuer in this actor run (Why these processes exist, p. 1; Process topology, pp. 2–4).

Policy travels over stdin/fd 0; fd 3 carries shared evidence and reciprocal release signaling, fd 4 readiness, and actor fd 5 the actor's authority region. Other actors and validators do not map that actor's authority region. For each scheduled visit the host activates the actor, observes arrival and ownership, plans fresh eligible queries, collects through an unsandboxed validator checking the actor PID, closes collection, then issues the numbered release. The actor acknowledges and executes ordered actions (pp. 4–6).

B and C each first perform a read query/attempt. A then issues `ta` in A's process, publishes bounded outbound bytes and erases its native allocation. The host takes custody and erases outbound bytes; A's transfer asks for delivery `db` to B. Parked B acknowledges framing, the host checks equality and settles delivery, then answers A. Later B consumes `db` as `hb`. On B's next visit its read query is collected before its read/issue/transfer actions; B issues `tb` and transfers `dc` to parked C through the same custody protocol. C later consumes `dc` as `hc`, then on a further visit queries/reads and releases `hc`; B finally releases `hb`. This is the requested trace, conditional on reported progress and completion, not a claim that any call succeeds. Transport acknowledgment itself does not consume an extension.

### Reading timeout plus later progress

First distinguish a transfer exchange timeout from the client's `xpc_timeout`: the latter ends controller waiting while host work can continue (p. 7). For the transfer, inspect `transfers[]` for custody/copy/equality, recipient acknowledgment, settlement and source acknowledgment; correlate the step and references through `resources`. The exchange allowance is separate on each side. Host answer and completed source action are different observations; a late answer cannot rewrite the source's recorded timeout, and a later operation cannot reuse the expired cell (pp. 4, 6).

Later phase progress is compatible with an earlier failed transfer. It does not prove transfer success or establish native permission/revocation. Recipient acceptance proves framing only; consume requires committed, accepted, usable settlement. Look separately at `extension_events[]` for the worker's completed native issue/consume/release results, and at `steps[].attempt.fresh_read` for open/stat/read/close observations, identity and bounded bytes. A native pre-call marker without a published result remains unresolved; later progress or independent knowledge cannot fill in that missing result. Predictions and `query_first` must be read with their phase-specific collection/release/ownership evidence, not as proof of the attempted effect (pp. 5–8, 11–12).

### Compilation, application and cleanup evidence

For B/C inspect their worker setup/application evidence and policy-input receipt, with policy-transfer counts kept separate from the worker's `policy_read` account. The ready byte comes after compile in the timeline and does not alone establish apply. If compiled-object capture was requested, `actors[].compiled_profile` is admitted only with application, completion, identity and integrity checks; this example does not opt in. A has no application or compiled-profile receipt. A controller fallback `sbpl-check` diagnostic occurs only for admitted `xpc_error`, compiles in the controller context and is not application evidence (pp. 1, 5–8, 11).

For final cleanup inspect each actor's raw exit/reap facts and `actors[].subprocess.disposition`, with the controller's per-actor projection, separately from worker release results and `resources` lifetime outcomes. Shared authority erasure requires a reaped or never-launched owner; host private custody erasure is separate and occurs at last declared transfer use, including failed delivery. Erasing token storage is not native release. Failed visits require actor stop/reap before further activation; unresolved termination cancels remaining activation. Fatal interruption can skip worker cleanup, and absent confirmed reap the collection basis can be `execution_may_continue`. Neither a client timeout nor a final publication proves all execution/cleanup ended (pp. 4, 6–8, 11–12).

No corrected work result yet. Stopped at work-result checkpoint.

## Task 5 — received: whole-document checkpoint

Read the complete artifact ordinarily, including all figures/tables, document graph, BYOXPC and known gaps, without outside links or citation audits. Explain its account and changes in understanding; assess coherence, thread loss, consequential misunderstandings and essential outside knowledge. Separate actual confusion from hypothetical risks and optional detail from missing central explanation. Stop before targeted questions.

Material exposure: completed the remaining text/table reading, including boundary nodes, all document-graph nodes/edges, verification mechanisms, all BYOXPC text/nodes/edges and known gaps. Viewed the boundary (p. 9), document graph (p. 13) and BYOXPC (p. 20) figures in addition to the previously viewed topology. Read tables as inventories, without auditing citation targets. The tall document graph was useful chiefly at its group level; detailed relationships came from its tables. No outside materials consulted.

## Task 5 — initial whole-document response

The document's account is of an observation apparatus whose structure protects both execution isolation and the meaning of its evidence. Fresh workers take irreversible policy application; the host remains able to orchestrate and reply. Validators query living workers while requested actions are held. Release and ownership records establish which phase those predictions precede. Native call publications, transport settlements and process-disposition observations remain distinct even when they concern the same attempted operation. Actor authority transfer adds custody and delivery gates to that model, not a new host sandbox role. Client reservation and no-replay rules protect the execution boundary when answers disappear.

The later half explains how this account is maintained and deployed. Version gates, shared layouts, generated identities and evidence admission protect record boundaries. Goldens, independent worker/driver tests, lifecycle oracles and artifact inspection check different kinds of claims. Manifests/generators keep duplicated values, tables, diagrams and guide content aligned; this is explicitly weaker than proving every behavioral citation. BYOXPC changes bundle selection, signatures/entitlements, launchd registration and provenance while preserving the same local-helper execution arrangement. Registry ownership survives incomplete removal; verify actually runs a specimen, whereas validate inspects signatures and reconcile reports candidates. The closing gap index points back to lost replies without safe replay.

My first impression remains substantially right. The full read adds that this is also a maintenance/change-impact map, with a large account of documentation/build consistency, rather than only a runtime tour. BYOXPC is more consequential than a connection-name variation: worker entitlement read-back, helper inventory, caller authorization and ownership recovery matter. None of that reverses my handoff work result. The boundary notes reinforce the distinction between failed exchange completion and schedule advancement, and between erasure and native release.

For its primary job—orienting contributors to responsibilities and boundaries before detailed implementation reading—the document forms a coherent whole. The opening explains why the process split exists, the sequences make the topology actionable, and evidence ownership supplies the interpretation rules. I could answer the acknowledgment proposal without importing missing premises. The topology's aggregate arrows did not confuse me because the text identifies them as inventory and directs ordering questions to the sequences.

Where I actually lost the main thread was the document graph and its long node/edge tables (pp. 13–19). I shifted from following a run to scanning a maintenance reference. I could understand individual rows and the manifest→generator→copy/check structure, but not retain that entire graph as one navigable picture under ordinary attention. The text's phrase “The last figure” before the document graph also briefly made me expect the figures were finished; BYOXPC later has another “last figure.” This was a minor navigation distraction, not a mistaken technical conclusion. BYOXPC's opening recovered the runtime thread.

A plausible risk on fuller reading, not a confusion I actually had, is reading the final one-item Known gaps index as the complete list of consequential limitations. Other limitations appear in place without that label: unconfirmed reap, no global lifecycle deadline, exec descendants, validator replacement authenticity and unrecorded worker environment. The body clearly states them, but a reader using only the final index could miss them. Another plausible skim risk is treating the many Sources/Checks columns as behavior certification; repeated captions explicitly prevent that inference, so I do not identify a missing explanation there.

I still need outside references for exact field semantics, SBPL/native API behavior, exhaustive resource lifetimes, concrete command execution and the implementation of a replacement protocol. Those are appropriate follow-on details for this tour. The initial request example plus this artifact supplied the central process, channel and ordering explanations needed for the assigned review. I did not encounter an essential missing premise that prevented that job. The document graph's full inventory is useful optional lookup detail; its density is an attention cost, not missing central runtime explanation.

No targeted prompting or corrections have occurred yet. Stopped at whole-document checkpoint.

## Task 6 — received: targeted questions

(1) Compare the opening/final Known gaps indexing promise with previously named limitations: consequential mismatch or navigation risk despite stated scope? (2) Locate “last figure” and explain reader consequence. (3) Explain how reciprocal topology arrows and actor sequence distinguish recipient acknowledgment, source-observed answer and advancement; can the diagram alone answer? Artifact only; stop before final report.

## Task 6 — prompted answers and qualification

1. The opening (p. 1) says “Behavior that falls short of a stated promise” appears where the promise is stated in a paragraph opening “Known gap,” and is indexed in the last section. The final section (p. 24) says each gap is stated in full at the promise it limits and this list only points there. It does not promise an exhaustive limitations inventory. The lost-reply item matches that stated category. My previously named limits—unconfirmed reap, absence of a global deadline, exec descendants, replacement-validator authenticity and unrecorded worker environment—do not by themselves establish unindexed shortfalls from stated promises. Thus my earlier hypothetical skim risk remains only a navigation risk for a reader who assumes broader scope despite the opening's explicit qualification. I do not identify a consequential scope mismatch. This narrows my previous assessment; it does not change the technical review.

2. “The last figure is the graph those generators and rules draw over the documents” is the closing paragraph of How the system verifies itself on p. 12, immediately before The document graph on p. 13. BYOXPC then says “The apparatus itself ... has the last figure” on p. 20 before its own figure. The first use is literally premature. My actual consequence was briefly expecting no more figures and then updating that expectation; the BYOXPC heading and caption still made its role clear. It is a minor navigation wording defect, not an ambiguity about process order or evidence.

3. Process topology explicitly calls itself an inventory rather than a full protocol trace and notes aggregated reciprocal traffic, notably T8 and T16–T17 (p. 1). T17 points me to recipient delivery/framing acknowledgment; T16 to source outbound/request-answer traffic; T8 to phase arrival, numbered release, acknowledgment and completion. Their arrows do not alone specify order or success criteria. The p. 6 actor sequence supplies those: parked recipient validates framing and acknowledges without consuming; host compares bytes and settles usable/failed before answering the source; source publishes the answer it observed or its own timeout/fault; matching completed source action is needed for host source acknowledgment. A late host answer cannot rewrite source timeout. The worker completes its phase after actions return, and the host services custody before checking completion and advancing. Successful transfer is not required for advancement; failed-visit stop/reap and cancellation rules still apply. Hence a recipient framing acknowledgment, host answer, source-observed result and phase completion are separate observations. The diagram locates channels and participants; the sequence and boundary notes (pp. 11–12) are necessary to interpret timeout with later progress.

Stopped before final report.

## Task 7 — received and completed: final first-reader report

Requested a short report at `../reports/architecture-first.md` covering initial/settled understanding, work result, onramp and targeted-question effects, coherence, plausible misunderstandings, outside knowledge and PDF expansion costs. Wrote that report using only authorized materials and this transcript. The report retains the qualified Known gaps assessment, identifies the premature “last figure” as minor, and separates expanded-inventory page cost from the source's maintenance topic transition. No new source exposure, tests or citation audits. Final handoff: the architecture supported the consequential task; no unresolved consequential misunderstanding identified. Stopped.
