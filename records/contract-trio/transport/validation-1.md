# Validation memo 1: transport pass, draft-1

Validated: `records/contract-trio/transport/draft-1.md`, against HEAD
`cc55288d`. `git diff --stat 4816b0e4 HEAD -- controller runner docs tests`
shows only `tests/suites/preflight/opt_in/build_refusals.py` (one line), as the
report says. I read the whole report and the transport instructions in the
plan. I read source, git history and the saved artifacts under
`.tmp/contract-trio/transport/`. I read saved envelopes with
`tests/lib/python.sh -I`. I did not rebuild, rerun the controlled harness or
repeat the host-loss run.

## Concerns

### C1. Incorrect citation: host refusal of a non-null top-level policy
- Location: TR-5, "Whole-request call": "the host refuses a non-null one
  ([PWRunnerRequest.swift] 68–73)".
- Checked: `runner/Sources/PWRunnerCore/PWRunnerRequest.swift`. Lines 68–73 are
  `probe_plan`/`executionPhases`/`probePath`. The refusal
  (`exclusive_plan_forms`, path `["policy"]`) is at line 132, with the sibling
  refusals at 138 and 141. The behavior the report relies on (an actor-form
  request with a non-null `policy` is refused) is supported, and B4iii's note
  that the host refuses it as `exclusive_plan_forms` matches. The line numbers
  do not, though the tree is byte-identical to the one DT-42 cites.
- Classification: incorrect citation (behavior supported).

### C2. Overstated native attribution for `result.admitted_other`
- Location: TR-1, "About DT-31's interface-join evidence": "Both are reachable;
  baseline and d1 produced them natively."
- Checked: `c/`, `d/` envelopes. d1 is `xpc_timeout`/1 (admission refusal),
  which is correct. The native baseline is `finished`/0, the admitted-finished
  row, not `admitted_other` (`result.rs` 173: host label that is not
  `finished`). The only native `admitted_other` evidence is
  `c/baseline0_bad_request_envelope.json` (`bad_request`/1,
  `transport_admission` accepted, `invoked`, host reply `bad_request`), which
  the report mentions in TR-5 but does not cite here. The conclusion (the join
  list cannot separate unreachable from uncovered) still follows.
- Classification: overstated (wrong run credited for one of two entries).

