# Stage-two evidence

These records retain the scoped source, assertion and artifact reviews used by
`records/contract/STAGE-TWO-DECISIONS.md`. The associated staging plan links
that decision record. `execution-summary.json` distinguishes the failed default
battery from the successful correction and opt-in selection.

`boundaries/` covers P1/P2/P3/P3b/P7; `native/` covers effects, timing,
extensions and override applicability; `readers/` covers P4/P5/P6 and later
outcomes; `mutations/` covers the additional setup, handoff and ordering
controls; `byoxpc/` covers external-runner observations and owned cleanup.
The author of each audit owns its source/artifact inspection. The coordinator
reviewed every report and the changed production code, retained their distinct
evidence scopes, and separately verified the terminal dispatcher summaries.

JSON receipts and the native/mutation reports are compressed with gzip; `manifest.json` records both the
stored and decoded SHA-256. The two reader source-snapshot files remain plain
JSON so the contract's exact reviewed-input hashes resolve directly. The
retained reports are their original frozen bytes; references to sibling JSON
files resolve to the corresponding `.json.gz` files here. Original absolute
`/private/tmp` preparation paths and `tests/out` raw runs are local evidence,
available only in this checkout/session and subject to ordinary retention.
The compressed run summaries and audits preserve the selected conclusions and
artifact hashes; they do not contain every raw observation.

The default run remains failed at 228/229. Its individual passed cases support
only their stated assertions. The fresh 15-case selection passed the entire
corrected runner-unit owner and all 14 required opt-ins. Release acceptance is
recorded separately in the release archive.

The final source-drift selection passed ten offline cases; its retained run
summary is `runs/source-drift.json.gz`. It establishes source/generator
agreement and refusal controls independently of the development app runs.
