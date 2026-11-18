# J-wire-identity — DT-105–112: wire identity and public JSON projection

Read-only assessment at HEAD `837296af`. Coverage-map row: "DT-105–112 — wire
fingerprint, variant production, conditional-null projection, path compaction,
reader rule order and shape/support coverage; qualify identity sensitivity
independently of actual admission discrimination." One shared subject, assessed
once below; entries, subfindings and qualifications keep their original
identifiers. The section's conventions and its coverage/limits carry no DT
number in the review; they appear here as `CONV.x` and `COV.x` labels, which
are row labels of this file only.

## Summary

58 claims assessed. Nearly all hold at HEAD. Six review statements are
narrower than written or need a refinement: CONV.d, DT-106.f, DT-107.c,
DT-109.b, DT-111.c and DT-111.g. The Rust-side executed rows (DT-107.f and the
Rust columns of DT-108) were not replayed; source reading agrees with them.

- **One product change is recommended (T-C, DT-108):** both readers refuse a
  frame that carries a conditional-null field without its guard. Today that
  frame is admitted and the carried value is absent from public JSON. No
  shipped producer can build the state; only a constructed frame or a
  different producer asserting this contract can. It needs one signed rebuild.
  The fallback is a stated limit (T-D).
- **Four repairs need no rebuild:** schema validation rules that refuse the
  combinations on which the two readers' rule orders disagree, a variant whose
  JSON does not identify its case, and unknown variant-case keys (T-A);
  presentation mutations in the fingerprint test (T-B); an exact comparison
  against a corrected normal fixture, with the shape-check credit narrowed
  (T-I); the Python actor reader's missing identifier requirement (T-G).
- **The rest is retained with stated limits:** fingerprint breadth (T-K), the
  hand-written Swift variant writer (T-J), path-form compaction (T-H), a
  synthetic result carrying a native return (T-F) and unchecked digest width
  (T-L). No non-frozen document states the compaction's size rationale, so
  there is no stale rationale to remove.

## Basis

