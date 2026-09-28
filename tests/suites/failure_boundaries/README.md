# Observer boundaries

`admission` exercises all fourteen capacity checks through the signed CLI: the
nine worker shared-memory bounds and five host-only fields (`sandbox_check.operation`,
`sandbox_check.filter.value`, `sandbox_check.filter.kind`, `attempt.kind` and
`attempt.action`), which the orchestrator refuses with the same record.
Every byte-limited field has exact, over, multibyte-exact and multibyte-over
controls; counts have exact/over controls. Refusals assert the same structured
host record, offending identity, units, absence of both children and an empty
`steps` array: a refusal echoes none of the plan. Accepted
boundaries require actual child completion.

`validator_frames` uses checked-in transcripts for valid replies followed by
invalid UTF-8, incomplete allow/deny, and a valid unfamiliar diagnostic. File
contents independently establish completed attempts. Rejected bytes are checked
against bounded host context; only valid preceding records may supply predictions.
`validator_association` tests duplicate/unexpected IDs and mismatched operation/filter type/value through the same route.

`validator_overlong_request` submits an operation of 65536 bytes between two
valid path-filter queries. Query admission refuses it before any process work:
the record names `sandbox_check.operation` on the middle step, the reply carries
no steps, no child exists and the target files keep their original contents.
Retained serialized NDJSON shows the middle line would have exceeded the
validator's line cap, and the largest admitted probe (63, 127 and 511 bytes,
every byte escaped) is measured to stay far inside it. The exact cap, the C
guard's null-ID diagnostic and drain/recovery remain owned by the native
`runner_abi_layout` boundary; the CLI can no longer reach them.
`validator_removed_target` uses the real validator and a completed unlink to
check that the join uses the submitted query even when a path no longer resolves.
Mixed and all-excluded create plans keep their pre-attempt exclusion decisions.

`fallback_helper` observes the shipped helper's separate 4 MiB admission refusal.
Rust tests separately check startup-note forwarding without fabricating an XPC
loss. Swift driver tests cover failed kill/reap, abnormal disposition, delayed
multibyte pipe writes, malformed/empty replies and competing I/O/decode faults.
These fixtures establish receiver handling, not claims about normal validator
behavior or policy causes. See the failure routing inventory for acceptance.
