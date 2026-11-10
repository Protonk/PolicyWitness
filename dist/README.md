# Distribution output

| Entry | Contents |
| --- | --- |
| `PolicyWitness.app` | Current signed local build, carrying its evidence manifest, symbols file and provenance record under `Contents/Resources/Evidence/`. |
| `PolicyWitness.zip` | ZIP from that build; release acceptance is recorded separately. |
| `PolicyWitness.md` | Standalone user guide from the same build. |
| `evidence/` | Dated release attempts, each with an index and named command receipts. An archived attempt is moved into its release archive and leaves an `<attempt>.archived` pointer. |
| `archive/v<version>/` | One of the four newest complete local releases, created by `tests/lib/release_archive.py`. |

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
the complete acceptance directory with its nested battery; `manifest.json`
inventories and hashes it; standalone JSON summaries are addressed relative to the
archive by `release.json`. Raw receipts keep their original paths as provenance.
Current release verification accepts portable bundle schema 3 with a captured
execution contract; `release.json` uses schema 2. The newest archive protects
its unpacked acceptance and nested battery. Ordinary pruning removes expired
archives and their positively linked attempts/pointers, plus inactive owned
non-release output regardless of completion. Unknown ownership and unresolved
resource cleanup block deletion. There are no manual pins or retention knobs.
The fixed archive root is this checkout's `dist/archive/`.

Unassociated attempts and pointers are reported as unmanaged and kept without
failing cleanup; association conflicts and corrupt records remain blockers.
Regular `.DS_Store` files directly in distribution containers are disposable.
Pruning does not search retained archives or the signed app for metadata.

Interrupted cleanup is journaled under `tests/out/.retention/`; resume with
`make prune APPLY=1`. The journal is removed on completion and surviving archives
are unchanged. The temporary historical storage inspector classifies known
schema-1 archives until the last such archive and dependent quarantine expire;
it does not admit them for publishing. Git tags and published assets survive
local expiry. Scratch follows [.tmp/AGENTS.md](../.tmp/AGENTS.md).

See [signing and releases](../docs/SIGNING.md) for the evidence format and procedure.
