# Evidence checker fixtures

Live captures of complete `run` envelopes for independent controls of the
evidence checker. The current directory is `response23/`. Each `*_run.json` is
an unmodified capture from the case named below, stamped with the build that
produced it, and each `*_specimen.json` is the exact submitted request.

- `valid_run.json` and `valid_specimen.json`: `blackbox_e2e/BBX-001`. The
  checker controls and the comparison controls start from it.
- `missing_path_run.json` and `missing_path_specimen.json`:
  `blackbox_e2e/BBX-002`, a read of a missing path. The checker controls and
  the menagerie checker controls start from it.
- `extension_run.json` and `extension_specimen.json`:
  `witness_contract/extensions`, the lifecycle artifact. The extension
  controls start from it.
- `issuer_abnormal_run.json` and `issuer_abnormal_specimen.json`:
  `witness_contract/extension_combinations`, the M01 artifact. The extension
  controls start from it, and the constructed patches in
  `../../contract/evidence_types.json` apply to it.

## Refresh

A `response_schema` bump makes the readers reject these captures, so a new
`responseNN/` set is captured, not edited. Run the four cases above against the
final candidate and copy from each case's `artifacts/` directory:

- `BBX-001`: `policy_witness.run.stdout.json` as `valid_run.json` and
  `specimen.rendered.json` as `valid_specimen.json`.
- `BBX-002`: the same two files as `missing_path_run.json` and
  `missing_path_specimen.json`.
- `extensions`: `lifecycle/run.json` and `lifecycle/specimen.json` as
  `extension_run.json` and `extension_specimen.json`.
- `extension_combinations`: `M01/run.json` and `M01/specimen.json` as
  `issuer_abnormal_run.json` and `issuer_abnormal_specimen.json`.

Specimens differ between captures only by temporary paths. Bump
`schema_version` in `../../contract/path_diagnostics.json` (one value per
case), replace `../../contract/response_shape.json` with the
`response_shape.candidate.json` that `runner_unit` writes when the golden
disagrees, and retain the capture run in `tests/RETAINED.json`. The
disposition capture ([`../../disposition/`](../../disposition/README.md))
refreshes with the same bump.
