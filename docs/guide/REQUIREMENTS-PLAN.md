# User guide staging ground (for now)

Each section here represents a potentially overlapping view into PolicyWitness accumulated with different means, attention, and process. 

## What qualifies as a user responsibility

A responsibility earns its place here by changing a test decision. **If the user follows this instruction, which outcome can vary while PW still owes them the same evidence?** 

### Partial procedure

Find a case in the suite map, then read its assertions for these patterns. [Suite coverage map](../../tests/README.md#suite-coverage)

- **Ambiguous input.** Two spellings, orders or declarations compete. Does the test require a particular winner that the author could specify directly?
- **Operator-controlled setup.** A test fixes a file, service or helper outcome. Could the operator establish the relevant condition before the run? Which assertion still checks PW's observation of it?
- **Interpretation.** A test records two observations and then requires a conclusion. Which conclusion belongs to the reader, and which raw facts and associations must PW still report correctly?
- **Repeated coverage.** Several cases rehearse the same user choice. Which surviving case observes the same effect at the same boundary?

Retire an assertion whose expected value the selected responsibility makes unnecessary. Keep a useful observation as informational when it has no expected product value. Subsume an assertion when another check establishes it independently. In a mixed case, apply the decision to the individual assertion. [Test outcome meanings](../../tests/README.md#declared-observations-and-judgments)

### Numbered findings with proposed changes

1. **Proposed — Use each field name at most once in each JSON object in your specimen.**

   The specimen author can check the original JSON before submission with a reader that detects repeated names. In the local development run `final-default` (`20261120T083452Z_fa6bb141`), byte-identical inputs named file A and then file B as `attempt.target`. The CLI created B. Direct XPC submission created A. Both reported `finished`. The test inspected both paths after each run. A successful result therefore gives the author no assurance that the intended file was chosen. [Current request statement](../REQUEST.md#contract-request-specimen-duplicate_keys)

   **Proposed test change.** In `runner_outcome_bad_request/accepted_input_contract`, `duplicate_entries` exercises six fields in both orders at both entries, alongside 24 single-occurrence controls. Move the choice of a single value to the author in the request surface and retire the first-value and last-value assertions. The direct host's refusal of a controller-only runner selector already has a single-occurrence control, `direct_selector`. [Authored request surface](../contract/10-request.surface.md) · [Test implementation](../../tests/suites/runner_outcome_bad_request/contract.py)

   **Check what survives.** Before folding away the paired controls, account for each independent obligation they exercise. Run the surviving admission case and inspect its accepted and refused inputs. A valid create must affect the declared target, a foreign contract must be refused at the receiving boundary, and a refused specimen must produce no file effect. Duplicate step IDs across different actions still have their own meaning and refusal check. [Admission suite](../../tests/suites/runner_outcome_bad_request/README.md) · [Request corpus](../../tests/fixtures/request_contract/examples.json)

2. **Proposed — Select an external runner by either its registry ID or its service name, and put all runner settings in one selector form.**

   An author can copy one identifier from `runner list` and put the required entitlements alongside it. Nested `runner` fields and the legacy top-level fields each work alone. Mixing them can change the experiment. In one test the ID names runner A and the service names runner B, and A is selected. In another, an empty nested entitlement list clears a nonempty top-level list. [Selector contract](../REQUEST.md#contract-request-options-precedence) · [Selector and registry tests](../../controller/src/runner_select.rs)

   **Proposed test change.** Retire the nested-over-legacy winner, the entitlement-list replacement assertion, and the ID-wins and ID-miss-with-matching-service expectations. A single pre-invocation conflict check could cover ambiguous selection. Exercise ID alone and service alone, including the legacy spelling for each. For every admitted request, verify the chosen worker's entitlement read-back against the requirements the author supplied. Keep the missing-key and false-valued-key refusals. [Selection implementation and entitlement controls](../../controller/src/runner_select.rs)

3. **Proposed — After a request is refused for an input defect, correct the reported defect and resubmit, repeating as needed.**

   A caller with two oversized query fields can repair either one first. `QueryAdmissionTests` nevertheless requires the operation to win over the filter value within one step, the earlier step to win over the later step, and the first field in a table to win for each pair of oversized request metadata fields. These are choices among defects already visible to the same admission check. The instruction applies to a confirmed input refusal. An XPC error with uncertain submission gives the caller different grounds for deciding whether to retry. [Branch-local refusal contract](../RESPONSE.md#contract-refusals-request-compound_order) · [Compound-fault assertions](../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)

   **Proposed test change.** Accept either complete, correct diagnostic for the submitted pair. Check its field and step association, actual size, unit and limit together. Repair just that defect and require the other one to be reported. Keep the single-defect boundary tests, bounded output, safe echoes, absence of worker or validator work, and the independent check for no file effect on refusal. Contract-first admission and the order of controller and host checks still protect distinct boundaries. [Admission contract](../REQUEST.md#contract-request-specimen-admission) · [Refusal and repair controls](../../tests/suites/runner_outcome_bad_request/contract.py)

4. **Proposed — When deliberately probing an absent pathname, use the filesystem attempt to determine what happened to that name.**

   In `witness_contract/phases`, one phase unlinks a seeded file. The next requests a path query and attempts `access` on the same name. The test checks the file's absence independently and requires `ENOENT` from that specific attempt. It also requires the host to skip the query. The shipped validator can query a missing pathname. The native path fixtures establish the distinction by collecting the raw return, the host's resolution result and the file effect separately, including for an attempted create. [Phased unlink assertions](../../tests/suites/witness_contract/check_phases.py) · [Native and integrated path controls](../../tests/CHANGE-VERIFICATION.md#native-path-query-observations)

   **Proposed test change.** Relax only the requirement to skip collection for the deliberately absent name. With today's planner, require the truthful unavailable record, `query_not_requested` and unestablished order. If PW offers a raw query, exercise that path explicitly and require the submitted pathname, planning-time resolution evidence and actual validator record for that worker and phase. Its native value can be informational. A denial-shaped return on an unresolved name cannot by itself establish a policy denial. In both cases enforce the unlink, the later `ENOENT`, fresh planning and the collection-before-action barrier. A change to eligibility also calls for the existing order-barrier mutation control. [Query eligibility](../REQUEST.md#contract-probes-query-eligibility) · [Order-barrier verification](../../tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls)

5. **Proposed — Before using a Mach lookup to judge a query's predictive value, check that the attempt used the namespace the query names.**

   In `runner_filter_local_name`, the query names `com.apple.logd` in the local namespace. The worker's `bootstrap_look_up` uses the global namespace. The comparison reports a matched operation and an unresolved target relation. Make the service's successful lookup (`rc == 0`) informational in this case. Enforce the attempted service name, the native result and comparison consistent with it, and the unresolved target relation. The menagerie's `core_mach_simple` already checks successful and failed global-name lookups. [Local-name fixture](../../tests/suites/runner_filter_local_name/README.md) · [Shared checker](../../tests/lib/unavailable_prediction.py) · [Menagerie expectations](../../tests/fixtures/blackbox_menagerie/cases/core.json)

   **Limit of the finding.** Of the four excluded pairs, only `mach-lookup/local_name` has a named native query the shipped validator can issue, using candidate filter ID 3 on the investigated build. Its raw return could be reported as such. Assessing local-name predictive value still requires an independently observed local-name operation. For `iokit-open-service/iokit_registry_entry_class`, `iokit-open-user-client/iokit_user_client_class` and `sysctl-read/sysctl_name`, the Swift planner has filter labels but the native validator has no numeric mapping for those labels. Keep those three unavailable checks. For local Mach, keep the current no-query check for as long as the planner withholds the candidate query. [Planner tests](../../runner/Tests/PWRunnerCoreTests/PredictionUnavailableTests.swift) · [Native filter mapping](../../controller/tools/sb_api_validator/sb_api_validator.c) · [Scope of the calibration evidence](../../tests/suites/witness_contract/harness/VERIFICATIONS.md)

6. **Proposed — Check both path spellings when interpreting an alias experiment.**

   The menagerie's `read_alias_foo` row expects a deny prediction and a failed open despite the fixture's nominal allow rule. Make the predicted and attempted outcomes informational on the alias rows, including whether the annotated mismatch occurs. Retire the skip for an absent alias mismatch. Keep the requested path, native result, errno, observed path on successful open, and the separate strict allow and deny controls. [Alias fixtures](../../tests/fixtures/blackbox_menagerie/cases/core.json) · [Mismatch checker](../../tests/suites/blackbox_menagerie/validate_run.py)

7. **Proposed — Use the host's path mapping when choosing a literal path for a policy rule.**

   Two CLI diagnostics tests assume stock macOS spellings, including a particular Data-volume path for `/etc/hosts`. Derive the expected paths independently from this machine's realpath and firmlink table. Keep checking the actual mapping and PW's representation of a form that equals the input, differs from it, or could not be resolved. [CLI path diagnostics](../../controller/integration/cli_contract.rs) · [Path representation controls](../../runner/Tests/PWRunnerCoreTests/PathDiagnosticsTests.swift)

8. **Proposed — Inspect which files an OS-supplied policy import resolved to on this machine.**

   The `system.sb` helper integration fixes its installed location and names `dyld-support.sb` as a transitive dependency. Allow those host facts to vary. Keep the documented search order, independent checks of each file's bytes and size, recomputation of the closure hash, and a recursion check using files with known contents. [Helper integration](../../controller/integration/cli_contract.rs) · [Resolver controls](../../controller/src/sbpl_imports.rs)

9. **Proposed — When an import scan is incomplete, read its individual errors as well as the summary.**

   In `import_failure_order`, allow either of two missing files to headline `failure` when the inventory correctly identifies both problems. Keep the incomplete status and both file/error associations. Keep the submitted-source diagnostic when the summary is its only reporting channel. [Dossier assertions](../../tests/suites/witness_contract/check_dossier.py) · [Import inventory contract](../contract/42-dossier.surface.md)

10. **Proposed — When saving generated JSON, provide writable stdout and check the saved document before submission.**

    The `example` and `test-input read` cases launched with stdout already closed require exit zero and empty stderr. Neither case observes a saved document. Make those two launch outcomes informational. Keep the complete-document checks and the broken-pipe, short-write and flush-failure controls. [CLI publication assertions](../../controller/integration/cli_contract.rs) · [Publication contract](../contract/10-request.surface.md)

11. **Proposed — Choose a valid ordinary or actor form before relying on fallback compilation.**

    A controlled XPC failure fixes which input reaches the helper when `actors` is mixed with a top-level policy, empty, or scalar. Retire that choice for malformed forms. Keep host admission, the original transport outcome, accurate attribution of any helper capture, and exact held-input checks for valid ordinary and actor forms. [Fallback tests](../../controller/src/run_flow.rs) · [Helper contract](../contract/11-policy.surface.md)

12. **Proposed — For a create on an existing file, judge its effect from the write-open and the file itself.**

    `create_existing_file_preserves_contents` derives the expected query return from expected attempt success even though the compound create has no single matching query operation. Make the native verdict informational in this case. Keep the permitted and refused write-opens, worker and operand association, and the independent before/after checks on file bytes and inode. [Create checker](../../tests/suites/witness_contract/check_create_existing.py) · [Comparison contract](../contract/31-steps.surface.md)

13. **Proposed — Copy one target string into both operands when byte-exact identity matters.**

    Producer and reader tests require `same_submitted` for two differently encoded spellings of *café*. Consider allowing `unresolved` for this pair. This would change a public comparison rule. Keep both submitted spellings, compatible-filter checks, byte-exact validator association, and the controls for identical and clearly different targets. [Producer test](../../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift) · [Reader controls](../../tests/suites/blackbox_e2e/checker_controls.py) · [Target relation](../contract/31-steps.surface.md)

14. **Proposed — Verify a helper's claimed file effect by inspecting the file before and after the run.**

    The denied-write row in `exec_helper_effect_is_real` requires the literal `--write` in the helper's stderr. Drop that wording requirement. Keep the independently observed marker bytes or absence, child PID, and known exit status. The separate argument and stream control checks status mapping and exact stderr forwarding. [Effect case](../../tests/suites/run_effects/check_exec_effect.py) · [Stream control](../../tests/suites/runner_use_c_worker/run.sh)

15. **Proposed — Establish baseline access before crediting an extension with granting access.**

    Make the exact `deny` prediction informational in `extension_policy_qualification`. Keep the subject's failed baseline fresh open and the ordinary control's successful read of the same bytes. Also keep applied-policy identity, worker PID, truthful query reporting and ordering. [Policy qualification](../../tests/suites/witness_contract/check_extension_policy_qualification.py) · [Extension contract](../contract/14-extensions.surface.md)

16. **Proposed — Check the interpreter query, actual spawn, and child output when judging script execution.**

    Treat the `interpreter_all` script fixture's precise combination of interpreter denial, absent child, and permission errno as supported-system calibration. Keep target identity, accurate spawn and failure evidence, the positive script-output control, and visibility when native behavior changes. [Script assertions](../../tests/suites/runner_exec_dac/check_query_scope.py) · [Suite purpose](../../tests/suites/runner_exec_dac/README.md)

17. **Proposed — Check `text_exact`, truncation and EOF before treating helper output as a complete byte record.**

    In the invalid-UTF-8 case, 17 invalid bytes produce 17 replacement characters. Reconsider the two assertions prescribing this exact text for lossy decoding. Keep visible replacement, `text_exact == false`, independently measured byte counts and EOF. The valid-text, embedded-NUL and split-scalar controls exercise separate obligations. [Invalid UTF-8 checker](../../tests/suites/runner_use_c_worker/check_exec_stream.py) · [Stream text contract](../contract/31-steps.surface.md)

18. **Proposed — Read the stream's `truncated` and `eof` fields before treating an exec child's output as complete.**

    A child can print the marker itself. A composition control supplies the literal text `done\n... [truncated]` and requires all 20 bytes to survive with `truncated == false`. The converse also matters. A collector that stops before EOF can retain every byte it read while leaving bytes unread. Finding 17 concerns loss during text decoding. This finding concerns how much output was collected and retained. [Stream fields](../contract/32-lifecycle.surface.md) · [Literal-marker control](../../runner/Tests/PWRunnerCoreTests/ExecStreamTextTests.swift)

    **Proposed test change.** For 4,096 ASCII bytes, `exec_attempt_stdout_truncation_marker` checks for the marker text and exactly 1,007 retained bytes. The host reserves 16 of the 1,023 available bytes for the suffix. Retire the required suffix and its 1,007-byte expectation together if the public stream contract adopts the structured flag as sufficient. The limit account and evidence reader also encode that reservation. Use the directly captured child output to verify received and retained byte counts, the longest prefix that fits the applicable allowance without splitting a valid UTF-8 scalar, and the relationship `truncated == (bytes_received > bytes_retained)`. Keep the exact-limit, EOF, and child-authored marker checks. [Overflow case](../../tests/suites/runner_use_c_worker/run.sh) · [Direct-output comparisons](../../tests/suites/runner_use_c_worker/check_exec_stream.py) · [Evidence reader](../../tests/lib/consumer.py) · [Limit owner](../limits.json)

19. **Proposed — Before relying on a transitive import from a system profile, check that dependency in the inventory on the Mac where PW ran.**

    The shipped-helper test for `system.sb` specifically requires a record named `dyld-support.sb`. Make that child name informational. Keep the independent reads of reported files, the size and hash comparisons, and the closure-hash check. A scanner that omits a child can still produce a consistent digest for its shortened list. The test-owned diamond requires its transitive leaf exactly once and catches that omission in the resolver. To keep the same protection through the shipped helper, use a controlled literal parent/child import there and assert that the child's record is returned. This lead concerns the child name specifically. Finding 8 also covers the installed location of the parent. [Helper integration](../../controller/integration/cli_contract.rs) · [Controlled import graphs](../../controller/src/sbpl_imports.rs) · [Scanner scope](../contract/11-policy.surface.md)

20. **Proposed — When an import inventory is incomplete, inspect the record for each file you depend on and the summary for problems in the submitted source.**

    This independently identifies the `import_failure_order` assertion in finding 9. The fixture names `zz-absent.sb` before `aa-absent.sb`, checks both sorted file/error pairs, then requires only `aa-absent.sb` to appear in `failure`. Allow either complete, accurate file diagnostic to lead the summary. Revise the public promise of first failure in traversal order if selected. Keep the exact records and `incomplete` status. A submitted-source import form the scanner could not follow has no file record of its own, so the mixed root/file case still needs the root diagnostic. A dependency missing from an incomplete inventory has no established scan result. [Dossier assertions](../../tests/suites/witness_contract/check_dossier.py) · [Import inventory contract](../contract/42-dossier.surface.md)

21. **Proposed — When overriding the client wait budget for `policy-witness run`, supply `--timeout-ms` once.**

    `run.repeated_timeout` passes `5` and `7` with no specimen. Its assertion that `data.timeout_ms` is `7` fixes which value appears in the error envelope. The command never starts a client. Retire that winner assertion and narrow the documented last-value rule for this option if selected. Keep `run.timeout_one` and `run.timeout_zero`, which check that a single `1` is recorded and `0` is refused. The BYOXPC orchestration test separately observes one `7000` override reaching the client, and the deadline tests cover what the client does with its budget. The input here is a repeated CLI option, distinct from repeated specimen keys in finding 1 and runner selectors in finding 2. [CLI cases](../../controller/integration/interface_cases.json) · [Current CLI rule](../../controller/README.md) · [Client invocation check](../../controller/src/run_flow.rs) · [Deadline checks](../../controller/src/runner_client.rs)

## What we must teach a user

A user learning the following may never see `QUESTIONS.md`.

### Numbered findings

1. **What starts fresh in a PW run is the process.** 

2. **A PW phase lets you place a prediction on one side of a real event.** Suppose a phase contains an unlink followed by an open of the same path. PW holds the worker while a separate validator collects eligible predictions against its live PID. Then it releases the worker to perform both actions. The prediction associated with the open belongs to the time before the unlink, even though the open itself happens after. Put the open in a second phase and PW can attempt a fresh query after removal, with the same worker and policy still in place. The path may then be unavailable for prediction, while the open can still go ahead and report `ENOENT`.

3. **A PW specimen can contain its own control subject.** Alice and Bob run separate copies of the same signed worker with the same profile. Both try to read a file containing a recognizable word. A third actor gives Alice a read extension. She consumes it, then both readers try again. In a second run, Bob receives and consumes the extension instead. If only Alice reads the word in the first run and only Bob reads it in the second, the successful read has followed the recipient. The other reader shows what another copy of the same program could do with the same file without receiving the extension. PW lets the user make that comparison without writing either reader.

## What work can the user trust PW to do?

A user investigating a sandbox policy needs evidence they can use whichever way the experiment turns out. Without PW, what would they have to arrange for the experiment to answer their question, and what would they have to check before drawing a conclusion? Even if PW performs every operation in its published contract exactly as described, naming a computation can still leave the reader wondering which part of that work it takes off their hands. PW can do that part for them even when the result overturns their expectation.

An entry earns its place when a reader can cross one duty off their own procedure. State what they can omit, under what conditions they can rely on PW for it, and where their own effort or judgment resumes. If a reader could reasonably entrust one part to PW while retaining the next, draw the boundary there. A general description of PW gives the reader too little detail to make that choice.

Follow one ordinary use from the user guide into the shipped implementation. Note what the caller prepares, trace what the app takes over, and identify what the caller still has to establish after PW returns. Read the corresponding case in `tests/suites/` from fixture setup through its assertions. Ask who supplied the facts each assertion relies on. A passing test can credit the app with work the harness actually did. Where that division is unclear, try the same task locally with the shipped app and compare what it supplies with what the harness supplied. *If PW ceased doing this particular work, what would the user have to add to accomplish the same task?*

### Numbered findings

1. **Coordinate a query with the worker it concerns.** To obtain a prediction before an action, the user would otherwise have to keep the sandboxed process alive, identify it to a separate caller, and hold it until the query was collected. For an eligible query that PW reports as `query_first`, the user can leave that coordination to PW.

2. **Get an observation out without relaxing the policy to report it.** For a built-in attempt under `(deny default)`, the user can omit writing a reporting helper or granting the worker permission to write a results file. PW prepares shared memory before the policy takes effect, and its host collects what the worker publishes there. If the worker stops before publishing, the effect of the attempt may still need an independent check.

3. **Keep a later edit to the specimen from changing the policy PW submits.** Once `policy-witness run` has read the specimen, the user can omit making a private staging copy solely to keep PW from reopening a changed file during that invocation. The controller resolves and submits the request it already holds.

## What must a user arrange outside of PW?

Sketch the experiment as a recipe a colleague could carry out at a terminal. Put each PW invocation on its own line and fill in the work around it. Which line would the colleague have to supply to make the experiment answer their question? Give that line enough detail to try by hand or turn into a script. Include any tradeoff that would change whether the colleague would use the recipe.

### Numbered findings

1. **Choose the second path after inspecting the first read.** One specimen can schedule two reads in successive phases of the same worker when both paths are known at submission. To let the first result determine the second path, the caller makes that choice between runs.

   ```sh
   policy-witness run first.json > first-result.json
   # Inspect the first read in first-result.json, choose the next path, and write second.json.
   policy-witness run second.json > second-result.json
   ```

   The person at the terminal can make that choice, or a script can apply their decision rule. The chosen path carries over in the second specimen. Its read takes place in a fresh worker, even if both specimens use the same policy.
