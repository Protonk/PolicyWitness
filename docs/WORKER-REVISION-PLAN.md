# Worker tour: explanatory structure and scope

## Implementation and deviations

The [worker tour](WORKER.md) implements the structure and scope below without
material deviations. Its authored overview uses nine conceptual boxes; the
knowledge section distinguishes observation limits, divided responsibilities
and measurement gaps. L sits beside the starting-state account, with its
recorded configuration qualified at each authored use. The detailed generated
inventory is relocated intact, and its receipt, manifest and figure files are
unchanged.

Visual review used the repository's Markdown parser and Mermaid 10.9.3 in a
local Safari preview at a 900-pixel document width. The overview's labels and
arrows are legible, the inventory expands, and navigation to L and the generated
node/edge headings works. No semantic discrepancies requiring separate
investigation were identified. The sections below retain the planning baseline
and acceptance criteria.

## Problem and intended result

[The worker tour](WORKER.md) needs to explain how resources, authority
and observation boundaries make PolicyWitness an experimental instrument.
Readers need an initial model of that instrument before they can use its
detailed resource inventory. The current opening reverses that dependency:
it presents a large capability graph and a particular launch receipt before
the explanatory sections.

The distinction between what the worker cannot establish and what it is
deliberately not responsible for is dispersed. References to launch observation
L can lose their configuration limits when read separately. These problems make
the tour's central explanation harder to acquire and its evidence easier to
overread.

The revised tour should give readers an initial model they can understand
without opening the detailed inventory, explain the worker's knowledge and
responsibility boundaries early, and keep recorded launch observations visibly
bounded. Detailed resource facts and their citations remain available.

## Scope

This plan covers the authored revision of the tour.

The expected implementation changes only authored content and section placement
in `docs/WORKER.md`. The compact overview will be authored Markdown/Mermaid,
with its conceptual groups grounded in existing inventory IDs. It will not
introduce another resource-fact table, a new generated graph, or a claim that
the overview's meaning is mechanically verified.

Keeping the inventory's claims true across future implementation changes is
a distinct maintenance problem. Change-impact tracing, structured fact-level
evidence support, maintenance replay experiments, and mechanisms for tracking
observation applicability belong to that investigation. The editorial revision
can proceed using the existing inventory and checks. Preserve the caveats about
source support and assertion scope.

Also excluded are runtime changes, stronger evidence claims, new native
observations, receipt replacement, build/signing changes, and new contributor
procedures. A runtime discrepancy discovered while editing should be recorded
for separate investigation rather than repaired incidentally in this revision.

## Grounding and implementation constraints

- The implementation account and check selection below were inspected at
  repository revision `001f4eab7f2f0baef2a8f66f58bde9925c728ddc` (2026-10-19).
