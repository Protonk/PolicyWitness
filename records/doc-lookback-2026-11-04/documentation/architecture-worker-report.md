# ARCHITECTURE / WORKER authored revision

Prepared against reviewed baseline `ea64218be2549fd034096f53ac23d79afac711ae` under
accepted D1–D4 and the instruction to return before tests/builds. This is an
implementation handoff, not final-reader acceptance or new runtime evidence.

## Files and decisions

- `docs/ARCHITECTURE.md`: replaced the internal-only actor account with public
  driver routing, scoped the ordinary/declaration sequence, added the local
  actor handoff sequence, and distinguished failed exchange completion from
  successful delivery and later consume eligibility. Added form-specific
  timing pools, sampled cutoff, actor receipt and fallback association (retaining the held-request diagnostic),
  declaration-only issuer dependency, and inventory-versus-flow framing.
- `docs/WORKER.md`: added a compact common/declaration/actor resource crosswalk,
  scoped launch inheritance and authority rows, clarified shared quiescence
  erasure versus private custody, documented release-local-state differences,
  corrected public activation applicability, and added fresh-write/create
  orientation. Historical launch L and its applicability limits are retained.
- `docs/architecture.json`: retained all node/edge IDs while correcting worker
  state, exec/setup labels, actor-plan routing, reciprocal T8/T16/T17 traffic,
  B18/B19 distinctions, receipt/fallback association, issuer dependencies,
  launchd wording and declaration resource scopes (S5/S7/S13d/S14b/S19–S22/S37).

The source-file enumeration in the old driver paragraph was consolidated into
one form-to-driver account. The repeated exit/erasure narrative in the checking
list was reduced to focused test routes because the sequence and worker tour
already carry those semantics. The introductory actor paragraph now routes to
the sequence. Resource rows and their source/check qualifications remain;
no row was deleted merely to reduce length. New sequence/crosswalk material
makes the documents longer overall, addressing the established local-account
gaps rather than targeting a word count.

## Grounding and limits

Supporting review records: `reports/architecture-ledger.md`,
`reports/worker-ledger.md`, `reports/consistency-report.md`, and
`investigations/authority-report.md`, `admission-report.md`, `timing-report.md`,
`evidence-report.md`, all under `records/doc-lookback-2026-11-04/`.
The accepted decision owner is root `READER-OUTFLOW-PLAN.md`.

Primary-source spot review covered the current CWorkerOrchestrator actor branch
before ExtensionSession construction, ActorScheduler walkSchedule and custody
service ordering, AuthorityCustody serviceTransfer/finish, ActorSession launch
flags, worker release state/settlement/erasure and fresh-write open/truncate
calls. No new permission, revocation, memory-policy or lifecycle guarantee was
introduced. Numeric bounds stay with LIMITS. Coordinator corrected qualification
measurement shorthand to setup plus elapsed schedule execution (including the
collection interval in elapsed, excluding final cleanup); these documents add
no duplicate qualification-total claim.

F1 remains deferred per `implementation/READY-FOR-DOCUMENTATION.md`; no flakiness
investigation or new runtime finding was opened. I1–I3 evidence remains as
recorded by the coordinator, not revalidated here. No consequential unresolved
factual question was identified in this authored scope.

## Pending generation and validation

All pre-existing generated ARCHITECTURE/WORKER regions were preserved byte for
byte. Root must run the owning architecture generator after coordination with
the limits owner; it updates tables and DOT/SVG figures from architecture.json.
Review generated T8/T9/T16/T17, B9/B12/B18/B19, X10/X27 and changed resource rows,
then inspect figure/table layout and link rendering. Generated text still
contains old wording until that step; it is not the finished candidate.

Only read-only source/diff inspection and `git diff --check` for these three
files were performed; the latter reported no whitespace errors. No generator,
generator check, test dispatcher, test, build, native probe or commit was run.
Source-drift/generator checks, full rendered fidelity, cross-document review and
fresh paired-reader acceptance remain unexecuted and belong to later work under
the coordinator's authorization boundary.
