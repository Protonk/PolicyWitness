# Candidate review and repair

Status: selection committed; repairs and verification pending. Claude, 2026-10-30.
Starting revision `ecd3795dfd44bddc7f437a122340c0fb10a65644` (tip of
`review/pytest-coherence` at `/private/tmp/pw-coherence-20261030`, left unchanged).
It descends directly from adoption baseline `809ef178f7a9ce2628f13fb137f1456452a49b85`
(frozen at `/private/tmp/pw-pytest-exec-candidate-20261030`); `6b35e27a` is the
coherence repair and tested source of pinned run `coherence-01`. Repairs are on
`review/pytest-candidate-repair` at `/private/tmp/pw-candidate-repair-20261030`.
No accepted-checkout merge, additional family adoption, CHECK.md work or cosmetic
standardization is authorized.

Associated material: [selection, hypotheses and eliminated checks](candidate-repair/selection.md).
Later files in `candidate-repair/` record findings, evidence and recovery. These
records and this plan are review material retired together; retirement does not
release pins or resources.

## Inherited protection (carried, not re-derived)

- Coherence worktree registry `tests/out/pytest-owners/`: 16 closed actual commands;
  eight deliberately unresolved nested fixture records inside pinned
  `tests/out/runs/coherence-01` (run `20261030T214512Z_f209aff2`), indexed by
  `/private/tmp/pw-coherence-20261030/records/coherence/recovery-index.json`.
- Frozen adoption worktree: 25 indexed runs, 176 closed actual records and 95
  unresolved nested fixture records under
  `/private/tmp/pw-pytest-exec-candidate-20261030/records/pytest-exec-adoption/recovery-index.json`;
  earlier prototype/unknown-worker resources under that candidate's
  `records/pytest-maintenance/resource-recovery.md`.
- Accepted checkout `/Users/raccoon/Desktop/Security/PolicyWitness` (`main`) and its
  `dist/PolicyWitness.app` are read-only inputs. Accepted F2 native evidence:
  `tests/out/runs/f2-controls-02` there.

None of these is signalled, recovered, unpinned or pruned by this review. Historical
PID fields are not live identities. Fixture-scoped holds stay with their pinned runs.

## Approach

Four hypotheses (selection record) were formed from the candidate's source and
consumers, then checked against the coherence traces to avoid repetition. Each
mechanism was reproduced in the scratch area before this selection was committed;
the decisive observations will come from registered controls in
`dispatcher/pytest_controls`, committed as stimuli before the repair, run once
against the unrepaired source, pinned, and rerun after repair.

Repairs stay inside the supervision/owner/engine equipment and the family's shared
baseline. Domain witnesses, the 58-attempt golden, the six mutation statements and
their expected assertions are unchanged. Verification: the owning control case,
the family, source/generator drift, and the dispatcher/preflight readers that
consume ownership receipts, using the accepted app unchanged and the pinned
interpreter/packages. Fresh `tests/out/runs/repair-*` output in this worktree only.

Return a consequential choice only if localization leaves materially different
defensible commitments.
