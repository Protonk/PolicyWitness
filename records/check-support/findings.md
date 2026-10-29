# Findings and decision boundary

Current behavior at `cf0136bbb6366d5f787c3547ec69d757772898c0`.

## F1 — host-source guarantee exceeds its symbol set

`tests/suites/source_drift/README.md` says the host-source check rejects native
extension issue/consume/release functions as well as compile/apply/check calls.
`check.py:HOST_SANDBOX_SYMBOLS` contains eight names, none an extension function.
`host_invariance_problems` only rejects direct names/bindings/dlsym lookups from
that set; literal libsandbox `dlopen` is separately rejected. Its control in
`check_planner.py:host_invariance_controls` builds rejected function examples
from the implementation's same set, so omission of an entire promised family
does not fail that control.

The minimal constructed examples are committed in `host-finding.json` and
reproduced by `collect.py:host_finding`. At the fixed source, direct calls to
`sandbox_extension_issue_file`, `sandbox_extension_consume` and
`sandbox_extension_release`, and a literal `dlsym` of consume, return no
diagnostic. The paired `sandbox_check` call and literal libsandbox load are
rejected; a comment is accepted. This is a local, in-process diagnostic of
the existing rule, not a dispatcher test or proof that production calls them.

`tests/lib/artifact.py` separately rejects undefined imports whose names begin
`sandbox_`, so a directly linked extension symbol can still be caught in the
shipped binary. That companion does not repair the source promise or cover a
computed runtime lookup. No production host violation has been demonstrated.

Disposition: reported to the primary executor for user discussion. Do not
silently weaken the documented guarantee, change the symbol set, or adopt the
checker-derived control oracle. D1 records evidence and leaves that decision
open; D2 must preserve the explicit decision boundary.

## F2 — observation applicability and retention

The L trace establishes changed represented inputs and absent former pins.
Neither establishes that L's historical facts are false. The existing
WORKER prose already requires applicability review or reobservation. The
paper design may make that review state visible, without turning all census
contents into universal expectations. No live rerun or pin repair is needed
to establish these documentary facts.

## F3 — names understate the suite's scope

The source_drift suite and runner_source_manifests_agree case now contain
distinct registry, parser, generator, textual-grounding and source-convention
contracts. D2 should trace edits before choosing organization; a renamed
container alone would not strengthen a claim's support.
