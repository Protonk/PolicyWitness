# Delegated traces behind the CONTRACT.md examination report

**This file is second-hand.** It holds what five delegated tracing passes
returned to the report writer during the examination recorded in
`records/contract/CONTRACT-FIRST-READER-REPORT.md`. The report writer did not
re-read the source behind this content, except where the report cites the same
source without a †. Nothing here has been re-verified, corrected or tidied for
this deposit.

## What is recorded and how

- **Source of the text.** Each brief and each return below is verbatim. It was
  copied by script from the session's subagent transcripts, which still held
  both. Nothing is from summary or recollection. The transcripts themselves,
  including every intermediate search and file read a pass made, exist only in
  the session's local storage on the maintainer's machine and are not
  deposited.
- **The passes.** Five general-purpose subagents of the report writer's model,
  launched together at 2026-11-10T01:57:42Z and returned between 02:04Z and
  02:08Z. Each received only its brief. None saw another's brief or return.
- **Conditions.** Each brief forbade edits, builds, tests and generator runs.
  The tree was clean before and after.
- **Reading the returns.** A return's own labels, OBSERVED, INFERRED and
  HYPOTHESIS, are the pass's. "A test asserts" in a return describes test
  source, not a passing run.
- **Line references.** `C:N` is `docs/CONTRACT.md` and `G:N` is
  `docs/PolicyWitness.md`, both at commit `298c1805`. The returns cite the
  contract as "line N", "L N" or "CONTRACT.md:N" and other files as
  `path:line` at the same commit.
- **Layout.** Each pass has one section with four parts: the brief; the
  return; what the report writer read first-hand at the time, which is why
  some report citations to the same source carry no †; and what is now known
  to be wrong. Briefs and returns are inside four-backtick fences so that
  their own headings and tables stay as written.
- **Overlap.** C:436-441 was assigned to both pass 2 and pass 5. Pass 2 says
  it did not examine the last sentence of that range; pass 5 did.
- **Append-only.** Later delegated work is added below the fifth pass.

| Pass | Subject | Contract lines assigned | Cost |
| --- | --- | --- | --- |
| 1 | Request admission and refusals | C:1-6, C:17-20, C:60-124, C:252-291 | 64 tool calls, about 319,000 tokens, 422 seconds |
| 2 | Policy, probes, envelope, dossier, steps, lifecycle, profile | C:126-136, C:144-166, C:240-244, C:372-377, C:436-441 | 99 tool calls, about 366,000 tokens, 541 seconds |
| 3 | Actors and equipment | C:138-142, C:168-238 | 75 tool calls, about 386,000 tokens, 643 seconds |
| 4 | Transport, typed response encoding, installation and reservation | C:19-20, C:246-250, C:293-298, C:300-358 | 82 tool calls, about 373,000 tokens, 621 seconds |
| 5 | Build identity plumbing and internal host/worker identity | C:8-15, C:100, C:171, C:379-425, C:436-441 | 87 tool calls, about 316,000 tokens, 628 seconds |

## Pass 1: Request admission and refusals

Launched 2026-11-10T01:57:42.869Z; last transcript record 2026-11-10T02:04:44.870Z. Brief: 6,856 characters. Return: 21,912 characters.

**Used in the report for:** `L-01`, `L-04`, `L-08` to `L-15`, `L-32` to `L-36`; section 5 rows `request`, `policy`, `refusals`; findings `F-05`, `F-08`, `F-09`, `F-18`; section 9 (duplicated JSON keys).

### Pass 1: brief, verbatim

````text
You are helping with a READ-ONLY examination of `docs/CONTRACT.md` in the repository at /Users/raccoon/Desktop/Security/PolicyWitness (commit 298c1805, clean tree). PolicyWitness is a macOS tool: a Rust controller CLI (`controller/src`), a Swift XPC runner host (`runner/Sources`, `runner/Clients`, `runner/Services`) and a C worker (`controller/tools/pw_probe_runner`). The examination prepares the public contract for external review. The goal is to establish, per claim, whether the document's statement is traceable to reachable implementation and to tests that exercise the stated relationship. It is not to defend the document and not to manufacture findings.

HARD RULES: Do not edit, create or delete any file in the checkout. Do not build, run tests, run generators, or run any command that writes into the checkout (no `make`, `cargo`, `swift build`, `tests/run.sh`, no generator scripts). Use only Read, Grep/Glob-style searching, and read-only git commands (`git log`, `git show`, `git grep`). The shell is zsh: quote globs; an unmatched glob aborts the command.

YOUR SCOPE: the request-admission and refusal surfaces. Read all of docs/CONTRACT.md once for context, then examine these line ranges claim by claim:
- lines 1-6 and 17-20 (exact admission; no negotiation/translation/bypass; PW never rewrites a specimen)
- lines 60-124 (`request` region: contract gate, "Accepted input contract", runner selection, meaning checks, limits, maintenance)
- lines 252-291 (`refusals` region: codes, `request_failure`, path bounds, table of codes, ordering statements)

For each substantive sentence, find the code that produces, validates, rejects or interprets it, in BOTH the controller (Rust) and the runner host (Swift, including the direct-XPC path that bypasses the controller), and determine:
1. Where is the `contract` assertion checked, relative to selector validation, augment resolution, helper invocation and any child process start? Is "refuse before selectors, augments, helpers or children" true in the code's actual order, in both controller and host? What does the host compare against (what is its "running build identity")? What happens for `unbound` builds? Is there any path (flags, env vars, `_test_overrides`, fixtures, alternate subcommands, policy-check/compile helpers, dossier-only commands) where a request is processed without the gate? "no bypass" is a strong claim — look for counterexamples.
2. "Unknown fields are refused after this gate" and "CodingKeys also define the accepted fields of every request object: the root, policy, each phase, ordinary action/probe step, sandbox check, filter, attempt and `_test_overrides`" — how is unknown-key rejection actually implemented (CaseIterable CodingKeys + a key walk?) and does it cover every listed object, plus actors, extension operations, after_termination? Is `_test_overrides` accepted in release/packaged builds, and what can it change?
3. Null semantics (line 75): "Optional null values generally have the same meaning as absence" and the four listed exceptions (actor `equipment`, `required_entitlements`, phase `after_termination`, actor equipment override map). Verify each, and look for other fields that reject explicit null but are not listed.
4. Runner selection (lines 77-85): precedence of nested selector over top-level alias incl. explicit empty list; removal before XPC; recorded in runner provenance; direct XPC rejects selection fields; actor `required_entitlements` checked per actor by host; augments need string `sbpl_source`; controller splices and strips; direct XPC with unresolved fragments rejected.
5. Meaning checks (lines 87-98): each sentence. In particular "before any worker or validator is created", `attempt.args` only for exec/spawn, `filter.value` for kind none, capture nonce rules, exactly-one plan form, phase id rules, step id distinctness, absolute exec targets, `prediction_unavailable`, `unsupported_operation`.
6. Limits (lines 108-114): capacity refusal names field, actual count, maximum, before any attempts; "PW never truncates or reinterprets the plan".
7. Refusals (lines 255-291): every code in the table at lines 273-284 — does each exist in code, is it emitted, with which path? Are there emitted codes NOT in the table? `expected_contract` presence; `path` bounds (8 components, 63 UTF-8 bytes, null when not reportable; "Refused parameter keys are also withheld"); controller exit code 1 for bad_request vs other failures; `data.request_failure` "unchanged copy of the runner's request_failure"; "Capacity checks precede meaning checks"; "These refusals contain no steps or child-process observations"; "an old `schema_version`-only specimen reports missing `contract`, not an unknown-field error" (line 255); "foreign output is unsupported, malformed output remains malformed"; "Delivery failure takes precedence over interpreting a reply".
8. Line 63's example ("a foreign assertion plus an invalid runner selector reports the contract refusal and starts no client") and line 121-122 (REQUEST-GRAMMAR.md uses "the same specimens used by Swift decoding/validation tests and signed CLI/direct-XPC controls") — find the tests and fixtures (`tests/fixtures/request_contract/examples.json`, `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift`, suites under `tests/suites/` such as failure_boundaries and runner_outcome_bad_request, `tests/catalog.json`). State precisely what each test exercises: constructed inputs against a library function, or the signed built binary end to end? Does the test check ordering ("starts no client") by observation, or only the reported code?

Do NOT treat the existence of a type, field, function or test as proof. Check reachability (is the function called on the production path?) and what a test asserts.

REPORT FORMAT (your final message is consumed by another agent writing the report; be precise, not polished). For each claim group give:
- CONTRACT.md line range and a short quote
- Verdict: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / CONTRADICTED / NOT DETERMINED
- Code evidence with `path:line` citations (controller and host separately)
- Test evidence with `path:line` and what the test actually asserts; say whether it is a unit test on constructed data or an integrated control on the signed product
- Label every statement as OBSERVED (you read the code/test and it says this), INFERRED (your interpretation), or HYPOTHESIS (would need an experiment; describe the experiment, do not run it)
Then a separate list: discrepancies, places a competent reader could reach a false conclusion, statements stronger than the code, distinctions the document requires but the code does not enforce, and statements that are correct and well supported (say so explicitly). Aim for completeness over brevity, up to about 3500 words. Do not propose fixes or rewrites.
````

### Pass 1: return, verbatim

````text
REPORT: docs/CONTRACT.md request-admission and refusal surfaces (commit 298c1805, read-only; nothing built or run)

Labels: OBSERVED = read in code/test; INFERRED = my interpretation; HYPOTHESIS = needs an experiment (not run).
All paths are under /Users/raccoon/Desktop/Security/PolicyWitness/.

## A. Structure of the two admission paths (OBSERVED)

Controller, `controller/src/run_flow.rs` `run()`:
- 539 `HostFacts::collect()` (sysctl only), 540 argument parsing, 558-563 app root, manifest load, optional `PW_VERIFY_EVIDENCE=1` verification
- 594 read file, 598 `parse_request`, **602 `validate_request_contract`**
- 605-614 `--runner-mode` injection and selector parse, 615 registry/target resolution, 626/634 augment resolution
- 681 selection error returns `tool_error`, 686 augment error returns `bad_request`
- 692 strip selectors, 696 one serialization, 699 client launch

No `Command::new` occurs before line 699 on this path (grep of controller/src; INFERRED from call-site inventory). The controller performs no unknown-field, meaning or capacity checks except nested `runner.*` keys.

Host, `runner/Sources/PWRunnerCore/PWRunnerService.swift`:
- `reserveRunner` 289-322 checks the reservation message's `contract` against `PWBuildContext.contract` (297)
- `runReservedSpecimen` 328: reservation consume, then 346 JSON decode
- Root decode, `PWRunnerRequest.swift` 108-145: contract gate 110-123, then 124 `rejectUnknownRequestKeys`, then fields
- 365 `admitSpecimen` (`ProbeRunner.swift` 202-220: capacity, then meaning), 381 policy hash, 403 orchestrate (first child creation)

"Running build identity" in the host is the compile-time constant `PWBuildContext.contract`:
- generated by `meson.build:93-94` under `PW_PACKAGED_BUILD`
- otherwise `"unbound"`, or `"test:policy-witness"` under `PW_UNIT_TEST_CONTEXT` (`PWRunnerAPI.swift:155-167`)

A decoder `userInfo[.expectedContract]` override exists (`PWRunnerRequest.swift:110`). It is set only in `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift:250`; production `pwRunnerDecodeJSON` (`PWRunnerCoding.swift:27-30`) sets no userInfo.

The XPC protocol has exactly two methods (`PWRunnerAPI.swift:11-15`).

## B. Claim groups

### B1. Lines 3-6, 17-20: "Admission is exact. There is no negotiation, implicit acceptance, historical translation or bypass." / "PolicyWitness never rewrites a user's specimen."
Verdict: PARTIALLY SUPPORTED. Supported for `policy-witness run` and the XPC host. A shipped helper is a counterexample to "no bypass" if `sbpl-check` counts as request processing.

- Controller (OBSERVED): `request_patch.rs:75-100` uses exact string equality and refuses when expected is empty or `unbound`. No translation code exists.
- Host (OBSERVED): `PWRunnerRequest.swift:121`.
- No write to the request path on the run path (INFERRED): every `fs::write` in run_flow.rs, augments.rs, runner_select.rs and dossier.rs sits in a test module.
- Counterexample (OBSERVED): `controller/src/bin/sbpl-check.rs:48-58` and `433-442`. `CheckRequest` deserializes only `policy`, with no `contract` check and no `deny_unknown_fields`. Given a saved specimen with a foreign, missing or `unbound` contract, it compiles the policy with libsandbox and prints a verdict.
  - It is shipped (`README.md:114`) and documented as directly runnable (`docs/PolicyWitness.md:684-685`).
  - It applies nothing and starts no child.
  - The controller itself relies on this: `run_flow.rs:397` sends `{"policy": ...}` with no contract for actor fallbacks.
  - An `unbound` cargo build of sbpl-check also does not refuse (INFERRED from the same code). That is relevant to line 13, "refuse public requests".
- Tests:
  - Integrated, signed app: `tests/suites/runner_outcome_bad_request/contract.py:47-51` and `100-104` assert request-file bytes are unchanged for every CLI and direct-XPC case.
  - Unit: `run_flow.rs:2450`.
  - No test asserts that sbpl-check refuses or accepts by contract.

### B2. Line 63: contract gate and ordering
"requires a string `contract` exactly equal to the running build identity. Missing, null, nonstring and foreign assertions refuse before selectors, augments, helpers or children."
Verdict: SUPPORTED for both paths, with one qualification on CLI flags.

- Controller (OBSERVED): the gate at `run_flow.rs:602` precedes everything in the claim. Codes at `request_patch.rs:81-99`: `missing_field`, `missing_value`, `type_mismatch`, `unsupported_contract`.
- Host (OBSERVED): `PWRunnerRequest.swift:111-123`, same four codes, before the unknown-key walk at 124.
- Unbound (OBSERVED): both refuse with `unsupported_contract` and `expected_contract: "unbound"` (`request_patch.rs:83`, `PWRunnerRequest.swift:121`). The host also refuses reservation (`PWRunnerService.swift:297`).
- Qualification (OBSERVED): argument errors precede the gate. `--runner-mode bogus` or `machme` returns `tool_error`, exit 2, before the file is read (`run_flow.rs:449-468`, `540-549`). A foreign assertion plus an invalid selector supplied as a CLI flag therefore reports the argument error, not the contract refusal.
- `_test_overrides`, env vars and fixtures (OBSERVED): none skips the gate. `PW_RUNNER_REGISTRY` and `PW_VERIFY_EVIDENCE` only affect steps around it. `runner verify` builds its own request with the current contract (`runner_commands.rs:532-543`).

"Unknown fields are refused after this gate."
Verdict: SUPPORTED. In the host this is `PWRunnerRequest.swift:124`. The controller checks only `runner.*` (`runner_select.rs:174-187`); other unknown fields are refused by the host after client and host launch, which lines 286-287 disclose.

"Example: a foreign assertion plus an invalid runner selector reports the contract refusal and starts no client."
Verdict: SUPPORTED by code order. The exact combination is tested only at unit level.

- Unit, constructed dependencies on the production `run()`: `run_flow.rs:2424-2453`.
  - Input: foreign, numeric, null or bool contract, plus `runner.mode: "unknown-mode"`, plus an unknown augment.
  - Asserts the counting client closure was never called, exit 1, `bad_request`, and that the error contains "expected".
  - It does not assert the `request_failure` code, and does not assert the registry or augment directory were untouched.
- Integrated, signed: `contract.py:151-152` `old_marker_only` is a missing contract plus `schema_version: 6` plus `runner: {misspelled: true}`. It asserts the exact `request_failure` and (line 85) `data.runner_client is None`. That is the controller's own report, not an independent process observation.
- Integrated, opt-in, not in the default battery: `opt_in/same_shape_contract.py:123-146`. Two instrumented signed builds; a foreign assertion (no selector) gives exit 1, `runner_client` and `runner_result` null, the file effect unchanged, and neither the client nor the worker trace file exists. This is the only independent observation of "starts no client".
- Integrated, unsigned cargo binary: `controller/integration/cli_contract.rs:126-149`. `{"contract":"unbound","runner":false}` gives `unsupported_contract` and `runner_client` null.

### B3. Lines 67-75: accepted fields, unknown keys, nulls
"CodingKeys also define the accepted fields of every request object: the root, policy, each phase, ordinary action/probe step, sandbox check, filter, attempt and `_test_overrides`."
Verdict: SUPPORTED.

- Mechanism (OBSERVED): `PWRunnerCoding.swift:12-19`. `CaseIterable` CodingKeys plus a walk of `allKeys`; the first unknown key in sorted order throws.
- Called in every listed decoder: `PWRunnerRequest.swift` 124, 192, 268, 340, 369, 392, 435, 461.
- Also called for objects the document does not list: actor and actor sandbox (`PWRunnerActors.swift:40,58`), `after_termination` (73), extension action and operation (`PWRunnerExtension.swift:35,91`).
- The equipment override map has a hand-written closed key set (`PWRunnerRequest.swift:285-287`).
- `policy.params` is open data (343).
- Tests:
  - Unit, injected contract: `RequestContractTests.swift:176-195`, seven object paths.
  - Integrated: `contract.py:153-158` checks an error substring only; corpus rows `capture_typo`, `unknown_phase_field`, `actor_unknown_sandbox_field`, `actor_gate_unknown_key` and `actor_issue_raw_token` check exact code and path on CLI and XPC.
  - I found no corpus row for an unknown key directly on an actor object or on an extension action object.

`_test_overrides` in packaged builds (OBSERVED): it is accepted unconditionally; there is no build-flag gate in `PWRunnerRequest.swift:223-298`. It is reachable through the signed CLI: `tests/suites/failure_boundaries/check.py:78` expects `worker_spawn_failed` from an override path. It can change:
- the worker executable (legacy form only; `PWRunnerService.swift:399`)
- the validator executable (401)
- actor equipment executables per role
- worker and validator timeouts
- post-apply hang and kill signal, pre-ready hang, kill-before-publish slot (`CWorkerOrchestrator.swift:117-123`)

The contract gate still applies. CONTRACT.md names the object but not its powers.

"Optional null values generally have the same meaning as absence. Actor `equipment`, `required_entitlements`, phase `after_termination`, and the actor equipment override map reject explicit null."
Verdict: PARTIALLY SUPPORTED. The four exceptions are correct; a fifth class is unlisted.

- The four (OBSERVED): `PWRunnerActors.swift:62-63`, `PWRunnerRequest.swift:197`, `280-281` (`contains` then non-optional decode). Corpus rows `actor_equipment_null`, `actor_requirements_null` and `actor_gate_null` expect `missing_value` on both paths.
- Unlisted (OBSERVED): extension operands. `PWRunnerExtension.swift:23-24,38` records presence separately, and `ActorPlan.swift:409-411` refuses a present-but-null inapplicable operand with `inapplicable_field`, where absence is accepted. Corpus rows `consume_extra_null` and `consume_removed_operand_null` confirm it.
- `contract: null` is also refused, as stated at line 63.
- Null as absence elsewhere (OBSERVED): `decodeIfPresent` throughout; the controller's `runner: null`, alias nulls and `augments: null` (`runner_select.rs:91,107,164`; `augments.rs:191`). Tests: `RequestContractTests.swift:210-220`, `runner_select.rs:722-736`, corpus `optional_nulls`.

### B4. Lines 77-85: runner selection and augments
Verdict: SUPPORTED, except "resolved meaning is recorded in runner provenance", which is PARTIALLY SUPPORTED.

- Types and every entitlement entry, including shadowed aliases: `runner_select.rs:148-156` validates top-level aliases before nested fields. Test `688-719` includes `{"runner":{"id":"valid"},"runner_id":42}`.
- Unknown nested fields: `174-187`.
- Precedence, including an explicit empty list: `188-202`; test `722-736`.
- Removal before XPC: `225-231`, called at `run_flow.rs:692`. Tests `run_flow.rs:2483,2954` compare the delivered request with the stripped file.
- Provenance (OBSERVED): `RunnerProvenance` (`runner_select.rs:57-72`) records the selected target and entitlement read-backs. It has no field for the selector's `required_entitlements` demand, and is null when selection fails (`run_flow.rs:669`).
- Direct XPC rejects selection fields: follows from the root key walk. Unit `RequestContractTests.swift:234-243` shows even a null value is refused; integrated `contract.py:174` and corpus `selector*` rows.
- Actor `required_entitlements`: not stripped (only root keys are removed) and checked per actor at `ActorEquipment.swift:368-375`.
- Augments:
  - String `sbpl_source` required: `augments.rs:222-233`.
  - Splice and strip: `182`, `276-280`.
  - Direct XPC refusal: `PWRunnerRequest.swift:349`, mapped to `unresolved_augments` at `PWRunnerService.swift:208-210`. The second site at `ProbeRunner.swift:55` is unreachable for decoded requests (INFERRED).
  - Integrated: `contract.py:164-165,175`; corpus `augment` and `actor_policy_augments_direct`.
- Ordering note (OBSERVED): a selection failure is returned before an augment refusal (`run_flow.rs:681` vs `686`). A request with both an unavailable runner and an unknown augment yields `tool_error`, exit 2.

### B5. Lines 87-98: meaning checks
Verdict: SUPPORTED, with one classification discrepancy (plan form; see C2).

- "before any worker or validator is created": `admitSpecimen` at `PWRunnerService.swift:365` precedes `orchestrate` at 403. The direct orchestrator entry also admits (`CWorkerOrchestrator.swift:67`).
  - Unit: `ServiceAdmissionTests.swift:146-160` asserts zero orchestration entries for invalid JSON and a capacity refusal.
  - Integrated: `contract.py:82-83,124-125` (`runner_subprocess` and `validator_subprocess` null, effect file absent).
- Attempt pairs and filter kinds: `ProbeRunner.swift:28-29,119-120`. The closed table is `CWorkerRequestPlanning.swift:107-134`.
- `attempt.args`: `ProbeRunner.swift:122`. `filter.value` for `none`: 37-38, including an empty string.
- Nonce: 64-70; the validator is exactly 32 lowercase hex bytes (`CWorker.swift:671-676`).
- Plan form: `PWRunnerRequest.swift:137-139`, at decode time.
- Phases: `ProbeRunner.swift:85-90`.
- Query and attempt both required: non-optional decode at `PWRunnerRequest.swift:463-464`.
- Step IDs distinct across phases: `ProbeRunner.swift:113-117`, over the flattened plan.
- Absolute exec target: 125.
- `prediction_unavailable`: `CWorkerRequestPlanning.swift:320-322`. Integrated: corpus `known_unavailable_prediction`, with `contract.py:62-63,113-114` asserting the prediction outcome and an `ok` attempt with a file effect.
- `unsupported_operation`: mapped at `CWorkerStepResults.swift:158`. Admission checks only non-empty and at most 127 bytes. I did not find a signed test that asserts this outcome in these suites (NOT DETERMINED for test coverage).
- "Query and attempt scopes need not match": there is no comparison in admission (OBSERVED absence).
- Dead branches (OBSERVED): the `unrecognized_filter_kind` planner branch (`CWorkerRequestPlanning.swift:323`) and the `PW_ATTEMPT_NONE` fallback (139-141) are unreachable after admission (INFERRED).

