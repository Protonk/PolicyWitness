# Drift-removal acceptance follow-up

The three acceptance conditions below remain open despite the earlier closeout.
The recovered requirements are in `.tmp/drift-audit/DRIFT-REMOVAL-PLAN.md`,
also recoverable with `git show ed0bd3da84f3b4020e243061b21ff7a460c04e4d^:DRIFT-REMOVAL-PLAN.md`.

This turn is limited to committing the audit and writing this plan. Schedule
execution and validation after the concurrent libsandbox work has finished.

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

4. **Scout the three review documents before deletion.** Read
   `DRIFT-REMOVAL-DECISIONS.md`, `DRIFT-REMOVAL-CANDIDATES.md`, and `FIVE-FOLLIES.md`.
   Flag content for the user's review only when it meets all three criteria:
   (A) true about the current system, verified against current sources;
   (B) devoid of narrative or history, including choice rationales, accounts of
   decisions, and descriptions of how things differed; and (C) valuable to know.
   For each candidate, capture its passage and source location, supporting
   evidence, practical value, and existing or proposed persistent documentation
   home. Report explicitly if none qualify. Present these findings before
   deleting the source documents; migrate content only after the user's review.

5. **Delete the superseded review documents.** Delete
   `DRIFT-REMOVAL-DECISIONS.md`, `DRIFT-REMOVAL-CANDIDATES.md`, and `FIVE-FOLLIES.md`.
   Remove or repair surviving references. Keep concrete acceptance receipts with
   test evidence; git retains the historical documents.

Validate the new orchestration controls, Rust unit suite, source controls, and
dossier witnesses; rebuild and run affected live checks when required by the
changed paths. Follow checkout locking and use fresh test-output directories.
Record commands, source/artifact identity, results, and any justified reuse of
earlier verification. Preserve failed attempts and investigate failures before
claiming acceptance. Close out only when all three receipts exist, scouting
findings have been reported for review, and all three review documents and their
stale links are removed.
