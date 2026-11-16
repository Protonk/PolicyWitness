### Investigation identity and evidence classes

This pass traced transport failure for `policy-witness run`, from client
capture through public result selection, and the independent `sbpl-check`
fallback. It starts from DT-31, DT-32 and DT-42.

**Snapshot and build.**
- Source: `main` at `cc55288d` (2026-11-16), clean tree. `controller/`,
  `runner/`, `docs/` and `tests/` are byte-identical to `4816b0e4`, the tree
  DT-31, DT-32 and DT-42 cite, so their line numbers still apply.
- Shipped app: `dist/PolicyWitness.app`, built from `8b5de2b2` (build 1482,
  `development:bdefcb44…fb18`). Since that commit, those four directories
  differ only in `tests/suites/preflight/opt_in/build_refusals.py`.
- Platform: macOS 26.7.1, build 25G241 (`sw_vers`), Darwin 25.6.0, arm64.
  XPC lookup worked from the investigating shell.

**Cargo-built controller for controlled client runs.**
- `policy-witness` and `sbpl-check` were built from HEAD with an isolated
  `CARGO_TARGET_DIR` and `CARGO_BUILD_BUILD_DIR` under
  `.tmp/contract-trio/transport/target`.
- `PW_BUILD_CONTRACT` was set to the output of `docs/build_contract.py`,
  as `build.sh` does. That output is `development:bdefcb44…fb18`, equal to the
  app's. The built binary's `--version` reports that contract.
- The scratch app `.tmp/contract-trio/transport/b/app/` holds this
  controller and a scripted `pw-runner-client`.
- Its `Contents/MacOS/sbpl-check` is a symlink to the shipped helper, which
  ran in place. The shipped helper hashes to `1d447028…`, matching the app
  manifest.

**Evidence classes.** Every claim below carries one of these labels:

| Label | Meaning |
| --- | --- |
| **N** | Native execution of shipped binaries: the shipped controller, client, host, worker and helper. |
| **C** | Controlled client output. The Cargo-built controller read bytes written by a scripted client. The bytes were recorded from the shipped client and then used verbatim, edited by same-length substitution, truncated (B5a only), or constructed. The controller's own decoding, admission, selection and fallback all ran. |
| **T** | Typed injection in Rust unit tests. A `RunnerClientRun` or `PWRunnerRunResult` is constructed directly, bypassing production decoding. |
| **S** | Source inspection. |

**What ran, and what did not.**
- No case was run through `tests/run.sh`.
- The orchestration tests discussed below were read, not executed. The claims
  made about them concern what they construct and assert, not whether they
  currently pass.

**Artifacts.** All are under `.tmp/contract-trio/transport/` in the local
checkout. That directory is gitignored, disposable and carries no retention
guarantee. It contains:
- `a/`: helper probes.
- `d/`: shipped-controller runs.
- `captures/`: raw native captures `r1` and `r2`.
- `b/`: controlled cases, `summary.json`, and per-case envelopes under
  `b/runs/`.
- `c/`: the native host-loss run and its process log.
- `tools/`: `pwire.py`, a wire reader and writer written independently of the
  generated readers, and the case scripts.

#### Native observations

| ID | Command (shipped binaries) | Observed |
| --- | --- | --- |
| baseline | `policy-witness run --timeout-ms 3000`, ordinary request | `finished`/0. Capture accepted, `invoked`, `runner_reply`. `policy_check` key present and null. `actor_policy_checks` absent. |
| d1 | Same request with `--timeout-ms 1` | `xpc_timeout`/1, `not_invoked`, 0 attempts, `acquisition_stop: overall_deadline`, error stage `acquisition`. Keys `runner_result`, `policy_check` and `runner_sandbox_diagnostics` present and null. `actor_policy_checks` absent. |
| d2 | `_test_overrides.worker_post_apply_hang_ms: 4000`, `--timeout-ms 1500` | `xpc_timeout`/1, `invoked` (elapsed 29 ms), error stage `submission`. `policy_check` null. The control reported host PID 43112. Seen at the terminal, not saved: shortly after the run, `ps -o … -p 43112` printed no process. |
| r1 | `pw-runner-client run --request -` with the built-in service name | Client exit 0, `runner_reply` with 2,575 host bytes. Ordinary request with `capture_compiled_profile`. Saved as `captures/r1.capture`. |
| r2 | `pw-runner-client` with a nonexistent service name, `--timeout-ms 2000` | Client exit 1. 20 attempts, each `transport_error` with stage `acquisition` and reason `xpc_error`. Every attempt carries NSCocoaErrorDomain 4099 "…lookup with error 3 - No such process". Final stop `overall_deadline`, terminal `xpc_timeout`. Saved as `captures/r2.capture`. |
| (c) | Single-actor request, exec `sleep 8`; this run's PWRunner host sent SIGKILL | `xpc_error`/1. See "Native host loss" below. |

For d2, no worker PID was recorded during the run, so nothing is established
about the worker after the client's timeout. A later check was seen at the
terminal and not saved. At 14:43:16, 3 minutes 12 seconds after d2 started,
`ps -axo pid=,ppid=,lstart=,command=` filtered by the pattern
`PWRunner\.xpc/Contents/MacOS/(pw-probe-runner|PWRunner)` matched nothing.
That pattern can match a host, whose argv[0] is its full path. It cannot
match a worker: run (c) later showed that a worker's argv[0] is the bare name
`pw-probe-runner`. So the check shows only that no PWRunner host with that
path in its argv remained. It says nothing about workers.

### Answers in brief

**1. Which states can reach execution admission and result selection.**
- Every `run` envelope passes through the one selection relation.
- Execution admission (`Disposition::Admitted`) is reached only when all of
  these hold: request delivery succeeded; the current capture was accepted;
  the capture records `invoked` and terminal `runner_reply`; the complete host
  frame decoded under the current schema and contract; and the reply passed
  geometry and compiled-profile admission.
