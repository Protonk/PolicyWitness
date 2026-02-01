# `tests/` (test runner + suites)

This directory contains the repository test harness. The test suite is organized to answer three questions:

1. Does the built `dist/PolicyWitness.app` basically work end-to-end?
2. Did we break a contract (CLI shape, evidence artifacts, JSON output schema)?
3. Can we reproduce known or suspected sandbox anomalies?

The harness is machine-readable: every test writes structured JSONL events and a per-run summary under `tests/out/`.

Related docs:

- CLI contract: `controller/README.md`
- Runner architecture: `runner/README.md`
- Signing/build: `SIGNING.md`
- Coverage map: `tests/INDEX.md`
- Fixtures catalog: `tests/fixtures/README.md`
- Opt-in registry: `tests/OPT_IN_TESTS.md`

## How to run

Build first (signed pipeline):

```sh
make build
```

Then run tests:

```sh
make test
# or:
./tests/run.sh --all
./tests/run.sh --suite preflight
./tests/run.sh --suite unit
./tests/run.sh --suite integration
./tests/run.sh --suite runner_debuggable
./tests/run.sh --suite runner_byoxpc
./tests/run.sh --suite runner_machme
./tests/run.sh --suite anomalies
./tests/run.sh --describe --all
```

Opt-in tests live under `tests/suites/runner_*/opt_in/` and are listed in `tests/OPT_IN_TESTS.md`.
Compatibility wrappers remain under `tests/suites/opt_in/`.
Runner suites that install launchd services (`runner_byoxpc`, `runner_machme`) require a logged-in GUI session.

## What We Cover / What We Promise

Baseline (default in `--all`):
- `preflight`: codesign/entitlements inventory matches the built bundle.
- `unit`: controller unit logic passes.
- `integration`: CLI contract + runner envelope work end-to-end for simple specimens.
- `runner_debuggable`: smoke + blackbox coverage through the built-in debuggable runner.

Extended (opt-in; host-dependent skips are normal):
- `runner_byoxpc`: smoke + blackbox coverage through a BYOXPC runner.
- `runner_machme`: smoke + blackbox coverage through a MachMe runner.

Diagnostic:
- `anomalies`: passes only when a known OS anomaly is reproduced.

Opt-in:
- scripts under `tests/suites/runner_*/opt_in/` (see `tests/OPT_IN_TESTS.md`).

For a compact coverage map, see `tests/INDEX.md`. For invariants and fixtures,
see `tests/suites/<suite>/README.md`.

## Suites

- `preflight`: codesign/entitlements inspection only (no execution)
- `unit`: Rust unit tests (`cargo test --bins`)
- `integration`: Rust integration tests (`cargo test --tests`), primarily `controller/integration/cli_contract.rs`
- `runner_debuggable`: smoke + blackbox coverage via the built-in debuggable runner
- `runner_byoxpc`: smoke + blackbox coverage via a BYOXPC runner (opt-in)
- `runner_machme`: smoke + blackbox coverage via a MachMe runner (opt-in)
- `anomalies`: structured reproductions of alleged system bugs (tests pass when the anomaly is reproduced)

Shared runners (invoked by runner suites, still runnable directly):
- `smoke`: end-to-end scripts against a built `dist/PolicyWitness.app`
- `blackbox_menagerie`: SBPL end-to-end cases copied from PAWL evidence
- `blackbox_e2e`: end-to-end runner black-box cases (specimen in, JSON out, strict evidence checks)

Anomalies are intentionally inverted: a test passes only when the anomaly is observed. Use messages of the form `Anomaly: <allegation> -- <observed behavior>` so the logs stay self-describing.

Anomalies set `PW_TEST_QUIET=1` so they emit only the final anomaly note; they are feelers rather than a full suite narrative.

## Blackbox menagerie

End-to-end specimen runs sourced from local copies of PAWL evidence. The suite
covers SBPL ingestion, probe execution, and evidence
correlation; it includes negative controls and canonicalization-boundary cases
where mismatches are recorded as evidence. Compiled-blob cases may skip when
profile registration is not permitted on the host. See
`tests/suites/blackbox_menagerie/README.md` for suite invariants and fixtures.

## Harness note: sandboxed automation environments

Some automation harnesses run commands inside an OS sandbox. In that situation, specimen execution and unified-log based evidence capture can fail for reasons unrelated to PolicyWitness; re-run from a normal Terminal (or with escalation) before diagnosing PolicyWitness itself.

## Output contract (`tests/out/`)

Every invocation of `tests/run.sh` overwrites the prior run output so tooling can read stable paths:

```text
tests/out/
  run.json
  events.jsonl
  suites/<suite>/<test_id>/
    report.json
    events.jsonl
    artifacts/...
```
