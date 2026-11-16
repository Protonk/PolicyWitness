# Validation memo 1: acceptance report (draft-1)

Validator: Sonnet. Snapshot: HEAD cc55288d, clean tree. Read-only: I read source, docs, the saved artifacts under `.tmp/contract-trio/acceptance/` and ran Python only on saved JSON and source text. I did not rebuild, rerun the seam or repeat live runs. The report is not rewritten here; each concern says what a claim would need to be supported.

## Concerns

### V-1. "No reader relates a usable `setup_status` to the setup scope" is contradicted by Rust and Python (overstated)

Located: DT-61 Sequence step 5, last sentence; AC-4 heading ("no reply reader relates `ready` to its prerequisites or to the actor's setup status"); AC-4 "What a final-reply reader cannot distinguish".

Checked: `controller/src/porcelain_actor.rs` `application` (lines ~468-602), `tests/lib/actor_evidence.py` lines ~170-225. Both require an `applied` actor not to carry a `terminal_required_failure` scope (`!applied || (... && !terminal && ...)` at porcelain_actor.rs 596-603; actor_evidence.py ~220), and tie the `terminal_authority_setup_refusal` assessment to the terminal scope. So readers do relate an actor's applied/usable status to the scope, in the terminal direction.

Finding: what the f61 seam rows establish (ready kept, prerequisite cell missing/failed or `required: false`, `setup_status: applied`, all body readers `[]`) is that nothing relates `ready` to its prerequisite prefix or to `required`. The relation "applied is incompatible with a terminal scope" exists. To be supported the sentence and heading need to say the missing direction (non-terminal/ready scope to prerequisites), not "no reader relates".

### V-2. "No reader accepts an incoherent record with a claimed order" (overstated wording)

Located: DT-48 "What this establishes", first sentence.

Checked: `corpus/analysis.txt` row `f48-claimed-order`: Rust withheld/invalid, consumer rejects (bare and envelope), but `py_lifecycle_oracle` is `[]` and the Swift reporting validator was not run on that frame (report section 7 says so). The report's own table shows Oracle `[]` on that row.

Finding: the claim holds for Rust and the Python consumer (executed), and for Swift by source (PWRunnerReply.swift 365-368 does check claimed `query_first`; I confirmed). The oracle accepts the row. "No reader" needs "no order-checking reader" or the oracle and Swift qualification.

### V-3. "All readers" / "every reader" wording for the DT-61 and DT-95 edits (overstated scope)

Located: section 3 rows "All readers accept `ready` without prerequisites or with `required: false`" and "All readers accept receipts whose association is wrong"; section 4 "acceptance by every reader of facts contradicting the request (`f95` rows, `f61` rows)".

Checked: Rust, Python consumer, `actor_evidence`, `extension_evidence` and the oracle were run on these rows (analysis.txt: all `[]`/`valid`). Swift reporting validation, `decodeAuthoritySetup` and `authoritySetupIntegrityErrors` were not (report section 7 and DT-61 closing paragraph say so). The Swift side rests on source reading (I confirmed the Swift decoder checks `ready => required` only against its argument, AuthoritySetupRuntime.swift ~98, and `contextProblem` only the label predicate). Seam rows also carry the rebound `producer.contract`.

Finding: the limit is disclosed in the report, but these three sentences state it without it. They need "every reader that was run" or an explicit "by source for Swift".

### V-4. Scheduler gate paraphrased as `authority_status == MAPPED` (supported with caveat)

Located: DT-61 Sequence step 3; section 1 Actor scheduler row; AC-4 Source.

Checked: ActorScheduler.swift 257-266. The gate is `actorSetup != 0 && (authorityStatus >= 3 || (authorityFD != nil && authorityStatus != 1))`. MAPPED = 1, DESCRIPTOR_MISSING = 2 (abi.h 161-162). Equivalence to "== MAPPED" holds only when an authority descriptor is present; with no descriptor, status 0 or 2 does not refuse. `ActorSession.swift` 490 reads the word only when the decoder observed the decision (confirmed). The C decision block (pw_probe_runner.c 745-752) writes disposition, primary and status together before the release store (confirmed).

Finding: the C-side and reply-retention claims are supported. The "requires MAPPED for required authority" summary omits the `authorityFD != nil` condition. I did not trace whether a required actor can lack a descriptor, so I cannot say the omission has an effect.

