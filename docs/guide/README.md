# `docs/guide/`

[PolicyWitness.md](PolicyWitness.md) is the user guide draft. [USER-GUIDE-PLAN.md](USER-GUIDE-PLAN.md) carries its review and the investigations behind it.

## Worked cases

Each worked case starts from a specimen the app prints, changes named fields with `/usr/bin/jq`, and states a relationship among the reader's own runs. A reader can rerun it with the shipped app. The shell blocks run in order in one Terminal window with `PW` and `PW_WORK` set. Later blocks read files that earlier blocks wrote: the handoff copies the first read's `read.json`, and the phase case starts from the repair case's `create-repaired.json`.

| Section | Starts from | Changes | Reads | What the reader sees |
| --- | --- | --- | --- | --- |
| Run your first specimen | `example`; `test-input read --target` on a file holding `first\n` | Nothing | `steps[0].attempt.fresh_read.content_hex` | `66697273740a` |
| Repairing a refused specimen | `test-input read --target` on an absent `notes` | Prepends a copy of the read step with `sandbox_check.operation` `file-write-create` and `attempt.action` `create_fresh`; then `probe_plan[0].step_id` | `result.normalized_outcome`, `data.request_failure`, the file | `bad_request` with `duplicate_step_id` at `probe_plan`, `1`, `step_id`, and no file. After the repair, a one-byte file. |
| Why couldn't my app open this file? | `test-input read --target` on `report` | `policy.sbpl_source`: `(deny default)`, then with one `file-read-data` literal | `steps[0]`: `attempt.outcome`, `attempt.errno`, `sandbox_check.outcome`, `comparison.limitations` | Absent file: errno 2 and `query_plan:path_unresolved_at_planning` under both policies. Present file: errno 1 with `deny`, then success with `allow`. |
| Handing a run to someone else | A copy of `read.json` | The document's bytes | `shasum -a 256`, `data.specimen.request_sha256`, `content_hex` | One digest for both files and both results; `66697273740a`, then `7365636f6e640a` |
| Choose the operation and the phase | `create-repaired.json`, after removing `notes` | `probe_plan` split into `create` and `read` phases; run twice | Each step's `attempt.errno`, `sandbox_check.outcome`, `content_hex` | One phase: no prediction for either step. First phased run: the read is predicted `allow`. Second: the create fails with errno 17 beside `allow`, and the read returns `78`. |
| Deciding whether to repeat a run | `test-input read --target` on an absent `late` | `step_id`, `sandbox_check.operation`, `attempt.action`; `test-input run --worker-pre-ready-hang-ms 5000 --timeout-ms 1000` | `result.normalized_outcome`, `data.runner_client.submission`, the file before and after `sleep 8` | `xpc_timeout`, `invoked`, no file, then a one-byte file |

The external-runner commands and the compiled-profile capture are procedures without a claimed result. The extension passage describes its experiment without a runnable specimen.
