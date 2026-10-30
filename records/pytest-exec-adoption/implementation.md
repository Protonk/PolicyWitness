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

### Consequential failure and correction

Source `46ec2289`: pinned `pytest-exec-ownership-01` and unchanged unsandboxed
repeat `pytest-exec-ownership-02` both failed after the controlled supervisor's
death. `owner.stderr` records `killpg(SIGKILL)` raising EPERM. The native peer and
owner exited (the control registered kernel exit observers before killing its
own supervisor), but settlement was never published; the registry correctly
remains checkout-blocking. This is not labelled environmental: the unsandboxed
repeat failed too. These are isolated nested fixture registries, not active
candidate-checkout ownership claims.

The correction polls/reaps before signalling and treats macOS zombie-group EPERM
as **not yet absent**, as the existing group observer already does. It never
turns EPERM into cleanup permission. The control now persists its external exit
observations before asserting the candidate's disposition. The failed runs'
empty recovery socket directories remain protected pending separately supported
bookkeeping; their paths and missing settlement are in each operation record.
