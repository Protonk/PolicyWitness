# Limits reader transcript

## Task 1 received — bounded onramp

Read only `packets/limits-onramp.md` and `packets/actor-example.json`. Prepare a short inventory of actors and declared setup modes, the schedule in order, ordinary query/attempt and extension action counts, and references connecting actions. Separate directly readable declarations from unknown behavior; do not infer success. Do not evaluate a target document, execute anything, or inspect other materials. Record the task and answer here and stop at this checkpoint.

## Task 1 answer — initial understanding

The request declares schema version 5 and specimen ID `extension_redelegation`. It declares three actors: A uses sandbox mode `unapplied`; B and C use mode `apply` with SBPL policies. Both policy strings include default allow, file-read-data and file-write denials, and a read allowance using the `com.apple.app-sandbox.read` extension. B also declares a file-issue-extension denial and a conditional allowance for issuance using that extension class and extension.

The declared schedule, in array order, is:

1. `b_before` (B): `b_read_before` pairs a file-read-data path query with a `read_fresh` file attempt.
2. `c_before` (C): `c_read_before` declares the same query/attempt pair.
3. `initial_supply` (A): `a_issue` declares issuance of file/read authority for the target as token `ta`; `a_to_b` transfers `ta` to B as delivery `db`.
4. `b_consume` (B): `b_consume_first` consumes `db`, naming handle `hb`.
5. `b_redelegate` (B): `b_read_after` declares the query/attempt pair; `b_issue` declares another file/read issuance as `tb`; `b_to_c` transfers `tb` to C as `dc`.
6. `c_consume` (C): `c_consume_second` consumes `dc`, naming handle `hc`.
7. `c_effect` (C): `c_read_after` declares the query/attempt pair; `c_release` releases `hc`.
8. `b_cleanup` (B): `b_release` releases `hb`.

There are 12 actions total: 4 ordinary actions, each containing one query and one attempt (4 queries and 4 attempts), and 8 extension actions: 2 issue, 2 transfer, 2 consume and 2 release. All ordinary query paths, attempt targets and issuance targets use `/private/tmp/pw-lookback-example/target`.

The action-reference chains are `a_issue` → token `ta` → `a_to_b` → delivery `db` → `b_consume_first` → handle `hb` → `b_release`, and `b_issue` → token `tb` → `b_to_c` → delivery `dc` → `c_consume_second` → handle `hc` → `c_release`. Phase actor IDs and transfer recipients refer to the declared actors. The second chain occurs after B's consumption in the declared schedule, but no explicit reference in `b_issue` points to `hb` or `ta`.

Directly readable facts are these declarations, names, counts, shared paths, policy text and array order. The request alone does not establish the actual process arrangement or setup meaning of `unapplied`, scheduling/barrier guarantees, the order and meaning of a query relative to its attempt, exact `read_fresh` behavior, extension/token/delivery/handle mechanics and lifetimes, policy interpretation, error handling, or result-envelope evidence. It supplies no observed success, target existence, effective authority, read outcome, successful redelegation or release effect. Those need explanatory documentation or observed results, depending on the question.

No prompted or corrected understanding yet. Stopping after the onramp checkpoint.

## Task 2 received — need checkpoint, target withheld

Advise a specimen author about an actor-form request with 8 actors, 16 global phases, 244 ordinary query/attempt pairs, 12 extension lifecycle actions (3 each issue/transfer/consume/release), 262143 UTF-8 bytes of SBPL source per policy and 1024 parameters. Proposed actor ID: 32 copies of `é`. They want compiled-object receipts from every apply actor and interpret `--timeout-ms 300000` as enough for the whole run. Eventually address numeric allowance/refusal, additional conditions, changed evidence availability, null `request_failure.path` with an echoed parameter key, and output-budget scope. At this checkpoint, provide only tentative calculation/approach and missing information; consult no additional sources and stop.

## Task 2 answer — prompted need checkpoint

