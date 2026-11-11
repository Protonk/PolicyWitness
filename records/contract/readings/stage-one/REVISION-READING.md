# Targeted revision reading after the prompted round

This is a targeted reading of a revision, after the completed first reading and the 29 prompted answers. It is not a second fresh isolated reading. Earlier conclusions below refer to my remembered first/prompted understanding and to the old-side text supplied in the delta. I did not reopen or alter JOURNAL.md or PROMPTED.md.

## Exact scope and limits

The input directory was `/private/tmp/pw-contract-stage-one-revised`. I read all 1,263 lines of DELTA.diff, including all 43 hunks and their eight-line context, before opening current-contract passages for interpretation. One attempted display of delta lines 241–460 was truncated; I reread that entire range as 241–350 and 351–460. No delta passage is being credited solely from a truncated display.

I then read these exact line ranges from the 4,487-line current CONTRACT.md, with line numbers: 7–26; 149–229; 283–333; 506–556; 603–646; 874–899; 1144–1181; 1394–1429; 1627–1650; 1937–1946; 2205–2265; 2355–2410; 2474–2499; 2648–2705; 2726–2746; 2774–2804; 2810–2855; 2918–3055; 3060–3127; 3185–3230; 3359–3446; 3491–3518; 3535–3544; 3582–3640; 4026–4040; and 4378–4445. Search output additionally exposed current lines 656, 657, 1330, 1453 and 1888 outside those ranges. Current-contract searches located component-definition anchors, capture fields, rendered bindings, structured operands and actor setup/lifetime quantities; their displayed matching lines were also read. A search for `reply.actors[a]`, receipt-alias wording and log/logs wording returned no matches. These were targeted searches, not a full rereading of the current contract.

The only input files opened in this round were DELTA.diff and this current CONTRACT.md. Their own support paragraphs were read as contract text; no linked source, test, support note, repository file or external document was opened. Shell commands were used only to count/read/search those files and write this separate artifact. No PolicyWitness tool, product, build, helper, test or native experiment was executed. The output was read mechanically for section and hunk-coverage counts. Nothing here verifies the implementation, the generation process, the linked evidence, or whether an implementation changed along with the prose.

All contract line numbers below refer to the CURRENT contract unless explicitly identified as delta lines. Hunk numbers count the `@@` headers in delta order. A statement that the contract now specifies something is not an assertion that I tested it. Related edits are grouped, and the coverage table accounts for every hunk.

## Changed understanding

### R1. Fixed digest widths and equipment representations

Hunks 1, 31, 32 and part of 33 make shared widths explicit: SHA-256 is 32 raw bytes or 64 lowercase hexadecimal characters; the admitted CodeDirectory hashes are 20 raw bytes or 40 lowercase hexadecimal characters (175–219). Inventory, expected worker identity, unsigned-input digest, signed-file digest and static/live CodeDirectory fields refer to those definitions (3068–3071, 3085–3099, 3118–3121, 3195).

I now have a common representation rule for these fields rather than separately repeated numbers. This does not collapse their subjects: a protocol-source digest, signed-file SHA-256 and CodeDirectory hash still describe different things. My earlier separation of public identity, schema identity, worker protocol identity and executing equipment remains. The preceding exact-admission rule still says equality supplies only that boundary's identity match (18–26); the worker identity still requires equipment/launch evidence for association with the executing binary (184–189).

Unresolved: a correctly sized string is not evidence that its hash was computed from the claimed object, that a signature is valid, or that the live process is bound. The new definitions do not answer the earlier direct-source-test regeneration/freshness question. The support remains source-read and excludes several runtime claims (221). Confidence is high about the stated representations, not their implementation enforcement.

### R2. “Actor and phase evidence” names the existing scope

Hunks 2 and 28 rename the surface/table title from “Actor evidence” to “Actor and phase evidence” (delta lines 70–88 and 720–742; current heading 2802). The surrounding current section includes actor process rows, phase ownership, activation observations and schedule/gate facts (2810–2851, 2918–3052).

I understand the title as naming the records already present, not adding a new execution form or extending ordinary checks to every retained report. My earlier distinction between ordinary executed replies, preparation refusals and retained reporting failures remains: the latter retain assembled associations under the degraded-form guarantee (2831–2851).

