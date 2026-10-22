# Distribution output

| Entry | Contents |
| --- | --- |
| `PolicyWitness.app` | Current signed local build, carrying its evidence manifest, symbols file and provenance record under `Contents/Resources/Evidence/`. |
| `PolicyWitness.zip` | ZIP from that build; release acceptance is recorded separately. |
| `PolicyWitness.md` | Standalone user guide from the same build. |
| `evidence/` | Dated release attempts, each with an index and named command receipts. An archived attempt is moved into its release archive and leaves an `<attempt>.archived` pointer. |
| `archive/v<version>/` | One preserved release per packaged version, created by `tests/lib/release_archive.py`. |

Each archive contains a versioned release ZIP, the guide, `SHA256SUMS`, the
`release.json` release record, and supporting `evidence/` (the moved attempt,
the `provenance.json` record copied out of the accepted ZIP, plus
`release-notes.md` and `github-release.json` once published). The release
record binds the copied record, the final controller hash and the app seal's
facts to the ZIP's bytes.
Only this README and AGENTS.md are tracked. Artifacts are local and may be absent
in a fresh checkout. An acceptance result identifies an exact ZIP hash.

The app's XPC bundle includes its worker, validator and `pw-extension-issuer`,
with separate entries in embedded signed evidence. Copy the complete bundle for
BYOXPC use; an older copy without the issuer can still serve ordinary specimens
but cannot perform an extension experiment.

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
