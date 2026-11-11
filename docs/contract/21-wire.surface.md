# Response encoding {wire: surface}

```contract
syntax: 1
artifact: "Binary response primitives and validator record transport"
part: "delivery"
goldens: ["tests/fixtures/contract/surfaces/wire.json", "tests/fixtures/contract/response_shape.json"]
checks: ["source_drift", "unit", "runner_unit"]
```

The host reply and client capture use typed binary frames. The controller projects admitted typed records into public JSON. Saved specimens and reservation controls use their own JSON decoders; validator query records use the separate line protocol below.

## Implementation and evidence {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "runner/Sources/PWRunnerCore/PWPorcelain.swift", "symbol": "pwPorcelainValue"}, {"path": "controller/src/porcelain.rs", "symbol": "decode_bound"}, {"path": "docs/generate_porcelain.py", "symbol": "wire_identity"}, {"path": "docs/generate_porcelain.py", "symbol": "rust"}, {"path": "tests/lib/porcelain.py", "symbol": "class Reader"}]
check: [{"path": "controller/src/porcelain.rs", "symbol": "native_integer_width_and_boolean_values_are_not_coerced", "form": "test"}, {"path": "controller/src/porcelain.rs", "symbol": "authored_record_faults_are_refused_before_typed_construction", "form": "test"}, {"path": "controller/src/porcelain.rs", "symbol": "list_slots_and_nested_strings_share_one_budget", "form": "test"}, {"path": "tests/suites/source_drift/porcelain_codec.py", "symbol": "test_homogeneous_lists_sorted_maps_variants_and_depth", "form": "test"}]
pins: "The schema owns record identities/tags/types and public projections. Swift writes declared values; Rust and Python independently read their structure. The named controls reject authored scalar/record faults and preserve byte projections."
context: "Read the cited producer/receiver declarations and branches; check citations identify the assertions read."
limits: "Shared generated tables establish agreement with the declared schema; native malformed-container and host frame-cap coverage remain separate evidence work."
```

## Frame grammar {frame: subject}

### Frame and value headers {headers: definition}

```contract
defines: "record"
```

A frame is the four ASCII bytes `PWP1`, 32 raw bytes of the schema SHA-256 fingerprint, then exactly one root value. A value is a one-byte kind, a four-byte unsigned little-endian payload length, and exactly that many payload bytes. Every multi-byte integer in the frame grammar is little-endian. Root, record and field identities are those of the declared wire schema retained with the wire surface’s canonical shape.

### Primitive payloads {primitives: definition}

```contract
defines: "value"
```

| Kind | Payload and interpretation |
| --- | --- |
| 1 · boolean | Exactly one byte: 0 means false and 1 means true. |
| 2 · signed integer | Exactly eight bytes, two’s-complement signed 64-bit. The declared destination type also constrains its representable range. |
| 3 · unsigned integer | Exactly eight bytes, unsigned 64-bit. The declared destination type also constrains its representable range. |
| 4 · text | Strict UTF-8 bytes of the string; payload length supplies its extent. |
| 5 · bytes | Uninterpreted octets. The owning field supplies their public JSON spelling. |
| 6 · record | Unsigned two-byte record ID, then repeated unsigned two-byte field tag and complete value pairs. Tags are nonzero and strictly increasing. |
| 7 · list | Unsigned four-byte element count, followed by that many complete values of the schema’s element type. |
| 8 · ordered string map | Unsigned four-byte entry count, followed by text-key/value pairs. Keys are unique and strictly increasing by their UTF-8 bytes; values have the declared homogeneous type. |
| 9 · declared variant | Unsigned two-byte case tag, followed by exactly one complete value of that case’s declared type. |

Optional record fields are omitted from the binary record when the producer has no value. A reader requires each nonoptional field and constructs optional absence from missing tags. JSON omission and null are projection choices owned by the field definition.

### Text enums and typed variants {variants: definition}

```contract
defines: "value"
```

Outcome, state and reason vocabularies travel as text values. Each field's named recipient checks and assessments determine the consequence of a familiar or unfamiliar value. Record references retain their declared record type; equipment references use unsigned indices into their named tables. The declared PWDispositionValue variant has case tag 1 carrying a signed integer and case tag 2 carrying PWRunnerTerminationRequest. Public JSON serializes the selected value directly.

### Retained-byte reader {reader: definition}

```contract
defines: "component"
```

The Python retained-byte reader admits captured porcelain frames against the
declared wire schema and projects their fields for the repository's evidence
readers. The received bytes remain with their capture owner.

### Exact structural admission {admit: checks}

```contract
who: ["identity.definitions.controller", "wire.frame.reader"]
where: "one complete client-capture or host-reply frame"
entry: ["client_stdout", "host_reply", "retained_frame"]
recipient: ["controller", "evidence_reader"]
report: ["controller_envelope"]
uses: ["identity.public.contract", "identity.other.wire"]
free.condition: A complete frame has been retained for the requested root kind.
free.effect: Check frame extent/magic and exact fingerprint, then the expected root and producer identity before descendants. Refuse wrong kinds, unknown records/tags/cases, missing required fields, invalid UTF-8, out-of-range integers, impossible lengths/counts, duplicate or out-of-order fields/keys and trailing bytes.
```

A complete header naming another fingerprint yields unsupported schema before payload interpretation. A short fingerprint is malformed. The bound reader compares the client’s contract or host producer contract with the caller’s expected public identity; `unbound` cannot supply a positive identity admission. Successful structural decoding establishes the declared typed shape. Native-operation, lifecycle, phase, actor, equipment and custody consistency have separately named semantic readers.

### Receiver and writer budgets {budgets: definition}

```contract
defines: "value"
```

The frame cap is <!-- span limits.porcelain_frame_bytes.value_unit -->134,217,728 bytes<!-- /span --> and the nesting limit is <!-- span limits.porcelain_nesting.value -->32<!-- /span --> values. Rust shares one <!-- span limits.porcelain_decoded_storage_bytes.value_unit -->134,217,728 bytes<!-- /span --> logical decoded-storage budget across collection slots, strings and byte arrays within each frame; slot charges use the compiled destination type’s size. Capture and embedded host reply are separate frames and separate budgets. Swift bounds encoded values and record growth so a produced frame fits its frame cap. The client retains at most <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span --> of a host reply. The controller collects client output before applying its <!-- span limits.controller_output.value_unit -->285,212,672 bytes<!-- /span --> per-stream retention cap. These quantities describe distinct allocation, encoding and retention operations; complete-output collection can use more memory than a retained prefix.

### Exact wire identity {identity: definition}

```contract
defines: "value"
```

The fingerprint is SHA-256 of the compact, object-key-sorted JSON wire identity emitted by `wire_identity`: schema version; records in schema order with ID, name and fields; each field’s tag, public name, type descriptor, null rule and any byte projection; path-form and conditional-null rules; root names mapped to record IDs; and declared variant cases. Local-only fields are omitted. Source paths, mutable/default annotations and descriptive text remain source provenance. Changes to a field’s name, tag, type, optionality, null/projection rule or a newly added optional field change the fingerprint and require exact receiver agreement.

### Public JSON projection {projection: definition}

```contract
defines: "record"
```

Bytecode, retained host frames and rejected validator context become standard base64. Digests, code-directory hashes, worker identity and fresh-read bytes become lowercase hexadecimal. Path-form fields equal to their input bytes are omitted and listed in `same_as_input`; unavailable forms remain null. Conditional-null fields are carried only when their guard has a value. Other optional fields follow their declared omit/null rule. The generated Rust serializers and independent Python projection apply these rules after typed byte admission.

### Primitive and writer evidence scope {reader_coverage: definition}

```contract
defines: "value"
```

Literal malformed frames exercise ordered maps, collection counts and item kinds, generated byte fields, variant alternatives and nested-container limits through the Rust decoder. The public schema is nonrecursive; the depth control uses a recursive test wrapper over the production list reader. A constructed oversized diagnostic exercises the actual host writer limit and rich-to-minimal fallback. Its emitted minimal frame is carried through the independent readers.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/porcelain.rs","symbol":"pub fn decode"},{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"pwRunnerReportData"}]
pins: "Actual decoder and writer boundaries own structural refusal and fallback."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"controller/src/porcelain.rs","symbol":"ordered_maps_require_unique_ascending_keys_in_actual_frames","form":"test"},{"path":"controller/src/porcelain.rs","symbol":"generated_disposition_variant_checks_tag_payload_and_complete_body","form":"test"},{"path":"controller/src/porcelain.rs","symbol":"actual_nested_container_frames_reach_but_do_not_exceed_depth_32","form":"test"},{"path":"runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift","symbol":"runReplyFailureTests","form":"test"}]
limits: "The huge diagnostic is constructed; writer refusal and its retained minimal frame are distinct from native production or XPC cap-interval observation."
```

