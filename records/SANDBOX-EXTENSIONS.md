# Sandbox extensions investigation

## Scope and checkpoint

M1 is complete: the native feasibility controls, registered mechanical checks,
and fresh rendered-documentation assessment passed. The sole rendering finding
was corrected and rechecked. The M1-only scope remains in force, with M0 pending.
Production phases and extension behavior are not implemented. This record is the
current account of findings, decisions and limitations, readable without commit
history.

Implementation commit `e8effbd` contains the native fixture, registered suite and
findings; `e423705` records mechanical checks and evidence reuse. The closure
checkpoint adds the completed review and disposition below. No product build,
XPC integration or BYOXPC acceptance is credited. On resuming the broader plan,
complete M0 before beginning M2; the M3 authority, ABI, transport and worker
invariant decisions are recorded here for integration and further testing.

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

## Mechanical checks and evidence reuse

All six cases in the registered `source_drift` suite passed at `e8effbd`:
`runner_source_manifests_agree`, `limits_documentation`, `contract_versions`,
`architecture_documentation`, `build_documentation`, and `generator_contract`.
The exact command was:

```sh
PW_TEST_OUT_DIR=tests/out/runs/extensions-m1-mechanical-20261012 \
  tests/run.sh --suite source_drift
```

The [mechanical run](../tests/out/runs/extensions-m1-mechanical-20261012/run.json)
is gitignored and local-only. It has six completed passes, no skips or unrun
cases, and no harness errors. This verifies registry/source agreement, generated
copies and generator mutation controls; it does not establish native semantics.
No generated owner or output changed in M1. The new native fixture is test
apparatus built by its own script, not a new production Meson target. Native
production sources, worker identity, wire versions and prose baseline are
unchanged.

On resumption, all nine captured executable/input source hashes matched the
committed versions: native C/build script, suite checker/runner, catalog, and
`case.sh`, `testlib.sh`, `test_cli.py`, `suite_run.py`. The native binary hash
also matched. The only differing captured file is this plan's checkpoint prose;
the checker copies it for provenance but does not interpret it. This is a
reviewed evidence-reuse exception for that narrative delta. Tracing dispatch
through `tests/run.sh`, shared harness helpers, the suite, build script and
checker found no other modified code dependencies: the Git diff from the
baseline adds the captured fixture/suite and documentation, and modifies only
the captured catalog among pre-existing execution inputs. Hash matches establish
identity, while this dependency review is the basis for reusing the native run.
Any subsequent relevant code change requires a fresh native run.

## Rendered assessment and disposition

Reviewer: fresh read-only agent `m1_rendered_review`, model `gpt-6-astra`, on
2026-10-12. The reviewed source was immutable snapshot `m1-v1`: `e8effbd` plus
its captured `source.diff`, subsequently committed unchanged as `e423705`.
The [review directory](../tests/out/runs/extensions-m1-mechanical-20261012/reviews/m1-v1/)
and its manifests, source copies, rendered HTML, PDF and PNG files are gitignored
and local-only. The review directory's `manifest.json` pins every source/HTML
hash; `print/manifest.json` pins PDF/page-image hashes. Renderer recipes and the
native evidence-reuse audit are retained in the parent `reviews/` directory.

The renderer was Pandoc 3.12 (GFM to standalone HTML), then WeasyPrint 70.0 with
local review CSS, rasterized by Poppler 26.10.0 at 90 dpi. The reviewer actually
viewed the rendered PNGs, including the results tables and visible links, before
returning the assessment. Safari new-tab attempts were refused because the user
was interacting with Safari; existing user content was untouched. Browser-specific
layout and interactive link navigation were not inspected. The independent page
renders supplied the required visual inspection, and a separate check of 159
local HTML links/anchors found no missing target. No diagram or staged guide was
produced for M1.

Inspected surfaces and scope:

| Surface | Rendered inspection |
| --- | --- |
| Investigative record | All four original pages, including native effects, allocation limitations, negative runs and reuse account |
| Plan | Pages 1–3 and 9: checkpoint, baseline context, allocation decision and complete M1 gate |
| Native fixture and suite READMEs | Complete, one page each |
| Tests README | Suite-map page 5 and native entry |
| Outcome coverage | Page 3, native paragraph and surrounding evidence-contract context |
| Opt-in registry | Page 4, native entry and surrounding context |
| Fixture catalog | Both pages |

The reviewer also traced all 18 raw native reports, the C fixture, the independent
checker, signing read-backs and referenced WebKit declarations/implementation.
Its conclusion was no M1 correctness finding or investigation blocker: the
account accurately distinguishes native observations, selected design assumptions
and future production obligations. The results table agrees with the native
returns, query patterns, fresh accesses and descriptor counts. Independent
content/identity and cleanup checks support the effect claims; zero allocation
callbacks are appropriately bounded. No missing generator coverage was identified:
the changed prose is authored Markdown and existing generated regions are
unchanged. Mechanical agreement was not used as semantic proof.

