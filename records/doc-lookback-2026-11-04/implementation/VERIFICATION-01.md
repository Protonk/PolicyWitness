# First repair verification: pause before rerun

User authorized the prepared build/test execution and required a return before
any rerun. One signed build and one 83-case dispatcher run completed. Build
passed; cases: 82 passed, one failed, zero skipped or unrun. No rerun, repair,
documentation-owner dispatch or final-reader dispatch followed this result.

## Source and artifact

Base revision: `ea64218be2549fd034096f53ac23d79afac711ae`, with the ten changed
files recorded in `implementation/prebuild-state.json`. Before and after execution,
all ten hashes and the tracked patch hash matched that snapshot. All twenty
baseline document/input/figure hashes remained unchanged. The patch SHA-256 is
`3187ec9af01ca527d180e8f9a592199cbf6b7db81fe53fa159278eddf853d1e7`.

Command, run once outside the automation sandbox:

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

Build 1121 (`v0.3.4-40-gea64218b-dirty`) passed compilation, generated-input,
inventory, provenance and Developer ID signature checks. Worker identity is
`c1f66cc04bf60846bcddcee5d765e965d75c1e6a8d682d116f14439dc9b93bf7`.
This build replaced the prior distribution app; the earlier retained-app
identity comparison in the stage-3 provenance record is historical.

## Test execution and direct repair results

The selection was listed once before execution. This command then ran once
outside the automation sandbox:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-01 tests/run.sh \
  --suite failure_boundaries \
  --suite runner_unit \
  --suite runner_abi_layout \
  --suite runner_c_worker_harness \
  --suite unit \
  --case runner_outcome_bad_request/accepted_input_contract \
  --case witness_contract/actor_compositions
```

Owned output: `tests/out/runs/doc-lookback-repairs-01`.
Run ID: `20261105T025009Z_d5dead5d`. Terminal run duration: 273,763 ms.
Canonical case accounting is 82 pass / 1 fail; the legacy-report subtotal is
81 pass / 1 fail because it excludes the separately reported family. All 83
cases completed and report zero system-sleep overlap. Artifact integrity reports
valid before execution and unchanged afterward, with no integrity errors.

- I1: `runner_unit/pwrunner_core_unit_executable` passed 524/524, including
  `actor parameter refusals retain policy ownership and safe keys`.
  `runner_outcome_bad_request/accepted_input_contract` passed, including all six
  new examples through both CLI and direct XPC. Value failures retain
  `["actors", "1", "sandbox", "policy", "params", "K.dot"]`; unsafe or
  overlong keys/components withhold the path. Independent effect records show
  no file creation for refusals and file creation at the accepted boundary.
  This does not add depth-eight/nine diagnostic-path coverage.
- I2: `runner_abi_layout/c_swift_layout_agreement` passed. The freshly compiled
  native fixture exercised independent exact 1 MiB capture and cap-plus-one
  refusal, payload/digest/identity and no-write assertions, alongside existing
  controls. This establishes capture behavior for constructed readable memory,
  not successful compilation or application of a 1 MiB policy. The compiler
  emitted signed/unsigned PID comparison warnings at capture.c lines 27 and 55;
  these were retained without changing or rerunning the fixture.
- I3: `unit/rust.unit` passed, including
  `run_flow::tests::orchestration::actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`.
  Its six constructed orchestration scenarios establish resolved helper input,
  ordering/association and transport-evidence preservation at the dependency
  seam. They do not independently exercise a live helper process.

All selected failure-boundary, public actor-composition and C-worker cases
passed. Internal baseline and mutation executions are part of their registered
case, not retries of this dispatcher selection.

## Unresolved failure

`runner_unit/host_setup_oracle_sensitivity` failed with
`AssertionError('child identity missing')` for `wrong_shm_argv` and
`partial_unmap`. The baseline and `wrong_ready_direction` variants completed.
This is an unexpected characterization failure, not the intended rejection of
a faulty variant. The ordinary `runner_unit/host_setup_controls` case passed.

Failure evidence is beneath
`suites/runner_unit/host_setup_oracle_sensitivity/artifacts/` in the owned run:
`controls.log`, `controls/results.json`, and each failed variant's
`legacy-controls/worker-baseline.json` plus observer/recipe records. Both failed
receipts record successful native spawn, host reap and fixture cleanup, but
`child` is null. Missing child observation prevents the characterization from
completing. No product, environmental or intermittent cause has been established.
Execution was already unsandboxed and did not overlap recorded sleep.

The next decision is how to investigate this failure and authorize any focused
rerun. Preserve the original failure. Do not repeat the whole selection merely
to obtain a green result. Documentation revision and final paired readers have
not started; the verification gate remains open.

## Retained transcripts

After terminal completion, the run ID and owner ID were checked under
`tests/lib/checkout_lock.sh` before attaching the original transcripts:

| File in owned run | SHA-256 |
| --- | --- |
| `build-console.log` | `c65ab973f70a90ee26765ca0ef2343823796b8de1e4cf47f55b728a36dc4d24f` |
| `test-console.log` | `f4d41f111b527597876692307abf54d8522aee50084832e67abd27f70f0971bb` |
| `requested-selection.json` | `b57ff4d6772cf139ce9f89f77b4e70014611eb757829b04fc5ce495388d56b5d` |

`implementation/verification-01.json` retains the terminal accounting and
source identity checks. No source or test files changed during this execution.
