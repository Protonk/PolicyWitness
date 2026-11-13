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
check binding them. Changes that would make them stale without any test
failing include a fourth action recording `observed_path`, a change to the
stat calls a fresh action makes, a reordering of the planning tests, and a
change to when the host computes path diagnostics.

## Pass 3 — Examples from their owner

The quick start already produces an example of this topic from app-owned
material: `lesson create` emits the request, and its result holds a planning
exclusion, a worker `observed_path` and both host diagnostics for one string.
The guide's new subsection "The quick start's records" selects those fields
from the reader's own `create-result.json` with one `jq` expression and reads
them in time order. It adds no request, command or lesson. The quick start's
`stat` line is named as a fifth observation.

The `jq` expression was run against a result produced by the staged app
(contract `development:aa400348…`) on 2026-11-13 and returned the fields the
text describes. Like the guide's other `jq` fences it is optional and no
harness case executes it, so its field names are a maintained copy.

No fixture was copied. `tests/fixtures/contract/path_diagnostics.json` holds
constructed three-state cases whose paths are placeholders, and the matrix
rows do not carry path records, so neither shows a reader a real sequence.

### A local two-phase observation

To check the tables against a live reply, one specimen ran once through the
same staged app under `(allow default)`, in a scratch directory holding a file
`real`, a symlink `link` to it and a dangling symlink. The first phase opened
`link` with `open_read`, read `link` and `real` with `read_fresh`, opened the
dangling link and ran `create_fresh`; the second phase unlinked `real`.

- `open_read` of `link` recorded `observed_path` ending in `real`.
- The two `read_fresh` steps recorded equal device and inode numbers and
  `observed_path: null`.
- Every first-phase query on `link` and `real` was answered by the validator
  with `query_first`, and each carried `realpath_resolved: null`: the host's
  pass ran after the second phase's unlink.
- The dangling link was excluded at planning; its open failed with errno 2,
  and its attempt diagnostics listed only the parent form.
- `create_fresh` recorded `preopen_stat` with `rc: -1` and errno 2, then
  `opened_stat` and `written_stat` with one inode and sizes 0 and 1. A shell
  `stat` afterwards reported the same inode.

This is one unretained observation on one machine. It agrees with the tables
and adds no support grade. A guide exercise built on it would need a new
request and coverage in `witness_contract/guide_workflows`, so it stays an
adjacent opportunity: a lesson that opens a symlink and unlinks its target in
a later phase would show the after-every-phase rule with the reader's data.

## Pass 4 — Support beside its claim

The current arrangement is retained, with one citation added.

| Record | Support beside the claim | Limit |
| --- | --- | --- |
| Planning check | The query admission and planning rule in `12-probes` carries its own support and the sentence that planning and later diagnostics "have separate times and owners". | Not re-read this cycle beyond the rule text. |
| `observed_path` | The subtree "Record-field support" owner in `31-steps`, source read. | It cited assembly and decoding but not the worker call that produces the path. |
| Descriptor and pre-open stats | "Publication support" under the fresh-operation rule, check read against `FreshWriteEvidenceTests`. | Its own limit says fresh-read sequencing is source-supported. |
| Host path diagnostics | "Path support" under "Add host path observations", check read against `PathDiagnosticsTests`. | Constructed parents and symlinks; the three test cases cover wire states, leaf and parent resolution and skipped non-path attempts. |

The record-field owner now also cites `capture_observed_path`, which was read
with its three callers this cycle, and its context names the descriptor-path
capture. This is an owner-only change: `docs/contract/public.json` is
byte-identical before and after regeneration.

No owner was added or merged. `CWorkerTests` has a case that runs the real
worker on `/etc/hosts` and asserts `observed_path` is `/private/etc/hosts`,
and no contract owner credits it. Crediting it needs a rule or field-level
claim to attach to, which follows the maintainer's decision on the contract's
`observed_path` sentence. Source inspection, constructed checks and native
evidence keep their separate grades.

## Consultation

The one consultation asked a read-only Opus reviewer, without my reading of
the code, whether the new guide section claims more than the contract and
producer source establish or omits a condition the source applies. It read the
section, `31-steps` and `12-probes`, and the planning, validator, worker,
decoding, step-assembly and path-enrichment sources. It reported no sentence
implying which object the query consulted and none claiming agreement or
disagreement. It reported two wrong statements, eight overstatements or
omitted conditions and one doubt. All were checked against the cited source
and applied:

- **Wrong.** `validator_not_invoked` was said to leave planning unknown. The
  step leaves it unknown; the phase's `collection_status` does not, and
  `not_reached` means the phase was never planned.
- **Wrong.** A failed open's "`rc` and `errno`" were offered as the open's own.
  `attempt.rc` is the worker's status; only `errno` is the native value.
- A successful open with `observed_path: null` also arises when the host
  cannot decode the returned bytes as UTF-8.
- `target_relation` was described without its filter-kind condition and as a
  byte comparison. See the finding below.
- The quick start row said the attempt created the file. `create` does not
  distinguish creating from opening, so the row now states the conditions.
- `firmlink_resolved: null` now names the path the mapping is applied to.
- The pair-exclusion sentence was removed: no excluded pair uses `path`.
- The reporting-failure scope now covers the minimal form and the retained
  `missing_reason`.
- The quick-start reading is conditional at each step and no longer says the
  file "exists now".
- The device and inode paragraph now states the filesystem property its
  inference needs.
- The count of record kinds in the quick-start subsection was removed.

### Finding outside this cycle's edits

`comparisonEvidence` compares `filter_value` and `requested_path` with Swift
string equality, which treats canonically equivalent Unicode as equal. Reading
rule 4 and one FAQ answer say `same_submitted` compares "bytes", and
`path_diagnostics.same_as_input` does compare UTF-8 bytes. Two submitted
strings with different bytes and one canonical form would therefore read
`same_submitted` while a diagnostic treats them as different. The contract's
field sentence says "compares submitted strings". Choosing between a byte
comparison in the producer and "strings" in the two guide sentences is a
decision about a public meaning, so nothing was changed.
