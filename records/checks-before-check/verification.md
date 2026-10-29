# Isolated candidate verification

Tested source: `53b8e88e616f85b67cdecdd7d4cf9a1a4a487790`, based on the D2
investigation source `7562d24ac2334122499ea349010fd67211058ac3`. This is development
verification of C1–C3, not acceptance of the later E2 implementation or the
combined workset. `verification-facts.json` retains the result and receipt hashes.

The command in `implementation.md` completed in the isolated worktree as run
`workset-d2-docs-01`, ID `20261029T221143Z_bc9fa172`: five passes, no failures,
skips, unrun cases or harness errors, and no observed system sleep overlap.
Elapsed dispatcher time was 69.717 seconds. No tracked edits occurred during
execution; git status was clean before and after it. The run has no automatic
whole-source snapshot, so the clean commit attribution is an executor observation;
the control receipts separately preserve their actual fixture/input snapshots.

| Case | Result and relevant evidence |
| --- | --- |
| source_drift/runner_source_manifests_agree | Passed source/catalog/command and guidance-route controls using Meson. |
| source_drift/contract_versions | All 16 controls passed, including all seven WorkerIdentityTests. These establish the corrected case routing and exercise identity inputs, relocation, stale output, markers and symlinks. |
| source_drift/architecture_documentation | All 10 controls passed. The strengthened stale-copy control accepted current inputs, refused damaged copies with the exact canonical repair command, preserved check inputs and restored currency. |
| source_drift/build_documentation | All 16 controls passed, including its corresponding stale-copy repair diagnostic and restoration control. |
| source_drift/generator_contract | All 26 controls passed, including selected-document link checking and generator ownership/failure boundaries. |

The architecture and build `--check` commands also passed before the dispatcher
run. Structural comparison kept every architecture graph except documents equal
to the investigation base, including worker_capabilities. The F1 host-source
paragraph remained byte-identical. These are bounded checks; none establishes
the unresolved F1 guarantee or new runtime behavior.

Raw managed output remains untouched at
`/private/tmp/pw-workset-binding/tests/out/runs/workset-d2-docs-01/`, local and
gitignored. It is not represented by a retention entry in main. The primary
executor will rerun the five cases after integration and retain that main
verification, avoiding a manifest entry whose relative path only resolves in
this isolated worktree. Any later cleanup remains under normal output ownership.

Prose spacing was normalized only after this run ended. Subsequent factual
availability/release-account corrections have their own source-inspection record;
this passing run is not silently extended to those edits. Final D2 acceptance,
E2 reconciliation and coordinated D1 retirement remain separate steps.
