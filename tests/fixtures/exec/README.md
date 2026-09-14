# Exec fixture

Build the test-only C executable with `build.sh <output binary>`. It uses
libSystem and no PW headers or libraries. It is not shipped in the app.

Without flags it writes `exec_fixture: hello from helper\n` and exits zero.
`--stderr TEXT` writes TEXT plus a newline; `--stdout-bytes N` replaces the
default stdout with N `A` bytes; `--exit N` selects the exit status (0–255).
These modes supply known input for output capture, truncation, and exit-status
contracts in `runner_use_c_worker`.

`--tree SOCKET` adds a leader and forked child, both retaining the inherited
process group and stdout/stderr. Output is flushed before the fork. Each
process connects to the test-owned socket and announces `P` or `C`. Commands
are one byte: `p` gets an `a` response; `q` requests a clean exit. The leader
waits for the child. EOF or a bad command fails; a 45-second alarm bounds
abandoned processes. The fixture does not create its own process group, so
it cannot hide a failure by PW to isolate exec children.

`control.py` owns the rendezvous and obtains PIDs from macOS `LOCAL_PEERPID`.
Its shared `ExitObserver` registers `EVFILT_PROC/NOTE_EXIT` before accepting startup as complete;
`assert_stopped()` requires exit events for both peers. A closed socket or a
PW-reported PID/status alone is insufficient. `close()` releases and, if
needed, kills surviving peers for cleanup; assertions must run before it.

The `exec_fixture` suite checks this equipment directly: exact generated
bytes and exit statuses, normal release, group kill, and leader-only kill.
The last case requires the same exit assertion used by the CLI test to fail
while the surviving child still answers a ping. These controls distinguish
fixture or observer faults from PW lifecycle regressions.

`assert_running()` requires both registered peers to remain alive and respond
to pings. A direct two-tree control releases B, observes both B exits, and
requires A to remain responsive with unchanged OS process identities. The
same liveness assertion must reject B after exit. `runner_specimen_isolation`
uses this contract while completing one specimen before releasing another.
It also uses `ExitObserver` for B's worker and XPC host, registering both while
they are held and requiring their real exits before checking A's survival.

`--process PID` is an observer mode that queries libproc for the given live
process, emitting PID, parent PID, start time, and executable path. It does not
rely on output from that process. `control.py`'s `process_snapshot()` validates
the complete report. Direct controls check known launched PIDs, parent/child
relationships, stable identities, and failure for an exited, reaped process.

## Process-state inspection

`--inspect NONCE [--env-key NAME] [--read-fd N]` replaces the usual stdout
marker with one JSON report and writes `inspect:NONCE\n` to stderr. The
default environment key is `PW_FIXTURE_CANARY`; the default canary FD is -1.
Inspection cannot be combined with tree/output/exit modes.

The report has `version=1`, the caller's nonce and PID, an environment entry
count and the selected variable's value, and `fds` as `[number, OS type]`
pairs. `PROC_PIDLISTFDS` supplies the inventory before the fixture opens,
closes, or duplicates any descriptors. A full 4096-entry buffer or failed
query exits with an error; a partial inventory is never marked complete.
The fixture does not read arbitrary descriptors: it uses `pread` on the
specified canary FD for up to 32 bytes and reports rc, errno, and hex bytes.
Stdin is polled for up to 100 ms, then read once if ready. `stdin_rc=0`
means EOF, -1 means an error, and -2 means no read occurred. A valid report
ends with `complete=true`; missing or truncated output fails parsing.

`--then-exec PATH ARGS...` must be the last inspection option. After emitting
the report it execs PATH in the same PID, preserving environment, descriptors,
and offsets. It sets `stdin_skipped=true` and leaves stdin unread. The worker
harness uses this to record actual launch state before the worker consumes
its policy pipe. Direct controls verify this forwarding behavior independently.

`inspection.py` contains parsing and contract assertions, independent of PW's
ABI and implementation. The direct fixture suite supplies known clean and
contaminated launches: a fresh environment value, a readable FD numbered at
least 200, and stdin data. It requires the corresponding clean-state assertions
to reject each contaminated state, and rejects missing, stale, and incomplete
reports. `runner_exec_inheritance` applies the same assertions through the CLI
and the controlled worker harness.
