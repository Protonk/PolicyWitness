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

- **`exec_baseline.sb`** — minimum SBPL needed for `posix_spawn` of a
  libSystem-dynamic helper to succeed under `(deny default)`. Three
  rules: `(allow process-exec*)`, `(allow process-fork)`, `(allow
  file-read*)`. Tested against `tests/suites/runner_use_c_worker/
  exec_fixture/helper.c`.

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

4. **Tighten one rule at a time.** Remove an allow rule; re-run.
   If still works, the rule wasn't needed. If broke, the rule is
   minimum. The current `exec_baseline.sb` was derived this way:
   started with seven rules, removed each in turn, settled on the
   three that actually broke when removed.

5. **Cross-verify with `log stream`.** When the worker reports a
   helper failure with no obvious cause, run
   `log stream --predicate 'sender == "Sandbox"' --info` in another
   terminal and re-run the specimen. Kernel deny messages name the
   denied operation + filter and let you target the augment fix
   precisely. (Note: the worker doesn't currently surface
   per-helper-child denies through `data.runner_sandbox_diagnostics`
   — that's PID-scoped to the worker, not its children — so the
   `log stream` cross-check is the canonical debugging path.)

6. **Pin with a test.** Add an e2e case under
   `tests/suites/runner_use_c_worker/` that drives the augment +
   fixture helper and asserts `attempt.outcome == "ok"`. If the
   augment ever needs additional rules (e.g. a new macOS revision
   tightens what dyld can do without explicit allows), the test
   fails first.

7. **Record the macOS revision** the augment was verified against in
   the .sb file's header comment + this README. Augments are not
   guaranteed to survive a major macOS upgrade; the comment is the
   audit trail for "this augment was minimum on Darwin X.Y.Z".

## Adding a new augment

1. Author the `.sb` file under this directory.
2. `build.sh` automatically copies every `*.sb` in this directory
   into `Contents/Resources/Augments/`. No build wiring needed.
3. `tests/build-evidence.py` automatically emits a manifest entry
   for every `.sb` it finds in the bundle's Augments dir, under
   `kind: "augment"`. No evidence wiring needed.
4. Document the augment in this README under "Shipped augments".
5. Add an e2e case under `tests/suites/runner_use_c_worker/` that
   exercises it. PolicyWitness.md → Augments should also list the
   new augment's intent in a sentence.
