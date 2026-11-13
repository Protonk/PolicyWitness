# Controller authority dispatch

The [plan](../../controller/NEW-DOC-INTEGRATION-PLAN.md) owns the assignments.
Source baseline: `dcc7dd0bd0634a603379ff185228abca70b5d22f`; production inputs
are frozen during initial reading. The entry decision is in `BASELINE.md`.

## Initial packets and independence

All principal initial turns use `gpt-6-astra`, fresh contexts
(`fork_turns="none"`). Each reads the plan and applicable
repository guidance, records actual exposure, and writes only its own report.
No principal starts builds/tests, mutates production, makes commits, or spawns
helpers. Experiments and additional assignments go through the coordinator.
The report destination is not an access-control boundary: separation is a
reading protocol. Do not open another report before the freeze.

| Principal | Allowed initial packet | Destination | Status |
| --- | --- | --- | --- |
| A, Contractual Authority Reader | Plan role A; baseline identity/maintainer disposition; authored contract, authoring model and imported declarations; generated views for navigation. No cited production/test implementation. Required README exposure is recorded as navigation. | `A-CONTRACT-INITIAL.md` | Active: `/root/contract_reader` |
| B, Implementation Authority Reader | Plan role B; baseline identity/maintainer disposition; production/build/test/fixture sources and component READMEs. No authored/generated contract as outline; record incidental wording exposure. Historical raw runs are unavailable. | `B-IMPLEMENTATION-INITIAL.md` | Active: `/root/implementation_reader` |
| C, Boundary Challenger | Plan role C; baseline identity/maintainer disposition, public entries and catalogs; write scenarios before targeted code/contract inspection. No A/B results. | `C-BOUNDARIES-INITIAL.md` | Active: `/root/boundary_challenger` |
| D, Integration Editor | Frozen reports, cross-examination, decisions, evidence and actual source. Started after initial adjudication; maintainer M01–M05 acceptance delivered during drafting. | `INTEGRATION.md`, agreed documentation destinations | Active: `/root/integration_editor`, fresh `gpt-6-astra` |

The packets were dispatched after entry-record commit `9b579bf7` using the
recorded model and fresh-context setting. Each was told to read only the
baseline's entry/identity section, excluding the coordinator's implementation
review as an outline. All three acknowledged the separation and no experiment
request accompanied their initial progress messages.

The coordinator plus A/B/C uses all four slots. Original contexts return for
cross-examination and final review; D runs afterward. Any substitution is
recorded with the old packet and original artifact preserved.

## Minor assignments

Used: 0 of 16. Initial allowance: up to eight, with eight reserved for later
uncertainty. No minor assignment is prescheduled. A task needs a bounded
question that could change a decision and an independent checker.

## Execution and retention

The maintainer accepted the historical prerequisite and asked to avoid the
previous accumulation of runs and worktrees. Initial reading creates neither.
Tests needed by several roles are combined when that preserves their boundary
and evidence. A necessary isolated mutation must have an explicit lifetime;
no permanent extra worktree is part of this dispatch.
