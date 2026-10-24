# Outcome coverage matrices

These two matrices pin which suite/case exercises every enumerated outcome value
the runner can emit. They are reference tables for `tests/README.md`'s suite
coverage map — start there for the per-suite view.

`source_drift` enforces both matrices mechanically: every value in
`runner/Sources/PWRunnerCore/PWRunnerAPI.swift::NormalizedOutcome` and `::AttemptOutcome` must appear
here exactly once. New outcomes are added here in the same change that
introduces the constant. "Untestable" rows are not unmaintained — the notes
column says why, and names the closest unit or harness coverage.

## Normalized outcome coverage matrix

| outcome | emitted by | primary suite/case | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) + validator (sb_api_validator) joined by `CWorkerOrchestrator` | `runner_apply_isolation_v2`, `runner_apply_isolation_v3`, `integration`, `runner_use_c_worker`, others | The happy path; covered everywhere. |
| `bad_policy` | defensive host policy-hash failure (`computePolicyHash`) | `runner_unit` (`EnvelopeInvariantTests`) | Public admission refuses missing source or wrong format as `bad_request` before this boundary. A published compilation/setup/application failure maps to `runner_failed`. |
| `bad_request` | controller syntax/version/selector/augment checks + host closed request decode + `CWorkerOrchestrator.admissionFailure(for:)` (capacity first) + `requestMeaningFailure` | `runner_outcome_bad_request/accepted_input_contract`, `runner_unit`, `runner_use_c_worker.duplicate_step_id_rejected`, `failure_boundaries.admission` | Structured `request_failure` names the refusal and location. Unknown filters, unsupported attempt pairs, duplicate IDs and inapplicable fields refuse the whole specimen before children. Known unavailable predictions retain their per-step observations. |
| `already_ran` | host (PWRunnerService) | `runner_unit`, `runner_byoxpc/single_use`, `runner_byoxpc/bad_neighbor_claims` | Shared host admission through distinct services, simultaneous claims and owner-only exit; live two-client file effects and fresh-host acceptance; live attribution of refusals to retirement lag or a foreign holder. |
| `worker_spawn_failed` | host (PWRunnerService) | `runner_outcome_worker_spawn_failed` | Driven via `_test_overrides.worker_executable_path`. |
| `runner_timeout` | host classifier | `runner_outcome_runner_timeout`, `runner_use_c_worker/worker_timeout_ms_honored`, `witness_contract/worker_post_apply_hang_seam`; `runner_unit` / `PolicyTransferTests` | Deliberate empty-plan control plus completed single-write and mixed allowed/denied-write plans. All assert host-kill timeout evidence and both overrides; populated plans independently check file effects and retained step evidence (allow/`succeeded` and deny/`permission_failure` records) and `partial_steps=false`. A policy transfer timeout without an observed worker refusal (the stalled lifecycle fixture) stays here with no EOF receipt. |
| `runner_failed` | host classifier | `runner_unit` / `HostOutcomeClassifierTests`, `CWorkerLifecycleTests`, `WorkerEvidenceTests`, `CWorkerTests`, `PolicyTransferTests`; `witness_contract/worker_termination`, `worker_progress_and_failure`, `worker_sparse_failure`; `runner_c_worker_harness` policy delivery refusals; `WorkerClockTests` | Published worker operation/native-result failure, a clock-setup refusal (operation 12, exit 12) or a local timing refusal of a proceed wait (operation 11, code 14), imprecise published failure, inconsistent/incomplete report, abnormal or unconfirmed disposition, cleanup/wait fault, or host setup/transport failure. Source-cap rejection and simultaneous host EPIPE survive together. A truncated policy delivery is the worker's length refusal (code 13) joined to the host's transfer timeout, with the EOF receipt beside the write counts. Completed slots survive; the underlying cause can remain unknown. |
| `runner_reporting_failed` | host reply boundary | `runner_unit` / `ReplyFailureTests`; `blackbox_e2e/checker_controls` | Constructed invariant rejection preserves original summary, queries, attempts and subprocess observations and withholds comparisons. Repeated encoder failure explicitly reports evidence loss. No result-forcing request override. |
| `validator_spawn_failed` | host classifier (CWorkerOrchestrator) | `witness_contract/validator_spawn_failed_reports_degraded` | Driven via `_test_overrides.validator_executable_path`. `result.ok=false`, `rc=1`; attempts still surfaced as degraded evidence. |
| `validator_no_reply` | host classifier (`verdictReadFailed` / `probeWriteFailed`) | `runner_outcome_validator_no_reply/validator_io_deadline_releases_worker`; `runner_unit` | Real monotonic I/O deadline after one of two verdicts; exact override echo and deadline diagnostic, retained eligible prediction, confirmed validator cleanup and both independently observed worker writes after release. |
| `validator_decode_failure` | host classifier (UTF-8/JSON/structure rejection) | `runner_validator_failure/validator_decode_failure_reports_degraded`, `witness_contract/validator_decode_failure_reports_degraded` | Two valid verdicts arrive in reverse step order before malformed JSON. Asserts partial verdict association, all three completed attempt outcomes and file effects, an explicit gap with its missing reason, and the honored override. |
| `validator_unavailable` | host classifier (unique expected-ID coverage and confirmed clean disposition) | `runner_validator_failure/validator_unavailable_reports_degraded`, `witness_contract/validator_unavailable_reports_degraded` | Checked-in transcript returns 2 of 3 verdicts in reverse step order, then clean EOF. Asserts partial verdict association, all three completed attempt outcomes and file effects, the shortfall diagnostic, the gap's missing reason, and the honored override. |
| `xpc_error` | client (`pw-runner-client`) synthetic reply | `smoke/runner_caller_auth` (real rejected and missing-service calls); `runner_unit` response-default controls | Client-generated failure replies carry the current response schema with empty steps. The caller-auth suite preserves no-effect controls and verifies disposable app copies without altering the selected source app. |
| `xpc_timeout` | client synthetic reply | none (e2e requires a slow specimen plus tight `--timeout-ms`) | Trigger is real (`--timeout-ms 50` plus a long `_test_overrides.worker_post_apply_hang_ms`) but not currently scripted. |
| `xpc_proxy_type_mismatch` | client synthetic reply | none (no realistic trigger) | Fires only if the remote XPC proxy doesn't conform to `PWRunnerProtocol`. Defense-in-depth for a code path that should never run with our matched client/host. |
| `xpc_no_reply` | client synthetic reply | none (no realistic trigger) | Fires only if the XPC reply never arrives but no error fires either. Defense-in-depth. |

