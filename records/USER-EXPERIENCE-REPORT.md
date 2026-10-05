**PolicyWitness integration feedback from PAWL**

PAWL uses PolicyWitness (PW) as a runtime oracle for macOS Seatbelt policies, including comparisons between original and reconstructed policies. The request behind this review was to identify where PAWL spends substantial effort shaping its questions into PW requests or accommodating awkward interactions, and how it actually uses the supplied response data. We examined policy comparisons, path-membership and calibration experiments, runner preflight, completion handling, tests, and retained execution evidence. The first section describes the work PAWL does to obtain usable policy observations: constructing requests, managing execution and filesystem witnesses, and establishing completion. Its five findings have equal standing as feedback. The second examines how PAWL uses the evidence PW returns, distinguishing fields that affect automated decisions, fields exercised by tests, and evidence retained without automated interpretation.

1. **Query-focused use requires constructing an independent attempt.**

   Many PAWL comparisons need the `sandbox_check` prediction for an operation and filter. A PW step also requires an attempt, so PAWL must choose and construct a supported operation even when its result will not contribute to the comparison. For generated targetless queries, PAWL attaches a `file` attempt with the `access` action against a known existing file. That companion may have no relationship to the queried operation. Its success or failure is not evidence that the queried operation would succeed or fail.

   This creates work in both the generator and the reader. The generator must select an admissible companion, because an unsupported attempt rejects the whole request. The reader must preserve the distinction between the two channels and explicitly exclude attempt results from query-only equality. For path queries, the generator also maintains special handling for pseudo-terminal and audit-session devices: it uses a permission check instead of opening devices whose opens have blocked workers in these experiments.

   The integration cost is having to reason about an additional operation, including its supported spelling, effects, and completion, merely to obtain the policy prediction that motivated the request.

2. **Deciding whether another native operation may start requires substantial completion interpretation.**

   PAWL distinguishes three questions: what the policy query answered, whether the command delivered a usable reply, and whether the native work has finished. A failed operation can be fully finished; a locally timed-out command can leave native completion unknown. The timeout forwarded to PW and PAWL's longer subprocess allowance do not, by themselves, establish worker or validator termination.

   PAWL therefore reconciles local command cleanup, worker and validator termination records, collection status, ordering information, and PW's disposition diagnostics. Supplied details can contradict an apparent success. An unresolved result prevents later native work within the caller's batch, including work reached through another harness layer. That state has to survive exception handling and subprocess transport as well as ordinary returns.

   Runner verification adds a separate interpretation. Successful verification carries a native completion guarantee, but failed verification does not expose the detailed child evidence available from an ordinary run. PAWL consequently leaves failed verification unresolved rather than treating a returned process identifier or CLI exit as completion. Serial admission is PAWL's requirement; the consumer-side effort needed to establish it is the feedback.

3. **External-runner reuse involves a readiness transition after the reply.**

   PAWL's external-runner harness treats receipt of a reply and readiness for the next connection as separate events. After verification and execution, it polls launchd to observe retirement of the single-request host. The accommodation addresses a host that replies before exiting: another connection can otherwise reach the retiring instance and lose its reply. This readiness check is separate from the worker and validator completion checks described above.

   The harness polls at 50-millisecond intervals with a two-second retirement allowance. Verification has a 20-second allowance to accommodate launchd's default ten-second respawn throttle. These are configured allowances, not measurements of how long every invocation takes. Verification itself executes a specimen, so it participates in this lifecycle rather than functioning as a passive installation check.

   PAWL chooses to verify even an unchanged, reused installation, which puts this coordination on its ordinary reuse path. The resulting effort includes observing host retirement, budgeting for restart, and keeping readiness distinct from native completion. This finding concerns that interaction; PAWL's own signing policy and installation bookkeeping have additional costs that are not attributed to PW here.

4. **Path-policy questions require managing concrete filesystem witnesses.**

   PAWL's path-membership helper creates parent directories and files before submitting queries. Its path-calibration experiments construct controlled directory relationships, record device, inode, mode, and ownership, and check those identities again before removing the directories. A policy question therefore brings filesystem preparation, identity checking, and cleanup into the experiment.

   This also affects which questions PAWL can usefully ask. The probe generator removed synthetic nonexistent "nonmatch" targets because those probes produced `prediction_unavailable` instead of deny evidence. When the source supplies no usable path values, the generator falls back to an existing witness. Deny-side coverage must come from other usable witnesses, including paths extracted from the source's own deny predicates. An unavailable prediction cannot become a negative membership example simply because the chosen name was intended not to match.

   The observed costs are additional fixture management and constraints on coverage. They do not establish whether the underlying restriction belongs to PW, macOS path handling, or an interaction between them. The maintenance burden and the unavailable observations are established independently of that attribution.

