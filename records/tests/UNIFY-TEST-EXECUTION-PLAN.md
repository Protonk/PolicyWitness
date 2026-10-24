# Unify test execution: implementation plan

One supported public way to exercise PolicyWitness tests, used identically in
ordinary development and release production. This plan is the associated plan
of the [opt-in survey](OPT-IN-REPORT.md), which examined revision `2f23cad`;
the tree is unchanged since, and every statement below about current behavior
was re-read from source at that revision. Default and non-default membership
is a constraint here, not a subject.

## Problem

The repository already has one selection and accounting implementation,
`tests/run.sh` with `tests/catalog.json`, and it is already what `make test`
and the release battery run. Around it sit routes that exercise the same
scripts under different rules:

- Every case script runs when invoked directly, because the shared library
  treats an absent selection as "everything" (`tests/lib/testlib.sh` lines
  173-180) and defaults its output to `tests/out/runs/direct` (lines 47-56).
  A direct `tests/suites/preflight/run.sh` therefore runs the five opt-in
  build controls; a direct `tests/suites/smoke/run.sh` runs one of three
  cases; a direct `tests/suites/runner_exec_inheritance/run.sh` runs the
  opt-in launch inventory. None of these produces a `run.json`, but each
  produces per-case reports under a directory the documentation names.
- Five `run.sh` files under `tests/suites/` are wrappers no catalog case
  names (`smoke`, `witness_contract`, `blackbox_e2e`, `run_effects`,
  `opt_in`), and one catalog command is a single-child wrapper
  (`sbpl_allowdeny_consistency/run.sh`). The `shell_helpers/script_groups`
  control copies six wrappers into fixture repositories and pins their direct
  behavior (`tests/suites/shell_helpers/check_scripts.py` lines 141-203).
- Release acceptance selects its own two-case battery
  (`tests/lib/release_accept.py` line 19) and then `make release` runs the
  default battery against a different path to the same bytes. The archive
  binds the battery to `dist/PolicyWitness.app` by path
  (`tests/lib/release_archive.py` lines 103-104), not to the ZIP it ships.
- `tests/FAILURE-PROPAGATION-CONTRACT.md` lines 1461-1463 say acceptance
  selects every registered case including opt-ins; nothing does.
- Documentation names the standalone Cargo command as a verification step
  (`tests/AGENTS.md` line 67) and repeats the direct-output default in
  twenty-two suite READMEs and the registry.

## Intended result

- `tests/run.sh` is the one test interface: `--case`, `--suite`, `--all`,
  no selectors for the default battery, `--list` to inspect, `--prune` for
  output. `make test` remains as its documented shorthand for the default
  battery against `$(DIST_DIR)`, forwarding without selectors.
- Every case script refuses to run outside a dispatcher invocation, with a
  message naming the `tests/run.sh --case` form. No script under
  `tests/suites/` is a public command, and no wrapper exists that is not a
  catalog command.
- Release production runs the default battery once, through `tests/run.sh`
  with no selectors, against the contents of the final stapled ZIP, inside
  release acceptance. Acceptance keeps its artifact checks (layout, staple,
  Gatekeeper, signatures, inventory, hash) and its standard-runner provenance
  check, now read from the battery's evidence. The archive binds the tested
  bytes to the shipped ZIP by inventory, not by path.
- Documentation, the Makefile card and the release procedure agree on the
  above; language test tools are described as the internals of their batch
  cases.
- Checks in the default battery detect a reintroduced direct route, a
  release-specific selection, or a documented alternative command.

## Entry-point census

Established by reading the scripts and by read-only `--list` planning
(counts in the survey, B.1 and B.2). "Semantics" says whose selection and
accounting rules apply.