### V-5. Reader-to-registered-case map (supported with caveat on wording)

Located: DT-53 "Which callers run which readers"; section 3 last row; AC-3 Scope.

Checked: `reader-case-map.jsonl` (74 rows, 66 distinct cases, hash matches the report) and `scripts/reader_case_map.py`. Recounting by distinct case (counting `witness_capture` as consumer plus oracle, excluding the source_drift cases that merely share `porcelain_codec.py`): oracle default = 10 witness_contract/blackbox cases + `porcelain_codec` + `pwrunner_core_unit_executable` = 13; consumer-only default = 30 with the 20/3/1/1/4/1 breakdown listed in the report; three of those assert diagnostics (`example_round_trip`, `_controls`, `worker_termination`); opt-in consumer-only = 12; two opt-in with oracle. All match the report. The ignored Rust test is invoked by the default `runner_unit` case (run_flow.rs 1251 ignore text).

Independent check beyond the script: the script follows only paths named in command scripts and does not follow Python imports. I grepped `tests/lib` and `tests/suites` for `lifecycle_oracle|check_record|check_actor_records|witness_capture`. Every hit is a file the map already classifies as oracle-bearing, plus `blackbox_e2e/disposition_controls.py` and `extension_controls.py`, which are reached only through `checker_controls.py` (an oracle case). The consumer-only checkers import `lifecycle_contract` only for `CAUSE_LABELS`. So the "consumer without oracle" count survives an import-level search for the oracle. Section 7 discloses the static-text method.

Finding: supported. Caveats: (a) "assert neither the oracle nor the Rust diagnostics" for twenty-seven rests on a regex `disposition_integrity|process_disposition` over the checker file only, and the report itself notes `pre_apply_failure...` and `dossier_witness` assert related things, so "twenty-seven assert neither" slightly overstates; (b) "would pass" is correctly hedged as checked scope, not observed. The map has duplicate rows for multi-checker cases (`actors_byoxpc` x3 etc.); the report's counts are by case, which I confirmed.

### V-6. "The one test selection by query column found" (scope not justified, method unstated)

Located: DT-48 "What this establishes", last paragraph.

