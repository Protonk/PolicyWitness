# Testing audit — shared-validator mutation measurement

## Task and required output

Measure whether the existing checker controls detect three deliberate regressions
in the shared validator, and what causes each detection. Also test a harmless
change to diagnostic order. Report observations; do not repair surviving
regressions or expand into a general review.

**Write your full results into this file, `tests/TESTING-AUDIT.md`, under
`Measurement results`. Preserve the prompt.** Include the execution matrix,
detecting controls, evidence for each classification, and any incomplete work.
Your final chat response should briefly state completion or blockage and link
to this document.

## Fixed source and offline boundary

The subject is `tests/lib/blackbox.py` at commit
`10c77c9ea20ec207aff37074c864dee55a3c9096`. Its expected SHA-256 is:

```text
75e460d3c6151c560b0c75e4e2b3187259dcd6cb17e4395c5e015e55541d9145
```

The isolation adapter, `tests/suites/runner_specimen_isolation/check.py`,
must have SHA-256:

```text
a0cee3a8431b3ab8f9bf3ad4e0cb078411d31fba41d15cdebad24fe088ed2d7e
```

Record actual HEAD and working-tree differences. Verify all copied source and
fixture files agree with the subject commit, and hash originals before and
after measurement. A later documentation-only commit is acceptable; changed
experiment code or fixtures are grounds to stop and report the mismatch. Do not
reset the checkout.

Edit only this document among repository source/documentation files. Create
fresh artifacts under `tests/out/testing-audit/measurement-02/<run-id>/`.
Use physical copies with the original relative directory layout. Do not use
symlinks or imports that accidentally resolve back into the original checkout.

Copy only these experiment dependencies into each disposable tree:

- `tests/lib/{blackbox.py,unavailable_prediction.py,run_capture.py}`
- `tests/fixtures/exec/control.py`
- `tests/fixtures/blackbox_e2e/checker/{valid_run.json,missing_path_run.json}`
- `tests/fixtures/blackbox_e2e/{BBX-001,BBX-002}/expected.json`
- `tests/suites/blackbox_e2e/{checker_controls.py,validate_run.py}`
- `tests/suites/blackbox_menagerie/{checker_controls.py,validate_run.py}`
- `tests/suites/runner_filter_sysctl_name/checker_controls.py`
- `tests/suites/runner_specimen_isolation/check.py`

Only the disposable `tests/lib/blackbox.py` may differ from its original.
Keep controls, adapters, expected statuses, diagnostic requirements, and JSON
fixtures unchanged. Do not introduce new malformed inputs or new test cases.
A small orchestration script and an isolation import wrapper are permitted.

Run only Python checker processes. Do not launch PolicyWitness, invoke
`tests/run.sh`, build fixtures, inspect live processes, or inspect production
implementation. Set `PYTHONDONTWRITEBYTECODE=1`; run with assertions enabled
(no `-O` or `PYTHONOPTIMIZE`). Use a fresh interpreter for each control group
so imported modules cannot leak between variants.

## Exact variants

Start each variant from the unmodified source. Save its exact unified diff and
resulting source hash. Apply each stated edit once; stop on an unexpected source
shape instead of improvising a different mutation.

1. **M1 — remove alias agreement.** In `validate_step`, remove the `elif`
   branch reporting `attempt.rc mismatch` and the complete agreement block
   beginning `if "errno" in attempt and "syscall_errno" in attempt:`.
   Keep required-field checks, individual type checks, explicit expected errno,
   and attempt-success checks. This permits otherwise well-typed contradictory
   aliases without relaxing those other requirements.
2. **M2 — match by position.** In `validate_run_shape`, replace
   `matched.append((step, by_id[step_id]))` with a positional match:
   `matched.append((step, expected_steps[index] if index < len(expected_steps) else by_id[step_id]))`.
   Keep the order diagnostic, ID validation, and all other checks. The fallback
   avoids an unrelated IndexError for excess steps. Do not rewrite the step's
   ID or any expectation.
