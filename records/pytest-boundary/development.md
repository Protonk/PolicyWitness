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

Candidate `4211d48b`, `pytest-boundary-demo-02`: ordinary completion, failed
pre-yield setup and simultaneous body/teardown failure passed. SIGINT also
preserved incomplete active/queued accounting and witnessed child cleanup,
but the observer rejected the actual finalizer receipt. Its exact receipt list
had unnecessarily assumed no teardown on interruption. The predeclared contract
requires no queued start and no invented active success, not absent finalizers.
Correcting the expected SIGINT receipt to include `active.teardown` preserves
those obligations. This is an observer defect; no candidate change is needed.

Candidate `493309ed`, `pytest-boundary-demo-03`: engine-death and dual-death
controls passed, including live child lock retention, rejected competing
execution, authenticated recovery and independent kernel exits. Selection and
deselection also passed. The environment observer then found that the actual
macOS child environment adds `__CF_USER_TEXT_ENCODING` to the three explicitly
supplied values. No inherited lock/capture descriptor or poisoned Python option
was present. The subject launch now explicitly supplies that observed encoding
value, and the observer requires the complete four-field environment. Engine
version, capture, disabled optimization and external-plugin absence are also
recorded and independently checked. This correction preserves exact environment
verification rather than ignoring unspecified extra variables.

Candidate `5c4cd41d`, `pytest-boundary-demo-04`: the exact four-field child
environment passed. The added interpreter check compared a reported keg-path
symlink with a fully resolved framework path as strings. Both identify the
same executable. The observer now resolves both paths before comparison; it
still rejects a different executable. No subject or engine change was needed.
