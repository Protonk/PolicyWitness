# Proposed destinations for the limits inventory

This draft collects the 111 reviewed rows by the place a reader would encounter them. The worksheet assigns proposed work to 82 IDs, including the 29 served by one 0.3.9 guide section on timing. The technical inventory is the proposed sole destination for 20, including the best-effort host retirement delay. Nine have a named investigation with the destination decision still open. No ID was closed solely on an existing user route outside the inventory. The tables count each ID at its primary destination. Shared entries and cross-references describe one change even when several IDs lead there. Release placement is a separate decision.

## Request lookups on `help run`

### Seven release outputs

These are the literal stdout expectations for the seven reviewed keys on a v0.3.9 build. Each block ends with a newline. Bare `help run` lists these keys separately from its options. An indexed alias prints the canonical key on the first line. The two 511-byte fields share a repair exercise and have separate entries, contract nodes, limit IDs and links.

```text
token_ref
  An issue must assign a new token reference. A transfer must name a previously assigned token that the active actor owns. Omit this field for other operations.
  Each reference or recipient ID must be nonempty, NUL-free and at most 63 UTF-8 bytes.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-extensions-operation-token_ref
```

```text
delivery_ref
  A transfer must assign a new delivery reference. A consume must name a previously assigned delivery that the active recipient owns. Omit this field for other operations.
  Each reference or recipient ID must be nonempty, NUL-free and at most 63 UTF-8 bytes.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-extensions-operation-delivery_ref
```

```text
handle_ref
  A consume must assign a new handle reference. A release must name a previously assigned handle that the active actor owns. Omit this field for other operations.
  Each reference or recipient ID must be nonempty, NUL-free and at most 63 UTF-8 bytes.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-extensions-operation-handle_ref
```

```text
recipient
  A transfer must name a declared actor as its recipient. The active actor can name itself. Omit this field for other operations.
  Each reference or recipient ID must be nonempty, NUL-free and at most 63 UTF-8 bytes.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-extensions-operation-recipient
```

```text
extension.target
  An issue requires a NUL-free absolute file or directory path of at most 1,023 UTF-8 bytes. The exact submitted bytes reach native issuance. Omit this field for other operations.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-extensions-operation-target
```

```text
target
  An attempt requires a non-null, NUL-free target string of at most 511 UTF-8 bytes. Exec requires an absolute path. Other admitted attempts use the target according to their native operation.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-probes-attempt-target
```

```text
sandbox_check.filter.value
  When sandbox_check.filter.kind is none, omit the value or set it to null. Every other supported kind requires a NUL-free string that is nonempty after whitespace trimming. The limit of 511 UTF-8 bytes applies to the original string, which is passed through unchanged.
  https://github.com/Protonk/PolicyWitness/blob/v0.3.9/docs/REQUEST.md#contract-probes-filter-value
```

### What the build projects

Use one typed registration per reviewed field. It selects a canonical spelling, the field node, applicable limit and any shared statement needed to read the field alone. For the four extension references, select the reference rule on the extension operation subject. The other three fields carry their bounds in their own statements. Resolve the spelling and its aliases through the lookup declarations. Use the same registrations for selection, the bare list and the interface inventory. The samples above are independent expectations for the CLI corpus. [Attempt and query fields](../../docs/contract/12-probes.surface.md) · [Extension fields and context](../../docs/contract/14-extensions.surface.md) · [Interface inventory](../../controller/interface/README.md)

Read paragraphs from the contract tree. Render inline code as its literal characters and a limit span as the manifest's rendered value and unit, once in place. Emit UTF-8 text, two spaces before each paragraph and link, one LF per line and no terminal-dependent wrapping. Keep the full field paragraph, including its conditions. The link opens the complete REQUEST field with its type and structured presence rules. Fail the export on a missing node, unsupported markup, unmatched limit or unresolved destination. If a paragraph depends on context, edit the owning statement and regenerate REQUEST so both readers get the same wording. The result and custody facts needed to interpret a zero reported native token length belong in the full account until an entry can cite them together. [Contract reader and presentation map](../../docs/contract/README.md)

