# Contract sources

The `*.surface.md` files form the authoring tree for the public contract.
Each file owns a surface; nested headings own its subjects, definitions,
fields, rules, conditions, effects, examples and support. Structured facts
sit beside the prose in `contract` fences.

`tree.py` parses the tree through the repository Markdown reader and derives
the document, field entries, applicability, findings and known-gap views.
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
`source`, `check` when read and `pins`. Check-read and executed owners also
state `context` and `limits`. Source-read owners state either whenever a
specific circumstance or support limitation is needed to understand their
assertion; those optional keys can omit the generic source-inspection meaning
already supplied by the grade. Preserve specific native, constructed-input,
shortened-budget, missing-assertion and retention limits. Citations use
the shared `path`, `symbol` and check `form` vocabulary. An owner's
`scope: "subtree"` supports its parent's descendants; the default `self`
supports its parent. Execution credit also names `run` and
`source_snapshot` or `build`; release credit names `release` and `case`
as `suite/case`.

The rendered contract keeps each owner's grade, scope, assertion, context and
limits beside its claim. Its Evidence details link leads to source and check
citations and execution provenance in Evidence support; each entry links back
to that owner's local support paragraph. Both views come from the same owner
record, including owners attached to compact table rows.

A rule or example has graded support or an explicit evidence gap. Gap
`kind` is `behavior`, `evidence` or `meaning`; its prose is public.
An evidence gap can explicitly cover a subtree. Metadata stays separate
from stamped public content, while public gaps, definitions, examples,
field meanings and relationship facts enter the public snapshot.

An example can take its request from code. `document` cites, by `path` and
`symbol`, one Rust constant spelled `const NAME: &str = r#"..."#;`. The reader
accepts that one spelling and exactly one definition of the symbol. The raw
string must hold a JSON object whose members are `PWRunnerRunSpec` fields,
without `contract`, `_test_overrides` or a controller selection key from
`runner_select.rs`; deeper validity belongs to host admission. The renderer
prints the document after the example's prose with `contract` shown as
`<reported-contract>`. The extracted document enters the public snapshot in
place of its citation, and the cited file is a generator input.

A `member` path of keys and indices, such as `["probe_plan", 0]`, selects one
object inside that request. The whole constant is checked first. The selected
object's members must then be fields of the record its subject describes, and
it is rendered as it stands, without the identity placeholder.

The renderer joins field meanings to public JSON types and presence in
record-local lists. A bare type requires its key; `T?` omits an absent field,
while `T ∪ null` keeps its key and represents absence as null. These signatures
apply to the entire field, including a collection; input and serialization
exceptions remain explicit. The public snapshot retains its full type and
presence descriptions independently of this display notation.

Expressions use the existing checked function names with their complete
operands, grouping and lists. The generated reading key defines every form,
including quantifier scope, effect operands and ordering. Full paths remain
visible. The renderer compacts condition/effect/outcome siblings into tables and derives
applicability, controller-finding and known-gap views. A subordinate row
follows its parent row in the same table and carries the parent's title.
The controller index selects checks whose `who` references
`identity.definitions.controller`, and retains exact literal `"controller"`
indexing for existing fixtures. It names the record members read by each
check's conditions, applicability, binding domains and association selectors.
Its consequence column links each consequence with its local entry, trigger or
case position and the targets it sets, withholds, retains, prevents or
performs. Operand paths, assigned values, free effects and consequence prose
remain at the linked rule and rows. The entry point fills
the surface-table marker after the opening identity material. Statistics
report rendered lines and words, table content, authored prose, field
meanings and free-text relationships separately. Field-entry and rule-table
counts are distinct; Markdown word counts include list/table scaffolding.

## Quantified relationships and decision cases

`each: ["p"]` gives a rule universal scope over an existing `bind.p` domain.
That scope applies to child obligations. A child may add further indices;
outer indices remain in scope and cannot be repeated. List order supplies the
outer-to-inner order, so a nested binding domain can use preceding indices.
A binding and its `match` restriction still establish no cardinality by themselves.

`matches(q)` counts candidates in `bind.q` satisfying its `match.q` restriction
in the current outer scope. It requires a selector. `sum_over(p, expression)`
sums a numeric expression over that binding's domain, restricted by `match.p`
when present; it supplies zero for an empty candidate set. Aggregates introduce
their own bound index. A candidate's domain, selector and sum term may refer to
outer quantified indices; a nested aggregate introduces a further index.
An index already fixed by `each` cannot be quantified again by an aggregate.
Within a quantified rule and its descendants, every index used by a condition or
effect must be in the explicit `each` scope or a containing aggregate. A count
such as `matches(q) == 1` does not bind `q` for a later expression. Binding and
selector declarations remain parameterized; their references are checked in the
quantified scope that consumes them. Existing rules without `each` retain their
symbolic binding interpretation until they acquire explicit quantification.
These facts describe requirements and are never executed against records.

