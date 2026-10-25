# Change-verification guide revamp plan

## Purpose and result

Rename `tests/OPT_IN_TESTS.md` to `tests/CHANGE-VERIFICATION.md`, titled
**Verification for changes and investigations**. Keep its substantive entries
together while reframing the document around a practical question: given a
change or an investigative question, which controls are relevant, under what
conditions, and what would their results establish?

The current document combines selection instructions, a non-default-case
registry, change-specific verification duties, execution conditions and detailed
test descriptions. Selection already belongs to [catalog.json](catalog.json)
and [the dispatcher](lib/test_cli.py); the
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
| What makes a test opt-in | Remove the general classification policy. Retain concrete costs and operating constraints in their applicable entries. |
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

The maintenance section should explain that an entry earns its place by
clarifying applicability, interpretation or consequential operating conditions.
Use the existing case identifiers and links to owning suite accounts. Avoid a
mandatory field template or a requirement to register every non-default case a
second time. Keep detailed assertions and fixture descriptions with their suites
as [the test guidance](AGENTS.md#add-or-change-tests) already requires.

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

Search tracked sources for the old filename, its relevant anchors and prose
such as "opt-in registry". Update current navigation and nearby descriptions
to name change-specific verification or the applicable control. Known callers
include:

- `tests/README.md` and `tests/AGENTS.md`.
- `runner/AGENTS.md`, `controller/AGENTS.md` and the root ordering guidance.
- `docs/DEPENDENCIES.md` and the authored barrier account in
  `docs/ARCHITECTURE.md`.
- The `runner_exec_inheritance`, `witness_contract`, `preflight` and `opt_in`
  suite READMEs.
- Working plans and reports containing navigational links to preserved entries.

In `tests/AGENTS.md`, replace the instruction to maintain an opt-in registry
with maintaining applicable change-verification guidance. Preserve the existing
order-barrier requirement and the force of other change-specific controls.

The harness account should continue to explain the real default/non-default
distinction and `opt_in` group. Its suite-map row can describe that group as
the selection of non-default cases and link to the harness selection account;
the new guide must not be presented as its complete membership registry.
Update incidental "opt-in" wording in touched navigation where it obscures
the new purpose. A repository-wide terminology purge is unnecessary.

Retarget navigational links in existing plans and reports to the same preserved
entry when their meaning is unchanged. Leave quoted text, revision-specific
claims, findings and literal historical path references intact. Inspect these
uses individually rather than globally replacing the old filename. Apply the
same distinction to this plan's references when implementing it.

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
section hierarchy and the destinations of any shortened text. Mechanical link
checks cannot establish that this meaning survived.

Use [the Markdown reader](../docs/markdown_reader.py) to check local files and
heading anchors in the new guide and every changed document. The existing
generator link scan does not cover all test guides, suite READMEs, plans and
records, so include those changed files explicitly. Search remaining old-path
references and account for deliberate historical mentions; current navigation
must resolve. Check `git diff --check`.

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

The work is complete when the renamed guide explains applicability and evidence
without organizing itself as an opt-in registry; substantive entries and
verification obligations survive; the two obsolete general policies are gone;
current links and guidance agree; and the unchanged selection plus documentation
checks pass. Commit the guide and its navigation changes together, recording the
tested source, commands, run location and any unresolved editorial questions in
the completion account. Do not claim those questions were settled by a passing
mechanical check.

Implementation is limited to this bounded documentation change. Preparing and
committing the plan does not itself rename the guide or change test behavior.
