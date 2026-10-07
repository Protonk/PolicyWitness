# PolicyWitness wire contracts

[contract.json](contract.json) owns the request, response and controller-envelope
version numbers. `python3 docs/generate_contract.py` copies the numbers into the code
and documents listed below; `--check` verifies the copies without writing. The
build runs the check before compiling. Nothing reads the JSON at run time; the
controller embeds it at compile time so `policy-witness --version` can report it.

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 4, response schema 15, controller envelope 7. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

<!-- BEGIN GENERATED CONTRACT TABLE -->
| Contract | Version | Generated copies |
| --- | --- | --- |
| request schema (`request_schema`) | 4 | [`PWContract.requestSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`REQUEST_SCHEMA_VERSION`](../controller/src/json_contract.rs); [`REQUEST_SCHEMA`](../tests/lib/contract.py) |
| response schema (`response_schema`) | 15 | [`PWContract.responseSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`RESPONSE_SCHEMA_VERSION`](../controller/src/json_contract.rs); [`RESPONSE_SCHEMA`](../tests/lib/contract.py) |
| controller envelope (`controller_envelope`) | 7 | [`SCHEMA_VERSION`](../controller/src/json_contract.rs); [`CONTROLLER_ENVELOPE`](../tests/lib/contract.py) |
<!-- END GENERATED CONTRACT TABLE -->

## What each number identifies

- **Request schema**: the specimen JSON the controller hands the runner
  (`PWRunnerRunSpec`). The marker identifies the accepted input contract,
  independently of implementation revisions. Both controller and runner
  require the current value before interpreting the request. The reply carries
  its own response version; it does not echo the request version.
- **Response schema**: the runner reply (`PWRunnerRunResult`). It tells a
  reader which rules apply; `tests/lib/consumer.py` and the controller accept
  exactly this number. `steps[].comparison` records the attempt channel's
  classified observation, the submitted-scope relations, the order PW
  established and the planner's exclusion or lifecycle limitations.
- **Controller envelope**: the top-level JSON that `policy-witness` prints.
  The controller forwards the runner reply inside it without version coercion.
  `data.specimen` is the dossier: request path, policy augmentation and
  imports, host facts, runner and app provenance, and hashes of any selected
  binary the app manifest does not describe; the raw runner reply, transport,
  diagnostics and log capture stay beside it. The same number versions the
  **envelope frame**: the outer object every controller-family binary prints
  (`kind`, `schema_version`, `generated_at_unix_ms`, `build`, `result`,
  `data`), rendered by [json_contract.rs](../controller/src/json_contract.rs),
  which `sbpl-check` and `sandbox-log-observer` compile in by `#[path]`. The
  frame therefore also appears on the helper envelopes the controller nests
  unchanged: `data.policy_check.envelope` from `sbpl-check` and
  `data.sandbox_log_capture.observer` from `sandbox-log-observer`. Inside the
  observer's frame, `data.observer_schema_version` identifies the observer's
  own report; the two numbers name different things and move independently.

## Supported versions

Semantic readers of runner responses and controller envelopes accept exactly
the versions in [contract.json](contract.json); another version is
unsupported. Raw transport retains the received bytes without interpreting
unsupported records. Stored evidence keeps its bytes; current semantic readers
reject unsupported versions. Request admission and the worker ABI follow their
own contracts.

Historical runs are retained as evidence with their original producer and build
provenance. PW does not translate their judgments or normalize them into current
records. Rerun the specimen with current PW to obtain usable current evidence.
Comparisons of current-format runs, including runs on different macOS versions,
remain useful; their worker identities need not match. Identity equality is a
requirement between components of one worker execution, not between experiments.

Persisted runner-installation recovery is separate from run interpretation.
The registry loader accepts the retired `machme` and `debuggable` kind spellings
so existing owned launchd jobs can still be listed and removed. Removing those
aliases would make the registry unreadable and strand cleanup. New runner-kind
input accepts `standard` and `byoxpc`; the recovery aliases do not admit any
historical run format. Current accepted request spellings retain their own
input contract.

