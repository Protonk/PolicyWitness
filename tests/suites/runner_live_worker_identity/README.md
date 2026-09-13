# runner_live_worker_identity

Checks the live worker's identity and policy independently of PW's JSON.
The specimen uses `(allow default)` with one narrow file-read denial, two
file probes, and an exec helper that waits on a Unix socket.

The test-owned observer accepts that connection and gets its peer PID from
the kernel (`LOCAL_PEERPID`). `proc_pidinfo` and `proc_pidpath` identify the
helper, its `pw-probe-runner` parent, and the parent's `PWRunner` host. The
observer directly calls libsandbox for both file targets against the worker
and host, then releases the helper. The worker must allow one target and
deny the other; the host must allow both. PW's final worker PID, helper PID,
and file predictions must match these independently collected observations.

The helper and observer share a small test-only C executable with no PW
headers, filter mappings, validator, or JSON parser dependencies. Socket
waits have seven-second deadlines, below the worker's default exec deadline.
No `_test_overrides`, launchd installation, or unified log access is used.
This checks one live process chain and policy; it does not prove that every
prediction in every run was obtained by calling libsandbox.

Run `tests/run.sh --suite runner_live_worker_identity` outside an automation
sandbox (request escalation there). Missing builds, toolchain failures,
inaccessible process metadata, and failed rendezvous are failures, not skips.

Artifacts: `specimen.json`, `run.json`, `observer.json` (kernel-derived process
IDs, start times, raw query results), both stderr streams, `build.log`, and
`assert.log`. Temporary targets and the socket are removed after the run.
