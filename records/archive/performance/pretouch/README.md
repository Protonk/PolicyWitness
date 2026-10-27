# Pre-touch fixture

> Archive availability: original raw runs are not retained. Reproduction
> procedures describe the original `records/performance/` layout and pinned
> environment; committed derived evidence remains available.

Equipment for the pre-touch investigation: does touching the shared evidence
region before the worker applies its policy change whether the worker can
publish into it afterwards? Nothing here is part of the application; the
production host, worker and test harness are unchanged.

## Pieces

- `harness.c`: the host side. It prepares a POSIX shared-memory region of the
  production size exactly as the production host does (`shm_open`, immediate
  unlink, `ftruncate`, one `MAP_SHARED` mapping, descriptor 3 by spawn file
  action, policy bytes on descriptor 0) and varies only which pages are
  touched before the child applies. It observes the child independently:
  `mincore` over its own mapping at six points, `proc_pidinfo` region
  information for the child's mapping at three, `wait4` status and resource
  usage, and the values it reads back from the probe pages.
- `child.c`: the experimental worker. It maps descriptor 3, reads the policy,
  optionally touches the probe pages, compiles, waits for a host gate, applies,
  opens `/etc/hosts` as a witness that the policy is in force, waits for a
  second gate, stores a nonce-derived value at both ends of each probe page,
  reads it back, then tries a second mapping of descriptor 3 and an anonymous
  mapping, publishes `done` and waits for permission to exit. Every wait is a
  spin on a shared word timed by `mach_absolute_time`.
- `pretouch_shared.h`: the control block, at the start of page 0.
- `patch_harness.py`: makes six copies of the test harness
  `tests/suites/runner_c_worker_harness/harness.c`, unchanged and with the
  host's full-region page touch removed, for deny-default policy versions 1,
  2 and 3. Each copy's diff is kept beside it.
- `build.sh`: compiles everything into `.tmp/pretouch-build/`, checks the
  fixture's region size against the shipped worker's, executes each new
  binary once and writes `build.json` with hashes.
- `measure.py`: the shuffled schedule, the unified-log read and the raw run
  directory. `analyze.py`: the reader.

## Build and run

From the repository root:

```sh
records/performance/pretouch/build.sh
tests/lib/python.sh records/performance/pretouch/measure.py --label series1-b853
tests/lib/python.sh records/performance/pretouch/analyze.py \
  records/performance/runs/RUN-ID --out records/performance/evidence/RUN-ID
```

`measure.py` prints the raw directory
(`records/performance/runs/<UTC stamp>-pretouch-<label>/`) first and refuses an
existing one; refuses while any process runs the shipped worker or the fixture
child; holds `tests/.checkout.lock`; gives each unit a 30 s deadline and the
schedule a 600 s ceiling; and stops at the first unit after which such a
process remains.

## Conditions

Touch modes, applied before spawn:

| Mode | Host before spawn | Child before apply |
| --- | --- | --- |
| `none` | writes only the control block in page 0 | nothing |
| `host` | reads and writes back one byte of each probe page | nothing |
| `child` | page 0 only | reads and writes back one byte of each probe page |
| `both` | one byte of each probe page | one byte of each probe page |
| `prod` | zeroes the whole region, then touches every page as `runCWorker` does | one byte of each probe page |

Policies: `(version 1)(allow default)`, `(version 1)(deny default)`,
`(version 2)(deny default)`, `(version 3)(deny default)`, and `noapply`, which
compiles the allow-default policy and never applies it. Geometry: one probe
page (page 100 of 225, second-mapping marker on page 200), or 200 probe
pages (10–209, marker on page 215). Shipped units run the test harness copies
with the shipped worker's `bare_deny_default`, `max_slots_deny_default` and
`happy_default_allow` scenarios.

## What one unit records

`result.json` from the harness: the policy text, touch mode, geometry and
nonce; `mincore` vectors after `ftruncate`, before spawn, at each gate, after
`done` and after reap; the child's region information at each gate; the
child's control block (stage reached, pages stored, its own read-back, the
apply and witness results, `getrusage` samples where the policy permits them,
the second-mapping and anonymous-mapping results, and `mach_absolute_time` at
each stage); the values the host read from the probe pages; and `wait4`
status, signal and resource usage. `measure.py` adds `status.json` per unit,
`run.json` with conditions and identities, `deny-log.ndjson` with the kernel's
sandbox reports naming either executable over the run's window, and
`SHA256SUMS`.

`analyze.py` decides each unit's condition and outcome from these
observations, not from its label.

## Limits

- `mincore` and region information count pages resident in the shared
  object; they do not show which process has a page mapped. The per-process
  fault count comes from `wait4` and the child's pre-apply `getrusage`
  sample, because `getrusage` is refused after a deny-default apply.
- One store pattern is exercised: two 8-byte stores per page.
- The fixture child is ad-hoc signed and unentitled; the shipped worker is
  Developer ID signed. Both apply the same policies here.
