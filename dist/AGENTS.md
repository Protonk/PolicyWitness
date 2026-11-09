# Working in dist/

- Build with `make build` and follow [the release procedure](../docs/SIGNING.md#release-procedure)
  for packaging and publication. [README.md](README.md) describes the artifacts.
- Preserve each release attempt's receipts until the central retention policy
  positively associates it with an expired release. Never substitute a later
  build or rebuild a tag to represent a published ZIP.
- Use `make prune` to preview and `make prune APPLY=1` to apply or resume cleanup.
  Preserve `tests/out/.retention/` after interruption and follow
  [the recovery procedure](../docs/SIGNING.md#portable-test-evidence-and-release-cleanup).
- Keep the four newest complete local archives and only the newest unpacked
  acceptance. There are no manual pins or configurable release roots. Inspect
  blockers; do not bypass ownership or resource-recovery checks.
- Keep generated files ignored. Update README.md for layout changes and this
  file for operating-rule changes. Scratch follows [.tmp/AGENTS.md](../.tmp/AGENTS.md).
