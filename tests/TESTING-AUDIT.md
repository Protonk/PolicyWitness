# Testing audit — bounded measurement

## Task and required output

Measure what the specimen-isolation checker accepts when one field of a saved
**denied file attempt** changes. Report observations, not judgments about whether
accepted changes are bugs. Do not review other code paths or propose fixes.

**Write your full results into this file, `tests/TESTING-AUDIT.md`, under
`Measurement results`.** Preserve this prompt. Include every measured case,
not only surprising results. Your final chat response should briefly state
completion or blockage and link to this document.

## Fixed subject and inputs

Import `tests/suites/runner_specimen_isolation/check.py` with `importlib.util`
and call only `envelope_errors(envelope, witness)`. Do not run its `main`, launch
PolicyWitness, invoke the suite runner, build fixtures, or observe live processes.
This is an offline experiment over JSON already on disk.

Measure the **working-tree checker, including the uncommitted errno fix**.
Do not substitute its older committed version. Expected checker SHA-256:

```text
df84bee9a60020ad600150cb3e9e703b24db917f3aac1291e1f77f5bf96aefcb
```

HEAD when this prompt was prepared:
`e31f4104ff68c149b32a8899dcc7184ddcbb7d70`.
Record actual HEAD, checker hash, and relevant working-tree differences.
Check the checker hash before and after measurement. If it differs from the
expected hash, stop and report the mismatch; do not reset or edit the checkout.

Use only run A from this capture root:

```text
tests/out/isolation_errno/live/suites/runner_specimen_isolation/overlapping_runs_keep_evidence_separate/artifacts/A/
```

Load `run.json` as the original envelope, `specimen.json` as the request, and
`processes.json` as the independently recorded process identities. Construct
this fixed witness from those inputs:

```python
witness = {
    "label": "A",
    "allowed_index": 0,
    "specimen": request,
    "processes": processes,
    "marker": request["probe_plan"][0]["attempt"]["args"][1],
}
```

Do not derive the witness from the returned envelope. The old specimen's
filesystem targets need not still exist: the checker compares their recorded
names and does not perform the operations again.

The sole mutation target is:

```python
envelope["data"]["runner_result"]["steps"][2]["attempt"]
```

Confirm that this is the request's second file step, that its `step_id` matches
`request["probe_plan"][2]["step_id"]`, and that its baseline outcome is
`open_failed`. Its nine keys must be:

```text
errno, error, exit_code, normalized_path, observed_path,
outcome, rc, requested_path, syscall_errno
```

If an input is missing, has an unexpected shape, or the unchanged baseline
returns errors or raises an exception, stop and document the limitation. Do not
repair the input or generate a replacement with a live run.

## Exact experiment — 24 mutations and two baseline checks

1. Confirm the original envelope returns an empty error list.
2. For each of the nine keys above, delete that key: **nine cases**.
3. For each key whose original value is non-null, replace it with JSON null:
   **seven cases**. The original `normalized_path` and `observed_path` are
   already null; do not count unchanged copies as mutations.
4. For each original numeric field (`errno`, `exit_code`, `rc`,
   `syscall_errno`), replace its value with JSON `true`, then JSON `false`:
   **eight cases**. These must be booleans, not the numbers 1 and 0.
5. Confirm the original envelope still returns an empty error list and that
   neither the original inputs nor the witness changed.

Every mutation starts from a fresh deep copy of the original envelope and
changes exactly one field of the target attempt. Keep step identity, other
steps, predictions, subprocess metadata and the witness intact. Do not combine
mutations or expand to other fields, steps or specimens.

Classify each invocation mechanically:

- **Accepted:** the checker returns an empty list.
- **Rejected:** the checker returns a nonempty list of diagnostic strings.
- **Exception:** the checker raises; record exception type and message. Do not
  count a crash as successful validation.
- **Unexpected return:** any other return shape; record it separately.

Continue through the bounded case list after a per-mutation exception. Stop
for broken setup or changed source. No speculative explanation is required.
An accepted deletion may concern an optional field; a rejected change may be
caught indirectly. Leave significance and remediation to the owner.

## Files to create and effort boundary

Edit only this document among repository source and documentation files.
Create a fresh directory `tests/out/testing-audit/measurement-01/<run-id>/`
without overwriting earlier output. Put these files there:

- `measure.py`: the single reproducible measurement script.
- `inputs/run.json`, `inputs/specimen.json`, `inputs/processes.json`: exact copies
  of the three saved inputs; retain their SHA-256 hashes.
- `inputs/check.py`: an unchanged snapshot of the checker for provenance. Import
  the original repository module, whose relative imports resolve correctly;
  the snapshot is evidence, not a relocated implementation.
- `cases/<field>.<mutation>.json`: the full envelope supplied in each of the
  24 cases. Use mutation names `delete`, `null`, `true`, and `false`.
- `results.json`: all 26 invocation records, including baseline checks, input
  paths, field/mutation, original value and type, classification, and the full
  returned diagnostics or exception details. Include source/input hashes.
- `run.log`: the script's stdout/stderr and exit status.

