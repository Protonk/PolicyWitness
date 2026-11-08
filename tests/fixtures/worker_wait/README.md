# Worker wait pilot fixtures

Test equipment for the worker-wait timing pilot,
`witness_contract/worker_wait_pilot`. Nothing here is compiled into the app,
and nothing adds a wire or evidence field. The pilot case builds and stages
these pieces into a disposable signed app copy.

## Stamp worker

`stamp_worker.c` is the production worker: it defines the worker's
compile-time measurement seams, then includes `pw_probe_runner.c` unchanged
from the worker directory that `build.sh` puts first on the include path,
`controller/tools/pw_probe_runner/` of the selected source tree. Every seam
defaults to a no-op in the production source; this wrapper defines them to
store into a stamp page whose layout is `pww_stamp_page.h`. The
[header comment](pww_stamp_page.h) is the byte-offset table that a Python
reader mirrors with `struct.unpack_from` (header `'<4IQ4I'`, stage register
`'<3Q'`, scan block `'<71Q'`, event `'<4IQ'`), together with the event ids,
flags and reading rules.

### Where the page lives

The page is region pages 201 and 202 (offset 3,293,184, 32,768 bytes) of the
evidence region the host already maps and pre-touches. Those pages lie wholly
inside the compiled-profile capture bytes, which the production worker writes
only when the host requests a capture. Using them adds no mapping, descriptor
or layout change. Page 200 belongs to the
[first-touch control](../worker_lifecycle/README.md) and is never written.
Static assertions in the header pin the size, every offset and this
placement.

### Before application

The clock-setup seam runs after the region mapping, the header checks and
authority preparation, and before any policy byte. In it the wrapper calls the
real `mach_timebase_info`, writes both stamp pages and initializes the header:
the timebase, the worker origin (the `worker_start` read, held in a static
because it precedes the mapping), the worker's pid and the initialized flag.
It then records the `worker_start` stage register and the `WORKER_START`
event. Before application the wrapper adds only `getpid` and these page
writes to what the worker does.

### After application

The seams call `mach_continuous_time` directly and store into the page. They
do not allocate, sleep or perform I/O, and they never call `pw_clock_sample`,
so the worker's clock history and sticky fault are unchanged.

- Every clock read through the production seam updates that stage's
  register (count, first and last raw value), including a sample that
  validation then rejects. Per-pass samples are kept as registers, not
  appended.
- At a decision point (ordinal loaded, activation loaded, eligible inbound slot
  observed) the record reuses the pass's existing sample, so no clock read
  lands between a decision and its acknowledgement store. Loaded records are
  bounded: each wait's first pass is recorded, and so is every pass whose
  loaded value changed, together with the pass before it. A change is
  therefore bracketed by two adjacent pass samples.
- After the arrival, applied, acknowledgement, activation-observed, inbound
  acknowledgement, attempt-completed and `done` stores, and at the exchange
  answer return, the wrapper takes one raw read and appends an event.
- Each release, parked and exchange wait has a pass counter, reset by that
  wait's start read and advanced by each of its observe reads. Right after the
  acknowledgement, activation-observed or exchange-answer event, the wrapper
  appends the wait's pass count (events 13, 14 and 15) with the same raw. A
  release or parked pass is one observe read and one load, so the count
  includes the accepting pass. An exchange pass reads the clock only after an
  unanswered load, so an answer on the first load counts as one pass, as does
  an answer on the second. Stage registers span all of a worker's waits;
  these counts are per wait.
- Each inbound scan pass, visit and acquire load is counted under the waiting
  role (parked activation or authority exchange), taken from the clock stage
  read earlier in the same pass. A visits-per-pass histogram is included.
  `PW_INBOUND_SCAN_LOAD` performs exactly the production acquire load and
  returns its value.
- The event count is release-published after each append. Events past
  capacity (1,000) set the overflow flag and are not recorded.

### Refusals

- When the host requests a capture (`capture_requested == 1`), the wrapper
  writes only the header, with the capture-refused flag, and stamps nothing
  else. A capture whose bytecode exceeds 670,832 bytes would also overwrite
  that header. The reader then finds no magic and must report the page as
  unobserved.
