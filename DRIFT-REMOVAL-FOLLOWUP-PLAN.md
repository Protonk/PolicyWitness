# Drift-removal acceptance follow-up

This plan completes three missing acceptance receipts, corrects documentation,
updates contract readers and test equipment, and retires the review documents.
Execute the numbered steps in order; scouting and deletion follow the system
changes, and step 15 checks acceptance using the surviving sources and receipts.
Schedule PW execution and validation after the concurrent libsandbox work has
finished. Step 11 includes a conversation whose outcome determines its text edits.

The recovered requirements are in `.tmp/drift-audit/DRIFT-REMOVAL-PLAN.md`,
also recoverable with `git show ed0bd3da84f3b4020e243061b21ff7a460c04e4d^:DRIFT-REMOVAL-PLAN.md`.
The existing audit fixes are in `0c82ae2`; steps below apply to that corrected
tree, so inspect current text before replacing a passage quoted from the landing.

The historical closeout's accounting is supported by the retained
`tests/out/runs/drift-i5-all-02/run.json` (run ID
`20261002T015030Z_a37db665`): 183/183 completed and passed, no skipped or unrun
cases or harness errors, and an app recorded as valid and unchanged.
Its `artifact-integrity/inspection.json` records no host sandbox symbols;
`supplemental/drift-i5/five-specimen-diff/summary.json` records ten passing
comparisons with no unexpected differences or failed named checks. The run is
registered in `tests/RETAINED.json` against `ed0bd3d`; the I1 baseline is retained
as `runs/drift-i1-baseline-01`. These establish historical results, not the three
missing receipts or acceptance of the follow-up tree. Step 15 states the final
checks directly; it does not depend on the decision log's completion claims.

1. **Count manifest loads through production orchestration.** Add a narrow
   controlled loader boundary to the ordinary `cmd_run` flow. Count attempts
   while delegating to the real manifest loader; cover successful loads and
   missing/invalid manifests for both built-in and BYOXPC selection. Assert
   exactly one attempt for each run reaching selection, and that selection,
   app provenance, and binary dossier collection consume that same result.
   Earlier argument refusals may make zero attempts. A source call count or
   test-local reconstruction of orchestration is insufficient.

2. **Prove BYOXPC invocation without a manifest.** Exercise production
   orchestration and external-runner selection with controlled registry,
   signature, and entitlement dependencies and a captured client boundary.
   Assert that a valid BYOXPC runner receives the held request despite manifest
   failure. Check the resulting envelope: null app provenance, all three
   binary roles unavailable with the manifest reason, null baselines, and
   retained paths and actual hashes where readable. Pair this with built-in
   refusal, exit 2, a diagnostic naming the manifest, and zero client calls.
   Merely constructing a `RunnerTarget` or checking record shape is insufficient.

3. **Record the no-PlistBuddy call-path review.** Trace ordinary built-in
   `cmd_run` and reachable helpers, including `plist_key_string`,
   `read_bundle_info`, and direct subprocess calls. Explain why retained runner
   management callers are outside this path. Pair the review with
   `builtin_selection_reads_the_manifest_entry_and_no_info_plist`; retain the
   review beside the controller read receipts. A text search alone is insufficient.

4. **Fix the documentation errors outside the fixture-build changes.**
   `runner/README.md` describes
   `Sources/PWCWorkerShim/` as "shared-memory, atomics and spawn helpers"; the
   header exports `pw_cworker_shm_open_create` and the two atomic load/store
   helpers only. `tests/COVERAGE.md`'s `unlink_failed` row lists S25 among the
   matrix rows that plan an unlink; S25 reads the path S19 unlinked.
   Step 9 owns all compiler-prerequisite text and registry entries, including
   the preflight README sentence, together with the fixture-build changes.
   Rerun `source_drift` (registry and link checks) after these edits.

