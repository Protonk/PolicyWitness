# PolicyWitness architecture

A tour of the internals at the level between the [README](../README.md)'s
Flow paragraph and the directory READMEs: how one run unfolds in time and the
boundaries it crosses. It is for a developer or agent who has read the README
and is about to open a directory. It is not a field reference, a contract, a
module list, a test map or a build guide; each of those exists and is linked.

The three figures are generated from [architecture.json](architecture.json)
by [generate_architecture.py](generate_architecture.py). Every node and edge in
a figure has an id, and the table beside the figure names, for that id, the
source symbol that implements it and the check that pins it. A node or edge
is chased by its id, not by prose.

## Why these processes exist

## Process topology

<!-- BEGIN GENERATED ARCHITECTURE GRAPH topology -->
![Process topology](architecture-topology.svg)

*Figure: process topology. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [architecture-topology.dot](architecture-topology.dot). The ids in the figure are the ids in the tables below, and each row names the source and the check that pin it.*

#### Process topology nodes

| Id | Node | Kind | Where | Lifetime | Language | Started by | Sandboxed | Native sandbox API | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user | the caller | person | a shell or a harness | owns the request file and reads the envelope |  |  |  |  | [`pub fn run`](../controller/src/cli.rs) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| controller | policy-witness | executable | app top level | one run | Rust | the caller | no | none | [`fn main`](../controller/src/main.rs); [`cmd_run`](../controller/src/run_flow.rs) | [`consumer_controls`](../tests/suites/blackbox_e2e/checker_controls.py); [`EXECUTABLES`](../tests/lib/artifact.py) |
| client | pw-runner-client | executable | app top level | one run | Swift | the controller | no | none | [`readDataToEndOfFile`](../runner/Clients/PWRunnerClient/main.swift); [`NSXPCConnection`](../runner/Clients/PWRunnerClient/main.swift) | [`mod tests`](../controller/src/runner_client.rs); [`client_output_control`](../tests/suites/blackbox_e2e/checker_controls.py) |
| host | PWRunner | executable | inside the XPC bundle | one specimen; exits 50 ms after replying | Swift | launchd: XPC service lookup, or a Mach service for BYOXPC | no | none, by the invariance rule | [`NSXPCListener.service()`](../runner/Services/PWRunner/main.swift); [`runSpecimen`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`milliseconds(50)`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`host_invariance`](../tests/lib/artifact.py); [`check_host_invariance`](../tests/suites/source_drift/check.py) |
| worker | pw-probe-runner | sandboxed | inside the XPC bundle | until the host requests exit; spins after done | C | the host | yes; applies the specimen policy to itself | sandbox_compile_string, params, sandbox_apply | [`sandbox_compile_string`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`sandbox_apply`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh); [`CWorkerOrchestrator`](../tests/suites/runner_use_c_worker/run.sh) |
| exec_child | exec helper children | sandboxed | the caller's path | bounded by the exec deadline and the attempt budget | caller-supplied | the worker | inherit the worker's sandbox | none of PolicyWitness's | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`runner_exec_lifecycle`](../tests/suites/runner_exec_lifecycle/run.sh); [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) |
| validator | sb_api_validator | executable | inside the XPC bundle | one batch | C | the host, after applied | no | sandbox_check | [`sandbox_check`](../controller/tools/sb_api_validator/sb_api_validator.c); [`SANDBOX_CHECK_NO_REPORT`](../controller/tools/sb_api_validator/sb_api_validator.c); [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`bothBinariesExist`](../runner/Tests/PWRunnerCoreTests/CWorkerValidatorTests.swift) |
| observer | sandbox-log-observer | executable | app top level | one scan | Rust | the controller, after execution completes, in its own process group | no | none | [`capture_sandbox_logs_with_timeout`](../controller/src/sandbox_log.rs); [`process_group`](../controller/src/log_capture.rs) | [`mod tests`](../controller/src/bin/sandbox-log-observer.rs); [`def main`](../tests/suites/witness_contract/check_deny_capture_window.py) |
| log_show | log show | os | /usr/bin/log | one query | OS | the observer | no | none | [`Command::new("/usr/bin/log")`](../controller/src/bin/sandbox-log-observer.rs) | [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) |
| sbpl_check | sbpl-check | executable | app top level | one compile | Rust | the controller, only for an admitted xpc_error reply | no | sandbox_compile_string and params; never applies | [`sandbox_compile_string`](../controller/src/bin/sbpl-check.rs); [`run_policy_check`](../controller/src/policy_check.rs) | [`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`](../controller/src/run_flow.rs) |
| launchd | launchd | os | system |  | OS |  | no | none | [`NSXPCListener(machServiceName:`](../runner/Services/PWRunner/main.swift); [`MachServices`](../controller/src/runner_manager.rs) | [`runner_mach_service_liveness`](../tests/suites/runner_mach_service_liveness/run.sh); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |

