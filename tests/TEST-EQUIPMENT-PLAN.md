# One-helper test equipment inventory

## Goal

Create a small, checked inventory for `tests/fixtures/exec/control.py`.
A reader should be able to find the canonical test cases that directly use this
module and the cases that directly test its behavior. The inventory itself is
the readable output. A dedicated `test_equipment` suite will check inventory
format and reference validity, with a separate case testing the validator itself.
Passing these checks does not establish agreement between declarations and
actual source dependencies; that remains a dated, reviewable manual claim.

This is an implementation plan. Writing the specification, tracing dependencies,
populating the inventory, and writing tests are tasks below; none is complete
merely because this plan exists.

## Scope

Inventory this one Python module, including its process observers and process
snapshot support. Leave its implementation and its consumers' assertions alone.
The new helper to build is an **inventory validator**, not a replacement for the
process-observation equipment.

Record declared direct dependencies at canonical test-case granularity. Manual
source review establishes the initial membership. Automated validation establishes
that records are well formed and their references resolve. Neither validation nor
a passing consumer proves that the equipment is adequately tested. Any claim of
completeness applies only to the sources examined at the recorded review revision.
Adding or removing an import can leave reference validation green while making
membership stale. Changes to consumers require manual review and an inventory
update where appropriate.

Keep this metadata separate from `tests/catalog.json`'s execution `depends_on`
relationships. Add two ordinary offline cases without changing selection,
ordering, prerequisites, or execution semantics for existing cases. Do not add
dependency discovery, transitive analysis, new runner flags, a report generator,
or inventories for other equipment.

## Starting points

- `tests/README.md`: public case selection, canonical IDs, and shared equipment.
- `tests/catalog.json` and `tests/lib/test_cli.py::catalog`: authoritative case
  identities and suite inclusion semantics. Canonical references have the exact
  form `suite/leaf`, such as `exec_fixture/controls`. A case included by several
  suites still has one canonical identity. `exec_fixture/controls` and
  `run_capture/controls` are distinct cases despite sharing a leaf name.
- `tests/suites/source_drift/check.py` and `README.md`: existing source and
  registry agreement checks. They will verify ordinary registration of the new
  suite; inventory validation must not be folded into their current case.
- `tests/suites/dispatcher/run.sh` and `tests/lib/case.sh`: existing patterns for
  separately selectable cases, failure propagation, and retained diagnostics.
- `tests/fixtures/exec/control.py` and its directory's `README.md`: the module
  being inventoried and its intended behavior.
- `tests/suites/exec_fixture/check.py`: direct equipment controls to examine.

Search all checked-in test sources for imports and uses of the module, then trace
the relevant scripts through their wrappers to canonical cases. For example,
release deadlines, dispatcher cancellation, run capture, specimen isolation, and
exec lifecycle use this equipment. These are search starting points, not a
completed or authoritative membership list. Using `helper.c` or `inspection.py`
alone does not establish a dependency on `tests/fixtures/exec/control.py`.

There is also an unrelated `tests/fixtures/worker_harness/control.py`.
`tests/suites/shell_helpers/check_worker_setup.py` selects that stand-in through
`CONTROL_WORKER_DRIVER`, with `FIXTURE` pointing to `tests/fixtures/worker_harness`.
Exec consumers instead insert `tests/fixtures/exec` into `sys.path` before a bare
`from control import ...`. Search hits are candidates: trace the path construction
or import search path to the actual repository-relative module path before
assigning membership. Neither the filename `control.py` nor the import name
`control` alone identifies the inventoried equipment.

## Work sequence

### 1. Write the specification

Create `tests/TEST-EQUIPMENT.md` before implementation. Keep it short and sufficient
to author the inventory and its acceptance tests without reading validator code.
Specify:

- The record format for `tests/equipment.json`, limited to the one inventoried
  module, its consumer references, and its direct control references.
- What qualifies as a direct consumer or a direct control, how to map a script
  to a case, and how to represent a case that serves both roles.
- Equipment identity by repository-relative path, with this inventory keyed to
  `tests/fixtures/exec/control.py`. Resolve the declared path from the repository
  root. Checking its existence does not check the reviewer's attribution of a
  consumer to that module.
- Exact, suite-qualified `suite/leaf` references for both consumers and controls.
  Reject bare leaves even when unique, and reject unknown qualified references
  rather than resolving their leaf in another suite. Duplicate detection applies
  to the full canonical ID within each role; distinct suites may share a leaf.
  Suite inclusion must not multiply a canonical case.
- Required fields and types and handling of missing or malformed input.
- How an explicitly empty control list expresses that no direct control has been
  identified. This is valid inventory data, not a reason to invent protection.
