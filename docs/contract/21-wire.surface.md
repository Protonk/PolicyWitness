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

### Primitive reader coverage {reader_coverage: gap}

```contract
kind: "evidence"
```

The current Rust controls directly cover scalar ranges/booleans/UTF-8, record ID/tag/required-field faults, incomplete prefixes, trailing bytes, fingerprint precedence and shared list/string storage charging. The independently written Python controls additionally exercise variant, map order, impossible count, byte-kind and nesting faults. Equivalent Rust malformed-container controls and a host-writer frame-cap failure observation remain open evidence items.

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

### Repeated query keys {duplicate_keys: gap}

```contract
kind: "behavior"
```

The native batch parser currently accepts repeated recognized keys and uses the last parsed string. Host query serialization emits each key once. Alignment with the other request decoders’ duplicate-key behavior and a shared acceptance policy remain unresolved.

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

### Direct-mode meaning and input issues {meaning: gap}

```contract
kind: "behavior"
```

The direct JSON `denied` Boolean means rc is nonzero, including a native error; it has a broader meaning than batch outcome deny, which requires rc 1 and errno zero. The RAW parser also accepts an empty numeric suffix as zero. Batch’s filter-value grammar treats only the name NONE as valueless, whereas direct mode treats every numeric-zero filter as valueless; a batch RAW:0 value is therefore accepted then unused by the native call. Direct arguments are passed as C strings without batch’s UTF-8 validation. Whether these direct and batch conventions should be aligned remains unresolved.

### Direct-command support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "int main("}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "parse_pid"}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "resolve_filter_type_id"}, {"path": "controller/tools/sb_api_validator/sb_api_validator.c", "symbol": "print_error"}, {"path": "docs/build.json", "symbol": "sig_validator"}]
pins: "Direct argv branches establish parsing, mode-specific output, filter resolution and exit selection; the build inventory establishes the shipped helper location."
context: "Read complete main/parse/filter/error-printer branches and the signed app helper inventory."
limits: "Source reading only. Existing discovery harness calls exercise RAW JSON output for investigations, but a dedicated independent direct-mode grammar/status/error/exit corpus has not been credited here."
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
