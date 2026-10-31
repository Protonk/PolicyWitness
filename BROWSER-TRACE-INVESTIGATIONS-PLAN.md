# Browser trace investigations: starting points for sandbox-extension experiments

This plan gives an agent working with the maintainer well-anchored starting
points for experiments on macOS sandbox extensions. It does not hand over a set
of experiments. It names traces in four browser engines' source, lists what we
want to learn, points at what PolicyWitness does today, and maps where an
outcome could land. The agent constructs each experiment and decides what change,
if any, its outcome motivates. A structural change to the worker or runner is a
legitimate landing, not an overreach.

The plan follows [planning a change](CONTRIBUTING.md#planning-a-change). It is
the one permitted inbound link to the source packet at
[records/browser-sandbox-sources](records/browser-sandbox-sources/README.md),
per [records/AGENTS.md](records/AGENTS.md). The packet persists in `records/`
while this plan lives. At closeout the plan is deleted; what the experiments
changed lives on in tests, documentation and application code, and the rest
remains in git history.

## Boundary

Every experiment under this plan respects these limits.

- **PolicyWitness witnesses one process on this host.** Results describe the
  recorded host (macOS 26, Apple Silicon), one policy applied once to one
  disposable worker, predictions collected before attempts, and observations
  recorded without interpretation. The native fixture records OS, SDK and
  compiler facts for the same reason.
- **No result is a claim about a browser.** The traces below are motivation and
  citation. An envelope, fixture report or document produced under this plan
  never names Chrome, Firefox, Safari, Ladybird or their engines as its subject,
  never says what a shipping browser can do, and never treats a source comment
  as an established macOS fact. The packet's
  [report](records/browser-sandbox-sources/REPORT.md) states the same boundary
  for the sources themselves: source relationships are inspectable, runtime
  behavior is not.
- **The core ideas in [AGENTS.md](AGENTS.md#core-ideas) hold.** One-way sandbox
  per process; host/worker split; witness over interpretation; predictions
  precede attempts; no dishonest attribution; runner simplicity. Any change to
  the wait, release store or eligibility rule reruns the
  [order-barrier mutation control](tests/CHANGE-VERIFICATION.md#order-barrier-mutation-controls).
- **Token confinement stays.** Raw tokens never enter a request, reply, report
  or retained artifact. The erasure discipline in
  [supplied extension authority](docs/WORKER.md#supplied-extension-authority)
  applies to any new issuer, channel or consumer the experiments introduce.
- **A native result is not an effect.** A nonnull token, a non-sentinel handle
  or a zero release return establishes that the call returned that value. Fresh
  descriptor observations establish access. Neither establishes kernel extension
  state, effective permission, revocation or cause.
- **Operating constraints.** Native and opt-in work needs the Developer ID
  Application identity in the login keychain, a run outside any automation
  sandbox, and the checkout lock; see
  [tests/AGENTS.md](tests/AGENTS.md#sandboxed-automation-harnesses) and
  [tests/suites/sandbox_extensions_native/README.md](tests/suites/sandbox_extensions_native/README.md).
  Signing and any release step stay with the maintainer. Pilots that are not
  tests live under [`.tmp/`](.tmp/AGENTS.md) with a recorded report.

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
| Query side | [`sb_api_validator.c`](controller/tools/sb_api_validator/sb_api_validator.c): one filter per query, `PATH`, `GLOBAL_NAME` and `LOCAL_NAME` recognized, queries made with the no-report flag |
| Native fixture and its controls | [suite README](tests/suites/sandbox_extensions_native/README.md); [fixture README](tests/fixtures/sandbox_extensions/README.md); host, issuer and worker as three processes; file and directory scenarios |
| Production extension controls | [native extension boundaries](tests/suites/witness_contract/README.md#native-extension-boundaries) and the `check_extension*.py` checkers beside it |
| Evidence contract | [native extension evidence](tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence); [native sandbox extensions](tests/CHANGE-VERIFICATION.md#native-sandbox-extensions) |
| Process topology and architecture account | [process topology](docs/ARCHITECTURE.md#process-topology); [docs/architecture.json](docs/architecture.json) and its generator |

In one sentence: the issuer runs outside the sandbox under ordinary authority,
issues one of two file classes with zero flags for a host-resolved path, is
reaped before the worker is spawned, and the worker consumes once and releases
once; the `file-issue-extension` operation has never been a PolicyWitness query
or attempt inside a sandbox.

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
questions are collected in the next section. Nothing here prescribes an
experiment's design, controls or expected outcome.

### T1. Issuance allowed inside a sandboxed process

All four engines allow `file-issue-extension` in a process that is itself
sandboxed.

- Chromium [gpu.sb](records/browser-sandbox-sources/sources/chromium/sandbox/policy/mac/gpu.sb)
  lines 115–121 allow the read class for `(subpath "/")`, with a comment
  attributing the issuance to Metal on behalf of a compiler service whose Mach
  lookup is allowed at line 40. [common.sb](records/browser-sandbox-sources/sources/chromium/sandbox/policy/mac/common.sb)
  lines 108–142 allow the read-write class for two cache subdirectories, and only
  when a helper bundle identifier parameter is defined.
- Firefox [SandboxPolicyGPU.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 allow the read-write class for two cache subdirectories, exclude
  symlink vnodes, and guard the whole rule with a version predicate (see T7).
- WebKit [Shared/Sandbox/common.sb](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/common.sb)
  lines 63–74 define helpers that pair a `file-read*` or `file-write*` rule with
  a `file-issue-extension` rule of the matching class over the same path filter.
  [com.apple.WebProcess.sb.in](records/browser-sandbox-sources/sources/webkit/Source/WebKit/WebProcess/com.apple.WebProcess.sb.in)
  lines 636–640 define a directory variant and lines 733–746 use them. Line 744
  passes `(extension "com.apple.app-sandbox.read")` as the path filter itself, so
  issuance is allowed for whatever a consumed read extension covers; lines
  745–746 do the same for read-write with report and telemetry modifiers.
- Ladybird [Sandbox.cpp](records/browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  lines 256–280 generate one `file-issue-extension` clause per configured path
  and class, called at lines 737–738. The compositor caller
  [SandboxMacOS.cpp](records/browser-sandbox-sources/sources/ladybird/Services/Compositor/SandboxMacOS.cpp)
  lines 54–60 creates a cache directory and adds it as read-write before the
  generator runs.

PolicyWitness never issues inside the sandbox. Its issuer is an unsandboxed
sibling, and no PolicyWitness query or attempt has ever named the
`file-issue-extension` operation. Raises Q1–Q4.

### T2. The consumer-side extension filter

- Firefox [SandboxPolicyContent.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyContent.h)
  lines 338–348 and [SandboxPolicyGPU.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 229–240 attach `(extension "com.apple.app-sandbox.read")` to a
  `file-read*` rule. The comment says the extensions are issued by the font
  server; that issuer is Apple's, not Firefox's, and not in the packet.
- Chromium [seatbelt_extension.h](records/browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_extension.h)
  lines 24–31 state the policy each wrapper type requires in the consumer.
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
  by constructing a new object from the same token. Lines 74–78 describe token
  internals; that is a Chromium comment, not a macOS fact.
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
  canonical flag set, lines 228–234 create a directory before resolving it, and
  lines 236–265 issue for a temporary-directory path that need not exist yet.
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

WebKit issues Mach, IOKit and generic extensions: the WebProcess template lines
748–753 and the `com.apple.webkit.extension.mach` filters from line 797 on,
[webcontent-defines.sb](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Sandbox/macOS/webcontent-defines.sb)
lines 94–245 for `com.apple.webkit.extension.iokit`, and
[SandboxExtensionCocoa.mm](records/browser-sandbox-sources/sources/webkit/Source/WebKit/Shared/Cocoa/SandboxExtensionCocoa.mm)
lines 267–364 for the handle constructors. Chromium's header line 34 leaves
these as a TODO. PolicyWitness admits two file classes. This trace is retained
for a later plan; see [boundaries owned elsewhere](#boundaries-owned-elsewhere).

### T7. Context-only traces

These are retained as traces. They raise no experiment under this plan, for the
reasons given.

- **Apply before loading frameworks.** The Chromium
  [design document](records/browser-sandbox-sources/sources/chromium/sandbox/mac/seatbelt_sandbox_design.md)
  lines 79–96 and [chrome_exe_main_mac.cc](records/browser-sandbox-sources/sources/chromium/chrome/app/chrome_exe_main_mac.cc)
  lines 165–177 and 211–214 apply the sandbox before `dlopen` of the main
  framework so that static initializers cannot acquire resources outside it. The
  document says nothing about extensions. PolicyWitness's C worker already
  resolves its symbols before apply and acquires nothing hidden; see
  [starting authority](docs/WORKER.md#starting-authority-and-ambient-context).
  Nothing new to witness.
- **Firefox's version predicate.** [SandboxPolicyGPU.h](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/SandboxPolicyGPU.h)
  lines 159–171 guard issuance with `(<= macosVersion 1500)` while the comment
  speaks of macOS 14 and earlier; [Sandbox.mm](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  lines 292–297 encode the version as major times one hundred plus minor. On this
  host the branch is off and cannot be exercised. The packet report records the
  discrepancy without judging it; so does this plan.
- **Third-party issuers.** Firefox's font comments (T2) and Chromium's Metal
  comments (T1) rely on Apple framework code issuing tokens to Apple services.
  PolicyWitness cannot witness those issuers, and a policy allowance is not
  evidence that they issue.
- **Policy application entry point.** Firefox ([Sandbox.mm](records/browser-sandbox-sources/sources/firefox/security/sandbox/mac/Sandbox.mm)
  line 562) and Ladybird ([Sandbox.cpp](records/browser-sandbox-sources/sources/ladybird/Libraries/LibSandbox/Sandbox.cpp)
  line 748) apply through `sandbox_init_with_parameters`; PolicyWitness compiles
  and applies separately. No extension question depends on this unless an
  experiment produces a difference it cannot otherwise explain.
- **Ladybird's macOS 27 branch** at lines 686–688 concerns a syscall, not
  extensions.

## What we want to learn

Each item is phrased as something an envelope or fixture report could contain.
Q1 is the lead; the rest are unordered. An experiment may answer one, several,
or add one.

**Issuance inside the sandbox (T1)**

- **Q1 (lead).** Whether a worker under a policy that allows
  `file-issue-extension` for a class and path obtains a nonnull token from the
  issue call after apply, and what result and errno it obtains when the
  allowance is absent, the class differs, or the path lies outside the filter.
- **Q2.** Whether the native query can address `file-issue-extension` at all
  with a filter the validator can pass, and whether its verdict tracks the
  allowance. This decides whether T1 experiments carry PolicyWitness's central
  prediction-before-attempt comparison or only attempts.
- **Q3.** Whether a token the worker issued and then consumed itself widens that
  worker's own access, observed as fresh reads before consume, after consume and
  after release, under policies with and without the consumer-side filter.
- **Q4.** Whether an issuance allowance whose path filter is itself
  `(extension ...)` permits issuing for a path the process reaches only through a
  consumed extension, in the same process.

**Lifecycle (T3)**

- **Q5.** What values consume returns on this host: whether zero ever appears,
  and whether repeated consumption of one token in one process returns equal or
  different values. Equality is an observation, not an identity claim.
- **Q6.** Whether the same token consumes again after a release, and what fresh
  access looks like afterward.
- **Q7.** What release returns for a handle already released, a handle never
  obtained, and a value that was never a handle.
- **Q8.** Whether fresh access after consume differs when the worker releases
  versus when it exits without releasing, as far as a later observer in the same
  specimen can see.

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
  covers that descendant. The directory case in the native suite already covers
  part of this; the open part is the before-and-after of the descendant's
  creation relative to issuance.

**Process binding (T5)**

- **Q13.** Whether a token issued to the worker's audit token consumes in the
  worker.
- **Q14.** Whether the same token consumes in a sibling process, with result and
  errno. This is the one two-process experiment this plan admits, in the native
  fixture only.
- **Q15.** How the host can obtain a posix_spawn child's audit token without
  handing the worker a resource before apply.
- **Q16.** What the bound issue call returns when the target process has
  already exited.

**Consumer-side filter (T2)**

- **Q17.** Which members of the `file-read*` family a consumed read extension
  widens when the filter is attached to each operation separately.
- **Q18.** Whether query verdicts for the target change across before-consume,
  after-consume and after-release. The existing checks accept any pattern; a
  stable one would be a learning, not a requirement.

## Where outcomes could land

The agent decides. The map says what each landing entails.

- **Nowhere.** An observation that confirms documented behavior is recorded in
  the pilot's report and closed.
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
- **Worker or runner structure.** Issuance inside the worker changes the
  authority story and may retire or re-purpose the issuer process. Bound
  issuance inverts the issue-before-spawn order and moves channel validation
  past apply. Either may change `pw_probe_runner`, the Swift host, or the
  process topology, which means [architecture.json](docs/architecture.json) and
  its regenerated account, the layout golden, and the order-barrier mutation
  rerun. This landing is legitimate and should be weighed on the same terms as
  the others.

## Boundaries owned elsewhere

- **Faithful cross-process delivery.** Issue in one sandboxed process and
  consume in another as a product capability needs a model of a second process
  that this project does not have. A separate plan owns it. Q14's sibling is a
  negative control in the fixture, not a start on that model.
- **Mach, IOKit and generic classes** (T6). Each needs a new issuer entry point,
  an attempt kind and a class vocabulary decision. A later plan.
- **Browsers as products**, installed-profile evidence, and anything the packet
  report lists as outside the sources.

## Planning observations

These are leanings formed while preparing the plan. The agent may discard any
of them. They are not decisions.

- **The lead question is really about self-widening.** In the engines, a
  sandboxed process issues because Apple framework code inside it hands tokens to
  a helper. A worker that issues and consumes its own token asks whether an
  issuance allowance plus a consumer-side filter lets a process widen its own
  sandbox. Stating Q1 and Q3 that way sharpens the policy-authoring lesson and
  suggests the controls, but it also moves issuance authority into the worker,
  which rewrites the authority section of WORKER.md.
- **The cheapest home for Q1 is the native fixture.** The production worker has
  no issue action, and admission refuses caller-selected classes, so a product
  path to Q1 is a request-grammar change before any observation.
- **Two tiers of rigor.** Pilots under `.tmp/` with a recorded report, and
  promotion to opt-in suite cases with constructed checker controls only for
  observations worth retaining. The stance against tolerated flakes applies to
  both tiers; the tiering is about checker construction, not about accepting
  unstable results.
- **Binding is a design pressure as much as an experiment.** Today the issuer is
  reaped before the worker exists and the worker validates the channel before
  apply. A bound token needs the worker first, so issuance moves inside the
  worker's lifetime, the channel fills late, and validation moves or waits. Q15
  is the question to settle first. The confinement gain is defense in depth and
  does not retire erasure, because a bound token is live while the worker is.
- **Two sentinels disagree.** Chromium treats a zero consume result as failure;
  WebKit and PolicyWitness treat only `-1` so. Q5 is cheap and settles which
  reading this host supports.
- **WebKit's flag naming is inverted.** Its do-not-canonicalize option sets the
  constant named canonical. Read the code, not the name, when designing Q9 and
  Q10.
- **A well-formed experiment** under this plan cites a trace, answers or adds a
  listed question, respects the boundary section, records host facts, keeps
  tokens out of evidence, and names where its outcome could land. That is the
  check the maintainer and agent apply when they talk about results.