### C3. Process-aftermath observations are not in the saved artifacts
- Location: TR-5, "Process aftermath" ("At 14:48:43, 20 seconds after start,
  all three were gone. No cleanup signal was needed"), and the note after the
  native table ("At 14:43:16 ... no `PWRunner` or `pw-probe-runner` process
  existed").
- Checked: `c/kill_log.json` has 9 events, ending at `nonce_children`. Its
  post-checks are the three taken immediately after the controller exited
  (host gone, worker and `sh` still present with parent 1, and the `sleep 8`
  child). A grep of the artifacts (excluding `target/`) for `14:43` and
  `14:48:43` finds nothing. The d2 and kill envelopes' mtimes (14:40:05,
  14:48:23) are consistent with the stated times. The later absence checks were
  evidently made interactively and not saved.
- Classification: unsupported by the saved artifacts (the immediate post-kill
  state is supported). The report already says d2 worker outlived-timeout is
  "not established", so only the "no cleanup signal was needed / all gone by
  14:48:43" statement needs a saved witness.

### C4. Precedence order lists two boundaries that cannot co-occur
- Location: "Answers in brief", item 2, steps 3 and 4 ("the host frame embedded
  in an accepted `runner_reply` capture; the capture's non-reply terminal"), and
  the precedence table.
- Checked: `runner_client.rs` 478–481 (`runner_reply.is_some() == (terminal ==
  "runner_reply")`) and 744–778. An accepted capture has a host frame only with
  terminal `runner_reply`. A capture with a non-reply terminal has no frame. So
  host-frame refusal and non-reply terminal are never both present, and "each
  step evaluated only if all earlier ones passed" gives no ordering between
  them. The table rows reflect this correctly. Only the numbered list implies a
  precedence there.
- Classification: supported with a caveat (steps 3 and 4 are alternatives, not
  ordered).

### C5. Evidence-class definition slightly narrower than B5a
- Location: evidence-class table, **C** ("edited at fixed lengths, or
  constructed").
- Checked: `b/captures/captures.json`: B5a is "r1 minus its last byte" (3236
  bytes), not a fixed-length edit. B2, B3a-c, B5b and B5c are same-length edits.
  Labelling of B5a as C is otherwise correct. B6 is the native r2 capture
  replayed through the scripted client, also correctly C.
- Classification: minor imprecision; labels are right.

## Claims checked and found supported

- TR-1 reachability. `git grep "RunnerClientRun {" -- controller` gives the
  parser (678), `test_client_run_bytes` (970, `#[cfg(test)]`, line 960) and
  `run_flow.rs` 4186 (inside the test module starting at 787/803).
  `RunnerClientRun`, `OutputCapture` and `RequestDelivery` derive `Serialize`
  only. No `Deserialize` appears in `runner_client.rs` or `runner_commands.rs`.
  `admit_reply` has two callers (run, verify), both fed by
  `run_pw_runner_client`. `failure()` returns `None` only for accepted/no
  delivery error/no reply error/terminal `runner_reply`, and `validate_capture`
  requires a host reply iff that terminal. The "cannot occur in run or verify"
  scope is justified. `runner_response_unavailable` was introduced at
  `2d5080d7` (`git show` diff replaces `runner_output_not_json`).
- Join-list claim. `joins.json` lists `result.admitted_unavailable`,
  `result.admission_refusal` and `result.admitted_other` under
  `entries_no_case_reaches`. The generator computes it from `reaching`
  (`generate_interface.py` ~366). The interface README 128 sentence is quoted
  correctly.
- TR-2 decoder order. `porcelain.rs` `decode_bound` checks the fingerprint, then
  the producer contract, then decodes, so a bytes-decoded reply carries the
  build contract. `ReplyVersion::Unsupported` is therefore reachable only from
  typed injection. `Deserialize` for the typed records is `cfg_attr(test)`
  only. B2, B3a, B3b and B3c envelopes match the table: outcomes, error text,
  `runner_result` null except B3b (decoded record present), diagnostics key
  present and null in all four, `policy_check` null and `actor_policy_checks`
  absent (explicit key presence checked).
- TR-3 test descriptions. `each_result_class_agrees...` (3626ff) has the quoted
  comment at 3656, the typed-reply-beside-refusal rows, the delivery-failure
  row, the no-host-reply row, and asserts only outcome, ok, exit and card.
  `refused_reply_versions...` (3016ff) has the quoted comment, asserts
  `runner_result == reply` for previous/next, null for string/missing, and the
  helper is not found beside the test binary (status `unavailable`). The
  consumer controls use an `xpc_error` `runner_result` with terminal
  `runner_reply` (blackbox.py skeleton). The actor controls in
  `checker_controls.py` are in `diagnostic_subject_controls`, not
  `policy_check_controls`. `tests/lib` and `tests/suites` contain no
  `actor_policy_checks`. ARCHITECTURE B9 and T12 text match the quotes.
- TR-4 disjointness. `fallback_eligible` requires terminal `xpc_error`;
  `failure()` returns `None` only for `runner_reply`, so the Admitted-branch
  fallback calls (run_flow 699–701) cannot run for any value. `validate_capture`
  requires `invoked` and stage `submission` for `xpc_error`. The Swift session
  emits `xpc_error` only in `connectionFailed` during `.submitted`
  (`PWRunnerClientSession.swift` 192–197). `invoked` is recorded before
  `submit` (244–253). The client never uses reasons `interrupted` or
  `invalidated`; `git grep` finds no use in `runner/Clients` or
  `runner/Sources` (only host handlers and comments). `xpc_error` appears in no
  `runner/Sources` file.
- History. `34496c0f` (2026-10-29), `29e3ead0` (2026-10-05, first adds the
  "yields a synthetic `xpc_timeout` reply" ARCHITECTURE sentence per `git log
  -S`), `ba483826` (2026-06-11, message contains the quoted rationale),
  `4e02cf51` (2026-10-03). At `29e3ead0` `fallback_policy_check` keyed on the
  reply's `xpc_error` outcome.
- TR-5 native host-loss run. `c/kill_log.json` and `c/kill_envelope.json`:
  nonce process 71752, parent worker 71750 (`pw-probe-runner`), parent host
  71748 (`PWRunner`), `host_absent_before_launch`, host only child is the
  worker, launchd client domain lists 71748, SIGKILL sent once to 71748,
  controller exited about 0.21 s later. Envelope: `xpc_error`/1, error
  "connection to service named ...", accepted/`invoked` (23 ms),
  `acquisition_stop: granted`, error stage `submission`, code 4097, control
  `host_pid` 71748, `runner_result` and `runner_sandbox_diagnostics` present
  and null, `policy_check` `tool_error`/2 with the quoted stderr (line 44),
  `actor_policy_checks` zeta `ok`/0 with hash `7a3962a7...`. The no-signal
  attempt (`kill_attempt0_no_signal_*`) finished/0.
- d1 and d2. d1: `xpc_timeout`/1, `not_invoked`, stage `acquisition`, zero
  attempts, `acquisition_stop: overall_deadline`, keys present and null,
  `actor_policy_checks` absent. d2: `xpc_timeout`/1, `invoked` (29 ms), stage
  `submission`, `policy_check` null, control `host_pid` 43112.
- TR-5 helper behavior. `sbpl-check.rs` `CheckRequest { policy }` is required,
  and decode failure exits 2 with "failed to parse request.json"; `a/` stderr
  files show the missing-field and null-policy messages;
  `policy_check.rs` maps empty stdout to `tool_error` and `code().unwrap_or(1)`.
  B4i, B4ii, B4iii, B4s and B4u envelopes match the table: statuses, exit codes,
  per-actor order and labels (B4iii dossier `future`, null, `scalar`,
  `unapplied_with_policy` against three checks), signal-killed helper recorded
  as `tool_error`/1 with empty stderr, absent helper `unavailable`/1.
- TR-5 tests. `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`
  (3237ff) returns `Err` for helper call index 0 and asserts
  `policy_check.status == "unavailable"` with inputs held string, then zeta,
  then alpha. `actor_fallback_uses_held_policy_objects_before_host_mode_admission`
  (3113ff) uses a controlled helper. `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`
  (2040ff) contains no actor input.
- TR-6/B7/B8/B9. The scripted client
  (`b/app/.../pw-runner-client`) is the investigator's shell script
  ("Not the shipped client"), so C labels are accurate. `make_captures.py`
  copies r1 root fields with tag at most 12 verbatim and adds tags 13 and 14.
  B7: `tool_error`/2, error after 65536 bytes, `delivery_failed`, `unknown`,
  transport `Rejected` (base64 length matches the 782-byte capture), `policy_check`
  null. B8 and B9 envelopes (finished/0 with mismatched actor request and
  exit-code 1 recorded) match summary values.
- TR-7. `stdout_parse_error` is set only in the decode-failure arm;
  `stdout_capture_error` forces `Err("malformed")` (runner_client.rs 708–710,
  724); B5a/B5b carry it and B5c does not. `reply_capacity` and `reply_geometry`
  occur only in `porcelain_admission.rs` within `controller` and `tests`.
  `pwRunnerReportData` falls back through rich, minimal and empty `Data()`.
  RESPONSE 243 and 254 and README 184–190 and guide 1409 quotes are accurate.
  `fallback_eligible` and `reply_contract` match the described behavior.
- Cross-references. DT-42's "none could be forced here because XPC lookup
  worked" is accurately superseded by the forced host loss. The TR-2 DT-105
  link (schema-then-contract order) is consistent with DT-105's title. DT-31 and
  DT-32 differences are preserved.

## Unresolved limits

- Not re-executed, per the boundaries: the controlled harness, the Cargo
  build, and the host-loss run. Envelope claims were checked only against the
  saved files.
- Test claims were checked by reading bodies, as the report itself did. I did
  not run any test.
- I did not check every documentation line citation (RESPONSE 89 and 252,
  guide 767–768 and 861–864, 11-policy 236/688/713, ARCHITECTURE 467 line
  placement, `PWRunnerTransport.swift` 57 which is actually 57–58) or the
  `retention_loss_precedes_decode_and_keeps_exact_prefix` and
  `arbitrary_rejected_host_bytes...` test bodies. The TR-5 negative claim that
  no statement says `policy_check` is `tool_error` for actor-form fallback was
  checked only against the passages quoted above, not by an exhaustive search.
- The report's SHA-256 equality of the dossier `applied_sha256` with a
  separately computed hash, the shipped-helper hash against the manifest, and
  the build-contract equality were not independently recomputed (the saved
  `build-env.txt` shows the contract; the shipped `sbpl-check` hash prefix
  `1d447028` matches).

## Counts

- Incorrect citation: 1 (C1)
- Overstated: 1 (C2)
- Unsupported by saved artifacts: 1 (C3)
- Supported with a caveat: 1 (C4)
- Minor imprecision: 1 (C5)
