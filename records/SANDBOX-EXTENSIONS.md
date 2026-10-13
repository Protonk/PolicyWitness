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

## M2 implementation checkpoint

The phase candidate exposes mutually exclusive `probe_plan` and `phases` forms.
The simple form normalizes to `main`. Eight phases share 256 total ordinary
query/attempt pairs, globally unique action IDs, fixed immutable phase
publications and one worker/application. Host planning is fresh at each arrived
boundary; a numbered release follows collection closure and a second ownership
check. Missing predictions do not suppress attempts. Wrong ordinals, expired
waits, invalid boundaries and lost ownership withhold progression; earlier
observations survive. Response schema 16 moves validator/ordering evidence into
phase records, associates each step with its phase and renames the three run
stage keys. Request 4 remains an additive authoring contract; envelope 7 retains
its reading rules. Bootstrap magic/identity offsets are unchanged; the compiled
C/Swift layout has a larger header and fixed phase records.

Collection uses a fresh validator per eligible phase, a cumulative 30-second
planning/collection allowance, and bounded frames, decoded strings, records and
retained bytes. The resolved filter-value bound is 1023 bytes, permitting a
resolved OS path longer than its submitted spelling. The Unicode round-trip
control distributes its original scalar corpus across admitted-size IDs.
The conservative production-encoded maximum is 52,257,718 bytes; the controller
budget is three times that value rounded upward to 152 MiB. This construction
places mutually exclusive fields together; it is not a reachable transcript
claim. The prose baseline lost its stale literal ABI-offset entry and gained
none. A stale architecture claim about an unversioned validator was corrected:
the receiver already requires its kind and schema marker.

Diagnostic runs remain under `tests/out/runs/extensions-m2-*` (gitignored,
local-only). The signed receiver run `extensions-m2-receiver-signed-20261012`
passed 395 Swift/native checks and the service-admission mutation case against
worker identity `e2dec1d651268c5d6424edff3f96b078f4cf02cb253d415a8dcacbdb561da716`.
The subsequent source adds invalid-prior-completion refusal before collection
and closes validator input immediately on byte cutoff; final acceptance requires
rerunning against that source. Earlier failed diagnostics identify old expected
shape/size/version values, test inputs exceeding newly explicit receiver bounds,
and a deliberately mismatched stale app during an intermediate unit run. They
are not acceptance evidence.

Registered live captures passed BBX-001 and BBX-002 in
`extensions-m2-live-captures-20261012`; the exact requests and envelopes populate
`tests/fixtures/blackbox_e2e/checker/response16`. The corrected deadline case and
public ordinary phase/aggregate-budget/byte-cutoff case passed in
`extensions-m2-live-captures2-20261012`; the former supplies
`tests/fixtures/disposition/response16`. Prior-version captures remain untouched.
These fixtures identify their producing build; later acceptance runs must test
the final candidate independently. The phase case was subsequently extended
with malformed-type reader controls. No fixture is rewritten to claim a newer
producer or schema.

The coordinated M2 gate is currently running as
`extensions-m2-gate-20261012`, after a signed rebuild with worker identity
`78e5ab71d82e101486f291e133e1bdb1a912577f0dabee8ebb35ac63b3a5233d`.
Selected suites are runner_unit, runner_abi_layout, runner_c_worker_harness,
failure_boundaries, runner_outcome_bad_request, runner_validator_failure, unit,
blackbox_e2e, witness_contract (including opt-in mutations and the owned BYOXPC
dossier fixture), and source_drift. Registry list/reconcile before installation
reported no runners, pending cleanup, candidates or inspection errors. The
harness owns any subsequent fixture session record and cleanup. No M2 gate or
rendered assessment is yet claimed complete. M3 has not begun.

## M2 gate closure

Implementation commit `66d41b5` and corrections commit `ac9c3b5` are accepted by
one consolidated run at the latter source, with no concurrent source edits:
`extensions-m2-accepted-20261012`, run ID `20261012T224802Z_44df7a6f`.
All 113 selected cases completed and passed, with no skips or unrun cases.
The command was `tests/run.sh --suite runner_unit --suite runner_abi_layout
--suite runner_c_worker_harness --suite failure_boundaries
--suite runner_outcome_bad_request --suite runner_validator_failure --suite unit
--suite blackbox_e2e --suite witness_contract --suite source_drift
--suite runner_ready_byte_resilience --suite runner_outcome_validator_no_reply
--suite runner_filter_sysctl_name --suite runner_exec_dac --suite blackbox_menagerie`,
with `PW_TEST_OUT_DIR=tests/out/runs/extensions-m2-accepted-20261012` and Rust's
rustup bin on PATH, outside the automation sandbox. The full command/configuration,
case IDs, source snapshots, equipment and unchanged signed app inventories are
in its [managed run](../tests/out/runs/extensions-m2-accepted-20261012/).
This is local-only, gitignored evidence, now protected in the retention index.

