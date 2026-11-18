# K-transport: transport reachability, error precedence, retained bytes, helper selection and held-input provenance

Read-only assessment at HEAD `837296af`. Coverage-map row: DT-31/32/42/113–119.
One subject, one assessment. Entries: DT-31, DT-32, DT-42, the section
"Additional findings: transport failure and helper fallback" (evidence classes,
the three answers, DT-113–DT-119, the precedence table, "How DT-31, DT-32 and
DT-42 relate", coverage and limits).

## 0. Basis for this pass

**Identifiers.** DT identifiers are the review's. Subfindings take `.a`, `.b`…
in the review's order (DT-115 keeps the review's own numbers 1–5). The
unnumbered parts of the transport section are anchored by heading, not
renumbered: `EV` (identity and evidence classes), `Q1`–`Q3` (the three answers),
`PR` (precedence and retention table), `REL` (how the three relate), `LIM`
(coverage and limits).

**Evidence labels.** N, C, T, S as the review defines them (native shipped
binaries; controlled client bytes through a Cargo-built controller; typed
injection in Rust unit tests; source inspection). In addition:

- `local`: the file is present under `.tmp/contract-trio/transport/` on
  2026-11-17. That directory is gitignored and was produced against contract
  `development:bdefcb44…` (app built from `8b5de2b2`). It shows what that
  investigation recorded. It is not a current case pass, and its captures are
  not accepted by the current controller without substituting the contract.
- `re-read`: I read the cited lines at HEAD.
- `re-run`: I executed a side-effect-free command against the current signed
  app (`dist/PolicyWitness.app`, built at `2f4d76e4`, contract
  `development:b55acb20…`, build 1519). Inputs and outputs are under
  `.tmp/trace-integration/assessments/work-K-transport/`.

**What I executed.** `policy-witness --version`; `policy-witness help result`;
the shipped `sbpl-check --request -` on three constructed inputs (an actor-form
held request with no top-level policy; `{"policy": null, …}`; a policy-only
object). Nothing else. No build, test case, `run`, cargo or swift command.

**Source stability.** `git diff --stat cc55288d HEAD -- controller runner`
shows two files: `controller/tools/pw_probe_runner/pw_probe_runner_abi.h` and
`runner/Sources/PWRunnerCore/CWorker.swift`, both only in the generated worker
identity constants. `controller/src`, `runner/Clients`, the contract surfaces,
`docs/limits.json`, `tests/suites/failure_boundaries`, `tests/suites/blackbox_e2e`,
`tests/lib/consumer.py` and `tests/lib/blackbox.py` are byte-identical to the
transport investigation's snapshot. Every line number the review gives for
those files applies at HEAD; I re-read each one I rely on.

**Registered cases the review did not name.** Two existing cases assert parts
of what the review reports as source-only or controlled-only. I read them; I
did not run them and do not credit a pass.

- `runner_byoxpc/reservation_controls` (opt-in; needs app, GUI, identity,
  swift, clang, meson). `lost_execution`
  (`tests/suites/runner_byoxpc/opt_in/reservation_controls.py:471-484`) runs
  the shipped `policy-witness run` on an ordinary request against an
  instrumented host copy, sends SIGKILL to that host at the reply gate, and
  asserts `submission == "invoked"`, accepted admission, terminal `xpc_error`,
  null `runner_result` and outcome `xpc_error`. It asserts nothing about
  `policy_check`. `old_response` (`:543-558`) alters only the encoded reply's
  producer contract after one real execution and asserts
  `unsupported_runner_response`, null `runner_result`, retained bytes and null
  `policy_check`.
- `integration/cli.integration`,
  `sbpl_check_argument_and_request_failures_exit_2_without_an_envelope`
  (`controller/integration/cli_contract.rs:811-853`): the row "request without
  a policy on stdin" (`:841-845`) asserts exit 2, empty stdout and nonempty
  stderr from the shipped helper for `{"probe_plan": []}`.

## 1. Claims table

Columns: id | claim | boundary (input form, representation, observer, time) |
holds at HEAD? | evidence class and availability | classification.

### DT-31, DT-32, DT-42

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-31.a | An execution-admitted run with no host result is not produced by the client-admission path, yet four statements describe that state and the unit test that produces the label injects the pair. | Any request form; typed `(RunnerClientRun, Option<reply>)` after capture parsing; controller; at reply admission. | yes. `controller/src/runner_client.rs:478-481,602-650,740-780`; `controller/src/run_flow.rs:330-342`. Statements: `docs/contract/40-envelope.surface.md:143-145` and `:242`; hand-authored `docs/RESPONSE.md:88-90`; `docs/contract/50-installation.surface.md:97`. | S in the review; re-read. A negative; no execution can show it. | inaccurate mechanism account |
| DT-31.b | A foreign producer contract is refused while decoding the frame, before a typed body exists, so `runner_result` is null; the controller README says a decoded reply with another contract is refused and its projection retained. | Host frame bytes inside an accepted capture; controller decoder; decode time. | yes. `controller/src/porcelain.rs:174-222`; `controller/src/runner_client.rs:752-777`; `controller/README.md:185-190`. | S; later C (B2, local); re-read. A live assertion exists in opt-in `runner_byoxpc/reservation_controls` (`reservation_controls.py:543-558`), not run here. | inaccurate mechanism account |
| DT-31.c | Limits: neither path was exercised; other constructors were not searched. | — | superseded by DT-113.b (constructors searched) and DT-114.c (C cases). | — | accurate observation needing no change |
| DT-32.a | The collection-bound rule's check-read support cites two tests that call the diagnostics function directly; on `run` an over-capacity reply is refused before `complete_execution`, so the asserted `withheld`/`reply_capacity` value is never published; no test carries such a reply through `run`. | Decoded typed reply; controller; admission versus diagnostics. | yes. Support `docs/contract/41-diagnostics.surface.md:320-330`; tests `controller/src/porcelain_admission.rs:3106` (asserts at `:3182-3197`) and `:3231` (asserts at `:3295-3300`); run gate `controller/src/run_flow.rs:99-107,341-353`; unpublished branch `porcelain_admission.rs:1588-1594`. | S; re-read; `git grep reply_capacity` outside `porcelain_admission.rs` is still empty. | overstated coverage credit |
| DT-32.b | Tiers two and three of the `result.error` precedence cannot occur after execution admission. | Run envelope `result.error`; controller; after admission. | yes. Statement `40-envelope.surface.md:112-117`; code `run_flow.rs:755-769`; parser `runner_client.rs:708-710,714-726`. | S; C (B5a, B5b, B5c local); re-read. | inaccurate mechanism account |
| DT-32.c | The failed-label effect and the context refusal state one path with different effects (`withhold(...)` and no exit code, against `set_value(..., None)` and exit 1). | Surface statements for `run`; refusal path. | yes. `docs/contract/35-profile.surface.md:334`; `41-diagnostics.surface.md:355` and `:309`. | S; C (B3b local: key present with null); re-read. | consequential ambiguity |
| DT-42.a | The shipped helper cannot decode an actor request with no top-level `policy` (exit 2, empty stdout); the controller sends the held whole request with no form condition; absent output is `tool_error`; the README says fallback "checks the held whole request"; the field statement does not say the status is `tool_error` for every eligible actor-form fallback. | Held whole request on helper stdin; helper and controller; at fallback. | yes. `controller/src/bin/sbpl-check.rs:48-58,433-439`; `run_flow.rs:716-719`; `controller/src/policy_check.rs:84-93`; `controller/README.md:5-8`; `40-envelope.surface.md:152-155`. | Review: partial reproduction, then N (run c) and C (B4ii), local. Re-read. Re-run: current helper on an actor-form request exits 2 with 0 stdout bytes and "missing field `policy`". | consequential ambiguity (field statement) and inaccurate mechanism account (README); pending product decision 1 |
| DT-42.b | On the `unavailable` path `stderr` holds the controller's own launch or delivery text and `tool_exit_code` is the constant 1, also used when the helper has no exit code. | Fallback capture; controller. | yes. `policy_check.rs:34-41,78`; `controller/src/utils.rs:141-155`; statements `docs/contract/11-policy.surface.md:628-630,672-674`. | S; later C (B4u, B4s local); re-read. | consequential ambiguity |

### Identity and evidence classes (EV)

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| EV.a | Source snapshot `cc55288d`; product directories equal to `4816b0e4`; shipped app from `8b5de2b2`. | Investigation identity. | partly. Line numbers apply (see section 0). The current `dist` app is `2f4d76e4` with another build contract, so the N observations were made under a different build identity than today's app. | `git diff --stat`; `--version` re-run. | accurate observation needing no change |
| EV.b | A Cargo-built controller carrying the app's contract ran inside a scratch app with a scripted client; its `sbpl-check` is a symlink to the shipped helper. | C-class apparatus. | unverifiable by reading. The scratch app is present under `b/app`; not re-executed. | local | accurate observation needing no change |
| EV.c | Labels N, C, T, S. | — | definitions | — | accurate observation needing no change |
| EV.d | No case ran through `tests/run.sh`; the orchestration tests were read, not executed. | — | true of the review and of this pass. | — | accurate observation needing no change |
| EV.e | Artifacts are under `.tmp/contract-trio/transport/` (`a`, `b`, `c`, `d`, `captures`, `tools`). | — | present; gitignored; no retention guarantee. | local | accurate observation needing no change |
| EV.f | Native observations baseline, d1, d2, r1, r2 and (c). | Shipped binaries at `8b5de2b2`; envelope and capture bytes. | Recorded values re-read from `d/*.json`, `captures/` and `c/kill_envelope.json`; they match the table. Not re-executed. | N, local | accurate observation needing no change |
| EV.g | d2: no worker PID was recorded; the later `ps` pattern can match a host and cannot match a worker; nothing is established about the worker after the timeout. | Process observation after a client timeout. | unverifiable by reading (terminal-only). | N, not saved | accurate observation needing no change |
| EV.h | Controlled cases B1–B9. | Scratch controller reading scripted client bytes. | All seventeen `b/runs/*/envelope.json` re-read; outcome, admission, submission, terminal, presence and helper statuses match the review. | C, local | accurate observation needing no change |

