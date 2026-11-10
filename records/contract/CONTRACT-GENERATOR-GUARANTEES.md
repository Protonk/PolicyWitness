# Contract generator guarantees

Stage-one acceptance controls for `docs/CONTRACT-STAGING-PLAN.md`. Each row
states a mutation that must refuse, or a pair whose distinction must survive.
This is the check design; an implementation or execution credit is recorded
only when its named control exists and has run. No product validity decision
belongs to this generator.

## Authoring tree and expressions

| ID | Control and required result |
| --- | --- |
| T01 | Duplicate full node ID, a skipped heading level, unknown node type, or illegal parent/child relation refuses with source location. |
| T02 | A heading inside an example's code fence remains example text. The repository Markdown reader determines headings and fences. |
| T03 | Unknown or duplicate structured keys and misplaced structured fences refuse; unparsed text cannot silently become a structured fact. |
| T04 | A cross-node reference resolves to an existing node of an appropriate kind. Removing the target refuses. |
| T05 | Object references resolve through imported record fields and collection bindings. A misspelled field, scalar indexed as a collection, unbound index, or invalid join refuses. |
| T06 | Presence, comparisons, conjunction, disjunction, negation and conditional requirements parse into distinct expressions. Unsupported syntax, calls and operators refuse without evaluating input. |
| T07 | Shared component and boundary context is rendered at the supported rule. Child applicability narrows inherited entry paths, recipients and report kinds; widening refuses. Parent and child conditions are conjoined. |
| T08 | A direct host recipient never acquires a controller obligation through an inherited default. The spike's direct/controller cases derive different applicability rows. |
| T09 | Check-order and refusal-precedence references are explicit, resolve across surfaces and refuse cycles. Nesting and prerequisite order cannot manufacture precedence. |
| T10 | A value set declares admitted openness and whether its displayed values are exhaustive. An open admitted vocabulary with an illustrative list retains both facts. |
| T11 | Effects identify affected actions or records and distinguish retained observations from supported assessments. Unknown effect verbs or unresolved targets refuse. |
| T12 | Free-text conditions, dependencies and effects are explicitly counted by kind. Growing any count above its baseline refuses; reducing it passes. A rewording preserves the count. |

## Fields, owners and public rendering

| ID | Control and required result |
| --- | --- |
| P01 | Every imported public field has a field node carrying meaning; removing one or adding an unknown field refuses. Type and presence rows are joined from their owning definitions. |
| P02 | A rule lacks its responsible component, boundary, applicability or obligation: refuse. A rule or example lacks graded support and an explicit evidence limitation: refuse. |
| P03 | An owner names source and check with assertion scope, context, limits and grade. Missing files, undefined symbols and an invalid check form refuse through shared citation checks. |
| P04 | An execution credit additionally identifies its run and exercised source/build. A release credit identifies its acceptance case. Source reading cannot render as execution credit. |
| P05 | A field meaning, obligation, example, public limit or known gap changes the owning public digest. Changing only an owner's citation or grade leaves that digest unchanged while still checking metadata. |
| P06 | Referenced shared public definitions enter every incorporating surface's digest. Editing one changes those dependent stamps without copying its prose into each source. |
| P07 | Editing a guide explanation leaves contract digests unchanged. No guide region participates in the new surface definitions. |
| P08 | Field tables, applicability rows, controller-finding rows and known-gap index derive from the same nodes. Removing an applicable node changes its derived view. |
| P09 | Re-rendering is deterministic and `--check` refuses a stale generated document or stamp table. Check mode writes nothing. |
| P10 | Generated contract prose is enclosed in a recognized generated region. Authored source duration/size references resolve through limits; a literal site is not hidden by the rendered document's generated status. |
| P11 | Size reporting distinguishes total lines/words, generated field/value rows and authored definitions/rules/gaps/examples. Tables count one physical line per row. |

## Release history and integration

| ID | Control and required result |
| --- | --- |
| H01 | Read `v0.3.6` with that tree's own surface manifest, normative regions and canonical shape goldens. A missing required input refuses; the release cannot be skipped. |
| H02 | A surface present at `v0.3.6` and absent from the new tree keeps a removal row through later releases. Reintroducing it changes its stamp and clears removal. |
| H03 | Moving a carried surface from the old representation to the tree marks it changed even if the prose expresses the same behavior. The release notes separately classify presentation and behavior. |
| H04 | The table prepared with `--release v0.3.7` equals ordinary derivation after committing and annotating that tag. Repeat for a changed `v0.3.8` tree. |
| H05 | Regeneration, including `--release`, refuses before writing when existing released stamps depend on unavailable history. Fixtures needing a first release start without inherited release stamps. |
| H06 | An ordinary history-free check verifies current inputs and agreement of both tables, returns its existing narrower-success result and explicitly reports its limit. `--require-history` refuses. |
| H07 | A checkout holding older tags but missing an intermediate release named by its tables refuses full verification. Partial available history cannot silently erase the missing version. |
| H08 | A later authoring-layout change retains the ability to derive the earlier layout. An unknown released layout refuses instead of being skipped or read under current assumptions. |
| H09 | A public shape change moves its owning surface. Wire field tags, native widths and projection rules move `wire`; reservation allowances move their declared transport/installation owners. |
| H10 | Build, release preflight, fixture discovery and opt-in build-refusal controls consume the same entry-point interface and complete input inventory. Relocation controls carry the tree, reader versions and cited inputs. |
| H11 | Every mutation control confirms that its mutation changed its intended input, then observes refusal. Removing an old marker cannot turn a mutation into a passing no-op. |
| H12 | Strict preflight compares ratchets with the preceding release. New rendered/source prose must not be accepted by adding a baseline exemption. |

## Evidence and implementation status

Design informed by the staging plan; the current stamp generator's complete
history/render/check paths; its source-drift controls; `generator_common.py`
citation and authored-region checks; `markdown_reader.py`; and the existing
porcelain record definitions. These are first-hand source/check reads by the
executor. The authoring spike and migration inventory supply the remaining
implementation choices. No row above has execution credit yet.
