### What acceptance, validity and successful completion establish

This pass follows DT-48, DT-50, DT-53, DT-61 and DT-95 from their raw or
constructed input to the outer `run` result. For each accepting boundary it
records the proposition checked, the representation of the evidence it reads,
and the consequence of a failure. The five findings concern different
boundaries. The entries below explain how they relate and add six findings
under provisional labels AC-1 to AC-6. Earlier findings keep their scope; where
this pass re-executes one, it says so. No implementation, test, contract or
document was changed, and nothing here proposes a repair, an authoritative
layer or a consolidation of findings.

#### Identity, evidence categories and reproduction

**Snapshot.** Source inspection used clean HEAD
`cc55288d033023ce2f18e8c02cd51a400ef2b530` on 2026-11-16. Line numbers below
refer to that snapshot. The machine reports macOS 26.7.1, build 25G241, arm64.
`dist/PolicyWitness.app` reports commit `8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`,
version 0.3.7, build 1482, contract
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
`git diff --stat 8b5de2b2 HEAD -- controller runner tests docs` shows only a
one-line change to `tests/suites/preflight/opt_in/build_refusals.py`. The five
app executables hashed identically before and after this pass's runs
(`policy-witness` `4bcd308b…8d28`, `PWRunner` `706d9a6c…8501`, `pw-probe-runner`
`d6d38f09…2116`, `pw-probe-runner-unentitled` `ee2a4248…312c`,
`sb_api_validator` `ccbf9803…0890`). Nothing was rebuilt or re-signed. Python ran
through `tests/lib/python.sh` (Python 3.14.9) with assertions enabled.

**Evidence categories.** Each result below names one of these:

- *Live*: `policy-witness run REQUEST` against the dist app, capturing stdout,
  stderr, exit status and the exact host reply bytes retained by the admitted
  client capture. Controlled-validator runs set
  `_test_overrides.validator_executable_path` to a copy of one Python script
  whose transcript mode is selected by file name. It reads each JSON query
  line and prints one verdict record (two in `dup` mode). It makes no
  `sandbox_check` call. These runs exercise the real host, worker, client and
  controller with a steered validator transcript; they are not native
  predictions.
- *Seam*: the existing ignored Rust test
  `run_flow::tests::reader_definition_corpus_cross_readers`
  ([run_flow.rs](../controller/src/run_flow.rs) lines 1250–1510) and the
  Python replay it launches
  ([reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py)), both
  unmodified. Details and limits are below.
- *Unit*: one existing Rust test run from the same binary (DT-95).
- *Source*: reading at the snapshot, with no execution.
- *Listing*: `tests/run.sh --all --list`, which listed 283 cases (232
  default) without a lock refusal. No registered case was executed, and no
  case pass is claimed.

**Environment.** The first live run (`base`) was made inside the automation
sandbox and returned `finished`, exit 0. Earlier passes saw lookup error 159
there; this run did not. All live runs and the seam execution therefore ran
inside the automation sandbox. No conclusion is drawn about the earlier
refusals.

**Live runs.** All used the request skeleton of the failure-contract
investigation: SBPL `(version 1)(allow default)`, one step per query, a
`file-read-data` path query, and a `file`/`open_read` attempt on the same path.
`é` below is U+00E9 (NFC). Its NFD form is `e` followed by U+0301.

| Run | Variation | Exit, outcome | Host frame SHA-256 (prefix), bytes |
| --- | --- | --- | --- |
| `base` | shipped validator, step `s`, `/etc/hosts` | 0, `finished` | `a5700b04ed25`, 3551 |
| `base_fixture` | controlled coherent record `allow`/0/0 | 0, `finished` | `ea1d250747d6`, 3636 |
| `incoherent` | controlled record `allow`, `rc` −1, `errno` 13 | 0, `finished` | `9001b5744b17`, 3642 |
| `nfc_id` | step `s-é`; record ID byte-identical | 0, `finished` | `2de88839aa36`, 3648 |
| `nfd_id` | step `s-é`; record ID in NFD | 0, `finished` | `3ca88d804093`, 3650 |
| `nfc_value` | path `…/files/café.txt`; record value byte-identical | 0, `finished` | `3cbb136d21b1`, 4484 |
| `nfd_value` | same path; record `filter_value` in NFD | 0, `finished` | `404e10fc643d`, 4489 |
| `dup_id` | step `s-é`; two records, NFC and NFD IDs | 1, `validator_unavailable` | `ba4277a91350`, 4174 |
| `both_ids` | two steps, `s-é` NFC and NFD | 1, `bad_request` | `551a7d270b9c`, 528 |
| `capture` | `capture_compiled_profile`, nonce `ad881d6a…9ae8` | 0, `finished` | `2b6efe373bbb`, 4340 |
| `actor` | issuer (unapplied, unentitled) issues and transfers a read extension; subject (applied) reads, consumes, reads | 0, `finished` | `7b729668604c`, 23352 |

**Seam method.** The Rust test reads `reader-corpus/swift.json` under
`$PW_POLICY_TRANSFER_REPLIES`. For each listed frame it:

- decodes the frame with `porcelain::decode`;
- runs `admit_reply`;
- assembles the run envelope with `complete_execution(driver_execution(typed, &raw))`;
- checks that the outer result follows the host label;
- writes `rust.json`;
- runs the Python replay. The replay records, per row:
  - independent `porcelain.decode_bound` equality;
  - `consumer.validate_fixture` on the bare reply and on the Rust-assembled envelope (binary bytes, so the JSON-fixture path is not taken);
  - `actor_evidence`, `extension_evidence` and `lifecycle_oracle.check_record`.

  It writes `python.json`.

The test binary was built from the unmodified crate:
`CARGO_TARGET_DIR=.tmp/contract-trio/acceptance/cargo-target cargo test
--manifest-path controller/Cargo.toml --locked --offline --no-run`, with cargo
and rustc 1.99.0. The resulting binary `policy_witness-bb8137965490ffba` has
SHA-256 `b64ac21a…7fe97`. `controller/build.rs` writes only under `OUT_DIR`,
and `git status` stayed clean.

Seam limits that apply to every seam result below:

- **Constructed contract binding.** Under `cfg(test)` the controller's
  `BUILD_CONTRACT` is the constant `test:policy-witness`
  ([json_contract.rs](../controller/src/json_contract.rs) lines 21–22). The
  Python replay admits frames only under that identity. Every seam row,
  including each baseline, is therefore a live frame with one constructed edit:
  `producer.contract` changed to `test:policy-witness`. The builder decoded each
  live frame and its rebound copy and required the difference to be exactly
  that field. Each further edit was likewise verified to differ from its
  rebound base only in the intended field (`corpus/edits.json`).
