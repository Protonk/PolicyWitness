# Integrated incident report: `inherit_child` `dynamic_extension` crash (and the inheritance + monitoring model it touches)
 
This document is a **self-contained, hermetic** maintainer report that merges and reconciles:

- `troubles/inherit_child/sandbox_impl.md` (durable mental model + contract/monitoring surfaces), and
- `troubles/inherit_child/inherit_child_crash.md` (detailed debugging journey + why it was hard), and
- `troubles/inherit_child/synthetic_re_report.md` (security/RE framing, evidence chain, and failure taxonomy).
 
It is written so a reader can understand the problem and fix **without repo access**, but it also includes **repo-relative file pointers** so maintainers can jump straight to the relevant code if they do have the repo.
 
## Executive summary
 
- **Symptom:** the smoke fixture for `inherit_child --scenario dynamic_extension` failed as `normalized_outcome="xpc_error"` with “connection interrupted/invalidated” (often `NSCocoaErrorDomain Code=4097`). In some environments it instead failed earlier with `failed at lookup with error 159 - Sandbox restriction` (often `Code=4099`).
- **Root cause:** the XPC service process for the `temporary_exception` profile was **crashing with a stack guard fault**. The immediate trigger was a “**probe calls probe**” nesting inside the service worker thread:
  - `inherit_child` (already large) called the large `sandbox_extension` probe implementation as a helper.
  - On a constrained XPC worker stack, the additional call depth + large local frames pushed execution into stack exhaustion, and the crash surfaced at seemingly innocuous Swift string/path routines.
- **Fix:** remove the nested call. In `xpc/InProcessProbeCore.swift`, `inherit_child.dynamic_extension` now issues/consumes sandbox extension tokens by calling the minimum required `sandbox_extension_*` SPI entrypoints directly, rather than routing through `probeSandboxExtension(...)`.
- **Related instrumentation hardening:** signposts are **optional and off-by-default**, but signpost capture tooling was improved to handle `/usr/bin/log show --style json` returning a **JSON array**; and the `inherit_child` smoke fixture was hardened to always emit a high-signal failure summary so future regressions are immediately attributable.
- **Validation:** `bash tests/suites/smoke/inherit_child_fixtures.sh` passes, and `./tests/run.sh --all` passes when executed in an environment that permits XPC launch and reading unified logs.
 
## Background: inheritance model and why `inherit_child` exists
 
PolicyWitness’s architecture is deliberately opinionated:
 
- The host CLI (`PolicyWitness.app/Contents/MacOS/policy-witness`, built from `runner/`) is **host-side and unsandboxed** by default (unless the caller itself is sandboxed by a harness such as `sandbox-exec`).
- The sandbox boundary is the chosen XPC service under `PolicyWitness.app/Contents/XPCServices/*.xpc` (built from `xpc/services/*`), and “entitlements as a variable” is expressed by selecting a different service/profile.
 
That architecture creates a common conceptual trap:

- People say “the child inherits entitlements,” but PolicyWitness’s stance is that meaningful entitlement differences are expressed by **service selection**, not by hoping entitlements “pass” across an exec boundary.

From a security/internals perspective, the trust boundary is explicit: the host CLI is a control plane and should be read as **channel health + transcript**, the XPC service is the **enforcement context**, the child helper is a **separate principal**, and observers (`sandbox-log-observer`, `signpost-log-observer`) are **external evidence gatherers**. No single surface is authoritative by itself: host JSON tells you what the tool thinks it did, unified-log denies tell you what the sandbox denied, crash reports tell you what died, and protocol/witness invariants tell you when the harness itself broke.

PolicyWitness’s identity model also matters here: it is many separately signed service bundles (profiles), not “one binary with flags.” Entitlements are part of the specimen and should be verified alongside evidence manifests before treating results as meaningful. Variants (such as `@injectable`) deliberately change risk posture by enabling debug/injection entitlements; temporary exception profiles are a separate concern tier for sandbox extension issuance. In practice, the early checks are: verify evidence/signing consistency, confirm which service principal actually ran (profile + variant + PID), and treat the `temporary_exception` class as high concern by default.

`inherit_child` exists to make inheritance *observable and discriminable* across processes. It’s not “just another probe”; it’s a **frozen inspection substrate** whose main job is to distinguish:
 
