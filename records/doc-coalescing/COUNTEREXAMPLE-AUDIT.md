# Counterexample audit of the comparison and path-observation explanations

This audit follows the second and third cycles of
[DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md) and the order-checklist
correction, starting from `6114293a`. It asks whether a reader following the
guide's new explanations can reach a conclusion the evidence does not support.
It is limited to four questions. Each entry gives the guide claim, the
discriminating case, the conclusion a reader could draw, what is established
and the correction.

Evidence is labelled by kind. **Source** means the producer or reader code was
read. **Constructed** means an existing or new control runs on built inputs.
**Native** means a single run of the staged app (`d04a3819`, contract
`development:aa400348…`) on one machine with an APFS scratch directory on
2026-11-13; those runs are unretained and raise no support grade.

Two maintainer decisions were given: `target_relation` keeps its behavior and
the documents stop calling it a byte comparison; the contract's
`observed_path` sentence stays, and the guide may describe the current
implementation without committing to it.

## 1. What does "same" mean?

**Claims.** Reading rule 4: "`same_submitted` compares the submitted path
bytes." The FAQ: "`same_submitted` compares submitted target bytes." The
comparison section: the validator asked `sandbox_check` using "the same
submitted target string".

**Case.** A query filter `…/café` spelled with U+00E9 and an attempt target
spelled `e` plus U+0301. The two strings are canonically equivalent and differ
in UTF-8 bytes.

**Reader's conclusion.** `same_submitted` means the query and the attempt
passed identical bytes, and a path form listed in `same_as_input` is "same" in
that sense too.

**Established.**

- Source: `comparisonEvidence` compares the two strings with Swift string
  equality, which is canonical equivalence. The JSON `same_as_input` list is
  decided by the controller's serializer with Rust string equality, which is
  byte equality. The controller does not recompute `target_relation`.
- Native: the step reported `same_submitted` with `query_first`. Its attempt
  diagnostics carried `realpath_resolved` as a string in the stored spelling
  and listed only `parent_realpath_resolved` in `same_as_input`. Fresh reads
  through both spellings recorded one device and inode on that filesystem. An
  `open_read` of the decomposed spelling recorded an `observed_path` in the
  stored spelling.
- Source and native: `tests/lib/consumer.py`, the test harness's independent
  reader, compared the strings by code point and expected
  `different_submitted` for that native step. It would have rejected a
  correct reply.

**Corrections.** Rule 4, the FAQ answer and three guide passages now say that
`same_submitted` compares strings with canonical equivalence, that
`same_as_input` compares bytes, and that neither compares objects. The test
reader now uses canonical equivalence.

**Controls.** `ComparisonEvidenceTests` gained a producer case for the pair in
both directions and a different string. `blackbox_e2e/checker_controls` gained
one accepted envelope with the pair as `same_submitted` beside a
byte-different carried path form, and two rejections: the pair called
`different_submitted`, and a byte-identical form left uncompacted. The
existing `PathDiagnosticsTests` case and its Python replay already keep this
pair as separate path forms.

## 2. Does a derived path imply existence?

**Claims.** The path section's row for a form listed in `same_as_input`: "This
is a resolved form, not a missing one … The host's later resolution, equal to
the submitted string." The quick-start reading: "A form named in
`same_as_input` resolved to the submitted bytes." The row "the later form
resolves".

**Case.** An absent leaf whose parent resolves to its submitted spelling.

**Reader's conclusion.** The target existed after the run, because a
"resolved" form equals the input.

**Established.**

- Source: `parentRealpathResolved` resolves the parent and appends the leaf
  as text. It never looks the leaf up. `firmlinkResolved` is a prefix mapping.
- Constructed: the existing fixture
  `tests/fixtures/blackbox_e2e/checker/response25/missing_path_run.json` has a
  failed open of an absent path with `realpath_resolved: null` and
  `same_as_input: ["parent_realpath_resolved"]`. `PathDiagnosticsTests`
  asserts a missing leaf has no leaf-followed form and keeps its parent form.
- Native: the dangling-link and unlinked steps of the third cycle's two-phase
  run showed the same pattern.

**Corrections.** The row now separates the three forms: only
`realpath_resolved` shows the whole path resolved at that time. The
quick-start reading tells the reader to use `realpath_resolved` and says a
failed create also leaves `parent_realpath_resolved` in `same_as_input`. The
"later form" row names `realpath_resolved`. No new control: the existing
fixture and unit case cover the distinction.

## 3. Can observations from different times be combined?

**Claims.** The table cell that host diagnostics run "after every phase's
actions". The row for an answered query whose later `realpath_resolved` is
`null`.

**Case.** A first-phase `open_read` of a symlink succeeds; a second-phase
action unlinks the symlink's destination.

