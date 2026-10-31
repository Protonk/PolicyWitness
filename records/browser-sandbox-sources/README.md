# macOS browser sandbox source packet

Start with **[REPORT.md](REPORT.md)** for selection rationale, product/source distinctions and coverage limits. **[SOURCE-CATALOG.md](SOURCE-CATALOG.md)** identifies every retained upstream file.

The packet contains 25 complete, Git-blob-verified upstream files from fixed Chromium, Firefox, WebKit and Ladybird commits, including the Chromium Mac Sandbox V2 design document and two repository license files. `sources/` preserves their repository-relative paths. `MANIFEST.json` records immutable upstream URLs and content identities; `SHA256SUMS` covers the archive contents.

This is source selection, not a comparative analysis or a buildable set of browser sources. There are no PAWL extractions, browser binaries, compiled profiles, runtime observations, tests to run against the OS, or proposed PolicyWitness changes. A complete retained file is not necessarily a complete policy or all of its transitive inputs.

No browser installation is required. Optional local integrity check:

```sh
python3 VERIFY.py
```

The check is offline and does not execute any upstream source. The source licenses are retained in their files and in `NOTICES.md`.
