# Decide where users encounter each PolicyWitness limit

Work through the complete [limits inventory](LIMITS.md) and deliver one proposal for what a caller should find in the app, guide and release reference. The first decision is editorial. For each limit, what question would lead someone to it, what could they decide from the answer, and where would they look? Keep the full technical account in LIMITS. Its five inventory tables will gain a **Where users find it** column for routes a caller can actually use.

Finish the inventory review and present the combined proposal **before the first app change**. Keep proposed card text, guide passages, example edits and column entries in the review record through that decision. A group can finish its research and hand it on while every proposed destination is still open to revision.

## Take one caller question at a time

The worklist assigns each of the current 111 manifest IDs to one group. The groups cross the inventory's five sections so that limits a caller encounters together can be read together. For instance, a refused step ID and a withheld refusal path can affect the same repair. Use the manifest in the checkout under review to pick up new or retired IDs. Refer across groups when the answer depends on another limit. [Manifest](limits.json) · [Interactions between limits](LIMITS.md#interactions-that-matter)

| Caller question | Limit IDs to review together |
| --- | --- |
| Which field do I repair, and how precisely did the refusal locate it? | `step_id`, `attempt_target`, `query_operation`, `query_filter_value`, `probe_plan_label`, `specimen_id`, `request_label`, `request_failure_path_components`, `request_failure_path_component` |
| Will my policy and parameters fit? What can I learn about compilation from a receipt or fallback diagnostic? | `policy_source`, `policy_parameters`, `parameter_key`, `parameter_value`, `compiled_profile`, `helper_source`, `helper_import_depth`, `helper_import_count`, `policy_helper_output` |
| How many actors, phases and actions can I schedule, and where is a visit recorded? | `probe_steps`, `phase_count`, `phase_id`, `actors`, `actor_phases`, `actor_id`, `phase_records`, `phase_publications` |
| How many grants can I issue, transfer, consume and release? Which parts of their handling can I observe? | `actor_issues`, `actor_deliveries`, `actor_handles`, `actor_releases`, `extension_reference`, `extension_issue_target`, `extension_token_storage`, `extension_token_payload`, `authority_slot_bytes`, `authority_setup_trailer`, `authority_setup_cells`, `authority_cleanup_name` |
| What equipment can I require, and how much of its identity and entitlements can I read back? | `actor_required_entitlements`, `actor_entitlement_key`, `equipment_entitlement_bytes`, `equipment_static_bindings`, `equipment_live_inspections`, `equipment_entitlement_records`, `equipment_inventory_bytes`, `equipment_diagnostic_bytes`, `equipment_metadata_bytes`, `equipment_signing_text`, `equipment_path`, `equipment_error_domain` |
| How much did the operation read, and what details of the attempt survive? | `fresh_read_bytes`, `sysctl_read_bytes`, `worker_diagnostic`, `observed_path`, `attempt_error` |
| What arguments fit an exec, how long can it run, and what child evidence survives? | `exec_arguments`, `exec_argument`, `exec_child_wait`, `exec_attempt_budget`, `exec_reap_grace`, `exec_stream` |
| How long will the client wait for a runner, an execution reply or removal? What should I do after it returns? | `client_rpc_wait`, `runner_verify_wait`, `reservation_lease`, `reservation_rpc_wait`, `reservation_attempts`, `reservation_retry_delay`, `host_exit_delay`, `byoxpc_throttle_interval`, `runner_remove_teardown_wait`, `runner_remove_poll_interval` |
| Which part of worker setup, an actor schedule or cleanup reached its deadline? | `worker_policy_transfer`, `worker_ready_wait`, `worker_sentinel_wait`, `worker_exit_grace`, `worker_proceed_wait`, `actor_setup_allowance`, `actor_execution_allowance`, `actor_release_wait`, `actor_exchange_allowance`, `actor_lifetime_cutoff`, `actor_termination_wait` |
| Why did prediction collection end, and which phases can still run? | `phase_collection_wait`, `actor_collection_allowance`, `validator_io_wait`, `validator_exit_grace`, `validator_release_margin` |
| Which validator records can I still use after a size or parsing failure? | `validator_query_payload`, `validator_fault_context`, `validator_reply_frame`, `validator_records_per_query`, `validator_reply_bytes_per_query`, `validator_reply_step_id`, `validator_reply_operation`, `validator_reply_filter_type`, `validator_reply_filter_value`, `validator_reply_outcome`, `validator_reply_error` |
| Which test setting could change this run, and what value took effect? | `test_override_path`, `worker_timeout_override_floor`, `validator_io_override_floor`, `validator_collection_override_floor`, `worker_fixture_delay` |
| Which reply or error reached the client, and how much of it can I interpret? | `controller_output`, `client_reply_retention`, `reservation_control_bytes`, `client_error_message`, `client_error_domain`, `porcelain_frame_bytes`, `porcelain_decoded_storage_bytes`, `porcelain_nesting` |

## Record the decisions

Carry the [decision worksheet](../records/limits-review/decisions.tsv) across sessions, with one header row and one row per ID. Keep the agreed placements, the manifest revision and the identity of any app inspected in the [review notes](../records/limits-review/README.md). Use these columns, keeping the ID first so coverage is easy to check.