- “child never ran user code” (diagnostic: early abort),
- “protocol or harness broke” (explicit harness outcomes),
- “permission-shaped failure” (EPERM/EACCES; may or may not be sandbox),
- “expected abort canary fired” (`inherit_bad_entitlements`),
- “capability transfer succeeded even when independent acquisition failed” (the interesting boundary).
 
Key insight used throughout:
 
- **Static identity controls** (service entitlements, signing identity, bundle selection) define the sandbox regime.
- **Dynamic capabilities** (FDs, sandbox extensions, bookmarks) define what access can be exercised at runtime.
- The “inheritance” question you can actually test is:
  **Which parts of the parent’s effective access survive an exec boundary, and which require explicit ferrying?**
 
This incident touched that substrate because `dynamic_extension` is a dynamic-capability scenario and because the crash was caused by reusing the general sandbox-extension probe inside `inherit_child` rather than keeping the substrate self-contained.

## Contracts and protocol surfaces

`inherit_child` is a frozen substrate. These surfaces are contract boundaries that should remain stable unless there is a deliberate protocol bump and fixture update:

- Wire framing: two-bus protocol (event bus JSONL + sentinel + payload bytes; rights bus `SCM_RIGHTS` only). The sentinel records bus FDs early, and "no child events" is a diagnostic for early child death. Never pass FDs over the event bus. See `xpc/ProbeAPI.swift` (`InheritChildProtocol`) and `xpc/child/main.swift`.
- Witness schema: `InheritChildWitness` in `xpc/ProbeAPI.swift`; fixtures in `tests/fixtures/inherit_child/*.json` and the scrubber `tests/tools/scrub_inherit_child_witness.py` lock the shape.
- Scenario catalog and names: `inheritChildScenarioCatalog` in `xpc/InProcessProbeCore.swift`. Fixtures and smoke tests depend on the names.
- Entitlement contract: the child helper must be app-sandbox + inherit only; the witness exposes `inherit_contract_ok`. The `inherit_bad_entitlements` scenario (using `pw-inherit-child-bad`) is the canary that the OS still aborts a mis-entitled child as expected, and `tests/build-evidence.py` guards the entitlements across embedded helper copies.

The capability ferry model is the point of the substrate: parent acquire, child acquire, and child use are recorded as distinct phases so "inheritance" becomes a testable delta rather than a philosophical argument. FDs travel only on the rights bus, bookmarks travel on the event bus payload path, and the witness consolidates these into `capability_results` plus an `outcome_summary`. For reverse engineering work, this provides stable hook points (spawn markers, capability handoff boundaries, and explicit phase labels) without needing to infer intent from syscall traces alone.

If you change framing or witness fields, update both parent and child together, bump protocol version where applicable, and update fixtures.

## Repo map
 
**Service-side probe implementation**
 
- `xpc/InProcessProbeCore.swift`
  - `probeInheritChild(...)` (the `inherit_child` probe implementation)
  - `probeSandboxExtension(...)` (the general-purpose `sandbox_extension` probe)
  - supporting helpers like path/target resolution (`resolveFsTarget(...)`) that appeared in crash frames
 
**XPC client and session wiring**

- `xpc/client/main.swift` (embedded `xpc-probe-client`; opens sessions and runs probes)
- `xpc/ProbeServiceSessionHost.swift` (service session host)
- `xpc/ProbeAPI.swift` (JSON-over-Data wire types)

**Child helper**

- `xpc/child/main.swift` (child helper implementation; two-bus protocol and capability actions)

**Observability + capture**
 
- `xpc/Signposts.swift` (signpost gating + correlation context)
- `runner/src/bin/signpost-log-observer.rs` (unified log signpost capture)
- `runner/src/bin/sandbox-log-observer.rs` (unified log sandbox deny capture)
- `runner/src/main.rs` (CLI flags and attachment injection)
 
**Tests**

- `tests/suites/smoke/inherit_child_fixtures.sh` (fixture runner; scrub+compare against `tests/fixtures/inherit_child/*.json`)
- `tests/suites/smoke/xpc_app_smoke.sh` (app-level smoke checks; includes capture tests)
- `tests/fixtures/inherit_child/*.json` (canonical fixture outputs)
- `tests/tools/scrub_inherit_child_witness.py` (scrubs volatile fields before comparison)

