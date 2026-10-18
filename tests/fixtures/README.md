# Fixtures

Fixtures are inputs and helper programs for test suites. Keep them small,
deterministic, and checked into the repo so tests are hermetic.

## Categories

- `contract/`: goldens for the wire contracts: the reply shape
  (`response_shape.json`, every key the encoder emits across the field-complete
  fixture and its production-shaped companions, checked by `runner_unit`), the
  controller envelope shape (`envelope_shape.json`, from the field-complete
  `kind: "run"` envelope a Rust unit test renders, with the helper envelopes it
  nests checked by the helpers' own tests) and the compiled worker ABI layout
  harvest (`abi_layout.txt`, checked by `runner_abi_layout`). The two shape
  goldens are the allowlists `tests/lib/consumer.py` validates documents
  against. A failing comparison writes a candidate into the case artifacts;
  replace the golden after review, and bump the number in `docs/contract.json`
  first when the failure says so. See `docs/CONTRACT.md`.
  `compiled_profile.json` supplies independent valid and invalid nested receipt
  contexts to Swift decoding, Rust reply admission and Python consumer controls.
  `phase_collection.json` supplies hand-reviewed compatible and contradictory
  collection/disposition observations to the Swift encoder, Rust disposition
  reader and Python consumer/oracle controls. Accepted failures include driver
  setup, native spawn failure and unconfirmed child cleanup.
  `evidence_types.json` supplies malformed and valid neighboring delivery and
  validator records to all three readers, including scalar types, integer
  bounds, independent cleanup and mixed-type association issues. Its patches
  apply to the retained issuer-abnormal capture; they are constructed controls.
  `exec_observation.json` supplies independent collection, signal-request and
  final-wait combinations to Swift ordinary-reply decoding/encoding, Rust
  disposition admission and Python consumer controls. Cases include unknown
  metadata, successful signalling without reap, native versus local errors,
  signed stream masks, malformed types/ranges and conflicting branches. These
  constructed facts are not native process observations.
  `path_diagnostics.json` contains independent compact path states,
  Unicode byte distinctions and malformed representations shared by Swift
  encoding/decoding, Rust forwarding and Python consumer checks.
- `dispatcher/`: controlled suite runners and evidence alterations exercised
  through the real `tests/run.sh` in isolated fixture repositories.
- `release/`: independent Apple/tool responses and execution receipts for release
  continuation and archive acceptance, plus real hung command trees for deadline
  controls; no real submission, signing, or PW run.
- `shell_case/`: independent builder/checker commands, shell cases, and
  controlled child scripts for Python startup, prerequisite, result-finalization, log/report,
  and wrapper execution controls in `shell_helpers`.
- `capture/`: independent CLI-shaped byte emitter with a socket gate for
  capture, exit-status, timeout, and overlapping-run controls in `run_capture`.
- `deny_capture/`: an observer transport fixture with fixed event timestamps;
  Rust tests pass the real outgoing interval arguments through Python's date
  parser to check padding, inclusion and exclusion without kernel-log delivery.
  The committed real log archive and independent manifest supply the required
  OS predicate-selection oracle, including nonempty positives and negatives
  checked before parsing. Its [README](deny_capture/README.md) records corpus,
  hashes, isolated generation and verified readers. Default tests never generate
  or download a replacement archive.
- `caller_auth/`: disposable built-in XPC app copies, explicit signing and
  signature inspection, command capture, and process cleanup. Authorization
  expectations and independent file-effect checks belong to the smoke case.
- `byoxpc/`: ownership of a disposable signed runner through setup, partial
  installation, and verified removal; independent fake OS/CLI tools exercise
  failures without signing or installing a real service.
- `validator/`: checked-in NDJSON validator program and partial-reply
  transcripts (EOF, malformed JSON and signal), plus an independent native
  bridge with acknowledged query/emission/closure gates. Used by
  `runner_validator_failure`, `validator_bridge` and `witness_contract`.
- `exec/`: shared C helper for controlled output, exit status, and process
  trees, plus OS identity/lifecycle and environment/descriptor inspection. Direct
  controls live in the `exec_fixture` suite.
- `sandbox_extensions/`: independent signed native issuer/worker experiment with
  transient token transport, fresh file-access evidence and allocation controls;
  see its [README](sandbox_extensions/README.md).
- `extension_controls/`: production issuer/worker boundary substitutions with
  transient independent receipts for native interruption and token confinement;
  see its [README](extension_controls/README.md).
- `path_query/`: independent signed native target for direct shipped-validator
  queries, path resolution and file-operation observations; see its
  [README](path_query/README.md). It does not implement PW's phase protocol.
- `host_setup/`: disposable Swift host copies with native setup substitutions and
  an independent child descriptor observer; see its [README](host_setup/README.md).
- `launch_descriptor/`: copied host drivers with independent evidence/decoy
  write challenges, exact descriptor reuse and native mapping teardown
  observations; see its [README](launch_descriptor/README.md).
- `worker_harness/`: shared compiler recipe for the C-worker ABI harness and
  independent builder/harness stand-ins for shell setup controls.
- `worker_lifecycle/`: test-only ABI producer for `runner_unit` host polling,
  cleanup and process-status controls. It never applies a sandbox; tests own
  cleanup of children deliberately left unreaped by OS-call fault controls.
- `pw_runner/`: minimal specimens for smoke/integration/runner suites and
  opt-in paths (single-step SBPL cases).
- `runner_smoke/`: template-based fixtures used by smoke and runner verification.
- `blackbox_menagerie/`: SBPL sources and a case manifest (`cases/core.json`)
  sourced from PAWL evidence.
- `blackbox_e2e/`: per-case directories (`BBX-*`) with specimen templates and
  expected outcomes for strict evidence validation, plus synthetic envelopes
  under `checker/` for independent controls of the evidence checker.
- `comparison/`: the comparison-record scenario matrix. `matrix.json` holds
  every S, B, C and T row with its specimen inputs, the raw channel inputs the
  Swift unit reader feeds to `comparisonEvidence(...)`, the raw fields the
  live case asserts beside the record, and the expected current-response
  `comparison` object; `stub_validator.py` is specimen B's steered validator,
  and `build.sh` compiles the exit-status helpers (`helper_status.c`) the spawn
  rows copy into the scenario root, named in `PW_COMPARISON_HELPER_FIXTURE`.
  Its [README](comparison/README.md) records the placeholder convention, the
  files each specimen needs and the row provenance. `baseline_response12/`
  holds the specimens, raw replies and match reports that verified the rows
  against the response 12 producer; its
  [README](comparison/baseline_response12/README.md) records that method.
  Readers: `witness_contract/comparison_matrix` (live) and
  `runner_unit`'s `ComparisonEvidenceTests` (unit).

## Adding fixtures

- Keep paths stable and avoid environment-specific values.
- Prefer minimal specimens unless the case requires a larger corpus.
- If a fixture implies a new contract, update the relevant suite README and
  the suite-coverage table in `tests/README.md`.

The `dispatcher` fixtures include `repository.py` (copies the public runner and
writes a caller-supplied catalog), `selection.sh`/`selection.py` (independent
execution receipts and controlled evidence), `controller_stub.c` (a runnable
Mach-O stub that records its own path, arguments, and bundle-local marker),
and the reconciliation fault scripts. Two stub bundles distinguish an explicit app
selection from a usable default. The setup fixture is also used by Python
startup controls; it contains no expected selections or result-checking logic.
`cancellation.sh`/`cancellation.py` supply standard cases and a helper that ignores
SIGINT. They use the exec fixture's existing readiness/ping/release protocol;
the cancellation checker reuses its kernel process-exit observer.
`fixture_bundle.py` lays out fake signed bundles around compiled Mach-O stubs
(`host_clean.c`, `host_imports_sandbox.c`, `worker_imports_clock.c`,
`worker_continuous_clock.c` and `controller_stub.c`, built by `build.sh` once
per suite run and named in `PW_DISPATCHER_HOST_FIXTURE`; a worker stub can
replace the clean stub at the worker path only) and
writes a complete full-build provenance record it authors: nominal toolchain
values, the stand-ins' hashes and load commands read with its own `otool`
parse, and the ad hoc signature facts their linker signatures carry, which the
inspector compares with `codesign -dvv`. `retention_case.py` can also start a
grandchild beyond itself that passes on, or drops, the checkout lock
descriptors, for the dispatcher's lock-lifetime control;
`seal_tool.py` is the independent file-seal command installed only inside
fixture repositories; it imports nothing but the standard library. The real
inspector still parses and checks their manifests, records and inventories. Real signing controls use disposable copies
through `caller_auth/bundle.py`; caller-auth and BYOXPC both reuse the inventory
in `tests/lib/artifact.py` to protect their source app.

`worker_lifecycle` includes worker progress/failure/diagnostic and closed-input
controls plus production C-main native-call/mapping companions. See its README
for the attribution and cleanup boundaries.

Validator transcript variants cover invalid UTF-8, incomplete predictions,
unfamiliar diagnostics and duplicate/unexpected IDs. The worker lifecycle build
also produces a `.validator` companion for actual host driver lifecycle and pipe
controls. [Fixture contract](worker_lifecycle/README.md),
[transcript contract](validator/README.md).

`diagnostic_transport/` supplies independent JSON oracles and C fixture literals
for open-code preservation through ABI decoding, runner/client/controller
forwarding, validator diagnostics and helper receivers. The fixture establishes
transport only; see its README for structural and competing-failure controls.
