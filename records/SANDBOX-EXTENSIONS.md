# Sandbox extensions investigation

## Scope and checkpoint

M1 native controls now pass; M1 itself remains open. The user requested a
stopping point after the current sub-task, so the full mechanical selection
and required rendered-documentation assessment are pending. M0 remains pending
under the earlier M1-only direction. Production phases and extension behavior
are not implemented. This record is the current account of findings and
limitations, readable without commit history.

The next session should run the applicable registered `source_drift` checks,
render the affected Markdown, and commission the plan's fresh read-only M1
assessment. Resolve findings and record dispositions before closing M1. No
review, product build, XPC integration or BYOXPC acceptance is credited here.

## Equipment and reproducibility

- Initial source: `fb2750d5abddb81291086cc3ae590a9ca7d3e1d2`, initially clean.
  Investigation baseline commit: `4f819b7`.
- Host: macOS 26.7.1, build 25G241, arm64. Selected SDK:
  `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX27.0.sdk`.
- Identity: `Developer ID Application: Adam Hyland (42D369QV8E)`;
  certificate SHA-1 `1A6E85D06FC762993C8BD3E932556DED3985F030`.
- `security find-identity -v -p codesigning` found no identities inside the
  automation sandbox and this identity outside it. That is a keychain visibility
  observation, not evidence of native extension authority.
- All three experiment roles exec the same Developer ID signed binary, with
  hardened runtime and empty entitlement read-back. Signature verification
  passed. Worker and issuer real/effective UID were 501 and GID 20. The children
  receive only `PATH=/usr/bin:/bin` and `LC_ALL=C` in their environment.
- Accepted experiment binary SHA-256:
  `ad4121f9f81e8f228a349d1ea1e30cc21ac6c23506a79cde076fb079c2cfe87f`.
- Existing distribution v0.2.8 was not used as experiment equipment or rebuilt.
  No service installation was needed. Rust tools for later product work are
  under `/opt/homebrew/opt/rustup/bin`; Pandoc and Graphviz are available.

The credited native case is `sandbox_extensions_native/feasibility`, run with:

```sh
PW_TEST_OUT_DIR=tests/out/runs/extensions-m1-native-gate-20261012 \
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' \
  tests/run.sh --suite sandbox_extensions_native
```

The [run summary](../tests/out/runs/extensions-m1-native-gate-20261012/run.json)
and [case artifacts](../tests/out/runs/extensions-m1-native-gate-20261012/suites/sandbox_extensions_native/feasibility/artifacts/)
are gitignored and available only in this local checkout. Artifacts include
compiler commands, source snapshots and SHA-256 hashes, Git source/status,
OS/SDK/compiler facts, credentials, signature and entitlement read-backs,
controlled target metadata, commands, raw native reports, checker controls and
summary. The native and checker sources were uncommitted atop `4f819b7` during
this run; their retained snapshots identify the executed implementation. Later
edits to this record and the plan do not change that executed test code or input.
A future rerun must use a fresh managed output directory.

The fixture and checker are documented in their
[fixture README](../tests/fixtures/sandbox_extensions/README.md) and
[suite README](../tests/suites/sandbox_extensions_native/README.md). They use
neither PW's result classifier nor its phase protocol. The native run passed all
18 experiments: nine controls, each in a fresh plain and instrumented process
set. Constructed checker controls independently reject missing native/effect,
identity, boundary, cleanup and confinement evidence; they also admit unchanged
or unavailable queries, a failed release return, and fresh access after release.
Those constructed cases test the reader, not kernel behavior.

## Experimental boundary and independent effects

The checker creates an owned regular file, mode 0600, containing the 33 bytes
`PW independent extension witness\n`, a distinct second file, and a symlink to
the first. It records submitted and resolved issuance paths and device, inode,
mode, owner, group and size. It verifies known contents and metadata before and
after each experiment. This is test discipline, not a proposed product admission
restriction or proof that a path cannot change between observations.

Parent and worker establish successful baseline reads before policy application.
The worker enumerates descriptors before its first target open; both target
identities have zero inherited descriptors. Each ordinary read uses a fresh
open, fstat, bounded read and close. The retained-descriptor control alone holds
its post-consume descriptor, rewinds it and records its later read separately.

The worker applies exactly one policy. The positive policy is:

```scheme
(version 1)
(allow default)
(deny file-read-data)
(allow file-read-data (extension "com.apple.app-sandbox.read"))
```

