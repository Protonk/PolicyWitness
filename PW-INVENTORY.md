# PolicyWitness Inventory (evidence-first)

**Status:** This inventory was written for the legacy profile/variant-based design. PolicyWitness is now specimen-first (single `PWRunner.xpc` runner applying SBPL/compiled bytes per run), so treat the contents below as historical context until this document is rewritten.

This document is a lab-notebook style inventory: it records what PolicyWitness
actually did on this machine, and the concrete artifacts that support each
claim. It is deliberately “evidence-first”: when something is unproven, it is
marked explicitly and a closure path is listed in the "Next closure set"
section.

A key context for interpreting results here is that the *same* PolicyWitness
binary behaves differently depending on whether it is launched from inside a
sandboxed automation harness (where some OS services are blocked) or outside it.
This inventory therefore includes two runs:

- **Run A:** inside a sandboxed harness (non-escalated) — XPC lookup and some
  evidence collection paths are blocked.
- **Run B:** outside that harness (escalated) — XPC services launch, sessions are
  durable, and probes produce witnesses.

## Summary (for skimming)

- **Profile/variant selection is concrete and inspectable:** `--profile`/`--variant`
  selects an XPC service by bundle id from `profiles.json` (runtime source of truth).
- **Harness sandboxing can block the experiment before it starts:** Run A fails at
  XPC lookup with `error 159 - Sandbox restriction`; no probe code runs.
- **Evidence pipelines can also be blocked:** in Run A, sandbox-log capture fails
  with `log: Cannot run while sandboxed`, so “no denies observed” is not a safe
  conclusion.
- **Outside the harness, the model works end-to-end:** Run B opens XPC services,
  keeps a stable service PID within a session, and emits witness payloads (e.g.
  `inherit_child`).
- **Injectable variants have an observable effect:** `dlopen_external` succeeds
  only in injectable and runs the dylib constructor marker; base fails on library
  validation (not a sandbox deny).

## Reader’s guide

- **“Observed”** means “backed by an artifact excerpted below.”
- **`normalized_outcome`** is PolicyWitness’s coarse classification (e.g. `ok`,
  `xpc_error`, `dlopen_failed`).
- **`layer_attribution`** identifies where a failure happened (e.g.
  `xpc:openSession_failed` means the probe never ran).
- **Evidence attachments** like `host_sandbox_log_capture` are best-effort; this
  inventory treats capture failures as first-class outcomes, not as absence of denies.

## Run capsules

These are the minimal “capsules” needed to reproduce and interpret the observed
behavior: environment, commands, and the resulting artifacts.

Artifacts referenced in this report were saved under:

- `.tmp/pw_inventory_sandboxed/` (Run A)
- `.tmp/pw_inventory_escalated/` (Run B)

### Run A: sandboxed harness (non-escalated)

- CWD: `/Users/achyland/Desktop/PolicyWitness`
- Runner: `PolicyWitness.app/Contents/MacOS/policy-witness`
- OS: macOS 14.4.1 (23E224), kernel 23.4.0 (arm64)
- SIP: enabled (`csrutil status`)
- Env highlights: `TERM=xterm-256color`, `CODEX_SANDBOX=seatbelt`, no `PW_*` env vars set
- Quarantine: no `com.apple.quarantine` xattr on `PolicyWitness.app`

Commands and observed outcomes:

```
$ RUST_LOG=debug PolicyWitness.app/Contents/MacOS/policy-witness xpc run --profile minimal world_shape
... "xpc_error_domain":"NSCocoaErrorDomain" ...
... "xpc_error_code":"4099" ...
... "failed at lookup with error 159 - Sandbox restriction."
... "layer_attribution":{"other":"xpc:openSession_failed"} ...
```

Raw OS evidence for the boundary (launchd denied lookup, error 159):

```
2026-01-11 20:10:50.260785-0800  localhost launchd[1]: [pid/95444 [xpc-probe-clien]:] denied lookup: name = com.yourteam.policy-witness.ProbeService_minimal, requestor = xpc-probe-clien[95444], error = 159: Sandbox restriction
```

Same requestor PID also fails to look up `com.apple.logd`, which explains why
log-based evidence capture can be blocked in this environment:

```
2026-01-11 20:10:50.261306-0800  localhost launchd[1]: [gui/501 [100016]:] denied lookup: name = com.apple.logd, flags = 0x9, requestor = xpc-probe-clien[95444], error = 159: Sandbox restriction
```