```contract
bind.p: request.phases
bind.q: request.phases
match.q: request.phases[q].phase_id == request.phases[p].phase_id
each: ["p"]
test: matches(q) == 1
```

`is_variant(value, "probe")` is a Boolean predicate over a declared variant;
`variant(value, "probe")` projects that declared alternative. Both validate the
operand's imported type and alternative label. The authored condition supplies
the case guard; the model performs no general implication or exhaustiveness
proof. Optional presence likewise belongs in authored applicability.

`utf8_length(text)` counts the decoded text's UTF-8 bytes. `contains(text,
fragment)` states a text-substring condition, including an embedded-NUL test.
`byte_length(bytes)` counts a typed byte payload: for a Data field projected as
base64 or hex, that is the decoded payload length. The imported projection
remains displayed in the field's public type. Text and Data operands are distinct;
encoded character width and decoded byte extent therefore use distinct facts.
`set_value(record.items, [])` takes its empty array type from the declared list
target. Nonempty values retain their normal element-type checks.

`limit("probe_steps")` reads the owned integer value from `docs/limits.json`.
Its literal ID and numeric type are checked. Rendering supplies the current value
and unit; public content carries the referenced value, unit, counting rule,
consequence and control alongside its identity. Shared references carry those
same dependencies. Source/check metadata remains outside the public digest.
Authors pair the limit with the matching measured quantity; this adds no unit
algebra or record evaluation. Unknown IDs and noninteger values refuse.

`perform(ref("refusals.request.consequence"), request)` states that the named
action applies to that explicit request scope, including its conditions and
triggered consequences under its declared applicability. The target must be
an action with a structured or retained consequence, and the scope must be a
record, event or collection. It shares the action's existing facts and public
dependencies; it neither evaluates the action nor binds new formal parameters.
A Boolean `requires` reference continues to name a condition or check.

`selection: "first_match"` on a rule selects its first satisfied direct
`outcome` child in heading order. Each case supplies Boolean `test` and typed
`effects`; it may also state `uses`, `object`, `value` and prose. The rule owns
shared context, bindings and applicability. Cases render as ordered condition
and consequence rows. A literal `test: True` fallback belongs last. Cases can
omit a fallback when the authored rule defines only conditional selection.
The canonical public payload records derived `case_order`, so moving a case
changes public content even though canonical node IDs remain sorted.

## Reasons for retained free relationships

Each remaining `free.*` fact has an authoring reason under `retained_free`.
The map keys are exactly the local free relationship kinds; reasons are local
and do not inherit. Each entry contains `kind` and a specific `reason`:
`native_protocol`, `serialized_grammar`, `raw_admission`,
`environment_observation` or `pending_decision`. The last kind additionally
names a public behavior or meaning `gap` by its full node identifier.

```contract
free.effect: Close collection before releasing the waiting worker.
retained_free: {"effect":{"kind":"native_protocol","reason":"This clause specifies the collector and release-store sequence across the live process boundary."}}
```

Strict checking requires exact reason coverage and rejects stale entries after
a relationship becomes structured. Preview permits absent reasons while a
surface is being converted; any supplied map is checked completely. Public free
prose and gaps remain stamped. Editorial reasons stay outside the readable
contract and public digest; statistics report their counts by reason kind.
Released v1 snapshots retain their canonical content and use the existing
snapshot reader independently of current authoring syntax.


The readable rule keeps its complete effective context and applicability.
The final applicability view lists rule links under each set of acting
components; the conditions stay beside the obligations they qualify. Support grades are defined
once, each support paragraph identifies its subject and scope, and citations
group source paths while retaining the named symbols. Owner-only editorial
changes and renderer layout leave the canonical public payload unchanged.
Context facts and component definitions remain public content and affect the
public payload when edited.

Context identifies the applicable operation at that node. `entry` names an
invocation or receiving protocol boundary, such as `cli_run`, `runner_verify`,
`xpc_execute` or `worker_action`; `where` names the precise operation there.
`report` names the produced or consumed artifact. Use actual request/report
operands for form conditions. A producer's assembly rule applies before the
report writer selects its fallback; a retained-report reader states its own
marker and form conditions. Field subjects shared by several producers receive
local context only when that ownership applies to the whole subject.
