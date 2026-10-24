# Pre-touching the evidence region: build 853

Under the conditions tested, pre-touching the shared evidence region did not
change whether a sandboxed process could publish into it after applying a
restrictive profile. A process that had applied `(version 1)`, `(version 2)`
or `(version 3)` `(deny default)` stored into a page that no process had ever
touched, the page came into existence at that store, the host read the stored
value back, the process exited 0, and the kernel logged no sandbox report for
the store. The same held for 200 such pages at once. Every one of 89 fixture
units and 16 shipped-worker units published.

What did differ between the conditions was the work the store cost the
sandboxed process: one page fault per untouched or host-touched page, none for
a page the process had written before applying. What the deny-default
profiles did refuse after application was the `mmap` system call itself under
versions 2 and 3, so a mapping made before application was load-bearing where
touching was not. These observations describe one machine, OS build, object
type and set of policies; they do not establish equivalence elsewhere.

## Evidence and conditions

The shipped worker was `pw-probe-runner` from `dist/PolicyWitness.app`,
version 0.3.3, build 853, commit `1bf0341`, SHA-256 `c8ac685b…`, Developer ID
signed with the hardened runtime. The runner, worker and test harness sources
are unchanged since that commit; the checkout was at `1fc9281` with only this
investigation's files untracked.

The fixture ([`pretouch/`](pretouch/README.md)) was compiled from this
repository by Apple clang 21.0.0 against the macOS 27.0 SDK: the experimental
child `pretouch_child` (SHA-256 `0005ca2e…`, ad-hoc linker-signed, no
entitlements) and its host `pretouch_harness` (`4f5e8c09…`). Six copies of the
test harness `tests/suites/runner_c_worker_harness/harness.c` were compiled
against the current ABI header: unchanged, and with the host's full-region
page touch removed, each for deny-default policy versions 1, 2 and 3. The
recorded diffs are in the run's `build.json` hashes and beside the copies
under `.tmp/pretouch-build/variants/`.

The machine was a Mac17,3 (Apple M5, 10 logical CPUs, 16 GiB, 16 KiB pages)
running macOS 26.7.1 (25G241), on AC power. The run was interactive, with this
agent session active; the load average was 1.98 at the start and 3.12 at the
end. The whole schedule took 24.5 s.

The run is
[`20261024T163347857619Z-pretouch-series1-b853`](evidence/20261024T163347857619Z-pretouch-series1-b853/summary.json):
`measure.py` SHA-256 `caf419c2…`, read by `analyze.py` SHA-256 `6ba44ca6…`.
It ran 105 units in a recorded shuffled order, seed 20261024:

- every unit exited within its deadline; none was killed;
- all 495 raw checksums verified with no unattested file;
- no process running the worker or the fixture child remained after any unit
  or after the run;
- the unified log returned 211 kernel sandbox reports naming either
  executable in the run's window, every one attributable to a unit's process.

Raw files are local to this checkout. A one-repeat pilot of the same schedule
(48 units, all published) ran first into scratch and is not retained.

## What pre-touching is in the implementation

Host, [`CWorker.swift`](../../runner/Sources/PWRunnerCore/CWorker.swift):
`runCWorker` creates the object with `shm_open`, unlinks it, sizes it with
`ftruncate` and maps it once (`MAP_SHARED`, read-write). It then zeroes the
whole region with `memset` (line 990), writes the header, slots and
parameters, and finally reads and writes back one byte of every page (lines
1060–1069) before storing `prepared` and spawning the worker. The `memset`
already writes every byte of every page, so the page loop is a second write
to pages the host has already backed. The host comment says as much: touching
"does not establish worker page residency or eliminate post-apply faults".

