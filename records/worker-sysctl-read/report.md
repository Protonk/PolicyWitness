# Sysctl read contract investigation

Status: investigation complete; recommendation awaiting design selection. No
production behavior, shared plan, limits inventory or wire contract was changed.
This record belongs to
[SYSCTL-READ-PLAN.md](../../controller/tools/pw_probe_runner/SYSCTL-READ-PLAN.md).
Source baseline: `503156f0693dd8a22acf633efccdc93e300f2ebc`.

## Recommendation

Keep `sysctl/read` as one post-apply `sysctlbyname` value-read invocation with a
non-null 4096-byte destination, no preliminary sizing call and no retry. Give
that capacity a source name and an explicit limits entry. Retain call status
and errno as today, and add a small optional observation carrying the supplied
capacity and raw value of `oldlen` after the call returns. Continue discarding
the value bytes.

The length observation should be named for what PW measured, for example
`sysctl_read: { buffer_capacity: 4096, oldlen_after: N }`. It must not be named
`required_size`, `bytes_copied` or `truncated`. In the native controls, a failed
4096-byte read changed thousands of destination bytes while returning
`oldlen = 0`. Another failure left `oldlen` equal to its input capacity. Neither
length is an independently measured byte count or a diagnosis of the failure.

This preserves the existing experiment and makes its bound reviewable without
adding post-apply allocation, another API invocation, retry policy or a request
parameter. The source/limits repair is separable and sufficient to disclose the
hidden bound. The optional observation is the recommended additional step
because it makes a run's actual supplied capacity and native out-parameter
available without requiring a reader to recover them from a source revision.
If only disclosure is wanted, stop after the source/limits repair and explicitly
retain the current absence of per-call length evidence.

No dependency on exec supervision or launch-descriptor ownership was found.
The settled terminal-worker lifetime and phase qualification rule are inputs,
not subjects reopened by this investigation.

## Current implementation: source-established facts

