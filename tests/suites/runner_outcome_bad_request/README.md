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
  Swift unit tests. The create/capture-typo input bodies resolve explicit paths
  to app-owned JSON under `controller/src/lessons/`; expected diagnostics remain
  independent corpus data. Every example runs through CLI and direct XPC with exact
  code/path expectations. Ineffective arguments, nonces and filter values,
  unknown attempt/filter names, duplicate IDs and capacity excess refuse the
  whole specimen. Exec arguments and enabled capture have positive controls;
  known unavailable predictions preserve the independent attempt.
  Capture controls require the worker/before-apply context and matching nonce
  through both entrypoints, reject the retired capture spelling and previous
  request version, and preserve successful application beside unavailable
  capture when the worker dies before normal completion.

The first two specimens are constructed in `run.sh`; the contract controls
are in `contract.py`. Every runner refusal asserts an absent subprocess and
empty steps. Controller refusals assert no client invocation. Submitted files
remain unchanged.

`same_shape_contract` is opt-in because it builds two signed variants in isolated
worktrees. Both trace client and worker entry; one deliberately replaces
`open_write` truncation with append while retaining the request and reply shapes.
Matching assertions establish the respective file effects. Foreign assertions
leave the file unchanged and both entry traces absent. These are disclosed
instrumented controls, not production-equivalence evidence. Source patches,
product identities, build logs, requests, traces and cleanup ownership are retained.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/runner_outcome_bad_request/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite runner_outcome_bad_request
```
