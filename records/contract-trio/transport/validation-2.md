# Validation memo 2: transport pass, draft-2 revalidation

Validated: `records/contract-trio/transport/draft-2.md` against
`response-1.md`, using `diff draft-1.md draft-2.md` as the change list. HEAD is
`cc55288d`. Read-only; nothing re-executed. `validation-1.md` is untouched.

## 1. Each response-1 change in draft-2

### R1. C1 (host refusal citation): resolved
- draft-2 TR-5 now cites `PWRunnerRequest.swift` 127–132, with siblings at 138
  and 141. Source: line 127 decodes `actors`, 132 throws `exclusive_plan_forms`
  at `["policy"]`. No new overstatement.
- Classification: supported.

### R2. C2 (admitted-other credit): resolved
- TR-1 now credits d1 for the admission-refusal row and
  `c/baseline0_bad_request_envelope.json` for admitted-other, and states that
  the ordinary baseline is `finished`/0. This matches what I saw in the
  envelope (accepted, invoked, host `bad_request`, run `bad_request`/1).
  Calling it the "first actor-form baseline" is consistent with the file name
  and request used.
- Classification: supported.

### R3. C3 (unsaved aftermath): resolved, with a withdrawal that is correct
- Each aftermath statement now says whether it is saved in `kill_log.json` or
  was seen at the terminal, with time and command. Saved: post-kill host gone,
  worker (parent 1), `sh` and `sleep` present (my reading of `kill_log.json`
  matches). Terminal-only: the 14:48:43 `ps -p 71750,71752,71753` check and the
  d2 `ps -p 43112` check. The draft says the only record is the transcript.
  These remain unverifiable by me; they are now honestly labelled.
- The `ps -p <pid>` check matches by PID, so absence of those PIDs is a valid
  inference regardless of argv.
- Withdrawal: `kill_log.json` `chain_found` records the worker command as
  `pw-probe-runner --shm-fd 3 --ready-fd 4 --step-count 1 --proceed-wait-ms
  60000` (bare name) and the host as a full path. So a pattern
  `PWRunner\.xpc/Contents/MacOS/(pw-probe-runner|PWRunner)` could match a host
  but not a worker. The withdrawal is correct and draft-2 now states that
  nothing is established about the d2 worker. I cannot see the original
  pattern (not saved), so I rely on the draft's account of it; the argv fact is
  checked.
- The d2 table cell ("Seen at the terminal, not saved") is consistent with the
  prose.
- Classification: supported (unsaved items labelled; remaining limit below).

### R4. C4 (steps 3 and 4): resolved
- Answer 2 now lists host-frame refusal (a) and non-reply terminal (b) as
  alternatives under one step and cites runner_client.rs 478–481; the table
  carries a note that the four rows are alternatives. The claim "`failure()`
  tests (a) first (623–634)" matches source (the `runner_reply_error` block
  precedes the terminal match). The note's within-host-frame order (truncation
  before decode; fingerprint before contract) matches `parse_runner_client_output`
  and `decode_bound`. Steps renumbered to 4 (geometry then labels), consistent
  with `admission_problem`.
- Classification: supported.

### R5. C5 (B5a): resolved
- C class now lists verbatim, same-length substitution, truncation (B5a only)
  and construction; the B5a cell says "r1 truncated by one byte". Matches
  `captures.json` (3236 bytes, "r1 minus its last byte"). B2/B3/B5b/B5c are
  same-length edits; B1 and B6 verbatim; B4 constructed.
- Classification: supported.

### Other changes checked (no new overstatement found)
- Platform line: not independently checked (`sw_vers` output not saved). The
  `.tmp` build log shows 25G241 (also in the helper envelopes'
  `macos_build_version`), consistent.
- Timing correction: see section 2.
- `ba483826` rationale: quotation now attributed to the commit message, with
  two further citations (guide line 110 at that commit, `run_flow.rs` module
  comment). I confirmed the commit message text in validation-1; I did not
  re-open the other two locations this round.
- "Fallback in production has never accompanied..." scoped correctly; the
  consumer fixtures remain the exception TR-3 item 4 describes.