#### Executed Rust wire controls {rust_execution: owner}

```contract
grade: "executed"
source: {"path":"controller/src/porcelain.rs","symbol":"pub fn decode"}
check: [{"path":"controller/src/porcelain.rs","symbol":"ordered_maps_require_unique_ascending_keys_in_actual_frames","form":"test"},{"path":"controller/src/porcelain.rs","symbol":"list_counts_item_kinds_and_trailing_items_refuse_in_actual_frames","form":"test"},{"path":"controller/src/porcelain.rs","symbol":"generated_capture_byte_field_requires_the_byte_kind","form":"test"},{"path":"controller/src/porcelain.rs","symbol":"generated_disposition_variant_checks_tag_payload_and_complete_body","form":"test"},{"path":"controller/src/porcelain.rs","symbol":"actual_nested_container_frames_reach_but_do_not_exceed_depth_32","form":"test"}]
pins: "Literal frames exercise duplicate/descending map keys, impossible or mixed lists, generated byte kind, variant tag/payload/body and actual nested depths 32 and 33."
context: "The completed unit/rust.unit case passed with zero recorded system sleep; all five named controls passed in cargo-test-bins.log."
limits: "The depth control uses a recursive test wrapper over the production list reader; the public schema is nonrecursive. These are structural decoder controls over constructed bytes."
run: "20261111T155411Z_29ef0802"
case: "unit/rust.unit"
source_snapshot: "reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)"
```