#### Process topology edges

| Id | From | To | Kind | Edge | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | user | controller | channel | argv in; one JSON envelope on stdout | [`pub fn run`](../controller/src/cli.rs); [`print_envelope`](../controller/src/json_contract.rs) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py); [`envelope_shape_golden_agrees_with_the_manifest`](../controller/src/run_flow.rs) |
| T2 | controller | client | spawn | spawn; held request on stdin, read to EOF; reply on stdout | [`run_pw_runner_client`](../controller/src/runner_client.rs); [`readDataToEndOfFile`](../runner/Clients/PWRunnerClient/main.swift) | [`mod tests`](../controller/src/runner_client.rs); [`client_output_control`](../tests/suites/blackbox_e2e/checker_controls.py) |
| T3 | client | host | channel | NSXPC runSpecimen(Data) and its reply | [`NSXPCConnection`](../runner/Clients/PWRunnerClient/main.swift); [`runSpecimen`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`authorizedCaller`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`CWorkerOrchestrator`](../tests/suites/runner_use_c_worker/run.sh); [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh) |
| T4 | launchd | host | launch | start on XPC lookup, or as a Mach service (BYOXPC) | [`NSXPCListener.service()`](../runner/Services/PWRunner/main.swift); [`NSXPCListener(machServiceName:`](../runner/Services/PWRunner/main.swift); [`launchctl_bootstrap`](../controller/src/runner_manager.rs) | [`runner_mach_service_liveness`](../tests/suites/runner_mach_service_liveness/run.sh); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |
| T5 | host | worker | spawn | posix_spawn; fd 0 policy pipe, fd 3 shared region, fd 4 ready pipe | [`posix_spawn_file_actions_adddup2`](../runner/Sources/PWRunnerCore/CWorker.swift); [`F_SETNOSIGPIPE`](../runner/Sources/PWRunnerCore/CWorker.swift); [`PW_SHM_ABI_MAGIC`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh); [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh) |
| T6 | host | validator | spawn | posix_spawn --batch <pid>; NDJSON probes in, verdicts out | [`runValidator`](../runner/Sources/PWRunnerCore/ValidatorClient.swift); [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`transcript_controls`](../tests/suites/runner_validator_failure/run.sh) |
| T7 | validator | worker | native | sandbox_check against the worker PID, with SANDBOX_CHECK_NO_REPORT | [`sandbox_check`](../controller/tools/sb_api_validator/sb_api_validator.c); [`SANDBOX_CHECK_NO_REPORT`](../controller/tools/sb_api_validator/sb_api_validator.c) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`independent_worker_and_host_queries`](../tests/suites/runner_live_worker_identity/run.sh) |
| T8 | worker | host | channel | evidence published in the shared region with release ordering; proceed waited for before attempts | [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`CWorkerStepResult`](../runner/Sources/PWRunnerCore/CWorker.swift); [`proceedOffset`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`signal_while_waiting`](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift); [`order_barrier_mutations`](../tests/suites/witness_contract/opt_in/mutations.sh) |
| T9 | worker | exec_child | spawn | posix_spawn after apply; stdout and stderr pipes into bounded slot buffers | [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`runner_exec_lifecycle`](../tests/suites/runner_exec_lifecycle/run.sh); [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh) |
| T10 | controller | observer | spawn | spawn in its own process group after execution; budget on argv; JSON report on stdout | [`capture_sandbox_logs_with_timeout`](../controller/src/sandbox_log.rs); [`capture_with_ops`](../controller/src/log_capture.rs); [`process_group`](../controller/src/log_capture.rs) | [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs); [`def main`](../tests/suites/witness_contract/check_deny_capture_window.py) |
| T11 | observer | log_show | spawn | log show over the padded client span; text on stdout, bounded | [`Command::new("/usr/bin/log")`](../controller/src/bin/sandbox-log-observer.rs); [`capture_sandbox_logs_with_timeout`](../controller/src/sandbox_log.rs) | [`run_span_window_floors_start_ceils_end_and_never_collapses`](../controller/src/sandbox_log.rs); [`both_raw_streams_are_bounded_at_exact_edges`](../controller/src/log_capture.rs) |
| T12 | controller | sbpl_check | spawn | spawn only for an admitted xpc_error reply; held request in; helper envelope out | [`fallback_policy_check`](../controller/src/run_flow.rs); [`run_policy_check`](../controller/src/policy_check.rs) | [`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`](../controller/src/run_flow.rs); [`refused_reply_versions_request_no_fallback_compilation`](../controller/src/run_flow.rs) |

