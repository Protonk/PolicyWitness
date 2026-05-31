# Attempt-kind plan

## Context

After Phase 1, PolicyWitness supports three curated attempt kinds:
`file`, `mach_lookup`, and `sysctl`.
Real macOS sandbox profiles author rules across many more operations; an
external corpus survey of 627 profiles ranked twelve `sandbox_check` kinds by
how often each is authored and rated each against five executability /
determinism / safety gates (full analysis:
`/Users/achyland/Desktop/Security/PAWL/integration/harvest/attempts/ATTEMPT-KIND-ENUMERATION.md`).

The honest distribution is:

- **3 well-behaved kinds (wire):** `file`, `mach_lookup`, `sysctl_read`.
  Single syscall family, public API, errno-clean failure, stable target.
  Cover 82% / 59% / 11% of the corpus respectively. All three are
  now represented by built-in attempt kinds.
- **7 messy kinds (case-work):** `generic`, `iokit`, `ipc`, `mach`, `process`,
  `socket`, `user_preference`. Each kind is a heterogeneous bucket whose
  constituent ops need per-op target hygiene, recipe authoring, and safety
  judgment that PW can't make on the caller's behalf.
- **3 unsafe kinds (never):** `network`, `signal`, `system`. Fail
  executability / determinism / non-destructiveness gates architecturally.

The hybrid plan: **enumerate the wire tier in PW; ship an `exec` extension
point for the case-work tier; the never tier remains unsupported.** Phase 1
covered the third well-behaved kind (`sysctl_read`). Phase 2 adds the `exec`
kind plus a named-augment interface (`policy.augments:
["exec_baseline"]`) so callers can author their own per-op probes for the
case-work tier without importing each op's safety burden into PW source.

Goal across both phases: PW commits to one curated atlas of three attempt
kinds plus one open-ended extension mechanism. PW does not chase Apple's
syscall surface; it provides a stable harness inside which callers exercise
the surface they care about.

---

## Phase 1 — Add `sysctl_read` as the third wire-tier attempt kind (complete)

**Status: complete.** This phase is implemented in the current worktree:
`PW_ATTEMPT_SYSCTL_READ = 7`, Swift `PWAttemptKind.sysctlRead = 7`,
`attempt.kind="sysctl" / action="read"`, `AttemptOutcome.sysctlFailed`
(`"sysctl_failed"`), drift-classifier handling for sysctl errnos, real
Channel A coverage in `runner_filter_sysctl_name`, and source-drift
enforcement for C/Swift attempt-kind enum agreement.

Validated with:

- `git diff --check`
- `swift build --package-path runner`
- `IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' make build`
- `tests/run.sh --suite source_drift --suite runner_unit --suite runner_filter_sysctl_name`
- `tests/run.sh --suite runner_c_worker_harness`
- `tests/run.sh --suite runner_use_c_worker`

The original implementation shape was: small, well-scoped, no ABI risk.
It closes the third corpus-frequency wire-tier op and replaces the
placeholder `file open_read` attempt currently used by
`runner_filter_sysctl_name` (the suite that pins the
prediction-unavailable behavior for `(sysctl-read, sysctl_name)`) with a
real sysctl probe.

### Wire surface

- `runner/PWRunnerAPI.swift::PWRunnerWire`
  - `static let attemptKindSysctl = "sysctl"`
  - `static let attemptActionRead = "read"`
- Request shape: `attempt: { kind: "sysctl", action: "read", target: "<sysctl-name>" }`.
  `target` is the sysctl name (e.g. `"kern.osrelease"`); no second arg.

### C worker

- `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`
  - Append `PW_ATTEMPT_SYSCTL_READ = 7` to `pw_attempt_kind_t`. Append-only;
    no ABI version bump per the existing rule for adding enum values without
    structural changes.
- `controller/tools/pw_probe_runner/pw_probe_runner.c`
  - New `case PW_ATTEMPT_SYSCTL_READ:` in `run_attempt`. Implementation:
    a single fixed-buffer read via
    `sysctlbyname(target, buf, &buf_len, NULL, 0)` where `buf_len`
    is initialized to `sizeof(buf)` on every call (4 KiB stack buffer
    is plenty for typical sysctl values). Write `rc / errno_val /
    error` into the slot per the existing convention. The value bytes
    are discarded — only success/failure + errno matters for the
    attempt verdict.
  - **Do NOT use the two-call size-probe pattern.** Calling
    `sysctlbyname(target, NULL, &len, NULL, 0)` first to size-probe
    and then re-using `len` for the read is unsafe: if the value
    grew between the two calls, or if the caller forgot to reset
    `len` to the buffer size, the second call would write past the
    buffer. Skip the probe; if a real value exceeds the fixed
    buffer the kernel returns `ENOMEM` and we report it as a sysctl
    failure (acceptable — the test is about sandbox attribution,
    not about reading the value).

### Swift / orchestrator

- `runner/CWorker.swift::PWAttemptKind`: add `sysctlRead = 7` (value
  matches the C enum).
- `runner/CWorkerOrchestrator.swift::mapAttemptKindOrNil`: add
  `case (PWRunnerWire.attemptKindSysctl, PWRunnerWire.attemptActionRead): return .sysctlRead`.
- `runner/PWRunnerAPI.swift::AttemptOutcome`: add
  `static let sysctlFailed = "sysctl_failed"`. Follows the existing
  per-op-family failure-name convention (`open_failed`, `unlink_failed`,
  `access_failed`, `lookup_failed`).