#### Executed writer fallback receipt {writer_execution: owner}

```contract
grade: "executed"
source: [{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"pwRunnerReportData"},{"path":"runner/Sources/PWRunnerCore/PWPorcelain.swift","symbol":"text exceeds byte limit"}]
check: [{"path":"runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift","symbol":"runReplyFailureTests","form":"test"},{"path":"controller/src/run_flow.rs","symbol":"reader_definition_corpus_cross_readers","form":"test"},{"path":"tests/suites/runner_unit/reader_corpus.py","symbol":"replay","form":"test"}]
pins: "A constructed 134217729-byte attempt diagnostic reaches the actual text guard twice. The independent minimal writer emits 621 bytes with evidence_retained false, empty steps/phases and preserved scalar identity and original summary; Rust and Python read the retained frame."
context: "The whole fresh runner-unit case passed with zero recorded system sleep. writer-cap-receipt.json and writer-cap-minimal.pwp join the actual Swift failures to the exact-one Rust and completed Python corpus replay."
limits: "The diagnostic is constructed. The observation covers the production writer and fallback; native production of that diagnostic and XPC behavior between retention and frame limits retain separate evidence scopes."
run: "20261111T162345Z_3d6c7242"
case: "runner_unit/pwrunner_core_unit_executable"
source_snapshot: "reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)"
```