```
$ PolicyWitness.app/Contents/MacOS/policy-witness xpc run --capture-sandbox-logs --capture-sandbox-logs-target client --profile minimal world_shape
... "host_sandbox_log_capture":{"capture_status":"captured", ...} ...
... "observer_report":{"data":{"log_error":"log show returned non-zero","log_stderr":"log: Cannot run while sandboxed", ...}} ...
... "normalized_outcome":"xpc_error" ...
```

Interpretation: a sandbox boundary is hit at the caller (XPC lookup fails with 159),
and the deny-evidence collector itself is blocked (`log: Cannot run while sandboxed`).
This means Run A is decisive about “connection-stage policy,” but cannot by itself
establish anything about probe behavior inside the service.
Practically, the denied lookup is performed by the embedded Swift client helper
(`xpc-probe-client`), which is the direct “requestor” in the launchd deny line.

### Run B: escalated (outside the harness sandbox)

Escalated commands ran the same binaries and inputs from the same CWD.
This run succeeded in opening XPC services and produced probe witnesses.

Operational definition (host harness, not a PolicyWitness feature):

- Run A environment had `CODEX_SANDBOX=seatbelt`; Run B did not.
- In Run A, basic process inspection (`ps`) was denied (`operation not permitted`);
  in Run B it worked normally.
- In Run B, `/usr/bin/log show` was usable for evidence capture (whereas in Run A,
  the observer hit `log: Cannot run while sandboxed`).

Process context (from `ps` under escalation):

```
PID 60068 PPID 92106 /bin/zsh
PID 92106 PPID 92047 codex
```

Codesign entitlements:

```
$ codesign -d --entitlements - PolicyWitness.app/Contents/MacOS/policy-witness
[Dict]
```

```
$ codesign -d --entitlements - /bin/zsh
Executable=/bin/zsh
```

```
$ codesign -d --entitlements - /opt/homebrew/bin/codex
Executable=/opt/homebrew/Caskroom/codex/0.77.0/codex-aarch64-apple-darwin
```

Key probe results:

```
$ PolicyWitness.app/Contents/MacOS/policy-witness xpc run --profile minimal world_shape
... "result":{"ok":true,"normalized_outcome":"ok"} ...
... "service_bundle_id":"com.yourteam.policy-witness.ProbeService_minimal" ...
```

```
$ PolicyWitness.app/Contents/MacOS/policy-witness xpc run --capture-sandbox-logs --capture-sandbox-logs-target client --profile minimal world_shape
... "host_sandbox_log_capture":{"capture_status":"captured","observed_deny":null,"log_error":null,"pid_source":"client_pid"} ...
```

Session PID stability (single session, two probes):

```
service_pids: ["60139", "60139"]
probe world_shape ok True
probe probe_catalog ok True
```

Process tree (durable `xpc session`, sampled while the session was open):

```
PolicyWitness.app/Contents/MacOS/policy-witness xpc session --profile minimal
  └─ /Users/achyland/Desktop/PolicyWitness/PolicyWitness.app/Contents/MacOS/xpc-probe-client session com.yourteam.policy-witness.ProbeService_minimal
      └─ /Users/achyland/Desktop/PolicyWitness/PolicyWitness.app/Contents/XPCServices/ProbeService_minimal.xpc/Contents/MacOS/ProbeService_minimal
```

Child-process witness (inherit_child dynamic_extension):

```
result.ok: true
data.witness.capability_results: cap_id ["file_fd"]
data.witness.events: len 14
child_event_fd + child_rights_fd present
```

Deliberate deny capture (to validate `--capture-sandbox-logs` correlation and targeting):

- Probe: `fs_op --op open_read --path /private/var/db/launchd.db/com.apple.launchd/overrides.plist --allow-unsafe-path`
- Result: `normalized_outcome: permission_error`
- Capture targeting:
  - `--capture-sandbox-logs-target client` → `observed_deny: false`
  - `--capture-sandbox-logs-target service` (and `auto`) → `observed_deny: true`
    with a concrete deny line like:

```
Sandbox: ProbeService_minimal(18612) deny(1) file-read-data /private/var/db/launchd.db/com.apple.launchd/overrides.plist
```

QuarantineLab sample (default profile, text payload):

```
kind: quarantine_response
result.normalized_outcome: wrote_new
data.quarantine_xattr_present: true
data.target_path: .../Containers/com.yourteam.policy-witness.QuarantineLab_default/.../pw_inventory_q15.txt
```

## 1. Unit of policy that matters

