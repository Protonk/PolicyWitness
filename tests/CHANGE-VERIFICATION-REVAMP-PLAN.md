# Change-verification guide revamp plan

## Purpose and result

Rename `tests/OPT_IN_TESTS.md` to `tests/CHANGE-VERIFICATION.md`, titled
**Verification for changes and investigations**. Keep its substantive entries
together while reframing the document around a practical question: given a
change or an investigative question, which controls are relevant, under what
conditions, and what would their results establish?

As part of this implementation, put a compact index of established
change-specific verification routes near the front of the guide. Include routes
covering default tests as well as the inherited non-default controls.

The current document combines selection instructions, a non-default-case
registry, change-specific verification duties, execution conditions and detailed
test descriptions. Selection already belongs to [catalog.json](catalog.json)
and [the dispatcher](lib/test_cli.py). The catalog records membership decisions;
contribution guidance explains how to choose that membership. The
[harness README](README.md#how-to-run) owns the public interface. The guide's
continuing value is explaining verification choices that those sources cannot
make for an implementer.

The catalog still distinguishes default and non-default cases and provides the
`opt_in` selection group. This change preserves that behavior. The new guide
will not promise an exhaustive inventory of either group, and inclusion will
not by itself make a control mandatory.

This is a documentation change. Preserve case IDs, commands, prerequisites,
dependencies, default membership, suite ownership, skip contracts, assertions,
artifact paths and the `--suite opt_in` alias. Keep executable files and
`opt_in/` source directories in place. No test retirement, new execution gate,
product change or redistribution of the guide's entries is part of this work.

## Reframe the document

Use this opening, with links to the catalog and harness README:

> This guide connects changes and investigative questions to relevant
> verification controls. It records when a control is needed, what its
> observations establish, and the conditions required to run and interpret it.
> The test catalog owns case membership, prerequisites and dependencies; the
> harness README describes selection and execution.

Follow it with a brief explanation that existing requirements retain their
force, while investigative entries describe useful observations. The guide is
maintained when a verification choice needs explanation; it need not grow with
every new non-default case.

Make these structural changes:

| Current material | Treatment |
| --- | --- |
| Title and introductory selection account | Use the new title and purpose; point to the harness for selection and output conventions. |
| What makes a test opt-in | Replace the category policy with default-membership guidance in `tests/AGENTS.md`, as specified below. Retain concrete costs and operating constraints in their applicable entries. |
| How to run opt-in tests | Reduce to ordinary dispatcher selection, inspection with `--list`, and links to execution guidance. Examples should select a relevant canonical case. |
| Registry (current opt-in tests) | Rename to **Controls and their applicability**. |
| Opt-in reason fields | Rename to **Execution considerations**; separate any embedded change trigger into **When to run**. |
| Adding a new opt-in test | Replace with a short **Maintaining this guide** section at the end. |

Keep the substantive entry headings and their anchors where possible. Several
BYOXPC/native-extension entries currently follow the contribution instructions;
put the maintenance section after all entries so they all belong to the controls
section. Preserve the existing entry order otherwise; no new taxonomy is needed.

Remove the generic instruction to keep specified red tests non-default until
they turn green, and the instruction to move a stabilized test into the smoke
suite. Neither rule is needed to describe current controls. Their removal does
not change any case's membership or expected result.

Carry the useful resource criteria into **Add or change tests** in
`tests/AGENTS.md`, where contributors choose and register default membership.
Cover interactive TTY/PTY or UI needs, network and GUI/other host services,
Developer ID signing or notarization, substantial execution cost, and access to
Unified Logging or other sandbox-sensitive telemetry. Explain how these needs
can justify non-default membership in relation to the ordinary battery's
equipment and operating conditions. Preserve case-specific reasons in the
owning suite account or applicable guide entry, with the actual membership
recorded in the catalog.

These are considerations for a concrete membership decision, not an automatic
rule that every case using a named facility belongs to a separate test class.
Default membership, suite ownership and expected results remain separate
decisions. Removing the old classification section does not retire resource
selection guidance or transfer that policy to the catalog. The two obsolete
rules above are the policies being retired. No current membership changes are
part of this move.

The maintenance section should explain that an entry earns its place by
clarifying applicability, interpretation or consequential operating conditions.
Use the existing case identifiers and links to owning suite accounts. Avoid a
mandatory field template or a requirement to register every non-default case a
second time. Keep detailed assertions and fixture descriptions with their suites
as [the test guidance](AGENTS.md#add-or-change-tests) already requires.

## Index established change-specific routes

After the introduction and before the detailed control entries, add a short
**Find verification for a change** index. Each row names a change or
investigative question and links to its authoritative requirements or detailed
control account. Organize the rows by the changed behavior, regardless of
default membership.

Bound the initial index to these established routes:

| Change | Existing instruction or account to expose |
| --- | --- |
| Admission or validator receivers | [Integrated verification guidance](AGENTS.md#choose-the-most-integrated-test-that-can-establish-the-behavior), including its boundary and reader checks. |
| Limits | [Limit-change verification](AGENTS.md#verify-a-limit-change) and its linked coverage account. |
| Ordering barriers, worker release or observers | The existing ordering requirement in root/test guidance and the retained order-barrier mutation entry. |
| Worker clock source, timebase or sample validation | The retained native worker clock applicability entry. |
| Exec publication, absence handling or confirmed-reap reconciliation | The retained exec-reader and confirmed-reap mutation entries. |
| BYOXPC selection, installation, registry or cleanup | The applicable retained BYOXPC entries and existing controller test-selection guidance. |

Leave requirements and detailed case lists with their current owners; the index
provides routes to those accounts. Preserve each route's actual trigger,
mandatory or investigative status, and qualifications. A link through to the
existing default-test guidance is sufficient; do not copy its checklists into
new control entries merely to make the index look uniform.

The index does not claim exhaustive coverage or require a new investigation to
map every component or test. If inspecting a route exposes missing or
conflicting requirements, record the specific issue as a follow-up question in
the completion account. Include the settled routes and preserve supported
instructions without inventing or reconciling obligations through an index
label. Creating this bounded index is part of the revamp, not a separate
planning deliverable.

## Preserve meaning while cleaning up entries

Review the entries against the previous document, concentrating on changes in
meaning rather than rewriting all prose. Preserve these distinctions:

- Required change-triggered verification remains required. In particular,
  retain the exec-reader and confirmed-reap mutation triggers, ordering-barrier
  obligations, worker-clock applicability and relevant BYOXPC change triggers.
  Move requirements out of cost descriptions without weakening them.
- Useful investigation remains distinguishable from mandatory acceptance.
  An entry with no established trigger does not acquire an invented obligation
  merely to fill a field.
- Costs and conditions remain concrete: disposable builds, matching signing
  identities, GUI launchd access, toolchain combinations, unified-log access,
  source-app preservation and owned cleanup/recovery.
- Evidence limits remain visible. A challenge may pass by observing a
  counterexample; an inventory has observer limits; a build, equipment or
  transport failure is not successful detection of a mutation. Preserve
  required observations, legitimate unavailable observations and cleanup duties.

Keep substantive entries even where they overlap suite READMEs. Shorten or
correct an entry when inspection establishes a specific duplication, stale
statement or misleading claim. An existing detailed account can be replaced by
a precise link only when the destination retains the needed meaning. There is
no length target or requirement to condense every entry.

Replace obsolete project-stage wording with a supported present-day trigger
where one is already established. For example, the order-barrier entry can
retain its release/barrier and observer-change duties without its old
"Gate 3 acceptance" reference. Do not add change-history notes to the guide.
When intent remains uncertain, preserve the supported existing obligation and
report the specific unresolved point in the completion account; do not silently
strengthen or withdraw it. Continue the independently settled editorial work.

## Repair navigation and guidance

Inventory occurrences of the old filename, its relevant anchors and prose such
as "opt-in registry" throughout tracked sources. Include Markdown links,
plain-text paths, code spans, examples and path strings. Classify each occurrence
by its purpose before editing: current navigation or an operational instruction,
a historical/revision-specific reference, or an intentional rename instruction.
Record the disposition of retained old-path occurrences in the review notes or
completion account. Update current navigation and nearby descriptions to name
change-specific verification or the applicable control. Known callers include:

- `tests/README.md` and `tests/AGENTS.md`.
- `runner/AGENTS.md`, `controller/AGENTS.md` and the root ordering guidance.
- `docs/DEPENDENCIES.md` and the authored barrier account in
  `docs/ARCHITECTURE.md`.
- The `runner_exec_inheritance`, `witness_contract`, `preflight` and `opt_in`
  suite READMEs.
- Working plans and reports containing navigational links or plain-text inputs
  to current or planned work.

In `tests/AGENTS.md`, replace the instruction to maintain an opt-in registry
with maintaining applicable change-verification guidance. Preserve the existing
order-barrier requirement and the force of other change-specific controls.
Add the default-membership guidance specified above alongside catalog
registration, keeping the guide focused on applicability and evidence.

The harness account should continue to explain the real default/non-default
distinction and `opt_in` group. Its suite-map row can describe that group as
the selection of non-default cases and link to the harness selection account;
the new guide must not be presented as its complete membership registry.
Update incidental "opt-in" wording in touched navigation where it obscures
the new purpose. A repository-wide terminology purge is unnecessary.

Retarget current links and operational path references to the new guide or the
same preserved entry. For example, the code-span path in
`tests/suites/source_drift/BINDING-THRU-REPLAY-PLAN.md` names an input to planned
work; update it even though a link checker will not see it. Code-span formatting,
quotation marks, or placement in a plan/report do not make a reference historical.

Preserve genuinely revision-specific claims, quotations, findings and historical
path references where changing the path would misrepresent their subject.
Retarget navigational links in those documents when the same preserved entry
still serves their meaning. Inspect uses individually rather than globally
replacing the filename. Apply the same distinction to this plan: an old path
identifying the source of the rename remains intentional, while an instruction
to consult the current guide must point to its new location.

Keep one maintained guide at the new path. Repair links rather than retaining a
duplicate guide at the old path. Read directory guidance before editing its
files. The current architecture link is outside generated regions; edit that
authored paragraph directly. If inspection finds an affected generated region,
edit its owning input and regenerate with the owning tool. Do not hand-edit
generated copies or expand the work into generator changes without a concrete
need.

## Verification

Before editing, check the working tree and preserve preexisting work. Capture
`tests/run.sh --all --list` and `tests/run.sh --suite opt_in --list` outside
managed run output. Repeat them afterwards and compare case IDs, commands,
membership, prerequisites, dependencies and selection. The catalog and
executable sources should remain unchanged. A difference needs explanation and
resolution, not an assumed consequence of the rename.

Review the document diff entry by entry for preserved triggers, requirement
strength, interpretation limits and operating conditions. Check the final
section hierarchy and the destinations of any shortened text. Confirm that
the resource-based membership considerations have a usable home in
`tests/AGENTS.md`, that the two retired policies were not recreated there, and
that catalog registration is not being presented as membership-selection
guidance. Mechanical link checks cannot establish that this meaning survived.

Trace every initial index row to its destination and review whether the linked
account supports the stated change and requirement strength. Confirm that the
admission/receiver and limit routes expose existing default-test verification,
and that the index preserves the qualifications on its other routes. Record any
unsettled requirement question separately from successful navigation checks.

Use [the Markdown reader](../docs/markdown_reader.py) to check local files and
heading anchors in the new guide and every changed document. The existing
generator link scan does not cover all test guides, suite READMEs, plans and
records, so include those changed files explicitly. Repeat the textual occurrence
search independently of the link check. Every remaining old-path occurrence
must be accounted for as historical/revision-specific or intentional rename
text; no active navigation, planned-work input or operating instruction may
point at the removed file, including in plain text or code spans. Check
`git diff --check`.

Run `tests/lib/python.sh docs/generate_limits.py --check` as required by the
documentation guidance. Inspect this selection with `--list`, then execute it
through the dispatcher using a fresh output directory:

```sh
PW_TEST_OUT_DIR=tests/out/runs/change-verification-revamp-01 tests/run.sh \
  --case source_drift/runner_source_manifests_agree \
  --case source_drift/generator_contract
```

These cases cover registry/guidance agreement and generator, prose and routing
contracts. Honor their equipment requirements and the documented sandbox retry
procedure. If generator inputs actually change, also run their owning
documentation case, such as `source_drift/architecture_documentation`.
No native mutation, BYOXPC, signing or full application battery is needed for
the planned documentation-only delta. Do not execute case scripts directly.

## Completion

The guide opens with a compact index of established change-specific
verification routes, covering both default and non-default controls. Each entry
names the relevant change or investigative question and links to its
authoritative requirements or detailed control account. The index preserves
existing obligations and makes no claim to exhaustive coverage.

The work is complete when the renamed guide explains applicability and evidence
without organizing itself as an opt-in registry; substantive entries and
verification obligations survive; the two obsolete general policies are gone;
resource-based membership guidance remains available; current links and
operational path references resolve; and the unchanged selection plus
documentation checks pass. Commit the guide and its navigation changes together,
recording the tested source, commands, run location and any unresolved editorial
questions in the completion account. Do not claim those questions were settled
by a passing mechanical check.

Implementation is limited to this bounded documentation change. Preparing and
committing the plan does not itself rename the guide or change test behavior.
