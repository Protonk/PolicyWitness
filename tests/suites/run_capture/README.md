# run_capture

Direct controls for `tests/lib/run_capture.py`, used by the validator-failure,
exec-lifecycle, specimen-isolation, execute-permission, live-worker-identity,
and allow/deny consistency suites. Requires macOS and Python 3; no
built PolicyWitness app or C compilation. This suite is in the default battery.
Run outside an automation sandbox so Unix sockets and OS exit observation work:

```sh
tests/run.sh --suite run_capture
```

## Capture contract

`RunCapture(pw, out, specimen, cli_args=...)` prepares `specimen.json` and reserves
the output paths. `start()` launches the public `run` command without waiting;
`wait(timeout=...)` returns its actual exit status. Tests can prepare multiple
specimens before starting any of them. The context-manager form starts on entry
and cleans up on exit; explicit start/close also works with an `ExitStack`.

The CLI writes directly to `run.json` and `pw.stderr` as binary files. Nonzero
exits, signals, and malformed output retain the original bytes. `load_json()`
decodes only on request, after CLI exit, and reports the artifact paths if
decoding fails. It makes no assertions about the envelope or expected status.
Existing capture paths are rejected rather than overwritten by a second run.

`capture.json` records the exact argv, PID, launch time, elapsed time through the
first observation of exit, return code, exit code or signal, and launch/JSON/
cleanup errors. `harness_timeout_seconds` records a test-side wait timeout;
`HarnessTimeout` raises with artifact locations. That timeout does not send a
signal and does not interpret any PolicyWitness deadline or result.

`close()` kills and reaps a still-running CLI with a bounded wait, recording
`cleanup_kill_requested`; exit status records what actually happened. It does
not manage the worker, XPC host, or fixture tree.
Callers must observe those processes before fixture or capture cleanup runs.
An assertion leaving the context remains a failure after cleanup.

## Independent controls

The small program in `tests/fixtures/capture/cli.py` receives a specimen,
records its actual arguments, emits explicitly specified bytes, and optionally
waits on a Unix socket gate. It imports no capture or production code.

Controls check successful and nonzero exits; exact bytes and literal arguments;
malformed JSON and UTF-8; termination by signal; a PW-shaped timeout result
distinct from a harness timeout; partial output retained through timeout and
assertion cleanup; context exit without waiting; overlapping captures with
different markers; refusal to overwrite artifacts; and launch failure.

Socket acknowledgements prove output was flushed and the CLI remains alive.
PIDs come from kernel socket credentials. The existing exec fixture's
`ExitObserver` supplies OS exit events, and `waitpid` checks that capture reaped
its child. B must complete while A still answers, without changing A's artifacts.

Artifacts retain every specimen, raw output, capture metadata, the fixture's
argument receipt, `controls.json`, and `assertions.log`.

The shell entry point uses `tests/lib/case.sh` for setup and logged checks.
Case IDs, checker arguments, and artifact paths remain defined by this suite.
The `shell_helpers` controls verify failure propagation and report/log behavior.