- So in the shipped command, execution admission always comes with
  `submission: invoked` and a decoded host reply. The row for an admitted run
  with no host reply (`runner_response_unavailable`) cannot be selected
  (TR-1).
- Every other combination ends in one of the refusal rows. A decoded host
  projection appears beside a refusal in only one case: the decoded reply
  fails geometry or compiled-profile admission (TR-2).

**2. Which failed boundary decides the outcome.** Precedence runs in this
order, each step evaluated only if all earlier ones passed:
1. request delivery;
2. client-capture retention, presence, decoding and semantics;
3. for an accepted capture, exactly one of two alternatives:
   - (a) with terminal `runner_reply`, the embedded host frame (truncation,
     schema, contract, structure);
   - (b) with any other terminal, that terminal itself.

   An accepted capture has a host frame exactly when its terminal is
   `runner_reply` (runner_client.rs 478–481). The two cannot co-occur, so
   neither has precedence over the other. `failure()` happens to test (a)
   first (623–634).
4. for a decoded reply, host geometry and then compiled-profile labels.

The earliest failed boundary selects outcome, error and exit. It also fixes
what is retained: rejected capture bytes, typed capture, retained host bytes,
or decoded projection. Fallback runs only for an accepted capture whose
terminal is `xpc_error` (TR-4). A combined-fault control confirmed that
delivery failure suppresses capture interpretation and fallback (B7). Other
semantic integrity findings never change the outcome; they change only the
diagnostics.

**3. Fallback: what permits it, what it receives, what it establishes.**
- It is permitted only for an accepted capture whose terminal is `xpc_error`
  and whose request delivery succeeded. The client emits that terminal only
  after it has invoked execution.
- The ordinary-form check receives the held, pretty-printed, augment-resolved
  request.
- For an actor request the host would admit, that same whole-request call
  always fails in the helper's decoder with exit 2. This was observed
  natively (TR-5).
- Each actor whose `sandbox.policy` is a JSON object gets its own policy-only
  check, whatever its mode.
- Each result establishes only that the helper's own process did, or did not,
  compile those bytes. In the native host-loss run, the worker was observed
  running its exec action while the envelope carried only fallback compile
  results.

### TR-1 — The admitted-without-host-reply row cannot be reached through either shipped caller

**Settled (S, with callers checked).**

The client-failure function returns no failure under exactly one condition. In
[runner_client.rs](../controller/src/runner_client.rs),
`parse_runner_client_output` (lines 667–794) and `RunnerClientRun::failure`
(602–650) return `None` only when all of these hold:
- there is no delivery error;
- `transport_admission == "accepted"`;
- there is no `runner_reply_error`;
- the terminal is `runner_reply`.

Under the same condition, the parser returns `Some(typed reply)`. Capture
admission requires a host reply if and only if the terminal is `runner_reply`
(478–481). An untruncated frame either decodes or sets `runner_reply_error`
(744–778).

The search for other constructors and callers:
- `RunnerClientRun` derives only `Serialize` (line 25). Its fields
  `OutputCapture` and `RequestDelivery` also derive only `Serialize` (utils.rs
  lines 15 and 102). Neither `runner_client.rs` nor `runner_commands.rs`
  mentions `Deserialize`.
- `git grep RunnerClientRun -- controller` finds three struct literals:
  - runner_client.rs line 678, in the parser;
  - line 970, `test_client_run_bytes`, which is `#[cfg(test)]`;
  - [run_flow.rs](../controller/src/run_flow.rs) line 4186, inside
    `#[cfg(test)] mod tests` (lines 788 to the end of the file).
- Its only containers are `ExecutionData` and `RunnerVerifyData`. Both derive
  only `Serialize`.
- `run_flow::admit_reply` has two callers: `run` (run_flow.rs 693) and
  `cmd_runner_verify`
  ([runner_commands.rs](../controller/src/runner_commands.rs) 612–626). Both
  take their input from `run_pw_runner_client`.

Consequences:
- `select(&Disposition::Admitted { host_outcome: None, .. })` cannot occur in
  `run`. That is the `AdmittedUnavailable` row of
  [result.rs](../controller/src/interface/result.rs).
- The no-worker assessment `execution_diagnostics(None)` cannot occur in
  `run`.
- Verify's `None` branch, which reports `runner_response_unavailable`
  (`project_verify_typed_reply`, runner_commands.rs 531–545), cannot occur in
  verify.

Statements that describe the unreachable state:
- RESPONSE lines 89, 252 and 300, and the verify rule at 3808, as DT-31
  listed.
- The shipped `policy-witness help result` card prints
  `runner_response_unavailable false 1` (N).

Only typed injections reach the label:
- `each_result_class_agrees_in_fields_process_status_and_card` builds the
  pair `(client_run(Some(&controlled_reply())), None)`.
- `execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields`
  calls `complete_execution` with no reply.
  [CONTRACT](../docs/CONTRACT.md) line 965 credits the latter to Execution
  diagnostics. The failure contract's row at line 687 describes it as
  "Constructed replies cross production assembly". `complete_execution` is
  production code; the assembler `execution_envelope` is a test helper
  (run_flow.rs 793).

**About DT-31's interface-join evidence.**
`controller/interface/joins.json` lists `result.admitted_unavailable` under
`entries_no_case_reaches`. The generator computes that list as entries no
case in the corpus `controller/integration/interface_cases.json` reaches
(`docs/generate_interface.py` 366). The interface README (117–128) describes
the join as a derivation from each case's argument vector and result fields.
For the companion list it says that it reports "a fact about the retained
cases, not a claim that production inputs cannot reach the entry."

The same list also holds `result.admission_refusal` and
`result.admitted_other`. Both are reachable natively:
- d1 selected the admission-refusal row (`xpc_timeout`/1).
- `c/baseline0_bad_request_envelope.json`, the first actor-form baseline,
  selected the admitted-other row. Its accepted, invoked capture carried a
  host reply labelled `bad_request`, and the run ended `bad_request`/1.

