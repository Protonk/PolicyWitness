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
- New archives carry full test evidence under `evidence/test-runs/`; validate the
  new release before cleanup. `release_rotate.py` keeps its acceptance and battery
  plus the newest completed local output and journals cleanup of older managed
  runs in `evidence/rotation.json`. Resume that helper after an interruption;
  preserve its quarantine under `tests/out/.release-rotation/`. Scratch follows
  [.tmp/AGENTS.md](../.tmp/AGENTS.md). Evidence stays local; no backup service is required.
- Preserve `v2.3.0` and `v0.2.3` as the two version-reset examples. Check provenance
  before removing other release material; test-evidence retention is governed
  separately by `tests/RETAINED.json`.
- Keep generated files ignored. Change these two tracked documents when the
  directory's layout or operating rules change.
