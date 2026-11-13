# Third coalescing cycle: path and object observations

This cycle follows [DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md)
through passes 1 to 4 for one topic, starting from `ae4f6185`.

## Topic, scope and reader questions

The topic is what a reply records about a step's file or exec target: the
submitted strings (`sandbox_check.filter_value`, `attempt.requested_path`), the
worker's `observed_path`, the fresh-descriptor stat records under
`attempt.fresh_read` and `attempt.fresh_write`, and the host's
`path_diagnostics`. The cycle explains existing observations and their limits.
It changes no behavior. Extension lifecycle records, the attempt-outcome
catalog, exec child observations and reporting degradation stay outside it.

1. What does each representation establish about the submitted target or the
   object encountered?
2. Who observed it, and when relative to query collection and the attempt?
3. When resolution fails, observations differ, or evidence is absent, what
   remains established?

None of the representations establishes which runtime object the query
consulted. Every pass keeps submitted strings, worker observations and later
host diagnostics distinct.

## Pass 1 — Ownership

| Question | Concept | Owner | Current presentations | Checks | Treatment |
| --- | --- | --- | --- | --- | --- |
| 1, 2 | Submitted strings | Contract: `filter_value` and `requested_path` fields in `31-steps`; query and target admission in `12-probes` | Guide per-step notes; reading rules 4 and 10 | Comparison matrix relations; request corpus | Keep. Restate observer and use in the guide's new reading section. |
| 2, 3 | Planning-time resolution | Contract: query admission and planning effect in `12-probes`; `limitations` vocabulary in `31-steps` | Guide quick start, ordered phases, `sandbox_check.outcome` list | `planValidatorQueries` unit controls; `witness_contract` create and phase cases | Keep. Place it in the guide's time sequence, with the branch order that decides whether the check ran. |
| 1, 2, 3 | Worker `observed_path` | Contract: one field sentence in `31-steps`; limit `observed_path` | Guide per-step note; WORKER inventory row n10 | `runner_use_c_worker` and `runner_c_worker_harness` cases | Guide states the actions, the moment and each cause of `null`, checked against the worker source. Contract sentence left as is; see ownership questions. |
| 1, 2, 3 | Fresh-descriptor stat records | Contract: `identity`, `stat`, `fresh_read`, `fresh_write` subjects in `31-steps`; action table in `12-probes` | Guide "Extension and fresh-read output" and attempt-kind catalog | `FreshWriteEvidenceTests`; matrix rows S26 and S27; `extension_boundaries` | Keep the field reference. Explain in the reading section what an identity supports and which call produced each record. |
| 1, 2, 3 | Host `path_diagnostics` | Contract: `query_paths` and `attempt_paths` subjects and the "Add host path observations" rule in `31-steps` | Guide `path_diagnostics` and `attempt.path_diagnostics` references; reading rule 11 and its test-contract original | `PathDiagnosticsTests`; `tests/fixtures/contract/path_diagnostics.json` with `checker_controls`; `queries_precede_attempts` | Keep both references. State in the reading section that the pass runs once after every phase, and how omitted, null and string forms read. |

Source read for this map: `planValidatorQueries` and
`pathFilterIsUnresolvable` (`CWorkerRequestPlanning.swift`), the per-phase
planning call in `CWorkerOrchestrator.swift`, the validator's `sandbox_check`
call (`sb_api_validator.c`), `capture_observed_path`, the three open actions,
`attempt_file_read_fresh` and `attempt_file_write_fresh`
(`pw_probe_runner.c`), `decodeFreshRead` and `decodeFreshWrite`
(`CWorker.swift`), `buildAttemptResult` (`CWorkerStepResults.swift`),
`enrichPathDiagnostics` (`PWRunnerService.swift`) and `PathUtils.swift`.

### Reading problems found

1. **No account sets the representations side by side.** The guide describes
   them in six places: per-step notes, the `sandbox_check.outcome` list,
   "Extension and fresh-read output", the attempt-kind catalog, reading rules
   4, 6 and 11, and two `path_diagnostics` references. A reader comparing two
   of them has to find the observer and time of each separately.
2. **`observed_path: null` has four causes under one phrase.** The per-step
   note says "explicit `null` otherwise". The source gives: no completed
   worker result, an action that never captures it, a failed open, and a
   successful open whose `F_GETPATH` call failed. The last leaves `outcome:
   ok` beside `null` with no error recorded.
3. **"After orchestration" is not related to phases.** The host computes every
   step's diagnostics in one pass after all phases. A first-phase step's
   diagnostic therefore reflects every later phase's actions. The guide says
   the diagnostic "can see a path changed by an attempt" without that scope.