(The native ordinary baseline is `finished`/0, the admitted-finished row, not
admitted-other.)

So the list cannot tell an unreachable entry from a reachable one that the
corpus does not cover. The unreachability claim rests on the caller trace
above, not on the join.

**History (S).** `runner_response_unavailable` was introduced in
`2d5080d7` (2026-11-08). Before that, a missing reply fell through to
`runner_output_not_json`. This pass did not establish whether the state was
reachable at that time.

### TR-2 — A foreign producer leaves only retained bytes; the typed-version branch exists only for injected replies

**Settled for the shipped decoder (S); executed through binary decoding (C).**

`decode_bound` ([porcelain.rs](../controller/src/porcelain.rs) 174–222) reads
the host frame in this order:
1. It checks the fingerprint, returning `UnsupportedSchema` on mismatch.
2. It reads root record tag 1, `PWProducer`, and that record's tag 1,
   `contract`.
3. It compares that contract with the build contract and returns
   `UnsupportedContract` on mismatch.
4. Only then does it decode the whole frame.

The generated reader maps tag 1 to `producer` and `PWProducer` tag 1 to
`contract`. `RecordReader` rejects duplicated or out-of-order tags. So any
`PWRunnerRunResult` produced from bytes carries the current contract.

The branch `ReplyVersion::Unsupported` in `run_flow::admit_reply` (343–349)
is therefore reachable only from typed injection. So is the
`unsupported_runner_response` projection in verify.

Controlled-client results (C, `b/runs/`; capture edits made by
`tools/make_captures.py`):

| Case | Host-frame change (same length) | Result | `runner_result` | `runner_reply_error` | Retained host bytes |
| --- | --- | --- | --- | --- | --- |
| B2 | producer contract → `development:fff…` | `unsupported_runner_response`/1, error "runner reply has foreign contract development:fff…" | present, null | that message | equal to the edited frame |
| B3a | first fingerprint byte flipped | `unsupported_runner_response`/1 | present, null | "…unsupported porcelain schema…" | equal |
| B3c | reply record id 55 → 56 | `malformed_runner_response`/1 | present, null | "…not a complete typed record: wrong record identity" | equal |
| B3b | `compiled_profile.capture_stage` `before_apply` → `after__apply` | `malformed_runner_response`/1, error "compiled_profile context is inconsistent" | **decoded record present** | null | equal |

In every case the capture was accepted and `submission` was `invoked`. The
diagnostics key and the `policy_check` key were present and null, and
`actor_policy_checks` was absent.

So a decoded projection beside a refusal exists in production only for the
semantic gate `admission_problem`
([porcelain_admission.rs](../controller/src/porcelain_admission.rs)
1308–1331), which checks geometry and then compiled-profile labels.

**Statements that describe a decoded foreign record:**
- [controller/README.md](../controller/README.md) 184–190: "…or a decoded
  reply carrying another producer contract, produces
  `unsupported_runner_response` … `data.runner_result` holds the decoded
  record's projection when decoding succeeded".
- Guide line 1409: "A decoded but refused producer/context can remain there".
  The *context* half is accurate (B3b). The *producer* half is not.
- 40-envelope `admit`: "then decoded host producer identity and host
  capacity/profile-label admission". This lists producer identity as a
  separate gate after decoding.

**Error text differs by path.**
- Production foreign-contract text (B2): "runner reply has foreign contract
  X".
- The typed path's text, which `delivery_failure_takes_precedence…` asserts:
  "runner reply carries contract X; this controller reads only Y".

