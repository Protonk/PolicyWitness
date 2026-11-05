# Critique resolution and refreshed acceptance

The user authorized resolving C1–C6, including corrective test reruns, and
returning before retirement. Those actions are complete. This record refreshes
the acceptance evidence; the earlier `../ACCEPTANCE.md` remains an unchanged
historical checkpoint. F1 remains the sole accepted deferral. Nothing has been
retired, pruned or unpinned.

The lookback includes I1's production host-admission diagnostic correction and
regenerated worker identity. They were already present in signed build 1121
and commit `f25c18edba1d0d60b9dcf517ce26de03e6edf760`. This critique tranche adds
documentation corrections, Rust tests and their generator/check ownership;
it makes no further production behavior change. Follow-up changes and these
new records are pending commit at this checkpoint.

## Resolved items

| Item | Resolution and evidence |
| --- | --- |
| C1 — refusal fields | Audited all 30 admission rows against emission sites. The manifest now uses literal fields or defined zero-based indexed templates, including actor prefixes and `extension.issue` through `extension.release`. Separate location fields and diagnostic path arrays are distinguished. Declaration repeated-consume/release rows explicitly identify meaning-refusal codes and paths instead of inventing numeric admission fields. Adjacent counting descriptions were aligned. `documentation-report.md` preserves the row-by-row source audit. |
| C2 — parallel process account | Replaced the fixed four-process statement with the controller/client/host, one worker per sandboxed process (one per actor), and the relevant validator, issuer, exec and fallback-helper lifetimes. The owning limits generator regenerated shared content and staged `dist/PolicyWitness.md`; that standalone file is byte-identical to `docs/PolicyWitness.md`. No app/ZIP rebuild occurred. |
| C3 — limit-change selection | The clean default run plus four supplemental cases cover 89 of the 90 cases in the seven required suites. The remaining case is the already deferred F1 sensitivity control, explicitly excluded rather than silently skipped. Full `integration` and all eight `source_drift` cases passed. |
| C4 — build 1121 battery | A complete 216-case default battery passed against the unchanged, valid signed build 1121. The preceding full run's single static owner-registration failure is retained below. No earlier build's outcome is substituted for this fresh result. |
| C5 — Rust diagnostic bounds | Three Rust tests now own both manifest values and literal depth 8/9 and component 63/64 UTF-8-byte boundaries, including multibyte strings, whole-path withholding and serialization. Their citations appear beside the Swift checks. Tests passed in `unit/rust.unit`; the production prefix of `request_patch.rs` is unchanged. `rust-bounds-report.md` records scope and assertions. |
| C6 — durable acceptance evidence | Identified raw observations, provenance and failures are copied into the record packages below. The two current passing run trees are preserved completely, with explicit symlink/directory identities; the superseded first run retains root/integrity receipts and its failed case. Historical support and omissions are separately identified. Acceptance no longer depends on the referenced managed run directories surviving retention. No pin replacement was needed. |

All 95 numeric values and units remain unchanged. The generator-contract text
now describes indexed templates and the two meaning-only exceptions precisely.
It also states the actual verification boundary: generator checks establish
nonempty descriptions and valid source/check references; correspondence with
emitted fields is source-reviewed, not mechanically proved by that check.

## Fresh execution

All executions used separate managed output directories and ran serially.
The source inputs remained unchanged during each run; the clean default and
supplemental runs used the same final input hashes. No sleep was recorded.

| Managed directory under `tests/out/runs/` | Run ID | Outcome |
| --- | --- | --- |
| `doc-lookback-critique-default-01` | `20261105T153920Z_e5426466` | 215 pass / 1 fail; all 216 completed. `source_drift/limits_documentation` rejected the missing new Rust path in its independent exercised-owner set. The suite-exit error is retained. |
| `doc-lookback-critique-default-02` | `20261105T155453Z_a3f793db` | 216 pass; all completed, no skipped/unrun cases or harness errors. |
| `doc-lookback-critique-controls-01` | `20261105T160939Z_eb80fd9d` | Four pass; all completed, no skipped/unrun cases or harness errors. |

The only source correction between the two default runs adds
`controller/src/request_patch.rs` to the exercised-owner set in
`tests/suites/source_drift/limits.py`. No assertion was relaxed. The first
failure is an integration omission, not attributed to the environment or F1.
The complete default battery was rerun after that correction.

The four supplemental passes are `runner_unit/exec_reader_mutations`,
`runner_unit/reaped_ack_mutation`, `runner_unit/actor_handoff_mutations` and
`runner_c_worker_harness/native_clock`. The last retains 36,000,000 usable
continuous-clock samples, old-clock failures in six of nine runs and five deny
records with log status zero. Those are observations on this equipment, not
platform-wide qualification.

