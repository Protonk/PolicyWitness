# Release command equipment

`tools.py` is an independent tool stand-in for `preflight/release_controls`.
It supplies raw Apple responses, records every invocation, extracts actual small
fixture ZIPs, and supplies controlled test reports. It never signs, submits to
Apple, invokes PW, or imports the release implementation.

The checker retains real manifest, archive-layout, and inventory checks; only
signature verification is modeled as successful there. Actual signature semantics
are checked by the existing opt-in signed-artifact controls. The release helpers
accept a Python-only command injection boundary; their CLIs always use the real
tools and expose no bypass flags.

`hanging_command.py` supplies real processes for `preflight/release_deadline_controls`.
It records each invocation, writes and flushes configured raw bytes before
forking, and connects its parent and child to the existing exec fixture's
`TreeControl` protocol. Both retain the inherited process group and ignore
SIGINT; one scenario lets only the parent exit zero on interruption. A normal
socket release exits cleanly. A 45-second alarm is an independent abandonment
backstop, longer than the checker's 15-second outer deadline. Exit assertions
run before fixture teardown can release or kill anything.
