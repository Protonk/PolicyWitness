# Host-lifetime observation harness

> Archive availability: original raw runs are not retained. Reproduction
> procedures describe the original `records/performance/` layout and pinned
> environment; committed derived evidence remains available.

Equipment for the host-lifetime investigation recorded in
`HOST-LIFETIME-INVESTIGATION-REPORT.md`.
It launches ordinary `policy-witness run` invocations against an existing app
and observes the processes from outside. It changes no application binary,
setting, schema, signature or external runner. It uses only the standard
library of the repository's pinned Python 3.14.

## Run

From the repository root:

```sh
tests/lib/python.sh records/performance/host-lifetime/observe.py \
  --series rapid --count 12 \
  --request tests/fixtures/pw_runner/specimen_mach_deny.json \
  --label builtin-rapid-b853
tests/lib/python.sh records/performance/host-lifetime/analyze.py \
  records/performance/runs/RUN-ID --out records/performance/evidence/RUN-ID
```

The first stdout line of `observe.py` names the new raw directory,
`records/performance/runs/<UTC stamp>-hostlife-<label>/`. Existing directories
are refused. Raw output is gitignored and local to the producing checkout;
`analyze.py` verifies `SHA256SUMS` before reading it and writes `summary.json`,
`units.json` and a trimmed `run-record.json` under `evidence/`.

| Series | Schedule |
| --- | --- |
| `separated` | Before each invocation, wait until no observed role process remains alive (bounded by `--quiesce-deadline-s`), then observe for `--gap-s` (default 1 s). |
| `rapid` | Spawn the next controller as soon as the previous controller's exit is collected by `wait4`. |
| `overlap` | `--count` pairs. Each pair spawns two controllers one after the other, then waits for both; pairs are separated as in `separated`. |

Options used by the recorded controls: `--unobserved` disables process-table
polling (controllers are still timed by kqueue and `wait4`); `--busy-loop`
keeps one spinning Python child alive for the series; `--pw-arg` appends an
argument after the request path (`--pw-arg=--timeout-ms --pw-arg=22`).

The harness holds `tests/.checkout.lock` with a nonblocking exclusive `flock`
for the series and refuses when it is held. It never removes the file.
Each controller deadline (`--unit-deadline-s`, default 30 s) sends SIGTERM,
then SIGKILL two seconds later; `--ceiling-s` bounds the series. A first
SIGINT or SIGTERM stops scheduling and terminates the current controller.
The observer and any busy loop end with the harness. Exit 0 means the schedule
completed; 1 means it stopped early; 2 is a refusal before raw output exists.

## What is observed

Each poll (about every millisecond) lists all PIDs with `proc_listallpids`.
A new process whose name matches one of the selected app's executables is
identified by `proc_pidpath`, its kernel creation time and `p_uniqueid` from
`PROC_PIDUNIQIDENTIFIERINFO`, with the creation time read before and after to
bracket a PID reuse. A process is keyed by PID and creation time; `p_uniqueid`
and the parent's `p_puniqueid` give generation-exact lineage. Exits are kqueue
`NOTE_EXIT` notifications on the observer's clock. Hosts also report
`NOTE_FORK`.

launchd starts a service as `xpcproxy`, which then execs the service
executable. New `xpcproxy` processes are watched for `NOTE_EXEC`, and an exec
into the host is recorded with its observation time. A `posix_spawn` child is
briefly visible under its parent's name and path before its exec; the
observer rereads the image after registering and on every `NOTE_EXEC` and
reassigns the role, retaining the history.

After the schedule, `log show` retrieves launchd's messages for the selected
service and client domains, plus the host's own connection-invalidation
message, into `launchd-log.ndjson`. Its `machTimestamp` values are converted
with the recorded mach timebase and compared on `CLOCK_MONOTONIC_RAW`, the
axis of every harness observation. Kernel creation times (`CLOCK_REALTIME`)
use the wall-minus-monotonic offset read with that process's discovery.

## Limits

- A process that starts and exits between two polls is not observed. The
  maximum poll gap is recorded per run; the reply's worker and validator PIDs
  are compared with the observed processes.
- Exit times are notification-retrieval times, not kernel exit times. The
  launchd exit message is a second observer of the same event.
- The host's exit status is unavailable to a non-parent; launchd's exit-reason
  message is the only account of the terminating signal.
- `responsibility_get_pid_responsible_for_pid` is recorded but names the
  terminal application for every process here, so it does not associate a
  host with a client.
- The observer itself consumes CPU while polling. The unobserved controls
  are the comparison for its effect on controller wall time.
- Unified-log retrieval needs ordinary log access; it ran unprivileged here.
