# Sandbox extensions investigation

## Scope and checkpoint

Current status: M0–M5.5, A1 and H1 are complete. The user authorized continuation
through A2. M5.6 final signed acceptance is next. Signed build 582 remains from
`ea10ce3`; the accepted documentation/test-catalog candidate is `80d9daf`.
Current gate evidence and review dispositions are appended below; the associated
plan owns resume instructions.

### M1 initial checkpoint

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
claim. The later M3 maximum-reply calculation below supersedes this M2 value
with 52,414,779 bytes while retaining the 152 MiB budget.
The prose baseline lost its stale literal ABI-offset entry and gained
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


## M3 consolidated diagnostic and rendered corrections

The consolidated selection at `1f7abc0d585470df5828efc21c3da4887d8b3922`
completed all 141 cases against unchanged signed build 558: 139 passed and two
failed. Run `extensions-m3-gate-20261013`, ID `20261013T141627Z_82f7aa31`,
retains its original failures, console, tracked-source hashes and signed-build
log. Source provenance is established by the clean committed tree and the
source manifest; the build retains its separately recorded `4158716-dirty` stamp.
The release fixture's independently maintained app inventory lacked
`pw-extension-issuer`; the real artifact inspector correctly rejected the fake
valid archive for a missing executable and missing manifest entry. The fixture
inventory now includes it without importing the inspector's inventory.

The BYOXPC extension workload passed its native lifecycle and placement checks,
then the ordinary-phase byte-limit control observed no validator output before
the production deadline. Its helper path was inside this Desktop checkout. The
preceding injected timeout also observed no output; that assertion did not prove
the fixture had reached its intended operation. No evidence establishes TCC as
the cause. The helper is now compiled and executed inside the fixture's already
owned `/private/tmp` target directory, with a retained binary copy in artifacts.
The timeout control additionally requires its first published fixture record;
the byte-cutoff control keeps its original record and byte-count requirements.
This honors the user's TCC preference and prevents a blocked helper launch from
satisfying the intended timeout experiment. No production code or wait changed.
All eight recorded BYOXPC sessions from the diagnostic have removal receipts and
absent staging paths. The earlier unrecorded empty-object limitation remains.

Fresh read-only reviewer `/root/m3_rendered_review` assessed the immutable
`m3-candidate` render of `1f7abc0` (snapshot base plus diff, document hashes
verified against the commit). The retained report identifies the runtime model
as unavailable to the reviewer; the dispatch was recorded as requesting
`gpt-6-astra`. The assessment is separate from A1. Renderer: Pandoc 3.12 GFM to
HTML, WeasyPrint 70.0 to PDF, Poppler 26.10.0 to actual inspected PNG pages.
Coverage and omissions are in the full report; source and staged guide pages,
embedded topology/boundary/BYOXPC diagrams, limits/build/signing inventories and
linked accounts were inspected. Unchanged release procedures/document-graph
rows, all duplicate limit-table pages, browser compatibility and exhaustive
link navigation were outside the bounded review.

Lead dispositions, all accepted as documentation issues:

| Finding | Owner and correction |
| --- | --- |
| F1: guide says attempts have no native returns | Handwritten guide now distinguishes aggregate PW status from fresh-read syscall observations. |
| F2: validation inventory omits issuer | Guide includes present-or-recorded issuer checks, the issuer failure label, and the unknown older-record case. |
| F3: BYOXPC X4 signing and X15 hash inventory omit issuer | Corrected labels in `architecture.json`; regenerated DOT, SVG and architecture tables. |
| F4: ownership table ends at S25 despite generated S26/S27 | Handwritten ownership now refers to specimen groups in the generated matrix, retaining S09's exception and adding independent fresh-prefix evidence. No second list of numeric ranges needs generation or parsing; the reviewer accepted this route. |
| F5: inline generated cap markers split guide paragraphs | Moved the existing markers inline with preceding text; numeric ownership is unchanged. Wide preview tables remain readable; browser-specific wrapping is not attributed to the shipped guide. |

The lead also corrected the new guide's “All queries ... are collected” wording
to collection closure before actions, including failure, without promising that
every query yields a prediction. Existing phase/validator controls establish
that distinction. The generator stages the corrected guide; the distribution
copy is never patched. No generator ownership region or baseline was expanded.
Focused mechanical checks, corrected rendered recheck and final consolidated
acceptance are pending at this entry. The gate remains open.


The focused correction run `extensions-m3-review-corrections-20261013`, ID
`20261013T143009Z_f238dea2`, passed all 15 cases: all `source_drift` and
`dispatcher` members, `preflight/release_controls`, `witness_contract/phases`
and `witness_contract/extensions_byoxpc`. The relocated BYOXPC helper published
one record before the injected deadline (223 stdout bytes) and one before the
byte cutoff (24,576 received bytes). Both children were reaped. The owned
BYOXPC session reports removal and its staging directory is absent. These facts
establish the corrected fixture experiment, not the cause of the earlier stall.
The app stayed build 558 with unchanged artifact inventories.

