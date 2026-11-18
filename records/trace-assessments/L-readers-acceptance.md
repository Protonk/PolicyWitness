# L-readers-acceptance: identity relations, order propositions and lifecycle-claim readers

Read-only assessment at `837296af` (branch `main`). Subjects, as the coverage map groups them:

1. DT-25/50/131: submitted-target canonical equality, validator identifier/metadata association, literal reader equality.
2. DT-48/130: native label/return coherence versus order eligibility; implication versus equivalence in order readers.
3. DT-53/132/135: lifecycle-claim coverage, byte-consistent envelope readers, shared predicates.

Section 0 covers the acceptance section's identity, conventions and limits, which qualify all three.

## Method and what was executed now

- **Source re-read at HEAD.** `git diff --stat bfc74b6b HEAD` over `controller/src`, `controller/tools`, `runner/Sources`, `runner/Tests`, `tests/lib/{consumer,lifecycle_oracle,lifecycle_adapter,phase_evidence,witness_capture,blackbox}.py`, `tests/FAILURE-PROPAGATION-CONTRACT.md` (FPC below), `docs/contract/*.surface.md`, `docs/QUESTIONS.md`, `tests/suites/{blackbox_e2e,witness_contract}` and `tests/COVERAGE.md` shows only the regenerated worker identity (`CWorker.swift`, `pw_probe_runner_abi.h`) and `docs/contract/{README.md,runtime.py}`. The review's line numbers for these files are therefore still exact; every line cited below was re-read.
- **Retained evidence checked.** All eleven artifact hashes in the review's availability table match `.tmp/contract-trio/acceptance/` (prefix and suffix). All eleven live frames match the live-run table (hash prefix, byte count, exit, outcome).
- **Python readers re-executed in memory (HEAD `tests/lib`, `tests/lib/python.sh`, Python 3.14.9).** Three read-only replays; scripts are in `work-L-readers-acceptance/`:
  - `replay_retained.py`: consumer (bare, envelope, fixture and non-fixture entry) and oracle over the retained seam envelopes in `corpus/reader-corpus/rust.json`. These carry the constructed `test:policy-witness` binding and retained Rust output from the `cc55288d` test binary.
  - the retained live envelopes (`live/*/stdout.json`), under each envelope's own contract.
  - `oracle_sweep.py`: consumer and oracle over every `kind: run` envelope retained by the checkpoint run `tests/out/runs/trace-instrument-after-corrected` (the `2f4d76e4` app), contract taken from each envelope. This shows reader judgments on retained documents. It is not a case result and binds no identity independently.
- **Constructed contrasts** (`contrasts.py`): edits of the retained `ordinary` seam envelope, in memory.
- **Static case map** (`case_reader_map.py` → `case_reader_map.json`): transitive text map from `tests/catalog.json` cases to reader calls. Text patterns only; it does not establish that a call executes.
- **Not executed:** Swift (any), Rust (any), the signed app, any registered case. Every Swift and Rust statement below is source reading plus retained output.
- **Working tree.** During this pass the tree acquired uncommitted changes that this pass did not make: `tests/catalog.json` (the `source_drift/markdown_reader` entry gains `engine` and `module`), `tests/suites/source_drift/run.sh`, and a new `tests/suites/source_drift/test_markdown_reader.py`. None is a file assessed here. The catalog counts below were taken with that change present.

## 0. Acceptance evidence identity and limits (qualifies all three subjects)

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| ACC-ID.a | Snapshot `cc55288d`; dist app `8b5de2b2` v0.3.7; five executables unchanged across the pass | investigation identity, 2026-11-16 | Historical. The dist app is now `2f4d76e4` (`development:b55acb20…`), so the live runs cannot be repeated against the same bytes; product source differs only by the regenerated worker identity | review executed; hashes not re-derivable now | accurate observation, no change |
| ACC-ID.b | Evidence categories live / seam / unit / source / listing; 283 cases, 232 default | catalog | yes: `tests/catalog.json` has 283 cases, 232 default | re-counted now | accurate observation |
| ACC-ID.c | Live runs ran inside the automation sandbox; nothing concluded about earlier lookup refusals | environment | unverifiable by reading | review executed | accurate observation |
| ACC-ID.d | Live-run table (eleven runs: exit, outcome, frame hash, size) | live CLI, old app | yes: all eleven retained frames match | retained, re-hashed now | accurate observation |
| ACC-ID.e | Seam method: `reader_definition_corpus_cross_readers` decodes, admits, assembles, then the Python replay runs consumer (bare and envelope), `actor_evidence`, `extension_evidence`, oracle | Rust test + replay | yes: `controller/src/run_flow.rs:1252-1389`, `tests/suites/runner_unit/reader_corpus.py:85-96` | source re-read | accurate observation |
| ACC-ID.f | Seam limits: constructed `test:policy-witness` binding; no `reply_contract`; placeholder rows disregarded; fidelity checked on twelve unedited rows; exit 101 by design | seam | yes; the limits still attach to every seam-derived statement here | retained `rust.json`, `python.json` | accurate observation; carried forward |
| ACC-ID.g | Swift reporting validator and setup decoder were not run on any edited frame | Swift | yes, and still true of this assessment | none | accurate observation; an open evidence limit |
| ACC-ID.h | Artifact availability and hashes under `.tmp/contract-trio/acceptance/` | local scratch | yes: all eleven hashes match | re-hashed now | accurate observation; gitignored, no retention guarantee |
| ACC-LIM.a | Non-native validator transcripts are steered; no claim that the shipped validator emits incoherent labels or rewrites Unicode | validator | yes: `sb_api_validator.c:49-75` passes UTF-8 through and `:403-427` derives the label from the native pair | source re-read | accurate observation |
| ACC-LIM.b | The reader map is a static text search; no registered case was run | registry | partly: the method is as stated, and its counts are understated (see DT-53.t9, DT-132.c) | recomputed now | overstated coverage credit in the opposite direction: the consumer-only population is larger than reported |
| ACC-LIM.c | No Swift package, mutated app or battery was built or run | investigation | yes | n/a | accurate observation |

**Comparison.** These rows describe the investigation, not a product obligation; there is no owning statement, producer or reader to compare.

**Treatments and disposition.** ACC-ID.a–.h, ACC-LIM.a and ACC-LIM.c: no change; they are accurate records, and further evidence would not alter them. ACC-ID.f and ACC-ID.g stay attached, as limits, to every seam-derived and Swift-related statement in sections 1–3. ACC-LIM.b: record the corrected reader population (DT-53.t8, DT-53.t9) in the management plan's disposition and do not reuse `reader-case-map.jsonl` as a complete list; no tree change.

**User duties.** None. **Worklist.** None.

**Routed to other passes, not assessed here.** The DT-61 and DT-95 anchor traces, the boundary-map rows for the shared-memory decoders, actor scheduler, `reply_contract` and `actor_evidence`/`extension_evidence`, agreement-classification rows 4–6, the results bullets on `ready` and receipts, the cross-reference bullets for DT-60, DT-96/97 and DT-101, and the two coverage-limit bullets on the scheduler gate and the `actor` specimen all belong to the DT-59–61/133 and DT-95–104/134 rows.

---

## 1. DT-25/50/131: target equality, validator association, literal readers