- `runner/CWorkerOrchestrator.swift::buildAttemptResult`: add
  `case PWRunnerWire.attemptActionRead: return AttemptOutcome.sysctlFailed`
  to the rc != 0 dispatch.
- `runner/CWorkerOrchestrator.swift::observationFromAttempt` (or the
  equivalent drift-classifier helper): add explicit handling for
  `sysctl_failed`. Without this, drift falls through to `null` for
  any sysctl probe whose attempt failed. The categorization:
  - `errno ∈ {EPERM=1, EACCES=13}` → **ambiguous deny** (could be
    sandbox-policy or could be a privileged-only sysctl). Same
    treatment as file open/access EPERM/EACCES, so a
    `(validator=allow, attempt=ambiguous-deny)` step reports
    `drift=null` rather than `drift=true` (avoids false
    libsandbox-drift attribution on root-only sysctls).
  - `errno == ENOENT` → **non-policy failure** (sysctl name doesn't
    exist on this host). Categorized as not-a-sandbox-event;
    `drift=null` regardless of validator verdict.
  - `errno == ENOMEM` → treat as non-policy failure too (value
    exceeded our buffer; not a sandbox event).
  - All other errno values → **strong deny** (treated as a
    sandbox-attributable failure, so a `(validator=allow,
    attempt=strong-deny)` step reports `drift=true`).

### Tests

- `runner/Tests/PWRunnerCoreTests/CWorkerTests.swift`
  - New unit test: drive the C worker with a `(allow default)` policy and
    a `sysctl_read` attempt on `kern.osrelease`; assert
    `attempt.outcome == "ok"` and slot rc=0.
  - New unit test: drive with `(deny default) (allow sysctl-read (sysctl-name "kern.osversion"))`
    and a `sysctl_read` attempt on `kern.osrelease`; assert
    `attempt.outcome == "sysctl_failed"` with errno EPERM or EACCES.
- `tests/suites/runner_filter_sysctl_name/run.sh`
  - Swap the placeholder `file open_read` attempt for a real
    `sysctl read kern.osrelease` attempt. The suite already pins
    `sandbox_check.outcome == "prediction_unavailable"`; the upgrade is
    that the attempt becomes a real sysctl probe, closing the
    "no Channel A coverage of sysctl-read" caveat in its README.

### Docs

- `PolicyWitness.md` "Attempt kinds the runner implements" section:
  add the `("sysctl", "read")` row with one sentence on shape.
- `tests/INDEX.md` AttemptOutcome matrix: add the `sysctl_failed` row
  pointing at the new unit test as primary coverage.
- `tests/suites/runner_filter_sysctl_name/README.md`: drop the
  "no Channel A coverage of sysctl-read today" caveat; the attempt is
  now a real sysctl read.

### Source-drift guard for attempt-kind enums

`PW_ATTEMPT_*` (in `pw_probe_runner_abi.h`) and `PWAttemptKind` (in
`runner/CWorker.swift`) must agree on both the set of values and the
numeric value for each name. Today nothing enforces this: a
contributor could append `PW_ATTEMPT_SYSCTL_READ = 7` in C and
forget the Swift `sysctlRead = 7` (or vice versa), and runtime would
fail late with cryptic shm misalignment.

- `tests/suites/source_drift/check.py`
  - New `check_attempt_kind_enum_agreement()` parser. Extracts the
    `(name, value)` pairs from each enum (regex over the C
    `pw_attempt_kind_t` block and the Swift `PWAttemptKind` block).
    Asserts the two sets agree on value-by-value: both sides have
    the same numeric range, no gaps, and (after normalizing case)
    matching name suffixes for the same numeric value.
  - Land this guard in the same PR as Phase 1 — adding
    `SYSCTL_READ = 7` is the first time we'd benefit from it, and
    Phase 2 also depends on it for `EXEC_SPAWN = 8`.

### Validation

- `tests/run.sh --suite source_drift --suite unit --suite runner_unit --suite runner_filter_sysctl_name`
- Source-drift counts: 8 attempt outcomes → 9; new
  attempt-kind-agreement check passes; `_Static_assert` on ABI
  region size unchanged.

### Sizing

~30 lines C in `run_attempt`, ~6 lines Swift wire, ~15 lines orchestrator
(map + outcome + drift classifier), ~50 lines tests, ~15 lines docs,
~40 lines Python in source_drift for the new enum-agreement check.
One PR, no notarization risk beyond the standard rebuild.

---

## Phase 2 — Add `exec` attempt kind + named-augment interface

The case-work escape hatch. The caller ships a helper binary that does the
one operation under test; PW provides the spawn frame, captures
rc / term_signal / stdout / stderr, and surfaces the result the same way
file / mach_lookup / sysctl_read do. The augment interface gives the caller
a clean opt-in for the SBPL baseline `posix_spawn` needs.

Phase 2 ships as four checkpoints, each independently buildable and
testable. Sequencing is strict — later checkpoints assume earlier ones
have landed:

