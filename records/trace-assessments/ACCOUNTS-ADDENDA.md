# Accounts addenda

Status, 2026-11-19, checked against `62d1c3d0`. Product source at that commit
equals `a4d49249`. This file supplements `ACCOUNTS-WORKLIST.md` for the three
technical-account passes in `records/TRACE-MANAGEMENT-PLAN.md`. It replaces
the coordinator's scratch addenda of November 18. The worklist's rules apply:
read the current text first, and correct a false statement with the scope
needed to state current behavior. `DISPOSITIONS.md` governs.

Part 1 takes the worklist sections from "Contract surfaces" through "Generator
code". Part 2 takes "Failure evidence contract" through "READMEs and test
accounts", and Part 3 takes "Test-side repairs". Each pass reports four counts:
entries it applied, entries a product thread already did, entries that do not
apply to current text, with reasons, and entries left undone, with reasons. It
also reports any statement it could not make true without a product change.
The sections no pass owns are settled below.

## Entries found after the worklist

### Part 1

- **`docs/build.json`, after R14 (`fc4586fc`).** The contract check's
  `reads` do not name the `docs/*.md` documents that the generator now scans
  for region markers outside the map. `input_paths` in
  `docs/generate_contract_stamps.py` declares them. Correct the entry and
  regenerate `docs/BUILD.md` with `docs/generate_build.py`.
- **`docs/contract/README.md`, after R14.** State the authoring rule that a
  document removed from the presentation map must lose its contract regions,
  because generation refuses markers in an unmapped `docs/` document.
- **The worklist's own R14 entries are done.** These are DT-01.a and DT-02.a
  in `presentation.py`, `input_paths`, and the `generators.py` controls with
  their description; skip them. The record-label entry (DT-05) in
  `presentation.py` is not done.
- **The installation surface's read rule.** In
  `docs/contract/50-installation.surface.md`, "Read and select records", the
  `entry` list omits `runner install`, `runner validate` and external runner
  selection in `run`, although all three use the same loader. This still
  holds at `62d1c3d0`. CONTROLLER-A left it for this pass. It is one of the
  worklist's coordinator notes (pass F).
- **The installation surface's `missing` field.** Its text is "Rows whose
  recorded host executable did not exist". `runner validate` decides with
  `Path::exists` in `controller/src/runner_commands.rs`, which is also false
  when an ancestor cannot be searched, so an executable it cannot inspect is
  counted and saved as missing. Correct the statement to the decision the
  code makes. Whether validate should refuse such a row, as R2 does for the
  registry, is a product question that no ruling covers. It belongs to the
  maintainer-judgment outflow. This is also a coordinator note (pass F).
- **Support grades for CONTROLLER-C's owners.** The thread reported that it
  graded two owners' support as check-read rather than executed. The retained
  thread note does not name them. Check the support grade of each owner that
  `227e5fc2` and `b5a941e7` changed in `11-policy`, `35-profile` and
  `42-dossier`.

### Part 2

- **`docs/LIMITS.md`, "Interactions that matter", first bullet.** It reads
  "Budgets nest, and one flag changes one of them … `worker_sentinel_wait`,
  the validator deadline `validator_io_wait` … keep their own values." Four
  rows are now classified "Flag" for a `policy-witness test-input run` test
  control: `worker_sentinel_wait`, `validator_io_wait`,
  `phase_collection_wait` and `actor_collection_allowance`. Scope the sentence
  to `policy-witness run`, where one `run` flag changes one budget and the
  others keep their values. Do not explain the test controls; the rows name
  them. If the sentence is a shared region copied to the guide, correct the
  owner and leave the guide copy frozen.
- **Accounts that still place a test control in `_test_overrides`.** Run
  `git grep -n '_test_overrides\.'` over `docs/*.md`, `docs/*.json`,
  `controller/README.md`, `runner/README.md`, `runner/AGENTS.md`,
  `tests/**/README.md` and `tests/*.md`. Each hit must be true of current
  behavior:
  - The two worker substitutions are request keys.
  - The eight controls are `test-input run` flags.
  - The host's refusal field for a refused validator control is still
    `_test_overrides.validator_executable_path`.
  - The internal record keeps its name.

  List hits in build inputs instead of editing them.

### Part 3

- **`tests/suites/source_drift/interface_literals.py`.** It cannot tokenize a
  Rust character or byte literal that holds an escaped quote (`b'\''`). Two
  drift cases fail on such a literal anywhere under `controller/src`.
  CONTROLLER-C respelled its own literal and left the reader unchanged. Repair
  the reader, adding a rejecting neighbour and a passing row for the escaped
  forms.

