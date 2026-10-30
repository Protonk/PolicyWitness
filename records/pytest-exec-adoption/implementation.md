# Candidate implementation sequence

Candidate worktree: `/private/tmp/pw-pytest-exec-candidate-20261030`.
Branch: `adoption/pytest-exec-family`; starts at authorization amendment
`8fd2c825`. Accepted checkout remains at `77eb9875` with its unrelated untracked
review materials. The frozen investigation and protected resources are unchanged.

## Preparation and stage 2 checkpoint

Provisioned the five pinned wheels into the interpreter/lock-keyed package target
using `tests/setup-pytest.sh --wheels .tmp/pytest-wheels`. This is explicit setup,
not collection-time installation. The lock records wheel URLs and SHA-256 digests.
Interpreter: `/opt/homebrew/opt/python@3.14/bin/python3.14`, 3.14.9; pytest 9.0.2.

The initial implementation adds the domain/module organization and the PW command
owner, durable registry and independent source-contract reader. The ordinary F
route is still the accepted shell route. The registry is **not yet** a shared
admission dependency. `dispatcher/pytest_controls` exercises the boundary before
that switch. Its observation file is authored by the external control, not the
candidate report interpreter. Fixture registry ambiguities are deliberately
retained inside that control's evidence, without claiming a production recovery
basis. Their launcher was never invoked by the fixture controller.

No acceptance claim has yet been made. Subsequent source commits, fresh run
identities, corrections and dispositions are recorded below before final sealing.
