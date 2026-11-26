# A first arrangement of the limits by reader question

Each of the 111 limit IDs appears once under the question it most helps answer. The tables suggest prose to read together across requests, results and implementation details. The worksheet still records each destination and release decision. [Limits review plan](../../docs/LIMITS-SURFACING-PLAN.md#review-one-combined-proposal)

## Which part of my specimen do I repair?

Start with the refusal the caller has and end at the edit in the saved specimen. A single path or name can appear in several roles, each with its own rule. [Refusal repair](../../docs/PolicyWitness.md#repairing-a-refused-specimen) · [Admission fields](../../docs/LIMITS.md#specimen-admission)

| Answer to give | Limits to read together |
| --- | --- |
| **Names and references.** Use the index to find the step, phase or actor. When a transfer to Alice becomes a transfer to Bob, the recipient and the actor that consumes the delivery must agree. A name can fit its byte allowance and still refer to the wrong owner. | `step_id`, `phase_id`, `actor_id`, `extension_reference` |
| **One path in several fields.** Give the guide’s retargeting edit a 512-byte absolute path. It fits the extension issue field and exceeds both the read target and the query filter. The first refusal names `target`. Shorten the read targets and the next refusal names `sandbox_check.filter.value`. Each is a 0.3.9 lookup. For an operation or action label, check its supported spelling as well as its byte length. | `attempt_target`, `query_operation`, `query_filter_value`, `probe_plan_label`, `extension_issue_target` |
| **Policy text, maps and requirements.** Count expanded source bytes and parameter entries per policy, and required entitlements per actor. The refusal’s unit distinguishes a list with too many entries from a single key or value that is too long. | `policy_source`, `policy_parameters`, `parameter_key`, `parameter_value`, `actor_required_entitlements`, `actor_entitlement_key` |
| **Exec and executable overrides.** A refusal on `args` can name the supplied argument count or one argument’s byte length. The target supplies `argv[0]`. A refusal on an executable override instead identifies a worker role or validator path that the caller can recover from the specimen or invocation. | `exec_arguments`, `exec_argument`, `test_override_path` |
| **An incomplete refusal location.** A null `request_failure.path` means the path was withheld. An empty array identifies the root. Use the reported field, index or retained parameter key and the saved input. An omitted label or `<admission_refused>` can also be a consequence of bounding the echo. | `specimen_id`, `request_label`, `request_failure_path_components`, `request_failure_path_component` |

## Who shares this allowance, and when does it start over?

Name the unit that owns the allowance. Then change one thing a caller might expect to give them more room, such as adding an actor or starting another phase. [Admission counts](../../docs/LIMITS.md#specimen-admission) · [Shared budgets](../../docs/LIMITS.md#interactions-that-matter)

| Answer to give | Limits to read together |
| --- | --- |
| **Phases and actions.** Eight actors share up to sixteen phases in the actor form. Adding a second actor to a sixteen-phase plan leaves room for zero more phases. Both forms share one 256-action limit across the specimen. | `probe_steps`, `phase_count`, `actors`, `actor_phases` |
| **Grants.** Count issue, transfer, consume and release actions across the specimen. Sending a token to two recipients uses two transfers. Having room for another release still requires a handle eligible for release. | `actor_issues`, `actor_deliveries`, `actor_handles`, `actor_releases` |
| **Time shared across work.** A later exec in the same worker spends what remains of that worker’s allowance. Prediction collection draws from one pool across phases, including visits to different actors. An exhausted pool can leave a later phase without a prediction while its attempt still runs. | `exec_attempt_budget`, `phase_collection_wait`, `actor_collection_allowance` |
| **Validator records.** Two submitted queries give their phase collector room for four records in total. Duplicates can consume the allowance. To find which queries received usable answers, inspect record association afterward. | `validator_records_per_query` |

## Which wait ended, and what could still run?

Follow an event from the component that waited to the evidence it could publish. A requested delay, an effective deadline, a timeout and confirmation of exit answer different questions. These comparisons feed the single 0.3.9 timing section. [Execution budgets](../../docs/LIMITS.md#execution-budgets) · [Timing work](../../docs/guide/USER-GUIDE-PLAN.md#timing-in-039)

| Answer to give | Limits to read together |
| --- | --- |
| **Start-up.** Compare the policy bytes the host wrote with the bytes the worker received. A missing readiness hint leaves later publications worth reading. An actor whose setup allowance expired may subsequently publish that it applied its policy. | `worker_policy_transfer`, `worker_ready_wait`, `actor_setup_allowance` |
| **Waiting for progress.** The ordinary host waits for publication. In an actor schedule, the host can be waiting for a visit, a worker for release, or a transfer participant for acknowledgement. Use the wait’s owner and start event to read its outcome. Parking counts toward the actor lifetime cutoff even before that visit’s release wait starts. | `worker_sentinel_wait`, `worker_proceed_wait`, `actor_execution_allowance`, `actor_release_wait`, `actor_exchange_allowance`, `actor_lifetime_cutoff` |
| **Collection, exit and cleanup.** An exec leader can exit while a descendant holds an output pipe open. Validator I/O can end before the validator is reaped. For a worker whose exit grace expired, read the termination request and the subsequent reap observation to see how it ended. A later cleanup reap cannot retroactively satisfy an actor’s timed-out termination dependency. | `exec_child_wait`, `exec_reap_grace`, `worker_exit_grace`, `actor_termination_wait`, `validator_io_wait`, `validator_exit_grace` |
| **Requested versus effective time.** A zero worker timeout selects a 50 ms ordinary publication budget. Remaining collection time can shorten a validator’s effective I/O wait. For a worker delay flag, first check that its value was accepted, then whether the worker reached the delay point. The 0.4.0 test-command review owns the flag wording. | `worker_timeout_override_floor`, `validator_io_override_floor`, `validator_collection_override_floor`, `worker_fixture_delay` |

## Can I retry or clean up now?

Use the last established state to decide what the caller can safely repeat, retain or remove. Elapsed time alone cannot settle whether a specimen was invoked or a named resource is still owned. [Retrying a run](../../docs/PolicyWitness.md#deciding-whether-to-repeat-a-run) · [Removal and recovery](../../docs/RESPONSE.md#contract-installation-commands-recovery)

| Answer to give | Limits to read together |
| --- | --- |
| **Submission.** A client can use up its reservation attempts with time left, and a reservation lease applies to an unused reservation. At a timeout or `control_too_large`, read the stage and `submission.state`. After invocation, work may continue. `run` and `runner verify` also start with different default waits. | `client_rpc_wait`, `runner_verify_wait`, `reservation_lease`, `reservation_rpc_wait`, `reservation_attempts`, `reservation_retry_delay`, `reservation_control_bytes` |
| **A fresh host.** Reply handoff, client receipt, retirement of the old host and launch of its successor are distinct observations. The host schedules exit 50 ms after handing off an execution reply. The client observes receipt independently. Disconnection of an unused reservation’s owner can also start retirement. The installed service’s launchd throttle cannot establish when a reply arrived. | `host_exit_delay`, `byoxpc_throttle_interval` |
| **Cleanup.** After `runner remove`, read `cleanup_retained` and the final service and plist observations before discarding staging. For a retained shared-memory name, use the creation and unlink records, host PID and session nonce to establish current ownership before acting. | `authority_cleanup_name`, `runner_remove_teardown_wait`, `runner_remove_poll_interval` |

## Who observed this, and what does it establish?

Name the observer, the object and the moment of observation. This lets readers explain an unavailable value and decide which claim they can pass on. [Native operations](../../docs/REQUEST.md#native-operations) · [Reading a result](../../docs/PolicyWitness.md#read-a-result)

| Answer to give | Limits to read together |
| --- | --- |
| **Policy compilation and application.** A fallback helper can stop before compilation or stop listing imports while the compiler follows its own rules. A worker’s optional compiled-profile receipt concerns that worker’s applied policy. A missing receipt still leaves its application evidence to read. The import-helper follow-up owns the open questions about its walk and output. | `compiled_profile`, `helper_source`, `helper_import_depth`, `helper_import_count` |
| **Equipment identity.** Follow the packaged or override binding to the live inspection of the actor. A single static binding can serve several actors with distinct live observations. Identify who supplied the signing identifier, Team ID, path or entitlement representation before interpreting its limit. The signing review retains those distinctions. | `equipment_entitlement_bytes`, `equipment_static_bindings`, `equipment_live_inspections`, `equipment_entitlement_records`, `equipment_signing_text`, `equipment_path` |
| **The object that exceeded a size check.** At `inventory_read`, the host was reading a complete sealed file. Equipment metadata is accounted for on each binding or live record. The entitlement plist has its own bound. A refused inventory file and an ineligible equipment record occur at different stages of the run. | `equipment_inventory_bytes`, `equipment_metadata_bytes` |
| **Native attempts.** Two `read_fresh` results can have identical 64-byte prefixes and different underlying files. A sysctl read discards the value and returned length, so `sysctl_failed` alone leaves the required size unknown. For a path or error, identify a worker descriptor observation, a later host lookup, or a host-supplied explanation by its source. | `fresh_read_bytes`, `sysctl_read_bytes`, `observed_path`, `attempt_error` |
| **Grant custody and setup.** A nonnull native issue return can leave custody unestablished. Read the host custody status. An authority operation can publish a cleanup result independently of the final setup decision. Use the individual operation when the decision reads `not_observed`. | `extension_token_payload`, `authority_setup_cells` |

## What survived the cutoff, and can I tell what was lost?

Start at the first reader that shortened, withheld or rejected something. Name the evidence it retained and whether it recorded the loss. The original object, the bytes received and the result another reader can interpret can all differ. [Transport and retention](../../docs/LIMITS.md#queries-and-transport) · [Evidence capture](../../docs/LIMITS.md#evidence-capture)

| Answer to give | Limits to read together |
| --- | --- |
| **Diagnostic text and error identity.** Equal-length worker diagnostics can have `complete` and `truncated` statuses. The client marks shortening of its message and native domain independently. The 0.3.9 equipment review asks what a reader can establish when an exact-fit message and a shortened one look alike, or two native domains retain the same prefix and code. | `equipment_diagnostic_bytes`, `equipment_error_domain`, `worker_diagnostic`, `client_error_message`, `client_error_domain` |
| **Output at successive readers.** A child stream can retain a marked prefix. A truncated helper stdout cannot supply a complete helper result. A truncated host reply leaves client capture evidence. If the controller truncates the client’s stdout, submission is unknown. Read receipt counts at the component that applied the bound. | `policy_helper_output`, `exec_stream`, `controller_output`, `client_reply_retention` |
| **Lines and frames.** The validator can drain an overlong input line and resume with the next query. On the reply path a collection cutoff can discard a partial line before decoding, while a complete malformed frame can leave a diagnostic prefix. In both reply cases, inspect earlier accepted verdicts. The 0.4.0 `byte_limit` and rejected-frame work uses this comparison. | `validator_query_payload`, `validator_fault_context`, `validator_reply_frame`, `validator_reply_bytes_per_query` |
| **Contents of a validator record.** An overlong field can cause rejection of the whole record. A record with an in-bounds but unexpected operation or filter can survive decoding and then fail association with the step. Read rejection, association and outcome as separate decisions. | `validator_reply_step_id`, `validator_reply_operation`, `validator_reply_filter_type`, `validator_reply_filter_value`, `validator_reply_outcome`, `validator_reply_error` |
| **The binary reply.** The receiver checks encoded frame length, charges typed collection slots and data against a decoded-storage allowance, and checks nesting. A compact frame can exhaust logical storage. A decoding error alone leaves the reason to be read from the diagnostic. | `porcelain_frame_bytes`, `porcelain_decoded_storage_bytes`, `porcelain_nesting` |

## Which quantities does PW provide or check for me?

Keep the caller’s question even if a number turns out to describe a layout or a relationship between defaults. Where the same structure also enforces a real boundary, say exactly which boundary the worker checks. [Grounding for the limits](../../docs/LIMITS.md#grounding-and-coverage) · [Shared storage](../../docs/FOOTPRINT.md#shared-backing)

| Answer to give | Limits to read together |
| --- | --- |
| **Phase storage.** PW reserves sixteen 32-byte records in each worker header. The worker checks the phase count in its header. For a specimen author the usable phase count comes from admission, so adding another worker provides no extra phase capacity for that schedule. | `phase_records`, `phase_publications` |
| **Authority storage.** PW allocates the token slots and setup trailer. The token buffer includes its terminating NUL, which leaves 16,383 payload bytes. Count the declared issues and transfers when planning a specimen. Inspect the setup publications to learn what happened. | `extension_token_storage`, `authority_slot_bytes`, `authority_setup_trailer` |
| **The release margin.** The default-budget test allows five seconds for host work when checking that the worker release wait exceeds validator I/O plus exit grace and margin. Nothing expires at that margin. A reader investigating a timeout needs the component that actually stopped. | `validator_release_margin` |

## Try the arrangement on a saved result

- A file path appears in a capacity refusal. Start with the field to repair. After the repaired run, use the observation question to distinguish the requested path, the worker’s descriptor path and the host’s later lookup.
- A phase has an attempt and no prediction. Check which phases shared the collection pool, then read the collector’s stop reason and surviving complete records. Each answer accounts for a different part of the same result.
- A client timed out. Identify whose wait ended, then find the submission state before deciding whether to repeat an operation with side effects. When stdout was truncated and submission is unknown, keep that uncertainty in the answer.