### 1.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-25.a | The field meaning and the rule say the relation "compares submitted strings" and name no equality relation | complete statement (RESPONSE from the steps surface) | yes: `docs/contract/31-steps.surface.md:283`, `:754-755` | source re-read | consequential ambiguity |
| DT-25.b | NFC and NFD "café" targets, unequal as UTF-8, return `same_submitted` | host producer, constructed | yes by source: `CWorkerComparison.swift:147-156`; pinned by `ComparisonEvidenceTests.swift:142-155` | review reproduction not retained; Swift not run now; Python side (`consumer.py:176-185`) read | accurate observation |
| DT-25.c | Swift `String ==`; the unit-test comment and `docs/QUESTIONS.md:41` state canonical equivalence; the complete statement does not | statements vs producer | yes; FPC reading rule 4 (`:1419-1422`) also states it | source re-read | consequential ambiguity (one owner silent, two owners explicit) |
| DT-25.d | `same_as_input` in the same record family is stated in UTF-8 bytes | path forms | yes: `PWRunnerPathEvidence.swift:18`, `consumer.py:133` | source re-read | accurate observation; a separate question, kept separate |
| DT-25.x | Cross-reference: reading rule 4 adopts canonical target equality and Python implements it with NFC; DT-50/131 differ in having no stated relation | statements | yes | source re-read | accurate observation |
| DT-50.a | FPC says every semantic reader checks association the same way and only unique matching records enter the join; "exact" spans two equality rules | FPC `:605-622`, `:1019-1027` | yes; also "exact submitted operation/filter tuple" `:1194`, "exact planned query tuple" `:1226` | source re-read | consequential ambiguity; the word "exact" reads as bytes |
| DT-50.b | Steered record ID in NFD for request ID in NFC: host `association_issues: []`, `query_first`, `finished`/0; Rust `withheld`/`invalid` with two findings; consumer rejects both; oracle D6 | one live reply, four readers | yes: Python re-run now on retained live `nfd_id` and seam `nfd-id` gives the same findings; Rust from retained output; Swift by source | original scratch absent; acceptance-pass copy retained | accurate observation |
| DT-50.c | Swift groups and compares with `String` equality; Rust and Python are literal | producers and readers | yes: `PWRunnerPredictionEvidence.swift:160-187`, `PWRunnerStepEvidence.swift:14-24`; `porcelain_admission.rs:776-786`, `:1029-1093`, `:1196-1220`; `phase_evidence.py:38-67`, `consumer.py:274-278` | source re-read | inaccurate mechanism account in two source comments (see DT-131.d); otherwise accurate |
| DT-50.d | `failure_boundaries` association controls use IDs `first`, `middle`, `last` and do not cover this boundary | test scope | yes: `tests/suites/failure_boundaries/check.py:246-255` | source re-read | accurate observation |
| DT-50.e | Qualification: steered transcript; no claim about the shipped validator; one real reply received opposed assessments without changing its summary | scope | yes | n/a | accurate observation |
| DT-50.t1 | Swift canonical equivalence also governs request duplicate refusal, lifecycle step joins and every reporting-validation `Set` | host | yes: `ProbeRunner.swift:83-90`, `:113-118`; `ActorPlan.swift:333`, `:358-363`, `:397`; `CWorkerStepResults.swift:19-22`, `:55`; `PWRunnerReply.swift:66`, `:296-299` | source re-read | accurate observation |
| DT-50.t2 | Two rules write identity as an unqualified `==`; the ownership paragraph states no relation; only `same_submitted` and `same_as_input` have explicit equality | statements | yes: `31-steps.surface.md:619-636`, `32-lifecycle.surface.md:1179-1243`, FPC `:605-622`; no string-equality definition exists in `docs/contract/README.md` | source re-read | consequential ambiguity |
| DT-50.t3 | Executed table for `nfc_id`, `nfd_id`, `nfc_value`, `nfd_value`, `dup_id`, `both_ids` | live + seam | yes: Python re-run now on all six live envelopes and seam rows reproduces every Python cell | retained | accurate observation |
| DT-50.t4 | In `dup_id` host classification under canonical grouping changed the result; a literal issue list would also give `validator_unavailable` but would have associated the NFC record | host outcome | yes for the observation; the counterfactual is source inference from `CWorkerDisposition.swift:443-452` | retained + inference | accurate observation; inference labelled |
| DT-50.t5 | Python flagged no withheld order in `dup_id` because eligibility reads the step's own synthetic query | consumer | yes: `consumer.py:279` | re-run now | accurate observation |
| DT-50.t6 | Request admission applies canonical identity, so a reply never carries two canonically equivalent step IDs; literal step/phase joins agree with Swift only through that restriction; child-output identities are where readers diverge | request vs reply | yes by source; the controller has no duplicate check (`grep duplicate_step_id controller/src` is empty) | retained `both_ids` + source | accurate observation; see reachability in 1.3 |
| DT-131.a | `nfd_value` repeats the pattern on `filter_value` | record metadata | yes | re-run now | accurate observation |
| DT-131.b | `dup_id`: one duplicate group, synthetic query, `validator_unavailable`, exit 1, error naming `duplicate_id:s-é` | host | yes | retained | accurate observation |
| DT-131.c | `both_ids` refused as `duplicate_step_id` at `probe_plan.1.step_id`; no controller duplicate check | request admission | yes | retained + source | accurate observation |
| DT-131.d | Step ID is "unique across all actions" with no relation (`12-probes.surface.md:23`); the comment "shared with every reader that recomputes it" (`PWRunnerPredictionEvidence.swift:157`) is accurate only for Swift readers | statements, source comment | yes | source re-read | consequential ambiguity (12-probes); inaccurate mechanism account (the comment) |
| DT-131.e | Cost: host outcome and controller finding disagree about how many records were associated | public envelope | yes | retained | accurate observation |
| ACC-MAP.assoc | Boundary-map rows "Host association" and "Host order eligibility": canonical `String` equality; issues feed `validator_unavailable` | host | yes | source re-read | accurate observation |
| ACC-CLS.3 | Agreement row: Rust and Python agree with Swift on step-to-phase joins through restricted inputs | readers | yes | source | accurate observation |
| ACC-RES.assoc | Results bullet: `association_issues: []` is the host's join under canonical equality; Rust's byte recomputation can disagree on the same frame | reply | yes | re-run now | accurate observation |

### 1.2 Comparison

**Obligations as stated.**

- Target relation. Owner `docs/contract/31-steps.surface.md`: "`same_submitted` or `different_submitted` compares submitted strings when the query filter matches the action's mapped filter and both strings exist" (`:283`); "Target equality compares submitted strings; runtime object identity requires its own observations" (`:754-755`). Shared owners: FPC reading rule 4, "Canonically equivalent Unicode spellings compare equal, so their UTF-8 bytes can differ; `same_as_input` in path diagnostics compares bytes instead" (`:1419-1422`); `docs/QUESTIONS.md:41`, "canonically equivalent Unicode spellings compare equal". FPC's working table adds "Different strings establish different submitted targets" (`:1225`).
- Association. Owner `docs/contract/32-lifecycle.surface.md:1159`: "A unique expected-ID record enters the per-step join only when every supplied query metadata value agrees with the submitted query." Cardinality conditions use `==` (`:1184-1242`). Owner `31-steps.surface.md:619-636`: `records[v].step_id == steps[s].step_id` and the "Exact retained query identity" condition. FPC: "Unique step ID plus exact submitted operation/filter tuple" (`:1194`); "Only a unique record matching the submitted query enters the step join" (`:1023`); "Every semantic reader checks ownership of a phase's validator subprocess the same way" (`:605`).
- Request identity. Owner `12-probes.surface.md:23`: "It is unique across all actions".

**Producer.**

- Target relation: `sandboxCheck.filter_value == attempt.requested_path` on Swift `String` (`CWorkerComparison.swift:154`), which is canonical equivalence.
- Association: `Dictionary(grouping:)` on record IDs and `!=` on operation, filter type and filter value (`PWRunnerPredictionEvidence.swift:161-177`), all Swift `String`. Order: `records.filter { $0.stepId == stepId }` and four `String` comparisons (`PWRunnerStepEvidence.swift:19-23`). Reporting validation calls the same two functions over reply-visible inputs (`PWRunnerReply.swift:77`, `:365`).
- Request uniqueness: `Set<String>.insert` (`ProbeRunner.swift:113-117`; `ActorPlan.swift:358-363`, `:397`), canonical.
- The shipped validator re-emits each parsed string byte for byte: `parse_json_string` decodes escapes to UTF-8 (`sb_api_validator.c:191-256`), and `print_json_string` escapes only `\`, `"` and bytes below 0x20, "so the host reads the exact submitted bytes" (`:65-70`). The host sends request strings unchanged (`CWorkerRequestPlanning.swift:335-338`, `ValidatorClient.swift:435-457`).

**Readers and tests.**

- Rust: `BTreeMap<&str>` groups and `as_deref() ==` (`porcelain_admission.rs:1030-1066`, `:776-786`). Literal.
- Python: dictionary groups and `!=` (`phase_evidence.py:40-56`); order tuple `==` (`consumer.py:274-278`). Literal. Target relation: NFC on both sides (`consumer.py:183-185`).
- Tests. `ComparisonEvidenceTests.swift:145-155` asserts canonical `same_submitted` in both directions. No test presents canonically equivalent but byte-different identifiers or metadata to association: `failure_boundaries` uses ASCII IDs, and the reader corpus has one NFC row (`ReaderCorpusTests.swift:65`). No test submits two canonically equivalent step IDs; `both_ids` was the review's own run.

**Observation versus inference.** Observed (retained, Python re-run now): the six-row table. Inferred from source: what Swift reporting would say on any edited frame; the `dup_id` counterfactual; that Foundation serialisation leaves scalars un-normalised (see 1.3).