| Finding | Route and owner | Lead disposition and recheck |
| --- | --- | --- |
| F1: narrow print table columns split checkpoint status words and suite-map identifiers | Low-priority rendering issue, high confidence; local review CSS/print recipe, not authored prose or a production generator | Accepted. Added minimum widths and ordinary word wrapping. The first correction fixed plan status and the native suite row but narrowed the Reference column; added a minimum width there too. Reviewer visually accepted plan pages 1–2 in `print-v2` and tests README page 5 in `print-v3`, with intact labels and no clipping/overflow. Resolved. |

Original renders are preserved. The corresponding `print-v2` and `print-v3`
manifests pin corrections, and `reviews/print-v2.py` and `print-v3.py` retain
recipes. No source or semantic claim changed to address F1. No finding remains
open or deferred. The final `reviews/m1-final/` snapshot adds only closure and
review metadata to this record and the plan; native findings, fixture/suite
accounts and evidence are unchanged. Lead review checks that final rendering and
bookkeeping without attributing those later metadata edits to the earlier review.

## Gate closure and next work

M1's native completion requirement is met by successful issuance under the
recorded ordinary authority, consume into a real 64-bit handle and release with
its native result, plus all required independent controls. The host-specific
findings support the initial class/flags, transient transport, issuer lifetime
and qualified worker invariant described above. They do not replace M2/M3's
production ordering, admission, transport, signing and confinement evidence.

All owned native children were reaped; the checker removed its temporary target
directory. No BYOXPC resources or cleanup obligations exist. Managed test outputs
and source snapshots remain available locally. The disposable development binary
`/private/tmp/pw-ext-dev-native` is not accepted equipment. Rendering used an
isolated temporary WeasyPrint environment and installed Homebrew Poppler; neither
is part of the native experiment or product dependency set.

The session stops at completed M1 under the user's scope. M0 and later
implementation milestones remain untouched. The next broader-plan action is M0;
then M2 can use these M1 decisions, retaining the independent native suite as a
control. Rerun native evidence if its fixture, checker or relevant execution
inputs change; preserve prior runs and state replacement credit explicitly.


## M0 vocabulary gate

The continuation is authorized through the A1 handoff. M0 was performed after
M1 because the preceding turn was expressly limited to M1. This sequencing
exception changes no implementation dependency: M0's prose edits precede M2.
The pinned-stage heading and budget/principle sentences in ARCHITECTURE, the
runner lifetime sentence, and four failure-contract passages now use “stage”.
Descriptions of unchanged wire keys retain “phase” until the M2 response bump.
Generator-owned copies were regenerated and remained unchanged.

`PW_TEST_OUT_DIR=tests/out/runs/extensions-m0-20261012 tests/run.sh --suite source_drift`
passed all six registered cases outside the automation sandbox, run ID
`20261012T214610Z_55b7a6b3`. The source was `d3fc32d` plus the M0 prose/checkpoint
diff preserved in the review snapshot. Direct drift, worker-identity check and
`git diff --check` also passed. The worker identity remains
`64aa50556d3a6220a443c7de8667be608d5fb78c9319a586285e55d90be39c7b`.
Later changes in this increment are checkpoint and review bookkeeping only;
no generator input, product source, or executed check changed.

Fresh read-only reviewer `m0_rendered_review`, model `gpt-6-astra`, inspected the
immutable [M0 rendered snapshot](../tests/out/runs/extensions-m0-20261012/reviews/m0-review/)
on 2026-10-12. These source/diff, HTML, PDF, PNG and hash manifests are gitignored,
local-only evidence. Rendering used Pandoc 3.12, WeasyPrint 70.0 and Poppler
26.10.0. Actual image inspection covered architecture pages 5–7 and 10–11;
runner reference 1–2; failure contract 3, 5–6, 10–11, 14–15 and 18; guide 15–17,
21 and 25. The reviewer found no documentation, implementation or investigation
issue: stages and retained wire fields are accurately distinguished and the
changed passages and table remain legible. These changes belong to handwritten
source regions; no generator correction or coverage extension was indicated.

Lead disposition: accepted after checking the changed passages and their source
ownership. No correction or recheck is required. This bounded vocabulary review
does not establish runtime behavior or constitute A1; unrelated diagrams/pages
were outside scope. Mechanical results and identity were supplied to the reviewer,
not rerun by it. No candidate build or external-runner resource was created by M0.
