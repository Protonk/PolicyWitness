# I-receipts — compiled-profile receipts (DT-95–104, DT-134, receipt side of both import/receipt investigations)

Read-only assessment at HEAD `837296af`, 2026-11-17. No tracked file was changed,
nothing was built and no test, `cargo`, `swift` or `policy-witness run` command ran.
Checks made here were file reads, read-only git, re-reading retained run artifacts
and three in-memory digest computations through `tests/lib/python.sh -I`.

## 0. Orientation

### What changed since the review's snapshot

The receipt entries were written at `eccd5de9`. `git diff --stat eccd5de9 HEAD`
over `runner/Sources/PWRunnerCore/CWorker.swift`, `controller/tools/pw_probe_runner`,
`controller/src`, `runner/Tests`, `tests/lib/consumer.py`,
`tests/suites/runner_outcome_bad_request`, `tests/suites/witness_contract`,
`tests/fixtures/contract` and `docs/contract/35-profile.surface.md` shows two files,
four lines each: the generated worker ABI identity in `CWorker.swift:52-53` and
`pw_probe_runner_abi.h`. Every receipt line number the review cites for those
files still lands on the same text; the citations below were each re-read.

### Evidence codes used in the tables

| Code | Meaning |
| --- | --- |
| SRC | The review read source; re-read now at HEAD at the cited `file:line`. |
| EXE-L | The review executed a live probe against the `8b5de2b2` app. Raw output is **absent**: the scratchpads `0a1dcc1e-…` and `8e36ddab-…` under `/private/tmp/claude-501/…` no longer exist, and `tests/out/runs/profile-receipt-trace` (run `20261116T192345Z_79fbbaf4`) is not present. The review's tables and `.tmp/82-103-OBSV.md` / `.tmp/SHARED-INTERP-FOLLOW-UP.md` are accounts, not replayable observations. |
| EXE-C | The review executed a constructed input (unit test, edited saved reply, seam row). |
| RET | Re-observed now in a locally retained development run: `tests/out/runs/trace-instrument-after-corrected`, run `20261118T011154Z_5cfcec0a`, app `dist/PolicyWitness.app` at commit `2f4d76e4`, contract `development:b55acb20…744719e`. Disposable development output, not release evidence. `unit/rust.unit`, `runner_unit/pwrunner_core_unit_executable`, `runner_outcome_bad_request/accepted_input_contract`, `runner_abi_layout/c_swift_layout_agreement`, `blackbox_e2e/checker_controls` and `witness_contract/max_targets_reply_survives` each report `pass` with `system_sleep_ms` 0. |
| CALC | Recomputed now from constructed in-memory input. |
| SEAM | Retained seam rows at `.tmp/contract-trio/acceptance/corpus/analysis.txt:20-24` (gitignored; produced through a path that bypasses `reply_contract`). |

Classification abbreviations: **CEC** contradicted explicit commitment; **CA**
consequential ambiguity; **UI** unsupported inference; **IMA** inaccurate mechanism
account; **OCC** overstated coverage credit; **AO** accurate observation needing no
change.

### What RET re-shows (values read from `…/accepted_input_contract/artifacts/`)

- `corpus-cli-capture/run.json`, `repair-cli-capture-2-enabled/run.json`,
  `repair-xpc-capture-2-enabled/reply.json`: `captured`, 492 bytes, digest
  `b2056ef2…97e0`; decoded length and SHA-256 recomputed equal; `request_nonce`
  equals the specimen's nonce (three different nonces, identical bytes);
  `source_sha256` `c3f48dc8…74b3` equals the SHA-256 of the specimen source and the
  reply's `policy_sha256`; `source_length` 27; `params_sha256` `df3f6198…1119`;
  `worker_pid` equals `runner_subprocess.pid`; key set is exactly the thirteen
  captured keys (no `reason`).
- `capture_worker_death/run.json`: receipt is exactly
  `{reason: worker_not_complete, status: unavailable, worker_pid: 22384}`, beside
  `sandboxed_after_apply: true` and `term_signal: 9`.
- `unit/rust.unit/artifacts/cargo-test-bins.log:154,173,213`: the three Rust
  receipt tests `ok`. `runner_unit/…/pwrunner_core_tests.log:984-1004`: twenty
  tests `ok` in "Compiled-profile capture: bounded worker receipt"; line 831:
  "production C apply failure preserves actual return and errno" `ok`.

