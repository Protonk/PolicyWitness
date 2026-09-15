# Testing audit — adversarial review of the test command

## Task and required output

Try to falsify the three claims below about the new test-control design. Look
for concrete counterexamples in behavior, not merely missing tests or stylistic
preferences. A convincing finding may concern misleading semantics even when
the implementation follows its own documentation.

**Write your full results into this file, `tests/TESTING-AUDIT.md`, under
`Audit results`. Preserve the prompt.** For each question, report your conclusion,
what you inspected/exercised, and any remaining uncertainty. For each finding,
include severity, source file/line, exact reproduction, expected versus observed
behavior, retained evidence, and the smallest useful remediation or contract
test. Distinguish reproduced failures, code-supported findings, and hypotheses.
If you find no counterexample, describe the bounds of your search; do not claim
exhaustive correctness. Your final chat reply should briefly report completion
or blockage and link to this document.

The reviewed implementation is commit `ed922f7` (test selection/configuration/
accounting), following `2d2283e` (Python assertion startup guard). Record actual
HEAD and working-tree differences; review the current implementation and explain
any relevant changes since those commits. Do not reset the checkout.

## Starting points and work boundary

Read `tests/README.md`, then follow the relevant paths:

- `tests/run.sh`, `tests/catalog.json`, `tests/lib/test_cli.py`
- `tests/lib/suite_run.py`, `tests/lib/testlib.sh`
- `tests/suites/runner_byoxpc/run.sh` and selected suite entrypoints
- `controller/integration/cli_contract.rs` for artifact consumption
- `tests/suites/dispatcher/{check.py,check_selection.py}` and
  `tests/suites/shell_helpers/check_scripts.py` for existing defenses

Edit only this audit document among repository source/documentation files.
Create any reproduction scripts, disposable fixture repositories, and raw
observations under `tests/out/testing-audit/flag-design/<your-run-id>/`.
Use physical copies of the reviewed runner for disposable experiments. You may
supply independent catalogs and fixture commands to exercise runner contracts;
clearly distinguish those experiments from reproductions using the real catalog.
Do not modify the reviewed planner/executor to manufacture a failure.

Prefer a small reproduction over a broad run. Do not run the full test suite.
`--list` and offline controls need no live PolicyWitness execution. If a live
PW/XPC/signing command is necessary, select a single command and request
escalation so an outer sandbox does not masquerade as a product failure. Give
executing test commands their own `PW_TEST_OUT_DIR`; the default output directory
is replaced on execution and may contain other evidence.

## Three adversarial questions

1. **Can a reasonable flag combination run a different set of work from what
   a human or agent would understand it to select?** Challenge no-argument
   defaults, literal `--all`, repeated/mixed `--suite` and `--case`, suite
   inclusions, runner contexts, dependency insertion, and `--list`. Can ordering,
   duplication, opt-in membership, or an unknown identifier silently add or omit
   work? Does a case advertised as selectable actually isolate that case in the
   real entrypoint? Inspect the relationship between catalog membership and
   existing suite/manifest cases: where could registration hide work? Use actual
   execution receipts where possible; a planner agreeing with its own catalog
   is insufficient evidence of correct dispatch.

2. **Can configuration be silently ignored, cause tests to use different
   artifacts, or let inspection/rejection alter existing evidence?** Challenge
   app/controller aliases, helper lookup, caller working directory, relative
   paths, symlinks, output overlap, run labels, quiet values, and private runner
   settings. Trace effective configuration into real shell and Rust consumers.
   Try to demonstrate a meaningful mismatch between the advertised plan and the
   artifact actually exercised, or a filesystem change caused by help, listing,
   or rejected input. Identify any restriction that makes the small interface
   misleading or needlessly inexpressive; explain the concrete use case.

3. **Can selected work disappear while the command exits successfully or
   reports `ok: true`?** Challenge crashes, incomplete/contradictory evidence,
   unexpected reports, skips, unavailable prerequisites, failed dependencies,
   and the BYOXPC shared installation/cleanup lifecycle. Can one failure suppress
   independent cases without accurate accounting? Does deduplication accidentally
   remove the defense against genuinely reused evidence? Are completed, skipped,
   and unrun selections truthful and consistent with the command exit? Examine
   whether existing controls independently observe these facts or merely echo
   the machinery they purport to check.

Concentrate effort on the strongest counterexample for each question. Report
additional material findings if you encounter them, but avoid expanding into
worker implementation review or a speculative feature wishlist.

## Existing verification and known failure

The expanded `--all` run selected 111 cases: 110 passed, one failed, none skipped
or unrun. The failure was `runner_byoxpc/runner_auth_external`: installation
succeeded but verification returned `xpc_timeout`. The unchanged script also
failed when invoked directly outside the new dispatcher and outside the harness
sandbox. Team-matched BYOXPC installation and all its selected specimens passed.
This timeout is known; do not report its existence as a new flag-design finding.
You may investigate whether the new design mishandles its consequences.

Useful existing artifacts, if still present:

- `tests/out/control_surface/all/run.json`: expanded live run (before final
  selector-metadata refinements; use the current code for fresh reproductions).
- `tests/out/control_surface/auth_direct/`: direct external-auth reproduction.
- `tests/out/control_surface/final-offline/`: passing final offline suites,
  including 63 public-command controls and 29 wrapper controls.
- `tests/out/control_surface/reuse-final/`: passing 28 reconciliation controls,
  including distinct selections that try to reuse the same evidence path.
- `tests/out/control_surface/alternate-run/` and
  `tests/out/control_surface/alternate/executed-tools.jsonl`: passing Rust
  integration and shell smoke through alternate app wrappers, with independent
  receipts for nine controller invocations and two bundled `sbpl-check` calls.

These results are starting evidence, not premises you must accept.

## Audit results

Pending.
