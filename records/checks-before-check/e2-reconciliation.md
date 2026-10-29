# E2 source reconciliation and factual follow-up

Examined main checkpoint: `29d1c797f7e057dae507abf0a8b47ee6473d7b55`, compared
with D2's fixed source `7562d24ac2334122499ea349010fd67211058ac3` on 2026-10-29.
This is source and retention inspection, not a new behavioral credit. The
primary executor approved C4/C5 after reviewing their exact wording and paths.
`e2-reconciliation-facts.json` retains the comparison hashes and availability facts.

## C4 — dated launch evidence and present availability

Neither `tests/out/runs/worker-doc-launch-20261018` nor
`tests/out/runs/validator-selection-receipts-20261018` exists in the examined main
checkout or appears in its retained-run manifest. The receipt remains useful:
it preserves the original run/source/app identities, copied observations and
original hashes. A hash of unavailable bytes does not supply those bytes.

At E2, six of the receipt's seven source-file hashes differ; only run_capture.py
matches. This is an applicability warning for review, not proof of a changed
launch observation. No current census, current worker identity credit or live
reobservation is claimed. The unchanged receipt and L's unchanged authored
paragraph make the two precise account edits independent of E2's other WORKER
changes.

The WORKER correction preserves the sentence listing the receipt's command,
specimens, source hashes, selected raw captures and final worker evidence. It
replaces only the unsupported complete-raw/pin claim with current unavailability
and the limit of dated observations. The JSON correction changes only
`raw_evidence_availability`; all source identities, hashes, copied observations,
configuration and reuse instructions remain exact. No generated worker graph is
edited or restamped. The finding is corrected as an availability account; the
dated observation still requires review before reuse for another implementation.

## C5 — both existing release baseline gates

SIGNING and release_preflight.py are identical between the D2 base and E2.
`inspect` invokes both `inspect_baseline` and `inspect_build_baseline`. Each
compares committed baseline entries with the nearest preceding annotated release
and refuses additions/rewrites. Missing prior baselines have an explicit report
status. The prose-only release-procedure account omitted the second gate.

The SIGNING correction names both baseline files and distinguishes prose sites
from build entries. It describes the existing report mode without changing
release policy, baseline entries, generators or checks. Source inspection and
the pre-existing constructed-history controls support that account; no release
command or publication was run here.

## Integration boundary

The five generators and the selected architecture/build/contract/generator
control modules are identical between the D2 base and E2 before these D2 edits.
That comparison explains compatibility of the bounded repair locations; it
does not establish the full fixture dependency closure. E2 changes contract,
limit and worker accounts, generated outputs, catalog/test inputs and other
production/consumer sources. Its response schema is 24; the T4 trace's 23 remains
correct only at its explicitly named historical source. The fixed ownership JSON
and trace records are preserved as historical facts, not silently restamped.

The isolated five-case pass at `53b8e88` precedes C4/C5. Local review checks that
only the intended receipt field and authored paragraphs changed, that the
generated architecture remains current, and that F1 is byte-identical. A fresh
five-case run in main after integration will supply combined verification and
properly located retained evidence. No isolated raw output is added to main's
retention manifest.

C1–C5 now have bounded implemented candidates. F1 remains unresolved by the
user's explicit decision. B1 machinery remains declined for this candidate.
Final D2 acceptance and coordinated D1 retirement await primary integration and
review; no future CHECK handoff or C0 evaluation is introduced.