The app is build 547, with worker identity
`78e5ab71d82e101486f291e133e1bdb1a912577f0dabee8ebb35ac63b3a5233d`, signed with
the established development identity. Its build stamp predates the implementation
commit (`d0b692e-dirty`); product sources match `66d41b5` and are unchanged in
`ac9c3b5`. The consolidated run established valid signatures before execution
and byte-for-byte inventory equality afterward. Its Swift suite passed 396
checks; compiled C/Swift ABI agreement covered 99 values. Real maximum-input
transport, one-phase success/failure/deadline controls, multi-phase collection,
fresh eligibility, interruptions and both ordering bypass mutations passed.
The test-owned BYOXPC dossier fixture confirmed removal through its owned
cleanup session. No remaining external resource obligation was reported.

Earlier `extensions-m2-gate-20261012` (92/99) and
`extensions-m2-corrections-20261012` (26/29) retain their original failures.
They exposed a test-only Swift helper visibility error and readers/fixtures
still using the preceding response shape. The ordering controls also needed
synchronization: the worker mutant now waits for independently held collection
before bypassing the barrier; the host mutant accepts the actual query count
when its premature unlink changes fresh eligibility. The baseline still requires
both queries. Neither timeout nor connection failure counts as a detected bypass.
`extensions-m2-final-checks-20261012` passed all ten selected checks after those
repairs; the consolidated run replaces earlier results for gate credit, avoiding
dependency-reuse exceptions.

Fresh read-only Astra reviewer `/root/m2_rendered_review` inspected immutable
[M2 rendered artifacts](../tests/out/runs/extensions-m2-accepted-20261012/reviews/).
The retained snapshot, source diff, hashes, HTML, PDFs and PNGs use Pandoc 3.12,
WeasyPrint 70.0 and Poppler 26.10.0. Actual image inspection covered root README
pages 1–2; architecture 2–10; contract 1 (remaining contract via extracted text);
limits 1, 3–4 and 8; grammar 1–2; runner reference 1–2; failure contract 11 and
16–21; guide 4, 18–20 and 22–23. Unrelated guide/BYOXPC pages, full grounding
tables, document graph and a separate staged-guide rendering were outside scope.
The staged guide was mechanically byte-identical to the source guide; this is
not separate visual inspection.

The reviewer raised two documentation findings. F1: shared reading rule 6's
“any step” wording could incorrectly reject later-phase `query_first` after an
earlier unlink. The owning failure-contract text and generated guide copy now
limit that claim to its own phase, distinguish cross-phase completion/arrival,
and make no stable-object claim. A real unlink/recreate/later-query experiment
was added to the public phase case and passed. F2: “All queries are collected”
implied complete verdict acquisition; the guide now states that collection
closes, retaining unavailable predictions. An editorial correction joined two
paragraphs split by inline generated limit spans. The reviewer rechecked actual
images of failure contract 18, guide 4/19/22 and witness README 1/3 and closed all
findings. Lead disposition: accepted; no implementation or investigation finding
remains. The review does not substitute for runtime evidence or A1.

Both baselines gained no entries. M2 is complete. M3 begins from the accepted
source, retaining one applied policy/worker and the established phase protocol.

## M3 pause checkpoint

The user requested a clean pause before interrupting the network. Implementation
is committed as `0daa018101ed39ecfd92d6d528b112784ed9c30f`. This is an unfinished
milestone checkpoint, not acceptance or an A1 handoff. The subsequent interruption
occurred before evidence attachment and resume-note edits; those bookkeeping
steps were completed on resumption without further implementation changes.

The checkpoint adds the bundle-local native issuer, a separate transient shared
memory token channel, bounded extension declarations and consume/release actions,
native lifecycle publications, and a fresh-read action retaining individual
open/read/stat/close observations. The worker performs consumption and release
under its once-applied policy. The host records preparation and issuer evidence,
coordinates delivery and erases its mapping. Tokens are carried in the transient
mapping, not serialized as lifecycle results. Dedicated token-confinement and
interruption controls are still required before crediting those invariants.
Build/signing integration and BYOXPC issuer registry/provenance fields are
implemented but have not received their full acceptance controls. The response
schema is now 17; request 4 and envelope 7 remain unchanged.

The signed development build completed with
`make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`, with
`/opt/homebrew/opt/rustup/bin` on PATH and outside the automation sandbox.
Build 550 retains version 0.2.8 and stamp `b62509e-dirty`; the product source
matches the implementation checkpoint committed afterward. Worker identity is
`1b8b6623d0ecedee44f49a378226fc5b9264b61bf1438817e3534d5284073301`.
Swift core compilation, production Rust `cargo check`, and worker-identity,
contract and build generator `--check` commands passed. These are not the full
Swift/Rust test suites, ABI check, `source_drift`, preflight or M3 gate.