This section answers: when you pick a profile/variant, *what concrete policy unit
is actually being selected*, and where do failures get attributed when the system
doesn’t reach probe code at all?

- **Observed:** policy selection is per XPC service **bundle id** (via `--profile`/`--variant`).
- **Observed:** probe execution happens inside a single service process; session runs keep a stable `service_pid`.
- **Observed failure boundary:** when XPC lookup fails, no probe runs and the error is attributed to `xpc:openSession_failed`.

Evidence (profile -> service bundle id mapping and open failure):

```
"service_bundle_id":"com.yourteam.policy-witness.ProbeService_minimal"
"layer_attribution":{"other":"xpc:openSession_failed"}
```

Evidence (session PID stability in an escalated run):

```
service_pids: ["60139", "60139"]
```

## 2. Where policy becomes concrete

This section answers: what on-disk artifacts make “policy” inspectable without
guessing (entitlements, manifests, and the derived profile catalog embedded in
the shipped `.app` bundle).

Concrete artifacts in the shipped bundle:

```
PolicyWitness.app/Contents/Resources/Evidence/
  manifest.json
  profiles.json
  symbols.json
```

Classification:

- `manifest.json`: build-generated hash inventory of embedded executables (per-entry sha256), plus metadata about the app bundle.
  - Generated by: `tests/build-evidence.py`
  - Consumed by: `policy-witness verify-evidence` (`runner/src/evidence.rs`)
  - Note: the app binary path is recorded as `app_binary_rel_path`, and the manifest explicitly omits the main binary hash (see `notes` in the manifest).
- `profiles.json`: build-generated profile catalog; per-profile variants with bundle id, service name, entitlements, and risk tier.
  - Generated by: `tests/build-evidence.py`
  - Consumed by: the launcher at runtime for `--profile` resolution (`runner/src/profiles.rs`)
- `symbols.json`: build-generated exported-symbol inventory (per embedded binary), used as a static evidence artifact.
  - Generated by: `tests/build-evidence.py` (via exported symbol enumeration)
  - Consumption: not observed in the runtime launcher path (this repo copies it into the bundle as evidence)

Cross-check (manifest sha256 vs on-disk binary):

```
manifest entry: Contents/MacOS/xpc-probe-client
sha256: a4b475a24ce47890d6b9869e7183eeaa2cfc5bb0bdeef8dfd7b22954dcf80519
actual: a4b475a24ce47890d6b9869e7183eeaa2cfc5bb0bdeef8dfd7b22954dcf80519
match: true
```

Spot-checks across multiple binary classes (all matched):

- `Contents/MacOS/xpc-probe-client`
- `Contents/XPCServices/ProbeService_minimal.xpc/Contents/MacOS/ProbeService_minimal`
- `Contents/MacOS/pw-inherit-child`
- `Contents/MacOS/xpc-quarantine-client`

Manifest note: `Contents/MacOS/policy-witness` is recorded as `app_binary_rel_path`, and its hash is intentionally omitted from the manifest (`notes` in the manifest).

Earliest concrete policy visible on disk:

```
$ codesign -d --entitlements - PolicyWitness.app/Contents/XPCServices/ProbeService_minimal.xpc
[Dict]
  com.apple.security.app-sandbox = true
```

## 3. Authoritative inputs to policy resolution

This section lists the inputs that were *observed* to change effective behavior on
this host (including “meta inputs” like whether the caller is itself sandboxed).

Observed inputs that directly influence effective policy:

- `--profile` / `--variant` -> `profiles.json` -> `bundle_id` -> XPC service lookup.
- Entitlements in the XPC service bundle (codesign).
- Host sandbox state of the caller (Run A cannot open XPC; Run B can).

CLI selection path (source-of-truth is `profiles.json`):

- `runner/src/profiles.rs`: `load_profiles()` + `find_profile_by_id()` + `find_variant()`
- `runner/src/main.rs`: `resolve_profile_variant()` picks `variant.bundle_id`
- `runner/src/main.rs`: `xpc run` forwards `bundle_id` to `xpc-probe-client`
- `xpc/client/main.swift`: `NSXPCConnection(serviceName: serviceBundleId)`

Service registration (ProbeService_minimal):

```
Info.plist:
  CFBundleIdentifier = com.yourteam.policy-witness.ProbeService_minimal
  CFBundleExecutable = ProbeService_minimal
  XPCService.ServiceType = Application
```

This establishes the chain:

```
profile "minimal"
  -> bundle path PolicyWitness.app/Contents/XPCServices/ProbeService_minimal.xpc
  -> CFBundleIdentifier com.yourteam.policy-witness.ProbeService_minimal
  -> NSXPCConnection(serviceName: bundle_id)
```

Delegation boundary (observed):

- `policy-witness xpc {run,session}` delegates to the embedded Swift helper
  `xpc-probe-client` (the Rust launcher does not speak NSXPC directly).
- In a durable session, the helper is invoked like:

```
/.../PolicyWitness.app/Contents/MacOS/xpc-probe-client session com.yourteam.policy-witness.ProbeService_minimal
```

I/O (from the session output):

- `xpc session` emits JSONL envelopes on stdout (`kind: xpc_session_event`, `kind: probe_response`, etc.).
- `xpc run` emits a single JSON envelope on stdout.

## 4. Invariants believed to hold (verified vs unverified)

This section is intentionally conservative: it lists what held in these runs, and
keeps broader invariants (e.g., cross-session stability) explicitly unverified.

- **Verified:** profile -> bundle id mapping is stable and derived from `profiles.json`.
- **Verified:** injectable variants add the same entitlement delta across profiles (see table below).
- **Verified:** session PID is stable within a single `xpc session` (escalated run).
- **Verified (sampled):** new sessions produce new service PIDs (sequential sessions and concurrent sessions both observed distinct `pid` values in `session_ready` events). This suggests the service is per-connection rather than a long-lived singleton on this host/config.

## 5. Evidence PW records vs not

This section prevents accidental over-claiming: it enumerates what PolicyWitness
actually records in artifacts versus what is currently lost (and therefore can’t be
used as evidence without additional work).

Recorded:

- XPC error attribution on open failure (`layer_attribution: xpc:openSession_failed`).
- Sandbox log capture metadata (`host_sandbox_log_capture`), including observer stderr.
- Witness payloads for probes (see `inherit_child` witness in Run B).

Not recorded (current):

- Underlying NSError `userInfo` / `NSUnderlyingErrorKey` chain beyond the stringified
  message. Today the XPC client surfaces `domain`, `code`, and a rendered message
  (which may include `NSDebugDescription` inline), but it does not emit a structured
  `userInfo` object (see `xpc/client/main.swift`).
  - Closure plan: include `NSError.userInfo` keys in the JSON (at minimum
    `NSDebugDescriptionErrorKey`, `NSUnderlyingErrorKey`, and any nested underlying
    error domains/codes), so lookup failures can be attributed to a specific API
    boundary without relying on a single formatted string.
- A stable “sandbox profile name” for the caller. In practice, the useful question
  is operational (“did `mach-lookup` get denied for this target?”), and this report
  treats explicit denies (launchd denied lookup / kernel `(Sandbox)` deny lines) as
  authoritative evidence rather than claiming a named profile.

## 6. Failure taxonomy (observed)

This section is a “what kind of failure is this?” decoder. The intent is that a
reader can distinguish “probe denied” from “probe never ran” and from “bad input”
based on structured fields, not by pattern-matching error strings.

Open-session failure (Run A):

```
normalized_outcome: xpc_error
layer_attribution: xpc:openSession_failed
error: NSCocoaErrorDomain 4099 ... failed at lookup with error 159 - Sandbox restriction
```

In this case, “error 159” is concretely a **launchd denied lookup** event (not a
probe denial). The denied name matches the service bundle id used for lookup:

```
denied lookup: name = com.yourteam.policy-witness.ProbeService_minimal, requestor = xpc-probe-clien[95444], error = 159: Sandbox restriction
```

Unknown profile (pre-lookup CLI validation):

```
$ policy-witness xpc run --profile doesnotexist world_shape
unknown profile or service: doesnotexist
```

Unknown probe (escalated run, open session succeeds):

```
normalized_outcome: unknown_probe
result.ok: false
```

Error mapping code (XPC client):

```
xpc/client/main.swift:
  open_session failure -> normalized_outcome "xpc_error"
  decode failure -> "decode_failed"
  open_session rc != 0 -> "open_session_failed"
  run_probe failure -> "xpc_error"
```

## 7. Where the system is willing to "lie"

This section captures the project’s pragmatic boundaries: places where the system
intentionally reports uncertainty (or avoids attribution) rather than manufacturing
false confidence.

- **Observed:** it does not assert "sandbox denied" when a probe never ran.
- **Observed:** missing log evidence is surfaced (Run A: `log: Cannot run while sandboxed`).
- **Observed:** it will still emit structured errors with attribution boundaries.

