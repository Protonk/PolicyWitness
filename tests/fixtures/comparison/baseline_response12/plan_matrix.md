# Scenario matrix as the drift removal plan stated it at verification time

The table `match_retained.py` and `match_live.py` parse: the plan's D1 scenario
matrix as of commit 7765be8, when `retained_row_match.txt` and `live_row_match.txt`
were produced (nine data columns: the prediction, the relation and order columns,
the A/I/M columns and the limitation strings that producer carried). The current
source of expectations is `../matrix.json`; the current record's rules are in
`tests/FAILURE-PROPAGATION-CONTRACT.md`, "Comparison record".

| ID | Scenario | Pred | Observation / basis | Op | Target | Order | A | I | M | Limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | allow, read succeeds | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | none | |
| S02 | deny, read EPERM | deny | permission_failure / permission_errno | matched | same | query_first | un | un | none | |
| S03 | allow, mode-000 file EACCES | allow | permission_failure / permission_errno | matched | same | query_first | un | un | none | |
| S05 | query denied path, attempt other path | deny | succeeded / completed_worker_status | matched | different | query_first | nr | un | none | `target:different_submitted` |
| S06 | query write, attempt read | allow | succeeded / completed_worker_status | different | same | query_first | nr | un | none | `operation:different` |
| S07 | absent path, both channels | unavailable | other_failure / completed_worker_status | matched | same | unestablished | un | un | none | `query_plan:path_unresolved_at_planning`, `prediction:query_not_requested` |
| S08 | compound create | unavailable | succeeded / completed_worker_status | unresolved | same | unestablished | nr | un | none | `query_plan:path_unresolved_at_planning`, `prediction:query_not_requested`, `compound_attempt`, `operation:unresolved` |
| S09 | unsupported attempt kind | allow | unavailable / no_completed_worker_result | unresolved | unresolved | query_first | na | un | none | `attempt:attempt_not_supported`, `attempt_operation_unestablished`, `operation:unresolved`, `target:unresolved`, `attempt:unsupported` |
| S10 | sysctl planning exclusion | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | na | none | `query_plan:prediction_unavailable_pair`, `prediction:query_not_requested` |
| S11 | bare `process-exec` query, spawn ok | unavailable | succeeded / spawned_child | different | same | unestablished | nr | un | none | `prediction:no_usable_verdict`, `exec_query_not_full_spawn_prediction`, `operation:different` |
| S12 | `file-read*` query | allow | succeeded / completed_worker_status | unresolved | same | query_first | nr | un | none | `broad_query_operation`, `operation:unresolved` |
| S13 | mach deny, kr=1100 | deny | permission_failure / bootstrap_permission_result | matched | same | query_first | un | na | none | |
| S14 | mach unknown service, kr=1102 | allow | other_failure / completed_worker_status | matched | same | query_first | un | na | none | |
| S15 | `process-exec*`, spawn ok, exit 0 | allow | succeeded / spawned_child | matched | same | query_first | nr | un | none | `exec_query_not_full_spawn_prediction` |
| S16 | spawn ok, child exits 1 | allow | succeeded / spawned_child | matched | same | query_first | un | un | none | `exec_result_failed_after_spawn`, `exec_query_not_full_spawn_prediction` |
| S17 | spawn of mode-000 target, EACCES | allow | permission_failure / permission_errno | matched | same | query_first | un | un | none | `exec_query_not_full_spawn_prediction` |
| S18 | spawn of absent target | unavailable | other_failure / completed_worker_status | matched | same | unestablished | un | un | none | `query_plan:path_unresolved_at_planning`, `prediction:query_not_requested`, `exec_query_not_full_spawn_prediction` |
| S19 | ordered unlink of queried path | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | after_query [S19] | `host_path_resolution_changed` |
| S20 | `process-exec-interpreter` query, binary spawn | allow | succeeded / spawned_child | different | same | query_first | nr | un | none | `exec_query_not_full_spawn_prediction`, `operation:different` |
| S21 | `local_name` query, kr=1100 | allow | permission_failure / bootstrap_permission_result | matched | unresolved | query_first | un | na | none | `query_filter_scope_unestablished`, `target:unresolved` |
| S22 | `none` filter on a file query | allow | succeeded / completed_worker_status | matched | unresolved | query_first | nr | un | none | `query_filter_scope_unestablished`, `submitted_target_unavailable`, `target:unresolved` |
| S23 | allow, `access` succeeds | as S01 | | | | | | | | |
| S24 | allow, `open_write` succeeds | as S01 | | | | | | | | |
| S25 | read of the path S19 unlinked, ENOENT | allow | other_failure / completed_worker_status | matched | same | query_first | un | un | after_query [S19] | `host_path_resolution_changed` |
| B1 | steered deny, read succeeds, ordered | deny | succeeded / completed_worker_status | matched | same | query_first | nr | un | none | |
| B2 | verdict omitted, read succeeds | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | none | `prediction:validator_no_verdict` |
| B3 | verdict omitted, unlink of queried path | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | unordered [B3] | `prediction:validator_no_verdict`, `host_path_resolution_changed` |
| B4 | validator error record | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | none | `prediction:no_usable_verdict` |
| B5 | verdict omitted, read of a path B6 unlinks | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | unordered [B6] | `prediction:validator_no_verdict`, `host_path_resolution_changed` |
| B6 | allow, ordered unlink | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | after_query [B6] | `host_path_resolution_changed` |
| B7 | allow, read succeeds (control) | as S01 | | | | | | | | |
| C1 | policy fails to compile, nothing runs | unavailable | unavailable / no_completed_worker_result | matched | same | unestablished | na | un | none | `prediction:validator_not_invoked`, `attempt:slot_incomplete`, `attempt:not_reached` |
| R | `runner_reporting_failed` | no `comparison` object and no `comparison_conditions`; both fallback levels tested in `ReplyFailureTests` | | | | | | | | |
| T | allow policy, FIFO read starts after release, then worker deadline | allow | unavailable / no_completed_worker_result | matched | same | query_first | na | un | none | `attempt:slot_incomplete`, `attempt:started_without_result` |