Unresolved: the reader-scope reconciliation gap remains explicit. The title alone cannot resolve it or establish that every actor/phase association has been validated. High confidence in this limited title change.

### R3. The cause definition no longer mentions log text

Hunk 3 removes “log text” from the sentence preserving individual observation scopes; query answers and attempt returns remain named (delta lines 89–109, current 420–437 as carried in the delta). The prohibition on turning permission-shaped returns into established sandbox cause remains in the same passage.

I no longer treat that particular sentence as an explicit statement about log-text scope. It does not grant logs any stronger causal meaning, establish a log channel, or withdraw the need for supporting evidence. The current attempt interpretation still requires supporting evidence for attribution to an enforcing mechanism (2260–2263). My earlier refusal to infer sandbox cause from a permission failure remains.

Unresolved: the targeted search found no remaining log/logs wording, so this reading supplies no positive contract for log evidence. Removing a named example is not an empirical finding about logs. High confidence in the deletion's narrow effect.

### R4. Contract and specimen label are expressly required non-null strings

Hunk 4 makes requiredness explicit in both `contract` and `specimen_id` meanings (514–515). The assertion must exactly match the target identity, and the caller label may still be empty and is separate from worker PID or actor ID. The existing host-admission order and no-worker/no-validator refusal consequence remain (531–545).

My earlier understanding that the assertion is mandatory is confirmed. Any uncertainty from “string; as defined below” about the specimen label's requiredness is now resolved by its meaning cell: absence or null is not the same as an accepted empty string.

Unresolved: these rows do not prescribe the complete precedence of every combination of malformed fields, nor do they fix repeated-key decoding. I do not infer a new runtime rejection was implemented merely because the prose is now explicit. High confidence about the declared requiredness.

### R5. Timeout floors are planning values, not exact waits

Hunk 6 changes “clamps it to” to an explicit floor for the ordinary worker allowance and the proposed validator I/O allowance (612, 616). Worker omission still uses 120,000 ms and actor scheduling still uses its fixed allowance. Validator aggregate collection is bounded from 1 ms through its 30,000 ms maximum (615). Crucially, remaining aggregate allowance can reduce the effective validator I/O timeout below its 50 ms proposed floor (616).

This sharpens the earlier override answer. A supplied worker allowance above 50 ms is not reduced to exactly 50 by that floor. The validator's 50 ms is not a guaranteed minimum effective wait once aggregate allowance is considered. The earlier claim that actor `worker_timeout_ms` does not change actor execution allowance remains.

Unresolved: planned allowance is not measured elapsed duration. The nearby check-read support expressly distinguishes planning values from elapsed worker time (622), and applicability of the accepted actor timeout override remains undecided (634). High confidence about the floor/aggregate relationship; no elapsed-time verification is supplied.

### R6. Override coverage is incomplete attribution, not absence of all cases

Hunk 7 changes the gap account. Collection floors are now described as selected by production planning helpers and checked against the limits inventory. The signal bound 31 remains source-owned. Existing signed-app cases are said to exercise several overrides; a complete mapping to boundary assertions and applicable release results still has to be assembled, including excessive downstream argument refusal (634–639).

I must narrow the blanket wording in my earlier A9/B10 coverage conclusions. The revised document does not support saying every override lacks a boundary case. It positively states that some cases exist. What remains unavailable is a complete, attributable coverage/result account for the override set. The authorization and packaged-host admission conclusions remain unchanged (607, 629).

Unresolved: this passage does not identify which overrides, which signed runs, their release applicability or their exact assertions. Its support still credits source inspection and no execution (641), and the planning support still credits no execution (622). Removing the earlier “execution remains outstanding” sentence does not, by itself, credit a particular run. High confidence in the revised distinction; actual coverage cannot be reconstructed from the new paragraph alone.

### R7. Exec timing, retained output and reap allowance are now quantified

Hunks 9, 17, 26 and 27 add connected exec meanings. Per-child collection gets 10,000 ms after successful spawn, capped by the remaining per-worker 115,000 ms active-plan allowance. That plan clock starts before setup, charges setup/intervening work, excludes acknowledged release and accepted parked-activation waits, and uses continuous time including sleep (877). `deadline_kind` identifies the selected child or plan deadline (2738). Final reap has a separate 1,000 ms continuous allowance after collection, while earlier ownership/group-request failures retain priority (2780–2786). Each stdout/stderr stream retains at most 1,023 bytes, with an overflow marker using part of that allowance (delta hunk 17, current 2099–2100).