- **No `reply_contract`.** The seam calls `complete_execution` directly. A
  receipt-label failure therefore appears there as a `reply_admission`
  integrity finding, whereas the production run path refuses the reply first.
- **Placeholders.** The test panics unless rows named `ordinary`,
  `actor-complete` and `preparation-0` exist. It also unconditionally reads
  `../porcelain-replies/writer-cap-{minimal.pwp,receipt.json}`, and the replay
  reads `../porcelain-replies/normal.pwp`. `ordinary` and `actor-complete` are
  the rebound `base` and `actor` frames. `preparation-0` is a second copy of
  the rebound `actor` frame. The writer-cap pair and `normal.pwp` are
  constructed (`seam_placeholders.py`; `normal.pwp` copies `ordinary`). All of
  these exist only so the seam can run. Their rows, and the seam's JSON-only
  rows derived from them, are disregarded.
- **Fidelity control.** For every unedited rebound row with a live envelope
  (twelve rows: eleven distinct live frames, plus `preparation-0`), the
  seam's `runner_result` (with
  `producer.contract` normalized), `runner_sandbox_diagnostics`, and
  `result.normalized_outcome`, `ok`, `exit_code` and `error` were identical to
  the live CLI envelope's. No field disagreed. `porcelain.decode_bound` and the
  Rust JSON agreed on all 25 rows.
- **Expectation failures.** The test exited 101 by design, because I gave
  every row `expected_semantic: true`. Its own failure list names exactly the
  rows where Rust found issues (`f48-claimed-order`, `nfd-id`, `nfd-value`,
  `dup-id`, `f95-producer-host`), plus placeholder mismatches. The replay's list
  names the consumer findings tabulated below, plus placeholder and corpus
  inventory mismatches. The test's check that "semantic findings changed outer
  result/exit" (line 1352) raised nothing: for every row, result and exit
  followed the host label.

The Swift reporting validator and the Swift setup decoder were not run on any
edited frame. Every Swift judgment about an edited frame below is source
reading.

**Availability.** Scripts, requests, envelopes, frames, the corpus,
`rust.json`, `python.json`, `analysis.json`, the catalog listing and the reader
map are under `.tmp/contract-trio/acceptance/` in this checkout. That directory
is gitignored scratch with no retention guarantee. SHA-256 of the main
artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `scripts/live_probe.py` | `388bd987…89ee` |
| `scripts/validator_fixture.py` | `7e5b1a97…6489` |
| `scripts/frame_edit.py` | `6b2bba47…9f69` |
| `scripts/build_corpus.py` | `bb952dc2…6739` |
| `scripts/seam_placeholders.py` | `548e9afd…6f49` |
| `scripts/analyze_seam.py` | `c442d6d6…f916` |
| `scripts/reader_case_map.py` | `e8517f42…22fb` |
| `corpus/reader-corpus/rust.json` | `ed61060c…0226` |
| `corpus/reader-corpus/python.json` | `83557186…b57d` |
| `corpus/edits.json` | `2f0f2e3f…44eb` |
| `reader-case-map.jsonl` | `0da5ed35…acbb` |

The frame editor re-encoded three unrelated old frames byte-identically before
use; those frames were a tool check only. The decisive values are reproduced
here.

#### 1. What each accepting boundary checks, and over which representation

Rows are in pipeline order. "Result" means `result.normalized_outcome`,
`result.ok` and the exit status.

| Boundary | Representation read | Proposition checked | Failure consequence |
| --- | --- | --- | --- |
| Validator verdict production ([21-wire](../docs/contract/21-wire.surface.md) lines 172–185; `emit_verdict`, [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c) lines 365–410) | native `sandbox_check` return and errno | *Producer obligation*: rc 0 → `allow`; rc 1, errno 0 → `deny`; rc −1, EINVAL → `unsupported_operation`; otherwise `error` | none checked downstream (see DT-48) |
| Host line admission ([ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift) lines 461–548; 21-wire lines 187–201) | raw stdout bytes | LF framing, strict UTF-8, JSON object, kind/schema, field types, string bounds; allow/deny require IDs and integer rc/errno. Not label/return coherence. | stops at the first refused frame; `decode_fault`; host outcome `validator_decode_failure` |
| Host association (`validatorAssociationIssues`, [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift) lines 157–187) | accepted verdict structs and the probes actually sent | unique group per expected ID; supplied metadata equal to the sent tuple, under Swift `String` equality (canonical equivalence) | issues are retained; host outcome `validator_unavailable` via `classify` ([CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift) lines 432–455) |
| Host order eligibility (`eligibleOrderedStep`, [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift) lines 4–24) | typed step query plus records | chain, setup, PID, coherent native return, unique canonical-equal record and tuple | sets `order`; nothing else |
| Host shared-memory decoders | raw worker region bytes plus host arguments | setup: decision snapshot, raw actor/required association, cell validity, primary cell (`decodeAuthoritySetup`, [AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift) lines 55–111); receipt: nine ordered capture conditions (`decodeProfileCapture`, [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift) lines 679–714) | `integrity_errors`; receipt `unavailable` with a reason |
| Actor scheduler (`setupDisposition` and its caller, [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift) lines 257–288) | decoded setup scope plus the header words `actor_setup` and `authority_status` | no integrity errors; not terminal; applied/declared setup; for required authority `authority_status == MAPPED` | actor not activated (`setup_failed` and similar) |
| Host reporting validation (`validateForReporting`, [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift) lines 241–378, called by `pwRunnerReportData`, [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift) lines 122–155) | assembled typed reply | claims vs basis, phase partition, collection/validator consistency, validator ownership (shared join), `query_first ⇒` eligibility (shared predicate), exec/fresh observations, actor and authority shapes, receipt status/labels | rich fallback: `runner_reporting_failed`, `rc` 1, comparisons removed; then minimal reply; then empty bytes |
| Controller structural decode ([21-wire](../docs/contract/21-wire.surface.md) lines 72–86) | client and host frame bytes | grammar, fingerprint, required fields, kinds | client/host refusal; result exit 1 |
| Controller `reply_contract` / `admission_problem` ([run_flow.rs](../controller/src/run_flow.rs) lines 99–107, 330–355; [porcelain_admission.rs](../controller/src/porcelain_admission.rs) lines 1308–1330) | typed reply | producer contract; collection geometry; each receipt's status and `producer`/`capture_stage` labels | `unsupported_runner_response` or `malformed_runner_response`; result exit 1; diagnostics null |
| Controller semantic admission (`admit_reply` 1436–1505, `validate_lifecycle` 385ff, actor `setup` [porcelain_actor.rs](../controller/src/porcelain_actor.rs) 385–466) | typed reply (sees dependents the JSON projection can hide, DT-108) | phase partition; literal association recomputation; `query_first ⇒` eligible; lifecycle claims vs raw fields; actor/authority shapes; terminal setup ⇒ required ∧ primary | `process_disposition: withheld`, `disposition_integrity: invalid`, findings; **result unchanged** |
| Result selection ([result.rs](../controller/src/interface/result.rs) lines 142–237) | admitted host label | `Admitted { integrity_issues }` is carried, but no row reads it; only exact `finished` gives true/0 ([40-envelope](../docs/contract/40-envelope.surface.md) lines 185–194) | n/a |
| Python `porcelain.decode_bound` | frame bytes | same grammar, independently generated tables | decode error |
| Python `consumer.validate` ([consumer.py](../tests/lib/consumer.py) lines 1085–1104) | envelope JSON, plus captured bytes decoded and compared for equality ([runner_client_capture.py](../tests/lib/runner_client_capture.py) lines 366–450) | shape allowlists; client admission; result consistent with admitted label; phases and literal association ([phase_evidence.py](../tests/lib/phase_evidence.py) lines 38–107); comparisons; `order ⇔ eligible` (lines 555–558); extension and actor evidence; receipt status/labels. Not lifecycle claims; not the values of Rust diagnostics. | test verdict only |
| Lifecycle oracle ([lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) lines 531–700) | envelope JSON | every claim against the value it computes from its own raw field; projection form (an invalid record must be `withheld`); phase ownership via the consumer's own `ownership_problem`; extension evidence via the shared reader | test verdict only |
| `actor_evidence`, `extension_evidence` | reply body JSON | operation shapes; terminal setup ⇒ required ∧ primary; custody relationships | test verdict only |