| Route | What it does today | Semantics | Disposition |
| --- | --- | --- | --- |
| `tests/run.sh` (`tests/lib/test_cli.py`, `suite_run.py`) | Catalog selection, dependency closure, equipment, skips, unrun accounting, `run.json`, artifact integrity, lock, retention | Canonical | Keep; the public boundary |
| `make test` | `PW_APP_DIR=$(DIST_DIR)/PolicyWitness.app ./tests/run.sh` | Canonical, forwarded | Keep as the documented shorthand; no selectors ever |
| `tests/suites/opt_in/run.sh` | `exec tests/run.sh --suite opt_in` | Canonical, forwarded | Remove; the group stays in the catalog and its README names the selector |
| 37 `tests/suites/*/run.sh` catalog commands (161 cases) | Under the dispatcher, run the selected leaves; directly, run every leaf they enumerate | Dispatcher when launched by it; none when direct | Keep as internal case commands; refuse without dispatcher context |
| 74 own-script catalog commands (74 cases; 16 under `opt_in/` directories) | Same | Same | Same |
| `tests/suites/{smoke,witness_contract,blackbox_e2e,run_effects}/run.sh` | Wrappers over sibling scripts; not catalog commands | None: no selection, no `run.json` | Remove |
| `tests/suites/sbpl_allowdeny_consistency/run.sh` | `exec bash sbpl_allowdeny_v1.sh`; is the catalog command | Dispatcher | Point the catalog at `sbpl_allowdeny_v1.sh`; remove the wrapper |
| `tests/suites/runner_byoxpc/run.sh` direct branch (lines 84-88) | Without `PW_TEST_CASES`, runs its own list including the `blackbox_e2e` wrapper | None | Remove the branch; the script runs only under selection |
| `tests/accept-release.sh` (`release_accept.py`) | Artifact checks, then `tests/run.sh --case` twice against the extracted ZIP | Dispatcher accounting over a release-specific list | Keep the artifact checks; replace the list with the default battery |
| `make notarize` | Fresh build, submit, staple, validate, Gatekeeper, re-zip, acceptance | As acceptance | Unchanged shape; acceptance now carries the battery |
| `make release` | Preflight, notarize, then a second default battery against `dist/PolicyWitness.app`, archive, rotate | Dispatcher | Drop the second battery; archive binds the acceptance's battery |
| `tests/lib/release_archive.py --battery` | Validates the battery run and ties it to the dist app path | Validation | Validate the acceptance's nested battery and bind it to the ZIP by inventory |
| `cargo test` by hand, `tests/lib/checkout_lock.sh -- cargo test` | Cargo discovery: 221 of 223 tests, two `#[ignore]` | Cargo's | Keep runnable; document as local debugging of the `unit` and `integration` cases, never as battery evidence |
| `swift run PWRunnerCoreTests` by hand | Every TestKit block; equipment failures are failures | TestKit's | Same, for `runner_unit/pwrunner_core_unit_executable` |
| Documentation routes | `runs/direct` boilerplate in 22 suite READMEs and `tests/OPT_IN_TESTS.md` lines 3-5; `tests/README.md` lines 94-99, 239-245, 389-393; `tests/AGENTS.md` lines 26 and 67; `tests/suites/runner_exec_inheritance/README.md` line 46; `tests/suites/shell_helpers/README.md` lines 110-133; `tests/suites/integration/README.md` line 14; `docs/BUILD.md` lines 562-573; `docs/SIGNING.md` lines 194-237, 353, 375-433, 473-493; the FPC sentence | Prose | Correct in the stage that changes the mechanism |

No CI configuration exists; nothing outside this table runs tests. The
`records/` harnesses are investigation equipment and are out of scope.

## The public boundary

`tests/run.sh` is the interface. Inside it, nothing changes about selection,
closure, equipment, skips, unrun accounting, `run.json`, locking or
retention; `dispatcher/selection_controls` already pins that contract and
keeps doing so. The boundary is made exclusive at two places:

1. **Case scripts require dispatcher context.** The executor already sets
   `PW_TEST_CASES`, `PW_TEST_EVENTS`, `PW_TEST_OUT_DIR` and `PW_TEST_RUN_ID`
   for every case it launches (`tests/lib/suite_run.py` lines 426-430 and
   459). `testlib_init` (called by `test_begin`) and `test_selected` refuse
   with exit 2 when `PW_TEST_CASES` or `PW_TEST_EVENTS` is unset, printing
   `run through tests/run.sh --case <suite>/<id>`; the `runs/direct` default
   and the `PW_TEST_EVENTS` default go away. Sourcing the library stays
   side-effect free, because `tests/run.sh`, `tests/accept-release.sh` and the
   executor's identity probe source it without beginning a case. Nothing
   consults the catalog from inside a script; the gate is presence of the
   context the dispatcher alone supplies, and authority remains what it is
   today: a terminal `run.json` under a dispatcher-owned directory.
2. **Release production calls the interface without selectors.** Acceptance
   invokes `tests/run.sh` with no arguments against the extracted ZIP app.
   The archive verifies that the recorded run had empty `requested_cases` and
   `requested_suites` (it does already) and that its tested bytes are the
   archived ZIP's.

Rejected alternatives, briefly. Teaching direct scripts to read the catalog
would be a second selection implementation. Keeping direct invocation and
documenting it as unofficial is what exists now. A `--release` mode or a
release-specific selector would recreate a second battery.

## Release path: what acceptance verifies and what changes

Today `release_accept.py` extracts the final ZIP under `/private/tmp`,
inventories and inspects the app, validates the staple, assesses Gatekeeper,
runs `smoke/specimen_file_read_deny` and `witness_contract/happy_path_baseline`
through `tests/run.sh --case` with inherited `PW_*` stripped, requires both to
pass with `completion == {selected: 2, completed: 2, skipped: 0, unrun: 0}`,
reads both envelopes to require `runner_kind == "standard"`, and re-inventories
the app and re-hashes the ZIP. Its legitimate purposes beyond the battery are:
the shipped bytes execute from an extracted location through their own bundled
runner; nothing inherited could substitute a local app; the artifact did not
change while under test. Those remain. What goes is the two-case list.

Both cases are default members, so the default battery contains everything
acceptance asserted and 194 more. The battery takes about 14 minutes here
(retained runs `release-0.3.3-default` and `observer-retirement-default-01`,
local to this checkout); the two cases take well under one.

**Decision: R1, the battery runs inside acceptance.** Acceptance invokes
`tests/run.sh` with no selectors, `PW_APP_DIR` the extracted app,
`PW_TEST_OUT_DIR` its nested `tests/` directory, and a fixed bound of 7,200
seconds in place of the current 180 s. It requires `ok`, `completion.unrun == 0`,
`completion.skipped == 0`, `completed == selected`, empty `requested_*`,
`configuration.app_dir` equal to the extracted app and
`artifact_integrity.valid_before and unchanged`. The provenance check reads
the same two envelopes out of the battery's reports. `acceptance.json` gains
the battery's `run_id`, `completion` and times. `make release` loses its
separate battery step; `release_archive.py` derives the battery from the
acceptance's nested run instead of `--battery`, keeps every validation in
`battery_record` except the dist-path rule, and adds the binding that matters:
the battery's `artifact-integrity/before.json` inventory equals, in full, an
inventory of a fresh extraction of the archived ZIP, taken where
`outer_seal_facts` already extracts it. `artifact.inventory` records every
path's mode, each regular file's hash and each symlink's target; the
comparison is equality of that whole record. Both sides are extractions of
the same ZIP by the same tool, so any difference, a mode bit included, is a
defect or tampering and fails archiving. No normalization is applied unless
a specific difference is explained, justified in the archive code and
covered by a control. The portable evidence packs one `acceptance` role (which
now contains the battery) plus `battery.json` copied from
`acceptance/tests/run.json`; rotation takes its checkpoint from that summary
and protects the acceptance directory. `tests/RETAINED.json` gains one entry
per release instead of two.