## 8. Profiles table (base vs injectable delta)

This section is a compact check that “injectable” means the same thing across the
whole profile set. It’s also the fastest way to sanity-check that the catalog
embedded into the `.app` bundle is coherent.

Extracted from `profiles.json` (all profiles include `base` + `injectable`):

```
profile_id	kind	label	base_risk_tier	base_bundle	base_service_name	inj_bundle	inj_service_name	inj_added_keys
bookmarks_app_scope	probe	bookmarks app scope	0	com.yourteam.policy-witness.ProbeService_bookmarks_app_scope	ProbeService_bookmarks_app_scope	com.yourteam.policy-witness.ProbeService_bookmarks_app_scope.injectable	ProbeService_bookmarks_app_scope__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
downloads_rw	probe	downloads rw	0	com.yourteam.policy-witness.ProbeService_downloads_rw	ProbeService_downloads_rw	com.yourteam.policy-witness.ProbeService_downloads_rw.injectable	ProbeService_downloads_rw__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
gatekeeper	probe	gatekeeper	0	com.yourteam.policy-witness.ProbeService_gatekeeper	ProbeService_gatekeeper	com.yourteam.policy-witness.ProbeService_gatekeeper.injectable	ProbeService_gatekeeper__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
minimal	probe	minimal	0	com.yourteam.policy-witness.ProbeService_minimal	ProbeService_minimal	com.yourteam.policy-witness.ProbeService_minimal.injectable	ProbeService_minimal__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
net_client	probe	net client	0	com.yourteam.policy-witness.ProbeService_net_client	ProbeService_net_client	com.yourteam.policy-witness.ProbeService_net_client.injectable	ProbeService_net_client__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
quarantine_bookmarks_app_scope	quarantine	quarantine bookmarks app scope	0	com.yourteam.policy-witness.QuarantineLab_bookmarks_app_scope	QuarantineLab_bookmarks_app_scope	com.yourteam.policy-witness.QuarantineLab_bookmarks_app_scope.injectable	QuarantineLab_bookmarks_app_scope__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
quarantine_default	quarantine	quarantine default	0	com.yourteam.policy-witness.QuarantineLab_default	QuarantineLab_default	com.yourteam.policy-witness.QuarantineLab_default.injectable	QuarantineLab_default__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
quarantine_downloads_rw	quarantine	quarantine downloads rw	0	com.yourteam.policy-witness.QuarantineLab_downloads_rw	QuarantineLab_downloads_rw	com.yourteam.policy-witness.QuarantineLab_downloads_rw.injectable	QuarantineLab_downloads_rw__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
quarantine_net_client	quarantine	quarantine net client	0	com.yourteam.policy-witness.QuarantineLab_net_client	QuarantineLab_net_client	com.yourteam.policy-witness.QuarantineLab_net_client.injectable	QuarantineLab_net_client__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
quarantine_user_selected_executable	quarantine	quarantine user selected executable	0	com.yourteam.policy-witness.QuarantineLab_user_selected_executable	QuarantineLab_user_selected_executable	com.yourteam.policy-witness.QuarantineLab_user_selected_executable.injectable	QuarantineLab_user_selected_executable__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
temporary_exception	probe	temporary exception	2	com.yourteam.policy-witness.ProbeService_temporary_exception	ProbeService_temporary_exception	com.yourteam.policy-witness.ProbeService_temporary_exception.injectable	ProbeService_temporary_exception__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
user_selected_executable	probe	user selected executable	0	com.yourteam.policy-witness.ProbeService_user_selected_executable	ProbeService_user_selected_executable	com.yourteam.policy-witness.ProbeService_user_selected_executable.injectable	ProbeService_user_selected_executable__injectable	com.apple.security.cs.allow-dyld-environment-variables,com.apple.security.cs.allow-unsigned-executable-memory,com.apple.security.cs.disable-library-validation,com.apple.security.get-task-allow
```

## 9. Entitlements cross-check (profiles.json vs codesign)

This section answers: is the embedded `profiles.json` describing reality, or could
it drift from what’s actually signed on disk? The sample checks below confirm the
catalog matches `codesign` for at least two representative services.

Minimal:

```
profiles.json (minimal/base):
  com.apple.security.app-sandbox = true
codesign (ProbeService_minimal.xpc):
  com.apple.security.app-sandbox = true
```

Temporary exception:

```
profiles.json (temporary_exception/base):
  com.apple.security.app-sandbox = true
  com.apple.security.temporary-exception.sbpl = [
    "(allow file-issue-extension (extension-class \"com.apple.app-sandbox.read\"))",
    "(allow file-issue-extension (extension-class \"com.apple.app-sandbox.read-write\"))"
  ]
codesign (ProbeService_temporary_exception.xpc): same keys/values
```

## 10. Sandboxed harness boundary is itself a sandbox decision

This section makes the core “harness gotcha” explicit: if the caller is blocked at
the XPC bootstrap boundary, the experiment didn’t reach sandboxed probe code, but
you still have a real policy decision worth recording (and it must not be misread
as a probe denial).

Run A shows that the caller is blocked at XPC lookup:

```
error: NSCocoaErrorDomain 4099 ... failed at lookup with error 159 - Sandbox restriction
```

This is a policy decision at the caller boundary, not a probe result.
Log capture in Run A further confirms sandbox restrictions:

```
log_error: "log show returned non-zero"
log_stderr: "log: Cannot run while sandboxed"
```

## 11. Tri-run harness (baseline vs policy vs entitlement)

This section shows the project’s “three legs” are separable: even when the policy
leg and entitlement leg are blocked on this host, the baseline leg can still
produce witnesses. That makes it a useful fallback for diagnosing “transport vs
probe semantics.”

`./experiments/bin/pw-harness run --plan experiments/plans/tri-run-smoke.json`

Observed on this host:

- baseline: ok (witness-substrate runs)
- policy: `sandbox-exec: sandbox_apply: Operation not permitted`
- entitlement: `xpc_error` (lookup 159 in harness; OK in escalated run)

This shows the harness can produce baseline witnesses even when policy and
entitlement legs are blocked by host sandbox constraints.

## 12. Injectable effect (base vs injectable)

This section is a concrete “model check” for Q1: it demonstrates that a permission-
shaped failure in `dlopen_external` can be a non-sandbox gate (library validation),
and that injectable changes the outcome in an observable way (constructor marker).

Q1 `dlopen_external` summary (escalated run):

```
base:
  normalized_outcome: dlopen_failed
  error: code signature not valid (Team ID mismatch)
  observed_deny: false
injectable:
  normalized_outcome: ok
  observed_deny: false
marker_base: absent
marker_inj: present
```

This demonstrates a real capability delta (disable-library-validation) rather
than a "return code only" claim.
These `marker_*` fields refer to an on-disk marker file written by the test dylib’s
constructor, not to exported-symbol “markers” in `symbols.json`.

## 13. Child-process semantics (inherit_child)

This section shows an end-to-end witness that is *structural*, not just “rc==0”:
the `inherit_child` probe exercises the two-bus protocol and records events plus
capability phase results in the witness payload.

`inherit_child --scenario dynamic_extension` (escalated run):

- witness includes `events` list (len 14)
- `child_event_fd` + `child_rights_fd` present (two-bus protocol)
- `capability_results` includes `file_fd` with phase-level outcomes

This is direct evidence that the capability ferry protocol is exercised and
witnessed, not inferred.

Minimal excerpt (phase ordering + PID attribution):

```
events[0]: pid 60142 phase parent_start
events[2]: pid 60142 phase child_spawned (details.child_pid=60143)
events[3]: pid 60143 phase child_sentinel
events[6]: pid 60143 phase child_acquire_attempt
events[7]: pid 60142 phase parent_token_consumed
```

## Next closure set (priority order)

1. Emit structured underlying error details from the XPC client (`NSError.userInfo`,
   `NSUnderlyingErrorKey`, etc.) so lookup failures can be triaged without relying on
   a single formatted error string.
2. Diagnose the tri-run policy leg failure (`sandbox-exec: sandbox_apply: Operation not
   permitted`) by capturing the exact `sandbox-exec` invocation and reproducing it
   inside vs outside a sandboxed harness.
3. Confirm whether the “Mach service name” looked up by the OS always equals the
   bundle id passed to `NSXPCConnection(serviceName:)` (or if any translation occurs),
   using launchd evidence (`denied lookup: name = ...`) as ground truth.
4. Validate session lifecycle boundaries beyond PID identity: does `session_closed`
   imply immediate service termination, idle timeout, or per-connection teardown?
5. Run an additional probe witness under a different profile family (e.g., bookmarks)
   to confirm cross-profile witness shape and entitlement-gated behavior beyond the
   minimal profile.
