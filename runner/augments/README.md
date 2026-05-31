# runner/augments

Named SBPL fragments callers opt into via `policy.augments: [...]`.
The controller (`controller/src/augments.rs`) resolves each name to
`<app>/Contents/Resources/Augments/<name>.sb` before invoking
`sbpl-preflight`, appends the contents to `policy.sbpl_source`, and
strips the `augments` field from the request forwarded to the runner.
Both preflight and the worker therefore compile the same bytes; the
runner has no augment-aware code path.

See PolicyWitness.md → Augments for the wire-side contract,
sha256 reporting, override semantics, and consumer-visible
behavior.

## Shipped augments

- **`exec_baseline.sb`** — three `(allow ...)` rules that let a
  libSystem-dynamic helper `posix_spawn` under `(deny default)`.
  Pragmatic baseline, NOT a narrow minimum — see the
  "exec_baseline derivation transcript" + "exec_baseline
  composition limits" sections below before composing it with
  callers that probe file-read denial.

## Contract

Augments are **append-only and allow-only**:

- Each augment contains only `(allow ...)` rules. Authors commit to
  never emitting `(deny ...)` or other policy-shrinking constructs.
- Augments are spliced after the caller's source. SBPL is
  last-match-wins, so an augment's allow overrides a caller's
  earlier deny for the operations the augment covers. A caller
  opting into the augment consents to that override; the controller
  does not warn.
- The augment file's bytes are sealed by the app codesign and
  surfaced in the signed evidence manifest under `kind: "augment"`
  with sha256. Downstream consumers can verify they're compiling the
  same augment text that was signed.

## exec_baseline composition limits

`exec_baseline.sb` grants `(allow file-read*)` unconditionally.
Because augments are last-match-wins, this overrides any
caller-authored `(deny file-read* ...)` rule that came earlier.
The practical consequence: **specimens that probe file-read
denial cannot be composed with `exec_baseline`**. Two examples:

- Caller writes `(version 1)(deny default)(deny file-read*
  (subpath "/secrets"))` and opts into `exec_baseline`. The
  augment's broad `(allow file-read*)` is appended after both
  denies. A `sandbox_check` for `file-read-data /secrets/foo`
  returns `allow`, and an `open(/secrets/foo, O_RDONLY)`
  succeeds. The caller's deny is silently no-op'd. If the
  intent was to test that the deny holds, the test is invalid
  under this augment.

- Caller writes `(version 1)(allow default)(deny file-read*)`
  intending an "allow everything except reads" baseline. With
  `exec_baseline` appended, every read is allowed. The caller's
  deny is dead.

For these cases the caller should either (a) drop the augment
and inline the spawn-support rules into their own source with
the narrower file-read scope they want, or (b) skip the
file-read denial probes and use the augment only for the exec
attempt.

`(allow process-exec*)` and `(allow process-fork)` have the same
override property but the affected surface is much smaller (only
exec/spawn) and isn't typically probed for denial in the same
specimen.

## exec_baseline derivation transcript

Verified against:

| field             | value                                           |
| ----------------- | ----------------------------------------------- |
| ProductName       | `macOS`                                         |
| ProductVersion    | `14.8.3`                                        |
| BuildVersion      | `23J220`                                        |
| uname -r          | `23.6.0` (Darwin 23.x is macOS 14 / Sonoma)     |
| Helper source     | `tests/suites/runner_use_c_worker/exec_fixture/helper.c` |
| Helper source sha | `07a29524a6a26c9a4b71a7346048f05b0618fd4589e9efc11235fc609b33c624` |
| Helper bin sha    | `2777e67a0a73a066bed65833d2daa979b65e1046810fedd3161491420a0d093a` (compiled at derivation time; subject to clang/SDK churn) |
| Helper linkage    | `/usr/lib/libSystem.B.dylib` (dynamic; verified via `otool -L`) |

Candidate rules (starting set):

