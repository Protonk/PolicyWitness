# Runtime measurement harness

Historical, unmaintained equipment for the completed build-841 investigation.
Its capture/no-capture comparison uses the former CLI in the
[archived source tree](https://github.com/Protonk/Observer/tree/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source).
The measurement and live-control commands below do not run against maintained
PolicyWitness. Reproduction requires the recorded application and inputs;
the archive contains source, not the original signed binaries or local-only
raw evidence. The scripts, configurations and captured commands remain
unchanged to preserve the experiment. The summary reader can still inspect
retained raw evidence without launching the application.

Run from the repository root with `tests/lib/python.sh`. The harness uses only
the standard library on the repository's pinned Python 3.14. It changes no
application binaries, policy fixtures, settings or external runners.

`measure.py` copies the five fixtures and the harness sources into a fresh raw
directory, records the executable's version and hashes, and executes a fixed
manifest. `configurations.json` contains the counts sized from the interactive
pilot and the app bytes to which that sizing applies. The `short` and `standard`
configurations refuse different app bytes even if the build number is reused.

```sh
tests/lib/python.sh records/performance/harness/measure.py \
  --config short --expect-build 841 --out records/performance/runs
```

The first stdout line names the created directory. Default IDs are UTC stamps
followed by configuration and build number; `--run-id` supplies an exact fresh
directory name when a terminal transcript needs the same name. Existing raw
directories are refused, never overwritten. Raw evidence must remain under
`records/performance/runs/`; it is gitignored and local-only.

The short and standard modes are labeled `operator` by default. They require
the human to launch the command from a normal terminal with agent sessions
ended. Pilot, overlap and control modes are labeled `interactive`. A bounded
rehearsal can explicitly use `--execution-context interactive --rounds 1`.
The overlap configuration is refused with operator context.

The same persistent `tests/.checkout.lock` inode used by builds and tests is
held with a nonblocking exclusive flock throughout measurement and cleanup.
The harness never removes that file. It refuses a busy checkout. No test
dispatcher or test-library Python implementation is imported.

Children receive a recorded environment constructed from the account's home
directory, a fixed system PATH and C locale. Inherited `PW_*`, Python and
shell settings do not change application behavior. The launcher still applies
the repository's interpreter and SDK checks. Start/end probes retain commands,
outputs and failures. Process inspection records executable names, not complete
command arguments. A custom server's exact executable name has not been
supplied; the broad name match is explicitly qualified.

Each invocation opens separate stdout/stderr files before reading the start
clocks, then launches a fresh controller. A kqueue process-exit event wakes the
harness; `wait4` supplies the authoritative wait and resource record. If event
registration fails (including a child exiting first), a recorded nonblocking
wait4 fallback polls at 1 ms. W includes this observation overhead. The raw
monotonic clock counts sleep; the uptime raw clock does not. Gaps of at least
1 ms flag sleep, using the dispatcher's read-skew convention.

The hard-finish deadline begins on entry to the Python procedure, before
preflight. A nominal invocation deadline is 300 s; the effective deadline also
reserves 10 s for cleanup before the configuration ceiling. Timeout records
name `nominal` or `ceiling`. SIGTERM is followed by SIGKILL only if the child is
still unreaped after two seconds. A child still unreaped one second after
SIGKILL is recorded and the series stops. No global process search or cleanup
is attempted. XPC service descendants retain their own budgets.

One Ctrl-C requests termination of the current controller, records the
interruption and leaves all later entries `never_started`. `caffeinate -i -w`
blocks idle system sleep while the harness lives; it does not prevent display
dimming or screen locking. Its launch and release observations are retained.

Cleanup first saves the loop's terminal facts, then bounded end-condition
probes, assertion release and incremental checksums. A 150 ms final-write
allowance is inside the reserve. Final `run.json` bytes are hashed last; the
provisional record is never listed in `SHA256SUMS`. Incomplete cleanup leaves
partial attestations and explicit skipped steps. Deadlines bound the harness's
decisions and supervised waits, not an OS scheduler stall or a blocked
filesystem operation. Actual durations and outer terminal status remain evidence.

| Exit | Meaning |
| --- | --- |
| 0 | Manifest exhausted and cleanup complete; individual app failures may still exist. |
| 1 | Loop stopped early, including interrupt, ceiling or harness error; cleanup complete. |
| 2 | Refusal before creating raw output. |
| 3 | Incomplete cleanup or a later filesystem failure; preserve the directory and terminal diagnostic. |

`summarize.py` verifies every listed checksum before reading the run. It refuses
a mismatch, reports uncovered files as `unattested`, and writes only outside the
raw directory. It exports small run records alongside the summaries:

```sh
tests/lib/python.sh records/performance/harness/summarize.py \
  records/performance/runs/RUN-ID \
  --out records/performance/evidence/RUN-ID
```

Warm-ups and outcomes are separate strata. Nonzero completed app exits remain
eligible observations. Sleep-affected or incomplete invocations are explicitly
excluded, while absent, invalid and inapplicable measures are counted. Negative
mixed-clock residuals and wide variability remain visible. `summary.json`
contains each observation, sequence, stratum and measure as well as aggregate
minimum, median, nearest-rank p90 and maximum. The envelope stamp E is retained
per observation and is not summarized as a duration.
Summary format 2 calls the source `runner_result.pid` field `runner_result_pid`:
after worker launch it identifies the worker; early refusal paths can use the
host PID. It is not an independent host-identity observation.

Harness controls run in fresh directories and retain external terminal
transcripts, exit statuses and assertion results under `evidence/`:

```sh
tests/lib/python.sh records/performance/harness/controls/check.py --mode synthetic
tests/lib/python.sh records/performance/harness/controls/check.py --mode live
tests/lib/python.sh records/performance/harness/controls/check.py --mode overlap
```

Live modes need ordinary XPC and unified-log access. The automation sandbox can
refuse those facilities and machine-condition probes; follow repository guidance
for an unsandboxed retry, preserving the original observations. Synthetic
stand-ins establish the harness's behavior only. The checksum-mismatch control
alters a separate copied directory, never the original evidence.