I now distinguish these clocks and stages more concretely. The plan allowance is not a fresh 115 seconds for each spawn, and setup time can consume it before an attempt. A 1,023-byte output field is bounded retained output, not a complete transcript or an allowance plus an additional marker. These details preserve my earlier separation of successful spawning, leader exit, stream EOF, termination request and owned reap (2730–2741, 2774–2797).

Unresolved: the document expressly allows blocking native calls to outlast the allowance (877); none of these numbers proves a hard process-wall-time bound or confirmed cleanup by a deadline. The marker's exact content/placement is not supplied by the added field text. Source support still credits no execution (889, 2799). High confidence in the assigned budgets and retention cap; actual duration and cleanup need observations.

### R8. Acquisition attempts count occupied and failed attempts

Hunk 12 clarifies that the client may begin a next acquisition only after fewer than 256 have already begun, and that the total maximum of 256 includes occupied replies and transport failures (1164–1166). The control's 65,536-byte bound is now represented by a named quantity without changing its value (1171).

The earlier bounded-acquisition understanding becomes more precise: this is at most 256 total acquisition attempts, not an initial attempt plus 256 retries, and not 256 successful control exchanges. The original overall allowance and per-attempt UUID still govern. This does not authorize replay of a specimen; execution invocation remains once after an admitted grant (1178–1180).

Unresolved: the edit alone does not demonstrate actual attempt counting under all connection failures. The transport evidence limitations remain (1144). High confidence about what is counted and the limit.

### R9. Named component references establish responsibility, not authentication

Across hunks 12–15, 18–19, 30, 35, 37, 41–43, several operation owners now refer explicitly to the defined Controller, Runner client or Runner host. The definitions identify request preparation/envelope interpretation, reservation/transport capture, and host orchestration/reply production respectively (289–309). Hunk 14 also gives the Python retained-byte reader its own description: it admits captured porcelain against the schema and projects fields for evidence readers; bytes remain with their capture owner (1397–1409).

This reinforces my earlier boundary assignments. The host authorizes a connection (1152); the client admits control replies (1171); the controller admits its client/output account; the host admits validator lines; both the controller and retained-byte reader are named for structural frame admission. Typed transport remains a public admission surface, not merely unpromised internal machinery. A named role reference is not the same thing as a producer contract string, signature, PID association or verified executable identity.

Unresolved: these links do not prove that either decoder implements the whole stated rule or that the Python reader runs during every controller invocation. Structural shape admission still leaves native/lifecycle/actor/equipment/custody semantics to their readers (1409), with primitive-reader evidence gaps remaining (1429). The index's display change from `build_contract.py` to “build contract.py” identifies a displayed component label; I do not derive a runnable filename or a changed build invocation from it. High confidence about responsibility; implementation correspondence remains unverified.

### R10. Fallback eligibility and actor policy selection are explicit

Hunks 16 and 36 specify the fallback trigger as accepted client transport admission, no request-delivery error, and terminal `xpc_error` in the admitted client capture (1630). Helper-envelope support remains independently bound to kind, current non-unbound contract and nonempty outcome (1632). Actor captures are now described as policies found in actor declarations' `sandbox.policy` objects before host admission of sandbox mode, not only policies of already admitted apply actors (1639, 3496).

This resolves the earlier vague phrase “fallback-eligible xpc_error” into conditions. It also removes an over-narrow reading of the old run-payload row: a retained per-actor compile result does not establish that its actor mode was valid or admitted. A malformed-mode declaration can still supply a policy object for this independent compiler path. My earlier separation of compiler verdict, host admission and execution remains.

Unresolved: the contract still gives this malformed-mode path source-read support and the selection controls check-read support, with no execution credited (1634). An independent helper success neither resolves uncertain post-invocation execution nor establishes sandbox application or probe effects. High confidence in the stated selection/eligibility conditions, not in an unobserved run.

### R11. Step-to-phase bindings narrow which ordering facts can be used

Hunk 18 renders `p` as an entry in `reply.phases`, `s` as an entry in `reply.steps`, and the association `reply.steps[s].phase_id = reply.phases[p].phase_id` (2208). The rule then combines that phase's collection/release/lifetime chain with that step's native validator answer and unique query association (2225–2232).