## Validator query and reply lines {validator: subject}

```contract
uses: ["steps.verdict", "lifecycle.validator", "lifecycle.decode_fault", "lifecycle.association_issue"]
```

### Query production and native boundary {query: acts}

```contract
who: "runner host and native validator helper"
where: "validator --batch PID stdin and sandbox_check call"
entry: ["eligible_phase_query"]
recipient: ["validator"]
report: ["validator_records"]
free.condition: The host has planned an eligible query against the active worker PID.
free.effect: Write one JSON object per line with string step_id, operation and filter_type, and string filter_value for a non-NONE filter. The helper parses that line and calls sandbox_check with SANDBOX_CHECK_NO_REPORT only after grammar and filter admission.
```

The batch parser accepts a flat object with exactly the recognized key names; each supplied value is a string. NONE requires filter_value absent; other types require it present. Trailing content, raw NUL, invalid UTF-8, invalid escapes, U+0000 and unpaired surrogates are refused. Standard JSON escapes and paired Unicode surrogate escapes decode to their UTF-8 characters. Physical lines exceeding <!-- span limits.validator_query_payload.value -->65,534<!-- /span --> payload bytes are drained and yield one parse_error diagnostic. Blank lines are skipped. A repeated recognized key currently replaces the earlier parsed value.

### Verdict production {emit: reports}

```contract
who: "native validator helper"
where: "batch stdout after each nonblank input line"
entry: ["validator_batch"]
recipient: ["runner_host"]
report: ["validator_records"]
free.condition: The helper parsed a physical input line or performed its requested native call.
free.effect: Emit a newline-terminated object with kind sb_api_validator_verdict, integer schema_version 1, step_id and outcome. Native-call records carry operation, filter_type, filter_type_id, filter_value, rc, errno and error; parse/filter refusals carry recovered-or-null step_id and error without inventing native results.
```

Before each native call the helper clears errno. Native rc 0 is `allow`; rc 1 with errno 0 is `deny`; rc -1 with EINVAL is `unsupported_operation`; other pairs are `error`. Parse errors use `parse_error`; an unsupported filter uses `bad_filter`. Per-line failures continue to the next line, and clean batch EOF returns zero even when individual records report failures.

### Host line admission {read: checks}

```contract
who: ["identity.definitions.host"]
where: "validator stdout framing and decoded-record construction"
entry: ["validator_stdout"]
recipient: ["runner_host"]
report: ["validator_records", "host_reply"]
uses: ["lifecycle.validator"]
free.condition: The host has received a validator output prefix within its stream allowance.
free.effect: Split on LF, ignore empty frames and decode a final nonempty fragment. Admit strict UTF-8 JSON objects under per-frame, record-count, primitive-type and string-byte checks. Stop at the first refused frame while preserving earlier complete records and bounded rejection context.
```

Every admitted object has exact kind, integer schema_version 1, a present string-or-null step_id and nonempty string outcome. Known optional strings and integer fields may be absent or null; Boolean, fractional, string-valued and overflowing numbers cannot supply native integers. Allow/deny require nonempty step_id, operation and filter_type plus integer rc and errno. Every other outcome requires string error. Extra JSON fields and unfamiliar diagnostic outcomes survive in the accepted raw line. Frame size is at most <!-- span limits.validator_reply_frame.value_unit -->8,192 bytes<!-- /span -->; string limits are <!-- span limits.validator_reply_step_id.value_unit -->63 UTF-8 bytes<!-- /span --> for step_id, <!-- span limits.validator_reply_filter_type.value_unit -->63 UTF-8 bytes<!-- /span --> for filter_type, <!-- span limits.validator_reply_outcome.value_unit -->63 UTF-8 bytes<!-- /span --> for outcome, <!-- span limits.validator_reply_operation.value_unit -->127 UTF-8 bytes<!-- /span --> for operation, <!-- span limits.validator_reply_filter_value.value_unit -->1,023 UTF-8 bytes<!-- /span --> for filter_value and <!-- span limits.validator_reply_error.value_unit -->511 UTF-8 bytes<!-- /span --> for error. Rejected context retains at most <!-- span limits.validator_fault_context.value_unit -->256 bytes<!-- /span -->. The validator subprocess account defines this phase collector's total stream and record allowances and subsequent unique-step association.