### B6. Lines 108-114: limits
Verdict: SUPPORTED.

- Code: `CWorkerRequestPlanning.swift:13-44`, the record at `PWRunnerRequest.swift:472-490`, the reply at 265-288 with `steps: []`.
- Integrated: `failure_boundaries/check.py:131-141` asserts field, actual, maximum, unit, no subprocess and empty steps. Lines 200-240 add an independent target-file check. Corpus `over_capacity` asserts no file effect.
- "never truncates or reinterprets the plan": I found no plan truncation. Override values are clamped (`CWorkerRequestPlanning.swift:60,69`), which LIMITS.md documents; these are not plan fields.
- The controller re-serializes the request (`run_flow.rs:696`), so the host does not receive the user's bytes. HYPOTHESIS: duplicate JSON keys collapse to the last occurrence in serde_json, while Foundation's handling of duplicates on direct XPC may differ. Experiment: submit a request with a duplicated key by CLI and by `pw-runner-client`, and compare the replies.

### B7. Lines 255-291: refusals
- `expected_contract` on contract failures: SUPPORTED (`request_patch.rs:33-34,78`; `PWRunnerRequest.swift:112-122`).
- Path bounds, 8 components of 63 UTF-8 bytes, else null: SUPPORTED.
  - `PWRunnerRequest.swift:22-24`; `request_patch.rs:31-32`.
  - Units: `request_patch.rs:164-224`.
  - Two sites assign `path` after init, bypassing the bound (`ProbeRunner.swift:109`, `ActorPlan.swift:431`). The components are fixed labels and indices, at most 7 (INFERRED harmless).
- "Refused parameter keys are also withheld": SUPPORTED (`CWorkerRequestPlanning.swift:302-304`; corpus `actor_parameter_key_bytes` and `_nul`).
- Exit 1 for `bad_request`: SUPPORTED (`run_flow.rs:177-179,760`). Exit 1 is not unique to it: transport and reply refusals also exit 1 (`run_flow.rs:713`), and `tool_error` exits 2.
- A non-UTF-8 request file is `tool_error`, not `invalid_json` (`read_to_string`, `run_flow.rs:594-596`).
- "unchanged copy of the runner's `request_failure`": SUPPORTED. It is a clone of the typed record, serialized by the same impl (`run_flow.rs:751-757`; `porcelain_records.rs:3221-3229`). It is copied only when the admitted reply's outcome is `bad_request`. Integrated: `contract.py:80`. The controller applies no vocabulary or bounds check to it.
- "Capacity checks precede meaning checks": SUPPORTED inside `admitSpecimen`. Integrated: `check.py:182-195`. It is not true of rules enforced at decode time (see C2).
- "no steps or child-process observations": SUPPORTED on all three host refusal constructors (`PWRunnerService.swift:348-359`, `ProbeRunner.swift:132-139`, `CWorkerRequestPlanning.swift:280-287`).
  - A driver backstop can also classify `bad_request` without `request_failure` (`CWorkerDisposition.swift:273`). It is reachable only if driver checks diverge from admission (INFERRED unreachable).
- Line 255 example, the old `schema_version`-only specimen: SUPPORTED. Unit `request_patch.rs:232`; integrated on both paths with the exact record, `contract.py:151-152,171,190-191`.
- "foreign output is unsupported, malformed output remains malformed" and "Delivery failure takes precedence": SUPPORTED by `run_flow.rs:96-104,332-360`. The tests are unit tests on constructed captures only (`run_flow.rs:1641-1723`).

Table, lines 273-284 (OBSERVED): every listed code exists and has a reachable emit site. The only site that supports the `invalid_termination_dependency` row is `ActorPlan.swift:370-377`; its path and three conditions match the row.

Emitted codes not in the table:
- Decode time: `exclusive_plan_forms`, `actors_require_phases`, `empty_equipment_overrides` (`PWRunnerRequest.swift:132-142,284`)
- Legacy meaning: `empty_phases`, `empty_phase_id`, `duplicate_phase_id` (`ProbeRunner.swift:85-89`)
- Admission: `relative_equipment_path` (`ProbeRunner.swift:210`)
- Actor form (`ActorPlan.swift:328-509`):
  - `empty_actors`, `empty_actor_id`, `duplicate_actor_id`, `unknown_actor`, `actor_without_phases`
  - `unsupported_sandbox_mode`, `unsupported_equipment`, `empty_entitlement`, `duplicate_entitlement`
  - `empty_step_id`, `empty_reference`, `duplicate_reference`
  - `unsupported_extension_action`, `unsupported_extension_family`, `unsupported_extension_authority`, `relative_extension_target`
  - `unknown_token_reference`, `unknown_delivery_reference`, `unknown_handle_reference`, `wrong_owner_reference`, `repeated_release`, `extension_exec_unsupported`

Most of these are exercised end to end by corpus rows.

### B8. Lines 121-122: shared specimens
Verdict: SUPPORTED, with a precision note.

- `tests/fixtures/request_contract/examples.json` holds 158 rows.
- Swift: `RequestContractTests.swift:35-84`. A library-level decode plus `admitSpecimen`, with an injected expected contract `"test:request"`. It checks only the `xpc` expectation (no row has an `admission` key) and executes nothing.
- Signed controls: `contract.py:88-125`, wired by `runner_outcome_bad_request/run.sh:201-208` as case `accepted_input_contract` in the default battery. Each row goes through the built `policy-witness` and through `pw-runner-client` against the embedded service, with an independent file-effect check.

## C. Discrepancies and places a reader could reach a false conclusion

1. "No bypass" (line 6) versus `sbpl-check`. The shipped, documented helper accepts request JSON with any or no `contract` and with unknown fields.
2. "Capacity checks precede meaning checks" (287-288) versus the plan-form rule. Line 91 places "exactly one non-null plan form" among the meaning checks, but it is enforced at decode time, before capacity. So are `unresolved_augments`, `actors_require_phases` and the override-map checks. The corpus labels `phases_and_plan` as "structure".
3. The refusal table reads as the vocabulary, but about 29 emitted codes are absent. They include codes for rules the `request` region itself states (plan form, nonempty phases, unique nonempty phase IDs). Line 289 tolerates unfamiliar codes; nothing says the table is partial.
4. Null exceptions (line 75) omit extension operands, where explicit null on an inapplicable operand is refused.
5. "Resolved meaning is recorded in runner provenance" (82-83): the selected runner is recorded; the required-entitlement demand is not.
6. Line 63's example holds for selectors inside the request. An invalid `--runner-mode` flag is reported first, as `tool_error` with exit 2.
7. `_test_overrides` is listed as an ordinary accepted object. In signed builds it can substitute the worker and validator executables.
8. "Starts no client" is observed independently only by an opt-in case, and without a selector. Default-battery evidence is the envelope's own null `runner_client` or a unit-level counting closure.
9. The Swift corpus test admits against an injected contract string, not the compiled identity. The compiled-identity path is covered by the signed controls and by the opt-in SwiftPM unbound control (`same_shape_contract.py:70-83`).
10. A distinction the code does not enforce: the controller does not validate a received `request_failure` (bounds or code vocabulary) before copying it. "Unchanged copy" is exact for that reason.

## D. Correct and well supported
- Contract gate order and the four contract codes, in both controller and host, including `unbound`.
- Unknown-key rejection for every listed object and for the unlisted actor and extension objects.
- The four listed null exceptions.
- Selector validation, precedence and stripping; direct-XPC refusal of selectors and unresolved augments.
- Each meaning rule in lines 87-94 and its position before child creation.
- Capacity refusal content and its precedence inside admission.
- Path bounds and parameter-key withholding.
- The old-marker example.
- Request file never modified.
- Corpus sharing between the lesson, the Swift tests and the signed controls.
````

### Pass 1: read first-hand by the report writer at the time

These readings were made to check the return before the report was written. They are the report writer's own and are not part of the return.

- The controller gate and its order: `controller/src/request_patch.rs` in full and `controller/src/run_flow.rs:560-640`.
- The host gate: `runner/Sources/PWRunnerCore/PWRunnerRequest.swift:104-146`.
- The helper without a contract check: `controller/src/bin/sbpl-check.rs:44-60` and `:428-445`; the guide at G:676-700.
- The 29 unlisted codes and the 22 listed codes, by a literal search of `runner/Sources` and `controller/src` and of the three documents.
- The extension-operand null rule: `PWRunnerExtension.swift:20-26`, `ActorPlan.swift:405-413`.

### Pass 1: now known to be wrong, and other notes

- Nothing in this return is known to be wrong.
- The return says "about 29" unlisted codes. The author's own search found exactly the 29 it names.

## Pass 2: Policy, probes, envelope, dossier, steps, lifecycle, profile

Launched 2026-11-10T01:57:42.889Z; last transcript record 2026-11-10T02:06:43.712Z. Brief: 7,275 characters. Return: 21,934 characters.

**Used in the report for:** `L-16`, `L-17`, `L-19` to `L-22`, `L-30`, `L-43`; section 5 rows `policy`, `probes`, `envelope`, `dossier`, `steps`, `lifecycle`, `profile`; findings `F-04` (rows for `policy`, `probes`, `envelope`, `dossier`, `steps`, `lifecycle`, `profile`), `F-05`, `F-06`, `F-07`, `F-18`, `F-19`; section 9.

### Pass 2: brief, verbatim

````text
You are helping with a READ-ONLY examination of `docs/CONTRACT.md` in the repository at /Users/raccoon/Desktop/Security/PolicyWitness (commit 298c1805, clean tree). PolicyWitness is a macOS tool: a Rust controller CLI (`controller/src`), a Swift XPC runner host (`runner/Sources`, `runner/Clients`, `runner/Services`) and a C worker (`controller/tools/pw_probe_runner`). The examination prepares the public contract for external review. The goal is to establish, per claim, whether the document's statement is traceable to reachable implementation and to tests that exercise the stated relationship. It is not to defend the document and not to manufacture findings.

HARD RULES: Do not edit, create or delete any file in the checkout. Do not build, run tests, run generators, or run any command that writes into the checkout (no `make`, `cargo`, `swift build`, `tests/run.sh`, no generator scripts). Use only Read, Grep/Glob-style searching, and read-only git commands. The shell is zsh: quote globs; an unmatched glob aborts the command.

YOUR SCOPE: the short normative regions for policy, probes, envelope, dossier, steps, lifecycle and profile. Read all of docs/CONTRACT.md once for context, then examine these line ranges sentence by sentence:
- lines 126-130 (`policy`): augments resolved by controller "in memory before submission"; direct XPC refuses unresolved augments; "Imports and hashes describe the held policy input and its closure"; example "a missing augment refuses before worker creation and leaves the input file unchanged".
- lines 132-136 (`probes`): unique step ID, query and attempt; closed vocabularies; "Predictions are observations distinct from attempts and do not establish enforcement agreement"; example "file `open_write` opens with truncation; a same-shape foreign build assertion prevents that operation".
- lines 144-148 (`envelope`): the five envelope keys; `build.contract` identifies producer; "Readers admit it before semantic fields"; "Nested helper envelopes have independent build context"; "Unsupported received bytes remain available without inferred claims"; example "a foreign helper envelope claiming compilation cannot supply a successful policy-check status". Also lines 436-441 ("Build stamp": every envelope carries build.contract, build.describe, build.commit, build.version, build.number).
- lines 150-154 (`dossier`): what the dossier records; "Unknown observations remain unknown"; "The submitted serialization and fallback compiler use the same held input"; example "changing the source file after admission does not change the held submission".
- lines 156-160 (`steps`): host reply carries `producer.contract/describe/commit`; "Admission is exact before interpreting steps"; comparisons; "permission-shaped failures do not prove a sandbox cause"; "`query_first` requires the collection/release evidence chain"; example "a foreign host reply inside a current envelope yields one unsupported diagnostic without recovered comparisons".
- lines 162-166 (`lifecycle`): claims depend on native progress, collection and termination observations; unknown/contradictory observations withhold dependent claims; "An exit request is not proof of reap; successful return alone is not an effect witness"; example "an unreaped worker remains unconfirmed even after a successful termination request".
- lines 240-244 (`profile`): receipt inherits admitted host reply context; "no independent schema marker"; "Status, nonce, worker binding, stage, byte count and digest must be consistent; a detached receipt grants no producer context"; example "a wrong nonce refuses the receipt even inside a current reply".
- lines 372-377: "Historical captures keep their bytes and are rejected if their producer is unsupported. Authored request templates carry no identity; the harness asserts the independently inspected candidate at submission. Constructed response tests supply an explicit producer context."

Key questions:
1. Who are the "readers" of envelopes? Find every place the controller (or test harness `tests/lib/*.py`, e.g. `tests/lib/contract.py`) reads an envelope or a host reply, and establish whether `build.contract` / `producer.contract` is compared for exact equality BEFORE any semantic field is used. Is there any reader that interprets fields without admission? What does the controller do with a helper's (e.g. `sb_api_validator`, policy-check/compile helper) nested envelope — where is its build context checked, and against what? Does "exact" mean string equality with the controller's compiled identity?
2. For a foreign host reply: follow `porcelain_admission.rs`, `run_flow.rs`, `runner_client.rs` etc. What is emitted ("one unsupported diagnostic")? Are the raw bytes retained in output (base64)? Are comparisons withheld?
3. Compiled-profile receipt: where are status/nonce/worker binding/stage/byte count/digest checked for consistency, and what does "refuses the receipt" produce?
4. Dossier: how is the request "held" (read once into memory? file descriptor?) and does the fallback compiler really use the same held bytes as the submission? What is the "fallback compiler"?
5. Lifecycle/steps: where are claims withheld on unknown/contradictory observations; where is `query_first` gated on the collection/release chain (C worker + Swift host + Rust admission)? Is the withholding implemented in the producer, in the controller's admission, or both?
6. Each "Example:" sentence in these regions asserts a concrete behavior. The document calls examples "verified examples" (line 104, 365). For each example find the test that verifies it (search `tests/suites/`, `tests/fixtures/`, `tests/catalog.json`, `runner/Tests`, Rust `#[cfg(test)]` modules) and say exactly what it asserts and whether it runs against the signed product or constructed data. If you find no test for an example, say so plainly.
7. The manifest `docs/contract_surfaces.json` names a `checks` suite per surface (e.g. policy→integration, probes→witness_contract, envelope→unit, dossier→witness_contract, steps→failure_boundaries, lifecycle→runner_unit, profile→failure_boundaries). Look at `tests/catalog.json` and the named suites: does the named suite actually exercise that surface's claims?

Do NOT treat the existence of a type, field, function or test as proof. Check reachability and what a test asserts.

REPORT FORMAT (your final message is consumed by another agent writing the report; be precise, not polished). For each claim group give:
- CONTRACT.md line range and a short quote
- Verdict: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / CONTRADICTED / NOT DETERMINED
- Code evidence with `path:line` citations
- Test evidence with `path:line` and what the test actually asserts; unit-on-constructed-data vs integrated control on the signed product
- Label every statement as OBSERVED, INFERRED, or HYPOTHESIS (would need an experiment; describe it, do not run it)
Then a separate list: discrepancies, places a competent reader could reach a false conclusion, statements stronger than the code, distinctions the document requires but the code does not enforce, and statements that are correct and well supported (say so explicitly). Aim for completeness over brevity, up to about 3500 words. Do not propose fixes or rewrites.
````

### Pass 2: return, verbatim

````text
Scope: docs/CONTRACT.md lines 126-166, 240-244, 372-377, 436-441 at 298c1805. Everything below was read from source; no test, build or generator was run, so "test asserts X" means the source asserts X, not that it passed. Labels: OBSERVED = read in source; INFERRED = follows from what was read; HYPOTHESIS = needs an experiment.

Note on the brief: `tests/lib/contract.py` holds only the generated worker identity (5 lines). The harness producer gate is `tests/lib/document_versions.py:8-38`, used by `tests/lib/consumer.py:31, 900-923`.

## Readers and what "exact" means (Q1)

OBSERVED. "Exact" is string equality with the compiled constant `BUILD_CONTRACT` (`controller/src/json_contract.rs:10-22`, from `PW_BUILD_CONTRACT`, else `"unbound"`). An `unbound` build admits nothing, including itself. Readers:

- **Helper envelope (sbpl-check)**: `controller/src/policy_check.rs:47-60`. Reads `kind` first, then `build.contract`, then `result.normalized_outcome`. Anything else becomes status `invalid_reply`. This is the only controller reader of a JSON helper envelope (`capture_json_output` has one production caller, `policy_check.rs:80`).
- **Client capture**: `controller/src/porcelain.rs:174-222` (`decode_bound`) checks frame magic and fingerprint, walks the root record to the contract tag, compares, and only then does the full decode. Rechecked at `runner_client.rs:718` and `:262-264`.
- **Host reply**: `runner_client.rs:743-765` calls `decode_bound(.., false, BUILD_CONTRACT)`, which decodes the whole `PWProducer` record then compares `contract`. A foreign producer never becomes a typed record.
- **Second gate**: `run_flow.rs:96-104` (`reply_contract`), also used by `runner verify` (`runner_commands.rs:549-560, 632`).
- **Test harness**: `document_versions.py:16-32` returns exactly one error for envelope `build.contract`, then one for `data.runner_result.producer.contract`.
- **Host (producer side)**: `PWRunnerAPI.swift:176`; a foreign producer is refused before binary writing (`ReplyFailureTests.swift:371-378`).

INFERRED. In production the `ReplyVersion::Unsupported` arm (`run_flow.rs:97-98, 348-354`) is unreachable, because `decode_bound` already refused with the same comparison. Only tests that inject a typed reply reach it.

I found no controller reader that interprets semantic fields before admission. Structural items (frame fingerprint, record id, leading tags, helper `kind`) are read first.

## policy (lines 126-130)

**"Named augments are resolved by the controller in memory before submission" — SUPPORTED.**
- Code (OBSERVED): `controller/src/augments.rs:72-81, 164-287` mutates the parsed value; `run_flow.rs:625-634` resolves; `:696-703` serialises once and delivers.
- Tests: `controller/integration/cli_contract.rs:838-947` (signed app); `tests/suites/witness_contract/check_dossier.py:192-208` (signed app; reply `policy_sha256` equals `applied_sha256`).

**"direct XPC refuses unresolved augments" — SUPPORTED.**
- Code: `runner/Sources/PWRunnerCore/PWRunnerRequest.swift:347-349`; `ProbeRunner.swift:54-57`.
- Tests: `runner/Tests/PWRunnerCoreTests/AugmentTests.swift:30-41` (constructed decode); `tests/suites/runner_outcome_bad_request/contract.py:96-123` with `tests/fixtures/request_contract/examples.json:875, 5247` (signed app, direct XPC, independent file-effect check). Neither is in the manifest's `integration`.

**"Imports and hashes describe the held policy input and its closure" — SUPPORTED, with limits.**
- Code: `run_flow.rs:254-291`; `dossier.rs:62-112, 151-173`.
- Hashes cover `sbpl_source` strings only. Neither params nor the held request is hashed in the dossier.
- The closure is the controller's own bounded scan at dossier time; `complete` "does not mean compiler-complete" (`dossier.rs:114-117`).
- `check_dossier.py:165, 189` checks only that `closure_sha256` is 64 characters long. `system.sb`'s hash is independently recomputed (`:187`).

**Example "a missing augment refuses before worker creation and leaves the input file unchanged" — PARTIALLY SUPPORTED.**
- First half: `cli_contract.rs:950-1035` and `check_dossier.py:210-229` (both signed) assert exit 1, `bad_request`, `runner_client` null, `runner_result` null. The witness is non-invocation of the client, not an independent process observation.
- Second half: no test asserts it. `cli_contract.rs:971` deletes the request file before any assertion. `check_dossier.py:139-141, 228` checks only that no temp request file appeared.
- INFERRED true from code: the run path's only access to the file is `read_to_string` (`run_flow.rs:594`).
- Nearby tests assert unchanged bytes for a contract refusal instead: `run_flow.rs:2424-2453` and `runner_outcome_bad_request/opt_in/same_shape_contract.py:137-139`.
- OBSERVED ordering: a selection failure is returned before an augment refusal (`run_flow.rs:681-688`), so a missing augment plus an unselectable runner yields `tool_error` exit 2.

## probes (lines 132-136)

**Unique step ID, query and attempt; closed vocabularies — SUPPORTED.**
- Code: `ProbeRunner.swift:29, 117, 120`.
- Tests: `tests/suites/failure_boundaries/check.py:166-167` (signed) and the `runner_outcome_bad_request` examples. None in `witness_contract`.

**"Predictions are observations distinct from attempts and do not establish enforcement agreement" — SUPPORTED.**
- Code: `CWorkerComparison.swift:6-11, 75-152`; no agreement field in `PWRunnerStepEvidence.swift:26-56`.
- Tests (signed): `witness_contract` cases `prediction_target_is_independent_of_attempt_target` and `comparison_matrix`; `runner_exec_dac` (an EACCES under an allow answer recorded as `permission_failure`).

**Example — PARTIALLY SUPPORTED by default tests; fully covered only by an opt-in case.**
- Truncation: `controller/tools/pw_probe_runner/pw_probe_runner.c:455-458` opens with `O_WRONLY | O_TRUNC`. Test: `tests/suites/run_effects/check_file_actions.py:32` with `effects.py:42-47` (signed, default) asserts one `x` byte, same dev/inode, same mode.
- "A same-shape foreign build assertion prevents that operation": only `runner_outcome_bad_request/same_shape_contract` (`tests/catalog.json` `default: false`; needs identity, meson, swift). `same_shape_contract.py:125-150` builds two signed, instrumented variants and asserts `bad_request`, `expected_contract`, null client and reply, unchanged seed bytes and no launch traces.
- The default foreign-contract control uses `create`, not `open_write` (`contract.py:147-193`).

## envelope (lines 144-148, 436-441)

**Five envelope keys and five build keys — SUPPORTED.**
- Code: `json_contract.rs:66-99`; `sbpl-check` shares the frame.
- Tests: `json_contract.rs:171-234` (constructed); `cli_contract.rs:151-177` (signed, `--version` only; all five build keys non-empty and not "unknown").