- Cost sentence on `policy_check`: now "a present `policy_check` implies only
  `submission: invoked`; an absent one says nothing (d2 invoked, none)".
  Supported by d2 (invoked, `policy_check` null) and TR-4's eligibility rule.
  The closing sentence ("adds nothing about possible execution beyond the
  submission state") is a design judgment and is labelled as the cost
  judgment.
- ARCHITECTURE 462–466 vs README 232–234 quotations now separate. README wording
  ("assembles the dossier, transport, ... diagnostics") and ARCHITECTURE
  ("assembles the execution records") match the lines I read in validation-1.
- Diagnostics-key sentence: `tool_error` (run_flow 154–164) and the
  `execution_only` call in `run` (~715) build the null execution records; the
  statement "follows from source" is accurate for those rows. I did not check
  the claim "`RunData` has no skip rule".
- Session 223–252 / 248–252 / 251–252: `reservationReply` begins at 223;
  `phase = .submitted` 250, `invoked` recorded 251, `submit` 252. Correct.
  Session test control "proxy failure during submission" exists at
  `runner/Tests/PWRunnerClientSessionTests/main.swift` 158.
- Dispositions that are judgments (Q5 "no further dependency... a judgment from
  this trace") are now labelled as such; supported.
- Classification: supported.

## 2. Withdrawal and timing correction against `c/kill_log.json`

- Event times relative to `controller_started`: `chain_found` 0.163 s,
  `sigkill_sent` 0.186 s, `controller_exited` 0.205 s, post-checks 0.227 s.
  draft-2: signal 0.19 s after launch, exit 19 ms after the signal, 0.21 s
  after launch. Correct to rounding (0.186, 0.019, 0.205). draft-1's "exited 0.2
  s later" was loosely worded and is fixed.
- "In that interval it ran both helper calls": the envelope holds both
  `policy_check` and `actor_policy_checks`, and fallback can only run after the
  `xpc_error`, which followed the signal; supported by inference from the
  envelope (no helper timestamps are saved).
- Worker argv: bare `pw-probe-runner ...`, confirmed. Withdrawal: correct.
- "Saved: host gone, worker, sh and sleep present": confirmed against the three
  post-check events and `nonce_children`.
- The added statement "`kill_log.json` records the nonce-carrying `sh` as W's
  child, before and after the signal": `chain_found` shows the nonce process
  (71752) with ppid 71750, and the post-check shows it still present with the
  same ppid 71750 (not a subsequent re-parenting check of the same field except
  via the `nonce_children` row). Supported.
- Baselines list: `single_baseline_envelope.json`, `baseline_envelope.json` and
  `baseline0_bad_request_envelope.json` all exist in `c/`. I did not open the
  first two to confirm `sleep 1` or `finished`/0 or the "1.1 seconds"; the
  sleep and timing statements for them are unchecked.
- Classification: supported (baseline detail unchecked).

## 3. Empty-reply path citations and the NSXPC inference

- `PWRunnerClientSession.swift` 260–262: `isResult` branch stores
  `PWRunnerReplyCapture(data)` and completes `"runner_reply"` with no length
  check (the `guard`s at 258–259 test phase, attempt id, clock and deadline
  only). Correct.
- `PWRunnerTransport.swift` 163–168: `init(_ data:)` sets `bytes_received`,
  `bytes_retained = held.count` and `truncated = held.count != data.count`, so
  0, 0, false for empty data. Correct.
- `main.swift` line 30: `exit(capture.terminal == "runner_reply" ? 0 : 1)`.
  Correct.
- `runner_client.rs` 478–481: presence by `Option` (`runner_reply.is_some() ==
  (terminal == "runner_reply")`). 575–587: retention requires nonnegative counts,
  `retained == received.min(cap)`, `truncated` consistent, and `data.len()`
  equal to `bytes_retained`; all hold at zero. Correct.
- `porcelain.rs` 179–181: `data.len() < 36` returns `Malformed("invalid
  porcelain frame")`. Correct (line 180 in my read; within the cited span).
- `arbitrary_rejected_host_bytes_survive_and_do_not_become_claims`: its first
  case is `vec![]` built through `capture(...)`/`parse`, asserting accepted
  admission, `malformed_runner_response`, no fallback and retained empty data.
  Matches the draft's description; that is a constructed-capture test of the
  parser, not a native empty reply.
- The host side (`PWRunnerService.swift` 123–155 and the comment at the empty
  fallback "an empty receipt is explicitly undecodable by the client/controller")
  matches the draft's description of the writer chain and the line 154 `Data()`.
- The NSXPC inference is explicitly labelled ("Inference, not observed") and
  the draft says no path reaching the empty writer was executed. The earlier
  assertion in draft-1 ("Empty bytes therefore reach the client as a
  `runner_reply` capture of length 0") is replaced by this staged account.
  The retained sentence "this is the one native route to malformed host bytes
  from a well-behaved client" is a reachability claim that depends on the same
  unverified inference and on the absence of other routes; it is stated as a
  route that was "not exercised", but is not itself marked inference.
  Classification: supported with a caveat.

## Unresolved limits

- The terminal-only checks (14:48:43 `ps`, d2 `ps -p 43112`, the d2 pattern
  itself) have no saved witness; they are now correctly labelled. The d2 pattern
  text is taken from the draft.
- Not re-opened: the guide line 110 and `run_flow.rs` module-comment quotations
  of `ba483826`; the `sleep 1` / "1.1 seconds" baseline details; `RunData` skip
  rules; `sw_vers` output.
- No tests or binaries were run.

## Counts

- Resolved, supported: 5 (R1 to R5) and the other listed changes, 1 group.
- Supported with a caveat: 1 (empty-reply path: the "one native route" sentence
  rests on the unverified NSXPC inference and is not itself labelled).
- New overstatements, incorrect citations or unsupported claims found: 0.
