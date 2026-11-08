# Worker wait acceptance review

This record belongs to the [worker wait exploration plan](../runner/WORKER-WAIT-EXPLORATION-PLAN.md).
It reaffirms HOST-01, HOST-02 with HOST-03, SCAN, and the preparation rejection
using corrected interpretation of the existing observations. It supplies no
new native measurements. Retire it with that plan after carrying any facts
still needed by ARM into its record or the outflow.

## Reader and instrument

Timestamp reader version 10 compares `max(candidate value + uncertainty)`
with `min(baseline value - uncertainty)`. The difference must be at most 2 ms.
Each side's largest uncertainty is summed for the 0.5 ms resolution gate;
unknown uncertainty on any trial withholds credit. Every applicable response
must occur on every accepted trial, with the declared number of matched pairs.
Missing declared phases or deliveries refuse completed pilot trials.
The reanalysis reader SHA-256 is
`2f344d858c91c8d42f31d4eb07ecd80645f28320116b5d6d13c3597b5a846f4b`;
its source and the other interpreted equipment are copied beside the outputs.

Host export version 2 adds stamps immediately before and after the inbound
commit store. Both are required. Version 1 exports retain a wider publication
bracket from the enclosing custody-service start to the transfer-wait start.
This includes a possible scheduling delay after the commit. It does not treat
the wait-start stamp as the publication itself.

The constructed controls cover the exact 2 ms boundary, extrema selected after
uncertainty expansion, uncertain non-extremal trials, missing responses on one
or both sides, insufficient pairs, missing all inbound starts, missing version-2
commit stamps, and the conservative legacy bracket when the wait stamp is
delayed. Production host and worker source and the signed app are unchanged.

## Reanalysis and disposition

The original run receipts, instrument identities and summaries remain intact.
Version-10 outputs and their source hashes are separate attachments under
`tests/out/runs/worker-wait-review-final-01/worker-wait-review/`.
The reanalysis uses both sides' original stamps with the same reader and
checks calibration from its retained raw observations. It replaces the earlier
response-bound credits; it does not change their frozen 2 ms acceptance rule.

| Comparison | Accepted trials | Complete matched pairs | Response bounds | Largest corrected bound |
| --- | ---: | ---: | ---: | ---: |
| HOST-01 | 120 | 60 | 36 | 185.541 µs |
| HOST-02 | 120 | 60 | 36 | 123.123 µs |
| HOST-03 | 120 | 60 | 36 | 104.955 µs |
| SCAN | 140 | 70 | 172 | 108.791 µs |

Every response bound is credited, including its uncertainty and complete
coverage. The HOST comparisons include four inbound bounds the earlier
acceptance summaries did not report. Their wider legacy commit brackets
account for the larger corrected maxima. The pilot's 144 trials remain
accepted. Its decomposition still supports the preparation rejection and ARM's
choice of a worthwhile benefit metric; it does not establish a CPU benefit.

HOST-01's shorter ordinary holds, HOST-02's detection improvement and whole
request regression, HOST-03's improvement when combined with HOST-02, and
SCAN's reduced loads per pass retain their dispositions. HOST-03's CPU,
sampled memory and peer interference remain unobserved by its comparison;
the latency observation cannot establish that those quantities did not worsen.

The only changed shared pair verdicts are SCAN A2D rapid delivery 51's
any-pair worsening flags: its wider uncertainty no longer resolves that
difference. Neither was the frozen every-pair regression gate. The null
comparison retains its two pairs per group as noise evidence; its response
credits are withheld because qualification requires five pairs.

## Verification and retention

`worker-wait-review-final-01` is the complementary repair run: reader controls
and the source-drift selection, 10 of 10 cases passing in
`20261108T170353Z_36ac19c5`, with no skips, unrun cases, harness errors or system
sleep. The controls reject 76 constructed faults after 65 accepted receipts.
The reanalysis is attached separately from case results. The retained default
battery is `main-scan-default-01`, run
`20261108T161704Z_e29fe638`, with 222 passing cases. Its production checks remain
applicable: the accepted production source and app are unchanged. Its earlier
pilot-reader and documentation results are superseded by the repair run.

The repair run's `worker-wait-review/archives/` contains identified copies of
the pilot, four candidate comparisons, the HOST-01 null comparison, final SCAN
unit/mutation and named verification, and the former complementary footprint
run. `worker-wait-review/archive-index.json` records original run IDs, original
paths, every archived file's hash, and archive hashes. The former footprint run includes
the still-needed held-phase, aftermath, response-memory and failed native-pause
evidence with their existing identity indexes. These are historical copies,
not relocated process or resource ownership. They do not add passing cases to
the repair run; the named selection retains its recorded native-pause failure.

All nine archives were verified file by file against their originals. All six
timestamp datasets were also replayed from their archived regular files with
the same calibration, accepted-trial counts and response results. The index
SHA-256 is `dcc7fa9a7d673e4bd34e3689994dbdb7ad4dec25892949a9fe504abeb91e5e6f`;
`reanalysis.json` SHA-256 is
`5af9bca6263d4d74219a183f91d2077c61ba3099eb10f19ba4bddeb7ba5d0e6f`.

Only the current default battery and this complementary run have non-release
pins. After archive verification and replay, the ordinary pruner removed 63
completed unretained runs with no deletion failures. Release-managed evidence,
the release-rotation directory and other unmanaged output retain their existing
protection. The preview and apply receipts are attached under
`worker-wait-review/pruning/`. Older iteration paths named in acceptance records
are historical identities; the archive index identifies the copies still retained.
