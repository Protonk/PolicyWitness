# Pilot native event protocol

`pilot supervise C0..C7 TRIAL_ID TRIAL_DIR [LOCK_FDS_CSV]` runs one native
trial. The driver owns the existing, fresh trial directory and process group.
The supervisor creates `A` and `B` there. Every role execs the same executable.
Issuer and recipient receive exactly `PATH=/usr/bin:/bin` and `LC_ALL=C`.

Stdout is token-free NDJSON. Each event has `schema_version: 1`, a strictly
increasing supervisor-assigned `seq`, `role` (`supervisor`, `issuer`, or
`recipient`), `pid`, `stage`, `status`, and `details`. Child events additionally
have `producer_seq`, the child's ordered shared-memory publication number.
`monotonic_ns` records the producer's publication time. Status is `attempted`
(a published observation), `omitted` (by design), `unavailable` (with `reason`),
or `interrupted` (the planned boundary lacks a published result).

Child publications use fixed, token-free shared slots. The supervisor emits
and flushes each slot before acknowledging it; `publication_ack` events name
`child_role`, `child_pid`, `producer_seq`, and `acknowledged_stage`. A native
call boundary is distinct from its result. An `issue_begin` or `consume_begin`
publication alone never supplies the corresponding native return.

## Supervisor records

| Stage | Details |
| --- | --- |
| `supervisor_start` | `trial_id`, `arrangement`, `process` (PID, PPID, PGID, credentials, executable path and kernel `start_identity`), core-limit result, environment. |
| `targets_prepared` | `a`, `b` objects with canonical `path`, `identity`, `known_content_hex`, and independent `baseline` fresh-read observations; exact `issuer_policy`, `recipient_policy`; native `extension_class`, `flags`. |
| `channel_resource` | Native shared-memory creation/unlink observation, including exact owned name; failed unlink sets `cleanup_pending: true` and prevents child launch. |
| `channel_preparation` | Raw channel `ftruncate`, mapping success, descriptor duplication, and original-descriptor close results, with unavailable dependent operations explicitly marked. |
| `channel_setup` | `evidence`, `issued_token`, and `delivered_token` objects with `descriptor`, `size`, `identity_rc`, `identity_errno`, and `identity`; `issued_initial_zero`, `delivered_initial_zero`, and explicitly inherited `child_lock_descriptors`. |
| `child_launch` | `child_role`, spawn `rc`, `errno`, `child_pid`, observed `process` including kernel start identity. Published immediately after each launch. |
| `query_capability` | Separate `api` and `flag` lookup observations, resolving `image` strings, numeric exported `no_report_flag` when available. |
| `query` | Exactly `filter_id` 0 and 1; `filter_value` null or A; `operation: file-issue-extension`, `caller_pid`, `target_pid`, numeric `no_report_flag` and complete `type_argument`, raw `rc`, `errno`; unavailable records retain query arguments and `reason`. |
| `issue_release` | `issuer_pid`, `recipient_pid`, `queries_collected: 2`, readiness observations. This follows both query records and precedes the issuer call. |
| `transfer_ready` | `ready`, validated `length`, framing checks, and issuance-publication reference; no bytes. |
| `transfer_equality` | After recipient acceptance and before consume release: transient `equal` and compared `length`, or unavailability reason. |
| `consume_release` | Recipient PID and acceptance/equality observations; source gate released even when consumption is unavailable, permitting the second read. |
| `child_reap` | `child_role`, PID, raw wait result/status/errno and decoded exit code or signal. |
| `child_signal` | Owned role/PID, signal and raw result/errno. |
| `targets_after` | Independent fresh-read and identity observations for A and B after children are reaped. |
| `supervisor_token_erasure` | Full-capacity erasure and zero read-back for both owned token mappings. |
| `interrupted_stages` | On equipment failure, `missing_publications` inventories expected role/stage/boundary observations that never arrived. These are supervisor descriptions with `interrupted` status for launched children or `unavailable` for unlaunched children, never fabricated child results. |
| `supervisor_complete` | Elapsed time, deadline/equipment-failure facts, child reaping facts. Driver supplies separate supervisor reap, group absence, and path removal evidence. |

## Child records

Each child publishes these preparation stages in order: `process_entry`,
`fd_snapshot` with `boundary: entry`, `channel_mapped`, `symbols`, `images`,
`policy_compile`, `fd_snapshot` with `boundary: before_apply`, and `apply`.
`process_entry` has the same process-identity shape as the supervisor.
`policy_compile` retains exact `policy`, `nonnull`, and `errno`; it never
retains arbitrary native diagnostic text. `apply` has `rc`, `errno`, and
`application_count`; C0 issuer instead records `omitted` with count zero.

