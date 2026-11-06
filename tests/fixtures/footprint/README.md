# Footprint observer fixture

`observer.c` is a test-only persistent libproc observer and acknowledged child
control. Its case builds it through `build.sh` into owned test artifacts using
Clang; it is not part of a production Meson target.

The newline protocol accepts `clock`, `sample PID [PID ...]` (1–64 PIDs), and
`quit`. Each response is one JSON object. Commands and responses are bounded;
malformed commands terminate the helper. The Python wrapper owns the protocol,
validates receipts and can retain every raw response and binary/source hashes.
One thread must own each observer instance.

Samples bracket `PROC_PIDTBSDINFO`, `proc_pid_rusage(RUSAGE_INFO_V0)`,
`proc_pidpath` and a second `PROC_PIDTBSDINFO` with continuous nanoseconds.
Generation is `(pid, pbi_start_tvsec, pbi_start_tvusec)`; changed or unavailable
generations invalidate all metrics. Native return values and errno remain in
the receipt. CPU fields `ri_user_time` and `ri_system_time` are raw Mach
absolute-time ticks. Receipts preserve these as `user_ticks`/`system_ticks`,
record `timebase_numer`/`timebase_denom`, and convert each cumulative counter to
`user_ns`/`system_ns` using 128-bit multiplication and integer division;
`ri_resident_size` and `ri_phys_footprint` are bytes. These are the installed
Darwin SDK `sys/resource.h` rusage-info fields, not `getrusage` timeval fields.
The unit basis is Apple's XNU implementation: [`fill_task_rusage`](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/bsd_kern.c)
copies task power CPU counters, and [`task_power_info_locked`](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/task.c)
obtains them from Mach-time recount fields. SDK field declarations alone do
not establish the CPU unit.
Resident size and physical footprint are separate metrics and are never added.
Failed inspection leaves metrics null, never zero or confirmed absence.

The clock is `mach_continuous_time` converted with `mach_timebase_info` using
128-bit multiplication. `clock` also records `mach_absolute_time` on the same
conversion basis so sleep can be detected with bracketing uncertainty. Python
monotonic timestamps must not be compared directly with these timestamps.

`FootprintObserver.sample(pids)` returns a batch with per-call, per-process and
batch brackets. `inspect(pid)` returns one sample; `require_sample(sample,
expected_generation)` requires successful same-generation inspection. Exit
observation uses the independent exec fixture's EVFILT_PROC observer, registered
while live with a subsequent generation check. Its event collection time is
not claimed to be the actual kernel exit timestamp.

`spawn_control('busy'|'sleep'|'allocation')` acknowledges readiness over a pipe.
The allocation control's `touch(bytes)` writes each page and acknowledges that
it holds the allocation until quit. The busy child checks its pipe between
bounded work batches; the sleeper blocks in poll. Closing a control requests
quit and reaps that owned child, with a bounded forced-cleanup failure path.
The child's `cpu` command separately returns `getrusage(RUSAGE_SELF)` timevals
with native call brackets. The live control sandwiches two such readings
inside external samples and checks CPU delta agreement within the measured
outer brackets plus a 5ms accounting tolerance. It requires enough actual
busy CPU to expose unit errors and rejects unconverted ticks on a non-unit
timebase. Apple's [`calcru`](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_resource.c)
converts recount Mach time to timeval for this independent API.
The case retains actual allocation changes, both raw/normalized counters,
timebase, independent timevals and busy/sleep CPU deltas. These calibrate this
run's sensitivity, not a universal CPU quantum,
fixed allocation overhead or a memory ceiling for other workloads.