- The validator's small callable boundary, success/failure behavior, and useful
  diagnostic content. Diagnostics must identify the offending path or reference;
  tests should not require an exact paragraph or line order.
- The maintenance rule for changing direct consumers or controls, and the
  distinction between reference validity and manually reviewed completeness.
  Include the source-trace and review-provenance requirements from step 2.

Use this specification to settle routine format choices before writing tests.
Do not introduce additional metadata without a need in this scope.

### 2. Create the inventory and failing tests

Populate `tests/equipment.json` by reviewing actual imports, uses, wrappers, and
case definitions. Read the assertions before calling a case a direct equipment
control: merely using the observer is not sufficient. Add a compact review note
in `tests/TEST-EQUIPMENT.md` that lets a reader re-check each attribution:

- Record the review date and full reviewed commit SHA. Review the committed
  source tree and confirm that the cited sources and existing case/wrapper
  definitions match it. Do not attach a commit SHA to a review of uncommitted
  source changes; refresh the review against their committed version if needed.
  Uncommitted inventory, validator, or documentation work does not by itself
  prevent reviewing the unchanged consumer sources. Retain one current review
  record, not a history log.
- For each consumer entry, cite the `sys.path.insert` or explicit path-construction
  statement, the import and actual use, and the wrapper connection to the
  canonical case. Give repository-relative paths and enclosing functions or
  distinctive statements; line numbers can supplement these anchors.
- For direct control entries, also cite the assertions that exercise the
  equipment's behavior. An import or a passing consumer is insufficient evidence
  that a case tests the equipment itself.
- Record `tests/fixtures/worker_harness/control.py` as examined and excluded.
  Cite both `FIXTURE = ROOT / 'tests/fixtures/worker_harness'` and the
  `CONTROL_WORKER_DRIVER` assignment in `check_worker_setup.py`, explaining that
  these resolve to the separate builder/harness stand-in.

The inventory remains the authoritative membership list; the note supplies
evidence for its entries and the exclusion. The note is a manual review record,
not a machine-verified proof or an automatic freshness check. This is where the
same-filename attribution risk is addressed; a validator cannot detect a false
consumer attribution when both recorded references exist.

In `tests/TEST-EQUIPMENT.md`, explain how to use the recorded SHA: substitute it
for `REVIEWED_SHA` in `git log REVIEWED_SHA..HEAD -- tests` to locate later work,
and use `git diff REVIEWED_SHA -- tests` plus `git status --short -- tests` to
inspect tracked and untracked changes. The note's own later commit does not make
the source review stale: inspect changes to consumer code, import resolution,
wrappers, and case definitions, not just the presence of later commits. Review
relevant changes and repeat the bounded consumer search when sources change;
searching all of `tests` includes potential new consumers outside the original
list. This is a documented manual procedure, not a new freshness checker.

Write independent validator controls under
`tests/suites/test_equipment/check_controls.py`. Use a tiny, hand-authored case
catalog and temporary inert helper files. Load that catalog through
`tests/lib/test_cli.py::catalog`, using the same catalog-loading path as the real
inventory checker, and pass its canonical case universe to the validator.
Expected answers must come from the specification, not from the real inventory
or validator output. These tests must not import or execute the real
process-observation module.

Cover at least the following agreed behaviors, plus the input rules settled in
step 1:

- A valid helper with two consumers and one direct control passes.
- A missing helper, an unknown consumer, and an unknown control each fail with
  an identifying diagnostic.
- Two distinct suite-qualified references sharing the leaf `controls` pass
  together; neither is treated as a duplicate of the other.
- Bare `controls` fails both when the leaf is shared and when it is unique.
- An unknown `suite/controls` fails even when another suite defines `controls`.
  Exercise reference rejection in both the consumer and control roles.
- Repeating the same fully qualified ID within a role fails rather than being
  silently collapsed.
- An explicitly empty control list passes and remains represented as empty.
- Suite inclusion preserves canonical identity: when an including suite lists
  another suite's case, the owning suite's canonical reference passes and an
  invented reference under the including suite fails. Exercise both roles.
- An opt-in case (`default: false`) with declared runtime prerequisites passes
  as both a consumer and a control without checking those prerequisites or
  executing its command.
- The chosen representation for a case serving both roles is accepted.

Run the tests before implementing the validator and retain the commands and
failure output under a dedicated `tests/out/` directory. A missing module or
callable establishes only that implementation is absent. Once the callable
boundary exists, demonstrate that a validator which accepts everything fails the
negative controls; do not treat import errors as behavioral test evidence.
Keep any such temporary stub confined to this development step.

### 3. Build the inventory validator