A reader checks a version before interpreting its record. Missing or
noninteger version fields are malformed; other integer versions are
unsupported. For an envelope, the envelope version is checked first, then any
nonnull runner reply. An unsupported document yields one version error, with
no downstream shape errors and no recovered claims. The controller reports an
unsupported or malformed reply as `unsupported_runner_response` or
`malformed_runner_response` with the reply retained; `tests/lib/consumer.py`
reports `unsupported`. Both read the numbers through generated copies of
this manifest, so a bump touches the manifest, the generated copies and the
fixtures that carry the number. Exactly one check, in the default `smoke`
suite, compares a built app against the manifest values; it is the check that
a build carries the numbers this repository believes it does.

## When a number moves

For responses and envelopes, bump a number when the rules for reading change:
a field removed, its type or meaning changed, or a new requirement placed on
readers. An added field alone
does not require a bump. An absent field means unknown, never false. An
additive contract change may also carry a bump, recorded in
[contract.json](contract.json).

The generated sentence above is the one place that states the current numbers;
describe current behavior without repeating them in prose.

## Accepted input contract

The request marker names the shapes and meanings described in
[the specimen format](PolicyWitness.md#specimen-format), not a runner build.
`schema_version` must be an integer-valued JSON number equal to the current
request schema. Other values are rejected explicitly with the expected value;
there is no older-request adapter or version negotiation. The controller checks
before runner selection or augment resolution; the XPC service independently
checks before worker or validator creation.

The existing Swift `Codable` types remain the parser. Their `CodingKeys` also
define the accepted fields of every request object: the root, policy, each
probe step, sandbox check, filter, attempt and `_test_overrides`. An unknown key
is a `bad_request` with a bounded field path, rather than an ignored option.
For example, `policy.capture_applied_profiel` is rejected. `policy.params`
is a dictionary of caller-chosen names to string values; its names are data,
not closed object fields. Missing required fields and wrong value types are
also rejected. Optional null values have the same meaning as absence.

The controller additionally accepts [runner selection](../controller/README.md#runner-selection-external-entitlements)
and resolves `policy.augments`. It validates selector types and every required
entitlement, including shadowed aliases; unknown nested selector fields are
errors. A non-null nested selector value takes precedence over its top-level
alias, including an explicit empty entitlement list. Selection fields are
removed before XPC delivery and their resolved meaning is recorded in runner
provenance. Direct XPC requests reject them. Nonempty augment lists require a
string `sbpl_source`; the controller splices the named fragments and strips
the list. A direct XPC request with unresolved fragments is rejected.

Meaning checks reject unknown attempt kind/action pairs and filter kinds before
any worker or validator is created. A non-null `attempt.args` is accepted only
for `exec/spawn`; a non-null `filter.value` is refused for `kind: "none"`;
`capture_nonce` requires enabled `capture_applied_profile`. Enabled capture
requires a valid nonce. Step IDs must be distinct and exec targets absolute.
Known operation/filter pairs excluded from prediction still produce explicit
`prediction_unavailable` observations, with supported attempts executed normally.
Operation names passed to `sandbox_check` remain OS queries; the validator can
report `unsupported_operation`. Query and attempt scopes need not match.

Changes fall into four categories:

| Change | Contract consequence |
| --- | --- |
| Replace the `probe_plan` array with an object, require a new field, remove an accepted spelling, or refuse an accepted combination | Callers must change their requests; use a new request contract value and reject unsupported values explicitly. |
| Change what `action: "open_read"` does | A new action spelling or request contract is required; do not reinterpret the same request as a different operation. |
| Add an optional field or action while preserving existing requests and meanings | The request value can stay stable. Older builds reject unknown fields and unsupported actions explicitly; acceptance by a newer build does not promise acceptance by an older one. |
| Fix parameter transfer or another implementation defect to honor the documented request | Keep the request value; build provenance identifies the implementation and results can change. |

[Runtime admission limits](LIMITS.md) are separate from this syntax and meaning.
For example, a structurally valid plan can exceed the worker's step capacity;
the refusal names the field, actual count and maximum before any attempts.
Raising capacity accepts more plans; lowering it can refuse previously runnable
requests. The caller decides whether to revise the specimen or use a build with
more capacity; PW never truncates or reinterprets the plan. Capacity changes must
be documented and tested even when they do not change the input grammar.

Maintenance consists of the existing decoder/selector fields, their meaning
in the guide, and acceptance/refusal tests. No additional schema language or
parser generator is used. These rules protect requested intent; they do not
promise identical sandbox observations across builds or macOS versions.

The [developer lesson](REQUEST-GRAMMAR.md) works through the same specimens
used by Swift decoding/validation tests and signed CLI/direct-XPC controls.

### Structured request refusals

Malformed JSON, request versions, selectors, augments, field structure and
meaning, and capacity refusals report `bad_request`; the controller exits 1.
Unreadable request files, unavailable runner installations and transport failures
remain tool/execution failures. The controller exposes `data.request_failure`;
when the runner refuses the request, this is an unchanged copy of the runner's
`request_failure`. It is optional additive response/envelope information: absence
means no structured diagnostic was supplied, never that execution succeeded.

The record has `code` and `path`, plus `expected_schema` for version-field
refusals. `path` is an array of object keys and decimal array positions, with
`[]` naming the root. It is `null` when the full location cannot be reported:
at most eight components of at most 63 UTF-8 bytes each are echoed. Refused
parameter keys are also withheld. Human-readable `error` is supplementary;
consumers use the code and path without parsing that prose.

| Codes | Meaning |
| --- | --- |
| `invalid_json` | The request could not be parsed as JSON. |
| `unsupported_schema` | The request marker names another contract. |
| `unknown_field`, `missing_field`, `missing_value`, `type_mismatch`, `invalid_value` | The named input is unknown, absent, null where required, mistyped or invalid. |
| `unsupported_policy_format`, `missing_policy_source` | The policy's structural prerequisites are absent. |
| `unknown_filter_kind`, `missing_filter_value`, `empty_operation` | A sandbox query cannot be formed from the request. |
| `unsupported_attempt`, `relative_exec_target`, `duplicate_step_id` | The plan cannot be carried out with its submitted meaning. |
| `inapplicable_field`, `invalid_capture_nonce` | A supplied field cannot take effect or satisfy its prerequisites. |
| `conflicting_selector`, `unresolved_augments`, `augment_unavailable` | Controller-owned instructions conflict, remain unresolved at XPC, or name unavailable fragments. |
| `admission_refused` | Capacity or native-string admission failed; `admission_failure` retains the field, actual count, maximum and applicable positions. |

These refusals contain no steps or child-process observations. The XPC host
itself may have launched to decode a request. Capacity checks precede meaning
checks; diagnostics identify one refusal, not an exhaustive list of defects.
Retain unfamiliar codes as unclassified refusals rather than guessing their cause.

## Internal host/worker identity

The XPC host and its bundle-local `pw-probe-runner` use an exact SHA-256 source
identity, generated by [generate_worker_identity.py](generate_worker_identity.py).
There is no worker ABI ordinal or compatibility negotiation. The build generates
the C, Swift and test copies before compilation and checks them again before
signing. `python3 docs/generate_worker_identity.py --check` verifies them without
writing; direct source-test builds can regenerate with the same command without
`--check`.

The digest covers sorted repository-relative paths and file contents, each
length-framed: all `.c`, `.h` and `.swift` files under
`controller/tools/pw_probe_runner/` and `runner/Sources/`, plus the generator,
`build.sh` and `runner/Package.swift`. Generated identity region bodies are
excluded to avoid self-reference. Discovery includes new helpers automatically.
This conservative scope includes the C wait and publication code, Swift release
and collection code, orchestration, ABI declarations and their host mirror.
Even comments or unrelated changes within those files change the identity;
there is no manual semantic-version judgment to make.

The shared header has a fixed bootstrap magic at byte 0 and 32 identity bytes
at byte 64. The worker checks the mapped region's size and these fields before
reading policy input, publishing evidence, or using layout-dependent fields.
An identity or magic mismatch exits with code 4 and no ready/applied/done
publication. The bootstrap magic also makes ordinal-era workers refuse the
header. The host checks the identity before decoding worker evidence and before
releasing attempts. These checks do not assert that a child validated the
header: `runner_subprocess.worker_evidence.abi_identity` records the
host-selected identity, including when no worker publication exists.

Equality establishes agreement on the selected source bytes. It does not prove
correct implementation, compiled layout agreement, identical compiler or SDK,
binary authenticity, runtime behavior, or sandbox cause. Compiled C/Swift layout
checks, signed artifact provenance, and lifecycle/order tests retain those
separate responsibilities. The hash is not a security authentication mechanism.

This exact-match requirement is confined to the jointly built host/worker pair.
The external runner XPC protocol and JSON request/response/envelope contracts
retain their own boundaries. Validator diagnostic JSON and observer reports
also keep their own contracts; they are consumed independently of this memory
interface.

## Shape goldens

Three goldens under `tests/fixtures/contract/` notice a change that nobody
acknowledged, and two of them are the readers' allowlists.
`response_shape.json` records, per object path, every key the runner reply
can carry and its JSON type, collected from the encoded documents of
`replyShapeDocuments()` in `ContractVersionTests` (the field-complete reply
fixture, its degraded reply, and production-shaped worker accounts resolved by
the real builders); `runner_unit` compares the current collection with it.
`envelope_shape.json` records the same for the controller envelope, from the
field-complete `kind: "run"` envelope a Rust unit test renders with every
optional object populated; the reply inside it is opaque to that golden because
the reply golden owns it, and the nested helper envelopes it carries
(`data.policy_check.envelope`, `data.sandbox_log_capture.observer`) are
compared with the helpers' own emitted shapes by their unit tests.
The JSON shape checks distinguish added fields (no bump needed), removed or
changed-type fields (bump first), and a manifest that already moved while its
golden is behind. A difference writes a candidate into the case's artifacts.
Replacing the golden with the reviewed candidate is the acknowledgement, and
that diff is what reviewers watch.

`abi_layout.txt` is the compiled harvest of every size, offset and layout constant
in the worker ABI header; `runner_abi_layout` compares the current harvest with
it. Layout changes fail the case and require reviewing the compiled geometry
candidate, with no ordinal bump. The source identity is checked separately and
is excluded from the layout golden, so protocol-only edits create no layout
acknowledgement chore.

The two shape goldens are the allowlists `tests/lib/consumer.py` reads
documents against: an unknown key at a recorded path is an error naming the
path, a present key must carry the golden's type (a recorded `null` constrains
nothing), and absence is allowed. A key appears in a golden because a producer
emitted it, so a new field reaches the readers only through the fixture that
records it. These response-shape checks in Python readers and golden comparisons
are separate from the closed request decoding described above.

For `data.policy_check`, the consumer validates the capture wrapper and applies
helper admission to its nested `envelope`. Admission requires `kind: "sbpl_check"`,
the envelope frame's exact current integer version and a nonempty string
`result.normalized_outcome`. An admitted envelope must have its outcome copied
into capture `status`, and its body is checked against the current helper shape.
Rejected parsed output under `status: "invalid_reply"` is opaque retained
evidence, including arrays and scalars; the current helper shape does not apply
to it. Transport failures may carry a null envelope. There is no interpretation
of historical helper schemas.

## Build stamp

The app version is a coordinate, not a contract, and nobody edits it. build.sh
derives it from git: `CFBundleShortVersionString` is the nearest `v*` tag,
`CFBundleVersion` the commit count, and `PWBuildDescribe`/`PWBuildCommit` the
exact source, with `-dirty` when the tree had uncommitted changes. The same four
values reach the controller at compile time and appear as `build` in every
envelope, and `policy-witness --version` prints them beside the contract
versions. Cutting a release is one annotated tag; the stamp then moves on every
commit for free, while the contract numbers move only under the rule above.
`PW_VERSION` and `PW_BUILD_NUMBER` override the derived values for builds made
outside a git checkout.

## Changing a number

Edit [contract.json](contract.json), run `python3 docs/generate_contract.py`
from the repository root, and commit the regenerated copies with the change
that needs them. `git log -- docs/contract.json` is the history of contract
changes. `source_drift` verifies the copies and exercises both generators;
`runner_unit` and the Rust unit tests compare compiled JSON versions with the
manifest. `runner_abi_layout` compares compiled C layout and identity with Swift
and the generated identity, independently of the JSON version manifest.
