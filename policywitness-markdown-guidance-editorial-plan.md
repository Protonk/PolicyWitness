# Plan a repository-wide Markdown guidance revision

Prepare an implementation plan for an editorial revision to PolicyWitness. Follow the repository's planning guidance in `CONTRIBUTING.md`. **Do not implement the revision yet.** Investigate the affected documents, their sources, and any checks that constrain them; then write a plan that can be executed without rediscovering those dependencies.

## Scope

The scope is **repository-maintained Markdown documentation**: tracked Markdown files and explicitly identified new documentation, including nested and hidden directories, working guidance, user documentation, test documentation, plans, records, and tracked historical narratives. **`CONTRIBUTING.md`** may be read but must not be edited.

Start the inventory with Git's tracked Markdown paths, then inspect nonignored untracked Markdown separately and classify any new documentation before including it. Record the final target list. Account for symlinks such as `CLAUDE.md`, generated Markdown regions, shared text, references between documents, and records whose wording describes past events. Edit each symlink's owning document once without replacing the link.

Exclude execution evidence, scratch copies, build products, packaged documentation, and release archives. Do not edit, regenerate, or delete those artifacts to satisfy the editorial acceptance search. Directory names alone do not establish an exclusion: tracked `.tmp/AGENTS.md`, `dist/AGENTS.md`, and `dist/README.md` remain in scope, as do tracked narratives under `records/archive/`. Tracked generated documentation remains in scope and must be regenerated from its owning inputs.

This brief is an instruction input, outside the editorial target list. In the resulting implementation plan, explicitly mark bounded verbatim “before” excerpts as evidence; only those excerpts are exempt from the final prose search. The rest of that plan is maintained documentation and remains in scope. No blanket exclusion applies to plans, quotations, or historical prose.

## Editorial requirement

Remove the standalone words **agent** and **agents** entirely from in-scope Markdown prose, including instructions, headings, explanatory link text, and historical narrative. Search case-insensitively for singular, plural, possessive, and closely related actor-label usages. In passages that name an actor working on the project, the aim is not to relabel that actor with another category.

In particular:

- Do **not** substitute *contributors*, *maintainers*, *operators*, *developers*, *participants*, *assistants*, *models*, *humans*, or another collective designation wherever the original phrase simply identified who should perform the work.
- Prefer instructions that stand without a named addressee: “When building PolicyWitness, check X”; “Before changing Y, verify Z”; “If the observation is unavailable, record the limitation.” Use direct imperatives and impersonal descriptions of requirements where they read better.
- Don't turn every sentence into “you should.” Rewrite sentences and paragraphs where necessary so the guidance remains natural, precise, and locally intelligible.
- Retain *users* for actual end users of the application. Do not redefine that word to mean people or systems working on the repository.
- Preserve technical distinctions, commands, observed facts, and the evidentiary limits of the documents. Do not confuse an **automation harness** (an actual execution environment) with a generic label for a person or system doing project work.
- Leave required file names, path references, command names, API identifiers, and platform terms intact—for example, `AGENTS.md` and macOS `LaunchAgents`. Those identifiers are not actor labels. Do not rename working-guidance files or disturb their routing.
- Where a historical record describes a particular event, preserve what happened rather than silently inventing a different actor or changing the technical finding. Identify any genuinely difficult cases in the plan and propose specific truthful edits.

Treat this as an editorial rewrite, **not** a global find-and-replace operation. The intended acceptance condition is **no remaining standalone *agent* or *agents* in in-scope Markdown prose**, whether or not the occurrence looks like guidance. Literal technical identifiers are not prose occurrences to be “fixed.”

## Required investigation: the sandboxed automation-harness warnings

Find the repeated warning headed **“Sandboxed automation harnesses”** in `AGENTS.md`, `runner/AGENTS.md`, `tests/AGENTS.md`, and `docs/BUILD.md`. Inspect its explanation in `tests/suites/source_drift/README.md` and the mechanism behind `check_harness_note_agreement` in `tests/suites/source_drift/check.py`, including related controls, fixtures, and documentation or architecture inventories.

**Do not just preserve four identical paragraphs and delete the sentence explaining that repetition.** Decide, as part of the plan, what should become of the duplicated warning and its enforced textual agreement. In particular, evaluate whether local, context-appropriate guidance can preserve the useful troubleshooting instructions without a mechanically synchronized paragraph; if so, plan the necessary changes to the check, tests, fixtures, and references. If any shared invariant should remain, name the actual invariant and how it would be checked without enforcing editorial sameness for its own sake.

Preserve the substantive caution: a restrictive macOS automation sandbox can obstruct XPC lookup, log access, signing/keychain operations, Swift discovery, or signature verification. An environmental explanation must not be assumed from a failure alone; the unchanged operation or artifact should be checked under suitable conditions before drawing that conclusion. Keep the guidance wherever it is operationally useful, but reconsider its presentation and coupling.

## Plan requirements

The plan should:

1. Inventory the affected Markdown files and classify the changes: straightforward prose edits, substantial paragraph rewrites, historical records, generated sections, link/heading dependencies, and mechanically checked text.
2. Give representative **before/after editorial examples** from the actual repository, especially cases that resist a simple deletion. Avoid substituting an actor noun for an actor noun.
3. Identify sources of generated prose and checks that may regenerate or reject the intended edits. Include necessary **non-Markdown** changes only when they support the Markdown revision; do not expand into unrelated refactoring.
4. State a concrete disposition for the repeated sandbox warnings and their agreement check, with the associated test and documentation changes.
5. Provide an execution order that keeps the documentation, generators, cross-references, and checks consistent. Protect unrelated working-tree changes.
6. Define verification: a complete final search against the recorded source-document target list (distinguishing prose, literal identifiers, and explicitly bounded before-excerpt evidence), inspection of the rewritten guidance for clarity and factual fidelity, link/anchor validation where applicable, generator checks, and the relevant `source_drift` controls. Reconcile newly added source documentation before the final search. Do not search disposable output as an acceptance gate or treat a clean word search as sufficient editorial review.
7. Identify risks and unresolved choices that actually affect implementation. Do not turn ordinary wording decisions into requests for approval.

Deliver `MARKDOWN-GUIDANCE-PLAN.md` at the repository root in the repository's customary planning format, with the explicit inventory, specific files, dependencies, proposed edits, and verification steps. Stop after producing the plan; do not edit the target documents in this pass.
