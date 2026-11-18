# Trace assessment records

Per-claim assessment records for `records/TRACE-MANAGEMENT-PLAN.md`, which
holds the dispositions and is the only document that links here. They cover
every claim in `records/DOCUMENTATION-TRACE-REVIEW.md`: DT-01–135, their
subfindings and qualifications, the thirteen DT-44 leads and both unnumbered
import/receipt investigations.

Twelve read-only passes wrote these on 2026-11-17 against `837296af`, one file
per group of shared subjects. No pass modified a tracked file, built, or ran a
registered case. Each file states what it re-read, what it executed on the
signed `2f4d76e4` app or on retained local runs, and which of the review's
executed evidence is no longer available. For each subject a file gives the
claims table, the comparison of statement, producer and readers, the plausible
treatments, a recommended disposition per claim, resulting user duties and an
implementation worklist.

A recommendation here is an input. The management plan's disposition section
records the decision for each claim and governs wherever the two differ.
Line references are those of `837296af` and go stale as the selected remedies
land.

| File | Review entries |
| --- | --- |
| [A-docs-generation-reading.md](A-docs-generation-reading.md) | DT-01–21 |
| [B-smaller-differences-leads.md](B-smaller-differences-leads.md) | DT-37–41, DT-44 |
| [C1-identity-classification-vocabulary.md](C1-identity-classification-vocabulary.md) | DT-22–24, DT-26–28, DT-30, DT-33–35, DT-51, DT-57 |
| [C2-failure-contract-producer-reader.md](C2-failure-contract-producer-reader.md) | DT-45, DT-47, DT-49, DT-52, DT-54–56, DT-58 |
| [D-erasure-handles-ownership.md](D-erasure-handles-ownership.md) | DT-63, DT-64, DT-66–68, DT-124–128 |
| [E-custody-setup-trigger.md](E-custody-setup-trigger.md) | DT-36, DT-43, DT-46, DT-59–62, DT-65, DT-120–123, DT-129, DT-133 |
| [F-reconcile.md](F-reconcile.md) | DT-69–80 |
| [G-import-inventory.md](G-import-inventory.md) | DT-29, DT-81–87, import side of both unnumbered investigations |
| [H-development-identity.md](H-development-identity.md) | DT-08 (executed side), DT-88–94 |
| [I-receipts.md](I-receipts.md) | DT-95–104, DT-134, receipt side of both unnumbered investigations |
| [J-wire-identity.md](J-wire-identity.md) | DT-105–112 |
| [K-transport.md](K-transport.md) | DT-31, DT-32, DT-42, DT-113–119 |
| [L-readers-acceptance.md](L-readers-acceptance.md) | DT-25, DT-48, DT-50, DT-53, DT-130–132, DT-135 |

The passes' probe scripts and outputs were written under
`.tmp/trace-integration/assessments/work-*/`. That directory is gitignored
scratch available only in the local checkout, with no retention guarantee; the
files here cite it as the location of what they executed, not as retained
evidence. Two passes ran one command each outside their limits, both read-only:
`policy-witness run --help` (an argument refusal that read no request and
contacted no runner) and a `codesign -dv` display of the built app.