3. **M3 — stop after prediction errors.** In `validate_step`, immediately
   before `attempt = step.get("attempt")`, insert:
   `if errors: return errors` (formatted on two lines). Leave caller loops
   unchanged. This suppresses the remaining checks for that step when its
   prediction validation has already reported an error.
4. **P1 — reverse diagnostics, preserve semantics.** Wrap both public helper
   functions in the copied module. The `validate_step` wrapper returns its
   original error list in reverse order. The `validate_run_shape` wrapper
   reverses only its returned error list, leaving the matched pairs untouched.
   Preserve signatures/call compatibility, diagnostic text, values, and all
   validation decisions. This positive control is expected to pass.

Do not combine variants or adjust them after seeing which controls fail.
A regression that survives is a useful measurement result.

## Four unchanged control groups

For each variant, run all four groups independently, even if another fails:

1. `python3 <tree>/tests/suites/blackbox_e2e/checker_controls.py <artifacts>/bbx`
2. `python3 <tree>/tests/suites/blackbox_menagerie/checker_controls.py <artifacts>/menagerie`
3. `python3 <tree>/tests/suites/runner_filter_sysctl_name/checker_controls.py <artifacts>/filters`
4. Import the copied isolation adapter and run its existing controls as below.

For isolation, copy both saved witnesses from:

```text
tests/out/shared_isolation/full/suites/runner_specimen_isolation/overlapping_runs_keep_evidence_separate/artifacts/
```

For each of `A/` and `B/`, copy `run.json`, `specimen.json`, and
`processes.json` into the experiment's `inputs/` directory and record their
hashes. For label A use `allowed_index = 0`; for B use `allowed_index = 1`.
Construct each witness from its saved request and independent process record:

```python
witness = {
    "label": label,
    "allowed_index": allowed_index,
    "specimen": request,
    "processes": processes,
    "marker": request["probe_plan"][0]["attempt"]["args"][1],
}
```

Load the corresponding `run.json` as the envelope. Do not derive witness
expectations from that envelope. Check matching requested/returned step IDs;
both specimens deliberately share the same ordered IDs.

The wrapper must import the copied `check.py` with `importlib.util`, record
the resolved `blackbox.__file__` and its hash, and call `envelope_errors` on
both unchanged envelopes. Require empty error lists. Then call
`exercise_checker(witnesses, envelopes, out)` with A before B and a fresh
existing output directory. Do not call `main`, instantiate process observers,
or access old specimen target files; these checks use recorded evidence only.
Confirm the loaded witnesses and envelopes remain unchanged afterward.

The isolation controls stop at their first failed assertion. Preserve that
behavior: record the failing case and mark subsequent cases **not reached**.
Do not alter assertions to collect more failures or claim unexecuted cases
passed. The CLI control groups already collect their own failures.

## Execution and interpretation

Run an opening unmodified baseline, M1, M2, M3, P1, and a closing unmodified
baseline: **six executions of four groups, 24 group invocations total**.
Use separate trees/output directories and retain every attempt. Opening baseline
failure or missing input blocks the experiment; report it without generating
replacement live evidence. If a variant fails, continue the remaining groups
and variants. Preserve a failed P1 result rather than repairing it.

Reference baseline totals are 14 BBX controls, 92 menagerie controls, 128 filter
controls, and isolation's 80 rejected corruptions plus eight accepted variants,
in addition to the two unmodified isolation envelopes.

For each variant/group record command, return code, completion/timeout, reached
controls, and failing control names. For each detecting control, cite its saved
input and actual output and distinguish:

- **Wrong acceptance/rejection:** checker status or error-list emptiness differs
  from the unchanged control's expectation.
- **Missing/misattributed diagnostics:** evidence is still rejected, but a
  required independent failure or its attribution disappeared.
- **Checker exception:** the checker itself raised or crashed. Identify the
  exception; do not count this as evidence of the intended validation behavior.
- **Equipment failure:** import, setup, wrapper, or timeout failure prevented
  a meaningful measurement.

Multiple reasons may apply. An assertion raised by the control driver because
it observed a bad checker result is detection, not itself a checker crash.
Retain the full diagnostics; do not infer successful detection from a nonzero
group exit alone. If a group passes against a mutant, report that it did not
detect that mutation. No overall coverage claim follows from these three edits.

