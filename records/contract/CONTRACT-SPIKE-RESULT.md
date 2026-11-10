# Contract authoring spike

Stage-one step two of `docs/CONTRACT-STAGING-PLAN.md`, performed on
2026-11-10. The Markdown tree and a small expression grammar can carry the
receipt and termination-gate distinctions. The proposed production form is
the tree below, with compact condition/effect tables in its rendered view.

The experiment is under `/private/tmp/pw-contract-spike.sWz5xn`. Those files
are disposable local evidence, outside the repository and unavailable to a
clone. `spike.py` is the prototype; `*.surface.md` are its sources;
`rendered.md`, `views.json`, `stats.json` and `controls.json` are its outputs.
The prototype is drafting equipment, not a replacement contract or a
production generator. This record carries the decisions needed to reproduce
the useful part without depending on the temporary files.

## Source form

Each surface has one Markdown file. Its root identifies the surface; child
headings have local identifiers. The full identifier follows the heading
path: `profile.receipt.labels.captured`, for example. The repository's
`markdown_reader.py` supplies headings and fenced blocks. A heading inside
an example's code fence remains example text.

````markdown
# Compiled-profile receipts {profile: surface}

```contract
syntax: 1
entry: ["cli", "direct_xpc"]
recipient: ["controller", "xpc_caller", "cli_caller"]
report: ["ordinary", "actor", "preparation_failure", "reporting_failure"]
```

## Receipt {receipt: subject}

```contract
record: "CompiledProfileCapture"
as: "receipt"
bind.a: reply.actors
at: ["reply.compiled_profile", "reply.actors[a].compiled_profile"]
coverage: "complete"
```