5. **Admission rules require a local mirror, and capacity already excludes real comparisons.**

   PAWL maintains local admission checks for PW's request grammar and capacities. These include UTF-8 byte counts, supported attempt combinations, duplicate step identifiers, and distinctions such as rejecting an empty `args` array on a non-exec attempt. Validation occurs before external preparation and again against the serialized specimen submitted to PW. Keeping those checks aligned is an ongoing integration responsibility.

   The tests exercise the boundary against native PW behavior. A valid first step creates a filesystem effect; a malformed later step must cause whole-request refusal before that effect occurs. Accepted requests and harmless metadata changes provide positive controls. The matrix covers multibyte identifiers and source, parameter, step, and argument limits, so agreement cannot be inferred merely from both implementations rejecting obviously malformed requests.

   Capacity also has a concrete workload consequence. Retained corpus evidence identifies the WebProcess profile and five mutations whose reversed submissions exceed the source-text limit while their corresponding source submissions are admitted. One retained reversed submission contains 306,731 UTF-8 bytes against a maximum of 262,143. PAWL keeps explicit tests for this population and an expected failure for the unmet admission requirement.

   The cause remains unresolved. PAWL may emit unnecessarily large reconstructed text; PW's bound may constrain a legitimate workload; both may contribute. The retained WebProcess source and reversed submissions are already import-free, and their sizes alone do not distinguish those accounts. The feedback is the blocked comparison and the continuing admission-maintenance effort, with ownership of the capacity problem still open.

The following observations trace PW’s returned evidence into PAWL’s policy comparisons, completion decisions, tests, and retained receipts. Comparator observations and persisted executor receipts preserve the full PW envelope and native step records, while automated decisions consume selected fields. Each entry identifies what PAWL reads, what that reading establishes, and what supplied evidence has no dedicated consumer. Together, these observations describe how much of PW’s response PAWL turns into decisions or explanations, and where the calling path retains or discards the remaining evidence.

1. **Per-step comparison summaries are exercised in tests but do not drive PAWL's policy comparison.**

   PAWL compares observations from separate executions of the original and reconstructed policies. Generated comparisons use query predictions; plans that include attempt comparison also compare attempt outcomes and errno values. PAWL checks that the observations belong to the requested accesses and have the required native evidence before comparing them.

   PW's `steps[].comparison` describes the attempt observation, its basis, the submitted operation and target relationships, ordering, and limitations within one step. PAWL's protocol tests check the object's shape and selected observation, relation, and ordering values. Its production comparator reads the underlying query and attempt records without consulting this summary. The choice of whether attempts participate in equality comes from PAWL's experiment definition.

   The summaries remain in the retained response. PAWL has no automated diagnostic consumer that uses their operation relations, target relations, or limitations to explain a policy mismatch.

2. **Host path diagnostics are excluded from membership identity and verdicts.**

   PAWL's path-membership question is whether the submitted operation and path receive an allow or deny prediction. It assigns the answer to that exact submitted path. Host `path_diagnostics`, including resolved spellings, neither relabel the membership entry nor change its verdict. PAWL tests this directly: changing the query outcome changes the membership answer, while changing only the diagnostic spelling leaves it unchanged.

   PAWL retains these diagnostics in comparator observations and persisted executor receipts. The path-membership helper itself returns a Boolean cache without archiving the response. PAWL has no automated reader that uses retained diagnostics to investigate unavailable or surprising predictions. The enforced exclusion concerns membership decisions; there is no corresponding diagnostic workflow built around the retained spellings.

3. **Several dossier inventories are retained without interpretation, alongside dossier fields PAWL actively checks.**

   PAWL does not read the contents of `data.specimen.policy.imports`, the dossier's host information, `app_provenance`, or its service, worker, and validator binary comparisons when deciding policy equality or run availability. Those subtrees survive in the archived response. PAWL has no automated analysis of their unresolved import records, host values, or binary mismatch reports.

   Other dossier fields are part of the decision. PAWL checks augmentation status and the original and applied source hashes when establishing that a query belongs to its submitted, unaugmented policy. Its calibration experiments also compare selected runner identity fields: runner kind, bundle identity and location, executable location, service name, registry identity, and the worker's declared bundle identity.

   The import inventory and binary hashes describe what PW inspected before invocation. PAWL does not use that inventory to establish what the worker's compiler consumed, or those hashes to establish which bytes were launched. Its retained dossier therefore contains both actively checked identity evidence and inventories for which PAWL has built no field-specific consumer.

