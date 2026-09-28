# Distribution output

| Entry | Contents |
| --- | --- |
| `PolicyWitness.app` | Current signed local build. |
| `PolicyWitness.zip` | ZIP from that build; release acceptance is recorded separately. |
| `PolicyWitness.md` | Standalone user guide from the same build. |
| `evidence/` | Dated release attempts, each with an index and named command receipts. |
| `archive/v2.3.0/`, `archive/v0.2.3/` | Preserved releases on either side of the version reset: 2.3.0 preceded 0.2.3. |

Each archive contains a versioned release ZIP, `SHA256SUMS`, `release.json`
provenance, and supporting `evidence/`; a guide is included when it shipped.
Only this README and AGENTS.md are tracked. Artifacts are local and may be absent
in a fresh checkout. An acceptance result identifies an exact ZIP hash.

See [signing and releases](../docs/SIGNING.md) for the evidence format and procedure.