### Repeated native query keys {duplicate_keys: definition}

```contract
defines: "value"
```

The native batch parser accepts repeated recognized string keys and keeps the last parsed value for each key. Host query serialization emits each key once. Direct-arrival batch queries retain their own parsing rule at this native boundary.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/tools/sb_api_validator/sb_api_validator.c","symbol":"parse_probe_line"},{"path":"controller/tools/sb_api_validator/sb_api_validator.c","symbol":"run_batch"}]
pins: "The native batch parser supplies the accepted query values."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/validator_batch_mode/run.sh","symbol":"batch_ndjson_roundtrip","form":"test"}]
limits: "Both member orders are retained in raw query text and checked against independently selected final strings."
```

### Native prediction example {example: example}

For a query with step_id `read`, operation `file-read-data`, filter_type `PATH` and a concrete path, a native return rc 1/errno 0 produces outcome `deny` and error null. That record describes the native prediction for the queried worker and target at the query boundary. The separate attempt observation supplies the operation’s observed effect.

### Validator protocol support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "parse_probe_line"}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "emit_verdict"}, {"path": "runner/Sources/PWRunnerCore/ValidatorClient.swift", "symbol": "decodeValidatorFrames"}, {"path": "runner/Sources/PWRunnerCore/ValidatorClient.swift", "symbol": "validatorStructureError"}]
check: [{"path": "runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift", "symbol": "runValidatorEvidenceTests", "form": "test"}]
pins: "Constructed byte controls retain valid prefixes and raw native values, refuse invalid UTF-8/numeric types/overflow/oversized fields, and withhold guessed joins for duplicate or unknown IDs."
context: "Read C query parser and batch emission, Swift framing/type validation, and the named Swift control body."
limits: "Check reading only. The numeric example follows the emitter branch; an observed deny prediction for a particular current host/path requires its own native run. Duplicate query-key behavior is source-read."
```


## Direct validator commands {standalone: subject}

Each shipped service contains `Contents/MacOS/sb_api_validator`. Direct invocation accepts `[--json] PID [operation filter_type [filter_value]]`; `--batch PID` selects the line protocol above. The leading flags select distinct modes and are not combined.

### Parse and report a PID {status: acts}

```contract
who: "native validator helper"
where: "direct argv admission"
entry: ["validator_status", "validator_single_query", "validator_batch"]
recipient: ["direct_helper_caller"]
report: ["validator_status", "validator_single_result", "validator_error"]
free.condition: The first positional value is consumed by base-10 strtol and is positive and at most 1,073,741,824, with no trailing bytes.
free.effect: Accept that numeric PID. With no further arguments in direct mode, print ok or the JSON status object and exit zero. With operation arguments, continue to filter admission; batch takes no further positional arguments.
```

The PID-only branch performs parsing and reaches no sandbox_check call or process-existence check. Missing arguments before a PID produce stderr and exit 2, including a bare --json. An invalid supplied PID produces stderr in plain mode or pid_missing in JSON mode, with pid -1 and exit 2.

### Choose a native filter {filters: definition}

```contract
defines: "value"
```

Direct and batch queries share a filter-name resolver: NONE is 0, PATH is 1, GLOBAL_NAME is 2 and LOCAL_NAME is 3. Conditional SDK names are APPLEEVENT_DESTINATION, RIGHT_NAME, PREFERENCE_DOMAIN, KEXT_BUNDLE_ID, INFO_TYPE, NOTIFICATION_TYPE, XPC_SERVICE_NAME, NVRAM_VARIABLE and POSIX_IPC_NAME when their corresponding sandbox filter macros exist at compilation. `RAW:<number>` uses base-10 strtol, accepts a fully consumed value from 0 through 255 and supplies that numeric filter ID. These accepted helper names are distinct from the host planner’s eligible query pairs.