Two features of this map matter for the anchors.

- **Which layers can change the result.** Host receiver, classification and
  reporting validation change the host label, and so the result. Controller
  capture, frame and `reply_contract` checks refuse the reply. Once a decoded
  reply passes the producer-contract gate, the receipt status/label check
  (with collection geometry) is the only semantic-record check that changes
  outcome and exit. Every other controller check only adds findings, by
  documented design (40-envelope lines 185–194; 41-diagnostics lines 657–666).
  A relationship that the host does not test, or tests under its own rule,
  reaches only the layer that cannot change the result. This is the common
  route for DT-48, DT-50, DT-53, DT-61 and DT-95.
- **Same predicate, different inputs.** Swift reporting validation re-checks
  association and order with the same functions the host used to produce them.
  It supplies different inputs: the reply's own step tuples instead of the
  sent probes (PWRunnerReply.swift lines 64–73), and the reply's projected
  setup and PID instead of the live ones (lines 357–368). The stated rationale
  is uniform phase ownership (PWRunnerReply.swift lines 51–57;
  [FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md)
  lines 605–622) and checking reported rather than live inputs
  ([31-steps](../docs/contract/31-steps.surface.md) "Order association
  source"). So the reporting check can detect a misattached or copied block,
  expected IDs that differ from the reply's plan, records altered after
  association, and an order claim whose reply-visible prerequisites fail. It
  cannot disagree with the production rule itself. This describes its scope;
  it is not a defect.

#### 2. The anchors

##### DT-48 — label/return coherence is an emitter obligation, checked only inside order eligibility

**Sequence.** The emitter rule (21-wire lines 172–185) assigns labels from the
native pair. Host line admission (lines 187–201) states a type-and-presence
check and does not test the pair. `classify` does not test it either.
`buildSandboxCheckResult` copies `outcome`, `rc` (default −1) and `errno`, and
sets `native_rc` from any allow/deny/error record (CWorkerStepResults.swift
lines 44–49, 128–139). The coherence test exists only inside the order rule's
"Native answer" condition (31-steps lines 613–617). Swift construction and
reporting (PWRunnerStepEvidence.swift lines 5–9), Rust (porcelain_admission.rs
lines 1204–1208) and Python (`eligible_order`, consumer.py lines 256–284)
implement it only there.

**Executed (live and seam).** The DT-48 result reproduces at this snapshot.
The four combinations of coherence and order claim behave as follows. The two
edited rows are seam frames with the constructed contract binding:

| Row | Record | `order` | Result | Rust | Python consumer | Oracle |
| --- | --- | --- | --- | --- | --- | --- |
| `base_fixture` (live) | allow/0/0 | `query_first` | `finished`, 0 | `clean_exit`, `valid` | `[]` | `[]` |
| `incoherent` (live) | allow/−1/13 | `unestablished` | `finished`, 0 | `clean_exit`, `valid` | `[]` | `[]` |
| `f48-claimed-order` (seam: `incoherent` with order → `query_first`) | allow/−1/13 | `query_first` | `finished`, 0 | `withheld`, `invalid`: "query_first lacks eligible prediction and complete ordering chain" | "query_first lacks eligible record or ordering chain" | `[]` |
| `f48-withheld-order` (seam: `base_fixture` with order → `unestablished`) | allow/0/0 | `unestablished` | `finished`, 0 | `clean_exit`, `valid`, no finding | "eligible record with complete chain requires query_first" | `[]` |

On the live incoherent run, `consumer.query_column` returns `allow`. The
public step carries `outcome: allow`, `rc` −1, `native_rc` −1, `errno` 13 and
`result_source: validator`. The raw record and its `raw_line` are retained.

**What this establishes.** No reader accepts an incoherent record with a
claimed order. By source, the host does not emit one: construction computes
`order` with the predicate that includes coherence, and reporting rejects any
claim that fails it. Without an order claim, every boundary
accepts the record. The label is then "the raw query answer" under reading
rule 1 (FAILURE-PROPAGATION-CONTRACT.md lines 1401–1411) and "the associated
answer" under the steps `outcome` meaning (31-steps line 69).

The arrangement is deliberate delegation: the host's receiver statement
assigns itself only types and presence, and the label rule belongs to the
emitter. The cost is interpretive. The only reply value that reflects the
incoherence is `order: unestablished`. That value is shared with a broken
chain, failed setup, missing association and a PID mismatch, so a reader who
wants to know *why* an answer is not credited must recompute coherence from
`rc`, `native_rc` and `errno`.

The one test selection by query column found
(`runner_exec_dac/check_query_scope.py` line 190) also requires
`order='query_first'`, so it does not depend on the label alone.
DT-108's conditional-null rule does not arise in these rows: the host sets
`result_source` on every built query, so `native_rc` stays visible.

The last row is a separate result, AC-1.

##### DT-50 — one identity rule in Swift, another in Rust and Python

**Sequence.**
- *Swift.* Canonical equivalence governs: request duplicate refusal
  ([ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift) lines
  112–117), association grouping and metadata equality, order matching,
  lifecycle step joins (CWorkerStepResults.swift line 55) and every
  reporting-validation `Set`.
- *Rust.* `BTreeMap<&str>` grouping and `==` on bytes (porcelain_admission.rs
  lines 1030–1091, `query_matches` at 776).
- *Python.* Dictionaries and `==` (phase_evidence.py lines 38–67; consumer.py
  lines 256–284).
- *Statements.* The rules write identity as an unqualified `==`: "Unique
  association" (31-steps lines 619–630), the cardinality conditions
  ([32-lifecycle](../docs/contract/32-lifecycle.surface.md) lines 1168–1252),
  and "Every semantic reader checks ownership … the same way"
  (FAILURE-PROPAGATION-CONTRACT.md line 605). Only two explicit equality
  definitions exist in the stated rules: canonical for `same_submitted`
  (reading rule 4, line 1419; implemented in Python as
  `same_submitted_string`, consumer.py line 176) and bytes for path-form
  `same_as_input`.

**Executed (live; seam rows match the live envelopes field for field).**

| Run | Host association issues | Host outcome | Order | Rust findings | Consumer findings | Oracle |
| --- | --- | --- | --- | --- | --- | --- |
| `nfc_id` | `[]` | `finished` | `query_first` | none, `valid` | `[]` | `[]` |
| `nfd_id` | `[]` | `finished` | `query_first` | association disagree; `query_first` lacks eligible…; `withheld`/`invalid` | `query_first` lacks eligible…; association disagree | D6 association disagree |
| `nfc_value` | `[]` | `finished` | `query_first` | none | `[]` | `[]` |
| `nfd_value` | `[]` | `finished` | `query_first` | the same two as `nfd_id` | the same two | D6 |
| `dup_id` | `duplicate_id` `s-é` count 2 | `validator_unavailable`, exit 1 | `unestablished` (query synthetic) | association disagree | association disagree | D6 |
| `both_ids` | n/a | `bad_request` `duplicate_step_id` at `probe_plan.1.step_id` (host refusal; no worker) | n/a | none | `[]` | `[]` |

**What this establishes.**
- DT-50 reproduces at this snapshot.
- The split is not specific to step IDs: it applies equally to the record's
  `filter_value` (AC-2).
- In `dup_id`, the layer that changed the result was host classification,
  under Swift's canonical grouping. Swift saw one group of two records, so it
  associated neither and the step's query is synthetic. Rust and Python, which
  group literally, recompute one associated NFC record and one `unexpected_id`
  NFD record. They flag only the disagreement in the stored issue list. By
  source inference, the literal issue list would also make `classify` report
  `validator_unavailable`, but it would have associated the NFC record with
  the step.
- Python did not flag a withheld order in `dup_id`, although its order check
  runs in both directions. Its eligibility test reads the step's own query,
  and that query is synthetic.
- `both_ids` shows that Swift also applies canonical identity at request
  admission. That is a different boundary: the request, not the evidence
  reply. Its consequence is that a reply can never carry two canonically
  equivalent step IDs. The literal step/phase joins in Rust and Python
  therefore agree with Swift on step identity only because Swift restricted
  the input. Identities that enter through child output (validator records)
  are where the readers diverge.
- In `nfd_id` and `nfd_value` the reply carries host `association_issues: []`
  and `query_first`, while Rust withholds the disposition. The result stays
  true/0.
- The number of readers that object overstates the number of independent
  judgments. The oracle's D6 finding is the consumer's `ownership_problem`
  ([lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py) lines 556–560).
  Swift's non-objection is its production join, re-applied by reporting.

These transcripts are steered. No claim is made that the shipped validator
rewrites IDs or values.

##### DT-53 — lifecycle claim checks belong to Rust and the oracle, not the general consumer

**Sequence.**
1. The host producer rejects a missing claim
   ([DispositionResolverTests.swift](../runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift)
   line 345 constructs that case). By source, such a record reaches the wire
   only in a degraded reply.
2. All seven run questions are optional in the binary schema
   (`PWDispositionRunQuestions`, [porcelain.json](../docs/porcelain.json)), so
   decoding accepts absence.
3. Rust `validate_lifecycle` reports a missing claim as `malformed_record`
   (porcelain_admission.rs line 204) and a value that differs from the raw
   reaped status as "final_status contradicts reaped status" (lines 433–460).
4. `project` withholds the disposition. Result selection ignores it.
5. The general consumer neither checks claims nor reads the values of
   `disposition_integrity` or `process_disposition`. It checks only the
   `subject_path` references of issues (consumer.py lines 954–972).
6. The oracle checks every claim against the value it computes from that
   claim's own raw field, and checks that an invalid record is projected as
   `withheld` (lifecycle_oracle.py lines 118–150, 665–676).
7. Claim "truth" in both Rust and the oracle means agreement with the retained
   raw field. Whether those raw fields are independent observations (for
   example `cleanup_trigger` derived from the stop reason, DT-46) is outside
   both checks.

**Executed (seam; frames are `base` with the constructed contract binding and
one further edit).**

| Row | Result | Rust diagnostics | Consumer (bare and envelope) | Oracle |
| --- | --- | --- | --- | --- |
| `f53-final-status-absent` | `finished`, 0 | `withheld`, `invalid`: "final_status: missing claim" | `[]`, `[]` | D8 `malformed_record` "record.questions lacks final_status" |
| `f53-final-status-17` | `finished`, 0 | `withheld`, `invalid`: "final_status contradicts reaped status" | `[]`, `[]` | D1 `wrong_answer` |

DT-53's controls edited saved JSON, and the full consumer refused those
envelopes because they differed from the retained bytes. Here the edit is in
the frame and passes through the actual Rust decode and admission path, so
captured bytes and JSON agree. The consumer then accepts an envelope that
carries Rust's `withheld`/`invalid`. DT-53's third edit (a null claim) has no
separate binary form; absence covers it.

**Which callers run which readers.** Scope: the 283 listed cases; each case's
command script and the `.sh`/`.py` files it names (resolving `${ROOT_DIR}` and
`${SUITE_DIR}`). Reader calls were found by source-text patterns:
`consumer.validate(`, `validate_fixture`, `from consumer import … validate`,
`check_record`/`check_actor_records`/`check_fixture_record`,
`witness_capture`. One false positive was removed: `shell_helpers` defines an
unrelated local `check_record`. Source-drift cases that merely share a
`run.sh` were excluded. The map is in `reader-case-map.jsonl`.

- Thirteen default cases, plus two opt-in ones, run the oracle:
  - through `witness_capture.capture`, which runs the consumer and then the
    oracle ([witness_capture.py](../tests/lib/witness_capture.py) lines 13–26),
    or by direct calls beside the consumer: `witness_contract/` `phases`,
    `extensions`, `extension_directory`, `extension_policy_qualification`,
    `extension_redelegation`, `extension_boundaries`, `actor_compositions`,
    `actor_timing_qualification`, `worker_killed_before_slot_publication`;
  - `witness_contract/worker_attempt_in_flight_at_deadline`, which calls the
    oracle without the consumer and asserts `process_disposition` itself;
  - `blackbox_e2e/checker_controls`, on constructed JSON envelopes;
  - `source_drift/porcelain_codec`, offline;
  - `runner_unit/pwrunner_core_unit_executable`, through the Rust corpus test,
    on constructed Swift frames;
  - opt-in: `witness_contract/actors_byoxpc`, `witness_contract/worker_wait_pilot`.
- Thirty default cases run the consumer without the oracle:
  - `runner_validator_failure/*` (3 cases);
  - `runner_outcome_validator_no_reply/validator_io_deadline_releases_worker`;
  - `runner_exec_dac/execute_permission_controls_spawn`;
  - four `runner_exec_lifecycle` cases;
  - `sbpl_allowdeny_consistency/sbpl_allowdeny_v1`;
  - twenty `witness_contract` cases, including the seven that use
    `check_ordering.py`, `comparison_matrix`, `test_input` and
    `max_targets_reply_survives`.
- Three of those thirty assert Rust diagnostics themselves:
  - `witness_contract/example_round_trip`: `disposition_integrity == valid`,
    no issues (check_example_round_trip.py lines 1123, 1321);
  - `witness_contract/example_round_trip_controls`: constructed;
  - `witness_contract/worker_termination`: `process_disposition` value, line 94.
- `pre_apply_failure_reports_no_policy_verdict` checks only the absence of
  cause labels. `dossier_witness` checks null diagnostics on refusal paths.
- Twelve opt-in cases are consumer-only (six `runner_byoxpc`, `guide_workflows`
  and others).
- `failure_boundaries/*` uses neither Python reader.

For the remaining consumer-only default cases, a lifecycle-claim fault that
only Rust and the oracle check would not fail the case. This is a statement of
checked scope, not an observed miss: those cases' live outputs were not
re-run.

##### DT-61 — readiness: decoder, scheduler and body readers check different things

**Sequence.**
1. *C worker* (`prepare_authority`,
   [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c)
   lines 676–752). It publishes each prerequisite cell and records a primary
   failure if any step fails. At the decision point it writes, together: the
   setup disposition, `primary_plus_one` and the header word
   `authority_status` (`MAPPED` iff the region pointer was bound after header
   validation). Then it release-stores `g_setup->published`. For required
   setup, READY and MAPPED come from the same program path and coincide.
2. *Host decoder.* It acquires the decision first and checks raw
   actor/required against its arguments and ready ⇒ required against the
   *argument* (line 98). It requires no prerequisite cell (DT-61's constructed
   control).
3. *Scheduler.* It requires a decoded decision that is free of integrity
   errors and not terminal. For a required actor, the decoder's argument
   check leaves `ready` as the only such decision. The scheduler then also
   requires the header word `authority_status == MAPPED`, read only after the
   decoder has observed the decision (ActorSession.swift line 490). It reads
   no prerequisite cell.
4. *Reply.* `authority_status` is not a wire field: `docs/porcelain.json` has
   no such name. When the gate refuses, the word appears only inside the
   classifier's error text, `shm setup: worker authority setup: status=…
   detail=…` (ActorScheduler.swift line 264; CWorker.swift line 749). The
   reply carries the decoded scope, with its decision and cells, and the
   actor's `setup_status`.
5. *Body readers.* Swift `authoritySetupIntegrityErrors`
   (PWRunnerAuthoritySetup.swift lines 142–213), Rust `setup` (porcelain_actor.rs
   lines 385–466) and Python `_setup` (actor_evidence.py lines 121–160) all check
   terminal ⇒ required ∧ primary. None checks ready ⇒ required
   ([34-equipment](../docs/contract/34-equipment.surface.md) lines 912–917) or
   the prerequisite prefix that the producer rule assigns to host and worker
   ([14-extensions](../docs/contract/14-extensions.surface.md) lines 349–360).
   No reader relates a usable `setup_status` to the setup scope.

**Executed (seam; the live `actor` frame with the constructed contract binding
plus one edit to the subject's worker setup scope).** The live baseline: both
workers `ready`, `required: true`, 12 cells including `core_limit` succeeded,
`mmap` succeeded and `header_binding` accepted; subject `setup_status: applied`;
query `before` deny / `after` allow, both `query_first`; all readers `[]`.

| Row | Result | Rust | Consumer | `actor_evidence` / `extension_evidence` | Oracle |
| --- | --- | --- | --- | --- | --- |
| `f61-core-limit-absent` (cell 3 removed; `ready` kept) | `finished`, 0 | `per_actor`, `valid`; both actors `clean_exit`; no finding | `[]` | `[]` / `[]` | `[]` |
| `f61-core-limit-failed` (cell 3 `failed`, `native_rc` −1, `errno` 1) | `finished`, 0 | the same | `[]` | `[]` / `[]` | `[]` |
| `f61-not-required` (`required: false`; `ready` kept) | `finished`, 0 | the same | `[]` | `[]` / `[]` | `[]` |

These confirm DT-61's JSON-body observations for Rust and Python on frames
that pass through the actual Rust decode, admission and assembly path. **The
Swift side remains source-only:** neither the Swift reporting validator nor the
Swift decoder was run on these frames. AC-4 states the consequence.

##### DT-95 — the outcome-changing receipt check reads constants; the binding checks run once, in the host decoder

**Checked by the host decoder** (CWorker.swift lines 679–714, in order):
1. observed application with rc 0;
2. `done`, exit 0, no signal;
3. capture-completion publication;
4. capture status 1;
5. recorded PID equal to the host-owned worker PID;
6. valid request nonce equal to the recorded nonce bytes;
7. profile type 0 and 0 < length ≤ the buffer;
8. SHA-256 of the copied bytes equal to the recorded digest;
9. recorded source length and digest, and parameter count and digest, equal
   to the host's supplied inputs.

It then emits the request nonce string, the recomputed digest, the copied
bytes, its own source length and parameter count, the recorded digests, and
constant labels. Presence is decided by the host's capture flag
([35-profile](../docs/contract/35-profile.surface.md) lines 114–125, `who: host`).

**Delegated to "the host capture rule" (35-profile line 309) and re-checked by
no recipient:**
- presence ⇔ capture requested;
- `request_nonce` = the request nonce;
- `worker_pid` = `runner_subprocess.pid` or the actor launch PID;
- decoded length of `bytecode_b64` = `bytecode_length` (stated condition, lines
  87–91, no checker);
- 0 < `bytecode_length` ≤ 1,048,576 (lines 73–79, no checker);
- `bytecode_sha256` = SHA-256 of the bytes;
- `source_sha256` = SHA-256 of the request source = `policy_sha256`;
- `source_length` = request source length;
- `params_sha256` and `parameter_count` match the request parameters;
- `profile_type` = 0;
- no `reason` on `captured`; a `reason` and no capture fields on `unavailable`.

**Checked by recipients:** status ∈ {captured, unavailable}; captured ⇒
`worker`/`before_apply`; unavailable ⇒ neither label. This is the same
predicate in the host's `contextProblem`
([PWRunnerProfileCapture.swift](../runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift)
lines 31–44), Rust `admission_problem` and Python `_validate_capture`
(consumer.py lines 575–588).

**Executed.** Seam rows carry the constructed contract binding:

| Row | Edit | Result | Rust | Consumer | Oracle |
| --- | --- | --- | --- | --- | --- |
| `capture` (live) | none | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-receipt-unrequested` | `capture`'s receipt (worker PID 51003) inserted into `base`, whose request has no capture | `finished`, 0 | `valid`, no finding | `[]` | `[]` |
| `f95-nonce` | `request_nonce` → 32 `f` | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-byte` | one byte of 492 flipped; length and digest kept | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-length-zero` | `bytecode_length` 0 | `finished`, 0 | `valid` | `[]` | `[]` |
| `f95-producer-host` (label control) | `producer` → `host` | seam: `finished`, 0, `withheld`/`invalid` with `reply_admission` "compiled_profile context is inconsistent" | — | "compiled_profile requires worker/before_apply context" | `[]` |

The production run path refuses the label control before semantic admission.
To confirm that at this snapshot, the existing test
`run_flow::tests::orchestration::compiled_profile_labels_determine_the_public_admission_outcome`
was run from the same isolated binary, with `TMPDIR` set to scratch, and
passed. It injects typed replies, deserialized from JSON, into the real `run`
orchestration: label failures give `malformed_runner_response` and exit 1;
the fixture's contradictory `captured` row gives `finished`. The seam row shows
how the same check reads where `reply_contract` is bypassed. It is not the
production outcome. The receipt edits confirm DT-95's saved-JSON and typed
observations on frames read by Rust and Python. AC-5 states the cross-anchor
consequence.

#### 3. Agreement: deliberate division, restricted inputs or shared code, and questionable rules

| Agreement | Basis | Classification | Concrete cost |
| --- | --- | --- | --- |
| All readers accept an incoherent allow record without an order claim (DT-48) | Emitter obligation (21-wire 172–185); host receiver states types only; reading rule 1 names the label as the raw answer | Deliberate delegation to the native emitter, faithfully followed by the readers | With a steered or foreign validator, `allow` beside rc −1 is reported as the raw answer. The only signal, `order: unestablished`, has several causes. |
| Swift objects to nothing in `nfd_id`; Rust and Python object (DT-50) | Swift association and reporting share one join; Python consumer and oracle share another | Shared code inside each language | Three objections from Rust, the consumer and the oracle are two independent judgments. Swift's silence is not an independent confirmation of its own association. |
| Rust and Python agree with Swift on step-to-phase joins (DT-50) | Swift request admission refuses canonically equivalent IDs (`both_ids`) | Agreement through restricted inputs | Holds only for identities that pass request admission; validator-record identities fall outside it. |
| All readers accept `ready` without prerequisites or with `required: false` (DT-61) | No reader encodes ready ⇒ required or the prefix; production ordering supplies both | The surface states a condition (34-equipment 912–917) that every body reader omits, and that holds in production by C program order | A final reply that breaks the condition is reported as valid; see AC-4. |
| All readers accept receipts whose association is wrong (DT-95) | Stated delegation (35-profile line 309) | Deliberate division of responsibility | A `captured` receipt in a `finished` envelope asserts association only through the host decoder; recipients cannot tell a correct receipt from a detached one. See AC-5. |
| Three layers apply the same receipt-label predicate, and it alone changes the result (DT-95, DT-96) | The host writes `producer` and `capture_stage` as constants (DT-96) | Design judgment, labeled as such: a questionable allocation, faithfully implemented | The checks that decide the outcome read values that carry no observation, while the request-binding checks run once, before the reply. A refusal says the reply is malformed; acceptance says nothing about the receipt's binding. |
| Lifecycle claims: Rust withholds, the oracle reports D1/D8, the consumer accepts (DT-53) | The reader-responsibility paragraph assigns claim checks to the oracle (FAILURE-PROPAGATION-CONTRACT.md lines 594–597) | Deliberate division across readers | Accepted by the consumer and invalid by Rust on the same envelope. Twenty-seven of the thirty default consumer-only cases assert neither the oracle nor the Rust diagnostics. |

#### 4. Differently named successes, and identical results that hide different checks

- `finished`/`ok: true`/exit 0 establishes the host label. In this pass it
  co-occurred with:
  - Rust `withheld`/`invalid` (`nfd_id`, `nfd_value`, `f48-claimed-order`, the
    `f53` rows);
  - Python rejection with Rust `valid` (`f48-withheld-order`);
  - acceptance by every reader of facts contradicting the request (`f95` rows,
    `f61` rows).
- `disposition_integrity: valid` certifies the controller's checks
  (41-diagnostics lines 50–60; FAILURE-PROPAGATION-CONTRACT.md line 586). It
  does not certify withheld-order consistency (AC-1), ready-setup
  prerequisites (AC-4) or receipt binding (AC-5).
- `consumer.validate == []` certifies shape, capture equality, result
  consistency and the consumer's semantic families. On the same envelope it
  does not certify the lifecycle claims or the Rust verdict (AC-3).
- `association_issues: []` in the reply is the host's join under canonical
  equality. Rust's recomputation under byte equality can disagree on the same
  frame (`nfd_id`, `nfd_value`).
- Swift reporting acceptance means the stored result agrees with reply-visible
  inputs under the production predicate. Rust acceptance means agreement under
  an independently written predicate.
- Two `unestablished` orders can mean an incoherent record (DT-48), a missing
  association, a synthetic query after a Swift duplicate (`dup_id`), or a
  broken chain. No field states which condition failed. A reader can tell
  them apart only by recomputing the conditions from `result_source`, `rc`,
  `native_rc`, `errno`, the phase ordering and the records.
- `ready` from the decoder means a published decision consistent with the
  host's expected-required argument. Scheduler activation means the
  MAPPED word was observed. The reply shows the first and only implies the
  second through `setup_status`.

#### 5. New findings (provisional labels)

##### AC-1 — Rust and Python accept different order propositions; a withheld order on an eligible record is valid for Rust and invalid for the consumer

**Statements.** The producer obligation is an if-and-only-if. The host
"Establish query order" rule (31-steps lines 573–596) sets `query_first` on
success and `unestablished` on failure, and the record table says "only when
… `unestablished` otherwise" (FAILURE-PROPAGATION-CONTRACT.md line 1226). The
recipient statements differ. The controller's family is "the complete
`query_first` chain" (41-diagnostics line 678), one direction. The consumer
"validates … `order` against the raw channel fields and `ordering`" (line
1378), with no direction stated. No statement assigns any recipient the check
that an eligible record's order was not withheld.

**Implementations.** Rust skips steps whose order is not `query_first`
(porcelain_admission.rs line 1185). Swift reporting checks only claimed
`query_first` (PWRunnerReply.swift lines 365–368; source). Python checks both
directions (consumer.py lines 555–558), and its checker control
`unestablished_despite_chain` (`checker_controls.py` line 457) pins that. That
control feeds a JSON envelope whose "host bytes" are compact JSON text:
`recapture_host_reply`, [blackbox.py](../tests/lib/blackbox.py) lines 16–31,
read through `validate_fixture`. Rust never sees it.

**Executed (seam, constructed contract binding).** `f48-withheld-order`: Rust
`valid`, no finding; consumer "eligible record with complete chain requires
query_first", on both the bare reply and the Rust envelope; oracle `[]`;
result `finished`.

**Scope and cost.** Each implementation stays within its own statement. This
is a difference in checked proposition, not a broken statement. By source, the
host computes `order` with the eligibility predicate, so it does not produce
the state. A reader cannot treat Rust `valid` as covering under-credited order,
and the Python checker control establishes nothing about Rust.

##### AC-2 — The canonical/literal split also governs validator filter values and the host's own failure outcome; request admission confines it to child-output identities

**Executed (live).**
- `nfd_value` repeats DT-50's pattern on `filter_value`. Swift associates and
  emits `query_first`. Rust reports "association issues disagree" and "query_first
  lacks eligible…", the consumer reports both, the oracle reports D6. Result
  `finished`.
- `dup_id`: Swift grouped the NFC and NFD records as one duplicate group,
  withheld the step's validator answer (synthetic query, `unestablished`) and
  classified the run `validator_unavailable`, exit 1, with error "duplicate_id:s-é".
  Rust and Python recompute one associated record plus one unexpected record
  and flag the disagreement.
- `both_ids`: the host refused the request as `duplicate_step_id` at
  `probe_plan.1.step_id`. The controller has no duplicate check of its own
  (no `duplicate_step_id` in `controller/src`).

**Statements.** Identity is an unqualified `==` (31-steps lines 619–630;
32-lifecycle lines 1168–1252). The step ID is "unique across all actions"
([12-probes](../docs/contract/12-probes.surface.md) line 23) without an
equality relation. Explicit equality is defined only for `same_submitted`
(canonical) and path forms (bytes). The comment on `validatorAssociationIssues`
(PWRunnerPredictionEvidence.swift line 157), "shared with every reader that
recomputes it", is accurate for the Swift readers, which share the code, and
describes the intended shared rule. The Rust and Python readers implement that
rule independently, and the implementations diverge because the rule leaves
string equality unstated.

**Cost.** The host's result-changing decision (`dup_id`) and its non-decision
(`nfd_id`) follow a rule that the independent readers do not apply. A reader
of the public envelope sees a host outcome and a controller finding that
disagree about how many records were associated. Steered transcripts; no
native rewrite is claimed.

##### AC-3 — On a byte-consistent envelope, the general consumer accepts lifecycle-claim faults that Rust reports as withheld and invalid

**Executed (seam, constructed contract binding).** A missing `final_status`
claim, and a `final_status` value of 17 beside a raw exit code 0, each passed
the actual Rust path to `withheld`/`invalid` with the matching finding, and
`finished`/0. `consumer.validate` returned `[]` for the bare reply and for the
complete envelope, whose captured bytes are the edited frame. The oracle
reported D8 and D1.

**Scope.** This extends DT-53 from saved-JSON edits to a frame read by every
reader. The reader-responsibility paragraph (FAILURE-PROPAGATION-CONTRACT.md
lines 594–597) describes the consumer's checks as shape, required-field and
semantic checks, and assigns lifecycle claims to the oracle. I read that as
deliberate division, so this is not an unmet consumer promise. The consequence
is in the registry: thirty default cases call the consumer without the oracle,
and three of them assert the Rust diagnostics themselves. Lifecycle claim faults that only Rust and the oracle
detect would pass the other twenty-seven, by checked scope. No live omission
was observed.

##### AC-4 — Required-authority activation rests on a header word the reply does not retain, and no reply reader relates `ready` to its prerequisites or to the actor's setup status

**Source.** The scheduler activates a required actor on decoder integrity, a
non-terminal decision, the setup publication and `authority_status == MAPPED`
(ActorScheduler.swift lines 257–288). MAPPED is written by the same C decision
block as the disposition (pw_probe_runner.c lines 748–753), from the bound
region pointer rather than the primary-failure variable. It is a second
encoding of one decision, not an independent observation. It is absent from
the wire schema and appears only inside the classifier's error text when the
gate refuses.

**Executed (seam, constructed contract binding).** A frame with `ready` and a
missing or failed `core_limit` cell, or `required: false`, beside
`setup_status: applied`, was `finished` with Rust `valid` per actor and `[]`
from the consumer, `actor_evidence`, `extension_evidence` and the oracle.
Swift reporting was not run on these frames (source: it does not check these
relationships).

**What a final-reply reader cannot distinguish.** From `ready`,
`setup_status: applied` and a missing or failed prerequisite cell, a reader
cannot tell whether the worker's MAPPED word was observed and a cell was lost
before the reply, or whether the cells are accurate and the scheduler
activated on a different fact. The C program order makes the two coincide in
production. That shared assumption is the only thing joining the activation
decision to the retained cells.

##### AC-5 — After producer admission, only geometry and the receipt's constant labels change the run result; the receipt's request binding is checked once, before the reply, and nowhere after

**Map.** Section 1 lists every boundary that can change the result. After the
controller holds a decoded reply under the expected producer contract,
collection geometry and the receipt status/label check are the only
semantic-record checks that refuse the reply. Every other relationship adds
diagnostics or is unchecked. That includes the receipt's request association
and its internal byte, length and digest relations.

**Executed (seam, constructed contract binding; and unit).** A receipt
inserted into a reply whose request did not ask for capture (carrying a
different worker PID), a replaced nonce, a flipped bytecode byte and a zero
length were each `finished` with Rust `valid` and consumer `[]`. The existing
label test passed at this snapshot.

**Cost (design judgment, labeled).** The outcome-changing check reads two
values the host writes as constants (DT-96). The association checks run once,
in `decodeProfileCapture`, and nothing in the reply lets a recipient
distinguish a correct receipt from a detached one without the request. The
live tests that do compare (contract.py lines 323–332, 430–435, 483–488) do so
for their own outputs. The statement acknowledges the delegation, so this is
not an unmet promise. The concern is that the only receipt check visible in
the outcome is the one with the least evidential content.

##### AC-6 — Swift reporting re-checks association and order with the production predicate, and the oracle's phase finding is the consumer's; agreement counts overstate independent judgments

**Source.** `validatorOwnershipProblem` recomputes issues with
`validatorAssociationIssues` (PWRunnerReply.swift line 77), and the order
check calls `eligibleOrderedStep` (line 365), the functions that produced the
values. The oracle's D6 comes from `phase_evidence.ownership_problem`, the
consumer's function (lifecycle_oracle.py lines 556–560). The oracle's
extension check is the consumer's `validate_extensions` (line 591).

**Executed.** In `nfd_id`, `nfd_value` and `dup_id`, three readers object:
Rust, the consumer and the oracle. Only Rust and Python are independent
implementations, and Swift's silence is its production rule restated.

**Scope.** The rationale for sharing is stated: uniform ownership checks, and
reporting validated against reply-visible inputs (Section 1). It achieves
that within each language. It cannot reveal a disagreement between languages,
and FAILURE-PROPAGATION-CONTRACT.md line 605 promises that "every semantic
reader checks … the same way" across them. DT-50 and AC-2 show the languages
do not. Counting reader verdicts therefore does not measure independent
confirmation.

#### 6. Cross-references

- **DT-23 and DT-51** (unapplied-actor validator failures become `finished`)
  are another route by which a host classification decision, not a reader
  judgment, sets the result. The `dup_id` run shows the converse: a Swift-only
  rule changing the result.
- **DT-24** (`missing_reason` and `pid` meanings) is a neighbor of the `dup_id`
  step. That step carries `missing_reason: validator_no_verdict` and the error
  "no validator verdict for this step", while its phase retains two records:
  one byte-identical to the step ID and one canonically equal to it. The
  reason fits its definition ("produced no associated record"), because no
  record was uniquely associated. The error text does not distinguish an
  ambiguous association from absent output.
- **DT-25** found canonical target equality in Swift. Reading rule 4 adopts it
  and Python implements it with NFC. DT-50 and AC-2 concern record identity,
  where no rule states the relation and the readers diverge. The difference
  between the two is that one has a stated equality and the other does not.
- **DT-38, DT-47 and DT-101** (support-scope findings) bear on AC-1. The
  Python order control and the Rust receipt-label test each establish
  behavior through a narrower path (JSON fixture; typed injection) than the
  frame path executed here.
- **DT-49** (a diagnostic's `rc` versus `native_rc`) is a sibling of DT-48:
  both concern how the query projection forwards record values without
  re-deriving them from the native pair. DT-49's input is a diagnostic record;
  DT-48's is a prediction label.
- **DT-52 and DT-53** (consumer tolerance) are extended by AC-3 to a
  byte-consistent envelope. DT-52's missing-errno tolerance was not re-tested.
- **DT-57** (empty ID rejected only by the oracle) is another oracle-only
  judgment. Under AC-3's registry map, it is visible only in the cases that
  run the oracle.
- **DT-60** (a mismatched raw association still projected) concerns the same
  decoder as DT-61 and AC-4, where the decoder's checks against its arguments
  are its whole readiness check.
- **DT-96 and DT-97** (constant labels; nonce never in the compiled bytes)
  explain why the label check in AC-5 has little evidential content.
- **DT-108** (conditional-null projection) did not arise in these rows,
  because host-built queries always carry `result_source`. Rust's typed
  checks and Python's projected checks saw identical values on every seam
  row (`decode_bound` equality).

#### 7. Remaining uncertainties and limits

- The Swift reporting validator, `decodeAuthoritySetup` and
  `authoritySetupIntegrityErrors` were not run on any edited frame. Their
  judgments of the f48, f61 and f95 edits are source reading.
- Every seam row carries a constructed `producer.contract` edit. The seam
  bypasses `reply_contract`. Its placeholder inputs (`preparation-0`, the
  writer-cap pair and `normal.pwp`) produced rows that were disregarded.
  Fidelity was checked only on the twelve unedited rebound rows.
- All non-native validator transcripts are steered. No claim is made that the
  shipped validator emits incoherent labels or rewrites Unicode spellings.
- The reader map is a static text search over command scripts and the files
  they name. It does not establish that each named check executes on every
  invocation, and no registered case was run. Their current pass status is not
  claimed.
- The `actor` specimen is this pass's own. It was not coordinated with other
  passes and covers one required-authority configuration.
- No Swift package, mutated app or registered battery was built or run. The
  only build was the unmodified controller test binary in an isolated target.
