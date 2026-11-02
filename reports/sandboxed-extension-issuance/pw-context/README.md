# Pinned PolicyWitness context

The [validator snapshot](controller/tools/sb_api_validator/sb_api_validator.c)
is copied byte-for-byte from PolicyWitness source commit
`6ea196363dd5007f3d98d72424e0ffd044524ddb`, at original path
`controller/tools/sb_api_validator/sb_api_validator.c`. Its batch call sites
around lines 515–521 pass either no filter value or one filter value; they do not
pass an extension class alongside a path. The snapshot supports Q2's
representation finding. It was inspected as source, not run as part of the pilot.
The original [PW license](LICENSE) accompanies it. Both content identities are
recorded in [the archive manifest](../ARCHIVE.json).

The independent pilot's sources and executed helper snapshots are already in
the archive. Other PW context linked from the plan is pinned to that same source
commit: the original native fixture/build command, production issuer/channel and
consumer implementation, host extension session, and the relevant documentation
and evidence contracts. [PW-REFERENCES.json](PW-REFERENCES.json) records original
paths, commit-specific URLs, Git blobs and SHA-256 values for those references.
Their identities were checked offline against the local Git objects during
preservation; network availability was not tested. These references preserve
the historical context without copying unrelated repository material.

The separately managed release and native-suite observations have the distinct
historical identities and availability limits described in the
[archive README](../README.md#historical-context). They are not r1 trial evidence.