Set `PYTHONDONTWRITEBYTECODE=1` when running the script. One script invocation
should perform the entire bounded measurement. Correct setup errors only as
needed to run it; describe any retry. Do not add a framework, change checker or
fixture code, commit, launch agents, run additional audits, or inspect production
implementation to explain acceptances. If the measurement cannot be completed
within the turn, report the completed cases and the exact remaining work.

## Measurement results

Auditor: Claude Opus 5 (1M context), session
`https://claude.ai/code/session_013qeETCCJA1tmbMGQupDFSF`.

Actual HEAD, checker hash before/after, and relevant working-tree differences:

- HEAD: `e31f4104ff68c149b32a8899dcc7184ddcbb7d70`, matching the prompt.
- Checker `tests/suites/runner_specimen_isolation/check.py`, SHA-256
  `df84bee9a60020ad600150cb3e9e703b24db917f3aac1291e1f77f5bf96aefcb` **before**
  and **after** the measurement — identical to the expected hash, so the
  working-tree version including the uncommitted errno fix was measured and the
  source did not change during the run.
- Nine tracked files carry uncommitted changes: `tests/README.md`,
  `tests/lib/unavailable_prediction.py`, the three `runner_filter_*/run.sh`
  files, `runner_filter_sysctl_name/{README.md,checker_controls.py}`, and
  `runner_specimen_isolation/{README.md,check.py}`. Only the last is the subject
  here. `tests/TESTING-AUDIT.md` is untracked. No tracked file other than this
  document was edited.

Input hashes and artifact directory:

Artifacts are in `tests/out/testing-audit/measurement-01/20260914-m1/`, a fresh
directory; the existing `batch-01/` and `batch-02/` output was not touched.

| File | SHA-256 |
| --- | --- |
| `inputs/run.json` | `d34466d5e52f47a3352e4a486f41d74a5e1ecaa722fb7924a5e71ef38385288f` |
| `inputs/specimen.json` | `26f7ffc3b681c24c275401e5ec0e9788e3926ff882597feb21f7f4753e5e0b7d` |
| `inputs/processes.json` | `c1cc1972b39c95b07d5c1c0391491246bd4db0695817c878e9541dd4e4b5a561` |
| `inputs/check.py` (provenance snapshot) | `df84bee9a60020ad600150cb3e9e703b24db917f3aac1291e1f77f5bf96aefcb` |

The three inputs were copied from
`tests/out/isolation_errno/live/suites/runner_specimen_isolation/overlapping_runs_keep_evidence_separate/artifacts/A/`.
The snapshot is byte-identical to the live checker; the measurement imported the
repository module itself with `importlib.util.spec_from_file_location`, so its
`fixtures/exec` and `lib` imports resolved normally, and called only
`envelope_errors`. `main` was not run, and no PolicyWitness process, suite
runner, fixture build or live process observation was involved.

Exact command, exit status, and any setup retries:

```sh
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  tests/out/testing-audit/measurement-01/20260914-m1/measure.py
```

Exit status 0 (`run.log`). Two retries, neither affecting measured values:

1. The first invocation aborted in the shell wrapper, not the script: zsh
   reserves `status`, so `status=$?` failed after the script had already run. The
   output directory was cleared and the script re-run under a different variable
   name.
2. `results.json` recorded `"head": null`, because the first version of the
   script had no HEAD lookup. A `git_head()` helper that reads `.git/HEAD` (no
   subprocess) was added, the case and result files were deleted, and the script
   was re-run from scratch. All 24 classifications were identical across runs.

`sys.dont_write_bytecode` was `True` in the recorded run, and no `__pycache__`
entries were created under `tests/fixtures/exec/` or `tests/lib/`.

Baseline checks and confirmation that inputs/witness stayed unchanged:

- Opening baseline: the unmodified envelope returned an empty error list
  (**accepted**).
- Closing baseline, after all 24 mutations: still **accepted**.
- Target confirmed before mutating: `steps[2].attempt` has `step_id`
  `fb60abfabe4e8b5f`, equal to `request["probe_plan"][2]["step_id"]`; baseline
  `outcome` is `open_failed`; its key set is exactly the nine specified keys.
- After the run, all three input files re-hashed to their original digests, their
  re-parsed contents equalled the frozen deep copies, the in-memory original
  envelope was unchanged, and the witness dict was unchanged. Each mutation
  operated on a fresh `copy.deepcopy` of the original envelope.

Counts by classification, accounting for all 24 mutations:

| Classification | Count |
| --- | --- |
| Accepted | 12 |
| Rejected | 12 |
| Exception | 0 |
| Unexpected return | 0 |
| **Total** | **24** |

By mutation kind: deletions 5 accepted / 4 rejected (9); nulls 3 accepted /
4 rejected (7); booleans 4 accepted / 4 rejected (8).

### Full case table

Baseline values of the target attempt: `errno` `1`, `error`
`'open(O_WRONLY|O_TRUNC): Operation not permitted'`, `exit_code` `1`,
`normalized_path` `null`, `observed_path` `null`, `outcome` `'open_failed'`,
`rc` `1`, `requested_path` `'/private/tmp/pw-overlap-f_u2djs9/A/fdae653224d4d3d5'`,
`syscall_errno` `1`.