Implement the specified boundary in `tests/lib/equipment.py`. Keep it read-only
and small. It should receive explicit inputs so controls can supply their own
root and case universe without editing the repository's inventory.

Reuse the authoritative catalog reader where practical; do not build a second
case-selection implementation. Check references against all canonical cases,
including opt-ins, without checking their runtime prerequisites or running them.
Validate helper paths without importing the helper. The module must not launch
processes, open observation sockets, or initialize test output as a side effect.

Run the unchanged controls until they pass. Change an expectation only to correct
a documented specification error, and keep the specification consistent with the
final tests. Do not hard-code the current consumer list into the validator.

### 4. Integrate and verify

Create `tests/suites/test_equipment/run.sh` using the existing case helpers, with
two independently selectable default cases registered in `tests/catalog.json`:

- `test_equipment/inventory_references`: a thin `check_inventory.py` entry point
  validates the real inventory's format, helper path, and canonical references.
  Success means only that the declared records and references are valid.
- `test_equipment/validator_controls`: runs the independent controls from step 2.
  Success means the validator accepts and rejects the specified inputs correctly.

Both cases need only Python and the ordinary shell harness. Give each its own
result, diagnostics, and artifacts. Keep
`source_drift/runner_source_manifests_agree` and its existing checks separate;
its result must not silently include either new check.

Keep each wrapper block as the ordinary selected-case setup, a direct
`test_check_python` invocation of the intended checker with explicit inputs,
and `test_pass` only after that succeeds. Add no custom status interpretation,
fallback input selection, or validation logic in the shell wrapper. Review the
checker path, inputs, and ordering explicitly.

Use the independent validator controls for acceptance/rejection behavior and the
existing shell-helper and dispatcher controls for failure propagation. Do not add
a suite-specific disposable-repository integration test or extend shared fixture
machinery for this MVP. Passing public-command runs check registration and normal
execution; they do not prove the wrapper rejects invalid input. Correct wiring
remains a small, explicit code-review obligation. If the wrapper needs its own
conditional behavior or result translation, reconsider a targeted test of that
behavior rather than silently expanding this plan's fixture setup.

Update all public discovery surfaces as planned implementation work:

- In `tests/catalog.json`, give the two new cases descriptions of their limited
  claims. Preserve the existing source-drift description's count enumeration as
  a diff-visible review cue. Update its suite count for the new suite (currently
  37 to 38), checking the enumeration against actual source-drift output. These
  counts are maintained description text, not an automatically enforced claim
  about dependency coverage.
- Add a `test_equipment` row to the suite-coverage table in `tests/README.md`,
  distinguishing reference validation from validator controls and manual review.
  Correct the `source_drift` row to cover its existing registry/outcome checks as
  well as runner source manifests. Do not attribute dependency discovery to it.
- Create `tests/suites/test_equipment/README.md` with the two cases' claims,
  artifacts, prerequisites, and limits. Link `tests/TEST-EQUIPMENT.md` from
  `tests/README.md` and `tests/fixtures/exec/README.md`.

Exercise each new case through an exact `--case` selector to verify independent
selection and reporting. Then run `tests/run.sh --suite test_equipment --suite
source_drift` to verify the real inventory, controls, and suite registration
together. Set an explicit, separate `PW_TEST_OUT_DIR` inside `tests/out` for every
public-command run, including both exact-case runs and the combined run. Keep
these directories and the retained development evidence directory non-overlapping;
none may contain another. The dispatcher replaces its selected output directory
before execution, so using the default `tests/out` or reusing an evidence
directory would erase earlier failure or pass evidence. Run dispatcher selection
controls only if shared catalog-reading behavior changes. This work requires no
app build, signing, live PW run, execution of the inventoried cases, or full suite.
Review the diff and run `git diff --check`.

## Completion and handoff

The work is complete when:

- The written specification matches the inventory and validator controls.
- Exactly one real equipment module is inventoried, with membership justified
  by revision-specific source traces, the recorded exclusion, and valid canonical
  references. Manual provenance is distinct from automated validation.
- Positive and negative controls pass, including acceptance of an empty control
  list. Public-command runs verify selection, registration, and normal execution;
  review confirms direct checker invocation and use of the shared failure path.
- Inventory validity and validator controls have separate canonical cases and
  results. Existing source-drift checks still pass, the suite is registered in
  every discovery surface, and execution semantics for existing cases are unchanged.
- The documentation explains how to use the recorded revision to inspect later
  changes, how to maintain the record, and what validation cannot establish.

Report the changed files, membership-review rationale, commands and results,
retained failure/pass evidence paths, and any unresolved limitation. Distinguish
manual review from automated verification. This plan contains no requirement to
add more equipment or to run its consumers merely to validate their references.