The focused rendered recheck closed F1–F5 and the collection-closure and witness
README corrections. Actual page inspection covered both guide copies at pages
5/21/34, architecture 25/31/32 including the BYOXPC SVG, failure contract 22 and
witness README 1. Full reports, immutable original/corrected HTML, source copies,
PDFs, PNGs, renderer scripts and hash manifests are retained in
[the correction run's reviews directory](../tests/out/runs/extensions-m3-review-corrections-20261013/reviews/).
The lead independently inspected corrected guide 5 and architecture 31 and
accepted the reviewer dispositions. There is no unresolved correctness finding
from this bounded assessment; its listed coverage omissions still apply.

Both runs are indexed, with original status unchanged. The correction checkpoint
retains the working diff/source hashes against `1f7abc0` and console transcript;
its source field remains null. Evidence attachment held the stable checkout lock
after run-ID, ownership and terminal-state checks. All rendered/evidence files
are gitignored and local-only; HTML links include original local preview paths,
while PDFs/PNGs and source copies preserve the inspected content. No required
baseline gained an entry. Final consolidated acceptance will use the committed
corrections and a freshly stamped signed build before M3 closure/A1 preparation.


## M3 signed consolidation and phase-log coverage closure

Source `6744f3c0652fac983d2823dfcc9cb848efb105af` built cleanly as signed build
560 (`v0.2.8-40-g6744f3c`), with the established Developer ID and unchanged native
identity. Run `extensions-m3-accepted-20261013`, ID
`20261013T143650Z_763cbafa`, passed all 147 selected cases with no skipped or
unrun cases. It selected the earlier consolidated suites plus `dispatcher`.
The retained plan records every canonical ID and configuration. Before/after
artifact inventories are unchanged; original results, build/console logs and
clean source hashes are attached under `checkpoint/`. Eight BYOXPC session
receipts report removal with absent staging; all 26 native observer receipts
report cleanup with absent recovery records. The original empty-object
limitation is retained explicitly. Neither documentation baseline changed.

The lead's gate-to-control trace then found that optional-log controls repeated
targets within a flat plan but had no explicit cross-phase case. The plan requires
this in M3. The existing serialized-execution preservation control now also runs
against explicit phases, with the same worker PID and target across phases.
It requires ambiguous candidates for matching captures and unchanged serialized
execution under all existing populated, empty, failed and disabled capture
states. The real CLI termination/log case also repeats its disabled/enabled
failure and successful-run controls with the writes in separate phases. It
asserts phase completion, distinct query collections and phase-local ordering;
any recovered kernel-event associations must remain ambiguous. Real events stay
optional; the deterministic control establishes association when they exist.

Only test code and its documentation change: Rust edits lie inside the existing
`#[cfg(test)] mod tests`, whose preceding production bytes are identical to
`6744f3c`; the signed app is unmodified. The witness README and coverage table
name the added coverage, and architecture B8 cites its unit and live controls.
This is a required coverage repair, not an implementation behavior change or M4
expansion. The focused Rust/live/source checks and rendered recheck remain
pending at this commit; M3 and A1 preparation remain open.

The final focused run at clean source
`fdbd89b215125b50fc6030e09bdc4a66b56e48f2`,
`extensions-m3-phase-logs-20261013` (`20261013T145127Z_5507dc70`), passed
13/13 cases with no skipped or unrun cases. The command used the established
Rust PATH, escalation and fresh output, selecting `--suite unit --suite
source_drift --case preflight/codesign.preflight --case
witness_contract/worker_termination_and_log_correlation`. All five unit cases,
six source-drift cases, signature preflight and the live correlation case passed.
The deterministic phased collector test passed all capture-state variants. The
live checker passed six flat/phased variants; the phased signal-capture and
success-capture specimens each recovered two events with two ambiguous
associations. Actual OS retrieval is an observation for this run, not a required
availability guarantee. The signed app remained build 560 throughout.

[The credit manifest](../tests/out/runs/extensions-m3-phase-logs-20261013/checkpoint/acceptance-credits.json)
maps all 147 canonical cases to 13 replacement results and 134 retained results.
Both runs' inspected app inventories are byte-identical and each changes report
is empty. Both documentation baselines are byte-identical to `ac9c3b5`. These
are mechanical facts. The applicability judgment is separate: the full unit
rerun covers the changed test helper; the changed live checker and all source
checks were rerun. The driver replay filters the unchanged
`policy_transfer_driver_replies_cross_assembly_and_consumer` test and unchanged
production dependencies. Build guards copy the changed docs and Rust test
module, but their Cargo build excludes `cfg(test)`; minimum-version/signing
refusal logic and tool substitutions are unchanged. Current source-drift checks
accept the new documentation and citations. Reuse for these changed-file paths
is a reviewed exception, not a claim that all their inputs are byte-identical.
Other credited cases retain unchanged scripts, fixtures, production inputs and
app. The focused checkpoint contains clean tracked-source hashes, the exact
test-only delta from the signed source, console transcript and credit manifest.

The same fresh read-only reviewer completed the focused rendered recheck at
`fdbd89b`. Actual PNG inspection covered architecture page 11 (B8), witness
README page 6 (termination/log controls), and coverage page 3 (record
preservation). No documentation issue, implementation problem or investigation
blocker was found. The lead accepts the report: its assertions agree with the
deterministic and live controls, and their separate runtime results above now
establish execution. This closes the remaining M3 rendered-review obligation;
it does not constitute A1. Unchanged surfaces were not re-inspected, and the
earlier bounded-review omissions remain applicable.

[The final review directory](../tests/out/runs/extensions-m3-phase-logs-20261013/reviews/)
retains the report, immutable source/HTML/PDF/PNG views and renderer scripts.
Its `applicability.json` verifies current source hashes for 14 unchanged earlier
reviewed documents and all three documents in the final recheck. The final
report and applicability attachment held the checkout lock after confirming
managed ownership, run ID and completed state. All detailed test/rendered
evidence is gitignored and available only in this checkout; it has not been
published or packaged for another checkout. No original result was overwritten.

M3 is complete at this handoff. The A1 exchange has been prepared from the
implemented candidate and evidence; auditor answers and execution dispositions
remain pending. No build, test or render process remains active. No additional
BYOXPC fixture was installed by the final run; the consolidated cleanup receipts
remain applicable. The earlier 25 unrecorded empty shared-memory objects remain
unverified and are not silently discharged by later cleanup. The allocation
invariant remains limited to PW-owned preallocated reporting/coordination with
no explicit PW allocator use after application; private API internal resource
behavior is not guaranteed. Issuer authority has not been expanded. Execution
stands by at A1; H1 and M4 have not started.


## A1 returned audit and executing-agent review

The out-of-band auditor returned attributed answers and nine numbered findings
on 2026-10-13. Commit `221f5ec` preserves those answers and the auditor's
retention entry before lead dispositions. The shared audit exchange contains
the detailed review and correction owners; its answers are not rewritten by the
executing agent. The auditor found no issue invalidating the demonstrated M3
gate and performed an additional full-default run on unchanged build 560.

`a1-audit-default-20261013` (`20261013T162635Z_9a7839fb`) passed 172/174,
with no skips or unrun cases. The lead verified ownership, results and all 21
current hashed app entries against the retained inventory. Forty-nine default
cases were absent from the 147 final M3 credits; the new run passed 47 and found
two stale controls. The wrapper fixture assumes every sibling script runs via
the wrapper, but the extension boundary case is separately cataloged. The
isolation checker reverses steps without updating phase action order, provoking
a legitimate additional partition diagnostic. Their original failures remain.
This confirms a test-selection gap in the implementation work, despite coverage
of the plan's named gate controls. Subsequent milestone acceptance must include
the default battery alongside required opt-in controls, applying the existing
case-level evidence-reuse rules.

The lead reproduced the accepted contradictory `collected`/`not_needed` phase
record using both Python validation entry points. It cannot establish
`query_first`, but `collected` itself claims driver execution; its repair is
moved from M5.1 to A1 follow-up. Current guide corrections likewise belong in
A1 rather than waiting for M5.5. An additional lead finding confirms the guide
confuses missing-helper and missing-native-API refusal codes; retained issuer-6
evidence and the orchestrator distinguish them. The test-build limitation is
already explained in fixture documentation and should be explicit beside the
suite description. The older M2 reply figure now points to its M3 successor.

The review recommends retaining the bounded existing machinery for H1. The
plan's validator-cost measurement is conditional on considering a persistent
protocol, which is not proposed; collection duration must not be presented as
isolated launch overhead. M4 owns the named post-publication issuer-exit,
missing-helper-file, issuer-entitlement and BYOXPC maximum-reply controls.
This turn records review and dispositions, with no product or test-control
changes and no new live/TCC-sensitive execution. A1 remains open for corrections,
verification and applicable rechecks; formal H1 preparation and M4 remain pending.

## A1 correction candidate

The correction pass repairs the wrapper inventory from independent catalog
commands and separates a pure request-order mutation (steps and phase action IDs
both reversed) from a broken-partition mutation. Neither fix weakens the
consumer's phase partition rule. The Swift encoder, Rust disposition reader and
shared Python consumer/oracle collection check now reject contradictory
collection status and validator observations. Hand-reviewed
`tests/fixtures/contract/phase_collection.json` supplies 21 full-reply controls:
nine compatible states, including driver setup/spawn failure and unconfirmed
cleanup, and twelve contradictory states. The existing public phase control
also mutates the actual no-query phase to claim collection and a collected phase
to claim it was unnecessary. Degraded reporting-failure replies can retain raw
conflicts without recovering claims.

This enforces the existing meanings of `collected` (driver ran and returned)
and validator disposition; no valid record gains a different interpretation,
field shape or vocabulary. Under the wire contract, the correction therefore
retains request/response/envelope versions 4/17/7. The conservative generated
worker identity changes because its inputs include the Swift encoder, although
the native wait/release code and ABI layout are unchanged. Its value is
`d728670539b289721b4cfbc567df5c14ec76917c09311bba283e64a39ba36957`.

Current accounts distinguish missing-helper and missing-native-API codes,
scope missing-helper behavior to a current runner copy, state the broader local
setup meaning of `malformed_transport`, and explicitly identify the alternate
instrumented clang build. The failure contract states compatible collection
observations, architecture B4 cites their controls, and owning generators
regenerate the identity, architecture views and staged guide. No baseline is
expanded and no worker scheduling, issuer authority or lifecycle cap changes.

Focused offline run `a1-repair-offline-20261013`, ID
`20261013T170001Z_26490059`, passed six cases and left the blackbox checker
unrun after sandboxed app signature inspection failed. The same selection
outside the automation sandbox, `a1-repair-offline-retry-20261013`, ID
`20261013T170037Z_0b6cd9f8`, passed all seven on the unchanged build 560. That
retry establishes the signature failure as environmental. The selection was
`--case shell_helpers/script_groups --case blackbox_e2e/checker_controls
--suite unit`, using the established Rust PATH and distinct managed outputs.
Both original runs, console logs, working source hashes/diff and new source
copies are retained locally with null source provenance in the index; the base
is `cbb0ccf`. Attachment verified run IDs, ownership and terminal state under
the stable checkout lock. Signed candidate build, Swift/live acceptance,
rendered recheck and handoff back to the original auditor remain pending.

The clean candidate `8707abc` built as signed build 565. Focused run
`a1-repair-focused-20261013` (`20261013T170412Z_f0335f92`) passed eight of
nine cases: all source-drift checks and repaired live isolation passed, while
the new Swift test failed compilation on overlapping access to its optional
ordering value. The test reads the disposition from the row before mutation.
The next Swift run (`a1-repair-swift-20261013`,
`20261013T170648Z_eaf9ab61`) passed 385/406: its new matrix passed, but the
guard exposed an older field-complete fixture carrying both a validator and
failed spawn in one phase. Those incompatible observations now have separate
shape documents. The maximum-reply calculation encodes the spawn member
separately and counts its insertion bytes per phase, preserving the exact
52,414,779-byte conservative union and 152 MiB budget without asking the ordinary
encoder to accept that contradiction. The shape golden is unchanged.

The following run (`a1-repair-swift-fixtures-20261013`,
`20261013T170908Z_46451de6`) passed 405/406. The remaining ordering control
deliberately paired a validator with absent worker/collection evidence. It now
asserts ordinary encoding rejection and retained validator evidence in the
degraded reply, with comparisons withheld, rather than dropping the conflicting
observation. `a1-repair-swift-accepted-20261013`
(`20261013T171008Z_f1ddacae`) passes 406/406 and Rust/Python driver replay.
All runs retain original results and attached console logs under the checkout
lock. The focused run has clean `8707abc` hashes; the accepted Swift correction
has the final working diff/hashes. Full intermediate source snapshots were not
captured for the two failed Swift executions, whose index sources remain null;
they are diagnostics, not final acceptance credits.

Rendered inspection also corrected an older phase-partition sentence: action
IDs partition both ordinary and native arrays while preserving each order.
The preview's new collection table has a wider first column. Immutable initial
and corrected rendered views are prepared for the existing documentation
reviewer's bounded recheck; the external follow-up remains assigned to the
original auditor. A final clean build and full default/opt-in acceptance follow
this test-fixture correction increment.

The clean `2f380d0` build is signed development build 566,
`v0.2.8-46-g2f380d0`. Full default run `a1-repair-default-20261013`
(`20261013T171246Z_a9d472bc`) passes 174/174 with no skips/unrun and unchanged
app inventories. The final oracle review found that a malformed scalar
`phases` value could raise instead of return a diagnostic. Explicit container
and entry checks now preserve the reader's diagnostic behavior; five independent
mutations exercise both Python entry points. Focused working-source run
`a1-repair-oracle-20261013` (`20261013T173450Z_39acbafc`) passes its checker
case; exact source hashes/diff and original console are retained with null
index source. The documentation reviewer found one wording overstatement in
the ordering table: local driver setup can fail before a native spawn-failure
record exists. The corrected cell qualifies that claim and has a new immutable
render for recheck. These final changes affect test readers and prose only.
The next acceptance run consolidates all default and required opt-in cases,
so final credits need no reuse of results from the earlier oracle revision.

## A1 requested pause during final acceptance

The user requested a safe pause while the final combined default/opt-in run was
active. Correction commit `52bb1b96df168033ccd24bb0ec96dc1385d30ffc` is clean;
signed app build 566 remains from `2f380d0`. The final selection contains 196
canonical cases. Run `a1-repair-accepted-20261013`, ID
`20261013T173617Z_a52124f2`, was interrupted with one SIGINT to the verified
owned dispatcher PID 3029. Its terminal report is unsuccessful because 166
cases are unrun; 30 completed cases passed, none failed or skipped. The wrapper
exited 1, the app inventory is unchanged, and no build/test/render process
remained at the process check. The output name does not confer acceptance.

The earlier default run passed all 174 cases at `2f380d0`. All 26 of that run's
owned observer-channel receipts report completed cleanup; an independent
read-only `shm_open` check returned ENOENT for each exact recorded name, and
all recovery paths are absent. No live BYOXPC or native observer case started
in the cancelled run. Its shell-helper session records are constructed test
controls, not installed services. The older 25 unrecorded empty shared-memory
names remain an unchanged historical limitation.

The existing documentation reviewer completed its final recheck: the setup/spawn
wording finding is closed and no findings remain. The lead inspected the final
page as well. All twelve final changed document sources match the selected
immutable render snapshots. The report, all initial/superseding rendered views,
source/HTML/PDF/PNG manifests and renderer scripts were copied into the partial
run's `reviews/` under the checkout lock after owner/run-ID/terminal validation.
`reviews/current-source-applicability.json` records exact hashes and reuse scope.
No runtime acceptance is inferred from the rendered review. Both documentation
baselines remain byte-identical to M2.

The same locked attachment retained the signed-build log, console, source hashes,
full selection/command, 22 opt-in IDs, 166 remaining case IDs, cleanup observations
and an explicitly unfinished audit-handoff template in `checkpoint/`. These
artifacts are local-only and gitignored. The final handoff is not published into
the audit exchange: its acceptance/cleanup placeholders, final run references
and credit wording still need completed evidence. Resume with a fresh managed
run for the remaining cases, review source applicability for the 30 prior passes,
and produce the exact final credit manifest before returning the handoff to the
original auditor. A1 stays open; H1 and M4 have not started.

## A1 corrections verified and returned for re-audit

The user resumed work through the re-audit point. No implementation or test-code
change was needed after `52bb1b9`. Run `a1-repair-resume-20261013`, ID
`20261013T185935Z_3249b0bd`, executed the exact 166 remaining canonical cases
at clean `efb588b54fd01caf1d91683e9df6a1bff8e45bbd` against unchanged signed
build 566. All 166 passed, with no skipped/unrun cases, harness errors or app
inventory changes. All 406 Swift checks and the Rust/Python actual-reply replay
passed, as did public phases/extensions, native boundaries, ordering mutations,
BYOXPC and integrated failure controls. The combined final credit set is 196:
the 174 default cases plus 22 required opt-ins.

Thirty final credits are completed passes from the cancelled `52bb1b9` run;
none is an unrun selection. Its unsuccessful original terminal summary remains
unchanged. Exact source comparison with `efb588b` changes only the plan, two
records and one appended retention-index entry. The review traced the commands,
shared helpers and fixtures by case group; 45 source anchors and all tracked
hashes are retained. Generator targets and scanned documents exclude the changed
plan/records. Release-publish/rotation fixtures make independent empty indexes;
retention controls replace the copied index with their controlled one. Other
dispatcher fixtures copy the changed index, whose new path does not overlap their
controlled outputs. Build guards copy all tracked bytes, but unchanged build
inputs do not consume this metadata. These are explicitly reviewed applicability
exceptions for copied files, not a claim that hashes prove complete dependency
coverage or that every input is identical. No older app or pre-correction oracle
result receives final credit. `checkpoint/acceptance-credits.json` and
`source-applicability.json` contain the per-case mapping, commands/configuration,
source/app provenance, exact deltas and review judgments.

The lead independently checked absence of eight owned ordinary BYOXPC sessions,
including exact service targets, registry/pending-cleanup membership, staging and
plist paths. Registry-recovery controls independently verified cleanup; the lead
also checked their removed staging directory and all seven exact service names
recovered from owned install receipts. All 26 observer-channel receipts show
completed cleanup; read-only `shm_open` returned ENOENT for each exact name,
and every recovery path is absent. These observations are retained in
`checkpoint/cleanup-verification.json`. No build, test or render process remains
active. The historical 25 unrecorded empty shared-memory objects remain a known
limitation, not silently credited as cleaned.

All twelve final changed document sources still match the completed rendered
review, retained under the cancelled run with its report and immutable views.
The source-applicability record identifies the final contract view superseding
the earlier wording. Both documentation baselines are unchanged from M2; the
response-shape golden and ABI layout are unchanged from the audit baseline.
All 21 app-file hashes still match the accepted inventory, including embedded
manifest SHA-256 `21d83af0bfd2e63197996038cd326e4b247f449ccdaa71e6c7fb72bf27839913`.
Attachments and retention updates were made only under the checkout lock after
terminal, owner and run-ID checks. These artifacts remain gitignored/local-only.

The focused follow-up is now in the shared audit document for the original
out-of-band auditor, Claude Fable 5.1. It reports the final state without
requiring a git-history investigation, preserves all seven original answers and
additional findings, maps corrections and carried work, and asks for review of
collection consistency/version neutrality, fixture and reply-bound coverage,
acceptance applicability, current documentation and deferrals. F5 and the named
M4 controls remain deferred as previously dispositioned; F8 remains an H1 design
note. A1 is open pending the auditor's return and lead dispositions. H1/M4 have
not started. The tree is being committed at this re-audit boundary; no further
implementation is authorized before the boundary is resolved.

## A1 re-audit returned and reviewed

The original auditor's follow-up and retention entry are preserved at `682fda9`
before lead disposition. Their independent default run
`a1-recheck-default-20261013` (`20261013T193011Z_7e1b6661`) passes 174/174
at `9a1f20b` on unchanged build 566. The lead verified terminal ownership,
counts, unchanged inventories and all 21 current app-file hashes. The auditor
accepts the collection/status repair, valid failed collections, degraded raw
evidence, unchanged versions 4/17/7, Swift fixture split and conservative reply
bound, 196-case credit/provenance record, current documentation and cleanup.
They did not independently rerun opt-ins because of their keychain restriction;
that is an audit-scope limitation, not a new implementation-workflow restriction.

A1-F10 identifies an error in the lead's earlier wrapper-control repair. The
catalog exclusion removes every cataloged witness script from the expectation,
leaving the baseline and only two validator scripts. The lead independently
reproduced the auditor's observations in an offline scratch copy: the unchanged
wrapper passes all 31 controls, removing phases.sh and extensions.sh also passes
all 31, and removing the unexcluded validator script fails. The dispatcher
still executes cataloged cases independently, so this does not invalidate the
runtime acceptance or M3, but it is unfinished A1-F2 work. The lead assigns the
small repair before A1 closure: include extension_boundaries.sh in the wrapper,
restore complete sibling coverage and add omission mutations that must fail.
No implementation or test repair is made in this review turn.

A1-F11 is accepted as M5.1 hardening. Rust's as_array/as_str paths conflate
present wrong-type data with absence for the reported phase container and
validator-disposition cases. The lead inspected the retained Rust replay and
its appended-test-only diff, traced the current branch, and replayed all 33
retained inputs through both Python entry points with identical outputs; the
Rust scratch build was not independently rerun. This confirms the narrower
malformed-evidence gap without demonstrating fabricated native completion,
access or ordering. The adjacent empty spawn-failure-object probe is carried
with the review of reader validation responsibilities. The recommendation to
clarify version-neutral enforcement of existing meanings is also recorded for
M5.1; no permanent contract wording is changed here.

Independent lead reproduction scripts, exact mutated wrappers, copied-input
hashes and outputs are retained in the auditor run's `lead-review-20261013/`.
Attachments were added under the checkout lock after owner/run-ID/terminal
checks. They are local-only diagnostics, not extra registered acceptance
credits. The returned attributed text is unchanged. The lead agrees that no
finding invalidates M3; A1 remains open for F10 verification as a completion
choice, with F11 and existing M4/H1 items explicitly carried. H1 and M4 have
not started. No live, signing, XPC or TCC-sensitive execution occurred during
this review.


## A1-F10 closure

Commit `7bfbdcdcb30bbc55b74a28561eb2fd1ffeeeee89` adds the extension-boundary
script to the witness wrapper and restores the independent inventory of every
sibling. All-pass and failing-baseline cases each observe all 37 children.
Three omission controls remove one phase/extension script at a time; the same
checker rejects exactly the missing receipt, and other failures cannot satisfy
that rejection. This supersedes the broad catalog-exclusion repair described
in earlier entries; those original findings and failures remain preserved.

Run [a1-f10-20261013](../tests/out/runs/a1-f10-20261013/run.json), ID
`20261013T205716Z_b30e0bce`, passes 13/13 at clean `7bfbdcd`: the script-group
case (35 controls), all six source-drift cases and all six dispatcher cases.
There are no skips, unrun cases or harness errors. No live runner, signing or
TCC-sensitive execution was needed. The signed app is unchanged: all 21 retained
content hashes still match build 566. Both documentation baselines, worker
identity, protocol and layout remain unchanged.

The [credit manifest](../tests/out/runs/a1-f10-20261013/checkpoint/acceptance-credits.json)
keeps the 196-case acceptance set (174 defaults plus 22 required opt-ins), with
13 replacements and 183 explicitly reviewed reuses. Its sibling
`source-applicability.json` identifies exact deltas and the copied-file exceptions:
the dispatcher runs explicit witness children, while build fixtures copy but do
not execute the changed wrapper/checker. Original provenance and cancelled-run
status remain intact. This pass adds no fresh default-battery or native claim.

The existing documentation reviewer inspected actual shell-helper README page 2
at `7bfbdcd`, matched it to the complete wrapper inventory and exact omission
checks, and found no issue. The lead accepts that disposition after independent
page inspection. The [report](../tests/out/runs/a1-f10-20261013/reviews/a1-f10-rendered-recheck.txt)
records `/root/m3_rendered_review`, the historical requested `gpt-6-astra`, and
unavailable independent runtime-model identity. Its source SHA-256 is
`51dbbd412ec59d97d59a89d4e23b74115b1408585a36600c51d1b79f69f4832a`.
Immutable renders, report, renderer scripts, commands, snapshots, receipts and
rejection records are retained under that run. All twelve current document
surfaces match their applicable reviewed source bytes. These artifacts are
local-only and gitignored; coverage omissions in earlier reviews remain.

F10/F2 is closed and A1 is complete. Original attributed audit answers remain
unchanged; F11 remains M5.1 work, F5 and the named additional controls remain
M4 work, and F8 is included in the H1 briefing below. No new cleanup ownership
was introduced. The existing verified removals and unverified absence of the
25 historical unnamed empty objects remain as recorded.

## H1 prepared human review

Status: complete. The user accepted the recommendations on 2026-10-13 after
discussion of interruption hooks and diagnostic-host alternatives. The prepared
briefing is preserved below; the user disposition follows it. A1 is closed by
the F10 disposition above. M4 has not started. Neither the fresh rendered M3 assessment nor the original
auditor identified a substantial unnecessary general mechanism or competing
model. The repeated evidence rules are a real maintenance cost, demonstrated by
A1-F3 and F11; the recommendation does not imply that every reader now rejects
every malformed shape identically.

The following briefing reconciles A1 Q6/F8, the M3 rendered findings (including
resolved concerns), and the current source. The lead re-inspected actual retained
architecture pages 5–6, failure-contract pages 3–4, and witness-suite page 1.
The latest source hashes for all twelve A1 document surfaces match their retained
rendered versions after substituting the F10 shell-helper review. These views and
reports are local-only, gitignored evidence. They are useful as a human review
account, not a new runtime test or a substitute for the original auditor.

1. **Separate issuer and phase-local collection.** The rendered architecture's
   [issuer and phase timeline](../tests/out/runs/a1-repair-accepted-20261013/reviews/a1-candidate/print/docs--ARCHITECTURE-05.png)
   continues on [page 6](../tests/out/runs/a1-repair-accepted-20261013/reviews/a1-candidate/print/docs--ARCHITECTURE-06.png):
   issue before worker creation, then collect and release each phase in order.
   The auditor found this coherent and the fresh validator the simplest protocol.
   [ExtensionSession](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift) owns
   the bounded token channel and delivery after clean reap; the
   [phase callback](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
   reuses the existing bounded `runValidator` driver and cumulative budget.
   Reusing the sandboxed worker for ordinary-authority issuance cannot serve
   that responsibility; issuing in the host would move native sandbox work
   into the process whose reply path must survive. A persistent validator could
   avoid launches but would add reset, phase-association and cleanup rules.
   **Retain the separate issuer and fresh validator.** The isolated launch cost
   has not been measured. A1-F8 correctly identifies that omission; the plan
   requires measurement before considering persistence, which is not proposed.
   Aggregate collection timings cannot supply isolated launch cost. Existing
   phase controls establish distinct children and collection/cleanup behavior,
   not an optimal performance tradeoff.

2. **Independent evidence checks in Swift, Rust and Python.** The rendered
   [native-evidence account](../tests/out/runs/a1-repair-accepted-20261013/reviews/a1-contract-final/print/tests--FAILURE-PROPAGATION-CONTRACT-04.png)
   names producer encoding, controller withholding and independent controls.
   The auditor considered the repetition justified but costly. The lead agrees:
   [Swift encoding](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift),
   [Rust disposition reading](../controller/src/disposition.rs), and
   [Python collection checking](../tests/lib/phase_evidence.py) operate at
   different boundaries. The existing vocabulary/contract generators can keep
   names aligned; using the producer's decision function as the test oracle
   would lose an independent check. **Retain the boundary checks and explicit
   positive/negative controls.** A1-F3 is repaired; M5.1 must finish F11's
   wrong-type/absence distinction and state which readers promise structural
   validation versus claim validation. A shared semantic engine would reduce
   repeated code but spread a single interpretation error across those checks.

3. **One action index, separate ordinary and native records.** The rendered
   [worker-disposition passage](../tests/out/runs/a1-repair-accepted-20261013/reviews/a1-contract-final/print/tests--FAILURE-PROPAGATION-CONTRACT-03.png)
   says `phases[].action_ids` partitions `steps` and `extension_events`.
   The auditor found the reader join justified. The
   [orchestrator](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) uses
   the existing worker slot/disposition model for all actions, then emits
   ordinary query/attempt pairs separately from native interventions. A `steps`
   index alone cannot identify slots after lifecycle actions are interleaved.
   **Retain this representation.** It requires joins by action identity and
   partition controls, but avoids inventing queries/comparisons for native
   calls. Replacing it with a new unified wire union would change the public
   record and readers without removing the underlying ordering responsibility.

4. **Compile-time interruption hooks.** The
   [rendered witness account](../tests/out/runs/a1-repair-accepted-20261013/reviews/a1-candidate/print/tests--suites--witness_contract--README-1.png)
   now states the alternate-build limitation explicitly, resolving A1-F7.
   [The fixture](../tests/fixtures/extension_controls/control.c) includes the
   production C sources and supplies `PW_EXTENSION_OBSERVE`; the
   [shipped worker](../controller/tools/pw_probe_runner/pw_probe_runner.c)
   compiles that hook to a no-op. Existing executable overrides select the
   fixture, but cannot themselves observe the interval between a native return
   and its publication. **Retain the narrow test-only hooks.** They establish
   publication/interruption handling in an instrumented build. Ordinary signed
   CLI controls separately establish real native results and fresh access;
   neither source instrumentation nor those results prove private API internals.
   Removing the hooks would lose the discriminating interval controls, while a
   public runtime interruption knob would add production machinery.

5. **Defensive repeated-action refusal.** Page 4's native-event table retains
   `repeated_action`, although
   [admission](../runner/Sources/PWRunnerCore/ProbeRunner.swift) already rejects
   repeated consume/release. The auditor explicitly left keeping this duplicate
   guard to the lead. In the C worker's `attempt_extension`, two decision bits
   prevent a second native call even if an invalid internal action sequence
   reaches the worker. **Retain the small local guard and its honest vocabulary.**
   Admission remains the public rule; the guard is not an additional supported
   grammar path or a separately demonstrated public scenario. Removing it saves
   little state/code and makes the worker's at-most-once behavior depend entirely
   on upstream admission. No general reference graph or additional lifecycle
   state machine is proposed.

The allocation qualification also remains unchanged: PW's extension report and
coordination storage is fixed before application, but private native calls have
no established allocation bound. The explicit old limitation concerning 25 unnamed empty shared-memory
objects remains; no claim of their absence is added. The authorized F10 work used
no live runner, signing or TCC-sensitive test. M4 retains the combined-fault and
missing-helper-file controls; M5.1 retains F11. Neither is silently discharged
by this design recommendation.

**Decision requested when H1 was prepared:** retain these choices and permit
continuation to M4, or redirect a specific mechanism. The preparation was
committed at `772d06b` before the scheduled human review pause.


### H1 user disposition

On 2026-10-13 the user requested the interruption-hook outflow note and said
H1 could be considered complete with their agreement on the recommendations.
The executing agent accepts this as closure of the scheduled H1 boundary.
Retain the separate issuer, fresh per-phase validator, independent evidence
checks, common action index, current interruption hooks and local repeated-action
guard. No API, implementation or evidence requirement was redirected.

The discussion distinguished future diagnostic-host controls with an unchanged
worker from precise interruption of a separately debug-eligible worker. It also
identified the possible redundancy of the replacement-function interruption,
instrumentation fidelity, per-executable signing, and the current BYOXPC
installer's coupling of worker/host entitlements as matters to revisit. A
standalone outflow note preserves that investigation without an inbound plan
link, as requested. It is deferred work, not a new prerequisite or a promise to
build a debugging framework during M4.

No build, runtime test, attachment, injection or signing experiment was performed
for this documentation-only closure. The accepted implementation and its test
and rendered-documentation evidence are unchanged. A1's named M4/M5 follow-ups
remain assigned; H1 is complete and M4 is next. No active task process or new
cleanup ownership remains.

## M4 closure

M4 is complete at tested correction source `2e6a2c1ffcca48211d91dce9755a47a9a7527780`.
The signed app is build 578, source `b6410544738ecd32feef95915363f4e51af82403`,
request/response/envelope 4/18/7, worker identity
`5d5015722db1555ed399f3cac1890b11b41af7982986e717d77fbb9d96e87ff2`.
The response vocabulary now distinguishes published bounded issuer output followed
by a confirmed abnormal exit (`issuer_abnormal_exit`) from missing publication.
Delivery remains withheld; the independent native result and process observation
both survive. Actual response-18 captures and the version-only shape-golden
refresh are retained with their producer provenance. No ABI geometry, aggregate
reply bound or documentation-baseline entry changed.

The shared matrix has eight new combined-fault rows, each also read by Swift
comparison controls. M01 and M07 retain issuer publication plus exit 87, including
omitted lifecycle actions; M02 kills the worker during bounded token-framing
validation; M03 combines consume EACCES with omitted release; M04 retains earlier
consume/access when cross-phase release returns EIO; M05 and M06 interrupt
consume/release publication while preserving earlier observations. M08 combines
validator timeout, failed termination, unconfirmed host reap and late EPIPE with
a separate next-phase validator and exact phase-local record IDs. A separate
test-owned kill/wait receipt establishes final cleanup without upgrading the
host's retained unconfirmed account. Constructed validator records are not
credited as kernel predictions.

The plan's partial-token-delivery example is implemented at the actual mapped
channel's framing-validation boundary: an independently recorded valid prefix
precedes death before delivery publication. It is not a partially copied stream.
Compile-time instrumentation remains narrow; no diagnostic-host/debugger design
was added. Native fixture executables, targets and recovery ownership now live
under owned `/private/tmp` paths to avoid Desktop TCC access during direct fixture
execution. Retained executable copies are evidence, not the executed location.

BYOXPC controls independently check empty issuer grants, carry the maximum
ordinary/phased/fresh-read/lifecycle/escaped-exec workloads through the installed
service, and remove only its owned issuer file to establish the named capability
refusal. They restore exact bytes, validate that service again, and verify removal.
Registry recovery and provenance controls also passed. No issuer authority was
expanded.

### M4 execution evidence and applicability

The full [candidate run](../tests/out/runs/extensions-m4-acceptance-20261013/run.json)
(`20261013T215322Z_49c4e35f`, clean `b641054`) completed 197/197 selected cases:
196 passed, `unit/rust.unit` failed, zero skips/unrun, unchanged signed inventory.
Its `sandbox-log-observer` unit binary's
`log_capture::tests::both_raw_streams_are_bounded_at_exact_edges` collected 63
expected bytes but reported stdout EOF false and `pipe_open_after_exit` after
exit 0; the full Rust case therefore failed. The same failure was already retained
in the Meson-cutover investigation, and `log_capture.rs` is unchanged. The exact
isolated retry passed. Neither recurrence nor passing retry explains its cause;
this remains an intermittent supervision limitation, not a repaired defect.
The failed run keeps its original status and logs.

The [correction run](../tests/out/runs/extensions-m4-review-fixes-20261013/run.json)
(`20261013T220720Z_b95d4ee4`, clean `2e6a2c1`) passed 17/17, zero skips/unrun or
harness errors. It includes all six source-drift checks, five registered Rust
checks, both runner-unit cases (416/416 Swift checks and production driver replay
through Rust and both Python readers), the independent blackbox checker, and the
ordinary matrix, FIFO and seven combined-extension CLI rows. The M08 raw assertion
reader rejects a substituted 20-byte count while accepting the independently
prepared 22-byte target and all other shared raw expectations.

Its [acceptance credits](../tests/out/runs/extensions-m4-review-fixes-20261013/checkpoint/acceptance-credits.json)
contain all 197 passing case credits: 175 default and 22 required opt-ins, with 17
fresh replacements and 180 reviewed reuses. The adjacent `source-applicability.json`
records exact changed-file hashes, identical app inventories and the dependency
judgment. Changes after the full run are confined to Swift tests, M08 expectations,
ownership prose and record/retention metadata. Every direct matrix reader and
mechanical account check was rerun. Other scripts, shared helpers, fixture code
and product inputs are unchanged; copied-document/test-file exceptions in build
and dispatcher controls are identified as review judgments, not hash proof.

Exact-name read-only checks establish absence of 33 full-run and seven correction
observer channels and their recovery directories. All six regular full-run BYOXPC
sessions have observed launchd/registry/staging/plist absence. Registry recovery's
own receipt records verified cleanup and removed staging. The old 25 unnamed M3
empty shared-memory objects remain unverified; no prefix cleanup was attempted.
The build log, source snapshots, exact commands/configurations, cleanup observations,
original observer failure and passing retry remain in retained evidence. All
linked evidence and renders are gitignored and local-only.

### M4 rendered assessment and disposition

Fresh reviewer `/root/m4_rendered_review` (gpt-6-astra) inspected immutable
`m4-readable` at `b641054`, rendered using Pandoc 3.12, WeasyPrint 70.0 and
Poppler 26.10.0. Selected actual PNGs cover native evidence, the complete wide
M01–M08 table and ownership, guide/staged-guide native rules, contract versions,
coverage, fixture and suite accounts, and architecture topology/channel/timeline
and citation tables. The report distinguishes visual inspection from additional
rendered-text/source tracing and does not claim every page or link was inspected.
The comparison table uses a wider review page so all eleven columns remain visible;
this is a rendering adjustment, not a contract change.

F1 (documentation, accepted): opening inventory and Ownership table omitted M rows
and their distinct live owners. Corrected the handwritten introductions/table and
reader inventory; generated comparison rows remain generator-owned.

F2 (test/fixture defect, accepted): M08 advertised shared raw assertions but only
consumed its comparison, and its unused raw expectation described a different
20-byte target. Aligned constructed/raw expectations to independently prepared
22-byte `combined phase witness`, asserted every raw path, and added the wrong-count
negative check. Existing phase-isolation/native-cleanup observations remained valid;
this was not evidence of a product phase-protocol failure.

The focused reviewer recheck at `2e6a2c1` closed both findings after inspecting
corrected PNGs, all changed source, fresh M08 receipts and Rust/Python replay. No
new substantive finding remained. It verified that all other previously reviewed
document sources are byte-identical. The lead accepts those dispositions and the
197-case credits above, closing M4. Full initial/recheck reports, immutable sources,
HTML/PDF/PNG manifests and renderer scripts are under the correction run's
[reviews](../tests/out/runs/extensions-m4-review-fixes-20261013/reviews/).
A1-F11 and the broader evidence-account review remain M5.1 work.

## M5.1 closure

M5.1 is complete at corrected test/documentation source
`e1231bd4f4c3ebcf74cbfc6e261658f3212e991d`. Signed app 0.2.8 build 582 is from
`ea10ce39b418694630ba63c92d6a515d1006466e`, clean stamp `v0.2.8-62-gea10ce3`;
its worker identity is
`5fd52343fc4431d5d7f7ab0f7aed326d432950ec9922a98c9a16d0226ab6de2e`.
Request/response/envelope remain 4/18/7. Maximum reply remains 52,414,779 bytes;
ABI geometry and both documentation baselines are unchanged. The final checkpoint
commit adds plan, record and retention metadata; it is not the source of that build.

A1-F11 is repaired in `de8b343`. The Rust claim reader rejects present wrong-type
phase containers, entries, ordering objects, dispositions and spawn-failure
objects before interpreting optional values. Missing/null optional evidence stays
absent; degraded reporting-failure replies retain their raw evidence. Production
assembly controls assert unchanged raw replies and withheld ordinary projections
for the auditor's `phases: 7` and integer-disposition probes. The independent
Python claim reader rejects the same impossible types. Empty spawn objects expose
the documented responsibility boundary: full consumers require complete record
shape, while the disposition reader checks supported claims and contradictions.
A valid disposition projection is not whole-response structural certification.

The two new Rust controls first failed on the old reader and passed after the
repair, alongside the existing phase consistency control. The retained red/green
logs and exact test-only red diff are in the cancelled initial run's `checkpoint/`.
The versioning clarification distinguishes enforcement of an existing invariant
from a change to valid-document meanings; genuinely changed reading rules still
require the wire-contract bump. This repair introduces no new accepted document
shape or vocabulary.

The contract review also found that host diagnostics labeled every operation-11
failure detail as a wait budget. The production worker's future-release failure
instead publishes the observed ordinal. `ea10ce3` formats known code/kind pairs
with their actual units and leaves unfamiliar details uninterpreted. Real C-worker
stale/future second-release controls distinguish the 80 ms timeout from ordinal 3,
retain earlier phase completion and reject invented later action evidence. An
unfamiliar-code control requires raw detail without either interpretation. Worker
identity was regenerated because host orchestration is one of its inputs; the
wait, release store and eligibility behavior did not change.

The handwritten account now includes lifecycle actions in disposition step
indexing, phase-relative progress positions, transfer timeout cleanup, clock-native
results, failure codes 8–11 and their units, fresh-read syscall returns, and
phase-local validator retention and replanning. It distinguishes public version
numbers from the internal source identity. Shared reading rules and guide copies
already preserve these meanings; regeneration leaves their bytes unchanged.
The comparison vocabulary check records agreement for four observations, five
bases, three operation relations, three target relations, two orders and eight
limitations. Three limitations occur in the matrix's declared vocabulary and
separate constructed controls rather than a live matrix row; spelling checks alone
are not semantic evidence. The retained review records the corresponding source
traces and limits.

### M5.1 verification and corrections

- `extensions-m51-acceptance-20261013`, run ID `20261013T221346Z_bccd72df`,
  is an intentionally cancelled initial attempt at clean `de8b343`, build 581.
  Eleven completed cases passed and 186 were unrun. The phase-detail finding
  prompted cancellation through the dispatcher's supported SIGINT path. Original
  terminal accounting, unchanged-app result, source snapshot, build log and
  cancellation reason remain retained. It contributes no acceptance credits.
- `extensions-m51-final-20261013`, run ID `20261013T221825Z_ab6a8824`, at clean
  `ea10ce3`, build 582, completed 197/197 cases: 196 pass, one fail, no skips or
  unrun cases, unchanged app inventory. `blackbox_e2e/checker_controls` failed
  because its new mutation expected an unknown disposition string to be a type
  error; the reader correctly rejected the value with a vocabulary/consistency
  diagnostic. `e1231bd` separates wrong types from the unknown string, retaining
  both negative checks. The original full run remains failed.
- `extensions-m51-doc-closure-20261013`, run ID `20261013T223127Z_78754a9d`, at clean
  `e1231bd`, unchanged build 582, passed 9/9: all six `source_drift` cases,
  both `runner_unit` cases and the complete blackbox checker. Thus
  `generator_contract`, `limits_documentation`, checker controls and Swift
  comparison tests pass together. Actual Swift output is 416/416 with no guarded
  skip, including real phase controls and Rust/Python driver replay.

The final run's `checkpoint/acceptance-credits.json` maps 197 passing credits
(175 default plus 22 required opt-ins) to nine fresh replacements and 188 reviewed
reuses. `source-applicability.json` records the exact three-file delta, identical
app inventories and dependency judgments. The changed blackbox helper is imported
only by the freshly rerun checker case. All generated/shared-copy inputs,
production code, remaining executable test paths and fixtures are unchanged;
source-drift owns and freshly checks the handwritten prose. Build/dispatcher
fixture copies can include that prose and the test helper without executing the
changed path; those are reviewed exceptions, not deductions from app identity.
The initial cancelled and full failed histories are not rewritten.

The full run includes native lifecycle on standard and BYOXPC runners, maximum
reply on both paths, all eight combined-fault matrix controls, actual failure
boundaries, ordering mutations, signing/build guards and registry recovery.
The old M4 observer failure did not recur in this run, but its cause remains
unexplained; these passes do not establish its resolution.

### M5.1 rendered assessment and pause

Fresh read-only reviewer `/root/m51_rendered_review` (Astra) reviewed the immutable
`m51-corrected` render at `ea10ce3`. Its report identifies actual PNG inspection,
source/control traces and sampling limits; it found no substantive issue. The
lead separately identified the public-version/worker-identity sentence, generic
attempt-native-return wording and run-scope duplicate-record wording. All three
are corrected in `e1231bd`. The follow-up review of `m51-final` inspected those
changed rendered pages and the blackbox-control correction; it accepts all
corrections with no additional findings.
The lead accepts the disposition within the stated coverage; the review does not
replace execution or certify every page pixel by pixel.

Source/HTML/PDF/PNG manifests, reports, rendering scripts, the signed-build log,
contract/vocabulary review, source snapshots and exact cleanup receipts are in
[the final focused run](../tests/out/runs/extensions-m51-doc-closure-20261013/).
They are gitignored and **local to this checkout**. HTML links can preserve their
original `/private/tmp` preview paths; retained source, PDFs and PNGs preserve the
inspected content independently. Pandoc 3.12, WeasyPrint 70 and Poppler 26.10
produced the views.

Exact cleanup observations confirm absence of all 33 named native observer
channels/recovery directories in the full run, six regular BYOXPC services/staging/plists
and seven exact registry-recovery service identities. The focused run created no
such owned channels or BYOXPC sessions. No prefix-based cleanup was used. The older 25 empty M3
shared-memory objects with unrecorded names remain an explicit unverified-absence
limitation. No test, build, render or owned recovery task is active at closure.

The requested stop is M5.1. M5.2 and later milestones remain pending. Resume only
when the user authorizes continuation; the associated plan identifies the next
milestone and accepted evidence. H1's deferred hook investigation remains outside
this gate.


## M5.2 limits-account closure

Closed at clean `c76975aeff2a5ef41bb8a2216e5a59c3b9ca7eb1`, signed build 582
unchanged. Lead review traced all new phase/extension limits to source/value-test
owners and boundary controls; the existing source-inspected rows retain their
coverage limits. Runtime values, public versions and worker identity did not change.
The corrections describe the issuer clock starting after spawn, its separation
from worker/phase allowances, and admission precedence/NUL handling for extension
fields. Owning inputs are `docs/limits.json` and handwritten LIMITS/architecture
explanations; the limits generator regenerated and staged the guide copies.

`extensions-m52-20261013` (`20261013T230245Z_e01bd438`) passed 24/24 without skips
or unrun cases. Six source-drift, five Rust, both runner-unit, compiled C/Swift ABI
and limits, seven failure-boundary and three phase/extension/maximum-reply cases
all passed. Swift output is 416/416. The run's checkpoint maps all 197 required
case credits to 24 fresh results and 173 reviewed reuses. Exact file/app comparison
is separated from dependency judgments: changed manifest counting prose does not
alter numeric consumers; those reading the manifest as contract input were rerun;
build/dispatcher copies preserve unchanged executable paths. App inventories and
both baselines are unchanged. Exact observation confirms all 26 named observer
channels and recovery directories absent; this run created no BYOXPC sessions.

Fresh Astra reviewer `/root/m52_rendered_review` inspected actual LIMITS, budget
and source/staged guide PNGs, with source/control traces. No semantic issue was
found. M52-R1 identified narrow local preview columns fragmenting quantities and
ownership identifiers. The local rendering stylesheet now uses wide table pages,
normal cell wrapping and minimum widths; no repository document or generator was
changed for this presentation issue. Focused reinspection of LIMITS and both guide
copies closed R1. The lead accepts the bounded disposition; source-inspected waits
and other declared behavioral gaps were not upgraded to tested guarantees.

Initial and corrected immutable source/HTML/PDF/PNG artifacts and reports are in
[the retained M5.2 run](../tests/out/runs/extensions-m52-20261013/reviews/), local
and gitignored. Pandoc 3.12, WeasyPrint 70 and Poppler 26.10 rendered the account.
The initial snapshot also contains the surfaces used by the independent M5.3
review, whose two documentation findings remain pending at this checkpoint.


## M5.3 build-account closure

Closed at clean `d8f3d43637ce803f1189eb79e271bc3858efbd70`, build 582 unchanged.
Fresh Astra reviewer `/root/m53_rendered_review` found two documentation issues:
F1 overstated preflight entitlement inspection; F2 omitted the issuer from the
generated assembly Reads/Writes cells and graph tooltip. The lead accepted both.
The preflight README now names its actual inventory/signature/signer/hash checks
and links separate entitlement read-back. `docs/build.json` now includes the
already-shipped issuer in assembly inputs/outputs; the owning generator refreshed
BUILD and its graph. No refusal or baseline entry, runtime behavior or signing
invariant changed. Focused rendered reinspection closed both findings.

`extensions-m53-20261013` (`20261013T230939Z_92d1dc74`) passed 11/11: all six
source-drift cases, preflight, BYOXPC verification, signed-artifact mutations, build
guards and installed entitlement read-back. The checkpoint credits 11 fresh and
186 reviewed reused cases, with exact source/app comparisons separated from
dependency judgments. Descriptive manifest cells and suite prose do not alter the
retained executable paths or controlled inputs. The app inventories and both
baselines remain unchanged. Exact cleanup observed the owned installed service,
staging and plist absent; no native observer channels were created.

The initial report is preserved in M5.2 and copied with the corrected source,
HTML/PDF/PNG, complete graph raster, report/recheck and renderer scripts into
[the M5.3 run](../tests/out/runs/extensions-m53-20261013/reviews/). These are local
gitignored evidence. Pandoc 3.12, WeasyPrint 70 and Poppler 26.10 produced the
views. The local print renderer's earlier clipping/wrapping is corrected; the
reviewer inspected the full graph and readable corrected tables. Existing build
refusal coverage gaps remain explicit, and this is not release acceptance.


## M5.4 architecture-account closure

Closed at clean `a1112bc6627f07abb27478bfcfe9db7b45453fac`, build 582 unchanged.
Lead corrections distinguish action publication from process exit, explicit
identity generation from build checks, documentation inputs from runtime evidence
manifests, and request overrides from direct-driver/native fixture seams.
Fresh Astra reviewer `/root/m54_rendered_review` inspected all four graph rasters,
generated table bodies/captions, timeline, evidence paths, principles and gaps.
F1 found four incomplete BYOXPC node facts; the lead accepted it and corrected
`docs/architecture.json`, regenerating tables/DOT/SVG. Current issuer signing and
read-back are explicit; validation checks an existing or previously recorded
issuer, while an absent unrecorded issuer stays unknown. F2 found an exhaustive
host-binding-check overclaim; handwritten prose now distinguishes direct and
literal/simple-constant scans from undefined-import inspection, and excludes
arbitrary computed names. Focused rendered recheck closes both with no new finding.

Initial runs `extensions-m54-20261013` (`20261013T231554Z_32d4b770`, `9333cdb`)
and `extensions-m54-closure-20261013` (`20261013T231834Z_ff43635d`, `9eac2a2`)
each passed six source-drift cases and retain their intermediate renders/reports.
Final `extensions-m54-final-20261013` (20261013T232042Z_2053ece7) passed 10/10: six source-drift plus
accepted-input corpus, blackbox readers, ordinary phases and native lifecycle.
Its 197-case ledger credits ten fresh results and 187 reviewed reuses. Exact
source/app comparisons are separate from dependency judgments: architecture
description changes do not alter executable paths or controlled inputs. Both
baselines remain unchanged. Exact cleanup observations confirm owned resources
absent; detailed counts and receipts are in the checkpoint.

[Final renders and reports](../tests/out/runs/extensions-m54-final-20261013/reviews/)
are local/gitignored source, HTML/PDF/PNG, enlarged graphs and manifests from
Pandoc 3.12, WeasyPrint 70 and Poppler 26.10. This bounded review does not certify
every cited test body or private native state. The independent user-facing
review continues in M5.5; its public behavior controls are already fresh here.


## M5.5 user-account closure

Closed at clean `80d9daf8e1729c71394579b1f6b62787022613ee`, build 582 unchanged.
Fresh Astra reviewer `/root/m55_rendered_review` inspected the rendered source and
staged guide, grammar, FAQ, operating references and test guidance, tracing public
examples and capability refusals to independent controls. The lead accepts F1
(documentation): removed a stale mutation tally and rewrote the maximum-reply
catalog description to include ordinary/phased/fresh-read/lifecycle workloads.
F2 (harness metadata): both standalone BYOXPC witness cases now declare `gui`,
matching their installation mechanism and documented prerequisite. Existing
dispatcher equipment handling remains unchanged. Focused rendered/source recheck
closes both findings. No product behavior, public contract or generator input changed.

`extensions-m55-20261013` (20261013T232419Z_c076273a) passed 9/9: six source-drift cases, dispatcher
selection controls and both affected BYOXPC witness cases. The plan records the
GUI requirement for each, and the standard public corpus/phases/lifecycle/reader
checks passed at the immediately preceding M5.4 candidate with identical inputs.
The checkpoint maps 197 passing credits to nine fresh and 188 reviewed reuses;
changed catalog requirements were rerun, other case commands/requirements/context/
dependencies/membership remain unchanged, and the maximum-reply description is
display-only. Hash/app facts remain separate from applicability judgments. Guide
staging and both unchanged baselines pass. Exact cleanup confirms both owned
services, staging and plists absent; no native observer channels were created.

[Initial and corrected renders/reports](../tests/out/runs/extensions-m55-20261013/reviews/)
are local gitignored evidence, using Pandoc 3.12, WeasyPrint 70 and Poppler 26.10.
The initial archive's architecture is superseded by M5.4's final reviewed snapshot;
its other twenty source documents matched the user-facing review candidate before
the narrow README correction. The recheck covers that changed paragraph and the
catalog's corrected descriptions/prerequisites. Coverage omissions are explicit
in the report; no blanket visual inspection of every legacy page is claimed.
M5.6 will freshly consolidate the whole required selection on a new signed build.
