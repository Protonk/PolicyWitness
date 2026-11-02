# Browser sandbox source traces

Seventeen of the packet's files are cited by a trace.

| File | Traces |
| --- | --- |
| chromium `chrome/app/chrome_exe_main_mac.cc` | T7 |
| chromium `sandbox/mac/seatbelt_extension.cc` | T3 |
| chromium `sandbox/mac/seatbelt_extension.h` | T2, T3, T6 |
| chromium `sandbox/mac/seatbelt_sandbox_design.md` | T7 |
| chromium `sandbox/policy/mac/common.sb` | T1 |
| chromium `sandbox/policy/mac/gpu.sb` | T1 |
| firefox `security/sandbox/mac/Sandbox.mm` | T7 |
| firefox `security/sandbox/mac/SandboxPolicyContent.h` | T2 |
| firefox `security/sandbox/mac/SandboxPolicyGPU.h` | T1, T2, T4, T7 |
| ladybird `Libraries/LibSandbox/Sandbox.cpp` | T1, T4, T7 |
| ladybird `Services/Compositor/SandboxMacOS.cpp` | T1 |
| webkit `Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm` | T3, T4, T5, T6 |
| webkit `Source/WebKit/Shared/Sandbox/common.sb` | T1 |
| webkit `Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb` | T6 |
| webkit `Source/WebKit/WebProcess/com.apple.WebProcess.sb.in` | T1, T2, T6 |
| webkit `Source/WTF/wtf/darwin/DarwinExtras.h` | T5 |
| webkit `Source/WTF/wtf/spi/darwin/SandboxSPI.h` | T4, T5 |

The remaining eight are not cited. Two are the Chromium and Ladybird license
files. The other six are in the packet as context for cited files and contain
no extension rules or calls of their own:

- firefox `security/sandbox/mac/Sandbox.h` declares the parameter and policy
  types that `Sandbox.mm` fills; `moz.build` lists the files of that module.
- ladybird `Libraries/LibSandbox/Sandbox.h` declares the path, access and
  service inputs the generator consumes, including the read-only, read-execute
  and read-write access enum. `Services/RendererSandboxMacOS.cpp` is the
  renderer's call into the generator; it adds only read-only paths, so unlike
  the compositor caller it produces no read-write issuance rule.
- webkit `Shared/Sandbox/macOS/common.sb` is the macOS include layer between
  the WebProcess template and the shared `common.sb`; it carries the conditional
  include of an additions file that is not in the packet, as the report notes.
  `Shared/Sandbox/preferences.sb` is the template's preferences include.

## Traces

Each trace names the source, states literally what it shows, describes what
PolicyWitness does at the same point, names the existing PolicyWitness test
equipment that already touches that point, and ends in the numbers of the
questions it raises. The questions themselves are listed after the traces.
The traces identify source relationships; the first investigation separately
fixes its design and controls.

### T1. Issuance allowed inside a sandboxed process

All four source selections construct `file-issue-extension` allowances for
processes intended to run sandboxed. Their presence does not establish native
issuance or usable delegation in a running process.

- Chromium [gpu.sb](../browser-sandbox-sources/sources/chromium/sandbox/policy/mac/gpu.sb)
  lines 115–121 allow the read class for `(subpath "/")`, with a comment
  attributing the issuance to Metal on behalf of a compiler service whose Mach
  lookup is allowed at line 40. [common.sb](../browser-sandbox-sources/sources/chromium/sandbox/policy/mac/common.sb)
  lines 108–142 define read-write issuance for two cache subdirectories. The GPU
  caller at line 123 uses `maybe-allow-metal-shader-cache-access`: its gate at
  common.sb lines 140–142 requires `disable-metal-shader-cache` not to be true,
  and the inner call requires a defined helper bundle identifier parameter.