Worker, [`pw_probe_runner.c`](../../controller/tools/pw_probe_runner/pw_probe_runner.c):
`map_region` (line 561, called at 1648) makes the worker's own mapping before
compilation. Before `sandbox_apply` (line 1945) the worker writes the
evidence header (first progress word at line 1663) and, for every populated
slot, the step and target terminators and `completed = 0` (lines 1715–1720).
Measured against the ABI header, a slot's written fields occupy its first
6,248 bytes, no slot's written range crosses a 16 KiB page boundary, and the
evidence header and diagnostic share the last page. So every page the shipped
worker publishes into after application, the header page, each populated
slot's page and the evidence page, is one the worker itself wrote before
application. The host's touch adds nothing to the worker's page state;
the worker's post-apply publications take no first-touch fault whether or not
the host touched the region.

At the investigated commit, `1fc9281`, the test harness's copy of the touch
stated the rationale the host comment does not: the touch is "so the
post-apply path never depends on lazy allocation (which a strict sandbox
would block)" (`harness.c` lines 665–667 at that commit). The experiment
below tests that parenthetical directly.

## Experimental distinction

The fixture holds everything about the mapping constant and varies only who
touched the probe pages before application:

- The object is created exactly as `runCWorker` creates it: `shm_open`,
  immediate unlink, `ftruncate` to the production region size (3,674,768
  bytes, 225 pages), one `MAP_SHARED` read-write mapping in the host,
  descriptor 3 by `posix_spawn` file action, policy bytes on descriptor 0.
- The child maps descriptor 3 once, before compilation, exactly as
  `map_region` does, then reads the policy, compiles, applies, and stores an
  8-byte nonce-derived value at the first and last words of each probe page.
  It never maps again before the store. The same binary ran every condition.
- The probe pages are far from the control block in page 0: page 100 for the
  single-page conditions and pages 10–209 for the 200-page conditions.

| Touch mode | Host, before spawn | Child, before apply |
| --- | --- | --- |
| `none` | page 0 only | nothing |
| `host` | reads and writes back one byte of each probe page | nothing |
| `child` | page 0 only | reads and writes back one byte of each probe page |
| `both` | one byte of each probe page | one byte of each probe page |
| `prod` | `memset` of the whole region, then every page, as `runCWorker` | one byte of each probe page |

The distinction was established by observations the child cannot forge:

- **`mincore` over the host's mapping** at six points. After `ftruncate` no
  page of the object was resident. Before spawn, in `none` and `child` units
  the probe pages reported only `MINCORE_ANONYMOUS` (value 128), and in
  `host`, `both` and `prod` units `INCORE|REFERENCED|MODIFIED|ANONYMOUS`
  (135); `prod` showed all 225 pages resident, `host` and `both` the probe
  pages and page 0 only, `none` and `child` page 0 only. At the first gate,
  after the child's optional touch and before `sandbox_apply`, `child` units
  now showed the probe pages resident. At the second gate, after
  `sandbox_apply` and before the store, nothing had changed. After `done`,
  every probe page was resident in every unit. All 89 units matched their
  intended condition at all three points.
- **`proc_pidinfo` region information for the child's mapping** at the same
  gates. Address, size and share mode were identical across conditions
  (89 of 89), and the resident count moved with the condition: 1, 1, 2 pages
  for `none` with one probe page; 1, 1, 201 for `none` with 200; 225
  throughout for `prod`.
- **The child's page faults.** `wait4` returned the child's lifetime minor
  faults, and the child published a `getrusage` sample taken after compiling
  and before the first gate. Their difference is the faults taken from just
  before `sandbox_apply` to exit. Under versions 2 and 3, where no other
  post-apply system call succeeded, that difference was exactly 1 for `none`
  and `host` with one probe page, exactly 200 with 200 pages, and exactly 0
  for `child`, `both` and `prod`. Under the policies that allowed
  `getrusage` after application, the child's own interval sample around the
  store gave the same 1, 200 or 0.

So in `none` the sandboxed process's store was the first access to a page by
any process, and the kernel created the page then; in `host` the page
existed but the process had no translation for it; in `child`, `both` and
`prod` the store faulted nothing.