5. **Validate reply and envelope shapes against goldens instead of removed-key
   lists.** `tests/fixtures/contract/response_shape.json` already records every
   key and JSON type per reply object path from the field-complete reply
   fixture. Add the same for the controller envelope: a field-complete envelope
   produced by a Rust unit test (the uniform `kind: "run"` shape with every
   optional object populated), recorded as
   `tests/fixtures/contract/envelope_shape.json` and compared by `unit/rust.unit`
   under the same replace-the-golden acknowledgement rule as the reply golden.
   Make `tests/lib/consumer.py` validate each object it reads against the
   golden for its path: an unknown key is an error naming the path, a present
   key must carry the golden's type, and absence stays allowed (the goldens
   are allowlists, not required sets). Delete `REMOVED_STEP_KEYS`,
   `REMOVED_COMPARISON_KEYS`, `REMOVED_ATTEMPT_KEYS`, `REMOVED_QUERY_KEYS`,
   `REMOVED_REPLY_KEYS`, `REMOVED_DATA_KEYS` and `REMOVED_DIAGNOSTIC_KEYS`
   with their rejection branches; replace the removed-key controls in
   `blackbox_e2e/checker_controls.py` with one "unknown key at path" control
   per golden and one wrong-type control. These are representative controls of
   the shared shape validator; step 7 separately checks that suite CLIs reach
   it. Establish passing controls here before step 7 removes their local
   counterparts. Update `docs/CONTRACT.md` → "Shape goldens" and the failure
   contract's consumer invariant to say that the
   goldens are the readers' allowlists. The Swift decoder keeps ignoring
   unknown keys; strictness lives in the Python readers and the Rust unit
   comparison only. Validate with `unit/rust.unit`, `runner_unit` and
   `blackbox_e2e/checker_controls`. Step 10 owns any later changes to this
   envelope fixture and golden caused by its observer decision.

6. **Generate the scenario-matrix table and share the reading rules.** The
   table under "Scenario matrix" in `tests/FAILURE-PROPAGATION-CONTRACT.md`
   was rendered once from `tests/fixtures/comparison/matrix.json`; nothing
   regenerates or checks it. Add a generator that writes the table between
   BEGIN/END markers from the fixture (a sibling of `docs/generate_limits.py`
   or a mode of it) and a `source_drift` check that the committed table equals
   the generator's output. Make the twelve reading rules one text: keep the
   contract's copy authoritative, mark it with SHARED markers, and transclude
   it into the guide's "Reading a comparison record" through the existing
   `generate_limits.py` marker mechanism, with its copy check. Do not change
   the rules' wording in this step. Run `source_drift`; later documentation
   regeneration uses this updated generator and preserves the shared rules.

7. **Delete redundant removed-key assertions and route every live checker
   through the consumer.** Fifteen hand-written `'drift' not in step` /
   `'deny_signal' not in step` assertions remain. In the suites that already
   call `consumer.validate` (`runner_exec_dac/check.py`,
   `runner_exec_dac/check_query_scope.py`, `runner_validator_failure/check.py`,
   `witness_contract/check_termination_correlation.py`,
   `witness_contract/check_ordering.py`) delete them. In the seven that do not
   (`smoke/check_caller_auth.py`, `runner_use_c_worker/run.sh`,
   `witness_contract/check_worker_sparse.py`,
   `witness_contract/check_worker_evidence.py`,
   `witness_contract/check_diagnostic_transport.py`,
   `runner_exec_lifecycle/check_edges.py`,
   `sbpl_allowdeny_consistency/check.py`) validate the envelope through
   `consumer.validate` first, then delete the local lines; `validate` already
   accepts reporting-failure replies and client-generated failure replies.
   Trim the removed-key mutation controls duplicated in
   `runner_filter_sysctl_name/checker_controls.py`,
   `blackbox_menagerie/checker_controls.py` and
   `runner_specimen_isolation/check.py` to one mutation per CLI, enough to
   prove the CLI reaches the consumer; step 5 owns the shared validator's
   representative unknown-key and wrong-type controls. Keep those central
   controls intact. Rerun every touched suite.

8. **Move `runner verify` to stdin delivery and delete the file-input
    wrapper.** `run_pw_runner_client_file` in `controller/src/runner_client.rs`
    survives only for the two `runner verify` call sites in
    `controller/src/runner_commands.rs`, which still write the
    `pw-runner-verify` temporary request file. Deliver the verify request
    through `run_pw_runner_client` (`--request -`), delete the file wrapper,
    its `the_file_input_form_carries_no_delivery_observation` test and the
    temporary file, let `request_delivery` be non-null in the verify capture
    if the management envelope carries it, and update `controller/README.md`
    and the guide's BYOXPC verify text. The Swift client keeps its positional
    file form for direct use. Verification needs the BYOXPC opt-in verify
    case (GUI session and identity).