| name              | included | minimum? | removal-test result                       |
| ----------------- | -------- | -------- | ----------------------------------------- |
| `process-exec*`   | ✓        | yes      | not removed individually (every test of "remove X" started here); inferred minimum because `posix_spawn` calls require the exec check |
| `process-fork`    | ✓        | yes      | without it: `posix_spawn` returns `EPERM` (errno=1); the fork half of spawn is denied |
| `file-read*`      | ✓        | yes      | without it: `posix_spawn` returns `EPERM` (errno=1); kernel reads the target binary's bytes before exec |
| `file-read*` narrowed to `(subpath "/usr/lib") (subpath "/System/Library")` | tested separately | no | `posix_spawn` returns `EPERM` because the helper at `/tmp/pw_exec_fixture_helper` is outside the narrow scope; broadening to cover any plausible helper path lands on `file-read*` unconditional |
| `mach-lookup`     | tested separately | no | removed → helper still exits 0 cleanly |
| `sysctl-read`     | tested separately | no | removed → helper still exits 0 cleanly |

Iteration commands (run from repo root):

```bash
# Build the fixture helper once
/usr/bin/xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
  -o /tmp/pw_exec_fixture_helper \
  tests/suites/runner_use_c_worker/exec_fixture/helper.c

# Drive a candidate baseline through PW. The spliced policy is
# inlined here (skipping the augment mechanism) so iteration
# doesn't require rebuilding the bundle.
cat > /tmp/req.json <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "exec_baseline_iter",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)\n(deny default)\n(allow process-exec*)\n(allow process-fork)\n(allow file-read*)\n"
  },
  "probe_plan": [{
    "step_id": "s",
    "sandbox_check": {"operation": "process-exec*", "filter": {"kind": "path", "value": "/tmp/pw_exec_fixture_helper"}},
    "attempt": {"kind": "exec", "action": "spawn", "target": "/tmp/pw_exec_fixture_helper"}
  }]
}
EOF
dist/PolicyWitness.app/Contents/MacOS/policy-witness run /tmp/req.json \
  | /usr/bin/python3 -c "import json,sys; e=json.load(sys.stdin); s=e['data']['runner_result']['steps'][0]; print('sb_check=', s['sandbox_check']['outcome'], 'attempt=', s['attempt']['outcome'], 'child_pid=', s['attempt'].get('child_pid'), 'errno=', s['attempt'].get('errno'))"
```

Observed failure modes:

| removed rule    | observed result (sb_check / attempt)             | classification                         |
| --------------- | ------------------------------------------------ | -------------------------------------- |
| `process-fork`  | `sb_check=deny` (validator agrees), `attempt=exec_failed`, `child_pid=0`, `errno=1` ("posix_spawn: Operation not permitted") | sandbox-blocked spawn (clean signal)   |
| `file-read*`    | same shape as removing process-fork: `posix_spawn` EPERM with `child_pid=0` | kernel reads binary pre-exec; without file-read of target, spawn is blocked |
| narrow `file-read*` to `(subpath "/usr/lib") (subpath "/System/Library")` | same: target at `/tmp/...` isn't in scope, spawn blocked | confirms file-read scope must cover the target path |
| `mach-lookup`   | `attempt=ok`, `child_exit_code=0`                | not required for this helper           |
| `sysctl-read`   | `attempt=ok`, `child_exit_code=0`                | not required for this helper           |

Pin tests (`tests/suites/runner_use_c_worker/`):

- `exec_attempt_without_baseline_fails_cleanly` — pins the
  `(deny default)` failure shape and the `child_pid==0` +
  `errno∈{1,13}` sentinel that the witness depends on.
- `exec_attempt_with_baseline_succeeds` — pins that the
  spliced `(deny default) + exec_baseline` policy actually lets
  the fixture helper spawn and exit 0, plus
  `sandbox_check.outcome=="allow"` + `drift==false`.
- `exec_attempt_args_and_stderr_round_trip` — pins argv[1..]
  delivery + stderr capture.
- `exec_attempt_stdout_truncation_marker` — pins the bounded
  output capture + truncation marker.

If any of these fail on a new macOS revision, the augment needs
re-derivation against the same fixture helper.

## Authoring a new augment

The augment-authoring loop is iterative because macOS's kernel
sandbox surface for a given operation (spawn, network, IOKit, …)
is non-obvious and not documented in a single place. The
recommended loop:

1. **Write the minimum helper.** Compile a libSystem-dynamic binary
   that exercises ONLY the operation the augment is meant to
   support. Don't include code paths that touch unrelated surfaces;
   you'll end up authoring allows you don't need.

2. **Pick a starting point.** Apple's profiles under
   `/System/Library/Sandbox/Profiles/` are the closest reference,
   but they're permissive (whole-system surfaces). Start with the
   broadest plausible allow set and tighten — not the other way
   around.

3. **Drive the helper through PW.** Compose a request with
   `policy.sbpl_source = "(version 1)\n(deny default)\n" + candidate
   baseline` (skip the augment mechanism while iterating — write the
   spliced source directly so you don't have to rebuild the bundle
   between attempts). Run via `policy-witness run`. The C worker's
   exec attempt surfaces `attempt.errno`, `attempt.error`,
   `attempt.child_pid`, and `attempt.child_term_signal`. The
   `child_pid` sentinel pins where the failure happened:

     - `child_pid == 0` + `errno ∈ {EPERM, EACCES}` → the **kernel
       sandbox blocked posix_spawn itself**. Add `(allow
       process-exec*)`, `(allow process-fork)`, or a broader
       `file-read*` for the target binary path.
     - `child_pid > 0` + `child_term_signal == 9` → dyld
       (or another early-exec process) was killed by the sandbox.
       Look at `attempt.stderr` for any pre-kill output, then
       cross-reference what dyld would have been doing (mmap of
       libSystem, shared cache lookup, code-sign verification).
       Typical fix: `(allow file-read*)`.
     - `child_pid > 0` + non-zero `child_exit_code` → the helper's
       own code returned an error. Not a sandbox event; treat as
       helper-debug rather than augment-author.

4. **Use the canonical SBPL operation name in `sandbox_check`.**
   The userland validator accepts operation names that include the
   `*` suffix (e.g., `process-exec*`, `process-fork`); the
   unstar'd `process-exec` returns `EINVAL` from `sandbox_check`
   on macOS 14. Specimens that drive a new augment should mirror
   the operation name used in the corresponding allow rule so the
   validator can predict the verdict alongside the attempt.

5. **Tighten one rule at a time.** Remove an allow rule; re-run.
   If still works, the rule wasn't needed. If broke, the rule is
   minimum. The current `exec_baseline.sb` was derived this way —
   see the transcript above for the actual removal matrix.

6. **Cross-verify with `log stream`.** When the worker reports a
   helper failure with no obvious cause, run
   `log stream --predicate 'sender == "Sandbox"' --info` in another
   terminal and re-run the specimen. Kernel deny messages name the
   denied operation + filter and let you target the augment fix
   precisely. (Note: the worker doesn't currently surface
   per-helper-child denies through `data.runner_sandbox_diagnostics`
   — that's PID-scoped to the worker, not its children — so the
   `log stream` cross-check is the canonical debugging path.)

7. **Pin with tests.** Add e2e cases under
   `tests/suites/runner_use_c_worker/` that drive the augment +
   fixture helper and assert BOTH `sandbox_check.outcome` (the
   prediction channel) AND `attempt.outcome` (the observation
   channel). If the augment ever needs additional rules (e.g. a
   new macOS revision tightens what dyld can do without explicit
   allows), the test fails first.

8. **Record the macOS revision** the augment was verified against
   in the .sb file's header comment + this README's "derivation
   transcript" section. Augments are not guaranteed to survive a
   major macOS upgrade; the transcript is the audit trail for
   "this augment was minimum on macOS X.Y.Z".

## Adding a new augment

1. Author the `.sb` file under this directory.
2. `build.sh` automatically copies every `*.sb` in this directory
   into `Contents/Resources/Augments/`. No build wiring needed.
3. `tests/build-evidence.py` automatically emits a manifest entry
   for every `.sb` it finds in the bundle's Augments dir, under
   `kind: "augment"`. No evidence wiring needed.
4. Document the augment in this README under "Shipped augments"
   and add a "derivation transcript" section.
5. Add an e2e case under `tests/suites/runner_use_c_worker/` that
   exercises it. PolicyWitness.md → Augments should also list the
   new augment's intent in a sentence.