1. **Controller augment plumbing (complete).** Added `policy.augments`
   resolution in the controller before `sbpl-preflight`; proved
   request splicing, hash reporting, unknown-name rejection, and
   runner-forwarding behavior with tests.
   `runner/augments/exec_baseline.sb` ships as a **single-line
   comment-only file** (no SBPL rules), so the wire/hash/preflight
   machinery exercises end-to-end without granting any permissions
   yet. Augments are listed in the signed evidence manifest under
   `kind: "augment"`. The user-facing surface
   (`policy.augments`, `data.policy_augmentation`,
   `augments: append-only allow-only`) is documented in
   PolicyWitness.md → Augments.

   *Status: complete.*

   Validated with:
   - `cargo test --bin policy-witness` — augments module unit tests pass
     (7 cases including the strip-without-apply mutation-tracking case
     `stripped_noop_when_empty_array` / `stripped_noop_when_null_field`).
   - `PW_INTEGRATION=1 cargo test --test cli_contract` — augment
     integration cases pass: `augment_applied_emits_policy_augmentation_block`
     (asserts the run reaches `ok`, preflight's `policy_sha256` equals
     `applied_sha256`, and runner's `policy_sha256` equals
     `applied_sha256`); `unknown_augment_short_circuits_to_bad_request`;
     `invalid_augment_name_rejected_as_bad_request`;
     `absent_augments_omits_policy_augmentation_block`.
   - `swift run --package-path runner PWRunnerCoreTests` — `AugmentTests`
     (4 cases) pass.
   - `tests/run.sh --suite source_drift --suite unit --suite runner_unit
     --suite runner_outcome_bad_request --suite runner_use_c_worker
     --suite integration --suite smoke` — clean.
   - `IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' make
     build` — bundle assembled with
     `Contents/Resources/Augments/exec_baseline.sb` present and sealed
     by the outer codesign; `manifest.json` records the augment with
     `kind: "augment"` and a sha256.

2. **ABI v4 layout + layout guard (complete).** Defined the C slot
   layout (`PW_SHM_SLOT_BYTES = 8192`), Swift offsets, bounds, and the
   new `runner_abi_layout` suite that compiles a C printer and asserts
   agreement against `PWShmLayout`. Landed before the exec runtime
   behavior so any future C/Swift offset drift is a mechanical test
   failure, not a runtime artifact. ABI version bumped 3 → 4;
   `PW_ATTEMPT_EXEC_SPAWN = 8` reserved at the wire level but the
   worker doesn't dispatch to it yet (the exec output fields are
   zero-initialised by the host's pre-spawn memset and no run_attempt
   case writes them — the eventual sentinel conventions ship with the
   runtime in checkpoint 3).

   *Status: complete.*

   Validated with:
   - `cargo build --manifest-path controller --release` — `pw-probe-runner`
     compiles against the new struct; `_Static_assert` confirms the slot
     budget at 8192.
   - `swift build --package-path runner` — `PWShmLayout` compiles;
     `PWAttemptKind.execSpawn = 8` mirrors C.
   - `tests/run.sh --suite runner_abi_layout` — 46 C↔Swift layout
     values agree; `diff.json` shows zero mismatches and no
     missing-in-either-direction entries.
   - `tests/run.sh --suite source_drift --suite runner_unit
     --suite runner_c_worker_harness --suite runner_use_c_worker
     --suite runner_outcome_bad_request --suite integration
     --suite smoke` — 24/24 pass against the v4 bundled worker
     (49/49 in `runner_unit`; the 256-slot harness test passes against
     the larger 2.6 MiB region).
   - `IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' make
     build` — bundle assembled; the bundled `pw-probe-runner` reports
     `abi=4 slot_bytes=8192`.

3. **Exec runtime (complete).** Implemented the narrow `exec` /
   `spawn` attempt with bounded argv, child status capture
   (child_pid / child_exit_code / child_term_signal), stdout/stderr
   capture with truncation marker, monotonic per-exec deadline +
   SIGKILL of the child process group on expiry,
   POSIX_SPAWN_CLOEXEC_DEFAULT + /dev/null on stdin so the child
   inherits no worker-internal fds, empty envp for hermetic
   environment, absolute-path enforcement on the target, and the
   child_pid sentinel-keyed drift classifier (sandbox-blocked spawn
   → strong deny; helper non-zero exit → non-policy failure).

   *Status: complete.*

   Validated with:
   - `cargo test --bin policy-witness` — clean.
   - `swift run --package-path runner PWRunnerCoreTests` — 59/59
     (10 new exec unit tests including the load-bearing
     deny-default spawn pin, the deadline-fires SIGKILL pin, the
     absolute-path rejection pin, and the empty-env pin).
   - `tests/run.sh --suite runner_use_c_worker` —
     `exec_attempt_without_baseline_fails_cleanly` passes: drives
     the orchestrator+wire path against `(deny default)` + exec
     `/usr/bin/true`, asserts `child_pid==0` +
     `errno∈{EPERM,EACCES}` + `error contains "posix_spawn"`.
   - `IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
     make build` — clean rebuild + sign.

4. **Empirical `exec_baseline` (complete).** Authored the actual
   `runner/augments/exec_baseline.sb` contents — three rules
   (`(allow process-exec*)`, `(allow process-fork)`, `(allow
   file-read*)`) — empirically derived against
   `tests/suites/runner_use_c_worker/exec_fixture/helper.c` on
   macOS 14.8.3 (build 23J220, Darwin 23.6.0). Documented the
   authoring protocol + composition limits + per-os derivation
   transcript in
   `runner/augments/README.md`. Added e2e cases
   (`exec_attempt_with_baseline_succeeds`,
   `exec_attempt_args_and_stderr_round_trip`,
   `exec_attempt_stdout_truncation_marker`) that pin the
   user-facing promise that `augments: ["exec_baseline"]` lets a
   libSystem-dynamic helper spawn cleanly under `(deny default)`.

   *Status: complete.*

   Validated with:
   - `tests/run.sh --suite runner_use_c_worker` — 13/13 (10
     pre-existing + 3 new exec_baseline e2e cases).
   - Bundle signed with the new augment;
     `Contents/Resources/Augments/exec_baseline.sb` carries the
     three-rule content; evidence manifest records the new sha256.