### Run one native query {query: acts}

```contract
who: "native validator helper"
where: "direct sandbox_check call and stdout"
entry: ["validator_single_query"]
recipient: ["direct_helper_caller"]
report: ["validator_single_result", "validator_error"]
free.condition: An operation and recognized filter are supplied. Numeric filter ID zero requires no filter-value argument; every other ID requires exactly one.
free.effect: Clear errno, invoke sandbox_check for the supplied PID with SANDBOX_CHECK_NO_REPORT, and report the native rc and errno. Plain output is rc=<value> errno=<value> and exits zero for rc zero, one otherwise. JSON mode emits its single-result object and exits zero after the call, whatever its native result.
```

CLI filter/argument refusal exits 2. JSON mode emits sb_api_validator_error: bad_filter carries the supplied filter; missing_args, unexpected_filter_value_for_none, missing_filter_value and unexpected_extra_args carry the parsed PID. The native string printer escapes quotes, backslashes and control bytes; remaining argument bytes pass through unchanged.

#### Direct-query execution support {execution_support: owner}

```contract
scope: "self"
grade: "executed"
source: [{"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "int main("}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "resolve_filter_type_id"}]
check: [{"path": "tests/fixtures/validator/no_report.c", "symbol": "raw_zero", "form": "control"}, {"path": "tests/fixtures/validator/no_report.c", "symbol": "result_meaning", "form": "control"}, {"path": "tests/suites/validator_batch_mode/run.sh", "symbol": "batch_ndjson_roundtrip", "form": "test"}]
pins: "RAW empty/zero direct value arity, no-report native-call flag, and direct JSON/plain versus batch output/exit for six supplied rc/errno pairs; the shipped helper separately observes selected allow, deny and unsupported-operation results against its owned native target."
context: "Read the production parser/emitter and exact assertions; inspected both completed validator_batch_mode case receipts, retained argv/input/output and control.log in run 20261111T155411Z_29ef0802."
limits: "The return matrix substitutes the native call in a production-source build. Shipped-helper observations use the selected target and macOS build; PID-only admission, other argument errors and invalid-UTF-8 direct arguments retain source support. The overall default run has a separate reader-corpus case failure."
run: "20261111T155411Z_29ef0802; validator_batch_mode/predictions_do_not_report and validator_batch_mode/batch_ndjson_roundtrip"
build: "Selected signed candidate build 1335, version 0.3.7, commit b6ce6d266ff281fafdae44c32061ceff018485bb dirty; public identity development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28"
source_snapshot: "controller/tools/sb_api_validator/sb_api_validator.c sha256 93318c0dd70ce26a0113fc0ab5fb676cf91938eda1bf2cfce3afc8d50c8ae4c6; tests/fixtures/validator/no_report.c sha256 d82d36711d15c824085a327f3dc268263f144949d8582c7ddc4682277d3a4e51; tests/suites/validator_batch_mode/run.sh sha256 da7ae5d7825202e974accd01149daff914c194a7d69d5af7bbc9c7d4a6e57897"
```

### Direct and batch validator meanings {meaning: definition}

```contract
defines: "value"
```

