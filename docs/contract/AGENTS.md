# Working on contract sources

Read [the directory reference](README.md) and [documentation guidance](../AGENTS.md).

Author public meanings in the surface tree. Identify the acting component,
boundary, applicability and consequences. Keep production rules separate from
the checks a recipient performs on a carried record. State the observation
supporting a value beside its meaning, including a successful value.

Use heading nesting for subordinate relationships and references for shared
definitions. Structured facts must feed a check or a derived view, or replace
prose. Mark a relationship as free text until it has an expression with
resolved operands. Public gaps identify current behavior under review,
unresolved meanings or limits in supporting evidence.

Read an owner's source and check before crediting it. State the assertion,
execution context and limits. Execution credit identifies the run and the
source/build exercised; release credit identifies the acceptance case.
Keep evidence metadata separate from stamped public meanings. Preserve useful
examples with their support or an explicit evidence gap.

Edit generator inputs and regenerate through the entry point. Review field
type and presence joins against their declarations, particularly custom
serialization, variants and conditional omission. A shape agreement supplies
no behavioral evidence. Preserve released snapshots and the legacy reader;
authoring changes must leave release history readable.

Run verification through `tests/run.sh`; follow [test guidance](../../tests/AGENTS.md)
for selection, evidence and output ownership. Shared build/test execution uses
one checkout lock.