9. **Split `tests/fixtures/dispatcher/artifacts.py` and take compilation out
    of Python.** The one file is the fixture bundle builder (`FILES`,
    `bundle`, the compiled host stubs) and, copied verbatim with a shebang by
    `repository.install_runner`, the fake `codesign` executable
    (`fingerprint`, `seal`, `main`). Split it into a self-contained
    `seal_tool.py` (fingerprint, seal, main; the only file the installer
    copies; imports nothing but the standard library) and
    `fixture_bundle.py` (layout constants and `bundle(app, host)`, pure
    Python; the compiled host is a required argument, so a missing stub is an
    equipment error rather than a compile on the side). Move the compile step
    to a fixture build script, `tests/fixtures/dispatcher/build.sh <out>`, a
    sibling of `tests/fixtures/worker_lifecycle/build.sh`, that
    `tests/suites/dispatcher/run.sh` and `tests/suites/preflight/run.sh` run
    once per suite run into the run's artifacts and expose to the checkers
    through environment variables, the shape `runner_unit`'s wrapper already
    uses for `PW_LIFECYCLE_WORKER_FIXTURE`. Only `check_artifacts.py` takes
    the sandbox-importing stub; the other three checkers take the clean one;
    the per-process `mkdtemp` cache goes. Apply the same rule to the other
    compile the landing put in Python: `check_comparison_matrix.py`'s
    `compile_helper` builds `helper_true` and `helper_false` per specimen;
    `tests/suites/witness_contract/run.sh` builds them once the same way and
    `prepare_files` copies the bytes into the scenario root. After this step
    no fixture Python invokes `clang`. State the compiler prerequisite once
    per suite in `tests/catalog.json` and the `tests/README.md` rows for
    `dispatcher`, `preflight` and `witness_contract`. This step also owns
    correcting `tests/suites/preflight/README.md`'s claim that release controls
    need no compiler and all other compiler-prerequisite descriptions; the
    preflight release controls keep needing the compiler because the inspector's
    `nm -u` check needs a real Mach-O host.
    Keep the manifest writer inside `bundle()` and keep the fixture's own
    `FILES` inventory independent of `tests/lib/artifact.py`'s `EXECUTABLES`
    (a mismatch fails the valid control, which is the point). Update
    `tests/suites/dispatcher/README.md` and `tests/fixtures/README.md`. Rerun
    `dispatcher`, `preflight`, `witness_contract/comparison_matrix` and
    `source_drift` for the changed registry and documentation.

10. **Decide the observer report's outer version.** The nested
    `sandbox_log_capture.observer` report carries the controller envelope's
    `schema_version` (4 → 5 in the acceptance diff) beside its own
    `observer_schema_version: 1`. Decide whether the nested report should
    carry only its own number; if so, drop or rename the outer field in
    `controller/src/bin/sandbox-log-observer.rs`, update the observer
    contract text in `controller/README.md` and the capture fixtures, and bump
    the controller envelope with the change through `docs/contract.json` and
    its generator. In the same step, update step 5's field-complete envelope
    fixture and golden under its acknowledgement rule, plus affected reader
    fixtures and version controls. Rerun `unit/rust.unit`, `runner_unit`,
    `blackbox_e2e/checker_controls`, `source_drift` and affected capture checks
    before proceeding. Preserve immutable historical captures. If the field is
    retained, explain what each number identifies in `docs/CONTRACT.md` using
    current semantics rather than decision history, then run `source_drift`.

