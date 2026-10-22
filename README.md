# PolicyWitness

PolicyWitness is a witness harness for macOS sandbox policies: it applies an
SBPL profile to a disposable process, records available predictions and what
happened when each probe was attempted, and prints the evidence as one JSON
envelope.

## The Problem

A query about a sandbox is not the same thing as attempting an operation inside it. `sandbox_check` answers questions about a live process, while an attempt takes place in a process that has already applied a policy it cannot remove. To put the two observations alongside one another, an experiment must keep the right process alive, establish their order, and recover its report even if the policy forbids ordinary communication. Preparation matters too: opening a resource before applying the sandbox can change what a later operation actually tests.

Even a well-arranged experiment does not make its results self-interpreting. An operation can fail for reasons other than sandbox denial; success can depend on entitlements, inherited resources, and conditions outside the SBPL text. A `sandbox_check` answer and an attempt result may differ without establishing why, or appear to agree without proving that prediction and enforcement agree. 

## The Experiment

PolicyWitness operates on specimens: an SBPL policy and a plan of probes. Each specimen gets a fresh worker that applies the policy once. An unsandboxed host arranges for a separate validator to query the worker's live PID before releasing it to attempt the planned operations. The host collects observations through a reporting path outside the policy under test. A specimen can also contain ordered phases, allowing successive rounds of queries and attempts within the same worker.

The result is one JSON envelope containing the available predictions, attempts and their observed outcomes, together with evidence of their provenance and ordering. Comparison records relate those observations without declaring whether prediction and enforcement agree. Missing or incomplete observations remain visible rather than being turned into conclusions.

> How one run unfolds in time, the boundaries it crosses and the checks that pin each of them: the [architecture tour](docs/ARCHITECTURE.md). The [user guide](docs/PolicyWitness.md) has the specimen format, the output
> envelope and the operating guidance.

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
one as described under [Build and bundle](#build-and-bundle). Releases and builds target
macOS 26 on Apple Silicon, the platform this repository is tested on: every
executable in the app is a thin arm64 Mach-O, so it does not run on an Intel
Mac. `Info.plist` and `meson.build` declare the minimum together. Run it from a normal
Terminal; a sandboxed automation harness can refuse the XPC lookup.

```sh
PW="/Applications/PolicyWitness.app/Contents/MacOS/policy-witness"

cat > /tmp/file_read_deny.json <<'JSON'
{
  "schema_version": 5,
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

## Build and bundle

Build on an Apple Silicon Mac, natively: `build.sh` refuses, before its other
checks and before taking the checkout lock, when the machine is not Apple
Silicon or the script runs translated by Rosetta. Through `make build`, make
itself and its `SDKROOT` check have already run by then. Building
PolicyWitness requires Rust with Cargo and its `aarch64-apple-darwin` target
(the default on Apple Silicon), Xcode Command Line Tools (or Xcode), and Meson
and Ninja on `PATH` (`brew install meson ninja`). The build checks every
executable it produces against that one output target, thin arm64 macOS code.
The Developer ID Application signing identity must already be in your
login keychain. From the repository root:

```sh
make build IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
```

The build writes `dist/PolicyWitness.app`, a ZIP ready for notarization at
`dist/PolicyWitness.zip`, and the standalone user guide at
`dist/PolicyWitness.md`. It reuses `builddir/` and `controller/target/`
under the toolchain and output target recorded when they were set up;
`PW_FRESH_BUILD=1` replaces their build state before compiling, and a changed compiler or SDK is refused
until then. A build holds the checkout's test lock, so a build and a test
battery in one checkout run one at a time.

`build.sh` compiles the Rust components with Cargo and the Swift and C
components with Meson, assembles them into one app bundle, and signs it
with the supplied identity, then verifies the Developer ID chain and secure
timestamps on the signatures it made. The app carries a version derived
from git and generated evidence recording its binaries' hashes and
entitlements and a provenance record of the tools, configuration and build
directories behind them.

The app contains:

- `dist/PolicyWitness.app`
  - `Contents/MacOS/policy-witness` (Rust controller)
  - `Contents/MacOS/pw-runner-client` (Swift NSXPCConnection wrapper)
  - `Contents/MacOS/sandbox-log-observer` (Rust unified-log capture helper)
  - `Contents/MacOS/sbpl-check` (SBPL compile-check helper)
  - `Contents/XPCServices/PWRunner.xpc` (Swift XPC host; one host and worker per specimen, with a fresh validator per eligible phase)
    - `Contents/MacOS/pw-probe-runner` (bundle-local C worker that applies the policy and runs probe attempts)
    - `Contents/MacOS/sb_api_validator` (bundle-local validator launched per eligible phase for sandbox_check verdicts)
    - `Contents/MacOS/pw-extension-issuer` (ordinary-authority file-extension issuer with a transient token channel)
  - `Contents/Resources/Evidence/*` (generated evidence: `manifest.json` with hashes and entitlements, `symbols.json`, and `provenance.json`, the build's record of its tools, configuration, directories and outputs)

The [build tour](docs/BUILD.md) describes the toolchain, build settings,
cache compatibility, the lock and the signing checks;
[the evidence inventory](docs/SIGNING.md#evidence-artifacts) owns the record
formats. Building produces a signed app; the
[release procedure](docs/SIGNING.md#release-procedure) covers the fresh
release build, notarization, acceptance testing and publication. The
[distribution directory](dist/README.md) describes the deliverables and
preserved release archives.

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
  - Build tour, native compilation and signing: [docs/BUILD.md](docs/BUILD.md)
  - CLI contract and controller behavior: [controller/README.md](controller/README.md)
  - Runner service architecture: [runner/README.md](runner/README.md)
  - Architecture tour (one run in time, boundaries, the document graph): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  - Worker tour (resources, authority and experimental constraints): [docs/WORKER.md](docs/WORKER.md)
- Contributing:
  - Working guidance: [AGENTS.md](AGENTS.md)
  - Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
  - Working on the controller: [controller/AGENTS.md](controller/AGENTS.md)
  - Working on the runner and native helpers: [runner/AGENTS.md](runner/AGENTS.md)
  - Test harness and coverage: [tests/README.md](tests/README.md)
  - Working on tests: [tests/AGENTS.md](tests/AGENTS.md)