The bound. `release_commands.command` already records `timeout_seconds`
and `elapsed_seconds` in the step's `command.json`; on expiry it sends the
dispatcher SIGINT, waits five seconds for it to finalize with its own
interruption accounting, then kills the process group and raises. Acceptance
therefore fails on a timeout, the nested `tests/` directory keeps whatever
the dispatcher wrote (a terminal `run.json` naming the interruption when it
finalized in time, otherwise an interrupted run), and the acceptance
directory is retained as failed evidence. `acceptance.json` copies the limit
and the elapsed time beside the battery summary. The limit is an initial
operational ceiling: the 14 minutes measured here on one machine on AC power
do not establish the slowest supported machine's runtime, and the ceiling is
revised from recorded elapsed times, not from the battery's size.

Cost of R1: `make notarize`, the rehearsable chain, grows by the battery's
duration, and a failing default case now stops acceptance rather than the
later battery step. Benefit: the tested bytes are the shipped bytes, tested
from where a user would run them, once, and a rehearsal is a complete
rehearsal.

**Rejected alternative R2:** acceptance keeps only artifact checks;
`make release` keeps one battery against `dist/PolicyWitness.app`; the
archive binds that battery's inventory to a fresh extraction of the ZIP; the
provenance check moves to the archive and reads the battery's envelopes. Same
binding strength on bytes and a fast rehearsal, but a rehearsal leaves an
untested ZIP and the battery never executes from the extracted location.
Rejected for those two reasons.

Under either, the FPC sentence is rewritten to what is true: change
acceptance selects through `tests/run.sh` by catalog identity; release
production runs the default battery; `--all` is the complete registered
population and is selected explicitly.

## Staged changes

Each stage leaves the default battery green and `tests/run.sh --all --list`
identical in membership to today (235 cases, 196 default, 39 non-default),
except where a command path is named below.

### Stage 1: close the direct route

Code.

- `tests/lib/testlib.sh`: `testlib_init` requires `PW_TEST_OUT_DIR` and
  `PW_TEST_EVENTS`; `test_selected` requires `PW_TEST_CASES`; both refuse with
  exit 2 and the canonical command. Remove the `runs/direct` and events
  defaults. `skip_missing_pw_app`/`require_pw_app` stay (the dispatcher turns
  their undeclared skips into `unexpected_skip`).
- Delete `tests/suites/{smoke,witness_contract,blackbox_e2e,run_effects,opt_in}/run.sh`.
  Point `sbpl_allowdeny_consistency`'s catalog command at
  `tests/suites/sbpl_allowdeny_consistency/sbpl_allowdeny_v1.sh` and delete
  its `run.sh`. Remove the direct branch of `tests/suites/runner_byoxpc/run.sh`
  (lines 70-88 keep only the selected-leaf loop). `tests/lib/scripts.sh`
  remains for that wrapper's children.
- `tests/suites/source_drift/check.py`: a suite directory is a directory
  under `tests/suites/` with `README.md` (replacing `suites_with_run_sh`, lines
  138-147); the catalog's suite set and the README table rows must equal that
  set (`check_index_vs_disk`, lines 254-266); add a rule that every `run.sh`
  under `tests/suites/` is named by a catalog command, with the usual
  disposable-checkout positive and negative controls.
- Controls that start case scripts themselves must now supply the context:
  `tests/suites/shell_helpers/check_scripts.py` (drop the five retired
  wrapper exercises; keep the generic group exercises; set `PW_TEST_CASES`
  and `PW_TEST_EVENTS` for the `runner_byoxpc` exercises and replace the
  `byoxpc_success` family, which relied on the direct branch, with selected
  variants), `check_mutation_prerequisites.py` (lines 41-44),
  `check_finalizers.py`, `check_worker_setup.py`,
  `tests/suites/blackbox_e2e/disposition_controls.py`, and the dispatcher
  fixture `tests/fixtures/dispatcher/run.sh`, which already runs under the
  real executor and should need no change; confirm.
