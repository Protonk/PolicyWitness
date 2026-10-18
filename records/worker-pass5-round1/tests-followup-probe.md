# Test-skeptic follow-up — prepared characterization probe

The independent first report `tests.md` is unchanged. This follow-up records the
implementation requested by the coordinator; it contains no new execution credit.

Prepared files:

- `tests/suites/runner_unit/host_setup_oracle_sensitivity.py`
- `tests/suites/runner_unit/host_setup_oracle_sensitivity.sh`
- A new “Host setup oracle sensitivity (opt-in)” section in
  `tests/suites/runner_unit/README.md`.

The coordinator owns catalog/opt-in registry/coverage registration and execution.
I have not built, run the case, executed a test or committed changes. The new
files were reviewed as text only; compilation and runtime assumptions remain to
be verified by the public dispatcher.

## Implementation and evidence boundaries

The Python wrapper preserves the existing `host_setup_controls.py` bytes and
imports that saved recipe/checker without changing its source or its `run` and
`check` functions. Only its input root/fixture path globals point to each
disposable source copy. Each variant runs the full existing 22 observations and
10 rejected checker controls. A failed recipe retains its original artifacts and
the wrapper continues to the next variant, writing a failed summary rather than
crediting a partial run.

The four variants are:

1. Baseline host source.
2. One source edit changing ready-pipe duplication from its write end to its
   read end.
3. One source edit changing the shared-memory argument value from 3 to 4 while
   retaining the descriptor actions.
4. One source edit reducing the host evidence `munmap` length to one native page.

All variants use the same supplemental copied-fixture instrumentation. Production
files and the original fixture/checker remain unchanged. Exact replacement
anchors must occur once; input source inventories, per-edit before/after hashes
and text, and each complete instrumented source copy are retained.

The copied child observer adds `F_GETFL` return/errno/access mode and its actual
argument vector to its original receipt. It takes those descriptor observations
before opening its receipt file. It still does not apply a sandbox or implement
worker/issuer publications. The original fstat/PID/argc fields and legacy checks
are preserved. The new assertions require the two baseline worker configurations
to report the expected complete argv and readiness access mode, including the
deliberately wrong value/direction in their respective variants.

The copied setup fixture records the actual mapping address and acquisition
length separately from `setupMaps`. Immediately after a successful native
`munmap`, a fixed C helper uses static storage and `mincore` to query the last
page of that original extent, before legacy bookkeeping and without allocation
inside the helper. Its return establishes whether that selected page remains
mapped; resident-bit contents are not treated as mapping evidence.

After host owner teardown, the fixture snapshots the unchanged legacy map count.
A separate native helper then unmaps only a mincore-positive suffix within the
recorded acquired extent, independently records the cleanup return, and queries
that page again before returning to Swift. This cleanup neither edits legacy
maps/events nor changes the earlier native unmap return. It runs before fixture
exit and before receipt serialization. The old count must already be zero before
fixture cleanup; the partial-unmap cases additionally require an observed mapped
suffix, successful independent cleanup and subsequent `ENOMEM` absence. Baseline
and unchanged full-length cleanup paths require the immediate suffix query to
report `ENOMEM`, with no supplementary cleanup attempted.

Original recipe receipts remain under each `legacy-controls/` directory. Native
mapping observations are written to separate `.json.oracle.json` files, and the
wrapper creates `independent-observations.json` plus a top-level `results.json`.
It replays the same unchanged checker on every preserved receipt and records its
acceptance separately from the supplementary assertions.

## Meaning of a passing case

A pass requires the baseline and all three controlled counterexamples to be
accepted by the old oracle while the added native observations distinguish the
counterexamples. It characterizes the test gaps described in T2/T3; it does not
establish product safety or fix those gaps. Compilation errors, changed anchors,
unexpected native failures, unsupported mapping observations, failed independent
cleanup, or any old-oracle rejection fail this characterization explicitly.

T1 remains untouched for adjudication. The additional fixture calls can alter
timing and preserve extra mapping metadata; their limited scope is disclosed in
the case source and README. The real worker's response to wrong endpoints/argv
is not executed by this observer case, so conclusions about such responses
remain source-supported unless separately reproduced.

## Revision after managed run `worker-p5-setup` failed

The coordinator executed the first probe through the public dispatcher. That run
remains a historical **failure**, with every artifact left untouched. I inspected
its `controls/results.json`, the baseline issuer initialization-fault receipt,
and baseline/partial-unmap worker receipts. All four full legacy recipes completed
and accepted their 22 observations plus 10 rejected checker controls. The new
supplemental assertions failed; that run is not credited as a passing
characterization case.

The old observer's assumption was wrong: baseline `issuer-actions_init` records
a full 17,472-byte unmap with `mincore` still returning zero for the queried last
page. The baseline worker does likewise after its full 3,674,768-byte unmap.
The partial-unmap worker receipt also records zero after its independent suffix
cleanup. These returns do not establish that mappings survived. The earlier
prepared-design statement that the mincore return established mapping existence
is withdrawn. This is a probe-observation defect, not new evidence of a product
mapping leak. Neither the first report nor the failed run was amended.

The revised new case replaces mincore with bounded `mach_vm_region` scans. I
reviewed the installed SDK declarations in `mach/mach_vm.h:315–329` and the
`vm_region_basic_info_64` layout/count in `mach/vm_region.h:76–91`. The copied
fixture now wraps its existing real `munmap` in a native shim that scans the
entire page-rounded acquisition immediately before and after that call, retaining
the syscall result and errno. The unchanged legacy setup bookkeeping still sees
that native return. A positive control requires complete mapped coverage before
cleanup; a full-unmap negative control requires zero overlap afterward.

Each scan retains every native query address, kernel return, returned region
address/size, info count, protections, sharing/offset fields and object-name
right. Every valid object-name right is deallocated, with the attempt and native
result retained. A returned region beginning beyond the requested range counts
as no overlap, rather than as a mapping of the requested address. Query bounds,
native errors and port-deallocation errors leave the scan incomplete and fail
the case. Python separately reconstructs coverage from these raw ranges and
requires agreement with the native scan summary; it does not rely on a scalar
“mapping exists” result.

For partial unmapping, the native observations must show the original complete
acquisition, the expected mapped suffix after owner cleanup, and complete
coverage of that same known suffix when rechecked before fixture cleanup. Only
then does the fixture unmap that owned suffix and scan its entire extent again
to establish zero overlap. The old map counter must already be zero before this
independent cleanup, and the fixture never edits the legacy maps or events.
The extra native calls use static result storage; their timing and Mach-right
observations remain disclosed instrumentation effects.

I changed only the new sensitivity case, its new README section and this
follow-up report. I did not execute the revised case, build, commit, alter the
failed evidence, repair the original host oracle or change T1. The coordinator
will retain the next dispatcher run separately and adjudicate what it establishes.