### 1.3 Reachability of a disagreement in a shipped run

The two rules disagree on a reply only if some validator record string is canonically equivalent to, and byte-different from, the request string it is compared with (`step_id`, `filter_value`), or two record IDs stand in that relation to each other.

1. **Request strings cannot supply it.** Admission refuses canonically duplicate step, phase and actor IDs (`both_ids`: `bad_request`, `duplicate_step_id`). Every other join among request-derived strings compares a string with a copy of itself.
2. **The shipped validator cannot supply it, by source reading.** It echoes parsed bytes. Not executed for a non-NFC request: across the checkpoint run's retained live envelopes there are 5,315 validator records (5,193 without a validator override); two carry non-ASCII identifiers or values, none is non-NFC, and none is canonically equal and byte-different from its step. `failure_boundaries` exercises control characters and `é` at limits through the shipped validator, and those envelopes pass the literal consumer on replay.
3. **So the disagreement needs child output that differs from the request's bytes.** Today that means `_test_overrides.validator_executable_path` on an ordinary request (the review's method), or an external runner bundle whose validator copy is not the shipped one. After the selected seam migration, validator substitution is reachable only through `test-input run` experimental controls.
4. **Not limited to non-ASCII requests.** Three non-ASCII code points are canonically equivalent to ASCII characters: U+212A → `K`, U+037E → `;`, U+1FEF → `` ` `` (Python `unicodedata` 16.0, enumerated now). A request ID such as `K1` has a canonically equivalent, byte-different spelling. The filter type names `IOKIT_REGISTRY_ENTRY_CLASS` and `IOKIT_USER_CLIENT_CLASS` contain `K`.
5. **Operation is a special case.** The reply's `sandbox_check.operation` is the record's own spelling when one is associated (`CWorkerStepResults.swift:132`), so literal readers compare the record with itself and cannot object. The reply field then carries the validator's bytes, not the submitted bytes, although its meaning is "The admitted query operation" (`31-steps.surface.md:79`).
6. **Request-side effect any user can reach.** Two step IDs that differ in bytes and are canonically equivalent are refused as duplicates. No reader disagrees, because none checks request uniqueness; the statement simply does not say which equality "unique" uses.

Submitted-target equality (DT-25) is a different question: it relates two request strings to each other, has a stated canonical rule, and is reachable by any user. Path-form `same_as_input` is a third question, stated and implemented in bytes. Neither participates in the association rehearsal.

### 1.4 Plausible treatments

**T1. Correct the target-relation account in its owner (DT-25).** Add the relation to `docs/contract/31-steps.surface.md:283` and `:754`. Replace the last sentence of FPC `:1225` so it does not say "Different strings establish different submitted targets". Regenerate with `tests/lib/python.sh docs/generate_contract_stamps.py`. No build-contract input. No behaviour change. Reading rule 4 and QUESTIONS are already correct and are not touched.

**T2. Make target equality byte-exact (DT-25 alternative).** Not a real candidate: it would contradict two shared owners copied into the frozen guide, a unit test and the Python reader, to fix a statement that is merely silent.

**T3. Make Swift association and order byte-exact (the rehearsed change; DT-50/131).**

- Files: `runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift` (`validatorAssociationIssues`: group record IDs by UTF-8 bytes; compare operation, filter type and filter value by bytes; sort unexpected IDs in UTF-8 byte order), `PWRunnerStepEvidence.swift` (`eligibleOrderedStep`: byte comparison for the record filter and four tuple members), `PWRunnerReply.swift` (`validatorOwnershipProblem`: compare issue keys by bytes). All three are build-contract inputs: **signed rebuild**.
- It changes the query eligibility rule, so `witness_contract/order_barrier_mutations` is required; its mutation anchors need review if the edited functions move.
- Behaviour change, only for canonically equivalent byte-different child output: `nfd_id` becomes `missing_id` plus `unexpected_id`, the step's query synthetic with `validator_no_verdict`, `unestablished`, host outcome `validator_unavailable`, exit 1. `nfd_value` becomes `query_mismatch` with the same outcome. `dup_id` keeps `validator_unavailable` but associates the byte-identical record and reports the other as `unexpected_id`.
- Held fixed: request-name uniqueness (canonical), `same_submitted` (canonical), `same_as_input` (bytes). `byStep` may stay keyed by `String`: its keys are request IDs, which admission keeps canonically unique.
- Who relies on current behaviour: only a validator that returns canonically equivalent, byte-different strings. The shipped validator does not.
- Incorrect behaviour a check must reject: a reply in which a record whose `step_id`, `operation`, `filter_type` or `filter_value` bytes differ from the submitted bytes is joined to the step (`association_issues: []`, `result_source: validator`) or credited `query_first`; and a byte-identical neighbour that fails to associate.

**T4. Make Rust and Python canonical.** Rust has no normalisation in `std`; a new crate would change `controller/Cargo.toml` and `Cargo.lock` (build-contract inputs) and offline vendoring. Three runtimes would then carry three Unicode data versions. All readers would accept attributing an answer about one byte string to a query for another, which the "exact" statements and "No dishonest attribution" argue against. Not recommended.

**T5. Retain, with the split stated.** Edit FPC `:605-622`, `31-steps` "Unique association" and `32-lifecycle` "Joining accepted validator records" to say the host joins under canonical equivalence while the controller and test readers recompute under byte equality. No rebuild. It leaves a documented case in which the host reports no issue and the controller withholds the disposition, and it requires weakening "exact" in three FPC statements.

**T6. State request-identity uniqueness (DT-131.d, independent of T3/T5).** `docs/contract/12-probes.surface.md:23`: say that uniqueness is under canonical Unicode equivalence. Check the phase and actor identifier statements in `10-request.surface.md` and `13-actors.surface.md` for the same silence. Surface edits only.

### 1.5 Recommended disposition

| Claim | Disposition | Reason and discriminating check |
| --- | --- | --- |
| DT-25.a, .c | **T1**: correct the account in `31-steps.surface.md` and FPC `:1225` | The producer, a unit test, the Python reader and two shared owners agree on canonical equivalence; only the complete statement is silent. Existing check: `runner_unit/pwrunner_core_unit_executable` ("canonically equivalent targets with different UTF-8 bytes are same_submitted") rejects a byte-exact producer. New control in `blackbox_e2e/checker_controls`: an NFC/NFD target pair reported `different_submitted` must be rejected with `comparison.target_relation disagrees with the submitted targets (same_submitted)`, beside a non-equivalent pair reported `same_submitted`. |
| DT-25.b, .d, .x | No change | Accurate. `same_as_input` stays a byte comparison and a separate question. |
| DT-50.a, .t2; ACC-MAP.assoc; ACC-RES.assoc | **T3** (product change), recommended to management, which holds this decision | The statements say "exact"; both independently written readers chose bytes; the validator's own contract is to return "the exact submitted bytes"; a canonically equivalent path is a different byte string to the native query, so joining it attributes an answer to a query that was not asked. If management declines, **T5** with the retention sentence below. |
| DT-50.b, .d, .e, .t1, .t3–.t6; DT-131.a–.c, .e; ACC-CLS.3 | No change to the record; behaviour follows T3 or T5 | Accurate observations. Under T3 the `nfd_id`, `nfd_value` and `dup_id` rows change as listed in T3 and all four readers agree on those frames. |
| DT-50.c, DT-131.d (source comment) | Correct the noun in `PWRunnerPredictionEvidence.swift:157` only inside a commit that already changes `runner/Sources` | A comment-only edit there forces a signed rebuild for no behaviour. Proposed: "shared by host association and reporting validation; the controller and the test readers implement the rule separately". |
| DT-131.d (12-probes) | **T6** | Current, executed behaviour (`both_ids`) with no stated relation. Stating it keeps `String`-keyed host joins sound under T3. |

**Discriminating control for T3.** Add rows to the existing reader corpus (`ReaderCorpusTests.swift`, case `runner_unit/pwrunner_core_unit_executable`), built from `orderedOrdinary` with a constructed `ValidatorOutput`. The Swift encoder writes each frame, Rust assembles the envelope and both Python readers replay it, so every row has a consistent binary capture.

- `association-nfc-id`, `association-nfc-value`: byte-identical record; all readers accept; `query_first`.
- `association-nfd-request`: request ID and path spelled in NFD, record byte-identical; all readers accept. This is the neighbour 1.3 item 2 lacks.
- `association-nfd-id`, `association-nfd-value`: record canonically equivalent and byte-different. Before T3 the Rust and consumer expectations fail; this is the incorrect behaviour. After T3 the host produces the issue list, all readers accept the reply as valid evidence of a failed association, and `order` is `unestablished`.
- `association-dup-nfc-nfd`: two records; after T3 one associates and one is `unexpected_id`.
- `association-kelvin-id`: request `K1`, record `K1`; same expectation as `association-nfd-id`.

Add matching `OrderingTests` assertions on `eligibleOrderedStep` for a byte-different record ID and value.

**Retention sentence if T5 is chosen** (FPC "Reader validation responsibilities", after `:614`): "The host joins validator records to submitted queries under canonical Unicode equivalence; the controller and the test readers recompute the join under UTF-8 byte equality. A record that is canonically equivalent to its query and differs in bytes is therefore joined by the host and reported by the controller as `validator association issues disagree with records`, with the disposition withheld."

### 1.6 Resulting user duties

- Do not conclude from `target_relation: same_submitted` that the query and attempt strings have identical bytes. Already stated in reading rule 4.
- Give actions step identifiers that are distinct under canonical Unicode equivalence; two that differ only in normalisation are refused as duplicates.
- Under T3: none further. Under T5: when `disposition_issues` reports an association disagreement beside host `association_issues: []`, compare record and step bytes before reading the step's answer.

### 1.7 Worklist

1. `docs/contract/31-steps.surface.md:283`: "…compares submitted strings under canonical Unicode equivalence when…". `:754`: "Target equality is canonical Unicode equivalence of the two submitted strings, so equal targets can differ in UTF-8 bytes;".
2. FPC `:1225`: replace the last sentence with "Submitted strings that are not canonically equivalent establish different submitted targets, not distinct runtime objects."
3. `docs/contract/12-probes.surface.md:23` (and the phase/actor identifier fields if they are equally silent): add "Uniqueness is under canonical Unicode equivalence: identifiers that differ only in normalisation are duplicates."
4. `tests/suites/blackbox_e2e/checker_controls.py`: the two target-relation controls from 1.5.
5. Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`; then `tests/lib/python.sh docs/generate_limits.py --check`.
6. Verify steps 1–5 (no rebuild): `tests/run.sh --suite source_drift --case blackbox_e2e/checker_controls`.
7. If T3 is selected, in the signed rebuild already planned for the seam migration: the three `runner/Sources` edits in T3; the `PWRunnerPredictionEvidence.swift:157` comment; `OrderingTests.swift` and `ReaderCorpusTests.swift` rows (`runner/Tests` is not a build-contract input); expectations in `tests/suites/runner_unit/reader_corpus.py` if a row needs a per-reader override (see 3.7).
8. T3 accounts, landed with the code: `31-steps.surface.md` under "Unique association" and `32-lifecycle.surface.md:1164-1166`: "Identifier and query-metadata equality in this join is equality of UTF-8 bytes; canonically equivalent spellings with different bytes do not match." FPC after `:614`: "Step identifiers and query metadata are compared as UTF-8 bytes in this recomputation." Regenerate as in step 5.
9. T3 verification, per `tests/CHANGE-VERIFICATION.md` "Admission or validator receivers" and "Ordering barriers, worker wait/release, query eligibility or observers": `tests/run.sh --suite failure_boundaries --suite runner_unit --suite runner_abi_layout --suite runner_c_worker_harness --suite unit --suite source_drift`, the `runner_validator_failure` and `witness_contract` default cases, `blackbox_e2e/checker_controls`, and `tests/run.sh --case witness_contract/order_barrier_mutations`.

