# Working in dist/

- Build through `build.sh` or `make build`; keep the three current deliverables
  at the paths described in [README.md](README.md).
- Use the release helpers in [docs/SIGNING.md](../docs/SIGNING.md). Keep each
  attempt's receipts under one dated `evidence/` directory and preserve failures.
- Archive exact release bytes under `archive/<version>/` with
  `tests/lib/release_archive.py` (run by `make release`), which writes checksums
  and `release.json` and moves the attempt's receipts, and publish with
  `tests/lib/release_publish.py` (`make publish`), which records origin only after
  verifying the uploaded assets. Preserve original receipts, including recorded
  paths. Never substitute a later build or rebuild a tag to represent a published ZIP.
- Preserve `v2.3.0` and `v0.2.3` as the two version-reset examples. Check provenance
  before removing other release material; test-evidence retention is governed
  separately by `tests/RETAINED.json`.
- Keep generated files ignored. Change these two tracked documents when the
  directory's layout or operating rules change.
