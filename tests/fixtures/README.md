# Fixtures

Fixtures are inputs and helper programs for test suites. Keep them small,
deterministic, and checked into the repo so tests are hermetic.

## Categories

- `validator/`: checked-in NDJSON validator program and partial-reply
  transcripts (EOF and malformed JSON), used by `runner_validator_failure`
  and the corresponding `witness_contract` entry points.
- `exec/`: shared C helper for controlled output, exit status, and process
  trees, plus OS identity/lifecycle and environment/descriptor inspection. Direct
  controls live in the `exec_fixture` suite.
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