I can now follow the selectors without supplying the phase/step join myself. I cannot pair a step from one phase with a convenient ordering record from another. This confirms rather than changes my earlier understanding of `query_first`: a prediction before its phase's attempt batch, with independent per-probe eligibility, not a guarantee that state remains unchanged until each later attempt (2237–2242).

Unresolved: the binding equation is not itself proof of unique phase IDs, correct worker PID association or a unique matching validator record. The full conditions still have to hold. Its rendering does not show an implementation performed them; the support still credits no new execution or mutation-control run (2244). High confidence in the declared relationship; runtime correctness remains unsupported by this reading.

### R12. Worker readiness, grace and policy-transfer deadlines have distinct meanings

Hunks 21 and 22 specify a 1,000 ms monotonic readiness-hint wait after successful policy delivery and readiness-pipe setup, reducible by actor setup allowance. Expiry leaves the hint absent and execution continues (2357). Worker exit grace is separately 1,000 ms monotonic after the host exit request (2359). Policy transfer has a 5,000 ms absolute monotonic deadline established immediately after spawn; partial writes and interrupted calls preserve it, and actor delivery can be shortened by shared setup allowance (2405).

I now know the origins and consequences of these particular allowances. Readiness expiry is not automatically a worker failure or proof that policy application did not occur. A partial write does not earn a new full transfer period. Grace expiry is not a statement that final termination/reap is already complete. The earlier distinction between host write counts and worker receipt remains (2401, 2493–2494).

Unresolved: actual assigned budgets and wait records, not these production maxima alone, are needed for a specific run. Host waits report where the host moved on and may lack valid elapsed accounting (2365–2374); termination request acceptance and reaping remain separate (2379). High confidence in the newly specified limits and origins, without a hard total-runtime conclusion.

### R13. Worker diagnostics are bounded bytes before replacement decoding

Hunk 23 changes “UTF-8 buffer length” to retained diagnostic-byte length and states the 4,095-byte bound excluding the terminating NUL (2477–2484). The bound applies before invalid sequences are replaced during UTF-8 decoding.

This resolves a possible earlier overreading of `length` as the length of the displayed UTF-8 text. It describes the retained source buffer. I infer that a consumer should not equate it mechanically with the encoded byte length or character count of replacement-decoded text; replacement can change those quantities. Complete/truncated publication validation remains a prerequisite for extraction.

Unresolved: the added number alone cannot establish that every original diagnostic byte survived or that an incomplete/invalid publication has usable text. Status retains its separate meaning. High confidence in the input-byte bound; the inference concerns interpreting that stated decoding sequence, not an executed malformed-text case.

### R14. Validator collection caps apply before query association

Hunks 15, 24 and 25 connect line admission to the validator subprocess account and state its collection bounds. For N submitted queries, the phase collector allows `2 × max(1, N)` records and `16,384 × max(1, N)` stdout bytes, sized before batch writing. On byte overflow it counts bytes actually received, retains the bounded prefix through its last complete LF frame, closes collection and reports `byte_limit` (2651–2653). Accepted records stay within that allowance even when they are diagnostics or have unexpected/null IDs (2672). Exit grace is a separate 1,000 ms monotonic wait, with later termination/reap potentially continuing beyond it (2675).

This adds concrete limits to my earlier accepted-prefix/association understanding. Retention of every accepted record means every record that survived these receiving limits, not unlimited output. Record acceptance and a unique per-step query join remain different; duplicate/null IDs can remain at collection scope (2680–2686). The overflow rule is specific: the general line decoder can also decode a final nonempty fragment in its normal admitted prefix path (delta hunk 15/current 1453), so I do not generalize “must end in LF” to every received record.

Unresolved: the zero-query formula does not establish that a validator is always launched when N is zero. “All bytes received” does not include bytes the child might emit after collection has closed. These limits do not prove complete native query coverage or cleanup by one second. High confidence in the formulas and retention boundaries; actual collector behavior remains unexecuted here.

### R15. Gate bindings make joins visible without validating retained assertions