- A scan pass that follows a clock stage other than the two parked/exchange
  observations is counted in no role and sets the unknown-role flag.
- `build.sh` refuses a production source whose call-site count for any seam
  the wrapper defines differs from its declaration (two each for the clock
  read and the scan load, one for every other seam). A changed count changes
  what a stamp means.

## Build

`build.sh <output directory> [source tree]` writes:

- `pw-probe-runner-stamps`, the stamp worker.
- `pw-probe-runner-plain`, the unmodified production source built with the
  same command and flags. It serves as the uninstrumented neighbor, so that
  the two staged workers differ only in the wrapper.
- `worker-build.json`, the receipt.

The source tree defaults to this repository. Another tree, such as a
candidate checkout, supplies the worker source, its ABI header and the identity
its `tests/lib/contract.py` declares; the wrapper, the stamp page header and
the recipe always come from this repository. Both outputs then report that
tree's identity, which a host built from the same tree enforces. The receipt
records the tree as `source_tree`, and inputs outside this repository by
absolute path.

The flags are those of `meson.build`'s worker target plus `-Werror`:
`-Wall -Wextra -Werror -O2 -std=c11 -mmacosx-version-min=26.0 -arch arm64`,
linked with `-lsandbox`, with the tree's worker directory and this fixture
directory as include paths. The receipt retains the exact commands and the toolchain (clang path and
version, SDK path and version, any `SDKROOT`/`DEVELOPER_DIR` in the
environment). Each output's repository inputs come from clang's `-MM` listing
with the same flags, and each is recorded with its sha256, as are the SDK
files clang reads. The receipt also records the build script's hash, every
seam call site found, and each output's sha256, size, device, inode and mode.
It retains both outputs' warm-up and `--version` executions with return codes,
output and elapsed time, plus the declared identity from the tree's ABI header
and `tests/lib/contract.py`, which must agree. The script needs the resolved `PW_PYTHON` that
`tests/run.sh` and `tests/lib/python.sh` export.

Each output is executed once with no arguments, stdin at EOF and only the
standard descriptors open. It must exit 2 at argument parsing. It is then run
with `--version`, which must report the identity the source declares. The
first execution of a new file can take hundreds of milliseconds. A copy staged
into an app is a new file, and it stays cold until its own excluded execution.
Any refusal still writes the receipt, then fails the build.

## What the stamp worker establishes and what it does not

- **It is not the production worker.** It reports its source tree's
  production `abi_identity`, and that tree's host accepts it, because the
  identity digests production sources only. The identity does not describe the
  stamp wrapper. Records name the stamp worker's actual bytes with
  `provenance_kind: substitution`. Actual bytes and substitution provenance
  remain separate, as in `witness_contract/order_barrier_mutations`. The plain
  twin is likewise not the distributed worker: it is built by this recipe, not
  by Meson, and its bytes are not established to equal the shipped binary.
- **Observer effect.** The page writes before application, the per-pass
  register, wait-state and pass-counter stores, the per-visit and per-load
  counter stores,
  and the raw reads after production stores all change worker timing and
  memory. Compare against the uninstrumented neighbor before attributing a
  response to the production wait. Footprint or resident-memory samples of
  this worker include the two written stamp pages and are not production
  footprint.
- **Counts and timing in one build.** The scan counts are exact counts of the
  visits and acquire loads this binary executed. Its timings include those
  counting stores. A scan comparison must use this same wrapper on both sides;
  the pilot's comparison mode builds it from each tree and its reader pairs the
  counts per actor.
  A timing claim that must exclude counting overhead needs a separate build,
  which this fixture does not provide.
- **Resolution and meaning of a stamp.** Raw values are absolute
  `mach_continuous_time` ticks, the domain the instrumented host also reads.
  The page records the timebase, and one tick is the finest step. A decision
  record carries the sample taken before its load, so it bounds the load from
  below, and the next record bounds it from above. Neither is the instant of
  the store the worker observed.
