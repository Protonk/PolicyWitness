# Runtime performance records

Records of the runtime investigation of PolicyWitness as a running program,
and the evidence behind them. The first built-in-runner cycle, two
log-observer pilots and the host-lifetime, phase-barrier, late-publication
and pre-touch investigations of build 853 are complete.
The original raw runs are not retained. Committed reports, summaries, manifests,
checksums and terminal records remain; calculations requiring raw observations
cannot be reproduced from these exports alone. All fixture commands describe
the original `records/performance/` layout and recorded dependencies. Scripts
and captured evidence retain their original bytes and paths; this archive is
not a runnable replacement for that environment.
The first-cycle and log-observer procedures and their source files are
historical, unmaintained equipment for those runs. They require the recorded pre-retirement application and inputs;
they are not measurement commands for the maintained application. The
[archived source tree](https://github.com/Protonk/Observer/tree/0d0678f375103251573bd32bb9c2a6f4eaa58a8e/source)
preserves their former integration. Recorded hashes, commands and evidence
remain unchanged.

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
- `PolicyWitness-Log-Observer-Investigation.md`: the log-observer investigation's
  questions about supplementary-collection cost and delayed retrieval.
- `LOG-OBSERVER-INVESTIGATION-REPORT.md`: two completed log-observer pilots,
  historical-query costs and fixed-event retrieval comparisons.
- `PolicyWitness-Host-Lifetime-Investigation.md`: the host-lifetime
  investigation's questions about host identity, admission, retirement and
  relaunch.
- `HOST-LIFETIME-INVESTIGATION-REPORT.md`: built-in host instancing, admission
  and retirement observations, controls and the untested external case.
- `host-lifetime/`: the external process observer and its run reader.
- `PolicyWitness-Phase-Barrier-Investigation.md`: the phase-barrier
  investigation's questions about the worker's wait between arrival and
  release, and its own proceed deadline.
- `phase-barrier/`: the driver-seam fixture that holds the phase-boundary
  callback, its schedule runner and reader.
- `PHASE-BARRIER-INVESTIGATION-REPORT.md`: worker CPU during held phase
  boundaries, the deadline-crossing control and measurement limits.
- `PolicyWitness-Late-Publication-Investigation.md`: the late-publication
  investigation's questions about evidence published during worker exit grace.
- `late-publication/`: the driver-seam fixture and CLI schedule for the four
  sentinel-expiry cases, and their reader.
- `LATE-PUBLICATION-INVESTIGATION-REPORT.md`: what exit grace retains after a
  host sentinel deadline, and what the exit request can interrupt.
- `PolicyWitness-Pretouch-Investigation.md`: the pre-touch investigation's
  question about whether touching the evidence region before application
  decides post-apply publication.
- `pretouch/`: the host harness and experimental child that vary which pages
  are touched before application, the test-harness patcher, the schedule
  runner and reader.
- `PRETOUCH-INVESTIGATION-REPORT.md`: first-touch stores after bare
  deny-default application at versions 1–3, the mapping controls and the
  shipped-worker comparison.
- `log-observer/`: the pinned pilot configuration, bounded query procedure,
  content-comparison reader and stand-in controls.
- `harness/`: the operator-run measurement procedure and its summarizer, with
  their stand-in controls under `harness/controls/` and pilot-sized counts in
  `harness/configurations.json`.
- `evidence/<run-id>/`: committed per run: `manifest.json`,
  `conditions-start.json`, `conditions-end.json`, `run.json`, `SHA256SUMS`
  and the summarizer's output; host-lifetime, phase-barrier,
  late-publication and pre-touch runs have `summary.json`, `units.json` and
  `run-record.json`. Small, reviewable, enough to interpret a run
  without its raw files.
- `evidence/<control-batch>/`: the external terminal transcripts, observed exit
  statuses and assertion ledger for each bounded control or pilot in that batch.
- `runs/<run-id>/` (not retained): the original ignored raw output, shared
  specimen copies and per-invocation argv, stdout, stderr and status.

A run identifier is `<UTC stamp>-<config>-b<build number>`; host-lifetime
runs are `<UTC stamp>-hostlife-<label>`, phase-barrier runs
`<UTC stamp>-phasebarrier-<label>`, late-publication runs
`<UTC stamp>-latepub-<label>` and pre-touch runs `<UTC stamp>-pretouch-<label>`,
with the build number in the label. Runs are never
overwritten; a procedure that finds its run directory present refuses.