The missing-predicate control removes only the final allow rule. At four fixed
boundaries the host queries its live owned worker with `sandbox_check`, operation
`file-read-data`, path filter and `SANDBOX_CHECK_NO_REPORT`, then releases that
boundary. Worker arrival, host query return and worker acknowledgement are
separate observations. Boundary 0 follows the pre-policy access and precedes
application; boundaries 1–3 precede fresh accesses before consume, after consume,
and after release (or the corresponding omitted intervention).

Native errno snapshots follow explicit zeroing. On success they are diagnostic,
not independent failures. Errno on an access operation is meaningful only if
that operation was attempted and returned failure; unattempted fields and failed
fstat identity storage do not establish observations.

## Observed native results

The table summarizes both plain and instrumented experiments; the raw reports
retain descriptor numbers, exact native results, errno and identities. “Read”
means the fresh descriptor retrieved all 33 expected bytes with matching fstat
identity. “Denied” means open returned -1/EPERM (1); no read was fabricated.
Every experiment had the baseline read and denied pre-consume fresh open.

| Control | Native issue / consume / release | Fresh after consume | Fresh after release or omitted release | External query returns, boundaries 0–3 |
| --- | --- | --- | --- | --- |
| Lifecycle | Non-null / handle 1 / 0 | Read | Denied | 0, 1, 0, 1 |
| Issuer exits before first release | Non-null / handle 1 / 0 | Read | Denied | 0, 1, 0, 1 |
| No consume | Non-null / omitted / omitted | Denied | Denied | 0, 1, 1, 1 |
| No release | Non-null / handle 1 / omitted | Read | Read | 0, 1, 0, 0 |
| No extension predicate | Non-null / handle 1 / 0 | Denied | Denied | 0, 1, 1, 1 |
| Issue for different file | Non-null / handle 1 / 0 | Denied | Denied | 0, 1, 1, 1 |
| Empty native issuance path | Null, ENOENT (2) / omitted / omitted | Denied | Denied | 0, 1, 1, 1 |
| Rejected token | Non-null / -1, EINVAL (22) / omitted | Denied | Denied | 0, 1, 1, 1 |
| Retained descriptor | Non-null / handle 1 / 0 | Read, held open | Fresh denied; retained read succeeds | 0, 1, 0, 1 |

The empty-path control deliberately replaces the prepared resolved path at the
native call. Both values are reported. It establishes an input-related native
refusal, not an issuer authority failure. The rejected-token control replaces
delivery with a fixed invalid string after successful issuance.

These controlled comparisons support a native file-extension experiment on this
host. They do not convert every permission-shaped failure into sandbox causation,
require prediction/enforcement agreement, or establish a general revocation
contract. In particular, release returned 0 while a previously opened descriptor
still retrieved the bytes. Successful consume and release also occurred without
fresh access in the missing-predicate and different-target controls.

## Authority, lifetime, transport and ABI decisions

An ordinary, non-root, Developer ID signed process with no entitlements
successfully issued the read-only file extension outside the automation sandbox.
No elevated authority or unavailable entitlement was required by this experiment.
The held issuer was observed live using owned-child `waitpid(..., WNOHANG)` at
each boundary. The exit control reaped it before the first query/release and
still completed the same native lifecycle and reads. Thus the initial production
design can use a short-lived ordinary issuer; actual app-bundle signing,
launch context, standard runner and BYOXPC behavior remain M3 obligations.

Use class `com.apple.app-sandbox.read`, flags 0, and the prepared resolved path
for the initial implementation. Preserve the submitted path separately. Keep
consume's signed 64-bit handle distinct from existing 32-bit status fields;
-1 denotes failure, and zero must remain representable as a handle. Release
takes that handle and returns an int. The experiment does not truncate either.

