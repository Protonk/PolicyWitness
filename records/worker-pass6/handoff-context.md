# Worker audit and design handoff context

## Preserved audit

`initial-report.md` is a byte-for-byte copy of the independent reader's report
from `.tmp/audits/worker-account-475ac0b/report.md`. Its SHA-256 is
`c44f4967fcbdeeb9b5d4fbaadf033e14d2d783abc4cc96c5e50c798fd417576e`.
The audited revision was `475ac0b7a284b784a4a65e5673f71c7f17941a5b`.
The reader reported a clean checkout before and after, and stopped before
opening earlier reviews. The report discloses initial exposure to auto-memory,
commit subjects and later artifact names; retain those qualifications when
describing the audit's independence.

The report, its conclusions and its proposed corrections remain the reader's
assessment. The design handoffs pose alternatives; they do not adopt every
diagnosis or remedy. In particular, receiving a writable descriptor and actually
violating collection/release order are different propositions. The generator's
positive caption accurately states its mechanical checks even where a cited
check is irrelevant to a row's behavior.

## Primary evidence availability

The audit records these fresh runs; their terminal summaries were checked during
handoff preparation:

| Local output directory | Run ID | Result |
| --- | --- | --- |
| `tests/out/runs/worker-audit-475ac0b-launch` | `20261018T150641Z_12585892` | 3 passed, 0 failed, 0 skipped |
| `tests/out/runs/worker-audit-475ac0b-checks` | `20261018T150739Z_fc07ecd7` | 11 passed, 0 failed, 0 skipped |

These directories, earlier launch artifacts, rendered map tiles and console
transcripts named in the report are gitignored local evidence. They are not
embedded in this record and may be unavailable in another checkout. Follow test
retention and applicability rules before crediting or replacing them. The audit
credits worker/host applicability through matching worker identity; it leaves
controller-side applicability unresolved for the dirty build. Passing cases
establish their actual assertions, not every property of an inventory row.

## Subsequent cleanup of the reported orphan

On 2026-10-18, the user expressly requested termination of PID 61820 before the
coordinator read the report. A process inspection found `pw-probe-runner`, parent
PID 1, elapsed time 19:27:31, and 99.7 percent CPU, with arguments
`--shm-fd 3 --ready-fd 4 --step-count 1 --post-apply-hang-ms 15000`.
SIGTERM returned successfully; a subsequent inspection still found the running
process. SIGKILL then returned successfully, and the following `ps -p 61820`
returned status 1 with no process entry. Only that process was targeted.

This resolves the report's immediate cleanup request. It does not identify the
instruction being executed, establish applicability to the current binary, or
explain the earlier host loss and removed BYOXPC staging. The initial report's
"still running" statement is preserved as its observation at delivery time.

## Provisional relationship to earlier findings

- WA-01 introduces a validator-reference question; existing register rows 19,
  23 and 26 constrain observation quality and descriptor handling at other
  boundaries.
- WA-03 recovers and extends the descendant-lifetime issue in row 10.
- WA-04 raises the worker's own terminal-lifetime question. WA-08 revisits the
  ordinary erasure paths described under row 14. Their terminal cleanup design
  is considered together without merging their guarantees.
- WA-02 and source-ownership portions of WA-09 broaden row 25. WA-05 and WA-06
  concern the identity, applicability and presentation of observations. These
  remain with the documentation workstream, including WA-09's role taxonomy.
- WA-07 motivates the execution-configuration question. WA-10 motivates a
  bounded environment-model question; the audit did not observe TCC behavior.
  WA-11 identifies a source-level capacity without a size-boundary experiment.

This is routing context, not completed adjudication. All earlier open register
rows remain open, including findings this reader did not recover. Investigation
results may change these groupings. The parent plan tracks those decisions and
the daughter plans carry the particular questions and source entry points.