Each checkpoint should land as a separate PR (or at least a separate
commit) so the bisect history is clean and any individual checkpoint
is independently revertible.

### Wire surface — attempt

- `runner/PWRunnerAPI.swift::PWRunnerWire`
  - `static let attemptKindExec = "exec"`
  - `static let attemptActionSpawn = "spawn"`
- `runner/PWRunnerAPI.swift::PWRunnerAttempt`
  - Add `public var args: [String]?` (optional argv beyond argv[0];
    helper paths interpret it).
- Request shape: `attempt: { kind: "exec", action: "spawn", target: "<path-to-helper>", args: ["..."] }`.
  `target` must be an absolute helper path in Phase 2. `args` is
  bounded by count and per-argument byte length in the worker ABI.
  No environment field is added initially; the worker should use an
  explicit empty/minimal environment unless implementation discovers
  a macOS loader requirement that must be documented.

### Wire surface — augments

- `runner/PWRunnerAPI.swift::PWRunnerPolicySpec`
  - Add `public var augments: [String]?` (optional; nil treated as []).
- `controller/src/run_flow.rs` (envelope synthesis): add a new
  `data.policy_augmentation` block emitted only when augments were
  applied:
  ```json
  "policy_augmentation": {
    "applied": ["exec_baseline"],
    "original_sha256": "<hash of caller's source as submitted>",
    "applied_sha256":  "<hash of source after augments appended>"
  }
  ```
  - The existing `runner_result.policy_sha256` field continues to
    report what the runner actually compiled (which, when augments
    were applied, equals `applied_sha256`). A consumer that wants
    "what the caller submitted" reads `policy_augmentation.original_sha256`.

### Augment storage + resolution

**Augment resolution lives in the controller, NOT the runner.** This is
the audit fix: if the runner spliced augments after the controller
already ran `sbpl-preflight` on the caller's source, the preflight
would describe the wrong policy (could say "compiled" for a source
that the runner then can't compile after the augment is appended,
or vice versa). Putting splicing in the controller means preflight
sees the spliced source.

- New app-level directory `dist/PolicyWitness.app/Contents/Resources/Augments/`
  containing one file per shipped augment (initially
  `exec_baseline.sb`). App-level rather than XPC-bundle-local so the
  controller can read it without descending into the XPC service.
- `build.sh` copies `runner/augments/*.sb` (repo source-of-truth) into
  `dist/PolicyWitness.app/Contents/Resources/Augments/` and signs the
  directory contents as part of the app bundle. Augments are
  resources, not executables.
- `controller/src/run_flow.rs`
  - After reading the request and BEFORE invoking `sbpl-preflight`,
    inspect `request.policy.augments`. If non-empty:
    1. Validate each name (must be alphanumeric + underscore; resolves
       to `<app>/Contents/Resources/Augments/<name>.sb`).
    2. Unknown name → return tool_error envelope immediately
       (`normalized_outcome = "bad_request"`,
       `error = "unknown augment '<name>'"`); the runner is never
       invoked.
    3. Read each augment file; append its contents to
       `request.policy.sbpl_source` (joined with a `\n`).
    4. Compute `original_sha256` from the caller's source and
       `applied_sha256` from the spliced source.
    5. Strip the `augments` field from the request before forwarding
       (so the runner sees a plain `policy.sbpl_source` and has no
       augment-aware code path).
  - Forward the spliced request to `sbpl-preflight` and then to the
    runner. Preflight now describes the policy that will actually be
    applied.
  - When assembling the envelope, emit `data.policy_augmentation`
    when augments were applied.
- The runner is augment-agnostic. `PWRunnerService.runSpecimen` sees
  a normal request, computes `policy_sha256` over the source it
  received (which is the spliced source), and runs it.

### Augment conflict semantics

Augments are appended after the caller's source. SBPL is last-match-wins,
so an augment's `(allow process-exec)` overrides a caller's earlier
`(deny process-exec)`. The contract:

- **Augments are append-only and allow-only.** Each shipped augment
  contains only `(allow ...)` rules. The augment author commits to not
  emitting `(deny ...)`.
- **Augment allows override caller denies for the operations the
  augment covers.** This is the SBPL semantic, and we don't fight it:
  a caller opting into `exec_baseline` consents to having
  `process-exec` and the supporting file-reads allowed even if their
  source denied them. Documented loudly so no one is surprised when
  a `(deny process-exec)` in their source is no-oped.
- **Plan validation does not warn about overlap.** We considered
  cross-referencing the augment's allow set against the caller's
  deny set and emitting a warning when they overlap, but it requires
  parsing SBPL on the controller side (which today we don't do —
  `sbpl-preflight` calls into libsandbox). Punt that to a future
  enhancement if the implicit-override semantic actually bites
  someone in practice.
- **Test coverage for this rule** lives in
  `controller/integration/cli_contract.rs`: a case asserting that a
  caller-authored `(deny process-exec)` plus `augments: ["exec_baseline"]`
  results in the exec attempt succeeding (augment wins, as documented).

