# Investigation Plan for Subordinate pytest Integration

## Objective

Investigate the effort required to introduce pytest beneath PolicyWitness’s existing test infrastructure, with the specific aim of eventually refactoring `tests/suites/preflight/check_build_provenance.py`.

Read this alongside [the investigation brief](PW-PYTEST-INVESTIGATION-BRIEF.md), which supplies external examples and the rationale for freezing a baseline, adopting common patterns, and examining the variants that remain. This plan defines the scope of the investigation.

The [external-pattern report](PW-PYTEST-PATTERNS-REPORT.md) records the four-project source investigation for item 3 and limited PW comparisons. The remaining investigation and implementation decisions are still open.

This is an investigation, not an implementation. Do not modify tracked files or undertake the refactor.

## Investigation

1. **Establish the current boundary.** Trace how `check_build_provenance.py` is invoked, how its tests are selected and executed, and how failures, output, cleanup, and evidence reach the existing dispatcher. Identify the responsibilities pytest should assume and those that should remain with the surrounding infrastructure. Examine the dependency and interpreter boundary without making the investigation contingent on a particular Python version or interpreter migration.

2. **Inventory the file and identify a comparison baseline.** Examine its `unittest` classes, fixtures, setup and cleanup behavior, assertions, subprocess controls, and shared helpers. Distinguish organizational machinery from meaningful test-specific behavior. Propose what should be held stable during an initial migration so its effects can be assessed: the selected checks, inputs and expectations, relevant state transitions, and outcome reporting. Flag questionable expectations separately rather than treating their current existence as a permanent requirement.

3. **Investigate transferable patterns.** Use the related projects in the brief as starting points. Examine both test bodies and their supporting fixtures or invocation paths. Consider Zephyr’s division of responsibility, meson-python’s visible build and mutation sequences, PyPA build’s independent malformed-input cases, and pytest’s checks of its own execution and reporting. Identify a few patterns worth borrowing, the conditions that make them work, and important differences from PW. Keep the external comparison bounded to these four projects.

4. **Evaluate subordinate integration.** Determine how pytest could execute within the existing catalog and dispatcher without replacing their authority. Compare running the current tests largely unchanged with gradually adopting pytest fixtures, parametrization, and assertions. Distinguish a useful transitional step from an organizational improvement. Consider temporary-directory and cache ownership, execution ordering, diagnostics, cleanup, interruption, and retained evidence.

5. **Examine representative refactors.** Select several tests with materially different characteristics. Include independent variations and an intentionally stateful sequence where the file provides them. Describe how each might look under an ordinary pytest pattern, what existing machinery could disappear, and what might become harder to understand or verify. Examine any necessary departures from that pattern: do they preserve a real requirement, accommodate an inherited arrangement, or indicate a poor fit? Do not implement examples in the repository.

6. **Estimate the work.** Identify the changes needed for initial integration, subsequent file-local refactoring, and verification. Distinguish mechanical work from changes requiring judgment. Explain how a later implementation could compare the frozen baseline with the migrated checks while keeping deliberate expectation changes identifiable.

## Deliverable

Write a short assessment containing:

- A proposed integration boundary and comparison baseline.
- A few useful external patterns, with source references and their transfer limits.
- Promising and unpromising refactor targets within `check_build_provenance.py`.
- Significant variants likely to remain, with reasons or unresolved questions.
- A staged effort estimate, including important uncertainties.
- The smallest productive first implementation step.
- Reasons to defer or reject the refactor, if warranted.

Preserve the possibility that pytest integration is worthwhile even if substantial portions of the file remain unchanged. Judge the proposal by whether it reduces infrastructure that requires PW-specific knowledge and makes the remaining special cases clearer, rather than by the proportion converted.

## Scope

Keep proposed migration work within `check_build_provenance.py` and the integration changes necessary to run it subordinately. Inspect surrounding code and related projects as needed to understand that boundary.

Do not propose migrating other test files, replacing PolicyWitness’s dispatcher, or restructuring the wider test system. Leave implementation and changes to existing expectations for a subsequent decision.

