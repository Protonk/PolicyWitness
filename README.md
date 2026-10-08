# PolicyWitness

PolicyWitness is a witness harness for macOS sandbox policies: it applies an
SBPL profile to a disposable process, records what the sandbox predicted for
each probe and what happened when the probe was attempted, and prints the
evidence as one JSON envelope.

Querying `sandbox_check` about a process and attempting an operation in that process under the same policy requires managing process lifecycles. `sandbox_check` answers for an existing PID, and sandbox application is one-way — a process gets exactly one sandbox. Evaluating a policy therefore means a fresh process per evaluation: compile and apply the policy to it once, aim both the query and the attempted operation at that PID while it lives, and carry the answer out through a channel the policy under test cannot sever.

> The [user guide](docs/PolicyWitness.md) has the specimen format, the output
> envelope and the operating guidance.

## Flow

PolicyWitness operates on specimens: an SBPL policy plus a probe plan. The
controller hands each specimen to a fresh runner, an unsandboxed XPC host that
spawns two short-lived children: a C worker that applies the policy to itself
and attempts the plan, and, for the probes it can predict, a validator that
asks `sandbox_check` about each one against the worker's PID. The host
releases the worker's attempts only after every prediction has been
collected, joins both children's outputs into one reply, and exits; the
controller wraps the reply in the envelope it prints.

Each step carries three records: the prediction, the attempt, and a
comparison that relates the two. The comparison says what was observed and
in what order; it never says whether prediction and enforcement agree, and no
failure is attributed to the sandbox without evidence. Kernel denial records
from the unified log are attached out of band, as candidates rather than
verdicts, and cannot change the execution result. The guide's
[reading rules](docs/PolicyWitness.md#reading-a-comparison-record) say how to
use each record.

> How one run unfolds in time, the boundaries it crosses and the checks that
> pin each of them: the [architecture tour](docs/ARCHITECTURE.md).

## Entitlements + SBPL

macOS sandboxing isn't just SBPL: a process's effective sandbox is its SBPL profile applied on top of the entitlements its binary was codesigned with. The same SBPL can yield different kernel behavior depending on which entitlements are granted, so a specimen has to describe both halves to be a faithful witness.

By default the policy is applied to a worker holding no entitlements. To
observe another combination, install an external runner (BYOXPC, bring your
own XPC service): a copy of the bundled service that `policy-witness runner
install` signs with your own entitlements plist. The policy is then applied to
a worker that holds those entitlements, the registry records what each binary
carries, and a specimen can require keys the worker must hold. The guide's
[external runners](docs/PolicyWitness.md#external-runners-byoxpc) section has
the install recipe and the signing constraints.

## Try it

Download a notarized release from
[GitHub Releases](https://github.com/Protonk/PolicyWitness/releases), or build
one as described under [What ships](#what-ships). Run it from a normal
Terminal; a sandboxed automation harness can refuse the XPC lookup.

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"

cat > /tmp/file_read_deny.json <<'JSON'
{
  "schema_version": 4,
  "specimen_id": "file_read_deny",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default) (deny file-read-data)"
  },
  "probe_plan": [
    {
      "step_id": "fr1",
      "sandbox_check": {
        "operation": "file-read-data",
        "filter": { "kind": "path", "value": "/etc/hosts" }
      },
      "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" }
    }
  ]
}
JSON

$PW run /tmp/file_read_deny.json > /tmp/result.json
```

The envelope's one step records a `deny` prediction, an attempt that failed
with `EPERM`, and a comparison stating that the query preceded the attempt;
the rest of the envelope records who ran it, what was run and what the host
observed.

> Short answers to common questions, including who needs this and what it can
> attribute, are in [QUESTIONS.md](docs/QUESTIONS.md).

## What ships

This repo builds a single distributable app bundle:

- `dist/PolicyWitness.app`
  - `Contents/MacOS/policy-witness` (Rust controller)
  - `Contents/MacOS/pw-runner-client` (Swift NSXPCConnection wrapper)
  - `Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper)
  - `Contents/MacOS/sbpl-check` (SBPL compile-check helper)
  - `Contents/XPCServices/PWRunner.xpc` (Swift XPC host; one host + two short-lived children per specimen)
    - `Contents/MacOS/pw-probe-runner` (bundle-local C worker that applies the policy and runs probe attempts)
    - `Contents/MacOS/sb_api_validator` (bundle-local validator launched once per run for sandbox_check verdicts)
  - `Contents/Resources/Evidence/*` (generated manifests: hashes/entitlements, `symbols.json`)

`./build.sh` compiles the Rust pieces with Cargo and the Swift and C pieces
with Meson (the root [meson.build](meson.build) owns their source lists and
flags), assembles them into that one bundle, signs it with the Developer ID
Application identity named by `IDENTITY` (see [docs/SIGNING.md](docs/SIGNING.md)),
stamps it with a version derived from the nearest tag, and embeds a generated
manifest of every binary's hash and entitlements. The [distribution directory](dist/README.md) describes the
current deliverables, release evidence, and preserved archives.

## Documentation

- Using the app:
  - User guide: [docs/PolicyWitness.md](docs/PolicyWitness.md)
  - Limits: [docs/LIMITS.md](docs/LIMITS.md)
  - FAQ: [docs/QUESTIONS.md](docs/QUESTIONS.md)
  - Signing/distribution: [docs/SIGNING.md](docs/SIGNING.md)
- Consuming the output:
  - Wire contracts (request, reply, envelope): [docs/CONTRACT.md](docs/CONTRACT.md)
  - Accepted requests and refusal diagnostics: [docs/REQUEST-GRAMMAR.md](docs/REQUEST-GRAMMAR.md)
- Implementation details:
  - CLI contract and controller behavior: [controller/README.md](controller/README.md)
  - Runner service architecture: [runner/README.md](runner/README.md)
  - Architecture tour (one run in time, boundaries, the document graph): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Contributing:
  - Repo orientation: [AGENTS.md](AGENTS.md)
  - Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
  - Testing: [tests/README.md](tests/README.md)