**"Readers admit it before semantic fields" — SUPPORTED** for every reader listed above.
- Tests: `policy_check.rs:175-235` and `runner_client.rs:1225-1265` (constructed bytes); `tests/suites/blackbox_e2e/checker_controls.py:446-477` (constructed, harness reader).

**"Nested helper envelopes have independent build context" — SUPPORTED** (`policy_check.rs:51`; `consumer.py:273-291`).

**"Unsupported received bytes remain available without inferred claims" — PARTIALLY SUPPORTED.**
- Exact for binary frames: a rejected capture is kept as base64 (`runner_client.rs:773-781`); a foreign host reply stays in the typed capture's `runner_reply.data`. Tests: `runner_client.rs:1259, 1303, 1338, 1369`.
- For a helper envelope that parses, the controller keeps a `serde_json::Value` (`policy_check.rs:30, 99`; `utils.rs:175-183`), not bytes. `controller/Cargo.toml` uses plain `serde_json`, so the value is re-serialised (INFERRED: key order, duplicate keys and number spelling are not preserved).
- Unparsed or oversized helper stdout is kept as lossy UTF-8 text cut at 8 MiB (`utils.rs:91-96, 183, 10`).
- "Without inferred claims" holds (`policy_check.rs:204-208, 226-234`).

**Example "a foreign helper envelope claiming compilation cannot supply a successful policy-check status" — SUPPORTED on constructed data only.**
- `policy_check.rs:204-208, 226-234`: outcome "ok", `data.compiled: true`, foreign contract gives `invalid_reply` with the envelope retained. In `unit/rust.unit`, which matches the manifest.
- Harness-reader counterpart: `checker_controls.py:80-105`.
- No signed-product control exists.

## dossier (lines 150-154)

**What the dossier records — SUPPORTED, with one wording gap.**
- Code: `dossier.rs:26-37`. Test: `check_dossier.py:118-175, 248-355` (signed; independent `sw_vers`/`uname`, manifest and file hashes).
- OBSERVED gap: for the built-in runner all four `binaries` records are null and nothing is hashed (`dossier.rs:444-450, 458, 365`; asserted at `check_dossier.py:133`). Hashing happens only for BYOXPC, overrides, or `PW_VERIFY_EVIDENCE=1` (`run_flow.rs:232-235`).
- The dossier records the path string, not a digest of the held submission.

**"Unknown observations remain unknown" — SUPPORTED.**
- Code: `dossier.rs:176-197, 245-258, 497-514`.
- Tests: `dossier.rs:1009-1044` (unit); `check_dossier.py:292-305, 339-347` (signed).

**"The submitted serialization and fallback compiler use the same held input" — SUPPORTED by code; tested only with constructed dependencies.**
- Held means: the file is read once into a `String` (`run_flow.rs:594`), parsed, mutated, and serialised once (`:696`). There is no file descriptor and no reread. It is a re-serialisation, not the file's bytes.
- The fallback compiler is `sbpl-check --request -` (`policy_check.rs:65-75`), run only when the client terminal is `xpc_error` (`runner_client.rs:642-652`); it receives the same `held` string (`run_flow.rs:715, 733-735`).
- In the actor form it additionally receives per-actor `{"policy": …}` strings built from the same in-memory value (`run_flow.rs:385-405`).
- No suite under `tests/suites` runs the real fallback (grep: `policy_check` is asserted null or constructed everywhere).
- HYPOTHESIS: on a signed build, force a client `xpc_error`, replace the request file mid-run, and compare `policy_check.envelope.data.policy_sha256` with `augmentation.applied_sha256`.

**Example "changing the source file after admission does not change the held submission" — SUPPORTED on constructed orchestration only.**
- `run_flow.rs:2666-2836`: the injected client rewrites the file (`:2741`); the test asserts the fallback input equals the delivered held string (`:2798-2806`).
- The rewrite happens after delivery, so it shows the fallback does not reread.
- Not in `witness_contract`.

## steps (lines 156-160)

**"A host reply carries producer.contract/describe/commit" — SUPPORTED** (`porcelain_records.rs:5091-5095`; `PWRunnerAPI.swift:176`).

**"Admission is exact before interpreting steps" — SUPPORTED** for producer identity (see readers above).
- OBSERVED distinction: full semantic admission (`porcelain_admission.rs:1416-1486`) is not a gate. Its failure sets `runner_sandbox_diagnostics` to `withheld`/`invalid` (`:1631-1636`), while `data.runner_result` is published unchanged and `result.ok` follows only `normalized_outcome == "finished"` (`run_flow.rs:748-760`). Test: `run_flow.rs:1023-1076` asserts exit 0 with `disposition_integrity: invalid`.

**Comparisons; "permission-shaped failures do not prove a sandbox cause" — SUPPORTED** (`CWorkerComparison.swift:92-108`; `runner_exec_dac`).

**"`query_first` requires the collection/release evidence chain" — SUPPORTED at four places (Q5).**
- Worker acknowledgement: `pw_probe_runner.c:1243-1260`.
- Host derivation: `PWRunnerStepEvidence.swift:14-24, 107-110`; `CWorkerStepResults.swift:75-80`.
- Host reporting re-check, which degrades to `runner_reporting_failed`: `PWRunnerReply.swift:356-359`.
- Controller cross-check, which flags but does not rewrite: `porcelain_admission.rs:1166-1208`.
- Harness: `consumer.py:218-252`.
- Tests: `failure_boundaries/check.py:352-363, 407` (signed; `query_first` only beside an eligible native prediction); `witness_contract` cases `queries_precede_attempts` and `attempt_effects_wait_for_collection` (signed, default); `order_barrier_mutations` (opt-in).

**Example "a foreign host reply inside a current envelope yields one unsupported diagnostic without recovered comparisons" — SUPPORTED, but literally it describes the harness reader (Q2).**
- Product (OBSERVED): `runner_client.rs:757-768` then `:614-624` gives `unsupported_runner_response`, exit 1 (`run_flow.rs:713`), `runner_result` null, diagnostics null (`:107-125, 731`), raw reply bytes as base64 in the typed capture. The message appears in both `result.error` and `runner_client.runner_reply_error`. No fallback compile runs.
- A current envelope containing a foreign `runner_result.producer` cannot be produced by the controller (INFERRED). That exact shape is tested as a constructed document against `document_versions.py`: `checker_controls.py:452-477` asserts one error and that the steps and lifecycle readers raise.
- Signed, live evidence exists only opt-in: `tests/suites/runner_byoxpc/opt_in/reservation_controls.py:543-586` (controller outcome, null `runner_result`, preserved bytes, one execution).
- `run_flow.rs:2569-2621` injects a typed foreign reply and asserts `runner_result == reply` (`:2619`), a state production cannot reach.
- Nothing in `failure_boundaries` covers this.

## lifecycle (lines 162-166)

**All four sentences — SUPPORTED, in both producer and controller.**
- Producer: `CWorkerDisposition.swift:102-115` (`reaped != true` gives `unresolved("no_successful_reap")` whatever the kill result) and `:170-213`.
- Controller: `porcelain_admission.rs:382-760` and `:1323-1354` (`unresolved` projects to `unconfirmed`; any issue to `withheld`).

**Example "an unreaped worker remains unconfirmed even after a successful termination request" — SUPPORTED across three tests, none end-to-end on the signed product.**
- Real host driver with a fixture child and an injected `waitpid` fault: `CWorkerLifecycleTests.swift:458-469` (`reaped: false`, kill rc 0).
- Resolver, constructed: `DispositionResolverTests.swift:410-419`.
- Controller projection, constructed: `porcelain_admission.rs:2058-2105` (asserts `unconfirmed`).
- The two Swift tests are in `runner_unit` (matches the manifest); the Rust one is in `unit`.

## profile (lines 240-244)

**"Inherits its admitted host reply context" — SUPPORTED.**
- Code: `porcelain_admission.rs:1289-1312`, called only after the producer check (`run_flow.rs:96-103`).
- Test: `run_flow.rs:1614-1638` (constructed).

