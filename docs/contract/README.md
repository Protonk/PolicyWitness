# Contract sources

The `*.surface.md` files form the authoring tree for the public contract.
Each file owns a surface; nested headings own its subjects, definitions,
fields, rules, conditions, effects, examples and support. Structured facts
sit beside the prose in `contract` fences.

`tree.py` parses the tree through the repository Markdown reader and derives
the document, field tables, applicability, findings and known-gap views.
`record_definitions.py` imports existing field declarations for the authored
meanings. The identity surface declares public coverage, requiring every
imported record to have one authored subject and every field a meaning.
`runtime.py` assembles the document, snapshot, shape goldens and stamp tables.
`history_v0.py` reads earlier manifest/region release trees with their original
digest framing; `history_v1.py` reads released canonical public snapshots.

The entry point is [generate_contract_stamps.py](../generate_contract_stamps.py).
It generates the [public contract](../CONTRACT.md), the guide's stamp table,
`public.json` and `free_text.json`. The latter records counts by relationship
kind; generation permits reductions and refuses increases. Shape changes use
`--refresh-shapes` and require review. Ordinary generation and explicit release
preparation require the history claimed by the carried tables and snapshot.
An ordinary check without tags verifies current content and table agreement,
and reports that historical stamp derivation remains unverified.

[AGENTS.md](AGENTS.md) gives the authoring and verification rules.

## Authoring a surface

A heading has a title, local identifier and node type. Its full identifier
is its path through the headings: `profile.receipt.labels`, for example.
The root is a `surface`; its `subject` children own `definition`, `field`
and rule nodes. Rules are `acts`, `reports` or `checks`, with subordinate
`condition`, `effect` and `outcome` nodes. An `owner` supplies support;
`gap` and `example` nodes retain their public text.

A `contract` fence immediately after a heading holds one keyed fact per
line. Scalar strings and lists use JSON spelling. Expressions are written
directly. Ordinary prose follows the fence.

````markdown
# Compiled-profile receipts {profile: surface}

```contract
syntax: 1
artifact: "Compiled-profile receipts"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/profile.json"]
checks: ["failure_boundaries"]
```

## Receipt {receipt: subject}

```contract
record: "CompiledProfileCapture"
as: "receipt"
```

### Status {status: field}

`captured` states that the host's capture checks passed.
````

The snippet shows the syntax of one field; a complete record subject
accounts for every field and every referenced record type. Imported field
types and presence come from `record_definitions.py`. For an authored
record absent from those imports, each field supplies `type`, and may
supply `optional`, `json_null` and byte `projection`. Definitions, defaults,
vocabularies and applicability remain in the same tree as their meanings.

Root `part` places the surface in `identity`, `definitions`, `input`,
`delivery`, `report`, `assessment`, `installation` or `version`. A subject
may override `part`, allowing one identity surface to supply the opening
identity, shared definitions and version operation. `goldens` names
canonical shapes; `checks` names catalog suites. Strict validation requires
populated surface contents, shapes and checks. Preview admits the empty
staging skeleton.

## Context and relationships

Rules state `who`, `where`, `entry`, `recipient` and `report`. `who` is a
nonempty literal label or a nonempty list of distinct component-definition
identifiers, such as `who: ["identity.definitions.controller"]`. Referenced
actors render with their definition titles. All current public checks use
references; literal labels remain available for existing sources and fixtures.

Context can be inherited. A child's `who` replaces its inherited actor or
actor list in full. A child may also replace the boundary and narrow the
three applicability lists. Parent and child `when` conditions conjoin.
An inherited `free.when` remains visible until it is expressed.

`bind.p: reply.phases` binds an index to a collection. A `match.p`
expression restricts its association. The rendered rule states each local
binding's domain and association restriction. Match cardinality is a separate
requirement. A record subject can supply `at`, a
list of checked object paths, alongside its `as` alias. The renderer prints
those locations beside the record alias. Expressions support presence,
absence, comparisons, membership, Boolean operators and
`implies(condition, requirement)`. `ref("full.node.id")` identifies another
node. The parser checks types and references and evaluates no condition.

`after` and `precedes` name order relationships; `requires` names
conditions or checks. `uses` names shared public definitions. These lists
contain full node identifiers. Ordering is checked separately from
dependencies. A rule's `failure` can specify `first` or `accumulate`.

Effects state `on: "failure"`, `"success"` or `"always"` and an `effects`
expression. The verbs distinguish `set_value`, `prevent`, `withhold`,
`retain_records`, `retain_assessments` and `emit`. Each names its operands;
`prevent` also names its affected scope. `later(collection, index)` names
later members of an indexed schedule. Conditional requirements use
`implies`; prose beside an unconditional expression cannot narrow it.

Fields can state `vocabulary: "open"` or `"closed"`,
`listed: "exhaustive"` or `"illustrative"`, and their displayed `values`.
An open vocabulary states what unfamiliar values establish in `unknown`.
`required_when` and `present_when` express field applicability; `default`
records an authored default.

An unstructured relationship uses `free.when`, `free.condition`,
`free.dependency` or `free.effect`. The generator counts these by kind.
Their rendered prose remains part of the public commitment.

## Support and rendering

An owner states `grade` (`source_read`, `check_read` or `executed`),
`source`, `check` when read, `pins`, `context` and `limits`. Citations use
the shared `path`, `symbol` and check `form` vocabulary. An owner's
`scope: "subtree"` supports its parent's descendants; the default `self`
supports its parent. Execution credit also names `run` and
`source_snapshot` or `build`; release credit names `release` and `case`
as `suite/case`.

A rule or example has graded support or an explicit evidence gap. Gap
`kind` is `behavior`, `evidence` or `meaning`; its prose is public.
An evidence gap can explicitly cover a subtree. Metadata stays separate
from stamped public content, while public gaps, definitions, examples,
field meanings and relationship facts enter the public snapshot.

The renderer joins field meanings to public JSON types and presence,
compacts condition/effect/outcome siblings into tables, and derives
applicability, controller-finding and known-gap views. The controller index
selects checks whose `who` references `identity.definitions.controller`, and
retains exact literal `"controller"` indexing for existing fixtures. Its
consequence column includes direct structured and free effects, followed by
child effects with their triggers and consequence prose. Structured operands
come from conditions, applicability, binding domains and association selectors;
free-text operands remain in the linked rule. The entry point fills
the surface-table marker after the opening identity material. Statistics
report rendered lines and words, table content, authored prose, field
meanings and free-text relationships separately.