Evidence and profile manifests live under `PolicyWitness.app/Contents/Resources/Evidence/` and are generated by `tests/build-evidence.py`. Risk signals (such as “high concern” for `@injectable` or temporary exception profiles) are derived from those entitlements, not hand-maintained, and should be treated as part of the specimen’s identity.

## Symptoms and reproduction
 
### Minimal reproduction (what the fixture runs)
 
The smoke fixture effectively runs this (arguments vary slightly depending on fixture):
 
```bash
PolicyWitness.app/Contents/MacOS/policy-witness \
  xpc run --profile temporary_exception \
  inherit_child --scenario dynamic_extension \
  --path-class tmp --target specimen_file --name pw_fixture_dynamic.txt --create
```
 
Expected (healthy) outcome: a normal `kind="probe_response"` JSON with `result.ok=true`, plus a structured witness under `data.witness`.

Note: the fixture uses the `temporary_exception` profile because `dynamic_extension` exercises sandbox extension operations that are only wired for that profile in this repo's fixture matrix.
 
Pre-fix observed outcomes:
 
1) **Unsandboxed environment (service can launch):** `normalized_outcome="xpc_error"` with an error like:
   - `NSCocoaErrorDomain Code=4097 ... connection to service ... interrupted`
2) **Sandboxed caller environment (service lookup blocked):** `normalized_outcome="xpc_error"` with an error like:
   - `NSCocoaErrorDomain Code=4099 ... failed at lookup with error 159 - Sandbox restriction`
 
These are not the same problem:
 
- The `159`/lookup failure is an **environmental harness gate**: the caller is not allowed to `mach-lookup` the XPC service name, so probe execution never begins.
- The `4097` interruption is a **real service failure**: the service started but died mid-run (crash/kill/etc.).
 
### Why it initially looked intermittent
 
The failure was described as intermittent because the first visible symptom was a generic NSXPC error, and two different execution contexts produced two different error codes. Once the fixture runner was hardened to always emit a structured failure summary, it became clear that:
 
- the lookup failure is deterministic given the caller sandbox constraints (for example, a `sandbox-exec` profile denying `mach-lookup` for the service name), and
- the `4097` path correlates with a real crash that is reproducible when the service launches.
 
## Investigation
 
### Improve failure attribution in the smoke fixture
 
`tests/run.sh` determines overall status by scanning for `tests/out/suites/*/*/report.json`. A failure that exits early (before writing a report) can be confusing: the console may show "mostly passes," but the suite returns non-zero.

The `inherit_child` fixture runner (`tests/suites/smoke/inherit_child_fixtures.sh`) was updated to trap failures and always route through `test_fail`, emitting a compact, high-signal JSON summary and ensuring `tests/out/run.json` reflects the failure. This was critical because it turned "XPC interrupted" from a vague symptom into a reliably recorded failure with enough context to classify.
 
### Separate harness gate from service crash
 
Once the fixture output was reliable, the next step was to isolate the unsandboxed crash path. The `4099`/`159` path was recognized as an expected consequence of a sandboxed caller environment that denies `mach-lookup` for the service name.
 
With XPC lookup allowed (unsandboxed caller), the error consistently became `4097` ("connection interrupted"), which strongly suggested "service crashed." At that point the correct move was: **trust crash reports over host symptoms**.
 
### Collect crash reports and extract faulting frames
 
Crash reports for the service live under:
 
```text
/Users/username/Library/Logs/DiagnosticReports/
  ProbeService_temporary_exception-*.ips
```
 
`.ips` reports are JSON. A reliable parsing approach is:
 
```python
first_line, rest = open(path).read().split("\n", 1)
meta = json.loads(first_line)
main = json.loads(rest)
frames = main["threads"][main["faultingThread"]]["frames"]
```
 
The reports consistently showed a stack-guard style fault (SIGBUS / protection failure near the stack guard) on a dispatch workloop worker thread.
 
The extracted call chain implicated a nested probe invocation:
 
