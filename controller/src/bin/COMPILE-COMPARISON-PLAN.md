# Can compilation settle a profile comparison?

**Release target.** Conclude during the 0.3.8 guide work. Choose the release for any product change with the result.

**Decision goes to.** Scope finding 4 under [how much of the problem comes into the specimen](../../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md#how-much-the-users-real-problem-has-to-come-into-the-specimen), and an entry in the [product-change ledger](../../../records/guide/PRODUCT-CHANGES.md), whether or not the behavior changes.

**Draft 0 decision, 2026-11-23.** Keep the helper source-only. Captured object digests already distinguish changed compiled bytes, including changes hidden by the submitted-source hash. The guide explains the effective-source boundary.

The standalone `sbpl-check --request` accepted a specimen naming `exec_baseline` and reported the original source hash. In a run, the controller resolves augments before submitting the policy or invoking the fallback checker. Which inputs can a compile-only result identify well enough to compare two profiles? [Saved request](../../../records/guide/work/evidence/sbpl-check-augments/request.json) · [Checker result](../../../records/guide/work/evidence/sbpl-check-augments/sbpl-check.json) · [Augment resolution](../augments.rs) · [Checker](sbpl-check.rs)

1. Hold the app, OS, parameters and imports fixed. Compare the standalone request, its explicitly expanded source, and the effective source supplied by the controller. Change only the augment. Record what each route accepted and hashed. Compare resolving augments at the controller entry point with declining unresolved input at the standalone entry point.
2. Repeat compilation of the saved `orig.sb`, `orig_regex.sb` and `hole.sb` (an added carve-out). Then vary one used parameter or imported rule. Compare source hashes with independently obtained compiled lengths and byte digests. Check the worker capture's supported object layout and the outcome when no bytes can be read. [Comparison study](../../../records/guide/work/scope/README.md#4-compiled-bytes) · [Native comparator](../../../records/guide/work/scope/evidence/policy-comparison/bin/compile.c) · [Worker capture](../../tools/pw_probe_runner/pw_profile_capture.h)

Return example results for equal bytes, different bytes, and unavailable bytes, scoped to the compiler and inputs observed. Decide separately whether the checker should clarify its accepted inputs and whether an opt-in digest would save a live run. A behavioral claim about a particular app still needs evidence from its process.
