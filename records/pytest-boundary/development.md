# Development observations

`pytest-boundary-reference-01`, run `20261030T144802Z_0cf0ac62`, preserves
automation-sandbox refusals for Unix socket binding and nested sandbox use.
Accounting and retention passed. The unchanged four-case selection outside
that sandbox passed in `pytest-boundary-reference-02`. These are distinct
observations, not retrospective repair of the first run.

Candidate `fa376979`, `pytest-boundary-demo-01`: ordinary completion passed.
The partial-setup stimulus produced the intended pytest setup error and later
independent pass, preserving separate phase reports. The supervisor nevertheless
crashed on a Unix datagram `ConnectionResetError` while the engine was exiting,
before it could finalize its resource lease. The independent exit observer
rejected cleanup because the child remained alive. Its outside safety release
is not candidate cleanup; the original acquired record and file remain in the
pinned failed output. This is a consequential prototype defect, not evidence
against failure continuation in pytest. The correction treats peer reset as
engine termination only after reaping, then executes normal resource finalization.
The observer now also durably records exits after its labeled safety cleanup.

The same correction adds the remaining declared malformed-account controls
(invalid outcome, unexpected skip, duplicate selection, unknown event) before
the next complete run. Their expectations remain independently literal.
