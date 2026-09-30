# Response 12 verification of the comparison matrix

These are the receipts behind the scenario matrix in
[DRIFT-REMOVAL-PLAN.md](../../../../DRIFT-REMOVAL-PLAN.md). Seven of the
matrix's nine columns — `prediction`, `observation`, `observation_basis`,
`operation_relation`, `target_relation`, `order` and `limitations` — are
unchanged by that plan, so each row's values for them are checkable against the
shipped response 12 producer before the matrix fixture becomes the single source
of comparison expectations. The `obligations` object and
`comparison_conditions` are not checkable here: no build emits them.

Two sources cover the rows.

**Retained evidence.** `match_retained.py` walks every reply under
`tests/out/runs/`, reduces each `steps[].comparison` to the seven columns with
the five removed `limitations` strings dropped, and looks for each matrix row's
tuple. Twenty-five rows matched, counting the three `as S01` aliases (S23, S24,
B7). `retained_row_match.txt` is its output, naming the suite and step that
supplied each match. Its `NO EXACT LIVE MATCH` list is exactly the set the live
runs below cover, plus S22 as corrected.

**Live runs.** The rows retained evidence did not cover were run directly
against `dist/PolicyWitness.app`. `specimen_a.json` covers S06, S10, S12, S18,
S21 and S22 with the real validator; `specimen_b.json` covers B1, B3, B5, B6 and
B7 with `stub_validator.py` steering the verdicts. `run_a.json` and
`run_b.json` are the raw envelopes. `match_live.py` prints the per-row
comparison; `live_row_match.txt` is its output.

One row was wrong: S22 also carries `submitted_target_unavailable`, because a
`none` filter submits no target to compare. The plan is corrected.

## What the runs established about the specimens

- An `unlink` attempt reaches `operation_relation: matched` only against a
  `file-write-unlink` query. `file-unlink` and `file-read-data` both yield
  `operation:different`.
- A steered validator cannot omit a verdict by skipping an output line: the host
  counts uniquely associated records and refuses the run with
  `validator_unavailable` before any comparison exists. `specimen_b.json`
  therefore uses the validator I/O deadline seam
  (`validator_io_timeout_ms: 500` plus a stub that answers the other steps and
  stalls), and its run-level outcome is `validator_no_reply` while B1, B6 and B7
  keep their verdicts and `query_first` order.
- `specimen_b.json` unlinks the paths it queries, and a run that fails after
  release still performs its attempts, so its files must be recreated before
  every run. The absolute paths in both specimens are the verification run's
  scratch directory; the matrix fixture parameterizes them.

## Provenance

`run_a.json` and `run_b.json` carry their own build stamp: `v0.2.4`, commit
`ff2b192`. Nothing under `runner/`, `controller/` or `docs/contract.json`
changed between that commit and the plan's inventory baseline `df333b4`, so
these replies describe the current producer. Both runs used
`--no-log-capture`; neither needed the unified log.

Rerunning this verification against a response 13 integration candidate is the
acceptance capture named in the plan's Verification section, and these two
specimens are its inputs.
