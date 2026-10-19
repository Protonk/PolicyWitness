# Markdown guidance revision plan

## Intended result and boundary

Revise maintained Markdown to remove the actor labels specified in the
[editorial brief](policywitness-markdown-guidance-editorial-plan.md), using direct
instructions and descriptions of requirements. Preserve commands, technical
identifiers, end-user distinctions, observations and limits on attribution.
Replacing a named addressee with another collective noun does not satisfy this
change.

Replace synchronized sandbox-warning paragraphs with independent guidance
suited to each workflow. Keep a mechanical check for the presence of the
guidance and the root document's diagnostic routes; review the advice's meaning
editorially. Paragraph equality does not establish correctness.

This is an implementation plan. It does not authorize implementing the
[retention proposal](tests/RETENTION-PLAN.md), altering runtime behavior, changing
protocol versions, cleaning evidence, or repackaging releases. The branch-build
investigation below includes focused infrastructure fixes supported by its
findings. Follow the
[planning guidance](CONTRIBUTING.md#planning-a-change) and
[test working rules](tests/AGENTS.md) when executing it.

## Branch workflow and build infrastructure

Carry out this revision on `doc-rework`, an explicit exception to the usual
integration on `main`. The branch starts from `a7cf758`; this plan amendment is
its first commit. Keep implementation and related infrastructure fixes on that
branch so the complete diff and the sequence of decisions can be reviewed
across commits. Preserve the review history rather than squashing or rewriting
it during the work. Integration into `main` follows review of the branch.

Use small, coherent commits: independent prose and heading-link edits; the
coupled warning/checker/control/graph change; any demonstrated build compatibility
fixes with their controls; and final editorial corrections and verification
findings. Keep a heading rename with its incoming links, and keep a changed
checker with its tests, documentation and generated citations. The requirement
for coherent changes does not require the entire revision to be one commit.

Use this branch to establish whether the build infrastructure works away from
`main` or `master`, including under a previously unused branch name. Initial
inspection found that [build.sh](build.sh) derives its stamp from `HEAD`,
`git describe` and commit count, while
[release_preflight.py](tests/lib/release_preflight.py) checks cleanliness, tags
and release ancestry. These paths do not explicitly require a particular branch
name; source inspection alone does not establish that the complete workflow is
independent of the branch name.

1. At the clean branch baseline, record the commit, branch name, describe string,
   toolchain, signing identity and cache state. Run the documented
   `make build IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'` with the
   configured identity, following the [build guide](docs/BUILD.md). Preserve
   the command receipt, observed refusals and resulting source/provenance stamp.
   Inspect the resulting app through the test dispatcher. Select
   `preflight/build_provenance_controls` and `preflight/signed_artifact_controls`
   after checking their equipment with `--list`.
2. Repeat the build at the committed editorial candidate and exercise both
   ordinary cache reuse and `PW_FRESH_BUILD=1`. Verify that the embedded commit,
   describe string, dirty flag and build number identify the branch's tested
   source state. Do not substitute `main`'s tip or a previously built app when
   crediting these results. Keep build/test receipts distinct for each source
   state and configuration.
3. Exercise branch-name variation in a disposable Git fixture using the same
   commit and tags under a conventional branch name and a newly created or
   renamed branch. Hold source, checkout path, toolchain and cache state fixed
   for the comparison. Compare stamp derivation and preflight decisions; if a
   real build fails only on `doc-rework`, use this comparison to isolate the
   relevant operation before changing it. Never rename or reset the shared
   `main` branch to create this control. A second worktree needs its own valid
   build directories; a checkout-path refusal is not a branch-name failure.
4. Inspect release preflight findings separately from development build
   compatibility. An untagged development commit's release refusal is expected;
   `--report` returning zero does not mean release preflight passed. Use local
   fixture tags for tagged controls. Preserve release eligibility, signing,
   provenance and cleanup guarantees; this experiment does not publish, notarize
   or create a release tag in the working repository.
5. Record observed branch assumptions, failures, successful comparisons and
   remaining coverage limits in the branch's verification account. Make focused
   fixes in separate commits, with a reproducing control in the owning build or
   preflight tests. Update `docs/build.json` and regenerate its outputs when
   build behavior changes. Choose additional verification from the changed
   boundary, then rerun the failed operation and its branch-name comparison.
   If no incompatibility is observed, report that result without inventing a
   branch-specific workaround.

The build experiments generate fresh evidence under the existing ownership and
retention rules. They do not expand the editorial target inventory to include
build output or retained test copies. Keep the branch available for review with
the commit range, tested revisions and any unresolved infrastructure findings.

## Source inventory and ownership

The inventory below was taken at `3354935`. Git lists 116 tracked Markdown
paths: 111 canonical targets, four symlink aliases and the excluded
`CONTRIBUTING.md`. This new plan adds one canonical target. The only nonignored
untracked Markdown at inventory time was the editorial brief, which is an
instruction input and remains excluded after it is committed.

Use the explicit 112-path target list in the appendix. At execution start and
before final verification, reconcile it with:

```sh
git ls-files -z --cached -- '*.md'
git ls-files -z --others --exclude-standard -- '*.md'
```

Account for new source documentation explicitly. Do not replace this inventory
with a recursive filesystem Markdown search. Exclude execution evidence,
scratch copies, build products, packaged guides and release archives, including
copies beneath `tests/out/`, `.tmp/`, `builddir/`, `controller/target/` and
distribution bundles. Do not edit, regenerate or delete those artifacts to
make an editorial search pass. Tracked `.tmp/AGENTS.md`, `dist/AGENTS.md` and
`dist/README.md` are source guidance and remain targets. So do tracked
`records/archive/` narratives and committed fixture READMEs.

| Ownership or change class | Files and disposition |
| --- | --- |
| Straightforward prose and heading changes | `AGENTS.md` introduction, documentation paragraph and external-runner heading; `docs/BUILD.md` distribution guidance; filename shorthand in `tests/suites/source_drift/README.md`. |
| Paragraph rewrites | `docs/ARCHITECTURE.md` introduction; `docs/LIMITS.md` editorial explanation; sandbox sections in `AGENTS.md`, `runner/AGENTS.md`, `tests/AGENTS.md` and `docs/BUILD.md`; the corresponding `source_drift` explanation. |
| Heading dependencies | `controller/AGENTS.md` and `tests/AGENTS.md` link to the root external-runner heading. Update both when that heading changes. Preserve all four `Sandboxed automation harnesses` headings. |
| Generated material | `docs/ARCHITECTURE.md` document-graph regions derive from `docs/architecture.json`. Regenerate them and the document graph's DOT/SVG files. Other generated or shared Markdown remains governed by its existing owner. |
| Historical records | All 19 tracked Markdown paths under `records/`, including its guidance and archive, were searched. No applicable actor-label prose was found. Preserve historical findings and technical names; do not invent revisions merely to touch this category. |
| Remaining source documents | All appendix entries remain acceptance targets, even where the initial scan found no prose to change. That includes existing plans, suite and fixture READMEs, and this plan outside its bounded before excerpts. |
| Symlink aliases | `CLAUDE.md` → `AGENTS.md`, `controller/CLAUDE.md` → `controller/AGENTS.md`, `runner/CLAUDE.md` → `runner/AGENTS.md`, `tests/CLAUDE.md` → `tests/AGENTS.md`. Edit the owning files once and preserve the symlinks. |
| Explicit exclusions | `CONTRIBUTING.md` and `policywitness-markdown-guidance-editorial-plan.md`. These are readable inputs, not editorial targets. |

The initial expected Markdown changes are in eight existing files:
`AGENTS.md`, `controller/AGENTS.md`, `runner/AGENTS.md`, `tests/AGENTS.md`,
`docs/ARCHITECTURE.md`, `docs/BUILD.md`, `docs/LIMITS.md` and
`tests/suites/source_drift/README.md`. Reconcile concurrent source additions
without assuming every target requires an edit.

## Editorial decisions and examples

Only the verbatim source excerpts between the paired
`EDITORIAL BEFORE` comments below are exempt from the final prose search.
The labels, proposed wording, inventory and other prose in this plan remain
in scope. Code formatting alone is not an exemption.

### Working instructions and routing

Before, from `AGENTS.md`:

<!-- EDITORIAL BEFORE root-introduction BEGIN -->
```text
This file governs how contributors and agents work here.
```
<!-- EDITORIAL BEFORE root-introduction END -->

After:

> This file sets the working rules for this repository.

Change the external-runner heading to `External runner workflow`. Its fragment
becomes `external-runner-workflow`; update the two incoming links in
`controller/AGENTS.md` and `tests/AGENTS.md`. Other working-guidance filenames
and their routes remain intact.

Before, from `docs/BUILD.md`:

<!-- EDITORIAL BEFORE distribution-guidance BEGIN -->
```text
- **The output directory.** `DIST_DIR`, `dist/` by default; a custom one
  also receives copies of the tracked `dist/` README and AGENTS files. Its
  trust and that of the build directories are in the table.
```
<!-- EDITORIAL BEFORE distribution-guidance END -->

After:

> **The output directory.** `DIST_DIR`, `dist/` by default; a custom one
> also receives copies of the tracked `dist/README.md` and `dist/AGENTS.md`.
> Its trust and that of the build directories are in the table.

Likewise, replace ambiguous filename shorthand in the root documentation
paragraph and the source-drift prose-scan description with explicit
`AGENTS.md` references. These are filenames, not replacement addressees.

### Reading order and explanatory prose

Before, from the opening of `docs/ARCHITECTURE.md`:

<!-- EDITORIAL BEFORE architecture-introduction BEGIN -->
```text
A tour of the internals at the level between the [README](../README.md)'s
Flow paragraph and the directory READMEs: how one run unfolds in time and the
boundaries it crosses. It is for a developer or agent who has read the README
and is about to open a directory. Each section links to the relevant field
reference, contract, module list, test map or build guide.
```
<!-- EDITORIAL BEFORE architecture-introduction END -->

After, with links resolved relative to that document:

> This tour follows one run through the internals and across their boundaries.
> Read it after the README's “The Experiment” section and before the directory
> READMEs. Each section links to the relevant field reference, contract, module
> list, test map or build guide.

Link “The Experiment” to `../README.md#the-experiment`. This also corrects the
stale “Flow paragraph” reference within the paragraph already being rewritten.

Before, from `docs/LIMITS.md`:

<!-- EDITORIAL BEFORE limits-rationale BEGIN -->
```text
Two editorial rules keep the shared section honest for its reader, a user of the
guide. First, shared prose states only what that reader can observe with the
shipped app: a reply field, a refusal's name, a count, a marker. Second, the
mechanism a statement rests on goes under "Premises behind the interactions",
beside the symbol that implements it, so that an agent or a maintainer can
reopen the premise.
```
<!-- EDITORIAL BEFORE limits-rationale END -->

Keep the first rule and its actual end-user distinction. Finish the second:

> Second, the mechanism a statement rests on goes under “Premises behind the
> interactions”, beside the implementing symbol so the premise can be reopened
> and checked.

This paragraph is authored text outside both the shared limits block and the
generated coverage block. It does not require a matching edit in the user guide.

### Historical and technical distinctions

Preserve `LaunchAgent`, `LaunchAgents`, `LaunchDaemons`, filenames such as
`AGENTS.md`, and graph identifiers such as `agents_md`. The observation
“sixteen ContextStoreAgent lines within a second” in
`records/archive/SANDBOX-LOG-ISOLATION-INVESTIGATION.md` names a process and
records a measurement; changing it would damage the evidence.

Search historical narratives as prose, with no blanket historical exemption.
If concurrent edits introduce an actual actor-label passage, rewrite the
sentence around the recorded action while preserving the event and attribution.
A technical substring is not grounds for changing an observed name.

## Independent sandbox guidance

Keep useful troubleshooting close to each workflow. Remove the synchronized
first paragraph and the explanation requiring coordinated edits. Preserve the
existing detailed continuations, integrating them where the new opening would
otherwise repeat them. The following drafts establish the intended content;
they need not share wording.

**Root `AGENTS.md`.**

> A restrictive macOS automation sandbox can obstruct runner XPC lookup,
> unified-log access, signing or keychain access, and Meson's Swift discovery.
> It can also make signature verification fail for unchanged bytes. Inspect the
> diagnostic before attributing a failure. Request escalation and rerun the same
> failing command once outside that sandbox without changing the artifact under
> investigation. Treat a signature failure as environmental only if that
> unsandboxed verification passes; investigate failures that remain.
>
> Follow the runner diagnostics, test execution guidance, or signing and compiler
> discovery guidance for the affected workflow.

Make the final sentence link, within this section, to
`runner/AGENTS.md#sandboxed-automation-harnesses`,
`tests/AGENTS.md#sandboxed-automation-harnesses` and
`docs/BUILD.md#sandboxed-automation-harnesses`.

**`runner/AGENTS.md`.**

> A restrictive automation sandbox can prevent XPC lookup before the host starts
> or block unified-log access after execution succeeds. Lookup diagnostics can
> include `NSCocoaErrorDomain` 4099 or error 159; log access can report
> `log: Cannot run while sandboxed`. Inspect the diagnostic, request escalation
> and rerun the same failing command once outside the automation sandbox,
> keeping the inspected artifact unchanged. A permission-shaped failure alone
> does not establish its cause.

Retain the detailed interpretation of `xpc_error`, empty `steps`, absent
`runner_subprocess`, the limited compilation evidence in `data.policy_check`,
and `sandbox_log_capture.capture_status`/`blocked_reason`. Keep
`--no-log-capture` limited to investigations that do not need log correlation.
Route signing or compiler problems to the build guidance rather than repeating
its full account.

**`tests/AGENTS.md`.**

> Inspect diagnostics before attributing a test failure to the product or its
> execution environment. Use an unsandboxed shell for cases requiring `app` or
> `worker`. If the automation sandbox refuses an operation, request escalation
> and rerun the same failing command once outside it without changing the
> artifact under investigation. A passing retry can support an environmental
> explanation; it does not retroactively supply missing observations.

Retain the distinctions for `runner_unit` children without XPC, local sockets
and process exit events in cases without an app requirement, Swift discovery in
`source_drift/build_documentation`, and the equipment-reference link. Link to
the runner diagnostics and build guidance for those failures, including
signature verification.

**`docs/BUILD.md`.**

> Run signing and Swift discovery from an unsandboxed shell with the required
> keychain access. A restrictive automation sandbox can block the login
> keychain or swiftc's per-user module cache, and can make `codesign --verify`
> report an invalid signature for unchanged bytes. Request escalation and rerun
> the same failing command once outside the automation sandbox without changing
> the inspected artifact. Treat a signature failure as environmental only if
> that verification passes; investigate any failure that remains.

Retain the explanation that Meson discovers Swift before targets can use
`builddir/`, the distinction between discovery and later signing failures,
`BUILD_XPC=0`, manifest-only introspection, and the Swift configuration exercised
by `source_drift/build_documentation`.

The root overview retains the full range of hazards. Local sections retain
actionable diagnosis and the unchanged retry rule. Neither wording nor the new
check may turn a failure alone into an environmental explanation.

## Checker, controls and documentation graph

### Replace equality with a structural contract

In [check.py](tests/suites/source_drift/check.py), replace
`parse_harness_note_paragraph` and `check_harness_note_agreement` with section
extraction and `check_harness_guidance_routes`. Replace the `HARNESS_NOTE_*`
constants with `HARNESS_GUIDANCE_HEADING`, `HARNESS_GUIDANCE_FILES` and
`HARNESS_GUIDANCE_ROUTES`. Update the invocation in `main` and diagnostics.

The rule must establish:

1. Each of the four workflow documents contains exactly one real Markdown
   heading named `Sandboxed automation harnesses` and a nonempty guidance body.
2. The section ends at the next heading of the same or higher level. Headings,
   comments and fenced examples alone cannot make an empty section pass.
   Heading-like or link-like text in code fences or HTML comments cannot stand
   in for real guidance or a route.
3. The root section contains ordinary Markdown links to each of the three
   prescribed diagnostic sections. Compare resolved repository paths and
   fragments, not link labels or paragraph wording. The destination headings
   must exist in their named documents.
4. Missing, duplicate or empty sections and missing or incorrect routes return
   ordinary check problems and exit status 1 through the existing main path,
   naming the affected document and condition.

Keep the implementation local to `check.py` and its existing fixture inputs.
This is a narrowly defined heading/link contract, not a general Markdown parser.
No paragraph equality, fixed diagnostic word list, or prescribed sentence
order remains. Existing G11 link checks supplement this rule; they do not
replace the requirement that the root section actually provides these routes.

Leave `check_core_ideas_agreement` intact: it checks principle labels and their
order against the architecture account, while allowing independent explanatory
prose. No runtime or native-source check should be weakened.

### Exercise the real checker

Update `guidance_scenarios` in
[check_planner.py](tests/suites/source_drift/check_planner.py). It already copies
selected checker inputs into a disposable checkout and restores them between
mutations. Keep that bounded input copy and the existing receipts.

| Mutation | Expected result |
| --- | --- |
| Independently rewrite a warning body in each document, retaining the root routes where relevant | Pass; no synchronized edits required. |
| Rewrap, reorder paragraphs or add local diagnostic prose | Pass. |
| Remove the heading, duplicate it, or empty the section in each document | Fail with document-specific status 1 diagnostics. |
| Put the only apparent heading/body in a fence or comment; put the only body after the next peer/parent heading | Fail; unrelated text must not fill the section. |
| Remove each root route or change its path or fragment | Fail naming the missing or incorrect route. |
| Put the only required route in a fenced example, comment or another root section | Fail. |
| Change a route's explanatory label while retaining its target | Pass. |
| Restore each damaged input and rerun the checker | Pass. |
| Independently change principle prose; remove, rename or reorder a principle label | Preserve the current pass/fail behavior. |

Replace the old changed-copy rejection and coordinated-copy control, and change
the missing-heading expectation from parser exit 2 to ordinary failure 1.
Retain all unrelated source, Known gap and configured-build controls.
Update the planner step description in
[run.sh](tests/suites/source_drift/run.sh) to describe guidance routes and
principle agreement. Keep the case ID `runner_source_manifests_agree`.

There is no committed warning-specific fixture to edit. The planner generates
its disposable Markdown from maintained inputs. Old planner output remains
evidence of the version that produced it.

### Describe and generate the new dependency

Rewrite `Intentional guidance agreement` in
[the suite reference](tests/suites/source_drift/README.md)
as `Workflow guidance and checked routes`. Explain the structural contract,
its limitations, the independent wording and the unchanged principle rule.
Remove the obsolete explanatory links from the four local warning sections;
any retained link to the suite explanation must use the new fragment
`workflow-guidance-and-checked-routes`. Update its prose-scan filename shorthand.

In [architecture.json](docs/architecture.json), update the documents graph:

- Change the descriptions and citations of `agents_md`, `runner_agents`,
  `tests_agents` and `drift_check` from warning copies/equality to local guidance
  and checked diagnostic routes. Extend `build_md`'s description if necessary
  to account for its guidance alongside its generated build account.
- Keep edge IDs `D22`, `D23` and `D62`, but represent links from the root to the
  local guidance rather than copied paragraphs. Add a `links` edge kind under
  `styles.edge_kinds` using `{"style": "solid", "color": "#444444"}`. Cite
  `HARNESS_GUIDANCE_ROUTES` and `check_harness_guidance_routes`.
- Keep `D29` as a `checks` edge; describe section presence and root routes,
  replacing the old equality source citation.
- Replace the old rule in every affected citation, including the `drift_check`
  node's complete list of checks. Preserve unrelated graph IDs and citations.

The new edge kind is permitted by the manifest's existing style-defined kinds;
no schema change is needed. The
`test_document_graph_cites_every_drift_rule` control in
[generators.py](tests/suites/source_drift/generators.py) compares this node's
citations with the functions called by `check.py`'s `main`. Keep that assertion;
changing only prose or only the function name would leave the dependency broken.

After the new symbols exist and the manifest is updated, run:

```sh
python3 docs/generate_architecture.py
```

Regenerate with Graphviz `dot` available, including SVG rendering; do not use
`--skip-svg` to retain an obsolete figure. Review generated
`docs/ARCHITECTURE.md` regions, `docs/architecture-documents.dot` and
`docs/architecture-documents.svg`. Inspect unexpected changes to other generator
targets rather than hand-editing or accepting them blindly.

### Other generated and shared prose

Use the [generator contracts](tests/suites/source_drift/README.md#generator-contracts)
to preserve ownership. The limits generator copies the shared limits and
questions into `docs/PolicyWitness.md` and owns the shared reading rules,
statuses and matrix outputs it declares. Contract, worker-identity, architecture
and build generators own their declared outputs. Never edit generated copies
to repair the prose search.

The planned `docs/LIMITS.md` paragraph and `docs/BUILD.md` prose edits lie outside
their generated/shared blocks. They need no unrelated manifest change.
The affected passages are absent from
`tests/fixtures/docs/prose_baseline.json`; do not add baseline exemptions for
this revision. No protocol, layout or worker-identity regeneration is expected.
All generator freshness checks still apply.

## Execution and verification

1. **Establish the source boundary.** Confirm `doc-rework`, record HEAD and
   working-tree status, and complete the branch-build baseline above. Then
   reconcile the appendix with tracked and separately classified untracked
   source Markdown, and preserve unrelated edits. Record symlink targets and
   existing local-link failures before editing. In a checkout receiving
   concurrent changes, recheck the source delta before crediting results;
   `tests/.checkout.lock` serializes executions, not editing.
2. **Make coherent source commits.** Apply the prose and heading edits,
   replace the warning rule and its controls, update suite documentation and
   architecture citations, then regenerate the architecture account. Follow
   the commit grouping above: keep the coupled warning change together so no
   committed intermediate state advertises the old equality requirement with
   the new checker, while preserving independent changes as separate commits.
3. **Review editorial meaning.** Compare each rewritten passage with its
   source. Check direct instructions, real end-user uses, historical fidelity,
   all five sandbox hazards, the unchanged retry, signature-verification
   qualification, XPC/fallback limits and unavailable log evidence. A clean
   word search or a structural pass alone cannot establish these properties.
4. **Search only the recorded targets.** Run a case-insensitive whole-word
   search for the brief's singular/plural labels, including possessives, and
   a broader substring search to catch related actor uses. Read every match in
   context. Classify remaining matches as literal technical identifiers or
   exact bounded before evidence; no unexplained prose occurrences may remain.
   Do not exempt all backticks, quotes, plans, historical records or filenames
   containing a broad substring. Confirm every before block is paired, contains
   only the quoted source, and is no larger than necessary.
5. **Check links and stale claims.** Validate changed links and headings and
   the new plan's local links. The G11 scan covers selected guidance and
   `docs/*.md`, not the entire appendix, so supplement it for source paths outside
   that scan. Search source documents and checker inputs for old equality
   descriptions, the old rule/constants, and obsolete heading fragments;
   update active guidance and citations. This plan's explicit migration
   references are intentional technical descriptions. Classify pre-existing
   missing raw-evidence links in historical records separately; do not recreate
   or edit test output to repair them.
6. **Check generator freshness and stability.** Run each command below. After
   regeneration, rerun the architecture generator once and verify that it
   introduces no further diff. Do not regenerate unrelated outputs to conceal
   a failed freshness check.

   ```sh
   python3 docs/generate_contract.py --check
   python3 docs/generate_worker_identity.py --check
   python3 docs/generate_limits.py --check
   python3 docs/generate_architecture.py --check
   python3 docs/generate_build.py --check
   ```

7. **Run the integrated static-documentation selection.** Inspect equipment with
   `tests/run.sh --suite source_drift --list`, unset `PYTHONOPTIMIZE`, then run
   `tests/run.sh --suite source_drift` with a fresh
   `PW_TEST_OUT_DIR=tests/out/runs/<unique-editorial-run>`. Require all six cases:
   `runner_source_manifests_agree`, `limits_documentation`, `contract_versions`,
   `architecture_documentation`, `build_documentation` and `generator_contract`.
   Inspect rejected controls as well as passes. Keep command receipts and source
   provenance under existing retention rules; this plan does not change them.
8. **Verify the branch candidate and review the commit series.** Complete the
   candidate build experiments and any focused infrastructure verification
   described above. Reconcile concurrent changes and
   newly added documentation once more. Verify symlink modes/targets,
   `git diff --check`, generated-source agreement, test accounting and the final
   search classification. Stage only changes belonging to this work and retain
   the separate commits on `doc-rework`. Report the base-to-tip diff, commit
   sequence, tested source states and any later changes that limit coverage.

The editorial suite includes fixture builds and Swift discovery; the branch
investigation additionally requires signed builds and selected artifact and
provenance controls. A full runtime battery is required only if the resulting
infrastructure changes affect boundaries that need it. If sandbox restrictions
cause the documented discovery, signing, XPC or log failures, request escalation and
rerun the same failing command once outside that sandbox with the inspected
artifact unchanged, following the existing working guidance. Never unlink the
checkout lock or alter outputs to force a pass.

## Risks and decisions that would require reconsideration

The main semantic risk is weakening attribution guidance while removing
repetition. The explicit review above is required because section and link
checks cannot assess advice. The main mechanical risks are a section parser
accepting unrelated text, stale heading links, and generated citations naming a
removed function; the negative controls and generator contract address them.

Concurrent edits on `doc-rework`, or later integration from `main`, can change
the inventory or checker inputs during work. Reconcile those changes and rerun
the affected checks; do not claim a prior result covers a later source state.
Keep disposable mutation copies out of the editorial acceptance universe even
when they contain the old prose. Record the branch point independently of a
moving `main` tip so the reviewed commit range stays unambiguous.

The editorial decisions are settled: independent local guidance, the structural
route rule, source-only acceptance and generator ownership. The branch-build
experiment must establish whether additional infrastructure changes are needed;
record that finding before claiming branch compatibility. Reconsider an
editorial dependency if source changes invalidate it or a control demonstrates
that the proposed check accepts a missing section or route. Routine wording and
line wrapping need no new approval.

## Appendix: canonical editorial targets

One repository-relative path per line. The aliases and exclusions are classified
above; generated source documents are included here, while disposable copies
are not.

<!-- BEGIN EDITORIAL TARGETS -->
```text
.tmp/AGENTS.md
AGENTS.md
EXECUTION-PREPARATION-AND-ORDERING-PLAN.md
MARKDOWN-GUIDANCE-PLAN.md
NATIVE-BUILD-PLAN.md
README.md
SHIM-ENVIRONMENT-GUARD-PLAN.md
controller/AGENTS.md
controller/README.md
dist/AGENTS.md
dist/README.md
docs/ARCHITECTURE.md
docs/BUILD.md
docs/CONTRACT.md
docs/LIMITS.md
docs/PolicyWitness.md
docs/QUESTIONS.md
docs/REQUEST-GRAMMAR.md
docs/SIGNING.md
docs/WORKER.md
records/AGENTS.md
records/APPLE-SILICON-ACCEPTANCE.md
records/BUILD-PROVENANCE-ACCEPTANCE.md
records/BYOXPC-ADHOC-BEHAVIOR.md
records/BYOXPC-ENTITLEMENT-BEHAVIOR.md
records/BYOXPC-VERIFICATION-BOUNDARIES.md
records/EVIDENCE-CLARITY-PARKING-LOT.md
records/INTERRUPTION-HOOKS-OUTFLOW.md
records/ISSUANCE-TIMING-OUTFLOW.md
records/PATH-QUERY-RESOLUTION-INVESTIGATION.md
records/README.md
records/SAFE-WAIT-TIME-INVESTIGATION.md
records/SLEEP-WAKE-VALIDATION.md
records/USER-EXPERIENCE-REPORT.md
records/archive/AGENTS.md
records/archive/BYOXPC-CONSUMER-PROBES.md
records/archive/BYOXPC-ENVIRONMENT-OBSERVABILITY.md
records/archive/MESON-CUTOVER-OBSERVATIONS.md
records/archive/SANDBOX-LOG-ISOLATION-INVESTIGATION.md
runner/AGENTS.md
runner/README.md
runner/augments/README.md
tests/AGENTS.md
tests/COVERAGE.md
tests/FAILURE-PROPAGATION-CONTRACT.md
tests/OPT_IN_TESTS.md
tests/README.md
tests/RETENTION-PLAN.md
tests/atlas/ATLAS-BUILD-PLAN.md
tests/fixtures/README.md
tests/fixtures/blackbox_e2e/checker/README.md
tests/fixtures/byoxpc/README.md
tests/fixtures/caller_auth/README.md
tests/fixtures/comparison/README.md
tests/fixtures/comparison/baseline_response12/README.md
tests/fixtures/deny_capture/README.md
tests/fixtures/diagnostic_transport/README.md
tests/fixtures/disposition/README.md
tests/fixtures/exec/README.md
tests/fixtures/extension_controls/README.md
tests/fixtures/host_setup/README.md
tests/fixtures/launch_descriptor/README.md
tests/fixtures/path_query/README.md
tests/fixtures/release/README.md
tests/fixtures/sandbox_extensions/README.md
tests/fixtures/validator/README.md
tests/fixtures/worker_harness/README.md
tests/fixtures/worker_lifecycle/README.md
tests/lib/vendor/README.md
tests/suites/blackbox_e2e/README.md
tests/suites/blackbox_menagerie/README.md
tests/suites/dispatcher/README.md
tests/suites/exec_fixture/README.md
tests/suites/failure_boundaries/README.md
tests/suites/integration/README.md
tests/suites/opt_in/README.md
tests/suites/preflight/README.md
tests/suites/run_capture/README.md
tests/suites/run_effects/README.md
tests/suites/runner_abi_layout/README.md
tests/suites/runner_apply_isolation_v2/README.md
tests/suites/runner_apply_isolation_v3/README.md
tests/suites/runner_byoxpc/README.md
tests/suites/runner_c_worker_harness/README.md
tests/suites/runner_exec_dac/README.md
tests/suites/runner_exec_inheritance/README.md
tests/suites/runner_exec_lifecycle/README.md
tests/suites/runner_filter_iokit_registry_entry_class/README.md
tests/suites/runner_filter_iokit_user_client_class/README.md
tests/suites/runner_filter_local_name/README.md
tests/suites/runner_filter_sysctl_name/README.md
tests/suites/runner_live_worker_identity/README.md
tests/suites/runner_mach_service_liveness/README.md
tests/suites/runner_outcome_bad_request/README.md
tests/suites/runner_outcome_runner_timeout/README.md
tests/suites/runner_outcome_validator_no_reply/README.md
tests/suites/runner_outcome_worker_spawn_failed/README.md
tests/suites/runner_ready_byte_resilience/README.md
tests/suites/runner_specimen_isolation/README.md
tests/suites/runner_unit/README.md
tests/suites/runner_use_c_worker/README.md
tests/suites/runner_validator_failure/README.md
tests/suites/sandbox_extensions_native/README.md
tests/suites/sbpl_allowdeny_consistency/README.md
tests/suites/shell_helpers/README.md
tests/suites/smoke/README.md
tests/suites/source_drift/README.md
tests/suites/unit/README.md
tests/suites/validator_batch_mode/README.md
tests/suites/validator_bridge/README.md
tests/suites/witness_contract/README.md
tests/suites/witness_contract/harness/VERIFICATIONS.md
```
<!-- END EDITORIAL TARGETS -->
