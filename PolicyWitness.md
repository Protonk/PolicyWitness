# PolicyWitness User Guide

PolicyWitness runs sandbox specimens and prints a single JSON envelope to stdout. Each specimen is an SBPL policy plus a probe plan; each run produces one envelope describing what the kernel actually did under that policy, alongside the validator's userland prediction for the same operations. For shorter answers to common questions see [QUESTIONS.md](QUESTIONS.md); for the project-level pitch see [README.md](README.md).

Reading paths: try it via [Quick start](#quick-start), write a specimen via [Specimen format](#specimen-format), or interpret output via [Output envelope](#output-envelope).

## Contents

- [Quick start](#quick-start)
- [Specimen format](#specimen-format)
- [Output envelope](#output-envelope)
- [What PolicyWitness understands](#what-policywitness-understands)
- [Operating](#operating)
- [External runners (BYOXPC)](#external-runners-byoxpc)

## Quick start

Quick start uses the built-in standard runner. If you need entitlements the standard runner doesn't ship — debug-attach, DYLD env, custom dylib loading, JIT — see [External runners (BYOXPC)](#external-runners-byoxpc) below.

Set a convenience variable:

```sh
PW="$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness"
```

Create a specimen:

```sh
cat > /tmp/pw_specimen_file_read_deny.json <<'JSON'
{
  "schema_version": 1,
  "specimen_id": "file_read_deny",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default) (deny file-read-data)"
  },
  "probe_plan": [
    {
      "step_id": "fr1",
      "sandbox_check": {
        "operation": "file-read-data",
        "filter": { "kind": "path", "value": "/etc/hosts" }
      },
      "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
    }
  ]
}
JSON
```

Run it:

```sh
$PW run /tmp/pw_specimen_file_read_deny.json > /tmp/pw_result.json
```

## Specimen format

### Top-level shape

Top-level fields:

- `schema_version`: number
- `specimen_id`: string
- `run_kind`: string (optional)
- `policy`: object
- `probe_plan`: array of steps
- `runner`: object (optional; select runner mode and external runners)

Minimal skeleton (copy/paste):

```json
{
  "schema_version": 1,
  "specimen_id": "skeleton",
  "runner": { "mode": "standard" },
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": []
}
```
Notes:
- All path rules live inside `policy.sbpl_source`; there is no `path_membership` field.
- `probe_plan` may be empty when you only want to exercise sandbox
  apply (the validator child is only spawned when there are probes
  to query).

### Policy

SBPL source:

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1) (allow default) (deny file-read-data)",
  "params": { "DENY_DIR": "/tmp/deny" }
}
```

`(import "...")` statements compile transparently — `sandbox_compile_string`
resolves them against the system profile search path. `(param "NAME")`
substitution uses values from `policy.params`. `string-append` of param
references is supported by the compiler.

### SBPL check (`sbpl-check`)

`sbpl-check` is a host-side SBPL compiler. The C worker exercises the
policy itself (a non-compiling policy surfaces as `sandbox_apply_failed` — the
worker does not distinguish compile failure from apply failure), so the run
flow does **not** run `sbpl-check` on the happy path — it invokes `sbpl-check`
only to disambiguate an `xpc_error` (a policy that compiled but then blocked
the XPC reply vs. one that never compiled), surfacing the result under
`data.policy_check` and `data.runner_startup_diagnostics`. You can also run
the tool directly for any of the diagnostics below. The sbpl-check envelope
exposes:

- `params_referenced`: names found in `(param "...")` forms in the source
  (string literals and `;` line comments are skipped).
- `params_supplied`: keys from `policy.params`.
- `params_missing`: referenced but not supplied. If non-empty, sbpl-check
  returns `result.normalized_outcome = "missing_params"` and exits 1 with a
  clean `result.error` listing the names — instead of the cryptic libsandbox
  message ("expected pattern, got boolean") that surfaces when an unbound
  `(param ...)` is folded into a path filter. The libsandbox message is
  still preserved under `data.compile_error` for auditability.
- `params_unused`: supplied but never referenced. Recorded as info only;
  does not fail the check.
- `params_scan_complete`: false when the source contains at least one
  `(param X)` form where `X` is not a quoted string. That's typically
  macro-indirected, e.g.
  `(define (helper pn) (subpath (param pn)))` with `(helper "FOO")` at the
  call site — the literal `"FOO"` is bound to `pn` at a level the surface
  lexer doesn't expand. When this flag is false, treat `params_missing:
  []` as "we couldn't tell" rather than "nothing required". The cryptic
  libsandbox error ("expected pattern, got boolean") then surfaces under
  `compile_error` as before. Resolving these would require real macro
  expansion and is out of scope for the sbpl-check scanner.

`policy.sbpl_source` is capped at 4 MiB. Oversized inputs are rejected with
`result.normalized_outcome = "policy_too_large"` and exit code 1; nothing is
sent to libsandbox and no imports are resolved. The cap is in place to bound
sbpl-check work — far above any real-world hand-written profile.

When the source passes the size cap and the params check but
libsandbox itself rejects the policy at compile time (syntax error,
unknown operation, malformed filter, etc.), `sbpl-check` returns
`result.normalized_outcome = "bad_policy"` and exit code 1, with
`data.compile_error` carrying the libsandbox-side diagnostic (often
cryptic — "expected pattern, got boolean" is the canonical example
for a malformed filter argument). `bad_policy` is distinct from
`missing_params` and `policy_too_large` above, both of which gate
before the policy reaches libsandbox. In the run flow a policy that
fails to compile is **not** reported as `bad_policy`: it reaches the C
worker and surfaces as `sandbox_apply_failed` (the worker writes the
same `apply_rc = -1` for a compile failure as for an apply failure).
`bad_policy` in a run is now emitted only by the runner host for a
structurally invalid policy (missing `sbpl_source`, or a non-`sbpl`
`format`); the host runs `sbpl-check` itself only on the
`xpc_error` path.

The sbpl-check envelope also records the imports closure:

- `imports`: each entry is `{name, resolved_path, sha256, size_bytes,
  mtime_unix, error}`. The resolver walks `(import "...")` statements
  recursively (depth cap 8, count cap 64), trying
  `/System/Library/Sandbox/Profiles/<name>` first and then
  `/usr/share/sandbox/<name>`. Names must include the `.sb` extension —
  libsandbox does not auto-append. Absolute paths starting with `/` are
  accepted as-is.
- `imports_truncated`: true when either the count cap (64 imports) or the
  depth cap (8 levels) was hit during resolution. Records still include the
  partial result up to the cap.
- `imports_cycle`: when a back-edge to an in-progress import is detected
  during resolution, the chain of import names that closed the cycle —
  `[outer, ..., inner, repeated_name]`. Null when no cycle is present. The
  field is single-valued: only the first cycle observed in a given walk is
  reported. (Diamond imports — the same file reached via two distinct paths
  with no cycle — are deduplicated silently and do not populate this field.)
- `policy_sha256`: sha256 of `policy.sbpl_source` only.
- `policy_closure_sha256`: sha256 of the source plus the sorted
  `resolved_path + " " + sha256` of every successfully resolved import.
  This hash is reproducible iff every resolved file is content-identical
  on the verifying host. Unresolved imports are excluded — check
  `imports[].error` to see which ones failed.
- `macos_build_version`: `sw_vers -buildVersion` for the host that ran `sbpl-check`. Import contents change between OS builds; this lets a
  downstream auditor decide whether a closure hash is verifiable on their
  machine.

### Augments

`policy.augments` is an optional array of named SBPL fragments shipped
inside the signed app bundle under
`Contents/Resources/Augments/<name>.sb`. The controller resolves each
name **before the runner runs**, appends the augment's contents to
`policy.sbpl_source`, computes both the original-source and
applied-source sha256, and strips the `augments` field from the
request forwarded to the runner. The runner therefore compiles the
spliced bytes (as does `sbpl-check` if the `xpc_error` path runs
it), and the runner has no augment-aware code path.

```json
"policy": {
  "format": "sbpl",
  "sbpl_source": "(version 1)\n(deny default)\n",
  "augments": ["exec_baseline"]
}
```

Resolution rules:

- Augment names must match `^[A-Za-z0-9_]+$`. Anything else (including
  `..`, path separators, or empty strings) is rejected with
  `normalized_outcome = "bad_request"` before the runner is invoked.
- A name that doesn't resolve to
  `<app>/Contents/Resources/Augments/<name>.sb` is rejected with
  `bad_request` and `error = "unknown augment '<name>'"`.
- The `augments` field being absent, `null`, or `[]` is treated as
  "no augments." In the empty/null cases the field is still stripped
  from the request before forwarding so the runner sees no
  augment-aware shape.

Splicing semantics:

- Augments are **append-only and allow-only.** Each shipped augment
  contains only `(allow ...)` rules; the author commits not to emit
  `(deny ...)`.
- SBPL is last-match-wins, so an augment's `(allow process-exec)`
  overrides a caller's earlier `(deny process-exec)` for the
  operations the augment covers. A caller opting into an augment
  consents to this override; the controller does not warn about
  overlap.

Envelope reporting:

- `data.policy_augmentation` is present only when augments were
  applied. Shape:

  ```json
  "policy_augmentation": {
    "applied": ["exec_baseline"],
    "original_sha256": "<sha256 of policy.sbpl_source as submitted>",
    "applied_sha256":  "<sha256 of source after augments appended>"
  }
  ```

  When augments were applied, `data.runner_result.policy_sha256`
  (the hash the runner computed over the bytes it actually compiled)
  equals `applied_sha256`. A consumer that wants "what the caller
  submitted" reads `original_sha256` instead.

Shipped augments:

- **`exec_baseline`** — three `(allow ...)` rules that let a
  libSystem-dynamic helper `posix_spawn` under `(deny default)`:
  `(allow process-exec*)`, `(allow process-fork)`, and an
  **unconditional** `(allow file-read*)`. Empirically derived
  against `tests/suites/runner_use_c_worker/exec_fixture/helper.c`
  on macOS 14.8.3 (build 23J220, Darwin 23.6.0).

  **This is a pragmatic baseline, not a narrow minimum.**
  `(allow file-read*)` is unconditional because the kernel reads
  the target binary's bytes before exec and the augment can't
  predict the caller's chosen helper path. Because augments are
  appended after the caller's source and SBPL is last-match-wins,
  this allow overrides any caller-authored `(deny file-read* ...)`.
  Specimens that probe file-read denial cannot be composed with
  `exec_baseline`.

### Probe plan steps

Each step has:

- `step_id`
- `sandbox_check`: `{ operation, filter }`
- `attempt`: `{ kind, action, target }`

Example:

```json
{
  "step_id": "read_etc_hosts",
  "sandbox_check": {
    "operation": "file-read-data",
    "filter": { "kind": "path", "value": "/etc/hosts" }
  },
  "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
}
```

## Output envelope

### Shape and schema_version

Runner responses use `schema_version = 4`. The XPC service host stays
unsandboxed and spawns two children per specimen: `pw-probe-runner`
(the sandboxed C worker that applies the policy and runs probe
attempts) and `sb_api_validator --batch` (queries `sandbox_check`
verdicts against the worker's PID). `data.runner_result.pid` names
the worker process when `runner_subprocess` is present; use it for
unified-log correlation. `runner_subprocess` records
`{ pid, term_signal, exit_code, partial_steps }`.
`validator_subprocess` records the validator child's
`{ pid, exit_code, term_signal }` or is `null` when no validator
ran (see [Top-level fields](#top-level-fields) below).

The `exec` attempt kind adds five optional per-step fields under
`steps[].attempt` — `child_pid`, `child_exit_code`,
`child_term_signal`, `stdout`, `stderr` — populated only for
`("exec", "spawn")` attempts. These are **additive optional fields
under the existing schema_version=4 contract** (no version bump):
consumers that don't introspect them see no shape change, and
consumers that branch on `attempt.outcome == "exec_failed"` see all
five fields exactly when an exec attempt's slot was filled. A
non-exec attempt's envelope omits the keys entirely so a sysctl /
file / mach result envelope does not grow five null fields it has
no use for.

### Top-level fields

Top-level fields beyond `pid` / `runner_subprocess`:

- `validator_subprocess: { pid, exit_code, term_signal } | null` —
  populated whenever the validator child ran. Exactly one of
  `exit_code` (clean exit) or `term_signal` (SIGKILL fallback) is
  non-null. `null` in two cases:
    1. No validator probes remained after orchestrator-side
       filtering, so the validator was never spawned. This covers an
       empty `probe_plan`, plus any plan where every step's
       `sandbox_check` falls into one of the
       `prediction_unavailable` buckets — `(operation, filter_kind)`
       pair in the empirically-drifting set (iokit / sysctl
       families), filter kind the runner doesn't predict
       (`preference_domain`, `mach_port`, etc.), or path filter
       whose `filter_value` doesn't resolve via `realpath` on the
       host. The orchestrator synthesizes
       `sandbox_check.outcome = "prediction_unavailable"` for each
       skipped step locally.
    2. The validator failed to spawn before any metadata could be
       captured (surfaced as `normalized_outcome =
       "validator_spawn_failed"`).
- `steps[].drift: bool | null` — disagreement between the
  validator's predicted verdict and the attempt's observed verdict
  for the step. `true` when they disagree about allow/deny
  (libsandbox-drift evidence; the property PolicyWitness exists to
  surface). `false` when they agree.
  `null` when no comparison is possible. Three cases produce `null`:
    1. The validator wasn't run for this step (the step's filter
       kind is unknown to the runner, or the (op, filter) pair is
       in the prediction-unavailable set, or no validator child ran
       at all).
    2. The attempt didn't produce an allow/deny verdict (the attempt
       errored before reaching the kernel, or the attempt outcome is
       `not_run_worker_died`).
    3. The attempt observed a *DAC*-ambiguous failure — EPERM or
       EACCES on a file/access path — while the validator predicted
       `allow`. Filesystem permissions and the sandbox both surface
       as EPERM/EACCES from a file open; the runner can't tell them
       apart from rc/errno alone, so `(validator=allow,
       attempt=ambiguous-deny)` is reported as `null` instead of
       `true` to avoid false libsandbox-drift attribution. Strong
       deny evidence (mach `kr=1100`, etc.) is unambiguous and does
       produce `drift=true` when the validator predicted `allow`.
  Encoded as explicit JSON `null` so the key is always present.

The request schema also accepts an optional `_test_overrides`
field. The leading underscore is intentional: it marks `_test_overrides`
as a private, unsupported field used by the project's own tests to
reach failure paths that production specimens can't construct.
Production callers should leave it unset. The one exception users
may want to reach for directly is `worker_post_apply_hang_ms` for
debugger attach (see [Debug-attach to the worker](#debug-attach-to-the-worker)).

### Per-step shape

The runner echoes step results with additional context:

- `steps[].sandbox_check`: `{ rc, outcome, pid, operation, scope, filter_kind, filter_value, effective_filter_value, filter_type_id, errno, error, path_diagnostics? }`
- `steps[].attempt`: `{ rc, exit_code, errno, syscall_errno, outcome, error, requested_path, normalized_path, observed_path }`
- `steps[].drift`: `bool | null` — see the field description above.

Notes:
- `scope` is `post_sandbox` for runner-hosted checks.
- `requested_path` echoes the attempt target for every attempt kind
  (path, Mach service name, sysctl name, etc.). `normalized_path` and
  `observed_path` are file-path diagnostics; non-file attempts carry
  explicit `null` for those fields.
- `filter_value` is the exact string the runner passes to `sandbox_check`,
  except when `outcome == "prediction_unavailable"` — in that case no
  `sandbox_check` call is made; `filter_value` is echoed back from the
  request unchanged for cross-referencing with the specimen.
- `effective_filter_value` is a canonicalized/realpath form used for reporting only.
- `filter_type_id`: `1` (path), `2` (mach-lookup global), `17`
  (mach-lookup local). The global-name ID was previously documented
  as `16` based on a now-invalidated external reference; empirical
  verification against actual kernel enforcement (see
  `tests/suites/witness_contract/harness/verify_filter_id.sh`) shows
  `2` works correctly under strict verification (deny on the policy's
  denied value AND allow on a sibling un-denied value). ID `12` also
  passes the same strict verification across the scan to 200 —
  presumably an alias or aliased predicate path — so `2` is the
  selected working ID, not the uniquely correct one. The local-name
  ID (`17`) has not been re-verified by the same methodology and may
  also be incorrect; it is documented here unchanged pending a
  verification fixture. For filter kinds in the
  prediction_unavailable set, no `filter_type_id` is emitted (see
  [Filter kinds where prediction is unavailable](#filter-kinds-where-prediction-is-unavailable)).
- `outcome`: `allow`, `deny`, `error`, `unsupported_operation`, or
  `prediction_unavailable`.
    - `allow` / `deny`: `sandbox_check` returned a clean verdict.
    - `error`: `sandbox_check` returned a non-EINVAL failure
      (rare in practice). `error` is always populated with
      `strerror(errno)` — consumers should never see
      `outcome == "error"` with `error == null`.
    - `unsupported_operation`: `sandbox_check` returned `rc=-1` +
      `errno=22` (EINVAL), which most commonly means the operation
      name is one libsandbox doesn't recognize. SBPL family
      operations must be passed to `sandbox_check` in their
      wildcard form — e.g. `process-exec*`, not the bare
      `process-exec`. `error` is always populated with a message
      naming the rejected operation and the wildcard hint. Treat
      this as a per-step skip (parallel to the attempt-side
      `unsupported` outcome): the step still runs the attempt
      channel for the observation, but the prediction channel
      yields no allow/deny verdict so `drift` is `null`.
    - `prediction_unavailable`: emitted when the runner deliberately
      skips `sandbox_check` for a step where the userland predicate
      is structurally suspect. Two triggers:
        - **op+filter pair** known to drift from kernel enforcement
          (iokit / sysctl families — see
          [Filter kinds where prediction is unavailable](#filter-kinds-where-prediction-is-unavailable)).
        - **per-step host condition**: a `path` filter whose
          `filter_value` doesn't resolve via `realpath` on the host.
          For absent paths the kernel ENOENTs file-* access vectors
          before reaching the sandbox layer, so a libsandbox verdict
          for that path is a userland canonicalization artifact, not
          a kernel prediction. `error` is populated naming the
          unresolved path; `path_diagnostics.realpath_resolved` is
          `null` as a second tell.
      Channel A (the `attempt` result) remains the reliable evidence
      for these probes; the prediction is honestly absent rather
      than wrong.
  When `outcome == "prediction_unavailable"`, `rc` is the sentinel
  `-1` (not `0`) and `errno`/`filter_type_id` are `null` — consumers
  that key on `rc == 0` for "allow" must check `outcome` first so the
  sentinel is not misread.

`steps[].attempt.outcome` values:

- `ok` — the attempt's syscall returned success (allow).
- `open_failed` — file `open()` (for `open_read` / `open_write` /
  `create`) returned non-zero; errno in `attempt.errno`. EPERM /
  EACCES are ambiguous between sandbox and DAC (see
  [Top-level fields](#top-level-fields) → `drift`).
- `unlink_failed` — file `unlink()` returned non-zero; errno in
  `attempt.errno`.
- `access_failed` — file `access(R_OK)` returned non-zero; errno in
  `attempt.errno`.
- `lookup_failed` — `bootstrap_look_up` returned a non-success
  Mach kernel return code; the `kr` is preserved in
  `attempt.error` as `"bootstrap_look_up: kr=<N>"`. `kr=1100`
  (`BOOTSTRAP_NOT_PRIVILEGED`) is the sandbox-deny signal;
  `kr=1102` (`BOOTSTRAP_UNKNOWN_SERVICE`) means the service simply
  isn't registered.
- `sysctl_failed` — `sysctlbyname()` returned non-zero; errno in
  `attempt.errno`. EPERM / EACCES are ambiguous; ENOENT / ENOMEM
  are non-policy failures.
- `exec_failed` — `posix_spawn` was blocked, the target was
  missing, the helper exited non-zero, the helper was signaled, or
  the per-exec deadline fired. See
  [Attempt kinds the runner implements](#attempt-kinds-the-runner-implements)
  → `("exec", "spawn")` for the `child_pid` sentinel rules that
  distinguish a sandbox-denied spawn from a helper that simply
  exited non-zero.
- `bootstrap_port_failed` — couldn't obtain the worker's bootstrap
  port via `task_get_special_port(TASK_BOOTSTRAP_PORT)` — a
  precondition failure for `mach_lookup` rather than a verdict on
  the lookup itself. Rare.
- `unsupported` — the `(attempt.kind, attempt.action)` combination
  isn't in PolicyWitness's implemented set. Per-step skip: the
  worker no-ops this slot; the `sandbox_check` verdict still runs;
  `drift` is `null` for the step.
- `not_run_worker_died` — the worker exited before reaching this
  slot. Distinct from a per-attempt failure: the attempt itself
  never ran, so the absent verdict is a missing-evidence signal
  rather than a deny attribution.

### path_diagnostics

`path_diagnostics` is emitted on every path-filter `sandbox_check`
result. It carries the candidate kernel-side forms of the check
path so a caller can see which prefix libsandbox could have been
comparing against when a `(subpath ...)` rule denies a path that
looked like it should match. Fields: `{ input, realpath_resolved,
firmlink_resolved, data_volume_form }`. The runner still passes
the raw `filter_value` to `sandbox_check` — this block is
observation only.

Producer: `path_diagnostics` is computed by the unsandboxed runner
host (`PWRunnerService.enrichPathDiagnostics`) after the worker
process returns. The host's `realpath(3)` is not blocked by the
worker's `(deny default)` policy, so `realpath_resolved` is reliably
populated even under restrictive sandboxes.

At v2+ all four keys are always emitted: a string when computed, an
explicit `null` when the computation didn't produce a value. Consumers
can therefore distinguish "computed and the result was null" (key
present, value `null`) from "diagnostic was not emitted at all" (key
absent or the entire `path_diagnostics` object absent).
- `realpath_resolved`: `realpath(3)` of `input`, or null on failure.
  Computed in the unsandboxed host; under normal conditions this is
  populated whenever the file exists. Null only when the host's own
  `realpath` fails (path doesn't exist, permission denied at the
  host level, etc.). The other forms below remain computable in that
  case.
- `firmlink_resolved`: the realpath result rewritten through
  `/usr/share/firmlinks`. When realpath returned null, the host
  falls back to a pure-string substitution of the standard userspace
  symlinks (`/etc`, `/tmp`, `/var` → `/private/{etc,tmp,var}`)
  before applying firmlinks, so `/etc/hosts` still lands at
  `/System/Volumes/Data/private/etc/hosts` in the rare case the
  host's `realpath` fails. The firmlinks map is loaded eagerly and
  has a built-in fallback mirroring the standard mappings on
  Catalina+.
- `data_volume_form`: heuristic shortcut that prepends
  `/System/Volumes/Data` to paths under `/private/`. Computed from the
  same fallback basis as `firmlink_resolved`, so it is populated for the
  common case even when realpath is unavailable.

Capture the sandbox_check argument quickly (no interpose needed):

```sh
jq '.data.runner_result.steps[].sandbox_check | {filter_value, effective_filter_value, filter_type_id, outcome, path_diagnostics}' run.json
```

### normalized_outcome catalog

`data.runner_result.normalized_outcome` values the runner can produce
(`bad_policy` for a structurally invalid policy, plus the standalone
`sbpl-check` tool outcomes `missing_params` and `policy_too_large`,
are documented under SBPL check above):

- `ok` — worker completed the probe plan and the validator returned
  verdicts for every non-skipped probe; both children clean-exited.
- `runner_sandbox_denied` — worker spawned, applied the policy, then
  was terminated by a fatal signal before flipping its `done`
  sentinel. The kernel sandbox is the overwhelming cause on macOS;
  the precise signal is preserved in `runner_subprocess.term_signal`
  (commonly `9` for SIGKILL, or `5`/`6` for SIGTRAP/SIGABRT from
  runtime allocation traps under `(deny default)`).
  `data.sandbox_log_capture.deny_events` carries the matching
  unified-log evidence when available.
- `runner_timeout` — worker did not flip `done` within the host's
  sentinel deadline. The host SIGKILLs the worker before replying.
- `runner_failed` — worker exited cleanly but didn't reach `done`,
  or hit a non-fatal failure mode that doesn't fit the other
  outcomes. Reachable only as a defense-in-depth path; no
  deterministic specimen produces it.
- `worker_spawn_failed` — host could not `posix_spawn` the worker
  (filesystem/codesign/quota error). Worker never ran.
- `validator_spawn_failed` — host could not `posix_spawn` the
  validator child. `result.ok=false`; attempts are still surfaced
  in `steps[*].attempt` as degraded evidence.
- `validator_no_reply` — validator started but exited without
  emitting the expected number of verdicts. Partial verdicts (if
  any) appear in `steps[*].sandbox_check`; missing verdicts surface
  as `null`.
- `validator_decode_failure` — validator emitted bytes the host
  couldn't parse as NDJSON verdicts.
- `validator_unavailable` — envelope has attempts but no validator
  ran. Distinct from the failure-mode-specific validator outcomes
  so a consumer can recognize the attempts-only degradation mode.
- `bad_request` — request rejected before any worker spawn. Causes
  include: JSON decode failure, empty `sandbox_check.operation`
  (`validateSandboxChecks`), unsupported top-level field (e.g.
  `instrumentation`), or duplicate `step_id` in the probe plan.
  Unknown `filter.kind` and unsupported `(attempt.kind,
  attempt.action)` combos do NOT produce `bad_request` — they
  downgrade to per-step `prediction_unavailable` and `unsupported`
  respectively (see the per-step sections above).
- `libsandbox_unavailable` — libsandbox could not be opened on this
  host (the host pre-spawn check failed `dlopen`).
- `sandbox_apply_failed` — the C worker wrote a non-zero `apply_rc` to
  shared memory before exiting. This covers **both** a failed
  `sandbox_compile_string` and a failed `sandbox_apply`: the worker
  writes `apply_rc = -1` either way and does not distinguish them, so a
  policy that won't compile lands here too (the controller no longer
  turns compile errors into `bad_policy`). `error` reads
  "sandbox_apply returned -1 inside pw-probe-runner"; run `sbpl-check`
  directly for the specific libsandbox compile diagnostic.
- `already_ran` — the XPC service instance only accepts one
  `runSpecimen` call. A second call returns this error.

`xpc_error`, `xpc_timeout`, `xpc_proxy_type_mismatch`, and
`xpc_no_reply` are synthesized by `pw-runner-client` when the XPC
peer itself can't be reached. Rare in practice — the unsandboxed
host always replies unless launchd or codesign reject the bundle
outright.

## What PolicyWitness understands

### Filter kinds the runner predicts

The runner predicts (asks `sandbox_check` about) these filter kinds:
`none`, `path`, `global_name`, `local_name`,
`iokit_registry_entry_class`, `iokit_user_client_class`,
`sysctl_name`. Specimens are free to author probes with other
filter kinds (`preference_domain`, `mach_port`, anything else SBPL
accepts) — those steps short-circuit to
`step.sandbox_check.outcome = "prediction_unavailable"` with
`rc == -1` per-step. The plan is not rejected; sibling steps with
predicted kinds run normally and the attempt for the
unpredicted step still produces evidence.

### Filter kinds where prediction is unavailable

Even within the predicted set, some `(operation, filter_kind)` pairs
have a documented mismatch between `sandbox_check`'s userland
verdict and the kernel's actual enforcement. For these, the runner
accepts the filter in specimens (so policies can be authored),
accepts and enforces the policy correctly at compile/apply time,
but skips `sandbox_check` entirely and emits the same
`prediction_unavailable` shape as for unknown filter kinds. The
attempt still runs and provides the real evidence.

The contract is keyed on the `(operation, filter_kind)` pair, not on
the filter kind alone — a filter kind that drifts for one operation
may behave correctly with another, and the verification is
op+filter-specific. A specimen pairing one of these filter kinds with
a DIFFERENT operation gets a normal `sandbox_check` call; the
prediction may still be wrong, but the runner doesn't override a
prediction it hasn't verified to be wrong.

Currently in this category:

- `(iokit-open-service, iokit_registry_entry_class)` — verified
  2026-05-29 unreliable across all candidate filter IDs in 1..200
  against `IOSurfaceRoot`. The runner short-circuits
  `sandbox_check.outcome` to `prediction_unavailable` (`rc=-1`); the
  C-worker orchestrator omits the probe from the validator batch.
- `(iokit-open-user-client, iokit_user_client_class)` — verified
  2026-05-29 with policy filter `IOSurfaceRootUserClient` and probe
  target `IOSurfaceRoot`. `iokit-open-user-client` is the SBPL
  operation `iokit-user-client-class` matches against (see Apple's
  `/System/Library/Sandbox/Profiles/application.sb` for canonical
  usage); `iokit-open-service` is a sibling operation that fires for
  the IOService class itself.
- `(sysctl-read, sysctl_name)` — verified 2026-05-29 unreliable
  across all candidate filter IDs in 1..200 against `kern.osrelease`.
  Confirms the drift pattern is not iokit-specific.

Adding a pair to this set requires empirical verification via
`tests/suites/witness_contract/harness/verify_filter_id.sh`. The
matching code lives in
`runner/Sources/PWRunnerCore/ProbeRunner.swift::predictionUnavailableOpFilters` and is
mirrored host-side by
`runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift::predictionUnavailableOpFiltersHostMirror`;
both lists must agree (source_drift enforces).

### Attempt kinds the runner implements

The C worker implements these `(attempt.kind, attempt.action)`
combinations:

- `("file", "open_read" | "open_write" | "create" | "unlink" | "access")` — exercise file ops on `target`.
- `("mach_lookup", "bootstrap_look_up")` — `bootstrap_look_up` on `target`.
- `("sysctl", "read")` — `sysctlbyname(target, ...)` read of a sysctl name such as `kern.osrelease`.
- `("exec", "spawn")` — `posix_spawn(target, argv, ...)` of a helper
  binary. `target` is the absolute path to the helper (becomes
  argv[0]). Optional `args: ["…", …]` supplies argv[1..N]; capped at
  15 entries with each entry up to 127 UTF-8 bytes (the ABI's
  `argv_count` includes argv[0], the per-entry budget reserves a
  trailing NUL). The runner pre-creates stdout/stderr pipes
  pre-apply (so the post-apply syscall surface stays minimal — see
  [Augments](#augments) → `exec_baseline` for the policy contract),
  drains both streams interleaved while the child runs, reaps via
  `waitpid`, and surfaces these fields under `attempt`:

  | field | populated when | sentinel when not | semantics |
  | --- | --- | --- | --- |
  | `child_pid` | spawn produced a child (helper ran, success or non-zero exit) | `0` — spawn blocked / target missing / setup failed | The drift classifier keys on `child_pid==0` + `errno∈{EPERM,EACCES}` to attribute a sandbox-denied spawn vs `child_pid>0` for a helper non-zero exit (treated as non-policy failure). |
  | `child_exit_code` | child clean-exited | `-1` — child was signaled or no child ran | |
  | `child_term_signal` | child killed by a signal | `0` — clean-exited or no child ran | |
  | `stdout` / `stderr` | stream produced bytes | key omitted (no stream output) | Captured up to 1023 bytes per stream; output past the buffer is truncated and tagged with a trailing `\n... [truncated]` marker. |
  | `rc` | always populated | (n/a) | Helper's exit code on spawn success (`rc==0` means the helper itself reported success); `-1` when spawn failed. |
  | `outcome` | always populated | (n/a) | `"ok"` when spawn succeeded AND the helper exited 0; `"exec_failed"` for every other terminal state (spawn-blocked, target missing, helper non-zero exit, helper signaled). |

  A minimal `(deny default)` policy will block `posix_spawn` itself.
  Callers who want exec attempts to succeed under a deny-by-default
  policy opt into `policy.augments: ["exec_baseline"]` (see
  [Augments](#augments)) — three `(allow ...)` rules are sufficient
  to let a libSystem-dynamic helper spawn, load dyld, and reach
  `main`. Callers who need to allow more (network, IOKit, specific
  filesystem subpaths) compose their own additional allows on top
  of the augment.

  The runner also enforces a bounded per-exec deadline (10 seconds
  by default) so a hung helper can't escalate into a worker-level
  sentinel timeout. When the deadline fires the worker SIGKILLs the
  child's process group and surfaces `outcome="exec_failed"` with
  `child_term_signal=9` and `error` containing
  `"child exceeded N-second deadline; SIGKILL'd"`. The helper is
  spawned with `POSIX_SPAWN_CLOEXEC_DEFAULT` (so it inherits only
  the runner's stdin=/dev/null + stdout/stderr pipes — no shm fd,
  no policy fd, no other exec slots' pipes) and an empty
  environment.

  Note that `data.runner_sandbox_diagnostics.first_deny` does NOT
  identify the denied syscall for an exec attempt — that
  diagnostic fires only for the `runner_sandbox_denied` outcome and
  is PID-scoped to the worker, not its children. Per-child deny
  correlation is a separate enhancement.

Specimens are free to author probes with other attempt combinations
(`("iokit", "open")`, future kinds, etc.) — those steps surface
`step.attempt.outcome = "unsupported"` per-step. The `sandbox_check`
verdict for the same step still runs normally; only the attempt
slot is no-op'd. `steps[].drift` is `null` for unsupported attempts
(no attempt verdict to compare against).

## Operating

### Common flags

- `--timeout-ms <n>`: runner RPC timeout (default 240000)
- `--log-last <dur>`: unified log lookback window for deny capture (default 10s)
- `--no-log-capture`: skip the unified-log (`log show`) deny scan. The scan is
  archive-bound and costs seconds per run independent of `--log-last`, so pass
  this when you don't consume `data.sandbox_log_capture` (or the
  `first_deny` diagnostic it backs) and want the per-run cost back.
  `data.sandbox_log_capture` is then `null`.
- `--runner-mode <standard|byoxpc>`: inject `runner.mode` into the request

### Debug-attach to the worker

To pause the worker for a debugger attach, set
`_test_overrides.worker_post_apply_hang_ms: <N>` on the request. The
C worker stays alive for `N` ms after applying the policy, giving
you an `lldb -p <runner_subprocess.pid>` window. The same seam
backs `tests/suites/witness_contract/worker_post_apply_hang_seam.sh`.

Custom dylib injection, JIT, DYLD env, and other entitlement-backed
inspection paths go through BYOXPC: install a signed `.xpc` bundle
with the entitlements you need and select it via `runner.id` or
`runner.service`. To set `DYLD_*` env vars, supply them at install
time:

```sh
$PW runner install --kind byoxpc --bundle /path/to/MyRunner.xpc --env DYLD_INSERT_LIBRARIES=/path/to/lib.dylib
```

### Troubleshooting

- Service not found: run `policy-witness runner list` and confirm the service name.
- System scope install fails: use `--scope user` or run with admin privileges.
- Verify fails with no reply: check launchd state and the service plist.
- BYOXPC crashes at launch: confirm `XPC_SERVICE_PATH` is set and the bundle is a valid XPC service (`CFBundlePackageType=XPC!`).
- `normalized_outcome` is `runner_sandbox_denied` and you expected
  `ok`: uncommon. The C worker's post-apply syscall surface is small
  (just shared-memory stores and a nanosleep), so most `(deny default)`
  policies don't actually kill it. The residual cases that do produce
  this outcome are policies that explicitly deny one of the syscalls
  in the worker's post-apply path, or kernel-issued aborts on the
  worker process for an unrelated reason. The worker was terminated
  by a fatal signal before flipping its `done` sentinel.
  - **Quickest read:** `data.runner_sandbox_diagnostics.first_deny` carries
    the first kernel deny attributed to the worker PID — `operation`,
    `path` if applicable, and the raw unified-log line. Use this when you
    want one line that names the cause.
  - `data.runner_sandbox_diagnostics.first_deny` is `null` when log capture
    was blocked/unavailable or when no deny event matches the worker PID
    (rare; usually means the capture window missed the event). The outer
    `runner_sandbox_diagnostics` object is present whenever the outcome is
    `runner_sandbox_denied`, so consumers can branch on `first_deny != null`
    directly.
  - For the full deny list (when one isn't enough), see
    `data.sandbox_log_capture.deny_events`.
  - `data.runner_result.runner_subprocess.term_signal` carries the
    exit signal. The C worker has a minimal post-apply syscall
    surface (shm writes only), so most `(deny default)` policies
    don't actually kill it; if you see `runner_sandbox_denied`, the
    `first_deny` line usually names the specific operation the
    policy needs to allow.
- `normalized_outcome` is `worker_spawn_failed`: the host could not
  `posix_spawn` the worker. Verify the bundle is signed and on a writable
  filesystem; `pgrep -fl PWRunner` should show no stragglers.
- If you are running inside a sandboxed automation harness, XPC lookup can be blocked;
  run from a normal Terminal to confirm behavior.

Common decode errors (quick fixes)
- `missing field 'policy'`: add a top-level `policy` object with `format` and `sbpl_source`.
- `keyNotFound(... "specimen_id" ...)`: add a top-level `specimen_id` string.
- `unknown field 'path_membership'`: path rules belong in `policy.sbpl_source` as SBPL, not as JSON fields.
- `runner.mode=debuggable` or top-level `instrumentation` field rejected:
  these are not supported. Install a BYOXPC runner with the entitlements
  you need and select it via `runner.id` or `runner.service`.

## External runners (BYOXPC)

Use this when you need entitlements that are not in the built-in runner.
BYOXPC is the only external runner kind.

### What you need

- A runner `.xpc` bundle to sign (typically a copy of `PWRunner.xpc`).
- A signing identity (Developer ID Application) or ad-hoc signing for local use.
- An entitlements plist.
- A logged-in GUI session (launchd bootstrap is not available from non-GUI shells).

### Tested install path (copy/paste)

This sequence matches `tests/suites/runner_byoxpc/run.sh` and is the
recommended starting point.

```sh
PW="$PWD/dist/PolicyWitness.app/Contents/MacOS/policy-witness"
IDENTITY="Developer ID Application: Your Name (TEAMID)"
ENT="$PWD/path/to/your-byoxpc-entitlements.plist"
BYO="$PWD/runtime/byosig/instances/PWRunner.byoxpc.xpc"

mkdir -p "$(dirname "$BYO")"
rm -rf "$BYO"
cp -R dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc "$BYO"

$PW runner install --kind byoxpc \
  --bundle "$BYO" \
  --identity "$IDENTITY" \
  --entitlements "$ENT" \
  --allow-adhoc \
  --scope user

$PW runner verify --service-name com.yourteam.policy-witness.PWRunner --timeout-ms 2000
```

### Install a BYOXPC runner

```sh
$PW runner install \
  --kind byoxpc \
  --bundle /path/to/MyRunner.xpc \
  --identity "Developer ID Application: Your Name (TEAMID)" \
  --entitlements /path/to/entitlements.plist \
  --scope user
```

Notes:
- Use `--allow-adhoc` for local ad-hoc signing.
- Use `--scope system` if you want a system-wide service (requires admin).
- Use `--skip-bootstrap` if you will run `launchctl` manually.
- Use `--env KEY=VALUE` to set launchd `EnvironmentVariables` (for `DYLD_*`).
- BYOXPC service name must match the bundle's `CFBundleIdentifier` (no override).
- The bundle must be a valid XPC service (`CFBundlePackageType=XPC!`); plain
  binaries are rejected at install time. The executable is derived from
  `<bundle>/Contents/MacOS/<CFBundleExecutable>`.
- `--entitlements` requires either `--identity <id>` or `--allow-adhoc` so the
  supplied entitlements are actually re-embedded into the binary. Passing
  `--entitlements` without one of those is rejected — the registry would
  otherwise record entitlements that the kernel will not enforce.

The install command writes a launchd plist, bootstraps the service, and records
the runner in the local registry. The registry's `entitlements` field always
reflects what's embedded in the binary (read back via `codesign -d --entitlements`),
not what was supplied on the command line.

### Verify the runner

```sh
$PW runner verify --service-name <service-name>
```

`runner verify` defaults to a 5-second timeout; pass `--timeout-ms <n>` for
slow cold-spawn cases.

### Use the runner in a specimen

Preferred: include a `runner` object:

```json
"runner": {
  "id": "runner-<id-from-install>",
  "mode": "byoxpc",
  "required_entitlements": [
    "com.apple.security.cs.disable-library-validation"
  ]
}
```

Alternative: select by service name:

```json
"runner": {
  "service": "com.yourteam.policy-witness.PWRunner",
  "mode": "byoxpc"
}
```

`runner.mode` is optional; when present it must equal `byoxpc` for external
runners. Valid modes: `standard`, `byoxpc`. `required_entitlements` enforces
a superset check before dispatch.

Quick smoke request (save as `/tmp/pw_byoxpc_smoke.json`):

```json
{
  "schema_version": 1,
  "specimen_id": "byoxpc_smoke",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (deny default)"
  },
  "probe_plan": [],
  "runner": {
    "service": "com.yourteam.policy-witness.PWRunner",
    "mode": "byoxpc"
  }
}
```

Then run:

```sh
$PW run /tmp/pw_byoxpc_smoke.json --timeout-ms 20000
```

### List, validate, or remove runners

```sh
$PW runner list
$PW runner validate
$PW runner remove --id runner-<id>
```

External runners install a launchd background item. `runner remove` is the
preferred uninstall path and removes the launchd entry and registry record.
It is also self-healing: if `launchctl bootout` fails (e.g. the service was
already booted out) or the plist file is already gone, the registry entry is
still removed and the failure is surfaced in the envelope's `data.warnings`
array. This means `remove` is safe to call defensively before a fresh
`install`.

`runner validate` re-reads each registry entry's on-disk signature and
entitlements (registry-internal only — it does not reconcile against launchctl
or `LaunchAgents/`).

`runner status`, `runner verify`, and `runner remove` emit an envelope with
`result.normalized_outcome = "not_found"` and exit code 2 when the lookup key
isn't present in the registry; the envelope `kind` still matches the operation
so consumers can dispatch by `kind` and then branch on `normalized_outcome`.

If you no longer have the registry entry, uninstall manually:

User scope:

```sh
launchctl bootout "gui/$(id -u)/<service-name>"
rm -f "$HOME/Library/LaunchAgents/<service-name>.plist"
```

System scope:

```sh
sudo launchctl bootout "system/<service-name>"
sudo rm -f "/Library/LaunchDaemons/<service-name>.plist"
```

Registry location:

```
~/Library/Application Support/PolicyWitness/runners.json
```