Tentative arithmetic: 244 ordinary actions plus 12 extension actions equals 256 total actions. The ordinary portion contains 244 queries and 244 attempts, not 488 actions under the example's action structure. Three actions of each of the four extension kinds sum to 12. If `é` is the precomposed character U+00E9 as written, the proposed ID has 32 Unicode code points and 64 UTF-8 bytes. The source size is one byte below 262144. If each of all 8 actors had one policy of that size, those sources alone would total 2097144 UTF-8 bytes before JSON encoding and other request fields. 300000 milliseconds equals 300 seconds (5 minutes).

These calculations do not yet establish acceptance: the supplied onramp contains no numeric limits or their units, inclusivity, scope or aggregation rules. I would first map each count to the documented budget (per actor, phase, policy or whole specimen), establish whether extension actions share the ordinary-action budget, and check identifier grammar as well as length. Then I would check structural and lifecycle requirements: valid phase/actor references, reference availability and ownership, ordering, policy/parameter validity and any aggregate request limits. The example suggests these as things to investigate, but does not establish their actual rules.

Missing information: limits for actors, global phases, actions, policy source and parameter count; identifier character restrictions and whether length means bytes or characters; JSON/source encoding treatment and parameter constraints; supported receipt modes and their availability in actor form; what evidence changed, under which configurations, and what a missing receipt means; timeout scope, starts/resets and relationship to cleanup or total wall time; output-budget categories, truncation/overflow behavior and exclusions; and the contract for `request_failure.path` and echoed parameter keys. Until supplied, I cannot say that the request fits, that every apply actor can provide a compiled-object receipt, that five minutes covers the whole run, or that a null failure path makes the echoed key invalid or identifies its location. No numeric threshold or runtime result has been inferred from the near-boundary numbers in the question.

No correction to initial understanding at this checkpoint. Target remains unread; stopping here.

## Task 3 received — first impression only

Candidate: `artifacts/LIMITS.md`, a flat reading copy retaining visible content and links with non-visible generation comments removed. Allowed materials remain this artifact, the supplied onramp/example and this reader's own history/transcript. Skim title, opening, headings and prominent summaries with limited attention. Do not follow links or perform the full work task. Respond in at most 150 words about purpose, central account and expected use, then stop.

Material exposure: read the first 35 lines and all headings, extracted from the candidate artifact. No linked materials or table bodies read.

## Task 3 answer — initial artifact impression

This document is an inventory for checking specimen capacities and interpreting limits on execution and retained evidence. Its central account is that a compilable policy and a numerically fitting request do not guarantee admission, meaningful operations or usable evidence. Limits have different scopes, and numeric admission failures differ from meaning failures and input-reading errors.

I expect the tables to let me calculate whether the proposed actor request fits, identify which fields explain a refusal, and distinguish per-policy limits from specimen-wide totals. Later sections should explain timing and transport budgets, evidence capture and diagnostic bounds, including why information may be absent. The interaction sections appear intended to connect those individual limits to consequential combinations. I expect to leave knowing which numeric checks I can perform directly and which semantic or evidence conditions still need separate establishment.

Stopping at the first-impression checkpoint; full work task not yet performed.

## Task 4 received — initial work result

Use the complete candidate LIMITS.md to answer the consequential specimen-author task. Read naturally with limited attention; do not reconstruct missing premises elsewhere or audit citations. Distinguish numerical fit, conditions needing other establishment and unresolved interpretation. Cite supporting headings/rows. Preserve this initial result, append it here and stop without a whole-document review.

Material exposure: requested the full artifact; tool output truncated the long grounding table. Read the operational tables and interaction prose, with targeted reads of lines 125–290 to recover execution, transport and evidence content. Did not follow citations or inspect other materials.

## Task 4 answer — initial work result

The proposed dimensions mostly fit, but the proposed actor ID is refused. In **Specimen admission**, `actors` permits 8 actors and `actor_phases` permits 16 phases globally, including empty visits. `probe_steps` permits 256 ordinary pairs plus lifecycle actions in total: 244 + 12 = 256 exactly. There is no extra allowance per actor or phase. The three issues, transfers, consumes and releases fit their respective aggregate maxima of 32, 64, 64 and 64.

