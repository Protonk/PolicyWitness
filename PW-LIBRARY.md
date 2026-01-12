# PW-LIBRARY: Signed Instrumentation Dylib (Design Sketch)

This document proposes a small, signed instrumentation dylib that can be loaded
by a dedicated instrumented service variant. It is intentionally narrow: a
controlled "instrument port" for observing in-process behavior, not a sandbox
bypass and not a general plugin system. The dylib runs with the full authority
of the service process, so the correct framing is "a small additional trusted
component" rather than "an untrusted plugin with restrictions". The goal is to
enrich runtime visibility while keeping base profiles and user-facing
documentation clean and stable.

The approach relies on:

- A dylib signed with the same Team ID as the app/services.
- Explicit opt-in in instrumented variants only.
- A minimal, stable C ABI that emits telemetry.
- Strict load gating and auditable witness records.

This is a design sketch. Some details may be adjusted during implementation.

## Trust framing (explicit trusted component)

Once loaded, the dylib has the same entitlements and sandbox authority as the
service. That is acceptable because it is our code, but it means the right
optimization is auditability and minimization, not runtime policing.

- Base variants remain the canonical sandbox profiles and never load
  instrumentation.
- Instrumented variants make the trust explicit and opt-in.
- Injectable remains a separate dev-power surface, not the default for
  instrumentation.
- The loader is strict and records every decision (path policy and signature
  checks).
- The ABI is narrow and telemetry-only; if it misbehaves, the Team ID and
  signing identifier are attributable.

## Path policy and bundle resolution

Default policy: servicebundle only.

- Recommended: embed the dylib inside each XPC service bundle, for example
  `ProbeService_minimal.xpc/Contents/Frameworks/PWInstrumentation.dylib`.
  In this mode, `servicebundle:` resolves relative to the XPC service bundle.
- `servicebundle:` is the only supported scheme in shipping builds.
- External paths (absolute) are dev-only and gated by both build config and an
  explicit flag (`--allow-external-paths`). External loads must be allowlisted
  (cdhash or sha256) and recorded in the witness.

The witness should include whether external paths were permitted by build
configuration, and whether the caller enabled them.

## TOCTOU and external paths (dev-only)

If external paths are allowed:

- Canonicalize with `realpath` and enforce root allowlists.
- Open with `O_NOFOLLOW`, `fstat`, and record `(dev, inode, size, mtime)`.
- Compute a content hash (sha256) before loading.
- After `dlopen`, resolve the loaded image path (`dladdr`/`dlinfo`) and
  re-verify it matches the verified target. If not, fail with
  `post_load_verification_failed`.

## Signature gating (strong and maintainable)

Prefer a designated requirement over ad hoc comparisons.

Suggested checks:

- Team ID
- signing identifier (use `--require-identifier`, not `--require-bundle-id`)
- optional cdhash or sha256 allowlist for exact build pinning

Record in the witness:

- `signature_team_id`, `signature_identifier`, `signature_cdhash`
- `requirement_string` and `check_mode` (requirement vs ad_hoc)
- `file_hash_sha256`
- `resolved_path` and `path_scheme` (servicebundle/abs)

## Minimal API (C ABI)

The dylib exports a tiny, versioned C interface. The host (PolicyWitness
service) calls a single start function, passes a context with function pointers
for telemetry, and optionally calls stop.

Proposed header (stable C ABI):

