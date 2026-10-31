# Browser sandbox source traces

Source readings behind the questions in
[BROWSER-TRACE-INVESTIGATIONS-PLAN.md](../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md).

## The packet

[records/browser-sandbox-sources](../browser-sandbox-sources/README.md)
holds 25 complete upstream files at fixed commits of Chromium, Firefox, WebKit
and Ladybird. Its [report](../browser-sandbox-sources/REPORT.md) explains
the selection and what is missing; its
[catalog](../browser-sandbox-sources/SOURCE-CATALOG.md) identifies every
file and links its pinned upstream location; `MANIFEST.json` and `SHA256SUMS`
carry the identities, and `python3 VERIFY.py` checks them offline. Line numbers
below refer to the unmodified files under `sources/`. The report's coverage
limits apply to every trace: a retained policy fragment may depend on inputs that
are not in the packet.

## Traces

Each trace names the source, states literally what it shows, states what
PolicyWitness does at the same point, and ends in the questions it raises. The
questions are collected in the plan. The traces identify source relationships; the
first investigation separately fixes its design and controls.

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

PolicyWitness's production issuer runs under ordinary authority outside the
worker's sandbox. There is no worker issuance action or established query
coverage for `file-issue-extension`. Raises Q1–Q4.

### T2. The consumer-side extension filter

- Firefox [SandboxPolicyContent.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyContent.h)
  lines 338–348 and [SandboxPolicyGPU.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 229–240 attach `(extension "com.apple.app-sandbox.read")` to a
  `file-read*` rule. The comment says the extensions are issued by the font
  server; that issuer is Apple's, not Firefox's, and not in the packet.
- Chromium [seatbelt_extension.h](../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.h)
  lines 27–32 state the policy each wrapper type requires in the consumer.
- WebKit line 744 of the WebProcess template, as in T1.

PolicyWitness's examples already use `(allow file-read-data (extension ...))`,
and the fixture's no-predicate control removes it. The traces attach the filter
to `file-read*`, a family, not to one operation. Raises Q17 and Q18.

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

PolicyWitness treats only `-1` as failure, admits one consume and one release
per specimen, publishes the release result without interpreting it, and makes
no exit-time release. The two engines' wrappers disagree about what a zero
consume result means. Raises Q5–Q8.

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

PolicyWitness resolves with `realpath` and records metadata before issuance,
passes flags `0`, admits symlinks and any owner or file type, and documents the
replacement hazard. Raises Q9–Q12.

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

PolicyWitness issues unbound tokens, and issuance completes before the worker
exists. The host knows the worker's PID only after spawn, and the worker is a
posix_spawn child with no Mach channel to the host. Raises Q13–Q16.

### T6. Non-file extension classes (boundary, not a starting point)

WebKit has native issuance wrappers and consumer-side policy predicates for
Mach, IOKit and generic extensions: the WebProcess template lines
748–753 and the `com.apple.webkit.extension.mach` filters from line 797 on,
[webcontent-defines.sb](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb)
lines 94–245 for `com.apple.webkit.extension.iokit`, and
[SandboxExtensionCocoa.mm](../browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
lines 267–364 for the handle constructors. Chromium's header line 34 leaves
these as a TODO. PolicyWitness admits two file classes. This trace is retained
for a later plan; see [boundaries owned elsewhere](../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md#boundaries-owned-elsewhere).

### T7. Context-only traces

These inform interpretation and preparation without adding separate experiments
to the first investigation.

- **Apply before loading frameworks.** The Chromium
  [design document](../browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_sandbox_design.md)
  lines 79–96 and [chrome_exe_main_mac.cc](../browser-sandbox-sources/sources/chromium/chrome/app/chrome_exe_main_mac.cc)
  lines 165–177 and 211–214 apply the sandbox before `dlopen` of the main
  framework so that static initializers cannot acquire resources outside it. The
  document says nothing about extensions. PolicyWitness's C worker resolves
  extension symbols and prepares reporting and token mappings before apply; see
  [starting authority](../../docs/WORKER.md#starting-authority-and-ambient-context).
  That account leaves loader internals and some inherited state unobserved.
  This trace informs the pilot's preparation boundary; comparing framework
  initialization strategies is deferred.
- **Firefox's version predicate.** [SandboxPolicyGPU.h](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 guard issuance with `(<= macosVersion 1500)` while the comment
  speaks of macOS 14 and earlier; [Sandbox.mm](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  lines 292–297 encode the version as major times one hundred plus minor. On this
  host a value encoding macOS 26 would not select that branch. A synthetic
  parameter could select it, but would not reproduce Firefox on an older OS.
  The packet report records the discrepancy without judging it; so does this plan.
- **Third-party issuers.** Firefox's font comments (T2) and Chromium's Metal
  comments (T1) describe Apple-owned issuance paths, with different issuer and
  recipient roles. The packet does not contain those implementations. This
  fixture does not observe them, and a policy allowance is not evidence that
  they issue.
- **Policy application entry point.** Firefox ([Sandbox.mm](../browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  line 562) and Ladybird ([Sandbox.cpp](../browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  line 748) apply through `sandbox_init_with_parameters`; PolicyWitness compiles
  and applies separately. The pilot uses the existing native fixture's separate
  compile/apply path; comparing entry points would require later review.