There are 220 distinct current passing cases. Within the seven-suite
limit-change selection (`unit`, `integration`, `source_drift`,
`runner_abi_layout`, `runner_unit`, `runner_c_worker_harness`,
`failure_boundaries`), 85 cases pass in the default and four in the supplement.
`runner_unit/host_setup_oracle_sensitivity` is the 90th, deferred as F1. The
clean default does not establish that F1 is repaired. The fresh Swift case
also passed all 525 tests and its three downstream reader replays.
Selection and terminal coverage are recorded in `selection-coverage.json`
and `final-state.json`; the three `*-result.json` files preserve run summaries.

## Source, equipment and reading applicability

`pretest-state-02.json` records all 1,410 non-record/non-plan source-input
hashes, HEAD and the prepared patch. `final-state.json` confirms they still
match, identifies the final source-only patch, and records archive identities.
The earlier candidate snapshots remain unchanged. Both default runs validated
the distribution app before execution and found it unchanged afterward; its
45-entry inventory equals the original repair run's build 1121 inventory.
The Rust production prefix, worker identity and numeric limits remain
unchanged in this tranche.

Build 1121 retains its original `ea64218b` dirty-source provenance. It is not
relabeled as a build of `f25c18ed` or this follow-up. Changes to `limits.json`
prose/check ownership and Rust `cfg(test)` code were reviewed as irrelevant to
the shipped production bytes. No release or notarization claim is made.
The staged standalone guide is current; the signed app and ZIP remain their
existing build-1121 artifacts, and this record does not claim the ZIP's guide
was refreshed. `staged-guide-before.md` preserves the previous standalone copy.

The original final-reader artifacts and histories are unchanged. ARCHITECTURE
still has its previously accepted R1 post-reading delta; WORKER is unchanged.
The LIMITS reading artifact now predates C1's field/counting corrections and
the added Rust citations. The source audit and fresh checks cover those
changes; the earlier pair is not credited with reading them. Numeric limits,
the principal explanations and the accepted R2/R3 evidence qualifications
remain intact. A new whole-document pair was not needed for these bounded
accuracy and ownership corrections. The user-approved WORKER inventory/
crosswalk approach remains unchanged.

## Durable packages and limits

The following paths are relative to this directory. Each manifest identifies
original paths/run IDs, hashes, byte counts and the corresponding archive
members. All unique archived byte streams were read back and hash-verified;
the coordinator also checked the archive-file hashes. The original managed
runs remain gitignored local evidence. The new copies are record artifacts
pending commit and are outside managed-run retention.

| Archive | Compressed bytes | SHA-256 |
| --- | ---: | --- |
| `current-evidence/evidence.tar.gz` | 50,289,445 | `efd5c15b4b16c1ddc76f996e59ee5935a3dfa4a9823591c4d66f7ffa3382f238` |
| `historical-evidence/evidence.tar.gz` | 23,579,844 | `8de145d7fee00fb786acab64cfffc952c74d5c9a6a9d4d19fd301380502960b4` |
| `historical-evidence/older-complementary.tar.gz` | 2,805,402 | `666314789e194d19e63bb126d9f2aba80b9a2c15ae67f78a305682bd0ed0ef47` |

The current manifest maps 36,323 files to 17,200 unique blobs, plus 88
symlinks and 11,588 directory identities. It explicitly omits the first
default run's 215 superseded passing-case directories; their terminal results
remain in its root receipts. Both replacement passing run trees are complete.
`preserve_current.py` copied only terminal, owner-checked runs while holding
the checkout lock. It does not relocate ownership or perform cleanup.

The historical manifest maps 12,334 original paths to 9,468 archive members.
It preserves the eleven previous lookback/audit runs' available root receipts,
the observations credited for I1–I3, documentation failures/passes, build 1121
provenance and the older pins' complementary observations. The existing 17
F1 copies were verified against their originals. `evidence-report.md` explains
which raw observations support which claims and lists provenance limits.
Historical compiled equipment and redundant source trees are explicitly
omitted; this is not a complete portable replay environment. No missing source
identity or transcript was invented.

The older pins remain unchanged. Five of their nondefault observations are
not replaced by the new default/supplement (`order_barrier_mutations`,
`extensions_byoxpc`, `actors_byoxpc`, `reservation_controls`,
`registry_recovery`); their available evidence is preserved without assigning
new execution credit. Any future pin retirement still needs its own credit
and live-cleanup-ownership assessment. Inert copied recovery/session receipts
do not establish present settlement or authorize removal.

## Reconvening point

C1–C6 are resolved with the stated evidence limits, and stage 6 acceptance is
refreshed. Three fresh specialists completed documentation/source review,
Rust boundaries and historical evidence preservation; the lookback total is
26. No build, test, reader or agent task remains active. No new deferral was
added, and no further F1 execution occurred. The next step is the user's
pre-retirement review, including the pending follow-up commit and any later
retirement/retention decision. The root outflow plan remains the single handoff.