### exec_baseline contents — to be authored empirically

The augment's exact SBPL is **NOT specified in this plan.** macOS's
spawn / dyld / shared-cache / code-signing syscall surface is non-obvious
and resists a-priori enumeration; a "rough" list (`(allow process-fork)`,
`(allow process-exec*)`, file-reads on `/usr/lib` etc.) almost certainly
under- or over-grants. The author of Phase 2 implements `exec_baseline.sb`
iteratively against a real test fixture:

1. Build a tiny test helper that calls `_exit(0)` and nothing else.
2. Author a starting-point `exec_baseline.sb` based on what's
   documented in Apple's `application.sb` for spawn support.
3. Drive a specimen: `(version 1)(deny default)` plus
   `augments: ["exec_baseline"]` plus an `exec` attempt targeting the
   helper.
4. If the spawn fails, the worker captures the spawn errno (typically
   EPERM with no further context). The author then runs the same
   specimen WITHOUT the C worker's sandbox (e.g. directly via
   `sandbox-exec` against the same compiled policy and a manual
   `posix_spawn` of the helper), captures the unified-log denies via
   `log stream`, and adds the missing `(allow ...)` rules to the
   augment.
5. Repeat until the helper spawns cleanly. Commit the resulting augment
   alongside a reproducible recipe in `runner/augments/README.md`
   documenting how it was derived and which deny lines drove each
   `(allow ...)` rule.
6. The augment author MUST also test against a non-statically-linked
   helper (libSystem-only dynamic binary, the realistic case) since
   true static linking against libSystem isn't supported on macOS.
   The augment needs to cover dyld + shared-cache mapping + code-sign
   verification, not just the literal exec syscall.

### Critical design decision — exec post-apply resources

Decide this before editing the C worker ABI. The existing worker design is
intentionally simple after `sandbox_apply`: fixed inputs, no hidden resource
acquisition, and shared-memory writes as the durable output channel. An exec
attempt complicates that because stdout/stderr capture needs pipes,
`posix_spawn_file_actions`, polling, reads, and child reaping.

Preferred starting model:

- Pre-read exec slot inputs before `sandbox_apply`.
- Pre-create per-exec stdout/stderr pipes before `sandbox_apply`.
- Pre-build or otherwise pre-allocate any `posix_spawn_file_actions`
  state before `sandbox_apply` if the API permits a stable prepared
  representation.
- After `sandbox_apply`, the attempt path should primarily call
  `posix_spawn`, drain already-created pipe FDs, `waitpid`, and write
  results to shared memory.

Reason: if pipe creation or file-action setup happens post-apply, an
unaugmented minimal-deny profile may fail before the operation under test
(`posix_spawn`) is reached. That would blur the witness: the attempt would
report an exec failure, but the observed denial might be pipe/file-action
setup rather than process execution.

If this model fails empirically, make an explicit choice before continuing:

- make pipe / file-action setup part of `exec_baseline` and document that
  unaugmented exec can fail during setup, not only at spawn;
- or defer stdout/stderr capture from Phase 2, keep only child PID/status
  and spawn errno, and add output capture later;
- or pre-create only pipes and keep file-action setup post-apply if testing
  proves that setup is allocation-free and not sandbox-gated in practice.

Do not silently degrade to whichever failure occurs first. The plan and tests
must preserve the difference between "the sandbox blocked spawn" and "the
worker failed to set up the observation frame."

### C worker — exec attempt and ABI v3 → v4 bump

exec needs structural slot changes (argv, child PID, separate
exit_code vs term_signal, stdout/stderr capture). Rather than smuggle
these in via sidechannels, **explicitly bump the worker ABI to v4
with concrete new slot fields.** Single owner of complexity; honors
the existing "structural change = ABI bump" rule.

- `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`
  - `PW_PROBE_RUNNER_ABI_VERSION` 3 → 4.
  - Append `PW_ATTEMPT_EXEC_SPAWN = 8` to `pw_attempt_kind_t`.
  - New optional input fields on `pw_shm_slot_t`:
    - `argv_count: u32` (0..PW_SHM_MAX_ARGV; e.g. 16)
    - `argv: char[PW_SHM_MAX_ARGV][PW_SHM_ARGV_BYTES]` (e.g. 16×128 = 2 KiB)
      — packed argv strings.
  - New optional output fields on `pw_shm_slot_t`:
    - `child_pid: i32` (0 when no child was spawned)
    - `child_exit_code: i32` (-1 when child was signaled or no child ran)
    - `child_term_signal: i32` (0 when child clean-exited or no child ran)
    - `child_stdout: char[PW_SHM_CHILD_OUTPUT_BYTES]` (e.g. 1024)
    - `child_stderr: char[PW_SHM_CHILD_OUTPUT_BYTES]` (e.g. 1024)
  - **Committed slot capacity: `PW_SHM_SLOT_BYTES = 8192`.** Existing
    slot consumes ~1.5 KiB; the new exec fields add ~4.1 KiB (argv
    table ~2 KiB + child_pid/exit_code/term_signal 12 B + child_stdout
    1 KiB + child_stderr 1 KiB), totalling ~5.6 KiB needed minimum.
    8 KiB gives ~2.4 KiB of headroom — room for one or two more
    attempt kinds with similar wire surface before another ABI bump.
    Region size at this value: 64 + 256×8192 + 1024×512 ≈ 2.6 MiB,
    well within a single page-aligned anonymous mapping.
  - Add a layout drift guard. The guard is a tiny C printer compiled
    against `pw_probe_runner_abi.h` at test time, which emits each
    `sizeof()` / `offsetof()` value to stdout as `KEY=VALUE` lines.
    A test driver parses Swift `PWShmLayout` constants and asserts
    line-by-line agreement. Parser-only source_drift over the header
    is insufficient because C struct member offsets depend on
    compiler-applied padding the parser doesn't model. Shape mirrors
    `tests/suites/runner_c_worker_harness/harness.c`: a small C file
    under a new `tests/suites/runner_abi_layout/` suite, compiled
    on demand by the suite driver and run as a subprocess. Manual
    mirrored constants alone are not enough for an ABI bump this
    large.
