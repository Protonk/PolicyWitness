# Fixtures

Fixtures are static inputs for test suites. Keep them small, deterministic, and
checked into the repo so tests are hermetic.

## Categories

- `pw_runner/`: minimal specimens for smoke/integration/opt-in runner paths
  (single-step SBPL cases and instrumentation examples).
- `runner_smoke/`: template-based fixtures used by smoke and runner verification.
- `blackbox_menagerie/`: SBPL sources, compiled blobs, and a case manifest
  (`cases/core.json`) sourced from PAWL evidence.
- `blackbox_e2e/`: per-case directories (`BBX-*`) with specimen templates and
  expected outcomes for strict evidence validation.
- `instrumentation/`: JSON fragments used with `--instrumentation` to exercise
  the instrumentation port.

## Adding fixtures

- Keep paths stable and avoid environment-specific values.
- Prefer minimal specimens unless the case requires a larger corpus.
- If a fixture implies a new contract, update the relevant suite README and
  `tests/INDEX.md`.