```text
InProcessProbeCore.probeInheritChild(...)
  issueToken helper
    InProcessProbeCore.probeSandboxExtension(argv:)
      InProcessProbeCore.resolveFsTarget(...)
      ...
_dispatch_workloop_worker_thread
```
 
The key inference (high confidence, based on crash signatures and frames):
 
- This was not a semantic sandbox denial; it was **resource exhaustion** (stack exhaustion) triggered by nesting two large probe implementations on an XPC worker stack.
 
## Root cause: why `dynamic_extension` crashed
 
### Scenario intent
 
From the substrate model (`troubles/inherit_child/sandbox_impl.md`):
 
- `dynamic_extension` is a scenario whose purpose is to make “dynamic grant vs capability possession” observable.
- The parent obtains a dynamic permission token (sandbox extension), uses it to acquire access, then ferries a capability (often an FD) to the child.
- The child’s behavior is separated into:
  - child acquire (can the child independently acquire?),
  - child use (can the child use a ferried capability even if it can’t acquire?).
 
This keeps “inheritance” grounded in measurable phases rather than hand-wavy claims.
 
### Implementation failure: the "probe calls probe" anti-pattern
 
The pre-fix implementation reused logic by calling the general sandbox-extension probe (`probeSandboxExtension`) from inside `probeInheritChild` to issue/consume tokens.
 
That was the critical defect. In practice:
 
- `probeInheritChild` is already a large function (spawn choreography, event bus + rights bus coordination, witness building).
- `probeSandboxExtension` is also large (argument parsing, path validation, multiple operations, more locals).
 
On macOS, XPC service workloop threads often have smaller stacks than main threads. Nesting large probe code on those threads can cause stack exhaustion in Swift, which then surfaces as a SIGBUS/guard fault at some leaf routine (often string/path code) rather than an obvious recursion. The crash frames pointing at `resolveFsTarget` and Swift string internals are therefore symptom-level, not the underlying cause.
 
This is exactly the maintainer guidance captured in `troubles/inherit_child/sandbox_impl.md`: **avoid “probe calls probe” patterns inside the service**. Extract small helpers if you want reuse; do not nest whole probe implementations.
 
## Fix (preserves the substrate contract)
 
The fix was intentionally surgical and contract-preserving:
 
- Remove the nested `probeSandboxExtension` invocation from `inherit_child.dynamic_extension`.
- Inline only the minimal sandbox-extension SPI calls needed for the scenario:
  - issue a file token (`sandbox_extension_issue_file`),
  - consume the token (`sandbox_extension_consume`),
  - free token where applicable (`sandbox_extension_free` if available),
  - record the same witness fields/events so fixtures remain stable.
 
This reduces call depth and stack usage dramatically, while keeping:
 
- scenario naming stable,
- the two-bus protocol untouched,
- the witness schema stable (fixtures continue to scrub+compare).
 
Primary code location: `xpc/InProcessProbeCore.swift`. No wire protocol changes were required, scenario names remained stable, and the witness schema remained unchanged (fixtures did not need to be regenerated; only the smoke fixture reporting path changed).
 
## Instrumentation hardening alongside the fix
 
These changes are adjacent but important because they improved diagnosis and reduced the chance of recurrence being mis-attributed.
 
### Signposts (optional, off-by-default)
 
Signposts remain:

- **off-by-default**,
- enabled only via explicit flags (`--signposts` / `--capture-signposts`),
- best-effort (capture may be unavailable depending on unified log access).

When enabled, the launcher sets `PW_ENABLE_SIGNPOSTS=1`, Swift checks `PWSignposts.isEnabled()`, and correlation context flows via `correlation_id` (propagated to the child as `PW_CORRELATION_ID`). `--capture-signposts` attaches a `data.host_signpost_capture` record to the probe response.

The signpost observer shells out to `/usr/bin/log show --signpost --style json`, filters by subsystem and `eventMessage CONTAINS "pw_corr=<id>"`, and captures a bounded slice of unified log output (truncation is recorded explicitly). This makes the capture usable for ordering and timing without treating it as exhaustive forensic evidence.

Key code surfaces:
 
- `xpc/Signposts.swift` for gating + correlation propagation.
- `runner/src/bin/signpost-log-observer.rs` for host-side capture.
 
### Signpost capture robustness for `/usr/bin/log show --style json`
 