### Final integrated verification, not a pass

- `tests/lib/contract_fixture.py::presentation` now removes contract regions
  from documents that a constructed map does not name. `build_refusals.py`
  uses it, and `preflight/build_refusal_controls` has not run since
  `fc4586fc`. Final verification runs that case.

## Leftovers the product threads reported

The management plan's progress entries name what CONTROLLER-A and
CONTROLLER-B left for this work. Apart from the read rule's entry list above,
every item named is a worklist entry: DT-28.c/e, DT-34.b/c/d, DT-69, DT-78,
DT-79, DT-116.g and DT-119.a, the installation surface's checks list, the
helper-envelope row, the oversize limits rows, `tool_exit_code` and `stderr`,
and the eligibility, `actor_id` and transport limits. CONTROLLER-B also
reported "four smaller entries" that no retained note names. Checking every
worklist entry against current text covers them, whatever they are.

The HOST progress entries record that the host-thread comment entries were
corrected. They name no leftover. Neither do the EXEC, WIRE and IDENT entries
or those threads' notes. Their `after R1`, `after R3` and `after R8` worklist
entries are checked like any other entry.

## Worklist sections that no pass owns

### Comments in build inputs

All seven corrections are in source at `62d1c3d0`, so none of them requires
a rebuild.

| Location | Claims | Carried by |
| --- | --- | --- |
| `pw_probe_runner.c`, flow step 4 | DT-45.a | `0cbdb557` (R1) |
| `pw_probe_runner_abi.h`, `apply_rc` | DT-45.a | `0cbdb557` (R1) |
| `CWorker.swift`, the cleanup-trigger sentence | DT-120.d | `a887c986` (R13) |
| `CWorkerDisposition.swift`, plan resolution | DT-43.a | `cb00a2bd` (R9) |
| `PWRunnerLifecycleEvidence.swift`, `PWHostWait` | DT-44.a1 | `c82a1dd6` |
| `PWRunnerPathEvidence.swift`, form comment | DT-109.c | `c82a1dd6` |
| `PWRunnerPredictionEvidence.swift`, join comment | DT-50.c, DT-131.d | `cb00a2bd` (R9) |

### Records

- **CL.5.** The CONTRACT-tracing scratch directory has a row in the
  management plan's evidence-availability table, added beside this file. It
  was absent when checked on 2026-11-19.
- **Import and receipt association** (U1.o1 and related claims) and **reader
  population** (ACC-LIM.b, DT-53.t8, DT-53.t9, DT-132.c). `DISPOSITIONS.md`
  records both, under "Both unnumbered investigations" and DT-53/132/135. No
  further edit is needed.

### Items the product threads carry

Each pass's per-entry check covers this table. For each item, confirm that it
landed with its ruling, and do not write it twice. The R9 row's open question
was decided in `cb00a2bd`: worker-slot identity joins use the byte rule.

### Outside-the-review notes

| Note | Status at `62d1c3d0` | Assigned |
| --- | --- | --- |
| Read rule's entry list | Still omits three users of the loader | Part 1, above |
| `runner validate` counts an inaccessible executable as missing | `Path::exists` still decides | Statement: Part 1, above. Behavior: maintainer-judgment outflow |
| `docs/ARCHITECTURE.md` and `docs/LIMITS.md` route receipt provenance to the frozen guide, while RESPONSE holds the complete statement | Not rechecked | No edit, since no recommendation requires the rearrangement. Carry to the guide rewrite through the maintainer-judgment outflow |
| `docs/build.json` has no refusal row for any derivation refusal other than R3's | Not rechecked | Maintainer-judgment outflow, unassessed |
| `tests/lib/native_sources.py`, `fixture_inputs.py` and `receipts.py` discard listing errors | Not rechecked | Maintainer-judgment outflow, unassessed |
| The consumer's order chain also requires `arrival_observed` | Still required (`tests/lib/consumer.py`) | Maintainer-judgment outflow, unassessed |
| Reply `sandbox_check.operation` spelling | Settled by R9: `cb00a2bd` returns the submitted bytes | None |
| Consumer admission of `actor_policy_checks` captures (pass K) | The consumer now requires `unfollowed_imports` inside them (`227e5fc2`); whether that settles the question was not assessed | Maintainer-judgment outflow |
| `formNames` in `PWRunnerPathEvidence.swift` has no reader | Still no reader in the tree | Maintainer-judgment outflow; removal changes a build input |
