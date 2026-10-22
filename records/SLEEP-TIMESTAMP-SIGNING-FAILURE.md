# A build refusal run failed at signing just after wake

Recorded 2026-10-21 on macOS 26.7.1 (25G241), during the native build plan's
verification. The run and its evidence are gitignored and exist only in the
local checkout.

## What failed

`preflight/build_refusal_controls` (run `20261022T010124Z_46fd4676`, output
[`tests/out/runs/native-refusals-20261021/`](../tests/out/runs/native-refusals-20261021/run.json))
failed after 78 control records had completed. The failing build was not a
refusal under test. It was `probe_failed-fresh-plain`, the fresh full build
that [`control_provenance_probe_failed`](../tests/suites/preflight/opt_in/build_refusals.py)
runs last to restore the checkout, and which must pass. The build exited 1
at `Codesigning embedded MacOS tools`, on the first
[`sign_macho`](../build.sh) call, for `Contents/MacOS/pw-runner-client`.
`codesign --force --options runtime --timestamp` reported:

```
pw-runner-client: The timestamp service is not available.
```

The raw output is in the case's
[`full-probe_failed-fresh-plain/build/`](../tests/out/runs/native-refusals-20261021/suites/preflight/build_refusal_controls/artifacts/full-probe_failed-fresh-plain/build/stderr)
directory, and the assertion in its
[`assertions.log`](../tests/out/runs/native-refusals-20261021/suites/preflight/build_refusal_controls/artifacts/assertions.log).

## Timeline

Local times, from the case's receipts and `pmset -g log`:

| Time | Event |
| --- | --- |
| 18:01:24 | Dispatcher starts the case. |
| 18:19:41 | The `probe_failed-hang` build finishes. |
| 18:19:42 | `Entering Sleep state due to 'Clamshell Sleep'`, on battery (lid closed). |
| 18:19:44 | The `probe_failed-stderr-overflow` build's receipt is written, during the transition into sleep; that refusal passed. |
| 18:30:20 | `Wake from Deep Idle`, lid opened. |
| 18:30:20 to 18:30:38 | `probe_failed-fresh-plain` runs and fails at the first signature, about 18 seconds after wake. |

The dispatcher recorded `system_sleep_ms` 635713 for the invocation and
printed its `SLEEP:` note that the failure is not creditable product
evidence. Its `caffeinate -i` assertion blocks idle sleep only, so closing
the lid still slept the machine.

## What is known and what is not

Signing requires Apple's timestamp service, so a build that reaches its first
signature soon after wake depends on the network having come back. That
connection was not observed here; the unavailable network is an inference
from the timing.

When the timestamp service is unavailable, the case cannot tell that apart
from a product failure. It has no retry, so the whole case, about 50 minutes,
was run again
([`native-refusals-20261021-2`](../tests/out/runs/native-refusals-20261021-2/run.json)).
Every signed build in the case signs with `--timestamp` and could meet the
same failure. None of this was investigated further, and no change was made
to the case.
