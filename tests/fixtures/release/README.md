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
