# F-reconcile — assessment of the `runner reconcile` continuation (DT-69 through DT-80)

Read-only assessment at HEAD `837296af`. Review entries assessed:
`records/DOCUMENTATION-TRACE-REVIEW.md` lines 2542–3183 ("Additional findings:
`runner reconcile`", its identity and reproduction conventions, DT-69 through
DT-80 and its coverage and limits section). Two coverage-map subjects:

- Subject 1: DT-69–73 and DT-75–80, with the two unnumbered sections.
- Subject 2: DT-74.

Unnumbered sections are labelled `RC.x` (reproduction conventions) and `RL.x`
(coverage and limits). These are labels for this file only; no DT entry is
renumbered.

## Orientation and evidence availability

**Source correspondence.** `git diff --stat 87422530 HEAD` is empty for
`controller/src`, `controller/README.md`,
`docs/contract/50-installation.surface.md`, `docs/limits.json`,
`docs/LIMITS.md`, `docs/RESPONSE.md`, `tests/suites/runner_byoxpc`,
`tests/fixtures/byoxpc` and
`tests/suites/witness_contract/opt_in/guide_workflows.py`. The only changes in
`docs/architecture.json` since then are the guide-staging rows, not the
reconcile rows. `git diff --stat 8b5de2b2 HEAD` and `git diff --stat b16f32d0
HEAD` are also empty for `controller/src` and the BYOXPC suite and fixture.
Every source and document location the review cites for this subject is still
at the cited line; the review's line numbers are usable as written.

**The review's executed evidence is not available locally.**

| Evidence | State on 2026-11-17 |
| --- | --- |
| Constructed-control driver and outputs under the review's session scratchpad (`…/814e589d-…/scratchpad/`) | Directory absent. Rows survive only as reproduced in the review. |
| Retained run `tests/out/runs/plain-help-byoxpc-b16f32d0` (artifacts 234–294) | Absent. `tests/out/runs/` holds only the eleven `trace-*` runs. |
| Signed app the review ran (SHA-256 `4bcd308b…`, commit `8b5de2b2`, build 1482) | Replaced. `dist/PolicyWitness.app` is build 1519 at `2f4d76e4` (SHA-256 `c464c5ef…`), compiled from the same `controller/src`. |

**What this pass ran.** `--version`, `runner list` and `runner reconcile` once
each on the current app, for orientation only: the default registry holds no
runners; reconcile returned `ok`, 0 records, 0 candidates, 0 inspection
errors. Outputs are in `work-F-reconcile/`. One errno probe (Python
`os.stat`/`os.lstat`/`open` over a tree created and removed under
`work-F-reconcile/errno-probe`, uid 501) established which system errors the
registry-path states produce; its table is in Subject 2. No build, test,
install or removal was run. Every "holds at HEAD" below is a source reading
unless it says otherwise.

**Evidence classes used in the tables.**

- `XC`: executed by the review as a constructed control (build 1482, child-only
  `HOME` and `PW_RUNNER_REGISTRY`, labels never bootstrapped). Raw output gone.
- `XL`: the review's single read-only run against the real registry.
- `XR`: the retained live development run (build 1469). Pruned.
- `SR`: source or document read by the review. `H`: `git log` history.
- `Now`: re-read at HEAD for this pass. Not executed.

**Standing commitments the dispositions respect.**
`controller/AGENTS.md:45-50`: "Require observed absence to retire cleanup;
unknown inspection is not absence, and a label prefix does not authorize
removal. Keep reconcile report-only". Root `AGENTS.md` "External runner
workflow": inspect `runner list` and `runner reconcile` first; "A label prefix
alone never establishes cleanup ownership." `docs/PolicyWitness.md` is frozen;
nothing below edits it.

---

## Subject 1 — DT-69–73, DT-75–80: reconcile recovery, classification, candidate discovery and credited coverage

### 1.1 Claims

Columns: id | claim | boundary | holds at HEAD? | evidence | classification.
"Boundary" abbreviations: *CR* = constructed registry and fixture `HOME`
supplied to the child, `runner_reconcile` envelope on stdout, observed by the
review's driver, one run; *SRC* = producer source, read; *DOC* = authored
statement, read.

**Reproduction conventions (unnumbered)**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| RC.a | Source read at `87422530`; execution used the signed app in place (build 1482 at `8b5de2b2`); correspondence is by empty `git diff`, not a new build; no registered case ran and nothing was installed or removed. | Identity statement | Partly. Source correspondence holds through HEAD. The binary is no longer at `dist/`. | Now (git diff, `shasum`) | Accurate observation needing no change |
| RC.b | One constructed run over nine recorded states and five unrecorded files exited 0 with `ok`; the row table, candidates, six inspection errors; registry hash, absence of a lock and an lstat inventory were identical before and after. | CR | Yes by source: each reported row follows from `runner_commands.rs:756-865` and `runner_manager.rs:1278-1429` (walked state by state). Output not replayable. | XC (gone); Now | Accurate observation needing no change |
| RC.c | With exec of `/bin/launchctl` or `/usr/bin/id` denied by `sandbox-exec`, reconcile still exited 0 with `ok` and left the registry unchanged; these are constructed environmental failures. | CR under `sandbox-exec` | Yes by source: `inspect_service` maps a spawn error to `unknown` (`runner_manager.rs:1270-1274`); `launchctl_target` returns the `id -u` error (`:1173-1178`, `:1155-1161`). | XC (gone); Now | Accurate observation needing no change |
| RC.d | A read-only live run with an empty real registry returned 0 records, 0 candidates, 0 inspection errors and changed no registry or lock metadata. | Real registry, one run | Consistent with this pass's orientation run on build 1519 (same counts). Metadata comparison not repeated. | XL; orientation run | Accurate observation needing no change |
| RC.e | The retained run passed `runner_byoxpc/registry_recovery` and `runner_install` on build 1469 and is pruneable development evidence. | Live launchd, retained artifacts | The run is gone. The case source it exercised is unchanged. | XR (gone) | Accurate observation needing no change |

**DT-69**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 69.a | The `runner_remove_teardown_wait` effect says "a later `runner remove` or `runner reconcile` continues recovery", while the README and the reconcile rule say reconcile changes nothing. | DOC | Yes. `docs/limits.json:1441`, rendered at `docs/LIMITS.md:145`; against `controller/README.md:340-345`, `50-installation.surface.md:172`, `:220`. | SR; Now | Inaccurate mechanism account (the limits row) |
| 69.b | A `pending_cleanup` record whose service and plist are both observed absent is reported and left in place; registry bytes unchanged. | CR | Yes by source: `cmd_runner_reconcile` (`runner_commands.rs:751-870`) has no lock, save, bootout or unlink. | XC (gone); Now | Accurate observation needing no change |
| 69.c | In the retained live run, after `remove --skip-bootout` the row was `pending_cleanup` with service `present`/`owned` and plist `absent`/`ambiguous`; the following `runner remove`, not reconcile, retired it. | Live launchd | Test source unchanged: `registry_recovery.py:446-466`. Artifact gone. | XR (gone); Now | Accurate observation needing no change |
| 69.d | Reconcile's calls are the loader, location check, two inspectors, two classifiers, `read_dir` and the envelope; its children are `launchctl print`, `id -u` and `plutil` fed on stdin. | SRC | Yes. `runner_commands.rs:751-870`; `runner_manager.rs:784-805`, `:1155-1161`, `:1259-1276`. | SR; Now | Accurate observation needing no change |
| 69.e | Reconcile has been report-only since `92891a50`; the wording entered with `cefed899` and is in `v0.3.0`–`v0.3.7`. | H | Commits confirmed by `git log -S`. Tag contents not re-read. | H; Now | Accurate observation needing no change |
| 69.f | DT-34's third bullet recorded the contradiction from source; this entry adds the executed state. | Cross-reference | Yes. | — | Accurate observation needing no change |

**DT-70**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 70.a | `ambiguous` ownership is reported for an absent service, an absent plist and a listed service with zero or several `program = ` lines; `presence` must be read with it. | SRC; CR for absence | Yes. `runner_manager.rs:1384-1386`, `:1422`, `:1426`, `:1236-1245`. The mapping is authored at `50-installation.surface.md:207`, `:777-800`; the field text at `:946` and `controller/README.md:341` list the four words only. | XC (absence); SR; Now | Consequential ambiguity (field-level text) |
| 70.b | No ownership value marks the both-absent state that `cleanup_complete` requires. | SRC | Yes. `runner_manager.rs:1431-1433`; reconcile computes no such value. | SR; Now | Accurate observation needing no change |
| 70.c | Qualification: the present-without-program branch is source-read plus a unit test with an empty synthetic stdout; no native output of that shape was observed. | Constructed text | Yes. `runner_manager.rs:2518-2524`. Several `program` lines are not exercised by any test. | SR; Now | Accurate observation needing no change |
| 70.d | The mappings date to `92891a50`, the statements to `f6551bf9`. | H | Not re-derived. | H | Accurate observation needing no change |