4. **The planning check is the only path observation before the query, and it
   leaves no path.** Its result appears only as an exclusion. A path query
   the validator answered implies the host's `realpath` succeeded at planning,
   which the guide uses in rule 11 without saying so. A query that was merely
   not excluded does not imply it: when no validator ran for the phase,
   planning may not have run. The check runs third, after the pair and
   filter-kind exclusions, so an excluded query does not always carry it.
5. **Descriptor identity is documented as a shape, in a section introduced as
   extension output.** "Extension and fresh-read output" opens by saying its
   records sit "separately from ordinary `steps`", then lists two
   `steps[].attempt` records. No text says what equal or different identities
   support.
6. **Differences between representations are unexplained.** `observed_path`
   can differ from `requested_path` and from
   `attempt.path_diagnostics.realpath_resolved`. Each pair has different
   observers, calls and times.
7. **An omitted `path_diagnostics` form and a `null` form mean opposite
   things.** The reference states the three states correctly. The reading
   rules mention only `null`.

### Ownership questions retained

- The contract's `observed_path` field says "Path observation supplied by the
  worker slot when available." It names neither the three actions nor the
  call. The guide's fuller statement rests on the worker source and two test
  descriptions. Stating the actions in the contract would add a public
  commitment, so it needs a maintainer decision.
- The fresh-descriptor field reference sits under "Extension and fresh-read
  output" in the guide. Moving it would change inbound anchors and the
  extension section's own reading path, so this cycle links to it.

### Adjacent opportunities for a later cycle

- "Extension and fresh-read output" mixes run-level extension records with
  per-step fresh records under one introduction.
- The attempt-kind catalog and the contract's action table both describe each
  file action's native calls.
- `firmlink_resolved` is described in the guide with implementation detail
  (map loading, built-in fallback) that belongs in a tour.
- Exec targets carry `attempt.path_diagnostics` but no worker path
  observation; the exec observation records are their own topic.

## Pass 2 — Consolidated explanations

The guide gained one section, "Reading path and object observations", placed
before the two `path_diagnostics` field references. It has three parts.

- **"Who observed what, and when"** is a seven-row table: the two submitted
  strings, the planning check, `observed_path`, the pre-open stat, the
  descriptor stats and the host diagnostics, each with its fields, observer,
  call and time. A paragraph gives the per-phase sequence and says that only
  `comparison.order: query_first` places a query answer before its phase's
  actions.
- **"What each record establishes"** gives one entry per record and a
  paragraph on comparing two records, including what equal and different
  device and inode numbers support.
- **"When a record is absent, null or different"** has three tables, for host
  diagnostics, the worker's path observation and the stat records. Each row
  gives what the reply shows, what it means and what remains established.

Smaller edits: the per-step note and the comparison section's "same runtime
object" entry link to the new section; the `path_diagnostics` reference says
one pass covers every step after the last phase; and the "Extension and
fresh-read output" introduction no longer says its two `steps[].attempt`
records sit outside `steps`.

No contract source, reading rule, generated region or public snapshot changed.
The retained ownership question about the contract's `observed_path` sentence
stands.

### Direct source check of the new tables

Each row was compared with its producer before commit. The comparison changed
the draft in five places:

- A `path` qualifier on "a query the validator answered passed the check".
- The statement about unknown planning now names
  `missing_reason: validator_not_invoked`. A first draft said any synthetic
  result without a `query_plan:` limitation leaves planning unknown, which is
  wrong for `validator_no_verdict`: there a validator ran, so planning ran.
- `realpath_resolved: null` no longer implies only absence or traversal.
- The parent-resolved, leaf-unresolved row gives its two causes as examples.
  A leaf the host cannot reach through an unsearchable parent is a third.
- The tables are scoped to an ordinary reply, because a
  `runner_reporting_failed` reply removes `comparison.limitations`.

Branch orders confirmed: planning tests pair, then filter kind, then path
(`planValidatorQueries`); `parentRealpathResolved` returns nil for a
non-absolute target, a trailing slash, a `.` or `..` leaf, or an unresolved
parent; `decodeFreshRead` returns only the open pair when the open failed;
`decodeFreshWrite` omits each stat whose slot value is the not-reached marker.

### Alignment duties added

The three tables restate producer behavior and contract field meanings with no
check binding them. Three facts would make them stale without any test
failing: a fourth action recording `observed_path`, a planning exclusion pair
that uses the `path` filter kind, and a change to when the host computes path
diagnostics.
