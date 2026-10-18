# Worker-language triage

The triage is complete against `5f878fe0603b039ef1edf3119d448b65534e2e18`.
It covers the prior sweep of [WORKER.md](../../docs/WORKER.md) and its direct
machinery. The ledger assigns the guard clauses to the three requested
outcomes; the rewrite candidates provide concrete local repairs for review.
No candidate has been applied.

## Dispositions

| Clause route | Stay; no later inference investigation | Stay pending RCA | Go after WORKER-only repair | Total |
| --- | ---: | ---: | ---: | ---: |
| C2 | 36 | 0 | 11 | 47 |
| D2 | 66 | 4 | 0 | 70 |
| **Total** | **102** | **4** | **11** | **117** |

All 101 original B1 occurrences are covered. Splitting passages whose clauses
have different bases or dispositions adds nine units. Seven secondary A1 guard
units bring the total to 117; three further A1 secondary roles refer to units
already counted. All 205 primary A1 occurrences are set aside, and the 23 prior
scope exclusions remain excluded. The original sweep labels are unchanged.
These are decision units, not counts of unique claims or sentences to delete.

“Settled” means that retaining the guard requires no further investigation of
its inference basis. It does not mean that an unobserved native fact has been
established, a test has newly run, or a register finding has closed. Some
settled guards describe an accepted observation limit; investigating the
underlying native behavior would be separate work.

## What the triage established

**Much of D2 is evidence provenance.** The plan explicitly required
observed/source-only/unknown scope for each resource. These qualifiers preserve
which evidence supports which row. Their documentary origin and present purpose
are identifiable without inventing a reader mistake or an external source that
caused it. A single general disclaimer would lose that per-resource information.

**Some guards answer a recorded overclaim.** The compiled-profile lifetime
guard has a concrete antecedent: the proposed sentence that the profile was
retained until worker exit exceeded what retaining its pointer established.
The allocation and private-extension boundaries likewise have documented source
limits and accepted scope. These stay without an editorial RCA. Historical
introduction, documented motivation and present reader premise are distinguished
in `origins.md`; an external contract's current meaning is not treated as proof
of historical causation.

**The removable C2 wording has local presentation causes.** Broad headings,
underspecified observation conditions, a repeated publication warning and a
graph edge can be repaired while preserving the instrument facts. Each draft
includes a reading with the guard absent and identifies the facts that must
survive. Conversely, renaming native extension state to describe only its
handle would discard part of the resource account, so that trial was rejected.

## Concrete repair candidates

| Package | Repair | Guard units |
| --- | --- | --- |
| R01 | Label release/teardown actions precisely; retain actual results and lifetimes. | N004.cleanup, N239 |
| R02 | Describe cited definitions and the generator's actual checks precisely. | N005, N057 |
| R03 | State the production case and deliberate fixture conditions at the observations. | N019, N122 |
| R04 | Name the invalid-handle adapter calls and their recorded results. | N017 |
| R05 | Identify which native result determines attempt status and make new-object acquisition conditional. | N025, N216.creation |
| R06 | Keep the concrete publication counterexample and remove its duplicate warning. | N051 |
| R07 | Remove W50's object-directed observation edge; retain later target-path metadata through W53. | N299 |

The seven packages are detailed in `rewrite-candidates.md` and its JSON
counterpart. WORKER-only includes the owning worker graph in the manifest,
worker-specific rendering and regenerated worker DOT/SVG. Other documents and
shared verification rules remain unchanged. The drafts do not add call-site
completeness enforcement or resolve existing citation/setup findings.

## Bounded investigations still needed

| RCA | Clauses kept meanwhile | Unresolved question |
| --- | --- | --- |
| Q01 | N164: mapping identity from size | Did retained launch evidence actually credit the evidence object by matching size, or was the caution precautionary? |
| Q02 | N203: exact child policy effects | Is the guarded inference parent/child effective-access equivalence, exhaustive helper-operation coverage, or another identifiable proposition? |
| Q03 | N266, N270: temporary-frame byte erasure | What data, observer or requirement makes erasure relevant, and what supplies the inference from return/teardown to wiping? |

The ledger gives each RCA established facts, explicitly hypothetical origins,
a bounded search and a completion condition. All four guards remain pending
that work. No new probe, wipe or child-policy guarantee is proposed merely to
resolve the wording. The retained launch evidence referenced by Q01 is
gitignored and local to the checkout; missing artifacts must remain an explicit
limit rather than be silently replaced with a fresh observation.

## Record and validation

`ledger.md` is the readable decision ledger, with exact guard quotations and
shared reasons. `ledger.json` preserves the original IDs, clause routes,
dispositions and secondary-role accounting. `origins.md` and `origins.json`
hold the provenance findings and revision-pinned excerpts. `build_record.py`
reproduces these six ledger/origin/candidate files from the frozen revision
and the unchanged sweep inventory.

`validation.json` records the static checks: complete ID accounting, valid
disposition references, revision-pinned quotations, manifest selectors,
reproducible artifacts and unchanged underlying files. No build, runtime
probe or generator execution was needed for this records-only round. The
generator and source-drift checks listed in the candidates are future repair
validation, not evidence claimed here.

The [associated plan](../../docs/WORKER-INST-DOC-PLAN.md) records this round's
status. Register adjudications remain unchanged. Pass 6 remains reserved for
a fresh agent and has not started.