Process objects have `pid`, `ppid`, `pgid`, `uid`, `euid`, `gid`, `egid`,
`start_identity: {seconds, microseconds}`, `executable_path`, and
`executable_identity`. The raw kernel process/executable inspection results
are `identity_rc`, `identity_errno`, `executable_rc`, `executable_errno`,
`executable_stat_rc`, and `executable_stat_errno`. Both role entry and
supervisor start records retain the actual `environment` string array and
`core_limit: {rc, errno}`. Executable metadata acquisition concerns the pilot
binary, never A or B.

`symbols` records an explicit pre-apply open of `/usr/lib/libsandbox.dylib`
(`library_opened`, `requested_library`) and `issue`, `consume`, `compile`,
and `apply` lookup objects. Relevant lookups have `available`, `image`, and
`dladdr_rc`; the other role's unused issue/consume lookup is omitted by design.
`channel_mapped` has `evidence` and `token` objects containing `descriptor`,
`map_succeeded`, `map_errno`, and `close: {rc, errno}`; it also records
`initial_token_zero`. The token descriptor is 4 for either role, referring to
its separately assigned issued or delivered mapping.

Each descriptor snapshot contains `boundary`, `inspection_complete`,
`scan_limit`, `descriptors`, and any `reason`. Each descriptor has `fd`, `type`,
`stat_rc`, `stat_errno`, an identity on successful fstat, and `matches_a` and
`matches_b`. Snapshot acquisition on entry occurs before mapping or symbol
resolution; its fixed local storage is subsequently published. Descriptor
identities use `device`, `inode`, `mode`, `uid`, `gid`, and `size` throughout.
An unavailable snapshot names the boundary and reason. The issuer has exactly
three snapshots: `entry`, `before_apply`, `before_issue`. The recipient has
exactly four: `entry`, `before_apply`, `before_read_before`, `before_read_after`.

After application the recipient publishes its first snapshot/read pair:
`fd_snapshot: before_read_before`, then `read_before`. It then waits for
transfer readiness. The issuer waits for `issue_release`, then publishes
`fd_snapshot: before_issue`, `issue_begin`, `issue_result`,
`raw_token_erasure`, and `token_publication` in order. `issue_result` retains
`nonnull` and raw `errno`; `token_publication` retains `published`, `length`,
and bounded NUL/framing results. These stages are explicit with unavailability
reasons after failed preparation, application, or null issuance.

Following `transfer_ready`, the recipient publishes `transfer_acceptance`
with `accepted`, `length`, `header_valid`, `length_valid`, `terminator_valid`,
and `embedded_nul_absent`. The supervisor checks issued versus received bytes
transiently, publishes `transfer_equality`, then `consume_release`.
The recipient publishes `consume_begin` and `consume_result` (`rc` is the
raw signed 64-bit return, `errno` saved immediately). C6 records omission;
failed delivery records unavailability. It then publishes its second
snapshot/read pair even after native consume `-1`, omitted consumption, or
unavailable delivery, provided its own application succeeded.

`read_before` and `read_after` contain `path`, `descriptor` (or null), separate
`open`, `identity_check`, `read`, and `close` objects, `identity` on successful
fstat, and `content_hex`. Each call object has `status`, `rc`, and `errno`, or
an unavailability `reason`. Successful access requires the independent target
identity and known bytes. Open failure leaves the other three calls explicitly
unavailable. Each successful open is closed within that read event.

After the final read, the recipient records `token_erasure` (full delivered
buffer), then `child_exit`. The issuer records `token_erasure` (full issued
buffer) and `child_exit` after the supervisor releases it for exit. Token
erasure records contain `buffer`, `capacity`, and `zero_confirmed`.
`child_exit` publishes the intended `exit_code`; independent wait results
remain separate. Fatal interruption can prevent erasure or exit publication.

The native issuer allocation's `raw_token_erasure` records inspected/erased
prefix lengths, `zero_confirmed`, and `terminator_within_bound`.
`allocation_extent_observed` remains false: locating a terminating NUL does
not establish the allocation extent or any private library copies.

`targets_after` contains `a` and `b`, each with `path` and `read` (the same
fresh-read object shape). `supervisor_complete` records `elapsed_seconds`,
`deadline_reached`, `equipment_failure`, `reason`, `issuer_reaped`,
`recipient_reaped`, `issuer_wait_status`, `recipient_wait_status`,
`all_children_reaped`, and `output_failed`.

The shared deadline begins immediately before the first child spawn and is
never restarted at gates. Its allowance is 20 seconds; cleanup SIGKILL/reap
allows at most two additional seconds per still-live child. Native failures
remain observations; process/evidence failures set equipment failure. The
driver's independent 30-second bound and group-absence check own outer cleanup.
A failed monotonic clock call terminates the affected native process with code
90, preserving earlier publications for the driver; it never supplies a
synthetic zero time that could disable the execution bound.
