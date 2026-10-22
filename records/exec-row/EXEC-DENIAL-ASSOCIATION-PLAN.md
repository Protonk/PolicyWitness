# Exec denial association: solution sketch

A sketch of possible responses to the problem in
[EXEC-DENIAL-ASSOCIATION.md](EXEC-DENIAL-ASSOCIATION.md), for comparison with
solutions formed independently. It is not an implementation plan. It sets no
steps, sequence or verification schedule, and nothing here is decided.

## What a response has to settle

1. Which operation names the exec row admits, and on what evidence.
2. What the guide's correlation table and the failure contract state about
   exec.
3. What independent oracle keeps the row, and the other rows, in agreement with
   what the kernel records.
4. Whether anything forces a log-eligibility decision for attempt kinds added
   later.
5. What, if anything, happens to the constructed `process-exec` line in the
   log-archive corpus.

## The row

- **A1. Admit `process-exec*` instead of `process-exec`.** This matches every
  observed record and is one exact string, consistent with the no-alias rule.
  It rests on one macOS build. Nothing in the repository says what earlier
  releases record.
- **A2. Admit both spellings.** This tolerates a release that might emit the
  bare name. It also makes eligibility claim a record form that no evidence
  shows exists. The rule against aliases is about wildcards, but the same
  caution applies to unobserved names.
- **A3. Choose the spelling by host release.** Eligibility would read the
  dossier's host facts. This is precise if releases differ and needs a capture
  per release to justify each branch. It is complexity with no current
  evidence of a difference.
- **A4. Withdraw exec from correlation.** Leave the row empty, document exec
  as uncorrelated, and exclude kinds without eligible operations from
  `permission_failures_without_record`, so the list does not report every exec
  failure as unrecorded. This is honest without new evidence, but it gives up
  an association the kernel does support.

Interpreter execs are an open edge for every option. A `#!` target may be
recorded under `process-exec*`, `process-exec-interpreter` or both. One
capture would settle it before a choice is fixed.

## The oracle

- **B1. Observed-record replay rows in the controller's tests.** This is the
  record's control, extended to every supported pair. It would sit beside the
  existing replay and `read_fresh` controls in
  `controller/src/log_replay_tests.rs` or in the `sandbox_log` tests. The
  captured lines would live in a fixture that records OS build, policy and
  capture method, in the manner of `tests/fixtures/deny_capture`. Refreshing it
  would be a maintenance capture, not default-test setup. It is deterministic,
  it distinguishes the defect, and it keeps the Python reader out of
  eligibility. A captured line is evidence for one build, and the fixture
  becomes something to refresh on new releases.
- **B2. Expectations written from the guide's table.** These are cheap, and they
  pin the documented contract. They cannot detect this defect: they inherit
  the guide's error, as the record's documented-table variant shows. They are
  useful only beside B1. With both present, a disagreement among code, guide
  and kernel fails something, whichever is wrong.
- **B3. Live association assertions.** Extend a live correlation case to plan
  exec, mach and sysctl denials and assert associations for the records that
  arrive. The input is real, but delivery varies, so a run without the record
  passes vacuously. It is better as the procedure that refreshes or rechecks
  B1's fixture on a new release than as the regression oracle.
- **B4. An envelope-level control.** Extend the supplied-text replay to an exec
  step, so `permission_failures_without_record` is pinned along with the
  association. The shared reply builders produce file steps only. A failed
  spawn's step would need `child_pid: 0` and path diagnostics, but no
  `exec_observation`. It is broader, and larger than the matcher-level control.

## The documentation

- **C1. Correct the guide's correlation table, citing the captured fixture as
  the basis.** It is the only place the documented log spelling appears. Every
  other bare `process-exec` in the documentation concerns SBPL source or the
  query channel, and is correct. This follows whichever row option is chosen.
- **C2. A drift rule binding each correlation-table row to a captured record
  in the fixture.** This would make the documentation claim answer to evidence
  rather than to code. It is structural: it checks presence of a matching
  line, not behavior. The question of how documentation claims bind to code
  and receipts is the subject of
  `tests/suites/source_drift/BINDING-THRU-REPLAY-PLAN.md`, and this defect is a
  candidate case for its replay of historical defects.
- **C3. The archive corpus line.** Leave it, since it tests OS query selection
  and its spelling is irrelevant there. Or note in the fixture's README that
  corpus spellings are declared, not kernel output. Regenerating the archive is
  a maintenance operation on an isolated host and buys nothing for this
  problem.

## The class: other rows and future kinds

- **D1. Observed-record rows for every supported pair.** The record's runs
  already hold mach, sysctl and `open_read` records. The other file actions
  would need captures. This covers what exists today and nothing added later.
- **D2. A completeness gate keyed on admission.** A drift rule would require
  every `(kind, action)` that `mapAttemptKindOrNil` admits to have a row in the
  guide's correlation table, where "no relevant record" is an allowed row. It
  forces the decision to be visible when a kind is added, and it says nothing
  about whether the decision is right. It couples the drift suite to the shape
  of a Swift switch. `check_prediction_unavailable_planner` already parses the
  same file.
- **D3. Make `AttemptOutcomeMappingTests` enumerate `PWAttemptKind` instead of
  a hand list.** This is Swift-local and cheap. It catches a routed kind without
  a failure outcome, the record's other silent omission, but not missing log
  rows.
- **D4. Generate the comparison, log and consumer tables from one source.**
  Copies would always agree. But the comparison and log tables legitimately
  differ: `create` has two log operations and no single query, filters apply
  only to queries, and query and record vocabularies need not coincide. A
  generator would also carry an error like this one into every copy, with no
  oracle beyond the author's belief. It would also end the Python reader's
  independence, which is what catches comparison mistakes today. I would not
  choose this.
- **D5. Have the Python consumer re-derive eligibility.** `tests/AGENTS.md`
  keeps consumers independent of the production classifier. A mirrored table
  reproduces a shared omission rather than detecting it. I would not choose
  this.

## My preference

A1, after one more capture covering an interpreter exec. A2 only if an older
release is shown to emit the bare spelling. B1 for every supported pair (D1)
with B2 kept beside it, and C1. D3 because it is cheap and closes the sibling
gap. D2 is worth considering if new kinds are expected. C3 as a README note.
B3 as the refresh procedure for B1's fixture, not as a gate.

## Evidence that would change this

- A record from an older macOS release, for the same denial, showing the bare
  spelling (favours A2 or A3), or showing no exec record at all.
- An interpreter-exec capture showing a third operation name, which widens the
  row under any option.
- An exec denial attributed to a child PID, for example if the worker's spawn
  mechanism changes. The row's worker-PID-only premise would then need
  revisiting.
- A delivery path whose message text differs from the kernel's. Run 1's
  `sandboxd` lines matched it; a divergent path would make B1's fixture need a
  line per path.