Direct JSON denied means native rc is nonzero, including a native error; successful direct JSON reporting exits 0. Plain output exits 0 or 1 from native rc. Batch deny requires rc 1 and errno zero and retains its diagnostic classifications. An empty RAW suffix resolves to numeric zero. Direct numeric-zero filters take no value; batch treats the spelling NONE as valueless, so RAW:0 carries a value that the zero-filter native call leaves unused. Direct argv uses C strings; batch validates its JSON strings as UTF-8.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: {"path":"controller/tools/sb_api_validator/sb_api_validator.c","symbol":"resolve_filter_type_id"}
pins: "Direct and batch parsing and native-result projection retain operation-specific rules."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/validator_batch_mode/run.sh","symbol":"batch_ndjson_roundtrip","form":"test"}]
limits: "The controls compare selected shipped-helper RAW-zero, duplicate and native error/deny cases; status and encoding branches retain their own source support."
```

### Direct-command support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "int main("}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "parse_pid"}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "resolve_filter_type_id"}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "print_error"}, {"path": "docs/build.json", "symbol": "sig_validator"}]
pins: "Direct argv branches establish parsing, mode-specific output, filter resolution and exit selection; the build inventory establishes the shipped helper location."
context: "Read complete main/parse/filter/error-printer branches and the signed app helper inventory."
limits: "PID-only admission, conditional filter names and raw C-string encoding are supported by the cited source branches. The query controls cover their selected RAW-zero and result/exit branches."
```

## Direct PID status {standalone_status: subject}

```contract
record: "ValidatorDirectStatus"
as: "standalone_status"
```

A status object records accepted PID syntax. It is separate from a native query result.

### kind {kind: field}

```contract
type: "String"
```

sb_api_validator_status identifies the PID-only JSON branch.

### schema_version {schema_version: field}

```contract
type: "Int32"
```

Version 1 of this direct JSON object.

### pid {pid: field}

```contract
type: "Int32"
```

Positive PID accepted by argument parsing.

### error {error: field}

```contract
type: "JSON"
```

Always null on this status branch.

## Direct native result {standalone_result: subject}

```contract
record: "ValidatorDirectResult"
as: "standalone_result"
```

### kind {kind: field}

```contract
type: "String"
```

sb_api_validator_result identifies one direct native query.

### schema_version {schema_version: field}

```contract
type: "Int32"
```

Version 1 of this direct JSON object.

### pid {pid: field}

```contract
type: "Int32"
```

Parsed PID passed to sandbox_check.

### operation {operation: field}

```contract
type: "String"
```

Operation argument passed to the native call.

### filter_type {filter_type: field}

```contract
type: "String"
```

Supplied symbolic or RAW filter spelling.

### filter_type_id {filter_type_id: field}

```contract
type: "Int32"
```

Resolved numeric filter ID before OR with SANDBOX_CHECK_NO_REPORT.

### filter_value {filter_value: field}

```contract
type: "String"
optional: true
json_null: true
```

Filter string passed for a nonzero ID; null for ID zero.

### extra {extra: field}

```contract
type: "JSON"
```

Always null in this producer.

### rc {rc: field}

```contract
type: "Int32"
```

Exact native sandbox_check return.

### errno {errno: field}

```contract
type: "Int32"
```

Native errno after clearing it before the call.

### allowed {allowed: field}

```contract
type: "Bool"
```

True exactly when native rc is zero.

### denied {denied: field}

```contract
type: "Bool"
```

True exactly when native rc is nonzero, including native errors.

## Direct argument error {standalone_error: subject}

```contract
record: "ValidatorDirectError"
as: "standalone_error"
```

### kind {kind: field}

```contract
type: "String"
```

sb_api_validator_error identifies a JSON-mode argument refusal.

### schema_version {schema_version: field}

```contract
type: "Int32"
```

Version 1 of this direct JSON object.

### error {error: field}

```contract
type: "String"
```

pid_missing, missing_args, bad_filter, unexpected_filter_value_for_none, missing_filter_value or unexpected_extra_args names the reached refusal.

### pid {pid: field}

```contract
type: "Int32"
optional: true
```

Parsed PID, or -1 for pid_missing; omitted for bad_filter.

### filter {filter: field}

```contract
type: "String"
optional: true
```

Rejected filter spelling for bad_filter; omitted for other errors.
