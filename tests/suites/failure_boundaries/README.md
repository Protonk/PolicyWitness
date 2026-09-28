# Observer boundaries

`admission` exercises all twenty capacity checks through the signed CLI: the
nine worker shared-memory bounds, five host-only plan fields
(`sandbox_check.operation`, `sandbox_check.filter.value`,
`sandbox_check.filter.kind`, `attempt.kind` and `attempt.action`) and six
top-level strings (`specimen_id`, `run_kind`, `policy.format` and the three
`_test_overrides` executable paths), all refused with the same record.
Every byte-limited field has exact, over, multibyte-exact and multibyte-over
controls; counts have exact/over controls. Refusals assert the same structured
host record, offending identity, units, absence of both children and an empty
`steps` array, and that the refused string appears nowhere in the reply: a
refused step ID is named by `step_index` alone, a refused key by field alone,
and a refused top-level string is replaced or dropped. Accepted boundaries
require actual child completion, except the at-limit format and seam paths,
which pass admission and fail as `bad_policy` or their own spawn/dlopen
outcome. Two precedence controls submit an oversized step ID beside an empty
operation and beside a duplicate ID: capacity is refused first, so the shape
diagnostics that quote step IDs never see an unbounded one.

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
`validator_control_characters` writes three files whose names and step IDs carry
U+0001, backspace, escape and U+001F, which Foundation sends to the validator as
`\uXXXX` escapes. The real validator must decode them, check the exact path and
echo them escaped: every prediction is `allow` from the validator, every
record's raw line is strict JSON without a raw control byte, association is
clean and every write completes. The native `runner_abi_layout` boundary owns
the parser controls, including surrogate pairs and malformed escapes.

`fallback_helper` observes the shipped helper's separate 4 MiB admission refusal.
Rust tests separately check startup-note forwarding without fabricating an XPC
loss. Swift driver tests cover failed kill/reap, abnormal disposition, delayed
multibyte pipe writes, malformed/empty replies and competing I/O/decode faults.
These fixtures establish receiver handling, not claims about normal validator
behavior or policy causes. See the failure routing inventory for acceptance.

Admission also checks every pair of invalid top-level/override fields through
the CLI, preserving a write target and requiring a refusal below 4 KiB. Tests
inspect decoded string values so JSON escaping cannot hide a repeated value.
Native-string NUL cases place a valid write before the invalid step and require
no file effects, no children and `nul_bytes` against maximum zero. Direct Swift
controls vary rejected input sizes and compare service/direct refusal encoding.
The native validator corpus covers raw and escaped Unicode, malformed UTF-8,
control bytes, surrogate pairs, raw NUL framing and recovery after each failure.