4. **PAWL consumes disposition summaries without independently interpreting the detailed worker account.**

   PAWL's completion decision reads worker and validator process identifiers, reap and exit information, collection status, and validator disposition. It also reads PW's `disposition_integrity` and `process_disposition`: an invalid or conflicting account can veto native completion, and an unconfirmed, withheld, or unrecognized disposition cannot authorize the next native operation.

   PAWL retains `worker_evidence`, the detailed `runner_subprocess.disposition` claims, readiness and progress details, and per-attempt lifecycle records without interpreting those structures itself. A protocol test checks that the disposition object is present. Production code does not traverse its supporting claims or construct its own explanation from them.

   PW derives the controller's disposition summaries from that detailed account, so PAWL already depends on some of its interpretation through the summary fields. PAWL has not built a separate reader for the underlying explanations or a diagnostic presentation based on them.

5. **Fallback compilation results have no automated consumer.**

   When PW supplies `data.policy_check`, PAWL retains it as part of the full envelope. No active reader uses its compilation status, diagnostics, or import inventory. PAWL decides run availability and policy comparison from execution and query evidence; fallback compilation does not supply a substitute prediction in those decisions.

   PAWL also has no failure-classification workflow that reads the fallback result to explain why the original execution failed. A failed run can therefore carry a compilation report that is preserved but does not affect the reported failure category.

6. **Exec child details are tested more extensively than production analysis consumes them.**

   PAWL's exec protocol tests distinguish a spawned child from a failed spawn and check the child's exit code against the attempt return status. They exercise successful and nonzero child exits. Production comparison does not separately read `attempt.child_pid`, `child_exit_code`, or `child_term_signal`.

   When attempt comparison is requested, PAWL consumes the generic attempt outcome and errno, and requires a worker-supplied result with an integer return status and no missing-result reason. It does not compare the additional child identifiers or final-status fields. Those fields remain in the retained step record, but PAWL has no dedicated production analysis of exec children built around them.

---

## Maintainer reading, 2026-10-05

This section was added after reading the report above from the PolicyWitness side. It attributes each reported cost to the decision that produced it, checks the report's checkable claims against the repository, and records impressions. It schedules nothing and proposes no changes; where a direction is obvious it is named as a candidate.

The report's deliberate refusal to abstract its complaints is what makes attribution possible. Every cost in the first section can be traced to a specific PolicyWitness rule, a specific macOS behavior, or a specific PAWL requirement, and the split is not the one the report's tone might suggest.

### Attribution of the first section

Three findings trace to PolicyWitness design choices, one to an undocumented PolicyWitness lifecycle behavior, and one to a PAWL requirement that exposes a thin PolicyWitness surface. Two further behaviors, discovered by PAWL through experiment, have no limit entry at all.

1. **The mandatory attempt (finding 1) is a PolicyWitness choice, and the headline.** `PWRunnerProbeStep` in [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) requires both `sandbox_check` and `attempt`; only the whole `probe_plan` may be empty. The query channel already has a planner-excluded state (`query_not_requested`), but there is no symmetric state for an attempt that was not requested. The comparison record already models an unrelated companion: `operation_relation` and `target_relation` report `different` for exactly the case the report describes. The tool understands that a companion attempt may be irrelevant; it only refuses to let the caller omit it. The release barrier does not depend on attempts being present, since a step without one contributes nothing to the batch the host releases. Candidate: an optional attempt, or an explicit attempt kind that attempts nothing and records that it did not.

2. **The absent-path exclusion (finding 4) belongs to PolicyWitness.** The report leaves ownership open between PolicyWitness, macOS path handling and their interaction. The exclusion is a host-side planning rule. `pathFilterIsUnresolvable` in [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) runs `realpath` in the unsandboxed host at query planning; a failure removes the validator query and synthesizes `prediction_unavailable` with `query_plan:path_unresolved_at_planning`. The [guide](../docs/PolicyWitness.md) calls the userland predicate "structurally suspect" for such paths and says nothing further; [LIMITS.md](../docs/LIMITS.md) has no row. The consequence is pinned and the premise is untested: no retained evidence in this repository shows that `sandbox_check` against an absent path yields a prediction that disagrees with enforcement. PAWL lost its entire synthetic nonmatch population to this rule and now takes deny-side coverage only from paths that exist. Candidate: test the premise live, then either document the rule as a limit with its reason or narrow it.

