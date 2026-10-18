# Worker-language resolution

All fifteen remaining units are resolved and implemented: **nine positive
repairs and six elisions**, with no editorial RCA pending. This round starts
from `672374c38b2b728719510300ced1090f1e0e35ef`. The earlier sweep and triage
records remain unchanged. The 102 settled guard units retain their meaning,
and the 205 primary A1 occurrences remain outside the removal exercise.

## Order and findings

A separate reviewer first compared the original, a concrete positive version
and an elided version of every passage. The frozen `positive-trial.md` and
`positive-trial.json` record eight positive wins, three elision wins and four
undecided units. That reviewer did no RCA or history search before freezing
the comparison.

A second reviewer then completed Q01, Q02 and Q03, using those concrete
alternatives. `rca.md` and `rca.json` preserve the bounded searches, exact
references and retained-evidence hashes. The post-RCA comparison selected one
further positive repair and three further elisions. The parent reconciled and
implemented the decisions, and the first reviewer subsequently checked the
resulting meaning against all fifteen units.

The wording trial found a missed trigger: changing S31b's creation caveat alone
left W41 saying “Publishes open/create status.” W41 now names the file-create
attempt status and the open result determining it. The graph's identity issue
also required changing the relationship itself; a positive X3 note with W50
still present was insufficient.

The RCAs established these present purposes and boundaries:

- S18's resource row combined generic VM observations with a size-attribution
  warning. The retained `vmmap` region and `lsof` object have matching sizes,
  but no recorded region-to-object identification. S18 now carries its source
  account; S16f and the ambient-context prose retain the actual VM inventory.
- The child-effects clause supplied an undefined coverage qualification in an
  inheritance column. Retaining the inherited-constraints fact is sufficient
  there; the separate helper-evidence and child-state accounts remain.
- The temporary-frame rows originated in the call-frame completeness audit.
  Their data ownership and the inspected erasure requirements supplied no
  separate whole-frame erasure obligation. The action heading and actual
  return/exit lifetimes now carry the relevant account. Token erasure, early
  exits and private-copy limitations remain intact.

These findings settle the editorial decisions within the named searches.
They do not establish historical author motivation or new native guarantees.
The RCA also corrects the earlier provenance shorthand: all four clauses were
already in the pass-1 inventory; pass 2 transferred them into the manifest.

## Final dispositions

| Unit | Final form | Implemented result |
| --- | --- | --- |
| N004.cleanup | Positive | `Release / teardown action` names the column's content; the redundant explanatory sentence is removed. |
| N005 | Elision | The preparation paragraph retains the named publication cases without the editorial instruction. |
| N017 | Positive | The fixture adapters record invalid-handle uses and return EINVAL; their receipts identify the observed host flow. |
| N019 | Positive | The deliberate low-descriptor setup precedes its observed collision. |
| N025 | Positive | The action table identifies the open result determining attempt status and retains the later discarded returns. |
| N051 | Elision | The repeated missing-publication warning leaves the change table; the concrete counterexample and event-order account remain. |
| N057 | Positive | The worker caption, summary and citation columns name symbol-presence and definition checks. |
| N122 | Positive | The stdio cell names L's observed endpoints; prose names the actual launch configuration. |
| N164 | Positive | S18 becomes `Source-only; mapped before compilation`; the general VM observations remain with ambient state. |
| N203 | Elision | S28 retains `Inherited sandbox constraints`. |
| N216.creation | Positive | S31b states conditional creation; W41 names attempt status from the open result. |
| N239 | Positive | The action column records a conditional process-group kill request; continuing group lifetime remains explicit. |
| N266 | Elision | N9a retains `Return or process exit` under the action heading. |
| N270 | Elision | N9b retains `Return or process exit` under the action heading. |
| N299 | Elision | W50 and X3's identity warning are removed; S31b, X3 and W53 remain. W53 names later path-resolution results. |

The host function `enrichPathDiagnostics` supplies path-resolution results,
so W53 uses that wording in place of the draft's broader “target-path metadata.”
No resource node was removed: the worker graph retains 83 nodes and now has
54 edges. Moving the acquisition cluster's heading from bottom to top corrects
an overlap with an edge label caused by the changed layout.

The generator's worker-specific branch leaves other graph captions unchanged.
Its existing contract control formerly required the negative sentence
verbatim. It now accepts the precise positive form for the worker, rejects
omitted scope and stronger coverage claims, and retains the other graphs'
checks. The column-order control expects the new worker citation heading while
continuing to reverse and check the declared columns. G10's documented meaning
and the shared citation-resolution implementation are unchanged.

## Validation and commits

Implementation commits:

- `5e4f5d3`: frozen trial/RCA records; observation, lifetime and evidence-scope repairs.
- `b1f5697`: worker citation presentation and caption controls.
- `143c8a4`: path-observation relationship and graph layout.
- The commit of this closeout records final validation and corrects the
  column-order control's worker heading expectation.

The final command was:

```sh
PW_TEST_OUT_DIR=tests/out/runs/worker-language-resolution-final-20261017 \
  tests/run.sh --case source_drift/architecture_documentation \
               --case source_drift/generator_contract
```

Run `20261018T033452Z_c544be35` passed both cases, zero failures or skips:
nine architecture controls and eighteen generator controls. These are
documentation/generator checks, not runtime observations. Evidence is
gitignored and local under the named output directory. `validation.json`
records hashes of the final code/documents and run artifacts.

The earlier run `20261018T033309Z_2ad07125`, at
`tests/out/runs/worker-language-resolution-20261017`, is preserved as failed:
architecture checks passed, while the column-order control still expected
`Checks`. Updating that expectation and the graph layout justified the fresh
two-case run; the earlier failure is not credited as a pass.

The generator's direct check and no-op regeneration passed. Scope comparison
confirmed that every other architecture graph, style and generated tour/figure
is unchanged. All resource identities and citations on retained items survive;
the twelve manifest deltas beyond the column-key rename are recorded in
`validation.json`. Of the 102 settled guard quotations, 101 remain after
whitespace normalization. N012's surrounding launch passage adds the exact
configuration while retaining its two observations; the semantic review
checked that preservation separately.

The parent inspected the rendered map in three panels and corrected the
acquisition-heading overlap. `implementation-review.md` records the separate
reviewer's scope and result. No worker/native source, evidence contract, build,
signature or runtime behavior changed. No new runtime probe was run.

## Handoff to the fresh pass-6 agent

Read the resulting [worker account](../../docs/WORKER.md), its owning manifest
and renderer, and this round's diff from `672374c`. The positive trial, RCAs,
final table above and validation receipt supply the reasons for the fifteen
decisions. The earlier triage remains the record for the 102 retained guards;
this round did not reopen them as removal candidates.

The [associated plan](../../docs/WORKER-INST-DOC-PLAN.md) retains the register.
Rows 10, 19 and 22 remain reopened; rows 23–24 await adjudication; rows 25–28
retain their recorded states. The repairs do not close those findings or
authorize the separate row-15 Mach fix. Native mapping identity, universal
child effective-access equivalence and frame-byte erasure were not established
by these editorial decisions. Pass 6 has not started. No push or release.