## Evidence contract coverage

The opt-in `runner_exec_inheritance/launch_inventory` case records external
descriptor/environment observations at production pre-ready and post-apply
sleep seams, with the contaminated-worker case as a dependency. It retains
optional mapping/port inspection failures and confirms worker cleanup. Its
source-and-timing placement is not a live publication read; it adds no clean
worker, signal-state, resource-limit or universal inheritance guarantee.

The complementary evidence-focused case
`witness_contract/pre_apply_failure_reports_no_policy_verdict` exercises the
real CLI with a populated plan and pre-ready delay/deadline overrides, then
runs an un-overridden positive control. It excludes unsupported apply/compile
and sandbox-cause claims without fixing a replacement outcome name; classifier
tests own that mapping. Its grouped attribution checks remain independent.
The [failure contract](FAILURE-PROPAGATION-CONTRACT.md) assigns publication,
host-driver and CLI coverage separately. Its
[comparison record ownership table](FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
names which case owns which matrix rows and invariants. Consumer validation
uses only one envelope; tests keep their scenario expectations separate from
the reported records.

The opt-in [native extension suite](suites/sandbox_extensions_native/README.md)
establishes file-extension feasibility with independent native calls, target
identity/content observations, issuer lifetime comparisons and allocation
controls. It neither produces nor validates PW outcomes; production extension
and phase integration is outside that case.

The default `witness_contract/extensions`, `extension_boundaries` and
`extension_combinations` cases cover
the integrated native lifecycle and its failure boundaries. Issuance refusal,
missing native APIs, each worker channel rejection and local setup failure
class, issuer death/deadline, consume/release failure and interrupted
publication retain separate native, delivery and access observations. The independent token detector compares actual bytes in memory;
controlled return values establish reporting behavior, not effective permissions.
`witness_contract/extensions_byoxpc` repeats placement and ordinary-phase
controls on an owned external runner, checking independent issuer/worker signing
and entitlement read-backs against registry and envelope provenance. Swift
`ExtensionEvidenceTests` inspect physical host-buffer erasure and withhold
delivery when a controlled host wait cannot establish issuer cleanup, despite
independent test observations of a completed native issuance.

The default `witness_contract/phases` case exercises the public phase grammar
through the signed CLI: an independently observed unlink makes the next path
query unavailable while its attempt reports ENOENT, and a third phase receives
a fresh native query. It checks separate validator PIDs and eleven rejected reader
mutations. The same case drives cumulative collection exhaustion through
`validator_total_timeout_ms` and a real validator stdout byte cutoff, retaining
completed attempts and independent cleanup evidence. No new normalized or
attempt outcome names are introduced by phases.

The opt-in `witness_contract/path_query_observations` case investigates native
path queries independently of PW's planner, using the shipped validator and a
separately signed target. It preserves missing/inaccessible path states and
same-process unlink/recreate observations; it does not change eligibility or
assert general prediction/enforcement agreement. The owning suite describes
its scope and equipment limits.

`runner_unit` / `PhaseProtocolTests` holds all phase boundaries while observing
file effects, injects stale/future release ordinals, kills the worker during a
later collection and checks earlier evidence. The required barrier mutation
control independently removes the worker wait and moves host release early.

The combined-fault matrix rows are shared by `extension_combinations`, the
ordinary-phase `runner_unit` driver control and the Swift comparison tests.
They retain published issuer results beside abnormal exit, withhold delivery
after interrupted validation, and preserve earlier ordinary and native evidence
through same-phase and cross-phase interruption. The ordinary driver combines
timeout, failed termination, unconfirmed reap and rejected late output; its reply
is replayed through Rust assembly and both independent Python readers.

Terminal lifetime is covered by `runner_c_worker_harness/terminal_exit_without_request`
(normal and empty-phase completion), `bare_deny_default`, and
`proceed_without_host_release` (refusal), all with independent reap and no exit
request or cleanup kill. `terminal_erasure` independently checks fixed-capacity
and pre-publication token erasure with rejected shortened/reordered controls.
`CWorkerLifecycleTests` qualifies unseen acknowledgement recovered only at clean
or fatal reap; the latter retains abnormal disposition. The opt-in
`runner_unit/reaped_ack_mutation` pins sensitivity to removed reconciliation.


## Attempt outcome coverage matrix

Host lifecycle observations have separate driver/encoding coverage in
`runner_unit/pwrunner_core_unit_executable`: `CWorkerLifecycleTests` drives
completed reports followed by abnormal exits or cleanup failure using an ABI
fixture and internal OS-call controls; `CWorkerTests` uses the real worker for
deadline followed by voluntary exit and polling-time reaping. `EnvelopeInvariantTests`
protects the encoded reply shape and the absence of the removed wire keys (`drift`, `deny_signal`, the attempt aliases and the comparison's former fields). The pre-apply CLI
witness checks forwarding on both failure and success. The classifier tests and live driver controls agree on the
outcome mapping. Rust correlation tests and the signed CLI retain log
associations separately from execution status and cause.

| outcome | emitted by | primary coverage | notes |
| --- | --- | --- | --- |
| `ok` | C worker (pw-probe-runner) | every smoke / happy-path suite | The attempt ran and the kernel allowed the operation. |
| `read_failed` | C worker (file read_fresh) | `witness_contract/extensions` | Fresh open, bounded read, descriptor identity and close results remain separate. |
| `open_failed` | C worker (file open_read / open_write / create) | `runner_use_c_worker.bare_deny_default`, blackbox file-deny cases, `witness_contract/create_existing_file_preserves_contents` | Covers permission failures (EPERM / EACCES) and ENOENT-class failures, with errno retained. The create CLI case checks a denied write-open alongside an allowed create on existing files, independently preserving bytes and identities. |
| `unlink_failed` | C worker (file unlink) | `runner_c_worker_harness` / `unlink_deny` (+ `unlink_allow` for the success path) | Harness drives `PW_ATTEMPT_FILE_UNLINK` directly: deny-default yields `rc=1` + EPERM/EACCES and the target survives; allow-default removes it. `runner_unit` covers the Codable shape; `witness_contract/comparison_matrix` (rows S19, B3 and B6 plan unlinks; S25 and B5 read the paths S19 and B6 remove) and `run_effects` plan unlinks through the controller. |
| `access_failed` | C worker (file `access(R_OK)`) | `runner_use_c_worker.access_failure_classified` | Errno preserved in `attempt.errno` (typically EPERM/EACCES on a denied path). |
| `lookup_failed` | C worker (mach_lookup bootstrap_look_up) | `blackbox_e2e` / `core_mach_simple` | The kernel return code is preserved in the error message (e.g. `kr=1102` BOOTSTRAP_UNKNOWN_SERVICE). |
| `sysctl_failed` | C worker (`sysctlbyname` read) | `runner_filter_sysctl_name`, `runner_unit` / `CWorkerTests` | EPERM/EACCES are permission-shaped failures without sandbox attribution; ENOENT/ENOMEM are non-policy failures. |
| `exec_failed` | C worker (`posix_spawn` + waitpid) | `runner_use_c_worker.exec_attempt_without_baseline_fails_cleanly`, `runner_exec_dac`, `runner_exec_lifecycle`, `runner_unit` / `CWorkerTests` exec cases | Spawn failure and helper nonzero exit share this outcome. With `child_pid == 0`, EPERM/EACCES are permission-shaped failures whose cause the record does not assign. `runner_exec_dac` verifies ordinary execute-permission EACCES using direct OS controls and exercises native exec-query mapping under independent exec/fork/interpreter policies. The query covers target admission, not every spawn prerequisite. A spawned child establishes spawn success independently of its later nonzero exit; `runner_use_c_worker.exec_attempt_args_and_stderr_round_trip` verifies status/output retention and continuation. `runner_exec_lifecycle` verifies deadline cleanup against OS process observations, retained output, and a subsequent file write. |
| `unsupported` | defensive host result construction for an unimplemented (attempt.kind, attempt.action) | `runner_unit` / `AttemptOutcomeMappingTests` and `DispositionResolverTests` | Constructed unsupported slots cannot claim successful execution. Public requests refuse these pairs before children; `runner_use_c_worker.unsupported_attempt_rejected` and the shared request corpus cover that refusal. |
| `no_completed_result` | host step builder | `witness_contract/pre_apply_failure_reports_no_policy_verdict`; `witness_contract/worker_killed_before_slot_publication`; `witness_contract/worker_attempt_in_flight_at_deadline`; `runner_unit` / `AttemptOutcomeMappingTests` | The outcome for no completed attempt result. It does not say whether the operation started: the pre-apply case dies before any attempt, the in-flight case dies with the native call blocked, and the killed-before-publication case observes the created file independently while the reply withholds the unpublished result. Errno remains null and the comparison carries the lifecycle limitation. `WorkerEvidenceTests` starts a slot without publishing its poisoned payload; source/reason/native-null fields identify the gap. |

## Worker publication and sparse evidence

`witness_contract/worker_progress_and_failure` separates real success/compilation
failure from fixture transport of unfamiliar codes and rich/missing/truncated
text. `worker_sparse_failure` proves real source-cap rejection alongside EPIPE,
closed-input fixture reports and absent reports, failed mapping, and completed
real file effects before self-signal. `runner_unit` / `WorkerEvidenceTests`
exercises C production parameter-allocation/assignment/apply call boundaries,
late publication, zero/unfamiliar records, malformed/unpublished payloads,
missing predictions, post-apply memory-only text, and failed cleanup after a
broken pipe. `runner_abi_layout` checks the worker ABI sizes/offsets; incompatible worker
rejection remains in `runner_c_worker_harness`. These controls do not establish
kernel policy attribution from a signal or synthesize a native call from text.

`failure_boundaries` checks every admission capacity, worker and host-only
(exact/over and UTF-8 multibyte boundaries, capacity before shape, no echo of the
refused string), independent sbpl-check admission (the shipped helper's size
refusal with null compile and import-inventory groups; the helper's native
verdict matrix, stage record and exit-2 paths are `integration/cli.integration`,
its controlled setup/compile/release paths and the capture's status precedence
are `unit/rust.unit`), admission refusal of an
overlong query with the largest admitted probe line measured against the native
cap, control-character round trip through the real validator, and fixture reply
UTF-8/structure/association.
`ValidatorEvidenceTests` covers actual driver kill/wait failures and abnormal exits
after verdicts, byte framing across delayed multibyte writes, bounded rejected
context, and independent I/O plus decode faults. Rust receiver tests use real
subprocess producers for valid oversized JSON, malformed within-cap output,
invalid UTF-8, and multibyte prefix boundaries. The C harness separately checks
the defensive source guard and published failure record; normal CLI oversized
source is rejected by the host before spawn.

## Unfamiliar diagnostic preservation

`witness_contract/unfamiliar_diagnostic_transport` exercises an ABI-compatible
test worker with two open codes, distinct operations/native results/errno/detail
and UTF-8 diagnostic text. It checks absent/unpublished/malformed/incompatible
records, text truncation independent of code recognition, and a real host EPIPE
beside the unfamiliar worker record. The same case checks two validator
diagnostics beside an observed UTF-8 receiver fault and a fixture-supplied allow
record. That record tests preservation of native-result fields; the transcript
producer does not call `sandbox_check`. The real worker's file change is checked
independently.
`DiagnosticTransportTests` supplies direct ABI/validator decoding and Codable
controls. Rust `unfamiliar_diagnostics_survive_*_capture` tests cover runner,
helper and observer JSON receivers. These are transport controls; real producer
attribution remains covered by `witness_contract/worker_progress_and_failure`,
`witness_contract/worker_sparse_failure`, and the `failure_boundaries` cases
listed in the [coverage ownership table](FAILURE-PROPAGATION-CONTRACT.md#coverage-audit-and-acceptance-ownership).

BYOXPC host acquisition is covered by `runner_byoxpc/single_use` and
`runner_byoxpc/bad_neighbor_claims`: attributed refusals, fresh generations,
exactly-once effects, a bounded refusal, and a spaced zero-re-acquisition control.
`unit/rust.unit` covers non-qualifying replies, failed observations, PID reuse,
shared deadlines and preservation of the admitted client's time span.
`runner_byoxpc/default_location` keeps default registry/plist resolution live;
`shell_helpers/byoxpc_setup` checks private registry routing and durable cleanup.

## Worker resource challenge observations

The opt-in `runner_exec_lifecycle/closed_streams_leader_exit` case combines
leader exit with closed output streams and checks whether a same-group
child remains responsive after the completed reply. Independent fixture
cleanup follows the survival observation. `runner_exec_inheritance/closed_worker_stderr`
compares an ordinary direct-worker launch with worker fd 2 closed and observes
child stderr usability. These characterize exercised starting states and lifetime
limits; neither establishes ordinary XPC-host descriptor arrangements.

`runner_unit/host_setup_oracle_sensitivity` measures whether the existing setup
oracle rejects wrong direction/argument and partial-unmap variants. Supplemental
native observations establish the controlled mistakes independently of the old
oracle's accepted receipts. It does not alter the shipped host or upgrade the
original setup controls into a complete protocol or mapping-absence proof.

### Exec collection, requests and leader reap

`ExecObservationTests` and the shared `contract/exec_observation.json` corpus
exercise optional evidence, native integer bounds, branch consistency and
legacy leader-status agreement through Swift, Rust and the independent Python
consumer. A successful signal with unconfirmed reap remains valid; missing
metadata creates no cleanup fact. Ordinary malformed replies degrade and
withhold comparisons. The opt-in `runner_unit/exec_reader_mutations` executes
source defects that bypass publication or invent metadata, requiring failures
at the original independent assertions. Signed `CWorkerTests` and
`runner_exec_lifecycle` separately exercise actual producer/transport paths.