---

## 2. DT-48/130: label/return coherence and the order proposition

### 2.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-48.a | `finished` requires completed evidence collection; allow/deny classify native returns; coherent returns are separately required for `query_first` | FPC `:15-18`, `:1229-1234`, `:1226` | yes | source re-read | accurate observation |
| DT-48.b | Steered record `allow`, rc −1, errno 13: exit 0, `finished`; query keeps `outcome: allow`, `rc: -1`, `native_rc: -1`, `errno: 13`; `unestablished`; controller `valid`; consumer and oracle `[]`; `query_column` returns `allow` | one live reply, all readers | yes: Python re-run now on live `incoherent` and seam `incoherent` gives `[]`, `[]`, `allow` | retained | accurate observation |
| DT-48.c | Line admission checks types and presence; `classify` checks process, transport and association; only the ordering gate checks coherence; the native emitter would label this pair `error` | host | yes: `ValidatorClient.swift:526-546`; `CWorkerDisposition.swift:432-455`; `PWRunnerStepEvidence.swift:5-9`; `sb_api_validator.c:403-427` | source re-read | accurate observation |
| DT-48.d | `ValidatorEvidenceTests.swift:154-163` constructs allow/−1/13 and asserts acceptance and preservation | unit test | yes | source re-read | accurate observation |
| DT-48.e | Checker control `incoherent_native` changes the native return under a surviving `query_first` claim, so it does not establish rejection of the unestablished case | `checker_controls.py:453` | yes | source re-read | accurate observation |
| DT-48.f | The structural acceptance pattern is present in `6885cb42` (2026-09-18) | history | unverifiable by reading here (the commit exists with that date; its content was not re-read) | review source reading | accurate observation |
| DT-48.g | Qualification: the gap is between labels and their native meaning, not loss of raw evidence or a false ordering claim; no contradictory native result was established | scope | yes | n/a | accurate observation |
| DT-48.t1 | `buildSandboxCheckResult` copies `outcome`, `rc` (default −1) and `errno`; `native_rc` comes from any allow/deny/error record | projection | yes: `CWorkerStepResults.swift:47-49`, `:128-139` | source re-read | accurate observation |
| DT-48.t2 | Four-row table (`base_fixture`, `incoherent`, `f48-claimed-order`, `f48-withheld-order`) | live + seam | yes: Python cells reproduced now; Rust cells from retained output | retained | accurate observation |
| DT-48.t3 | Incoherent record with a claimed order: Rust and the consumer reject; the oracle does not check `order`; Swift reporting would reject by source and the host does not produce the state | readers | yes: `porcelain_admission.rs:1204-1227`; `consumer.py:555-556`; `PWRunnerReply.swift:365-369` | retained + source | accurate observation |
| DT-48.t4 | Incoherent record without an order claim: every boundary accepted it; the label is then "the raw query answer" under reading rule 1 and "the associated answer" under the steps `outcome` meaning | statements | yes: FPC `:1401-1402`; `31-steps.surface.md:71` | source re-read | unsupported inference if a reader takes the label as coherent with `rc`; the statements do not say so |
| DT-48.t5 | Deliberate delegation; the only reply value reflecting incoherence is `order: unestablished`, which is shared with other causes | reply | yes: `21-wire.surface.md:185`, `:201` | source re-read | accurate observation |
| DT-48.t6 | `query_column` has three uses; none relies on the label without the order or an expected row | tests | yes: `consumer.py:1142`; `runner_exec_dac/check_query_scope.py:166`, `:190`; `witness_contract/check_comparison_matrix.py:151-152` | re-grepped now | accurate observation |
| DT-48.t7 | DT-108's conditional-null rule does not arise in these rows | projection | yes: `CWorkerStepResults.swift:46` always sets `result_source` | source re-read | accurate observation |
| DT-130.a | The producer obligation is an if-and-only-if; the controller's family is "the complete `query_first` chain" (one direction); the consumer "validates … `order`" with no direction; no statement assigns a recipient the withheld-order check | statements | yes: `31-steps.surface.md:573-596`; FPC `:1226`, `:1378-1379`; `41-diagnostics.surface.md:678` | source re-read | consequential ambiguity (direction unstated for recipients) |
| DT-130.b | Rust skips steps whose order is not `query_first`; Swift reporting checks only a claimed `query_first`; Python checks both directions; `unestablished_despite_chain` pins Python through a JSON-text carrier that Rust never sees | readers | yes: `porcelain_admission.rs:1185-1187`; `PWRunnerReply.swift:365`; `consumer.py:555-558`; `checker_controls.py:457`; `blackbox.py:16-31` | source re-read | accurate observation |
| DT-130.c | `f48-withheld-order`: Rust `valid`, no finding; consumer "eligible record with complete chain requires query_first" on bare reply and envelope; oracle `[]`; `finished` | seam | yes: reproduced now on the retained row | retained | accurate observation |
| DT-130.d | Each implementation stays within its statement; the host does not produce the state; Rust `valid` does not cover under-credited order; the Python control establishes nothing about Rust | scope | yes | source | accurate observation |
| ACC-MAP.wire | Boundary-map rows "Validator verdict production" and "Host line admission" | wire | yes | source re-read | accurate observation |
| ACC-CLS.1 | Agreement row: every boundary accepts an incoherent allow without an order claim; deliberate delegation to the emitter | readers | yes | retained | accurate observation |
| ACC-RES.order | Results bullets: `valid` does not certify withheld-order consistency; `unestablished` has several causes and no field states which | envelope | yes | source | accurate observation |
| ACC-XREF.48 | Cross-references: DT-38/47 bear on DT-130 (the Python control uses a JSON fixture); DT-49 is a sibling of DT-48 | review | yes | n/a | accurate observation |