- Extend the existing `shell_helpers/controls` case
  (`tests/suites/shell_helpers/check.py`, run by
  `tests/suites/shell_helpers/run.sh` lines 31-41) with refusal assertions: a
  real case script (one from each library path: a `run.sh` command, an own
  script, the BYOXPC wrapper) invoked without `PW_TEST_CASES` exits 2, writes
  no report, no event and no output directory, and names the canonical
  command; the same script with the context behaves as before; and
  `tests/out/runs/direct` is never created. No new catalog identity:
  membership stays at 235 cases and 196 defaults throughout.

Documentation.

- `tests/README.md`: lines 59-64 and 94-99 name `tests/run.sh` as the
  interface and `make test` as its shorthand; remove the direct-entrypoint
  sentences at 239-245 and 389-393 and describe the refusal.
- `tests/AGENTS.md` line 26 ("Direct suite scripts omit the dispatcher's
  guarantees") becomes the refusal rule; line 115's alignment list is
  unchanged.
- The `<run>` paragraph in the 22 suite READMEs and `tests/OPT_IN_TESTS.md`
  lines 3-5 and 45-46 drop the direct default. `tests/suites/opt_in/README.md`
  names `tests/run.sh --suite opt_in` only.
  `tests/suites/runner_exec_inheritance/README.md` line 46 names the `--case`
  form. `tests/suites/shell_helpers/README.md` lines 110-133 and
  `tests/suites/dispatcher/README.md` lines 24-26 describe the remaining
  BYOXPC wrapper and the refusal assertions in `shell_helpers/controls`.

Verification. `tests/run.sh --suite shell_helpers --suite source_drift
--suite dispatcher` against a signed build; then the default battery; then
`tests/run.sh --all --list` compared with the plan recorded before the stage
(same 235 identities, same requirements, one changed command path). A direct
invocation of three real scripts, performed by `shell_helpers/controls`, is
the evidence that the route is closed; a hand invocation is not needed.

### Stage 2: language tools and guidance

Documentation only.

- `tests/AGENTS.md` lines 66-68: the limit-change verification names
  `tests/run.sh --suite unit --suite integration` and the listed suites; the
  standalone Cargo command moves to the locking note at line 168 as
  debugging guidance.
- `tests/README.md` lines 225-231 and `docs/BUILD.md` lines 562-573: keep the
  lock instructions, state that a standalone `cargo test` or
  `swift run PWRunnerCoreTests` exercises the crate or package for local
  debugging, runs under its tool's own rules (two Rust tests are `#[ignore]`
  there and run only through `runner_unit`), and is not a run of any catalog
  case. `tests/suites/integration/README.md` line 14 names the case.
- `tests/FAILURE-PROPAGATION-CONTRACT.md` lines 1461-1463 rewritten as
  above.
- `docs/BUILD.md` carries generated regions; these lines are outside them.
  Run `tests/lib/python.sh docs/generate_limits.py --check` and the
  `source_drift` suite to confirm no generated copy is touched.

Verification. `tests/run.sh --suite source_drift`.

### Stage 3: one battery in release production

Code.

- `tests/lib/release_accept.py`: remove `CASES`; invoke `tests/run.sh` with
  no arguments; replace the completion check as specified under R1; keep the
  stripped environment; read the two provenance envelopes from the battery;
  pass `timeout=7200` to `command()`, which records the limit and the elapsed
  time in `execution/command.json`; copy both with the battery's `run_id`,
  `completion` and times into `acceptance.json`; keep the suggested retention
  entry. A timeout is a failed acceptance with the nested output retained, as
  described under the bound above.
- `tests/lib/release_archive.py`: locate the battery at
  `<acceptance>/tests` from the acceptance pointer; drop `--battery` and the
  dist-path rule; add the inventory binding against a fresh extraction of the
  final ZIP, as full inventory equality with no mode fallback; one retained
  entry per release.
