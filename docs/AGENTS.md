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
counts. Stamp tables occur only in CONTRACT and the user guide. Development generation
updates CONTRACT while checking the guide against its frozen `3d3f8e65` bytes. Use
`--check --require-history` when verifying historical derivation with annotated
release tags; a history-free check validates current outputs and table agreement
without establishing their historical derivation. Follow
[test guidance](../tests/AGENTS.md) for the integrated verification selected by
the changed boundary.

Scalar limit spans inside generated contract regions are rendered copies.
Change their authored surface inputs through the limits generator, then
regenerate the contract. The shared span reader excludes generated regions
from its authored-span pass, preserving each generator's ownership.

## Editing limits and shared guide content

Edit [limits.json](limits.json) for limit records, then run
`tests/lib/python.sh docs/generate_limits.py` from the repository root. Edit shared limit
explanations in [LIMITS.md](LIMITS.md) and shared questions in
[QUESTIONS.md](QUESTIONS.md); the generator derives their guide projection for validation. The development
boundary keeps [PolicyWitness.md](PolicyWitness.md) byte-unchanged at
`3d3f8e65`, including copied regions, scalar spans and stamps. Write links in shared questions as
`PolicyWitness.md#anchor` so the copied guide can resolve them internally.
The extension coverage region in [EXTENSIONS.md](EXTENSIONS.md) is also copied
into the guide. Keep the topic introduction inside the shared markers so it
travels with the section. Use level-two headings in the extension source;
the generator nests them under the guide's sandbox-extension heading.
Shared content must stand alone: keep repository citations and implementation
references outside its markers, and maintenance instructions in this file.
Use inline links to guide anchors, not reference definitions, autolinks or
companion files. Write guide links as `PolicyWitness.md#anchor`; the generator
rebases them to internal links. The bare `EXTENSIONS.md` link in QUESTIONS is
also rebased to the copied coverage anchor. Each target anchor must exist in
the guide.
Author scalar spans outside generated regions; the generator renders them
before copying the shared prose.
The guide's recorded comparison scenarios are rows of
[the scenario matrix](../tests/fixtures/comparison/matrix.json), selected by
`GUIDE_SCENARIO_ROWS` in the generator. Change a row's wording in the fixture
and the selection in the generator; the guide's notes on those rows are
authored beside the copy and must still describe them.

Keep shared prose about what a user can observe with the shipped app: reply
fields, refusal names, counts and markers. Put the implementing mechanism under
[Premises behind the interactions](LIMITS.md#premises-behind-the-interactions),
beside its source symbol. Put developer-only remarks about a limit in its
`behavior` field, which only the limits inventory renders.

Run `tests/lib/python.sh docs/generate_limits.py --check` after editing. The
[generator contracts](../tests/suites/source_drift/README.md#generator-contracts)
describe manifest validation, copying, staging and prose checks. For changes to
limits themselves, follow the
[verification guidance](../tests/AGENTS.md#verify-a-limit-change).

Development builds record publication withheld and preserve any frozen guide
copy. `--publication` selects strict guide freshness; staging with
`--publication --stage-guide PATH` checks it without regenerating sources.
Do not use publication generation to refresh the frozen repository guide.
Strict release acceptance, archival and publication require the checkout at
the corresponding annotated tag and compare actual source bytes with its blobs.
Review the copied sections as part of the guide, including their introductions,
heading levels and links. Run `tests/run.sh --suite source_drift` for the
documentation checks. If an edit removes a mutation control's prose target,
update the control to make the same change to the revised document and confirm
that its mutation still changes the input; do not restore reader-facing prose
solely to satisfy a test fixture.

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