- `controller/tools/pw_probe_runner/pw_probe_runner.c`
  - Update the version check + region-size math for v4.
  - New `case PW_ATTEMPT_EXEC_SPAWN:` in `run_attempt`. Implementation:
    construct argv from the slot argv table; use the resource-setup
    model chosen above for stdout/stderr; `posix_spawn(target, argv, ...)`
    with pipes dup'd to the child when output capture is enabled; drain
    both pipes with `poll()` until child exits or the bounded child
    deadline fires; `waitpid` and capture exit_code + term_signal into
    the new slot fields. Write `rc = child_exit_code` (0 = success,
    non-zero = failure) and `errno_val = 0` on clean spawn; on spawn
    failure write `rc = -1` and `errno_val = spawn errno`.
  - Truncate stdout/stderr to `PW_SHM_CHILD_OUTPUT_BYTES - 1` and
    NUL-terminate. Add a trailing "... [truncated]" marker when
    content exceeded the buffer. If output capture is deferred, omit
    these fields from Phase 2's response contract and docs instead of
    emitting misleading empty strings.

### Swift / orchestrator

- `runner/CWorker.swift::PWShmLayout`: update `abiVersion` 3 → 4,
  `slotBytes` to the new value, `regionBytes` re-derived. Update the
  offset constants for the new slot fields.
- `runner/CWorker.swift::PWAttemptKind`: add `execSpawn = 8`.
- `runner/CWorker.swift::CWorkerSlotInput`: add
  `optional args: [String]` and validate count + per-arg length
  against the new ABI caps before shm allocation.
- `runner/CWorker.swift::CWorkerSlotResult`: add
  `optional childPid: Int32, childExitCode: Int32?,
  childTermSignal: Int32?, childStdout: String?, childStderr: String?`.
  Read these from the new shm slot offsets. If stdout/stderr capture is
  deferred by the critical design decision above, omit `childStdout` /
  `childStderr` until the ABI actually carries them.
- `runner/CWorkerOrchestrator.swift::mapAttemptKindOrNil`: add
  `case (PWRunnerWire.attemptKindExec, PWRunnerWire.attemptActionSpawn): return .execSpawn`.
- `runner/CWorkerOrchestrator.swift::workerSlotsFromProbePlan`: thread
  `attempt.args` into the slot input for exec attempts.
- `runner/CWorkerOrchestrator.swift::buildAttemptResult`: add
  `case PWRunnerWire.attemptActionSpawn:` returning
  `AttemptOutcome.execFailed` when child rc != 0 or spawn failed;
  populate the new optional response fields with childPid,
  childExitCode/childTermSignal, stdout/stderr from the slot when
  present.