## Required artifacts and effort limit

Create:

- `measure.py` and, if separate, `isolation_controls.py`: reproducible
  orchestration only, without changed expectations or copied assertion logic.
- `inputs/{A,B}/{run.json,specimen.json,processes.json}`: saved witness inputs.
- `source-manifest.json`: original paths/hashes, subject commit, actual HEAD,
  input hashes, and before/after integrity checks.
- `variants/<name>/tree/`, `change.diff`, and group artifact directories:
  physical source copies, exact patch (empty for baselines), generated control
  inputs, and logs. Keep each group's stdout/stderr and exit metadata.
- `results.json`: all 24 planned group records with completed, blocked, or
  not-run state, failures/classifications, and references to supporting files.
- `run.log`: orchestration output and exit status.

Use a bounded subprocess timeout (at most 60 seconds per group). One small
script is sufficient; do not build a reusable mutation framework. Correct only
experiment setup mistakes, describe retries, and retain earlier attempts.
Do not change the suite, add tests, commit, launch agents, run the full suite,
or pursue other audits. If time runs short, report partial measurements and
precisely identify unrun work.

## Measurement results

Auditor: Claude Opus 5 (1M context), session
`https://claude.ai/code/session_013qeETCCJA1tmbMGQupDFSF`.

Artifacts: `tests/out/testing-audit/measurement-02/20260914-m2/`.

### Source integrity and provenance

- Actual HEAD `10c77c9ea20ec207aff37074c864dee55a3c9096`, **equal to the subject
  commit**, so no documentation-only follow-up commit had to be tolerated.
- `tests/lib/blackbox.py` =
  `75e460d3c6151c560b0c75e4e2b3187259dcd6cb17e4395c5e015e55541d9145` and
  `tests/suites/runner_specimen_isolation/check.py` =
  `a0cee3a8431b3ab8f9bf3ad4e0cb078411d31fba41d15cdebad24fe088ed2d7e`, both
  matching the expected hashes.
- `git diff HEAD -- tests/lib tests/fixtures tests/suites` was empty: all
  fourteen copied experiment dependencies agree with the subject commit. The only
  working-tree difference was this document.
- All fourteen originals were hashed before and after; `originals_unchanged:
  true`, and the six saved witness inputs re-hashed identically
  (`source-manifest.json`).
- Saved witness inputs (from
  `tests/out/shared_isolation/full/.../artifacts/`): A `run.json`
  `89e5bd18…4d6e`, `specimen.json` `054e6e8d…8f9b`, `processes.json`
  `bfba14e0…ad28`; B `run.json` `97591a59…982e`, `specimen.json`
  `0219f6d7…7275`, `processes.json` `37239093…d279`. Full values in
  `source-manifest.json`.
- Each variant is a physical copy in the original relative layout under
  `variants/<name>/tree/`; only that tree's `tests/lib/blackbox.py` differs. Every
  isolation group recorded its resolved `blackbox.__file__` inside its own tree,
  with a hash equal to that variant's subject hash — so no group silently
  validated against the real checkout. Python 3.9.6,
  `PYTHONDONTWRITEBYTECODE=1`, `PYTHONOPTIMIZE` removed from the environment so
  assertions stayed enabled, 60-second per-group timeout.

Variant subject hashes and diffs (`variants/<name>/change.diff`): `baseline_open`
and `baseline_close` `75e460d3…` (empty diff, 0 bytes); M1 `9380d6dd…` (20 diff
lines); M2 `982aaa7d…` (11); M3 `8793f9bc…` (11); P1 `aece001f…` (20). Each edit
applied exactly once, guarded by a single-occurrence anchor check.

### Execution matrix — 24 of 24 group invocations completed

No group timed out, and none failed for import, setup or wrapper reasons, so
there were no equipment failures. `rc=0` means the group passed against that
variant; for a mutant that means **it did not detect the regression**.

