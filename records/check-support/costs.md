# Cost and evidence boundaries

Inventory source: `cf0136bbb6366d5f787c3547ec69d757772898c0`.
`cost-facts.json` commits compact original-run measurements and receipt hashes.
The raw directories named there are local, gitignored evidence, read only by
D1 and retained by the primary executor. Later removal does not remove the
numbers or their provenance from this package. No D1 live battery was run.

| Historical run | Run ID / source provenance | Observed elapsed | Interpretation |
| --- | --- | --- | --- |
| drift-plan-investigation-20261027-02 | 20261027T175448Z_a3635ceb; attached clean source snapshot/report identify 1612eb5e0bd503f0185dda9cda0331be0d9a764f | 349.757s | Historical full selected run; no per-control receipts. The attached profiler separately records discovered entries and parsing/generator cost. |
| drift-cost-candidate-01 | 20261027T230701Z_a7cce91f; executor supplied source22f688d7d4c1aefe890c41db03a897141796f0e9, not independently re-established by a whole-source snapshot here | 199.987s | Earlier control receipts; unittest launch/input fields absent, so their zero sums mean unmeasured, not zero work. |
| drift-acceptance-fixes-03 | 20261027T233059Z_1f7c68fa; attached source.json HEAD d3ded472 plus recorded working.diff, attached after run with no intervening source edits according to its observation | 203.017s | Instrumented receipts identify input snapshots and direct launches. Do not mislabel this as clean d3ded472 or cf0136b execution. |

All three run summaries report success. The latest snapshot differs from cf0136b
in README, retention, investigation/planning records and plan files, listed in
the JSON. Checking code is represented identically, but README itself is a
registered input. These measurements inform order of cost, not a reused passing
credit for the whole present checkout or a benchmark proving speedup.

Latest-run per-module observed control elapsed seconds and direct wrapper
launches (rounded; totals are not wall-time decomposition):

| Canonical case | Controls | Seconds | Direct launches |
| --- | ---: | ---: | ---: |
| source_drift/runner_source_manifests_agree | 188 | 17.07 | 8 |
| source_drift/limits_documentation | 20 | 34.27 | 74 |
| source_drift/contract_versions | 16 | 5.41 | 87 |
| source_drift/architecture_documentation | 10 | 13.33 | 19 |
| source_drift/build_documentation | 16 | 10.23 | 53 |
| source_drift/generator_contract | 26 | 38.68 | 118 |
| source_drift/markdown_reader | 36 | 1.27 | 7 |
| source_drift/direct_python_start | 6 | .71 | 0 |
| preflight/build_entry_controls | 15 | 26.97 | 42 |
| preflight/native_policy_controls | 3 | 32.45 | 69 |
| preflight/native_source_controls | 8 | 10.19 | 19 |

Counts include fixture/control records where the owning receipt does; they are
not a uniform test count. Planner elapsed covers recorded scenarios, not an
OS process census; nested compilers/Meson/helpers are outside direct launches.
Input snapshot counts, selected entries and bytes are repeated observations,
not distinct filesystem files or all reads. Missing measurement can be settled
by one targeted instrumented selection if a concrete performance decision
requires it. D1's paper review trigger does not require a new full run to choose.

The earlier discovery profiler visited222,124 entries for Markdown and214,946
for shell (214,664 under tests/out in each), taking7.116s and6.802s respectively.
Those are historical costs at1612eb5, not the now-pruned tree reader's costs.
New machinery should not recreate unbounded raw-output scans to produce a
reverse index. Read declared claim/receipt inputs and existing registered
document scope only. Churn and review cost of the paper design are accounted
separately after open replay; estimated human decisions must not be mixed into
these machine timings.