**A foreign host is refused earlier (S, plus one N observation).**
- In the shipped host, the control reply's contract
  ([PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
  57) and the reply producer (`PWProducer.current`,
  [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
  175–177) both read `PWBuildContext.contract`.
- Packaged builds generate that value as a single constant
  (`docs/build_contract.py` 96–97).
- The client refuses a control whose contract does not match its own as
  `unsupported_protocol`, giving terminal `protocol_error`
  ([PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
  205–216).
- In r1 the client admitted a granted control, and the embedded frame
  carried the current contract (N).
- So a host from another build is refused during acquisition, as
  `xpc_protocol_error`. The host-frame contract refusal can be reached only
  when a host's control and frame identities disagree, or when bytes have been
  altered, as in B2.
- This connects to DT-105, which examined what the fingerprint covers. The
  schema-then-contract order of the same `decode_bound` gate is what makes a
  typed foreign reply impossible. B2 and B3a reach the same public label from
  those two different checks; only `runner_reply_error` text separates them.

### TR-3 — Tests and controls that build combinations production cannot produce

These tests are T unless marked otherwise. Each item gives what the test
constructs and how that differs from production. The costs are design
judgment and are labelled as such.

1. **`each_result_class_agrees_in_fields_process_status_and_card`** (run_flow.rs 3626–3869).
   - The rows "capture missing", "capture unsupported" and "capture
     malformed", and the three reply-refusal rows, return `Some(typed reply)`
     beside the refusal. The comment reads: "The capture carries a decoded
     `finished` reply beside the refusal."
   - The refused branch passes `runner_result` into the envelope (line 715).
     Those rendered envelopes therefore carry a decoded host record beside
     `missing_runner_client` and similar refusals. Production cannot emit
     that pairing.
   - "Delivery failure beside a received finished reply" pairs a delivery
     error with a typed reply. Production cannot do this: a delivery error is
     checked first and stops all decoding (line 705).
   - "Reply contract foreign" injects a typed foreign record, the TR-2 branch.
   - "Admitted completion with no host reply" is the TR-1 pair.
   - The test asserts outcome, `ok`, exit and card line, not data presence.
     So the impossible pairings neither fail it nor are pinned by it.
   - Cost (judgment): the test reaches every card line, including
     `runner_response_unavailable`, by reaching unreachable states. A reader
     who takes coverage as reachability would be misled.

2. **`delivery_failure_takes_precedence_and_retains_the_client_frame_unread`** (1971–2037).
   - It asserts `admit_reply(&intact, None)` is `Admitted`. Here `intact` is a
     constructed capture with terminal `runner_reply`.
   - It asserts that a typed foreign record is refused with the typed-path
     message.
   - Its envelope uses a hand-built `JsonResult::new(false, 2, …)` rather
     than `select`.

3. **`refused_reply_versions_request_no_fallback_compilation`** (3016–3110).
   - The comment (3017–3024) begins: "Through production admission: a reply
     under another response version is refused before anything reads it, so
     no helper is requested and `policy_check` is null."
   - Production code it exercises: `run` and everything it calls (`admit_reply`,
     `fallback_policy_check`, `actor_fallback_checks`, `select`, rendering),
     `evidence::load_manifest`, and `run_policy_check`. The helper is never
     found beside the unit-test binary, so the fallback capture is
     `unavailable`.
   - Not production: the client dependency returns `client_run(..)`, whose
     embedded host bytes are JSON. The typed reply comes from serde
     `from_value`, which is test-only and skips `decode_bound`.
   - In the narrow sense, the comment is accurate: the label matches
     production, and nothing reads the reply before admission.
   - The gap: the "previous" and "next" rows assert
     `wire["data"]["runner_result"] == reply`, a retained typed record. For
     the same host bytes, production reports `runner_result: null` (B2).
   - The "string" and "missing" rows map fixture-reader failure to
     `ReplyRefusal::Malformed` with a null projection. That matches
     production.

4. **Consumer `policy_check_controls`**
   ([checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py)
   39ff, through `envelope_skeleton` in
   [blackbox.py](../tests/lib/blackbox.py) 54–112).
   - These controls wrap helper captures in an envelope whose `runner_result`
     has `normalized_outcome: "xpc_error"` and whose capture terminal is
     `runner_reply`.
   - Since `34496c0f` (2026-10-29), fallback in production has never
     accompanied a host reply or a `runner_reply` terminal.
   - History (S): the fixture form predates that change. `git log -S` finds it
     back to `4e02cf51` (2026-10-03). At `29e3ead0` the client synthesized an
     `xpc_error` *reply*, and fallback keyed on that reply's outcome (run_flow
     line 380 at that commit).
   - The consumer's helper-envelope admission does not depend on the outer
     state. So the control still tests that admission, and the surrounding
     envelope is a leftover from the earlier design.
   - [ARCHITECTURE](../docs/ARCHITECTURE.md) row B9 credits these controls,
     with `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`,
     for "associated with the selected policy/actor". Neither contains an
     actor or checks association. The consumer has no `actor_policy_checks`
     handling (`git grep` in `tests/lib/consumer.py`).

5. **The field-complete shape fixture** (run_flow.rs 3940–4243). It combines
   mutually exclusive fields, including both client stdout errors on an
   accepted capture, but it says so ("Field-complete shape fixture"). It
   feeds the shape golden only. It is listed here for completeness and is not
   a finding.

### TR-4 — Fallback eligibility coincides exactly with an invoked client `xpc_error`; the fallback calls on the admitted branch can never run

**Settled (S), with N and C confirmation.**

The admitted-branch fallback calls are dead code.
- `fallback_eligible` (runner_client.rs 651–661) requires an accepted
  capture, no delivery error and terminal `xpc_error`.
- For any `RunnerClientRun`, however it was built, those conditions make
  `failure()` return `Some(Refused(..))`.
- So the calls on the `Admitted` branch (run_flow.rs 699–701) cannot run for
  any value. Fallback runs only on the refused branch (715–724), with
  `runner_result` and `runner_sandbox_diagnostics` null.

`xpc_error` always means `invoked`.
- `validate_capture` requires `invoked` for that terminal (516–529).
- The Swift session emits it only from `connectionFailed` during the submitted
  phase (Session 192–197).
- With the shipped client, outcome `xpc_error`, fallback invoked, and
  `submission: invoked` therefore always occur together.

Fallback does not track whether execution may have happened.
- A native invoked timeout (d2) has the same receipt uncertainty and gets no
  fallback.
- A lookup failure never yields fallback. Lookup errors are acquisition-stage
  attempts, as r2 shows: the same NSCocoaErrorDomain error class as an
  eligible `xpc_error`, but at the acquisition stage.
- Conversely, `proxy_type_mismatch` during submission is an eligible
  `xpc_error`, yet `proxy()` returned nil and nothing was sent. `invoked` was
  recorded before the proxy was acquired (Session 248–252; session control
  "proxy failure during submission…", `PWRunnerClientSessionTests/main.swift`
  158–167).

What `submission: invoked` establishes.
- The client process records it in `reservationReply`, on its serial queue
  (Session 223–252), after admitting a granted control and re-sampling the
  clock, and before it calls `submit` (251–252).
- It is the client's own report, checked by `validate_capture` 446–473.
- It establishes that the client crossed its one execution-call boundary. It
  does not establish that a message was sent or received, that the host
  admitted the credential, or that anything executed.

Rationale and history (S).
- The fallback was introduced in `ba483826` (2026-06-11). That commit's
  message says the host compile "now runs only on `xpc_error` (to tell a
  never-compiled policy from one that compiled but blocked the XPC reply)".
- The same commit put the rationale in two other places:
  - the guide, then `PolicyWitness.md` at the repository root (line 110 at
    that commit): "only to disambiguate an `xpc_error` (a policy that
    compiled but then blocked the XPC reply vs. one that never compiled)";
  - a module comment in `controller/src/run_flow.rs`: "only to disambiguate
    an `xpc_error` (compiled-but-reply-blocked vs. never-compiled)".
- Current documents disclaim that inference: the fallback "establishes
  neither worker progress nor the cause of a lost reply" (README 224; guide
  767–768).
- No current statement gives another reason for restricting fallback to
  `xpc_error`.