- **Visibility.** Stamps written after `done`, or on a cancellation exit, are
  not ordered by any production publication. Read the page only after the
  worker's reap is confirmed, and decode only `event_count` events.
- **Absence is not zero.** A missing page copy, a wrong magic or a clear
  initialized flag means nothing was observed. Zero counters on such a page
  are not zero counts.

## Instrumented host

The pilot driver's optional `--window-gate PATH` separates staging from native
trials. The path must be absent at startup. After preparing both apps, the driver
writes `prepared.json` with their identities and a fresh token, then waits up to
five minutes for the coordinator to write that token to the gate. No worker trial
runs before release; timeout or a wrong token follows normal owned cleanup.
This lets the coordinator record exact staged identities and announce a quiet
window after compilation and signing finish.

`HostStamps.swift` is a test-only timeline recorder compiled only into the
disposable PWRunner hosts that `host_stamps.py` builds; the builder prepends the
literal `PWW_STAMP_DIR`, `PWW_STAMP_SWIFT_FLAGS` and `PWW_STAMP_INSPECTION`
declarations. Every stamp is `mach_continuous_time()`, the worker's tick domain.
All storage is allocated and zero-filled once, when the service starts, before
the listener resumes: 4096 records, registers for polled publications, per-wait
sleep registers, custody-pass registers, one 32 KiB buffer per actor and 16
stamp-cost words. The record path neither allocates nor faults a fresh page. At
request start the recorder makes 16 consecutive records through the call sites'
own `HostStamps.shared.record` expression, copies their raws to
`stamp_cost.raws` in `stamps.json` and withdraws them from the timeline;
adjacent differences give the per-record cost in the selected host flavour, in situ.
The release, activation and inbound commit stores each have a record immediately
before them (139, 149 and 158) as well as after (141, 150 and 159). Host export
version 2 requires the inbound pair, keyed by phase and delivery. The reader
also accepts version 1 exports with a wider conservative commit bracket from
custody-service start to transfer-wait start; the latter alone cannot bound
publication time. The first 64 sleeps of each wait
key are also appended as stamped begin and end events (180 and 181, phase = key,
aux = requested nanoseconds), so a worker publication can be placed in the exact
host sleep that contained it; later sleeps update only the registers. A
bounded wait for the worker's exit records its pair the same way and then event
182 (`WAIT_OUTCOME`: phase = key, aux 0 timed out, 1 notified, 2 unusable, raw =
the pair's end), while that key's pairs are still appended. The worker exit
grace is bracketed by program points 148 (`WORKER_GRACE_BEGIN`, right after the
host presets the stop to exhausted) and 157 (`WORKER_GRACE_FINISHED`, right
after it records the grace wait), phase = actor index, aux 0 exhausted,
1 reaped, 2 wait_error. Polled
publications keep
`last_negative`, `first_positive` and a negative-sample count. Host sleeps keep
count, last pre/post, requested and actual sums, and min/max, keyed 1 to 7 by
caller; key 0 is the ready-byte wait and key 5 the worker exit grace. Sleep
registers and events record bounded waits, whether sleeping or
readiness-driven: in a tree whose ready-byte wait is readiness-driven
(`HostWaitClock.expiredAfterWaiting(readable:)`), an optional patch brackets
each bounded wait with the same hook, so it appears under key 0 exactly as a
sleep does, and a wait that returns early records an actual duration below the
requested one. In a tree whose worker grace waits for the exit notification
(`HostWaitClock.expiredAfterWaiting(exit:)`), a second optional patch records
each such wait under key 5 with `HostStamps.wait`, which adds its outcome
event. The same patch records a final ordinary sentinel exit wait under key 1.
The reader separates final key-1 waits after the last release and before the
exit request; missing boundaries or a truncated trace leave that accounting
unobserved. Plain sleeps and each native wait outcome stay distinct.
Event 172 marks the end of session teardown, after its mapping, descriptor and
spawn-state cleanup calls. Direct terminal-to-reap and terminal-to-teardown
intervals retain the terminal publication bracket; spawn-to-teardown describes
the host's session residence between program points. The teardown stamp does
not establish that each native cleanup operation succeeded or that resources
are absent from the kernel. Custody passes in the actor completion
loop are registers; events 153/154 are appended only for passes that changed
the custody or transfer record count.

The recorder writes `<stamp_dir>/<stem>.started` after the request decodes and
before admission or any spawn, and `<stem>.stamps.json` once, immediately
before the reply is sent. The export cannot wait for the host's delayed exit
closure: launchd removes the service as soon as the client disconnects, and in
the first dry run no export ever appeared from that closure. The export's cost
therefore lies inside the instrumented host's request latency, after event 171.
Once the stamps file is renamed into place, the recorder writes
`<stem>.exported`: `host_pid`, `begin_raw` (event 171's raw), `end_raw` (a read
after that rename) and `bytes` (the stamps file's size). The marker's own write
follows `end_raw` and is not in that span; no marker follows a failed stamps
write. Every write uses a close-on-exec temporary file and a rename, and all are
skipped when the directory is absent.
The stem is the `specimen_id` with each byte outside `[A-Za-z0-9._-]` replaced
by `_`, truncated to 120 bytes. Each worker's stamp page is copied immediately
before its session unmaps the evidence region; the copy records whether the
worker had been reaped. Overflow and out-of-range samples are counted under
`dropped`, never discarded silently.

`host_stamps.py` owns the patch set: an ordered list of replace-once edits over
copies of nine runner files. Each anchor must occur exactly once or the build
fails before compiling. A patch marked optional applies when its anchor occurs
once, is skipped when the anchor is absent, and fails when it occurs more than
once; skipped patches are listed under `patches_skipped` in `host-build.json`.
The two optional patches bracket the readiness-driven ready-byte wait and the
bounded worker exit wait described above, so a tree without either wait builds
unchanged; the grace program points apply to every tree. `build_host` copies a
source tree's `runner/` (this repository's by default), applies the patches and
compiles that tree's Meson PWRunner source list with
`swiftc -j 2` with either `-Onone -g` (inspection, the default) or `-O`
(optimized), and `-target arm64-apple-macosx<minimum>`; the shim is built
with `clang -c -arch arm64 -mmacosx-version-min=<minimum>`. The builder's
`--flavour` and pilot driver's `--host-flavour` select only these host flags;
workers, validator and controller retain their own recipes. A pilot run uses
the same flavour for both sides. Different-flavour diagnostics stay separate
from implementation comparisons and do not authorize a shipped-policy change.
Its `host-build.json`
records the source tree, the exact argv, flavour, the tree and compiled sha256
of every source with its patched flag, the full patch texts with whether each
applied, the generated recorder source, the toolchain versions and the output
hash. With no patches it builds the uninstrumented neighbor by the same recipe,
without `HostStamps.swift`. `stage` copies a signed app into a durable
caller-supplied directory, places one fixture worker in both worker roles,
installs the host, gives the app and service fresh bundle identifiers,
regenerates `worker-equipment.json` and signs in the order-barrier control's
order, then inspects the result and writes `staging.json` with inventory
hashes, per-executable sha256 with device and inode, bundle identifiers,
identity, recipe and stamp directory. It is given the source tree the app and
workers came from and reads that tree's `WORKER_IDENTITY` from the text of its
`tests/lib/contract.py`, without importing it. Before any copy is signed, the
app's equipment identity and the worker's `--version` must both equal it, and
it is the identity the regenerated equipment declares; the tree's entitlement
files sign the copy. `staging.json` records the tree's `HEAD` and its
`git status --porcelain` output, read without taking the index lock.

The instrumented host's timings describe a `-Onone -g` disposable rebuild with
added clock reads, register stores and file I/O outside the held interval. They
do not describe the Meson-built distribution host; the neighbor separates
instrument cost from recipe cost only between those two rebuilds. Fixture hosts
and workers report their source tree's ABI identity, which does not describe
their bytes; the receipts' hashes and substitution provenance do. A missing
`stamps.json` is an incomplete trial.

## Calibration pair

`clock_pair.c` is the calibration control for the pilot's timestamp instrument,
independent of PolicyWitness: it applies no sandbox and contains no host, worker
or validator code. A parent forks a writer and a reader sharing one anonymous
`MAP_SHARED` mapping. Per trial the reader stamps and release-stores a ready
word; the writer polls it with 1000 `yield` hints per pass, stamps its arm,
sleeps the injected delay (0 to 3 ms, by `nanosleep` or `mach_wait_until`),
stamps, stores that stamp in a mailbox, release-stores the published word and
stamps again. The reader polls the published word with the selected pacing
(`busy`: one read, one acquire load and 1000 hints per pass; `sleep2` or
`sleep1`: a 2 ms or 1 ms `nanosleep` per pass) and stamps immediately after the
load that first returns it. The parent prints one JSON object: raw ticks for
every trial, the clock read cost before forking and after reaping, a
pass-interval histogram and both children's dispositions. Unfinished trials are
nulls. It fails only on mechanics and always reaps both children.

`tests/suites/witness_contract/worker_wait_clock_pair.py` compiles the pair with
the production worker's clang flags, runs the pacing-by-injection matrix one
cell at a time and writes `calibration.json`: every cell's raw output embedded,
labels for injected sleeps that overran and for system sleep, per-cell
summaries, a resolution section, the conditions before and after, and a list of
what the pair did not observe. `check_calibration` recomputes everything from
the raw ticks and checks the declared timebase against `CLOCK_MONOTONIC_RAW`.
Its constructed controls accept a valid receipt, reject each fault and withhold
the gate's credit under each condition that should withhold it.

The pair establishes finite-run facts for this machine: the clock read cost and
its tick, publication-to-observation latency per pacing, the actual length of
requested sleeps, a causal bound on the clock offset between two processes, and
whether the busy reader's combined uncertainty is within the pilot's 0.5 ms
gate. The sleeping readers' brackets are host polling behavior, measured by the
pilot as response, not instrument resolution. A hop between two processes can
finish within one tick here, so equal ticks across processes are accepted and
counted. The pair measures neither loop's real decisions, scheduling or core
placement, and its busy pass is not the worker's pass.

## Pilot driver

`tests/suites/witness_contract/check_worker_wait_pilot.py` is this fixture's
caller. It builds the stamped host with `PATCHES` and the neighbor with no
patches through `build_host`, requires both receipts to report the same flavour,
and stages each app once into `<artifacts>/staging/<kind>/` with the two workers
`build.sh` writes. In comparison mode both hosts carry `PATCHES`: the baseline
host over this repository's `runner/` and the candidate host over the compare
tree's, each staged with the stamp worker `build.sh` built from the same tree. It creates the stamp directory only after both hosts are
built, finds both stamp files through `stamp_paths()` and the marker through
`exported_path()`, and copies them into each trial directory (the marker, when
present, as `exported.json`) before removing them; residue left at cleanup is
copied into the artifacts before the directory is removed. It records its own
staged-executable identity (hashes, device and inode) before and after the
schedule, beside `staging.json`.

`tests/suites/witness_contract/worker_wait_pilot_reader.py` mirrors
`pww_stamp_page.h` with its own struct layout. Its default controls
(`witness_contract/worker_wait_pilot_controls`) check those offsets against
values written independently from the C layout, pack pages in program order,
and require the reader to accept them. The reader treats host events 101 and 153
as carrying earlier caller-read raws; a new `record(..., raw:)` call site in
`HostStamps` must be added to the reader's `HOST_PRESAMPLED`.

### Startup and resampling observations

The host exports whether its resampling helper was instrumented. Events 183/184
bracket each call's work before the fallback sleep, using the clock's wait key.
The reader reports ordinary resampling before first arrival separately from
sleep, and leaves older/uninstrumented captures unknown. This elapsed span can
include descheduling; it is not process CPU. Missing, malformed or dropped pairs
cannot establish zero work. Startup intervals distinguish spawn, readiness
observation, the worker's post-application stamp and first-arrival stamp. A
post-store stamp does not identify the instant of application or publication.
