# Browser trace investigations: starting points for sandbox-extension experiments

This plan investigates under what restrictions an already sandboxed issuer can
delegate usable file authority to another sandboxed process. Q1 and its bounded
query companion Q2 are the only active questions. The first investigation uses
an independent native fixture and ends in a durable report for maintainer review,
whether issuance, consumption or access succeeds or fails. It authorizes no
production change or promotion into a registered fixture or test suite.

Seven browser source traces supply the motivation and a deferred question
inventory. They remain useful beyond this first investigation. A later result
could justify a structural change to PolicyWitness, but the native question
does not require implementing a general multiprocess PolicyWitness capability.

The plan follows [planning a change](CONTRIBUTING.md#planning-a-change). It is
the associated plan permitted to link to the source packet at
[records/browser-sandbox-sources](records/browser-sandbox-sources/README.md),
per [records/AGENTS.md](records/AGENTS.md). The packet persists in `records/`
while this plan lives. The investigation report and its supporting evidence are
retained before review; they need not result in product work. Retirement of the
plan and its records is a later closeout decision, not the pilot's stopping rule.

## Boundary

Every experiment under this plan respects these limits.

- **Independent process roles.** Production PolicyWitness applies one policy
  once to one disposable worker. This pilot instead uses a fresh supervisor,
  issuer and recipient per trial. The issuer and recipient each apply their own
  policy once, except for the explicitly unsandboxed issuer baseline. The native
  fixture records OS, SDK, compiler, signing and process facts. Its observations
  are not production envelopes or evidence of PW's production phase protocol.
- **Sources can be named.** Reports may identify Chromium, Firefox, WebKit and
  Ladybird as motivating sources. Runtime findings describe the fixture and its
  recorded environment, not an installed browser. Source comments are not
  established macOS facts. The packet's
  [report](records/browser-sandbox-sources/REPORT.md) states the same boundary
  for the sources themselves: source relationships are inspectable, runtime
  behavior is not.
- **The core ideas in [AGENTS.md](AGENTS.md#core-ideas) hold.** Disposable
  sandboxed processes, explicit preparation, separate supervision and reporting,
  observations supporting effects, and no unsupported causal attribution apply
  to the pilot. Q2 queries precede issuance through the fixture's own observed
  barrier. Production wait, release and eligibility rules remain unchanged; a
  later change to them requires the
  [order-barrier mutation control](tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls).
- **Token confinement stays.** Raw tokens never enter a request, reply, report
  or retained artifact. The erasure discipline in
  [supplied extension authority](docs/WORKER.md#supplied-extension-authority)
  applies to any new issuer, channel or consumer the experiments introduce.
- **Keep the observations distinct.** A nonnull issue result, accepted transfer,
  consume return and fresh read establish different facts. Known bytes read
  through a newly opened descriptor establish that access in that process at
  that boundary. Their controlled contrast can support a bounded delegation
  finding; they do not reveal private kernel state or establish general
  permissions, revocation or the cause of a permission-shaped failure.
- **Operating constraints.** Native and opt-in work needs the Developer ID
  Application identity in the login keychain, a run outside any automation
  sandbox, and the checkout lock; see
  [tests/AGENTS.md](tests/AGENTS.md#sandboxed-automation-harnesses) and
  [tests/suites/sandbox_extensions_native/README.md](tests/suites/sandbox_extensions_native/README.md).
  Use the existing fixture's Developer ID signing and empty-entitlement context;
  retain its read-back rather than seeking different entitlements on failure.
  Scratch build outputs may live under [`.tmp/`](.tmp/AGENTS.md); sole copies of
  sources, evidence and reports may not. No release work is in scope.

## Where PolicyWitness stands

Read current behavior from these sources rather than from this summary.

| Topic | Where |
| --- | --- |
| Request shape, two classes, one declaration, one consume, one release | [Sandbox extensions](docs/PolicyWitness.md#sandbox-extensions); [extension output](docs/PolicyWitness.md#extension-and-fresh-read-output); [QUESTIONS.md](docs/QUESTIONS.md#can-policywitness-test-sandbox-extension-behavior) |
| Issuer, channel, worker preparation, lifecycle calls, erasure, known gap | [Supplied extension authority](docs/WORKER.md#supplied-extension-authority); [known gaps](docs/WORKER.md#known-gaps) |
| Limits and the issue-before-spawn ordering | [Specimen admission](docs/LIMITS.md#specimen-admission) rows `extension_*`; [interactions that matter](docs/LIMITS.md#interactions-that-matter) |
| Issuer implementation | [`pw_extension_issuer.c`](controller/tools/pw_probe_runner/pw_extension_issuer.c): `dlopen` of libsandbox, `sandbox_extension_issue_file` with flags `0`, class chosen by the `authority` field; [`pw_extension_channel.h`](controller/tools/pw_probe_runner/pw_extension_channel.h) |
| Worker side | [`prepare_extension`](controller/tools/pw_probe_runner/pw_probe_runner.c) resolves consume/release symbols before apply and validates the channel before apply; [`attempt_extension`](controller/tools/pw_probe_runner/pw_probe_runner.c) treats only `-1` as a failed consume and keeps one static handle |
| Host session | [`ExtensionIssuer.swift`](runner/Sources/PWRunnerCore/ExtensionIssuer.swift): `realpath` and `fstatat` before issuance, issuer spawned and reaped before the worker exists |
| Query side | [`sb_api_validator.c`](controller/tools/sb_api_validator/sb_api_validator.c): `NONE` or one filter value, including `PATH`, `GLOBAL_NAME` and `LOCAL_NAME`; queries use the no-report flag; no class-plus-path argument representation |
| Native fixture and its controls | [suite README](tests/suites/sandbox_extensions_native/README.md); [fixture README](tests/fixtures/sandbox_extensions/README.md); host, issuer and worker as three processes; file and directory scenarios |
| Production extension controls | [native extension boundaries](tests/suites/witness_contract/README.md#native-extension-boundaries) and the `check_extension*.py` checkers beside it |
| Evidence contract | [native extension evidence](tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence); [native sandbox extensions](tests/CHANGE-VERIFICATION.md#native-sandbox-extensions) |
| Process topology and architecture account | [process topology](docs/ARCHITECTURE.md#process-topology); [docs/architecture.json](docs/architecture.json) and its generator |

In one sentence: the issuer runs outside the sandbox under ordinary authority,
issues one of two file classes with zero flags for a host-resolved path, is
reaped before the worker is spawned, and the worker admits at most one consume
and one release. Production PW has no post-apply issuance action. Query operation
strings remain OS queries under [request admission](docs/REQUEST-GRAMMAR.md);
accepting a string does not establish a useful native prediction for it.

## The packet

[records/browser-sandbox-sources](records/browser-sandbox-sources/README.md)
holds 25 complete upstream files at fixed commits of Chromium, Firefox, WebKit
and Ladybird. Its [report](records/browser-sandbox-sources/REPORT.md) explains
the selection and what is missing; its
[catalog](records/browser-sandbox-sources/SOURCE-CATALOG.md) identifies every
file and links its pinned upstream location; `MANIFEST.json` and `SHA256SUMS`
carry the identities, and `python3 VERIFY.py` checks them offline. Line numbers
below refer to the unmodified files under `sources/`. The report's coverage
limits apply to every trace: a retained policy fragment may depend on inputs that
are not in the packet.

## Traces

Each trace names the source, states literally what it shows, states what
PolicyWitness does at the same point, and ends in the questions it raises. The
questions are collected below. The traces identify source relationships; the
first investigation separately fixes its design and controls.

### T1. Issuance allowed inside a sandboxed process

All four source selections construct `file-issue-extension` allowances for
processes intended to run sandboxed. Their presence does not establish native
issuance or usable delegation in a running process.

- Chromium [gpu.sb](records/browser-sandbox-sources/sources/chromium/sandbox/policy/mac/gpu.sb)
  lines 115–121 allow the read class for `(subpath "/")`, with a comment
  attributing the issuance to Metal on behalf of a compiler service whose Mach
  lookup is allowed at line 40. [common.sb](records/browser-sandbox-sources/sources/chromium/sandbox/policy/mac/common.sb)
  lines 108–142 define read-write issuance for two cache subdirectories. The GPU
  caller at line 123 uses `maybe-allow-metal-shader-cache-access`: its gate at
  common.sb lines 140–142 requires `disable-metal-shader-cache` not to be true,
  and the inner call requires a defined helper bundle identifier parameter.
- Firefox [SandboxPolicyGPU.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 allow the read-write class for two cache subdirectories, exclude
  symlink vnodes, and guard the whole rule with a version predicate (see T7).
- WebKit [Shared/Sandbox/common.sb](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/common.sb)
  lines 63–74 define helpers that pair a `file-read*` or `file-write*` rule with
  a `file-issue-extension` rule of the matching class over the same path filter.
  [com.apple.WebProcess.sb.in](records/browser-sandbox-sources/sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in)
  lines 636–640 define a directory variant and lines 733–746 use them. Line 744
  passes `(extension "com.apple.app-sandbox.read")` as the path filter itself,
  coupling the issuance rule to an extension predicate; lines 745–746 use the
  read-write predicate with report and telemetry modifiers. Whether those
  constructions permit effective re-delegation is a runtime question.
- Ladybird [Sandbox.cpp](records/browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  lines 256–280 generate one `file-issue-extension` clause per configured path
  and class, called at lines 737–738. The compositor caller
  [SandboxMacOS.cpp](records/browser-sandbox-sources/sources/ladybird/Services/Compositor/SandboxMacOS.cpp)
  lines 54–60 creates a cache directory and adds it as read-write before the
  generator runs.

PolicyWitness's production issuer runs under ordinary authority outside the
worker's sandbox. There is no worker issuance action or established query
coverage for `file-issue-extension`. Raises Q1–Q4.

### T2. The consumer-side extension filter

- Firefox [SandboxPolicyContent.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyContent.h)
  lines 338–348 and [SandboxPolicyGPU.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 229–240 attach `(extension "com.apple.app-sandbox.read")` to a
  `file-read*` rule. The comment says the extensions are issued by the font
  server; that issuer is Apple's, not Firefox's, and not in the packet.
- Chromium [seatbelt_extension.h](records/browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.h)
  lines 27–32 state the policy each wrapper type requires in the consumer.
- WebKit line 744 of the WebProcess template, as in T1.

PolicyWitness's examples already use `(allow file-read-data (extension ...))`,
and the fixture's no-predicate control removes it. The traces attach the filter
to `file-read*`, a family, not to one operation. Raises Q17 and Q18.

### T3. Wrapper lifecycle semantics

- Chromium [seatbelt_extension.cc](records/browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.cc)
  lines 52–55 treat a consume result greater than zero as success; lines 57–62
  consume then drop both handle and token without a release; lines 64–69 treat a
  zero release return as success. The header's lines 60–72 say a consuming
  process may revoke at any time and that a revoked extension can be re-acquired
  by constructing a new object from the same token. The implementation's lines
  75–79 describe token internals; that is a Chromium comment, not a macOS fact.
- WebKit [SandboxExtensionCocoa.mm](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
  lines 61–73 treat only `-1` as a failed consume; lines 75–78 release with the
  handle exchanged to zero; lines 55–59 zero the token on destruction; lines
  366–430 count uses so that only the last revoke calls release, and provide
  consume-permanently variants that never release.

PolicyWitness treats only `-1` as failure, admits one consume and one release
per specimen, publishes the release result without interpreting it, and makes
no exit-time release. The two engines' wrappers disagree about what a zero
consume result means. Raises Q5–Q8.

### T4. Flags and path preparation

- WebKit [SandboxExtensionCocoa.mm](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
  lines 86–120 map a no-report option to `SANDBOX_EXTENSION_NO_REPORT` and an
  option named do-not-canonicalize to `SANDBOX_EXTENSION_CANONICAL`, and add
  `SANDBOX_EXTENSION_USER_INTENT` on the Mac for the process-bound read type.
  Lines 154–203 resolve symlinks with `realpath` and then issue with the
  canonical flag set. The directory helper at lines 162–172, called from
  lines 228–234, creates a directory before resolving it. Lines 236–265 issue
  for a temporary-directory path that need not exist yet.
  [SandboxSPI.h](records/browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
  lines 73–75 declare the three flags as external constants; their values are
  not in the source.
- Firefox GPU line 167 excludes symlink vnodes from issuance in the policy.
- Ladybird [Sandbox.cpp](records/browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  lines 123–152 `stat` then `realpath` each path and silently skip paths that do
  not exist.

PolicyWitness resolves with `realpath` and records metadata before issuance,
passes flags `0`, admits symlinks and any owner or file type, and documents the
replacement hazard. Raises Q9–Q12.

### T5. Process-bound issuance

- [SandboxSPI.h](records/browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
  lines 79, 80 and 96 declare issue variants that take an `audit_token_t`; line
  83 declares a query variant that takes one too.
- WebKit [SandboxExtensionCocoa.mm](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
  lines 110–116 refuse to issue the process-bound read type without an audit
  token and add the user-intent flag on the Mac; lines 323–333 are its caller;
  lines 99–108 choose the bound variant for Mach and IOKit whenever a token is
  supplied. [DarwinExtras.h](records/browser-sandbox-sources/sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h)
  lines 55–92 are the thin wrappers.
- Chromium's wrapper never uses the bound variants. Firefox and Ladybird issue
  nothing natively in the retained files.

PolicyWitness issues unbound tokens, and issuance completes before the worker
exists. The host knows the worker's PID only after spawn, and the worker is a
posix_spawn child with no Mach channel to the host. Raises Q13–Q16.

### T6. Non-file extension classes (boundary, not a starting point)

WebKit has native issuance wrappers and consumer-side policy predicates for
Mach, IOKit and generic extensions: the WebProcess template lines
748–753 and the `com.apple.webkit.extension.mach` filters from line 797 on,
[webcontent-defines.sb](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb)
lines 94–245 for `com.apple.webkit.extension.iokit`, and
[SandboxExtensionCocoa.mm](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
lines 267–364 for the handle constructors. Chromium's header line 34 leaves
these as a TODO. PolicyWitness admits two file classes. This trace is retained
for a later plan; see [boundaries owned elsewhere](#boundaries-owned-elsewhere).

### T7. Context-only traces

These inform interpretation and preparation without adding separate experiments
to the first investigation.

- **Apply before loading frameworks.** The Chromium
  [design document](records/browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_sandbox_design.md)
  lines 79–96 and [chrome_exe_main_mac.cc](records/browser-sandbox-sources/sources/chromium/chrome/app/chrome_exe_main_mac.cc)
  lines 165–177 and 211–214 apply the sandbox before `dlopen` of the main
  framework so that static initializers cannot acquire resources outside it. The
  document says nothing about extensions. PolicyWitness's C worker resolves
  extension symbols and prepares reporting and token mappings before apply; see
  [starting authority](docs/WORKER.md#starting-authority-and-ambient-context).
  That account leaves loader internals and some inherited state unobserved.
  This trace informs the pilot's preparation boundary; comparing framework
  initialization strategies is deferred.
- **Firefox's version predicate.** [SandboxPolicyGPU.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 guard issuance with `(<= macosVersion 1500)` while the comment
  speaks of macOS 14 and earlier; [Sandbox.mm](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  lines 292–297 encode the version as major times one hundred plus minor. On this
  host a value encoding macOS 26 would not select that branch. A synthetic
  parameter could select it, but would not reproduce Firefox on an older OS.
  The packet report records the discrepancy without judging it; so does this plan.
- **Third-party issuers.** Firefox's font comments (T2) and Chromium's Metal
  comments (T1) describe Apple-owned issuance paths, with different issuer and
  recipient roles. The packet does not contain those implementations. This
  fixture does not observe them, and a policy allowance is not evidence that
  they issue.
- **Policy application entry point.** Firefox ([Sandbox.mm](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  line 562) and Ladybird ([Sandbox.cpp](records/browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  line 748) apply through `sandbox_init_with_parameters`; PolicyWitness compiles
  and applies separately. The pilot uses the existing native fixture's separate
  compile/apply path; comparing entry points would require later review.
- **Ladybird's macOS 27 branch** at lines 686–688 concerns a syscall, not
  extensions.

## What we want to learn

Only Q1 and Q2 are active. Q3–Q18 remain an unordered inventory for later review,
not commitments or automatic follow-ups to an unexpected result.

**Issuance inside the sandbox (T1)**

- **Q1 (active lead).** Under the specified issuance restrictions, whether an
  already sandboxed issuer produces a token that a separately sandboxed
  recipient accepts and consumes, and whether that recipient's fresh access
  changes from before to after consumption. Record issuance, transfer,
  consumption and access independently, including failures and unavailable
  stages. Compare matching, absent, wrong-class and wrong-path allowances with
  the controls specified below. The issuer never consumes its own token.
- **Q2 (active companion).** What `file-issue-extension` queries using `NONE`
  and `PATH` return against the live, paused issuer before issuance, and what
  part of the native call's context those queries represent. The current
  validator passes no extension class alongside a path. A returned verdict or
  a pattern across policies does not establish a class-specific issuance
  prediction or prediction/enforcement agreement. Query inadequacy does not
  prevent Q1 or require a new query API or production comparison.
- **Q3.** Whether a token the worker issued and then consumed itself widens that
  worker's own access, observed as fresh reads before consume, after consume and
  after release, under policies with and without the consumer-side filter.
- **Q4.** Whether an issuance allowance whose path filter is itself
  `(extension ...)` permits issuing for a path the process reaches only through a
  consumed extension, in the same process.

**Lifecycle (T3)**

- **Q5.** What values consume returns on this host: whether zero ever appears,
  and whether repeated consumption of one token in one process returns equal or
  different values. Equality is an observation, not an identity claim. If zero
  is not observed, the Chromium/WebKit success-condition difference remains
  untested; if it is, access observations still matter.
- **Q6.** Whether the same token consumes again after a release, and what fresh
  access looks like afterward.
- **Q7.** What release returns for a handle already released, a handle never
  obtained, and a value that was never a handle.
- **Q8.** What access or persistent effects distinguish explicit release from
  omission and process exit. A live worker can compare fresh access after
  release with omission (the native suite already has `no_release`). After
  exit, another observer can inspect filesystem effects or its own authority,
  not the exited worker's fresh access. A further exit experiment needs a
  specified surviving observer and observable before it can be selected.

**Flags and paths (T4)**

- **Q9.** What values libsandbox exports on this host for the three flag
  constants, and whether issuance, consumption or fresh access differ for the
  same target under each.
- **Q10.** For a symlink target: issuance for the link path with and without the
  canonical flag, then fresh reads through the link and through the resolved
  path.
- **Q11.** Issuance for a path that does not exist yet, then creation, then
  fresh access; and issuance for a path whose parent does not exist.
- **Q12.** Whether a token for a directory issued before a descendant exists
  covers that descendant. The native directory case already records absence
  before issuance and tests subsequent exclusive creation with controls. Retain
  that coverage; any follow-up must identify an additional distinction, such as
  fresh reading of a descendant created by a different process, before selection.

**Process binding (T5)**

- **Q13.** Whether a token issued to the worker's audit token consumes in the
  worker.
- **Q14.** Whether the same token consumes in a sibling process, with result and
  errno. This is a deferred process-binding control, separate from Q1's unbound
  delegation between a sandboxed issuer and recipient.
- **Q15.** How a supervisor can obtain a posix_spawn child's audit token, with
  the acquisition mechanism, any supplied resource and its lifetime explicit.
  A pre-apply reporting resource is not automatically disqualifying; its
  authority and effect on the proposed observation must be accounted for.
- **Q16.** What the bound issue call returns when the target process has
  already exited.

**Consumer-side filter (T2)**

- **Q17.** Which members of the `file-read*` family a consumed read extension
  widens when the filter is attached to each operation separately.
- **Q18.** Whether query verdicts for the target change across before-consume,
  after-consume and after-release. The existing checks accept any pattern; a
  stable one would be a learning, not a requirement.

## First investigation: Q1 and Q2

Use an investigation-local adaptation of
[`tests/fixtures/sandbox_extensions/native.c`](tests/fixtures/sandbox_extensions/native.c).
Its existing host/issuer/worker split, separate token storage and explicit
descriptor passing are useful equipment. Its unsandboxed issuer and pre-policy
worker read change for this pilot. The suite's checker owns acceptance criteria;
the native fixture's early exits gate equipment and execution.
Retain the adapted source with the investigation; do not edit production code,
the registered fixture, suite checkers or test catalog to conduct it.

### Preparation and application boundary

The first result concerns issuance after application with a prepared native
runtime. It does not claim issuance before any initialization, or reproduce
Chromium's framework startup. T7 explains why the boundary must be explicit.

| Stage | Operations and evidence |
| --- | --- |
| Supervisor before child launch | Create owned regular files A and B with known bytes under a fresh temporary directory outside privacy-protected user folders. Resolve their canonical absolute paths, record metadata and ordinary fresh-read baselines, and close target descriptors. Prepare exact policies and separate evidence/token channels; the token channels start empty. Pass strings and apparatus descriptors, never a target descriptor or pre-issued token. |
| Each child before apply | Record role, PID, credentials and the inherited descriptor inventory. Map the explicit channels, close their mapping descriptors, disable core dumps, resolve the needed libsandbox entry points, initialize fixed reporting storage, and compile the policy. Record preparation results and an inventory of loaded images. No target open, target `stat`/`realpath`, extension issue/consume/release, or extension warm-up occurs in either child before apply. |
| Application | Each sandboxed child applies its policy once and publishes the native result before advancing. Failure withholds dependent actions and remains evidence. The ordinary-authority issuer baseline follows C1's preparation but explicitly omits application. Source order and supervisor gates associate the application and later call publications with the same owned process. |
| After apply | The recipient opens, reads, identifies and closes A before token consumption. The supervisor completes Q2 against the waiting issuer, then releases its first issuance call. Native path processing within that call therefore occurs under the issuer's policy. The recipient validates the subsequent transfer, optionally consumes, and makes another fresh open/read/identity/close attempt. Record unavailable stages explicitly when issuance or transfer fails. |

Use the minimal C/libsystem/libsandbox setup of the existing native fixture;
do not add application frameworks or optional allocation instrumentation. Symbol
resolution before apply avoids confusing a loader failure with issuance refusal.
The supervisor's path preparation supplies names and metadata, not open-file
authority to the children. All native extension calls in the sandboxed issuer
and recipient occur after their respective application boundaries. The existing
fixture's pre-policy target-read baseline moves to the supervisor for this pilot.

Inspect the retained source and linked/loaded-image inventory for pre-apply
acquisitions, and record descriptor inventories immediately before apply and
before target access or issuance. A target descriptor already present invalidates
a fresh-acquisition inference. Retain application results, per-process ordered
markers, supervisor acknowledgements and independent wait/reap observations.
These establish the explicit preparation and observed order, not a complete
census of transient resources, Mach rights or private library initialization.
A comparison of pre- versus post-apply framework loading is later work.

### Fixed contrasts and positive controls

Use one signed executable with empty entitlements for all roles, identical
credentials, environment, path preparation and flags `0`. Every native issue call
requests `com.apple.app-sandbox.read` for A. B is another existing owned regular
file used only as the nonmatching policy path. Keep the issuer's ordinary data
and metadata read rules permissive in this first investigation; whether issuance
can exceed the issuer's own read access is not answered by these contrasts.
All sandboxed issuer policies share a file-write restriction, while only their
issuance allowance changes. Store the exact expanded policies, not just row names.

The recipient's fixed policy denies ordinary `file-read-data` and permits it
through the read extension predicate. The no-predicate row omits that exception.
No descriptor spans the two access attempts. The supervisor independently checks
target identity and bytes before and after the trial. A pre-consume successful
read is retained but prevents claiming that the later read demonstrates newly
delegated access. Neither child spawns the other; the supervisor execs fresh
siblings so that the recipient does not inherit an issuer's applied policy.

| Row | Issuer arrangement | Recipient intervention | Purpose |
| --- | --- | --- | --- |
| C0 | Ordinary-authority issuer, no applied profile | Consume if delivery permits | Context baseline for this binary, class, target, OS and recipient path |
| C1 | Applied common policy with unrestricted `file-issue-extension` allowance | Consume if delivery permits | Matched positive control for restricting issuance by class and path |
| C2 | Applied common policy; issuance denied except read class at literal A | Consume if delivery permits | Matching restricted delegation |
| C3 | Same common policy; explicit issuance denial, no exception | Consume if delivery permits | Absence of the issuance allowance |
| C4 | Same as C2, but policy exception names the known read-write class | Consume if delivery permits | Class mismatch with the native call still requesting read |
| C5 | Same as C2, but policy exception names literal B | Consume if delivery permits | Path mismatch with the native call still targeting A |
| C6 | Same as C2 | Accept transfer but omit consumption | Separate delivered bytes from consumed authority |
| C7 | Same as C2 | Consume if delivery permits; omit recipient extension predicate | Separate consumption from access allowed through that predicate |

Make the absent-allowance row an actual issuance restriction: deleting an allow
clause from `allow default` alone does not do so. The mismatch rows change policy
filters rather than inventing an invalid native class or nonexistent target.
No read-write issue call, symlink, directory, flag variant, process-bound token,
self-consumption or release comparison is part of this matrix. After the final
read, erase owned token buffers and reap the children; omission of release is
fixed across rows and supports no claim about exit-time revocation.

C1 is the smallest matched positive control for the filter contrasts: the same
sandboxed native setup can issue without the class/path restriction. A usable
delegation control additionally needs accepted transfer, a consume result and
known bytes obtained by a fresh recipient read, alongside its before-consume
observation. Nonnull issuance alone is only a positive control for token production.
C0 is one additional diagnostic baseline, not a search over identities or
entitlements. It tests the same path with issuer application omitted.

If C0 works but C1 does not, the limitation concerns the applied-sandbox setup;
it does not isolate a class/path restriction. If C1 works but C2 does not, the
narrow allowance or its representation remains at issue. If C2 works while
C3–C5 differ, those matched contrasts support a finding scoped to the changed
rules and recorded environment, not an errno-based claim about kernel cause.
If issuance works but delivery, consumption or fresh access does not, report each
stage's observations; do not collapse them into issuance refusal. If C0 and C1
both fail at a stage, neither designated baseline establishes feasibility there.
Preserve the results and withhold restriction-specific negative conclusions that
require a working baseline. A usable restricted result remains evidence even if
another control is unavailable, with the inconsistency made explicit. No control's
success is required for closeout.

For recipient access, compare C2 with C6 and C7 using valid observations from
the same apparatus revision. If C2 and C6 both accept delivery and their
pre-consume fresh reads fail, but C2 obtains known bytes through a fresh read
after a non-sentinel consume result while C6's fresh read still fails, the
contrast supports consumption-dependent delegation in this setup. Delivery alone
did not produce that access in C6.

For C2/C7, require accepted delivery, failed pre-consume fresh reads and
non-sentinel consume results in both rows before interpreting the access contrast.
If C2 gains fresh access while C7's read still fails, the contrast supports a role
for the recipient's extension predicate and shows why the consume result alone
does not establish access. Failed delivery or consumption leaves a contrast
requiring that stage unestablished. Pre-consume access, access in C6/C7 despite
the omission, or no access gain in C2 likewise does not support the proposed
separation; retain those observations and their limits without requiring another
trial or a successful delegation result.

### Ordering, query scope and evidence checks

Both children publish their preparation and application state before issuance.
The recipient's first fresh access precedes consumption, and its second follows
the consume result or recorded omission/unavailability. Keep issuance return,
bounded token publication, transfer readiness, recipient acceptance, consume
return and read results as separate publications. Preserve partial evidence when
a process dies between a native call and publication; never invent its return.
Transfer evidence includes framing/length validation and a transient equality
check between issued and received bytes. Retain only the check result, never
tokens, token hashes, token-bearing diagnostics or core files.

For Q2, make exactly the `NONE` and `PATH(A)` queries for
`file-issue-extension`, with no-report, against the live issuer paused before
issuance in each row. Preserve target PID, arguments, raw return, errno and
collection/release ordering. Missing query capability or a native query failure
is recorded and does not prevent the issuer from attempting Q1. The recipient
is not the query target. Do not add filter-ID searches, alternate query APIs or
recipient before/after query experiments from Q18.

The [validator implementation](controller/tools/sb_api_validator/sb_api_validator.c)
passes no class alongside a path. A `RAW` filter ID does not add that argument.
Record query availability and observed patterns separately from representational
adequacy. These sources do not establish a native way to query the complete
class-and-path issuance condition; a returned verdict does not supply the missing
context. The pilot's ordering evidence is not PW's `comparison.order=query_first`.

The report reader checks evidence completeness and consistency separately from
whether delegation occurred. Use small constructed report controls to reject
missing/reordered application or transfer evidence, a target descriptor inherited
or held across access boundaries, and claimed read success without matching
identity and bytes. Reuse of a descriptor number alone is not retention. Also
accept honestly recorded native refusal, failed consumption, unavailable queries
and missing dependent stages. Do not import the existing suite's mandatory
positive outcomes as this investigation's completion criteria.

### Repetitions, troubleshooting and endpoint

Run the 24 planned trials in three blocks of eight. Each block contains exactly
one trial of every arrangement C0–C7, with fresh processes and targets for each
trial and all existing evidence requirements. Choose and record each block's
sequence before starting that block. Blocks two and three may be ordered after
reviewing earlier observations and equipment behavior. Retain the chosen
sequences, each trial's block and chronological positions, and any relevant
scheduling rationale, alongside every trial's observations.

Deliberately vary positions across blocks: do not consistently put C0, C1 and C2
first or repeat the same adjacency relationships among positive and negative
controls. Sensible positional variation is sufficient; formal randomization is
not required. Three repetitions describe this small sample, not a universal or
statistically stable pattern. Scheduling discretion does not permit changing the
arrangements or their contrasts after seeing results.

Use explicit equipment-readiness checkpoints. An early checkpoint after the
planned C0/C1 trials in the first block is reasonable, as are checkpoints between
blocks; these review planned trials rather than adding control runs. Record
whether process control, evidence collection and cleanup remain functional, and
any diagnosed fault. Distinguish broken apparatus or missing required evidence
from a correctly executed native call returning an unexpected result, including
dependent stages honestly recorded as unavailable. Successful issuance,
consumption or access is never a prerequisite for continuing. When equipment
remains functional, execute all 24 planned trials. Do not add, replace, omit or
selectively repeat arrangements based on favorable or unfavorable native outcomes.

Use a 20-second trial deadline as in the native fixture, with bounded
termination/reaping and retained cleanup ownership if absence is unconfirmed.

Allow at most two documented equipment/instrumentation correction-and-retry
cycles and 60 minutes of cumulative troubleshooting across the pilot.
Troubleshooting ends at whichever limit is reached first. Each cycle permits at
most one affected trial rerun. Record these reruns separately from the 24 planned
positions; they do not replace the original observations. Retain the original
failures and any source changes; never combine results from different apparatus
revisions as matched contrasts.

After a source-level correction, keep the existing block sequence and continue
its remaining planned positions on the corrected revision if equipment functions.
Those trials count toward the 24 planned positions; record the apparatus revision
for every trial. Earlier positions remain recorded on their original revision,
including any invalidated evidence. A block spanning revisions is not a complete
set of matched contrasts, even if all eight positions were executed. Report only
contrasts supported within one revision and identify the missing comparisons as
coverage gaps. The single permitted diagnostic rerun does not repair or restart
that block, and no earlier arrangement is backfilled. Subsequent blocks still
contain C0–C7 once each; all remaining planned positions run if equipment functions.
Execution of a planned position and valid evidence for a contrast are separate
counts in the report.

If equipment prevents further execution within the troubleshooting allowance,
report the remaining positions as unrun rather than starting another battery.
Necessary cleanup still follows its ownership rules. A larger redesign, changed
signing context, extra contrasts or further retries require review.

Retain the report at `records/browser-trace-investigations/REPORT.md`, with the
pilot source, exact policies and inputs, build commands and source/binary hashes,
signature and entitlement read-backs, OS/SDK/compiler facts, raw token-free
observations, checker controls and cleanup records alongside it. This is an
investigation record associated with this plan under [records guidance](records/AGENTS.md),
not a replacement plan or promoted test. Existing suite evidence, if referenced,
keeps its managed ownership and is not moved into scratch or these records.

The report distinguishes attempted and unrun rows, observations and inference,
control failures, preparation limits, query limits, variable outcomes and
recommendations. Finish after all 24 planned trials, or with an incomplete report
when equipment prevents further execution within the troubleshooting allowance.
Retain the report even if delegation was never observed and return to the
maintainer. Neither a useful native query, successful issuance nor a feature
proposal is a condition of completion. Recommendations do not authorize follow-up
experiments, fixture promotion or production changes.

## Where later outcomes could land

These are options for maintainer review after the report, not work authorized
by this investigation.

- **Report only.** Observations, including failures or inconclusive controls,
  can close the investigation without any product change.
- **Documentation.** Narrowing or restating the known gap in
  [WORKER.md](docs/WORKER.md#known-gaps), the FAQ answer in
  [QUESTIONS.md](docs/QUESTIONS.md), or a premise in
  [LIMITS.md](docs/LIMITS.md#premises-behind-the-interactions). Documentation
  describes current behavior only; no change history.
- **Fixture cases.** New opt-in cases in `sandbox_extensions_native` with
  constructed checker controls, under
  [add or change tests](tests/AGENTS.md#add-or-change-tests) and the suite's
  evidence rules.
- **Request grammar and admission.** A new lifecycle action, new `authority`
  values, flags or classes touch [the wire contract](docs/CONTRACT.md) and its
  version decision, [REQUEST-GRAMMAR.md](docs/REQUEST-GRAMMAR.md), the limits
  manifest and its regenerated document, the admission corpus, and worker
  identity regeneration.
- **Worker or runner structure.** A future production issuance action or
  process-binding capability could change the authority account, process
  topology or token channel. A live binding target must exist before issuance.
  Whether issuance before that target applies its policy yields a usable token
  remains untested; the packet does not establish the target's sandbox state.
  Validation timing is a later design decision dependent on that evidence.
  Any proposal would identify affected implementation, contracts and checks:
  [architecture.json](docs/architecture.json) for topology changes, C/Swift layout
  agreement when layout changes, and the order-barrier mutation control when
  wait, release or eligibility changes. The independent pilot does not require
  retiring PW's ordinary-authority issuer.

## Boundaries owned elsewhere

- **Faithful cross-process delivery.** Issue in one sandboxed process and
  consume in another as a product capability needs a model of a second process
  that production PW does not have. A later proposal would own it. Q1's fixed
  native issuer/recipient experiment establishes no general product capability;
  Q14's process-binding control remains deferred.
- **Mach, IOKit and generic classes** (T6). Each needs a new issuer entry point,
  an attempt kind and a class vocabulary decision. A later plan.
- **Browsers as products**, installed-profile evidence, and anything the packet
  report lists as outside the sources.

## Considerations for later review

These preserve possible directions from the traces without expanding Q1/Q2.

- **Self-consumption is distinct from delegation.** Q3 asks whether an issuer
  can widen its own access; Q4 asks about issuing under an extension predicate.
  Neither is needed to observe Q1. The Chromium Metal comments motivate a helper
  recipient, while other retained constructions have different or unspecified
  callers. They do not supply one common browser runtime story.
- **Native equipment and product integration are separate.** Production has no
  issue action and admits a bounded authority vocabulary. The independent fixture
  can investigate native calls without first changing that grammar. Promotion
  would require a separate decision about useful coverage and maintained checks.
- **Preparation remains part of the result.** The initial issuer has permissive
  read rules and pre-resolved symbols. Testing tighter ordinary access, loading
  strategies or additional ambient restrictions would change that premise and
  needs another bounded question, not an automatic response to refusal.
- **Binding creates choices, not a prescribed topology.** Q15 concerns obtaining
  a child's audit token and accounting for the resources used. A recipient waiting
  before apply is a candidate arrangement for later testing, not established
  bound-token behavior. Any claimed confinement benefit would need its own
  observations and would not replace token erasure.
- **Consume success conditions differ.** Chromium uses `> 0`; WebKit and PW use
  `!= -1`. Q5 records values and associated behavior if selected later. No zero
  result means this difference remains untested; one occurrence would not specify
  all native consume behavior.
- **Flag mappings are source facts.** WebKit's `DoNotCanonicalize` sets
  `SANDBOX_EXTENSION_CANONICAL`. That mapping alone does not establish the
  installed flag's semantics; Q9/Q10 remain deferred.
