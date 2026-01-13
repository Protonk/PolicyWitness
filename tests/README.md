# `tests/` (test runner + suites)

This directory contains the repository test harness. The test suite is organized to answer two questions:

1. Does the built `PolicyWitness.app` basically work end-to-end?
2. Did we break a contract (CLI shape, evidence artifacts, JSON output schema)?

The harness is machine-readable: every test writes structured JSONL events and a per-run summary under `tests/out/`.

Related docs:

- CLI contract: `controller/README.md`
- Runner architecture: `runner/README.md`
- Signing/build: `SIGNING.md`

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
./tests/run.sh --suite smoke
```

Opt-in tests live under `tests/suites/opt_in/` and are listed in `tests/OPT_IN_TESTS.md`.

## Suites

- `preflight`: codesign/entitlements inspection only (no execution)
- `unit`: Rust unit tests (`cargo test --bins`)
- `integration`: Rust integration tests (`cargo test --tests`), primarily `controller/tests/cli_integration.rs`
- `smoke`: end-to-end scripts against a built `PolicyWitness.app`

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
