# Sysctl disclosure implementation acceptance

Status: implemented, reviewed and accepted against the signed app. Associated
[implementation plan](../../controller/tools/pw_probe_runner/SYSCTL-DISCLOSURE-REFACTOR-PLAN.md).

## Implemented operation and disclosure

The existing 4096-byte stack destination now uses `PW_SYSCTL_READ_BYTES`.
`len = sizeof(buf)`, the single post-apply `sysctlbyname` call with a non-null
destination, and its success/failure handling are unchanged. The worker still
discards value bytes and post-call length. No sizing call, retry, allocation,
request option, per-run evidence or native resource was added.

The limits inventory now owns `sysctl_read_bytes`, with generated guide and
worker-account disclosure. The operation account states its bound and discarded
results. The worker account distinguishes selected copied observations from
sysctl bytes and length. The limits generator and independent source-drift
checker both register the compiled capacity control as a value owner.

The coordinator reviewed the production delta, independent control, generated
copies and unchanged descriptor-lifetime implementation. Request/response/
envelope versions remain 5/23/7, with unchanged shared layout. Optional raw
length metadata remains outside this refactor.

## Signed source and build

The base is `0262dfea37cc7a04e65af5e0b10fe3f7ffac1b6f`.
[implementation-source.json](implementation-source.json) records hashes and modes
for the 21 changed source/test/doc files. Unchanged files come from the base;
plan statuses, acceptance records and retention entries are bookkeeping.

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

The [build log](implementation-build.log) retains output with trailing whitespace
trimmed. The signed app, ZIP and standalone guide were produced; eight
executables and two seals passed Developer ID, hardened-runtime and secure
timestamp checks. Worker identity is
`53e40b215b0002c69e748f7706d9fd63fd750aef20e0ccfaace16bac7847d9f3`.
This is development acceptance, not notarization/release acceptance.

## Verification

Commands ran from the repository root outside the automation sandbox, through
the checkout-locked dispatcher with fresh managed output:

```sh
PW_TEST_OUT_DIR=tests/out/runs/sysctl-controls-20261018 tests/run.sh \
  --case runner_c_worker_harness/sysctl_read_capacity \
  --suite runner_filter_sysctl_name
PW_TEST_OUT_DIR=tests/out/runs/sysctl-default-20261018 tests/run.sh
```

The [targeted run](../../tests/out/runs/sysctl-controls-20261018/run.json),
`20261018T212641Z_c9f8ce22`, passed all three cases with no skips, unrun cases or
harness errors. Its inspected app was valid and unchanged.

The [full default run](../../tests/out/runs/sysctl-default-20261018/run.json),
`20261018T212659Z_9535057c`, passed all 194 cases with no skips, unrun cases
or harness errors. This includes all 461 Swift tests, the new capacity case,
compiled C/Swift layout agreement and live worker, phase, extension and exec
cases. Its inspected app was valid and unchanged. All 21 source/test/doc file
hashes and modes still match the acceptance snapshot. Final generated-copy,
link and whitespace checks passed.

[implementation-runs.json](implementation-runs.json) retains run identities,
configuration and canonical case outcomes. The full run records retain exact
commands, equipment and artifact inventories. Raw test evidence is gitignored
and available locally; both runs are pinned in the retention index. No earlier
source's test results are needed for acceptance.

## What the new control establishes

The [call receipts](../../tests/out/runs/sysctl-controls-20261018/suites/runner_c_worker_harness/sysctl_read_capacity/artifacts/observations.json)
come from production C compiled with only `sysctlbyname` substituted. They
independently record one call, the submitted target, a non-null destination,
input capacity 4096, null new-value pointer and zero new-value length. The
assertion uses literal 4096 independently of the production constant; the
actual receipt must also agree with the limits manifest and its exact owned ID.

The substitute changes the out-parameter to 7 on success and 0 on ENOMEM failure.
Success produces PW rc 0 and errno 0 despite a deliberately stale native errno;
failure produces PW rc 1, errno 12 and the existing error label. A disposable
source mutation supplying 4095 preserves those other facts but fails the same
independent capacity assertion. Commands, copied sources, source hashes,
compiler diagnostics and raw receipts are retained with the run.

These are supplied-call facts from controlled native returns, without sandbox
application or a real kernel sysctl call. They do not measure copied-byte counts,
required size or ENOMEM's cause. The existing live sysctl case separately retains
its specimen's unavailable prediction and observed attempt, while its checker
controls retain independent channel assertions.
