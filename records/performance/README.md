# Runtime performance records

Records of the runtime investigation of PolicyWitness as a running program,
and the evidence behind them. The first built-in-runner cycle is complete.
Any later work's associated `*-PLAN.md` carries links between these records
and proposed work, as `records/AGENTS.md` requires; indexes name records
without linking to them.

Layout:

- `PolicyWitness-Runtime-Exploration-Guide.md`: the staged method the
  investigation follows.
- `PolicyWitness-Boundaries-Findings.md`: the synthesis of the read-only
  report whose questions the investigation starts from.
- `RUNTIME-MEASUREMENT-BRIEF.md`: measurement definitions, pilot observations,
  verification credits and the operator handoff.
- `RUNTIME-INVESTIGATION-REPORT.md`: the completed first-cycle findings,
  operator-run measurements, pilot comparison and unresolved boundaries.
- `harness/`: the operator-run measurement procedure and its summarizer, with
  their stand-in controls under `harness/controls/` and pilot-sized counts in
  `harness/configurations.json`.
- `evidence/<run-id>/`: committed per run: `manifest.json`,
  `conditions-start.json`, `conditions-end.json`, `run.json`, `SHA256SUMS`
  and the summarizer's output. Small, reviewable, enough to interpret a run
  without its raw files.
- `evidence/<control-batch>/`: the external terminal transcripts, observed exit
  statuses and assertion ledger for each bounded control or pilot in that batch.
- `runs/<run-id>/`: the complete raw output of a run, shared specimen copies
  and one directory per invocation with argv, stdout, stderr and status. Ignored
  by git and present only in the checkout that produced it; a record that
  cites a raw file says so.

A run identifier is `<UTC stamp>-<config>-b<build number>`. Runs are never
overwritten; a procedure that finds its run directory present refuses.
