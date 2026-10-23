# Runtime performance records

Records of the runtime investigation of PolicyWitness as a running program,
and the evidence behind them. The active `*-PLAN.md` here carries the links
between these records and the work they propose, as `records/AGENTS.md`
requires; nothing else links to a record.

Layout:

- `PolicyWitness-Runtime-Exploration-Guide.md`: the staged method the
  investigation follows.
- `PolicyWitness-Boundaries-Findings.md`: the synthesis of the read-only
  report whose questions the investigation starts from.
- `harness/`: the operator-run measurement procedure and its summarizer, with
  their stand-in controls under `harness/controls/`. Added by the plan.
- `evidence/<run-id>/`: committed per run: `manifest.json`,
  `conditions-start.json`, `conditions-end.json`, `run.json`, `SHA256SUMS`
  and the summarizer's output. Small, reviewable, enough to interpret a run
  without its raw files.
- `runs/<run-id>/`: the complete raw output of a run, one directory per
  invocation with the request copy, argv, stdout, stderr and status. Ignored
  by git and present only in the checkout that produced it; a record that
  cites a raw file says so.

A run identifier is `<UTC stamp>-<config>-b<build number>`. Runs are never
overwritten; a procedure that finds its run directory present refuses.