Unified logging output shape is not stable across “formats”:
 
- `/usr/bin/log show --style json` returns a **JSON array** (not JSONL).
 
The signpost observer now accepts both:
 
- JSON array (whole stdout parses as an array), and
- JSONL (one record per line).
 
This is locked in with a unit test in `runner/src/bin/signpost-log-observer.rs`.
 
### Smoke failures are self-reporting
 
`tests/suites/smoke/inherit_child_fixtures.sh` was improved to always produce a high-signal `report.json` and summary on failure. This matters because the tool’s epistemics depend on distinguishing:
 
- “probe outcome” vs
- “XPC boundary failed” vs
- “harness broke” vs
- “child died before writing.”
 
When tests fail without a report, it pushes maintainers back into guesswork.
 
## Monitoring and attribution (what PolicyWitness can and cannot prove)
 
From `troubles/inherit_child/sandbox_impl.md`, the discipline is to assume in-sandbox signals collapse into EPERM/EACCES or process death, and to attach evidence **outside** the boundary into the same JSON artifact so absence/presence is interpretable.

PolicyWitness treats the probe JSON as a **witness transcript**, not a complete attribution record. The witness is authoritative for what the tool attempted and observed in-band (rc, errno, per-phase outcomes), but attribution claims require out-of-band evidence. Concretely: EPERM/EACCES is necessary for "permission-shaped failure" but not sufficient for "sandbox denied"; a host-side XPC error is a transport symptom, not proof of a policy decision; and service crashes are only provable with crash reports (or explicit service-side lifecycle evidence).

A concise admissibility map helps keep conclusions honest:

- **Claim: "EPERM/EACCES observed."** Required: in-band witness record. This is permission-shaped only, not a deny claim.
- **Claim: "Sandbox denied."** Required: a matching unified-log deny line for the correct PID/time window.
- **Claim: "Service crashed."** Required: a crash report (`.ips`) for the service principal, not just an XPC interruption.
- **Claim: "Harness/protocol bug."** Required: explicit normalized outcomes (protocol violation/bus errors) or missing sentinel/events.

Signposts and sandbox log capture are intentionally additive. Signposts help build a time-ordered narrative (what ran, when it blocked, and which phase took time), but absence of signposts is not proof of absence unless you can establish signposts were enabled for that principal. Sandbox deny capture is the canonical source for "Seatbelt denied" attribution and should be treated as PID- and time-bounded evidence rather than a global signal.

If you need a hermetic incident record, collect a minimal artifact bundle: crash reports (`.ips`) for the service, sandbox deny lines (captured with `--capture-sandbox-logs` or `sandbox-log-observer`), signpost traces (if enabled), and the fixture JSON/report outputs. Correlate by service PID/process name, timestamps, and the `pw_corr` correlation id when available.

### Sandbox deny evidence (`sandbox-log-observer`)

Host-side observer runs `/usr/bin/log` with a sandbox predicate and requires a PID (ideally a process name).

Captures must remain PID-scoped and time-bounded to avoid mis-attribution and unintended exfiltration. The tri-state capture status keeps absence interpretable.

When requested, captures are attached under `data.host_sandbox_log_capture` (launcher-side attachment).
 
For `inherit_child`, the witness also summarizes capture state under `data.witness.sandbox_log_capture_status` (`not_requested|requested_unavailable|captured`) and `data.witness.sandbox_log_capture` (string map for stable fixtures).
 
`requested_unavailable` means capture was requested but could not be completed (for example, no PID was available or the observer failed); it is not a deny signal by itself.

In practice, the most reliable capture path is to run with `--capture-sandbox-logs` so the observer output is attached to the same JSON artifact and time-bounded around the probe run. If you must run it out-of-band, extract `service_pid` and `process_name` from the probe response and use those to scope the observer; otherwise you risk attributing denies from an unrelated principal or time window.

### Failure taxonomy to preserve
 
`inherit_child` already encodes (and maintainers should preserve) a taxonomy that prevents mis-attribution. The practical classifier is: **launch vs runtime**, and **policy-shaped vs liveness-shaped**. In that framing:

- **XPC boundary failures** (`normalized_outcome="xpc_error"`) describe transport health, not policy. Lookup/launch errors (often `Code=4099` / `xpc_error=159`) mean the service never ran; interruption errors (often `Code=4097`) mean the service launched and then died or dropped the connection.
- **Harness failures** are explicit and should remain explicit (protocol violations, bus I/O errors, missing sentinel, or no child events). These are substrate correctness failures, not sandbox outcomes.
- **Expected abort canaries** (`inherit_bad_entitlements`) are “success” for that scenario. Treating them as generic failure would remove a critical guardrail that the inheritance contract is still enforced by the OS.
- **Permission-shaped failures** (EPERM/EACCES) are ambiguous without phase/callsite/evidence attachments. They are necessary for “permission-shaped failure” but not sufficient for “sandbox denied.” Return codes from private SPI are not evidence; access-delta checks are the ground truth.
 
This incident is an example of why that taxonomy matters: the host symptom (“connection interrupted”) is not the root cause.
 
## Why this was hard
 
This is the distilled "why hard" list from `troubles/inherit_child/inherit_child_crash.md`:

- **NSXPC error codes are ambiguous.** "Connection interrupted" can mean crash, kill, denial, or launch issues.
- **Environment injected a confounder.** A sandboxed caller can deterministically fail at XPC lookup (error 159), which looks superficially similar to "the probe failed."
- **Test runner visibility matters.** When a failing script exits without writing a report, it increases uncertainty and slows diagnosis.
- **Multi-process + multi-language.** Rust launcher -> Swift client -> Swift service -> child helper makes "where did it die?" non-trivial without structured evidence.
- **Stack exhaustion in Swift can look like unrelated code.** The crash point was in string/path validation, but the cause was already-exhausted stack due to nested large probe implementations.
 
## Prevention: maintainer rules reinforced by this incident

This incident reinforces the guardrails in `troubles/inherit_child/sandbox_impl.md` and turns them into concrete review habits. Keep `inherit_child` self-contained; avoid nesting whole probe implementations inside service execution and keep private SPI interactions shallow enough for service-thread stacks. Treat protocol framing, witness schema, and scenario semantics as contract surfaces; fixture updates are a design-review gate and should preserve explicit protocol-violation outcomes. Keep monitoring attachments interpretable with tri-state capture status and bounded scopes so absence is meaningful.

From a security-review perspective, the same incident reaffirms a few invariants. Execution surfaces stay constrained (identifier-dispatched probes; no arbitrary path exec; `run-system` and `run-embedded` are limited to allowed paths). Risk signals stay derived from entitlements, not hand-maintained labels. Attribution remains evidence-backed rather than return-code-backed: private sandbox extension SPI varies across OS releases, so success is defined by access-delta observations, not `rc==0`. Token formatting options and call-variant hooks should remain documented and stable so debugging can pin an ABI path when needed.

A short review checklist that aligns with those principles:

- Keep capture scopes PID/correlation-bound; record truncation and `requested_unavailable`.
- Preserve protocol fail-closed behavior (cap-id validation, version checks, sentinel requirements).
- Ensure tests emit artifacts and summaries even on non-zero exits.
 
## Operator checklist

When you see `normalized_outcome="xpc_error"`, treat it as transport health first, not policy. Classify the error and collect evidence before drawing conclusions:

- **Classify lookup/launch vs interruption.** Lookup/launch errors (often `Code=4099` / `xpc_error=159`) suggest a harness gate; interruption (`Code=4097`) suggests the service died after launch.
- **If interruption:** go to crash reports under `/Users/username/Library/Logs/DiagnosticReports/` and search for the service principal; correlate by PID/time and any `pw_corr` signpost tags.
- **If permission-shaped failures show up later:** require a matching sandbox deny line for the service PID/time window before claiming "sandbox denied."
- **Verify identity early:** confirm the profile + variant actually ran (service principal, entitlements, and evidence manifests) and treat `temporary_exception` profiles as high concern.
- **Collect an artifact bundle:** crash report, sandbox deny capture (prefer `--capture-sandbox-logs`), signposts if enabled, and the fixture report JSON so the failure is preserved even on non-zero exit.
- **If the fault looks stack-like:** search for "probe calls probe" or large nested helpers in `xpc/InProcessProbeCore.swift`, and keep the fix local to the probe rather than nesting another probe.
 