[`attempt_sysctl_read`](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
declares `char buf[4096]`, initializes `len = sizeof(buf)`, and invokes
`sysctlbyname(slot->target, buf, &len, NULL, 0)` once. The buffer and updated
length are discarded. This promises neither retrieval of an arbitrarily sized
value nor publication of its bytes. A returned failure goes through
`fail_from_errno`: the public attempt `rc` is PW status **1**, not the native
return **-1**; saved errno and an API-labelled error are retained. Success
publishes PW status 0. Changing `rc` into a raw return would be a separate
meaning change and is not proposed.

The host's completed-slot read and
[CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
map a failed `read` action to `sysctl_failed`. Existing comparison handling may
identify a permission-shaped errno; it does not diagnose ENOMEM as a buffer
bound. [limits.json](../../docs/limits.json) limits the target name but has no
entry for this output buffer.

The existing
[`runner_filter_sysctl_name`](../../tests/suites/runner_filter_sysctl_name/README.md)
case exercises a denial-shaped attempt on `kern.osrelease`, with unavailable
prediction for the operation/filter pair. It is compatibility evidence, not a
test of output capacity, returned length or size-only equivalence.

## Applicable native sources and their limits

Apple's archived [userland sysctl manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/sysctlbyname.3.html)
distinguishes a null-destination size query from a value read. It describes
in/out `oldlen`, warns that some sizing estimates concern changing data, and
lists multiple possible ENOMEM conditions. Its generic description of copying
on ENOMEM is insufficient to define a universal byte-count oracle for the
observed modern handlers.

Apple's [XNU `kern_newsysctl.c`, tag `xnu-12377.121.6`](https://github.com/apple-oss-distributions/xnu/blob/xnu-12377.121.6/bsd/kern/kern_newsysctl.c)
separates `sysctl_old_kernel` from `sysctl_old_user`. The latter can reject a
chunk before advancing its output index; `userland_sysctl` reports an index
bounded by supplied capacity. `sys_sysctlbyname` may return other errors without
replacing the caller's length. Its allocation path also has ENOMEM. The MAC
check receives the destination pointer and input length. Those facts do not
establish that null and non-null destinations have equivalent policy effects.
The kernel KPI named `sysctlbyname` uses a different path, so its description is
not a substitute for the userland contract.

Sources were read on 2026-10-18. That published XNU tag is not the exact installed
kernel (`xnu-12377.161.15.700.19~2`). These are source explanations and reasons
to avoid overclaiming, not proof of an installed binary's control flow. The
observations below establish the local outcomes independently.

## Native observations

The standalone equipment is [native_read.c](native_read.c), driven by
[run_native.py](run_native.py). It uses real userland `sysctlbyname`, with
fixed canary regions immediately outside the supplied capacity. It initializes
the destination to a sentinel and counts bytes that differ afterward. That
count establishes some writes independently of `oldlen`; it is not an exact
copy count because a written byte can equal the sentinel. No value bytes,
process entries, socket entries or hashes of their contents were retained.

The helper has no specimen sandbox and allocates its observation buffer before
calling the API. It is native semantics equipment, not a replacement worker or
evidence about post-apply allocation. Each observation uses a fresh helper
process. Consequently the discovery and larger read below are separate native
calls in separate processes; they illustrate size/value differences but do not
test an adaptive algorithm in one worker.

Observed on macOS 26.7.1, build 25G241, Darwin 25.6.0 arm64, using Apple clang
21.0.0. [Provenance](provenance.json) retains exact top-level commands, source
and equipment hashes, environment and app-run references.
[Per-call commands](native-observations-20261018/commands.json) retain argv,
stdout, stderr and process status. All native helper processes exited 0;
their JSON retains the sysctl call's separate return status.

| Name and operation | Supplied capacity | Native rc / errno | `oldlen` after | Bytes differing from sentinel |
| --- | ---: | --- | ---: | ---: |
| `kern.osrelease`, size-only | 0, destination null | 0 / 0 | 7 | 0 |
| `kern.osrelease`, value read | 0, destination non-null | -1 / ENOMEM | 0 | 0 |
| `kern.osrelease`, value read | 1 | -1 / ENOMEM | 0 | 0 |
| `kern.osrelease`, value read | 6 | -1 / ENOMEM | 0 | 0 |
| `kern.osrelease`, value read | 7 | 0 / 0 | 7 | 7 |
| `kern.osrelease`, value read | 4096 | 0 / 0 | 7 | 7 |
| `kern.proc.all`, size-only | 0, destination null | 0 / 0 | 404352 | 0 |
| `kern.proc.all`, value read | 4096 | -1 / ENOMEM | 0 | 3888 |
| `kern.proc.all`, value read | 404352 | 0 / 0 | 401112 | 401020 |
| `kern.proc.all`, second size-only | 0, destination null | 0 / 0 | 404352 | 0 |
| nonexistent control name, value read | 4096 | -1 / ENOENT | 4096 | 0 |

All canaries remained unchanged. Exact raw numbers are in
[observations.json](native-observations-20261018/observations.json).

The controlled capacity sweep on the same small, stable named value provides
evidence of the capacity boundary beyond errno alone. The live oversized table
shows why a single failed call cannot report required size or absence of writes
from its returned length. The gap between the size estimate and successful
read's length is observed; it does not by itself prove a race, padding, growth
or shrinkage. Discovery and value-read success are distinct observations.
No claim is made about which cause produced an arbitrary production ENOMEM.

The small-value checker passed and rejected three independently introduced
interpretation mutations: replacing the 4096-capacity read's returned length
with its capacity; replacing a short read's returned length with discovered
required size; and treating a non-null zero-capacity read as size-only. The
specific rejection messages are retained in
[checker-controls.json](native-observations-20261018/checker-controls.json).
These controls establish the equipment's interpretation for these observations,
not a future production metadata implementation.

## Signed-app compatibility observation

Run `20261018T192613Z_fe6fb31d` selected exactly:

- `runner_filter_sysctl_name/checker_controls`;
- `runner_filter_sysctl_name/prediction_unavailable_attempt_observed`.

Both passed, with no skips or unrun cases; the app was valid before execution
and unchanged afterward. The live attempt retained `rc: 1`, `errno: 1`
(EPERM), `outcome: sysctl_failed`, worker provenance and a completed lifecycle;
prediction remained unavailable. These are observations under that specimen,
not a general causal interpretation of permission failures. A compact exact
step extraction is in [compatibility-observation.json](compatibility-observation.json),
and the console is in [compatibility-console.log](compatibility-console.log).

The complete run, original specimen, raw envelope, checker fixtures and app
inventory are under
[tests/out/runs/worker-sysctl-read-baseline-20261018/](../../tests/out/runs/worker-sysctl-read-baseline-20261018/).
That directory is gitignored and available only in the local checkout. This
investigation did not build or alter the signed app. The inventory identifies
the tested bytes; its generated worker identity is
`4dd8d75126025defa7b9719fb434d265b69f25b9d3bd6d9fd3836d1321f02976`.
The repository source baseline is not asserted as the original app-build commit.

## Alternatives and costs

| Choice | Operation promised | Cost and consequence |
| --- | --- | --- |
| Explicit fixed-capacity value read | One non-null 4096-byte `sysctlbyname` invocation | Preserves the current stack buffer, call shape and bounded storage. Failing oversized values remain legitimate observations. Recommended. |
| Size-only query | One invocation with a null destination | Obtains a size observation, not value retrieval. Changing existing `read` to this would change its meaning. A separately named action would need admission and request-contract work. |
| Discover, allocate, read | A sizing invocation followed by an allocated value read | Adds post-apply allocation and another API invocation. Allocation failure and a failed first call must remain distinct; a changed size can defeat the second call. Requires a memory cap and an explicit retry/no-retry rule, plus evidence for each stage. |
| Raise the fixed constant | The same bounded read at a larger bound | Changes resource use and the capacity being tested; leaves the conceptual bound and disclosure problem in place. No current requirement justifies it. |
| Request-selectable capacity | A caller-chosen bounded read | Adds request admission, an upper bound and request/ABI transport. Useful for deliberately testing capacity, but unnecessary to disclose the current fixed operation. |
| Name and document only | Existing operation and output | Smallest repair to WA-11. No new output or native calls; per-run returned-length evidence stays unavailable. |

Moving adaptive allocation or discovery before sandbox application would change
the apparatus again. It would not answer how a fresh post-apply value read acts
with the existing resources. No such pre-acquisition is recommended. Likewise,
an adaptive retry's second success must not overwrite its first failure or be
presented as a single attempted call.

## Representation and verification consequences

The source/limits-only repair needs a named constant used in the actual array
and length initialization, a limits-manifest entry with appropriate source and
value/boundary controls, and regenerated limits/user-guide/worker accounts.
Worker source identity regenerates even for a naming/comment change. It needs
no request, response or envelope version change and no ABI layout change.

The recommended optional observation needs two integer facts in the internal
slot plus explicit validity, read only after the existing slot completion
publication. Reserve layout space explicitly and update the Swift mirror,
layout probes/golden and generated identity together. A completed sysctl call
must preserve post-call length on success and failure, including unchanged
length. No metadata is recoverable from an unpublished slot, nor should a host
synthesize observed capacity solely from the requested kind or a known constant.

Add the optional object to `PWRunnerAttemptResult`, map it in
`CWorkerSlotResult` and the orchestrator, and update Swift reply validation and
independent Python/Rust readers and fixtures as applicable. Keep existing PW
status, errno, outcome and comparison rules. The two new fields need no duplicate
native status: their presence identifies returned-call metadata, while the
existing status/errno retain their documented meanings. If raw native rc is
later desired, add it separately rather than reinterpret PW's `rc`.

Under [CONTRACT.md](../../docs/CONTRACT.md#when-a-number-moves), an optional
additive field can avoid a response bump when old documents remain valid,
absence means unknown, and existing reading rules stay unchanged. Making this
object mandatory for all completed sysctl results, reclassifying failures from
it, or reinterpreting an existing field would require a fresh version decision.
There is no request change in the recommendation. Size-only/adaptive replacement
would change the operation's meaning and must not be hidden behind this repair.

An implementation should establish more than successful compilation:

- A narrow native-call substitute independently records the actual incoming
  pointer and capacity, returns an independently chosen out-length, and checks
  that the published observation matches both. A mutation passing a shortened
  buffer while publishing 4096 must fail. A mutation publishing the input length
  instead of the post-call length must fail.
- Cover fitting, exactly fitting and oversized synthetic values at the actual
  4096 boundary; preserve failure oldlen values of zero, unchanged capacity and
  a separately chosen value. Include ENOMEM injected for a non-capacity reason,
  so a checker cannot derive a `too_small` or sandbox-cause classification.
- Retain a native small-value capacity sweep and live oversized observation as
  native evidence. A dynamic table is not a stable exact-size test fixture.
  Keep capacity controlled independently of the field being checked.
- Exercise completion gating, other attempt kinds, missing optional metadata,
  malformed metadata and old valid replies in producer and independent-reader
  controls. Do not interpret zero-filled/unpublished fields as observed zeros.
- Rebuild the app through the signed pipeline; run the existing sysctl filter
  suite and relevant worker/ABI/reader controls. This investigation's standalone
  reads cannot establish host transport or future publication correctness.

Open limits are bounded: no all-handler survey, no proof of size-only policy
equivalence, no stress experiment for changing data, and no causal ENOMEM
diagnostic. None is needed to select the preserved bounded operation and raw
length representation. A future requirement to fetch complete values would
justify reopening the adaptive-operation design explicitly.