Every node and edge above names at least one check.
<!-- END GENERATED ARCHITECTURE GRAPH topology -->

## One run in time

## Evidence channels and ownership

## Boundaries

<!-- BEGIN GENERATED ARCHITECTURE GRAPH boundaries -->
![Boundaries and their guards](architecture-boundaries.svg)

*Figure: boundaries and their guards. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [architecture-boundaries.dot](architecture-boundaries.dot). The ids in the figure are the ids in the tables below, and each row names the source and the check that pin it.*

#### Boundaries and their guards nodes

| Id | Node | Kind | Owner | Form | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| request_file | request JSON | record | the caller | a JSON file naming the request schema | [`parse_request`](../controller/src/request_patch.rs) | [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh) |
| held_request | held request bytes | record | the controller | one serialization; selectors stripped, augments spliced | [`strip_runner_selector`](../controller/src/runner_select.rs); [`pub fn resolve_augments`](../controller/src/augments.rs) | [`invalid_request_version_stops_before_selection_augments_or_client_invocation`](../controller/src/run_flow.rs) |
| run_spec | decoded request (PWRunnerRunSpec) | record | the host | Codable with closed keys | [`PWRunnerRunSpec`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`CodingKeys`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh); [`admission`](../tests/suites/failure_boundaries/check.py) |
| shm_region | shared region and policy pipe (worker ABI) | record | host writes inputs, worker writes outputs | fixed layout; magic at byte 0, source identity at byte 64 | [`PW_SHM_ABI_MAGIC`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PW_WORKER_ABI_IDENTITY_HEX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PWShmLayout`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh); [`PW_SHM_`](../tests/fixtures/contract/abi_layout.txt) |
| validator_wire | validator NDJSON (probes and verdicts) | record | host and validator, co-shipped in one bundle | NDJSON; kind sb_api_validator_verdict; no version marker | [`sb_api_validator_verdict`](../runner/Sources/PWRunnerCore/ValidatorClient.swift); [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift); [`sandbox_check`](../controller/tools/sb_api_validator/sb_api_validator.c) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`validator_overlong_request`](../tests/suites/failure_boundaries/check.py) |
| reply | runner reply (PWRunnerRunResult) | record | the host | response schema; shape golden | [`PWRunnerRunResult`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`PWContract`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`replyShapeDocuments`](../runner/Tests/PWRunnerCoreTests/ContractVersionTests.swift); [`schema_version`](../tests/fixtures/contract/response_shape.json) |
| envelope | controller envelope (kind run) | record | the controller | envelope frame; shape golden | [`SCHEMA_VERSION`](../controller/src/json_contract.rs); [`render_envelope`](../controller/src/json_contract.rs); [`complete_execution`](../controller/src/run_flow.rs) | [`envelope_shape_golden_agrees_with_the_manifest`](../controller/src/run_flow.rs); [`_validate_envelope`](../tests/lib/consumer.py) |
| observer_report | observer report (nested envelope) | record | the observer | envelope frame around observer_schema_version | [`OBSERVER_SCHEMA_VERSION`](../controller/src/bin/sandbox-log-observer.rs) | [`mod tests`](../controller/src/bin/sandbox-log-observer.rs); [`def main`](../tests/suites/witness_contract/check_deny_capture_window.py) |
| helper_envelope | sbpl-check envelope (nested) | record | sbpl-check | envelope frame; kind sbpl_check | [`run_policy_check`](../controller/src/policy_check.rs); [`sandbox_compile_string`](../controller/src/bin/sbpl-check.rs) | [`_validate_policy_check_reply`](../tests/lib/consumer.py); [`policy_check_controls`](../tests/suites/blackbox_e2e/checker_controls.py) |
| evidence_manifest | evidence manifest (in the app) | record | the build | hashes and entitlements of every shipped binary | [`manifest.json`](../tests/build-evidence.py); [`EVIDENCE_SCHEMA_VERSION`](../controller/src/evidence.rs) | [`codesign.preflight`](../tests/suites/preflight/run.sh); [`VALIDATOR_REL`](../tests/suites/witness_contract/check_dossier.py) |
| runner_registry | runner registry (BYOXPC installs) | record | the runner commands | additive-field loader; retired kind aliases kept for recovery | [`load_registry`](../controller/src/runner_manager.rs); [`alias = "machme"`](../controller/src/runner_manager.rs) | [`legacy_machme_kind_deserializes_as_byoxpc`](../controller/src/runner_manager.rs); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |

#### Boundaries and their guards edges

| Id | From | To | Kind | Edge | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | request_file | held_request | guard | request version gate; selector parse; augment resolution | [`validate_request_version`](../controller/src/request_patch.rs); [`parse_runner_selector_value`](../controller/src/runner_select.rs); [`pub fn resolve_augments`](../controller/src/augments.rs) | [`invalid_request_version_stops_before_selection_augments_or_client_invocation`](../controller/src/run_flow.rs); [`accepted_input_contract`](../tests/suites/runner_outcome_bad_request/run.sh) |
| B2 | held_request | run_spec | guard | caller authorization; closed-key decode; capacity, then meaning; policy hash | [`authorizedCaller`](../runner/Sources/PWRunnerCore/PWRunnerService.swift); [`CodingKeys`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`admissionFailure(for`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`requestMeaningFailure`](../runner/Sources/PWRunnerCore/ProbeRunner.swift); [`computePolicyHash`](../runner/Sources/PWRunnerCore/SandboxApply.swift) | [`admission`](../tests/suites/failure_boundaries/check.py); [`NormalizedOutcome.badPolicy`](../runner/Tests/PWRunnerCoreTests/EnvelopeInvariantTests.swift) |
| B3 | run_spec | shm_region | guard | host writes identity, counts, slots, params; worker refuses on magic or identity mismatch (exit 4) | [`abiIdentityHex`](../runner/Sources/PWRunnerCore/CWorker.swift); [`PW_WORKER_ABI_IDENTITY`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`return 4`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh); [`independent_worker_and_host_queries`](../tests/suites/runner_live_worker_identity/run.sh); [`exec_control_states`](../tests/suites/runner_c_worker_harness/run.sh) |
| B4 | shm_region | reply | guard | release/acquire publication; proceed before attempts; disposition record from raw facts | [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`proceedOffset`](../runner/Sources/PWRunnerCore/CWorker.swift); [`PWRunnerOrdering`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | [`signal_while_waiting`](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift); [`order_barrier_mutations`](../tests/suites/witness_contract/opt_in/mutations.sh) |
| B5 | run_spec | validator_wire | guard | planned probes; strict NDJSON decode; association by unique id | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`decodeValidatorFrames`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`predictions_do_not_report`](../tests/suites/validator_batch_mode/run.sh); [`transcript_controls`](../tests/suites/runner_validator_failure/run.sh) |
| B6 | validator_wire | reply | guard | verdict joined to its step, or an explicit unavailable prediction | [`ComparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [`sb_api_validator_verdict`](../runner/Sources/PWRunnerCore/ValidatorClient.swift) | [`transcript_controls`](../tests/suites/runner_validator_failure/run.sh); [`CWorkerOrchestrator`](../tests/suites/runner_use_c_worker/run.sh) |
| B7 | reply | envelope | guard | exact response version; disposition validated and projected; reply retained unread when refused | [`reply_version`](../controller/src/run_flow.rs); [`complete_execution`](../controller/src/run_flow.rs); [`execution_diagnostics`](../controller/src/disposition.rs); [`validate_disposition`](../controller/src/disposition.rs) | [`reply_versions_are_gated_exactly`](../controller/src/run_flow.rs); [`disposition::tests::`](../tests/suites/blackbox_e2e/disposition_controls.py) |
| B8 | observer_report | envelope | guard | nested unchanged; log evidence never changes execution evidence | [`attach_sandbox_logs`](../controller/src/run_flow.rs); [`OBSERVER_SCHEMA_VERSION`](../controller/src/bin/sandbox-log-observer.rs) | [`collector_states_preserve_the_serialized_execution_half`](../controller/src/run_flow.rs); [`_validate_envelope`](../tests/lib/consumer.py) |
| B9 | helper_envelope | envelope | guard | nested unchanged; admitted by kind and frame version | [`fallback_policy_check`](../controller/src/run_flow.rs); [`_validate_policy_check_reply`](../tests/lib/consumer.py) | [`fallback_compilation_is_requested_only_for_an_admitted_xpc_error`](../controller/src/run_flow.rs); [`policy_check_controls`](../tests/suites/blackbox_e2e/checker_controls.py) |
| B10 | evidence_manifest | envelope | guard | dossier compares selected binaries with manifest baselines; lookup by exact path and kind | [`unique_typed_entry`](../controller/src/evidence.rs); [`pub struct Binaries`](../controller/src/dossier.rs) | [`codesign.preflight`](../tests/suites/preflight/run.sh); [`VALIDATOR_REL`](../tests/suites/witness_contract/check_dossier.py) |
| B11 | runner_registry | held_request | guard | selection resolves a BYOXPC target; selector fields stripped before XPC | [`resolve_runner_target_with_registry`](../controller/src/runner_select.rs); [`strip_runner_selector`](../controller/src/runner_select.rs); [`load_registry`](../controller/src/runner_manager.rs) | [`legacy_machme_kind_deserializes_as_byoxpc`](../controller/src/runner_manager.rs); [`runner_byoxpc`](../tests/suites/runner_byoxpc/run.sh) |

Notes:

- `validator_wire`: The wire carries no version because the host and the validator are built, signed and shipped inside one XPC bundle, so no cross-version pairing can occur; the suite pins the shape.

Every node and edge above names at least one check.
<!-- END GENERATED ARCHITECTURE GRAPH boundaries -->

## Principles as enforced constraints

## How the system verifies itself

<!-- BEGIN GENERATED ARCHITECTURE GRAPH documents -->
![The document graph](architecture-documents.svg)

*Figure: the document graph. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [architecture-documents.dot](architecture-documents.dot). The ids in the figure are the ids in the tables below, and each row names the source and the check that pin it.*

#### The document graph nodes

| Id | Node | Kind | Owns | Carries | Checks | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract_json | docs/contract.json | manifest | the request, response and envelope version numbers |  |  | [`controller_envelope`](../docs/contract.json) | [`class `](../tests/suites/source_drift/contract.py) |
| limits_json | docs/limits.json | manifest | every runtime limit with its source and check citations |  |  | [`schema_version`](../docs/limits.json) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| matrix_json | tests/fixtures/comparison/matrix.json | manifest | the comparison scenario matrix |  |  | [`observation`](../tests/fixtures/comparison/matrix.json) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| architecture_json | docs/architecture.json | manifest | the nodes and edges of these figures, each with its citations |  |  | [`schema_version`](../docs/architecture.json) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| catalog_json | tests/catalog.json | manifest | the registered suites and cases |  |  | [`"suites"`](../tests/catalog.json) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| gen_contract | generate_contract.py | generator | the generated contract-version regions |  |  | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| gen_limits | generate_limits.py | generator | the limits tables, the scenario matrix and the guide's copied regions |  |  | [`CONTRACT_NAME`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| gen_identity | generate_worker_identity.py | generator | the host/worker source identity regions |  |  | [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`class `](../tests/suites/source_drift/contract.py) |
| gen_architecture | generate_architecture.py | generator | these figures, their dot and SVG files and the tables beside them |  |  | [`MANIFEST_NAME`](../docs/generate_architecture.py) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| contract_md | docs/CONTRACT.md | document |  | the version sentence and table |  | [`BEGIN GENERATED CONTRACT VERSIONS`](../docs/CONTRACT.md) | [`class `](../tests/suites/source_drift/contract.py) |
| limits_md | docs/LIMITS.md | document |  | the limits tables and coverage |  | [`BEGIN GENERATED LIMITS`](../docs/LIMITS.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| guide | docs/PolicyWitness.md | document |  | copied limits, questions and reading rules; the version sentence; the only document that ships |  | [`BEGIN COPIED LIMITS`](../docs/PolicyWitness.md); [`BEGIN GENERATED CONTRACT VERSIONS`](../docs/PolicyWitness.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py); [`--stage-guide`](../build.sh) |
| questions_md | docs/QUESTIONS.md | document |  | the shared questions the guide copies |  | [`BEGIN SHARED QUESTIONS`](../docs/QUESTIONS.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| failure_contract | tests/FAILURE-PROPAGATION-CONTRACT.md | document |  | the generated scenario matrix and the shared reading rules |  | [`BEGIN GENERATED SCENARIO MATRIX`](../tests/FAILURE-PROPAGATION-CONTRACT.md); [`BEGIN SHARED READING RULES`](../tests/FAILURE-PROPAGATION-CONTRACT.md) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| architecture_md | docs/ARCHITECTURE.md | document |  | these three figures and their tables |  | [`BEGIN GENERATED ARCHITECTURE GRAPH`](../docs/ARCHITECTURE.md) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| agents_md | AGENTS.md | document |  | the canonical sandboxed-harness note |  | [`Sandboxed automation harnesses`](../AGENTS.md) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) |
| controller_readme | controller/README.md | document |  | the CLI surface block and the version sentence |  | [`CLI surface (contract)`](../controller/README.md); [`BEGIN GENERATED CONTRACT VERSIONS`](../controller/README.md) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| runner_readme | runner/README.md | document |  | the harness-note copy, the test-seam table and the version sentence |  | [`Sandboxed automation harnesses`](../runner/README.md); [`_test_overrides`](../runner/README.md) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py); [`check_test_overrides_table_agreement`](../tests/suites/source_drift/check.py) |
| tests_readme | tests/README.md | document |  | the harness-note copy and the suite table |  | [`Sandboxed automation harnesses`](../tests/README.md) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py); [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| coverage_md | tests/COVERAGE.md | document |  | the outcome coverage matrices |  | [`Normalized outcome coverage matrix`](../tests/COVERAGE.md) | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) |
| api_swift | PWRunnerAPI.swift | source |  | the Swift contract versions and the outcome vocabularies |  | [`PWContract`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`NormalizedOutcome`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) |
| json_contract_rs | json_contract.rs | source |  | the Rust contract versions; the envelope frame |  | [`SCHEMA_VERSION`](../controller/src/json_contract.rs) | [`class `](../tests/suites/source_drift/contract.py) |
| contract_py | tests/lib/contract.py | source |  | the Python contract versions and the worker identity |  | [`CONTROLLER_ENVELOPE`](../tests/lib/contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| abi_header | pw_probe_runner_abi.h | source |  | the C identity region and the shared-region layout |  | [`PW_WORKER_ABI_IDENTITY_HEX`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh) |
| cworker_swift | CWorker.swift | source |  | the Swift identity region and the layout mirror |  | [`abiIdentityHex`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`runner_abi_layout`](../tests/suites/runner_abi_layout/run.sh) |
| cli_rs | cli.rs | source |  | the usage text the controller README mirrors |  | [`pub fn run`](../controller/src/cli.rs) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| identity_sources | worker and runner sources | source |  | every byte the identity digest covers |  | [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`class `](../tests/suites/source_drift/contract.py) |
| suites | tests/suites/<name>/ | source |  | one run.sh and README per suite |  | [`suites_with_run_sh`](../tests/suites/source_drift/check.py) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| drift_check | source_drift check.py | check |  |  | copies and vocabularies that are not generated | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) | [`planner`](../tests/suites/source_drift/check_planner.py) |
| drift_limits | source_drift limits.py | check |  |  | the limits generator's copies and every local documentation link | [`broken_links`](../tests/suites/source_drift/limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| drift_contract | source_drift contract.py | check |  |  | the contract and identity generators' copies | [`class `](../tests/suites/source_drift/contract.py) | [`contract_versions`](../tests/suites/source_drift/run.sh) |
| drift_architecture | source_drift architecture.py | check |  |  | this manifest against its dot, SVG and document copies | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) | [`architecture_documentation`](../tests/suites/source_drift/run.sh) |
| build | build.sh | check |  |  | runs the generators' checks before compiling and stages the guide | [`generate_worker_identity.py`](../build.sh); [`--stage-guide`](../build.sh) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |

#### The document graph edges

| Id | From | To | Kind | Edge | Sources | Checks |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | contract_json | gen_contract | reads | version numbers | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D2 | gen_contract | contract_md | writes | version sentence and table | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D3 | gen_contract | api_swift | writes | PWContract | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D4 | gen_contract | json_contract_rs | writes | SCHEMA_VERSION and the schema constants | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D5 | gen_contract | contract_py | writes | version constants | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D6 | gen_contract | guide | writes | version sentence | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D7 | gen_contract | runner_readme | writes | version sentence | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D8 | gen_contract | controller_readme | writes | version sentence | [`TARGETS`](../docs/generate_contract.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D9 | limits_json | gen_limits | reads | limits with citations | [`load_limits`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D10 | matrix_json | gen_limits | reads | scenario rows | [`MATRIX_NAME`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D11 | questions_md | gen_limits | reads | shared questions | [`QUESTIONS_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D12 | failure_contract | gen_limits | reads | shared reading rules | [`RULES_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D13 | gen_limits | failure_contract | writes | scenario matrix | [`MATRIX_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D14 | gen_limits | limits_md | writes | limits tables and coverage | [`COVERAGE_START`](../docs/generate_limits.py) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D15 | gen_limits | guide | writes | copied limits, questions and reading rules; staged copy at build | [`GUIDE_START`](../docs/generate_limits.py); [`--stage-guide`](../build.sh) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D16 | identity_sources | gen_identity | reads | sorted paths and contents, length-framed | [`SOURCE_DIRS`](../docs/generate_worker_identity.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D17 | gen_identity | abi_header | writes | identity bytes | [`TARGETS`](../docs/generate_worker_identity.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D18 | gen_identity | cworker_swift | writes | identity bytes | [`TARGETS`](../docs/generate_worker_identity.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D19 | gen_identity | contract_py | writes | identity hex | [`TARGETS`](../docs/generate_worker_identity.py) | [`class `](../tests/suites/source_drift/contract.py) |
| D20 | architecture_json | gen_architecture | reads | nodes, edges, styles and citations | [`load_manifest`](../docs/generate_architecture.py) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| D21 | gen_architecture | architecture_md | writes | figure regions; dot and stamped SVG files beside the document | [`render_region`](../docs/generate_architecture.py); [`stamp_svg`](../docs/generate_architecture.py) | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) |
| D22 | agents_md | runner_readme | copies | harness note, first paragraph | [`HARNESS_NOTE_HEADING`](../tests/suites/source_drift/check.py) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) |
| D23 | agents_md | tests_readme | copies | harness note, first paragraph | [`HARNESS_NOTE_HEADING`](../tests/suites/source_drift/check.py) | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) |
| D24 | cli_rs | controller_readme | copies | usage text | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) |
| D25 | api_swift | coverage_md | copies | one matrix row per outcome constant | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) |
| D26 | api_swift | runner_readme | copies | test-seam table from PWRunnerTestOverrides | [`check_test_overrides_table_agreement`](../tests/suites/source_drift/check.py) | [`check_test_overrides_table_agreement`](../tests/suites/source_drift/check.py) |
| D27 | suites | tests_readme | copies | one suite-table row per suite | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| D28 | suites | catalog_json | copies | suite directories equal catalog suites | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) |
| D29 | drift_check | agents_md | checks | harness note equality across three copies | [`check_harness_note_agreement`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D30 | drift_check | controller_readme | checks | CLI surface block equals cli.rs usage | [`check_cli_surface_agreement`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D31 | drift_check | coverage_md | checks | every outcome constant has a row and every row a constant | [`check_normalized_outcomes_have_matrix_rows`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D32 | drift_check | tests_readme | checks | suite table equals suites and catalog | [`check_index_vs_disk`](../tests/suites/source_drift/check.py) | [`runner_source_manifests_agree`](../tests/suites/source_drift/run.sh) |
| D33 | drift_limits | gen_limits | checks | --check, stale-copy and staging controls; every local link in docs/*.md | [`broken_links`](../tests/suites/source_drift/limits.py) | [`limits_documentation`](../tests/suites/source_drift/run.sh) |
| D34 | drift_contract | gen_contract | checks | --check and generator controls | [`class `](../tests/suites/source_drift/contract.py) | [`contract_versions`](../tests/suites/source_drift/run.sh) |
| D35 | drift_contract | gen_identity | checks | regeneration, relocation and stale-value controls | [`class `](../tests/suites/source_drift/contract.py) | [`contract_versions`](../tests/suites/source_drift/run.sh) |
| D36 | drift_architecture | gen_architecture | checks | --check, citation, stale-copy and SVG-stamp controls | [`ArchitectureDocumentationTests`](../tests/suites/source_drift/architecture.py) | [`architecture_documentation`](../tests/suites/source_drift/run.sh) |
| D37 | build | gen_limits | checks | --check before compiling; --stage-guide into dist | [`--stage-guide`](../build.sh) | [`LimitsDocumentationTests`](../tests/suites/source_drift/limits.py) |
| D38 | build | gen_contract | checks | --check before compiling | [`generate_contract.py`](../build.sh) | [`class `](../tests/suites/source_drift/contract.py) |
| D39 | build | gen_identity | checks | regenerate before compiling; --check before signing | [`generate_worker_identity.py`](../build.sh) | [`class `](../tests/suites/source_drift/contract.py) |

Every node and edge above names at least one check.
<!-- END GENERATED ARCHITECTURE GRAPH documents -->

## BYOXPC as a variation on launch and selection