WebKit's [SandboxSPI.h](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
and [extension implementation](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
provide independent declaration and calling-convention evidence, including
freeing returned issue storage and treating consume -1 as failure. Live results
above establish the narrower host-specific feasibility.

Two separate, unlinked POSIX shared-memory objects successfully carried evidence
and token bytes. Only explicit mapping descriptors and `/dev/null` streams cross
exec; mapping descriptors are closed after mapping. The issuer erases returned
storage before freeing it. The worker erases delivery storage after its consume
decision, including omission/refusal; the parent erases it again at cleanup.
The parent scans serialized output against a transient token copy before writing,
then erases that copy. Child stdout/stderr are discarded and core dumps disabled.
No raw token is passed in arguments, environment, native evidence or retained
reports. This supports transient shared-memory transport as a candidate; M3
must still establish product confinement, partial transfer, timeouts and cleanup.
It does not establish protection against privileged memory inspection, swap or
all possible private-library/OS diagnostics.

## Allocation and resource observations

The first consume and first release in every instrumented worker were made only
after policy application. No native extension call warmed either path beforehand.
Dynamic `malloc_logger` and `__syscall_logger` callbacks use static lock-free
atomic bookkeeping, counting callbacks from any thread during each native call.
Apple's [libmalloc source](https://github.com/apple-oss-distributions/libmalloc/blob/main/src/malloc.c)
informs the hook and event-bit interpretation. Local positive controls, rather
than symbol presence, establish that the hooks actually worked here.

Every instrumented experiment observed malloc, free, mmap and munmap positive
controls before application and after the experiment: one allocation, one
deallocation, one VM allocation and one VM deallocation at each control. Every
attempted consume/release window recorded zero callbacks. Descriptor counts were
3 before consume, after consume and after release, except the retained-descriptor
control's intentional fourth descriptor after release. Plain runs have disabled
instrumentation; their zero fields are not allocation measurements.

Zero observed callbacks and unchanged descriptor snapshots cannot prove absence
of allocations through other paths, allocations outside the windows, transient
FDs, other resource types, or kernel resources. The instrumentation itself also
changes the process. Matching plain controls reduce, but do not eliminate, that
limitation. Measurements apply to the recorded host/library and exercised paths.

**Worker invariant decision for M3:** retain preallocated bounded PW-owned
reporting and coordination, with no explicit PW allocator use after application;
treat private native calls as separately observed boundaries whose internal
allocation/resource behavior is not guaranteed. Do not extend the existing
absolute no-post-apply-allocation statement to extension-enabled workers based
on these zero counters. M3 owns the corresponding production source comment and
architecture-account changes when it introduces these calls. M1 changes no
production worker or generated account and makes no new whole-process guarantee.

## Negative results and evidence accounting

All runs below are preserved, gitignored, local-only, and receive no full native
gate credit. Their artifact source snapshots identify the exact failed versions.

| Run under `tests/out/runs/` | Finding and disposition |
| --- | --- |
| `extensions-m1-first-20261012` | Interrupted while diagnosing child mmap failure (exit 91). A Darwin CLOEXEC descriptor duplicated onto itself did not become inherited. Fixture now moves source descriptors above the destination slots before spawn actions. |
| `extensions-m1-native-20261012` | Eight plain controls passed. All-flags-set issuance unexpectedly returned a token and consume handle 0; it was not a refusal control. Instrumented children failed before native calls. Do not interpret their zero counters. |
| `extensions-m1-allocator-probe-20261012` | Token-free logger diagnostics only. A temporary diagnostic-only early return incorrectly let the outer case label report pass. That label is explicitly rejected as feasibility evidence; no lifecycle matrix ran. The bypass was removed, and the checker now requires all 18 results before success. |
| `extensions-m1-controls-20261012` | Sixteen controls passed after allocator repair. An empty extension class also returned a token, handle 1 and release 0 without fresh target access. It did not establish failed issuance. The final refusal control changes the native path to empty instead. |

Crash-report stack frames from the token-free allocator investigation showed
`allocation_logger` entering `_tlv_get_addr`, which allocated while initializing
thread-local storage and recursively called the logger. Other failures reported
libmalloc traps in that recursion. Replacing thread-local bookkeeping with
static lock-free counters fixed the probe and permitted all instrumented native
controls. No private-library allocation conclusion is drawn from the failed
instrumentation. OS crash reports are outside the repository; only the diagnosis
is retained here, not process memory or token material.

## Remaining gate work and stopping state

The current native acceptance run passed, all owned native children were reaped,
and the checker removed its temporary target directory. No BYOXPC resources were
created. Test output and source snapshots remain in their managed directories.
The disposable development compile at `/private/tmp/pw-ext-dev-native` is not
accepted equipment.

A direct `source_drift/check.py` check accompanies this increment. The registered
mechanical selection and rendered assessment remain owed. There is no reviewer
or rendered artifact to credit yet. At resumption, compare retained source hashes
to the current fixture/checker and shared harness dependencies before reusing the
native result; rerun if relevant implementation changes. Then render the record,
plan checkpoint and affected fixture/suite documentation with their surrounding
context, commission the plan's fresh read-only assessment, resolve findings and
record reviewer/model, revision, renderer, artifacts and dispositions. Only then
can M1 close. M0 and all later implementation milestones remain untouched.
