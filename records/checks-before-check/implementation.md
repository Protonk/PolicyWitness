# Bounded D2 candidate

Base investigation source: `7562d24ac2334122499ea349010fd67211058ac3`.
This record accompanies the candidate implementing the primary executor's
authorized C1–C3 corrections. It is not final D2 acceptance; E2 reconciliation
and the recorded C4/C5 dispositions remain outstanding. F1 is unchanged and
unresolved under the user's explicit repeated instruction.

## Changes and scope

- docs/architecture.json documents graph now assigns general selected-prose
  link checking to generators, keeps standalone-guide checking with limits,
  removes the brittle build-table count and cites actual worker-identity
  controls. Build-to-generator edges cite the existing before-signing control;
  source inspection, not that test, establishes more specific placements.
- Source_drift README states the same link boundary and places the
  WorkerIdentityTests account under contract_versions, where timed_main runs
  them. Its complete host-source/F1 paragraph is byte-identical to the base.
- Architecture/build stale-copy diagnostics prescribe tests/lib/python.sh.
  Existing stale-copy tests now require the exact canonical command while
  retaining accepted, rejected, unchanged-on-check and restored cases.
- Only the architecture document graph's owning outputs were regenerated:
  ARCHITECTURE, architecture-documents.dot and SVG. Other graphs, including
  worker_capabilities, are unchanged. No runtime, catalog, baseline or worker
  identity change is made.

The initial freshness checks for architecture and build pass. A structural
comparison confirms that all architecture graphs except documents are equal
to the base and that the F1 paragraph is unchanged. These checks do not replace
the selected dispatcher run below.

## Candidate verification

Selection inspected through the public dispatcher: runner_source_manifests_agree
requires Meson; architecture_documentation, build_documentation, generator_contract
and contract_versions have no listed external equipment. No app, XPC, signing
or shared service operation is selected.

Command executed from this isolated worktree at the committed candidate:

```
PW_TEST_OUT_DIR=tests/out/runs/workset-d2-docs-01 tests/run.sh --case source_drift/architecture_documentation --case source_drift/build_documentation --case source_drift/generator_contract --case source_drift/runner_source_manifests_agree --case source_drift/contract_versions
```

The candidate was committed before execution. `verification.md` and
`verification-facts.json` record the five passing cases at that exact source,
including the scope of this isolated development credit. Raw managed output is
local and gitignored. The primary executor controls retention and workset cleanup.
