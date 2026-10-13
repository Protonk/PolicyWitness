# Interruption hooks and diagnostic-host investigation

Recorded 2026-10-13 after human review of the sandbox-extension design, against
source `772d06b652d9e38f36775cd65900653b24cb5ca2`.

Status: deferred investigation. The user agreed to retain the current design
and requested this standalone outflow note. This is not an implementation plan,
a new acceptance gate, or a commitment to replace the existing hooks. No new
diagnostic build, debugger attachment, injection experiment, or entitlement
change was performed during the discussion. This note has no inbound link from
the sandbox-extensions plan, as requested.

## Question to return to

Can a separately signed diagnostic XPC host improve deterministic failure
coverage while preserving the exact worker executable and entitlements? Which
worker-local interruption claims, if any, would benefit from a separate
debugger-based experiment? Evaluate those questions independently. More invasive
instrumentation should earn its complexity through a specific additional
observation or discriminating control.

## What the current hooks establish

The worker's
[`attempt_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
contains two `PW_EXTENSION_OBSERVE` locations: after publishing the pre-call
marker, and after the native call returns and errno is saved but before its
result payload is written. The production macro expands to a no-op; there is
no runtime callback or request option enabling these hooks in the shipped worker.

The [fixture](../tests/fixtures/extension_controls/control.c) includes the
production C source and supplies an observer which records its intervention in
separate transient shared memory, then kills the worker at the selected point.
It also substitutes the native entrypoints. Its middle interruption occurs
inside the replacement function, before that function calls the real native API.
It does not observe execution inside Apple's implementation or the kernel.

The [checker](../tests/suites/witness_contract/check_extension_boundaries.py)
requires the selected observation receipt, worker death/reap, an unpublished
result, and an unresolved event without native return or errno. Earlier completed
observations must survive. The particularly useful distinction is that the test
can know a real native call returned while PW must still withhold its result:
the result was never published to PW's evidence channel.

These controls compile a separate clang `-O2` executable. Shared production
source prevents a second handwritten implementation, but does not establish
equivalence to the shipped executable's instructions, timing, resource use or
security configuration. The [fixture account](../tests/fixtures/extension_controls/README.md)
states that limit. Ordinary signed CLI controls separately establish native
results and fresh access observations.

Revisit whether the middle, replacement-function interruption detects a defect
that the pre-call control would miss. Do not assume three intervention positions
correspond to three independently established native effects. Also examine
whether observation code changes ordering or publication behavior relevant to
the asserted property. This is a fidelity question, not a demonstrated defect in
the current result handling.

## Route A: diagnostic host with an unchanged worker

Compile selected controls into a separate XPC host, with its own identifiable
build and test-only coordination channel. Code compiled into the host generally
needs no debugging entitlement merely to execute its own instrumentation.
Debugger attachment to that host is a separate choice.

Candidate responsibilities include externally coordinated pauses around phase
release, snapshots of publications the host has actually observed, and controlled
failure around collection, cleanup or reply construction. Host death at a known
boundary could be driven by an independent test process. These are possible
experiments, not claims that current coverage lacks them.

First inventory existing tests and the narrow internal seams in
[CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `phaseBoundary`,
`phaseReleaseOrdinal`, and `ChildProcessCalls`. The latter substitutes wait/kill
calls for driver tests; a simulated syscall failure must remain distinguishable
from an observed real kernel failure. Prefer making an existing seam usable for
one justified experiment over building a general fault-injection framework.

This route can preserve the worker's compiled bytes and signed entitlements
while changing the host's orchestration. It still changes scheduling and the
host under test, so it does not establish an unmodified whole-system run.
Observation receipts must remain separate from the product reply. A debug
control must not manufacture a normalized outcome or erase conflicting facts.

Host observations alone cannot identify the exact interval after a worker's
native return but before result publication. Polling a pre-call marker cannot
establish that the call has entered or returned. This route complements the
worker hooks rather than automatically replacing them.

## Route B: precise interruption of a debug-eligible worker

Investigate debugger attachment only for a concrete worker-local question left
unanswered by Route A and the existing controls. A worker signed to permit
debugging could potentially retain its compiled instructions while changing its
signature and entitlements. Verify that distinction instead of calling it the
unchanged shipped worker. Breakpoints and debugger intervention also perturb
execution; user-space debugger eligibility does not establish visibility inside
kernel implementation paths.

A successful experiment would need to identify the actual stop location,
distinguish native return from result publication, record the intervention
independently, and show how the result strengthens a named evidence claim.
Attachment feasibility on the current macOS build has not been tested.

## macOS signing and debugging facts to recheck

Apple's documentation was consulted on 2026-10-13. Recheck these rules when the
investigation starts; documented capability is not evidence that attachment or
injection succeeded on the test machine.

| Mechanism | Relevant boundary |
| --- | --- |
| `com.apple.security.get-task-allow` | Target executable eligibility for debugging. Apply it to the executable being inspected, not indiscriminately to the enclosing app. |
| `com.apple.security.cs.debugger` | Authority of a debugging tool to request eligible targets' task ports. It does not itself overcome a protected target's lack of `get-task-allow`. |
| `com.apple.security.cs.allow-dyld-environment-variables` | Enables the target process to honor DYLD variables used for injection or changed loading behavior. Library validation remains a separate check. |
| `com.apple.security.cs.disable-library-validation` | Relaxes library-signing restrictions. It is not automatically required for a diagnostic library signed with the executable's own Team ID. |

Sources: Apple's [debugger entitlement](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.debugger),
[macOS provisioning rules](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles),
[DYLD exception](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-dyld-environment-variables),
and [library validation](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.disable-library-validation).
The ordinary debugging/hardened-runtime entitlements described here can be
claimed on macOS without special provisioning-profile authorization. Apple
documents an authorization prompt for non-root debugging tools; do not assume
unattended attachment. The new
[Enhanced Security capability](https://developer.apple.com/documentation/xcode/enabling-enhanced-security-for-your-app)
introduced with Xcode 26 supplies additional compiler/runtime protections and
should be inventoried separately from ordinary hardened-runtime signing.

In this repository, [build.sh](../build.sh) signs native helpers separately from
the XPC host. However, the current BYOXPC
[`sign_install_tree`](../controller/src/runner_manager.rs) applies supplied
entitlements to both the worker and host. Passing debug entitlements through
that ordinary installation route would therefore not preserve an unchanged
worker. A host-only experiment needs explicit per-executable signing and
read-back, plus its own bundle identity/provenance. Do not weaken the existing
installer's contract to make a diagnostic fixture convenient.

Dynamic injection is a possible third technique, but explicit compiled host
controls are initially preferable for code we own: placement and responsibility
are easier to review. Neither technique on the host confers debugger access to
the separately signed worker.

## Suggested bounded investigation and decision

1. Map existing controls to their intervention, independently observed facts,
   withheld claims and known limits. Select one uncovered question before adding
   machinery; include the possible redundancy of the middle interruption case.
2. Try the smallest host-only experiment first. Record source/build identity,
   exact signatures/entitlements, and worker byte identity. Keep accepted and
   distributed artifacts separate from diagnostic fixtures.
3. If a worker-local gap remains, test attachment with the minimum target/tool
   entitlements and record actual OS/toolchain behavior and any authorization
   needed. Preserve SIP and distinguish unsuccessful attachment from a product
   result; do not assume additional authority is available.
4. Check independent receipts, effects and cleanup. Preserve token confinement:
   extra observation channels or debugger captures must not put raw token bytes
   in retained artifacts. Retain exact resource ownership when cleanup is unknown.
5. Decide whether to retain, supplement or remove each hook based on the added
   discriminating evidence. Verify that distributed builds have no active
   diagnostic controls or unintended debug entitlements. If the proposed route
   adds no useful coverage, record that result and retain the bounded current
   design without further framework work.

The accepted decision today is to retain the current hooks and their qualified
claims. No stronger interruption, shipped-binary equivalence, native API interior,
or policy-effect claim follows from this note.