Hunks 29 and 30 render the gate's dependent phase `p`, source actor `s` and source final phase `f`, with source-ID and final-phase-ID association restrictions (2979, 3008). The source-final-phase field still means the source actor's last declared phase preceding the dependent phase (2963–2968). Thus, for the earlier A-to-D situation, `p` is D's dependent phase, `s` is A, and `f` is A's last declared phase. These are selections in the report, not observation ordinals.

My earlier sequence conclusion remains: A's final activation, A's owned reap and the gate waiting for A are comparable in A's sequence; D's activation ordinal is in another sequence and cross-process timing uses timestamps (3014, 3047–3052). Missing source activation time still violates a carried satisfied gate's requirements. The controller's failure consequence is still invalid top-level integrity, withheld disposition and unknown cause, retaining host fields, independent actor projections and the outer result (3008). The bindings do not make a retained `satisfied` value trustworthy by itself.

Unresolved: the visible join keys do not remove missing/nonfinal/same-actor/nonpreceding association findings, nor do they apply the ordinary semantic gate check to reporting-failure replies. Most importantly, documentary selectors do not add selectors to each emitted finding: the structured actor/phase finding-subject gap remains at 3020–3022. The cancellation evidence gap also remains (3036–3039). High confidence in the clarified joins and unchanged consequences; no generated-selector or runtime-check correctness is presumed.

### R16. Live inspection has a guarded setup deadline and an optional additional deadline

Hunk 33 materially qualifies the earlier short description of a matched observation's timing. Matched inspection needs valid start/final samples and nondecreasing time. The scheduler includes inspection in a shared 10,000 ms monotonic setup allowance and cancels when an otherwise successful inspection reaches or exceeds that deadline (3193, 3208). Orchestration separately attempts to establish a 180,000 ms monotonic deadline from an earlier initial sample. That additional deadline reuses the actor-lifetime duration but has a separate clock/origin from workers' continuous cutoff. When its initial sample is unavailable, this additional comparison is absent; valid inspection clocks and the scheduler setup guard still apply. When present, both inspection samples must be strictly before it.

I must qualify any earlier broad statement that `matched` always proves comparison with one established inspection deadline. The additional deadline is conditional. Conversely, failure to establish it does not mean all timing guards disappear. Equal numeric durations do not make the monotonic additional deadline the same measurement as the worker lifetime cutoff. Static `bound`, live `matched`, activation eligibility and later observations remain separate claims (3206–3214).

Unresolved: the unavailable-initial-clock-then-valid-inspection-clock branch is explicitly source-read with no credited control (3223); signed-product inspection-failure/cancellation evidence also remains open (3219–3222). A retained final observation timestamp alone cannot reconstruct every origin and sample used in these checks. High confidence about the revised conditional timing account; no live deadline behavior is established here.

### R17. Receipt capacity is per opted-in worker; the actor binding is not a nonce check

Hunks 34 and 35 add `a` as an actor-entry binding (3369) and quantify compiled capture as a positive raw byte count of at most 1,048,576 bytes for each opted-in worker (3382, 3417). The cap counts decoded bytes represented by base64, not base64 character count and not a single shared aggregate cap for all actors. Ordinary receipt placement and per-actor receipt placement remain separately defined (1943, 2822).

The binding helps identify actor scope, but its declaration alone supplies neither a new comparison nor an explicit `receipt = reply.actors[a].compiled_profile` equation. No `reply.actors[a]` occurrence appeared in the targeted search. The human-readable coverage comes from those placement fields and the rule saying every present receipt is checked, including actor, preparation-failure and reporting-failure records (3427–3429). I therefore do not presume the rendered binding proves an implementation visits every receipt correctly.

My earlier nonce answer remains: host publication compares the recorded nonce and other capture facts in order; failure yields the reduced unavailable receipt without changing host normalized outcome (3405–3420). The controller checks carried status/producer/stage labels; retained nonce, bytes, digests, lengths and counts remain host assertions after the separately stated admission/capacity gates (3380, 3429–3436). Rendering `a` does not give the carried-label check a request-nonce operand.

Unresolved: no new native capture, actor iteration or request-association execution is credited. The existing executed `future` producer example still establishes only its constructed admission/retention case (3441–3445). High confidence in the cap and stated division of checks; the mechanical relationship between the rendered alias and actual traversal is outside this reading.

### R18. Outer result selection is consolidated, not changed to fail on findings