`policy_source` permits 262143 decoded UTF-8 bytes per policy, inclusive, but counts the final source after augments. Thus a submitted source already at that limit only fits if the final augmented source remains within it; imported contents are excluded. `policy_parameters` allows 1024 entries separately per policy. Individual parameter keys and values still have limits of 127 and 383 UTF-8 bytes. Under `actor_id`, 32 precomposed `é` characters occupy 64 UTF-8 bytes and exceed the 63-byte cap, producing `admission_refused`. Length counts decoded bytes, not characters or JSON escape spelling. Use an otherwise valid identifier within 63 bytes; identifiers must also be nonempty, NUL-free and nonduplicate.

Numerical fit is not semantic acceptance or runtime success. **How to read the tables** and **Interactions that matter** require the actor form to remain separate from declarations; every phase must name an actor. Extension ownership, references and action order must be valid; releases are at most once per handle. Issue targets must be absolute and within their own 1023-byte limit. Other IDs, ordinary targets and query fields must fit their rows, and relevant strings must exclude NUL. Authority participation, including receiving a transfer, excludes exec in that actor; a separate actor may exec. Policy validity, receipt prerequisites and prediction eligibility still need establishment. This artifact points to other semantic documentation, which I have not consulted, so I cannot certify a complete specimen from the given dimensions.

Compiled-object receipts can be requested separately for each opted-in apply actor. **Evidence capture — compiled_profile** caps each at 1048576 raw bytecode bytes before base64. **Interactions that matter** additionally requires a 32-character lowercase hexadecimal nonce, successful application, completion, clean exit and matching identity/checksum. Oversized or unsupported objects make capture unavailable without preventing application; unapplied actors have no receipt. Therefore asking for every receipt does not guarantee receiving every receipt, and an unavailable receipt alone does not establish failed application.

`--timeout-ms 300000` is allowed but means a five-minute client allowance, not a guarantee that the whole run completes within five minutes. **Execution budgets — client_rpc_wait** includes helper launch/input delivery, reservation acquisition and reply waiting. The actor setup (10000 ms), serial schedule (120000 ms excluding synchronous collection), aggregate collection (30000 ms), release/exchange waits and shared lifetime cutoff (180000 ms) retain their separate meanings. **Interactions that matter** explicitly says none is end-to-end runtime. Blocked native calls and cleanup can overrun relevant budgets. Client expiry yields `xpc_timeout`, does not establish nonexecution and does not cancel host work.

Changed evidence availability must be interpreted at the relevant layer. Collection exhaustion can leave later predictions unavailable while attempts still run; earlier collections survive. A fitting query or complete record can still provide no usable prediction. Capture limits do not change attempt status or sandbox_check verdicts. A 64-byte `read_fresh` prefix is not a complete file dump. Missing or truncated evidence cannot establish what the omitted content would have shown.

For a null `request_failure.path` with an echoed parameter key, **Evidence capture — request_failure_path_components/request_failure_path_component** and **Premises behind the interactions — Admission order and echo** explain separate bounds. A path is retained whole only with at most 8 components of at most 63 UTF-8 bytes each; otherwise the whole path becomes null. A safe key can independently appear in `admission_failure.parameter_key` up to 127 bytes. The combination is therefore consistent, for example with a 64–127-byte key component, but does not by itself prove that exact cause: depth could also exceed its bound. Null does not mean there was no offending location or that the key is invalid. Read the structured failure category/field and counts rather than inventing a shortened path.

**Queries and transport** bounds retention at different receivers: controller stdout/stderr capture is 260046848 bytes per stream; host reply retention is 88080384 bytes before base64; helper stdout/stderr retention is 8388608 bytes per stream per invocation. Overflow is marked, not silently treated as complete JSON. Truncated client capture is not parsed, so submission remains unknown and no host evidence is inferred; truncated host bytes cannot become a complete result. The 85852557-byte `runner_reply_maximum` is informative, not a refusal threshold. Validator record and byte budgets scale with submitted queries, not phase capacity times action capacity: for 244 submitted queries the allowances total at most 488 records and 3997696 retained stdout bytes. Lifecycle actions add no queries. Earlier complete records can survive frame rejection; incomplete cutoff fragments are not decoded. Output budgets bound retained evidence, not total runtime, all output produced or process memory. Controller collection buffers the stream before applying its capture cap; per-helper caps also do not bound the cumulative fallback envelope. Authority-region logical storage is separately derived from admitted issues and deliveries, with allocator/page/private-custody overhead outside its formula.

