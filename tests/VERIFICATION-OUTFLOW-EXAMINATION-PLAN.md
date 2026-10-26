# Verification requirement examination plan

This handoff identifies unresolved verification requirements exposed by the
guide revamp(c.f. 47e280a7fc9f5e1bd53f87f8ed3bc1eb30a5bd9c). Examine each item with the
user before changing the obligation. The guide's qualifications remain in place
until the corresponding question is settled; preparing this plan does not settle
it or require executing the controls.

## Build-provenance acceptance scope

- **Index route:** Build, toolchain, signing or artifact inspection in
  [Find verification for a change](CHANGE-VERIFICATION.md#find-verification-for-a-change).
- **Affected control:** `preflight/build_toolchain_switch_controls`; the
  uncertainty does not apply to the other build controls in that row.
- **Unresolved question:** Beyond changes to the stamp's fields or comparison,
  what present-day work falls under "acceptance of the build provenance work",
  and does it require executing the toolchain-switch control? Is that additional
  acceptance instruction specific to the original implementation, or recurring?
- **Supported instruction:** Run the control after changing the stamp's fields
  or comparison. Preserve its distinct-toolchain equipment conditions, retained
  observations and failure treatment while examining the broader scope.
- **Sources:** The [guide entry and qualification](CHANGE-VERIFICATION.md#build-toolchain-switch-controls)
  retain the trigger and the unresolved wording. The original instruction is at
  `tests/OPT_IN_TESTS.md`, lines 329–330, in revision
  `430f0db1bdaf08388b60d9f870c7da53058b34ae`; inspect it with
  `git show 430f0db1bdaf08388b60d9f870c7da53058b34ae:tests/OPT_IN_TESTS.md`.
  The [build refusal account](../docs/BUILD.md#refusals) and
  [preflight account](suites/preflight/README.md#success-criteria) describe actual
  toolchain switching and the equipment it requires, but do not define a broader
  acceptance trigger. These accounts do not establish that the additional
  requirement has expired or applies to every build change.
- **Examination:** Trace the instruction's introduction and associated acceptance
  scope, then review with the user which current changes, if any, inherit that
  obligation. Separate that policy decision from what a successful control can
  establish; running it once cannot determine when future work must run it.
- **Done when:** A supported instruction or explicit user decision defines the
  scope and mandatory status beyond stamp changes, or explicitly retires the
  additional requirement. Update the guide's entry and index together, keeping
  the stamp-change trigger and equipment qualifications unless the decision
  explicitly changes them. Record the decision and its basis in this item.
