# Working in `docs/`

Read the [repository documentation index](../README.md#documentation) for the
documents and their audiences. These rules supplement the
[root guidance](../AGENTS.md#documentation).

## Editing developer statements and reading paths

Author public meanings, conditions, examples and support in the
[contract surface tree](contract/README.md). [REQUEST](REQUEST.md) presents
declarations and admission, [RESPONSE](RESPONSE.md) presents returned evidence,
and [ARCHITECTURE](ARCHITECTURE.md) states the named cross-process protocols.
[CONTRACT](CONTRACT.md) retains identity, shared definitions, notation, history,
support details and trace indexes. The rendered location does not determine
whether a statement is public.

Edit [presentation.json](contract/presentation.json) to route whole subjects
and associate tour sections with commitments. Placement metadata supplies no
second public meaning or coverage claim. Keep inherited conditions, first-match
order and owner scope with the statement; a subject that needs separate homes
requires an authored-tree change before it can be routed separately.

Run `tests/lib/python.sh docs/generate_contract_stamps.py` after changing the
tree or map. Edit teaching prose outside generated regions; the generator owns
the statement and commitment-list regions, trace views, snapshot and free-text
counts. Stamp tables occur only in CONTRACT and the user guide. Generation updates both stamp tables. Use
`--check --require-history` when verifying historical derivation with annotated
release tags; a history-free check validates current outputs and table agreement
without establishing their historical derivation. Follow
[test guidance](../tests/AGENTS.md) for the integrated verification selected by
the changed boundary.

Scalar limit spans inside generated contract regions are rendered copies.
Change their authored surface inputs through the limits generator, then
regenerate the contract. The shared span reader excludes generated regions
from its authored-span pass, preserving each generator's ownership.

## Editing limits and the published guide

Edit [limits.json](limits.json) for limit records, then run
`tests/lib/python.sh docs/generate_limits.py`. The generator renders the
technical tables, comparison matrix and authored limit spans. The standalone
[guide](PolicyWitness.md) contains worked cases, internal links and the
generated public stamp table. Edit its prose directly. Keep technical
references and supporting citations in the developer documentation.
Run the generator with `--check` and use the `source_drift` suite for the
documentation checks. [Limit verification](../tests/AGENTS.md#verify-a-limit-change)

## Editing the guide's worked cases

A worked case in [the guide](PolicyWitness.md) must run with the
shipped app. Start from what `example` or `test-input` prints, change named
fields with `/usr/bin/jq`, and state relationships among the reader's runs
rather than values from a maintainer's trial. Give exact values only where the
reader chose them. A passage that cannot meet this states current behavior
without narrating a trial. Keep the [case table](guide/README.md#worked-cases)
current with each case's inputs, edits, fields read and claim. Before
publication, set `PW` to the staged app and run every block except the
external-runner installation in order in one zsh session. Compare each
output with the table.

## Editing footprint content

Edit [footprint.json](footprint.json), then run
`tests/lib/python.sh docs/generate_footprint.py` from the repository root.
Keep its reading guide outside the generated regions; quantities belong in
manifest rows or authored `footprint.<row>.<field>` spans. Do not add literal
size/time prose to the prose baseline.
When a footprint resource uses an existing LIMITS capacity or budget, reference
that limit through the row's `quantity.limit` instead of repeating its value.
Keep allocation counts, derived storage geometry, backing identity and resource
lifetimes in FOOTPRINT; the capacity's boundary and consequence belong in LIMITS.
Each check's `pins` phrase identifies its assertion scope; receipt validation
is distinct from a fixed value assertion. Measured, logical and source-supported
claims keep their stated units, conditions and intervals.
The document's provenance section names the run behind its measured rows;
to change a measured row, rerun its case, transcribe the new receipt and
update that section, rather than editing numbers in place. A release's
acceptance battery runs every measurement case; the
[release procedure](SIGNING.md#release-procedure) transcribes all measured rows
from its archive during preparation of the next release, before committing and
tagging. Name the source archive and acceptance/battery identities; preflight
checks their freshness, not the numerical transcription. No post-tag footprint
commit is required.

Run the generator with `--check` and the `source_drift` suite through the
dispatcher after edits. Review shared backing versus views and distinguish
erasure, native release, unmapping, exit and reap. An unknown observation
never establishes absence.
