# Working in `docs/`

Read the [repository documentation index](../README.md#documentation) for the
documents and their audiences. These rules supplement the
[root guidance](../AGENTS.md#documentation).

## Editing limits and shared guide content

Edit [limits.json](limits.json) for limit records, then run
`tests/lib/python.sh docs/generate_limits.py` from the repository root. Edit shared limit
explanations in [LIMITS.md](LIMITS.md) and shared questions in
[QUESTIONS.md](QUESTIONS.md); the generator copies both into
[PolicyWitness.md](PolicyWitness.md). Write links in shared questions as
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

When staging the standalone guide, run
`tests/lib/python.sh docs/generate_limits.py --stage-guide dist/PolicyWitness.md`
after regeneration; staging checks freshness and does not regenerate sources.
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
update that section, rather than editing numbers in place.

Run the generator with `--check` and the `source_drift` suite through the
dispatcher after edits. Review shared backing versus views and distinguish
erasure, native release, unmapping, exit and reap. An unknown observation
never establishes absence.