Application was witnessed in every unit: `sandbox_apply` returned 0, a
post-apply `open("/etc/hosts")` failed with EPERM under every deny-default
policy and returned a descriptor under `(allow default)` and in the `noapply`
control, and the kernel's reports for the child named that open.

## Observations

Single probe page, three units per cell. "Faults" is the child's minor
faults from its pre-apply sample to exit; under `allow1`, `deny1` and
`noapply` two of them belong to the post-apply mapping controls described
below.

| Policy | Touch | Units | Published | Probe page backed before spawn / before apply | Faults | Store, median µs |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| allow1 | none | 3 | 3 | none / none | 3 | 4.8 |
| allow1 | host | 3 | 3 | all / all | 3 | 2.4 |
| allow1 | child | 3 | 3 | none / all | 2 | 0.6 |
| allow1 | both | 3 | 3 | all / all | 2 | 0.5 |
| allow1 | prod | 3 | 3 | all / all | 2 | 1.0 |
| deny1 | none | 3 | 3 | none / none | 3 | 3.3 |
| deny1 | host | 3 | 3 | all / all | 3 | 2.0 |
| deny1 | child | 3 | 3 | none / all | 2 | 0.7 |
| deny1 | both | 3 | 3 | all / all | 2 | 0.8 |
| deny1 | prod | 3 | 3 | all / all | 2 | 1.0 |
| deny2 | none | 3 | 3 | none / none | 1 | 5.1 |
| deny2 | host | 3 | 3 | all / all | 1 | 4.8 |
| deny2 | child | 3 | 3 | none / all | 0 | 2.6 |
| deny2 | both | 3 | 3 | all / all | 0 | 1.6 |
| deny2 | prod | 3 | 3 | all / all | 0 | 1.0 |
| deny3 | none | 3 | 3 | none / none | 1 | 2.5 |
| deny3 | host | 3 | 3 | all / all | 1 | 5.9 |
| deny3 | child | 3 | 3 | none / all | 0 | 1.5 |
| deny3 | both | 3 | 3 | all / all | 0 | 1.5 |
| deny3 | prod | 3 | 3 | all / all | 0 | 1.3 |
| noapply | none | 3 | 3 | none / none | 3 | 1.4 |
| noapply | host | 3 | 3 | all / all | 3 | 1.2 |
| noapply | child | 3 | 3 | none / all | 2 | 0.4 |
| noapply | both | 3 | 3 | all / all | 2 | 0.6 |
| noapply | prod | 3 | 3 | all / all | 2 | 0.6 |

Policies: `allow1` is `(version 1)(allow default)`; `deny1`, `deny2` and
`deny3` are `(version N)(deny default)`; `noapply` compiles the allow-default
policy and never applies it.

Two hundred probe pages, two units per cell:

| Condition | Units | Published | Backed before spawn / before apply | Faults | Store, µs |
| --- | ---: | ---: | --- | ---: | ---: |
| allow1 none | 2 | 2 | none / none | 202 | 161–324 |
| deny1 none | 2 | 2 | none / none | 202 | 149–464 |
| deny2 none | 2 | 2 | none / none | 200 | 124–396 |
| deny2 host | 2 | 2 | all / all | 200 | 126–322 |
| deny2 both | 2 | 2 | all / all | 0 | 6–21 |
| deny3 none | 2 | 2 | none / none | 200 | 224–307 |
| noapply none | 2 | 2 | none / none | 202 | 108–128 |

"Published" means all of: the child reached its read-back stage with every
page stored, its own read-back matched, the host read the expected value at
both ends of every probe page through its own mapping, every host wait was
satisfied, and the child exited 0 without being killed. No unit was
classified as stored-but-unreadable, died during the store, or ended before
it.

In a representative `deny2 none` unit the child had mapped 3.7 ms after
spawn, compiled at 15.5 ms, returned from `sandbox_apply` at 17.0 ms, stored
between 18.222 and 18.228 ms and published `done` at 18.236 ms.

