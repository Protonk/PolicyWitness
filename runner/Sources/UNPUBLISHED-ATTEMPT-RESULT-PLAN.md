# What return code can an unfinished step report?

A worker completed one open, reached a create whose result it never published, and never reached the final open. The host supplied `rc: -1` for the two incomplete attempts. A file existed afterward. What can a reader establish about each call from that envelope? [Interrupted-create study](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md) · [Result assembly](PWRunnerCore/CWorkerStepResults.swift)

1. Set the three rows beside a completed open that actually returned `-1` with errno. For each, identify slot publication, lifecycle state, result producer, recorded code, and any independently observed file effect. Preserve a collected query for the unreached open. [Publication control](../../tests/suites/witness_contract/check_killed_before_publication.py) · [Independent file samples](../../records/guide/work/evidence/creator-handoff/samples.json)
2. Render those same rows with the existing code, a null code and an omitted code. Trace the Swift record, wire encoding and Rust reader for each. Include an older saved envelope and the synthetic unsupported-action case to find where a reader assumes every attempt has an integer. [Attempt record](PWRunnerCore/PWRunnerAttemptEvidence.swift) · [Controller validation](../../controller/src/porcelain_native.rs)

Return the side-by-side rows, the reading each supports, and the compatibility cost of each representation. Keep the worker's published aggregate status distinct from the return of an individual native call.
