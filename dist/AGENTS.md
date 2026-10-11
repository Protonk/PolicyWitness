# Working in dist/

- Build with `make build` and follow [the release procedure](../docs/SIGNING.md#release-procedure)
  for packaging and publication. [README.md](README.md) describes the artifacts.
- Preserve each release attempt's receipts, including failures and their recorded
  paths. Never substitute a later build or rebuild a tag to represent a published ZIP.
- Use the release helpers for test-evidence cleanup. After an interruption,
  preserve `tests/out/.release-rotation/` and resume the archive's
  `release_rotate.py --apply` transaction through [the recovery procedure](../docs/SIGNING.md#portable-test-evidence-and-release-cleanup).
- Preserve `v2.3.0` and `v0.2.3` as the two version-reset examples. Check provenance
  before removing other release material; test-evidence retention is governed
  separately by `tests/RETAINED.json`.
- Keep generated files ignored. Update README.md for layout changes and this
  file for operating-rule changes. Scratch follows [.tmp/AGENTS.md](../.tmp/AGENTS.md).