### The three answers (Q1–Q3)

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| Q1.a | Every `run` envelope passes through the one selection relation. | `run`; controller. | yes. `run_flow.rs:160,174,192,725,737`; `controller/src/interface/result.rs:202-237`. An `Err` escaping `run` reaches the same tool-failure selection through `print_escaped_tool_error` (`run_flow.rs:183-193`). | S re-read | accurate observation needing no change |
| Q1.b | Execution admission needs: delivery succeeded; capture accepted; `invoked` with terminal `runner_reply`; the whole host frame decoded under the current schema and contract; geometry and compiled-profile admission. | Capture and host frame bytes; controller. | yes. `runner_client.rs:602-650,704-780`; `run_flow.rs:99-107,330-355`. | S | accurate observation needing no change |
| Q1.c | In the shipped command admission always comes with `invoked` and a decoded reply; the `runner_response_unavailable` row cannot be selected. | As DT-113. | yes (DT-113.a–c). | S | accurate observation needing no change |
| Q1.d | Every other combination is a refusal row; a decoded projection beside a refusal exists only when geometry or compiled-profile admission refused it. | As DT-114. | yes. `run_flow.rs:350-353,715`; `porcelain_admission.rs:1308-1331`. | S; C (B3b) | accurate observation needing no change |
| Q2.a | Precedence: delivery; capture retention, presence, decoding, semantics; then the host frame or the terminal; then geometry and profile labels. | Controller reading client stdout. | yes. `runner_client.rs:705-737,744-778,603-649`; `porcelain_admission.rs:1308-1330`. | S | accurate observation needing no change |
| Q2.b | The host-frame alternative and the other-terminal alternative cannot co-occur, because an accepted capture has a host frame exactly when its terminal is `runner_reply`. | Accepted capture. | yes. `runner_client.rs:478-481`. | S | accurate observation needing no change |
| Q2.c | The earliest failed boundary fixes outcome, error, exit and what is retained; fallback runs only for an accepted `xpc_error`; delivery failure suppresses capture interpretation and fallback; other integrity findings change diagnostics only. | Run envelope. | yes. `run_flow.rs:693-725`; `runner_client.rs:651-661`; `result.rs:205`. | S; C (B7 local) | accurate observation needing no change |
| Q3.a | Fallback is permitted only for an accepted capture with terminal `xpc_error` and successful delivery; the client emits that terminal only after it invoked execution. | Capture; controller and client. | yes. `runner_client.rs:651-661,516-529`; `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift:192-197,250-252`. | S; N (c) | accurate observation needing no change |
| Q3.b | The ordinary check receives the held, pretty-printed, augment-resolved request. | Helper stdin bytes. | yes. `run_flow.rs:608,674-679,717-719`. | S; C (B4i: the helper's `policy_sha256` equals the independently computed hash of source, newline and augment). No Rust test observes the helper's input for the ordinary form (see "Outside the review"). | accurate observation needing no change |
| Q3.c | For an actor request the host would admit, the whole-request call always fails in the helper's decoder with exit 2. | Helper stdin; helper. | yes. As DT-42.a; host exclusivity `runner/Sources/PWRunnerCore/PWRunnerRequest.swift:127-132`. | N (c), C (B4ii); helper probe re-run | accurate observation; product decision 1 |
| Q3.d | Each actor whose `sandbox.policy` is a JSON object gets its own policy-only check, whatever its mode. | Held policy objects; controller. | yes. `run_flow.rs:623-643,374-394`. | S; C (B4iii); T | accurate observation needing no change |
| Q3.e | Each result establishes only that the helper's process did or did not compile those bytes; in the native host-loss run the worker ran its exec action while the envelope carried only fallback results. | Helper process against worker process. | first half yes (`policy_check.rs:1-6`); second half unverifiable by reading, with `c/kill_log.json` and `c/kill_envelope.json` present and consistent. | N, local, one run | accurate observation needing no change |

### DT-113 to DT-119

| id | claim | boundary | holds at HEAD? | evidence | classification |
| --- | --- | --- | --- | --- | --- |
| DT-113.a | `failure()` returns `None` only with no delivery error, accepted admission, no `runner_reply_error` and terminal `runner_reply`; under exactly that condition the parser returns a typed reply. | Parser output; controller. | yes. `runner_client.rs:602-650,740-780,478-481`. | S re-read | accurate observation needing no change |
| DT-113.b | Constructor and caller search: the types derive only `Serialize`; three struct literals (the parser and two `cfg(test)` sites); two `admit_reply` callers, both fed by `run_pw_runner_client`. | Controller source. | yes. `runner_client.rs:25,678,970`; `run_flow.rs:4186`; `utils.rs:15,102`; `run_flow.rs:693`; `controller/src/runner_commands.rs:611-614`. | S; `git grep` re-run | accurate observation needing no change |
| DT-113.c | So `select` with an admitted, reply-less disposition, `execution_diagnostics(None)` and verify's `None` arm cannot occur. | `run` and `runner verify`. | yes. `result.rs:174-180`; `porcelain_admission.rs:1587`; `runner_commands.rs:544`. | S | accurate observation needing no change |
| DT-113.d | Statements describe the unreachable state (RESPONSE 89, 252, 300, 3808) and the shipped `help result` card prints `runner_response_unavailable false 1`. | Public statements and card. | yes. Owners as DT-31.a. Card re-run at the current app prints the line. | S; N (re-run) | inaccurate mechanism account for the two sentences that say such a completion "can" occur; the classification row and the card line define a row no client output reaches (consequential ambiguity) |
| DT-113.e | Only typed injections reach the label (`each_result_class…`, `execution_envelopes_preserve…`); CONTRACT credits the latter to Execution diagnostics; the failure contract says "Constructed replies cross production assembly"; `execution_envelope` is a test helper. | Rust unit tests and their credits. | yes. `run_flow.rs:3806-3814,990,793-799`; credit source `41-diagnostics.surface.md:733`; `tests/FAILURE-PROPAGATION-CONTRACT.md:687`. The phrase is accurate for `complete_execution`, `execution_parts`, `run_result` and `render_envelope`, which are production functions; what is not production is the reply-less input row and the bypassed `run` gate. | S re-read | overstated coverage credit |
| DT-113.f | The join's `entries_no_case_reaches` cannot separate an unreachable row from an uncovered one: it also lists two rows reached natively. | `controller/interface/joins.json`. | yes. `joins.json:880-888`; `controller/interface/README.md:117-128`. | S; N (d1; `c/baseline0_bad_request_envelope.json`) | unsupported inference in DT-31's use of the list; the join's own account is accurate |
| DT-113.g | History: the label entered at `2d5080d7`; whether the state was reachable earlier is not established. | History. | commit exists; not re-examined. | S | accurate observation needing no change |
| DT-114.a | `decode_bound` checks the fingerprint, then the producer contract, then decodes; any reply produced from bytes carries the current contract. | Host frame bytes. | yes. `porcelain.rs:179-221`. The only production decoders are `runner_client.rs:715,752`; `porcelain::decode` is called only from tests. | S; grep re-run | accurate observation needing no change |
| DT-114.b | `ReplyVersion::Unsupported` in `admit_reply` and verify's `unsupported_runner_response` projection are reachable only from typed injection. | Typed reply. | partly, and stricter than stated. `run_flow.rs:343-349`: yes. In `cmd_runner_verify`, the `Unsupported` and `Malformed` arms of `project_verify_typed_reply` (`runner_commands.rs:536-541`) cannot run for any value, typed or parsed, because `admit_reply` refused those first (`:614-623`); only the direct-call unit test (`:968-988`) reaches them. | S re-read | accurate observation needing no change |
| DT-114.c | Controlled results: B2, B3a, B3c give a null `runner_result`; B3b retains the decoded record; keys present and null as listed. | Scratch controller; edited host frames. | recorded envelopes re-read; match. | C, local | accurate observation needing no change |
| DT-114.d | A decoded projection beside a refusal exists in production only for `admission_problem`. | Decoded reply. | yes. `porcelain_admission.rs:1308-1331`; `run_flow.rs:103-106,350-353`. | S; C | accurate observation needing no change |
| DT-114.e | Statements describe a decoded foreign record: README 184–190; the guide's "producer" half; the 40-envelope `admit` condition lists producer identity as a gate after decoding. | Public statements. | yes. `controller/README.md:185-190`; `40-envelope.surface.md:251`. The guide is frozen and not assessed for change. | S | inaccurate mechanism account |
| DT-114.f | The production foreign-contract text differs from the typed path's text, which `delivery_failure_takes_precedence…` asserts. | Error text. | yes. `runner_client.rs:766-769` against `run_flow.rs:343-348,2001-2006`. | S; C (B2) | overstated coverage credit: the asserted text is one no envelope carries |
| DT-114.g | A host from another build is refused earlier, at the control reply (`unsupported_protocol`, terminal `protocol_error`); a host-frame contract refusal needs disagreeing control and frame identities or altered bytes. | Client admission of the control. | yes. `PWRunnerClientSession.swift:205-216,237-240`; `runner/Sources/PWRunnerCore/PWRunnerTransport.swift:57`; `runner/Sources/PWRunnerCore/PWRunnerAPI.swift:175-177`; `docs/build_contract.py:92-97`. | S; N (r1). Both arrangements are constructed in opt-in `reservation_controls.py:530-558`. | accurate observation needing no change |
| DT-114.h | B2 and B3a reach the same label from two checks; only `runner_reply_error` text separates them. Link to DT-105. | Public label. | yes. `runner_client.rs:627-629,760-769`. | S; C | accurate observation needing no change (DT-105 belongs to another row) |
| DT-115.1 | `each_result_class…` returns a typed reply beside capture and reply refusals, pairs a delivery failure with a typed reply, injects a typed foreign reply and the reply-less admitted pair; it asserts outcome, `ok`, exit and card line, not data presence. | Typed pair into production `run`. | yes. `run_flow.rs:3626-3869` (`:3654-3671`, `:3696-3703`, `:3758-3759`, `:3806-3809`). Credited at `docs/architecture.json:3091-3119`, `controller/interface/mutations.json:169` and `tests/CHANGE-VERIFICATION.md:223-256`. | T; re-read | overstated coverage credit |
| DT-115.2 | `delivery_failure_takes_precedence…` asserts `admit_reply(&intact, None)` is admitted, asserts the typed foreign text and renders with a hand-built result. | Typed. | yes. `run_flow.rs:1971-2037` (`:1997-2008`, `:2012-2016`). Not cited outside the file. | T | overstated coverage credit |
| DT-115.3 | `refused_reply_versions…` runs production orchestration on a client value whose host bytes are JSON and whose typed reply comes from serde; its "previous" and "next" rows assert a retained typed foreign `runner_result` where production gives null; the helper is never found, so the capture is `unavailable`. | Typed pair into `run`. | yes. `run_flow.rs:3016-3110` (`:3062-3066`, `:3093-3099`); fixture `runner_client.rs:961-966`; `run_flow.rs:2658-2679`. Credited at `architecture.json:977-1004` (T12). | T; C (B2) and the opt-in live case for the production value | overstated coverage credit |
| DT-115.4 | Consumer `policy_check_controls` wrap helper captures in an envelope whose `runner_result` is a host reply labelled `xpc_error` with terminal `runner_reply`; ARCHITECTURE B9 credits them and `fallback_compilation…` for association with the selected policy or actor; the consumer has no `actor_policy_checks` handling. | Constructed envelope; Python consumer. | yes. `tests/suites/blackbox_e2e/checker_controls.py:39-43`; `tests/lib/blackbox.py:54-112`; `architecture.json:1983-2011`; `tests/lib/consumer.py:343-345`. | S; re-read; `git log -S` history re-checked (`4e02cf51`, `34496c0f`) | overstated coverage credit |
| DT-115.5 | The field-complete shape fixture combines exclusive fields and says so. | Shape golden input. | yes. `run_flow.rs:4025-4243`; `runner_client.rs:942-958`. | S | accurate observation needing no change |
| DT-116.a | The fallback calls on the admitted branch cannot run for any `RunnerClientRun` value. | Typed value; controller. | yes. `fallback_eligible` (`runner_client.rs:651-661`) implies `failure()` is `Some` (`:602-650`); calls at `run_flow.rs:699-701`. | S | accurate observation (dead code) |
| DT-116.b | `xpc_error` always accompanies `invoked`. | Capture. | yes. `runner_client.rs:516-529`; `PWRunnerClientSession.swift:192-197`. | S; N; C | accurate observation needing no change |
| DT-116.c | Fallback does not track possible execution: an invoked timeout has none; a lookup failure never has one; `proxy_type_mismatch` at submission is eligible although nothing was sent. | Client terminal against host progress. | yes. `PWRunnerClientSession.swift:29-43,193-203,250-254`; `runner_client.rs:520-526`; session control `runner/Tests/PWRunnerClientSessionTests/main.swift:158-167`. | S; N (d2, r2) | accurate observation; for a reader of the field, a consequential ambiguity |
| DT-116.d | `submission: invoked` is the client's own record that it crossed its one execution-call boundary; it does not establish sending, receipt or execution. | Capture field. | yes. `PWRunnerClientSession.swift:223-254`; `runner_client.rs:446-473`; already stated at `tests/FAILURE-PROPAGATION-CONTRACT.md:1060-1061`. | S | accurate observation needing no change |
| DT-116.e | The fallback was introduced (`ba483826`) to disambiguate an `xpc_error`; current documents disclaim that; no current statement gives another reason; judgment: the field adds nothing about possible execution. | Rationale. | partly. Documents and module comments: yes (`controller/README.md:221-224`; `run_flow.rs:8-10`; `policy_check.rs:3-4`). One residue of the withdrawn reason remains in a test comment, `controller/integration/cli_contract.rs:1296-1297` ("the xpc_error disambiguation path"). | S | accurate observation; the cost statement is a judgment |
| DT-116.f | Statements imply a pairing that cannot occur: 11-policy "any retained worker evidence"; the guide's "may also be present"; README and ARCHITECTURE name `execution_envelope` as the assembler of fallback with diagnostics. | Public and implementation accounts. | yes. `11-policy.surface.md:392`; `controller/README.md:232-235`; `docs/ARCHITECTURE.md:462-465`; the helper is `#[cfg(test)]` at `run_flow.rs:793`. | S | inaccurate mechanism account |
| DT-116.g | ARCHITECTURE says the client's timeout "yields a synthetic `xpc_timeout` reply"; no reply is synthesized. | Implementation account. | yes. `docs/ARCHITECTURE.md:467-468`. | S; N (d1, d2: `runner_result` null) | inaccurate mechanism account |
| DT-116.h | Combined fault B7: a delivery failure beside an `xpc_error` capture gives `tool_error`/2 with no fallback; this rules out two readings of the 40-envelope `admit` effect. | 200 KB request; scripted client closing stdin. | yes. `runner_client.rs:603-609,653-656,705-707`; statement `40-envelope.surface.md:252`. | C (B7 local) | consequential ambiguity in the statement; behavior as 11-policy states |
| DT-117.a | Native host-loss run (c): `xpc_error`/1; `policy_check` is `tool_error`/2 with "missing field `policy`"; `actor_policy_checks` has zeta `ok` with a helper hash equal to the dossier's `applied_sha256`; the worker and its child outlived the host. | One applied actor; shipped binaries at `8b5de2b2`; SIGKILL to the host 0.19 s after launch. | Recorded files re-read (`c/kill_envelope.json`, `c/kill_log.json`); they match. The check at +20 s is terminal-only. | N, local, one run | accurate observation needing no change |
| DT-117.b | Controlled replays B4i, B4ii, B4iii. | Constructed `xpc_error` capture; shipped helper through a symlink. | re-read; match. | C, local | accurate observation needing no change |
| DT-117.c | Helper-only probes. | Shipped helper on stdin. | re-run at the current app for three inputs: same exit codes and messages. | N (`a/` local); N re-run | accurate observation needing no change |
| DT-117.d | Whole-request call: the held pretty string; `CheckRequest` reads only `policy`; the host refuses a top-level policy beside actors; so every host-admissible actor request is a decode failure; the controller has no form check, so a mixed-form request has its top-level policy compiled. | Held whole request. | yes. `run_flow.rs:678,717-719`; `sbpl-check.rs:48-58`; `PWRunnerRequest.swift:127-132`; `controller/src/request_patch.rs:46-100`. | S; C (B4iii) | accurate observation; product decision 1 |
| DT-117.e | Per-actor calls: collected after actor augment resolution and before delivery; every object-valued policy whatever its mode; compact `{"policy": …}`; sequential, after the whole-request call. | Held policy objects. | yes. `run_flow.rs:616,623-643,386,716-724`. | S; T; C | accurate observation needing no change |
| DT-117.f | A check is tied to its actor only by label and by position among policy-bearing actors. | `actor_policy_checks[]`. | yes. `run_flow.rs:383-391,633-636`. | S; C (B4iii) | accurate observation; a consequential ambiguity for null labels |
| DT-117.g | Exit-code provenance: absent helper gives `unavailable`/1 with null counts; death by signal gives `tool_error`/1, the same as printing nothing and exiting 1; the `tool_exit_code` text omits the signal case; a helper delivery failure discards the helper's output. | Fallback capture. | yes. `policy_check.rs:34-41,69-73,78`; statement `11-policy.surface.md:628-630`. | C (B4u, B4s local); S | consequential ambiguity |
| DT-117.h | Statements: README 5–8 says the whole request is checked; none says `tool_error` for the actor form; 11-policy `read` documents the helper side; "can run before host admission" against the contract's accurate "collection … precedes host admission"; cost judgment. | Accounts. | yes. `controller/README.md:5-8`; `11-policy.surface.md:236,688,713`. The "before host admission" phrase has four current owners: `docs/LIMITS.md:77-78` (shared region), `docs/ARCHITECTURE.md:164`, `architecture.json:551`, `docs/limits.json:1646`. | S | inaccurate mechanism account |
| DT-117.i | Credited tests: `actor_fallback_preserves…` asserts `unavailable` where production gives `tool_error`/2 but establishes the inputs; `actor_fallback_uses…` returns `Err` for every call; T12 cites tests with no actor input; `failure_boundaries/fallback_helper` shows the helper's own admission only. | Rust and Python tests and their credits. | yes. `run_flow.rs:3317-3318,3378-3379,3172-3175`; `architecture.json:977-1004`; `tests/suites/failure_boundaries/check.py:415-438`. Related credit: `docs/limits.json:1881` says oversize input is tested "through the shipped helper and fallback CLI"; the case invokes the helper with a file path only. | S | overstated coverage credit |
| DT-118.a | The constructed 782-byte `xpc_error` capture follows the Swift emission and the controller accepted it; the native (c) capture has the same field shape. | Constructed capture bytes; scratch controller. | `b/captures/B4_constructed_xpc_error.capture` present; acceptance recorded in the B4 envelopes. In-tree typed analog: `runner_client.rs:919-939`. | C, local | accurate observation needing no change |
| DT-118.b | Nothing binds the capture or reply to the held request (B8). | Controller admission. | yes. No comparison exists in `runner_client.rs` or `run_flow.rs` (`git grep specimen_id` re-run). | C (B8 local); S | accurate observation needing no change |
| DT-118.c | The client's exit code is recorded and not consulted (B9). | `runner_client.exit_code`. | yes. `runner_client.rs:682`; `docs/contract/20-transport.surface.md:492-494` describes the client's own exit rule. | C (B9 local); S | accurate observation needing no change |
| DT-118.d | With the shipped client the binding holds by construction; these are not native faults. | One client process reads the held bytes and submits them. | yes. `runner/Clients/PWRunnerClient/main.swift:104-108,124`; `run_flow.rs:681-686`. | S | accurate observation needing no change |
| DT-119.a | The admitted-other row copies any host label: a current-contract reply labelled `xpc_error` gives `xpc_error`/1 with `runner_result` present and no fallback; the shipped host never emits that label. | Host label against controller refusal spelling. | yes. `result.rs:173`; `run_flow.rs:3068-3076`; `git grep xpc_error -- runner/Sources` is empty. | T; S | accurate observation needing no change |
| DT-119.b | DT-32 precedence with C evidence: both stdout errors accompany refused captures only; no test passes them through `complete_execution`. | As DT-32.b. | yes. | S; C | as DT-32.b |
| DT-119.c | DT-32 collection bound: no over-capacity reply crosses `run` in any test; capacity is source-only there. | As DT-32.a. | yes. | S | as DT-32.a |
| DT-119.d | DT-32 label effect: a notation difference only; the key is present with null. | As DT-32.c. | yes. `docs/contract/tree.py:1450`; `tests/fixtures/contract/surfaces/envelope.json` records the field as `json_null: true`, `omission: null`. | S; C (B3b) | as DT-32.c |
| DT-119.e | Integrity findings never select the outcome. | Selection. | yes. `result.rs:205`; `run_flow.rs:730-743`; stated at `40-envelope.surface.md:191-194`. | S; typed row in `each_result_class…` | accurate observation needing no change |
| DT-119.f | The host report writer always emits something, ending in empty bytes; the client records a zero-length `runner_reply`; the controller refuses it as `malformed_runner_response`; delivery of empty data by NSXPC is inferred. | Host writer, client session, controller parser. | yes for source. `runner/Sources/PWRunnerCore/PWRunnerService.swift:123-155,337-340`; `PWRunnerClientSession.swift:260-262`; `PWRunnerTransport.swift:163-168`; `main.swift:30`; `runner_client.rs:478-481,575-587,1307-1322`; `porcelain.rs:179-181`. Host unit control: `runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift:314-328`. The NSXPC step is unverifiable by reading. | S; real-parser unit test; inference unobserved | accurate observation; one unsupported inference, which the review labels as such |
| DT-119.g | The readers accept client error reasons `interrupted` and `invalidated`, which the client never emits. | Capture reader vocabulary. | yes. `runner_client.rs:129-130,356,522-523`; the independent Python reader also accepts them (`tests/lib/runner_client_capture.py:25,223,283`); the client emits `xpc_error` and `proxy_type_mismatch` only (`PWRunnerClientSession.swift:32,35`). | S | accurate observation needing no change |

### Precedence and retention table (PR)

| id | row | holds at HEAD? | evidence |
| --- | --- | --- | --- |
| PR.1 | Client launch, deadline setup or tool resolution: `tool_error`/2; `runner_client` null. | yes. `run_flow.rs:681-689`; `runner_client.rs:859-865,881-882`. | S |
| PR.2 | Request delivery: `tool_error`/2; submission unknown; rejected bytes never decoded; no fallback. | yes. `runner_client.rs:705-707,782-791,603-609`; `run_flow.rs:694`. | C (B7); real-child unit test `runner_client.rs:1542-1567` |
| PR.3 | Retention loss: `malformed_runner_client`/1; rejected prefix. | yes. `runner_client.rs:687-689,708-710`. | unit test through the real parser (`:1584`) |
| PR.4 | Empty stdout: `missing_runner_client`/1; transport null. | yes. `:711-713,785`. | S |
| PR.5 | Capture schema or contract: `unsupported_runner_client`/1. | yes. `:714-726`. | C (B5b) |
| PR.6 | Capture frame malformed: `malformed_runner_client`/1. | yes. `:721`. | C (B5a) |
| PR.7 | Capture semantics: `malformed_runner_client`/1. | yes. `:737`. | C (B5c) |
| PR.8 | Accepted; host reply truncated: `runner_reply_truncated`/1; prefix retained. | yes. `:745-750,626`. | S |
| PR.9 | Accepted; host schema or contract: `unsupported_runner_response`/1; bytes retained; `runner_result` null. | yes. `:760-769,627-629`. | C (B2, B3a); opt-in live assertion |
| PR.10 | Accepted; host bytes malformed or empty: `malformed_runner_response`/1; null projection. | yes. `:770-773,630`; `porcelain.rs:179-181`. | C (B3c); real-parser unit test |
| PR.11 | Accepted; terminal not `runner_reply`: that refusal/1; fallback only for `xpc_error`. | yes. `:635-649,651-661`. | N (d1, d2, c); C (B6, B4) |
| PR.12 | Decoded; geometry or profile labels: `malformed_runner_response`/1; decoded reply retained. | yes. `run_flow.rs:350-353,715`; `porcelain_admission.rs:1308-1331`. | C (B3b) for labels; geometry S only |
| PR.13 | Admitted: host label; `finished`/0, otherwise 1. | yes. `run_flow.rs:698-713,737-743`; `result.rs:166-173`. | N (baseline); C (B1) |
| PR.n1 | The host-frame rows and the terminal row are alternatives; truncation precedes decoding; fingerprint precedes contract. | yes. `runner_client.rs:478-481,745`; `porcelain.rs:182-220`. | S |
| PR.n2 | `runner_sandbox_diagnostics` is present and null on every row but the last; `actor_policy_checks` is omitted unless fallback ran for an actor request. | yes. `run_flow.rs:50-51,66-71,126,379`. | N and C for saved rows; S otherwise |

All fifteen: accurate observation needing no change.

### Relation (REL) and limits (LIM)

| id | claim | holds at HEAD? | classification |
| --- | --- | --- | --- |
| REL.a | One gate (`failure()`) yields three consequences: admission always carries a decoded reply; client stdout errors never reach post-admission precedence; a fallback capture never shares an envelope with a host report or diagnostics. | yes. One refinement: a refused envelope can carry a decoded host reply (PR.12), but never together with a fallback capture, since fallback needs terminal `xpc_error` and a decoded reply needs `runner_reply`. | accurate observation needing no change |
| REL.b | The unreachable states survive in code and tests through injected constructors and JSON-decoded fixtures. | yes (DT-115). | accurate observation needing no change |
| REL.c | DT-31's foreign-producer half and DT-42's actor-form branch are different boundaries. | yes. | accurate observation needing no change |
| REL.d | No further shared dependency was found; a judgment from the trace. | I found none either; the same kind of judgment. | accurate observation needing no change |
| LIM.a | What was traced. | still an accurate list. | accurate observation needing no change |
| LIM.b | No `tests/run.sh` case was run. | true of both passes. | accurate observation needing no change |
| LIM.c | A native truncated reply, a native empty reply and a native over-capacity reply were not produced. | still so; no registered case produces them through XPC. | accurate observation needing no change |
| LIM.d | A native `xpc_error` for the ordinary form was not produced. | partly. True of that investigation. A registered opt-in case produces one through the shipped controller (`reservation_controls.py:471-484`); it makes no `policy_check` assertion and was not run here. | accurate observation; incomplete as a statement of available coverage |
| LIM.e | `runner verify` was traced only as a second caller. | still so. | accurate observation needing no change |
| LIM.f | Reachability of `runner_response_unavailable` before `34496c0f` is open. | open; no decision depends on it. | accurate observation needing no change |
| LIM.g | C cases establish how the controller handles bytes, not native client or host behavior. | yes. | accurate observation needing no change |
| LIM.h | Run (c) is one native observation under a forced host kill. | yes. | accurate observation needing no change |
| LIM.i | The constructed capture's resemblance to the native one was compared by fields, not bytes. | yes. | accurate observation needing no change |

## 2. Comparison

### 2.1 Reachable submission, capture and host-reply combinations

Derived from `parse_runner_client_output` and `failure()` at HEAD; each line
is what an envelope retains after the first failure.

| Delivery | Capture admission | `submission` | Terminal | Host frame | Typed reply | Result | Retained beside the result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| client not run | — | — | — | — | — | `tool_error`/2 | dossier only; `runner_client` null |
| error | `delivery_failed` | `unknown` | unread | unread | none | `tool_error`/2 | rejected client bytes if any |
| ok | `malformed` (retention loss, frame, semantics) | `unknown` | unread | unread | none | `malformed_runner_client`/1 | rejected bytes |
| ok | `missing` | `unknown` | — | — | none | `missing_runner_client`/1 | nothing from the client |
| ok | `unsupported` | `unknown` | unread | unread | none | `unsupported_runner_client`/1 | rejected bytes |
| ok | `accepted` | `invoked` | `runner_reply` | truncated | none | `runner_reply_truncated`/1 | typed capture with prefix |
| ok | `accepted` | `invoked` | `runner_reply` | other fingerprint or contract | none | `unsupported_runner_response`/1 | typed capture with bytes |
| ok | `accepted` | `invoked` | `runner_reply` | malformed or empty | none | `malformed_runner_response`/1 | typed capture with bytes |
| ok | `accepted` | `invoked` | `runner_reply` | decodes | present; capacity or label gate refuses | `malformed_runner_response`/1 | typed capture and decoded reply |
| ok | `accepted` | `invoked` | `runner_reply` | decodes | present; admitted | host label, 0 or 1 | typed capture, reply, diagnostics |
| ok | `accepted` | `invoked` | `xpc_error` | absent | none | `xpc_error`/1 | typed capture and fallback captures |
| ok | `accepted` | `invoked` or `not_invoked` | `xpc_timeout`, `protocol_error`, `local_error` | absent | none | that refusal/1 | typed capture |
| ok | `accepted` | `not_invoked` | `acquisition_failed` | absent | none | `xpc_acquisition_failed`/1 | typed capture |
| ok | `accepted` | `invoked` | `submission_refused` | absent | none | `xpc_submission_refused`/1 | typed capture with the refusal control |

Combinations no client output produces: accepted admission with no failure and
no typed reply (DT-113); a typed reply whose producer contract differs
(DT-114); a typed reply beside a delivery failure, a capture refusal or a
host-frame refusal (DT-115.1); a fallback capture beside a host reply or
diagnostics (DT-116); either client stdout error beside accepted admission
(DT-32.b).

### 2.2 Obligation, producer, readers

**A. Admitted completion without a host reply (DT-31.a, DT-113).**

- Stated, `docs/contract/40-envelope.surface.md`: "An admitted execution with
  no host report can still produce the controller's no-worker assessment"
  (`:144-145`); "`runner_response_unavailable` | Completion has no host result
  to supply an outcome; exit 1." (`:242`). `docs/RESPONSE.md:88-90`,
  hand-authored: "An admitted completion without a host reply can instead have
  a no-worker assessment." `docs/contract/50-installation.surface.md:97`: "an
  absent reply selects runner_response_unavailable and no PID."
- Producer: the row exists (`result.rs:174-180`), `admit_reply` maps a missing
  reply to admitted (`run_flow.rs:341-342`), and `execution_diagnostics(None)`
  returns `no_worker` (`porcelain_admission.rs:1579-1587`). No client output
  reaches them. The value `no_worker` itself is reached by an admitted reply
  that has no worker subprocess record, for example a host `bad_request`
  refusal (`porcelain_admission.rs:1579-1587,1642`; observed in
  `c/baseline0_bad_request_envelope.json`, local).
- Readers and tests: `each_result_class…` asserts the row's fields and card
  line from a typed pair; `execution_envelopes_preserve…` asserts `no_worker`
  for a reply-less `complete_execution`; `verification_projects_only_current_replies`
  calls the projection directly. None asserts or denies reachability.

**B. Foreign producer (DT-31.b, DT-114).**

- Stated, `controller/README.md:185-190`: "A host frame naming another schema
  fingerprint, or a decoded reply carrying another producer contract, produces
  `unsupported_runner_response`. … `data.runner_result` holds the decoded
  record's projection when decoding succeeded and is null otherwise."
  `40-envelope.surface.md:251`: "…then decoded host producer identity and host
  capacity/profile-label admission." Accurate statements beside them:
  `40-envelope.surface.md:237` ("captured bytes retained") and
  `tests/FAILURE-PROPAGATION-CONTRACT.md:1072-1075`.
- Producer: the contract is read from the root record and compared before the
  body is decoded (`porcelain.rs:186-220`). The typed comparison in
  `reply_contract` (`run_flow.rs:100-102`) runs afterwards and cannot fail for
  a frame the decoder accepted.
- Readers and tests: through real bytes,
  `producer_gate_precedes_malformed_descendants_and_keeps_raw_bytes`
  (`runner_client.rs:1243-1282`) asserts no typed reply and retained bytes;
  opt-in `reservation_controls.py:543-558` asserts the null `runner_result`
  through the shipped controller. Against them,
  `refused_reply_versions…` (`run_flow.rs:3062-3066`) asserts a retained typed
  foreign record.

**C. `result.error` precedence (DT-32.b, DT-119.b).**

- Stated, `40-envelope.surface.md:115-117`: "After execution admission,
  precedence is host error, client `stdout_capture_error`, client
  `stdout_parse_error`, then a generic unsuccessful-run message."
- Producer: `complete_execution` has the four arms (`run_flow.rs:755-769`).
  The transport surface already states that a capture error forces
  `transport_admission == "malformed"` (`20-transport.surface.md:585`), and
  `stdout_parse_error` is set only on the decoder's error path
  (`runner_client.rs:716-726`).
- Tests: the host-error tier is asserted once, typed
  (`run_flow.rs:3074`). No test asserts the two client tiers or the generic
  message.

**D. Collection bound (DT-32.a, DT-119.c).**

- Stated support, `41-diagnostics.surface.md:327`: "Collection bounds precede
  semantic joins and profile-context checking on run and verification
  admission; their refusal retains the decoded reply."
- Producer: `admission_problem` calls `reply_geometry` first
  (`porcelain_admission.rs:1308-1311`); `run` refuses before diagnostics.
- Tests: the first cited test asserts the diagnostics function's own
  `withheld` and `reply_capacity` output and the integrity admission's error
  count (`:3182-3197`), neither published on `run`. The second asserts
  `admission_problem(&r).is_some()` (`:3295`), which is the function the run
  gate uses, then the same unpublished diagnostics. No assertion reads a
  rendered envelope.

**E. Label-effect notation (DT-32.c, DT-119.d).** `35-profile.surface.md:334`
uses `withhold(envelope.data.runner_sandbox_diagnostics)` and sets no exit
code; `41-diagnostics.surface.md:355` sets exit 1 and
`set_value(…runner_sandbox_diagnostics, None)`. The producer serializes the
key with null (`run_flow.rs:66-71,126`). The run-level test asserts exit 1 and
`is_null()` (`run_flow.rs:2986,3006-3010`), which does not distinguish an
absent key (see "Outside the review").

**F. What fallback is and when it runs (DT-116, Q3).**

- Stated, `11-policy.surface.md:688`: "Invoke the fallback helper when client
  transport admission is accepted, request delivery has no error, and the
  admitted client capture has terminal xpc_error. Deliver the held request on
  stdin." `controller/README.md:221-224`: "It establishes neither worker
  progress nor the cause of a lost reply." `11-policy.surface.md:392`: "The
  fallback capture reports this independent attempt alongside the transport
  result and any retained worker evidence."
- Producer: as the first two statements say. The third cannot be instantiated:
  an envelope with a fallback capture has null `runner_result` and null
  diagnostics. The calls on the admitted branch (`run_flow.rs:699-701`) never
  run.
- Tests: `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`
  counts invocations of a closure that receives no input. It establishes
  eligibility. It observes no helper input and no association.

**G. The whole-request helper call for the actor form (DT-42.a, DT-117).**

- Stated: `controller/README.md:6-8`, "it checks the held whole request and
  each carried actor policy object in request order"; `docs/CONTROLLER.md:314-316`
  likewise; `docs/ARCHITECTURE.md:161-162`, "The held whole request retains its
  fallback diagnostic"; `42-dossier.surface.md:36`, "use those bytes for client
  delivery and whole-request fallback compilation". The envelope surface titles
  the field "Ordinary fallback compilation" and says "eligible ordinary
  fallback compilation" (`40-envelope.surface.md:152,257`).
- Producer: every eligible fallback delivers the held whole request to the
  helper. For any request with no top-level `policy` object the helper exits 2
  before producing an envelope. The host admits an actor request only without
  a top-level policy. So for every host-admissible actor request `policy_check`
  is `tool_error` with exit 2 and the decoder's message.
- Tests: the two actor tests substitute the helper and return `Err` for that
  call, so they assert `unavailable`, a status the real helper does not give
  for that input. The helper's own behavior is asserted natively by
  `integration/cli.integration` for a request without `policy`.

**H. Held-input provenance (DT-117.d–f, DT-117.i).**

- Stated, `42-dossier.surface.md:36,40`: one held serialization; "Actor
  fallback checks serialize the held resolved policy objects separately in
  request order." Working rule (`controller/AGENTS.md`): "Keep one held
  serialization for the client and fallback compiler; never reread or mutate
  the user's file to prepare either invocation."
- Producer: `held` is serialized once (`run_flow.rs:678`) and passed by
  reference to the client and the whole-request helper; actor policies are
  cloned from the resolved value before delivery (`:623-643`).
- Tests: the two actor tests record client and helper inputs and replace the
  file inside the client callback. Their provenance assertions are fused with
  call count and call order (section 6.1). No test observes the helper's input
  for an ordinary request.

**I. Capture, reply and request association (DT-118).** No statement says the
controller compares a reply with the request. The producer makes no such
comparison. With the shipped client the association follows from one process
reading the held bytes and submitting them.

## 3. Plausible treatments

File classes used below. **Build input**: any `.rs` under `controller/src`,
including tests there; an edit changes the build contract and forces a signed
rebuild (`docs/build_contract.py:15-28`). **Not a build input**:
`docs/contract/*.surface.md`, `docs/architecture.json`, `docs/limits.json`,
`controller/README.md`, `docs/*.md`, `controller/integration/*.rs`,
`runner/Tests/**`, `tests/**` other than the five `tests/lib` files and two
`tests/build*` files that `build_contract.py` lists. The build still refuses
stale generated copies, so every generator-input edit needs its regeneration.

Surface edits change stamped public content. Development generation keeps the
frozen guide bytes and regenerates CONTRACT's table. Edit existing `free.*`
text or prose; do not add a new `free.*` fact, because
`docs/contract/free_text.json` refuses an increase.

### Decision 1: the actor-form whole-request helper call

**1A. Do not invoke the whole-request helper when the held request carries an
`actors` array; keep per-actor calls.** Product behavior change.

- Rule. Use the predicate the controller already uses to collect actor
  policies and actor dossiers: the held value's `actors` member is an array
  (`run_flow.rs:623-626`). Such a request gets per-actor checks only.
- Presence. `policy_check` stays present on every run envelope and is null for
  every request with an `actors` array. `actor_policy_checks` is unchanged:
  present when fallback is eligible and at least one actor carries a policy
  object.
- What a user loses. The `tool_error`/exit 2 capture carrying "missing field
  `policy`"; for an actor request in which no actor carries a policy object,
  the only sign that the helper could be launched; for a mixed-form request
  the host would refuse (`exclusive_plan_forms`), the compilation of its
  top-level policy (B4iii). None of these is a compilation of an actor's
  policy.
- Compatibility. `actor_policy_checks` shipped in v0.3.5–v0.3.7 with the
  current behavior. A reader that treats a non-null `policy_check` as "fallback
  ran" for an actor request would stop seeing it. Eligibility is readable from
  the capture (accepted, terminal `xpc_error`, no delivery error) and from
  `actor_policy_checks`.
- Files that change together.
  - Product, build input: `controller/src/run_flow.rs`, the refused branch
    (`:715-724`).
  - Tests, build input: the two actor fallback tests (section 6.1) and a new
    ordinary-form held-input control, because removing this call removes the
    only observation that the helper receives the held bytes.
  - Statements, not build inputs: `docs/contract/11-policy.surface.md`
    `fallback.classify` (`:688`) and its support `limits` (`:702`);
    `docs/contract/40-envelope.surface.md` `data.policy_check` (`:152-155`);
    `docs/contract/42-dossier.surface.md` `collection.held` (`:36`) and its
    support check (`:92`); `controller/README.md:5-8`;
    `docs/CONTROLLER.md:118-119,313-316`; `docs/ARCHITECTURE.md:160-163`;
    `docs/architecture.json` `sbpl_check` Lifetime (`:551`) and T12 label
    (`:981`).
  - Unchanged: shape goldens (`tests/fixtures/contract/envelope_shape.json`,
    `surfaces/envelope.json`, `surfaces/policy.json`), `tests/lib/consumer.py`,
    `docs/limits.json` values.
- A check must reject: a helper input equal to the held string for a request
  with an `actors` array; a dropped, reordered or misattributed per-actor
  capture; loss of the ordinary whole-request call or a change in its bytes;
  omission of the `policy_check` key.

**1B. Keep the call; state its consequence.** Reasoned retention.

- No source change. Add to `40-envelope.surface.md` `data.policy_check` and
  `11-policy.surface.md` `fallback.classify` the sentence in section 4
  (DT-42.a, alternative). Correct the README, CONTROLLER, ARCHITECTURE and T12
  wording from "checks the held whole request" to "delivers the held whole
  request to the helper".
- The two actor tests must stop asserting `unavailable` as the whole-request
  status (build input).
- Consequence: every actor-form fallback keeps one helper launch, one delivery
  of the whole request and one `tool_error` capture that concerns no policy.
  A check must reject a statement or test that presents that capture as a
  helper fault or as a compile result.

**1C. Remove actor automatic compilation entirely** (the acceptance plan's
rehearsed hypothetical; not selected there).

- Presence. `policy_check` present and null for actor requests;
  `actor_policy_checks` never emitted, so the field and `rust.ActorPolicyCheck`
  leave the record definitions. This is a shape change.
- What a user loses. Every independent per-actor compile capture and helper
  import inventory after an `xpc_error`. Standalone `sbpl-check` remains, but
  the envelope publishes only hashes of each resolved actor policy, not its
  text: a user must rebuild each spliced source (source, newline, augment
  files in order) to give the helper the same bytes.
- Files that change together. Product, build input: `run_flow.rs` (`:44-64`,
  `:374-394`, `:623-643`, `:720-724`, shape fixture `:4176-4184`). Statements:
  delete subject `policy.actor_check` (`11-policy.surface.md:706-730`) and its
  entry in `docs/contract/presentation.json:130`; field
  `40-envelope.surface.md:157-162`; `42-dossier.surface.md:17,40,83,92`;
  `11-policy.surface.md:699` (source citation `let actor_policies:`);
  `controller/README.md:5-8,173-175`; `docs/CONTROLLER.md:118-119,313-319,412,421-423`;
  `docs/ARCHITECTURE.md:160-167`; `architecture.json` `sbpl_check`, T12, B9;
  `docs/limits.json:1646,1858`; the three actor sentences in the
  `docs/LIMITS.md:76-82` shared region, removed in the owner while the guide's
  copy and guide lines 861–864 stay frozen and diverge. Goldens through
  `--refresh-shapes`: `tests/fixtures/contract/envelope_shape.json`,
  `surfaces/envelope.json`, `surfaces/policy.json`. Tests: both actor fallback
  tests are rewritten to assert absence.
- A check must reject any helper launch for a request with an `actors` array.

Weighing. The root principles say an independent compile is not evidence of
worker progress and must not explain a lost reply. All three alternatives keep
that. They differ in what an actor-form user retains after a transport
failure: under 1A everything that concerns an actor's policy; under 1B the
same plus a capture that concerns no policy; under 1C nothing automatic, and
the resolved policy text is not in the envelope to compile by hand.

### Decision 2: unreachable states

**2a. The admitted-without-host-reply row (DT-113).**

- Delete. Product, build input: `controller/src/interface/result.rs` (label,
  row), `run_flow.rs` (`admit_reply`, `complete_execution`),
  `runner_client.rs` (the parser would have to return the reply inside its
  no-failure result so the state is unrepresentable),
  `runner_commands.rs:531-545,975`; `controller/interface/cards.rs:136-142`.
  Regenerate `controller/interface/inventory.json`, `joins.json`,
  `residue.json`; record the mutation in `controller/interface/mutations.json`;
  update `controller/integration/interface_cases.json` (three stored `help
  result` outputs). The `help result` card loses a line, which is a public CLI
  text change. Statements: `40-envelope.surface.md:143-145,242`,
  `50-installation.surface.md:97`, `docs/RESPONSE.md:88-90`. Tests:
  `each_result_class…` row, the reply-less row of
  `execution_envelopes_preserve…`, `admit_reply(&intact, None)`,
  `verification_projects_only_current_replies`.
- Keep as defensive code and say so (recommended). `select` is total over its
  disposition type and the build script requires every class and host label to
  have a row (`result.rs:234-236`). Correct the two sentences that say the
  state can occur, qualify the classification row and the verify clause, and
  narrow the tests' credit. No build input changes unless the supporting
  control below is added.
- Keep as is. Leaves two sentences that describe a completion no input
  produces, and a reading rule that misdirects a reader looking for the source
  of `no_worker`.

**2b. The typed-version foreign branch (DT-114).**

- Delete `ReplyVersion::Unsupported` and the comparison at
  `run_flow.rs:100-102,343-349` and verify's arms. Build input; the typed
  value would then carry no second identity check.
- Keep as defensive code (recommended). It is the typed gate the controller's
  working rules ask for ("Gate replies before interpreting fields under an
  admitted producer"). Correct `controller/README.md:185-190` and
  `40-envelope.surface.md:251`; rebuild the "previous" and "next" rows of
  `refused_reply_versions…` in the production shape; leave the typed gate's
  own unit tests (`reply_versions_are_gated_exactly`,
  `compiled_profile_context_is_gated_after_the_response_version`) as the
  function-level controls they are.
- Decode foreign frames to make the README true. Rejected: it contradicts
  `porcelain.rs:172-173` ("A foreign producer cannot turn malformed descendant
  bytes into shape claims") and the working rule against recovering semantic
  claims from unsupported bodies.

**2c. Fallback calls on the admitted branch (DT-116.a).**

- Delete (recommended). `run_flow.rs:699-701` cannot run for any value, not
  only for parser-produced ones. Pass `None` for both fields. Build input; no
  behavior change; no fixture depends on it.
- Keep. Preserves code that suggests fallback and diagnostics can share an
  envelope, which the README and ARCHITECTURE then repeat.

### Decision 3: constructed combinations and their credit (DT-115, DT-118)

| Test or control | Credited with | Narrowing |
| --- | --- | --- |
| `each_result_class_agrees_in_fields_process_status_and_card` | `architecture.json:3091-3119` (interface definitions); `mutations.json:169`; CHANGE-VERIFICATION "result-class unit test" | Keep its claim: each row's fields, process status and card line agree. Build refusal rows in the shape the parser produces (no typed reply beside a capture or reply refusal or a delivery failure; the foreign row as `runner_reply_error` with the contract refusal and no reply). Keep the reply-less admitted pair only as the row's totality sample, labelled as a typed construction no client output produces. Build input. |
| `delivery_failure_takes_precedence_and_retains_the_client_frame_unread` | nothing outside its name | Keep the delivery assertions. Label `admit_reply(&intact, None)` and the typed foreign text as typed-gate facts or move them beside `reply_versions_are_gated_exactly`. Render through `tool_error` or `select`, not a hand-built result. Delivery precedence through real bytes is carried by `runner_client.rs:1391-1407` and `:1542-1567`. Build input. |
| `refused_reply_versions_request_no_fallback_compilation` | T12 (`architecture.json:977-1004`) | Its claim is the invocation rule: no helper for a refused or admitted host reply; one capture for a client `xpc_error`. Rebuild "previous" and "next" as host-frame refusals with a null `runner_result`. Bind a recording helper dependency so "requested" is observed, not inferred from an `unavailable` capture. Remove it from T12's actor-association credit. Build input. |
| `fallback_compilation_is_requested_only_for_an_admitted_xpc_error` | `11-policy.surface.md:703`; `architecture.json` `sbpl_check` (`:563-568`), T12, B9 | Its claim is eligibility. It supports "spawn only for an admitted client terminal xpc_error". It does not support "held-request diagnostic", "associated with the selected policy/actor" or "nested unchanged". Correct those credits in `architecture.json`. No source change needed for the narrowing. |
| `policy_check_controls` with `envelope_skeleton` | `helper_envelope` and B9 (`architecture.json:1396-1425,1983-2011`); `tests/suites/blackbox_e2e/README.md:217-222` | Its claim is the consumer's helper-envelope admission, which the suite README states accurately. Build the surrounding envelope in the shape production gives a fallback: null `runner_result`, capture terminal `xpc_error`, result `xpc_error`. Drop the association credit from B9. Not build inputs (`tests/lib/blackbox.py`, `checker_controls.py`). |
| Typed `xpc_error` capture `test_capture_bytes(None)` and the review's constructed capture | fallback tests above; `runner_client.rs:1409-1416` | Supports: the controller accepts such a capture, selects `xpc_error` and finds it eligible. Does not support: that the shipped client emits it. That rests on `runner_unit/client_session_controls` (constructed connection), on opt-in `runner_byoxpc/reservation_controls` and on the one local native run. `11-policy.surface.md:702` already says "no execution credited". |
| Field-complete shape fixture | shape golden only | None. |

A stronger mechanism for the orchestration tests, optional: expose the capture
frame builder of `runner_client::binary_tests` (`runner_client.rs:1142-1236`)
as a `#[cfg(test)] pub(crate)` helper and bind the client dependency to
`parse(capture_bytes)`. Rows then pass through the real parser, and a
combination the parser cannot produce cannot be written by accident. Build
input; larger than the row-by-row narrowing.

### Decision 4: `result.error` precedence and collection-bound support (DT-32)

- Precedence statement. Correct `40-envelope.surface.md:112-117` (text in
  section 4). Not a build input. Optional, in the same rebuild as other
  `run_flow.rs` edits and with no observable change: delete the two client
  arms at `run_flow.rs:763-766`. If they stay, they are defensive code the
  statement no longer describes.
- Collection bound, account. Rewrite the support owner's `pins` and `limits`
  at `41-diagnostics.surface.md:327-329` to say what the two controls call and
  that the run-level refusal is source-read. Owner-only; leaves the public
  payload unchanged.
- Collection bound, coverage. Add an over-capacity typed reply to the
  run-level orchestration control that already drives `admission_problem`
  through `run` (`compiled_profile_labels_determine_the_public_admission_outcome`,
  `run_flow.rs:2967-3013`), asserting `malformed_runner_response`, exit 1, the
  retained reply, the present-and-null diagnostics key and no fallback. A
  typed reply is adequate here: an over-capacity decoded reply is producible
  from bytes. Build input. It must reject a controller that publishes
  `withheld`/`reply_capacity` diagnostics, or admits the reply, on `run`.
- Label-effect notation. Change `35-profile.surface.md:334` to the effects
  `41-diagnostics.surface.md:355` already states. Structured public content;
  not a build input.

## 4. Recommended disposition per claim

"No further evidence would change this" is abbreviated NFE with its reason.
Case identifiers are from `tests/catalog.json`.

| id | disposition | reason | check, or NFE |
| --- | --- | --- | --- |
| DT-31.a, DT-113.a–d, Q1.c | Reasoned retention of the row as defensive code; correction of the account in its owners (decision 2a, keep). | The row makes selection total; deleting it rewrites three controller modules, the interface inventory, the mutation record and the public result card for no observable change. Two sentences are false as written. | New control in `runner_client.rs` binary tests: over the existing capture corpus, a typed reply is returned exactly when `failure()` is `None` (`unit/rust.unit`; build input). It must reject a parser that reports no failure and returns no reply. NFE on reachability itself: it is a universal negative settled by the caller trace. |
| DT-31.b, DT-114.a, DT-114.d, DT-114.e, Q1.d | Correction of the account (`controller/README.md:185-190`; `40-envelope.surface.md:251`). No behavior change (decision 2b, keep). | The decoder never yields a foreign typed reply; the README says it does. | Existing: `unit/rust.unit` (`producer_gate_precedes_malformed_descendants_and_keeps_raw_bytes`, `host_frame_naming_another_schema_is_a_version_refusal_with_bytes_retained`); opt-in `runner_byoxpc/reservation_controls` (`old_response`). |
| DT-31.c | No change. | Superseded by DT-113 and DT-114. | NFE. |
| DT-32.a, DT-119.c | Correction of the support account now; coverage repair with the `run_flow.rs` batch (decision 4). | The cited controls assert a diagnostics value that `run` never publishes. | New row in `compiled_profile_labels_determine_the_public_admission_outcome` (`unit/rust.unit`; build input). Accepted limit until then, in the owner's `limits`: "No control carries an over-capacity reply through `run` or `runner verify`; the run-level refusal and null diagnostics follow from the cited admission branch." |
| DT-32.b, DT-119.b | Correction of the account (`40-envelope.surface.md:112-117`); optional deletion of the two dead arms. | The statement lists tiers that cannot be selected. | Proposed text: "Human-readable diagnostic, null on successful controller/helper results. A refusal carries the refused boundary's diagnostic. After execution admission it is the host reply's `error` when present, otherwise a generic unsuccessful-run message; client `stdout_capture_error` and `stdout_parse_error` accompany only refused captures." Add an assertion of the generic message for an admitted non-`finished` reply without `error` (`unit/rust.unit`; build input). It must reject a client stdout diagnostic in `result.error` of an admitted run. |
| DT-32.c, DT-119.d | Correction of the account: make `35-profile.surface.md:334` use `set_value(envelope.result.exit_code, 1)` and `set_value(envelope.data.runner_sandbox_diagnostics, None)`. | One path, two notations; the key is present with null. | Existing `compiled_profile_labels…` asserts exit 1; add a key-presence assertion there (build input). `source_drift/build_contracts` holds the regenerated tree. |
| DT-42.a, Q3.c, DT-117.d, DT-117.h (whole-request part) | Product behavior change 1A (recommended). If declined: 1B with this sentence beside `data.policy_check`: "For a request that carries `actors` and no top-level `policy` object, which is every actor request the host admits, this capture is `tool_error` with helper exit 2 and the decoder's message in `stderr`: the helper could not decode a top-level policy. It reports no compilation; the per-actor captures do." | A call that can only fail to decode yields a capture unrelated to any policy and reads as a fault. The rebuild is already required by the selected test correction. | Helper side, existing: `integration/cli.integration` row "request without a policy on stdin"; add an actor-form row (not a build input). Mapping, existing: `policy_check::tests::empty_stdout_is_a_tool_error_regardless_of_exit_code`. Controller side: section 6.1 controls (`unit/rust.unit`). |
| DT-42.b, DT-117.g | Correction of the account in `11-policy.surface.md`. | The field texts omit two cases that share the value 1. | Proposed `tool_exit_code`: "Helper process exit code. It is 1 when the process status supplies no numeric exit code, as after termination by a signal, and 1 for an `unavailable` capture; `status` and the retained streams distinguish these." Proposed `stderr`: "Retained stderr text, including diagnostic output when the helper produced no envelope. For an `unavailable` capture it holds the controller's launch or delivery diagnostic, and the byte counts are null." NFE: `policy_check.rs:34-41,78` and B4u/B4s agree. Accepted limit, same place: a helper delivery failure is reported as `unavailable` and the helper's own output is not retained. |
| EV.a–EV.h | No change. | Records of what the review executed. | NFE. Availability: local only; made under another build identity. |
| Q1.a, Q1.b, Q2.a–Q2.c, Q3.a, Q3.b, Q3.d, Q3.e | No change to behavior. Q3.b gains a control (section 6.1, item 5). | Accurate. | Existing: `unit/rust.unit`. |
| DT-113.e | Assertion and credit repair (decision 3). In `tests/FAILURE-PROPAGATION-CONTRACT.md:687`, name what crosses: "Constructed replies cross production completion and rendering". | The reply-less row is a typed construction; `execution_envelope` is a test helper. | `source_drift/generator_contract` for the document; `unit/rust.unit`. |
| DT-113.f | No change. | The join README already says the list reports retained cases only. | NFE. |
| DT-113.g, LIM.f | No change. | History; no decision depends on it. | NFE. |
| DT-114.b | Reasoned retention (decision 2b). | Defensive typed gate. Accepted limit, for `controller/README.md`: "A second comparison of the decoded reply's producer contract follows decoding; it cannot refuse a frame the decoder accepted." | NFE. |
| DT-114.c, DT-114.g, DT-114.h | No change. | Accurate. | Opt-in `runner_byoxpc/reservation_controls`. |
| DT-114.f | Assertion repair: assert the production text where a host-frame contract refusal is constructed; label the typed text as the typed gate's. | The asserted message is one no envelope carries. | `unit/rust.unit` (build input). |
| DT-115.1, DT-115.2, DT-115.3, DT-115.4 | Assertion and credit repair as in decision 3. | Each is credited beyond what it constructs or asserts. | `unit/rust.unit`; `blackbox_e2e/checker_controls`; `source_drift/architecture_documentation`. |
| DT-115.4 (consumer and `actor_policy_checks`) | Not decided here; see section 7. Until decided, narrow B9 to the ordinary capture. | Extending the consumer is new coverage, not a correction. | — |
| DT-115.5 | No change. | Labelled shape fixture. | NFE. |
| DT-116.a | Product source cleanup with no behavior change (decision 2c, delete). | Dead for every value. | Existing rows "host-ok" and "host-xpc-error" of `actor_fallback_preserves…` (no helper input on an admitted reply). |
| DT-116.b, DT-116.d | No change. | Accurate; DT-116.d is already stated in the failure contract. | `runner_unit/client_session_controls`. |
| DT-116.c, DT-116.e | Reasoned retention of `xpc_error`-only eligibility, with the limit stated beside `fallback.classify`: "Eligibility follows the client's terminal event only. It does not classify whether the specimen ran: an invoked `xpc_timeout` has no fallback capture, and an eligible `xpc_error` can follow a submission call that sent no request." Correct the noun in `controller/integration/cli_contract.rs:1296-1297`. | No decision in this thread widens or removes ordinary fallback; the limit is what a reader needs. | NFE: d2, r2 and the session control at `PWRunnerClientSessionTests/main.swift:158-167` already show both directions. |
| DT-116.f | Correction of the accounts: `11-policy.surface.md:392`; `controller/README.md:232-235`; `docs/ARCHITECTURE.md:462-465`. | They describe a pairing and an assembler that do not exist in production. | Proposed 11-policy sentence: "The fallback capture reports this independent attempt beside the client transport capture; an envelope that carries a fallback capture carries no host reply and no execution diagnostics." Proposed README sentence: "`execution_parts` joins the dossier, transport and acquisition history with the execution diagnostics. Independent fallback compilation is attached only to a refused `xpc_error` capture, which carries no diagnostics." `source_drift/build_contracts`, `source_drift/generator_contract`. |
| DT-116.g | Correction of the account, `docs/ARCHITECTURE.md:467-468`: "The client's timeout ends the controller's wait; the admitted capture records terminal `xpc_timeout` and `runner_result` is null." | No reply is synthesized. | NFE: d1, d2 and `runner_client.rs:642`. |
| DT-116.h | Correction of the account, `40-envelope.surface.md:251-252`. | Two readings are possible; one behavior. | Proposed `free.condition`: "Check request delivery error first, then client failure (capture admission, host frame admission including its schema fingerprint and producer contract, and transport terminal), then host capacity and profile-label admission of the decoded reply." Proposed last sentence of `free.effect`: "An accepted capture with terminal xpc_error and no delivery error adds independent fallback compilation." Existing: `runner_client.rs:1391-1407` (`unit/rust.unit`). |
| DT-117.a–c | No change. | Records. | NFE; local only. |
| DT-117.e | No change. | Accurate. | Section 6.1 controls. |
| DT-117.f | Reasoned retention. Accepted limit beside `actor_check.actor_id` (`11-policy.surface.md:715-717`): "A capture is associated with its actor by this label and by its position among the actors that carry a policy object; a null label is identified by position only." | The envelope carries no other key; adding one is a new field nobody asked for. | Section 6.1, item 3. |
| DT-117.h ("before host admission") | Correction in the four owners. `docs/LIMITS.md:77-78`: "These independent compile diagnostics do not depend on host admission; they do not establish application." `docs/ARCHITECTURE.md:164-165`: "Fallback does not depend on host admission, so the admitted actor-count bound does not bound the number of helper invocations." `architecture.json:551`: replace "potentially before host admission" with "host admission may not have occurred". `docs/limits.json:1646`: "Actor fallback does not depend on host admission and can accumulate more policies than the admitted actor count." | In the native run the helper ran after the host admitted the request. The supported claim is independence, not order. The LIMITS sentence is a shared region: this corrects a statement in its owner and adds nothing. | `source_drift/limits_documentation`, `source_drift/architecture_documentation`. |
| DT-117.i | Assertion and credit repair: section 6.1; T12 checks; `docs/limits.json:1881` to "Oversized input is tested through the shipped helper with a request file; the controller's fallback delivery of an oversized source and the exact boundary are source-inspected." | Credits exceed what the controls run. | `failure_boundaries/fallback_helper` keeps its stated claim (`tests/suites/failure_boundaries/README.md:47`). |
| DT-118.a | No change. | Record; see decision 3 for the in-tree analog. | NFE. |
| DT-118.b, DT-118.d | Reasoned retention. Accepted limit, to stand in `20-transport.surface.md` after `:574`: "Admission compares the capture and the host frame with the build contract and with their own retained-byte accounts. It does not compare either with the held request; their association rests on the one client invocation that read the held bytes." | No statement claims a comparison; the limit is real for anyone substituting the client or reusing captures. | NFE: B8 and the source agree; a comparison would be a new admission rule outside this thread. |
| DT-118.c | No change. | `20-transport.surface.md:492-494` describes the client's exit rule and claims no controller use. | NFE. |
| DT-119.a | Reasoned retention. Accepted limit, in the "Other admitted host label" row (`40-envelope.surface.md:243`): "A host label is copied without comparison with the controller's refusal spellings; a non-null `runner_result` with terminal `runner_reply` identifies a host-supplied label." | The shipped host emits none of the transport refusal spellings. | Existing typed assertion `run_flow.rs:3068-3076`. |
| DT-119.e | No change. | Stated and implemented alike. | `unit/rust.unit`; the build script's derived facts in `inventory.json`. |
| DT-119.f | Reasoned retention; the inference stays labelled. | Each observed link is covered by a unit control; the NSXPC link is not. | Existing: `runner_unit/pwrunner_core_unit_executable` (`ReplyFailureTests.swift:314-328`); `unit/rust.unit` (`runner_client.rs:1307-1322`). Optional: a session control delivering `(true, Data())` in `runner_unit/client_session_controls` (not a build input). The NSXPC step needs an executed fixture host; see section 7. |
| DT-119.g | Reasoned retention. Accepted limit, beside `error.reason` (`20-transport.surface.md:449-451`): "The capture readers also accept `interrupted` and `invalidated`; the shipped client reports a failed connection as `xpc_error` or `proxy_type_mismatch` and emits neither." | Two readers accept the values consistently; removing them changes admission for no observed case. | NFE. |
| PR.1–PR.13, PR.n1, PR.n2 | No change. | Re-verified row by row. | `unit/rust.unit`; geometry on PR.12 gains the DT-32.a row. |
| REL.a–REL.d | No change. | Accurate; the judgments stay judgments. | NFE. |
| LIM.a–LIM.c, LIM.e, LIM.g–LIM.i | No change. | Accurate limits. | NFE. |
| LIM.d | Coverage repair, optional: assert the ordinary fallback capture in opt-in `runner_byoxpc/reservation_controls` `lost_execution` (`policy_check.status == "ok"`, helper `policy_sha256` equal to the SHA-256 of the specimen's source, null diagnostics). | The case already produces the state through the shipped controller and observes an independent file effect of the execution. | `runner_byoxpc/reservation_controls` (opt-in; not a build input). |

## 5. Resulting user duties

Under the recommended dispositions an ordinary user must:

- After `xpc_error`, read `data.runner_client.submission` and the capture. Do
  not conclude from a present `policy_check` or `actor_policy_checks` that the
  worker ran, stopped or applied the policy, and do not conclude from an
  `ok` capture that the policy was applied. The native observation in the
  review shows a worker running its action while the envelope held only
  fallback results.
- Do not conclude from an absent fallback capture that nothing ran. An invoked
  `xpc_timeout` has none.
- For an actor request, read `actor_policy_checks`. Under 1A `policy_check` is
  null and is not a sign that fallback did not run. With the current app, and
  under 1B, a `policy_check` of `tool_error` with exit 2 on an actor request is
  the helper declining an input with no top-level policy. It is not a helper
  or controller fault and says nothing about any actor's policy.
- Match an actor capture to its actor by `actor_id` and by order among the
  actors that carry a policy object. A null label is identified by order only.
- Do not read `tool_exit_code: 1` as the helper's own exit status without
  `status`: `unavailable` and death by signal carry the same value.
- For `unsupported_runner_response`, expect a null `runner_result`. The
  refused host bytes are in `data.runner_client.transport.runner_reply`,
  uninterpreted.
- Do not plan for `runner_response_unavailable` from `run` or `runner verify`.

Nothing else. A user who replaces the client or replays captures takes on the
association between request, capture and reply, which the controller does not
check.

## 6. Implementation worklist

### 6.1 The selected `run_flow.rs` test correction

All four tests are in `controller/src/run_flow.rs` (build input). For each:
the assertion that fuses helper invocation with provenance or attribution, and
the independent observation that should carry the provenance claim.

1. `actor_fallback_uses_held_policy_objects_before_host_mode_admission`
   (`:3113-3234`).
   - Fused: `*helper_inputs == vec![inputs[0], {"policy": last}, …]`
     (`:3199-3208`) states at once that five calls happen, that the first is
     the whole request, the call order, and each input's bytes.
     `checks.len() == 4` (`:3210`). Every call returns `Err`
     (`:3172-3175`), so all captures are identical and no assertion can tie a
     capture to an input; `policy_check.status == "unavailable"` (`:3228`) is a
     property of the substitute.
   - Provenance should rest on: (a) membership, not sequence: every recorded
     helper input is either byte-equal to the client's held string or equal to
     `{"policy": P}` for an independently authored `P`, and none derives from
     the file content written after the client call (`:3169`); (b) the
     duplicate-key case by content: the "future" actor's capture is the one
     returned for `{"policy": last}`; (c) request order from the envelope:
     the `actor_id` sequence of `actor_policy_checks`.
   - Invocation policy, separately: one assertion that the held string is, or
     is not, among the helper inputs for this form (it flips with decision 1);
     one that no helper input exists when a host reply was delivered
     (`:3194`).
2. `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`
   (`:3237-3406`).
   - Fused: the substitute answers by call index (`:3315-3335`), so "zeta is
     `ok`, alpha is `compile_error`" (`:3380-3398`) follows call order, not
     input. `*checks == vec![inputs[0], zeta, alpha]` (`:3368-3376`) fixes
     count, order and bytes together. `policy_check == outputs[0]` with
     `status == "unavailable"` (`:3378-3379`) asserts a status the shipped
     helper does not give for that input.
   - Provenance should rest on a substitute keyed by input bytes: a table from
     `{"policy": zeta}` (with the spliced augment, authored independently as
     at `:3268-3271`) to one capture and from `{"policy": alpha}` to another,
     with any other input recorded and answered distinctly. Then assert
     `actor_policy_checks == [{zeta, capture(zeta)}, {alpha, capture(alpha)}]`.
     This holds for any call count or order and fails for an unresolved
     policy, a reread file or a swapped association.
   - Invocation policy, separately: no helper input for the four ineligible
     labels (`:3400`); the whole-request presence assertion as in item 1.
   - Noted while listing: the "delivery-failed" label sets a delivery error on
     a capture that keeps accepted admission and a typed `xpc_error`
     (`:3299-3301`). The parser cannot produce that; build it as
     `delivery_failure_takes_precedence…` does (`:1977-1983`). B7 is the
     real-bytes observation.
3. `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`
   (`:2040-2135`).
   - Its counts (`invoked == 1`, `invoked == 0`) are invocation policy and
     nothing else: the closure receives no input. Leave the assertions. The
     conflation is in the credits (`architecture.json` T12 and B9;
     decision 3). Render its envelope through `select`, not the hand-built
     result at `:2117-2120`.
4. `refused_reply_versions_request_no_fallback_compilation` (`:3016-3110`).
   - "Requests the fallback compiler once" (`:3078-3079`) is inferred from an
     `unavailable` capture whose `stderr` names `sbpl-check` (`:3093-3099`),
     which depends on the helper being absent beside the unit-test binary. No
     helper call or input is observed.
   - Bind a recording helper dependency. Provenance: the envelope's
     `policy_check` equals the capture returned for the input that is
     byte-equal to the client's held string. Invocation: the recorded input
     list is empty for every refused or admitted reply row.
5. New, required by decision 1A or 1C and useful in any case: an ordinary-form
   control. Bind recording client and helper dependencies; replace the request
   file inside the client callback; assert the helper input is byte-equal to
   the client input, that it parses to an independently authored expectation
   including a spliced augment, and that the envelope's `policy_check` is the
   capture returned for that input. Suggested name:
   `ordinary_fallback_receives_the_held_request_after_the_file_is_replaced`.

Client-invocation counts elsewhere (`observed.calls.len() == 1`,
`inputs.len() == 1`) assert the one-submission commitment and are not part of
this correction.

Where a claim is "present with null", assert the key
(`wire["data"].get("policy_check") == Some(&Value::Null)` or the `DATA_KEYS`
comparison), not `wire["data"]["policy_check"].is_null()`.

### 6.2 Ordered edits

Step A. Accounts and non-build tests. No rebuild; may land before the source
batch. Items marked (1A) wait for the product change and land with it.

1. `docs/contract/40-envelope.surface.md`: `result.error` (`:112-117`);
   `data.runner_sandbox_diagnostics` (`:141-145`) to "Assessments after
   client/reply admission. Null for earlier refusals and tool errors. An
   admitted reply with no worker subprocess record has the no-worker
   assessment."; classification row (`:242`) to "`runner_response_unavailable`
   | Selected for an admitted completion that carries no host reply; exit 1.
   No client output reaches this row: capture admission yields a decoded host
   reply whenever it reports no failure."; row `:243` limit (DT-119.a);
   `admit` (`:251-252`); (1A) `data.policy_check` (`:152-155`) to "Independent
   helper capture of the held whole request after an eligible admitted
   client-terminal `xpc_error`, for a request without an `actors` array. Null
   when fallback was ineligible or the request carries an `actors` array."
2. `docs/contract/11-policy.surface.md`: sentence at `:392`; `tool_exit_code`
   (`:628-630`); `stderr` (`:672-674`); eligibility limit under
   `fallback.classify` (`:692`); `actor_check.actor_id` limit (`:715-717`);
   (1A) `fallback.classify` `free.effect` (`:688`): after "terminal
   xpc_error." read "For a held request without an `actors` array, deliver the
   held request on stdin; a request with an `actors` array receives only the
   per-actor checks."; support `check` list (`:703`) gains the item 5 control.
3. `docs/contract/35-profile.surface.md:334`: effects as decision 4.
4. `docs/contract/41-diagnostics.surface.md:327-329`: support `pins` and
   `limits` as decision 4.
5. `docs/contract/42-dossier.surface.md`: (1A) `collection.held` `free.effect`
   (`:36`) to "…use those bytes for client delivery and, for a request without
   an `actors` array, whole-request fallback compilation."; support `check`
   (`:92`) gains the item 5 control; `limits` (`:93`) says the client input is
   compared by value with an independent expectation and by bytes with the
   helper input.
6. `docs/contract/50-installation.surface.md:97`: after "an absent reply
   selects runner_response_unavailable and no PID" add "; capture admission
   supplies a decoded reply with every admitted capture, so no client output
   selects it".
7. `docs/contract/20-transport.surface.md`: limits after `:574` (DT-118.b) and
   at `:451` (DT-119.g).
8. `docs/RESPONSE.md:88-90` (hand-authored, outside the generated regions):
   "Null `runner_sandbox_diagnostics` accompanies earlier refusals and tool
   errors. An admitted reply with no worker subprocess record has a no-worker
   assessment. A withheld assessment has its own supporting findings."
9. `controller/README.md`: `:185-190` to "A host frame naming another schema
   fingerprint or another producer contract produces
   `unsupported_runner_response`; the frame is not decoded and
   `data.runner_result` is null. Host bytes that are not one complete typed
   record produce `malformed_runner_response` with a null `runner_result`. A
   decoded reply that fails capacity or compiled-profile label admission
   produces `malformed_runner_response` with the decoded record in
   `data.runner_result`. Each exits 1 and withholds runner-derived
   diagnostics."; `:232-235` (DT-116.f); (1A) `:5-8` to "When fallback
   compilation is eligible, it checks the held whole request for the ordinary
   form and, for the actor form, each carried actor policy object in request
   order, without knowing whether the host admitted the request or its sandbox
   modes (`data.actor_policy_checks[]`)."; `:173-175` to match the corrected
   tests.
10. `docs/CONTROLLER.md`: (1A) `:118-119` and `:313-316`.
11. `docs/ARCHITECTURE.md` prose: `:160-167` ((1A) for the whole-request
    sentence; the "host admission" sentence now); `:462-468`.
12. `docs/architecture.json`: `sbpl_check` Lifetime (`:551`); T12 label and
    checks (`:977-1004`): drop the association credit from the two cited
    tests, add `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence`
    once corrected; B9 label (`:1987`) to "nested unchanged; admitted by kind
    and frame version; per-helper retention is not a cumulative envelope or
    memory bound"; `helper_envelope` Form (`:1401`) to "…independently
    compiled diagnostic for the delivered policy input, not application
    evidence".
13. `docs/limits.json`: `:1646`, `:1881`. `docs/LIMITS.md:77-78` in the shared
    region.
14. `tests/FAILURE-PROPAGATION-CONTRACT.md:687`.
15. `tests/lib/blackbox.py` and `tests/suites/blackbox_e2e/checker_controls.py`:
    a fallback-shaped skeleton (null `runner_result`, terminal `xpc_error`
    with its error record) for `policy_check_controls`.
16. `controller/integration/cli_contract.rs`: an actor-form row in
    `sbpl_check_argument_and_request_failures_exit_2_without_an_envelope`;
    comment at `:1296-1297` to "reserved for an admitted client `xpc_error`".
17. Optional: `tests/suites/runner_byoxpc/opt_in/reservation_controls.py`
    `lost_execution` assertions (LIM.d); a zero-length result control in
    `runner/Tests/PWRunnerClientSessionTests/main.swift`.

Step B. `controller/src` batch. Every item is a build input; land them
together for one signed rebuild.

1. Tests first, against current behavior (the management plan's rule where
   test authority and product behavior both change): section 6.1 items 1–5
   with the whole-request assertion expecting presence; decision 3 rows; the
   DT-32.a over-capacity row; the generic-message assertion; the parser
   equivalence control in `runner_client.rs`.
2. Product: delete `run_flow.rs:699-701` and pass `None` (2c). Optional:
   delete `run_flow.rs:763-766`.
3. Product (1A): in the refused branch (`:715-724`) skip
   `fallback_policy_check` when the held value's `actors` member is an array;
   flip the one whole-request presence assertion.
4. `tests/suites/unit/README.md:25-39` if a described test changes.

### 6.3 Regeneration

After Step A and again after Step B, in this order, then check every owner:

```sh
tests/lib/python.sh docs/generate_limits.py
tests/lib/python.sh docs/generate_architecture.py
tests/lib/python.sh docs/generate_contract_stamps.py
tests/lib/python.sh docs/generate_limits.py --check
tests/lib/python.sh docs/generate_architecture.py --check
tests/lib/python.sh docs/generate_contract_stamps.py --check
```

No shape refresh under the recommendations. Alternative 1C needs
`docs/generate_contract_stamps.py --refresh-shapes` and a review of
`tests/fixtures/contract/envelope_shape.json`. Alternative 2a "delete" needs
`docs/generate_interface.py --refresh-inventory` and a mutation record.

### 6.4 Routed verification

- Step A: `source_drift/limits_documentation`,
  `source_drift/architecture_documentation`, `source_drift/build_contracts`,
  `source_drift/generator_contract`; `blackbox_e2e/checker_controls`;
  `integration/cli.integration` (signed app) for item 16.
- Step B, after the signed rebuild, per the controller's verification table
  (`controller/AGENTS.md`, "Rust helpers, orchestration or formatting",
  "Public CLI arguments and envelope behavior", "Request/reply admission or
  evidence interpretation"): `unit/rust.unit`, `unit/rust.fmt`,
  `integration/cli.integration`, the `failure_boundaries` suite,
  `blackbox_e2e/checker_controls`, and the `source_drift` cases above.
- `tests/CHANGE-VERIFICATION.md`, "BYOXPC reservation and lost-reply
  controls": run `runner_byoxpc/reservation_controls` if item 17 lands or to
  observe 1A's ordinary-form fallback through the shipped controller.
- `tests/CHANGE-VERIFICATION.md`, "Interface definitions and help cards":
  only if `controller/src/interface/result.rs` changes, which the
  recommendations avoid.
- The rebuilt app joins the thread's grouped signed-app verification in the
  management plan's sequence.

## 7. Not decided here

- **Whether the independent consumer should admit `actor_policy_checks`
  captures.** `tests/lib/consumer.py:343-345` routes only
  `data.policy_check.envelope` to helper-envelope admission; an actor capture
  gets shape checks only. Extending it is new coverage. Missing: a statement
  of whether the consumer is meant to be the independent reader for actor
  captures. Until then B9's credit is narrowed to the ordinary capture.
- **External reliance on a non-null `policy_check` for actor requests.** The
  behavior shipped in v0.3.5–v0.3.7. Nothing in the tree reads it that way. I
  cannot see users' readers. This is the one input that could favor 1B over
  1A.
- **Whether NSXPC delivers a zero-length reply as empty data** (DT-119.f).
  Unverifiable by reading. It needs an executed fixture host that replies with
  empty data. No disposition above depends on the answer.

## Outside the review

Noticed while tracing; none is added to the review.

1. The capture has the same duplicated identity check as the host frame.
   `decode_bound(retained, true, …)` compares the capture's contract before
   decoding (`porcelain.rs:199-220`), so the comparison at
   `runner_client.rs:727-736` cannot refuse. B5b's retained error text is the
   decoder's ("unsupported producer contract …"), not that branch's. Same
   treatment as decision 2b: defensive code; no statement depends on it.
2. `serde_json` indexing returns null for a missing key, so the many
   `wire["data"][…].is_null()` assertions in `run_flow.rs` hold for an absent
   key as well. Key presence on refusal envelopes is asserted only where
   `keys(&wire["data"]) == DATA_KEYS` is used (`:1009`, `:2019`). This matters
   for asserting decision 1's presence consequence.
3. No Rust test observes the helper's input for an ordinary request. The
   helper dependency is bound only in the two actor tests (`:3181`, `:3351`).
   The ordinary route is supported by the same line of code and by the local
   C case B4i. Section 6.1 item 5 closes this.
4. No test asserts the generic unsuccessful-run message (`run_flow.rs:768`).
5. `fallback_compilation…` renders with a hand-built result (`:2117-2120`),
   like the instance DT-115.2 names. The controller's working rules give
   result selection one owner.
