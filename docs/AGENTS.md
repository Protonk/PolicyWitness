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
The historical archive reference in QUESTIONS is an explicit external-link
exception; the guide must remain usable without that destination.
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