| Column | What to record |
| --- | --- |
| Limit ID | The exact manifest ID, even when several rows share a destination. |
| Caller question and starting point | A decision and a spelling or observation available to the caller, such as `--timeout-ms`, `content_hex`, or a missing path. For an internal bound, say who could encounter its consequence. |
| Current route and support | Where the reader can find the answer today. Name the passage, invocation or result field. Follow the row's source and checks to establish what they support. |
| Proposed disposition and destination | Choose by hand. Keep an existing route, propose a specific addition or revision, retain the inventory as the sole destination, or defer an identified question. Name the exact card, guide passage, specimen edit, result field or release reference. Add a second route when it serves a different use. |
| Reason and verification | State what the reader can decide there. Give an input, observation or reading task that distinguishes a useful answer from a plausible wrong one. For a deferral, name the evidence or decision needed. |

Read the row's counting rule, scope, control and consequence before choosing. A flag may change one wait while others keep running. An output cap may leave a usable prefix, withhold a whole field, or make a reply unusable. A derived storage size can be fully accounted for by the reference. Use the [coverage notes](LIMITS.md#grounding-and-coverage) when deciding whether a boundary can be demonstrated with the shipped app.

Try the current route from the caller's starting point. A guide passage can teach an inference, a help entry can give the default beside its flag, and a result can explain a refusal at the point of use. An example can supply a valid starting specimen for a one-field edit. Use `test-input` when a demonstration depends on an intervention available there. Distinguish what a terminal user can discover from what a program can read in the envelope. [Interface and help owners](../controller/interface/README.md) · [Worked guide cases](guide/README.md#worked-cases) · [Caller responsibilities](REQUIREMENTS.md)

Use these examples to calibrate subsequent decisions. The worksheet records which destinations the team has agreed to propose.

- **Repair a refusal.** Change one ordinary `step_id` in the emitted example from 63 to 64 ASCII bytes. Could a reader of `bad_request` find the field, actual count, maximum and unit in `data.runner_result.admission_failure`, see that no step ran and repair the specimen? Compare what the existing guide's duplicate-ID case teaches before proposing another passage. [Repairing a refused specimen](PolicyWitness.md#repairing-a-refused-specimen)
- **Interpret a successful read.** Give `read_fresh` two 65-byte files with identical first 64 bytes and different last bytes. Would the reader know why matching `content_hex` leaves whole-file equality open? Consider adding the comparison where the guide first reads a known file. [First specimen](PolicyWitness.md#run-your-first-specimen)
- **Decide whether to retry.** Read the same `--timeout-ms` spelling on `run` and `runner verify`, which have different defaults. Try a help lookup for the applicable wait and use the guide's delayed-create case for the separate decision about resubmission. Compare the nominal `validator_release_margin`, which has no expiry of its own. The worksheet can assign that row to the inventory alone. [Execution budgets](LIMITS.md#execution-budgets) · [Retry case](PolicyWitness.md#deciding-whether-to-repeat-a-run)

## Review one combined proposal

Reconcile the worksheet with the current manifest at handoff. From the repository root the following comparison should produce no differences. Sorting both lists preserves duplicate IDs. Check the manifest diff from the recorded revision for changes to existing rows. Review each added or changed limit and resolve all open or blank dispositions before closing the list.

```sh
diff -u <(jq -r '.limits[].id' docs/limits.json | LC_ALL=C sort) \
        <(tail -n +2 records/limits-review/decisions.tsv | cut -f1 | LC_ALL=C sort)
```

With every ID accounted for, write `records/limits-review/proposal.md`. Turn the worksheet around and read it by destination. Give one entry per proposed change with the limit IDs it serves, the caller's starting point, the proposed wording, invocation or demonstration, its owner and the observation that would establish it works. Show the resulting help cards and guide passages together in draft. Count the IDs with an adequate existing route, proposed work, inventory alone and a reasoned deferral. Count shared changes once when describing the work.

Review the whole mix for repeated explanations, overloaded cards and decisions that still have no path from the app or a saved result. Include a way for someone with the release to find its **complete** inventory. Compare a reference to the tagged inventory with any proposed offline delivery and say what each would require. For guide edits, preserve the standalone reading path. For help proposals, identify the governing definition and any new ability the card renderer would need. Reconcile shared work with the [CLI transition](../CLI-TRANSITION-PLAN.md#find-the-applicable-release-contract-during-normal-use) and the [guide plan](guide/USER-GUIDE-PLAN.md).

**Stop here for the scope decision.** Present the complete proposal, including what the team would keep, combine, defer or drop. Select the changes and their release placement together. Implementation starts after that review.

## Publish the selected routes

Keep the routing decision with each limit in [limits.json](limits.json). Extend the [limits generator](generate_limits.py) to validate that metadata and render **Where users find it** in each of the five inventory tables. Use a specific destination a reader can follow, such as a guide heading, a help invocation or a result field with its containing path. Use **Inventory only** when the reference is the sole route. Keep drafts and deferred additions in the review record. Enter a new destination in the column when it works in the same revision. Preserve each row's counting rule, consequence, control and supporting checks.

Regenerate LIMITS through its owner, run `tests/lib/python.sh docs/generate_limits.py --check` and exercise `source_drift/limits_documentation`. Check that every row has a disposition and that every advertised route resolves. Then start at the user's actual field, flag or outcome on the staged app and try the decision promised by each selected change. Run changed guide examples with their fixtures and compare the observed refusal or effect with independent expectations. Test the route to the full reference from the release materials. [Generator and guide workflow](AGENTS.md#editing-limits-and-the-published-guide) · [Interface verification](../tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards)
