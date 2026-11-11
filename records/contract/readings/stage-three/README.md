# Stage-three isolated readings

The initial, revised and final directories preserve separate frozen inputs and
responses. CONTRACT snapshots and textual deltas use deterministic gzip; their
decoded bytes exactly match the original files. Initial JOURNAL.md and PROMPTED.md
come from the separately frozen copies, with their original aliases verified.
TASK.md and isolation.json preserve the isolation boundary. The revision and final
readings are targeted follow-ups, not replacements for the original reading.

manifest.json records original source, decoded and stored SHA-256 and byte counts.
Original /private/tmp paths are session-local. Evidence adjudications are retained
separately under records/contract/evidence/stage-three; the coordinator owns the
stage-three account and final narrow adjudication. Reading reports retain their
original claims and scope rather than being rewritten by this packaging step.
