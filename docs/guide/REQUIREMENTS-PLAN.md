# Plan for the user requirements core

## 1. What qualifies as a user responsibility

Build a small set of instructions around which to organize the future user guide. Each should fit in one sentence addressed to someone doing real work with PW. Name who acts, when they can act, and what to do or what conclusion to withhold. The effort and access required must be reasonable for someone using the shipped app. Identify the cue in the specimen, environment or result and the concrete consequence of overlooking it. [PolicyWitness user guide](../PolicyWitness.md)

A responsibility earns its place here by changing a test decision. **If the user follows this instruction, which outcome can vary while PW still owes them the same evidence?** Name the assertion that currently fixes that outcome. Then name what PW still owes the user and the check that would catch it getting that wrong.

Start with the maintainer's candidate list. Trace each instruction to its authored contract statement, the assertion in the test, and the evidence behind it. Record the proposed disposition in part 3. Combine findings that ask the same person to take the same action under the same conditions, keeping each affected assertion traceable. The core is ready for the guide when each selected instruction is actionable and its test disposition is justified. A finding stays a proposal until the responsibility and its effect on the public contract have been selected. [Contract sources and trace views](../contract/README.md)

## 2. Where to look in the tests

Find the case in the suite map, then read its assertions for these patterns. [Suite coverage map](../../tests/README.md#suite-coverage)

- **Ambiguous input.** Two spellings, orders or declarations compete. Does the test require a particular winner that the author could specify directly?
- **Operator-controlled setup.** A test fixes a file, service or helper outcome. Could the operator establish the relevant condition before the run? Which assertion still checks PW's observation of it?
- **Interpretation.** A test records two observations and then requires a conclusion. Which conclusion belongs to the reader, and which raw facts and associations must PW still report correctly?
- **Repeated coverage.** Several cases rehearse the same user choice. Which surviving case observes the same effect at the same boundary?

Retire an assertion whose expected value the selected responsibility makes unnecessary. Keep a useful observation as informational when it has no expected product value. Subsume an assertion when another check establishes it independently. In a mixed case, apply the decision to the individual assertion. [Test outcome meanings](../../tests/README.md#declared-observations-and-judgments)

## 3. Numbered findings

1. **Proposed — Use each field name at most once in each JSON object in your specimen.**

   The specimen author can check the original JSON before submission with a reader that detects repeated names. In the local development run `final-default` (`20261120T083452Z_fa6bb141`), byte-identical inputs named file A and then file B as `attempt.target`. The CLI created B. Direct XPC submission created A. Both reported `finished`. The test inspected both paths after each run. A successful result therefore gives the author no assurance that the intended file was chosen. [Current request statement](../REQUEST.md#contract-request-specimen-duplicate_keys)

   **Proposed test change.** In `runner_outcome_bad_request/accepted_input_contract`, `duplicate_entries` exercises six fields in both orders at both entries, alongside 24 single-occurrence controls. Move the choice of a single value to the author in the request surface and retire the first-value and last-value assertions. The direct host's refusal of a controller-only runner selector already has a single-occurrence control, `direct_selector`. [Authored request surface](../contract/10-request.surface.md) · [Test implementation](../../tests/suites/runner_outcome_bad_request/contract.py)

   **Check what survives.** Before folding away the paired controls, account for each independent obligation they exercise. Run the surviving admission case and inspect its accepted and refused inputs. A valid create must affect the declared target, a foreign contract must be refused at the receiving boundary, and a refused specimen must produce no file effect. Duplicate step IDs across different actions still have their own meaning and refusal check. [Admission suite](../../tests/suites/runner_outcome_bad_request/README.md) · [Request corpus](../../tests/fixtures/request_contract/examples.json)
