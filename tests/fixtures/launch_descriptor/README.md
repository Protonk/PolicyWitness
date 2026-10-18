# Launch descriptor ownership controls

`runner_unit/launch_descriptor_controls` copies the current Swift package and
instruments native calls/observation points only in that copy. `Probe.swift`
retains original descriptor ownership, original/decoy mapping readbacks and
driver results. `observer.c` snapshots incoming descriptors before acquiring
its output file. In worker mode it execs the unchanged signed worker in the
same PID; in validator mode it writes challenges and consumes input without
calling `sandbox_check`. No request-selected test seam is added to production.

All specimens submit zero slots. The observer writes nonzero random challenges
into per-descriptor cells of unused slot 255. The host independently reads
both its evidence mapping and a separate same-sized, byte-identical decoy after
validator reap. Successful writable decoy readback is required even when the
true object is absent. Descriptor number, stat fields and matching ABI/header
bytes only identify candidates; they do not identify the underlying object.
The old-lifetime source control must expose the true object using the same
observer and still distinguish the decoy.

The candidate closes and relinquishes the original descriptor, then the fixture
opens `/dev/null` at that exact number. Driver teardown must leave this sentinel
open. The stale-owner source control must close it and fail the fixed assertion.
High-fd launch retains its worker original-number alias; fd 3 self-dup requires
the existing pre-spawn close-on-exec clear. Removing that clear in a source
control must lose actual worker completion. A separate read-only executable
descriptor exercises fd 5 delivery; this is not extension-token consumption.

Earlier setup controls replace `ftruncate`, both `mmap` refusal forms, both
pipes, checked pipe flags and extension duplication with EIO. Native spawn
refusal uses a missing executable. All retain one successful original close
and no invented child. `mapping.c` inspects the complete acquired VM range
immediately before/after the real production unmap, using `mach_vm_region` and
deallocating returned object-name rights. The positive range must be fully
mapped and the later range entirely absent; no allocation intervenes. The
requested unmap length and successful native return alone are insufficient.

Each case has a fresh process group and durable child-owner receipt. The
worker-entry watchdog survives exec. The host's reap is independently checked
with `waitpid`/ECHILD; only an unreaped owned process can be signalled during
fixture timeout cleanup. After host reap, group inventory is read-only; any
survivor fails and retains ownership receipts for recovery. The signed worker
hash is unchanged across the case. Exact copied sources, substitutions, hashes,
build/run commands, native observations and rejected checker/source controls
remain in managed test artifacts.

These controls establish host descriptor lifetime and unchanged endpoints in
the copied drivers. They do not establish a shipped-validator write, an ordering
violation, a remedy for the existing closed-stdin collision or new worker/exec
inheritance policy. Default live suites separately exercise the built app.