### 2.2 Comparison

**Obligations as stated.**

- Emitter (`docs/contract/21-wire.surface.md:185`): "Native rc 0 is `allow`; rc 1 with errno 0 is `deny`; rc -1 with EINVAL is `unsupported_operation`; other pairs are `error`."
- Host receiver (`21-wire.surface.md:201`): "Allow/deny require nonempty step_id, operation and filter_type plus integer rc and errno." No label/return relation is stated.
- Label meaning. `31-steps.surface.md:71`: "`allow` or `deny` is the associated answer". FPC `:1231-1232`: "These labels classify native returns." Reading rule 1 (FPC `:1401-1409`): the raw query answer is the outcome when `result_source` is `validator`, and "An otherwise eligible answer qualifies as a prediction about a live specimen only with its phase's collection/release/acknowledgement chain, reflected by `comparison.order: query_first`."
- Order (`31-steps.surface.md:573-596`, `who` the host): on success set `query_first`, on failure set `unestablished`, with the "Native answer" condition at `:616`. This is an equivalence, stated as a producer rule.
- Recipients. Controller family (`41-diagnostics.surface.md:678`): "comparison vocabulary and the complete `query_first` chain". Consumer (FPC `:1378-1379`): "validates `observation`, the two relations and `order` against the raw channel fields and `ordering`". FPC `:586-587`: "`disposition_integrity: valid` certifies those claim checks, not every relationship in the response."

**Producer.** The shipped validator derives the label from the native pair, so label and pair cohere for every record it emits. The host admits by type and presence, projects the label and the pair side by side, and computes `order` with the predicate that includes coherence (`CWorkerStepResults.swift:74-80`). It therefore never emits `query_first` on an incoherent record and never withholds it from an eligible one. `OrderingTests.swift:429-459` asserts `query_first` on the complete chain and `unestablished` for each missing link; `:484-498` asserts `unestablished` for `rc` and `errno` defects.

**Readers.** Rust and Swift reporting check the implication `query_first ⇒ eligible`. Python checks the equivalence.

**Which proposition, and which reader is right.**

- The owning statement makes the equivalence, and makes it of the producer.
- A recipient can check `query_first ⇒ eligible` soundly from the reply alone: any failed reply-visible condition disproves the claim.
- A recipient can check `eligible ⇒ query_first` only by assuming the reply-visible fields equal the producer's inputs. The "Setup" condition says they are not the same thing: "their final summary labels alone do not establish the eligibility observation" (`31-steps.surface.md:610`). The reply's `sandboxed_after_apply` projects `applied` alone (`CWorkerOrchestrator.swift:221`) while production also requires `applyRC == 0` (`CWorkerStepResults.swift:78`). The reader corpus already carries this: "applyRC is a producer observation, not a field of the carried reply" (`ReaderCorpusTests.swift:69-117`).
- By source reading, no host-produced reply is consumer-eligible and host-ineligible at HEAD: the one state where the proxies differ adds `release_without_successful_application`, which breaks the chain for the consumer too. So the consumer's reverse check has no known false positive, and it is the only check that would catch a producer that stopped crediting eligible records.
- Both readers are right within their statements. The controller reports on claims the reply makes; an `unestablished` order makes none, and a valid unfavourable value is not invalid evidence. The consumer is a test reader verifying the producer's success effect under an assumption a product recipient should not make.

Neither the producer nor a reader should change. The statements should name their direction.

### 2.3 Plausible treatments

**T1. Retain, with the limit stated and the direction of each check named (recommended).**

- `docs/contract/21-wire.surface.md` "Host line admission" prose (`:201`): add "Admission does not compare an `allow` or `deny` label with its `rc` and `errno`; that relation is the emitter's, and the host tests it only as a condition of `query_first`."
- FPC `:1231-1232`: replace "These labels classify native returns." with "These labels are the validator's classification of its native returns; the host admits them by type and tests their agreement with `rc` and `errno` only as a condition of `query_first`."
- FPC `:1378-1379` (consumer bullet): "…validates `observation` and the two relations against the raw channel fields, and `order` against them and `ordering` in both directions: a claimed `query_first` needs an eligible record and the complete chain, and an eligible record with the complete chain must say `query_first`."
- `docs/contract/41-diagnostics.surface.md:678`: "…comparison vocabulary and each claimed `query_first` against its complete chain. An `unestablished` order is not compared with eligibility."
- No build-contract input. Regenerate surfaces with `tests/lib/python.sh docs/generate_contract_stamps.py`. Reading rule 1 is not false and is not touched.

**T2. Refuse an incoherent allow/deny frame at host line admission.** One guard in `validatorStructureError` (`ValidatorClient.swift:537-543`): `runner/Sources`, **signed rebuild**. The frame becomes a `structure` decode fault, the run `validator_decode_failure`, exit 1. Costs: the record is no longer accepted evidence (at most 256 context bytes survive); every later frame of that collection is lost, because decoding stops at the first refused frame; `ValidatorEvidenceTests.swift:154-163` must use another outcome; the 21-wire statement and FPC `:995-1001` change. It makes FPC `:1231` true at the host boundary for any validator. Not recommended: it converts an observation the host can retain into a refusal in order to settle a relation the reply already exposes, and the state needs a non-shipped validator.

**T3. Make Rust check both directions (DT-130).** `controller/src/porcelain_admission.rs:1185`: **signed rebuild**. A withheld order would produce an `ordering` finding and withhold the worker's disposition for a reply that asserts nothing false, on a premise the steps surface says a recipient cannot establish. Not recommended.

**T4. Narrow the consumer to the implication (DT-130).** `tests/lib` only. Removes the one check sensitive to a producer that under-credits. Not recommended.

### 2.4 Recommended disposition

| Claim | Disposition | Reason and discriminating check |
| --- | --- | --- |
| DT-48.a–.g, .t1–.t3, .t5–.t7; ACC-MAP.wire; ACC-CLS.1; ACC-XREF.48 | Retention; no behaviour change | Accurate. Incorrect behaviour that must stay rejected: an incoherent record acquiring `query_first`. Existing checks: `runner_unit/pwrunner_core_unit_executable` (`OrderingTests` "record eligibility rejects rc" and "errno"); `blackbox_e2e/checker_controls` `order_incoherent_native` for the claimed case on the consumer. Further evidence would not change this: the state needs a validator other than the shipped one. |
| DT-48.t4 | **T1**: state the limit in `21-wire.surface.md` and FPC `:1231` | The inference "validator-sourced `allow` implies native rc 0" is not supported by any check outside `query_first`; the statements should say so. |
| DT-130.a; ACC-RES.order | **T1**: name each recipient's direction in FPC `:1378` and `41-diagnostics.surface.md:678` | The ambiguity is consequential for anyone reading `valid` or crediting the Python control. |
| DT-130.b–.d | Retention of both reader behaviours | See 2.2. New control: one reader-corpus row `ordering-ordinary-withheld` (`orderedOrdinary(applyRC: 0)` with `order` set to `unestablished`), expecting host accepts, Rust admits with `valid`, consumer rejects with `s: eligible record with complete chain requires query_first`. It pins the division on a consistent binary capture; `unestablished_despite_chain` has only a JSON-text carrier. It needs the per-reader expectation described in 3.7. |

**Accepted limits, as sentences beside the claims.** In `21-wire.surface.md` and FPC `:1231`: the sentences in T1. In `41-diagnostics.surface.md:678`: "An `unestablished` order is not compared with eligibility."

### 2.5 Resulting user duties

- Read a validator-sourced `allow` or `deny` together with `native_rc`, `rc` and `errno`. Treat it as a prediction about the live specimen only when `comparison.order` is `query_first`. With the shipped validator the label and the pair always cohere.
- Do not conclude from `disposition_integrity: valid` that every `unestablished` order was unavoidable.

### 2.6 Worklist

