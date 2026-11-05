# Documentation validation: citation repair ready for rerun

The user resumed validation. The saved candidate matched every recorded file
hash and patch hash before execution, and the fresh output path did not exist.
Both direct generator checks passed:

```sh
env -u PYTHONOPTIMIZE tests/lib/python.sh docs/generate_limits.py --check
env -u PYTHONOPTIMIZE tests/lib/python.sh docs/generate_architecture.py --check
```

They reported 95 limits, 15 questions and 43 matrix rows current; and five
architecture graphs, 178 nodes and 187 edges current. These are mechanical
freshness/manifest results, not behavioral or reader-comprehension findings.

## One coordinated execution

The four-case selection was inspected with `--list`, then executed once outside
the automation sandbox:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-docs-01 tests/run.sh \
  --case source_drift/architecture_documentation \
  --case source_drift/limits_documentation \
  --case source_drift/generator_contract \
  --case runner_unit/pwrunner_core_unit_executable
```

Run ID: `20261105T043512Z_9e9ed163`. Duration: 128,239 ms. All four selected
cases completed: three pass, one fail, no skipped/unrun cases and zero recorded
sleep overlap. The signed app was valid before execution and unchanged after;
its 45-entry inventory also equals the earlier repair run's inventory.
Build 1121 was reused as unchanged implementation equipment. No distribution
build was run and the revised guide has not been staged as a new distribution.

| Case | Result and scope |
| --- | --- |
| `source_drift/limits_documentation` | Pass; 22 completed controls covering inventory/copies, standalone guide, staging and rejection behavior. |
| `source_drift/architecture_documentation` | Pass; 10 completed controls covering manifest/DOT/SVG stamps/document regions, citations and stale-copy refusals. |
| `source_drift/generator_contract` | Fail; 26 completed controls, with one failing top-level test: prose-baseline consistency. |
| `runner_unit/pwrunner_core_unit_executable` | Pass; 525/525 Swift tests, followed by the three Rust/independent-consumer replay checks. New diagnostic value observations and whole-path depth/UTF-8 boundary assertions passed, as did the earlier actor-parameter ownership assertion. |

The candidate remained byte-identical to `documentation/pretest-state.json`
through terminal completion. The original console transcript was attached as
`test-console.log` under the checkout lock after checking owner/run IDs,
resolved output path and terminal state. SHA-256:
`dfe8e43e40850ef857aa8740c8dc80b8a3a41446b8edfdf8117dc84bfd28921c`.

## Failure and prepared correction

G11 requires a source citation to put its backticked symbol inside the link.
The new ARCHITECTURE prose instead placed `runActors` before a filename link,
and listed `serviceOutbound` and related symbols before another filename link.
The prose scan correctly reported these as two new unverified citation-pair
sites. This was not a missing file/anchor, runtime failure or recurrence of F1.

After execution completed and its source identity was recorded, root converted
both passages to direct symbol links. The handoff paragraph now directly links
all six named methods/functions to their source files. No prose-baseline
exception, generated region, generator, test or production source changed.
`git diff --check` passed for the correction. No generator or test was rerun.

`documentation/verification-01.json` pins the tested snapshot, terminal result
and corrected candidate; `documentation/candidate-after-citations.patch`
preserves the corrected patch. The failed historical run remains failed.

## Resume recommendation

Rerun only `source_drift/generator_contract` in fresh output
`tests/out/runs/doc-lookback-docs-02`. It directly checks the repaired symbol
links and prose baseline. The limits and Swift inputs are unchanged. The
architecture suite's manifest, generated regions and figures are unchanged;
retaining that pass after the authored citation-only change is a reviewed
applicability exception, not an assertion that it executed after the edit.

No rerun has started. This return respects the user's earlier instruction to
pause before reruns. Final reader preparation/dispatch remains pending after
validation. F1 stays explicitly deferred; its fixture was not selected and
no further flakiness investigation was opened.