Use a checked-in publication base for the repository and the tag from the derived release build contract. The presentation map supplies the document and field anchor. Keep the inventory reference independent of the release revision and bind the URL when building the executable. Include the publication base and projection inputs in freshness, build identity and stale-export checks. For development builds use the commit only when the referenced inputs and destination match it, otherwise print the working-tree path and anchor labelled as local. The executable only prints the reference and needs neither Git nor network access. Check the destination against the tagged bytes during staging. [Build identity](../../docs/build_contract.py) · [Release publication](../../docs/SIGNING.md#release-procedure)

Prove the dependency in a disposable build. Hold the card and renderer fixed. Change one field statement and check its canonical and indexed outputs against the changed REQUEST passage. Change a bound at its owner and check the real admission boundary and its displayed value. Change one governed refusal spelling and check the emitted field, lookup and inventory together, including the old spelling and an unaffected sibling. An editorial change should leave admission behavior intact. Run the seven literal cases independently on the extracted release app and follow the path-refusal exercise below.

### Which spellings resolve

Seven is the editorial review boundary for the extension example. Separately, recognize the full vocabulary that capacity admission can emit in `admission_failure.field`. Give each literal or pattern a structured declaration. Use it for the producer's spelling and the controller's matcher, and join the applicable limits and optional reviewed entry to it. Generate the inventory's human-readable refusal spellings from those declarations, keeping units, indices and other accompanying fields separate. The current manifest contains prose and abbreviations such as `.recipient`. Parsing that display text would lose the owner. A capacity spelling can belong to multiple rows, as `args` does for item count and byte length and `phases` does for the two specimen forms. [Current inventory](../../docs/LIMITS.md#specimen-admission) · [Capacity manifest](../../docs/limits.json)

Match the whole argument. Register compact discovery keys explicitly. Bind the indexed extension fields at `phases.<index>.actions.<index>.extension.<field>`. An index matches the producer's nonnegative decimal spelling, including zero. Only an index slot permits index substitution. Keep a dynamic dictionary key as data in its declared position, including any punctuation the producer can emit. Reserve literal `target` for the attempt. Reject conflicting entry registrations at build time. A shared capacity spelling with several possible limits is still recognizable from the field alone. The actual refusal's unit and context select its bound.

Use these outcomes on the staged app. All failed lookups exit 2 with empty stdout. Keep diagnostics bounded and independent of untrusted operand text.

- A reviewed key or registered alias selects its exact entry at exit 0. Compare `phases.2.actions.1.extension.target` with `extension.target`, then with the different entry for `target`.
- A recognized admission spelling without a reviewed entry writes `No help entry for this admission field. See help run for available entries.` to stderr, followed by the release link to `docs/LIMITS.md#specimen-admission`. Exercise `step_id`, `sandbox_check.operation`, `args` and an indexed entitlement key. Use the reported maximum, unit and index to interpret the original refusal.
- An unrecognized single key writes `Unknown help run key. See help run for available entries.` A malformed index or unrelated prefix cannot reach a field by its suffix. This diagnostic makes a claim only about help's vocabulary. Extra operands and non-UTF-8 input print the usage diagnostic for `help run [<key>]`. `help result junk` still prints the whole result card at exit 0.

Check both directions. Every capacity refusal producer must use a declared spelling, and each of the 28 manifest admission rows must resolve to its declarations. Submit an oversized actor ID in a phase's termination dependency. Copy the emitted `phases.1.after_termination.actor_id` into help and expect the recognized-field diagnostic. Also exercise both units for `args`, an indexed extension alias, an unreviewed sibling and a misspelling. Use constructed cases for the remaining pattern and argument boundaries, including a dictionary key containing a dot. Keep structured request errors in `request_failure.path` distinct from this vocabulary. Adding a recognized spelling extends diagnostics automatically. Advertising an entry requires its own wording and reader review. [Admission producer](../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift) · [Actor capacity checks](../../runner/Sources/PWRunnerCore/ActorPlan.swift)

### Reader exercises by limit

| Limit IDs | Reader’s entry point | Proposed text or demonstration and reader check |
| --- | --- | --- |
| `attempt_target`, `query_operation`, `query_filter_value` | `target`, `sandbox_check.operation`, `sandbox_check.filter.value` | The attempt target and query filter value each allow 511 UTF-8 bytes. Use the field and step index to look up and shorten the correct operand when they name different paths. In 0.3.9 the operation name reaches the recognized-field diagnostic. A later focused entry can give its 127-byte bound. |
| `probe_plan_label` | `sandbox_check.filter.kind`, `attempt.kind`, `attempt.action` | Put “up to 127 UTF-8 bytes” beside the supported spellings. Compare a short unknown spelling with a 128-byte label and identify which refusal each receives. |
| `policy_source` | `policy.sbpl_source` or its actor-policy field | “The expanded source allows 262,143 UTF-8 bytes per policy. This count excludes imported file contents.” Test a source near the ceiling with an augment and identify which bytes count. |
| `policy_parameters`, `parameter_key`, `parameter_value` | `policy.params`, `key` or `value`, including actor-qualified fields | “Up to 1,024 entries per policy, 127 UTF-8 bytes per key and 383 per value.” Locate an oversized key using the saved map and the reported size. For an overlong value check whether the refusal retained `parameter_key`. |
| `probe_steps`, `phase_count`, `actors`, `actor_phases` | `phases` or `actors` | “An ordinary specimen can have 8 phases. An actor-form specimen can have up to 16 phases total across up to 8 actors. One actor can use all 16. Both forms allow 256 actions across the specimen.” Try adding an actor to a 16-phase specimen and see which limit still binds. |
| `actor_id`, `phase_id` | `actors[].actor_id`, `phases[].actor_id` and `phase_id` | Explain actor references and phase identity in adjacent lookups. Both names are nonempty, NUL-free and at most 63 UTF-8 bytes. Rename an actor and repair its phase references. Find an oversized phase ID by the refusal index. |
| `actor_issues`, `actor_deliveries`, `actor_handles`, `actor_releases` | `extension.issue`, `.transfer`, `.consume`, `.release` | “The specimen allows 32 issues, 64 transfers, 64 consumes and 64 releases. Each uses one action.” Check that a self-transfer counts and that a repeated release can be refused with capacity to spare. Use the existing extension example for the 0.3.9 entry. |
| `extension_reference` | `token_ref`, `delivery_ref`, `handle_ref`, `recipient`, or the indexed refusal spelling | List the four names on `help run`. Explain which action assigns or uses each name and the 63 UTF-8 byte ceiling. For example, “`delivery_ref` names a transfer for its recipient’s later consume.” Move a transfer to Bob and ask which consume must move with it. Compare field and indexed lookups on the staged app. |
| `extension_issue_target` | `extension.target` or its indexed refusal spelling | “An issue target is an absolute path of up to 1,023 UTF-8 bytes. A read target allows 511.” In 0.3.9, put a 512-byte path in all three fields. Look up `target`, shorten every read target, then look up `sandbox_check.filter.value`. Starting from the valid example, change only the issue path to 1,024 bytes and compare its indexed lookup with `help run extension.target`. |
| `actor_required_entitlements`, `actor_entitlement_key` | `required_entitlements`, its indexed list or a key refusal | “Each actor can require 64 distinct boolean-true grants. Each key is nonempty, NUL-free and at most 255 UTF-8 bytes.” Use the index to choose between shortening the list and repairing one key. |
| `exec_arguments`, `exec_argument` | `attempt.args` or the `args` refusal field | “Up to 15 supplied arguments, 127 UTF-8 bytes each. The target supplies argv[0].” Compare refusal units `items` and `utf8_bytes`, then locate the argument in the saved step. |

## Reading a saved result with `help result`

In 0.4.0, have the result card and “Read a result” advertise `help result <field-or-status>`. The 0.3.9 result card carries one reference to the guide heading “Which wait ended?”. Use paths qualified by their record when the same field name has several owners. Select entry text and release links from the result contract and build definitions. Check the literal spelling from a saved envelope against the CLI corpus, then ask the reader to make the decision in the same row. [Result contract](../../docs/RESPONSE.md) · [Interface checks](../../tests/CHANGE-VERIFICATION.md#interface-definitions-and-help-cards)

For future result lookups, advertise `actors.equipment.execution.status` with array positions omitted and accept the quoted documentation spelling `help result 'actors[].equipment.execution.status'` as an alias. Advertise `data.runner_result.specimen_id` and accept `help result '<admission_refused>'`. The shell removes the quotes before dispatch. `byte_limit`, `attempt_limit` and `inventory_read` are usable as unique literal keys. An ambiguous `path` should list `equipment_inventory.path`, `equipment_bindings.path` and `actors.equipment.execution.path` on stderr. Check advertised invocations in zsh as well as the argument-vector corpus. These result examples describe the later result lookup.

| Limit IDs | Reader’s entry point | Proposed text or demonstration and reader check |
| --- | --- | --- |
| `specimen_id`, `request_label` | `<admission_refused>` | “The host substituted this marker for an unsafe specimen ID. Recover the original ID from the saved request.” Link the echo rule for omitted `run_kind` and a `policy.format` echoed as `unknown`. Keep the full label list and 63-byte label ceiling in LIMITS. Compare an oversized specimen ID with an unrelated refusal. |
| `worker_diagnostic` | `worker_evidence.diagnostic.status` | “The worker can retain 4,095 bytes of primary diagnostic. Read `complete` or `truncated` alongside `length`.” Give the reader two equal-length diagnostics with different statuses. |
| `attempt_error` | `attempt.error` | Start with `result_source`. “A completed worker slot retains up to 255 bytes. A synthetic attempt can carry the host’s explanation.” Compare `outcome`, `rc` and any errno for each source. |
| `sysctl_read_bytes` | `sysctl_failed` | “The worker requests the value once with a 4,096-byte buffer. It discards the value and the returned length.” Ask whether the reported failure establishes the required capacity. |
| `extension_token_payload` | `issued_uncustodied` or `custody_unavailable` | “A publishable token contains 1–16,383 bytes. A nonnull native return with `token_length: 0` leaves its length unresolved.” Compare an empty return with an oversized return and read host custody separately. |
| `authority_cleanup_name` | `cleanup_reference`, `unresolved_manual`, `authority_cleanup_reference` | The first two selectors open recovery. Look up `shm_open` and `shm_unlink`, retain the name, host PID and session nonce, and establish current ownership before acting. The host-generated name allows 31 UTF-8 bytes. The third selector opens validation. Compare an overlong name with inconsistent operation records that raise the same diagnostic. Advertise the lookup in “Read a result.” |
| `authority_setup_cells` | `authority_setup.workers[].operations` or `.publication` | “Each of the 16 slots can publish one operation. An observed cleanup result can survive a `not_observed` setup decision.” Find the published operation and identify which other slots have no native result. |
| `equipment_static_bindings` | `equipment_bindings` | “Use `preparation_failure.binding_ref` as a zero-based index. Read `role`, `source` and `reason`.” With a packaged binding and an override present, locate the refused row among the four possible rows. |
| `equipment_live_inspections` | `actors[].equipment.execution.status` | “The host inspects each setup-usable actor before activation, up to eight.” At `mismatched` or `inspection_failed`, identify which earlier setup and application evidence survived cancellation. |
| `equipment_inventory_bytes` | `inventory_read` | “`equipment_inventory.path` names the sealed inventory for both worker roles. Its complete JSON file must fit in 1 MiB.” Compare message `inventory limit` during inspection with `missing` and native `ENOENT`. |
| `equipment_path` | The inventory, binding or live inspection’s qualified `path` | Identify the manifest, selected executable and observed executable at their respective lookups. Each absolute path allows 1,023 UTF-8 bytes. Trace one actor through all three owners, then examine an overlong reported path. |
| `exec_stream` | `attempt.stdout` or `attempt.stderr` | “Read `bytes_received`, `bytes_retained` and `truncated` for each stream. The truncation marker uses space within the 1,023-byte allowance.” Compare an exact fit on one stream with overflow on the other. |
| `reservation_attempts` | `attempt_limit` | “Acquisition stopped after 256 opened attempts.” Read `submission.state: not_invoked` and check whether time remained. Explain this in the 0.3.9 guide. The proposed lookup serves a reader starting from the saved status and is provisionally scheduled for 0.4.0. |
| `validator_reply_bytes_per_query` | `byte_limit` from `validator_subprocess.stdout_collection_stop` | “The phase reserves 16,384 stdout bytes per submitted query. A read can cross that cap. Look in `records` for complete verdicts retained before the cutoff.” Write this entry with the 0.4.0 rejected-frame review. Compare a cutoff mid-frame with a complete malformed frame and identify when the decoder can supply context. |
| `test_override_path` | The executable path in `admission_failure.field` | “Each path allows 1,023 UTF-8 bytes. Recover an omitted path from the request or invocation.” Identify the ordinary worker field, either actor role, or the validator flag. Compare refusal before launch with an exact-fit missing executable that reaches spawn or equipment preparation. The 0.4.0 test migration already owns a second look at the bound and behavior. |
| `controller_output` | `data.runner_client.stdout_truncated` or `.stderr_truncated` | “The controller retains 272 MiB per client stream. With truncated stdout, submission is unknown. With only stderr truncated, inspect the complete stdout capture.” Compare received and retained counts per stream. |
| `client_reply_retention` | `runner_reply_truncated` | “The client received a host reply and retained up to 92 MiB of it.” Ask which bytes survived and whether a complete host result is available. Compare with the controller’s separate `stdout_truncated` case. |
| `reservation_control_bytes` | `control_too_large` | “Reservation requests and control replies allow 65,536 bytes.” At an oversized control reply, read the byte count, hash, error stage and submission state. Compare acquisition with a reply after invocation. |
| `client_error_message`, `client_error_domain` | `message_truncated` or `domain_truncated` | “The client retains up to 1,024 UTF-8 bytes of diagnostic text and 128 of native domain. Each has its own loss flag.” At a shortened domain, ask what the intact native code can identify. |

## Standalone guide

Keep these edits with their existing cases. The exception is the single new timing section due before 0.3.9. Use existing emitted specimens as the starting point and reproduce worked examples with the staged release. The per-clock checks and the separate producer and reader obligations are in the working notes and the guide plan. [Guide](../../docs/PolicyWitness.md) · [Timing work](../../docs/guide/USER-GUIDE-PLAN.md#timing-in-039)

| Limit IDs | Reader’s entry point | Proposed text or demonstration and reader check |
| --- | --- | --- |
| `step_id`, `request_failure_path_components`, `request_failure_path_component` | Repairing a refused specimen | Edit the emitted example to contain a 64-byte step ID, find `actual`, `maximum`, `unit` and the step index, then shorten it to 63 bytes. Add a reading note for `path: null`. The host can retain eight components of 63 UTF-8 bytes each. An empty array identifies the root. A retained `parameter_key` can locate a value even without a path. |
| `fresh_read_bytes` | Run your first specimen | “Give the files the same first 64 bytes and different final bytes. Compare `content_hex`, then compare the two files independently.” The matching read prefixes leave whole-file equality open. |
| `observed_path`, `compiled_profile` | Handing a run to someone else | “The worker can report up to 1,023 bytes of descriptor path. `path_diagnostics` records a later host lookup.” In the existing capture paragraph add “Each opted-in worker can capture 1 MiB of raw compiled bytecode. Read `bytecode_length` before base64 encoding. For `worker_capture_refused`, inspect application separately. Several capture conditions share this reason.” Check a captured receipt and one unavailable after successful application. |
| `client_rpc_wait`, `runner_verify_wait`, `reservation_lease`, `reservation_rpc_wait`, `reservation_retry_delay`, `byoxpc_throttle_interval`, `runner_remove_teardown_wait`, `runner_remove_poll_interval`, `worker_policy_transfer`, `worker_ready_wait`, `worker_sentinel_wait`, `worker_timeout_override_floor`, `worker_exit_grace`, `worker_proceed_wait`, `actor_release_wait`, `actor_setup_allowance`, `actor_execution_allowance`, `actor_exchange_allowance`, `actor_lifetime_cutoff`, `actor_termination_wait`, `phase_collection_wait`, `actor_collection_allowance`, `validator_collection_override_floor`, `validator_io_wait`, `validator_io_override_floor`, `validator_exit_grace`, `exec_child_wait`, `exec_attempt_budget`, `exec_reap_grace` | The result card points to “Which wait ended?” in the release guide. Run and runner cards show their timeout defaults. | “Which wait ended? Start with the component that reported it. A client timeout after invocation can leave work running. Read a host wait’s `budget_ms` beside its stop reason. Each released phase also has a worker-side wait. Cleanup can continue after those clocks expire.” Use the delayed-create case to check whether the worker acted, and the phase/actor examples to identify which waits share time. Retire the corresponding QUESTIONS entry. |

In 0.3.9, show `--timeout-ms <n>` and 240,000 ms on `help run`, and the option and 5,000 ms beside `verify` on `help runner`. Check omitted and explicit values at client invocation, plus each parser's zero behavior. Start at a saved result, find `help result` from base help and follow its guide reference. Locate each timing row's field or observation in the passage and record which clock or allowance explains it. The timing section explains the acquisition count directly and links to the existing guide passage on removal. Try the reverse link from the recovery card separately, provisionally in 0.4.0, if it helps someone who already has the recovery instructions interpret `teardown_wait`. Read `submission.state`, an independent file observation, a late actor application, and confirmed and unconfirmed reap before signing off the timing prose. [Timing fields and proof obligations](../../docs/LIMITS.md#execution-budgets)

## Test flags and helper diagnostics

The test flag descriptions belong to the controller interface, using the worker’s argument rule. The helper owns its refusal text. Exercise the actual entry point for each and compare its output with the boundary it reached. [Override contract](../../docs/REQUEST.md#contract-request-overrides) · [Diagnostic helper limits](../../docs/LIMITS.md#diagnostic-helpers)

| Limit IDs | Reader’s entry point | Proposed text or demonstration and reader check |
| --- | --- | --- |
| `worker_fixture_delay` | The two worker delay flags moving from `test-input run` to `test run` | “Both flags accept positive delays through 60,000 ms. At 60,001 the launched worker refuses its arguments before setup.” During the 0.4.0 migration, decide where the new route should refuse an over-limit delay and how the caller will see that refusal. Write the shared flag help against that decision. Check worker progress for an admitted delay. |
| `helper_source` | `sbpl-check` diagnostic `policy_too_large` | “The helper allows 4 MiB of input and stopped before walking imports or compiling.” Check the absent compile and import results. A helper success still leaves the runner’s separate policy admission to check. |

## Inventory only

Keep each row’s counting rule, consequence, controls and support in the generated reference. The current refusal or diagnostic named below supplies evidence when applicable. [Technical inventory](../../docs/LIMITS.md)

| Limit IDs | Reader’s entry point | Proposed text or demonstration and reader check |
| --- | --- | --- |
| `phase_records`, `phase_publications`, `extension_token_storage`, `authority_slot_bytes`, `authority_setup_trailer`, `equipment_metadata_bytes` | Layouts and accounting | Keep slot counts, record sizes, the token terminator, setup trailer and equipment text accounting in the technical inventory. Cross-check those rows against the limits on actions or payloads the specimen author actually controls. |
| `host_exit_delay` | Host retirement | Inventory only. The unsandboxed host hands the execution reply to XPC and schedules exit after 50 ms. The client records receipt separately. The delay also schedules retirement of an unused reservation. |
| `validator_release_margin` | Timing implementation detail | Check the 5,000 ms nominal margin against the production budget inequality in the timing review. No timer expires at this margin. |
| `validator_query_payload`, `validator_reply_frame`, `validator_records_per_query`, `validator_reply_step_id`, `validator_reply_operation`, `validator_reply_filter_type`, `validator_reply_filter_value`, `validator_reply_outcome`, `validator_reply_error` | Validator protocol | Keep the exact query-line, response-frame, count and field ceilings in LIMITS. Compare the validator draining an overlong input line with the host stopping at its first invalid reply frame. Use the existing field-specific diagnostics and association evidence. |
| `porcelain_frame_bytes`, `porcelain_decoded_storage_bytes`, `porcelain_nesting` | Binary response reader | Keep the 128 MiB encoded and logical decoded-storage ceilings and the 32-level nesting check together. Read a short header, a compact frame that exhausts typed slot storage, and a 33-level constructed frame. |

## Decisions reserved for follow-up

The implementation owners supply the comparisons below. The worksheet and working notes record the specific files, controls and limits on interpretation. The timing section appears in the guide table. The timing review classified the host retirement delay under Inventory only. [Limits review plan](../../docs/LIMITS-SURFACING-PLAN.md#record-the-decisions)

| Limit IDs | Reader’s entry point | Proposed text or demonstration and reader check |
| --- | --- | --- |
| `helper_import_depth`, `helper_import_count`, `policy_helper_output` | Import helper investigation | Compare deep and wide import walks in the helper and dossier. Check whether an 8 MiB truncated fallback stream supports any complete helper result. Choose the routes after comparing what survived. |
| `equipment_signing_text`, `equipment_entitlement_bytes`, `equipment_entitlement_records` | Signing investigation | Trace a signer-chosen identifier and assigned Team ID through their producers and readers. Compare the inventory and host entitlement XML for the same dictionary, then follow one shared static binding into two live actor readbacks. Choose a route for each distinction that its producer can support. |
| `equipment_diagnostic_bytes` | 0.3.9 classification alongside `equipment_error_domain` | Compare exact-fit and shortened messages that look identical, including a multibyte boundary. Trace native and message-only errors to the reader and compare transport’s `message_truncated` field. Record what the release can say about lost text. The destination remains open. |
| `equipment_error_domain` | Decision due in 0.3.9 | Compare distinct native domains that share the retained 128-byte prefix and numeric code. Check an overlong supplied domain at the receiver. Decide how to classify the row. |
| `validator_fault_context` | Classification due in 0.4.0 | Compare 256- and 257-byte invalid frames sharing their first 256 bytes. Read `frame_bytes`, `retained_bytes`, `context_truncated` and the earlier verdicts. Decide what the diagnostic prefix represents and where to publish it. |

## Finding the whole inventory from a release

Propose a “Complete limits for this release” link in the standalone guide, with the same link discoverable from base help. Form it from the release tag and the repository path `docs/LIMITS.md`. The tag must match the staged build. Follow it from an extracted release, check the version and resolve a row that has no other route. Use the same revision and local-path rules as the request entries for development builds. [Release identity and discovery](../../CLI-TRANSITION-PLAN.md#find-the-applicable-release-contract-during-normal-use)

The offline alternative would stage the generated inventory with the guide. That requires choosing a distribution path, resolving its repository-relative links for offline readers, verifying its bytes in release preparation and exposing the file from the app or release materials. The tagged link suffices if network access is acceptable for the full reference. Decide the offline requirement alongside the 0.4.0 guide packaging work. [Guide delivery](../../docs/guide/USER-GUIDE-PLAN.md#deliver-one-authored-guide) · [Build publication](../../docs/BUILD.md)

After scope selection, store the chosen routes in `docs/limits.json` and render **Where users find it** in the five inventory tables. Enter a route when the corresponding release actually supplies it. Verify the generator, the tagged link and the reader checks on the staged app. [Publishing selected routes](../../docs/LIMITS-SURFACING-PLAN.md#publish-the-selected-routes)
