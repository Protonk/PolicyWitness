# PolicyWitness wire contracts

[contract.json](contract.json) owns the request, response and controller-envelope
version numbers. `python3 docs/generate_contract.py` copies the numbers into the code
and documents listed below; `--check` verifies the copies without writing. The
build runs the check before compiling. Nothing reads the JSON at run time; the
controller embeds it at compile time so `policy-witness --version` can report it.

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 3, response schema 14, controller envelope 6. Each number is a separate contract. `docs/contract.json` owns these numbers; the internal host/worker boundary uses a generated source identity.
<!-- END GENERATED CONTRACT VERSIONS -->

<!-- BEGIN GENERATED CONTRACT TABLE -->
| Contract | Version | Generated copies |
| --- | --- | --- |
| request schema (`request_schema`) | 3 | [`PWContract.requestSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`REQUEST_SCHEMA`](../tests/lib/contract.py) |
| response schema (`response_schema`) | 14 | [`PWContract.responseSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`RESPONSE_SCHEMA_VERSION`](../controller/src/json_contract.rs); [`RESPONSE_SCHEMA`](../tests/lib/contract.py) |
| controller envelope (`controller_envelope`) | 6 | [`SCHEMA_VERSION`](../controller/src/json_contract.rs); [`CONTROLLER_ENVELOPE`](../tests/lib/contract.py) |
<!-- END GENERATED CONTRACT TABLE -->

## What each number identifies

- **Request schema**: the specimen JSON the controller hands the runner
  (`PWRunnerRunSpec`). Decoding requires an integer `schema_version`, but
  admission does not currently gate its value. The reply carries its own
  response version; it does not echo the request version.
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
  diagnostics and log capture stay beside it. The same number is the frame
  every controller-family binary prints (`kind`, `schema_version`,
  `generated_at_unix_ms`, `build`, `result`, `data`), so it also appears on
  the helper envelopes the controller nests unchanged:
  `data.policy_check.envelope` from `sbpl-check` and
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

Bump a number when the rules for reading change: a field removed, its type or
meaning changed, or a new requirement placed on readers. An added field alone
does not require a bump. An absent field means unknown, never false. An
additive contract change may also carry a bump, recorded in
[contract.json](contract.json).

The generated sentence above is the one place that states the current numbers;
describe current behavior without repeating them in prose.

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
records it. The Swift decoder keeps ignoring unknown keys; strictness lives in
the Python readers and the golden comparisons.

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
