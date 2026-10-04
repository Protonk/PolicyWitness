# Distribution output

| Entry | Contents |
| --- | --- |
| `PolicyWitness.app` | Current signed local build. |
| `PolicyWitness.zip` | ZIP from that build; release acceptance is recorded separately. |
| `PolicyWitness.md` | Standalone user guide from the same build. |
| `evidence/` | Dated release attempts, each with an index and named command receipts. An archived attempt is moved into its release archive and leaves an `<attempt>.archived` pointer. |
| `archive/v<version>/` | One preserved release per packaged version, created by `tests/lib/release_archive.py`. `v2.3.0` and `v0.2.3` sit on either side of the version reset: 2.3.0 preceded 0.2.3. |

Each archive contains a versioned release ZIP, `SHA256SUMS`, `release.json`
provenance, and supporting `evidence/` (the moved attempt, plus `release-notes.md`
and `github-release.json` once published); a guide is included when it shipped.
Only this README and AGENTS.md are tracked. Artifacts are local and may be absent
in a fresh checkout. An acceptance result identifies an exact ZIP hash.

Portable test evidence lives under `evidence/test-runs/`: `runs.tar.gz` holds
the complete acceptance and battery directories; `manifest.json` inventories
and hashes them; standalone JSON summaries are addressed relative to the
archive by `release.json`. Raw receipts keep their original paths as provenance.
`evidence/rotation.json` records cleanup of older managed test output, including
enough state to resume an interrupted deletion. Successful packaging keeps the
latest release's working acceptance and battery plus the newest completed local
output. Explicit pins and pending resource cleanup remain protected. Historical
release archives stay local; cleanup does not archive every development run or
require an off-machine backup. Scratch follows [.tmp/AGENTS.md](../.tmp/AGENTS.md).

See [signing and releases](../docs/SIGNING.md) for the evidence format and procedure.