**DT-71**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 71.a | The guide says list and reconcile "confirm retirement and service/plist absence", but reconcile looks up a service only for a record whose location resolved and for a candidate whose label parsed, and never enumerates launchd services. | DOC (frozen guide `:3206-3208`, `:3005`); SRC | Yes. `runner_commands.rs:775-781`, `:856-860`, `:791-846`. No technical owner makes the guide's claim. | SR; Now | Unsupported inference (in the frozen guide) |
| 71.b | The empty-registry live report holds no service observation and is identical for a retired service whose plist is gone and for one never installed. | Real registry | Yes by source and by the orientation run's shape. | XL; Now | Accurate observation needing no change |
| 71.c | Qualification: a loaded service with neither record nor plist was not constructed; its omission is established by source only. | SRC | Yes; still unexecuted. | SR | Accurate observation needing no change |
| 71.d | The guide-workflow case checks the post-removal reconcile envelope for `kind` and build contract only and establishes absence with its own `launchctl print` and `lexists`. | Test source | Yes. `guide_workflows.py:356-362`, `:583-585`. | SR; Now | Accurate observation needing no change |
| 71.e | The guide sentence is from `897be512`; discovery has been plist-only since `92891a50`. | H | Not re-derived. | H | Accurate observation needing no change |

**DT-72**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 72.a | Candidate suppression compares the parsed `Label` and directory scope with recorded `service_name` and `scope`, never the path; a plist with no readable label is a candidate by filename prefix and matches no record. | SRC | Yes. `runner_commands.rs:837-854`. | SR; Now | Accurate observation needing no change |
| 72.b | Four recorded plist paths were also reported as `unregistered` candidates (`unreadable`, `unconvertible`, `symlink` as `unknown`; `foreignlabel` as `unowned` with the foreign label). | CR | Yes by source. | XC (gone); Now | Consequential ambiguity (what "unregistered" covers) |
| 72.c | The retained live run shows the same for a real installation whose plist label was changed. | Live launchd | Fixture source unchanged: `registry_recovery.py:288-301`. Artifact gone. | XR (gone) | Consequential ambiguity |
| 72.d | The case that produced that report asserts the record row only and does not read `candidates`. | Test source | Yes. `registry_recovery.py:299-301`. | SR; Now | Accurate observation needing no change |
| 72.e | Suppression dates to `92891a50`, the README wording to `625c9051`, the rule to `f6551bf9`. | H | Not re-derived. | H | Accurate observation needing no change |

**DT-73**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 73.a | An unrecorded plist file carrying a registered label appears in no row, candidate or inspection error. | CR | Yes by source: suppressed at `runner_commands.rs:848-855`; the record row inspects only its own path (`:775-778`); no error because the file parsed. | XC (gone); Now | Consequential ambiguity (unstated consequence of the stated rule) |
| 73.b | Present, readable plists at the `uidmismatch` and `symlinkparent` recorded paths are suppressed as candidates while their rows hold only placeholders. | CR | Yes by source: `:784-787` with `:848-855`. | XC (gone); Now | Consequential ambiguity |
| 73.c | Qualification: launchd's handling of two plists with one label was not examined; a loaded extra plist would make the record row's service `unowned` (source-read). | SRC | Yes. `runner_manager.rs:1419-1429`. Still unexamined. | SR | Accurate observation needing no change |
| 73.d | Since `92891a50`. | H | Not re-derived. | H | Accurate observation needing no change |

**DT-75**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 75.a | A recorded uid or domain that differs from the current user, a recorded path under a symlinked ancestor, and a failed `id -u` all produce the same row: `ownership: "unknown"`, `service` and `plist` each `{"presence":"unknown"}`, no observation. | CR; CR under `sandbox-exec` | Yes. `runner_manager.rs:1322-1378`; `runner_commands.rs:784-787`. The field text states the placeholder (`surface:911`, `:919`, `:964`, `:973`). | XC (gone); Now | Consequential ambiguity |
| 75.b | Denying `/bin/launchctl` kept every plist observation and put the error inside the service observation. | CR under `sandbox-exec` | Yes. `runner_manager.rs:1270-1274`, `:1421`. | XC (gone); Now | Accurate observation needing no change |
| 75.c | `unknown` therefore has three sources; only the free-text row `error` separates an identity contradiction from an environmental failure, and a contradiction is not reported as `unowned`. | Output reading | Yes. | XC; Now | Consequential ambiguity |
| 75.d | `launchctl_target` (which runs `id -u`) precedes the ownership comparison, the uid comparison and the ancestor check. | SRC | Yes. `runner_manager.rs:1331`, `:1334`, `:1339-1358`, `:1360-1370`. | SR; Now | Accurate observation needing no change |
| 75.e | With `id` denied, candidate `service` values became null. | CR under `sandbox-exec` | Yes; this is the authored meaning (`surface:1034`; `runner_commands.rs:856-860`). | XC (gone); Now | Accurate observation needing no change |
| 75.f | No reconcile assertion covers a location-error row. | Test source | Yes. None in `registry_recovery.py`, the unit tests or the integration crate. The dynamic-record owner already says an output control for every branch "remains open" (`surface:1191`). | SR; Now | Accurate observation needing no change |
| 75.g | Checks and placeholder date to `92891a50`, field statements to `f6551bf9`. | H | Not re-derived. | H | Accurate observation needing no change |

**DT-76**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 76.a | A symlink at a recorded path is `present`, `regular: false`, `plist_ownership: "unowned"`; the same object as a candidate is `unknown`. The statement names neither result. | CR | Yes. `runner_manager.rs:1302-1305`, `:1387-1389`; `runner_commands.rs:863`. Statement: `surface:202`, `:207`. | XC (gone); Now | Inaccurate mechanism account (an unstated branch) |
| 76.b | A regular file that `plutil` cannot convert is `present` with a hash, `config: null` and `plist_ownership: "unknown"`; the statement gives `unknown` ownership only for unknown presence. | CR | Yes. `runner_manager.rs:1306-1312`, `:1390-1392`. | XC (gone); Now | Inaccurate mechanism account (an unstated branch) |
| 76.c | A plist matching in every respect except `XPC_SERVICE_PATH` is `unowned`, as stated; installation's `--env` handling and removal were not exercised. | CR | Yes. `runner_manager.rs:1402-1408`. | XC (gone); Now | Accurate observation needing no change |
| 76.d | A mode-000 plist is `unknown` presence with `regular: true` and an owner uid from metadata, matching the presence definition. | CR | Yes. `runner_manager.rs:1296-1300`, `:1314-1317`; `surface:818`. | XC (gone); Now | Accurate observation needing no change |
| 76.e | DT-34's second bullet recorded 76.a and 76.b from source only. | Cross-reference | Yes. | — | Accurate observation needing no change |

**DT-77**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 77.a | Every inspection error carries `presence: "unknown"`, including for files whose plist observation in the same report says `present`. | CR | Yes. The value is a literal at `runner_commands.rs:827`. `surface:1074` states the constant; `surface:818` defines plist presence differently. | XC (gone); Now | Consequential ambiguity |
| 77.b | A valid property list holding a `<data>` value is reported as an inspection error (`plutil` cannot emit it as JSON) and is not a candidate. | CR; separate `plutil` run | Yes by source: the error is appended before the candidate filter (`runner_commands.rs:824-847`). The `plutil` behavior was not re-run. | XC (gone); Now | Consequential ambiguity (unstated scope) |
| 77.c | The other two errors are read failures, which the plist observation also reports as `unknown`. | CR | Yes. | XC (gone); Now | Accurate observation needing no change |
| 77.d | An inspection error is appended for every `*.plist` in both directories whose observation carries an error. | SRC | Yes. `runner_commands.rs:821-828`. | SR; Now | Accurate observation needing no change |
| 77.e | The only assertion on an inspection error is for a mode-000 candidate. | Test source | Yes. `registry_recovery.py:337-340`. | SR; Now | Accurate observation needing no change |
| 77.f | Since `92891a50`. | H | Not re-derived. | H | Accurate observation needing no change |

**DT-78**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 78.a | The reconcile node says it "reports launchd services and plists that look owned, changing nothing"; reconcile reports every record regardless of ownership, and no candidate is ever `owned`. | DOC; SRC | Yes. `docs/architecture.json:6791` (rendered `docs/ARCHITECTURE.md:1127`); `runner_commands.rs:756-790`, `:863`. | SR; Now | Inaccurate mechanism account |
| 78.b | Edge X24 says "inspect_service lists candidate services"; `inspect_service` prints one supplied label. | DOC; SRC | Yes. `architecture.json:7463`; `runner_manager.rs:1259-1276`. | SR; Now | Inaccurate mechanism account |
| 78.c | Edge X25 says "inspect_plist lists candidate plists". | DOC; SRC | Yes. `architecture.json:7484`. `inspect_plist` reads one path (`runner_manager.rs:1278-1320`); the listing is `read_dir` in `cmd_runner_reconcile` (`runner_commands.rs:800`). | SR; Now | Inaccurate mechanism account |
| 78.d | All three cite `runner_install`, which reaches reconcile once, on an absent per-session registry, and asserts exit 0 and `result.ok` only. | Test source | Yes. `tests/fixtures/byoxpc/session.py:28-32`, `:229`, `:234`; `tests/fixtures/caller_auth/bundle.py:44`. | SR; Now | Overstated coverage credit |
| 78.e | Row and edges entered with `e2115cf3`. | H | Confirmed for the node text by `git log -S`; edges not re-derived. | H; Now | Accurate observation needing no change |

