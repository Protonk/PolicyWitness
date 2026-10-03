# runner_outcome_bad_request

Exercises request refusal at the controller and XPC service. The host rejects
malformed intent before worker or validator creation; a refused request cannot
produce the independent file effect used by the accepted-input controls.

## Cases

- **`swift_decode_failure`**: current-version request missing `specimen_id`.
  It reaches the Swift decoder and reports `bad_request` with a decode error.
- **`missing_required_filter_value`**: a path filter with an empty value
  reports `bad_request` from request meaning validation.
- **`accepted_input_contract`**: current requests, selector aliases, nulls and
  nested selectors execute a file create. Unsupported versions, unknown fields
  at every object depth, malformed entitlements, optional types and augment
  sources fail explicitly without creating the file. Direct XPC controls prove
  the service independently checks versions and rejects unresolved controller
  options. Raw inputs, replies and stderr are retained per subcase.
  The [developer lesson](../../../docs/REQUEST-GRAMMAR.md) uses the shared
  [example corpus](../../fixtures/request_contract/examples.json), also read by
  Swift unit tests. Every example runs through CLI and direct XPC with exact
  code/path expectations. Ineffective arguments, nonces and filter values,
  unknown attempt/filter names, duplicate IDs and capacity excess refuse the
  whole specimen. Exec arguments and enabled capture have positive controls;
  known unavailable predictions preserve the independent attempt.

The first two specimens are constructed in `run.sh`; the contract controls
are in `contract.py`. Every runner refusal asserts an absent subprocess and
empty steps. Controller refusals assert no client invocation. Submitted files
remain unchanged.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/runner_outcome_bad_request/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_bad_request
```