### Status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["captured", "unavailable"]
```

`captured` states that the host's capture checks passed. `unavailable`
states that a capture condition failed.
````

The outer example fence above is illustrative; an actual surface starts
with its heading and contains the `contract` fences directly.

The constrained block contains one keyed line per fact. Strings and lists
use JSON syntax; expression keys contain the expression directly. A block
is attached to its immediately preceding heading and precedes that node's
prose. Unknown keys, duplicate keys, multiple blocks and a block placed
after prose refuse. Production diagnostics should include file and line.

The subject imports a record definition and declares the public paths at
which that record occurs. A field's local identifier selects its imported
field. Field prose supplies meaning; type, optionality, omission/null
projection and byte spelling come from the owning record definition.
The spike imports `docs/porcelain.json`, including `json_null`, byte
projections and record-level `conditional_null`. Other record adapters
belong in the same generator: request declarations, envelope definitions
and shape goldens, and registry declarations. They supply record metadata,
not a second authored hierarchy.

`coverage: "complete"` made omitted or extra receipt/gate field nodes a
refusal in the spike. Production coverage must apply to every public field
in the source inventory, rather than depend on an author's opt-in flag.

## Relationships and inheritance

The expression parser uses `ast.parse(..., mode="eval")` followed by a
whitelist. It never evaluates an expression. It accepts object paths,
bound collection indexes, literals, comparisons, membership, conjunction,
disjunction, negation, presence/absence and implication. Calls have fixed
names and arities; arbitrary calls, attributes on arbitrary objects,
comprehensions and executable statements refuse.

Examples exercised by the source:

```text
test: receipt.status in ["captured", "unavailable"]
test: implies(receipt.status == "captured", receipt.producer == "worker" and receipt.capture_stage == "before_apply")
test: implies(receipt.status == "unavailable", absent(receipt.producer) and absent(receipt.capture_stage))
bind.p: reply.phases
bind.s: reply.actors
bind.f: reply.phases
match.s: reply.actors[s].actor_id == reply.phases[p].termination_gate.source_actor_id
match.f: reply.phases[f].phase_id == reply.phases[p].termination_gate.source_final_phase_id
test: reply.phases[f].activation_observation.capture_ordinal < reply.actors[s].owned_reap.capture_ordinal
```

A binding identifies an index domain, and its match selects the named
association within that domain. A missing association remains something
the applicable condition must address. Production should distinguish a
failed lookup from a value comparison and check that reference targets
have appropriate kinds. The prototype checks domain identity and path
resolution; it does not establish existence or uniqueness at runtime.

`who` and `where` inherit and may be explicitly replaced. `entry`,
`recipient` and `report` inherit and may only narrow: a child cannot add a
value its parent excluded. Parent and child `when` expressions conjoin.
Bindings and the subject's record alias are available beneath that subject.
Production should refuse ambiguous rebinding rather than silently replace
a bound domain or record alias.

The two receiver paths stay distinct. Host receipt production names the
controller and direct XPC caller as recipients. The controller's label
check narrows to the CLI entry and CLI recipient, and remains applicable
to a carried receipt in ordinary, actor, preparation-failure and
reporting-failure replies. The gate check separately requires an actor
reply without a reporting-failure record. The derived applicability view
contains those effective scopes.

Conditions nested directly under a rule express its identified
requirements. A dependency on a condition elsewhere uses
`ref("full.condition.id")`. Conditional requirements need an expression:
the gate's successful-outcome conditions appear under
`implies(gate.outcome == "satisfied", ...)`. An unconditional dependency
cannot acquire that restriction from adjacent prose.

Order is explicit. `after` and `precedes` name nodes across surfaces and
form a graph checked for cycles. A failed identity-admission effect
prevents the receipt-label check, establishing refusal precedence in
addition to order. `failure: "first"` records the host capture check's
first-failure selection. Production needs to validate that value and
render its meaning, just as it validates the order references.

An effect has `on: "failure"`, `"success"` or `"always"`; its title does
not supply its trigger. The tested effect vocabulary distinguishes setting
a field, preventing an action within a scope, withholding an assessment,
retaining records and retaining assessments:

```text
on: "failure"
effects: [prevent(ref("actor_evidence.gate.activate"), reply.phases[p]), prevent(ref("actor_evidence.gate.activate"), later(reply.phases, p)), retain_records(reply)]
```

`later(reply.phases, p)` expresses the schedule scope, including phases of
other actors. `retain_records(reply)` and
`retain_assessments(reply.normalized_outcome)` are different effects.
Definitions and effect targets need kind checking in production; a
resolving identifier alone does not establish an appropriate target.

The receipt's `reason` field exercises an open admitted vocabulary with
an illustrative displayed list. The field names the controller-admission
boundary and states that unfamiliar strings are retained as host reasons.
The gate outcome and receipt status exercise closed vocabularies with
exhaustive displayed lists. Openness and list completeness remain separate
facts.

`free.when`, `free.condition`, `free.dependency` and `free.effect` hold
explicit unstructured text. The prototype counts each by kind and rejects
count growth against its baseline. Rewording preserves a count. The
receipt's native capture-input conditions remain free text in this spike
because the prototype imports public records, not native capture/input
events; wrapping those sentences in keys does not claim structured meaning.

## Rendering and evidence

The renderer emits prose, one field row per imported field, effective
rule context, and compact sibling condition/effect rows. The first version
gave every condition and effect a heading; compact rows reduced the same
material from 317 lines to 209. The final explicit identity-refusal effect
brought it to 213 lines. Final production wording should render expressions
as sentences and links where that improves reading; the spike displays
their literal syntax to make the tested relationships inspectable.

A child owner holds `source`, `check`, `grade`, `pins`, `context`, `limits`
and, for execution credit, `run`. Source/check existence and check form are
validated with `generator_common.citation`. The public output shows a short
support grade and assertion scope. Detailed provenance can remain in the
separate evidence view. An evidence gap affecting a commitment is a public
gap node; moving it into owner metadata would remove it from the stamped
public account.

Owner metadata is excluded from the spike's public-content digest. A
metadata-only edit preserves the digest; a field-meaning edit changes it.
The production digest also needs canonical shapes and the closure of
referenced public content. Those additions, released-layout readers and
stamp history are covered by the separate generator-guarantees work.

`derived_views` walks the same nodes to produce effective applicability,
controller checks and their read paths/effects, and the known-gap index.
The spike's read-path collector includes intermediate paths; production
should collapse those without losing named records or effects. Field
tables and derived views do not need separately authored lists.

The spike's small callable interface is:

| Function | Result |
| --- | --- |
| `parse_surface(text, name)` | Ordered nodes with parent/child ownership and path-derived IDs. |
| `validate(nodes)` | Node index and free-text counts, or a refusal. |
| `render(nodes)` | Readable Markdown and the generated table rows. |
| `derived_views(nodes)` | Applicability, controller-finding and known-gap views. |
| `public_digest(nodes)` | Public tree-content digest, excluding owner metadata. |
| `ratchet(counts, baseline)` | Refusal if a free-text count grew. |

## Observed checks and size

Executed authoring-prototype commands:

```sh
tests/lib/python.sh /private/tmp/pw-contract-spike.sWz5xn/spike.py
tests/lib/python.sh /private/tmp/pw-contract-spike.sWz5xn/controls.py
```

The second command completed 36 controls: 11 positive distinctions and 25
expected refusals. These are prototype assertions, not executions of a
repository case or product behavior. The positive controls establish:
fenced example headings stay text; direct-host and controller recipients
stay separate; degraded receipt-label applicability stays broad; inherited
conditions conjoin; metadata and public meaning affect the digest
differently; equal/decreased free-text counts pass; rewording preserves the
count; rendering is deterministic; and views derive from the nodes.

The rejection controls cover duplicate IDs; heading-level and nesting
errors; unknown, duplicate or misplaced facts; missing and unknown fields;
unbound indexes, mismatched domains and scalar indexing; unsupported calls;
unresolved references; widening any applicability axis; order cycles;
missing meanings; an open vocabulary lacking its unfamiliar-value effect;
an effect lacking its trigger; missing source/check citations; execution
credit without a run; unsupported examples; and free-text count growth.

| Quantity | Observed value |
| --- | --- |
| Authored source | 556 lines across four files; two worked surfaces plus identity/refusal scaffolding. |
| Nodes / field nodes | 80 / 22. |
| Rendered document | 213 lines; 2,056 whitespace-delimited words. |
| Generated field, condition and effect tables together | 68 lines; 1,220 words. |
| Authored prose outside fields and owners | 22 physical lines; 526 words. Free-text facts and structured expressions are counted separately from this prose figure. |
| Free-text facts | 13 conditions, 3 applicability items, 3 effects; no free-text dependencies. |

These are measurements of the representative source and scaffolding, not
a whole-contract size forecast. The empty production skeleton supplies the
next size measurement, and complete record coverage supplies the meaningful
projection of field-table size.

Two initial refusals improved the draft: `report.outcome` in the worked
proposal is a conceptual name, while the schema's field is
`normalized_outcome`; and a gate field and action both named `wait`
collided. The prototype uses `reply.normalized_outcome` and
`wait_for_source` for the action. The gate's source requirements were also
changed from an unconditional reference list to an explicit implication
for `satisfied`, keeping structure and prose in agreement.

## Evidence grade and remaining work

First-hand reads covered the staging plan's source/generator and spike
requirements; the full worked gate and receipt sections; `docs/AGENTS.md`
and `records/AGENTS.md`; `markdown_reader.py`; the shared citation checker;
relevant porcelain record definitions and projection generation;
`decodeProfileCapture`; receipt `admission_problem`; the scheduler's
`walkSchedule`, `observeTermination` and cleanup; the gate validator's
initial association checks; the constructed compiled-profile check file;
and the scheduler cleanup-after-timeout fixture. These reads support the
source examples at the stated source/check-read grade.

During the spike, the executor added and executed
`compiled_profile_labels_determine_the_public_admission_outcome`. This
reader inspected the new test's assertions and updated the example's
owner to it. Execution credit remains with the executor's recorded unit
run; the spike does not retain the earlier R-06 evidence gap as a current
claim.

The prototype has exercised the requested authoring distinctions. The
production implementation still needs complete support coverage for every
rule, type-specific fact and reference rules, source-located diagnostics,
the non-porcelain record adapters, public dependency hashing, preserved
release-layout readers and integration with the existing generator entry
point. The stage-one guarantees in
`records/contract/CONTRACT-GENERATOR-GUARANTEES.md` identify those acceptance
controls. No build, repository test battery, commit, tag or release action
was performed by this spike.
