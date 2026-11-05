# I1 actor parameter diagnostic preparation

Prepared source and coverage only. No build, tests, compiler, generator, formatter check, dispatcher (including listing), or native trial ran. The user-requested sleep checkpoint remains ahead of execution. Context: sibling `COMMON.md`, investigation `../investigations/admission-report.md`, and the I1 assignment in the root plan.

## Mechanism and contract judgment

[ActorPlan.swift](../../../runner/Sources/PWRunnerCore/ActorPlan.swift) previously discarded actor ownership by emitting bare `value`. [CWorkerRequestPlanning.swift](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift) consequently reported the legacy `policy.params.<key>` location. The prepared change retains the actor policy prefix in `admission_failure.field` as `actors.<index>.sandbox.policy.value`; path conversion recognizes that contextual value field and appends the safe parameter key as one segment beneath `params`. Parameter-count refusals still name `actors.<index>.sandbox.policy.params` without a key.

Legacy `value` still maps to `policy.params.<key>`. Key refusals still name bare `key`, omit `parameter_key`, and withhold the path. No gate, limit, ordering, normalization, execution, or native layout changed. The existing safe-key echo and request-path constructors remain authoritative: an admitted key can be up to 127 UTF-8 bytes in the admission record, while a request-failure component over 63 bytes withholds the entire path.

This repairs a location under the existing [structured refusal contract](../../../docs/CONTRACT.md#structured-request-refusals); it does not reinterpret the diagnostic's meaning or change accepted requests. No contract version bump or shape change is proposed. The field spelling is observably more specific, so public documentation should name it when explaining actor parameter failures. Source searches found no closed field-name dispatch in Rust or Python readers; Swift Codable retains the string. Existing field-name oracles in `QueryAdmissionTests`, `ReplyFailureTests`, `failure_boundaries/check.py`, and `witness_contract/check_max_target_reply.py` concern preserved legacy/other fields. The limits generator uses field text for documentation routing, not runtime admission.

## Prepared acceptance assertions

[RequestContractTests.swift](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift) adds one existing-group control with independent numeric expectations:

- Accepted 127-byte key and 383-byte value; rejected 384-byte value and embedded NUL, with exact counts, units, and maxima.
- Three policies, a shared key, multiple rejected values, and independently chosen key order establish the first offending actor and sorted key rather than merely any plausible path.
- Safe 127-byte admission echo with null diagnostic path; exact 63-byte path component retained and 64-byte component withheld.
- Rejected 128-byte/NUL keys precede their bad values and remain unechoed; 1,025 parameters precede bad values and retain the distinct count path.
- Legacy parameter-value path remains unchanged.

Six literal cases appended to [examples.json](../../../tests/fixtures/request_contract/examples.json) are consumed unchanged by the existing two Swift corpus loops and the CLI/direct-XPC `accepted_input_contract` loop: `actor_parameter_value_nul`, `actor_parameter_value_bytes`, `actor_parameter_exact_bytes`, `actor_parameter_key_bytes`, `actor_parameter_key_nul`, and `actor_parameter_path_bound`. Rejected values use three policies, with an earlier actor carrying a real file-create action. Exact expected paths contain the dotted key `K.dot` as one component. Existing live assertions require absent independent file effects, empty steps, and no worker/validator observations for refusals; the accepted exact-bound case must create the file. Thus a diagnostic-only fabricated pass cannot establish public no-execution. No materializer changes or new suite registration is needed; the corpus is authored input, not generated output.

## Changed files and deferred validation

Only the two production files, `RequestContractTests.swift`, the authored corpus, and this report were edited. The coordinator owns worker-identity regeneration because both production files are identity inputs. No other generated dependency was identified.

After the user resumes, build through the signed pipeline with the available Developer ID identity. Run serialized checks with a fresh managed output directory and matching signed app. Primary selectors are `runner_unit/pwrunner_core_unit_executable` and `runner_outcome_bad_request/accepted_input_contract`; the core wrapper requires app, Swift, clang and Cargo, and the public case requires working XPC. Repository admission-change guidance additionally calls for `--suite failure_boundaries --suite runner_unit --suite runner_abi_layout --suite runner_c_worker_harness --suite unit`. Coordinate these with I2/I3 to avoid duplicate execution and checkout-lock contention. No wait/release/eligibility code changed, so this repair does not trigger the order-barrier mutation rerun rule. Use an unsandboxed invocation for app/worker cases per repository guidance; keep any failed artifacts unchanged for diagnostic retries.

Remaining uncertainty is execution: compilation and all prepared assertions are unverified. Public SBPL acceptance of the exact multibyte parameter fixture and forwarding of actor refusal paths must be established by the selected run, not by this preparation report. Later documentation should explain actor-specific value fields, preserve bare key withholding and the separate 127/63-byte echo/path bounds, and avoid claiming any new control passed before execution.