3. **Blocking opens are an undocumented limit (inside finding 1).** PAWL substitutes a permission check for device opens because opens "have blocked workers in these experiments." The file attempts in [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c) call `open` without `O_NONBLOCK`, and only exec attempts carry a per-step deadline (`PW_EXEC_CHILD_DEADLINE_MS_DEFAULT`). An open that blocks, as a slave pseudo-terminal or a FIFO can, holds the worker until the host's `worker_sentinel_wait` expires and the run reports `runner_timeout` with whatever slots completed before it. PAWL found this by losing runs. Candidate: a limits row now; a per-attempt deadline or `O_NONBLOCK` for non-regular files later.

4. **Reply-then-exit (finding 3) is real and undocumented.** `replyAndExit` in [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift) sends the reply and schedules `exit(0)` 50 ms later. A second request that reaches the live instance receives `already_ran`; a connection accepted during the exit receives an XPC error. The guide documents launchd's respawn throttle and the `already_ran` outcome but not this window, so PAWL built a launchd retirement poll that no PolicyWitness document told it to expect. Its 50 ms interval and two-second allowance are a consumer's guess at a number we know. Verifying an unchanged installation on every reuse is PAWL's choice and doubles its exposure to the throttle; that part is not attributed here. Candidate: document the window and the retirement condition beside the throttle note.

5. **The verify envelope (finding 2) is the cheap asymmetry.** Serial admission is PAWL's requirement, as the report says. The asymmetry it exposes is ours: `cmd_runner_verify` in [runner_commands.rs](../controller/src/runner_commands.rs) projects the runner reply to a PID and an outcome and discards the rest, so a failed verify carries none of the `runner_subprocess` evidence a failed run carries. PAWL's conclusion that a failed verify leaves native completion unresolved is the correct reading of what we give it. The fields PAWL reads to establish completion (process identifiers, reap and exit status, collection status, validator disposition, `process_disposition`, `disposition_integrity`) are the load-bearing set for that decision and should be treated as such across contract changes. Candidate: carry the runner reply, or at least its subprocess report, in the verify envelope.

6. **The source cap (finding 5) is arbitrary.** `PW_SHM_POLICY_BYTES` in [pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) is a shared-memory layout constant, 256 KiB including the terminating NUL. Nothing in the repository ties it to a `libsandbox` limit, and the source submission of the same WebProcess profile is admitted and runs. The retained reversed submission overshoots by about seventeen percent. Raising the cap is an ABI identity regeneration and a reply-maximum recompute, not a design question. Ownership of the expansion remains open as the report says; the roundness of the number is our half of it. The admission mirror is expected of a careful consumer and is not itself a complaint we can answer, but [limits.json](../docs/limits.json) and the request-contract examples corpus live only in the repository. The bundle's `Contents/Resources` holds augments and evidence, so a consumer cannot read the admission rules from the installed app it is mirroring. Candidate: ship the machine-readable limits and the examples corpus.

### Reading of the second section

PAWL consumes a thin slice of the envelope and re-derives everything else from raw records. The load-bearing set is: `sandbox_check.outcome`; `attempt.outcome`, `attempt.errno`, `result_source` and `missing_reason`; the disposition summaries and the process facts behind them; the source hashes with augmentation status; and the runner identity fields. The comparison records, both `path_diagnostics` blocks, the dossier inventories, `policy_check`, `worker_evidence` with the disposition claims, and the exec child fields are retained without a reader.

- The only PolicyWitness interpretation PAWL accepts is the disposition summary pair, and only as a veto. That is the shape "witness over interpretation" predicts, and it identifies `process_disposition` and `disposition_integrity` as the fields whose meaning must not drift.
- The comparison record is exercised in PAWL's tests and bypassed in production. The guide's reading rules direct consumers to the raw fields, and PAWL complied. For this consumer the record is a fixture and a teaching device, not a decision input. One consumer is not a verdict on the record, but it is the only external evidence we have of how it is used.
- The retained-without-a-reader entries are not a cut list. The dossier inventories are provenance; their value is forensic and arrives only when something is wrong. The telling detail is elsewhere: PAWL has no workflow for unavailable or surprising predictions, which is the case `path_diagnostics` exists for, and it did not reach for them when finding 4 produced exactly that case. The diagnostics are discoverable as fields, not as a procedure.
- Exec child fields and `policy_check` follow the same pattern, tested or retained and never consulted. No action follows from that alone.

### Net

Attributable costs on the PolicyWitness side, in order of leverage: the mandatory attempt, the verify envelope, the source cap. Two behaviors need limit entries whether or not they ever change: blocking opens, and the absent-path exclusion with its premise tested first. The reply-then-exit window needs documentation at minimum. The second section changes no priorities but names the fields whose semantics an external consumer actually depends on.