**Files.** The ten files the review hashed are byte-identical at HEAD
(`git diff --stat b377cb8a HEAD` over them is empty; SHA-256 prefixes and
suffixes match the review's list). The review's line numbers for those files
are therefore current, except that it cites the wire surface one line high
(its "103" and "111" are lines 102 and 110).

Abbreviations: **GP** `docs/generate_porcelain.py`; **PJ** `docs/porcelain.json`;
**PY** `tests/lib/porcelain.py`; **RS** `controller/src/porcelain.rs`; **RR**
`controller/src/porcelain_records.rs` (generated); **SW**
`runner/Sources/PWRunnerCore/PWPorcelain.swift`; **WS**
`docs/contract/21-wire.surface.md`; **PC**
`tests/suites/source_drift/porcelain_codec.py`; **PRP**
`tests/suites/runner_unit/porcelain_replies.py`.

**Evidence classes used in the tables.**

- **[X]** executed by the review; its run `tests/out/runs/wire-identity-trace`
  and its scratchpad drivers are absent now. Not replayable.
- **[S]** source read at HEAD for this assessment.
- **[M]** re-executed now, in memory: `validate`, `wire_identity`, `swift`,
  `rust` and `python_tables` from GP over mutated copies of PJ. Nothing written.
- **[F]** re-executed now with the Python reader over the 261 Swift-emitted
  `.pwp` frames retained under
  `tests/out/runs/trace-instrument-after-corrected/suites/runner_unit/pwrunner_core_unit_executable/artifacts/`
  (run `20261118T011154Z_5cfcec0a`, `ok: true`). Constructed frames.
- **[L]** observed now in that run's retained live envelopes: 608 `kind: run`
  envelopes outside `runner_unit` carry a binary host frame and a
  `data.runner_result` written by the signed app (commit `2f4d76e4`, contract
  `development:b55acb20…719e`, equal to `docs/build_contract.py` at HEAD).
- **[C]** re-executed now on constructed in-memory records (hand-assembled TLV).

[F] and [L] rest on disposable development output with no retention guarantee.
No Rust or Swift code was compiled or run. Rust-side statements rest on [S]
(generated text and admission source) and, for live frames, on the Rust
projection recorded in the retained envelopes.

Probe scripts, all read-only, are in
`.tmp/trace-integration/assessments/work-J-wire-identity/`:
`probe_identity.py`, `probe_projection.py`, `probe_guard_states.py`,
`probe_paths.py`, `probe_live_null.py`, `probe_presence.py`, `probe_subset.py`,
`probe_rules.py`, `probe_refusal_sketch.py`. Each runs as
`tests/lib/python.sh -I <script> <artifacts-or-run-dir> "$PWD"`
(`probe_rules.py` takes only `"$PWD"`).

**Working tree.** While this pass ran, another actor changed
`tests/catalog.json` and `tests/suites/source_drift/run.sh` and added
`tests/suites/source_drift/test_markdown_reader.py` in the working tree
(a `source_drift/markdown_reader` conversion). This pass did not touch them.
Every citation here is to HEAD content; the case identifiers used below are
unchanged by that edit.

---

## 1. Claims table

Classification vocabulary: contradicted explicit commitment (CEC); consequential
ambiguity (CA); unsupported inference (UI); inaccurate mechanism account (IMA);
overstated coverage credit (OCC); accurate observation needing no change (AO).

### Conventions (`CONV`)

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| CONV.a | Ten named files had the listed hashes at `b377cb8a`; schema, generator and readers last changed in `897be512`. | Tracked bytes; observer: `shasum`; time: 2026-11-16. | Yes. All ten are byte-identical at HEAD. | [S] hashes recomputed now. | AO |
| CONV.b | The app was `8b5de2b2` with contract `development:bdefcb44…`, equal to HEAD's identity then. | Signed app `--version`; time of review. | No. `dist/PolicyWitness.app` now reports commit `2f4d76e4`, contract `development:b55acb20…719e`; `docs/build_contract.py` prints the same value at HEAD. | `--version` and `build_contract.py` run now. | AO (historical) |
| CONV.c | Run `20261116T213728Z_d05f0e15` passed three cases; 261 Swift frames and nine probe drivers supplied the executed values. | Disposable run output and scratchpad. | Unverifiable: both are absent. A later default battery (`20261118T011154Z_5cfcec0a`) retains 261 Swift frames from the same test source. | [X]; replaced here by [F]. | AO |
| CONV.d | Independent recomputation of the fingerprint (`80013e5b…e224`) equalled the generated constants and all 261 frame headers; the identity JSON is 48,563 bytes; "the descriptor spellings are not in any statement", so the recomputation is "not an independent specification". | PJ → identity JSON → SHA-256; observer: separate writer. | Partly. Values hold: [M] gives `80013e5b…e224`, 48,563 bytes, equal to `tests/lib/porcelain_schema.py:2`, RR:7, the Swift constant and all 261 retained headers. The last sentence is incomplete: WS:32 says identities are "those of the declared wire schema retained with the wire surface's canonical shape", and that golden, `tests/fixtures/contract/surfaces/wire.json`, holds the whole identity JSON as `wire_schema` (`docs/contract/runtime.py:158-159`). It equals `wire_identity(PJ)` and its compact sorted JSON hashes to the fingerprint (checked now). | [M], [F]; the review's own writer is [X]. | AO, with the review's inference corrected |

### DT-105

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-105.a | Every change the statement names moves the fingerprint; provenance, storage names and `Int`/`Int64` on a field do not. | Schema in memory → generator; time: generation. | Yes. GP:275-298 (`wire_identity`), GP:13-15, 81-86 (`descriptor`). | [M]: 13 of the review's rows re-run with the same fingerprint/output pattern. | AO |
| DT-105.b | The Swift writer consumes only record IDs, tags, stored types and optionality; a producer from an older schema writes the same bytes after a rename, null-rule flip, projection change, path-form or conditional edit, record reorder or rename, variant-case rename or root-key rename. | Generated Swift writer text; producer bytes. | Yes. GP:154-171 emits IDs, tag constants and `writer.field` calls only. | [M]: for null flip, projection, path-form order, conditional removal, root rename the Swift output differs only in the fingerprint line; rename and reorder change identifiers or declaration order, not written bytes [S]. | AO |
| DT-105.c | After an added optional field, or a removed conditional rule, all 260 reply-rooted frames decode and project identically, yet the new fingerprint refuses them. | Swift frames under mutated receiver tables, header ignored. | Yes. | [F]: 0 of 260 frames differ for both mutations; fingerprint changed in both. | AO |
| DT-105.d | The fingerprint constants are build-contract inputs, so in the controller the fingerprint check refuses no frame the exact-contract check would admit. | Producer built by the pipeline; receiver `decode_bound`. | Yes, for producers whose contract string is derived by `docs/build_contract.py`: RR and `PWPorcelainRecords.swift` lie under `controller/src` and `runner/Sources` (`docs/build_contract.py:15-25`); RS:182-184 then 218-220; `controller/src/runner_client.rs:715, 752-756`. Not for a frame that asserts the receiver's contract with another fingerprint (constructed frames, and unit-test contexts that share `test:policy-witness`). | [S]. | AO, boundary stated |
| DT-105.e | The fingerprint check's own effects are a different message under the same refusal code, a refusal before the producer context is decoded, and the only identity check for unbound readers. | Controller refusal path; unbound `decode`. | Yes. `runner_client.rs:627-629`; RS:155-161, 182-184; PY:143-150. | [S]. | AO |
| DT-105.f | A schema mismatch does not name the foreign producer; a contract mismatch does. | Controller diagnostics. | Yes. `runner_client.rs:760-769`. | [S]. | AO |
| DT-105.g | "Changes to … null/projection rule … require exact receiver agreement" treats a receiver-local rendering choice as a producer/receiver protocol change. | WS:102 statement versus what a producer writes. | Yes as an observation; the sentence is literally true of the mechanism. | [S], [M]. | AO; retained with a stated limit |
| DT-105.h | Tentative judgment: needlessly broad rather than wrong; an identity over binary structure, or reading the producer context before refusing, are alternatives. | Design judgment. | The premise holds; the second alternative conflicts with WS:82, 86 (see Comparison). | [S]. | AO (judgment) |

### DT-106

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-106.a | `json_null` is ignored on path-form and conditional-null fields by the Rust generator, the Python reader and the documentation generator; the authored flags differ; flipping `native_rc`, `team_id` or `realpath_resolved` changes only the fingerprint and Python table lines. | Schema flag → three interpreters. | Yes. GP:235-245; PY:90-106; `docs/contract/record_definitions.py:377-381`. | [M]+[F]: three flips give a changed fingerprint, unchanged Rust text apart from the constant, 0 of 260 frames projecting differently. | AO |
| DT-106.b | `json_null: true` on a required field is accepted by `validate()`; only the fingerprint changes. | Schema validation. | Yes. GP:89-151 has no rule on `json_null`; GP:244-247. | [M] on `CompiledProfileCapture.status`. | AO |
| DT-106.c | Variants are fingerprinted verbatim: `Int`→`Int64` in a variant case changes the fingerprint while Rust and Python output do not change; on a field it does not change the fingerprint. | `wire_identity` variant branch. | Yes. GP:298 versus GP:286. | [M]. | AO |
| DT-106.d | A `doc` key on a variant case changes the fingerprint, an unknown key on a field does not, and `validate()` accepts both, although WS says descriptive text remains source provenance. | Schema keys → identity. | Yes. GP:298; GP:128-136 checks only `name` and `type`. No variant case carries such a key today. | [M]. | IMA (an unexercised exception to WS:102) |
| DT-106.e | Case names are neither on the wire nor in public JSON; they name Rust enum cases, RESPONSE's "Alternative" column and `is_variant(…)` operands; they change the fingerprint. | Names in generated code and documents. | Yes. RR:13-16; `docs/RESPONSE.md:1904-1907`. | [M] (`Integer`→`Number`: Rust enum only). | AO |
| DT-106.f | The fingerprint tests are a comment control and five structural mutations; none mutates a public name, null rule, projection, path-form or conditional rule, default, source path, record order, variant or root. ARCHITECTURE row 942 and D78 cite them for presentation rules; the presentation half of the statement had only source-read support. | PC:470-539; `docs/architecture.json:3824-3842, 5618-5637`. | Partly. The test inventory holds. The last sentence omits one registered support: `generate_contract_stamps.py --check` (run by `build.sh:227` and by `source_drift/build_contracts`) refuses when `surfaces/wire.json` differs from `wire_identity(PJ)` (`runtime.py:158-159, 173-180`), so any change to a fingerprinted presentation property is a refused, reviewed golden difference. That check pins the identity input; it does not show the fingerprint moves. | [S]; golden equality checked now. | OCC for the two architecture citations |

### DT-107

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-107.a | `swift()` emits record writers only; `PWDispositionValue` and its writer are hand-written with literal case tags 1 and 2; the Rust enum/reader and Python `VARIANTS` are generated. | Generator versus authored Swift. | Yes. GP:154-171; `PWRunnerDisposition.swift:49-52`; SW:115-126; GP:183-190, 268. | [S]. | AO; "Swift writers" in two accounts is imprecise (IMA, minor) |
| DT-107.b | Swapping the two schema case tags generates successfully: Swift changes only in the fingerprint, Rust and Python swap; `--check` compares generated text only; under the swapped tables every frame with a disposition claim value is refused. | Mutated schema → outputs; Swift frames under swapped tables. | Yes. GP:337-345. | [M]+[F]: Swift text unchanged apart from the constant; 153 of 260 frames refused. A compiled build from that tree was never made. | AO |
| DT-107.c | The registered checks would catch this at test time, not build time: the Rust literal-tag test, the Python variant control and the `runner_unit` corpus replay. | Registered cases. | Yes, with a refinement. RS:553-595 and PC:125-129 compare the *schema's* tag assignment with literals; they do not read the Swift writer. An edit of the Swift literals alone is rejected only by checks that decode Swift-written frames (`runner_unit/pwrunner_core_unit_executable`, and every live case, where the controller would report a malformed reply). | [S]. | AO |
| DT-107.d | The case payload types are also hand-written in Swift. | Authored Swift enum. | Yes. `PWRunnerDisposition.swift:50-51`. | [S]. | AO |
| DT-107.e | The untagged projection is recoverable only because the two cases have different JSON types; `validate()` accepts a variant with two integer cases. | Public JSON of a variant; schema validation. | Yes; hypothetical schema only. RR:12; PY:128-137. | [M]: adding case 3 `Signal: Int` is accepted and generated. The current cases are a number and an object. | AO; guard available |
| DT-107.f | Four one-property variant edits of `ordering-ordinary`: Rust `admit_reply` raises no issue, the envelope reports `disposition_integrity: invalid`, the consumer has a finding only for the Request-typed value, the oracle reports D1/D8, and the outcome is unchanged. | Edited binary frame → Rust unit-test binary and Python readers. | Unverifiable by reading alone. Consistent with `controller/src/porcelain_admission.rs:127-132, 1651-1656`. | [X]; needs the Rust test binary. | AO; repeats DT-53 on binary frames, disposition belongs to the DT-53/132 row |

### DT-108

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-108.a | Dependent and guard are independent optional tags; structural admission accepts any combination; projection drops the dependent when the guard is absent; no reader compares the two first. | Received frame → typed record → public JSON; observers: both readers. | Yes. GP:205-222 (no relation in `read_payload`); RR:3523, 2133; PY:102-104. | [C]: record 56 with `native_rc` 7 and no `result_source` projects with both keys absent; record 36 with `team_id` and no `identifier` likewise. | CA: WS:110 "carried only when their guard has a value" is silent on a dependent that was received without its guard |
| DT-108.b | Rust semantic admission reads typed values and could see the dropped dependent; Python readers read the projection. | Reader inputs. | Yes. `porcelain_admission.rs:1188-1208`; `tests/lib/consumer.py:268-279`. | [S]. | AO |
| DT-108.c | The shipped host sets `result_source` on every built query; the guard-absent state never occurs in the Swift frames; removing the rule changes no frame and no shape document. | Shipped producer; Swift corpus. | Yes. `CWorkerStepResults.swift:46-49` is the only site that builds the record's provenance (callers `CWorkerOrchestrator.swift:179`, `ActorOrchestration.swift:342`); `native_rc` is set only from a verdict, which implies `validator`. Equipment `identifier`/`team_id` are assigned together (`ActorEquipment.swift:410, 452`). | [S]; [F]: across 261 frames, 0 query records without the guard and 0 dependents without a guard in any of the three records; [L]: 0 of the query results in 608 live envelopes lack `result_source`, 0 are `synthetic` with a non-null `native_rc`. | AO |
| DT-108.d | On the `query_first` base, three different wire states project to one JSON and draw the same issue, which comes from the ordering rule's `result_source == "validator"` requirement and not from a presence check. | Edited frame → Rust admission, Python reader. | Yes by source: `porcelain_admission.rs:1204-1226`. | [X] for the Rust runs; [C] for the projection. | AO |
| DT-108.e | On the synthetic base a carried `native_rc` of 5 with no guard reaches the envelope invisibly; it is admitted with no finding; only the retained host bytes show it. | Edited frame → envelope. | Yes by source: the pair is read only inside the ordering rule (`porcelain_admission.rs:1204-1217`); the other reads of the query record (lines 777, 1004, 1055, 1734) concern operation, filter and `missing_reason`. | [X] for the Rust run; [C] for the projection. | CA: a received value is absent from the public record and no stated rule says so |
| DT-108.f | A synthetic result with a non-null `native_rc` contradicts RESPONSE 962, and every reader accepts it. | Constructed frame → all readers. | Yes. `docs/contract/31-steps.surface.md:59` is a producer statement that the shipped producer satisfies; no `checks` node, Rust rule, Swift rule or Python rule tests it. | [C]: projects as `synthetic` / `5`; [S] for the readers. | UI if the definition is read as reader-enforced; otherwise AO |
| DT-108.g | `identifier` removed with `team_id` kept: both keys absent in JSON; Rust refuses with "equipment bound observations"; the Python general, actor and extension readers return no finding (recorded as a lead). `team_id` removed projects `null` and is admitted. | Edited equipment binding → readers. | Yes; the lead is confirmed by reading. Rust `porcelain_actor.rs:1869-1876` and Swift `PWRunnerEquipment.swift:229-231` require a nonempty identifier on a bound row; Python `tests/lib/actor_evidence.py:302-309` does not. | [C] for the projection; [S] for the three readers; [X] for the runs. | AO; a Python reader omission |
| DT-108.h | Tentative judgment: the rule turns an internally inconsistent record into a consistent-looking public one; a stated presence relation would more naturally be refused at admission or projected visibly. | Design judgment. | Premise holds for frames no shipped producer builds. | [S], [C]. | AO (judgment) |

### DT-109

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-109.a | The nine Swift path-state frames project identically in Rust and Python; each form is in exactly one of three states; the NFD spelling stays a separate string. | Swift frames → both projections. | Yes for Python. | [F]: all nine states reproduced; Rust side [X] and [S] (RR:2924-2948). | AO |
| DT-109.b | The nine frames are replayed only by Python; in the cross-reader corpus the null state never occurs (264 equal, 248 different). | Registered cross-reader comparison. | Partly. The corpus counts hold exactly ([F] over the retained `rust.json`: 264 / 248 / 0). A second cross-reader comparison exists: `validate_client` requires the Python projection of the retained host frame to equal `data.runner_result` (`tests/lib/runner_client_capture.py:440-449`, reached from `tests/lib/consumer.py:1016`). | [F]; [L]: 608 of 608 live envelopes equal, 37 of them (seven suites) carrying a null path form. | AO; qualified |
| DT-109.c | `same_as_input` was introduced in `085bffc7` because a maximum JSON reply exceeded the then 1 MiB retention cap; JSON was then the transport; today the host writes every resolved form onto the wire and only the projection compacts. | History; host writer; projection. | Yes. Commit message read; `PWRunnerService.swift:422-453`; GP:235-250; PY:93-101. No non-frozen document states the size rationale (see Comparison). | [S]; [F]: frame `0-0` contains the input bytes six times. | AO |
| DT-109.d | One live run: a 3,663-byte host frame containing the path 11 times; the 19,809-byte envelope carries the frame as base64 (24.7%) beside the compacted projection. | Live envelope. | Not replayable; the same structure is present in a retained envelope. | [X]; [L]: `blackbox_e2e/BBX-001` envelope 33,352 bytes, frame 7,637 bytes, base64 30.5% of the envelope, target path 11 times in the frame and 8 times in the projected JSON. | AO |
| DT-109.e | Cost: about 40 guide lines, a dedicated exclusivity checker, a `#[cfg(test)] same_as_input` field, test fixtures whose typed forms are `None` while listed as equal, a test-only override that drops a differing value, and no controller code reading the typed fields. | Maintenance surface. | Yes. `tests/lib/consumer.py:105-142`; GP:201-202, 220-221, 236-238; `controller/src/reply_fixtures.rs:27-38`. | [S]. | AO |
| DT-109.f | Tentative judgment: lossless and consistently implemented; the stated benefit no longer applies at the wire or the envelope; emitting each form as a string or null would keep the byte-identity distinction. | Design judgment. | Premise holds. No current limit bounds public JSON size (`docs/limits.json` bounds binary frames and retention). | [S]. | AO (judgment) |

### DT-110

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-110.a | Generated Rust handles each field by the first matching branch (path form, conditional null, optional without `json_null`, otherwise always); Python applies `json_null`, then path forms, then conditional rules, reading the guard from the already-projected result. | Projection code of the two readers. | Yes. GP:227-247; PY:86-106. | [S]. | AO |
| DT-110.b | `validate()` does not prevent a guard or a dependent from being a path form. | Schema validation. | Yes. GP:105-111. | [M]. | AO |
| DT-110.c | With `conditional_null: {"observer": "realpath_resolved"}` on `PWRunnerPathDiagnostics`, accepted by `validate()`, Python drops `observer` when the realpath equals the input while the generated Rust branch keeps it. | Constructed schema; Rust side is generated text, not compiled. | Yes. | [M]+[C]: accepted; generated line `if self.realpath_resolved.is_some() { map.serialize_entry("observer", …) }`; Python drops `observer` for the equal state and agrees for the other two. | AO |
| DT-110.d | The current schema has no such combination, so the observed agreement depends on authored data that neither `validate()` nor any test constrains; the Python projection control exercises each rule alone. | PJ at HEAD; PC:157-181. | Yes. Only a hypothetical schema expresses the case: records 26 and 48 declare path forms, records 36, 39 and 56 declare one conditional rule each, and no record declares both. | [M] inventory of PJ. | CA for future schema edits; none for the shipped schema |

### DT-111

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-111.a | Traversal and projection are implemented twice, but every field rule has one source; the cross-reader corpus compares complete dicts and cannot detect a mistaken flag. | PJ → both readers and RESPONSE phrases. | Yes. `tests/suites/runner_unit/reader_corpus.py:56-60`; `record_definitions.py:497-509`. The live comparison named at DT-109.b shares the same limit. | [S]. | AO |
| DT-111.b | The shape golden does not encode presence or byte spelling: five of six table mutations change 0–30 shape documents and leave the golden unchanged. | 64 shape frames → `collect_shape` → `response_shape.json`. | Yes. PRP:44-62, 109-126. | [F]: identical counts (7, 2, 22, 30, 0 unchanged; 23 changed) with the production `collect_shape`. Of 328 optional wire fields, the 64 frames show 219 absent somewhere, and all 219 are also present somewhere, so no omit/null flip on an exercised field can alter the golden. | OCC: `tests/fixtures/README.md:24` and PRP:29 say shape checks own null versus omission |
| DT-111.c | Two assertions would catch particular flips: `null_pid` for the `pid` flip, and live digest comparisons for the base64 change. | Registered assertions. | Partly. `null_pid` holds (PRP:292-294; [F]). The `source_sha256` hex→base64 change is also rejected by the registered `require_subset` at PRP:291, because `normal_reply.json` authors that digest as hex ([F]: "authored value differs"). The fixture pins the spelling of six byte fields (lines 10, 20-24, 351) and the substituted `abi_identity`. | [F]. | AO; narrower than stated |
| DT-111.d | The general readers accept missing and null alike; a wrong omit/null rule on most other fields would pass every registered check. | Registered checks. | Yes for omit/null. | [F] (shape golden and subset both pass for `CompiledProfileCapture.reason`, `ValidatorVerdict.error`, `ValidatorVerdict.step_id`, `PWRunnerSubprocess.term_signal` flips). | AO |
| DT-111.e | `require_subset` treats an authored `null` as satisfied by an absent key and ignores extra keys; `normal_reply.json:387` authors `error: null` where the projection omits the key, and the projection carries `request_failure.expected_contract`, which the fixture lacks. | Authored fixture versus `normal.pwp`. | Yes. PRP:24-37; `docs/contract/31-steps.surface.md:153` ("omitted when absent"); PJ `ValidatorVerdict.error` has `json_null: false`. | [F]: exactly those two differences. | OCC (the comparison is credited as an expected-observation check while hiding a disagreement with the statement) |
| DT-111.f | DT-47's two `CWorkerTests` assertions read the pre-encoding object; `run_flow.rs` has 15 `serde_json::from_value` sites; the test derive maps null and absence to one `None`; the controller decodes binary frames only in the `run_flow.rs` replays and `runner_client.rs`. | Test paths around encoding. | Yes. `CWorkerTests.swift:417-424`; 15 sites counted; production decodes are `runner_client.rs:715, 752`. | [S]. | AO; dispositions belong to DT-47 and DT-104 |
| DT-111.g | Four incorrect implementations would pass all registered checks: a wrong `json_null` without a dedicated assertion; a guard/dependent pair that hides a value; a hex/base64 swap on a digest no live comparison reads; a schema combining path forms with conditional rules. Uppercase hex would fail. | Registered checks. | Partly. The third holds only for byte fields absent from `normal_reply.json` (see DT-111.c). The others hold. RS:764-776; PC:72-76. | [F], [M]. | AO; third bullet narrower |

### DT-112 (compound; one row per observation)

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| DT-112.a | Digest width is unchecked for most hex fields: a 0-, 1- or 32-byte root `policy_sha256` is projected and accepted by Rust admission and every Python reader; the inspected readers check widths only for the equipment-binding digests. | Constructed frame → readers. | Yes. Width checks exist for equipment inventory (`porcelain_actor.rs:629-631`), binding (717-719, 1860-1863), execution `cdhash` (1926) and the control hash (`runner_client.rs:169`). None exists for reply or actor `policy_sha256`, `policy_received_sha256`, the three compiled-profile digests (`porcelain_admission.rs:1312-1329`) or `abi_identity`. RESPONSE names a width only on fields whose definition says "Uses SHA-256 hexadecimal width"; `policy_sha256` (`docs/RESPONSE.md:387`) does not. | [S]; the runs are [X]. | AO; UI only if "SHA-256 … as lowercase hexadecimal" is read as a checked width |
| DT-112.b | Empty text and null, empty bytes and an absent key, `pid: 0` and `pid: null`, `false` and an absent key stay distinct in both readers; base64 for 0–4 bytes and hex agree between the Rust encoders and Python. | Constructed frames → both readers. | Consistent with source (RS:366-402; PY:76-91). Registered partial support: PC:76, 82-84; RS:764-776. | [X]; [S]. | AO |
| DT-112.c | The validator's native `"error": null` and absence merge before encoding; only `raw_line` keeps the native spelling. | Validator line → host record → projection. | Yes, and stated: WS:201 ("Known optional strings and integer fields may be absent or null"); `31-steps.surface.md:153, 157`. | [S]. | AO |
| DT-112.d | The local-only field `PWRunnerAttemptResult.execObservationDecodeProblem` holds tag 9, which no frame carries; `validate()` requires local-only tags to keep ascending order. | Schema tag space. | Yes. GP:100-101. | [M]: moving it out of order or onto a used tag is refused. | AO |
| DT-112.e | A public-name rename changes the Swift writer's tag-constant names although the written bytes are identical. | Generated Swift text. | Yes. GP:163, 169. | [M]. | AO |

### Coverage and limits (`COV`)

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Class. |
| --- | --- | --- | --- | --- | --- |
| COV.a | Answers 1–3: the fingerprint boundary is wider than what a receiver needs and is subsumed in the controller by the exact-contract check; the listed distinctions survive or merge; all layers can agree on an undesirable rule and do for conditional-null suppression and compaction. | Summary of DT-105–111. | Yes, with the qualifications at CONV.d, DT-106.f, DT-109.b and DT-111.c. | As for the entries. | AO |
| COV.b | Six affirmative results. | As stated there. | Fingerprint equality and the nine path states reproduced ([M], [F]); independent re-encoding of 261 frames and the 40 probe frames are [X]; "Rust and Python JSON were equal" is supported now by [L] (608 of 608 live envelopes) and by the passing retained corpus replay; the live-envelope equality is reproduced on another envelope ([L]). | Mixed. | AO |
| COV.c | Not exercised: a compiled Rust or Swift build from a mutated schema; the live `run` path with edited frames; a foreign-schema or foreign-contract frame through the live controller; client-capture-root projections; actor-form records beyond the equipment probes. | Limits of the review. | Still unexercised here. | — | AO |
| COV.d | Unresolved: the `team_id` reader difference; whether an identity over binary structure alone would serve the test readers; whether any external consumer relies on `same_as_input`. | Open questions. | First: resolved by reading (DT-108.g). Second: not needed under retention. Third: cannot be established from the repository. | [S]. | AO |

58 claims: CONV 4, DT-105 8, DT-106 6, DT-107 6, DT-108 8, DT-109 6, DT-110 4,
DT-111 7, DT-112 5, COV 4.

---

## 2. Comparison

### 2.1 Fingerprint (DT-105, DT-106, DT-107.a–d)

**Obligation as stated.**

- Owner `docs/contract/21-wire.surface.md:102` (rendered at
  `docs/ARCHITECTURE.md:745`): "The fingerprint is SHA-256 of the compact,
  object-key-sorted JSON wire identity emitted by `wire_identity`: schema
  version; records in schema order with ID, name and fields; each field’s tag,
  public name, type descriptor, null rule and any byte projection; path-form and
  conditional-null rules; root names mapped to record IDs; and declared variant
  cases. Local-only fields are omitted. Source paths, mutable/default
  annotations and descriptive text remain source provenance. Changes to a
  field’s name, tag, type, optionality, null/projection rule or a newly added
  optional field change the fingerprint and require exact receiver agreement."
- Owner `docs/contract/00-identity.surface.md:240-247` (rendered at
  `docs/CONTRACT.md:192-198`): "A matching fingerprint establishes the selected
  wire-schema match; the public producer identity is then checked separately."
- Owner WS:86: "A complete header naming another fingerprint yields
  unsupported schema before payload interpretation."
- Owner WS:60: "The declared PWDispositionValue variant has case tag 1
  carrying a signed integer and case tag 2 carrying PWRunnerTerminationRequest."
- Owner WS:19 (support `pins`): "Swift writes declared values; Rust and Python
  independently read their structure."

**Producer.** The generator stamps one fingerprint into the Swift constant,
the Rust constant and the Python table (GP:303-304). Swift record writers are
generated and consume IDs, tags and stored types (GP:154-171). The variant
writer and all primitive writers are hand-written (SW:57-126).

**Readers.** Both readers compare the 32 header bytes first (RS:159-161,
182-184; PY:149-150, 162-163), then, in the bound form, the producer contract
(RS:218-220; PY:184-185). Structural admission then checks each frame against
the receiver's own tables, including unknown variant cases and payload kinds
(RR:17-27; PY:128-137).

**Tests.** PC:470-489 asserts a comment leaves the fingerprint and outputs
unchanged. PC:491-539 asserts five structural mutations change every output
and that the Python reader refuses the old fingerprint. RS:752-757 asserts a
flipped fingerprint byte yields `UnsupportedSchema` ahead of a corrupt length.
`generate_contract_stamps.py --check` compares the retained identity JSON in
`tests/fixtures/contract/surfaces/wire.json` with `wire_identity(PJ)`.

**Observation.** A mismatch occurs for properties no producer writes (public
names, null flags including ineffective ones, record order, variant case names
and type spellings, root keys). A match occurs between any two builds stamped
from the same declarations, whatever their hand-written writers do.

**Inference kept apart.** What a *mismatch* establishes: the two builds'
schema declarations differ in at least one fingerprinted property. It does not
establish that the producer's bytes would be misread; no statement says it
does. WS:86 and the controller message ("names an unsupported porcelain
schema; this controller reads only the schema it was built with") claim only
the difference. What a *match* establishes: equal declarations. It does not by
itself establish that producer bytes conform; per-frame structural admission
does that. "Establishes the selected wire-schema match" is true when "selected
wire-schema" is read as the selected schema representation of the preceding
sentence, and could be read as conformance. No statement overclaims a mismatch;
one statement is open to an over-reading of a match.

For the hand-written variant writer: with the current two cases (wire kinds 2
and 6) a mis-tagged value fails the receiver's kind check and the frame is
refused as malformed; it cannot be decoded as the other case. That protection
is a property of the current case types, not of the generator.

Reading the producer contract before refusing a foreign fingerprint
(DT-105.h's second alternative) would interpret payload bytes under a schema
the header has just declared not shared; WS:82 orders "exact fingerprint, then
the expected root and producer identity", and WS:86 says "before payload
interpretation". The current order is the stated one.

### 2.2 Conditional-null projection (DT-108)

**Obligation as stated.**

- Owner WS:110: "Conditional-null fields are carried only when their guard has
  a value."
- Owner WS:52: "Optional record fields are omitted from the binary record when
  the producer has no value. A reader requires each nonoptional field and
  constructs optional absence from missing tags. JSON omission and null are
  projection choices owned by the field definition."
- Owner WS:10: "The controller projects admitted typed records into public
  JSON."
- Owner `docs/contract/31-steps.surface.md:59` (rendered at
  `docs/RESPONSE.md:962` with the derived phrase "present when result_source
  has a value; may be null"): "Native return carried by an associated allow,
  deny or error record. Synthetic results carry explicit null when
  result_source is present."
- Derived phrase for `team_id` at `docs/RESPONSE.md:2236, 2325`: "present when
  identifier has a value; may be null".

**Producer.** One function builds every query result and always sets
`result_source`; it sets `native_rc` only from an associated verdict
(`CWorkerStepResults.swift:44-49`). Both equipment producers assign
`identifier` and `team_id` together from one signed-code observation
(`ActorEquipment.swift:410, 452`). No shipped producer can emit a dependent
without its guard, or a synthetic result with a native return. The Swift
record type permits both states and the writer would encode them (generated
`writer.field` calls are independent).

**Readers.** Structural admission: no relation (GP:205-222; PY:64-91).
Projection: Rust emits the dependent only when the guard is present (RR:3523,
2133); Python removes it when the projected guard is `None` (PY:102-104).
Rust semantic admission: the pair is read only inside the `query_first`
eligibility rule (`porcelain_admission.rs:1204-1208`); a bound binding needs
an identifier (`porcelain_actor.rs:1869-1876`); nothing compares dependent with
guard. Python readers read the projection.

**Tests.** PC:166-173 asserts the three conditional states on a constructed
table, and at line 171 asserts that a dependent carried without its guard
projects to `{}`. That line pins the discarding behavior. No test constructs a
synthetic result with a native return.

**Observation.** For a frame that asserts this build's contract and carries
`native_rc` without `result_source`, the envelope's `data.runner_result` shows
neither key, the reply is admitted, and the value is visible only in
`runner_client.transport.runner_reply.data_base64`.

**Inference kept apart.** That any user has received such an envelope is not
supported: 261 unit frames and 608 live envelopes contain no instance, and the
producer source excludes it. The exposure is a producer other than the shipped
host (an external runner built from other source that asserts this contract, or
a constructed frame).

### 2.3 Path-form compaction (DT-109)

**Obligation as stated.** Owner WS:110: "Path-form fields equal to their input
bytes are omitted and listed in `same_as_input`; unavailable forms remain
null." Owner `docs/contract/31-steps.surface.md:355-357, 386-388`: "Names of
available resolved fields whose UTF-8 bytes equal input; those equal-valued
keys are omitted. A differing form is carried as a string; an unavailable form
is explicit null."

**Producer.** The host writes each derived form to the wire
(`PWRunnerService.swift:431-453`). Both projections compact (GP:235-250;
PY:93-101).

**Readers and tests.** `tests/lib/consumer.py:117-136` enforces the three-state
exclusivity; PRP:65-83 replays nine Swift frames; `blackbox_e2e/checker_controls`
runs the authored `path_diagnostics.json` rows.

**Rationale.** No non-frozen document states a size rationale. It appears in
the message of `085bffc7` and, as "so the path is carried once", in the frozen
guide (true of the JSON object it describes). One source comment labels the
compacted form the "Wire form" (`PWRunnerPathEvidence.swift:17-20`); the wire
carries every form, so that label is inaccurate. There is no stale rationale
in an owner to remove.

### 2.4 Rule order (DT-110)

**Obligation as stated.** Owner WS:110: "The generated Rust serializers and
independent Python projection apply these rules after typed byte admission."
No statement gives an order or a precedence among the rules.

**Producer of the difference.** GP:227-247 versus PY:86-106, as in the claims
table. `validate()` (GP:105-111) admits schemas on which the two orders give
different JSON. PJ at HEAD has none.

**Tests.** PC:157-181 exercises each rule on its own table.

### 2.5 Projection checks (DT-111) and smaller observations (DT-112)

**Credits as stated.**

- `tests/fixtures/README.md:23-24`: "`normal_reply.json` is the authored
  expected observation subset for the independent binary reply projection
  control … Shape checks separately own explicit null versus omitted fields."
- PRP:29 (comment): "Authored absent observation; shape checks own
  null-versus-omission."
- WS:6 lists `response_shape.json` as a golden of the wire surface;
  `docs/contract/AGENTS.md` says "A shape agreement supplies no behavioral
  evidence."

**What the checks assert.** `collect_shape` records, per path, each key's JSON
type, with `null` replaced by any typed occurrence (PRP:53-58). It records
neither absence nor spelling. `require_subset` compares authored non-null
scalars exactly, accepts an absent key for an authored `null`, and ignores
projected keys the fixture lacks (PRP:24-37). `null_pid` asserts one explicit
null (PRP:292-294). The corpus and `validate_client` compare the two readers'
complete JSON, both of which take every rule from PJ.

**Observation.** The fixture and the authored statement disagree on one key
(`ValidatorVerdict.error`), and the comparison passes. An exact comparison
against the fixture, once corrected, would reject an omit-to-null flip on the
fields `normal.pwp` leaves absent ([F]: `ValidatorVerdict.error` and
`PWRunnerSubprocess.term_signal` flips rejected; 37 optional fields are absent
in that frame) and would not reject a flip on a field that is present there.

**Digest width (DT-112.a).** The definitions that name a width are the ones
whose readers check it. The statement for `policy_sha256` describes what the
producer computes.

---

## 3. Plausible treatments

Build-contract inputs are the files matched by `docs/build_contract.py:15-25`.
Of the files named below, RR, RS, SW, `PWPorcelainRecords.swift` and
`PWRunnerPathEvidence.swift` are inputs. GP, PJ, PY, the surface files,
`docs/architecture.json`, the test suites and the fixtures are not.

### T-A. Schema validation rules (DT-110, DT-107.e, DT-106.d) — arrangement change

- **Edit:** GP `validate()` (after line 111 and inside the variant loop at
  128-136). Refuse a record whose `conditional_null` names, as dependent or
  guard, a field listed in `path_forms`; refuse a guard that is also a
  dependent; refuse a variant whose cases do not have pairwise different JSON
  types; refuse a variant case with a key other than `name` and `type`.
  `probe_rules.py` holds a working sketch: the current schema is accepted and
  each constructed combination is refused.
- **Controls:** add rows to the mutation list at PC:361-393
  (`test_literal_invalid_ids_variants_and_cycles_do_not_write`), each requiring
  refusal with its diagnostic and unchanged fixture bytes.
- **Build-contract input:** none. No generated output changes; the fingerprint
  is unchanged. `build.sh:230` already runs `generate_porcelain.py --check`,
  which calls `validate()`, so the rules bind every build.
- **Consequence:** none for users. A developer who later authors one of these
  combinations gets "invalid porcelain schema: …" from the generator and the
  build.
- **Incorrect behavior the check rejects:** a schema on which the two readers'
  rule orders give different JSON; a variant whose JSON does not identify its
  case; a variant-case key that silently enters the fingerprint.
- **Alternative for DT-110:** align the Python order with the generated Rust.
  It removes the disagreement but leaves both readers silently ignoring one
  declared rule on such a schema, and RESPONSE's derived phrase would describe
  the ignored rule. Not preferred.

### T-B. Presentation mutations in the fingerprint test (DT-106.f) — assertion repair

- **Edit:** PC:491-539, add mutations to the loop: a public-name rename, a
  null-rule flip on an optional field, a projection change, a reversed
  `path_forms` list, a removed `conditional_null`, a variant case rename and a
  root-key rename. The existing assertions (every output changes; the old
  fingerprint is refused; a one-sided restore is stale) apply unchanged.
  Extend the sentences at `tests/suites/source_drift/README.md:801-803`.
- **Build-contract input:** none.
- **Incorrect behavior rejected:** a `wire_identity` that stops covering a
  presentation rule the statement lists.
- **Alternative:** narrow the two architecture citations
  (`docs/architecture.json:3836-3842, 5630-5636`). The labels are true of the
  schema and the edge; only the cited checks fall short, so adding the
  assertions is the smaller truthful repair.

### T-C. Refuse a conditional-null field carried without its guard (DT-108.a–e, h) — product behavior change

- **Edits:**
  1. GP `rust()`: before `Ok(Self {` (line 215), for each
     `conditional_null` pair emit a check that returns
     `Err("<Record>.<dependent> carried without <guard>")` when the dependent
     local is `Some` and the guard local is `None`.
  2. PY:102-106: decide from the tags actually read (`seen`), and raise
     `ValueError('conditional field carried without its guard: …')` for a
     carried dependent whose guard was not carried. `probe_refusal_sketch.py`
     holds a working sketch: 261 of 261 retained Swift frames and 608 of 608
     retained live host frames project identically; the constructed state is
     refused.
  3. PC:171: the assertion that the state projects to `{}` becomes an
     expected refusal.
  4. RS tests: a literal record-56 frame with tags 2, 4, 5, 7, 8 must return
     `FrameError::Malformed`; tags 1 and 2 decode; tags 4, 5, 7, 8 decode and
     serialize with neither key; tag 1 alone serializes `native_rc: null`.
  5. WS:82 `free.effect`: add "a conditional-null field carried without its
     guard" to the refusal list. Extend
     `tests/suites/source_drift/README.md:786-790`.
- **Regeneration:** `tests/lib/python.sh docs/generate_porcelain.py`, then
  `tests/lib/python.sh docs/generate_contract_stamps.py`.
- **Build-contract input:** yes (RR is regenerated; RS gains a test). The
  fingerprint and `surfaces/wire.json` do not change, because
  `wire_identity` is unchanged; the public contract does.
- **Consequence:** no shipped output changes. A reply carrying the state is
  refused as `malformed_runner_response` with `data.runner_result` null and
  its bytes retained, where today it is admitted with the value missing. A
  developer of an external runner sees the refusal instead of a reduced record.
- **Incorrect behavior rejected:** a reader that admits a dependent without
  its guard; a projection that drops a received value.
- **Not included:** a check in the generated Swift writer. The producer cannot
  build the state, and a writer refusal would add a reporting-failure path.

### T-D. State that the projection discards (DT-108.a–e, h) — reasoned retention

- **Edit:** WS:110, after the conditional-null sentence: "A conditional-null
  field received without its guard is omitted from public JSON. The retained
  host frame still carries it, and no reader refuses that frame."
- **Regeneration:** `generate_contract_stamps.py`. No build-contract input.
- **Consequence:** behavior unchanged; the loss becomes a stated limit.
- **Check:** none needed beyond PC:171, which already pins the behavior.

### T-E. Carry the dependent whenever it has a value (DT-108) — product behavior change

- GP:241-243, PY:102-106 and `record_definitions.py:499-500` change so a
  dependent with a value is always projected. The presence phrase for three
  fields changes, RESPONSE and two surface goldens regenerate, RR changes.
  The inconsistent record becomes visible and is still admitted with no
  finding. More documentation change than T-C for a weaker result. Not
  preferred.

### T-F. Synthetic result with a native return (DT-108.f)

- **Retention (preferred):** `docs/contract/31-steps.surface.md:59`, append:
  "No reader checks this relation: a result marked `synthetic` that carries a
  native return is admitted and projected as received."
- **Product change (alternative):** a semantic rule in
  `porcelain_admission.rs`, the Swift reporting validation and
  `tests/lib/consumer.py`, with a `checks` node in the steps surface and
  corpus rows. Three readers and a signed rebuild for a state the shipped
  producer cannot build and on which no `query_first` claim can rest
  (`porcelain_admission.rs:1204`).

### T-G. Python actor reader identifier requirement (DT-108.g) — assertion repair

- **Edit:** `tests/lib/actor_evidence.py:302-309`, require a nonempty bounded
  `identifier` on a bound row, as Rust and Swift do. Add one shared row (bound
  binding without identifier, expected invalid) to
  `tests/fixtures/contract/actor_evidence.json`, which the Rust test at
  `porcelain_actor.rs:2188` and `tests/suites/blackbox_e2e/extension_controls.py:184`
  both read.
- **Build-contract input:** none.
- **Incorrect behavior rejected:** a Python reader that accepts a bound
  binding with no signing identifier.

### T-H. Path compaction (DT-109)

- **Retention (preferred):** no behavior change. Add to WS:110, after the
  path-form sentence: "The compaction applies to public JSON only; the frame,
  and the envelope's retained copy of it, carry each derived form."
- **Rider:** `PWRunnerPathEvidence.swift:17` "Wire form" → "Public JSON form".
  This file is a build-contract and worker-identity input; make the edit only
  together with another `runner/Sources` change.
- **Removal (alternative):** drop `path_forms` from PJ records 26 and 48 and
  set the forms to `json_null: true`. Consequences: new fingerprint and public
  contract; worker-identity regeneration; GP, PY and
  `record_definitions.py` branches removed; two surface subjects and WS:102,
  110 reworded; `surfaces/steps.json`, `surfaces/wire.json` and
  `response_shape.json` refreshed; `consumer.py:105-142`,
  `path_diagnostics_contract.py`, `path_diagnostics.json`, `reply_fixtures.rs`,
  PC:157-181, PRP:65-83, `build_contracts.py:629-631`,
  `contract_tree_controls.py:246`, three checker-control files and
  `runner_use_c_worker/run.sh:1125` changed; the shared reading rule at
  `tests/FAILURE-PROPAGATION-CONTRACT.md:1421` corrected in its owner. The
  frozen guide would keep about 40 lines describing a field that no longer
  exists, with no errata permitted. External reliance on `same_as_input`
  cannot be assessed from the repository.

### T-I. Exact normal-fixture comparison and narrowed credit (DT-111.b, e) — assertion repair

- **Edits:**
  1. `tests/fixtures/contract/normal_reply.json`: remove `"error": null` at
     line 387 (the statement and the projection omit it); add
     `"expected_contract": "test:request"` to `request_failure` (lines 276-282).
  2. PRP:24-37 and 291: compare exactly. An authored `null` requires a present
     `null`; a projected key the fixture lacks is a failure.
  3. `tests/fixtures/README.md:23-24` and the comment at PRP:29: say that
     shape checks record key names and JSON types and do not distinguish an
     omitted key from an explicit null or one byte spelling from another, and
     that the normal fixture is the authored exact projection of `normal.pwp`.
- **Build-contract input:** none.
- **Incorrect behavior rejected:** an omit/null flip on any optional field
  that `normal.pwp` leaves absent; an extra or missing projected key; a
  changed byte spelling on a field the fixture carries.
- **Alternative:** a presence golden over the 64 shape frames. It would cover
  219 fields but would be regenerated from the same flags it checks, so it
  detects drift, not a mistaken rule. Not preferred as the first repair.

### T-J. Accounts for the hand-written variant writer (DT-107.a–c)

- **Retention with account correction (preferred):**
  `docs/architecture.json:3849` "Swift writers" → "Swift record writers";
  `tests/suites/source_drift/README.md:321`, same word, and add: "The variant
  writer in `PWPorcelain.swift` is hand-written. Check mode does not compare
  its case tags or payload types with the schema; `runner_unit` replays
  Swift-written frames through the generated readers, and that replay is the
  first check to read a Swift-written variant value." Regenerate with
  `tests/lib/python.sh docs/generate_architecture.py`. No build-contract input.
- **Arrangement change (alternative):** generate the variant writer in
  `swift()` and delete SW:115-126. Bytes unchanged, but SW and
  `PWPorcelainRecords.swift` are build-contract and worker-identity inputs:
  worker-identity regeneration and a signed rebuild for no behavior change.
  Then `--check` would refuse a stale writer at build time. Worth taking only
  with another `runner/Sources` change.

### T-K. Fingerprint breadth (DT-105, DT-106.a–c, e)

- **Retention (preferred):** append to WS:102: "The fingerprint identifies the
  schema declarations and is not a compatibility test. It also changes for a
  declaration that no producer writes: a public name, a null rule that a
  path-form or conditional-null rule or a required field makes ineffective,
  record order, a variant case name or declared type spelling, and a root key.
  A match shows that both builds carry the same declarations; structural
  admission, applied to each frame, checks the bytes."
- **Identity over binary structure (alternative):** change `wire_identity`.
  The fingerprint and public contract change, `surfaces/wire.json` is
  refreshed, WS:102 and `00-identity.surface.md:240-247` are rewritten, and
  presentation rules need their own versioning for the unbound test readers.
  Operational gain is nil while the exact-contract rule holds.

### T-L. Digest width (DT-112.a)

- **Retention (preferred):** append to WS:110 after the hexadecimal sentence:
  "The projection spells the bytes received; digest length is checked only by
  the equipment and control-observation readers."
- **Product change (alternative):** a declared byte width per field, enforced
  structurally. It adds a descriptor to the identity (new fingerprint) for
  values every shipped producer computes at fixed width.

---

## 4. Recommended disposition per claim

| Id | Disposition | Reason | Discriminating check, or why more evidence would not change the decision |
| --- | --- | --- | --- |
| CONV.a | No change. | Files unchanged. | Hashes recomputed. |
| CONV.b | No change; cite the current app identity when crediting anything. | Historical. | `--version` and `docs/build_contract.py` agree at HEAD. |
| CONV.c | No change; treat the review's executed values as unavailable and use the retained later run with its availability limit. | Evidence gone. | — |
| CONV.d | Record the correction: the identity JSON, with every descriptor, is retained in `surfaces/wire.json` and checked by the contract generator. | The review's note understated a registered support. | Golden equals `wire_identity(PJ)` and hashes to the fingerprint (checked now). |
| DT-105.a–c | Reasoned retention (T-K). | Over-sensitivity causes only refusals, each of which coincides with an exact-contract refusal for pipeline-built producers. | T-B makes the presentation half executed. Further probes would repeat [M]. |
| DT-105.d | Accurate; keep with its boundary (pipeline-derived contract strings). | — | Source reading is decisive: both constants are hashed inputs. |
| DT-105.e–f | No change. | The refusal order is the stated one; reading a producer string from a frame whose schema is declared foreign would be interpretation without a shared grammar. | Further evidence would not change it. |
| DT-105.g–h | Reasoned retention with the T-K sentence beside WS:102. | The sentence under review is literally true; the limit removes the over-reading. | — |
| DT-106.a–c | Reasoned retention; the T-K sentence names ineffective null rules and variant type spellings. | Normalizing them changes the fingerprint and forces a rebuild for no behavioral gain. | [M] is complete for the three flips and the variant spelling. |
| DT-106.d | T-A (closed key set for variant cases), which makes WS:102's provenance sentence true without editing it. | Smallest change; no output or fingerprint change. | New refusal control in PC; `source_drift/porcelain_codec`. |
| DT-106.e | No change. | Case names have a documentation role, like public field names. | — |
| DT-106.f | T-B. | The cited checks do not exercise presentation rules. | `source_drift/porcelain_codec` with the added mutations. |
| DT-107.a | Reasoned retention with the T-J account correction. | The gap is stated nowhere; one word and one sentence make the accounts exact. | `source_drift/architecture_documentation`. |
| DT-107.b–c | Reasoned retention. Accepted limit: the T-J sentence. | A drifted writer cannot pass `runner_unit/pwrunner_core_unit_executable` or any live case that returns a claim value, so it cannot pass a default battery or release acceptance. | That case, default membership. |
| DT-107.d | No change; covered by the T-J sentence. | — | — |
| DT-107.e | T-A (distinct JSON types per variant). | Keeps "serializes the selected value directly" safe by construction. | New refusal control in PC. |
| DT-107.f | No disposition here; it is DT-53's observation on binary frames. | Belongs to the DT-53/132 reader row. | Needs the Rust test binary; not run in this pass. |
| DT-108.a, b, d, e, h | T-C. If the maintainer declines the added refusal, T-D with its sentence. | The public record should not omit a received value silently; a refusal costs shipped producers nothing and keeps the bytes. Root guidance: witness over interpretation. | Revised PC:171 control and the RS literal-frame test, run first against the current readers (expected to fail), then against the change. Cases `source_drift/porcelain_codec`, `unit/rust.unit`, `runner_unit/pwrunner_core_unit_executable`. |
| DT-108.c | No change. | Accurate; it bounds the exposure to non-shipped producers. | [S], [F], [L] agree. |
| DT-108.f | Reasoned retention with the T-F sentence. | The definition is a producer statement the producer satisfies; the value is visible, and `result_source` qualifies it. | Further evidence would not change it: the producer has one assignment site. |
| DT-108.g | T-G. | Two readers enforce the requirement and the third omits it. | New shared fixture row; `blackbox_e2e/checker_controls` and `unit/rust.unit`. |
| DT-109.a | No change. | Affirmative. | — |
| DT-109.b | No change; record that the null state is cross-compared in live envelopes by `validate_client`. | The corpus gap is covered by a registered live comparison. | [L]: 37 retained envelopes with a null form, all equal. |
| DT-109.c, f | Reasoned retention (T-H). No owner states the rationale, so there is nothing stale to remove outside the frozen guide. | Removal changes the wire identity, the public shape and a dozen readers, and leaves the frozen guide describing a removed field; reliance by external consumers is unknown. | Further evidence would not change it short of knowing external reliance. |
| DT-109.d–e | No change. | Accurate costs of the retained form. | — |
| DT-110.a–d | T-A. | The shipped schema cannot express the case; a validation rule keeps it so and keeps the two independent orders as a real cross-check. | Three new refusal controls in PC. |
| DT-111.a | No change; state the limit (below). | Single-source rules are the design. | — |
| DT-111.b, e | T-I. | Removes the hidden disagreement and corrects two credits. | `runner_unit/pwrunner_core_unit_executable`; [F] shows which flips the exact comparison rejects. |
| DT-111.c, g | No change; record that the normal fixture already pins byte spelling for the fields it carries. | The review's third bullet is narrower than stated. | [F]. |
| DT-111.d | Reasoned retention after T-I. | An independent expectation for every field would be a second hand-kept copy of 329 flags. | — |
| DT-111.f | No disposition here. | Owned by DT-47 and DT-104. | — |
| DT-112.a | Reasoned retention with the T-L sentence. | Statements that name a width are the ones readers check. | Further evidence would not change it. |
| DT-112.b–e | No change. | Accurate observations. | — |
| COV.a–d | No change beyond the entries above. | — | — |

**Accepted-limit sentences and where they belong.**

- WS:102 (identity definition): the T-K sentence.
- WS:110 (projection definition): the T-H sentence, the T-L sentence, and the
  T-D sentence only if T-C is declined.
- `docs/contract/31-steps.surface.md:59`: the T-F sentence.
- `tests/suites/source_drift/README.md` (generator contracts, porcelain
  paragraph): the T-J sentence.
- `tests/fixtures/README.md` (contract fixtures): "The omit or null rule of an
  optional field is compared with an authored expectation only where
  `normal_reply.json` leaves that field absent or a dedicated assertion names
  it. Elsewhere both readers and RESPONSE's presence phrase take the rule from
  `docs/porcelain.json`."

**Missing authority or information.** None blocks these dispositions. T-C adds
a refusal to a public reader; the management plan gives the implementer that
authority, and the choice between T-C and T-D is the one place where the
maintainer's preference decides. Whether an external consumer reads
`same_as_input` is unknown and cannot be learned from the repository.

---

## 5. Resulting user duties

- On "runner reply frame names an unsupported porcelain schema", conclude only
  that the runner and controller were built from different schema
  declarations. Do not conclude that the runner's records would be misread, or
  which build produced them; compare the two builds' contracts.
- Read `sandbox_check.native_rc` together with `result_source`. A non-null
  `native_rc` on a `synthetic` result is not a native return.
- With T-C: a reply refused as malformed for a conditional field without its
  guard keeps its bytes in `runner_client.transport.runner_reply.data_base64`.
  With T-D instead: when `result_source` or `identifier` is absent, do not
  conclude from the missing `native_rc` or `team_id` key that the frame
  carried none; decode the retained frame.
- Do not treat the length of `policy_sha256`, an actor source digest or a
  compiled-profile digest as checked by a reader.
- Path forms: no new duty. A form named in `same_as_input` equals `input` byte
  for byte; the retained frame carries all forms.
- Developers: any edit to a fingerprinted declaration in PJ yields a new
  fingerprint and public contract and a refused `surfaces/wire.json` until
  shapes are refreshed. Edit the Swift variant writer together with the
  schema's variant, and run `runner_unit`.

---

## 6. Implementation worklist

Order follows the plan's rule to exercise a revised test against existing
behavior first, and groups the one signed rebuild.

**Stage 1 — no build-contract input.** Confirm before and after that
`tests/lib/python.sh docs/build_contract.py` prints the same identity.

1. GP `validate()`: the four T-A rules. PC:361-393: five refusal controls
   (guard is a path form; dependent is a path form; chained guard; variant
   with two integer cases; variant case with an extra key).
   `tests/suites/source_drift/README.md:799-801`: name the new refusals.
   Run `tests/lib/python.sh docs/generate_porcelain.py --check` (expect
   "checked 84 porcelain records").
2. PC:491-539: the T-B mutations.
3. `normal_reply.json`, PRP:24-37, 29, 291 and `tests/fixtures/README.md:23-24`:
   T-I.
4. `tests/lib/actor_evidence.py:302-309` and one row in
   `tests/fixtures/contract/actor_evidence.json`: T-G.
5. `docs/architecture.json:3849`, then
   `tests/lib/python.sh docs/generate_architecture.py`;
   `tests/suites/source_drift/README.md:321`: T-J.
6. Verification: `tests/run.sh --suite source_drift` (includes
   `porcelain_codec`, `generator_contract`, `build_contracts`,
   `architecture_documentation`), `--case preflight/build_entry_controls`,
   `--case runner_unit/pwrunner_core_unit_executable`,
   `--case blackbox_e2e/checker_controls`, `--case unit/rust.unit`. Route:
   `tests/CHANGE-VERIFICATION.md`, "Porcelain schema or binary
   representation". The plan's wire/layout/schema/identity row is not
   triggered: no wire byte, layout, schema or identity derivation changes, and
   no rebuild is forced.

**Stage 2 — T-C, one signed rebuild.**

7. Change PC:171 and add the RS literal-frame test. Run
   `source_drift/porcelain_codec` against the current reader and keep the
   failing result as the pre-change observation.
8. GP `rust()` and PY:102-106 as in T-C. Run
   `tests/lib/python.sh docs/generate_porcelain.py`; review the RR diff (three
   added checks, in records 36, 39 and 56).
9. Surface text in one pass: WS:82 (T-C), WS:102 (T-K), WS:110 (T-H, T-L),
   `31-steps.surface.md:59` (T-F). Run
   `tests/lib/python.sh docs/generate_contract_stamps.py` in development mode
   and then `--check`. ARCHITECTURE, RESPONSE, CONTRACT and
   `docs/contract/public.json` regenerate; the frozen guide and its stamp
   table stay byte-unchanged. No shape golden changes.
   `tests/suites/source_drift/README.md:786-790`: add the refusal.
10. This stage triggers the plan's row in full: owning regeneration (step 8),
    `source_drift`, `runner_abi_layout/c_swift_layout_agreement`, the default
    build controls (`preflight/build_entry_controls`), and a signed rebuild
    before the next change. Also `unit/rust.unit` and
    `runner_unit/pwrunner_core_unit_executable`; retain the ordinary, ordering,
    actor and ending semantic controls of the default battery for the rebuilt
    app. Worker identity is not regenerated: no `runner/Sources` file changes.
11. If T-C is declined: skip steps 7, 8 and 10, put the T-D sentence in WS:110
    in step 9, and the stage needs only `generate_contract_stamps.py` and
    `source_drift` (documentation row; no build-contract input).

**Rider — only with another `runner/Sources` change.**

12. `PWRunnerPathEvidence.swift:17`: "Wire form" → "Public JSON form". Needs
    `tests/lib/python.sh docs/generate_worker_identity.py` and a signed
    rebuild, with `runner_abi_layout`.

Nothing here edits `docs/PolicyWitness.md`, its copies or its stamp table, and
no proposed text links to `records/`.

---

## Outside the review

- **Chained guards.** `validate()` also accepts a guard that is itself a
  dependent. On `{native_rc: result_source, result_source: missing_reason}`
  the Python result depends on the order of the rule dictionary, and the
  generated Rust keeps `native_rc` where Python may drop it ([M]+[C]). Only a
  hypothetical schema; the second T-A rule refuses it.
- **Path-diagnostics test credit.** `tests/suites/runner_unit/README.md:95-98`
  says `PathDiagnosticsTests` pins "rejection of conflicting/missing
  representations" and that `path_diagnostics.json` supplies cases "to Rust
  and Python reader checks". At HEAD the Swift group has three cases, none a
  rejection, and the fixture is read only by
  `tests/suites/blackbox_e2e/checker_controls.py:978`.
- **Unused statics.** `formNames` at `PWRunnerPathEvidence.swift:22, 56` has
  no reader in `runner/Sources` or `runner/Tests`.