- [Planning guidance](../CONTRIBUTING.md#planning-a-change) governs this plan:
  resolve consequential choices here and verify the intended reader outcome.
- [The current tour](WORKER.md) supplies the resource and observation
  account; [architecture.json](architecture.json) owns the detailed
  `worker_capabilities` inventory.
- Capability-review procedures live in
  [runner guidance](../runner/AGENTS.md#reviewing-a-new-capability). Preserve
  the tour's link there and its distinction between source review, assertion
  scope and recorded observations; do not restore a contributor-procedure
  section in the tour.
- [generate_architecture.py](generate_architecture.py) owns the marked
  inventory region and its DOT/SVG files. Move the entire region, including
  both markers, without changing its contents. Its current destination and
  figure/table anchors can remain intact; no generator or schema change is
  needed for this plan.
- [L's receipt](worker-launch-observation.json) identifies the observed
  app, sources, platform, specimens, captures and applicability limits. Preserve
  its historical contents. This plan does not credit L as a new observation of
  the current checkout. Its worker identity differs from the current generated
  identity; retain both the recorded identity and the applicability caveat
  instead of substituting the planning baseline.
- [Generator contracts](../tests/suites/source_drift/README.md#generator-contracts)
  explain ownership, link checks and their limits. The shared
  [Markdown reader](markdown_reader.py) supplies parsed headings, links,
  paragraphs and lists to these checks. The Known gap rule in
  [check.py](../tests/suites/source_drift/check.py) requires a final
  `## Known gaps` section indexing the preceding authored, top-level gap
  paragraphs in order, by their containing second-level section.
- Existing incoming links target `#acquisitions-inside-attempts` and
  `#supplied-extension-authority`; the SVG targets the generated node/edge
  headings. Preserve these and `#launch-observation-l`. Preserve
  `#capability-map` for the new introductory overview: runner guidance uses
  this anchor to reach the inventory, so the overview needs a direct inventory
  link.

## Proposed document structure

Keep the title and opening explanation, then arrange the sections as follows:

1. **Capability map:** compact conceptual overview and a link to the detailed
   inventory.
2. **What the worker can establish:** the explicit knowledge/responsibility
   distinction described below.
3. **Reporting apparatus.**
4. **Starting authority and ambient context**, with **Launch observation L**
   as a third-level subsection after the general starting-state account.
5. **Acquisitions inside attempts.**
6. **Supplied extension authority.**
7. **Native observations and publications.**
8. **Changes that change the experiment.**
9. **Detailed capability inventory:** the existing detailed legend, generated
   graph, expandable tables, notes and limitations.
10. **Known gaps**, still last and containing only its index.

The original generated graph remains an available reference illustration near
its tables. Moving it later removes the requirement to decode it before reading
the explanation. Keep the inventory's existing generated headings unchanged.

## Execution

### 1. Establish the overview and move the reference material

Move the complete generated region and its detailed color/edge/table legend to
`Detailed capability inventory`. Put a direct link to that section near the
new overview. Do not hand-edit generated table rows, captions, counts or figure
files while relocating them.

Author a small Mermaid flowchart directly in `WORKER.md`, targeting roughly
seven to nine conceptual boxes and short, meaningful edge labels. This is an
authored abstraction, like the surrounding prose. Use the following grounding
to compress the existing account; the ID lists are executor references, not a
second introductory table to paste into the tour:

| Concept | Existing inventory grounding | Meaning to preserve |
| --- | --- | --- |
| Starting worker context | S7, S16a and the other S16 entries | The process already has credentials, restrictions and runtime state when application occurs. |
| Prepared reporting storage | S1a, S2, S18 | Host and worker views refer to shared storage prepared before apply; the host retains its view for collection. |
| Policy application | S26a, S28 | Compilation and application are distinct; applying the policy is the boundary for later attempts. |
| Acquisitions inside attempts | S29–S36 and N12 | Targets and exec setup resources are acquired under the applied policy. |
| Optional token channel | S8a, S12b, S21, S22 | Supplied bearer authority travels separately from reporting storage. |
| Requested extension action | S37, S32 | Delivery precedes requested consumption; fresh reads acquire a descriptor at each requested action. |
| Evidence assembled outside the worker | X1, X2, X3, X4 | Validator predictions and other external observations are joined outside the worker. |

Make the before-application and under-applied-policy sides explicit in labels
or grouping. Show publication from attempts into the existing reporting
storage and host observation of that storage. Keep validator query collection
and host joining visibly outside the worker; do not imply predictions are
delivered to it. Explain the collection/release hold in a short sentence linked
to the architecture tour rather than reconstructing the full execution sequence.

Do not let role colors imply acquisition time: exec reporting resources are
acquired inside attempts. Do not imply that token delivery consumes the token,
that prepared storage is newly acquired after application, or that a fresh
worker starts without ambient authority. The figure and its nearby prose should
be understandable with the detailed inventory closed.

The overview covers alternative admitted experiments. It must not suggest that
exec and extension actions can be combined in one admitted specimen; the
[extension admission rule](../runner/Sources/PWRunnerCore/ProbeRunner.swift)
refuses that combination.

### 2. State the limits of the worker's knowledge early

Add a short section after the overview distinguishing three cases:

- **Limits of the available observations:** native return values and local
  publications do not establish private kernel extension state, effective
  permissions, revocation, or the cause of a permission-shaped failure.
- **Deliberate division of responsibilities:** the worker performs admitted
  actions and publishes native observations. The validator produces predictions;
  the host owns disposition, collection and comparison; the controller gathers
  log candidates. The worker receives a release ordinal, not the predictions.
- **Currently unmeasured behavior:** absent live measurements, such as a complete
  initial Mach-right census or live signal-mask observation, describe gaps in
  available evidence. Do not describe every unmeasured fact as fundamentally
  unknowable or deliberately excluded from all future investigation.

Include the distinction between a native effect and a published result, using
the existing create-then-kill example or a short forward link. A completed call
can leave an effect even when its unpublished result cannot be decoded.
Additional host/controller observations do not automatically justify causal
attribution or a verdict of prediction/enforcement agreement.

Review `Native observations and publications` for repetition after this move.
Keep its detailed publication, lifetime and ordering explanation, with links to
the owning contracts. Preserve the local caveats beside each resource discussion
and the existing Known gap paragraphs. Keep the starting-state gap under
`Starting authority and ambient context`; making L a third-level subsection
does not change that gap's second-level index target.

### 3. Present L as a bounded recorded example

Move the existing L section beside the starting-authority discussion, retaining
the heading text as `### Launch observation L` so its anchor survives. Lead with
what was observed and its scope; keep the exact app/revision/source identity and
receipt link available after that explanation.

Preserve these qualifications explicitly: two separate workers, empty
allow-default plans, no extension-bearing launch or validator queries, observation
windows selected by existing seams, no live publication-flag reading, and refused
task-port inspection. The captures do not establish a within-process transition,
an empty Mach-right set, or the identity of an unnamed mapping.

Review every authored use of L, including the inventory legend, reporting
apparatus and ambient-context discussion. Each should say it describes the
recorded configurations and link to L when the context is otherwise easy to lose.
Keep a clear distinction between L, source-derived inheritance behavior and the
separate contaminated-worker control.

Retain a concise statement that reuse for another implementation or environment
requires applicability review or another observation. Source/hash equality is
evidence about identity, not proof that all relevant conditions were exercised.
This revision need not assert whether L applies to today's build, introduce an
expiry date, rerun the launch case, or create an applicability-status system.
Its purpose is to make the recorded observation's scope clear wherever it is used.

## Verification and acceptance

### Mechanical checks

From the repository root, inspect and run the following existing selection.
These three cases have no signed-app requirement;
`runner_source_manifests_agree` requires Meson. Use a fresh output
name if the example below already exists, following
[test guidance](../tests/AGENTS.md).

```sh
env -u PYTHONOPTIMIZE python3 -B docs/generate_architecture.py --check
tests/run.sh --case source_drift/architecture_documentation \
  --case source_drift/generator_contract \
  --case source_drift/runner_source_manifests_agree --list
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/worker-tour-editorial-20261019 \
  tests/run.sh --case source_drift/architecture_documentation \
  --case source_drift/generator_contract \
  --case source_drift/runner_source_manifests_agree
git diff --check
```

These checks cover generated-region agreement, citation/link rules and the final
gap index. `architecture_documentation` checks the generated inventory and its
citations, `generator_contract` checks prose/link and ownership contracts, and
`runner_source_manifests_agree` runs the general checker containing the gap-index
rule. The Markdown parser controls have their own `source_drift/markdown_reader`
case; changing only authored prose does not require changing or retesting that
parser separately.

These checks do not verify Mermaid rendering or the explanation's truth and
readability. No new runtime tests, signed build, identity regeneration or live
launch run is required for this authored-document change. Preserve test output
under the managed test directory, not in `.tmp`. Inspect the dispatcher's
per-case sleep records: a failure overlapping system sleep is not product
evidence, and credit requires a run without that overlap, as specified by
[test guidance](../tests/AGENTS.md#choose-and-run-verification).

Compare the relocated generated region with its pre-edit bytes: it should be
identical. The receipt, architecture manifest, DOT/SVG assets and executable
sources should have no diff. If an inventory fact actually needs correction,
use its owning generator in a separately scoped change; do not repair a
generated copy to make this check pass.

### Reader and visual review

Render the Markdown in a Mermaid-capable preview and inspect the overview at
ordinary document width. Confirm labels and arrows are legible, the inventory
opens, and links to L and the generated table headings work. Inspect the final
section order and verify that the large graph no longer interrupts the opening
explanation.

Review the following acceptance questions independently of a passing test run:

| Reader question | Required result |
| --- | --- |
| What exists before policy application, and what is acquired under it? | The overview and opening explanation answer without the inventory. |
| How does reporting remain available while attempted acquisitions face policy? | Prepared shared storage and the host's collection role are clear. |
| Does the worker know the predictions or determine why an operation failed? | Responsibilities and limits prevent either inference. |
| Is a missing signal-mask measurement the same limitation as private extension state that these observations cannot establish? | The knowledge section distinguishes the evidence gaps. |
| Does an observed effect guarantee a published worker result? | The publication distinction answers no and points to its existing control. |
| Does L describe every current worker or one worker before and after apply? | Its recorded configuration and two-worker limitation are explicit. |
| Where do detailed facts and supporting assertions live? | The complete existing inventory remains easy to find. |

The revision is complete when these reader outcomes hold, the targeted checks
pass, and the diff remains within the editorial scope. Reconsider the approach
if the compact figure needs a second detailed inventory to explain itself or if
qualifying L requires a new claim about current runtime behavior. Report any
pre-existing check failure separately; do not expand the plan to unrelated fixes.

The executor's completion report should identify the revised document, summarize
the structural changes, record the targeted check results and visual review,
and identify any semantic discrepancies requiring further investigation.