Hunks 36 and 38 move the completion rule to the envelope's result-selection account and explicitly place it after reply-wide findings (3505). The diagnostics section now refers back to that rule instead of repeating a `finished`-specific operation. Its old row disappears from the rule-applicability index. The definition of “ordinary semantic reply” moves before the check-family table: no `reporting_failure`, covering both single-worker and actor forms (3621–3638).

My earlier conclusions about outcomes remain intact. After admission, exact `finished` selects success/exit 0 despite individual attempt failures or integrity findings. A reply-wide withheld disposition can coexist with that outer success (3505–3515, 3599–3616). Removing a repeated rule/index row does not remove the behavior, because its surviving owner explicitly states it. The ordinary semantic definition's relocation does not broaden ordinary association checking to degraded replies.

Unresolved: whether success/exit should reflect integrity findings remains a stated open question (3513–3515). Different reporting-failure reader scopes remain unreconciled (2843–2851). High confidence in unchanged result meaning and narrowed ownership of the rule; no runtime-order verification follows from the documentary `Follows` reference.

### R19. The controller-findings index now exposes consequences, not every operand

Hunk 43 changes the column from “Records inspected” to “Structured operands,” replaces empty cells with references to the full rules, adds structural admission, includes gate join-key operands, and shows consequences previously available in the rule text (4436–4443). In particular, gate findings retain the host account and independent actor projections, whereas a profile-label refusal changes the public outcome to malformed, withholds diagnostics, retains the report and exits 1. Delivery failure and other admission refusal preserve their distinct exit 2/exit 1 consequences.

I can now obtain those distinctions directly from the index. This confirms the earlier prompted distinction between semantic findings and admission refusal; the visible consequences do not create new execution evidence. “See the linked rule” means the row does not enumerate structured operands there, not that the operation inspects nothing. The gate row's operand list includes source/final-phase join keys, but it still does not enumerate every fact named in prose. For example, 3014 requires activation/reap timestamps, while 4440 does not list their `observed_ns` fields. That omission does not cancel the prose requirement.

Unresolved: the table is not enough to reconstruct every predicate, precedence decision, loop or semantic reader. The separate check-family table (3624–3632) describes additional relationships. I cannot infer that all checks or all inspected data are exhaustively represented by the six summary rows, or that generated operands correspond to implementation reads. The emitted finding-subject gap remains despite the index's joins. High confidence in the now-visible stated consequences; completeness/correctness as an executable checking specification is not established.

### R20. Numeric formatting and named-quantity markers preserve many values

Several hunks only add thousands separators or replace literal wording with named quantity spans: policy source/parameter capacities, helper source and output limits, sysctl buffer, override paths/defaults, extension target/payload/exchange limits, the import scanner's 4 MiB bound, and the external service's one-second throttle (hunks 5–12, 16, 39–40, with substantive portions discussed above). For example, 262143 becomes 262,143; 4194304 becomes 4,194,304; “one-second” becomes “1 second.” These displayed values are numerically the same.

I do not infer new capacities, request wire values or runtime throttling from those formatting changes. A named span connects the document to a quantity label, but this reading cannot prove that the production value, generated inventory and prose actually agree. The newly informative timing origins, formulas, floors and per-worker scopes are the substantive changes already separated in R5, R7–R8 and R12–R17.

Unresolved: no source or generator was read, so mechanical agreement remains unverified. No behavioral question is resolved solely by punctuation or markup. Confidence is high that these individual displayed numeric values are unchanged.

### R21. Added support citations do not supply new execution credit

Hunks 1, 7, 9, 16, 20, 28 and 34 add or refine source/check citations concerning equipment, clocks, exec buffers, fallback selection and lifecycle boundaries. The corresponding support paragraphs continue to identify source-read or check-read support and their limits. The override coverage wording changes what kinds of existing cases are said to exist, as addressed in R6; it still does not attach a complete release-result account.

My earlier answer that a citation or a passing unspecified default battery cannot credit every listed surface remains. The unchanged executed receipt-producer case still has its specific source snapshot/run and constructed-context limits (3443). This revision does not turn all newly exposed selectors, caps or consequences into executed assertions. The source/test paths were not opened.

Unresolved: the applicable test selection, execution results and native boundary observations remain to be established where the contract says so. Nothing in this delta answers who regenerates worker identity copies during direct source-test builds. Development-to-release review still lacks a baseline (152–156). Confidence is high about the support grades printed here, with no independent evidence verification.

