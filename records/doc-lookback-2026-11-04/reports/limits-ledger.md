# LIMITS reader audit ledger — lookback-ea64218b

Read-only source review; assigned report outputs only. All findings are provisional documentary findings. No implementation, test source, manifest, generator, retained test evidence, history, external source, or native trial was inspected. A citation is navigation, never verification. “Retain” means keep the entry in scope with no identified documentary defect, not proven correct. “Question” means a specific documentary ambiguity or verification dependency is recorded.

## Exposure and checkpoints

- L0: only `packets/limits-onramp.md` and `packets/actor-example.json`; actor/action/reference inventory, no result evidence.
- L1: same sources plus coordinator scenario; tentative totals/UTF-8 arithmetic and missing timing/evidence semantics, before documentation.
- L2 initial task: complete `docs/LIMITS.md` only. Exact-fit action/actor counts, extra-action refusal, UTF-8 ID boundary, independent actor budgets and unknown submission after truncated capture. Q1 phase-record contradiction and Q3 unqualified issuance ordering were identified unprompted here.
- L3 prompted checkpoint: same sources; expanded Q1/Q3 and identified Q2 admission-row form scoping. No new sources.
- Stage 2B audit: `records/doc-lookback-2026-11-04/BASELINE.md`; complete LIMITS revisited mechanically for inventory; linked `docs/PolicyWitness.md` sections listed below. Q4–Q12 and omission hypotheses below are audit-only findings, not retrospectively attributed to initial task.
- Guide exposure: a heading/keyword search (`actor`, `admission_refused`, `one-shot`, `quiescen`, `unavailable`) printed matching lines throughout guide, including duplicated Limits and output sections. Detailed reads: Top-level shape and Ordered phases (147–226); Two request forms through What can go wrong (422–541); What acceptance establishes / Correcting a refused request (612–650); Compiled-object receipt (681–718); Receiver evidence (1473–1544); What PolicyWitness understands / filter and attempt sections (2115–2243). No further linked documents opened.
- Guide dependencies: form/issuance distinction and typed ownership (422–470) resolve intended scope, not actual implementation; authority movement/lifetime (472–541) grounds Q4 and missing-budget questions; accepted-input rules (147–226, 612–650) ground omission hypotheses; receipt prerequisites (681–718) ground optional-evidence omissions; receiver evidence (1473–1544) strengthens truncated-capture interpretation; supported attempts/filters (2115–2243) ground finite capability restrictions. These are documentary statements only.
- BASELINE says actor issue occurs inside issuing actor and declaration issuance remains preparatory; this corroborates intended distinction after initial checkpoints, without verifying code.

## Findings and remaining questions

Q1 (initial): `phase_records` says extra records are unreachable publicly/under development, while actor admission, phase_publications and its own coverage describe 16 actor visits. Guide Ordered phases also says eight per specimen without a form qualifier. Neither newer-looking wording nor the brief proves implementation behavior. Need authoritative form admission and public boundary evidence.

Q2 (prompted): phase_count, extension declaration/consume/release/reference rows need an explicit scope selection rule. Actor-specific rows strongly suggest intended separate limits, corroborated by guide Two request forms. Literal whole-specimen one-consume wording conflicts with actor repeated consumption and 64 handles. Verify scope and refusal classifications/order, not merely constants.

Q3 (initial): blanket pre-worker issuance statement and issuer wait describe declaration form in guide/brief; actor issue follows actor setup and schedule. This is a demonstrated scope gap. Actual call ordering remains unverified.

Q4 (audit): lifetime row says a worker reaching cutoff publishes/exits; guide says only at checked waits, and blocked native calls may prevent checking. Do not present 180 seconds as an unconditional preemption or cleanup deadline. Verify sampling boundaries and late/missing-publication interpretation.

Q5 (audit): generic and actor budgets coexist with incomplete cross-form explanation: setup caps policy/readiness waits, schedule excludes collection, shared lifetime includes all waits. Determine whether phase_collection_wait and actor_collection_allowance are the same pool in different paths, and which seam override applies. Do not add or multiply durations; fixed flag only changes client wait.

Q6 (audit): actor timing qualification prose claims finite one/three/eight-actor workloads with 25% headroom. It neither promises all admitted compositions finish nor supplies equipment/results here. Coverage rows primarily list value/path controls, so qualification itself needs its named evidence located and checked.

Q7 (audit): token storage/payload may be common, but resolved-path extension_channel is plausibly declaration-only. Confirm both geometry and public malformed/oversized statuses per form. Actor slot and declaration channel must not be conflated.

Q8 (audit): authority_slot_bytes supplies per-slot size and counts but not a whole-region allocation formula or answer-cell/header sizes. This is a potential omission of a resource bound, not proof of an undisclosed cap. Verify whether resource limits are derived only from admitted issues/deliveries and how setup failure is reported.

Q9 (audit): reply-size coverage explicitly counts actor components and mutually exclusive fields; premises abbreviate the derivation as a 256-step fixture. Need actual bound, actor receipt multiplication, capture overhead and array completeness verified. 260,046,848 equals 62 × 4,194,304 and exceeds 3 × 85,852,557 = 257,557,671, consistent with stated rounding; that arithmetic alone does not verify bound completeness. Retention cap is not memory cap.

Q10 (audit): per-worker diagnostic/capture bounds must be read with actor-indexed output. Optional receipt publication additionally requires apply/exit/identity/checksum conditions, not only size support. Guide adds these conditions; no implementation verification.

Q11 (audit): opening “every such limit” is broader than numeric inventory if read to include all PW restrictions that refuse compilable policy requests or reduce evidence. Missing-limit hypotheses below distinguish semantic capability restrictions from missing numerical caps. Narrow intent is plausible, but not explicitly established by opening.

Q12 (audit): first-failing-field interaction and premises enumerate legacy admission order without actor identifiers, ownership, actor capacities or mixed-form rules. Cannot predict precedence for a request failing both actor and generic checks from that enumeration. Need order evidence, not inference from table order.

## Initial expansion-task decision retained

8 actors, 16 actor phases, 32 issues, 64 transfers, 64 consumes, 64 releases and 32 ordinary pairs use 256 total slots. Actor-specific rows admit those maxima; 257 does not fit. Each ordinary pair counts once and each extension action once, with no extension query. Twenty-one 界 characters = 63 decoded UTF-8 bytes; adding x = 64 and exceeds step_id. All other admission conditions remain assumed. 480000 ms is one client wait, not each actor’s budget. No observed run was supplied. Truncated client capture is not parsed and leaves submission unknown; timeout alone establishes neither execution nor nonexecution. Earlier valid publications/collections can survive internal expiry; missing prediction is not missing attempt. If all 32 queries are sent, phase-specific validator allowances sum to at most 64 records and 524288 bytes, not 16 full-plan pools. This calculation does not promise records are produced or associated.

## Separate missing-limit search (hypotheses, not new verified limits)

The search followed admission → setup → serial visits/authority exchange → cleanup/publication → client retention, plus unchanged attempts/helper paths. It used the neutral brief and guide sections above; it did not search implementation or infer hidden constants.

| ID | Candidate restriction or missing bound | Documentary basis / consequence | Scope and verification question |
| --- | --- | --- | --- |
| M01 | Form exclusivity, schema versions, unknown fields/types | Guide Top-level shape and acceptance reject unsupported shape/version before execution | Both forms; decide whether opening promise includes semantic admission. No numeric cap inferred. |
| M02 | Minimum/nonempty schedule, unique identities, every actor owns a phase | Guide Ordered phases and Two request forms; empty action arrays legal | Actor/legacy; minima and uniqueness not fully inventoried as limits. Verify exact refusals and form combinations. |
| M03 | Typed reference ownership, producer-before-use, once-assigned names | Guide Operations and references | Actor; admission restrictions beyond capacity, repeated consumes with distinct handles legal. Verify diagnostic paths and precedence. |
| M04 | Authority-participating actor cannot exec, including recipient | Guide Operations and references | Actor; materially restricts otherwise admitted attempt kind, other actor may exec. Missing from LIMITS numeric tables; applicability under broad promise is a documentation question. |
| M05 | Supported extension family/authority only file read/read_write; no raw token/class/flags | Guide Supported families | Both forms; request capability refusal. Verify exact accepted fields and refusal, not platform capability. |
| M06 | Authority-region/custody allocation and mapping failures | Guide How authority moves / What can go wrong | Actor; host refuses launch or stops worker before release. Need full geometry/allocation derivation if inventory intends all resource bounds; no undisclosed numerical limit proven. |
| M07 | One-shot immutable issue/transfer slots, last-use erasure, no timeout reuse | Guide How authority moves and brief settlement repair | Actor lifetime/resource restriction; examine whether any additional wait/retained-resource budget exists. Never infer erase success after unknown quiescence. |
| M08 | Checked lifetime cutoff and unresolved termination | Guide What can go wrong plus brief unknown quiescence repair | Actor; native blocking may delay checks; no hard total cleanup/native-call limit documented. Verify absence as well as presence of a cap; no invented timeout. |
| M09 | Query representation cannot express extension class plus path | Guide What each observation establishes | Extension queries; unavailable expressive evidence distinct from byte capacity. LIMITS says events supply no queries but does not explain representational restriction. |
| M10 | Known prediction exclusions and path eligibility | Guide Filter kinds / Ordered phases | Four named operation/filter exclusions and fresh path eligibility reduce evidence without admission rejection. Determine intended completeness scope; verify exclusions from authoritative list/evidence. |
| M11 | Finite attempt/filter set; exec-only args; none filter accepts no value | Guide acceptance/filter/attempt sections | All forms; unsupported combinations refuse before child. Not all semantic restrictions listed in LIMITS. No new numeric limit inferred. |
| M12 | Compiled receipt nonce shape and publication prerequisites | Guide Correcting refusals / Compiled-object receipt | 32 lowercase hex nonce; requires opt-in, identity/checksum/exit/apply checks. Size alone insufficient; classify missing semantic/capture restrictions under opening promise. |
| M13 | Response/transport schema admission, lost envelopes, duplicate validator IDs | Guide Receiver evidence | Complete bytes can still be unusable; transport rejected/malformed/schema mismatch and duplicate-ID lack unique verdict. LIMITS has frame/byte bounds but not complete evidence-admission account. Verify limits inventory scope. |
| M14 | Total allocation/retention outside captured streams | LIMITS premises explicitly says buffers whole stream before retention; guide actor regions | No process-memory ceiling promised; investigate whether separate request, allocator, host-custody or reply-growth caps exist. Absence of documented cap is not proof of unbounded implementation. |
| M15 | Fresh file/sysctl observations and exec descendant boundaries | Guide Attempt kinds and LIMITS retained entries | Unaffected paths still in scope: discarded sysctl length/content, read prefix, open-only statuses, escaping descendants, blocking spawn. Existing entries cover many bounds; remaining representational omissions are hypotheses. |
| M16 | Diagnostic helper is separate from compilation/import resolution | LIMITS Diagnostic helpers and premises | Existing three helper bounds retained; confirm no additional actor fallback payload/selection ceiling introduced. No omission established. |
| M17 | Actor-indexed arrays, late setup, empty visits and transfer settlement | Brief plus guide How authority moves / What can go wrong | Verify reply maximum classification and bounded vocabulary/arrays cover repaired variants. Coverage says they do; citation alone is not verification. |

No exhaustive statement of implementation completeness is possible under reader-only permissions. The list records concrete documented restrictions and bounded search questions, not claims that implementation lacks limits or that every restriction belongs in a numeric table.

## Ledger conventions (handoff-quality revision)

The coordinator requested distinct meaning assessments rather than duplicated source statements. Each entry now retains its original combined wording once as **Source claim**, followed by separate counting, scope, enforcement and consequence assessments. This correction does not itself establish a defect in LIMITS. “Not stated” means the documentation does not supply the requested detail; “not applicable” means the field does not apply, such as enforcement of an explicitly informative bound. All implementation and evidence claims remain unverified. Qualifications remain in the preserved source claim, controls and coverage statements even where concise assessments abbreviate them. Cross-form applicability is not silently inferred.

Source quotations are blockquoted; assessment fields are bullets. Coverage text is documentary evidence claimed by the source, not evidence inspected. Markdown links copied from docs/LIMITS.md are rebased for this reports directory; locators identify the original document and line.

## Accounting

```json
{
  "limit_entries": 93,
  "coverage_rows": 93,
  "matched": 93,
  "unmatched_coverage": [],
  "prose_blocks": 27,
  "separate_field_revision": "93 separate counting/scope/enforcement/consequence assessments; complete source claim retained once per row."
}
```

### policy_source — [docs/LIMITS.md:61](../../../docs/LIMITS.md#L61)

**Source claim (documentary quotation):**