- Cost (judgment): a present `policy_check` implies only
  `submission: invoked`, which the capture already records. An absent one
  says nothing about whether the specimen may have executed: d2 was invoked
  and has none. So the field adds nothing about possible execution beyond the
  submission state.

Statements implying a pairing that cannot occur:
- 11-policy line 392: the capture reports the attempt "alongside the
  transport result and any retained worker evidence". No worker evidence is
  ever present.
- Guide 1515: "an independent fallback compiler result may also be present"
  for `xpc_error`. With the shipped host it is always present (see TR-7 for
  the host-label case).
- README 232–234 says `execution_envelope` "assembles the dossier,
  transport, acquisition history, independent fallback compilation and
  execution diagnostics". ARCHITECTURE 462–466 says `execution_envelope`
  "assembles the execution records". That function is a `#[cfg(test)]`
  helper (run_flow.rs 793). In production, fallback and diagnostics never
  coexist in one envelope.

**ARCHITECTURE 467**: "The client's timeout ends the controller's wait and
yields a synthetic `xpc_timeout` reply." This wording entered at `29e3ead0`
(2026-10-05). At that time the client did synthesize a `PWRunnerRunResult`
with `xpc_timeout` (`runner/Clients/PWRunnerClient/main.swift` 156–170 at that
commit). `34496c0f` replaced
that with the capture. The sentence describes the earlier design. d1 and d2
show that `runner_result` is null on timeout (N).

**Combined-fault control (C, B7).**
- Inputs: the constructed `xpc_error` capture and a 200,241-byte request. The
  scripted client closed stdin and then wrote the capture.
- Result: `tool_error`/2, error "request delivery failed after 65536 bytes:
  Broken pipe (os error 32)", `transport_admission: delivery_failed`,
  `submission: unknown`, transport `Rejected` with bytes equal to the
  capture, `policy_check` present and null, `actor_policy_checks` absent.