## Hunk coverage

Each row identifies the portion of the delta considered, including edits that change only representation or repeated indexes. A hunk with several changes points to every relevant discussion.

| Hunk | Delta start line | Subject | Reading |
| --- | ---: | --- | --- |
| 1 | 3 | Worker identity and fixed digest widths | R1, R21 |
| 2 | 70 | Actor/phase surface title | R2 |
| 3 | 89 | Cause definition omits log text | R3 |
| 4 | 110 | Required contract/specimen strings | R4 |
| 5 | 131 | Policy capacity formatting | R20 |
| 6 | 150 | Override floors, aggregate cap, formatting | R5, R20 |
| 7 | 178 | Override quantities/coverage/support and policy formatting | R6, R20, R21 |
| 8 | 223 | Helper-source capacity formatting | R20 |
| 9 | 242 | Exec budgets and support; sysctl formatting | R7, R20, R21 |
| 10 | 290 | Extension target formatting | R20 |
| 11 | 309 | Extension payload/exchange formatting | R20 |
| 12 | 338 | Authorization owner, acquisition counts, control bound/owner | R8, R9, R20 |
| 13 | 380 | Client/host admission owner | R9 |
| 14 | 399 | Retained-byte reader definition and owners | R9 |
| 15 | 428 | Validator line owner and collection-account reference | R9, R14 |
| 16 | 451 | Fallback trigger/support and helper-output formatting | R10, R20, R21 |
| 17 | 483 | Exec stdout/stderr caps | R7 |
| 18 | 504 | Step/phase bindings and ordering owner | R9, R11 |
| 19 | 540 | Attempt-classification owner | R9 |
| 20 | 559 | Step support references | R21 |
| 21 | 578 | Readiness and worker exit grace | R12 |
| 22 | 600 | Policy-transfer deadline | R12 |
| 23 | 619 | Diagnostic byte length and decoding | R13 |
| 24 | 640 | Validator record and byte formulas | R14 |
| 25 | 659 | Bounded validator records and exit grace | R14 |
| 26 | 682 | Exec deadline-kind reference | R7 |
| 27 | 701 | Exec reap allowance | R7 |
| 28 | 720 | Lifecycle support and actor/phase title | R2, R21 |
| 29 | 743 | Evaluated-gate phase binding | R15 |
| 30 | 762 | Carried-gate owner and joins | R9, R15 |
| 31 | 781 | Inventory digest representations | R1 |
| 32 | 837 | Static binding hash representations | R1 |
| 33 | 862 | Live hash representation and inspection timing/gap | R1, R16 |
| 34 | 912 | Equipment support, receipt actor binding/cap | R17, R21 |
| 35 | 955 | Host capture cap and controller label-check owner | R9, R17 |
| 36 | 985 | Actor fallback meaning and result-selection ordering | R10, R18 |
| 37 | 1014 | Admission precedence owner | R9 |
| 38 | 1033 | Completion-rule consolidation and semantic-reply definition | R18 |
| 39 | 1088 | Import-source bound marker | R20 |
| 40 | 1107 | Installation throttle marker | R20 |
| 41 | 1126 | Cleanup ownership component reference | R9, R19 |
| 42 | 1145 | Build component display in applicability index | R9 |
| 43 | 1164 | Applicability owners, removed duplicate row, findings index | R9, R15, R18, R19 |

## What this revision does and does not settle for this reader

The revision lets me state more exact timing and capacity commitments, resolve particular document-level joins, and directly see responsible components and consequences. It changes the override evidence conclusion to incomplete attribution of some existing cases and qualifies the additional live-inspection deadline as conditional. Those are changes to my reading, not proof of implementation changes.

The earlier central limits persist: matching identities alone do not establish equipment/authentication; a retained host claim can coexist with a controller finding; current producer identity does not supply a controller nonce comparison; success is still selected from the admitted host outcome; and a compiler fallback is a separate observation, including for policy objects whose actor mode was not admitted. The rendered selectors do not fill the emitted finding-subject gap, establish end-to-end generated-check correctness or reconcile different readers' degraded-reply scopes.

The completed original journal and prompted answers remain unchanged. This file records the later reading and its stated limits only.
