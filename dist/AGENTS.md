# Working in dist/

- Build through `build.sh` or `make build`; keep the three current deliverables
  at the paths described in [README.md](README.md).
- Use the release helpers in [docs/SIGNING.md](../docs/SIGNING.md). Keep each
  attempt's receipts under one dated `evidence/` directory and preserve failures.
- Archive exact published release bytes under `archive/<version>/`, with
  checksums and `release.json` recording origin, tag/commit when established,
  and evidence locations. Preserve original receipts, including recorded paths.
  Never substitute a later build or rebuild a tag to represent a published ZIP.
- Preserve `v2.3.0` and `v0.2.3` as the two version-reset examples. Check provenance
  before removing other release material; test-evidence retention is governed
  separately by `tests/RETAINED.json`.
- Keep generated files ignored. Change these two tracked documents when the
  directory's layout or operating rules change.