> Final SBPL source after augments. Imported file contents are not added to this count. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 262,143 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `policy.sbpl_source`
- **Counting rule:** Decoded UTF-8 bytes of final SBPL after augments; imported contents excluded.
- **Scope assessment:** Each final policy source; per-actor multiplication not explicitly stated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host worker-string admission before compilation, per Premises; exact actor gate unstated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:255](../../../docs/LIMITS.md#L255)
- **implementation_navigation:** [`PW_SHM_POLICY_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### probe_steps — [docs/LIMITS.md:62](../../../docs/LIMITS.md#L62)

**Source claim (documentary quotation):**

> Total ordinary pairs and extension lifecycle actions across the complete plan. Lifecycle actions occupy slots but supply no query; phases do not multiply this cap. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 256 items
- **Unit:** items
- **Refusal field / location:** `probe_plan` or `phases.actions`
- **Counting rule:** One item per ordinary pair or extension action; lifecycle action supplies no query.
- **Scope assessment:** Complete plan across phases; actor issues share cap according to coverage. No phase multiplier.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host plan-count admission before children; actor-form precedence not specified.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:256](../../../docs/LIMITS.md#L256)
- **implementation_navigation:** [`PW_SHM_MAX_STEPS`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### policy_parameters — [docs/LIMITS.md:63](../../../docs/LIMITS.md#L63)

**Source claim (documentary quotation):**

> Entries in `policy.params`. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 1,024 items
- **Unit:** items
- **Refusal field / location:** `policy.params`
- **Counting rule:** Number of entries in policy.params.
- **Scope assessment:** Each policy.params dictionary; actor applicability not explicitly restated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host plan/parameter-count admission per Premises; exact actor gate unstated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:257](../../../docs/LIMITS.md#L257)
- **implementation_navigation:** [`PW_SHM_MAX_PARAMS`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### step_id — [docs/LIMITS.md:64](../../../docs/LIMITS.md#L64)

**Source claim (documentary quotation):**

> Each `step_id`. A refused ID is identified by `step_index` and is never echoed. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `step_id`, with `step_index`
- **Counting rule:** Decoded UTF-8 payload bytes in step_id.
- **Scope assessment:** Each step ID individually; no form qualifier in row.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host worker-string admission; refusal identifies step_index.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields bad_request/admission_failure, identifies step_index and never echoes refused ID.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:258](../../../docs/LIMITS.md#L258)
- **implementation_navigation:** [`PW_SHM_STEP_ID_MAX`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### attempt_target — [docs/LIMITS.md:65](../../../docs/LIMITS.md#L65)

**Source claim (documentary quotation):**

> Each attempt target (path, service or sysctl name). For exec, this is also argument zero. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 511 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `target`, with `step_id` and `step_index`
- **Counting rule:** Decoded UTF-8 target bytes; exec target is argv[0].
- **Scope assessment:** Each attempt target, including exec argv[0]; separate from query target.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host worker-string admission per Premises.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:259](../../../docs/LIMITS.md#L259)
- **implementation_navigation:** [`PW_SHM_TARGET_MAX`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### exec_arguments — [docs/LIMITS.md:66](../../../docs/LIMITS.md#L66)

**Source claim (documentary quotation):**

> Arguments supplied in `attempt.args`; the exec target is the additional argument zero. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 15 items
- **Unit:** items
- **Refusal field / location:** `args` with unit `items`, with `step_id` and `step_index`
- **Counting rule:** Number of supplied attempt.args entries, excluding target/argv[0].
- **Scope assessment:** Each exec attempt's supplied argument array; argv[0] additional.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host exec-argument admission under worker strings in Interactions.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:260](../../../docs/LIMITS.md#L260)
- **implementation_navigation:** [`PW_SHM_MAX_ARGV`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### exec_argument — [docs/LIMITS.md:67](../../../docs/LIMITS.md#L67)

**Source claim (documentary quotation):**

> Each supplied exec argument; the target has its own larger limit. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 127 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `args` with unit `utf8_bytes`, with `index`, `step_id` and `step_index`
- **Counting rule:** Decoded UTF-8 bytes in one supplied exec argument.
- **Scope assessment:** Each supplied exec argument; argv[0] uses separate target limit.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host exec-argument string admission; offending index/step identified.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:261](../../../docs/LIMITS.md#L261)
- **implementation_navigation:** [`PW_SHM_ARGV_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### parameter_key — [docs/LIMITS.md:68](../../../docs/LIMITS.md#L68)

**Source claim (documentary quotation):**

> Each parameter key. A refused key is identified by field and byte count and is never echoed. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 127 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `key`
- **Counting rule:** Decoded UTF-8 bytes in one parameter key.
- **Scope assessment:** Each policy parameter key; actor application not explicitly restated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host worker-string parameter-key admission per Premises.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields bad_request/admission_failure; field and byte count identify refused key without echo.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:262](../../../docs/LIMITS.md#L262)
- **implementation_navigation:** [`PW_SHM_PARAM_KEY_MAX`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### parameter_value — [docs/LIMITS.md:69](../../../docs/LIMITS.md#L69)

**Source claim (documentary quotation):**

> Each parameter value. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 383 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `value`, with `parameter_key`
- **Counting rule:** Decoded UTF-8 bytes in one parameter value.
- **Scope assessment:** Each policy parameter value; actor application not explicitly restated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host worker-string parameter-value admission per Premises.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:263](../../../docs/LIMITS.md#L263)
- **implementation_navigation:** [`PW_SHM_PARAM_VALUE_MAX`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI.


### query_operation — [docs/LIMITS.md:70](../../../docs/LIMITS.md#L70)

**Source claim (documentary quotation):**

> Each `sandbox_check.operation`, also echoed per step in the reply. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 127 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `sandbox_check.operation`, with `step_id` and `step_index`
- **Counting rule:** Decoded UTF-8 bytes in sandbox_check.operation.
- **Scope assessment:** Each query operation string; echoed per step.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host queryAdmissionFailure per Premises; coverage says string never enters shared memory.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields bad_request/admission_failure; accepted operation also echoed per step.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:264](../../../docs/LIMITS.md#L264)
- **implementation_navigation:** [`sandboxCheckOperationMaxBytes`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift); [`queryAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)
Behavioral claim:

> Host-only: the string goes to the validator line and is echoed per step in the reply; it never enters shared memory. At-limit, over-limit and multibyte admission controls through the CLI; constructed orchestrator controls refuse before any process work and cover every filter kind.


### query_filter_value — [docs/LIMITS.md:71](../../../docs/LIMITS.md#L71)

**Source claim (documentary quotation):**

> Each `sandbox_check.filter.value` when present, including for `none` and unrecognized filter kinds. The query value and attempt target are counted separately, even when they name different paths. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 511 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `sandbox_check.filter.value`, with `step_id` and `step_index`
- **Counting rule:** Decoded UTF-8 bytes in present filter.value; separate measurement from attempt target.
- **Scope assessment:** Each present filter value, including none/unknown kinds; separate from attempt target.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host query-field admission per Premises.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:265](../../../docs/LIMITS.md#L265)
- **implementation_navigation:** [`sandboxCheckFilterValueMaxBytes`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift); [`queryAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)
Behavioral claim:

> At-limit, over-limit and multibyte admission controls through the CLI; constructed orchestrator controls refuse before any process work and cover every filter kind.


### probe_plan_label — [docs/LIMITS.md:72](../../../docs/LIMITS.md#L72)

**Source claim (documentary quotation):**

> Each `sandbox_check.filter.kind`, `attempt.kind` and `attempt.action`. Unknown labels within the capacity still receive a meaning refusal. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 127 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `sandbox_check.filter.kind`, `attempt.kind` or `attempt.action`, with `step_id` and `step_index`
- **Counting rule:** Decoded UTF-8 bytes in each filter.kind, attempt.kind or attempt.action separately.
- **Scope assessment:** Each of three named labels separately, not combined.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host query/label capacity admission before meaning validation.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields bad_request/admission_failure; within-capacity unknown labels still receive meaning refusal.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:266](../../../docs/LIMITS.md#L266)
- **implementation_navigation:** [`probePlanLabelMaxBytes`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift); [`queryAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)
Behavioral claim:

> Exact, over-limit and multibyte boundaries through the CLI; 256-step oversized-label regressions require a small refusal and unchanged write targets.


### specimen_id — [docs/LIMITS.md:73](../../../docs/LIMITS.md#L73)

**Source claim (documentary quotation):**

> The `specimen_id` string. Echoed once per reply; a refused ID is replaced by `<admission_refused>`. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 255 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `specimen_id`
- **Counting rule:** Decoded UTF-8 bytes in specimen_id.
- **Scope assessment:** One request-level specimen ID, echoed once.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Top-level metadata admission, first group in stated ordering.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields bad_request/admission_failure; refused ID replaced by <admission_refused>.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:267](../../../docs/LIMITS.md#L267)
- **implementation_navigation:** [`specimenIdMaxBytes`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift); [`requestAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)
Behavioral claim:

> Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; the refusal reply never contains the refused string.


### request_label — [docs/LIMITS.md:74](../../../docs/LIMITS.md#L74)

**Source claim (documentary quotation):**

> Each of `run_kind` and `policy.format`. A refused `run_kind` is omitted and a refused format reads `unknown`. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `run_kind` or `policy.format`
- **Counting rule:** Decoded UTF-8 bytes in each run_kind or policy.format.
- **Scope assessment:** Each run_kind or policy.format; per-actor policy.format applicability not restated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Top-level metadata admission before semantic validation.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields bad_request/admission_failure; refused run_kind omitted and format echoed as unknown.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:268](../../../docs/LIMITS.md#L268)
- **implementation_navigation:** [`requestLabelMaxBytes`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift); [`requestAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)
Behavioral claim:

> Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; an at-limit format passes capacity admission and fails meaning validation as bad_request.


### test_override_path — [docs/LIMITS.md:75](../../../docs/LIMITS.md#L75)

**Source claim (documentary quotation):**

> Each executable override path. Every path that fails byte or NUL admission is omitted from a refusal echo, even when another field is refused first. Excess returns `bad_request` with `admission_failure`.

- **Category:** Specimen admission
- **Value / derivation:** 1,023 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `_test_overrides.worker_executable_path`, `validator_executable_path` or `issuer_executable_path`
- **Counting rule:** Each executable override path.
- **Scope assessment:** Each worker/validator/issuer override; invalid echoes sanitized independently.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Executable-override admission before plan/parameter counts per Premises.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `bad_request` with `admission_failure`.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:269](../../../docs/LIMITS.md#L269)
- **implementation_navigation:** [`testOverridePathMaxBytes`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift); [`requestAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`admission`](../../../tests/suites/failure_boundaries/check.py); boundary (test): [`runQueryAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/QueryAdmissionTests.swift)
Behavioral claim:

> Override paths are mirrored in test_overrides and named in dlopen and spawn diagnostics; each invalid path is independently dropped from a refusal mirror. Exact, over-limit and multibyte boundaries through the CLI and in constructed controls; at-limit nonexistent paths pass admission and reach their own seam failures.


### phase_count — [docs/LIMITS.md:76](../../../docs/LIMITS.md#L76)

**Source claim (documentary quotation):**

> Explicit phases in one request; probe_plan normalizes to one phase. Excess returns admission_failure before any child.

- **Category:** Specimen admission
- **Value / derivation:** 8 items
- **Unit:** items
- **Refusal field / location:** `phases`
- **Counting rule:** Number of explicit phases; probe_plan normalizes to one.
- **Scope assessment:** Ambiguous: row says one request, coverage calls eight legacy/declaration; actor row allows 16.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Request phase-count admission before any child; form dispatch unresolved.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns admission_failure before any child.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q1: Unqualified eight-phase request wording conflicts in scope with explicit actor_phases=16; coverage calls eight legacy/declaration.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q1: Unqualified eight-phase request wording conflicts in scope with explicit actor_phases=16; coverage calls eight legacy/declaration.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:306](../../../docs/LIMITS.md#L306)
- **implementation_navigation:** [`PWRunnerPhase`](../../../runner/Sources/PWRunnerCore/PWRunnerRequest.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift)
Behavioral claim:

> Explicit phases in one request; probe_plan normalizes to one phase. Excess returns admission_failure before any child.


### phase_id — [docs/LIMITS.md:77](../../../docs/LIMITS.md#L77)

**Source claim (documentary quotation):**

> UTF-8 payload bytes in each phase_id. NUL is refused independently. Excess returns admission_failure without echoing the refused identity.

- **Category:** Specimen admission
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `phase_id`
- **Counting rule:** Decoded UTF-8 payload bytes in phase_id; NUL independently checked.
- **Scope assessment:** Each phase identity; form qualifier absent.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Request phase-identity admission; exact actor gate/order not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess yields admission_failure without echoing identity; embedded NUL refused independently.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:307](../../../docs/LIMITS.md#L307)
- **implementation_navigation:** [`admissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift)
Behavioral claim:

> UTF-8 payload bytes in each phase_id. NUL is refused independently. Excess returns admission_failure without echoing the refused identity.


### extension_declarations — [docs/LIMITS.md:78](../../../docs/LIMITS.md#L78)

**Source claim (documentary quotation):**

> Across the complete specimen, including separate phases. Omitted actions are legal. Additional declarations return `admission_refused`.

- **Category:** Specimen admission
- **Value / derivation:** 1 item
- **Unit:** item
- **Refusal field / location:** `extensions`
- **Counting rule:** Number of extension declarations.
- **Scope assessment:** Whole specimen across phases; extensions field suggests declaration form, exclusion of actors not explicit.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Declaration-count admission before lifecycle strings per Interactions.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Additional declarations return admission_refused; omission of actions is legal.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q2: Declaration field suggests scope but whole-specimen wording does not state exclusion of actor form.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q2: Declaration field suggests scope but whole-specimen wording does not state exclusion of actor form.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:321](../../../docs/LIMITS.md#L321)
- **implementation_navigation:** [`PWExtensionLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerExtension.swift); [`extensionMeaningFailure`](../../../runner/Sources/PWRunnerCore/ProbeRunner.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Shared corpus through Swift admission, public CLI and direct XPC, including refused intent with no file effect.


### extension_consumes — [docs/LIMITS.md:79](../../../docs/LIMITS.md#L79)

**Source claim (documentary quotation):**

> Across the complete specimen, including separate phases. Omitted actions are legal. A repeated consume returns `repeated_consume`.

- **Category:** Specimen admission
- **Value / derivation:** 1 item
- **Unit:** item
- **Refusal field / location:** `phases.actions.extension`
- **Counting rule:** Number of consume actions, regardless of runtime success.
- **Scope assessment:** Ambiguous: whole specimen wording conflicts with separate actor_handles cap unless declaration-specific.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Request repetition refusal indicated; precise gate/order not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Repeated consume returns repeated_consume; omitted action legal. Actor-form applicability unresolved.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q2: One-consume cap lacks declaration-form qualifier; actor_handles admits 64 and repeated delivery consumption.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q2: One-consume cap lacks declaration-form qualifier; actor_handles admits 64 and repeated delivery consumption.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:322](../../../docs/LIMITS.md#L322)
- **implementation_navigation:** [`PWExtensionLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerExtension.swift); [`extensionMeaningFailure`](../../../runner/Sources/PWRunnerCore/ProbeRunner.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Shared corpus through Swift admission, public CLI and direct XPC, including refused intent with no file effect.


### extension_releases — [docs/LIMITS.md:80](../../../docs/LIMITS.md#L80)

**Source claim (documentary quotation):**

> Across the complete specimen, including separate phases. Omitted actions are legal. A repeated release returns `repeated_release`.

- **Category:** Specimen admission
- **Value / derivation:** 1 item
- **Unit:** item
- **Refusal field / location:** `phases.actions.extension`
- **Counting rule:** Number of release actions, regardless of runtime success.
- **Scope assessment:** Ambiguous: whole specimen wording conflicts with separate actor_releases cap unless declaration-specific.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Request repetition refusal indicated; precise gate/order not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Repeated release returns repeated_release; omitted action legal. Actor-form applicability unresolved.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q2: One-release cap lacks declaration-form qualifier; actor_releases admits 64 distinct handles.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q2: One-release cap lacks declaration-form qualifier; actor_releases admits 64 distinct handles.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:323](../../../docs/LIMITS.md#L323)
- **implementation_navigation:** [`PWExtensionLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerExtension.swift); [`extensionMeaningFailure`](../../../runner/Sources/PWRunnerCore/ProbeRunner.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Shared corpus through Swift admission, public CLI and direct XPC, including refused intent with no file effect.


### extension_reference — [docs/LIMITS.md:81](../../../docs/LIMITS.md#L81)

**Source claim (documentary quotation):**

> Each nonempty local token or handle reference; embedded NUL is refused. Excess returns `admission_refused`; references must also satisfy declaration and action order.

- **Category:** Specimen admission
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `extensions.token_ref` or `phases.actions.extension.token_ref` / `handle_ref`
- **Counting rule:** Decoded UTF-8 bytes in each nonempty local token or handle reference.
- **Scope assessment:** Each local token/handle reference; listed action paths do not explicitly exclude actor form.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Extension/lifecycle string admission per Premises; ownership/order check location unstated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused`; references must also satisfy declaration and action order.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q2: Mixed declaration/action paths do not delimit declaration versus actor references; actor_id separately covers actor reference types.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q2: Mixed declaration/action paths do not delimit declaration versus actor references; actor_id separately covers actor reference types.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:324](../../../docs/LIMITS.md#L324)
- **implementation_navigation:** [`PWExtensionLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerExtension.swift); [`requestAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Shared corpus through Swift admission, public CLI and direct XPC, including refused intent with no file effect.


### extension_target — [docs/LIMITS.md:82](../../../docs/LIMITS.md#L82)

**Source claim (documentary quotation):**

> Submitted target path, before host realpath preparation; excludes terminating NUL. This is separate from an ordinary attempt target. Excess or embedded NUL returns `admission_refused`. Resolution and metadata failures remain preparation evidence.

- **Category:** Specimen admission
- **Value / derivation:** 1,023 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `extensions.target`
- **Counting rule:** Submitted target UTF-8 bytes before host realpath; terminating NUL excluded.
- **Scope assessment:** extensions.target before realpath; guide identifies declaration path, row lacks form qualifier.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Declaration-string admission before host realpath preparation.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess or embedded NUL returns `admission_refused`. Resolution and metadata failures remain preparation evidence.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q3: Preparation/realpath is declaration-specific per linked guide; must not apply to actor issue targets.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q3: Preparation/realpath is declaration-specific per linked guide; must not apply to actor issue targets.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:325](../../../docs/LIMITS.md#L325)
- **implementation_navigation:** [`PWExtensionLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerExtension.swift); [`PW_EXTENSION_PATH_BYTES`](../../../controller/tools/pw_probe_runner/pw_extension_channel.h)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Shared corpus through Swift admission, public CLI and direct XPC, including refused intent with no file effect.


### actors — [docs/LIMITS.md:83](../../../docs/LIMITS.md#L83)

**Source claim (documentary quotation):**

> Actor objects in one actor-form request; every phase names one of them. Excess returns `admission_refused` before any child.

- **Category:** Specimen admission
- **Value / derivation:** 8 items
- **Unit:** items
- **Refusal field / location:** `actors`
- **Counting rule:** Number of actor objects.
- **Scope assessment:** One actor-form request; every phase names a declared actor.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Actor request admission explicitly before any child; detailed order unstated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused` before any child.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:326](../../../docs/LIMITS.md#L326)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> The actor form launches one fresh worker per actor; the shared corpus holds the exact and over-limit examples.


### actor_phases — [docs/LIMITS.md:84](../../../docs/LIMITS.md#L84)

**Source claim (documentary quotation):**

> Explicit phases in one actor-form request; each is one visit of its actor. Excess returns `admission_refused` before any child.

- **Category:** Specimen admission
- **Value / derivation:** 16 items
- **Unit:** items
- **Refusal field / location:** `phases`
- **Counting rule:** Number of phase objects, each representing one visit.
- **Scope assessment:** All phases of one actor-form request, not per actor.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Actor phase-count admission explicitly before any child.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused` before any child.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:327](../../../docs/LIMITS.md#L327)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Each actor's shared header holds a record for every phase it can be activated in; the legacy cap of eight phases is unchanged.


### actor_issues — [docs/LIMITS.md:85](../../../docs/LIMITS.md#L85)

**Source claim (documentary quotation):**

> Issue actions across the complete actor-form specimen; each assigns one token reference. Excess returns `admission_refused` before any child.

- **Category:** Specimen admission
- **Value / derivation:** 32 items
- **Unit:** items
- **Refusal field / location:** `phases[].actions[].extension`
- **Counting rule:** Number of issue actions, each assigning one token reference.
- **Scope assessment:** All issue actions across actor-form specimen, not per actor.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Actor issue-count admission explicitly before any child.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused` before any child.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:328](../../../docs/LIMITS.md#L328)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Issue outputs share the action capacity; the host allocates custody for admitted tokens only.


### actor_deliveries — [docs/LIMITS.md:86](../../../docs/LIMITS.md#L86)

**Source claim (documentary quotation):**

> Transfer actions across the complete actor-form specimen; each assigns one delivery reference. Excess returns `admission_refused` before any child.

- **Category:** Specimen admission
- **Value / derivation:** 64 items
- **Unit:** items
- **Refusal field / location:** `phases[].actions[].extension`
- **Counting rule:** Number of transfer actions, each assigning one delivery reference.
- **Scope assessment:** All transfers across actor-form specimen; coverage says self-transfer counts.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Actor transfer-count admission explicitly before any child.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused` before any child.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:329](../../../docs/LIMITS.md#L329)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Each delivery has one inbound slot in its recipient's authority region; a self-transfer counts.


### actor_handles — [docs/LIMITS.md:87](../../../docs/LIMITS.md#L87)

**Source claim (documentary quotation):**

> Consume actions across the complete actor-form specimen; each assigns one handle reference. Excess returns `admission_refused` before any child.

- **Category:** Specimen admission
- **Value / derivation:** 64 items
- **Unit:** items
- **Refusal field / location:** `phases[].actions[].extension`
- **Counting rule:** Number of consume actions, each assigning one handle reference.
- **Scope assessment:** All consumes across actor-form specimen; repeated delivery consumption uses distinct handles.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Actor consume-count admission explicitly before any child.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused` before any child.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:330](../../../docs/LIMITS.md#L330)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> Repeated consumption of one delivery assigns distinct handles; raw native handles are never identified by equality.


### actor_releases — [docs/LIMITS.md:88](../../../docs/LIMITS.md#L88)

**Source claim (documentary quotation):**

> Release actions across the complete actor-form specimen; at most one per handle. Excess returns `admission_refused` before any child.

- **Category:** Specimen admission
- **Value / derivation:** 64 items
- **Unit:** items
- **Refusal field / location:** `phases[].actions[].extension`
- **Counting rule:** Number of release actions; at most one per handle.
- **Scope assessment:** All releases across actor-form specimen; at most one per handle.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Actor release-count admission before children; coverage separately states repeated-handle refusal.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused` before any child.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:331](../../../docs/LIMITS.md#L331)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> A second release of a handle is refused at admission; a release still runs when its consume failed, and publishes unavailability.


### actor_id — [docs/LIMITS.md:89](../../../docs/LIMITS.md#L89)

**Source claim (documentary quotation):**

> Actor identifiers and token, delivery and handle references; nonempty, no NUL. Excess returns `admission_refused`; empty or duplicate identifiers are request refusals.

- **Category:** Specimen admission
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `actors[].actor_id`
- **Counting rule:** Decoded UTF-8 bytes per actor identifier or token/delivery/handle reference.
- **Scope assessment:** Actor identifiers and actor token/delivery/handle reference strings, despite narrower refusal-path label.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Request identity admission indicated; exact actor gate/order unstated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused`; empty or duplicate identifiers are request refusals.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:332](../../../docs/LIMITS.md#L332)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> The same bound as the legacy extension references, shared by every identifier the reply echoes.


### extension_issue_target — [docs/LIMITS.md:90](../../../docs/LIMITS.md#L90)

**Source claim (documentary quotation):**

> Absolute path an issue action submits; passed to the native call unchanged. Excess returns `admission_refused`; a relative target is a request refusal.

- **Category:** Specimen admission
- **Value / derivation:** 1,023 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** `phases[].actions[].extension.target`
- **Counting rule:** Decoded UTF-8 bytes of absolute submitted issue path.
- **Scope assessment:** Each actor issue action's submitted absolute target, unchanged at native call.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Request target admission before native call; precise gate unstated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess returns `admission_refused`; a relative target is a request refusal.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:333](../../../docs/LIMITS.md#L333)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`normalizeActorPlan`](../../../runner/Sources/PWRunnerCore/ActorPlan.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runRequestContractTests`](../../../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift); boundary (test): [`main`](../../../tests/suites/runner_outcome_bad_request/contract.py)
Behavioral claim:

> The exact submitted bytes reach the worker's slot and the native issue call; no canonicalization is applied.


### host_exit_delay — [docs/LIMITS.md:96](../../../docs/LIMITS.md#L96)

**Source claim (documentary quotation):**

> Delay scheduled once by the terminal execution or abandoned-reservation owner. The unsandboxed host schedules exit after the delay. An occupied host grants no further reservation; client acquisition can reconnect before submission.

- **Category:** Execution budgets
- **Value / derivation:** 50 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Scheduled delay after terminal execution or abandoned-reservation ownership.
- **Scope assessment:** Once per retiring host, terminal execution or abandoned reservation; not per action.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host schedules exit; actual scheduling latency not bounded per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Host schedules exit after delay; occupied host grants no new reservation. Reconnect before submission remains possible; no delivery/scheduling guarantee.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:270](../../../docs/LIMITS.md#L270)
- **implementation_navigation:** [`hostExitDelayMs`](../../../runner/Sources/PWRunnerCore/PWRunnerService.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
Behavioral claim:

> Compiled value, single retirement ownership and stale-timer refusal are tested. The delay is not a delivery guarantee and does not bound scheduling latency.


### runner_verify_wait — [docs/LIMITS.md:97](../../../docs/LIMITS.md#L97)

**Source claim (documentary quotation):**

> Default allowance for the fixed runner verify specimen, shared by reservation acquisition and the execution reply wait. Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Elapsed overall verification allowance shared by acquisition and execution reply waiting.
- **Scope assessment:** One fixed runner verify invocation; shared acquisition/reply allowance, separate host budgets.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client overall acquisition/reply wait; acquisition attempt bound may stop earlier.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Flag `--timeout-ms` on `runner verify`.
- **Boundary consequence:** Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:271](../../../docs/LIMITS.md#L271)
- **implementation_navigation:** [`RUNNER_VERIFY_DEFAULT_TIMEOUT_MS`](../../../controller/src/runner_commands.rs); [`PWRunnerClientSession`](../../../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
- **permanent_checks_navigation:** value (test): [`documented_verification_wait`](../../../controller/src/runner_commands.rs); path (test): [`verification_request_is_the_fixed_allow_all_specimen`](../../../controller/src/runner_commands.rs); path (test): [`runClientSessionControls`](../../../runner/Tests/PWRunnerClientSessionTests/main.swift)
Behavioral claim:

> Compiled defaults and the fixed verification request are checked separately from production-client controls for shared deadlines, late callbacks, grant-before-deadline-expiry and no replay after invocation.


### worker_policy_transfer — [docs/LIMITS.md:98](../../../docs/LIMITS.md#L98)

**Source claim (documentary quotation):**

> One absolute monotonic deadline starting immediately after spawn; partial writes and interrupted calls do not restart it. Expiry closes the input pipe and enters host cleanup with policy_transfer_timeout and policy_transfer_deadline; no write errno is invented. The worker, reaching EOF, publishes the count it read beside the host's expected length and refuses a different length before compiling; an observed refusal takes worker-failure precedence.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** One absolute monotonic deadline starting immediately after spawn; partial writes and interrupted calls do not restart it.
- **Scope assessment:** One worker policy delivery; actor_setup_allowance caps each actor delivery.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host policy-pipe write deadline; worker separately validates EOF length before compile.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; internal driver controls may shorten it.
- **Boundary consequence:** Expiry closes the input pipe and enters host cleanup with policy_transfer_timeout and policy_transfer_deadline; no write errno is invented. The worker, reaching EOF, publishes the count it read beside the host's expected length and refuses a different length before compiling; an observed refusal takes worker-failure precedence.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:272](../../../docs/LIMITS.md#L272)
- **implementation_navigation:** [`CWorkerInput.defaultPolicyTransferTimeoutMs`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runPolicyTransferTests`](../../../runner/Tests/PWRunnerCoreTests/PolicyTransferTests.swift); boundary (test): [`policy_truncated_prefix`](../../../tests/suites/runner_c_worker_harness/run.sh)
Behavioral claim:

> Real stalled and draining pipes plus deterministic interrupted, partial and zero-progress writes. Readiness wait starts only after successful delivery. The production budget fits within the default client wait; a shorter client override is independent and does not cancel the host. One driver control joins the host timeout to the shipped worker's refusal of a truncated delivery; the worker harness pins the receipt and both directions of the length comparison.


### worker_ready_wait — [docs/LIMITS.md:99](../../../docs/LIMITS.md#L99)

**Source claim (documentary quotation):**

> Nominal wait for the worker readiness hint. Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues.

- **Category:** Execution budgets
- **Value / derivation:** 1,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Nominal wait for the worker readiness hint.
- **Scope assessment:** One readiness wait; actor setup aggregate caps it.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host readiness wait; coverage describes elapsed clock and failure behavior.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry can leave `runner_subprocess.ready_byte_received: false` while the run continues.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q5: Generic worker row is capped by actor setup aggregate; applicability clear only through cross-reading.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q5: Generic worker row is capped by actor setup aggregate; applicability clear only through cross-reading.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:273](../../../docs/LIMITS.md#L273)
- **implementation_navigation:** [`CWorkerInput`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerTests`](../../../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift)
Behavioral claim:

> runCWorker measures the readiness wait as elapsed monotonic time starting after policy transfer, after making the read end nonblocking; a failed prerequisite is recorded as setup_failed and no wait runs. CWorkerClockTests drive the clock and sleep; expiry leaves ready_byte_received false and the run continues. The ready_wait record carries the budget, elapsed time and stop reason.


### worker_sentinel_wait — [docs/LIMITS.md:100](../../../docs/LIMITS.md#L100)

**Source claim (documentary quotation):**

> Nominal wait for worker results after the readiness-hint wait. Validator collection is outside this allowance; the listed duration is not a total runtime limit. Expiry can yield `runner_timeout` with partial evidence and reported cleanup results.

- **Category:** Execution budgets
- **Value / derivation:** 120,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Nominal wait for worker results after the readiness-hint wait.
- **Scope assessment:** One worker publication wait; relationship to actor schedule allowance not explicitly scoped.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host publication/sentinel polling; coverage describes collection exclusions and clock faults.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry can yield `runner_timeout` with partial evidence and reported cleanup results.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q5: Relationship of legacy publication window to actor schedule budget needs scope clarification, not arithmetic addition.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q5: Relationship of legacy publication window to actor schedule budget needs scope clarification, not arithmetic addition.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:274](../../../docs/LIMITS.md#L274)
- **implementation_navigation:** [`timeoutMsForCWorker`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerTests`](../../../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift)
Behavioral claim:

> runCWorker measures the publication wait as elapsed monotonic time from the end of the readiness wait, with each synchronous phase collection interval measured and excluded; every sleep is bounded by the remaining allowance, and a failed or regressing clock spends only the last remaining allowance in nominal sleeps, including the last requested sleep, and sentinel_wait.clock_fault reports the fault. CWorkerClockTests cover oversleep, irregular polling costs, zero allowance, interrupted waits, clock failure, regression and excluded intervals; the live deadline cases assert the measured allowance within a stated scheduling tolerance. The worker uses a separate local active-time exec budget, configured below this window without an end-to-end guarantee.


### actor_setup_allowance — [docs/LIMITS.md:101](../../../docs/LIMITS.md#L101)

**Source claim (documentary quotation):**

> One aggregate allowance from the first actor launch to the last setup disposition, capping each policy delivery and readiness wait. An actor whose setup is unresolved at expiry is stopped and reported `setup_timeout`; independent actors keep their own dispositions.

- **Category:** Execution budgets
- **Value / derivation:** 10,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** One aggregate allowance from the first actor launch to the last setup disposition, capping each policy delivery and readiness wait.
- **Scope assessment:** All actor setup dispositions from first launch to last setup; aggregate, not per actor.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host actor-setup scheduler, polling pending setup publications per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; the actor timing qualification case measures finite one-, three- and eight-actor workloads against this allowance on the recorded equipment and requires at least a quarter of it to remain.
- **Boundary consequence:** At expiry, unresolved actors are stopped and reported setup_timeout; independent actors retain their own dispositions.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q6: Qualification claims finite workloads, not all admitted maximal plans; exact workload/equipment unverified.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q6: Qualification claims finite workloads, not all admitted maximal plans; exact workload/equipment unverified.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:275](../../../docs/LIMITS.md#L275)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`ActorScheduleInput`](../../../runner/Sources/PWRunnerCore/ActorScheduler.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runActorSchedulerTests`](../../../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift)
Behavioral claim:

> The scheduler launches actors in order under one clock and polls every pending setup publication; a later actor can still launch while an earlier one is pending.


### actor_execution_allowance — [docs/LIMITS.md:102](../../../docs/LIMITS.md#L102)

**Source claim (documentary quotation):**

> One host allowance for the whole serial schedule, excluding measured validator collection; not one allowance per actor. Expiry ends the current visit (`arrival_timeout` or `completion_timeout`) and cancels the remaining schedule; every earlier publication is retained.

- **Category:** Execution budgets
- **Value / derivation:** 120,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** One host allowance for the whole serial schedule, excluding measured validator collection; not one allowance per actor.
- **Scope assessment:** One whole serial actor schedule excluding measured collection, not per actor.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host serial scheduler while awaiting visit arrival/completion.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; the actor timing qualification case measures finite one-, three- and eight-actor workloads against this allowance on the recorded equipment and requires at least a quarter of it to remain.
- **Boundary consequence:** Expiry ends the current visit (`arrival_timeout` or `completion_timeout`) and cancels the remaining schedule; every earlier publication is retained.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q6: Qualification claims finite workloads, not all admitted maximal plans; exact workload/equipment unverified.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q6: Qualification claims finite workloads, not all admitted maximal plans; exact workload/equipment unverified.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:276](../../../docs/LIMITS.md#L276)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`ActorScheduleInput`](../../../runner/Sources/PWRunnerCore/ActorScheduler.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runActorSchedulerTests`](../../../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift)
Behavioral claim:

> Collection time is excluded through the same clock discipline as the single-worker sentinel wait.


### actor_collection_allowance — [docs/LIMITS.md:103](../../../docs/LIMITS.md#L103)

**Source claim (documentary quotation):**

> Aggregate validator planning and collection allowance across every actor's phases. Exhaustion marks later phases `budget_exhausted`; earlier collections are retained.

- **Category:** Execution budgets
- **Value / derivation:** 30,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Aggregate validator planning and collection allowance across every actor's phases.
- **Scope assessment:** All actor phases together; relationship to phase_collection_wait override not stated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host collection budgeting; relation to generic phase pool not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed; the actor timing qualification case measures finite one-, three- and eight-actor workloads against this allowance on the recorded equipment and requires at least a quarter of it to remain.
- **Boundary consequence:** Exhaustion marks later phases `budget_exhausted`; earlier collections are retained.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q5: Aggregate actor pool is clear, but relationship to phase_collection_wait internal override is not.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q5: Aggregate actor pool is clear, but relationship to phase_collection_wait internal override is not.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:277](../../../docs/LIMITS.md#L277)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`runActors`](../../../runner/Sources/PWRunnerCore/ActorOrchestration.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift)
Behavioral claim:

> Each phase plans its queries freshly against the active actor; the aggregate does not restart per actor.


### actor_release_wait — [docs/LIMITS.md:104](../../../docs/LIMITS.md#L104)

**Source claim (documentary quotation):**

> The worker's wait from a visit's arrival to the host's release of that visit's ordinal. Expiry refuses the visit with a published timing failure, as the single-worker release wait does.

- **Category:** Execution budgets
- **Value / derivation:** 60,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** The worker's wait from a visit's arrival to the host's release of that visit's ordinal.
- **Scope assessment:** Each activated actor visit from arrival to release; parked time excluded per coverage.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker arrival-to-release wait; same mechanism as legacy per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; the actor timing qualification case measures finite one-, three- and eight-actor workloads against this allowance on the recorded equipment and requires at least a quarter of it to remain.
- **Boundary consequence:** Expiry refuses the visit with a published timing failure, as the single-worker release wait does.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q6: Same release mechanism described; finite qualification does not establish all schedules finish.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q6: Same release mechanism described; finite qualification does not establish all schedules finish.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:278](../../../docs/LIMITS.md#L278)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`wait_for_proceed`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runActorSchedulerTests`](../../../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift)
Behavioral claim:

> The same wait the legacy worker runs, started only after the activated actor arrives; parked time is not charged to it.


### actor_exchange_allowance — [docs/LIMITS.md:105](../../../docs/LIMITS.md#L105)

**Source claim (documentary quotation):**

> Each custody acknowledgement a worker awaits after publishing an issued token, each transfer request it awaits an answer to, and each recipient acknowledgement the host awaits. Expiry is a transport observation (`timeout` custody or a `host_timeout`/`recipient_timeout` transfer status), never a native result.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Elapsed duration of each custody, transfer-answer or recipient acknowledgement wait.
- **Scope assessment:** Each custody/transfer-answer/recipient acknowledgement wait; shared lifetime also bounds it per coverage.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker custody/transfer-answer waits and host recipient-ack wait, independent clocks per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; the actor timing qualification case measures finite one-, three- and eight-actor workloads against this allowance on the recorded equipment and requires at least a quarter of it to remain.
- **Boundary consequence:** Expiry is a transport observation (`timeout` custody or a `host_timeout`/`recipient_timeout` transfer status), never a native result.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q6: Per-exchange budgets cannot be multiplied into guaranteed total time; native call deadline not stated.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q6: Per-exchange budgets cannot be multiplied into guaranteed total time; native call deadline not stated.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:279](../../../docs/LIMITS.md#L279)
- **implementation_navigation:** [`PW_AUTHORITY_EXCHANGE_WAIT_MS`](../../../controller/tools/pw_probe_runner/pw_authority_region.h); [`PWAuthorityLayout`](../../../runner/Sources/PWRunnerCore/AuthorityCustody.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runActorAuthorityTests`](../../../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift)
Behavioral claim:

> Both sides measure the exchange on their own clocks; the shared lifetime cutoff also bounds it.


### actor_lifetime_cutoff — [docs/LIMITS.md:106](../../../docs/LIMITS.md#L106)

**Source claim (documentary quotation):**

> One absolute continuous-clock cutoff shared by every actor, taken before the first launch; it includes parked waits, collection and sleep. A worker that reaches the cutoff publishes a timing failure and exits; a cutoff already past at launch refuses before any policy byte.

- **Category:** Execution budgets
- **Value / derivation:** 180,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** One absolute continuous-clock cutoff shared by every actor, taken before the first launch; it includes parked waits, collection and sleep.
- **Scope assessment:** One common absolute cutoff for all actors including parking/collection/sleep, established before launch.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker checked timing paths; guide says blocked native call can prevent check.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; the actor timing qualification case measures finite one-, three- and eight-actor workloads against this allowance on the recorded equipment and requires at least a quarter of it to remain.
- **Boundary consequence:** Checked cutoff publishes timing failure and exits; already-past cutoff at launch refuses before policy bytes. Guide qualifies blocked native calls may prevent checking.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q4: Row can be read as unconditional cutoff exit; guide qualifies checked waits and blocked native calls.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q4: Row can be read as unconditional cutoff exit; guide qualifies checked waits and blocked native calls.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:280](../../../docs/LIMITS.md#L280)
- **implementation_navigation:** [`PWActorLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerActors.swift); [`continuousCutoff`](../../../runner/Sources/PWRunnerCore/ActorScheduler.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runActorSchedulerTests`](../../../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift)
Behavioral claim:

> Each actor's header carries the same raw `mach_continuous_time` cutoff; acknowledgements and heartbeats cannot extend it.


### worker_exit_grace — [docs/LIMITS.md:107](../../../docs/LIMITS.md#L107)

**Source claim (documentary quotation):**

> Elapsed monotonic wait for an unreaped worker after the host stores an exit request. Expiry requests `SIGKILL`. Termination and reap failures remain reported.

- **Category:** Execution budgets
- **Value / derivation:** 1,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Elapsed monotonic wait for an unreaped worker after the host stores an exit request.
- **Scope assessment:** Each unreaped worker after exit request; actor aggregation not explicitly described.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host reap wait after exit request when worker is unreaped.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry requests `SIGKILL`. Termination and reap failures remain reported.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:281](../../../docs/LIMITS.md#L281)
- **implementation_navigation:** [`CWorkerInput`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerLifecycleTests`](../../../runner/Tests/PWRunnerCoreTests/CWorkerLifecycleTests.swift)
Behavioral claim:

> runCWorker measures the exit grace as elapsed monotonic time after storing exit_requested when the child is not already reaped, then attempts SIGKILL and reaping; exit_grace_wait records the budget, elapsed time and how the wait ended. Terminal worker publication exits without waiting for that request; cancellation and fallback cleanup remain. Deadline/cleanup paths use controlled children and a controlled clock; the production duration is source-inspected.


### worker_proceed_wait — [docs/LIMITS.md:108](../../../docs/LIMITS.md#L108)

**Source claim (documentary quotation):**

> Sampled continuous time for each phase release after the worker arrives, converted once before application to a ceiling tick allowance. Continuous time includes system sleep. Expiry records the phase index and milliseconds and prevents its actions. An unusable sample, an earlier rejected sample or an unrepresentable plan exclusion records a local timing refusal with its reason instead; neither invents a native result or errno. Earlier published phase evidence remains.

- **Category:** Execution budgets
- **Value / derivation:** 60,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Sampled continuous time for each phase release after the worker arrives, converted once before application to a ceiling tick allowance.
- **Scope assessment:** Each arrived phase's release wait; actor row says same mechanism.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker wait_for_proceed samples time before release/cancellation per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry records the phase index and milliseconds and prevents its actions. An unusable sample, an earlier rejected sample or an unrepresentable plan exclusion records a local timing refusal with its reason instead; neither invents a native result or errno. Earlier published phase evidence remains.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:282](../../../docs/LIMITS.md#L282)
- **implementation_navigation:** [`PW_PROCEED_WAIT_MS_DEFAULT`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h); [`wait_for_proceed`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c); [`publish_done_and_exit`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); path (control): [`main`](../../../tests/suites/runner_c_worker_harness/harness.c); path (test): [`runOrderingTests`](../../../runner/Tests/PWRunnerCoreTests/OrderingTests.swift); boundary (control): [`main`](../../../tests/fixtures/worker_lifecycle/proceed_control.c); path (test): [`runWorkerClockTests`](../../../runner/Tests/PWRunnerCoreTests/WorkerClockTests.swift); path (test): [`proceed_without_host_release`](../../../tests/suites/runner_c_worker_harness/run.sh); boundary (test): [`terminal_erasure`](../../../tests/suites/runner_c_worker_harness/run.sh)
Behavioral claim:

> wait_for_proceed decides expiry from a validated continuous sample before consulting release or cancellation. A pre-expiry sample can be followed by delayed scheduling and a late acknowledgement, and a release stored before expiry can be refused by an expired next sample; cancellation wins only when its load observes it. A sample below the origin or the last accepted sample fails closed without another clock, and a rejection during an earlier exec refuses later phases without another read. Each phase's measured wait is added to the exec plan once, in ticks, at acknowledgement. Refusal erases an accepted token buffer, publishes done and exits without a host exit request; cancellation erases and exits without adding done, acknowledgement or failure. This bounds the sampled refusal path, not native calls, descendant lifetime or total cleanup. Deterministic precedence, race-gate, sample and exclusion controls establish the order; native controls exercise the clock under deny-default profiles on the recorded machine; actual system sleep is untested. Production duration is value-checked.


### validator_release_margin — [docs/LIMITS.md:109](../../../docs/LIMITS.md#L109)

**Source claim (documentary quotation):**

> Informative allowance between the validator budgets and worker release wait. No separate timeout or refusal occurs at this value.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Nominal configuration allowance between validator and release budgets.
- **Scope assessment:** Configuration relationship between validator and release allowances; no independently timed operation.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Not applicable: explicitly unenforced configuration margin.
- **Enforcement status:** not_applicable
- **Control (documentary):** Not enforced; no flag.
- **Boundary consequence:** Not applicable: no expiry, timeout or refusal at this informative value.
- **Boundary status:** not_applicable
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:283](../../../docs/LIMITS.md#L283)
- **implementation_navigation:** [`validatorReleaseMarginMs`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift)
Behavioral claim:

> validatorReleaseMarginMs allows for host observation, setup, decoding and scheduling. Production defaults satisfy 60000 > 30000 + 1000 + 5000. This configuration guard excludes test overrides and does not bound final blocking reap, host descheduling, prompt replies or eventual orphan cleanup. Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked.


### validator_io_override_floor — [docs/LIMITS.md:110](../../../docs/LIMITS.md#L110)

**Source claim (documentary quotation):**

> Minimum proposed `_test_overrides.validator_io_timeout_ms`. Smaller supplied values propose 50 ms; the reply mirrors the supplied value. The remaining aggregate collection allowance caps the effective deadline, including below this floor.

- **Category:** Execution budgets
- **Value / derivation:** 50 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Minimum proposed override value, not effective deadline after aggregate cap.
- **Scope assessment:** Each proposed internal validator I/O override, not effective deadline after aggregate cap.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Proposed override normalization; remaining collection budget caps effective deadline separately.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Smaller supplied values propose 50 ms, but supplied value is mirrored. Remaining aggregate budget may cap effective deadline below floor.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:284](../../../docs/LIMITS.md#L284)
- **implementation_navigation:** [`timeoutMsForValidator`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift)
Behavioral claim:

> Short-budget, delayed-release, clock-failure and delayed-cleanup controls establish fail-closed behavior; production duration is value-checked.


### validator_io_wait — [docs/LIMITS.md:111](../../../docs/LIMITS.md#L111)

**Source claim (documentary quotation):**

> Default elapsed monotonic deadline for one phase’s query delivery and verdict collection, capped by the remaining aggregate collection allowance. Received verdicts survive an I/O timeout; cleanup results remain reported.

- **Category:** Execution budgets
- **Value / derivation:** 30,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Default elapsed monotonic deadline for one phase’s query delivery and verdict collection, capped by the remaining aggregate collection allowance.
- **Scope assessment:** Each phase's query delivery/verdict collection; capped by remaining aggregate budget.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Validator driver nonblocking I/O deadline per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Received verdicts survive an I/O timeout; cleanup results remain reported.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:285](../../../docs/LIMITS.md#L285)
- **implementation_navigation:** [`ValidatorClientInput`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> runValidator uses CLOCK_MONOTONIC for nonblocking writes and reads. The validator_io_timeout_ms seam changes its proposed deadline, floored at 50 ms, while the aggregate phase allowance can cap the effective deadline below that floor. Earlier records survive timeout; cleanup observations remain separate.


### validator_exit_grace — [docs/LIMITS.md:112](../../../docs/LIMITS.md#L112)

**Source claim (documentary quotation):**

> Nominal wait for validator exit after collection closes. Expiry requests `SIGKILL`. Termination and reap failures remain reported.

- **Category:** Execution budgets
- **Value / derivation:** 1,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Nominal wait for validator exit after collection closes.
- **Scope assessment:** Each validator exit observation after collection closes.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host wait after validator collection closes, then termination/reap per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry requests `SIGKILL`. Termination and reap failures remain reported.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:286](../../../docs/LIMITS.md#L286)
- **implementation_navigation:** [`ValidatorClientInput`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> runValidator closes the validator pipes and measures the exit grace as elapsed monotonic time before attempting SIGKILL and reaping; the phase collection record carries exit_grace_wait. Cleanup paths use controlled children; the production duration is source-inspected.


### exec_child_wait — [docs/LIMITS.md:113](../../../docs/LIMITS.md#L113)

**Source claim (documentary quotation):**

> Continuous time after successful spawn, limited by the remaining `exec_attempt_budget`. Expiry fails the attempt while preserving any observed natural exit code. An unusable sample or unrepresentable child deadline ends observation as a local timing fault with no errno. Cleanup results remain reported; an observed leader exit does not establish that every descendant stopped.

- **Category:** Execution budgets
- **Value / derivation:** 10,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Continuous time after successful spawn, limited by the remaining `exec_attempt_budget`.
- **Scope assessment:** Each spawned exec child's observation, not all descendants' lifetime.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker observation deadline after successful spawn.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry fails the attempt while preserving any observed natural exit code. An unusable sample or unrepresentable child deadline ends observation as a local timing fault with no errno. Cleanup results remain reported; an observed leader exit does not establish that every descendant stopped.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:287](../../../docs/LIMITS.md#L287)
- **implementation_navigation:** [`PW_EXEC_CHILD_DEADLINE_MS_DEFAULT`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); path (test): [`runCWorkerTests`](../../../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift); boundary (control): [`main`](../../../tests/fixtures/worker_lifecycle/exec_control.c)
Behavioral claim:

> The absolute child deadline and local exec plan cutoff are compared in ticks with checked addition, without restarting the plan budget after spawn. EOF and child exit are observed separately. Deadline, observation failure or a local timing fault requests process-group termination while the leader is still owned, even after leader exit. Live controls close streams while both processes remain alive and exit the leader while a descendant retains streams. Independent socket credentials, OS exit events and file effects establish the behavior.


### exec_attempt_budget — [docs/LIMITS.md:114](../../../docs/LIMITS.md#L114)

**Source claim (documentary quotation):**

> Continuous time from the worker origin before setup, shared by exec steps, including worker setup and intervening work but excluding each acknowledged release wait. Continuous time includes system sleep. Exhaustion refuses a later spawn with `exec_failed` and `ETIMEDOUT`, no `child_pid` and no sandbox attribution. An unusable sample refuses spawn with no errno, or after spawn records a local timing fault beside any native error; after a rejected sample, later spawns are refused. Blocking spawn and non-exec operations may outlast this allowance.

- **Category:** Execution budgets
- **Value / derivation:** 115,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Continuous time from the worker origin before setup, shared by exec steps, including worker setup and intervening work but excluding each acknowledged release wait.
- **Scope assessment:** All exec steps sharing worker origin; actor-level ownership of pool not explicitly restated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Worker checks before spawn and during timed observation; blocking spawn/non-exec work not preempted.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Exhaustion refuses a later spawn with `exec_failed` and `ETIMEDOUT`, no `child_pid` and no sandbox attribution. An unusable sample refuses spawn with no errno, or after spawn records a local timing fault beside any native error; after a rejected sample, later spawns are refused. Blocking spawn and non-exec operations may outlast this allowance.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:288](../../../docs/LIMITS.md#L288)
- **implementation_navigation:** [`PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h); [`pw_timing_setup`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`exec_attempt_budget_remainder`](../../../tests/suites/runner_c_worker_harness/run.sh)
Behavioral claim:

> pw_clock_start records the worker origin before setup; pw_timing_setup converts the allowance to a ceiling tick count before policy reading or application and refuses an invalid timebase or unrepresentable duration with exit 12. wait_for_proceed adds each phase's measured wait once with checked addition. Exec attempts receive an absolute cutoff independent of the host polling clock. A local timing fault after spawn triggers cleanup. Blocking spawn and non-exec operations are not preemptible here. The production default sits a nominal 5,000 ms below worker_sentinel_wait; test equipment may shorten it independently and the specimen worker_timeout_ms override does not move it. Compiled values agree with the host configuration. Deterministic native controls vary spawn latency, release exclusion, intervening work, exact exhaustion, every timing stage, arithmetic refusals and cleanup. Real short-budget plans preserve completed prefix and trailing file effects through host assembly and serialization.


### exec_reap_grace — [docs/LIMITS.md:115](../../../docs/LIMITS.md#L115)

**Source claim (documentary quotation):**

> Continuous-time allowance to confirm an exec child's exit after observation ends. Expiry, an unusable sample or a wait error leaves reaping unconfirmed and supplies no invented exit status; an unusable clock still permits the immediate exit check. Failed group termination leaves only an immediate exit check. This is not a total cleanup runtime limit.

- **Category:** Execution budgets
- **Value / derivation:** 1,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Continuous-time allowance to confirm an exec child's exit after observation ends.
- **Scope assessment:** Each exec child's final exit-confirmation window; not whole cleanup.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker nonblocking final reap checks; failed group kill leaves immediate check only.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry, an unusable sample or a wait error leaves reaping unconfirmed and supplies no invented exit status; an unusable clock still permits the immediate exit check. Failed group termination leaves only an immediate exit check. This is not a total cleanup runtime limit.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:289](../../../docs/LIMITS.md#L289)
- **implementation_navigation:** [`PW_EXEC_REAP_GRACE_MS`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (control): [`main`](../../../tests/fixtures/worker_lifecycle/exec_control.c)
Behavioral claim:

> Final reaping uses nonblocking waitpid in a local continuous-time observation window. Failed group termination or unusable reap time permits only an immediate nonblocking reap, whose status is kept when it returns the child. The allowance does not bound native syscall duration or host descheduling. Controlled pending/EINTR waits exhaust the grace; kill, wait and local timing faults retain missing status. Every wait is required to be nonblocking.


### client_rpc_wait — [docs/LIMITS.md:116](../../../docs/LIMITS.md#L116)

**Source claim (documentary quotation):**

> One absolute client allowance, including helper launch/stdin delivery, reservation acquisition and the execution reply wait. Direct helper invocation starts after reading input. Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate.

- **Category:** Execution budgets
- **Value / derivation:** 240,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** One absolute client allowance, including helper launch/stdin delivery, reservation acquisition and the execution reply wait.
- **Scope assessment:** One client invocation across launch/stdin/acquisition/reply, not each actor.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client overall deadline including controller launch/stdin; acquisition bound can stop first.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Flag `--timeout-ms`, floored at 1 ms; values above this default are permitted.
- **Boundary consequence:** Overall expiry reports xpc_timeout with the captured submission state. Acquisition may stop earlier at its attempt bound. Expiry after invocation does not establish nonexecution or cancel host work; worker/validator budgets remain separate.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:290](../../../docs/LIMITS.md#L290)
- **implementation_navigation:** [`DEFAULT_TIMEOUT_MS`](../../../controller/src/run_flow.rs); [`defaultClientTimeoutMs`](../../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift); [`defaultClientTimeoutMs`](../../../runner/Clients/PWRunnerClient/main.swift); [`PWRunnerClientSession`](../../../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`documented_controller_limits`](../../../controller/src/run_flow.rs); path (test): [`runClientSessionControls`](../../../runner/Tests/PWRunnerClientSessionTests/main.swift)
Behavioral claim:

> Compiled defaults and the fixed verification request are checked separately from production-client controls for shared deadlines, late callbacks, grant-before-deadline-expiry and no replay after invocation.


### runner_remove_teardown_wait — [docs/LIMITS.md:117](../../../docs/LIMITS.md#L117)

**Source claim (documentary quotation):**

> Nominal wait for a removed BYOXPC service to disappear from launchd. The cleanup observation records the service checks and the wait. A service still listed at expiry retains its cleanup record with a warning; a later `runner remove` or `runner reconcile` continues recovery.

- **Category:** Execution budgets
- **Value / derivation:** 1,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Nominal wait for a removed BYOXPC service to disappear from launchd.
- **Scope assessment:** One BYOXPC removal that issued bootout; no wait if none issued.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Runner removal polls launchd service state, every 50 ms per coverage.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed. No wait when the removal issued no bootout.
- **Boundary consequence:** A service still listed at expiry retains its cleanup record with a warning; a later `runner remove` or `runner reconcile` continues recovery.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:291](../../../docs/LIMITS.md#L291)
- **implementation_navigation:** [`TEARDOWN_WAIT_MS`](../../../controller/src/runner_manager.rs)
- **permanent_checks_navigation:** value (test): [`documented_removal_limits`](../../../controller/src/runner_manager.rs); boundary (test): [`bootout_waits_out_launchd_teardown_within_the_budget`](../../../controller/src/runner_manager.rs)
Behavioral claim:

> After its own bootout, runner remove re-reads the service every 50 milliseconds until it is absent or the nominal allowance is spent. Controlled cleanup systems report the job present for two reads and then absent (completion after two waits), present for every read (retention after the whole allowance), and a skipped bootout (nothing awaited). The live removal cases observe real launchd teardown.


### byoxpc_throttle_interval — [docs/LIMITS.md:118](../../../docs/LIMITS.md#L118)

**Source claim (documentary quotation):**

> `ThrottleInterval` in every launchd plist that `runner install` generates. The host exits after each specimen and launchd starts the job at most once per interval; the wait is counted from the previous launch, not from the previous exit. A request to an installed external runner that arrives within the interval of the previous launch waits for the remainder before a host serves it. Without the key launchd applies its ten-second default. Acquisition reaching an occupied or retiring host can retry without sending the specimen; the interval still controls launch pacing.

- **Category:** Execution budgets
- **Value / derivation:** 1 second
- **Unit:** second
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Minimum launch spacing from previous launch, not previous exit.
- **Scope assessment:** Each generated external runner launchd job; interval measured from previous launch.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** launchd job ThrottleInterval set by runner install.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed in the generated plist. An installed plist can be edited by hand after `runner remove` and a fresh install; the registry's plist hash then differs and removal reports the ownership disagreement.
- **Boundary consequence:** Request arriving within interval waits remainder. Missing key means launchd ten-second default; occupied/retiring acquisition can retry without submission.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:292](../../../docs/LIMITS.md#L292)
- **implementation_navigation:** [`BYOXPC_THROTTLE_INTERVAL_SECONDS`](../../../controller/src/runner_manager.rs)
- **permanent_checks_navigation:** value (test): [`documented_throttle_interval`](../../../controller/src/runner_manager.rs); boundary (test): [`byoxpc_plist_sets_the_respawn_throttle`](../../../controller/src/runner_manager.rs); boundary (test): [`single_use`](../../../tests/suites/runner_byoxpc/opt_in/single_use.sh)
Behavioral claim:

> Measured on one owned installation (macOS 14.8, user scope) with the plist rewritten per candidate: with no key a run 0.4 s after the previous one took about 10.3 s and a run after the install's own verify about 9.2 s; with the interval at one second those took about 1.3 s and 0.3 s. The single-use live case reads the installed plist's value and waits it out plus a margin before requiring a fresh host.


### phase_collection_wait — [docs/LIMITS.md:119](../../../docs/LIMITS.md#L119)

**Source claim (documentary quotation):**

> Cumulative monotonic time spent planning and collecting across all phases. The remaining allowance caps each validator I/O deadline. Cleanup and scheduling can overrun that deadline. After exhaustion, subsequent predictions are unavailable; the worker can still execute released attempts.

- **Category:** Execution budgets
- **Value / derivation:** 30,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Cumulative monotonic time spent planning and collecting across all phases.
- **Scope assessment:** All phases cumulatively; relation to actor_collection_allowance not explicitly delimited.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host cumulative planning/collection accounting; cleanup can overrun.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; `_test_overrides.validator_total_timeout_ms` can reduce it to at least 1 millisecond.
- **Boundary consequence:** Exhaustion makes later predictions unavailable while released attempts can still execute; cleanup/scheduling may overrun the capped I/O deadline.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q5: Relationship/override applicability to actor_collection_allowance is unstated; do not assume two independent 30-second pools.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q5: Relationship/override applicability to actor_collection_allowance is unstated; do not assume two independent 30-second pools.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:311](../../../docs/LIMITS.md#L311)
- **implementation_navigation:** [`phaseCollectionBudgetMs`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runPhaseProtocolTests`](../../../runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift)
Behavioral claim:

> Cumulative monotonic time spent planning and collecting across all phases. The remaining allowance caps each validator I/O deadline. Cleanup and scheduling can overrun that deadline. After exhaustion, subsequent predictions are unavailable; the worker can still execute released attempts.


### extension_issuer_wait — [docs/LIMITS.md:120](../../../docs/LIMITS.md#L120)

**Source claim (documentary quotation):**

> Monotonic host wait starting after successful issuer spawn, before worker creation. Target preparation and spawn precede this clock; phase collection and worker waits have not started. Expiry requests termination, records native publication and cleanup independently, and withholds delivery. Termination/reaping and scheduling can overrun this wait.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Monotonic host wait starting after successful issuer spawn, before worker creation.
- **Scope assessment:** Preparatory issuer path; guide identifies declaration form, row lacks explicit qualifier.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Host issuer collection after spawn, followed by termination/reap efforts.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Expiry requests termination, records native publication and cleanup independently, and withholds delivery. Termination/reaping and scheduling can overrun this wait.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q3: Pre-worker issuance applies to declaration form per guide and brief; row and interaction lack explicit form qualifier.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q3: Pre-worker issuance applies to declaration form per guide and brief; row and interaction lack explicit form qualifier.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:337](../../../docs/LIMITS.md#L337)
- **implementation_navigation:** [`PW_EXTENSION_ISSUER_WAIT_MS`](../../../controller/tools/pw_probe_runner/pw_extension_channel.h); [`ExtensionSession`](../../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`run_case`](../../../tests/suites/witness_contract/check_extension_boundaries.py)
Behavioral claim:

> Production issuer/worker controls cover maximum payload, over-capacity or malformed framing, deadline, missing publication, native failure and independent cleanup/confinement.


### sysctl_read_bytes — [docs/LIMITS.md:121](../../../docs/LIMITS.md#L121)

**Source claim (documentary quotation):**

> Destination for one post-apply sysctlbyname value read with a non-null buffer; no sizing call or retry. Larger values can fail within this bound. Returned value bytes and post-call length are discarded; a failed call does not diagnose whether capacity was insufficient.

- **Category:** Execution budgets
- **Value / derivation:** 4,096 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Destination buffer capacity in one sysctlbyname read; no sizing/retry.
- **Scope assessment:** Each post-apply sysctl/read attempt with one non-null destination; not complete arbitrary-value retrieval.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** One native sysctlbyname call receives fixed non-null destination; no growth/retry.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Larger values can fail within this bound. Returned value bytes and post-call length are discarded; a failed call does not diagnose whether capacity was insufficient.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:338](../../../docs/LIMITS.md#L338)
- **implementation_navigation:** [`PW_SYSCTL_READ_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c); [`attempt_sysctl_read`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c)
- **permanent_checks_navigation:** value (test): [`check_manifest`](../../../tests/suites/runner_c_worker_harness/check_sysctl.py); boundary (test): [`check_capacity`](../../../tests/suites/runner_c_worker_harness/check_sysctl.py); path (test): [`check_call_and_result`](../../../tests/suites/runner_c_worker_harness/check_sysctl.py)
Behavioral claim:

> Compiled production-call substitution checks the actual incoming capacity and call shape independently, preserves success/failure status and errno, and rejects a shortened supplied-capacity mutation. The live sysctl filter case separately establishes public compatibility for its specimen.


### reservation_lease — [docs/LIMITS.md:122](../../../docs/LIMITS.md#L122)

**Source claim (documentary quotation):**

> Requested unused lease, capped by the host; the client requests no more than its remaining allowance. Expiry or owner disconnect retires the unused host. Submission checks expiry atomically and an old timer cannot terminate execution.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Requested unused lease, capped by the host; the client requests no more than its remaining allowance.
- **Scope assessment:** Each unused reservation, nonrenewable; client remaining allowance caps request.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Host unused-lease expiry/disconnect and atomic submission expiry check.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed. No renewal.
- **Boundary consequence:** Expiry or owner disconnect retires the unused host. Submission checks expiry atomically and an old timer cannot terminate execution.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:340](../../../docs/LIMITS.md#L340)
- **implementation_navigation:** [`reservationLeaseMs`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### reservation_rpc_wait — [docs/LIMITS.md:123](../../../docs/LIMITS.md#L123)

**Source claim (documentary quotation):**

> Maximum wait for one reserve reply, also bounded by the original overall client deadline. Expiry abandons and invalidates that connection; acquisition may continue without submitting a specimen.

- **Category:** Execution budgets
- **Value / derivation:** 5,000 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Maximum wait for one reserve reply, also bounded by the original overall client deadline.
- **Scope assessment:** Each reserve RPC, additionally capped by original overall client deadline.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client wait for reserve reply; expiry invalidates connection.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed per-attempt ceiling.
- **Boundary consequence:** Expiry abandons and invalidates that connection; acquisition may continue without submitting a specimen.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:341](../../../docs/LIMITS.md#L341)
- **implementation_navigation:** [`reservationRPCMs`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runClientSessionControls`](../../../runner/Tests/PWRunnerClientSessionTests/main.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### reservation_attempts — [docs/LIMITS.md:124](../../../docs/LIMITS.md#L124)

**Source claim (documentary quotation):**

> Every opened acquisition attempt, including transport failures and occupied replies. Exhaustion ends acquisition explicitly at attempt_limit with no submission; it can precede the overall timeout. Every attempted acquisition stays in the capture.

- **Category:** Execution budgets
- **Value / derivation:** 256 items
- **Unit:** items
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Every opened acquisition attempt, including transport failures and occupied replies.
- **Scope assessment:** Entire client acquisition sequence, including failed/occupied attempts.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client acquisition loop's opened-attempt counter.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Exhaustion ends acquisition explicitly at attempt_limit with no submission; it can precede the overall timeout. Every attempted acquisition stays in the capture.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:342](../../../docs/LIMITS.md#L342)
- **implementation_navigation:** [`acquisitionAttempts`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runClientSessionControls`](../../../runner/Tests/PWRunnerClientSessionTests/main.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### reservation_retry_delay — [docs/LIMITS.md:125](../../../docs/LIMITS.md#L125)

**Source claim (documentary quotation):**

> Minimum delay between a failed/occupied attempt and another connection, within the remaining allowance. No delay after a successful grant. Scheduling may take longer; neither waiting nor progress renews the deadline.

- **Category:** Execution budgets
- **Value / derivation:** 100 milliseconds
- **Unit:** milliseconds
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Minimum interval before next connection after failed/occupied attempt.
- **Scope assessment:** Between failed/occupied acquisition attempts; none after grant, no overall deadline renewal.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client reconnect pacing after failed/occupied attempt.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed minimum.
- **Boundary consequence:** Another attempt waits at least interval; scheduling may take longer. No delay after grant and no deadline renewal.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:343](../../../docs/LIMITS.md#L343)
- **implementation_navigation:** [`retryDelayMs`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runClientSessionControls`](../../../runner/Tests/PWRunnerClientSessionTests/main.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### validator_query_payload — [docs/LIMITS.md:131](../../../docs/LIMITS.md#L131)

**Source claim (documentary quotation):**

> Serialized JSON bytes for one validator probe, excluding the final LF. JSON escapes count toward this size. An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit.

- **Category:** Queries and transport
- **Value / derivation:** 65,534 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Serialized JSON bytes for one validator probe, excluding the final LF.
- **Scope assessment:** Each serialized probe line excluding LF, not complete query batch.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Validator physical-line reader before JSON parsing; coverage describes draining overlong line.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** An overlong line produces one `parse_error` without a step ID; later lines remain usable. Admitted specimens stay below this limit.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:293](../../../docs/LIMITS.md#L293)
- **implementation_navigation:** [`LINE_MAX_BYTES`](../../../controller/tools/sb_api_validator/sb_api_validator.c); [`runValidator`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`query_boundary`](../../../tests/suites/runner_abi_layout/limits.py); path (test): [`validator_overlong_request`](../../../tests/suites/failure_boundaries/check.py)
Behavioral claim:

> The fixed 65536-byte buffer allows a 65534-byte payload. The reader counts physical bytes, including raw NUL, and drains an overlong line. Admission bounds on operation and filter value keep a fully escaped probe line to a few KiB. Exact payload boundary, over-limit drain/recovery, valid raw and escaped Unicode, malformed escapes/UTF-8/raw controls and raw-NUL physical framing. Every rejected probe is followed by a valid recovery probe.


### runner_reply_maximum — [docs/LIMITS.md:132](../../../docs/LIMITS.md#L132)

**Source claim (documentary quotation):**

> Upper bound on the encoded size of one runner JSON reply for this build. No reply is refused at this size; retained output is bounded by `controller_output`.

- **Category:** Queries and transport
- **Value / derivation:** 85,852,557 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Conservative encoded reply size; mutually exclusive fields counted together, actor components added per coverage.
- **Scope assessment:** One encoded runner reply; coverage includes actor components and mutually exclusive fields.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Not applicable: informative upper bound, explicitly not enforced.
- **Enforcement status:** not_applicable
- **Control (documentary):** Not enforced; it sizes `controller_output`.
- **Boundary consequence:** Not applicable: no reply is refused at this informative bound; receiver retention acts separately.
- **Boundary status:** not_applicable
- **Disposition:** question
- **Reason:** Q9: Upper-bound claim includes actor components in coverage; numeric bound and completeness need independent verification.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q9: Upper-bound claim includes actor components in coverage; numeric bound and completeness need independent verification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:294](../../../docs/LIMITS.md#L294)
- **implementation_navigation:** [`maximalReplyEncodedSize`](../../../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift); [`pwRunnerEncodeJSON`](../../../runner/Sources/PWRunnerCore/PWRunnerCoding.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runReplyMaximumTests`](../../../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift); path (test): [`main`](../../../tests/suites/witness_contract/check_max_target_reply.py); path (test): [`assert_composition`](../../../tests/suites/witness_contract/check_actor_compositions.py)
Behavioral claim:

> The production encoder sizes a conservative ordinary reply: 256 actions and disposition entries in eight phases, 512 retained validator records with each bounded scalar and raw line maximized, up to 768 association issues, per-phase diagnostics, and maximal profile capture. Separately encoded declaration/issuer, lifecycle-event, fresh-read, fresh-write, exec-observation and actor components are added without reclaiming ordinary fields. Actor components use the union of encoded success, failure, interruption and capture fixtures: eight actor records with full compiled-profile payloads, sixteen phase overheads, every event, transfer and resource at its capacity, aggregate disposition entries and issues, and ordinary-step actor identities. Bounded echoed strings use maximal escaping, native scalars use 20 decimal bytes, fixed actor vocabulary has a checked 128-byte ASCII ceiling, and each array has an explicit capacity. The actor capture allowance is compared with production encoding of a maximum receipt; missing capture fixtures and unclassified or oversized arrays fail. Ordinary controls separately encode valid exec evidence and fresh-write evidence on every slot. Mutually exclusive fields remain counted, so this is an upper bound, not a reachable reply. Every string key across all reply-shape documents must have a size policy. Real transport controls separately measure admitted ordinary, fresh-read, fresh-write, mixed native and actor capture workloads.


### controller_output — [docs/LIMITS.md:133](../../../docs/LIMITS.md#L133)

**Source claim (documentary quotation):**

> Captured bytes per stdout or stderr stream from the runner client, before text decoding. Stdout carries the versioned client capture, including base64 host bytes. Excess is marked truncated. Truncated client capture is not parsed, so submission remains unknown and no host evidence is inferred.

- **Category:** Queries and transport
- **Value / derivation:** 260,046,848 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Captured bytes per stdout or stderr stream from the runner client, before text decoding.
- **Scope assessment:** Each client stdout/stderr stream separately; not envelope-wide or process-memory limit.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Controller retention before text decoding/parsing; full stream buffered first per Premises.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Derived: three times `runner_reply_maximum`, rounded up to a whole 4 MiB; no flag.
- **Boundary consequence:** Excess is marked truncated. Truncated client capture is not parsed, so submission remains unknown and no host evidence is inferred.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q9: Derived arithmetic and all actor/client overhead need verification; retention is expressly not memory bound.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q9: Derived arithmetic and all actor/client overhead need verification; retention is expressly not memory bound.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:295](../../../docs/LIMITS.md#L295)
- **implementation_navigation:** [`RUNNER_CAPTURE_BYTES`](../../../controller/src/utils.rs)
- **permanent_checks_navigation:** value (test): [`documented_controller_limits`](../../../controller/src/run_flow.rs); path (test): [`valid_oversized_producer_is_receiver_loss_not_malformed_json`](../../../controller/src/runner_client.rs); path (test): [`main`](../../../tests/suites/witness_contract/check_max_target_reply.py); boundary (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
Behavioral claim:

> The byte prefix precedes lossy text decoding. This is a per-stream retention budget, not an envelope-wide cap or process-memory limit. The production maximal-capture control includes base64 expansion of the retained host reply at its full capacity and 256 bounded attempt/error records and requires the result to fit this cap. Independent receiver controls exercise oversized and malformed captures; normal maximal workloads separately establish actual host replies.


### policy_helper_output — [docs/LIMITS.md:134](../../../docs/LIMITS.md#L134)

**Source claim (documentary quotation):**

> Captured bytes per stdout or stderr stream from `sbpl-check`, before text decoding. Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply.

- **Category:** Queries and transport
- **Value / derivation:** 8,388,608 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Captured bytes per stdout or stderr stream from `sbpl-check`, before text decoding.
- **Scope assessment:** Each sbpl-check stdout/stderr stream separately; not process-memory limit.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Controller helper-output retention before text decode/JSON parse.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess is marked truncated. Truncated JSON stdout is not parsed as a complete reply.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:296](../../../docs/LIMITS.md#L296)
- **implementation_navigation:** [`HELPER_CAPTURE_BYTES`](../../../controller/src/utils.rs)
- **permanent_checks_navigation:** value (test): [`documented_controller_limits`](../../../controller/src/run_flow.rs); boundary (test): [`arbitrary_budgets_preserve_counts_at_every_unicode_cut`](../../../controller/src/utils.rs)
Behavioral claim:

> The byte prefix precedes lossy text decoding. This is a per-stream retention budget, not an envelope-wide cap or a process-memory limit. The shared receiver accepts an explicit per-stream retention budget for this producer; exact byte counts, truncation and JSON parse suppression are tested independently of the runner budget.


### validator_fault_context — [docs/LIMITS.md:135](../../../docs/LIMITS.md#L135)

**Source claim (documentary quotation):**

> Retained prefix of the first rejected validator frame, measured before base64 encoding. `frame_bytes`, `retained_bytes` and `context_truncated` describe how much context was retained.

- **Category:** Queries and transport
- **Value / derivation:** 256 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained prefix of the first rejected validator frame, measured before base64 encoding.
- **Scope assessment:** First rejected frame's diagnostic prefix; collection lifetime not restated in row.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Rejected-frame diagnostic retention before base64 encoding.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Only bounded prefix retained; frame_bytes, retained_bytes and context_truncated expose context loss.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:297](../../../docs/LIMITS.md#L297)
- **implementation_navigation:** [`decodeValidatorFrames`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift)
Behavioral claim:

> Exact and over-limit invalid-frame context controls; no rejected bytes become verdicts.


### validator_reply_frame — [docs/LIMITS.md:136](../../../docs/LIMITS.md#L136)

**Source claim (documentary quotation):**

> UTF-8 bytes in one NDJSON frame, before parsing. An overlong frame is rejected with bounded context; earlier complete records remain.

- **Category:** Queries and transport
- **Value / derivation:** 8,192 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** UTF-8 bytes in one NDJSON frame, before parsing.
- **Scope assessment:** Each validator NDJSON frame before parsing, not whole stream.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Validator reply-frame receiver/decoder before frame acceptance.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** An overlong frame is rejected with bounded context; earlier complete records remain.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:312](../../../docs/LIMITS.md#L312)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> UTF-8 bytes in one NDJSON frame, before parsing. An overlong frame is rejected with bounded context; earlier complete records remain.


### validator_records_per_query — [docs/LIMITS.md:137](../../../docs/LIMITS.md#L137)

**Source claim (documentary quotation):**

> Retained-record allowance is twice the number of queries actually sent in that phase; at most 512 records across a production run. The first excess record produces a decode fault; no excess record enters association.

- **Category:** Queries and transport
- **Value / derivation:** 2 items
- **Unit:** items
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Two retained records per actual query sent; maximum 512 per production run.
- **Scope assessment:** Per-phase allowance from actual queries sent; max 512 across run, no phase-capacity multiplier.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Validator record retention/association boundary.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** The first excess record produces a decode fault; no excess record enters association.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:313](../../../docs/LIMITS.md#L313)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Retained-record allowance is twice the number of queries actually sent in that phase; at most 512 records across a production run. The first excess record produces a decode fault; no excess record enters association.


### validator_reply_bytes_per_query — [docs/LIMITS.md:138](../../../docs/LIMITS.md#L138)

**Source claim (documentary quotation):**

> Twice the frame bound per actual query; at most 4,194,304 retained stdout bytes across a production run. The first read crossing the cap closes collection with byte_limit; its cutoff fragment is never decoded as a complete frame.

- **Category:** Queries and transport
- **Value / derivation:** 16,384 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Twice frame-bound bytes per actual query; maximum 4194304 retained bytes per production run.
- **Scope assessment:** Per-phase retained stdout from actual queries sent; max 4194304 across run.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Validator stdout retention while reading, before cutoff-fragment decoding.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** The first read crossing the cap closes collection with byte_limit; its cutoff fragment is never decoded as a complete frame.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:314](../../../docs/LIMITS.md#L314)
- **implementation_navigation:** [`runValidator`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Twice the frame bound per actual query; at most 4,194,304 retained stdout bytes across a production run. The first read crossing the cap closes collection with byte_limit; its cutoff fragment is never decoded as a complete frame.


### validator_reply_step_id — [docs/LIMITS.md:139](../../../docs/LIMITS.md#L139)

**Source claim (documentary quotation):**

> Bytes in a decoded validator step_id string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.

- **Category:** Queries and transport
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Bytes in a decoded validator step_id string, when present.
- **Scope assessment:** Each present decoded validator record step_id, not submitted request ID.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Decoded validator record string admission.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Entire overlong record rejected with bounded context; accepted string values never truncated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:315](../../../docs/LIMITS.md#L315)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Bytes in a decoded validator step_id string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.


### validator_reply_operation — [docs/LIMITS.md:140](../../../docs/LIMITS.md#L140)

**Source claim (documentary quotation):**

> Bytes in a decoded validator operation string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.

- **Category:** Queries and transport
- **Value / derivation:** 127 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Bytes in a decoded validator operation string, when present.
- **Scope assessment:** Each present decoded validator record operation.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Decoded validator record string admission.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Entire overlong record rejected with bounded context; accepted string values never truncated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:316](../../../docs/LIMITS.md#L316)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Bytes in a decoded validator operation string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.


### validator_reply_filter_type — [docs/LIMITS.md:141](../../../docs/LIMITS.md#L141)

**Source claim (documentary quotation):**

> Bytes in a decoded validator filter_type string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.

- **Category:** Queries and transport
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Bytes in a decoded validator filter_type string, when present.
- **Scope assessment:** Each present decoded validator record filter_type.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Decoded validator record string admission.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Entire overlong record rejected with bounded context; accepted string values never truncated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:317](../../../docs/LIMITS.md#L317)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Bytes in a decoded validator filter_type string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.


### validator_reply_filter_value — [docs/LIMITS.md:142](../../../docs/LIMITS.md#L142)

**Source claim (documentary quotation):**

> Bytes in a decoded validator filter_value string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.

- **Category:** Queries and transport
- **Value / derivation:** 1,023 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Bytes in a decoded validator filter_value string, when present.
- **Scope assessment:** Each present decoded validator record filter_value.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Decoded validator record string admission.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Entire overlong record rejected with bounded context; accepted string values never truncated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:318](../../../docs/LIMITS.md#L318)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Bytes in a decoded validator filter_value string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.


### validator_reply_outcome — [docs/LIMITS.md:143](../../../docs/LIMITS.md#L143)

**Source claim (documentary quotation):**

> Bytes in a decoded validator outcome string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.

- **Category:** Queries and transport
- **Value / derivation:** 63 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Bytes in a decoded validator outcome string, when present.
- **Scope assessment:** Each present decoded validator record outcome.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Decoded validator record string admission.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Entire overlong record rejected with bounded context; accepted string values never truncated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:319](../../../docs/LIMITS.md#L319)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Bytes in a decoded validator outcome string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.


### validator_reply_error — [docs/LIMITS.md:144](../../../docs/LIMITS.md#L144)

**Source claim (documentary quotation):**

> Bytes in a decoded validator error string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.

- **Category:** Queries and transport
- **Value / derivation:** 511 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Bytes in a decoded validator error string, when present.
- **Scope assessment:** Each present decoded validator record error.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Decoded validator record string admission.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Entire overlong record rejected with bounded context; accepted string values never truncated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:320](../../../docs/LIMITS.md#L320)
- **implementation_navigation:** [`ValidatorReplyLimits`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runValidatorEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift)
Behavioral claim:

> Bytes in a decoded validator error string, when present. The entire overlong record is rejected with bounded context; accepted values are never truncated.


### extension_token_storage — [docs/LIMITS.md:145](../../../docs/LIMITS.md#L145)

**Source claim (documentary quotation):**

> Fixed token array including its terminating NUL; never part of a retained reply. Empty, oversized or malformed publications cannot supply a consumed token.

- **Category:** Queries and transport
- **Value / derivation:** 16,384 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Fixed token-array bytes including terminating NUL.
- **Scope assessment:** One transient token array; actor/declaration applicability not explicit, never retained reply.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Publication/framing checks implied; precise producer/receiver enforcement point not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Empty, oversized or malformed publication cannot supply a consumed token.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q7: Token payload limit may be shared, but this row does not identify actor/declaration applicability or actor malformed-publication status.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q7: Token payload limit may be shared, but this row does not identify actor/declaration applicability or actor malformed-publication status.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:334](../../../docs/LIMITS.md#L334)
- **implementation_navigation:** [`PW_EXTENSION_TOKEN_BYTES`](../../../controller/tools/pw_probe_runner/pw_extension_channel.h)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`run_case`](../../../tests/suites/witness_contract/check_extension_boundaries.py)
Behavioral claim:

> Production issuer/worker controls cover maximum payload, over-capacity or malformed framing, deadline, missing publication, native failure and independent cleanup/confinement.


### extension_token_payload — [docs/LIMITS.md:146](../../../docs/LIMITS.md#L146)

**Source claim (documentary quotation):**

> Nonempty token bytes excluding the required trailing NUL. Larger native results report `token_oversized`; malformed delivery is unavailable.

- **Category:** Queries and transport
- **Value / derivation:** 16,383 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Nonempty token bytes excluding required trailing NUL.
- **Scope assessment:** One native token result/delivery; form-specific public status applicability not explicit.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Native token-result size and delivery framing checks implied; precise enforcing process not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Larger native results report `token_oversized`; malformed delivery is unavailable.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q7: Verify whether token_oversized is the public status in both forms; no implementation inference.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q7: Verify whether token_oversized is the public status in both forms; no implementation inference.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:335](../../../docs/LIMITS.md#L335)
- **implementation_navigation:** [`PW_EXTENSION_TOKEN_BYTES`](../../../controller/tools/pw_probe_runner/pw_extension_channel.h)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`run_case`](../../../tests/suites/witness_contract/check_extension_boundaries.py)
Behavioral claim:

> Production issuer/worker controls cover maximum payload, over-capacity or malformed framing, deadline, missing publication, native failure and independent cleanup/confinement.


### extension_channel — [docs/LIMITS.md:147](../../../docs/LIMITS.md#L147)

**Source claim (documentary quotation):**

> Logical mapped channel with header, resolved path and token array. The OS backing object may round its storage up. Insufficient backing size or invalid channel geometry cannot supply a token.

- **Category:** Queries and transport
- **Value / derivation:** 17,472 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Logical header + resolved path + token-array bytes; OS backing may round up.
- **Scope assessment:** One logical mapped channel; resolved-path layout suggests declaration path but form not explicit.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Backing-size/geometry validation before token use; checking process not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Insufficient backing size or invalid channel geometry cannot supply a token.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q7: Logical resolved-path channel appears declaration-specific; distinguish it from actor authority regions.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q7: Logical resolved-path channel appears declaration-specific; distinguish it from actor authority regions.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:336](../../../docs/LIMITS.md#L336)
- **implementation_navigation:** [`PW_EXTENSION_CHANNEL_BYTES`](../../../controller/tools/pw_probe_runner/pw_extension_channel.h)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`run_case`](../../../tests/suites/witness_contract/check_extension_boundaries.py)
Behavioral claim:

> Production issuer/worker controls cover maximum payload, over-capacity or malformed framing, deadline, missing publication, native failure and independent cleanup/confinement.


### reservation_control_bytes — [docs/LIMITS.md:148](../../../docs/LIMITS.md#L148)

**Source claim (documentary quotation):**

> Encoded reservation request or control reply, before JSON decoding. Excess is a protocol failure. No oversized control can grant execution.

- **Category:** Queries and transport
- **Value / derivation:** 65,536 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Encoded reservation request or control reply, before JSON decoding.
- **Scope assessment:** Each reservation request/control reply before JSON decode.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Control-message protocol admission before JSON decoding.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess is a protocol failure. No oversized control can grant execution.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:344](../../../docs/LIMITS.md#L344)
- **implementation_navigation:** [`controlBytes`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### client_error_message — [docs/LIMITS.md:149](../../../docs/LIMITS.md#L149)

**Source claim (documentary quotation):**

> Retained error prose at a Unicode boundary. Excess is truncated with message_truncated; error stage, domain and native code remain separate observations.

- **Category:** Queries and transport
- **Value / derivation:** 1,024 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained error prose at a Unicode boundary.
- **Scope assessment:** Each retained client transport error message; independent of stage/domain/code.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client error-prose retention at Unicode boundary.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess is truncated with message_truncated; error stage, domain and native code remain separate observations.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:345](../../../docs/LIMITS.md#L345)
- **implementation_navigation:** [`errorMessageBytes`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### client_error_domain — [docs/LIMITS.md:150](../../../docs/LIMITS.md#L150)

**Source claim (documentary quotation):**

> Retained native error domain at a Unicode boundary. Excess is truncated with domain_truncated. No arbitrary userInfo dictionary is retained.

- **Category:** Queries and transport
- **Value / derivation:** 128 UTF-8 bytes
- **Unit:** UTF-8 bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained native error domain at a Unicode boundary.
- **Scope assessment:** Each retained native error domain; arbitrary userInfo excluded.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client native-domain retention at Unicode boundary.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Excess truncated with domain_truncated; arbitrary userInfo not retained.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:346](../../../docs/LIMITS.md#L346)
- **implementation_navigation:** [`errorDomainBytes`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### client_reply_retention — [docs/LIMITS.md:151](../../../docs/LIMITS.md#L151)

**Source claim (documentary quotation):**

> Host result bytes retained before base64 encoding in the client capture. Excess is explicitly truncated and cannot be admitted as a complete host result; received and retained byte counts remain distinct.

- **Category:** Queries and transport
- **Value / derivation:** 88,080,384 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Host result bytes retained before base64 encoding in the client capture.
- **Scope assessment:** One host reply body inside client capture, separate from outer controller cap.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Client host-reply retention before encoding capture.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed; must cover the informative maximal reply.
- **Boundary consequence:** Excess is explicitly truncated and cannot be admitted as a complete host result; received and retained byte counts remain distinct.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q9: Fixed cap claims to cover maximal reply; verify production encoding separately from documentation.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q9: Fixed cap claims to cover maximal reply; verify production encoding separately from documentation.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:347](../../../docs/LIMITS.md#L347)
- **implementation_navigation:** [`runnerReplyBytes`](../../../runner/Sources/PWRunnerCore/PWRunnerTransport.swift); [`REPLY_CAPTURE_BYTES`](../../../controller/src/runner_client.rs); [`REPLY_BYTES`](../../../tests/lib/runner_client_capture.py)
- **permanent_checks_navigation:** value (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); boundary (test): [`runReservationAdmissionTests`](../../../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift); value (test): [`reply_capture_limit_matches_documented_capacity`](../../../controller/src/runner_client.rs)
Behavioral claim:

> Production constants and independent at/over-boundary controls retain actual decisions. Client controls exercise production session state; host controls exercise shared reservation state. These constructed controls do not establish live XPC delivery.


### exec_stream — [docs/LIMITS.md:157](../../../docs/LIMITS.md#L157)

**Source claim (documentary quotation):**

> Retained stdout or stderr bytes for each exec child. An overflow marker occupies part of this allowance. Excess output is not retained.

- **Category:** Evidence capture
- **Value / derivation:** 1,023 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained stdout or stderr bytes for each exec child.
- **Scope assessment:** Each exec child's stdout/stderr separately; marker inside cap, terminating NUL outside per coverage.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker child-output buffer retention; coverage says draining continues after retention stops.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** An overflow marker occupies part of this allowance. Excess output is not retained.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:298](../../../docs/LIMITS.md#L298)
- **implementation_navigation:** [`PW_SHM_CHILD_OUTPUT_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runCWorkerTests`](../../../runner/Tests/PWRunnerCoreTests/CWorkerTests.swift)
Behavioral claim:

> Each text buffer reserves its terminating NUL outside this payload limit. Additional output is drained even after retention stops. Small stdout/stderr capture is tested. Overflow truncation and the exact retained-prefix/marker split are source-inspected.


### worker_diagnostic — [docs/LIMITS.md:158](../../../docs/LIMITS.md#L158)

**Source claim (documentary quotation):**

> Retained primary diagnostic bytes. The reply reports retained length and truncation state; this is not a complete transcript.

- **Category:** Evidence capture
- **Value / derivation:** 4,095 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained primary diagnostic bytes.
- **Scope assessment:** Each primary worker diagnostic; actor aggregate handling not explicit in row.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Worker primary diagnostic buffer retention; coverage states bounded truncation controls.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Retained length and truncation state reported; diagnostic is not complete transcript.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q10: Per-worker scope plausible but actor multiplicity/aggregation must be checked when validating reply bound.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q10: Per-worker scope plausible but actor multiplicity/aggregation must be checked when validating reply bound.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:299](../../../docs/LIMITS.md#L299)
- **implementation_navigation:** [`PW_SHM_DIAGNOSTIC_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`runWorkerEvidenceTests`](../../../runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift)
Behavioral claim:

> The diagnostic buffer reserves its terminating NUL outside the payload limit. Bounded diagnostic/truncation controls in the Swift worker evidence tests.


### compiled_profile — [docs/LIMITS.md:159](../../../docs/LIMITS.md#L159)

**Source claim (documentary quotation):**

> Raw bytecode bytes in an optional compiled-object receipt, before base64 encoding. Oversized or unsupported objects leave capture unavailable without preventing policy application.

- **Category:** Evidence capture
- **Value / derivation:** 1,048,576 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Raw bytecode bytes in an optional compiled-object receipt, before base64 encoding.
- **Scope assessment:** Each optional compiled-object receipt; actor multiplicity not explicitly restated.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Worker capture before applying same object per coverage; guide separately states host publication checks.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Oversized/unsupported object makes capture unavailable without blocking application. Guide adds identity/checksum/exit/apply publication prerequisites.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q10: Optional receipt limit versus per-actor receipt multiplicity and publication prerequisites require guide cross-reading.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q10: Optional receipt limit versus per-actor receipt multiplicity and publication prerequisites require guide cross-reading.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:300](../../../docs/LIMITS.md#L300)
- **implementation_navigation:** [`PW_SHM_CAPTURE_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (control): [`main`](../../../tests/suites/runner_abi_layout/capture.c)
Behavioral claim:

> Capture supports nonempty single-profile (type 0) objects; it runs before applying the same object. Failed capture leaves application unchanged. Independently constructed object controls cover exact, excessive and unsupported captures.


### observed_path — [docs/LIMITS.md:160](../../../docs/LIMITS.md#L160)

**Source claim (documentary quotation):**

> Retained bytes in each worker-observed path. Path observation can be absent or bounded; a host-side path diagnostic is a separate observation.

- **Category:** Evidence capture
- **Value / derivation:** 1,023 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained bytes in each worker-observed path.
- **Scope assessment:** Each worker-observed path; host path diagnostic is separate.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker path-buffer use is source-inspected per coverage; exact excess-handling mechanism not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Observation may be absent or bounded. Not stated: exact over-capacity status or truncation marker.
- **Boundary status:** partly_unstated
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:301](../../../docs/LIMITS.md#L301)
- **implementation_navigation:** [`PW_SHM_OBSERVED_PATH_MAX`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift)
Behavioral claim:

> The per-step C path-buffer payload excludes its terminating NUL. Source-inspected buffer use; no exact path-length behavior claim is tested.


### attempt_error — [docs/LIMITS.md:161](../../../docs/LIMITS.md#L161)

**Source claim (documentary quotation):**

> Retained bytes in each worker attempt error message. Error text is bounded; structured result and status fields remain separate.

- **Category:** Evidence capture
- **Value / derivation:** 255 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Retained bytes in each worker attempt error message.
- **Scope assessment:** Each worker attempt error message; structured status separate.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker bounded error formatting is source-inspected per coverage; exact truncation mechanism not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Text bounded while structured status stays separate. Not stated: exact over-capacity marker.
- **Boundary status:** partly_unstated
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:302](../../../docs/LIMITS.md#L302)
- **implementation_navigation:** [`PW_SHM_ERROR_MAX`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h)
- **permanent_checks_navigation:** value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift)
Behavioral claim:

> The per-step C error-buffer payload excludes its terminating NUL. Source-inspected bounded formatting; no exact error-text boundary claim is tested.


### phase_records — [docs/LIMITS.md:162](../../../docs/LIMITS.md#L162)

**Source claim (documentary quotation):**

> Fixed phase records in each worker's shared header. The legacy form admits eight phases (`phase_count`); the remaining records are internal support for the actor form under development and no public request reaches them. A worker refuses a header naming more phases than its records before application.

- **Category:** Evidence capture
- **Value / derivation:** 16 items
- **Unit:** items
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Number of fixed phase records in each shared header.
- **Scope assessment:** Each worker shared header; public reachability claim conflicts with actor 16-phase admission.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker header phase-count validation before application.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Worker refuses header exceeding records before application; public actor reachability remains contradictory.
- **Boundary status:** documented_unverified
- **Disposition:** question
- **Reason:** Q1: Public-unreachable/under-development statement conflicts with actor admission and this row own coverage claim.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q1: Public-unreachable/under-development statement conflicts with actor admission and this row own coverage claim.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:308](../../../docs/LIMITS.md#L308)
- **implementation_navigation:** [`PWShmLayout`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py)
Behavioral claim:

> Fixed phase records in each worker shared header. The declaration form admits eight phases; actor-form visits use the same records under their own admitted phase limit. A worker refuses a header naming more phases than its records before application.


### authority_slot_bytes — [docs/LIMITS.md:163](../../../docs/LIMITS.md#L163)

**Source claim (documentary quotation):**

> One token publication slot in an actor's authority region: a fixed header and the token buffer. A region holds one outbound slot per admitted issue and one inbound slot per admitted delivery to that actor, with distinct bounded transfer answer cells; nothing in it enters the reply.

- **Category:** Evidence capture
- **Value / derivation:** 16,448 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Fixed header plus token buffer bytes per slot; one outbound per issue and inbound per recipient delivery.
- **Scope assessment:** One actor authority slot, not entire region; header/answer-cell total formula not supplied.
- **Scope status:** ambiguous_or_partly_unstated
- **Enforcement assessment:** Fixed region layout stated; separate byte-capacity enforcement point not stated.
- **Enforcement status:** partly_unstated
- **Control (documentary):** Fixed.
- **Boundary consequence:** Not stated: separate over-capacity response for slot bytes. Slot contents never enter reply; guide separately describes region/custody setup failure.
- **Boundary status:** partly_unstated
- **Disposition:** question
- **Reason:** Q8: Per-slot size given, but complete region/header/answer-cell derivation and resource-failure boundary not provided.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Q8: Per-slot size given, but complete region/header/answer-cell derivation and resource-failure boundary not provided.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:309](../../../docs/LIMITS.md#L309)
- **implementation_navigation:** [`PWAuthorityLayout`](../../../runner/Sources/PWRunnerCore/AuthorityCustody.swift); [`PW_AUTHORITY_SLOT_BYTES`](../../../controller/tools/pw_probe_runner/pw_authority_region.h)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); path (test): [`c_swift_layout_agreement`](../../../tests/suites/runner_abi_layout/run.sh)
Behavioral claim:

> Published outbound bytes remain immutable until the host copies or rejects and erases them. Inbound consumption/erasure follows host settlement. Shared teardown erasure requires confirmed worker quiescence; private custody is erased independently. The layout suite compares compiled C geometry with the Swift mirror.


### phase_publications — [docs/LIMITS.md:164](../../../docs/LIMITS.md#L164)

**Source claim (documentary quotation):**

> Sixteen fixed 32-byte phase records within each shared header, one per visit an actor can be activated in; the legacy form uses the first eight. The legacy and actor-form phase caps prevent excess publication storage.

- **Category:** Evidence capture
- **Value / derivation:** 512 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Sixteen fixed 32-byte records: 16 × 32 = 512 bytes.
- **Scope assessment:** Each shared header; sixteen actor visit records, legacy first eight.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Legacy/actor phase admission caps prevent excess publication storage per row.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Phase admission caps prevent excess storage; no independent publication-byte refusal stated.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:310](../../../docs/LIMITS.md#L310)
- **implementation_navigation:** [`PWShmLayout`](../../../runner/Sources/PWRunnerCore/CWorker.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); boundary (test): [`runPhaseProtocolTests`](../../../runner/Tests/PWRunnerCoreTests/PhaseProtocolTests.swift)
Behavioral claim:

> Sixteen fixed 32-byte phase records within each shared header, one per visit an actor can be activated in; the legacy form uses the first eight. The legacy and actor-form phase caps prevent excess publication storage.


### fresh_read_bytes — [docs/LIMITS.md:165](../../../docs/LIMITS.md#L165)

**Source claim (documentary quotation):**

> At most one read from a freshly opened descriptor; content_hex encodes only the returned prefix. Longer files remain readable experiments; the bounded result does not claim complete file contents.

- **Category:** Evidence capture
- **Value / derivation:** 64 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Returned prefix from at most one read of up to 64 bytes.
- **Scope assessment:** Each read_fresh on freshly opened descriptor; not file size admission.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Worker's single bounded native read/retention; coverage names prefix-boundary controls.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Longer files remain valid experiments; content_hex represents only returned prefix, not full contents.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:339](../../../docs/LIMITS.md#L339)
- **implementation_navigation:** [`PW_SHM_FRESH_READ_BYTES`](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h); [`PWExtensionLimits`](../../../runner/Sources/PWRunnerCore/PWRunnerExtension.swift)
- **permanent_checks_navigation:** value (test): [`runLimitsContractTests`](../../../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift); value (test): [`compare`](../../../tests/suites/runner_abi_layout/limits.py); boundary (test): [`run_targets`](../../../tests/suites/witness_contract/check_extensions.py)
Behavioral claim:

> Known file contents just below, at and above the prefix capacity, descriptor identity and unchanged source bytes through standard and BYOXPC CLI.


### helper_source — [docs/LIMITS.md:171](../../../docs/LIMITS.md#L171)

**Source claim (documentary quotation):**

> Top-level source bytes read by the diagnostic helper; not the runner policy cap. policy_too_large with null compile and import_inventory groups; no compile verdict.

- **Category:** Diagnostic helpers
- **Value / derivation:** 4,194,304 bytes
- **Unit:** bytes
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Top-level source bytes read by the diagnostic helper; not the runner policy cap.
- **Scope assessment:** One sbpl-check top-level source, not runner policy cap or compiler import closure.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Diagnostic helper source admission before compile/import inventory.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Oversize yields policy_too_large, null compile/import_inventory, no compile verdict.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:303](../../../docs/LIMITS.md#L303)
- **implementation_navigation:** [`MAX_SBPL_SOURCE_BYTES`](../../../controller/src/sbpl_imports.rs)
- **permanent_checks_navigation:** value (test): [`documented_helper_limits`](../../../controller/src/bin/sbpl-check.rs); path (test): [`source_byte_cap_counts_utf8_bytes_not_characters`](../../../controller/src/bin/sbpl-check.rs)
Behavioral claim:

> Oversized input is tested through the shipped helper and fallback CLI; exact boundary behavior is source-inspected.


### helper_import_depth — [docs/LIMITS.md:172](../../../docs/LIMITS.md#L172)

**Source claim (documentary quotation):**

> Import depth in the helper inventory, starting at 0. Depth 8 is the first depth replaced by a depth-limit diagnostic. The affected branch stops and `import_inventory.truncated` is set. This does not limit compilation of imports.

- **Category:** Diagnostic helpers
- **Value / derivation:** 8 levels
- **Unit:** levels
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Inventory depth, starting at zero; first excluded depth is eight.
- **Scope assessment:** Each branch of helper import inventory, not libsandbox compilation.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Helper import traversal depth check.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** At depth eight, branch stops with depth diagnostic and import_inventory.truncated; compilation unaffected.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:304](../../../docs/LIMITS.md#L304)
- **implementation_navigation:** [`IMPORT_MAX_DEPTH`](../../../controller/src/sbpl_imports.rs)
- **permanent_checks_navigation:** value (test): [`documented_helper_limits`](../../../controller/src/bin/sbpl-check.rs); path (test): [`resolve_imports_truncates_on_depth_cap`](../../../controller/src/sbpl_imports.rs)
Behavioral claim:

> At depth 8 the helper records a diagnostic instead of reading or expanding that file; libsandbox compilation has its own import resolution. Deep import-chain control in the helper unit tests.


### helper_import_count — [docs/LIMITS.md:173](../../../docs/LIMITS.md#L173)

**Source claim (documentary quotation):**

> Import-inventory records, including unresolved and error records. Repeated files or names are listed once. Further inventory stops and `import_inventory.truncated` is set. This does not limit compilation of imports.

- **Category:** Diagnostic helpers
- **Value / derivation:** 64 records
- **Unit:** records
- **Refusal field / location:** Not applicable: not a specimen admission row.
- **Counting rule:** Number of inventory records, including errors/unresolved records; repeated file/name deduplicated.
- **Scope assessment:** Entire helper import inventory, not compiler's resolved import set.
- **Scope status:** stated_or_cross_referenced
- **Enforcement assessment:** Helper import inventory record accumulation/deduplication.
- **Enforcement status:** documented_unverified
- **Control (documentary):** Fixed.
- **Boundary consequence:** Further inventory stops at cap and truncated flag set; compilation unaffected.
- **Boundary status:** documented_unverified
- **Disposition:** retain
- **Reason:** No internal conflict identified in this bounded documentation audit. Retain in inventory; not a verification of value or behavior.
- **Verification needed:** Verify actual constant/default or derivation, counted objects/bytes, relevant form, boundary consequence and named controls against authoritative implementation and representative boundary evidence. Confirm the documentary coverage strength and any stated source-only or untested qualification.

**Stated evidence (documentary claims, unverified):**

- **location:** [docs/LIMITS.md:305](../../../docs/LIMITS.md#L305)
- **implementation_navigation:** [`IMPORT_MAX_COUNT`](../../../controller/src/sbpl_imports.rs)
- **permanent_checks_navigation:** value (test): [`documented_helper_limits`](../../../controller/src/bin/sbpl-check.rs); path (test): [`resolve_imports_truncates_on_count_cap`](../../../controller/src/sbpl_imports.rs)
Behavioral claim:

> The helper traversal deduplicates visited files/names and accumulates at most this many records; libsandbox compilation does not use that inventory as a limit. Import-count exhaustion control in the helper unit tests.


## Shared explanation, interaction and premise ledger

All 27 non-table prose blocks remain, and all 93 coverage rows remain attached above.

### P01 — [docs/LIMITS.md:4](../../../docs/LIMITS.md#L4) — Opening

> A specimen that `libsandbox` would compile can still be refused here, or run
> with less evidence than it produced. This section lists every such limit with
> its value, what it counts and what happens at the boundary.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q11: Completeness promise requires separate missing-limit search; semantic restrictions may fit broad promise.

### P02 — [docs/LIMITS.md:8](../../../docs/LIMITS.md#L8) — Opening

> Capacity refusals carry `data.runner_result.admission_failure`, which names the
> `field`, the `actual` count, the `maximum` and the `unit`, with location details
> where available and `origin: "runner_host"`. Find that field in the "Refusal
> names" column of the Specimen admission table; the row says what was measured
> and which location fields are reported. To check a specimen before submitting
> it, compare it with the same rows.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P03 — [docs/LIMITS.md:15](../../../docs/LIMITS.md#L15) — Opening

> Request files must be UTF-8 JSON. A file containing invalid UTF-8 yields exit
> code 2 and `result.normalized_outcome: "tool_error"`, with an error beginning
> `failed to read request.json` and `data.runner_result: null`. It has no
> `admission_failure` to look up.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P04 — [docs/LIMITS.md:22](../../../docs/LIMITS.md#L22) — How to read the tables

> - Capacities are inclusive maxima unless the row says otherwise: a step ID
>   of <!-- span limits.step_id.value -->63<!-- /span --> UTF-8 bytes fits, and any longer step ID exceeds its limit. UTF-8 counts measure decoded
>   strings rather than JSON escapes or characters. Rows labeled `bytes` specify
>   whether they count raw output, bytecode or a calculated allowance. String
>   capacities exclude any terminating NUL.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P05 — [docs/LIMITS.md:27](../../../docs/LIMITS.md#L27) — How to read the tables

> - Time rows distinguish defaults, elapsed monotonic deadlines, nominal waits
>   and unenforced allowances. Monotonic deadlines are unaffected by wall-clock
>   adjustments. The C worker's release wait and exec allowances count continuous
>   Mach time, which includes system sleep; host, validator and controller waits
>   keep their own clocks, and no worker time is compared with them. Nominal waits
>   can take longer than their listed duration; each row describes what expiry does.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P06 — [docs/LIMITS.md:33](../../../docs/LIMITS.md#L33) — How to read the tables

> - The Control column describes `policy-witness` flags using four words.
>   "Fixed" means no flag changes the value in this build. "Flag" names the flag
>   that does. "Derived" means the value follows from another row.
>   "Not enforced" means the number is informative.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P07 — [docs/LIMITS.md:37](../../../docs/LIMITS.md#L37) — How to read the tables

> - Specimen admission answers whether a specimen fits this build's capacities
>   and why one did not. A capacity refusal names one field, has empty `steps`
>   and carries no worker or validator subprocess record. PolicyWitness never
>   truncates a plan to fit.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P08 — [docs/LIMITS.md:41](../../../docs/LIMITS.md#L41) — How to read the tables

> - Execution budgets describe waits and deadlines within a run. Some expiries
>   lead to cleanup or missing results; the readiness hint can expire while the
>   run continues. The nominal release margin has no expiry of its own.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P09 — [docs/LIMITS.md:44](../../../docs/LIMITS.md#L44) — How to read the tables

> - Queries and transport describe query sizes and received output. The rows
>   identify rejected queries, truncated output and unavailable parsing. Truncated JSON is not parsed as a complete reply.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P10 — [docs/LIMITS.md:46](../../../docs/LIMITS.md#L46) — How to read the tables

> - Evidence capture bounds optional evidence: child output and
>   compiled-object receipts. Excess can retain a prefix with a truncation marker
>   or make capture unavailable, as the row describes. Attempt
>   status and `sandbox_check` verdicts are unchanged by these evidence limits.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P11 — [docs/LIMITS.md:50](../../../docs/LIMITS.md#L50) — How to read the tables

> - Diagnostic helpers lists the limits of `sbpl-check`, which runs only after an
>   XPC error. This is independent of the normal admission path, and the
>   helper's import inventory does not control how
>   `libsandbox` resolves or compiles imports.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P12 — [docs/LIMITS.md:179](../../../docs/LIMITS.md#L179) — Interactions that matter

> - Budgets nest, and one flag changes one of them. `--timeout-ms` sets
>   `client_rpc_wait`, which also bounds external host re-acquisition. The worker polling
>   window `worker_sentinel_wait`, the validator deadline `validator_io_wait`,
>   the release wait `worker_proceed_wait` and the exec budgets keep their own
>   values, so no number here is an end-to-end runtime. The reply records the
>   client span in `data.runner_client.started_at_unix_ms` and
>   `ended_at_unix_ms`; an expired client wait yields `xpc_timeout`.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q5: Generic account omits actor setup/schedule/exchange/lifetime layers or requires cross-reading.

### P13 — [docs/LIMITS.md:186](../../../docs/LIMITS.md#L186) — Interactions that matter

> - Extension issuance precedes worker creation.
>   Its <!-- span limits.extension_issuer_wait.value_unit -->5,000 milliseconds<!-- /span -->
>   wait starts after the issuer spawns; target preparation and the spawn call
>   precede that clock. Issuer cleanup can overrun the wait. This work consumes
>   the client's reply window but none of the later worker or phase collection
>   budgets. A client timeout does not cancel issuance or its cleanup.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q3: Unqualified issuance ordering needs declaration/actor distinction.

### P14 — [docs/LIMITS.md:192](../../../docs/LIMITS.md#L192) — Interactions that matter

> - Phases share one total action/query capacity and a cumulative collection
>   allowance of <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span -->.
>   Each eligible phase gets a fresh validator; its I/O deadline is capped by the
>   remaining allowance. Planning and cleanup consume this allowance, but cleanup
>   and scheduling can overrun it. Exhaustion leaves later predictions unavailable
>   while attempts may still run. Each worker arrival starts its
>   own <!-- span limits.worker_proceed_wait.value_unit -->60,000 milliseconds<!-- /span -->
>   release wait; stale releases cannot satisfy it. The host's sentinel polling
>   excludes every synchronous collection, and the worker's exec budget excludes
>   every measured release wait. Client timeout still cancels none of this work.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q5: Generic account omits actor setup/schedule/exchange/lifetime layers or requires cross-reading.

### P15 — [docs/LIMITS.md:202](../../../docs/LIMITS.md#L202) — Interactions that matter

> - Validator storage scales with queries actually sent, never with the phase
>   capacity multiplied by the action capacity. Frame and string rejection retain
>   earlier complete records and bounded fault context; the stdout byte cutoff
>   closes collection with `byte_limit` and discards any incomplete cutoff frame.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P16 — [docs/LIMITS.md:206](../../../docs/LIMITS.md#L206) — Interactions that matter

> - Output budgets mark, they never silently cut. Each receiver reports the
>   budget it applied in `capture_limit_bytes` (`controller_output`,
>   `policy_helper_output`). Output beyond it is marked truncated, and a
>   truncated JSON stream is not parsed as a reply.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P17 — [docs/LIMITS.md:210](../../../docs/LIMITS.md#L210) — Interactions that matter

> - One refusal names the first failing field. When a specimen exceeds several
>   admission limits, the order is: top-level metadata (`specimen_id`,
>   `request_label`), extension declaration count and declaration strings, then
>   lifecycle-action strings and `test_override_path` executable overrides,
>   then phase count, total action count, phase identities
>   and parameter counts (`phase_count`, `probe_steps`, `phase_id`, `policy_parameters`), then worker strings
>   (`policy_source`, `step_id`, `attempt_target`, exec arguments, parameter keys
>   and values), then host query
>   fields (`query_operation`, `query_filter_value`, `probe_plan_label`). A
>   refused value is never echoed shortened: an oversized `specimen_id` is
>   replaced by `<admission_refused>`, an oversized `run_kind` is omitted and an
>   oversized `policy.format` reads `unknown`.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q12: Stated refusal order lists legacy fields but omits actor admission gates; cannot infer first actor-form failure.

### P18 — [docs/LIMITS.md:222](../../../docs/LIMITS.md#L222) — Interactions that matter

> - The `policy_source`, `parameter_key`, `parameter_value`, `step_id`,
>   `attempt_target`, `exec_argument`, `query_operation`, `query_filter_value`,
>   `phase_id`, `extension_reference`, `extension_target` and `test_override_path`
>   limits also reject embedded NUL, as do lifecycle-action identities and operation
>   labels. For a string within
>   its byte capacity, that refusal reports unit `nul_bytes`, maximum 0 and the
>   same field. Metadata and labels (`specimen_id`, `request_label`,
>   `probe_plan_label`) permit escaped NUL at this gate; their
>   normal meaning rules still apply. Within the capacities above, other control
>   characters and valid Unicode survive request transport unchanged.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P19 — [docs/LIMITS.md:232](../../../docs/LIMITS.md#L232) — Interactions that matter

> - Exec steps share a budget and each child has a deadline. `exec_attempt_budget`
>   bounds all exec steps of a plan together and `exec_child_wait` bounds each
>   child; neither has a flag. A step the exhausted budget refuses reports
>   `exec_failed` with `ETIMEDOUT`, no `child_pid` and no sandbox attribution. A
>   child cut by its deadline fails the attempt but keeps any exit code that was
>   observed. A worker that dies first leaves the step's exec details
>   unpublished, which establishes neither that no child spawned nor that cleanup
>   succeeded.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P20 — [docs/LIMITS.md:242](../../../docs/LIMITS.md#L242) — Interactions that matter

> See the [user guide](../../../docs/PolicyWitness.md) for the request and response contracts.
> Tables are generated from [limits.json](../../../docs/limits.json).
> For edits to the inventory and shared prose, follow the
> [documentation guidance](../../../docs/AGENTS.md#editing-limits-and-shared-guide-content).

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P21 — [docs/LIMITS.md:251](../../../docs/LIMITS.md#L251) — Grounding and coverage

> Value checks compare the inventory with compiled constants, constructed defaults or actual returned bytes. Boundary checks exercise a limit and its consequence; path checks cover related behavior without proving the exact boundary. A source reference alone is not a value check. Coverage notes below identify where behavior remains source-inspected.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P22 — [docs/LIMITS.md:353](../../../docs/LIMITS.md#L353) — Premises behind the interactions

> The shared text above states only what a reader can observe in a reply. The
> mechanisms those statements rest on live here, each beside the symbol that
> implements it, so that a premise can be reopened when the platform changes.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P23 — [docs/LIMITS.md:357](../../../docs/LIMITS.md#L357) — Premises behind the interactions

> - Reply and output budgets. [`RUNNER_CAPTURE_BYTES`](../../../controller/src/utils.rs) is three times `runner_reply_maximum`
>   rounded up to a whole 4 MiB. The maximum is synthesized by
>   [`maximalReplyEncodedSize`](../../../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift)
>   from the field-complete <!-- span limits.probe_steps.value -->256<!-- /span -->-step reply fixture encoded by
>   `pwRunnerEncodeJSON`; it places fields that cannot co-occur side by side, so it
>   is an upper bound for the schema, and a reply string key added without a size
>   classification fails that test. Collection buffers the whole stream before
>   applying the controller capture budget; that budget is not a memory limit.
>   The validator driver independently caps retained bytes while reading; its
>   bounded decoded records and per-phase evidence are included in the maximum.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q9: Premise describes 256-step fixture, while coverage describes additional actor components; verify derivation, not just count.

### P24 — [docs/LIMITS.md:367](../../../docs/LIMITS.md#L367) — Premises behind the interactions

> - Admission order and echo. `CWorkerOrchestrator`'s [`admissionFailure`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift)
>   checks decoded requests before semantic validation or child process work.
>   Its `requestAdmissionFailure` checks metadata, extension declarations and
>   lifecycle-action strings, then executable overrides before plan/parameter
>   counts. [`workerAdmissionFailure`](../../../runner/Sources/PWRunnerCore/CWorker.swift) and the host
>   `queryAdmissionFailure` check worker strings and query fields. The service
>   ([PWRunnerService.swift](../../../runner/Sources/PWRunnerCore/PWRunnerService.swift))
>   and direct orchestration share this gate. Each string checks its UTF-8
>   capacity before its native-string constraint.
>   `AdmissionStringRule.requiresCString` selects the NUL guard:
>   native strings reject it, while host-only metadata and labels permit escaped
>   NUL before semantic validation. `AdmissionStringRule.safeEcho` sanitizes every
>   echoed metadata field independently of which diagnostic was selected.
>   Host-only metadata is echoed once per reply. The shared-memory string
>   slots ([pw_probe_runner_abi.h](../../../controller/tools/pw_probe_runner/pw_probe_runner_abi.h))
>   carry no length, so the host rule is the only NUL guard for them; the worker's
>   policy reader refuses a NUL on its own (`PW_FAILURE_SOURCE_NUL`, exit 9, offset
>   in detail) and a delivery whose length at EOF differs from the expected count
>   the host wrote into the header (`PW_FAILURE_SOURCE_LENGTH`, exit 11, received
>   count in detail) rather than compile a prefix. The validator
>   ([sb_api_validator.c](../../../controller/tools/sb_api_validator/sb_api_validator.c))
>   rejects raw controls, invalid UTF-8, malformed escapes and lone surrogates per
>   probe line while preserving the next physical line; admitted specimens cannot
>   produce such lines. Decoder failures report a bounded category and path, not
>   input-derived prose.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q12: Stated refusal order lists legacy fields but omits actor admission gates; cannot infer first actor-form failure.

### P25 — [docs/LIMITS.md:392](../../../docs/LIMITS.md#L392) — Premises behind the interactions

> - Exec budget and observation. [`PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h)
>   sits `PW_EXEC_ATTEMPT_BUDGET_MARGIN_MS` below the host polling window; the
>   margin is a configuration allowance, not an enforced timer. The worker keeps
>   one continuous-time domain in relative ticks: [`pw_clock_start`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h)
>   records the origin before worker setup, [`pw_timing_setup`](../../../controller/tools/pw_probe_runner/pw_worker_timing.h)
>   queries the Mach timebase once before the policy read and converts every
>   allowance to a ceiling tick count with 128-bit products, and
>   [`wait_for_proceed`](../../../controller/tools/pw_probe_runner/pw_probe_runner.c) adds
>   each phase's measured wait to the plan cutoff once, at acknowledgement, with
>   checked addition. An invalid timebase or unrepresentable allowance refuses
>   before any policy byte with exit 12. A sample below the origin or the last
>   accepted sample is rejected and recorded with its stage, phase and slot; later
>   timed work refuses because of it without another read, and nothing falls back
>   to another clock. Overflow refuses only its own operation. The cutoff never
>   restarts after spawn, and a blocking spawn is not preemptible. Pipe EOF and
>   leader exit are observed separately: `waitid` with `WNOWAIT` retains the
>   unreaped leader so deadline cleanup can still target its process group after a
>   leader exit; kill and wait errors remain native errors and local timing faults
>   carry no errno; final reaping is a nonblocking window of
>   `PW_EXEC_REAP_GRACE_MS`; descendants that leave the group are outside cleanup.
>   The clock's documented sleep inclusion has not been observed across an actual
>   system sleep here.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

### P26 — [docs/LIMITS.md:414](../../../docs/LIMITS.md#L414) — Premises behind the interactions

> - Nested timeouts. [`DEFAULT_TIMEOUT_MS`](../../../controller/src/run_flow.rs)
>   is the client wait. [`ExtensionSession`](../../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)
>   prepares the target and spawns the issuer before starting its monotonic wait;
>   it observes or attempts issuer cleanup before worker creation. Neither target
>   preparation nor blocking spawn/reap is bounded by that issuer wait.
>   [`timeoutMsForCWorker`](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift) is
>   the worker polling window; [`ValidatorClientInput`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
>   the validator deadline; `PW_PROCEED_WAIT_MS_DEFAULT` the release wait, with
>   `validatorReleaseMarginMs` as the nominal margin
>   (<!-- span limits.worker_proceed_wait.value -->60,000<!-- /span --> > <!-- span limits.validator_io_wait.value -->30,000<!-- /span --> + <!-- span limits.validator_exit_grace.value -->1,000<!-- /span --> + <!-- span limits.validator_release_margin.value -->5,000<!-- /span -->).
>   Policy transfer precedes polling, each synchronous phase collection interval is
>   measured and excluded from the publication allowance, and cleanup and reaping
>   add time. [`runCWorker`](../../../runner/Sources/PWRunnerCore/CWorker.swift) measures
>   readiness, publication and exit grace as elapsed `CLOCK_MONOTONIC` time
>   through [`HostWaitClock`](../../../runner/Sources/PWRunnerCore/CWorker.swift): each sleep
>   is bounded by the remaining allowance, syscall and scheduling costs consume
>   it, and a failed or regressing clock spends only the last remaining allowance
>   in nominal sleeps, charging the last requested sleep. Every reading, including
>   exclusion boundaries, is checked against its predecessor; the wait record
>   reports a clock fault. The exit grace in [`runValidator`](../../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
>   uses the same clock; its I/O deadline already used `CLOCK_MONOTONIC`. Expiry
>   starts the stop and cleanup path; it is not an exact total response time.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** question
- **verification_needed:** Q5: Generic account omits actor setup/schedule/exchange/lifetime layers or requires cross-reading.

### P27 — [docs/LIMITS.md:436](../../../docs/LIMITS.md#L436) — Premises behind the interactions

> - Transport encoding. The controller's [`run`](../../../controller/src/run_flow.rs) reads the request with
>   `std::fs::read_to_string` before calling `parse_request`. Invalid UTF-8 takes
>   the read-error path to `tool_error`; it never reaches serde_json or the
>   runner's JSONDecoder. This path is source-inspected and checked with a
>   non-UTF-8 request through the shipped CLI; there is no permanent encoding
>   refusal control. Non-UTF-8 bytes in comments and string literals have compiled
>   through `libsandbox` on Darwin 23.6; that compiler observation also has no
>   permanent check.

- **value_unit_counting_scope:** As explicitly stated in claim; not applicable to purely navigational or editorial claims.
- **enforcement_control_boundary:** As explicitly stated in claim; not applicable where claim makes no enforcement statement.
- **stated_evidence:** Named citations are navigation only; related complete coverage rows are recorded with every limit.
- **disposition:** retain
- **verification_needed:** Validate factual claims against named authority/evidence if making a behavior claim. For navigation-only blocks, verify link/ownership separately; no runtime inference.

