# PolicyWitness wire contracts

[contract.json](contract.json) owns every version number that crosses a process
boundary. `python3 docs/generate_contract.py` copies the numbers into the code
and documents listed below; `--check` verifies the copies without writing. The
build runs the check before compiling. Nothing reads the JSON at run time; the
controller embeds it at compile time so `policy-witness --version` can report it.

<!-- BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py) -->
Current wire contracts: request schema 1, response schema 10, worker ABI 7, controller envelope 3. Each number is a separate contract. `docs/contract.json` owns all four, and generated copies carry them into code and documents.
<!-- END GENERATED CONTRACT VERSIONS -->

<!-- BEGIN GENERATED CONTRACT TABLE -->
| Contract | Version | Generated copies |
| --- | --- | --- |
| request schema (`request_schema`) | 1 | [`PWContract.requestSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`REQUEST_SCHEMA`](../tests/lib/contract.py) |
| response schema (`response_schema`) | 10 | [`PWContract.responseSchema`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`RESPONSE_SCHEMA`](../tests/lib/contract.py) |
| worker ABI (`worker_abi`) | 7 | [`PW_PROBE_RUNNER_ABI_VERSION`](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PWShmLayout.abiVersion`](../runner/Sources/PWRunnerCore/CWorker.swift); [`WORKER_ABI`](../tests/lib/contract.py) |
| controller envelope (`controller_envelope`) | 3 | [`SCHEMA_VERSION`](../controller/src/json_contract.rs); [`CONTROLLER_ENVELOPE`](../tests/lib/contract.py) |
<!-- END GENERATED CONTRACT TABLE -->

## What each number identifies

- **Request schema**: the specimen JSON the controller hands the runner
  (`PWRunnerRunSpec`). The runner reports it back unchanged.
- **Response schema**: the runner reply (`PWRunnerRunResult`). It tells a
  reader of a stored reply which rules apply; `tests/lib/consumer.py` branches
  on it. Older replies stay decodable and keep their original meaning.
- **Worker ABI**: the shared-memory layout between the XPC host and
  `pw-probe-runner`. Host and worker ship together inside each XPC bundle, so
  this is a tripwire, not a live compatibility boundary: the worker refuses a
  mismatched header before applying any policy. The reply repeats it in
  `runner_subprocess.worker_evidence.abi_version`.
- **Controller envelope**: the top-level JSON that `policy-witness` prints.
  The controller forwards the runner reply inside it without version coercion.

## Tests assert minimums, not the current number

A test states the lowest version that carries the fields it inspects, for
example `schema_version >= 7` for a check that reads `comparison`. A bump then
touches the manifest plus the tests for the change that caused it, and nothing
else. Exactly one check, in the default `smoke` suite, compares a built app
against the exact manifest values; it is the check that a build carries the
numbers this repository believes it does.

## When a number moves

Bump a number only when the rules for reading change. Adding a field never
bumps: an absent field means unknown, never false, so a reader written for the
previous number stays correct. A bump is required when a field is removed, its
type or meaning changes, or readers must now enforce a new requirement, as they
did when ordering became mandatory at response 8. Because host and worker ship
together, the worker ABI bumps on any change to the shared-memory layout or the
handshake over it; that keeps the mismatch tripwire meaningful.

## Naming numbers in prose

Describe current behavior without a number. Name a number only in a clause about
the past, such as "replies before schema 8 carry no `comparison.order`". Those
sentences stay true after every later bump. The generated sentence above is the
one place that states the current numbers. The table below is the one place that
says what each older number lacked.

## Reading older replies

A stored reply keeps the meaning it had when written. The response number says
which of these rules apply; every later number keeps the earlier rows.