- `tests/lib/release_runs.py`, `release_rotate.py`, `release_cleanup.py`:
  a nested evidence format, explicitly distinguished from the existing one.
  The test-runs manifest becomes `schema_version: 2` with the single
  `acceptance` role, a declaration that the battery is `tests/run.json`
  inside that role, and the same two summaries, `acceptance.json` and
  `battery.json`; `release.json.battery.original_path` names the nested run
  under `release-acceptance/`. Rotation takes its checkpoint from
  `battery.json` in both formats, and the rotation journal format
  (`schema_version: 2` in `tests/out/.release-rotation/`) does not change.
- Compatibility requirement. The six archives under `dist/archive/`
  (`v0.2.7` to `v0.3.3`, local to this checkout) carry manifest
  `schema_version: 1` with the separate `acceptance` and `battery` roles and
  a battery `original_path` under `runs/`. They must keep verifying through
  `release_runs.verify_release` and `verify_bundle`, which `make publish`
  runs again on every invocation, and an interrupted rotation whose journal
  references a separate battery must still resume through
  `release_rotate.py --apply`. The verifiers and rotation dispatch on the
  manifest's schema version; no historical archive, journal or retention
  entry is rewritten, and the new packer writes only the nested format.
- `Makefile`: `release` drops the battery lines; the help card's `notarize`
  and `release` entries say the acceptance runs the default battery against
  the final ZIP's contents.
- Controls: `tests/fixtures/release/tools.py` asserts the test command is
  exactly `bash tests/run.sh` with no further arguments and produces a
  default-shaped `run.json` (nonzero `selected`, empty `requested_*`,
  `artifact_integrity`), with a new `selected` mode whose `run.json` carries
  a selector and must be refused, and a `timeout` mode whose acceptance fails
  with the nested output retained; `tests/suites/preflight/check_release.py`
  gains those modes; `check_release_publish.py` (`make_battery`, lines
  273-290 and 453-475) models the nested battery and adds "battery inventory
  differs from the ZIP" to the rejected scenarios, in two forms: a changed
  file hash, and a battery inventory that differs from the fresh extraction
  in exactly one mode bit of one file with every hash equal; both must be
  refused with the binding named; `check_release_rotation.py`
  (`portable`, lines 88-112, asserts the battery role today) becomes
  format-aware. Both control files keep a builder for the schema 1 shape and
  gain one for schema 2, so verification, archiving refusals, publication
  re-verification and interrupted-rotation resumption are exercised against
  both formats without copying a real archive into the fixtures.

Documentation. `docs/SIGNING.md`: the release procedure (lines 194-237),
the step table (line 353), the manual equivalents (lines 375-433) and "What
archive acceptance proves" (lines 473-493) describe one battery inside
acceptance and the inventory binding. `tests/README.md` lines 101-109
likewise. `docs/DEPENDENCIES.md` is unaffected.

Verification. `tests/run.sh --suite preflight` minus the opt-in members, that
is the four release control cases by `--case`; the default battery; then
`release_runs.verify_release` run read-only over each of the six local
archives, which must pass unchanged. The real chain cannot be rehearsed
without a notarization submission, which is the
user's step; the first `make release` after this stage is the live evidence,
and its archive must verify (`release_runs.verify_release`) and publish. To
exercise the real acceptance path offline, extend the opt-in
`preflight/build_refusal_controls` driver, which already runs `make notarize`
and `make release` with a controlled build step, with controlled staple,
Gatekeeper and notarization stand-ins so that the real `release_accept.py`
runs the real default battery against a real build ZIP once. During
implementation, extract `make build`'s own ZIP twice with `ditto` and
confirm the two `artifact.inventory` records are equal; that is the
comparison the binding performs. A comparison with `dist/PolicyWitness.app`
is informative only and is not the binding: differences between the working
app and an extraction, should any exist, do not justify weakening the
extraction-to-extraction equality.

### Stage 4: protections against reappearance