| Variant | bbx | menagerie | filters | isolation |
| --- | --- | --- | --- | --- |
| `baseline_open` | rc=0 — 14 controls | rc=0 — 92 controls | rc=0 — 128 controls | rc=0 — 88 cases (80 rejected, 8 accepted) |
| **M1** | **rc=0 — not detected** | rc=1 — detected, 8 failing | rc=1 — detected, 4 failing | rc=1 — detected, stopped at case 16 |
| **M2** | **rc=0 — not detected** | **rc=0 — not detected** | **rc=0 — not detected** | **rc=0 — not detected** |
| **M3** | rc=1 — detected, 2 failing | rc=1 — detected, 2 failing | rc=1 — detected, 3 failing | **rc=0 — not detected** |
| `P1` | rc=0 | rc=0 | rc=0 | rc=0 |
| `baseline_close` | rc=0 — 14 controls | rc=0 — 92 controls | rc=0 — 128 controls | rc=0 — 88 cases (80 rejected, 8 accepted) |

Both baselines reproduced the reference totals exactly — 14 BBX, 92 menagerie,
128 filter, and isolation's 80 rejected corruptions plus 8 accepted variants —
and in every isolation run the two unmodified envelopes were accepted (empty
error lists) and the loaded witnesses and envelopes were unchanged afterward.
Both specimens' requested and returned step IDs matched, and the two specimens
shared the same ordered IDs, as designed.

### M1 — remove alias agreement

Detected by three of four groups; **not detected by bbx**.

**menagerie (rc=1, 8 failing controls).** Six are **wrong acceptance** — the
checker returned rc=0 with `ok` where the control required rc=1:
`null_attempt_errno`, `disagreeing_attempt_rc` and `disagreeing_attempt_errno`,
each in both the `blackbox_e2e` and `blackbox_menagerie` adapters. Two are
**missing/misattributed diagnostics** — `float_alias_equals_integer` in both
adapters still exited 1, but only `fs_read_missing: invalid attempt.errno=2.0`
survived; the separately required `attempt.errno mismatch` disappeared, so the
float value is still rejected for its type while the independent agreement
failure is no longer reported. Inputs and outputs in
`variants/M1/artifacts/menagerie/*.run.json` and `*.log`.

**filters (rc=1, 4 failing controls).** All four are **wrong acceptance**
(rc=0, `unavailable prediction and attempt evidence checked`):
`rc_disagreement` for all three filter callers, plus
`sysctl_name/denial_errno_disagreement`. See
`variants/M1/artifacts/filters/*.log`.

**isolation (rc=1).** **Wrong acceptance**, at case 16 of 88:
`A_step0_errno_mismatch`. The recorded assertion payload is
`('A_step0_errno_mismatch', [])` — an empty error list where the control
requires a rejection carrying `attempt.errno mismatch`. That control sets
`attempt.errno` to a value differing from `syscall_errno` while both remain
well-typed, which is exactly what M1 stops checking. Per the prompt, the
adapter's stop-at-first-failure behavior was preserved: 16 cases were entered and
evaluated, and the remaining **72 cases were not reached** — they are not claimed
as passing. Input and output at
`variants/M1/artifacts/isolation/controls_out/checker_controls/A_step0_errno_mismatch.{json,log}`.

**bbx (rc=0) did not detect M1.** Its 14 generated control inputs and logs are
byte-identical to the baseline run's (`diff -rq` reports no differences), so none
of its controls constructs a well-typed alias disagreement for the removed checks
to catch.

### M2 — match by position