```c
// pw_instrument.h (sketch)
#pragma once
#include <stdint.h>

// Increase when struct layout changes.
#define PW_INSTRUMENT_ABI_VERSION 1

typedef struct pw_instrument_context {
  uint32_t abi_version;
  uint32_t context_size;
  uint64_t flags;

  // Identity of the running service variant.
  const char *service_bundle_id;
  const char *service_executable;
  const char *service_variant; // "base", "instrumented", or "injectable"

  // Correlation primitives for joining events to sessions/probes.
  const char *session_id;
  const char *probe_invocation_id;
  const char *plan_id;
  const char *run_id;

  // Backpressure hints.
  uint32_t max_event_bytes;
  uint32_t max_events_per_sec;

  // Length-delimited event emission (host owns framing and timestamps).
  void (*emit_event_json)(const char *json, uint32_t len);
  void (*emit_marker)(const char *name, uint32_t len);
  void (*emit_drop_notice)(uint32_t dropped, const char *reason, uint32_t len);

  // Optional monotonic clock source.
  uint64_t (*now_monotonic_ns)(void);

  // Reserved for append-only ABI extension.
  void *reserved0;
  void *reserved1;
  void *reserved2;
} pw_instrument_context_t;

// Required: returns the ABI version the dylib was built for.
uint32_t pw_instrument_version(void);

// Required: initialize and start instrumentation.
// Must be idempotent and safe to call once per process.
int pw_instrument_start(const pw_instrument_context_t *ctx);

// Optional: stop and release resources.
void pw_instrument_stop(void);
```

ABI rules:

- The struct is append-only; new fields are added at the end.
- The dylib must check `ctx->abi_version == PW_INSTRUMENT_ABI_VERSION`.
- The dylib must check `ctx->context_size >= sizeof(pw_instrument_context_t)`
  for its compiled header version.

## Behavior constraints (recommended)

- Treat the dylib as a tiny, audited component; keep it minimal.
- Avoid spawning subprocesses or loading additional code by path unless this is
  explicitly designed and documented (it is not enforceable in-process).
- Emit a structured `pw_instrumentation_failed` event on errors instead of
  crashing the service.

## Telemetry robustness and framing

- Emissions are length-delimited; the host owns framing and timestamps.
- Host callbacks should be non-blocking or bounded; if saturated, they drop and
  increment counters.
- The host records `events_received`, `events_dropped`, and `max_queue_depth`
  (if buffered), plus a monotonic sequence number.
- The host rejects or escapes newline characters if any string-based callback
  is retained.

Telemetry MVP and goal:

- MVP: JSON events only (single stream, in-band with witness output).
- Goal: coalesced output that merges multi-source telemetry (JSON events,
  signposts, and other sources) into one robust stream so users do not need to
  consult external logs.

Stream shape decision:

- Use a single JSONL output channel with a distinct `kind` (for example
  `instrumentation_event`) rather than a separate output stream. This keeps the
  "one place to look" promise and avoids a merge step.
- Include a `source` field so instrumentation events remain clearly separated
  from probe responses and session events.

## Probe shape (explicit load, instrumented-only)

Proposed probe: `instrumentation_load` (instrumented variant only).

Suggested interface:

```
instrumentation_load --path <servicebundle:...|/abs>
                      [--allow-external-paths]
                      [--require-team-id <TEAMID>]
                      [--require-identifier <id>]
                      [--require-cdhash <hex>]
                      [--require-sha256 <hex>]
                      [--mode <dlopen>]
```

Suggested behavior:

- Refuse on base variants (`normalized_outcome: "not_allowed"`).
- Default to `servicebundle:` only. External absolute paths require build-time
  permission plus `--allow-external-paths`.
- Verify code signature using a designated requirement when possible.
- If external paths are allowed, perform TOCTOU defenses and post-load
  verification.
- Use explicit `dlopen` rather than relying on DYLD environment variables.
- Record in the witness:
  - `instrument_path`, `resolved_path`, `path_scheme`
  - `signature_team_id`, `signature_identifier`, `signature_cdhash`
  - `requirement_string`, `check_mode`, `file_hash_sha256`
  - `external_paths_allowed_by_build`, `external_paths_allowed_by_flag`
  - `has_disable_library_validation`, `has_allow_dyld_env`

Success path:

- Calls `pw_instrument_start` with a context that includes event emitters.
- Emits a `pw_instrumentation_started` event.
  - This start event should include version and signing metadata
    (`instrumentation_version`, `instrumentation_abi_version`,
    `signature_identifier`, `signature_cdhash`).
  - Subsequent events should include a short `instrumentation_id` that can be
    joined back to the start event, rather than repeating full version fields
    in every event.

Failure path:

- Emits a `pw_instrumentation_failed` event with error details.
- Returns a normalized outcome like `signature_check_failed`, `dlopen_failed`,
  or `abi_mismatch`.

Note: this can be implemented as a standalone probe or as a controlled wrapper
over the existing `dlopen_external` probe with added gating.

## Failure taxonomy (normalized_outcome)

Suggested additions:

- `path_not_allowed`
- `path_resolution_failed`
- `signature_check_failed`
- `identifier_mismatch`
- `cdhash_mismatch`
- `hash_mismatch`
- `export_missing`
- `abi_mismatch`
- `start_failed`
- `post_load_verification_failed`

## Optional observability features (narrow but high value)

- Dyld image inventory: emit a full image list at start, then
  `image_loaded` events as new images load.
- Probe lifecycle markers: `probe_start`/`probe_end` events around each probe.
- Health snapshots: memory footprint, thread count, CPU time deltas.
- Very small, labeled interposition if needed (avoid global "hook everything").

## Variant hygiene

Use a dedicated `@instrumented` variant as the only supported target for
`instrumentation_load`.

- `@instrumented` is a minimal delta variant (ideally only the entitlements
  required to load the dylib and attach a debugger).
- `@injectable` stays a separate dev-power surface for broader experiments.
- `instrumentation_load` should refuse on `@injectable` unless an explicit
  dev-only override is set and recorded in the witness.

## Minimal entitlements sketch for `@instrumented`

The goal is to keep `@instrumented` as close to the base profile as possible,
while still enabling explicit `dlopen` of the signed instrumentation dylib and
debugger attach.

Proposed delta (add to the base service entitlements):

- `com.apple.security.get-task-allow` = true
- `com.apple.security.cs.disable-library-validation` = true (required for
  loading the instrumentation dylib)

Notarization note: Apple will fail notarization for `get-task-allow` and other
debug-style entitlements (including `disable-library-validation`,
`allow-dyld-environment-variables`, `allow-unsigned-executable-memory`, and
`allow-jit`). Treat `@instrumented` as dev/internal or exclude it from
notarized release bundles.

Explicitly *not* included by default:

- `com.apple.security.cs.allow-dyld-environment-variables`
- `com.apple.security.cs.allow-unsigned-executable-memory`
- `com.apple.security.cs.allow-jit`

Optional extensions (dev-only or separate variant):

- If you want env-based injection experiments, add
  `com.apple.security.cs.allow-dyld-environment-variables`.
- If you want runtime codegen/patching tools, add
  `com.apple.security.cs.allow-unsigned-executable-memory`. This entitlement is
  a superset of `allow-jit`; use `allow-jit` only when you specifically need
  MAP_JIT but do not want the broader superset. Selecting both is redundant.

This keeps `@instrumented` aligned with the "observability only" goal while
preserving `@injectable` as the broader, explicitly high-concern surface.

## User-facing documentation blurb (for PolicyWitness.md)

This is a minimal, user-facing explanation that can be pasted into
`PolicyWitness.md` if the feature ships.

```
### Instrumentation dylib (instrumented variants only)

Instrumented variants can optionally load a signed instrumentation dylib to emit
extra telemetry from inside the service process. This does not change the
sandbox entitlements; it only adds observability.

To load the dylib:

  $PW xpc session --profile minimal@instrumented \
      instrumentation_load --path servicebundle:Frameworks/PWInstrumentation.dylib

External paths are dev-only and require an explicit flag plus build-time
permission. The loader validates the dylib signature (Team ID / identifier /
cdhash) and records the result in the witness output. Base variants never load
instrumentation.
```

## Non-goals

- This is not a general plugin system.
- It does not permit arbitrary path exec.
- It does not expand sandbox entitlements or add new capability profiles.

## Open questions (to resolve when implementing)

- Exact embed location inside the service bundle (Frameworks vs Resources) and
  how to version it.
- Final entitlement set for `@instrumented`.
- How strict to make signature gating (requirement string vs cdhash pinning).
- Whether to emit telemetry as JSONL, signposts, or both.