Unresolved: the supplied counts do not specify actual policy validity, reference topology, query eligibility, successful application or receipt availability. Those need the full request, applicable semantics or observations; no execution success has been inferred here. This is the preserved initial work result, not a whole-document review.

## Task 5 received — whole-document checkpoint

Give the complete artifact an ordinary read, including tables, interactions, grounding/coverage and premises, without outside links or citation auditing. Explain its account, changes in understanding, coherence for its primary job, where its thread is lost, consequential misunderstandings or missing knowledge. Distinguish experienced confusion from hypothetical risks, and optional detail from missing central explanation. Append and stop before targeted questioning.

Material exposure: read the remaining grounding/coverage rows, recovering the middle of that long table with a narrower read after tool-output truncation. Together with the earlier operational content and full premises, this completes the ordinary artifact reading. No outside source consulted or citation audited.

## Task 5 answer — whole-document understanding before targeted questions

The document describes several different boundaries a specimen and its evidence cross. First, decoded requests must fit fixed capacities, with refusal rather than silent plan shortening. Then execution progresses under several clocks whose expiry effects differ. Finally, receivers and optional capture mechanisms retain only bounded evidence, explicitly signaling loss or unavailability. None of those numerical checks substitutes for meaning validation, application success, prediction eligibility or observation of an effect. The later material explains how the bounds are derived and how far the supporting checks actually establish their behavior.

My first impression holds. The full reading adds a stronger distinction between a documented constant, a tested boundary, an exercised path and a general guarantee. For example, finite actor timing workloads do not establish that every admitted workload completes; sampled lifetime enforcement is not an asynchronous timer; a constructed exact-size bytecode capture does not establish compilation/application of a policy of that size. The reply maximum is a conservative construction with mutually exclusive fields and review obligations, not a demonstrated reachable reply or a universal resource cap. These qualifications sharpen the work result without changing its numerical or timeout conclusions.

I also learned some concrete semantics in the coverage material: actor consumption may repeat for one delivery with distinct handles; a release after failed consumption still runs and records unavailability; capture currently supports nonempty single-profile type-0 objects. These refine my earlier list of things requiring establishment. I did not previously claim the opposite, and my initial work result remains preserved.

For its primary job as a limits reference, the document is coherent. The counting/consequence/control columns make the values actionable, the interaction section prevents the most consequential incorrect arithmetic, and the coverage account openly limits evidential claims. I could answer the supplied author task without following links, while identifying what this reference cannot certify.

The main thread becomes harder to hold in the long execution table and especially the grounding table: the author moves from deciding whether a specimen fits to reading low-level clock, process-lifecycle, fixture and encoding details. Mixed ordinary/declaration/actor rows require repeated attention to scope. This was an actual navigation/attention burden, not an actual belief that an actor received the ordinary worker budget. The repeated scope statements kept my conclusions straight. The grounding section is valuable reference support, but most of its implementation names and control descriptions are optional for an author doing the stated numeric-fit task.

I did not experience an unresolved numerical contradiction or reverse an admission decision after the whole read. The null-path/echo explanation and receipt prerequisites were sufficiently explicit. I did need to combine a table row with interaction prose rather than treating a row's number as a complete answer. That seems appropriate to a reference of this scope, although it makes a table-only skim less safe.

Hypothetical risks, rather than errors I actually made: a reader could treat all time allowances as additive guarantees, all capacities as memory caps, or the existence of a permanent-check link as proof of every consequence. The document directly counters each. Another reader might assume repeated consumption is globally prohibited from the declaration row; the actor scopes and later actor coverage correct that. The latter detail is more distant than the numeric capacities, but full extension lifecycle rules are explicitly outside this inventory's primary job.

Essential outside knowledge for constructing a complete valid specimen remains the actual request grammar, extension ownership/order rules, prediction-eligibility rules, receipt opt-in field placement and interpretation of application/effect evidence. The document names and links these dependencies instead of pretending numeric fit establishes them. They are necessary for broader authoring and interpretation, but I do not see a missing central explanation for the narrower limits task. A tutorial on host/worker/validator operation or every native API would be optional background here, not required to repair the account. No whole-document defect needs to be invented merely because that background is elsewhere.

