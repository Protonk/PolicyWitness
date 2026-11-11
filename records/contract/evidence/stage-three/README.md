# Stage-three evidence package

This package preserves frozen isolated-reading adjudications, source/model reviews,
integration and repair manifests, settled statistics, and six canonical dispatcher
selection summaries. The coordinator owns the stage-three account and acceptance
judgments. Each report retains its original source/execution grade and preparation
status; later successful selections do not rewrite earlier failed selections.

The corresponding frozen reading inputs/responses are under
records/contract/readings/stage-three. Patches are omitted because implementation
history belongs to Git. Original /private/tmp and tests/out paths identify local
preparation/raw evidence and remain subject to ordinary retention. This package
copies no raw logs and changes no retention or resource-cleanup ownership.

JSON manifests and run summaries use deterministic gzip (empty filename, mtime 0).
For exact copies, manifest source_sha256 and decoded_sha256 are identical. For run
summary projections, source_sha256/source_bytes identify the original run.json,
while decoded_sha256/bytes identify the selected summary; stored_sha256/stored_bytes
identify its gzip bytes. Generated README records identify the packaging script.
The package manifests exclude themselves and each area records its own files.

Run projections preserve run identity/terminal/result/completion, complete case
results/counts, harness errors, artifact-integrity value, configuration and Python
identity, selected execution-contract identities plus catalog/reader digests, and
whitelisted invocation/case entries. They omit embedded catalog bodies, plans,
duplicated report objects and raw logs. Original run.json SHA and extraction keys
are retained in each summary. A null artifact_integrity remains null. These source
verification selections establish their selected checks, not native guide behavior
or final release acceptance. The script requires all six run.json files, including
the final-presentation owner, to be terminal before writing any destination.
