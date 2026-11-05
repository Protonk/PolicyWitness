# LIMITS.md first-reader report

Read only the supplied onramp/example, candidate artifact and my own transcript. No execution, outside sources or citation verification. Checkpoint references below refer to `../interactions/limits.md`.

## Initial and settled understanding

The onramp (Task 1) supplied the action structure: ordinary query/attempt pairs count as single actions; lifecycle actions connect through token, delivery and handle references. It supplied no limits or runtime guarantees. At the need checkpoint (Task 2), I could calculate 256 actions, 64 UTF-8 bytes for 32 precomposed `é` characters and five minutes, but could not decide acceptance.

My first artifact impression (Task 3) was a reference separating numeric fit from semantic validity and usable evidence. That remained the settled account after the work and whole-document readings (Tasks 4–5): admission capacities, execution clocks and evidence-retention bounds have different scopes and consequences. The grounding and premises additionally distinguish checked constants, tested boundaries, exercised paths and broader guarantees.

## Work result

The proposed 8 actors, 16 global phases and 244 ordinary pairs plus 12 lifecycle actions fit their maxima, with the total exactly 256. Three of each lifecycle kind fit aggregate caps. Each policy's 1024 parameters fits, subject to key/value bounds. Its 262143-byte source fits only if the final source after augments stays within the cap. The 32-character precomposed `é` actor ID exceeds the 63-byte limit and is refused. These conclusions follow from **Specimen admission**, notably `actors`, `actor_phases`, `probe_steps`, `actor_issues/deliveries/handles/releases`, `policy_source`, `policy_parameters` and `actor_id`.

Receipts are separately available to opted-in apply actors, with the `compiled_profile` limit and nonce/application/completion/clean-exit/identity/checksum prerequisites. Availability is not guaranteed by capacity. `--timeout-ms 300000` changes the client allowance, not every internal budget or whole-run completion time; client timeout does not cancel host work or prove nonexecution. Null diagnostic paths and echoed parameter keys have independent bounds: path depth 8, component size 63 bytes, safe parameter-key echo up to 127 bytes. Null does not supply a replacement location or prove the key invalid.

Retention budgets do not bound all produced output, aggregate envelopes, runtime or process memory. Overflow remains explicit and truncated JSON cannot become a complete reply. Numerical fit alone does not establish valid references/order, prediction eligibility, application success or observed effects.

## Prompted qualifications

Task 6 question 1 clarified, without reversing my earlier conditional calculation, that validator retention uses the planned/submitted query list **before writes**, not successfully written query lines. If all 244 queries are submitted to collectors, allowances total 488 records and 3997696 retained stdout bytes. The 244 ordinary actions alone do not establish that all queries are eligible, submitted, written or usable. **Interactions that matter** states the distinction explicitly; `validator_records_per_query` and `validator_reply_bytes_per_query` repeat “sized before writes.”

Task 6 question 2 made the fallback condition explicit: an actor-shaped rejection alone does not establish fallback. Diagnostics may run before admission after an **eligible terminal XPC error**, for selected policies. Malformed input can exceed the admitted actor count, so eight times the per-helper cap is not an aggregate bound. **How to read the tables**, `helper_source`, `policy_helper_output` and its coverage row establish this. Diagnostics establish independent compile information, not application.

Task 6 question 3 confirmed that learning repeated actor-delivery consumption from `actor_handles` coverage did not correct a contrary belief. My earlier answer deferred ownership/order rules and did not prohibit reuse. The assigned count-only topology did not require resolving reuse semantics. Initial answers remain preserved in the transcript.

## Coherence and main thread

The reference is coherent for its primary job. Counting/consequence/control columns make values actionable, interactions prevent misleading arithmetic, and coverage notes qualify support candidly. I completed the assigned task without following links and did not encounter an unresolved numerical contradiction.

The actual burden was navigation and attention. The execution table mixes ordinary, declaration and actor scopes; the grounding table shifts from author decisions to clock mechanics, fixtures, process lifecycle and encoding. Scope reminders kept my conclusions straight. Most implementation and check detail is optional support for the numeric-fit task, though useful for deeper investigation. Combining rows with interaction prose was necessary, particularly for timing and receipts.

## Consequential plausible misunderstandings

These are hypothetical skim risks, not errors I experienced:

- Treating time budgets as additive completion guarantees. **Execution budgets — client_rpc_wait, actor_execution_allowance, actor_lifetime_cutoff** and the prominent first and third **Interactions that matter** bullets directly counter this, including noncancellation and blocked-call/cleanup qualifications.
- Treating receiver caps as memory or cumulative-envelope bounds. **How to read the tables**, `policy_helper_output` coverage and **Premises — Reply and output budgets** explicitly counter this. The deeper premises explain controller buffering before capture truncation.
- Applying declaration consumption restrictions to actors. **extension_consumes** explicitly labels its scope and separates actor counts; **How to read the tables** distinguishes forms. `actor_handles` coverage supplies the repeated-consumption detail. Contrary scope passages are visible early; full reuse semantics appear later. I did not make this inference.

No additional defect is needed to satisfy a concern quota.

## Outside knowledge

Full specimen authoring still needs request grammar, ownership/action-order rules, prediction eligibility, receipt opt-in field placement and interpretation of application/effect evidence. The artifact identifies those dependencies explicitly. They do not leave the narrower limits task centrally incomplete. Detailed host/worker/validator tutorials and native implementation mechanisms are optional follow-on background for this task.
