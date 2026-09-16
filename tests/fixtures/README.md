# Fixtures

Fixtures are inputs and helper programs for test suites. Keep them small,
deterministic, and checked into the repo so tests are hermetic.

## Categories

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
- `caller_auth/`: disposable built-in XPC app copies, explicit signing and
  signature inspection, command capture, and process cleanup. Authorization
  expectations and independent file-effect checks belong to the smoke case.
- `byoxpc/`: ownership of a disposable signed runner through setup, partial
  installation, and verified removal; independent fake OS/CLI tools exercise
  failures without signing or installing a real service.
- `validator/`: checked-in NDJSON validator program and partial-reply
  transcripts (EOF and malformed JSON), used by `runner_validator_failure`
  and the corresponding `witness_contract` entry points.
- `exec/`: shared C helper for controlled output, exit status, and process
  trees, plus OS identity/lifecycle and environment/descriptor inspection. Direct
  controls live in the `exec_fixture` suite.
- `worker_harness/`: shared compiler recipe for the C-worker ABI harness and
  independent builder/harness stand-ins for shell setup controls.
- `pw_runner/`: minimal specimens for smoke/integration/runner suites and
  opt-in paths (single-step SBPL cases).
- `runner_smoke/`: template-based fixtures used by smoke and runner verification.
- `blackbox_menagerie/`: SBPL sources and a case manifest (`cases/core.json`)
  sourced from PAWL evidence.
- `blackbox_e2e/`: per-case directories (`BBX-*`) with specimen templates and
  expected outcomes for strict evidence validation, plus synthetic envelopes
  under `checker/` for independent controls of the evidence checker.

## Adding fixtures

- Keep paths stable and avoid environment-specific values.
- Prefer minimal specimens unless the case requires a larger corpus.
- If a fixture implies a new contract, update the relevant suite README and
  the suite-coverage table in `tests/README.md`.

The `dispatcher` fixtures include `repository.py` (copies the public runner and
writes a caller-supplied catalog), `selection.sh`/`selection.py` (independent
execution receipts and controlled evidence), `controller.py` (a runnable stub
that records its own path, arguments, and bundle-local marker), and the
reconciliation fault scripts. Two stub bundles distinguish an explicit app
selection from a usable default. The setup fixture is also used by Python
startup controls; it contains no expected selections or result-checking logic.
`cancellation.sh`/`cancellation.py` supply standard cases and a helper that ignores
SIGINT. They use the exec fixture's existing readiness/ping/release protocol;
the cancellation checker reuses its kernel process-exit observer.
`artifacts.py` supplies fake signed bundles and an independent file-seal command
only inside fixture repositories. The real inspector still parses and checks
their manifests and inventories. Real signing controls use disposable copies
through `caller_auth/bundle.py`; caller-auth and BYOXPC both reuse the inventory
in `tests/lib/artifact.py` to protect their source app.