| Response | Introduced |
| --- | --- |
| 1 | Initial shape. |
| 2 | Optional `steps[].sandbox_check.path_diagnostics` on path-filter checks. |
| 3 | Host/worker split: top-level `pid` is the sandboxed worker when `runner_subprocess` is present, and `runner_subprocess` carries the worker exit status observed by the unsandboxed host. |
| 4 | `validator_subprocess` for the `sb_api_validator --batch` child, and nullable `steps[].drift`. |
| 5 | Explicit `steps[].deny_signal: null` (channel unobserved) and evidence-based execution classification without sandbox-cause inference. Older signal objects stay decodable. |
| 6 | Nullable `steps[].sandbox_check.pid` when no worker was spawned, and `runner_subprocess.worker_evidence`. |
| 7 | Per-step `comparison` with scope and limitations, submitted attempt intent (`requested_kind`, `requested_action`) and host path provenance. Older replies keep their original `drift` and lack these derivations. |
| 8 | Ordered comparisons (`comparison.order`, `runner_subprocess.ordering`), the `runner_reporting_failed` reply with `reporting_failure`, and optional `validator_spawn_failure`. Absence of the spawn record in older replies is unknown, not a successful spawn. |
| 9 | `sandbox_check.effective_filter_value` is gone; it always equaled `filter_value`. `path_diagnostics` names the forms equal to `input` in `same_as_input` and omits their keys, carries `realpath_resolved` and `firmlink_resolved` only when they differ (a string) or could not be derived (null), and no longer carries the `data_volume_form` heuristic. Each form is in exactly one of those states; equality means identical UTF-8 bytes. Conflicting or missing states are malformed; legacy omissions remain unreported. |
| 10 | `runner_subprocess.disposition`, the worker disposition record, is mandatory beside a worker subprocess, with the host facts `cleanup_trigger`, `grace_end` and `collection_basis`, and `steps[].attempt.lifecycle` with its `attempt:*` lifecycle limitations. Readers validate the record against the raw facts it cites and project from it; a subprocess without the record at this version is invalid, not a legacy omission. Omission in older replies is unreported. See tests/FAILURE-PROPAGATION-CONTRACT.md, "Worker disposition record". |

| Worker ABI | Introduced |
| --- | --- |
| 1 | Initial shared-memory header, step slots and policy text. |
| 2 | SBPL parameter slots. |
| 3 | Parameter capacity raised from 16 to 1,024. |
| 4 | Augments and the exec attempt runtime. |
| 5 | Compiled-profile capture region. |
| 6 | Progress/failure evidence header and diagnostic text region. |
| 7 | Host release and worker acknowledgement words in the header (the ordering barrier). |

| Controller envelope | Introduced |
| --- | --- |
| 1 | Initial shape. `data.sandbox_log_capture.window` recorded a trailing `last` lookback (`kind: "trailing"`), and `data.log_last` echoed the flag that set it. |
| 2 | Deny-log capture requests the runner client's own span: `window` carries `kind: "runner_client_span"`, the client's start and end milliseconds and the whole-second UTC `start`/`end` strings handed to `log show`; `last` and `data.log_last` are gone. Reversed clock readings retain the milliseconds with null bounds and `capture_status: "invalid_window"`, without invoking the observer. `runner_sandbox_diagnostics.permission_failures_without_record` names the steps whose attempt reported a permission-shaped failure that no captured event records. A reply for different or missing bounds or a trailing lookback is `window_mismatch`; raw observer evidence survives without candidate or diagnostic correlation. |
| 3 | `runner_sandbox_diagnostics` projects the worker disposition record: `termination_cause` names witnessed host cleanup (`host_sentinel_deadline`, `host_exit_grace_exhausted`, `host_cleanup_after_wait_error`, `host_cleanup_after_transfer_error`) instead of a blanket `unknown`, `stop_reason` carries the projected poll stop reason, `disposition_integrity` and `disposition_issues` report validation, and `process_disposition` adds `conflicting`, `withheld` and `unrecognized`. Legacy replies without the record keep the raw-status projection with `unknown` and `not_reported`. |

Request schema has stayed at 1.

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