- Firefox [SandboxPolicyGPU.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 allow the read-write class for two cache subdirectories, exclude
  symlink vnodes, and guard the whole rule with a version predicate (see T7).
- WebKit [Shared/Sandbox/common.sb](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/common.sb)
  lines 63–74 define helpers that pair a `file-read*` or `file-write*` rule with
  a `file-issue-extension` rule of the matching class over the same path filter.
  [com.apple.WebProcess.sb.in](../browser-sandbox-sources/sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in)
  lines 636–640 define a directory variant and lines 733–746 use them. Line 744
  passes `(extension "com.apple.app-sandbox.read")` as the path filter itself,
  coupling the issuance rule to an extension predicate; lines 745–746 use the
  read-write predicate with report and telemetry modifiers. Whether those
  constructions permit effective re-delegation is a runtime question.
- Ladybird [Sandbox.cpp](../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  lines 256–280 generate one `file-issue-extension` clause per configured path
  and class, called at lines 737–738. The compositor caller
  [SandboxMacOS.cpp](../browser-sandbox-sources/sources/ladybird/Services/Compositor/SandboxMacOS.cpp)
  lines 54–60 creates a cache directory and adds it as read-write before the
  generator runs.

In PolicyWitness, the process that issues a token is never the sandboxed one.
The host runs a separate issuer under ordinary authority, collects the token,
and reaps that issuer before the worker is even spawned; the worker only ever
consumes. There is no request action that would make a worker issue, and the
validator has never been pointed at `file-issue-extension` as an operation, so
nothing in the tree says what such a query returns.

Existing equipment: none. Every issuer in the tree, production or fixture, runs
unsandboxed, and no suite queries the issuance operation.

Raises Q1–Q4.

### T2. The consumer-side extension filter

- Firefox [SandboxPolicyContent.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyContent.h)
  lines 338–348 and [SandboxPolicyGPU.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 229–240 attach `(extension "com.apple.app-sandbox.read")` to a
  `file-read*` rule. The comment says the extensions are issued by the font
  server; that issuer is Apple's, not Firefox's, and not in the packet.
- Chromium [seatbelt_extension.h](../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.h)
  lines 27–32 state the policy each wrapper type requires in the consumer.
- WebKit line 744 of the WebProcess template, as in T1.

PolicyWitness already writes this filter the same way. The public extension
example and the native fixture's policies both deny `file-read-data` and then
allow it back through `(extension "com.apple.app-sandbox.read")`, and the
directory policies do the same for `file-write*` with the read-write class. The
difference from the traces is granularity: the browsers attach the filter to the
whole `file-read*` family, while PolicyWitness attaches it to the single
`file-read-data` operation and has never looked at the other members.

Existing equipment: the native fixture's `no_predicate`,
`directory_no_predicate` and `directory_read_only_no_predicate` scenarios and
the `no_predicate` row of the production `extension_directory` case each remove
the filter while keeping the native calls. Nothing separates the members of
`file-read*`.

Raises Q17 and Q18.

### T3. Wrapper lifecycle semantics

- Chromium [seatbelt_extension.cc](../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.cc)
  lines 52–55 treat a consume result greater than zero as success; lines 57–62
  consume then drop both handle and token without a release; lines 64–69 treat a
  zero release return as success. The header's lines 60–72 say a consuming
  process may revoke at any time and that a revoked extension can be re-acquired
  by constructing a new object from the same token. The implementation's lines
  75–79 describe token internals; that is a Chromium comment, not a macOS fact.
- WebKit [SandboxExtensionCocoa.mm](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
  lines 61–73 treat only `-1` as a failed consume; lines 75–78 release with the
  handle exchanged to zero; lines 55–59 zero the token on destruction; lines
  366–430 count uses so that only the last revoke calls release, and provide
  consume-permanently variants that never release.

PolicyWitness sides with WebKit on the consume result: only `-1` means no
handle, and anything else is recorded as the handle it got. It does not count
uses or wrap handles in objects. A specimen may consume once and release once,
each as an explicit action in a phase, and the release's return value is
published as a number with no reading attached. If a worker exits without
releasing, nothing releases for it. So the two engines' disagreement about a
zero consume result is something PolicyWitness has never had to settle, because
it has never seen one.

Existing equipment: the native fixture's `lifecycle`, `no_consume`,
`no_release`, `issuer_exit`, `rejected_token` and `retained_fd` scenarios; the
production `extensions` case's omitted-action and cross-phase placements; the
`extension_boundaries` controls for native refusal, absent symbols and
consumption or release interrupted at the pre-call, in-call and pre-publication
positions; and the `extension_combinations` rows that pair those interruptions
with abnormal exit. None of it consumes a token twice, releases a handle twice,
or releases a value that was never a handle.

Raises Q5–Q8.

### T4. Flags and path preparation

- WebKit [SandboxExtensionCocoa.mm](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
  lines 86–120 map a no-report option to `SANDBOX_EXTENSION_NO_REPORT` and an
  option named do-not-canonicalize to `SANDBOX_EXTENSION_CANONICAL`, and add
  `SANDBOX_EXTENSION_USER_INTENT` on the Mac for the process-bound read type.
  Lines 154–203 resolve symlinks with `realpath` and then issue with the
  canonical flag set. The directory helper at lines 162–172, called from
  lines 228–234, creates a directory before resolving it. Lines 236–265 issue
  for a temporary-directory path that need not exist yet.
  [SandboxSPI.h](../browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
  lines 73–75 declare the three flags as external constants; their values are
  not in the source.
- Firefox GPU line 167 excludes symlink vnodes from issuance in the policy.
- Ladybird [Sandbox.cpp](../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  lines 123–152 `stat` then `realpath` each path and silently skip paths that do
  not exist.

PolicyWitness resolves the declared path with `realpath` and records the
resolved file's identity and metadata before issuing, then passes a flags
argument of zero. The native fixture does the same. A symlink is accepted as a
declaration and resolved through; any owner or file type is accepted; the path
has to exist, because the resolution and the metadata read both need it. The
documented hazard is replacement: the token names a path, so a file swapped in
between issuance and consumption is what the consumer reaches, and the evidence
is written to show that rather than hide it. No flag other than zero has ever
been passed, and the exported values of the three WebKit flag constants have
not been read.

Existing equipment: the production `extensions` case issues for a symlink and
checks the resolved identity, and replaces the target between issuance
preparation and consumption; the `extension_directory` rows and the native
`directory*` scenarios issue for a directory with the absent child recorded
before issuance and created exclusively afterward; the native `issue_failure`
scenario substitutes an empty path at the native call. Nothing issues for a
path that does not yet exist, with a nonzero flag, or for the link path rather
than its resolution.

Raises Q9–Q12.

### T5. Process-bound issuance

- [SandboxSPI.h](../browser-sandbox-sources/sources/webkit/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
  lines 79, 80 and 96 declare issue variants that take an `audit_token_t`; line
  83 declares a query variant that takes one too.
- WebKit [SandboxExtensionCocoa.mm](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
  lines 110–116 refuse to issue the process-bound read type without an audit
  token and add the user-intent flag on the Mac; lines 323–333 are its caller;
  lines 99–108 choose the bound variant for Mach and IOKit whenever a token is
  supplied. [DarwinExtras.h](../browser-sandbox-sources/sources/webkit/Source/WTF/wtf/darwin/DarwinExtras.h)
  lines 55–92 are the thin wrappers.
- Chromium's wrapper never uses the bound variants. Firefox and Ladybird issue
  nothing natively in the retained files.

PolicyWitness cannot bind a token to its worker as things stand, because the
order is wrong for it: the issuer has already produced the token and been
reaped by the time the worker is spawned, so there is no worker PID, let alone
an audit token, when the issue call happens. The worker is a plain posix_spawn
child with a shared-memory channel for the token and no Mach port back to the
host. Every token in the tree is the unbound kind.

Existing equipment: none calls a bound variant. The `extension_boundaries`
issuer-death and deadline controls are about losing the issuer before
publication, not about a bound call against an exited target.

Raises Q13–Q16.

### T6. Non-file extension classes (boundary, not a starting point)

WebKit has native issuance wrappers and consumer-side policy predicates for
Mach, IOKit and generic extensions: the WebProcess template lines
748–753 and the `com.apple.webkit.extension.mach` filters from line 797 on,
[webcontent-defines.sb](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb)
lines 94–245 for `com.apple.webkit.extension.iokit`, and
[SandboxExtensionCocoa.mm](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
lines 267–364 for the handle constructors. Chromium's header line 34 leaves
these as a TODO. PolicyWitness admits exactly two classes, the file read and
read-write ones, and refuses anything else at admission. No existing equipment
touches another class. This trace is retained for a later plan; see
[boundaries owned elsewhere](../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md#boundaries-owned-elsewhere).

### T7. Context-only traces

These inform interpretation and preparation without adding separate experiments
to the first investigation.

- **Apply before loading frameworks.** The Chromium
  [design document](../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_sandbox_design.md)
  lines 79–96 and [chrome_exe_main_mac.cc](../browser-sandbox-sources/sources/chromium/chrome/app/chrome_exe_main_mac.cc)
  lines 165–177 and 211–214 apply the sandbox before `dlopen` of the main
  framework so that static initializers cannot acquire resources outside it. The
  document says nothing about extensions. PolicyWitness's C worker goes the
  other way on purpose: before it applies the policy it resolves the extension
  symbols it will need, sets up its reporting channel and maps the token, so
  that nothing after apply has to acquire anything. What the loader itself did
  during startup, and what state was inherited across the spawn, is not
  observed. This trace informs the pilot's preparation boundary; comparing
  framework initialization strategies is deferred.
- **Firefox's version predicate.** [SandboxPolicyGPU.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 guard issuance with `(<= macosVersion 1500)` while the comment
  speaks of macOS 14 and earlier; [Sandbox.mm](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  lines 292–297 encode the version as major times one hundred plus minor. On this
  host a value encoding macOS 26 would not select that branch. A synthetic
  parameter could select it, but would not reproduce Firefox on an older OS.
  The packet report records the discrepancy without judging it; so does this
  record.
- **Third-party issuers.** Firefox's font comments (T2) and Chromium's Metal
  comments (T1) describe Apple-owned issuance paths, with different issuer and
  recipient roles. The packet does not contain those implementations. Nothing
  in PolicyWitness observes them, and a policy allowance is not evidence that
  they issue.
- **Policy application entry point.** Firefox ([Sandbox.mm](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  line 562) and Ladybird ([Sandbox.cpp](../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  line 748) apply through `sandbox_init_with_parameters`. PolicyWitness and its
  native fixture compile the policy first and apply the compiled form as a
  second call, so every existing case uses that two-step path. Comparing entry
  points would require later review.

## Questions

This list is the only copy of the questions; the plan refers to them by number
and never restates them. Each question gives the observable, what it needs
beyond the first investigation's apparatus (a supervisor, a sandboxed issuer
and a sandboxed recipient, two owned files, the read class, flags `0`, no
release, no self-consumption), and what an answer does not establish. Only
Q1 and Q2 are active; Q3–Q18 are an unordered inventory for later review, not
commitments or automatic follow-ups to an unexpected result.

**Issuance inside the sandbox (T1)**

- **Q1 (active lead).** Under the specified issuance restrictions, whether an
  already sandboxed issuer produces a token that a separately sandboxed
  recipient accepts and consumes, and whether that recipient's fresh access
  changes from before to after consumption. The parts are recorded
  independently, including failures and unavailable stages: (a) issuance, the
  raw issue return under each issuer arrangement; (b) transfer, framing and
  recipient acceptance; (c) consumption, the raw consume return; (d) access, the
  recipient's fresh reads before and after consumption; (e) contrast, the
  matching arrangement against absent, wrong-class and wrong-path allowances,
  omitted consumption and omitted recipient predicate. The issuer never consumes
  its own token. *Needs:* the first investigation as specified in the plan.
  *Does not establish:* private kernel state, general permissions, revocation,
  or the cause of a permission-shaped failure.
- **Q2 (active companion).** Two parts. (a) Observed: what `file-issue-extension`
  queries using `NONE` and `PATH` return, as raw return/errno pairs, against the
  live, paused issuer before issuance in each row. (b) Representation: what part
  of the native call's context those two filters carry, answered from the
  validator source, the complete type argument and the recorded exported flag
  value, not from trials. The current validator passes no extension class
  alongside a path. *Needs:* nothing beyond the first investigation for (a);
  source inspection for (b). *Does not establish:* usable issuance, a
  class-specific issuance prediction, prediction/enforcement agreement, a need
  for a new query API, or a production comparison. Query inadequacy does not
  prevent Q1.
- **Q3.** Whether a token the worker issued and then consumed itself widens that
  worker's own access, observed as fresh reads before consume, after consume and
  after release, under policies with and without the consumer-side filter.
  *Needs:* one sandboxed process that issues, consumes, reads and releases; no
  recipient. *Does not establish:* general self-delegation, revocation, or
  access beyond the read operation and target observed.
- **Q4.** Whether an issuance allowance whose path filter is itself
  `(extension ...)` permits issuing for a path the process reaches only through a
  consumed extension, in the same process. *Needs:* a first token from an
  outside issuer, a process that consumes it and then issues under the
  extension-filtered allowance, and a recipient that shows the second token
  usable. *Does not establish:* WebKit's re-delegation behavior; a nonnull second
  issue return alone is not usable delegation.

**Lifecycle (T3)**

- **Q5.** What values consume returns on this host: whether zero ever appears,
  and whether repeated consumption of one token in one process returns equal or
  different values. *Needs:* repeated consume calls on one token in one process
  with every raw value retained. *Does not establish:* equality as an identity
  claim; absence of zero across the trials run as absence in general; a
  resolution of the Chromium/WebKit success-condition difference. If zero is
  observed, access observations still matter.
- **Q6.** Whether the same token consumes again after a release, and what fresh
  access looks like afterward. *Needs:* a release followed by a second consume,
  with a fresh read after each. *Does not establish:* general revocation
  semantics; the path-replacement hazard still applies to each read.
- **Q7.** What release returns for a handle already released, a handle never
  obtained, and a value that was never a handle. *Needs:* release calls with
  prepared values and a process whose death would itself be the observation.
  *Does not establish:* a reading of the returned numbers or any memory-safety
  claim.
- **Q8.** What access or persistent effects distinguish explicit release from
  omission and process exit. A live worker can compare fresh access after
  release with omission (the native suite already has `no_release`). After
  exit, another observer can inspect filesystem effects or its own authority,
  not the exited worker's fresh access. *Needs:* a specified surviving observer
  and observable before an exit experiment can be selected. *Does not
  establish:* exit-time revocation from filesystem effects alone.

**Flags and paths (T4)**

- **Q9.** What values libsandbox exports on this host for the three flag
  constants, and whether issuance, consumption or fresh access differ for the
  same target under each. *Needs:* `dlsym` of the three constants with their
  numeric values recorded, then one issue call per value. *Does not establish:*
  values or meanings on another host or OS; any meaning beyond the observed
  differences.
- **Q10.** For a symlink target: issuance for the link path with and without the
  canonical flag, then fresh reads through the link and through the resolved
  path. *Needs:* an owned symlink to A, issuance for the link path, and two
  separate fresh reads. *Does not establish:* general symlink semantics; the
  replacement hazard applies to both paths.
- **Q11.** Issuance for a path that does not exist yet, then creation, then
  fresh access; and issuance for a path whose parent does not exist. *Needs:* a
  stated creator for the path and its authority, with creation after issuance.
  *Does not establish:* creation authority as delegated read; a nonnull return
  for an absent path as usable delegation.
- **Q12.** Whether a token for a directory issued before a descendant exists
  covers that descendant. The native directory case already records absence
  before issuance and tests subsequent exclusive creation with controls.
  *Needs:* an additional distinction, such as fresh reading of a descendant
  created by a different process, before selection; the existing coverage is
  retained. *Does not establish:* anything the directory case already answers.

**Process binding (T5)**

- **Q13.** Whether a token issued to the worker's audit token consumes in the
  worker. *Needs:* Q15's acquisition, a recipient alive before issuance, and
  the bound issue variant resolved. *Does not establish:* binding behavior at
  other timings relative to the target's apply, or a confinement benefit.
- **Q14.** Whether the same token consumes in a sibling process, with result and
  errno. This is a deferred process-binding control, separate from Q1's unbound
  delegation. *Needs:* Q13's apparatus plus a second recipient. *Does not
  establish:* a kernel-cause claim from errno.
- **Q15.** How a supervisor can obtain a posix_spawn child's audit token, with
  the acquisition mechanism, any supplied resource and its lifetime explicit.
  *Needs:* a chosen mechanism, the resource it supplies to the child and the
  authority and effect of that resource on the proposed observation; a pre-apply
  reporting resource is not automatically disqualifying. *Does not establish:*
  a PolicyWitness topology; a recipient waiting before apply is a candidate
  arrangement, not established behavior.
- **Q16.** What the bound issue call returns when the target process has
  already exited. *Needs:* Q13's apparatus with the target reaped before
  issuance. *Does not establish:* a general liveness check.

**Consumer-side filter (T2)**

- **Q17.** Which members of the `file-read*` family a consumed read extension
  widens when the filter is attached to each operation separately. *Needs:*
  recipient policies that deny the family and allow one member back through the
  predicate per trial, with a separate fresh operation per member. *Does not
  establish:* members not tried, or browser behavior.
- **Q18.** Whether query verdicts for the target change across before-consume,
  after-consume and after-release. The existing checks accept any pattern.
  *Needs:* queries against the recipient at the three boundaries; the first
  investigation queries only the issuer. *Does not establish:* a stable pattern
  as a requirement rather than a learning; prediction/enforcement agreement.