**DT-79**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 79.a | The subtree owner grades "Managing runners and its descendants" **check read**; none of its six cited checks calls `cmd_runner_reconcile`, `record_location`, `inspect_service`, `inspect_plist`, "or `load_registry` on an absent or inaccessible path". | DOC; test source | Partly. The grade and the reconcile gap hold (`surface:14-21`; `docs/RESPONSE.md:3769`). The `load_registry` clause is mistaken for the absent path: four of the six call it on a path not yet created (`runner_manager.rs:2358`, `:2370`, `:2437`, `:2803`), and `install_failure_boundaries_preserve_observed_pending_state` asserts empty `runners` from one (`:2469-2471`). None uses an inaccessible path. | SR; Now | Overstated coverage credit (reconcile); the absent-path clause is a review error |
| 79.b | The classifier unit tests are not cited for the reconcile or ownership rules. | DOC | Yes. `surface:209-216` and `:801-807` are `source_read` with no `check`. | SR; Now | Accurate observation needing no change |
| 79.c | The executed reconcile assertions are five groups in the opt-in `registry_recovery.py`. | Test source | Yes. `:299-301`, `:317-321`, `:335-340`, `:429-436`, `:450-453`. | SR; Now | Accurate observation needing no change |
| 79.d | Every no-change comparison covers reconcile together with other commands. | Test source | Yes. `:317-321` (list, status, reconcile, verify); `:411-436` (run, verify, list, status, reconcile). | SR; Now | Accurate observation needing no change |
| 79.e | "Reconcile creates no registry or lock" (`controller/README.md:344`) has no assertion. | DOC; test source | Yes. In `registry_recovery.py` the directory and lock already exist; `session.py:234` asserts nothing after `reconcile-before`. | SR; Now | Overstated coverage credit (an unasserted claim under a check-read subtree) |
| 79.f | The constructed control executed that claim but is not a registered case; the retained run passed both cases. | CR; live | Neither artifact remains. | XC, XR (gone) | Accurate observation needing no change |

**DT-80**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 80.a | A pending-cleanup row carries only the nested runner; `cleanup_started_at_unix_ms` and `observations` are not in reconcile output, while the `records` field says "retained cleanup entries". | CR | Yes. `runner_commands.rs:768-773`; `surface:863`. `runner list` prints them (`:455-460`). | XC (gone); Now | Consequential ambiguity |
| 80.b | Recognition needs a `com.policywitness.` label, a `PWRunner` executable name or that filename prefix; installation accepts any bundle identifier and executable name, so a lost record for a differently named service is not recognizable. | SRC | Yes. `runner_commands.rs:837-844`, `:251-255`, `:273-282`. | SR; Now | Accurate observation needing no change (limit unstated) |
| 80.c | The registry is read once without a lock before the per-row reads; only the envelope carries a time. | SRC | Yes. `runner_commands.rs:752`; `json_contract.rs` envelope. Not exercised. | SR; Now | Accurate observation needing no change (limit unstated) |
| 80.d | The three child processes have no time bound, and LIMITS has no reconcile entry. | SRC; DOC | Yes. `runner_manager.rs:1260-1263`, `:1156-1161`, `:785-799`. Not exercised. | SR; Now | Accurate observation needing no change (limit unstated) |

**Coverage and limits (unnumbered)**

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| RL.a | The trace covered dispatch through envelope and exit status; reconcile writes nothing. | SRC | Yes. | SR; Now | Accurate observation needing no change |
| RL.b | The executed evidence is one fixture run, two denial runs, four registry-path variants, one live run and the retained run. | Evidence inventory | The inventory is accurate as history; none of it is present now. | — | Accurate observation needing no change |
| RL.c | Present-service evidence comes only from retained artifacts 279 and 294. | Live launchd | Those artifacts are gone. The assertions that produced them are at `registry_recovery.py:429-433`, `:450-452`. | XR (gone) | Accurate observation needing no change |
| RL.d | Not executed: present-without-program, system scope, legacy records without ownership, unset `HOME`, a broken stdout, concurrent modification, duplicate labels in launchd, and the consequences of an inaccessible registry for list, status, verify and remove. | Scope statement | Still unexecuted. Subject 2 reads the last item from source. | — | Accurate observation needing no change |
| RL.e | History shows when mechanisms and statements appeared, not how older binaries behaved. | Scope statement | Yes. | — | Accurate observation needing no change |

### 1.2 Comparison

**Obligations as stated.**

- `controller/README.md:340-345` (owner: the README): "Reconcile is
  report-only: recorded state, observed service/plist presence and ownership
  (`owned`, `unowned`, `ambiguous`, `unknown`). It also scans user LaunchAgents
  and readable system LaunchDaemons for unrecorded `com.policywitness.*` labels
  or `PWRunner` executables. These are reporting candidates, not cleanup
  authorization. Reconcile creates no registry or lock and makes no machine
  changes."
- `docs/contract/50-installation.surface.md:171-176` (owner: the installation
  surface; rendered into `docs/RESPONSE.md`): condition "The registry loaded
  successfully."; effect "Report each active and cleanup record with current
  service/plist observations and separate ownership classifications, and report
  recognizable unregistered plist candidates plus inspection errors. Leave
  installation resources and registry records as observed."; prose "Registered
  label/scope pairs are suppressed from candidates. Discovery establishes a
  candidate for inspection; cleanup authority requires the recorded identity
  and the independent ownership gates."
- `surface:207`: "Absent resources are classified ambiguous for ownership and
  retain their independently observed absent presence. Unknown presence
  produces unknown ownership."
- `surface:847`: "The result reports successful reconciliation execution even
  when individual inspections remain unknown."
- `docs/limits.json:1441` (owner: the limits manifest; rendered into
  `docs/LIMITS.md:145`): "a later `runner remove` or `runner reconcile`
  continues recovery."
- `docs/architecture.json:6791`, `:7463`, `:7484` (owner: the architecture
  manifest): the three texts in 78.a–c, each with the check citation
  `runner_install`.
- `surface:14-21`: subtree support graded `check_read`, with pins naming
  "pending saves at failure boundaries, opaque metadata round trips, safe
  registry replacement and bounded post-bootout observation".

**What the producer does (observation, by source at HEAD).**
`cmd_runner_reconcile` loads the registry without a lock, builds one row per
`runners` entry and per `pending_cleanup[].runner`, and for each row either
resolves a location and attaches two observations and two classifications or
attaches placeholders and an error text. It then lists two directories,
inspects every `*.plist`, records an inspection error for each observation
that carries an error, keeps as candidates those recognized by label prefix,
executable name or filename prefix, drops candidates whose parsed label and
scope match a record, and prints one envelope with `ok` and exit 0. It calls
no function that writes, locks, boots out or unlinks.

**What readers and tests assert (observation).**

| Reader | What it asserts about reconcile |
| --- | --- |
| `session.install` (`session.py:234`), reached by `runner_byoxpc/runner_install` and every session-based opt-in | Exit 0 and `result.ok is True`, on a registry path that does not exist yet. Data unread. |
| `registry_recovery.py:299-301` | A pending-cleanup row with a foreign-label plist has `plist_ownership: "unowned"`. |
| `:317-321` | With the lock held by the test, list, status and reconcile exit 0; registry and plist bytes equal their prior values after those and a `verify`. |
| `:335-340` | An unrecorded `com.policywitness.` plist is an `unowned` candidate; made mode 000, it yields an inspection error with `presence: "unknown"`. |
| `:429-436` | A constructed legacy record on a live installation is `installed`, service and plist `present` and `owned`; a snapshot of bundle, registry directory, LaunchAgents directory and plist is equal before and after refused `run` and `verify`, list, status and reconcile. |
| `:450-453` | After `--skip-bootout`, the row is `pending_cleanup` with service `present` and plist `absent`. |
| `guide_workflows.py:498`, `:583` | `kind` and build contract of the saved envelope. |
| Unit: `service_absence_requires_specific_observation_not_any_nonzero_exit` (`runner_manager.rs:2488-2525`) | `classify_service_output` and `service_ownership` over constructed text: unknown, absent, owned, unowned, and `ambiguous` for an empty successful output. |
| Unit: `plist_and_service_evidence_independently_gate_cleanup_retirement` (`:2527-2567`) | `plist_ownership` is `owned` for a matching constructed observation and `unowned` after a hash change; `cleanup_complete` needs both absent. |

