# Verification transcript

What was actually verified, when, and how. Updated whenever a new
(operation, filter_kind) pair is added to or removed from the
`prediction_unavailable` set or whenever a sandbox_check filter ID
constant changes.

Each entry names the command that was run and the result. The
`verify_filter_id.sh` script is the canonical tool; rerun the
documented commands on a Sonoma+ host to reproduce.

## 2026-05-29 — post-audit strict verification (sibling-allowed)

### GLOBAL_NAME filter ID (mach-lookup)

```
verify_filter_id.sh mach_lookup global-name \
    com.apple.cfprefsd.xpc.daemon \
    --allowed-value com.apple.unknown.fake.service \
    --max-id 200
```

Result: IDs **2 and 12** both pass strict verification. ID 16 (the
previously-documented constant, source of BBX-001) fails — returns
allow on the denied value.

The code uses ID 2 (`PW_SANDBOX_FILTER_GLOBAL_NAME` in
`runner/ProbeRunner.swift`). ID 12 is presumably an alias or aliased
predicate path. Uniqueness of ID 2 is NOT proven — "selected working
ID" rather than "the correct value." Both IDs produce identical
verdicts across the scan, so the distinction is invisible to
consumers in practice.

### (iokit-open-service, iokit_registry_entry_class)

```
verify_filter_id.sh iokit_open iokit-registry-entry-class \
    IOSurfaceRoot \
    --allowed-value SomeNonexistentService \
    --max-id 200
```

Result: **NO filter ID in 1..200** produces (deny on `IOSurfaceRoot`,
allow on `SomeNonexistentService`). The kernel correctly enforces the
deny rule (probe baseline allow, post-apply kr=-536870174 =
kIOReturnNotPermitted). `sandbox_check` is unreliable for this
op+filter — routed to `prediction_unavailable` in
`runner/ProbeRunner.swift::predictionUnavailableOpFilters`.

### (iokit-open-user-client, iokit_user_client_class)

```
verify_filter_id.sh iokit_open_user_client iokit-user-client-class \
    IOSurfaceRootUserClient \
    --probe-target IOSurfaceRoot \
    --allowed-value AnotherUserClient \
    --max-id 200
```

Result: **NO filter ID in 1..200** matches strictly. Kernel enforces
the deny (kr=-536870174). `prediction_unavailable`.

Note: this pair specifies BOTH `--probe-target IOSurfaceRoot` (the
IOService class to open, where the kernel observation happens) and
`IOSurfaceRootUserClient` as the policy filter value (the user-client
class name the policy denies). The earlier "verification" (pre-audit)
conflated these and used the wrong SBPL operation
(`iokit-open-service`); the corrected verification uses
`iokit-open-user-client`, which is the SBPL operation
`iokit-user-client-class` matches against (confirmed via Apple's
`/System/Library/Sandbox/Profiles/application.sb`).

### (sysctl-read, sysctl_name)

```
verify_filter_id.sh sysctl_read sysctl-name kern.osrelease \
    --allowed-value kern.nonexistent.sibling \
    --max-id 200
```

Result: **NO filter ID in 1..200** matches strictly. Kernel enforces
the deny. `prediction_unavailable`.

### (user-preference-read, preference_domain)

**Not verified — punted.** The `preferences_read` probe in
`enforcement_probe.c` uses `CFPreferencesCopyKeyList`, which did not
appear to observe enforcement of a deny rule against
`com.apple.dock`. A narrow probe is insufficient evidence that the
filter is unenforceable, so the filter is intentionally NOT exposed
in `validateSandboxChecks`. Before exposing it, extend the probe to
also try `CFPreferencesCopyAppValue`, `CFPreferencesSetValue`, sync,
and the per-user variants — and only then verify with this harness.

## Methodology notes

- `--allowed-value` enables **strict mode** with asymmetric
  evidence: a filter ID passes when its sandbox_check verdict is
  deny for the policy's denied value (matched against the kernel's
  observed verdict via the probe) AND allow for the sibling
  un-denied value (sandbox_check's own answer; the syscall is NOT
  exercised against the sibling). This excludes incidental deniers
  like ID 1 (PATH) which returns deny for any string. It does not
  prove the kernel would allow the sibling — to raise confidence
  further, exercise the operation against the sibling out of band
  and confirm the kernel allows. Without `--allowed-value`, the
  script runs in permissive mode and reports candidate matches
  that may include incidental deniers.
- Default `--max-id 200`; the older `SCAN_MAX=63` was insufficient
  for several real filter IDs. The 1..200 default was chosen to cover
  the known constants comfortably; raise via `--max-id` if a new
  filter kind needs a wider scan.
- For each pair removed from or added to
  `predictionUnavailableOpFilters`, add a stanza here with the
  command and result. The audit trail is part of the contract.