**Reader's conclusion.** The first step's `null` diagnostic describes the
state its attempt met, so the successful open and the `null` conflict, or the
`null` shows the attempt's effect.

**Established.**

- Source: `enrichPathDiagnostics` runs once after `orchestrate` returns, over
  every step.
- Native: in that case the first-phase step had `outcome: ok`, an
  `observed_path` naming the destination and `realpath_resolved: null`. The
  cause was known there from the specimen and the unlink step's own result.
  The fields alone establish two host results at two times and one worker
  observation at a third; they name no cause.
- Constructed: `ComparisonEvidenceTests` "later host disappearance is distinct
  from an earlier supplied validator record" and the native
  `queries_precede_attempts` case cover later disappearance within a phase.
  No control runs a later phase against an earlier step's diagnostics.

**Corrections.** The claims survive with two additions. The row now says the
two host observations do not bracket the step's attempt. The table cell now
says the pass follows every phase the worker reached and that process cleanup
has its own records, which is what the field reference already said. No
control was added: the timing is one call site, and a native case for it is
the lesson noted as an adjacent opportunity in the third cycle.

## 4. Does missing evidence identify a cause?

**`unestablished`.**

- Claim: "These fields show which", a column headed "Why it can be unmet", and
  the setup row "Ordinary form: `sandboxed_after_apply` is true".
- Case: a worker that published `applied` beside a nonzero apply status.
- Reader's conclusion: setup was established, or the chain row's listed
  reasons are the reason.
- Established, source: the producer requires the applied publication and a
  zero status; the reply's `sandboxed_after_apply` is the publication alone.
  A release under that record adds `release_without_successful_application`.
  The check uses `runner_subprocess.pid` or the actor's `launch.pid` as the
  worker PID. Constructed: `OrderingTests` already removes each link,
  including `apply_rc`, and expects `unestablished`.
- Correction: the setup row states the zero status, a paragraph explains the
  inconsistent record, the PID fields are named, and the last column is
  headed as examples. A sentence says an unmet requirement identifies the
  missing observation and not its reason.

**`observed_path: null`.** The four rows are separated by other fields
(`result_source`, the action and `outcome`), and the row for a successful open
gives two causes the reply cannot tell apart and says so. The claim survives.
The section now also says the three actions and the call are this build's
implementation, per the maintainer's decision.

**Omitted and null path forms.** The `null` rows already give more than one
cause each. The omitted-form row was the defect corrected under question 2.

## Decisions not taken

- The contract's relations definition says "Target equality compares
  submitted strings". Proposal: append "under canonical Unicode equivalence;
  their UTF-8 bytes can differ". It states current behavior but adds a public
  commitment, so it is left for the maintainer.
- Reporting validation admits `query_first` when `sandboxed_after_apply` is
  true without reading the apply status. The producer never emits that
  combination. Whether the reader should refuse it is a behavior question and
  is only noted.

## Verification

One run from clean `84f9993a` covered the documentation, the changed test
reader and both new controls:

```sh
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  PW_TEST_OUT_DIR=tests/out/runs/doc-coalescing-counterexample-audit PW_TEST_QUIET=1 \
  tests/run.sh --suite source_drift \
  --case runner_unit/pwrunner_core_unit_executable \
  --case blackbox_e2e/checker_controls --case run_effects/checker_controls \
  --case runner_filter_sysctl_name/checker_controls \
  --case witness_contract/comparison_matrix
```

Run `20261113T203503Z_78cbe115` completed in 621,295 ms. All 15 cases passed,
with no skips, unrun cases, harness errors or recorded system sleep.

- Constructed: `runner_unit` ran 605 of 605 tests, including "canonically
  equivalent targets with different UTF-8 bytes are same_submitted".
  `blackbox_e2e/checker_controls` wrote the accepted
  `canonical_equivalent_targets` envelope and both rejections. The two other
  checker-control cases exercise the changed reader on their own inputs.
- Native: `witness_contract/comparison_matrix` ran the live matrix rows
  through the changed reader. Its rows use ASCII targets, so it shows the
  reader still accepts ordinary replies and does not exercise the equivalent
  pair.
- Documentation: the ten `source_drift` cases passed after regeneration of
  the copied questions and reading rules.

Limits. No test compares the corrected sentences with the code; they rest on
the source inspection recorded above. The equivalent pair is exercised by
constructed inputs only; the one native observation of it is unretained. The
reader's equivalence uses Python's Unicode data and the producer's uses the
Swift standard library's, so a code point known to only one of them could
compare differently. The other suites that use the shared reader on live
replies were not run. No runtime source changed, the staged app was not
rebuilt, and no support grade rose. The run was reviewed and removed with
`make prune APPLY=1`. The staged `dist/PolicyWitness.md` still equals the
guide at `bfa65341`.