**Inference kept apart from observation.**

- That the limits row is the inaccurate one (rather than reconcile being
  defective) is a judgment: two authored statements and the standing rule in
  `controller/AGENTS.md` say report-only, and the row's own checks exercise
  only `remove_record`.
- That a second plist with a registered label could become the loaded job is
  not observed. The review did not examine launchd's choice between two files.
- That the review's rows would reproduce on build 1519 is inferred from
  identical source, not executed.

### 1.3 Plausible treatments

**T1 — Correct the limits row (DT-69).** Edit `docs/limits.json`, row
`runner_remove_teardown_wait`: remove "or `runner reconcile`" from `effect`;
add the check citation `removal_preserves_recovery_across_faults_and_repeated_cleanup`
(`controller/src/runner_manager.rs`, kind `path`, form `test`) and one clause
to `behavior` saying a repeated removal retires a retained record once absence
is observed. Regenerate with `tests/lib/python.sh docs/generate_limits.py`
(writes `docs/LIMITS.md`; the development mode leaves the guide's bytes
unchanged). Not a build-contract input. The correction removes a false clause
from a shared region and adds no workflow; the citation and `behavior` clause
land in the coverage table (`docs/LIMITS.md:310-430`), which is outside the
shared region. Consequence: `docs/LIMITS.md` and the guide's frozen copy of
that row differ. A check must reject a limits row that credits reconcile with
recovery; none exists and none is proposed, because the generator checks text
freshness, not meaning.