All three diagnostic runs selected `tests/run.sh --case witness_contract/extensions`
with a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>`, the Rust PATH above and
execution outside the automation sandbox. Each run completed its one selected
case with a failed result; no historical result has been changed:

| Run directory | Run ID | Finding |
| --- | --- | --- |
| `extensions-m3-first-cli-20261012` | `20261012T230544Z_b10608a4` | Issuer exited 92 before issuance; exact shared-memory file-size comparison was incorrect. |
| `extensions-m3-channel-cli-20261012` | `20261012T230814Z_90b3a9c6` | Issuer still exited 92 after the size correction; spawn descriptor inheritance required a distinct source descriptor. |
| `extensions-m3-pause-check-20261012` | `20261012T230934Z_648b13f3` | Native lifecycle and fresh-read assertions passed; unfinished independent readers rejected the new response fields and phase action partition. |

The channel correction follows two observations. A temporary, unlinked macOS
shared-memory experiment requested 17,472 bytes with `ftruncate`, but `fstat`
reported 32,768; the mapping now checks sufficient backing size while mapping
only the fixed logical capacity. The issuer descriptor could originally equal
its destination descriptor 3, leaving close-on-exec set through a same-descriptor
spawn duplication. A separate source descriptor allocated at or above 64 now
feeds the spawn duplication to descriptor 3. The third CLI run exercised both
corrections together. These are implementation repairs within the planned
transient-channel design, not authority or scope expansions.

The third run records a nonnull native issuance result, a reaped issuer exiting
0, token length/delivery of 328 bytes, consume handle `1` with errno 0, and release
result `0` with errno 0 for that handle reference. Both calls have their boundary
and result publications. The worker applied its policy and was reaped; all three
phases retained arrival/completion and their ordinary `query_first` observations.
Fresh open attempts before consumption and after release returned -1/EPERM. The
middle attempt opened descriptor 5, read the expected 32 bytes, and recorded
successful stat and close results. Independent observations retained matching
device/inode and unchanged contents. These are this experiment's observations,
not a general inference from release success to permission revocation.

The failing independent-reader assertions identify unrecognized `extensions`,
`extension_events`, `fresh_read` and issuer provenance fields, missing read-action
comparison mappings, and phase partition logic that still counts only ordinary
steps. Consequently the case remains failed despite its preceding native
assertions. All three runs established valid app signatures before execution and
unchanged inventories afterward. The first two pre-correction snapshots have no
credited source commit; their retention entries deliberately use `source: null`.
The third uses the exact implementation checkpoint above.

The [third managed run](../tests/out/runs/extensions-m3-pause-check-20261012/)
contains the raw specimen/envelope under
`suites/witness_contract/extensions/artifacts/lifecycle/`, the assertion failure,
and `independent-observations.json`. Its `checkpoint/` attachment contains all
three build logs, all three diagnostic console logs, the Swift/Rust compile logs,
and a SHA-256 manifest identifying source and build. All three runs are protected
in `tests/RETAINED.json`. This evidence is gitignored and local-only. Attachment
was performed under the stable checkout lock after validating ownership, run IDs
and terminal completion; original evidence was preserved.

Resume with independent reader integration in `tests/lib/consumer.py`, lifecycle
adapter/oracle checks and Rust disposition validation, including rejected
invented completion and reference/order controls. Then finish these M3 obligations:

- Compile and update Swift/Rust tests and initializer fixtures; cover admission,
  reference/limit refusals, issuer capability failures and lifecycle evidence.
- Complete issuer/worker failure and interruption controls, token confinement,
  target preparation and identity observations, fresh descriptor controls, and
  lifecycle placement/omission cases on standard and BYOXPC runners. Check
  BYOXPC signing/read-back and older-registry recovery.
- Update C/Swift ABI printers and reviewed golden values for the new fields,
  check the separate channel layout agreement, and reassess maximum-reply bounds.
- Finish the limits, failure contract, scenario matrix, coverage/catalog,
  architecture, public grammar/guide, FAQ and build/signing inventories through
  their owning inputs and generators. Preserve earlier response captures while
  adding genuine response-17 captures and updating current fixture references.
- Inspect degraded/minimal reply fallback handling for the new evidence fields,
  unpublished native outcomes, uncertain cleanup and token erasure claims.
- Run the coordinated signed M3 checks and required ordering mutations, then
  obtain and close the fresh rendered assessment. Prepare A1 only after M3 closes.

No M3 BYOXPC installation was made. M2's owned fixture cleanup remains verified.
The final process inspection found no matching build, issuer, worker, validator
or runner task; the evidence lock was released normally. There is no active test
or new cleanup obligation at this pause. No release was published.

## M3 reader integration increment

Execution resumed on user instruction. Independent Python readers now join the
ordinary steps and native events using the phase action sequence and check
extension publication, reference/order, delivery/issuance and fresh-read evidence.
The lifecycle oracle checks native events against their disposition slots and
claims. Rust disposition validation withholds projections on inconsistent native
accounts. Swift controls cover full-width handles, unresolved call boundaries,
unavailable dependent actions and rejected fabricated publication/references.

The response and envelope shape candidates were generated by the field-complete
Swift and Rust fixtures, reviewed (no removed or retyped existing keys), and
installed. The C printer added 24 lifecycle/read values; its reviewed golden
keeps all existing values unchanged. The current contract path-state fixture is
constructed data and now carries response 17. Historical live captures remain
unchanged; new response-17 directories contain exact requests and raw envelopes.

The following managed runs are gitignored, local-only and retained. Original
failures remain failures. Commands used `tests/run.sh`, fresh output directories,
the established Rust PATH and escalation for signed/live equipment:

| Run directory | Run ID | Result and selected controls |
| --- | --- | --- |
| `extensions-m3-readers-build-20261012` | `20261013T003405Z_d8585112` | 1/3 passed; initial `--suite runner_unit --case unit/rust.unit` exposed stale shape/path fixtures, a missing issuer in the signing fixture and omitted optional fields in the populated-round-trip test. |
| `extensions-m3-reader-live-20261012` | `20261013T003604Z_59543cf5` | 3/3 passed: `witness_contract/extensions`, `blackbox_e2e/BBX-001`, `blackbox_e2e/BBX-002`. Supplies the response-17 blackbox/extension captures. |
| `extensions-m3-disposition-capture-20261012` | `20261013T003743Z_0d4448ea` | `witness_contract/worker_attempt_in_flight_at_deadline` passed; supplies the response-17 a1 capture. |
| `extensions-m3-reader-controls-20261012` | `20261013T003940Z_a3f6cd10` | 4/4 passed: `unit/rust.unit`, `unit/rust.fmt`, `runner_unit/pwrunner_core_unit_executable` (400/400 checks plus real driver reply replay), `blackbox_e2e/checker_controls`. |
| `extensions-m3-layout-20261012` | `20261013T004044Z_cb6ae7fe` | Layout check failed on the deliberately stale golden and wrote its candidate. |
| `extensions-m3-layout-accepted-20261012` | `20261013T004128Z_95d547b6` | `runner_abi_layout/c_swift_layout_agreement` passed with 123 values, capture controls and native query boundary checks. |

The live and Swift-driver runs used unchanged signed app build 550 with the
native source identity recorded above. App inspection was valid before and
unchanged afterward. Rust unit tests exercised the new controller source;
the signed app's controller predates these reader changes. Test/reader edits
were incremental in the working tree, so retention entries use unknown full-run
source provenance rather than assigning a later commit to an earlier execution.
Each run retains its configuration, outcomes, app inventory where applicable and
attached console log. The final reader checks preceded only the independent ABI
printer/golden and documentation/bookkeeping changes; full M3 acceptance still
requires a rebuilt final candidate and coordinated rerun.

The current extension capture supplies successful native issuance, consumption,
release and fresh-read evidence; its independent reader now accepts the complete
account. Constructed mutations reject unsupported integer types/ranges, native
completion without publication, bad references, missing disposition/phase
association, delivery without bounded issuance/reap and inconsistent read bytes.
A positive constructed consume failure retains access observations and an
unavailable release, preserving the distinction between native results and
effective access. These controls establish interpretation, not live native
failure reachability. M3's native interruption, confinement and BYOXPC obligations,
remaining manifest/documentation work, integrated gate and rendered assessment
are still outstanding. No audit handoff is claimed.

## M3 native boundary increment

The signed app is now build 553, source stamp `d4f512a-dirty`, worker identity
`5e8afcb85a49a54cb9df6b24cf594befd5b74712618161ebadd92679fc28c8a0`. It includes
the prior independent Rust reader changes and current native publication guards.
Malformed issuer magic, PID, state or call-marker association cannot promote
native values or delivery. Swift rejects unsupported fresh-read observations,
missing lifecycle publication and inconsistent retained-evidence claims. The
separate transient channel has a compiled C/Swift layout check. The API constants
remain in the standalone client compilation closure; an initial signed-build
attempt exposed and corrected a reference to host-only constants.

Registered `witness_contract/extension_boundaries` now uses production native
sources with compile-time substitutions, entirely outside the inspected app.
Its 25 controls include genuine native success; issuance refusal, oversize/empty
tokens, issuer death/deadline and unavailable API; malformed channel headers and
token framing; native consume/release failure and worker API absence; and three
interruption positions for each lifecycle call. Independent receipts distinguish
pre-call publication, execution inside a controlled replacement before return,
and real native return before result publication. The middle position is not a
claim about execution inside the kernel API. In every interrupted case PW keeps
native results unresolved and retains earlier completed observations.

Real token bytes remain in test-owned transient shared memory. The parent scans
captured output in memory before saving it and tests detector sensitivity with
an in-memory contaminated string. Receipts observe clean argv/environment,
disabled core dumps, closed production channel descriptors and erased issuer and
worker buffers. Host erasure is reported separately; a direct host-buffer control
is still pending. Deliberately malformed or refused calls do not establish native
permission effects. The app's signatures were valid before and its inventory
unchanged after each live run.

All rows below are local-only managed evidence, protected by `tests/RETAINED.json`.
Commands used the established Rust PATH, fresh `PW_TEST_OUT_DIR` and `tests/run.sh`
outside the automation sandbox. `native-boundaries*` selected the new boundary
case; the first also selected `runner_abi_layout` and the ordinary extension case.
`boundary-shape*` selected the Swift unit executable. `boundary-accepted` selected
both `runner_unit` cases, `runner_abi_layout` and blackbox checker controls.

| Run suffix after `extensions-m3-` and before `-20261012` | Run ID | Original result |
| --- | --- | --- |
| `native-boundaries` | `20261013T005443Z_6f4769fb` | 2/3 passed; test observer open failed and issuer override was absent from the shape fixture. |
| `boundary-shape` | `20261013T005655Z_5070748b` | Swift test initializer argument order failed compilation. |
| `boundary-shape2` | `20261013T005711Z_0b11e43e` | 400/401 Swift checks; generated shape candidate added only the issuer override path and was reviewed before installation. |
| `native-boundaries2` | `20261013T005825Z_9297dc20` | Failed; diagnostic exit identified EACCES opening the test observer. |
| `native-boundaries3` | `20261013T005937Z_5456c6b2` | Failed before native execution: `fchmod` on POSIX shared memory returned EINVAL. |
| `native-boundaries4` | `20261013T010344Z_50fecfb7` | All 25 native controls passed after fixture setup corrections. |
| `boundary-accepted` | `20261013T010431Z_8ce6e4fb` | 4/4 registered cases passed: 401 Swift checks and driver replay, service admission mutations, 123 worker-layout values plus 18 transient-layout values, independent-reader controls. |
| `native-boundaries5` | `20261013T010558Z_be27d671` | All 25 controls passed with durable observer recovery receipts; all channel cleanup and recovery-record removal verified. |

The observer failure was a fixture ABI error: macOS declares `shm_open` variadic,
so ctypes must declare only its two fixed arguments on arm64. The failed
`fchmod` retry then exposed an ownership bug in the fixture: it created 25 empty
objects before recording their random names. No mapping, target, token or child
was created in that run, but those object names cannot now be recovered from its
artifacts and absence is unverified. No cleanup by name prefix was attempted.
Subsequent setup records ownership before metadata checks, unlinks on setup
failure, and retains a duplicate recovery record outside prunable output if
native child cleanup is unconfirmed. All recorded channels in the first, second,
fourth and fifth runs have verified unlink receipts. This is a test-fixture
cleanup limitation, not evidence of token retention or production cleanup.

Each run has an attached console transcript. The fifth native run's `checkpoint/`
contains both signed-build logs, the tracked diff, source copies and SHA-256
manifest against base `d4f512a`. Full-run source provenance remains null in the
index because these were incremental working-tree runs. Attachments and retention
updates used the checkout lock after checking run ownership and completion.
This increment does not close M3 or prepare A1; the checkpoint lists remaining
obligations. No release or external-runner installation occurred.

## M3 placement, host cleanup and BYOXPC increment

After native checkpoint `250126a`, Swift controls inspected the actual shared
mapping before and after host erasure, then confirmed descriptor closure. A
second control independently reaped the real issuer but substituted failed
wait/kill observations at the host boundary. Native issuance remained published
with a nonnull result; the host's reap stayed unconfirmed and delivery was
withheld. No token bytes were printed. The passing Swift suite now contains 403
checks and its real-driver reader replay.

The shared CLI workload covers consume/release in one phase or separate phases,
intervention-only phases, delivered-but-unconsumed tokens, consumption without
release, and ordinary requests without a declaration. Failed target resolution
retains preparation errno, unavailable consume/release and unavailable query
planning. A symlink preserves submitted/resolved path distinctions. Replacement
between preparation and consumption retains the issuance identity while later
reads describe their actual opened descriptor; an independent non-inherited
handle prevents reuse of the removed inode during the control. Release results
do not dictate the asserted later access outcome.

The owned BYOXPC fixture now independently reads the issuer's signature and
entitlements and compares registry/envelope provenance. Its issuer receives the
selected Developer ID identity without the supplied worker entitlements. A fake
OS control rejects an issuer with unexpected entitlements. Setup records both
`runner list` and `runner reconcile` before installation. The new opt-in
`witness_contract/extensions_byoxpc` repeats the extension workload and the
ordinary phase controls, using the same assertions as the standard runner.

The first BYOXPC run reached the issuer's pre-call marker but timed out without
native result publication. Its target was inside this Desktop checkout. The
user then reported and approved a macOS TCC prompt naming `PWRunner.xpc` and
requesting Desktop access, and asked to avoid such prompts where possible. A
separate run with targets in the owned `/private/tmp` staging directory passed.
This supports a target-location/TCC explanation, but the timeout itself does
not establish a cause and user approval is a confounding environmental change.
No issuer authority was expanded. New standard and BYOXPC extension/phase
controls now use owned `/private/tmp` targets; raw output and sanitized evidence
remain in managed test output. No private-data access is part of the workload.

| Run suffix after `extensions-m3-` and before `-20261012` | Run ID | Original result |
| --- | --- | --- |
| `issuer-owner` | `20261013T010817Z_d6ec36c3` | Failed Swift compilation: extra optional chaining in the new test. |
| `issuer-owner2` | `20261013T010854Z_6424bf8c` | Swift executable passed 403 checks and driver-reader replay. |
| `placement` | `20261013T011019Z_5e0e9521` | Expanded standard `witness_contract/extensions` passed. |
| `byoxpc-fixture` | `20261013T011136Z_0d583d90` | `shell_helpers/byoxpc_setup` and `witness_contract/phases` passed. |
| `byoxpc` | `20261013T011236Z_c1108960` | First `extensions_byoxpc` failed on issuer timeout with a Desktop target; owned cleanup verified. |
| `byoxpc2` | `20261013T011327Z_84e3293f` | `extensions_byoxpc` passed with temporary staging targets; native and ordinary workloads, read-back/provenance and removal verified. |
| `targets` | `20261013T011541Z_4ca69577` | Four registered cases passed with temporary targets: standard extensions/phases, all native boundaries and BYOXPC extensions/phases. |

Commands used `tests/run.sh` with the case IDs above, a fresh managed output
path, established Rust PATH and escalation for required equipment. The signed
app remains build 553 with the native identity recorded in the preceding
increment; it was valid before and unchanged after the live runs. The source
changes in this increment are test and account changes. Original failed results
remain failed. All listed runs are retained with console logs; `targets/checkpoint/`
contains a tracked diff and source/hash snapshot against `250126a`. Evidence is
gitignored and local-only. Retention entries keep source null for incremental
working-tree runs, and attachment used the checkout lock after run-ID/ownership
and completion checks. Every actual BYOXPC staging directory is absent after
verified removal; every final native observer receipt confirms unlink and
removal of its durable duplicate. The earlier unrecorded empty-object limitation
remains unchanged. No active process or newly owned resource remains.

M3 remains open. Next are the issuer's per-binary dossier observations (currently
only issuer registry provenance is represented), older-registry and capability
controls, limits/maximum reply, admission corpus and permanent generated accounts,
followed by consolidated acceptance and the fresh rendered assessment. No A1
handoff or gate completion is claimed.

## M3 issuer dossier and validation increment

The issuer now participates in `data.specimen.binaries` under the same rules as
the worker and validator: the uniquely selected shipped path needs no duplicate
record; an override or BYOXPC copy records its selected path, actual hash, shipped
baseline hash and comparison. Missing bytes remain unavailable observations and
do not create a product verdict. The generated envelope candidate added only the
issuer object and its existing binary-record fields; it was reviewed and installed
without changing the additive envelope version. Independent native controls check
the instrumented issuer's exact hash; BYOXPC captures compare the installed issuer
bytes and baseline independently. Historical captures remain unchanged.

Registry controls now distinguish an older record with no issuer observations
from a recorded issuer that later disappears or cannot be read. The former
remains manageable with unknown issuer evidence; the latter records a validation
failure without fabricating a signature. Never-launched signed-copy controls
corrupt the worker and issuer separately: installation rejects each copy before
registration, validation names the bundle and affected helper, unaffected helper
signatures remain valid, and registry/plist removal is verified. Both standard
and BYOXPC CLI workloads exercise `extension_issuer_unavailable` at the helper
resolution boundary and require no worker or lifecycle execution. The native
API-absence control remains in the boundary workload.

| Run suffix after `extensions-m3-` and before `-20261012` | Run ID | Original result |
| --- | --- | --- |
| `issuer-dossier` | `20261013T011855Z_c39d93d9` | Rust formatting passed; unit batch failed on stale field/manifest fixtures and the deliberate envelope-golden difference. |
| `issuer-dossier2` | `20261013T012002Z_f87e4d78` | Rust unit and formatting cases plus independent blackbox checker controls passed. |
| `dossier-live` | `20261013T012157Z_3f705769` | Five cases passed: preflight BYOXPC signed-copy verification, dossier witness, extension placement/capability, native boundaries and owned BYOXPC extension/phase/provenance controls. |

The development app is build 555, stamp `21b01d6-dirty`, built with the established
Developer ID identity and unchanged native worker identity
`5e8afcb85a49a54cb9df6b24cf594befd5b74712618161ebadd92679fc28c8a0`. Live
inspection found valid signatures before and unchanged bytes afterward. All
new test targets remain in owned temporary directories. The actual BYOXPC
fixture was removed with absence verified; all native observer channels were
unlinked and their recovery copies retired. No live build or test remains.

These managed runs and console logs are retained, with incremental source
provenance null. The final run's `checkpoint/` contains the signed-build log and
source/diff/hash snapshot against `21b01d6`. Attachments were added under the
checkout lock after verifying completed ownership. Evidence is gitignored and
local-only. M3 still requires its limits/maximum-reply and admission corpus,
permanent contract/architecture/build/user accounts, consolidated acceptance and
rendered assessment before A1. The earlier empty shared-memory object cleanup
limitation remains recorded and is not revised by these passing controls.

## M3 limits/admission pause checkpoint

The user requested a clean pause during this increment. The active selection
finished, its single checker defect was corrected and rerun, and no further
implementation work was started. M3 and A1 remain open.

The limits manifest now owns ten additional extension/fresh-read bounds:
declarations, consume/release counts, reference and target bytes, token storage
and payload bytes, transient-channel size, issuer wait and fresh-read prefix.
Swift and C/layout checks establish the applicable values. Admission and reply
guards use the shared Swift constants. The owning generator regenerated the
limits account and guide; worker-identity copies were regenerated too.

The shared request corpus adds 35 examples (81 total), covering native-action
grammar, ordering/references, unsupported combinations, capacity boundaries in
ASCII and multibyte UTF-8, and missing issuer capability. The Swift corpus can
distinguish successful admission from a later helper-capability refusal. Signed
CLI admission controls now include the issuer override path. A 16,383-byte
synthetic token reaches delivery at the exact payload bound and is rejected by
the real consume API; it is not an authority token. The separate real-token
confinement controls remain intact. Fresh reads of independently known 63-, 64-
and 65-byte files verify the 64-byte prefix bound and unchanged file contents.

| Run suffix after `extensions-m3-` and before `-20261012` | Run ID | Original result |
| --- | --- | --- |
| `admission-unit` | `20261013T012656Z_0d5a7df7` | 380/403 Swift checks: real-driver cases refused the stale signed worker identity after source regeneration. Original diagnostics explicitly name the identity mismatch. |
| `limits-admission` | `20261013T012952Z_f559434e` | Five of six cases passed; the admission checker raised KeyError because its expected-error map lacked the issuer override field. |
| `admission-correction` | `20261013T013418Z_971c42bb` | `failure_boundaries/admission` passed after adding the expected `extension_issuer_unavailable` code, against the unchanged app. |

The six-case selection used `tests/run.sh` with
`--case runner_unit/pwrunner_core_unit_executable --suite runner_abi_layout
--case runner_outcome_bad_request/accepted_input_contract
--case failure_boundaries/admission --case witness_contract/extensions
--case witness_contract/extension_boundaries`. Passing cases include all 403
Swift checks and real-driver reader replay, the 81-example request corpus,
both native layouts and manifest limits, extension placement/fresh reads, and
all 26 native boundary controls. The correction selected only
`failure_boundaries/admission`; it changed one test expectation map, so the other
five results remain applicable. This is a reviewed reuse judgment, not a claim
that an entire consolidated run passed. No product source changed after building.

Build 556 reports `v0.2.8-36-g0a41ed1-dirty`, source
`0a41ed11df580adcebab3431c653c96a5590d2d9`, and native identity
`12a5db4345b0801bd519224e65955eeb623f06664ed058c9a5c34ba7acbfc91d`.
Signing used the established Developer ID identity. The two post-build runs
verified valid app signatures before execution and unchanged app bytes afterward.
Protocol versions remain request 4, response 17 and envelope 7. Generator checks
and `git diff --check` pass. No broad acceptance credit is taken from this
selection; the required coordinated admission and full M3 checks remain pending.

All three runs are retained in `tests/RETAINED.json` with their original failed
or passing status and attached console logs. The correction run's `checkpoint/`
contains the signed-build log, build manifest, tracked diff, changed source copies
and SHA-256 manifest based on `0a41ed1`. Snapshot collection preceded pause-note
and retention-index edits. It records final source after the checker correction,
not an exact source snapshot for either failed original run. Full-run source
provenance stays null. Evidence is gitignored and local-only; attachment used
the stable checkout lock after verifying run ID, completed state and ownership.

All 26 observer receipts report completed cleanup; their target and recovery
paths are absent. This selection installed no BYOXPC runner. Earlier verified
BYOXPC removal and the earlier unrecorded empty shared-memory object limitation
remain as recorded above. Build and test sessions have exited, and the process
check found no runner/native test children. The checkout lock was acquired and
released for evidence attachment without replacing its inode. The TCC preference
remains in effect: extension/phase targets use owned temporary locations.

Resume at the maximum-reply work in `ReplyMaximumTests.swift` and
`docs/limits.json`: the old 52,257,718-byte reply bound and 152 MiB controller
output cap have not yet been reassessed for extension and fresh-read fields.
Cover the new string/numeric fields through the production encoder, and add
mixed ordinary/native 256-action aggregate admission boundaries. Remaining work
also includes the public grammar/examples, permanent guide/FAQ/build/signing
and runner/controller accounts, architecture manifest and generated views,
comparison matrix response-version update, consolidated signed M3 checks and a
fresh rendered assessment. Preserve generator ownership and the distinction
between independent native observations and constructed interpretation tests.
Only after M3 closes should the A1 handoff be prepared; H1 and M4 are not started.


## M3 maximum reply and aggregate admission increment

Resumed from `7f0dbd9` at the user's instruction. The conservative reply bound is
now 52,414,779 bytes. The production encoder sizes the ordinary full reply plus
separate maximal declaration/issuer, lifecycle-event, issuer-override and fresh-read
components. The added components include incompatible optional fields and are
counted without subtracting the ordinary records they would replace. This is a
conservative union, not a reachable response. Four issuer wait-error records
cover two lifetime EINTR retries and the final wait at each host boundary.
Native-width values, escaped references/paths, event lifecycle claims and a full
fresh-read prefix are included. Every string key in all shape documents is
classified; the expanded check exposed previously unclassified failure keys.
The existing 152 MiB receiver budget still equals three times the bound rounded
up to 4 MiB; no runtime budget or signed artifact changed.

The shared corpus now has 83 examples. Its compact repeat recipe preserves
trailing lifecycle actions in both Swift and Python. New exact/over cases admit
254 ordinary actions plus consume/release and refuse 255 ordinary actions plus
those two actions, through both CLI and direct XPC. The live maximum-reply case
adds 256 fresh reads and 254 fresh reads plus native consume/release in eight
phases. It checks actual returned prefixes, descriptor identities, native handle
and release results against independent observations; files remain unchanged.
These measurements establish transport behavior separately from the constructed
size bound. All targets are owned temporary files outside Desktop.

| Run under `tests/out/runs/` | Run ID | Original result |
| --- | --- | --- |
| `extensions-m3-reply-bound-20261013` | `20261013T134922Z_9627e810` | Swift failed the stale bound and four unclassified string keys; expanded CLI/direct-XPC corpus passed. |
| `extensions-m3-reply-bound2-20261013` | `20261013T135147Z_6f841544` | String classification passed; two Swift checks still rejected the old manifest value, providing the final measured bound. |
| `extensions-m3-reply-accepted-20261013` | `20261013T135316Z_076616a9` | All three registered cases passed: 403 Swift checks and driver replay, shared request corpus, maximum-target/native/fresh-read transport. |

Commands used `tests/run.sh` with fresh managed output and the established Rust
PATH, outside the automation sandbox. The final selection was
`--case runner_unit/pwrunner_core_unit_executable
--case runner_outcome_bad_request/accepted_input_contract
--case witness_contract/max_targets_reply_survives`. A preceding misspelled case
selector was refused before creating output; its console is retained with the
accepted run. Live fresh-read and mixed-native replies measured 1,771,243 and
1,760,931 bytes; the escaped exec workload measured 9,473,544 bytes. Build 556
remained valid before and unchanged after each run, with the identity recorded
above. This increment did not require rebuilding production code.

Original results and console logs are retained. The accepted run's `checkpoint/`
contains the source/diff/hash snapshot against `7f0dbd9`; it also captures
independent documentation work in progress. Attachment and indexing used the
checkout lock after run ownership/completion checks. Source provenance remains
null for these incremental working-tree runs. Evidence is gitignored and local-only.
After execution, only the shell case's report text changed to stop saying there
were five workloads; invocation and assertions are identical, a reviewed evidence
reuse exception. No active run or new external-runner installation remains.
M3 still requires its permanent account, consolidated checks and rendered
assessment before the A1 handoff. The earlier empty-object limitation remains.


## M3 public and generated account increment

The guide now defines extension declarations/actions, placement and omission,
target preparation, fresh reads, native event validity and unavailable capability.
Its complete temporary-file lifecycle example is executed directly from the
Markdown JSON by the shared standard/BYOXPC case. The FAQ and shared reading
rules are updated at their owning sources and regenerated into the guide.
The request lesson connects named corpus examples to admission versus later
capability refusal. README Flow, runner/controller references, signing and
distribution/preflight accounts now include the ordinary-authority issuer.
The build manifest already owns its signing call, inventory and native target;
regeneration confirms those accounts without adding any build refusal or baseline.

Architecture input now owns issuer topology, transient transport, preparation
and publication guards, plus separate BYOXPC signing/read-back/provenance.
Regenerated SVGs/tables have source and control citations; those checks establish
mechanical grounding, not semantic truth. Handwritten rationale/timeline/evidence
paths describe native actions and distinguish operational progress from sandbox
state. The allocation invariant is limited to PW-owned preallocated storage;
private-library allocation and state are an explicit indexed gap. Neither docs
baseline gained an entry. The matrix now follows response 17 and adds S26/S27
for successful and denied fresh reads, with independently prepared content and
separate syscall observations. Native lifecycle events have no comparison rows.

| Run under `tests/out/runs/` | Run ID | Original result |
| --- | --- | --- |
| `extensions-m3-doc-contract-20261013` | `20261013T140803Z_3f47daad` | 8/11 passed. Source mutation's disposable checkout omitted the new channel header; shared-rule and Swift matrix cardinality checks expected their old counts. Signature inspection, contract/architecture/build/generator checks, live matrix and actual public example on both runner kinds passed. |
| `extensions-m3-doc-corrections-20261013` | `20261013T141149Z_778afdcd` | 4/4 passed: corrected source/header fixture, shared-rule count, all 405 Swift checks and driver replay, and standard public example/extension workload. |

The first command selected `--suite source_drift --case preflight/codesign.preflight
--case runner_unit/pwrunner_core_unit_executable --case witness_contract/comparison_matrix
--case witness_contract/extensions --case witness_contract/extensions_byoxpc`.
The correction selected the two failed source-drift cases, Swift unit executable
and standard extensions. Commands used the established PATH, fresh managed output
and escalation. Original failed evidence remains unchanged. Build 558 is signed
with the established identity, stamped `4158716-dirty`, and retains native identity
`12a5db4345b0801bd519224e65955eeb623f06664ed058c9a5c34ba7acbfc91d`.
Both runs verified signatures before and unchanged artifact inventories afterward.
The BYOXPC fixture's receipt marks removal and its owned staging path is absent.
No newly owned external fixture or active test remains at this increment.

The two completed runs and console logs are retained with null incremental-source
provenance. The correction checkpoint contains the signed-build log and source,
diff and hash snapshot against `4158716`; attachment used the stable checkout
lock after ownership/run-ID/completion checks. Evidence is gitignored and local-only.
A local immutable HTML/PDF/page-image snapshot is being prepared with the existing
Pandoc/WeasyPrint/Poppler toolchain for the plan's fresh rendered review. That
assessment and the consolidated M3 acceptance remain pending; no A1 handoff or
M3 completion is claimed. The earlier unrecorded empty-object limitation remains.
