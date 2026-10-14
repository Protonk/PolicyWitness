# runner_filter_local_name

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

Exercises `(mach-lookup, local_name)` with a policy containing a local-name
deny for `com.apple.logd`. The prediction is explicitly unavailable, while
the worker's `bootstrap_look_up` attempt must complete with `outcome: ok`
and `rc: 0` on this test host. That attempt uses a global-name lookup; it is
not a positive local-name enforcement control. The capability exclusion's
limits and the open empirical mapping gate are recorded in
[VERIFICATIONS.md](../witness_contract/harness/VERIFICATIONS.md). The
[exploratory harness](../witness_contract/harness/verify_local_name.sh) retains
raw evidence for future investigation; this suite checks PW's conservative
behavior, not the native mapping question.

## Shared filter contract

The suite calls `tests/lib/unavailable_prediction.py` with its step ID,
operation, filter value and the `mach_lookup_allowed` attempt contract, as the
other `runner_filter_*` suites do with theirs. The adapter requires an
unavailable prediction (`rc=-1`, null `filter_type_id` and `errno`, the
`query_plan:prediction_unavailable_pair` limitation, `order: unestablished`,
and the synthetic `query_not_requested` record), a completed attempt with
`outcome: ok` and `rc: 0`, and a comparison that observes `succeeded` with a
`matched` operation relation and an `unresolved` target relation: the lookup
attempt maps to `global_name`, not the query's `local_name` (reading rule 10
of the evidence contract). The independent checker controls for every caller
run in
[runner_filter_sysctl_name](../runner_filter_sysctl_name/README.md).

## Fixtures and artifacts

`run.sh` generates the live specimen inline. Artifacts under
`<run>/suites/runner_filter_local_name/<test_id>/artifacts/` retain the
specimen, raw `run.json`, `pw.stderr`, and assertion log.