- `source_drift`: a Markdown rule over every document outside `records/`
  that forbids `tests/suites/` paths presented as commands (a code span or
  fenced line beginning with `bash tests/suites/`, `./tests/suites/` or a
  bare `tests/suites/<x>/<y>.sh` invocation), forbids `runs/direct`, and
  requires that the only `tests/run.sh` invocations in `Makefile` and under
  `tests/lib/release_*.py` carry no selectors. Positive and negative
  controls in disposable checkouts, as the suite does for its other prose
  rules.
- The `shell_helpers/controls` refusal assertions and the stage 3 argument
  assertion are the behavioral protections; the `dispatcher/test_command_controls` membership
  oracle already guards the `opt_in` group.
- `tests/AGENTS.md` "Add or change tests" states the rule: a case is reached
  only through `tests/run.sh`; a new wrapper or a documented direct command
  fails the drift suite.

## Acceptance evidence

| Criterion | Evidence |
| --- | --- |
| One documented canonical invocation governs all supported testing, including release production | `tests/README.md`, `tests/AGENTS.md`, the Makefile card and `docs/SIGNING.md` name `tests/run.sh`; `release_accept.py` invokes it without selectors; the stage 4 text rule passes |
| Development and release testing share selection and accounting and record the tested artifact | The release `run.json` is a default-selection run with empty `requested_*`; `configuration.app_dir` and `artifact-integrity/before.json` identify the extracted app; the archive's full inventory equality, modes included, ties them to the ZIP hash, and the one-mode-bit control is refused |
| No release-specific list or script defines a second battery; obsolete direct routes cannot claim an authoritative run | `CASES` is gone; the `tools.py` argument assertion and the `selected` rejection mode pass; three real scripts refuse without context in `shell_helpers/controls`; no `run.sh` exists outside the catalog |
| Membership, dependency closure and targeted selection are preserved | `tests/run.sh --all --list` before and after each stage: identical identities, `default` flags, `requires`, `depends_on`; one command path changed (`sbpl_allowdeny_consistency`) |
| Prerequisites, skips, unrun cases and failures stay visible with consistent completion effects | Unchanged dispatcher code; `dispatcher/selection_controls` and `accounting_controls` pass; acceptance refuses skips and unrun cases as the archive does |
| Guidance, release procedure and implementation agree | The stage 2 and 3 documentation edits; `source_drift` passes, including the new rules |
| Verification exercises the real entry paths and detects bypasses | Real scripts are invoked in `shell_helpers/controls`; the real `release_accept.accept` runs under the release controls with argument and timeout assertions; the opt-in driver runs the real acceptance battery once against a real build ZIP |
| Existing archives stay verifiable and interrupted rotations resumable | `verify_release` passes on the six local archives unchanged; the publish and rotation controls exercise schema 1 and schema 2 fixtures, including a resumed rotation whose journal names a separate battery |

## Decisions

Settled before implementation, on 2026-10-24:

1. **R1.** The default battery runs once inside acceptance against the
   extracted final ZIP. This verifies execution from the shipped artifact and
   makes `make notarize` a complete rehearsal; the added duration is accepted.
2. **A fixed 7,200-second bound.** The limit and the elapsed time are
   recorded; a timeout fails acceptance and preserves partial evidence. This
   is an initial operational ceiling, not a measurement of the slowest
   supported machine.
3. **The refusal assertions extend `shell_helpers/controls`.** No new catalog
   identity; membership is preserved exactly.
4. **Existing archives and interrupted rotations keep working.** The nested
   format is distinguished by schema version, both formats are verified and
   exercised by controls, and no historical archive is rewritten.
5. **The inventory binding is full equality, modes included.** Both sides
   are extractions of the same ZIP; an unexplained difference fails
   archiving. Any normalization must be justified in the code and covered by
   a control, and a control that changes only one mode bit must be refused.

Routine for the executor: the exact wording of the refusal, the order of the
three scripts the assertions invoke, and the field names of the battery
summary beyond those named above.