- `runner/CWorkerOrchestrator.swift::observationFromAttempt` (drift
  classifier): treat `exec_failed` with `errno=EPERM` or `EACCES`
  from `posix_spawn` itself as **strong deny** (the sandbox blocked
  spawn — that's a clean signal). Treat setup failures before
  `posix_spawn` and child non-zero exits as **non-policy failure** →
  `drift=null` (the child exit code encodes a verdict the runner has
  no way to interpret).
- `runner/PWRunnerAPI.swift::AttemptOutcome`: add
  `static let execFailed = "exec_failed"`.
- `runner/PWRunnerAPI.swift::PWRunnerAttemptResult`: add optional
  fields `child_pid`, `child_exit_code`, `child_term_signal`,
  `stdout`, `stderr` (Codable; nil for non-exec attempts). Only add
  `stdout` / `stderr` in the same change that implements real bounded
  capture.

### Sandbox-policy interaction (the augment story in practice)

- **Caller wants Apple baseline:** writes `(import "system.sb")` inside
  `sbpl_source` and sets nothing else. PW resolves the import via the
  existing preflight + runtime path; the exec attempt's spawn syscalls
  are satisfied by system.sb.
- **Caller wants minimal-deny test plus exec support:** sets
  `policy.augments: ["exec_baseline"]`. Controller resolves and
  appends; preflight describes the spliced policy; `data.policy_augmentation`
  in the envelope reports what was applied.
- **Caller wants pure minimal-deny (no exec support):** sets nothing.
  exec attempts under a profile that denies spawn syscalls fail with
  `attempt.outcome == "exec_failed"`, `child_pid = 0`, and the slot's
  errno/error fields carry the spawn errno (typically EPERM with
  "posix_spawn: Operation not permitted"). Note that
  `data.runner_sandbox_diagnostics.first_deny` does NOT name the
  denied operation in this case — that diagnostic only fires for the
  `runner_sandbox_denied` outcome and is PID-scoped to the worker,
  not its children. Surfacing per-child deny correlation is a
  separate enhancement (would require either re-scoping log capture
  to include the child PID or having the C worker observe and report
  the deny line itself); not in Phase 2 scope.

### Tests

- `runner/Tests/PWRunnerCoreTests/CWorkerTests.swift`
  - The ABI v4 layout agreement is enforced by the new
    `runner_abi_layout` suite (see "C worker — exec attempt and ABI
    v3 → v4 bump" above), not by a unit test inside the SwiftPM
    target. The suite gates the mirrored Swift `PWShmLayout`
    constants against C `sizeof`/`offsetof` before any exec
    behavior tests run; if the suite fails, no later checkpoint may
    proceed.
  - Unit: drive the C worker with `(allow default)` plus an exec
    attempt invoking `/bin/true`. Assert
    `attempt.outcome == "ok"`, `child_exit_code == 0`,
    `child_term_signal == nil`.
  - Unit: drive with `/bin/false`. Assert
    `attempt.outcome == "exec_failed"`, `child_exit_code == 1`.
  - Unit: drive with `/nonexistent`. Assert
    `attempt.outcome == "exec_failed"`, spawn errno (ENOENT)
    surfaced via `attempt.errno`, `child_pid == 0`.
  - Unit: drive a helper that writes to stdout/stderr and exits 0.
    Assert the captured bytes round-trip via `attempt.stdout` /
    `attempt.stderr` (within the configured truncation). If output
    capture is deferred, replace this with a test documenting the
    absence of output fields.
  - Unit/e2e: pin the chosen post-apply resource setup model. If pipes
    and file actions are pre-created, include a minimal-deny test that
    proves the unaugmented failure is attributable to `posix_spawn`
    rather than setup.
- New unit test file `runner/Tests/PWRunnerCoreTests/AugmentTests.swift`
  - (Augment resolution itself lives in Rust — see the integration
    tests below. Swift-side unit coverage is for `PWRunnerPolicySpec`
    Codable shape, asserting the optional field decodes when present
    and is nil when absent.)
- `controller/integration/cli_contract.rs`
  - Augment resolution: known name appends source; unknown name
    produces tool_error/bad_request without ever invoking the
    runner; `data.policy_augmentation.original_sha256` differs from
    `applied_sha256` when augments applied.
  - Augment conflict: caller authors `(deny process-exec)`, sets
    `augments: ["exec_baseline"]`, exec attempt succeeds — the
    augment's allow wins per the documented contract.
- `tests/suites/runner_use_c_worker/run.sh`
  - New case `exec_attempt_with_augment`: a minimal `(deny default)`
    policy plus `augments: ["exec_baseline"]` plus an exec attempt
    invoking the test fixture helper (see below). Asserts the run
    completes ok, `data.policy_augmentation` reports the augment was
    applied, and the helper's exit code reaches the attempt outcome.
  - New case `exec_attempt_without_baseline_fails_cleanly`: same minimal
    `(deny default)` without the augment. Expects
    `attempt.outcome == "exec_failed"` with `attempt.errno == EPERM`
    or `EACCES` from `posix_spawn` and `attempt.error` mentioning
    posix_spawn. If the selected resource setup model can fail before
    spawn, split that into a separate setup-failure assertion rather
    than using it as the spawn-deny test. Does NOT assert on
    `first_deny` (see the sandbox-policy interaction note above).
- Test fixture helper (test-only, not shipped):
  - Lives under `tests/suites/runner_use_c_worker/exec_fixture/helper.c`.
  - Built on demand by `runner_use_c_worker/run.sh` via xcrun clang
    into `tests/out/<run>/exec_fixture/helper`. Output directory is
    under `tests/out/`, gitignored. The fixture is dynamically linked
    against libSystem (the realistic shape; true static linking
    against libSystem is not supported on macOS).
  - **Not part of the app bundle.** `build.sh` does not touch it,
    `make notarize` does not sign it. It exists solely to give the
    e2e suite a reproducible target for exec attempts.

### Docs

- `PolicyWitness.md`
  - New section "Augments": explains the `policy.augments` field,
    what `exec_baseline` allows (deferring exact contents to the
    augment file itself), the augment-is-append-only-and-allow-only
    rule and its override consequence for caller-authored denies,
    and the envelope fields under `data.policy_augmentation` that
    surface what was applied.
  - "Attempt kinds the runner implements" section: add the
    `("exec", "spawn")` row with the helper-binary contract
    (caller ships a binary, exit code becomes attempt verdict,
    stdout/stderr captured up to the bounded buffer, child PID and
    signal status round-tripped).
  - "Common decode errors" updated: `unknown augment '<name>'` rejected
    as bad_request before any runner invocation.
  - Add an explicit "schema_version notes" paragraph: Phase 2 adds
    `data.policy_augmentation`, the `exec` attempt kind, child status
    fields under `steps[].attempt`, and stdout/stderr fields if bounded
    output capture remains in Phase 2. These are **additive optional
    fields under the existing schema_version=4 contract.** Consumers
    that introspect the raw JSON see the new keys but don't need to
    branch on schema_version to handle them. This is a deliberate
    compatibility decision — not a schema-version bump — because no
    existing v4 field changes shape.
  - Document the selected post-apply resource setup model. Consumers
    should know whether `exec_failed` means spawn was denied, child
    exited non-zero, or the worker could not set up capture resources.
- `runner/README.md` augments directory documented (mentioning the
  controller-side resolution, not a runner-side concept).
- `runner/augments/README.md`: NEW. Explains the augment authoring
  protocol (the iterative process documented above), the
  append-only/allow-only rule, and how to add a new augment.
- `controller/README.md`: document the new `data.policy_augmentation`
  envelope field and the controller's augment-resolution
  responsibility.
- `tests/INDEX.md`
  - AttemptOutcome matrix: add `exec_failed` row.
  - Note the runner ABI bump (3 → 4) in any place that pins the
    version.

### Validation

- `tests/run.sh --suite source_drift --suite unit --suite runner_unit --suite runner_c_worker_harness --suite runner_use_c_worker --suite integration`
- Source-drift counts: 9 attempt outcomes → 10; attempt-kind enum
  agreement check passes for the new `EXEC_SPAWN = 8`; region-size
  `_Static_assert` passes with the new slot byte count.
- ABI layout agreement passes: C `sizeof` / `offsetof` values match
  Swift `PWShmLayout` for every header, slot, param, and exec field.
- New augment-resolution integration tests must pass.
- The two new exec e2e cases must demonstrate both the augmented-policy
  success path and the unaugmented-policy clean failure (with errno,
  NOT with `first_deny`).
- The resource-setup model is explicitly tested. A failure before
  `posix_spawn` must not be accepted as proof that a sandbox denied
  process execution.
- Notarization: `make notarize` rebuilds, signs the new
  `Contents/Resources/Augments/` directory contents as part of the app
  bundle, and ships. The test fixture helper is NOT signed or
  notarized — it's test-only and lives outside the bundle.

### Sizing

~150 lines C in `run_attempt` if stdout/stderr capture stays in Phase 2
(spawn + pipe-drain + waitpid loop + child output capture), ~60 lines C
in the v4 ABI struct/region updates, ~40 lines Swift in `PWShmLayout`
for the new offsets, ~50 lines Swift in `CWorker.swift` for slot
input/output fields, ~30 lines Swift in the orchestrator (map + drift
classifier), ~120 lines Rust in `controller/src/run_flow.rs` for augment
resolution + hash computation + envelope synthesis, ~200+ lines tests
(unit + integration + e2e + ABI layout guard), ~60 lines test fixture C helper +
build script, ~100 lines docs, one new
`runner/augments/exec_baseline.sb` (authoring is empirical; sizing
TBD), one new `runner/augments/README.md`. Substantially larger than
Phase 1 and structurally significant (ABI bump). Prefer checkpointed
PRs by default: augment machinery first, ABI/layout guard second, exec
runtime third, empirical `exec_baseline` last.

---

## Out of scope

The seven case-work kinds (`generic`, `iokit`, `ipc`, `mach`, `process`,
`socket`, `user_preference`) are deliberately not enumerated. Each kind's
ops have heterogeneous safety + recipe profiles that the corpus survey
flags as "the maintainer's empirical burden"; per-op decisions belong to
the caller writing the helper, not to PW source. The exec attempt kind
is the supported mechanism for testing any of these ops.

The three never kinds (`network`, `signal`, `system`) remain unsupported
through any mechanism. exec attempts that try to act on these surfaces
are not blocked by PW — the helper can do whatever it wants under the
applied policy — but PW makes no commitment to determinism or safety
for these probes. Documented as caller's responsibility.

## Sequence

1. **Phase 1 is complete.** It shipped the third wire-tier attempt kind
   (`sysctl` / `read`) without a worker ABI bump, replaced the
   `runner_filter_sysctl_name` placeholder attempt with real Channel A
   evidence, added `sysctl_failed`, and added the source-drift guard for
   C/Swift attempt-kind enum agreement.
2. **Phase 2 ships as four checkpoints** (detailed at the top of the
   Phase 2 section): controller augment plumbing → ABI v4 layout +
   layout guard → exec runtime → empirical `exec_baseline`. Each
   checkpoint should leave the tree buildable and testable.
3. **Decisions already committed (no further deliberation needed):**
   - `PW_SHM_SLOT_BYTES = 8192` for v4.
   - Layout guard ships as a new `runner_abi_layout` suite that
     compiles a C printer and asserts agreement against `PWShmLayout`.
   - Checkpoint-1 ships `runner/augments/exec_baseline.sb` as a
     comment-only no-op file; checkpoint-3 may use a fixture-private
     augment if needed; checkpoint-4 fills in the real content.
   - Post-apply resource setup commitment: the preferred model
     (pre-apply pipes + file_actions, post-apply only posix_spawn +
     drain + waitpid + shm writes) is the target. If empirical
     testing during checkpoint 3 shows it fails, the implementer
     stops and raises an explicit decision per the "Critical design
     decision" section — they do not silently degrade.
4. **Deferred by design:**
   - The exact `exec_baseline.sb` contents, which must be authored
     empirically from deny logs during checkpoint 4.
   - Any fallback choice for post-apply resource setup, surfaced
     only if checkpoint 3's empirical testing forces it.

Each phase is independently shippable, testable, and reversible.
Neither changes the response schema version (currently 4) — both
add only additive optional fields under the existing v4 contract,
which is a deliberate compatibility decision and is documented as
such in `PolicyWitness.md`. Phase 2 does bump the **worker-internal**
ABI version (`PW_PROBE_RUNNER_ABI_VERSION` 3 → 4), but that's the
host↔worker shm contract, not the wire-visible response schema; the
two are independent.
