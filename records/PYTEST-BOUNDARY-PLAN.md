# Pytest primary-engine boundary investigation

Authorized 2026-10-30 following the completed independent workset assessment.
Accepted source is fixed at `77eb987554eef10ffa3371ffb21b235097562a78`.
The isolated worktree is `/private/tmp/pw-pytest-boundary-20261030`, branch
`investigation/pytest-boundary`. The original checkout's untracked review and
prompt remain untouched, as do the accepted app, old retained output and all
previously protected resources. This is experimental equipment, not a harness
migration or a change to an existing promise. C0.2 remains at
`0c22d256:records/workset/pytest-first.md`; no amended copy replaces it.

The [experimental amendment](pytest-boundary/amendment.md) fixes questions,
observations and scope. The [independent comparison contract](pytest-boundary/controls.md)
declares expectations before candidate implementation. Material results,
including design-changing failures, will be pinned in this worktree's
`tests/RETAINED.json` before any pruning. Pruning uses repository tools only;
previous evidence is not eligible for this investigation's cleanup.

Sequence:

1. Run the existing selection, accounting, cancellation and retention controls
   as a reference subject. Preserve source and equipment identity.
2. Implement the smallest serial pytest engine, durable report integration,
   external resource supervisor and restricted recovery path. Reuse existing
   lock/retention primitives explicitly; do not run the candidate under the
   dispatcher or an enclosing checkout hold.
3. Drive the declared stimuli with an independent observer. Check native
   process/descriptor facts separately from candidate summaries. Correct
   ordinary prototype mistakes, retaining consequential failures.
4. Decide credibility. If the selected obligations survive with pytest still
   owning ordinary execution, replay the C extraction through a small native
   exec-control slice. Otherwise localize the architectural failure and stop.
5. Account for displaced, relocated and new machinery and report limits.

New experiment drivers may create compatible owner/terminal envelopes solely
to use the existing retention/pruning tools. This is an explicit isolated
experimental entry point authorized by this assignment, not a new production
case or a claim to have run a repository battery. Candidate output belongs to
the candidate supervisor; the outside driver does not supply its lock, fixed
selection, recovery or successful-completion interpretation.

No production repair, CHECK handoff, historical pruning, or integration of
the demonstrator is in scope. A new production defect or proposed change to an
existing promise returns to the user. Ordinary equipment corrections proceed.

The [development account](pytest-boundary/development.md) preserves corrections
and original evidence. Candidate source is [supervisor](pytest-boundary/supervisor.py),
[pytest integration](pytest-boundary/engine.py), [accounting](pytest-boundary/common.py),
[resource owner](pytest-boundary/resource_owner.py) and [recovery](pytest-boundary/recover.py).
The [independent driver](pytest-boundary/observe.py) and
[synthetic subjects](pytest-boundary/test_subject.py) are investigative equipment.
[Dependency inventory](pytest-boundary/equipment.json) and
[version requirements](pytest-boundary/requirements.txt) identify the environment.

Credibility decision after `cfbd753a` / `pytest-boundary-demo-05`: all eighteen
declared groups passed, including ten independent accounting inputs and the
deliberately dropped-lock negative control. Pytest owns ordinary selection and
execution; the supervisor waits on one engine and resource requests, not selected
case commands. The selected obligations survived. This warrants the one exposed
C extraction replay, not migration or a claim of net savings. Durability here
means process death with fsync-backed records, not power loss; the external
resource adapter is one bounded file/child kind, not launchd.

The exposed replay uses the [native adapter](pytest-boundary/native_adapter.py),
[pytest cases](pytest-boundary/test_native.py) and
[outside replay observer](pytest-boundary/observe_replay.py). The pre-extraction
adapter remains recoverable at `0085bd54`; its actual adaptation is the next
source commit, so the comparison need not be reconstructed from prose.