Stopped before targeted questioning.

## Task 6 received — targeted questions

1. Distinguish planned/submitted validator queries from successfully written lines and locate support.
2. Explain fallback diagnostics and aggregate output bounds for an actor-shaped request with more policies than the admitted actor count, rejected before host admission.
3. Explain whether finding repeated-consumption semantics in coverage corrected a contrary inference, filled a consequential task gap or supplied deferred optional grammar; separate actual confusion from hypothetical risk.

Answer only from the artifact; append and stop before final report.

## Task 6 answer — prompted clarification

1. The collector sizes retention allowances from the query list submitted to that phase collector before it writes query bytes. A failed or incomplete delivery can therefore mean fewer successfully written lines than the list used to allocate the allowance; the allowance is not recalculated as twice only the successfully delivered lines. **Interactions that matter**, the validator-storage bullet, explicitly says this and distinguishes expected from written bytes. **Queries and transport**, `validator_records_per_query` and `validator_reply_bytes_per_query`, both say “sized before writes.” My calculation of 488 records and 3997696 bytes was conditional on 244 queries being submitted to collectors. The mere presence of 244 ordinary actions does not establish that all 244 become submitted eligible queries, all are written, or all return usable predictions. This is clarification of the work result's condition, not a correction from a successful-write basis.

2. **How to read the tables**, the diagnostic-helpers bullet, states that fallback sbpl-check diagnostics follow an eligible terminal XPC error and can run before host admission. Actor fallback associates each selected policy with its actor label when present; malformed requests can supply more policies than the admitted actor limit. Thus 8 actors is not a cap on fallback helper count. The shape/rejection described alone does not establish that fallback will run: the eligible terminal-XPC-error condition and policy selection still matter. **Diagnostic helpers — helper_source** limits each helper input to 4194304 bytes, not all fallback inputs together; excess supplies policy_too_large with null compile/import groups. **Queries and transport — policy_helper_output** limits retained stdout and stderr separately to 8388608 bytes per invocation, marking overflow and suppressing complete-JSON interpretation. **Grounding and coverage — policy_helper_output** and the introductory diagnostic-helpers bullet expressly deny an envelope-wide or process-memory bound and note pre-admission accumulation. Therefore there is no fixed aggregate fallback-output cap established by multiplying the per-helper cap by the admitted actor count. The artifact describes independent compile diagnostics, not evidence of application.

3. It supplied deferred grammar detail; it did not correct an actual contrary conclusion or fill a consequential gap in my assigned numeric-fit answer. **Specimen admission — extension_consumes** expressly belongs to the declaration form, permits one consume, and says actor counts are separate. **Specimen admission — actor_handles** permits 64 actor consume actions, each assigning a handle reference, but does not itself spell out reuse of a delivery. **How to read the tables** separates the public forms, and the opening plus semantic-links paragraph defer ownership/action-order rules to the guide. **Grounding and coverage — actor_handles** adds that repeated consumption of one delivery assigns distinct handles and native handles are not identified by equality. My work result only required valid ownership/references/order; I did not prohibit repeated consumption. For the specified three consumes, the task supplied no delivery topology to validate. The hypothetical risk was a skimmer carrying the declaration restriction into actor form, despite those scope statements; I did not experience that confusion. Exact delivery-reuse grammar is essential when authoring such a topology but optional detail for the numeric-capacity question as posed.

Stopped before the final report. Earlier initial answers remain unchanged.

## Task 7 received — final first-reader report

Write a short report to `reports/limits-first.md`, now permitted, covering initial/settled understanding, work result, onramp and prompted changes, coherence, consequential actual/hypothetical misunderstandings and outside knowledge. Preserve submitted-versus-written and conditional-fallback qualifications. No outside verification or rewriting.

## Task 7 answer — final handoff

Wrote `reports/limits-first.md`. The report preserves the initial work conclusions, distinguishes actual navigation burden from hypothetical misunderstanding, and records Task 6's explicit query-submission and fallback qualifications. No source verification or reviewed-document changes were made. Reader work is complete; stopping.