**"No independent schema marker" — SUPPORTED by structure** (`porcelain_records.rs:31-50`), but contradicted in wording elsewhere:
- `docs/PolicyWitness.md:655-656` (this surface's listed definition) says "Readers require the nested receipt version".
- `PWRunnerProfileCapture.swift:4` says "Versioned optional receipt".

**"Status, nonce, worker binding, stage, byte count and digest must be consistent" — PARTIALLY SUPPORTED; stronger than any reader (Q3).**
- Host at production checks all of them against worker shared memory: `CWorker.swift:678-716` (PID `:692`, nonce `:693-695`, extent `:697-699`, digest `:702-703`, inputs `:705-709`). Failure yields `status: "unavailable"` with a reason, not a refusal.
- Readers check only status, producer and stage: controller `porcelain_admission.rs:1300-1309`; host reporting `PWRunnerProfileCapture.swift:29-48`; harness `consumer.py:538-551`.
- OBSERVED: `porcelain_admission.rs:2713-2742` builds a `captured` receipt with nonce, length, digest and bytecode all `None` and asserts the controller admits it.
- The 19 cases in `tests/fixtures/contract/compiled_profile.json` vary only status, producer and stage.

**"A detached receipt grants no producer context" — NOT DETERMINED.** No reader takes a detached receipt and no test names one.

**Example "a wrong nonce refuses the receipt even inside a current reply" — UNSUPPORTED as written.**
- Nearest test: `CompiledProfileCaptureTests.swift:67-76` flips a nonce byte in constructed shared memory and asserts `unavailable` with no bytecode. That is before any reply exists, and it is in `runner_unit`.
- Signed tests assert only the positive case (`contract.py:65, 116`; `check_actor_compositions.py:127`).
- INFERRED: a current reply carrying a `captured` receipt with a different nonce would be admitted by the controller.
- When a receipt is refused for status/producer/stage, the result is `malformed_runner_response` exit 1, and the typed reply including the receipt is still published in `data.runner_result` (`run_flow.rs:355-358, 731`).

## lines 372-377

**"Historical captures keep their bytes and are rejected if their producer is unsupported" — PARTIALLY SUPPORTED.**
- Files exist under `tests/fixtures/disposition/response23`, `response24`, `response25`, plus `a1_known_loss.json`. No test opens them (grep: only READMEs and `tests/atlas/ATLAS-BUILD-PLAN.md`).
- `disposition_controls.py:251-272` rejects a constructed `{'build': {'contract': 'test:previous'}, …}` instead.
- OBSERVED: the captures have `schema_version` and no `build.contract` or `producer`. INFERRED: `document_versions.py:8-14` would report them as "malformed … missing or nonstring contract", not "unsupported".
- Nothing checks their bytes mechanically. `git log` shows each file modified once after it was added (for example `deb67eff` on `response25/a1_expected.json`, a re-capture the day after).

**"Authored request templates carry no identity; the harness asserts the independently inspected candidate at submission" — SUPPORTED where the helper is used.**
- `build_context.py:11-25` (reads `PWContract` from the app plist; raises on a template with a marker); `cli_contract.rs:66-97`.
- Many cases build requests inline with `candidate_contract()`. I found no tree-wide check that every template lacks a marker.

**"Constructed response tests supply an explicit producer context" — SUPPORTED** (`blackbox.py:34-51`; `build_context.py:28-29`; `reply_fixtures.rs:241-252`).

## Manifest `checks` versus what the suite exercises (Q7)

`docs/generate_contract_stamps.py:55-56` checks only that the suite name exists in the catalog.

| Surface | Named suite | Does it exercise the surface's claims? |
| --- | --- | --- |
| policy | integration | Augment application and refusal, import provenance. Not the direct-XPC refusal, not "file unchanged". |
| probes | witness_contract | Prediction and attempt separation, ordering. Not unique ID, closed vocabularies, or the example. |
| envelope | unit | Yes, on constructed data, including the example. |
| dossier | witness_contract | Dossier contents and unknowns on the signed app. Not the held-input sentence or the example (those are in `unit`). |
| steps | failure_boundaries | `query_first` versus `unestablished` on the signed app. No producer admission, not the example. |
| lifecycle | runner_unit | Yes for the producer; the `unconfirmed` projection is in `unit`. |
| profile | failure_boundaries | Nothing. `check.py`, `README.md` and `run.sh` contain no "profile" or "nonce". Receipt checks are in `unit`, `runner_unit` and `blackbox_e2e/checker_controls`. |

## Discrepancies and places a reader could reach a false conclusion

1. **profile**: the consistency sentence and the wrong-nonce example read as reader behaviour. No reader checks nonce, worker binding, byte count or digest, and a controller test admits a `captured` receipt lacking all of them. The host's check produces `unavailable`, not a refusal.
2. **profile**: CONTRACT.md's "no independent schema marker" conflicts with `docs/PolicyWitness.md:655-656` and a Swift comment.
3. **profile → failure_boundaries** names a suite with no profile coverage; **probes → witness_contract** and **steps → failure_boundaries** do not contain their examples.
4. **"Verified examples"** (lines 104, 365): three examples are not verified by any default case.
   - policy: the "file unchanged" half has no assertion.
   - probes: the foreign-build half is opt-in only.
   - profile: the wrong-nonce example has no matching test.
   
   Three more are verified only on constructed data: envelope, dossier, and steps (whose live control is opt-in).
5. **envelope**: "bytes remain available" is exact for binary frames only; helper envelopes are kept as re-serialised JSON or lossy, capped text.
6. **steps**: "Admission is exact before interpreting steps" covers producer identity. A reply failing semantic admission is still published in full, with exit 0 if `finished`; the withholding is in `runner_sandbox_diagnostics`.
7. **steps example**: the shape "foreign reply inside a current envelope" is a harness-reader state. A Rust orchestration test asserts a typed foreign reply published as `runner_result`, which production cannot reach.
8. **dossier**: "observed binary inventory" is four nulls with no hashing on the default built-in path.
9. **lines 372-377**: the historical captures are never read by a test, and would be classed malformed rather than unsupported.
10. **Withholding** is implemented in both producer and controller for lifecycle and `query_first`. For the receipt it is producer-only.

## Correct and well supported

- Exact string admission of client capture, host reply and helper envelope before interpretation, with raw frame bytes retained.
- Controller-side in-memory augment resolution, and direct-XPC refusal with a signed control.
- A single held serialisation with no reread or write of the request file (code).
- `open_write` truncation, with a signed default effect test.
- The `query_first` chain, enforced in worker, host, controller and harness, with signed default tests.
- Lifecycle: no reap means unresolved, which projects to `unconfirmed`.
- No agreement or sandbox-cause field in the comparison record.
- Constructed tests carrying an explicit producer context.

Not examined: the release-tag sentence at lines 440-441 (build pipeline).
````

### Pass 2: read first-hand by the report writer at the time

These readings were made to check the return before the report was written. They are the report writer's own and are not part of the return.

- The receipt reader and its test: `controller/src/porcelain_admission.rs:1286-1313` and `:2710-2744`.
- The host receipt check: `runner/Sources/PWRunnerCore/CWorker.swift:676-716`.
- The guide's receipt sentences: G:648-660.
- That `tests/suites/failure_boundaries/check.py`, `README.md` and `run.sh` contain neither "profile" nor "nonce".
- Publication after semantic admission: `controller/src/run_flow.rs:740-762`, `porcelain_admission.rs:1416-1452` and `:1622-1638`.

### Pass 2: now known to be wrong, and other notes

- Nothing in this return is known to be wrong.
- The brief was wrong on one point, and the return says so: it named `tests/lib/contract.py` as a harness reader. That file holds only the generated worker identity.
- The return ends "Not examined: the release-tag sentence at lines 440-441". The brief had assigned C:436-441. Pass 5 covered that sentence.

## Pass 3: Actors and equipment

Launched 2026-11-10T01:57:42.896Z; last transcript record 2026-11-10T02:08:25.914Z. Brief: 7,089 characters. Return: 35,120 characters.

**Used in the report for:** `L-18`, `L-23` to `L-29`; section 5 rows `actors`, `equipment`; findings `F-04` (row for `equipment`), `F-07`, `F-12` (undefined terms), `F-15`, `F-18`. The report's phrase "table in the delegated trace" at `L-28` refers to the conjunct table in this return's section 7.4.

### Pass 3: brief, verbatim

````text
You are helping with a READ-ONLY examination of `docs/CONTRACT.md` in the repository at /Users/raccoon/Desktop/Security/PolicyWitness (commit 298c1805, clean tree). PolicyWitness is a macOS tool: a Rust controller CLI (`controller/src`), a Swift XPC runner host (`runner/Sources`, `runner/Clients`, `runner/Services`) and a C worker (`controller/tools/pw_probe_runner`). The examination prepares the public contract for external review. The goal is to establish, per claim, whether the document's statement is traceable to reachable implementation and to tests that exercise the stated relationship. It is not to defend the document and not to manufacture findings.

HARD RULES: Do not edit, create or delete any file in the checkout. Do not build, run tests, run generators, or run any command that writes into the checkout (no `make`, `cargo`, `swift build`, `tests/run.sh`, no generator scripts). Use only Read, Grep/Glob-style searching, and read-only git commands. The shell is zsh: quote globs; an unmatched glob aborts the command.

YOUR SCOPE: the actors and equipment surfaces. Read all of docs/CONTRACT.md once for context, then examine these line ranges sentence by sentence:
- lines 138-142 (`actors` region): single-worker form vs actors/phases; "Every sandboxed process is fresh; an actor applies its policy once"; phases name the active actor and preserve action order; "Extension transfer and consumption use explicit owned records"; example "a phase naming a nonexistent actor is refused before children".
- lines 168-238 (`equipment` region including "Actor evidence ownership"). This is the densest part of the document. Every sentence states a constraint on reply evidence. Lines of particular interest:
  * 171: "Actor evidence binds observations to the named process and service-sealed equipment. The worker ABI identity remains independent of the public build identity. Worker entitlements are read from the selected binary. Example: an equipment hash mismatch prevents use of the claimed equipment."
  * 176-181: no declaration reply or singular worker projection; `actors[]` ownership; `authority_setup.host` scopes and `authority_setup.workers` cells; "An acquired decision does not publish another cell, and a scheduling summary does not replace any actor's facts."
  * 183-196: `equipment_inventory`, `equipment_bindings`, `equipment_entitlements`, `binding_ref`/`entitlements_ref` zero-based indexes, null `binding_ref`, `unverified_fixture`, static and live XML read-backs, "boolean true keys", runtime inspection failure semantics vs `preparation_failure`.
  * 198-202: `preparation_failure` admits only two stage/code pairs, with `runner_failed`, `rc: 1`, no launched actors, empty observation arrays, and the "sole exception" about declarative phase/action identities.
  * 204-210: `actors[].application` closed state/basis pairs (`not_requested/unapplied_declaration`, `not_attempted`, `observed`, `unobserved`) and what cannot establish nonattempt.
  * 212-228: termination dependencies: `owned_reap` fields, `activation_observation`, `capture_ordinal` local to the source actor, `termination_gate.observation`, requirements for nonnull observations and for a satisfied gate, timestamps, usable clock, allowance; "An abnormal natural reap can satisfy termination; final phase completion, `done`, a requested exit or cleanup-only reap cannot substitute."
  * 230-236: absent timestamps after clock failure; stored dependent activation; "Reached failed gates withhold activation, collection and release even if cleanup later observes reap."

For each sentence determine:
1. Is the constraint ENFORCED, and where? Distinguish three places: (a) the producer (Swift host / C worker) constructs evidence this way; (b) the controller's semantic admission (`controller/src/porcelain_admission.rs`, `porcelain_actor.rs`, `porcelain_records.rs`) rejects replies violating it; (c) only tests construct it. A constraint stated as "requires" or "admits only" that is enforced only by the producer and not by the reader is a different thing from one a reader rejects — say which.
2. Are the "closed" pairs (application state/basis; preparation_failure stage/code) actually closed in the reader, i.e. is an unlisted pair rejected? Cite the match arms.
3. For the termination gate rules (lines 212-236), map each conjunct of "A satisfied gate additionally requires..." to the code condition that checks it. Report any conjunct with no corresponding check, and any check in code not described in the document.
4. Tests: find unit tests (Rust `#[cfg(test)]`, `runner/Tests/PWRunnerCoreTests/*`) and integrated suites (`tests/suites/*`, `tests/catalog.json`; the manifest `docs/contract_surfaces.json` names `runner_unit` for actors and `runner_byoxpc` for equipment). State what each actually asserts and whether it runs constructed data or the signed product. Does a test exist for each "Example:" sentence (lines 141, 171)?
5. Vocabulary check: for every backticked field or value name in these lines (e.g. `owned_reap`, `capture_ordinal`, `observed_ns`, `activation_observation`, `termination_gate`, `binding_ref`, `entitlements_ref`, `unverified_fixture`, `equipment_inventory`, `preparation_failure`, `resolved_plan/inconsistent_assignment`, `equipment/equipment_binding_refused`, `runner_failed`, `not_requested/unapplied_declaration`, `not_attempted`, `observed`, `unobserved`, `authority_setup.host`, `authority_setup.workers`), confirm it exists in `docs/porcelain.json` and/or the code with that spelling and that it reaches public JSON output. Report any name that does not exist or is spelled differently.
6. Terms a first-time reader cannot resolve from CONTRACT.md alone (e.g. "declaration reply", "singular worker projection", "custody scopes", "cells", "acquired decision", "capture stage", "departure flags", "eligible terminal worker branch", "native apply-failure publication"). For each, say where (if anywhere) it is defined: docs/PolicyWitness.md, docs/WORKER.md, docs/ARCHITECTURE.md, docs/EXTENSIONS.md, docs/LIMITS.md. Give file:line.

Do NOT treat the existence of a type, field, function or test as proof. Check reachability and what a test asserts.

REPORT FORMAT (your final message is consumed by another agent writing the report; be precise, not polished). For each claim group give:
- CONTRACT.md line range and a short quote
- Verdict: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / CONTRADICTED / NOT DETERMINED
- Code evidence with `path:line` citations, stating producer-side vs reader-side
- Test evidence with `path:line` and what the test actually asserts
- Label every statement as OBSERVED, INFERRED, or HYPOTHESIS (would need an experiment; describe it, do not run it)
Then a separate list: discrepancies, places a competent reader could reach a false conclusion, statements stronger than the code, distinctions the document requires but the code does not enforce, and statements that are correct and well supported (say so explicitly). Aim for completeness over brevity, up to about 4000 words. Do not propose fixes or rewrites.
````

### Pass 3: return, verbatim

````text
REPORT: docs/CONTRACT.md actors (138-142) and equipment (168-238) surfaces, commit 298c1805, clean tree. Read-only; nothing built or run. "OBSERVED" means read in source at the cited lines. Statements about tests describe what the test source asserts, not a recorded execution.

## 0. Cross-cutting facts (apply to every "requires / admits only" sentence)

C0.1 OBSERVED. Four enforcement places exist, not three:
- (a) Producer construction (Swift host, C worker).
- (a') Producer self-check: `PWRunnerRunResult.validateForReporting()` -> `actorExtensionEvidenceProblem()` (runner/Sources/PWRunnerCore/PWRunnerReply.swift:241-365, 379-473, 643-650). On failure the host does not drop the evidence: `pwRunnerReportData` (PWRunnerService.swift:124-160) rewrites the reply to `runner_reporting_failed`, `rc 1`, `reporting_failure.evidence_retained: true`, strips comparisons and re-encodes the same actor records.
- (b) Controller semantic reader: `porcelain_admission::admit_reply` (controller/src/porcelain_admission.rs:1416-1486) calls `actor::validate` (porcelain_actor.rs:1655-1699).
- (c) Tests only.

C0.2 OBSERVED. Reader-side "rejection" is not refusal of the reply.
- `run_flow::admit_reply` (controller/src/run_flow.rs:332-359) refuses only on delivery or client failure, a foreign `producer.contract`, or `admission_problem` (table capacities plus compiled_profile context; porcelain_admission.rs:1289-1312, 1675-1795).
- Every check discussed below runs later, inside `execution_diagnostics` (porcelain_admission.rs:1556-1638). A violation sets `runner_sandbox_diagnostics.process_disposition: "withheld"`, `disposition_integrity: "invalid"` and appends `disposition_issues` of kind `actor_evidence` (1631-1636).
- `data.runner_result` is still published unchanged. `result.ok` and the exit code come only from `normalized_outcome == "finished"` (run_flow.rs:748-786).
- So "`preparation_failure` admits only ...", "`observed` requires ...", "a satisfied gate requires ..." mean: a violating reply is still emitted with the violating fields, flagged invalid. CONTRACT.md:352-355 says this ("Conflicting observations remain publishable with dependent claims withheld"), but in the transport_encoding region, not in 168-238.
- INFERRED: the only claims withheld are the controller's disposition projections; the raw `termination_gate.outcome: "satisfied"` or `application` pair stays in the output.

C0.3 OBSERVED. `admit_reply` skips `phase_issues`, `native::validate`, `actor_associations` and `actor::validate` whenever `reporting_failure` is present (porcelain_admission.rs:1426-1449 versus the else-branch 1449-1484). Combined with C0.1, a reply the host itself found inconsistent reaches public JSON with no reader check of any equipment-region constraint. It is marked only by `runner_reporting_failed`.

C0.4 OBSERVED. The main Rust control is `typed_setup_equipment_application_and_gate_corpus` (porcelain_actor.rs:2025-2083) over tests/fixtures/contract/actor_evidence.json (77 cases).
- It asserts only `issues.is_empty() == accepted` and that the input was not mutated. It never asserts which issue fired.
- It calls `account_only` (2007-2024), which runs `setup`, `equipment`, `application`, `gates` but not `identity`, `custody` or `preparation_failure_valid`.
- Fixtures are sparse, hand-authored JSON patched in the test (1963-2006).
- Several rejected cases are over-determined. Example: `runtime_failure_cannot_be_preparation` patches the execution status to `inspection_failed` on a baseline whose `normalized_outcome` is `finished`, whose `schedule` is `{}` and whose phases all arrived (checked in actor_authority_reply.json). It is rejected by 840-861 without the `preparation_failure.is_none()` conjunct.
- The same corpus is replayed through a separately written Python reader (tests/lib/actor_evidence.py; tests/suites/blackbox_e2e/extension_controls.py:184-204).

C0.5 OBSERVED. The manifest check for `equipment` is `runner_byoxpc` (docs/contract_surfaces.json).
- No file under tests/suites/runner_byoxpc references `termination_gate`, `owned_reap`, `activation_observation`, `preparation_failure`, `application`, `actors` or `execution_form`. The only equipment hits are registry-level inventory comparisons (opt_in/entitlement_readback.py:51-54, registry_recovery.py:122, 191-192).
- The generator validates only that the named suite exists (docs/generate_contract_stamps.py:53-56; tests/suites/source_drift/build_contracts.py:394-397).
- Signed-product checks of this surface live in `witness_contract` (extensions, extension_boundaries, extension_redelegation, actor_compositions, opt-in actors_byoxpc), `preflight/byoxpc_verification_controls`, `failure_boundaries` and `runner_unit`.
- The manifest `definitions` for equipment are PolicyWitness.md#equipment and #lifecycle. The `equipment` region there (docs/PolicyWitness.md:1653-1735, "Extension and fresh-read output") defines `extension_events`, `transfers`, `resources`, `fresh_read`, `fresh_write`. `termination_gate`, `preparation_failure`, `unapplied_declaration`, `binding_ref`, `unverified_fixture` do not occur anywhere in PolicyWitness.md (grep count 0).
- The equipment shape golden (tests/fixtures/contract/surfaces/equipment.json) contains no `preparation_failure`, `termination_gate` or `activation_observation`; those appear only in the lifecycle, envelope and transport goldens.

## 1. Lines 138-142 (actors)

1.1 "either the ordinary single-worker form or named actors and phases". SUPPORTED, with a wording hazard.
- OBSERVED: `admitSpecimen` branches on `request.isActorForm` (ProbeRunner.swift:201-219); the reply carries `execution_form` (ActorOrchestration.swift:512). The reader forbids actor tables in an ordinary reply (porcelain_actor.rs:1656-1672) and singular projections in an actor reply (1155-1162).
- Hazard: the single-worker form also has `phases` (PolicyWitness.md:207-254), so "named actors and phases" is not what distinguishes the forms.
- Tests: Rust `typed_ordinary_reply_cannot_hide_actor_evidence_behind_its_form` (porcelain_admission.rs:2496-2528, constructed); check_extensions.py:185-188 (signed CLI: an ordinary run has no actors, events or authority_setup).

1.2 "Every sandboxed process is fresh". SUPPORTED by the producer; NOT reader-enforced.
- OBSERVED: one `ActorSession` spawn per actor (ActorScheduler.swift:221-253), no reuse path.
- OBSERVED: no reader requires distinct launch PIDs across actors. Rust `identity()` (porcelain_actor.rs:2257-2368), the Swift self-check and tests/lib have no such check.
- Tests: check_extensions.py:56 (`len({pid}) == len(actors)`, signed CLI); ActorSchedulerTests.swift:475 (real worker processes, no XPC). INFERRED for the single-worker form (CWorker.swift:1119 onward not traced in full).

1.3 "an actor applies its policy once". SUPPORTED.
- Producer: a single `sandbox_apply` call site (controller/tools/pw_probe_runner/pw_probe_runner.c:1641); `applicationCount` is 0 or 1 (ActorScheduler.swift:260, 574).
- Reader: `application_count` in {0,1} and equal to `applied` (porcelain_actor.rs:461-466, 1174-1182).
- Tests: check_actor_equipment.py:149-152 and check_extensions.py:89 (signed CLI); the cross-reader mutation `late-setup:/actors/1/application_count` = 0 is rejected (run_flow.rs:1289).

1.4 "Phases name the active actor and preserve action order". SUPPORTED.
- Reader: phase actor exists and `actor_visit` order (porcelain_actor.rs:2342-2355); steps belong to their phase's actor (2356-2367); step and event array order equals the phase plan (porcelain_admission.rs:1083-1109).
- Producer self-check: PWRunnerReply.swift:296-302.
- Tests: Rust custody mutation "order" (porcelain_actor.rs:2500, asserts only that issues are non-empty); ActorPlanTests.swift:233.

1.5 "Extension transfer and consumption use explicit owned records". SUPPORTED. "Owned records" is undefined in CONTRACT.md.
- OBSERVED: `transfers[]`, `resources.{tokens,deliveries,handles}` with owner actor IDs (PWRunnerActors.swift:147-190, 221-240); reader `custody()` (porcelain_actor.rs:1142-1654).
- Tests: `typed_custody_host_delivery_survives_missing_source_publication` (2462-2514, constructed, includes "token_owner"); `actor_driver_replies_cross_readers` (run_flow.rs:1250-1345). The latter decodes six binary replies written by the Swift driver with real worker processes, asserts the full reader accepts them and rejects about 25 mutations. It is `#[ignore]`d by default and invoked by tests/suites/runner_unit/run.sh:62,77.

1.6 Example "a phase naming a nonexistent actor is refused before children". SUPPORTED; a test exists; "before children" is shown indirectly.
- Code: `normalizeActorPlan` returns `unknown_actor` at path `phases/<i>/actor_id` (ActorPlan.swift:364-365). It runs inside `admitSpecimen` before `runActors` (CWorkerOrchestrator.swift:67-76).
- Tests: corpus example `phase_unknown_actor` (tests/fixtures/request_contract/examples.json:5725, expected code at 5939-5953). Constructed: ActorPlanTests.swift:93-107 (normalizer only). Signed CLI and direct XPC: tests/suites/runner_outcome_bad_request/contract.py:86-93 with the assertions at 73-84 and 109-112 (`bad_request`, exact code and path, `steps == []`, `runner_subprocess is None`, effect file absent).
- Limits: `runner_subprocess` is always null in the actor form, so that assertion cannot show that no actor process was launched. No process-table observation is made. The independent witness is only that the file effect did not occur.
- Cross-surface: the code `unknown_actor` is not in the code table at CONTRACT.md:273-284.

## 2. Line 171

2.1 "Actor evidence binds observations to the named process and service-sealed equipment". SUPPORTED for a `matched` execution.
- Reader (porcelain_actor.rs:788-833): the binding is `bound`; path, cdhash, identifier and team equal the binding's; `execution.pid` equals the actor's launch PID; the live read-back row names this actor and binding; four native observations have OSStatus 0.
- Producer: `inspect` (ActorEquipment.swift:429-468); seal and inventory in `prepare` (323-358).
- The reader cannot verify the seal. For `verified` it requires `seal_osstatus == 0`, three digests of the right length and `schema_version 1` (609-619). It does not compare `worker_identity` to any expected value.

2.2 "The worker ABI identity remains independent of the public build identity". PARTIALLY SUPPORTED; "independent" is undefined.
- OBSERVED: the two are separate values, separately compared (`value.contract == expectedContract, value.worker_identity == expectedIdentity`, ActorEquipment.swift:129-130). The reply inventory carries `worker_identity` and no contract.
- INFERRED: the worker identity inputs (CONTRACT.md:392-395) are a subset of shipped source, so a worker-source edit changes both; a controller-only edit changes only the contract. Independence holds in one direction.
- Tests: ActorEquipmentTests.swift:330-362 (mutations "build_identity" and "protocol" both refuse as `worker_identity_mismatch`; constructed fixture bundle with injected signature inspection); preflight/check_byoxpc_verification.py:296-309 (signed bundle, `wrong_identity`).

2.3 "Worker entitlements are read from the selected binary". SUPPORTED; ambiguous term.
- Static read: `SecStaticCodeCreateWithPath` plus `SecCodeCopySigningInformation` on the bound path (ActorEquipment.swift:217-259). Live read: on the process's static code (263-284).
- "selected" is also a role value (`selected` / `unentitled`). The code reads entitlements for whichever role is bound, including `unentitled`.

2.4 Example "an equipment hash mismatch prevents use of the claimed equipment". SUPPORTED; a constructed test exists; the integrated test covers install, not `run`.
- Producer: `row.sha256 == expected.sha256` else `worker_identity_mismatch` (ActorEquipment.swift:417-422); `executablePaths` stays nil; preparation refusal (ActorOrchestration.swift:42-46).
- OBSERVED: any refused row, including a role no actor requested, refuses the whole run (the `defer` at 385). Asserted by ActorEquipmentTests.swift:83-98.
- Reader: a `bound` packaged row needs `sha256 == expected_sha256` (porcelain_actor.rs:702).
- Tests: ActorEquipmentTests.swift:364-374 (file bytes changed under an unchanged manifest; asserts reason, `binding_ref 0`, statuses `["refused","bound"]`, no executable paths; constructed bundle, injected inspection). preflight/check_byoxpc_verification.py:229 (`wrong_hash`) and 248-282 (`resigned_stale_hash`): the signed controller's `runner install` refuses.
- Not found: a signed-product `run` against a hash-mismatched worker. The nearest is opt_in/check_missing_equipment.py:43-50 (worker file moved away, BYOXPC, default false).
- No public reason code says "hash"; the reason is `worker_identity_mismatch`.

## 3. Lines 176-181

3.1 "no declaration reply or singular worker projection". SUPPORTED; both terms undefined.
- No `extensions` field exists in docs/porcelain.json (grep 0). Corpus case `removed_declarations_null` is rejected because decoding fails.
- Singular projection: reader porcelain_actor.rs:1155-1162; producer PWRunnerReply.swift:381-382.

3.2 "`actors[]` owns each launch, subprocess, application assessment and equipment association". SUPPORTED. Fields `launch`, `subprocess`, `application`, `equipment`, `owned_reap` (PWRunnerActors.swift:123-143); in the shape golden.

3.3 "`authority_setup.host` run/region/custody scopes and `authority_setup.workers` cells retain primary setup, independent cleanup and native-capability observations". SUPPORTED, with loose naming.
- Fields are `host.run`, `host.regions[]`, `host.custody[]` (the plural `regions` differs from the prose). `workers[]` are scopes; the cells are `workers[].operations[]`.
- Reader `scope()` and `setup()` (porcelain_actor.rs:164-451): slot and name tables, role, native-kind and state matrices, primary operation needs a failed or rejected setup cell.
- Tests: Rust 2114-2204; corpus; ActorAccountTests.swift:6-23; ActorAuthorityTests.swift:155-178 (constructed memory); check_extension_boundaries.py:47-58 (signed CLI with fault-mode workers: exact primary and cleanup cells).

3.4 "An acquired decision does not publish another cell". NOT DETERMINED; one natural reading is CONTRADICTED.
- OBSERVED: the C worker publishes the decision (`atomic_store ... published`), then publishes cleanup cells 9 and 12, and cell 11 at exit (pw_probe_runner.c, the `decision:` block of `prepare_authority`, about 755-766; `erase_authority` about 579-590; comment "Publish refusal before cleanup").
- A reading "the decision is not itself an `operations[]` row" is consistent with `decodeAuthoritySetup` (AuthoritySetupRuntime.swift:95-103).
- "Acquired decision" is defined in none of the five named documents. No test names this property.

3.5 "a scheduling summary does not replace any actor's facts". PARTIALLY SUPPORTED. Application precedence ignores `schedule` (porcelain_actor.rs:544-577). Tests: corpus `late_application_does_not_rewrite_setup_timeout`; ActorSchedulerTests.swift:315; ActorReplyTests.swift:157. No check states the sentence as written.

## 4. Lines 183-196

4.1 Inventory, positional naming, `role`+`source` identity, zero-based refs. SUPPORTED in producer and reader.
- Producer: `UInt32(bindings.count)` before append (ActorEquipment.swift:381, 404, 411, 444, 453).
- Reader: duplicate (role, source) rejected (porcelain_actor.rs:623-630); refs resolved with `.get(n)` (634, 736, 790).
- Not checked by the reader: `preparation_failure.binding_ref`, `.actor_id`, `.reason` (absent from `preparation_failure_valid`, 1066-1116).

4.2 "`binding_ref` is null when no binding row was produced for its role". SUPPORTED. Producer 369-370. Reader 740-741 requires that null coincide with no row of that role. The Swift self-check is weaker (PWRunnerEquipment.swift:250). Schema `json_null: true` for this field only, so it appears as JSON null. `termination_gate.observation`, gate `capture_ordinal`, `observed_ns` and `entitlements_ref` are omitted keys when absent.

4.3 Overrides carry `unverified_fixture` "and cannot establish packaged selection". PARTIALLY SUPPORTED.
- Row shape is enforced: `test_override` rows need `unverified_fixture`, no `relative_path` and no expected hashes (reader 669-695; producer 382-384).
- "cannot establish packaged selection" has no corresponding check. An actor bound to an override row can be `matched` and `eligible` and run. The reader does not require the actor to choose the override over the packaged row of the same role.
- Tests: corpus `override_cannot_claim_packaged`, `override_cannot_claim_generated_implementation`, `explicit_override_is_instrumented_not_packaged`; ActorEquipmentTests.swift:143.

4.4 "independently associated static and live XML read-backs". SUPPORTED. Values are `source: "binding"` / `"execution"` and `raw_plist`; the words "static" and "live" are not field values. Reader 633-667, 1759-1777.

4.5 "requirements are evaluated separately using boolean true keys, including in the live read-back". SUPPORTED.
- Producer: `granted` (ActorEquipment.swift:201-204), static 372, live 462.
- Reader: CoreFoundation boolean filter (porcelain_actor.rs:99-128), static 754-773, live 815-817 (only when `matched`).
- Tests: Rust 2245-2254; corpus `live_integer_one_cannot_satisfy_boolean_requirement`; ActorEquipmentTests.swift:99, 467; check_actor_equipment.py:160-173 (signed BYOXPC, opt-in).

4.6 Runtime inspection failure. SUPPORTED, constructed and unit level only.
- Producer: ActorScheduler.swift:163-182; `cancelled` is set only if nil (177), so an earlier cancellation survives; every visit is then skipped (316-319).
- Reader: 840-861 and 1930-1950 (not `finished`, no `preparation_failure`, non-empty `schedule.cancelled`, no activation, arrival, collection or proceed).
- "retains any already published setup/application facts" is producer behaviour; a reader cannot check retention.
- Tests: ActorSchedulerTests.swift:116-166 (real processes); ActorAccountTests.swift:93-105; corpus compound cases.
- No file under tests/suites asserts `inspection_failed`, `executable_mismatch` or `equipment_execution_*` against the signed product.

## 5. Lines 198-202 (`preparation_failure`)

5.1 Closed pairs. SUPPORTED in three readers; the Rust arm is not unit-tested.
- Rust: `matches!((stage, code), ("resolved_plan","inconsistent_assignment") | ("equipment","equipment_binding_refused"))` (porcelain_actor.rs:1076-1079). An unlisted pair gives "invalid before-launch preparation failure" (1677-1683).
- Swift: PWRunnerReply.swift:410-421. Python: tests/lib/actor_evidence.py:423-437.
- OBSERVED: no Rust test reaches `preparation_failure_valid`. The only Rust-visible fixture with the field is the corpus case in C0.4, run through `account_only`.
- `resolved_plan/inconsistent_assignment` is produced only when `actorPlanAssignmentsConsistent` fails or translation throws (ActorOrchestration.swift:27-52). Its only test hand-corrupts an in-memory plan (ActorPlanTests.swift:195-231). INFERRED: not reachable from a public request.
- Signed-product tests of the equipment pair: check_actor_equipment.py:160-173, check_missing_equipment.py:43-50, failure_boundaries/check.py:170-172.

5.2 "with `runner_failed`, `rc: 1` and no launched actors". SUPPORTED (reader 1080-1085; producer 532-551).

5.3 "Observation arrays are empty". PARTIALLY SUPPORTED; imprecise.
- Empty per the reader: `steps`, `extension_events`, `transfers`, `resources.{tokens,deliveries,handles}`, `authority_setup.host.regions` and `custody` (1086-1108).
- Not empty: `actors`, `phases`, `authority_setup.workers` (one `not_observed` scope per actor, 569-571), and normally `equipment_bindings` and `equipment_entitlements`. The refused binding row is the evidence; check_actor_equipment.py:171 asserts the bindings are present.

5.4 "sole exception to their normal complete observation partition". SUPPORTED as written. The partition check is skipped only when `preparation_failure` is present (porcelain_admission.rs:1076-1082; PWRunnerReply.swift:298). Under `reporting_failure` it is not evaluated at all (C0.3). Action identities are checked for count 256 or fewer, 63 bytes, unique (1113-1115); phase-ID length is not checked there.

## 6. Lines 204-210 (`application`)

6.1 Closed state/basis pairs. SUPPORTED; the document names four states and one basis.
- Reader arms (porcelain_actor.rs:493-538), eleven pairs then `_ => false`:
  - `not_requested/unapplied_declaration`
  - `not_attempted/worker_not_launched`
  - `not_attempted/terminal_authority_setup_refusal`
  - `not_attempted/terminal_input_refusal`
  - `not_attempted/terminal_parameter_refusal`
  - `not_attempted/terminal_compile_refusal`
  - `not_attempted/terminal_timing_refusal`
  - `observed/applied_publication`
  - `observed/apply_failure_publication`
  - `unobserved/apply_call_boundary_without_result`
  - `unobserved/no_eligible_apply_publication`
- A second check recomputes the single expected pair by precedence and requires equality (544-577). The producer uses the same function (PWRunnerAuthoritySetup.swift:109-140, 215-223).
- Ten of the eleven basis strings appear in none of the five named documents.

6.2 `not_attempted`, `observed`, `unobserved` sources. SUPPORTED.
- No launch: 495-504.
- "Eligible terminal worker branch": a published failure with operation in {1 header, 2 policy_read, 3 params_create, 4 param_set, 5 compile, 12 clock_setup} and specific codes (477-488; enum at pw_probe_runner_abi.h:312-349), or an observed `terminal_required_failure` without integrity errors.
- "Native apply-failure publication": operation 8, code 1, kind 1, `native_result != 0` (521-526; C at pw_probe_runner.c:1646).

6.3 "setup timeout, `done`, process death or an auxiliary reporting failure alone cannot establish application nonattempt". SUPPORTED by the precedence check. None of those appear among the sources; operations 6 (capture) and 7 (ready) are outside the whitelist.
- Tests: corpus `invented_application_nonattempt`, `terminal_refusal_cannot_claim_apply`, the six `*_with(out)_launch_*` cases, `empty_subprocess_is_not_absence_for_worker_not_launched`; ActorAccountTests.swift:6-23, 33-40.
- Signed-product assertions exist for three pairs only: `observed/applied_publication` and `not_requested/unapplied_declaration` (check_extension_redelegation.py:99, 104; check_actor_compositions.py:112, 115) and `not_attempted/terminal_authority_setup_refusal` (check_extension_boundaries.py:55).
- No integrated assertion was found for `apply_failure_publication`, either `unobserved` basis, the four other terminal bases or `worker_not_launched`.

## 7. Lines 212-236 (termination)

7.1 `owned_reap` contents. SUPPORTED. Fields `pid`, `native_rc`, `raw_status`, `stage`, `ownership_unbroken`, `departure_requested`, `capture_ordinal`, optional `observed_ns` (porcelain.json record PWOwnedReapObservation). Created only on `waitpid == pid` (CWorker.swift:1090-1093). The prose words "capture stage" and "ownership/departure flags" are not field names.

7.2 "These ordinals are local to the source actor process". SUPPORTED for the three values compared; ambiguous as written.
- OBSERVED: one counter per child process (CWorker.swift:1070-1076). `activate` uses the activated actor's own counter (ActorSession.swift:543-547). The gate close uses the source's counter (ActorScheduler.swift:500).
- A dependent phase's `activation_observation.capture_ordinal` therefore lives in the dependent's sequence. Fixture example: dependent ordinal 1, gate ordinal 3.

7.3 "Every nonnull observation, including a failed gate's, requires a positive matching source reap ordinal and a present later gate `capture_ordinal`". SUPPORTED. Reader 979-990, which additionally requires `owned_reap_valid(source)`. Producer self-check PWRunnerReply.swift:442-446. Corpus: `timed_out_gate_retains_associated_late_owned_reap` (accepted) and four `failed_gate_*` cases (rejected).

7.4 Conjunct map for "A satisfied gate additionally requires ..." (Rust reader; the Swift self-check at PWRunnerReply.swift:451-461 and PWRunnerAuthoritySetup.swift:234-242 mirrors it):

| Conjunct | Reader condition |
| --- | --- |
| source's final activation before its owned reap | `a.capture_ordinal < r.capture_ordinal`, `a` from the phase named by `source_final_phase_id` (992-995); that phase must be the source's last and earlier than the gated phase (934-951) |
| before gate closure | `r.capture_ordinal < g.capture_ordinal` (996) |
| consistent child PID | `owned_reap_valid`: `native_rc == pid == launch.pid == subprocess.pid`, `reaped == true` (875-880) |
| decoded wait status | WIFEXITED/WIFSIGNALED decode equals subprocess `exit_code` / `term_signal` (868-874) |
| unbroken ownership | `r.ownership_unbroken` (1006) |
| no prior host departure request | `!r.departure_requested` (1007) |
| both timestamps present and ordered | both `observed_ns` present and `a <= r`, non-strict (998-1001) |
| usable clock | `!w.clock_fault` and `elapsed_ms` present (1022, 1024) |
| no native wait error | `w.native_errno.is_none()` (1023) |
| elapsed within positive allowance | `budget_ms` in 1..=5000 and `elapsed_ms <= budget_ms` (1021, 1024) |

- No conjunct lacks a check.
- OBSERVED on "no native wait error": the producer never passes an errno into a gate wait record (`wait.record(stop:)`, ActorScheduler.swift:499). A failed `waitpid` produces outcome `ownership_lost` (528) instead. The reader's condition guards a state the producer does not construct.
- The reader compares elapsed time with the reply's own `budget_ms`, which the producer caps by remaining execution time (488). LIMITS.md:153 calls this "Actor termination dependency wait (`actor_termination_wait`)"; CONTRACT says "termination-gate allowance".

Checks in code not described in lines 212-236:
- reap `stage` must be `schedule` or `termination_gate` (1008); the stage vocabulary is not in the document;
- `observation.capture_ordinal == reap.capture_ordinal` restated for satisfied (1010-1013);
- `condition == "terminated"`; source is not the gated actor (940-942);
- a closed outcome set of eight values (952-966): `not_reached`, `satisfied`, `timed_out`, `ownership_lost`, `clock_unavailable`, `source_unavailable`, `source_departure_requested`, `execution_allowance_exhausted`; only `satisfied` is named in the document;
- `wait.stop == outcome`, `budget_ms` in 0..=5000, `excluded_ms` absent (913-919, 967-977);
- a `not_reached` gate carries no observation, capture or wait (906-912);
- `activation_eligible` implies `satisfied` and a dependent actor with usable setup and `equipment.execution.eligible` (1052-1063);
- `activation_observation.capture_ordinal > 0` for every phase (896-902);
- `owned_reap_valid` for every actor that carries `owned_reap`, gate source or not (886-894).

7.5 "An abnormal natural reap can satisfy termination; final phase completion, `done`, a requested exit or cleanup-only reap cannot substitute". SUPPORTED.
- Producer: `observeTermination` (ActorScheduler.swift:486-539) never requests departure. `requestExit` and `terminate` set `departureRequested` before any later reap (ActorSession.swift:558-562; CWorker.swift:1110-1117).
- Tests: ActorSchedulerTests.swift:173-203 (real processes, exit 0 and SIGKILL, with an independent `waitpid` witness), 204-260, 261-277. Corpus: `abnormal_natural_reap_satisfies_termination`, `final_activation_without_completion_can_precede_natural_reap`, `gate_cleanup_reap`, `gate_cleanup_grace_reap`, `gate_requested_departure`. Signed CLI: check_extensions.py:90-98; check_extension_boundaries.py:300-314 (timed out with a later cleanup reap whose ordinal exceeds the gate's; satisfied with exit code 87). Mutation control `runner_unit/actor_handoff_mutations` (default false) removes the gate.

7.6 Lines 230-236. SUPPORTED.
- Absent source timestamps cannot satisfy: reader `time` (998-1001); producer returns `clock_unavailable` (532). Corpus: `unclocked_native_facts_retained_without_gate_credit`, `gate_unclocked_reap`, `gate_unclocked_activation`.
- A missing dependent timestamp retains activation and gate: reader 1028-1037; producer `activate` (ActorSession.swift:543-547). Corpus `gate_dependent_activation_time_{null,missing}_retains_store`; ActorAccountTests.swift:66-73.
- A present dependent timestamp must not precede the source reap: reader 1031-1035. Corpus `gate_dependent_activation_time_precedes_reap`.
- Failed gates withhold activation, collection and release: reader 1039-1051 and 920-932; producer ActorScheduler.swift:340-345. Tests: ActorSchedulerTests.swift:261-277; check_extension_boundaries.py:303-306.

## 8. Vocabulary

Every backticked field name exists in docs/porcelain.json with the documented spelling and appears in a shape golden: `actors`, `authority_setup` (`host`, `workers`), `equipment_inventory`, `equipment_bindings`, `equipment_entitlements`, `role`, `source`, `binding_ref` (three records), `entitlements_ref` (two records), `preparation_failure`, `application`, `owned_reap`, `capture_ordinal` (four records), `observed_ns`, `activation_observation`, `termination_gate`, `observation`.

Enumerated values are absent from porcelain.json by design (CONTRACT.md:319-322) and exist only as code strings, spelled as documented: `unverified_fixture` (ActorEquipment.swift:383; porcelain_actor.rs:685), `resolved_plan/inconsistent_assignment`, `equipment/equipment_binding_refused`, `runner_failed`, `not_requested/unapplied_declaration`, `not_attempted`, `observed`, `unobserved`.

No documented name is missing or misspelled.

`done` and `rc: 1` are prose references, not reply fields under those names in this region.

## 9. Terms not resolvable from CONTRACT.md

- "declaration reply": not defined in the five named documents. Nearest: tests/FAILURE-PROPAGATION-CONTRACT.md:242 ("no `extensions[]`"); the tests/lib/actor_evidence.py message "removed declaration reply field". PolicyWitness.md:240 uses "declaration order" in another sense.
- "singular worker projection": not defined. runner/README.md:136; FAILURE-PROPAGATION-CONTRACT.md:243; field list at PolicyWitness.md:1316-1318.
- "service-sealed": phrase only in CONTRACT. Explained at PolicyWitness.md:374 and EXTENSIONS.md:13.
- "custody scopes": phrase only in CONTRACT. FAILURE-PROPAGATION-CONTRACT.md:196-203 ("private-custody"); ARCHITECTURE.md:77.
- "cells": LIMITS.md (authority setup rows; PolicyWitness.md:1107-1108); FAILURE-PROPAGATION-CONTRACT.md:197.
- "acquired decision": nowhere.
- "native-capability observations": nowhere. INFERRED to be the `*_symbol` cells (PolicyWitness.md:376 "each extension-symbol lookup").
- "scheduling summary": nowhere.
- "capture stage": for `owned_reap`, nowhere (FAILURE-PROPAGATION-CONTRACT.md:224 says "observer stage"). runner/README.md:200 uses "capture stage" for the compiled-profile field `capture_stage`, a different record.
- "departure flags": FAILURE-PROPAGATION-CONTRACT.md:224 ("prior departure-request flag").
- "eligible terminal worker branch": nowhere. PolicyWitness.md:988 and LIMITS.md:78 use "eligible terminal" for XPC errors. FAILURE-PROPAGATION-CONTRACT.md:207 has "terminal pre-apply branch".
- "native apply-failure publication": FAILURE-PROPAGATION-CONTRACT.md:208 only.
- "owned records", "reserve geometry": not defined; LIMITS.md has no "reserve geometry" phrase (closest is "Authority-region geometry", LIMITS.md:526).
- "termination-gate allowance": LIMITS.md:153 and 228 under another name.

## 10. Summary lists

Discrepancies:
1. Manifest check `runner_byoxpc` asserts none of the equipment-region relationships (C0.5).
2. Manifest definitions for equipment point at a user-guide region that does not define most of the region's fields (C0.5).
3. "An acquired decision does not publish another cell" is contradicted under the literal temporal reading (3.4).
4. "Observation arrays are empty" while `equipment_bindings`, `equipment_entitlements`, `authority_setup.workers`, `actors` and `phases` are populated (5.3).
5. PolicyWitness.md:1320-1322 lists `setup_status` values without `authority_setup_failed`, which producer and reader both use (ActorScheduler.swift:52; porcelain_actor.rs:2282). Outside the assigned lines, inside the manifest's definition target.
6. The line 141 example produces `unknown_actor`, which the refusal code table does not list.

Places a competent reader could reach a false conclusion:
- That "admits only" and "requires" mean a violating reply is refused or unpublished (C0.2).
- That a `runner_reporting_failed` reply has passed these checks (C0.3).
- That all phases' `capture_ordinal` values share the source's sequence (7.2).
- That `owned_reap` has a field named `capture_stage` (7.1, section 9).
- That "final activation before owned reap" shows the process died after activation. HYPOTHESIS: a source that exits while parked between visits is reaped only at the first `waitpid` after its next `activate` (ActorScheduler.swift:347, 371), giving activation ordinal below reap ordinal and a `satisfied` gate. Experiment, not run: a two-visit source that exits right after completing visit 1 while another actor's phase is active, with a dependent gated on it; record the kernel exit time independently and compare.
- That "selected binary" means the `selected` role (2.3).
- That only the claimed role's hash matters (2.4).
- That the application vocabulary is four states and one basis (6.1).

Statements stronger than the code:
- "cannot establish packaged selection" (4.3).
- "Every sandboxed process is fresh" as a property of reply evidence (1.2).
- "remains independent" (2.2).

Distinctions the document requires but no reader enforces:
- distinct actor processes;
- override versus packaged choice per actor;
- resolution of `preparation_failure.binding_ref`, `actor_id`, `reason`;
- retention of setup/application facts after inspection failure;
- any of these constraints under `reporting_failure`.

Correct and well supported:
- The closed `preparation_failure` pair set with its side conditions (three readers agree; signed-product tests for the equipment pair).
- The closed application pairs and their source precedence (reader and producer share the rule; constructed negatives; three pairs asserted on the signed product).
- Positional binding and entitlement references and the null `binding_ref` rule.
- Boolean-true requirement evaluation, static and live.
- The whole termination-gate group, lines 212-236: every conjunct has a reader check and a producer condition, with constructed negatives, real-process scheduler tests with an independent `waitpid` witness, and signed-CLI assertions for the satisfied, abnormal-exit and timed-out cases.
- The line 141 example (signed CLI and direct XPC).
- The line 171 example at the binder (constructed) and at install (signed).

Not determined: the intended meaning of 3.4 and 3.5; whether any default-battery case exercises runtime inspection failure or the non-asserted application bases on the signed product (none found by search under tests/suites); single-worker freshness (not traced).
````

### Pass 3: read first-hand by the report writer at the time

These readings were made to check the return before the report was written. They are the report writer's own and are not part of the return.

- The closed pairs and the emptiness conditions: `controller/src/porcelain_actor.rs:1066-1116`.
- That violations flag and do not refuse, and that the validators are skipped under `reporting_failure`: `porcelain_admission.rs:1416-1452`, `:1622-1638`.
- Occurrence counts of eight equipment-region terms in the guide and the contract, and the absence of "acquired decision", "scheduling summary", "declaration reply" and "singular worker projection" from the documents searched.

### Pass 3: now known to be wrong, and other notes

- Nothing in this return is known to be wrong.
- The gate conjunct table (7.4), the eleven application pairs (6.1) and the list of undefined terms (9) were used in the report as returned and were not re-read.

## Pass 4: Transport, typed response encoding, installation and reservation

Launched 2026-11-10T01:57:42.931Z; last transcript record 2026-11-10T02:08:03.719Z. Brief: 8,601 characters. Return: 32,711 characters.

**Used in the report for:** `L-31`, `L-37` to `L-42`; section 5 rows `transport`, `installation`; findings `F-04`, `F-05`, `F-14`, `F-16`, `F-18`; section 9. The report's phrase "three-column table in the delegated trace" at `L-39` refers to the table in this return's group 12.

### Pass 4: brief, verbatim

````text
You are helping with a READ-ONLY examination of `docs/CONTRACT.md` in the repository at /Users/raccoon/Desktop/Security/PolicyWitness (commit 298c1805, clean tree). PolicyWitness is a macOS tool: a Rust controller CLI (`controller/src`), a Swift XPC runner host (`runner/Sources`, `runner/Clients`, `runner/Services`) and a C worker (`controller/tools/pw_probe_runner`). The examination prepares the public contract for external review. The goal is to establish, per claim, whether the document's statement is traceable to reachable implementation and to tests that exercise the stated relationship. It is not to defend the document and not to manufacture findings.

HARD RULES: Do not edit, create or delete any file in the checkout. Do not build, run tests, run generators, or run any command that writes into the checkout (no `make`, `cargo`, `swift build`, `tests/run.sh`, no generator scripts — not even with --check). Use only Read, Grep/Glob-style searching, and read-only git commands. The shell is zsh: quote globs; an unmatched glob aborts the command.

YOUR SCOPE: the transport, typed-response encoding, and installation/reservation surfaces. Read all of docs/CONTRACT.md once for context, then examine these line ranges sentence by sentence:
- lines 246-250 (`transport` region): "Client capture and reservation messages carry a string `contract`. The capture and embedded host frame are independently admitted. The binary shape fingerprint guards decoding and is not a public compatibility identity. Reservation and submission failures never authorize replay after an uncertain invocation. Example: a foreign live peer behind a matching registry entry receives no specimen submission."
- lines 293-298 (`installation` region): "Install admits service `PWContract` before signing or launchd mutation and rechecks after signing. Registry and live-peer identities must both match for execution. Records without a contract remain listable, reconcilable and removable under the existing ownership rules. Example: an owned legacy record cannot execute but can be removed after observed absence." plus line 297: opaque survival of unknown metadata; pending cleanup entry shape (`runner` record, `cleanup_started_at_unix_ms`, `observations`); "the reader also accepts historical flattened entries"; "Publication requires a lossless read-back before atomic replacement. It never establishes execution compatibility or ownership. Known retired kind aliases project as their current kind."
- lines 300-358 (`transport_encoding` region, "Typed response transport"): schema ownership (`docs/porcelain.json`, `docs/generate_porcelain.py`), the claim that Swift writers, Rust readers and a "separately written Python reader" all derive from one schema "so they cannot disagree with each other about structure; none of them checks the schema itself"; frame format (`PWP1`, SHA-256 of the schema's wire identity, value kinds, one-byte kind, four-byte LE length, eight-byte integers, two-byte record identity, strictly increasing nonzero two-byte field tags, list/map four-byte count, sorted unique map keys, two-byte variant case tag, optional fields absent); reader rejections (line 328-330); budgets (byte, nesting, logical-storage per frame; "not physical peak-memory bounds"); capture and host reply separate frames each under own budget; host writer bounds reply by frame limit; client retains at most its smaller reply allowance; `runner_reply_truncated`; "The controller collects the client's complete output before applying its retention cap; reading is not streamed and has no receiver deadline of its own"; fingerprint coverage (lines 341-345: "every record identity, field tag, field name, kind and public presentation rule ... Source locations, defaults and comments are outside it"); "The public build contract is checked during reservation before execution"; presentation rules (lines 347-355: which byte fields become base64 vs lowercase hex); "named validators separately check native operations, lifecycle, phase order, actor setup/equipment, owned endings and extension custody before projecting claims. Conflicting observations remain publishable with dependent claims withheld."
- line 19-20: "Reinstall external runners from the current app when its contract changes."

Key questions:
1. Reservation: read `runner/Clients/PWRunnerClient/*`, `runner/Sources/PWRunnerCore/PWRunnerService.swift`, the reservation request/control reply types, `controller/src/runner_client.rs`, `runner_manager.rs`, `runner_commands.rs`, `runner_select.rs`. Where does each side compare `contract`? What exactly is compared at (a) registry lookup, (b) live peer reservation, (c) client capture admission, (d) embedded host frame admission? Establish the ORDER: can a specimen reach a foreign live peer before the peer's contract is known? Who refuses: client or host or both? What does "never authorize replay after an uncertain invocation" correspond to in code (retry logic for reservation vs submission)? Look for any retry that could resubmit a specimen.
2. Install: where is the service bundle's `PWContract` Info.plist key read and compared, relative to codesign and launchctl calls; is there a recheck after signing? What do `runner list`, `runner reconcile`, removal do with a record lacking `contract`? Can such a record be selected for execution? Is the legacy/flattened pending-cleanup form actually parsed? What is "lossless read-back before atomic replacement" in code? What are the "retired kind aliases"?
3. Encoding: compare the prose frame description against `controller/src/porcelain.rs` (primitive reader), the generated Swift writer (`runner/Sources/PWRunnerCore/PWPorcelainRecords.swift` and any writer primitives), and the Python reader (find it under `tests/lib/`). Check each stated width, ordering rule and rejection. Is the Python reader "separately written" (hand-written primitives) with only tables generated? Is each stated reader rejection (unsupported fingerprint, unknown tag/record/case, missing required, incorrect kind, invalid text, impossible length/count, duplicates, trailing data) implemented in the Rust reader, and is each covered by a test? Does the Swift writer enforce "strictly increasing" tags and sorted map keys by construction?
4. Fingerprint: read `wire_identity` in `docs/generate_porcelain.py`. Exactly which schema attributes enter it? Is the prose list (record identity, field tag, field name, kind, public presentation rule) accurate and complete — e.g. are optionality/requiredness, integer width/signedness, variant cases, record names, list element types included? Would toggling a field between required and optional change the fingerprint? The doc says "an added optional field ... produces a different fingerprint" and "defaults ... are outside it" — check both.
5. Budgets/limits: find the constants (frame limit, reply allowance, nesting, logical storage) in code and `docs/limits.json`; confirm `runner_reply_truncated` exists and when emitted; confirm the "collects complete output before applying retention cap ... no receiver deadline" statement against `runner_client.rs`.
6. Presentation: which fields are base64 vs hex in the Rust projection; does it match lines 347-351 exactly?
7. Tests: unit tests in Rust for the reader, Swift tests for writer, Python reader tests, and integrated suites (`runner_byoxpc` is the manifest's named check for transport and installation; see `tests/catalog.json`, `tests/suites/`). For each "Example:" (lines 249, 296) find the verifying test and say what it asserts and whether it runs the signed product. If none, say so.

Do NOT treat the existence of a type, field, function or test as proof. Check reachability and what a test asserts.

REPORT FORMAT (your final message is consumed by another agent writing the report; be precise, not polished). For each claim group give:
- CONTRACT.md line range and a short quote
- Verdict: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / CONTRADICTED / NOT DETERMINED
- Code evidence with `path:line` citations
- Test evidence with `path:line` and what the test actually asserts
- Label every statement as OBSERVED, INFERRED, or HYPOTHESIS (would need an experiment; describe it, do not run it)
Then a separate list: discrepancies, places a competent reader could reach a false conclusion, statements stronger than the code, distinctions the document requires but the code does not enforce, and statements that are correct and well supported (say so explicitly). Aim for completeness over brevity, up to about 4000 words. Do not propose fixes or rewrites.
````

### Pass 4: return, verbatim

````text
REPORT: docs/CONTRACT.md transport / installation / transport_encoding surfaces (commit 298c1805, read-only)

Root for every path below: /Users/raccoon/Desktop/Security/PolicyWitness/ (paths are written relative to it; absolute index at the end). Nothing in the checkout was written, built or run. One in-memory experiment was run from /private/tmp with `python3 -I -B -` reading only docs/porcelain.json (described under group 9). `git diff --stat v0.3.6 HEAD` is empty for CONTRACT.md, porcelain.json, porcelain.rs, runner_client.rs, runner_manager.rs, PWPorcelain.swift and runner/Clients.

Labels: OBSERVED = read in source/test text; INFERRED = reasoning from that text, not executed; HYPOTHESIS = needs an experiment.

---

## A. Claim groups

### 1. L249 "Client capture and reservation messages carry a string `contract`."
Verdict: SUPPORTED
- OBSERVED: `PWRunnerReservationRequest.contract: String`, `PWRunnerControlReply.contract: String` (runner/Sources/PWRunnerCore/PWRunnerTransport.swift:41-86); `PWRunnerClientCapture.contract` (same file :175; schema record 32 tag 2 `String`).
- OBSERVED: host refuses a reservation without a decodable string `contract` as `invalid_request/malformed_control` (PWRunnerService.swift:293-296). Submission refusals reuse `PWRunnerControlReply`, so they also carry it.
- Tests: OBSERVED ReservationAdmissionTests.swift:100-117; client main.swift:168-190 (runner/Tests/PWRunnerClientSessionTests).

### 2. L249 "The capture and embedded host frame are independently admitted."
Verdict: SUPPORTED
- OBSERVED: capture: `decode_bound(retained, true, BUILD_CONTRACT)`, then explicit contract compare, then `validate_capture` (controller/src/runner_client.rs:705-729, 260-266). Reply: separate `decode_bound::<PWRunnerRunResult>(&raw.data, false, BUILD_CONTRACT)` (:743-766). `decode_bound` reads fingerprint, then root record id, then producer context only, then full decode (controller/src/porcelain.rs:174-222). Production has no unbound `decode` caller (grep: only tests).
- Tests: OBSERVED runner_client.rs:1226-1265 (foreign reply inside current capture → `UnsupportedContract`, bytes retained; also asserts the contract gate precedes a malformed descendant), :1374-1389 (foreign capture → `unsupported`, submission `unknown`), :1308-1344. Integrated: reservation_controls.py:543-588 `old_response` (shipped controller + client; instrumented host flips one byte of producer contract): asserts `unsupported_runner_response`, `submission == invoked`, `runner_result is None`, no fallback compile, one `request_received`.

### 3. L249 "The binary shape fingerprint guards decoding and is not a public compatibility identity." / L345 "supplies no independent compatibility permission"
Verdict: SUPPORTED
- OBSERVED: fingerprint mismatch → `UnsupportedSchema` before any payload byte (porcelain.rs:156-161, 179-184); a matching fingerprint still requires the contract (porcelain.rs:218-220).
- Tests: porcelain.rs:568-573; runner_client.rs:1308-1339; Python porcelain_codec.py:194-205, 525-533.
- INFERRED distinction: the fingerprint covers the schema only. The hand-written primitive codec (kind codes, widths, header) in PWPorcelain.swift, porcelain.rs, tests/lib/porcelain.py is outside it; only the `PWP1` magic and the build contract cover that.

### 4. L249 "Reservation and submission failures never authorize replay after an uncertain invocation."
Verdict: SUPPORTED (client and controller); the retry that exists is reservation-only
- OBSERVED client: `submit` is called once, at PWRunnerClientSession.swift:252, after `phase = .submitted`. `retry()` requires `phase == .acquiring` (:169); `beginAttempt` requires `.initial/.waiting` (:130). After submission, connection failure → `complete("xpc_error")` (:197); deadline → `xpc_timeout`; refusal/malformed control → terminal (:257-275).
- OBSERVED acquisition retry: occupied, `transport_error`, `rpc_timeout` retry on a new connection up to 256 attempts / overall deadline (:168-204; limits in PWRunnerTransport.swift:7-16). A lost reservation reply can leave a granted-but-unused reservation at the host; that re-reserves, it does not resubmit. The reservation request has no specimen fields.
- OBSERVED host: slot never returns to `.free` (PWRunnerReservation.swift:18-99); reused token → `consumed`.
- OBSERVED controller: one client invocation (runner_client.rs:844-882; run_flow.rs:699 single call site, no loop). `fallback_eligible` (runner_client.rs:642-652) only gates an sbpl-check compile.
- Tests: client main.swift:83-98, 138-167 (production session class compiled with fake connections; not the signed binary). Rust runner_client.rs:1488-1514. Integrated (opt-in): reservation_controls.py `lost_execution` :471-484 (host killed before reply; one `request_received`), `lost_capture` :486-509 (one `client_started`, one `selector_invoked`), `lost_control` :447-469 (exactly one granted attempt, one effect byte).

### 5. L249 "Example: a foreign live peer behind a matching registry entry receives no specimen submission."
Verdict: PARTIALLY SUPPORTED (code fully; test weaker than the sentence)
Order established:
- (a) Registry: `require_current_contract(&record.contract)` — nonempty, not `unbound`, equal to controller `BUILD_CONTRACT` (runner_manager.rs:20-28) — at runner_select.rs:480 (run) and runner_commands.rs:628 (verify), before the client is launched. Compared value is the stored registry string, not the bundle or binary.
- (b) Live peer, host side: request `contract` == host compiled `PWBuildContext.contract`, host not `unbound`, else control `unsupported_protocol` (PWRunnerService.swift:293-299).
- (b) Live peer, client side: control reply `contract` == client compiled contract, checked before the rest of the reply is decoded (PWRunnerClientSession.swift:205-216). Failure → `protocol_error/unsupported_protocol`, terminal, no retry (:237-241).
- Specimen bytes leave the client only at :252, after an admitted `granted`. So both sides refuse, and the specimen cannot reach a peer whose reported contract differs (OBSERVED code order). The identity is self-reported by the peer (PWRunnerTransport.swift:5-6).
- (c)/(d): group 2, both after the fact.
Tests:
- OBSERVED unit, client: main.swift:179-181 (`{"contract":"test:foreign",...}` → `unsupported_protocol`, `submissions == 0`). Host: ReservationAdmissionTests.swift:110-116 (foreign request → `unsupported_protocol`, no reservation id).
- OBSERVED integrated: reservation_controls.py:532-541 `old_control`. The host is a recompiled, instrumented copy whose `reserveRunner` returns `{"contract":"test:foreign","legacy":true}` before production checks (tests/fixtures/byoxpc/ReservationTrace.swift:35-41; injection at reservation_controls.py:49-57). Controller and client are the shipped signed binaries. Asserts: `submission == not_invoked`, terminal `protocol_error`, reason `unsupported_protocol`, `runner_result is None`, no effect file, no `orchestration_entered`/`worker_spawned` on those hosts.
- Gap: the branch does not assert absence of a host-side `request_received` event. "Receives no submission" rests on the client's own capture plus absence of orchestration.
- Gap: the production host's own refusal is bypassed in this arrangement; it is covered only by the Swift unit test.
- Gap: no test uses a genuinely foreign signed host.
- HYPOTHESIS: a host predating `reserveRunner` yields XPC errors and up to 256 reconnects, no submission. Experiment: install a v0.3.5 service under a current-contract registry record and trace.

### 6. L296 "Install admits service `PWContract` before signing or launchd mutation and rechecks after signing."
Verdict: SUPPORTED by code; "before" tested end to end; the recheck refusal is untested
- OBSERVED: `PWContract` read with `plutil -extract PWContract raw -expect string` (controller/src/bundle.rs:19-41). `require_current_contract` at runner_commands.rs:261 precedes registry lock (:302), equipment verification (:318), `sign_install_tree` (:343-356), plist write and `launchctl bootstrap` (:451-457).
- OBSERVED recheck: `codesign_verify`, re-read Info.plist, `require_current_contract`, and equality of contract/bundle id/executable/package type (:364-373). It runs even when no signing flag was given.
- Tests: bundle.rs:73-113. Integrated (opt-in) registry_recovery.py:224-259: missing/empty/number/real/boolean/old/foreign markers through the shipped CLI with `--identity - --allow-adhoc` and bootstrap enabled; asserts exit 2, the message, identical bundle/registry-dir/LaunchAgents inventories before and after, service absent, no record. The suite README notes these are endpoint observations.
- No test references "runner bundle metadata changed during signing" (grep: source only). HYPOTHESIS experiment: mutate Info.plist between signing and the recheck.
- INFERRED distinction: the admitted value is the Info.plist string. Nothing at install compares it with the host executable's compiled identity; that is first observed at reservation.

### 7. L296 "Registry and live-peer identities must both match for execution."
Verdict: SUPPORTED (external runners). Evidence: groups 5(a), 5(b). Tests: runner_select.rs:1290-1308 (`""`, `unbound`, `test:foreign` not executable, still findable); registry_recovery.py:374-379.
- OBSERVED: the built-in runner has no registry identity; only the reservation check applies (runner_select.rs:430-438).

### 8. L296 "Records without a contract remain listable, reconcilable and removable…" + "Example: an owned legacy record cannot execute but can be removed after observed absence."
Verdict: SUPPORTED
- OBSERVED: `contract` is `#[serde(default, skip_serializing_if = "String::is_empty")]` (runner_manager.rs:452-453). list/status/reconcile do no contract check (runner_commands.rs:473-522, 769-888). `remove_record` has none (runner_manager.rs:1532-1650); it completes only when service and plist are observed absent with no warnings (:1437-1439, 1623).
- Tests: runner_manager.rs:2163-2228; runner_select.rs:1290. Integrated (opt-in) registry_recovery.py:345-424 with the shipped CLI and a live user-domain launchd service: `contract` popped, `kind: debuggable`, helper read-backs removed. Asserts `run` → `tool_error` containing "upgrade and reinstall" with `runner_client is None`; `runner verify` exit 2; list/status/reconcile return the record, ownership `owned`; an unrelated install/remove leaves it without `contract`; `remove --skip-bootout` retains pending cleanup; second remove boots out and both are absent.
- Limits: the record is constructed, the service is the current build (the README says so). "No client launched" is `runner_client is None`, not a process trace.

### 9. L297 opaque metadata, pending-cleanup shape, read-back, aliases
(a) "Unknown record, ownership, signature, entitlements and registry metadata survives unrelated writes and pending cleanup as opaque data."
Verdict: PARTIALLY SUPPORTED
- OBSERVED: `#[serde(flatten)] extra` on `RunnerSignature`, `RunnerEntitlements`, `RunnerOwnership`, `RunnerRecord`, `RunnerRegistry`, `PendingCleanup` (runner_manager.rs:89-139, 436-497). No production code reads `.extra`.
- Tests: runner_manager.rs:2163-2228; registry_recovery.py:353-401 (`kept == projected`).
- OBSERVED exception: `runner validate` replaces `record.signature`, `record.entitlements` and helper read-backs with fresh values whose `extra` is empty (runner_manager.rs:1046-1069, 1093-1098; runner_commands.rs:716-756), for every record whose executable exists. Unknown keys inside signature/entitlements are therefore dropped (INFERRED effect; no test asserts either way). It also adds `kind` and read-backs to legacy records. Whether validate is an "unrelated write" is not defined by the document.
- OBSERVED: "unknown metadata" means unknown keys. An unknown value for a known key (e.g. unrecognised `kind`) fails the whole registry parse (:557-558).

(b) Pending cleanup entry shape; "the reader also accepts historical flattened entries."
Verdict: SUPPORTED (unit level)
- OBSERVED: writer emits nested `runner`, `cleanup_started_at_unix_ms`, `observations` (:132-139). Reader tries the flattened form first, then nested (:141-191). The flattened form was the real v0.3.5 layout (`git show v0.3.5:controller/src/runner_manager.rs` lines 126-133).
- Tests: runner_manager.rs:2231-2251 only. No test feeds a flattened entry to the shipped CLI; registry_recovery checks only the nested output (:405-406).
- HYPOTHESIS: because flattened is tried first, a nested entry carrying opaque top-level keys that satisfy every required `RunnerRecord` field would be read as flattened. The current writer cannot produce this.

(c) "Publication requires a lossless read-back before atomic replacement."
Verdict: SUPPORTED, narrower than the words may suggest
- OBSERVED: `save_registry` serializes in memory, parses those bytes, reserializes, requires byte equality; then temp file `create_new` 0600, `write_all`, `sync_all`, `rename` (:596-629).
- The "read-back" is of the in-memory serialization. The temp file is not re-read from disk, and nothing is compared with the previous on-disk content. What it catches is an opaque key colliding with a known key.
- Tests: :2254-2263, :2266-2283; registry_recovery.py:261-286.
- HYPOTHESIS: values serde_json cannot represent exactly (integers beyond u64; `serde_json = "1"` with no feature list visible at controller/Cargo.toml:22) change at load and pass the check.

(d) "It never establishes execution compatibility or ownership."
Verdict: SUPPORTED on either reading; the pronoun is ambiguous. In source the sentence is attached to opaque metadata (runner_manager.rs:438-439); in the document "It" follows "Publication".

(e) "Known retired kind aliases project as their current kind."
Verdict: SUPPORTED. Aliases `machme`, `debuggable` → `byoxpc` (:46-52); `RunnerKind::parse` rejects them for new input (:56-62). Tests :1997-2031; registry_recovery.py:383-388, 400. The next save rewrites the stored value.

### 10. L19-20 "Reinstall external runners from the current app when its contract changes."
Verdict: SUPPORTED as operator guidance. Refusal text says "upgrade and reinstall the runner" (runner_manager.rs:25). OBSERVED: install over an existing record is refused (runner_commands.rs:303-314), so reinstall means remove then install.

### 11. L304-311 schema ownership; "All three derive from the one schema, so they cannot disagree with each other about structure; none of them checks the schema itself."
Verdict: PARTIALLY SUPPORTED — "cannot disagree" is stronger than the code
- OBSERVED: the generator emits Swift record writers and stored-field regions, Rust structs/readers/Serialize, and Python tables (docs/generate_porcelain.py:154-271, 301-319). tests/lib/porcelain.py is hand-written (186 lines) and imports only the generated tables, so "separately written" holds. "None checks the schema": only the generator's `validate` does (:89-151).
- OBSERVED exceptions:
  1. The Swift writer for the one declared variant is hand-written with literal case tags 1 and 2 (PWPorcelain.swift:115-126). `swift()` emits nothing for variants. Rust and Python derive those tags from the schema. I found no check pinning the Swift literals.
  2. Producer-context tags are hard-coded in Rust `decode_bound` (porcelain.rs:199-207) and Python `decode_bound` (tests/lib/porcelain.py:172-181), and offsets in the test fixture ReservationTrace.swift:76-88.
  3. The three primitive codecs are independent hand-written implementations.
  4. The minimal-reply writers in PWRunnerService.swift:161-200 choose fields by hand (tags come from generated constants and are ascending).
- INFERRED: agreement also depends on outputs being fresh; porcelain_codec.py:491-539 tests one-sided staleness.
- "Production reply ingestion is binary": SUPPORTED (Rust `Deserialize` is `#[cfg(test)]`; Python JSON path needs `allow_fixture_json`, porcelain_codec.py:183-192).

### 12. L313-326 frame format
Verdict: SUPPORTED on every width and rule
| Statement | Swift writer | Rust reader | Python reader |
|---|---|---|---|
| `PWP1` + 32-byte fingerprint + one root value | PWPorcelain.swift:28-33 | porcelain.rs:156-168 | porcelain.py:143-155 |
| 1-byte kind, 4-byte LE length | :18-26 | :84-90 | :32-38 |
| kinds 1-9 | :57-126 | :86, KIND consts | :15-16 |
| 8-byte integers; native width/signedness enforced | :69-83 | :244-258 | :46-54 |
| record: 2-byte id, strictly increasing nonzero 2-byte tags | :39-55 (`tag > last`, last starts 0) | :109-137 (`tag <= last` refused) | :63-73 |
| list/map 4-byte count; keys unique, UTF-8 byte order | :85-113 | :272-323 | :107-127 |
| variant 2-byte case tag | :115-126 | :223-233 | :128-137 |
| optionals absent | :51-53 | generated `Option` | :86-91 |
- Writer "by construction": the generator requires sorted unique tags (generate_porcelain.py:101) and emits in schema order; a runtime guard throws otherwise. Map keys sorted at write. No Swift test exercises the "field order" guard (grep of runner/Tests: none).
- OBSERVED schema: all digest fields are `Data`; equipment refs are `UInt32`/`UInt32?`. The other `*_ref` fields are `String` request-chosen names, as the prose says.
- INFERRED: Rust and Python nesting bounds agree at 32 values.

### 13. L328-330 "Readers reject unsupported fingerprints, unknown tags/records/cases, missing required fields, incorrect kinds, invalid text, impossible lengths/counts, duplicates and trailing data."
Verdict: SUPPORTED in code for both readers; Rust test coverage is incomplete
| Rejection | Rust code | Rust test | Python test (porcelain_codec.py) |
|---|---|---|---|
| fingerprint | porcelain.rs:159 | :568-573 | :199 |
| unknown tag | generated `_ =>` arm | :547-550 | :91 |
| unknown record | :121-123 | :543 | :89 |
| unknown variant case | porcelain_records.rs:21-25 | none | :128-129 |
| missing required | generated `ok_or` | :544 | :88 |
| wrong kind | :33-35, 39-41 | :551 | :92 |
| invalid text | :262 | :516 | :97 |
| impossible length | :68-72 | :562-564 | :98-100 |
| impossible count | :77-83 | none | :114-117 |
| duplicate/unordered tag | :131-133 | :545-546 | :90, 105-108 |
| duplicate/unordered map key | :315-317 | none | :121-124 |
| trailing data | :101-107 | :565-567 | :101, 199 |
- OBSERVED: the Rust fault loop asserts only `is_err()` per frame (:554-556), so it does not tell which rule fired; each frame differs from the valid one by a single fault.
- OBSERVED: no Rust unit test builds a map (kind 8) or variant (kind 9) frame (grep of controller/src). Only two map fields and one variant field exist in the schema.

### 14. L330-339 budgets, separate frames, truncation, collection
(a) Byte, nesting and logical-storage budgets; "not physical peak-memory bounds." Verdict: SUPPORTED
- OBSERVED: `LIMIT` 128 MiB, `DEPTH` 32 (porcelain.rs:17-18, 58, 91, 156); one `Cell` budget per `decode`; charges for list slots, map slots, strings, bytes (:42, 263, 277-282, 303-308). docs/limits.json rows `porcelain_frame_bytes` 134217728, `porcelain_decoded_storage_bytes` 134217728, `porcelain_nesting` 32.
- Tests: :457-481 (constants; `Cursor::new` at depth 32/33), :483-507 (shared budget).
- OBSERVED: no Rust test feeds a frame over `LIMIT` or a value nested past 32 through `value()`. limits.json names `authored_record_faults…` as the "boundary" check for frame bytes and nesting; that test contains neither. Python covers depth 33 (:130-135) and a patched byte limit (:204).
- Nuance: `decode_bound` uses one throwaway budget for the producer pre-read, then a fresh one (:185, 221 → 162).
(b) "separate frames, each read under its own budget." SUPPORTED (runner_client.rs:706, 743).
(c) "The host writer bounds a reply by the frame limit." SUPPORTED by code; untested at the limit.
- OBSERVED: `pwPorcelainByteLimit = 128 MiB` with guards (PWPorcelain.swift:6, 19, 46, 62, 87-106). This Swift constant is not in docs/limits.json and no test compares it with the Rust `LIMIT` (grep: only ReplyMaximumTests.swift:163 uses it, as an upper bound on dense fixtures). Writer-failure tests use injected failing encoders (ReplyFailureTests.swift:220-262).
(d) "client retains at most its smaller reply allowance; a larger reply arrives truncated and is refused as `runner_reply_truncated`." Verdict: SUPPORTED by code; the outcome has no test
- OBSERVED: client retains a 92 MiB prefix and sets `truncated` (PWRunnerTransport.swift:15, 156-169). Controller maps it to `runner_reply_truncated` (runner_client.rs:736-741, 617). Constant agreement tested (ReservationAdmissionTests.swift:6-27, 185-191; runner_client.rs:994-1014).
- OBSERVED: the string `runner_reply_truncated` occurs only in runner_client.rs, docs/CONTRACT.md and tests/COVERAGE.md:45. The Rust capture builder hard-codes `truncated = false` (runner_client.rs:1179).
- HYPOTHESIS: whether a 92-128 MiB reply is reachable from a live host. Wording: the full reply does arrive at the client; the capture retains a prefix.
(e) "The controller collects the client's complete output before applying its retention cap; reading is not streamed and has no receiver deadline of its own." Verdict: SUPPORTED
- OBSERVED: `child.wait_with_output()` with no timeout (controller/src/utils.rs:55-82); 272 MiB prefix cap applied afterwards (utils.rs:7-9; runner_client.rs:665-667); a truncated stdout is never decoded (:699-701). The only deadline is the client's own (`--deadline-ticks`, :844-857).
- Tests: runner_client.rs:1566-1579, 1524-1565.

### 15. L341-345 fingerprint coverage
Verdict: SUPPORTED; the listed attributes are accurate but not the complete set
- OBSERVED `wire_identity` (generate_porcelain.py:275-298) includes: schema `version`; per record `id`, `name`, `path_forms`, `conditional_null`; per non-`local_only` field `tag`, `name`, type descriptor (optional/list/map wrappers, primitive width and signedness, record id or variant name), `json_null`, `projection`; `roots`; the whole `variants` object.
- Excluded: `source`, `default`, `doc`, `mutable`, `swift_name`, `local_only` fields.
- OBSERVED experiment: my in-memory reimplementation reproduces the committed fingerprint `80013e5b…e224`. Mutations of the loaded schema: optional↔required CHANGED; field rename CHANGED; `json_null` toggle CHANGED; hex→base64 CHANGED; `Int`→`Int32` CHANGED; variant case rename CHANGED; `default`, `doc`, `source`, `mutable`, `swift_name`, `local_only` field, `Int`→`Int64` unchanged.
- So "an added optional field or a changed null or byte spelling produces a different fingerprint" and "Source locations, defaults and comments are outside it" both hold. Not named in the prose but included: optionality, record names, variant case names/tags/types, roots, schema version.
- Tests (porcelain_codec.py): :491-527 add optional field, drop field, renumber tag, change kind, add record → fingerprint differs; :470-489 doc-only → unchanged. Not tested: null-spelling change, projection change, field rename, optionality toggle, default-only change.
- "The public build contract is checked during reservation before execution": SUPPORTED (group 5).

### 16. L347-351 presentation rules
Verdict: SUPPORTED exactly for schema byte fields; one public base64 field is outside the list
- OBSERVED schema, 20 projected fields. base64: `PWRunnerReplyCapture.data_base64`, `CompiledProfileCapture.bytecode_b64`, `PWValidatorDecodeFault.context_b64`. hex: `PWRunnerFreshRead.content_hex` and 16 digest fields (all `*sha256`, `*cdhash`, `worker_identity`, `PWWorkerEvidence.abi_identity`, `PWRunnerControlObservation.sha256`). The generator requires every `Data` field to declare a projection (:122-125). `Hex` is lowercase (porcelain.rs:366-377).
- Tests: porcelain.rs:581-592; porcelain_codec.py:70-81, 388-392.
- OBSERVED: a rejected client capture is also published as base64 at `runner_client.transport.data_base64` with `format: "porcelain"` (runner_client.rs:70-82, 776-780; test :1401-1405). It is a controller field, not a schema byte field, so it is absent from L348-349 and from the fingerprint.

### 17. L351-355 named validators; "Conflicting observations remain publishable with dependent claims withheld."
Verdict: SUPPORTED at reachability level only; individual rules not examined (outside this scope)
- OBSERVED: `porcelain_admission::admit_reply` calls `phase_issues`, `policy_read_issues`, `native::validate`, `actor_associations`, `actor::validate` (porcelain_admission.rs:1416-1486); the actor module has `setup`, `application`, `equipment`, `owned_reap_valid`, `gates`, `custody` (porcelain_actor.rs:369-1655); lifecycle via `validate_lifecycle` in `project` (:1323-1335). Reached from run_flow.rs:749. Any issue sets `process_disposition "withheld"`, integrity `invalid`; the reply stays in the envelope.
- Ordering nuance: `project(...)` runs before `admit_reply` and is overridden afterwards (:1626-1631). The emitted result matches "withheld"; "before projecting" is not the literal call order.

---

## B. Discrepancies and risks

Statements stronger than the code
1. L307-308 "cannot disagree with each other about structure": the Swift variant writer's case tags are hand-written, and producer-context tags are hard-coded in both `decode_bound` implementations (group 11).
2. L297 "survives unrelated writes": `runner validate` drops unknown keys inside `signature`/`entitlements` and helper read-backs (group 9a).
3. L297 "lossless read-back": it is an in-memory idempotence check, not a read of the written file or a comparison with the prior registry (group 9c).

Places a competent reader could reach a false conclusion
4. The manifest's named check for `transport` and `installation` is `runner_byoxpc`. That suite is `default: false` in tests/catalog.json, and release acceptance runs only the default battery (docs/SIGNING.md:229-231, 397). The manifest check itself only requires that the suite name exists (docs/generate_contract_stamps.py:53-55). Both "Example:" sentences are therefore verified only by opt-in cases (`reservation_controls` also needs identity, swift, clang, meson).
5. L249 example: the integrated control uses an instrumented host returning a substituted control; it shows the shipped client declines to submit, not that a foreign signed host was contacted, and it does not assert absence of a host-side receive event (group 5).
6. L296 "Install admits service `PWContract`": this is the Info.plist string, not the service binary's compiled identity (group 6).
7. L336 "arrives truncated": truncation is client retention after full receipt.
8. L341 list reads as complete but omits optionality, record names, variants, roots and schema version (group 15).
9. L347-349 base64 list omits the rejected-capture `data_base64` (group 16).
10. L297 "It never establishes…": ambiguous referent.
11. Peer identity at reservation is self-reported; a foreign peer's advertised contract value is not retained in the capture, only the control's byte count and SHA-256 (PWRunnerTransport.swift:119-135).

Implemented but untested
12. `runner_reply_truncated` outcome (group 14d).
13. Post-signing recheck refusal (group 6).
14. Rust reader: unknown variant case, impossible collection count, duplicate/unordered map key, frame over 128 MiB, nesting past 32 through `value()` (groups 13, 14a). Python covers the first three and depth.
15. Swift writer: tag-order guard, over-limit refusal; `pwPorcelainByteLimit` unpinned to limits.json or the Rust constant (groups 12, 14c).
16. Fingerprint sensitivity to null spelling, projection, rename, optionality; insensitivity to defaults (group 15) — code and my recomputation only.
17. Flattened pending-cleanup form through the shipped CLI (group 9b).
18. limits.json attributes "boundary" checks for `porcelain_frame_bytes` and `porcelain_nesting` to a test that contains neither (group 14a). This is in docs/limits.json, not CONTRACT.md.

Distinctions the document requires that the code does enforce (correct and well supported)
- Contract compared on both sides of reservation before any specimen bytes are sent; no post-submission retry anywhere in client or controller (groups 4, 5).
- Capture and host reply admitted separately, each under its own budget, producer gate before descendants (groups 2, 14b).
- Fingerprint checked first and never sufficient alone (group 3).
- `PWContract` admission before signing, registry and launchd changes, with endpoint evidence from the shipped CLI (group 6).
- Contract-less records listable, reconcilable, removable, not executable; removal gated on observed absence (group 8).
- Retired kind aliases; nested pending-cleanup writer; atomic replace with old readers preserved (group 9).
- Every stated frame width, ordering rule and reader rejection is implemented in both readers (groups 12, 13).
- Byte/hex presentation mapping for schema byte fields matches L347-351 exactly (group 16).
- Controller collects all client output, caps afterwards, no receiver deadline (group 14e).
- Fingerprint inputs/exclusions as stated; committed fingerprint independently reproduced (group 15).

Not determined
- Live XPC behaviour against a genuinely foreign or pre-reservation host (group 5).
- Reachability of a 92-128 MiB reply (group 14d).
- Rule-level correctness of the semantic validators (group 17).
- Whether any opt-in case named here has a recorded passing run for this commit: no test output was inspected.

---

## C. Absolute file index
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/contract_surfaces.json
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/porcelain.json
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/generate_porcelain.py
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/generate_contract_stamps.py
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/limits.json
- /Users/raccoon/Desktop/Security/PolicyWitness/docs/SIGNING.md
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/porcelain.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/porcelain_records.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/porcelain_admission.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/porcelain_actor.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/runner_client.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/runner_manager.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/runner_commands.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/runner_select.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/run_flow.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/bundle.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/controller/src/utils.rs
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Clients/PWRunnerClient/PWRunnerClientSession.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Clients/PWRunnerClient/main.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Sources/PWRunnerCore/PWRunnerService.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Sources/PWRunnerCore/PWRunnerReservation.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Sources/PWRunnerCore/PWRunnerTransport.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Sources/PWRunnerCore/PWPorcelain.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Sources/PWRunnerCore/PWPorcelainRecords.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Tests/PWRunnerClientSessionTests/main.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/lib/porcelain.py
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/lib/porcelain_schema.py
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/lib/runner_client_capture.py
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/suites/source_drift/porcelain_codec.py
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/suites/runner_byoxpc/README.md
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/suites/runner_byoxpc/opt_in/reservation_controls.py
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/suites/runner_byoxpc/opt_in/registry_recovery.py
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/fixtures/byoxpc/ReservationTrace.swift
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/catalog.json
- /Users/raccoon/Desktop/Security/PolicyWitness/tests/COVERAGE.md
````

### Pass 4: read first-hand by the report writer at the time

These readings were made to check the return before the report was written. They are the report writer's own and are not part of the return.

- Reservation order on both sides: `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift:200-256`, `runner/Sources/PWRunnerCore/PWRunnerService.swift:286-326`.
- The hand-written variant writer and the schema's variant: `runner/Sources/PWRunnerCore/PWPorcelain.swift:112-127`, `docs/porcelain.json`.
- Occurrences of `runner_reply_truncated` in the tree.
- Registry save and validate: `controller/src/runner_manager.rs:596-630`, `:1040-1070`.
- `wire_identity` in `docs/generate_porcelain.py`, read in full before the pass returned.

### Pass 4: now known to be wrong, and other notes

- Nothing in this return is known to be wrong.
- The pass reports one in-memory recomputation of the fingerprint, run outside the checkout from `docs/porcelain.json`. The brief forbade running generator scripts; the pass re-implemented the computation and ran no repository script. The report mentions this in its section 1.5.

## Pass 5: Build identity plumbing and internal host/worker identity

Launched 2026-11-10T01:57:42.937Z; last transcript record 2026-11-10T02:08:11.212Z. Brief: 8,454 characters. Return: 31,861 characters.

**Used in the report for:** `L-02`, `L-03`, `L-12`, `L-23`, `L-44` to `L-48`; sections 4.3 and 4.4; findings `F-09`, `F-10`, `F-11`, `F-17`, `F-18`; section 9.

### Pass 5: brief, verbatim

````text
You are helping with a READ-ONLY examination of `docs/CONTRACT.md` in the repository at /Users/raccoon/Desktop/Security/PolicyWitness (commit 298c1805, clean tree). PolicyWitness is a macOS tool: a Rust controller CLI (`controller/src`), a Swift XPC runner host (`runner/Sources`, `runner/Clients`, `runner/Services`) and a C worker (`controller/tools/pw_probe_runner`). The examination prepares the public contract for external review. The goal is to establish, per claim, whether the document's statement is traceable to reachable implementation and to tests that exercise the stated relationship. It is not to defend the document and not to manufacture findings.

HARD RULES: Do not edit, create or delete any file in the checkout. Do not build, run tests, run generators, or run any command that writes into the checkout (no `make`, `cargo`, `swift build`, `tests/run.sh`, no generator scripts — not even with --check). Use only Read, Grep/Glob-style searching, and read-only git commands. The shell is zsh: quote globs; an unmatched glob aborts the command.

YOUR SCOPE: how the compiled build identity reaches binaries, and the internal host/worker identity. Read all of docs/CONTRACT.md once for context. (Another examiner is separately reading `docs/build_contract.py`, `docs/source_identity.py`, `docs/generate_contract_stamps.py` and `docs/generate_worker_identity.py` themselves; you should read them for context but concentrate on the consumers.)

PART 1 — build identity plumbing (CONTRACT.md lines 8-15 and 436-441):
- "Other packaged builds emit `development:<sha256>`"; "Direct Cargo and SwiftPM builds are `unbound` and refuse public requests and packaged peer checks."; "`--version`, the envelope `build.contract`, and app/service `PWContract` report the compiled identity. Describe and commit remain provenance, not admission keys."; "Only an annotated release tag on a clean tree can produce a release contract."
Trace: `build.sh`, `meson.build`, `meson.options`, `Makefile`, `controller/build.rs`, `controller/Cargo.toml`, `runner/Package.swift`, `Info.plist`, any generated `PWBuildContext` Swift, and `tests/build_equipment.py`, `tests/build-evidence.py`, `tests/lib/build_provenance.py`. Determine:
  a. When in the build is `docs/build_contract.py` invoked, how many times, and how does its value reach (i) the Rust controller (env var read by build.rs? `env!`?), (ii) the Swift host/client/service (generated source? `-D`?), (iii) `Info.plist` `PWContract` for the app and each service bundle. Can the three disagree within one build? Is there a check that they agree (before signing, in tests)? Could sources change between identity computation and compilation without detection (the docs say build checks happen "before compilation and again before signing" for the worker identity — is there an analogous recheck for the public contract)?
  b. Can a caller supply the identity (env `PW_BUILD_CONTRACT`, meson option, make variable)? The script's docstring says "never accept a caller-supplied identity" — check what build.rs / Package.swift / meson do if `PW_BUILD_CONTRACT` is set in the environment of a direct `cargo build` or `swift build`. Is `unbound` really the only result of a direct build? Where is `unbound` defined and where is it refused ("refuse public requests and packaged peer checks") — cite each refusal site in Rust and Swift.
  c. `--version` output, envelope `build.*` fields (contract, describe, commit, version, number): where each comes from. Are describe/commit used in any admission comparison anywhere (Rust, Swift, Python harness)?
  d. Which inputs that influence the built product are NOT in the identity scope (`DIRECTORIES`, `FILES`, `SUFFIXES` in build_contract.py)? Enumerate files under those directories whose suffix is outside SUFFIXES (use `git ls-files` on those directories and filter), and build inputs outside them: `Makefile`, `notarize.py`, `docs/porcelain.json`, `docs/limits.json`, generators in docs/, entitlements files with other suffixes, `runner/Services/*` resources, toolchain/SDK, environment variables that alter compilation (search build.sh/meson.build for `PW_` env vars and options that change behavior of the product, e.g. debug/test-only features). For each, say whether it is packaged or affects packaged behavior. CONTRACT.md line 100 says "Every shipped-source change changes a development contract" and line 10-11 says "shipped-input edits change it. Ordinary documentation and test edits do not" — list concrete counterexamples if any exist, and concrete confirmations.
  e. Tests that exercise this: search `tests/suites/` (e.g. source_drift, anything named contract/identity/release), `tests/catalog.json`, and `tests/lib/contract.py`. What do they assert? Is the release path (`release:vX.Y.Z`) tested (e.g. in a temporary clone with a tag), including dirty tree, lightweight tag, two tags, index flags (`assume-unchanged`/`skip-worktree`)?

PART 2 — internal host/worker identity (CONTRACT.md lines 379-425) and line 171 "The worker ABI identity remains independent of the public build identity":
  a. Lines 382-390: build checks "the C, Swift and test copies before compilation and again before signing, and never writes them" — find those invocations in build.sh/meson.build. "Direct source-test builds regenerate the same way" — what does this refer to and is it true?
  b. Lines 392-404: digest scope. Compare prose to the generator's SOURCE_DIRS/SOURCE_FILES/suffixes. "the build reads Ninja's dependency log to check that the compiler consumed nothing for the worker and the shim beyond these inputs, the selected SDK and the developer directory" — find this check; what is "the shim"? Is the check performed for Swift host sources too or only the C worker and shim?
  c. Lines 406-414: header layout — "fixed bootstrap magic at byte 0 and 32 identity bytes at byte 64" — verify against `pw_probe_runner_abi.h` and the Swift mirror (offset assertions?). "The worker checks the mapped region's size and these fields before reading policy input, publishing evidence, or using layout-dependent fields" — verify order in `pw_probe_runner.c`. "An identity or magic mismatch exits with code 4 and no ready/applied/done publication." "The bootstrap magic also makes ordinal-era workers refuse the header." "The host checks the identity before decoding worker evidence and before releasing attempts." — find the host checks in Swift and whether they are on the production path; what does the host compare (the shared region is written by the host itself — what does a host-side identity check establish?). "`runner_subprocess.worker_evidence.abi_identity` records the host-selected identity, including when no worker publication exists" — verify the field path exists in public output with that spelling.
  d. Lines 416-425: the limits disclaimers. Are "Compiled C/Swift layout checks, signed artifact provenance, and lifecycle/order tests" real, and where?
  e. Tests for exit code 4 / identity mismatch / magic mismatch: find them, say what they assert and whether they run a real worker binary.
  f. Is the worker identity "independent of the public build identity"? Note the two digests share inputs (`runner/Sources`, `controller/tools/pw_probe_runner`, build.sh, meson files) — say precisely in what sense they are independent (separate computation, separate purpose) and in what sense not (overlapping inputs; a worker-identity change implies a development-contract change?).

Do NOT treat the existence of a type, field, function or test as proof. Check reachability and what a test asserts.

REPORT FORMAT (your final message is consumed by another agent writing the report; be precise, not polished). For each claim group give:
- CONTRACT.md line range and a short quote
- Verdict: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / CONTRADICTED / NOT DETERMINED
- Code evidence with `path:line` citations
- Test evidence with `path:line` and what the test actually asserts
- Label every statement as OBSERVED, INFERRED, or HYPOTHESIS (would need an experiment; describe it, do not run it)
Then a separate list: discrepancies, places a competent reader could reach a false conclusion, statements stronger than the code, distinctions the document requires but the code does not enforce, and statements that are correct and well supported (say so explicitly). Aim for completeness over brevity, up to about 4000 words. Do not propose fixes or rewrites.
````

### Pass 5: return, verbatim

````text
REPORT: build-identity plumbing and internal host/worker identity (docs/CONTRACT.md lines 8-15, 100, 171, 379-425, 436-441). Commit 298c1805, clean tree. Read-only; nothing was built or run. Labels: OBSERVED = read in source; INFERRED = follows from source plus tool semantics; HYPOTHESIS = needs an experiment (described, not run). Paths are relative to /Users/raccoon/Desktop/Security/PolicyWitness.

## PART 1: public build identity

### 1.1 Lines 8-9, 441: "A clean tree at exactly one annotated vX.Y.Z tag emits release:vX.Y.Z" / "Only an annotated release tag on a clean tree can produce a release contract"
Verdict: SUPPORTED for docs/build_contract.py and build.sh. NOT enforced for a direct Cargo build (see 1.4).
- OBSERVED docs/build_contract.py:81-90. `release:` needs all of: git toplevel equals root; `git status --porcelain --untracked-files=all` empty; exactly one tag at HEAD matching `v\d+\.\d+\.\d+` whose `cat-file -t` is `tag`; and `release_bytes_match` (39-70), which compares on-disk bytes with the tag's blobs for scoped paths and requires equal path sets.
- OBSERVED build.sh:251 overwrites `PW_BUILD_CONTRACT` unconditionally from the script, so a caller cannot supply it through build.sh, the Makefile (93-95) or Meson (meson.options has only `inspection` and `xpc`).
- Tests, OBSERVED tests/suites/source_drift/build_contracts.py (default case `source_drift/build_contracts`, temp copies with `git init`):
  - 228-257: lightweight tag gives development; annotated tag gives `release:v9.0.0`; an untracked file gives development with the same digest; a doc-only commit past the tag gives the same development digest; edits to main.rs, an augment and PolicyWitness.entitlements each change the digest; a symlinked source raises.
  - 180-197: an unsuffixed executable and `.DS_Store` leave the digest unchanged; an `--assume-unchanged` edit with clean `git status` gives a changed `development:`.
  - 259-267: env `PW_BUILD_CONTRACT=release:v9.9.9` is ignored by the script.
- Opt-in only: tests/suites/preflight/opt_in/build_refusals.py:2009-2030 builds a real `release:v0.0.0` and runs acceptance; tests/lib/release_accept.py:113-116 requires plist `PWContract` and `--version` `build.contract` to equal `release:v<CFBundleShortVersionString>`.
- Not tested (searched tests/suites): two annotated release tags at HEAD, `skip-worktree`, the nested-repository toplevel condition, tag-entry mode/kind refusal.
- Discrepancy with line 9 ("Other packaged builds emit development"), OBSERVED build_contract.py:88-89 and 121-122: a clean tree with more than one annotated release tag raises `ambiguous release`, the script exits 1 and build.sh stops at line 251. No identity is emitted. A dirty tree with two tags does emit development.
- Limit of "clean", INFERRED: outside the scoped paths, cleanliness is `git status` only. An index-flag-hidden edit to an unscoped tracked file (Makefile, docs/porcelain.json, tests/lib/native_sources.py) still yields `release:`. Line 12's "Git index flags cannot hide edited inputs" holds for scoped inputs only.

### 1.2 Lines 9-12, 100: "development:<sha256> over the shipped source and build inputs… shipped-input edits change it. Ordinary documentation and test edits do not" / "Every shipped-source change changes a development contract"
Verdict: PARTIALLY SUPPORTED. True for tracked source files in scope; the identity does not cover build variant, toolchain or caller flags, and the scope includes some files that are not shipped.
- OBSERVED scope, build_contract.py:15-26: DIRECTORIES are controller/src, controller/tools, runner/Sources, runner/Clients, runner/Services, runner/augments, filtered by SUFFIXES `.rs .c .h .swift .sb .plist .ent`. FILES are build.sh, meson.build, meson.options, runner/Package.swift, controller/Cargo.toml, Cargo.lock, build.rs, Info.plist, PolicyWitness.entitlements, docs/build_contract.py, docs/source_identity.py, tests/build_equipment.py, tests/build-evidence.py and tests/lib/{build_provenance,signer_check,cargo_config,checkout_lock,output_target}.py. Digest (73-79) is a domain prefix plus 8-byte length-framed path and bytes. File modes are not hashed.
- OBSERVED (`git ls-files`): only two tracked files under DIRECTORIES fall outside SUFFIXES: controller/tools/sb_api_validator/build.sh (manual helper) and runner/augments/README.md (build.sh:596 copies only `*.sb`). Neither is shipped. No tracked shipped source file is out of scope.
- OBSERVED/INFERRED: every Rust `include_str!` of an out-of-scope file (docs/limits.json, tests/fixtures/…) follows a `#[cfg(test)]` marker (e.g. porcelain.rs:447/459, request_patch.rs:102/131, utils.rs:231/233; reply_fixtures is `#[cfg(test)] mod` at main.rs:22-23). C local includes all resolve inside controller/tools/pw_probe_runner.

Counterexamples: inputs that change packaged bytes or behavior without changing the contract.
1. Build knobs, OBSERVED build.sh:135-137, 397-411; meson.build:91. `PW_INSPECTION` switches Swift `-Onone -g` vs `-O` and Rust flags. `BUILD_XPC=0` produces an app with no client, host or XPC service. Same contract either way. `make release` does not pin them (Makefile:95 forwards only DIST_DIR, IDENTITY, PW_FRESH_BUILD; the environment passes through).
2. Caller `RUSTFLAGS`, OBSERVED build.sh:398-407: accepted and recorded as `caller`; not in the identity.
3. Toolchain and SDK (rustc/cargo, swiftc, clang, `SDKROOT`, `DEVELOPER_DIR`, Meson/Ninja): recorded in provenance, not in the identity. CONTRACT.md 416-420 disclaims this for the worker identity; there is no matching disclaimer for the public contract.
4. `PW_VERSION` / `PW_BUILD_NUMBER`, OBSERVED build.sh:245-246: caller overrides change `build.version`, `build.number` and the plist version strings. Line 440 does call these descriptive.
5. Crate sources: Cargo.lock is in scope, but build.sh:447 passes no `--locked`/`--frozen`. INFERRED: a stale lock would be rewritten in-tree and then caught by the pre-sign recheck.
6. Checks whose outcome gates the product but whose code is unscoped: tests/lib/native_sources.py, tests/lib/cargo_artifacts.py, tests/lib/python_start.sh, tests/lib/checkout_lock.sh, the docs/generate_*.py `--check` scripts, vendored tomli. They gate; they do not contribute bytes.
7. docs/porcelain.json and docs/limits.json are unscoped generator inputs; the generated Swift/Rust is in scope and build.sh:225-234 refuses stale copies.
8. Makefile, notarize.py, dist/README.md, dist/AGENTS.md and the staged guide dist/PolicyWitness.md are unscoped; none is inside the app.

Counterexamples in the other direction: non-shipped files that change the contract.
- controller/tools/sb_api_validator/debug.ent is in scope by suffix, but build.sh:727 signs the validator with no entitlements; only the manual helper uses it. OBSERVED.
- runner/Package.swift and the SwiftPM placeholder header under runner/Sources/PWCWorkerShim/include are in scope though not part of the Meson product.
- Eight files under tests/ are in FILES. "Ordinary … test edits do not change that digest" is true only because of the word "ordinary".
- INFERRED: any untracked or ignored file with a scoped suffix under a scoped directory enters the digest whether or not it is compiled, since discovery is by filesystem (source_identity.py:19-23).
- "Incidental executables and OS files are excluded" is by suffix only. HYPOTHESIS: an AppleDouble `._main.rs` would be hashed, and an Emacs lock symlink `.#main.rs` would raise. Experiment: create each in a temp copy and call `identity()`.

Confirmations: build_contracts.py:245-252 (three edit kinds change the digest), 240-243 (doc-only change does not), 184-186.

### 1.3 Plumbing: when the script runs and how the value reaches each artifact
- OBSERVED invocations in one full build.sh run:
  1. build.sh:251, before session start and any compile; exported at 252.
  2. meson.build:94-96 `configure_file(command: … build_contract.py --swift-stdout, capture: true)`, at every `meson setup` / `--reconfigure` (build.sh:510-516), only when `xpc=true`.
  3. build.sh:681-685, recomputed before signing; refuses with "public build contract changed during compilation".
- Rust: OBSERVED controller/src/json_contract.rs:11-20, `option_env!("PW_BUILD_CONTRACT")`; empty or absent gives `"unbound"`; under `cfg(test)` the constant is `"test:policy-witness"` (21-22). controller/build.rs:20-28 only emits `rerun-if-env-changed`; it neither computes nor validates. `sbpl-check` shares the file via `#[path]` (bin/sbpl-check.rs:11).
- Swift: OBSERVED the generated `builddir/PWBuildContext.swift` is added to both the client and host targets (meson.build:127) with `-D PW_PACKAGED_BUILD` (93), which removes the fallback enum at runner/Sources/PWRunnerCore/PWRunnerAPI.swift:155-167. `--swift-stdout` refuses if the value differs from env `PW_BUILD_CONTRACT` (build_contract.py:110-112). tests/lib/native_sources.py:226-229 requires the generated file in both targets.
- Info.plist: OBSERVED build.sh:263-270 `stamp_info_plist` writes `PWContract` from the shell variable into the app plist (573-574) and each service plist (636-637). It is not read back from any binary.
- Can the three disagree in one build.sh run? INFERRED no, by construction: one shell value feeds Cargo and both plists; the Swift value is recomputed and compared to it; the pre-sign recompute is compared to it.
- OBSERVED: build.sh has no step that asks a built binary for its public contract. The worker identity does get such a check (build.sh:687-689); the public contract does not.
- Not detected, INFERRED: a change-and-revert between lines 251 and 681 (the comment at 675-677 says the build "otherwise trusts the checkout not to change under it"); stale incremental objects under non-fresh builds (release paths force `PW_FRESH_BUILD=1`, Makefile:154-158).
- Tests of agreement, OBSERVED:
  - tests/suites/smoke/pw_specimen_smoke.sh:61-78 (default): app-plist `PWContract` equals `--version` `build.contract`, envelope `build.contract`, `runner_client.transport.contract` and `runner_result.producer.contract`; envelope describe/commit equal the plist values.
  - controller/integration/cli_contract.rs:152-177 (default `integration/cli.integration`): `--version` `data.contract` and `build.contract` equal the app plist.
  - build_contracts.py:199-206 (script refuses a foreign or empty env value) and 269-289 (the pre-sign guard text is extracted from build.sh and run in a copy; docs/BUILD.md:683 states the control runs "in the helper, not through the script").
  - Service-plist `PWContract` against the host's compiled value is checked at runtime only through the equipment inventory (tests/build_equipment.py:66 copies it from the plist; runner/Sources/PWRunnerCore/ActorEquipment.swift:129 and 352 compare it to `PWBuildContext.contract`) and at external install (controller/src/runner_commands.rs:261, 366-367).
- Secondary, OBSERVED: Swift `describe`/`commit` come from build_contract.py's own git calls (113-114), not build.sh's values (243-244). Same commands at different times; no check that they agree. The Swift context has no version/number. PolicyWitness.app/Contents/Resources/Evidence/provenance.json does not record the public contract (build_provenance.py:1560-1562).

### 1.4 Lines 12-13: "Direct Cargo and SwiftPM builds are unbound and refuse public requests and packaged peer checks"
Verdict: PARTIALLY SUPPORTED. True only when `PW_BUILD_CONTRACT` is absent from the environment and no compile flag is supplied. The compiled identity is caller-suppliable outside build.sh.
- Direct Cargo, OBSERVED json_contract.rs:11-20 with build.rs:20-28: any nonempty `PW_BUILD_CONTRACT` in the environment of a plain `cargo build` becomes the compiled contract, `release:vX.Y.Z` included. Nothing validates it. The suite accommodates this: tests/suites/integration/run.sh:15 runs `env -u PW_BUILD_CONTRACT cargo test`. The script docstring "never accept a caller-supplied identity" is true of the script (and tested), not of the Rust binary. HYPOTHESIS experiment: `PW_BUILD_CONTRACT=release:v9.9.9 cargo build` into a scratch target dir, then `--version`.
- Direct SwiftPM, OBSERVED: Package.swift defines no flag, so the result is `"unbound"`. With `-Xswiftc -DPW_UNIT_TEST_CONTEXT` it is `"test:policy-witness"` (PWRunnerAPI.swift:157-160; used at tests/suites/runner_unit/run.sh:32), and that build admits requests asserting that string, because PWRunnerRequest.swift:121 refuses only `"unbound"`. The package builds a library and a test executable, not the service or client.
- Paths the sentence does not mention, OBSERVED: a direct `meson setup`/`compile` outside build.sh produces bound Swift binaries. Direct `swiftc -D PW_PACKAGED_BUILD` with a hand-written `PWBuildContext.swift` yields any identity; tests/lib/build_context.py:32-37 does this for fixtures, with users in tests/fixtures/worker_wait/host_stamps.py:435, tests/suites/witness_contract/opt_in/mutations.py:122 and tests/suites/runner_byoxpc/opt_in/reservation_controls.py:147, 234.
- `unbound` is defined at json_contract.rs:14, 19 and PWRunnerAPI.swift:162.
- Refusal sites, OBSERVED.
  - Rust, with production callers:
    - controller/src/request_patch.rs:75-85 (called at run_flow.rs:602)
    - controller/src/run_flow.rs:96-99 (reply producer)
    - controller/src/porcelain.rs:218 (frame producer; via runner_client.rs:706, 743-746)
    - controller/src/policy_check.rs:51 (helper envelope)
    - controller/src/runner_client.rs:262-264 and 718
    - controller/src/runner_manager.rs:20-27 (called at runner_commands.rs:261, 366, 628 and runner_select.rs:480)
  - Swift:
    - runner/Sources/PWRunnerCore/PWRunnerRequest.swift:121
    - runner/Sources/PWRunnerCore/PWRunnerService.swift:297 (reservation)
    - runner/Clients/PWRunnerClient/PWRunnerClientSession.swift:209 (control reply)
  - Python readers: tests/lib/porcelain.py:184, runner_client_capture.py:129, document_versions.py:11, build_context.py:14.
  - No `unbound` guard: PWRunnerReply.swift:243 (`validateForReporting`) and ActorEquipment.swift:129. An unbound host fails earlier at request decode and reservation.
- Tests, OBSERVED:
  - cli_contract.rs:126-149 (default): a real plain-Cargo binary reports `build.contract == "unbound"`; a request asserting `"unbound"` exits 1 with `unsupported_contract`, `expected_contract: "unbound"` and a null `runner_client`.
  - request_patch.rs:241 (unit): `validate_contract(…, "unbound")` is an error.
  - tests/suites/runner_outcome_bad_request/opt_in/same_shape_contract.py:67-83 (opt-in, `default: false`): plain SwiftPM is `unbound` and refuses a request.
  - The `expected == "unbound"` branches at run_flow.rs:97, porcelain.rs:218, policy_check.rs:51, runner_client.rs:264/718 and runner_manager.rs:21 are not exercised with an unbound expectation, because `BUILD_CONTRACT` is `test:policy-witness` under `cfg(test)`. run_flow.rs:1645 and runner_select.rs:1291 test `"unbound"` as a foreign peer value. So "refuse … packaged peer checks" by an unbound build rests on code reading, with no executing test found.

### 1.5 Lines 14-15, 438-440: `--version`, `build.contract`, `PWContract` "report the compiled identity"; "Describe and commit remain provenance, not admission keys"; five `build.*` fields
Verdict: SUPPORTED, with two notes.
- OBSERVED controller/src/cli.rs:43-49: `--version` prints a `version` envelope with `data.contract = BUILD_CONTRACT`. json_contract.rs:66-82: `BuildStamp` has exactly commit, contract, describe, number, version, each from `option_env!` (default `"unknown"`).
- Note 1: `PWContract` is the build script's shell value, equal to the compiled value by construction and by the tests in 1.3, not a readback.
- Note 2: OBSERVED no Rust or Swift production code compares describe or commit; `PWProducer` only carries them (PWRunnerAPI.swift:169-177). The release tooling does gate on them: tests/lib/release_archive.py:184-187 requires `PWBuildCommit` to equal the tag's commit and `PWBuildDescribe` to equal the tag; also release_runs.py:204 and historical_release_storage.py:70. Line 15 is correct for request/reply/peer admission and not for release-archive admission.
- HYPOTHESIS: in a source copy nested inside another repository, build.sh:243-244 and build_contract.py:113-114 run `git -C root describe/rev-parse` with no toplevel check, so describe/commit could name the enclosing repository. Experiment: run the script with `--swift-stdout` in such a copy.

## PART 2: internal host/worker identity

### 2.1 Lines 382-390: "exact SHA-256 source identity… no worker ABI ordinal or compatibility negotiation… The build checks the C, Swift and test copies before compilation and again before signing, and never writes them… Direct source-test builds regenerate the same way"
Verdict: SUPPORTED except the last sentence, which is UNSUPPORTED as a mechanism.
- OBSERVED build.sh:233-234 (`--check`, before Cargo and Meson) and 686 (before signing). build.sh:687-689 additionally runs the built worker's `--version` and compares `abi_identity=` with the generated value (build_provenance.py:1493-1506; worker at pw_probe_runner.c:1278-1284). `--check` writes nothing (generate_worker_identity.py:85-90). The three copies are TARGETS (29-30): pw_probe_runner_abi.h:47-50, CWorker.swift:51-54, tests/lib/contract.py:3-5.
- No ordinal remains (abi.h:45-50). INFERRED from `git show 352c510a`: `PW_PROBE_RUNNER_ABI_VERSION 7u` was replaced.
- Tests, OBSERVED:
  - tests/suites/preflight/check_build_entry.py:106-114 (default `build_entry_controls`): a stale contract.py refuses with the regeneration command.
  - build_refusals.py:1630-1648 `stale_identity_presign` and 1651-1668 `worker_identity_mismatch` (opt-in, through the unchanged build.sh; the stand-in tests/fixtures/build_refusals/wrong_worker.c reports 64 zeros).
  - build_contracts.py:56-176: relocation, idempotence, per-input sensitivity, stale-copy repair, symlink refusal, missing marker.
  - tests/suites/runner_abi_layout/run.sh:169-171: compiled C identity equals the Swift text equals contract.py.
  - smoke/pw_specimen_smoke.sh:77-81: live `worker_evidence.abi_identity` equals contract.py.
- "Direct source-test builds regenerate the same way": OBSERVED nothing regenerates automatically. Package.swift has no plugin; tests/suites/runner_unit/run.sh neither runs nor checks the generator. The only automated regeneration outside the generator's own tests is opt-in same_shape_contract.py:102, in a disposable worktree after it edits the worker. `git show 352c510a -- docs/CONTRACT.md` shows the sentence began as "direct source-test builds can regenerate with the same command". The present-tense wording reads as automatic regeneration; no other file in the tree uses the phrase.

### 2.2 Lines 392-404: digest scope; symlinks; Ninja dependency log
Verdict: SUPPORTED, with a scope note.
- OBSERVED the prose matches generate_worker_identity.py:26-28 and 43 exactly: `.c/.h/.swift` under controller/tools/pw_probe_runner and runner/Sources, plus the generator, docs/source_identity.py, build.sh, meson.build, meson.options, runner/Package.swift. Length framing at 52-55; generated-region exclusion at 49-51; symlink refusal at source_identity.py:10-14, 20-21.
- Ninja check: OBSERVED tests/lib/native_sources.py:160-215, invoked at build.sh:535. `IDENTITY_TARGETS = ('pw-probe-runner', 'PWCWorkerShim')`. "The shim" is the static library from runner/Sources/PWCWorkerShim/PWCWorkerShim.c (meson.build:101-102). Each recorded dependency must be a digest input, or lie under `SDKROOT`, `DEVELOPER_DIR` or `xcode-select -p` (172-181).
- The check covers the C worker and shim only. Swift host sources get a membership check (218-230), not a consumed-file closure. The validator is excluded by design (docstring 25-26). The prose says "the worker and the shim", which is accurate.
- Tests, OBSERVED tests/suites/preflight/check_native_sources.py:40-80 (default `native_source_controls`, real Meson/Ninja, `xpc=false`): substituted worker source, symlinked include, relative escape to controller/src/escape.h and absolute escape are each refused by name. INFERRED: with `xpc=false` the shim's closure is not exercised by this default control.
- Scope notes:
  - OBSERVED runner/Services/PWRunner/main.swift (host entry point, 23 lines, compiled into `PWRunner` at meson.build:163) is outside the worker identity; it is inside the public contract.
  - "Discovery includes new helpers automatically" holds for `.c/.h/.swift` only. A consumed worker or shim file with another suffix would be caught by the closure check, not discovered.

### 2.3 Lines 406-414: header layout, worker checks, exit 4, ordinal-era workers, host checks, `abi_identity`
(a) "fixed bootstrap magic at byte 0 and 32 identity bytes at byte 64". SUPPORTED.
- OBSERVED abi.h:45-46, 256, 269 and `_Static_assert`s at 290-293. Swift mirror CWorker.swift:56-57, 88-89 holds constants only, with no compile-time assertion.
- Test: runner_abi_layout compiles printer.c:103-104 against the header and compares with constants parsed from the Swift source text and the golden tests/fixtures/contract/abi_layout.txt:64-65. The Swift side is read as text, not compiled.

(b) "The worker checks the mapped region's size and these fields before reading policy input, publishing evidence, or using layout-dependent fields. An identity or magic mismatch exits with code 4 and no ready/applied/done publication." SUPPORTED.
- OBSERVED pw_probe_runner.c main: `--version` (1278), `parse_args`, `pw_clock_start` (1299), `map_region` (1301; `fstat` size below `PW_SHM_REGION_BYTES` returns NULL, exit 3, at 342-361), then the magic/identity comparison returning 4 (1305-1311). The first shared write, `pw_progress`, is at 1319; the `prepared` check at 1320; policy handling starts after 1399.
- A too-small region exits 3, not 4. No test of the size refusal was found in tests/suites/runner_c_worker_harness or runner/Tests; the harness always sizes the region fully (harness.c:630).
- Tests, OBSERVED tests/suites/runner_c_worker_harness/run.sh:75-101 and 498, case `abi_mismatch_refused` (default; requires app, clang, worker). It runs the real bundled worker (run.sh:12).
  - Scenario `abi_mismatch` (harness.c:709-710 flips the last identity byte): exit_code 4, no signal, applied/done/ready byte false, no SIGKILL, `failure_published == 0`, no slot completed.
  - Scenario `abi_magic_mismatch` (harness.c:711-712, magic = 7 with a correct identity): same assertions.
  - Neither asserts that policy bytes were left unread.

(c) "The bootstrap magic also makes ordinal-era workers refuse the header." NOT DETERMINED by current code or tests; INFERRED from history.
- `git show 352c510a` shows the previous worker compared `hdr->abi_version` (first header word) with `PW_PROBE_RUNNER_ABI_VERSION 7u`; the magic `0x50574944` now occupies that word.
- The existing control tests the converse: the current worker refusing an ordinal-style header. No test runs an ordinal-era worker binary.

(d) "The host checks the identity before decoding worker evidence and before releasing attempts. These checks do not assert that a child validated the header." SUPPORTED, in a narrower sense than the words suggest.
- OBSERVED the host writes magic and identity itself before spawn (ActorSession.swift:137-141). `workerIdentityMatches` (CWorker.swift:584-588) rereads those bytes from the shared mapping and compares them with the host's compiled constants. It can establish only that the header was not altered after the host wrote it; it says nothing about which worker ran. The document's own disclaimer matches.
- Production call sites:
  - `decodeWorkerEvidence` (CWorker.swift:591; used at ActorSession.swift:639, 747)
  - `decodeAuthoritySetup` (AuthoritySetupRuntime.swift:58)
  - ordinary-form arrival, collection and release gate (CWorker.swift:1167-1171, release at 1213)
  - actor setup disposition (ActorScheduler.swift:284-285)
- In the actor form the check is at setup only; the per-visit release at ActorScheduler.swift:425-429 does not recheck it.
- `collectOutput` (ActorSession.swift:625-700) reads applied, done, phase and slot publications without an identity gate. Only the `worker_evidence` record and the authority-setup decode are gated. "Worker evidence" must be read as that record.
- Tests, OBSERVED:
  - runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift:258-262 (constructed memory, no worker): an identity bit flip or magic 7 gives nil.
  - tests/suites/witness_contract/check_diagnostic_transport.py:64-72 (default, `unfamiliar_diagnostic_transport`; real CLI and host, fixture worker via `_test_overrides.worker_executable_path`): mode `transport_incompatible`, where the fixture child flips the header identity byte (tests/fixtures/worker_lifecycle/worker.c:362), produces no public `worker_evidence`.
  - OrderingTests.swift:361-366: a fixture worker built with `PW_MISMATCHED_IDENTITY` exits 92 (the fixture's own code) and the host neither applies nor releases. This is a stand-in worker, not the production binary.
  - No test was found that isolates the gates at CWorker.swift:1170 or ActorScheduler.swift:285.

(e) "`runner_subprocess.worker_evidence.abi_identity` records the host-selected identity, including when no worker publication exists". SUPPORTED, path incomplete.
- OBSERVED CWorker.swift:643 fills `abi_identity` from the host's compiled constant, never from shared memory.
- Schema: docs/porcelain.json:3989 and 4972; projected as hex at controller/src/porcelain_records.rs:4651.
- The public path is `data.runner_result.runner_subprocess.worker_evidence.abi_identity`. The actor form uses `actors[].subprocess.worker_evidence.abi_identity` (tests/fixtures/contract/response_shape.json:274-275, 908-909), which the sentence does not name.
- The record is absent when the header no longer matches or no child was spawned (porcelain_records.rs:3844 omits it when None).
- Tests: smoke:77-81; check_diagnostic_transport.py:73 (64-character string with `failure_state` absent/incomplete/invalid); tests/lib/lifecycle_oracle.py:311.

### 2.4 Lines 416-425: limits disclaimers
Verdict: SUPPORTED. The named mechanisms exist:
- Layout: abi.h `_Static_assert`s and the runner_abi_layout suite (C compiled, Swift parsed as text).
- Signed artifact provenance: tests/build-evidence.py, tests/lib/build_provenance.py, tests/lib/signer_check.py, tests/build_equipment.py; preflight `codesign.preflight`.
- Lifecycle/order: runner_c_worker_harness `proceed_*` cases, OrderingTests.swift, `witness_contract/order_barrier_mutations`.
- "The hash is not a security authentication mechanism" is consistent with 2.3(d).
- Not described in this section, OBSERVED: the authority region carries a second magic and identity at offsets 0 and 4 (AuthorityCustody.swift:32-33, 181-183; worker check at pw_probe_runner.c:725-726), and the equipment inventory carries `worker_identity`, checked at ActorEquipment.swift:130.

### 2.5 Line 171: "The worker ABI identity remains independent of the public build identity"
Verdict: PARTIALLY SUPPORTED. Independent in computation and use; not independent in inputs.
- Independent, OBSERVED: separate scripts and domain prefixes (generate_worker_identity.py:46; build_contract.py:74). Neither digest takes the other's value as input: docs/build_contract.py and the generated PWBuildContext.swift are not worker-identity inputs. Separate check sites (shared header vs request/reply/reservation). A public-contract change can leave the worker identity unchanged (controller/src, runner/Clients, runner/Services, augments, plists).
- Not independent, OBSERVED: every worker-identity input except docs/generate_worker_identity.py is also a public-contract input. The public digest does not exclude the generated identity regions in abi.h and CWorker.swift. INFERRED: in any tree build.sh accepts, a changed worker identity implies a changed development contract, because the regenerated copies are public-scope bytes. The comment at build_refusals.py:1633-1634 reflects this coupling. Both identities sit in worker-equipment.json and are checked together (ActorEquipment.swift:129-130).

## SUMMARY

Discrepancies:
1. Lines 12-13: a direct Cargo build is unbound only if `PW_BUILD_CONTRACT` is absent from the environment; otherwise the binary reports whatever string was supplied, including `release:…`. A SwiftPM build with `-DPW_UNIT_TEST_CONTEXT` is `test:policy-witness`. Direct Meson is bound. (1.4)
2. Lines 8-9: a clean tree with two annotated release tags produces no build, not a development build. (1.1)
3. Line 389: "Direct source-test builds regenerate the same way" has no implementing mechanism; regeneration is manual. (2.1)
4. Line 413: the field path omits the actor form `actors[].subprocess.worker_evidence.abi_identity`. (2.3e)
5. Out of CONTRACT.md but encountered: tests/fixtures/diagnostic_transport/README.md:32 says `transport_incompatible` "changes the version word to 7" while worker.c:362 flips an identity byte; build.sh:488-490 says later builds use "meson configure" while the code runs `meson setup --reconfigure` (512).

Places a competent reader could reach a false conclusion:
- "The public contract is the release" plus line 100 suggests equal contracts mean equal binaries. `PW_INSPECTION`, `BUILD_XPC`, caller `RUSTFLAGS`, toolchain and SDK vary under one contract, with no disclaimer comparable to 416-420. (1.2)
- "report the compiled identity" suggests `PWContract` is read from binaries; it is a build-script stamp. (1.3, 1.5)
- "Describe and commit … not admission keys": release archiving does compare them. (1.5)
- "before decoding worker evidence": slot, applied, done and phase publications are decoded without the identity gate. (2.3d)
- "ordinal-era workers refuse the header": the test of that name checks the converse. (2.3c)
- "Git index flags cannot hide edited inputs" applies to scoped paths only. (1.1)

Statements stronger than the code:
- "Every shipped-source change changes a development contract" holds for source files; build variants and flags change shipped bytes without changing it.
- "refuse … packaged peer checks" for unbound builds has code at every site but no test that runs those branches with an unbound expectation; the SwiftPM request control is opt-in.
- The public contract's pre-sign guard is tested by extracting its text, not through the build; no build step asks binaries for their public contract.

Distinctions the document requires that the code does not enforce:
- Packaged vs direct build as the boundary for a bound identity: Rust takes an environment variable and Swift a compile flag plus a source file; neither verifies that build.sh produced the value.
- "Exactly one annotated tag" is enforced; "clean tree" beyond scoped paths is `git status`, not byte comparison.

Correct and well supported:
- Release derivation rules, including annotated-only, dirty-tree and assume-unchanged handling (code plus default tests).
- Path-and-content length-framed digest, with equal results for Git checkouts and source copies.
- One shell value feeding Rust and both plists, with the Swift value checked against it, and a pre-sign recompute.
- The five `build.*` fields and `--version` output.
- No describe/commit comparison in Rust or Swift admission.
- Worker-identity digest scope prose matching the generator exactly.
- Checks before compilation and before signing, with no writes, plus the built-worker self-report.
- The Ninja closure check for the worker (default control) and for the shim (code).
- Magic at byte 0 and identity at byte 64 (static asserts plus the layout suite).
- Worker ordering, exit 4 and absence of publication, tested against the real bundled worker.
- The host recording its own compiled identity in `worker_evidence.abi_identity`.
- The disclaimers at lines 412-420.
````

### Pass 5: read first-hand by the report writer at the time

These readings were made to check the return before the report was written. They are the report writer's own and are not part of the return.

- The worker's startup order: `controller/tools/pw_probe_runner/pw_probe_runner.c:1296-1322`.
- The fallback build context: `runner/Sources/PWRunnerCore/PWRunnerAPI.swift:152-178`.
- The build knobs and the two computations of the contract: `build.sh:130-138`, `:218-256`, `:676-690`.
- That `tests/suites/runner_unit/run.sh` and `runner/Package.swift` do not mention the worker-identity generator.
- The host identity comparison and header write: `CWorker.swift:582-594`, `ActorSession.swift:134-142`.
- Release archiving compares describe and commit: `tests/lib/release_archive.py:180-188`.
- The identity scope: the author enumerated the 105 scoped files and the two tracked files outside the suffix list independently of this pass.

### Pass 5: now known to be wrong, and other notes

- Nothing in this return is known to be wrong.
