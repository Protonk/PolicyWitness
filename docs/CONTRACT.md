# PolicyWitness wire contracts

[contract.json](contract.json) owns every version number that crosses a process
boundary. `python3 docs/generate_contract.py` copies the numbers into the code
and documents listed below; `--check` verifies the copies without writing. The
build runs the check before compiling. Nothing reads the JSON at run time; the
controller embeds it at compile time so `policy-witness --version` can report it.

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 3, response schema 13, worker ABI 7, controller envelope 5. Each number is a separate contract. `docs/contract.json` owns all four, and generated copies carry them into code and documents.
<!-- END GENERATED CONTRACT VERSIONS -->

<!-- BEGIN GENERATED CONTRACT TABLE -->
| Contract | Version | Generated copies |
| --- | --- | --- |
| request schema (`request_schema`) | 3 | [`PWContract.requestSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`REQUEST_SCHEMA`](../tests/lib/contract.py) |
| response schema (`response_schema`) | 13 | [`PWContract.responseSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`RESPONSE_SCHEMA_VERSION`](../controller/src/json_contract.rs); [`RESPONSE_SCHEMA`](../tests/lib/contract.py) |
| worker ABI (`worker_abi`) | 7 | [`PW_PROBE_RUNNER_ABI_VERSION`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PWShmLayout.abiVersion`](../runner/Sources/PWRunnerCore/CWorker.swift); [`WORKER_ABI`](../tests/lib/contract.py) |
| controller envelope (`controller_envelope`) | 5 | [`SCHEMA_VERSION`](../controller/src/json_contract.rs); [`CONTROLLER_ENVELOPE`](../tests/lib/contract.py) |
<!-- END GENERATED CONTRACT TABLE -->

## What each number identifies

- **Request schema**: the specimen JSON the controller hands the runner
  (`PWRunnerRunSpec`). The runner reports it back unchanged.
- **Response schema**: the runner reply (`PWRunnerRunResult`). It tells a
  reader which rules apply; `tests/lib/consumer.py` and the controller accept
  exactly this number. `steps[].comparison` records the attempt channel's
  classified observation, the submitted-scope relations, the order PW
  established and the planner's exclusion or lifecycle limitations.
- **Worker ABI**: the shared-memory layout between the XPC host and
  `pw-probe-runner`. Host and worker ship together inside each XPC bundle, so
  this is a tripwire, not a live compatibility boundary: the worker refuses a
  mismatched header before applying any policy. The reply repeats it in
  `runner_subprocess.worker_evidence.abi_version`.
- **Controller envelope**: the top-level JSON that `policy-witness` prints.
  The controller forwards the runner reply inside it without version coercion.
  `data.specimen` is the dossier: request path, policy augmentation and
  imports, host facts, runner and app provenance, and hashes of any selected
  binary the app manifest does not describe; the raw runner reply, transport,
  diagnostics and log capture stay beside it.

## Supported versions

Semantic readers of runner responses and controller envelopes accept exactly
the versions in [contract.json](contract.json); another version is
unsupported. Raw transport retains the received bytes without interpreting
unsupported records. Stored evidence keeps its bytes; current semantic readers
reject unsupported versions. Request admission and the worker ABI follow their
own contracts.

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
[contract.json](contract.json). Bump the worker ABI on any change to the
shared-memory layout or handshake; because host and worker ship together,
that keeps the mismatch tripwire meaningful.

The generated sentence above is the one place that states the current numbers;
describe current behavior without repeating them in prose.

## Shape goldens

Two goldens under `tests/fixtures/contract/` notice a change that nobody
acknowledged. `response_shape.json` records, per object path, every key of the
field-complete reply fixture in `ReplyFailureTests` and its JSON type;
`runner_unit` compares the fixture's encoded shape with it. `abi_layout.txt` is
the compiled harvest of every size, offset and constant in the worker ABI
header; `runner_abi_layout` compares the current harvest with it. Any
difference fails the case and writes a candidate into the case's artifacts. The
failure says which of three things happened: the reply gained fields, which
needs no bump; a reply key was removed or changed type, or the ABI layout moved
under an unchanged number, which needs a bump first; or the manifest already
moved and only the golden is behind. Replacing the golden with the reviewed
candidate is the acknowledgement, and that diff is what reviewers watch.
The reply golden covers what the fixture populates; a new nested field must be
added to that fixture, as its comment already requires.

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
changes. `source_drift` verifies the copies and exercises the generator;
`runner_abi_layout`, `runner_unit` and the Rust unit tests compare the compiled
C, Swift and Rust values with the manifest.