11. **Measure the per-run cost, then agree on how to describe it.** Use the
    built app containing the runtime changes through step 10. First, live:
    time `policy-witness run --no-log-capture` for a specimen with no imports,
    one with `(import "system.sb")`, and a BYOXPC runner (binary hashing of
    three executables), against the 0.08 s fast-path figure, and separately
    the default log-capture path; retain the timings and source/build/app
    identity as a receipt. Then stop and talk: the user and the agent go over
    how PolicyWitness's live cost should be described, as one terse, precise
    answer in `docs/QUESTIONS.md` and as the information in `docs/limits.json`
    (hence `LIMITS.md` and the guide's copies) that lets a user infer their own
    per-run floor from the numbers in a reply. The step ends with agreed text,
    copies regenerated using step 6's generator, and a green `source_drift`.
    The wording is decided in that conversation.

12. **Retire the baseline receipt scripts.** Under
    `tests/fixtures/comparison/baseline_response12/`, `match_retained.py`
    walks run directories that pruning may remove and `match_live.py` needs
    `plan_matrix.md`, a copy of the deleted plan's table. The stored
    `retained_row_match.txt` and `live_row_match.txt` are the receipts: delete
    the two scripts and `plan_matrix.md`, and say in that README that the
    outputs stand alone with `run_a.json` and `run_b.json`.

13. **Scout the three review documents before deletion.** Read
    `DRIFT-REMOVAL-DECISIONS.md`, `DRIFT-REMOVAL-CANDIDATES.md`, and `FIVE-FOLLIES.md`
    against the system resulting from steps 1 to 12. Flag content for the user's
    review only when it meets all three criteria: (A) true about the current
    system, verified against current sources; (B) devoid of narrative or history,
    including choice rationales, accounts of decisions, and descriptions of how
    things differed; and (C) valuable to know. For each candidate, capture its
    passage and source location, supporting evidence, practical value, and
    existing or proposed persistent documentation home. Report explicitly if
    none qualify. Present these findings and save the report alongside the
    follow-up verification receipts before deleting the source documents;
    migrate content only after the user's review. Accepted migrations use the
    owning sources and generators established above.

14. **Delete the superseded review documents.** Delete
    `DRIFT-REMOVAL-DECISIONS.md`, `DRIFT-REMOVAL-CANDIDATES.md`, and `FIVE-FOLLIES.md`.
    Remove or repair references in surviving current documentation; names in
    this plan and immutable historical evidence are not live documentation links.
    Keep concrete acceptance receipts with test evidence and the scouting report
    available for review; git retains the historical documents. Run `source_drift`
    after deletion and any approved documentation migration.

15. **Check acceptance on the final tree.** Use this plan, current source and
    contracts, the scouting report, and retained verification artifacts. Check
    the following directly, without reopening the deleted review documents:

    - Steps 1 to 3 have concrete receipts for counted manifest loading across
      both selection modes and load outcomes, BYOXPC invocation without a
      manifest paired with built-in refusal, and the no-PlistBuddy call-path
      review paired with its no-Info.plist control. Recheck the review against
      any subsequent edits to the reachable helpers.
    - The final reply/envelope goldens, consumer controls and routed suite
      checkers agree with the observer decision. Contract versions, generated
      copies, matrix table, shared reading rules, compiler prerequisites and
      fixture-build ownership agree with current sources. Required Rust, Swift,
      source, affected-suite, dossier and BYOXPC verify checks pass. The matrix
      and dossier witnesses cover the current documented rows and failure
      shapes; a green aggregate alone does not establish a missing scenario.
    - The cost receipt identifies the source and app containing the final
      runtime changes, the user's agreed text is present, and all generated
      copies agree.
    - Credited verification identifies the tested source and app and supports
      the final tree, including the signed app's integrity and host-invariance
      inspection. Preserve the historical baseline, ten specimen comparisons
      and symbol receipts identified above. Assess their applicability to
      changed paths explicitly; any replacement comparison records full field
      paths and distinguishes intended changes from unexpected differences.
      Register credited runs in `tests/RETAINED.json`. Historical `--all`
      success does not establish `--all` success on the follow-up tree.
    - Scouting findings (or the explicit none-found result) have been presented
      and remain available. Only reviewed migrations have been applied; pending
      user decisions are reported as pending. All three review documents, the
      retired baseline scripts and `plan_matrix.md` are gone, their retained
      raw evidence is intact, and current documentation has no stale links.

Validate the new orchestration controls, Rust unit suite, source controls, and
dossier witnesses; rebuild and run affected live checks when required by the
changed paths. Follow checkout locking and use fresh test-output directories.
Record commands, source/artifact identity, results, and any justified reuse of
earlier verification. Preserve failed attempts and investigate failures before
claiming acceptance. Reuse a receipt only where its tested dependencies remain
applicable; later edits require the affected checks again. Required checks have
no failures, skips, unrun cases, or harness/integrity errors. Preserve both sides
of retries and verify owned BYOXPC cleanup. Close out only when step 15's checks
are satisfied, with explicit links to the evidence supporting each claim.
