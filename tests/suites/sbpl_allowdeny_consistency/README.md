# sbpl_allowdeny_consistency

End-to-end check that SBPL `(allow ...)` / `(deny ...)` rules produce
verdicts and attempt outcomes that agree with kernel-observed behavior.

A single specimen (`fixtures/runner_smoke/v1`) drives four steps — file
write and `mach-lookup`, each in an allowed and a denied variant — through
a real `dist/PolicyWitness.app` run.

## Invariants

- `result.ok == true`, `normalized_outcome == "ok"`, `sandboxed_after_apply == true`.
- Exactly four steps; each carries `attempt.requested_path` / `normalized_path` / `observed_path`.
- Allowed step: `sandbox_check.outcome == "allow"`, attempt `exit_code == 0`,
  `syscall_errno == null`, `deny_signal.delta == 0`.
- Denied step: `sandbox_check.outcome == "deny"`, attempt `exit_code != 0`,
  `syscall_errno` populated.

This is a **positive** correctness check: it passes when verdicts and
attempts line up and fails when they diverge. (It was formerly framed as an
inverted "anomaly reproduction" suite; the test has asserted consistency,
not reproduced a bug, since the evidence contract was tightened.)

## Host dependency

Sandboxed automation harnesses can block XPC lookup or unified-log access,
which can perturb `deny_signal` capture. If the test fails with those
symptoms, rerun from a normal Terminal.

## Fixtures

- `tests/fixtures/runner_smoke/v1/profile.sbpl`
- `tests/fixtures/runner_smoke/v1/specimen.template.json`

## Artifacts

- `tests/out/suites/sbpl_allowdeny_consistency/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite sbpl_allowdeny_consistency
```