**No group detected M2.** All four passed with the baseline's control totals.
This is not equipment failure: every group resolved the mutated module (the
isolation group recorded `blackbox_sha256 = 982aaa7d…`, its own tree's hash), and
the mutation demonstrably changed output in cases that reorder or duplicate
steps — it just changed it in ways no control's expectations covered.

Concretely, `variants/M2/artifacts/bbx/reordered_steps.log` still carries the
`expected step IDs in order` diagnostic that its control requires, and still
exits 1, but gains six further diagnostics that the baseline did not emit, among
them `mach_lookup_denied: expected sandbox_check allow (got 'deny')` and
`fs_write_allowed: expected sandbox_check deny (got 'allow')` — evidence compared
against the expectation sitting at that position rather than the one with the
matching ID. The same pattern appears in the menagerie group's `reordered_step`
and `duplicate_step` cases for both adapters, in several filter cases, and in the
isolation group, where exactly two of 88 case logs changed
(`A_reordered_and_bad_attempt`, `B_reordered_and_bad_attempt`), again gaining
misattributed diagnostics rather than losing required ones. Every affected
control already required only the order diagnostic and a nonzero status, both of
which M2 preserves.

### M3 — stop after prediction errors

Detected by the three CLI groups; **not detected by isolation**. Every detection
is **missing/misattributed diagnostics**: the evidence is still rejected (rc=1
in all six failing controls), but a required independent attempt-side failure
disappeared.

**bbx (rc=1, 2 failing controls).** `prediction_and_same_attempt` still reported
`fs_write_allowed: expected sandbox_check allow (got 'deny')` but lost
`fs_write_allowed: expected attempt_ok=True`. `malformed_channels` still reported
`missing sandbox_check for fs_write_allowed` and `missing attempt for
mach_lookup_denied` but lost `fs_write_allowed: expected attempt_ok=True`.

**menagerie (rc=1, 2 failing controls).** `independent_malformed_channels` in
both adapters retained the two `missing …` diagnostics but lost
`fs_read_missing: expected attempt_ok=False`.

**filters (rc=1, 3 failing controls).** `malformed_prediction_and_attempt` for
all three callers retained `missing sandbox_check for <step>` but lost
`invalid attempt.rc`.

**isolation (rc=0) did not detect M3**, although the mutation was reachable
there: 6 of the 88 case logs differ from the baseline
(`A_envelope`, `A_step1`, `A_step2` and the three B equivalents). For example
`A_step1.log` loses two shared-validator diagnostics —
`expected attempt_ok=True (got False)` and `expected errno=None (got 1)` — while
that control's required fragments, `requested_path:` and `filter value:`, are
produced by the isolation adapter's own comparisons, which run after
`validate_step` and are unaffected. The controls' required sets therefore still
matched.

### P1 — reverse diagnostics, preserve semantics

**Passed in all four groups**, as expected of a positive control, with the
baseline totals reproduced everywhere. It was not a no-op: 33 of the 88 isolation
case logs differ from the baseline purely in line order, and no control's exit
status, required fragments or accepted/rejected classification changed. This
result was not repaired or adjusted.

### Retries

One retry, a setup mistake in the orchestration only; no measured value was
affected. The first attempt's M2 anchor string was written with twelve spaces of
indentation while the source line has eight, so `measure.py` stopped with
`STOP: M2 positional match: anchor appears 0 times, expected 1` after completing
`baseline_open` and M1. That attempt is retained in full at
`attempt-1/` (its `run.log`, its copy of `measure.py`, and the two variant trees
and artifact directories it produced). The anchor and its replacement were
re-indented to match the source, and the whole six-variant measurement was re-run
from scratch. M1's group results were identical across both attempts.

The M2 replacement text is the prompt's exact single line; no variant was
adjusted after seeing which controls failed.

### Limits or incomplete work

The planned work is complete: 24 of 24 group invocations ran to completion, all
recorded in `results.json` with command, state, return code, stdout and stderr,
plus per-group logs under `variants/<name>/artifacts/`.

Observations bounding what these numbers cover:

- These are three specific edits. Nothing here supports a general coverage claim
  about the shared validator, and a group that passed against a mutant is
  recorded as not having detected that mutation, not as evidence of anything
  broader.
- The isolation group stops at its first failed assertion by design, so M1's 72
  unreached cases are unmeasured for M1 — some of them might also have detected
  it. They are neither passing nor failing in this record.
- `rc` alone was not treated as detection anywhere: each failing control's
  required expectation and actual output were retained and used for the
  classifications above.
- No surviving regression was repaired, and no checker, control, fixture or
  expectation was modified; the only file edited in the repository is this
  document.