**Post-apply controls.** After the store, the child tried a second
`MAP_SHARED` mapping of descriptor 3 and a fresh anonymous mapping, writing a
marker through each if it succeeded, and took two more `getrusage` samples.

| Policy | Second mapping of descriptor 3 | Anonymous mapping | `getrusage` | Kernel reports for the child |
| --- | --- | --- | --- | --- |
| allow1, noapply | succeeded; host read the marker | succeeded | succeeded | none |
| deny1 | succeeded; host read the marker | succeeded | succeeded | `file-read-metadata /etc` |
| deny2, deny3 | EPERM | EPERM | EPERM | `syscall-unix 5` (open), `syscall-unix 117` (getrusage), `syscall-unix 197` (mmap) |

Under versions 2 and 3 the kernel's reports name the system call, not an
operation on a path, and the refused calls are `open`, `getrusage` and `mmap`
(numbers from the SDK's `sys/syscall.h`). No report of any kind accompanied
a store, in any unit. Report counts in the log are coalesced by the kernel
and are not used here; the set of operations is.

**Shipped worker.** The test harness copies ran the shipped worker with the
host's full-region page touch present or removed:

| Harness copy | Scenario | Units | Published | Slot 0 | Kernel reports for the worker |
| --- | --- | ---: | ---: | --- | --- |
| touch_v1 | bare_deny_default | 2 | 2 | completed, rc 1, errno 1 | `file-read-metadata /etc` |
| notouch_v1 | bare_deny_default | 2 | 2 | completed, rc 1, errno 1 | `file-read-metadata /etc` |
| touch_v2 | bare_deny_default | 2 | 2 | completed, rc 1, errno 1 | `syscall-unix 5` |
| notouch_v2 | bare_deny_default | 2 | 2 | completed, rc 1, errno 1 | `syscall-unix 5` |
| touch_v3 | bare_deny_default | 2 | 2 | completed, rc 1, errno 1 | `syscall-unix 5` |
| notouch_v3 | bare_deny_default | 2 | 2 | completed, rc 1, errno 1 | `syscall-unix 5` |
| touch_v1 | max_slots_deny_default | 1 | 1 | 256 slots completed | none |
| notouch_v1 | max_slots_deny_default | 1 | 1 | 256 slots completed | none |
| touch_v1 | happy_default_allow | 1 | 1 | completed, rc 0 | none |
| notouch_v1 | happy_default_allow | 1 | 1 | completed, rc 0 | none |

"Published" here means `applied` and `done` set, every slot completed, exit
0 and no cleanup kill; the ready byte was received in every unit. These
units show that removing the host's touch loop changes nothing for the
shipped worker. They do not exercise a first touch after application,
because, as the source inspection shows, the shipped worker's own pre-apply
writes reach every page it later publishes into.

## Interpretation

**Pre-touching did not decide publication.** Under every tested policy, the
sandboxed process's first-ever store into a never-backed page of the shared
object succeeded, the page was created at that moment, and the host read the
value. Touching before application removed the page fault from the store,
nothing more. The cost of the fault was about 1–2 µs per page here, zero-fill
and translation-only alike, with no visible difference between applied and
unapplied processes at this sample size.

**Mapping before application is what the restrictive profiles make
necessary.** After `(version 2)` or `(version 3)` `(deny default)`, the
`mmap` system call was refused outright, for the evidence descriptor and for
anonymous memory. A worker without a mapping at that point could not obtain
one. Under `(version 1)(deny default)` both mappings succeeded after
application. The version number therefore mattered to mapping and to raw
system calls such as `getrusage`, and not to faulting on an existing mapping.

**The explanation consistent with these observations** is that page faults
on an established mapping are resolved by the virtual memory system without
consulting the sandbox, while `mmap`, `open` and `getrusage` are system calls
the version 2 and 3 deny-default profiles filter. The experiment establishes
the behavior, not the kernel's code paths. An alternative in which the
sandbox does mediate faults but permitted these for another reason, such as
the object being anonymous shared memory, the process being ad-hoc signed, or
the faults being zero-fill rather than file-backed, is not excluded by this
evidence; it is only constrained to behave identically for the tested
object, signature and policies.

**For the shipped worker the question is moot in a second way.** Its own
pre-apply writes already back and map every page it publishes into, so no
production publication takes a first-touch fault regardless of the host's
touch. The host's `memset` and page loop commit all 225 pages of every
region up front; the worker then publishes into pages it has already written.

**On the rationale recorded in the test harness.** The claim that a strict
sandbox would block lazy allocation of these pages was not borne out by bare
`(deny default)` at any version on this build. The production host's own
comment makes no such claim.

**Not observed here.** None of the 69 processes that applied a bare
`(deny default)` profile, 55 fixture children and 14 shipped workers, had
its exit refused; all exited 0.

## Limits

- One machine, OS build and page size; one object type, an unlinked POSIX
  shared-memory object of the production size, mapped once `MAP_SHARED`
  read-write before application; stores of 8 bytes at two offsets per page;
  1 or 200 pages. Other object types, mapping flags, access patterns or
  profiles with explicit rules were not tested.
- Five policies: bare allow-default and bare deny-default at versions 1, 2
  and 3, plus an unapplied control. Profiles that deny specific memory or
  process operations were not tested.
- A first touch after application was exercised only by the ad-hoc signed,
  unentitled fixture child. The shipped worker, Developer ID signed with the
  hardened runtime, never reaches that path, so its behavior on it is not
  observed.
- `mincore` and region information count pages resident in the shared object
  and say nothing about a particular process's translations. The
  per-process fault evidence is a count difference; it is exact under
  versions 2 and 3 because every other post-apply call failed, and under the
  other policies the two extra faults are accounted for by the mapping
  controls' stores.
- The kernel's sandbox reports show reported refusals; a refusal the kernel
  does not report would not appear. The stores' success does not rest on the
  log; it rests on the host's read of the values.
- Quiet-machine timing was not sought; the microsecond figures describe this
  interval and are not a measurement of fault cost.
- Memory pressure, system sleep, concurrent workers and the extension token
  channel were not exercised.

## One further question

After a version 2 or 3 profile is applied, does any PolicyWitness attempt
kind's native result depend on a system call the profile's syscall filter
refuses, such as the `mmap` behind an allocation inside libc or libsandbox,
rather than on the rule governing the attempted operation?

It deserves investigation because the instrument reports a permission-shaped
native result as the attempted operation's outcome. This run showed that
under versions 2 and 3 the kernel refuses `mmap`, `getrusage` and `open` as
raw system calls, reports them by number, and returns the same EPERM a
denied operation returns. An attempt whose implementation allocates after
application could fail on the allocation under a profile that allows the
operation itself, and the reply would not distinguish the two.

The distinguishing observation is, per attempt kind, a profile
`(version 2)(deny default)` plus rules allowing exactly the attempted
operation, with the kernel's sandbox reports for the worker's PID collected
over the attempt window: success with no report means the attempt did not
depend on a refused call; a failure accompanied by a `syscall-unix` report
means the result was shaped by the filter, not the operation's rule; a
failure with no report points elsewhere. The same attempts under `(version 1)`
give the contrast.

## Reproduction and cleanup

The [fixture README](pretouch/README.md) has the build, schedule and reader
commands. The evidence directory holds `summary.json` (per-condition counts,
attestation and the deny-log account), `units.json` (each unit's condition,
application witness, faults, store, controls, disposition, attributed
sandbox reports and timeline) and `run-record.json` (identities, build
hashes, conditions with the process snapshot trimmed to CPU shares).

Cleanup:

- Every shared-memory object was unlinked at creation; no name remains.
- No child process remained after any unit or after the run.
- The checkout lock was released.
- Build intermediates and the harness copies are in `.tmp/pretouch-build`.