1. `docs/contract/21-wire.surface.md:201`, FPC `:1231-1232`, FPC `:1378-1379`, `docs/contract/41-diagnostics.surface.md:678`: the four sentences in T1.
2. `runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift`: row `ordering-ordinary-withheld` (with 3.7 step 3).
3. Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`; `tests/lib/python.sh docs/generate_limits.py --check`.
4. Verify (no rebuild): `tests/run.sh --suite source_drift --case runner_unit/pwrunner_core_unit_executable --case blackbox_e2e/checker_controls`.

---

## 3. DT-53/132/135: lifecycle-claim coverage, byte-consistent readers, shared predicates

### 3.1 Claims

| id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-53.a | FPC requires all seven run questions, matching values and resolved references; the reader section separates the consumer from the oracle; `consumer.validate` alone supplies less lifecycle validation than its description suggests | FPC `:380-430`, `:594-603` | yes | source re-read | consequential ambiguity ("required-field and semantic checks" does not say claims are excluded) |
| DT-53.b | Deleting `final_status`, changing its value 0→17 beside raw exit 0, or nulling it, each still gives `[]` from `consumer.validate` on the bare reply | bare reply, constructed | yes: reproduced now (`contrasts.py` C) | re-executed now | accurate observation |
| DT-53.c | The oracle rejects the first as D8 `malformed_record` "record.questions lacks final_status" and the second as D1 `wrong_answer` | envelope copy | yes: reproduced now; the null edit gives D8 "questions.final_status: claim is not an object" | re-executed now | accurate observation |
| DT-53.d | Those controls do not claim consistency with the binary capture; the unmodified envelope passed both readers | representation | yes | re-executed now | accurate observation |
| DT-53.e | `_validate_worker` requires the disposition object and runs no claim oracle; `validate_shape` allows missing keys and null; the adapter and `_compare_claim` own the rejections | readers | yes: `consumer.py:799-800`, `:322-357`; `lifecycle_adapter.py:112-116`; `lifecycle_oracle.py:408-455` | source re-read | accurate observation |
| DT-53.f | `DispositionResolverTests.swift:345` separately checks producer rejection | host | yes (`:345`, `:383`) | source re-read | accurate observation |
| DT-53.g | Those paths should not receive credit merely because the consumer returned no errors; related to DT-38; separate from DT-52 | credit | yes | n/a | overstated coverage credit wherever it occurs; see 3.3 for where it does |
| DT-53.t1 | Sequence 1–4: host rejects a missing claim; the binary schema makes all seven questions optional; Rust reports `malformed_record` and "final_status contradicts reaped status"; `project` withholds; result selection ignores it | producer to result | yes: `docs/porcelain.json:5326-5337`; `porcelain_admission.rs:203-205`, `:435-462`, `:1342-1355`; `interface/result.rs:166-175`, `:205`; `40-envelope.surface.md:191-194` | source re-read | accurate observation |
| DT-53.t2 | The consumer checks neither claims nor the values of `disposition_integrity` or `process_disposition`, only `subject_path` references | consumer | yes: `consumer.py:954-971`; reproduced now (`contrasts.py` D: a `withheld` projection on a valid record gives `[]`) | re-executed now | accurate observation |
| DT-53.t3 | The oracle checks every claim against its own raw field and that an invalid record is projected `withheld` | oracle | yes: `lifecycle_oracle.py:584-585`, `:665-677`; `contrasts.py` D gives D7 | re-executed now | accurate observation |
| DT-53.t4 | Claim "truth" means agreement with the retained raw field; whether raw fields are independent observations is outside both checks | meaning | yes | source | accurate observation |
| DT-53.t5 | Seam rows `f53-final-status-absent` and `-17`: `finished`/0; Rust `withheld`/`invalid`; consumer `[]`, `[]`; oracle D8 and D1 | byte-consistent frame | yes: Python cells reproduced now | retained | accurate observation |
| DT-53.t6 | DT-53's JSON edits of saved envelopes were refused by the full consumer because they differed from the retained bytes | representation | yes: reproduced now, diagnostic `host result differs from exact captured host reply bytes` | re-executed now | accurate observation; that diagnostic is about the capture, not the claim |
| DT-53.t7 | A null claim has no separate binary form | wire | yes: `json_null: false` at `docs/porcelain.json:5335` | source re-read | accurate observation |
| DT-53.t8 | Thirteen default and two opt-in cases run the oracle | registry | partly: `witness_contract/extension_combinations` also runs it, through `check_extension_boundaries.run_case` (`check_extension_combinations.py:6`; `check_extension_boundaries.py:195-196`) | recomputed now | accurate observation, understated by one |
| DT-53.t9 | Thirty default cases are attributed to the consumer without the oracle; twenty-eight run the app; two assert a Rust diagnostics value a withheld projection would change; two more mention diagnostics without detecting it; twelve opt-in are consumer-only; `failure_boundaries` uses neither | registry | partly: understated. The retained map did not follow `blackbox.validate_run_shape`, `tests/lib/unavailable_prediction.py`, `footprint_workloads.HeldWorkload` or inline shell Python. A transitive text map finds about forty-nine default live cases that reach the consumer and no oracle. The two diagnostics-asserting cases are confirmed (`check_example_round_trip.py:1123-1126`; `check_worker_termination.py:94-96`) | recomputed now | overstated precision; the conclusion is unaffected in direction |
| DT-53.t10 | For the consumer-only live cases a claim fault that only Rust and the oracle check would not fail the case; checked scope, not an observed miss | registry | yes; and on the checkpoint run's retained envelopes the oracle reports no finding for any live envelope (106 case directories carry envelopes; consumer or oracle findings occur only on constructed-control documents: six control cases and the `checker_controls` artifacts inside `runner_specimen_isolation`) | replay now | accurate observation |
| DT-132.a | On a byte-consistent envelope a missing `final_status` and a value 17 each pass Rust to `withheld`/`invalid`, `finished`/0, and the consumer returns `[]` for bare reply and envelope; the oracle reports D8 and D1 | seam | yes: reproduced now | retained | accurate observation |
| DT-132.b | The reader paragraph assigns claims to the oracle; deliberate division, not an unmet consumer promise | FPC `:594-597` | yes as a reading; the text does not say it outright | source re-read | consequential ambiguity |
| DT-132.c | Registry consequence: thirty / twenty-eight / two / twenty-six | registry | partly: as DT-53.t9 | recomputed now | overstated precision |
| DT-135.a | `validatorOwnershipProblem` recomputes with `validatorAssociationIssues`; the order check calls `eligibleOrderedStep`; the oracle's D6 is the consumer's `ownership_problem`; its extension check is the consumer's `validate_extensions` | shared code | yes: `PWRunnerReply.swift:77`, `:365`; `lifecycle_oracle.py:29`, `:560`, `:591`, `:495-498`; `consumer.py:36-37` | source re-read | accurate observation |
| DT-135.b | In `nfd_id`, `nfd_value`, `dup_id` three readers object; only Rust and Python are independent implementations; Swift's silence is its production rule restated | agreement counting | yes | retained | overstated coverage credit where a statement counts the oracle and the consumer as two |
| DT-135.c | FPC `:605-614` quoted in full; the paragraph to `:622` states one procedure and no equality relation | statement | yes, verbatim | source re-read | consequential ambiguity (shared with DT-50.a) |
| DT-135.d | Uniformity holds within each language; "the same way" fixes the procedure, not the equality; counting verdicts does not measure independent confirmation | scope | yes | source | accurate observation |
| ACC-MAP.same | "Same predicate, different inputs": reporting validation can detect a misattached block, plan drift, altered records and an unsupported order claim; it cannot disagree with the production rule; scope, not a defect | Swift reporting | yes: `PWRunnerReply.swift:64-73`, `:359-368` | source re-read | accurate observation |
| ACC-MAP.readers | Boundary-map rows for controller semantic admission, result selection, `consumer.validate`, lifecycle oracle | readers | yes, with one correction: the consumer's order check is `consumer.py:555-558` and its chain adds `arrival_observed` (`:253`) | source re-read | accurate observation |
| ACC-CLS.2 | Agreement row: three objections in `nfd_id` are two independent judgments | readers | yes | source | accurate observation |
| ACC-CLS.7 | Agreement row: lifecycle claims, deliberate division across readers; registry counts | readers | yes for the division; counts as DT-53.t9 | source | accurate observation; counts understated |
| ACC-RES.readers | Results bullets: `finished` co-occurred with Rust `withheld`; `consumer.validate == []` does not certify lifecycle claims or the Rust verdict; Swift reporting acceptance means agreement under the production predicate | envelope | yes | re-run now | accurate observation |
| ACC-XREF.53 | Cross-references: DT-52/53 extended by DT-132 (DT-52 not re-tested); DT-57 another oracle-only judgment; DT-108 did not arise; DT-23/51 and DT-24 neighbours of `dup_id` | review | yes; DT-52 is still not re-tested here | n/a | accurate observation |

### 3.2 Comparison

**Obligation as stated.** FPC "Nesting": "Every question is present in every record; an absent question is malformed, never unresolved" (`:402-403`). FPC "Reader validation responsibilities" (`:594-597`): "`tests/lib/consumer.py` combines shape-golden checks with required-field and semantic checks. `tests/lib/lifecycle_oracle.py` independently checks lifecycle claims and their supporting observations; it is not a complete response-shape validator." FPC `:1379-1380`: "The goldens are allowlists, not required sets: absence is allowed." `tests/README.md:606-608`: "`tests/lib/phase_evidence.py` checks collection status against validator disposition and presence for both the consumer and lifecycle oracle. It is independent of Swift reporting admission and Rust reply admission." `41-diagnostics.surface.md:774-777`: "Host, controller and test readers retain separately authored semantic classifiers… No generated shared classifier or universal equivalence is promised."

**Producer.** Host reporting admission rejects a record that contradicts its basis and degrades the reply (`PWRunnerReply.swift:263-270`), so an ordinary reply with a missing or wrong claim is not a host product. The wire schema allows the absence.

**Readers.** Rust: `validate_lifecycle` then `project` (withheld, invalid), result unchanged by design. Consumer: requires only that a record object exists beside a worker. Oracle: claims, references, projections; its phase and extension findings are the consumer's own functions.

**Tests.** `witness_capture.capture` runs the consumer then the oracle (`witness_capture.py:21-25`). Other live cases call `consumer.validate` directly or through `blackbox.validate_run_shape` (`blackbox.py:175`). The reader corpus runs both readers on Swift-encoded frames. It has a valid degraded baseline and a degraded wrong-exit row (`ReaderCorpusTests.swift:245-263`) and no ordinary-form claim fault, because one Boolean, `expected_semantic`, is compared with the host verdict (`:350`), Rust `admit_reply` (`run_flow.rs:1316`) and the consumer (`reader_corpus.py:118-119`) alike.

**Three contrasts, run now, with the rejecting reader and its diagnostic.**

| Contrast | Carrier | Consumer | Oracle | Rust (retained) | Public result |
| --- | --- | --- | --- | --- | --- |
| Accepted baseline | binary frame, Rust-assembled envelope (`ordinary`) | `[]` | `[]` | `clean_exit`, `valid` | `finished`, true, 0 |
| `final_status` absent | binary, byte-consistent (`f53-final-status-absent`) | `[]` bare and envelope | **D8 `malformed_record`: `record.questions lacks final_status`** | **`withheld`, `invalid`: `malformed_record` "final_status: missing claim"** | unchanged: `finished`, true, 0 |
| value 17 beside raw `exit_code` 0 | binary, byte-consistent (`f53-final-status-17`) | `[]` bare and envelope | **D1 `wrong_answer`: `expected {'state': 'supported', 'answer': 'exit_code', 'value': 0}, record says 'exit_code' 17`** | **`withheld`, `invalid`: `invalid_claim` "final_status contradicts reaped status"** | unchanged |
| either edit | JSON projection edited, binary bytes left | `host result differs from exact captured host reply bytes` | D8 / D1 as above | n/a | n/a |
| either edit | JSON-text carrier (`recapture_host_reply`), `validate_fixture` | `[]` | D8 / D1 as above | never reads it | n/a |
| either edit | JSON-text carrier, `consumer.validate` | `unreadable host bytes require null host result and a host-byte diagnostic` | D8 / D1 | n/a | n/a |

The responsible readers for both faults are the lifecycle oracle and the controller's lifecycle family. The consumer is not, by assignment. The fourth row matters for crediting: a test that edits a live envelope's JSON and sees the consumer object has observed the capture comparison, not a claim check.

**Text versus binary capture for whole-envelope claims.**

- Binary, consistent: every live case; the reader corpus and the Rust-launched replays in `runner_unit/pwrunner_core_unit_executable` (`validate_fixture` is called, and the binary path is taken); `source_drift/porcelain_codec`.
- JSON-text carrier (`recapture_host_reply`, `bind_constructed_envelope`, `envelope_skeleton`, `validate_fixture`): `blackbox_e2e/checker_controls` (with `disposition_controls.py` and `extension_controls.py`), `blackbox_menagerie/validation_controls`, `runner_filter_sysctl_name/checker_controls`, the checker controls inside `runner_specimen_isolation`, `witness_contract/test_input_controls`, `witness_contract/example_round_trip_controls` (`allow_fixture_json=True` at `:1812`), `run_effects/checker_controls`. Rust never reads these documents.

### 3.3 Caller list for the selected DT-53/132 correction

Scope searched: `tests/COVERAGE.md`, FPC coverage and ownership rows (`:670-688`, `:1535-1548`) and matrix rows, suite READMEs, `tests/README.md`, catalog descriptions, and `check:` entries in `docs/contract/*.surface.md`. No contract surface support entry credits lifecycle claims to a consumer-only check: the lifecycle surface's support entries are `source_read`, and the diagnostics corpus entry (`41-diagnostics.surface.md:758-770`) names the corpus, which runs both readers.

**A. Callers with lifecycle-related credit that do not run the oracle.**

| Caller | Credit | Readers invoked | What it asserts | Decision |
| --- | --- | --- | --- | --- |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict` (`check_pre_apply_failure.py`) | FPC `:683` "Independent attribution, lifecycle and consumer-validation groups"; `COVERAGE.md:236` "the comparison carries the lifecycle limitation"; suite README `:1157-1159` | `consumer.validate` (`:83`, `:292`, `:339`) | Raw host observations (`:173-186`); `attempt:not_reached` in limitations (`:94`); `termination_cause` in a set that admits `unknown` (`:72-73`). A withheld projection would pass | **Invoke the oracle**: add a group `{name}.lifecycle_claims` calling `lifecycle_oracle.check_record` after `:253`, for both runs. It is the only default live case found that produces a pre-application deadline record (`worker_pre_ready_hang_ms` elsewhere is used with a sufficient budget), and it asserts a lifecycle projection. Replay now over its seven retained checkpoint envelopes gives no oracle finding. Also say "raw lifecycle-observation" at FPC `:683` |
| `witness_contract/worker_termination` | catalog "preserve worker disposition"; FPC `:687` "execution diagnostics" | `consumer.validate` (`:97`) | `process_disposition` and `termination_cause` equal the scenario's own expectation (`:94-96`); a withheld projection fails it | **No change.** The credit is an assertion of the controller's projection against an independent expectation, which is what the row says |
| `witness_contract/example_round_trip` | suite README `:1329` | `consumer.validate` (`:1099`) | `disposition_integrity == valid`, no issues (`:1123-1126`) | **No change.** The README credits exactly the controller's verdict |
| `witness_contract/comparison_matrix`, row C1 | generated matrix: Limitations `attempt:not_reached` | `consumer.validate` (`:221`) | The limitation equals the authored row | **No change.** A projection value against an authored expectation; no claim-record credit |
| `runner_outcome_runner_timeout/host_kills_hung_worker`, `runner_use_c_worker/worker_timeout_ms_honored`, `witness_contract/worker_post_apply_hang_seam`, `runner_apply_isolation_v2`, `_v3` | `COVERAGE.md:21` and suite READMEs: `partial_steps=false` | none or consumer | `partial_steps` by direct equality | **No change.** Direct assertion of one projection |

**B. Consumer-only callers with no lifecycle-claim credit found** (about forty-nine default live cases by the transitive map): `blackbox_e2e` BBX cases and `blackbox_menagerie` (through `validate_run_shape`), `runner_filter_*`, `runner_specimen_isolation`, `runner_use_c_worker/happy_default_allow`, `sbpl_allowdeny_consistency`, `runner_exec_dac`, `runner_exec_lifecycle`, `runner_validator_failure`, `runner_outcome_validator_no_reply`, `run_effects/aftermath_footprint`, and the remaining `witness_contract` cases (`check_ordering.py` family, `dossier_witness`, `test_input`, `worker_progress_and_failure`, `worker_sparse_failure`, `unfamiliar_diagnostic_transport`, `max_targets_reply_survives`, `held_phase_footprint`, `response_footprint`, others). Their accounts say the consumer "validates the envelope" (`blackbox_e2e/README.md:40`, `blackbox_menagerie/README.md:34`, `runner_specimen_isolation/README.md:23`) or name consumer invariants (FPC `:1545`). **Decision: narrow once, in the owner** (3.4 T1); no per-case edit and no added oracle. Do not broaden the consumer.

**C. Callers that already run the responsible check.** The cases in DT-53.t8, plus `witness_contract/extension_combinations`. No change.

### 3.4 Plausible treatments

**T1. State the division in its owner.** FPC `:594-597`, after the first sentence: "The consumer does not check lifecycle claims: a record whose claim is absent or contradicts its raw field passes it. The lifecycle oracle and the controller's lifecycle checks reject such a record, and the envelope result is unchanged." Not a shared region; no build-contract input.

**T2. Retain the three contrasts on a consistent binary capture, in the reader corpus.** `runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift`, from `orderedOrdinary(applyRC: 0)`: rows `lifecycle-ordinary-final-status-absent` and `lifecycle-ordinary-final-status-17`, with `ordering-ordinary` as the accepted baseline (give it `expected_lifecycle_findings: []`). Needs a per-reader expectation because the readers divide: host rejects, Rust `admit_reply` admits while its projection withholds, the consumer accepts, the oracle rejects. Edits: Swift row keys `expected_host` and `expected_projection`; `tests/suites/runner_unit/reader_corpus.py` reads `expected_consumer` (default `expected_semantic`) and asserts `expected_projection` against the Rust-assembled diagnostics. `controller/src/run_flow.rs` needs no edit: it copies row keys through (`:1384`) and its admission expectation stays true. `runner/Tests` and `tests/suites` are not build-contract inputs: **no signed rebuild**.

**T3. Invoke the oracle in `pre_apply_failure`.** `tests/suites/witness_contract/check_pre_apply_failure.py` only.

**T4. Narrow statements that credit independence (DT-135).**

- `tests/COVERAGE.md:201`: "…its reply is replayed through Rust assembly and the Python consumer and lifecycle oracle, whose phase-collection and ownership checks are one shared implementation."
- `tests/suites/blackbox_e2e/extension_controls.py:129-130` (comment): "…Each reader entry point must reject the transplant for the stated reason; the lifecycle oracle surfaces the shared phase-evidence finding."
- `tests/lib/lifecycle_oracle.py` module docstring: add "D6 phase-collection and extension findings come from `phase_evidence` and `extension_evidence`, which the consumer also calls; they are not a second judgment."
- Already accurate; no change: `tests/README.md:606-611`; FPC `:1278-1281` ("both Python reader entry points"); `41-diagnostics.surface.md:745-777`; `docs/CONTROLLER.md:334-341`; `docs/architecture.json` scopes naming one "Independent reader"; the `executed` corpus contexts at `41-diagnostics.surface.md:765` and `33-actor_evidence.surface.md:161`, where "independent Python readers" means independent of Swift and Rust.

**T5. Invoke the oracle in every consumer-only live case, or fold claim checks into the consumer.** Not recommended. No credited claim requires it; the overhaul plan excludes broadening the consumer; the management plan excludes a reader added for uniformity. The replay shows the oracle would pass on current output, so the cost is small, and the choice stays open as a coverage decision.

**T6. Add an independent Swift reporting predicate or a second Python phase reader (DT-135).** Not recommended: the shared predicate checks different inputs, which is its stated purpose, and Rust plus Python already supply two independent implementations.

### 3.5 Recommended disposition

| Claim | Disposition | Reason and discriminating check |
| --- | --- | --- |
| DT-53.a, DT-132.b | **T1** | The division is real and deliberate; the text should say it. |
| DT-53.b–.f, .t1–.t7; DT-132.a; ACC-RES.readers; ACC-XREF.53 | **T2**: retain the contrasts in the corpus; no reader change | Incorrect behaviour the rows must reject: an oracle or controller that accepts an absent or wrong `final_status`; a consumer verdict credited as a claim check; a result that changes with the finding. Case: `runner_unit/pwrunner_core_unit_executable`. |
| DT-53.g, .t10; ACC-CLS.7 | **T3** for `pre_apply_failure`; group B narrowed by T1; others unchanged | Table 3.3. Per the overhaul plan, run the revised checker against existing behaviour first; the replay predicts no finding. |
| DT-53.t8, .t9; DT-132.c; ACC-LIM.b | Record the corrected population in the management plan's disposition; no tree change | The counts are a lower bound; the retained `reader-case-map.jsonl` should not be reused as a complete list. |
| DT-135.a, .d; ACC-MAP.same; ACC-MAP.readers; ACC-CLS.2 | Retention | Accepted limit, beside the claim (the docstring sentence in T4, and FPC `:605-622` through 1.7 step 8 or the T5 sentence in 1.5): agreement between the consumer and the oracle on phase collection, ownership or extension evidence is one judgment; agreement between host reporting and host production on association or order is one predicate over two inputs. |
| DT-135.b | **T4** | Three statements credit independence the code does not have. |
| DT-135.c | Resolved with subject 1 | The missing equality relation is the same omission as DT-50.a. |

### 3.6 Resulting user duties

None for an ordinary user beyond what `40-envelope.surface.md:191-194` already states: `result.ok` and exit 0 do not certify the controller's relationship checks; read `disposition_integrity` and `disposition_issues`.

For test authors: `consumer.validate == []` does not establish lifecycle claims; run `lifecycle_oracle.check_record` or assert the controller's projection where a case credits them; do not count a consumer rejection of a JSON-edited live envelope as a claim check.

### 3.7 Worklist

1. FPC `:594-597`: the T1 sentence.
2. `tests/COVERAGE.md:201`, `tests/suites/blackbox_e2e/extension_controls.py:129-130`, `tests/lib/lifecycle_oracle.py` docstring: the T4 edits. FPC `:683`: "Independent attribution, raw lifecycle-observation, lifecycle-claim and consumer-validation groups…" (with step 4).
3. `runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift`: per-row `expected_host` (the `:350` comparison uses it when present), the two lifecycle rows, `expected_lifecycle_findings` on `ordering-ordinary`, `expected_projection` on the lifecycle rows, and row `ordering-ordinary-withheld` from 2.4. `tests/suites/runner_unit/reader_corpus.py:118-119`: use `case.get('expected_consumer', expected)`; add the `expected_projection` assertion beside `:94-96`. Update `tests/suites/runner_unit/README.md` where it describes the corpus rows.
4. `tests/suites/witness_contract/check_pre_apply_failure.py`: import `lifecycle_oracle`; add the `lifecycle_claims` group after `:253`; update suite README `:1157-1161`.
5. No regeneration except `tests/lib/python.sh docs/generate_limits.py --check` after the FPC edits.
6. Verify (no signed rebuild): `tests/run.sh --suite source_drift --case runner_unit/pwrunner_core_unit_executable --case witness_contract/pre_apply_failure_reports_no_policy_verdict --case blackbox_e2e/checker_controls`. The oracle's own sensitivity stays with `blackbox_e2e/checker_controls` (`disposition_controls.py`); the new group's wiring has no separate rejected control, and the corpus rows supply the reader-level rejection.

---

## Outside the review

These are not findings of the review and are not added to it.

1. **The consumer's chain is stricter than the stated chain.** `_ordering_chain` also requires `arrival_observed` (`consumer.py:253`); the "Collection chain" condition (`31-steps.surface.md:601`), Swift `chainEstablished` (`PWRunnerStepEvidence.swift:107-110`) and Rust (`porcelain_admission.rs:1189-1195`) do not. No host-produced divergence was found by reading. It bears on the T1 wording in 2.3: the consumer's forward direction checks one condition more than the rule states.
2. **Reply `operation` can carry the validator's spelling** (1.3 item 5). Under T3 a byte-different operation becomes `query_mismatch` and the field returns to the submitted bytes; under T5 the field meaning "The admitted query operation" needs the same qualification.
3. **`same_submitted` across runtimes.** Swift compares with the OS runtime's Unicode data and the consumer with the pinned Python's (16.0). For code points assigned after the older database the two could disagree. Inference only; not observed.
4. **The reader corpus encodes one verdict for three readers** (`expected_semantic`). That is why it holds no ordinary-form claim fault; 3.7 step 3 addresses it.
5. **Worker slot joins also use `String` keys** (`CWorkerDisposition.swift:6-8`, `CWorkerStepResults.swift:40`, `:54`). The slot identifier is child output. No reply field exposes it separately, so no reader can disagree, and the association rehearsal does not cover it. If T3 is taken, decide whether slot identity follows the same byte rule.

## Count

Claims assessed: 87 (section 0: 11; subject 1: 24; subject 2: 22; subject 3: 30).