- Two readings of the 40-envelope `admit` effect are ruled out:
  - that an `xpc_error` terminal inside the capture can authorize fallback
    beside a delivery refusal ("another refused boundary … Eligible
    xpc_error can add independent fallback compilation");
  - that the client's terminal takes precedence over delivery.
- With the shipped client, this pairing is unlikely natively, because the
  client reads stdin to EOF before connecting (main.swift 104–108).

### TR-5 — DT-42 settled: the actor-form whole-request helper fails to decode, beside ordinary per-actor compilations

**Native host loss (N, `c/`).**
- Request: one applied actor `zeta`, whose policy is `(version 1) (allow
  default)` with augment `exec_baseline`. Its one action runs `/bin/sh -c
  "/bin/sleep 8; true" trio-transport-k8b2d4`.
- Baselines without a kill:
  - The single-actor request used for the kill, with `sleep 1`, finished/0
    (`c/single_baseline_envelope.json`).
  - A three-actor variant with `sleep 1` finished/0 in 1.1 seconds
    (`c/baseline_envelope.json`).
  - An earlier three-actor variant omitted `sandbox_check` and was refused by
    the host as `bad_request`, reaching the admitted-other row
    (`c/baseline0_bad_request_envelope.json`).

Target identification (`kill_driver.py`, `kill_log.json`):
- The process with the nonce (PID 71752) had parent W = 71750.
  `proc_pidpath(W)` was the app's `pw-probe-runner`.
- W's parent H = 71748 had `proc_pidpath` equal to the app's `PWRunner`.
- H's only child was W.
- H was absent from a process snapshot taken before the controller was
  launched.
- `launchctl print pid/71747` (the controller's `pw-runner-client`) listed
  `71748 … com.policywitness.policy-witness.PWRunner` in that client's
  per-process domain.
- The service's Info.plist declares `ServiceType = Application`.

SIGKILL was sent once, to 71748, 0.19 s after launch. The controller exited
19 ms after the signal, 0.21 s after launch (`kill_log.json` event times). In
that interval it ran both helper calls. Its envelope:
- result `xpc_error`/1, error "connection to service named
  com.policywitness.policy-witness.PWRunner";
- capture accepted, `invoked` (elapsed 23 ms), `acquisition_stop: granted`;
- error stage `submission`, reason `xpc_error`, NSCocoaErrorDomain 4097;
- the control-reported host PID was 71748;
- `runner_result` and `runner_sandbox_diagnostics` present and null.

The fallback captures:
- **`policy_check`**: `status: "tool_error"`, `tool_exit_code: 2`, envelope
  null, stdout 0 bytes, stderr "failed to parse request.json: missing field
  `policy` at line 44 column 1".
- **`actor_policy_checks`**: `[{"actor_id": "zeta", "policy_check": {status:
  "ok", tool_exit_code: 0, …}}]`. The helper's `policy_sha256` was
  `7a3962a7…`. That equals the dossier's `applied_sha256` and the
  independently computed SHA-256 of the source plus `"\n"` plus
  `exec_baseline.sb`.

Process aftermath:
- Saved in `kill_log.json`: immediately after the controller exited, the
  host was gone. W (now with parent 1), the `sh` child and its `sleep` were
  still present, with the same PIDs, start times and commands.
- Seen at the terminal, not saved: at 14:48:43 (`date`), 20 seconds after
  start, `ps -o pid=,ppid=,lstart=,command= -p 71750,71752,71753` printed no
  process and exited 1. So no process with any of those PIDs existed then. I
  sent no cleanup signal. The only record of this check is the
  investigation transcript.
- An earlier attempt sent no signal: its identification predicate failed
  because the worker's argv[0] is not a path. That run finished normally
  (`kill_attempt0_no_signal_*`).
- During the observed run, the worker ran the exec action. `kill_log.json`
  records the nonce-carrying `sh` as W's child, before and after the signal.
  The envelope holds no host evidence of that execution. Its only policy evidence is the dossier
  and two helper results.

**Controlled replay (C, B4).** A constructed `xpc_error` capture was used
(TR-6 gives its derivation and acceptance). Each fallback call ran the shipped
helper through the symlink.

| Case | Request (held bytes) | `policy_check` | `actor_policy_checks` |
| --- | --- | --- | --- |
| B4i | ordinary with `exec_baseline` (1,794 B) | `ok`/0, helper hash `7a3962a7…` = spliced expectation | absent |
| B4ii | actors: zeta (augmented), middle unapplied, alpha `(allow no-such-operation)` with params (2,556 B) | `tool_error`/2, stderr "…missing field `policy` at line 52 column 1" | `zeta ok/0` (hash `7a3962a7…`), `alpha compile_error/1` (hash `a8cf11b5…`) |
| B4iii | actors plus non-null top-level `(deny default)`; modes `"future"` and `9`, `actor_id: 17`, scalar policy, unapplied with policy (1,002 B) | `ok`/0, hash `46f655c8…`: the top-level policy, which the host refuses as `exclusive_plan_forms` | `future ok`, `null ok`, `unapplied_with_policy ok` (`(deny default)` hash); the scalar policy is omitted |

Helper-only probes (N, `a/`), shipped `sbpl-check --request -`:

| Input | Exit | Output |
| --- | --- | --- |
| Actor held request, no top-level policy | 2 | stdout empty, "missing field `policy`" |
| `"policy": null` | 2 | "invalid type: null, expected struct CheckPolicy" |
| Non-null top-level policy | 0 | `ok` |
| Per-actor objects | — | `ok`/0 and `compile_error`/1 |

**What each invocation receives (S, confirmed by helper hashes).**

*Whole-request call.*
- It receives the held string from `serde_json::to_string_pretty` (run_flow
  678), after augment resolution and selector stripping. That is the same
  string the client receives.
- `sbpl-check`'s `CheckRequest { policy }` has no `deny_unknown_fields`
  ([sbpl-check.rs](../controller/src/bin/sbpl-check.rs) 48–58, 433–439). It
  reads only `policy.format`, `policy.sbpl_source` and `policy.params`.
- A host-admissible actor request has no top-level policy, because the host
  refuses a non-null one
  ([PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift)
  127–132: `exclusive_plan_forms` at path `["policy"]`; sibling refusals at
  138 and 141).
- So for every such request the whole-request result is a decode failure:
  exit 2, empty stdout, `tool_error`
  ([policy_check.rs](../controller/src/policy_check.rs) 84–93).
- Controller admission has no form check: it checks only object, contract,
  mode injection, selector, selection and augments (request_patch.rs 47–100;
  run_flow 576–670). An actor request with a non-null top-level policy
  therefore reaches the client, and on fallback its top-level policy is
  compiled (B4iii).

*Per-actor calls.*
- `actor_policies` is collected after actor augment resolution and before
  delivery (run_flow 616–643). It contains every actor whose
  `sandbox.policy` is a JSON object, whatever its mode, so invalid and
  `unapplied` modes are included.
- Each call receives compact `{"policy": <object>}` (377–394).
- The calls run sequentially after the whole-request call (716–724).

*Association.*
- `actor_id` is the declaration's string label, or null.
- A check is tied to its actor only by that label and by its position among
  policy-bearing actors. In B4iii the dossier lists four actors
  (`future`, null, `scalar`, `unapplied_with_policy`) against three checks.
  Only the null label at check index 1 depends on order.

*Exit-code provenance (C).*
- B4u, helper absent: `status: "unavailable"`, `tool_exit_code: 1`, stderr
  "embedded tool not found in Contents/MacOS: \"sbpl-check\" …", stdout and
  stderr byte counts null.
- B4s, helper replaced by a script that reads stdin and then sends itself
  SIGKILL: `status: "tool_error"`, `tool_exit_code: 1`, stderr empty, counts
  0.
- A helper killed by a signal is therefore recorded as exit 1 (`code()
  .unwrap_or(1)`, policy_check.rs 78). That is indistinguishable from a helper
  that printed nothing and exited 1.
- The 11-policy `tool_exit_code` text ("Helper process exit code, or the
  capture's fallback value when unavailable") omits the signal case.
- A helper delivery failure returns `Err` and discards the helper's actual
  output (policy_check.rs 69–73). This is source only; the helper reads
  stdin to EOF first.

**What the statements say.**
- controller/README 5–8: "it checks the held whole request and each carried
  actor policy object". For actor requests the whole request is not checked;
  it fails to decode.
- No statement says that `policy_check` is `tool_error` for every eligible
  actor-form fallback:
  - 40-envelope `policy_check` (RESPONSE 254);
  - 11-policy `classify` (688) and `actor_check` (713);
  - guide 861–864 and 1073–1075.
- 11-policy `read` (236) does state, for `controller_helper_stdin`, that
  decode errors exit 2 and are reported on stderr. So the helper side of the
  outcome is documented, while the run-level consequence is not.
- Guide 1074–1075: "These independent compile diagnostics can run before host
  admission". In the native run, the fallback ran after the host had admitted
  the request and the actor's worker had begun its action. The checks are
  independent of host admission; they are not ordered before it. The
  contract's wording, "Collection of these policy objects precedes host
  admission", is accurate.
- Cost (judgment): one actor-form envelope carries a `policy_check` with
  status `tool_error` and exit 2 beside per-actor `ok` or `compile_error`
  captures. No statement explains how they relate. A reader can mistake the
  decode failure for a helper or controller fault.

**What the tests credited for this establish.**
- `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`
  (run_flow 3237–3406) substitutes the helper. Call index 0, the whole
  request, always returns `Err`. The test therefore asserts
  `policy_check.status == "unavailable"`, where production gives
  `tool_error`/2. It does establish the inputs: the held string first, then
  the resolved policies in order, then the labels.
- `actor_fallback_uses_held_policy_objects_before_host_mode_admission`
  (3113–3234) returns `Err` for every call. It establishes collection
  independent of mode, and the held bytes. It is credited in 42-dossier and
  CONTROLLER 313–319.
- ARCHITECTURE T12 (229) cites `fallback_compilation_…` and
  `refused_reply_versions…`, which contain no actor input, for "independently
  associated actor-policy diagnostics".
- `failure_boundaries/fallback_helper`
  ([check.py](../tests/suites/failure_boundaries/check.py) 415–438) runs the
  shipped helper with a file path on a source over 4 MiB and asserts
  `policy_too_large`. That establishes the helper's own admission, not the
  controller's fallback path, stdin delivery or the actor form.

### TR-6 — The constructed `xpc_error` capture, and what nothing binds

**Derivation (S, C).**
- B4 and B7 use `B4_constructed_xpc_error.capture`, 782 bytes. It keeps r1's
  root fields 1–12 byte-for-byte: identity, clock, the granted attempt with
  its admitted control, `acquisition_stop: granted`, and
  `submission: invoked` at 31 ms.
- It then adds terminal `xpc_error` (tag 13) and an error record (tag 14,
  record 67). That record has stage `submission`, reason `xpc_error`, domain
  NSCocoaErrorDomain, code 4097, the message "constructed: …" and two false
  truncation flags.
- This follows the Swift emission:
  - `connectionFailed` sets stage `submission` in the `.submitted` phase and
    completes `"xpc_error"` (Session 192–197);
  - `complete` leaves `acquisition_stop`, attempts and submission as recorded
    (276–283);
  - `PWRunnerTransportError.init` records the NSError domain and code
    (PWRunnerTransport.swift 105–116);
  - no `runner_reply` is present.
- The controller *accepted* it: `transport_admission: accepted`,
  `submission: invoked`.
- Its acceptance is part of the result. The native capture from (c) has the
  same shape, with message "connection to service named …" and code 4097.

**No binding between capture and request (C).**
- B8 used r1's capture, from an ordinary request with
  `specimen_id: trio-transport-r1`, under an actor-form request
  (`trio-b-actor`).
- Result: admitted `finished`/0. The dossier listed three actors, the reply
  carried no `execution_form`, diagnostics were an ordinary `clean_exit`, and
  the reply's `specimen_id` differed from the request's.
- Nothing compares the capture or reply with the held request.
- B9 shows that the client's exit code is recorded and not consulted: r1 with
  scripted exit 1 was admitted as `finished`/0, with
  `runner_client.exit_code: 1`.
- With the shipped client, the binding holds by construction: one process
  reads the held bytes from stdin and submits them. These results are not a
  native fault. They show that the controller's admission does not itself
  check that binding.

### TR-7 — Smaller observations

- **Refusal spellings shared with host labels.** AdmittedOther copies any
  host label. A current-contract reply labelled `xpc_error` therefore
  produces outcome `xpc_error`/1 with `runner_result` present and no
  fallback. `refused_reply_versions…` asserts this (T). The shipped host
  never emits that label (`git grep` finds `xpc_error` in no file under
  `runner/Sources`). The guide's row for `xpc_error` (1515) describes only
  the client capture.
- **DT-32, error precedence (S).** `stdout_parse_error` is set only in the
  decode-failure arm, which returns `Err` (runner_client.rs 724).
  `stdout_capture_error` forces `Err("malformed")` (708–710). B5a and B5b set
  `stdout_parse_error` with a refused capture; B5c refused on semantics with
  no `stdout_parse_error` (C). The second and third precedence tiers in
  40-envelope (RESPONSE 243) cannot follow execution admission. No test
  passes those errors through `complete_execution`.
- **DT-32, collection bound.** `git grep` for `reply_capacity` or
  `reply_geometry` in `controller/` and `tests/` outside
  `porcelain_admission.rs` finds nothing. No test carries an over-capacity
  reply through `run`. The capacity gate shares `admission_problem` with the
  label gate. B3b exercised that path through binary decoding for the label.
  Capacity remains source-only for `run`.
- **DT-32, label effect notation.** RESPONSE 2619 renders the label effect
  as `withhold(envelope.data.runner_sandbox_diagnostics)`. 2866 and 2885 use
  `set_value(…, null)`. The notation table defines `withhold` only as
  "Withhold that target" (tree.py 1450). The surface golden
  `tests/fixtures/contract/surfaces/envelope.json` records the field as
  `json_null: true, omission: null`, meaning always present. The shape golden
  `envelope_shape.json` is an allowlist and blind to presence (DT-111). B3b's
  real envelope has the key present with null (C). The two statements differ
  in notation only.
- **Integrity findings do not select the outcome** (relayed by the
  acceptance pass; verified, S). `select` never reads
  `Disposition::Admitted.integrity_issues` (result.rs 202–237; only run_flow
  730–742 computes it). This matches 40-envelope 189–194. Only geometry and
  compiled-profile problems refuse admission. Every other semantic finding
  changes diagnostics only.
- **Host reporting fallback** (relayed; verified, S). `pwRunnerReportData`
  ([PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
  123–155) always emits something:
  - first the validated report;
  - then a rich `runner_reporting_failed` reply;
  - then a minimal reply;
  - then, at line 154, empty `Data()`.

  Every writer uses `PWProducer.current`. Whatever bytes result are sent
  with `reply(true, data)` (339).

  What happens to empty bytes is partly source and partly inference:
  - **Client side (S, Swift client).** `submissionReply` does not check
    length when `isResult` is true. It stores `PWRunnerReplyCapture(data)` and
    completes `"runner_reply"`
    ([PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
    260–262). For empty data, `PWRunnerReplyCapture.init` records
    `bytes_received` 0, `bytes_retained` 0 and `truncated` false
    ([PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
    163–168). `emit` exits 0 for terminal `runner_reply` (main.swift 30).
  - **Controller side (S).** `validate_capture` tests whether a host reply is
    present by the `Option`, not by length (runner_client.rs 478–481). Its
    retention checks hold for zero (575–587). `decode_bound` refuses a frame
    shorter than 36 bytes as `Malformed` (porcelain.rs 179–181), which yields
    `malformed_runner_response` with a null projection. Through the real
    parser, `arbitrary_rejected_host_bytes_survive_and_do_not_become_claims`
    constructs a capture with empty host bytes and asserts that label.
  - **Inference, not observed.** That NSXPC delivers a zero-length `Data`
    argument to the client's reply block as an empty `Data`, rather than
    failing. No path that reaches the empty writer was executed.

  The rich and minimal replies would be admitted with the host label
  `runner_reporting_failed`/1. This is the one native route to malformed host
  bytes from a well-behaved client, and it was not exercised.
- **Accepted-but-unproduced client vocabulary.** The client never emits
  error reasons `interrupted` or `invalidated`
  (`git grep` in `runner/Clients` and `runner/Sources` finds them only in the
  host's own connection handlers). `validate_error` accepts both
  (runner_client.rs 126–143).

### Precedence and retention (question 2)

The first failing row decides the outcome. Each cell is marked with its
evidence class.

| Boundary that failed first | Outcome / exit | `submission` | `runner_client.transport` | `runner_result` | Fallback | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Client launch, deadline setup or tool resolution | `tool_error`/2 | — (`runner_client` null) | — | null | no | S |
| Request delivery | `tool_error`/2 | unknown | rejected bytes, never decoded | null | no | C (B7) |
| Retention loss (>272 MiB) | `malformed_runner_client`/1 | unknown | rejected prefix | null | no | unit test through the real parser (`retention_loss_precedes_decode_and_keeps_exact_prefix`) |
| Empty stdout | `missing_runner_client`/1 | unknown | null | null | no | S |
| Capture schema or contract | `unsupported_runner_client`/1 | unknown | rejected bytes | null | no | C (B5b) |
| Capture frame malformed | `malformed_runner_client`/1 | unknown | rejected bytes | null | no | C (B5a, r1 truncated by one byte) |
| Capture semantics | `malformed_runner_client`/1 | unknown | rejected bytes | null | no | C (B5c) |
| Accepted; host reply truncated | `runner_reply_truncated`/1 | invoked | typed, prefix retained | null | no | S |
| Accepted; host schema or contract | `unsupported_runner_response`/1 | invoked | typed, bytes retained | null | no | C (B2, B3a) |
| Accepted; host bytes malformed or empty | `malformed_runner_response`/1 | invoked | typed, bytes retained | null | no | C (B3c), T |
| Accepted; terminal not `runner_reply` | that refusal/1 | `not_invoked` or `invoked` | typed | null | only `xpc_error` | N (d1, d2, c), C (B6, B4) |
| Decoded; geometry or profile labels | `malformed_runner_response`/1 | invoked | typed | **decoded, retained** | no | C (B3b) |
| Admitted | host label; `finished`/0, otherwise 1 | invoked | typed | decoded | no | N (baseline), C (B1) |

The four rows beginning "Accepted; host …" and "Accepted; terminal not
`runner_reply`" are alternatives, not a sequence. The three host-frame rows
apply only with terminal `runner_reply`; the terminal row applies only
without it. Of the three host-frame rows, truncation is tested before
decoding, and the fingerprint before the contract.

For every row except the last, `runner_sandbox_diagnostics` is present and
null. For rows with N or C evidence, the saved envelopes show it. For the
S and unit-test rows, it follows from source: `tool_error` and
`execution_only` both set it to `None` (run_flow.rs 154–164 and 715), and
`RunData` has no skip rule. `actor_policy_checks` is omitted unless fallback ran for an
actor request.

### How DT-31, DT-32 and DT-42 relate

The three findings share one mechanism (S). Client-capture admission
(`failure()`) gates `complete_execution`, and fallback eligibility is a
subset of the `failure()` refusals. Three consequences follow from that
single gate:
- execution admission always carries a decoded host reply (DT-31);
- the client stdout errors never reach the post-admission precedence (DT-32);
- a fallback capture never shares an envelope with a host report or with
  execution diagnostics (DT-42 / TR-4).

The same states survive in code and tests because injected constructors and
JSON-decoded fixtures produce them (TR-3).

DT-31's foreign-producer half and DT-42's actor-form branch are different
boundaries:
- the first concerns the order of `decode_bound`;
- the second concerns the helper's decoder and the absence of a form check
  in the controller.

In the paths I traced, I found no further dependency they share. That is a
judgment from this trace. It is not the result of a search designed to rule
one out.

### Coverage and limits

**Traced.**
- The client parser, capture validation and `failure()`.
- `admit_reply`, `complete_execution`, the fallback functions and `run`.
- `select`, `policy_check.rs` and `sbpl-check.rs`.
- Verify's use of the admission path.
- The Swift session and entry point.
- The host's control and report writers.
- The stated contracts:
  - 20-transport, 40-envelope, 41-diagnostics (admit and geometry), and the
    11-policy helper and fallback sections;
  - the corresponding passages in the controller README, guide, ARCHITECTURE
    and CONTROLLER;
  - the failure contract's transport paragraph.

**Not done.**
- No `tests/run.sh` case was run. Statements about tests rest on reading
  their bodies.
- A native truncated host reply (between 96,468,992 and 134,217,728 bytes), a
  native empty reply and a native reply over the capacity bound were not
  produced.
- A native `xpc_error` for the ordinary form was not produced. B4i covers that
  path with controlled output.
- `runner verify` was traced only as a second caller.
- Whether `runner_response_unavailable` was reachable before `34496c0f` is
  open.

**Limits of the evidence.**
- The C cases establish how the controller handles bytes. They do not
  establish native client or host behaviour.
- The (c) run is one native observation, made with a forced host kill. It
  establishes that the run-level outcome exists. It does not show how often
  such failures occur.
- The constructed capture's acceptance is an observation. Its resemblance to
  the native (c) capture was compared by fields, not by bytes.
- No change to code, tests or documentation accompanies this report.