**T2 — Make reconcile continue recovery (DT-69, alternative).** A product
change under `controller/src` (signed rebuild) that would retire or act on
cleanup records from reconcile. It contradicts `controller/AGENTS.md` ("Keep
reconcile report-only"), `README:340-345` and `surface:172`. Not a real
candidate; listed because the limits wording has been published since
`v0.3.0`.

**T3 — State reconcile's classification and discovery limits in the surface
(DT-70, 71, 72, 73, 75, 76, 77, 80).** Edit prose in
`docs/contract/50-installation.surface.md` only: the candidate paragraph
(`:176`), the ownership prose (`:207`), the reconciliation intro (`:847`) and
the field texts at `:863`, `:879`, `:911`, `:919`, `:946`, `:955`, `:973`,
`:1050`, `:1074`. Regenerate with
`tests/lib/python.sh docs/generate_contract_stamps.py` (writes
`docs/RESPONSE.md`, `docs/CONTRACT.md`, `docs/contract/public.json`). Not a
build-contract input. No `free.*` key is added, so `free_text.json` counts do
not rise. Public payload text changes, so the installation surface's stamp in
`docs/CONTRACT.md` changes while the guide's stamp table stays frozen.
Consequence for users: none in behavior; the statements stop permitting the
inferences listed in 1.5.

**T4 — Change reconcile's candidate rule so each scanned plist is reported
exactly once (DT-72, 73, alternative).** Suppress a scanned plist only when a
record row in the same report observed that path. This removes the double
report and the unreported file, but a plist with a registered label at another
path would then be a candidate labelled `recorded_state: "unregistered"` and
`ownership: "unowned"`, which misdescribes it; an honest form needs a new
candidate value or field, a shape-golden refresh
(`tests/fixtures/contract/surfaces/installation.json`), new assertions and a
signed rebuild. A narrower variant (drop a candidate whose path equals a
resolved recorded path) removes only the double report and loses the service
lookup for a foreign label.

**T5 — Type the location error or copy observed presence into inspection
errors (DT-75, 77, alternative).** Small edits at `runner_commands.rs:784-787`
and `:827` plus `record_location`'s error type. Both change public values
(`presence` in inspection errors from `unknown` to `present` for present
files; a new row field), need shape and prose updates and a signed rebuild.
`remove_record` shares `record_location` and pushes its text as a warning.

**T6 — Correct the architecture rows and their credited check (DT-78).** Edit
`docs/architecture.json`: node `reconcile` `facts.Behavior`; edge X24 and X25
`label`; replace the `runner_install` citation on all three with
`tests/suites/runner_byoxpc/opt_in/registry_recovery.sh` / `registry_recovery`
(form `test`), and add the integration control from T8 once it exists.
Regenerate with `tests/lib/python.sh docs/generate_architecture.py`
(Graphviz `dot` is at `/opt/homebrew/bin/dot`; it rewrites
`docs/architecture-byoxpc.dot`, its SVG and the `docs/ARCHITECTURE.md`
regions), then run the contract generator. Not a build-contract input.

**T7 — Scope the support statements (DT-79, 70.c, 75.f).** In the surface: add
to the subtree owner's `limits` (`:21`) that its cited controls exercise
neither reconcile, record location, service or plist inspection nor a registry
load refusal; add an owner under "Reconcile observations" graded `check_read`
that cites `registry_recovery` and states what it asserts and does not; add
the two classifier unit tests as `check` on the owners at `:209-216` and
`:801-807` with their constructed-input limits. Regenerate as in T3.

**T8 — Add the missing assertions (DT-79.d, 79.e, 69.b, 76.a, 76.b, 70.c).**

- An integration control in `controller/integration/cli_contract.rs` (runs in
  `integration/cli.integration`, default battery, signed app in place,
  `HOME` and `PW_RUNNER_REGISTRY` pointed into scratch as
  `help_needs_no_app_home_registry_or_valid_tail` does at `:1922-1932`):
  reconcile on an absent registry path leaves the path, its `.lock` sibling and
  its parent directory absent; reconcile on a constructed registry holding one
  installed record and one `pending_cleanup` record (plist path under the
  fixture `LaunchAgents`, label never bootstrapped) exits 0, reports both
  `recorded_state` values, and leaves the registry bytes and the directory
  listing identical with no lock created. `controller/integration` is not a
  build-contract input. The control must reject a reconcile that creates a
  lock or directory, rewrites the registry, or retires a record whose
  resources are absent. It does not assert presence values, which depend on
  whether a GUI launchd domain is reachable. The scratch path must be
  canonicalized before it is written into the fixture record and `HOME`:
  `env::temp_dir()` is under `/var`, a symlink, and `record_location` refuses
  a recorded plist path with a symlinked ancestor
  (`runner_manager.rs:1360-1370`), which would turn every row into a
  location-error placeholder.
- A unit control in `controller/src/runner_manager.rs` over constructed
  observations: `plist_ownership` is `unowned` for a non-regular object,
  `unknown` for a regular file with no converted configuration, `ambiguous`
  when absent, `unknown` when presence is unknown and `unowned` when
  `XPC_SERVICE_PATH` differs; `service_ownership` is `ambiguous` for two
  `program = ` lines. It must reject `owned` for any of the first five, which
  is the value that authorizes unlinking in `remove_record`
  (`runner_manager.rs:1594-1598`). This edit is under `controller/src`: it
  changes the build contract and forces a signed rebuild.

**T9 — Retain.** For every claim marked "accurate observation needing no
change", and for the behavior behind DT-70 through DT-77 and DT-80 once T3
states the limit.

### 1.4 Recommended disposition per claim

| Claims | Disposition | Reason | Discriminating check, or why none |
| --- | --- | --- | --- |
| RC.a–RC.e, RL.a–RL.e | Reasoned retention as a record of how the observations were made. | They describe evidence, not product behavior. Their one consequence is that no executed output can be reused; every disposition here rests on unchanged source. | None needed. If an executed row is wanted, the fixture table at review lines 2603–2620 is sufficient to rebuild the driver. |
| 69.a | T1: correct the account in `docs/limits.json`. Reconcile stays report-only. | Reconcile's report-only form is a standing commitment and is what three other statements say. The published row may have created reliance, but implementing it would withdraw that commitment. | The revised clause "a later `runner remove` continues recovery" is asserted by `removal_preserves_recovery_across_faults_and_repeated_cleanup` (`runner_manager.rs:2754-2770`), which T1 cites, and live by `registry_recovery.py:458-465`. The retention half is `bootout_waits_out_launchd_teardown_within_the_budget` (`:2831-2853`). The retry in the unit test follows other retention causes, not budget expiry; `remove_record` has no branch on the cause of an earlier retention (`:1551-1558`), so a budget-specific retry would not change the decision. |
| 69.b | Retain the behavior; add the T8 integration control. | Leaving a cleanup-complete record in place is what report-only means. | T8, second half. |
| 69.c, 69.d, 69.e, 69.f | Retain; no change. | Accurate. 69.f: the limits correction is the same edit DT-34's third bullet needs; make it once. | — |
| 70.a | T3: one sentence at the `service_ownership` and `plist_ownership` fields. Behavior retained. Accepted limit, to stand at `surface:946`: "`ambiguous` is assigned to an absent service and to a listed service without exactly one `program` line; read it with `service.presence`." | The mapping is already authored at `:207` and `:777-800`; only the field-level text omits it. A new value for absence would also change the durable cleanup observations that share the classifier (`runner_manager.rs:1575-1580`). | Existing unit test `service_absence_requires_specific_observation_not_any_nonzero_exit` for the service mapping; T8 adds the two-line case and the absent plist. |
| 70.b | Retain. Accepted limit, same field: "Reconcile reports no retirement decision; `runner remove` decides retirement from its own observations." | Reconcile makes no retirement claim, and adding one would be an interpretation beyond its two observations. | `plist_and_service_evidence_independently_gate_cleanup_retirement` covers `cleanup_complete`. |
| 70.c | T7: carry the qualification into the classify owner's `limits`. | It is a limit of the support, not of the product. | T8 adds the several-lines case; native output of that shape remains unobserved and is stated as such. |
| 70.d, 71.e, 72.e, 73.d, 75.g, 77.f, 78.e | Retain; no change. | History notes. | — |
| 71.a | T3: retention with a stated limit. To stand in the candidate paragraph at `surface:176`: "Reconcile looks up a launchd service only for a record whose location resolved and for a candidate whose Label parsed. It does not enumerate launchd services, so a report with no row for a service is not an observation that the service is absent." No edit to the guide. | No technical owner makes the guide's claim, the guide is frozen, and enumerating launchd services would add a new parser of `launchctl` domain output to a report-only command. Absence after removal is already established by `runner remove`: `cleanup_retained: false` requires both resources observed absent, no warnings and a saved registry (`runner_manager.rs:1617`, `:1629-1637`, `:1644`). | None needed: the omission follows from the absence of any launchd enumeration in `runner_commands.rs:756-865`, and the guide-workflow case already establishes absence independently (71.d). |
| 71.b, 71.c, 71.d | Retain; no change. | Accurate; 71.d shows no coverage credit rests on reconcile for absence. | — |
| 72.a, 72.b, 72.c | T3: correct the account, retain the behavior. To stand at `surface:176` and at the `candidates` and candidate `recorded_state` fields (`:871`, `:988`): "Suppression compares the parsed Label and the scanned directory's scope only. A plist at a recorded path whose Label cannot be read, or differs from the recorded service name, is reported in its record row and again as a candidate. `unregistered` means that no record in that scope has the candidate's parsed Label." | Every authored sentence is literally true of the code; the defect is that "unregistered" reads as a statement about the file. T4 would need a new candidate vocabulary to stay truthful. The record row already reports the same path as `unowned` or `unknown`, and candidates carry no authority. | T8 integration control can add one assertion that the constructed foreign-label path appears in both places, so the stated overlap is exercised. Not required for the decision. |
| 72.d | Retain; T7 records in the reconcile owner's `limits` that no assertion reads `candidates` for an overlapping path. | Accurate coverage statement. | — |
| 73.a, 73.b | T3: retention with a stated limit, same paragraph: "Another plist file that carries a registered Label in the same scope is reported in neither place, and on a location error the plist at the recorded path is not inspected." | Same reason as DT-72. For 73.a the record row's service observation still reports a different executable as `unowned` when such a file is the loaded job. For 73.b the row's `error` and `runner.ownership.plist_path` name what was not inspected. | None proposed. What would change the decision: an observation that launchd loads the second file while the record row still reports `owned`. That is not possible by source, because `owned` requires the listed program to equal the recorded executable (`runner_manager.rs:1424`). |
| 73.c | Retain as an open qualification. | launchd's handling of duplicate labels is still unexamined; the disposition does not depend on it. | — |
| 75.a, 75.c | T3: retention with a stated limit. At `surface:911` and `:919`: "…otherwise only `{"presence":"unknown"}`: the resource was not inspected." At `:973`: "Location-check refusal text. It is the only field that distinguishes a recorded identity that disagrees with the current user, scope or paths from a location that could not be determined." | The row is truthful (nothing was inspected) and the field text already states the placeholder. Typing the error (T5) changes a function that removal shares, for a distinction the text already carries. | None proposed; the dynamic-record owner's stated limit at `surface:1191` already covers the missing output control (75.f). |
| 75.b, 75.d, 75.e, 75.f | Retain; no change. | Accurate; 75.e matches the authored field meaning. | — |
| 76.a, 76.b | T3: correct the account at `surface:207`: "A present object that is not a regular file is unowned. A regular file whose content could not be converted is unknown." At the candidate `ownership` field (`:1050`): "Assigned without reference to any record." Behavior retained. | The two branches exist and are safe (neither yields `owned`); the statement omits them. The record and candidate classifiers answer different questions, so their different words for a symlink are both correct once that is said. This is the same edit DT-34's second bullet needs; make it once. | T8 unit control. |
| 76.c, 76.d, 76.e | Retain; no change here. | 76.c and 76.d match their statements. The `--env XPC_SERVICE_PATH` consequence belongs to DT-34's first bullet. | — |
| 77.a | T3: retention with a stated limit at `surface:1074`: "The constant `unknown`, marking a failed inspection. It is not the file's observed presence; a record row or candidate for the same path carries that." | The constant is authored as a constant. T5 would make it an observation, at the cost of a public value change, for a field no reader uses to decide anything. | Existing `registry_recovery.py:340` asserts the constant for a read failure. |
| 77.b, 77.d | T3: stated limit at `surface:879`: "…for every `.plist` entry in the scanned directories, whether or not it is a candidate. A property list that cannot be represented as JSON is one such failure and is recognized as a candidate only by filename prefix." | Accurate and consequential for readers who treat every inspection error as concerning a runner. | None proposed; the `plutil` behavior is a system-tool property the review observed once. |
| 77.c, 77.e | Retain; no change. | Accurate. | — |
| 78.a, 78.b, 78.c | T6: correct the account in `docs/architecture.json`. Suggested texts: node, "reports each recorded runner and cleanup entry with its observed service and plist, and recognizable unrecorded plists, changing nothing"; X24, "launchctl print for each recorded service and each candidate label, without changes"; X25, "reads each recorded plist and each plist in the two launchd directories, without changes" (add `cmd_runner_reconcile` to X25's sources for the listing). | The three texts misstate the mechanism. | Citation checks establish only that the symbol exists; the review of support is 78.d. |
| 78.d | T6: replace the credited check. `registry_recovery` asserts row contents, a candidate, an inspection error and joint no-change; add the T8 integration control for "without changes" on its own. | `runner_install` asserts only that reconcile on an absent registry exits 0 with `ok`. | `runner_byoxpc/registry_recovery`; T8. |
| 79.a | T7. Record that the review's absent-path clause is mistaken. | The grade's scope is too wide for reconcile; the absent-registry result does have a read assertion. | Subject 2 adds the inaccessible-path control. |
| 79.b | T7: cite the two classifier tests on their owners, with constructed-input limits. | They are the only assertions on the classifiers. | The tests themselves. |
| 79.c, 79.d | T7: state in the new owner that the assertions are opt-in and that no-change comparisons are joint. Retain the joint form. | A joint comparison still rejects a change by any one of the commands; it cannot say reconcile alone was observed. | T8 integration control observes reconcile alone. |
| 79.e | T8 integration control (first half), then cite it. | The README sentence is otherwise unasserted. | T8. |
| 79.f | Retain; no change. | Evidence statement; both artifacts are gone. | — |
| 80.a | T3: correct the account at `surface:863`: "One row for each recorded runner and for the nested runner of each retained cleanup entry, with current observations or a location error. A cleanup entry's `cleanup_started_at_unix_ms` and `observations` are not repeated; `runner list` returns them." | The field set is accurate; the summary sentence is loose. Adding the history to reconcile would duplicate `runner list`. | None needed; the field list at `surface:881-973` already has no such member. |
| 80.b | T3: stated limit at `surface:176`: "Installation accepts any bundle identifier and executable name. An installed service with neither the label prefix nor the `PWRunner` executable name is not recognizable as a candidate without its record." | Accurate and consequential only after a record is lost. | None needed; by source at `runner_commands.rs:837-844`. |
| 80.c | T3: stated limit at `surface:847`: "The registry is read once, without the lock, before the per-row observations; a report is not a snapshot taken at one time." | Lock-free reading is already stated at `:39`; the per-row timing is not. | Not exercised; a concurrency control would not change the decision. |
| 80.d | T3: stated limit at `surface:847`: "Reconcile waits without a time bound for each `launchctl print`, `id` and `plutil` child." No LIMITS row. | LIMITS inventories what "a request encounters" (`docs/LIMITS.md:4-8`); the absence of a reconcile row is not a false statement there, and shared regions must not gain content. | None needed; by source. |

### 1.5 Resulting user duties

1. Do not expect `runner reconcile` to continue or finish a retained cleanup.
   Repeat `runner remove` until it reports `cleanup_retained: false` with no
   warnings. (DT-69. The guide's frozen copy of the limits row says otherwise.)
2. Do not conclude that a service is absent because a reconcile report has no
   row for it. The `runner remove` result or an independent
   `launchctl print` establishes absence. (DT-71.)
3. Read `presence` together with every ownership value; `ambiguous` does not
   say whether the resource exists. (DT-70.)
4. Before treating a candidate as unregistered, compare its `plist_path` with
   each record's `plist_path` and, on a location-error row, with
   `runner.ownership.plist_path`. Do not conclude that the scanned directories
   hold no other plist with a registered label. (DT-72, DT-73.)
5. On a row with `error`, read the text: the placeholders mean the resources
   were not inspected, and the text is the only statement of why. (DT-75.)
6. Do not read `presence` in an inspection error as the file's presence, and
   do not assume every inspection error concerns a runner. (DT-77.)
7. Use `runner list` for a cleanup entry's start time and stored observations.
   (DT-80.a.)
8. Keep the registry record for a service whose bundle identifier or
   executable name does not follow the defaults; reconcile cannot rediscover
   it. (DT-80.b.)
9. Do not treat a reconcile report as one consistent snapshot while an
   install or remove may be running, and impose your own time limit if one is
   needed. (DT-80.c, DT-80.d.)

Duties 3, 5, 6 and 7 restate authored field meanings and may belong in working
guidance rather than the user-responsibility outflow.

### 1.6 Implementation worklist

All of group A is true of the product at HEAD and touches no build-contract
input. Group B's unit edit is under `controller/src` and should ride the
Subject 2 rebuild.

**Group A — accounts and support (no rebuild).**

1. `docs/limits.json`, row `runner_remove_teardown_wait` (`:1435-1463`):
   `effect`, `checks`, `behavior` as in T1.
2. `docs/architecture.json`: node `reconcile` (`:6787-6812`), edges X24
   (`:7459-7478`) and X25 (`:7480-7499`) as in T6.
3. `docs/contract/50-installation.surface.md`: prose and field texts as in the
   1.4 table (`:176`, `:207`, `:847`, `:863`, `:871`, `:879`, `:911`, `:919`,
   `:946`, `:955`, `:973`, `:988`, `:1050`, `:1074`); owner `limits` at `:21`;
   a new owner under `:163`; `check` and `limits` on the owners at `:209-216`
   and `:801-807` (T7).
4. Regenerate in this order: `tests/lib/python.sh docs/generate_limits.py`;
   `tests/lib/python.sh docs/generate_architecture.py`;
   `tests/lib/python.sh docs/generate_contract_stamps.py`. Then run each with
   `--check`. Review the `docs/RESPONSE.md`, `docs/CONTRACT.md` and
   `docs/contract/public.json` diffs as a public text change to one surface.
5. `controller/integration/cli_contract.rs`: the T8 integration control. Run it
   against the existing app first; it is expected to pass there, since it
   asserts current behavior. Add a line to
   `tests/suites/integration/README.md` under Invariants.
6. Cite the new control from the reconcile owner (surface) and from the three
   architecture entries; regenerate again.
7. Verification: `PW_TEST_OUT_DIR=tests/out/runs/<name> tests/run.sh --suite
   source_drift --suite unit --suite integration` (`unit` because
   `documented_removal_limits` compiles `docs/limits.json` in). Routes:
   `tests/CHANGE-VERIFICATION.md` "Find verification for a change", rows for
   limits and for "BYOXPC selection, installation, registry or cleanup";
   `controller/AGENTS.md` "Documentation or generated contracts" and "Public
   CLI arguments and envelope behavior".

**Group B — classifier unit control (rebuild).**

8. `controller/src/runner_manager.rs`, test module: the T8 unit control. This
   edit changes the build contract and forces a signed rebuild before any
   app-bound case. Cite it from the owners at `surface:209-216` and
   `:801-807`, replacing the constructed-input limits it removes; regenerate
   the contract.
9. Verification: `unit/rust.unit`, `unit/rust.fmt`, `source_drift`; after the
   rebuild, the group's default battery under the plan's signed-app
   checkpoint rule.

---

## Subject 2 — DT-74: absent registry versus failed inspection

### 2.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| 74.a | `load_registry` returns the empty registry whenever `path.exists()` is false, which includes permission denial on an ancestor and a dangling symlink; only an existing file that cannot be read reaches the failing read. | SRC | Yes. `runner_manager.rs:540-550`. | SR; Now; errno probe | Contradicted explicit commitment (see 2.2) |
| 74.b | With the registry under a mode-000 parent, reconcile exits 0 with `ok`, `records: []`, 12 candidates and 6 inspection errors. | CR, registry-path variant | Yes by source: `lstat`/`stat` give `EACCES`, `exists()` is false. | XC (gone); Now; errno probe | Contradicted explicit commitment |
| 74.c | With the registry path a symlink to a missing file, the same. | CR | Yes by source: `stat` gives `ENOENT`, `lstat` succeeds. | XC (gone); Now; errno probe | Consequential ambiguity ("its path is absent") |
| 74.d | With the parent directory absent, the same output, and the directory is still absent afterward. | CR | Yes. This is the stated absent case; reconcile takes no lock (`runner_commands.rs:104-108`). | XC (gone); Now | Accurate observation needing no change |
| 74.e | With the registry file mode 000, exit 2, no stdout, stderr `failed to read …: Permission denied (os error 13)`. | CR | Yes. `runner_manager.rs:549-550`; `cli.rs:63-69`. | XC (gone); Now | Accurate observation needing no change (the form is DT-35's subject) |
| 74.f | The three exit-0 outputs are identical apart from `registry_path`; "In the first two cases, the unreadable registry held seven runners and two cleanup entries"; every recorded plist became an `unregistered` candidate; nothing says the registry could not be read; the guide's steps for unregistered candidates would then apply to installations the registry still owns. | CR | Yes by source for the outputs. The quoted sentence cannot be true of the second case as described: a symlink to a missing file has no registry behind it. Which was built cannot be checked. A symlink into an unreadable directory also makes `exists()` false (errno probe), so the classification does not depend on it. | XC (gone); Now | Contradicted explicit commitment; one imprecise sentence |
| 74.g | Qualification: only reconcile was executed; `runner list` uses the same loader, and status, verify and remove reach it; their consequences were not exercised. | Scope statement | Yes, and extended in 2.2: remove, install and validate take the lock first, which fails on an inaccessible ancestor before the loader runs. | SR; Now | Accurate observation needing no change |
| 74.h | The `exists()` check dates to `4ca7ff81` and is in every release; the rule to `f6551bf9`; the retained note to `5c1c63dc`. | H | Commits confirmed by `git log -S`. Tags not re-read. | H; Now | Accurate observation needing no change |
| 74.i | Related: DT-72 (another route to recorded plists as candidates), DT-71, DT-35 (exit 2 without an envelope). | Cross-reference | Yes. | — | Accurate observation needing no change |

### 2.2 Comparison

**The obligation as stated.** `docs/contract/50-installation.surface.md`
(owner; rendered at `docs/RESPONSE.md:3780`):

- `:34` condition: "The registry is readable with schema_version 1, or its
  path is absent."
- `:35` effect: "An absent file yields schema_version 1 with empty runners and
  pending_cleanup."
- `:36` retained note: "Registry absence, unreadability and decoded schema
  version are filesystem/decoder outcomes before a registry value exists." and
  "an empty decoded registry cannot distinguish an absent file."
- `:39`: "Unsupported registry schemas and malformed known fields refuse
  loading."
- `:171` reconcile condition: "The registry loaded successfully."

`controller/AGENTS.md:47-49`: "unknown inspection is not absence".
`docs/CONTROLLER.md:387` repeats it for removal.

**Where the registry is located, opened and read.**

| Step | Location | Behavior |
| --- | --- | --- |
| Path | `runner_registry_path`, `runner_manager.rs:508-526` | `PW_RUNNER_REGISTRY` when nonempty, else `$HOME/Library/Application Support/PolicyWitness/runners.json`; unset `HOME` is an error. |
| Read | `load_registry`, `runner_manager.rs:540-560` | `path.exists()` (`:541`), then `fs::read_to_string` (`:549-550`), `serde_json` (`:551-552`), schema comparison (`:553-558`). This is the only read of the file in `controller/src`. |
| Lock | `lock_registry`, `:564-588` | `create_dir_all(parent)`, then opens `<name>.lock` with create. |
| Write | `save_registry`, `:590-623` | Temporary file in the same directory, then `rename` over the path. A symlink at the path is replaced, not followed. |

**How each path state is classified today.** The errno column is this pass's
probe (macOS 26, uid 501); `Path::exists` is `fs::metadata(path).is_ok()`.

| Registry path state | `stat` | `lstat` | open and read | `load_registry` today |
| --- | --- | --- | --- | --- |
| Final component absent, parent present | `ENOENT` | `ENOENT` | `ENOENT` | Empty registry |
| Parent directory absent | `ENOENT` | `ENOENT` | `ENOENT` | Empty registry |
| Parent mode 000 | `EACCES` | `EACCES` | `EACCES` | Empty registry |
| Grandparent mode 000 | `EACCES` | `EACCES` | `EACCES` | Empty registry |
| Parent readable but not searchable | `EACCES` | `EACCES` | `EACCES` | Empty registry |
| File mode 000 | ok | ok | `EACCES` | `Err("failed to read <path>: Permission denied (os error 13)")` |
| Symlink to a missing target | `ENOENT` | ok | `ENOENT` | Empty registry |
| Symlink into a mode-000 directory | `EACCES` | ok | `EACCES` | Empty registry |
| An ancestor is a regular file | `ENOTDIR` | `ENOTDIR` | `ENOTDIR` | Empty registry |
| Symlink loop at the path | `ELOOP` | ok | `ELOOP` | Empty registry |
| Directory at the path | ok | ok | `EISDIR` | `Err("failed to read <path>: Is a directory (os error 21)")` |
| Unparseable JSON or a wrongly typed known field | — | — | — | `Err("failed to parse <path>: …")` |
| `schema_version` other than 1 | — | — | — | `Err("unsupported runner registry schema_version …")` |

A restrictive automation sandbox that denies the metadata read returns
`EPERM`, which `exists()` also turns into false; that case was not probed.

**Every caller, and what it does when the loader returns the empty registry
for a path it could not inspect.** By source; none of this was executed except
reconcile by the review.

| Caller | Loader call | Result for an uninspectable path |
| --- | --- | --- |
| `runner list` | `runner_commands.rs:455-460` via `load_registry_or_default` (`:104-108`) | `runner_registry` envelope with empty `runners` and `pending_cleanup`, `ok`, exit 0. The output carries no registry path. |
| `runner status` | `:484` | `not_found` envelope, exit 2. |
| `runner verify` | `:579` | `not_found` envelope, exit 2; no client is launched. |
| `runner reconcile` | `:752` | `ok`, exit 0, `records: []`; every recognizable plist, including those the registry records, is an `unregistered` candidate. |
| `run` with `runner.id` or `runner.service` | `run_flow.rs:597` → `runner_select.rs:437-443` | `tool_error` envelope, exit 2, `result.error` and each `binaries.<role>.reason` equal to `external runner not found in registry`. No client call. A built-in selection never reads the registry (`runner_select.rs:426-435`). |
| `runner install` | `:284` via `load_registry_locked` (`:113-118`) | Inaccessible ancestor: refused before the loader, at `create_dir_all` or at opening the lock. Symlink to a missing target with an accessible parent: lock taken, empty registry, the conflict check (`:285-296`) passes on nothing, installation proceeds and the final save replaces the symlink with a new file. |
| `runner remove` | `:669` | Inaccessible ancestor: refused at the lock. Symlink to a missing target: `not_found`, exit 2, nothing saved. |
| `runner validate` | `:699` | Inaccessible ancestor: refused at the lock. Symlink to a missing target: visits no record, then saves unconditionally (`:738`), replacing the symlink with an empty registry file, and reports `updated: 0`, `ok`. |

Test-only readers (`runner_manager.rs:2224-2248`, `runner_select.rs:1166-1174`,
`run_flow.rs:2596-2606`) call the same function on fixture paths.

**What readers and tests assert.**

- Absent path reads as empty: asserted in units
  (`runner_manager.rs:2392`, `:2469-2471`) and relied on by every
  session-based case, whose per-service registry does not exist at its first
  `runner list` (`session.py:229-234`).
- Unreadable file, unparseable file, unsupported schema: no assertion anywhere.
  A search of `controller/src` tests, `controller/integration`,
  `tests/suites/runner_byoxpc`, `tests/fixtures/byoxpc` and
  `tests/suites/preflight/check_byoxpc_verification.py` for the three refusal
  texts finds only the producer.
- Inaccessible ancestor: no assertion.
- `run_effects/check_installs_nothing.py:42-43` (default registry unless
  overridden) and `witness_contract/check_dossier.py:363` (the session
  registry its wrapper exports) require `runner list` to exit 0.

**Observation and inference.** Observed by the review: reconcile's outputs
for four registry-path variants. Observed here: the errno table. Read, not
executed: every other caller row, and the lock-first refusal for the three
modifying commands. Inferred: that an operator would apply the guide's
candidate-cleanup steps to owned installations.

### 2.3 Plausible treatments

**P1 — Refuse when the registry path cannot be inspected (product change).**
In `load_registry` only, replace the `exists()` test:

1. `fs::symlink_metadata(path)`: `NotFound` returns the empty registry. Any
   other error returns `Err` naming the path and the system error, with a
   prefix distinct from the read failure (suggested: `cannot inspect runner
   registry <path>: <error>`).
2. On success, `fs::read_to_string(path)` as today, with today's
   `failed to read <path>: <error>` text.
3. Parse and schema checks unchanged.

The signature stays `Result<RunnerRegistry, String>`; all eight callers
already propagate the error, so no caller changes. Resulting classification:

| State | Result | Public form |
| --- | --- | --- |
| Absent path | Empty registry | Unchanged. |
| Inaccessible ancestor, ancestor not a directory | `Err("cannot inspect runner registry …: … (os error N)")` | Runner commands: one line on stderr, exit 2, empty stdout (`cli.rs:63-69`), the form the unreadable file has today. `run` with an external selector: `kind: "run"`, `result.normalized_outcome: "tool_error"`, exit 2, `result.error` and `binaries.<role>.reason` carrying the text (`run_flow.rs:645-664`). |
| Unreadable file, directory at the path | `Err("failed to read …")` | Unchanged. |
| Symlink whose target is missing or unreachable, symlink loop | `Err("failed to read …: … (os error N)")` | New refusal; today an empty registry. |
| Unparseable, unsupported schema | Unchanged | Unchanged. |

The system error number stays in the text, as it does today for the read
failure. No envelope field, vocabulary value or shape golden changes.

*Files.* `controller/src/runner_manager.rs` (`load_registry`, and unit
controls): a build-contract input; **forces a signed rebuild**.
`controller/src/runner_select.rs` (one unit control): the same.
`controller/integration/cli_contract.rs`, the surface, `controller/README.md`
and suite READMEs: not build-contract inputs. No worker-identity regeneration
(`docs/generate_worker_identity.py:26-28` does not read `controller/src`), no
interface-inventory change, no `docs/build.json` change.

*Consequences for those relying on current behavior.*

- `runner list` and `runner reconcile` on a path that cannot be inspected exit
  2 with empty stdout instead of 0 with an empty report. A caller that parses
  stdout without checking the exit sees no JSON.
- `runner status` and `runner verify` in that state stop returning a
  `not_found` envelope; the exit status stays 2.
- `run` with an external selector keeps `tool_error` and exit 2; only the text
  changes.
- `runner install` and `runner validate` stop replacing a registry symlink
  whose target is missing.
- In a restrictive automation sandbox that denies the metadata read, default
  cases that call `runner list` (`run_effects/run_installs_nothing`) fail with
  a diagnostic naming the inspection failure instead of reading an empty
  registry. Root `AGENTS.md` "Sandboxed automation harnesses" already says to
  rerun such a command outside the sandbox.
- Every existing test that starts from a not-yet-created registry path is
  unaffected: `ENOENT` at `lstat` is still the empty registry.
  `registry_recovery.py`'s mode-0500 boundaries keep the directory searchable
  and are unaffected.

*Incorrect behavior a check must reject.* A loader that returns a registry
value for a path whose inspection failed; a `runner list` or `runner
reconcile` that exits 0 in that state; a `run` that reports `external runner
not found in registry` in that state; a loader that refuses an absent path.

**P2 — The same with `Path::try_exists` (product change, narrower).**
`Ok(false)` is the empty registry, `Err` refuses. A symlink to a missing
target stays an empty registry. Then `surface:34` must be reworded so that
"its path is absent" includes a symlink whose target is missing, and install
and validate continue to replace such a link.

**P3 — One step: read and match `NotFound` (product change, narrower).** Drop
the metadata call; `read_to_string` errors other than `NotFound` refuse. Fewer
lines and no gap between inspection and read, but an inaccessible ancestor and
an unreadable file then share one message and are distinguishable from absence
only, not from each other; a symlink to a missing target stays empty.

**P4 — Report the failure inside the reconcile envelope (product change,
larger).** Keep exit 0 and add a registry observation with `unknown` presence.
It needs a new field on `RunnerReconcileData`, a value other than
`unregistered` for candidates found while the registry is unknown, a
shape-golden refresh and new readers, and it leaves `runner list` unsolved.

**P5 — Retain and state the limit.** Not a real candidate: the selected thread
requires the three contrasts to be distinguishable, and the stated condition
at `surface:34` is false for the outputs observed.

**Account edits that land with P1.**

- `surface:34`: "The registry file was read and decoded with schema_version 1,
  or inspecting its path found no entry there."
- `surface:35`: keep; "An absent file" becomes "A path with no entry".
- `surface:36`: add failed inspection to the first reason.
- `surface:39`: "A registry path that cannot be inspected, a registry entry
  that cannot be read, an unsupported schema and malformed known fields refuse
  the command, naming the path and the system error. Ordinary selection of an
  external runner reads the registry through the same loader, and a refusal
  there is that run's tool error."
- `controller/README.md:311-319`: one sentence stating the same three
  outcomes.
- A support owner under "Read and select records" graded `check_read`, citing
  the new unit and integration controls, with the limit that the
  permission-based contrasts are exercised as a non-root user.
- Regenerate with `tests/lib/python.sh docs/generate_contract_stamps.py`.

### 2.4 Recommended disposition per claim

| Claims | Disposition | Reason | Discriminating check |
| --- | --- | --- | --- |
| 74.a, 74.b, 74.f | P1: product behavior change in `load_registry`, with the account edits above. | The stated condition distinguishes a readable registry from an absent path, the standing rule says unknown inspection is not absence, and the present result presents owned installations as unregistered with no signal. One function carries the whole change. P1 over P3 because the thread asks for all three contrasts to stay distinguishable; P1 over P4 because reconcile's condition is already "The registry loaded successfully". | New controls U1, U2 and I1 below. None of `tests/catalog.json`'s existing cases rejects the current behavior. |
| 74.c | P1 as specified (`lstat`), so a symlink whose target is missing refuses. This is a separate behavioral commitment; P2 is the alternative. | Under `lstat` an entry exists at the path, so "its path is absent" is false; the registry it names was not inspected; and treating it as empty lets `runner install` and `runner validate` replace the link (`runner_manager.rs:617`). The cost of refusal: a registry deliberately symlinked to a file that does not exist yet must have its target created by hand, since no command will. A symlinked registry already does not survive the first save. | U1 includes the case. If the maintainer prefers P2, the control asserts the empty registry instead and `surface:34` says so. |
| 74.d | Retain; assert it. | Correct absent case, and the README's "creates no registry or lock". | I1 absent rows; Subject 1's T8 control. |
| 74.e | Retain the classification. The refusal's form (stderr only, exit 2) follows whatever DT-35's disposition settles for runner-command refusals. | It is already a refusal that names path and error. | U1 and I1 assert the text and the empty stdout. |
| 74.f, quoted sentence | Record as imprecise; no action. | See 2.1. | — |
| 74.g | Retain; this file's caller table closes the reading. The consequences remain unexecuted until I1 runs. | — | I1 covers list, status, reconcile and `run`. |
| 74.h, 74.i | Retain; no change. | History and cross-references. DT-72's residual overlap is disposed in Subject 1. | — |

**Controls.** All redirect the registry; none reads the user's real registry
or contacts launchd in the refusing cases, because the loader runs before any
other step.

- **U1**, `controller/src/runner_manager.rs` tests, using `RegistryFixture`
  (`:2224-2248`): `load_registry` returns an empty registry for a path with no
  entry and for a path under an absent directory; returns an error with the
  inspection prefix and `os error 13` for a registry written and then placed
  under a mode-000 directory; returns the `failed to read` error with
  `os error 13` for a mode-000 file; refuses a symlink to a missing target;
  refuses a path whose parent is a regular file and a directory at the path
  (two contrasts that do not depend on the test's uid); refuses unparseable
  JSON and `schema_version: 2`. The fixture's `Drop` restores the directory
  mode before removal. **Forces a signed rebuild.**
- **U2**, `controller/src/runner_select.rs` tests, beside
  `resolve_via_registry_blocks_external_runner_missing_entitlements`
  (`:1176-1199`): with the registry override under a mode-000 directory and an
  external selector, the error has the inspection prefix and is not `external
  runner not found in registry`. **Forces a signed rebuild.**
- **I1**, `controller/integration/cli_contract.rs`, on the signed app in place
  with `HOME` and `PW_RUNNER_REGISTRY` in scratch: for an absent path,
  `runner list` exits 0 with empty collections and creates nothing; for an
  inaccessible ancestor and for an unreadable file, `runner list`,
  `runner reconcile` and `runner status --service-name x` each exit 2 with an
  empty stdout and a stderr line that names the supplied path, the expected
  prefix and the error number, and the two prefixes differ; `run` with a
  request that carries the app's contract (the crate's `candidate_contract()`,
  `:66`) and selects `{"mode":"byoxpc","service":"x"}` returns a `tool_error`
  envelope whose `result.error` has the inspection prefix. Without the app's
  contract the request is refused before selection. The absent-path and
  not-a-directory rows can also be written as corpus cases in
  `controller/integration/interface_cases.json`, whose steps accept `env` with
  `{scratch}` and `stderr_prefix` (`cli_contract.rs:1650-1733`); the mode-based
  rows need a test function because the corpus cannot set modes.

**Are `runner_byoxpc` opt-in cases needed?** Not to establish the contrasts:
U1, U2 and I1 do that with a redirected registry and no launchd contact. They
are needed as routed regression verification because install, verify and
remove share the changed loader: `runner_byoxpc/registry_recovery`,
`runner_byoxpc/runner_install` and `runner_byoxpc/default_location` confirm on
the rebuilt app that a not-yet-created session registry and the default
registry still load. No new opt-in case is proposed.

### 2.5 Resulting user duties

1. Check the exit status and stderr of every `runner` command. Exit 2 with
   `cannot inspect runner registry` or `failed to read` means the registry was
   not read; it does not mean no runner is registered. Restore access before
   installing, removing or cleaning up anything.
2. Do not conclude from an empty `runner list` that a registry file exists.
   An absent path and an empty registry print the same data; reconcile's
   `registry_path` shows which path was read.
3. Until P1 ships: an `ok` reconcile report with no records under a registry
   path that should hold records is not evidence that the plists it lists are
   unregistered.

### 2.6 Implementation worklist

1. Write U1, U2 and I1 first. Run `unit/rust.unit` and observe U1 and U2
   fail on the inaccessible-ancestor, not-a-directory and symlink contrasts;
   run `integration/cli.integration` against the existing app (build 1519) and
   observe I1 fail on its inaccessible-ancestor rows and its `run` row. Keep
   both results as the record that the controls reject current behavior. An
   edit to U1 or U2 changes the build contract as soon as it is in the tree.
2. `controller/src/runner_manager.rs`, `load_registry` (`:540-560`): P1. Correct
   the comment at `:509-513` only if its noun becomes wrong.
3. `docs/contract/50-installation.surface.md` `:34-39` and the new support
   owner; `controller/README.md:311-319`;
   `tests/suites/integration/README.md` and `tests/suites/unit/README.md`
   invariants. If an owner cites an integration test, review whether the
   surface's `checks` list at `:7` should name `integration`; that list is
   DT-14's subject.
4. `tests/lib/python.sh docs/generate_contract_stamps.py`, then `--check`.
5. `unit/rust.unit`, `unit/rust.fmt`, `unit/rust.byoxpc_reds`, `source_drift`.
6. Signed rebuild through the documented pipeline with the maintainer's
   identity.
7. On the rebuilt app: `integration/cli.integration`;
   `runner_byoxpc/registry_recovery`, `runner_byoxpc/runner_install`,
   `runner_byoxpc/default_location` in a logged-in GUI session, verifying
   owned resources absent afterward; then the group's default battery, which
   includes `run_effects/run_installs_nothing` and
   `preflight/byoxpc_verification_controls`. Routes:
   `tests/CHANGE-VERIFICATION.md` "Registry recovery", "runner_byoxpc" and
   "BYOXPC default location"; `controller/AGENTS.md` rows "Selection, signing,
   registry or recovery" and "Public CLI arguments and envelope behavior"; the
   plan's row "Installation, registry, reconciliation or cleanup".
8. Land the loader, its controls and its account edits together, with
   Subject 1's group B unit control in the same rebuild.

---

## Outside the review

Not findings of the review, and not assessed further here.

- `runner validate` uses the same idiom on the recorded executable:
  `runner_commands.rs:705-709` counts a path that `exists()` cannot confirm as
  `missing`, sets `signature.valid = false` and `entitlements.error =
  "executable missing"`, and `:738` saves that. An executable under an
  inaccessible ancestor is therefore recorded as missing. `surface:142` and
  `:683` say "did not exist". A later validate with access restores the
  observations.
- The read act's entry list (`surface:31`) names list, status, verify, remove
  and reconcile. `runner install` (`runner_commands.rs:284`), `runner validate`
  (`:699`) and external selection in `run` (`runner_select.rs:441`) use the
  same loader.

During this pass, another actor modified `tests/catalog.json` and
`tests/suites/source_drift/run.sh` and added
`tests/suites/source_drift/test_markdown_reader.py` in the working tree
(timestamps 19:14–19:15 on 2026-11-17). This pass did not write them, and the
catalog case ids cited above were read before that change.
