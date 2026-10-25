# unit

Rust unit tests and formatting for the controller crate.

## Invariants

- `rust.unit` runs `cargo test --bins`. Controlled orchestration checks count
  manifest loads and client calls through the real `run` path. The field-complete
  envelope is compared with `tests/fixtures/contract/envelope_shape.json`;
  helper binaries check their nested subtrees.
- `rust.fmt` runs `cargo fmt -- --check` and fails on any difference; fix with
  `cargo fmt` in `controller/`.
- `rust.disposition_reds` selects the four disposition record controller tests by
  their full names with `cargo test --bin policy-witness -- --include-ignored --exact`
  (status conflict, projection and withholding of the carried record).
- `rust.byoxpc_reds` selects the two BYOXPC selection tests the same way: a required
  entitlement key present with value `false` is refused, naming the worker and key.
- Both selections also run inside `rust.unit`. Each wrapper requires all named
  tests to report success, the exact test count, and a zero Cargo exit status.
  Missing/ignored results, wrong selections, test failures and build/equipment
  failures fail the case. Raw Cargo diagnostics are retained without classifying
  assertion messages.
- No case requires a built `.app` bundle.

`execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields`
in [run_flow.rs](../../../controller/src/run_flow.rs) exercises completion,
assembly and serialization for successful, signaled, degraded and absent-worker
replies, including ordered phases and fresh reads. It checks the exact public
field sets, unchanged raw reply and client observations, exit status and
execution diagnostics. Real Swift policy-transfer and worker-clock replies
also cross this assembly boundary and independent consumers in `runner_unit`.

## Success criteria

- All unit tests pass (exit code 0) and the crate is rustfmt-clean.

## Fixtures

Current response captures and constructed reply helpers support disposition and
assembly tests. Phase collection controls distinguish wrong JSON types from
optional absence, withhold unsupported projections and retain the raw reply
through assembly. Empty spawn-failure objects exercise claim-validation scope;
the independent full consumer owns their required-field rejection.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/unit/rust.unit/artifacts/cargo-test-bins.log`
- `<run>/suites/unit/rust.fmt/artifacts/cargo-fmt-check.log`
- `<run>/suites/unit/rust.disposition_reds/artifacts/cargo-test-ignored.log`
- `<run>/suites/unit/rust.byoxpc_reds/artifacts/cargo-test-ignored.log`

Run:

```
./tests/run.sh --suite unit
```