Two diagnostic shapes recur below and are abbreviated:

- **D1** — `A: step fb60abfabe4e8b5f: denied attempt lacks failure/permission
  errno: {…}`, where `{…}` is the whole mutated attempt dict.
- **D2** — `A: step fb60abfabe4e8b5f: missing syscall_errno`.

Every row's untruncated diagnostics are in `results.json` under `records`, and
the exact envelope supplied is in `cases/<field>.<mutation>.json`.

| # | Field | Mutation | Original type | Original value | Classification | Diagnostics / exception |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `errno` | delete | int | `1` | Accepted | — |
| 2 | `error` | delete | str | `'open(O_WRONLY…permitted'` | Accepted | — |
| 3 | `exit_code` | delete | int | `1` | Accepted | — |
| 4 | `normalized_path` | delete | NoneType | `null` | Accepted | — |
| 5 | `observed_path` | delete | NoneType | `null` | Accepted | — |
| 6 | `outcome` | delete | str | `'open_failed'` | Rejected (1) | `A: step fb60abfabe4e8b5f attempt outcome: expected 'open_failed', got None` |
| 7 | `rc` | delete | int | `1` | Rejected (1) | D1 (attempt shown without `rc`) |
| 8 | `requested_path` | delete | str | `'/private/tmp/pw-overlap-f_u2djs9/A/fdae653224d4d3d5'` | Rejected (1) | `A: step fb60abfabe4e8b5f requested_path: expected '/private/tmp/…/fdae653224d4d3d5', got None` |
| 9 | `syscall_errno` | delete | int | `1` | Rejected (2) | D2, then D1 (attempt shown without `syscall_errno`) |
| 10 | `errno` | null | int | `1` | Accepted | — |
| 11 | `error` | null | str | `'open(O_WRONLY…permitted'` | Accepted | — |
| 12 | `exit_code` | null | int | `1` | Accepted | — |
| 13 | `outcome` | null | str | `'open_failed'` | Rejected (1) | `A: step fb60abfabe4e8b5f attempt outcome: expected 'open_failed', got None` |
| 14 | `rc` | null | int | `1` | Rejected (1) | D1 (`rc: None`) |
| 15 | `requested_path` | null | str | `'/private/tmp/pw-overlap-f_u2djs9/A/fdae653224d4d3d5'` | Rejected (1) | `A: step fb60abfabe4e8b5f requested_path: expected '/private/tmp/…/fdae653224d4d3d5', got None` |
| 16 | `syscall_errno` | null | int | `1` | Rejected (1) | D1 (`syscall_errno: None`) |
| 17 | `errno` | true | int | `1` | Accepted | — |
| 18 | `errno` | false | int | `1` | Accepted | — |
| 19 | `exit_code` | true | int | `1` | Accepted | — |
| 20 | `exit_code` | false | int | `1` | Accepted | — |
| 21 | `rc` | true | int | `1` | Rejected (1) | D1 (`rc: True`) |
| 22 | `rc` | false | int | `1` | Rejected (1) | D1 (`rc: False`) |
| 23 | `syscall_errno` | true | int | `1` | Rejected (1) | D1 (`syscall_errno: True`) |
| 24 | `syscall_errno` | false | int | `1` | Rejected (1) | D1 (`syscall_errno: False`) |

`normalized_path` and `observed_path` were already `null` in the baseline, so
they have no `null` row, and no field other than `errno`, `exit_code`, `rc` and
`syscall_errno` was numeric, so no other field has `true`/`false` rows. That
gives 9 + 7 + 8 = 24 rows.

Grouping the same data by field: `errno` and `exit_code` were accepted under all
four mutations applied to them (delete, null, true, false). `error`,
`normalized_path` and `observed_path` were accepted under every mutation applied
to them. `outcome` and `requested_path` were rejected under both mutations
applied to them. `rc` and `syscall_errno` were rejected under all four, and
`syscall_errno` was the only field whose deletion produced two diagnostics rather
than one.

### Limits or incomplete work

The bounded case list was completed: 24 mutations plus both baseline checks, all
classified, with no exceptions and no unexpected return shapes, and no case
skipped or retried individually.

Observations bounding what these numbers cover, stated without judgment:

- The measurement covers exactly one saved envelope (run A of one capture), one
  step (`steps[2]`, the denied file attempt), and one field per invocation.
  Allowed steps, the exec step, predictions, subprocess metadata, run B, and
  combinations of mutations were outside the fixed case list and were not
  measured.
- Classification is purely on `envelope_errors`' return value. A rejection here
  records only that a nonempty diagnostic list came back; the measurement does
  not attribute it to any particular assertion, and D1 in particular is a single
  composite diagnostic that prints the whole attempt dict.
- The two retries described above re-ran the entire script from a cleared
  directory rather than resuming, so `results.json`, `cases/` and `run.log`
  reflect one complete invocation.
- Whether any accepted mutation matters is left to the owner; no accepted case is
  characterized as a defect here and no change is proposed.