Checked: `grep` for `select(...query=` finds only `runner_exec_dac/check_query_scope.py:190`, so "one selection" is right. Other `query_column` uses exist: `check_query_scope.py:166` (asserts `unavailable`) and `witness_contract/check_comparison_matrix.py:151` (compares `query_column` with the row's `query` beside all comparison keys including `order`).

Finding: conclusion ("does not depend on the label alone") still holds, since the matrix compares `order` as well, but the report does not state the search or mention the matrix check, so the negative's scope is not shown. The report would need the pattern searched and the two other uses.

### V-7. Cross-reference grouping of DT-38, DT-47, DT-101 under AC-1 (cross-reference does not preserve evidence limit)

Located: section 6, "DT-38, DT-47 and DT-101 (support-scope findings) bear on AC-1."

Checked: DT-101 concerns the host receipt-check fixture (six of nine reasons occur in no test); DT-38 and DT-47 concern other support scopes. The second sentence of the bullet ("the Python order control and the Rust receipt-label test each establish behavior through a narrower path") is true of the checker control (blackbox.py 16-31, JSON text recaptured as host bytes, confirmed) and of the label test (DT-95 text), but the label test belongs to AC-5, not AC-1.

Finding: DT-101's limit (host decoder reasons mostly untested) is relevant to the DT-95 section and AC-5, where the report lists nine decoder conditions as "Checked by the host decoder" without that limit. Classify as incorrect attachment plus an omitted earlier limit; the DT-95 section would need to say the nine conditions are source-read, with only some reasons exercised by tests (per DT-101).

### V-8. Minor: line citations and counts that need no change

I spot-checked cited lines and they hold: FAILURE-PROPAGATION-CONTRACT 605, 1226, 1378, 1401-1411, 1419; 41-diagnostics 678; consumer.py 555-558, 575-588, 954-972; checker_controls.py 457 (`unestablished_despite_chain`); porcelain_admission.rs 1185, 1308-1330, 204, 460; PWRunnerReply.swift 77, 365-368; CWorker.swift 679-714; ProbeRunner.swift 112-117; json_contract.rs 21-22; lifecycle_oracle.py 556-560 and 591. No incorrect citation found among those checked.

## Consequential claims checked and found supported

- Seam rows (all of them): I recomputed every row in `corpus/analysis.txt` (25 rows) against the report's tables for DT-48 (f48 rows), DT-50 (nfd-id, nfd-value, dup-id, both-ids), DT-53 (f53 rows), DT-61 (f61 rows), DT-95 (f95 rows). Outcomes, Rust diagnostics, consumer findings (bare equals envelope), oracle D1/D6/D8 and the `f95-producer-host` reply_admission finding all match.
- Fidelity control: exactly twelve rows carry fidelity fields, all with empty diffs; `py_binary_projection_equal` true on all 25.
- Live runs: `live/summary-*.json` for base, base_fixture, incoherent (allow, rc -1, errno 13, `unestablished`, `query_column` allow, valid), nfc/nfd id and value (association issues empty at host, consumer and oracle reject NFD), dup_id (`validator_unavailable`, exit 1, group count 2, synthetic step with `validator_no_verdict`), both_ids (`bad_request` `duplicate_step_id` at `probe_plan.1.step_id`), capture and actor, all match the tables.
- Bare-reply, envelope and body-helper distinctions: `reader_corpus.py` lines 85-89 show `validate_fixture` on bare reply and on the Rust-assembled envelope, `actor_evidence`, `extension_evidence` and `check_record` separately; the report's columns follow that and the constructed `producer.contract` limit is stated.
- AC-1: Rust skips non-`query_first` steps (porcelain_admission.rs 1185); Swift reporting checks only the claimed direction; Python checks both (consumer.py 555-558). "No statement assigns the withheld-direction check": I read 31-steps 573-660, 41-diagnostics 678 and FAILURE-PROPAGATION 1378; the only related text is 31-steps line 291 ("`unestablished` retains the channels without that temporal assessment"), a meaning statement that assigns no check. Supported.
- AC-5: `admission_problem` (porcelain_admission.rs 1308-1330) checks geometry, status and the two labels only; `reply_contract` adds the producer contract; the nine decoder conditions in CWorker.swift 679-714 match the report's list and order; the delegation text is 35-profile (via DT-95 quotation). The f95 rows `valid`/`[]` match.
- AC-2 and AC-6: `validatorAssociationIssues` is recomputed in `validatorOwnershipProblem` (PWRunnerReply.swift 77); the oracle's D6 text is the consumer's `ownership_problem` output; the FAILURE-PROPAGATION line 605 paragraph is about validator-block ownership and recomputed `association_issues`, which supports using it for the AC-2/AC-6 divergence. "No `duplicate_step_id` in controller/src" confirmed by grep (only runner sources).
- Producer versus recipient: "host receiver states types and presence only" and "coherence tested only in the order rule" match 31-steps "Native answer" and CWorkerStepResults.swift 44-49, 128-139.
- DT-48/50/53/61/95 cross-references to earlier findings (DT-50 oracle result and steered-transcript limit, DT-53 saved-JSON controls and capture-equality caveat, DT-61 controls and source-only Swift/Rust statements, DT-95 label test and saved-JSON mutations) preserve those entries' differences. Cross-references to DT-24, DT-25, DT-52, DT-57, DT-60, DT-96 and DT-97 are consistent with the entry text I read. DT-49 as a "sibling" of DT-48 is a loose analogy, not an error.
- Listing and hashes: catalog has 283 cases, 232 default; hashes for rust.json, python.json, edits.json, the reader map and the scripts match the prefixes in the report.

## Unresolved limits

- I did not run Swift code, so every Swift judgment (reporting validator, decoder, scheduler) is source reading by both author and me.
- I did not rerun the seam, the live runs or the label unit test; their results are taken from saved artifacts. The unit-test pass and the app-hash invariance statement are therefore not independently confirmed.
- I did not verify the frame editor's byte-level claims that each edit differs from its rebound base only in the intended field (`edits.json` has 24 entries; I read it only for existence).
- Whether a required actor can lack an authority descriptor (V-4) is untraced.
- "Earlier passes saw lookup error 159 in the sandbox" and the environment statement are not checkable from the saved artifacts.
- Whether production cases would fail on a lifecycle-claim fault by some assertion not matched by the reader map (for example an `ok`/exit assertion) is unknowable without running them; the report does not claim it.
