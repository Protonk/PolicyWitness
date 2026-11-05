# Authorized focused rerun

The user authorized a rerun after the first verification checkpoint. Root
reran only the failed `runner_unit/host_setup_oracle_sensitivity` case, once,
outside the automation sandbox, with no source changes or rebuild:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-02 tests/run.sh \
  --case runner_unit/host_setup_oracle_sensitivity
```

Run ID: `20261105T030143Z_908ddc80`. The single selected case completed and
failed in 31,684 ms, with zero recorded system-sleep overlap. This case uses
copied sources and fixtures, not the signed app; its artifact-integrity field
is therefore null. The prior 82 passing cases were not rerun.

| Variant | First run | Focused rerun |
| --- | --- | --- |
| `baseline` | Pass | Pass |
| `wrong_ready_direction` | Pass | Missing child identity |
| `wrong_shm_argv` | Missing child identity | Pass |
| `partial_unmap` | Missing child identity | Pass |

The new failing `worker-baseline.json` records native spawn rc 0, PID 94002,
host reap, closed descriptors and completed fixture cleanup, but `child` is
null. The 46 retained copied-input files match exactly between both runs;
the tracked patch and ten prepared-file hashes still match the pre-build
snapshot. This changing outcome with identical inputs supports intermittent
behavior in this control, but does not establish the mechanism or assign cause
to the product, compiler or environment.

The fixture gives the observer a 100 ms worker-ready allowance and does not
use the worker protocol. Whether host cleanup can terminate the observer
before it writes its receipt is a concrete next investigation question, not
an established cause. Do not credit complementary passes across the two failed
runs as a complete passing case.

Owned evidence remains at `tests/out/runs/doc-lookback-repairs-02`, including
`run.json` and
`suites/runner_unit/host_setup_oracle_sensitivity/artifacts/controls/`.
The console transcript was attached as `test-console.log` under the checkout
lock after verifying the run and owner IDs. Original run 01 is untouched.
`implementation/verification-02.json` records source and evidence hashes.

No further rerun, source repair or documentation dispatch followed. The next
step is investigation of the observer startup/receipt/teardown sequence before
another execution; the verification gate remains open.
