**PolicyWitness integration feedback from PAWL**

PAWL uses PolicyWitness (PW) as a runtime oracle for macOS Seatbelt policies, including comparisons between original and reconstructed policies. The request behind this review was to identify where PAWL spends substantial effort shaping its questions into PW requests or accommodating awkward interactions, and how it actually uses the supplied response data. We examined policy comparisons, path-membership and calibration experiments, runner preflight, completion handling, tests, and retained execution evidence. The five user-experience findings below have equal standing as feedback. They are followed by observations about PAWL's consumption of PW responses.

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

   The cause remains unresolved. PAWL may emit unnecessarily large reconstructed text; PW's bound may constrain a legitimate workload; both may contribute. Both submission paths expand imports, so their input sizes alone do not distinguish those accounts. The feedback is the blocked comparison and the continuing admission-maintenance effort, with ownership of the capacity problem still open.

PAWL's policy-comparison reports preserve the full PW envelope and native step records. Its automated decisions consume selected fields from that retained evidence.

1. **Per-step comparison summaries are exercised in tests but do not drive PAWL's policy comparison.**

   PAWL compares observations from separate executions of the original and reconstructed policies. Generated comparisons use query predictions; plans that include attempt comparison also compare attempt outcomes and errno values. PAWL checks that the observations belong to the requested accesses and have the required native evidence before comparing them.

   PW's `steps[].comparison` describes the attempt observation, its basis, the submitted operation and target relationships, ordering, and limitations within one step. PAWL's protocol tests check the object's shape and selected observation, relation, and ordering values. Its production comparator reads the underlying query and attempt records without consulting this summary. The choice of whether attempts participate in equality comes from PAWL's experiment definition.

   The summaries remain in the retained response. PAWL has no automated diagnostic consumer that uses their operation relations, target relations, or limitations to explain a policy mismatch.

2. **Host path diagnostics are excluded from membership identity and verdicts.**

   PAWL's path-membership question is whether the submitted operation and path receive an allow or deny prediction. It assigns the answer to that exact submitted path. Host `path_diagnostics`, including resolved spellings, neither relabel the membership entry nor change its verdict. PAWL tests this directly: changing the query outcome changes the membership answer, while changing only the diagnostic spelling leaves it unchanged.

   PAWL retains these diagnostics with the full response, but has no automated reader that uses them to investigate unavailable or surprising predictions. The enforced exclusion concerns membership decisions; there is no corresponding diagnostic workflow built around the retained spellings.

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