CALC: SHA-256 of four zero bytes is `df3f6198…1119`; the documented framing over
`ROOT=/etc`, `Z=é` gives `2a4f1d69…95fd` (the review's B2 value); the cited
Rust test's request source is 28 bytes, `d130f968…765c`.

---

## Subject 1 — DT-95–104 and DT-134: host binding, the application/completion/publication guards, constant labels, input coverage, the capture view, test support

### 1.1 Claims table

Boundary is written as *input form; representation; observer; time*. "Disp."
names the disposition in 1.4.

#### Conventions

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| RC.a | Live observations used the `8b5de2b2` dist app; nothing was rebuilt. | ordinary form; signed app; reviewer; 2026-11-16 | Unverifiable by reading. The dist app now reports `2f4d76e4`; receipt product source differs only in generated identity lines. | EXE-L (absent) | AO | D-OBS |
| RC.b | Registered run `20261116T192345Z_79fbbaf4` passed three cases; Swift group 20/20; three Rust receipt tests `ok`. | constructed and live; dispatcher run; that date | Original run absent. The same cases and tests pass in RET. | RET | AO | D-OBS |
| RC.c | Probes A, B, B2: receipt absent when unrequested; captured receipts agree with request and reply on length, digest, source, parameters, nonce, PID; `consumer.admitted_reply` receipt equals the controller's JSON receipt. | ordinary; envelope JSON and retained host bytes; reviewer scripts; one run each | Partly re-observable: RET re-shows every comparison for three zero-parameter captures; B2's parameter digest reproduces by CALC. Probe A, B2's envelope and the admitted-reply equality are not re-observable. | EXE-L (absent), RET, CALC | AO | D-OBS |
| RC.d | Probe C uses the existing `worker_post_apply_kill_signal: 9` control; the registered case is the only ordinary-form live control asserting an `unavailable` receipt; no other guard was forced live. | ordinary; live; `contract.py` | Yes — `tests/suites/runner_outcome_bad_request/contract.py:498-512`; RET. "Only ordinary-form" holds by grep; the actor form has another (`check_actor_compositions.py:121-123`). The invocation is the "live self-signal case" in the seam caller map. | SRC, RET | AO | D-OBS |

#### DT-95 and its acceptance trace

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-95.a | `admission_problem` checks geometry, status vocabulary and the two labels; it compares no receipt field with the delivered request, `runner_subprocess.pid`, `policy_sha256`, the dossier or the receipt's own bytes. | `run`, `runner verify`; typed reply after binary decode; controller; reply admission | Yes — `controller/src/porcelain_admission.rs:1308-1331`; `controller/src/run_flow.rs:99-107`, `:330-355`, call site `:693` | SRC | AO; CA for a reader of `finished` | D-ADM |
| DT-95.b | The binary reader requires only `status` and `worker_pid` and accepts any subset of the other twelve fields. | host frame bytes; controller decode | Yes — `controller/src/porcelain_records.rs:51-104` (`:89`, `:91`) | SRC | AO | D-OBS |
| DT-95.c | Python `_validate_capture` / `admitted_reply` and Swift `contextProblem` apply the same three conditions. | envelope JSON, test consumer; typed reply, host before encoding | Yes — `tests/lib/consumer.py:575-588`, `:1049-1051`; `runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift:31-44` | SRC | AO | D-OBS |
| DT-95.d | The cited test's request has no capture fields; the fixture's `captured` row carries a nonce, `source_length` 24 against a 28-byte source, all-`f` source and parameter digests with `parameter_count` 0; it is admitted as `finished`, exit 0. | constructed typed reply read by the test's serde reader; production `run` orchestration with a substituted client | Yes — `run_flow.rs:2608-2623`, `:2967-3013`; `tests/fixtures/contract/compiled_profile.json` row `captured`; CALC | EXE-C; `ok` in RET | OCC (name, support pin and suite account do not say the accepted row is unrelated to the request) | D-FIX |
| DT-95.e | `typed_profile_context_gate_includes_actor_captures_and_degradation` asserts admission of a `captured` actor receipt with no nonce, type, length, bytes or digests. | constructed typed actor reply; `admission_problem` | Yes — `porcelain_admission.rs:2731-2782` (`:2762`) | EXE-C; `ok` in RET | AO | D-OBS |
| DT-95.f | Eleven separate edits of B's saved reply were accepted by `consumer.validate`; `status: "future"` and `producer: "host"` were rejected. | edited saved JSON; Python consumer, not the controller | Not re-executed (scripts absent). Consistent with `consumer.py:575-588` by reading. | EXE-C (absent), SRC | AO, limited to the Python reader | D-OBS |
| DT-95.g | No reader checks the two extent conditions or presence against the request; live tests assert them on their own outputs. | record conditions; no acting component | Yes — `docs/contract/35-profile.surface.md:73-77`, `:87-92` (no `who`); `contract.py:322-332`, `:430-435`, `:483-488`; `tests/suites/witness_contract/check_response_footprint.py:235-241`; `opt_in/guide_workflows.py:461-470`; also `check_actor_compositions.py:126-135` | SRC | CA (rendered as "Requires …" with no component that requires it) | D-ADM |
| DT-95.h | CONTRACT's checker index lists only the three label conditions; the extent conditions are credited only to the source-read owner over the Receipt subject. | generated RESPONSE/CONTRACT | Yes — `docs/RESPONSE.md:2554`, `:2560`, `:2616-2618`, `:2637` | SRC | AO | D-OBS |
| DT-95.i | At v0.3.5 the controller applied the same check; a v0.3.5 plan row expected a "wrong nonce, worker or hash binding" to fail; no reader then or now makes those comparisons. | history | HEAD part yes; history not re-read | SRC (history) | AO; the plan row is not a public statement, so no obligation follows | D-OBS |
| DT-95.AT.a | The host decoder checks nine ordered conditions, source-read; DT-101 limits their check support. | raw worker capture record plus host arguments; host; worker collection | Yes — `CWorker.swift:685-711` | SRC | AO | D-OBS |
| DT-95.AT.b | Eleven relations (presence, nonce, PID, decoded length, extent, byte digest, source digest/length, parameters, type, `reason` presence) are delegated to the host rule and re-checked by no recipient. | reply as received | Yes | SRC | AO; CA as DT-95.a | D-ADM |
| DT-95.AT.c | Recipients check one predicate, implemented three times. | — | Yes — as DT-95.c | SRC | AO | D-OBS |
| DT-95.AT.d | Seam rows `f95-receipt-unrequested`, `-nonce`, `-byte`, `-length-zero`: `finished`, exit 0, Rust `valid`, consumer `[]`; `f95-producer-host` appears as a `reply_admission` finding on the seam while production refuses first. | live frames with a constructed contract binding and one edit; seam, not production | Rows retained (SEAM). `porcelain_admission.rs:1443-1445` adds `reply_admission` from the same predicate. | EXE-C (SEAM) | AO | D-OBS |
| DT-95.AT.e | Agreement classification: deliberate division of responsibility (stated delegation), and a labelled design judgment that the outcome-changing check is a questionable allocation. | judgment | Judgment, not a fact to verify | — | Judgment | D-ADM |
| DT-95.AT.f | `disposition_integrity: valid` does not certify receipt binding. | envelope diagnostics | Yes — `porcelain_admission.rs:1436-1445` | SRC | AO; CA | D-ADM |

#### DT-96 — constant labels

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-96.a | `pw_shm_capture_t` has no producer or stage member; the decoder writes both labels as literals on its one success path. | worker record; host decoder | Yes — `controller/tools/pw_probe_runner/pw_probe_runner_abi.h:575-588`; `CWorker.swift:712-713` | SRC | IMA in the field meanings (`35-profile:55`, `:59` say the value "identifies") | D-LBL |
| DT-96.b | The stage is true because of the worker's straight-line order: compile, capture, optional sleep, ready byte, apply. | worker program | Yes — `pw_probe_runner.c:1574`, `:1594-1602`, `:1608-1615`, `:1622-1628`, `:1641` | SRC | AO | D-LBL |
| DT-96.c | The progress word records `PW_OP_CAPTURE` (6) as one value later operations overwrite; probe C read operation 9, stage 2. | worker evidence | Yes for the source (`pw_probe_runner_abi.h:315-316`, `:384-391`); probe value not re-observable | SRC, EXE-L (absent) | AO | D-OBS |
| DT-96.d | The two label comparisons can detect only a producer that writes different constants; they test no observation of the capturing process or the order. | controller admission | Yes | SRC | IMA as DT-96.a | D-LBL |
| DT-96.e | The Rust label test and the Swift label test change the constants after construction. | constructed | Yes — `CompiledProfileCaptureTests.swift:37-54`; fixture rows 2–18 | SRC | AO | D-OBS |
| DT-96.f | Labels added in `b6e6c313`; the original decoder `660de67b` had neither. | history | Not re-read | SRC (history) | AO | D-OBS |

#### DT-97 — nonce

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-97.a | The nonce path has seven steps: format-only host admission; pass-through; zeroed mapping and header write; worker local copy; copy into the capture record; host re-decode and compare; host emits the request string. | request string → header bytes → record bytes → reply string | Yes — `ProbeRunner.swift:64-70`; `CWorker.swift:672-677`; `CWorkerOrchestrator.swift:124-125`; `ActorSession.swift:133`, `:152-155`; `pw_probe_runner.c:1531-1532`; `pw_profile_capture.h:64`; `CWorker.swift:694-697`, `:713` | SRC | AO | D-OBS |
| DT-97.b | The nonce enters no compile call and no digest; both comparison operands originate in bytes the host wrote into one mapping; the comparison detects a record not written from that header. | host decoder | Yes | SRC | IMA in the source owner's pin "Fields bind the observed worker, nonce …" (`35-profile:394`) | D-NONCE |
| DT-97.c | Bytes and digest do not vary with the nonce; `request_nonce` associates a receipt with a request only together with the reply the host placed it in. | six repeat runs | Repeat runs not re-observable; RET shows three nonces with identical bytes. Second half follows from DT-97.b. | EXE-L (absent), RET, SRC | CA (`35-profile:63` "supplies a consumer's request association") | D-NONCE |
| DT-97.d | The refusal text says "fresh"; the host keeps no record of earlier nonces and checks only length and alphabet; reuse was not executed. | host admission | Yes — `CWorker.swift:744`; `PWRunnerRequest.swift:41`; `CWorker.swift:672-677`; no nonce store exists (grep). Reuse still unexecuted. | SRC | CA | D-NONCE |
| DT-97.e | Checks: Swift flips one nonce bit and asserts `unavailable` without a reason; `capture.c` asserts copy equality; live tests assert `request_nonce` equals the request's; no test supplies a valid but different nonce, and none shows what the association adds beyond PID and the per-worker mapping. | tests | Yes — `CompiledProfileCaptureTests.swift:67-76`; `tests/suites/runner_abi_layout/capture.c:29`, `:57`; `contract.py:326`, `:431`, `:484` | SRC | AO (coverage statement) | D-SUP |

#### DT-98 — input identity

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-98.a | With one source importing a file by absolute path, rewriting the file between two runs changed the bytecode and no receipt identity field. | ordinary; two separate runs; receipt fields | Executed part not re-observable. Structural part yes: the record and receipt have no member for a file (`pw_profile_capture.h:60-71`; `CWorker.swift:706-709`). | EXE-L (absent), SRC | AO | D-INPUT |
| DT-98.b | The source owner's "consumed input bytes" and the guide's "identifies compiler output" can be read as complete input identity; no statement claims imported bytes. | owner pin; frozen guide | Yes — `35-profile:394`; `docs/contract/11-policy.surface.md:72` separately says source, parameters and imported bytes are distinct inputs | SRC | IMA/CA in the pin | D-INPUT |
| DT-98.c | Limits: two separate runs, not two reads within one run; the worker's file reads were not traced. | — | Still true; nothing since has traced them | — | AO | D-OBS |

#### DT-99 and DT-100 — reasons and guard order

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-99.a | The worker records status 1–4; the host maps every status other than 1 to `worker_capture_refused`. | worker record; host decoder | Yes — `pw_profile_capture.h:68-86`; `pw_probe_runner_abi.h:573-574`; `CWorker.swift:692` | SRC | CA | D-REASON |
| DT-99.b | `capture_extent_or_type_invalid` is reachable only through a status-1 record with an invalid extent or type, which the worker's own checks prevent. | host decoder | Yes — `pw_profile_capture.h:78-80`, `:86`; `CWorker.swift:698-701` | SRC | AO; CA for a consumer matching on that reason | D-REASON |
| DT-99.c | The receipt has no field for the worker's status, so "unsupported" (the LIMITS cases) cannot be told from "unreadable". | receipt | Yes — `docs/limits.json:1760`, `:1788`; LIMITS names no reason | SRC | CA | D-REASON |
| DT-99.d | No statement mentions the worker's `reserved == 0` requirement. | statements | Yes — `pw_profile_capture.h:78`; absent from `35-profile` and `limits.json` | SRC | IMA (omission) | D-REASON |
| DT-99.e | Status 4 appears unreachable with the shipped worker. | worker | Yes by reading — one snapshot feeds both the setter and capture (`pw_probe_runner.c:1530-1534`); the NUL check `:1548-1554` precedes; `pw_profile_capture.h:36-41` | SRC | AO | D-OBS |
| DT-99.f | `capture.c` asserts statuses 2, 3, 4 on constructed memory; Swift reaches the extent reason only with constructed status-1 records; no test names `worker_capture_refused`; none ran live. | tests | Yes — `capture.c:36-42`, `:71-84`; `CompiledProfileCaptureTests.swift:77-83`; grep | SRC | AO (coverage statement) | D-SUP |
| DT-100.a | The decoder checks application then completion before reading any capture word; `applied` comes from the worker's published flag; no classifier reads `profileCapture`. | host | Yes — `CWorker.swift:685-689`; `ActorSession.swift:630-642`, `:737-741`; consumers only at `CWorkerOrchestrator.swift:226` and `ActorOrchestration.swift:442` | SRC | AO | D-GUARD |
| DT-100.b | A source that fails to compile, with capture requested, yields `unavailable` / `successful_application_unconfirmed`; the capture block never ran. | ordinary; live | Not re-observable. By source: the worker leaves at `pw_probe_runner.c:1582-1589` before `:1594`, publishing done and exiting 0 (`:601-606`). | EXE-L (absent), SRC | AO | D-GUARD |
| DT-100.c | A worker killed after application yields `worker_not_complete` although capture had returned; the record's completion and status words are not projected. | ordinary; live | Yes — RET | RET, SRC | AO | D-GUARD |
| DT-100.d | Neither receipt alone says whether capture was attempted; the reply's worker evidence does; neither receipt changed the reply outcome. | receipt versus reply | Yes | SRC, RET | CA (`35-profile:35` "`unavailable` states that a capture condition failed") | D-GUARD |
| DT-100.e | The registered case does not assert absence of the other eight withheld fields; no test requests capture for a policy that fails to compile. | tests | **Partly.** First half yes (`contract.py:509-510`). Second half holds for the ordinary form only: `witness_contract/actor_compositions` requests capture for every apply actor of its `failed_recipient` specimen, whose actor C source is `(version 1) (allow` (`check_actor_compositions.py:76-79`, `:481-482`), and asserts `unavailable`, no bytes, no labels, no nonce and a truthy `reason`, not its value (`:121-123`). | SRC | AO for the ordinary form; the unqualified sentence was over-broad | D-SUP |

#### DT-101, DT-102, DT-104 — test support

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-101.a | The Swift fixture constructs every premise: a 144-byte header at literal offsets, a three-byte payload, injected `applied`, `applyRC`, `done`, exit and signal. | constructed bytes; `decodeProfileCapture` called directly | Yes — `CompiledProfileCaptureTests.swift:12-36`; offsets agree with `pw_probe_runner_abi.h:575-588` | SRC | AO (the owner's `context` says so) | D-OBS |
| DT-101.b | The corruption loop flips one bit at eleven offsets and asserts `unavailable`, nil bytes and nil digest; it asserts neither the seven distinct reasons nor the other nine withheld fields. | constructed | Yes — `:67-76` | SRC | OCC (the rule states `failure: "first"` and nine reasons; the owner's `limits` does not say reasons are unasserted) | D-SUP |
| DT-101.c | The extent loop asserts `capture_extent_or_type_invalid` for lengths 0, 1,048,577 and `UInt32.max` on status-1 records. | constructed | Yes — `:77-83` | SRC | AO | D-OBS |
| DT-101.d | `successful_application_unconfirmed` is asserted once (`applied: false`); `applyRC: -1`, `done: false` and signal 9 assert status only; nonzero exit without a signal is not exercised. | constructed | Yes — `:84-91` | SRC | OCC as DT-101.b | D-SUP |
| DT-101.e | The label test and the round trip change the constant labels after construction. | constructed | Yes — `:37-54`, `:98-110` | SRC | AO | D-OBS |
| DT-101.f | Four invalid nonces through `runCWorker` return `.captureNonceInvalid` before any mapping or spawn. | constructed | Yes — `:111-119`; `ActorSession.swift:71-73` | SRC | AO | D-OBS |
| DT-101.g | No case combines two failing conditions; the first-failure order is source-supported only. | constructed | Yes | SRC | OCC as DT-101.b | D-SUP |
| DT-101.h | Six of nine reasons are named in no test. | tests | Yes — `git grep` at HEAD finds `capture_not_complete`, `worker_capture_refused`, `capture_worker_mismatch`, `capture_nonce_mismatch`, `capture_bytecode_digest_mismatch`, `capture_consumed_input_mismatch` only in `CWorker.swift`, `35-profile.surface.md` and generated documents | SRC | OCC as DT-101.b; `capture_nonce_mismatch` is one of the three displayed values | D-SUP |
| DT-101.i | The encoding fixture `value46` is `captured`, carries `reason: "constructed"` and a digest that does not match its bytes; host reporting validation accepts it. | constructed encoding input | Yes — `runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift:88`; same content in `tests/fixtures/contract/normal_reply.json:11-26` | SRC | AO (the file header says it is field-complete encoding input) | D-OBS |
| DT-101.j | The support pin matches the assertions; guard-specific reasons, order and the eleven withheld fields go beyond them. ARCHITECTURE cites the same check for "admitted only after … checks". | owner `35-profile:281-290`; `docs/architecture.json:2077-2095` (B12) | Yes. B12's claim is necessity of each listed check, which the single-fault rows do support; it claims no reason or order. | SRC | OCC for the receipt rule's owner; AO for B12 | D-SUP |
| DT-102.a | Every live capture assertion about parameters uses none. | live tests | Yes — `contract.py:332`; `check_actor_compositions.py:134-135`; `guide_workflows.py:470` | SRC | AO (coverage limit) | D-SUP |
| DT-102.b | `capture.c` checks order independence and sensitivity, not the digest value; Swift checks the host value against one independently framed pair; no test compares the C value for a nonempty set with the Swift value or an independent value. | constructed | Yes — `capture.c:65-70`; `CompiledProfileCaptureTests.swift:21-24`, `:92-97` | SRC | OCC risk only if agreement is credited; no document credits it | D-SUP |
| DT-102.c | In B2 the worker's digest for two parameters, one non-ASCII, equalled an independent recomputation, and `captured` implies the Swift recomputation agreed. | ordinary; live; one input | Not re-observable; the value reproduces by CALC | EXE-L (absent), CALC | AO, one input | D-SUP |
| DT-104.a | Eight of the seventeen invalid fixture rows fail the test-only serde reader before admission; nine reach `admission_problem`; the run test never uses the binary reader. | constructed JSON typed by the `cfg(test)` derive | Yes — nineteen rows, two valid; the eight are `producer_False`, `producer_7`, `capture_stage_False`, `capture_stage_7`, `status_None`, `status_False`, `status_7`, `status_absent`; `run_flow.rs:2658-2678`, `:1929-1952` | SRC | OCC (the test name and `tests/suites/unit/README.md:33-39` credit label refusal for all refused rows) | D-FIX |
| DT-104.b | The run test cannot tell a withheld diagnostics key from a null one. | `serde_json` indexing | Yes — `run_flow.rs:3006-3010`. The producer emits the key with JSON null (`run_flow.rs:66-71`, `:126`). **The review's cross-reference is mistaken:** the statement/source difference is recorded in DT-32's third bullet (review lines 937–945), not in DT-37. | SRC | OCC in the pin "diagnostic presence" (`35-profile:348`) | D-FIX |
| DT-104.c | The credited run `20261110T195016Z_0d197151` at `5e51300d` is not in this checkout; the test body, fixture and `admission_problem` are unchanged since. | owner `35-profile:339-351` | **Partly.** The run is absent and the three items are unchanged, but `controller/src/run_flow.rs` changed in four commits between `5e51300d` and `3d3f8e65` (`git diff --stat`: 1,157 changed lines), including how `admit_reply` types the refusal (`:330-355`) and the introduction of the `select` relation for the run result (no `select(&` call at `5e51300d`, five at HEAD). The credited execution therefore did not exercise HEAD's path from admission to the public result. The test passes over HEAD-equal source in RET. | SRC, RET | OCC (execution credit names a snapshot whose orchestrating source differs) | D-CRED |
| DT-104.d | The host always supplies `reason` on `unavailable` and never on `captured`; no reader requires either. | host; readers | Yes — `CWorker.swift:682-683`, `:712-716`; the three predicates | SRC | AO; folded into the DT-95 admission question | D-ADM |

#### DT-103 — the capture view

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-103.a | The worker reads the returned object through a four-member, 24-byte private view; only the size is asserted statically; reads use `mach_vm_read_overwrite`; the same pointer goes to `sandbox_apply` with only a sleep, the ready byte and progress stores between. | worker memory before application | Yes — `pw_profile_capture.h:15-22`, `:53-58`, `:72-82`; `pw_probe_runner.c:1574`, `:1598-1600`, `:1603-1641` | SRC | AO | D-VIEW |
| DT-103.b | Decoded length and digest matched for every capture; equal inputs gave equal bytes; different policies gave different bytes. | live | Partly re-observable: RET shows three equal captures with matching length and digest | EXE-L (absent), RET | AO | D-VIEW |
| DT-103.c | The host-side `bytecode_digest.c` probe read the same 492 bytes through the same view: agreement across processes under one layout reading, not an independent decoding. | separate process | Not re-observable | EXE-L (absent) | AO | D-VIEW |
| DT-103.d | The live control cited by WORKER rows s27, x5, W14, W38, W54 requires `captured` and a positive length; other live tests add the length and digest check; together they show the four words read as type 0, reserved 0, a readable pointer and a bounded length, and that the bytes are deterministic, on this macOS build. | live | Yes — `docs/WORKER.md:613`, `:643`, `:669`, `:678`, `:692` (scope text states exactly that assertion); `check_max_target_reply.py:253`, `:378` | SRC, RET | AO | D-VIEW |
| DT-103.e | No check compares the bytes with a reference compilation, decodes them, or shows `sandbox_apply` submits them; the source owner's limit does not name the native checks it refers to. | — | Yes — `35-profile:396` | SRC | IMA (unnamed checks); CA at `35-profile:85` | D-VIEW |

#### Coverage and limits section

| Id | Claim | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- |
| CL.a1 | Receipt key absent from JSON and host bytes when capture was not requested; the registered corpus asserts the same through CLI and XPC. | Yes for the assertion (`contract.py:435`, `:488`) | SRC, RET (case passed) | AO | D-OBS |
| CL.a2 | For captured contrasts, length, digest, source, parameters, nonce and PID agreed with request and reply. | Re-shown for three captures | RET | AO | D-OBS |
| CL.a3 | The controller's JSON receipt equalled the receipt decoded independently from retained host bytes. | Not re-observed here; `blackbox_e2e/checker_controls` passed in RET | EXE-L (absent) | AO | D-OBS |
| CL.a4 | The kill-after-application control produced `unavailable` / `worker_not_complete` with every capture field withheld. | Yes | RET | AO | D-OBS |
| CL.a5 | The three registered cases passed without system sleep. | Original absent; same in RET | RET | AO | D-OBS |
| CL.b1 | Not established: that the bytes come from the compiler's object beyond the private layout reading. | Still not established | — | AO | D-VIEW |
| CL.b2 | Not established: how the bytes relate to what `sandbox_apply` submitted. | Still not established | — | AO | D-VIEW |
| CL.b3 | Not established: any kernel state. | Still not established | — | AO | D-VIEW |
| CL.c1 | Not exercised: live `worker_capture_refused` or `capture_not_complete`. | Still unexercised | — | AO | D-SUP |
| CL.c2 | Not exercised: live PID, nonce, digest or consumed-input failures; the shipped worker does not publish the records these need. | Still unexercised | — | AO | D-SUP |
| CL.c3 | Not exercised: an oversized or non-type-0 compiled object. | Still unexercised (constructed only, `capture.c:36-42`, `:71-76`) | — | AO | D-SUP |
| CL.c4 | Not exercised: a reused nonce. | Still unexercised | — | AO | D-NONCE |
| CL.c5 | Not exercised: augments with capture. | Still unexercised by a receipt assertion | — | AO | D-OBS |
| CL.c6 | The controller's response to edited receipts is inferred from source and two constructed Rust tests, not run through `policy-witness run`. | Still so; SEAM rows are not the production path either | — | AO | D-ADM |
| CL.c7 | Actor receipts, BYOXPC and `runner verify` were excluded. | Still excluded here except where noted | — | AO | D-OBS |
| CL.d | The saved-reply mutations exercised the Python consumer; history shows when mechanisms and statements appeared, not how older binaries behaved. | Yes | — | AO | D-OBS |

#### DT-134

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| DT-134.a | After producer admission, collection geometry and the receipt status/label check are the only semantic-record checks that refuse the reply; every other relationship adds diagnostics or is unchecked, including receipt association and the receipt's internal relations. | typed reply; controller | Yes for the receipt part — `run_flow.rs:99-107`; `porcelain_admission.rs:1308-1331`, `:1436-1445`. The "only" over all record families was not re-derived here. | SRC | AO | D-ADM |
| DT-134.b | An inserted receipt with another PID, a replaced nonce, a flipped byte and a zero length were each `finished` with Rust `valid` and consumer `[]`. | seam; constructed | SEAM rows present | EXE-C | AO | D-OBS |
| DT-134.c | Design judgment: the outcome-changing check reads two host constants; association is checked once in the host decoder; a recipient cannot tell a correct receipt from a detached one without the request; the statement acknowledges the delegation, so this is not an unmet promise. | judgment | Judgment. Its factual premises hold. | SRC | Judgment; CA | D-ADM |

### 1.2 Comparison

**The obligation as stated.** Owner: `docs/contract/35-profile.surface.md`
(rendered at `docs/RESPONSE.md#contract-profile`). Request side:
`docs/contract/11-policy.surface.md:39-54`.

- Status (`:35`): "`captured` states that the host's capture checks passed. `unavailable` states that a capture condition failed."
- Reason (`:47`): "The host names the first failing capture condition. The controller's label check accepts the carried reason string." Open vocabulary, three illustrative values.
- Producer (`:55`): "`worker` on a captured receipt identifies the component that captured the bytes." Stage (`:59`): "`before_apply` on a captured receipt identifies when the worker captured the bytes."
- Nonce (`:63`): "The host returns the request's capture nonce after comparing it with the worker's recorded bytes. A comparison with a separately retained request nonce supplies a consumer's request association; the controller's carried-label check has no request-nonce operand."
- Bytecode (`:85`): "The bytes copied from the compiler object passed to `sandbox_apply`, presented as base64."
- Two record conditions with no acting component (`:73-77`, `:87-92`).
- Host rule (`:127-279`), `failure: "first"`, nine ordered conditions each with a reason, then "Capture failure" withholding eleven fields.
- Labels rule (`:299-337`), `who: controller`: "After public producer admission and reply-capacity checks, the controller applies these conditions to every present receipt … The retained nonce, bytecode, digests, lengths and counts remain the host's assertions; their production checks belong to the host capture rule."
- Source owner pin (`:394`): "Fields bind the observed worker, nonce and consumed input bytes." Limits (`:396`): "Live capture behavior and platform private-layout compatibility require their native checks."
- Request side (`11-policy:54`): "exactly 32 lowercase hexadecimal characters encoding the caller's nonce … Receipt publication and consistency checks belong to the compiled-profile surface." `11-policy:72`: "Source text, selected parameter values and imported file bytes are distinct inputs."

**What the producers do (observation, by reading).**

- Worker: snapshots nonce and parameters (`pw_probe_runner.c:1530-1534`), compiles (`:1574`), and when asked copies the object through the 24-byte view into its region, recording PID, source length and digest, parameter count and digest, type, extent, byte digest and a status 1–4, then release-publishes completion (`pw_profile_capture.h:60-89`). It then writes the ready byte and calls `sandbox_apply` on the same pointer (`:1641`). On a nonzero apply return it publishes the failure and calls `publish_done_and_exit`, which stores `done` and calls `_exit(0)` (`:1645-1654`, `:601-606`).
- Host: `decodeProfileCapture` (`CWorker.swift:679-717`) applies the nine guards in the stated order and on success emits the request's nonce string, its own source length and parameter count, the worker-recorded source and parameter digests, a recomputed byte digest, the bytes and the two literal labels. `contextProblem` runs before encoding.
- Controller: `admission_problem` reads `status`, `producer`, `capture_stage` of every present receipt. At the call site (`run_flow.rs:693`) the controller also holds, and does not consult: the resolved request value (`request_value`, `:580`–`:674`, including `policy.sbpl_source`, `policy.params`, `policy.capture_compiled_profile`, `policy.capture_nonce` and each `actors[].sandbox.policy`), its one serialization `held` (`:678`), the dossier (`specimen.policy.augmentation.applied_sha256`, `:609-613`, `:653`), and in the reply `policy_sha256`, `sandboxed_after_apply`, `runner_subprocess.pid` and exit fields.

**What each reader or test asserts.**

| Reader or test | Asserts | Does not assert |
| --- | --- | --- |
| `admission_problem`, `_validate_capture`, `contextProblem` | status vocabulary; captured ⇒ both labels; unavailable ⇒ neither label | everything else, including `reason` presence and the two record conditions |
| `compiled_profile_labels_determine_the_public_admission_outcome` (`run_flow.rs:2967`) | exit, `ok`, outcome, typed read-back of the retained reply, `policy_check` null, diagnostics null-or-absent | which boundary refused (eight rows are client decode refusals); any relation between receipt and request; absent versus null |
| `CompiledProfileCaptureTests` | `unavailable` and withheld bytes/digest for eleven single-bit corruptions; the extent reason; one application reason; label handling; digest sensitivity | six reasons; first-failure order; the other nine withheld fields; nonzero exit without a signal |
| `capture.c` | statuses 1–4 on constructed memory; exact-capacity copy; digest sensitivity | any digest value for a nonempty parameter set; the platform's layout |
| `contract.py:322-332`, `check_actor_compositions.py:118-135`, `guide_workflows.py:461-470`, `check_response_footprint.py:235-241` | on their own live outputs: nonce, PID, source digest, decoded length and digest, zero parameters | parameters other than none; any failure reason except `worker_not_complete` |
| `check_max_target_reply.py:253`, `:378` | `captured`, positive length | byte content |

**Inference kept apart from observation.** That a captured receipt's bytes are
"the compiler object passed to `sandbox_apply`" is a reading of the worker's
source under an assumed private layout; that application consumed those bytes
is not observed by any component (DT-103). That labels describe who copied and
when is a reading of the worker's program order, not a record (DT-96). That a
receipt belongs to its request is established once, by the host, from the raw
worker record; recipients observe only the host's emitted values (DT-95, DT-134).

### 1.3 Plausible treatments

Build-contract inputs are `controller/src`, `controller/tools`, `runner/Sources`
and the files listed in `docs/build_contract.py:15-27`. `docs/contract/*.surface.md`,
`runner/Tests`, `tests/suites`, `tests/fixtures` and suite READMEs are not.
Surface edits regenerate through `tests/lib/python.sh docs/generate_contract_stamps.py`.
Per `docs/contract/README.md`, owner-only edits (`pins`, `context`, `limits`,
`run`, `source_snapshot`) leave the public payload unchanged; field and rule
prose changes it, so the profile (and policy) surface stamp in CONTRACT changes
while the guide's frozen stamp table does not.

#### T1 — controller admission of receipts (DT-95, DT-134, DT-104.d) — product decision 2

What the controller could compare with what it holds at `run_flow.rs:693`:

| Relation | Operands the controller holds | Needs the request passed into admission? |
| --- | --- | --- |
| captured ⇒ capture fields present, `reason` absent; unavailable ⇒ `reason` present, eleven fields absent | receipt only | no |
| captured ⇒ `0 < bytecode_length ≤ 1,048,576` and `len(bytecode) == bytecode_length`; `profile_type == 0` | receipt only | no |
| captured ⇒ `sha256(bytecode) == bytecode_sha256` | receipt only | no |
| `worker_pid == runner_subprocess.pid` (actor: `actors[a].subprocess.pid`) | reply only | no |
| captured ⇒ `source_sha256 == policy_sha256` | reply only (ordinary form) | no |
| captured ⇒ `sandboxed_after_apply == true`, clean exit | reply only | no |
| receipt present ⇒ `capture_compiled_profile == true` for that policy | `request_value` | yes |
| captured ⇒ `request_nonce == capture_nonce` | `request_value` | yes |
| captured ⇒ `source_sha256`/`source_length` match the resolved source (equal to `applied_sha256`) | `request_value` or dossier | yes |
| captured ⇒ `parameter_count`/`params_sha256` match the request's parameters | `request_value`; a third implementation of the framing, in Rust | yes |

What a comparison would establish: that the reply the host sent is consistent
with itself and with the request the controller delivered. It would reject a
host or codec defect that attaches or alters a receipt (wrong actor, stale
values, a field corrupted in a way the frame grammar still accepts). It would
not establish authenticity: the host and worker are the product's own
processes, and four of the compared values (`request_nonce`, `source_length`,
`parameter_count`, `bytecode_sha256`) are values the host itself writes from its
own inputs (`CWorker.swift:713-716`), so the controller would be comparing the
request with the host's echo of it. It would say nothing about imported files
(DT-98), the layout (DT-103) or what was applied.

- **T1-A, reasoned retention with the account completed.** Files:
  `docs/contract/35-profile.surface.md` labels-rule prose (`:309`); nothing else.
  Not a build-contract input. Users and developers see no behavior change. The
  check that must keep discriminating is the existing one: a reply with an
  unknown status or a missing/foreign label must be refused. The property newly
  worth pinning is the limit itself: an admitted receipt that disagrees with
  the request must remain an explicit, named expectation of the Rust test so
  that a later change to admission is a visible decision (T7).
- **T1-B, refuse on inconsistency.** Files: `controller/src/porcelain_admission.rs`
  (`admission_problem` and a request parameter), `controller/src/run_flow.rs`
  (`reply_contract`, `admit_reply`, call site, tests at `:1929`, `:2967`),
  `controller/src/runner_commands.rs:614` (verify's fixed request never asks for
  capture, so any present receipt would be refused), a Rust parameter-digest
  implementation, `tests/lib/consumer.py:575-588` (mirror it or state the
  divergence in `tests/FAILURE-PROPAGATION-CONTRACT.md`), optionally
  `runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift:31-44`;
  `tests/fixtures/contract/compiled_profile.json` (the `captured` row must
  become coherent and gain a capture-requesting request; new invalid rows);
  `tests/fixtures/contract/normal_reply.json:11-26` and `ReplyFailureTests.swift:88`
  (a field-complete receipt carrying both `reason` and capture fields could no
  longer be admitted, so the reply shape golden needs two receipts);
  `porcelain_admission.rs:2732`; `check_actor_compositions.py:499-503`;
  `35-profile.surface.md` labels rule (new structured conditions), shape golden
  `tests/fixtures/contract/surfaces/profile.json`. **Build-contract input: yes
  (signed rebuild).** Consequence: no change for replies the shipped host
  produces; a disagreeing reply becomes `malformed_runner_response`, exit 1,
  where it is `finished` today. A Rust digest that disagreed with C and Swift on
  some parameter set would refuse real runs. A check must reject: an
  unrequested receipt; a nonce, source, parameter or PID mismatch; bytes that
  do not match their length or digest; `reason` on `captured`.
- **T1-C, report inconsistency as a finding without changing the result.** Same
  operand plumbing and fixtures as T1-B, plus `docs/contract/41-diagnostics.surface.md`
  (what `disposition_integrity` covers) and the lifecycle oracle. Build-contract
  input: yes.

#### T2 — capture despite failed application (DT-100) — product decision 1

- **T2-A, retain both guards; state the limit.** Files: `35-profile.surface.md`
  Status prose (`:35`). Not a build-contract input. Consequence: none for
  behavior. Checks: `CompiledProfileCaptureTests.swift:86-87` already rejects a
  decoder that publishes `captured` when `applied` is false.
- **T2-B, select the rehearsed change.** The guard that withholds a completed
  copy after a returned apply failure is the application guard alone
  (`CWorker.swift:685`). On that path the worker publishes `done` and exits 0
  (`pw_probe_runner.c:1645-1654`, `:601-606`; asserted for the production C main
  with a substituted `sandbox_apply` at `WorkerEvidenceTests.swift:36-47`, `ok`
  in RET), so the completion guard (`:686`) already holds and needs no
  replacement. The completion guard separately withholds on signal, deadline
  and unreaped paths, which are not failed application. Files:
  `runner/Sources/PWRunnerCore/CWorker.swift:685` and the doc comment at
  `PWRunnerProfileCapture.swift:4-7`, `pw_probe_runner_abi.h:569-574` comment
  (**build-contract inputs**); `35-profile.surface.md` (Application condition
  and its effect, Reason's displayed values, Status, `capture_stage`);
  `docs/architecture.json:2081` (B12) and `:1345`, authored
  `docs/ARCHITECTURE.md:437-442`, `:569`; `docs/limits.json:1788`; the shared
  region sentence at `docs/LIMITS.md:294-297` (owner corrected, guide copy
  frozen); `CompiledProfileCaptureTests.swift:84-91`, `ActorShapeFixtures.swift:355-356`,
  `ContractShapeTests.swift:183-203`; `tests/suites/runner_unit/README.md:291-292`,
  `tests/suites/witness_contract/README.md:745`,
  `tests/suites/runner_outcome_bad_request/README.md:34-35`. Consequences:
  `captured` no longer implies observed application; a compile failure would
  report `capture_not_complete` instead of `successful_application_unconfirmed`
  (the worker exits 0 with `done` before the capture block), so
  `check_actor_compositions.py:121-123` still passes but its reason changes. A
  check must reject: `captured` when the capture record is incomplete;
  `captured` after a signal or deadline; an envelope whose result treats failed
  application as success because a receipt is `captured`.

#### T3 — label meanings (DT-96)

- **Correction of the account in its owner.** Files: `35-profile.surface.md:55`,
  `:59`. Not a build-contract input. This applies the authoring rule in
  `docs/contract/AGENTS.md` ("State the observation supporting a value beside
  its meaning, including a successful value").
- Recording producer and stage in the worker's capture record is not a real
  candidate: a worker-written constant is still a constant, and the change
  would alter the ABI layout and worker identity for no added observation.

#### T4 — nonce (DT-97)

- **Correction of the account.** Files: `35-profile.surface.md:63` and the
  source owner pin `:394`; `11-policy.surface.md:54` for caller-owned
  uniqueness. Not build-contract inputs.
- Removing "fresh" from the refusal text (`CWorker.swift:744`,
  `PWRunnerRequest.swift:41`) is a build-contract edit that changes a public
  message for a wording gain only. A host-side record of earlier nonces would
  contradict the fresh-host-per-specimen rule. Neither is recommended.

#### T5 — input identity (DT-98) — product decision 3

- **Reasoned retention with the limit stated.** Files: `35-profile.surface.md:112`
  (definition prose) and `:394` (pin). Not build-contract inputs. No product
  candidate exists inside the bounded decision: no component observes the
  compiler's file reads, and the management plan already records that a
  dossier/receipt digest comparison cannot supply that observation.

#### T6 — reason vocabulary (DT-99, DT-100.d) — product decision 4

- **T6-A, correction of the account; vocabulary retained.** Files:
  `35-profile.surface.md:47` (Reason prose). Not a build-contract input.
- **T6-B, split `worker_capture_refused` by worker status.** Files:
  `CWorker.swift:692` (**build-contract input**), the Capture status condition
  in `35-profile.surface.md:184-197` (three conditions or a mapped effect; a
  new `free.condition` is refused by the generator's free-text count, so the
  conditions need structured expressions), Swift tests, README. Consequence:
  consumers matching `worker_capture_refused` see new strings; a user can tell
  an object above the limit from an unreadable one. A check must reject a
  decoder that reports the size-limit reason for an unreadable object.

#### T7 — test support (DT-95.d, DT-101, DT-102, DT-104)

- **Assertion and coverage repair.**
  - `runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift` (not a
    build-contract input): assert the reason for each of the eleven corruptions;
    assert that every `unavailable` result has only `status`, `reason`,
    `worker_pid`; add `rc: -1` → `successful_application_unconfirmed`,
    `done: false`, signal 9 and `exit: 1` → `worker_not_complete`; add adjacent
    two-fault cases for the order (application+completion, completion+capture
    completion, capture completion+status, status+PID, PID+nonce, nonce+type,
    type+byte digest, byte digest+input); add a known-answer parameter digest.
  - `tests/suites/runner_abi_layout/capture.c` (not a build-contract input):
    assert the same known answer for `a=é`, `z=2`:
    `5aa8848d0fbdc2f9c5bb4c59cbf358459609fe0a42982d825a40ba787a36fcb6` (CALC from
    the framing at `35-profile:112`). Asserting one literal in both languages
    makes C/Swift agreement on a nonempty set a tested fact.
  - `tests/suites/runner_outcome_bad_request/contract.py` (not a build-contract
    input): for `capture_worker_death` assert the exact key set; add an ordinary
    compile-failure specimen with capture requested asserting
    `successful_application_unconfirmed`, the exact key set, `sandboxed_after_apply`
    false and the worker's published compile failure; add one captured specimen
    with two parameters (one non-ASCII) asserting `parameter_count` and an
    independently framed `params_sha256`.
  - `controller/src/run_flow.rs:2967-3013` (**build-contract input**; already
    selected in the overhaul plan): see 1.6 step 7.
- **Narrow the credit instead.** Owner `limits` and README wording only (no
  test edit). Sufficient to make every stated credit true; leaves six reasons
  and the order source-read.
- A check must reject: a decoder that swaps two guards or two reason strings;
  a decoder that leaves a capture field on an `unavailable` receipt; a C
  framing change the Swift side does not mirror; a controller that admits an
  unknown status or label.

#### T8 — the capture view (DT-103) — product decision 5

- **Reasoned retention with the limit stated.** Files: `35-profile.surface.md:85`
  (field prose), `:396` (owner limits). Not build-contract inputs. No
  independent observer of the compiled object is available to the product: a
  second process using the same view repeats the same reading, and decoding the
  bytes would add a second private-format assumption.

### 1.4 Recommended disposition per claim

| Code | Claims | Disposition | Reason; discriminating check or why more evidence would not change it |
| --- | --- | --- | --- |
| D-OBS | RC.a–d; DT-95.b, .c, .e, .f, .h, .i, AT.a, AT.c, AT.d; DT-96.c, .e, .f; DT-97.a; DT-98.c; DT-99.e; DT-101.a, .c, .e, .f, .i; DT-134.b; CL.a1–a5, CL.c5, CL.c7, CL.d | Accurate observation; no change. | Each was re-read at HEAD, or is a dated executed observation whose raw output is gone and whose value is either re-shown in RET or not relied on by any recommendation here. |
| D-ADM | DT-95.a, .g, AT.b, AT.e, AT.f; DT-104.d; DT-134.a, .c; CL.c6 | **Reasoned retention (T1-A)** of status-and-label admission, with the labels rule saying what admission does not do. Management owns this ruling; it is recommended, not assumed. | The host decoder already establishes each relation from the raw worker record; a controller comparison would establish consistency between two of the product's processes, largely against the host's echo of the request, at the cost in T1-B. The statement already delegates (`35-profile:309`), so after one added sentence no stated claim is false. Check: `unit/rust.unit` (the label test, corrected per D-FIX to name the admitted disagreeing row). More evidence would not change the decision: every operand and both outcomes are determined by source already read. **Accepted limit, to stand in the labels rule:** "The controller compares no receipt field with the request it delivered, with the reply's worker record or with the receipt's own bytes, and evaluates neither extent condition. A `finished` result beside a `captured` receipt reports the host's capture checks, not a controller comparison." |
| D-FIX | DT-95.d; DT-104.a, .b | **Assertion/coverage repair and credit correction** (already selected). Retain enforcement. | The test enforces status and label handling over typed replies. Corrected scope for each crediting place is in 1.6 step 4 and step 7. Check: `unit/rust.unit`; the corrected test must fail if a label row is refused by the decode path instead of `admission_problem`, and if the diagnostics key changes form. The assertion form for DT-104.b follows the disposition of DT-32's label-effect bullet, which another pass owns. |
| D-CRED | DT-104.c | **Correction of the account in its owner.** | The `executed` grade names run `20261110T195016Z_0d197151` at `5e51300d`; `run_flow.rs` changed afterwards. Re-credit with the `unit/rust.unit` run at the commit that carries the corrected test, or grade the owner `check_read` until then. |
| D-LBL | DT-96.a, .b, .d | **Correction of the account in its owner (T3).** | The values are host-written constants. Proposed meanings: producer — "`worker` on a captured receipt names the component whose program copies the bytes. The host writes this value on every captured receipt; no worker publication carries it." Stage — "`before_apply` on a captured receipt names the position of the copy in the worker's program, between compilation and application. The host writes this value on every captured receipt; it is not a recorded observation of that order." No check applies to prose; the program order it restates is at `pw_probe_runner.c:1574-1641`. |
| D-NONCE | DT-97.b, .c, .d; CL.c4 | **Correction of the account (T4)**; behavior retained. | Add to `35-profile:63`: "The nonce enters no compiled byte and no digest; the comparison associates the receipt with the reply that carries it." Replace the pin clause at `:394` (see D-INPUT). Add to `11-policy:54`: "The host checks the nonce's form only and keeps no record of earlier nonces; uniqueness across requests is the caller's." A reuse experiment would not change this: no nonce store exists in the source. |
| D-INPUT | DT-98.a, .b | **Reasoned retention with the limit stated (T5).** | **Accepted limit, to stand in "Captured input identity" (`35-profile:112`):** "The identity covers the source string and the parameter strings passed to the compiler. No receipt field identifies a file the compiler reads for an `import` form, so equal source and parameter identities do not imply equal bytecode." Pin at `:394`: replace "Fields bind the observed worker, nonce and consumed input bytes." with "The host compares the worker-recorded PID, nonce, source identity and parameter identity with its own values before emitting them; files read for imports are outside these identities." The limit is structural, so the two-run observation need not be repeated to support it. |
| D-REASON | DT-99.a–d | **Correction of the account; vocabulary retained (T6-A).** | Add to Reason (`35-profile:47`): "`worker_capture_refused` covers every worker capture status other than captured: an unsupported type, reserved word or extent (including an empty object and one above the limit), an unreadable object, and malformed consumed input. The receipt does not say which. The host's extent and type condition repeats checks the worker makes before it records captured status." The split in T6-B is cheap in code but needs a signed rebuild, restructured conditions and new strings for an optional diagnostic; the reply cannot distinguish the cases either way without it, which is the limit being stated. Check after D-SUP: the Swift status-corruption row asserts `worker_capture_refused`. |
| D-GUARD | DT-100.a–d | **Reasoned retention of both guards (T2-A); the rehearsed change is not selected.** | `captured` today implies observed application and clean completion, and `docs/LIMITS.md:294-297`, B12 and the Swift tests state that. Selecting T2-B withdraws that implication for every consumer to return bytes of an object whose application was refused; the only apply-failure observation is a substituted `sandbox_apply`, so there is no evidence the case arises for real specimens. The ambiguity is resolved from the reply's own worker evidence. **Accepted limit, to stand in Status (`35-profile:35`):** "The host evaluates application and worker completion before it reads any capture record. An `unavailable` receipt therefore does not report whether the worker copied the object, and a completed copy is withheld when application was not observed to succeed or the worker did not complete cleanly." Check: `CompiledProfileCaptureTests.swift:86-87` now; the D-SUP additions after. |
| D-SUP | DT-97.e; DT-99.f; DT-100.e; DT-101.b, .d, .g, .h, .j; DT-102.a–c; CL.c1–c3 | **Assertion/coverage repair (T7)** in `runner/Tests`, `capture.c` and `contract.py`; then state the strengthened scope in the owner. If the repair is deferred, narrow the owner `limits` instead. | The rule publishes nine reason strings and a first-failure order that consumers may match; pinning them costs no signed rebuild. Cases: `runner_unit/pwrunner_core_unit_executable`, `runner_abi_layout/c_swift_layout_agreement`, `runner_outcome_bad_request/accepted_input_contract`. CL.c1–c3 stay unexercised live: the shipped worker does not publish those records for ordinary inputs, and a live oversized object would need a policy compiling above 1 MiB; constructed coverage is the stated support. |
| D-VIEW | DT-103.a–e; CL.b1–b3 | **Reasoned retention with the limit stated (T8).** | **Accepted limit, to stand at `bytecode_b64` (`35-profile:85`):** "The worker reads that object through a fixed four-member view (type, reserved word, byte pointer, length) of a private structure. The receipt establishes that the bytes read this way matched their recorded length and digest. It does not establish the structure's layout on the running system, or which bytes application submitted." Owner limits at `:396`: "Constructed-layout controls (`tests/suites/runner_abi_layout/capture.c`) and live captures (`witness_contract/max_targets_reply_survives`, `runner_outcome_bad_request/accepted_input_contract`) show that the reading yields captured status and self-consistent, repeatable bytes on the tested system. None decodes the bytes, compares them with a reference compilation or observes what application submitted." Those checks reject a layout change that makes the type or reserved word nonzero, the length zero or the pointer unreadable; no available check can reject a readable but different extent. |

**Where authority or information is missing.**

- D-ADM and D-GUARD decide public meanings (what `finished` beside a receipt
  certifies; what `captured` implies). They are recommendations; the ruling is
  management's.
- The assertion form for DT-104.b depends on the disposition of DT-32's
  label-effect bullet (surface says `withhold`, producer emits present-null),
  which this pass does not own.
- No observation exists of `sandbox_apply` returning failure for a real
  specimen, and none of a receipt produced on the `.apply-failure` companion.
  The value of T2-B to a user is therefore unevidenced, and the receipt outcome
  on that path is source-read.
- Nonce reuse was never executed. The source leaves no room for a different
  result, so this is noted, not pending.
- The single cross-link sentence between the receipt identity and the import
  statement needs one agreed wording with the import-inventory pass.

### 1.5 Resulting user duties

Each depends on the recommended dispositions being accepted.

1. **Join the receipt to the request yourself.** A consumer who relies on a
   `captured` receipt compares `request_nonce` with the nonce in its own
   retained request, `worker_pid` with `runner_subprocess.pid`, `source_sha256`
   with the digest of the source it submitted (after augmentation:
   `specimen.policy.augmentation.applied_sha256`), and decodes and re-hashes
   `bytecode_b64`. `result.ok`, `finished` and `disposition_integrity: valid`
   establish none of these. Evidence: DT-95.a, .d (constructed, `ok` in RET), SEAM.
2. **Supply a nonce unique to each application** if the nonce is to distinguish
   replies. The host checks its form only. Evidence: DT-97.d (source; reuse not
   executed).
3. **Do not read the receipt's identity fields as identifying imported files**,
   or equal identities as equal compiled objects. Evidence: DT-98 (executed
   once, raw output gone; structural by source).
4. **Do not read `bytecode_b64` as the kernel's effective policy, or as proven
   to be the bytes application submitted.** Evidence: DT-103 (source).
5. **Do not conclude from an `unavailable` receipt that capture did not run or
   that application failed**; read `sandboxed_after_apply` and
   `runner_subprocess.worker_evidence`. Evidence: DT-100 (RET for the kill case).
6. **Do not infer which worker failure occurred from `worker_capture_refused`**,
   and do not expect `capture_extent_or_type_invalid` for an object above the
   limit. Evidence: DT-99 (source; constructed controls).
7. **Do not treat `producer` and `capture_stage` as observations** of who copied
   the bytes or when. Evidence: DT-96 (source).

### 1.6 Implementation worklist

Steps 1–6 touch no build-contract input. Step 7 does.

1. `docs/contract/35-profile.surface.md` — field and rule prose (public payload
   changes): Status `:35` (D-GUARD sentence); Reason `:47` (D-REASON); producer
   `:55` and stage `:59` (D-LBL); nonce `:63` (D-NONCE); `bytecode_b64` `:85`
   (D-VIEW); Captured input identity `:112` (D-INPUT, with a link to
   `policy.imports.holds`, rendered at `RESPONSE.md#contract-policy-imports-holds`;
   settle the wording once with the import-inventory pass); labels rule `:309`
   (D-ADM). Add no `free.*` fact: the generator refuses an increased free-text
   count.
2. `docs/contract/11-policy.surface.md:54` — nonce uniqueness sentence (D-NONCE).
3. `docs/contract/35-profile.surface.md` — owner-only edits (no public payload
   change): source owner `:394` pin and `:396` limits (D-INPUT, D-VIEW); host
   support owner `:289` limits, adding until step 5 lands: "The corruption cases
   assert unavailability without a reason; reasons are asserted for the
   application guard with one input and for the extent guard. The first-failure
   order and the remaining withheld fields are source-read."; "Constructed run
   labels" owner `:348-350`: pins → "The constructed check follows status and
   label admission through the public outcome, exit status, result and retained
   decoded report; it reads the diagnostics value as null without distinguishing
   an absent key."; limits add → "Eight of the seventeen refused rows carry a
   non-string or absent status or label and are refused by the test's typed JSON
   reader as a client decode refusal before label admission. The admitted
   captured row's nonce, source and parameter fields do not correspond to the
   test request; admission here establishes nothing about request association."
4. Suite accounts (corrected wording scope for each place that credits the
   receipt checks):
   - `tests/suites/unit/README.md:33-39` — say that the corpus has two admitted
     and seventeen refused rows; nine refusals are status/label refusals by
     `admission_problem`, eight are refusals by the test's typed reader with a
     null `runner_result`; the admitted captured row is unrelated to the request.
   - `tests/suites/blackbox_e2e/README.md:71-74` — "checks the nested receipt
     version" names a field and rows that do not exist; "Swift and Rust controls
     read the same … cases" names the wrong readers. Corrected scope: the corpus
     checks the status vocabulary and the worker/before-apply labels in the Rust
     reply-admission tests (`run_flow.rs:1929`, `:2967`) and the Python consumer
     controls (`checker_controls.py:296-300`, `:758-775`); Swift constructs its own.
   - `tests/fixtures/README.md:25-27` — accurate as to readers; add that the
     valid captured row's other fields are arbitrary.
   - `tests/suites/witness_contract/README.md:40-41` — "The capture receipt
     binds nonce, worker PID, source hash …" → the case compares those receipt
     fields with its own request and reply.
   - `tests/suites/runner_unit/README.md:285-293` — accurate now; extend after
     step 5 to say reasons, order and withheld fields are asserted.
   - `tests/suites/runner_abi_layout/capture.c:1-2` comment — "live authored
     controls separately qualify that layout" → name what they observe (captured
     status and self-consistent bytes on the tested system).
   - No edit: `tests/COVERAGE.md` and `tests/FAILURE-PROPAGATION-CONTRACT.md`
     carry no compiled-profile receipt credit (grep at HEAD); `tests/catalog.json`
     descriptions make no receipt claim; `docs/architecture.json` B12 and the
     `profile_capture` form are accurate; `docs/limits.json` `compiled_profile`
     is accurate. `docs/CONTRACT.md:961`, `:2571` and `docs/RESPONSE.md:2623`,
     `:2637` are generated and follow from steps 1 and 3.
5. `runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift` and
   `tests/suites/runner_abi_layout/capture.c` — the T7 repairs. Optionally, in
   `runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift`, run the
   `.apply-failure` companion with capture requested and assert
   `unavailable` / `successful_application_unconfirmed` beside failure operation
   8, `done` and exit 0: a real production-C-main instance of "completed and
   withheld". Then replace the interim owner limits from step 3 with the
   strengthened pin.
6. `tests/suites/runner_outcome_bad_request/contract.py` — the three T7 live
   additions. `capture_worker_death` is the seam caller map's "live self-signal
   case": make its exact-key-set assertion part of that invocation's migration
   so the only ordinary-form unavailable-receipt control survives it.
7. `controller/src/run_flow.rs:2967-3013` (**build-contract input; land after
   the instrument checkpoint with a signed-rebuild group, as the overhaul plan
   says**). For rows where `retained` is `Some`, assert `result.error` is the
   admission text (`"unsupported or malformed compiled_profile"` for
   `status_future`, `"compiled_profile context is inconsistent"` otherwise);
   for the other rows assert `runner_result` is null and count exactly eight.
   Assert the diagnostics key's actual form (present with JSON null at HEAD;
   follow DT-32's disposition). Add a one-line comment that the admitted
   captured row deliberately disagrees with the request. A rename to
   `compiled_profile_status_and_labels_alone_decide_run_admission` is optional;
   if renamed, update `35-profile.surface.md:347` and
   `tests/suites/unit/README.md:33`. Then refresh `run` and `source_snapshot`
   at `35-profile:344-345` from the `unit/rust.unit` run at the carrying commit
   (D-CRED).

Regeneration after steps 1–3 and 7: `tests/lib/python.sh docs/generate_contract_stamps.py`,
then the same with `--check`. Expect no shape change; a refusal that names
`--refresh-shapes` means an edit altered structure and needs re-review.

Routed verification (`tests/CHANGE-VERIFICATION.md` "Find verification for a
change"; `controller/AGENTS.md` table):

- Documentation rows: `tests/run.sh --suite source_drift` (notably
  `source_drift/build_contracts`, `source_drift/generator_contract`).
- Steps 5–6: `runner_unit/pwrunner_core_unit_executable`,
  `runner_abi_layout/c_swift_layout_agreement`,
  `runner_outcome_bad_request/accepted_input_contract`, against the current
  signed app, with a fresh `PW_TEST_OUT_DIR`.
- Step 7: signed rebuild, then `unit/rust.unit`, `unit/rust.fmt`,
  `blackbox_e2e/checker_controls`, and the group's default battery.
- If management instead selects T1-B, T1-C, T2-B or T6-B: the admission route
  (`failure_boundaries` with `runner_unit`, `runner_abi_layout`,
  `runner_c_worker_harness`, `unit`), `blackbox_e2e/checker_controls`,
  `witness_contract/actor_compositions`, `witness_contract/max_targets_reply_survives`
  and a signed rebuild; none of those changes touches the worker wait, release
  store or eligibility rule, so the order-barrier control is not triggered.

---

## Subject 2 — both unnumbered import/receipt investigations, receipt side

The import-inventory side (DT-29, DT-81–87, the scanner, the helper projection,
the resolver comment) belongs to another pass. Rows below take each passage for
what it says about the receipt. "U1" is the first synthesis (review lines
8384–8577), "U2" the follow-up (8579–8759), "NW" the narrower-wording table.

### 2.1 Claims table

#### U1 — first synthesis

| Id | Claim (receipt side) | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| U1.o1 | Nothing observes the compiler's file inputs; dossier and receipt share only the source digest, "and I found no reader that compares the two". | one run envelope | Yes for the first two parts. The last clause is superseded by NW1. | SRC | AO; the last clause was UI as a weakness | S-JOIN |
| U1.o2 | One envelope can show dossier `complete` with no records beside a captured receipt whose checked fields are all correct, while its bytes match a compilation that included an imported rule and the applied policy refused the write (R2/E2); the reverse is R4/E4. | ordinary; live; joint-1, joint-2 | Not re-observable (outputs absent). The receipt half is consistent with source: nothing in the receipt depends on the dossier. | EXE-L (absent) | AO, narrowed by NW2 | S-LIMIT |
| U1.o3 | DT-103 limits only the bytecode parts of the import findings; E2/E4 add evidence for the worker's own compilation that does not depend on the 24-byte view. | — | Reasoning holds | EXE-L (absent) | AO | S-KEEP |
| U1.o4 | DT-82 never appears beside a receipt in a `run` envelope. | `run` envelope | Yes within NW7's scope — `run_flow.rs:699-701`, `:716-724`; `controller/src/runner_client.rs:651-661` | SRC | AO, narrowed by NW7 | S-KEEP |
| U1.s1.98 | Table row DT-98: the receipt's identity covers the compile arguments; the host compares them with its supplied inputs. | — | Yes — `pw_profile_capture.h:71`; `CWorker.swift:706-709` | SRC | AO | S-LIMIT |
| U1.s1.103 | Table row DT-103: bytes are read through the view; consistency and repeatability only. | — | Yes | SRC | AO | S-LIMIT |
| U1.s2.a | `runner_result.policy_sha256` is the host's hash of the request source; nothing compares it with the dossier. | reply | Yes — `CWorkerOrchestrator.swift:220`; no comparison in `porcelain_admission.rs` | SRC | AO | S-JOIN |
| U1.s2.b | `source_sha256`/`source_length` cover the C string passed to compilation, computed by the worker after compile and before apply, compared by the host with its supplied source: "the only source association that is checked". | worker record; host | Yes | SRC | AO | S-JOIN |
| U1.s2.c | `params_sha256`/`parameter_count` cover the worker's parameter snapshot; the host recomputes independently. | worker record; host | Yes — `pw_probe_runner.c:1530-1534`; `CWorker.swift:657-667`, `:708-709` | SRC | AO | S-KEEP |
| U1.s2.d | `bytecode_*` cover bytes read through the view; the worker hashes, the host re-hashes. | worker; host | Yes — `pw_profile_capture.h:82-85`; `CWorker.swift:702-704` | SRC | AO | S-LIMIT |
| U1.s2.e | Imported bytes the worker's compiler consumed: computed by nobody. | — | Yes | SRC | AO | S-LIMIT |
| U1.s2.f | What `sandbox_apply` submitted: computed by nobody. | — | Yes | SRC | AO | S-LIMIT |
| U1.s2.g | The helper's `import_inventory` appears in a run only on fallback, when there is no admitted receipt. | `run` envelope | Yes within NW7's scope | SRC | AO | S-KEEP |
| U1.s2.h | "The separation is documented" in three places: the policy surface, the resolver header, a dossier comment. | statements | **Partly.** The rendered public statement is one sentence, `docs/RESPONSE.md:874` (owner `11-policy.surface.md:577`). The quoted "final equal hashes do not establish read ownership or simultaneity" is a `retained_free` authoring reason at `11-policy.surface.md:574`, which `docs/contract/README.md` says stays outside the readable contract; it appears in no rendered document. The other two are source comments (`controller/src/sbpl_imports.rs:6`, `controller/src/dossier.rs:117`). | SRC | AO for the files; overstated as public documentation | S-LIMIT |
| U1.s2.i | The dossier walk always precedes delivery, so a window for a file to change exists by construction; nothing exercised a change inside it. | within one run | Yes — `run_flow.rs:609-613` precede `:681`; still unexercised | SRC | AO, scoped by NW5 | S-KEEP |
| U1.s3.a | R0–R4: all five runs `finished` with a captured receipt whose length, digest, source, parameters, PID and nonce all checked; bytes were 492 or 548 according to whether the imported rule was evaluated. | ordinary; live; one run per case | Not re-observable | EXE-L (absent) | AO | S-KEEP |
| U1.s3.b | E0–E4: the attempt was refused in exactly the runs whose bytes included the imported rule. | ordinary; live | Not re-observable | EXE-L (absent) | AO, narrowed by NW3 | S-KEEP |
| U1.s3.c | E2/E4 show the applied policy included or excluded the rule without relying on the view; they do not show the captured bytes are what apply consumed, only that enforcement and capture sort the cases alike. | inference from a matched contrast | Reasoning holds | EXE-L (absent) | AO | S-LIMIT |
| U1.s3.d | R1–R3's bytes equal DT-98 run 1's: "the bytes carry neither the import path nor the split"; identity does not determine bytes, bytes do not determine identity. | cross-run equality | Not re-observable; the generalization is narrowed by NW4 | EXE-L (absent) | UI as generalized; AO as narrowed | S-KEEP |
| U1.s4.a | DT-103 is a premise for the bytecode parts of DT-82 and DT-85 and for interpreting DT-98. | — | Reasoning holds | — | AO | S-KEEP |
| U1.s4.b | DT-103 is not a premise for diagnostics, compile success, enforcement or DT-98's field-level claim. | — | Reasoning holds | — | AO | S-KEEP |
| U1.s4.c | Co-variation of the dossier closure with the bytes (DT-98) does not establish association, because R4's closure covers a file never evaluated. | — | Reasoning holds | — | AO | S-LIMIT |
| U1.s4.d | DT-98 and DT-103 share `pw_capture_profile` in different parts: argument digests versus the object view. | — | Yes — `pw_profile_capture.h:66-71` versus `:72-85` | SRC | AO | S-KEEP |
| U1.s4.e | Different mechanisms leave one question unanswered — which file bytes the compilation consumed — and DT-103 leaves an adjacent one, what application consumed. | — | Yes | — | AO | S-LIMIT |
| U1.s4.f | Accurate statements combine to invite "compiled from this source, these parameters and these files"; R2 and R4 are counterexamples. | reader inference | Holds as narrowed by NW2 | EXE-L (absent) | CA | S-LIMIT |
| U1.s5.q1 | Even with a complete inventory: whether the compiler read the same bytes is unobserved; the receipt would carry no import identity and its join to the inventory would cross processes "through a key no reader checks"; what application consumed stays unknown. | — | Yes, with the quoted phrase superseded by NW1 | SRC | AO | S-JOIN, S-LIMIT |
| U1.s5.q2 | Every reported digest can be accurate while the association stays unestablished (R2, R4; DT-98 consistent but unchecked). | — | Holds for the file association only (NW1) | EXE-L (absent) | AO | S-LIMIT |
| U1.s5.q3 | Observed by no component: the compiler's file reads, the layout, what apply submitted. Meaning: "consumed input bytes" and "identifies compiler output" claim more coverage than the receipt has. | — | Yes — `35-profile:394`; guide frozen | SRC | IMA in the pin | S-LIMIT |
| U1.s5.q4 | DT-98 and DT-103 remain meaningful with the import findings set aside. | — | Yes | — | AO | S-KEEP |
| U1.s6 | A narrower formulation in four sentences; the fourth: "The only shared term is the source digest, which no reader compares." | — | First three hold; fourth superseded by NW1 | — | AO for 1–3 | S-JOIN |
| U1.s7 | Judgment: not an unmet promise; the disclaimers sit on the inventory side while the receipt's owner pins "consumed input bytes"; R2 is the concrete cost; no stated reason for the receipt carrying no import identity. | arrangement | Factual premises hold (and U1.s2.h shows the public inventory-side statement is a single sentence) | SRC | Judgment; CA | S-LIMIT |
| U1.s8 | Stages, compilations, changes over time and equality should stay distinct. | — | Yes | — | AO | S-KEEP |
| U1.lim | Single runs, no file-access tracing, query unavailable in E; scripts and outputs in a scratchpad. | — | The scratchpad `8e36ddab-…` is absent | — | AO | S-KEEP |

#### U2 — follow-up

| Id | Claim (receipt side) | Boundary | Holds at HEAD? | Evidence | Class | Disp. |
| --- | --- | --- | --- | --- | --- | --- |
| U2.o | Outcome: the interpretation holds as a description of a documented separation; divergence is narrower than first written; several passages need narrower wording; one new run series. | — | Yes | — | AO | S-KEEP |
| U2.s1.a | `applied_sha256`, `policy_sha256` and `source_sha256` are equal by construction: the dossier is built from the resolved value, that value is serialized once and delivered, and the host checks the worker's digest against what it received. | ordinary; one run | Yes — `run_flow.rs:607-613`, `:678-686`; `CWorkerOrchestrator.swift:220`; `CWorker.swift:706-707`. For `source_sha256` the equality is enforced only on `captured` receipts. | SRC | AO | S-JOIN |
| U2.s1.b | One test joins the receipt to the request source. | actor form; live | Yes — `check_actor_compositions.py:132-133`; also `contract.py:328` and `guide_workflows.py:469` (ordinary) | SRC | AO | S-JOIN |
| U2.s1.c | The envelope carries the request path and digests but not the source text; seeing import forms needs the retained request. | envelope | Yes | SRC | AO | S-LIMIT |
| U2.s1.d | Case table: no single envelope shows divergence; R1/E1 not observed, R3 signaled, R2/E2 and R4/E4 observed only by contrast. | five cases | Not re-observable | EXE-L (absent) | AO | S-LIMIT |
| U2.s1.e | Without a scanner miss, what remains is an unverified association (the receipt names no files; the walk is a separate earlier read); two divergence routes were not exercised. | — | Yes; still unexercised | SRC | AO | S-LIMIT |
| U2.s1.f | An expected object made by compiling the same source on the same host would match R2's bytes and would not reveal the missed import (reasoning, not run). | consumer comparison | Reasoning holds; not run | — | UI if stated as observed; AO as labelled | S-LIMIT |
| U2.s1.g | The formulation's fourth sentence should say the source association holds by construction; claims of unsignaled divergence should name DT-84 and DT-85 as the only observed sources. | — | Yes | — | AO | S-JOIN |
| U2.s2.a | For a source with an import, the identity fields do not determine the bytes; one absolute import changed between runs. | two runs | Not re-observable; structural by source | EXE-L (absent), SRC | AO | S-LIMIT |
| U2.s2.b | On this build and OS, arrangements evaluating the same rules in the same order gave identical bytes through the view. | four arrangements | Not re-observable | EXE-L (absent) | AO | S-KEEP |
| U2.s2.c | Not supported: that bytes never carry import-path information; a one-character change in a rule's literal path changed the 644-byte output. | joint-2 versus joint-3 | Not re-observable | EXE-L (absent) | AO | S-KEEP |
| U2.s3.a | The imported rule's effect, a refusal confined to its literal path, was in force in E1 and E2 and absent in E4; alternation and a sibling path rule out drift and a blanket refusal. | matched live contrast | Not re-observable | EXE-L (absent) | AO (the attribution is the investigator's inference) | S-KEEP |
| U2.s3.b | Not supported: how the compiler obtained the file; which bytes application consumed (co-variation only); the kernel mechanism; breadth beyond one operation and one pair of paths. | — | Yes | — | AO | S-LIMIT |
| U2.s4.a | `BTLEServer.sb`: one file under two names; a changed condition, not a contradiction. | import side | Import-inventory pass owns it; no receipt-side consequence | — | — | S-KEEP |
| U2.s4.b | Both system search directories are on the read-only snapshot, so the within-run window matters for imports outside it (inferred from the mount; writes not tested). | — | Inference, untested | — | UI if stated as fact | S-KEEP |
| U2.s4.c | "DT-82 never appears beside a receipt" holds for both forms in the examined callers. | `run` envelope | Yes — as U1.o4 | SRC | AO | S-KEEP |
| U2.s4.d | Outside that scope: the guide's direct `sbpl-check --request` workflow puts the helper's projection beside a receipt in the reader's hands; a fallback envelope puts DT-82 beside the dossier (source reading, not executed). | two outputs side by side | Yes by reading; guide frozen | SRC | AO | S-KEEP |
| U2.ev | Evidence for the new contrast: build `8b5de2b2`, one run per case, scripts and outputs in the scratchpad. | — | Scratchpad absent | — | AO | S-KEEP |

#### NW — passages needing narrower wording, receipt side

| Id | As written → narrower reading | Receipt-side content | Holds at HEAD? | Disp. |
| --- | --- | --- | --- | --- |
| NW1 | "which no reader compares" → the source join holds by construction; nothing joins records to compiled inputs. | The receipt's `source_sha256` is host-compared with the delivered source on every captured receipt. | Yes — U2.s1.a | S-JOIN |
| NW2 | R2 as the concrete cost → holds; observed divergence comes only from DT-84/DT-85; ordinary literal imports give an unverified association. | A captured receipt with every field correct sits beside a dossier that omits or over-includes a file. | Yes as narrowed | S-LIMIT |
| NW3 | E2/E4 show the rule included or excluded → supported and confined to the rule's path; a matched-contrast inference that says nothing about which bytes apply consumed. | Enforcement and capture co-vary; application input stays unobserved. | Yes | S-LIMIT |
| NW4 | "Bytes carry neither the import path nor the split" → true only for arrangements that evaluate the same rules in the same order; bytes do carry rule-supplied paths. | A statement about what `bytecode_b64` contains. | Yes as narrowed | S-KEEP |
| NW5 | "Separate, earlier read" → matters for imports outside the sealed system snapshot. | The worker's compile reads later than the dossier walk. | Inference from the mount; untested | S-KEEP |
| NW6 | "Contradicts the 14.8.3 comment" → a changed condition; one file under two names. | None. | Import-inventory pass | S-KEEP |
| NW7 | "DT-82 never appears beside a receipt" → holds for `run` envelopes in the examined callers; the direct workflow pairs them outside an envelope; a fallback envelope puts DT-82 beside the dossier. | A receipt and the helper projection can be laid side by side by a reader. | Yes | S-KEEP |

#### Distinctions the follow-up says still matter

| Id | Distinction | Disp. |
| --- | --- | --- |
| DX1 | Four statuses: documented separation; unverified association; observed divergence (DT-84/85 only, by contrast); signaled incompleteness. | S-LIMIT |
| DX2 | Source join (holds by construction) versus file join (no field exists). | S-JOIN |
| DX3 | "Same rules, same order, same bytes" versus "bytes never carry path information". | S-KEEP |
| DX4 | A rule's effect on one path (supported); file opens (unobserved); which bytes application consumed (unobserved). | S-LIMIT |
| DX5 | Changed OS conditions versus contradiction; one file under two names versus two files. | S-KEEP (import side) |
| DX6 | Appearing together in one envelope versus a reader putting two outputs side by side. | S-KEEP |

### 2.2 Comparison

**Stated.** `docs/contract/11-policy.surface.md:568-577` (owner; rendered at
`docs/RESPONSE.md:869-874`): "Bind each digest to the bytes held by its
producing read. The controller dossier walk, fallback helper walk and worker
native compiler perform their own reads. Preserve import errors and bounds
beside each inventory." and "Files named by imports can change between these
independent reads. A literal inventory describes the producer's walk; the worker
compiled-profile receipt has its own observation boundary."
`11-policy.surface.md:72`: "Source text, selected parameter values and imported
file bytes are distinct inputs." Receipt side, `35-profile.surface.md:96`: "The
SHA-256 digest of the UTF-8 C-string source passed to compilation … The host
compares it with its supplied source bytes"; `:104`, `:112` for parameters; pin
`:394` "Fields bind the observed worker, nonce and consumed input bytes."

**Produced.** The controller builds the dossier from the resolved request
value and serializes that value once for delivery (`run_flow.rs:607-613`,
`:678-686`). The host hashes the source it parsed (`policy_sha256`) and
requires the worker's recorded source length and digest and parameter count
and digest to equal its own before a receipt is `captured`
(`CWorker.swift:706-711`). The worker hashes the C string and the parameter
snapshot it passes to the compiler (`pw_profile_capture.h:66-71`). No component
records which files the compiler opens or which bytes application submits.

**Read or asserted.** No reader relates dossier import records to a receipt.
Three live tests compare `source_sha256` with the digest of their own request
source (`contract.py:328`, `check_actor_compositions.py:132-133`,
`guide_workflows.py:469`). No test relates a receipt to an imported file.

**Observation versus inference.** Observed (dated, not replayable): equal
identity fields beside different bytes; bytes grouping by evaluated rules;
enforcement grouping the same way. Inferred: that the captured bytes are what
application consumed; that the compiler read the bytes the walk hashed; that
system-directory imports cannot change within a boot.

### 2.3 Plausible treatments

- **S-A, reasoned retention of the separation, limit stated on the receipt
  side.** The edits are those of D-INPUT and D-VIEW in Subject 1
  (`35-profile.surface.md:85`, `:112`, `:394`, `:396`) plus a link from the
  identity definition to `policy.imports.holds`. Not build-contract inputs.
  Consequence: the receipt's owner states what its identity excludes, beside
  the one public inventory-side sentence. No check can reject prose; the
  structural fact it states is at `pw_profile_capture.h:60-71`.
- **S-B, add a controller comparison of `applied_sha256` with `source_sha256`.**
  `controller/src/porcelain_admission.rs` and `run_flow.rs` (build-contract
  inputs). It would re-confirm an equality the code already guarantees on
  captured receipts and could not establish file inputs. The management plan
  already records this. Not a candidate.
- **S-C, a live control for DT-98's contrast.** A new case in
  `tests/suites/runner_outcome_bad_request/contract.py` or `witness_contract`:
  one source importing a scratch file by absolute path, two runs, the file
  rewritten between them; assert equal identity fields, different byte digests
  and a changed dossier closure. Not a build-contract input. It would give the
  stated limit executed, retained support in place of an observation whose
  output is gone. It must reject nothing in the product; it is a witness that
  the limit is real on the tested system.
- A compiler-file observer or an application-input observer is outside the
  bounded decision ("No new compiler-file observer or authenticity claim is
  introduced") and no mechanism for one exists in the worker.

### 2.4 Recommended disposition per claim

| Code | Claims | Disposition | Reason; check or why more evidence would not change it |
| --- | --- | --- | --- |
| S-JOIN | U1.o1, U1.s2.a, U1.s2.b, U1.s5.q1 (join clause), U1.s6, U2.s1.a, U2.s1.b, U2.s1.g, NW1, DX2 | **Reasoned retention; adopt the narrowed statement.** The source association holds by construction and is enforced by the host on captured receipts; no comparison is added. | Verified by reading at HEAD. No permanent document carries the earlier "no reader compares" wording, so nothing is edited for it; the sentences added under D-INPUT must not reintroduce it. Checks that already discriminate a broken source join: `runner_outcome_bad_request/accepted_input_contract` (`contract.py:328`), `witness_contract/actor_compositions` (`:132-133`). |
| S-LIMIT | U1.o2, U1.s1.98, U1.s1.103, U1.s2.d–f, U1.s2.h, U1.s3.c, U1.s4.c, U1.s4.e, U1.s4.f, U1.s5.q1 (other clauses), U1.s5.q2, U1.s5.q3, U1.s7, U2.s1.c–f, U2.s2.a, U2.s3.b, NW2, NW3, DX1, DX4 | **Reasoned retention with the limit stated in the receipt's owner (S-A).** | **Accepted limits** are the D-INPUT and D-VIEW sentences in 1.4. They state three separate things, as the follow-up requires: the identity excludes imported files; the dossier's records come from a separate earlier read (by link, not restated); which bytes application submitted is not observed. S-C is optional: the limit is structural and holds without it. The R/E contrasts stay dated observations in the record; no permanent document should cite them as current evidence. |
| S-KEEP | U1.o3, U1.o4, U1.s2.c, U1.s2.g, U1.s2.i, U1.s3.a, U1.s3.b, U1.s3.d, U1.s4.a, U1.s4.b, U1.s4.d, U1.s5.q4, U1.s8, U1.lim, U2.o, U2.s2.b, U2.s2.c, U2.s3.a, U2.s4.a–d, U2.ev, NW4–NW7, DX3, DX5, DX6 | **Accurate observation, or reasoning that holds, needing no change.** Preserve the narrowings as written. | None of these is carried by a permanent document. NW4 and DX3 constrain future wording: do not write that compiled bytes carry no path information. NW5 and U2.s4.b are untested inferences from the mount and must not be written as fact. U2.s4.a, NW6 and DX5 belong to the import-inventory pass. |

### 2.5 Resulting user duties

1. **Do not conclude from a dossier reporting `complete` and a `captured`
   receipt that the compiled object was built from exactly the inventoried
   files.** The receipt names no file; the inventory is a separate, earlier
   read. (Shared with the import-inventory pass, which owns the scanner side.)
2. **Do not treat an enforcement result or matching bytes as showing which
   bytes application consumed.**
3. Duties 3 and 4 of Subject 1 apply unchanged.

A consumer who needs to know which imported bytes were compiled has no field
for it; that is a limit of the instrument, not a duty the consumer can discharge
from one envelope.

### 2.6 Implementation worklist

1. Carry out Subject 1 worklist steps 1 and 3 for `35-profile.surface.md:85`,
   `:112`, `:394`, `:396`; agree the one cross-link wording with the
   import-inventory pass so the two owners do not both explain the separation.
2. Optional: add S-C as a live case and cite it from the source owner's limits.
3. Regenerate and verify as in 1.6 (`source_drift`; S-C would add
   `runner_outcome_bad_request/accepted_input_contract`).

---

## Outside the review

These are not review findings and are not added to it.

1. **The capture rehearsal's premise about the completion guard.**
   `records/TRACE-ACCEPTANCE-PLAN.md` ("One captured-profile trace") says the
   rehearsal "replaces the second [guard] with a specific collection/ownership
   condition that permits application-failure exit; merely deleting the
   application guard does not reach the hypothetical", and the overhaul plan's
   receipt row asks the rehearsal to account for both guards. By source and by
   an existing executed assertion, a returned apply failure ends with `done`
   published and exit 0 (`pw_probe_runner.c:601-606`, `:1645-1654`;
   `WorkerEvidenceTests.swift:36-47`, `ok` in RET), so the completion guard
   already holds on that path and the application guard alone withholds the
   copy. The completion guard governs signal, deadline and unreaped paths. No
   test requests capture on the `.apply-failure` companion, so the receipt
   outcome on that path is source-read.
2. `tests/suites/blackbox_e2e/README.md:71-74` credits the receipt corpus with
   checking a "nested receipt version" and names Swift as a reader; neither
   holds at HEAD (worklist 1.6 step 4).
3. `docs/ARCHITECTURE.md:441-442` (authored prose) says the guide "defines the
   receipt's provenance and reading rules", and `docs/LIMITS.md:303` routes
   "receipt prerequisites" to the guide. The complete statement is
   `docs/RESPONSE.md#contract-profile`. If the limits above are stated in the
   surface, those two pointers lead to frozen text that lacks them. Repointing
   is an arrangement change in authored prose outside the frozen guide; it is
   not required by any recommendation here.
4. The surface header at `35-profile.surface.md:7` names `failure_boundaries`
   as a check suite; no file under `tests/suites/failure_boundaries` mentions a
   receipt. DT-14 already records this pattern across surfaces.
